"""
CleanGuard System Tray Icon & Notification Management.
Provides background residency, tray context menu, and intelligent balloon alerts.
"""

from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen, QFont
from PyQt5.QtCore import Qt, pyqtSignal
from cleanguard.localization import tr
from cleanguard.core.contracts import DriveInfo
from cleanguard.utils.formatting import format_bytes


def create_default_tray_icon() -> QIcon:
    """Create a crisp 32x32 emerald shield pixmap icon for Windows System Tray."""
    pix = QPixmap(32, 32)
    pix.fill(Qt.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)

    # Emerald circular background
    brush = QBrush(QColor("#10B981"))
    pen = QPen(QColor("#059669"), 1.5)
    painter.setBrush(brush)
    painter.setPen(pen)
    painter.drawRoundedRect(2, 2, 28, 28, 6, 6)

    # Shield symbol / letter C
    painter.setPen(QColor("#FFFFFF"))
    font = QFont("Segoe UI", 14, QFont.Bold)
    painter.setFont(font)
    painter.drawText(0, 0, 32, 30, Qt.AlignCenter, "C")
    painter.end()

    return QIcon(pix)


class CleanGuardTrayIcon(QSystemTrayIcon):
    """System Tray Icon controller with localized context menu and smart notifications."""
    show_window_requested = pyqtSignal()
    quick_clean_requested = pyqtSignal()
    exit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(create_default_tray_icon())
        self.setToolTip("CleanGuard — Windows Storage Optimizer")

        self._init_menu()
        self.activated.connect(self._on_tray_activated)

    def _init_menu(self) -> None:
        self.menu = QMenu()
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #1F2937;
                color: #F9FAFB;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 6px;
            }
            QMenu::item {
                padding: 8px 24px 8px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #10B981;
                color: #FFFFFF;
            }
            QMenu::separator {
                height: 1px;
                background-color: #374151;
                margin: 4px 8px;
            }
        """)

        # 1. Open Window Action
        self.act_open = QAction("📊 " + tr("tray_open_app"), self)
        self.act_open.triggered.connect(self.show_window_requested.emit)
        self.menu.addAction(self.act_open)

        # 2. Quick Clean Action
        self.act_clean = QAction("🔍 " + tr("tray_quick_clean"), self)
        self.act_clean.triggered.connect(self.quick_clean_requested.emit)
        self.menu.addAction(self.act_clean)

        self.menu.addSeparator()

        # 3. Status Action (Disabled / Informational)
        self.act_status = QAction("🛡️ " + tr("tray_status_active"), self)
        self.act_status.setEnabled(False)
        self.menu.addAction(self.act_status)

        self.menu.addSeparator()

        # 4. Exit Application Action
        self.act_exit = QAction("❌ " + tr("tray_exit"), self)
        self.act_exit.triggered.connect(self.exit_requested.emit)
        self.menu.addAction(self.act_exit)

        self.setContextMenu(self.menu)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_window_requested.emit()

    def show_minimized_notification(self) -> None:
        """Inform user that CleanGuard was minimized to notification tray."""
        self.showMessage(
            tr("tray_minimized_title"),
            tr("tray_minimized_msg"),
            QSystemTrayIcon.Information,
            3000,
        )

    def show_low_space_alert(self, drive: DriveInfo) -> None:
        """Display Windows toast notification when a drive is critically low on space."""
        title = tr("tray_low_space_title")
        msg = tr("tray_low_space_msg", drive=drive.letter, free=format_bytes(drive.free_bytes))
        self.showMessage(title, msg, QSystemTrayIcon.Warning, 8000)

    def retranslate_ui(self) -> None:
        """Update context menu actions dynamically on language switch."""
        self.act_open.setText("📊 " + tr("tray_open_app"))
        self.act_clean.setText("🔍 " + tr("tray_quick_clean"))
        self.act_status.setText("🛡️ " + tr("tray_status_active"))
        self.act_exit.setText("❌ " + tr("tray_exit"))
