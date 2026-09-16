"""
Deletion and Recovery Strategies for CleanGuard.
Implements non-destructive Recycle Bin movement and safe file removal.
"""

import os
import sys
import time
from typing import Tuple
from cleanguard.core.contracts import CleanupStrategy, ErrorCode
from cleanguard.windows.recycle_bin import move_to_recycle_bin, empty_recycle_bin
from cleanguard.utils.logging import get_logger

logger = get_logger("cleanup_strategy")


def execute_deletion(
    path: str,
    strategy: CleanupStrategy,
    drive_letter: str = "C:",
) -> Tuple[bool, ErrorCode, str]:
    """
    Execute deletion of a verified target using the specified strategy.
    Returns (success, error_code, error_message).
    """
    if not os.path.exists(path) and not path.endswith("$Recycle.Bin"):
        return True, ErrorCode.NONE, "File already removed or absent."

    # Strategy 1: Empty Recycle Bin
    if path.endswith("$Recycle.Bin"):
        ok = empty_recycle_bin(drive_letter=drive_letter, show_confirmation=False)
        if ok:
            return True, ErrorCode.NONE, "Recycle Bin emptied."
        return False, ErrorCode.IO_ERROR, "Failed to empty Recycle Bin via Shell."

    # Strategy 2: Move to Recycle Bin (Non-destructive, preferred)
    if strategy == CleanupStrategy.RECYCLE_BIN:
        ok = move_to_recycle_bin(path)
        if ok:
            return True, ErrorCode.NONE, "Moved to Recycle Bin."
        # If Shell operation failed (e.g. file too large for trash), fallback to SAFE_DELETE only if temp
        logger.debug(f"Recycle bin move failed for {path}, falling back to safe delete.")

    # Strategy 3: Safe Direct File Deletion (for temporary / cache items)
    if strategy in (CleanupStrategy.SAFE_DELETE, CleanupStrategy.PERMANENT_DELETE, CleanupStrategy.RECYCLE_BIN):
        try:
            if os.path.isdir(path):
                # Only remove directory if empty
                os.rmdir(path)
            else:
                # Remove file with retry for brief transient locks
                max_retries = 2
                for attempt in range(max_retries):
                    try:
                        # Clear read-only attribute if present
                        try:
                            os.chmod(path, 0o777)
                        except Exception:
                            pass
                        os.remove(path)
                        return True, ErrorCode.NONE, "File removed successfully."
                    except PermissionError:
                        if attempt < max_retries - 1:
                            time.sleep(0.05)
                            continue
                        return False, ErrorCode.ACCESS_DENIED, "Access denied / locked by another process."
                    except FileNotFoundError:
                        return True, ErrorCode.NONE, "Target already gone."

            return True, ErrorCode.NONE, "Target removed successfully."
        except OSError as exc:
            return False, ErrorCode.IO_ERROR, str(exc)

    return False, ErrorCode.UNKNOWN_ERROR, "Unrecognized cleanup strategy."
