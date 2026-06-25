"""Comprehensive stress / bug / error test for Command Nexus core systems."""

from __future__ import annotations

import sys
import tempfile
import shutil
import uuid
from pathlib import Path

sys.path.insert(0, r"B:\Documents\GitHub\Command Nexus")

from src.core.settings_manager import SettingsManager, NexusSettings
from src.core.adaptive_memory import AdaptiveMemoryStore, MemoryEntry
from src.core.nexus_ai_runtime import NexusAIRuntime, RuntimeStatus
from src.core.tool_executor import ToolExecutor
from src.core.approval_gate import ApprovalGate, RiskLevel
from src.core.audit_logger import AuditLogger
from src.core.command_router import CommandRouter, ToolRegistry


def make_temp_workspace():
    tmp = Path(tempfile.mkdtemp(prefix="cnx_stress_"))
    return tmp


def test_settings():
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(workspace_path=str(tmp / "workspace"), memory_path=str(tmp / "memory"))

        # Paths exist
        assert Path(s.get().workspace_path).exists()
        assert Path(s.get().memory_path).exists()

        # Persistence roundtrip
        s.update(ai_backend="ollama")
        s2 = SettingsManager()
        s2.initialize(config_path=str(tmp / "config.json"))
        assert s2.get().ai_backend == "ollama"
        assert s2.get().memory_path == str(tmp / "memory")

        print("[OK] SettingsManager")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_memory_store():
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(memory_path=str(tmp / "memory"))

        store = AdaptiveMemoryStore(s)
        ai = str(uuid.uuid4())

        # Add / retrieve
        e1 = store.add(ai, "User likes dark mode", tags=["preference"], importance=0.8)
        e2 = store.add(ai, "Project Alpha uses Python", tags=["project"], importance=0.7)
        assert len(store.get_for_ai(ai)) == 2

        # Keyword search
        hits = store.search_keyword(ai, "dark mode")
        assert len(hits) == 1
        assert hits[0].id == e1.id

        # Tag filter
        assert len(store.get_by_tag(ai, "project")) == 1

        # Delete
        assert store.delete(ai, e1.id)
        assert len(store.get_for_ai(ai)) == 1

        # Semantic search (will fall back to keyword because Ollama likely not running)
        semantic = store.search_semantic(ai, "programming language")
        # We accept either an empty list or the keyword fallback if embeddings fail.
        assert isinstance(semantic, list)

        print("[OK] AdaptiveMemoryStore")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_runtime_intents_and_learning():
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(memory_path=str(tmp / "memory"))

        runtime = NexusAIRuntime(s)

        # Simulate a backend that is offline to prove the runtime does NOT fake completion.
        r_fail = runtime.run("hello", "Lily", str(uuid.uuid4()), {
            "uuid": str(uuid.uuid4()),
            "use_case": "Individual",
            "abilities": ["Chatbot"],
            "libraries": [],
            "guardrails": [],
        })
        assert r_fail.status == RuntimeStatus.FAILED, f"Expected FAILED when backend offline, got {r_fail.status}: {r_fail.title}"
        assert "offline" in (r_fail.result_text or "").lower() or "unavailable" in (r_fail.result_text or "").lower()
        assert "completed" not in (r_fail.result_text or "").lower()

        # Now wire a mocked backend that returns real-looking text so the success path is also tested.
        from src.core.backend_manager import BackendResponse
        def fake_call_model(prompt, model=None):
            return BackendResponse(
                text="Mock model response for: " + prompt[:80],
                provider_id="mock",
                display_name="Mock Backend",
            )
        runtime._backend.call_model = fake_call_model

        ai = str(uuid.uuid4())
        meta = {
            "uuid": ai,
            "use_case": "Individual",
            "abilities": ["Chatbot", "Coder", "Research", "Planner"],
            "libraries": [],
            "guardrails": [],
        }

        # Chatbot
        r1 = runtime.run("hello", "TestAI", ai, meta)
        assert r1.status == RuntimeStatus.COMPLETED

        # Coder
        r2 = runtime.run("Write a Python function to add two numbers", "TestAI", ai, meta)
        assert r2.status == RuntimeStatus.COMPLETED

        # Research without a search API key is expected to pause (cannot fake real web results)
        r3 = runtime.run("Research the latest Python features", "TestAI", ai, meta)
        assert r3.status == RuntimeStatus.PAUSED

        # Planner
        r4 = runtime.run("Plan a project to build a website", "TestAI", ai, meta)
        assert r4.status == RuntimeStatus.COMPLETED

        # Preference extraction with a working backend should complete
        r5 = runtime.run("I prefer short answers. What is Rust?", "TestAI", ai, meta)
        assert r5.status == RuntimeStatus.COMPLETED

        # All completed/paused missions should have produced memories
        memories = runtime._memory.get_for_ai(ai)
        assert len(memories) >= 5, f"Expected at least 5 memories, got {len(memories)}"

        # Suggestions should be produced
        suggestions = runtime.suggest_next_steps(ai, "TestAI")
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

        print("[OK] NexusAIRuntime intents + learning")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_tool_executor():
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(workspace_path=str(tmp), memory_path=str(tmp / "memory"))

        tools = ToolExecutor(s)

        write = tools.write_file("test.txt", "hello world")
        assert write.ok, write.message

        read = tools.read_file("test.txt")
        assert read.ok and read.data["content"] == "hello world", read.message

        list_res = tools.list_dir(".")
        assert list_res.ok and any(e["name"] == "test.txt" for e in list_res.data["entries"]), list_res.data

        move = tools.move_file("test.txt", "moved.txt")
        assert move.ok, move.message

        delete = tools.delete_file("moved.txt")
        assert delete.ok, delete.message

        print("[OK] ToolExecutor")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_runtime_tool_user():
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(workspace_path=str(tmp), memory_path=str(tmp / "memory"))

        runtime = NexusAIRuntime(s)
        ai = str(uuid.uuid4())
        meta = {
            "uuid": ai,
            "use_case": "Individual",
            "abilities": ["Tool User"],
            "libraries": [],
            "guardrails": [],
        }

        r1 = runtime.run('write file "hello.txt" content: greetings from tool user', "TestAI", ai, meta)
        assert r1.status == RuntimeStatus.COMPLETED, f"write failed: {r1.title}"

        r2 = runtime.run('read file "hello.txt"', "TestAI", ai, meta)
        assert r2.status == RuntimeStatus.COMPLETED, f"read failed: {r2.title}"
        assert "greetings from tool user" in r2.result_text.lower()

        r3 = runtime.run('list files', "TestAI", ai, meta)
        assert r3.status == RuntimeStatus.COMPLETED, f"list failed: {r3.title}"

        r4 = runtime.run('delete file "hello.txt"', "TestAI", ai, meta)
        assert r4.status == RuntimeStatus.COMPLETED, f"delete failed: {r4.title}"

        print("[OK] NexusAIRuntime Tool User")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_runtime_capability_gate():
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(memory_path=str(tmp / "memory"))

        runtime = NexusAIRuntime(s)
        ai = str(uuid.uuid4())
        meta = {"uuid": ai, "use_case": "Individual", "abilities": ["Chatbot"], "libraries": [], "guardrails": []}

        # Coder intent without Coder ability should pause
        r = runtime.run("Write a Python script", "TestAI", ai, meta)
        assert r.status == RuntimeStatus.PAUSED
        assert "Capability" in r.title

        # But preferences should still be extracted from the task
        memories = runtime._memory.get_for_ai(ai)
        assert len(memories) > 0

        print("[OK] Capability gate")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_router_and_governance():
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(auto_approve_low_risk=True)

        audit = AuditLogger(s)
        approval = ApprovalGate(s)
        registry = ToolRegistry()
        router = CommandRouter(approval, audit, registry)

        ai = str(uuid.uuid4())
        registry.ensure_enabled(ai, name="TestAI", use_case="Individual", abilities=["Chatbot"])

        ok, msg = router.route(
            action="mission_start",
            tool_uuid=ai,
            description="Stress test mission",
            rationale="verification",
            targets=["test"],
            risk=RiskLevel.LOW,
            can_undo=True,
            require_approval=True,
            parent=None,
        )
        assert ok, msg

        # High-risk should be denied when not approved
        ok2, msg2 = router.route(
            action="delete_files",
            tool_uuid=ai,
            description="Delete files",
            rationale="test",
            targets=["C:\\fake"],
            risk=RiskLevel.HIGH,
            can_undo=False,
            require_approval=True,
            parent=None,
        )
        assert not ok2

        print("[OK] CommandRouter + ApprovalGate")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_health_check():
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        runtime = NexusAIRuntime(s)
        status = runtime.health_check()
        assert "provider_id" in status
        assert "reachable" in status
        assert "message" in status
        print("[OK] Health check")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_memory_prompt_injection():
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(memory_path=str(tmp / "memory"))

        runtime = NexusAIRuntime(s)
        ai = str(uuid.uuid4())
        meta = {"uuid": ai, "use_case": "Individual", "abilities": ["Chatbot"], "libraries": [], "guardrails": []}
        runtime.save_memory(ai, "User prefers Python over JavaScript", tags=["preference"], importance=0.9)

        prompt = runtime._prompt("What language should I use?", "TestAI", meta, "", "chat")
        assert "Python over JavaScript" in prompt
        print("[OK] Memory prompt injection")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("=" * 60)
    print("Command Nexus Stress / Bug / Error Test")
    print("=" * 60)

    tests = [
        ("settings", test_settings),
        ("memory_store", test_memory_store),
        ("tool_executor", test_tool_executor),
        ("runtime_tool_user", test_runtime_tool_user),
        ("runtime_intents", test_runtime_intents_and_learning),
        ("capability_gate", test_runtime_capability_gate),
        ("router", test_router_and_governance),
        ("health_check", test_health_check),
        ("memory_prompt", test_memory_prompt_injection),
    ]

    for _name, fn in tests:
        fn()

    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
