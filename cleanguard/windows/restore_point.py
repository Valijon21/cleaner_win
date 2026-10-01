"""
Windows System Restore Point Service.
Allows creating system snapshots prior to large-scale cleanup operations for recovery.
Uses srclient.dll via ctypes with fallback to PowerShell Checkpoint-Computer.
Compatible with Windows 7 SP1, 8, 8.1, 10, and 11.
"""

import ctypes
from ctypes import wintypes
import subprocess
from typing import Tuple
from cleanguard.utils.logging import get_logger
from cleanguard.windows.privileges import is_user_admin

logger = get_logger("windows.restore_point")

# Restore point constants
BEGIN_SYSTEM_CHANGE = 100
END_SYSTEM_CHANGE = 101
MODIFY_SETTINGS = 12


class RESTOREPOINTINFO(ctypes.Structure):
    _fields_ = [
        ("dwEventType", wintypes.DWORD),
        ("dwRestorePtType", wintypes.DWORD),
        ("llSequenceNumber", ctypes.c_int64),
        ("szDescription", ctypes.c_wchar * 256),
    ]


class STATEMGRSTATUS(ctypes.Structure):
    _fields_ = [
        ("nStatus", wintypes.DWORD),
        ("llSequenceNumber", ctypes.c_int64),
    ]


def _call_srclient(info: RESTOREPOINTINFO, status: STATEMGRSTATUS) -> int:
    return ctypes.windll.srclient.SRSetRestorePointW(ctypes.byref(info), ctypes.byref(status))


def create_restore_point(description: str = "CleanGuard Pre-Clean Snapshot") -> Tuple[bool, str]:
    """
    Create a Windows System Restore Point.
    Returns: (success: bool, message: str)
    """
    # Both SRSetRestorePointW and Checkpoint-Computer require elevation; without it
    # the PowerShell fallback only burns up to 30 seconds before failing.
    if not is_user_admin():
        return False, "Administrator privileges are required to create a restore point."

    try:
        info = RESTOREPOINTINFO()
        info.dwEventType = BEGIN_SYSTEM_CHANGE
        info.dwRestorePtType = MODIFY_SETTINGS
        info.llSequenceNumber = 0
        info.szDescription = description

        status = STATEMGRSTATUS()

        res = _call_srclient(info, status)
        if res and status.nStatus == 0:
            # Every BEGIN_SYSTEM_CHANGE must be closed with END_SYSTEM_CHANGE,
            # otherwise the restore point is left open / incomplete.
            end_info = RESTOREPOINTINFO()
            end_info.dwEventType = END_SYSTEM_CHANGE
            end_info.dwRestorePtType = 0
            end_info.llSequenceNumber = status.llSequenceNumber
            _call_srclient(end_info, STATEMGRSTATUS())
            logger.info("Created system restore point sequence %d", status.llSequenceNumber)
            return True, f"Restore point created successfully (Seq: {status.llSequenceNumber})"
    except Exception as ex:
        logger.debug("srclient.SRSetRestorePointW failed: %s, attempting PowerShell fallback", ex)

    # Fallback to powershell checkpoint command
    try:
        safe_description = description.replace("'", "''")  # PowerShell single-quote escaping
        cmd = [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            f"Checkpoint-Computer -Description '{safe_description}' -RestorePointType MODIFY_SETTINGS -ErrorAction Stop",
        ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if proc.returncode == 0:
            return True, "Restore point created via PowerShell"
        else:
            err = proc.stderr.strip() or proc.stdout.strip()
            return False, f"Failed creating restore point: {err}"
    except Exception as ex:
        return False, str(ex)
