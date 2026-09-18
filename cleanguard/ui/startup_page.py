"""
Startup Manager Page: Inspect and control Windows autorun applications to boost boot speed.
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
    QLineEdit,
    QComboBox,
    QFrame,
    QMessageBox,
)
from PyQt5.QtCore import Qt
from cleanguard.windows.startup import StartupManager, StartupItem
from cleanguard.core.contracts import RiskLevel
from cleanguard.localization import tr
from cleanguard.utils.logging import get_logger

logger = get_logger("ui.startup")


class StartupPage(QWidget):
    """Interactive Windows Startup Manager UI."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = StartupManager()
        self.items: List[StartupItem] = []
        self._init_ui()
        self.refresh_items()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # Header Row
        header_row = QHBoxLayout()
        header_text = QVBoxLayout()
        self.lbl_title = QLabel(tr("nav_startup", "🚀 Avto-yuklanish boshqaruvi"))
        self.lbl_title.setStyleSheet("font-size: 24px; font-weight: 700; color: #F9FAFB;")

        self.lbl_subtitle = QLabel(
            tr("startup_subtitle", "Windows yuklanishini sekinlashtiruvchi keraksiz dasturlarni o'chiring")
        )
        self.lbl_subtitle.setStyleSheet("font-size: 13px; color: #9CA3AF;")
        header_text.addWidget(self.lbl_title)
        header_text.addWidget(self.lbl_subtitle)
        header_row.addLayout(header_text)
        header_row.addStretch()

        self.btn_refresh = QPushButton("🔄 " + tr("btn_refresh", "Yangilash"))
        self.btn_refresh.setObjectName("SecondaryButton")
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.refresh_items)
        header_row.addWidget(self.btn_refresh)
        layout.addLayout(header_row)

        # Stats Summary Cards
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        self.card_total = self._create_stat_card("Jami dasturlar", "0", "#3B82F6")
        self.card_enabled = self._create_stat_card("Faol yuklanuvchilar", "0", "#10B981")
        self.card_high_impact = self._create_stat_card("Yuqori ta'sirli", "0", "#EF4444")

        stats_row.addWidget(self.card_total)
        stats_row.addWidget(self.card_enabled)
        stats_row.addWidget(self.card_high_impact)
        layout.addLayout(stats_row)

        # Search & Filter Controls
        filter_row = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 " + tr("search_placeholder", "Qidirish..."))
        self.txt_search.textChanged.connect(self._apply_filters)
        filter_row.addWidget(self.txt_search)

        self.combo_filter = QComboBox()
        self.combo_filter.addItems(["Barchasi", "Faqat faollar", "Faqat o'chirilganlar", "Yuqori ta'sirlilar"])
        self.combo_filter.currentIndexChanged.connect(self._apply_filters)
        filter_row.addWidget(self.combo_filter)
        layout.addLayout(filter_row)

        # Items Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Dastur", "Noshir", "Ta'siri", "Joylashuvi", "Holati", "Amal"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(5, 120)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def _create_stat_card(self, title: str, value: str, accent_color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            f"""
            QFrame {{
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 12px;
            }}
            """
        )
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(8, 8, 8, 8)
        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("font-size: 11px; color: #9CA3AF; text-transform: uppercase;")
        lbl_v = QLabel(value)
        lbl_v.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {accent_color};")
        c_layout.addWidget(lbl_t)
        c_layout.addWidget(lbl_v)
        card.lbl_val = lbl_v
        return card

    def refresh_items(self) -> None:
        """Scan and populate startup items."""
        self.items = self.manager.get_all_startup_items()
        total = len(self.items)
        enabled = sum(1 for x in self.items if x.enabled)
        high = sum(1 for x in self.items if x.impact == "High")

        self.card_total.lbl_val.setText(str(total))
        self.card_enabled.lbl_val.setText(str(enabled))
        self.card_high_impact.lbl_val.setText(str(high))

        self._populate_table(self.items)

    def _apply_filters(self) -> None:
        query = self.txt_search.text().strip().lower()
        filter_idx = self.combo_filter.currentIndex()

        filtered: List[StartupItem] = []
        for it in self.items:
            # Text filter
            if query and query not in it.name.lower() and query not in (it.publisher or "").lower():
                continue

            # Status filter
            if filter_idx == 1 and not it.enabled:
                continue
            elif filter_idx == 2 and it.enabled:
                continue
            elif filter_idx == 3 and it.impact != "High":
                continue

            filtered.append(it)

        self._populate_table(filtered)

    def _populate_table(self, items: List[StartupItem]) -> None:
        self.table.setRowCount(len(items))

        for row, it in enumerate(items):
            # Name
            item_name = QTableWidgetItem(f"  {it.name}")
            if it.risk_level == RiskLevel.BLOCKED:
                item_name.setToolTip("Windows tizim fayli — o'chirish taqiqlanadi")
            self.table.setItem(row, item_name)

            # Publisher
            item_pub = QTableWidgetItem(it.publisher or "Noma'lum")
            item_pub.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, item_pub)

            # Impact badge
            item_impact = QTableWidgetItem(it.impact)
            item_impact.setTextAlignment(Qt.AlignCenter)
            if it.impact == "High":
                item_impact.setForeground(Qt.red)
            elif it.impact == "Medium":
                item_impact.setForeground(Qt.yellow)
            else:
                item_impact.setForeground(Qt.green)
            self.table.setItem(row, 2, item_impact)

            # Location
            item_loc = QTableWidgetItem(it.location_type)
            item_loc.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, item_loc)

            # Status
            status_text = "🟢 Faol" if it.enabled else "⚪ O'chirilgan"
            item_status = QTableWidgetItem(status_text)
            item_status.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, item_status)

            # Action button
            if it.risk_level == RiskLevel.BLOCKED:
                lbl_blocked = QLabel("🛡️ Himoyalangan")
                lbl_blocked.setAlignment(Qt.AlignCenter)
                lbl_blocked.setStyleSheet("color: #6B7280; font-size: 11px;")
                self.table.setCellWidget(row, 5, lbl_blocked)
            else:
                btn_toggle = QPushButton("O'chirish" if it.enabled else "Yoqish")
                btn_toggle.setCursor(Qt.PointingHandCursor)
                if it.enabled:
                    btn_toggle.setStyleSheet("background-color: #EF4444; color: white; border-radius: 4px; padding: 4px;")
                else:
                    btn_toggle.setStyleSheet("background-color: #10B981; color: white; border-radius: 4px; padding: 4px;")
                btn_toggle.clicked.connect(lambda _, item=it: self._on_toggle_clicked(item))
                self.table.setCellWidget(row, 5, btn_toggle)

    def _on_toggle_clicked(self, item: StartupItem) -> None:
        new_state = not item.enabled
        success, msg = self.manager.set_startup_state(item, new_state)
        if not success:
            QMessageBox.warning(self, "Xatolik", f"Holatni o'zgartirib bo'lmadi: {msg}")
        self.refresh_items()
