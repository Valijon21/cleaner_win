"""
Cache Scanner: Scans DirectX shader caches, GPU caches, and application caches.
"""

import os
from typing import List, Optional
from cleanguard.core.scanner.base import BaseScanner, CancellationToken, ProgressCallback
from cleanguard.core.contracts import ScanItem, CleanCategory
from cleanguard.windows.known_folders import get_known_folders


class CacheScanner(BaseScanner):
    """Scans system and application shader/temporary caches."""

    @property
    def scanner_id(self) -> str:
        return "cache_scanner"

    @property
    def display_name(self) -> str:
        return "Application & Shader Cache"

    @property
    def category(self) -> CleanCategory:
        return CleanCategory.APP_CACHE

    def get_allowed_roots(self) -> List[str]:
        folders = get_known_folders()
        roots = []
        local_app = folders.local_app_data

        if local_app:
            # DirectX Shader Cache
            d3d_cache = os.path.join(local_app, "D3DSCache")
            if os.path.exists(d3d_cache):
                roots.append(d3d_cache)

            # NVIDIA Shader Cache
            nv_cache = os.path.join(local_app, "NVIDIA", "GLCache")
            if os.path.exists(nv_cache):
                roots.append(nv_cache)

            # AMD Shader Cache
            amd_cache = os.path.join(local_app, "AMD", "GLCache")
            if os.path.exists(amd_cache):
                roots.append(amd_cache)

        return roots

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
                rule_id="RULE-SHADER-CACHE",
                default_reason="Shader cache regenerated on demand by graphics drivers.",
            )
            items.extend(found)
        return items
