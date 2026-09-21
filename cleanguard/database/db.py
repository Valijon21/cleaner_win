"""
SQLite Database Connection and Migration Manager.
"""

import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from typing import Optional, Generator
from cleanguard.database.schema import CREATE_TABLES_SQL, CURRENT_SCHEMA_VERSION
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
        """Apply schema and run migrations."""
        with self._lock:
            try:
                os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
                with self.session() as conn:
                    cursor = conn.cursor()
                    cursor.executescript(CREATE_TABLES_SQL)

                    # Check schema version
                    cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1;")
                    row = cursor.fetchone()
                    if not row:
                        cursor.execute(
                            "INSERT INTO schema_version (version, applied_at) VALUES (?, ?);",
                            (CURRENT_SCHEMA_VERSION, time.time()),
                        )
                logger.info(f"Database initialized successfully at {self.db_path}.")
            except Exception as exc:
                logger.error(f"Failed to initialize database: {exc}")
                raise

