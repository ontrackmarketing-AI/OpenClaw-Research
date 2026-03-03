"""
Offline resilience utilities.

Provides functions for monitoring unsynced capture backlog and
cleaning up old captures beyond the retention period.
"""

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger("openclaw-capture.offline")


def get_unsynced_count(db_path: str) -> int:
    """
    Count captures that have not yet been synced to Mac receiver.

    Args:
        db_path: Path to local SQLite database.

    Returns:
        Number of rows where synced = 0.
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM captures WHERE synced = 0")
        result = cursor.fetchone()
        return result[0] if result else 0
    finally:
        conn.close()


def cleanup_old_captures(db_path: str, retention_days: int) -> int:
    """
    Delete local captures older than retention_days.

    Also deletes corresponding screenshot files from disk.

    Args:
        db_path: Path to local SQLite database.
        retention_days: Number of days to retain captures.

    Returns:
        Number of captures deleted.
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    deleted_count = 0

    try:
        # Find captures older than retention period
        cursor.execute(
            """
            SELECT id, image_path FROM captures
            WHERE captured_at < datetime('now', ? || ' days')
            """,
            (f"-{retention_days}",),
        )
        old_captures = cursor.fetchall()

        if not old_captures:
            return 0

        # Delete screenshot files from disk
        for capture_id, image_path in old_captures:
            if image_path:
                path = Path(image_path)
                if path.exists():
                    try:
                        path.unlink()
                    except OSError as e:
                        logger.warning(
                            "Failed to delete screenshot %s: %s", image_path, e
                        )

        # Delete rows from database
        old_ids = [row[0] for row in old_captures]
        placeholders = ",".join("?" for _ in old_ids)
        cursor.execute(
            f"DELETE FROM captures WHERE id IN ({placeholders})", old_ids
        )
        conn.commit()

        deleted_count = len(old_ids)
        logger.info(
            "Cleaned up %d captures older than %d days",
            deleted_count,
            retention_days,
        )

        # Clean up empty date directories
        screenshots_dir = Path.home() / ".openclaw-capture" / "screenshots"
        if screenshots_dir.exists():
            for date_dir in screenshots_dir.iterdir():
                if date_dir.is_dir() and not any(date_dir.iterdir()):
                    try:
                        date_dir.rmdir()
                    except OSError:
                        pass

    except Exception as e:
        logger.error("Error during cleanup: %s", e)
    finally:
        conn.close()

    return deleted_count
