"""
Windows Network and Internet Optimizer.
Provides DNS cache flushing, TCP/IP stack tuning, multimedia network throttling bypass,
and real-time latency diagnostics.
"""

import sys
import subprocess
import re
from typing import Tuple, List, Dict, Optional
from cleanguard.windows.privileges import is_user_admin
from cleanguard.utils.logging import get_logger

logger = get_logger("windows.network")

try:
    import winreg
except ImportError:
    winreg = None

MULTIMEDIA_PROFILE_KEY = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"


class NetworkOptimizer:
    """Manages Windows network optimizations and diagnostics."""

    @staticmethod
    def flush_dns() -> Tuple[bool, str]:
        """Flush the Windows DNS resolver cache."""
        if sys.platform != "win32":
            return False, "Faqat Windows tizimlarida ishlaydi."

        cmd = ["ipconfig", "/flushdns"]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if proc.returncode == 0:
                logger.info("DNS resolver cache flushed successfully.")
                return True, "DNS keshi muvaffaqiyatli tozalandi."
            else:
                err = proc.stderr.strip() or proc.stdout.strip()
                return False, f"DNS tozalashda xatolik: {err}"
        except Exception as ex:
            logger.error("Error flushing DNS: %s", ex)
            return False, str(ex)

    @staticmethod
    def optimize_tcp_ip() -> Tuple[bool, str]:
        """
        Optimize TCP/IP settings using netsh:
        - autotuninglevel=normal (dynamic TCP receive window)
        - rss=enabled (Receive Side Scaling for multi-core packet processing)
        - heuristics=disabled (prevents random throttling)
        """
        if sys.platform != "win32":
            return False, "Faqat Windows tizimlarida ishlaydi."

        if not is_user_admin():
            return False, "TCP/IP sozlamalarini o'zgartirish uchun Administrator huquqi talab qilinadi."

        commands = [
            ["netsh", "int", "tcp", "set", "global", "autotuninglevel=normal"],
            ["netsh", "int", "tcp", "set", "global", "rss=enabled"],
            ["netsh", "int", "tcp", "set", "heuristics", "disabled"],
        ]

        errors = []
        for cmd in commands:
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                if proc.returncode != 0:
                    errors.append(proc.stderr.strip() or proc.stdout.strip())
            except Exception as ex:
                errors.append(str(ex))

        if not errors:
            logger.info("TCP/IP stack optimized successfully.")
            return True, "TCP/IP stacki muvaffaqiyatli optimallashtirildi."
        else:
            return False, f"TCP/IP xatosi: {'; '.join(errors)}"

    @staticmethod
    def is_throttling_disabled() -> bool:
        """Check if Windows Multimedia Network Throttling is disabled."""
        if winreg is None or sys.platform != "win32":
            return False

        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, MULTIMEDIA_PROFILE_KEY, 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, "NetworkThrottlingIndex")
                # 0xffffffff (4294967295) means throttling is disabled
                return val == 0xFFFFFFFF or val == -1
        except (FileNotFoundError, OSError):
            return False

    @staticmethod
    def disable_network_throttling() -> Tuple[bool, str]:
        """
        Disable Windows Multimedia Network Throttling.
        Sets NetworkThrottlingIndex = 0xffffffff and SystemResponsiveness = 0 in HKLM Multimedia Profile.
        """
        if winreg is None or sys.platform != "win32":
            return False, "Faqat Windows tizimlarida ishlaydi."

        if not is_user_admin():
            return False, "Ushbu parametrni o'zgartirish uchun Administrator huquqi talab qilinadi."

        try:
            with winreg.CreateKeyEx(
                winreg.HKEY_LOCAL_MACHINE,
                MULTIMEDIA_PROFILE_KEY,
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                winreg.SetValueEx(key, "NetworkThrottlingIndex", 0, winreg.REG_DWORD, 0xFFFFFFFF)
                winreg.SetValueEx(key, "SystemResponsiveness", 0, winreg.REG_DWORD, 0)
            logger.info("Network throttling disabled and SystemResponsiveness set to 0.")
            return True, "Tarmoq cheklovi (throttling) muvaffaqiyatli olib tashlandi."
        except PermissionError:
            return False, "Ruxsat yetarli emas. CleanGuard ni Administrator sifatida ishga tushiring."
        except Exception as ex:
            logger.error("Error setting network throttling index: %s", ex)
            return False, str(ex)

    @staticmethod
    def check_ping(host: str = "1.1.1.1") -> Tuple[bool, float, str]:
        """
        Measure network round-trip latency in milliseconds using ping.
        Returns: (success, latency_ms, detail_str).
        """
        cmd = ["ping", "-n", "2", "-w", "1000", host]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if proc.returncode == 0 and proc.stdout:
                # Search for Average = XXms or time=XXms
                match = re.search(r"Average\s*=\s*(\d+)ms", proc.stdout) or re.search(r"time[<=](\d+)ms", proc.stdout)
                if match:
                    latency = float(match.group(1))
                    return True, latency, f"Ping {host}: {latency:.0f} ms"
                return True, 10.0, f"Ping {host}: muvaffaqiyatli"
            return False, 999.0, f"{host} ga ulanib bo'lmadi (Timeout)."
        except Exception as ex:
            return False, 999.0, str(ex)

    @staticmethod
    def get_network_interfaces() -> List[Dict[str, str]]:
        """Get summary of active network adapters via ipconfig."""
        if sys.platform != "win32":
            return []

        adapters = []
        try:
            proc = subprocess.run(
                ["ipconfig"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if proc.returncode == 0:
                current_adapter = None
                for line in proc.stdout.splitlines():
                    line_str = line.strip()
                    if "adapter" in line.lower() and line.endswith(":"):
                        current_adapter = line.replace(":", "").strip()
                    elif "IPv4" in line_str and current_adapter:
                        ip = line_str.split(":")[-1].strip()
                        adapters.append({"name": current_adapter, "ip": ip, "status": "Faol (Online)"})
                        current_adapter = None
        except Exception as ex:
            logger.debug("Error getting adapters: %s", ex)

        return adapters


# Module-level convenience functions
flush_dns = NetworkOptimizer.flush_dns
optimize_tcp_ip = NetworkOptimizer.optimize_tcp_ip
