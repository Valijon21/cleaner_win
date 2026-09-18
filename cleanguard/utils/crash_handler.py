"""
CleanGuard Global Crash & Exception Protection.
Intercepts uncaught main thread exceptions, background thread failures, and Qt internal messages.
Generates comprehensive diagnostic crash logs and user-friendly error dialogs.
"""

import sys
import os
import time
import traceback
import threading
from typing import Optional
from cleanguard.utils.logging import get_logger, get_default_log_dir, open_log_folder
from cleanguard.app.version import get_version_string

logger = get_logger("crash_handler")


def write_crash_report(exc_type, exc_value, exc_tb, target_dir: Optional[str] = None) -> str:
    """Generate a detailed standalone crash report file on disk."""
    log_dir = target_dir or get_default_log_dir()
    timestamp_str = time.strftime("%Y-%m-%d_%H-%M-%S")
    crash_file_name = f"crash_{timestamp_str}.log"
    crash_file_path = os.path.join(log_dir, crash_file_name)


    tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
    tb_text = "".join(tb_lines)

    from cleanguard.windows.os_info import get_windows_version
    os_info = get_windows_version()

    report_lines = [
        "=" * 70,
        f"CLEANGUARD CRASH REPORT - {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 70,
        f"Application:   {get_version_string()}",
        f"OS Platform:   {os_info.display_name} ({os_info.architecture}) - Build {os_info.build}",
        f"Python:        {sys.version.split()[0]} ({sys.executable})",
        f"Thread:        {threading.current_thread().name}",
        "=" * 70,
        "TRACEBACK:",
        "=" * 70,
        tb_text.strip(),
        "=" * 70,
        "ACTIVE THREADS:",
        "=" * 70,
    ]

    for th in threading.enumerate():
        report_lines.append(f" - ID: {th.ident}, Name: '{th.name}', Alive: {th.is_alive()}, Daemon: {th.daemon}")

    report_lines.append("=" * 70)
    report_content = "\n".join(report_lines) + "\n"

    try:
        with open(crash_file_path, "w", encoding="utf-8") as f:
            f.write(report_content)
    except Exception as io_err:
        logger.error(f"Failed to write crash dump to {crash_file_path}: {io_err}")

    return crash_file_path


def handle_uncaught_exception(exc_type, exc_value, exc_tb) -> None:
    """Handle uncaught exceptions in the main thread."""
    if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return

    # Log to our enterprise logger (goes to both cleanguard.log and cleanguard_errors.log)
    logger.critical(
        f"FATAL UNCAUGHT EXCEPTION: {exc_type.__name__}: {exc_value}",
        exc_info=(exc_type, exc_value, exc_tb),
    )

    crash_file = write_crash_report(exc_type, exc_value, exc_tb)

    # If Qt GUI is running, display user-friendly alert
    try:
        from PyQt5.QtWidgets import QApplication, QMessageBox, QPushButton
        app = QApplication.instance()
        if app:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("CleanGuard - Fatal Error")
            msg_box.setText(
                f"CleanGuard encountered an unexpected error:\n\n"
                f"{exc_type.__name__}: {exc_value}\n\n"
                f"A diagnostic crash report has been saved to:\n{crash_file}"
            )
            btn_open_folder = msg_box.addButton("Open Logs Folder", QMessageBox.ActionRole)
            btn_copy = msg_box.addButton("Copy Details", QMessageBox.ActionRole)
            msg_box.addButton(QMessageBox.Close)

            msg_box.exec_()
            if msg_box.clickedButton() == btn_open_folder:
                open_log_folder()
            elif msg_box.clickedButton() == btn_copy:
                tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
                clipboard = app.clipboard()
                if clipboard:
                    clipboard.setText(f"CleanGuard Error:\n{tb_text}")
    except Exception as ui_err:
        sys.stderr.write(f"[CleanGuard] Error displaying crash dialog: {ui_err}\n")


def handle_thread_exception(args: threading.ExceptHookArgs) -> None:
    """Handle uncaught exceptions in background threads (Python 3.8+)."""
    if issubclass(args.exc_type, (KeyboardInterrupt, SystemExit)):
        return

    logger.error(
        f"UNHANDLED EXCEPTION in thread '{args.thread.name}': {args.exc_type.__name__}: {args.exc_value}",
        exc_info=(args.exc_type, args.exc_value, args.exc_tb),
    )
    write_crash_report(args.exc_type, args.exc_value, args.exc_tb)


def qt_message_handler(mode, context, message: str) -> None:
    """Route PyQt internal messages to our structured logging system."""
    from PyQt5.QtCore import QtDebugMsg, QtInfoMsg, QtWarningMsg, QtCriticalMsg, QtFatalMsg

    # Filter harmless styling/font noise
    if "QFont::setPointSizeF" in message or "native event filter" in message:
        return

    qt_logger = get_logger("qt")
    ctx_info = f"[{context.file}:{context.line}] " if context.file else ""

    if mode == QtDebugMsg:
        qt_logger.debug(f"{ctx_info}{message}")
    elif mode == QtInfoMsg:
        qt_logger.info(f"{ctx_info}{message}")
    elif mode == QtWarningMsg:
        qt_logger.warning(f"{ctx_info}{message}")
    elif mode == QtCriticalMsg:
        qt_logger.error(f"{ctx_info}{message}")
    elif mode == QtFatalMsg:
        qt_logger.critical(f"FATAL: {ctx_info}{message}")


def install_crash_handlers() -> None:
    """Install global crash hooks across Python main thread, background threads, and Qt."""
    # 1. Main thread excepthook
    sys.excepthook = handle_uncaught_exception

    # 2. Worker thread excepthook
    if hasattr(threading, "excepthook"):
        threading.excepthook = handle_thread_exception

    # 3. Qt message handler
    try:
        from PyQt5.QtCore import qInstallMessageHandler
        qInstallMessageHandler(qt_message_handler)
    except ImportError:
        pass

    logger.info("Crash and exception handlers successfully installed.")
