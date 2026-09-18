"""
Localization Manager for CleanGuard.
Provides dynamic language switching across Uzbek, Russian, and English.
"""

import os
import json
from typing import Dict, Optional
from cleanguard.core.config import ConfigManager
from cleanguard.utils.logging import get_logger

logger = get_logger("localization")

SUPPORTED_LANGUAGES = {
    "uz": "O'zbekcha",
    "ru": "Русский",
    "en": "English",
}


class LocalizationManager:
    """Manages loaded language strings and string formatting."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LocalizationManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, current_lang: Optional[str] = None):
        if getattr(self, "_initialized", False):
            return
        self.config = ConfigManager()
        self.current_lang = current_lang or self.config.get("language", "uz")
        self._strings: Dict[str, str] = {}
        self._listeners = []
        self._load_language(self.current_lang)
        self._initialized = True

    def register_listener(self, callback) -> None:
        """Register a callback invoked when the UI language changes."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def set_language(self, lang_code: str) -> None:
        """Switch active UI language and notify listeners."""
        if lang_code in SUPPORTED_LANGUAGES:
            self.current_lang = lang_code
            self._load_language(lang_code)
            self.config.set("language", lang_code)
            for cb in list(self._listeners):
                try:
                    cb(lang_code)
                except Exception as exc:
                    logger.warning(f"Error in language listener callback: {exc}")

    def _load_language(self, lang_code: str) -> None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        lang_file = os.path.join(base_dir, f"{lang_code}.json")

        # Fallback to en.json if requested file does not exist
        if not os.path.exists(lang_file):
            lang_file = os.path.join(base_dir, "en.json")

        try:
            with open(lang_file, "r", encoding="utf-8") as f:
                self._strings = json.load(f)
        except Exception as exc:
            logger.error(f"Failed to load localization file {lang_file}: {exc}")
            self._strings = {}

    def tr(self, key: str, default: Optional[str] = None, **kwargs) -> str:
        """Translate key and format template values."""
        text = self._strings.get(key, default if default is not None else key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text


_loc_manager: Optional[LocalizationManager] = None


def get_localization() -> LocalizationManager:
    """Singleton getter for localization manager."""
    global _loc_manager
    if _loc_manager is None:
        _loc_manager = LocalizationManager()
    return _loc_manager


def tr(key: str, default: Optional[str] = None, **kwargs) -> str:
    """Convenience translation function."""
    return get_localization().tr(key, default=default, **kwargs)
