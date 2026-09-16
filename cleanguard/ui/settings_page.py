"""
Settings Page: Configuration of language, safety rules, and custom exclusions.
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QCheckBox,
    QFrame,
    QSpinBox,
)
from cleanguard.core.config import ConfigManager
from cleanguard.localization import get_localization, tr, SUPPORTED_LANGUAGES


class SettingsPage(QWidget):
    """User configuration screen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = ConfigManager()
        self.loc = get_localization()
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        self.lbl_title = QLabel(tr("nav_settings"))
        self.lbl_title.setStyleSheet("font-size: 26px; font-weight: 700; color: #F9FAFB;")
        layout.addWidget(self.lbl_title)

        # Settings Card
        card = QFrame()
        card.setObjectName("SurfaceCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(18)

        # 1. Language Row
        lang_row = QHBoxLayout()
        lbl_lang = QLabel("Application Language:")
        lbl_lang.setStyleSheet("font-size: 14px; font-weight: 500;")
        self.combo_lang = QComboBox()
        for code, name in SUPPORTED_LANGUAGES.items():
            self.combo_lang.addItem(name, code)

        cur_lang = self.config.get("language", "uz")
        idx = list(SUPPORTED_LANGUAGES.keys()).index(cur_lang) if cur_lang in SUPPORTED_LANGUAGES else 0
        self.combo_lang.setCurrentIndex(idx)
        self.combo_lang.currentIndexChanged.connect(self._on_language_changed)

        lang_row.addWidget(lbl_lang)
        lang_row.addStretch()
        lang_row.addWidget(self.combo_lang)
        card_layout.addLayout(lang_row)

        # 2. Confirm before cleanup
        self.chk_confirm = QCheckBox("Show confirmation dialog before executing cleanup")
        self.chk_confirm.setChecked(self.config.get("confirm_before_cleanup", True))
        self.chk_confirm.stateChanged.connect(
            lambda s: self.config.set("confirm_before_cleanup", s == 2)
        )
        card_layout.addWidget(self.chk_confirm)

        # 3. Minimum Temp File Age
        age_row = QHBoxLayout()
        lbl_age = QLabel("Minimum file age before cleanup (hours):")
        lbl_age.setStyleSheet("font-size: 14px;")
        self.spin_age = QSpinBox()
        self.spin_age.setRange(0, 168)  # up to 7 days
        self.spin_age.setValue(int(self.config.get("min_file_age_hours", 24)))
        self.spin_age.valueChanged.connect(
            lambda val: self.config.set("min_file_age_hours", val)
        )
        age_row.addWidget(lbl_age)
        age_row.addStretch()
        age_row.addWidget(self.spin_age)
        card_layout.addLayout(age_row)

        layout.addWidget(card)
        layout.addStretch()

    def _on_language_changed(self, index: int) -> None:
        lang_code = self.combo_lang.itemData(index)
        self.loc.set_language(lang_code)
