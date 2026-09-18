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
