"""
Unit tests for Windows MemoryOptimizer.
"""

from cleanguard.windows.memory import MemoryOptimizer


def test_get_memory_info():
    info = MemoryOptimizer.get_memory_info()
    assert isinstance(info, dict)
    assert info["total_bytes"] > 0
    assert info["avail_bytes"] > 0
    assert 0 <= info["used_percent"] <= 100


def test_flush_memory():
    trimmed, freed = MemoryOptimizer.flush_memory()
    assert isinstance(trimmed, int)
    assert isinstance(freed, int)
    assert trimmed >= 0
    assert freed >= 0
