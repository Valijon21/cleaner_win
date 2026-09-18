"""
Cleanup Page: Progress indicator during cleanup, live path ticker, and celebration report.
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
from cleanguard.core.contracts import CleanupSummary
from cleanguard.localization import tr
from cleanguard.utils.formatting import format_bytes, format_number


class CleanupPage(QWidget):
    """Cleanup execution screen, cancellation control, and final recovery report."""
    done_clicked = pyqtSignal()
    cancel_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(24)

        self.lbl_title = QLabel(tr("nav_cleanup"))
        self.lbl_title.setStyleSheet("font-size: 26px; font-weight: 700; color: #F9FAFB;")
        self.main_layout.addWidget(self.lbl_title)

        # Progress Card
        self.card = QFrame()
        self.card.setObjectName("SurfaceCard")
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(32, 32, 32, 32)
        self.card_layout.setSpacing(20)

        self.lbl_status = QLabel(tr("status_cleaning"))
        self.lbl_status.setStyleSheet("font-size: 18px; font-weight: 600; color: #10B981;")
        self.card_layout.addWidget(self.lbl_status)

        self.prog_bar = QProgressBar()
        self.prog_bar.setRange(0, 100)
        self.prog_bar.setValue(0)
        self.prog_bar.setFixedHeight(12)
        self.card_layout.addWidget(self.prog_bar)

        self.lbl_current_path = QLabel("Starting safety verification...")
        self.lbl_current_path.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        self.card_layout.addWidget(self.lbl_current_path)

        self.lbl_recovered = QLabel("Space recovered: 0 B")
        self.lbl_recovered.setStyleSheet("color: #10B981; font-weight: 700; font-size: 15px;")
        self.card_layout.addWidget(self.lbl_recovered)

        self.main_layout.addWidget(self.card)

        # Action Buttons Row
        self.btn_row = QHBoxLayout()
        self.btn_row.addStretch()

        self.btn_cancel = QPushButton(f"  {tr('btn_cancel')}  ")
        self.btn_cancel.setObjectName("SecondaryButton")
        self.btn_cancel.clicked.connect(self._on_cancel)
        self.btn_row.addWidget(self.btn_cancel)

        self.btn_done = QPushButton(f"  {tr('btn_return_dashboard')}  ")
        self.btn_done.setObjectName("PrimaryButton")
        self.btn_done.setVisible(False)
        self.btn_done.clicked.connect(self.done_clicked.emit)
        self.btn_row.addWidget(self.btn_done)

        self.btn_row.addStretch()
        self.main_layout.addLayout(self.btn_row)

        self.main_layout.addStretch()

    def reset_state(self) -> None:
        """Reset UI for a new cleanup run."""
        self.lbl_status.setText(tr("status_cleaning"))
        self.lbl_status.setStyleSheet("font-size: 18px; font-weight: 600; color: #10B981;")
        self.prog_bar.setValue(0)
        self.lbl_current_path.setText("Starting safety verification...")
        self.lbl_recovered.setText("Space recovered: 0 B")
        self.btn_cancel.setEnabled(True)
        self.btn_cancel.setVisible(True)
        self.btn_done.setVisible(False)

    def update_progress(self, processed: int, total: int, recovered: int, cur_path: str) -> None:
        """Update progress bar and status without GUI lag."""
        pct = int((processed / max(1, total)) * 100)
        self.prog_bar.setValue(pct)
        self.lbl_recovered.setText(f"Space recovered: {format_bytes(recovered)}")
        display_path = ("..." + cur_path[-80:]) if len(cur_path) > 83 else cur_path
        self.lbl_current_path.setText(f"Processing ({processed}/{total}): {display_path}")

    def show_completion(self, summary: CleanupSummary) -> None:
        """Display successful completion metrics."""
        self.prog_bar.setValue(100)
        self.lbl_status.setText(tr("cleanup_celebration_title"))
        self.lbl_status.setStyleSheet("font-size: 20px; font-weight: 700; color: #10B981;")

        recovered_str = format_bytes(summary.bytes_recovered)
        self.lbl_recovered.setText(tr("cleanup_celebration_subtitle", size=recovered_str))
        self.lbl_recovered.setStyleSheet("font-size: 22px; font-weight: 800; color: #10B981;")

        self.lbl_current_path.setText(
            tr(
                "cleanup_summary_details",
                deleted=format_number(summary.files_deleted),
                skipped=format_number(summary.files_skipped),
            )
        )

        self.btn_cancel.setVisible(False)
        self.btn_done.setVisible(True)

    def _on_cancel(self) -> None:
        self.btn_cancel.setEnabled(False)
        self.lbl_status.setText("Cancelling cleanup safely...")
        self.cancel_clicked.emit()

    def retranslate_ui(self) -> None:
        self.lbl_title.setText(tr("nav_cleanup"))
        self.btn_cancel.setText(f"  {tr('btn_cancel')}  ")
        self.btn_done.setText(f"  {tr('btn_return_dashboard')}  ")

