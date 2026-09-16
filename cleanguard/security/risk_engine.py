"""
Risk Classification and Explainability Engine for CleanGuard.
Strictly evaluates file safety using multi-factor heuristics.
"""

import os
from typing import Tuple, List, Optional
from cleanguard.core.contracts import RiskLevel, CleanCategory
from cleanguard.security.protected_paths import ProtectedPathRegistry
from cleanguard.security.path_guard import PathGuard
from cleanguard.windows.shell import is_file_locked, is_reparse_point_or_junction
from cleanguard.utils.formatting import calculate_age_days

# File extensions that represent executable or script code — require strict scrutiny
EXECUTABLE_EXTENSIONS = {
    ".exe", ".dll", ".sys", ".drv", ".ocx", ".cpl", ".scr",
    ".bat", ".cmd", ".ps1", ".vbs", ".js", ".wsf", ".msi", ".msp"
}

# Known safe cache and temp extensions
SAFE_EXTENSIONS = {
    ".tmp", ".temp", ".log", ".bak", ".old", ".dmp",
    ".cache", ".thumb", ".etl", ".chk", ".gid", ".prv"
}


class RiskEngine:
    """Evaluates candidates to assign RiskLevel (SAFE, REVIEW, BLOCKED) with explainable reasons."""

    def __init__(
        self,
        protected_registry: Optional[ProtectedPathRegistry] = None,
        path_guard: Optional[PathGuard] = None,
        min_age_hours: float = 24.0,
    ):
        self.protected = protected_registry or ProtectedPathRegistry()
        self.path_guard = path_guard or PathGuard(self.protected)
        self.min_age_hours = min_age_hours

    def evaluate(
        self,
        path: str,
        category: str,
        size: int = 0,
        modified_at: float = 0.0,
        allowed_roots: Optional[List[str]] = None,
        check_locks: bool = False,
    ) -> Tuple[RiskLevel, str, bool]:
        """
        Evaluate candidate file.
        Returns:
            risk_level: RiskLevel (SAFE, REVIEW, BLOCKED)
            reason: Human-readable explainable justification
            is_deletable: bool (whether candidate may be deleted at all)
        """
        # 1. Path Boundary and Security Validation
        valid, err_code, reason = self.path_guard.validate_target_path(
            target_path=path,
            allowed_boundary_roots=allowed_roots,
            allow_reparse_points=False,
        )
        if not valid:
            return RiskLevel.BLOCKED, f"Blocked by Safety Guard: {reason}", False

        # 2. Check if file is locked (optional during scan, mandatory at cleanup gate)
        if check_locks and is_file_locked(path):
            return RiskLevel.REVIEW, "File is locked by an active process.", False

        # 3. Check for Reparse Points / Junctions
        if is_reparse_point_or_junction(path):
            return RiskLevel.BLOCKED, "Target is a symbolic link or junction.", False

        # 4. Check file extension
        _, ext = os.path.splitext(path)
        ext_lower = ext.lower()

        if ext_lower in EXECUTABLE_EXTENSIONS:
            # Executable files outside explicit safe rules must be BLOCKED or REVIEW
            return RiskLevel.BLOCKED, f"Blocked: Executable binary file ({ext_lower}).", False

        # 5. File Age Assessment
        age_days = calculate_age_days(modified_at)
        age_hours = age_days * 24.0

        # Files modified very recently (< 1 hour) are risky to delete as an app may be writing them
        if age_hours < 1.0 and category != CleanCategory.RECYCLE_BIN.value:
            return RiskLevel.REVIEW, f"Recently modified ({int(age_hours * 60)} min ago). May be in active use.", True

        # 6. Category-based Classification
        if category == CleanCategory.TEMP_FILES.value:
            if age_hours >= self.min_age_hours or ext_lower in SAFE_EXTENSIONS:
                return RiskLevel.SAFE, "Temporary file older than safety threshold.", True
            return RiskLevel.REVIEW, f"Temporary file modified within {self.min_age_hours:.0f} hours.", True

        elif category in (CleanCategory.APP_CACHE.value, CleanCategory.THUMBNAIL_CACHE.value):
            return RiskLevel.SAFE, "Application or thumbnail cache (regenerable by system).", True

        elif category == CleanCategory.BROWSER_CACHE.value:
            return RiskLevel.SAFE, "Browser cache files (does not delete cookies or logins).", True

        elif category == CleanCategory.SYSTEM_LOGS.value:
            if age_days >= 7.0:
                return RiskLevel.SAFE, f"Old diagnostic log ({int(age_days)} days old).", True
            return RiskLevel.REVIEW, "Recent system log file.", True

        elif category == CleanCategory.CRASH_DUMPS.value:
            return RiskLevel.REVIEW, "Crash dump file (.dmp). Safe for cleanup if not troubleshooting.", True

        elif category == CleanCategory.RECYCLE_BIN.value:
            return RiskLevel.SAFE, "Recycle Bin content marked by user for deletion.", True

        elif category == CleanCategory.LARGE_FILES.value:
            return RiskLevel.REVIEW, "Large file discovered during analysis. User review required.", True

        elif category == CleanCategory.UPDATE_LEFTOVERS.value:
            return RiskLevel.REVIEW, "Windows Update download cache. Review recommended.", True

        # Default fallback for unknown items
        return RiskLevel.REVIEW, "Uncategorized item. Manual user review required.", True
