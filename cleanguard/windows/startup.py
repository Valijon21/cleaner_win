"""
Windows Startup Items Manager.
Enumerates and manages autorun/startup entries from Windows Registry, Startup folders,
Windows 10/11 Task Manager StartupApproved keys, and Scheduled Tasks (Logon/Startup).
Compatible with Windows 7 SP1, 8, 8.1, 10, and 11.
"""

import os
import sys
import csv
import io
import re
import subprocess
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
REG_HKLM_WOW64_RUN = r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"
REG_HKCU_WOW64_RUN = r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"
REG_CLEANGUARD_BACKUP = r"Software\CleanGuard\DisabledStartup"

REG_STARTUP_APPROVED_HKCU_RUN = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"
REG_STARTUP_APPROVED_HKLM_RUN = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"
REG_STARTUP_APPROVED_HKLM_RUN32 = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run32"
REG_STARTUP_APPROVED_HKCU_FOLDER = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder"
REG_STARTUP_APPROVED_HKLM_FOLDER = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder"


@dataclass
class StartupItem:
    """Represents a Windows Startup application or scheduled logon task."""
    id: str
    name: str
    command: str
    location_type: str  # "HKCU_RUN", "HKLM_RUN", "HKLM_WOW64_RUN", "USER_FOLDER", "COMMON_FOLDER", "SCHEDULED_TASK"
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
    """Service to discover, analyze and toggle Windows startup programs and tasks."""

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
        """
        Enumerate startup items across all supported locations:
        - HKCU Run (64-bit and 32-bit)
        - HKLM Run (64-bit and 32-bit WOW6432Node)
        - Windows 10/11 Task Manager StartupApproved synchronization
        - User and Common Startup folders (.lnk shortcuts)
        - Windows Task Scheduler logon and startup tasks
        - CleanGuard disabled backup keys
        """
        items: List[StartupItem] = []

        # 1. HKCU Run
        items.extend(
            self._scan_registry_key(
                winreg.HKEY_CURRENT_USER,
                REG_HKCU_RUN,
                "HKCU_RUN",
                approved_key=REG_STARTUP_APPROVED_HKCU_RUN,
            )
        )

        # 2. HKLM Run (64-bit)
        access_64 = winreg.KEY_READ | getattr(winreg, "KEY_WOW64_64KEY", 0)
        items.extend(
            self._scan_registry_key(
                winreg.HKEY_LOCAL_MACHINE,
                REG_HKLM_RUN,
                "HKLM_RUN",
                approved_key=REG_STARTUP_APPROVED_HKLM_RUN,
                access_flags=access_64,
            )
        )

        # 3. HKLM WOW6432Node Run (32-bit on 64-bit Windows)
        access_32 = winreg.KEY_READ | getattr(winreg, "KEY_WOW64_32KEY", 0)
        items.extend(
            self._scan_registry_key(
                winreg.HKEY_LOCAL_MACHINE,
                REG_HKLM_WOW64_RUN,
                "HKLM_WOW64_RUN",
                approved_key=REG_STARTUP_APPROVED_HKLM_RUN32,
                access_flags=access_32,
            )
        )

        # 4. HKCU WOW6432Node Run
        items.extend(
            self._scan_registry_key(
                winreg.HKEY_CURRENT_USER,
                REG_HKCU_WOW64_RUN,
                "HKCU_WOW64_RUN",
                approved_key=REG_STARTUP_APPROVED_HKCU_RUN,
            )
        )

        # 5. CleanGuard Disabled Backup Keys
        items.extend(self._scan_disabled_backup_keys())

        # 6. User Startup Folder
        if self.user_startup_dir and os.path.isdir(self.user_startup_dir):
            items.extend(
                self._scan_folder(
                    self.user_startup_dir,
                    "USER_FOLDER",
                    approved_hive=winreg.HKEY_CURRENT_USER,
                    approved_key=REG_STARTUP_APPROVED_HKCU_FOLDER,
                )
            )

        # 7. Common Startup Folder
        if self.common_startup_dir and os.path.isdir(self.common_startup_dir):
            items.extend(
                self._scan_folder(
                    self.common_startup_dir,
                    "COMMON_FOLDER",
                    approved_hive=winreg.HKEY_LOCAL_MACHINE,
                    approved_key=REG_STARTUP_APPROVED_HKLM_FOLDER,
                )
            )

        # 8. Windows Task Scheduler Logon & Startup Tasks
        items.extend(self._scan_scheduled_tasks())

        # Deduplicate items by ID
        unique_items: Dict[str, StartupItem] = {}
        for it in items:
            unique_items[it.id] = it

        return list(unique_items.values())

    def _is_approved_enabled(self, hive: int, approved_subkey: Optional[str], value_name: str) -> bool:
        """
        Check Windows Task Manager's StartupApproved binary registry key.
        If first byte is even (0x02, 0x06), item is enabled.
        If first byte is odd (0x01, 0x03), item was disabled by user in Task Manager / Windows Settings.
        """
        if not approved_subkey:
            return True
        try:
            with winreg.OpenKey(hive, approved_subkey, 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, value_name)
                if isinstance(val, (bytes, bytearray)) and len(val) > 0:
                    return (val[0] % 2) == 0
        except OSError:
            pass
        return True

    def _set_approved_state(self, hive: int, approved_subkey: str, value_name: str, enabled: bool) -> bool:
        """Update or create Windows Task Manager StartupApproved registry flag."""
        try:
            with winreg.CreateKeyEx(hive, approved_subkey, 0, winreg.KEY_READ | winreg.KEY_SET_VALUE) as key:
                try:
                    val, vtype = winreg.QueryValueEx(key, value_name)
                    if isinstance(val, (bytes, bytearray)) and len(val) >= 4:
                        b = bytearray(val)
                        b[0] = 0x02 if enabled else 0x03
                        winreg.SetValueEx(key, value_name, 0, vtype, bytes(b))
                        return True
                except FileNotFoundError:
                    pass

                payload = bytearray(12)
                payload[0] = 0x02 if enabled else 0x03
                winreg.SetValueEx(key, value_name, 0, winreg.REG_BINARY, bytes(payload))
                return True
        except OSError as err:
            logger.debug("Cannot update StartupApproved for %s: %s", value_name, err)
            return False

    def _scan_registry_key(
        self,
        hive: int,
        subkey: str,
        loc_type: str,
        approved_key: Optional[str] = None,
        access_flags: int = winreg.KEY_READ,
    ) -> List[StartupItem]:
        items: List[StartupItem] = []
        try:
            with winreg.OpenKey(hive, subkey, 0, access_flags) as key:
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

                        # Check if Windows Task Manager disabled this item via StartupApproved
                        is_enabled = self._is_approved_enabled(hive, approved_key, name)

                        item_id = f"{loc_type}_{name}"
                        items.append(
                            StartupItem(
                                id=item_id,
                                name=name,
                                command=command,
                                location_type=loc_type,
                                enabled=is_enabled,
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
        """Scan items previously disabled and stored in CleanGuard backup registry."""
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
                            publisher = self._detect_publisher(name, target_path)

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
                                    publisher=publisher,
                                    target_path=target_path,
                                )
                            )
                    except OSError:
                        continue
        except OSError:
            pass
        return items

    def _scan_folder(
        self,
        folder_path: str,
        loc_type: str,
        approved_hive: int = winreg.HKEY_CURRENT_USER,
        approved_key: Optional[str] = None,
    ) -> List[StartupItem]:
        items: List[StartupItem] = []
        try:
            for entry in os.listdir(folder_path):
                if entry.lower() in ("desktop.ini", "thumbs.db"):
                    continue
                full_path = os.path.join(folder_path, entry)
                is_disabled_file = entry.endswith(".disabled")

                # Clean display name: remove .disabled and .lnk extensions
                clean_name = entry
                if is_disabled_file:
                    clean_name = clean_name[:-9]
                if clean_name.lower().endswith(".lnk"):
                    clean_name = clean_name[:-4]

                # Resolve target binary from shortcut if possible
                target_path = self._resolve_shortcut_target(full_path)
                if not target_path:
                    target_path = full_path

                risk = self._assess_risk(clean_name, target_path)
                impact = self._estimate_impact(clean_name, target_path)
                publisher = self._detect_publisher(clean_name, target_path)

                # Check Windows Task Manager StartupApproved for startup folder items
                approved_name = entry[:-9] if is_disabled_file else entry
                is_enabled = not is_disabled_file and self._is_approved_enabled(approved_hive, approved_key, approved_name)

                item_id = f"{loc_type}_{clean_name}"
                items.append(
                    StartupItem(
                        id=item_id,
                        name=clean_name,
                        command=full_path,
                        location_type=loc_type,
                        enabled=is_enabled,
                        risk_level=risk,
                        impact=impact,
                        publisher=publisher,
                        target_path=target_path,
                    )
                )
        except OSError as err:
            logger.debug("Cannot scan startup folder %s: %s", folder_path, err)
        return items

    def _scan_scheduled_tasks(self) -> List[StartupItem]:
        """
        Enumerate logon, startup, and third-party scheduled tasks using schtasks.exe.
        Captures vendor updaters, OEM control centers, and background tools that bypass registry Run.
        """
        items: List[StartupItem] = []
        try:
            cmd = ["schtasks.exe", "/query", "/fo", "CSV", "/v"]
            res = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")
            if res.returncode != 0 or not res.stdout:
                return items

            reader = csv.DictReader(io.StringIO(res.stdout))
            seen_tasks = set()

            for row in reader:
                t_name = row.get("TaskName", "").strip()
                if not t_name or t_name.lower() in ("taskname", ""):
                    continue

                if t_name in seen_tasks:
                    continue

                action = row.get("Task To Run", "").strip()
                if not action or action.upper() == "N/A" or action.lower() == "task to run":
                    continue

                # Exclude Windows internal maintenance and core OS telemetry tasks
                if t_name.startswith("\\Microsoft\\Windows\\"):
                    continue

                stype = row.get("Schedule Type", "").lower()
                state = row.get("Scheduled Task State", "").strip()

                is_startup_trigger = any(x in stype for x in ["logon", "startup", "boot"])
                is_third_party = not t_name.startswith("\\Microsoft\\")

                if is_startup_trigger or is_third_party:
                    seen_tasks.add(t_name)
                    clean_name = t_name.lstrip("\\")
                    enabled = (state.lower() != "disabled")

                    target_path = self._extract_executable_path(action)
                    risk = self._assess_risk(clean_name, target_path)
                    impact = self._estimate_impact(clean_name, action)
                    publisher = self._detect_publisher(clean_name, target_path)

                    # Better friendly name for long GUID tasks
                    friendly_name = clean_name
                    if "{" in friendly_name and "}" in friendly_name:
                        # Extract clean prefix before GUID
                        prefix = friendly_name.split("{")[0].rstrip("_-")
                        if prefix:
                            friendly_name = prefix

                    item_id = f"TASK_{clean_name}"
                    items.append(
                        StartupItem(
                            id=item_id,
                            name=friendly_name,
                            command=action,
                            location_type="SCHEDULED_TASK",
                            enabled=enabled,
                            risk_level=risk,
                            impact=impact,
                            publisher=publisher,
                            target_path=target_path,
                        )
                    )
        except Exception as ex:
            logger.debug("Failed querying scheduled tasks: %s", ex)

        return items

    def _resolve_shortcut_target(self, shortcut_path: str) -> Optional[str]:
        """Resolve executable target path from .lnk shortcut file."""
        if not os.path.isfile(shortcut_path):
            return None
        try:
            with open(shortcut_path, "rb") as f:
                content = f.read()
            # Fast binary search for Windows absolute executable pattern
            matches = re.findall(rb'[a-zA-Z]:\\[^:\*\?\"<>\|\x00-\x1f]+\.(?:exe|bat|cmd)', content)
            if matches:
                # Return the longest valid match
                for m in reversed(matches):
                    try:
                        p = m.decode("latin1", errors="ignore")
                        if os.path.exists(p):
                            return p
                    except Exception:
                        continue
                return matches[0].decode("latin1", errors="ignore")
        except Exception:
            pass
        return None

    @staticmethod
    def _extract_pe_metadata(file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract real Product Name/Description and Publisher/CompanyName
        directly from PE executable version resource using native Windows API.
        Returns (product_description, company_name).
        """
        if not file_path or not os.path.isfile(file_path):
            return None, None
        try:
            import ctypes
            ver = ctypes.windll.version
            size = ver.GetFileVersionInfoSizeW(file_path, None)
            if not size:
                return None, None
            buf = ctypes.create_string_buffer(size)
            if not ver.GetFileVersionInfoW(file_path, 0, size, buf):
                return None, None

            lplp_buffer = ctypes.c_void_p()
            pu_len = ctypes.c_uint()
            if ver.VerQueryValueW(buf, r"\VarFileInfo\Translation", ctypes.byref(lplp_buffer), ctypes.byref(pu_len)) and pu_len.value >= 4:
                raw = ctypes.string_at(lplp_buffer, 4)
                lang = (raw[1] << 8) | raw[0]
                codepage = (raw[3] << 8) | raw[2]
                trans = f"{lang:04x}{codepage:04x}"
            else:
                trans = "040904b0"

            def query_str(field: str) -> Optional[str]:
                p = ctypes.c_void_p()
                l = ctypes.c_uint()
                if ver.VerQueryValueW(buf, f"\\StringFileInfo\\{trans}\\{field}", ctypes.byref(p), ctypes.byref(l)) and l.value > 0:
                    val = ctypes.wstring_at(p).strip()
                    return val if val else None
                return None

            desc = query_str("FileDescription") or query_str("ProductName")
            comp = query_str("CompanyName")
            return desc, comp
        except Exception:
            return None, None

    def set_startup_state(self, item: StartupItem, enabled: bool) -> Tuple[bool, str]:
        """
        Enable or disable a startup item safely.
        Supports Scheduled Tasks, Registry Run keys, and Startup folders.
        """
        if item.risk_level == RiskLevel.BLOCKED:
            return False, "This is a critical Windows system item and cannot be disabled."

        if item.enabled == enabled:
            return True, "No change required"

        try:
            if item.location_type == "SCHEDULED_TASK":
                return self._toggle_scheduled_task(item, enabled)
            elif item.location_type in ("HKCU_RUN", "HKCU_WOW64_RUN"):
                return self._toggle_hkcu_run(item, enabled)
            elif item.location_type in ("USER_FOLDER", "COMMON_FOLDER"):
                return self._toggle_folder_item(item, enabled)
            elif item.location_type in ("HKLM_RUN", "HKLM_WOW64_RUN"):
                return self._toggle_hklm_run(item, enabled)
            else:
                return False, f"Unsupported location type: {item.location_type}"
        except Exception as ex:
            logger.error("Failed toggling startup state for %s: %s", item.name, ex)
            return False, str(ex)

    def _toggle_scheduled_task(self, item: StartupItem, enabled: bool) -> Tuple[bool, str]:
        """Enable or disable Windows Scheduled Task using schtasks.exe."""
        # Find raw task name
        raw_name = item.id.replace("TASK_", "", 1)
        task_name = raw_name if raw_name.startswith("\\") else f"\\{raw_name}"
        action = "/enable" if enabled else "/disable"
        try:
            cmd = ["schtasks.exe", "/change", "/tn", task_name, action]
            res = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")
            if res.returncode == 0:
                item.enabled = enabled
                return True, f"Successfully {'enabled' if enabled else 'disabled'}"
            else:
                err_msg = res.stderr.strip() or res.stdout.strip() or "schtasks command failed"
                return False, err_msg
        except Exception as e:
            return False, str(e)

    def _toggle_hkcu_run(self, item: StartupItem, enabled: bool) -> Tuple[bool, str]:
        subkey = REG_HKCU_WOW64_RUN if item.location_type == "HKCU_WOW64_RUN" else REG_HKCU_RUN
        approved_key = REG_STARTUP_APPROVED_HKCU_RUN

        if not enabled:
            # Save to CleanGuard backup
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{REG_CLEANGUARD_BACKUP}\\{item.name}") as bkey:
                winreg.SetValueEx(bkey, "Name", 0, winreg.REG_SZ, item.name)
                winreg.SetValueEx(bkey, "Command", 0, winreg.REG_SZ, item.command)
                winreg.SetValueEx(bkey, "OrigLocation", 0, winreg.REG_SZ, item.location_type)

            # Remove from active Run key
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey, 0, winreg.KEY_SET_VALUE) as rkey:
                    winreg.DeleteValue(rkey, item.name)
            except FileNotFoundError:
                pass

            # Synchronize with Windows StartupApproved
            self._set_approved_state(winreg.HKEY_CURRENT_USER, approved_key, item.name, False)
            item.enabled = False
            return True, "Successfully disabled"
        else:
            # Restore to active Run key
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey, 0, winreg.KEY_SET_VALUE) as rkey:
                winreg.SetValueEx(rkey, item.name, 0, winreg.REG_SZ, item.command)

            # Remove from backup key
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"{REG_CLEANGUARD_BACKUP}\\{item.name}")
            except OSError:
                pass

            # Synchronize with Windows StartupApproved
            self._set_approved_state(winreg.HKEY_CURRENT_USER, approved_key, item.name, True)
            item.enabled = True
            return True, "Successfully enabled"

    def _toggle_hklm_run(self, item: StartupItem, enabled: bool) -> Tuple[bool, str]:
        subkey = REG_HKLM_WOW64_RUN if item.location_type == "HKLM_WOW64_RUN" else REG_HKLM_RUN
        approved_key = (
            REG_STARTUP_APPROVED_HKLM_RUN32
            if item.location_type == "HKLM_WOW64_RUN"
            else REG_STARTUP_APPROVED_HKLM_RUN
        )

        try:
            if not enabled:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{REG_CLEANGUARD_BACKUP}\\{item.name}") as bkey:
                    winreg.SetValueEx(bkey, "Name", 0, winreg.REG_SZ, item.name)
                    winreg.SetValueEx(bkey, "Command", 0, winreg.REG_SZ, item.command)
                    winreg.SetValueEx(bkey, "OrigLocation", 0, winreg.REG_SZ, item.location_type)

                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey, 0, winreg.KEY_SET_VALUE) as rkey:
                    winreg.DeleteValue(rkey, item.name)

                self._set_approved_state(winreg.HKEY_LOCAL_MACHINE, approved_key, item.name, False)
                item.enabled = False
                return True, "Successfully disabled"
            else:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey, 0, winreg.KEY_SET_VALUE) as rkey:
                    winreg.SetValueEx(rkey, item.name, 0, winreg.REG_SZ, item.command)

                try:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"{REG_CLEANGUARD_BACKUP}\\{item.name}")
                except OSError:
                    pass

                self._set_approved_state(winreg.HKEY_LOCAL_MACHINE, approved_key, item.name, True)
                item.enabled = True
                return True, "Successfully enabled"
        except PermissionError:
            return False, "Administrator privileges required to modify HKLM startup items."

    def _toggle_folder_item(self, item: StartupItem, enabled: bool) -> Tuple[bool, str]:
        current_path = item.command
        if not os.path.exists(current_path):
            return False, "File not found"

        # Determine approved hive
        approved_hive = (
            winreg.HKEY_LOCAL_MACHINE
            if item.location_type == "COMMON_FOLDER"
            else winreg.HKEY_CURRENT_USER
        )
        approved_key = (
            REG_STARTUP_APPROVED_HKLM_FOLDER
            if item.location_type == "COMMON_FOLDER"
            else REG_STARTUP_APPROVED_HKCU_FOLDER
        )
        base_name = os.path.basename(current_path)
        clean_file_name = base_name[:-9] if base_name.endswith(".disabled") else base_name

        if not enabled:
            if not current_path.endswith(".disabled"):
                new_path = current_path + ".disabled"
                os.rename(current_path, new_path)
                item.command = new_path
            self._set_approved_state(approved_hive, approved_key, clean_file_name, False)
            item.enabled = False
            return True, "Successfully disabled"
        else:
            if current_path.endswith(".disabled"):
                new_path = current_path[:-9]
                os.rename(current_path, new_path)
                item.command = new_path
            self._set_approved_state(approved_hive, approved_key, clean_file_name, True)
            item.enabled = True
            return True, "Successfully enabled"

    def _extract_executable_path(self, command: str) -> str:
        """Extract clean, environment-expanded file path from arbitrary command line string."""
        if not command:
            return ""
        cmd = os.path.expandvars(command.strip())
        if cmd.startswith('"'):
            end_quote = cmd.find('"', 1)
            if end_quote != -1:
                return cmd[1:end_quote]
            return cmd[1:]

        # Handle unquoted paths containing spaces: search for common executable extensions
        lower = cmd.lower()
        for ext in (".exe", ".bat", ".cmd", ".vbs", ".ps1"):
            idx = lower.find(ext)
            if idx != -1:
                return cmd[: idx + len(ext)].strip()

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
        name_lower = name.lower()
        heavy_signatures = [
            "steam", "epicgames", "discord", "spotify", "teams", "adobe", "chrome",
            "firefox", "nitrosense", "care center", "docker", "warp", "torrent"
        ]
        for sig in heavy_signatures:
            if sig in cmd_lower or sig in name_lower:
                return "High"

        medium_signatures = ["updater", "tray", "assistant", "cloud", "sync", "service", "onedrive"]
        for sig in medium_signatures:
            if sig in cmd_lower or sig in name_lower:
                return "Medium"

        return "Low"

    def _detect_publisher(self, name: str, target_path: Optional[str]) -> str:
        """Detect company / vendor using PE version metadata, with fallback heuristics."""
        if target_path:
            _, company = self._extract_pe_metadata(target_path)
            if company and not company.upper().startswith("TODO") and len(company) > 1:
                return company

        path_lower = (target_path or "").lower()
        name_lower = name.lower()
        combined = f"{path_lower} {name_lower}"

        if "acer" in combined:
            return "Acer Incorporated"
        if "microsoft" in combined or "windows" in combined or "edge" in combined:
            return "Microsoft Corporation"
        if "google" in combined or "chrome" in combined:
            return "Google LLC"
        if "mozilla" in combined or "firefox" in combined:
            return "Mozilla Corporation"
        if "adobe" in combined:
            return "Adobe Inc."
        if "telegram" in combined:
            return "Telegram FZ-LLC"
        if "discord" in combined:
            return "Discord Inc."
        if "docker" in combined:
            return "Docker Inc."
        if "skillbrains" in combined or "lightshot" in combined:
            return "Skillbrains"
        if "bittorrent" in combined or "utorrent" in combined or "utweb" in combined:
            return "BitTorrent Inc."
        if "anydesk" in combined:
            return "AnyDesk Software GmbH"

        return "Unknown Application"
