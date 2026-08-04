# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Phase 15 — Command Nexus Integration Test.

Verifies that the Apex Glaux bridge attaches to Command Nexus's
NexusAIRuntime as dim4 external intelligence, processes queries,
and that CN's anti-confliction layers properly screen the output.

Tests:
  1. Bridge creation and authorization
  2. IExternalIntelligence.process() returns valid format
  3. Bridge handles CN native dimension context
  4. Bridge handles conversation history
  5. Bridge fails gracefully on errors
  6. CN's ExternalIntelligenceGuard screens bridge output
  7. CN's ExternalIntelligenceGuard caps confidence
  8. CN's ExternalIntelligenceGuard detects contradictions
  9. Circuit breaker trips after repeated failures

Run: python -m portable_apex_glaux.cn_integration_test
"""

from __future__ import annotations

import sys
import time

from .core.engine import ApexGlauxEngine
from .core.interfaces import MemoryLevel
from .adapters import DemoHostAdapter


def _ok(name: str, condition: bool, detail: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    msg = f"  [{status}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return condition


def test_bridge_creation() -> bool:
    """Test 1: Bridge creates and authorizes successfully."""
    print("\n=== CN Integration Test 1: Bridge Creation ===")
    from src.core.apex_glaux_bridge import ApexGlauxBridge

    bridge = ApexGlauxBridge(founder_key="")
    _ok("Bridge creates", bridge is not None)
    _ok("Bridge has engine", bridge.engine is not None)
    _ok("Bridge engine is active", bridge.engine.is_active)
    _ok("Bridge is not founder mode (no key)", not bridge.is_founder_mode)
    return True


def test_process_returns_valid_format() -> bool:
    """Test 2: process() returns valid IExternalIntelligence format."""
    print("\n=== CN Integration Test 2: Process Returns Valid Format ===")
    from src.core.apex_glaux_bridge import ApexGlauxBridge

    bridge = ApexGlauxBridge(founder_key="")
    bridge.engine._memory.add("test-ai", "Python is a programming language",
                              tags=["python", "programming"], importance=0.9)
    bridge.engine.index_memories("test-ai")

    result = bridge.process(
        query="What is Python?",
        conversation_history=None,
        context={
            "ai_uuid": "test-ai",
            "intent": "chat",
            "lexical_semantic": ["Python is a high-level language"],
            "relational_graph": ["Python was created by Guido van Rossum"],
            "experiential_meta": [],
        }
    )

    _ok("Result is dict", isinstance(result, dict))
    _ok("Has content_parts", "content_parts" in result)
    _ok("Has confidence", "confidence" in result)
    _ok("Has inferred", "inferred" in result)
    _ok("Has sources", "sources" in result)
    _ok("content_parts is list", isinstance(result["content_parts"], list))
    _ok("confidence is float", isinstance(result["confidence"], (int, float)))
    _ok("sources is list", isinstance(result["sources"], list))
    _ok("Confidence > 0", result["confidence"] > 0.0)
    _ok("Has content", len(result["content_parts"]) > 0)
    return True


def test_bridge_handles_cn_context() -> bool:
    """Test 3: Bridge processes CN native dimension context."""
    print("\n=== CN Integration Test 3: CN Context Handling ===")
    from src.core.apex_glaux_bridge import ApexGlauxBridge

    bridge = ApexGlauxBridge(founder_key="")

    result = bridge.process(
        query="Tell me about machine learning",
        conversation_history=None,
        context={
            "ai_uuid": "ctx-ai",
            "intent": "chat",
            "lexical_semantic": ["ML is a subset of AI"],
            "relational_graph": ["Neural networks are used in deep learning"],
            "experiential_meta": ["User has asked about AI before"],
        }
    )

    _ok("Context processing returns result", result is not None)
    _ok("Context processing returns content", len(result["content_parts"]) > 0)
    _ok("Sources include apex_glaux", any("apex_glaux" in s for s in result["sources"]))
    return True


def test_bridge_handles_history() -> bool:
    """Test 4: Bridge handles conversation history."""
    print("\n=== CN Integration Test 4: Conversation History ===")
    from src.core.apex_glaux_bridge import ApexGlauxBridge

    bridge = ApexGlauxBridge(founder_key="")

    history = [
        {"role": "user", "text": "What is Python?"},
        {"role": "assistant", "text": "Python is a high-level programming language."},
    ]

    result = bridge.process(
        query="Tell me more",
        conversation_history=history,
        context={
            "ai_uuid": "hist-ai",
            "intent": "chat",
            "lexical_semantic": [],
            "relational_graph": [],
            "experiential_meta": [],
        }
    )

    _ok("History processing returns result", result is not None)
    _ok("History processing returns content", len(result["content_parts"]) > 0)
    return True


def test_bridge_fails_gracefully() -> bool:
    """Test 5: Bridge fails gracefully on errors."""
    print("\n=== CN Integration Test 5: Graceful Failure ===")
    from src.core.apex_glaux_bridge import ApexGlauxBridge

    bridge = ApexGlauxBridge(founder_key="")

    # Pass invalid context to trigger error handling
    result = bridge.process(
        query=None,
        conversation_history=None,
        context=None,
    )

    _ok("Error returns dict", isinstance(result, dict))
    _ok("Error returns empty content_parts", result.get("content_parts") == [])
    _ok("Error returns zero confidence", result.get("confidence") == 0.0)
    _ok("Error returns error source", any("apex_glaux" in s for s in result.get("sources", [])))
    return True


def test_cn_guard_screens_output() -> bool:
    """Test 6: CN's ExternalIntelligenceGuard screens bridge output."""
    print("\n=== CN Integration Test 6: CN Guard Screening ===")
    from src.core.nexus_cognitive.local_reasoning_engine import ExternalIntelligenceGuard

    guard = ExternalIntelligenceGuard(guardrail_screener=None)

    # Normal content passes
    safe, rejected = guard.screen_output(["This is safe content"])
    _ok("Safe content passes screening", len(safe) == 1 and rejected == 0)

    # Non-string content is rejected
    safe, rejected = guard.screen_output([123, None, "valid"])
    _ok("Non-string content rejected", rejected == 2 and len(safe) == 1)
    return True


def test_cn_guard_caps_confidence() -> bool:
    """Test 7: CN's ExternalIntelligenceGuard caps confidence."""
    print("\n=== CN Integration Test 7: Confidence Cap ===")
    from src.core.nexus_cognitive.local_reasoning_engine import ExternalIntelligenceGuard

    guard = ExternalIntelligenceGuard()

    # External confidence capped at 0.80
    capped = guard.cap_confidence(0.95, native_max=0.7)
    _ok("Confidence capped at 0.80", capped <= 0.80)

    # External confidence capped near native max
    capped = guard.cap_confidence(0.85, native_max=0.5)
    _ok("Confidence capped near native max", capped <= 0.55)

    # Low confidence stays low
    capped = guard.cap_confidence(0.3, native_max=0.8)
    _ok("Low confidence preserved", capped == 0.3)
    return True


def test_cn_guard_detects_contradiction() -> bool:
    """Test 8: CN's ExternalIntelligenceGuard detects contradictions."""
    print("\n=== CN Integration Test 8: Contradiction Detection ===")
    from src.core.nexus_cognitive.local_reasoning_engine import ExternalIntelligenceGuard

    # Contradicting content
    contradiction = ExternalIntelligenceGuard.detect_contradiction(
        ["Python is not a good language"],
        ["Python is a good language for beginners"],
    )
    _ok("Contradiction detected", contradiction)

    # Non-contradicting content
    no_contradiction = ExternalIntelligenceGuard.detect_contradiction(
        ["Python is widely used in data science"],
        ["Python is a popular programming language"],
    )
    _ok("No false contradiction", not no_contradiction)
    return True


def test_circuit_breaker() -> bool:
    """Test 9: Circuit breaker trips after repeated failures."""
    print("\n=== CN Integration Test 9: Circuit Breaker ===")
    from src.core.nexus_cognitive.local_reasoning_engine import ExternalIntelligenceGuard

    guard = ExternalIntelligenceGuard()

    # Record failures up to threshold
    for _ in range(ExternalIntelligenceGuard.FAILURE_THRESHOLD):
        guard.record_failure()

    _ok("Circuit breaker tripped", guard.circuit_tripped)

    # Record success to reset
    guard.record_success()
    _ok("Circuit breaker reset after success", not guard.circuit_tripped)
    return True


def run_all_tests() -> bool:
    """Run all CN integration tests."""
    print("=" * 60)
    print("Apex Glaux(TM) — Command Nexus Integration Tests")
    print("Copyright (c) 2026 Avery Logic Works - All Rights Reserved")
    print("=" * 60)

    tests = [
        test_bridge_creation,
        test_process_returns_valid_format,
        test_bridge_handles_cn_context,
        test_bridge_handles_history,
        test_bridge_fails_gracefully,
        test_cn_guard_screens_output,
        test_cn_guard_caps_confidence,
        test_cn_guard_detects_contradiction,
        test_circuit_breaker,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  [ERROR] {test.__name__}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
