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
from typing import Optional
from PyQt5.QtCore import QThread, pyqtSignal

from cleanguard.core.scanner.engine import ScannerEngine
from cleanguard.core.cleaner.executor import CleanupExecutor
from cleanguard.core.cleaner.planner import CleanupPlanner
from cleanguard.windows.registry_cleaner import SafeRegistryCleaner
from cleanguard.windows.memory import flush_memory
from cleanguard.windows.network import flush_dns
from cleanguard.windows.updates import WindowsUpdateCleaner
from cleanguard.windows.privileges import is_user_admin
from cleanguard.database.db import DatabaseManager
from cleanguard.database.repositories import HistoryRepository
from cleanguard.localization import tr
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
            self.stage_changed.emit(tr("smart_care_stage_junk", "1/4: Tizim axlatlari va keshni tozalash..."), 10)
            summary, items = self.scanner.scan_all()
            self._record(lambda repo: repo.record_scan_session(summary))
            # Unattended mode: SAFE only, never the Recycle Bin or privacy history.
            safe_items = CleanupPlanner.select_unattended(items)

            if safe_items:
                self.stage_changed.emit(
                    tr("smart_care_stage_junk_count", "1/4: {count} ta xavfsiz fayl tozalanmoqda...", count=len(safe_items)),
                    25,
                )
                planned, _ = CleanupPlanner.build_plan(safe_items)
                cleanup_summary = self.cleaner.execute(planned, scan_id=summary.scan_id)
                result.junk_bytes_reclaimed = cleanup_summary.bytes_recovered
                result.junk_files_deleted = cleanup_summary.files_deleted
                self._record(lambda repo: repo.record_cleanup_session(cleanup_summary))
            self.stage_changed.emit(tr("smart_care_stage_junk_done", "1/4: Tizim axlatlari tozalandi."), 40)

            # Stage 2: Registry Repair with Automated Backup (40% - 70%)
            self.stage_changed.emit(tr("smart_care_stage_registry", "2/4: Reestr xatolarini tekshirish va zaxiralash..."), 50)
            mui_issues = self.reg_cleaner.scan_mui_cache()
            mru_issues = self.reg_cleaner.scan_run_mru()
            all_issues = mui_issues + mru_issues

            if all_issues:
                # clean_issues() writes the .reg backup itself and refuses to touch
                # the registry if that backup cannot be created.
                cleaned, _failed, _backup = self.reg_cleaner.clean_issues(all_issues, backup=True)
                result.registry_issues_fixed = cleaned
            self.stage_changed.emit(tr("smart_care_stage_registry_done", "2/4: Reestr xatoliklari tuzatildi."), 70)

            # Stage 3: Turbo RAM Flush (70% - 85%)
            self.stage_changed.emit(tr("smart_care_stage_ram", "3/4: RAM tezkor xotirasi bo'shatilmoqda..."), 75)
            trimmed_count, freed_mem = flush_memory()
            result.ram_bytes_freed = freed_mem
            self.stage_changed.emit(tr("smart_care_stage_ram_done", "3/4: RAM kesh bo'shatildi."), 85)

            # Stage 4: DNS Cache Flush & Windows Update (85% - 100%)
            self.stage_changed.emit(tr("smart_care_stage_dns", "4/4: DNS tarmoq keshini yangilash..."), 90)
            success_dns, _ = flush_dns()
            result.dns_flushed = success_dns

            if is_user_admin():
                success_upd, freed_upd, _ = self.update_cleaner.clean_update_download_cache()
                if success_upd:
                    result.update_bytes_freed = freed_upd

            result.duration_seconds = round(time.time() - start_time, 2)
            self.stage_changed.emit(tr("smart_care_stage_done", "Bajarildi! Tizim to'liq optimallandi."), 100)
            self.finished.emit(result)

        except Exception as ex:
            logger.error("Smart Care pipeline encountered error: %s", ex, exc_info=True)
            self.error.emit(str(ex))

    def _record(self, action) -> None:
        """Persist history so Smart Care results appear on the Dashboard and History pages."""
        try:
            action(HistoryRepository(self.db))
        except Exception as exc:
            logger.warning("Could not persist Smart Care history: %s", exc)
