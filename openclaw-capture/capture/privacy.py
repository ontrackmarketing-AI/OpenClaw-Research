"""
Privacy-first filter for screen capture.

Checks active window against exclusion lists and scrubs sensitive text
from OCR output. All filtering happens BEFORE data enters the pipeline.
"""

import fnmatch
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("openclaw-capture.privacy")

# Module-level config cache
_config_cache: dict[str, Any] | None = None
_config_path_cached: str | None = None


def load_config(config_path: str) -> dict[str, Any]:
    """Load YAML config, cache it to avoid repeated disk reads."""
    global _config_cache, _config_path_cached

    if _config_cache is not None and _config_path_cached == config_path:
        return _config_cache

    path = Path(config_path)
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    _config_cache = config
    _config_path_cached = config_path
    return config


def should_skip(app_name: str, window_title: str, config: dict[str, Any]) -> bool:
    """
    Returns True if the capture should be skipped based on privacy rules.

    Checks (all case-insensitive):
    1. app_name matches excluded_apps or excluded_apps_personal
    2. window_title matches excluded_title_patterns (fnmatch glob)
    3. window_title contains any incognito_patterns substring
    """
    app_lower = app_name.lower()
    title_lower = window_title.lower()

    # Check excluded apps (password managers, etc.)
    excluded_apps = config.get("excluded_apps", [])
    for excluded in excluded_apps:
        if excluded.lower() == app_lower:
            logger.debug("Skipping excluded app: %s", app_name)
            return True

    # Check excluded personal apps
    excluded_personal = config.get("excluded_apps_personal", [])
    for excluded in excluded_personal:
        if excluded.lower() == app_lower:
            logger.debug("Skipping excluded personal app: %s", app_name)
            return True

    # Check excluded title patterns (fnmatch glob, case-insensitive)
    excluded_patterns = config.get("excluded_title_patterns", [])
    for pattern in excluded_patterns:
        if fnmatch.fnmatch(title_lower, pattern.lower()):
            logger.debug("Skipping excluded title pattern: %s", pattern)
            return True

    # Check incognito/private browsing patterns (substring match)
    incognito_patterns = config.get("incognito_patterns", [])
    for pattern in incognito_patterns:
        if pattern.lower() in title_lower:
            logger.debug("Skipping incognito pattern: %s", pattern)
            return True

    return False


def scrub_sensitive_text(
    ocr_text: str, config: dict[str, Any]
) -> tuple[str, bool]:
    """
    Scan OCR text for sensitive patterns and redact them.

    Returns:
        (cleaned_text, was_scrubbed) -- cleaned text with matches replaced
        by [REDACTED], and a boolean indicating if any scrubbing occurred.
    """
    was_scrubbed = False
    cleaned = ocr_text

    sensitive_patterns = config.get("sensitive_text_patterns", [])
    for pattern_str in sensitive_patterns:
        try:
            pattern = re.compile(pattern_str)
            if pattern.search(cleaned):
                cleaned = pattern.sub("[REDACTED]", cleaned)
                was_scrubbed = True
        except re.error as e:
            logger.error("Invalid regex pattern '%s': %s", pattern_str, e)

    if was_scrubbed:
        logger.warning(
            json.dumps(
                {
                    "level": "WARN",
                    "component": "privacy",
                    "action": "sensitive_text_scrubbed",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "message": "Sensitive content detected and redacted from OCR text",
                }
            )
        )

    return cleaned, was_scrubbed
