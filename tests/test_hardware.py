"""
Tests for Windows Hardware and System Performance Engine.
"""

import pytest
from unittest.mock import patch, MagicMock
from cleanguard.windows.hardware import HardwareEngine


def test_hardware_engine_initialization():
    engine = HardwareEngine()
    assert engine is not None


def test_get_memory_metrics():
    engine = HardwareEngine()
    metrics = engine.get_memory_metrics()
    assert "total_bytes" in metrics
    assert "avail_bytes" in metrics
    assert "load_pct" in metrics
    assert metrics["total_bytes"] > 0
    assert 0 <= metrics["load_pct"] <= 100


def test_get_system_uptime_seconds():
    engine = HardwareEngine()
    uptime = engine.get_system_uptime_seconds()
    assert uptime >= 0


def test_get_cpu_usage_pct_mock():
    engine = HardwareEngine()
    with patch("cleanguard.windows.hardware.ctypes.windll.kernel32.GetSystemTimes") as mock_times:
        mock_times.return_value = 1
        pct = engine.get_cpu_usage_pct()
        assert 0.0 <= pct <= 100.0


def test_get_hardware_specs():
    engine = HardwareEngine()
    specs = engine.get_hardware_specs()
    assert "cpu_name" in specs
    assert "cpu_cores" in specs
    assert specs["cpu_cores"] >= 1
    assert "gpus" in specs
    assert "os_name" in specs
