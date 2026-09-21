"""
Unit tests for Custom Protected Paths (Whitelist / Exclusion List) in CleanGuard.
"""

import pytest
from cleanguard.core.config import ConfigManager
from cleanguard.security.protected_paths import ProtectedPathRegistry
from cleanguard.security.path_guard import PathGuard
from cleanguard.security.risk_engine import RiskEngine, RiskLevel
from cleanguard.core.contracts import CleanCategory


@pytest.fixture
def clean_config(tmp_path):
    """Fixture providing an isolated configuration instance."""
    cfg_file = str(tmp_path / "config.json")
    config = ConfigManager(config_path=cfg_file)
    config.set("custom_protected_paths", [])
    return config


def test_whitelist_directory_protection(tmp_path, clean_config):
    """Verify that a directory added to custom protected paths is blocked."""
    reg = ProtectedPathRegistry(config_manager=clean_config)
    guard = PathGuard(protected_registry=reg)
    engine = RiskEngine(protected_registry=reg, path_guard=guard)

    # Create a dummy folder and file inside it
    secret_dir = tmp_path / "MySpecialProject"
    secret_dir.mkdir()
    secret_file = secret_dir / "data.tmp"
    secret_file.write_text("important project data")

    str_file = str(secret_file)
    str_dir = str(secret_dir)

    # Before adding to whitelist:
    valid, _, _ = guard.validate_target_path(str_file, allowed_boundary_roots=[str(tmp_path)])
    assert valid is True

    # Add directory to whitelist
    reg.add_custom_protected_path(str_dir)

    # After adding to whitelist: PathGuard must report PROTECTED_PATH
    valid, err_code, reason = guard.validate_target_path(str_file, allowed_boundary_roots=[str(tmp_path)])
    assert valid is False
    assert "protected location" in reason.lower()

    # RiskEngine evaluation must be BLOCKED
    risk, r_reason, deletable = engine.evaluate(
        path=str_file,
        category=CleanCategory.TEMP_FILES.value,
        allowed_roots=[str(tmp_path)],
    )
    assert risk == RiskLevel.BLOCKED
    assert deletable is False


def test_whitelist_individual_file_protection(tmp_path, clean_config):
    """Verify that an individual file added to custom protected paths is blocked."""
    reg = ProtectedPathRegistry(config_manager=clean_config)
    guard = PathGuard(protected_registry=reg)
    engine = RiskEngine(protected_registry=reg, path_guard=guard)

    test_file = tmp_path / "important_archive.zip"
    test_file.write_text("zip content")
    str_file = str(test_file)

    # Add specific file to whitelist
    reg.add_custom_protected_path(str_file)
    assert reg.is_protected_path(str_file) is True

    # RiskEngine evaluation must be BLOCKED
    risk, _, deletable = engine.evaluate(
        path=str_file,
        category=CleanCategory.TEMP_FILES.value,
        allowed_roots=[str(tmp_path)],
    )
    assert risk == RiskLevel.BLOCKED
    assert deletable is False


def test_whitelist_removal(tmp_path, clean_config):
    """Verify that removing a path from custom protected paths unblocks it."""
    reg = ProtectedPathRegistry(config_manager=clean_config)

    custom_folder = str(tmp_path / "TempFolder")
    reg.add_custom_protected_path(custom_folder)
    assert reg.is_protected_path(custom_folder) is True

    # Remove it
    reg.remove_custom_protected_path(custom_folder)
    assert reg.is_protected_path(custom_folder) is False
