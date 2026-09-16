"""
Unit tests for Localization (Phase 13).
"""

import os
import json
from cleanguard.localization.manager import LocalizationManager, tr, SUPPORTED_LANGUAGES


def test_all_language_files_exist_and_have_keys():
    base_dir = os.path.join(os.path.dirname(__file__), "..", "cleanguard", "localization")

    loaded_dicts = {}
    for lang in ["en", "ru", "uz"]:
        path = os.path.join(base_dir, f"{lang}.json")
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert isinstance(data, dict)
            assert len(data) > 10
            loaded_dicts[lang] = set(data.keys())

    # Check key consistency across languages
    en_keys = loaded_dicts["en"]
    for lang, keys in loaded_dicts.items():
        missing = en_keys - keys
        assert not missing, f"Language {lang} is missing keys: {missing}"


def test_localization_translation_and_formatting():
    loc = LocalizationManager(current_lang="uz")
    assert "CleanGuard" in loc.tr("app_name")

    formatted = loc.tr("confirm_cleanup_msg", items_count=5, size_str="25 MB")
    assert "5" in formatted
    assert "25 MB" in formatted

    # Switch to Russian
    loc.set_language("ru")
    assert "Сканировать ПК" in loc.tr("btn_scan_now")

    # Switch to English
    loc.set_language("en")
    assert "Scan PC Now" in loc.tr("btn_scan_now")
