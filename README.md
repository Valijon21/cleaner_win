# CleanGuard — Professional Windows Storage Cleanup & Analysis Utility

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%207%20SP1%20%7C%208%20%7C%208.1%20%7C%2010%20%7C%2011-0078D7.svg)](https://microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

CleanGuard is an enterprise-grade, safety-first Windows storage cleanup desktop utility. It provides transparent, explainable, and non-destructive reclamation of drive storage across all major Windows versions.

---

## 🛡️ Core Philosophy: Safety by Architecture

1. **Non-bypassable Safety Engine**: Every target must pass strict canonicalization, boundary verification, and hard protection rules before deletion.
2. **Immutable Protected Paths**: `System32`, `WinSxS`, `Boot`, `Program Files`, `Documents`, `Desktop`, `Pictures`, `Videos`, `Downloads`, and critical registry/system files are hard-coded as **BLOCKED** and can never be cleaned.
3. **TOCTOU Defense**: Targets are re-validated immediately prior to removal to ensure they haven't been substituted or modified between scan and cleanup.
4. **Explainable AI/Rule Layer**: Every cleanup candidate specifies its category, risk level (`SAFE`, `REVIEW`, `BLOCKED`), age, size, and explicit justification.

---

## 🚀 Key Features

- **Concurrent Multi-Scanner Engine**:
  - Windows User & System Temporary Files (`%TEMP%`, `Windows\Temp`)
  - Application & DirectX Shader Caches
  - Windows Explorer Thumbnail Caches (`thumbcache_*.db`)
  - System Crash Dumps (`.dmp`) & Minidumps
  - Diagnostic & Windows Error Reporting Logs (`WER`)
  - Web Browser Cache Isolation (Chrome, Edge, Firefox, Opera) — *Zero impact on logins, history, or cookies*
  - Windows Recycle Bin storage analysis
- **Modern High-DPI PyQt5 Interface**:
  - Dark-mode first sleek slate palette with semantic status indicators
  - Real-time disk capacity gauges for all local storage drives (C:, D:, etc.)
  - Interactive results table with granular item selection and risk badges
  - Live progress feedback with safe cancellation support
- **Trilingual Localization**:
  - 🇺🇿 **O'zbekcha** (Native default)
  - 🇷🇺 **Русский**
  - 🇬🇧 **English**
- **Full Audit History**:
  - Integrated SQLite WAL database tracking lifetime recovered storage, itemized deletion records, and session logs.

---

## 📦 Installation & Running

### Requirements
- Windows 7 SP1, 8, 8.1, 10, or 11
- Python 3.8 or higher

```bash
# Clone or navigate to the project directory
cd winCleaner

# Activate virtual environment
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run CleanGuard
python -m cleanguard.app.main
```

### Running Automated Tests

```bash
pytest -v tests/
```
