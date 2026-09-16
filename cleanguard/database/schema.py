"""
Database Schema and Table Definitions for CleanGuard.
"""

CURRENT_SCHEMA_VERSION = 1

CREATE_TABLES_SQL = """
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

CREATE TABLE IF NOT EXISTS ignored_paths (
    id TEXT PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    reason TEXT,
    created_at REAL NOT NULL
);
"""
