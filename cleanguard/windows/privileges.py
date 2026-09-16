"""
Windows UAC, Tokens and Administrator Privilege Management.
Strictly compatible with Windows 7 SP1 through Windows 11.
"""

import sys
import ctypes
from typing import List, Optional
from cleanguard.utils.logging import get_logger

logger = get_logger("privileges")

SW_SHOWNORMAL = 1


def is_user_admin() -> bool:
    """
    Check if the current process possesses elevated Administrator rights.
    Uses shell32.IsUserAnAdmin().
    """
    if sys.platform != "win32":
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception as exc:
        logger.warning(f"IsUserAnAdmin check failed: {exc}")
        return False


def request_elevation(arguments: Optional[List[str]] = None) -> bool:
    """
    Launch an elevated instance of CleanGuard via UAC prompt ("runas" verb).
    Returns True if ShellExecute was successfully dispatched.
    """
    if sys.platform != "win32":
        return False

    if is_user_admin():
        logger.info("Process is already elevated.")
        return True

    try:
        args_str = " ".join(arguments) if arguments else ""
        executable = sys.executable

        h_inst = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            executable,
            args_str,
            None,
            SW_SHOWNORMAL,
        )
        # ShellExecute returns > 32 on success
        return int(h_inst) > 32
    except Exception as exc:
        logger.error(f"Failed to elevate process via ShellExecute: {exc}")
        return False
