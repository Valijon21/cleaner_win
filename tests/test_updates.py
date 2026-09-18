"""
Unit tests for Windows Update and WinSxS Component Store Cleaner.
"""

import os
import subprocess
from unittest.mock import patch, MagicMock
from cleanguard.windows.updates import WindowsUpdateCleaner


def test_windows_update_cleaner_init():
    cleaner = WindowsUpdateCleaner()
    assert "SoftwareDistribution" in cleaner.download_dir
    assert "Download" in cleaner.download_dir


def test_get_cache_size():
    cleaner = WindowsUpdateCleaner()
    sz = cleaner.get_cache_size()
    assert isinstance(sz, int)
    assert sz >= 0


def test_clean_download_cache_custom_dir(tmp_path):
    # Test cleaning on a controlled mock download directory
    mock_download = tmp_path / "SoftwareDistribution" / "Download"
    mock_download.mkdir(parents=True)

    file1 = mock_download / "update1.cab"
    file1.write_bytes(b"A" * 1024)

    file2 = mock_download / "update2.msu"
    file2.write_bytes(b"B" * 2048)

    sub_dir = mock_download / "nested"
    sub_dir.mkdir()
    file3 = sub_dir / "patch.bin"
    file3.write_bytes(b"C" * 512)

    cleaner = WindowsUpdateCleaner(download_dir=str(mock_download))
    cache_sz = cleaner.get_cache_size()
    assert cache_sz == 1024 + 2048 + 512

    ok, reclaimed, msg = cleaner.clean_update_download_cache(check_admin=False)
    assert ok
    assert reclaimed == 1024 + 2048 + 512
    assert not file1.exists()
    assert not file2.exists()
    assert not file3.exists()
    assert cleaner.get_cache_size() == 0


def test_run_dism_non_admin():
    cleaner = WindowsUpdateCleaner()
    with patch("cleanguard.windows.updates.is_user_admin", return_value=False):
        ok, msg = cleaner.run_dism_component_cleanup()
        assert not ok
        assert "Administrator" in msg


def test_run_dism_success():
    cleaner = WindowsUpdateCleaner()
    with patch("cleanguard.windows.updates.is_user_admin", return_value=True):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "The operation completed successfully.\n100.0%"
        mock_proc.stderr = ""
        with patch("subprocess.run", return_value=mock_proc):
            ok, msg = cleaner.run_dism_component_cleanup()
            assert ok
            assert "successfully" in msg


def test_run_dism_failure():
    cleaner = WindowsUpdateCleaner()
    with patch("cleanguard.windows.updates.is_user_admin", return_value=True):
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = "Error: 0x800f0806"
        mock_proc.stderr = "Component store cleanup failed."
        with patch("subprocess.run", return_value=mock_proc):
            ok, msg = cleaner.run_dism_component_cleanup()
            assert not ok
            assert "0x800f0806" in msg
