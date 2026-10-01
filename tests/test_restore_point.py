"""
Unit tests for Windows System Restore Point creation service.
"""

from unittest.mock import patch, MagicMock
from cleanguard.windows.restore_point import create_restore_point


def test_create_restore_point_success_srclient():
    def fake_call(info, status):
        status.nStatus = 0
        status.llSequenceNumber = 123
        return 1

    with patch("cleanguard.windows.restore_point.is_user_admin", return_value=True),          patch("cleanguard.windows.restore_point._call_srclient", side_effect=fake_call):
        success, msg = create_restore_point("Test Snapshot")
        assert success is True
        assert "123" in msg


def test_create_restore_point_powershell_fallback():
    with patch("cleanguard.windows.restore_point.is_user_admin", return_value=True),          patch("cleanguard.windows.restore_point._call_srclient", side_effect=OSError("DLL missing")):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        with patch("subprocess.run", return_value=mock_proc):
            success, msg = create_restore_point("Test Snapshot")
            assert success is True
            assert "PowerShell" in msg


def test_create_restore_point_begin_is_closed_with_end():
    calls = []

    def fake_call(info, status):
        calls.append(info.dwEventType)
        status.nStatus = 0
        status.llSequenceNumber = 7
        return 1

    with patch("cleanguard.windows.restore_point.is_user_admin", return_value=True),          patch("cleanguard.windows.restore_point._call_srclient", side_effect=fake_call):
        success, _ = create_restore_point("Test Snapshot")
    assert success is True
    assert calls == [100, 101]  # BEGIN_SYSTEM_CHANGE then END_SYSTEM_CHANGE


def test_create_restore_point_requires_admin():
    with patch("cleanguard.windows.restore_point.is_user_admin", return_value=False),          patch("cleanguard.windows.restore_point._call_srclient") as mock_call,          patch("subprocess.run") as mock_run:
        success, _ = create_restore_point("Test Snapshot")
    assert success is False
    mock_call.assert_not_called()
    mock_run.assert_not_called()
