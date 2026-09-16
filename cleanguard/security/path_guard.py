"""
Path Guard and Boundary Enforcement Engine.
Provides canonicalization, traversal prevention, and boundary containment checks.
"""

import os
from typing import List, Tuple, Optional
from cleanguard.utils.filesystem import normalize_path, is_path_under_directory
from cleanguard.windows.shell import is_reparse_point_or_junction
from cleanguard.security.protected_paths import ProtectedPathRegistry
from cleanguard.core.contracts import ErrorCode
from cleanguard.utils.logging import get_logger

logger = get_logger("path_guard")


class PathGuard:
    """Enforces strict path boundary, canonicalization, and security rules."""

    def __init__(self, protected_registry: Optional[ProtectedPathRegistry] = None):
        self.protected = protected_registry or ProtectedPathRegistry()

    def validate_target_path(
        self,
        target_path: str,
        allowed_boundary_roots: Optional[List[str]] = None,
        allow_reparse_points: bool = False,
    ) -> Tuple[bool, ErrorCode, str]:
        """
        Validate a candidate file or directory for cleanup.
        Returns (is_valid, error_code, reason).
        """
        if not target_path or not isinstance(target_path, str):
            return False, ErrorCode.INVALID_PATH, "Empty or non-string path."

        # Null byte check (security vulnerability defense)
        if "\x00" in target_path:
            return False, ErrorCode.INVALID_PATH, "Path contains illegal null bytes."

        # Canonicalize path
        norm_path = normalize_path(target_path)

        # Path length check (MAX_PATH is 260 unless extended path syntax is used)
        if len(norm_path) > 32767:
            return False, ErrorCode.PATH_TOO_LONG, "Path exceeds maximum allowable length."

        # Check traversal sequences attempting to escape
        if ".." in target_path:
            # Recheck after normalization
            if not is_path_under_directory(norm_path, os.path.dirname(norm_path)):
                return False, ErrorCode.INVALID_PATH, "Directory traversal sequence detected."

        # Hard Protected Paths Check
        if self.protected.is_protected_path(norm_path):
            return False, ErrorCode.PROTECTED_PATH, f"Path is under system or user protected location: {norm_path}"

        # Reparse point / junction check
        if not allow_reparse_points:
            if is_reparse_point_or_junction(norm_path):
                return False, ErrorCode.INVALID_REPARSE_POINT, "Target is a reparse point, junction, or symbolic link."

        # Boundary Root containment check
        if allowed_boundary_roots:
            is_contained = False
            for root in allowed_boundary_roots:
                if is_path_under_directory(norm_path, root):
                    # Make sure it's not the root itself being deleted
                    if norm_path == normalize_path(root):
                        return False, ErrorCode.PROTECTED_PATH, "Cannot delete cleanup root directory itself."
                    is_contained = True
                    break

            if not is_contained:
                return False, ErrorCode.ACCESS_DENIED, f"Target is outside authorized cleanup root boundaries."

        return True, ErrorCode.NONE, "Path validated successfully."
