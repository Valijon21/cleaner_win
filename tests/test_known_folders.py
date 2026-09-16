"""
Unit tests for Windows Known Folders and Recycle Bin (Phase 3).
"""

import os
from cleanguard.windows.known_folders import (
    get_known_folders,
    KnownFolders,
    KnownFolderResolver,
)
from cleanguard.windows.recycle_bin import (
    query_recycle_bin,
    RecycleBinInfo,
)


def test_get_known_folders():
    folders = get_known_folders()
    assert isinstance(folders, KnownFolders)

    # Windows dir must exist
    assert len(folders.windows) > 0
    assert os.path.exists(folders.windows)

    # System32 must exist
    assert len(folders.system32) > 0
    assert os.path.exists(folders.system32)

    # Temp directories must exist
    assert len(folders.user_temp) > 0
    assert os.path.exists(folders.user_temp)
    assert len(folders.system_temp) > 0

    # User folders
    assert len(folders.local_app_data) > 0
    assert len(folders.program_files) > 0


def test_recycle_bin_query():
    info = query_recycle_bin("C:")
    assert isinstance(info, RecycleBinInfo)
    assert info.total_size >= 0
    assert info.num_items >= 0
