"""
CleanGuard Main Entry Point.
"""

import sys
from cleanguard.app.bootstrap import bootstrap_application
from cleanguard.ui.main_window import MainWindow
from cleanguard.utils.logging import setup_logging, get_logger

logger = get_logger("main")


def main() -> int:
    """Run CleanGuard application."""
    if "--auto-clean" in sys.argv:
        setup_logging()
        logger.info("Executing scheduled headless auto-clean...")
        from cleanguard.windows.scheduler import AutoCareScheduler
        files_cleaned, bytes_cleaned = AutoCareScheduler.run_auto_clean_now()
        logger.info(f"Auto-clean completed: {files_cleaned} files removed, {bytes_cleaned} bytes freed.")
        return 0

    app = bootstrap_application()
    window = MainWindow()
    window.show()
    logger.info("Main window displayed successfully.")
    exit_code = app.exec_()
    logger.info(f"Application event loop terminated with code {exit_code}.")
    return exit_code



if __name__ == "__main__":
    sys.exit(main())
