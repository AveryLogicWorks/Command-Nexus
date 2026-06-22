from pathlib import Path
import re
import shutil
import sys

ROOT = Path.cwd()
VIS = ROOT / "src" / "parts" / "visibility" / "visibility_window.py"
RUNTIME = ROOT / "src" / "core" / "runtime_executor.py"

if not VIS.exists():
    print("ERROR: visibility_window.py not found.")
    print(r'Run from: B:\Documents\GitHub\Command Nexus')
    sys.exit(1)

RUNTIME.parent.mkdir(parents=True, exist_ok=True)

runtime_code = r"""
# Command Nexus runtime executor.
#
# This is the missing bridge between:
# - an AI being selectable/approved in the UI
# - a task actually doing work
#
# It never marks research/system/outbound tasks complete unless a real backend exists.
# It can use:
# - local Ollama at http://127.0.0.1:11434 if available
# - OPENAI_API_KEY if available
# - BRAVE_SEARCH_API_KEY for web source collection if available
#
# Without those, it pauses honestly instead of fake-completing.

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
import os
import urllib.parse
import urllib.request
import webbrowser
from typing import Any


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
    def __init__(self):
        self.openai_api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        self.openai_model = os.environ.get("COMMAND_NEXUS_OPENAI_MODEL", "gpt-4o-mini").strip()
        self.ollama_url = os.environ.get("COMMAND_NEXUS_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
        self.ollama_model = os.environ.get("COMMAND_NEXUS_OLLAMA_MODEL", "llama3.1").strip()
        self.brave_api_key = os.environ.get("BRAVE_SEARCH_API_KEY", "").strip()

    def run(self, task: str, ai_name: str = "AI", ai_metadata: dict[str, Any] | None = None) -> RuntimeResult:
        task = (task or "").strip()
        ai_metadata = ai_metadata or {}
        if not task:
            return RuntimeResult(
                RuntimeStatus.FAILED,
                "Empty task",
                ["No task text was provided."],
                ["Nothing was executed."],
                ["Enter a task, then start again."],
            )

        kind = self._classify(task)
        base_thought = [
            f"[{ai_name}] Runtime received task.",
            f"[{ai_name}] Classified task as: {kind}.",
            f"[{ai_name}] Checking for real executor support before completion.",
        ]

        if kind == "research":
            return self._run_research(task, ai_name, base_thought)

        if kind in {"system_action", "outbound_action"}:
            return RuntimeResult(
                RuntimeStatus.PAUSED,
                "Approval/action bridge required",
                base_thought + [f"[{ai_name}] This task can affect files, apps, messages, or outside systems."],
                [f"[{ai_name}] Paused before pretending to perform an external/system action."],
                ["Next: wire a real approved tool executor for this action, then resume."],
                "This task was not completed because Command Nexus does not yet have a real approved tool executor for it.",
            )

        prompt = self._build_prompt(task, ai_name, ai_metadata, kind)
        model_text = self._call_model(prompt)

        if model_text:
            return RuntimeResult(
                RuntimeStatus.COMPLETED,
                "Model response completed",
                base_thought + [f"[{ai_name}] A real model backend returned output."],
                [f"[{ai_name}] Generated response using connected runtime backend."],
                ["Next: review result, then approve any real outward action separately."],
                model_text,
            )

        return RuntimeResult(
            RuntimeStatus.PAUSED,
            "No model backend connected",
            base_thought + [f"[{ai_name}] No Ollama/OpenAI model backend answered."],
            [f"[{ai_name}] Stopped before fake-completing the task."],
            [
                "Next: start Ollama locally or set OPENAI_API_KEY.",
                "Then retry this mission so the AI has a real brain behind the UI.",
            ],
            "Command Nexus routed the task, but no actual model executor is connected. Task paused instead of fake-completed.",
        )

    def _classify(self, text: str) -> str:
        t = text.lower()
        if any(x in t for x in ["research", "look up", "lookup", "search", "find sources", "sources", "source", "citation", "citations", "verify", "current", "latest", "web", "internet", "news"]):
            return "research"
        if any(x in t for x in ["send email", "email this", "post", "message ", "sms", "call ", "publish", "upload"]):
            return "outbound_action"
        if any(x in t for x in ["delete", "move file", "rename file", "run command", "install", "uninstall", "download", "open app", "click", "type into"]):
            return "system_action"
        return "model_task"

    def _run_research(self, task: str, ai_name: str, base_thought: list[str]) -> RuntimeResult:
        sources = self._brave_search(task) if self.brave_api_key else []

        if sources:
            source_text = "\n".join(
                f"{i+1}. {s.get('title','Untitled')} - {s.get('url','')} - {s.get('description','')}"
                for i, s in enumerate(sources[:8])
            )
            prompt = (
                f"You are {ai_name}. The user requested research.\n"
                f"Task: {task}\n\n"
                f"Use ONLY these collected search results. Be clear about uncertainty.\n"
                f"Sources:\n{source_text}\n\n"
                f"Return a concise researched answer with source list."
            )
            model_text = self._call_model(prompt)
            if model_text:
                return RuntimeResult(
                    RuntimeStatus.COMPLETED,
                    "Research completed with collected sources",
                    base_thought + [f"[{ai_name}] Search backend returned sources.", f"[{ai_name}] Model summarized collected source data."],
                    [f"[{ai_name}] Collected {len(sources[:8])} source candidates via search backend."],
                    ["Next: user reviews source quality before relying on the result."],
                    model_text + "\n\nCollected sources:\n" + source_text,
                )

            return RuntimeResult(
                RuntimeStatus.PAUSED,
                "Sources collected, model missing",
                base_thought + [f"[{ai_name}] Search backend returned sources, but no model backend answered."],
                [f"[{ai_name}] Collected sources but did not fake a summary."],
                ["Next: connect model backend, then summarize and cite."],
                "Sources were collected, but no model backend is connected to summarize them.\n\nCollected sources:\n" + source_text,
            )

        url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(task)
        opened = False
        try:
            webbrowser.open(url)
            opened = True
        except Exception:
            opened = False

        return RuntimeResult(
            RuntimeStatus.PAUSED,
            "Research requires source review",
            base_thought + [f"[{ai_name}] No search API backend is connected."],
            [f"[{ai_name}] Opened browser search." if opened else f"[{ai_name}] Could not open browser search."],
            [
                "Next: collect real sources.",
                "Next: read/verify them.",
                "Next: summarize with citations.",
                "Do not mark complete until sources exist.",
            ],
            "Research was paused because no real search/source backend is connected. It cannot truthfully complete in seconds.",
            opened_url=url if opened else "",
        )

    def _build_prompt(self, task: str, ai_name: str, meta: dict[str, Any], kind: str) -> str:
        abilities = meta.get("abilities") or meta.get("capabilities") or []
        return (
            f"You are {ai_name}, a Command Nexus governed AI.\n"
            f"Task type: {kind}\n"
            f"Configured abilities: {abilities}\n"
            f"User task: {task}\n\n"
            f"Answer usefully. Do not claim you performed external actions unless the tool actually did them."
        )

    def _call_model(self, prompt: str) -> str:
        text = self._call_ollama(prompt)
        if text:
            return text
        return self._call_openai(prompt)

    def _call_ollama(self, prompt: str) -> str:
        payload = {"model": self.ollama_model, "prompt": prompt, "stream": False}
        try:
            req = urllib.request.Request(
                self.ollama_url + "/api/generate",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
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
                {"role": "system", "content": "You are the execution backend for Command Nexus. Be honest about what was actually done."},
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
            with urllib.request.urlopen(req, timeout=120) as resp:
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
"""

old_runtime = RUNTIME.read_text(encoding="utf-8") if RUNTIME.exists() else ""
if old_runtime != runtime_code:
    if RUNTIME.exists():
        bak = RUNTIME.with_suffix(".py.runtime_backup")
        if not bak.exists():
            shutil.copy2(RUNTIME, bak)
    RUNTIME.write_text(runtime_code, encoding="utf-8")
    print("WROTE:", RUNTIME)
else:
    print("OK:", RUNTIME)

text = VIS.read_text(encoding="utf-8")
original = text

vis_backup = VIS.with_suffix(".py.runtime_bridge_backup")
if not vis_backup.exists():
    shutil.copy2(VIS, vis_backup)

if "from ...core.runtime_executor import LocalRuntimeExecutor, RuntimeStatus" not in text:
    anchor = "from ...core.nexus_moirai import check_action_allowed, MoiraiHealthReport\n"
    if anchor in text:
        text = text.replace(anchor, anchor + "from ...core.runtime_executor import LocalRuntimeExecutor, RuntimeStatus\n", 1)
    else:
        print("WARN: import anchor not found")

if "self._runtime_executor = LocalRuntimeExecutor()" not in text:
    anchor = "        self._settings.initialize()\n"
    if anchor in text:
        text = text.replace(anchor, anchor + "        self._runtime_executor = LocalRuntimeExecutor()\n", 1)
    else:
        print("WARN: settings initialize anchor not found")

text = text.replace(
"""        colors = {
            AIStatus.IDLE: ("#888888", "#21262d"),
            AIStatus.RUNNING: ("#4caf50", "#1b5e20"),
            AIStatus.PAUSED: ("#ff9800", "#4a2c00"),
            AIStatus.FAILED: ("#f44336", "#4a0000"),
            AIStatus.COMPLETED: ("#58a6ff", "#0d47a1"),
        }""",
"""        colors = {
            AIStatus.IDLE: ("#888888", "#21262d"),
            AIStatus.WAITING_APPROVAL: ("#ffee58", "#4a3b00"),
            AIStatus.RUNNING: ("#4caf50", "#1b5e20"),
            AIStatus.PAUSED: ("#ff9800", "#4a2c00"),
            AIStatus.FAILED: ("#f44336", "#4a0000"),
            AIStatus.COMPLETED: ("#58a6ff", "#0d47a1"),
        }"""
)

new_tick = r"""    def _on_mission_tick(self):
        self._mission_progress += 1
        uuid = self._get_selected_uuid()
        if not uuid or uuid not in self._sessions:
            self._mission_timer.stop()
            return

        session = self._sessions[uuid]
        if not session.current_task:
            self._mission_timer.stop()
            return

        task = session.current_task

        if self._mission_progress == 1:
            self._thought_pane.append(f"[SYSTEM] Dispatching '{task.name}' to runtime executor for {session.name}.")
            self._action_pane.append("[SYSTEM] This mission will not be marked complete unless the executor returns completed.")
            self._trajectory_pane.append("[SYSTEM] Runtime path: classify task -> run model/search/tool bridge -> report honest status.")
            return

        self._mission_timer.stop()

        try:
            meta = self._registry.get(uuid) if self._registry else {}
        except Exception:
            meta = {}

        try:
            result = self._runtime_executor.run(task.name, ai_name=session.name, ai_metadata=meta or {})
        except Exception as e:
            result = None
            self._thought_pane.append(f"[SYSTEM] Runtime executor crashed: {e}")

        if result is None:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            session.current_task = None
            session.status = AIStatus.FAILED
            self._action_pane.append("[SYSTEM] Task failed because runtime executor crashed.")
            self._trajectory_pane.append("[SYSTEM] Next: inspect runtime_executor.py and logs.")
            self._update_status_display(AIStatus.FAILED)
            self._set_presence(PresenceState.ERROR, "Runtime crashed")
            self._refresh_task_queue()
            self._btn_cancel.setEnabled(False)
            self._audit_event("mission_runtime_crashed", msg=task.name)
            return

        for line in result.thought_lines:
            self._thought_pane.append(line)
        for line in result.action_lines:
            self._action_pane.append(line)
        for line in result.trajectory_lines:
            self._trajectory_pane.append(line)
        if result.result_text:
            self._action_pane.append("[RESULT]")
            self._action_pane.append(result.result_text)
        if getattr(result, "opened_url", ""):
            self._trajectory_pane.append(f"[SYSTEM] Opened: {result.opened_url}")

        if result.status == RuntimeStatus.PAUSED:
            task.status = TaskStatus.PAUSED
            session.status = AIStatus.PAUSED
            self._update_status_display(AIStatus.PAUSED)
            self._set_presence(PresenceState.PAUSED, result.title)
            self._refresh_task_queue()
            self._btn_cancel.setEnabled(True)
            self._viewport.stop_stream("AI Vision Stream - task paused / waiting for real executor or review.")
            self._audit_event("mission_paused_runtime", msg=result.title)
            return

        if result.status == RuntimeStatus.FAILED:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            session.current_task = None
            session.status = AIStatus.FAILED
            self._update_status_display(AIStatus.FAILED)
            self._set_presence(PresenceState.ERROR, result.title)
            self._refresh_task_queue()
            self._btn_cancel.setEnabled(False)
            self._viewport.stop_stream()
            self._audit_event("mission_failed_runtime", msg=result.title)
            return

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        session.task_history.append(task)
        session.current_task = None
        session.status = AIStatus.IDLE
        self._action_pane.append(f"[SYSTEM] Task '{task.name}' completed by runtime executor.")
        self._speak(f"Task {task.name} completed.")
        self._update_status_display(AIStatus.IDLE)
        self._set_presence(PresenceState.IDLE, "Idle / ready")
        self._refresh_task_queue()
        self._btn_cancel.setEnabled(False)
        self._viewport.stop_stream()
        self._audit_event("mission_complete_runtime", msg=task.name)

"""

pattern = re.compile(r"    def _on_mission_tick\(self\):\n.*?(?=\n    def _on_cancel_mission\(self\):)", re.S)
text2, count = pattern.subn(new_tick, text, count=1)
if count != 1:
    print("ERROR: Could not replace _on_mission_tick. File shape changed.")
    sys.exit(2)
text = text2

if "Runtime executor queued. Fake timer completion disabled." not in text:
    text = text.replace(
"""        self._audit_event("mission_start", msg=task.name)
        self._thought_pane.append(f"[SYSTEM] Mission '{task.name}' started for '{session.name}'.")
""",
"""        self._audit_event("mission_start", msg=task.name)
        self._thought_pane.append(f"[SYSTEM] Mission '{task.name}' started for '{session.name}'.")
        self._trajectory_pane.append("[SYSTEM] Runtime executor queued. Fake timer completion disabled.")
""",
        1,
    )

if text != original:
    VIS.write_text(text, encoding="utf-8")
    print("PATCHED:", VIS)
    print("BACKUP:", vis_backup)
else:
    print("No visibility changes needed.")

print()
print("Runtime bridge installed.")
print("Behavior now:")
print(" - Research/outside actions pause unless a real executor/search backend exists.")
print(" - Model tasks run through Ollama or OpenAI if configured.")
print(" - No mission should fake-complete from a timer anymore.")
