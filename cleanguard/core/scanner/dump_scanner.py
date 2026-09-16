"""
Crash Dump Scanner: Scans Windows memory dump files (.dmp).
"""

import os
from typing import List, Optional
from cleanguard.core.scanner.base import BaseScanner, CancellationToken, ProgressCallback
from cleanguard.core.contracts import ScanItem, CleanCategory
from cleanguard.windows.known_folders import get_known_folders


class CrashDumpScanner(BaseScanner):
    """Scans system and application crash dumps."""

    @property
    def scanner_id(self) -> str:
        return "crash_dump_scanner"

    @property
    def display_name(self) -> str:
        return "Crash Dumps"

    @property
    def category(self) -> CleanCategory:
        return CleanCategory.CRASH_DUMPS

    def get_allowed_roots(self) -> List[str]:
        folders = get_known_folders()
        roots = []

        if folders.windows:
            minidump = os.path.join(folders.windows, "Minidump")
            if os.path.exists(minidump):
                roots.append(minidump)

        if folders.local_app_data:
            user_dumps = os.path.join(folders.local_app_data, "CrashDumps")
            if os.path.exists(user_dumps):
                roots.append(user_dumps)

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
                extensions={".dmp", ".mdmp", ".hdmp"},
                rule_id="RULE-CRASH-DUMP",
                default_reason="Crash dump recording application failure state.",
            )
            items.extend(found)
        return items
