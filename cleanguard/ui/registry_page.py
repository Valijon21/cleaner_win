"""
Registry Cleaner Page: Safe registry scan, cleanup, and 1-click backup rollback UI.
"""

import os
from typing import List
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QMessageBox,
    QDialog,
    QListWidget,
    QListWidgetItem,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from cleanguard.windows.registry_cleaner import SafeRegistryCleaner, RegistryIssue
from cleanguard.localization import tr
from cleanguard.utils.logging import get_logger

logger = get_logger("ui.registry")


class RegistryScanWorker(QThread):
    """Background worker for scanning registry without UI freezes."""
    finished = pyqtSignal(list)

    def __init__(self, cleaner: SafeRegistryCleaner):
        super().__init__()
        self.cleaner = cleaner

    def run(self):
        issues = self.cleaner.scan_all()
        self.finished.emit(issues)


class RollbackDialog(QDialog):
    """Dialog allowing the user to select and restore a previous .reg backup."""

    def __init__(self, cleaner: SafeRegistryCleaner, parent=None):
        super().__init__(parent)
        self.cleaner = cleaner
        self.setWindowTitle("Reestr zaxirasini qaytarish (Rollback)")
        self.resize(550, 360)
        self.setStyleSheet("background-color: #111827; color: #F9FAFB;")
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        lbl = QLabel("Mavjud reestr zaxira nusxalari (.reg):")
        lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #10B981;")
        layout.addWidget(lbl)

        self.list_backups = QListWidget()
        self.list_backups.setStyleSheet("background-color: #1F2937; border: 1px solid #374151; border-radius: 6px; padding: 6px;")
        backups = self.cleaner.get_available_backups()
        for b in backups:
            item = QListWidgetItem(f"📄 {os.path.basename(b)}")
            item.setData(Qt.UserRole, b)
            self.list_backups.addItem(item)
        layout.addWidget(self.list_backups)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Bekor qilish")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_restore = QPushButton("⏪ Tanlangan nusxani tiklash")
        btn_restore.setStyleSheet("background-color: #10B981; color: white; font-weight: 700; padding: 6px 14px; border-radius: 6px;")
        btn_restore.clicked.connect(self._on_restore)
        btn_row.addWidget(btn_restore)

        layout.addLayout(btn_row)

    def _on_restore(self) -> None:
        cur_item = self.list_backups.currentItem()
        if not cur_item:
            QMessageBox.warning(self, "Tanlang", "Iltimos, tiklash uchun ro'yxatdan birorta zaxira faylini tanlang.")
            return

        b_path = cur_item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self,
            "Reestrni tiklash",
            f"Haqiqatan ham '{os.path.basename(b_path)}' faylidagi ma'lumotlarni reestrga qaytarmoqchimisiz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply == QMessageBox.Yes:
            ok, msg = self.cleaner.restore_backup(b_path)
            if ok:
                QMessageBox.information(self, "Tiklandi", msg)
                self.accept()
            else:
                QMessageBox.warning(self, "Xatolik", msg)


class RegistryPage(QWidget):
    """Safe registry cleaning and repair UI."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cleaner = SafeRegistryCleaner()
        self.issues: List[RegistryIssue] = []
        self.scan_worker = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # Header
        header_row = QHBoxLayout()
        header_text = QVBoxLayout()
        self.lbl_title = QLabel("🧩 " + tr("nav_registry", "Xavfsiz Reestr tozalovchi"))
        self.lbl_title.setStyleSheet("font-size: 24px; font-weight: 700; color: #F9FAFB;")
        self.lbl_subtitle = QLabel(
            tr("registry_subtitle", "Eskirgan va buzilgan reestr kalitlarini avtomatik zaxiralash bilan tozalash")
        )
        self.lbl_subtitle.setStyleSheet("font-size: 13px; color: #9CA3AF;")
        header_text.addWidget(self.lbl_title)
        header_text.addWidget(self.lbl_subtitle)
        header_row.addLayout(header_text)
        header_row.addStretch()

        self.btn_rollback = QPushButton("⏪ " + tr("btn_registry_rollback", "Zaxiradan qaytarish (Rollback)"))
        self.btn_rollback.setCursor(Qt.PointingHandCursor)
        self.btn_rollback.clicked.connect(self._open_rollback_dialog)
        header_row.addWidget(self.btn_rollback)

        layout.addLayout(header_row)

        # Action Bar & Stats
        action_bar = QHBoxLayout()
        self.btn_scan = QPushButton("🔍 " + tr("btn_scan_registry", "Reestrni skanerlash"))
        self.btn_scan.setStyleSheet("background-color: #3B82F6; color: white; font-weight: 700; padding: 7px 16px; border-radius: 6px;")
        self.btn_scan.setCursor(Qt.PointingHandCursor)
        self.btn_scan.clicked.connect(self.start_scan)
        action_bar.addWidget(self.btn_scan)

        self.btn_clean = QPushButton("🧹 " + tr("btn_clean_registry", "Tanlanganlarni tozalash"))
        self.btn_clean.setStyleSheet("background-color: #EF4444; color: white; font-weight: 700; padding: 7px 16px; border-radius: 6px;")
        self.btn_clean.setCursor(Qt.PointingHandCursor)
        self.btn_clean.setEnabled(False)
        self.btn_clean.clicked.connect(self._on_clean_clicked)
        action_bar.addWidget(self.btn_clean)

        self.lbl_status = QLabel("Holat: Skanerlashga tayyor")
        self.lbl_status.setStyleSheet("color: #9CA3AF; font-size: 13px; margin-left: 12px;")
        action_bar.addWidget(self.lbl_status)
        action_bar.addStretch()

        layout.addLayout(action_bar)

        # Issues Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Muammo tavsifi", "Toifa", "Kalit joylashuvi", "Reestr qiymati"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def start_scan(self) -> None:
        self.btn_scan.setEnabled(False)
        self.lbl_status.setText("Reestr skanerlanmoqda...")
        self.scan_worker = RegistryScanWorker(self.cleaner)
        self.scan_worker.finished.connect(self._on_scan_completed)
        self.scan_worker.start()

    def _on_scan_completed(self, issues: List[RegistryIssue]) -> None:
        self.btn_scan.setEnabled(True)
        self.issues = issues
        self.lbl_status.setText(f"Topildi: {len(issues)} ta eskirgan reestr yozuvi (Xavfsiz tozalash mumkin)")
        self.btn_clean.setEnabled(len(issues) > 0)
        self._populate_table()

    def _populate_table(self) -> None:
        self.table.setRowCount(len(self.issues))
        for row, iss in enumerate(self.issues):
            item_desc = QTableWidgetItem(f"  {iss.details}")
            item_desc.setCheckState(Qt.Checked)
            self.table.setItem(row, 0, item_desc)

            item_type = QTableWidgetItem(iss.issue_type)
            item_type.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, item_type)

            item_key = QTableWidgetItem(f"{iss.hive_name}\\{iss.sub_key}")
            self.table.setItem(row, 2, item_key)

            item_val = QTableWidgetItem(iss.value_name[:30])
            self.table.setItem(row, 3, item_val)

    def _on_clean_clicked(self) -> None:
        selected_issues = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                selected_issues.append(self.issues[row])

        if not selected_issues:
            QMessageBox.information(self, "Tanlang", "Tozalash uchun birorta ham yozuv belgilanmagan.")
            return

        reply = QMessageBox.question(
            self,
            "Reestrni tozalash",
            f"Tanlangan {len(selected_issues)} ta reestr kalitlari tozalanadi.\nOldin avtomatik .reg zaxira nusxasi olinadi.\nDavom etilsinmi?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply == QMessageBox.Yes:
            deleted, failed, backup_path = self.cleaner.clean_issues(selected_issues, backup=True)
            msg = f"{deleted} ta reestr yozuvi muvaffaqiyatli tozalandi."
            if backup_path:
                msg += f"\nZaxira saqlandi: {os.path.basename(backup_path)}"
            QMessageBox.information(self, "Bajarildi", msg)
            self.start_scan()

    def _open_rollback_dialog(self) -> None:
        dialog = RollbackDialog(self.cleaner, self)
        dialog.exec_()

    def retranslate_ui(self, lang_code: str = "") -> None:
        self.lbl_title.setText("🧩 " + tr("nav_registry", "Xavfsiz Reestr tozalovchi"))
        self.lbl_subtitle.setText(tr("registry_subtitle", "Eskirgan va buzilgan reestr kalitlarini avtomatik zaxiralash bilan tozalash"))
        self.btn_scan.setText("🔍 " + tr("btn_scan_registry", "Reestrni skanerlash"))
        self.btn_clean.setText("🧹 " + tr("btn_clean_registry", "Tanlanganlarni tozalash"))
        self.btn_rollback.setText("⏪ " + tr("btn_registry_rollback", "Zaxiradan qaytarish (Rollback)"))
