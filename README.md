# CleanGuard Professional — Enterprise Windows Storage, Optimization & Security Suite

<div align="center">

![CleanGuard Logo](https://img.shields.io/badge/CleanGuard-Professional-0078D7?style=for-the-badge&logo=windows&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%207%20SP1%20%7C%208%20%7C%208.1%20%7C%2010%20%7C%2011-0078D7?style=for-the-badge&logo=windows)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Architecture](https://img.shields.io/badge/Architecture-x86%20%7C%20x64%20%7C%20ARM64-lightgrey?style=for-the-badge)

**Next-generation, safety-first Windows system cleanup, maintenance, privacy hardening, and performance suite.**

[ 🇺🇿 O'zbekcha ](README.uz.md) &nbsp; | &nbsp; [ 🇷🇺 Русский ](README.ru.md) &nbsp; | &nbsp; [ 🇬🇧 English ](README.md)

</div>

---

## 🌟 Executive Overview

**CleanGuard** is an open-source, enterprise-grade Windows optimization desktop utility engineered with strict safety guarantees. Unlike traditional PC cleaners that blindly purge files and risk OS stability, CleanGuard operates on a **Safety-by-Architecture** principle: every single deletion candidate is cryptographically checked, boundary-isolated, and verified against system policies before any modification takes place.

Featuring **15 specialized modules**, CleanGuard delivers comprehensive disk reclamation, duplicate file hashing, safe registry cleaning with automatic rollback, large file discovery, startup optimization, bloatware & telemetry removal, Windows Update & WinSxS cleanup, network latency tuning, real-time hardware diagnostics, and silent scheduled maintenance.

---

## 🛡️ Core Safety Architecture

CleanGuard enforces non-bypassable guarantees to ensure your operating system remains 100% stable:

1. **PathGuard Boundary Engine**:
   - Hard-blocks `C:\Windows`, `System32`, `SysWOW64`, `WinSxS`, `Boot`, `Program Files`, and protected system volumes.
   - Prevents scanning or touching user personal libraries: `Desktop`, `Documents`, `Pictures`, `Videos`, `Music`, `Downloads`.
   - Canonicalizes every target path (`GetFinalPathNameByHandleW`) to detect and reject symlink, hardlink, and junction loop manipulations.
2. **TOCTOU (Time-of-Check to Time-of-Use) Defense**:
   - Re-evaluates each target file directly before unlinking. If permissions, file handles, or targets change after scan time, the operation safely aborts.
3. **Automated Rollback & Restore Protection**:
   - **System Restore Point**: Creates a native Windows VSS Restore Point (`SRSetRestorePointW`) prior to major cleaning operations.
   - **Registry Rollback**: Automatically exports pre-cleanup registry state into timestamped `.reg` backup files before any key modification.
4. **3-Tier Explainable Risk Model**:
   - 🟢 `SAFE`: Routine application caches, temporary files, and thumbnail artifacts (>24h old).
   - 🟡 `REVIEW`: System logs, memory crash dumps, and browser cache data requiring explicit user consent.
   - 🔴 `BLOCKED`: Protected OS components, active processes, and user documents strictly forbidden from modification.

---

## 🚀 The 15 Enterprise Modules

```text
CleanGuard Suite
├── 📊 01. Dashboard              ── Live system health, 1-Click Smart Care & storage gauges
├── 🧹 02. Deep Cleaner           ── Multi-threaded concurrent junk & cache scanner
├── 🔍 03. Duplicate Finder       ── Multi-phase hash detector (MD5/SHA256) with preview
├── 🐘 04. Large Files Finder     ── 100MB+ & 1GB+ space-hog analyzer with SafetyEngine protection
├── 🛡️ 05. Registry Cleaner       ── Safe invalid key scanner with 1-click .reg rollback
├── 📦 06. App Uninstaller        ── Win32/UWP uninstaller with deep leftover residue purge
├── 🚀 07. Startup Manager        ── Run/RunOnce, Startup folders & Task Scheduler manager
├── ⚡ 08. Turbo RAM Booster      ── Working set trimming & Standby memory cache flush
├── 🌐 09. Network Optimizer      ── DNS flush, Winsock reset, TCP tuning & DNS benchmark
├── 🛠️ 10. Tweaks & WinSxS        ── Bloatware remover, telemetry blocker & Windows Update (DISM)
├── 💻 11. Hardware Monitor       ── Real-time CPU, GPU, RAM, Disks, Motherboard & OS specs
├── ⏰ 12. Auto-Care Scheduler    ── Windows Task Scheduler integration for automated care
├── 🔄 13. Restore Point Manager  ── Windows VSS System Restore Point generation
├── 📜 14. Audit & History        ── SQLite WAL database with CSV/JSON export engine
└── 🎨 15. Modern Fluent UI       ── High-DPI dark interface with dynamic trilingual support
```

### 1. 📊 System Dashboard & 1-Click Smart Care
- Real-time disk capacity meters for all detected drives (C:, D:, etc.) with color-coded warning thresholds.
- Overall system health score, memory load indicator, and instant circular SCAN centerpiece.
- **⚡ 1-Click Smart Care**: ASC-style all-in-one automated pipeline running Junk Clean + Safe Registry Repair + RAM Flush + DNS Purge + Windows Update Cache purge with live progress metrics and completion modal.

### 2. 🧹 Deep Clean Engine
- Concurrent multithreaded scanning across high-volume storage categories:
  - **User & System Temp**: `%TEMP%`, `C:\Windows\Temp`, Prefetch (safe metadata).
  - **Shader & App Caches**: DirectX Shader Cache, D3DSCache, Delivery Optimization.
  - **Explorer Thumbnail Caches**: `thumbcache_*.db` and icon caches.
  - **Crash Dumps & Error Reports**: `MEMORY.DMP`, minidumps, WER reports, and CBS logs.
  - **Web Browser Isolation**: Chromium (Chrome, Edge, Brave, Opera) and Firefox caches isolated with zero risk to passwords, sessions, or cookies.
  - **Recycle Bin**: Per-drive cluster analysis with native Win32 `SHEmptyRecycleBinW`.

### 3. 🔍 Duplicate File Finder
- High-performance two-stage file comparison:
  1. Fast preliminary file size & 4KB header hash matching.
  2. Full cryptographic hashing (MD5 / SHA256) for exact match confirmation.
- Side-by-side file visualizer with smart auto-selection (keep oldest, keep newest, or custom).
- PathGuard integration prevents duplicates from deleting system or application files.

### 4. 🐘 Large & Space-Hog Files Finder
- Identifies storage-hogging files across drives (>100 MB, >500 MB, >1 GB, >5 GB).
- Automatically groups files into categories:
  - 🎬 **Videos** (`.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`)
  - 🎵 **Audio** (`.mp3`, `.wav`, `.flac`, `.aac`)
  - 📦 **Archives & ISOs** (`.zip`, `.rar`, `.7z`, `.iso`, `.img`)
  - 💿 **Virtual Machines & Disk Images** (`.vmdk`, `.vhd`, `.vhdx`)
  - 📄 **Documents & Databases** (`.pdf`, `.docx`, `.bak`, `.sql`)
  - ⚙️ **Installers & Packages** (`.exe`, `.msi`, `.cab`)
- **SafetyEngine Guard**: Critical OS and kernel files (`pagefile.sys`, `swapfile.sys`, `hiberfil.sys`, `C:\Windows\*`) are blocked from accidental deletion.
- Features one-click **"Reveal in Explorer"** (`explorer.exe /select`) and safety-confirmed deletion.

### 5. 🛡️ Safe Registry Cleaner
- Scans orphaned and corrupt registry entries:
  - Invalid CLSIDs and COM/ActiveX components
  - Broken file associations and missing extensions
  - Obsolete shared DLL references
  - Broken application uninstaller entries
  - Obsolete Windows MUI caches
- **Zero-Risk Guarantee**: Generates an automated `.reg` backup before any changes are applied, enabling immediate 1-click rollback.

### 6. 📦 Application Uninstaller & Leftover Cleaner
- Unified view of standard desktop software (Win32) and modern Windows apps (UWP).
- Supports standard and silent/unattended uninstall routines.
- **Deep Leftover Hunter**: Automatically crawls `%AppData%`, `%LocalAppData%`, `Program Files`, and the Windows Registry to purge residual files left behind by uninstalled software.

### 7. 🚀 Startup Manager
- Inspects HKCU/HKLM `Run`, `RunOnce`, Startup directories, and Task Scheduler triggers.
- Analyze boot impact (High, Medium, Low) for each item.
- Toggle entries on/off or configure delayed launch to dramatically accelerate boot time.

### 8. ⚡ Turbo Memory Booster
- Direct Win32 API integration via `ctypes` calling `EmptyWorkingSet`.
- Flushes orphaned system standby lists and working set caches without terminating user applications or risking data corruption.

### 9. 🌐 Network & Latency Optimizer
- One-click **DNS Cache Flush** (`ipconfig /flushdns`) to resolve stale routing.
- **Winsock Catalog Reset** (`netsh winsock reset`) for connection repair.
- **TCP/IP Stack Auto-Tuning** optimization for reduced gaming latency and buffer bloat.
- **Live DNS Benchmark**: Pings top secure DNS providers (Cloudflare `1.1.1.1`, Google `8.8.8.8`, OpenDNS `208.67.222.222`) and displays real-time latency (ms).

### 10. 🛠️ Windows Tweaks & WinSxS Component Store
- **Windows Update Cache Purge**: Safely removes gigabytes of obsolete update installers from `SoftwareDistribution\Download` and `DeliveryOptimization\Cache`.
- **WinSxS Component Store (DISM)**: Executes official Microsoft `dism.exe /Online /Cleanup-Image /StartComponentCleanup` to compress and purge superseded Windows OS service packs and manifests (reclaims 10–25+ GB).
- **Bloatware Purge**: Safely removes pre-installed Windows UWP apps (Cortana, Bing News, Xbox telemetry, Solitaire, etc.).
- **Telemetry & Tracking Blocker**: Disables Microsoft DiagTrack, Connected User Experiences, and Activity History logging.
- **Start Menu & Search Tuning**: Disables online Bing search and web ads in the Windows Start menu.
- **Gaming Tweaks**: Optimizes GPU scheduling, disables mouse acceleration, and configures low-latency power profiles.

### 11. 💻 Hardware & System Specs Monitor
- Live hardware telemetries:
  - **Processor (CPU)**: Architecture, physical/logical core counts, utilization percentage.
  - **Memory (RAM)**: Total, available, in-use, and utilization graph.
  - **Graphics (GPU)**: Adapter name, driver version, dedicated video memory.
  - **Storage Devices**: Drive models, interfaces, free/total space, drive types (SSD, NVMe, HDD).
  - **Motherboard & BIOS**: Manufacturer, product board, BIOS release version.
  - **Operating System**: Windows edition, build number (e.g. 22631), UBR, and bitness.

### 12. ⏰ Auto-Care Task Scheduler
- Seamlessly registers native Windows scheduled tasks via `schtasks.exe`.
- Configurable intervals (Daily, Weekly, Idle time).
- Supports headless silent background execution (`--auto-clean`) without opening the GUI.

### 13. 🔄 System Restore Point Engine
- Direct interaction with Windows Volume Shadow Copy (VSS) via `SRSetRestorePointW` and WMI `SystemRestore`.
- Automatically checkpoints system state before any risky cleanups or registry operations.

### 14. 📜 Audit History & Reports
- Every cleaning event is immutably logged into a local SQLite database configured with **WAL (Write-Ahead Logging)** mode.
- Tracks lifetime recovered space, file counts, and error audits.
- Full export capabilities to **CSV** and **JSON** formats.

### 15. 🎨 Fluent High-DPI UI & Trilingual Localization
- Clean, dark-mode slate theme inspired by Windows Fluent Design.
- Fully responsive layout with crisp SVG icons and real-time visual progress bars.
- Dynamic runtime language switching without restarting the app:
  - 🇺🇿 **O'zbekcha** (Native default)
  - 🇷🇺 **Русский**
  - 🇬🇧 **English**

---

## 🏛️ Project Architecture

```text
winCleaner/
├── cleanguard/                    # Main Application Package
│   ├── app/                       # Application Lifecycle & Entry Points
│   │   ├── bootstrap.py           # Pre-flight environment, DPI, Elevation & DB init
│   │   ├── main.py                # Main executable & CLI entry
│   │   └── version.py             # Version metadata (0.1.0, Build 2026.1)
│   ├── core/                      # Domain Logic & Cleaner Engine
│   │   ├── cleaner/               # Execution planners, strategies, shredders
│   │   ├── contracts.py           # Core interfaces (CleanTarget, RiskLevel, etc.)
│   │   ├── config.py              # Application settings & safe path defaults
│   │   └── scanner/               # 8+ specialized scanner workers
│   ├── database/                  # Storage Layer
│   │   ├── db.py                  # SQLite WAL connection manager
│   │   ├── schema.py              # DDL schema definitions
│   │   └── repositories.py        # Query repositories for sessions & history
│   ├── localization/              # Trilingual Translation Engine
│   │   ├── en.json                # English translation catalogue
│   │   ├── ru.json                # Russian translation catalogue
│   │   ├── uz.json                # Uzbek translation catalogue
│   │   └── manager.py             # Dynamic runtime localization manager
│   ├── security/                  # Safety Verification & Guardrails
│   │   ├── path_guard.py          # Boundary validation & symlink/junction defense
│   │   ├── protected_paths.py     # Hardcoded Windows system & user protected paths
│   │   ├── pyinstaller_tracker.py # Runtime protection against temp folder deletion
│   │   └── risk_engine.py         # 3-tier risk evaluation classifier
│   ├── services/                  # Asynchronous Application Services
│   │   ├── cleanup_service.py     # Background QThread deletion executor
│   │   ├── export_service.py      # CSV and JSON report exporter
│   │   ├── monitor_service.py     # Live disk & RAM monitor service
│   │   └── scan_service.py        # Background QThread scanner coordinator
│   ├── ui/                        # PyQt5 User Interface
│   │   ├── main_window.py         # Primary window shell & navigation sidebar
│   │   ├── theme.py               # Modern dark slate stylesheet
│   │   ├── tray.py                # Windows notification area (Tray) integration
│   │   ├── widgets/               # Custom reusable cards, badges, buttons
│   │   └── *_page.py              # 14 distinct module views
│   ├── utils/                     # System Utilities
│   │   ├── crash_handler.py       # Global unhandled exception & mini-crash logger
│   │   ├── filesystem.py          # Low-level disk & file operations
│   │   ├── formatting.py          # Byte/Date/Speed humanizers
│   │   └── logging.py             # Rotating file & console logging system
│   └── windows/                   # Native Win32 API Integrations
│       ├── drives.py              # Drive detection & cluster metrics
│       ├── hardware.py            # CPU/GPU/RAM/Disk hardware telemetry
│       ├── known_folders.py       # SHGetKnownFolderPath resolution
│       ├── memory.py              # Win32 EmptyWorkingSet RAM management
│       ├── network.py             # DNS/Winsock/TCP latency optimization
│       ├── os_info.py             # OS build, version & architecture detection
│       ├── privileges.py          # UAC elevation & token privileges
│       ├── recycle_bin.py         # SHEmptyRecycleBinW Win32 wrapper
│       ├── registry_cleaner.py    # Winreg scanner & automated .reg backup/rollback
│       ├── restore_point.py       # Windows VSS Restore Point generator
│       ├── scheduler.py           # schtasks.exe Task Scheduler integration
│       ├── startup.py             # Windows startup items inspector
│       ├── tweaks.py              # Windows telemetry & bloatware tweaker
│       └── uninstaller.py         # Application uninstaller & leftover cleaner
├── tests/                         # 25+ Comprehensive Test Suites
│   ├── conftest.py                # Pytest fixtures & mock environments
│   ├── test_cleaner.py            # Safety & executor tests
│   ├── test_hardware.py           # Hardware telemetry tests
│   ├── test_network.py            # Network optimizer tests
│   ├── test_registry_cleaner.py   # Registry scanner & rollback tests
│   ├── test_safety_engine.py      # PathGuard & boundary tests
│   ├── test_ui.py                 # UI navigation & responsive layout tests
│   └── ...                        # Additional unit & integration tests
├── .gitignore                     # Repository hygiene filter
├── LICENSE                        # MIT License
├── pytest.ini                     # Test configuration
├── requirements.txt               # Production dependencies
└── requirements-dev.txt           # Development & testing dependencies
```

---

## 💻 Installation & Quick Start

### Prerequisites
- **Operating System**: Windows 7 SP1, Windows 8, Windows 8.1, Windows 10, or Windows 11 (32-bit or 64-bit)
- **Python**: Version 3.8 or higher
- **Privileges**: Administrator privileges recommended for full system cleaning and registry access.

### 1. Clone & Setup

```powershell
# Clone the repository
git clone https://github.com/Valijon21/cleaner_win.git
cd cleaner_win

# Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install required dependencies
pip install -r requirements.txt
```

### 2. Launch CleanGuard

```powershell
# Launch the full graphical user interface (GUI)
python -m cleanguard.app.main
```

### 3. Headless Auto-Care Mode

CleanGuard can be executed silently without opening the GUI (ideal for Windows Task Scheduler or background automation):

```powershell
# Run headless silent cleanup (SAFE category items only)
python -m cleanguard.app.main --auto-clean
```

---

## 🧪 Automated Testing

CleanGuard maintains 28 comprehensive unit and integration test suites (**132 passing tests**) covering path safety, duplicate file hashing, 1-Click Smart Care, Windows Update DISM cleanup, large file scanner, registry rollback, hardware metrics, and UI responsiveness.

```powershell
# Install development dependencies
pip install -r requirements-dev.txt

# Execute all 132 test suites
pytest -v tests/

# Execute specific component tests
pytest -v tests/test_smart_care.py
pytest -v tests/test_updates.py
pytest -v tests/test_large_files.py
pytest -v tests/test_safety_engine.py
pytest -v tests/test_registry_cleaner.py
pytest -v tests/test_network.py
```

---

## 🤝 Contributing

Contributions, bug reports, and feature proposals are warmly welcomed!
1. Fork the repository (`https://github.com/Valijon21/cleaner_win/fork`).
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes with conventional commit messages (`git commit -m 'feat: add new feature'`).
4. Ensure all tests pass (`pytest -v tests/`).
5. Push to the branch (`git push origin feature/AmazingFeature`).
6. Open a Pull Request.

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.

---

<div align="center">
  <sub>Built with ❤️ for a faster, safer, and cleaner Windows experience.</sub>
</div>
