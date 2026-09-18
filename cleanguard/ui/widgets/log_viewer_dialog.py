"""
CleanGuard Diagnostic Log Viewer Dialog.
Interactive, color-coded, searchable real-time log inspector.
"""

import os
import logging
from typing import List, Dict, Any
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QTextEdit,
    QCheckBox,
    QFileDialog,
    QApplication,
    QFrame,
)
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtCore import Qt, QTimer
from cleanguard.utils.logging import (
    get_memory_logs,
    clear_memory_logs,
    open_log_folder,
    get_log_file_paths,
)
from cleanguard.localization import tr


class LogViewerDialog(QDialog):
    """Real-time diagnostic log inspector for CleanGuard."""

    LEVEL_COLORS = {
        "DEBUG": "#38BDF8",      # Light Blue
        "INFO": "#34D399",       # Emerald Green
        "WARNING": "#FBBF24",    # Amber
        "ERROR": "#F87171",      # Red
        "CRITICAL": "#F43F5E",   # Rose
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("log_viewer_title") if tr("log_viewer_title") != "log_viewer_title" else "CleanGuard - Diagnostic Logs")
        self.resize(1000, 620)
        self.setMinimumSize(800, 480)
        self._last_rendered_count = 0
        self._current_filter_level = logging.DEBUG
        self._search_query = ""

        self._init_ui()
        self._load_logs()

        # Auto-refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._on_timer_tick)
        self.refresh_timer.start(1000)

    def _init_ui(self) -> None:
        self.setStyleSheet("""
            QDialog {
                background-color: #0F172A;
                color: #F8FAFC;
            }
            QLabel {
                color: #F1F5F9;
            }
            QLineEdit, QComboBox {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 10px;
                color: #F8FAFC;
                font-size: 12px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #10B981;
            }
            QPushButton {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #E2E8F0;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #334155;
                border: 1px solid #475569;
            }
            QCheckBox {
                color: #94A3B8;
                font-size: 12px;
            }
            QTextEdit {
                background-color: #090D16;
                border: 1px solid #1E293B;
                border-radius: 8px;
                padding: 10px;
                color: #E2E8F0;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        # 1. Header Toolbar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        lbl_title = QLabel("📋 Diagnostic Logs")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #10B981;")
        top_bar.addWidget(lbl_title)

        top_bar.addSpacing(15)

        # Filter Level
        lbl_filter = QLabel("Level:")
        top_bar.addWidget(lbl_filter)
        self.combo_level = QComboBox()
        self.combo_level.addItem("All (DEBUG+)", logging.DEBUG)
        self.combo_level.addItem("INFO+", logging.INFO)
        self.combo_level.addItem("WARNING+", logging.WARNING)
        self.combo_level.addItem("ERRORS ONLY", logging.ERROR)
        self.combo_level.setCurrentIndex(1)  # Default INFO+
        self._current_filter_level = logging.INFO
        self.combo_level.currentIndexChanged.connect(self._on_level_changed)
        top_bar.addWidget(self.combo_level)

        # Search Query
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search in logs...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search_changed)
        top_bar.addWidget(self.search_input)

        # Auto-scroll Checkbox
        self.chk_autoscroll = QCheckBox("Auto-scroll")
        self.chk_autoscroll.setChecked(True)
        top_bar.addWidget(self.chk_autoscroll)

        layout.addLayout(top_bar)

        # 2. Main Log Output Console
        self.text_logs = QTextEdit()
        self.text_logs.setReadOnly(True)
        font = QFont("Cascadia Code", 10)
        font.setStyleHint(QFont.Monospace)
        self.text_logs.setFont(font)
        layout.addWidget(self.text_logs)

        # 3. Footer Toolbar
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        self.lbl_status = QLabel("Entries: 0")
        self.lbl_status.setStyleSheet("color: #64748B; font-size: 11px;")
        bottom_bar.addWidget(self.lbl_status)

        bottom_bar.addStretch()

        btn_folder = QPushButton("📂 Open Folder")
        btn_folder.setCursor(Qt.PointingHandCursor)
        btn_folder.clicked.connect(open_log_folder)
        bottom_bar.addWidget(btn_folder)

        btn_copy = QPushButton("📋 Copy All")
        btn_copy.setCursor(Qt.PointingHandCursor)
        btn_copy.clicked.connect(self._on_copy_all)
        bottom_bar.addWidget(btn_copy)

        btn_export = QPushButton("💾 Export...")
        btn_export.setCursor(Qt.PointingHandCursor)
        btn_export.clicked.connect(self._on_export_file)
        bottom_bar.addWidget(btn_export)

        btn_clear = QPushButton("🧹 Clear")
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.clicked.connect(self._on_clear_logs)
        bottom_bar.addWidget(btn_clear)

        btn_close = QPushButton("Close")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: #FFFFFF;
                border: 1px solid #10B981;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #10B981;
            }
        """)
        btn_close.clicked.connect(self.accept)
        bottom_bar.addWidget(btn_close)

        layout.addLayout(bottom_bar)

    def _on_level_changed(self, index: int) -> None:
        self._current_filter_level = self.combo_level.itemData(index)
        self._reload_view()

    def _on_search_changed(self, text: str) -> None:
        self._search_query = text.strip().lower()
        self._reload_view()

    def _matches_filter(self, entry: Dict[str, Any]) -> bool:
        if entry["levelno"] < self._current_filter_level:
            return False
        if self._search_query:
            combined = f"{entry['asctime']} {entry['level']} {entry['module']} {entry['message']} {entry.get('exc_text', '')}".lower()
            if self._search_query not in combined:
                return False
        return True

    def _format_html_entry(self, entry: Dict[str, Any]) -> str:
        color = self.LEVEL_COLORS.get(entry["level"], "#E2E8F0")
        msg = entry["message"].replace("<", "&lt;").replace(">", "&gt;")
        exc = ""
        if entry.get("exc_text"):
            exc_escaped = entry["exc_text"].replace("<", "&lt;").replace(">", "&gt;")
            exc = f"<pre style='color:#F87171; margin:2px 0 6px 20px;'>{exc_escaped}</pre>"

        return (
            f"<div style='margin-bottom: 3px; line-height: 1.35;'>"
            f"<span style='color: #64748B;'>{entry['asctime']}</span> "
            f"<span style='color: {color}; font-weight: bold;'>[{entry['level']:<7}]</span> "
            f"<span style='color: #818CF8;'>[{entry.get('threadName', 'MainThread')}]</span> "
            f"<span style='color: #94A3B8;'>[{entry['module']}:{entry['funcName']}:{entry['lineno']}]</span> "
            f"<span style='color: #F8FAFC;'>{msg}</span>"
            f"{exc}"
            f"</div>"
        )

    def _reload_view(self) -> None:
        entries = get_memory_logs(min_level=logging.DEBUG)
        filtered = [e for e in entries if self._matches_filter(e)]

        html_blocks = [self._format_html_entry(e) for e in filtered]
        self.text_logs.setHtml("".join(html_blocks))

        self.lbl_status.setText(f"Showing {len(filtered)} of {len(entries)} entries")
        self._last_rendered_count = len(entries)

        if self.chk_autoscroll.isChecked():
            self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        cursor = self.text_logs.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_logs.setTextCursor(cursor)

    def _load_logs(self) -> None:
        self._reload_view()

    def _on_timer_tick(self) -> None:
        entries = get_memory_logs(min_level=logging.DEBUG)
        current_len = len(entries)
        if current_len != self._last_rendered_count:
            self._reload_view()

    def _on_copy_all(self) -> None:
        text = self.text_logs.toPlainText()
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(text)

    def _on_export_file(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Logs As",
            "cleanguard_diagnostic.log",
            "Log Files (*.log);;Text Files (*.txt);;All Files (*)",
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.text_logs.toPlainText())
            except Exception as exc:
                get_logger("ui").error(f"Failed to export logs: {exc}")

    def _on_clear_logs(self) -> None:
        clear_memory_logs()
        self.text_logs.clear()
        self._last_rendered_count = 0
        self.lbl_status.setText("Entries: 0")
