"""
Windows Recycle Bin integration via Shell32 APIs.
Supports querying size/items, emptying, and recycling files with undo.
"""

import sys
import ctypes
from dataclasses import dataclass
from typing import Optional
from cleanguard.utils.logging import get_logger

logger = get_logger("recycle_bin")


class SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("i64Size", ctypes.c_int64),
        ("i64NumItems", ctypes.c_int64),
    ]


# SHFileOperation constants
FO_DELETE = 0x0003
FOF_SILENT = 0x0004
FOF_NOCONFIRMATION = 0x0010
FOF_ALLOWUNDO = 0x0040
FOF_NOERRORUI = 0x0400


class SHFILEOPSTRUCTW(ctypes.Structure):
    _fields_ = [
        ("hwnd", ctypes.c_void_p),
        ("wFunc", ctypes.c_uint),
        ("pFrom", ctypes.c_wchar_p),
        ("pTo", ctypes.c_wchar_p),
        ("fFlags", ctypes.c_ushort),
        ("fAnyOperationsAborted", ctypes.c_bool),
        ("hNameMappings", ctypes.c_void_p),
        ("lpszProgressTitle", ctypes.c_wchar_p),
    ]


@dataclass
class RecycleBinInfo:
    """Statistics about Recycle Bin for a drive or entire system."""
    drive: str  # e.g., "C:" or "ALL"
    total_size: int
    num_items: int


def query_recycle_bin(drive_letter: Optional[str] = None) -> RecycleBinInfo:
    """
    Query total size and item count in Recycle Bin.
    If drive_letter is None, queries all drives.
    """
    if sys.platform != "win32":
        return RecycleBinInfo(drive="ALL", total_size=0, num_items=0)

    rb_info = SHQUERYRBINFO()
    rb_info.cbSize = ctypes.sizeof(SHQUERYRBINFO)

    root_path = None
    if drive_letter:
        clean = drive_letter.rstrip(":\\/").upper() + ":\\"
        root_path = clean

    try:
        shell32 = ctypes.windll.shell32
        hr = shell32.SHQueryRecycleBinW(root_path, ctypes.byref(rb_info))
        if hr == 0:
            return RecycleBinInfo(
                drive=drive_letter or "ALL",
                total_size=max(0, rb_info.i64Size),
                num_items=max(0, rb_info.i64NumItems),
            )
        else:
            logger.debug(f"SHQueryRecycleBinW returned error HRESULT: {hr:#x}")
    except Exception as exc:
        logger.warning(f"Failed to query recycle bin: {exc}")

    return RecycleBinInfo(drive=drive_letter or "ALL", total_size=0, num_items=0)


def move_to_recycle_bin(file_path: str) -> bool:
    """
    Send a file or directory to the Windows Recycle Bin using SHFileOperationW with FOF_ALLOWUNDO.
    This guarantees non-destructive cleanup with user recovery capability.
    """
    if sys.platform != "win32":
        return False

    try:
        # SHFileOperation requires double null-terminated string: path + "\0\0"
        double_null_path = file_path + "\x00\x00"

        file_op = SHFILEOPSTRUCTW()
        file_op.hwnd = None
        file_op.wFunc = FO_DELETE
        file_op.pFrom = double_null_path
        file_op.pTo = None
        # FOF_ALLOWUNDO moves to Recycle Bin; FOF_NOCONFIRMATION avoids modal prompts
        file_op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT | FOF_NOERRORUI
        file_op.fAnyOperationsAborted = False

        shell32 = ctypes.windll.shell32
        result = shell32.SHFileOperationW(ctypes.byref(file_op))
        if result == 0 and not file_op.fAnyOperationsAborted:
            return True
        logger.warning(f"SHFileOperationW failed with code {result} for {file_path}")
        return False
    except Exception as exc:
        logger.error(f"Exception moving {file_path} to Recycle Bin: {exc}")
        return False


def empty_recycle_bin(drive_letter: Optional[str] = None, show_confirmation: bool = False) -> bool:
    """
    Empty Recycle Bin on specified drive or all drives.
    """
    if sys.platform != "win32":
        return False

    flags = 0
    if not show_confirmation:
        # SHERB_NOCONFIRMATION = 0x00000001
        # SHERB_NOPROGRESSUI = 0x00000002
        # SHERB_NOSOUND = 0x00000004
        flags = 0x00000001 | 0x00000002 | 0x00000004

    root_path = None
    if drive_letter:
        clean = drive_letter.rstrip(":\\/").upper() + ":\\"
        root_path = clean

    try:
        shell32 = ctypes.windll.shell32
        hr = shell32.SHEmptyRecycleBinW(None, root_path, flags)
        return hr == 0
    except Exception as exc:
        logger.error(f"Failed to empty recycle bin: {exc}")
        return False
