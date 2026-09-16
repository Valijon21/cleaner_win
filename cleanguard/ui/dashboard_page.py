"""
Dashboard Page: Storage overview, drive health, and quick actions.
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)
from PyQt5.QtCore import Qt, pyqtSignal
from cleanguard.windows.drives import enumerate_drives
from cleanguard.windows.os_info import get_windows_version
from cleanguard.ui.widgets.cards import StatCard, DriveCard
from cleanguard.database.db import DatabaseManager
from cleanguard.database.repositories import HistoryRepository
from cleanguard.localization import tr
from cleanguard.utils.formatting import format_bytes, format_number


class DashboardPage(QWidget):
    """Main dashboard overview screen."""
    start_scan_requested = pyqtSignal()

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.history_repo = HistoryRepository(self.db)
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(24)

        # Header Row: Title & Action
        header_row = QHBoxLayout()
        header_text = QVBoxLayout()
        self.lbl_title = QLabel(tr("nav_dashboard"))
        self.lbl_title.setStyleSheet("font-size: 26px; font-weight: 700; color: #F9FAFB;")

        os_info = get_windows_version()
        self.lbl_subtitle = QLabel(f"{os_info.display_name} ({os_info.architecture}) • CleanGuard Engine Active")
        self.lbl_subtitle.setStyleSheet("font-size: 13px; color: #9CA3AF;")

        header_text.addWidget(self.lbl_title)
        header_text.addWidget(self.lbl_subtitle)
        header_row.addLayout(header_text)

        header_row.addStretch()

        self.btn_scan = QPushButton(f"  {tr('btn_scan_now')}  ")
        self.btn_scan.setObjectName("PrimaryButton")
        self.btn_scan.setCursor(Qt.PointingHandCursor)
        self.btn_scan.clicked.connect(self.start_scan_requested.emit)
        header_row.addWidget(self.btn_scan)

        main_layout.addLayout(header_row)

        # Cumulative Metrics Row
        stats = self.history_repo.get_cumulative_stats()
        tot_bytes = stats.get("total_bytes_recovered", 0.0)
        tot_files = stats.get("total_files_deleted", 0.0)

        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(16)

        self.card_recovered = StatCard(
            title=tr("stat_total_cleaned").upper(),
            value=format_bytes(tot_bytes),
            subtext="Lifetime reclaimed space",
        )
        self.card_files = StatCard(
            title=tr("stat_files_removed").upper(),
            value=format_number(int(tot_files)),
            subtext="Junk & cache items cleaned",
        )
        self.card_safety = StatCard(
            title="SAFETY ENGINE",
            value="100% ENFORCED",
            subtext="Zero risk of personal data loss",
        )

        metrics_row.addWidget(self.card_recovered)
        metrics_row.addWidget(self.card_files)
        metrics_row.addWidget(self.card_safety)

        main_layout.addLayout(metrics_row)

        # Drive Storage Section Header
        lbl_drives_title = QLabel("LOCAL STORAGE DRIVES")
        lbl_drives_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #9CA3AF; letter-spacing: 1px;")
        main_layout.addWidget(lbl_drives_title)

        # Drives Grid/List
        self.drives_container = QVBoxLayout()
        self.drives_container.setSpacing(12)
        self.refresh_drives()
        main_layout.addLayout(self.drives_container)

        main_layout.addStretch()

    def refresh_drives(self) -> None:
        """Reload drive information."""
        # Clear previous cards
        while self.drives_container.count():
            item = self.drives_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        drives = enumerate_drives()
        for drive in drives:
            if drive.is_ready and drive.drive_type == "Fixed Disk":
                card = DriveCard(drive)
                self.drives_container.addWidget(card)

    def refresh_stats(self) -> None:
        """Update metrics numbers after cleanup."""
        stats = self.history_repo.get_cumulative_stats()
        self.card_recovered.set_value(format_bytes(stats.get("total_bytes_recovered", 0.0)))
        self.card_files.set_value(format_number(int(stats.get("total_files_deleted", 0.0))))
        self.refresh_drives()
