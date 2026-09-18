"""
Unit tests for the Smart PyInstaller Temp Cleanup Rule.
Verifies multi-layered safety (active process blocking, age threshold, lock checking, and empty dir pruning).
"""

import os
import time
import pytest
from cleanguard.core.contracts import RiskLevel, CleanCategory
from cleanguard.security.pyinstaller_tracker import PyInstallerTracker
from cleanguard.security.risk_engine import RiskEngine
from cleanguard.core.safety import SafetyEngine
from cleanguard.core.cleaner.executor import CleanupExecutor
from cleanguard.core.contracts import ScanItem, CleanupStrategy


def test_extract_pid_from_dirname():
    tracker = PyInstallerTracker()
    assert tracker.extract_pid_from_dirname("_MEI119602") == 119602
    assert tracker.extract_pid_from_dirname("_MEI12345") == 12345
    # Hex PID format: 0x2bdc = 11228
    assert tracker.extract_pid_from_dirname("_MEI00002bdc2") == 11228
    assert tracker.extract_pid_from_dirname("_MEInonnumeric") is None
    assert tracker.extract_pid_from_dirname("regular_folder") is None


def test_find_mei_root(tmp_path):
    tracker = PyInstallerTracker()
    temp_root = str(tmp_path)
    mei_dir = os.path.join(temp_root, "_MEI123456")
    os.makedirs(mei_dir, exist_ok=True)
    sub_dir = os.path.join(mei_dir, "PySide6", "plugins")
    os.makedirs(sub_dir, exist_ok=True)
    target_file = os.path.join(sub_dir, "test.dll")
    with open(target_file, "w") as f:
        f.write("dummy dll")

    # Should identify the _MEI root
    found_root = tracker.find_mei_root(target_file, allowed_temp_roots=[temp_root])
    assert found_root is not None
    assert os.path.normcase(found_root) == os.path.normcase(mei_dir)

    # Non-MEI directory under temp root
    other_dir = os.path.join(temp_root, "some_app")
    os.makedirs(other_dir, exist_ok=True)
    other_file = os.path.join(other_dir, "test.dll")
    with open(other_file, "w") as f:
        f.write("dummy dll")
    assert tracker.find_mei_root(other_file, allowed_temp_roots=[temp_root]) is None


def test_active_process_blocks_cleanup(tmp_path, monkeypatch):
    tracker = PyInstallerTracker()
    temp_root = str(tmp_path)
    mei_dir = os.path.join(temp_root, "_MEI99999")
    os.makedirs(mei_dir, exist_ok=True)
    dll_path = os.path.join(mei_dir, "module.dll")
    with open(dll_path, "w") as f:
        f.write("dummy dll")

    # Simulate active process with PID 99999
    monkeypatch.setattr(
        tracker,
        "get_active_process_info",
        lambda max_cache_age_sec=5.0: ({99999}, set()),
    )

    is_pyi, risk, reason = tracker.evaluate_path(
        dll_path, min_age_hours=24.0, allowed_temp_roots=[temp_root]
    )
    assert is_pyi is True
    assert risk == RiskLevel.BLOCKED
    assert "running" in reason or "active" in reason


def test_recent_mei_directory_is_review(tmp_path, monkeypatch):
    tracker = PyInstallerTracker()
    temp_root = str(tmp_path)
    mei_dir = os.path.join(temp_root, "_MEI88888")
    os.makedirs(mei_dir, exist_ok=True)
    dll_path = os.path.join(mei_dir, "module.dll")
    with open(dll_path, "w") as f:
        f.write("dummy dll")

    # Set mtime to 2 hours ago (recent)
    past_time = time.time() - (2 * 3600)
    os.utime(mei_dir, (past_time, past_time))
    os.utime(dll_path, (past_time, past_time))

    # Simulate no active process
    monkeypatch.setattr(
        tracker,
        "get_active_process_info",
        lambda max_cache_age_sec=5.0: (set(), set()),
    )

    is_pyi, risk, reason = tracker.evaluate_path(
        dll_path, min_age_hours=24.0, allowed_temp_roots=[temp_root]
    )
    assert is_pyi is True
    assert risk == RiskLevel.REVIEW
    assert "review" in reason.lower() or "recent" in reason.lower()


def test_orphaned_old_mei_directory_is_safe(tmp_path, monkeypatch):
    tracker = PyInstallerTracker()
    temp_root = str(tmp_path)
    mei_dir = os.path.join(temp_root, "_MEI77777")
    os.makedirs(mei_dir, exist_ok=True)
    dll_path = os.path.join(mei_dir, "module.dll")
    with open(dll_path, "w") as f:
        f.write("dummy dll")

    # Set mtime to 48 hours ago (> 24h)
    past_time = time.time() - (48 * 3600)
    os.utime(mei_dir, (past_time, past_time))
    os.utime(dll_path, (past_time, past_time))

    # Simulate no active process
    monkeypatch.setattr(
        tracker,
        "get_active_process_info",
        lambda max_cache_age_sec=5.0: (set(), set()),
    )

    is_pyi, risk, reason = tracker.evaluate_path(
        dll_path, min_age_hours=24.0, allowed_temp_roots=[temp_root]
    )
    assert is_pyi is True
    assert risk == RiskLevel.SAFE
    assert "terminated" in reason.lower() or "orphaned" in reason.lower()


def test_risk_engine_integration_with_pyinstaller(tmp_path, monkeypatch):
    temp_root = str(tmp_path)
    mei_dir = os.path.join(temp_root, "_MEI11111")
    os.makedirs(mei_dir, exist_ok=True)
    dll_inside_mei = os.path.join(mei_dir, "qtcore.dll")
    with open(dll_inside_mei, "w") as f:
        f.write("binary content")

    # Set age to 30 hours
    past_time = time.time() - (30 * 3600)
    os.utime(mei_dir, (past_time, past_time))
    os.utime(dll_inside_mei, (past_time, past_time))

    # Standard non-PyInstaller DLL in temp
    normal_temp_dll = os.path.join(temp_root, "standalone.dll")
    with open(normal_temp_dll, "w") as f:
        f.write("binary content")
    os.utime(normal_temp_dll, (past_time, past_time))

    risk_engine = RiskEngine()
    # Mock no active process
    monkeypatch.setattr(
        risk_engine.pyinstaller_tracker,
        "get_active_process_info",
        lambda max_cache_age_sec=5.0: (set(), set()),
    )

    # 1. DLL inside orphaned _MEI folder -> SAFE
    risk1, reason1, deletable1 = risk_engine.evaluate(
        path=dll_inside_mei,
        category=CleanCategory.TEMP_FILES.value,
        modified_at=past_time,
        allowed_roots=[temp_root],
    )
    assert risk1 == RiskLevel.SAFE
    assert deletable1 is True
    assert "PyInstaller" in reason1

    # 2. DLL outside _MEI folder -> strictly BLOCKED (defense in depth)
    risk2, reason2, deletable2 = risk_engine.evaluate(
        path=normal_temp_dll,
        category=CleanCategory.TEMP_FILES.value,
        modified_at=past_time,
        allowed_roots=[temp_root],
    )
    assert risk2 == RiskLevel.BLOCKED
    assert deletable2 is False
    assert "Executable binary file" in reason2


def test_executor_prunes_empty_mei_directory(tmp_path):
    temp_root = str(tmp_path)
    mei_dir = os.path.join(temp_root, "_MEI33333")
    sub_dir = os.path.join(mei_dir, "sub")
    os.makedirs(sub_dir, exist_ok=True)
    file1 = os.path.join(sub_dir, "test.tmp")
    with open(file1, "w") as f:
        f.write("data")

    import types
    from cleanguard.core.cleaner import executor as exec_mod

    fake_folders = types.SimpleNamespace(user_temp=temp_root, system_temp="")
    orig_get_known = exec_mod.get_known_folders
    exec_mod.get_known_folders = lambda: fake_folders

    try:
        executor = CleanupExecutor()
        item = ScanItem(
            path=file1,
            name="test.tmp",
            size=len("data"),
            modified_at=time.time() - 3600,
            category=CleanCategory.TEMP_FILES.value,
            risk_level=RiskLevel.SAFE,
            reason="Orphaned temp file",
            rule_id="RULE-PYINSTALLER-ORPHAN",
            is_locked=False,
            is_symlink=False,
            is_junction=False,
            is_deletable=True,
            selected=True,
        )

        summary = executor.execute(
            planned_items=[item],
            strategy=CleanupStrategy.SAFE_DELETE,
            scan_id="test_scan",
        )

        assert summary.files_deleted == 1
        assert not os.path.exists(file1)
        # Empty subdirectories and _MEI directory should be safely pruned
        assert not os.path.exists(sub_dir)
        assert not os.path.exists(mei_dir)
        # The temp root itself must never be removed
        assert os.path.exists(temp_root)
    finally:
        exec_mod.get_known_folders = orig_get_known
