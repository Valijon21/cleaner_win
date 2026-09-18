"""
Tweaks Page: Windows 10/11 Bloatware Remover & Telemetry Privacy Tweaker UI.
"""

from typing import List, Optional
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
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from cleanguard.windows.tweaks import TweaksManager, PrivacyTweak, BloatwareApp
from cleanguard.windows.updates import WindowsUpdateCleaner
from cleanguard.windows.privileges import is_user_admin, request_elevation
from cleanguard.localization import tr
from cleanguard.utils.formatting import format_bytes
from cleanguard.utils.logging import get_logger

logger = get_logger("ui.tweaks")


class BloatwareScanWorker(QThread):
    """Asynchronous background worker for scanning AppX bloatware packages."""
    finished = pyqtSignal(list)

    def __init__(self, manager: TweaksManager, parent=None):
        super().__init__(parent)
        self.manager = manager

    def run(self):
        apps = self.manager.get_bloatware_status()
        self.finished.emit(apps)


class DismCleanupWorker(QThread):
    """Asynchronous worker for executing DISM Component Store cleanup."""
    finished = pyqtSignal(bool, str)

    def __init__(self, cleaner: WindowsUpdateCleaner, parent=None):
        super().__init__(parent)
        self.cleaner = cleaner

    def run(self):
        success, message = self.cleaner.run_dism_component_cleanup()
        self.finished.emit(success, message)


class TweaksPage(QWidget):
    """Modern interface for managing Windows bloatware and privacy/telemetry settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = TweaksManager()
        self.update_cleaner = WindowsUpdateCleaner()
        self.bloatware_apps: List[BloatwareApp] = []
        self._loaded: bool = False
        self._bloatware_worker: Optional[BloatwareScanWorker] = None
        self._dism_worker: Optional[DismCleanupWorker] = None
        self._init_ui()

    def lazy_load(self) -> None:
        """Query tweaks and bloatware on demand when page is first activated."""
        if not self._loaded:
            self.refresh_all()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.lazy_load()

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

        # Tabs: 1) Privacy & Telemetry  2) Bloatware Apps  3) Windows Update & WinSxS
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

        # Tab 3: Windows Update & WinSxS
        self.tab_updates = QWidget()
        self._init_updates_tab()
        self.tabs.addTab(self.tab_updates, tr("tweaks_tab_updates", "🔄 Windows Update va WinSxS"))

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

    def _init_updates_tab(self) -> None:
        u_layout = QVBoxLayout(self.tab_updates)
        u_layout.setContentsMargins(20, 20, 20, 20)
        u_layout.setSpacing(16)

        # Card 1: SoftwareDistribution Download Cache
        card_update = QFrame()
        card_update.setStyleSheet("""
            QFrame {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        u1_layout = QVBoxLayout(card_update)
        u1_layout.setSpacing(10)

        self.lbl_upd_cache_title = QLabel("💾 " + tr("updates_cache_title", "Windows Update yuklab olish keshi"))
        self.lbl_upd_cache_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #F9FAFB;")
        u1_layout.addWidget(self.lbl_upd_cache_title)

        self.lbl_upd_cache_desc = QLabel(tr("updates_cache_desc", "SoftwareDistribution\\Download papkasida saqlanuvchi vaqtinchalik yangilanish o'rnatuvchilari. Yangilanishlar o'rnatilgach xavfsiz tozalash mumkin."))
        self.lbl_upd_cache_desc.setStyleSheet("font-size: 12px; color: #9CA3AF;")
        self.lbl_upd_cache_desc.setWordWrap(True)
        u1_layout.addWidget(self.lbl_upd_cache_desc)

        row_upd = QHBoxLayout()
        self.lbl_upd_size = QLabel(f"{tr('table_col_size', 'Hajmi')}: ...")
        self.lbl_upd_size.setStyleSheet("font-size: 13px; font-weight: 600; color: #10B981;")
        row_upd.addWidget(self.lbl_upd_size)
        row_upd.addStretch()

        self.btn_clean_upd = QPushButton("🧹 " + tr("btn_clean_update_cache", "Update keshini tozalash"))
        self.btn_clean_upd.setCursor(Qt.PointingHandCursor)
        self.btn_clean_upd.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                font-weight: 600;
                font-size: 12px;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.btn_clean_upd.clicked.connect(self._on_clean_update_cache_clicked)
        row_upd.addWidget(self.btn_clean_upd)
        u1_layout.addLayout(row_upd)

        u_layout.addWidget(card_update)

        # Card 2: WinSxS Component Store (DISM)
        card_dism = QFrame()
        card_dism.setStyleSheet("""
            QFrame {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        u2_layout = QVBoxLayout(card_dism)
        u2_layout.setSpacing(10)

        self.lbl_dism_title = QLabel("🚀 " + tr("dism_title", "WinSxS Component Store tozalash (DISM)"))
        self.lbl_dism_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #F9FAFB;")
        u2_layout.addWidget(self.lbl_dism_title)

        self.lbl_dism_desc = QLabel(tr("dism_desc", "Eski va o'rniga yangisi kelgan Windows tizim komponentlarini Microsoft DISM rasmiy vositasi orqali tozalaydi. 10-25+ GB joy bo'shatishi mumkin."))
        self.lbl_dism_desc.setStyleSheet("font-size: 12px; color: #9CA3AF;")
        self.lbl_dism_desc.setWordWrap(True)
        u2_layout.addWidget(self.lbl_dism_desc)

        row_dism = QHBoxLayout()
        self.lbl_dism_status = QLabel("Windows DISM: Tayyor")
        self.lbl_dism_status.setStyleSheet("font-size: 13px; color: #D1D5DB;")
        row_dism.addWidget(self.lbl_dism_status)
        row_dism.addStretch()

        self.btn_run_dism = QPushButton("⚡ " + tr("btn_run_dism", "Chuqur komponent tozalashni boshlash"))
        self.btn_run_dism.setCursor(Qt.PointingHandCursor)
        self.btn_run_dism.setStyleSheet("""
            QPushButton {
                background-color: #0284C7;
                color: white;
                font-weight: 600;
                font-size: 12px;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #0369A1;
            }
        """)
        self.btn_run_dism.clicked.connect(self._on_run_dism_clicked)
        row_dism.addWidget(self.btn_run_dism)
        u2_layout.addLayout(row_dism)

        u_layout.addWidget(card_dism)
        u_layout.addStretch()

    def refresh_all(self) -> None:
        self._loaded = True
        self._refresh_privacy_tweaks()
        self._refresh_bloatware_list()
        self._refresh_updates_status()

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
        if self._bloatware_worker and self._bloatware_worker.isRunning():
            return

        if self.table_bloatware.rowCount() == 0:
            self.table_bloatware.setRowCount(1)
            item_loading = QTableWidgetItem(f"  {tr('loading_bloatware', '⏳ Windows AppX paketlari tekshirilmoqda...')}")
            self.table_bloatware.setItem(0, 0, item_loading)

        self._bloatware_worker = BloatwareScanWorker(self.manager, self)
        self._bloatware_worker.finished.connect(self._on_bloatware_scanned)
        self._bloatware_worker.start()

    def _on_bloatware_scanned(self, apps: List[BloatwareApp]) -> None:
        self.bloatware_apps = apps
        self.table_bloatware.setUpdatesEnabled(False)
        try:
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
        finally:
            self.table_bloatware.setUpdatesEnabled(True)

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

    def _refresh_updates_status(self) -> None:
        try:
            sz = self.update_cleaner.get_cache_size()
            self.lbl_upd_size.setText(f"{tr('table_col_size', 'Hajmi')}: {format_bytes(sz)}")
        except Exception as ex:
            logger.debug(f"Failed to query update cache size: {ex}")

    def _on_clean_update_cache_clicked(self) -> None:
        ok, reclaimed, msg = self.update_cleaner.clean_update_download_cache()
        self._refresh_updates_status()
        if ok:
            QMessageBox.information(
                self,
                tr("msg_success_title", "Muvaffaqiyatli"),
                tr("updates_cache_cleared", size=format_bytes(reclaimed)),
            )
        else:
            QMessageBox.warning(self, tr("msg_error_title", "Xatolik"), msg)

    def _on_run_dism_clicked(self) -> None:
        if not is_user_admin():
            reply = QMessageBox.question(
                self,
                tr("msg_admin_required", "Administrator huquqi talab qilinadi"),
                tr("msg_admin_restart_prompt", "DISM Component Store tozalash uchun Administrator huquqi zarur.\nCleanGuard ni Administrator rejimida qayta ishga tushirilsinmi?"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
                request_elevation()
            return

        if self._dism_worker and self._dism_worker.isRunning():
            return

        self.btn_run_dism.setEnabled(False)
        self.lbl_dism_status.setText("⏳ " + tr("dism_running", "DISM tozalanmoqda..."))
        self._dism_worker = DismCleanupWorker(self.update_cleaner, self)
        self._dism_worker.finished.connect(self._on_dism_finished)
        self._dism_worker.start()

    def _on_dism_finished(self, success: bool, message: str) -> None:
        self.btn_run_dism.setEnabled(True)
        self.lbl_dism_status.setText("Windows DISM: Tayyor")
        if success:
            QMessageBox.information(
                self,
                tr("msg_success_title", "Muvaffaqiyatli"),
                f"{tr('dism_complete', 'DISM tozalash muvaffaqiyatli yakunlandi!')}\n\n{message[:300]}",
            )
        else:
            QMessageBox.warning(
                self,
                tr("msg_error_title", "Xatolik"),
                f"{tr('msg_error_title', 'Xatolik')}:\n{message[:300]}",
            )

    def retranslate_ui(self, lang_code: str = "") -> None:
        """Dynamically update labels on language switch."""
        self.lbl_title.setText("🛠️ " + tr("nav_tweaks", "Windows optimizatsiya va Maxfiylik"))
        self.lbl_subtitle.setText(tr("tweaks_subtitle", "Windows 10/11 standart ilovalarini (Bloatware) va telemetriya xizmatlarini boshqaring"))
        self.btn_refresh.setText("🔄 " + tr("btn_refresh", "Yangilash"))
        self.tabs.setTabText(0, tr("tweaks_tab_privacy", "🛡️ Maxfiylik va Telemetriya (Privacy)"))
        self.tabs.setTabText(1, tr("tweaks_tab_bloatware", "📦 Standart UWP Ilovalar (Bloatware)"))
        self.tabs.setTabText(2, tr("tweaks_tab_updates", "🔄 Windows Update va WinSxS"))
        self.table_bloatware.setHorizontalHeaderLabels([
            tr("tbl_app_name", "Ilova nomi"),
            tr("tbl_category", "Kategoriya"),
            tr("tbl_status", "Holati"),
            tr("tbl_action", "Amal"),
        ])
        self.lbl_upd_cache_title.setText("💾 " + tr("updates_cache_title", "Windows Update yuklab olish keshi"))
        self.lbl_upd_cache_desc.setText(tr("updates_cache_desc", "SoftwareDistribution\\Download papkasida saqlanuvchi vaqtinchalik yangilanish o'rnatuvchilari. Yangilanishlar o'rnatilgach xavfsiz tozalash mumkin."))
        self.btn_clean_upd.setText("🧹 " + tr("btn_clean_update_cache", "Update keshini tozalash"))
        self.lbl_dism_title.setText("🚀 " + tr("dism_title", "WinSxS Component Store tozalash (DISM)"))
        self.lbl_dism_desc.setText(tr("dism_desc", "Eski va o'rniga yangisi kelgan Windows tizim komponentlarini Microsoft DISM rasmiy vositasi orqali tozalaydi. 10-25+ GB joy bo'shatishi mumkin."))
        self.btn_run_dism.setText("⚡ " + tr("btn_run_dism", "Chuqur komponent tozalashni boshlash"))
        self._refresh_updates_status()
