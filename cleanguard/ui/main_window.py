"""
Main Window: Application shell containing sidebar navigation, view stack,
UAC elevation controls, system tray icon, and background storage monitoring.
"""

from typing import List, Optional
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QStackedWidget,
    QFrame,
    QLabel,
    QMessageBox,
    QApplication,
)
from PyQt5.QtCore import Qt
from cleanguard.app.version import APP_NAME, APP_VERSION
from cleanguard.ui.theme import DARK_STYLESHEET
from cleanguard.ui.dashboard_page import DashboardPage
from cleanguard.ui.scan_page import ScanPage
from cleanguard.ui.results_page import ResultsPage
from cleanguard.ui.cleanup_page import CleanupPage
from cleanguard.ui.history_page import HistoryPage
from cleanguard.ui.settings_page import SettingsPage
from cleanguard.ui.about_page import AboutPage
from cleanguard.ui.startup_page import StartupPage
from cleanguard.ui.duplicates_page import DuplicatesPage
from cleanguard.ui.tray import CleanGuardTrayIcon
from cleanguard.services.scan_service import ScanWorker
from cleanguard.services.cleanup_service import CleanupWorker
from cleanguard.services.monitor_service import StorageMonitorService
from cleanguard.core.contracts import ScanSummary, ScanItem, CleanupSummary
from cleanguard.core.safety import SafetyEngine
from cleanguard.core.config import ConfigManager
from cleanguard.database.db import DatabaseManager
from cleanguard.windows.privileges import is_user_admin, request_elevation
from cleanguard.localization import tr, get_localization
from cleanguard.utils.formatting import format_bytes
from cleanguard.utils.logging import get_logger

logger = get_logger("ui.main")


class MainWindow(QMainWindow):
    """Primary application window and navigation controller."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None, enable_monitor: bool = True):

        super().__init__()
        self.db = db_manager or DatabaseManager()
        self.config = ConfigManager()
        self.safety_engine = SafetyEngine()
        self.scan_worker = ScanWorker(db_manager=self.db, parent=self)
        self.cleanup_worker = None
        self._force_quit = False

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1080, 720)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(DARK_STYLESHEET)

        self._init_shell()
        self._init_tray_and_monitor(enable_monitor=enable_monitor)

    def _init_shell(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        shell_layout = QHBoxLayout(central)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        # 1. Sidebar Navigation
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(240)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(12, 24, 12, 20)
        side_layout.setSpacing(8)

        # Brand / Logo Header
        brand_row = QHBoxLayout()
        lbl_logo = QLabel("🛡️")
        lbl_logo.setStyleSheet("font-size: 24px;")
        lbl_app = QLabel(APP_NAME)
        lbl_app.setStyleSheet("font-size: 20px; font-weight: 800; color: #10B981; letter-spacing: 0.5px;")
        brand_row.addWidget(lbl_logo)
        brand_row.addWidget(lbl_app)
        brand_row.addStretch()
        side_layout.addLayout(brand_row)
        side_layout.addSpacing(20)

        # Navigation Buttons
        self.nav_buttons = []
        nav_items = [
            ("📊 " + tr("nav_dashboard"), 0),
            ("🔍 " + tr("nav_scan"), 1),
            ("📋 " + tr("nav_results"), 2),
            ("🚀 " + tr("nav_startup"), 7),
            ("👥 " + tr("nav_duplicates"), 8),
            ("📜 " + tr("nav_history"), 4),
            ("⚙️ " + tr("nav_settings"), 5),
            ("ℹ️ " + tr("nav_about"), 6),
        ]

        for text, page_idx in nav_items:
            btn = QPushButton(text)
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=page_idx: self._on_nav_button_clicked(idx))
            side_layout.addWidget(btn)
            self.nav_buttons.append((btn, page_idx))

        side_layout.addStretch()

        # UAC Administrator Elevation Action / Status Badge
        self.btn_elevation = None
        self.lbl_admin_badge = None

        if is_user_admin():
            self.lbl_admin_badge = QLabel("🛡️ " + tr("admin_mode_active"))
            self.lbl_admin_badge.setStyleSheet("""
                background-color: #064E3B;
                color: #34D399;
                border: 1px solid #059669;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 700;
                padding: 6px 8px;
            """)
            self.lbl_admin_badge.setAlignment(Qt.AlignCenter)
            side_layout.addWidget(self.lbl_admin_badge)
        else:
            self.btn_elevation = QPushButton("🛡️ " + tr("btn_restart_admin"))
            self.btn_elevation.setStyleSheet("""
                QPushButton {
                    background-color: #78350F;
                    color: #FDE68A;
                    border: 1px solid #D97706;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 700;
                    padding: 6px 8px;
                }
                QPushButton:hover {
                    background-color: #92400E;
                    border: 1px solid #F59E0B;
                }
            """)
            self.btn_elevation.setCursor(Qt.PointingHandCursor)
            self.btn_elevation.clicked.connect(self._on_request_elevation)
            side_layout.addWidget(self.btn_elevation)

        # Safety Guard Badge in Sidebar Footer
        lbl_shield = QLabel("● Safety Engine Active")
        lbl_shield.setStyleSheet("color: #10B981; font-size: 11px; font-weight: 600; padding: 6px;")
        lbl_shield.setAlignment(Qt.AlignCenter)
        side_layout.addWidget(lbl_shield)

        shell_layout.addWidget(sidebar)

        # 2. Main Stacked Content Views
        self.stack = QStackedWidget()

        self.page_dashboard = DashboardPage(self.db)
        self.page_scan = ScanPage(self.scan_worker)
        self.page_results = ResultsPage()
        self.page_cleanup = CleanupPage()
        self.page_history = HistoryPage(self.db)
        self.page_settings = SettingsPage()
        self.page_about = AboutPage()
        self.page_startup = StartupPage()
        self.page_duplicates = DuplicatesPage()

        self.stack.addWidget(self.page_dashboard)   # 0
        self.stack.addWidget(self.page_scan)        # 1
        self.stack.addWidget(self.page_results)     # 2
        self.stack.addWidget(self.page_cleanup)     # 3
        self.stack.addWidget(self.page_history)     # 4
        self.stack.addWidget(self.page_settings)    # 5
        self.stack.addWidget(self.page_about)       # 6
        self.stack.addWidget(self.page_startup)     # 7
        self.stack.addWidget(self.page_duplicates)  # 8

        shell_layout.addWidget(self.stack)

        # Connect inter-page signals
        self.page_dashboard.start_scan_requested.connect(self._on_dashboard_start_scan)
        self.page_dashboard.start_category_scan_requested.connect(self._on_category_scan_requested)
        self.page_scan.scan_completed.connect(self._on_scan_completed)
        self.page_scan.scan_cancelled.connect(lambda: self.navigate_to(0))
        self.page_results.cleanup_requested.connect(self._on_cleanup_requested)
        self.page_cleanup.done_clicked.connect(self._on_cleanup_done)
        self.page_cleanup.cancel_clicked.connect(self._on_cleanup_cancel)

        # Register live retranslation on language switch
        get_localization().register_listener(self.retranslate_ui)

        self.navigate_to(0)

    def _init_tray_and_monitor(self, enable_monitor: bool = True) -> None:
        """Initialize system tray integration and background disk monitor."""
        self.tray_icon = CleanGuardTrayIcon(parent=self)
        self.tray_icon.show_window_requested.connect(self._show_and_activate)
        self.tray_icon.quick_clean_requested.connect(self._on_tray_quick_clean)
        self.tray_icon.exit_requested.connect(self._on_force_exit)
        self.tray_icon.show()

        self.storage_monitor = StorageMonitorService(parent=self)
        self.storage_monitor.low_space_detected.connect(self.tray_icon.show_low_space_alert)
        if enable_monitor:
            self.storage_monitor.start()

    def _show_and_activate(self) -> None:
        """Restore window and bring to front."""
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.raise_()
        self.activateWindow()

    def _on_tray_quick_clean(self) -> None:
        """Trigger scan and navigate to scan page from tray."""
        self._show_and_activate()
        self._on_dashboard_start_scan()

    def _shutdown_workers(self) -> None:
        """Safely stop and join all background threads before window destruction."""
        if hasattr(self, "storage_monitor") and self.storage_monitor is not None:
            self.storage_monitor.stop()
        if hasattr(self, "scan_worker") and self.scan_worker is not None and self.scan_worker.isRunning():
            self.scan_worker.cancel()
            self.scan_worker.wait(1500)
        if hasattr(self, "cleanup_worker") and self.cleanup_worker is not None and self.cleanup_worker.isRunning():
            self.cleanup_worker.cancel()
            self.cleanup_worker.wait(1500)

    def _on_force_exit(self) -> None:
        """Terminate application completely without minimizing to tray."""
        self._force_quit = True
        self._shutdown_workers()
        self.close()
        QApplication.quit()

    def _on_request_elevation(self) -> None:
        """Ask user confirmation and trigger UAC elevation prompt."""
        reply = QMessageBox.question(
            self,
            tr("confirm_elevation_title"),
            tr("confirm_elevation_msg"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply == QMessageBox.Yes:
            if request_elevation():
                self._on_force_exit()

    def closeEvent(self, event) -> None:
        """Handle window close: minimize to tray if enabled, or exit."""
        if self._force_quit:
            self._shutdown_workers()
            event.accept()
            return

        if self.config.get("minimize_to_tray", False):
            event.ignore()
            self.hide()
            self.tray_icon.show_minimized_notification()
        else:
            self._shutdown_workers()
            event.accept()

    def retranslate_ui(self, lang_code: str = "") -> None:
        """Update navigation labels, tray actions, and subpages dynamically."""
        nav_titles = [
            ("📊 " + tr("nav_dashboard"), 0),
            ("🔍 " + tr("nav_scan"), 1),
            ("📋 " + tr("nav_results"), 2),
            ("🚀 " + tr("nav_startup"), 7),
            ("👥 " + tr("nav_duplicates"), 8),
            ("📜 " + tr("nav_history"), 4),
            ("⚙️ " + tr("nav_settings"), 5),
            ("ℹ️ " + tr("nav_about"), 6),
        ]
        for idx, (btn, page_idx) in enumerate(self.nav_buttons):
            if idx < len(nav_titles):
                btn.setText(nav_titles[idx][0])

        if self.btn_elevation:
            self.btn_elevation.setText("🛡️ " + tr("btn_restart_admin"))
        if self.lbl_admin_badge:
            self.lbl_admin_badge.setText("🛡️ " + tr("admin_mode_active"))

        # Update Tray menu
        self.tray_icon.retranslate_ui()

        # Propagate to subpages
        self.page_dashboard.retranslate_ui(lang_code)
        self.page_scan.retranslate_ui()
        self.page_results.retranslate_ui()
        self.page_cleanup.retranslate_ui()
        self.page_history.retranslate_ui(lang_code)
        self.page_settings.retranslate_ui(lang_code)
        self.page_about.retranslate_ui()

    def _on_nav_button_clicked(self, page_index: int) -> None:
        """Handle sidebar navigation clicks, auto-starting scan if scan tab clicked."""
        if page_index == 1:
            if not self.scan_worker.isRunning():
                self._on_dashboard_start_scan()
            else:
                self.navigate_to(1)
        else:
            self.navigate_to(page_index)

    def navigate_to(self, page_index: int) -> None:
        """Switch view and update navigation button state."""
        logger.debug(f"User navigated to view index {page_index}")
        self.stack.setCurrentIndex(page_index)
        for btn, idx in self.nav_buttons:
            btn.setChecked(idx == page_index)

    def _on_dashboard_start_scan(self, categories: Optional[List[str]] = None) -> None:
        target_cats = categories if isinstance(categories, list) else None
        logger.info(f"Scan triggered. Target categories: {target_cats or 'ALL_ENABLED'}")
        self.scan_worker.set_target_categories(target_cats)
        self.navigate_to(1)
        self.page_scan.start_scan(target_cats)

    def _on_category_scan_requested(self, category_id: str) -> None:
        logger.info(f"Single-category scan triggered for: '{category_id}'")
        self.scan_worker.set_target_categories([category_id])
        self.navigate_to(1)
        self.page_scan.start_scan([category_id])

    def _on_scan_completed(self, summary: ScanSummary, items: list) -> None:
        logger.info(f"Scan finished successfully: {len(items)} items ({summary.bytes_reclaimable} bytes).")
        self.page_results.load_results(summary, items)
        self.navigate_to(2)

    def _on_cleanup_requested(self, selected_items: List[ScanItem]) -> None:
        tot_bytes = sum(it.size for it in selected_items)
        logger.info(f"Cleanup requested for {len(selected_items)} items ({format_bytes(tot_bytes)})")
        reply = QMessageBox.question(
            self,
            tr("confirm_cleanup_title"),
            tr("confirm_cleanup_msg", items_count=len(selected_items), size_str=format_bytes(tot_bytes)),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply == QMessageBox.Yes:
            logger.info("User confirmed cleanup execution.")
            self.navigate_to(3)
            self.page_cleanup.reset_state()

            self.cleanup_worker = CleanupWorker(
                items_to_clean=selected_items,
                safety_engine=self.safety_engine,
                db_manager=self.db,
                parent=self,
            )
            self.cleanup_worker.progress.connect(self.page_cleanup.update_progress)
            self.cleanup_worker.finished.connect(self._on_cleanup_finished)
            self.cleanup_worker.start()

    def _on_cleanup_cancel(self) -> None:
        if self.cleanup_worker and self.cleanup_worker.isRunning():
            self.cleanup_worker.cancel()

    def _on_cleanup_finished(self, summary: CleanupSummary) -> None:
        self.page_cleanup.show_completion(summary)
        self.page_dashboard.refresh_stats()
        self.page_dashboard.update_health_status(is_good=True)
        self.page_history.reload_history()

    def _on_cleanup_done(self) -> None:
        self.page_dashboard.refresh_stats()
        self.page_dashboard.update_health_status(is_good=True)
        self.navigate_to(0)
