"""
Unit tests for CleanGuard Multi-Theme Engine and Live Theme Switching.
"""

import sys
import pytest
from PyQt5.QtWidgets import QApplication
from cleanguard.ui.theme import (
    THEMES,
    THEME_PALETTES,
    get_theme_stylesheet,
    get_available_themes,
    DARK_STYLESHEET,
)
from cleanguard.ui.settings_page import SettingsPage
from cleanguard.core.config import ConfigManager


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    for w in app.topLevelWidgets():
        w.close()
        w.deleteLater()
    app.processEvents()


def test_theme_registry_and_palettes():
    """Verify all 4 themes are registered with valid palettes and tokens."""
    themes = get_available_themes()
    assert len(themes) == 4
    assert set(themes.keys()) == {"dark", "midnight", "stealth", "light"}

    required_tokens = [
        "bg_main",
        "bg_sidebar",
        "bg_card",
        "border_color",
        "border_focus",
        "text_primary",
        "text_secondary",
        "accent_primary",
    ]

    for theme_id in themes:
        assert theme_id in THEME_PALETTES
        palette = THEME_PALETTES[theme_id]
        for token in required_tokens:
            assert token in palette, f"Token {token} missing in palette {theme_id}"


def test_theme_stylesheet_generation():
    """Verify each theme generates valid non-empty QSS stylesheets."""
    assert len(DARK_STYLESHEET) > 500
    for theme_id in THEMES:
        qss = get_theme_stylesheet(theme_id)
        assert len(qss) > 500
        assert "QMainWindow" in qss
        assert "QPushButton#PrimaryButton" in qss
        assert "QFrame#Sidebar" in qss


def test_settings_page_theme_switching(qapp, tmp_path):
    """Verify SettingsPage combo triggers theme_changed signal and saves to config."""
    config_file = str(tmp_path / "test_config.json")
    config = ConfigManager(config_path=config_file)
    settings = SettingsPage(config=config)

    emitted_themes = []
    settings.theme_changed.connect(lambda t: emitted_themes.append(t))

    # Test switching to midnight
    midnight_idx = settings.combo_theme.findData("midnight")
    assert midnight_idx >= 0
    settings.combo_theme.setCurrentIndex(midnight_idx)

    assert "midnight" in emitted_themes
    assert config.get("theme") == "midnight"

    # Test switching to light
    light_idx = settings.combo_theme.findData("light")
    assert light_idx >= 0
    settings.combo_theme.setCurrentIndex(light_idx)

    assert "light" in emitted_themes
    assert config.get("theme") == "light"
