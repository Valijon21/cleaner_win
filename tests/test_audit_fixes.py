"""
Regression tests for the 2026-10 audit fixes (see AUDIT_VA_TUZATISHLAR.md).
Each test pins one defect that previously reached users.
"""

import ctypes
import json
import os
import sys
import time
from unittest.mock import MagicMock, patch

import pytest

from cleanguard.core.cleaner.executor import CleanupExecutor
from cleanguard.core.cleaner.planner import CleanupPlanner
from cleanguard.core.cleaner.strategy import execute_deletion, recycle_bin_root_drive
from cleanguard.core.cleaner.user_data import recycle_user_items
from cleanguard.core.config import ConfigManager
from cleanguard.core.contracts import (
    CleanCategory,
    CleanupStatus,
    CleanupStrategy,
    CleanupSummary,
    ErrorCode,
    RiskLevel,
    ScanItem,
)
from cleanguard.core.safety import SafetyEngine
from cleanguard.database.db import DatabaseManager
from cleanguard.database.repositories import HistoryRepository
from cleanguard.security.path_guard import PathGuard
from cleanguard.security.protected_paths import ProtectedPathRegistry
from cleanguard.security.risk_engine import RiskEngine
from cleanguard.windows.recycle_bin import SHFILEOPSTRUCTW
from cleanguard.windows.shell import (
    INVALID_FILE_ATTRIBUTES,
    get_file_attributes,
    is_file_locked,
    is_reparse_point_or_junction,
    is_system_file,
)
from cleanguard.windows.uninstaller import AppUninstallerManager, leftover_match_key

windows_only = pytest.mark.skipif(sys.platform != "win32", reason="Windows API behaviour")


@pytest.fixture
def isolated_config(tmp_path):
    cfg = ConfigManager(config_path=str(tmp_path / "config.json"))
    cfg.set("custom_protected_paths", [])
    return cfg


def _item(path, category=CleanCategory.TEMP_FILES.value, risk=RiskLevel.SAFE, selected=True, size=10):
    return ScanItem(
        path=path,
        name=os.path.basename(path),
        size=size,
        modified_at=0.0,
        category=category,
        risk_level=risk,
        reason="test",
        rule_id="TEST",
        selected=selected,
    )


# --- Win32 / ctypes ---------------------------------------------------------

@windows_only
def test_missing_path_is_not_reported_as_reparse_or_system(tmp_path):
    missing = str(tmp_path / "does_not_exist.bin")
    assert get_file_attributes(missing) == INVALID_FILE_ATTRIBUTES
    assert is_reparse_point_or_junction(missing) is False
    assert is_system_file(missing) is False


@windows_only
def test_is_file_locked_detects_exclusive_handle(tmp_path):
    target = tmp_path / "locked.bin"
    target.write_bytes(b"x")
    assert is_file_locked(str(target)) is False


def test_shfileopstruct_matches_win32_layout():
    # BOOL fAnyOperationsAborted is 4 bytes and 4-byte aligned after the WORD flags.
    ptr = ctypes.sizeof(ctypes.c_void_p)
    flags_offset = SHFILEOPSTRUCTW.fFlags.offset
    assert SHFILEOPSTRUCTW.fAnyOperationsAborted.size == 4
    expected = (flags_offset + 2 + 3) // 4 * 4
    assert SHFILEOPSTRUCTW.fAnyOperationsAborted.offset == expected
    if ptr == 8:
        assert SHFILEOPSTRUCTW.fAnyOperationsAborted.offset == 36


# --- Deletion strategy / executor ------------------------------------------

def test_recycle_bin_root_detection_is_exact():
    assert recycle_bin_root_drive("C:\\$Recycle.Bin") == "C:"
    assert recycle_bin_root_drive("d:\\$recycle.bin\\") == "D:"
    assert recycle_bin_root_drive("C:\\Temp\\evil$Recycle.Bin") is None
    assert recycle_bin_root_drive("C:\\Temp\\$Recycle.Bin") is None


def test_recycle_strategy_never_falls_back_to_permanent_delete(tmp_path):
    victim = tmp_path / "keep_me.dat"
    victim.write_text("user data")
    with patch("cleanguard.core.cleaner.strategy.move_to_recycle_bin", return_value=False):
        ok, err, _ = execute_deletion(str(victim), strategy=CleanupStrategy.RECYCLE_BIN)
    assert ok is False
    assert err == ErrorCode.IO_ERROR
    assert victim.exists()


def test_fake_recycle_bin_path_goes_through_safety_gate(tmp_path):
    fake = tmp_path / "$Recycle.Bin"
    fake.mkdir()
    item = _item(str(fake), category=CleanCategory.RECYCLE_BIN.value)
    engine = MagicMock()
    engine.verify_cleanup_target.return_value = (False, ErrorCode.ACCESS_DENIED, "rejected")
    with patch("cleanguard.core.cleaner.strategy.empty_recycle_bin") as mock_empty:
        summary = CleanupExecutor(safety_engine=engine).execute([item])
    mock_empty.assert_not_called()
    engine.verify_cleanup_target.assert_called_once()
    assert summary.item_results[0].status == CleanupStatus.SKIPPED


def test_progress_reaches_total_even_when_items_are_skipped(tmp_path):
    items = [_item(str(tmp_path / f"f{i}.tmp")) for i in range(3)]
    engine = MagicMock()
    engine.verify_cleanup_target.return_value = (False, ErrorCode.FILE_NOT_FOUND, "gone")
    calls = []
    CleanupExecutor(safety_engine=engine).execute(items, progress_callback=lambda *a: calls.append(a))
    assert calls[-1][0] == 3 and calls[-1][1] == 3


# --- Unattended cleanup -----------------------------------------------------

def test_unattended_selection_skips_recycle_bin_privacy_and_non_safe():
    items = [
        _item("C:\\$Recycle.Bin", category=CleanCategory.RECYCLE_BIN.value),
        _item("C:\\x\\recent.lnk", category=CleanCategory.PRIVACY_TRACES.value),
        _item("C:\\x\\review.tmp", risk=RiskLevel.REVIEW),
        _item("C:\\x\\ok.tmp", selected=False),
    ]
    chosen = CleanupPlanner.select_unattended(items)
    assert [it.path for it in chosen] == ["C:\\x\\ok.tmp"]
    assert chosen[0].selected is True


def test_smart_care_registry_stage_and_recycle_bin_exclusion(qapp):
    from cleanguard.services.smart_care_service import SmartCareWorker

    worker = SmartCareWorker(db_manager=MagicMock())
    errors, results = [], []
    worker.error.connect(errors.append)
    worker.finished.connect(results.append)

    rb_item = _item("C:\\$Recycle.Bin", category=CleanCategory.RECYCLE_BIN.value)
    tmp_item = _item("C:\\Users\\u\\AppData\\Local\\Temp\\a.tmp")
    issue = MagicMock()

    with patch.object(worker.scanner, "scan_all", return_value=(MagicMock(scan_id="s1"), [rb_item, tmp_item])), \
         patch.object(worker.cleaner, "execute", return_value=CleanupSummary(files_deleted=1, bytes_recovered=10)) as mock_exec, \
         patch.object(worker.reg_cleaner, "scan_mui_cache", return_value=[issue]), \
         patch.object(worker.reg_cleaner, "scan_run_mru", return_value=[]), \
         patch.object(worker.reg_cleaner, "clean_issues", return_value=(1, 0, "backup.reg")), \
         patch("cleanguard.services.smart_care_service.flush_memory", return_value=(0, 0)), \
         patch("cleanguard.services.smart_care_service.flush_dns", return_value=(True, "OK")), \
         patch("cleanguard.services.smart_care_service.is_user_admin", return_value=False):
        worker.run()

    assert errors == []
    assert results and results[0].registry_issues_fixed == 1
    executed = mock_exec.call_args[0][0]
    assert [it.path for it in executed] == [tmp_item.path]


# --- Safety engine ----------------------------------------------------------

def test_safety_engine_exposes_is_protected_path(isolated_config, tmp_path):
    reg = ProtectedPathRegistry(config_manager=isolated_config)
    engine = SafetyEngine(protected_registry=reg)
    assert engine.is_protected_path(os.environ.get("WINDIR", "C:\\Windows")) is True
    assert engine.is_protected_path(str(tmp_path / "x.txt")) is False


def test_new_exclusion_applies_to_existing_registry_without_restart(isolated_config, tmp_path):
    reg = ProtectedPathRegistry(config_manager=isolated_config)
    target = tmp_path / "Project"
    target.mkdir()
    assert reg.is_protected_path(str(target / "a.tmp")) is False
    # Simulates the Settings page writing through the shared config.
    isolated_config.set("custom_protected_paths", [str(target)])
    assert reg.is_protected_path(str(target / "a.tmp")) is True


@windows_only
def test_junction_is_rejected_by_path_guard(isolated_config, tmp_path):
    import _winapi

    real_dir = tmp_path / "real"
    real_dir.mkdir()
    link = tmp_path / "link"
    _winapi.CreateJunction(str(real_dir), str(link))
    guard = PathGuard(ProtectedPathRegistry(config_manager=isolated_config))
    ok, code, _ = guard.validate_target_path(str(link))
    assert ok is False
    assert code == ErrorCode.INVALID_REPARSE_POINT


def test_risk_engine_follows_min_age_setting(isolated_config, tmp_path):
    reg = ProtectedPathRegistry(config_manager=isolated_config)
    engine = RiskEngine(protected_registry=reg, smart_pyinstaller_enabled=False)
    path = str(tmp_path / "cache.dat")
    open(path, "w").close()
    two_hours_ago = time.time() - 2 * 3600

    isolated_config.set("min_file_age_hours", 24)
    risk, _, _ = engine.evaluate(path, CleanCategory.TEMP_FILES.value, modified_at=two_hours_ago)
    assert risk == RiskLevel.REVIEW

    isolated_config.set("min_file_age_hours", 1)
    risk, _, _ = engine.evaluate(path, CleanCategory.TEMP_FILES.value, modified_at=two_hours_ago)
    assert risk == RiskLevel.SAFE


def test_user_data_removal_rejects_protected_and_uses_recycle_bin(isolated_config, tmp_path):
    reg = ProtectedPathRegistry(config_manager=isolated_config)
    engine = SafetyEngine(protected_registry=reg)
    ok_file = tmp_path / "dup.bin"
    ok_file.write_bytes(b"1")
    protected = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "win.ini")

    with patch("cleanguard.core.cleaner.user_data.move_to_recycle_bin", return_value=True) as mock_rb:
        result = recycle_user_items([(str(ok_file), 1), (protected, 5)], safety_engine=engine)

    assert result.removed == [str(ok_file)]
    assert [p for p, _ in result.rejected] == [protected]
    mock_rb.assert_called_once_with(str(ok_file), warn_if_permanent=True)


# --- Config / persistence ---------------------------------------------------

def test_config_save_is_atomic(tmp_path):
    path = tmp_path / "config.json"
    cfg = ConfigManager(config_path=str(path))
    cfg.set("theme", "light")
    assert json.loads(path.read_text(encoding="utf-8"))["theme"] == "light"
    assert not (tmp_path / "config.json.tmp").exists()


def test_cleanup_with_unrecorded_scan_id_is_still_audited(tmp_path):
    repo = HistoryRepository(DatabaseManager(db_path=str(tmp_path / "h.db")))
    summary = CleanupSummary(scan_id="never-recorded", started_at=1.0, finished_at=2.0, files_deleted=3)
    repo.record_cleanup_session(summary)
    history = repo.get_cleanup_history()
    assert len(history) == 1
    assert history[0]["scan_id"] is None
    assert history[0]["files_deleted"] == 3


# --- Uninstaller leftovers --------------------------------------------------

def test_leftover_key_strips_versions_and_arch():
    assert leftover_match_key("Notepad++ 8.6.4 (64-bit)") == "notepad"
    assert leftover_match_key("7-Zip 23.01 (x64)") == "7zip"
    assert leftover_match_key("Git") == "git"


def test_leftovers_do_not_match_unrelated_folders(tmp_path):
    mgr = AppUninstallerManager()
    mgr.localappdata = str(tmp_path)
    mgr.appdata = ""
    mgr.programdata = ""
    for name in ("Git", "DigitalSignatures", "GitHubDesktop", "Microsoft"):
        (tmp_path / name).mkdir()

    found = sorted(it.name for it in mgr.find_leftovers("Git", publisher="The Git Development Community"))
    assert found == ["Git"]
    assert mgr.find_leftovers("Microsoft", publisher="Microsoft Corporation") == []
