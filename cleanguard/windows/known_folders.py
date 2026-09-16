"""
Windows Known Folders Resolution Service.
Provides reliable, canonical resolution of system and user known folders
across Windows 7 SP1, 8, 8.1, 10, and 11.
"""

import os
import sys
import ctypes
from dataclasses import dataclass
from typing import Dict, Optional
from cleanguard.utils.filesystem import normalize_path
from cleanguard.utils.logging import get_logger

logger = get_logger("known_folders")

# Known Folder GUID definitions
KNOWN_FOLDER_GUIDS = {
    "LocalAppData": "{F1B32785-6FBA-4FCF-9D55-7B8E7F157091}",
    "RoamingAppData": "{3EB685FD-986F-4770-8620-03A5317169E9}",
    "ProgramData": "{62AB5D82-FDC1-4DC3-A9DD-070D1D495D97}",
    "Windows": "{F38BF404-1D43-42F2-9305-67DE0B28FC23}",
    "System32": "{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}",
    "ProgramFiles": "{905E63B6-C1BF-494E-B29C-65B732D3D21A}",
    "ProgramFilesX86": "{7C5A40EF-A0FB-4BFC-874A-C0F2E0B9FA8E}",
    "Documents": "{FDD39AD0-238F-46AF-ADB4-6C85480369C7}",
    "Desktop": "{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}",
    "Downloads": "{374DE290-123F-4565-9164-39C4925E467B}",
    "Pictures": "{33E28130-4E1E-4676-835A-98395C3BC3BB}",
    "Videos": "{18989B1D-9E62-4BAE-9EEB-30E10357614E}",
}


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8),
    ]


def _guid_from_string(guid_str: str) -> GUID:
    """Parse standard registry GUID string into Win32 GUID structure."""
    guid = GUID()
    ole32 = ctypes.windll.ole32
    ole32.CLSIDFromString(ctypes.c_wchar_p(guid_str), ctypes.byref(guid))
    return guid


@dataclass
class KnownFolders:
    """Container for resolved canonical paths."""
    local_app_data: str
    roaming_app_data: str
    program_data: str
    windows: str
    system32: str
    syswow64: str
    winsxs: str
    program_files: str
    program_files_x86: str
    user_temp: str
    system_temp: str
    documents: str
    desktop: str
    downloads: str
    pictures: str
    videos: str


class KnownFolderResolver:
    """Resolves Windows standard known paths reliably using Shell32 and fallbacks."""

    def __init__(self):
        self._cache: Dict[str, str] = {}
        self._folders: Optional[KnownFolders] = None

    def resolve_known_folder(self, name: str) -> str:
        """Resolve a specific known folder path by name."""
        if name in self._cache:
            return self._cache[name]

        path = ""
        guid_str = KNOWN_FOLDER_GUIDS.get(name)

        if sys.platform == "win32" and guid_str:
            try:
                shell32 = ctypes.windll.shell32
                ole32 = ctypes.windll.ole32
                guid = _guid_from_string(guid_str)
                path_ptr = ctypes.c_wchar_p()

                # KF_FLAG_DEFAULT = 0
                hr = shell32.SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(path_ptr))
                if hr == 0 and path_ptr.value:
                    path = path_ptr.value
                    # Free memory allocated by Shell
                    ole32.CoTaskMemFree(path_ptr)
            except Exception as e:
                logger.debug(f"SHGetKnownFolderPath failed for {name}: {e}")

        # Fallback if SHGetKnownFolderPath failed or on non-windows
        if not path:
            path = self._fallback_resolve(name)

        canonical = normalize_path(path) if path else ""
        self._cache[name] = canonical
        return canonical

    def _fallback_resolve(self, name: str) -> str:
        """Fallback to environment variables."""
        if name == "LocalAppData":
            return os.environ.get("LOCALAPPDATA", "")
        elif name == "RoamingAppData":
            return os.environ.get("APPDATA", "")
        elif name == "ProgramData":
            return os.environ.get("ProgramData", "C:\\ProgramData")
        elif name == "Windows":
            return os.environ.get("WINDIR", os.environ.get("SystemRoot", "C:\\Windows"))
        elif name == "System32":
            windir = os.environ.get("WINDIR", "C:\\Windows")
            return os.path.join(windir, "System32")
        elif name == "ProgramFiles":
            return os.environ.get("ProgramFiles", "C:\\Program Files")
        elif name == "ProgramFilesX86":
            return os.environ.get("ProgramFiles(x86)", os.environ.get("ProgramFiles", "C:\\Program Files (x86)"))
        elif name == "Documents":
            return os.path.join(os.path.expanduser("~"), "Documents")
        elif name == "Desktop":
            return os.path.join(os.path.expanduser("~"), "Desktop")
        elif name == "Downloads":
            return os.path.join(os.path.expanduser("~"), "Downloads")
        elif name == "Pictures":
            return os.path.join(os.path.expanduser("~"), "Pictures")
        elif name == "Videos":
            return os.path.join(os.path.expanduser("~"), "Videos")
        return ""

    def get_user_temp(self) -> str:
        """Get canonical user Temp directory."""
        if sys.platform == "win32":
            buf = ctypes.create_unicode_buffer(1024)
            ctypes.windll.kernel32.GetTempPathW(1024, buf)
            path = buf.value.rstrip("\\")
            if path:
                return normalize_path(path)
        return normalize_path(os.environ.get("TEMP", os.path.expanduser("~/AppData/Local/Temp")))

    def get_system_temp(self) -> str:
        """Get canonical system Temp directory."""
        windir = self.resolve_known_folder("Windows")
        if windir:
            return normalize_path(os.path.join(windir, "Temp"))
        return normalize_path("C:\\Windows\\Temp")

    def get_all(self) -> KnownFolders:
        """Return container with all resolved known folders."""
        if self._folders is not None:
            return self._folders

        windows_dir = self.resolve_known_folder("Windows")
        self._folders = KnownFolders(
            local_app_data=self.resolve_known_folder("LocalAppData"),
            roaming_app_data=self.resolve_known_folder("RoamingAppData"),
            program_data=self.resolve_known_folder("ProgramData"),
            windows=windows_dir,
            system32=self.resolve_known_folder("System32"),
            syswow64=normalize_path(os.path.join(windows_dir, "SysWOW64")) if windows_dir else "",
            winsxs=normalize_path(os.path.join(windows_dir, "WinSxS")) if windows_dir else "",
            program_files=self.resolve_known_folder("ProgramFiles"),
            program_files_x86=self.resolve_known_folder("ProgramFilesX86"),
            user_temp=self.get_user_temp(),
            system_temp=self.get_system_temp(),
            documents=self.resolve_known_folder("Documents"),
            desktop=self.resolve_known_folder("Desktop"),
            downloads=self.resolve_known_folder("Downloads"),
            pictures=self.resolve_known_folder("Pictures"),
            videos=self.resolve_known_folder("Videos"),
        )
        return self._folders


# Singleton accessor
_default_resolver: Optional[KnownFolderResolver] = None


def get_known_folders() -> KnownFolders:
    """Global accessor for cached known folders."""
    global _default_resolver
    if _default_resolver is None:
        _default_resolver = KnownFolderResolver()
    return _default_resolver.get_all()
