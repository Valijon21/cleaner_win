"""
Unit and Integration tests for Cleanup Engine (Phase 7).
"""

import os
import tempfile
from cleanguard.core.contracts import (
    ScanItem,
    RiskLevel,
    CleanupStrategy,
    CleanupStatus,
    CleanCategory,
    ErrorCode,
)
from cleanguard.core.cleaner.planner import CleanupPlanner
from cleanguard.core.cleaner.executor import CleanupExecutor
from cleanguard.core.safety import SafetyEngine


def test_cleanup_planner_filters_and_blocks():
    items = [
        ScanItem(
            path="C:\\Temp\\safe.tmp",
            name="safe.tmp",
            size=100,
            modified_at=100,
            category=CleanCategory.TEMP_FILES.value,
            risk_level=RiskLevel.SAFE,
            reason="Temp",
            rule_id="R1",
            selected=True,
        ),
        ScanItem(
            path="C:\\Temp\\unselected.tmp",
            name="unselected.tmp",
            size=200,
            modified_at=100,
            category=CleanCategory.TEMP_FILES.value,
            risk_level=RiskLevel.SAFE,
            reason="Temp",
            rule_id="R1",
            selected=False,  # Unselected
        ),
        ScanItem(
            path="C:\\Windows\\System32\\cmd.exe",
            name="cmd.exe",
            size=500000,
            modified_at=100,
            category=CleanCategory.TEMP_FILES.value,
            risk_level=RiskLevel.BLOCKED,  # Blocked!
            reason="System file",
            rule_id="R1",
            selected=True,
        ),
    ]

    planned, bytes_count = CleanupPlanner.build_plan(items)
    assert len(planned) == 1
    assert planned[0].name == "safe.tmp"
    assert bytes_count == 100


def test_cleanup_executor_executes_safe_files():
    safety = SafetyEngine()
    executor = CleanupExecutor(safety_engine=safety)

    with tempfile.TemporaryDirectory() as td:
        # Create real temp file
        fpath = os.path.join(td, "test_clean.tmp")
        with open(fpath, "w") as f:
            f.write("content to delete")

        assert os.path.exists(fpath)
        sz = os.path.getsize(fpath)

        item = ScanItem(
            path=fpath,
            name="test_clean.tmp",
            size=sz,
            modified_at=100,
            category=CleanCategory.TEMP_FILES.value,
            risk_level=RiskLevel.SAFE,
            reason="Temp",
            rule_id="R1",
            selected=True,
        )

        summary = executor.execute([item], strategy=CleanupStrategy.SAFE_DELETE)

        assert summary.files_deleted == 1
        assert summary.files_failed == 0
        assert summary.bytes_recovered == sz
        assert not os.path.exists(fpath)


def test_cleanup_executor_rejects_protected_path():
    safety = SafetyEngine()
    executor = CleanupExecutor(safety_engine=safety)

    # Fake item pointing to System32
    item = ScanItem(
        path="C:\\Windows\\System32\\calc.exe",
        name="calc.exe",
        size=1000,
        modified_at=100,
        category=CleanCategory.TEMP_FILES.value,
        risk_level=RiskLevel.SAFE,  # Even if mislabeled as SAFE!
        reason="Hacked item",
        rule_id="R_BAD",
        selected=True,
    )

    summary = executor.execute([item], strategy=CleanupStrategy.SAFE_DELETE)
    assert summary.files_deleted == 0
    assert summary.files_skipped == 1
    assert summary.item_results[0].status == CleanupStatus.SKIPPED
    assert summary.item_results[0].error_code == ErrorCode.PROTECTED_PATH
