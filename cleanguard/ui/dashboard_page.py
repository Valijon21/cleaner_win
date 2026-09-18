"""
Dashboard Page: IObit Advanced SystemCare style Care Center.
Features PC Health Status banner, glowing circular SCAN centerpiece,
7-module Care Selector Grid with Select All toggle, metrics, and drive storage gauges.
"""

from typing import Dict, List, Optional
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QProgressBar,
    QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from cleanguard.windows.drives import enumerate_drives
from cleanguard.windows.os_info import get_windows_version
from cleanguard.ui.widgets.cards import StatCard, DriveCard, CareModuleCard
from cleanguard.ui.widgets.buttons import CircularScanButton
from cleanguard.services.smart_care_service import SmartCareWorker, SmartCareResult
from cleanguard.database.db import DatabaseManager
from cleanguard.database.repositories import HistoryRepository
from cleanguard.localization import tr
from cleanguard.utils.formatting import format_bytes, format_number


class DashboardPage(QWidget):
    """ASC-Style Care Center Dashboard screen."""
    start_scan_requested = pyqtSignal(object)  # Emits Optional[List[str]] (selected category IDs)
    start_category_scan_requested = pyqtSignal(str)  # Emits single category_id

    CATEGORIES_CONFIG = [
        ("temp_files", "🗑️", "category_temp_files", "category_desc_temp_files"),
        ("app_cache", "⚡", "category_app_cache", "category_desc_app_cache"),
        ("browser_cache", "🌐", "category_browser_cache", "category_desc_browser_cache"),
        ("system_logs", "📋", "category_system_logs", "category_desc_system_logs"),
        ("crash_dumps", "⚠️", "category_crash_dumps", "category_desc_crash_dumps"),
        ("thumbnail_cache", "🖼️", "category_thumbnail_cache", "category_desc_thumbnail_cache"),
        ("recycle_bin", "♻️", "category_recycle_bin", "category_desc_recycle_bin"),
    ]

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.history_repo = HistoryRepository(self.db)
        self.care_cards: Dict[str, CareModuleCard] = {}
        self.category_cards = self.care_cards  # Backward-compatibility alias
        self._all_selected = True
        self.smart_care_worker: Optional[SmartCareWorker] = None
        self._init_ui()

    def _init_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # Responsive Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(24)

        # 1. Header: OS Info & Tagline
        header_row = QHBoxLayout()
        header_text = QVBoxLayout()
        self.lbl_title = QLabel(tr("nav_dashboard"))
        self.lbl_title.setStyleSheet("font-size: 26px; font-weight: 700; color: #F9FAFB;")

        self.os_info = get_windows_version()
        self.lbl_subtitle = QLabel(f"{self.os_info.display_name} ({self.os_info.architecture}) • CleanGuard Safety Engine")
        self.lbl_subtitle.setStyleSheet("font-size: 13px; color: #9CA3AF;")

        header_text.addWidget(self.lbl_title)
        header_text.addWidget(self.lbl_subtitle)
        header_row.addLayout(header_text)
        header_row.addStretch()
        main_layout.addLayout(header_row)

        # 2. Top PC Health Assessment Banner
        self.health_banner = QFrame()
        self.health_banner.setObjectName("HealthBannerFair")
        banner_layout = QHBoxLayout(self.health_banner)
        banner_layout.setContentsMargins(20, 14, 20, 14)
        banner_layout.setSpacing(16)

        self.lbl_health_icon = QLabel("🛡️")
        self.lbl_health_icon.setStyleSheet("font-size: 32px; background: transparent;")
        banner_layout.addWidget(self.lbl_health_icon)

        banner_text_col = QVBoxLayout()
        banner_text_col.setSpacing(2)
        self.lbl_health_title = QLabel(tr("health_fair_title"))
        self.lbl_health_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #FBBF24; background: transparent;")
        self.lbl_health_desc = QLabel(tr("health_fair_desc"))
        self.lbl_health_desc.setStyleSheet("font-size: 12px; color: #D1D5DB; background: transparent;")

        banner_text_col.addWidget(self.lbl_health_title)
        banner_text_col.addWidget(self.lbl_health_desc)
        banner_layout.addLayout(banner_text_col, stretch=1)

        main_layout.addWidget(self.health_banner)

        # 3. Centerpiece: Pulsing Circular SCAN Button + 1-Click Smart Care
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 12, 0, 12)
        center_layout.setSpacing(14)
        center_layout.setAlignment(Qt.AlignCenter)

        self.btn_circular_scan = CircularScanButton()
        self.btn_circular_scan.clicked.connect(self._on_scan_clicked)
        center_layout.addWidget(self.btn_circular_scan, alignment=Qt.AlignCenter)

        self.btn_smart_care = QPushButton("⚡ " + tr("btn_smart_care", "1-Click Smart Care"))
        self.btn_smart_care.setCursor(Qt.PointingHandCursor)
        self.btn_smart_care.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #06B6D4);
                color: #FFFFFF;
                font-size: 13px;
                font-weight: 700;
                border-radius: 18px;
                padding: 9px 28px;
                border: 1px solid #34D399;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #0891B2);
                border: 1px solid #6EE7B7;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
            QPushButton:disabled {
                background: #374151;
                color: #9CA3AF;
                border: 1px solid #4B5563;
            }
        """)
        self.btn_smart_care.clicked.connect(self._on_smart_care_clicked)
        center_layout.addWidget(self.btn_smart_care, alignment=Qt.AlignCenter)

        # Smart Care Progress Container (hidden initially)
        self.smart_care_progress_widget = QWidget()
        self.smart_care_progress_widget.setFixedWidth(360)
        self.smart_care_progress_widget.setVisible(False)
        p_layout = QVBoxLayout(self.smart_care_progress_widget)
        p_layout.setContentsMargins(0, 4, 0, 4)
        p_layout.setSpacing(6)

        self.lbl_smart_care_status = QLabel(tr("smart_care_running", "Tizim optimallashtirilmoqda..."))
        self.lbl_smart_care_status.setStyleSheet("font-size: 11px; font-weight: 600; color: #34D399;")
        self.lbl_smart_care_status.setAlignment(Qt.AlignCenter)
        p_layout.addWidget(self.lbl_smart_care_status)

        self.smart_care_progress_bar = QProgressBar()
        self.smart_care_progress_bar.setRange(0, 100)
        self.smart_care_progress_bar.setValue(0)
        self.smart_care_progress_bar.setTextVisible(True)
        self.smart_care_progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 6px;
                height: 14px;
                text-align: center;
                color: white;
                font-size: 10px;
                font-weight: 700;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #06B6D4);
                border-radius: 5px;
            }
        """)
        p_layout.addWidget(self.smart_care_progress_bar)

        center_layout.addWidget(self.smart_care_progress_widget, alignment=Qt.AlignCenter)

        main_layout.addWidget(center_container)

        # 4. Care Selector Grid (Modullarni tanlash paneli)
        care_header_row = QHBoxLayout()
        self.lbl_care_title = QLabel(tr("care_selector_title"))
        self.lbl_care_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #06B6D4; letter-spacing: 1px;")
        care_header_row.addWidget(self.lbl_care_title)
        care_header_row.addStretch()

        self.btn_toggle_all = QPushButton(tr("deselect_all"))
        self.btn_toggle_all.setObjectName("SecondaryButton")
        self.btn_toggle_all.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_all.clicked.connect(self._on_toggle_all_clicked)
        care_header_row.addWidget(self.btn_toggle_all)
        main_layout.addLayout(care_header_row)

        # Grid of CareModuleCards
        care_grid = QGridLayout()
        care_grid.setSpacing(12)

        for i, (cat_id, icon, title_key, desc_key) in enumerate(self.CATEGORIES_CONFIG):
            card = CareModuleCard(
                category_id=cat_id,
                icon=icon,
                title=tr(title_key),
                description=tr(desc_key),
                checked=True,
            )
            self.care_cards[cat_id] = card
            row = i // 2
            col = i % 2
            care_grid.addWidget(card, row, col)

        main_layout.addLayout(care_grid)

        # 5. Cumulative Metrics Row
        stats = self.history_repo.get_cumulative_stats()
        tot_bytes = stats.get("total_bytes_recovered", 0.0)
        tot_files = stats.get("total_files_deleted", 0.0)

        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(16)

        self.card_recovered = StatCard(
            title=tr("stat_total_cleaned").upper(),
            value=format_bytes(tot_bytes),
            subtext=tr("stat_lifetime_recovered"),
        )
        self.card_files = StatCard(
            title=tr("stat_files_removed").upper(),
            value=format_number(int(tot_files)),
            subtext=tr("stat_junk_cleaned"),
        )
        self.card_safety = StatCard(
            title=tr("stat_safety_engine"),
            value=tr("stat_safety_enforced"),
            subtext=tr("stat_safety_subtext"),
        )

        metrics_row.addWidget(self.card_recovered)
        metrics_row.addWidget(self.card_files)
        metrics_row.addWidget(self.card_safety)

        main_layout.addLayout(metrics_row)

        # 6. Drive Storage Section
        self.lbl_drives_title = QLabel(tr("drives_section_header"))
        self.lbl_drives_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #9CA3AF; letter-spacing: 1px;")
        main_layout.addWidget(self.lbl_drives_title)

        self.drives_container = QVBoxLayout()
        self.drives_container.setSpacing(12)
        self.refresh_drives()
        main_layout.addLayout(self.drives_container)

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

    def get_selected_categories(self) -> List[str]:
        """Return list of category IDs currently checked in Care Grid."""
        return [cat_id for cat_id, card in self.care_cards.items() if card.is_checked()]

    def _on_scan_clicked(self) -> None:
        """Trigger scan with currently checked care categories."""
        selected = self.get_selected_categories()
        # If user deselected everything, default to scanning all
        if not selected:
            selected = [cat_id for cat_id, _, _, _ in self.CATEGORIES_CONFIG]
        self.start_scan_requested.emit(selected)

    def _on_toggle_all_clicked(self) -> None:
        """Toggle all module checkboxes between select all and deselect all."""
        self._all_selected = not self._all_selected
        for card in self.care_cards.values():
            card.set_checked(self._all_selected)
        btn_text = tr("deselect_all") if self._all_selected else tr("select_all")
        self.btn_toggle_all.setText(btn_text)

    def refresh_drives(self) -> None:
        """Reload drive information safely."""
        while self.drives_container.count():
            item = self.drives_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        try:
            drives = enumerate_drives()
            for drive in drives:
                if drive.is_ready and drive.drive_type == "Fixed Disk":
                    card = DriveCard(drive)
                    self.drives_container.addWidget(card)
        except Exception:
            pass

    def refresh_stats(self) -> None:
        """Update metrics numbers after cleanup."""
        stats = self.history_repo.get_cumulative_stats()
        self.card_recovered.set_value(format_bytes(stats.get("total_bytes_recovered", 0.0)))
        self.card_files.set_value(format_number(int(stats.get("total_files_deleted", 0.0))))
        self.refresh_drives()

    def _on_smart_care_clicked(self) -> None:
        """Trigger 1-Click Smart Care all-in-one system optimization."""
        if self.smart_care_worker and self.smart_care_worker.isRunning():
            return

        self.btn_smart_care.setEnabled(False)
        self.btn_circular_scan.setEnabled(False)
        self.smart_care_progress_widget.setVisible(True)
        self.smart_care_progress_bar.setValue(0)
        self.lbl_smart_care_status.setText(tr("smart_care_running", "Tizim optimallashtirilmoqda..."))

        self.smart_care_worker = SmartCareWorker(self.db, parent=self)
        self.smart_care_worker.stage_changed.connect(self._on_smart_care_stage)
        self.smart_care_worker.finished.connect(self._on_smart_care_finished)
        self.smart_care_worker.start()

    def _on_smart_care_stage(self, stage_text: str, percent: int = 0) -> None:
        self.lbl_smart_care_status.setText(stage_text)
        self.smart_care_progress_bar.setValue(percent)

    def _on_smart_care_finished(self, result: SmartCareResult) -> None:
        self.btn_smart_care.setEnabled(True)
        self.btn_circular_scan.setEnabled(True)
        self.smart_care_progress_widget.setVisible(False)

        self.refresh_stats()
        self.update_health_status(is_good=True)

        summary_text = tr(
            "smart_care_summary",
            junk_size=format_bytes(result.junk_cleaned_bytes),
            ram_freed=format_bytes(result.ram_freed_bytes),
            reg_count=result.registry_issues_fixed,
            update_size=format_bytes(result.update_cache_cleaned_bytes),
            total_space=format_bytes(result.total_space_reclaimed_bytes),
        )

        QMessageBox.information(
            self,
            tr("smart_care_complete_title", "Smart Care optimizatsiyasi yakunlandi!"),
            summary_text,
        )

    def update_health_status(self, is_good: bool) -> None:
        """Switch banner styling and text between Good and Fair/Needs Attention."""
        if is_good:
            self.health_banner.setObjectName("HealthBannerGood")
            self.lbl_health_title.setText(tr("health_good_title"))
            self.lbl_health_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #10B981; background: transparent;")
            self.lbl_health_desc.setText(tr("health_good_desc"))
        else:
            self.health_banner.setObjectName("HealthBannerFair")
            self.lbl_health_title.setText(tr("health_fair_title"))
            self.lbl_health_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #FBBF24; background: transparent;")
            self.lbl_health_desc.setText(tr("health_fair_desc"))
        # Force re-polish stylesheet for objectName change
        self.health_banner.style().unpolish(self.health_banner)
        self.health_banner.style().polish(self.health_banner)

    def retranslate_ui(self, lang_code: str = "") -> None:
        """Update all text dynamically when language is switched."""
        self.lbl_title.setText(tr("nav_dashboard"))
        self.lbl_subtitle.setText(f"{self.os_info.display_name} ({self.os_info.architecture}) • CleanGuard Safety Engine")

        self.lbl_health_title.setText(tr("health_fair_title"))
        self.lbl_health_desc.setText(tr("health_fair_desc"))

        self.btn_circular_scan.retranslate_ui()
        if hasattr(self, "btn_smart_care"):
            self.btn_smart_care.setText("⚡ " + tr("btn_smart_care", "1-Click Smart Care"))
        self.lbl_care_title.setText(tr("care_selector_title"))
        btn_text = tr("deselect_all") if self._all_selected else tr("select_all")
        self.btn_toggle_all.setText(btn_text)

        for cat_id, _, title_key, desc_key in self.CATEGORIES_CONFIG:
            if cat_id in self.care_cards:
                self.care_cards[cat_id].update_text(tr(title_key), tr(desc_key))

        self.card_recovered.title_label.setText(tr("stat_total_cleaned").upper())
        self.card_recovered.set_subtext(tr("stat_lifetime_recovered"))

        self.card_files.title_label.setText(tr("stat_files_removed").upper())
        self.card_files.set_subtext(tr("stat_junk_cleaned"))

        self.card_safety.title_label.setText(tr("stat_safety_engine"))
        self.card_safety.set_value(tr("stat_safety_enforced"))
        self.card_safety.set_subtext(tr("stat_safety_subtext"))

        self.lbl_drives_title.setText(tr("drives_section_header"))
