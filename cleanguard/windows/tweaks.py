"""
Windows 10/11 Bloatware and Telemetry Tweaks Manager.
Provides inspection and management of built-in AppX packages and system privacy/telemetry settings.
Safe by design: Never removes critical system packages (Store, Shell, Windows Security).
"""

import os
import sys
import subprocess
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional, Set
from cleanguard.windows.privileges import is_user_admin
from cleanguard.utils.logging import get_logger

logger = get_logger("windows.tweaks")

# Windows Registry module import with safe fallback
try:
    import winreg
except ImportError:
    winreg = None


@dataclass
class PrivacyTweak:
    """Represents a configurable Windows privacy, telemetry, or system tweak."""
    id: str
    name: str
    description: str
    category: str  # "Telemetry", "Privacy", "Search"
    hive: int      # winreg.HKEY_LOCAL_MACHINE or winreg.HKEY_CURRENT_USER
    sub_key: str
    value_name: str
    value_type: int
    protect_value: Any  # Value that enforces maximum privacy/optimization
    default_value: Any  # Default Windows value
    requires_admin: bool = False


@dataclass
class BloatwareApp:
    """Represents a removable Windows 10/11 AppX package."""
    id: str
    name: str
    package_pattern: str
    description: str
    category: str  # "Entertainment", "Microsoft", "Gaming"
    installed: bool = False


# Curated list of safe privacy and telemetry tweaks
BUILTIN_TWEAKS: List[PrivacyTweak] = [
    PrivacyTweak(
        id="disable_telemetry",
        name="Windows Telemetriya ma'lumotlarini to'xtatish",
        description="Diagnostika va tizim xatolik jurnallarining Microsoft ga jo'natilishini bloklaydi.",
        category="Telemetry",
        hive=getattr(winreg, "HKEY_LOCAL_MACHINE", 0),
        sub_key=r"SOFTWARE\Policies\Microsoft\Windows\DataCollection",
        value_name="AllowTelemetry",
        value_type=getattr(winreg, "REG_DWORD", 4),
        protect_value=0,
        default_value=1,
        requires_admin=True,
    ),
    PrivacyTweak(
        id="disable_advertising_id",
        name="Reklama identifikatorini (Advertising ID) o'chirish",
        description="Foydalanuvchi profiliga moslashtirilgan reklamalar uchun maxsus ID ni o'chiradi.",
        category="Privacy",
        hive=getattr(winreg, "HKEY_CURRENT_USER", 0),
        sub_key=r"Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo",
        value_name="Enabled",
        value_type=getattr(winreg, "REG_DWORD", 4),
        protect_value=0,
        default_value=1,
        requires_admin=False,
    ),
    PrivacyTweak(
        id="disable_tailored_experiences",
        name="Moslashtirilgan tajribalar (Tailored Experiences)",
        description="Microsoft ning shaxsiy ma'lumotlarga asoslangan keraksiz maslahat va bildirishnomalarini to'xtatadi.",
        category="Privacy",
        hive=getattr(winreg, "HKEY_CURRENT_USER", 0),
        sub_key=r"Software\Microsoft\Windows\CurrentVersion\Privacy",
        value_name="TailoredExperiencesWithDiagnosticDataEnabled",
        value_type=getattr(winreg, "REG_DWORD", 4),
        protect_value=0,
        default_value=1,
        requires_admin=False,
    ),
    PrivacyTweak(
        id="disable_bing_search",
        name="Start menyusida Bing qidiruvini o'chirish",
        description="Pusk menyusida mahalliy qidirganda internetdagi Bing reklamalari va natijalarini ko'rsatmaydi.",
        category="Search",
        hive=getattr(winreg, "HKEY_CURRENT_USER", 0),
        sub_key=r"Software\Microsoft\Windows\CurrentVersion\Search",
        value_name="BingSearchEnabled",
        value_type=getattr(winreg, "REG_DWORD", 4),
        protect_value=0,
        default_value=1,
        requires_admin=False,
    ),
    PrivacyTweak(
        id="disable_activity_feed",
        name="Faoliyat lentasi (Activity Feed) sinxronizatsiyasi",
        description="Ishlatilgan fayllar va harakatlar tarixining bulutga yuborilishini bloklaydi.",
        category="Privacy",
        hive=getattr(winreg, "HKEY_LOCAL_MACHINE", 0),
        sub_key=r"SOFTWARE\Policies\Microsoft\Windows\System",
        value_name="EnableActivityFeed",
        value_type=getattr(winreg, "REG_DWORD", 4),
        protect_value=0,
        default_value=1,
        requires_admin=True,
    ),
    PrivacyTweak(
        id="disable_feedback_prompts",
        name="Fikr-mulohaza so'rovnomalari (Feedback Prompts)",
        description="Windows ning bezovta qiluvchi 'Tizim qanday ishlayapti?' kabi so'rovlarini to'xtatadi.",
        category="Privacy",
        hive=getattr(winreg, "HKEY_CURRENT_USER", 0),
        sub_key=r"Software\Microsoft\Siuf\Rules",
        value_name="NumberOfSIUFInPeriod",
        value_type=getattr(winreg, "REG_DWORD", 4),
        protect_value=0,
        default_value=1,
        requires_admin=False,
    ),
]


# Curated list of safe removable Windows AppX packages
BUILTIN_BLOATWARE: List[BloatwareApp] = [
    BloatwareApp(
        id="cortana",
        name="Microsoft Cortana",
        package_pattern="Microsoft.549981C3F5F10",
        description="Eskirgan ovozli yordamchi ilovasi",
        category="Microsoft",
    ),
    BloatwareApp(
        id="bing_news",
        name="Microsoft News / Bing News",
        package_pattern="Microsoft.BingNews",
        description="Yangiliklar va reklama maqolalari vidjeti",
        category="Entertainment",
    ),
    BloatwareApp(
        id="bing_weather",
        name="MSN Weather (Ob-havo)",
        package_pattern="Microsoft.BingWeather",
        description="Standart ob-havo vidjeti",
        category="Entertainment",
    ),
    BloatwareApp(
        id="xbox_game_bar",
        name="Xbox Game Bar / Overlay",
        package_pattern="Microsoft.XboxGamingOverlay",
        description="O'yinlar uchun ekran yozib olish va overlay paneli",
        category="Gaming",
    ),
    BloatwareApp(
        id="xbox_app",
        name="Xbox Console Companion",
        package_pattern="Microsoft.XboxApp",
        description="Xbox konsol bog'lash va do'stlar paneli",
        category="Gaming",
    ),
    BloatwareApp(
        id="zune_music",
        name="Groove Music (Media Player)",
        package_pattern="Microsoft.ZuneMusic",
        description="Standart musiqa pleyeri",
        category="Entertainment",
    ),
    BloatwareApp(
        id="zune_video",
        name="Movies & TV (Kino va TV)",
        package_pattern="Microsoft.ZuneVideo",
        description="Standart video ko'rish ilovasi",
        category="Entertainment",
    ),
    BloatwareApp(
        id="skype",
        name="Skype",
        package_pattern="Microsoft.SkypeApp",
        description="Standart oldindan o'rnatilgan Skype ilovasi",
        category="Microsoft",
    ),
    BloatwareApp(
        id="solitaire",
        name="Microsoft Solitaire Collection",
        package_pattern="Microsoft.MicrosoftSolitaireCollection",
        description="Standart kassa o'yini va reklamali integratsiya",
        category="Gaming",
    ),
    BloatwareApp(
        id="3d_viewer",
        name="3D Viewer",
        package_pattern="Microsoft.Microsoft3DViewer",
        description="3D modellarni ko'rish ilovasi",
        category="Microsoft",
    ),
    BloatwareApp(
        id="feedback_hub",
        name="Feedback Hub",
        package_pattern="Microsoft.WindowsFeedbackHub",
        description="Fikr-mulohaza va diagnostika hisobotlari markazi",
        category="Microsoft",
    ),
    BloatwareApp(
        id="get_help",
        name="Get Help",
        package_pattern="Microsoft.GetHelp",
        description="Microsoft onlayn yordam ilovasi",
        category="Microsoft",
    ),
    BloatwareApp(
        id="phone_link",
        name="Phone Link (Your Phone)",
        package_pattern="Microsoft.YourPhone",
        description="Smartfonni kompyuter bilan sinxronlash ilovasi",
        category="Microsoft",
    ),
]


class TweaksManager:
    """Manages Windows privacy tweaks and UWP bloatware uninstallation."""

    def __init__(self):
        self.tweaks = list(BUILTIN_TWEAKS)
        self.bloatware = list(BUILTIN_BLOATWARE)

    def is_tweak_applied(self, tweak: PrivacyTweak) -> bool:
        """Check whether the given privacy tweak is actively enforced in the Windows registry."""
        if winreg is None or sys.platform != "win32":
            return False

        try:
            with winreg.OpenKey(tweak.hive, tweak.sub_key, 0, winreg.KEY_READ) as key:
                val, val_type = winreg.QueryValueEx(key, tweak.value_name)
                return val == tweak.protect_value
        except (FileNotFoundError, OSError):
            return False

    def apply_tweak(self, tweak: PrivacyTweak, enable_protection: bool) -> Tuple[bool, str]:
        """
        Apply or revert a privacy tweak in the Windows registry.
        If enable_protection=True, writes protect_value (privacy safe).
        If enable_protection=False, writes default_value (Windows default).
        """
        if winreg is None or sys.platform != "win32":
            return False, "Not supported on non-Windows platform."

        if tweak.requires_admin and not is_user_admin():
            return False, "Ushbu parametrni o'zgartirish uchun Administrator huquqi talab qilinadi."

        target_value = tweak.protect_value if enable_protection else tweak.default_value

        try:
            with winreg.CreateKeyEx(tweak.hive, tweak.sub_key, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, tweak.value_name, 0, tweak.value_type, target_value)
            logger.info("Tweak '%s' set to %s successfully.", tweak.id, target_value)
            return True, "Muvaffaqiyatli saqlandi."
        except PermissionError:
            logger.warning("Permission denied writing registry tweak %s", tweak.id)
            return False, "Ruxsat yetarli emas. CleanGuard ni Administrator sifatida ishga tushiring."
        except Exception as ex:
            logger.error("Error setting tweak %s: %s", tweak.id, ex)
            return False, str(ex)

    def get_installed_appx_names(self) -> Set[str]:
        """Query currently installed AppX package names via PowerShell."""
        if sys.platform != "win32":
            return set()

        cmd = [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "Get-AppxPackage | Select-Object -ExpandProperty Name",
        ]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if proc.returncode == 0 and proc.stdout:
                names = {line.strip() for line in proc.stdout.splitlines() if line.strip()}
                return names
            else:
                logger.debug("Get-AppxPackage returned non-zero or empty: %s", proc.stderr)
        except Exception as ex:
            logger.warning("Failed executing Get-AppxPackage: %s", ex)

        return set()

    def get_bloatware_status(self) -> List[BloatwareApp]:
        """Scan system and return bloatware apps marked with current installation status."""
        installed_names = self.get_installed_appx_names()
        results: List[BloatwareApp] = []

        for app in self.bloatware:
            is_present = False
            for pkg in installed_names:
                if app.package_pattern.lower() in pkg.lower():
                    is_present = True
                    break
            app_copy = BloatwareApp(
                id=app.id,
                name=app.name,
                package_pattern=app.package_pattern,
                description=app.description,
                category=app.category,
                installed=is_present,
            )
            results.append(app_copy)

        return results

    def remove_bloatware(self, app: BloatwareApp) -> Tuple[bool, str]:
        """
        Uninstall an AppX package using PowerShell Remove-AppxPackage.
        """
        if sys.platform != "win32":
            return False, "Not supported on non-Windows platform."

        logger.info("Uninstalling bloatware package %s...", app.package_pattern)
        cmd = [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            f"Get-AppxPackage -Name *{app.package_pattern}* | Remove-AppxPackage",
        ]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if proc.returncode == 0:
                logger.info("Successfully removed %s", app.name)
                return True, f"'{app.name}' muvaffaqiyatli o'chirildi."
            else:
                err = proc.stderr.strip() or proc.stdout.strip() or "Noma'lum xatolik"
                logger.warning("Failed removing %s: %s", app.name, err)
                return False, f"O'chirishda xatolik: {err}"
        except subprocess.TimeoutExpired:
            return False, "Jarayon vaqti tugadi (Timeout)."
        except Exception as ex:
            return False, str(ex)
