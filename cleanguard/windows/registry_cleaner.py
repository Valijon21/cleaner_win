"""
Safe Registry Cleaner and Fixer.
Scans and safely eliminates orphaned MUI caches, Explorer MRU traces, and obsolete associations.
Safety Architecture: Automated .reg backup before any modification, with 1-click rollback.
Strictly avoids touching sensitive system hives (SAM, SECURITY, CLSID, SYSTEM).
"""

import os
import sys
import time
import subprocess
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from cleanguard.windows.known_folders import get_known_folders
from cleanguard.utils.logging import get_logger

logger = get_logger("windows.registry_cleaner")

try:
    import winreg
except ImportError:
    winreg = None

MUI_CACHE_KEY = r"Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\MuiCache"
RUN_MRU_KEY = r"Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU"
TYPED_PATHS_KEY = r"Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths"


@dataclass
class RegistryIssue:
    """Represents a discovered orphaned or obsolete registry value."""
    id: str
    hive_name: str  # "HKCU"
    hive: int
    sub_key: str
    value_name: str
    value_data: Any
    value_type: int
    issue_type: str  # "MuiCache", "RunMRU", "TypedPaths"
    details: str
    target_path: Optional[str] = None


class SafeRegistryCleaner:
    """Safely cleans orphaned registry items with automated backup and rollback."""

    def __init__(self):
        kf = get_known_folders()
        if hasattr(kf, "roaming_app_data"):
            appdata = kf.roaming_app_data
        elif isinstance(kf, dict):
            appdata = kf.get("roaming_app_data", kf.get("appdata", os.path.expanduser("~")))
        else:
            appdata = os.path.expanduser("~")
        self.backup_dir = os.path.join(appdata, "CleanGuard", "Backups")
        os.makedirs(self.backup_dir, exist_ok=True)

    def scan_mui_cache(self) -> List[RegistryIssue]:
        """Scan MuiCache for executables that no longer exist on disk."""
        issues: List[RegistryIssue] = []
        if winreg is None or sys.platform != "win32":
            return issues

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, MUI_CACHE_KEY, 0, winreg.KEY_READ) as key:
                i = 0
                while True:
                    try:
                        v_name, v_data, v_type = winreg.EnumValue(key, i)
                        i += 1
                        # Extract file path before .ApplicationCompany or .FriendlyAppName
                        raw_path = v_name.split(".ApplicationCompany")[0].split(".FriendlyAppName")[0]
                        if raw_path.startswith("C:\\") or raw_path.startswith("D:\\") or ":\\" in raw_path:
                            # Normalize path and check if file exists
                            clean_path = raw_path.strip('"').strip()
                            if not os.path.exists(clean_path):
                                issues.append(
                                    RegistryIssue(
                                        id=f"mui_{i}",
                                        hive_name="HKCU",
                                        hive=winreg.HKEY_CURRENT_USER,
                                        sub_key=MUI_CACHE_KEY,
                                        value_name=v_name,
                                        value_data=v_data,
                                        value_type=v_type,
                                        issue_type="MuiCache",
                                        details=f"O'chirilgan ilovaning kesh yozuvi: {os.path.basename(clean_path)}",
                                        target_path=clean_path,
                                    )
                                )
                    except OSError:
                        break
        except Exception as ex:
            logger.debug("Failed reading MuiCache: %s", ex)

        return issues

    def scan_run_mru(self) -> List[RegistryIssue]:
        """Scan RunMRU (Win+R command history)."""
        issues: List[RegistryIssue] = []
        if winreg is None or sys.platform != "win32":
            return issues

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_MRU_KEY, 0, winreg.KEY_READ) as key:
                i = 0
                while True:
                    try:
                        v_name, v_data, v_type = winreg.EnumValue(key, i)
                        i += 1
                        if v_name.lower() != "mrulist":
                            cmd_str = str(v_data).replace("\\1", "").strip()
                            issues.append(
                                RegistryIssue(
                                    id=f"runmru_{i}",
                                    hive_name="HKCU",
                                    hive=winreg.HKEY_CURRENT_USER,
                                    sub_key=RUN_MRU_KEY,
                                    value_name=v_name,
                                    value_data=v_data,
                                    value_type=v_type,
                                    issue_type="RunMRU",
                                    details=f"Win+R ishga tushirish tarixi: {cmd_str}",
                                )
                            )
                    except OSError:
                        break
        except Exception as ex:
            logger.debug("Failed reading RunMRU: %s", ex)

        return issues

    def scan_typed_paths(self) -> List[RegistryIssue]:
        """Scan Explorer typed paths history."""
        issues: List[RegistryIssue] = []
        if winreg is None or sys.platform != "win32":
            return issues

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, TYPED_PATHS_KEY, 0, winreg.KEY_READ) as key:
                i = 0
                while True:
                    try:
                        v_name, v_data, v_type = winreg.EnumValue(key, i)
                        i += 1
                        issues.append(
                            RegistryIssue(
                                id=f"typed_{i}",
                                hive_name="HKCU",
                                hive=winreg.HKEY_CURRENT_USER,
                                sub_key=TYPED_PATHS_KEY,
                                value_name=v_name,
                                value_data=v_data,
                                value_type=v_type,
                                issue_type="TypedPaths",
                                details=f"Explorer manzil satri tarixi: {v_data}",
                            )
                        )
                    except OSError:
                        break
        except Exception as ex:
            logger.debug("Failed reading TypedPaths: %s", ex)

        return issues

    def scan_all(self) -> List[RegistryIssue]:
        """Run safe scan across all supported registry categories."""
        all_issues = []
        all_issues.extend(self.scan_mui_cache())
        all_issues.extend(self.scan_run_mru())
        all_issues.extend(self.scan_typed_paths())
        return all_issues

    def create_backup(self, issues: List[RegistryIssue]) -> Tuple[bool, str]:
        """
        Generate a standard Windows .reg backup file for the specified issues.
        """
        if not issues:
            return True, ""

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.backup_dir, f"registry_backup_{timestamp}.reg")

        try:
            # Group by hive and subkey
            grouped: Dict[Tuple[str, str], List[RegistryIssue]] = {}
            for iss in issues:
                key = (iss.hive_name, iss.sub_key)
                grouped.setdefault(key, []).append(iss)

            with open(backup_file, "w", encoding="utf-16", errors="replace") as f:
                f.write("Windows Registry Editor Version 5.00\r\n\r\n")
                for (h_name, s_key), items in grouped.items():
                    full_hive = "HKEY_CURRENT_USER" if h_name == "HKCU" else "HKEY_LOCAL_MACHINE"
                    f.write(f"[{full_hive}\\{s_key}]\r\n")
                    for it in items:
                        val_escaped = it.value_name.replace("\\", "\\\\").replace('"', '\\"')
                        if isinstance(it.value_data, int):
                            f.write(f'"{val_escaped}"=dword:{it.value_data:08x}\r\n')
                        else:
                            data_escaped = str(it.value_data).replace("\\", "\\\\").replace('"', '\\"')
                            f.write(f'"{val_escaped}"="{data_escaped}"\r\n')
                    f.write("\r\n")

            logger.info("Registry backup created at: %s", backup_file)
            return True, backup_file
        except Exception as ex:
            logger.error("Failed creating registry backup: %s", ex)
            return False, str(ex)

    def clean_issues(self, issues: List[RegistryIssue], backup: bool = True) -> Tuple[int, int, Optional[str]]:
        """
        Clean the specified registry issues.
        Returns: (deleted_count, failed_count, backup_path_or_none).
        """
        if winreg is None or sys.platform != "win32":
            return 0, len(issues), None

        backup_path = None
        if backup and issues:
            ok, b_path = self.create_backup(issues)
            if ok:
                backup_path = b_path

        deleted = 0
        failed = 0

        # Group by hive and subkey for batch operations
        grouped: Dict[Tuple[int, str], List[RegistryIssue]] = {}
        for it in issues:
            grouped.setdefault((it.hive, it.sub_key), []).append(it)

        for (hive, sub_key), items in grouped.items():
            try:
                with winreg.OpenKey(hive, sub_key, 0, winreg.KEY_SET_VALUE) as key:
                    for it in items:
                        try:
                            winreg.DeleteValue(key, it.value_name)
                            deleted += 1
                        except Exception as ex:
                            logger.debug("Failed deleting registry value %s: %s", it.value_name, ex)
                            failed += 1
            except Exception as ex:
                logger.error("Failed opening key %s for deletion: %s", sub_key, ex)
                failed += len(items)

        logger.info("Registry cleanup complete: %d deleted, %d failed.", deleted, failed)
        return deleted, failed, backup_path

    def restore_backup(self, backup_path: str) -> Tuple[bool, str]:
        """Import a previously exported .reg file using reg import."""
        if not os.path.exists(backup_path):
            return False, "Zaxira fayli topilmadi."

        cmd = ["reg", "import", backup_path]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if proc.returncode == 0:
                logger.info("Successfully restored registry backup %s", backup_path)
                return True, "Zaxira nusxasi muvaffaqiyatli tiklandi."
            else:
                err = proc.stderr.strip() or proc.stdout.strip()
                return False, f"Tiklashda xatolik: {err}"
        except Exception as ex:
            return False, str(ex)

    def get_available_backups(self) -> List[str]:
        """Return list of existing backup files sorted by newest first."""
        if not os.path.exists(self.backup_dir):
            return []
        files = [
            os.path.join(self.backup_dir, f)
            for f in os.listdir(self.backup_dir)
            if f.startswith("registry_backup_") and f.endswith(".reg")
        ]
        files.sort(key=os.path.getmtime, reverse=True)
        return files
