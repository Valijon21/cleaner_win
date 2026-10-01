"""
Cleanup Planner: Plans and validates actionable targets prior to execution.
"""

from typing import List, Tuple
from cleanguard.core.contracts import (
    ScanItem,
    RiskLevel,
    CleanupStrategy,
    CleanCategory,
)
from cleanguard.utils.logging import get_logger

logger = get_logger("cleanup_planner")

# Categories never cleaned without the user reviewing them on the Results page.
# Emptying the Recycle Bin destroys the user's own undo buffer, and wiping recent
# document / Jump List history is a visible change to their workspace.
UNATTENDED_EXCLUDED_CATEGORIES = frozenset({
    CleanCategory.RECYCLE_BIN.value,
    CleanCategory.PRIVACY_TRACES.value,
})


class CleanupPlanner:
    """Filters selected items and builds an actionable execution plan."""

    @staticmethod
    def select_unattended(items: List[ScanItem]) -> List[ScanItem]:
        """
        Items eligible for unattended cleanup (scheduled Auto-Care, 1-Click Smart Care):
        strictly SAFE and outside UNATTENDED_EXCLUDED_CATEGORIES.
        Returned items are marked selected so build_plan() accepts them.
        """
        chosen: List[ScanItem] = []
        for item in items:
            if item.risk_level != RiskLevel.SAFE:
                continue
            if item.category in UNATTENDED_EXCLUDED_CATEGORIES:
                continue
            item.selected = True
            chosen.append(item)
        return chosen

    @staticmethod
    def build_plan(
        items: List[ScanItem],
        default_strategy: CleanupStrategy = CleanupStrategy.SAFE_DELETE,
    ) -> Tuple[List[ScanItem], int]:
        """
        Produce vetted list of items ready for execution.
        Returns:
            (actionable_items, total_planned_bytes)
        """
        planned_items: List[ScanItem] = []
        planned_bytes = 0

        for item in items:
            # 1. Must be selected by user
            if not item.selected:
                continue

            # 2. Safety Engine invariance: BLOCKED items can NEVER be cleaned!
            if item.risk_level == RiskLevel.BLOCKED:
                logger.warning(f"Planner rejected BLOCKED item: {item.path}")
                continue

            # 3. Recycle Bin item handling
            if item.category == CleanCategory.RECYCLE_BIN.value:
                planned_items.append(item)
                planned_bytes += item.size
                continue

            # 4. Standard file candidate
            planned_items.append(item)
            planned_bytes += item.size

        logger.info(f"Cleanup plan generated: {len(planned_items)} items, {planned_bytes} bytes.")
        return planned_items, planned_bytes
