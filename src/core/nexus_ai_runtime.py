
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Any
import json
import os
import re
import time
import urllib.parse
import urllib.request
import webbrowser


_BOOK_CIPHER_KEY = b"AVERY_LOGIC_WORKS_NEXUS_BOOK_2026"


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


CAPABILITY_ALIASES = {
    "Chat Companion": "Chatbot",
    "Chat": "Chatbot",
    "Customer Support Agent": "Chatbot",
    "Customer Support AI": "Chatbot",
    "Email Sifter & Responder": "Chatbot",

    "Research Assistant": "Research",
    "Academic Researcher": "Research",
    "Business Intelligence Analyst": "Research",

    "Coding Assistant": "Coder",
    "IT Operations Agent": "Coder",

    "Creative Writer": "Creative Writing",
    "Marketing Generator": "Creative Writing",

    "Personal Organizer": "Notebook",
    "Meeting Scribe": "Notebook",

    "Task / Project Manager": "Planner",
    "Strategic Planner": "Planner",
    "Workflow Automator": "Planner",

    "Document Processor": "Document Processor",

    "Learning Tutor": "Tutor",
    "Classroom Tutor": "Tutor",
    "Assignment Grader": "Tutor",
    "Lesson Planner": "Tutor",
    "Language Coach": "Tutor",
    "Accessibility Aide": "Tutor",

    "Sales Assistant": "Business Workflow",
    "Financial Analyst": "Business Workflow",
    "HR Assistant": "Business Workflow",
    "Compliance Auditor": "Business Workflow",
    "Supply Chain Coordinator": "Business Workflow",
    "Legal Document Reviewer": "Business Workflow",
    "Multi-Department Orchestrator": "Business Workflow",
    "Data Entry Agent": "Business Workflow",
    "Content Moderator": "Business Workflow",

    "Archive": "Archive",
    "Memory": "Archive",
    "Tool User": "Tool User",
    "Agent": "Tool User",
}


class NexusAIRuntime:
    """
    Real Command Nexus runtime bridge.

    This connects:
    - AI metadata from Forge
    - Knowledge / Intelligence profile
    - capabilities
    - local safe capability behaviors
    - optional Ollama/OpenAI model backend
    - optional Brave Search backend

    It must never fake-complete external, research, browser, file, or tool actions.
    """

    def __init__(self):
        self.home = Path.home() / ".command_nexus"
        self.notes_dir = self.home / "notes"
        self.archive_dir = self.home / "runtime_archive"
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        # Model backend config: in-app Settings take priority, env vars are the fallback.
        s = self._load_model_settings()
        self.model_backend = (s.get("model_backend") or "auto").strip().lower()
        self.openai_api_key = (s.get("openai_api_key") or os.environ.get("OPENAI_API_KEY", "")).strip()
        self.openai_model = (s.get("openai_model") or os.environ.get("COMMAND_NEXUS_OPENAI_MODEL", "gpt-4o-mini")).strip()

        self.ollama_url = (s.get("ollama_url") or os.environ.get("COMMAND_NEXUS_OLLAMA_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.ollama_model = (s.get("ollama_model") or os.environ.get("COMMAND_NEXUS_OLLAMA_MODEL", "llama3.2:1b")).strip()

        self.brave_api_key = os.environ.get("BRAVE_SEARCH_API_KEY", "").strip()

    def _load_model_settings(self) -> dict[str, Any]:
        """Read model backend settings from the app SettingsManager, if available."""
        try:
            from src.core.settings_manager import SettingsManager
            s = SettingsManager().get()
            return {
                "model_backend": getattr(s, "model_backend", ""),
                "openai_api_key": getattr(s, "openai_api_key", ""),
                "openai_model": getattr(s, "openai_model", ""),
                "ollama_url": getattr(s, "ollama_url", ""),
                "ollama_model": getattr(s, "ollama_model", ""),
            }
        except Exception:
            return {}

    def run(self, task: str, ai_name: str = "AI", ai_uuid: str = "", ai_metadata: dict[str, Any] | None = None) -> RuntimeResult:
        task = (task or "").strip()
        meta = ai_metadata or {}

        if not task:
            return RuntimeResult(
                RuntimeStatus.FAILED,
                "Empty task",
                ["[SYSTEM] No task was entered."],
                ["[SYSTEM] Runtime refused to fake an empty task."],
                ["Next: enter a real mission/task and start again."],
            )

        abilities = self._canonical_abilities(meta)
        intent = self._classify(task)
        knowledge = self._load_knowledge(ai_uuid or str(meta.get("uuid", "")), meta)

        thought = [
            f"[{ai_name}] Runtime received task.",
            f"[{ai_name}] Intent detected: {intent}.",
            f"[{ai_name}] Active capabilities: {', '.join(sorted(abilities)) if abilities else 'none detected'}.",
            f"[{ai_name}] Knowledge/Intelligence profile: {'connected' if knowledge else 'not found'}."
        ]

        if not self._capability_allowed(intent, abilities):
            return RuntimeResult(
                RuntimeStatus.PAUSED,
                "Capability not attached",
                thought + [f"[{ai_name}] Required capability is not attached for this task."],
                [f"[{ai_name}] Paused instead of pretending unsupported capability exists."],
                ["Next: add the needed capability in AI Forge or choose an AI that has it."],
                f"Required capability missing for this task: {intent}",
            )

        if intent == "Research":
            return self._run_research(task, ai_name, meta, knowledge, thought)

        if intent == "Coder":
            return self._run_coder(task, ai_name, meta, knowledge, thought)

        if intent == "Creative Writing":
            return self._run_writer(task, ai_name, meta, knowledge, thought)

        if intent == "Planner":
            return self._run_planner(task, ai_name, meta, knowledge, thought)

        if intent == "Document Processor":
            return self._run_document_processor(task, ai_name, meta, knowledge, thought)

        if intent == "Notebook":
            return self._run_notebook(task, ai_name, meta, knowledge, thought)

        if intent == "Archive":
            return self._run_archive(task, ai_name, meta, knowledge, thought)

        if intent == "Tutor":
            return self._run_tutor(task, ai_name, meta, knowledge, thought)

        if intent == "Business Workflow":
            return self._run_business(task, ai_name, meta, knowledge, thought)

        if intent == "Tool User":
            return RuntimeResult(
                RuntimeStatus.PAUSED,
                "Approved tool executor required",
                thought + [f"[{ai_name}] This requires real browser/file/app/tool control."],
                [f"[{ai_name}] Paused before performing real external action."],
                ["Next: attach approved tool executors, then resume."],
                "Command Nexus can propose and approve this action, but no real tool executor is attached yet.",
            )

        return self._run_chat(task, ai_name, meta, knowledge, thought)

    def _canonical_abilities(self, meta: dict[str, Any]) -> set[str]:
        raw = meta.get("abilities") or meta.get("capabilities") or []
        out: set[str] = set()
        for item in raw:
            item = str(item).strip()
            if not item:
                continue
            out.add(item)
            out.add(CAPABILITY_ALIASES.get(item, item))
        if not out:
            out.add("Chatbot")
        return out

    def _capability_allowed(self, intent: str, abilities: set[str]) -> bool:
        if intent == "Chatbot":
            return True
        if intent in abilities:
            return True
        if intent == "Tool User" and any(x in abilities for x in {"Coder", "Research", "Planner", "Business Workflow"}):
            return True
        return False

    def _classify(self, task: str) -> str:
        t = task.lower()

        if any(x in t for x in ["research", "look up", "lookup", "search", "find sources", "sources", "citation", "cite", "verify", "current", "latest", "web", "internet", "news", "game mechanics"]):
            return "Research"

        if any(x in t for x in ["code", "bug", "python", "javascript", "html", "css", "function", "class", "error", "traceback", "fix script", "patch"]):
            return "Coder"

        if any(x in t for x in ["write", "draft", "rewrite", "story", "script", "copy", "article", "post", "paragraph", "creative"]):
            return "Creative Writing"

        if any(x in t for x in ["plan", "steps", "strategy", "schedule", "roadmap", "milestone", "organize project", "workflow"]):
            return "Planner"

        if any(x in t for x in ["document", "summarize this", "extract", "compare document", "pdf", "docx", "file:"]):
            return "Document Processor"

        if any(x in t for x in ["note", "remember", "log this", "save note", "take notes"]):
            return "Notebook"

        if any(x in t for x in ["archive", "save this result", "store this", "retrieve archive"]):
            return "Archive"

        if any(x in t for x in ["teach", "lesson", "quiz", "study", "explain like", "tutor"]):
            return "Tutor"

        if any(x in t for x in ["customer", "sales", "marketing", "hr", "sop", "business", "support reply"]):
            return "Business Workflow"

        if any(x in t for x in ["delete", "move file", "rename file", "run command", "install", "uninstall", "download", "open app", "click", "type into", "send email", "upload", "publish", "submit"]):
            return "Tool User"

        return "Chatbot"

    def _derive_book_key(self, uuid: str) -> bytes:
        return sha256(_BOOK_CIPHER_KEY + uuid.encode()).digest()

    def _decrypt_book(self, data: bytes, uuid: str) -> str:
        key = self._derive_book_key(uuid)
        plain = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
        return plain.decode("utf-8", errors="replace")

    def _load_knowledge(self, uuid: str, meta: dict[str, Any]) -> str:
        p = meta.get("ability_book_path") or meta.get("knowledge_path") or meta.get("intelligence_path") or ""
        if not p:
            return ""
        path = Path(str(p))
        try:
            nbk = path.with_suffix(".nbk")
            if nbk.exists() and uuid:
                return self._decrypt_book(nbk.read_bytes(), uuid)
            if path.exists():
                return path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return f"[Knowledge read error: {e}]"
        return ""

    def _knowledge_excerpt(self, knowledge: str, limit: int = 6000) -> str:
        if not knowledge:
            return ""
        clean = knowledge.strip()
        if len(clean) <= limit:
            return clean
        return clean[:limit] + "\n\n[Knowledge excerpt truncated for runtime prompt.]"

    def _run_chat(self, task, ai_name, meta, knowledge, thought):
        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "chat"))
        if model:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Chat completed", thought + [f"[{ai_name}] Model backend answered using Knowledge/Intelligence context."], [f"[{ai_name}] Returned chat response."], ["Next: continue conversation or approve outward action."], model)

        return RuntimeResult(
            RuntimeStatus.COMPLETED,
            "Local chat fallback completed",
            thought + [f"[{ai_name}] No model backend connected; using governed local fallback."],
            [f"[{ai_name}] Produced basic local response from task and Knowledge metadata."],
            ["Next: connect Ollama/OpenAI for full AI answers."],
            f"{ai_name} received: {task}\n\nKnowledge connected: {'yes' if knowledge else 'no'}\n\nLocal fallback: I can clarify, plan, draft, code-triage, or research-gate this. Connect Ollama or OPENAI_API_KEY for full model reasoning.",
        )

    def _run_research(self, task, ai_name, meta, knowledge, thought):
        sources = self._brave_search(task) if self.brave_api_key else []

        if sources:
            source_text = "\n".join(
                f"{i+1}. {s.get('title','Untitled')} | {s.get('url','')} | {s.get('description','')}"
                for i, s in enumerate(sources[:8])
            )
            model = self._call_model(
                self._prompt(
                    "Research task: " + task + "\n\nUse only these source candidates:\n" + source_text,
                    ai_name, meta, knowledge, "research"
                )
            )
            if model:
                return RuntimeResult(
                    RuntimeStatus.COMPLETED,
                    "Research completed with source candidates",
                    thought + [f"[{ai_name}] Search backend returned source candidates.", f"[{ai_name}] Model summarized sources."],
                    [f"[{ai_name}] Collected {len(sources[:8])} source candidates."],
                    ["Next: user reviews source quality."],
                    model + "\n\nCollected sources:\n" + source_text,
                )
            return RuntimeResult(
                RuntimeStatus.PAUSED,
                "Sources collected, model missing",
                thought + [f"[{ai_name}] Sources were collected, but no model backend summarized them."],
                [f"[{ai_name}] Stopped before fake research summary."],
                ["Next: connect model backend, then summarize."],
                "Collected sources:\n" + source_text,
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
            "Research waiting for real source review",
            thought + [f"[{ai_name}] No search API/source reader is connected."],
            [f"[{ai_name}] Browser search opened." if opened else f"[{ai_name}] Browser search could not open."],
            ["Next: collect sources -> read sources -> summarize -> cite -> then complete."],
            "Research paused. It cannot truthfully complete until sources are collected and reviewed.",
            opened_url=url if opened else "",
        )

    def _run_coder(self, task, ai_name, meta, knowledge, thought):
        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "coding"))
        if model:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Coder completed", thought + [f"[{ai_name}] Model backend produced coding output using Knowledge context."], [f"[{ai_name}] Returned code analysis/draft."], ["Next: review before applying changes."], model)

        result = (
            "Local Coder fallback:\n"
            "1. I can analyze pasted code or error text.\n"
            "2. I can draft a patch plan.\n"
            "3. I will not edit files or run commands without approval.\n\n"
            f"Task received:\n{task}\n\n"
            "Suggested next action: paste the exact error/log or file path and ask for a patch."
        )
        return RuntimeResult(RuntimeStatus.COMPLETED, "Coder local fallback completed", thought + [f"[{ai_name}] No model backend; using safe code fallback."], [f"[{ai_name}] Produced code-task triage."], ["Next: provide file/error for deeper patch."], result)

    def _run_writer(self, task, ai_name, meta, knowledge, thought):
        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "writing"))
        if model:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Writer completed", thought + [f"[{ai_name}] Model backend produced writing output using Knowledge context."], [f"[{ai_name}] Returned draft/rewrite."], ["Next: revise tone or export after approval."], model)

        result = (
            "Local Writing fallback:\n"
            f"Working title: {task[:80]}\n\n"
            "Outline:\n"
            "1. Purpose / main idea\n"
            "2. Key points\n"
            "3. Draft body\n"
            "4. Closing / call to action\n\n"
            "Connect Ollama/OpenAI for full prose generation."
        )
        return RuntimeResult(RuntimeStatus.COMPLETED, "Writer local fallback completed", thought + [f"[{ai_name}] No model backend; produced writing scaffold."], [f"[{ai_name}] Built outline scaffold."], ["Next: connect model for full draft."], result)

    def _run_planner(self, task, ai_name, meta, knowledge, thought):
        result = (
            f"Plan for: {task}\n\n"
            "1. Define the exact desired outcome.\n"
            "2. List resources and blockers.\n"
            "3. Break work into 3-5 testable steps.\n"
            "4. Do the smallest safe step first.\n"
            "5. Verify output before outward/file/system actions.\n\n"
            "Risks:\n"
            "- Scope creep\n"
            "- Fake completion\n"
            "- Missing executor/backend\n\n"
            "Approval point: anything that changes files, sends data, or controls apps."
        )
        return RuntimeResult(RuntimeStatus.COMPLETED, "Planner completed", thought + [f"[{ai_name}] Built a local governed plan."], [f"[{ai_name}] Planner capability executed locally."], ["Next: approve or adjust plan."], result)

    def _run_document_processor(self, task, ai_name, meta, knowledge, thought):
        file_path = self._extract_path(task)
        if file_path and file_path.exists() and file_path.is_file():
            raw = file_path.read_text(encoding="utf-8", errors="replace")
            summary = self._simple_summary(raw)
            return RuntimeResult(RuntimeStatus.COMPLETED, "Document processed", thought + [f"[{ai_name}] Read local document."], [f"[{ai_name}] Processed: {file_path}"], ["Next: review before export/save."], summary)

        inline = self._extract_inline_text(task)
        if inline:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Inline document processed", thought + [f"[{ai_name}] Processed inline document text."], [f"[{ai_name}] Extracted local summary."], ["Next: review output."], self._simple_summary(inline))

        return RuntimeResult(RuntimeStatus.PAUSED, "Document needed", thought + [f"[{ai_name}] No readable document or inline text found."], [f"[{ai_name}] Paused for document input."], ["Next: paste document text or include file: C:\\path\\file.txt"], "Document Processor needs text or a readable local file path.")

    def _run_notebook(self, task, ai_name, meta, knowledge, thought):
        stamp = time.strftime("%Y%m%d_%H%M%S")
        path = self.notes_dir / f"note_{stamp}.txt"
        path.write_text(task + "\n", encoding="utf-8")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Note saved", thought + [f"[{ai_name}] Notebook wrote a local note."], [f"[{ai_name}] Saved note: {path}"], ["Next: ask to retrieve notes by date/topic."], f"Saved note to:\n{path}")

    def _run_archive(self, task, ai_name, meta, knowledge, thought):
        base = Path(meta.get("archive_path") or self.archive_dir)
        try:
            base.mkdir(parents=True, exist_ok=True)
        except Exception:
            base = self.archive_dir
            base.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        path = base / f"archive_{stamp}.txt"
        path.write_text(task + "\n", encoding="utf-8")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Archived", thought + [f"[{ai_name}] Archive wrote a local artifact."], [f"[{ai_name}] Archived item: {path}"], ["Next: retrieve by archive path/date."], f"Archived to:\n{path}")

    def _run_tutor(self, task, ai_name, meta, knowledge, thought):
        result = (
            f"Tutor mode for: {task}\n\n"
            "Explanation path:\n"
            "1. Define the concept.\n"
            "2. Show a small example.\n"
            "3. Ask one check-for-understanding question.\n"
            "4. Adjust difficulty based on the answer.\n\n"
            "Question: What part should I explain first?"
        )
        return RuntimeResult(RuntimeStatus.COMPLETED, "Tutor completed", thought + [f"[{ai_name}] Tutor capability executed locally."], [f"[{ai_name}] Created lesson scaffold."], ["Next: user answers check question."], result)

    def _run_business(self, task, ai_name, meta, knowledge, thought):
        result = (
            f"Business workflow for: {task}\n\n"
            "Draft-safe workflow:\n"
            "1. Identify audience/customer/internal team.\n"
            "2. Draft response or SOP.\n"
            "3. Flag risk/approval items.\n"
            "4. Wait for review before sending or publishing.\n\n"
            "Approval required before external send/publish."
        )
        return RuntimeResult(RuntimeStatus.COMPLETED, "Business workflow completed", thought + [f"[{ai_name}] Business workflow executed locally."], [f"[{ai_name}] Produced draft-safe workflow."], ["Next: review and approve outward actions."], result)

    def _prompt(self, task, ai_name, meta, knowledge, mode):
        return (
            f"You are {ai_name}, a Command Nexus governed AI.\n"
            f"Mode: {mode}\n"
            f"Use case: {meta.get('use_case', '')}\n"
            f"Abilities: {meta.get('abilities') or meta.get('capabilities') or []}\n"
            f"Libraries: {meta.get('libraries', [])}\n"
            f"Guardrails: {meta.get('guardrails', [])}\n\n"
            f"Knowledge / Intelligence Profile:\n{self._knowledge_excerpt(knowledge)}\n\n"
            f"Task:\n{task}\n\n"
            "Do not claim external actions were performed unless a tool actually performed them."
        )

    def _call_model(self, prompt: str) -> str:
        """Route to a model backend per the user's preference.
        auto       -> offline (Ollama) first, then cloud (OpenAI)
        offline/local_only -> Ollama only (learns-with-user, works offline)
        cloud      -> OpenAI only
        """
        backend = getattr(self, "model_backend", "auto")
        if backend == "cloud":
            return self._call_openai(prompt)
        if backend in ("offline", "local_only"):
            return self._call_ollama(prompt)
        # auto
        out = self._call_ollama(prompt)
        if out:
            return out
        return self._call_openai(prompt)

    def _call_ollama(self, prompt: str) -> str:
        try:
            payload = {"model": self.ollama_model, "prompt": prompt, "stream": False}
            req = urllib.request.Request(
                self.ollama_url + "/api/generate",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
            return (data.get("response") or "").strip()
        except Exception:
            return ""

    def _call_openai(self, prompt: str) -> str:
        if not self.openai_api_key:
            return ""
        try:
            payload = {
                "model": self.openai_model,
                "messages": [
                    {"role": "system", "content": "You are a governed Command Nexus runtime backend. Be honest about what was actually done."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.4,
            }
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "Authorization": "Bearer " + self.openai_api_key},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"OpenAI backend error: {e}"

    def _brave_search(self, query: str) -> list[dict[str, str]]:
        try:
            url = "https://api.search.brave.com/res/v1/web/search?q=" + urllib.parse.quote_plus(query)
            req = urllib.request.Request(
                url,
                headers={"Accept": "application/json", "X-Subscription-Token": self.brave_api_key},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
            return data.get("web", {}).get("results", []) or []
        except Exception:
            return []

    def _extract_path(self, task: str) -> Path | None:
        m = re.search(r'file:\s*["\']?([^"\']+)["\']?', task, re.I)
        if m:
            return Path(m.group(1).strip())
        q = re.findall(r'["\']([^"\']+\.(?:txt|md|py|json|csv|log))["\']', task, re.I)
        if q:
            return Path(q[0])
        return None

    def _extract_inline_text(self, task: str) -> str:
        for token in ["text:", "document:", "content:"]:
            idx = task.lower().find(token)
            if idx >= 0:
                return task[idx + len(token):].strip()
        return ""

    def _simple_summary(self, raw: str) -> str:
        words = raw.split()
        lines = [x.strip() for x in raw.splitlines() if x.strip()]
        preview = "\n".join(lines[:12])
        return (
            f"Document summary:\n"
            f"- Characters: {len(raw)}\n"
            f"- Words: {len(words)}\n"
            f"- Non-empty lines: {len(lines)}\n\n"
            f"Preview / first lines:\n{preview}"
        )
