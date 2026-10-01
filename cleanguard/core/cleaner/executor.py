"""
Cleanup Executor: Executes vetted cleanup plan with TOCTOU pre-validation.
"""

import os
import time
import uuid
from typing import List, Optional, Callable, Set
from cleanguard.core.contracts import (
    ScanItem,
    CleanupItemResult,
    CleanupSummary,
    CleanupStatus,
    CleanupStrategy,
    CleanCategory,
    ErrorCode,
)
from cleanguard.core.scanner.base import CancellationToken
from cleanguard.core.safety import SafetyEngine
from cleanguard.core.cleaner.strategy import execute_deletion, recycle_bin_root_drive
from cleanguard.utils.filesystem import prune_empty_directories, is_path_under_directory
from cleanguard.windows.known_folders import get_known_folders
from cleanguard.utils.logging import get_logger

logger = get_logger("cleanup_executor")

CleanupProgressCallback = Callable[[int, int, int, str], None]
# Callback signature: (items_processed, total_items, bytes_recovered, current_path)


class CleanupExecutor:
    """Executes file removal under strict supervision of the Safety Engine."""

    def __init__(self, safety_engine: Optional[SafetyEngine] = None):
        self.safety_engine = safety_engine or SafetyEngine()

    def execute(
        self,
        planned_items: List[ScanItem],
        scan_id: Optional[str] = None,
        strategy: CleanupStrategy = CleanupStrategy.SAFE_DELETE,
        cancel_token: Optional[CancellationToken] = None,
        progress_callback: Optional[CleanupProgressCallback] = None,
    ) -> CleanupSummary:
        """
        Execute the vetted cleanup plan with TOCTOU pre-validation.
        """
        token = cancel_token or CancellationToken()
        cleanup_id = str(uuid.uuid4())
        start_time = time.time()

        deleted_count = 0
        skipped_count = 0
        failed_count = 0
        recovered_bytes = 0
        item_results: List[CleanupItemResult] = []
        affected_dirs: Set[str] = set()
        last_report_time = 0.0

        total_items = len(planned_items)
        logger.info(f"Starting Cleanup Session {cleanup_id} ({total_items} targets).")

        def record(item: ScanItem, status: CleanupStatus, err: ErrorCode = ErrorCode.NONE, msg: str = "") -> None:
            item_results.append(
                CleanupItemResult(
                    path=item.path,
                    category=item.category,
                    risk_level=item.risk_level,
                    size=item.size,
                    status=status,
                    strategy=strategy,
                    error_code=err,
                    error_message=msg,
                )
            )

        cancel_logged = False
        for idx, item in enumerate(planned_items):
            if token.is_cancelled():
                if not cancel_logged:
                    logger.info(f"Cleanup Session {cleanup_id} cancelled by user.")
                    cancel_logged = True
                record(item, CleanupStatus.CANCELLED, ErrorCode.USER_CANCELLED, "Cleanup cancelled by user.")
                skipped_count += 1
                continue

            # Recycle Bin root entries are emptied through the Shell API. Only an exact
            # drive-root "$Recycle.Bin" path of the recycle_bin category qualifies; any
            # other path ending in that name goes through the full safety gate.
            if item.category == CleanCategory.RECYCLE_BIN.value and recycle_bin_root_drive(item.path):
                ok, err, msg = execute_deletion(item.path, strategy=strategy)
                if ok:
                    deleted_count += 1
                    recovered_bytes += item.size
                    record(item, CleanupStatus.SUCCESS)
                else:
                    failed_count += 1
                    record(item, CleanupStatus.FAILED, err, msg)
            else:
                # TOCTOU Mitigation: Revalidate target immediately before deletion
                approved, err_code, reason = self.safety_engine.verify_cleanup_target(
                    path=item.path,
                    category=item.category,
                    allowed_roots=item.allowed_roots,
                )
                if not approved:
                    logger.warning(f"Target {item.path} rejected at deletion safety gate: {reason}")
                    skipped_count += 1
                    record(item, CleanupStatus.SKIPPED, err_code, reason)
                else:
                    success, err, msg = execute_deletion(item.path, strategy=strategy)
                    if success:
                        deleted_count += 1
                        recovered_bytes += item.size
                        affected_dirs.add(os.path.dirname(item.path))
                        record(item, CleanupStatus.SUCCESS)
                    else:
                        failed_count += 1
                        logger.warning(f"Failed to delete '{item.path}': [{err}] {msg}")
                        record(item, CleanupStatus.FAILED, err, msg)

            # Report progress for every processed item (skipped ones included) so the
            # progress bar always reaches 100%.
            now = time.time()
            if progress_callback and (idx == 0 or idx == total_items - 1 or (now - last_report_time) >= 0.08):
                last_report_time = now
                progress_callback(idx + 1, total_items, recovered_bytes, item.path)

        # Safely prune emptied temporary subdirectories (e.g. emptied _MEI... directories)
        try:
            folders = get_known_folders()
            temp_roots = [r for r in (folders.user_temp, folders.system_temp) if r and os.path.exists(r)]
            for d in affected_dirs:
                for root in temp_roots:
                    if is_path_under_directory(d, root) and d != root:
                        prune_empty_directories(d, stop_at_dir=root)
        except Exception as exc:
            logger.debug(f"Directory pruning notice: {exc}")

        summary = CleanupSummary(
            cleanup_id=cleanup_id,
            scan_id=scan_id,
            started_at=start_time,
            finished_at=time.time(),
            files_deleted=deleted_count,
            files_skipped=skipped_count,
            files_failed=failed_count,
            bytes_recovered=recovered_bytes,
            item_results=item_results,
        )

        logger.info(
            f"Cleanup Session {cleanup_id} finished: {deleted_count} deleted, "
            f"{skipped_count} skipped, {failed_count} failed. Recovered: {recovered_bytes} bytes."
        )
        return summary
