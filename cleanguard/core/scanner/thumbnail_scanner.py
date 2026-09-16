"""
Thumbnail Scanner: Scans Windows Explorer thumbnail and icon caches.
"""

import os
from typing import List, Optional
from cleanguard.core.scanner.base import BaseScanner, CancellationToken, ProgressCallback
from cleanguard.core.contracts import ScanItem, CleanCategory
from cleanguard.windows.known_folders import get_known_folders


class ThumbnailScanner(BaseScanner):
    """Scans Explorer thumbnail database files (thumbcache_*.db)."""

    @property
    def scanner_id(self) -> str:
        return "thumbnail_scanner"

    @property
    def display_name(self) -> str:
        return "Thumbnail Cache"

    @property
    def category(self) -> CleanCategory:
        return CleanCategory.THUMBNAIL_CACHE

    def get_allowed_roots(self) -> List[str]:
        folders = get_known_folders()
        if not folders.local_app_data:
            return []
        explorer_dir = os.path.join(folders.local_app_data, "Microsoft", "Windows", "Explorer")
        if os.path.exists(explorer_dir):
            return [explorer_dir]
        return []

    def scan(
        self,
        cancel_token: Optional[CancellationToken] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> List[ScanItem]:
        items: List[ScanItem] = []
        for root in self.get_allowed_roots():
            if cancel_token and cancel_token.is_cancelled():
                break
            found = self.safe_scan_directory(
                root_dir=root,
                cancel_token=cancel_token,
                progress_callback=progress_callback,
                rule_id="RULE-THUMB-CACHE",
                default_reason="Windows Explorer thumbnail cache database.",
            )
            # Only include thumbcache and iconcache files
            for it in found:
                lower_name = it.name.lower()
                if "thumbcache" in lower_name or "iconcache" in lower_name:
                    items.append(it)
        return items
