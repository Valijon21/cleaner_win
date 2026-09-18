"""
Unit tests for Duplicate Files Scanner.
"""

import os
from cleanguard.core.scanner.duplicate_scanner import DuplicateScanner, DuplicateGroup


def test_duplicate_scanner_detects_duplicates(tmp_path):
    scanner = DuplicateScanner()

    # Create distinct files
    file_a = tmp_path / "file_a.txt"
    file_a.write_text("Hello CleanGuard World! " * 50)

    file_b = tmp_path / "file_b.txt"
    file_b.write_text("Different content here " * 60)

    # Create duplicates of file_a
    file_a_copy1 = tmp_path / "file_a_copy1.txt"
    file_a_copy1.write_text("Hello CleanGuard World! " * 50)

    file_a_copy2 = tmp_path / "subfolder" / "file_a_copy2.txt"
    file_a_copy2.parent.mkdir()
    file_a_copy2.write_text("Hello CleanGuard World! " * 50)

    groups = scanner.scan_directory(str(tmp_path), min_size_bytes=10)

    assert len(groups) == 1
    grp = groups[0]
    assert len(grp.items) == 3
    assert grp.file_size == len(file_a.read_bytes())
    assert grp.reclaimable_bytes == grp.file_size * 2


def test_duplicate_scanner_no_duplicates(tmp_path):
    scanner = DuplicateScanner()

    f1 = tmp_path / "f1.dat"
    f1.write_bytes(b"content 1" * 100)

    f2 = tmp_path / "f2.dat"
    f2.write_bytes(b"content 2" * 100)

    groups = scanner.scan_directory(str(tmp_path), min_size_bytes=10)
    assert len(groups) == 0


def test_duplicate_scanner_prunes_protected_paths():
    scanner = DuplicateScanner()
    # Attempting to scan windows system dir should return empty immediately
    res = scanner.scan_directory(r"C:\Windows\System32")
    assert res == []
