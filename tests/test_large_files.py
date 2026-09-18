"""
Unit tests for Large Files Finder and Safety Protection.
"""

import os
import pytest
from cleanguard.core.scanner.large_files import LargeFileScanner, LargeFileItem


def test_category_detection():
    scanner = LargeFileScanner()
    assert scanner._detect_category("movie.mp4") == "VIDEOS"
    assert scanner._detect_category("track.flac") == "AUDIO"
    assert scanner._detect_category("backup.zip") == "ARCHIVES"
    assert scanner._detect_category("system.iso") == "ARCHIVES"
    assert scanner._detect_category("vm.vmdk") in ("DISK_IMAGES", "VIRTUAL_MACHINES")
    assert scanner._detect_category("doc.pdf") == "DOCUMENTS"
    assert scanner._detect_category("setup.exe") == "INSTALLERS"
    assert scanner._detect_category("unknown.xyz") == "OTHER"


def test_scan_path_filtering(tmp_path):
    scanner = LargeFileScanner()

    # Create dummy files
    small_file = tmp_path / "small.txt"
    small_file.write_bytes(b"A" * 100)

    large_file = tmp_path / "large.zip"
    large_file.write_bytes(b"B" * 5000)

    # Threshold 1000 bytes
    items = scanner.scan_path(str(tmp_path), min_size_bytes=1000)
    assert len(items) == 1
    assert items[0].name == "large.zip"
    assert items[0].size == 5000
    assert items[0].category == "ARCHIVES"
    assert not items[0].is_protected


def test_hard_protected_files(tmp_path):
    scanner = LargeFileScanner()

    # Simulate a pagefile.sys or hiberfil.sys
    protected_file = tmp_path / "pagefile.sys"
    protected_file.write_bytes(b"P" * 2000)

    items = scanner.scan_path(str(tmp_path), min_size_bytes=1000)
    assert len(items) == 1
    assert items[0].name == "pagefile.sys"
    assert items[0].is_protected is True


def test_delete_file_safety(tmp_path):
    scanner = LargeFileScanner()

    normal_file = tmp_path / "temp_video.mp4"
    normal_file.write_bytes(b"V" * 2000)

    items = scanner.scan_path(str(tmp_path), min_size_bytes=1000)
    assert len(items) == 1
    item = items[0]

    # Deleting normal file should succeed
    ok, msg = scanner.delete_file(item)
    assert ok is True
    assert not normal_file.exists()

    # If file was protected, deletion must be blocked
    mock_protected_item = LargeFileItem(
        path=r"C:\Windows\System32\ntoskrnl.exe",
        name="ntoskrnl.exe",
        size=10000000,
        extension=".exe",
        category="EXECUTABLES",
        modified_at=0.0,
        drive="C:",
        is_protected=True,
    )
    ok_p, msg_p = scanner.delete_file(mock_protected_item)
    assert ok_p is False
    assert "SafetyEngine" in msg_p


def test_scan_invalid_path():
    scanner = LargeFileScanner()
    items = scanner.scan_path(r"Z:\NonExistentDirectoryForTesting12345")
    assert items == []
