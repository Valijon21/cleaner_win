"""
Hardware Page: Real-time CPU, RAM, Disk telemetry and hardware specification passport UI.
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QScrollArea,
)
from PyQt5.QtCore import Qt, QTimer
from cleanguard.windows.hardware import HardwareEngine
from cleanguard.utils.formatting import format_bytes, format_duration
from cleanguard.localization import tr
from cleanguard.utils.logging import get_logger

logger = get_logger("ui.hardware")


class HardwarePage(QWidget):
    """Real-time hardware status and system specifications display."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.engine = HardwareEngine()
        self.specs = self.engine.get_hardware_specs()
        self._init_ui()

        # 1.5s refresh timer for live metrics
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_live_metrics)
        self.timer.start(1500)
        self._update_live_metrics()

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
        layout.setSpacing(20)

        # Header Row
        header_row = QHBoxLayout()
        header_text = QVBoxLayout()
        self.lbl_title = QLabel("📊 " + tr("nav_hardware", "Tizim va Apparat ta'minoti monitori"))
        self.lbl_title.setStyleSheet("font-size: 24px; font-weight: 700; color: #F9FAFB;")
        self.lbl_subtitle = QLabel(
            tr("hardware_subtitle", "Protsessor, Tezkor xotira, Disklar va Video karta holatini real vaqtda nazorat qilish")
        )
        self.lbl_subtitle.setStyleSheet("font-size: 13px; color: #9CA3AF;")
        header_text.addWidget(self.lbl_title)
        header_text.addWidget(self.lbl_subtitle)
        header_row.addLayout(header_text)
        header_row.addStretch()

        self.btn_refresh = QPushButton("🔄 " + tr("btn_refresh", "Yangilash"))
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.clicked.connect(self._update_live_metrics)
        header_row.addWidget(self.btn_refresh)
        layout.addLayout(header_row)

        # 3 Live Telemetry Cards
        telemetry_row = QHBoxLayout()
        telemetry_row.setSpacing(16)

        # 1. CPU Card
        card_cpu = QFrame()
        card_cpu.setStyleSheet("background-color: #1F2937; border: 1px solid #374151; border-radius: 10px; padding: 14px;")
        layout_cpu = QVBoxLayout(card_cpu)
        layout_cpu.setSpacing(6)
        self.lbl_cpu_head = QLabel("⚡ " + tr("hw_cpu_load", "CPU Yuklamasi"))
        self.lbl_cpu_head.setStyleSheet("font-size: 14px; font-weight: 600; color: #10B981;")
        layout_cpu.addWidget(self.lbl_cpu_head)

        self.lbl_cpu_val = QLabel("0%")
        self.lbl_cpu_val.setStyleSheet("font-size: 28px; font-weight: 800; color: #F9FAFB;")
        layout_cpu.addWidget(self.lbl_cpu_val)

        self.bar_cpu = QProgressBar()
        self.bar_cpu.setRange(0, 100)
        self.bar_cpu.setTextVisible(False)
        self.bar_cpu.setFixedHeight(8)
        self.bar_cpu.setStyleSheet("""
            QProgressBar { background-color: #374151; border-radius: 4px; }
            QProgressBar::chunk { background-color: #10B981; border-radius: 4px; }
        """)
        layout_cpu.addWidget(self.bar_cpu)

        self.lbl_cpu_desc = QLabel(
            tr(
                "hw_cores_logical",
                "{cores} ta mantiqiy yadro ({mhz} MHz)",
                cores=self.specs.get("cpu_cores", 1),
                mhz=self.specs.get("cpu_mhz", 0),
            )
        )
        self.lbl_cpu_desc.setStyleSheet("font-size: 11px; color: #9CA3AF;")
        layout_cpu.addWidget(self.lbl_cpu_desc)
        telemetry_row.addWidget(card_cpu)

        # 2. RAM Card
        card_ram = QFrame()
        card_ram.setStyleSheet("background-color: #1F2937; border: 1px solid #374151; border-radius: 10px; padding: 14px;")
        layout_ram = QVBoxLayout(card_ram)
        layout_ram.setSpacing(6)
        self.lbl_ram_head = QLabel("🧠 " + tr("hw_ram_load", "RAM Bandligi"))
        self.lbl_ram_head.setStyleSheet("font-size: 14px; font-weight: 600; color: #10B981;")
        layout_ram.addWidget(self.lbl_ram_head)

        self.lbl_ram_val = QLabel("0%")
        self.lbl_ram_val.setStyleSheet("font-size: 28px; font-weight: 800; color: #F9FAFB;")
        layout_ram.addWidget(self.lbl_ram_val)

        self.bar_ram = QProgressBar()
        self.bar_ram.setRange(0, 100)
        self.bar_ram.setTextVisible(False)
        self.bar_ram.setFixedHeight(8)
        self.bar_ram.setStyleSheet("""
            QProgressBar { background-color: #374151; border-radius: 4px; }
            QProgressBar::chunk { background-color: #3B82F6; border-radius: 4px; }
        """)
        layout_ram.addWidget(self.bar_ram)

        self.lbl_ram_desc = QLabel("-- / --")
        self.lbl_ram_desc.setStyleSheet("font-size: 11px; color: #9CA3AF;")
        layout_ram.addWidget(self.lbl_ram_desc)
        telemetry_row.addWidget(card_ram)

        # 3. System Uptime Card
        card_up = QFrame()
        card_up.setStyleSheet("background-color: #1F2937; border: 1px solid #374151; border-radius: 10px; padding: 14px;")
        layout_up = QVBoxLayout(card_up)
        layout_up.setSpacing(6)
        self.lbl_up_head = QLabel("⏱️ " + tr("hw_uptime", "Tizim ish vaqti"))
        self.lbl_up_head.setStyleSheet("font-size: 14px; font-weight: 600; color: #10B981;")
        layout_up.addWidget(self.lbl_up_head)

        self.lbl_uptime_val = QLabel("--")
        self.lbl_uptime_val.setStyleSheet("font-size: 22px; font-weight: 800; color: #F9FAFB;")
        layout_up.addWidget(self.lbl_uptime_val)

        self.lbl_uptime_desc = QLabel(
            tr(
                "hw_active_partitions",
                "Disklar: {count} ta faol bo'lim",
                count=self.specs.get("drives_count", 1),
            )
        )
        self.lbl_uptime_desc.setStyleSheet("font-size: 11px; color: #9CA3AF; margin-top: 14px;")
        layout_up.addWidget(self.lbl_uptime_desc)
        telemetry_row.addWidget(card_up)

        layout.addLayout(telemetry_row)

        # Apparat Ta'minoti Pasporti Card
        card_specs = QFrame()
        card_specs.setStyleSheet("background-color: #1F2937; border: 1px solid #374151; border-radius: 10px; padding: 18px;")
        layout_specs = QVBoxLayout(card_specs)
        layout_specs.setSpacing(14)

        self.lbl_specs_head = QLabel("📋 " + tr("hw_specs_title", "Apparat ta'minoti pasporti (System Specifications)"))
        self.lbl_specs_head.setStyleSheet("font-size: 16px; font-weight: 700; color: #F9FAFB;")
        layout_specs.addWidget(self.lbl_specs_head)

        self.table_specs = QTableWidget()
        self.table_specs.setColumnCount(2)
        self.table_specs.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_specs.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_specs.verticalHeader().setVisible(False)
        self.table_specs.setAlternatingRowColors(True)
        self._populate_specs_table()

        layout_specs.addWidget(self.table_specs)
        layout.addWidget(card_specs)

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

    def _populate_specs_table(self) -> None:
        self.table_specs.setHorizontalHeaderLabels([
            tr("tbl_device_component", "Qurilma / Komponent"),
            tr("tbl_specs_value", "Xususiyatlari"),
        ])

        specs_rows = [
            (tr("hw_comp_cpu", "🖥️ Protsessor (CPU)"), self.specs.get("cpu_name", "--")),
            (
                tr("hw_comp_cores", "⚙️ Yadro va chastota"),
                tr(
                    "hw_cores_logical",
                    "{cores} ta mantiqiy yadro ({mhz} MHz)",
                    cores=self.specs.get("cpu_cores", 1),
                    mhz=self.specs.get("cpu_mhz", 0),
                ),
            ),
            (tr("hw_comp_gpu", "🎮 Video karta (GPU)"), ", ".join(self.specs.get("gpus", []))),
            (tr("hw_comp_motherboard", "🗄️ Asosiy plata (Motherboard)"), self.specs.get("motherboard", "--")),
            (tr("hw_comp_bios", "🔧 BIOS versiyasi"), self.specs.get("bios_version", "--")),
            (
                tr("hw_comp_os", "💻 Operatsion tizim"),
                f"{self.specs.get('os_name', '--')} ({self.specs.get('os_arch', '')}) - Build {self.specs.get('os_build', '')}",
            ),
        ]

        self.table_specs.setRowCount(len(specs_rows))
        for row, (comp, desc) in enumerate(specs_rows):
            it_comp = QTableWidgetItem(f"  {comp}")
            it_desc = QTableWidgetItem(f"  {desc}")
            self.table_specs.setItem(row, 0, it_comp)
            self.table_specs.setItem(row, 1, it_desc)

    def _update_live_metrics(self) -> None:
        """Fetch real-time metrics and update UI counters."""
        # 1. CPU %
        cpu_pct = self.engine.get_cpu_usage_pct()
        self.lbl_cpu_val.setText(f"{cpu_pct:.1f}%")
        self.bar_cpu.setValue(int(cpu_pct))

        # 2. RAM %
        mem = self.engine.get_memory_metrics()
        ram_pct = mem.get("load_pct", 0)
        self.lbl_ram_val.setText(f"{ram_pct}%")
        self.bar_ram.setValue(int(ram_pct))
        used_str = format_bytes(mem.get("used_bytes", 0))
        tot_str = format_bytes(mem.get("total_bytes", 0))
        self.lbl_ram_desc.setText(f"{tr('drive_storage_used', 'Ishlatilmoqda')}: {used_str} / {tot_str}")

        # 3. Uptime
        uptime_sec = self.engine.get_system_uptime_seconds()
        self.lbl_uptime_val.setText(format_duration(uptime_sec))

    def retranslate_ui(self, lang_code: str = "") -> None:
        self.lbl_title.setText("📊 " + tr("nav_hardware", "Tizim va Apparat ta'minoti monitori"))
        self.lbl_subtitle.setText(tr("hardware_subtitle", "Protsessor, Tezkor xotira, Disklar va Video karta holatini real vaqtda nazorat qilish"))
        self.btn_refresh.setText("🔄 " + tr("btn_refresh", "Yangilash"))
        self.lbl_cpu_head.setText("⚡ " + tr("hw_cpu_load", "CPU Yuklamasi"))
        self.lbl_ram_head.setText("🧠 " + tr("hw_ram_load", "RAM Bandligi"))
        self.lbl_up_head.setText("⏱️ " + tr("hw_uptime", "Tizim ish vaqti"))
        self.lbl_specs_head.setText("📋 " + tr("hw_specs_title", "Apparat ta'minoti pasporti (System Specifications)"))
        self.lbl_cpu_desc.setText(
            tr(
                "hw_cores_logical",
                "{cores} ta mantiqiy yadro ({mhz} MHz)",
                cores=self.specs.get("cpu_cores", 1),
                mhz=self.specs.get("cpu_mhz", 0),
            )
        )
        self.lbl_uptime_desc.setText(
            tr(
                "hw_active_partitions",
                "Disklar: {count} ta faol bo'lim",
                count=self.specs.get("drives_count", 1),
            )
        )
        self._populate_specs_table()
