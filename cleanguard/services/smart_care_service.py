"""
Smart Care Service: All-in-One 1-Click System Optimization Pipeline.
Sequentially coordinates:
1. System Junk & Cache Cleaning (Safe items)
2. Safe Registry Repair (MUI Cache, MRU traces with automatic .reg backup)
3. Turbo RAM Optimization (Flush standby memory working sets)
4. Network DNS Cache Purge (Refresh resolver cache)
5. Windows Update Cache Purge (If admin privileges available)
"""

import time
from dataclasses import dataclass
from typing import Optional, List
from PyQt5.QtCore import QThread, pyqtSignal

from cleanguard.core.contracts import ScanItem, RiskLevel
from cleanguard.core.scanner.engine import ScannerEngine
from cleanguard.core.cleaner.executor import CleanupExecutor
from cleanguard.windows.registry_cleaner import SafeRegistryCleaner
from cleanguard.windows.memory import flush_memory
from cleanguard.windows.network import flush_dns
from cleanguard.windows.updates import WindowsUpdateCleaner
from cleanguard.windows.privileges import is_user_admin
from cleanguard.database.db import DatabaseManager
from cleanguard.utils.logging import get_logger

logger = get_logger("services.smart_care")


@dataclass
class SmartCareResult:
    junk_bytes_reclaimed: int = 0
    junk_files_deleted: int = 0
    registry_issues_fixed: int = 0
    ram_bytes_freed: int = 0
    dns_flushed: bool = False
    update_bytes_freed: int = 0
    duration_seconds: float = 0.0

    @property
    def junk_cleaned_bytes(self) -> int:
        return self.junk_bytes_reclaimed

    @property
    def ram_freed_bytes(self) -> int:
        return self.ram_bytes_freed

    @property
    def update_cache_cleaned_bytes(self) -> int:
        return self.update_bytes_freed

    @property
    def total_space_reclaimed_bytes(self) -> int:
        return self.junk_bytes_reclaimed + self.update_bytes_freed


class SmartCareWorker(QThread):
    """Asynchronous background worker executing 1-Click All-in-One Smart Care."""
    stage_changed = pyqtSignal(str, int)  # (stage_title, percent 0-100)
    finished = pyqtSignal(object)  # Emits SmartCareResult
    error = pyqtSignal(str)

    def __init__(self, db_manager: Optional[DatabaseManager] = None, parent=None):
        super().__init__(parent)
        self.db = db_manager or DatabaseManager()
        self.scanner = ScannerEngine()
        self.cleaner = CleanupExecutor()
        self.reg_cleaner = SafeRegistryCleaner()
        self.update_cleaner = WindowsUpdateCleaner()

    def run(self):
        start_time = time.time()
        result = SmartCareResult()

        try:
            # Stage 1: Junk File Cleaning (0% - 40%)
            self.stage_changed.emit("1/4: Tizim axlatlari va keshni tozalash...", 10)
            summary, items = self.scanner.scan_all()
            safe_items = [it for it in items if it.risk_level == RiskLevel.SAFE]

            if safe_items:
                self.stage_changed.emit(f"1/4: {len(safe_items)} ta xavfsiz fayllar tozalanmoqda...", 25)
                cleanup_summary = self.cleaner.execute(safe_items)
                result.junk_bytes_reclaimed = cleanup_summary.bytes_recovered
                result.junk_files_deleted = cleanup_summary.files_deleted
            self.stage_changed.emit("1/4: Tizim axlatlari tozalandi.", 40)

            # Stage 2: Registry Repair with Automated Backup (40% - 70%)
            self.stage_changed.emit("2/4: Reestr xatolarini tekshirish va zaxiralash...", 50)
            mui_issues = self.reg_cleaner.scan_mui_cache()
            mru_issues = self.reg_cleaner.scan_run_mru()
            all_issues = mui_issues + mru_issues

            if all_issues:
                # Automatic backup before cleaning
                self.reg_cleaner.create_backup(all_issues)
                cleaned, _ = self.reg_cleaner.clean_issues(all_issues)
                result.registry_issues_fixed = cleaned
            self.stage_changed.emit("2/4: Reestr xatoliklari tuzatildi.", 70)

            # Stage 3: Turbo RAM Flush (70% - 85%)
            self.stage_changed.emit("3/4: RAM tezkor xotirasi bo'shatilmoqda...", 75)
            trimmed_count, freed_mem = flush_memory()
            result.ram_bytes_freed = freed_mem
            self.stage_changed.emit("3/4: RAM kesh bo'shatildi.", 85)

            # Stage 4: DNS Cache Flush & Windows Update (85% - 100%)
            self.stage_changed.emit("4/4: DNS tarmoq keshini yangilash...", 90)
            success_dns, _ = flush_dns()
            result.dns_flushed = success_dns

            if is_user_admin():
                success_upd, freed_upd, _ = self.update_cleaner.clean_update_download_cache()
                if success_upd:
                    result.update_bytes_freed = freed_upd

            result.duration_seconds = round(time.time() - start_time, 2)
            self.stage_changed.emit("Bajarildi! Tizim to'liq optimallandi.", 100)
            self.finished.emit(result)

        except Exception as ex:
            logger.error("Smart Care pipeline encountered error: %s", ex)
            self.error.emit(str(ex))
