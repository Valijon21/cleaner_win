"""
Scan Page: Multi-Module Live Scan Pipeline inspired by IObit Advanced SystemCare.
Visualizes real-time per-module stage progress, badges, and aggregated counters.
"""

from typing import Dict, List, Optional
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QFrame,
    QScrollArea,
)
from PyQt5.QtCore import Qt, pyqtSignal
from cleanguard.services.scan_service import ScanWorker
from cleanguard.core.contracts import ScanSummary
from cleanguard.localization import tr
from cleanguard.utils.formatting import format_bytes, format_number


class ModuleStageCard(QFrame):
    """Visual stage card representing an individual module in the ASC pipeline."""

    def __init__(self, category_id: str, icon: str, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("ModuleStageCard")
        self.category_id = category_id

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        self.lbl_icon = QLabel(icon)
        self.lbl_icon.setStyleSheet("font-size: 20px; background: transparent;")
        layout.addWidget(self.lbl_icon)

        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #F9FAFB; background: transparent;")
        layout.addWidget(self.lbl_title)

        layout.addStretch()

        self.lbl_stats = QLabel("0 ta • 0 B")
        self.lbl_stats.setStyleSheet("font-size: 12px; color: #9CA3AF; font-weight: 500; background: transparent;")
        layout.addWidget(self.lbl_stats)

        self.lbl_badge = QLabel(f" ⏳ {tr('module_status_queued')} ")
        self.lbl_badge.setStyleSheet("""
            background-color: #1F2937;
            color: #9CA3AF;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            padding: 3px 8px;
        """)
        layout.addWidget(self.lbl_badge)

    def set_status(self, status: str, count: int = 0, bytes_val: int = 0) -> None:
        if count > 0 or bytes_val > 0:
            self.lbl_stats.setText(f"{format_number(count)} ta • {format_bytes(bytes_val)}")

        if status == "queued":
            self.lbl_badge.setText(f" ⏳ {tr('module_status_queued')} ")
            self.lbl_badge.setStyleSheet("""
                background-color: #1F2937;
                color: #9CA3AF;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
                padding: 3px 8px;
            """)
        elif status == "scanning":
            self.lbl_badge.setText(f" 🔄 {tr('module_status_scanning')} ")
            self.lbl_badge.setStyleSheet("""
                background-color: #1E3A8A;
                color: #60A5FA;
                border: 1px solid #3B82F6;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 700;
                padding: 3px 8px;
            """)
        elif status == "completed":
            self.lbl_badge.setText(f" ✅ {tr('module_status_completed')} ")
            self.lbl_badge.setStyleSheet("""
                background-color: #064E3B;
                color: #34D399;
                border: 1px solid #059669;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 700;
                padding: 3px 8px;
            """)

    def update_title(self, title: str) -> None:
        self.lbl_title.setText(title)


class ScanPage(QWidget):
    """Multi-module stage pipeline visualization and scan control."""
    scan_completed = pyqtSignal(object, list)  # (ScanSummary, List[ScanItem])
    scan_cancelled = pyqtSignal()

    CATEGORIES_CONFIG = [
        ("temp_files", "🗑️", "category_temp_files"),
        ("app_cache", "⚡", "category_app_cache"),
        ("browser_cache", "🌐", "category_browser_cache"),
        ("system_logs", "📋", "category_system_logs"),
        ("crash_dumps", "⚠️", "category_crash_dumps"),
        ("thumbnail_cache", "🖼️", "category_thumbnail_cache"),
        ("recycle_bin", "♻️", "category_recycle_bin"),
    ]

    def __init__(self, scan_worker: ScanWorker, parent=None):
        super().__init__(parent)
        self.worker = scan_worker
        self.stage_cards: Dict[str, ModuleStageCard] = {}
        self.active_categories: List[str] = [cat_id for cat_id, _, _ in self.CATEGORIES_CONFIG]

        self.worker.progress.connect(self._on_worker_progress)
        self.worker.category_progress.connect(self._on_category_progress)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.error.connect(self._on_worker_error)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(20)

        # Header Row: Title & Safe Cancel
        header_row = QHBoxLayout()
        self.lbl_title = QLabel(tr("nav_scan"))
        self.lbl_title.setStyleSheet("font-size: 26px; font-weight: 700; color: #F9FAFB;")
        header_row.addWidget(self.lbl_title)
        header_row.addStretch()

        self.btn_cancel = QPushButton(f"  {tr('btn_cancel')}  ")
        self.btn_cancel.setObjectName("SecondaryButton")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)
        self.btn_cancel.setVisible(False)
        header_row.addWidget(self.btn_cancel)

        layout.addLayout(header_row)

        # Top Aggregated Progress Card
        card = QFrame()
        card.setObjectName("SurfaceCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(14)

        top_stats_row = QHBoxLayout()
        self.lbl_status = QLabel(tr("scan_ready_title"))
        self.lbl_status.setStyleSheet("font-size: 16px; font-weight: 700; color: #06B6D4;")
        top_stats_row.addWidget(self.lbl_status)
        top_stats_row.addStretch()

        self.lbl_files_scanned = QLabel(tr("files_scanned_count", count="0"))
        self.lbl_files_scanned.setStyleSheet("color: #F9FAFB; font-weight: 600; font-size: 13px;")
        top_stats_row.addWidget(self.lbl_files_scanned)

        top_stats_row.addSpacing(16)
        self.lbl_bytes_found = QLabel(tr("junk_found_size", size="0 B"))
        self.lbl_bytes_found.setStyleSheet("color: #10B981; font-weight: 800; font-size: 14px;")
        top_stats_row.addWidget(self.lbl_bytes_found)

        card_layout.addLayout(top_stats_row)

        # Progress Bar
        self.prog_bar = QProgressBar()
        self.prog_bar.setRange(0, 100)
        self.prog_bar.setValue(0)
        self.prog_bar.setFixedHeight(10)
        card_layout.addWidget(self.prog_bar)

        # Current path ticker
        self.lbl_current_path = QLabel(tr("scan_ready_subtext"))
        self.lbl_current_path.setStyleSheet("color: #6B7280; font-size: 12px;")
        self.lbl_current_path.setWordWrap(True)
        card_layout.addWidget(self.lbl_current_path)

        layout.addWidget(card)

        # Pipeline Header
        self.lbl_pipeline_title = QLabel("ASC LIVE PIPELINE")
        self.lbl_pipeline_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #9CA3AF; letter-spacing: 1px;")
        layout.addWidget(self.lbl_pipeline_title)

        # Scrollable Stages Pipeline
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")

        stages_container = QWidget()
        self.stages_layout = QVBoxLayout(stages_container)
        self.stages_layout.setContentsMargins(0, 0, 0, 0)
        self.stages_layout.setSpacing(8)

        for cat_id, icon, title_key in self.CATEGORIES_CONFIG:
            stage_card = ModuleStageCard(
                category_id=cat_id,
                icon=icon,
                title=tr(title_key),
            )
            self.stage_cards[cat_id] = stage_card
            self.stages_layout.addWidget(stage_card)

        self.stages_layout.addStretch()
        scroll.setWidget(stages_container)
        layout.addWidget(scroll, stretch=1)

    def start_scan(self, target_categories: Optional[List[str]] = None) -> None:
        """Start or restart the background scanning process with pipeline feedback."""
        self.active_categories = target_categories or [c[0] for c in self.CATEGORIES_CONFIG]

        self.lbl_status.setText(tr("status_scanning"))
        self.lbl_status.setStyleSheet("font-size: 16px; font-weight: 700; color: #06B6D4;")
        self.lbl_current_path.setText(tr("status_initializing_workers"))
        self.lbl_files_scanned.setText(tr("files_scanned_count", count="0"))
        self.lbl_bytes_found.setText(tr("junk_found_size", size="0 B"))
        self.prog_bar.setRange(0, 0)  # Animated busy mode

        self.btn_cancel.setVisible(True)
        self.btn_cancel.setEnabled(True)

        # Reset module stage cards
        for cat_id, card in self.stage_cards.items():
            if cat_id in self.active_categories:
                card.setVisible(True)
                card.set_status("queued", 0, 0)
            else:
                card.setVisible(False)

        if not self.worker.isRunning():
            self.worker.start()

    def reset_to_idle(self) -> None:
        """Reset UI to ready / idle state."""
        self.lbl_status.setText(tr("scan_ready_title"))
        self.lbl_status.setStyleSheet("font-size: 16px; font-weight: 700; color: #10B981;")
        self.lbl_current_path.setText(tr("scan_ready_subtext"))
        self.prog_bar.setRange(0, 100)
        self.prog_bar.setValue(0)
        self.btn_cancel.setVisible(False)

        for card in self.stage_cards.values():
            card.setVisible(True)
            card.set_status("queued", 0, 0)

    def _on_category_progress(self, cat_id: str, status: str, count: int, bytes_found: int) -> None:
        """Update live status for a specific module card in the pipeline."""
        if cat_id in self.stage_cards:
            self.stage_cards[cat_id].set_status(status, count, bytes_found)

    def _on_worker_progress(self, msg: str, count: int, bytes_found: int) -> None:
        if len(msg) > 85:
            display_msg = "..." + msg[-82:]
        else:
            display_msg = msg
        self.lbl_current_path.setText(display_msg)
        self.lbl_files_scanned.setText(tr("files_scanned_count", count=format_number(count)))
        self.lbl_bytes_found.setText(tr("junk_found_size", size=format_bytes(bytes_found)))

    def _on_worker_finished(self, summary: ScanSummary, items: list) -> None:
        self.prog_bar.setRange(0, 100)
        self.prog_bar.setValue(100)
        self.lbl_status.setText(tr("status_scan_complete"))
        self.lbl_status.setStyleSheet("font-size: 16px; font-weight: 700; color: #10B981;")
        self.btn_cancel.setVisible(False)

        # Ensure all active stage cards show completed
        for cat_id in self.active_categories:
            if cat_id in self.stage_cards:
                cat_count = summary.items_by_category.get(cat_id, 0)
                cat_bytes = summary.bytes_by_category.get(cat_id, 0)
                self.stage_cards[cat_id].set_status("completed", cat_count, cat_bytes)

        self.scan_completed.emit(summary, items)

    def _on_worker_error(self, err_msg: str) -> None:
        self.lbl_status.setText(f"Scan Error: {err_msg}")
        self.lbl_status.setStyleSheet("color: #EF4444; font-size: 16px;")
        self.btn_cancel.setVisible(False)

    def _on_cancel_clicked(self) -> None:
        self.lbl_status.setText(tr("scan_cancelled"))
        self.lbl_status.setStyleSheet("color: #F59E0B; font-size: 16px;")
        self.btn_cancel.setEnabled(False)
        self.worker.cancel()
        self.scan_cancelled.emit()

    def retranslate_ui(self) -> None:
        """Dynamic translation updates on language switch."""
        self.lbl_title.setText(tr("nav_scan"))
        self.btn_cancel.setText(f"  {tr('btn_cancel')}  ")

        for cat_id, _, title_key in self.CATEGORIES_CONFIG:
            if cat_id in self.stage_cards:
                self.stage_cards[cat_id].update_title(tr(title_key))
