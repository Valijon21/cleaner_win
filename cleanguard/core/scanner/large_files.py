"""
Large and Space-Hog Files Scanner.
Identifies files consuming significant disk storage (100MB+, 500MB+, 1GB+, 5GB+),
categorizes them by media/archive/installer type, and integrates with SafetyEngine to protect system files.
"""

import os
import time
from dataclasses import dataclass
from typing import List, Optional, Set, Callable
from cleanguard.security.protected_paths import ProtectedPathRegistry, HARD_PROTECTED_FILENAMES
from cleanguard.utils.filesystem import normalize_path
from cleanguard.windows.drives import enumerate_drives
from cleanguard.utils.logging import get_logger

logger = get_logger("core.scanner.large_files")

CATEGORY_EXTENSIONS = {
    "VIDEOS": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".ts"},
    "AUDIO": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"},
    "ARCHIVES": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso", ".img", ".wim"},
    "INSTALLERS": {".exe", ".msi", ".msu", ".cab"},
    "EXECUTABLES": {".exe", ".msi", ".msu", ".cab", ".bat", ".cmd"},
    "DISK_IMAGES": {".vmdk", ".vhd", ".vhdx", ".qcow2", ".vdi", ".hdd"},
    "VIRTUAL_MACHINES": {".vmdk", ".vhd", ".vhdx", ".qcow2", ".vdi", ".hdd"},
    "DOCUMENTS": {".pdf", ".docx", ".xlsx", ".pptx", ".csv", ".txt", ".epub"},
    "DATABASES_BACKUPS": {".bak", ".sql", ".db", ".sqlite", ".dmp"},
}


@dataclass
class LargeFileItem:
    """Represents a discovered large file on disk."""
    path: str
    name: str
    size: int
    extension: str
    category: str  # "VIDEOS", "AUDIO", "ARCHIVES", "INSTALLERS", "DOCUMENTS", "OTHER"
    modified_at: float
    drive: str
    is_protected: bool = False

    def to_dict(self):
        return {
            "path": self.path,
            "name": self.name,
            "size": self.size,
            "extension": self.extension,
            "category": self.category,
            "modified_at": self.modified_at,
            "drive": self.drive,
            "is_protected": self.is_protected,
        }


class LargeFileScanner:
    """High-speed disk scanner for large space-consuming files."""

    def __init__(self, protected_registry: Optional[ProtectedPathRegistry] = None):
        self.protected_registry = protected_registry or ProtectedPathRegistry()

    def get_category_for_ext(self, ext: str) -> str:
        ext_lower = ext.lower()
        for cat, ext_set in CATEGORY_EXTENSIONS.items():
            if ext_lower in ext_set:
                return cat
        return "OTHER"

    def detect_category(self, filename_or_path: str) -> str:
        """Extract extension and determine file category."""
        _, ext = os.path.splitext(filename_or_path)
        return self.get_category_for_ext(ext)

    _detect_category = detect_category

    def is_file_protected(self, filepath: str) -> bool:
        """Check if file is critical system file or located in protected root."""
        base_name = os.path.basename(filepath).lower()
        if base_name in HARD_PROTECTED_FILENAMES:
            return True
        norm = normalize_path(filepath)
        # Check against protected roots (Windows, System32, WinSxS, Recovery, etc.)
        for p in self.protected_registry.get_protected_paths():
            if norm.startswith(p):
                return True
        return False

    def delete_file(self, item: LargeFileItem):
        """Safely delete a large file if not protected by SafetyEngine."""
        if item.is_protected or self.is_file_protected(item.path):
            return False, "Deletion blocked by SafetyEngine: Protected system or core file."

        if not os.path.exists(item.path):
            return False, f"File not found on disk: {item.path}"

        try:
            os.remove(item.path)
            logger.info("Successfully deleted large file: %s (%d bytes)", item.path, item.size)
            return True, f"Successfully deleted: {item.name}"
        except OSError as e:
            logger.error("Failed to delete large file %s: %s", item.path, e)
            return False, f"Failed to delete file: {e}"

    def scan_path(
        self,
        root_path: str,
        min_size_bytes: int = 104_857_600,  # 100 MB default
        category_filter: str = "ALL",
        progress_callback: Optional[Callable[[str, int], None]] = None,
        cancel_token: Optional[Callable[[], bool]] = None,
    ) -> List[LargeFileItem]:
        """
        Recursively scan a folder or entire drive root for files >= min_size_bytes.
        """
        results: List[LargeFileItem] = []
        if not os.path.exists(root_path):
            return results

        drive_letter = os.path.splitdrive(root_path)[0].upper() or "C:"
        files_count = 0

        try:
            for root, dirs, files in os.walk(root_path, topdown=True):
                if cancel_token and cancel_token():
                    break

                # Skip standard system volume and recycle bin roots from deep directory walks
                dirs[:] = [
                    d for d in dirs
                    if d.lower() not in ("$recycle.bin", "system volume information", "$windows.~bt", "winsxs")
                ]

                for name in files:
                    files_count += 1
                    if progress_callback and files_count % 250 == 0:
                        progress_callback(root, len(results))

                    filepath = os.path.join(root, name)
                    try:
                        stat = os.stat(filepath)
                        sz = stat.st_size

                        if sz >= min_size_bytes:
                            _, ext = os.path.splitext(name)
                            cat = self.get_category_for_ext(ext)

                            if category_filter != "ALL" and cat != category_filter:
                                continue

                            is_prot = self.is_file_protected(filepath)
                            item = LargeFileItem(
                                path=filepath,
                                name=name,
                                size=sz,
                                extension=ext.lower(),
                                category=cat,
                                modified_at=stat.st_mtime,
                                drive=drive_letter,
                                is_protected=is_prot,
                            )
                            results.append(item)
                    except (OSError, PermissionError):
                        continue
        except Exception as ex:
            logger.warning(f"Error walking path {root_path}: {ex}")

        # Sort largest files first
        results.sort(key=lambda x: x.size, reverse=True)
        return results

    def scan_drive(
        self,
        drive_letter: str = "C:",
        min_size_bytes: int = 104_857_600,
        category_filter: str = "ALL",
        progress_callback: Optional[Callable[[str, int], None]] = None,
        cancel_token: Optional[Callable[[], bool]] = None,
    ) -> List[LargeFileItem]:
        root = f"{drive_letter}\\" if not drive_letter.endswith("\\") else drive_letter
        return self.scan_path(
            root_path=root,
            min_size_bytes=min_size_bytes,
            category_filter=category_filter,
            progress_callback=progress_callback,
            cancel_token=cancel_token,
        )
