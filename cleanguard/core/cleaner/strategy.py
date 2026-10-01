"""
Deletion and Recovery Strategies for CleanGuard.
Implements non-destructive Recycle Bin movement and safe file removal.
"""

import os
import re
import time
from typing import Optional, Tuple
from cleanguard.core.contracts import CleanupStrategy, ErrorCode
from cleanguard.windows.recycle_bin import move_to_recycle_bin, empty_recycle_bin
from cleanguard.utils.logging import get_logger

logger = get_logger("cleanup_strategy")

# Only a drive-root Recycle Bin (e.g. "C:\$Recycle.Bin") may trigger SHEmptyRecycleBin.
_RECYCLE_BIN_ROOT_RE = re.compile(r"^([A-Za-z]:)[\\/]\$Recycle\.Bin[\\/]?$", re.IGNORECASE)


def recycle_bin_root_drive(path: str) -> Optional[str]:
    """Return the drive letter ("C:") if path is exactly a drive's Recycle Bin root, else None."""
    if not path:
        return None
    m = _RECYCLE_BIN_ROOT_RE.match(path)
    return m.group(1).upper() if m else None


def execute_deletion(
    path: str,
    strategy: CleanupStrategy,
    drive_letter: str = "C:",
) -> Tuple[bool, ErrorCode, str]:
    """
    Execute deletion of a verified target using the specified strategy.
    Returns (success, error_code, error_message).
    """
    rb_drive = recycle_bin_root_drive(path)

    # Strategy 1: Empty Recycle Bin
    if rb_drive:
        ok = empty_recycle_bin(drive_letter=rb_drive, show_confirmation=False)
        if ok:
            return True, ErrorCode.NONE, "Recycle Bin emptied."
        return False, ErrorCode.IO_ERROR, "Failed to empty Recycle Bin via Shell."

    if not os.path.exists(path):
        return True, ErrorCode.NONE, "File already removed or absent."

    # Strategy 2: Move to Recycle Bin (Non-destructive, preferred)
    if strategy == CleanupStrategy.RECYCLE_BIN:
        if move_to_recycle_bin(path):
            return True, ErrorCode.NONE, "Moved to Recycle Bin."
        # Never silently escalate a recoverable delete into a permanent one:
        # the user explicitly chose the reversible strategy.
        logger.warning(f"Recycle bin move failed for {path}; item left in place.")
        return False, ErrorCode.IO_ERROR, "Could not move item to Recycle Bin."

    # Strategy 3: Safe Direct File Deletion (for temporary / cache items)
    if strategy in (CleanupStrategy.SAFE_DELETE, CleanupStrategy.PERMANENT_DELETE):
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
