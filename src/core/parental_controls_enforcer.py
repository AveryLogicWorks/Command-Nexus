# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""
Parental Controls Enforcer — Runtime Kid-Safety Layer
======================================================

This module enforces parental controls at the runtime level. It:
1. Loads parental control settings (with tamper detection)
2. Screens all AI input against topic restrictions
3. Blocks personal information sharing by children
4. Enforces session time limits
5. Logs conversations for parent review
6. Integrates with the expanded parental controls system

The enforcer is called BEFORE the governance sanitizer and BEFORE any
AI processing, ensuring that kid-safety filters are the first line of
defense when parental controls are enabled.

Password is stored as a SHA-256 hash (never plaintext).
Settings file has a tamper-detection checksum.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class ParentalBlockReason(Enum):
    MATURE_TOPIC = "mature_topic"
    VIOLENCE = "violence"
    EXPLICIT_LANGUAGE = "explicit_language"
    UNSAFE_WEB = "unsafe_web"
    PERSONAL_INFO = "personal_info"
    LOCATION_SHARING = "location_sharing"
    PHOTO_REQUEST = "photo_request"
    MEET_REQUEST = "meet_request"
    PLATFORM_REDIRECT = "platform_redirect"
    EXTERNAL_LINK = "external_link"
    SESSION_LIMIT = "session_limit"
    BEDTIME_MODE = "bedtime_mode"
    OUTSIDE_SCHEDULE = "outside_schedule"
    TAMPER_DETECTED = "tamper_detected"


@dataclass
class ParentalScreenResult:
    """Result of screening input through parental controls."""
    allowed: bool
    blocked_reason: ParentalBlockReason = ParentalBlockReason.MATURE_TOPIC
    block_message: str = ""
    should_log: bool = True
    alert_parent: bool = False
    matched_keywords: list[str] = field(default_factory=list)
    settings: dict = field(default_factory=dict)


# Default settings when parental controls file doesn't exist
DEFAULT_SETTINGS = {
    "enabled": False,
    "block_mature_topics": True,
    "block_violence": True,
    "block_explicit_language": True,
    "block_unsafe_web": True,
    "require_approval_for_outbound": True,
    "max_session_minutes": 120,
    "log_all_conversations": True,
    "password_hash": "",
    "age_preset": "",
    "active_restrictions": [],
    "interaction_safety": {
        "block_personal_info": True,
        "block_location_sharing": True,
        "block_photo_requests": True,
        "block_meet_requests": True,
        "block_platform_redirect": True,
        "block_external_links": False,
    },
}

# Topic restriction keywords — mapped from parental_controls_expanded.py
# These are the enforced keyword sets for each category
_TOPIC_KEYWORDS = {
    "mature": [
        "dating", "boyfriend", "girlfriend", "breakup", "romance", "crush",
        "sex", "contraception", "reproductive", "pregnancy", "std", "birth control",
        "drugs", "alcohol", "weed", "marijuana", "vaping", "smoking", "tobacco", "drinking",
        "gambling", "betting", "casino", "lottery", "poker", "slots", "sports betting",
    ],
    "violence": [
        "violence", "fighting", "blood", "gore", "crime", "attack", "assault",
        "horror", "nightmare", "psychological horror", "disturbing", "trauma",
        "gun", "weapon", "knife", "sword", "war", "military", "combat",
    ],
    "explicit_language": [
        "fuck", "shit", "bitch", "asshole", "dick", "pussy", "cunt",
        "bastard", "damn", "crap", "piss", "slut", "whore",
    ],
    "self_harm": [
        "self harm", "cutting", "suicide", "kill myself", "end it all",
        "worthless", "anorexia", "bulimia", "binge", "purge", "starving", "thinspo",
    ],
    "personal_info": [
        "my address", "my phone", "my name is", "i live at", "my school is",
        "my email", "my real name", "where i live", "my social security",
        "my credit card", "my bank account",
    ],
    "location_sharing": [
        "where are you", "send me your location", "what city",
        "gps coordinates", "what's your address",
    ],
    "photo_request": [
        "send me a photo", "show me your face", "video call",
        "take a picture", "send a selfie", "show me what you look like",
    ],
    "meet_request": [
        "let's meet", "meet up", "in person", "see you", "hang out together",
        "come to my house", "let's go somewhere",
    ],
    "platform_redirect": [
        "add me on", "message me on", "talk on snapchat", "follow me on",
        "dm me", "text me at", "call me at",
    ],
    "external_link": [
        "http", "www.", ".com", "click here", "visit this site",
        "go to this website",
    ],
}

# Compile regex patterns for efficiency
_COMPILED_PATTERNS: dict[str, list[re.Pattern]] = {}


def _get_compiled_patterns(category: str) -> list[re.Pattern]:
    """Get compiled regex patterns for a topic category."""
    if category not in _COMPILED_PATTERNS:
        keywords = _TOPIC_KEYWORDS.get(category, [])
        _COMPILED_PATTERNS[category] = [
            re.compile(re.escape(kw), re.IGNORECASE) for kw in keywords
        ]
    return _COMPILED_PATTERNS[category]


def _compute_checksum(settings: dict) -> str:
    """Compute a SHA-256 checksum of the settings (excluding the checksum field itself)."""
    clean = {k: v for k, v in settings.items() if k != "_checksum"}
    return hashlib.sha256(json.dumps(clean, sort_keys=True).encode("utf-8")).hexdigest()


def _hash_password(password: str) -> str:
    """Hash a parental controls password using SHA-256 with a salt."""
    salt = "CN_PARENTAL_2026_ALW"
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def verify_password(password: str, settings: dict) -> bool:
    """Verify a password against the stored hash."""
    stored_hash = settings.get("password_hash", "")
    if not stored_hash:
        # Legacy: check plaintext password (migrate on next save)
        legacy = settings.get("password", "")
        if legacy and password == legacy:
            return True
        # Default password
        return password == "Nexus"
    return _hash_password(password) == stored_hash


def _get_settings_path() -> Path:
    """Get the parental controls settings file path."""
    return Path.home() / ".command_nexus" / "parental_controls.json"


def load_parental_settings() -> dict:
    """Load parental controls settings with tamper detection.

    If the settings file has been tampered with (checksum mismatch),
    parental controls are forced ON with maximum restrictions.
    """
    path = _get_settings_path()
    if not path.exists():
        return dict(DEFAULT_SETTINGS)

    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        # Corrupted file — force maximum restrictions
        result = dict(DEFAULT_SETTINGS)
        result["enabled"] = True
        result["_tamper_detected"] = True
        return result

    # Tamper detection: verify checksum
    stored_checksum = settings.pop("_checksum", "")
    if stored_checksum:
        actual_checksum = _compute_checksum(settings)
        if stored_checksum != actual_checksum:
            # TAMPER DETECTED — force maximum restrictions
            settings["enabled"] = True
            settings["block_mature_topics"] = True
            settings["block_violence"] = True
            settings["block_explicit_language"] = True
            settings["block_unsafe_web"] = True
            settings["require_approval_for_outbound"] = True
            settings["log_all_conversations"] = True
            settings["_tamper_detected"] = True
            return settings

    # Merge with defaults for any missing keys
    merged = dict(DEFAULT_SETTINGS)
    merged.update(settings)
    return merged


def save_parental_settings(settings: dict) -> None:
    """Save parental controls settings with checksum and hashed password."""
    path = _get_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    # Hash password if it's still plaintext
    if "password" in settings and settings["password"]:
        if not settings.get("password_hash"):
            settings["password_hash"] = _hash_password(settings.pop("password"))
        else:
            settings.pop("password", None)

    # Compute and attach checksum
    settings["_checksum"] = _compute_checksum(settings)

    path.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def screen_input(text: str, settings: Optional[dict] = None) -> ParentalScreenResult:
    """Screen user input through parental controls.

    Returns ParentalScreenResult with allowed=False if the input
    violates any active parental control restriction.

    This should be called BEFORE governance sanitizer when parental
    controls are enabled.
    """
    if settings is None:
        settings = load_parental_settings()

    # If parental controls are not enabled, allow everything
    if not settings.get("enabled", False):
        return ParentalScreenResult(allowed=True, settings=settings)

    # Check for tamper detection
    if settings.get("_tamper_detected"):
        return ParentalScreenResult(
            allowed=False,
            blocked_reason=ParentalBlockReason.TAMPER_DETECTED,
            block_message=(
                "Parental Controls detected tampering with settings. "
                "Maximum restrictions are now active. Contact your parent to reset."
            ),
            alert_parent=True,
            settings=settings,
        )

    if not text or not text.strip():
        return ParentalScreenResult(allowed=True, settings=settings)

    text_lower = text.lower()
    matched: list[str] = []
    interaction_safety = settings.get("interaction_safety", {})

    # Check mature topics
    if settings.get("block_mature_topics", True):
        for pattern in _get_compiled_patterns("mature"):
            m = pattern.search(text)
            if m:
                matched.append(m.group())
                return ParentalScreenResult(
                    allowed=False,
                    blocked_reason=ParentalBlockReason.MATURE_TOPIC,
                    block_message=(
                        "This topic is blocked by Parental Controls. "
                        "Ask your parent if you have questions about this."
                    ),
                    alert_parent=True,
                    matched_keywords=matched,
                    settings=settings,
                )

    # Check violence
    if settings.get("block_violence", True):
        for pattern in _get_compiled_patterns("violence"):
            m = pattern.search(text)
            if m:
                matched.append(m.group())
                return ParentalScreenResult(
                    allowed=False,
                    blocked_reason=ParentalBlockReason.VIOLENCE,
                    block_message=(
                        "Violence-related topics are blocked by Parental Controls. "
                        "Ask your parent if you have questions about this."
                    ),
                    alert_parent=True,
                    matched_keywords=matched,
                    settings=settings,
                )

    # Check explicit language
    if settings.get("block_explicit_language", True):
        for pattern in _get_compiled_patterns("explicit_language"):
            m = pattern.search(text)
            if m:
                matched.append(m.group())
                return ParentalScreenResult(
                    allowed=False,
                    blocked_reason=ParentalBlockReason.EXPLICIT_LANGUAGE,
                    block_message=(
                        "Inappropriate language is blocked by Parental Controls. "
                        "Please use respectful language."
                    ),
                    alert_parent=True,
                    matched_keywords=matched,
                    settings=settings,
                )

    # Check self-harm (always blocked when parental controls are on)
    for pattern in _get_compiled_patterns("self_harm"):
        m = pattern.search(text)
        if m:
            matched.append(m.group())
            return ParentalScreenResult(
                allowed=False,
                blocked_reason=ParentalBlockReason.MATURE_TOPIC,
                block_message=(
                    "This topic requires adult attention. "
                    "Please talk to your parent or a trusted adult right away. "
                    "If you need help, call or text 988 (Suicide & Crisis Lifeline)."
                ),
                alert_parent=True,
                matched_keywords=matched,
                settings=settings,
            )

    # Check interaction safety — personal info sharing
    if interaction_safety.get("block_personal_info", True):
        for pattern in _get_compiled_patterns("personal_info"):
            m = pattern.search(text)
            if m:
                matched.append(m.group())
                return ParentalScreenResult(
                    allowed=False,
                    blocked_reason=ParentalBlockReason.PERSONAL_INFO,
                    block_message=(
                        "Sharing personal information is blocked by Parental Controls. "
                        "Never share your address, phone number, or school name online."
                    ),
                    alert_parent=True,
                    matched_keywords=matched,
                    settings=settings,
                )

    # Check location sharing
    if interaction_safety.get("block_location_sharing", True):
        for pattern in _get_compiled_patterns("location_sharing"):
            m = pattern.search(text)
            if m:
                matched.append(m.group())
                return ParentalScreenResult(
                    allowed=False,
                    blocked_reason=ParentalBlockReason.LOCATION_SHARING,
                    block_message="Location sharing is blocked by Parental Controls.",
                    alert_parent=True,
                    matched_keywords=matched,
                    settings=settings,
                )

    # Check photo requests
    if interaction_safety.get("block_photo_requests", True):
        for pattern in _get_compiled_patterns("photo_request"):
            m = pattern.search(text)
            if m:
                matched.append(m.group())
                return ParentalScreenResult(
                    allowed=False,
                    blocked_reason=ParentalBlockReason.PHOTO_REQUEST,
                    block_message="Photo and video requests are blocked by Parental Controls.",
                    alert_parent=True,
                    matched_keywords=matched,
                    settings=settings,
                )

    # Check meet requests
    if interaction_safety.get("block_meet_requests", True):
        for pattern in _get_compiled_patterns("meet_request"):
            m = pattern.search(text)
            if m:
                matched.append(m.group())
                return ParentalScreenResult(
                    allowed=False,
                    blocked_reason=ParentalBlockReason.MEET_REQUEST,
                    block_message="Meeting in person is blocked by Parental Controls. Never meet strangers.",
                    alert_parent=True,
                    matched_keywords=matched,
                    settings=settings,
                )

    # Check platform redirects
    if interaction_safety.get("block_platform_redirect", True):
        for pattern in _get_compiled_patterns("platform_redirect"):
            m = pattern.search(text)
            if m:
                matched.append(m.group())
                return ParentalScreenResult(
                    allowed=False,
                    blocked_reason=ParentalBlockReason.PLATFORM_REDIRECT,
                    block_message="Moving to other apps or platforms is blocked by Parental Controls.",
                    alert_parent=True,
                    matched_keywords=matched,
                    settings=settings,
                )

    # Check external links
    if interaction_safety.get("block_external_links", False):
        for pattern in _get_compiled_patterns("external_link"):
            m = pattern.search(text)
            if m:
                matched.append(m.group())
                return ParentalScreenResult(
                    allowed=False,
                    blocked_reason=ParentalBlockReason.EXTERNAL_LINK,
                    block_message="External links are blocked by Parental Controls.",
                    alert_parent=False,
                    matched_keywords=matched,
                    settings=settings,
                )

    # All checks passed
    return ParentalScreenResult(allowed=True, settings=settings)


def check_session_time(settings: dict, session_start_time: float) -> ParentalScreenResult:
    """Check if the current session has exceeded the time limit.

    Args:
        settings: Parental controls settings dict
        session_start_time: Unix timestamp when the session started

    Returns ParentalScreenResult with allowed=False if time limit exceeded.
    """
    if not settings.get("enabled", False):
        return ParentalScreenResult(allowed=True, settings=settings)

    max_minutes = settings.get("max_session_minutes", 120)
    if max_minutes <= 0:
        return ParentalScreenResult(allowed=True, settings=settings)

    elapsed_minutes = (time.time() - session_start_time) / 60.0
    if elapsed_minutes >= max_minutes:
        return ParentalScreenResult(
            allowed=False,
            blocked_reason=ParentalBlockReason.SESSION_LIMIT,
            block_message=(
                f"Session time limit reached ({max_minutes} minutes). "
                "Take a break and come back later!"
            ),
            alert_parent=False,
            settings=settings,
        )

    return ParentalScreenResult(allowed=True, settings=settings)


def log_conversation(text: str, ai_name: str, settings: dict) -> None:
    """Log a conversation entry for parent review if logging is enabled."""
    if not settings.get("log_all_conversations", True):
        return
    if not settings.get("enabled", False):
        return

    try:
        log_dir = Path.home() / ".command_nexus" / "parental_logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"conversation_{time.strftime('%Y-%m-%d')}.jsonl"

        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "ai_name": ai_name,
            "text": text[:500],  # Truncate for log file size
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def alert_parent(message: str, settings: dict) -> None:
    """Write a parent alert to the alerts file."""
    try:
        alert_dir = Path.home() / ".command_nexus" / "parental_alerts"
        alert_dir.mkdir(parents=True, exist_ok=True)
        alert_file = alert_dir / f"alert_{int(time.time())}.json"
        alert_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "message": message,
            "settings_checksum": settings.get("_checksum", ""),
        }
        alert_file.write_text(json.dumps(alert_data, indent=2), encoding="utf-8")
    except Exception:
        pass
