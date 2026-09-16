"""
CleanGuard Main Entry Point.
"""

import sys
from cleanguard.app.bootstrap import bootstrap_application
from cleanguard.ui.main_window import MainWindow
from cleanguard.utils.logging import get_logger

logger = get_logger("main")


def main() -> int:
    """Run CleanGuard application."""
    app = bootstrap_application()
    window = MainWindow()
    window.show()
    logger.info("Main window displayed.")
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
