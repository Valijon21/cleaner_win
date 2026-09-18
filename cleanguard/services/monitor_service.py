"""
Storage Monitor Service: Background drive space monitor and intelligent alert trigger.
Strictly compatible with Windows 7 SP1 through Windows 11.
"""

import time
from typing import Dict, Optional, Set
from PyQt5.QtCore import QThread, pyqtSignal
from cleanguard.windows.drives import enumerate_drives
from cleanguard.core.contracts import DriveInfo
from cleanguard.utils.logging import get_logger

logger = get_logger("monitor_service")


class StorageMonitorService(QThread):
    """
    Background daemon thread monitoring drive free space and emitting alerts
    when storage drops below critical thresholds.
    """
    low_space_detected = pyqtSignal(object)  # Emits DriveInfo
    drives_updated = pyqtSignal(list)       # Emits List[DriveInfo]

    def __init__(
        self,
        check_interval_seconds: int = 1800,  # 30 minutes default
        threshold_percentage: float = 15.0,  # Alert if free space <= 15%
        threshold_min_bytes: int = 10 * 1024 * 1024 * 1024,  # or free <= 10 GB
        cooldown_seconds: int = 7200,        # Don't re-alert same drive within 2 hours
        parent=None,
    ):
        super().__init__(parent)
        self.check_interval = check_interval_seconds
        self.threshold_percentage = threshold_percentage
        self.threshold_min_bytes = threshold_min_bytes
        self.cooldown_seconds = cooldown_seconds
        self._is_running = True
        self._last_alerted: Dict[str, float] = {}

    def stop(self) -> None:
        """Gracefully request thread shutdown and wait for exit."""
        self._is_running = False
        if self.isRunning():
            self.wait(2000)

    def check_drives_now(self) -> Set[str]:
        """
        Perform an immediate check across all fixed drives.
        Returns a set of drive letters that breached threshold.
        """
        breached: Set[str] = set()
        try:
            drives = enumerate_drives()
            self.drives_updated.emit(drives)
            now = time.time()

            for drive in drives:
                if not drive.is_ready or drive.drive_type != "Fixed Disk":
                    continue

                free_pct = 100.0 - drive.used_percentage
                is_critical = (free_pct <= self.threshold_percentage) or (drive.free_bytes <= self.threshold_min_bytes)

                if is_critical:
                    last_alert = self._last_alerted.get(drive.letter, 0.0)
                    if (now - last_alert) >= self.cooldown_seconds:
                        self._last_alerted[drive.letter] = now
                        logger.warning(
                            f"Drive {drive.letter} low space warning: {free_pct:.1f}% free ({drive.free_bytes} bytes)."
                        )
                        self.low_space_detected.emit(drive)
                        breached.add(drive.letter)
        except Exception as exc:
            logger.error(f"StorageMonitor encountered exception checking drives: {exc}")
        return breached

    def run(self) -> None:
        logger.info(f"StorageMonitorService started with {self.check_interval}s check interval.")
        while self._is_running:
            self.check_drives_now()

            # Responsive sleep loop checking _is_running every 50ms
            elapsed = 0.0
            while self._is_running and elapsed < self.check_interval:
                time.sleep(0.05)
                elapsed += 0.05

        logger.info("StorageMonitorService stopped.")

