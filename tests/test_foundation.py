"""
Unit tests for Foundation (Phase 0).
"""

import os
import tempfile
import pytest
from cleanguard.app.version import APP_NAME, APP_VERSION, get_version_string
from cleanguard.utils.formatting import format_bytes, format_duration, calculate_age_days
from cleanguard.utils.filesystem import normalize_path, is_path_under_directory
from cleanguard.core.contracts import RiskLevel, ErrorCode, ScanItem, DriveInfo
from cleanguard.core.config import ConfigManager


def test_version_info():
    assert APP_NAME == "CleanGuard"
    assert APP_VERSION == "0.1.0"
    v_str = get_version_string()
    assert "CleanGuard" in v_str
    assert "0.1.0" in v_str


def test_format_bytes():
    assert format_bytes(0) == "0 B"
    assert format_bytes(500) == "500 B"
    assert format_bytes(1024) == "1.00 KB"
    assert format_bytes(1024 * 1024) == "1.00 MB"
    assert format_bytes(1024 * 1024 * 1024 * 2.5) == "2.50 GB"


def test_format_duration():
    assert "ms" in format_duration(0.5)
    assert "s" in format_duration(15.2)
    assert "m" in format_duration(125.0)


def test_path_normalization_and_containment():
    base = tempfile.gettempdir()
    child = os.path.join(base, "cleanguard_test_sub", "file.txt")
    
    assert is_path_under_directory(child, base) is True
    # Path outside
    outside = "C:\\SomeOtherFolder\\file.txt"
    assert is_path_under_directory(outside, base) is False


def test_contracts_creation():
    item = ScanItem(
        path="C:\\Temp\\test.tmp",
        name="test.tmp",
        size=1024,
        modified_at=1000.0,
        category="temp_files",
        risk_level=RiskLevel.SAFE,
        reason="Temporary file",
        rule_id="RULE-TEMP-01",
    )
    assert item.risk_level == RiskLevel.SAFE
    d = item.to_dict()
    assert d["name"] == "test.tmp"
    assert d["risk_level"] == "SAFE"


def test_config_manager():
    with tempfile.TemporaryDirectory() as td:
        cfg_file = os.path.join(td, "test_config.json")
        cfg = ConfigManager(config_path=cfg_file)
        assert cfg.get("language") == "uz"
        cfg.set("language", "en")
        assert cfg.get("language") == "en"
        assert os.path.exists(cfg_file)
