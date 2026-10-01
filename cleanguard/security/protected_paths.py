"""
Protected Paths Registry for CleanGuard.
Defines immutable hard system protection boundaries.
"""

import os
import threading
from typing import Set, List, Optional
from cleanguard.windows.known_folders import get_known_folders
from cleanguard.utils.filesystem import normalize_path
from cleanguard.core.config import ConfigManager


# Critical root files that must NEVER be touched under any circumstance
HARD_PROTECTED_FILENAMES: Set[str] = {
    "pagefile.sys",
    "hiberfil.sys",
    "swapfile.sys",
    "bootmgr",
    "bootnxt",
    "bcd",
    "ntuser.dat",
    "ntuser.dat.log1",
    "ntuser.dat.log2",
    "ntuser.ini",
    "sam",
    "security",
    "system",
    "software",
    "default",
    "desktop.ini",
}


class ProtectedPathRegistry:
    """Registry maintaining all protected system and user locations."""

    def __init__(self, config_manager: ConfigManager = None):
        self.config = config_manager or ConfigManager()
        self._protected_directories: Set[str] = set()
        self._system_temp = ""
        self._windows_dir = ""
        self._config_revision = -1
        self._reload_protected_paths()

    def _ensure_current(self) -> None:
        """Reload when settings changed (e.g. a new exclusion added on the Settings page),
        so every long-lived SafetyEngine honours it without an app restart."""
        if getattr(self.config, "revision", self._config_revision) != self._config_revision:
            self._reload_protected_paths()

    def _reload_protected_paths(self) -> None:
        """Populate canonical protected paths from system and config."""
        self._config_revision = getattr(self.config, "revision", 0)
        folders = get_known_folders()
        self._windows_dir = folders.windows
        self._system_temp = folders.system_temp
        dirs: Set[str] = set()

        # Core Windows OS Protected Roots
        if folders.windows:
            dirs.add(folders.windows)
        if folders.system32:
            dirs.add(folders.system32)
        if folders.syswow64:
            dirs.add(folders.syswow64)
        if folders.winsxs:
            dirs.add(folders.winsxs)

        # Boot & System Volume directories
        sys_drive = os.environ.get("SystemDrive", "C:")
        dirs.add(normalize_path(os.path.join(sys_drive, "\\Boot")))
        dirs.add(normalize_path(os.path.join(sys_drive, "\\System Volume Information")))
        dirs.add(normalize_path(os.path.join(sys_drive, "\\Recovery")))

        # Installed Program Directories
        if folders.program_files:
            dirs.add(folders.program_files)
        if folders.program_files_x86:
            dirs.add(folders.program_files_x86)

        # Personal User Folders
        if folders.documents:
            dirs.add(folders.documents)
        if folders.desktop:
            dirs.add(folders.desktop)
        if folders.pictures:
            dirs.add(folders.pictures)
        if folders.videos:
            dirs.add(folders.videos)
        if getattr(folders, "music", ""):
            dirs.add(folders.music)
        if folders.downloads:
            dirs.add(folders.downloads)

        # User's Home root itself (e.g. C:\Users\John)
        self._user_home = normalize_path(os.path.expanduser("~"))

        # Custom user-defined protected paths from settings
        custom_paths = self.config.get("custom_protected_paths", [])
        if isinstance(custom_paths, list):
            for cp in custom_paths:
                norm_cp = normalize_path(cp)
                if norm_cp:
                    dirs.add(norm_cp)

        self._protected_directories = dirs

    def is_protected_filename(self, filename: str) -> bool:
        """Check if filename matches known critical system file or registry hive."""
        if not filename:
            return False
        return filename.lower() in HARD_PROTECTED_FILENAMES

    def is_protected_path(self, target_path: str) -> bool:
        """
        Determine whether target_path is inside or identical to a protected directory,
        or is a critical system file.
        """
        if not target_path:
            return True

        self._ensure_current()
        norm_target = normalize_path(target_path)
        base_name = os.path.basename(norm_target)

        # Check critical filename
        if self.is_protected_filename(base_name):
            return True

        # Check drive root itself (e.g., "c:\" or "c:")
        if norm_target.endswith(":") or norm_target.endswith(":\\") or norm_target == "":
            return True

        # Check user profile root itself (e.g. C:\Users\John)
        if getattr(self, "_user_home", None) and norm_target == self._user_home:
            return True

        # Check if inside any protected directory
        for p_dir in self._protected_directories:
            if not p_dir:
                continue
            # Exactly matching protected folder
            if norm_target == p_dir:
                return True
            # Inside protected folder
            p_prefix = p_dir if p_dir.endswith(os.sep) else (p_dir + os.sep)
            if norm_target.startswith(p_prefix):
                # Exception: Known safe subdirectories under C:\Windows (specifically Windows\Temp)
                # If target is inside Windows\Temp, it is NOT blocked by the Windows directory protection
                if p_dir == self._windows_dir:
                    sys_temp = self._system_temp
                    if sys_temp and (norm_target.startswith(sys_temp + os.sep) or norm_target == sys_temp):
                        continue
                return True

        return False

    def get_protected_paths(self) -> List[str]:
        """Return list of all registered protected directories."""
        self._ensure_current()
        return sorted(list(self._protected_directories))

    def reload(self) -> None:
        """Refresh protected paths cache from system and configuration."""
        self._reload_protected_paths()

    def add_custom_protected_path(self, custom_path: str) -> None:
        """Add a path to custom protected paths, save to config and reload."""
        norm_path = normalize_path(custom_path)
        if not norm_path:
            return
        current = list(self.config.get("custom_protected_paths", []))
        if norm_path not in current:
            current.append(norm_path)
            self.config.set("custom_protected_paths", current)
            self.reload()

    def remove_custom_protected_path(self, custom_path: str) -> None:
        """Remove a path from custom protected paths, update config and reload."""
        norm_path = normalize_path(custom_path)
        current = list(self.config.get("custom_protected_paths", []))
        if norm_path in current:
            current.remove(norm_path)
            self.config.set("custom_protected_paths", current)
            self.reload()


_shared_registry: Optional[ProtectedPathRegistry] = None
_shared_registry_lock = threading.Lock()


def is_system_critical_path(path: str) -> bool:
    """
    Convenience helper to check if a path is protected.
    Uses one shared registry: building a registry resolves every known folder, and
    this helper is called per directory during duplicate / leftover walks.
    """
    global _shared_registry
    if _shared_registry is None:
        with _shared_registry_lock:
            if _shared_registry is None:
                _shared_registry = ProtectedPathRegistry()
    return _shared_registry.is_protected_path(path)
