"""
Application configuration management for CleanGuard.
"""

import os
import json
import threading
from typing import Dict, Any

DEFAULT_CONFIG: Dict[str, Any] = {
    "language": "uz",  # Default language: Uzbek
    "theme": "dark",   # Default theme: Dark
    "auto_scan_on_startup": False,
    "minimize_to_tray": False,
    "confirm_before_cleanup": True,
    "recycle_bin_retention_days": 30,
    "log_file_retention_days": 14,
    "min_file_age_hours": 24,  # Safe default: files must be at least 24h old unless purely temp
    "smart_pyinstaller_cleanup": True,  # Smart cleanup for orphaned PyInstaller temp caches
    "pyinstaller_min_age_hours": 24,  # Threshold for orphaned PyInstaller caches
    "scan_threads": 4,
    "custom_protected_paths": [],
    "ignored_paths": [],
    "enabled_categories": [
        "temp_files",
        "app_cache",
        "system_logs",
        "browser_cache",
        "recycle_bin",
        "crash_dumps",
        "thumbnail_cache",
    ],
}


class ConfigManager:
    """Thread-safe configuration manager."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        # If an explicit config_path is specified, create an isolated instance
        config_path = kwargs.get("config_path") or (args[0] if args else None)
        if config_path is not None:
            inst = super(ConfigManager, cls).__new__(cls)
            inst._initialized = False
            return inst

        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, config_path: str = None):
        if getattr(self, "_initialized", False) and config_path is None:
            return
        self._lock = threading.Lock()
        self.config_path = config_path or self._resolve_config_path()
        self._data: Dict[str, Any] = dict(DEFAULT_CONFIG)
        self.load()
        self._initialized = True

    @staticmethod
    def _resolve_config_path() -> str:
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            base_dir = os.path.join(local_app_data, "CleanGuard")
        else:
            base_dir = os.path.join(os.path.expanduser("~"), ".cleanguard")
        try:
            os.makedirs(base_dir, exist_ok=True)
        except OSError:
            base_dir = "."
        return os.path.join(base_dir, "config.json")

    def load(self) -> None:
        """Load configuration from disk."""
        with self._lock:
            if os.path.exists(self.config_path):
                try:
                    with open(self.config_path, "r", encoding="utf-8") as f:
                        loaded = json.load(f)
                        if isinstance(loaded, dict):
                            self._data.update(loaded)
                except (OSError, IOError, ValueError):
                    pass

    def save(self) -> None:
        """Persist configuration to disk."""
        with self._lock:
            try:
                os.makedirs(os.path.dirname(os.path.abspath(self.config_path)), exist_ok=True)
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, indent=2, ensure_ascii=False)
            except (OSError, IOError):
                pass

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any, auto_save: bool = True) -> None:
        with self._lock:
            self._data[key] = value
        if auto_save:
            self.save()

    def get_all(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._data)
