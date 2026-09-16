"""
Cards and Data Visualizations UI Components.
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import Qt
from cleanguard.core.contracts import DriveInfo
from cleanguard.utils.formatting import format_bytes


class StatCard(QFrame):
    """High-contrast metric statistic card."""

    def __init__(self, title: str, value: str, subtext: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("SurfaceCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: 500;")

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("color: #F9FAFB; font-size: 24px; font-weight: 700;")

        self.sub_label = QLabel(subtext)
        self.sub_label.setStyleSheet("color: #6B7280; font-size: 11px;")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        if subtext:
            layout.addWidget(self.sub_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)

    def set_subtext(self, subtext: str) -> None:
        self.sub_label.setText(subtext)


class DriveCard(QFrame):
    """Visual storage capacity and health gauge card for a drive."""

    def __init__(self, drive: DriveInfo, parent=None):
        super().__init__(parent)
        self.setObjectName("SurfaceCard")
        self.drive = drive

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        # Header Row: Drive Letter + Label + System Tag
        top_row = QHBoxLayout()
        drive_title = f"{drive.letter} ({drive.label or 'Local Disk'})"
        self.lbl_title = QLabel(drive_title)
        self.lbl_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #F9FAFB;")
        top_row.addWidget(self.lbl_title)

        top_row.addStretch()

        if drive.is_system_drive:
            sys_tag = QLabel(" SYSTEM ")
            sys_tag.setStyleSheet("""
                background-color: #1E3A8A;
                color: #60A5FA;
                font-size: 10px;
                font-weight: 700;
                border-radius: 4px;
                padding: 2px 6px;
            """)
            top_row.addWidget(sys_tag)

        layout.addLayout(top_row)

        # Storage Progress Bar
        self.progress_bar = QProgressBar()
        used_pct = int(drive.used_percentage)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(used_pct)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)

        # Adjust bar color if disk space is critical (> 90% full)
        if used_pct >= 90:
            self.progress_bar.setStyleSheet("""
                QProgressBar::chunk {
                    background-color: #EF4444;
                    border-radius: 4px;
                }
            """)
        elif used_pct >= 75:
            self.progress_bar.setStyleSheet("""
                QProgressBar::chunk {
                    background-color: #F59E0B;
                    border-radius: 4px;
                }
            """)

        layout.addWidget(self.progress_bar)

        # Storage Numbers Row: Free / Total
        stats_row = QHBoxLayout()
        free_str = format_bytes(drive.free_bytes)
        tot_str = format_bytes(drive.total_bytes)
        self.lbl_stats = QLabel(f"{free_str} free of {tot_str}")
        self.lbl_stats.setStyleSheet("color: #9CA3AF; font-size: 12px;")

        self.lbl_pct = QLabel(f"{used_pct}% used")
        self.lbl_pct.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: 500;")

        stats_row.addWidget(self.lbl_stats)
        stats_row.addStretch()
        stats_row.addWidget(self.lbl_pct)

        layout.addLayout(stats_row)
