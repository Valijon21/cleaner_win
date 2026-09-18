"""
Unit tests for Windows Startup Items Manager.
"""

import os
from unittest.mock import patch, MagicMock
from cleanguard.windows.startup import StartupManager, StartupItem
from cleanguard.core.contracts import RiskLevel


def test_startup_manager_initialization():
    mgr = StartupManager()
    assert mgr is not None


def test_assess_risk_critical_binary():
    mgr = StartupManager()
    assert mgr._assess_risk("ctfmon", r"C:\Windows\System32\ctfmon.exe") == RiskLevel.BLOCKED
    assert mgr._assess_risk("explorer", r"C:\Windows\explorer.exe") == RiskLevel.BLOCKED
    assert mgr._assess_risk("SecurityHealth", r"C:\Windows\System32\SecurityHealthSystray.exe") == RiskLevel.BLOCKED


def test_assess_risk_normal_application():
    mgr = StartupManager()
    assert mgr._assess_risk("Telegram", r"C:\Users\user\AppData\Roaming\Telegram Desktop\Telegram.exe") == RiskLevel.REVIEW
    assert mgr._assess_risk("Spotify", r"C:\Users\user\AppData\Roaming\Spotify\Spotify.exe") == RiskLevel.REVIEW


def test_estimate_impact():
    mgr = StartupManager()
    assert mgr._estimate_impact("Spotify", "Spotify.exe") == "High"
    assert mgr._estimate_impact("Discord", "Discord.exe") == "High"
    assert mgr._estimate_impact("CloudDrive", "clouddrive.exe") == "Medium"
    assert mgr._estimate_impact("LightApp", "light.exe") == "Low"


def test_extract_executable_path():
    mgr = StartupManager()
    assert mgr._extract_executable_path('"C:\\Program Files\\App\\app.exe" --minimized') == "C:\\Program Files\\App\\app.exe"
    assert mgr._extract_executable_path('C:\\App\\app.exe -silent') == "C:\\App\\app.exe"
    assert mgr._extract_executable_path("") == ""


def test_blocked_item_cannot_be_disabled():
    mgr = StartupManager()
    item = StartupItem(
        id="HKCU_RUN_ctfmon",
        name="ctfmon",
        command=r"C:\Windows\System32\ctfmon.exe",
        location_type="HKCU_RUN",
        enabled=True,
        risk_level=RiskLevel.BLOCKED,
        impact="Low",
    )
    success, msg = mgr.set_startup_state(item, False)
    assert success is False
    assert "critical" in msg.lower()


def test_unquoted_executable_path_with_spaces():
    mgr = StartupManager()
    unquoted = r"C:\Program Files (x86)\Vendor\App.exe -auto"
    assert mgr._extract_executable_path(unquoted) == r"C:\Program Files (x86)\Vendor\App.exe"

    bat_cmd = r"C:\Tools and Scripts\runner.bat --silent"
    assert mgr._extract_executable_path(bat_cmd) == r"C:\Tools and Scripts\runner.bat"


def test_approved_enabled_eval():
    mgr = StartupManager()
    with patch("winreg.OpenKey") as mock_open:
        with patch("winreg.QueryValueEx") as mock_val:
            # Even first byte (0x02) = enabled
            mock_val.return_value = (b"\x02\x00\x00\x00", 3)
            assert mgr._is_approved_enabled(0, "Subkey", "Item1") is True

            # Odd first byte (0x03) = disabled
            mock_val.return_value = (b"\x03\x00\x00\x00", 3)
            assert mgr._is_approved_enabled(0, "Subkey", "Item1") is False


def test_scan_scheduled_tasks_mock():
    mgr = StartupManager()
    csv_mock = (
        '"HostName","TaskName","Schedule Type","Task To Run","Scheduled Task State"\n'
        '"PC","\\MyVendorApp","At logon time","C:\\Program Files\\Vendor\\app.exe -silent","Enabled"\n'
        '"PC","\\Microsoft\\Windows\\Telemetry","Daily","C:\\Windows\\System32\\telemetry.exe","Enabled"\n'
    )
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=csv_mock)
        tasks = mgr._scan_scheduled_tasks()
        # Telemetry under \Microsoft\Windows\ must be excluded
        assert len(tasks) == 1
        assert tasks[0].name == "MyVendorApp"
        assert tasks[0].enabled is True
        assert tasks[0].location_type == "SCHEDULED_TASK"


def test_toggle_scheduled_task_mock():
    mgr = StartupManager()
    item = StartupItem(
        id="TASK_VendorApp",
        name="VendorApp",
        command="app.exe",
        location_type="SCHEDULED_TASK",
        enabled=True,
        risk_level=RiskLevel.REVIEW,
        impact="Medium",
    )
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        success, msg = mgr.set_startup_state(item, False)
        assert success is True
        assert item.enabled is False
        mock_run.assert_called_once()
        called_args = mock_run.call_args[0][0]
        assert "schtasks.exe" in called_args
        assert "/disable" in called_args
