"""
Network Page: Internet & Network Latency Booster UI.
"""

from typing import List, Dict
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from cleanguard.windows.network import NetworkOptimizer
from cleanguard.windows.privileges import is_user_admin, request_elevation
from cleanguard.localization import tr
from cleanguard.utils.logging import get_logger

logger = get_logger("ui.network")


class PingWorker(QThread):
    """Background worker for testing latency without blocking UI."""
    finished = pyqtSignal(bool, float, str)

    def run(self):
        ok, latency, desc = NetworkOptimizer.check_ping("1.1.1.1")
        self.finished.emit(ok, latency, desc)


class NetworkPage(QWidget):
    """Interface for Windows internet acceleration and DNS diagnostics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ping_worker = None
        self._init_ui()
        self.refresh_all()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        # Header
        header_row = QHBoxLayout()
        header_text = QVBoxLayout()
        self.lbl_title = QLabel("🚀 " + tr("nav_network", "Internet va Tarmoqni tezlashtirish"))
        self.lbl_title.setStyleSheet("font-size: 24px; font-weight: 700; color: #F9FAFB;")
        self.lbl_subtitle = QLabel(
            tr("network_subtitle", "Tarmoq parametrlarini optimallashtirish, DNS keshini tozalash va kechikishni (Ping) pasaytirish")
        )
        self.lbl_subtitle.setStyleSheet("font-size: 13px; color: #9CA3AF;")
        header_text.addWidget(self.lbl_title)
        header_text.addWidget(self.lbl_subtitle)
        header_row.addLayout(header_text)
        header_row.addStretch()

        self.btn_refresh = QPushButton("🔄 " + tr("btn_refresh", "Yangilash"))
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.refresh_all)
        header_row.addWidget(self.btn_refresh)
        layout.addLayout(header_row)

        # Top Section: Ping Card + 1-Click Boost Card
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        # 1. Ping / Latency Card
        card_ping = QFrame()
        card_ping.setStyleSheet("background-color: #1F2937; border: 1px solid #374151; border-radius: 10px; padding: 14px;")
        ping_layout = QVBoxLayout(card_ping)
        ping_layout.setSpacing(8)

        lbl_ping_title = QLabel("📡 " + tr("network_ping_title", "Tarmoq kechikishi (Ping)"))
        lbl_ping_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #10B981;")
        ping_layout.addWidget(lbl_ping_title)

        self.lbl_ping_val = QLabel("-- ms")
        self.lbl_ping_val.setStyleSheet("font-size: 32px; font-weight: 800; color: #34D399;")
        ping_layout.addWidget(self.lbl_ping_val)

        self.lbl_ping_target = QLabel("Server: Cloudflare Fast DNS (1.1.1.1)")
        self.lbl_ping_target.setStyleSheet("font-size: 11px; color: #9CA3AF;")
        ping_layout.addWidget(self.lbl_ping_target)

        self.btn_ping_test = QPushButton("⚡ " + tr("btn_check_ping", "Pingni o'lchash"))
        self.btn_ping_test.setCursor(Qt.PointingHandCursor)
        self.btn_ping_test.clicked.connect(self._run_ping_test)
        ping_layout.addWidget(self.btn_ping_test)
        cards_row.addWidget(card_ping, stretch=1)

        # 2. Optimization Status & Action Card
        card_boost = QFrame()
        card_boost.setStyleSheet("background-color: #1F2937; border: 1px solid #374151; border-radius: 10px; padding: 14px;")
        boost_layout = QVBoxLayout(card_boost)
        boost_layout.setSpacing(8)

        lbl_boost_title = QLabel("⚡ " + tr("network_turbo_title", "Tarmoq tezlatgich (Network Accelerator)"))
        lbl_boost_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #10B981;")
        boost_layout.addWidget(lbl_boost_title)

        self.lbl_throttling_status = QLabel("Holat: Tekshirilmoqda...")
        self.lbl_throttling_status.setStyleSheet("font-size: 13px; color: #F9FAFB;")
        boost_layout.addWidget(self.lbl_throttling_status)

        boost_btn_row = QHBoxLayout()
        self.btn_optimize = QPushButton("🚀 " + tr("btn_boost_network", "Internetni tezlashtirish"))
        self.btn_optimize.setStyleSheet("background-color: #10B981; color: white; font-weight: 700; padding: 7px 14px; border-radius: 6px;")
        self.btn_optimize.setCursor(Qt.PointingHandCursor)
        self.btn_optimize.clicked.connect(self._on_boost_clicked)
        boost_btn_row.addWidget(self.btn_optimize)

        self.btn_flush_dns = QPushButton("🧹 " + tr("btn_flush_dns", "DNS keshini tozalash"))
        self.btn_flush_dns.setCursor(Qt.PointingHandCursor)
        self.btn_flush_dns.clicked.connect(self._on_flush_dns_clicked)
        boost_btn_row.addWidget(self.btn_flush_dns)

        boost_layout.addLayout(boost_btn_row)
        cards_row.addWidget(card_boost, stretch=2)

        layout.addLayout(cards_row)

        # Bottom: Network Adapters Table
        lbl_adapters_header = QLabel("🌐 " + tr("network_adapters_title", "Faol tarmoq adapterlari:"))
        lbl_adapters_header.setStyleSheet("font-size: 14px; font-weight: 600; color: #F9FAFB; margin-top: 10px;")
        layout.addWidget(lbl_adapters_header)

        self.table_adapters = QTableWidget()
        self.table_adapters.setColumnCount(3)
        self.table_adapters.setHorizontalHeaderLabels(["Adapter nomi", "IPv4 manzili", "Holati"])
        self.table_adapters.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_adapters.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_adapters.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_adapters.verticalHeader().setVisible(False)
        self.table_adapters.setAlternatingRowColors(True)
        layout.addWidget(self.table_adapters)

    def refresh_all(self) -> None:
        self._refresh_throttling_status()
        self._refresh_adapters()
        self._run_ping_test()

    def _refresh_throttling_status(self) -> None:
        is_opt = NetworkOptimizer.is_throttling_disabled()
        if is_opt:
            self.lbl_throttling_status.setText("✅ Tarmoq cheklovi o'chiq (Maksimal tezlik faol)")
            self.lbl_throttling_status.setStyleSheet("color: #34D399; font-size: 13px; font-weight: 600;")
        else:
            self.lbl_throttling_status.setText("⚠️ Windows multimedia tarmoq throttlingi faol (Sekinlashuv mumkin)")
            self.lbl_throttling_status.setStyleSheet("color: #FBBF24; font-size: 13px;")

    def _refresh_adapters(self) -> None:
        adapters = NetworkOptimizer.get_network_interfaces()
        self.table_adapters.setRowCount(len(adapters))
        for row, it in enumerate(adapters):
            self.table_adapters.setItem(row, 0, QTableWidgetItem(f"  {it.get('name', 'Adapter')}"))
            ip_item = QTableWidgetItem(it.get("ip", "--"))
            ip_item.setTextAlignment(Qt.AlignCenter)
            self.table_adapters.setItem(row, 1, ip_item)
            stat_item = QTableWidgetItem(f"✅ {it.get('status', 'Online')}")
            stat_item.setTextAlignment(Qt.AlignCenter)
            self.table_adapters.setItem(row, 2, stat_item)

    def _run_ping_test(self) -> None:
        self.lbl_ping_val.setText("O'lchanmoqda...")
        self.btn_ping_test.setEnabled(False)
        self.ping_worker = PingWorker(self)
        self.ping_worker.finished.connect(self._on_ping_finished)
        self.ping_worker.start()

    def _on_ping_finished(self, ok: bool, latency: float, desc: str) -> None:
        self.btn_ping_test.setEnabled(True)
        if ok and latency < 999:
            self.lbl_ping_val.setText(f"{latency:.0f} ms")
            if latency < 50:
                self.lbl_ping_val.setStyleSheet("font-size: 32px; font-weight: 800; color: #34D399;")
            elif latency < 100:
                self.lbl_ping_val.setStyleSheet("font-size: 32px; font-weight: 800; color: #FBBF24;")
            else:
                self.lbl_ping_val.setStyleSheet("font-size: 32px; font-weight: 800; color: #EF4444;")
        else:
            self.lbl_ping_val.setText("Timeout")
            self.lbl_ping_val.setStyleSheet("font-size: 26px; font-weight: 700; color: #EF4444;")

    def _on_boost_clicked(self) -> None:
        if not is_user_admin():
            reply = QMessageBox.question(
                self,
                "Administrator huquqi",
                "TCP/IP va tarmoq throttlingini optimallashtirish uchun Administrator huquqi talab qilinadi.\nCleanGuard ni Administrator rejimida qayta ishga tushirilsinmi?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
                request_elevation()
            return

        ok_tcp, msg_tcp = NetworkOptimizer.optimize_tcp_ip()
        ok_th, msg_th = NetworkOptimizer.disable_network_throttling()

        if ok_tcp and ok_th:
            QMessageBox.information(self, "Bajarildi", "Tarmoq muvaffaqiyatli tezlashtirildi!\n- TCP/IP Auto-Tuning va RSS yoqildi.\n- Windows tarmoq throttlingi o'chirildi.")
        else:
            QMessageBox.warning(self, "Ogohlantirish", f"Optimizatsiyada ayrim xatoliklar:\n{msg_tcp}\n{msg_th}")

        self._refresh_throttling_status()
        self._run_ping_test()

    def _on_flush_dns_clicked(self) -> None:
        ok, msg = NetworkOptimizer.flush_dns()
        if ok:
            QMessageBox.information(self, "DNS Tozalandi", msg)
        else:
            QMessageBox.warning(self, "Xatolik", msg)

    def retranslate_ui(self, lang_code: str = "") -> None:
        self.lbl_title.setText("🚀 " + tr("nav_network", "Internet va Tarmoqni tezlashtirish"))
        self.lbl_subtitle.setText(tr("network_subtitle", "Tarmoq parametrlarini optimallashtirish, DNS keshini tozalash va kechikishni (Ping) pasaytirish"))
        self.btn_refresh.setText("🔄 " + tr("btn_refresh", "Yangilash"))
