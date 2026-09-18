"""
Uninstaller Page: View installed applications, trigger official uninstallers, and clean residual leftovers.
"""

import os
import shutil
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
    QFrame,
    QMessageBox,
    QDialog,
    QTreeWidget,
    QTreeWidgetItem,
)
from PyQt5.QtCore import Qt
from cleanguard.windows.uninstaller import AppUninstallerManager, InstalledApp
from cleanguard.core.safety import SafetyEngine
from cleanguard.utils.formatting import format_bytes
from cleanguard.localization import tr
from cleanguard.utils.logging import get_logger

logger = get_logger("ui.uninstaller")


class LeftoversDialog(QDialog):
    """Modal dialog displaying residual application data leftovers for deletion."""

    def __init__(self, app: InstalledApp, leftovers: list, parent=None):
        super().__init__(parent)
        self.app = app
        self.leftovers = leftovers
        self.safety_engine = SafetyEngine()
        self.setWindowTitle(f"'{app.name}' — Qoldiq fayllar")
        self.resize(700, 420)
        self.setStyleSheet("""
            QDialog {
                background-color: #111827;
                color: #F9FAFB;
            }
            QLabel { color: #F9FAFB; }
        """)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        lbl_header = QLabel(f"'{self.app.name}' dasturining diskdagi qoldiqlari:")
        lbl_header.setStyleSheet("font-size: 16px; font-weight: 700; color: #10B981;")
        layout.addWidget(lbl_header)

        tot_bytes = sum(it.size for it in self.leftovers)
        lbl_info = QLabel(f"Topildi: {len(self.leftovers)} ta qoldiq katalog ({format_bytes(tot_bytes)})")
        lbl_info.setStyleSheet("font-size: 13px; color: #9CA3AF;")
        layout.addWidget(lbl_info)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Qoldiq yo'li", "Hajmi", "Xavfsizlik"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        for it in self.leftovers:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, it.path)
            item.setText(1, format_bytes(it.size))
            item.setText(2, "O'chirish xavfsiz")
            item.setCheckState(0, Qt.Checked)
            item.setData(0, Qt.UserRole, it)

        layout.addWidget(self.tree)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_cancel = QPushButton("Yopish")
        self.btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_cancel)

        self.btn_clean = QPushButton("🗑️ Tanlangan qoldiqlarni tozalash")
        self.btn_clean.setStyleSheet("background-color: #EF4444; color: white; font-weight: 700; padding: 6px 14px; border-radius: 6px;")
        self.btn_clean.clicked.connect(self._on_clean)
        btn_row.addWidget(self.btn_clean)

        layout.addLayout(btn_row)

    def _on_clean(self) -> None:
        deleted = 0
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            child = root.child(i)
            if child.checkState(0) == Qt.Checked:
                it = child.data(0, Qt.UserRole)
                if it and os.path.exists(it.path):
                    # Validate through SafetyEngine
                    if self.safety_engine.is_protected_path(it.path):
                        continue
                    try:
                        if os.path.isdir(it.path):
                            shutil.rmtree(it.path, ignore_errors=True)
                        else:
                            os.remove(it.path)
                        deleted += 1
                    except Exception as ex:
                        logger.error("Failed cleaning leftover %s: %s", it.path, ex)

        QMessageBox.information(self, "Tozalandi", f"{deleted} ta qoldiq muvaffaqiyatli tozalandi.")
        self.accept()


class UninstallerPage(QWidget):
    """Installed applications and leftover cleaner UI."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = AppUninstallerManager()
        self.apps: List[InstalledApp] = []
        self._init_ui()
        self.refresh_apps()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # Header Row
        header_row = QHBoxLayout()
        header_text = QVBoxLayout()
        self.lbl_title = QLabel(tr("nav_uninstaller", "📦 Dasturlar va qoldiqlarni o'chirish"))
        self.lbl_title.setStyleSheet("font-size: 24px; font-weight: 700; color: #F9FAFB;")
        self.lbl_subtitle = QLabel(
            tr("uninstaller_subtitle", "O'rnatilgan dasturlarni to'liq o'chiring va qoldiqlarini tozalang")
        )
        self.lbl_subtitle.setStyleSheet("font-size: 13px; color: #9CA3AF;")
        header_text.addWidget(self.lbl_title)
        header_text.addWidget(self.lbl_subtitle)
        header_row.addLayout(header_text)
        header_row.addStretch()

        self.btn_refresh = QPushButton("🔄 " + tr("btn_refresh", "Yangilash"))
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.refresh_apps)
        header_row.addWidget(self.btn_refresh)
        layout.addLayout(header_row)

        # Search Bar & Count
        filter_row = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 " + tr("search_placeholder", "Dastur yoki noshir nomini qidiring..."))
        self.txt_search.textChanged.connect(self._apply_filter)
        filter_row.addWidget(self.txt_search)

        self.lbl_count = QLabel("Jami: 0 ta dastur")
        self.lbl_count.setStyleSheet("color: #9CA3AF; font-size: 13px; margin-left: 12px;")
        filter_row.addWidget(self.lbl_count)
        layout.addLayout(filter_row)

        # Apps Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Dastur nomi", "Noshir", "Versiya", "Hajmi", "Amallar"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(4, 210)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def refresh_apps(self) -> None:
        self.apps = self.manager.get_installed_apps()
        self.lbl_count.setText(f"Jami: {len(self.apps)} ta dastur")
        self._populate_table(self.apps)

    def _apply_filter(self) -> None:
        query = self.txt_search.text().strip().lower()
        if not query:
            self._populate_table(self.apps)
            return

        filtered = [
            a for a in self.apps
            if query in a.name.lower() or query in a.publisher.lower()
        ]
        self._populate_table(filtered)

    def _populate_table(self, apps: List[InstalledApp]) -> None:
        self.table.setRowCount(len(apps))

        for row, a in enumerate(apps):
            # Name
            self.table.setItem(row, 0, QTableWidgetItem(f"  {a.name}"))

            # Publisher
            item_pub = QTableWidgetItem(a.publisher)
            item_pub.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, item_pub)

            # Version
            item_ver = QTableWidgetItem(a.version or "--")
            item_ver.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, item_ver)

            # Size
            size_str = format_bytes(a.estimated_size) if a.estimated_size > 0 else "--"
            item_size = QTableWidgetItem(size_str)
            item_size.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, item_size)

            # Actions cell (Uninstall + Leftovers)
            cell_widget = QWidget()
            cell_layout = QHBoxLayout(cell_widget)
            cell_layout.setContentsMargins(4, 2, 4, 2)
            cell_layout.setSpacing(6)

            btn_uninstall = QPushButton("O'chirish")
            btn_uninstall.setStyleSheet("background-color: #EF4444; color: white; border-radius: 4px; padding: 3px 8px; font-size: 11px;")
            btn_uninstall.setCursor(Qt.PointingHandCursor)
            btn_uninstall.clicked.connect(lambda _, app=a: self._on_uninstall_clicked(app))

            btn_leftovers = QPushButton("Qoldiqlar")
            btn_leftovers.setStyleSheet("background-color: #3B82F6; color: white; border-radius: 4px; padding: 3px 8px; font-size: 11px;")
            btn_leftovers.setCursor(Qt.PointingHandCursor)
            btn_leftovers.clicked.connect(lambda _, app=a: self._on_leftovers_clicked(app))

            cell_layout.addWidget(btn_uninstall)
            cell_layout.addWidget(btn_leftovers)
            self.table.setCellWidget(row, 4, cell_widget)

    def _on_uninstall_clicked(self, app: InstalledApp) -> None:
        reply = QMessageBox.question(
            self,
            "Dasturni o'chirish",
            f"'{app.name}' dasturining rasmiy o'chiruvchisi (Uninstaller) ishga tushirilsinmi?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply == QMessageBox.Yes:
            ok, msg = self.manager.launch_uninstall(app)
            if ok:
                QMessageBox.information(self, "Bajarildi", f"{msg}\nO'chirish yakunlangach 'Qoldiqlar' tugmasi orqali qolgan kesh va ma'lumotlarni tozalashingiz mumkin.")
            else:
                QMessageBox.warning(self, "Xato", f"Uninstaller ishga tushmadi: {msg}")

    def _on_leftovers_clicked(self, app: InstalledApp) -> None:
        leftovers = self.manager.find_leftovers(app.name, app.publisher)
        if not leftovers:
            QMessageBox.information(self, "Toza", f"'{app.name}' uchun hech qanday qoldiq papkalar topilmadi.")
            return

        dialog = LeftoversDialog(app, leftovers, parent=self)
        dialog.exec_()

    def retranslate_ui(self, lang_code: str = "") -> None:
        self.lbl_title.setText(tr("nav_uninstaller", "📦 Dasturlar va qoldiqlarni o'chirish"))
        self.lbl_subtitle.setText(tr("uninstaller_subtitle", "O'rnatilgan dasturlarni to'liq o'chiring va qoldiqlarini tozalang"))
        self.btn_refresh.setText("🔄 " + tr("btn_refresh", "Yangilash"))
        self.txt_search.setPlaceholderText("🔍 " + tr("search_placeholder", "Dastur yoki noshir nomini qidiring..."))
        self.lbl_count.setText(f"Jami: {len(self.apps)} ta dastur")
        self.table.setHorizontalHeaderLabels([
            tr("tbl_app_name", "Dastur nomi"),
            tr("tbl_publisher", "Noshir"),
            tr("tbl_version", "Versiya"),
            tr("tbl_size", "Hajmi"),
            tr("tbl_actions", "Amallar"),
        ])

