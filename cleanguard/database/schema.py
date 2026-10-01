"""
Database Schema and Migrations for CleanGuard.

BASE_SCHEMA_SQL is the original (version 1) schema and must never change.
Every later change is appended to MIGRATIONS under the next version number;
DatabaseManager applies the pending ones in order, each in its own transaction.
"""

from typing import Dict, List

BASE_SCHEMA_VERSION = 1

BASE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS scan_sessions (
    id TEXT PRIMARY KEY,
    started_at REAL NOT NULL,
    finished_at REAL NOT NULL,
    status TEXT NOT NULL,
    files_scanned INTEGER NOT NULL,
    items_found INTEGER NOT NULL,
    bytes_found INTEGER NOT NULL,
    safe_items INTEGER NOT NULL,
    review_items INTEGER NOT NULL,
    blocked_items INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS cleanup_sessions (
    id TEXT PRIMARY KEY,
    scan_id TEXT,
    started_at REAL NOT NULL,
    finished_at REAL NOT NULL,
    status TEXT NOT NULL,
    files_deleted INTEGER NOT NULL,
    files_skipped INTEGER NOT NULL,
    files_failed INTEGER NOT NULL,
    bytes_recovered INTEGER NOT NULL,
    FOREIGN KEY(scan_id) REFERENCES scan_sessions(id)
);

CREATE TABLE IF NOT EXISTS cleanup_items (
    id TEXT PRIMARY KEY,
    cleanup_id TEXT NOT NULL,
    path TEXT NOT NULL,
    category TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    status TEXT NOT NULL,
    size INTEGER NOT NULL,
    error_code TEXT,
    error_message TEXT,
    FOREIGN KEY(cleanup_id) REFERENCES cleanup_sessions(id)
);

CREATE TABLE IF NOT EXISTS statistics (
    metric_key TEXT PRIMARY KEY,
    metric_value REAL NOT NULL,
    updated_at REAL NOT NULL
);
"""

# version -> statements. Keep them idempotent (IF [NOT] EXISTS): version 2 was
# first shipped inside the base script, so some databases already contain it.
MIGRATIONS: Dict[int, List[str]] = {
    2: [
        # History page sorts sessions by time and loads items per session.
        "CREATE INDEX IF NOT EXISTS idx_cleanup_items_cleanup_id ON cleanup_items(cleanup_id);",
        "CREATE INDEX IF NOT EXISTS idx_cleanup_sessions_started_at ON cleanup_sessions(started_at);",
        "CREATE INDEX IF NOT EXISTS idx_scan_sessions_started_at ON scan_sessions(started_at);",
    ],
    3: [
        # Never used: user exclusions live in the "custom_protected_paths" setting.
        "DROP TABLE IF EXISTS ignored_paths;",
    ],
}

CURRENT_SCHEMA_VERSION = max(MIGRATIONS) if MIGRATIONS else BASE_SCHEMA_VERSION
