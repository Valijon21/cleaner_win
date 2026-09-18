"""
Privacy Scanner: Scans and clears user privacy traces, recent file histories, and Jump Lists.
Compatible with Windows 7 SP1, 8, 8.1, 10, and 11.
"""

import os
import winreg
import ctypes
from typing import List, Optional
from cleanguard.core.scanner.base import BaseScanner, CancellationToken, ProgressCallback
from cleanguard.core.contracts import ScanItem, CleanCategory, RiskLevel
from cleanguard.windows.known_folders import get_known_folders
from cleanguard.utils.logging import get_logger

logger = get_logger("scanner.privacy")


class PrivacyScanner(BaseScanner):
    """Scans Windows Recent documents, Explorer Jump Lists, and privacy tracks."""

    @property
    def scanner_id(self) -> str:
        return "privacy_scanner"

    @property
    def display_name(self) -> str:
        return "Privacy Traces"

    @property
    def category(self) -> CleanCategory:
        return CleanCategory.PRIVACY_TRACES

    def get_allowed_roots(self) -> List[str]:
        folders = get_known_folders()
        roots: List[str] = []
        if folders.roaming_app_data:
            recent_dir = os.path.join(folders.roaming_app_data, "Microsoft", "Windows", "Recent")
            if os.path.exists(recent_dir):
                roots.append(recent_dir)
                auto_dest = os.path.join(recent_dir, "AutomaticDestinations")
                if os.path.exists(auto_dest):
                    roots.append(auto_dest)
                custom_dest = os.path.join(recent_dir, "CustomDestinations")
                if os.path.exists(custom_dest):
                    roots.append(custom_dest)
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
                rule_id="RULE-PRIVACY-RECENT",
                default_reason="Windows Explorer recent document track or Jump List shortcut",
                max_depth=2,
            )
            # Mark all as SAFE to clean since these are merely pointer shortcuts / history
            for it in found:
                it.category = CleanCategory.PRIVACY_TRACES.value
                it.risk_level = RiskLevel.SAFE
                items.append(it)

        return items

    @staticmethod
    def clear_clipboard() -> bool:
        """Clear Windows system clipboard contents."""
        try:
            user32 = ctypes.windll.user32
            if user32.OpenClipboard(None):
                user32.EmptyClipboard()
                user32.CloseClipboard()
                return True
        except Exception as ex:
            logger.debug("Clipboard clear failed: %s", ex)
        return False

    @staticmethod
    def clear_run_history() -> int:
        """Clear Windows Run dialog command MRU entries."""
        cleared = 0
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
                info = winreg.QueryInfoKey(key)
                for _ in range(info[1]):
                    try:
                        name, _, _ = winreg.EnumValue(key, 0)
                        winreg.DeleteValue(key, name)
                        cleared += 1
                    except OSError:
                        break
        except OSError:
            pass
        return cleared
