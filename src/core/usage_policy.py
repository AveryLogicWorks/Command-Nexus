# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""
Usage Policy Engine — Unified Access & Behavior Control
========================================================

This module provides a unified policy engine that supports multiple
deployment contexts:

1. PARENTAL — Kid safety (families): topic filtering, interaction safety,
   session limits, conversation logging, age-based presets.

2. ENTERPRISE — Business/employee restrictions: capability lockdown,
   backend restrictions, work-only mode, compliance logging, data
   exfiltration prevention, file path restrictions, approval requirements.

3. CUSTOM — Mix and match rules from both modes.

4. DISABLED — No restrictions (default).

The policy engine is called BEFORE the governance sanitizer and BEFORE
any AI processing. It is the first gate in the access pipeline.

Password is stored as SHA-256 hash. Settings file has tamper detection.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, time as dtime
from enum import Enum
from pathlib import Path
from typing import Optional


# ── Policy Modes ──

class PolicyMode(Enum):
    DISABLED = "disabled"
    PARENTAL = "parental"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class PolicyBlockReason(Enum):
    # Parental reasons
    MATURE_TOPIC = "mature_topic"
    VIOLENCE = "violence"
    EXPLICIT_LANGUAGE = "explicit_language"
    PERSONAL_INFO = "personal_info"
    LOCATION_SHARING = "location_sharing"
    PHOTO_REQUEST = "photo_request"
    MEET_REQUEST = "meet_request"
    PLATFORM_REDIRECT = "platform_redirect"
    EXTERNAL_LINK = "external_link"
    SELF_HARM = "self_harm"
    SESSION_LIMIT = "session_limit"
    BEDTIME_MODE = "bedtime_mode"
    OUTSIDE_SCHEDULE = "outside_schedule"
    # Enterprise reasons
    NON_WORK_TOPIC = "non_work_topic"
    CAPABILITY_RESTRICTED = "capability_restricted"
    BACKEND_RESTRICTED = "backend_restricted"
    FILE_PATH_RESTRICTED = "file_path_restricted"
    DATA_EXFILTRATION = "data_exfiltration"
    UNAPPROVED_OUTBOUND = "unapproved_outbound"
    ENTERTAINMENT_BLOCKED = "entertainment_blocked"
    SOCIAL_MEDIA_BLOCKED = "social_media_blocked"
    CUSTOM_KEYWORD = "custom_keyword"
    MODEL_RESTRICTED = "model_restricted"
    IP_RESTRICTED = "ip_restricted"
    WEEKEND_BLOCKED = "weekend_blocked"
    QUOTA_EXCEEDED = "quota_exceeded"
    CONTENT_RATING = "content_rating"
    CYBERBULLYING = "cyberbullying"
    WEBSITE_BLOCKED = "website_blocked"
    UNAUTHORIZED_USER = "unauthorized_user"
    # Shared
    TAMPER_DETECTED = "tamper_detected"


@dataclass
class PolicyScreenResult:
    """Result of screening input through the usage policy engine."""
    allowed: bool
    blocked_reason: PolicyBlockReason = PolicyBlockReason.MATURE_TOPIC
    block_message: str = ""
    should_log: bool = True
    alert_admin: bool = False
    matched_keywords: list[str] = field(default_factory=list)
    policy_mode: PolicyMode = PolicyMode.DISABLED
    settings: dict = field(default_factory=dict)


# ── Default Settings ──

DEFAULT_PARENTAL_SETTINGS = {
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
    "bedtime": "",  # "21:00" format
    "scheduled_access_start": "",  # "15:00"
    "scheduled_access_end": "",  # "19:00"
    "break_reminder_minutes": 0,  # 0 = disabled
    "daily_time_limit_minutes": 0,  # 0 = no limit
    "interaction_safety": {
        "block_personal_info": True,
        "block_location_sharing": True,
        "block_photo_requests": True,
        "block_meet_requests": True,
        "block_platform_redirect": True,
        "block_external_links": False,
    },
    # ── New: Expanded Parental Controls ──
    "block_cyberbullying": True,
    "content_rating_limit": "",  # "G", "PG", "PG-13", "R", "" = no limit
    "blocked_websites": [],  # ["facebook.com", "tiktok.com", ...]
    "allowed_websites": [],  # empty = all allowed; populated = whitelist
    "custom_blocked_keywords": [],  # parent adds their own ["fortnite", "roblox", ...]
    "custom_allowed_topics": [],  # whitelist specific topics even if category blocked
    "child_profiles": [],  # [{"name": "Alice", "age": 8, "preset": "child"}, ...]
    "active_child_profile": "",  # name of currently active profile
    "usage_report_frequency": "daily",  # "daily", "weekly", "none"
    "block_online_gaming": False,
    "block_streaming": False,
    "block_shopping": False,
    "block_financial": False,
}

DEFAULT_ENTERPRISE_SETTINGS = {
    "enabled": False,
    "company_name": "",
    "work_only_mode": True,
    "block_entertainment": True,
    "block_social_media": True,
    "block_personal_use": True,
    "require_approval_for_outbound": True,
    "require_approval_for_file_write": True,
    "require_approval_for_shell": True,
    "log_all_conversations": True,
    "compliance_logging": True,
    "block_data_exfiltration": True,
    "local_backend_only": True,
    "password_hash": "",
    "allowed_capabilities": [],  # empty = all allowed; populated = whitelist
    "blocked_capabilities": [],  # populated = blacklist
    "allowed_file_paths": [],  # empty = all allowed; populated = whitelist
    "blocked_file_paths": [],  # populated = blacklist
    "max_session_minutes": 0,  # 0 = no limit
    "scheduled_access_start": "",
    "scheduled_access_end": "",
    # ── New: Enterprise Multi-User & Advanced Controls ──
    "seat_count": 1,  # number of licensed seats
    "licensed_to": "",  # company or person who holds the license
    "license_key": "",  # enterprise license key
    "users": [],  # [{"username": "john", "role": "employee", "quota_messages": 100, ...}]
    "default_role": "employee",  # default role for unrecognized users
    "roles": {
        "admin": {
            "can_change_policy": True,
            "can_view_logs": True,
            "can_export_data": True,
            "quota_messages_per_day": 0,  # 0 = unlimited
            "quota_tokens_per_day": 0,
            "allowed_models": [],  # empty = all allowed
        },
        "manager": {
            "can_change_policy": False,
            "can_view_logs": True,
            "can_export_data": True,
            "quota_messages_per_day": 500,
            "quota_tokens_per_day": 0,
            "allowed_models": [],
        },
        "employee": {
            "can_change_policy": False,
            "can_view_logs": False,
            "can_export_data": False,
            "quota_messages_per_day": 100,
            "quota_tokens_per_day": 50000,
            "allowed_models": [],
        },
        "contractor": {
            "can_change_policy": False,
            "can_view_logs": False,
            "can_export_data": False,
            "quota_messages_per_day": 50,
            "quota_tokens_per_day": 20000,
            "allowed_models": [],
        },
    },
    "allowed_models": [],  # empty = all allowed; populated = whitelist ["qwen2.5-coder-7b", ...]
    "blocked_models": [],  # populated = blacklist
    "allowed_ip_addresses": [],  # empty = all allowed; populated = whitelist
    "block_weekends": False,  # block access on Sat/Sun
    "allowed_days": [],  # ["mon", "tue", "wed", "thu", "fri"], empty = all days
    "data_retention_days": 90,  # auto-delete logs after N days, 0 = never
    "watermark_outputs": True,  # stamp user ID on all AI outputs
    "block_copy_paste": False,  # prevent copying AI output to clipboard
    "block_screenshots": False,  # warn about screenshots
    "custom_blocked_keywords": [],  # company-specific blocked terms
    "custom_allowed_topics": [],  # company-specific whitelist
    "block_online_shopping": True,
    "block_financial_trading": True,
    "block_job_search": False,  # don't block employees from looking for jobs (HR setting)
    "block_streaming": True,
    "block_online_gaming": True,
    "audit_export_enabled": True,  # allow admin to export audit logs
}

DEFAULT_SETTINGS = {
    "mode": PolicyMode.DISABLED.value,
    "password_hash": "",
    "parental": dict(DEFAULT_PARENTAL_SETTINGS),
    "enterprise": dict(DEFAULT_ENTERPRISE_SETTINGS),
}


# ── Topic Keywords ──

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
    # Enterprise topics
    "entertainment": [
        "netflix", "movie", "tv show", "game", "gaming", "fun", "joke",
        "entertainment", "music", "spotify", "youtube", "tiktok",
        "meme", "funny video", "celebrity", "gossip", "drama",
    ],
    "social_media": [
        "facebook", "twitter", "instagram", "tiktok", "snapchat",
        "linkedin", "reddit", "discord", "telegram", "whatsapp",
        "social media", "post", "tweet", "feed", "timeline",
    ],
    "personal_use": [
        "plan my vacation", "personal shopping", "my dating profile",
        "my personal blog", "my hobby", "plan my party",
    ],
    "data_exfiltration": [
        "email this to", "send this to my personal", "forward to external",
        "upload to", "post this online", "share externally",
        "send to my private email", "copy to usb", "download all data",
    ],
    # ── New: Cyberbullying detection (parental) ──
    "cyberbullying": [
        "you're ugly", "you're stupid", "nobody likes you", "kill yourself",
        "everyone hates you", "you're worthless", "go die", "you're a loser",
        "shut up no one cares", "you have no friends", "freak", "weirdo",
        "make fun of", "bully", "harass", "intimidate", "threaten",
        "spread rumors", "exclude", "make them cry",
    ],
    # ── New: Online gaming (parental + enterprise) ──
    "online_gaming": [
        "fortnite", "roblox", "minecraft server", "among us", "call of duty",
        "valorant", "league of legends", "steam", "epic games", "xbox live",
        "playstation network", "nintendo online", "twitch", "esports",
    ],
    # ── New: Streaming (parental + enterprise) ──
    "streaming": [
        "netflix", "hulu", "disney plus", "amazon prime video", "hbo max",
        "youtube tv", "sling tv", "paramount plus", "peacock", "crunchyroll",
        "stream movie", "stream show", "watch online",
    ],
    # ── New: Online shopping (parental + enterprise) ──
    "online_shopping": [
        "amazon", "ebay", "etsy", "wish", "aliexpress", "temu",
        "add to cart", "checkout", "buy now", "online shopping",
        "credit card purchase", "order online",
    ],
    # ── New: Financial trading (enterprise) ──
    "financial_trading": [
        "stock market", "crypto trading", "bitcoin", "ethereum", "dogecoin",
        "coinbase", "robinhood", "etrade", "td ameritrade", "binance",
        "buy stocks", "sell stocks", "trade options", "day trading",
        "forex", "investment portfolio",
    ],
    # ── New: Job search (enterprise HR setting) ──
    "job_search": [
        "job listing", "job search", "indeed", "glassdoor", "linkedin jobs",
        "apply for job", "resume", "cover letter", "interview prep",
        "career change", "new employer", "leaving the company",
    ],
}

_COMPILED_PATTERNS: dict[str, list[re.Pattern]] = {}


def _get_patterns(category: str) -> list[re.Pattern]:
    if category not in _COMPILED_PATTERNS:
        keywords = _TOPIC_KEYWORDS.get(category, [])
        _COMPILED_PATTERNS[category] = [
            re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE) for kw in keywords
        ]
    return _COMPILED_PATTERNS[category]


# ── Age Presets ──

AGE_PRESETS = {
    "child": {
        "name": "Child (5-8 years)",
        "description": "Maximum protection for young children",
        "settings": {
            "block_mature_topics": True,
            "block_violence": True,
            "block_explicit_language": True,
            "block_unsafe_web": True,
            "require_approval_for_outbound": True,
            "max_session_minutes": 30,
            "log_all_conversations": True,
            "bedtime": "20:00",
            "break_reminder_minutes": 15,
            "daily_time_limit_minutes": 60,
            "interaction_safety": {
                "block_personal_info": True,
                "block_location_sharing": True,
                "block_photo_requests": True,
                "block_meet_requests": True,
                "block_platform_redirect": True,
                "block_external_links": True,
            },
        },
    },
    "preteen": {
        "name": "Pre-Teen (9-12 years)",
        "description": "Moderate protection with some educational exceptions",
        "settings": {
            "block_mature_topics": True,
            "block_violence": True,
            "block_explicit_language": True,
            "block_unsafe_web": True,
            "require_approval_for_outbound": True,
            "max_session_minutes": 60,
            "log_all_conversations": True,
            "bedtime": "21:00",
            "break_reminder_minutes": 20,
            "daily_time_limit_minutes": 120,
            "interaction_safety": {
                "block_personal_info": True,
                "block_location_sharing": True,
                "block_photo_requests": True,
                "block_meet_requests": True,
                "block_platform_redirect": True,
                "block_external_links": False,
            },
        },
    },
    "teen": {
        "name": "Teen (13-17 years)",
        "description": "Light protection with safety monitoring",
        "settings": {
            "block_mature_topics": False,
            "block_violence": False,
            "block_explicit_language": True,
            "block_unsafe_web": True,
            "require_approval_for_outbound": True,
            "max_session_minutes": 120,
            "log_all_conversations": True,
            "bedtime": "22:00",
            "break_reminder_minutes": 30,
            "daily_time_limit_minutes": 180,
            "interaction_safety": {
                "block_personal_info": True,
                "block_location_sharing": True,
                "block_photo_requests": True,
                "block_meet_requests": True,
                "block_platform_redirect": True,
                "block_external_links": False,
            },
        },
    },
    "focus_mode": {
        "name": "Study Focus Mode",
        "description": "Block distractions for homework time",
        "settings": {
            "block_mature_topics": True,
            "block_violence": True,
            "block_explicit_language": True,
            "block_unsafe_web": True,
            "require_approval_for_outbound": True,
            "max_session_minutes": 45,
            "log_all_conversations": False,
            "break_reminder_minutes": 20,
            "daily_time_limit_minutes": 0,
            "interaction_safety": {
                "block_personal_info": True,
                "block_location_sharing": True,
                "block_photo_requests": True,
                "block_meet_requests": True,
                "block_platform_redirect": True,
                "block_external_links": True,
            },
        },
    },
}


# ── Enterprise Presets ──

ENTERPRISE_PRESETS = {
    "strict": {
        "name": "Strict Enterprise",
        "description": "Maximum lockdown — work only, local backend, full compliance logging",
        "settings": {
            "work_only_mode": True,
            "block_entertainment": True,
            "block_social_media": True,
            "block_personal_use": True,
            "require_approval_for_outbound": True,
            "require_approval_for_file_write": True,
            "require_approval_for_shell": True,
            "log_all_conversations": True,
            "compliance_logging": True,
            "block_data_exfiltration": True,
            "local_backend_only": True,
            "max_session_minutes": 480,
        },
    },
    "standard": {
        "name": "Standard Enterprise",
        "description": "Work-focused with compliance logging, allows some flexibility",
        "settings": {
            "work_only_mode": True,
            "block_entertainment": True,
            "block_social_media": True,
            "block_personal_use": False,
            "require_approval_for_outbound": True,
            "require_approval_for_file_write": False,
            "require_approval_for_shell": True,
            "log_all_conversations": True,
            "compliance_logging": True,
            "block_data_exfiltration": True,
            "local_backend_only": False,
            "max_session_minutes": 0,
        },
    },
    "light": {
        "name": "Light Enterprise",
        "description": "Compliance logging only, minimal restrictions",
        "settings": {
            "work_only_mode": False,
            "block_entertainment": False,
            "block_social_media": False,
            "block_personal_use": False,
            "require_approval_for_outbound": False,
            "require_approval_for_file_write": False,
            "require_approval_for_shell": False,
            "log_all_conversations": True,
            "compliance_logging": True,
            "block_data_exfiltration": True,
            "local_backend_only": False,
            "max_session_minutes": 0,
        },
    },
}


# ── Password & Checksum ──

def _hash_password(password: str) -> str:
    salt = "CN_USAGE_POLICY_2026_ALW"
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def verify_password(password: str, settings: dict) -> bool:
    stored_hash = settings.get("password_hash", "")
    if not stored_hash:
        legacy = settings.get("password", "")
        if legacy and password == legacy:
            return True
        return password == "Nexus"
    return _hash_password(password) == stored_hash


def _compute_checksum(settings: dict) -> str:
    clean = {k: v for k, v in settings.items() if k != "_checksum"}
    return hashlib.sha256(json.dumps(clean, sort_keys=True).encode("utf-8")).hexdigest()


# ── Settings Persistence ──

def _get_settings_path() -> Path:
    return Path.home() / ".command_nexus" / "usage_policy.json"


def load_policy_settings() -> dict:
    """Load usage policy settings with tamper detection."""
    path = _get_settings_path()
    if not path.exists():
        return dict(DEFAULT_SETTINGS)

    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        result = dict(DEFAULT_SETTINGS)
        result["mode"] = PolicyMode.ENTERPRISE.value
        result["_tamper_detected"] = True
        return result

    stored_checksum = settings.pop("_checksum", "")
    if stored_checksum:
        actual = _compute_checksum(settings)
        if stored_checksum != actual:
            settings["mode"] = PolicyMode.ENTERPRISE.value
            settings["_tamper_detected"] = True
            if "enterprise" in settings:
                settings["enterprise"]["enabled"] = True
                settings["enterprise"]["work_only_mode"] = True
                settings["enterprise"]["compliance_logging"] = True
            return settings

    merged = dict(DEFAULT_SETTINGS)
    merged.update(settings)
    return merged


def save_policy_settings(settings: dict) -> None:
    path = _get_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    if "password" in settings and settings["password"]:
        if not settings.get("password_hash"):
            settings["password_hash"] = _hash_password(settings.pop("password"))
        else:
            settings.pop("password", None)

    settings["_checksum"] = _compute_checksum(settings)
    path.write_text(json.dumps(settings, indent=2), encoding="utf-8")


# ── Screening Functions ──

def screen_input(text: str, settings: Optional[dict] = None) -> PolicyScreenResult:
    """Screen user input through the active usage policy.

    This is the main entry point. It checks the policy mode and routes
    to the appropriate screening logic.
    """
    if settings is None:
        settings = load_policy_settings()

    mode_str = settings.get("mode", PolicyMode.DISABLED.value)
    try:
        mode = PolicyMode(mode_str)
    except ValueError:
        mode = PolicyMode.DISABLED

    if mode == PolicyMode.DISABLED:
        return PolicyScreenResult(allowed=True, policy_mode=mode, settings=settings)

    if settings.get("_tamper_detected"):
        return PolicyScreenResult(
            allowed=False,
            blocked_reason=PolicyBlockReason.TAMPER_DETECTED,
            block_message=(
                "Usage Policy detected tampering with settings. "
                "Maximum restrictions are now active. Contact your administrator or parent to reset."
            ),
            alert_admin=True,
            policy_mode=mode,
            settings=settings,
        )

    if not text or not text.strip():
        return PolicyScreenResult(allowed=True, policy_mode=mode, settings=settings)

    # Route to appropriate screener
    if mode == PolicyMode.PARENTAL:
        return _screen_parental(text, settings, mode)
    elif mode == PolicyMode.ENTERPRISE:
        return _screen_enterprise(text, settings, mode)
    elif mode == PolicyMode.CUSTOM:
        # Run both parental and enterprise checks
        parental_result = _screen_parental(text, settings, mode)
        if not parental_result.allowed:
            return parental_result
        enterprise_result = _screen_enterprise(text, settings, mode)
        if not enterprise_result.allowed:
            return enterprise_result
        return PolicyScreenResult(allowed=True, policy_mode=mode, settings=settings)

    return PolicyScreenResult(allowed=True, policy_mode=mode, settings=settings)


def _screen_parental(text: str, settings: dict, mode: PolicyMode) -> PolicyScreenResult:
    """Screen input through parental controls."""
    parental = settings.get("parental", {})
    if not parental.get("enabled", False):
        return PolicyScreenResult(allowed=True, policy_mode=mode, settings=settings)

    matched: list[str] = []
    interaction_safety = parental.get("interaction_safety", {})

    # Check mature topics
    if parental.get("block_mature_topics", True):
        for pattern in _get_patterns("mature"):
            m = pattern.search(text)
            if m:
                matched.append(m.group())
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.MATURE_TOPIC,
                    block_message="This topic is blocked by Parental Controls. Ask your parent if you have questions.",
                    alert_admin=True,
                    matched_keywords=matched,
                    policy_mode=mode,
                    settings=settings,
                )

    # Check violence
    if parental.get("block_violence", True):
        for pattern in _get_patterns("violence"):
            m = pattern.search(text)
            if m:
                matched.append(m.group())
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.VIOLENCE,
                    block_message="Violence-related topics are blocked by Parental Controls.",
                    alert_admin=True,
                    matched_keywords=matched,
                    policy_mode=mode,
                    settings=settings,
                )

    # Check explicit language
    if parental.get("block_explicit_language", True):
        for pattern in _get_patterns("explicit_language"):
            m = pattern.search(text)
            if m:
                matched.append(m.group())
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.EXPLICIT_LANGUAGE,
                    block_message="Inappropriate language is blocked by Parental Controls. Please use respectful language.",
                    alert_admin=True,
                    matched_keywords=matched,
                    policy_mode=mode,
                    settings=settings,
                )

    # Check self-harm (always blocked when parental controls on)
    for pattern in _get_patterns("self_harm"):
        m = pattern.search(text)
        if m:
            matched.append(m.group())
            return PolicyScreenResult(
                allowed=False,
                blocked_reason=PolicyBlockReason.SELF_HARM,
                block_message=(
                    "This topic requires adult attention. Please talk to your parent or a trusted adult right away. "
                    "If you need help, call or text 988 (Suicide & Crisis Lifeline)."
                ),
                alert_admin=True,
                matched_keywords=matched,
                policy_mode=mode,
                settings=settings,
            )

    # Interaction safety checks
    if interaction_safety.get("block_personal_info", True):
        for pattern in _get_patterns("personal_info"):
            m = pattern.search(text)
            if m:
                matched.append(m.group())
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.PERSONAL_INFO,
                    block_message="Sharing personal information is blocked by Parental Controls. Never share your address, phone, or school online.",
                    alert_admin=True,
                    matched_keywords=matched,
                    policy_mode=mode,
                    settings=settings,
                )

    if interaction_safety.get("block_location_sharing", True):
        for pattern in _get_patterns("location_sharing"):
            m = pattern.search(text)
            if m:
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.LOCATION_SHARING,
                    block_message="Location sharing is blocked by Parental Controls.",
                    alert_admin=True,
                    matched_keywords=[m.group()],
                    policy_mode=mode,
                    settings=settings,
                )

    if interaction_safety.get("block_photo_requests", True):
        for pattern in _get_patterns("photo_request"):
            m = pattern.search(text)
            if m:
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.PHOTO_REQUEST,
                    block_message="Photo and video requests are blocked by Parental Controls.",
                    alert_admin=True,
                    matched_keywords=[m.group()],
                    policy_mode=mode,
                    settings=settings,
                )

    if interaction_safety.get("block_meet_requests", True):
        for pattern in _get_patterns("meet_request"):
            m = pattern.search(text)
            if m:
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.MEET_REQUEST,
                    block_message="Meeting in person is blocked by Parental Controls. Never meet strangers.",
                    alert_admin=True,
                    matched_keywords=[m.group()],
                    policy_mode=mode,
                    settings=settings,
                )

    if interaction_safety.get("block_platform_redirect", True):
        for pattern in _get_patterns("platform_redirect"):
            m = pattern.search(text)
            if m:
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.PLATFORM_REDIRECT,
                    block_message="Moving to other apps or platforms is blocked by Parental Controls.",
                    alert_admin=True,
                    matched_keywords=[m.group()],
                    policy_mode=mode,
                    settings=settings,
                )

    if interaction_safety.get("block_external_links", False):
        for pattern in _get_patterns("external_link"):
            m = pattern.search(text)
            if m:
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.EXTERNAL_LINK,
                    block_message="External links are blocked by Parental Controls.",
                    matched_keywords=[m.group()],
                    policy_mode=mode,
                    settings=settings,
                )

    # ── New: Cyberbullying detection ──
    if parental.get("block_cyberbullying", True):
        for pattern in _get_patterns("cyberbullying"):
            m = pattern.search(text)
            if m:
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.CYBERBULLYING,
                    block_message=(
                        "Cyberbullying language is blocked by Parental Controls. "
                        "Be kind online — words can hurt. If someone is bullying you, tell a trusted adult."
                    ),
                    alert_admin=True,
                    matched_keywords=[m.group()],
                    policy_mode=mode,
                    settings=settings,
                )

    # ── New: Online gaming blocking ──
    if parental.get("block_online_gaming", False):
        for pattern in _get_patterns("online_gaming"):
            m = pattern.search(text)
            if m:
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.MATURE_TOPIC,
                    block_message="Online gaming content is blocked by Parental Controls.",
                    alert_admin=True,
                    matched_keywords=[m.group()],
                    policy_mode=mode,
                    settings=settings,
                )

    # ── New: Streaming blocking ──
    if parental.get("block_streaming", False):
        for pattern in _get_patterns("streaming"):
            m = pattern.search(text)
            if m:
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.MATURE_TOPIC,
                    block_message="Streaming content is blocked by Parental Controls.",
                    alert_admin=True,
                    matched_keywords=[m.group()],
                    policy_mode=mode,
                    settings=settings,
                )

    # ── New: Online shopping blocking ──
    if parental.get("block_shopping", False):
        for pattern in _get_patterns("online_shopping"):
            m = pattern.search(text)
            if m:
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.MATURE_TOPIC,
                    block_message="Online shopping is blocked by Parental Controls. Ask your parent before buying things.",
                    alert_admin=True,
                    matched_keywords=[m.group()],
                    policy_mode=mode,
                    settings=settings,
                )

    # ── New: Financial blocking ──
    if parental.get("block_financial", False):
        for pattern in _get_patterns("financial_trading"):
            m = pattern.search(text)
            if m:
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.MATURE_TOPIC,
                    block_message="Financial content is blocked by Parental Controls.",
                    alert_admin=True,
                    matched_keywords=[m.group()],
                    policy_mode=mode,
                    settings=settings,
                )

    # ── New: Website blocking ──
    for website in parental.get("blocked_websites", []):
        if website.lower() in text.lower():
            return PolicyScreenResult(
                allowed=False,
                blocked_reason=PolicyBlockReason.WEBSITE_BLOCKED,
                block_message=f"Website '{website}' is blocked by Parental Controls.",
                alert_admin=True,
                matched_keywords=[website],
                policy_mode=mode,
                settings=settings,
            )

    # ── New: Custom blocked keywords (parent-defined) ──
    for keyword in parental.get("custom_blocked_keywords", []):
        pattern = re.compile(r"\b" + re.escape(keyword) + r"\b", re.IGNORECASE)
        m = pattern.search(text)
        if m:
            return PolicyScreenResult(
                allowed=False,
                blocked_reason=PolicyBlockReason.CUSTOM_KEYWORD,
                block_message=f"Content blocked by Parental Controls (custom keyword: '{keyword}').",
                alert_admin=True,
                matched_keywords=[m.group()],
                policy_mode=mode,
                settings=settings,
            )

    return PolicyScreenResult(allowed=True, policy_mode=mode, settings=settings)


def _screen_enterprise(text: str, settings: dict, mode: PolicyMode) -> PolicyScreenResult:
    """Screen input through enterprise controls."""
    ent = settings.get("enterprise", {})
    if not ent.get("enabled", False):
        return PolicyScreenResult(allowed=True, policy_mode=mode, settings=settings)

    # Check data exfiltration
    if ent.get("block_data_exfiltration", True):
        for pattern in _get_patterns("data_exfiltration"):
            m = pattern.search(text)
            if m:
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.DATA_EXFILTRATION,
                    block_message=(
                        "Data exfiltration attempt blocked by Enterprise Policy. "
                        "Sending company data to external destinations is not allowed."
                    ),
                    alert_admin=True,
                    matched_keywords=[m.group()],
                    policy_mode=mode,
                    settings=settings,
                )

    # Check entertainment
    if ent.get("block_entertainment", True):
        for pattern in _get_patterns("entertainment"):
            m = pattern.search(text)
            if m:
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.ENTERTAINMENT_BLOCKED,
                    block_message=(
                        "Entertainment content is blocked by Enterprise Policy. "
                        "This workstation is for work purposes only."
                    ),
                    alert_admin=True,
                    matched_keywords=[m.group()],
                    policy_mode=mode,
                    settings=settings,
                )

    # Check social media
    if ent.get("block_social_media", True):
        for pattern in _get_patterns("social_media"):
            m = pattern.search(text)
            if m:
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.SOCIAL_MEDIA_BLOCKED,
                    block_message=(
                        "Social media content is blocked by Enterprise Policy. "
                        "This workstation is for work purposes only."
                    ),
                    alert_admin=True,
                    matched_keywords=[m.group()],
                    policy_mode=mode,
                    settings=settings,
                )

    # Check personal use
    if ent.get("block_personal_use", True):
        for pattern in _get_patterns("personal_use"):
            m = pattern.search(text)
            if m:
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.NON_WORK_TOPIC,
                    block_message=(
                        "Personal use is blocked by Enterprise Policy. "
                        "This workstation is for work purposes only."
                    ),
                    alert_admin=True,
                    matched_keywords=[m.group()],
                    policy_mode=mode,
                    settings=settings,
                )

    # ── New: Online gaming blocking ──
    if ent.get("block_online_gaming", True):
        for pattern in _get_patterns("online_gaming"):
            m = pattern.search(text)
            if m:
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.ENTERTAINMENT_BLOCKED,
                    block_message="Online gaming is blocked by Enterprise Policy.",
                    alert_admin=True,
                    matched_keywords=[m.group()],
                    policy_mode=mode,
                    settings=settings,
                )

    # ── New: Streaming blocking ──
    if ent.get("block_streaming", True):
        for pattern in _get_patterns("streaming"):
            m = pattern.search(text)
            if m:
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.ENTERTAINMENT_BLOCKED,
                    block_message="Streaming content is blocked by Enterprise Policy.",
                    alert_admin=True,
                    matched_keywords=[m.group()],
                    policy_mode=mode,
                    settings=settings,
                )

    # ── New: Online shopping blocking ──
    if ent.get("block_online_shopping", True):
        for pattern in _get_patterns("online_shopping"):
            m = pattern.search(text)
            if m:
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.NON_WORK_TOPIC,
                    block_message="Online shopping is blocked by Enterprise Policy.",
                    alert_admin=True,
                    matched_keywords=[m.group()],
                    policy_mode=mode,
                    settings=settings,
                )

    # ── New: Financial trading blocking ──
    if ent.get("block_financial_trading", True):
        for pattern in _get_patterns("financial_trading"):
            m = pattern.search(text)
            if m:
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.NON_WORK_TOPIC,
                    block_message="Financial trading is blocked by Enterprise Policy.",
                    alert_admin=True,
                    matched_keywords=[m.group()],
                    policy_mode=mode,
                    settings=settings,
                )

    # ── New: Job search blocking (HR setting) ──
    if not ent.get("block_job_search", False):
        pass  # job search allowed
    else:
        for pattern in _get_patterns("job_search"):
            m = pattern.search(text)
            if m:
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.NON_WORK_TOPIC,
                    block_message="Job search content is blocked by Enterprise Policy.",
                    alert_admin=True,
                    matched_keywords=[m.group()],
                    policy_mode=mode,
                    settings=settings,
                )

    # ── New: Website blocking ──
    for website in ent.get("blocked_websites", []):
        if website.lower() in text.lower():
            return PolicyScreenResult(
                allowed=False,
                blocked_reason=PolicyBlockReason.WEBSITE_BLOCKED,
                block_message=f"Website '{website}' is blocked by Enterprise Policy.",
                alert_admin=True,
                matched_keywords=[website],
                policy_mode=mode,
                settings=settings,
            )

    # ── New: Custom blocked keywords (company-defined) ──
    for keyword in ent.get("custom_blocked_keywords", []):
        pattern = re.compile(r"\b" + re.escape(keyword) + r"\b", re.IGNORECASE)
        m = pattern.search(text)
        if m:
            return PolicyScreenResult(
                allowed=False,
                blocked_reason=PolicyBlockReason.CUSTOM_KEYWORD,
                block_message=f"Content blocked by Enterprise Policy (custom keyword: '{keyword}').",
                alert_admin=True,
                matched_keywords=[m.group()],
                policy_mode=mode,
                settings=settings,
            )

    return PolicyScreenResult(allowed=True, policy_mode=mode, settings=settings)


# ── Time-Based Checks ──

def check_session_time(settings: dict, session_start_time: float) -> PolicyScreenResult:
    """Check if session has exceeded the time limit."""
    mode_str = settings.get("mode", PolicyMode.DISABLED.value)
    try:
        mode = PolicyMode(mode_str)
    except ValueError:
        mode = PolicyMode.DISABLED

    if mode == PolicyMode.DISABLED:
        return PolicyScreenResult(allowed=True, policy_mode=mode, settings=settings)

    section = settings.get("parental" if mode == PolicyMode.PARENTAL else "enterprise", {})
    max_minutes = section.get("max_session_minutes", 0)
    if max_minutes <= 0:
        return PolicyScreenResult(allowed=True, policy_mode=mode, settings=settings)

    elapsed = (time.time() - session_start_time) / 60.0
    if elapsed >= max_minutes:
        return PolicyScreenResult(
            allowed=False,
            blocked_reason=PolicyBlockReason.SESSION_LIMIT,
            block_message=f"Session time limit reached ({max_minutes} minutes). Take a break and come back later.",
            policy_mode=mode,
            settings=settings,
        )

    return PolicyScreenResult(allowed=True, policy_mode=mode, settings=settings)


def check_schedule(settings: dict) -> PolicyScreenResult:
    """Check if current time is within allowed access schedule."""
    mode_str = settings.get("mode", PolicyMode.DISABLED.value)
    try:
        mode = PolicyMode(mode_str)
    except ValueError:
        mode = PolicyMode.DISABLED

    if mode == PolicyMode.DISABLED:
        return PolicyScreenResult(allowed=True, policy_mode=mode, settings=settings)

    section = settings.get("parental" if mode == PolicyMode.PARENTAL else "enterprise", {})

    # Check bedtime (parental only)
    bedtime_str = section.get("bedtime", "")
    if bedtime_str and mode == PolicyMode.PARENTAL:
        try:
            bedtime = _parse_time(bedtime_str)
            now = datetime.now().time()
            if now >= bedtime:
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.BEDTIME_MODE,
                    block_message=f"It's past bedtime ({bedtime_str}). No more AI access tonight. Good night!",
                    policy_mode=mode,
                    settings=settings,
                )
        except Exception:
            pass

    # Check scheduled access
    start_str = section.get("scheduled_access_start", "")
    end_str = section.get("scheduled_access_end", "")
    if start_str and end_str:
        try:
            start = _parse_time(start_str)
            end = _parse_time(end_str)
            now = datetime.now().time()
            if not (start <= now <= end):
                return PolicyScreenResult(
                    allowed=False,
                    blocked_reason=PolicyBlockReason.OUTSIDE_SCHEDULE,
                    block_message=f"Access is only allowed between {start_str} and {end_str}.",
                    policy_mode=mode,
                    settings=settings,
                )
        except Exception:
            pass

    return PolicyScreenResult(allowed=True, policy_mode=mode, settings=settings)


def _parse_time(time_str: str) -> dtime:
    """Parse 'HH:MM' format to time object."""
    parts = time_str.strip().split(":")
    return dtime(int(parts[0]), int(parts[1]))


# ── Capability Checking (Enterprise) ──

def check_capability_allowed(capability: str, settings: dict) -> tuple[bool, str]:
    """Check if a capability is allowed by the enterprise policy.

    Returns (allowed, reason).
    """
    mode_str = settings.get("mode", PolicyMode.DISABLED.value)
    try:
        mode = PolicyMode(mode_str)
    except ValueError:
        mode = PolicyMode.DISABLED

    if mode == PolicyMode.DISABLED:
        return True, ""

    ent = settings.get("enterprise", {})
    if not ent.get("enabled", False):
        return True, ""

    # Check blacklist
    blocked = ent.get("blocked_capabilities", [])
    if capability in blocked:
        return False, f"Capability '{capability}' is blocked by Enterprise Policy."

    # Check whitelist (if populated, only whitelisted capabilities are allowed)
    allowed = ent.get("allowed_capabilities", [])
    if allowed and capability not in allowed:
        return False, f"Capability '{capability}' is not in the allowed list. Only {', '.join(allowed)} are permitted."

    return True, ""


def check_file_path_allowed(path: str, settings: dict) -> tuple[bool, str]:
    """Check if a file path is allowed by the enterprise policy.

    Returns (allowed, reason).
    """
    mode_str = settings.get("mode", PolicyMode.DISABLED.value)
    try:
        mode = PolicyMode(mode_str)
    except ValueError:
        mode = PolicyMode.DISABLED

    if mode == PolicyMode.DISABLED:
        return True, ""

    ent = settings.get("enterprise", {})
    if not ent.get("enabled", False):
        return True, ""

    # Check blocked paths
    blocked = ent.get("blocked_file_paths", [])
    for bp in blocked:
        if bp.lower() in path.lower():
            return False, f"File path '{path}' is blocked by Enterprise Policy (matches '{bp}')."

    # Check allowed paths (if populated, only these are allowed)
    allowed = ent.get("allowed_file_paths", [])
    if allowed:
        if not any(ap.lower() in path.lower() for ap in allowed):
            return False, f"File path '{path}' is not in the allowed directories."

    return True, ""


def check_backend_allowed(is_local: bool, settings: dict) -> tuple[bool, str]:
    """Check if the backend type is allowed by enterprise policy.

    Returns (allowed, reason).
    """
    mode_str = settings.get("mode", PolicyMode.DISABLED.value)
    try:
        mode = PolicyMode(mode_str)
    except ValueError:
        mode = PolicyMode.DISABLED

    if mode == PolicyMode.DISABLED:
        return True, ""

    ent = settings.get("enterprise", {})
    if not ent.get("enabled", False):
        return True, ""

    if ent.get("local_backend_only", False) and not is_local:
        return False, "Remote/cloud backends are blocked by Enterprise Policy. Only local backends are allowed."

    return True, ""


# ── Logging ──

def log_conversation(text: str, ai_name: str, settings: dict) -> None:
    """Log a conversation entry for parent/admin review."""
    mode_str = settings.get("mode", PolicyMode.DISABLED.value)
    if mode_str == PolicyMode.DISABLED.value:
        return

    section = settings.get("parental" if mode_str == PolicyMode.PARENTAL else "enterprise", {})
    if not section.get("log_all_conversations", False) and not section.get("compliance_logging", False):
        return

    try:
        log_dir = Path.home() / ".command_nexus" / "policy_logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"conversation_{time.strftime('%Y-%m-%d')}.jsonl"

        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "ai_name": ai_name,
            "mode": mode_str,
            "text": text[:500],
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def alert_admin(message: str, settings: dict) -> None:
    """Write an admin/parent alert."""
    try:
        alert_dir = Path.home() / ".command_nexus" / "policy_alerts"
        alert_dir.mkdir(parents=True, exist_ok=True)
        alert_file = alert_dir / f"alert_{int(time.time())}.json"
        alert_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "message": message,
            "mode": settings.get("mode", ""),
        }
        alert_file.write_text(json.dumps(alert_data, indent=2), encoding="utf-8")
    except Exception:
        pass


# ── Preset Application ──

def apply_age_preset(preset_name: str, settings: dict) -> dict:
    """Apply an age preset to parental settings."""
    preset = AGE_PRESETS.get(preset_name)
    if not preset:
        return settings

    settings.setdefault("parental", {}).update(preset["settings"])
    settings["parental"]["age_preset"] = preset_name
    settings["parental"]["enabled"] = True
    if settings.get("mode", PolicyMode.DISABLED.value) == PolicyMode.DISABLED.value:
        settings["mode"] = PolicyMode.PARENTAL.value
    return settings


def apply_enterprise_preset(preset_name: str, settings: dict) -> dict:
    """Apply an enterprise preset to enterprise settings."""
    preset = ENTERPRISE_PRESETS.get(preset_name)
    if not preset:
        return settings

    settings.setdefault("enterprise", {}).update(preset["settings"])
    settings["enterprise"]["enabled"] = True
    if settings.get("mode", PolicyMode.DISABLED.value) == PolicyMode.DISABLED.value:
        settings["mode"] = PolicyMode.ENTERPRISE.value
    return settings


# ── New: Enterprise Multi-User Functions ──

def check_model_allowed(model_name: str, settings: dict) -> tuple[bool, str]:
    """Check if an AI model is allowed by enterprise policy.

    Returns (allowed, reason).
    """
    mode_str = settings.get("mode", PolicyMode.DISABLED.value)
    if mode_str == PolicyMode.DISABLED.value:
        return True, ""

    ent = settings.get("enterprise", {})
    if not ent.get("enabled", False):
        return True, ""

    blocked = ent.get("blocked_models", [])
    if model_name.lower() in [m.lower() for m in blocked]:
        return False, f"Model '{model_name}' is blocked by Enterprise Policy."

    allowed = ent.get("allowed_models", [])
    if allowed and model_name.lower() not in [m.lower() for m in allowed]:
        return False, f"Model '{model_name}' is not in the approved models list."

    return True, ""


def check_ip_allowed(ip_address: str, settings: dict) -> tuple[bool, str]:
    """Check if an IP address is allowed by enterprise policy.

    Returns (allowed, reason).
    """
    mode_str = settings.get("mode", PolicyMode.DISABLED.value)
    if mode_str == PolicyMode.DISABLED.value:
        return True, ""

    ent = settings.get("enterprise", {})
    if not ent.get("enabled", False):
        return True, ""

    allowed_ips = ent.get("allowed_ip_addresses", [])
    if allowed_ips and ip_address not in allowed_ips:
        return False, f"IP address '{ip_address}' is not in the allowed list. Access restricted to approved networks only."

    return True, ""


def check_weekend_allowed(settings: dict) -> PolicyScreenResult:
    """Check if access is allowed on the current day.

    Returns PolicyScreenResult.
    """
    mode_str = settings.get("mode", PolicyMode.DISABLED.value)
    try:
        mode = PolicyMode(mode_str)
    except ValueError:
        mode = PolicyMode.DISABLED

    if mode == PolicyMode.DISABLED:
        return PolicyScreenResult(allowed=True, policy_mode=mode, settings=settings)

    ent = settings.get("enterprise", {})
    if not ent.get("enabled", False):
        return PolicyScreenResult(allowed=True, policy_mode=mode, settings=settings)

    # Check weekend blocking
    if ent.get("block_weekends", False):
        today = datetime.now().weekday()  # 0=Monday, 5=Saturday, 6=Sunday
        if today >= 5:
            return PolicyScreenResult(
                allowed=False,
                blocked_reason=PolicyBlockReason.WEEKEND_BLOCKED,
                block_message="Weekend access is blocked by Enterprise Policy. Access is allowed on business days only.",
                policy_mode=mode,
                settings=settings,
            )

    # Check allowed days
    allowed_days = ent.get("allowed_days", [])
    if allowed_days:
        day_map = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}
        today_str = day_map.get(datetime.now().weekday(), "")
        if today_str and today_str not in [d.lower() for d in allowed_days]:
            return PolicyScreenResult(
                allowed=False,
                blocked_reason=PolicyBlockReason.WEEKEND_BLOCKED,
                block_message=f"Access is only allowed on: {', '.join(allowed_days)}. Today is {today_str}.",
                policy_mode=mode,
                settings=settings,
            )

    return PolicyScreenResult(allowed=True, policy_mode=mode, settings=settings)


def get_user_role(username: str, settings: dict) -> str:
    """Get the role for a given user.

    Returns the role name, or the default role if user not found.
    """
    ent = settings.get("enterprise", {})
    users = ent.get("users", [])
    for user in users:
        if user.get("username", "").lower() == username.lower():
            return user.get("role", ent.get("default_role", "employee"))
    return ent.get("default_role", "employee")


def get_role_permissions(role: str, settings: dict) -> dict:
    """Get the permissions for a given role."""
    ent = settings.get("enterprise", {})
    roles = ent.get("roles", {})
    return roles.get(role, roles.get("employee", {}))


def check_user_authorized(username: str, settings: dict) -> tuple[bool, str]:
    """Check if a user is authorized to use the system.

    Returns (authorized, reason).
    """
    mode_str = settings.get("mode", PolicyMode.DISABLED.value)
    if mode_str == PolicyMode.DISABLED.value:
        return True, ""

    ent = settings.get("enterprise", {})
    if not ent.get("enabled", False):
        return True, ""

    # Check seat count
    seat_count = ent.get("seat_count", 1)
    users = ent.get("users", [])
    if len(users) > seat_count:
        # Check if this user is in the registered users list
        registered = [u.get("username", "").lower() for u in users[:seat_count]]
        if username.lower() not in registered:
            return False, f"User '{username}' is not within the licensed seat count ({seat_count} seats). Contact your administrator."

    return True, ""


def check_quota(username: str, settings: dict) -> tuple[bool, str]:
    """Check if a user has remaining quota for today.

    Returns (allowed, reason).
    """
    mode_str = settings.get("mode", PolicyMode.DISABLED.value)
    if mode_str == PolicyMode.DISABLED.value:
        return True, ""

    ent = settings.get("enterprise", {})
    if not ent.get("enabled", False):
        return True, ""

    role = get_user_role(username, settings)
    perms = get_role_permissions(role, settings)
    max_messages = perms.get("quota_messages_per_day", 0)
    max_tokens = perms.get("quota_tokens_per_day", 0)

    if max_messages <= 0 and max_tokens <= 0:
        return True, ""

    # Check usage file
    try:
        usage_dir = Path.home() / ".command_nexus" / "policy_usage"
        usage_file = usage_dir / f"usage_{username}_{time.strftime('%Y-%m-%d')}.json"
        if usage_file.exists():
            usage = json.loads(usage_file.read_text(encoding="utf-8"))
            messages_used = usage.get("messages", 0)
            tokens_used = usage.get("tokens", 0)
            if max_messages > 0 and messages_used >= max_messages:
                return False, f"Daily message quota exceeded ({messages_used}/{max_messages}). Contact your administrator for more."
            if max_tokens > 0 and tokens_used >= max_tokens:
                return False, f"Daily token quota exceeded ({tokens_used}/{max_tokens}). Contact your administrator for more."
    except Exception:
        pass

    return True, ""


def record_usage(username: str, messages: int = 1, tokens: int = 0, settings: dict = None) -> None:
    """Record usage for quota tracking."""
    if settings is None:
        settings = load_policy_settings()
    mode_str = settings.get("mode", PolicyMode.DISABLED.value)
    if mode_str == PolicyMode.DISABLED.value:
        return

    try:
        usage_dir = Path.home() / ".command_nexus" / "policy_usage"
        usage_dir.mkdir(parents=True, exist_ok=True)
        usage_file = usage_dir / f"usage_{username}_{time.strftime('%Y-%m-%d')}.json"
        usage = {"messages": 0, "tokens": 0, "date": time.strftime("%Y-%m-%d")}
        if usage_file.exists():
            usage = json.loads(usage_file.read_text(encoding="utf-8"))
        usage["messages"] = usage.get("messages", 0) + messages
        usage["tokens"] = usage.get("tokens", 0) + tokens
        usage_file.write_text(json.dumps(usage, indent=2), encoding="utf-8")
    except Exception:
        pass


# ── New: Data Retention ──

def cleanup_old_logs(settings: dict) -> int:
    """Delete log files older than the retention period.

    Returns number of files deleted.
    """
    mode_str = settings.get("mode", PolicyMode.DISABLED.value)
    if mode_str == PolicyMode.DISABLED.value:
        return 0

    ent = settings.get("enterprise", {})
    retention_days = ent.get("data_retention_days", 0)
    if retention_days <= 0:
        return 0

    deleted = 0
    cutoff = time.time() - (retention_days * 86400)

    for log_dir_name in ["policy_logs", "policy_alerts", "policy_usage"]:
        log_dir = Path.home() / ".command_nexus" / log_dir_name
        if not log_dir.exists():
            continue
        for f in log_dir.iterdir():
            try:
                if f.stat().st_mtime < cutoff:
                    f.unlink()
                    deleted += 1
            except Exception:
                pass

    return deleted


# ── New: Usage Reports (Parental) ──

def generate_usage_report(settings: dict, days: int = 7) -> dict:
    """Generate a usage report for parent/admin review.

    Returns a dict with summary statistics.
    """
    report = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "period_days": days,
        "total_conversations": 0,
        "blocked_attempts": 0,
        "alerts": 0,
        "daily_breakdown": {},
    }

    log_dir = Path.home() / ".command_nexus" / "policy_logs"
    alert_dir = Path.home() / ".command_nexus" / "policy_alerts"

    cutoff = time.time() - (days * 86400)

    # Count conversations
    if log_dir.exists():
        for f in log_dir.iterdir():
            try:
                if f.stat().st_mtime < cutoff:
                    continue
                if f.suffix == ".jsonl":
                    lines = f.read_text(encoding="utf-8").strip().split("\n")
                    report["total_conversations"] += len(lines)
                    day = f.stem.replace("conversation_", "")
                    report["daily_breakdown"].setdefault(day, {"conversations": 0, "alerts": 0})
                    report["daily_breakdown"][day]["conversations"] += len(lines)
            except Exception:
                pass

    # Count alerts
    if alert_dir.exists():
        for f in alert_dir.iterdir():
            try:
                if f.stat().st_mtime < cutoff:
                    continue
                report["alerts"] += 1
                # Try to read the alert date
                alert_data = json.loads(f.read_text(encoding="utf-8"))
                day = alert_data.get("timestamp", "")[:10]
                if day:
                    report["daily_breakdown"].setdefault(day, {"conversations": 0, "alerts": 0})
                    report["daily_breakdown"][day]["alerts"] += 1
            except Exception:
                pass

    return report


# ── New: Output Watermarking (Enterprise) ──

def watermark_output(text: str, username: str, settings: dict) -> str:
    """Add a watermark to AI output for enterprise compliance.

    Returns the watermarked text.
    """
    mode_str = settings.get("mode", PolicyMode.DISABLED.value)
    if mode_str == PolicyMode.DISABLED.value:
        return text

    ent = settings.get("enterprise", {})
    if not ent.get("enabled", False) or not ent.get("watermark_outputs", True):
        return text

    company = ent.get("company_name", "Enterprise")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    watermark = f"\n\n--- Generated by Command Nexus for {company} | User: {username} | {timestamp} ---"

    return text + watermark


# ── New: Child Profile Management (Parental) ──

def add_child_profile(name: str, age: int, preset: str, settings: dict) -> dict:
    """Add a child profile to parental settings."""
    settings.setdefault("parental", {})
    profiles = settings["parental"].setdefault("child_profiles", [])
    profiles.append({"name": name, "age": age, "preset": preset})
    return settings


def switch_child_profile(name: str, settings: dict) -> dict:
    """Switch to a different child profile, applying its preset."""
    settings.setdefault("parental", {})
    profiles = settings["parental"].get("child_profiles", [])
    for profile in profiles:
        if profile["name"] == name:
            settings["parental"]["active_child_profile"] = name
            preset = profile.get("preset", "")
            if preset:
                apply_age_preset(preset, settings)
            break
    return settings
