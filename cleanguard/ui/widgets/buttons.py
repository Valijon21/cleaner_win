"""
Specialized high-tech UI buttons: Circular pulsing SCAN button and glowing controls.
Inspired by IObit Advanced SystemCare Pro.
"""

from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QLabel
from PyQt5.QtGui import QPainter, QRadialGradient, QLinearGradient, QColor, QPen, QBrush
from PyQt5.QtCore import Qt, QPointF, QRectF
from cleanguard.localization import tr


class CircularScanButton(QPushButton):
    """
    Futuristic circular SCAN button inspired by IObit Advanced SystemCare.
    Features concentric cyber rings, radial depth, glowing accents, and dual-line typography.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CircularScanButton")
        self.setFixedSize(140, 140)
        self.setCursor(Qt.PointingHandCursor)

        self._is_hovered: bool = False
        self._is_pressed: bool = False

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

    def enterEvent(self, event) -> None:
        super().enterEvent(event)
        self._is_hovered = True
        self.lbl_sub.setStyleSheet(
            "color: #34D399; font-size: 11px; font-weight: 700; letter-spacing: 1.5px; background: transparent;"
        )
        self.update()

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)
        self._is_hovered = False
        self.lbl_sub.setStyleSheet(
            "color: #06B6D4; font-size: 11px; font-weight: 700; letter-spacing: 1.5px; background: transparent;"
        )
        self.update()

    def mousePressEvent(self, event) -> None:
        self._is_pressed = True
        self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._is_pressed = False
        self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        w = self.width()
        h = self.height()
        center = QPointF(w / 2.0, h / 2.0)

        # 1. Outer Ambient Glow Halo
        glow_radius = 67.0
        if self._is_pressed:
            halo_color = QColor(13, 148, 136, 120)
        elif self._is_hovered:
            halo_color = QColor(16, 185, 129, 90)
        else:
            halo_color = QColor(6, 182, 212, 50)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(halo_color))
        painter.drawEllipse(center, glow_radius, glow_radius)

        # 2. Outer Concentric Cyber Orbit Ring
        orbit_radius = 64.0
        if self._is_hovered:
            orbit_pen = QPen(QColor("#10B981"), 1.5, Qt.DashLine)
        else:
            orbit_pen = QPen(QColor(6, 182, 212, 160), 1.2, Qt.DashLine)
        painter.setPen(orbit_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center, orbit_radius, orbit_radius)

        # 3. Main Centerpiece Disc with Radial Depth
        disc_radius = 58.0
        radial = QRadialGradient(center, disc_radius)
        if self._is_pressed:
            radial.setColorAt(0.0, QColor("#0D9488"))
            radial.setColorAt(0.8, QColor("#042F2E"))
            radial.setColorAt(1.0, QColor("#064E3B"))
            border_color = QColor("#22D3EE")
        elif self._is_hovered:
            radial.setColorAt(0.0, QColor("#065F46"))
            radial.setColorAt(0.65, QColor("#0F172A"))
            radial.setColorAt(1.0, QColor("#064E3B"))
            border_color = QColor("#34D399")
        else:
            radial.setColorAt(0.0, QColor("#1E293B"))
            radial.setColorAt(0.7, QColor("#0F172A"))
            radial.setColorAt(1.0, QColor("#062335"))
            border_color = QColor("#06B6D4")

        painter.setPen(QPen(border_color, 2.5))
        painter.setBrush(QBrush(radial))
        painter.drawEllipse(center, disc_radius, disc_radius)

        # 4. Top Specular Glass Reflection Arc
        top_specular = QRadialGradient(center.x(), center.y() - 25, 45)
        top_specular.setColorAt(0.0, QColor(255, 255, 255, 45))
        top_specular.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(top_specular))
        specular_rect = QRectF(center.x() - 40.0, center.y() - 52.0, 80.0, 50.0)
        painter.drawEllipse(specular_rect)

        painter.end()

    def retranslate_ui(self) -> None:
        self.lbl_sub.setText(tr("care_scan_sub"))
