"""
Filesystem utility functions and safe file operations.
"""

import os
import sys
from typing import Optional, Tuple


def normalize_path(path: str) -> str:
    """
    Canonicalize filesystem path:
    - Expand environment variables and user home
    - Convert to absolute path
    - Normalize case on Windows for reliable comparison
    - Replace forward slashes with Windows backslashes
    """
    if not path:
        return ""
    expanded = os.path.expanduser(os.path.expandvars(path))
    abs_path = os.path.abspath(expanded)
    # Normcase on Windows converts slashes and lowercases for case-insensitive matching
    return os.path.normcase(os.path.normpath(abs_path))


def get_display_path(path: str) -> str:
    """
    Get clean normalized path preserving visual casing where possible.
    """
    if not path:
        return ""
    expanded = os.path.expanduser(os.path.expandvars(path))
    return os.path.normpath(os.path.abspath(expanded))


def is_path_under_directory(child_path: str, parent_directory: str) -> bool:
    """
    Safely check if child_path is strictly inside parent_directory (preventing traversal).
    """
    norm_child = normalize_path(child_path)
    norm_parent = normalize_path(parent_directory)
    
    if not norm_child or not norm_parent:
        return False
        
    # Parent must end with separator to avoid partial folder name matches
    if not norm_parent.endswith(os.sep):
        norm_parent += os.sep
        
    # Check common path or prefix
    return norm_child.startswith(norm_parent) or norm_child == norm_parent.rstrip(os.sep)


def safe_stat(path: str) -> Optional[os.stat_result]:
    """
    Query os.stat safely catching IO, permission, and not found errors.
    """
    try:
        return os.stat(path)
    except (OSError, IOError, ValueError):
        return None


def safe_get_size(path: str) -> int:
    """Get size of file in bytes, returning 0 if error."""
    st = safe_stat(path)
    return st.st_size if st else 0


def safe_get_mtime(path: str) -> float:
    """Get modification timestamp, returning 0.0 if error."""
    st = safe_stat(path)
    return st.st_mtime if st else 0.0


def calculate_dir_size_and_count(dir_path: str, max_depth: int = 20) -> Tuple[int, int]:
    """
    Safely calculate total size (bytes) and file count of a directory tree.
    Does not follow junctions/symlinks.
    """
    total_size = 0
    file_count = 0
    try:
        for root, dirs, files in os.walk(dir_path, topdown=True, followlinks=False):
            for f in files:
                f_path = os.path.join(root, f)
                try:
                    # Don't follow symlinks
                    if not os.path.islink(f_path):
                        st = os.stat(f_path)
                        total_size += st.st_size
                        file_count += 1
                except (OSError, IOError):
                    continue
    except (OSError, IOError):
        pass
    return total_size, file_count
