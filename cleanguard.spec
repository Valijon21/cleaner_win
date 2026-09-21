# -*- mode: python ; coding: utf-8 -*-
"""
CleanGuard Professional - PyInstaller Build Specification.
Compiles the application into a standalone Windows executable with
embedded resources, UAC elevation manifest, and high-DPI awareness.
"""

import os
import sys

block_cipher = None
PROJECT_ROOT = os.path.abspath(SPECPATH)

# Generate or verify file_version_info.txt
version_file = os.path.join(PROJECT_ROOT, "file_version_info.txt")
try:
    from scripts.version_info import generate_version_info_file
    generate_version_info_file(version_file)
except Exception as exc:
    print(f"Notice: Version info generator note: {exc}")

datas = [
    (os.path.join(PROJECT_ROOT, "assets"), "assets"),
    (os.path.join(PROJECT_ROOT, "cleanguard", "localization", "*.json"), os.path.join("cleanguard", "localization")),
    (os.path.join(PROJECT_ROOT, "README.md"), "."),
    (os.path.join(PROJECT_ROOT, "LICENSE"), "."),
]

hidden_imports = [
    "PyQt5",
    "PyQt5.QtCore",
    "PyQt5.QtGui",
    "PyQt5.QtWidgets",
    "sqlite3",
    "ctypes",
    "ctypes.wintypes",
    "winreg",
    "cleanguard",
    "cleanguard.app",
    "cleanguard.app.bootstrap",
    "cleanguard.app.version",
    "cleanguard.core",
    "cleanguard.core.config",
    "cleanguard.core.contracts",
    "cleanguard.security",
    "cleanguard.security.path_guard",
    "cleanguard.security.protected_paths",
    "cleanguard.security.risk_engine",
    "cleanguard.security.pyinstaller_tracker",
    "cleanguard.windows",
    "cleanguard.windows.drives",
    "cleanguard.windows.hardware",
    "cleanguard.windows.known_folders",
    "cleanguard.windows.memory",
    "cleanguard.windows.network",
    "cleanguard.windows.os_info",
    "cleanguard.windows.privileges",
    "cleanguard.windows.recycle_bin",
    "cleanguard.windows.registry_cleaner",
    "cleanguard.windows.restore_point",
    "cleanguard.windows.scheduler",
    "cleanguard.windows.shell",
    "cleanguard.windows.startup",
    "cleanguard.windows.tweaks",
    "cleanguard.windows.uninstaller",
    "cleanguard.windows.updates",
    "cleanguard.services",
    "cleanguard.services.cleanup_service",
    "cleanguard.services.export_service",
    "cleanguard.services.monitor_service",
    "cleanguard.services.scan_service",
    "cleanguard.services.smart_care_service",
    "cleanguard.database",
    "cleanguard.database.db",
    "cleanguard.localization",
    "cleanguard.localization.manager",
    "cleanguard.ui",
    "cleanguard.ui.main_window",
    "cleanguard.ui.dashboard_page",
    "cleanguard.ui.scan_page",
    "cleanguard.ui.results_page",
    "cleanguard.ui.cleanup_page",
    "cleanguard.ui.duplicates_page",
    "cleanguard.ui.large_files_page",
    "cleanguard.ui.registry_page",
    "cleanguard.ui.uninstaller_page",
    "cleanguard.ui.startup_page",
    "cleanguard.ui.turbo_page",
    "cleanguard.ui.network_page",
    "cleanguard.ui.tweaks_page",
    "cleanguard.ui.hardware_page",
    "cleanguard.ui.history_page",
    "cleanguard.ui.settings_page",
    "cleanguard.ui.about_page",
    "cleanguard.ui.tray",
    "cleanguard.ui.theme",
    "cleanguard.ui.models",
    "cleanguard.utils",
    "cleanguard.utils.logging",
    "cleanguard.utils.formatting",
    "cleanguard.utils.crash_handler",
    "cleanguard.utils.filesystem",
]

excludes = [
    "tkinter",
    "matplotlib",
    "numpy",
    "scipy",
    "pandas",
    "IPython",
    "unittest",
    "pytest",
    "_pytest",
]

a = Analysis(
    [os.path.join(PROJECT_ROOT, "cleanguard", "app", "main.py")],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Single Executable Mode
icon_path = os.path.join(PROJECT_ROOT, "assets", "cleanguard.ico")
version_param = version_file if os.path.isfile(version_file) else None

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="CleanGuard",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # False to prevent antivirus false-positives
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed GUI application (no cmd pop-up)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
    version=version_param,
    uac_admin=True,  # Embeds requireAdministrator UAC manifest
    uac_uiaccess=False,
)
