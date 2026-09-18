"""
Unit tests for CleanGuard System Tray Icon and Context Menu.
"""

from cleanguard.ui.tray import CleanGuardTrayIcon, create_default_tray_icon
from cleanguard.core.contracts import DriveInfo


def test_tray_icon_creation(qapp):
    icon = create_default_tray_icon()
    assert icon.isNull() is False


def test_tray_controller_and_actions(qapp):
    tray = CleanGuardTrayIcon()
    assert tray.menu is not None
    assert len(tray.menu.actions()) >= 4

    # Test retranslation
    tray.retranslate_ui()
    assert len(tray.act_open.text()) > 0
    assert len(tray.act_clean.text()) > 0
    assert len(tray.act_exit.text()) > 0


def test_tray_alert_method(qapp):
    tray = CleanGuardTrayIcon()
    dummy_drive = DriveInfo(
        letter="C:",
        drive_type="Fixed Disk",
        filesystem="NTFS",
        total_bytes=100 * 1024 * 1024 * 1024,
        free_bytes=5 * 1024 * 1024 * 1024,
        used_bytes=95 * 1024 * 1024 * 1024,
        label="System",
        is_system_drive=True,
        is_ready=True,
    )
    # Ensure calling show_low_space_alert doesn't throw
    tray.show_low_space_alert(dummy_drive)
