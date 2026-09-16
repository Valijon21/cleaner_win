"""
Unit tests for Windows OS detection and capability registry (Phase 1).
"""

from cleanguard.windows.os_info import (
    get_windows_version,
    _determine_display_name,
    _evaluate_capabilities,
    WindowsVersion,
)


def test_get_windows_version_runs_without_exception():
    info = get_windows_version()
    assert isinstance(info, WindowsVersion)
    assert info.architecture in ["x64", "x86", "ARM64", "ARM"]
    assert len(info.display_name) > 0
    assert info.capabilities.is_supported_by_cleanguard is True


def test_determine_display_name():
    assert _determine_display_name(10, 0, 22631, 0, 1) == "Windows 11"
    assert _determine_display_name(10, 0, 19045, 0, 1) == "Windows 10"
    assert _determine_display_name(6, 3, 9600, 0, 1) == "Windows 8.1"
    assert _determine_display_name(6, 2, 9200, 0, 1) == "Windows 8"
    assert _determine_display_name(6, 1, 7601, 1, 1) == "Windows 7 SP1"
    assert _determine_display_name(6, 1, 7600, 0, 1) == "Windows 7"


def test_capabilities_evaluation():
    # Windows 7
    w7_caps = _evaluate_capabilities(6, 1, 7601)
    assert w7_caps.is_supported_by_cleanguard is True
    assert w7_caps.supports_modern_notifications is False

    # Windows 10 (20H2)
    w10_caps = _evaluate_capabilities(10, 0, 19042)
    assert w10_caps.is_supported_by_cleanguard is True
    assert w10_caps.supports_modern_notifications is True
    assert w10_caps.supports_per_monitor_v2_dpi is True

    # Windows XP (Unsupported)
    xp_caps = _evaluate_capabilities(5, 1, 2600)
    assert xp_caps.is_supported_by_cleanguard is False
