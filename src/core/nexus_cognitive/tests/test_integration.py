"""End-to-end integration: the full cognitive pipeline, mocks only.

user input -> route -> classify/orchestrate -> retrieve memory -> build
prompt -> execute (mock) -> learn from outcome -> consolidate.
"""

from src.core.nexus_cognitive.hierarchical_memory_store import MemoryLevel
from src.core.nexus_cognitive.interfaces import RuntimeResult, RuntimeStatus
from src.core.nexus_cognitive.persona_memory import PersonaDomain, PersonaOp
from src.core.nexus_cognitive.snap_in_adapter import NexusSnapInAdapter

AI = "ai_integration"


def test_full_pipeline_end_to_end():
    nexus = NexusSnapInAdapter()  # all mocks: no model, no network, no API

    # ---- turn 1: user states a personal fact --------------------------
    user_text = "my favorite drink is coffee, remember that"
    routing = nexus.memory_router.route(user_text, AI)
    assert routing.store and routing.importance >= 0.8

    entry = nexus.memory_store.add(AI, user_text, tags=routing.tags,
                                   source="user", importance=routing.importance)
    persona_mut = nexus.persona_memory.apply(
        AI, PersonaDomain.PREFERENCES, "drink", "coffee")
    assert persona_mut.op is PersonaOp.ADD
    nexus.emotional_continuity.record_turn(AI, "no rush, whenever works")

    # ---- turn 2: a task that needs orchestration ----------------------
    task = "search for coffee brewing guides and summarize the best one"
    meta = nexus.metacognitive_engine.get_context(AI, "web.search", task)
    assert meta.effort is not None

    plan = nexus.capability_orchestrator.decompose("", task)
    assert plan.requires_multiple
    assert "web.search" in plan.capabilities and "doc.summarize" in plan.capabilities

    # memory retrieval for prompt building (fused path)
    hits = nexus.search_memories(AI, "coffee")
    assert hits and "coffee" in hits[0].text

    prompt_parts = [
        nexus.compendium.get_truths_for_prompt(AI),
        nexus.persona_memory.summarize(AI),
        nexus.emotional_continuity.emotional_context(AI),
        meta.to_prompt_block(),
        hits[0].text,
    ]
    prompt = "\n".join(p for p in prompt_parts if p)
    assert "coffee" in prompt and "metacognition" in prompt

    # ---- execute (mock) ------------------------------------------------
    result = RuntimeResult(
        status=RuntimeStatus.FAILED,
        title="unexpected captcha wall stopped the search",
        result_text="unexpected captcha wall stopped the search before any guide loaded",
    )

    # ---- learn from outcome -------------------------------------------
    conf_before = nexus.metacognitive_engine.confidence(AI, "web.search")
    nexus.metacognitive_engine.record_outcome(AI, "web.search", success=False)
    assert nexus.metacognitive_engine.confidence(AI, "web.search") < conf_before

    verdict = nexus.experiential_learner.process_mission(
        AI, task, "web.search", result, expected_keywords=["brewing", "guide"])
    assert verdict.wrote
    lesson = nexus.memory_store.get_by_level(AI, MemoryLevel.PROCEDURAL)
    assert len(lesson) == 1

    # ---- consolidation --------------------------------------------------
    nexus.memory_store.add(AI, "coffee contains caffeine and antioxidants",
                           tags=["food", "health"], importance=0.85)
    report = nexus.consolidator.consolidate(AI, prune=False)
    assert report.decayed >= 3
    assert report.promoted >= 1  # high-importance fact -> archival

    # ---- session boundary: affect carries over --------------------------
    nexus.emotional_continuity.end_session(AI)
    seed = nexus.emotional_continuity.current_affect(AI)
    assert seed is not None and "residual" in seed.label

    # ---- revision keeps provenance --------------------------------------
    revised = nexus.memory_store.revise(AI, entry.id,
                                        "my favorite drink is black coffee")
    assert revised.revision == 1
    assert nexus.memory_store.get_history(entry.id)[0].content == user_text


def test_pipeline_isolation_between_ais():
    nexus = NexusSnapInAdapter()
    nexus.memory_store.add("ai_a", "secret of ai_a", tags=["x"])
    nexus.memory_store.add("ai_b", "secret of ai_b", tags=["x"])
    assert nexus.memory_store.search("ai_a", "secret")[0].content == "secret of ai_a"
    assert len(nexus.memory_store.get_for_ai("ai_b")) == 1
    assert nexus.consolidator.consolidate("ai_a", prune=False).decayed == 1
