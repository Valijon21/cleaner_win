"""
Tests for Windows Network and Internet Optimizer.
"""

import pytest
from unittest.mock import patch, MagicMock
from cleanguard.windows.network import NetworkOptimizer


def test_flush_dns_mock():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="Successfully flushed DNS Resolver Cache.", stderr="")
        ok, msg = NetworkOptimizer.flush_dns()
        assert ok is True
        assert "muvaffaqiyatli" in msg


def test_optimize_tcp_ip_admin_required():
    with patch("cleanguard.windows.network.is_user_admin", return_value=False):
        ok, msg = NetworkOptimizer.optimize_tcp_ip()
        assert ok is False
        assert "Administrator" in msg


def test_optimize_tcp_ip_success():
    with patch("cleanguard.windows.network.is_user_admin", return_value=True), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="Ok.", stderr="")
        ok, msg = NetworkOptimizer.optimize_tcp_ip()
        assert ok is True
        assert "muvaffaqiyatli" in msg


def test_is_throttling_disabled_mock():
    with patch("cleanguard.windows.network.winreg") as mock_winreg:
        mock_winreg.OpenKey.return_value.__enter__.return_value = MagicMock()
        mock_winreg.QueryValueEx.return_value = (0xFFFFFFFF, 4)
        assert NetworkOptimizer.is_throttling_disabled() is True

        mock_winreg.QueryValueEx.return_value = (10, 4)
        assert NetworkOptimizer.is_throttling_disabled() is False


def test_disable_network_throttling_admin():
    with patch("cleanguard.windows.network.is_user_admin", return_value=False):
        ok, msg = NetworkOptimizer.disable_network_throttling()
        assert ok is False
        assert "Administrator" in msg


def test_disable_network_throttling_success():
    with patch("cleanguard.windows.network.is_user_admin", return_value=True), \
         patch("cleanguard.windows.network.winreg") as mock_winreg:
        mock_winreg.CreateKeyEx.return_value.__enter__.return_value = MagicMock()
        ok, msg = NetworkOptimizer.disable_network_throttling()
        assert ok is True
        assert "olib tashlandi" in msg


def test_check_ping_mock():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Reply from 1.1.1.1: bytes=32 time=14ms TTL=57\nAverage = 14ms",
            stderr="",
        )
        ok, lat, desc = NetworkOptimizer.check_ping("1.1.1.1")
        assert ok is True
        assert lat == 14.0
        assert "14 ms" in desc


def test_get_network_interfaces_mock():
    ipconfig_out = """
Wireless LAN adapter Wi-Fi:
   Connection-specific DNS Suffix  . :
   IPv4 Address. . . . . . . . . . . : 192.168.1.105
   Subnet Mask . . . . . . . . . . . : 255.255.255.0
"""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=ipconfig_out, stderr="")
        adapters = NetworkOptimizer.get_network_interfaces()
        assert len(adapters) == 1
        assert "Wi-Fi" in adapters[0]["name"]
        assert adapters[0]["ip"] == "192.168.1.105"
