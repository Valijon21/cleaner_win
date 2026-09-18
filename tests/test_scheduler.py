"""
Tests for Scheduled Auto-Care and Windows Task Scheduler Integration.
"""

import pytest
from unittest.mock import patch, MagicMock
from cleanguard.windows.scheduler import AutoCareScheduler, TASK_NAME
from cleanguard.core.contracts import ScanItem, ScanSummary, RiskLevel, CleanupSummary


def test_get_task_command():
    cmd = AutoCareScheduler.get_task_command()
    assert "--auto-clean" in cmd


def test_is_scheduled_mock():
    # Test True
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="TaskName: CleanGuardAutoCare\nNext Run Time: 2026-09-20 12:00:00\nStatus: Ready",
            stderr="",
        )
        is_sched, info = AutoCareScheduler.is_scheduled()
        assert is_sched is True
        assert "2026-09-20 12:00:00" in info

    # Test False
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="ERROR: The system cannot find the file specified.",
        )
        is_sched, info = AutoCareScheduler.is_scheduled()
        assert is_sched is False
        assert info is None


def test_enable_schedule_mock():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="SUCCESS", stderr="")
        ok, msg = AutoCareScheduler.enable_schedule(frequency="WEEKLY", day="SUN", time_str="12:00")
        assert ok is True
        assert "muvaffaqiyatli" in msg

        # Verify command arguments passed to schtasks
        called_args = mock_run.call_args[0][0]
        assert "schtasks" in called_args
        assert "/Create" in called_args
        assert TASK_NAME in called_args
        assert "WEEKLY" in called_args
        assert "SUN" in called_args


def test_disable_schedule_mock():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="SUCCESS", stderr="")
        ok, msg = AutoCareScheduler.disable_schedule()
        assert ok is True
        assert "bekor qilindi" in msg


def test_run_auto_clean_now_mock():
    mock_scan_summary = ScanSummary(
        files_scanned=2,
        bytes_reclaimable=1024,
    )
    mock_items = [
        ScanItem(
            path="C:/dummy/temp1.tmp",
            name="temp1.tmp",
            size=512,
            modified_at=0.0,
            category="temp_files",
            risk_level=RiskLevel.SAFE,
            reason="Safe temp file",
            rule_id="temp_rule",
        ),
        ScanItem(
            path="C:/dummy/review.tmp",
            name="review.tmp",
            size=512,
            modified_at=0.0,
            category="temp_files",
            risk_level=RiskLevel.REVIEW,
            reason="Review temp file",
            rule_id="review_rule",
        ),
    ]

    mock_clean_summary = CleanupSummary(
        files_deleted=1,
        bytes_recovered=512,
    )

    with patch("cleanguard.windows.scheduler.ScannerEngine.scan_all", return_value=(mock_scan_summary, mock_items)), \
         patch("cleanguard.windows.scheduler.CleanupExecutor.execute", return_value=mock_clean_summary), \
         patch("cleanguard.windows.scheduler.HistoryRepository.record_cleanup_session"):

        files_count, bytes_count = AutoCareScheduler.run_auto_clean_now()
        assert files_count == 1
        assert bytes_count == 512


def test_cli_auto_clean_flag():
    from cleanguard.app.main import main
    with patch("sys.argv", ["cleanguard", "--auto-clean"]), \
         patch("cleanguard.windows.scheduler.AutoCareScheduler.run_auto_clean_now", return_value=(5, 1048576)) as mock_run:
        exit_code = main()
        assert exit_code == 0
        mock_run.assert_called_once()
