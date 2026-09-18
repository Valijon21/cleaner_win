"""
Large Files Finder Page: Identify, inspect, reveal, and safely delete space-consuming files.
"""

import os
import subprocess
from datetime import datetime
from typing import List, Optional
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QProgressBar,
    QFrame,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from cleanguard.core.scanner.large_files import LargeFileScanner, LargeFileItem
from cleanguard.security.protected_paths import ProtectedPathRegistry
from cleanguard.windows.drives import enumerate_drives
from cleanguard.localization import tr
from cleanguard.utils.formatting import format_bytes
from cleanguard.utils.logging import get_logger

logger = get_logger("ui.large_files")


class LargeFileScanWorker(QThread):
    """Background worker scanning for large files without freezing GUI."""
    progress_updated = pyqtSignal(str, int)  # (current_folder, items_found)
    scan_completed = pyqtSignal(list)       # List[LargeFileItem]

    def __init__(self, scanner: LargeFileScanner, drive_path: str, min_size: int, category: str, parent=None):
        super().__init__(parent)
        self.scanner = scanner
        self.drive_path = drive_path
        self.min_size = min_size
        self.category = category
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        items = self.scanner.scan_drive(
            drive_letter=self.drive_path,
            min_size_bytes=self.min_size,
            category_filter=self.category,
            progress_callback=lambda fld, count: self.progress_updated.emit(fld, count),
            cancel_token=lambda: self._cancelled,
        )
        self.scan_completed.emit(items)


class LargeFilesPage(QWidget):
    """Interactive visual manager for large space-hog files."""

    SIZE_OPTIONS = [
        (104_857_600, "> 100 MB"),
        (262_144_000, "> 250 MB"),
        (524_288_000, "> 500 MB"),
        (1_073_741_824, "> 1 GB"),
        (5_368_709_120, "> 5 GB"),
    ]

    CATEGORY_OPTIONS = [
        ("ALL", "Barcha turlar (All)"),
        ("VIDEOS", "🎬 Videolar (.mp4, .mkv, .avi)"),
        ("ARCHIVES", "📦 Arxivlar va Disk obrazlari (.zip, .rar, .iso)"),
        ("INSTALLERS", "💿 O'rnatuvchilar (.exe, .msi)"),
        ("VIRTUAL_MACHINES", "🖥️ Virtual mashinalar (.vmdk, .vhd)"),
        ("DATABASES_BACKUPS", "💾 Ma'lumotlar bazasi va zaxiralar (.bak, .sql)"),
        ("OTHER", "Boshqa fayllar (Other)"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scanner = LargeFileScanner()
        self.items: List[LargeFileItem] = []
        self.worker: Optional[LargeFileScanWorker] = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # Header Row
        header_row = QHBoxLayout()
        header_text = QVBoxLayout()
        self.lbl_title = QLabel("🐘 " + tr("nav_large_files", "Katta va Og'ir Fayllar Tahlilchisi"))
        self.lbl_title.setStyleSheet("font-size: 24px; font-weight: 700; color: #F9FAFB;")
        self.lbl_subtitle = QLabel(
            tr("large_files_subtitle", "Diskni to'ldirib yotgan 100MB+, 1GB+ fayllarni aniqlang va joy bo'shating")
        )
        self.lbl_subtitle.setStyleSheet("font-size: 13px; color: #9CA3AF;")
        header_text.addWidget(self.lbl_title)
        header_text.addWidget(self.lbl_subtitle)
        header_row.addLayout(header_text)
        header_row.addStretch()
        layout.addLayout(header_row)

        # Stat Cards Row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self.card_count = self._create_stat_card(tr("stat_large_files_count", "Topilgan fayllar"), "0", "#3B82F6")
        self.card_total_size = self._create_stat_card(tr("stat_large_files_size", "Umumiy egallagan joy"), "0 B", "#EF4444")
        self.card_largest = self._create_stat_card(tr("stat_largest_file", "Eng katta fayl"), "—", "#F59E0B")
        stats_row.addWidget(self.card_count)
        stats_row.addWidget(self.card_total_size)
        stats_row.addWidget(self.card_largest)
        layout.addLayout(stats_row)

        # Filter & Scan Controls Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        # Drive selector
        self.lbl_drive_tag = QLabel(tr("lbl_drive", "Disk:"))
        self.lbl_drive_tag.setStyleSheet("font-weight: 600; color: #9CA3AF;")
        toolbar.addWidget(self.lbl_drive_tag)

        self.combo_drives = QComboBox()
        self._populate_drives()
        toolbar.addWidget(self.combo_drives)

        # Size threshold selector
        self.lbl_size_tag = QLabel(tr("lbl_min_size", "Minimal hajm:"))
        self.lbl_size_tag.setStyleSheet("font-weight: 600; color: #9CA3AF;")
        toolbar.addWidget(self.lbl_size_tag)

        self.combo_size = QComboBox()
        for sz, label in self.SIZE_OPTIONS:
            self.combo_size.addItem(label, sz)
        toolbar.addWidget(self.combo_size)

        # Category filter
        self.combo_category = QComboBox()
        for cat_id, label in self.CATEGORY_OPTIONS:
            self.combo_category.addItem(label, cat_id)
        toolbar.addWidget(self.combo_category)

        toolbar.addStretch()

        # Scan Button
        self.btn_scan = QPushButton("🔍 " + tr("btn_scan_large_files", "Skanerlash"))
        self.btn_scan.setObjectName("PrimaryButton")
        self.btn_scan.setCursor(Qt.PointingHandCursor)
        self.btn_scan.clicked.connect(self._start_scan)
        toolbar.addWidget(self.btn_scan)

        layout.addLayout(toolbar)

        # Progress bar and status
        self.prog_bar = QProgressBar()
        self.prog_bar.setRange(0, 0)
        self.prog_bar.setFixedHeight(6)
        self.prog_bar.setVisible(False)
        layout.addWidget(self.prog_bar)

        self.lbl_scan_status = QLabel("")
        self.lbl_scan_status.setStyleSheet("color: #06B6D4; font-size: 11px;")
        self.lbl_scan_status.setVisible(False)
        layout.addWidget(self.lbl_scan_status)

        # Results Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            tr("tbl_filename", "Fayl nomi"),
            tr("tbl_size", "Hajmi"),
            tr("tbl_category", "Turi"),
            tr("tbl_modified", "O'zgartirilgan sana"),
            tr("tbl_path", "Joylashuvi"),
            tr("tbl_action", "Amal"),
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.table.horizontalHeader().resizeSection(0, 240)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(5, 180)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def _create_stat_card(self, title: str, value: str, accent_color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(8, 8, 8, 8)
        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("font-size: 11px; color: #9CA3AF; text-transform: uppercase;")
        lbl_v = QLabel(value)
        lbl_v.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {accent_color};")
        c_layout.addWidget(lbl_t)
        c_layout.addWidget(lbl_v)
        card.lbl_val = lbl_v
        card.lbl_title = lbl_t
        return card

    def _populate_drives(self) -> None:
        self.combo_drives.clear()
        try:
            drives = enumerate_drives()
            for d in drives:
                if d.is_ready and d.drive_type == "Fixed Disk":
                    self.combo_drives.addItem(f"{d.caption} ({d.volume_name or 'Mahalliy disk'})", d.caption)
        except Exception:
            self.combo_drives.addItem("C:", "C:")

    def _start_scan(self) -> None:
        drive = self.combo_drives.currentData() or "C:"
        min_sz = self.combo_size.currentData() or 104_857_600
        cat = self.combo_category.currentData() or "ALL"

        self.btn_scan.setEnabled(False)
        self.prog_bar.setVisible(True)
        self.lbl_scan_status.setVisible(True)
        self.lbl_scan_status.setText(f"{drive} dagi katta fayllar skanerlanmoqda...")

        self.worker = LargeFileScanWorker(
            scanner=self.scanner,
            drive_path=drive,
            min_size=min_sz,
            category=cat,
            parent=self,
        )
        self.worker.progress_updated.connect(self._on_scan_progress)
        self.worker.scan_completed.connect(self._on_scan_completed)
        self.worker.start()

    def _on_scan_progress(self, current_folder: str, count: int) -> None:
        self.lbl_scan_status.setText(f"Topildi: {count} ta • {current_folder[-50:] if len(current_folder) > 50 else current_folder}")

    def _on_scan_completed(self, items: List[LargeFileItem]) -> None:
        self.items = items
        self.btn_scan.setEnabled(True)
        self.prog_bar.setVisible(False)
        self.lbl_scan_status.setVisible(False)

        total_bytes = sum(it.size for it in items)
        self.card_count.lbl_val.setText(str(len(items)))
        self.card_total_size.lbl_val.setText(format_bytes(total_bytes))
        largest_str = format_bytes(items[0].size) if items else "—"
        self.card_largest.lbl_val.setText(largest_str)

        self._populate_table(items)

    def _populate_table(self, items: List[LargeFileItem]) -> None:
        self.table.setUpdatesEnabled(False)
        try:
            self.table.setRowCount(len(items))

            for row, it in enumerate(items):
                # Name
                item_name = QTableWidgetItem(f"  {it.name}")
                item_name.setToolTip(it.path)
                self.table.setItem(row, 0, item_name)

                # Size
                item_size = QTableWidgetItem(format_bytes(it.size))
                item_size.setTextAlignment(Qt.AlignCenter)
                item_size.setForeground(Qt.yellow if it.size > 1_073_741_824 else Qt.white)
                self.table.setItem(row, 1, item_size)

                # Category
                item_cat = QTableWidgetItem(it.category)
                item_cat.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 2, item_cat)

                # Date
                dt = datetime.fromtimestamp(it.modified_at).strftime("%Y-%m-%d %H:%M")
                item_date = QTableWidgetItem(dt)
                item_date.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 3, item_date)

                # Path
                item_path = QTableWidgetItem(it.path)
                item_path.setToolTip(it.path)
                self.table.setItem(row, 4, item_path)

                # Action buttons (Reveal & Delete)
                action_widget = QWidget()
                act_layout = QHBoxLayout(action_widget)
                act_layout.setContentsMargins(4, 2, 4, 2)
                act_layout.setSpacing(6)

                btn_reveal = QPushButton("📂")
                btn_reveal.setToolTip("Faylni papkada ko'rsatish")
                btn_reveal.setFixedSize(30, 26)
                btn_reveal.clicked.connect(lambda _, p=it.path: self._reveal_in_explorer(p))
                act_layout.addWidget(btn_reveal)

                if it.is_protected:
                    lbl_prot = QLabel("🛡️ Himoyalangan")
                    lbl_prot.setStyleSheet("color: #6B7280; font-size: 11px;")
                    act_layout.addWidget(lbl_prot)
                else:
                    btn_del = QPushButton("🗑️")
                    btn_del.setToolTip("Faylni xavfsiz o'chirish")
                    btn_del.setFixedSize(30, 26)
                    btn_del.setStyleSheet("background-color: #EF4444; color: white;")
                    btn_del.clicked.connect(lambda _, item=it: self._delete_file(item))
                    act_layout.addWidget(btn_del)

                self.table.setCellWidget(row, 5, action_widget)
        finally:
            self.table.setUpdatesEnabled(True)

    def _reveal_in_explorer(self, filepath: str) -> None:
        """Open Windows Explorer and select the specified file."""
        if not os.path.exists(filepath):
            QMessageBox.warning(self, tr("msg_error_title", "Xatolik"), "Fayl diskda topilmadi.")
            return
        subprocess.run(["explorer.exe", f"/select,{filepath}"], check=False)

    def _delete_file(self, item: LargeFileItem) -> None:
        """Confirm and safely delete large file."""
        if item.is_protected:
            QMessageBox.warning(
                self,
                tr("msg_protected_title", "Tizim himoyasi"),
                "Ushbu fayl Windows tizim yadrosi yoki muhim zaxiralar tarkibida bo'lgani sababli uni o'chirish taqiqlanadi.",
            )
            return

        reply = QMessageBox.question(
            self,
            tr("confirm_delete_title", "O'chirishni tasdiqlang"),
            f"Rostdan ham ushbu katta faylni o'chirmoqchimisiz?\n\n{item.name} ({format_bytes(item.size)})\n{item.path}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                os.remove(item.path)
                QMessageBox.information(
                    self,
                    tr("msg_success_title", "Muvaffaqiyatli"),
                    f"Fayl o'chirildi va {format_bytes(item.size)} joy bo'shatildi!",
                )
                # Remove from current list and refresh table
                self.items = [x for x in self.items if x.path != item.path]
                self._populate_table(self.items)
                total_bytes = sum(x.size for x in self.items)
                self.card_count.lbl_val.setText(str(len(self.items)))
                self.card_total_size.lbl_val.setText(format_bytes(total_bytes))
            except Exception as e:
                QMessageBox.critical(self, tr("msg_error_title", "Xatolik"), f"Faylni o'chirib bo'lmadi: {e}")
