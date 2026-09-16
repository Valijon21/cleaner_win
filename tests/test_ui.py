"""
Unit tests for PyQt5 UI components and Main Window.
"""

import sys
import pytest
from PyQt5.QtWidgets import QApplication
from cleanguard.ui.main_window import MainWindow
from cleanguard.ui.widgets.cards import StatCard, DriveCard
from cleanguard.ui.widgets.badges import RiskBadge
from cleanguard.core.contracts import RiskLevel, DriveInfo
from cleanguard.database.db import DatabaseManager

# Fixture to initialize QApplication once for test suite
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def test_stat_card_and_risk_badge(qapp):
    card = StatCard(title="Test", value="10 GB", subtext="Sub")
    assert card.title_label.text() == "Test"
    assert card.value_label.text() == "10 GB"

    badge_safe = RiskBadge(RiskLevel.SAFE)
    assert len(badge_safe.text()) > 0

    badge_review = RiskBadge(RiskLevel.REVIEW)
    assert len(badge_review.text()) > 0

    badge_blocked = RiskBadge(RiskLevel.BLOCKED)
    assert len(badge_blocked.text()) > 0


def test_drive_card(qapp):
    d = DriveInfo(
        letter="C:",
        drive_type="Fixed Disk",
        filesystem="NTFS",
        total_bytes=1000,
        free_bytes=400,
        used_bytes=600,
        label="Test Drive",
        is_system_drive=True,
        is_ready=True,
    )
    card = DriveCard(d)
    assert "C:" in card.lbl_title.text()
    assert card.progress_bar.value() == 60


def test_main_window_instantiation(qapp, tmp_path):
    db_path = str(tmp_path / "test_ui.db")
    db = DatabaseManager(db_path=db_path)
    win = MainWindow(db_manager=db)

    assert win.stack.count() == 7
    assert win.stack.currentIndex() == 0

    # Test navigation
    win.navigate_to(1)
    assert win.stack.currentIndex() == 1

    win.navigate_to(0)
    assert win.stack.currentIndex() == 0

    # Test live retranslation via set_language
    from cleanguard.localization import get_localization
    get_localization().set_language("ru")
    assert any("Панель" in btn.text() for btn, _ in win.nav_buttons)

    get_localization().set_language("uz")
    assert any("Boshqaruv" in btn.text() for btn, _ in win.nav_buttons)


def test_results_page_table_loading(qapp):
    from cleanguard.ui.results_page import ResultsPage
    from cleanguard.core.contracts import ScanSummary, ScanItem, RiskLevel
    page = ResultsPage()
    summary = ScanSummary(items_found=2, bytes_reclaimable=2048, safe_items=1, review_items=1)
    items = [
        ScanItem("C:\\Temp\\a.tmp", "a.tmp", 1024, 100, "temp_files", RiskLevel.SAFE, "safe temp", "R1", selected=True),
        ScanItem("C:\\Temp\\b.dmp", "b.dmp", 1024, 100, "crash_dumps", RiskLevel.REVIEW, "review dump", "R2", selected=False),
    ]
    page.load_results(summary, items)
    assert page.table.rowCount() == 2
    assert page.btn_clean.isEnabled() is True

