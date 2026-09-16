"""
Database Repositories for Scan, Cleanup, History and Statistics.
"""

import time
import uuid
from typing import List, Dict, Any
from cleanguard.database.db import DatabaseManager
from cleanguard.core.contracts import ScanSummary, CleanupSummary


class HistoryRepository:
    """Repository for querying and storing scan and cleanup sessions."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def record_scan_session(self, summary: ScanSummary, status: str = "COMPLETED") -> None:
        """Persist a completed scan session."""
        sql = """
        INSERT OR REPLACE INTO scan_sessions (
            id, started_at, finished_at, status,
            files_scanned, items_found, bytes_found,
            safe_items, review_items, blocked_items
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        with self.db.get_connection() as conn:
            conn.execute(
                sql,
                (
                    summary.scan_id,
                    summary.started_at,
                    summary.finished_at,
                    status,
                    summary.files_scanned,
                    summary.items_found,
                    summary.bytes_reclaimable,
                    summary.safe_items,
                    summary.review_items,
                    summary.blocked_items,
                ),
            )
            conn.commit()

    def record_cleanup_session(self, summary: CleanupSummary, status: str = "COMPLETED") -> None:
        """Persist a cleanup session and all itemized audit records."""
        session_sql = """
        INSERT OR REPLACE INTO cleanup_sessions (
            id, scan_id, started_at, finished_at, status,
            files_deleted, files_skipped, files_failed, bytes_recovered
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        item_sql = """
        INSERT INTO cleanup_items (
            id, cleanup_id, path, category, risk_level, status,
            size, error_code, error_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        with self.db.get_connection() as conn:
            conn.execute(
                session_sql,
                (
                    summary.cleanup_id,
                    summary.scan_id,
                    summary.started_at,
                    summary.finished_at,
                    status,
                    summary.files_deleted,
                    summary.files_skipped,
                    summary.files_failed,
                    summary.bytes_recovered,
                ),
            )

            # Insert audit items
            for item in summary.item_results:
                conn.execute(
                    item_sql,
                    (
                        item.id or str(uuid.uuid4()),
                        summary.cleanup_id,
                        item.path,
                        item.category,
                        item.risk_level.value,
                        item.status.value,
                        item.size,
                        item.error_code.value,
                        item.error_message,
                    ),
                )

            # Update cumulative statistics
            conn.execute(
                """
                INSERT INTO statistics (metric_key, metric_value, updated_at)
                VALUES ('total_bytes_recovered', ?, ?)
                ON CONFLICT(metric_key) DO UPDATE SET
                    metric_value = metric_value + excluded.metric_value,
                    updated_at = excluded.updated_at;
                """,
                (float(summary.bytes_recovered), time.time()),
            )
            conn.execute(
                """
                INSERT INTO statistics (metric_key, metric_value, updated_at)
                VALUES ('total_files_deleted', ?, ?)
                ON CONFLICT(metric_key) DO UPDATE SET
                    metric_value = metric_value + excluded.metric_value,
                    updated_at = excluded.updated_at;
                """,
                (float(summary.files_deleted), time.time()),
            )

            conn.commit()

    def get_cleanup_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent cleanup sessions."""
        sql = """
        SELECT id, scan_id, started_at, finished_at, status,
               files_deleted, files_skipped, files_failed, bytes_recovered
        FROM cleanup_sessions
        ORDER BY started_at DESC
        LIMIT ?;
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_cumulative_stats(self) -> Dict[str, float]:
        """Query lifetime recovered storage and deleted file count."""
        sql = "SELECT metric_key, metric_value FROM statistics;"
        stats = {
            "total_bytes_recovered": 0.0,
            "total_files_deleted": 0.0,
        }
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            for row in cursor.fetchall():
                stats[row["metric_key"]] = row["metric_value"]
        return stats
