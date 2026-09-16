"""
Base Scanner Interface, Cancellation Token, and Progress Reporting.
"""

import os
import threading
from abc import ABC, abstractmethod
from typing import List, Callable, Optional, Set
from cleanguard.core.contracts import ScanItem, CleanCategory
from cleanguard.core.safety import SafetyEngine
from cleanguard.windows.shell import is_reparse_point_or_junction
from cleanguard.utils.filesystem import safe_stat
from cleanguard.utils.logging import get_logger

logger = get_logger("scanner_base")


class CancellationToken:
    """Thread-safe cooperative cancellation token."""

    def __init__(self):
        self._cancelled = threading.Event()

    def cancel(self) -> None:
        """Signal cancellation to all running workers."""
        self._cancelled.set()

    def is_cancelled(self) -> bool:
        """Check if cancellation was requested."""
        return self._cancelled.is_set()

    def reset(self) -> None:
        """Reset token for new scan run."""
        self._cancelled.clear()


# Progress Callback: (files_scanned, current_file_path, bytes_found)
ProgressCallback = Callable[[int, str, int], None]


class BaseScanner(ABC):
    """Abstract base class for all CleanGuard domain scanners."""

    def __init__(self, safety_engine: Optional[SafetyEngine] = None):
        self.safety_engine = safety_engine or SafetyEngine()
        self.logger = get_logger(self.__class__.__name__)

    @property
    @abstractmethod
    def scanner_id(self) -> str:
        """Unique machine-readable scanner identifier."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable localized name."""
        pass

    @property
    @abstractmethod
    def category(self) -> CleanCategory:
        """Primary category managed by this scanner."""
        pass

    @abstractmethod
    def get_allowed_roots(self) -> List[str]:
        """List of authorized directory roots this scanner is restricted to."""
        pass

    @abstractmethod
    def scan(
        self,
        cancel_token: Optional[CancellationToken] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> List[ScanItem]:
        """
        Execute scan operation.
        Must respect cancel_token, invoke progress_callback periodically,
        and never modify or delete any file.
        """
        pass

    def safe_scan_directory(
        self,
        root_dir: str,
        cancel_token: Optional[CancellationToken] = None,
        progress_callback: Optional[ProgressCallback] = None,
        extensions: Optional[Set[str]] = None,
        min_age_seconds: float = 0.0,
        rule_id: str = "RULE-GENERIC",
        default_reason: str = "Reclaimable temporary data",
        max_depth: int = 10,
    ) -> List[ScanItem]:
        """
        Reusable helper to safely walk a directory tree:
        - Avoids reparse points and junction loops.
        - Checks cancellation token every few files.
        - Evaluates items through SafetyEngine.
        - Throttles progress callbacks.
        """
        items: List[ScanItem] = []
        if not root_dir or not os.path.exists(root_dir):
            return items

        allowed_roots = self.get_allowed_roots()
        files_count = 0
        bytes_found = 0
        token = cancel_token or CancellationToken()

        try:
            for root, dirs, files in os.walk(root_dir, topdown=True, followlinks=False):
                if token.is_cancelled():
                    self.logger.info(f"{self.scanner_id} cancelled during walk.")
                    break

                # Prune junctions or reparse points from descending subdirectories
                dirs[:] = [d for d in dirs if not is_reparse_point_or_junction(os.path.join(root, d))]

                for file_name in files:
                    if token.is_cancelled():
                        break

                    files_count += 1
                    file_path = os.path.join(root, file_name)

                    # Reparse point check on file
                    if is_reparse_point_or_junction(file_path):
                        continue

                    # Extension filter check
                    if extensions is not None:
                        _, ext = os.path.splitext(file_name)
                        if ext.lower() not in extensions:
                            continue

                    st = safe_stat(file_path)
                    if not st:
                        continue

                    size = st.st_size
                    mtime = st.st_mtime

                    # Age filter check
                    if min_age_seconds > 0:
                        import time
                        if (time.time() - mtime) < min_age_seconds:
                            continue

                    # Safety evaluation
                    risk, reason, deletable = self.safety_engine.evaluate_scan_candidate(
                        path=file_path,
                        category=self.category.value,
                        size=size,
                        modified_at=mtime,
                        allowed_roots=allowed_roots,
                    )

                    item = ScanItem(
                        path=file_path,
                        name=file_name,
                        size=size,
                        modified_at=mtime,
                        category=self.category.value,
                        risk_level=risk,
                        reason=reason or default_reason,
                        rule_id=rule_id,
                        is_locked=False,
                        is_symlink=False,
                        is_junction=False,
                        is_deletable=deletable,
                        selected=(risk.value == "SAFE"),
                    )
                    items.append(item)
                    bytes_found += size

                    # Throttled progress update every 20 files
                    if progress_callback and (files_count % 20 == 0 or files_count == 1):
                        progress_callback(files_count, file_path, bytes_found)

        except (OSError, IOError) as exc:
            self.logger.warning(f"Error scanning directory {root_dir}: {exc}")

        return items
