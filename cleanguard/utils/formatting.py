"""
Formatting utilities for sizes, numbers, and timestamps.
"""

import time
from datetime import datetime
from typing import Union


def format_bytes(bytes_count: Union[int, float], precision: int = 2) -> str:
    """
    Format a byte count into a human-readable string (B, KB, MB, GB, TB).
    """
    if bytes_count < 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(bytes_count)
    unit_idx = 0

    while size >= 1024.0 and unit_idx < len(units) - 1:
        size /= 1024.0
        unit_idx += 1

    if unit_idx == 0:
        return f"{int(size)} B"
    return f"{size:.{precision}f} {units[unit_idx]}"


def format_number(count: int) -> str:
    """Format integer with thousands separator."""
    return f"{count:,}"


def format_duration(seconds: float) -> str:
    """Format duration in seconds into a friendly string."""
    if seconds < 1.0:
        return f"{int(seconds * 1000)} ms"
    elif seconds < 60.0:
        return f"{seconds:.1f} s"
    else:
        minutes = int(seconds // 60)
        rem_sec = seconds % 60
        return f"{minutes}m {rem_sec:.0f}s"


def format_timestamp(timestamp: Union[float, int]) -> str:
    """Format Unix timestamp to human-readable date string."""
    if not timestamp or timestamp <= 0:
        return "Unknown"
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def calculate_age_days(timestamp: Union[float, int]) -> float:
    """Calculate file age in days based on modified or created timestamp."""
    if not timestamp or timestamp <= 0:
        return 0.0
    now = time.time()
    diff = now - timestamp
    if diff <= 0:
        return 0.0
    return diff / 86400.0
