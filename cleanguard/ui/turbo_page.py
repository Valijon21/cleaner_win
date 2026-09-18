"""
Turbo Boost Page: Live memory optimization, RAM flushing, and performance mode switching.
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QFrame,
    QRadioButton,
    QButtonGroup,
    QScrollArea,
)
from PyQt5.QtCore import Qt, QTimer
from cleanguard.windows.memory import MemoryOptimizer
from cleanguard.utils.formatting import format_bytes
from cleanguard.localization import tr
from cleanguard.utils.logging import get_logger

logger = get_logger("ui.turbo")


class TurboPage(QWidget):
    """Turbo Boost & Memory Optimization View."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

        # Update stats periodically
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(2500)
        self.update_stats()

    def _init_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        # Header Row
        header_row = QHBoxLayout()
        header_text = QVBoxLayout()
        self.lbl_title = QLabel(tr("nav_turbo", "⚡ Turbo Boost (Tizimni tezlashtirish)"))
        self.lbl_title.setStyleSheet("font-size: 24px; font-weight: 700; color: #F9FAFB;")
        self.lbl_subtitle = QLabel(
            tr("turbo_subtitle", "Operativ xotira (RAM)ni bo'shating va og'ir vazifalar uchun tizimni tezlashtiring")
        )
        self.lbl_subtitle.setStyleSheet("font-size: 13px; color: #9CA3AF;")
        header_text.addWidget(self.lbl_title)
        header_text.addWidget(self.lbl_subtitle)
        header_row.addLayout(header_text)
        header_row.addStretch()
        layout.addLayout(header_row)

        # Main RAM Status Card
        self.ram_card = QFrame()
        self.ram_card.setStyleSheet("""
            QFrame {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 12px;
                padding: 24px;
            }
        """)
        ram_layout = QVBoxLayout(self.ram_card)
        ram_layout.setSpacing(14)

        card_top = QHBoxLayout()
        self.lbl_ram_title = QLabel("💻 OPERATIV XOTIRA (RAM) HOLATI")
        self.lbl_ram_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #9CA3AF; letter-spacing: 0.5px;")
        self.lbl_ram_pct = QLabel("0%")
        self.lbl_ram_pct.setStyleSheet("font-size: 28px; font-weight: 800; color: #10B981;")
        card_top.addWidget(self.lbl_ram_title)
        card_top.addStretch()
        card_top.addWidget(self.lbl_ram_pct)
        ram_layout.addLayout(card_top)

        # RAM Bar
        self.ram_bar = QProgressBar()
        self.ram_bar.setRange(0, 100)
        self.ram_bar.setValue(0)
        self.ram_bar.setTextVisible(False)
        self.ram_bar.setFixedHeight(14)
        self.ram_bar.setStyleSheet("""
            QProgressBar {
                background-color: #374151;
                border-radius: 7px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #3B82F6);
                border-radius: 7px;
            }
        """)
        ram_layout.addWidget(self.ram_bar)

        # RAM details row
        details_row = QHBoxLayout()
        self.lbl_used_ram = QLabel("Band: --")
        self.lbl_used_ram.setStyleSheet("color: #E5E7EB; font-size: 13px; font-weight: 600;")
        self.lbl_free_ram = QLabel("Bo'sh: --")
        self.lbl_free_ram.setStyleSheet("color: #10B981; font-size: 13px; font-weight: 600;")
        self.lbl_total_ram = QLabel("Jami: --")
        self.lbl_total_ram.setStyleSheet("color: #9CA3AF; font-size: 13px;")

        details_row.addWidget(self.lbl_used_ram)
        details_row.addSpacing(20)
        details_row.addWidget(self.lbl_free_ram)
        details_row.addSpacing(20)
        details_row.addWidget(self.lbl_total_ram)
        details_row.addStretch()
        ram_layout.addLayout(details_row)

        layout.addWidget(self.ram_card)

        # Mode Selection Card
        mode_card = QFrame()
        mode_card.setStyleSheet("""
            QFrame {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        mode_layout = QVBoxLayout(mode_card)
        self.lbl_mode_title = QLabel("⚙️ OPTIMALLASHTIRISH REJIMI")
        self.lbl_mode_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #9CA3AF;")
        mode_layout.addWidget(self.lbl_mode_title)

        modes_row = QHBoxLayout()
        self.radio_work = QRadioButton("💼 Ish rejimi (Work Mode) — Ofis va dasturlash uchun barqaror tezlashtirish")
        self.radio_work.setChecked(True)
        self.radio_work.setStyleSheet("color: #F9FAFB; font-size: 13px;")

        self.radio_game = QRadioButton("🎮 O'yin rejimi (Game Mode) — Maksimal erkin RAM va fonni to'xtatish")
        self.radio_game.setStyleSheet("color: #F9FAFB; font-size: 13px;")

        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.radio_work)
        self.mode_group.addButton(self.radio_game)

        modes_row.addWidget(self.radio_work)
        modes_row.addWidget(self.radio_game)
        mode_layout.addLayout(modes_row)

        layout.addWidget(mode_card)

        # Action Button & Result Feedback
        action_layout = QVBoxLayout()
        action_layout.setSpacing(10)

        self.btn_flush = QPushButton("⚡ TEZLASHTIRISH VA RAMNI BO'SHATISH")
        self.btn_flush.setCursor(Qt.PointingHandCursor)
        self.btn_flush.setFixedHeight(48)
        self.btn_flush.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: #FFFFFF;
                font-size: 15px;
                font-weight: 800;
                letter-spacing: 0.5px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
        """)
        self.btn_flush.clicked.connect(self._on_flush_clicked)
        action_layout.addWidget(self.btn_flush)

        self.lbl_feedback = QLabel("")
        self.lbl_feedback.setAlignment(Qt.AlignCenter)
        self.lbl_feedback.setStyleSheet("font-size: 13px; color: #10B981; font-weight: 600;")
        action_layout.addWidget(self.lbl_feedback)

        layout.addLayout(action_layout)
        layout.addStretch()

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

    def update_stats(self) -> None:
        """Fetch real-time memory information."""
        info = MemoryOptimizer.get_memory_info()
        pct = info.get("used_percent", 0)
        self.ram_bar.setValue(pct)
        self.lbl_ram_pct.setText(f"{pct}%")

        if pct > 85:
            self.lbl_ram_pct.setStyleSheet("font-size: 28px; font-weight: 800; color: #EF4444;")
        elif pct > 65:
            self.lbl_ram_pct.setStyleSheet("font-size: 28px; font-weight: 800; color: #F59E0B;")
        else:
            self.lbl_ram_pct.setStyleSheet("font-size: 28px; font-weight: 800; color: #10B981;")

        used_str = format_bytes(info.get("used_bytes", 0))
        free_str = format_bytes(info.get("avail_bytes", 0))
        total_str = format_bytes(info.get("total_bytes", 0))

        self.lbl_used_ram.setText(tr("turbo_used", "Band: {val}", val=used_str))
        self.lbl_free_ram.setText(tr("turbo_free", "Bo'sh: {val}", val=free_str))
        self.lbl_total_ram.setText(tr("turbo_total", "Jami: {val}", val=total_str))

    def _on_flush_clicked(self) -> None:
        self.btn_flush.setEnabled(False)
        self.btn_flush.setText(tr("turbo_flushing", "⏳ Xotira optimallashtirilmoqda..."))
        trimmed, freed = MemoryOptimizer.flush_memory()
        self.update_stats()
        self.btn_flush.setEnabled(True)
        self.btn_flush.setText(tr("btn_turbo_flush", "⚡ TEZLASHTIRISH VA RAMNI BO'SHATISH"))

        mode_name = (
            tr("turbo_mode_game_label", "O'yin rejimi")
            if self.radio_game.isChecked()
            else tr("turbo_mode_work_label", "Ish rejimi")
        )
        if freed > 0:
            self.lbl_feedback.setText(
                tr(
                    "turbo_feedback_freed",
                    "🎉 {mode}: {count} ta jarayon optimallashtirildi, {size} RAM bo'shatildi!",
                    mode=mode_name,
                    count=trimmed,
                    size=format_bytes(freed),
                )
            )
        else:
            self.lbl_feedback.setText(
                tr(
                    "turbo_feedback_optimized",
                    "✅ {mode}: Barcha jarayonlar ishchi to'plami optimallashtirildi.",
                    mode=mode_name,
                )
            )

    def retranslate_ui(self, lang_code: str = "") -> None:
        self.lbl_title.setText(tr("nav_turbo", "⚡ Turbo Boost (Tizimni tezlashtirish)"))
        self.lbl_subtitle.setText(tr("turbo_subtitle", "Operativ xotira (RAM)ni bo'shating va og'ir vazifalar uchun tizimni tezlashtiring"))
        self.lbl_ram_title.setText("💻 " + tr("turbo_ram_title", "OPERATIV XOTIRA (RAM) HOLATI"))
        self.lbl_mode_title.setText("⚙️ " + tr("turbo_mode_title", "OPTIMALLASHTIRISH REJIMI"))
        self.radio_work.setText(tr("turbo_mode_work", "💼 Ish rejimi (Work Mode) — Ofis va dasturlash uchun barqaror tezlashtirish"))
        self.radio_game.setText(tr("turbo_mode_game", "🎮 O'yin rejimi (Game Mode) — Maksimal erkin RAM va fonni to'xtatish"))
        self.btn_flush.setText(tr("btn_turbo_flush", "⚡ TEZLASHTIRISH VA RAMNI BO'SHATISH"))
        self.update_stats()

