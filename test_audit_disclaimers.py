# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""Stress test for three-tier audit and capability disclaimers."""
import sys
import traceback

passed = 0
failed = 0
failures = []

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
        failures.append((name, detail))

# ─── Three-Tier Audit Tests ───────────────────────────────────────────────────
try:
    from src.core.three_tier_audit import (
        ThreeTierAuditLogger, AuditTier, AuditCategory, AuditEntry
    )

    # Test 1: Basic logging
    audit = ThreeTierAuditLogger()
    audit.log_past(category=AuditCategory.RESEARCH, action="test research", source="Brave")
    audit.log_present(category=AuditCategory.MODEL_CALL, action="calling model")
    audit.log_future(category=AuditCategory.CAPABILITY, action="will do X")
    check("audit_basic_logging", len(audit._entries) == 3, f"Expected 3 entries, got {len(audit._entries)}")

    # Test 2: Tier filtering
    past = audit.get_past_actions()
    present = audit.get_present_actions()
    future = audit.get_future_actions()
    check("audit_past_filter", len(past) == 1, f"Expected 1 past, got {len(past)}")
    check("audit_present_filter", len(present) == 1, f"Expected 1 present, got {len(present)}")
    check("audit_future_filter", len(future) == 1, f"Expected 1 future, got {len(future)}")

    # Test 3: Category filtering
    research = audit.get_entries(category=AuditCategory.RESEARCH)
    check("audit_category_filter", len(research) == 1, f"Expected 1 research, got {len(research)}")

    # Test 4: Summary
    summary = audit.get_summary()
    check("audit_summary_past", summary["past_count"] == 1)
    check("audit_summary_present", summary["present_count"] == 1)
    check("audit_summary_future", summary["future_count"] == 1)
    check("audit_summary_research", summary["research_done"] == 1)

    # Test 5: Format for user
    text = audit.format_summary_for_user()
    check("audit_format_has_past", "PAST" in text)
    check("audit_format_has_present", "PRESENT" in text)
    check("audit_format_has_future", "FUTURE" in text)

    # Test 6: Local-only warning
    audit2 = ThreeTierAuditLogger()
    audit2.log_past(category=AuditCategory.LOCAL_RESPONSE, action="local answer 1")
    audit2.log_past(category=AuditCategory.LOCAL_RESPONSE, action="local answer 2")
    text2 = audit2.format_summary_for_user()
    check("audit_local_warning", "without doing" in text2 or "no research" in text2.lower(),
          f"Expected warning about no research, got: {text2}")

    # Test 7: Tier format
    tier_text = audit.format_tier_for_user(AuditTier.PAST)
    check("audit_tier_format", "PAST ACTIONS" in tier_text)

    # Test 8: Clear
    audit.clear()
    check("audit_clear", len(audit._entries) == 0)

    # Test 9: Capability filtering
    audit3 = ThreeTierAuditLogger()
    audit3.log_past(category=AuditCategory.CAPABILITY, action="test", capability="Research")
    audit3.log_past(category=AuditCategory.CAPABILITY, action="test2", capability="Coder")
    caps = audit3.get_entries(capability="Research")
    check("audit_cap_filter", len(caps) == 1, f"Expected 1 Research, got {len(caps)}")

    # Test 10: Evidence field
    audit4 = ThreeTierAuditLogger()
    audit4.log_past(category=AuditCategory.SOURCE_CITATION, action="cited", evidence="http://example.com")
    entries = audit4.get_past_actions()
    check("audit_evidence", entries[0].evidence == "http://example.com")

    print("Three-Tier Audit: ALL TESTS PASSED")
except Exception as e:
    failed += 1
    failures.append(("audit_exception", traceback.format_exc()))
    print(f"Three-Tier Audit: EXCEPTION: {e}")

# ─── Capability Disclaimers Tests ──────────────────────────────────────────────
try:
    from src.core.capability_disclaimers import (
        show_capability_disclaimer, GUARDED_CAPABILITIES,
        is_disclaimer_acknowledged, reset_session_acknowledgments,
        _build_disclaimer_text, LLM_ACCURACY_WARNING, NON_LIABILITY_NOTICE,
        CAPABILITY_DISCLAIMERS,
    )

    # Test 1: All 81 guarded capabilities have disclaimers
    check("disclaimer_count", len(CAPABILITY_DISCLAIMERS) == 81,
          f"Expected 81, got {len(CAPABILITY_DISCLAIMERS)}")

    # Test 2: LLM accuracy warning present
    check("disclaimer_llm_warning", "AI can get things wrong" in LLM_ACCURACY_WARNING)

    # Test 3: Non-liability notice present
    check("disclaimer_non_liability", "not liable" in NON_LIABILITY_NOTICE.lower())

    # Test 4: Each capability has unique disclaimer text
    texts = set()
    for cap in GUARDED_CAPABILITIES:
        t = _build_disclaimer_text(cap)
        texts.add(t)
    check("disclaimer_unique", len(texts) == 81, f"Expected 81 unique texts, got {len(texts)}")

    # Test 5: Each disclaimer mentions the capability name
    for cap in GUARDED_CAPABILITIES:
        t = _build_disclaimer_text(cap)
        check(f"disclaimer_mentions_{cap}", cap.upper() in t.upper(),
              f"{cap} not mentioned in its disclaimer")

    # Test 6: Each disclaimer has the LLM warning
    for cap in GUARDED_CAPABILITIES:
        t = _build_disclaimer_text(cap)
        check(f"disclaimer_has_llm_warn_{cap}", "AI can get things wrong" in t,
              f"{cap} missing LLM warning")

    # Test 7: Each disclaimer has non-liability
    for cap in GUARDED_CAPABILITIES:
        t = _build_disclaimer_text(cap)
        check(f"disclaimer_has_liability_{cap}", "not liable" in t.lower(),
              f"{cap} missing non-liability notice")

    # Test 8: Each disclaimer mentions audit system
    for cap in GUARDED_CAPABILITIES:
        t = _build_disclaimer_text(cap)
        check(f"disclaimer_has_audit_{cap}", "audit" in t.lower(),
              f"{cap} missing audit system mention")

    # Test 9: Unguarded capability returns True (no disclaimer needed)
    reset_session_acknowledgments()
    check("disclaimer_unguarded", "Chatbot" not in GUARDED_CAPABILITIES)

    # Test 10: Session acknowledgment tracking
    reset_session_acknowledgments()
    check("disclaimer_reset", not is_disclaimer_acknowledged("Security Auditor"))

    print("Capability Disclaimers: ALL TESTS PASSED")
except Exception as e:
    failed += 1
    failures.append(("disclaimer_exception", traceback.format_exc()))
    print(f"Capability Disclaimers: EXCEPTION: {e}")

# ─── Temperature Override Tests ────────────────────────────────────────────────
try:
    from src.core.nexus_ai_runtime import NexusAIRuntime
    from src.core.backend_manager import BackendManager

    # Test 1: Runtime has _HIGH_RISK_INTENTS
    r = NexusAIRuntime()
    check("temp_has_high_risk", hasattr(r, "_HIGH_RISK_INTENTS"))
    check("temp_high_risk_count", len(r._HIGH_RISK_INTENTS) == 14,
          f"Expected 14 high-risk intents, got {len(r._HIGH_RISK_INTENTS)}")

    # Test 2: All expected intents present
    expected = {"Legal Document Reviewer", "Medical Researcher", "Financial Gainer", "Security Auditor", "Code Reviewer",
                "API Integrator", "Database Manager", "DevOps Assistant", "Fact Checker", "Patent Researcher",
                "Personal Finance Manager", "Privacy Compliance Checker", "Script Writer", "Statistical Modeler"}
    check("temp_intents_match", r._HIGH_RISK_INTENTS == expected,
          f"Expected {expected}, got {r._HIGH_RISK_INTENTS}")

    # Test 3: _current_temperature starts as None
    check("temp_init_none", r._current_temperature is None)

    # Test 4: BackendManager.call_model accepts temperature parameter
    import inspect
    sig = inspect.signature(BackendManager.call_model)
    check("temp_backend_param", "temperature" in sig.parameters,
          "BackendManager.call_model missing temperature parameter")

    # Test 5: _call_builtin accepts temperature
    sig2 = inspect.signature(BackendManager._call_builtin)
    check("temp_builtin_param", "temperature" in sig2.parameters)

    # Test 6: _call_openai accepts temperature
    sig3 = inspect.signature(BackendManager._call_openai)
    check("temp_openai_param", "temperature" in sig3.parameters)

    # Test 7: _call_ollama_compatible accepts temperature
    sig4 = inspect.signature(BackendManager._call_ollama_compatible)
    check("temp_ollama_param", "temperature" in sig4.parameters)

    # Test 8: _call_model accepts temperature
    sig5 = inspect.signature(NexusAIRuntime._call_model)
    check("temp_runtime_param", "temperature" in sig5.parameters)

    print("Temperature Override: ALL TESTS PASSED")
except Exception as e:
    failed += 1
    failures.append(("temp_exception", traceback.format_exc()))
    print(f"Temperature Override: EXCEPTION: {e}")

# ─── Results ───────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"STRESS TEST RESULTS: {passed} PASSED, {failed} FAILED")
if failures:
    print(f"\nFAILURES ({len(failures)}):")
    for name, detail in failures:
        print(f"  [{name}] {detail[:200]}")
else:
    print("ALL TESTS PASSED")
print(f"{'='*60}")
sys.exit(1 if failed else 0)
