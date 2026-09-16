"""
Main Window: Application shell containing sidebar navigation and view stack.
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
from cleanguard.services.scan_service import ScanWorker
from cleanguard.services.cleanup_service import CleanupWorker
from cleanguard.core.contracts import ScanSummary, ScanItem, CleanupSummary
from cleanguard.core.safety import SafetyEngine
from cleanguard.database.db import DatabaseManager
from cleanguard.localization import tr, get_localization
from cleanguard.utils.formatting import format_bytes


class MainWindow(QMainWindow):
    """Primary application window and navigation controller."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        super().__init__()
        self.db = db_manager or DatabaseManager()
        self.safety_engine = SafetyEngine()
        self.scan_worker = ScanWorker(db_manager=self.db, parent=self)

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1080, 720)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(DARK_STYLESHEET)

        self._init_shell()

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
            ("📜 " + tr("nav_history"), 4),
            ("⚙️ " + tr("nav_settings"), 5),
            ("ℹ️ " + tr("nav_about"), 6),
        ]

        for text, page_idx in nav_items:
            btn = QPushButton(text)
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=page_idx: self.navigate_to(idx))
            side_layout.addWidget(btn)
            self.nav_buttons.append((btn, page_idx))

        side_layout.addStretch()

        # Safety Guard Badge in Sidebar Footer
        lbl_shield = QLabel("● Safety Engine Active")
        lbl_shield.setStyleSheet("color: #10B981; font-size: 11px; font-weight: 600; padding: 6px;")
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

        self.stack.addWidget(self.page_dashboard)   # 0
        self.stack.addWidget(self.page_scan)        # 1
        self.stack.addWidget(self.page_results)     # 2
        self.stack.addWidget(self.page_cleanup)     # 3
        self.stack.addWidget(self.page_history)     # 4
        self.stack.addWidget(self.page_settings)    # 5
        self.stack.addWidget(self.page_about)       # 6

        shell_layout.addWidget(self.stack)

        # Connect inter-page signals
        self.page_dashboard.start_scan_requested.connect(self._on_dashboard_start_scan)
        self.page_scan.scan_completed.connect(self._on_scan_completed)
        self.page_scan.scan_cancelled.connect(lambda: self.navigate_to(0))
        self.page_results.cleanup_requested.connect(self._on_cleanup_requested)
        self.page_cleanup.done_clicked.connect(self._on_cleanup_done)

        # Register live retranslation on language switch
        get_localization().register_listener(self.retranslate_ui)

        self.navigate_to(0)

    def retranslate_ui(self, lang_code: str = "") -> None:
        """Update navigation labels dynamically when language changes."""
        nav_titles = [
            "📊 " + tr("nav_dashboard"),
            "🔍 " + tr("nav_scan"),
            "📋 " + tr("nav_results"),
            "📜 " + tr("nav_history"),
            "⚙️ " + tr("nav_settings"),
            "ℹ️ " + tr("nav_about"),
        ]
        for idx, (btn, page_idx) in enumerate(self.nav_buttons):
            if idx < len(nav_titles):
                btn.setText(nav_titles[idx])

    def navigate_to(self, page_index: int) -> None:
        """Switch view and update navigation button state."""
        self.stack.setCurrentIndex(page_index)
        for btn, idx in self.nav_buttons:
            btn.setChecked(idx == page_index)

    def _on_dashboard_start_scan(self) -> None:
        self.navigate_to(1)
        self.page_scan.start_scan()

    def _on_scan_completed(self, summary: ScanSummary, items: list) -> None:
        self.page_results.load_results(summary, items)
        self.navigate_to(2)

    def _on_cleanup_requested(self, selected_items: List[ScanItem]) -> None:
        tot_bytes = sum(it.size for it in selected_items)
        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            tr("confirm_cleanup_title"),
            tr("confirm_cleanup_msg", items_count=len(selected_items), size_str=format_bytes(tot_bytes)),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply == QMessageBox.Yes:
            self.navigate_to(3)
            # Create worker
            cleanup_worker = CleanupWorker(
                items_to_clean=selected_items,
                safety_engine=self.safety_engine,
                db_manager=self.db,
                parent=self,
            )
            cleanup_worker.progress.connect(self.page_cleanup.update_progress)
            cleanup_worker.finished.connect(self._on_cleanup_finished)
            cleanup_worker.start()

    def _on_cleanup_finished(self, summary: CleanupSummary) -> None:
        self.page_cleanup.show_completion(summary)
        self.page_dashboard.refresh_stats()
        self.page_history.reload_history()

    def _on_cleanup_done(self) -> None:
        self.navigate_to(0)
