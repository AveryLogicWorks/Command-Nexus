# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Live conversation test — proves Apex Glaux works like a real intelligence.

Seeds diverse knowledge, then has a multi-turn conversation with
varied topics, follow-ups, emotional context, and knowledge building.
"""

from __future__ import annotations

import json
import os
import time

from portable_apex_glaux import ApexGlauxEngine
from portable_apex_glaux.adapters import DemoHostAdapter
from portable_apex_glaux.core.interfaces import MemoryLevel


def load_founder_key() -> str:
    path = os.path.join(
        r"B:\Documents\GitHub\Command Nexus Secrets",
        "apex_glaux_founder_key.json"
    )
    with open(path, "r") as f:
        data = json.load(f)
    return data["founder_key"]


def seed_knowledge(engine: ApexGlauxEngine, ai_uuid: str):
    """Seed a diverse knowledge base across multiple domains."""
    knowledge = [
        # Geography
        ("The Eiffel Tower is located in Paris, France.",
         ["eiffel", "paris", "france", "geography"], 0.9),
        ("Paris is the capital of France.",
         ["paris", "france", "capital", "geography"], 0.85),
        ("France is a country in Western Europe.",
         ["france", "europe", "geography"], 0.8),
        ("The Eiffel Tower was built in 1889 for the World's Fair.",
         ["eiffel", "history", "paris"], 0.75),
        ("The Eiffel Tower stands 330 meters tall.",
         ["eiffel", "paris", "architecture"], 0.7),

        # Programming
        ("Python is a high-level programming language created by Guido van Rossum.",
         ["python", "programming", "guido"], 0.9),
        ("Python emphasizes code readability and simplicity.",
         ["python", "design", "readability"], 0.75),
        ("Python was first released in 1991.",
         ["python", "history", "programming"], 0.7),
        ("JavaScript is a programming language primarily used for web development.",
         ["javascript", "programming", "web"], 0.85),
        ("JavaScript was created by Brendan Eich in 1995.",
         ["javascript", "history", "programming"], 0.7),

        # AI/ML
        ("Machine learning is a subset of artificial intelligence.",
         ["ml", "ai", "machine_learning"], 0.85),
        ("Deep learning uses neural networks with multiple layers.",
         ["deep_learning", "neural_networks", "ai"], 0.8),
        ("Neural networks are inspired by the human brain's structure.",
         ["neural_networks", "brain", "ai"], 0.7),

        # Science
        ("Water boils at 100 degrees Celsius at sea level.",
         ["water", "boiling", "science", "physics"], 0.85),
        ("The speed of light is approximately 300 million meters per second.",
         ["light", "physics", "science"], 0.8),
        ("Photosynthesis is how plants convert sunlight into energy.",
         ["photosynthesis", "plants", "biology"], 0.8),

        # History
        ("The Roman Empire fell in 476 AD.",
         ["rome", "history", "empire"], 0.8),
        ("World War II ended in 1945.",
         ["wwii", "history", "war"], 0.85),
    ]

    for content, tags, importance in knowledge:
        engine._memory.add(ai_uuid, content, tags=tags, importance=importance,
                          level=MemoryLevel.SEMANTIC)

    engine.index_memories(ai_uuid)
    engine.discover_relations(ai_uuid)
    print(f"[Seeded {len(knowledge)} knowledge entries across 5 domains]\n")


def print_exchange(turn: int, user: str, result, latency: float):
    """Print a conversation exchange in a clean format."""
    print(f"--- Turn {turn} ---")
    print(f"You: {user}")
    print(f"Apex Glaux: {result.text}")
    print(f"   [conf={result.confidence:.2f} mode={result.mode} "
          f"dims={len(result.dimensions_used)} {latency:.0f}ms]")
    print()


def run_conversation():
    print("=" * 70)
    print("  APEX GLAUX(TM) — LIVE CONVERSATION TEST")
    print("  Copyright (c) 2026 Avery Logic Works - All Rights Reserved")
    print("=" * 70)
    print()

    founder_key = load_founder_key()
    engine = ApexGlauxEngine(
        host=DemoHostAdapter(name="Conversation Test Host"),
        founder_key=founder_key,
    )
    engine.authorize("founder_host", license_key=founder_key)

    print(f"Status: {'FOUNDER MODE ACTIVE' if engine.provenance.is_founder else 'AUTHORIZED'}")
    print(f"Engine: {engine.identity_block.split(chr(10))[0]}")
    print()

    ai_uuid = "conv-test-ai"
    seed_knowledge(engine, ai_uuid)

    # Track conversation history
    history: list[dict] = []

    # --- Conversation Turn 1: Direct factual question ---
    q1 = "What is the capital of France?"
    t0 = time.perf_counter()
    r1 = engine.think(ai_uuid, q1, intent="chat", conversation_history=list(history))
    latency1 = (time.perf_counter() - t0) * 1000
    print_exchange(1, q1, r1, latency1)
    history.append({"role": "user", "text": q1})
    history.append({"role": "assistant", "text": r1.text})

    # --- Turn 2: Follow-up (should connect to previous topic) ---
    q2 = "Tell me more about the Eiffel Tower"
    t0 = time.perf_counter()
    r2 = engine.think(ai_uuid, q2, intent="chat", conversation_history=list(history))
    latency2 = (time.perf_counter() - t0) * 1000
    print_exchange(2, q2, r2, latency2)
    history.append({"role": "user", "text": q2})
    history.append({"role": "assistant", "text": r2.text})

    # --- Turn 3: Topic switch — programming ---
    q3 = "Who created Python?"
    t0 = time.perf_counter()
    r3 = engine.think(ai_uuid, q3, intent="chat", conversation_history=list(history))
    latency3 = (time.perf_counter() - t0) * 1000
    print_exchange(3, q3, r3, latency3)
    history.append({"role": "user", "text": q3})
    history.append({"role": "assistant", "text": r3.text})

    # --- Turn 4: Follow-up on programming ---
    q4 = "What about JavaScript? Who made that?"
    t0 = time.perf_counter()
    r4 = engine.think(ai_uuid, q4, intent="chat", conversation_history=list(history))
    latency4 = (time.perf_counter() - t0) * 1000
    print_exchange(4, q4, r4, latency4)
    history.append({"role": "user", "text": q4})
    history.append({"role": "assistant", "text": r4.text})

    # --- Turn 5: Cross-domain question (AI/ML) ---
    q5 = "How does machine learning relate to artificial intelligence?"
    t0 = time.perf_counter()
    r5 = engine.think(ai_uuid, q5, intent="chat", conversation_history=list(history))
    latency5 = (time.perf_counter() - t0) * 1000
    print_exchange(5, q5, r5, latency5)
    history.append({"role": "user", "text": q5})
    history.append({"role": "assistant", "text": r5.text})

    # --- Turn 6: Preference/directive (should be noted, not searched) ---
    q6 = "I prefer concise answers without too much fluff"
    t0 = time.perf_counter()
    r6 = engine.think(ai_uuid, q6, intent="chat", conversation_history=list(history))
    latency6 = (time.perf_counter() - t0) * 1000
    print_exchange(6, q6, r6, latency6)
    history.append({"role": "user", "text": q6})
    history.append({"role": "assistant", "text": r6.text})

    # --- Turn 7: Science question ---
    q7 = "At what temperature does water boil?"
    t0 = time.perf_counter()
    r7 = engine.think(ai_uuid, q7, intent="chat", conversation_history=list(history))
    latency7 = (time.perf_counter() - t0) * 1000
    print_exchange(7, q7, r7, latency7)
    history.append({"role": "user", "text": q7})
    history.append({"role": "assistant", "text": r7.text})

    # --- Turn 8: Unknown topic (should admit no knowledge gracefully) ---
    q8 = "What's the best recipe for chocolate lava cake?"
    t0 = time.perf_counter()
    r8 = engine.think(ai_uuid, q8, intent="chat", conversation_history=list(history))
    latency8 = (time.perf_counter() - t0) * 1000
    print_exchange(8, q8, r8, latency8)
    history.append({"role": "user", "text": q8})
    history.append({"role": "assistant", "text": r8.text})

    # --- Turn 9: Teach it something new ---
    q9 = "Remember that chocolate lava cake is a dessert with a molten chocolate center"
    t0 = time.perf_counter()
    r9 = engine.think(ai_uuid, q9, intent="chat", conversation_history=list(history))
    latency9 = (time.perf_counter() - t0) * 1000
    print_exchange(9, q9, r9, latency9)
    history.append({"role": "user", "text": q9})
    history.append({"role": "assistant", "text": r9.text})

    # --- Turn 10: Ask about what we just taught it ---
    q10 = "What is chocolate lava cake?"
    t0 = time.perf_counter()
    r10 = engine.think(ai_uuid, q10, intent="chat", conversation_history=list(history))
    latency10 = (time.perf_counter() - t0) * 1000
    print_exchange(10, q10, r10, latency10)
    history.append({"role": "user", "text": q10})
    history.append({"role": "assistant", "text": r10.text})

    # --- Summary ---
    print("=" * 70)
    print("  CONVERSATION SUMMARY")
    print("=" * 70)

    stats = engine.get_stats(ai_uuid)
    print(f"  Total memories:     {stats['memories']}")
    print(f"  Relations:          {stats['relations']}")
    print(f"  Cognition states:   {stats['cognition_states']}")
    print(f"  Persona version:    {stats['persona_version']}")
    print()

    # Check quality
    checks = []

    # Turn 1: Should mention Paris
    checks.append(("T1: Answer mentions Paris", "paris" in r1.text.lower()))

    # Turn 2: Should mention Eiffel Tower details, NOT "What is the capital"
    checks.append(("T2: Answer mentions Eiffel", "eiffel" in r2.text.lower()))
    checks.append(("T2: No leaked user query", "what is the capital" not in r2.text.lower()))

    # Turn 3: Should mention Guido van Rossum
    checks.append(("T3: Answer mentions Guido", "guido" in r3.text.lower()))

    # Turn 4: Should mention Brendan Eich / JavaScript
    checks.append(("T4: Answer mentions JavaScript", "javascript" in r4.text.lower()))

    # Turn 5: Should mention ML/AI relationship
    checks.append(("T5: Answer mentions ML/AI", "machine learning" in r5.text.lower() or "artificial intelligence" in r5.text.lower()))

    # Turn 6: Should acknowledge preference
    checks.append(("T6: Preference acknowledged", r6.confidence >= 0.5))

    # Turn 7: Should mention 100 degrees
    checks.append(("T7: Answer mentions 100 degrees", "100" in r7.text))

    # Turn 8: Should admit no knowledge gracefully
    checks.append(("T8: Admits no knowledge", r8.confidence < 0.3))

    # Turn 9: Should accept the teaching
    checks.append(("T9: Accepts new knowledge", r9.confidence >= 0.5))

    # Turn 10: Should recall what was taught
    checks.append(("T10: Recalls taught knowledge", "chocolate" in r10.text.lower() and "molten" in r10.text.lower()))

    passed = 0
    failed = 0
    for name, result in checks:
        status = "PASS" if result else "FAIL"
        if result:
            passed += 1
        else:
            failed += 1
        print(f"  [{status}] {name}")

    print()
    print(f"  Quality checks: {passed} passed, {failed} failed out of {len(checks)}")
    print()

    # Show reversible cognition state
    cog_states = engine.get_cognition_state_summary(ai_uuid)
    print(f"  Reversible Cognition:")
    print(f"    Past Known:      {cog_states['past_known']}")
    print(f"    Last Known Good: {cog_states['last_known_good']}")
    print(f"    New Info:        {cog_states['new_info']}")

    print()
    print("=" * 70)
    if failed == 0:
        print("  RESULT: ALL CHECKS PASSED — Apex Glaux is fully operational")
    else:
        print(f"  RESULT: {failed} check(s) failed — needs attention")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    run_conversation()
