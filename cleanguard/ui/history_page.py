"""
History Page: Historical audit records of all previous cleanup sessions.
Features interactive session inspection (cleaned files list) and CSV/JSON export.
"""

from typing import Optional
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QDialog,
    QFileDialog,
    QMessageBox,
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
from cleanguard.database.db import DatabaseManager
from cleanguard.database.repositories import HistoryRepository
from cleanguard.services.export_service import export_history_to_csv, export_history_to_json
from cleanguard.localization import tr, get_localization
from cleanguard.utils.formatting import format_bytes, format_timestamp, format_number


class SessionDetailDialog(QDialog):
    """Modal dialog displaying file-level audit details for a selected session."""

    def __init__(self, session_info: dict, items: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("history_details_title"))
        self.resize(800, 480)
        self.setStyleSheet("""
            QDialog {
                background-color: #111827;
                color: #F9FAFB;
            }
            QLabel {
                color: #F9FAFB;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Info
        date_str = format_timestamp(session_info.get("started_at", 0.0))
        rec_str = format_bytes(session_info.get("bytes_recovered", 0))
        del_count = format_number(session_info.get("files_deleted", 0))
        skip_count = format_number(session_info.get("files_skipped", 0))

        lbl_title = QLabel(f"<b>{tr('history_details_title')}</b> — {date_str}")
        lbl_title.setStyleSheet("font-size: 16px; color: #10B981;")
        layout.addWidget(lbl_title)

        lbl_sub = QLabel(
            tr(
                "history_sub_details",
                recovered=rec_str,
                deleted=del_count,
                skipped=skip_count,
            )
        )
        lbl_sub.setStyleSheet("font-size: 13px; color: #9CA3AF;")
        layout.addWidget(lbl_sub)

        # Items Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            tr("history_detail_col_path"),
            tr("history_detail_col_category"),
            tr("history_detail_col_size"),
            tr("history_detail_col_status"),
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        self.table.setRowCount(len(items))
        for row, it in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(str(it.get("path", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(it.get("category", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(format_bytes(it.get("size", 0))))

            st = str(it.get("status", ""))
            st_item = QTableWidgetItem(st)
            if st == "SUCCESS":
                st_item.setForeground(QColor("#10B981"))
            elif st == "SKIPPED":
                st_item.setForeground(QColor("#F59E0B"))
            else:
                st_item.setForeground(QColor("#EF4444"))
            self.table.setItem(row, 3, st_item)

        layout.addWidget(self.table)

        # Close Button
        btn_close = QPushButton(f"  {tr('history_btn_close')}  ")
        btn_close.setObjectName("SecondaryButton")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)


class HistoryPage(QWidget):
    """View historical cleanup sessions with audit inspection and report exports."""

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.history_repo = HistoryRepository(self.db)
        self._history_cache = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # Header Row
        header_row = QHBoxLayout()
        self.lbl_title = QLabel(tr("nav_history"))
        self.lbl_title.setStyleSheet("font-size: 26px; font-weight: 700; color: #F9FAFB;")
        header_row.addWidget(self.lbl_title)

        header_row.addStretch()

        # Action Buttons: Inspect, Export CSV, Export JSON
        self.btn_inspect = QPushButton(f"  👁️ {tr('history_btn_inspect')}  ")
        self.btn_inspect.setObjectName("SecondaryButton")
        self.btn_inspect.setCursor(Qt.PointingHandCursor)
        self.btn_inspect.clicked.connect(self._inspect_selected)
        header_row.addWidget(self.btn_inspect)

        self.btn_csv = QPushButton(f"  📥 {tr('history_btn_export_csv')}  ")
        self.btn_csv.setObjectName("SecondaryButton")
        self.btn_csv.setCursor(Qt.PointingHandCursor)
        self.btn_csv.clicked.connect(self._export_csv)
        header_row.addWidget(self.btn_csv)

        self.btn_json = QPushButton(f"  📥 {tr('history_btn_export_json')}  ")
        self.btn_json.setObjectName("SecondaryButton")
        self.btn_json.setCursor(Qt.PointingHandCursor)
        self.btn_json.clicked.connect(self._export_json)
        header_row.addWidget(self.btn_json)

        layout.addLayout(header_row)

        # History Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self._update_table_headers()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemDoubleClicked.connect(lambda _: self._inspect_selected())

        layout.addWidget(self.table)
        self.reload_history()

    def _update_table_headers(self) -> None:
        self.table.setHorizontalHeaderLabels([
            tr("history_col_date"),
            tr("history_col_status"),
            tr("history_col_deleted"),
            tr("history_col_skipped"),
            tr("history_col_recovered"),
        ])

    def retranslate_ui(self, lang_code: str = "") -> None:
        """Dynamically update labels on language change."""
        self.lbl_title.setText(tr("nav_history"))
        self.btn_inspect.setText(f"  👁️ {tr('history_btn_inspect')}  ")
        self.btn_csv.setText(f"  📥 {tr('history_btn_export_csv')}  ")
        self.btn_json.setText(f"  📥 {tr('history_btn_export_json')}  ")
        self._update_table_headers()
        self.reload_history()

    def reload_history(self) -> None:
        """Fetch history records from database and render rows."""
        self._history_cache = self.history_repo.get_cleanup_history(limit=50)
        self.table.setRowCount(len(self._history_cache))

        for row_idx, entry in enumerate(self._history_cache):
            self.table.setItem(row_idx, 0, QTableWidgetItem(format_timestamp(entry["started_at"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(entry["status"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(format_number(entry["files_deleted"])))
            self.table.setItem(row_idx, 3, QTableWidgetItem(format_number(entry["files_skipped"])))

            rec_item = QTableWidgetItem(format_bytes(entry["bytes_recovered"]))
            rec_item.setForeground(QColor("#10B981"))
            self.table.setItem(row_idx, 4, rec_item)

    def _inspect_selected(self) -> None:
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            if self._history_cache:
                row_idx = 0
            else:
                return
        else:
            row_idx = selected_rows[0].row()

        if 0 <= row_idx < len(self._history_cache):
            session_info = self._history_cache[row_idx]
            session_id = session_info["id"]
            items = self.history_repo.get_cleanup_items(session_id)
            dialog = SessionDetailDialog(session_info, items, parent=self)
            dialog.exec_()

    def _export_csv(self) -> None:
        if not self._history_cache:
            QMessageBox.information(self, tr("msg_info_title"), tr("history_details_no_items"))
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("history_btn_export_csv"),
            "cleanguard_history.csv",
            "CSV Files (*.csv)",
        )
        if path:
            ok = export_history_to_csv(path, self._history_cache)
            if ok:
                QMessageBox.information(self, tr("msg_success_title"), tr("history_export_success", path=path))
            else:
                QMessageBox.warning(self, tr("msg_error_title"), tr("msg_export_failed"))

    def _export_json(self) -> None:
        if not self._history_cache:
            QMessageBox.information(self, tr("msg_info_title"), tr("history_details_no_items"))
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("history_btn_export_json"),
            "cleanguard_history.json",
            "JSON Files (*.json)",
        )
        if path:
            ok = export_history_to_json(
                path,
                self._history_cache,
                items_provider=self.history_repo.get_cleanup_items,
            )
            if ok:
                QMessageBox.information(self, tr("msg_success_title"), tr("history_export_success", path=path))
            else:
                QMessageBox.warning(self, tr("msg_error_title"), tr("msg_export_failed"))
