"""
Unit tests for 1-Click Smart Care Pipeline (SmartCareWorker and SmartCareResult).
"""

import pytest
from unittest.mock import patch, MagicMock
from cleanguard.services.smart_care_service import SmartCareWorker, SmartCareResult
from cleanguard.core.contracts import ScanItem, RiskLevel, CleanupSummary


def test_smart_care_result_properties():
    res = SmartCareResult(
        junk_bytes_reclaimed=10_000_000,
        junk_files_deleted=42,
        registry_issues_fixed=15,
        ram_bytes_freed=500_000_000,
        dns_flushed=True,
        update_bytes_freed=25_000_000,
        duration_seconds=3.5,
    )
    assert res.junk_cleaned_bytes == 10_000_000
    assert res.ram_freed_bytes == 500_000_000
    assert res.update_cache_cleaned_bytes == 25_000_000
    assert res.total_space_reclaimed_bytes == 35_000_000
    assert res.registry_issues_fixed == 15
    assert res.dns_flushed is True


def test_smart_care_worker_run(qapp):
    mock_db = MagicMock()
    worker = SmartCareWorker(db_manager=mock_db)

    stages_received = []
    results_received = []

    worker.stage_changed.connect(lambda stage, pct: stages_received.append((stage, pct)))
    worker.finished.connect(lambda res: results_received.append(res))

    # Mock Junk Scanner & Cleaner
    mock_item = ScanItem(
        path=r"C:\Users\test\AppData\Local\Temp\test.tmp",
        name="test.tmp",
        size=1024 * 1024,
        modified_at=0.0,
        category="temp_files",
        risk_level=RiskLevel.SAFE,
        reason="Temporary file",
        rule_id="temp_rule",
    )
    mock_summary = CleanupSummary(
        bytes_recovered=1024 * 1024,
        files_deleted=1,
        files_failed=0,
        files_skipped=0,
    )

    with patch.object(worker.scanner, "scan_all", return_value=(MagicMock(), [mock_item])), \
         patch.object(worker.cleaner, "execute", return_value=mock_summary), \
         patch.object(worker.reg_cleaner, "scan_mui_cache", return_value=[]), \
         patch.object(worker.reg_cleaner, "scan_run_mru", return_value=[]), \
         patch("cleanguard.services.smart_care_service.flush_memory", return_value=(10, 50 * 1024 * 1024)), \
         patch("cleanguard.services.smart_care_service.flush_dns", return_value=(True, "OK")), \
         patch("cleanguard.services.smart_care_service.is_user_admin", return_value=True), \
         patch.object(worker.update_cleaner, "clean_update_download_cache", return_value=(True, 20 * 1024 * 1024, "OK")):

        # Run synchronously in test thread
        worker.run()

    assert len(results_received) == 1
    res = results_received[0]
    assert isinstance(res, SmartCareResult)
    assert res.junk_bytes_reclaimed == 1024 * 1024
    assert res.junk_files_deleted == 1
    assert res.ram_bytes_freed == 50 * 1024 * 1024
    assert res.dns_flushed is True
    assert res.update_bytes_freed == 20 * 1024 * 1024
    assert res.total_space_reclaimed_bytes == (1 + 20) * 1024 * 1024
    assert len(stages_received) >= 4
