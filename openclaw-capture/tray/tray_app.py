"""
System tray application for OpenClaw screen capture daemon.

Provides a system tray icon with pause/resume, delete, status, and quit controls.
Uses pystray for cross-platform tray support.
"""

import json
import logging
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from PIL import Image, ImageDraw

logger = logging.getLogger("openclaw-capture.tray")


def create_icon_image(color: str = "green", size: int = 64) -> Image.Image:
    """
    Create a simple colored circle icon for the system tray.

    Args:
        color: "green" for running, "red" for paused.
        size: Icon size in pixels.

    Returns:
        PIL Image of a colored circle.
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    fill_color = (76, 175, 80, 255) if color == "green" else (244, 67, 54, 255)
    draw.ellipse([4, 4, size - 4, size - 4], fill=fill_color)

    return img


def get_status_text(db_path: str, pause_event: threading.Event) -> str:
    """
    Build a status string showing capture count today, unsynced count, and state.

    Args:
        db_path: Path to local SQLite database.
        pause_event: Threading event indicating pause state.

    Returns:
        Human-readable status string.
    """
    state = "Paused" if pause_event.is_set() else "Running"
    today_count = 0
    unsynced_count = 0

    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        cursor = conn.cursor()

        # Count captures today
        cursor.execute(
            """
            SELECT COUNT(*) FROM captures
            WHERE captured_at >= date('now')
            """
        )
        result = cursor.fetchone()
        today_count = result[0] if result else 0

        # Count unsynced
        cursor.execute("SELECT COUNT(*) FROM captures WHERE synced = 0")
        result = cursor.fetchone()
        unsynced_count = result[0] if result else 0

        conn.close()
    except Exception as e:
        logger.error("Failed to get status: %s", e)

    return (
        f"OpenClaw Capture\n"
        f"State: {state}\n"
        f"Captures today: {today_count}\n"
        f"Unsynced: {unsynced_count}"
    )


def delete_last_30m(db_path: str) -> int:
    """
    Delete captures from the last 30 minutes.

    Also deletes corresponding screenshot files.

    Returns:
        Number of captures deleted.
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    deleted = 0

    try:
        # Get image paths for deletion
        cursor.execute(
            """
            SELECT id, image_path FROM captures
            WHERE captured_at >= datetime('now', '-30 minutes')
            """
        )
        rows = cursor.fetchall()

        for row_id, image_path in rows:
            if image_path:
                path = Path(image_path)
                if path.exists():
                    try:
                        path.unlink()
                    except OSError:
                        pass

        # Delete from database
        cursor.execute(
            "DELETE FROM captures WHERE captured_at >= datetime('now', '-30 minutes')"
        )
        conn.commit()
        deleted = cursor.rowcount

    except Exception as e:
        logger.error("Failed to delete last 30m: %s", e)
    finally:
        conn.close()

    return deleted


def run_tray(
    db_path: str,
    pause_event: threading.Event,
    shutdown_event: threading.Event,
) -> None:
    """
    Run the system tray icon on the main thread.

    Menu items:
    - Pause Capture / Resume Capture (toggles pause_event)
    - Delete Last 30m
    - Status
    - Quit

    Args:
        db_path: Path to local SQLite database.
        pause_event: Threading event for pause/resume control.
        shutdown_event: Threading event for clean shutdown.
    """
    import pystray

    def on_pause(icon: Any, item: Any) -> None:
        pause_event.set()
        icon.icon = create_icon_image("red")
        icon.title = "OpenClaw Capture (Paused)"
        logger.info(
            json.dumps(
                {
                    "level": "INFO",
                    "component": "tray",
                    "action": "capture_paused",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        )

    def on_resume(icon: Any, item: Any) -> None:
        pause_event.clear()
        icon.icon = create_icon_image("green")
        icon.title = "OpenClaw Capture (Running)"
        logger.info(
            json.dumps(
                {
                    "level": "INFO",
                    "component": "tray",
                    "action": "capture_resumed",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        )

    def on_delete_30m(icon: Any, item: Any) -> None:
        deleted = delete_last_30m(db_path)
        logger.info("Deleted %d captures from last 30 minutes", deleted)

    def on_status(icon: Any, item: Any) -> None:
        status = get_status_text(db_path, pause_event)
        logger.info(status)
        # On Windows, pystray can show notifications
        try:
            icon.notify(status, "OpenClaw Capture")
        except Exception:
            pass  # Notification not available on all platforms

    def on_quit(icon: Any, item: Any) -> None:
        shutdown_event.set()
        icon.stop()
        logger.info(
            json.dumps(
                {
                    "level": "INFO",
                    "component": "tray",
                    "action": "quit_requested",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        )

    def is_paused(item: Any) -> bool:
        return pause_event.is_set()

    def is_running(item: Any) -> bool:
        return not pause_event.is_set()

    menu = pystray.Menu(
        pystray.MenuItem(
            "Pause Capture",
            on_pause,
            visible=is_running,
        ),
        pystray.MenuItem(
            "Resume Capture",
            on_resume,
            visible=is_paused,
        ),
        pystray.MenuItem("Delete Last 30m", on_delete_30m),
        pystray.MenuItem("Status", on_status),
        pystray.MenuItem("Quit", on_quit),
    )

    icon = pystray.Icon(
        "openclaw-capture",
        create_icon_image("green"),
        "OpenClaw Capture (Running)",
        menu,
    )

    logger.info(
        json.dumps(
            {
                "level": "INFO",
                "component": "tray",
                "action": "tray_started",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    )

    # This blocks on the main thread
    icon.run()
