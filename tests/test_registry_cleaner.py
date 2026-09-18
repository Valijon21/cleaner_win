"""
Tests for Safe Registry Cleaner and Rollback Engine.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from cleanguard.windows.registry_cleaner import SafeRegistryCleaner, RegistryIssue


def test_registry_cleaner_initialization(tmp_path):
    with patch("cleanguard.windows.registry_cleaner.get_known_folders", return_value={"appdata": str(tmp_path)}):
        cleaner = SafeRegistryCleaner()
        assert os.path.exists(cleaner.backup_dir)


def test_scan_mui_cache_detects_missing_file(tmp_path):
    with patch("cleanguard.windows.registry_cleaner.get_known_folders", return_value={"appdata": str(tmp_path)}), \
         patch("cleanguard.windows.registry_cleaner.winreg") as mock_winreg:

        # Return one missing file, then raise OSError to end loop
        mock_winreg.OpenKey.return_value.__enter__.return_value = MagicMock()
        mock_winreg.EnumValue.side_effect = [
            ("C:\\NonExistent\\App\\test.exe.ApplicationCompany", "Test Corp", 1),
            OSError(),
        ]

        cleaner = SafeRegistryCleaner()
        issues = cleaner.scan_mui_cache()
        assert len(issues) == 1
        assert issues[0].issue_type == "MuiCache"
        assert "test.exe" in issues[0].details


def test_scan_run_mru(tmp_path):
    with patch("cleanguard.windows.registry_cleaner.get_known_folders", return_value={"appdata": str(tmp_path)}), \
         patch("cleanguard.windows.registry_cleaner.winreg") as mock_winreg:

        mock_winreg.OpenKey.return_value.__enter__.return_value = MagicMock()
        mock_winreg.EnumValue.side_effect = [
            ("a", "notepad.exe\\1", 1),
            ("MRUList", "a", 1),
            OSError(),
        ]

        cleaner = SafeRegistryCleaner()
        issues = cleaner.scan_run_mru()
        assert len(issues) == 1
        assert issues[0].issue_type == "RunMRU"
        assert "notepad.exe" in issues[0].details


def test_create_backup_generates_valid_reg_file(tmp_path):
    with patch("cleanguard.windows.registry_cleaner.get_known_folders", return_value={"appdata": str(tmp_path)}):
        cleaner = SafeRegistryCleaner()
        issue = RegistryIssue(
            id="test_1",
            hive_name="HKCU",
            hive=0,
            sub_key=r"Software\TestKey",
            value_name="TestVal",
            value_data="Hello",
            value_type=1,
            issue_type="MuiCache",
            details="Test",
        )
        ok, path = cleaner.create_backup([issue])
        assert ok is True
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-16") as f:
            content = f.read()
            assert "Windows Registry Editor Version 5.00" in content
            assert "[HKEY_CURRENT_USER\\Software\\TestKey]" in content
            assert '"TestVal"="Hello"' in content


def test_restore_backup_mock(tmp_path):
    with patch("cleanguard.windows.registry_cleaner.get_known_folders", return_value={"appdata": str(tmp_path)}), \
         patch("subprocess.run") as mock_run:
        cleaner = SafeRegistryCleaner()
        dummy_file = tmp_path / "test.reg"
        dummy_file.write_text("Windows Registry Editor Version 5.00")

        mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")
        ok, msg = cleaner.restore_backup(str(dummy_file))
        assert ok is True
        assert "muvaffaqiyatli" in msg
