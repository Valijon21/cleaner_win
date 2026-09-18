"""
CleanGuard Application Bootstrapper.
Initializes logging, DPI scaling, database, configuration, and localization.
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from cleanguard.app.version import get_version_string
from cleanguard.utils.logging import setup_logging, get_logger, shutdown_logging
from cleanguard.utils.crash_handler import install_crash_handlers
from cleanguard.core.config import ConfigManager
from cleanguard.localization import get_localization
from cleanguard.database.db import DatabaseManager
from cleanguard.windows.os_info import get_windows_version
from cleanguard.windows.privileges import is_user_admin

logger = get_logger("bootstrap")


def bootstrap_application() -> QApplication:
    """Pre-flight configuration and QApplication instantiation."""
    # 1. Initialize Logging & Crash Protection
    setup_logging()
    install_crash_handlers()
    logger.info(f"Starting {get_version_string()}")

    # 2. Check Windows OS compatibility and privileges
    os_info = get_windows_version()
    admin_state = "ELEVATED (Admin)" if is_user_admin() else "STANDARD (Non-Admin)"
    logger.info(f"Platform: {os_info.display_name} ({os_info.architecture}) - Build {os_info.build} [{admin_state}]")

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

    # Set application-wide brand icon
    try:
        from cleanguard.ui.tray import get_app_icon
        app.setWindowIcon(get_app_icon())
    except Exception:
        pass

    # Hook graceful shutdown of logging listener
    app.aboutToQuit.connect(shutdown_logging)

    return app

