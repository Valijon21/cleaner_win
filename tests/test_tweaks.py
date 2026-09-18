"""
Tests for Windows Tweaks and Bloatware Manager.
"""

import pytest
from unittest.mock import patch, MagicMock
from cleanguard.windows.tweaks import (
    TweaksManager,
    PrivacyTweak,
    BloatwareApp,
    BUILTIN_TWEAKS,
    BUILTIN_BLOATWARE,
)


def test_tweaks_manager_initialization():
    manager = TweaksManager()
    assert len(manager.tweaks) >= 5
    assert len(manager.bloatware) >= 10
    assert any(t.id == "disable_telemetry" for t in manager.tweaks)
    assert any(b.id == "cortana" for b in manager.bloatware)


def test_is_tweak_applied_mock():
    manager = TweaksManager()
    tweak = manager.tweaks[0]

    with patch("cleanguard.windows.tweaks.winreg") as mock_winreg:
        # Simulate value matches protect_value (0)
        mock_winreg.OpenKey.return_value.__enter__.return_value = MagicMock()
        mock_winreg.QueryValueEx.return_value = (0, 4)
        assert manager.is_tweak_applied(tweak) is True

        # Simulate value does not match (1)
        mock_winreg.QueryValueEx.return_value = (1, 4)
        assert manager.is_tweak_applied(tweak) is False


def test_apply_tweak_admin_requirement():
    manager = TweaksManager()
    admin_tweak = next(t for t in manager.tweaks if t.requires_admin)

    with patch("cleanguard.windows.tweaks.is_user_admin", return_value=False):
        ok, msg = manager.apply_tweak(admin_tweak, enable_protection=True)
        assert ok is False
        assert "Administrator" in msg


def test_apply_tweak_success():
    manager = TweaksManager()
    user_tweak = next(t for t in manager.tweaks if not t.requires_admin)

    with patch("cleanguard.windows.tweaks.winreg") as mock_winreg:
        mock_winreg.CreateKeyEx.return_value.__enter__.return_value = MagicMock()
        ok, msg = manager.apply_tweak(user_tweak, enable_protection=True)
        assert ok is True
        mock_winreg.SetValueEx.assert_called_once()


def test_get_bloatware_status_detection():
    manager = TweaksManager()
    mock_packages = {
        "Microsoft.549981C3F5F10",  # Cortana
        "Microsoft.BingNews",
        "Microsoft.WindowsCalculator",
    }

    with patch.object(manager, "get_installed_appx_names", return_value=mock_packages):
        status = manager.get_bloatware_status()
        cortana = next(a for a in status if a.id == "cortana")
        assert cortana.installed is True

        weather = next(a for a in status if a.id == "bing_weather")
        assert weather.installed is False


def test_remove_bloatware_execution():
    manager = TweaksManager()
    app = BloatwareApp(
        id="test_app",
        name="Test Bloat",
        package_pattern="Microsoft.TestBloat",
        description="Test description",
        category="Test",
        installed=True,
    )

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")
        ok, msg = manager.remove_bloatware(app)
        assert ok is True
        assert "muvaffaqiyatli" in msg
