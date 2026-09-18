"""
Windows Installed Applications and Leftover File Manager.
Enumerates installed desktop software from registry hives and safely identifies residual leftover data.
Compatible with Windows 7 SP1, 8, 8.1, 10, and 11.
"""

import os
import shlex
import subprocess
import winreg
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
from cleanguard.core.contracts import ScanItem, CleanCategory, RiskLevel
from cleanguard.security.protected_paths import is_system_critical_path
from cleanguard.utils.filesystem import safe_stat, normalize_path
from cleanguard.utils.logging import get_logger

logger = get_logger("windows.uninstaller")

# Registry keys containing installed software
UNINSTALL_REG_KEYS = [
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall", "HKLM64"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall", "HKLM32"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall", "HKCU"),
]


@dataclass
class InstalledApp:
    """Represents an installed Windows application."""
    id: str
    name: str
    publisher: str
    version: str
    install_date: str
    estimated_size: int  # in bytes
    uninstall_string: str
    install_location: str
    registry_hive: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "publisher": self.publisher,
            "version": self.version,
            "install_date": self.install_date,
            "estimated_size": self.estimated_size,
            "uninstall_string": self.uninstall_string,
            "install_location": self.install_location,
            "registry_hive": self.registry_hive,
        }


class AppUninstallerManager:
    """Service to discover installed software and scan for orphaned leftovers."""

    def __init__(self):
        self.appdata = os.environ.get("APPDATA", "")
        self.localappdata = os.environ.get("LOCALAPPDATA", "")
        self.programdata = os.environ.get("PROGRAMDATA", "")

    def get_installed_apps(self) -> List[InstalledApp]:
        """Query registry hives for installed programs, filtering out hotfixes and system components."""
        apps: Dict[str, InstalledApp] = {}

        for hive, subkey_path, hive_tag in UNINSTALL_REG_KEYS:
            try:
                with winreg.OpenKey(hive, subkey_path, 0, winreg.KEY_READ) as key:
                    num_subkeys = winreg.QueryInfoKey(key)[0]
                    for i in range(num_subkeys):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name, 0, winreg.KEY_READ) as app_key:
                                app = self._parse_app_key(app_key, subkey_name, hive_tag)
                                if app and app.name:
                                    # Use app name as key to avoid duplicate entries across 32/64 bit views
                                    norm_key = app.name.strip().lower()
                                    if norm_key not in apps or (not apps[norm_key].uninstall_string and app.uninstall_string):
                                        apps[norm_key] = app
                        except (OSError, ValueError):
                            continue
            except OSError as ex:
                logger.debug("Cannot open uninstall registry key %s: %s", subkey_path, ex)

        # Sort alphabetically by application name
        return sorted(list(apps.values()), key=lambda a: a.name.lower())

    def _parse_app_key(self, app_key: Any, subkey_name: str, hive_tag: str) -> Optional[InstalledApp]:
        """Extract metadata from an individual application registry subkey."""
        def get_val(name: str, default="") -> str:
            try:
                v, _ = winreg.QueryValueEx(app_key, name)
                return str(v).strip()
            except OSError:
                return default

        def get_int(name: str, default=0) -> int:
            try:
                v, _ = winreg.QueryValueEx(app_key, name)
                return int(v)
            except (OSError, ValueError):
                return default

        # Filter out hidden or system components
        if get_int("SystemComponent") == 1:
            return None

        # Filter out Windows updates
        parent_key = get_val("ParentKeyName")
        if parent_key:
            return None

        name = get_val("DisplayName")
        if not name or name.startswith("KB") and len(name) > 2 and name[2:8].isdigit():
            return None

        uninstall_str = get_val("UninstallString") or get_val("QuietUninstallString")
        if not uninstall_str:
            return None

        version = get_val("DisplayVersion")
        publisher = get_val("Publisher", "Unknown Publisher")
        install_date = get_val("InstallDate")
        install_loc = get_val("InstallLocation")
        size_kb = get_int("EstimatedSize", 0)

        app_id = f"{hive_tag}_{subkey_name}"

        return InstalledApp(
            id=app_id,
            name=name,
            publisher=publisher,
            version=version,
            install_date=install_date,
            estimated_size=size_kb * 1024,
            uninstall_string=uninstall_str,
            install_location=install_loc,
            registry_hive=hive_tag,
        )

    def find_leftovers(self, app_name: str, publisher: Optional[str] = None) -> List[ScanItem]:
        """
        Scan user profile and system data directories for residual folders matching the application name.
        Uses strict boundaries to never suggest deleting protected roots.
        """
        if not app_name or len(app_name.strip()) < 3:
            return []

        clean_name = app_name.strip().lower()
        candidates: List[str] = []

        search_roots = [
            self.localappdata,
            self.appdata,
            self.programdata,
        ]

        for root in search_roots:
            if not root or not os.path.exists(root):
                continue
            try:
                for entry in os.listdir(root):
                    entry_path = os.path.join(root, entry)
                    if not os.path.isdir(entry_path):
                        continue

                    # Direct match
                    if entry.lower() == clean_name or clean_name in entry.lower():
                        candidates.append(entry_path)

                    # Subfolder under publisher
                    if publisher and publisher.lower() in entry.lower():
                        try:
                            for sub_entry in os.listdir(entry_path):
                                sub_path = os.path.join(entry_path, sub_entry)
                                if os.path.isdir(sub_path) and clean_name in sub_entry.lower():
                                    candidates.append(sub_path)
                        except OSError:
                            pass
            except OSError as ex:
                logger.debug("Failed listing root %s for leftovers: %s", root, ex)

        leftover_items: List[ScanItem] = []
        for c_path in set(candidates):
            norm_c = normalize_path(c_path)
            # Must not be a system-critical protected root
            if is_system_critical_path(norm_c):
                continue

            # Calculate total size of directory
            tot_size = 0
            mtime = 0.0
            try:
                for r, _, files in os.walk(c_path):
                    for f in files:
                        f_stat = safe_stat(os.path.join(r, f))
                        if f_stat:
                            tot_size += f_stat.st_size
                            mtime = max(mtime, f_stat.st_mtime)
            except OSError:
                pass

            item = ScanItem(
                path=norm_c,
                name=os.path.basename(c_path),
                size=tot_size,
                modified_at=mtime,
                category=CleanCategory.OTHER.value,
                risk_level=RiskLevel.REVIEW,
                reason=f"Residual application data leftover from '{app_name}'",
                rule_id="RULE-UNINSTALLER-LEFTOVER",
            )
            leftover_items.append(item)

        return leftover_items

    def launch_uninstall(self, app: InstalledApp) -> Tuple[bool, str]:
        """
        Execute the official uninstaller command for an application.
        Launches non-blockingly so the GUI remains responsive.
        """
        if not app.uninstall_string:
            return False, "No uninstall string available for this application."

        try:
            cmd = app.uninstall_string.strip()
            # If command starts with MsiExec.exe, launch directly
            if "msiexec" in cmd.lower():
                subprocess.Popen(cmd, shell=True)
                return True, "Launched Windows Installer uninstallation."

            # Otherwise launch standard uninstaller binary
            subprocess.Popen(cmd, shell=True)
            return True, f"Launched uninstaller for '{app.name}'."
        except Exception as ex:
            logger.error("Failed executing uninstaller for %s: %s", app.name, ex)
            return False, str(ex)
