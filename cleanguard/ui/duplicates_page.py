"""
Duplicate Files Page: Scan drives and folders for identical files and safely reclaim storage.
"""

import os
from typing import List, Optional
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QComboBox,
    QFileDialog,
    QProgressBar,
    QFrame,
    QMessageBox,
    QHeaderView,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from cleanguard.core.scanner.duplicate_scanner import DuplicateScanner, DuplicateGroup
from cleanguard.core.safety import SafetyEngine
from cleanguard.windows.drives import enumerate_drives
from cleanguard.utils.formatting import format_bytes
from cleanguard.localization import tr
from cleanguard.utils.logging import get_logger

logger = get_logger("ui.duplicates")


class DuplicateScanWorker(QThread):
    """Background worker for duplicate file scanning."""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(list)

    def __init__(self, target_dir: str, min_size_bytes: int = 1048576, parent=None):
        super().__init__(parent)
        self.target_dir = target_dir
        self.min_size_bytes = min_size_bytes
        self.scanner = DuplicateScanner()
        self._cancelled = False

    def run(self):
        def on_prog(count, path, _):
            self.progress.emit(count, path)

        groups = self.scanner.scan_directory(
            self.target_dir,
            min_size_bytes=self.min_size_bytes,
            progress_callback=on_prog,
        )
        self.finished.emit(groups)

    def cancel(self):
        self._cancelled = True


class DuplicatesPage(QWidget):
    """Interactive UI page to find and clean duplicate files."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.groups: List[DuplicateGroup] = []
        self.worker: Optional[DuplicateScanWorker] = None
        self.safety_engine = SafetyEngine()
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # Header Row
        header_row = QHBoxLayout()
        header_text = QVBoxLayout()
        self.lbl_title = QLabel(tr("nav_duplicates", "🔍 Dublikat fayllarni qidirish"))
        self.lbl_title.setStyleSheet("font-size: 24px; font-weight: 700; color: #F9FAFB;")
        self.lbl_subtitle = QLabel(
            tr("duplicates_subtitle", "Bir xil mazmundagi nusxa fayllarni aniqlang va diskda joy tejang")
        )
        self.lbl_subtitle.setStyleSheet("font-size: 13px; color: #9CA3AF;")
        header_text.addWidget(self.lbl_title)
        header_text.addWidget(self.lbl_subtitle)
        header_row.addLayout(header_text)
        header_row.addStretch()

        self.btn_browse = QPushButton(tr("btn_browse_folder", "📁 Papka tanlash..."))
        self.btn_browse.setObjectName("SecondaryButton")
        self.btn_browse.setCursor(Qt.PointingHandCursor)
        self.btn_browse.clicked.connect(self._on_browse_folder)
        header_row.addWidget(self.btn_browse)

        layout.addLayout(header_row)

        # Drive and Size Filter Bar
        filter_bar = QHBoxLayout()
        self.lbl_drive = QLabel(tr("lbl_drive_path", "Disk / Manzil:"))
        self.lbl_drive.setStyleSheet("color: #D1D5DB; font-weight: 600;")
        filter_bar.addWidget(self.lbl_drive)

        self.combo_drives = QComboBox()
        drives = enumerate_drives()
        for d in drives:
            self.combo_drives.addItem(f"{d.letter} ({d.label or 'Mahalliy disk'})", d.letter + "\\")
        filter_bar.addWidget(self.combo_drives)

        self.lbl_min_size = QLabel(tr("lbl_min_size", "Minimal hajm:"))
        self.lbl_min_size.setStyleSheet("color: #D1D5DB; font-weight: 600; margin-left: 12px;")
        filter_bar.addWidget(self.lbl_min_size)

        self.combo_min_size = QComboBox()
        self._populate_min_sizes()
        filter_bar.addWidget(self.combo_min_size)

        filter_bar.addStretch()

        self.btn_start_scan = QPushButton("  " + tr("btn_scan_duplicates", "🔍 Dublikatlarni qidirish") + "  ")
        self.btn_start_scan.setObjectName("PrimaryButton")
        self.btn_start_scan.setCursor(Qt.PointingHandCursor)
        self.btn_start_scan.setStyleSheet("background-color: #10B981; font-weight: 700; color: white; padding: 8px 16px; border-radius: 6px;")
        self.btn_start_scan.clicked.connect(self._on_start_scan)
        filter_bar.addWidget(self.btn_start_scan)

        layout.addLayout(filter_bar)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #374151;
                border-radius: 4px;
                text-align: center;
                background-color: #1F2937;
                color: #F9FAFB;
                height: 18px;
            }
            QProgressBar::chunk {
                background-color: #10B981;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Quick Actions Bar
        self.action_bar = QHBoxLayout()
        self.lbl_stats = QLabel("Dublikatlar topilmadi")
        self.lbl_stats.setStyleSheet("color: #9CA3AF; font-size: 13px;")
        self.action_bar.addWidget(self.lbl_stats)
        self.action_bar.addStretch()

        self.btn_keep_oldest = QPushButton(tr("btn_keep_oldest", "Eng eskisini saqlash"))
        self.btn_keep_oldest.setCursor(Qt.PointingHandCursor)
        self.btn_keep_oldest.clicked.connect(lambda: self._apply_auto_selection("oldest"))
        self.action_bar.addWidget(self.btn_keep_oldest)

        self.btn_keep_newest = QPushButton(tr("btn_keep_newest", "Eng yangisini saqlash"))
        self.btn_keep_newest.setCursor(Qt.PointingHandCursor)
        self.btn_keep_newest.clicked.connect(lambda: self._apply_auto_selection("newest"))
        self.action_bar.addWidget(self.btn_keep_newest)

        self.btn_clean_duplicates = QPushButton("🗑️ Tanlangan dublikatlarni o'chirish")
        self.btn_clean_duplicates.setCursor(Qt.PointingHandCursor)
        self.btn_clean_duplicates.setStyleSheet("background-color: #EF4444; font-weight: 700; color: white; padding: 6px 14px; border-radius: 6px;")
        self.btn_clean_duplicates.clicked.connect(self._on_clean_duplicates)
        self.action_bar.addWidget(self.btn_clean_duplicates)

        layout.addLayout(self.action_bar)

        # Results Tree Widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Fayl nomi / Joylashuvi", "Hajmi", "O'zgartirilgan sana", "Belgi"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        layout.addWidget(self.tree)

    def _populate_min_sizes(self) -> None:
        cur_data = self.combo_min_size.currentData() if hasattr(self, "combo_min_size") and self.combo_min_size.count() > 0 else 1024 * 1024
        self.combo_min_size.clear()
        self.combo_min_size.addItem(tr("size_above_1mb", "1 MB dan katta"), 1024 * 1024)
        self.combo_min_size.addItem(tr("size_above_10mb", "10 MB dan katta"), 10 * 1024 * 1024)
        self.combo_min_size.addItem(tr("size_above_50mb", "50 MB dan katta"), 50 * 1024 * 1024)
        self.combo_min_size.addItem(tr("size_above_100kb", "100 KB dan katta"), 100 * 1024)
        idx = self.combo_min_size.findData(cur_data)
        if idx >= 0:
            self.combo_min_size.setCurrentIndex(idx)

    def _on_browse_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, tr("btn_browse_folder", "Dublikatlarni qidirish uchun papkani tanlang"))
        if folder:
            self.combo_drives.insertItem(0, f"📁 {folder}", folder)
            self.combo_drives.setCurrentIndex(0)

    def _on_start_scan(self) -> None:
        target = self.combo_drives.currentData()
        if not target or not os.path.exists(target):
            QMessageBox.warning(self, tr("msg_error_title", "Xato"), tr("msg_path_not_found", "Tanlangan manzil mavjud emas."))
            return

        min_size = self.combo_min_size.currentData()
        self.btn_start_scan.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.lbl_stats.setText("Skanerlanmoqda, kuting...")
        self.tree.clear()

        self.worker = DuplicateScanWorker(target, min_size_bytes=min_size, parent=self)
        self.worker.progress.connect(lambda count, path: self.lbl_stats.setText(f"Tekshirilmoqda ({count} ta fayl): {os.path.basename(path)}"))
        self.worker.finished.connect(self._on_scan_finished)
        self.worker.start()

    def _on_scan_finished(self, groups: List[DuplicateGroup]) -> None:
        self.btn_start_scan.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.groups = groups

        tot_dups = sum(len(g.items) - 1 for g in groups)
        tot_reclaim = sum(g.reclaimable_bytes for g in groups)

        self.lbl_stats.setText(
            f"Topildi: {len(groups)} ta guruh, {tot_dups} ta ortiqcha nusxa ({format_bytes(tot_reclaim)} bo'shatilishi mumkin)"
        )

        self.tree.clear()
        for idx, grp in enumerate(groups, 1):
            top_item = QTreeWidgetItem(self.tree)
            top_item.setText(0, f"Guruh #{idx} ({len(grp.items)} ta nusxa) — Xesh: {grp.file_hash[:8]}...")
            top_item.setText(1, format_bytes(grp.file_size))
            top_item.setExpanded(True)

            for it in grp.items:
                child = QTreeWidgetItem(top_item)
                child.setText(0, it.path)
                child.setText(1, format_bytes(it.size))
                child.setText(2, str(it.modified_at))
                child.setCheckState(0, Qt.Unchecked)
                child.setData(0, Qt.UserRole, it)

    def _apply_auto_selection(self, mode: str) -> None:
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            grp_item = root.child(i)
            children = [grp_item.child(j) for j in range(grp_item.childCount())]
            if not children:
                continue

            # Sort children by modified_at
            children.sort(key=lambda c: c.data(0, Qt.UserRole).modified_at if c.data(0, Qt.UserRole) else 0)

            if mode == "oldest":
                # Keep first (oldest), check remaining
                children[0].setCheckState(0, Qt.Unchecked)
                for c in children[1:]:
                    c.setCheckState(0, Qt.Checked)
            elif mode == "newest":
                # Keep last (newest), check preceding
                children[-1].setCheckState(0, Qt.Unchecked)
                for c in children[:-1]:
                    c.setCheckState(0, Qt.Checked)

    def _on_clean_duplicates(self) -> None:
        selected_to_delete = []
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            grp_item = root.child(i)
            for j in range(grp_item.childCount()):
                child = grp_item.child(j)
                if child.checkState(0) == Qt.Checked:
                    it = child.data(0, Qt.UserRole)
                    if it:
                        selected_to_delete.append(it)

        if not selected_to_delete:
            QMessageBox.information(self, tr("msg_info_title", "Ma'lumot"), tr("msg_duplicate_no_selection", "O'chirish uchun birorta ham dublikat tanlanmagan."))
            return

        tot_bytes = sum(it.size for it in selected_to_delete)
        reply = QMessageBox.question(
            self,
            tr("msg_confirm_title", "Tasdiqlash"),
            tr("msg_duplicate_clean_confirm", count=len(selected_to_delete), size=format_bytes(tot_bytes)),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            deleted_count = 0
            for it in selected_to_delete:
                try:
                    # Pass through SafetyEngine path guard first
                    if self.safety_engine.is_protected_path(it.path):
                        continue
                    if os.path.exists(it.path):
                        os.remove(it.path)
                        deleted_count += 1
                except Exception as ex:
                    logger.error("Failed removing duplicate %s: %s", it.path, ex)

            QMessageBox.information(self, tr("msg_success_title", "Muvaffaqiyatli"), tr("msg_duplicate_clean_success", count=deleted_count))
            self._on_start_scan()

    def retranslate_ui(self, lang_code: str = "") -> None:
        self.lbl_title.setText(tr("nav_duplicates", "🔍 Dublikat fayllarni qidirish"))
        self.lbl_subtitle.setText(tr("duplicates_subtitle", "Bir xil mazmundagi nusxa fayllarni aniqlang va diskda joy tejang"))
        self.btn_browse.setText(tr("btn_browse_folder", "📁 Papka tanlash..."))
        if hasattr(self, "lbl_drive"):
            self.lbl_drive.setText(tr("lbl_drive_path", "Disk / Manzil:"))
        if hasattr(self, "lbl_min_size"):
            self.lbl_min_size.setText(tr("lbl_min_size", "Minimal hajm:"))
        self._populate_min_sizes()
        self.btn_keep_oldest.setText(tr("btn_keep_oldest", "Eng eskisini saqlash"))
        self.btn_keep_newest.setText(tr("btn_keep_newest", "Eng yangisini saqlash"))
        self.btn_start_scan.setText("  " + tr("btn_scan_duplicates", "🔍 Dublikatlarni qidirish") + "  ")
        self.btn_clean_duplicates.setText(tr("btn_clean_duplicates", "🗑️ Tanlangan dublikatlarni o'chirish"))
        self.tree.setHeaderLabels([
            tr("tbl_file_path", "Fayl nomi / Joylashuvi"),
            tr("tbl_size", "Hajmi"),
            tr("tbl_modified_date", "O'zgartirilgan sana"),
            tr("tbl_marker", "Belgi"),
        ])

