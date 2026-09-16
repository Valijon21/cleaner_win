"""
Unit and Integration tests for Safety Engine (Phase 4).
Validates critical safety boundaries, protected paths, and traversal prevention.
"""

import os
import tempfile
import pytest
from cleanguard.core.safety import SafetyEngine
from cleanguard.core.contracts import RiskLevel, ErrorCode, CleanCategory
from cleanguard.windows.known_folders import get_known_folders


@pytest.fixture
def safety_engine():
    return SafetyEngine()


def test_system32_path_is_blocked(safety_engine):
    folders = get_known_folders()
    bad_path = os.path.join(folders.system32, "kernel32.dll")
    risk, reason, deletable = safety_engine.evaluate_scan_candidate(
        path=bad_path,
        category=CleanCategory.TEMP_FILES.value,
    )
    assert risk == RiskLevel.BLOCKED
    assert deletable is False


def test_winsxs_path_is_blocked(safety_engine):
    folders = get_known_folders()
    bad_path = os.path.join(folders.winsxs, "some_component.dll")
    risk, reason, deletable = safety_engine.evaluate_scan_candidate(
        path=bad_path,
        category=CleanCategory.TEMP_FILES.value,
    )
    assert risk == RiskLevel.BLOCKED
    assert deletable is False


def test_documents_and_desktop_blocked(safety_engine):
    folders = get_known_folders()
    doc_file = os.path.join(folders.documents, "my_thesis.docx")
    risk_doc, _, deletable_doc = safety_engine.evaluate_scan_candidate(
        path=doc_file,
        category=CleanCategory.TEMP_FILES.value,
    )
    assert risk_doc == RiskLevel.BLOCKED
    assert deletable_doc is False

    desk_file = os.path.join(folders.desktop, "shortcut.lnk")
    risk_desk, _, deletable_desk = safety_engine.evaluate_scan_candidate(
        path=desk_file,
        category=CleanCategory.TEMP_FILES.value,
    )
    assert risk_desk == RiskLevel.BLOCKED
    assert deletable_desk is False


def test_critical_filenames_blocked(safety_engine):
    for fname in ["pagefile.sys", "hiberfil.sys", "NTUSER.DAT", "SAM", "SYSTEM"]:
        fake_path = os.path.join("C:\\Temp", fname)
        risk, reason, deletable = safety_engine.evaluate_scan_candidate(
            path=fake_path,
            category=CleanCategory.TEMP_FILES.value,
        )
        assert risk == RiskLevel.BLOCKED
        assert deletable is False


def test_directory_traversal_blocked(safety_engine):
    folders = get_known_folders()
    # Attempt to escape Temp to Windows using ..
    traversal_path = os.path.join(folders.user_temp, "..", "..", "Windows", "System32", "calc.exe")
    risk, reason, deletable = safety_engine.evaluate_scan_candidate(
        path=traversal_path,
        category=CleanCategory.TEMP_FILES.value,
    )
    assert risk == RiskLevel.BLOCKED
    assert deletable is False


def test_allowed_roots_boundary_enforcement(safety_engine):
    with tempfile.TemporaryDirectory() as allowed_root:
        with tempfile.TemporaryDirectory() as forbidden_root:
            # File inside allowed root
            valid_file = os.path.join(allowed_root, "valid.tmp")
            with open(valid_file, "w") as f:
                f.write("temporary data")

            # File outside allowed root
            invalid_file = os.path.join(forbidden_root, "unauthorized.tmp")
            with open(invalid_file, "w") as f:
                f.write("other data")

            # Validate valid file
            approved, err, _ = safety_engine.verify_cleanup_target(
                path=valid_file,
                category=CleanCategory.TEMP_FILES.value,
                allowed_roots=[allowed_root],
            )
            assert approved is True
            assert err == ErrorCode.NONE

            # Validate invalid file (outside boundary)
            approved2, err2, _ = safety_engine.verify_cleanup_target(
                path=invalid_file,
                category=CleanCategory.TEMP_FILES.value,
                allowed_roots=[allowed_root],
            )
            assert approved2 is False
            assert err2 == ErrorCode.ACCESS_DENIED


def test_nonexistent_file_rejected(safety_engine):
    approved, err, _ = safety_engine.verify_cleanup_target(
        path="C:\\NonExistentPath_XYZ_123.tmp",
        category=CleanCategory.TEMP_FILES.value,
    )
    assert approved is False
    assert err == ErrorCode.FILE_NOT_FOUND
