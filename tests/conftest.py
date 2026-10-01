"""
Pytest configuration and common fixtures.
"""

import os
import sys
import pytest
from PyQt5.QtWidgets import QApplication

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture(scope="session")
def qapp():
    """Shared QApplication instance across all test modules."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture(autouse=True)
def _default_ui_language():
    """
    Pin the UI language for every test. Service messages are localized, so a test
    that switched language (e.g. test_localization) must not leak into the next one.
    """
    from cleanguard.localization import get_localization

    loc = get_localization()
    previous = loc.current_lang
    # Load strings directly: set_language() would also persist the choice into the
    # developer's real %LOCALAPPDATA%\CleanGuard\config.json.
    loc.current_lang = "uz"
    loc._load_language("uz")
    yield
    loc.current_lang = previous
    loc._load_language(previous)
