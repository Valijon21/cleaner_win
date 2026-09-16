"""
History Page: Historical audit records of all previous cleanup sessions.
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PyQt5.QtGui import QColor
from cleanguard.database.db import DatabaseManager
from cleanguard.database.repositories import HistoryRepository
from cleanguard.localization import tr
from cleanguard.utils.formatting import format_bytes, format_timestamp, format_number


class HistoryPage(QWidget):
    """View historical cleanup sessions."""

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.history_repo = HistoryRepository(self.db)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        self.lbl_title = QLabel(tr("nav_history"))
        self.lbl_title.setStyleSheet("font-size: 26px; font-weight: 700; color: #F9FAFB;")
        layout.addWidget(self.lbl_title)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Date & Time",
            "Status",
            "Files Deleted",
            "Files Skipped",
            "Space Recovered",
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)

        layout.addWidget(self.table)
        self.reload_history()

    def reload_history(self) -> None:
        """Fetch history records from database and render rows."""
        history = self.history_repo.get_cleanup_history(limit=50)
        self.table.setRowCount(len(history))

        for row_idx, entry in enumerate(history):
            self.table.setItem(row_idx, 0, QTableWidgetItem(format_timestamp(entry["started_at"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(entry["status"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(format_number(entry["files_deleted"])))
            self.table.setItem(row_idx, 3, QTableWidgetItem(format_number(entry["files_skipped"])))

            rec_item = QTableWidgetItem(format_bytes(entry["bytes_recovered"]))
            rec_item.setForeground(QColor("#10B981"))
            self.table.setItem(row_idx, 4, rec_item)
