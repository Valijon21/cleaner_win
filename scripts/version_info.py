"""
Windows Version Info Generator for CleanGuard PyInstaller Build.
Dynamically creates a file_version_info.txt compatible with PyInstaller.
"""

import os
import sys

# Add project root to sys.path to import version
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cleanguard.app.version import (
    APP_NAME,
    APP_DISPLAY_NAME,
    APP_VERSION,
    BUILD_NUMBER,
    COPYRIGHT,
)


def get_version_tuple(version_str: str):
    """Convert version string like '0.1.0' to 4-element integer tuple (0, 1, 0, 0)."""
    parts = version_str.split(".")
    nums = []
    for p in parts:
        try:
            nums.append(int(p))
        except ValueError:
            nums.append(0)
    while len(nums) < 4:
        nums.append(0)
    return tuple(nums[:4])


def generate_version_info_file(output_path: str) -> str:
    """Generate PyInstaller file_version_info.txt."""
    v_tuple = get_version_tuple(APP_VERSION)
    v_str = f"{v_tuple[0]}.{v_tuple[1]}.{v_tuple[2]}.{v_tuple[3]}"

    content = f"""# UTF-8
#
# CleanGuard Professional Version Info Resource
#
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={v_tuple},
    prodvers={v_tuple},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904b0',
          [
            StringStruct('CompanyName', '{APP_NAME} Team'),
            StringStruct('FileDescription', '{APP_DISPLAY_NAME} - Windows System Cleaner and Optimizer'),
            StringStruct('FileVersion', '{v_str}'),
            StringStruct('InternalName', '{APP_NAME}'),
            StringStruct('LegalCopyright', '{COPYRIGHT}'),
            StringStruct('OriginalFilename', '{APP_NAME}.exe'),
            StringStruct('ProductName', '{APP_DISPLAY_NAME}'),
            StringStruct('ProductVersion', '{APP_VERSION}'),
            StringStruct('BuildNumber', '{BUILD_NUMBER}')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


if __name__ == "__main__":
    out = os.path.join(PROJECT_ROOT, "file_version_info.txt")
    generate_version_info_file(out)
    print(f"Generated version info file: {out}")
