"""
Results Page: Categorized scan results, ASC PC Health Assessment, 1-Click FIX, and filtering.
Built on Qt Model/View architecture for 60 FPS performance with 50,000+ items.
"""

from typing import List, Optional
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableView,
    QHeaderView,
    QLineEdit,
    QComboBox,
    QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal
from cleanguard.core.contracts import ScanSummary, ScanItem
from cleanguard.ui.models import ScanResultsModel, RiskBadgeDelegate
from cleanguard.localization import tr
from cleanguard.utils.formatting import format_bytes


class ResultsPage(QWidget):
    """Scan results review, ASC Health Score assessment, and cleanup staging view."""
    cleanup_requested = pyqtSignal(list)  # Emits selected ScanItem list

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_summary: Optional[ScanSummary] = None
        self.model = ScanResultsModel(parent=self)
        self.model.selection_changed.connect(self._update_clean_button_text)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(14)

        # Header Row: Title & High-Impact 1-Click FIX NOW Button
        header_row = QHBoxLayout()
        header_text = QVBoxLayout()
        self.lbl_title = QLabel(tr("nav_results"))
        self.lbl_title.setStyleSheet("font-size: 26px; font-weight: 700; color: #F9FAFB;")

        self.lbl_summary = QLabel(tr("results_empty_msg"))
        self.lbl_summary.setStyleSheet("font-size: 13px; color: #9CA3AF;")

        header_text.addWidget(self.lbl_title)
        header_text.addWidget(self.lbl_summary)
        header_row.addLayout(header_text)

        header_row.addStretch()

        # Primary High-Impact 1-Click FIX Button (IObit ASC Style)
        self.btn_clean = QPushButton(f"  {tr('btn_fix_now')}  ")
        self.btn_clean.setObjectName("FixNowButton")
        self.btn_clean.setCursor(Qt.PointingHandCursor)
        self.btn_clean.setEnabled(False)
        self.btn_clean.clicked.connect(self._on_clean_clicked)
        header_row.addWidget(self.btn_clean)

        layout.addLayout(header_row)

        # Dynamic PC Health Assessment Banner
        self.health_banner = QFrame()
        self.health_banner.setObjectName("HealthBannerFair")
        self.health_banner.setVisible(False)  # Revealed when results are loaded
        banner_layout = QHBoxLayout(self.health_banner)
        banner_layout.setContentsMargins(18, 12, 18, 12)
        banner_layout.setSpacing(14)

        self.lbl_health_icon = QLabel("🛡️")
        self.lbl_health_icon.setStyleSheet("font-size: 26px; background: transparent;")
        banner_layout.addWidget(self.lbl_health_icon)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self.lbl_health_title = QLabel("")
        self.lbl_health_title.setStyleSheet("font-size: 14px; font-weight: 700; background: transparent;")
        self.lbl_health_desc = QLabel("")
        self.lbl_health_desc.setStyleSheet("font-size: 12px; color: #D1D5DB; background: transparent;")
        text_col.addWidget(self.lbl_health_title)
        text_col.addWidget(self.lbl_health_desc)
        banner_layout.addLayout(text_col, stretch=1)

        layout.addWidget(self.health_banner)

        # Filter & Search Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        # Search Bar
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍  Search files or paths...")
        self.txt_search.setStyleSheet("""
            QLineEdit {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 6px 12px;
                color: #F9FAFB;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #3B82F6;
            }
        """)
        self.txt_search.textChanged.connect(self.model.filter_by_search)
        toolbar.addWidget(self.txt_search, stretch=2)

        # Category Filter Dropdown
        self.combo_category = QComboBox()
        self.combo_category.setStyleSheet("""
            QComboBox {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 6px 12px;
                color: #F9FAFB;
            }
        """)
        self.combo_category.addItem("All Categories", "ALL")
        self.combo_category.addItem(tr("category_temp_files"), "temp_files")
        self.combo_category.addItem(tr("category_app_cache"), "app_cache")
        self.combo_category.addItem(tr("category_browser_cache"), "browser_cache")
        self.combo_category.addItem(tr("category_system_logs"), "system_logs")
        self.combo_category.addItem(tr("category_crash_dumps"), "crash_dumps")
        self.combo_category.addItem(tr("category_thumbnail_cache"), "thumbnail_cache")
        self.combo_category.addItem(tr("category_recycle_bin"), "recycle_bin")
        self.combo_category.currentIndexChanged.connect(self._on_category_filter_changed)
        toolbar.addWidget(self.combo_category)

        # Risk Filter Dropdown
        self.combo_risk = QComboBox()
        self.combo_risk.setStyleSheet("""
            QComboBox {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 6px 12px;
                color: #F9FAFB;
            }
        """)
        self.combo_risk.addItem("All Risk Levels", "ALL")
        self.combo_risk.addItem(tr("risk_safe"), "SAFE")
        self.combo_risk.addItem(tr("risk_review"), "REVIEW")
        self.combo_risk.addItem(tr("risk_blocked"), "BLOCKED")
        self.combo_risk.currentIndexChanged.connect(self._on_risk_filter_changed)
        toolbar.addWidget(self.combo_risk)

        # Action Buttons
        self.btn_select_safe = QPushButton(tr("btn_select_all_safe"))
        self.btn_select_safe.setObjectName("SecondaryButton")
        self.btn_select_safe.clicked.connect(self.model.select_all_visible_safe)
        toolbar.addWidget(self.btn_select_safe)

        self.btn_clear = QPushButton(tr("btn_clear_selection"))
        self.btn_clear.setObjectName("SecondaryButton")
        self.btn_clear.clicked.connect(self.model.clear_visible_selection)
        toolbar.addWidget(self.btn_clear)

        layout.addLayout(toolbar)

        # Table View with Virtualized Model
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setItemDelegateForColumn(4, RiskBadgeDelegate(self.table))
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(38)

        # Column sizing - fast fixed & interactive sections avoiding O(N) layout scans
        header = self.table.horizontalHeader()
        header.setHighlightSections(False)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.resizeSection(0, 48)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.resizeSection(1, 145)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.resizeSection(2, 230)
        header.setSectionResizeMode(3, QHeaderView.Interactive)
        header.resizeSection(3, 95)
        header.setSectionResizeMode(4, QHeaderView.Interactive)
        header.resizeSection(4, 135)
        header.setSectionResizeMode(5, QHeaderView.Stretch)

        layout.addWidget(self.table)

    def load_results(self, summary: ScanSummary, items: List[ScanItem]) -> None:
        """Feed items to virtual model instantaneously and evaluate PC Health score."""
        self.current_summary = summary
        total_size_str = format_bytes(summary.bytes_reclaimable)
        self.lbl_summary.setText(
            tr(
                "results_summary_text",
                total_items=summary.items_found,
                total_size=total_size_str,
                safe_count=summary.safe_items,
                review_count=summary.review_items,
                blocked_count=summary.blocked_items,
            )
        )
        self.model.set_items(items)

        # ASC Health Score Assessment
        self._evaluate_health_score(summary.bytes_reclaimable)

    def _evaluate_health_score(self, total_bytes: int) -> None:
        """Categorize system status into Good, Fair, or Critical based on detected junk."""
        self.health_banner.setVisible(True)

        # Thresholds: < 500 MB (Good), 500 MB - 3 GB (Fair), > 3 GB (Critical)
        if total_bytes < 500 * 1024 * 1024:
            self.health_banner.setObjectName("HealthBannerGood")
            self.lbl_health_icon.setText("🟢")
            self.lbl_health_title.setText(tr("health_good_title"))
            self.lbl_health_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #10B981; background: transparent;")
            self.lbl_health_desc.setText(tr("health_good_desc"))
        elif total_bytes <= 3 * 1024 * 1024 * 1024:
            self.health_banner.setObjectName("HealthBannerFair")
            self.lbl_health_icon.setText("🟡")
            self.lbl_health_title.setText(tr("health_fair_title"))
            self.lbl_health_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #FBBF24; background: transparent;")
            self.lbl_health_desc.setText(tr("health_fair_desc"))
        else:
            self.health_banner.setObjectName("HealthBannerCritical")
            self.lbl_health_icon.setText("🔴")
            self.lbl_health_title.setText(tr("health_critical_title"))
            self.lbl_health_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #EF4444; background: transparent;")
            self.lbl_health_desc.setText(tr("health_critical_desc"))

        self.health_banner.style().unpolish(self.health_banner)
        self.health_banner.style().polish(self.health_banner)

    def _on_category_filter_changed(self, index: int) -> None:
        cat = self.combo_category.itemData(index)
        self.model.filter_by_category(cat)

    def _on_risk_filter_changed(self, index: int) -> None:
        risk = self.combo_risk.itemData(index)
        self.model.filter_by_risk(risk)

    def _update_clean_button_text(self) -> None:
        selected_items = self.model.get_selected_items()
        selected_bytes = self.model.get_selected_bytes()
        count = len(selected_items)
        size_str = format_bytes(selected_bytes)
        self.btn_clean.setText(f"  {tr('btn_fix_now')} ({size_str})  ")
        self.btn_clean.setEnabled(count > 0)

    def _on_clean_clicked(self) -> None:
        selected = self.model.get_selected_items()
        if selected:
            self.cleanup_requested.emit(selected)

    def retranslate_ui(self) -> None:
        """Dynamically update labels and column headers on language switch."""
        self.lbl_title.setText(tr("nav_results"))
        self.btn_select_safe.setText(tr("btn_select_all_safe"))
        self.btn_clear.setText(tr("btn_clear_selection"))

        if self.current_summary:
            total_size_str = format_bytes(self.current_summary.bytes_reclaimable)
            self.lbl_summary.setText(
                tr(
                    "results_summary_text",
                    total_items=self.current_summary.items_found,
                    total_size=total_size_str,
                    safe_count=self.current_summary.safe_items,
                    review_count=self.current_summary.review_items,
                    blocked_count=self.current_summary.blocked_items,
                )
            )
            self._evaluate_health_score(self.current_summary.bytes_reclaimable)
        else:
            self.lbl_summary.setText(tr("results_empty_msg"))

        self._update_clean_button_text()
        self.model.headerDataChanged.emit(Qt.Horizontal, 0, self.model.columnCount() - 1)
