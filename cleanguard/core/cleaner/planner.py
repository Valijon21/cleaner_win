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


class CleanupPlanner:
    """Filters selected items and builds an actionable execution plan."""

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
