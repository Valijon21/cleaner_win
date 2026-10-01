"""
Static i18n guard: every tr("literal_key") used in the code base must exist in all
language files, and the language files must expose identical key sets with the same
{placeholders}. Otherwise English/Russian users silently see Uzbek fallback text.
"""

import ast
import json
import os
import re
import string

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PKG = os.path.join(ROOT, "cleanguard")
LANGS = ("uz", "en", "ru")


def _load(lang):
    with open(os.path.join(PKG, "localization", f"{lang}.json"), encoding="utf-8") as fh:
        return json.load(fh)


def _used_keys():
    keys = {}
    for dirpath, _, files in os.walk(PKG):
        for name in files:
            if not name.endswith(".py"):
                continue
            path = os.path.join(dirpath, name)
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and getattr(node.func, "id", getattr(node.func, "attr", "")) == "tr"
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)
                ):
                    keys.setdefault(node.args[0].value, os.path.relpath(path, ROOT))
    return keys


def _placeholders(text):
    return {field for _, field, _, _ in string.Formatter().parse(text) if field}


@pytest.mark.parametrize("lang", LANGS)
def test_every_used_key_is_translated(lang):
    data = _load(lang)
    missing = sorted(f"{k} ({where})" for k, where in _used_keys().items() if k not in data)
    assert not missing, f"{lang}.json is missing keys:\n" + "\n".join(missing)


def test_language_files_have_identical_keys():
    sets = {lang: set(_load(lang)) for lang in LANGS}
    base = sets["uz"]
    for lang in ("en", "ru"):
        assert sets[lang] == base, f"{lang}: extra={sorted(sets[lang] - base)} missing={sorted(base - sets[lang])}"


def test_placeholders_match_across_languages():
    uz, others = _load("uz"), {lang: _load(lang) for lang in ("en", "ru")}
    mismatched = []
    for key, text in uz.items():
        for lang, data in others.items():
            if _placeholders(text) != _placeholders(data.get(key, "")):
                mismatched.append(f"{lang}:{key}")
    assert not mismatched, "Placeholder mismatch: " + ", ".join(mismatched)


def test_service_messages_follow_ui_language():
    from cleanguard.localization import get_localization
    from cleanguard.windows.tweaks import BUILTIN_TWEAKS

    loc = get_localization()
    tweak = BUILTIN_TWEAKS[0]
    loc.current_lang = "en"
    loc._load_language("en")
    assert tweak.display_name == _load("en")[f"tweak_{tweak.id}_name"]
    assert re.search(r"[A-Za-z]", tweak.display_name)
    loc.current_lang = "ru"
    loc._load_language("ru")
    assert tweak.display_name == _load("ru")[f"tweak_{tweak.id}_name"]
