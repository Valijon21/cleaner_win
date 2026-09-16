"""
Log Scanner: Scans Windows error reports and diagnostic log files.
"""

import os
from typing import List, Optional, Set
from cleanguard.core.scanner.base import BaseScanner, CancellationToken, ProgressCallback
from cleanguard.core.contracts import ScanItem, CleanCategory
from cleanguard.windows.known_folders import get_known_folders


class LogScanner(BaseScanner):
    """Scans Windows Error Reporting (WER) logs and old diagnostic logs."""

    @property
    def scanner_id(self) -> str:
        return "log_scanner"

    @property
    def display_name(self) -> str:
        return "System Logs"

    @property
    def category(self) -> CleanCategory:
        return CleanCategory.SYSTEM_LOGS

    def get_allowed_roots(self) -> List[str]:
        folders = get_known_folders()
        roots = []

        # User WER Report Archive / Queue
        if folders.local_app_data:
            wer_user = os.path.join(folders.local_app_data, "Microsoft", "Windows", "WER")
            if os.path.exists(wer_user):
                roots.append(wer_user)

        # ProgramData WER
        if folders.program_data:
            wer_all = os.path.join(folders.program_data, "Microsoft", "Windows", "WER")
            if os.path.exists(wer_all):
                roots.append(wer_all)

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
                rule_id="RULE-WER-LOGS",
                default_reason="Windows Error Reporting diagnostic crash record.",
            )
            items.extend(found)
        return items
