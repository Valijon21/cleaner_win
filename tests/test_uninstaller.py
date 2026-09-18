"""
Unit tests for Windows AppUninstallerManager.
"""

from unittest.mock import patch, MagicMock
from cleanguard.windows.uninstaller import AppUninstallerManager, InstalledApp
from cleanguard.core.contracts import RiskLevel


def test_uninstaller_manager_initialization():
    mgr = AppUninstallerManager()
    assert mgr is not None


def test_get_installed_apps_runs_without_exception():
    mgr = AppUninstallerManager()
    apps = mgr.get_installed_apps()
    assert isinstance(apps, list)
    # Most Windows installations have at least some installed applications
    for a in apps[:5]:
        assert isinstance(a, InstalledApp)
        assert len(a.name) > 0


def test_find_leftovers_safety_enforcement(tmp_path):
    mgr = AppUninstallerManager()
    mgr.localappdata = str(tmp_path)

    # Create dummy app leftover directory
    dummy_app_dir = tmp_path / "DummyTestApp"
    dummy_app_dir.mkdir()
    (dummy_app_dir / "cache.bin").write_text("dummy leftover data")

    leftovers = mgr.find_leftovers("DummyTestApp")
    assert len(leftovers) == 1
    assert leftovers[0].name == "DummyTestApp"
    assert leftovers[0].risk_level == RiskLevel.REVIEW


def test_launch_uninstall_msi():
    mgr = AppUninstallerManager()
    app = InstalledApp(
        id="HKLM_Test",
        name="TestApp",
        publisher="TestPub",
        version="1.0",
        install_date="20260101",
        estimated_size=1024,
        uninstall_string="MsiExec.exe /X{12345678-ABCD-1234-ABCD-1234567890AB}",
        install_location="",
        registry_hive="HKLM",
    )

    with patch("subprocess.Popen") as mock_popen:
        success, msg = mgr.launch_uninstall(app)
        assert success is True
        assert mock_popen.called
