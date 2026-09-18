"""
Windows Memory & System Resource Optimizer.
Provides RAM trimming via EmptyWorkingSet and real-time memory metrics using Win32 API.
Compatible with Windows 7 SP1, 8, 8.1, 10, and 11.
"""

import ctypes
from ctypes import wintypes
from typing import Dict, Tuple, Any
from cleanguard.utils.logging import get_logger

logger = get_logger("windows.memory")


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_uint64),
        ("ullAvailPhys", ctypes.c_uint64),
        ("ullTotalPageFile", ctypes.c_uint64),
        ("ullAvailPageFile", ctypes.c_uint64),
        ("ullTotalVirtual", ctypes.c_uint64),
        ("ullAvailVirtual", ctypes.c_uint64),
        ("ullAvailExtendedVirtual", ctypes.c_uint64),
    ]


class MemoryOptimizer:
    """Provides memory status and RAM flushing via EmptyWorkingSet."""

    @staticmethod
    def get_memory_info() -> Dict[str, Any]:
        """Query physical RAM usage from Windows kernel."""
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        try:
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                total = stat.ullTotalPhys
                avail = stat.ullAvailPhys
                used = total - avail
                pct = stat.dwMemoryLoad
                return {
                    "total_bytes": total,
                    "avail_bytes": avail,
                    "used_bytes": used,
                    "used_percent": pct,
                }
        except Exception as ex:
            logger.debug("GlobalMemoryStatusEx failed: %s", ex)

        return {
            "total_bytes": 0,
            "avail_bytes": 0,
            "used_bytes": 0,
            "used_percent": 0,
        }

    @staticmethod
    def flush_memory() -> Tuple[int, int]:
        """
        Trim working sets of accessible user-level processes to release physical RAM.
        Returns: (processes_trimmed, bytes_freed_estimate)
        """
        before = MemoryOptimizer.get_memory_info()

        psapi = ctypes.windll.psapi
        kernel32 = ctypes.windll.kernel32

        processes = (wintypes.DWORD * 2048)()
        cb_needed = wintypes.DWORD()

        trimmed_count = 0
        try:
            if psapi.EnumProcesses(ctypes.byref(processes), ctypes.sizeof(processes), ctypes.byref(cb_needed)):
                count = cb_needed.value // ctypes.sizeof(wintypes.DWORD)
                # PROCESS_QUERY_INFORMATION (0x0400) | PROCESS_SET_QUOTA (0x0100)
                desired_access = 0x0400 | 0x0100

                for i in range(count):
                    pid = processes[i]
                    if pid == 0:
                        continue
                    h_process = kernel32.OpenProcess(desired_access, False, pid)
                    if h_process:
                        try:
                            if psapi.EmptyWorkingSet(h_process):
                                trimmed_count += 1
                        finally:
                            kernel32.CloseHandle(h_process)
        except Exception as ex:
            logger.debug("EnumProcesses / EmptyWorkingSet failed: %s", ex)

        after = MemoryOptimizer.get_memory_info()
        freed = max(0, after["avail_bytes"] - before["avail_bytes"])
        logger.info("RAM flush completed: %d processes trimmed, ~%d bytes freed.", trimmed_count, freed)
        return trimmed_count, freed
