"""
Unit tests for Windows Privileges and UAC Elevation Management.
"""

from cleanguard.windows.privileges import is_user_admin, request_elevation


def test_is_user_admin_boolean():
    """Verify is_user_admin always returns a boolean without throwing."""
    admin = is_user_admin()
    assert isinstance(admin, bool)


def test_request_elevation_dry_check():
    """Verify request_elevation function signature and behavior."""
    # If already admin, returns True immediately
    if is_user_admin():
        assert request_elevation() is True
