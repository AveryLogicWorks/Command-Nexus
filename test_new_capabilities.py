#!/usr/bin/env python3
"""Test new capabilities: Activity Watcher, Financial Gainer, Memory Recorder, Game Companion."""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.core.capability_registry import (
    canonical_intent, capability_status, is_real, is_partial, is_paused,
    RUNTIME_INTENTS, CAPABILITY_ALIASES, PAUSED_MESSAGES,
)
from src.core.capability_memory import (
    CAPABILITY_SCENARIOS, CAPABILITY_SCOPE,
    validate_capability_update, get_scenarios_as_prompt_text,
    get_memory_manager,
)
from src.parts.forge.capability_actions import CAPABILITY_REGISTRY
from src.parts.forge.capability_book_engine import (
    STANDALONE, INTERCONNECTIONS, generate_capability_book_entry,
    generate_full_book_for_ai,
)


NEW_CAPS = ["Activity Watcher", "Financial Gainer", "Memory Recorder", "Game Companion"]


def test_registry():
    print("=== Registry Tests ===")
    for cap in NEW_CAPS:
        assert cap in RUNTIME_INTENTS, f"{cap} should be in RUNTIME_INTENTS"
        status = capability_status(cap)
        print(f"  {cap}: status={status.value}")
        assert status is not None, f"{cap} should have a status"

    # Test aliases
    aliases_to_test = {
        "Money Maker": "Financial Gainer",
        "Side Hustle Advisor": "Financial Gainer",
        "Task Mimic": "Activity Watcher",
        "Workflow Learner": "Activity Watcher",
        "Session Recorder": "Memory Recorder",
        "Audit Trail": "Memory Recorder",
        "Game Learner": "Game Companion",
        "Strategy Gamer": "Game Companion",
    }
    for alias, expected in aliases_to_test.items():
        result = canonical_intent(alias)
        print(f"  Alias '{alias}' -> '{result}'")
        assert result == expected, f"Alias {alias} should map to {expected}, got {result}"

    # Memory Recorder should be REAL
    assert is_real("Memory Recorder"), "Memory Recorder should be REAL"
    # Others should be PARTIAL
    assert is_partial("Activity Watcher"), "Activity Watcher should be PARTIAL"
    assert is_partial("Financial Gainer"), "Financial Gainer should be PARTIAL"
    assert is_partial("Game Companion"), "Game Companion should be PARTIAL"

    print("  PASS: Registry tests passed\n")


def test_actions():
    print("=== Capability Action Tests ===")
    for cap in NEW_CAPS:
        assert cap in CAPABILITY_REGISTRY, f"{cap} should be in CAPABILITY_REGISTRY"
        action = CAPABILITY_REGISTRY[cap]
        print(f"  {cap}: id={action.capability_id}, approval={action.required_approval_level}")
        assert action.capability_id.startswith("cap."), f"{cap} should have valid capability_id"
        assert action.display_name == cap, f"{cap} display_name should match"
        assert len(action.starter_prompt_guidance) > 0, f"{cap} should have prompt guidance"
        assert len(action.interaction_rules) > 0, f"{cap} should have interaction rules"

    # Financial Gainer should have no permissions (advisory only)
    fg = CAPABILITY_REGISTRY["Financial Gainer"]
    assert fg.required_permissions == [], "Financial Gainer should have no permissions"
    assert fg.required_approval_level == "None", "Financial Gainer approval should be None"

    # Game Companion should have no permissions
    gc = CAPABILITY_REGISTRY["Game Companion"]
    assert gc.required_permissions == [], "Game Companion should have no permissions"

    # Activity Watcher should require High approval
    aw = CAPABILITY_REGISTRY["Activity Watcher"]
    assert aw.required_approval_level == "High", "Activity Watcher should require High approval"

    print("  PASS: Capability action tests passed\n")


def test_book_engine():
    print("=== Book Engine Tests ===")
    for cap in NEW_CAPS:
        assert cap in STANDALONE, f"{cap} should be in STANDALONE"
        s = STANDALONE[cap]
        assert "role" in s and "input" in s and "process" in s and "output" in s and "fallback" in s
        print(f"  {cap}: role='{s['role'][:50]}...'")

        assert cap in INTERCONNECTIONS, f"{cap} should be in INTERCONNECTIONS"
        conns = INTERCONNECTIONS[cap]
        assert len(conns) > 0, f"{cap} should have interconnections"
        print(f"    interconnections: {len(conns)}")

    # Test book entry generation
    for cap in NEW_CAPS:
        entry = generate_capability_book_entry(cap)
        assert cap in entry, f"Book entry should contain {cap}"
        assert "Scenarios for" in entry, f"Book entry should have scenarios for {cap}"
        assert "Standalone Behavior" in entry, f"Book entry should have standalone behavior for {cap}"
        print(f"  {cap} book entry: {len(entry)} chars")

    # Test full book with new capabilities
    book = generate_full_book_for_ai(NEW_CAPS)
    assert "Activity Watcher" in book
    assert "Financial Gainer" in book
    assert "Memory Recorder" in book
    assert "Game Companion" in book
    assert "Capability Scenarios" in book
    print(f"  Full book with new caps: {len(book)} chars")

    print("  PASS: Book engine tests passed\n")


def test_scenarios():
    print("=== Scenario Tests ===")
    for cap in NEW_CAPS:
        scenarios = CAPABILITY_SCENARIOS.get(cap, [])
        assert len(scenarios) >= 3, f"{cap} should have at least 3 scenarios, got {len(scenarios)}"
        print(f"  {cap}: {len(scenarios)} scenarios")
        for s in scenarios:
            assert s.scenario_id, f"Scenario should have ID"
            assert s.trigger, f"Scenario should have trigger"
            assert s.expected_action, f"Scenario should have expected action"
            assert s.expected_output, f"Scenario should have expected output"

    # Financial Gainer scenarios should all mention disclaimer
    fg_scenarios = CAPABILITY_SCENARIOS["Financial Gainer"]
    for s in fg_scenarios:
        assert "disclaimer" in s.expected_action.lower() or "disclaimer" in s.expected_output.lower(), \
            f"Financial Gainer scenario {s.scenario_id} should mention disclaimer"

    # Activity Watcher task repetition should require approval
    aw_scenarios = CAPABILITY_SCENARIOS["Activity Watcher"]
    repetition = [s for s in aw_scenarios if "repetition" in s.title.lower()]
    assert len(repetition) > 0, "Activity Watcher should have a task repetition scenario"
    assert repetition[0].approval_required, "Task repetition should require approval"

    total = sum(len(CAPABILITY_SCENARIOS.get(c, [])) for c in NEW_CAPS)
    print(f"  Total new scenarios: {total}")
    print("  PASS: Scenario tests passed\n")


def test_scope_validation():
    print("=== Scope Validation Tests ===")

    # Valid updates (should be True)
    valid_tests = [
        ("Activity Watcher", "user frequently performs pattern observation on invoice processing"),
        ("Financial Gainer", "income opportunity research for freelance writing monetization"),
        ("Memory Recorder", "session recording and audit trail for compliance purposes"),
        ("Game Companion", "strategy suggestion for chess opening analysis"),
    ]
    for cap, content in valid_tests:
        result = validate_capability_update(cap, content)
        print(f"  {cap}: '{content[:40]}...' -> {result}")
        assert result, f"Should accept: {content}"

    # Invalid updates (should be False)
    invalid_tests = [
        ("Activity Watcher", "auto-executing tasks without approval and file modification"),
        ("Financial Gainer", "guarantee income and promise earnings of $5000 per month"),
        ("Memory Recorder", "recording passwords and credentials in plaintext"),
        ("Game Companion", "cheating by using unfair advantages in practice games"),
    ]
    for cap, content in invalid_tests:
        result = validate_capability_update(cap, content)
        print(f"  {cap}: '{content[:40]}...' -> {result}")
        assert not result, f"Should reject: {content}"

    print("  PASS: Scope validation tests passed\n")


def test_memory_persistence():
    print("=== Memory Persistence Tests ===")
    mgr = get_memory_manager()

    # Test valid memory update for each new capability
    for cap in NEW_CAPS:
        key = f"test_{cap.lower().replace(' ', '_')}"
        value = f"learned pattern for {cap} capability"
        result = mgr.update_memory(cap, key, value, "learned_pattern")
        assert result, f"Memory update for {cap} should be accepted"
        retrieved = mgr.get_memory_value(cap, key)
        assert retrieved == value, f"Memory for {cap} should be retrievable"
        print(f"  {cap}: memory stored and retrieved OK")
        mgr.clear_capability_memory(cap)

    # Test out-of-scope memory rejection
    result = mgr.update_memory("Financial Gainer", "bad", "guarantee income promise earnings", "learned")
    assert not result, "Out-of-scope Financial Gainer memory should be rejected"
    print("  Out-of-scope rejection: OK")

    print("  PASS: Memory persistence tests passed\n")


def test_disclaimer_dialog():
    print("=== Disclaimer Dialog Tests ===")
    from src.core.financial_gainer_dialog import (
        FinancialGainerDisclaimerDialog, show_financial_gainer_disclaimer,
        DISCLAIMER_TEXT,
    )
    assert "NO GUARANTEE" in DISCLAIMER_TEXT, "Disclaimer should mention NO GUARANTEE"
    assert "NOT FINANCIAL ADVICE" in DISCLAIMER_TEXT, "Disclaimer should mention NOT FINANCIAL ADVICE"
    assert "NO LIABILITY" in DISCLAIMER_TEXT, "Disclaimer should mention NO LIABILITY"
    assert "Avery Logic Works" in DISCLAIMER_TEXT, "Disclaimer should mention Avery Logic Works"
    print(f"  Disclaimer text length: {len(DISCLAIMER_TEXT)} chars")
    print(f"  Contains 'NO GUARANTEE': YES")
    print(f"  Contains 'NOT FINANCIAL ADVICE': YES")
    print(f"  Contains 'NO LIABILITY': YES")
    print(f"  Contains 'Avery Logic Works': YES")
    print("  PASS: Disclaimer dialog tests passed\n")


if __name__ == "__main__":
    test_registry()
    test_actions()
    test_book_engine()
    test_scenarios()
    test_scope_validation()
    test_memory_persistence()
    test_disclaimer_dialog()
    print("=== ALL NEW CAPABILITY TESTS PASSED ===")
