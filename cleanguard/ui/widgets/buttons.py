"""
Specialized high-tech UI buttons: Circular pulsing SCAN button and glowing controls.
"""

from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from cleanguard.localization import tr


class CircularScanButton(QPushButton):
    """
    Futuristic circular SCAN button inspired by IObit Advanced SystemCare.
    Features glowing cyber borders, radial gradient depth, and dual-line typography.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CircularScanButton")
        self.setFixedSize(140, 140)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignCenter)

        self.lbl_main = QLabel("SCAN")
        self.lbl_main.setAlignment(Qt.AlignCenter)
        self.lbl_main.setStyleSheet(
            "color: #FFFFFF; font-size: 22px; font-weight: 900; letter-spacing: 2px; background: transparent;"
        )
        self.lbl_main.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.lbl_sub = QLabel(tr("care_scan_sub"))
        self.lbl_sub.setAlignment(Qt.AlignCenter)
        self.lbl_sub.setStyleSheet(
            "color: #06B6D4; font-size: 11px; font-weight: 700; letter-spacing: 1.5px; background: transparent;"
        )
        self.lbl_sub.setAttribute(Qt.WA_TransparentForMouseEvents)

        layout.addWidget(self.lbl_main)
        layout.addWidget(self.lbl_sub)

    def retranslate_ui(self) -> None:
        self.lbl_sub.setText(tr("care_scan_sub"))
