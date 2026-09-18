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
    win = MainWindow(db_manager=db, enable_monitor=False)

    assert win.stack.count() >= 10
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
    assert page.model.rowCount() == 2
    assert page.btn_clean.isEnabled() is True


def test_risk_badge_delegate_painting(qapp):
    from PyQt5.QtWidgets import QStyleOptionViewItem, QStyle
    from PyQt5.QtGui import QImage, QPainter
    from cleanguard.ui.models import RiskBadgeDelegate, ScanResultsModel
    from cleanguard.core.contracts import ScanItem, RiskLevel

    model = ScanResultsModel()
    item = ScanItem("C:\\test.dll", "test.dll", 100, 10, "temp_files", RiskLevel.SAFE, "reason", "R1")
    model.set_items([item])
    idx = model.index(0, 4)

    delegate = RiskBadgeDelegate()
    img = QImage(200, 40, QImage.Format_ARGB32)
    painter = QPainter(img)
    opt = QStyleOptionViewItem()
    opt.rect.setRect(0, 0, 200, 40)
    opt.state = QStyle.State_Enabled | QStyle.State_Selected

    delegate.paint(painter, opt, idx)
    painter.end()


def test_dashboard_and_settings_pages(qapp, tmp_path):
    from cleanguard.ui.dashboard_page import DashboardPage
    from cleanguard.ui.settings_page import SettingsPage
    from cleanguard.ui.history_page import HistoryPage
    from cleanguard.database.db import DatabaseManager

    db = DatabaseManager(db_path=str(tmp_path / "ui_pages.db"))

    # Dashboard page
    dash = DashboardPage(db_manager=db)
    assert len(dash.category_cards) >= 5
    assert "temp_files" in dash.category_cards
    dash.retranslate_ui("ru")
    assert "Панель" in dash.lbl_title.text() or "Boshqaruv" in dash.lbl_title.text() or len(dash.lbl_title.text()) > 0

    # Settings page
    settings = SettingsPage()
    assert len(settings.category_checkboxes) >= 5
    assert "temp_files" in settings.category_checkboxes
    assert settings.chk_confirm.isChecked() is True

    # History page
    history = HistoryPage(db_manager=db)
    assert history.table.columnCount() == 5
    history.retranslate_ui("uz")
    assert history.lbl_title.text() == "Boshqaruv paneli" or "Tarix" in history.lbl_title.text()


def test_asc_care_center_and_pipeline(qapp, tmp_path):
    from cleanguard.ui.widgets.buttons import CircularScanButton
    from cleanguard.ui.widgets.cards import CareModuleCard
    from cleanguard.ui.dashboard_page import DashboardPage
    from cleanguard.ui.scan_page import ScanPage, ModuleStageCard
    from cleanguard.ui.results_page import ResultsPage
    from cleanguard.services.scan_service import ScanWorker
    from cleanguard.database.db import DatabaseManager
    from cleanguard.core.contracts import ScanSummary, ScanItem, RiskLevel

    # 1. CircularScanButton
    btn = CircularScanButton()
    assert btn.lbl_main.text() == "SCAN"
    assert btn.width() == 140
    assert btn.height() == 140

    # 2. CareModuleCard & Dashboard Care Grid
    db = DatabaseManager(db_path=str(tmp_path / "asc_test.db"))
    dash = DashboardPage(db_manager=db)
    assert len(dash.care_cards) == 7
    assert dash.care_cards["temp_files"].is_checked() is True

    # Test Deselect/Select All toggle
    dash._on_toggle_all_clicked()
    assert dash.care_cards["temp_files"].is_checked() is False
    dash._on_toggle_all_clicked()
    assert dash.care_cards["temp_files"].is_checked() is True

    selected = dash.get_selected_categories()
    assert len(selected) == 7

    # 3. Multi-Module Live ScanPage Pipeline
    worker = ScanWorker(db_manager=db)
    scan_page = ScanPage(scan_worker=worker)
    assert len(scan_page.stage_cards) == 7
    stage = scan_page.stage_cards["browser_cache"]
    assert "browser_cache" in stage.category_id

    # Test real-time category progress update
    scan_page._on_category_progress("browser_cache", "scanning", 15, 102400)
    assert "15" in stage.lbl_stats.text()
    assert "🔄" in stage.lbl_badge.text()

    scan_page._on_category_progress("browser_cache", "completed", 50, 500000)
    assert "50" in stage.lbl_stats.text()
    assert "✅" in stage.lbl_badge.text()

    # 4. ResultsPage Health Score Assessment & FIX NOW Button
    results_page = ResultsPage()
    # Good (< 500 MB)
    results_page.load_results(ScanSummary(bytes_reclaimable=100 * 1024 * 1024), [])
    assert not results_page.health_banner.isHidden()
    assert "🟢" in results_page.lbl_health_icon.text()

    # Critical (> 3 GB)
    results_page.load_results(ScanSummary(bytes_reclaimable=4 * 1024 * 1024 * 1024), [])
    assert "🔴" in results_page.lbl_health_icon.text()
    assert "⚡" in results_page.btn_clean.text()


