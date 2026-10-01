"""
Windows Installed Applications and Leftover File Manager.
Enumerates installed desktop software from registry hives and safely identifies residual leftover data.
Compatible with Windows 7 SP1, 8, 8.1, 10, and 11.
"""

import os
import re
import subprocess
import winreg
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
from cleanguard.core.contracts import ScanItem, CleanCategory, RiskLevel
from cleanguard.security.protected_paths import is_system_critical_path
from cleanguard.utils.filesystem import safe_stat, normalize_path
from cleanguard.windows.shell import is_reparse_point_or_junction
from cleanguard.utils.logging import get_logger
from cleanguard.localization import tr

logger = get_logger("windows.uninstaller")

# Shared vendor / platform folders under AppData and ProgramData. They hold data
# for many applications, so they are never offered as one app's leftover.
SHARED_DATA_FOLDERS = {
    "microsoft", "windows", "packages", "programs", "temp", "google", "mozilla",
    "apple", "adobe", "intel", "nvidia", "amd", "oracle", "java", "package cache",
    "comms", "connecteddevicesplatform", "d3dscache", "crashdumps", "cleanguard",
    "microsoft help", "regid.1991-06.com.microsoft", "ssh", "usoshared", "softwaredistribution",
}

_PARENS_RE = re.compile(r"\(.*?\)|\[.*?\]")
_VERSION_TAIL_RE = re.compile(r"[\s_-]+v?\d+(?:[.\d]*)(?:\s.*)?$", re.IGNORECASE)
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def leftover_match_key(name: str) -> str:
    """
    Reduce an application or folder name to a comparison key:
    "Notepad++ 8.6.4 (64-bit)" -> "notepad". Parenthesised suffixes and trailing
    version numbers are dropped, then everything but [a-z0-9] is removed.
    """
    if not name:
        return ""
    core = _PARENS_RE.sub(" ", name).strip()
    core = _VERSION_TAIL_RE.sub("", core)
    return _NON_ALNUM_RE.sub("", core.lower())

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

    def is_app_installed(self, app: InstalledApp) -> bool:
        """
        Whether the app's Uninstall registry entry still exists.
        Folders of an installed application are live data, not leftovers.
        """
        prefix = f"{app.registry_hive}_"
        subkey_name = app.id[len(prefix):] if app.id.startswith(prefix) else ""
        for hive, subkey_path, hive_tag in UNINSTALL_REG_KEYS:
            if hive_tag != app.registry_hive or not subkey_name:
                continue
            try:
                with winreg.OpenKey(hive, f"{subkey_path}\\{subkey_name}", 0, winreg.KEY_READ):
                    return True
            except OSError:
                return False
        # Unknown origin: be conservative and treat it as still installed.
        return True

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
        app_key = leftover_match_key(app_name or "")
        # Short keys ("Git", "VLC" are fine, "Go"/"R" are not) would match unrelated folders.
        if len(app_key) < 3:
            return []
        publisher_key = leftover_match_key(publisher or "")
        app_keys = {app_key}
        # "Mozilla Firefox" by "Mozilla" is stored as ...\Mozilla\Firefox
        if publisher_key and app_key.startswith(publisher_key) and len(app_key) - len(publisher_key) >= 3:
            app_keys.add(app_key[len(publisher_key):])
        candidates: List[str] = []

        search_roots = [
            self.localappdata,
            self.appdata,
            self.programdata,
        ]

        def is_app_folder(folder_name: str) -> bool:
            # Exact key match only. The previous substring test ("git" in "digital")
            # proposed unrelated applications' data for deletion.
            if folder_name.strip().lower() in SHARED_DATA_FOLDERS:
                return False
            return leftover_match_key(folder_name) in app_keys

        for root in search_roots:
            if not root or not os.path.exists(root):
                continue
            try:
                for entry in os.listdir(root):
                    entry_path = os.path.join(root, entry)
                    if not os.path.isdir(entry_path):
                        continue

                    # Direct match: <root>\<AppName>
                    if is_app_folder(entry):
                        candidates.append(entry_path)
                        continue

                    # Vendor layout: <root>\<Publisher>\<AppName>
                    if publisher_key and len(publisher_key) >= 3 and leftover_match_key(entry) == publisher_key:
                        try:
                            for sub_entry in os.listdir(entry_path):
                                sub_path = os.path.join(entry_path, sub_entry)
                                if os.path.isdir(sub_path) and is_app_folder(sub_entry):
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

            # Never follow a junction out of the AppData tree
            if os.path.islink(c_path) or is_reparse_point_or_junction(c_path):
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
            return False, tr("uninst_no_cmd", "Ushbu dastur uchun o'chirish buyrug'i mavjud emas.")

        try:
            # The command line comes from the registry. Run it directly (no cmd.exe)
            # so shell metacharacters in it are not interpreted.
            cmd = os.path.expandvars(app.uninstall_string.strip())
            subprocess.Popen(cmd, shell=False)
            if "msiexec" in cmd.lower():
                return True, tr("uninst_msi_launched", "Windows Installer orqali o'chirish ishga tushirildi.")
            return True, tr("uninst_launched", "'{name}' uchun o'chirish dasturi ishga tushirildi.", name=app.name)
        except Exception as ex:
            logger.error("Failed executing uninstaller for %s: %s", app.name, ex)
            return False, str(ex)
