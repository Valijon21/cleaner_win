"""
Results Page: Categorized scan results, interactive safety review and selection.
"""

from typing import List, Optional
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from cleanguard.core.contracts import ScanSummary, ScanItem, RiskLevel
from cleanguard.localization import tr
from cleanguard.utils.formatting import format_bytes


class ResultsPage(QWidget):
    """Scan results review and cleanup staging table."""
    cleanup_requested = pyqtSignal(list)  # Emits selected ScanItem list

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_summary: Optional[ScanSummary] = None
        self.all_items: List[ScanItem] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # Header Row
        header_row = QHBoxLayout()
        header_text = QVBoxLayout()
        self.lbl_title = QLabel(tr("nav_results"))
        self.lbl_title.setStyleSheet("font-size: 26px; font-weight: 700; color: #F9FAFB;")

        self.lbl_summary = QLabel("Scan completed. Review items before proceeding.")
        self.lbl_summary.setStyleSheet("font-size: 13px; color: #9CA3AF;")

        header_text.addWidget(self.lbl_title)
        header_text.addWidget(self.lbl_summary)
        header_row.addLayout(header_text)

        header_row.addStretch()

        # Selection Helpers & Clean Button
        self.btn_select_safe = QPushButton(tr("btn_select_all_safe"))
        self.btn_select_safe.setObjectName("SecondaryButton")
        self.btn_select_safe.clicked.connect(self._select_safe_only)
        header_row.addWidget(self.btn_select_safe)

        self.btn_clear = QPushButton(tr("btn_clear_selection"))
        self.btn_clear.setObjectName("SecondaryButton")
        self.btn_clear.clicked.connect(self._clear_selection)
        header_row.addWidget(self.btn_clear)

        self.btn_clean = QPushButton(f"  {tr('btn_clean_safely')}  ")
        self.btn_clean.setObjectName("PrimaryButton")
        self.btn_clean.setCursor(Qt.PointingHandCursor)
        self.btn_clean.clicked.connect(self._on_clean_clicked)
        header_row.addWidget(self.btn_clean)

        layout.addLayout(header_row)

        # Results Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Select",
            "Category",
            "Item Name",
            "Size",
            "Safety Level",
            "Safety Reason & Path",
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemChanged.connect(self._on_table_item_changed)

        layout.addWidget(self.table)

    def load_results(self, summary: ScanSummary, items: List[ScanItem]) -> None:
        """Populate the table with discovered scan candidates using lightweight items."""
        self.current_summary = summary
        self.all_items = items

        total_size_str = format_bytes(summary.bytes_reclaimable)
        self.lbl_summary.setText(
            f"Found {summary.items_found} items ({total_size_str}) • "
            f"{summary.safe_items} Safe, {summary.review_items} Review, {summary.blocked_items} Blocked"
        )

        self.table.blockSignals(True)
        self.table.setRowCount(len(items))

        for row_idx, item in enumerate(items):
            # 0. Checkbox using native QTableWidgetItem
            chk_item = QTableWidgetItem()
            if item.risk_level == RiskLevel.BLOCKED:
                chk_item.setFlags(Qt.ItemIsEnabled)
                chk_item.setCheckState(Qt.Unchecked)
            else:
                chk_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
                chk_item.setCheckState(Qt.Checked if item.selected else Qt.Unchecked)
            self.table.setItem(row_idx, 0, chk_item)

            # 1. Category
            cat_key = f"category_{item.category}"
            cat_label = tr(cat_key) if cat_key in tr(cat_key) else item.category
            self.table.setItem(row_idx, 1, QTableWidgetItem(cat_label))

            # 2. Item Name
            self.table.setItem(row_idx, 2, QTableWidgetItem(item.name))

            # 3. Size
            size_item = QTableWidgetItem(format_bytes(item.size))
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_idx, 3, size_item)

            # 4. Safety Level (Colored badge text)
            risk_text = tr(f"risk_{item.risk_level.value.lower()}")
            risk_item = QTableWidgetItem(f" {risk_text} ")
            risk_item.setTextAlignment(Qt.AlignCenter)
            if item.risk_level == RiskLevel.SAFE:
                risk_item.setForeground(QColor("#34D399"))
            elif item.risk_level == RiskLevel.REVIEW:
                risk_item.setForeground(QColor("#FBBF24"))
            else:
                risk_item.setForeground(QColor("#F87171"))
            self.table.setItem(row_idx, 4, risk_item)

            # 5. Reason & Path
            reason_text = f"{item.reason} — ({item.path})"
            self.table.setItem(row_idx, 5, QTableWidgetItem(reason_text))

        self.table.blockSignals(False)
        self._update_clean_button_text()

    def _on_table_item_changed(self, table_item: QTableWidgetItem) -> None:
        if table_item.column() == 0:
            row = table_item.row()
            if 0 <= row < len(self.all_items):
                item = self.all_items[row]
                if item.risk_level != RiskLevel.BLOCKED:
                    item.selected = (table_item.checkState() == Qt.Checked)
                    self._update_clean_button_text()

    def _select_safe_only(self) -> None:
        for item in self.all_items:
            if item.risk_level == RiskLevel.SAFE:
                item.selected = True
            else:
                item.selected = False
        self.load_results(self.current_summary, self.all_items)

    def _clear_selection(self) -> None:
        for item in self.all_items:
            item.selected = False
        self.load_results(self.current_summary, self.all_items)

    def _update_clean_button_text(self) -> None:
        selected_count = sum(1 for it in self.all_items if it.selected)
        selected_bytes = sum(it.size for it in self.all_items if it.selected)
        self.btn_clean.setText(f"  {tr('btn_clean_safely')} ({format_bytes(selected_bytes)})  ")
        self.btn_clean.setEnabled(selected_count > 0)

    def _on_clean_clicked(self) -> None:
        selected = [it for it in self.all_items if it.selected and it.risk_level != RiskLevel.BLOCKED]
        if selected:
            self.cleanup_requested.emit(selected)
