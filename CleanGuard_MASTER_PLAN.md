# CleanGuard — Master Product, Architecture & AI-Agent Task Specification

> **Project type:** Professional Windows cleanup / storage analysis desktop application
> **Primary stack:** Python 3.8-compatible codebase + PyQt5 + Windows API (`ctypes` / `pywin32`) + SQLite
> **Target OS:** Windows 7 SP1, Windows 8, Windows 8.1, Windows 10, Windows 11
> **Product principle:** Maximize reclaimable storage while minimizing the probability of deleting useful, user-owned, or system-critical data.
> **Execution mode:** Human-supervised AI-agent development with task-by-task verification.
>
> **Important:** This document is the source of truth for the project. Agents must not invent cleanup rules, delete paths, or expand scope without updating the specification and tests.

---

## 1. Product Vision

CleanGuard is a professional Windows desktop utility that scans local disks, identifies reclaimable junk, explains why each item is considered safe or review-worthy, and performs controlled cleanup without damaging Windows, installed applications, or personal files.

The product should feel like a polished commercial utility, not a script wrapped in a GUI.

### Core user promise

1. Scan the PC.
2. Understand exactly what can be cleaned.
3. Clean only items permitted by the Safety Engine.
4. See what happened and how much space was recovered.
5. Preserve system stability and user data.

### Non-goals for MVP

- Registry “optimizer” that removes arbitrary registry keys.
- Driver deletion.
- Automatic removal of installed programs.
- Automatic deletion of arbitrary large personal files.
- Automatic modification of boot configuration.
- Automatic deletion from Documents/Desktop/Downloads/Pictures/Videos.
- Antivirus replacement.
- Disk defragmentation/optimization engine.
- RAM booster claims or fake performance optimization.

---

# 2. Product Modules

```text
CleanGuard
├── Application Shell
├── Dashboard
├── Drive Manager
├── Scanner Engine
│   ├── Temp Scanner
│   ├── Cache Scanner
│   ├── Log Scanner
│   ├── Browser Scanner
│   ├── Recycle Bin Scanner
│   ├── Update Leftovers Scanner
│   ├── Crash Dump Scanner
│   ├── Thumbnail Scanner
│   └── Large File Analyzer
├── Analyzer / Risk Engine
├── Safety Engine
├── Cleanup Engine
├── Recovery / Recycle Strategy
├── Windows Integration Layer
├── Permission / UAC Layer
├── SQLite Database
├── Settings / Rules
├── History / Reporting
├── Localization
├── Logging / Diagnostics
├── Packaging / Installer
└── Test / QA Infrastructure
```

---

# 3. Target Compatibility

## Runtime compatibility

The implementation must remain compatible with the selected Python 3.8 runtime baseline for Windows 7 support.

Do not use language features introduced after Python 3.8.

### Required validation matrix

| OS | Architecture | Required status |
|---|---|---|
| Windows 7 SP1 | x86 | Supported if packaged runtime and dependencies work |
| Windows 7 SP1 | x64 | Supported |
| Windows 8 | x86 | Supported where dependency stack permits |
| Windows 8 | x64 | Supported |
| Windows 8.1 | x86 | Supported where dependency stack permits |
| Windows 8.1 | x64 | Supported |
| Windows 10 | x64 | Supported |
| Windows 11 | x64 | Supported |

### Compatibility rules

- Detect OS and build at runtime.
- Detect architecture.
- Avoid APIs unavailable on old target OS versions unless a compatibility fallback exists.
- Never crash because an optional Windows capability is missing.
- Feature-gate newer Windows functionality.
- Keep Windows-specific code isolated under `windows/`.

---

# 4. Proposed Repository Structure

```text
cleanguard/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── bootstrap.py
│   └── version.py
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── dashboard.py
│   ├── scan_page.py
│   ├── results_page.py
│   ├── cleanup_page.py
│   ├── history_page.py
│   ├── settings_page.py
│   ├── about_page.py
│   └── widgets/
│       ├── cards.py
│       ├── buttons.py
│       ├── progress.py
│       ├── tables.py
│       ├── dialogs.py
│       └── status.py
│
├── core/
│   ├── scanner/
│   ├── analyzer/
│   ├── cleaner/
│   ├── safety/
│   ├── permissions/
│   └── recovery/
│
├── windows/
│   ├── os_info.py
│   ├── known_folders.py
│   ├── drives.py
│   ├── recycle_bin.py
│   ├── privileges.py
│   ├── processes.py
│   └── shell.py
│
├── rules/
│   ├── base.py
│   ├── temp_rules.py
│   ├── cache_rules.py
│   ├── log_rules.py
│   ├── browser_rules.py
│   ├── recycle_rules.py
│   └── protected_rules.py
│
├── database/
│   ├── db.py
│   ├── models.py
│   ├── repositories.py
│   └── migrations.py
│
├── security/
│   ├── protected_paths.py
│   ├── whitelist.py
│   ├── path_guard.py
│   └── risk_engine.py
│
├── services/
│   ├── scan_service.py
│   ├── cleanup_service.py
│   ├── history_service.py
│   ├── settings_service.py
│   └── report_service.py
│
├── localization/
│   ├── uz.json
│   ├── ru.json
│   └── en.json
│
├── utils/
│   ├── filesystem.py
│   ├── formatting.py
│   ├── concurrency.py
│   └── platform.py
│
├── resources/
│   ├── icons/
│   └── themes/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── safety/
│   ├── windows/
│   └── fixtures/
│
├── installer/
├── docs/
├── requirements.txt
├── requirements-dev.txt
├── README.md
└── LICENSE
```

---

# 5. Architectural Principles

## 5.1 Separation of concerns

UI must never directly delete files.

Correct flow:

```text
UI → Service → Cleanup Planner → Safety Engine → Cleanup Engine → Windows/FileSystem Adapter
```

## 5.2 Safe by default

Unknown = Review/Blocked, never Safe.

## 5.3 Explainability

Every cleanup candidate should have:

```text
path
category
size
age
reason
risk_level
rule_id
```

## 5.4 Least privilege

Run as standard user by default. Request elevation only when required.

## 5.5 Idempotency

Running the same cleanup twice must not cause unexpected side effects.

## 5.6 Fail-safe behavior

A failed permission check, path validation, or safety check must skip deletion.

## 5.7 No silent destructive behavior

No permanent delete without an explicit user path and confirmation.

---

# 6. Safety Model

## 6.1 Risk levels

```text
SAFE
REVIEW
BLOCKED
```

### SAFE

High-confidence temporary/cache/log data where the cleanup rule explicitly allows deletion.

### REVIEW

Potentially reclaimable but may contain useful user/application data.

### BLOCKED

System-critical, user-critical, ambiguous, or unsafe path.

## 6.2 Hard protected areas

At minimum protect:

```text
C:\Windows\System32
C:\Windows\SysWOW64
C:\Windows\WinSxS
C:\Windows\Boot
C:\Program Files
C:\Program Files (x86)
C:\Users\<user>\Documents
C:\Users\<user>\Desktop
C:\Users\<user>\Pictures
C:\Users\<user>\Videos
C:\Users\<user>\Downloads
pagefile.sys
hiberfil.sys
swapfile.sys
boot files
BCD
NTUSER.DAT
SAM
SECURITY
SYSTEM
SOFTWARE
```

These are policy examples and must be implemented as canonical, normalized paths rather than simple string-prefix checks.

## 6.3 Junction / symbolic link protection

Scanner must not recursively follow arbitrary junctions or symbolic links when scanning protected/system locations.

## 6.4 Path canonicalization

Before cleanup:

1. Normalize path.
2. Resolve drive/UNC representation where possible.
3. Check traversal attempts.
4. Check parent protection.
5. Check reparse point / junction behavior.
6. Revalidate immediately before delete.

## 6.5 TOCTOU mitigation

A file can change between scan and delete. Therefore the cleanup stage must re-check:

- file existence;
- path;
- file attributes;
- risk classification;
- target category;
- whether it is still within allowed boundary.

---

# 7. Safe Cleanup Categories — MVP

## Tier A — automatic-safe candidates

- User temporary files in known Temp directories.
- Windows temporary files when rule permits.
- Known application cache locations explicitly registered by rules.
- Old temporary log files where rule specifies safe age and location.
- Recycle Bin contents only after explicit user selection.

## Tier B — review required

- Browser cookies.
- Browser sessions.
- Crash dumps.
- Old Windows update leftovers.
- Large files.
- Downloads.
- Application-generated reports.

## Tier C — blocked

- Windows system files.
- Boot files.
- Installed program binaries.
- User personal files.
- Unknown executable files outside approved cache/temp rules.
- Registry hives.
- Files outside allowed cleanup roots.

---

# 8. Data Contracts

## 8.1 ScanItem

Conceptual fields:

```text
id
path
name
size
modified_at
category
risk_level
reason
rule_id
is_locked
is_symlink
is_junction
is_deletable
```

## 8.2 ScanSummary

```text
scan_id
started_at
finished_at
drive_count
files_scanned
items_found
safe_items
review_items
blocked_items
bytes_reclaimable
```

## 8.3 CleanupSummary

```text
cleanup_id
started_at
finished_at
files_deleted
files_skipped
files_failed
bytes_recovered
```

---

# 9. Database Design

## Tables

```text
scan_sessions
cleanup_sessions
cleanup_items
settings
rules
ignored_paths
statistics
application_logs
```

### `scan_sessions`

```text
id
started_at
finished_at
status
files_scanned
items_found
bytes_found
```

### `cleanup_sessions`

```text
id
started_at
finished_at
status
files_deleted
files_skipped
files_failed
bytes_recovered
```

### `cleanup_items`

```text
id
cleanup_session_id
path
category
risk_level
status
size
error_code
error_message
```

### `settings`

```text
key
value
updated_at
```

### `ignored_paths`

```text
id
path
created_at
reason
```

---

# 10. Scanner Architecture

Scanner interface:

```text
BaseScanner
├── TempScanner
├── CacheScanner
├── LogScanner
├── BrowserScanner
├── RecycleBinScanner
├── UpdateLeftoversScanner
├── CrashDumpScanner
├── ThumbnailScanner
└── LargeFileScanner
```

Each scanner must:

- expose a stable identifier;
- expose supported OS versions/features;
- return `ScanItem` objects;
- never perform deletion;
- support cancellation;
- catch filesystem errors and return structured results.

---

# 11. Cleanup Architecture

```text
CleanupRequest
   ↓
CleanupPlanner
   ↓
Safety Gate
   ↓
Permission Gate
   ↓
Lock Check
   ↓
Delete Strategy
   ↓
Verify
   ↓
Audit Log
```

Delete strategies:

```text
SKIP
RECYCLE_BIN
SAFE_DELETE
PERMANENT_DELETE
```

`PERMANENT_DELETE` is disabled in MVP except for a clearly scoped internal test path.

---

# 12. Windows Integration

Required adapters:

- OS version/build detection.
- Architecture detection.
- Known-folder lookup.
- Logical drive enumeration.
- Disk free-space retrieval.
- Administrator/elevation detection.
- Process detection.
- Recycle Bin integration.
- File attribute inspection.
- Reparse point/junction inspection.
- Shell/UAC launch helper.

All Windows-specific calls must be isolated and unit/integration tested.

---

# 13. UI / UX Specification

## Main navigation

```text
Dashboard
Scan
Results
History
Settings
About
```

## Dashboard content

- Total free space.
- Estimated reclaimable space.
- C: storage card.
- D: storage card.
- Last scan.
- Last cleanup.
- Files cleaned.
- Space recovered.
- Primary Scan button.

## Results screen

Columns:

```text
Select
Category
Path
Size
Age
Risk
Reason
```

Actions:

```text
Select Safe
Select All Review
Clear Selection
Review
Clean Safely
```

## Cleanup completion

Show:

- recovered space;
- deleted item count;
- skipped item count;
- failure count;
- reason for skipped/failed items;
- link to history/report.

---

# 14. Design System

Style target: professional utility software, not a toy app.

### Visual principles

- Clean typography.
- Strong hierarchy.
- Clear danger/safety states.
- Large primary action.
- Consistent spacing.
- Dark theme first; light theme supported.
- Keyboard accessible.
- DPI-aware.
- Avoid excessive animation during scanning.

### Component inventory

```text
AppShell
Sidebar
Header
StatCard
DriveCard
CategoryCard
ProgressBar
ResultTable
RiskBadge
Dialog
ConfirmationDialog
ErrorBanner
EmptyState
SuccessState
SettingsRow
```

---

# 15. Localization

Supported languages:

```text
Uzbek
Russian
English
```

Rules:

- No hard-coded user-facing strings in business logic.
- Use stable localization keys.
- Numbers and sizes use localized formatting where appropriate.

---

# 16. Logging & Diagnostics

Levels:

```text
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

Never log secrets or unnecessary personal data.

Important events:

- application start;
- scan start/end;
- cleanup start/end;
- safety rejection;
- permission rejection;
- file deletion result;
- unexpected exception;
- update/installer event.

---

# 17. Error Code Taxonomy

```text
FILE_NOT_FOUND
ACCESS_DENIED
FILE_LOCKED
INVALID_PATH
PATH_TOO_LONG
INVALID_REPARSE_POINT
PROTECTED_PATH
UNKNOWN_RULE
DISK_UNAVAILABLE
PERMISSION_REQUIRED
USER_CANCELLED
IO_ERROR
UNKNOWN_ERROR
```

---

# 18. Performance Requirements

- UI thread must never perform long recursive filesystem scans.
- Scanning uses worker threads/tasks.
- Cancellation must propagate to scanner workers.
- Progress must be reported periodically, not for every file if that causes UI overhead.
- Memory usage should not grow linearly with millions of scanned files when results can be streamed/aggregated.
- Use bounded concurrency.

---

# 19. Agent Development Rules

These rules apply to every AI coding agent.

## Rule A — Read before editing

Inspect the existing implementation and relevant tests before modifying code.

## Rule B — One task at a time

Agents should work against a specific task ID.

## Rule C — No scope creep

Do not add unrelated features.

## Rule D — Safety first

Never weaken protected-path checks to make a test pass.

## Rule E — Tests are mandatory

Every engine change must add/update tests.

## Rule F — Explainability

New cleanup rules require a reason and rule identifier.

## Rule G — Backward compatibility

Do not break Windows 7 compatibility without an explicit architecture decision.

## Rule H — No hidden destructive behavior

No automatic permanent deletion.

## Rule I — Keep dependencies minimal

Every new dependency needs justification for compatibility, licensing, size, and security.

## Rule J — Verify before claiming done

Run tests, compile checks, and targeted smoke tests before marking the task complete.

---

# 20. Git / Branch Strategy

```text
main
├── develop
├── feature/Txxx-description
├── bugfix/Txxx-description
└── release/vX.Y.Z
```

Commit style:

```text
feat(scanner): add temp scanner
fix(safety): block junction traversal
refactor(ui): extract risk badge
 test(safety): add protected path coverage
docs(plan): update agent task specification
```

---

# 21. Definition of Done

A task is DONE only when:

- code is implemented;
- type/API contracts are consistent;
- tests are added or updated;
- no known regression is introduced;
- logging/errors are handled;
- compatibility impact is understood;
- documentation is updated when behavior changes;
- the task acceptance criteria are satisfied.

---

# 22. Master Task Backlog

## PHASE 0 — Foundation

- [ ] T001 Create repository.
- [ ] T002 Define Python runtime baseline.
- [ ] T003 Pin PyQt5 dependency.
- [ ] T004 Create requirements files.
- [ ] T005 Create repository structure.
- [ ] T006 Create configuration system.
- [ ] T007 Create platform abstraction.
- [ ] T008 Create application logging.
- [ ] T009 Create version module.
- [ ] T010 Create build configuration.

### Acceptance
Application launches, shows version, writes logs, and does not perform cleanup.

---

## PHASE 1 — Windows Compatibility

- [ ] T011 Implement Windows version detector.
- [ ] T012 Implement Windows build detector.
- [ ] T013 Implement architecture detector.
- [ ] T014 Implement Windows 7 compatibility adapter.
- [ ] T015 Implement Windows 8 compatibility adapter.
- [ ] T016 Implement Windows 8.1 compatibility adapter.
- [ ] T017 Implement Windows 10 compatibility adapter.
- [ ] T018 Implement Windows 11 compatibility adapter.
- [ ] T019 Handle unsupported OS gracefully.
- [ ] T020 Create OS capability registry.

### Acceptance
OS/version/architecture are displayed correctly and optional features are gated without crashes.

---

## PHASE 2 — Drive Engine

- [ ] T021 Enumerate logical drives.
- [ ] T022 Detect C: drive.
- [ ] T023 Detect D: drive.
- [ ] T024 Detect removable drives.
- [ ] T025 Detect filesystem type.
- [ ] T026 Read free space.
- [ ] T027 Read total space.
- [ ] T028 Create drive metadata abstraction.
- [ ] T029 Handle unavailable drives.
- [ ] T030 Build drive selection UI.

### Acceptance
Drives are detected correctly, inaccessible drives do not crash the app, and free-space values are shown.

---

## PHASE 3 — Known Folder Engine

- [ ] T031 Create known-folder abstraction.
- [ ] T032 Resolve LocalAppData.
- [ ] T033 Resolve RoamingAppData.
- [ ] T034 Resolve ProgramData.
- [ ] T035 Resolve Windows directory.
- [ ] T036 Resolve user Temp.
- [ ] T037 Resolve system/shared Temp.
- [ ] T038 Add optional per-user folder resolution.
- [ ] T039 Add Recycle Bin abstraction.
- [ ] T040 Validate resolved folders.

### Acceptance
Known folders resolve through platform-aware logic and not hard-coded user names.

---

## PHASE 4 — Safety Engine

- [ ] T041 Create protected-path registry.
- [ ] T042 Protect System32.
- [ ] T043 Protect SysWOW64.
- [ ] T044 Protect WinSxS.
- [ ] T045 Protect Boot directories.
- [ ] T046 Protect Program Files.
- [ ] T047 Protect Program Files (x86).
- [ ] T048 Protect Documents.
- [ ] T049 Protect Desktop.
- [ ] T050 Protect Downloads.
- [ ] T051 Protect Pictures.
- [ ] T052 Protect Videos.
- [ ] T053 Detect junctions.
- [ ] T054 Detect symbolic links/reparse points.
- [ ] T055 Implement locked-file detection.
- [ ] T056 Implement file age policy.
- [ ] T057 Implement extension policy.
- [ ] T058 Implement ownership classification.
- [ ] T059 Implement risk scoring.
- [ ] T060 Implement final deletion safety gate.

### Acceptance
All hard-protected paths return BLOCKED; unknown locations never become SAFE automatically; safety tests cover traversal and reparse points.

---

## PHASE 5 — Scanner Engine

- [ ] T061 Define BaseScanner interface.
- [ ] T062 Implement filesystem walker.
- [ ] T063 Implement bounded parallel scanning.
- [ ] T064 Implement cancellation.
- [ ] T065 Implement progress reporting.
- [ ] T066 Implement TempScanner.
- [ ] T067 Implement CacheScanner.
- [ ] T068 Implement LogScanner.
- [ ] T069 Implement BrowserScanner interface.
- [ ] T070 Implement InstallerLeftoversScanner.
- [ ] T071 Implement RecycleBinScanner.
- [ ] T072 Implement UpdateLeftoversScanner.
- [ ] T073 Implement CrashDumpScanner.
- [ ] T074 Implement ThumbnailScanner.
- [ ] T075 Implement ApplicationCacheScanner.
- [ ] T076 Implement LargeFileScanner.
- [ ] T077 Implement duplicate-candidate detector.
- [ ] T078 Aggregate scanner results.
- [ ] T079 Deduplicate results.
- [ ] T080 Profile and optimize scanning.

### Acceptance
Scanning is cancellable, responsive, deterministic enough for repeated runs, and does not delete anything.

---

## PHASE 6 — Analyzer

- [ ] T081 Implement file classification.
- [ ] T082 Implement category grouping.
- [ ] T083 Implement size aggregation.
- [ ] T084 Implement age aggregation.
- [ ] T085 Implement risk aggregation.
- [ ] T086 Calculate reclaimable space.
- [ ] T087 Calculate confidence score.
- [ ] T088 Separate review-required items.
- [ ] T089 Separate blocked items.
- [ ] T090 Generate scan report.

### Acceptance
Scanner results become an explainable list with safe/review/blocked states and correct byte totals.

---

## PHASE 7 — Cleanup Engine

- [ ] T091 Implement cleanup planner.
- [ ] T092 Revalidate every target before deletion.
- [ ] T093 Implement permission validation.
- [ ] T094 Implement locked-file handling.
- [ ] T095 Implement safe delete.
- [ ] T096 Implement Recycle Bin strategy.
- [ ] T097 Implement permanent-delete strategy as disabled-by-default internal capability.
- [ ] T098 Implement safe retry logic.
- [ ] T099 Implement partial-failure handling.
- [ ] T100 Verify cleanup results.
- [ ] T101 Calculate recovered space.
- [ ] T102 Save cleanup statistics.
- [ ] T103 Generate cleanup report.
- [ ] T104 Implement cancellation.
- [ ] T105 Implement recovery/rollback strategy.

### Acceptance
Only safety-approved items are removed, locked/system files are skipped, failures are reported, and the UI remains responsive.

---

## PHASE 8 — Administrator/UAC

- [ ] T106 Detect administrator state.
- [ ] T107 Implement UAC launcher.
- [ ] T108 Implement elevated-process handoff.
- [ ] T109 Implement permission error UI.
- [ ] T110 Enforce least-privilege mode.
- [ ] T111 Add administrator cleanup mode.

### Acceptance
App starts non-elevated, asks for elevation only when required, and does not duplicate or lose cleanup state during elevation.

---

## PHASE 9 — Browser Cleanup

- [ ] T112 Detect Chrome.
- [ ] T113 Detect Edge.
- [ ] T114 Detect Firefox.
- [ ] T115 Detect Opera.
- [ ] T116 Detect running browser processes.
- [ ] T117 Define browser cache rules.
- [ ] T118 Implement browser-safe cleanup.
- [ ] T119 Implement browser cleanup preview.

### Acceptance
Browser cleanup clearly separates cache from sessions/cookies and never silently deletes user history/session data outside approved rules.

---

## PHASE 10 — Database

- [ ] T120 Initialize SQLite.
- [ ] T121 Create schema.
- [ ] T122 Create migration system.
- [ ] T123 Implement scan session model.
- [ ] T124 Implement cleanup session model.
- [ ] T125 Implement cleanup item model.
- [ ] T126 Implement settings model.
- [ ] T127 Implement rules model.
- [ ] T128 Implement ignored-path model.
- [ ] T129 Implement statistics model.

### Acceptance
Scan and cleanup history survive application restart and schema changes are versioned.

---

## PHASE 11 — PyQt UI

- [ ] T130 Create application shell.
- [ ] T131 Create main window.
- [ ] T132 Create sidebar navigation.
- [ ] T133 Create header.
- [ ] T134 Create dashboard cards.
- [ ] T135 Create drive cards.
- [ ] T136 Create scanning state animation.
- [ ] T137 Create progress screen.
- [ ] T138 Create results table.
- [ ] T139 Create category cards.
- [ ] T140 Create cleanup confirmation dialog.
- [ ] T141 Create cleanup result screen.
- [ ] T142 Create settings UI.
- [ ] T143 Create logs viewer.
- [ ] T144 Create About page.
- [ ] T145 Create system tray behavior.
- [ ] T146 Create user notifications.

### Acceptance
All long-running work remains outside the UI thread and every major state has loading, success, empty, error, and cancelled UX.

---

## PHASE 12 — Design System

- [ ] T147 Define typography scale.
- [ ] T148 Define spacing scale.
- [ ] T149 Select icon strategy.
- [ ] T150 Build button components.
- [ ] T151 Build card components.
- [ ] T152 Build table components.
- [ ] T153 Build progress components.
- [ ] T154 Build dialogs.
- [ ] T155 Build warning/safety components.
- [ ] T156 Build dark theme.
- [ ] T157 Build light theme.
- [ ] T158 Create responsive desktop layouts.
- [ ] T159 Verify Windows 7 visual compatibility.
- [ ] T160 Verify DPI scaling.

### Acceptance
Visual components are reusable, consistent, and readable at supported DPI settings.

---

## PHASE 13 — Settings & Personalization

- [ ] T161 Implement localization framework.
- [ ] T162 Add Uzbek translations.
- [ ] T163 Add Russian translations.
- [ ] T164 Add English translations.
- [ ] T165 Add startup settings.
- [ ] T166 Add tray settings.
- [ ] T167 Add cleanup defaults.
- [ ] T168 Add scan-depth settings.
- [ ] T169 Add custom protected paths.
- [ ] T170 Add ignored paths.

### Acceptance
User settings persist between launches and custom protection can only strengthen, not weaken, system safety boundaries.

---

## PHASE 14 — Reporting

- [ ] T171 Add cleanup history page.
- [ ] T172 Calculate cumulative recovered space.
- [ ] T173 Track deleted files.
- [ ] T174 Track skipped files.
- [ ] T175 Track errors.
- [ ] T176 Add weekly statistics.
- [ ] T177 Add monthly statistics.
- [ ] T178 Build cleanup report.
- [ ] T179 Add report export.
- [ ] T180 Add CSV/JSON export.

### Acceptance
Statistics reconcile with cleanup-session records and reports identify failed/skipped items.

---

## PHASE 15 — Security Hardening

- [ ] T181 Add path traversal protection.
- [ ] T182 Add deletion-boundary validation.
- [ ] T183 Add TOCTOU mitigation tests.
- [ ] T184 Harden symlink/junction handling.
- [ ] T185 Protect executable targets outside explicit safe rules.
- [ ] T186 Expand system-file heuristics.
- [ ] T187 Validate configuration integrity.
- [ ] T188 Validate audit log behavior.
- [ ] T189 Add safe-mode cleanup.
- [ ] T190 Add emergency cleanup-disable switch.

### Acceptance
Security tests attempt malicious/ambiguous paths and all are rejected or routed to review/blocked.

---

## PHASE 16 — Performance

- [ ] T191 Profile scanner.
- [ ] T192 Profile memory usage.
- [ ] T193 Profile CPU usage.
- [ ] T194 Optimize disk IO.
- [ ] T195 Tune worker pool.
- [ ] T196 Remove UI freezes.
- [ ] T197 Benchmark large drive.
- [ ] T198 Benchmark million-file fixture.
- [ ] T199 Benchmark long paths.
- [ ] T200 Benchmark low-RAM environment.

### Acceptance
Performance tests do not introduce UI hangs and memory usage remains bounded under large scan loads.

---

## PHASE 17 — Automated Testing

- [ ] T201 Create unit test framework.
- [ ] T202 Test scanner interfaces.
- [ ] T203 Test safety engine.
- [ ] T204 Test cleanup engine.
- [ ] T205 Test permission handling.
- [ ] T206 Test locked files.
- [ ] T207 Test junctions.
- [ ] T208 Test symbolic links.
- [ ] T209 Test database repositories.
- [ ] T210 Test key UI state transitions.
- [ ] T211 Windows 7 test matrix.
- [ ] T212 Windows 8 test matrix.
- [ ] T213 Windows 8.1 test matrix.
- [ ] T214 Windows 10 test matrix.
- [ ] T215 Windows 11 test matrix.

### Acceptance
All critical safety paths have automated tests and every supported OS gets smoke validation.

---

## PHASE 18 — Installer / Release

- [ ] T216 Create application icon.
- [ ] T217 Package executable.
- [ ] T218 Build installer.
- [ ] T219 Implement uninstall.
- [ ] T220 Implement startup registration only when enabled.
- [ ] T221 Implement upgrade path.
- [ ] T222 Implement repair installation.
- [ ] T223 Implement installer rollback.
- [ ] T224 Prepare code-signing workflow.
- [ ] T225 Produce release build.

### Acceptance
Install, launch, scan, cleanup, upgrade, uninstall, and reinstall all work in supported environments.

---

## PHASE 19 — QA / Final Verification

- [ ] T226 Validate clean Windows 7 VM.
- [ ] T227 Validate clean Windows 8 VM.
- [ ] T228 Validate clean Windows 8.1 VM.
- [ ] T229 Validate clean Windows 10 VM.
- [ ] T230 Validate clean Windows 11 VM.
- [ ] T231 Test low-disk condition.
- [ ] T232 Test unusual permission conditions.
- [ ] T233 Test locked files.
- [ ] T234 Test huge Temp directory.
- [ ] T235 Test no-admin mode.
- [ ] T236 Test multiple Windows user profiles.
- [ ] T237 Test interrupted cleanup.
- [ ] T238 Test crash/restart recovery.
- [ ] T239 Verify uninstall cleanup.
- [ ] T240 Perform final compatibility audit.

### Acceptance
No critical safety defect remains; all release gates pass.

---

# 23. Extended Post-MVP Backlog

## V1.1

- [ ] P001 Better browser cache rules.
- [ ] P002 Advanced storage analyzer.
- [ ] P003 Duplicate candidate visualization.
- [ ] P004 Improved cleanup history charts.
- [ ] P005 Scheduled scan.
- [ ] P006 Scheduled cleanup with strict safe-only mode.
- [ ] P007 Better tray experience.
- [ ] P008 Richer export reports.
- [ ] P009 Custom scan profiles.
- [ ] P010 Portable build investigation.

## V2

- [ ] P011 Startup application analyzer.
- [ ] P012 Installed-app storage analyzer.
- [ ] P013 Storage heatmap.
- [ ] P014 Duplicate finder with manual confirmation.
- [ ] P015 Smart recommendations.
- [ ] P016 Cleanup presets.
- [ ] P017 Per-user cleanup profiles.
- [ ] P018 Enterprise policy mode.
- [ ] P019 Centralized diagnostics.
- [ ] P020 Crash telemetry only with explicit consent.

## V3 — AI Assistant Layer

- [ ] P021 AI scan summary.
- [ ] P022 AI explanation of cleanup categories.
- [ ] P023 AI recommendation engine.
- [ ] P024 Natural-language cleanup queries.
- [ ] P025 AI must not have unrestricted delete authority.
- [ ] P026 AI action approval workflow.
- [ ] P027 AI audit trail.
- [ ] P028 Prompt-injection-resistant action boundary.
- [ ] P029 Explainable recommendations.
- [ ] P030 Human approval before destructive operations.

---

# 24. AI-Agent Operating Protocol

AI agents must use the following cycle for every task:

```text
1. Read TASK ID.
2. Inspect repository state.
3. Inspect relevant modules/tests.
4. State implementation intent internally.
5. Implement smallest correct change.
6. Add/update tests.
7. Run targeted tests.
8. Run compatibility/compile checks.
9. Review for safety regressions.
10. Update task status and notes.
```

### Never do this

```text
Scan result → immediate delete
```

### Always do this

```text
Scan → classify → safety gate → user selection → revalidate → delete → verify → audit
```

---

# 25. Agent Handoff Template

Each agent should receive a task using this structure:

```text
TASK ID: Txxx
TITLE: <task title>

CONTEXT:
<why this task exists>

SCOPE:
<files/modules that may be changed>

DO NOT:
<forbidden changes>

REQUIREMENTS:
<technical requirements>

ACCEPTANCE CRITERIA:
- ...
- ...
- ...

TESTS:
<tests to add/run>

DELIVERABLE:
<expected output>
```

---

# 26. Critical Safety Test Scenarios

Every release candidate must test at least:

1. Attempted deletion of `System32` path → BLOCKED.
2. Attempted deletion of `WinSxS` path → BLOCKED.
3. Attempted deletion of Documents file → BLOCKED.
4. Attempted deletion through `..` traversal → BLOCKED.
5. Attempted deletion through junction → BLOCKED or safely isolated.
6. Locked temporary file → SKIPPED, no crash.
7. File disappears after scan → handled gracefully.
8. File changes category after scan → revalidated.
9. Permission denied → structured error.
10. D: drive unavailable during scan → handled gracefully.
11. User cancellation during scan → workers stop safely.
12. User cancellation during cleanup → no unsafe partial state.
13. Application crash during cleanup → state recoverable/auditable.
14. Multiple users → user-scoped cleanup does not leak into other profiles.
15. System clock anomalies → age rules fail safe.

---

# 27. Product Metrics

Track locally:

- scan count;
- cleanup count;
- bytes discovered;
- bytes recovered;
- skipped files;
- failed files;
- average scan duration;
- average cleanup duration;
- top cleanup categories.

Do not silently transmit telemetry.

---

# 28. Release Gates

Release is blocked if any of these are true:

- system-critical path can be marked SAFE;
- user personal path can be automatically deleted;
- scanner crashes on inaccessible directory;
- cleanup bypasses Safety Engine;
- UI freezes during normal scan;
- Windows 7 build fails baseline checks;
- installer removes unrelated user data;
- release artifact is not reproducible/documented;
- dependency/license status is unknown.

---

# 29. Commercialization Checklist

Before public sale/distribution:

- [ ] Product name/trademark review.
- [ ] Dependency licenses reviewed.
- [ ] PyQt licensing decision documented.
- [ ] Third-party notices collected.
- [ ] Executable signing strategy completed.
- [ ] Privacy policy prepared if telemetry/update checks are introduced.
- [ ] Crash reporting consent designed if introduced.
- [ ] Update mechanism secured.
- [ ] Installer integrity verified.
- [ ] Support documentation prepared.

---

# 30. Recommended MVP Order

Do not implement all 240 tasks linearly without integration milestones.

### Milestone A — Foundation

T001–T020

### Milestone B — Drive + Known Folders

T021–T040

### Milestone C — Safety Engine

T041–T060

### Milestone D — First Real Scan

T061–T090

### Milestone E — First Real Cleanup

T091–T111

### Milestone F — UI Productization

T120–T170

### Milestone G — Reporting + Security

T171–T190

### Milestone H — Performance + QA

T191–T215

### Milestone I — Installer + Release

T216–T240

---

# 31. MVP Definition

The MVP is complete when the user can:

```text
Open CleanGuard
    ↓
See C:/D: drives
    ↓
Scan safely
    ↓
See categories and sizes
    ↓
Review safe/review/blocked items
    ↓
Select safe cleanup items
    ↓
Confirm cleanup
    ↓
Application revalidates targets
    ↓
Cleanup executes
    ↓
Results are verified
    ↓
History is saved
    ↓
User sees recovered space
```

The MVP must **not** claim that it “optimizes Windows” unless an actual, measurable, tested operation is implemented. The product should communicate storage cleanup honestly.

---

# 32. Final CTO Architecture Decision

### Chosen architecture

```text
PyQt5 Presentation Layer
        ↓
Application Services
        ↓
Core Domain
 ┌──────┼───────────────┐
Scan  Safety        Cleanup
        ↓                ↓
   Windows Adapters / FileSystem
        ↓
      Windows OS

SQLite ← History / Settings / Audit
```

### Key engineering decision

The **Safety Engine is a mandatory dependency of the Cleanup Engine**. No UI component, scanner, plugin, or future AI module may bypass it.

### Future AI boundary

```text
AI
 ↓
Recommend / Explain
 ↓
Human approval
 ↓
Safety Engine
 ↓
Cleanup Engine
```

AI is advisory by architecture, not an unrestricted destructive actor.

---

# 33. Immediate Next Tasks for the Coding Agent

Start with:

```text
T001
T002
T003
T004
T005
T006
T007
T008
T009
T010
```

Then:

```text
T011 → T020
T021 → T040
T041 → T060
```

Do not begin dangerous cleanup modules before T041–T060 are implemented and tested.

---

# 34. Project Status Template

```text
PROJECT: CleanGuard
VERSION: 0.1.0

FOUNDATION: [ ]
WINDOWS COMPATIBILITY: [ ]
DRIVE ENGINE: [ ]
KNOWN FOLDERS: [ ]
SAFETY ENGINE: [ ]
SCANNER ENGINE: [ ]
ANALYZER: [ ]
CLEANUP ENGINE: [ ]
DATABASE: [ ]
UI: [ ]
DESIGN SYSTEM: [ ]
LOCALIZATION: [ ]
REPORTING: [ ]
SECURITY HARDENING: [ ]
PERFORMANCE: [ ]
TESTING: [ ]
INSTALLER: [ ]
RELEASE QA: [ ]
```

---

# 35. Agent Completion Report Template

```text
TASK ID:
STATUS: DONE / BLOCKED

CHANGED FILES:
- ...

IMPLEMENTED:
- ...

TESTS:
- ...

COMPATIBILITY:
- Python 3.8: PASS/FAIL
- Windows target impact: ...

SAFETY REVIEW:
- Protected paths affected: YES/NO
- Cleanup behavior affected: YES/NO
- New deletion capability: YES/NO

KNOWN LIMITATIONS:
- ...

NEXT TASK:
- ...
```

---

# 36. Success Criteria

CleanGuard is successful when it is:

- safe by default;
- understandable to non-technical users;
- responsive during heavy scanning;
- compatible with target Windows versions;
- modular enough for multiple AI coding agents;
- testable without touching a real production OS;
- auditable after cleanup;
- commercially maintainable.

The guiding principle remains:

> **Never trade system safety for a larger “GB cleaned” number.**

