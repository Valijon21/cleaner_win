"""
Unit and Integration tests for Scanner Engine (Phase 5).
"""

import os
import tempfile
import pytest
from cleanguard.core.scanner.base import CancellationToken, BaseScanner
from cleanguard.core.scanner.temp_scanner import TempScanner
from cleanguard.core.scanner.engine import ScannerEngine
from cleanguard.core.contracts import CleanCategory, RiskLevel, ScanItem
from cleanguard.core.safety import SafetyEngine


class MockDirectoryScanner(BaseScanner):
    """Custom test scanner pointing to a controlled directory fixture."""

    def __init__(self, target_dir: str, safety_engine: SafetyEngine):
        super().__init__(safety_engine)
        self.target_dir = target_dir

    @property
    def scanner_id(self) -> str:
        return "mock_scanner"

    @property
    def display_name(self) -> str:
        return "Mock Scanner"

    @property
    def category(self) -> CleanCategory:
        return CleanCategory.TEMP_FILES

    def get_allowed_roots(self):
        return [self.target_dir]

    def scan(self, cancel_token=None, progress_callback=None):
        return self.safe_scan_directory(
            root_dir=self.target_dir,
            cancel_token=cancel_token,
            progress_callback=progress_callback,
            rule_id="RULE-MOCK",
        )


def test_cancellation_token():
    token = CancellationToken()
    assert token.is_cancelled() is False
    token.cancel()
    assert token.is_cancelled() is True
    token.reset()
    assert token.is_cancelled() is False


def test_mock_directory_scanning():
    safety = SafetyEngine()
    with tempfile.TemporaryDirectory() as td:
        # Create test temporary files
        f1 = os.path.join(td, "file1.tmp")
        f2 = os.path.join(td, "file2.bak")
        with open(f1, "w") as f:
            f.write("content 1")
        with open(f2, "w") as f:
            f.write("content 222")

        scanner = MockDirectoryScanner(td, safety)
        items = scanner.scan()

        assert len(items) == 2
        names = [it.name for it in items]
        assert "file1.tmp" in names
        assert "file2.bak" in names


def test_scanner_cancellation_stops_walk():
    safety = SafetyEngine()
    with tempfile.TemporaryDirectory() as td:
        # Create 50 files
        for i in range(50):
            with open(os.path.join(td, f"file_{i}.tmp"), "w") as f:
                f.write(f"data {i}")

        scanner = MockDirectoryScanner(td, safety)
        token = CancellationToken()
        token.cancel()  # Pre-cancelled

        items = scanner.scan(cancel_token=token)
        assert len(items) == 0


def test_scanner_engine_orchestration():
    safety = SafetyEngine()
    engine = ScannerEngine(safety_engine=safety, max_threads=2)
    # Ensure all scanners are registered
    assert len(engine.scanners) >= 5

    # Run quick scan with pre-cancelled token to verify orchestration without long IO
    token = CancellationToken()
    token.cancel()
    summary, items = engine.scan_all(cancel_token=token)

    assert summary.scan_id is not None
    assert isinstance(items, list)
