"""
Unit tests for Privacy Scanner.
"""

from unittest.mock import patch, MagicMock
from cleanguard.core.scanner.privacy_scanner import PrivacyScanner
from cleanguard.core.contracts import CleanCategory, RiskLevel


def test_privacy_scanner_properties():
    scanner = PrivacyScanner()
    assert scanner.scanner_id == "privacy_scanner"
    assert scanner.category == CleanCategory.PRIVACY_TRACES
    assert "Privacy" in scanner.display_name


def test_privacy_scanner_allowed_roots():
    scanner = PrivacyScanner()
    roots = scanner.get_allowed_roots()
    assert isinstance(roots, list)


def test_privacy_scanner_scan(tmp_path):
    scanner = PrivacyScanner()

    # Create dummy recent lnk files
    track_file = tmp_path / "recent_doc.lnk"
    track_file.write_text("dummy track link content")

    with patch.object(scanner, "get_allowed_roots", return_value=[str(tmp_path)]):
        items = scanner.scan()
        assert len(items) == 1
        assert items[0].risk_level == RiskLevel.SAFE
        assert items[0].category == CleanCategory.PRIVACY_TRACES.value


def test_clear_clipboard_no_crash():
    res = PrivacyScanner.clear_clipboard()
    assert isinstance(res, bool)


def test_clear_run_history_no_crash():
    res = PrivacyScanner.clear_run_history()
    assert isinstance(res, int)
