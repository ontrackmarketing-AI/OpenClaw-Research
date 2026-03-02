"""
Main screen capture daemon.

Captures the active screen every N seconds, runs OCR, filters privacy-sensitive
content, deduplicates, and stores results in a local SQLite database.
Designed to run on Windows as a background service.
"""

import json
import logging
import sqlite3
import threading
import time
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

import mss
from PIL import Image

from capture.dedup import compute_hash, is_duplicate
from capture.privacy import scrub_sensitive_text, should_skip

logger = logging.getLogger("openclaw-capture.daemon")


def get_active_window() -> tuple[str, str]:
    """
    Get the currently active window's app name and title.

    Returns:
        (app_name, window_title) -- defaults to ("unknown", "unknown") on failure.
    """
    try:
        import pygetwindow as gw

        active = gw.getActiveWindow()
        if active is None:
            return ("unknown", "unknown")

        title = active.title or "unknown"

        # Extract app name from the window title or process
        # pygetwindow on Windows: title is the full window title
        # We use the last segment after " - " as a heuristic for app name
        parts = title.rsplit(" - ", 1)
        app_name = parts[-1].strip() if len(parts) > 1 else title.strip()

        return (app_name, title)
    except Exception as e:
        logger.debug("Failed to get active window: %s", e)
        return ("unknown", "unknown")


def capture_screen(max_width: int) -> Image.Image:
    """
    Capture the primary monitor screenshot.

    Uses mss for fast DMA-based capture, converts BGRA to RGB,
    and downscales if width exceeds max_width.

    Args:
        max_width: Maximum image width (e.g. 1920 for 4K downscale).

    Returns:
        PIL Image in RGB format.
    """
    with mss.mss() as sct:
        # Grab primary monitor (index 1; index 0 is "all monitors")
        monitor = sct.monitors[1]
        raw = sct.grab(monitor)

        # mss returns BGRA; convert to RGB via Pillow
        img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

    # Downscale if needed for OCR performance
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)

    return img


def ocr_image(image: Image.Image) -> str:
    """
    Run Tesseract OCR on a PIL Image.

    Args:
        image: PIL Image to OCR.

    Returns:
        Extracted text, stripped of leading/trailing whitespace.
    """
    import pytesseract

    text = pytesseract.image_to_string(image)
    return text.strip()


def init_local_db(db_path: str) -> sqlite3.Connection:
    """
    Initialize the local SQLite database for screen captures.

    Creates the captures table and indexes if they don't exist.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        SQLite connection.
    """
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS captures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            captured_at TEXT NOT NULL,
            app_name TEXT,
            window_title TEXT,
            ocr_text TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            image_path TEXT,
            synced INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_captures_synced ON captures(synced)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_captures_hash ON captures(content_hash)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_captures_time ON captures(captured_at DESC)"
    )

    conn.commit()
    return conn


def run_capture_loop(
    config: dict[str, Any],
    db_path: str,
    pause_event: threading.Event,
    shutdown_event: threading.Event,
) -> None:
    """
    Main capture loop. Runs continuously until shutdown_event is set.

    1. Check pause_event -- if set, sleep and continue
    2. Get active window
    3. Call should_skip() -- if True, sleep (NO screenshot taken)
    4. Capture screen
    5. Run OCR
    6. Skip if OCR text is empty or under 10 chars
    7. Scrub sensitive text; if entirely redacted, skip
    8. Compute content hash; check dedup -- if duplicate, skip
    9. Post-capture privacy check (race condition mitigation)
    10. Save screenshot to disk
    11. Insert into local SQLite
    12. Sleep for capture_interval_seconds
    """
    interval = config.get("capture_interval_seconds", 30)
    max_width = config.get("max_image_width", 1920)
    base_dir = Path.home() / ".openclaw-capture"
    screenshots_dir = base_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()

    logger.info(
        json.dumps(
            {
                "level": "INFO",
                "component": "daemon",
                "action": "capture_loop_started",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "interval_seconds": interval,
            }
        )
    )

    while not shutdown_event.is_set():
        try:
            # 1. Check pause state
            if pause_event.is_set():
                time.sleep(interval)
                continue

            # 2. Get active window
            app_name, window_title = get_active_window()

            # 3. Privacy check BEFORE capture (privacy-first pattern)
            if should_skip(app_name, window_title, config):
                time.sleep(interval)
                continue

            # 4. Capture screen
            image = capture_screen(max_width)

            # 5. Run OCR
            ocr_text = ocr_image(image)

            # 6. Skip if OCR text is empty or too short
            if not ocr_text or len(ocr_text) < 10:
                time.sleep(interval)
                continue

            # 7. Scrub sensitive text
            cleaned_text, was_scrubbed = scrub_sensitive_text(ocr_text, config)
            # If text is entirely redacted or too short after scrubbing, skip
            stripped_cleaned = cleaned_text.replace("[REDACTED]", "").strip()
            if not stripped_cleaned or len(stripped_cleaned) < 10:
                time.sleep(interval)
                continue

            # 8. Content hash deduplication
            content_hash = compute_hash(cleaned_text)
            if is_duplicate(content_hash, cursor):
                time.sleep(interval)
                continue

            # 9. Post-capture privacy check (race condition mitigation -- Pitfall 6)
            post_app, post_title = get_active_window()
            if post_app != app_name and should_skip(post_app, post_title, config):
                logger.debug(
                    "Post-capture privacy check triggered: app switched to %s",
                    post_app,
                )
                time.sleep(interval)
                continue

            # 10. Save screenshot to disk (date-organized)
            now = datetime.now(timezone.utc)
            date_dir = screenshots_dir / now.strftime("%Y-%m-%d")
            date_dir.mkdir(parents=True, exist_ok=True)
            image_filename = now.strftime("%H-%M-%S") + ".png"
            image_path = date_dir / image_filename
            image.save(str(image_path), "PNG")

            # 11. Insert into local SQLite
            captured_at = now.isoformat()
            cursor.execute(
                """
                INSERT INTO captures (captured_at, app_name, window_title,
                                      ocr_text, content_hash, image_path, synced)
                VALUES (?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    captured_at,
                    app_name,
                    window_title,
                    cleaned_text,
                    content_hash,
                    str(image_path),
                    ),
            )
            conn.commit()

            logger.info(
                json.dumps(
                    {
                        "level": "INFO",
                        "component": "daemon",
                        "action": "capture_stored",
                        "timestamp": captured_at,
                        "app_name": app_name,
                        "ocr_length": len(cleaned_text),
                        "was_scrubbed": was_scrubbed,
                    }
                )
            )

            # 12. Sleep
            time.sleep(interval)

        except Exception as e:
            # Never let the loop break -- log and continue
            logger.error(
                json.dumps(
                    {
                        "level": "ERROR",
                        "component": "daemon",
                        "action": "capture_loop_error",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "error": str(e),
                    }
                )
            )
            time.sleep(interval)

    conn.close()
    logger.info(
        json.dumps(
            {
                "level": "INFO",
                "component": "daemon",
                "action": "capture_loop_stopped",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    )
