"""
High-Performance Qt Model/View Architecture for Scan Results.
Provides 60 FPS scrolling and instantaneous filtering across 100,000+ items.
"""

from typing import List, Optional
from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, pyqtSignal, QRectF
from PyQt5.QtGui import QColor, QFont, QPainter, QBrush, QPen
from PyQt5.QtWidgets import QStyledItemDelegate, QStyle
from cleanguard.core.contracts import ScanItem, RiskLevel
from cleanguard.localization import tr
from cleanguard.utils.formatting import format_bytes


class RiskBadgeDelegate(QStyledItemDelegate):
    """
    Renders RiskLevel in Column 4 as a modern pill-shaped badge
    with semi-transparent background tint, subtle border, and bold status text.
    """

    def paint(self, painter: QPainter, option, index: QModelIndex) -> None:
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw selection/hover background if applicable
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor("#1E3A8A"))
        elif option.state & QStyle.State_MouseOver:
            painter.fillRect(option.rect, QColor("#1E293B"))

        text = index.data(Qt.DisplayRole) or ""
        raw_text = text.upper()
        if "XAVFSIZ" in raw_text or "SAFE" in raw_text or "БЕЗОПАСН" in raw_text:
            bg_color = QColor(16, 185, 129, 38)
            border_color = QColor(16, 185, 129, 100)
            text_color = QColor("#34D399")
        elif "KO'RIB" in raw_text or "REVIEW" in raw_text or "ПРОВЕРК" in raw_text:
            bg_color = QColor(245, 158, 11, 38)
            border_color = QColor(245, 158, 11, 100)
            text_color = QColor("#FBBF24")
        else:
            bg_color = QColor(239, 68, 68, 38)
            border_color = QColor(239, 68, 68, 100)
            text_color = QColor("#F87171")

        badge_w = min(115, option.rect.width() - 14)
        badge_h = 24
        badge_x = option.rect.x() + (option.rect.width() - badge_w) // 2
        badge_y = option.rect.y() + (option.rect.height() - badge_h) // 2
        badge_rect = QRectF(badge_x, badge_y, badge_w, badge_h)

        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(badge_rect, 12, 12)

        painter.setPen(text_color)
        font = painter.font()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(badge_rect, Qt.AlignCenter, text)

        painter.restore()


class ScanResultsModel(QAbstractTableModel):
    """
    Virtual model for rendering scan results without allocating QTableWidgetItems.
    Memory footprint is O(1) relative to display widgets.
    """
    selection_changed = pyqtSignal()

    HEADERS = [
        "Select",
        "Category",
        "Item Name",
        "Size",
        "Safety Level",
        "Safety Reason & Path",
    ]

    def __init__(self, items: Optional[List[ScanItem]] = None, parent=None):
        super().__init__(parent)
        self._all_items: List[ScanItem] = items or []
        self._filtered_items: List[ScanItem] = list(self._all_items)
        self._search_query: str = ""
        self._category_filter: str = "ALL"
        self._risk_filter: str = "ALL"

    def set_items(self, items: List[ScanItem]) -> None:
        """Update items and reapply active filters."""
        self.beginResetModel()
        self._all_items = items
        self._apply_filters()
        self.endResetModel()
        self.selection_changed.emit()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._filtered_items)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.HEADERS)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            col_keys = [
                "table_col_select",
                "table_col_category",
                "table_col_name",
                "table_col_size",
                "table_col_risk",
                "table_col_reason",
            ]
            if section < len(col_keys):
                return tr(col_keys[section])
            return self.HEADERS[section]
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags

        item = self._filtered_items[index.row()]
        base_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable

        if index.column() == 0:
            if item.risk_level == RiskLevel.BLOCKED:
                return base_flags  # Cannot check blocked items
            return base_flags | Qt.ItemIsUserCheckable

        return base_flags

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._filtered_items)):
            return None

        item = self._filtered_items[index.row()]
        col = index.column()

        # Checkbox column
        if col == 0:
            if role == Qt.CheckStateRole:
                if item.risk_level == RiskLevel.BLOCKED:
                    return Qt.Unchecked
                return Qt.Checked if item.selected else Qt.Unchecked
            return None

        # Display text
        if role == Qt.DisplayRole:
            if col == 1:
                cat_key = f"category_{item.category}"
                tr_cat = tr(cat_key)
                return tr_cat if tr_cat != cat_key else item.category
            elif col == 2:
                return item.name
            elif col == 3:
                return format_bytes(item.size)
            elif col == 4:
                return tr(f"risk_{item.risk_level.value.lower()}")
            elif col == 5:
                return f"{item.reason}  |  {item.path}"

        # Alignment
        if role == Qt.TextAlignmentRole:
            if col == 0 or col == 4:
                return Qt.AlignCenter
            elif col == 3:
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        # Font typography hierarchy
        if role == Qt.FontRole:
            font = QFont()
            if col == 2:
                font.setWeight(QFont.DemiBold)
                return font
            elif col == 3:
                font.setWeight(QFont.Medium)
                return font
            elif col == 4:
                font.setWeight(QFont.Bold)
                return font

        # Foreground semantic colors (eliminates stark white, provides clean visual hierarchy)
        if role == Qt.ForegroundRole:
            if col == 1:
                return QColor("#94A3B8")  # Slate 400 - category tag
            elif col == 2:
                return QColor("#F8FAFC")  # Slate 50 - primary item name
            elif col == 3:
                return QColor("#38BDF8")  # Sky 400 - highlighted numeric size
            elif col == 4:
                if item.risk_level == RiskLevel.SAFE:
                    return QColor("#34D399")
                elif item.risk_level == RiskLevel.REVIEW:
                    return QColor("#FBBF24")
                else:
                    return QColor("#F87171")
            elif col == 5:
                return QColor("#94A3B8")  # Slate 400 - secondary reason & path

        # Tooltip for rich context
        if role == Qt.ToolTipRole:
            if col == 1:
                cat_key = f"category_{item.category}"
                return tr(cat_key) if tr(cat_key) != cat_key else item.category
            elif col == 2:
                return f"{item.name}\nSize: {format_bytes(item.size)}\nFull Path: {item.path}"
            elif col == 3:
                return f"{format_bytes(item.size)} ({item.size:,} bytes)"
            elif col == 4:
                return f"Safety: {item.risk_level.value}\nCan delete: {'Yes' if item.is_deletable else 'No'}"
            elif col == 5:
                return f"Reason: {item.reason}\nRule ID: {item.rule_id}\nPath: {item.path}"

        return None

    def setData(self, index: QModelIndex, value, role=Qt.EditRole) -> bool:
        if not index.isValid() or index.column() != 0:
            return False

        if role == Qt.CheckStateRole:
            item = self._filtered_items[index.row()]
            if item.risk_level != RiskLevel.BLOCKED:
                item.selected = (value == Qt.Checked)
                self.dataChanged.emit(index, index, [Qt.CheckStateRole])
                self.selection_changed.emit()
                return True
        return False

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        """Sort filtered items by clicked column."""
        self.beginResetModel()
        reverse = (order == Qt.DescendingOrder)

        if column == 0:
            self._filtered_items.sort(key=lambda it: it.selected, reverse=reverse)
        elif column == 1:
            self._filtered_items.sort(key=lambda it: it.category.lower(), reverse=reverse)
        elif column == 2:
            self._filtered_items.sort(key=lambda it: it.name.lower(), reverse=reverse)
        elif column == 3:
            self._filtered_items.sort(key=lambda it: it.size, reverse=reverse)
        elif column == 4:
            self._filtered_items.sort(key=lambda it: it.risk_level.value, reverse=reverse)
        elif column == 5:
            self._filtered_items.sort(key=lambda it: it.path.lower(), reverse=reverse)

        self.endResetModel()

    def filter_by_search(self, query: str) -> None:
        """Filter items matching query in filename or path."""
        self._search_query = query.strip().lower()
        self.beginResetModel()
        self._apply_filters()
        self.endResetModel()
        self.selection_changed.emit()

    def filter_by_category(self, category: str) -> None:
        """Filter by cleanup category ('ALL' or category enum value)."""
        self._category_filter = category
        self.beginResetModel()
        self._apply_filters()
        self.endResetModel()
        self.selection_changed.emit()

    def filter_by_risk(self, risk: str) -> None:
        """Filter by risk level ('ALL', 'SAFE', 'REVIEW', 'BLOCKED')."""
        self._risk_filter = risk
        self.beginResetModel()
        self._apply_filters()
        self.endResetModel()
        self.selection_changed.emit()

    def _apply_filters(self) -> None:
        filtered = self._all_items

        # Category filter
        if self._category_filter != "ALL":
            filtered = [it for it in filtered if it.category == self._category_filter]

        # Risk filter
        if self._risk_filter != "ALL":
            filtered = [it for it in filtered if it.risk_level.value == self._risk_filter]

        # Search query
        if self._search_query:
            q = self._search_query
            filtered = [it for it in filtered if q in it.name.lower() or q in it.path.lower()]

        self._filtered_items = filtered

    def select_all_visible_safe(self) -> None:
        """Select only visible SAFE items."""
        for it in self._filtered_items:
            it.selected = (it.risk_level == RiskLevel.SAFE)
        self.beginResetModel()
        self.endResetModel()
        self.selection_changed.emit()

    def select_all_visible(self) -> None:
        """Select all visible non-blocked items."""
        for it in self._filtered_items:
            if it.risk_level != RiskLevel.BLOCKED:
                it.selected = True
        self.beginResetModel()
        self.endResetModel()
        self.selection_changed.emit()

    def clear_visible_selection(self) -> None:
        """Clear selection for all visible items."""
        for it in self._filtered_items:
            it.selected = False
        self.beginResetModel()
        self.endResetModel()
        self.selection_changed.emit()

    def get_selected_items(self) -> List[ScanItem]:
        """Return all selected non-blocked items across the entire dataset."""
        return [it for it in self._all_items if it.selected and it.risk_level != RiskLevel.BLOCKED]

    def get_selected_bytes(self) -> int:
        """Return total size of selected items."""
        return sum(it.size for it in self._all_items if it.selected and it.risk_level != RiskLevel.BLOCKED)
