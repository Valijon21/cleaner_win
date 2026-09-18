"""
Cards and Data Visualizations UI Components.
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
from cleanguard.core.contracts import DriveInfo
from cleanguard.localization import tr
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
        local_disk_text = tr("drive_local_disk", "Local Disk")
        drive_title = f"{drive.letter} ({drive.label or local_disk_text})"
        self.lbl_title = QLabel(drive_title)
        self.lbl_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #F9FAFB;")
        top_row.addWidget(self.lbl_title)

        top_row.addStretch()

        if drive.is_system_drive:
            sys_tag = QLabel(f" {tr('lbl_system', 'SYSTEM')} ")
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
        self.lbl_stats = QLabel(tr("lbl_free_of", "{free} free of {total}", free=free_str, total=tot_str))
        self.lbl_stats.setStyleSheet("color: #9CA3AF; font-size: 12px;")

        self.lbl_pct = QLabel(tr("lbl_used_pct", "{pct}% used", pct=used_pct))
        self.lbl_pct.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: 500;")

        stats_row.addWidget(self.lbl_stats)
        stats_row.addStretch()
        stats_row.addWidget(self.lbl_pct)

        layout.addLayout(stats_row)


class CategoryCard(QFrame):
    """Card representing a cleanup category with quick scan trigger."""
    scan_requested = pyqtSignal(str)  # category_id

    def __init__(self, category_id: str, icon: str, title: str, description: str, parent=None):
        super().__init__(parent)
        self.setObjectName("SurfaceCard")
        self.category_id = category_id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # Header: Icon + Title
        top_row = QHBoxLayout()
        self.lbl_icon = QLabel(icon)
        self.lbl_icon.setStyleSheet("font-size: 20px;")
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #F9FAFB;")
        top_row.addWidget(self.lbl_icon)
        top_row.addWidget(self.lbl_title)
        top_row.addStretch()
        layout.addLayout(top_row)

        # Description
        self.lbl_desc = QLabel(description)
        self.lbl_desc.setStyleSheet("font-size: 11px; color: #9CA3AF; line-height: 1.3;")
        self.lbl_desc.setWordWrap(True)
        layout.addWidget(self.lbl_desc)

        # Bottom row: Quick action button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_action = QPushButton(tr("dashboard_btn_scan_category"))
        self.btn_action.setObjectName("SecondaryButton")
        self.btn_action.setCursor(Qt.PointingHandCursor)
        self.btn_action.clicked.connect(lambda: self.scan_requested.emit(self.category_id))
        btn_row.addWidget(self.btn_action)
        layout.addLayout(btn_row)

    def update_text(self, title: str, description: str) -> None:
        self.lbl_title.setText(title)
        self.lbl_desc.setText(description)
        self.btn_action.setText(tr("dashboard_btn_scan_category"))


CATEGORY_BADGE_STYLES = {
    "temp_files": "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #064E3B, stop:1 #059669); border: 1px solid #10B981;",
    "app_cache": "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #78350F, stop:1 #D97706); border: 1px solid #F59E0B;",
    "browser_cache": "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E3A8A, stop:1 #2563EB); border: 1px solid #3B82F6;",
    "system_logs": "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4C1D95, stop:1 #7C3AED); border: 1px solid #8B5CF6;",
    "crash_dumps": "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #881337, stop:1 #E11D48); border: 1px solid #F43F5E;",
    "thumbnail_cache": "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #134E4A, stop:1 #0D9488); border: 1px solid #14B8A6;",
    "recycle_bin": "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #064E3B, stop:1 #10B981); border: 1px solid #34D399;",
}


class CareModuleCard(QFrame):
    """Interactive selectable module card for IObit ASC Care Selector Grid."""
    toggled = pyqtSignal(bool)

    def __init__(self, category_id: str, icon: str, title: str, description: str, checked: bool = True, parent=None):
        super().__init__(parent)
        self.setObjectName("CareCard")
        self.category_id = category_id
        self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(14)

        from PyQt5.QtWidgets import QCheckBox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(checked)
        self.checkbox.toggled.connect(self._on_toggled)
        self.checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #4B5563;
                border-radius: 4px;
                background-color: #1F2937;
            }
            QCheckBox::indicator:hover {
                border-color: #10B981;
            }
            QCheckBox::indicator:checked {
                background-color: #10B981;
                border-color: #34D399;
            }
        """)
        layout.addWidget(self.checkbox)

        # High-tech gradient icon badge box (IObit ASC signature style)
        badge_style = CATEGORY_BADGE_STYLES.get(
            category_id,
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E293B, stop:1 #334155); border: 1px solid #475569;"
        )
        self.badge_box = QFrame()
        self.badge_box.setFixedSize(40, 40)
        self.badge_box.setStyleSheet(f"{badge_style} border-radius: 8px;")
        badge_layout = QVBoxLayout(self.badge_box)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        badge_layout.setAlignment(Qt.AlignCenter)

        self.lbl_icon = QLabel(icon)
        self.lbl_icon.setStyleSheet("font-size: 20px; background: transparent;")
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        badge_layout.addWidget(self.lbl_icon)
        layout.addWidget(self.badge_box)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #F9FAFB; background: transparent;")
        self.lbl_desc = QLabel(description)
        self.lbl_desc.setStyleSheet("font-size: 11px; color: #9CA3AF; background: transparent; line-height: 1.3;")
        self.lbl_desc.setWordWrap(True)

        text_layout.addWidget(self.lbl_title)
        text_layout.addWidget(self.lbl_desc)
        layout.addLayout(text_layout, stretch=1)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            if not self.checkbox.geometry().contains(pos):
                self.checkbox.setChecked(not self.checkbox.isChecked())
        super().mousePressEvent(event)

    def _on_toggled(self, checked: bool) -> None:
        self.toggled.emit(checked)

    def is_checked(self) -> bool:
        return self.checkbox.isChecked()

    def set_checked(self, checked: bool) -> None:
        self.checkbox.setChecked(checked)

    def update_text(self, title: str, description: str) -> None:
        self.lbl_title.setText(title)
        self.lbl_desc.setText(description)

