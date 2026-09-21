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
    QScrollArea,
    QSystemTrayIcon,
)
from PyQt5.QtCore import Qt
from cleanguard.app.version import APP_NAME, APP_VERSION
from cleanguard.ui.theme import DARK_STYLESHEET, get_theme_stylesheet
from cleanguard.ui.dashboard_page import DashboardPage
from cleanguard.ui.scan_page import ScanPage
from cleanguard.ui.results_page import ResultsPage
from cleanguard.ui.cleanup_page import CleanupPage
from cleanguard.ui.history_page import HistoryPage
from cleanguard.ui.settings_page import SettingsPage
from cleanguard.ui.about_page import AboutPage
from cleanguard.ui.startup_page import StartupPage
from cleanguard.ui.duplicates_page import DuplicatesPage
from cleanguard.ui.turbo_page import TurboPage
from cleanguard.ui.uninstaller_page import UninstallerPage
from cleanguard.ui.tweaks_page import TweaksPage
from cleanguard.ui.network_page import NetworkPage
from cleanguard.ui.registry_page import RegistryPage
from cleanguard.ui.hardware_page import HardwarePage
from cleanguard.ui.large_files_page import LargeFilesPage
from cleanguard.ui.tray import CleanGuardTrayIcon, get_app_icon
from cleanguard.services.scan_service import ScanWorker
from cleanguard.services.cleanup_service import CleanupWorker
from cleanguard.services.monitor_service import StorageMonitorService
from cleanguard.core.contracts import ScanSummary, ScanItem, CleanupSummary
from cleanguard.core.safety import SafetyEngine
from cleanguard.core.config import ConfigManager
from cleanguard.database.db import DatabaseManager
from cleanguard.windows.privileges import is_user_admin, request_elevation
from cleanguard.windows.restore_point import create_restore_point
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
        self.resize(1180, 760)
        self.setMinimumSize(960, 620)
        current_theme = self.config.get("theme", "dark")
        self.setStyleSheet(get_theme_stylesheet(current_theme))
        self.setWindowIcon(get_app_icon())

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
        sidebar.setFixedWidth(250)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(6, 16, 6, 12)
        side_layout.setSpacing(6)

        # Brand / Logo Header
        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(8, 0, 8, 8)
        brand_row.setSpacing(10)
        
        lbl_logo = QLabel()
        app_icon = get_app_icon()
        pixmap = app_icon.pixmap(28, 28)
        if not pixmap.isNull():
            lbl_logo.setPixmap(pixmap)
            lbl_logo.setFixedSize(28, 28)
            lbl_logo.setScaledContents(True)
        else:
            lbl_logo.setText("🛡️")
            lbl_logo.setStyleSheet("font-size: 24px;")

        brand_col = QVBoxLayout()
        brand_col.setSpacing(1)
        lbl_app = QLabel(APP_NAME)
        lbl_app.setStyleSheet("font-size: 18px; font-weight: 800; color: #10B981; letter-spacing: 0.5px;")
        lbl_badge = QLabel("PROFESSIONAL SUITE")
        lbl_badge.setStyleSheet("font-size: 8px; font-weight: 800; color: #34D399; letter-spacing: 1.2px;")
        brand_col.addWidget(lbl_app)
        brand_col.addWidget(lbl_badge)

        brand_row.addWidget(lbl_logo)
        brand_row.addLayout(brand_col)
        brand_row.addStretch()
        side_layout.addLayout(brand_row)

        # Scrollable Navigation Container
        nav_scroll = QScrollArea()
        nav_scroll.setObjectName("NavScrollArea")
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        nav_container = QWidget()
        nav_container_layout = QVBoxLayout(nav_container)
        nav_container_layout.setContentsMargins(2, 4, 2, 4)
        nav_container_layout.setSpacing(2)

        # Navigation Groups & Buttons
        self.nav_buttons = []
        self.nav_section_labels = []

        nav_groups = [
            ("nav_sec_core", "BOSHQARUV", [
                ("📊 " + tr("nav_dashboard"), 0),
                ("🔍 " + tr("nav_scan"), 1),
                ("📋 " + tr("nav_results"), 2),
            ]),
            ("nav_sec_boost", "TEZLIK & OPTIMIZATSIYA", [
                ("⚡ " + tr("nav_turbo"), 9),
                ("🚀 " + tr("nav_startup"), 7),
                ("🌐 " + tr("nav_network"), 12),
                ("🛠️ " + tr("nav_tweaks"), 11),
            ]),
            ("nav_sec_tools", "TOZALASH & ASBOBLAR", [
                ("📦 " + tr("nav_uninstaller"), 10),
                ("🧩 " + tr("nav_registry"), 13),
                ("👥 " + tr("nav_duplicates"), 8),
                ("🐘 " + tr("nav_large_files", "Katta fayllar"), 15),
                ("📈 " + tr("nav_hardware"), 14),
            ]),
            ("nav_sec_system", "TIZIM & SOZLAMALAR", [
                ("📜 " + tr("nav_history"), 4),
                ("⚙️ " + tr("nav_settings"), 5),
                ("ℹ️ " + tr("nav_about"), 6),
            ]),
        ]

        for sec_key, sec_default, items in nav_groups:
            lbl_sec = QLabel(tr(sec_key, sec_default))
            lbl_sec.setStyleSheet("""
                color: #6B7280;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.8px;
                padding-left: 10px;
                margin-top: 8px;
                margin-bottom: 2px;
            """)
            nav_container_layout.addWidget(lbl_sec)
            self.nav_section_labels.append((lbl_sec, sec_key, sec_default))

            for text, page_idx in items:
                btn = QPushButton(text)
                btn.setObjectName("NavButton")
                btn.setCheckable(True)
                btn.setCursor(Qt.PointingHandCursor)
                btn.clicked.connect(lambda checked, idx=page_idx: self._on_nav_button_clicked(idx))
                nav_container_layout.addWidget(btn)
                self.nav_buttons.append((btn, page_idx))

        nav_container_layout.addStretch()
        nav_scroll.setWidget(nav_container)
        side_layout.addWidget(nav_scroll, stretch=1)

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
        self.page_settings.theme_changed.connect(self.apply_theme)
        self.page_about = AboutPage()
        self.page_startup = StartupPage()
        self.page_duplicates = DuplicatesPage()
        self.page_turbo = TurboPage()
        self.page_uninstaller = UninstallerPage()
        self.page_tweaks = TweaksPage()
        self.page_network = NetworkPage()
        self.page_registry = RegistryPage()
        self.page_hardware = HardwarePage()
        self.page_large_files = LargeFilesPage()

        self.stack.addWidget(self.page_dashboard)   # 0
        self.stack.addWidget(self.page_scan)        # 1
        self.stack.addWidget(self.page_results)     # 2
        self.stack.addWidget(self.page_cleanup)     # 3
        self.stack.addWidget(self.page_history)     # 4
        self.stack.addWidget(self.page_settings)    # 5
        self.stack.addWidget(self.page_about)       # 6
        self.stack.addWidget(self.page_startup)     # 7
        self.stack.addWidget(self.page_duplicates)  # 8
        self.stack.addWidget(self.page_turbo)       # 9
        self.stack.addWidget(self.page_uninstaller) # 10
        self.stack.addWidget(self.page_tweaks)      # 11
        self.stack.addWidget(self.page_network)     # 12
        self.stack.addWidget(self.page_registry)    # 13
        self.stack.addWidget(self.page_hardware)    # 14
        self.stack.addWidget(self.page_large_files) # 15

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
        try:
            get_localization().unregister_listener(self.retranslate_ui)
        except Exception:
            pass
        if hasattr(self, "storage_monitor") and self.storage_monitor is not None:
            self.storage_monitor.stop()
        if hasattr(self, "scan_worker") and self.scan_worker is not None and self.scan_worker.isRunning():
            self.scan_worker.cancel()
            self.scan_worker.wait(1500)
        if hasattr(self, "cleanup_worker") and self.cleanup_worker is not None and self.cleanup_worker.isRunning():
            self.cleanup_worker.cancel()
            self.cleanup_worker.wait(1500)
        if hasattr(self, "page_hardware") and hasattr(self.page_hardware, "timer"):
            self.page_hardware.timer.stop()
        if hasattr(self, "page_turbo") and hasattr(self.page_turbo, "timer"):
            self.page_turbo.timer.stop()
        if hasattr(self, "page_tweaks") and hasattr(self.page_tweaks, "_bloatware_worker") and self.page_tweaks._bloatware_worker:
            if self.page_tweaks._bloatware_worker.isRunning():
                self.page_tweaks._bloatware_worker.terminate()
        if hasattr(self, "page_large_files") and hasattr(self.page_large_files, "_scan_worker") and self.page_large_files._scan_worker:
            if self.page_large_files._scan_worker.isRunning():
                self.page_large_files._scan_worker.cancel()
                self.page_large_files._scan_worker.wait(1000)

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

    def apply_theme(self, theme_name: str) -> None:
        """Apply a named theme to the entire application dynamically."""
        sheet = get_theme_stylesheet(theme_name)
        self.setStyleSheet(sheet)
        self.config.set("theme", theme_name)
        logger.info(f"Theme switched dynamically to: {theme_name}")

    def retranslate_ui(self, lang_code: str = "") -> None:
        """Update navigation labels, tray actions, and subpages dynamically."""
        for lbl_sec, key, default in self.nav_section_labels:
            lbl_sec.setText(tr(key, default))

        nav_titles = [
            ("📊 " + tr("nav_dashboard"), 0),
            ("🔍 " + tr("nav_scan"), 1),
            ("📋 " + tr("nav_results"), 2),
            ("⚡ " + tr("nav_turbo"), 9),
            ("🚀 " + tr("nav_startup"), 7),
            ("🌐 " + tr("nav_network"), 12),
            ("🛠️ " + tr("nav_tweaks"), 11),
            ("📦 " + tr("nav_uninstaller"), 10),
            ("🧩 " + tr("nav_registry"), 13),
            ("👥 " + tr("nav_duplicates"), 8),
            ("🐘 " + tr("nav_large_files", "Katta fayllar"), 15),
            ("📈 " + tr("nav_hardware"), 14),
            ("📜 " + tr("nav_history"), 4),
            ("⚙️ " + tr("nav_settings"), 5),
            ("ℹ️ " + tr("nav_about"), 6),
        ]
        for idx, (btn, page_idx) in enumerate(self.nav_buttons):
            if idx < len(nav_titles):
                btn.setText(nav_titles[idx][0])

        for lbl_sec, sec_key, sec_default in self.nav_section_labels:
            lbl_sec.setText(tr(sec_key, sec_default))

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
        if hasattr(self, "page_turbo") and hasattr(self.page_turbo, "retranslate_ui"):
            self.page_turbo.retranslate_ui(lang_code)
        if hasattr(self, "page_startup") and hasattr(self.page_startup, "retranslate_ui"):
            self.page_startup.retranslate_ui(lang_code)
        if hasattr(self, "page_duplicates") and hasattr(self.page_duplicates, "retranslate_ui"):
            self.page_duplicates.retranslate_ui(lang_code)
        if hasattr(self, "page_uninstaller") and hasattr(self.page_uninstaller, "retranslate_ui"):
            self.page_uninstaller.retranslate_ui(lang_code)
        if hasattr(self, "page_tweaks") and hasattr(self.page_tweaks, "retranslate_ui"):
            self.page_tweaks.retranslate_ui(lang_code)
        if hasattr(self, "page_network") and hasattr(self.page_network, "retranslate_ui"):
            self.page_network.retranslate_ui(lang_code)
        if hasattr(self, "page_registry") and hasattr(self.page_registry, "retranslate_ui"):
            self.page_registry.retranslate_ui(lang_code)
        if hasattr(self, "page_hardware") and hasattr(self.page_hardware, "retranslate_ui"):
            self.page_hardware.retranslate_ui(lang_code)
        if hasattr(self, "page_large_files") and hasattr(self.page_large_files, "retranslate_ui"):
            self.page_large_files.retranslate_ui(lang_code)

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

        # Trigger on-demand lazy loading if target page supports it
        target_page = self.stack.widget(page_index)
        if target_page and hasattr(target_page, "lazy_load"):
            target_page.lazy_load()

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
            if self.config.get("create_restore_point", True):
                try:
                    create_restore_point("CleanGuard Pre-Clean Snapshot")
                except Exception as ex:
                    logger.debug("Restore point creation skipped/failed: %s", ex)

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

    def closeEvent(self, event) -> None:
        if not getattr(self, "_force_quit", False) and self.config.get("minimize_to_tray", False) and hasattr(self, "tray_icon") and self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                tr("tray_minimized_title"),
                tr("tray_minimized_msg"),
                QSystemTrayIcon.Information,
                2500,
            )
            event.ignore()
            return

        self._shutdown_workers()
        super().closeEvent(event)

