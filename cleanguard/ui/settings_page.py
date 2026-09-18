"""
Settings Page: Configuration of language, safety rules, scanner categories, and custom exclusions.
"""

import logging
from typing import Dict
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QCheckBox,
    QFrame,
    QSpinBox,
    QPushButton,
    QListWidget,
    QFileDialog,
    QScrollArea,
    QGridLayout,
    QMessageBox,
)
from PyQt5.QtCore import Qt
from cleanguard.core.config import ConfigManager
from cleanguard.localization import get_localization, tr, SUPPORTED_LANGUAGES
from cleanguard.security.protected_paths import ProtectedPathRegistry
from cleanguard.utils.logging import open_log_folder, set_log_level, get_current_log_level
from cleanguard.ui.widgets.log_viewer_dialog import LogViewerDialog
from cleanguard.services.export_service import export_diagnostic_package
from cleanguard.windows.scheduler import AutoCareScheduler
from cleanguard.utils.formatting import format_bytes



class SettingsPage(QWidget):
    """Comprehensive user configuration screen."""

    CATEGORIES = [
        ("temp_files", "category_temp_files"),
        ("app_cache", "category_app_cache"),
        ("browser_cache", "category_browser_cache"),
        ("system_logs", "category_system_logs"),
        ("crash_dumps", "category_crash_dumps"),
        ("thumbnail_cache", "category_thumbnail_cache"),
        ("recycle_bin", "category_recycle_bin"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = ConfigManager()
        self.loc = get_localization()
        self.path_registry = ProtectedPathRegistry(self.config)
        self.category_checkboxes: Dict[str, QCheckBox] = {}
        self._init_ui()

    def _init_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for clean layout on smaller screens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        # Page Title
        self.lbl_title = QLabel(tr("nav_settings"))
        self.lbl_title.setStyleSheet("font-size: 26px; font-weight: 700; color: #F9FAFB;")
        layout.addWidget(self.lbl_title)

        # 1. General Preferences Card
        self.card_general = QFrame()
        self.card_general.setObjectName("SurfaceCard")
        gen_layout = QVBoxLayout(self.card_general)
        gen_layout.setContentsMargins(24, 20, 24, 20)
        gen_layout.setSpacing(16)

        # Language row
        lang_row = QHBoxLayout()
        self.lbl_lang = QLabel(tr("settings_app_language"))
        self.lbl_lang.setStyleSheet("font-size: 14px; font-weight: 500; color: #F9FAFB;")
        self.combo_lang = QComboBox()
        for code, name in SUPPORTED_LANGUAGES.items():
            self.combo_lang.addItem(name, code)

        cur_lang = self.config.get("language", "uz")
        idx = list(SUPPORTED_LANGUAGES.keys()).index(cur_lang) if cur_lang in SUPPORTED_LANGUAGES else 0
        self.combo_lang.setCurrentIndex(idx)
        self.combo_lang.currentIndexChanged.connect(self._on_language_changed)

        lang_row.addWidget(self.lbl_lang)
        lang_row.addStretch()
        lang_row.addWidget(self.combo_lang)
        gen_layout.addLayout(lang_row)

        # Confirm before cleanup
        self.chk_confirm = QCheckBox(tr("settings_confirm_cleanup"))
        self.chk_confirm.setChecked(self.config.get("confirm_before_cleanup", True))
        self.chk_confirm.stateChanged.connect(
            lambda s: self.config.set("confirm_before_cleanup", s == 2)
        )
        gen_layout.addWidget(self.chk_confirm)

        # Auto scan on startup
        self.chk_auto_scan = QCheckBox(tr("settings_auto_scan"))
        self.chk_auto_scan.setChecked(self.config.get("auto_scan_on_startup", False))
        self.chk_auto_scan.stateChanged.connect(
            lambda s: self.config.set("auto_scan_on_startup", s == 2)
        )
        gen_layout.addWidget(self.chk_auto_scan)

        # Minimize to tray
        self.chk_tray = QCheckBox(tr("settings_minimize_tray"))
        self.chk_tray.setChecked(self.config.get("minimize_to_tray", False))
        self.chk_tray.stateChanged.connect(
            lambda s: self.config.set("minimize_to_tray", s == 2)
        )
        gen_layout.addWidget(self.chk_tray)

        # Smart PyInstaller Cleanup
        self.chk_pyinstaller = QCheckBox(tr("rule_pyinstaller_title"))
        self.chk_pyinstaller.setToolTip(tr("rule_pyinstaller_desc"))
        self.chk_pyinstaller.setChecked(self.config.get("smart_pyinstaller_cleanup", True))
        self.chk_pyinstaller.stateChanged.connect(
            lambda s: self.config.set("smart_pyinstaller_cleanup", s == 2)
        )
        gen_layout.addWidget(self.chk_pyinstaller)

        # Minimum File Age
        age_row = QHBoxLayout()
        self.lbl_age = QLabel(tr("settings_min_file_age"))
        self.lbl_age.setStyleSheet("font-size: 14px; color: #F9FAFB;")
        self.spin_age = QSpinBox()
        self.spin_age.setRange(0, 168)
        self.spin_age.setValue(int(self.config.get("min_file_age_hours", 24)))
        self.spin_age.valueChanged.connect(
            lambda val: self.config.set("min_file_age_hours", val)
        )
        age_row.addWidget(self.lbl_age)
        age_row.addStretch()
        age_row.addWidget(self.spin_age)
        gen_layout.addLayout(age_row)

        layout.addWidget(self.card_general)

        # 2. Enabled Scanner Categories Card
        self.card_categories = QFrame()
        self.card_categories.setObjectName("SurfaceCard")
        cat_layout = QVBoxLayout(self.card_categories)
        cat_layout.setContentsMargins(24, 20, 24, 20)
        cat_layout.setSpacing(14)

        self.lbl_cat_title = QLabel(tr("settings_scanner_categories"))
        self.lbl_cat_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #10B981;")
        cat_layout.addWidget(self.lbl_cat_title)

        grid = QGridLayout()
        grid.setSpacing(12)

        enabled_cats = set(self.config.get("enabled_categories", []))
        for i, (cat_id, tr_key) in enumerate(self.CATEGORIES):
            chk = QCheckBox(tr(tr_key))
            chk.setChecked(cat_id in enabled_cats)
            chk.stateChanged.connect(self._on_category_toggled)
            self.category_checkboxes[cat_id] = chk
            row = i // 2
            col = i % 2
            grid.addWidget(chk, row, col)

        cat_layout.addLayout(grid)
        layout.addWidget(self.card_categories)

        # 3. Custom Protected Directories (Exclusions) Card
        self.card_protected = QFrame()
        self.card_protected.setObjectName("SurfaceCard")
        prot_layout = QVBoxLayout(self.card_protected)
        prot_layout.setContentsMargins(24, 20, 24, 20)
        prot_layout.setSpacing(14)

        self.lbl_prot_title = QLabel(tr("settings_protected_paths"))
        self.lbl_prot_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #10B981;")
        prot_layout.addWidget(self.lbl_prot_title)

        self.list_protected = QListWidget()
        self.list_protected.setFixedHeight(120)
        self.list_protected.setStyleSheet("""
            QListWidget {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 6px;
                color: #E5E7EB;
            }
        """)
        self._reload_protected_list()
        prot_layout.addWidget(self.list_protected)

        prot_btn_row = QHBoxLayout()
        self.btn_add_path = QPushButton(f"  + {tr('settings_add_path')}  ")
        self.btn_add_path.setObjectName("SecondaryButton")
        self.btn_add_path.setCursor(Qt.PointingHandCursor)
        self.btn_add_path.clicked.connect(self._on_add_protected_path)
        prot_btn_row.addWidget(self.btn_add_path)

        self.btn_remove_path = QPushButton(f"  - {tr('settings_remove_path')}  ")
        self.btn_remove_path.setObjectName("SecondaryButton")
        self.btn_remove_path.setCursor(Qt.PointingHandCursor)
        self.btn_remove_path.clicked.connect(self._on_remove_protected_path)
        prot_btn_row.addWidget(self.btn_remove_path)

        prot_btn_row.addStretch()
        prot_layout.addLayout(prot_btn_row)

        layout.addWidget(self.card_protected)

        # 4. Diagnostics & System Logs Card
        self.card_diagnostics = QFrame()
        self.card_diagnostics.setObjectName("SurfaceCard")
        diag_layout = QVBoxLayout(self.card_diagnostics)
        diag_layout.setContentsMargins(24, 20, 24, 20)
        diag_layout.setSpacing(14)

        self.lbl_diag_title = QLabel(tr("settings_diagnostics_title"))
        self.lbl_diag_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #10B981;")
        diag_layout.addWidget(self.lbl_diag_title)

        self.lbl_diag_desc = QLabel(tr("settings_diagnostics_desc"))
        self.lbl_diag_desc.setStyleSheet("font-size: 13px; color: #9CA3AF;")
        self.lbl_diag_desc.setWordWrap(True)
        diag_layout.addWidget(self.lbl_diag_desc)

        # Log Level row
        level_row = QHBoxLayout()
        self.lbl_log_level = QLabel(tr("settings_log_level"))
        self.lbl_log_level.setStyleSheet("font-size: 14px; color: #F9FAFB;")
        level_row.addWidget(self.lbl_log_level)
        level_row.addStretch()

        self.combo_log_level = QComboBox()
        self.combo_log_level.addItem("DEBUG (Batafsil / Texnik)", logging.DEBUG)
        self.combo_log_level.addItem("INFO (Standart)", logging.INFO)
        self.combo_log_level.addItem("WARNING (Ogohlantirishlar)", logging.WARNING)
        self.combo_log_level.addItem("ERROR (Faqat xatolar)", logging.ERROR)

        current_lvl = get_current_log_level()
        lvl_map = {logging.DEBUG: 0, logging.INFO: 1, logging.WARNING: 2, logging.ERROR: 3}
        self.combo_log_level.setCurrentIndex(lvl_map.get(current_lvl, 1))
        self.combo_log_level.currentIndexChanged.connect(self._on_log_level_changed)
        level_row.addWidget(self.combo_log_level)
        diag_layout.addLayout(level_row)

        # Actions buttons row
        diag_btn_row = QHBoxLayout()
        diag_btn_row.setSpacing(12)

        self.btn_view_logs = QPushButton(f"  📋  {tr('btn_view_live_logs')}  ")
        self.btn_view_logs.setObjectName("PrimaryButton")
        self.btn_view_logs.setCursor(Qt.PointingHandCursor)
        self.btn_view_logs.clicked.connect(self._on_view_logs_clicked)
        diag_btn_row.addWidget(self.btn_view_logs)

        self.btn_open_folder = QPushButton(f"  📂  {tr('btn_open_logs_folder')}  ")
        self.btn_open_folder.setObjectName("SecondaryButton")
        self.btn_open_folder.setCursor(Qt.PointingHandCursor)
        self.btn_open_folder.clicked.connect(open_log_folder)
        diag_btn_row.addWidget(self.btn_open_folder)

        self.btn_export_diag = QPushButton(f"  📦  {tr('btn_export_diagnostics')}  ")
        self.btn_export_diag.setObjectName("SecondaryButton")
        self.btn_export_diag.setCursor(Qt.PointingHandCursor)
        self.btn_export_diag.clicked.connect(self._on_export_diagnostic_package)
        diag_btn_row.addWidget(self.btn_export_diag)

        diag_btn_row.addStretch()
        diag_layout.addLayout(diag_btn_row)

        layout.addWidget(self.card_diagnostics)

        # 5. Scheduled Auto-Care Card
        self.card_autocare = QFrame()
        self.card_autocare.setObjectName("SurfaceCard")
        auto_layout = QVBoxLayout(self.card_autocare)
        auto_layout.setContentsMargins(24, 20, 24, 20)
        auto_layout.setSpacing(14)

        self.lbl_auto_title = QLabel("⏰ " + tr("autocare_title", "Avtomatik parvarish (Scheduled Auto-Care)"))
        self.lbl_auto_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #10B981;")
        auto_layout.addWidget(self.lbl_auto_title)

        self.lbl_auto_desc = QLabel(
            tr("autocare_desc", "Windows Task Scheduler orqali kompyuterni muntazam fonda xavfsiz tozalash.")
        )
        self.lbl_auto_desc.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        auto_layout.addWidget(self.lbl_auto_desc)

        sched_row = QHBoxLayout()
        self.chk_autocare = QCheckBox(tr("autocare_enable", "Avtomatik fonda tozalashni yoqish"))
        self.chk_autocare.setCursor(Qt.PointingHandCursor)
        self.combo_schedule = QComboBox()
        self.combo_schedule.addItem(tr("autocare_weekly", "Har hafta (Yakshanba 12:00)"), ("WEEKLY", "SUN", "12:00"))
        self.combo_schedule.addItem(tr("autocare_daily", "Har kuni (12:00)"), ("DAILY", "", "12:00"))

        sched_row.addWidget(self.chk_autocare)
        sched_row.addSpacing(16)
        sched_row.addWidget(self.combo_schedule)
        sched_row.addStretch()
        auto_layout.addLayout(sched_row)

        action_row = QHBoxLayout()
        self.lbl_autocare_status = QLabel("Holat: Tekshirilmoqda...")
        self.lbl_autocare_status.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        action_row.addWidget(self.lbl_autocare_status)
        action_row.addStretch()

        self.btn_test_autocare = QPushButton("⚡ " + tr("btn_test_clean", "Hozir sinab ko'rish"))
        self.btn_test_autocare.setCursor(Qt.PointingHandCursor)
        self.btn_test_autocare.clicked.connect(self._on_test_autocare_clicked)
        action_row.addWidget(self.btn_test_autocare)
        auto_layout.addLayout(action_row)

        # Wire signals
        self.chk_autocare.toggled.connect(self._on_autocare_toggled)
        self.combo_schedule.currentIndexChanged.connect(self._on_autocare_schedule_changed)

        layout.addWidget(self.card_autocare)
        self._refresh_autocare_status()

        layout.addStretch()

        scroll.setWidget(content_widget)
        outer_layout.addWidget(scroll)

    def _on_log_level_changed(self, index: int) -> None:
        level = self.combo_log_level.itemData(index)
        if level is not None:
            set_log_level(level)
            self.config.set("log_level", level)

    def _on_view_logs_clicked(self) -> None:
        dialog = LogViewerDialog(self)
        dialog.exec_()

    def _on_export_diagnostic_package(self) -> None:
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Diagnostic Package",
            "cleanguard_diagnostic_report.zip",
            "Zip Archives (*.zip);;All Files (*)",
        )
        if save_path:
            success = export_diagnostic_package(save_path)
            if success:
                QMessageBox.information(
                    self,
                    tr("diag_export_success_title"),
                    tr("diag_export_success_msg").format(path=save_path),
                )
            else:
                QMessageBox.warning(
                    self,
                    "Export Failed",
                    f"Could not generate diagnostic package at {save_path}",
                )

    def _reload_protected_list(self) -> None:
        self.list_protected.clear()
        custom_paths = self.config.get("custom_protected_paths", [])
        for p in custom_paths:
            self.list_protected.addItem(p)

    def _on_add_protected_path(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Directory to Protect")
        if folder:
            self.path_registry.add_custom_protected_path(folder)
            self._reload_protected_list()

    def _on_remove_protected_path(self) -> None:
        current_item = self.list_protected.currentItem()
        if current_item:
            self.path_registry.remove_custom_protected_path(current_item.text())
            self._reload_protected_list()

    def _on_category_toggled(self) -> None:
        enabled = [
            cat_id
            for cat_id, chk in self.category_checkboxes.items()
            if chk.isChecked()
        ]
        self.config.set("enabled_categories", enabled)

    def _on_language_changed(self, index: int) -> None:
        lang_code = self.combo_lang.itemData(index)
        self.loc.set_language(lang_code)

    def retranslate_ui(self, lang_code: str = "") -> None:
        """Dynamically update all text labels on language change."""
        self.lbl_title.setText(tr("nav_settings"))
        self.lbl_lang.setText(tr("settings_app_language"))
        self.chk_confirm.setText(tr("settings_confirm_cleanup"))
        self.chk_auto_scan.setText(tr("settings_auto_scan"))
        self.chk_tray.setText(tr("settings_minimize_tray"))
        self.lbl_age.setText(tr("settings_min_file_age"))
        self.lbl_cat_title.setText(tr("settings_scanner_categories"))
        self.lbl_prot_title.setText(tr("settings_protected_paths"))
        self.btn_add_path.setText(f"  + {tr('settings_add_path')}  ")
        self.btn_remove_path.setText(f"  - {tr('settings_remove_path')}  ")

        self.lbl_diag_title.setText(tr("settings_diagnostics_title"))
        self.lbl_diag_desc.setText(tr("settings_diagnostics_desc"))
        self.lbl_log_level.setText(tr("settings_log_level"))
        self.btn_view_logs.setText(f"  📋  {tr('btn_view_live_logs')}  ")
        self.btn_open_folder.setText(f"  📂  {tr('btn_open_logs_folder')}  ")
        self.btn_export_diag.setText(f"  📦  {tr('btn_export_diagnostics')}  ")

        for cat_id, tr_key in self.CATEGORIES:
            if cat_id in self.category_checkboxes:
                self.category_checkboxes[cat_id].setText(tr(tr_key))

        self.lbl_auto_title.setText("⏰ " + tr("autocare_title", "Avtomatik parvarish (Scheduled Auto-Care)"))
        self.lbl_auto_desc.setText(tr("autocare_desc", "Windows Task Scheduler orqali kompyuterni muntazam fonda xavfsiz tozalash."))
        self.chk_autocare.setText(tr("autocare_enable", "Avtomatik fonda tozalashni yoqish"))
        self.btn_test_autocare.setText("⚡ " + tr("btn_test_clean", "Hozir sinab ko'rish"))
        if hasattr(self, "combo_schedule") and self.combo_schedule.count() >= 2:
            self.combo_schedule.setItemText(0, tr("autocare_weekly", "Har hafta (Yakshanba 12:00)"))
            self.combo_schedule.setItemText(1, tr("autocare_daily", "Har kuni (12:00)"))

    def _refresh_autocare_status(self) -> None:
        try:
            is_sched, info = AutoCareScheduler.is_scheduled()
        except Exception:
            is_sched, info = False, None

        self.chk_autocare.blockSignals(True)
        self.chk_autocare.setChecked(is_sched)
        self.chk_autocare.blockSignals(False)
        if is_sched:
            self.lbl_autocare_status.setText(f"Holat: Faol ({info})")
            self.lbl_autocare_status.setStyleSheet("color: #10B981; font-size: 12px; font-weight: 600;")
        else:
            self.lbl_autocare_status.setText("Holat: O'chiq")
            self.lbl_autocare_status.setStyleSheet("color: #9CA3AF; font-size: 12px;")

    def _on_autocare_toggled(self, checked: bool) -> None:
        if checked:
            data = self.combo_schedule.currentData()
            freq, day, time_str = data if data else ("WEEKLY", "SUN", "12:00")
            ok, msg = AutoCareScheduler.enable_schedule(freq, day, time_str)
            if not ok:
                self.chk_autocare.blockSignals(True)
                self.chk_autocare.setChecked(False)
                self.chk_autocare.blockSignals(False)
                QMessageBox.warning(self, "Xatolik", msg)
        else:
            ok, msg = AutoCareScheduler.disable_schedule()
            if not ok:
                QMessageBox.warning(self, "Xatolik", msg)
        self._refresh_autocare_status()

    def _on_autocare_schedule_changed(self) -> None:
        if self.chk_autocare.isChecked():
            self._on_autocare_toggled(True)

    def _on_test_autocare_clicked(self) -> None:
        try:
            files, recovered = AutoCareScheduler.run_auto_clean_now()
            QMessageBox.information(
                self,
                "Auto-Care sinovi",
                f"Sinov muvaffaqiyatli yakunlandi!\nO'chirilgan fayllar: {files} ta\nBo'shatilgan joy: {format_bytes(recovered)}",
            )
        except Exception as ex:
            QMessageBox.warning(self, "Xatolik", f"Auto-Care sinovida xatolik: {ex}")

