"""
Unit tests for Windows drive enumeration (Phase 2).
"""

from cleanguard.windows.drives import (
    enumerate_drives,
    get_system_drive_letter,
    get_drive_by_letter,
)
from cleanguard.core.contracts import DriveInfo


def test_system_drive_letter():
    letter = get_system_drive_letter()
    assert letter.endswith(":")
    assert len(letter) == 2


def test_enumerate_drives():
    drives = enumerate_drives()
    assert len(drives) > 0

    # Ensure C: drive is present
    c_drive = None
    for d in drives:
        assert isinstance(d, DriveInfo)
        assert d.letter.endswith(":")
        if d.letter == "C:":
            c_drive = d

    assert c_drive is not None
    assert c_drive.is_system_drive is True
    assert c_drive.total_bytes > 0
    assert c_drive.free_bytes > 0
    assert 0 <= c_drive.used_percentage <= 100.0


def test_get_drive_by_letter():
    c1 = get_drive_by_letter("C")
    c2 = get_drive_by_letter("C:")
    assert c1 is not None
    assert c2 is not None
    assert c1.letter == c2.letter == "C:"

    non_existent = get_drive_by_letter("Z:")
    # Could be None if Z: is not mounted
    if non_existent is not None:
        assert non_existent.letter == "Z:"
