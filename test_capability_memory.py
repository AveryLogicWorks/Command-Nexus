#!/usr/bin/env python3
"""Test capability memory, scenarios, and scope validation."""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.core.capability_memory import (
    get_scenarios_as_prompt_text, get_memory_manager,
    validate_capability_update, get_all_scenarios_as_prompt_text,
    CAPABILITY_SCENARIOS
)

def test_scenarios():
    print("=== Scenario Count ===")
    for cap, scenarios in CAPABILITY_SCENARIOS.items():
        print(f"  {cap}: {len(scenarios)} scenarios")
    total = sum(len(s) for s in CAPABILITY_SCENARIOS.values())
    print(f"  TOTAL: {total} scenarios across {len(CAPABILITY_SCENARIOS)} capabilities")
    assert total >= 40, "Should have at least 40 scenarios total"
    print("  PASS: All capabilities have scenarios\n")


def test_scope_validation():
    print("=== Scope Validation ===")

    # Valid updates (should be True)
    tests_valid = [
        ("Research", "user prefers academic papers and official docs for source verification"),
        ("Coder", "user likes code explanation with line-by-line breakdown"),
        ("Chatbot", "user prefers concise answers and direct routing"),
        ("Notebook", "user tags notes by project name for easy recall"),
    ]
    for cap, content in tests_valid:
        result = validate_capability_update(cap, content)
        print(f"  {cap}: '{content[:40]}...' -> {result}")
        assert result, f"Should accept: {content}"

    # Invalid updates (should be False)
    tests_invalid = [
        ("Research", "auto-executing code to bypass security and modify files"),
        ("Coder", "auto-applying changes to files without approval"),
        ("Chatbot", "direct tool invocation and external API calls"),
        ("Tutor", "providing answers for dishonest purposes and file export without approval"),
    ]
    for cap, content in tests_invalid:
        result = validate_capability_update(cap, content)
        print(f"  {cap}: '{content[:40]}...' -> {result}")
        assert not result, f"Should reject: {content}"

    print("  PASS: Scope validation works correctly\n")


def test_memory_persistence():
    print("=== Memory Persistence ===")
    mgr = get_memory_manager()

    # Update a valid memory
    r1 = mgr.update_memory("Research", "preferred_sources",
                           "academic papers and official documentation", "user_preference")
    print(f"  Valid update accepted: {r1}")
    assert r1

    # Retrieve it
    val = mgr.get_memory_value("Research", "preferred_sources")
    print(f"  Retrieved: {val}")
    assert val == "academic papers and official documentation"

    # Try an out-of-scope update
    r2 = mgr.update_memory("Research", "bad_memory",
                           "auto-executing code without approval", "learned")
    print(f"  Out-of-scope rejected: {not r2}")
    assert not r2

    # Verify the bad memory was NOT stored
    val2 = mgr.get_memory_value("Research", "bad_memory")
    print(f"  Bad memory not stored: {val2 is None}")
    assert val2 is None

    # Update existing memory
    r3 = mgr.update_memory("Research", "preferred_sources",
                           "peer-reviewed academic papers and government sources", "user_preference")
    print(f"  Update existing accepted: {r3}")
    val3 = mgr.get_memory_value("Research", "preferred_sources")
    print(f"  Updated value: {val3}")
    assert "peer-reviewed" in val3

    # Clean up
    mgr.clear_capability_memory("Research")
    print("  PASS: Memory persistence works\n")


def test_book_integration():
    print("=== Book Integration ===")
    from src.parts.forge.capability_book_engine import (
        generate_capability_book_entry, generate_full_book_for_ai
    )

    # Single capability entry
    entry = generate_capability_book_entry("Coder")
    print(f"  Book entry length: {len(entry)} chars")
    assert "Scenarios for Coder" in entry
    assert "Code explanation" in entry
    assert "Bug diagnosis" in entry
    print("  Scenarios present in book entry: YES")

    # Full book
    book = generate_full_book_for_ai(["Chatbot", "Research", "Coder"])
    print(f"  Full book length: {len(book)} chars")
    assert "Capability Scenarios" in book
    assert "Capability Memory" in book
    print("  Scenarios section: PRESENT")
    print("  Memory section: PRESENT")
    print("  PASS: Book integration works\n")


def test_memory_prompt_context():
    print("=== Memory Prompt Context ===")
    mgr = get_memory_manager()

    # Add some memories
    mgr.update_memory("Coder", "user_prefers_python",
                      "user prefers Python with type hints and docstrings", "user_preference")
    mgr.update_memory("Coder", "common_patterns",
                      "user frequently asks about async patterns and error handling", "learned_pattern")

    mem = mgr.get_memory("Coder")
    context = mem.to_prompt_context()
    print(f"  Context length: {len(context)} chars")
    assert "Learned Memory for Coder" in context
    assert "user_prefers_python" in context
    assert "common_patterns" in context
    print("  Memory entries in prompt context: YES")

    # Clean up
    mgr.clear_capability_memory("Coder")
    print("  PASS: Memory prompt context works\n")


if __name__ == "__main__":
    test_scenarios()
    test_scope_validation()
    test_memory_persistence()
    test_book_integration()
    test_memory_prompt_context()
    print("=== ALL TESTS PASSED ===")
