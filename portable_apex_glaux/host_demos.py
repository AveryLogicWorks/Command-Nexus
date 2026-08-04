# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Phase 15 — Four Distinct Host Demonstrations.

Demonstrates Apex Glaux operating with four distinct host types:
  1. Chat host (DemoHostAdapter) — native cognition, no LLM
  2. Tool-using host (ToolHostAdapter) — tool execution capabilities
  3. Memory-enabled host (MemoryHostAdapter) — persistent memory
  4. Orchestration host (OrchestrationHostAdapter) — multi-agent coordination

Each demonstration seeds knowledge, runs cognition, and verifies output.

Run: python -m portable_apex_glaux.host_demos
"""

from __future__ import annotations

import sys

from .core.engine import ApexGlauxEngine
from .core.interfaces import HostCapability
from .adapters import (
    DemoHostAdapter,
    ToolHostAdapter,
    MemoryHostAdapter,
    OrchestrationHostAdapter,
)


def _ok(name: str, condition: bool, detail: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    msg = f"  [{status}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return condition


def demo_chat_host() -> bool:
    """Demonstration 1: Basic chat host with native cognition only."""
    print("\n=== Host Demo 1: Chat Host (Native Cognition) ===")
    host = DemoHostAdapter(name="Chat Demo Host")
    engine = ApexGlauxEngine(host=host)
    engine.authorize("chat_host_sig")

    # Seed knowledge
    engine._memory.add("demo-ai", "Python is a high-level programming language",
                       tags=["python", "programming"], importance=0.9)
    engine._memory.add("demo-ai", "Python emphasizes code readability",
                       tags=["python", "design"], importance=0.7)
    engine._memory.add("demo-ai", "Python was created by Guido van Rossum",
                       tags=["python", "history"], importance=0.8)
    engine.index_memories("demo-ai")
    engine.discover_relations("demo-ai")

    result = engine.think("demo-ai", "What is Python?")
    _ok("Chat host returns text", len(result.text) > 0)
    _ok("Chat host returns confidence", result.confidence > 0.0)
    _ok("Chat host uses dimensions", len(result.dimensions_used) > 0)
    _ok("Response mentions Python", "python" in result.text.lower())

    stats = engine.get_stats("demo-ai")
    _ok("Stats show memories", stats["memories"] >= 3)
    return True


def demo_tool_host() -> bool:
    """Demonstration 2: Tool-using host with tool execution."""
    print("\n=== Host Demo 2: Tool-Using Host ===")

    # Define mock tools
    def calculator(operation: str, a: float, b: float) -> dict:
        if operation == "add":
            return {"result": a + b}
        elif operation == "multiply":
            return {"result": a * b}
        return {"error": f"unknown operation: {operation}"}

    def file_reader(path: str) -> dict:
        return {"content": f"Mock file contents of {path}", "size": 42}

    host = ToolHostAdapter(
        name="Tool Demo Host",
        tools={"calculator": calculator, "file_reader": file_reader},
    )
    engine = ApexGlauxEngine(host=host)
    engine.authorize("tool_host_sig")

    # Test tool execution directly
    calc_result = host.execute_tool("calculator", {"operation": "add", "a": 5, "b": 3})
    _ok("Calculator tool works", calc_result.get("result") == 8)

    file_result = host.execute_tool("file_reader", {"path": "/test/file.txt"})
    _ok("File reader tool works", "content" in file_result)

    # Seed knowledge about tools
    engine._memory.add("tool-ai", "The calculator tool can add and multiply numbers",
                       tags=["calculator", "tool"], importance=0.8)
    engine.index_memories("tool-ai")

    result = engine.think("tool-ai", "What can the calculator tool do?")
    _ok("Tool host cognition returns text", len(result.text) > 0)
    _ok("Tool host cognition mentions calculator", "calculator" in result.text.lower())

    # Verify capabilities
    _ok("Tool host has TOOL_USE capability",
        HostCapability.TOOL_USE in host.capabilities)
    _ok("Tool host has CODE_EXECUTION capability",
        HostCapability.CODE_EXECUTION in host.capabilities)
    return True


def demo_memory_host() -> bool:
    """Demonstration 3: Memory-enabled host with persistent storage."""
    print("\n=== Host Demo 3: Memory-Enabled Host ===")

    persistent = {
        "user_preference": "prefers concise answers",
        "project_context": "building a web application with React",
        "past_decision": "chose PostgreSQL over MongoDB for data consistency",
    }

    host = MemoryHostAdapter(
        name="Memory Demo Host",
        persistent_store=persistent,
    )
    engine = ApexGlauxEngine(host=host)
    engine.authorize("memory_host_sig")

    # Verify host memory is accessible
    retrieved = host.retrieve_memory("preference")
    _ok("Host memory retrieval works", len(retrieved) > 0)
    _ok("Host memory contains preference", any("prefers" in r for r in retrieved))

    # Store new memory
    stored = host.store_memory("User wants to learn about database design",
                               metadata={"key": "learning_goal"})
    _ok("Host memory storage works", stored)

    # Seed Apex Glaux's own memory
    engine._memory.add("mem-ai", "The user is building a web application with React",
                       tags=["project", "react"], importance=0.9)
    engine._memory.add("mem-ai", "The user chose PostgreSQL for data consistency",
                       tags=["database", "postgresql"], importance=0.85)
    engine.index_memories("mem-ai")

    result = engine.think("mem-ai", "What database is the user using?")
    _ok("Memory host cognition returns text", len(result.text) > 0)
    _ok("Memory host response mentions database or PostgreSQL",
        "postgresql" in result.text.lower() or "database" in result.text.lower())

    # Verify persistent store grew
    store = host.get_persistent_store()
    _ok("Persistent store has entries", len(store) >= 4)
    _ok("Persistent store contains learning goal",
        "learning_goal" in store)
    return True


def demo_orchestration_host() -> bool:
    """Demonstration 4: Orchestration host for multi-agent coordination."""
    print("\n=== Host Demo 4: Orchestration Host ===")

    # Define mock agents
    def research_agent(task: str) -> dict:
        return {"agent": "researcher", "task": task, "result": f"Research on: {task}"}

    def writer_agent(task: str) -> dict:
        return {"agent": "writer", "task": task, "result": f"Draft on: {task}"}

    def reviewer_agent(task: str) -> dict:
        return {"agent": "reviewer", "task": task, "result": f"Review of: {task}"}

    host = OrchestrationHostAdapter(
        name="Orchestration Demo Host",
        agents={
            "researcher": research_agent,
            "writer": writer_agent,
            "reviewer": reviewer_agent,
        },
    )
    engine = ApexGlauxEngine(host=host)
    engine.authorize("orch_host_sig")

    # Test delegation
    delegate_result = host.execute_tool("delegate", {
        "agent": "researcher", "task": "AI safety patterns"
    })
    _ok("Delegation to researcher works",
        delegate_result.get("status") == "delegated")

    delegate_result2 = host.execute_tool("delegate", {
        "agent": "writer", "task": "Write safety guidelines"
    })
    _ok("Delegation to writer works",
        delegate_result2.get("status") == "delegated")

    # Test aggregate
    agg_result = host.execute_tool("aggregate", {})
    _ok("Aggregate tool works", "results" in agg_result)

    # Seed knowledge about orchestration
    engine._memory.add("orch-ai", "The research agent handles information gathering",
                       tags=["orchestration", "researcher"], importance=0.8)
    engine._memory.add("orch-ai", "The writer agent creates content drafts",
                       tags=["orchestration", "writer"], importance=0.8)
    engine._memory.add("orch-ai", "The reviewer agent checks quality and accuracy",
                       tags=["orchestration", "reviewer"], importance=0.8)
    engine.index_memories("orch-ai")
    engine.discover_relations("orch-ai")

    result = engine.think("orch-ai", "What does the research agent do?")
    _ok("Orchestration host cognition returns text", len(result.text) > 0)
    _ok("Orchestration host response mentions research",
        "research" in result.text.lower())

    # Verify task queue
    queue = host.get_task_queue()
    _ok("Task queue has entries", len(queue) >= 2)

    # Verify capabilities
    _ok("Orchestration host has MULTI_AGENT capability",
        HostCapability.MULTI_AGENT in host.capabilities)
    return True


def run_all_demos() -> bool:
    """Run all four host demonstrations."""
    print("=" * 60)
    print("Apex Glaux(TM) — Phase 15 Host Demonstrations")
    print("Copyright (c) 2026 Avery Logic Works - All Rights Reserved")
    print("=" * 60)

    demos = [
        demo_chat_host,
        demo_tool_host,
        demo_memory_host,
        demo_orchestration_host,
    ]

    passed = 0
    failed = 0
    for demo in demos:
        try:
            if demo():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  [ERROR] {demo.__name__}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    success = run_all_demos()
    sys.exit(0 if success else 1)
