"""
About Page: Application details, licensing, and safety guarantees.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from cleanguard.app.version import (
    APP_DISPLAY_NAME,
    APP_VERSION,
    BUILD_NUMBER,
    COPYRIGHT,
    SUPPORTED_OS_LIST,
)
from cleanguard.localization import tr


class AboutPage(QWidget):
    """About & Product Information Screen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        self.lbl_title = QLabel(tr("nav_about"))
        self.lbl_title.setStyleSheet("font-size: 26px; font-weight: 700; color: #F9FAFB;")
        layout.addWidget(self.lbl_title)

        card = QFrame()
        card.setObjectName("SurfaceCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(14)

        lbl_name = QLabel(f"{APP_DISPLAY_NAME} v{APP_VERSION}")
        lbl_name.setStyleSheet("font-size: 20px; font-weight: 700; color: #10B981;")

        lbl_build = QLabel(f"Build: {BUILD_NUMBER} • Target Python 3.8+ Baseline")
        lbl_build.setStyleSheet("color: #9CA3AF; font-size: 13px;")

        self.lbl_desc = QLabel(
            tr(
                "about_description",
                "CleanGuard is a safety-first Windows cleanup and storage optimization utility.\n"
                "Engineered with strict non-bypassable safety gates to ensure zero loss of user documents\n"
                "or Windows system integrity.",
            )
        )
        self.lbl_desc.setStyleSheet("color: #D1D5DB; font-size: 14px; line-height: 1.5;")

        self.lbl_os_header = QLabel(tr("about_supported_os", "Supported Operating Systems:"))
        self.lbl_os_header.setStyleSheet("font-weight: 600; color: #F9FAFB; margin-top: 10px;")

        card_layout.addWidget(lbl_name)
        card_layout.addWidget(lbl_build)
        card_layout.addWidget(self.lbl_desc)
        card_layout.addWidget(self.lbl_os_header)

        for os_name in SUPPORTED_OS_LIST:
            lbl_os = QLabel(f"  ✓  {os_name}")
            lbl_os.setStyleSheet("color: #9CA3AF; font-size: 12px;")
            card_layout.addWidget(lbl_os)

        lbl_copy = QLabel(COPYRIGHT)
        lbl_copy.setStyleSheet("color: #6B7280; font-size: 11px; margin-top: 14px;")
        card_layout.addWidget(lbl_copy)

        layout.addWidget(card)
        layout.addStretch()

    def retranslate_ui(self) -> None:
        self.lbl_title.setText(tr("nav_about"))
        self.lbl_desc.setText(
            tr(
                "about_description",
                "CleanGuard is a safety-first Windows cleanup and storage optimization utility.\n"
                "Engineered with strict non-bypassable safety gates to ensure zero loss of user documents\n"
                "or Windows system integrity.",
            )
        )
        self.lbl_os_header.setText(tr("about_supported_os", "Supported Operating Systems:"))

