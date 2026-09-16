"""
CleanGuard Application Bootstrapper.
Initializes logging, DPI scaling, database, configuration, and localization.
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from cleanguard.app.version import get_version_string
from cleanguard.utils.logging import setup_logging, get_logger
from cleanguard.core.config import ConfigManager
from cleanguard.localization import get_localization
from cleanguard.database.db import DatabaseManager
from cleanguard.windows.os_info import get_windows_version

logger = get_logger("bootstrap")


def bootstrap_application() -> QApplication:
    """Pre-flight configuration and QApplication instantiation."""
    # 1. Initialize Logging
    setup_logging()
    logger.info(f"Starting {get_version_string()}")

    # 2. Check Windows OS compatibility
    os_info = get_windows_version()
    logger.info(f"Platform: {os_info.display_name} ({os_info.architecture}) - Build {os_info.build}")

    # 3. Enable DPI Scaling attributes (Critical for Windows 10/11 4K displays)
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # 4. Initialize Database
    DatabaseManager()

    # 5. Initialize Configuration and Localization
    cfg = ConfigManager()
    loc = get_localization()
    loc.set_language(cfg.get("language", "uz"))

    # 6. Instantiate Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("CleanGuard")
    app.setApplicationDisplayName("CleanGuard Professional")

    return app
