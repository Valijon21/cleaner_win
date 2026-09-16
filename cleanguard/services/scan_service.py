"""
Scan Application Service: Background worker integrating ScannerEngine with UI signals.
"""

from typing import Optional
from PyQt5.QtCore import QThread, pyqtSignal
from cleanguard.core.scanner.engine import ScannerEngine
from cleanguard.core.scanner.base import CancellationToken
from cleanguard.database.db import DatabaseManager
from cleanguard.database.repositories import HistoryRepository
from cleanguard.utils.logging import get_logger

logger = get_logger("scan_service")


class ScanWorker(QThread):
    """Background worker thread for running full storage scans without blocking UI."""
    progress = pyqtSignal(str, int, int)  # (status_msg, files_count, bytes_found)
    finished = pyqtSignal(object, list)   # (ScanSummary, List[ScanItem])
    error = pyqtSignal(str)

    def __init__(
        self,
        scanner_engine: Optional[ScannerEngine] = None,
        db_manager: Optional[DatabaseManager] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.scanner_engine = scanner_engine or ScannerEngine()
        self.history_repo = HistoryRepository(db_manager or DatabaseManager())
        self.cancel_token = CancellationToken()

    def cancel(self) -> None:
        """Request scan cancellation."""
        self.cancel_token.cancel()

    def run(self) -> None:
        try:
            self.cancel_token.reset()

            def on_progress(msg: str, count: int, bytes_f: int):
                self.progress.emit(msg, count, bytes_f)

            summary, items = self.scanner_engine.scan_all(
                cancel_token=self.cancel_token,
                progress_callback=on_progress,
            )

            # Record session to SQLite
            try:
                self.history_repo.record_scan_session(summary)
            except Exception as exc:
                logger.warning(f"Could not persist scan session to DB: {exc}")

            self.finished.emit(summary, items)
        except Exception as exc:
            logger.error(f"Scan worker failed: {exc}")
            self.error.emit(str(exc))
