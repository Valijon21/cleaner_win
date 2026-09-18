"""
Windows Startup Items Manager.
Enumerates and manages autorun/startup entries from Windows Registry and Startup folders.
Compatible with Windows 7 SP1, 8, 8.1, 10, and 11.
"""

import os
import sys
import winreg
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
from cleanguard.core.contracts import RiskLevel
from cleanguard.utils.logging import get_logger

logger = get_logger("windows.startup")

# Critical Windows binaries that must never be disabled
CRITICAL_STARTUP_BINARIES = {
    "ctfmon.exe",
    "securityhealthsystray.exe",
    "securityhealthhost.exe",
    "explorer.exe",
    "cmd.exe",
    "conhost.exe",
    "dwm.exe",
    "lsass.exe",
    "services.exe",
    "svchost.exe",
}

# Registry paths for startup
REG_HKCU_RUN = r"Software\Microsoft\Windows\CurrentVersion\Run"
REG_HKLM_RUN = r"Software\Microsoft\Windows\CurrentVersion\Run"
REG_CLEANGUARD_BACKUP = r"Software\CleanGuard\DisabledStartup"
REG_STARTUP_APPROVED = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"


@dataclass
class StartupItem:
    """Represents a Windows Startup application."""
    id: str
    name: str
    command: str
    location_type: str  # "HKCU_RUN", "HKLM_RUN", "USER_FOLDER", "COMMON_FOLDER"
    enabled: bool
    risk_level: RiskLevel
    impact: str  # "High", "Medium", "Low", "None"
    publisher: Optional[str] = None
    target_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "command": self.command,
            "location_type": self.location_type,
            "enabled": self.enabled,
            "risk_level": self.risk_level.value,
            "impact": self.impact,
            "publisher": self.publisher or "Unknown",
            "target_path": self.target_path or "",
        }


class StartupManager:
    """Service to discover, analyze and toggle Windows startup programs."""

    def __init__(self):
        self.user_startup_dir = self._get_user_startup_dir()
        self.common_startup_dir = self._get_common_startup_dir()

    def _get_user_startup_dir(self) -> str:
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            return os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup")
        return ""

    def _get_common_startup_dir(self) -> str:
        programdata = os.environ.get("PROGRAMDATA", "")
        if programdata:
            return os.path.join(programdata, r"Microsoft\Windows\Start Menu\Programs\Startup")
        return ""

    def get_all_startup_items(self) -> List[StartupItem]:
        """Enumerate startup items across all supported locations."""
        items: List[StartupItem] = []

        # 1. HKCU Run
        items.extend(self._scan_registry_key(winreg.HKEY_CURRENT_USER, REG_HKCU_RUN, "HKCU_RUN"))

        # 2. HKLM Run
        items.extend(self._scan_registry_key(winreg.HKEY_LOCAL_MACHINE, REG_HKLM_RUN, "HKLM_RUN"))

        # 3. CleanGuard Disabled Key (to show currently disabled items)
        items.extend(self._scan_disabled_backup_keys())

        # 4. User Startup Folder
        if self.user_startup_dir and os.path.isdir(self.user_startup_dir):
            items.extend(self._scan_folder(self.user_startup_dir, "USER_FOLDER"))

        # 5. Common Startup Folder
        if self.common_startup_dir and os.path.isdir(self.common_startup_dir):
            items.extend(self._scan_folder(self.common_startup_dir, "COMMON_FOLDER"))

        # Deduplicate items by ID
        unique_items: Dict[str, StartupItem] = {}
        for it in items:
            unique_items[it.id] = it

        return list(unique_items.values())

    def _scan_registry_key(self, hive: int, subkey: str, loc_type: str) -> List[StartupItem]:
        items: List[StartupItem] = []
        try:
            with winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ) as key:
                num_values = winreg.QueryInfoKey(key)[1]
                for i in range(num_values):
                    try:
                        name, val, _ = winreg.EnumValue(key, i)
                        if not name:
                            continue
                        command = str(val).strip()
                        target_path = self._extract_executable_path(command)
                        risk = self._assess_risk(name, target_path)
                        impact = self._estimate_impact(name, command)
                        publisher = self._detect_publisher(name, target_path)

                        item_id = f"{loc_type}_{name}"
                        items.append(
                            StartupItem(
                                id=item_id,
                                name=name,
                                command=command,
                                location_type=loc_type,
                                enabled=True,
                                risk_level=risk,
                                impact=impact,
                                publisher=publisher,
                                target_path=target_path,
                            )
                        )
                    except (OSError, ValueError) as err:
                        logger.debug("Failed reading registry value index %d: %s", i, err)
        except OSError as err:
            logger.debug("Cannot open registry key %s: %s", subkey, err)

        return items

    def _scan_disabled_backup_keys(self) -> List[StartupItem]:
        """Scan items previously disabled by CleanGuard."""
        items: List[StartupItem] = []
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_CLEANGUARD_BACKUP, 0, winreg.KEY_READ) as key:
                num_subkeys = winreg.QueryInfoKey(key)[0]
                for s in range(num_subkeys):
                    sub_name = winreg.EnumKey(key, s)
                    try:
                        with winreg.OpenKey(key, sub_name, 0, winreg.KEY_READ) as item_key:
                            name, _ = winreg.QueryValueEx(item_key, "Name")
                            cmd, _ = winreg.QueryValueEx(item_key, "Command")
                            loc_type, _ = winreg.QueryValueEx(item_key, "OrigLocation")
                            target_path = self._extract_executable_path(cmd)
                            risk = self._assess_risk(name, target_path)
                            impact = self._estimate_impact(name, cmd)

                            item_id = f"{loc_type}_{name}"
                            items.append(
                                StartupItem(
                                    id=item_id,
                                    name=name,
                                    command=cmd,
                                    location_type=loc_type,
                                    enabled=False,
                                    risk_level=risk,
                                    impact=impact,
                                    target_path=target_path,
                                )
                            )
                    except OSError:
                        continue
        except OSError:
            pass
        return items

    def _scan_folder(self, folder_path: str, loc_type: str) -> List[StartupItem]:
        items: List[StartupItem] = []
        try:
            for entry in os.listdir(folder_path):
                if entry.lower() in ("desktop.ini", "thumbs.db"):
                    continue
                full_path = os.path.join(folder_path, entry)
                is_disabled = entry.endswith(".disabled")
                clean_name = entry[:-9] if is_disabled else entry
                risk = self._assess_risk(clean_name, full_path)
                impact = self._estimate_impact(clean_name, full_path)

                item_id = f"{loc_type}_{clean_name}"
                items.append(
                    StartupItem(
                        id=item_id,
                        name=clean_name,
                        command=full_path,
                        location_type=loc_type,
                        enabled=not is_disabled,
                        risk_level=risk,
                        impact=impact,
                        target_path=full_path,
                    )
                )
        except OSError as err:
            logger.debug("Cannot scan startup folder %s: %s", folder_path, err)
        return items

    def set_startup_state(self, item: StartupItem, enabled: bool) -> Tuple[bool, str]:
        """
        Enable or disable a startup item safely.
        Never deletes information — stores disabled state in CleanGuard backup registry key.
        """
        if item.risk_level == RiskLevel.BLOCKED:
            return False, "This is a critical Windows system item and cannot be disabled."

        if item.enabled == enabled:
            return True, "No change required"

        try:
            if item.location_type == "HKCU_RUN":
                return self._toggle_hkcu_run(item, enabled)
            elif item.location_type in ("USER_FOLDER", "COMMON_FOLDER"):
                return self._toggle_folder_item(item, enabled)
            elif item.location_type == "HKLM_RUN":
                return self._toggle_hklm_run(item, enabled)
            else:
                return False, f"Unsupported location type: {item.location_type}"
        except Exception as ex:
            logger.error("Failed toggling startup state for %s: %s", item.name, ex)
            return False, str(ex)

    def _toggle_hkcu_run(self, item: StartupItem, enabled: bool) -> Tuple[bool, str]:
        if not enabled:
            # Save to CleanGuard backup
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{REG_CLEANGUARD_BACKUP}\\{item.name}") as bkey:
                winreg.SetValueEx(bkey, "Name", 0, winreg.REG_SZ, item.name)
                winreg.SetValueEx(bkey, "Command", 0, winreg.REG_SZ, item.command)
                winreg.SetValueEx(bkey, "OrigLocation", 0, winreg.REG_SZ, "HKCU_RUN")

            # Remove from active Run key
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_HKCU_RUN, 0, winreg.KEY_SET_VALUE) as rkey:
                    winreg.DeleteValue(rkey, item.name)
            except FileNotFoundError:
                pass
            item.enabled = False
            return True, "Successfully disabled"
        else:
            # Restore to active Run key
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_HKCU_RUN, 0, winreg.KEY_SET_VALUE) as rkey:
                winreg.SetValueEx(rkey, item.name, 0, winreg.REG_SZ, item.command)

            # Remove from backup key
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"{REG_CLEANGUARD_BACKUP}\\{item.name}")
            except OSError:
                pass
            item.enabled = True
            return True, "Successfully enabled"

    def _toggle_hklm_run(self, item: StartupItem, enabled: bool) -> Tuple[bool, str]:
        # Modifying HKLM requires elevated administrator privileges
        try:
            if not enabled:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{REG_CLEANGUARD_BACKUP}\\{item.name}") as bkey:
                    winreg.SetValueEx(bkey, "Name", 0, winreg.REG_SZ, item.name)
                    winreg.SetValueEx(bkey, "Command", 0, winreg.REG_SZ, item.command)
                    winreg.SetValueEx(bkey, "OrigLocation", 0, winreg.REG_SZ, "HKLM_RUN")

                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_HKLM_RUN, 0, winreg.KEY_SET_VALUE) as rkey:
                    winreg.DeleteValue(rkey, item.name)
                item.enabled = False
                return True, "Successfully disabled"
            else:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_HKLM_RUN, 0, winreg.KEY_SET_VALUE) as rkey:
                    winreg.SetValueEx(rkey, item.name, 0, winreg.REG_SZ, item.command)

                try:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"{REG_CLEANGUARD_BACKUP}\\{item.name}")
                except OSError:
                    pass
                item.enabled = True
                return True, "Successfully enabled"
        except PermissionError:
            return False, "Administrator privileges required to modify HKLM startup items."

    def _toggle_folder_item(self, item: StartupItem, enabled: bool) -> Tuple[bool, str]:
        current_path = item.command
        if not os.path.exists(current_path):
            return False, "File not found"

        if not enabled:
            if not current_path.endswith(".disabled"):
                new_path = current_path + ".disabled"
                os.rename(current_path, new_path)
                item.command = new_path
                item.enabled = False
                return True, "Successfully disabled"
        else:
            if current_path.endswith(".disabled"):
                new_path = current_path[:-9]
                os.rename(current_path, new_path)
                item.command = new_path
                item.enabled = True
                return True, "Successfully enabled"

        return True, "Already in target state"

    def _extract_executable_path(self, command: str) -> str:
        """Extract clean file path from arbitrary command line string."""
        if not command:
            return ""
        cmd = command.strip()
        if cmd.startswith('"'):
            end_quote = cmd.find('"', 1)
            if end_quote != -1:
                return cmd[1:end_quote]
        parts = cmd.split(" ")
        return parts[0]

    def _assess_risk(self, name: str, target_path: Optional[str]) -> RiskLevel:
        name_lower = name.lower()
        if target_path:
            base_name = os.path.basename(target_path).lower()
            if base_name in CRITICAL_STARTUP_BINARIES:
                return RiskLevel.BLOCKED

            normalized = target_path.lower().replace("/", "\\")
            if "\\windows\\system32\\" in normalized or "\\windows\\syswow64\\" in normalized:
                return RiskLevel.BLOCKED

        for crit in CRITICAL_STARTUP_BINARIES:
            if crit in name_lower:
                return RiskLevel.BLOCKED

        return RiskLevel.REVIEW

    def _estimate_impact(self, name: str, command: str) -> str:
        """Estimate boot impact for user guidance."""
        cmd_lower = command.lower()
        heavy_signatures = ["steam", "epicgames", "discord", "spotify", "teams", "adobe", "chrome", "firefox"]
        for sig in heavy_signatures:
            if sig in cmd_lower or sig in name.lower():
                return "High"

        medium_signatures = ["updater", "tray", "assistant", "cloud", "sync", "service"]
        for sig in medium_signatures:
            if sig in cmd_lower or sig in name.lower():
                return "Medium"

        return "Low"

    def _detect_publisher(self, name: str, target_path: Optional[str]) -> str:
        path_lower = (target_path or "").lower()
        if "microsoft" in path_lower or "windows" in path_lower:
            return "Microsoft Corporation"
        if "google" in path_lower:
            return "Google LLC"
        if "mozilla" in path_lower:
            return "Mozilla Corporation"
        if "adobe" in path_lower:
            return "Adobe Inc."
        if "telegram" in path_lower:
            return "Telegram FZ-LLC"
        if "discord" in path_lower:
            return "Discord Inc."
        return "Unknown Application"
