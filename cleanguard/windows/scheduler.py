"""
Scheduled Auto-Care Engine: Integrates with Windows Task Scheduler (schtasks.exe)
and provides headless automated safe maintenance.
"""

import os
import sys
import subprocess
from typing import Tuple, Optional
from cleanguard.core.scanner.engine import ScannerEngine
from cleanguard.core.cleaner.planner import CleanupPlanner
from cleanguard.core.cleaner.executor import CleanupExecutor
from cleanguard.core.contracts import RiskLevel, CleanupStrategy
from cleanguard.core.safety import SafetyEngine
from cleanguard.database.db import DatabaseManager
from cleanguard.database.repositories import HistoryRepository
from cleanguard.utils.logging import get_logger

logger = get_logger("windows.scheduler")

TASK_NAME = "CleanGuardAutoCare"


class AutoCareScheduler:
    """Controls Windows Task Scheduler jobs for CleanGuard background maintenance."""

    @staticmethod
    def get_task_command() -> str:
        """Construct the command line string for scheduled execution."""
        if getattr(sys, "frozen", False):
            return f'"{sys.executable}" --auto-clean'
        # Python script mode
        python_exe = sys.executable
        return f'"{python_exe}" -m cleanguard.app.main --auto-clean'

    @classmethod
    def is_scheduled(cls) -> Tuple[bool, Optional[str]]:
        """
        Check if CleanGuardAutoCare task exists in Windows Task Scheduler.
        Returns (is_present, info_string).
        """
        if sys.platform != "win32":
            return False, "Not supported on non-Windows platform."

        cmd = ["schtasks", "/Query", "/TN", TASK_NAME, "/FO", "LIST"]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if proc.returncode == 0:
                # Find Next Run Time or Status
                lines = proc.stdout.splitlines()
                info = "Faol"
                for line in lines:
                    if "Next Run Time:" in line:
                        info = line.split(":", 1)[1].strip()
                        break
                return True, info
            return False, None
        except Exception as ex:
            logger.debug("Failed querying schtasks: %s", ex)
            return False, None

    @classmethod
    def enable_schedule(
        cls,
        frequency: str = "WEEKLY",
        day: str = "SUN",
        time_str: str = "12:00",
    ) -> Tuple[bool, str]:
        """
        Create or update scheduled auto-clean task in Windows Task Scheduler.
        Args:
            frequency: 'WEEKLY' or 'DAILY'
            day: 'SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'
            time_str: 'HH:MM' 24-hour format
        """
        if sys.platform != "win32":
            return False, "Windows Task Scheduler faqat Windows tizimlarida ishlaydi."

        tr_cmd = cls.get_task_command()
        cmd = [
            "schtasks",
            "/Create",
            "/TN",
            TASK_NAME,
            "/TR",
            tr_cmd,
            "/SC",
            frequency.upper(),
            "/ST",
            time_str,
            "/F",
        ]
        if frequency.upper() == "WEEKLY":
            cmd.extend(["/D", day.upper()])

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if proc.returncode == 0:
                logger.info("AutoCare scheduled successfully: %s %s %s", frequency, day, time_str)
                return True, f"Avtomatik tozalash muvaffaqiyatli rejalashtirildi ({frequency} {time_str})."
            else:
                err = proc.stderr.strip() or proc.stdout.strip()
                logger.warning("Failed creating schtask: %s", err)
                if "access is denied" in err.lower():
                    return False, "Vazifani rejalashtirish uchun Administrator huquqi talab qilinadi."
                return False, f"Rejalashtirishda xatolik: {err}"
        except Exception as ex:
            logger.error("Exception enabling schedule: %s", ex)
            return False, str(ex)

    @classmethod
    def disable_schedule(cls) -> Tuple[bool, str]:
        """Delete CleanGuardAutoCare task from Windows Task Scheduler."""
        if sys.platform != "win32":
            return False, "Not supported on non-Windows platform."

        cmd = ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if proc.returncode == 0:
                logger.info("CleanGuardAutoCare schedule deleted.")
                return True, "Rejalashtirilgan tozalash bekor qilindi."
            else:
                err = proc.stderr.strip() or proc.stdout.strip()
                if "cannot find" in err.lower():
                    return True, "Vazifa avvaldan mavjud emas."
                return False, f"O'chirishda xatolik: {err}"
        except Exception as ex:
            return False, str(ex)

    @classmethod
    def run_auto_clean_now(cls) -> Tuple[int, int]:
        """
        Execute silent headless scanning and cleanup of strictly SAFE items.
        Returns: (files_removed, bytes_recovered).
        """
        logger.info("Initiating Headless Auto-Care maintenance...")
        safety_engine = SafetyEngine()
        db = DatabaseManager()
        history_repo = HistoryRepository(db)

        # 1. Scan default safe junk categories
        engine = ScannerEngine(safety_engine=safety_engine)
        summary, items = engine.scan_all()

        # 2. Filter strictly RiskLevel.SAFE
        safe_items = [it for it in items if it.risk_level == RiskLevel.SAFE]
        logger.info("Auto-Care identified %d safe items (%d total items found).", len(safe_items), len(items))

        if not safe_items:
            logger.info("No safe items to clean. Auto-Care complete.")
            return 0, 0

        # 3. Build plan and execute cleanup
        planned, _ = CleanupPlanner.build_plan(
            items=safe_items,
            default_strategy=CleanupStrategy.SAFE_DELETE,
        )
        executor = CleanupExecutor(safety_engine=safety_engine)
        clean_summary = executor.execute(planned)

        # 4. Record history session
        try:
            history_repo.record_cleanup_session(clean_summary)
            logger.info("Recorded Auto-Care cleanup session in database.")
        except Exception as ex:
            logger.warning("Failed saving session to database: %s", ex)

        return clean_summary.files_deleted, clean_summary.bytes_recovered
