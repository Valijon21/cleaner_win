"""
Unified Safety Engine for CleanGuard.
The mandatory gateway for all scanning and deletion operations.
"""

from typing import Tuple, List, Optional
from cleanguard.core.contracts import RiskLevel, ErrorCode
from cleanguard.security.protected_paths import ProtectedPathRegistry
from cleanguard.security.path_guard import PathGuard
from cleanguard.security.risk_engine import RiskEngine
from cleanguard.windows.shell import is_file_locked, is_reparse_point_or_junction
from cleanguard.utils.filesystem import safe_stat
from cleanguard.utils.logging import get_logger

logger = get_logger("safety_engine")


class SafetyEngine:
    """
    Mandatory safety gate.
    No file or folder may be cleaned up without passing verify_cleanup_target.
    """

    def __init__(
        self,
        protected_registry: Optional[ProtectedPathRegistry] = None,
        path_guard: Optional[PathGuard] = None,
        risk_engine: Optional[RiskEngine] = None,
    ):
        self.protected_registry = protected_registry or ProtectedPathRegistry()
        self.path_guard = path_guard or PathGuard(self.protected_registry)
        self.risk_engine = risk_engine or RiskEngine(self.protected_registry, self.path_guard)

    def evaluate_scan_candidate(
        self,
        path: str,
        category: str,
        size: int = 0,
        modified_at: float = 0.0,
        allowed_roots: Optional[List[str]] = None,
        check_locks: bool = False,
    ) -> Tuple[RiskLevel, str, bool]:
        """Classify item during scanning."""
        return self.risk_engine.evaluate(
            path=path,
            category=category,
            size=size,
            modified_at=modified_at,
            allowed_roots=allowed_roots,
            check_locks=check_locks,
        )

    def verify_cleanup_target(
        self,
        path: str,
        category: str,
        allowed_roots: Optional[List[str]] = None,
    ) -> Tuple[bool, ErrorCode, str]:
        """
        Final safety gate invoked immediately prior to deletion (TOCTOU defense).
        Must recheck:
        - Target still exists.
        - Target is not under protected paths (System32, Documents, etc.).
        - Target has not become a junction/symlink.
        - Target is within designated allowed roots.
        - Target is not locked.
        """
        # 1. Existence check
        st = safe_stat(path)
        if st is None:
            return False, ErrorCode.FILE_NOT_FOUND, "Target file no longer exists on disk."

        # 2. Path validation
        valid, err_code, reason = self.path_guard.validate_target_path(
            target_path=path,
            allowed_boundary_roots=allowed_roots,
            allow_reparse_points=False,
        )
        if not valid:
            logger.warning(f"Safety Gate REJECTED deletion of {path}: {reason}")
            return False, err_code, reason

        # 3. Lock check
        if is_file_locked(path):
            return False, ErrorCode.FILE_LOCKED, "Target file is currently locked by another process."

        # 4. Reparse check
        if is_reparse_point_or_junction(path):
            return False, ErrorCode.INVALID_REPARSE_POINT, "Target is a junction or symbolic link."

        # 5. Smart PyInstaller active process TOCTOU check
        if getattr(self.risk_engine, "smart_pyinstaller_enabled", False) and category == "temp_files":
            is_pyi, pyi_risk, pyi_reason = self.risk_engine.pyinstaller_tracker.evaluate_path(
                path=path,
                min_age_hours=self.risk_engine.pyinstaller_min_age_hours,
                allowed_temp_roots=allowed_roots,
            )
            if is_pyi and pyi_risk == RiskLevel.BLOCKED:
                logger.warning(f"Safety Gate REJECTED active PyInstaller file {path}: {pyi_reason}")
                return False, ErrorCode.ACCESS_DENIED, f"Active PyInstaller process detected: {pyi_reason}"

        return True, ErrorCode.NONE, "Safety Gate approved target."
