"""
CleanGuard Version and Build Information.
"""

APP_NAME = "CleanGuard"
APP_DISPLAY_NAME = "CleanGuard Professional"
APP_VERSION = "0.1.0"
BUILD_NUMBER = "2026.1"
RELEASE_CHANNEL = "stable"
COPYRIGHT = "© 2026 CleanGuard. All rights reserved."

SUPPORTED_OS_LIST = [
    "Windows 7 SP1 (x86, x64)",
    "Windows 8 (x86, x64)",
    "Windows 8.1 (x86, x64)",
    "Windows 10 (x86, x64)",
    "Windows 11 (x64, ARM64)",
]


def get_version_string() -> str:
    """Return formatted version string."""
    return f"{APP_NAME} v{APP_VERSION} (Build {BUILD_NUMBER})"
