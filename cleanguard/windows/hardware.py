"""
Windows Hardware & System Performance Engine.
Zero external bloatware: Uses native Windows Win32 APIs (GetSystemTimes, GlobalMemoryStatusEx, GetTickCount64)
and Windows Registry for processor, GPU, motherboard, and real-time load telemetry.
"""

import os
import sys
import ctypes
from ctypes import wintypes
from typing import Dict, Any, List, Optional
from cleanguard.windows.memory import MemoryOptimizer
from cleanguard.windows.drives import enumerate_drives
from cleanguard.windows.os_info import get_windows_version
from cleanguard.utils.logging import get_logger

logger = get_logger("windows.hardware")

try:
    import winreg
except ImportError:
    winreg = None


class FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]


def _filetime_to_int(ft: FILETIME) -> int:
    return (ft.dwHighDateTime << 32) | ft.dwLowDateTime


class HardwareEngine:
    """Provides hardware specifications and real-time CPU/RAM/Disk metrics."""

    def __init__(self):
        self._prev_idle: int = 0
        self._prev_kernel: int = 0
        self._prev_user: int = 0
        self._init_cpu_baseline()

    def _init_cpu_baseline(self) -> None:
        """Capture initial CPU timestamp counter."""
        if sys.platform != "win32":
            return
        idle, kernel, user = FILETIME(), FILETIME(), FILETIME()
        try:
            if ctypes.windll.kernel32.GetSystemTimes(
                ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)
            ):
                self._prev_idle = _filetime_to_int(idle)
                self._prev_kernel = _filetime_to_int(kernel)
                self._prev_user = _filetime_to_int(user)
        except Exception as ex:
            logger.debug("Error initializing GetSystemTimes: %s", ex)

    def get_cpu_usage_pct(self) -> float:
        """
        Calculate current system-wide CPU utilization percentage since last call.
        """
        if sys.platform != "win32":
            return 0.0

        idle, kernel, user = FILETIME(), FILETIME(), FILETIME()
        try:
            if not ctypes.windll.kernel32.GetSystemTimes(
                ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)
            ):
                return 0.0

            cur_idle = _filetime_to_int(idle)
            cur_kernel = _filetime_to_int(kernel)
            cur_user = _filetime_to_int(user)

            sys_diff = (cur_kernel - self._prev_kernel) + (cur_user - self._prev_user)
            idle_diff = cur_idle - self._prev_idle

            self._prev_idle = cur_idle
            self._prev_kernel = cur_kernel
            self._prev_user = cur_user

            if sys_diff > 0:
                pct = 100.0 * (sys_diff - idle_diff) / sys_diff
                return max(0.0, min(100.0, pct))
            return 0.0
        except Exception as ex:
            logger.debug("Error reading CPU times: %s", ex)
            return 0.0

    def get_memory_metrics(self) -> Dict[str, Any]:
        """Return memory statistics."""
        mem = MemoryOptimizer.get_memory_info()
        return {
            "total_bytes": mem.get("total_bytes", 0),
            "avail_bytes": mem.get("avail_bytes", 0),
            "used_bytes": mem.get("used_bytes", 0),
            "load_pct": mem.get("memory_load_pct", 0),
        }

    def get_system_uptime_seconds(self) -> int:
        """Return system uptime in seconds using GetTickCount64."""
        if sys.platform != "win32":
            return 0
        try:
            uptime_ms = ctypes.windll.kernel32.GetTickCount64()
            return int(uptime_ms // 1000)
        except Exception:
            return 0

    def get_hardware_specs(self) -> Dict[str, Any]:
        """Extract detailed hardware information from Registry and Windows APIs."""
        cpu_name = "Noma'lum protsessor"
        cpu_mhz = 0
        gpus: List[str] = []
        motherboard = "Noma'lum"
        bios_ver = "--"

        if winreg is not None and sys.platform == "win32":
            # 1. CPU
            try:
                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
                ) as k:
                    name_raw, _ = winreg.QueryValueEx(k, "ProcessorNameString")
                    cpu_name = str(name_raw).strip()
                    mhz_raw, _ = winreg.QueryValueEx(k, "~MHz")
                    cpu_mhz = int(mhz_raw)
            except Exception:
                pass

            # 2. GPU
            try:
                gpu_root = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, gpu_root) as k:
                    for idx in range(12):
                        try:
                            sub = winreg.EnumKey(k, idx)
                            with winreg.OpenKey(k, sub) as sub_k:
                                desc, _ = winreg.QueryValueEx(sub_k, "DriverDesc")
                                desc_str = str(desc).strip()
                                if desc_str and desc_str not in gpus:
                                    gpus.append(desc_str)
                        except OSError:
                            pass
            except Exception:
                pass

            # 3. Motherboard & BIOS
            try:
                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\BIOS"
                ) as k:
                    mfg, _ = winreg.QueryValueEx(k, "SystemManufacturer")
                    prod, _ = winreg.QueryValueEx(k, "SystemProductName")
                    bios, _ = winreg.QueryValueEx(k, "BIOSVersion")
                    motherboard = f"{str(mfg).strip()} {str(prod).strip()}"
                    bios_ver = str(bios).strip()
            except Exception:
                pass

        os_info = get_windows_version()
        drives = enumerate_drives()

        return {
            "cpu_name": cpu_name,
            "cpu_cores": os.cpu_count() or 1,
            "cpu_mhz": cpu_mhz,
            "gpus": gpus or ["Standart video kontroller"],
            "motherboard": motherboard,
            "bios_version": bios_ver,
            "os_name": os_info.display_name,
            "os_build": os_info.build,
            "os_arch": os_info.architecture,
            "drives_count": len(drives),
            "uptime_seconds": self.get_system_uptime_seconds(),
        }
