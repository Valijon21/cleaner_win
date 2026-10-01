"""
CleanGuard Main Entry Point.
"""

import sys
from PyQt5.QtWidgets import QMessageBox
from cleanguard.app.bootstrap import bootstrap_application
from cleanguard.app.single_instance import SingleInstanceGuard, HANDOVER_WAIT_MS
from cleanguard.localization import tr
from cleanguard.ui.main_window import MainWindow
from cleanguard.utils.logging import setup_logging, get_logger

logger = get_logger("main")


def main() -> int:
    """Run CleanGuard application."""
    guard = SingleInstanceGuard()

    if "--auto-clean" in sys.argv:
        setup_logging()
        # Never run unattended cleanup while the GUI (or another Auto-Care run) is active.
        if not guard.try_acquire():
            logger.info("CleanGuard is already running; scheduled auto-clean skipped.")
            return 0
        try:
            logger.info("Executing scheduled headless auto-clean...")
            from cleanguard.windows.scheduler import AutoCareScheduler
            files_cleaned, bytes_cleaned = AutoCareScheduler.run_auto_clean_now()
            logger.info(f"Auto-clean completed: {files_cleaned} files removed, {bytes_cleaned} bytes freed.")
        finally:
            guard.release()
        return 0

    app = bootstrap_application()

    if not guard.try_acquire():
        if guard.notify_running_instance():
            logger.info("Another CleanGuard instance is running; asked it to show its window.")
            return 0
        # No one answered: the previous instance is probably exiting (e.g. the
        # restart-as-administrator handover), so wait for it to release the lock.
        if not guard.try_acquire(HANDOVER_WAIT_MS):
            QMessageBox.information(
                None,
                "CleanGuard",
                tr("already_running_msg", "CleanGuard allaqachon ishlamoqda."),
            )
            return 0

    try:
        guard.start_listening()
        window = MainWindow()
        guard.activation_requested.connect(window._show_and_activate)
        window.show()
        logger.info("Main window displayed successfully.")
        exit_code = app.exec_()
        logger.info(f"Application event loop terminated with code {exit_code}.")
        return exit_code
    finally:
        guard.release()


if __name__ == "__main__":
    sys.exit(main())
