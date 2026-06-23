
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
import os
import urllib.parse
import urllib.request
import webbrowser
from typing import Any

from .settings_manager import SettingsManager


class RuntimeStatus(str, Enum):
    COMPLETED = "completed"
    PAUSED = "paused"
    FAILED = "failed"


@dataclass
class RuntimeResult:
    status: RuntimeStatus
    title: str
    thought_lines: list[str] = field(default_factory=list)
    action_lines: list[str] = field(default_factory=list)
    trajectory_lines: list[str] = field(default_factory=list)
    result_text: str = ""
    opened_url: str = ""


class LocalRuntimeExecutor:
    """
    The honest execution bridge.

    The UI can register and approve an AI, but that is not the same thing as doing work.
    This executor decides whether real work can happen.

    Real completion is allowed only when:
    - a model backend answers, or
    - a search backend plus model backend answers.

    Otherwise the task pauses visibly.
    """

    def __init__(self, settings: SettingsManager | None = None):
        self._settings = settings or SettingsManager()
        self._settings.initialize()
        s = self._settings.get()

        self.ai_backend = (os.environ.get("COMMAND_NEXUS_AI_BACKEND") or s.ai_backend or "ollama").strip().lower()
        self.openai_api_key = (os.environ.get("OPENAI_API_KEY") or s.openai_api_key or "").strip()
        self.openai_model = (os.environ.get("COMMAND_NEXUS_OPENAI_MODEL") or s.openai_model or "gpt-4o-mini").strip()

        self.ollama_url = (os.environ.get("COMMAND_NEXUS_OLLAMA_URL") or s.ollama_url or "http://127.0.0.1:11434").rstrip("/")
        self.ollama_model = (os.environ.get("COMMAND_NEXUS_OLLAMA_MODEL") or s.ollama_model or "llama3.1").strip()

        self.brave_api_key = (os.environ.get("BRAVE_SEARCH_API_KEY") or s.brave_api_key or "").strip()

    def run(self, task: str, ai_name: str = "AI", ai_metadata: dict[str, Any] | None = None) -> RuntimeResult:
        task = (task or "").strip()
        ai_metadata = ai_metadata or {}

        if not task:
            return RuntimeResult(
                RuntimeStatus.FAILED,
                "Empty task",
                ["[SYSTEM] No task text was provided."],
                ["[SYSTEM] Nothing was executed."],
                ["Next: enter a real task, then start again."],
            )

        kind = self._classify(task)
        base_thought = [
            f"[{ai_name}] Runtime received task.",
            f"[{ai_name}] Classified task as: {kind}.",
            f"[{ai_name}] Checking for real executor support before completion.",
        ]

        if kind == "research":
            return self._run_research(task, ai_name, ai_metadata, base_thought)

        if kind in {"system_action", "outbound_action"}:
            return RuntimeResult(
                RuntimeStatus.PAUSED,
                "Real tool executor required",
                base_thought + [
                    f"[{ai_name}] This task would affect files, apps, messages, web pages, or outside systems.",
                    f"[{ai_name}] Command Nexus will not pretend this action was performed.",
                ],
                [
                    f"[{ai_name}] Paused before performing external/system action.",
                    "[SYSTEM] No approved tool executor is currently attached for this action.",
                ],
                [
                    "Next: wire an approved tool executor for browser/file/app/email actions.",
                    "Then retry or resume the mission.",
                ],
                "Task paused. Command Nexus routed the request, but no real approved tool executor is attached yet.",
            )

        prompt = self._build_prompt(task, ai_name, ai_metadata, kind)
        model_text = self._call_model(prompt)

        if model_text:
            return RuntimeResult(
                RuntimeStatus.COMPLETED,
                "Model response completed",
                base_thought + [f"[{ai_name}] A real model backend returned output."],
                [f"[{ai_name}] Generated response using connected runtime backend."],
                ["Next: review result. Approve any real outward action separately."],
                model_text,
            )

        return RuntimeResult(
            RuntimeStatus.PAUSED,
            "No model backend connected",
            base_thought + [
                f"[{ai_name}] No Ollama/OpenAI model backend answered.",
                f"[{ai_name}] Stopping here so the app does not fake completion.",
            ],
            [
                f"[{ai_name}] Task was routed, but not executed by a real AI backend.",
                "[SYSTEM] Start Ollama locally or set OPENAI_API_KEY to enable real model execution.",
            ],
            [
                "Next: connect Ollama or OpenAI.",
                "Then retry the mission.",
            ],
            "Command Nexus routed the task, but no actual model executor is connected. Task paused instead of fake-completed.",
        )

    def _classify(self, text: str) -> str:
        t = text.lower()

        if any(x in t for x in [
            "research", "look up", "lookup", "search", "find sources", "sources",
            "source", "citation", "citations", "cite", "verify", "current",
            "latest", "web", "internet", "news", "game mechanics"
        ]):
            return "research"

        if any(x in t for x in [
            "send email", "email this", "post", "message ", "sms", "call ",
            "publish", "upload", "submit", "buy", "purchase"
        ]):
            return "outbound_action"

        if any(x in t for x in [
            "delete", "move file", "rename file", "run command", "install",
            "uninstall", "download", "open app", "click", "type into",
            "control browser", "edit file", "save file"
        ]):
            return "system_action"

        return "model_task"

    def _run_research(self, task: str, ai_name: str, meta: dict[str, Any], base_thought: list[str]) -> RuntimeResult:
        sources = self._brave_search(task) if self.brave_api_key else []

        if sources:
            source_text = "\n".join(
                f"{i + 1}. {s.get('title', 'Untitled')} | {s.get('url', '')} | {s.get('description', '')}"
                for i, s in enumerate(sources[:8])
            )

            prompt = (
                f"You are {ai_name}, a Command Nexus governed AI.\n"
                f"The user requested research.\n\n"
                f"Task: {task}\n\n"
                f"Use ONLY these collected source candidates.\n"
                f"Do not invent sources.\n"
                f"Be clear about uncertainty.\n\n"
                f"Sources:\n{source_text}\n\n"
                f"Return a concise research answer and include the source list."
            )

            model_text = self._call_model(prompt)

            if model_text:
                return RuntimeResult(
                    RuntimeStatus.COMPLETED,
                    "Research completed with source candidates",
                    base_thought + [
                        f"[{ai_name}] Search backend returned source candidates.",
                        f"[{ai_name}] Model backend summarized collected source data.",
                    ],
                    [f"[{ai_name}] Collected {len(sources[:8])} source candidates."],
                    ["Next: user reviews source quality before relying on the result."],
                    model_text + "\n\nCollected sources:\n" + source_text,
                )

            return RuntimeResult(
                RuntimeStatus.PAUSED,
                "Sources collected, model backend missing",
                base_thought + [
                    f"[{ai_name}] Search backend returned sources.",
                    f"[{ai_name}] No model backend is connected to summarize them.",
                ],
                [f"[{ai_name}] Collected sources but did not fake a summary."],
                ["Next: connect model backend, then summarize and cite."],
                "Sources were collected, but no model backend is connected.\n\nCollected sources:\n" + source_text,
            )

        search_url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(task)

        opened = False
        try:
            webbrowser.open(search_url)
            opened = True
        except Exception:
            opened = False

        return RuntimeResult(
            RuntimeStatus.PAUSED,
            "Research waiting for real source review",
            base_thought + [
                f"[{ai_name}] No real search API is connected.",
                f"[{ai_name}] Browser search was opened for manual/source review." if opened else f"[{ai_name}] Browser search could not be opened.",
                f"[{ai_name}] Research cannot truthfully complete until sources are collected and read.",
            ],
            [
                f"[{ai_name}] Opened browser search." if opened else f"[{ai_name}] Browser did not open.",
                "[SYSTEM] Audit simulator is stopped. No fake activity will continue.",
            ],
            [
                "Next: collect actual sources.",
                "Next: read/verify them.",
                "Next: summarize with citations.",
                "Do not mark complete until that exists.",
            ],
            "Research paused. Command Nexus opened search, but no real source collector/reader is attached yet.",
            opened_url=search_url if opened else "",
        )

    def _build_prompt(self, task: str, ai_name: str, meta: dict[str, Any], kind: str) -> str:
        abilities = meta.get("abilities") or meta.get("capabilities") or []
        use_case = meta.get("use_case") or ""

        return (
            f"You are {ai_name}, a Command Nexus governed AI.\n"
            f"Task type: {kind}\n"
            f"Use case: {use_case}\n"
            f"Configured abilities: {abilities}\n\n"
            f"User task:\n{task}\n\n"
            f"Answer usefully. Do not claim you performed external actions unless a tool actually performed them."
        )

    def _call_model(self, prompt: str) -> str:
        if self.ai_backend == "openai":
            text = self._call_openai(prompt)
            if text and not text.startswith("OpenAI backend error"):
                return text
            return self._call_ollama(prompt)
        text = self._call_ollama(prompt)
        if text:
            return text
        return self._call_openai(prompt)

    def _call_ollama(self, prompt: str) -> str:
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
        }

        try:
            req = urllib.request.Request(
                self.ollama_url + "/api/generate",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
            return (data.get("response") or "").strip()
        except Exception:
            return ""

    def _call_openai(self, prompt: str) -> str:
        if not self.openai_api_key:
            return ""

        payload = {
            "model": self.openai_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are the execution backend for Command Nexus. Be honest about what was actually done."
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        }

        try:
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + self.openai_api_key,
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"OpenAI backend error: {e}"

    def _brave_search(self, query: str) -> list[dict[str, str]]:
        if not self.brave_api_key:
            return []

        url = "https://api.search.brave.com/res/v1/web/search?q=" + urllib.parse.quote_plus(query)

        try:
            req = urllib.request.Request(
                url,
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": self.brave_api_key,
                },
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
            return data.get("web", {}).get("results", []) or []
        except Exception:
            return []
