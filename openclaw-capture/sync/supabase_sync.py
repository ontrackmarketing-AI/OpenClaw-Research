"""
Supabase sync service.

Batch-syncs unsynced captures from local SQLite to Supabase REST API.
Designed for offline resilience: if Supabase is unreachable, captures
remain in local SQLite and sync catches up when connectivity resumes.
"""

import json
import logging
import sqlite3
import threading
import time
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger("openclaw-capture.sync")


def sync_unsynced_captures(config: dict[str, Any], db_path: str) -> int:
    """
    Fetch up to 50 unsynced captures and POST them to Supabase REST API.

    Args:
        config: Configuration dict with supabase_url and supabase_service_role_key.
        db_path: Path to local SQLite database.

    Returns:
        Number of captures successfully synced.
    """
    supabase_url = config.get("supabase_url", "")
    service_key = config.get("supabase_service_role_key", "")

    if not supabase_url or not service_key:
        logger.debug("Supabase not configured, skipping sync")
        return 0

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Fetch up to 50 unsynced rows
        cursor.execute(
            """
            SELECT id, captured_at, app_name, window_title,
                   ocr_text, content_hash
            FROM captures
            WHERE synced = 0
            ORDER BY captured_at ASC
            LIMIT 50
            """,
        )
        rows = cursor.fetchall()

        if not rows:
            return 0

        # Build batch payload for Supabase REST API
        payload = []
        local_ids = []
        for row in rows:
            payload.append(
                {
                    "captured_at": row["captured_at"],
                    "source_device": "windows_desktop",
                    "monitor_index": 0,
                    "window_title": row["window_title"],
                    "app_name": row["app_name"],
                    "ocr_text": row["ocr_text"],
                    "content_hash": row["content_hash"],
                }
            )
            local_ids.append(row["id"])

        # POST to Supabase REST API
        url = f"{supabase_url.rstrip('/')}/rest/v1/screen_captures"
        headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)

        if response.status_code == 201:
            # Mark rows as synced
            placeholders = ",".join("?" for _ in local_ids)
            cursor.execute(
                f"UPDATE captures SET synced = 1 WHERE id IN ({placeholders})",
                local_ids,
            )
            conn.commit()

            logger.info(
                json.dumps(
                    {
                        "level": "INFO",
                        "component": "sync",
                        "action": "batch_synced",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "count": len(local_ids),
                    }
                )
            )
            return len(local_ids)
        else:
            logger.error(
                json.dumps(
                    {
                        "level": "ERROR",
                        "component": "sync",
                        "action": "sync_failed",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "status_code": response.status_code,
                        "response": response.text[:500],
                    }
                )
            )
            return 0

    except Exception as e:
        logger.error(
            json.dumps(
                {
                    "level": "ERROR",
                    "component": "sync",
                    "action": "sync_error",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "error": str(e),
                }
            )
        )
        return 0
    finally:
        conn.close()


def run_sync_loop(
    config: dict[str, Any],
    db_path: str,
    shutdown_event: threading.Event,
) -> None:
    """
    Run sync_unsynced_captures() every sync_interval_seconds.

    Wrapped in try/except with continue to never crash.
    """
    interval = config.get("sync_interval_seconds", 60)

    logger.info(
        json.dumps(
            {
                "level": "INFO",
                "component": "sync",
                "action": "sync_loop_started",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "interval_seconds": interval,
            }
        )
    )

    while not shutdown_event.is_set():
        try:
            synced = sync_unsynced_captures(config, db_path)
            if synced > 0:
                logger.debug("Synced %d captures", synced)
        except Exception as e:
            logger.error(
                json.dumps(
                    {
                        "level": "ERROR",
                        "component": "sync",
                        "action": "sync_loop_error",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "error": str(e),
                    }
                )
            )
        time.sleep(interval)

    logger.info(
        json.dumps(
            {
                "level": "INFO",
                "component": "sync",
                "action": "sync_loop_stopped",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    )
