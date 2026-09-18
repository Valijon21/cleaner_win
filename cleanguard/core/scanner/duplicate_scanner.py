"""
High-Performance Large & Duplicate Files Scanner.
Implements a 3-tier algorithm (Size Clustering -> Partial 4KB Head Hash -> Full BLAKE2b Hash)
strictly adhering to CleanGuard Safety Rules and avoiding protected system directories.
"""

import os
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Set, Tuple
from cleanguard.core.contracts import ScanItem, CleanCategory, RiskLevel
from cleanguard.core.safety import SafetyEngine
from cleanguard.core.scanner.base import CancellationToken, ProgressCallback
from cleanguard.security.protected_paths import is_system_critical_path
from cleanguard.utils.filesystem import safe_stat, normalize_path
from cleanguard.utils.logging import get_logger

logger = get_logger("scanner.duplicate")


@dataclass
class DuplicateGroup:
    """Group of files that have identical byte content."""
    file_hash: str
    file_size: int
    items: List[ScanItem] = field(default_factory=list)

    @property
    def reclaimable_bytes(self) -> int:
        """Space saved if keeping 1 file and removing the duplicates."""
        if len(self.items) > 1:
            return self.file_size * (len(self.items) - 1)
        return 0


class DuplicateScanner:
    """Scanner that detects exact duplicate files safely and efficiently."""

    def __init__(self, safety_engine: Optional[SafetyEngine] = None):
        self.safety_engine = safety_engine or SafetyEngine()
        self.min_size_bytes = 1024  # 1 KB minimum

    def scan_directory(
        self,
        target_dir: str,
        min_size_bytes: int = 1024,
        cancel_token: Optional[CancellationToken] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> List[DuplicateGroup]:
        """
        Scan a directory tree for duplicate files using 3-tier matching:
        Tier 1: Group by exact byte size.
        Tier 2: Group by 4KB head hash.
        Tier 3: Full BLAKE2b hash confirmation.
        """
        target_dir = normalize_path(target_dir)
        if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
            return []

        # Check safety guard on target root
        if is_system_critical_path(target_dir):
            logger.warning("Target directory %s is protected. Duplicate scan aborted.", target_dir)
            return []

        # Tier 1: Group by size
        size_map: Dict[int, List[str]] = {}
        files_scanned = 0

        for root, dirs, files in os.walk(target_dir, topdown=True):
            if cancel_token and cancel_token.is_cancelled():
                return []

            # Prune protected directories from walking
            dirs[:] = [
                d for d in dirs
                if not is_system_critical_path(os.path.join(root, d))
                and not d.startswith(".")
                and d.lower() not in ("$recycle.bin", "system volume information", "windows")
            ]

            for file_name in files:
                if cancel_token and cancel_token.is_cancelled():
                    return []

                full_path = os.path.join(root, file_name)
                files_scanned += 1

                if progress_callback and files_scanned % 50 == 0:
                    progress_callback(files_scanned, full_path, 0)

                stat = safe_stat(full_path)
                if not stat or stat.st_size < min_size_bytes:
                    continue

                size = stat.st_size
                if size not in size_map:
                    size_map[size] = []
                size_map[size].append(full_path)

        # Filter out sizes with only 1 file
        candidate_sizes = {s: paths for s, paths in size_map.items() if len(paths) > 1}
        if not candidate_sizes:
            return []

        # Tier 2: Partial 4KB Head Hash
        partial_hash_map: Dict[Tuple[int, str], List[str]] = {}
        for size, paths in candidate_sizes.items():
            for path in paths:
                if cancel_token and cancel_token.is_cancelled():
                    return []
                part_hash = self._compute_partial_hash(path)
                if not part_hash:
                    continue
                key = (size, part_hash)
                if key not in partial_hash_map:
                    partial_hash_map[key] = []
                partial_hash_map[key].append(path)

        # Filter out unique partial hashes
        candidate_partial = {k: paths for k, paths in partial_hash_map.items() if len(paths) > 1}
        if not candidate_partial:
            return []

        # Tier 3: Full BLAKE2b Hash
        full_hash_map: Dict[Tuple[int, str], List[ScanItem]] = {}
        for (size, _), paths in candidate_partial.items():
            for path in paths:
                if cancel_token and cancel_token.is_cancelled():
                    return []
                full_hash = self._compute_full_hash(path)
                if not full_hash:
                    continue

                key = (size, full_hash)
                stat = safe_stat(path)
                mtime = stat.st_mtime if stat else 0.0

                item = ScanItem(
                    path=path,
                    name=os.path.basename(path),
                    size=size,
                    modified_at=mtime,
                    category=CleanCategory.OTHER.value,
                    risk_level=RiskLevel.REVIEW,
                    reason="Exact byte-for-byte duplicate copy",
                    rule_id="RULE-DUPLICATE-FILE",
                )

                if key not in full_hash_map:
                    full_hash_map[key] = []
                full_hash_map[key].append(item)

        # Construct DuplicateGroups
        groups: List[DuplicateGroup] = []
        for (size, fhash), items in full_hash_map.items():
            if len(items) > 1:
                # Sort items by modification date (oldest first)
                items.sort(key=lambda x: x.modified_at)
                groups.append(DuplicateGroup(file_hash=fhash, file_size=size, items=items))

        return groups

    def _compute_partial_hash(self, path: str) -> Optional[str]:
        try:
            with open(path, "rb") as f:
                head = f.read(4096)
                return hashlib.blake2b(head, digest_size=16).hexdigest()
        except (OSError, PermissionError):
            return None

    def _compute_full_hash(self, path: str) -> Optional[str]:
        hasher = hashlib.blake2b(digest_size=20)
        try:
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (OSError, PermissionError):
            return None
