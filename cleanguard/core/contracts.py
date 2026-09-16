"""
Data contracts, enumerations and domain types for CleanGuard.
Strictly compatible with Python 3.8+.
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class RiskLevel(str, Enum):
    """Safety and risk classification levels."""
    SAFE = "SAFE"
    REVIEW = "REVIEW"
    BLOCKED = "BLOCKED"


class CleanupStrategy(str, Enum):
    """File deletion / removal strategies."""
    SKIP = "SKIP"
    RECYCLE_BIN = "RECYCLE_BIN"
    SAFE_DELETE = "SAFE_DELETE"
    PERMANENT_DELETE = "PERMANENT_DELETE"


class CleanupStatus(str, Enum):
    """Execution status for a cleanup item."""
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ErrorCode(str, Enum):
    """Standardized error taxonomy."""
    NONE = "NONE"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    ACCESS_DENIED = "ACCESS_DENIED"
    FILE_LOCKED = "FILE_LOCKED"
    INVALID_PATH = "INVALID_PATH"
    PATH_TOO_LONG = "PATH_TOO_LONG"
    INVALID_REPARSE_POINT = "INVALID_REPARSE_POINT"
    PROTECTED_PATH = "PROTECTED_PATH"
    UNKNOWN_RULE = "UNKNOWN_RULE"
    DISK_UNAVAILABLE = "DISK_UNAVAILABLE"
    PERMISSION_REQUIRED = "PERMISSION_REQUIRED"
    USER_CANCELLED = "USER_CANCELLED"
    IO_ERROR = "IO_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class CleanCategory(str, Enum):
    """Primary cleanup categories."""
    TEMP_FILES = "temp_files"
    APP_CACHE = "app_cache"
    SYSTEM_LOGS = "system_logs"
    BROWSER_CACHE = "browser_cache"
    RECYCLE_BIN = "recycle_bin"
    UPDATE_LEFTOVERS = "update_leftovers"
    CRASH_DUMPS = "crash_dumps"
    THUMBNAIL_CACHE = "thumbnail_cache"
    LARGE_FILES = "large_files"
    OTHER = "other"


@dataclass
class ScanItem:
    """Represents a discovered cleanup candidate file or directory."""
    path: str
    name: str
    size: int
    modified_at: float
    category: str
    risk_level: RiskLevel
    reason: str
    rule_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_locked: bool = False
    is_symlink: bool = False
    is_junction: bool = False
    is_deletable: bool = False
    selected: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert item to serializable dictionary."""
        return {
            "id": self.id,
            "path": self.path,
            "name": self.name,
            "size": self.size,
            "modified_at": self.modified_at,
            "category": self.category,
            "risk_level": self.risk_level.value,
            "reason": self.reason,
            "rule_id": self.rule_id,
            "is_locked": self.is_locked,
            "is_symlink": self.is_symlink,
            "is_junction": self.is_junction,
            "is_deletable": self.is_deletable,
            "selected": self.selected,
        }


@dataclass
class ScanSummary:
    """Summary of a storage scan run."""
    scan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: float = 0.0
    finished_at: float = 0.0
    drive_count: int = 0
    files_scanned: int = 0
    items_found: int = 0
    safe_items: int = 0
    review_items: int = 0
    blocked_items: int = 0
    bytes_reclaimable: int = 0
    items_by_category: Dict[str, int] = field(default_factory=dict)
    bytes_by_category: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scan_id": self.scan_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "drive_count": self.drive_count,
            "files_scanned": self.files_scanned,
            "items_found": self.items_found,
            "safe_items": self.safe_items,
            "review_items": self.review_items,
            "blocked_items": self.blocked_items,
            "bytes_reclaimable": self.bytes_reclaimable,
            "items_by_category": self.items_by_category,
            "bytes_by_category": self.bytes_by_category,
        }


@dataclass
class CleanupItemResult:
    """Execution result for a single target during cleanup."""
    path: str
    category: str
    risk_level: RiskLevel
    size: int
    status: CleanupStatus
    strategy: CleanupStrategy
    error_code: ErrorCode = ErrorCode.NONE
    error_message: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class CleanupSummary:
    """Aggregated result of a cleanup session."""
    cleanup_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    scan_id: Optional[str] = None
    started_at: float = 0.0
    finished_at: float = 0.0
    files_deleted: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    bytes_recovered: int = 0
    item_results: List[CleanupItemResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cleanup_id": self.cleanup_id,
            "scan_id": self.scan_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "files_deleted": self.files_deleted,
            "files_skipped": self.files_skipped,
            "files_failed": self.files_failed,
            "bytes_recovered": self.bytes_recovered,
            "item_results_count": len(self.item_results),
        }


@dataclass
class DriveInfo:
    """Details about a detected storage volume/drive."""
    letter: str  # e.g., "C:"
    drive_type: str  # Fixed, Removable, CD-ROM, etc.
    filesystem: str  # NTFS, FAT32, exFAT
    total_bytes: int
    free_bytes: int
    used_bytes: int
    label: str = ""
    is_system_drive: bool = False
    is_ready: bool = True

    @property
    def used_percentage(self) -> float:
        if self.total_bytes <= 0:
            return 0.0
        return (self.used_bytes / self.total_bytes) * 100.0

    @property
    def free_percentage(self) -> float:
        if self.total_bytes <= 0:
            return 0.0
        return (self.free_bytes / self.total_bytes) * 100.0
