"""
Unit tests for Windows Startup Items Manager.
"""

import os
from unittest.mock import patch, MagicMock
from cleanguard.windows.startup import StartupManager, StartupItem
from cleanguard.core.contracts import RiskLevel


def test_startup_manager_initialization():
    mgr = StartupManager()
    assert mgr is not None


def test_assess_risk_critical_binary():
    mgr = StartupManager()
    assert mgr._assess_risk("ctfmon", r"C:\Windows\System32\ctfmon.exe") == RiskLevel.BLOCKED
    assert mgr._assess_risk("explorer", r"C:\Windows\explorer.exe") == RiskLevel.BLOCKED
    assert mgr._assess_risk("SecurityHealth", r"C:\Windows\System32\SecurityHealthSystray.exe") == RiskLevel.BLOCKED


def test_assess_risk_normal_application():
    mgr = StartupManager()
    assert mgr._assess_risk("Telegram", r"C:\Users\user\AppData\Roaming\Telegram Desktop\Telegram.exe") == RiskLevel.REVIEW
    assert mgr._assess_risk("Spotify", r"C:\Users\user\AppData\Roaming\Spotify\Spotify.exe") == RiskLevel.REVIEW


def test_estimate_impact():
    mgr = StartupManager()
    assert mgr._estimate_impact("Spotify", "Spotify.exe") == "High"
    assert mgr._estimate_impact("Discord", "Discord.exe") == "High"
    assert mgr._estimate_impact("CloudDrive", "clouddrive.exe") == "Medium"
    assert mgr._estimate_impact("LightApp", "light.exe") == "Low"


def test_extract_executable_path():
    mgr = StartupManager()
    assert mgr._extract_executable_path('"C:\\Program Files\\App\\app.exe" --minimized') == "C:\\Program Files\\App\\app.exe"
    assert mgr._extract_executable_path('C:\\App\\app.exe -silent') == "C:\\App\\app.exe"
    assert mgr._extract_executable_path("") == ""


def test_blocked_item_cannot_be_disabled():
    mgr = StartupManager()
    item = StartupItem(
        id="HKCU_RUN_ctfmon",
        name="ctfmon",
        command=r"C:\Windows\System32\ctfmon.exe",
        location_type="HKCU_RUN",
        enabled=True,
        risk_level=RiskLevel.BLOCKED,
        impact="Low",
    )
    success, msg = mgr.set_startup_state(item, False)
    assert success is False
    assert "critical" in msg.lower()
