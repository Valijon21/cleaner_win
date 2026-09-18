"""
Unit tests for StorageMonitorService.
"""

from cleanguard.services.monitor_service import StorageMonitorService


def test_storage_monitor_initialization(qapp):
    monitor = StorageMonitorService(check_interval_seconds=60)
    assert monitor.check_interval == 60
    assert monitor.threshold_percentage == 15.0


def test_storage_monitor_check_now(qapp):
    monitor = StorageMonitorService(
        check_interval_seconds=60,
        threshold_percentage=100.0,  # Set threshold to 100% to force alert on any drive
        cooldown_seconds=0,
    )
    breached = monitor.check_drives_now()
    assert isinstance(breached, set)
    monitor.stop()
