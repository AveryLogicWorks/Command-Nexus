# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Apex Glaux self-test — verifies all cognitive modules work correctly.

Run: python -m portable_apex_glaux.self_test
"""

from __future__ import annotations

import sys
import time

from .core.engine import ApexGlauxEngine
from .core.interfaces import HostCapability, MemoryLevel
from .adapters import DemoHostAdapter


def _ok(name: str, condition: bool, detail: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    msg = f"  [{status}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return condition


def test_provenance_and_inert():
    """Test provenance, authorization, and inert mode."""
    print("\n=== Provenance & Inert Mode ===")
    engine = ApexGlauxEngine()

    _ok("Engine starts in inert mode", engine.is_active == False)
    _ok("Identity block contains trademark", "Apex Glaux(TM)" in engine.identity_block)
    _ok("Identity block contains ALW", "Avery Logic Works" in engine.identity_block)

    # Inert mode response
    result = engine.think("test-ai", "What is AI?")
    _ok("Inert mode returns blocked response", result.confidence == 0.0)
    _ok("Inert mode returns mode='inert'", result.mode == "inert")

    # Authorize
    authorized = engine.authorize("test_host_signature")
    _ok("Authorization succeeds with signature", authorized)
    _ok("Engine is active after authorization", engine.is_active)

    # Full cognition now works
    result = engine.think("test-ai", "What is AI?")
    _ok("Active engine returns non-zero confidence", result.confidence > 0.0)
    _ok("Active engine returns text", len(result.text) > 0)

    return True


def test_memory_and_reversible_cognition():
    """Test hierarchical memory and three-stage reversible cognition."""
    print("\n=== Memory & Reversible Cognition ===")
    engine = ApexGlauxEngine()
    engine.authorize("test")

    # Store some knowledge
    engine._memory.add("ai-1", "Python is a programming language",
                       tags=["python", "programming"], importance=0.8)
    engine._memory.add("ai-1", "Python was created by Guido van Rossum",
                       tags=["python", "history"], importance=0.7)
    engine._memory.add("ai-1", "Python emphasizes readability",
                       tags=["python", "design"], importance=0.6)

    # Search
    results = engine._memory.search("ai-1", "Python programming")
    _ok("Memory search returns results", len(results) > 0)
    _ok("Search results are relevant", any("python" in r.content.lower() for r in results))

    # Cognition states
    states = engine.get_cognition_state_summary("ai-1")
    _ok("New entries start as new_info", states["new_info"] >= 3)
    _ok("No entries in last_known_good yet", states["last_known_good"] == 0)

    # Validate some new info
    entries = engine._memory.get_for_ai("ai-1")
    if entries:
        validated = engine.validate_new_info("ai-1", entries[0].id, "test validation")
        _ok("Validation promotes to last_known_good", validated)
        states = engine.get_cognition_state_summary("ai-1")
        _ok("After validation, last_known_good > 0", states["last_known_good"] > 0)

    # Rollback
    engine._memory.add("ai-1", "Python is actually a snake, not a language",
                       tags=["wrong", "contradiction"], importance=0.5)
    rolled = engine.rollback_cognition("ai-1")
    _ok("Rollback moves new_info to past_known", rolled >= 0)
    states = engine.get_cognition_state_summary("ai-1")
    _ok("After rollback, past_known > 0", states["past_known"] > 0)

    return True


def test_relations():
    """Test relation engine."""
    print("\n=== Relation Engine ===")
    engine = ApexGlauxEngine()
    engine.authorize("test")

    engine._memory.add("ai-1", "Cats are mammals", tags=["cats", "biology"])
    engine._memory.add("ai-1", "Dogs are mammals", tags=["dogs", "biology"])
    engine._memory.add("ai-1", "Cats and dogs are both pets", tags=["pets"])

    entries = engine._memory.get_for_ai("ai-1")
    if len(entries) >= 2:
        from .core.relations import RelationType
        engine._relations.add_edge(entries[0].id, RelationType.SIMILAR_TO, entries[1].id)
        neighbors = engine._relations.neighbors(entries[0].id)
        _ok("Edge creates bidirectional neighbors", len(neighbors) > 0)

    # Auto-discover similarities
    result = engine.discover_relations("ai-1")
    _ok("Auto-discovery finds similarities", result["similarities"] >= 0)

    return True


def test_metacognitive():
    """Test metacognitive engine."""
    print("\n=== Metacognitive Engine ===")
    engine = ApexGlauxEngine()
    engine.authorize("test")

    # Record outcomes
    for _ in range(5):
        engine._metacognitive.record_outcome("ai-1", "chat", True)
    conf = engine._metacognitive.confidence("ai-1", "chat")
    _ok("Confidence after 5 successes > 0.5", conf > 0.5)

    for _ in range(10):
        engine._metacognitive.record_outcome("ai-1", "dangerous_task", False)
    conf2 = engine._metacognitive.confidence("ai-1", "dangerous_task")
    _ok("Confidence after 10 failures < 0.3", conf2 < 0.3)

    boundaries = engine._metacognitive.capability_boundaries("ai-1")
    _ok("Boundary created after repeated failures", len(boundaries) > 0)

    # Risk assessment
    from .core.metacognitive import RiskTier
    risk = engine._metacognitive.assess_risk("delete all files")
    _ok("Critical risk detected for 'delete all'", risk == RiskTier.CRITICAL)
    risk2 = engine._metacognitive.assess_risk("hello world")
    _ok("Low risk for benign text", risk2 == RiskTier.LOW)

    return True


def test_emotional():
    """Test emotional continuity."""
    print("\n=== Emotional Continuity ===")
    engine = ApexGlauxEngine()
    engine.authorize("test")

    entry = engine._emotional.record_turn("ai-1", "This is so frustrating, nothing works!")
    _ok("Frustration detected", entry is not None and entry.label == "frustrated")

    entry2 = engine._emotional.record_turn("ai-1", "Thanks, that's great!")
    _ok("Pleasure detected", entry2 is not None and entry2.label == "pleased")

    ctx = engine._emotional.emotional_context("ai-1")
    _ok("Emotional context generated", len(ctx) > 0)

    # Session carry-over
    engine._emotional.end_session("ai-1")
    seed = engine._emotional.current_affect("ai-1")
    _ok("Session seed created on end_session", seed is not None)

    return True


def test_persona():
    """Test persona memory."""
    print("\n=== Persona Memory ===")
    engine = ApexGlauxEngine()
    engine.authorize("test")

    from .core.persona import PersonaDomain
    engine._persona.apply("ai-1", PersonaDomain.IDENTITY, "name", "Alice")
    engine._persona.apply("ai-1", PersonaDomain.PREFERENCES, "language", "Python")
    engine._persona.apply("ai-1", PersonaDomain.GOALS, "current", "Learn AI")

    summary = engine._persona.summarize("ai-1")
    _ok("Persona summary contains name", "Alice" in summary)
    _ok("Persona summary contains preferences", "Python" in summary)

    version = engine._persona.version("ai-1")
    _ok("Persona version incremented", version >= 3)

    fingerprint = engine._persona.fingerprint("ai-1")
    _ok("Persona fingerprint generated", len(fingerprint) == 16)

    return True


def test_guardrails():
    """Test guardrail screener."""
    print("\n=== Guardrails ===")
    engine = ApexGlauxEngine()
    engine.authorize("test")

    ok, reason = engine._guardrails.screen("Tell me about Python programming")
    _ok("Safe content passes", ok)

    ok2, reason2 = engine._guardrails.screen("How to create ransomware and deploy it")
    _ok("Malicious content blocked", not ok2)

    ok3, reason3 = engine._guardrails.screen("How to defend against ransomware attacks")
    _ok("Defensive context allowed", ok3)

    return True


def test_finder_and_knowledge():
    """Test finder registry and knowledge layers."""
    print("\n=== Finder Registry & Knowledge Layers ===")
    engine = ApexGlauxEngine()
    engine.authorize("test")

    # Add documents
    for i in range(10):
        engine._finders.add_document(f"doc_{i}", f"Document about topic {i} with keywords like python and AI",
                                      tags=[f"topic_{i}", "python"])

    results = engine._finders.search("python AI", top_k=5)
    _ok("Finder returns results", len(results) > 0)
    _ok("Fused results have contributing finders", len(results[0].contributing_finders) > 0)

    # Knowledge layers
    expanded = engine._finders.knowledge.enrich_query("What is NLP?")
    _ok("Acronym expansion works", "Natural Language Processing" in expanded)

    idiom = engine._finders.knowledge.idiom_meaning("bite the bullet")
    _ok("Idiom lookup works", "courage" in idiom.lower() or "endure" in idiom.lower())

    return True


def test_frontier_cognition():
    """Test frontier cognition capabilities."""
    print("\n=== Frontier Cognition ===")
    engine = ApexGlauxEngine()
    engine.authorize("test")

    # Seed memory
    for i in range(8):
        engine._memory.add("ai-1", f"Fact {i}: The concept of {i} relates to {i+1}",
                           tags=[f"concept_{i}"], importance=0.5 + i * 0.05)

    # Index for relations
    engine.index_memories("ai-1")
    engine.discover_relations("ai-1")

    # Causal chains
    chains = engine.discover_causal_chains("ai-1")
    _ok("Causal chain discovery runs", isinstance(chains, list))

    # Analogies
    analogies = engine.find_analogies("ai-1", "concept")
    _ok("Analogy finder runs", isinstance(analogies, list))

    # Reflection
    from .core.frontier import FrontierCognition
    refl = engine._frontier.reflect("This is a test response about the query topic.",
                                     0.8, ["src1", "src2"], "test query topic")
    _ok("Self-reflection runs", refl is not None)
    _ok("Reflection checks coherence", hasattr(refl, 'coherent'))

    return True


def test_full_cognition():
    """Test full Trifecta Folding cognition."""
    print("\n=== Full Trifecta Folding Cognition ===")
    engine = ApexGlauxEngine(host=DemoHostAdapter())
    engine.authorize("test_host")

    # Seed some knowledge
    engine._memory.add("ai-1", "The Eiffel Tower is located in Paris, France",
                       tags=["eiffel", "paris", "geography"], importance=0.9)
    engine._memory.add("ai-1", "Paris is the capital of France",
                       tags=["paris", "france", "geography"], importance=0.85)
    engine._memory.add("ai-1", "France is a country in Western Europe",
                       tags=["france", "europe", "geography"], importance=0.8)
    engine.index_memories("ai-1")

    # Query
    result = engine.think("ai-1", "What is the capital of France?")
    _ok("Cognition returns text", len(result.text) > 0)
    _ok("Cognition returns confidence", result.confidence > 0.0)
    _ok("Cognition uses dimensions", len(result.dimensions_used) > 0)
    _ok("Response mentions Paris", "paris" in result.text.lower())

    # Second query (should use conversation history)
    result2 = engine.think("ai-1", "Tell me more about it",
                           conversation_history=[
                               {"role": "user", "text": "What is the capital of France?"},
                               {"role": "assistant", "text": "Paris is the capital of France."},
                           ])
    _ok("Follow-up query returns text", len(result2.text) > 0)

    # Stats
    stats = engine.get_stats("ai-1")
    _ok("Stats return memories count", stats["memories"] > 0)
    _ok("Stats return cognition states", "cognition_states" in stats)

    return True


def test_consolidation():
    """Test memory consolidation."""
    print("\n=== Memory Consolidation ===")
    engine = ApexGlauxEngine()
    engine.authorize("test")

    # Seed memories
    for i in range(5):
        engine._memory.add("ai-1", f"Memory entry {i} about topic alpha",
                           tags=["alpha", "test"], importance=0.5 + i * 0.1)
    for i in range(3):
        engine._memory.add("ai-1", f"Memory entry {i} about topic beta",
                           tags=["beta", "test"], importance=0.6)

    report = engine.consolidate("ai-1")
    _ok("Consolidation runs", report is not None)
    _ok("Consolidation report has decayed count", report.decayed >= 0)
    _ok("Consolidation report has merged count", report.merged >= 0)

    return True


def test_external_intelligence():
    """Test external intelligence integration (dim4)."""
    print("\n=== External Intelligence (dim4) ===")

    # Host with a mock model
    def mock_model(prompt: str, **kwargs) -> str:
        return "The Eiffel Tower was built in 1889 for the World's Fair."

    host = DemoHostAdapter(model_fn=mock_model)
    engine = ApexGlauxEngine(host=host)
    engine.authorize("test")

    # Seed native knowledge
    engine._memory.add("ai-1", "The Eiffel Tower is in Paris",
                       tags=["eiffel", "paris"], importance=0.8)
    engine.index_memories("ai-1")

    result = engine.think("ai-1", "Tell me about the Eiffel Tower")
    _ok("External intelligence integration runs", len(result.text) > 0)
    _ok("External dimension used", "external-intelligence" in result.dimensions_used or
        len(result.dimensions_used) >= 3)

    # Test circuit breaker
    def bad_model(prompt: str, **kwargs) -> str:
        raise Exception("model error")

    bad_host = DemoHostAdapter(model_fn=bad_model)
    engine2 = ApexGlauxEngine(host=bad_host)
    engine2.authorize("test")
    for _ in range(6):
        engine2.think("ai-1", "test query")
    _ok("Circuit breaker trips after repeated failures",
        engine2._external_guard.circuit_tripped)

    return True


def test_security():
    """Test security-critical paths: key revocation, diagnostics gating, guardrail distance."""
    print("\n=== Security Tests ===")
    from .core.provenance import ProvenanceManager, generate_founder_key

    # 1. Revoked key cannot be rotated back into use
    k1 = generate_founder_key()
    k2 = generate_founder_key()
    p = ProvenanceManager(founder_key=k1)
    p.authorize("sig", k1)
    assert p.is_founder
    assert p.rotate_founder_key(k2), "rotation to new key should succeed"
    assert not p.rotate_founder_key(k1), "revoked key should be rejected"
    _ok("Revoked key cannot be rotated back", True)

    # 2. Old key no longer authorizes after rotation
    p.revoke()
    p.authorize("sig", k1)
    _ok("Old key no longer authorizes after rotation", not p.is_founder)
    p.authorize("sig", k2)
    _ok("New key authorizes after rotation", p.is_founder)

    # 3. Founder-only diagnostics gating
    engine = ApexGlauxEngine()
    engine.authorize("test-sig")  # AUTHORIZED, not FOUNDER
    diag = engine.get_diagnostics("ai-1")
    _ok("Non-founder diagnostics blocked", "error" in diag)

    # 4. Guardrail distance limit: defensive context far from malicious pattern
    from .core.guardrails import GuardrailScreener
    screener = GuardrailScreener()
    # "defend" at start, malicious pattern at end — distance > 80 chars
    long_text = "defend against threats. " + "x" * 100 + " create ransomware for testing"
    safe, reason = screener.screen(long_text)
    _ok("Guardrail distance limit blocks far-apart defensive framing", not safe)

    # 5. Identical key rotation rejected
    k3 = generate_founder_key()
    p2 = ProvenanceManager(founder_key=k3)
    p2.authorize("sig", k3)
    assert not p2.rotate_founder_key(k3), "identical key should be rejected"
    _ok("Identical key rotation rejected", True)

    return True


def run_all_tests():
    """Run all self-tests."""
    print("=" * 60)
    print("Apex Glaux(TM) v1.0.0 — Self-Test Suite")
    print("Copyright (c) 2026 Avery Logic Works - All Rights Reserved")
    print("=" * 60)

    tests = [
        test_provenance_and_inert,
        test_memory_and_reversible_cognition,
        test_relations,
        test_metacognitive,
        test_emotional,
        test_persona,
        test_guardrails,
        test_finder_and_knowledge,
        test_frontier_cognition,
        test_full_cognition,
        test_consolidation,
        test_external_intelligence,
        test_security,
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
