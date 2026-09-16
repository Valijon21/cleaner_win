"""
Windows OS Version, Build, Architecture and Capability Detection.
Strictly compatible with Windows 7 SP1 through Windows 11 and Python 3.8+.
"""

import sys
import os
import platform
import ctypes
from dataclasses import dataclass
from typing import Optional, Dict, Any


class OSVersionInfoExW(ctypes.Structure):
    _fields_ = [
        ("dwOSVersionInfoSize", ctypes.c_ulong),
        ("dwMajorVersion", ctypes.c_ulong),
        ("dwMinorVersion", ctypes.c_ulong),
        ("dwBuildNumber", ctypes.c_ulong),
        ("dwPlatformId", ctypes.c_ulong),
        ("szCSDVersion", ctypes.c_wchar * 128),
        ("wServicePackMajor", ctypes.c_ushort),
        ("wServicePackMinor", ctypes.c_ushort),
        ("wSuiteMask", ctypes.c_ushort),
        ("wProductType", ctypes.c_byte),
        ("wReserved", ctypes.c_byte),
    ]


class SystemInfo(ctypes.Structure):
    _fields_ = [
        ("wProcessorArchitecture", ctypes.c_ushort),
        ("wReserved", ctypes.c_ushort),
        ("dwPageSize", ctypes.c_ulong),
        ("lpMinimumApplicationAddress", ctypes.c_void_p),
        ("lpMaximumApplicationAddress", ctypes.c_void_p),
        ("dwActiveProcessorMask", ctypes.c_void_p),
        ("dwNumberOfProcessors", ctypes.c_ulong),
        ("dwProcessorType", ctypes.c_ulong),
        ("dwAllocationGranularity", ctypes.c_ulong),
        ("wProcessorLevel", ctypes.c_ushort),
        ("wProcessorRevision", ctypes.c_ushort),
    ]


# Architecture constants
PROCESSOR_ARCHITECTURE_INTEL = 0
PROCESSOR_ARCHITECTURE_ARM = 5
PROCESSOR_ARCHITECTURE_IA64 = 6
PROCESSOR_ARCHITECTURE_AMD64 = 9
PROCESSOR_ARCHITECTURE_ARM64 = 12


@dataclass
class OSCapabilities:
    """Feature gate and capabilities map based on OS and build."""
    supports_recycle_bin: bool = True
    supports_known_folder_manager: bool = True
    supports_modern_notifications: bool = False
    supports_per_monitor_v2_dpi: bool = False
    supports_storage_sense_integration: bool = False
    supports_reparse_points: bool = True
    supports_uac: bool = True
    is_supported_by_cleanguard: bool = True


@dataclass
class WindowsVersion:
    """Represents detected Windows operating system details."""
    major: int
    minor: int
    build: int
    service_pack_major: int
    service_pack_minor: int
    product_type: int
    architecture: str
    display_name: str
    is_windows: bool
    capabilities: OSCapabilities

    def to_dict(self) -> Dict[str, Any]:
        return {
            "major": self.major,
            "minor": self.minor,
            "build": self.build,
            "service_pack": f"SP{self.service_pack_major}.{self.service_pack_minor}" if self.service_pack_major > 0 else "None",
            "architecture": self.architecture,
            "display_name": self.display_name,
            "is_windows": self.is_windows,
            "capabilities": self.capabilities.__dict__,
        }


def _get_native_architecture() -> str:
    """Query processor architecture using GetNativeSystemInfo."""
    if sys.platform != "win32":
        return platform.machine()
    
    try:
        kernel32 = ctypes.windll.kernel32
        sys_info = SystemInfo()
        if hasattr(kernel32, "GetNativeSystemInfo"):
            kernel32.GetNativeSystemInfo(ctypes.byref(sys_info))
            arch_id = sys_info.wProcessorArchitecture
            if arch_id == PROCESSOR_ARCHITECTURE_AMD64:
                return "x64"
            elif arch_id == PROCESSOR_ARCHITECTURE_INTEL:
                return "x86"
            elif arch_id == PROCESSOR_ARCHITECTURE_ARM64:
                return "ARM64"
            elif arch_id == PROCESSOR_ARCHITECTURE_ARM:
                return "ARM"
    except Exception:
        pass
    
    # Fallback
    m = platform.machine().lower()
    if "64" in m or "amd64" in m:
        return "x64"
    return "x86"


def get_windows_version() -> WindowsVersion:
    """
    Accurately detect Windows version, build number, and architecture.
    Uses ntdll!RtlGetVersion to bypass manifest version-lying.
    """
    if sys.platform != "win32":
        # Non-windows fallback (for testing/development)
        caps = OSCapabilities(
            supports_recycle_bin=False,
            supports_known_folder_manager=False,
            supports_modern_notifications=False,
            supports_per_monitor_v2_dpi=False,
            supports_storage_sense_integration=False,
            supports_reparse_points=False,
            supports_uac=False,
            is_supported_by_cleanguard=False,
        )
        return WindowsVersion(
            major=0,
            minor=0,
            build=0,
            service_pack_major=0,
            service_pack_minor=0,
            product_type=0,
            architecture=platform.machine(),
            display_name=f"Non-Windows ({sys.platform})",
            is_windows=False,
            capabilities=caps,
        )

    os_version = OSVersionInfoExW()
    os_version.dwOSVersionInfoSize = ctypes.sizeof(OSVersionInfoExW)
    
    major = 0
    minor = 0
    build = 0
    sp_major = 0
    sp_minor = 0
    product_type = 1  # 1 = Workstation / Client

    try:
        # ntdll.RtlGetVersion is the most accurate API in NT
        ntdll = ctypes.windll.ntdll
        if hasattr(ntdll, "RtlGetVersion") and ntdll.RtlGetVersion(ctypes.byref(os_version)) == 0:
            major = os_version.dwMajorVersion
            minor = os_version.dwMinorVersion
            build = os_version.dwBuildNumber
            sp_major = os_version.wServicePackMajor
            sp_minor = os_version.wServicePackMinor
            product_type = os_version.wProductType
    except Exception:
        # Fallback to sys.getwindowsversion()
        try:
            wv = sys.getwindowsversion()
            major = wv.major
            minor = wv.minor
            build = wv.build
            sp_major = wv.service_pack_major if hasattr(wv, "service_pack_major") else 0
            sp_minor = wv.service_pack_minor if hasattr(wv, "service_pack_minor") else 0
        except Exception:
            major, minor, build = 10, 0, 19045

    arch = _get_native_architecture()
    display_name = _determine_display_name(major, minor, build, sp_major, product_type)
    capabilities = _evaluate_capabilities(major, minor, build)

    return WindowsVersion(
        major=major,
        minor=minor,
        build=build,
        service_pack_major=sp_major,
        service_pack_minor=sp_minor,
        product_type=product_type,
        architecture=arch,
        display_name=display_name,
        is_windows=True,
        capabilities=capabilities,
    )


def _determine_display_name(major: int, minor: int, build: int, sp_major: int, product_type: int) -> str:
    """Derive friendly Windows commercial name."""
    is_server = product_type != 1

    if major == 10:
        if build >= 22000:
            return "Windows Server 2022/2025" if is_server else "Windows 11"
        return "Windows Server 2016/2019/2022" if is_server else "Windows 10"
    elif major == 6:
        if minor == 3:
            return "Windows Server 2012 R2" if is_server else "Windows 8.1"
        elif minor == 2:
            return "Windows Server 2012" if is_server else "Windows 8"
        elif minor == 1:
            sp_text = f" SP{sp_major}" if sp_major > 0 else ""
            return f"Windows Server 2008 R2{sp_text}" if is_server else f"Windows 7{sp_text}"
        elif minor == 0:
            return "Windows Server 2008" if is_server else "Windows Vista"
    elif major == 5:
        return "Windows XP / Server 2003 (Legacy Unsupported)"

    return f"Windows {major}.{minor} (Build {build})"


def _evaluate_capabilities(major: int, minor: int, build: int) -> OSCapabilities:
    """Build capability flags for this Windows release."""
    caps = OSCapabilities()

    # Supported: Win 7 (6.1) up to Win 11
    if major < 6 or (major == 6 and minor < 1):
        caps.is_supported_by_cleanguard = False
    else:
        caps.is_supported_by_cleanguard = True

    # Windows 10 build 10240+ has toast notification APIs
    caps.supports_modern_notifications = (major >= 10)

    # Windows 10 Creators Update (1703, build 15063+) supports Per-Monitor V2 DPI
    caps.supports_per_monitor_v2_dpi = (major >= 10 and build >= 15063)

    # Windows 10 1709 (build 16299+) supports Storage Sense
    caps.supports_storage_sense_integration = (major >= 10 and build >= 16299)

    return caps
