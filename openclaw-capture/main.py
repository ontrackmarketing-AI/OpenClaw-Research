"""
OpenClaw Screen Capture Daemon -- Entry Point

Starts the screen capture daemon on Windows with:
1. Capture loop thread (mss + pytesseract + privacy filter)
2. Sync loop thread (SQLite -> Supabase REST API)
3. Command poller thread (polls Supabase screen_commands for Telegram relay)
4. System tray on main thread (pause/resume/delete/status/quit)

Usage:
    python main.py
"""

import json
import logging
import sqlite3
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from capture.daemon import init_local_db, run_capture_loop
from capture.privacy import load_config
from sync.offline_queue import cleanup_old_captures
from sync.supabase_sync import run_sync_loop
from tray.tray_app import run_tray

# -- Logging setup --
BASE_DIR = Path.home() / ".openclaw-capture"
BASE_DIR.mkdir(parents=True, exist_ok=True)

LOG_PATH = BASE_DIR / "daemon.log"
DB_PATH = str(BASE_DIR / "captures.db")
CONFIG_PATH = str(Path(__file__).parent / "config" / "screen_capture.yaml")

# Configure structured JSON logging to both console and file
log_formatter = logging.Formatter("%(message)s")

file_handler = logging.FileHandler(str(LOG_PATH), encoding="utf-8")
file_handler.setFormatter(log_formatter)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)

root_logger = logging.getLogger("openclaw-capture")
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

logger = logging.getLogger("openclaw-capture.main")


def poll_commands(
    config: dict[str, Any],
    pause_event: threading.Event,
    shutdown_event: threading.Event,
    db_path: str,
) -> None:
    """
    Poll Supabase screen_commands table for Telegram relay commands.

    Fetches pending commands every command_poll_seconds, executes them,
    and marks them as executed.

    Supported commands:
    - pause: sets pause_event
    - resume: clears pause_event
    - delete_last_30m: deletes captures from last 30 minutes
    - delete_today: deletes all captures from today
    - status: no-op (status is queried directly from Supabase by Telegram handler)
    """
    import httpx

    supabase_url = config.get("supabase_url", "")
    service_key = config.get("supabase_service_role_key", "")
    interval = config.get("command_poll_seconds", 10)

    if not supabase_url or not service_key:
        logger.info("Supabase not configured, command poller disabled")
        return

    base_url = supabase_url.rstrip("/")
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    logger.info(
        json.dumps(
            {
                "level": "INFO",
                "component": "command-poller",
                "action": "poller_started",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "interval_seconds": interval,
            }
        )
    )

    while not shutdown_event.is_set():
        try:
            with httpx.Client(timeout=10.0) as client:
                # Fetch pending commands
                resp = client.get(
                    f"{base_url}/rest/v1/screen_commands",
                    params={
                        "status": "eq.pending",
                        "order": "created_at.asc",
                        "limit": "10",
                    },
                    headers={
                        "apikey": service_key,
                        "Authorization": f"Bearer {service_key}",
                    },
                )

                if resp.status_code != 200:
                    time.sleep(interval)
                    continue

                commands = resp.json()
                if not commands:
                    time.sleep(interval)
                    continue

                for cmd in commands:
                    cmd_id = cmd.get("id")
                    command = cmd.get("command", "").lower()
                    cmd_args = cmd.get("args", {})

                    logger.info(
                        json.dumps(
                            {
                                "level": "INFO",
                                "component": "command-poller",
                                "action": "executing_command",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "command": command,
                                "command_id": cmd_id,
                            }
                        )
                    )

                    # Execute command
                    if command == "pause":
                        pause_event.set()
                    elif command == "resume":
                        pause_event.clear()
                    elif command == "delete_last_30m":
                        conn = sqlite3.connect(db_path, check_same_thread=False)
                        cursor = conn.cursor()
                        cursor.execute(
                            "DELETE FROM captures WHERE captured_at >= datetime('now', '-30 minutes')"
                        )
                        conn.commit()
                        conn.close()
                    elif command == "delete_today":
                        conn = sqlite3.connect(db_path, check_same_thread=False)
                        cursor = conn.cursor()
                        cursor.execute(
                            "DELETE FROM captures WHERE captured_at >= date('now')"
                        )
                        conn.commit()
                        conn.close()
                    elif command == "status":
                        pass  # Status is read directly by Telegram handler
                    else:
                        logger.warning("Unknown command: %s", command)

                    # Mark command as executed
                    now_iso = datetime.now(timezone.utc).isoformat()
                    client.patch(
                        f"{base_url}/rest/v1/screen_commands",
                        params={"id": f"eq.{cmd_id}"},
                        json={
                            "status": "executed",
                            "executed_at": now_iso,
                        },
                        headers=headers,
                    )

        except Exception as e:
            logger.error(
                json.dumps(
                    {
                        "level": "ERROR",
                        "component": "command-poller",
                        "action": "poll_error",
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
                "component": "command-poller",
                "action": "poller_stopped",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    )


def main() -> None:
    """Main entry point -- starts all daemon threads and the system tray."""

    logger.info(
        json.dumps(
            {
                "level": "INFO",
                "component": "main",
                "action": "starting",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "db_path": DB_PATH,
                "config_path": CONFIG_PATH,
            }
        )
    )

    # 1. Load config
    config = load_config(CONFIG_PATH)

    # 2. Initialize local SQLite database
    conn = init_local_db(DB_PATH)
    conn.close()  # Threads will open their own connections

    # 3. Create shared events
    pause_event = threading.Event()  # Set = paused
    shutdown_event = threading.Event()  # Set = shutting down

    # 4. Start capture loop thread
    capture_thread = threading.Thread(
        target=run_capture_loop,
        args=(config, DB_PATH, pause_event, shutdown_event),
        name="capture-loop",
        daemon=True,
    )
    capture_thread.start()

    # 5. Start sync loop thread
    sync_thread = threading.Thread(
        target=run_sync_loop,
        args=(config, DB_PATH, shutdown_event),
        name="sync-loop",
        daemon=True,
    )
    sync_thread.start()

    # 6. Start command poller thread
    command_thread = threading.Thread(
        target=poll_commands,
        args=(config, pause_event, shutdown_event, DB_PATH),
        name="command-poller",
        daemon=True,
    )
    command_thread.start()

    # 7. Run system tray on main thread (blocking)
    try:
        run_tray(DB_PATH, pause_event, shutdown_event)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        # 8. Clean shutdown
        shutdown_event.set()
        logger.info("Waiting for threads to stop...")

        capture_thread.join(timeout=5.0)
        sync_thread.join(timeout=5.0)
        command_thread.join(timeout=5.0)

        # Run cleanup on exit
        retention_days = config.get("local_image_retention_days", 30)
        cleanup_old_captures(DB_PATH, retention_days)

        logger.info(
            json.dumps(
                {
                    "level": "INFO",
                    "component": "main",
                    "action": "stopped",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        )


if __name__ == "__main__":
    main()
