"""
CleanGuard Enterprise Logging System.
Provides thread-safe queue-based logging, rotating dual-file sinks (general + dedicated error log),
ANSI colored console output, in-memory ring buffer for UI diagnostics, and execution step tracking.
"""

import os
import sys
import time
import logging
import threading
import queue
from collections import deque
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler, QueueHandler, QueueListener
from typing import Optional, List, Dict, Any

LOGGER_NAME = "cleanguard"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
CONSOLE_FORMAT = "%(asctime)s.%(msecs)03d [%(levelname)-7s] [%(threadName)-12s] [%(name)s:%(funcName)s:%(lineno)d] %(message)s"
FILE_FORMAT = "%(asctime)s.%(msecs)03d [%(levelname)-7s] [%(threadName)-12s] [%(name)s:%(funcName)s:%(lineno)d] %(message)s"

# Global references for runtime control
_queue_listener: Optional[QueueListener] = None
_memory_handler: Optional["MemoryLogHandler"] = None
_log_queue: Optional[queue.Queue] = None
_current_log_level: int = logging.INFO


class ColorFormatter(logging.Formatter):
    """Console formatter with ANSI color coding for improved terminal legibility."""

    COLORS = {
        logging.DEBUG: "\033[36m",      # Cyan
        logging.INFO: "\033[32m",       # Green
        logging.WARNING: "\033[33m",    # Yellow
        logging.ERROR: "\033[31m",      # Red
        logging.CRITICAL: "\033[35;1m", # Bold Magenta
    }
    RESET = "\033[0m"

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        super().__init__(fmt=fmt, datefmt=datefmt)
        try:
            self.use_colors = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
        except Exception:
            self.use_colors = False

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        if self.use_colors:
            color = self.COLORS.get(record.levelno, "")
            if color:
                return f"{color}{message}{self.RESET}"
        return message



class MemoryLogHandler(logging.Handler):
    """
    Thread-safe in-memory circular buffer of recent log records.
    Allows real-time inspection in the GUI without touching disk files.
    """

    def __init__(self, capacity: int = 1000):
        super().__init__()
        self.capacity = capacity
        self.records: deque = deque(maxlen=capacity)
        self._buffer_lock = threading.RLock()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            entry = {
                "timestamp": record.created,
                "asctime": getattr(record, "asctime", time.strftime(DATE_FORMAT, time.localtime(record.created))),
                "level": record.levelname,
                "levelno": record.levelno,
                "name": record.name,
                "module": record.module,
                "funcName": record.funcName,
                "lineno": record.lineno,
                "threadName": record.threadName,
                "message": record.getMessage(),
                "formatted": msg,
                "exc_text": getattr(record, "exc_text", "") or "",
            }
            with self._buffer_lock:
                self.records.append(entry)
        except Exception:
            self.handleError(record)

    def get_entries(self, min_level: int = logging.DEBUG) -> List[Dict[str, Any]]:
        with self._buffer_lock:
            return [e for e in self.records if e["levelno"] >= min_level]

    def clear(self) -> None:
        with self._buffer_lock:
            self.records.clear()



def get_default_log_dir() -> str:
    """Resolve directory where logs should be stored."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        log_dir = os.path.join(local_app_data, "CleanGuard", "Logs")
    else:
        log_dir = os.path.join(os.path.expanduser("~"), ".cleanguard", "logs")

    try:
        os.makedirs(log_dir, exist_ok=True)
    except OSError:
        log_dir = os.path.abspath("logs")
        os.makedirs(log_dir, exist_ok=True)
    return log_dir


def setup_logging(
    log_level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_dir: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    Initialize high-performance queue-based logging for CleanGuard.
    All background threads write to an in-memory queue, processed asynchronously
    by a dedicated listener. Eliminates console corruption and file I/O lock contention.
    """
    global _queue_listener, _memory_handler, _log_queue, _current_log_level

    # Stop any previous listener
    shutdown_logging()

    _current_log_level = log_level
    root_logger = logging.getLogger(LOGGER_NAME)
    root_logger.setLevel(logging.DEBUG)  # Root catches all; handlers filter
    root_logger.propagate = False        # Do not propagate to python root logger
    root_logger.handlers = []

    # 1. Prepare Target Sinks
    sinks: List[logging.Handler] = []

    # Console Sink
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_formatter = ColorFormatter(fmt=CONSOLE_FORMAT, datefmt=DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        sinks.append(console_handler)


    file_formatter = logging.Formatter(fmt=FILE_FORMAT, datefmt=DATE_FORMAT)

    # File Sinks
    target_dir = log_dir or get_default_log_dir()
    if log_to_file:
        try:
            # Main general log file (captures all events >= configured level)
            main_log_path = os.path.join(target_dir, "cleanguard.log")
            main_file_handler = RotatingFileHandler(
                main_log_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            main_file_handler.setLevel(log_level)
            main_file_handler.setFormatter(file_formatter)
            sinks.append(main_file_handler)

            # Dedicated error log file (captures ONLY WARNING, ERROR, CRITICAL)
            error_log_path = os.path.join(target_dir, "cleanguard_errors.log")
            error_file_handler = RotatingFileHandler(
                error_log_path,
                maxBytes=5 * 1024 * 1024,  # 5 MB
                backupCount=3,
                encoding="utf-8",
            )
            error_file_handler.setLevel(logging.WARNING)
            error_file_handler.setFormatter(file_formatter)
            sinks.append(error_file_handler)
        except (OSError, IOError) as exc:
            sys.stderr.write(f"[CleanGuard] Could not initialize file logging: {exc}\n")

    # In-Memory Ring Buffer Sink (for live GUI viewer)
    _memory_handler = MemoryLogHandler(capacity=1000)
    _memory_handler.setLevel(logging.DEBUG)
    _memory_handler.setFormatter(file_formatter)
    sinks.append(_memory_handler)

    # 2. Setup Queue & QueueListener
    _log_queue = queue.Queue(-1)
    queue_handler = QueueHandler(_log_queue)
    root_logger.addHandler(queue_handler)

    _queue_listener = QueueListener(_log_queue, *sinks, respect_handler_level=True)
    _queue_listener.start()

    return root_logger


def get_logger(sub_name: Optional[str] = None) -> logging.Logger:
    """Return a scoped logger under the CleanGuard namespace."""
    if sub_name:
        return logging.getLogger(f"{LOGGER_NAME}.{sub_name}")
    return logging.getLogger(LOGGER_NAME)


def set_log_level(level: int) -> None:
    """Dynamically update logging verbosity across console and general file handlers."""
    global _current_log_level, _queue_listener
    _current_log_level = level
    if _queue_listener and _queue_listener.handlers:
        for handler in _queue_listener.handlers:
            if not isinstance(handler, MemoryLogHandler) and getattr(handler, "level", 0) < logging.WARNING:
                handler.setLevel(level)


def get_current_log_level() -> int:
    """Return the active log level."""
    return _current_log_level


def get_memory_logs(min_level: int = logging.DEBUG) -> List[Dict[str, Any]]:
    """Retrieve captured in-memory logs for UI display."""
    if _memory_handler:
        return _memory_handler.get_entries(min_level)
    return []


def clear_memory_logs() -> None:
    """Clear in-memory logs."""
    if _memory_handler:
        _memory_handler.clear()


def open_log_folder() -> bool:
    """Open log directory in Windows File Explorer."""
    log_dir = get_default_log_dir()
    try:
        if os.name == "nt":
            os.startfile(log_dir)  # type: ignore
        else:
            import subprocess
            subprocess.Popen(["xdg-open", log_dir])
        return True
    except Exception as exc:
        get_logger("logging").error(f"Failed to open log folder '{log_dir}': {exc}")
        return False


def get_log_file_paths() -> Dict[str, str]:
    """Return paths of active log files."""
    target_dir = get_default_log_dir()
    return {
        "general": os.path.join(target_dir, "cleanguard.log"),
        "errors": os.path.join(target_dir, "cleanguard_errors.log"),
    }


def shutdown_logging() -> None:
    """Safely flush and stop the background logging listener on application exit."""
    global _queue_listener
    if _queue_listener:
        try:
            handlers = list(_queue_listener.handlers)
            _queue_listener.stop()
            for h in handlers:
                try:
                    h.flush()
                    h.close()
                except Exception:
                    pass
        except Exception:
            pass
        _queue_listener = None






@contextmanager
def log_step(step_name: str, logger: Optional[logging.Logger] = None, **metadata):
    """
    Context manager to trace execution steps with duration and automatic error reporting.
    Usage:
        with log_step("Scan Temp Files", logger=logger, files_scanned=100):
            # perform operation
    """
    log = logger or get_logger("step")
    meta_str = " | ".join(f"{k}={v}" for k, v in metadata.items())
    meta_suffix = f" ({meta_str})" if meta_str else ""
    log.info(f"▶ [STEP START] {step_name}{meta_suffix}")
    start_time = time.perf_counter()
    try:
        yield
        elapsed = time.perf_counter() - start_time
        log.info(f"✔ [STEP COMPLETE] {step_name} in {elapsed:.3f}s")
    except Exception as exc:
        elapsed = time.perf_counter() - start_time
        log.error(f"✖ [STEP FAILED] {step_name} after {elapsed:.3f}s with error: {exc}", exc_info=True)
        raise
