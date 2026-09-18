"""
Unit tests for Database and History Repository (Phase 10).
"""

import os
import tempfile
from cleanguard.database.db import DatabaseManager
from cleanguard.database.repositories import HistoryRepository
from cleanguard.core.contracts import (
    ScanSummary,
    CleanupSummary,
    CleanupItemResult,
    CleanupStatus,
    CleanupStrategy,
    RiskLevel,
)


def test_database_initialization_and_repository():
    with tempfile.TemporaryDirectory() as td:
        db_path = os.path.join(td, "test.db")
        db = DatabaseManager(db_path=db_path)
        repo = HistoryRepository(db)

        # 1. Record Scan Session
        scan = ScanSummary(
            scan_id="scan-001",
            started_at=100.0,
            finished_at=105.0,
            files_scanned=250,
            items_found=15,
            safe_items=10,
            review_items=5,
            blocked_items=0,
            bytes_reclaimable=1024 * 1024 * 50,
        )
        repo.record_scan_session(scan)

        # 2. Record Cleanup Session
        item_res = CleanupItemResult(
            path="C:\\Temp\\f1.tmp",
            category="temp_files",
            risk_level=RiskLevel.SAFE,
            size=1024 * 1024 * 10,
            status=CleanupStatus.SUCCESS,
            strategy=CleanupStrategy.SAFE_DELETE,
        )
        cleanup = CleanupSummary(
            cleanup_id="clean-001",
            scan_id="scan-001",
            started_at=110.0,
            finished_at=112.0,
            files_deleted=1,
            files_skipped=0,
            files_failed=0,
            bytes_recovered=1024 * 1024 * 10,
            item_results=[item_res],
        )
        repo.record_cleanup_session(cleanup)

        # 3. Verify History
        history = repo.get_cleanup_history()
        assert len(history) == 1
        assert history[0]["id"] == "clean-001"
        assert history[0]["bytes_recovered"] == 1024 * 1024 * 10

        # 4. Verify Cumulative Statistics
        stats = repo.get_cumulative_stats()
        assert stats["total_bytes_recovered"] == 1024 * 1024 * 10
        assert stats["total_files_deleted"] == 1

        # 5. Verify Itemized File Audit Details
        items = repo.get_cleanup_items("clean-001")
        assert len(items) == 1
        assert items[0]["path"] == "C:\\Temp\\f1.tmp"
        assert items[0]["status"] == "SUCCESS"
        assert items[0]["size"] == 1024 * 1024 * 10

        # 6. Verify History CSV & JSON Export
        from cleanguard.services.export_service import export_history_to_csv, export_history_to_json
        csv_path = os.path.join(td, "export.csv")
        json_path = os.path.join(td, "export.json")

        assert export_history_to_csv(csv_path, history) is True
        assert os.path.exists(csv_path)
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            content = f.read()
            assert "clean-001" in content
            assert "10.00 MB" in content

        assert export_history_to_json(json_path, history, items_provider=repo.get_cleanup_items) is True
        assert os.path.exists(json_path)
        with open(json_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "clean-001" in content
            assert "C:\\\\Temp\\\\f1.tmp" in content

