"""
Recycle Bin Scanner: Detects trash size and count across all mounted drives.
"""

from typing import List, Optional
from cleanguard.core.scanner.base import BaseScanner, CancellationToken, ProgressCallback
from cleanguard.core.contracts import ScanItem, CleanCategory, RiskLevel
from cleanguard.windows.drives import enumerate_drives
from cleanguard.windows.recycle_bin import query_recycle_bin


class RecycleBinScanner(BaseScanner):
    """Queries Recycle Bin metrics across fixed logical drives."""

    @property
    def scanner_id(self) -> str:
        return "recycle_bin_scanner"

    @property
    def display_name(self) -> str:
        return "Recycle Bin"

    @property
    def category(self) -> CleanCategory:
        return CleanCategory.RECYCLE_BIN

    def get_allowed_roots(self) -> List[str]:
        # Recycle bin doesn't use filesystem directory scanning
        return []

    def scan(
        self,
        cancel_token: Optional[CancellationToken] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> List[ScanItem]:
        items: List[ScanItem] = []
        drives = enumerate_drives()

        for d in drives:
            if cancel_token and cancel_token.is_cancelled():
                break
            if not d.is_ready or d.drive_type != "Fixed Disk":
                continue

            rb_info = query_recycle_bin(d.letter)
            if rb_info.num_items > 0:
                item = ScanItem(
                    path=f"{d.letter}\\$Recycle.Bin",
                    name=f"Recycle Bin ({d.letter})",
                    size=rb_info.total_size,
                    modified_at=0.0,
                    category=self.category.value,
                    risk_level=RiskLevel.SAFE,
                    reason=f"{rb_info.num_items:,} items deleted by user waiting in trash.",
                    rule_id="RULE-RECYCLE-BIN",
                    is_locked=False,
                    is_symlink=False,
                    is_junction=False,
                    is_deletable=True,
                    selected=False,  # Unchecked by default for safety
                )
                items.append(item)

                if progress_callback:
                    progress_callback(len(items), item.path, rb_info.total_size)

        return items
