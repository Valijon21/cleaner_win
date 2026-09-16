"""
Structured logging module for CleanGuard.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

LOGGER_NAME = "cleanguard"
DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(name)s:%(module)s:%(lineno)d] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_default_log_dir() -> str:
    """Resolve directory where logs should be stored."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        log_dir = os.path.join(local_app_data, "CleanGuard", "Logs")
    else:
        # Fallback to user home
        log_dir = os.path.join(os.path.expanduser("~"), ".cleanguard", "logs")

    try:
        os.makedirs(log_dir, exist_ok=True)
    except OSError:
        # If impossible to create, use current directory
        log_dir = os.path.abspath(".")
    return log_dir


def setup_logging(
    log_level: int = logging.INFO,
    log_to_file: bool = True,
    log_dir: Optional[str] = None,
    max_bytes: int = 5 * 1024 * 1024,  # 5 MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    Initialize and configure the root logger for CleanGuard.
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(log_level)
    logger.handlers = []  # Clear previous handlers if re-initialized

    formatter = logging.Formatter(fmt=DEFAULT_LOG_FORMAT, datefmt=DATE_FORMAT)

    # Console Handler (StreamHandler)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    if log_to_file:
        target_dir = log_dir or get_default_log_dir()
        log_file_path = os.path.join(target_dir, "cleanguard.log")
        try:
            file_handler = RotatingFileHandler(
                log_file_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (OSError, IOError) as exc:
            logger.warning(f"Could not initialize file logger at {log_file_path}: {exc}")

    return logger


def get_logger(sub_name: Optional[str] = None) -> logging.Logger:
    """Return a scoped logger under the CleanGuard namespace."""
    if sub_name:
        return logging.getLogger(f"{LOGGER_NAME}.{sub_name}")
    return logging.getLogger(LOGGER_NAME)
