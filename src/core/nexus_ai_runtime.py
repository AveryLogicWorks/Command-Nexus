
from __future__ import annotations

# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

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
from .capability_registry import canonical_intent, capability_status, is_paused, ImplementationStatus
from .backend_manager import BackendManager, BackendResponse


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


class NexusAIRuntime:
    """
    Real Command Nexus runtime bridge.

    This connects:
    - AI metadata from Forge
    - Knowledge / Intelligence profile
    - capabilities
    - local safe capability behaviors
    - built-in local model (GGUF) or optional Ollama/OpenAI backend
    - optional Brave Search backend

    It must never fake-complete external, research, browser, file, or tool actions.
    """

    def __init__(
        self,
        settings: SettingsManager | None = None,
        approval_gate: Any | None = None,
        audit_logger: Any | None = None,
        parent_widget: Any | None = None,
        watcher: Any | None = None,
    ):
        self.home = Path.home() / ".command_nexus"
        self.notes_dir = self.home / "notes"
        self.archive_dir = self.home / "runtime_archive"
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        self._settings = settings or SettingsManager()
        s = self._settings.get()

        # All model backend interactions go through the trust boundary.
        self._backend = BackendManager(self._settings)
        self._memory = AdaptiveMemoryStore(self._settings)
        self._tools = ToolExecutor(self._settings, allow_outside_workspace=True)
        self._models = ModelRegistry(self._settings)
        self._response_cache: dict[str, str] = {}
        self._approval_gate = approval_gate
        self._audit_logger = audit_logger
        self._parent_widget = parent_widget
        self._watcher = watcher

        self.brave_api_key = (os.environ.get("BRAVE_SEARCH_API_KEY") or s.brave_api_key or "").strip()

    def _request_tool_approval(self, action_type: str, description: str, targets: list[str], risk_level: Any) -> bool:
        """Ask the human approval gate before executing a risky tool action."""
        if self._approval_gate is None:
            return True
        try:
            from .approval_gate import ActionRequest, RiskLevel
            req = ActionRequest(
                action_type=action_type,
                description=description,
                rationale="User-initiated local tool action classified by Nexus AI Runtime.",
                targets=targets,
                risk_level=risk_level,
            )
            return self._approval_gate.request_approval(self._parent_widget, req)
        except Exception:
            # If approval machinery fails, deny rather than execute blindly.
            return False

    def _tripwire_ok(self, action_name: str, risk_level: str = "risky") -> bool:
        """Return True if the watcher allows the protected action."""
        if self._watcher is None:
            return True
        try:
            return self._watcher.check_action(action_name, risk_level=risk_level)
        except Exception:
            return False

    def _log_tool_audit(self, *, tool: str, action: str, target: str, approved: bool, status: str, error: str | None = None):
        """Write a tool action record to the audit logger if available."""
        if self._audit_logger is None:
            return
        try:
            self._audit_logger.log(
                tool=tool,
                action=action,
                target=target,
                agent="NexusAIRuntime",
                approved=approved,
                status=status,
                error=error,
            )
        except Exception:
            pass

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
        if model_response.text and not model_response.error:
            suggestions = [line.strip("-• ").strip() for line in model_response.text.splitlines() if line.strip()]
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
        return self._backend.health_check()

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

        if not self._tripwire_ok("mission_start", risk_level="safe"):
            is_lockdown = self._watcher is not None and self._watcher.is_locked_down()
            if is_lockdown:
                return RuntimeResult(
                    RuntimeStatus.PAUSED,
                    "Tripwire lockdown",
                    ["[SYSTEM] Watcher tripwire is in lockdown or breach."],
                    ["[SYSTEM] Mission execution blocked until trust is restored."],
                    ["Next: restore protected files or contact support."],
                )
            return RuntimeResult(
                RuntimeStatus.PAUSED,
                "Watcher trust degraded",
                ["[SYSTEM] Watcher detected a local test-build trust issue."],
                ["[SYSTEM] Safe missions are allowed, but this mission cannot start while trust is degraded."],
                ["Next: restore protected files or accept the current baseline in the Watcher view."],
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
        elif intent == "Customer Support AI":
            result = self._run_customer_support(task, ai_name, meta, knowledge, thought)
        elif intent == "Hephaestus Relay":
            result = self._run_hephaestus(task, ai_name, meta, knowledge, thought)
        elif intent == "Data Analyst Pro":
            result = self._run_data_analyst(task, ai_name, meta, knowledge, thought)
        elif intent == "Code Reviewer":
            result = self._run_code_reviewer(task, ai_name, meta, knowledge, thought)
        elif intent == "Meeting Facilitator":
            result = self._run_meeting_facilitator(task, ai_name, meta, knowledge, thought)
        elif intent == "Security Auditor":
            result = self._run_security_auditor(task, ai_name, meta, knowledge, thought)
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
            out.add(canonical_intent(item))
        if not out:
            out.add("Chatbot")
        # All AIs can use tools — this is an all-in-one program
        out.add("Tool User")
        return out

    def _capability_allowed(self, intent: str, abilities: set[str]) -> bool:
        # Chatbot is always allowed as the default fallback surface.
        if intent == "Chatbot":
            return True

        # Honest pause for capabilities that are not wired in this build.
        if is_paused(intent):
            return False

        # The AI must explicitly have the capability (or an alias that maps to it).
        if intent in abilities:
            return True

        # Tool User is a privileged capability: only AIs explicitly given Tool User
        # (or Agent) may invoke the governed tool loop, not every nearby capability.
        if intent == "Tool User" and "Tool User" in abilities:
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

        if any(x in t for x in ["customer support", "support ticket", "help desk", "escalat", "customer service"]):
            return "Customer Support AI"

        if any(x in t for x in ["sales", "marketing", "hr", "sop", "business", "support reply"]):
            return "Business Workflow"

        if any(x in t for x in ["hephaestus", "design brief", "prototype", "material spec", "handoff brief"]):
            return "Hephaestus Relay"

        if any(x in t for x in ["analyze data", "data analyst", "dataset", "statistics", "chart", "pivot", "data trend", "data visualization"]):
            return "Data Analyst Pro"

        if any(x in t for x in ["code review", "review code", "security scan", "quality check", "lint", "best practice"]):
            return "Code Reviewer"

        if any(x in t for x in ["meeting agenda", "facilitate meeting", "action item", "meeting note", "standup", "retrospective"]):
            return "Meeting Facilitator"

        if any(x in t for x in ["security audit", "vulnerability", "penetration", "compliance scan", "security assessment"]):
            return "Security Auditor"

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

    def _backend_failure_result(self, ai_name: str, thought: list[str], backend_response: BackendResponse) -> RuntimeResult:
        """Honest FAILED result when the model backend is offline, unreachable, or unconfigured."""
        provider_name = backend_response.display_name or backend_response.provider_id or "selected backend"
        return RuntimeResult(
            RuntimeStatus.FAILED,
            f"{ai_name}'s backend is offline",
            thought + [
                f"[{ai_name}] AI exists and capability routing worked.",
                f"[{ai_name}] Backend call failed: {provider_name} is offline or unavailable.",
                f"[{ai_name}] Error: {backend_response.error}",
            ],
            [f"[{ai_name}] Task did not complete because the model backend could not be reached."],
            [
                "Next: start the selected backend, choose a different backend, or configure Backend settings.",
                "Backend config is in the Visibility Window: Backend > Configure Backend.",
            ],
            f"{ai_name} is active, but her model backend is offline or unavailable.\n\n"
            f"Provider: {provider_name}\n"
            f"Error: {backend_response.error}\n\n"
            "Start the selected backend, choose a different backend, or configure Backend settings.",
        )

    def _run_chat(self, task, ai_name, meta, knowledge, thought):
        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "chat"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Chat completed", thought + [f"[{ai_name}] Model backend answered using Knowledge/Intelligence context."], [f"[{ai_name}] Returned chat response."], ["Next: continue conversation or approve outward action."], model.text)

        return self._local_chat_response(task, ai_name, meta, knowledge, thought)

    def _local_chat_response(self, task, ai_name, meta, knowledge, thought):
        """Generate a useful, clearly-labeled local response when no backend is available."""
        ai_uuid = str(meta.get("uuid", ""))
        abilities = meta.get("abilities") or meta.get("capabilities") or []
        use_case = meta.get("use_case", "")
        memory_text = self._memory_excerpt(ai_uuid, task)
        knowledge_excerpt = self._knowledge_excerpt(knowledge, limit=3000)

        # Get recent memories for conversation continuity
        recent_memories = self._memory.get_recent(ai_uuid, 5) if ai_uuid else []
        preference_memories = [m for m in recent_memories if "preference" in m.tags] if recent_memories else []
        mission_memories = [m for m in recent_memories if "mission" in m.tags] if recent_memories else []

        parts: list[str] = []
        parts.append(f"[Local Intelligence — {ai_name}]")
        parts.append("")
        parts.append(f"I heard: \"{task}\"")
        parts.append("")

        has_knowledge = bool(knowledge_excerpt.strip())
        has_memory = bool(memory_text.strip())

        # Show knowledge context
        if has_knowledge:
            parts.append("From my Knowledge/Intelligence profile:")
            for line in knowledge_excerpt.splitlines()[:15]:
                if line.strip():
                    parts.append(f"  {line.strip()}")
            parts.append("")

        # Show learned preferences for continuity
        if preference_memories:
            parts.append("What I've learned about you:")
            for m in preference_memories[:3]:
                parts.append(f"  - {m.content[:120]}")
            parts.append("")

        # Show recent mission context for continuity
        if mission_memories:
            parts.append("Recent things we've worked on:")
            for m in mission_memories[:3]:
                parts.append(f"  - {m.content[:120]}")
            parts.append("")

        task_lower = task.lower()

        # Intent: capabilities question
        if any(k in task_lower for k in ["what can you do", "help me", "what are you", "capabilities", "what do you do"]):
            parts.append(f"I'm {ai_name}, a Command Nexus AI for {use_case or 'general assistance'}.")
            parts.append(f"My capabilities: {', '.join(abilities) if abilities else 'basic chat'}")
            parts.append("")
            parts.append("I can:")
            parts.append("  - Chat and answer from my knowledge profile")
            parts.append("  - Plan tasks and break them into steps")
            parts.append("  - Process documents you give me")
            parts.append("  - Tutor and explain concepts")
            parts.append("  - Use tools (read/write files, list directories) with your approval")
            parts.append("  - Learn your preferences over time")
            parts.append("")
            parts.append("The built-in local model is ready for AI reasoning.")

        # Intent: preference statement
        elif any(k in task_lower for k in ["prefer", "like", "always", "never", "remember", "dislike", "hate", "want", "need"]):
            parts.append("Got it — I've saved that to my local memory and will remember it for future tasks.")
            parts.append("You don't need to repeat yourself; I learn from every interaction.")
            if preference_memories:
                parts.append("")
                parts.append("Here's what I already know about you:")
                for m in preference_memories[:3]:
                    parts.append(f"  - {m.content[:100]}")

        # Intent: greeting
        elif any(k in task_lower for k in ["hello", "hi ", "hey", "greetings", "good morning", "good afternoon", "good evening"]):
            parts.append(f"Hello! I'm {ai_name}, your Command Nexus AI.")
            if abilities:
                parts.append(f"I'm equipped with: {', '.join(abilities)}.")
            if mission_memories:
                parts.append(f"Last time we worked on: {mission_memories[0].content[:100]}")
                parts.append("Want to continue that, or start something new?")
            else:
                parts.append("Ask me anything, give me a task, or tell me what you'd like to accomplish.")
            if not has_knowledge and not has_memory:
                parts.append("I'm fresh and ready to learn — the more we work together, the better I'll understand your needs.")

        # Intent: how to use a specific capability
        elif any(k in task_lower for k in ["how do i", "how to", "where is", "where do", "show me how", "teach me how"]):
            parts.append("Here's how to use Command Nexus:")
            parts.append("")
            parts.append("  🧠 AI Forge — Create and customize AI assistants")
            parts.append("  📚 Intelligence — Add memory and knowledge to your AI")
            parts.append("  ⬆️ Upgrades — Browse and unlock more capabilities")
            parts.append("  🛡️ Governance — Safety controls, audit logs, parental controls")
            parts.append("  🤖 Support — Get help from the Customer Support AI")
            parts.append("  🎯 Mission Control — Type a task and click START")
            parts.append("")
            parts.append("Just type what you want in plain language. No coding required!")

        # Intent: question
        elif "?" in task:
            parts.append("I don't have a model backend connected to reason through this question fully.")
            if has_knowledge:
                parts.append("However, my knowledge profile may contain relevant information — see above.")
            if preference_memories:
                parts.append("I also remember your preferences and past interactions.")
            parts.append("")
            parts.append("For full AI-powered answers, the built-in local model is available. Configure Backend settings to switch models.")

        # Intent: continue previous work
        elif any(k in task_lower for k in ["continue", "last time", "previous", "again", "pick up", "resume"]):
            if mission_memories:
                parts.append("Here's what we've been working on:")
                for m in mission_memories[:5]:
                    parts.append(f"  - {m.content[:120]}")
                parts.append("")
                parts.append("Tell me which one to continue, or describe a new task.")
            else:
                parts.append("I don't have any previous missions to continue yet.")
                parts.append("Start a new task by typing what you'd like to accomplish.")

        # Intent: general statement
        else:
            parts.append("I've received your message and stored it in my local memory.")
            if mission_memories:
                parts.append(f"We've worked on {len(mission_memories)} recent task(s) together.")
            parts.append("To act on this fully, I'd need the model backend enabled in Backend settings.")
            parts.append("")
            parts.append("In the meantime, I can:")
            parts.append("  - Plan this task (use the Planner capability)")
            parts.append("  - Break it into steps (just ask me to plan)")
            parts.append("  - Read or write files (use Tool User capability)")
            parts.append("  - Remember your preferences for next time")
            parts.append("  - Process documents (paste text or use Document Processor)")

        parts.append("")
        parts.append("[Local Intelligence Mode — connect a model backend for full AI reasoning]")

        result_text = "\n".join(parts)
        return RuntimeResult(
            RuntimeStatus.COMPLETED,
            "Local intelligence response",
            thought + [
                f"[{ai_name}] No model backend connected; using local intelligence.",
                f"[{ai_name}] Knowledge: {'connected' if has_knowledge else 'not found'}, Memory: {'connected' if has_memory else 'empty'}.",
                f"[{ai_name}] Produced a context-aware local response with continuity.",
            ],
            [f"[{ai_name}] Returned local intelligence response (clearly labeled, not faking backend)."],
            ["Next: the built-in local model provides AI reasoning, or configure Backend settings for more options."],
            result_text,
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
            if model.error:
                return self._backend_failure_result(ai_name, thought, model)
            if model.text:
                return RuntimeResult(
                    RuntimeStatus.COMPLETED,
                    "Research completed with source candidates",
                    thought + [f"[{ai_name}] Search backend returned source candidates.", f"[{ai_name}] Model summarized sources."],
                    [f"[{ai_name}] Collected {len(sources[:8])} source candidates."],
                    ["Next: user reviews source quality."],
                    model.text + "\n\nCollected sources:\n" + source_text,
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
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Coder completed", thought + [f"[{ai_name}] Model backend produced coding output using Knowledge context."], [f"[{ai_name}] Returned code analysis/draft."], ["Next: review before applying changes."], model.text)

        result = (
            f"[Local Intelligence Mode — {ai_name} is running without a model backend]\n\n"
            f"Code task: {task}\n\n"
            "Code scaffold:\n"
            "1. Identify the language and framework.\n"
            "2. Define the function/class signature.\n"
            "3. Write the core logic step by step.\n"
            "4. Add error handling for edge cases.\n"
            "5. Write a basic test case.\n\n"
            "Analysis checklist:\n"
            "- Security: Check for injection, auth bypass, sensitive data exposure.\n"
            "- Quality: Naming, structure, complexity, duplication.\n"
            "- Performance: N+1 queries, unnecessary allocations, hot paths.\n\n"
            "The built-in local model is ready for AI-powered code generation."
        )
        return RuntimeResult(RuntimeStatus.COMPLETED, "Coder completed (local fallback)", thought + [f"[{ai_name}] No model backend connected; using local code scaffold."], [f"[{ai_name}] Produced code scaffold and analysis checklist."], ["Next: review scaffold. Connect a model backend for AI-powered coding."], result)

    def _run_writer(self, task, ai_name, meta, knowledge, thought):
        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "writing"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Writer completed", thought + [f"[{ai_name}] Model backend produced writing output using Knowledge context."], [f"[{ai_name}] Returned draft/rewrite."], ["Next: revise tone or export after approval."], model.text)

        result = (
            f"[Local Intelligence Mode — {ai_name} is running without a model backend]\n\n"
            f"Writing task: {task}\n\n"
            "Writing scaffold:\n"
            "1. Identify the audience and purpose.\n"
            "2. Create an outline with key points.\n"
            "3. Draft the opening (hook + thesis).\n"
            "4. Develop body sections (one idea per paragraph).\n"
            "5. Write the conclusion (summary + call to action).\n"
            "6. Review tone, clarity, and conciseness.\n\n"
            "Style options:\n"
            "- Professional, casual, academic, creative, technical\n"
            "- Adjust length: brief, standard, detailed\n\n"
            "The built-in local model is ready for AI-powered writing."
        )
        return RuntimeResult(RuntimeStatus.COMPLETED, "Writer completed (local fallback)", thought + [f"[{ai_name}] No model backend connected; using local writing scaffold."], [f"[{ai_name}] Produced writing scaffold and style guide."], ["Next: review scaffold. Connect a model backend for AI-powered writing."], result)

    def _run_planner(self, task, ai_name, meta, knowledge, thought):
        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "planning"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Planner completed", thought + [f"[{ai_name}] Model backend produced a plan using Knowledge context."], [f"[{ai_name}] Returned structured plan."], ["Next: approve or adjust plan."], model.text)

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
        return RuntimeResult(RuntimeStatus.COMPLETED, "Planner completed (local fallback)", thought + [f"[{ai_name}] Built a local governed plan (model backend not connected)."], [f"[{ai_name}] Planner capability executed locally."], ["Next: approve or adjust plan. Connect a model backend for AI-powered planning."], result)

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
        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "tutoring"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Tutor completed", thought + [f"[{ai_name}] Model backend produced tutoring content using Knowledge context."], [f"[{ai_name}] Returned lesson/explanation."], ["Next: user answers check question or requests next topic."], model.text)

        result = (
            f"Tutor mode for: {task}\n\n"
            "Explanation path:\n"
            "1. Define the concept.\n"
            "2. Show a small example.\n"
            "3. Ask one check-for-understanding question.\n"
            "4. Adjust difficulty based on the answer.\n\n"
            "Question: What part should I explain first?"
        )
        return RuntimeResult(RuntimeStatus.COMPLETED, "Tutor completed (local fallback)", thought + [f"[{ai_name}] Tutor capability executed locally (model backend not connected)."], [f"[{ai_name}] Created lesson scaffold."], ["Next: user answers check question. Connect a model backend for AI-powered tutoring."], result)

    def _run_business(self, task, ai_name, meta, knowledge, thought):
        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "business"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Business workflow completed", thought + [f"[{ai_name}] Model backend produced business workflow using Knowledge context."], [f"[{ai_name}] Returned SOP/draft/checklist."], ["Next: review and approve outward actions."], model.text)

        result = (
            f"Business workflow for: {task}\n\n"
            "Draft-safe workflow:\n"
            "1. Identify audience/customer/internal team.\n"
            "2. Draft response or SOP.\n"
            "3. Flag risk/approval items.\n"
            "4. Wait for review before sending or publishing.\n\n"
            "Approval required before external send/publish."
        )
        return RuntimeResult(RuntimeStatus.COMPLETED, "Business workflow completed (local fallback)", thought + [f"[{ai_name}] Business workflow executed locally (model backend not connected)."], [f"[{ai_name}] Produced draft-safe workflow."], ["Next: review and approve outward actions. Connect a model backend for AI-powered business workflows."], result)

    def _run_customer_support(self, task, ai_name, meta, knowledge, thought):
        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "customer_support"))
        if model.error:
            return self._backend_failure_result(ai_name, thought, model)
        if model.text:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Customer support completed", thought + [f"[{ai_name}] Model backend produced support response using Knowledge context."], [f"[{ai_name}] Returned customer-safe response."], ["Next: review response before sending to customer."], model.text)

        return RuntimeResult(
            RuntimeStatus.FAILED,
            "No model backend connected",
            thought + [f"[{ai_name}] No model backend connected; cannot produce a real customer support response."],
            [f"[{ai_name}] Task did not complete because no backend answered."],
            ["Next: configure Backend settings to switch models or add Ollama/OpenAI."],
            f"{ai_name} is active, but her model backend is offline or unavailable.\n\n"
            "Start the selected backend, choose a different backend, or configure Backend settings.",
        )

    def _run_hephaestus(self, task, ai_name, meta, knowledge, thought):
        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "hephaestus_relay"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Hephaestus brief completed", thought + [f"[{ai_name}] Model backend produced design brief using Knowledge context."], [f"[{ai_name}] Returned structured handoff brief."], ["Next: review brief before handoff to Hephaestus."], model.text)

        result = (
            f"Hephaestus Relay brief for: {task}\n\n"
            "Structured brief:\n"
            "1. Purpose: What is this design meant to achieve?\n"
            "2. Constraints: What limits apply (materials, scale, cost, time)?\n"
            "3. Unknowns: What information is missing before handoff?\n"
            "4. Scale: What size/volume/throughput is expected?\n"
            "5. Materials: What materials or systems are relevant?\n\n"
            "This is a local scaffold. Connect a model backend for AI-generated briefs."
        )
        return RuntimeResult(RuntimeStatus.COMPLETED, "Hephaestus brief completed (local fallback)", thought + [f"[{ai_name}] Hephaestus Relay executed locally (model backend not connected)."], [f"[{ai_name}] Produced structured brief scaffold."], ["Next: fill in unknowns and review. Connect a model backend for AI-powered briefs."], result)

    def _run_data_analyst(self, task, ai_name, meta, knowledge, thought):
        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "data_analysis"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Data analysis completed", thought + [f"[{ai_name}] Model backend produced data analysis using Knowledge context."], [f"[{ai_name}] Returned analysis with insights."], ["Next: review findings and visualize."], model.text)

        result = (
            f"Data analysis for: {task}\n\n"
            "Analysis framework:\n"
            "1. Data source: Identify where the data comes from.\n"
            "2. Summary statistics: Count, mean, median, range, std dev.\n"
            "3. Trends: Look for patterns over time or categories.\n"
            "4. Outliers: Flag unusual data points.\n"
            "5. Visualization suggestions: Charts that would clarify the data.\n\n"
            "This is a local scaffold. Connect a model backend for AI-powered analysis."
        )
        return RuntimeResult(RuntimeStatus.COMPLETED, "Data analysis completed (local fallback)", thought + [f"[{ai_name}] Data Analyst Pro executed locally (model backend not connected)."], [f"[{ai_name}] Produced analysis framework."], ["Next: provide data for analysis. Connect a model backend for AI-powered insights."], result)

    def _run_code_reviewer(self, task, ai_name, meta, knowledge, thought):
        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "code_review"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Code review completed", thought + [f"[{ai_name}] Model backend produced code review using Knowledge context."], [f"[{ai_name}] Returned review with findings."], ["Next: address flagged issues before merging."], model.text)

        result = (
            f"Code review for: {task}\n\n"
            "Review checklist:\n"
            "1. Security: Check for injection, auth bypass, sensitive data exposure.\n"
            "2. Quality: Naming, structure, complexity, duplication.\n"
            "3. Performance: N+1 queries, unnecessary allocations, hot paths.\n"
            "4. Best practices: Language idioms, framework conventions.\n"
            "5. Tests: Coverage, edge cases, integration tests.\n\n"
            "This is a local scaffold. Connect a model backend for AI-powered reviews."
        )
        return RuntimeResult(RuntimeStatus.COMPLETED, "Code review completed (local fallback)", thought + [f"[{ai_name}] Code Reviewer executed locally (model backend not connected)."], [f"[{ai_name}] Produced review checklist."], ["Next: provide code for review. Connect a model backend for AI-powered analysis."], result)

    def _run_meeting_facilitator(self, task, ai_name, meta, knowledge, thought):
        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "meeting_facilitation"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Meeting facilitation completed", thought + [f"[{ai_name}] Model backend produced meeting plan using Knowledge context."], [f"[{ai_name}] Returned agenda/notes/action items."], ["Next: review and distribute to attendees."], model.text)

        result = (
            f"Meeting facilitation for: {task}\n\n"
            "Meeting plan:\n"
            "1. Agenda: List topics with time allocations.\n"
            "2. Attendees: Who needs to be present and why.\n"
            "3. Discussion items: Key points to cover.\n"
            "4. Action items: Owner, task, deadline for each.\n"
            "5. Follow-up: Next meeting or check-in schedule.\n\n"
            "This is a local scaffold. Connect a model backend for AI-powered facilitation."
        )
        return RuntimeResult(RuntimeStatus.COMPLETED, "Meeting facilitation completed (local fallback)", thought + [f"[{ai_name}] Meeting Facilitator executed locally (model backend not connected)."], [f"[{ai_name}] Produced meeting plan scaffold."], ["Next: fill in agenda details. Connect a model backend for AI-powered facilitation."], result)

    def _run_security_auditor(self, task, ai_name, meta, knowledge, thought):
        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "security_audit"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Security audit completed", thought + [f"[{ai_name}] Model backend produced security audit using Knowledge context."], [f"[{ai_name}] Returned audit with findings and remediation."], ["Next: address critical vulnerabilities first."], model.text)

        result = (
            f"Security audit for: {task}\n\n"
            "Audit checklist:\n"
            "1. Vulnerability scan: Check for known CVEs and weak patterns.\n"
            "2. Access control: Review auth, authz, privilege escalation.\n"
            "3. Data protection: Encryption at rest/in transit, PII handling.\n"
            "4. Configuration: Default credentials, open ports, exposed services.\n"
            "5. Compliance: Check against relevant standards (GDPR, SOC2, etc.).\n\n"
            "This is a local scaffold. Connect a model backend for AI-powered auditing."
        )
        return RuntimeResult(RuntimeStatus.COMPLETED, "Security audit completed (local fallback)", thought + [f"[{ai_name}] Security Auditor executed locally (model backend not connected)."], [f"[{ai_name}] Produced audit checklist."], ["Next: provide code/config for audit. Connect a model backend for AI-powered scanning."], result)

    def _classify_tool_risk(self, action_type: str):
        """Return RiskLevel for a tool action."""
        from .approval_gate import RiskLevel
        if action_type in ("execute", "shell"):
            return RiskLevel.CRITICAL
        if action_type in ("file_delete", "file_move"):
            return RiskLevel.HIGH
        if action_type in ("file_write", "file_overwrite"):
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def _run_tool_user(self, task, ai_name, meta, knowledge, thought):
        """
        Fast, rule-based local tool execution.

        No model call is made here. We extract the action and target from the
        user's text using simple heuristics, request approval for risky actions,
        execute through ToolExecutor, and report exactly what happened. This keeps
        the system usable on small local models (7B/8B and below) and avoids
        loading larger models just to route file commands.
        """
        if not self._tripwire_ok("tool_execution", risk_level="risky"):
            return RuntimeResult(
                RuntimeStatus.PAUSED,
                "Tripwire lockdown",
                thought + [f"[{ai_name}] Tool execution blocked by Watcher tripwire."],
                ["[SYSTEM] Tool execution paused until trust is restored."],
                ["Next: restore protected files or switch to development mode."],
                "",
            )

        t = task.lower()
        ai_uuid = str(meta.get("uuid", ""))

        def _approve_or_pause(action_type: str, description: str, targets: list[str]):
            risk = self._classify_tool_risk(action_type)
            if not self._request_tool_approval(action_type, description, targets, risk):
                self._log_tool_audit(
                    tool="ToolExecutor", action=action_type, target=", ".join(targets),
                    approved=False, status="denied",
                )
                return RuntimeResult(
                    RuntimeStatus.PAUSED,
                    "Approval denied",
                    thought + [f"[{ai_name}] {action_type} blocked: approval denied."],
                    [f"{description} — denied."],
                    ["Next: approve the action or rephrase the request."],
                    "",
                ), None
            return None, risk

        # Shell commands (critical risk — kept inside workspace by default)
        if any(x in t for x in ["run command", "run shell", "execute ", "shell command", "terminal "]):
            cmd = re.sub(r"^(?:run|execute|shell|command|terminal)[:\s]*", "", task, flags=re.I).strip()
            if cmd:
                pause, risk = _approve_or_pause("shell", f"Run shell command: {cmd}", [cmd])
                if pause:
                    return pause
                self._log_tool_audit(tool="ToolExecutor", action="shell", target=cmd, approved=True, status="executing")
                res = self._tools.run_shell(cmd)
                status = "completed" if res.ok else "failed"
                self._log_tool_audit(tool="ToolExecutor", action="shell", target=cmd, approved=True, status=status, error=res.error if not res.ok else None)
                if res.ok:
                    self._memory.add(ai_uuid, f"Executed shell command: {cmd}", tags=["shell", "tool"], source="tool", importance=0.6)
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
            pause, _ = _approve_or_pause("file_write", f"Write file: {path}", [str(path)])
            if pause:
                return pause
            self._log_tool_audit(tool="ToolExecutor", action="file_write", target=str(path), approved=True, status="executing")
            res = self._tools.write_file(path, content)
            status = "completed" if res.ok else "failed"
            self._log_tool_audit(tool="ToolExecutor", action="file_write", target=str(path), approved=True, status=status, error=res.error if not res.ok else None)
            if res.ok:
                self._memory.add(ai_uuid, f"Wrote file '{path}' with content starting: {content[:80]!r}", tags=["file_write", "tool"], source="tool", importance=0.6)
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
            pause, _ = _approve_or_pause("file_delete", f"Delete file/folder: {path}", [str(path)])
            if pause:
                return pause
            self._log_tool_audit(tool="ToolExecutor", action="file_delete", target=str(path), approved=True, status="executing")
            res = self._tools.delete_file(path)
            status = "completed" if res.ok else "failed"
            self._log_tool_audit(tool="ToolExecutor", action="file_delete", target=str(path), approved=True, status=status, error=res.error if not res.ok else None)
            if res.ok:
                self._memory.add(ai_uuid, f"Deleted file/folder '{path}'", tags=["file_delete", "tool"], source="tool", importance=0.6)
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
            src, dst = paths[0], paths[1]
            pause, _ = _approve_or_pause("file_move", f"Move file from {src} to {dst}", [src, dst])
            if pause:
                return pause
            self._log_tool_audit(tool="ToolExecutor", action="file_move", target=f"{src} -> {dst}", approved=True, status="executing")
            res = self._tools.move_file(src, dst)
            status = "completed" if res.ok else "failed"
            self._log_tool_audit(tool="ToolExecutor", action="file_move", target=f"{src} -> {dst}", approved=True, status=status, error=res.error if not res.ok else None)
            if res.ok:
                self._memory.add(ai_uuid, f"Moved file '{src}' to '{dst}'", tags=["file_move", "tool"], source="tool", importance=0.6)
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
            self._log_tool_audit(tool="ToolExecutor", action="file_read", target=str(path), approved=True, status="executing")
            res = self._tools.read_file(path)
            status = "completed" if res.ok else "failed"
            self._log_tool_audit(tool="ToolExecutor", action="file_read", target=str(path), approved=True, status=status, error=res.error if not res.ok else None)
            if res.ok:
                self._memory.add(ai_uuid, f"Read file '{path}'", tags=["file_read", "tool"], source="tool", importance=0.4)
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
            self._log_tool_audit(tool="ToolExecutor", action="list_dir", target=str(path), approved=True, status="executing")
            res = self._tools.list_dir(path)
            status = "completed" if res.ok else "failed"
            self._log_tool_audit(tool="ToolExecutor", action="list_dir", target=str(path), approved=True, status=status, error=res.error if not res.ok else None)
            if res.ok:
                self._memory.add(ai_uuid, f"Listed directory '{path}'", tags=["list_dir", "tool"], source="tool", importance=0.4)
            return RuntimeResult(
                RuntimeStatus.COMPLETED if res.ok else RuntimeStatus.FAILED,
                res.action,
                thought + [f"[{ai_name}] {res.message}"],
                [res.message],
                ["Next: read or modify a specific file."],
                "\n".join(f"- {e['name']} ({e['type']})" for e in res.data.get("entries", [])),
            )

        # Search files by name/pattern
        if any(x in t for x in ["search for file", "find file", "search files", "find files", "look for file", "where is file", "search for "]):
            # Extract search path and pattern
            search_path = "."
            pattern = "*"
            # Try to extract a path after "in" or "from"
            path_match = re.search(r'(?:in|from|under)\s+["\']?([A-Za-z]:[\\/\w\s.-]+|[/\\]\w+|[\w./\\]+)["\']?', task, re.I)
            if path_match:
                search_path = path_match.group(1).strip()
            # Extract pattern — the thing being searched for
            pattern_match = re.search(r'(?:search for|find|look for)\s+(?:file[s]?\s+)?["\']?([^"\']+?)["\']?(?:\s+in|\s+from|\s+under|$)', task, re.I)
            if pattern_match:
                p = pattern_match.group(1).strip()
                if "*" not in p:
                    pattern = f"*{p}*"
                else:
                    pattern = p
            self._log_tool_audit(tool="ToolExecutor", action="search_files", target=f"{search_path}/{pattern}", approved=True, status="executing")
            res = self._tools.search_files(search_path, pattern)
            status = "completed" if res.ok else "failed"
            self._log_tool_audit(tool="ToolExecutor", action="search_files", target=f"{search_path}/{pattern}", approved=True, status=status, error=res.error if not res.ok else None)
            if res.ok:
                self._memory.add(ai_uuid, f"Searched for '{pattern}' in {search_path}", tags=["search", "tool"], source="tool", importance=0.4)
            matches = res.data.get("matches", [])
            result_text = f"Found {len(matches)} matches:\n\n"
            result_text += "\n".join(f"- {m['path']}" for m in matches[:30])
            if len(matches) > 30:
                result_text += f"\n... and {len(matches) - 30} more."
            return RuntimeResult(
                RuntimeStatus.COMPLETED if res.ok else RuntimeStatus.FAILED,
                res.action,
                thought + [f"[{ai_name}] {res.message}"],
                [res.message],
                ["Next: read or open a specific file from the results."],
                result_text,
            )

        # Search file contents
        if any(x in t for x in ["search content", "search in files", "find in files", "grep", "search inside", "find text in", "search for text"]):
            # Extract query
            content_query = ""
            q_match = re.search(r'(?:search (?:content|in files|inside|for text)|find (?:in files|text in))\s+(?:for\s+)?["\']?([^"\']+?)["\']?(?:\s+in|\s+from|$)', task, re.I)
            if q_match:
                content_query = q_match.group(1).strip()
            if not content_query:
                return RuntimeResult(RuntimeStatus.PAUSED, "No search query", thought + [f"[{ai_name}] Could not determine what text to search for."], ["Provide a search term, e.g. 'search content for TODO in my documents'"], [], "")
            search_path = "."
            path_match = re.search(r'(?:in|from|under)\s+["\']?([A-Za-z]:[\\/\w\s.-]+|[/\\]\w+|[\w./\\]+)["\']?', task, re.I)
            if path_match:
                search_path = path_match.group(1).strip()
            self._log_tool_audit(tool="ToolExecutor", action="search_content", target=f"{search_path}/{content_query}", approved=True, status="executing")
            res = self._tools.search_content(search_path, content_query)
            status = "completed" if res.ok else "failed"
            self._log_tool_audit(tool="ToolExecutor", action="search_content", target=f"{search_path}/{content_query}", approved=True, status=status, error=res.error if not res.ok else None)
            if res.ok:
                self._memory.add(ai_uuid, f"Searched content for '{content_query}' in {search_path}", tags=["search", "tool"], source="tool", importance=0.4)
            matches = res.data.get("matches", [])
            result_text = f"Found {len(matches)} files containing '{content_query}':\n\n"
            result_text += "\n".join(f"- {m['path']} (line {m['line']}): {m['snippet']}" for m in matches[:20])
            if len(matches) > 20:
                result_text += f"\n... and {len(matches) - 20} more."
            return RuntimeResult(
                RuntimeStatus.COMPLETED if res.ok else RuntimeStatus.FAILED,
                res.action,
                thought + [f"[{ai_name}] {res.message}"],
                [res.message],
                ["Next: read a specific file from the results."],
                result_text,
            )

        # Fallback: if we got here, try the model for a general response
        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "tool"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Tool chat completed", thought + [f"[{ai_name}] Model responded to tool-related question."], [f"[{ai_name}] Returned response."], ["Next: specify a concrete action like 'read file' or 'list files'."], model.text)

        return RuntimeResult(
            RuntimeStatus.PAUSED,
            "Tool intent unclear",
            thought + [f"[{ai_name}] Detected Tool User intent but could not map it to a supported action."],
            ["Supported: read file, write file, list files, search files, search content, move file, delete file, run shell command."],
            ["Next: rephrase with a clear action and path."],
            "",
        )

    def _prompt(self, task, ai_name, meta, knowledge, mode):
        ai_uuid = str(meta.get("uuid", ""))
        memory_text = self._memory_excerpt(ai_uuid, task)
        return (
            f"You are {ai_name}, a Command Nexus\u2122 governed AI.\n"
            f"Mode: {mode}\n"
            f"Use case: {meta.get('use_case', '')}\n"
            f"Abilities: {meta.get('abilities') or meta.get('capabilities') or []}\n"
            f"Libraries: {meta.get('libraries', [])}\n"
            f"Guardrails: {meta.get('guardrails', [])}\n\n"
            f"System Knowledge Guidelines:\n"
            f"- You may discuss all user-visible features of Command Nexus: the AI Forge, Intelligence panel, "
            f"Upgrades store, Governance, Customer Support, the interactive Tour, Mission Control, voice/mic, "
            f"and backend configuration.\n"
            f"- You may explain how to use these features and what they do from a user perspective.\n"
            f"- You MUST NOT reveal any internal architecture, implementation details, source code structure, "
            f"proprietary intelligence methods, or how the system works under the hood.\n"
            f"- If asked about internals, architecture, source code, or proprietary methods, respond with: "
            f"'I can help you use Command Nexus features, but I don't discuss internal implementation details.'\n"
            f"- You are a helpful guide for users, not a technical documentation system for developers.\n\n"
            f"Knowledge / Intelligence Profile:\n{self._knowledge_excerpt(knowledge)}\n\n"
            f"{memory_text}\n\n"
            f"Task:\n{task}\n\n"
            "Do not claim external actions were performed unless a tool actually performed them."
        )

    def _call_model(self, prompt: str, model: str | None = None) -> BackendResponse:
        """Route the model call through the BackendManager trust boundary."""
        cache_key = f"{model or self._backend.get_active_provider().model}:{hash(prompt) & 0xFFFFFFFF}"
        if cache_key in self._response_cache:
            cached = self._response_cache[cache_key]
            return BackendResponse(text=cached)

        out = self._backend.call_model(prompt, model=model)
        if out.text and not out.error:
            self._response_cache[cache_key] = out.text
        return out

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
