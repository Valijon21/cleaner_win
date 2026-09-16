"""
Browser Cache Scanner: Safely isolates browser temporary web caches.
Guaranteed to NEVER touch browser history, sessions, saved passwords, or cookies.
"""

import os
import glob
from typing import List, Optional
from cleanguard.core.scanner.base import BaseScanner, CancellationToken, ProgressCallback
from cleanguard.core.contracts import ScanItem, CleanCategory
from cleanguard.windows.known_folders import get_known_folders


class BrowserScanner(BaseScanner):
    """Scans web browser cache storage for Chrome, Edge, Firefox, and Opera."""

    @property
    def scanner_id(self) -> str:
        return "browser_scanner"

    @property
    def display_name(self) -> str:
        return "Browser Web Cache"

    @property
    def category(self) -> CleanCategory:
        return CleanCategory.BROWSER_CACHE

    def get_allowed_roots(self) -> List[str]:
        folders = get_known_folders()
        roots: List[str] = []
        local_app = folders.local_app_data

        if not local_app:
            return roots

        # Google Chrome Cache
        chrome_cache = os.path.join(local_app, "Google", "Chrome", "User Data", "Default", "Cache", "Cache_Data")
        if os.path.exists(chrome_cache):
            roots.append(chrome_cache)

        # Microsoft Edge Cache
        edge_cache = os.path.join(local_app, "Microsoft", "Edge", "User Data", "Default", "Cache", "Cache_Data")
        if os.path.exists(edge_cache):
            roots.append(edge_cache)

        # Mozilla Firefox Cache (cache2/entries under profiles)
        firefox_profiles = os.path.join(local_app, "Mozilla", "Firefox", "Profiles")
        if os.path.exists(firefox_profiles):
            for entry_dir in glob.glob(os.path.join(firefox_profiles, "*", "cache2", "entries")):
                if os.path.isdir(entry_dir):
                    roots.append(entry_dir)

        # Opera Cache
        opera_cache = os.path.join(local_app, "Opera Software", "Opera Stable", "Cache", "Cache_Data")
        if os.path.exists(opera_cache):
            roots.append(opera_cache)

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
                rule_id="RULE-BROWSER-CACHE",
                default_reason="Cached web media and temporary browser assets.",
            )
            items.extend(found)
        return items
