"""
Windows UAC, Tokens and Administrator Privilege Management.
Strictly compatible with Windows 7 SP1 through Windows 11.
"""

import os
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
    Automatically handles both compiled standalone binaries and Python script invocations.
    Returns True if ShellExecute was successfully dispatched.
    """
    if sys.platform != "win32":
        return False

    if is_user_admin():
        logger.info("Process is already elevated.")
        return True

    try:
        if getattr(sys, "frozen", False):
            # Standalone compiled executable (e.g. PyInstaller CleanGuard.exe)
            executable = sys.executable
            args_str = " ".join(arguments) if arguments is not None else " ".join(f'"{a}"' for a in sys.argv[1:])
        else:
            # Running via python.exe
            executable = sys.executable
            if arguments is not None:
                args_list = arguments
            elif len(sys.argv) > 0 and sys.argv[0].endswith(".py"):
                args_list = [f'"{os.path.abspath(sys.argv[0])}"'] + [f'"{a}"' for a in sys.argv[1:]]
            else:
                args_list = ["-m", "cleanguard.app.main"]
            args_str = " ".join(args_list)

        logger.info(f"Requesting UAC elevation for {executable} with parameters: {args_str}")

        h_inst = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            executable,
            args_str,
            None,
            SW_SHOWNORMAL,
        )
        # ShellExecute returns an integer > 32 on success
        success = int(h_inst) > 32
        if success:
            logger.info("UAC elevation successfully triggered.")
        else:
            logger.warning(f"ShellExecute returned error code: {h_inst}")
        return success
    except Exception as exc:
        logger.error(f"Failed to elevate process via ShellExecute: {exc}")
        return False
