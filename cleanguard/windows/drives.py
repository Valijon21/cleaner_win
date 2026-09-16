"""
Windows Logical Drive Enumeration and Storage Analysis.
Strictly compatible with Windows 7 SP1 through Windows 11.
"""

import os
import sys
import ctypes
from typing import List, Optional
from cleanguard.core.contracts import DriveInfo
from cleanguard.utils.logging import get_logger

logger = get_logger("drives")

# Win32 Drive Types
DRIVE_UNKNOWN = 0
DRIVE_NO_ROOT_DIR = 1
DRIVE_REMOVABLE = 2
DRIVE_FIXED = 3
DRIVE_REMOTE = 4
DRIVE_CDROM = 5
DRIVE_RAMDISK = 6

DRIVE_TYPE_NAMES = {
    DRIVE_UNKNOWN: "Unknown",
    DRIVE_NO_ROOT_DIR: "No Root Directory",
    DRIVE_REMOVABLE: "Removable",
    DRIVE_FIXED: "Fixed Disk",
    DRIVE_REMOTE: "Network Drive",
    DRIVE_CDROM: "CD-ROM",
    DRIVE_RAMDISK: "RAM Disk",
}


def get_system_drive_letter() -> str:
    """Determine Windows system drive letter (e.g. 'C:')."""
    sys_drive = os.environ.get("SystemDrive", "C:")
    return sys_drive.rstrip("\\").upper()


def enumerate_drives() -> List[DriveInfo]:
    """
    Enumerate all logical drives in the system, querying storage space and filesystem info.
    Safe against disconnected or unready media (e.g., empty DVD-ROM, disconnected network drive).
    """
    if sys.platform != "win32":
        # Fallback for mock/test environments
        return [
            DriveInfo(
                letter="C:",
                drive_type="Fixed Disk",
                filesystem="NTFS",
                total_bytes=512 * 1024 * 1024 * 1024,
                free_bytes=256 * 1024 * 1024 * 1024,
                used_bytes=256 * 1024 * 1024 * 1024,
                label="System",
                is_system_drive=True,
                is_ready=True,
            )
        ]

    kernel32 = ctypes.windll.kernel32
    drives: List[DriveInfo] = []
    system_drive = get_system_drive_letter()

    # Disable Windows critical-error-handler dialogs (e.g. "No disk in drive")
    # SEM_FAILCRITICALERRORS = 0x0001
    old_mode = kernel32.SetErrorMode(0x0001)

    try:
        # Buffer length query
        buf_len = kernel32.GetLogicalDriveStringsW(0, None)
        if buf_len == 0:
            logger.warning("GetLogicalDriveStringsW returned 0 bytes buffer.")
            return drives

        buf = ctypes.create_unicode_buffer(buf_len)
        kernel32.GetLogicalDriveStringsW(buf_len, buf)

        # Parse null-separated strings: "C:\\\x00D:\\\x00\x00"
        raw_drives = [d for d in buf.value.split("\x00") if d]

        for drive_path in raw_drives:
            # Ensure format like "C:\"
            drive_root = drive_path.rstrip("\\") + "\\"
            letter = drive_path[:2].upper()

            drive_type_id = kernel32.GetDriveTypeW(drive_root)
            drive_type_name = DRIVE_TYPE_NAMES.get(drive_type_id, "Unknown")

            # Query Volume Information (Label and Filesystem)
            vol_name_buf = ctypes.create_unicode_buffer(261)
            fs_name_buf = ctypes.create_unicode_buffer(261)
            fs_flags = ctypes.c_ulong()
            max_component_len = ctypes.c_ulong()

            vol_ok = kernel32.GetVolumeInformationW(
                drive_root,
                vol_name_buf,
                len(vol_name_buf),
                None,
                ctypes.byref(max_component_len),
                ctypes.byref(fs_flags),
                fs_name_buf,
                len(fs_name_buf),
            )

            is_ready = bool(vol_ok)
            label = vol_name_buf.value if is_ready else ""
            fs_type = fs_name_buf.value if is_ready else "Unknown"

            # Query Disk Free Space (64-bit integers)
            free_user = ctypes.c_ulonglong(0)
            total_bytes = ctypes.c_ulonglong(0)
            free_total = ctypes.c_ulonglong(0)

            space_ok = kernel32.GetDiskFreeSpaceExW(
                drive_root,
                ctypes.byref(free_user),
                ctypes.byref(total_bytes),
                ctypes.byref(free_total),
            )

            tot = total_bytes.value if space_ok else 0
            free = free_total.value if space_ok else 0
            used = max(0, tot - free) if tot > 0 else 0

            drives.append(
                DriveInfo(
                    letter=letter,
                    drive_type=drive_type_name,
                    filesystem=fs_type,
                    total_bytes=tot,
                    free_bytes=free,
                    used_bytes=used,
                    label=label,
                    is_system_drive=(letter == system_drive),
                    is_ready=is_ready and (tot > 0),
                )
            )
    finally:
        # Restore original error mode
        kernel32.SetErrorMode(old_mode)

    return drives


def get_drive_by_letter(letter: str) -> Optional[DriveInfo]:
    """Retrieve DriveInfo for a specific drive letter (e.g. 'C' or 'C:')."""
    clean_letter = letter.rstrip(":\\/").upper() + ":"
    for d in enumerate_drives():
        if d.letter == clean_letter:
            return d
    return None
