"""
Cleanup Application Service: Background worker integrating CleanupExecutor with UI.
"""

from typing import List, Optional
from PyQt5.QtCore import QThread, pyqtSignal
from cleanguard.core.cleaner.executor import CleanupExecutor
from cleanguard.core.cleaner.planner import CleanupPlanner
from cleanguard.core.scanner.base import CancellationToken
from cleanguard.core.contracts import ScanItem, CleanupStrategy
from cleanguard.core.safety import SafetyEngine
from cleanguard.database.db import DatabaseManager
from cleanguard.database.repositories import HistoryRepository
from cleanguard.windows.restore_point import create_restore_point
from cleanguard.utils.logging import get_logger

logger = get_logger("cleanup_service")


class CleanupWorker(QThread):
    """Background worker thread for running file cleanup safely."""
    progress = pyqtSignal(int, int, int, str)  # (processed, total, bytes_recovered, current_path)
    finished = pyqtSignal(object)              # (CleanupSummary)
    error = pyqtSignal(str)

    def __init__(
        self,
        items_to_clean: List[ScanItem],
        scan_id: Optional[str] = None,
        strategy: CleanupStrategy = CleanupStrategy.SAFE_DELETE,
        safety_engine: Optional[SafetyEngine] = None,
        db_manager: Optional[DatabaseManager] = None,
        create_restore_point: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.raw_items = items_to_clean
        self.scan_id = scan_id
        self.strategy = strategy
        self.create_restore_point = create_restore_point
        self.safety_engine = safety_engine or SafetyEngine()
        self.history_repo = HistoryRepository(db_manager or DatabaseManager())
        self.cancel_token = CancellationToken()

    def cancel(self) -> None:
        """Cancel cleanup operations gracefully."""
        self.cancel_token.cancel()

    def run(self) -> None:
        try:
            self.cancel_token.reset()

            # 0. Optional System Restore snapshot. Done here, not on the GUI thread:
            # SRSetRestorePointW / Checkpoint-Computer can block for 30+ seconds.
            if self.create_restore_point:
                try:
                    ok, msg = create_restore_point("CleanGuard Pre-Clean Snapshot")
                    logger.info(f"Restore point: {msg}" if ok else f"Restore point skipped: {msg}")
                except Exception as exc:
                    logger.debug(f"Restore point creation failed: {exc}")

            # 1. Plan and vet items
            planned_items, _ = CleanupPlanner.build_plan(
                items=self.raw_items,
                default_strategy=self.strategy,
            )

            # 2. Execute cleanup under Safety Engine supervision
            executor = CleanupExecutor(safety_engine=self.safety_engine)

            def on_progress(processed: int, total: int, recovered: int, cur_path: str):
                self.progress.emit(processed, total, recovered, cur_path)

            summary = executor.execute(
                planned_items=planned_items,
                scan_id=self.scan_id,
                strategy=self.strategy,
                cancel_token=self.cancel_token,
                progress_callback=on_progress,
            )

            # 3. Persist audit records to SQLite database
            try:
                self.history_repo.record_cleanup_session(summary)
            except Exception as exc:
                logger.warning(f"Could not persist cleanup session to DB: {exc}")

            self.finished.emit(summary)
        except Exception as exc:
            logger.error(f"Cleanup worker encountered failure: {exc}", exc_info=True)
            self.error.emit(str(exc))
