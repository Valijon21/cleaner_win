"""
Localization Manager for CleanGuard.
Provides dynamic language switching across Uzbek, Russian, and English.
"""

import os
import sys
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

    def unregister_listener(self, callback) -> None:
        """Unregister a language change callback."""
        if callback in self._listeners:
            self._listeners.remove(callback)

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

    def _find_language_file(self, lang_code: str) -> Optional[str]:
        """Find the localization JSON file, accounting for frozen PyInstaller environment."""
        candidate_dirs = [
            os.path.dirname(os.path.abspath(__file__)),
        ]
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidate_dirs.insert(0, os.path.join(meipass, "cleanguard", "localization"))
            candidate_dirs.insert(1, os.path.join(meipass, "localization"))

        for d in candidate_dirs:
            p = os.path.join(d, f"{lang_code}.json")
            if os.path.isfile(p):
                return p

        # Fallback to English
        for d in candidate_dirs:
            p = os.path.join(d, "en.json")
            if os.path.isfile(p):
                return p
        return None

    def _load_language(self, lang_code: str) -> None:
        lang_file = self._find_language_file(lang_code)
        if not lang_file or not os.path.exists(lang_file):
            logger.error(f"Could not locate localization file for '{lang_code}' (or fallback en.json).")
            self._strings = {}
            return

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
