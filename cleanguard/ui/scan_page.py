"""
Scan Page: Active scanning status, animated progress, and cancellation.
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal
from cleanguard.services.scan_service import ScanWorker
from cleanguard.core.contracts import ScanSummary, ScanItem
from cleanguard.localization import tr
from cleanguard.utils.formatting import format_bytes, format_number


class ScanPage(QWidget):
    """Real-time scan progress visualization."""
    scan_completed = pyqtSignal(object, list)  # (ScanSummary, List[ScanItem])
    scan_cancelled = pyqtSignal()

    def __init__(self, scan_worker: ScanWorker, parent=None):
        super().__init__(parent)
        self.worker = scan_worker
        self.worker.progress.connect(self._on_worker_progress)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.error.connect(self._on_worker_error)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)

        # Title
        self.lbl_title = QLabel(tr("nav_scan"))
        self.lbl_title.setStyleSheet("font-size: 26px; font-weight: 700; color: #F9FAFB;")
        layout.addWidget(self.lbl_title)

        # Main Progress Surface Card
        card = QFrame()
        card.setObjectName("SurfaceCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(20)

        # Status text
        self.lbl_status = QLabel(tr("status_scanning"))
        self.lbl_status.setStyleSheet("font-size: 18px; font-weight: 600; color: #10B981;")
        card_layout.addWidget(self.lbl_status)

        # Progress Bar (Indeterminate / Animated during scan)
        self.prog_bar = QProgressBar()
        self.prog_bar.setRange(0, 0)  # Indeterminate marquee animation
        self.prog_bar.setFixedHeight(12)
        card_layout.addWidget(self.prog_bar)

        # Current File path label (truncated ticker)
        self.lbl_current_path = QLabel("Initializing scanner workers...")
        self.lbl_current_path.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        card_layout.addWidget(self.lbl_current_path)

        # Stats row
        stats_row = QHBoxLayout()
        self.lbl_files_scanned = QLabel("Files scanned: 0")
        self.lbl_files_scanned.setStyleSheet("color: #F9FAFB; font-weight: 600; font-size: 14px;")

        self.lbl_bytes_found = QLabel("Junk found: 0 B")
        self.lbl_bytes_found.setStyleSheet("color: #10B981; font-weight: 700; font-size: 14px;")

        stats_row.addWidget(self.lbl_files_scanned)
        stats_row.addStretch()
        stats_row.addWidget(self.lbl_bytes_found)
        card_layout.addLayout(stats_row)

        layout.addWidget(card)

        # Cancel Button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_cancel = QPushButton(f"  {tr('btn_cancel')}  ")
        self.btn_cancel.setObjectName("SecondaryButton")
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)
        btn_row.addWidget(self.btn_cancel)
        layout.addLayout(btn_row)

        layout.addStretch()

    def start_scan(self) -> None:
        """Start the background scanning process."""
        self.lbl_status.setText(tr("status_scanning"))
        self.lbl_current_path.setText("Searching storage for reclaimable data...")
        self.lbl_files_scanned.setText("Files scanned: 0")
        self.lbl_bytes_found.setText("Junk found: 0 B")
        self.prog_bar.setRange(0, 0)
        self.btn_cancel.setEnabled(True)

        if not self.worker.isRunning():
            self.worker.start()

    def _on_worker_progress(self, msg: str, count: int, bytes_found: int) -> None:
        # Show truncated path
        if len(msg) > 85:
            display_msg = "..." + msg[-82:]
        else:
            display_msg = msg
        self.lbl_current_path.setText(display_msg)
        self.lbl_files_scanned.setText(f"Files scanned: {format_number(count)}")
        self.lbl_bytes_found.setText(f"Junk found: {format_bytes(bytes_found)}")

    def _on_worker_finished(self, summary: ScanSummary, items: list) -> None:
        self.prog_bar.setRange(0, 100)
        self.prog_bar.setValue(100)
        self.lbl_status.setText("Scan Complete!")
        self.scan_completed.emit(summary, items)

    def _on_worker_error(self, err_msg: str) -> None:
        self.lbl_status.setText(f"Scan Error: {err_msg}")
        self.lbl_status.setStyleSheet("color: #EF4444; font-size: 16px;")

    def _on_cancel_clicked(self) -> None:
        self.btn_cancel.setEnabled(False)
        self.lbl_status.setText("Cancelling scan safely...")
        self.worker.cancel()
        self.scan_cancelled.emit()
