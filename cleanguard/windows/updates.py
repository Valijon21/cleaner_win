"""
Windows Update and WinSxS Component Cleanup Manager.
Reclaims significant storage (10-25+ GB) by cleaning obsolete Windows Update download caches
and executing official Microsoft DISM Component Store cleanup.
"""

import os
import subprocess
from typing import Tuple, Optional, Dict, Any
from cleanguard.windows.privileges import is_user_admin
from cleanguard.utils.logging import get_logger

logger = get_logger("windows.updates")


def _get_dir_size(path: str) -> int:
    """Calculate directory size catching OS errors safely."""
    total = 0
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_file(follow_symlinks=False):
                        total += entry.stat(follow_symlinks=False).st_size
                    elif entry.is_dir(follow_symlinks=False):
                        total += _get_dir_size(entry.path)
                except OSError:
                    pass
    except OSError:
        pass
    return total


class WindowsUpdateCleaner:
    """Manages Windows Update cache purging and WinSxS Component Store optimization."""

    def __init__(self, download_dir: Optional[str] = None, delivery_optimization_cache: Optional[str] = None):
        windir = os.environ.get("SystemRoot") or os.environ.get("windir") or r"C:\Windows"
        self.download_dir = download_dir or os.path.join(windir, "SoftwareDistribution", "Download")
        self.software_distribution_download = self.download_dir
        self.delivery_optimization_cache = delivery_optimization_cache or os.path.join(
            windir, "ServiceProfiles", "NetworkService", "AppData", "Local", "Microsoft", "Windows", "DeliveryOptimization", "Cache"
        )

    def get_cache_size(self) -> int:
        """Calculate total reclaimable bytes across Windows Update download caches."""
        total = 0
        if os.path.isdir(self.software_distribution_download):
            total += _get_dir_size(self.software_distribution_download)
        if os.path.isdir(self.delivery_optimization_cache):
            total += _get_dir_size(self.delivery_optimization_cache)
        return total

    def clean_update_download_cache(self, check_admin: bool = True) -> Tuple[bool, int, str]:
        """
        Delete cached Windows Update installation files from SoftwareDistribution\\Download.
        Requires Administrator privileges.
        """
        if check_admin and not is_user_admin():
            return False, 0, "Administrator privileges required to clean Windows Update download cache."

        bytes_reclaimed = 0
        errors = []

        targets = [self.software_distribution_download, self.delivery_optimization_cache]
        for target_dir in targets:
            if not os.path.isdir(target_dir):
                continue
            try:
                for root, dirs, files in os.walk(target_dir, topdown=False):
                    for name in files:
                        filepath = os.path.join(root, name)
                        try:
                            sz = os.path.getsize(filepath)
                            os.remove(filepath)
                            bytes_reclaimed += sz
                        except OSError as e:
                            errors.append(str(e))
                    for name in dirs:
                        dirpath = os.path.join(root, name)
                        try:
                            os.rmdir(dirpath)
                        except OSError:
                            pass
            except Exception as ex:
                logger.warning(f"Error accessing update directory {target_dir}: {ex}")
                errors.append(str(ex))

        msg = f"Successfully purged Windows Update cache ({bytes_reclaimed} bytes reclaimed)."
        if errors:
            msg += f" Note: {len(errors)} active or locked files were skipped safely."
        return True, bytes_reclaimed, msg

    def run_dism_component_cleanup(self, reset_base: bool = False) -> Tuple[bool, str]:
        """
        Execute Microsoft official DISM StartComponentCleanup on WinSxS.
        Reclaims gigabytes of superseded Windows Update service packs and manifests.
        """
        if not is_user_admin():
            return False, "Administrator privileges required to run DISM Component Store cleanup."

        try:
            cmd = ["dism.exe", "/Online", "/Cleanup-Image", "/StartComponentCleanup"]
            if reset_base:
                cmd.append("/ResetBase")

            logger.info("Executing DISM command: %s", " ".join(cmd))
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if proc.returncode == 0:
                logger.info("DISM Component Cleanup completed successfully.")
                return True, "DISM Component Store cleanup completed successfully."
            else:
                err_text = " ".join(filter(None, [proc.stdout.strip(), proc.stderr.strip()])) or f"DISM returned code {proc.returncode}"
                logger.error("DISM Component Cleanup failed: %s", err_text)
                return False, err_text
        except subprocess.TimeoutExpired:
            return False, "DISM Component Cleanup timed out after 10 minutes."
        except Exception as e:
            return False, f"Unexpected error executing DISM: {e}"
