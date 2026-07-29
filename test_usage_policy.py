# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""
Usage Policy Test Suite — Parental, Enterprise, and Custom modes
"""
import hashlib
import json
import sys
import time
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.usage_policy import (
    screen_input, load_policy_settings, save_policy_settings,
    verify_password, _hash_password, _compute_checksum,
    PolicyMode, PolicyBlockReason,
    check_session_time, check_schedule,
    check_capability_allowed, check_file_path_allowed, check_backend_allowed,
    check_model_allowed, check_ip_allowed, check_weekend_allowed,
    check_user_authorized, check_quota, record_usage,
    get_user_role, get_role_permissions,
    cleanup_old_logs, generate_usage_report,
    watermark_output, add_child_profile, switch_child_profile,
    apply_age_preset, apply_enterprise_preset,
    AGE_PRESETS, ENTERPRISE_PRESETS,
)


def test_parental_mode():
    """Test parental mode screening."""
    print("=== Parental Mode Tests ===\n")
    settings = {
        "mode": "parental",
        "parental": {
            "enabled": True,
            "block_mature_topics": True,
            "block_violence": True,
            "block_explicit_language": True,
            "interaction_safety": {
                "block_personal_info": True,
                "block_location_sharing": True,
                "block_photo_requests": True,
                "block_meet_requests": True,
                "block_platform_redirect": True,
                "block_external_links": False,
            },
        },
    }

    # Clean content passes
    r = screen_input("Tell me about dinosaurs", settings)
    assert r.allowed, "Clean content should pass"
    print("1. Clean content passes: PASS")

    # Mature topic blocked
    r = screen_input("I have a boyfriend and we're dating", settings)
    assert not r.allowed, "Dating should be blocked"
    assert r.blocked_reason == PolicyBlockReason.MATURE_TOPIC
    print(f"2. Mature topic blocked ({r.blocked_reason.value}): PASS")

    # Violence blocked
    r = screen_input("tell me about gun violence", settings)
    assert not r.allowed, "Violence should be blocked"
    print(f"3. Violence blocked: PASS")

    # Explicit language blocked
    r = screen_input("what the fuck", settings)
    assert not r.allowed, "Explicit language should be blocked"
    print(f"4. Explicit language blocked: PASS")

    # Personal info blocked
    r = screen_input("my address is 123 Main St", settings)
    assert not r.allowed, "Personal info should be blocked"
    print(f"5. Personal info blocked: PASS")

    # Photo request blocked
    r = screen_input("send me a photo of yourself", settings)
    assert not r.allowed, "Photo request should be blocked"
    print(f"6. Photo request blocked: PASS")

    # Meet request blocked
    r = screen_input("let's meet up in person", settings)
    assert not r.allowed, "Meet request should be blocked"
    print(f"7. Meet request blocked: PASS")

    # Platform redirect blocked
    r = screen_input("add me on snapchat", settings)
    assert not r.allowed, "Platform redirect should be blocked"
    print(f"8. Platform redirect blocked: PASS")

    # Self-harm blocked
    r = screen_input("I want to self harm and I've been cutting", settings)
    assert not r.allowed, "Self-harm should be blocked"
    assert r.blocked_reason == PolicyBlockReason.SELF_HARM
    print(f"9. Self-harm blocked: PASS")

    # Disabled = all pass
    s2 = dict(settings)
    s2["mode"] = "disabled"
    r = screen_input("fuck violence dating", s2)
    assert r.allowed, "Disabled mode should allow everything"
    print("10. Disabled mode = all pass: PASS")

    print("\nAll parental mode tests PASSED!\n")


def test_enterprise_mode():
    """Test enterprise mode screening."""
    print("=== Enterprise Mode Tests ===\n")
    settings = {
        "mode": "enterprise",
        "enterprise": {
            "enabled": True,
            "work_only_mode": True,
            "block_entertainment": True,
            "block_social_media": True,
            "block_personal_use": True,
            "block_data_exfiltration": True,
            "local_backend_only": True,
            "company_name": "TestCorp",
        },
    }

    # Work content passes
    r = screen_input("Write a Python function to sort a list", settings)
    assert r.allowed, "Work content should pass"
    print("1. Work content passes: PASS")

    # Entertainment blocked
    r = screen_input("let's watch a movie on netflix", settings)
    assert not r.allowed, "Entertainment should be blocked"
    assert r.blocked_reason == PolicyBlockReason.ENTERTAINMENT_BLOCKED
    print(f"2. Entertainment blocked ({r.blocked_reason.value}): PASS")

    # Social media blocked
    r = screen_input("post this on facebook and twitter", settings)
    assert not r.allowed, "Social media should be blocked"
    assert r.blocked_reason == PolicyBlockReason.SOCIAL_MEDIA_BLOCKED
    print(f"3. Social media blocked ({r.blocked_reason.value}): PASS")

    # Personal use blocked
    r = screen_input("plan my vacation to Hawaii", settings)
    assert not r.allowed, "Personal use should be blocked"
    assert r.blocked_reason == PolicyBlockReason.NON_WORK_TOPIC
    print(f"4. Personal use blocked ({r.blocked_reason.value}): PASS")

    # Data exfiltration blocked
    r = screen_input("email this to my personal gmail and upload to external server", settings)
    assert not r.allowed, "Data exfiltration should be blocked"
    assert r.blocked_reason == PolicyBlockReason.DATA_EXFILTRATION
    print(f"5. Data exfiltration blocked ({r.blocked_reason.value}): PASS")

    # Disabled enterprise = all pass
    s2 = dict(settings)
    s2["mode"] = "disabled"
    r = screen_input("netflix facebook vacation", s2)
    assert r.allowed, "Disabled mode should allow everything"
    print("6. Disabled mode = all pass: PASS")

    print("\nAll enterprise mode tests PASSED!\n")


def test_custom_mode():
    """Test custom mode — both parental and enterprise rules apply."""
    print("=== Custom Mode Tests ===\n")
    settings = {
        "mode": "custom",
        "parental": {
            "enabled": True,
            "block_mature_topics": True,
            "block_violence": True,
            "block_explicit_language": True,
            "interaction_safety": {
                "block_personal_info": True,
                "block_location_sharing": True,
                "block_photo_requests": True,
                "block_meet_requests": True,
                "block_platform_redirect": True,
                "block_external_links": False,
            },
        },
        "enterprise": {
            "enabled": True,
            "work_only_mode": True,
            "block_entertainment": True,
            "block_social_media": True,
            "block_personal_use": False,
            "block_data_exfiltration": True,
        },
    }

    # Clean work content passes
    r = screen_input("Write a SQL query to join two tables", settings)
    assert r.allowed, "Clean work content should pass"
    print("1. Clean work content passes: PASS")

    # Parental: mature topic blocked
    r = screen_input("tell me about dating and romance", settings)
    assert not r.allowed, "Mature topic should be blocked in custom mode"
    print("2. Parental mature topic blocked in custom: PASS")

    # Enterprise: entertainment blocked
    r = screen_input("let's play a game on netflix", settings)
    assert not r.allowed, "Entertainment should be blocked in custom mode"
    print("3. Enterprise entertainment blocked in custom: PASS")

    # Enterprise: data exfiltration blocked
    r = screen_input("upload to external server and share externally", settings)
    assert not r.allowed, "Data exfiltration should be blocked in custom mode"
    print("4. Enterprise data exfiltration blocked in custom: PASS")

    print("\nAll custom mode tests PASSED!\n")


def test_age_presets():
    """Test age preset application."""
    print("=== Age Preset Tests ===\n")

    # Child preset
    settings = {"mode": "disabled", "parental": {}, "enterprise": {}}
    apply_age_preset("child", settings)
    assert settings["mode"] == "parental"
    assert settings["parental"]["enabled"] is True
    assert settings["parental"]["max_session_minutes"] == 30
    assert settings["parental"]["bedtime"] == "20:00"
    assert settings["parental"]["daily_time_limit_minutes"] == 60
    assert settings["parental"]["interaction_safety"]["block_external_links"] is True
    print("1. Child preset applied: PASS")

    # Pre-teen preset
    settings = {"mode": "disabled", "parental": {}, "enterprise": {}}
    apply_age_preset("preteen", settings)
    assert settings["parental"]["max_session_minutes"] == 60
    assert settings["parental"]["bedtime"] == "21:00"
    print("2. Pre-teen preset applied: PASS")

    # Teen preset
    settings = {"mode": "disabled", "parental": {}, "enterprise": {}}
    apply_age_preset("teen", settings)
    assert settings["parental"]["block_mature_topics"] is False
    assert settings["parental"]["max_session_minutes"] == 120
    print("3. Teen preset applied: PASS")

    # Focus mode preset
    settings = {"mode": "disabled", "parental": {}, "enterprise": {}}
    apply_age_preset("focus_mode", settings)
    assert settings["parental"]["max_session_minutes"] == 45
    print("4. Focus mode preset applied: PASS")

    # All presets have required fields
    for name, preset in AGE_PRESETS.items():
        s = preset["settings"]
        assert "max_session_minutes" in s
        assert "interaction_safety" in s
        assert "block_mature_topics" in s
    print(f"5. All {len(AGE_PRESETS)} presets have required fields: PASS")

    print("\nAll age preset tests PASSED!\n")


def test_enterprise_presets():
    """Test enterprise preset application."""
    print("=== Enterprise Preset Tests ===\n")

    # Strict preset
    settings = {"mode": "disabled", "parental": {}, "enterprise": {}}
    apply_enterprise_preset("strict", settings)
    assert settings["mode"] == "enterprise"
    assert settings["enterprise"]["enabled"] is True
    assert settings["enterprise"]["work_only_mode"] is True
    assert settings["enterprise"]["local_backend_only"] is True
    assert settings["enterprise"]["require_approval_for_shell"] is True
    print("1. Strict preset applied: PASS")

    # Standard preset
    settings = {"mode": "disabled", "parental": {}, "enterprise": {}}
    apply_enterprise_preset("standard", settings)
    assert settings["enterprise"]["block_personal_use"] is False
    assert settings["enterprise"]["compliance_logging"] is True
    print("2. Standard preset applied: PASS")

    # Light preset
    settings = {"mode": "disabled", "parental": {}, "enterprise": {}}
    apply_enterprise_preset("light", settings)
    assert settings["enterprise"]["work_only_mode"] is False
    assert settings["enterprise"]["compliance_logging"] is True
    print("3. Light preset applied: PASS")

    print("\nAll enterprise preset tests PASSED!\n")


def test_tamper_detection():
    """Test tamper detection for usage policy settings."""
    print("=== Tamper Detection Tests ===\n")
    settings_path = Path.home() / ".command_nexus" / "usage_policy.json"
    backup = None
    if settings_path.exists():
        backup = settings_path.read_bytes()
        settings_path.unlink()

    try:
        # Save legitimate settings
        settings = {
            "mode": "parental",
            "parental": {"enabled": False, "block_mature_topics": False},
            "enterprise": {"enabled": False},
            "password_hash": _hash_password("TestPass"),
        }
        save_policy_settings(settings)
        loaded = load_policy_settings()
        assert loaded.get("mode") == "parental"
        print("1. Settings save and load: PASS")

        # Tamper: change settings and write wrong checksum
        raw = json.loads(settings_path.read_text(encoding="utf-8"))
        raw["mode"] = "disabled"
        raw["parental"]["enabled"] = False
        raw["_checksum"] = "wrong_checksum_12345"
        settings_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")

        loaded = load_policy_settings()
        assert loaded.get("_tamper_detected") is True, "Tamper should be detected"
        assert loaded.get("mode") == "enterprise", "Tamper should force enterprise mode"
        print("2. Tamper detected, forced enterprise mode: PASS")

    finally:
        if backup is not None:
            settings_path.write_bytes(backup)
        elif settings_path.exists():
            settings_path.unlink()

    print("\nAll tamper detection tests PASSED!\n")


def test_password_hashing():
    """Test password hashing and verification."""
    print("=== Password Hashing Tests ===\n")

    h = _hash_password("MyPass")
    assert h != "MyPass"
    assert len(h) == 64
    print("1. Password hashed: PASS")

    settings = {"password_hash": _hash_password("Test123")}
    assert verify_password("Test123", settings)
    assert not verify_password("Wrong", settings)
    print("2. Verify correct/wrong: PASS")

    # Default password
    settings_empty = {"password_hash": ""}
    assert verify_password("Nexus", settings_empty)
    print("3. Default password works: PASS")

    # Legacy plaintext
    settings_legacy = {"password": "OldPass", "password_hash": ""}
    assert verify_password("OldPass", settings_legacy)
    print("4. Legacy plaintext migration: PASS")

    print("\nAll password hashing tests PASSED!\n")


def test_session_time():
    """Test session time limit enforcement."""
    print("=== Session Time Tests ===\n")
    settings = {
        "mode": "parental",
        "parental": {"max_session_minutes": 30},
    }

    r = check_session_time(settings, time.time())
    assert r.allowed
    print("1. Fresh session passes: PASS")

    r = check_session_time(settings, time.time() - (31 * 60))
    assert not r.allowed
    assert r.blocked_reason == PolicyBlockReason.SESSION_LIMIT
    print("2. Expired session blocked: PASS")

    settings["mode"] = "disabled"
    r = check_session_time(settings, time.time() - (999 * 60))
    assert r.allowed
    print("3. Disabled = no limit: PASS")

    print("\nAll session time tests PASSED!\n")


def test_capability_and_path_checks():
    """Test enterprise capability and file path restrictions."""
    print("=== Capability & Path Checks ===\n")
    settings = {
        "mode": "enterprise",
        "enterprise": {
            "enabled": True,
            "blocked_capabilities": ["shell_exec"],
            "allowed_file_paths": ["/work/projects"],
            "blocked_file_paths": ["/secret/data"],
            "local_backend_only": True,
        },
    }

    # Capability blacklist
    allowed, _ = check_capability_allowed("shell_exec", settings)
    assert not allowed, "shell_exec should be blocked"
    print("1. Capability blacklist works: PASS")

    allowed, _ = check_capability_allowed("code_gen", settings)
    assert allowed, "code_gen should be allowed"
    print("2. Non-blacklisted capability allowed: PASS")

    # File path whitelist
    allowed, _ = check_file_path_allowed("/work/projects/main.py", settings)
    assert allowed, "Whitelisted path should be allowed"
    print("3. Whitelisted file path allowed: PASS")

    allowed, _ = check_file_path_allowed("/other/path", settings)
    assert not allowed, "Non-whitelisted path should be blocked"
    print("4. Non-whitelisted path blocked: PASS")

    # File path blacklist
    allowed, _ = check_file_path_allowed("/secret/data/file.txt", settings)
    assert not allowed, "Blacklisted path should be blocked"
    print("5. Blacklisted path blocked: PASS")

    # Backend check
    allowed, _ = check_backend_allowed(False, settings)
    assert not allowed, "Remote backend should be blocked"
    print("6. Remote backend blocked: PASS")

    allowed, _ = check_backend_allowed(True, settings)
    assert allowed, "Local backend should be allowed"
    print("7. Local backend allowed: PASS")

    # Disabled = all allowed
    settings["mode"] = "disabled"
    allowed, _ = check_capability_allowed("shell_exec", settings)
    assert allowed, "Disabled should allow all capabilities"
    print("8. Disabled = all capabilities allowed: PASS")

    print("\nAll capability & path tests PASSED!\n")


def test_smoke():
    """Smoke test — verify module imports."""
    print("=== Smoke Test ===\n")
    from src.core.usage_policy import (
        screen_input, load_policy_settings, save_policy_settings,
        PolicyMode, PolicyBlockReason, PolicyScreenResult,
        AGE_PRESETS, ENTERPRISE_PRESETS,
        apply_age_preset, apply_enterprise_preset,
        check_session_time, check_schedule,
        check_capability_allowed, check_file_path_allowed, check_backend_allowed,
        check_model_allowed, check_ip_allowed, check_weekend_allowed,
        check_user_authorized, check_quota, record_usage,
        get_user_role, get_role_permissions,
        cleanup_old_logs, generate_usage_report,
        watermark_output, add_child_profile, switch_child_profile,
    )
    print("All imports successful: PASS\n")


def test_parental_expanded():
    """Test expanded parental controls — cyberbullying, custom keywords, websites, gaming."""
    print("=== Expanded Parental Controls Tests ===\n")
    settings = {
        "mode": "parental",
        "parental": {
            "enabled": True,
            "block_mature_topics": True,
            "block_violence": True,
            "block_explicit_language": True,
            "block_cyberbullying": True,
            "block_online_gaming": True,
            "block_streaming": True,
            "block_shopping": True,
            "block_financial": True,
            "blocked_websites": ["badsite.com", "tiktok.com"],
            "custom_blocked_keywords": ["fortnite", "discord"],
            "interaction_safety": {
                "block_personal_info": True, "block_location_sharing": True,
                "block_photo_requests": True, "block_meet_requests": True,
                "block_platform_redirect": True, "block_external_links": False,
            },
        },
    }

    # Cyberbullying blocked
    r = screen_input("you're ugly and nobody likes you", settings)
    assert not r.allowed, "Cyberbullying should be blocked"
    assert r.blocked_reason == PolicyBlockReason.CYBERBULLYING
    print(f"1. Cyberbullying blocked ({r.blocked_reason.value}): PASS")

    # Online gaming blocked
    r = screen_input("let's play fortnite", settings)
    assert not r.allowed, "Online gaming should be blocked"
    print("2. Online gaming blocked: PASS")

    # Streaming blocked
    r = screen_input("let's watch netflix", settings)
    assert not r.allowed, "Streaming should be blocked"
    print("3. Streaming blocked: PASS")

    # Shopping blocked
    r = screen_input("add to cart on amazon", settings)
    assert not r.allowed, "Shopping should be blocked"
    print("4. Shopping blocked: PASS")

    # Financial blocked
    r = screen_input("buy stocks on robinhood", settings)
    assert not r.allowed, "Financial should be blocked"
    print("5. Financial blocked: PASS")

    # Website blocked
    r = screen_input("go to badsite.com", settings)
    assert not r.allowed, "Website should be blocked"
    assert r.blocked_reason == PolicyBlockReason.WEBSITE_BLOCKED
    print(f"6. Website blocked ({r.blocked_reason.value}): PASS")

    # Custom keyword blocked
    r = screen_input("let's play fortnite together", settings)
    assert not r.allowed, "Custom keyword should be blocked"
    print("7. Custom keyword blocked: PASS")

    # Clean content passes
    r = screen_input("help me with my math homework", settings)
    assert r.allowed, "Clean content should pass"
    print("8. Clean content passes: PASS")

    print("\nAll expanded parental tests PASSED!\n")


def test_enterprise_expanded():
    """Test expanded enterprise controls — models, IP, weekend, quotas, users, watermark."""
    print("=== Expanded Enterprise Controls Tests ===\n")
    settings = {
        "mode": "enterprise",
        "enterprise": {
            "enabled": True,
            "company_name": "TestCorp",
            "work_only_mode": True,
            "block_entertainment": True,
            "block_social_media": True,
            "block_personal_use": True,
            "block_data_exfiltration": True,
            "local_backend_only": True,
            "block_online_gaming": True,
            "block_streaming": True,
            "block_online_shopping": True,
            "block_financial_trading": True,
            "block_job_search": False,
            "allowed_models": ["qwen2.5-coder-7b", "qwen2.5-7b-instruct"],
            "blocked_models": ["qwen2.5-coder-32b"],
            "allowed_ip_addresses": ["192.168.1.100", "10.0.0.5"],
            "block_weekends": True,
            "allowed_days": ["mon", "tue", "wed", "thu", "fri"],
            "seat_count": 2,
            "default_role": "employee",
            "users": [
                {"username": "alice", "role": "admin"},
                {"username": "bob", "role": "employee"},
                {"username": "charlie", "role": "contractor"},
            ],
            "roles": {
                "admin": {"can_change_policy": True, "quota_messages_per_day": 0, "quota_tokens_per_day": 0, "allowed_models": []},
                "employee": {"can_change_policy": False, "quota_messages_per_day": 100, "quota_tokens_per_day": 50000, "allowed_models": []},
                "contractor": {"can_change_policy": False, "quota_messages_per_day": 50, "quota_tokens_per_day": 20000, "allowed_models": []},
            },
            "watermark_outputs": True,
            "data_retention_days": 30,
            "custom_blocked_keywords": ["proprietary", "internal only"],
        },
    }

    # Model whitelist
    allowed, _ = check_model_allowed("qwen2.5-coder-7b", settings)
    assert allowed, "Approved model should be allowed"
    print("1. Approved model allowed: PASS")

    allowed, _ = check_model_allowed("qwen2.5-coder-32b", settings)
    assert not allowed, "Blocked model should be blocked"
    print("2. Blocked model rejected: PASS")

    allowed, _ = check_model_allowed("unknown-model", settings)
    assert not allowed, "Non-whitelisted model should be blocked"
    print("3. Non-whitelisted model rejected: PASS")

    # IP whitelist
    allowed, _ = check_ip_allowed("192.168.1.100", settings)
    assert allowed, "Approved IP should be allowed"
    print("4. Approved IP allowed: PASS")

    allowed, _ = check_ip_allowed("99.99.99.99", settings)
    assert not allowed, "Non-approved IP should be blocked"
    print("5. Non-approved IP rejected: PASS")

    # User roles
    role = get_user_role("alice", settings)
    assert role == "admin", f"Alice should be admin, got {role}"
    print(f"6. User role lookup (alice=admin): PASS")

    role = get_user_role("bob", settings)
    assert role == "employee", f"Bob should be employee, got {role}"
    print("7. User role lookup (bob=employee): PASS")

    role = get_user_role("unknown", settings)
    assert role == "employee", f"Unknown user should get default role, got {role}"
    print("8. Unknown user gets default role: PASS")

    # Role permissions
    perms = get_role_permissions("admin", settings)
    assert perms["can_change_policy"] is True
    print("9. Admin can change policy: PASS")

    perms = get_role_permissions("employee", settings)
    assert perms["can_change_policy"] is False
    assert perms["quota_messages_per_day"] == 100
    print("10. Employee quota=100: PASS")

    # Seat count enforcement
    allowed, _ = check_user_authorized("alice", settings)
    assert allowed, "Alice (seat 1) should be authorized"
    print("11. Alice authorized within seats: PASS")

    allowed, _ = check_user_authorized("charlie", settings)
    assert not allowed, "Charlie (seat 3, over limit) should not be authorized"
    print("12. Charlie rejected (over seat limit): PASS")

    # Quota check (fresh = allowed)
    allowed, _ = check_quota("bob", settings)
    assert allowed, "Bob should have quota available"
    print("13. Bob has quota available: PASS")

    # Watermark
    wm = watermark_output("Hello world", "bob", settings)
    assert "TestCorp" in wm, "Watermark should contain company name"
    assert "bob" in wm, "Watermark should contain username"
    print("14. Output watermarking works: PASS")

    # Custom keyword blocked
    r = screen_input("this is proprietary information", settings)
    assert not r.allowed, "Custom keyword 'proprietary' should be blocked"
    assert r.blocked_reason == PolicyBlockReason.CUSTOM_KEYWORD
    print(f"15. Custom keyword blocked ({r.blocked_reason.value}): PASS")

    # Online gaming blocked
    r = screen_input("let's play fortnite", settings)
    assert not r.allowed, "Online gaming should be blocked in enterprise"
    print("16. Online gaming blocked in enterprise: PASS")

    # Financial trading blocked
    r = screen_input("buy bitcoin on coinbase", settings)
    assert not r.allowed, "Financial trading should be blocked"
    print("17. Financial trading blocked: PASS")

    # Job search allowed (block_job_search=False)
    r = screen_input("search for jobs on indeed", settings)
    assert r.allowed, "Job search should be allowed when block_job_search=False"
    print("18. Job search allowed (HR setting): PASS")

    # Disabled = watermark not added
    s2 = dict(settings)
    s2["mode"] = "disabled"
    wm = watermark_output("Hello", "bob", s2)
    assert wm == "Hello", "Disabled mode should not watermark"
    print("19. Disabled mode = no watermark: PASS")

    print("\nAll expanded enterprise tests PASSED!\n")


def test_child_profiles():
    """Test child profile management."""
    print("=== Child Profile Tests ===\n")
    settings = {"mode": "disabled", "parental": {}, "enterprise": {}}

    add_child_profile("Alice", 8, "child", settings)
    add_child_profile("Bob", 14, "teen", settings)
    assert len(settings["parental"]["child_profiles"]) == 2
    print("1. Added 2 child profiles: PASS")

    switch_child_profile("Alice", settings)
    assert settings["parental"]["active_child_profile"] == "Alice"
    assert settings["parental"]["age_preset"] == "child"
    assert settings["mode"] == "parental"
    print("2. Switched to Alice (child preset): PASS")

    switch_child_profile("Bob", settings)
    assert settings["parental"]["active_child_profile"] == "Bob"
    assert settings["parental"]["age_preset"] == "teen"
    print("3. Switched to Bob (teen preset): PASS")

    print("\nAll child profile tests PASSED!\n")


def test_usage_report():
    """Test usage report generation."""
    print("=== Usage Report Tests ===\n")
    settings = {"mode": "parental", "parental": {"enabled": True}}
    report = generate_usage_report(settings, days=7)
    assert "generated" in report
    assert "total_conversations" in report
    assert "alerts" in report
    assert "daily_breakdown" in report
    assert report["period_days"] == 7
    print("1. Report has required fields: PASS")
    print(f"   Conversations: {report['total_conversations']}, Alerts: {report['alerts']}")
    print("\nUsage report test PASSED!\n")


if __name__ == "__main__":
    print("=" * 70)
    print("COMMAND NEXUS — USAGE POLICY TEST SUITE")
    print("=" * 70)
    print()

    test_smoke()
    test_parental_mode()
    test_enterprise_mode()
    test_custom_mode()
    test_age_presets()
    test_enterprise_presets()
    test_tamper_detection()
    test_password_hashing()
    test_session_time()
    test_capability_and_path_checks()
    test_parental_expanded()
    test_enterprise_expanded()
    test_child_profiles()
    test_usage_report()

    print("=" * 70)
    print("ALL USAGE POLICY TESTS COMPLETE")
    print("=" * 70)
