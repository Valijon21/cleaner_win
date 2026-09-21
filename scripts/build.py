"""
CleanGuard Automated Build & Packaging Script.
Orchestrates environment preparation, version resource generation,
PyInstaller execution, and output validation.
"""

import os
import sys
import shutil
import subprocess
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.version_info import generate_version_info_file
from cleanguard.app.version import get_version_string


def clean_previous_builds():
    """Remove previous build and dist artifacts."""
    for folder_name in ["build", "dist"]:
        folder_path = os.path.join(PROJECT_ROOT, folder_name)
        if os.path.exists(folder_path):
            print(f"Cleaning {folder_name} directory...")
            try:
                shutil.rmtree(folder_path)
            except Exception as exc:
                print(f"Warning: Could not remove {folder_path}: {exc}")


def build_executable() -> bool:
    """Execute PyInstaller build process."""
    print("=" * 60)
    print(f"Starting Build for: {get_version_string()}")
    print("=" * 60)

    # 1. Clean prior outputs
    clean_previous_builds()

    # 2. Generate file_version_info.txt
    version_file = os.path.join(PROJECT_ROOT, "file_version_info.txt")
    generate_version_info_file(version_file)
    print(f"Generated version info resource: {version_file}")

    # 3. Check for PyInstaller
    try:
        import PyInstaller
        print(f"Found PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("Notice: PyInstaller module not directly importable in current Python.")

    spec_file = os.path.join(PROJECT_ROOT, "cleanguard.spec")
    if not os.path.exists(spec_file):
        print(f"Error: Spec file not found at {spec_file}")
        return False

    # 4. Run PyInstaller
    cmd = [sys.executable, "-m", "PyInstaller", spec_file, "--noconfirm", "--clean"]
    print(f"Executing: {' '.join(cmd)}")
    start_time = time.time()

    process = subprocess.run(cmd, cwd=PROJECT_ROOT)
    elapsed = time.time() - start_time

    if process.returncode != 0:
        print(f"Build failed with exit code {process.returncode}")
        return False

    # 5. Verify Output Executable
    exe_path = os.path.join(PROJECT_ROOT, "dist", "CleanGuard.exe")
    if os.path.isfile(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print("=" * 60)
        print("BUILD SUCCESSFUL!")
        print(f"Binary Output: {exe_path}")
        print(f"Binary Size:   {size_mb:.2f} MB")
        print(f"Build Time:    {elapsed:.1f} seconds")
        print("=" * 60)
        return True
    else:
        print(f"Error: Expected binary not found at {exe_path}")
        return False


if __name__ == "__main__":
    success = build_executable()
    sys.exit(0 if success else 1)
