
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

from .settings_manager import SettingsManager
from .adaptive_memory import AdaptiveMemoryStore
from .tool_executor import ToolExecutor, ToolResult
from .model_registry import ModelRegistry


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

    def __init__(self, settings: SettingsManager | None = None):
        self.home = Path.home() / ".command_nexus"
        self.notes_dir = self.home / "notes"
        self.archive_dir = self.home / "runtime_archive"
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        self._settings = settings or SettingsManager()
        self._settings.initialize()
        s = self._settings.get()

        self.ai_backend = (os.environ.get("COMMAND_NEXUS_AI_BACKEND") or s.ai_backend or "ollama").strip().lower()
        self.openai_api_key = (os.environ.get("OPENAI_API_KEY") or s.openai_api_key or "").strip()
        self.openai_model = (os.environ.get("COMMAND_NEXUS_OPENAI_MODEL") or s.openai_model or "gpt-4o-mini").strip()

        self.ollama_url = (os.environ.get("COMMAND_NEXUS_OLLAMA_URL") or s.ollama_url or "http://127.0.0.1:11434").rstrip("/")
        self.ollama_model = (os.environ.get("COMMAND_NEXUS_OLLAMA_MODEL") or s.ollama_model or "llama3.1").strip()

        self.brave_api_key = (os.environ.get("BRAVE_SEARCH_API_KEY") or s.brave_api_key or "").strip()

        self._memory = AdaptiveMemoryStore(self._settings)
        self._tools = ToolExecutor(self._settings)
        self._models = ModelRegistry(self._settings)
        self._response_cache: dict[str, str] = {}

    def save_memory(
        self,
        ai_uuid: str,
        content: str,
        tags: list[str] | None = None,
        source: str = "mission",
        importance: float = 0.5,
    ) -> Any:
        """Save a learned fact/preference to the local adaptive memory store."""
        if not ai_uuid or not content:
            return None
        return self._memory.add(ai_uuid, content, tags=tags, source=source, importance=importance)

    def _learn_from_mission(self, ai_uuid: str, task: str, intent: str, result: Any) -> None:
        """Automatically extract and store memories from a mission attempt."""
        if not ai_uuid or not self._memory:
            return

        status = getattr(result, "status", None)
        title = getattr(result, "title", "Mission")

        # Save a concise mission summary for completed missions, or an attempt record otherwise.
        if status == "completed":
            summary = f"Mission: {task} | Intent: {intent} | Outcome: {title}"
            self._memory.add(
                ai_uuid,
                summary,
                tags=[intent.lower(), "mission"],
                source="mission",
                importance=0.5,
            )
        else:
            attempt = f"Attempted: {task} | Intent: {intent} | Status: {status}"
            self._memory.add(
                ai_uuid,
                attempt,
                tags=[intent.lower(), "attempt"],
                source="mission",
                importance=0.3,
            )

        # Extract preference / fact statements from the user task regardless of outcome.
        prefs = self._extract_preferences(task)
        for p in prefs:
            self._memory.add(
                ai_uuid,
                p,
                tags=["preference", "user_input"],
                source="user_input",
                importance=0.85,
            )

    def _extract_preferences(self, text: str) -> list[str]:
        """Simple heuristic extraction of preference/fact statements from user text."""
        text = (text or "").strip()
        if not text:
            return []

        cues = ["prefer", "like", "always", "never", "want", "need", "use", "remember", "dislike", "hate"]
        bare_phrases = {"remember that", "remember this", "remember to"}
        sentences = [s.strip() for s in re.split(r"[.!?\n]", text) if s.strip()]
        found: list[str] = []
        for s in sentences:
            lower = s.lower()
            if len(s) < 10 or len(s) > 300:
                continue
            if not any(c in lower for c in cues):
                continue
            if any(p in lower for p in bare_phrases):
                continue
            # Require at least 4 words so bare cues like 'I want that' are skipped.
            if len(s.split()) < 4:
                continue
            found.append(s)
        return found

    def suggest_next_steps(self, ai_uuid: str, ai_name: str = "AI") -> list[str]:
        """
        Propose next actions based on the AI's accumulated local memory.
        Uses the configured model if available; otherwise falls back to heuristics.
        """
        if not ai_uuid or not self._memory:
            return []

        memories = self._memory.get_recent(ai_uuid, 15)
        if not memories:
            return ["Start a mission to build up local memory and preferences."]

        memory_text = "\n".join(f"- [{m.source}] {m.content}" for m in memories)

        prompt = (
            f"You are {ai_name}, a Command Nexus governed AI.\n"
            "Based on the user's recent local memory below, suggest 2-3 concrete next actions the user might want.\n"
            "Keep each suggestion under 100 characters. Be helpful and privacy-aware.\n\n"
            f"Recent memory:\n{memory_text}\n\n"
            "Suggestions (one per line, no numbering):"
        )

        model_response = self._call_model(prompt)
        if model_response:
            suggestions = [line.strip("-• ").strip() for line in model_response.splitlines() if line.strip()]
            return [s for s in suggestions if s][:5]

        # Offline heuristic fallback.
        suggestions: list[str] = []
        project_memories = [m for m in memories if "project" in m.tags or "project" in m.content.lower()]
        if project_memories:
            suggestions.append(f"Continue working on {project_memories[0].content[:80]}...")
        preference_memories = [m for m in memories if "preference" in m.tags]
        if preference_memories:
            suggestions.append(f"Apply your preference: {preference_memories[0].content[:80]}...")
        if any("mission" in m.tags for m in memories):
            suggestions.append("Review recent mission outcomes and refine the next task.")
        if not suggestions:
            suggestions.append("Keep using the AI to build more context and preferences.")
        return suggestions[:5]

    def health_check(self) -> dict[str, Any]:
        """Return the current backend reachability and selected model status."""
        result: dict[str, Any] = {
            "backend": self.ai_backend,
            "reachable": False,
            "message": "",
            "models": [],
            "selected_model": "",
        }
        try:
            if self.ai_backend == "openai":
                if not self.openai_api_key:
                    result["message"] = "OpenAI backend selected but no API key configured."
                    return result
                req = urllib.request.Request(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": "Bearer " + self.openai_api_key},
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8", errors="replace"))
                models = [m.get("id", "") for m in data.get("data", [])]
                result["reachable"] = True
                result["models"] = models
                result["selected_model"] = self.openai_model
                result["message"] = (
                    f"OpenAI connected. Model '{self.openai_model}' is available."
                    if self.openai_model in models
                    else f"OpenAI connected. Model '{self.openai_model}' not found in available models."
                )
            else:
                url = self.ollama_url + "/api/tags"
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8", errors="replace"))
                models = [m.get("name", "") for m in data.get("models", [])]
                result["reachable"] = True
                result["models"] = models
                result["selected_model"] = self.ollama_model
                result["message"] = (
                    f"Ollama connected. Model '{self.ollama_model}' is available."
                    if self.ollama_model in models
                    else f"Ollama connected. Model '{self.ollama_model}' not found. Available: {', '.join(models[:5]) or 'none'}."
                )
        except Exception as e:
            result["message"] = f"{self.ai_backend} backend unreachable: {e}"
        return result

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
            result = RuntimeResult(
                RuntimeStatus.PAUSED,
                "Capability not attached",
                thought + [f"[{ai_name}] Required capability is not attached for this task."],
                [f"[{ai_name}] Paused instead of pretending unsupported capability exists."],
                ["Next: add the needed capability in AI Forge or choose an AI that has it."],
                f"Required capability missing for this task: {intent}",
            )
            self._learn_from_mission(ai_uuid, task, intent, result)
            return result

        if intent == "Research":
            result = self._run_research(task, ai_name, meta, knowledge, thought)
        elif intent == "Coder":
            result = self._run_coder(task, ai_name, meta, knowledge, thought)
        elif intent == "Creative Writing":
            result = self._run_writer(task, ai_name, meta, knowledge, thought)
        elif intent == "Planner":
            result = self._run_planner(task, ai_name, meta, knowledge, thought)
        elif intent == "Document Processor":
            result = self._run_document_processor(task, ai_name, meta, knowledge, thought)
        elif intent == "Notebook":
            result = self._run_notebook(task, ai_name, meta, knowledge, thought)
        elif intent == "Archive":
            result = self._run_archive(task, ai_name, meta, knowledge, thought)
        elif intent == "Tutor":
            result = self._run_tutor(task, ai_name, meta, knowledge, thought)
        elif intent == "Business Workflow":
            result = self._run_business(task, ai_name, meta, knowledge, thought)
        elif intent == "Tool User":
            result = self._run_tool_user(task, ai_name, meta, knowledge, thought)
        else:
            result = self._run_chat(task, ai_name, meta, knowledge, thought)

        self._learn_from_mission(ai_uuid, task, intent, result)
        return result

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

        if any(x in t for x in [
            "research", "look up", "lookup", "search", "find sources", "sources", "citation",
            "cite", "verify", "current", "latest", "web search", "search the web", "websearch",
            "internet", "news", "game mechanics",
        ]):
            return "Research"

        if any(x in t for x in ["code", "bug", "python", "javascript", "html", "css", "function", "class", "error", "traceback", "fix script", "patch"]):
            return "Coder"

        if any(x in t for x in [
            "read file", "show file", "display file", "open file", "cat file", "view file",
            "write file", "create file", "save file", "write to file", "create a file",
            "list directory", "list files", "list folder", "list dir", "show files",
            "delete file", "delete folder", "delete directory", "remove file", "remove folder",
            "move file", "move folder", "rename file", "rename folder",
            "run command", "run shell", "execute ", "shell command", "terminal ",
            "install", "uninstall", "download", "open app", "click", "type into",
            "send email", "upload", "publish", "submit",
        ]):
            return "Tool User"

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

    def _memory_excerpt(self, ai_uuid: str, task: str, limit: int = 2000) -> str:
        """Retrieve the most relevant learned memories for this AI and task."""
        if not ai_uuid or not self._memory:
            return ""
        memories = self._memory.search(ai_uuid, task)[:12]
        if not memories:
            memories = self._memory.get_recent(ai_uuid, 6)
        if not memories:
            return ""
        lines = ["Learned context from previous interactions:"]
        total = 0
        for m in memories:
            entry = f"- [{m.source}] {m.content}"
            if total + len(entry) > limit:
                lines.append("[Additional memories omitted for prompt size]")
                break
            lines.append(entry)
            total += len(entry)
        return "\n".join(lines)

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

        return RuntimeResult(
            RuntimeStatus.PAUSED,
            "Research waiting for real source review",
            thought + [f"[{ai_name}] No search API/source reader is connected."],
            [f"[{ai_name}] Research paused; URL ready for manual review: {url}"],
            ["Next: collect sources -> read sources -> summarize -> cite -> then complete."],
            "Research paused. It cannot truthfully complete until sources are collected and reviewed.",
            opened_url=url,
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

    def _run_tool_user(self, task, ai_name, meta, knowledge, thought):
        """
        Fast, rule-based local tool execution.

        No model call is made here. We extract the action and target from the
        user's text using simple heuristics, execute through ToolExecutor, and
        report exactly what happened. This keeps the system usable on small local
        models (7B/8B and below) and avoids loading larger models just to route
        file commands.
        """
        t = task.lower()

        # Shell commands (high risk — kept inside workspace by default)
        if any(x in t for x in ["run command", "run shell", "execute ", "shell command", "terminal "]):
            cmd = re.sub(r"^(?:run|execute|shell|command|terminal)[:\s]*", "", task, flags=re.I).strip()
            if cmd:
                res = self._tools.run_shell(cmd)
                return RuntimeResult(
                    RuntimeStatus.COMPLETED if res.ok else RuntimeStatus.FAILED,
                    res.action,
                    thought + [f"[{ai_name}] Executed shell command via ToolExecutor."],
                    [res.message],
                    ["Next: review stdout/stderr if needed."],
                    f"Command: {res.data.get('command', cmd)}\nExit: {res.data.get('returncode', '?')}\n\nSTDOUT:\n{res.data.get('stdout', '')}\n\nSTDERR:\n{res.data.get('stderr', '')}",
                )

        # Write / create file
        if any(x in t for x in ["write file", "create file", "save file", "write to file", "create a file"]):
            path = self._extract_path(task)
            content = self._extract_inline_text(task)
            if not path:
                return RuntimeResult(RuntimeStatus.PAUSED, "No file path found", thought + [f"[{ai_name}] Could not determine which file to write."], ["Provide a file path or filename, e.g. 'write file notes.txt content: hello'"], [], "")
            if not content:
                return RuntimeResult(RuntimeStatus.PAUSED, "No content found", thought + [f"[{ai_name}] Could not determine what content to write."], ["Provide content after 'content:' or in quotes."], [], "")
            res = self._tools.write_file(path, content)
            return RuntimeResult(
                RuntimeStatus.COMPLETED if res.ok else RuntimeStatus.FAILED,
                res.action,
                thought + [f"[{ai_name}] {res.message}"],
                [res.message],
                ["Next: read the file back to verify."],
                res.message,
            )

        # Delete file/dir
        if any(x in t for x in ["delete file", "delete folder", "delete directory", "remove file", "remove folder"]):
            path = self._extract_path(task)
            if not path:
                return RuntimeResult(RuntimeStatus.PAUSED, "No path found", thought + [f"[{ai_name}] Could not determine which file or folder to delete."], ["Provide a path, e.g. 'delete file old.txt'"], [], "")
            res = self._tools.delete_file(path)
            return RuntimeResult(
                RuntimeStatus.COMPLETED if res.ok else RuntimeStatus.FAILED,
                res.action,
                thought + [f"[{ai_name}] {res.message}"],
                [res.message],
                ["Next: confirm deletion or list parent directory."],
                res.message,
            )

        # Move / rename
        if any(x in t for x in ["move file", "move folder", "rename file", "rename folder"]):
            paths = re.findall(r'["\']([^"\']+)["\']', task)
            if len(paths) < 2:
                return RuntimeResult(RuntimeStatus.PAUSED, "Move needs two paths", thought + [f"[{ai_name}] Need source and destination paths."], ["Use quotes, e.g. 'move file \"a.txt\" to \"b.txt\"'"], [], "")
            res = self._tools.move_file(paths[0], paths[1])
            return RuntimeResult(
                RuntimeStatus.COMPLETED if res.ok else RuntimeStatus.FAILED,
                res.action,
                thought + [f"[{ai_name}] {res.message}"],
                [res.message],
                ["Next: verify the destination."],
                res.message,
            )

        # Read file (default or explicit)
        if any(x in t for x in ["read file", "show file", "display file", "open file", "cat file", "view file"]):
            path = self._extract_path(task)
            if not path:
                return RuntimeResult(RuntimeStatus.PAUSED, "No file path found", thought + [f"[{ai_name}] Could not determine which file to read."], ["Provide a file path, e.g. 'read file notes.txt'"], [], "")
            res = self._tools.read_file(path)
            return RuntimeResult(
                RuntimeStatus.COMPLETED if res.ok else RuntimeStatus.FAILED,
                res.action,
                thought + [f"[{ai_name}] {res.message}"],
                [res.message],
                ["Next: summarize or edit the content."],
                res.data.get("content", res.message),
            )

        # List directory
        if any(x in t for x in ["list directory", "list files", "list folder", "list dir", "show files", "dir "]):
            path = self._extract_path(task) or "."
            res = self._tools.list_dir(path)
            return RuntimeResult(
                RuntimeStatus.COMPLETED if res.ok else RuntimeStatus.FAILED,
                res.action,
                thought + [f"[{ai_name}] {res.message}"],
                [res.message],
                ["Next: read or modify a specific file."],
                "\n".join(f"- {e['name']} ({e['type']})" for e in res.data.get("entries", [])),
            )

        # Fallback: if we got here, we don't know what tool to run
        return RuntimeResult(
            RuntimeStatus.PAUSED,
            "Tool intent unclear",
            thought + [f"[{ai_name}] Detected Tool User intent but could not map it to a supported action."],
            ["Supported: read file, write file, list files, move file, delete file, run shell command."],
            ["Next: rephrase with a clear action and path."],
            "",
        )

    def _prompt(self, task, ai_name, meta, knowledge, mode):
        ai_uuid = str(meta.get("uuid", ""))
        memory_text = self._memory_excerpt(ai_uuid, task)
        return (
            f"You are {ai_name}, a Command Nexus governed AI.\n"
            f"Mode: {mode}\n"
            f"Use case: {meta.get('use_case', '')}\n"
            f"Abilities: {meta.get('abilities') or meta.get('capabilities') or []}\n"
            f"Libraries: {meta.get('libraries', [])}\n"
            f"Guardrails: {meta.get('guardrails', [])}\n\n"
            f"Knowledge / Intelligence Profile:\n{self._knowledge_excerpt(knowledge)}\n\n"
            f"{memory_text}\n\n"
            f"Task:\n{task}\n\n"
            "Do not claim external actions were performed unless a tool actually performed them."
        )

    def _call_model(self, prompt: str, model: str | None = None) -> str:
        cache_key = f"{model or self.ollama_model}:{hash(prompt) & 0xFFFFFFFF}"
        if cache_key in self._response_cache:
            return self._response_cache[cache_key]

        if self.ai_backend == "openai":
            out = self._call_openai(prompt)
            if out and not out.startswith("OpenAI backend error"):
                self._response_cache[cache_key] = out
                return out
            out = self._call_ollama(prompt, model=model)
            if out:
                self._response_cache[cache_key] = out
            return out

        # Default / ollama: local-first, fall back to OpenAI if configured
        out = self._call_ollama(prompt, model=model)
        if out:
            self._response_cache[cache_key] = out
            return out
        out = self._call_openai(prompt)
        if out:
            self._response_cache[cache_key] = out
        return out

    def _call_ollama(self, prompt: str, model: str | None = None) -> str:
        try:
            payload = {"model": model or self.ollama_model, "prompt": prompt, "stream": False}
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
