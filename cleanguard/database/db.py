"""
SQLite Database Connection and Migration Manager.
"""

import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from typing import Generator, List, Optional
from cleanguard.database.schema import (
    BASE_SCHEMA_SQL,
    BASE_SCHEMA_VERSION,
    CURRENT_SCHEMA_VERSION,
    MIGRATIONS,
)
from cleanguard.utils.logging import get_logger

logger = get_logger("database")


class DatabaseManager:
    """Thread-safe SQLite database manager for CleanGuard."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or self._resolve_default_db_path()
        self._lock = threading.Lock()
        self._initialize_database()

    @staticmethod
    def _resolve_default_db_path() -> str:
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            base_dir = os.path.join(local_app_data, "CleanGuard")
        else:
            base_dir = os.path.join(os.path.expanduser("~"), ".cleanguard")
        try:
            os.makedirs(base_dir, exist_ok=True)
        except OSError:
            base_dir = "."
        return os.path.join(base_dir, "cleanguard.db")

    def get_connection(self) -> sqlite3.Connection:
        """Create a configured connection to the SQLite database."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        # Enable Write-Ahead Logging for superior concurrent performance
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    @contextmanager
    def session(self) -> Generator[sqlite3.Connection, None, None]:
        """Provide a transactional and auto-closing SQLite connection."""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _initialize_database(self) -> None:
        """Create the base schema, then apply pending migrations in order."""
        with self._lock:
            try:
                os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
                conn = self.get_connection()
                try:
                    conn.executescript(BASE_SCHEMA_SQL)
                    current = self.get_schema_version(conn)
                    if current == 0:
                        conn.execute(
                            "INSERT INTO schema_version (version, applied_at) VALUES (?, ?);",
                            (BASE_SCHEMA_VERSION, time.time()),
                        )
                        conn.commit()
                        current = BASE_SCHEMA_VERSION

                    if current > CURRENT_SCHEMA_VERSION:
                        logger.warning(
                            f"Database schema v{current} is newer than this build (v{CURRENT_SCHEMA_VERSION}); "
                            "no migrations applied."
                        )
                    for version in sorted(v for v in MIGRATIONS if v > current):
                        self._apply_migration(conn, version, MIGRATIONS[version])
                finally:
                    conn.close()
                logger.info(f"Database initialized successfully at {self.db_path}.")
            except Exception as exc:
                logger.error(f"Failed to initialize database: {exc}")
                raise

    @staticmethod
    def get_schema_version(conn: sqlite3.Connection) -> int:
        row = conn.execute("SELECT MAX(version) FROM schema_version;").fetchone()
        return int(row[0]) if row and row[0] is not None else 0

    @staticmethod
    def _apply_migration(conn: sqlite3.Connection, version: int, statements: List[str]) -> None:
        """Run one migration atomically: its statements and the version row commit together."""
        version_row = f"INSERT INTO schema_version (version, applied_at) VALUES ({int(version)}, {time.time()!r});"
        script = "\n".join(["BEGIN;", *statements, version_row, "COMMIT;"])
        try:
            conn.executescript(script)
        except Exception:
            conn.rollback()
            logger.error(f"Database migration v{version} failed and was rolled back.")
            raise
        logger.info(f"Applied database migration v{version}.")
