# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Host Adapters for Apex Glaux — demonstrates integration into any AI.

This file provides four distinct host adapter types as required by Phase 15:
  1. DemoHostAdapter  — basic chat host (no LLM, native cognition only)
  2. LLMHostAdapter   — chat host with an LLM backend (dim4 activates)
  3. ToolHostAdapter  — tool-using host (execute_tool, code execution)
  4. MemoryHostAdapter— memory-enabled host (persistent memory access)
  5. OrchestrationHostAdapter — multi-agent orchestration host

Copy these patterns into your own AI application to integrate Apex Glaux.
"""

from __future__ import annotations

import time

from .core.interfaces import IHostAdapter, HostCapability, HostContext


class DemoHostAdapter(IHostAdapter):
    """Minimal host adapter for demonstration and testing.

    This host has no LLM backend — it relies entirely on Apex Glaux's
    native cognition (dims 1-3). When you provide a real LLM via
    call_model(), dim4 activates and the full Trifecta Folding runs.
    """

    def __init__(self, name: str = "Demo Host",
                 capabilities: set[HostCapability] | None = None,
                 model_fn=None):
        self._name = name
        self._capabilities = capabilities or {HostCapability.CHAT}
        self._model_fn = model_fn
        self._memory: list[str] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def capabilities(self) -> set[HostCapability]:
        return self._capabilities

    def call_model(self, prompt: str, **kwargs) -> str:
        """Call the host's model. If no model function provided, returns empty."""
        if self._model_fn:
            try:
                return self._model_fn(prompt, **kwargs)
            except Exception:
                return ""
        return ""

    def retrieve_memory(self, query: str, top_k: int = 5) -> list[str]:
        """Return from the host's own memory (if any)."""
        return self._memory[:top_k]

    def store_memory(self, content: str, metadata: dict | None = None) -> bool:
        self._memory.append(content)
        return True

    def execute_tool(self, tool_name: str, args: dict) -> dict:
        return {"error": f"tool '{tool_name}' not supported in demo host"}

    def web_search(self, query: str, top_k: int = 5) -> list[dict]:
        return []


class ToolHostAdapter(IHostAdapter):
    """Host adapter that provides tool execution capabilities.

    This host can execute tools, run code, and access files.
    Apex Glaux uses this for tool-augmented cognition where the
    host's tools become an extension of the reasoning engine.
    """

    def __init__(self, name: str = "Tool Host",
                 model_fn=None,
                 tools: dict | None = None):
        self._name = name
        self._model_fn = model_fn
        self._tools = tools or {}
        self._memory: list[str] = []
        self._capabilities = {
            HostCapability.CHAT,
            HostCapability.TOOL_USE,
            HostCapability.CODE_EXECUTION,
            HostCapability.FILE_ACCESS,
        }

    @property
    def name(self) -> str:
        return self._name

    @property
    def capabilities(self) -> set[HostCapability]:
        return self._capabilities

    def call_model(self, prompt: str, **kwargs) -> str:
        if self._model_fn:
            try:
                return self._model_fn(prompt, **kwargs)
            except Exception:
                return ""
        return ""

    def retrieve_memory(self, query: str, top_k: int = 5) -> list[str]:
        return self._memory[:top_k]

    def store_memory(self, content: str, metadata: dict | None = None) -> bool:
        self._memory.append(content)
        return True

    def execute_tool(self, tool_name: str, args: dict) -> dict:
        if tool_name in self._tools:
            try:
                return self._tools[tool_name](**args)
            except Exception as e:
                return {"error": f"tool '{tool_name}' failed: {e}"}
        return {"error": f"tool '{tool_name}' not registered"}

    def register_tool(self, name: str, fn) -> None:
        self._tools[name] = fn

    def web_search(self, query: str, top_k: int = 5) -> list[dict]:
        return []


class MemoryHostAdapter(IHostAdapter):
    """Host adapter with persistent memory capabilities.

    This host has its own persistent memory store that Apex Glaux
    can read from and write to. This enables cross-session knowledge
    retention and collaborative memory between host and Apex Glaux.
    """

    def __init__(self, name: str = "Memory Host",
                 model_fn=None,
                 persistent_store: dict | None = None):
        self._name = name
        self._model_fn = model_fn
        self._persistent = persistent_store if persistent_store is not None else {}
        self._capabilities = {
            HostCapability.CHAT,
            HostCapability.MEMORY_ACCESS,
        }

    @property
    def name(self) -> str:
        return self._name

    @property
    def capabilities(self) -> set[HostCapability]:
        return self._capabilities

    def call_model(self, prompt: str, **kwargs) -> str:
        if self._model_fn:
            try:
                return self._model_fn(prompt, **kwargs)
            except Exception:
                return ""
        return ""

    def retrieve_memory(self, query: str, top_k: int = 5) -> list[str]:
        results = []
        query_lower = query.lower()
        for key, value in self._persistent.items():
            if query_lower in key.lower() or query_lower in str(value).lower():
                results.append(f"{key}: {value}")
                if len(results) >= top_k:
                    break
        return results

    def store_memory(self, content: str, metadata: dict | None = None) -> bool:
        key = metadata.get("key", f"mem_{len(self._persistent)}") if metadata else f"mem_{len(self._persistent)}"
        self._persistent[key] = content
        return True

    def execute_tool(self, tool_name: str, args: dict) -> dict:
        return {"error": "not supported"}

    def web_search(self, query: str, top_k: int = 5) -> list[dict]:
        return []

    def get_persistent_store(self) -> dict:
        return dict(self._persistent)


class OrchestrationHostAdapter(IHostAdapter):
    """Host adapter for multi-agent orchestration.

    This host manages multiple AI agents and can delegate tasks,
    aggregate results, and coordinate workflows. Apex Glaux
    augments the orchestrator's decision-making with its cognitive
    architecture.
    """

    def __init__(self, name: str = "Orchestration Host",
                 model_fn=None,
                 agents: dict | None = None):
        self._name = name
        self._model_fn = model_fn
        self._agents = agents if agents is not None else {}
        self._memory: list[str] = []
        self._task_queue: list[dict] = []
        self._completed_tasks: list[dict] = []
        self._capabilities = {
            HostCapability.CHAT,
            HostCapability.MULTI_AGENT,
            HostCapability.TOOL_USE,
        }

    @property
    def name(self) -> str:
        return self._name

    @property
    def capabilities(self) -> set[HostCapability]:
        return self._capabilities

    def call_model(self, prompt: str, **kwargs) -> str:
        if self._model_fn:
            try:
                return self._model_fn(prompt, **kwargs)
            except Exception:
                return ""
        return ""

    def retrieve_memory(self, query: str, top_k: int = 5) -> list[str]:
        return self._memory[:top_k]

    def store_memory(self, content: str, metadata: dict | None = None) -> bool:
        self._memory.append(content)
        return True

    def execute_tool(self, tool_name: str, args: dict) -> dict:
        if tool_name == "delegate":
            agent_name = args.get("agent", "")
            task = args.get("task", "")
            if agent_name in self._agents:
                self._task_queue.append({
                    "agent": agent_name, "task": task,
                    "status": "queued", "timestamp": time.time()
                })
                return {"status": "delegated", "agent": agent_name, "task": task}
            return {"error": f"agent '{agent_name}' not registered"}
        elif tool_name == "aggregate":
            return {"results": list(self._completed_tasks)}
        return {"error": f"tool '{tool_name}' not supported"}

    def register_agent(self, name: str, agent_fn) -> None:
        self._agents[name] = agent_fn

    def run_tasks(self) -> list[dict]:
        """Execute all queued tasks, moving results to completed."""
        results = []
        for task in self._task_queue:
            agent_fn = self._agents.get(task["agent"])
            if agent_fn:
                try:
                    result = agent_fn(task["task"])
                    task["status"] = "completed"
                    task["result"] = result
                    self._completed_tasks.append(task)
                    results.append(task)
                except Exception as e:
                    task["status"] = "failed"
                    task["error"] = str(e)
                    results.append(task)
        self._task_queue.clear()
        return results

    def web_search(self, query: str, top_k: int = 5) -> list[dict]:
        return []

    def get_task_queue(self) -> list[dict]:
        return list(self._task_queue)

    def get_completed_tasks(self) -> list[dict]:
        return list(self._completed_tasks)


class LLMHostAdapter(IHostAdapter):
    """Host adapter that wraps any LLM (OpenAI, Anthropic, local model, etc.).

    Usage:
        import openai
        def my_llm(prompt, **kwargs):
            resp = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            return resp.choices[0].message.content

        host = LLMHostAdapter(model_fn=my_llm, name="GPT-4 Host")
        engine = ApexGlauxEngine(host=host)
        engine.authorize("my_app_signature")
        result = engine.think("user-1", "Explain quantum computing")
    """

    def __init__(self, model_fn, name: str = "LLM Host",
                 capabilities: set[HostCapability] | None = None):
        self._model_fn = model_fn
        self._name = name
        self._capabilities = capabilities or {HostCapability.CHAT}
        self._memory: list[str] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def capabilities(self) -> set[HostCapability]:
        return self._capabilities

    def call_model(self, prompt: str, **kwargs) -> str:
        try:
            return self._model_fn(prompt, **kwargs)
        except Exception:
            return ""

    def retrieve_memory(self, query: str, top_k: int = 5) -> list[str]:
        return self._memory[:top_k]

    def store_memory(self, content: str, metadata: dict | None = None) -> bool:
        self._memory.append(content)
        return True

    def execute_tool(self, tool_name: str, args: dict) -> dict:
        return {"error": "not supported"}

    def web_search(self, query: str, top_k: int = 5) -> list[dict]:
        return []
