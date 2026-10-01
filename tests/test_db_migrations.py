"""
Schema migration tests: fresh install, upgrade of a legacy v1 database, and
atomic rollback of a failing migration.
"""

import sqlite3
from unittest.mock import patch

import pytest

from cleanguard.database import db as db_module
from cleanguard.database.db import DatabaseManager
from cleanguard.database.schema import CURRENT_SCHEMA_VERSION

LEGACY_V1_SQL = """
CREATE TABLE schema_version (version INTEGER PRIMARY KEY, applied_at REAL NOT NULL);
CREATE TABLE scan_sessions (
    id TEXT PRIMARY KEY, started_at REAL NOT NULL, finished_at REAL NOT NULL, status TEXT NOT NULL,
    files_scanned INTEGER NOT NULL, items_found INTEGER NOT NULL, bytes_found INTEGER NOT NULL,
    safe_items INTEGER NOT NULL, review_items INTEGER NOT NULL, blocked_items INTEGER NOT NULL
);
CREATE TABLE cleanup_sessions (
    id TEXT PRIMARY KEY, scan_id TEXT, started_at REAL NOT NULL, finished_at REAL NOT NULL,
    status TEXT NOT NULL, files_deleted INTEGER NOT NULL, files_skipped INTEGER NOT NULL,
    files_failed INTEGER NOT NULL, bytes_recovered INTEGER NOT NULL
);
CREATE TABLE cleanup_items (
    id TEXT PRIMARY KEY, cleanup_id TEXT NOT NULL, path TEXT NOT NULL, category TEXT NOT NULL,
    risk_level TEXT NOT NULL, status TEXT NOT NULL, size INTEGER NOT NULL,
    error_code TEXT, error_message TEXT
);
CREATE TABLE statistics (metric_key TEXT PRIMARY KEY, metric_value REAL NOT NULL, updated_at REAL NOT NULL);
CREATE TABLE ignored_paths (id TEXT PRIMARY KEY, path TEXT UNIQUE NOT NULL, reason TEXT, created_at REAL NOT NULL);
INSERT INTO schema_version VALUES (1, 0);
INSERT INTO cleanup_sessions VALUES ('old-1', NULL, 1, 2, 'COMPLETED', 7, 0, 0, 4096);
"""


def _objects(path, kind):
    with sqlite3.connect(path) as conn:
        return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = ?;", (kind,))}


def _version(path):
    with sqlite3.connect(path) as conn:
        return conn.execute("SELECT MAX(version) FROM schema_version;").fetchone()[0]


def test_fresh_database_is_fully_migrated(tmp_path):
    path = str(tmp_path / "fresh.db")
    DatabaseManager(db_path=path)
    assert _version(path) == CURRENT_SCHEMA_VERSION
    assert "ignored_paths" not in _objects(path, "table")
    assert "idx_cleanup_items_cleanup_id" in _objects(path, "index")


def test_legacy_v1_database_upgrades_and_keeps_data(tmp_path):
    path = str(tmp_path / "legacy.db")
    with sqlite3.connect(path) as conn:
        conn.executescript(LEGACY_V1_SQL)

    DatabaseManager(db_path=path)

    assert _version(path) == CURRENT_SCHEMA_VERSION
    assert "ignored_paths" not in _objects(path, "table")
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT files_deleted FROM cleanup_sessions WHERE id='old-1';").fetchone()[0] == 7
        versions = [r[0] for r in conn.execute("SELECT version FROM schema_version ORDER BY version;")]
    assert versions == list(range(1, CURRENT_SCHEMA_VERSION + 1))


def test_reopening_is_idempotent(tmp_path):
    path = str(tmp_path / "again.db")
    DatabaseManager(db_path=path)
    DatabaseManager(db_path=path)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM schema_version;").fetchone()[0] == CURRENT_SCHEMA_VERSION


def test_failing_migration_rolls_back_atomically(tmp_path):
    path = str(tmp_path / "broken.db")
    DatabaseManager(db_path=path)
    bad = dict(db_module.MIGRATIONS)
    bad[CURRENT_SCHEMA_VERSION + 1] = [
        "CREATE TABLE half_applied (x INTEGER);",
        "THIS IS NOT SQL;",
    ]
    with patch.object(db_module, "MIGRATIONS", bad):
        with pytest.raises(sqlite3.Error):
            DatabaseManager(db_path=path)

    assert _version(path) == CURRENT_SCHEMA_VERSION
    assert "half_applied" not in _objects(path, "table")
