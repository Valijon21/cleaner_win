"""
User Data Remover: the single, safety-gated path for deleting user-selected data
(duplicate files, large files, uninstall leftovers).

Unlike junk cleanup, this data is not regenerable, so items are always moved to the
Recycle Bin (recoverable) and never deleted permanently.
"""

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Tuple
from cleanguard.core.safety import SafetyEngine
from cleanguard.windows.recycle_bin import move_to_recycle_bin
from cleanguard.utils.logging import get_logger

logger = get_logger("user_data_remover")


@dataclass
class UserDataRemovalResult:
    """Outcome of a user-data removal batch."""
    removed: List[str] = field(default_factory=list)
    bytes_removed: int = 0
    rejected: List[Tuple[str, str]] = field(default_factory=list)  # (path, reason)
    failed: List[Tuple[str, str]] = field(default_factory=list)    # (path, reason)


def recycle_user_items(
    items: Iterable[Tuple[str, int]],
    safety_engine: Optional[SafetyEngine] = None,
) -> UserDataRemovalResult:
    """
    Move (path, size) items to the Recycle Bin after passing the Safety Engine gate.
    """
    engine = safety_engine or SafetyEngine()
    result = UserDataRemovalResult()

    for path, size in items:
        approved, _, reason = engine.verify_user_data_target(path)
        if not approved:
            result.rejected.append((path, reason))
            continue
        if move_to_recycle_bin(path, warn_if_permanent=True):
            result.removed.append(path)
            result.bytes_removed += int(size or 0)
            logger.info("Moved user data to Recycle Bin: %s", path)
        else:
            result.failed.append((path, "Could not move item to Recycle Bin."))
            logger.warning("Failed moving user data to Recycle Bin: %s", path)

    return result
