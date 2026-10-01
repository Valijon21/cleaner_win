"""
Registry backup fidelity: values of every common type must survive
backup (.reg) -> delete -> `reg import` with their original type and data.
Uses a throw-away key under HKCU\\Software\\CleanGuardTests that is removed afterwards.
"""

import os
import sys
import uuid

import pytest

from cleanguard.windows.registry_cleaner import (
    RegistryIssue,
    SafeRegistryCleaner,
    format_reg_value,
    is_orphaned_local_path,
)

winreg = pytest.importorskip("winreg")
windows_only = pytest.mark.skipif(sys.platform != "win32", reason="Windows registry")

VALUES = [
    ("plain", "C:\\Program Files\\App \"quoted\"", winreg.REG_SZ),
    ("expand", "%SystemRoot%\\system32", winreg.REG_EXPAND_SZ),
    ("multi", ["first", "second line"], winreg.REG_MULTI_SZ),
    ("dword", 0xDEADBEEF, winreg.REG_DWORD),
    ("qword", 0x0123456789ABCDEF, winreg.REG_QWORD),
    ("binary", b"\x00\x01\xfe\xff", winreg.REG_BINARY),
    ("", "default value", winreg.REG_SZ),
]


def test_format_reg_value_encodings():
    assert format_reg_value("a", 1, winreg.REG_DWORD) == '"a"=dword:00000001'
    assert format_reg_value("", "x", winreg.REG_SZ) == '@="x"'
    assert format_reg_value("p", 'C:\\x"y', winreg.REG_SZ) == '"p"="C:\\\\x\\"y"'
    assert format_reg_value("b", b"\x0a\xff", winreg.REG_BINARY) == '"b"=hex:0a,ff'
    assert format_reg_value("e", "%A%", winreg.REG_EXPAND_SZ) == '"e"=hex(2):25,00,41,00,25,00,00,00'
    assert format_reg_value("m", ["a"], winreg.REG_MULTI_SZ) == '"m"=hex(7):61,00,00,00,00,00'
    assert format_reg_value("q", 1, winreg.REG_QWORD) == '"q"=hex(b):01,00,00,00,00,00,00,00'


def test_orphan_check_ignores_unreachable_locations(tmp_path):
    assert is_orphaned_local_path(str(tmp_path / "gone.exe")) is True
    assert is_orphaned_local_path(str(tmp_path)) is False
    assert is_orphaned_local_path("\\\\server\\share\\app.exe") is False
    unmounted = next(
        (f"{c}:" for c in "ZYXWVUTSRQPON" if not os.path.exists(f"{c}:\\")), None
    )
    if unmounted:
        assert is_orphaned_local_path(f"{unmounted}\\Apps\\tool.exe") is False


@windows_only
def test_backup_restore_roundtrip_preserves_types(tmp_path):
    sub_key = f"Software\\CleanGuardTests\\{uuid.uuid4().hex}"
    cleaner = SafeRegistryCleaner()
    cleaner.backup_dir = str(tmp_path)
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            for name, data, vtype in VALUES:
                winreg.SetValueEx(key, name, 0, vtype, data)

        issues = [
            RegistryIssue(
                id=f"t{i}", hive_name="HKCU", hive=winreg.HKEY_CURRENT_USER, sub_key=sub_key,
                value_name=name, value_data=data, value_type=vtype, issue_type="Test", details="",
            )
            for i, (name, data, vtype) in enumerate(VALUES)
        ]
        deleted, failed, backup_path = cleaner.clean_issues(issues, backup=True)
        assert (deleted, failed) == (len(VALUES), 0)
        assert backup_path and os.path.exists(backup_path)
        with open(backup_path, encoding="utf-16", newline="") as fh:
            assert "\r\r\n" not in fh.read()  # no double CR from text-mode newline translation

        ok, msg = cleaner.restore_backup(backup_path)
        assert ok, msg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            for name, data, vtype in VALUES:
                got, got_type = winreg.QueryValueEx(key, name)
                assert got_type == vtype, name
                assert got == data, name
    finally:
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, sub_key)
        except OSError:
            pass
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, "Software\\CleanGuardTests")
        except OSError:
            pass
