"""
Windows Shell, Reparse Points, Attributes and File Lock Utilities.
Strictly compatible with Windows 7 SP1 through Windows 11.
"""

import sys
import ctypes
from ctypes import wintypes

# Windows File Attributes
FILE_ATTRIBUTE_READONLY = 0x00000001
FILE_ATTRIBUTE_HIDDEN = 0x00000002
FILE_ATTRIBUTE_SYSTEM = 0x00000004
FILE_ATTRIBUTE_DIRECTORY = 0x00000010
FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF

# CreateFile Access & Share Modes
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x80
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

# Error Codes
ERROR_SHARING_VIOLATION = 32
ERROR_LOCK_VIOLATION = 33
ERROR_ACCESS_DENIED = 5

_kernel32 = None


def _get_kernel32():
    """
    Load kernel32 with explicit prototypes.
    Without restype declarations ctypes assumes a signed 32-bit int, which turns
    INVALID_FILE_ATTRIBUTES (0xFFFFFFFF) into -1 and truncates 64-bit HANDLEs.
    """
    global _kernel32
    if _kernel32 is None:
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
        k32.GetFileAttributesW.restype = wintypes.DWORD
        k32.CreateFileW.argtypes = [
            wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
            wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
        ]
        k32.CreateFileW.restype = wintypes.HANDLE
        k32.CloseHandle.argtypes = [wintypes.HANDLE]
        k32.CloseHandle.restype = wintypes.BOOL
        _kernel32 = k32
    return _kernel32


def get_file_attributes(path: str) -> int:
    """Get Win32 file attributes using GetFileAttributesW."""
    if sys.platform != "win32":
        return 0
    try:
        return int(_get_kernel32().GetFileAttributesW(path))
    except Exception:
        return INVALID_FILE_ATTRIBUTES


def is_reparse_point_or_junction(path: str) -> bool:
    """
    Check if a path is a Windows Reparse Point, Junction, or Symbolic Link.
    This prevents recursive traversals from escaping into unintended locations.
    """
    attrs = get_file_attributes(path)
    if attrs == INVALID_FILE_ATTRIBUTES:
        return False
    return bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT)


def is_system_file(path: str) -> bool:
    """Check if file has FILE_ATTRIBUTE_SYSTEM."""
    attrs = get_file_attributes(path)
    if attrs == INVALID_FILE_ATTRIBUTES:
        return False
    return bool(attrs & FILE_ATTRIBUTE_SYSTEM)


def is_file_locked(path: str) -> bool:
    """
    Test if a file is currently locked/opened exclusively by another process.
    Uses Win32 CreateFileW with 0 share mode (exclusive).
    """
    if sys.platform != "win32":
        return False

    attrs = get_file_attributes(path)
    if attrs == INVALID_FILE_ATTRIBUTES or (attrs & FILE_ATTRIBUTE_DIRECTORY):
        # Directories are not locked this way
        return False

    kernel32 = _get_kernel32()
    handle = kernel32.CreateFileW(
        path,
        GENERIC_READ,
        0,  # dwShareMode = 0 (Check if any process is preventing access)
        None,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        None,
    )

    if handle is None or handle == INVALID_HANDLE_VALUE:
        last_error = ctypes.get_last_error()
        if last_error in (ERROR_SHARING_VIOLATION, ERROR_LOCK_VIOLATION, ERROR_ACCESS_DENIED):
            return True
        return False

    # File was successfully opened, close handle immediately
    kernel32.CloseHandle(handle)
    return False
