"""
Tweaks Page: Windows 10/11 Bloatware Remover & Telemetry Privacy Tweaker UI.
"""

from typing import List
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QMessageBox,
    QScrollArea,
    QFrame,
)
from PyQt5.QtCore import Qt
from cleanguard.windows.tweaks import TweaksManager, PrivacyTweak, BloatwareApp
from cleanguard.windows.privileges import is_user_admin, request_elevation
from cleanguard.localization import tr
from cleanguard.utils.logging import get_logger

logger = get_logger("ui.tweaks")


class TweaksPage(QWidget):
    """Modern interface for managing Windows bloatware and privacy/telemetry settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = TweaksManager()
        self.bloatware_apps: List[BloatwareApp] = []
        self._init_ui()
        self.refresh_all()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # Header Row
        header_row = QHBoxLayout()
        header_text = QVBoxLayout()
        self.lbl_title = QLabel("🛠️ " + tr("nav_tweaks", "Windows optimizatsiya va Maxfiylik"))
        self.lbl_title.setStyleSheet("font-size: 24px; font-weight: 700; color: #F9FAFB;")
        self.lbl_subtitle = QLabel(
            tr("tweaks_subtitle", "Windows 10/11 standart ilovalarini (Bloatware) va telemetriya xizmatlarini boshqaring")
        )
        self.lbl_subtitle.setStyleSheet("font-size: 13px; color: #9CA3AF;")
        header_text.addWidget(self.lbl_title)
        header_text.addWidget(self.lbl_subtitle)
        header_row.addLayout(header_text)
        header_row.addStretch()

        self.btn_refresh = QPushButton("🔄 " + tr("btn_refresh", "Yangilash"))
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.refresh_all)
        header_row.addWidget(self.btn_refresh)
        layout.addLayout(header_row)

        # Tabs: 1) Privacy & Telemetry  2) Bloatware Apps
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #374151;
                background-color: #111827;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #1F2937;
                color: #9CA3AF;
                padding: 8px 18px;
                font-weight: 600;
                font-size: 13px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background-color: #10B981;
                color: white;
            }
        """)

        # Tab 1: Privacy Tweaks
        self.tab_privacy = QWidget()
        self._init_privacy_tab()
        self.tabs.addTab(self.tab_privacy, tr("tweaks_tab_privacy", "🛡️ Maxfiylik va Telemetriya (Privacy)"))

        # Tab 2: Bloatware Remover
        self.tab_bloatware = QWidget()
        self._init_bloatware_tab()
        self.tabs.addTab(self.tab_bloatware, tr("tweaks_tab_bloatware", "📦 Standart UWP Ilovalar (Bloatware)"))

        layout.addWidget(self.tabs)

    def _init_privacy_tab(self) -> None:
        p_layout = QVBoxLayout(self.tab_privacy)
        p_layout.setContentsMargins(20, 20, 20, 20)
        p_layout.setSpacing(14)

        lbl_desc = QLabel(
            "Microsoft ga ma'lumot yuborish, diagnostika telemetriyasi va shaxsiy tavsiyalarni o'chirish orqali "
            "tizim tezligini hamda shaxsiy daxlsizlikni oshiring."
        )
        lbl_desc.setStyleSheet("color: #9CA3AF; font-size: 12px; line-height: 1.4;")
        lbl_desc.setWordWrap(True)
        p_layout.addWidget(lbl_desc)

        # Scroll area for tweak cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll_content = QWidget()
        self.tweaks_container = QVBoxLayout(scroll_content)
        self.tweaks_container.setSpacing(10)
        self.tweaks_container.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(scroll_content)
        p_layout.addWidget(scroll)

    def _init_bloatware_tab(self) -> None:
        b_layout = QVBoxLayout(self.tab_bloatware)
        b_layout.setContentsMargins(20, 20, 20, 20)
        b_layout.setSpacing(12)

        lbl_info = QLabel(
            "Windows bilan birga avtomatik o'rnatilgan, fonga yuk bo'luvchi AppX paketlarini xavfsiz o'chirish. "
            "CleanGuard tizim do'koni (Store) va xavfsizlik komponentlariga tegmaydi."
        )
        lbl_info.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        lbl_info.setWordWrap(True)
        b_layout.addWidget(lbl_info)

        self.table_bloatware = QTableWidget()
        self.table_bloatware.setColumnCount(4)
        self.table_bloatware.setHorizontalHeaderLabels(["Ilova nomi", "Kategoriya", "Holati", "Amal"])
        self.table_bloatware.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_bloatware.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_bloatware.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_bloatware.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.table_bloatware.setColumnWidth(3, 130)
        self.table_bloatware.verticalHeader().setVisible(False)
        self.table_bloatware.setAlternatingRowColors(True)
        b_layout.addWidget(self.table_bloatware)

    def refresh_all(self) -> None:
        self._refresh_privacy_tweaks()
        self._refresh_bloatware_list()

    def _refresh_privacy_tweaks(self) -> None:
        # Clear existing cards
        while self.tweaks_container.count() > 0:
            item = self.tweaks_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for tweak in self.manager.tweaks:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #1F2937;
                    border: 1px solid #374151;
                    border-radius: 8px;
                    padding: 8px;
                }
            """)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(14, 10, 14, 10)

            info_layout = QVBoxLayout()
            info_layout.setSpacing(4)
            lbl_name = QLabel(tweak.name)
            lbl_name.setStyleSheet("font-size: 14px; font-weight: 600; color: #F9FAFB;")
            lbl_desc = QLabel(tweak.description)
            lbl_desc.setStyleSheet("font-size: 12px; color: #9CA3AF;")
            lbl_desc.setWordWrap(True)
            info_layout.addWidget(lbl_name)
            info_layout.addWidget(lbl_desc)
            card_layout.addLayout(info_layout, stretch=1)

            # State switch / checkbox
            is_applied = self.manager.is_tweak_applied(tweak)
            chk = QCheckBox("Himoyalangan" if is_applied else "O'chiq (Standart)")
            chk.setChecked(is_applied)
            chk.setCursor(Qt.PointingHandCursor)
            chk.setStyleSheet("""
                QCheckBox {
                    color: #10B981;
                    font-weight: 600;
                    font-size: 13px;
                }
            """)
            chk.toggled.connect(lambda checked, t=tweak, c=chk: self._on_tweak_toggled(t, checked, c))
            card_layout.addWidget(chk)

            self.tweaks_container.addWidget(card)

        self.tweaks_container.addStretch()

    def _on_tweak_toggled(self, tweak: PrivacyTweak, enable: bool, chk: QCheckBox) -> None:
        if tweak.requires_admin and not is_user_admin():
            reply = QMessageBox.question(
                self,
                tr("msg_admin_required", "Administrator huquqi talab qilinadi"),
                tr("msg_admin_restart_prompt", f"'{tweak.name}' parametrini o'zgartirish uchun Administrator huquqi zarur.\nCleanGuard ni Administrator rejimida qayta ishga tushirilsinmi?"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            # Revert checkbox state
            chk.blockSignals(True)
            chk.setChecked(not enable)
            chk.blockSignals(False)
            if reply == QMessageBox.Yes:
                request_elevation()
            return

        ok, msg = self.manager.apply_tweak(tweak, enable)
        if ok:
            chk.setText("Himoyalangan" if enable else "O'chiq (Standart)")
        else:
            chk.blockSignals(True)
            chk.setChecked(not enable)
            chk.blockSignals(False)
            QMessageBox.warning(self, tr("msg_error_title", "Xatolik"), f"{tr('msg_error_title', 'Xatolik')}:\n{msg}")

    def _refresh_bloatware_list(self) -> None:
        self.bloatware_apps = self.manager.get_bloatware_status()
        self.table_bloatware.setRowCount(len(self.bloatware_apps))

        for row, app in enumerate(self.bloatware_apps):
            # Name
            self.table_bloatware.setItem(row, 0, QTableWidgetItem(f"  {app.name}"))

            # Category
            item_cat = QTableWidgetItem(app.category)
            item_cat.setTextAlignment(Qt.AlignCenter)
            self.table_bloatware.setItem(row, 1, item_cat)

            # Status
            if app.installed:
                item_stat = QTableWidgetItem("⚠️ O'rnatilgan")
                item_stat.setForeground(Qt.yellow)
            else:
                item_stat = QTableWidgetItem("✅ Mavjud emas")
                item_stat.setForeground(Qt.gray)
            item_stat.setTextAlignment(Qt.AlignCenter)
            self.table_bloatware.setItem(row, 2, item_stat)

            # Action button
            if app.installed:
                btn_remove = QPushButton("🗑️ O'chirish")
                btn_remove.setStyleSheet("""
                    QPushButton {
                        background-color: #EF4444;
                        color: white;
                        font-weight: 600;
                        font-size: 11px;
                        border-radius: 4px;
                        padding: 4px 8px;
                    }
                    QPushButton:hover {
                        background-color: #DC2626;
                    }
                """)
                btn_remove.setCursor(Qt.PointingHandCursor)
                btn_remove.clicked.connect(lambda _, a=app: self._on_remove_bloatware_clicked(a))
                self.table_bloatware.setCellWidget(row, 3, btn_remove)
            else:
                lbl_clean = QLabel("Toza")
                lbl_clean.setAlignment(Qt.AlignCenter)
                lbl_clean.setStyleSheet("color: #6B7280; font-size: 11px;")
                self.table_bloatware.setCellWidget(row, 3, lbl_clean)

    def _on_remove_bloatware_clicked(self, app: BloatwareApp) -> None:
        reply = QMessageBox.question(
            self,
            tr("msg_confirm_title", "Ilovani o'chirish"),
            tr("msg_bloatware_remove_confirm", app=app.name, pkg=app.package_pattern),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply == QMessageBox.Yes:
            ok, msg = self.manager.remove_bloatware(app)
            if ok:
                QMessageBox.information(self, tr("msg_success_title", "Muvaffaqiyatli"), msg)
                self._refresh_bloatware_list()
            else:
                QMessageBox.warning(self, tr("msg_error_title", "Xatolik"), msg)

    def retranslate_ui(self, lang_code: str = "") -> None:
        """Dynamically update labels on language switch."""
        self.lbl_title.setText("🛠️ " + tr("nav_tweaks", "Windows optimizatsiya va Maxfiylik"))
        self.lbl_subtitle.setText(tr("tweaks_subtitle", "Windows 10/11 standart ilovalarini (Bloatware) va telemetriya xizmatlarini boshqaring"))
        self.btn_refresh.setText("🔄 " + tr("btn_refresh", "Yangilash"))
        self.tabs.setTabText(0, tr("tweaks_tab_privacy", "🛡️ Maxfiylik va Telemetriya (Privacy)"))
        self.tabs.setTabText(1, tr("tweaks_tab_bloatware", "📦 Standart UWP Ilovalar (Bloatware)"))
        self.table_bloatware.setHorizontalHeaderLabels([
            tr("tbl_app_name", "Ilova nomi"),
            tr("tbl_category", "Kategoriya"),
            tr("tbl_status", "Holati"),
            tr("tbl_action", "Amal"),
        ])
