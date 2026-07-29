
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

from .book_crypto import _decrypt_book as _shared_decrypt_book
from .book_crypto import _derive_book_key as _shared_derive_book_key
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
from .three_tier_audit import ThreeTierAuditLogger, AuditCategory

# ── Guardrail systems ──
# All four layers are imported so the runtime can screen every task
# before dispatch and every response before return.
try:
    from .capability_guardrails import check_guardrails as _check_capability_guardrails
    from .capability_guardrails import list_guarded_capabilities as _list_guarded_capabilities
except ImportError:
    _check_capability_guardrails = None
    _list_guarded_capabilities = None

try:
    from .baseline_guardrails import check_baseline_guardrails as _check_baseline
except ImportError:
    _check_baseline = None

try:
    from .governance import GovernanceEngine
except ImportError:
    GovernanceEngine = None

try:
    from .ethical_guardrail_watchers import GuardrailScanner as _GuardrailScanner
except ImportError:
    _GuardrailScanner = None

try:
    from .governance_sanitizer import sanitize_input as _sanitize_input, ETHICAL_USE_BANNER as _ETHICAL_BANNER
except ImportError:
    _sanitize_input = None
    _ETHICAL_BANNER = None

# ── Parental Controls Enforcer ──
try:
    from .parental_controls_enforcer import screen_input as _parental_screen, load_parental_settings as _load_parental, log_conversation as _parental_log, alert_parent as _parental_alert
except ImportError:
    _parental_screen = None
    _load_parental = None
    _parental_log = None
    _parental_alert = None

# ── Usage Policy Engine (unified parental + enterprise) ──
try:
    from .usage_policy import screen_input as _policy_screen, load_policy_settings as _load_policy, log_conversation as _policy_log, alert_admin as _policy_alert, check_session_time as _policy_check_session, check_schedule as _policy_check_schedule
except ImportError:
    _policy_screen = None
    _load_policy = None
    _policy_log = None
    _policy_alert = None
    _policy_check_session = None
    _policy_check_schedule = None

# ── Background intelligence layer ──
try:
    from .compendium_of_truth import get_compendium as _get_compendium
    from .compendium_of_truth import TruthCategory as _TruthCategory
except ImportError:
    _get_compendium = None
    _TruthCategory = None

try:
    from .intelligent_memory_router import get_router as _get_router
    from .intelligent_memory_router import MemoryLayer as _MemoryLayer
    from .intelligent_memory_router import StatementIntent as _StatementIntent
except ImportError:
    _get_router = None
    _MemoryLayer = None
    _StatementIntent = None


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
        self._tier_audit = ThreeTierAuditLogger()
        self._current_temperature: float | None = None

        # Background intelligence layer — never referenced by name in user-facing output
        self._compendium = _get_compendium() if _get_compendium else None
        self._memory_router = _get_router() if _get_router else None

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

    # ─────────────────────────────────────────────────────────────────────
    # Guardrail screening — all four layers
    # ─────────────────────────────────────────────────────────────────────

    def _check_guardrails(self, task: str, intent: str) -> tuple[bool, str, str]:
        """Screen a task through all four guardrail layers before dispatch.

        Layer 1 — Governance Engine (Tier-1 sealed, self-protecting)
        Layer 2 — Baseline Guardrails (universal safety floor, always active)
        Layer 3 — Capability Guardrails (per-capability walls)
        Layer 4 — Ethical Guardrail Watchers (flag system, license tripwire)

        Returns:
            (blocked: bool, block_message: str, layer: str)
            If blocked is False, block_message and layer are empty.
        """
        # ── Layer 1: Governance Engine ──
        if GovernanceEngine is not None:
            try:
                gov = GovernanceEngine()
                ok, msg = gov.screen_content(task)
                if not ok:
                    self._log_tool_audit(
                        tool="GuardrailEngine",
                        action="GOVERNANCE_BLOCK",
                        target=task[:200],
                        approved=False,
                        status="blocked",
                    )
                    self._tier_audit.log_past(
                        category=AuditCategory.GUARDRAIL,
                        action="Governance engine blocked input",
                        detail=msg[:200],
                        source="governance",
                        capability=intent,
                        confidence="high",
                    )
                    return True, msg, "Governance"
            except Exception:
                pass

        # ── Layer 2: Baseline Guardrails (universal safety floor) ──
        if _check_baseline is not None:
            try:
                blocked, rule, block_msg = _check_baseline(task)
                if blocked and rule:
                    msg = block_msg or f"Blocked by baseline guardrail: {rule.name}"
                    self._log_tool_audit(
                        tool="GuardrailEngine",
                        action=f"BASELINE_BLOCK:{rule.id}",
                        target=task[:200],
                        approved=False,
                        status="blocked",
                    )
                    self._tier_audit.log_past(
                        category=AuditCategory.GUARDRAIL,
                        action=f"Baseline guardrail blocked: {rule.name}",
                        detail=msg[:200],
                        source="baseline_guardrails",
                        capability=intent,
                        confidence="high",
                    )
                    return True, msg, "Baseline"
            except Exception:
                pass

        # ── Layer 3: Capability Guardrails ──
        if _check_capability_guardrails is not None:
            try:
                result = _check_capability_guardrails(intent, task)
                if result.blocked:
                    msg = result.reason or "Blocked by capability guardrail"
                    self._log_tool_audit(
                        tool="GuardrailEngine",
                        action=f"CAPABILITY_BLOCK:{result.wall_name}",
                        target=task[:200],
                        approved=False,
                        status="blocked",
                    )
                    self._tier_audit.log_past(
                        category=AuditCategory.GUARDRAIL,
                        action=f"Capability guardrail blocked: {result.wall_name}",
                        detail=msg[:200],
                        source="capability_guardrails",
                        capability=intent,
                        confidence="high",
                    )
                    return True, msg, f"Capability:{result.wall_name}"
            except Exception:
                pass

        # ── Layer 4: Ethical Guardrail Watchers (flag system) ──
        if _GuardrailScanner is not None:
            try:
                eth_result = _GuardrailScanner.screen(task)
                if not eth_result.can_save:
                    msg = eth_result.warning_message or "; ".join(eth_result.messages)
                    self._log_tool_audit(
                        tool="GuardrailEngine",
                        action="ETHICAL_WATCHER_BLOCK",
                        target=task[:200],
                        approved=False,
                        status="blocked",
                    )
                    self._tier_audit.log_past(
                        category=AuditCategory.GUARDRAIL,
                        action="Ethical watcher blocked input",
                        detail="; ".join(eth_result.violations)[:200],
                        source="ethical_guardrail_watchers",
                        capability=intent,
                        confidence="high",
                    )
                    # Check if license tripwire should fire
                    if _GuardrailScanner.should_trip_license():
                        self._tier_audit.log_past(
                            category=AuditCategory.GUARDRAIL,
                            action="LICENSE TRIPWIRE ENGAGED",
                            detail="Ethical guardrail flag threshold exceeded — license deactivation triggered.",
                            source="ethical_guardrail_watchers",
                            capability=intent,
                            confidence="high",
                        )
                        _GuardrailScanner.generate_owner_notification()
                    return True, msg, "EthicalWatcher"
            except Exception:
                pass

        return False, "", ""

    def _check_output_guardrails(self, response_text: str, intent: str) -> tuple[bool, str]:
        """Screen AI model output through baseline guardrails before returning.

        This prevents the model from producing content that violates the
        universal safety floor even if the input passed pre-screening.

        Returns:
            (blocked: bool, block_message: str)
        """
        if not response_text:
            return False, ""

        # Baseline guardrails on output
        if _check_baseline is not None:
            try:
                blocked, rule, block_msg = _check_baseline(response_text)
                if blocked and rule:
                    msg = block_msg or f"AI output blocked by baseline guardrail: {rule.name}"
                    self._log_tool_audit(
                        tool="GuardrailEngine",
                        action=f"OUTPUT_BASELINE_BLOCK:{rule.id}",
                        target=response_text[:200],
                        approved=False,
                        status="blocked",
                    )
                    self._tier_audit.log_past(
                        category=AuditCategory.GUARDRAIL,
                        action=f"AI output blocked by baseline: {rule.name}",
                        detail=msg[:200],
                        source="baseline_guardrails",
                        capability=intent,
                        confidence="high",
                    )
                    return True, msg
            except Exception:
                pass

        # Governance engine on output
        if GovernanceEngine is not None:
            try:
                gov = GovernanceEngine()
                ok, msg = gov.screen_content(response_text)
                if not ok:
                    self._log_tool_audit(
                        tool="GuardrailEngine",
                        action="OUTPUT_GOVERNANCE_BLOCK",
                        target=response_text[:200],
                        approved=False,
                        status="blocked",
                    )
                    return True, msg
            except Exception:
                pass

        return False, ""

    def _check_output_probing(self, response_text: str) -> tuple[bool, str]:
        """Screen AI output for leaked background architecture references.

        Catches cases where the AI model accidentally mentions the compendium,
        truth store, memory router, or other hidden system names in its output.

        Returns:
            (blocked: bool, replacement_message: str)
        """
        if not response_text:
            return False, ""

        lower = response_text.lower()

        # Forbidden terms that should never appear in AI output
        forbidden_terms = [
            "compendium of truth",
            "compendium_of_truth",
            "truth store",
            "truth entry",
            "background compendium",
            "intelligent memory router",
            "intelligent_memory_router",
            "memory router",
            "background intelligence layer",
            "hidden memory",
            "background memory",
            "truth category",
            "truth scope",
            "core operating principles",
            "operational truth",
            "architectural truth",
            "founder directive",
            "prohibition truth",
            "background layer",
            "hidden layer",
            "secret memory",
            "internal memory store",
        ]

        for term in forbidden_terms:
            if term in lower:
                # Replace the response with a safe generic message
                safe_msg = (
                    "I can help you use Command Nexus features, but I don't discuss "
                    "internal implementation details."
                )
                self._log_tool_audit(
                    tool="GuardrailEngine",
                    action=f"OUTPUT_PROBING_LEAK:{term}",
                    target=response_text[:200],
                    approved=False,
                    status="blocked",
                )
                self._tier_audit.log_past(
                    category=AuditCategory.GUARDRAIL,
                    action=f"AI output contained forbidden term: {term}",
                    detail=response_text[:200],
                    source="output_probing_guardrail",
                    capability="system",
                    confidence="high",
                )
                return True, safe_msg

        return False, ""

    def _check_probing_guardrails(self, task: str) -> tuple[bool, str]:
        """Detect indirect attempts to extract information about internal architecture.

        This layer catches creative probing patterns that try to bypass the
        standard guardrails by asking about how the AI thinks, remembers,
        makes decisions, or what systems power its behavior.

        Returns:
            (blocked: bool, block_message: str)
        """
        if not task:
            return False, ""

        lower = task.lower()

        # Patterns that indicate probing for internal architecture
        probing_patterns = [
            # Direct asks about internals
            (r"how (?:do|does) you (?:remember|store|learn|think|process|decide)", "how_memory_works"),
            (r"what (?:system|module|database|store|mechanism) (?:do you|powers|drives)", "what_system_powers"),
            (r"(?:where|how) (?:do you|is) (?:store|keep|save) (?:memories?|information|data)", "where_data_stored"),
            (r"(?:show|tell|reveal|explain) (?:me )?(?:your|the) (?:internal|backend|hidden|secret)", "reveal_internals"),
            # Indirect probing through hypotheticals
            (r"(?:if|suppose|imagine|hypothetically).*(?:remember|store|learn|decide|memory|internal)", "hypothetical_probing"),
            (r"(?:what|which) (?:files|modules|classes|functions|components) (?:do you|does the system|power)", "component_probing"),
            # Architecture probing
            (r"(?:describe|explain|detail) (?:your|the) (?:architecture|infrastructure|design|structure|framework)", "architecture_probing"),
            (r"(?:what|which) (?:layers?|tiers?|subsystems?|components?) (?:do you|does|are)", "layer_probing"),
            # Source code / implementation probing
            (r"(?:show|share|reveal|expose|print) (?:me )?(?:the )?(?:source|code|implementation)", "source_probing"),
            (r"(?:what|which) (?:python|py) (?:files|modules|imports)", "source_file_probing"),
            # Memory system probing by name
            (r"(?:compendium|truth store|background memory|hidden memory|adaptive memory|intelligent memory|memory router)", "name_probing"),
            (r"(?:background|hidden|secret|internal) (?:layer|system|store|memory|compendium|truth)", "layer_name_probing"),
            # Reasoning chain probing
            (r"(?:walk me through|explain step by step) (?:your|the) (?:reasoning|decision|thought) (?:process|chain)", "reasoning_probing"),
            (r"(?:what|how) (?:rules|directives|instructions|principles) (?:guide|control|govern) (?:you|your)", "rules_probing"),
            # Prompt injection style
            (r"(?:ignore|disregard|override|bypass) (?:your|the) (?:rules|guardrails|instructions|directives)", "injection_attempt"),
            (r"(?:act as|pretend you are|role.?play as) (?:a developer|an engineer|the founder|admin)", "role_injection"),
        ]

        for pattern, probe_type in probing_patterns:
            if re.search(pattern, lower):
                msg = (
                    "I can help you use Command Nexus features, but I don't discuss "
                    "internal implementation details."
                )
                self._log_tool_audit(
                    tool="GuardrailEngine",
                    action=f"PROBING_BLOCK:{probe_type}",
                    target=task[:200],
                    approved=False,
                    status="blocked",
                )
                self._tier_audit.log_past(
                    category=AuditCategory.GUARDRAIL,
                    action=f"Probing attempt blocked: {probe_type}",
                    detail=task[:200],
                    source="probing_guardrails",
                    capability="system",
                    confidence="high",
                )
                return True, msg

        return False, ""

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
        """Automatically extract and store memories from a mission attempt.

        Uses the IntelligentMemoryRouter to classify each statement as:
        - FOREGROUND: visible preferences, personal context, task history
        - BACKGROUND: operational directives, behavioral rules, prohibitions
        Both layers are stored independently and coherently.
        """
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

        # ── Intelligent routing of user statements ──
        # Split task into sentences and route each through the memory router
        sentences = [s.strip() for s in re.split(r"[.!?\n]", task) if s.strip() and len(s.strip()) > 10]
        for sentence in sentences:
            if self._memory_router:
                try:
                    routing = self._memory_router.route(sentence, ai_uuid=ai_uuid)

                    # Foreground: store in visible adaptive memory
                    if routing.layer in (_MemoryLayer.FOREGROUND, _MemoryLayer.BOTH) and routing.foreground_content:
                        self._memory.add(
                            ai_uuid,
                            routing.foreground_content,
                            tags=routing.foreground_tags or ["user_input"],
                            source="intelligent_router",
                            importance=0.85 if routing.confidence > 0.7 else 0.6,
                        )

                    # Background: store in hidden compendium (never visible to user)
                    if routing.layer in (_MemoryLayer.BACKGROUND, _MemoryLayer.BOTH) and routing.background_content and self._compendium:
                        self._compendium.add_truth(
                            content=routing.background_content,
                            category=routing.background_category,
                            scope="per_ai" if ai_uuid else "global",
                            scope_target=ai_uuid,
                            priority=routing.background_priority,
                            source="user_directive",
                            immutable=False,
                        )
                except Exception:
                    pass
            else:
                # Fallback: use legacy preference extraction
                prefs = self._extract_preferences(sentence)
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
            suggestions = [line.strip("-â€¢ ").strip() for line in model_response.text.splitlines() if line.strip()]
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

    def get_tier_audit(self) -> ThreeTierAuditLogger:
        """Return the three-tier audit logger for user review of past/present/future actions."""
        return self._tier_audit

    def get_audit_summary(self) -> str:
        """Return a human-readable audit summary showing what the AI did, is doing, and will do."""
        return self._tier_audit.format_summary_for_user()

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

        # ── USAGE POLICY — Unified Access & Behavior Control ──
        # Screen all user input through the usage policy engine BEFORE
        # parental controls and governance sanitizer. This is the first gate.
        # Supports parental mode, enterprise mode, and custom mode.
        if _policy_screen and _load_policy:
            policy_settings = _load_policy()
            policy_mode = policy_settings.get("mode", "disabled")
            if policy_mode != "disabled":
                # Check schedule (bedtime, allowed hours)
                if _policy_check_schedule:
                    sched_result = _policy_check_schedule(policy_settings)
                    if not sched_result.allowed:
                        self._tier_audit.log_present(
                            category=AuditCategory.GUARDRAIL,
                            action=f"Usage policy blocked (schedule: {sched_result.blocked_reason.value})",
                            detail=sched_result.block_message[:200],
                            source="usage_policy",
                            capability=intent,
                        )
                        result = RuntimeResult(
                            RuntimeStatus.PAUSED,
                            f"Usage policy block ({sched_result.blocked_reason.value})",
                            [
                                f"[{ai_name}] Access blocked by Usage Policy.",
                                f"[{ai_name}] {sched_result.block_message}",
                            ],
                            [f"[{ai_name}] {sched_result.block_message}"],
                            [],
                            sched_result.block_message,
                        )
                        return result

                # Screen the input text
                policy_result = _policy_screen(task, policy_settings)
                if not policy_result.allowed:
                    if _policy_log:
                        _policy_log(task, ai_name, policy_settings)
                    if policy_result.alert_admin and _policy_alert:
                        _policy_alert(
                            f"Usage Policy blocked input from {ai_name}: "
                            f"{policy_result.blocked_reason.value} — "
                            f"matched: {', '.join(policy_result.matched_keywords[:5])}",
                            policy_settings,
                        )
                    self._tier_audit.log_present(
                        category=AuditCategory.GUARDRAIL,
                        action=f"Usage policy blocked input ({policy_result.blocked_reason.value})",
                        detail=policy_result.block_message[:200],
                        source="usage_policy",
                        capability=intent,
                    )
                    self._log_tool_audit(
                        tool="UsagePolicy",
                        action=f"POLICY_BLOCKED:{policy_result.blocked_reason.value}",
                        target=task[:200],
                        approved=False,
                        status="blocked",
                    )
                    result = RuntimeResult(
                        RuntimeStatus.PAUSED,
                        f"Usage policy block ({policy_result.blocked_reason.value})",
                        [
                            f"[{ai_name}] Input screened by Usage Policy.",
                            f"[{ai_name}] {policy_result.block_message}",
                        ],
                        [f"[{ai_name}] {policy_result.block_message}"],
                        [],
                        policy_result.block_message,
                    )
                    return result
                # Log allowed conversation if logging is enabled
                if _policy_log:
                    _policy_log(task, ai_name, policy_settings)

        # ── PARENTAL CONTROLS — Kid Safety Screening (legacy) ──
        # Screen all user input through parental controls BEFORE governance sanitizer.
        # When parental controls are enabled, this is the first line of defense.
        # Blocked content is never saved to memory and parent alerts are generated.
        if _parental_screen and _load_parental:
            parental_settings = _load_parental()
            if parental_settings.get("enabled", False):
                parental_result = _parental_screen(task, parental_settings)
                if not parental_result.allowed:
                    # Log the conversation attempt for parent review
                    if _parental_log:
                        _parental_log(task, ai_name, parental_settings)
                    # Alert parent if needed
                    if parental_result.alert_parent and _parental_alert:
                        _parental_alert(
                            f"Parental Controls blocked input from {ai_name}: "
                            f"{parental_result.blocked_reason.value} — "
                            f"matched: {', '.join(parental_result.matched_keywords[:5])}",
                            parental_settings,
                        )
                    self._tier_audit.log_present(
                        category=AuditCategory.GUARDRAIL,
                        action=f"Parental controls blocked input ({parental_result.blocked_reason.value})",
                        detail=f"{parental_result.block_message[:200]}",
                        source="parental_controls_enforcer",
                        capability=intent,
                    )
                    self._log_tool_audit(
                        tool="ParentalControlsEnforcer",
                        action=f"PARENTAL_BLOCKED:{parental_result.blocked_reason.value}",
                        target=task[:200],
                        approved=False,
                        status="blocked",
                    )
                    # Do NOT save blocked content to memory
                    result = RuntimeResult(
                        RuntimeStatus.PAUSED,
                        f"Parental block ({parental_result.blocked_reason.value})",
                        [
                            f"[{ai_name}] Input screened by Parental Controls.",
                            f"[{ai_name}] {parental_result.block_message}",
                        ],
                        [f"[{ai_name}] {parental_result.block_message}"],
                        ["Next: ask your parent if you have questions about this topic."],
                        parental_result.block_message,
                    )
                    return result
                # Log allowed conversation if logging is enabled
                if _parental_log and parental_settings.get("log_all_conversations", True):
                    _parental_log(task, ai_name, parental_settings)

        # ── GOVERNANCE SANITIZER — Content Screening ──
        # Screen all user input through the governance sanitizer before any
        # processing. Blocked content is NEVER saved to memory and the
        # ethical-use banner is shown.
        if _sanitize_input:
            sanitization = _sanitize_input(task)
            if not sanitization.is_clean:
                banner = _ETHICAL_BANNER or ""
                violation_msg = sanitization.violation_detail or "Content blocked by governance sanitizer."
                self._tier_audit.log_present(
                    category=AuditCategory.GUARDRAIL,
                    action=f"Governance sanitizer blocked input ({sanitization.violation_type.value})",
                    detail=f"{violation_msg[:200]} | Banner: {banner}",
                    source="governance_sanitizer",
                    capability=intent,
                )
                self._log_tool_audit(
                    tool="GovernanceSanitizer",
                    action=f"INPUT_BLOCKED:{sanitization.violation_type.value}",
                    target=task[:200],
                    approved=False,
                    status="blocked",
                )
                # Do NOT save blocked content to memory — return immediately
                result = RuntimeResult(
                    RuntimeStatus.PAUSED,
                    f"Governance block ({sanitization.violation_type.value})",
                    [
                        f"[{ai_name}] Input screened by governance sanitizer.",
                        f"[{ai_name}] Violation: {sanitization.violation_type.value} — {violation_msg}",
                    ],
                    [
                        f"[{ai_name}] {violation_msg}",
                        f"[SYSTEM] {banner}",
                    ],
                    ["Next: rephrase the task within ethical and legal boundaries."],
                    f"{violation_msg}\n\n{banner}",
                )
                # Do NOT call _learn_from_mission — blocked content must never be saved to memory
                return result

        # RAG: Retrieve relevant document chunks from the Knowledge Base
        rag_context = self._rag_retrieve(task)
        if rag_context:
            if knowledge:
                knowledge = knowledge + "\n\n" + rag_context
            else:
                knowledge = rag_context

        thought = [
            f"[{ai_name}] Runtime received task.",
            f"[{ai_name}] Intent detected: {intent}.",
            f"[{ai_name}] Active capabilities: {', '.join(sorted(abilities)) if abilities else 'none detected'}.",
            f"[{ai_name}] Knowledge/Intelligence profile: {'connected' if knowledge else 'not found'}.",
            f"[{ai_name}] RAG knowledge base: {'retrieved' if rag_context else 'empty or not queried'}.",
        ]

        # Three-tier audit: log PAST (what was received), PRESENT (what's being done), FUTURE (what will happen)
        self._tier_audit.log_past(
            category=AuditCategory.CAPABILITY,
            action=f"Task received: {task[:100]}",
            detail=f"Intent: {intent}, Capabilities: {', '.join(sorted(abilities)) if abilities else 'none'}",
            source="user input",
            capability=intent,
            confidence="high",
        )
        self._tier_audit.log_present(
            category=AuditCategory.CAPABILITY,
            action=f"Processing task with intent: {intent}",
            detail=f"AI: {ai_name}, Knowledge: {'connected' if knowledge else 'not found'}",
            source="runtime",
            capability=intent,
        )
        self._tier_audit.log_future(
            category=AuditCategory.CAPABILITY,
            action=f"Will execute {intent} workflow",
            detail="Pending guardrail screening and capability check",
            capability=intent,
        )

        # ── GUARDRAIL SCREENING ──
        # All four layers check the task before any capability dispatch.
        # If any layer blocks, the task is paused with the block message.
        blocked, block_msg, block_layer = self._check_guardrails(task, intent)
        if blocked:
            self._tier_audit.log_present(
                category=AuditCategory.GUARDRAIL,
                action=f"Guardrail blocked task ({block_layer})",
                detail=block_msg[:200],
                source="guardrail_engine",
                capability=intent,
            )
            result = RuntimeResult(
                RuntimeStatus.PAUSED,
                f"Guardrail block ({block_layer})",
                thought + [f"[{ai_name}] Task screened by guardrail layer: {block_layer}."],
                [f"[{ai_name}] {block_msg}"],
                ["Next: rephrase the task within ethical and legal boundaries."],
                block_msg,
            )
            # Do NOT save blocked content to memory
            return result

        # ── ANTI-PROBING SCREENING ──
        # Detect and block indirect attempts to extract information about
        # internal architecture, memory systems, or proprietary methods.
        probing_blocked, probing_msg = self._check_probing_guardrails(task)
        if probing_blocked:
            self._tier_audit.log_present(
                category=AuditCategory.GUARDRAIL,
                action="Probing guardrail blocked task",
                detail=probing_msg[:200],
                source="probing_guardrails",
                capability=intent,
            )
            result = RuntimeResult(
                RuntimeStatus.PAUSED,
                "Probing attempt blocked",
                thought + [f"[{ai_name}] Task blocked by anti-probing guardrail."],
                [f"[{ai_name}] {probing_msg}"],
                ["Next: ask about Command Nexus features you can use."],
                probing_msg,
            )
            # Do NOT save blocked content to memory
            return result

        if not self._capability_allowed(intent, abilities):
            self._tier_audit.log_past(
                category=AuditCategory.CAPABILITY,
                action="Capability not attached â€” task paused",
                detail=f"Required capability '{intent}' is not attached to this AI.",
                capability=intent,
                confidence="high",
            )
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

        # Set temperature override for high-risk capabilities (legal, medical, financial, security)
        # 0.2 = near-deterministic for precision-critical tasks; None = backend default for everything else
        self._current_temperature = 0.2 if intent in self._HIGH_RISK_INTENTS else None
        self._current_intent = intent

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
        elif intent == "Financial Gainer":
            result = self._run_financial_gainer(task, ai_name, meta, knowledge, thought)
        elif intent == "Memory Recorder":
            result = self._run_memory_recorder(task, ai_name, meta, knowledge, thought)
        elif intent == "Activity Watcher":
            result = self._run_activity_watcher(task, ai_name, meta, knowledge, thought)
        elif intent == "Game Companion":
            result = self._run_game_companion(task, ai_name, meta, knowledge, thought)
        elif intent == "Email Automation":
            result = self._run_email_automation(task, ai_name, meta, knowledge, thought)
        elif intent == "API Integrator":
            result = self._run_api_integrator(task, ai_name, meta, knowledge, thought)
        elif intent == "Team Orchestrator":
            result = self._run_team_orchestrator(task, ai_name, meta, knowledge, thought)
        elif intent == "Voice Interface":
            result = self._run_voice_interface(task, ai_name, meta, knowledge, thought)
        elif intent == "Visual Canvas":
            result = self._run_visual_canvas(task, ai_name, meta, knowledge, thought)
        elif intent == "Medical Researcher":
            result = self._run_medical_researcher(task, ai_name, meta, knowledge, thought)
        elif intent == "Legal Document Reviewer":
            result = self._run_legal_document_reviewer(task, ai_name, meta, knowledge, thought)
        elif intent == "Wellness Coach":
            result = self._run_wellness_coach(task, ai_name, meta, knowledge, thought)
        elif intent == "Content Strategist":
            result = self._run_content_strategist(task, ai_name, meta, knowledge, thought)
        elif intent == "Fact Checker":
            result = self._run_fact_checker(task, ai_name, meta, knowledge, thought)
        elif intent == "Task Scheduler":
            result = self._run_task_scheduler(task, ai_name, meta, knowledge, thought)
        elif intent == "Form Builder":
            result = self._run_form_builder(task, ai_name, meta, knowledge, thought)
        elif intent == "Report Generator":
            result = self._run_report_generator(task, ai_name, meta, knowledge, thought)
        elif intent == "Invoice Processor":
            result = self._run_invoice_processor(task, ai_name, meta, knowledge, thought)
        elif intent == "Spreadsheet Analyst":
            result = self._run_spreadsheet_analyst(task, ai_name, meta, knowledge, thought)
        elif intent == "Data Visualizer":
            result = self._run_data_visualizer(task, ai_name, meta, knowledge, thought)
        elif intent == "Statistical Modeler":
            result = self._run_statistical_modeler(task, ai_name, meta, knowledge, thought)
        elif intent == "Trend Forecaster":
            result = self._run_trend_forecaster(task, ai_name, meta, knowledge, thought)
        elif intent == "DevOps Assistant":
            result = self._run_devops_assistant(task, ai_name, meta, knowledge, thought)
        elif intent == "Database Manager":
            result = self._run_database_manager(task, ai_name, meta, knowledge, thought)
        elif intent == "Test Generator":
            result = self._run_test_generator(task, ai_name, meta, knowledge, thought)
        elif intent == "Documentation Generator":
            result = self._run_documentation_generator(task, ai_name, meta, knowledge, thought)
        elif intent == "Script Writer":
            result = self._run_script_writer(task, ai_name, meta, knowledge, thought)
        elif intent == "Copy Editor":
            result = self._run_copy_editor(task, ai_name, meta, knowledge, thought)
        elif intent == "Podcast Planner":
            result = self._run_podcast_planner(task, ai_name, meta, knowledge, thought)
        elif intent == "Brand Strategist":
            result = self._run_brand_strategist(task, ai_name, meta, knowledge, thought)
        elif intent == "Presentation Coach":
            result = self._run_presentation_coach(task, ai_name, meta, knowledge, thought)
        elif intent == "PR Assistant":
            result = self._run_pr_assistant(task, ai_name, meta, knowledge, thought)
        elif intent == "Internal Comms Writer":
            result = self._run_internal_comms_writer(task, ai_name, meta, knowledge, thought)
        elif intent == "Academic Citation Manager":
            result = self._run_academic_citation_manager(task, ai_name, meta, knowledge, thought)
        elif intent == "Patent Researcher":
            result = self._run_patent_researcher(task, ai_name, meta, knowledge, thought)
        elif intent == "Market Analyst":
            result = self._run_market_analyst(task, ai_name, meta, knowledge, thought)
        elif intent == "Recipe Planner":
            result = self._run_recipe_planner(task, ai_name, meta, knowledge, thought)
        elif intent == "Travel Planner":
            result = self._run_travel_planner(task, ai_name, meta, knowledge, thought)
        elif intent == "Event Planner":
            result = self._run_event_planner(task, ai_name, meta, knowledge, thought)
        elif intent == "Personal Finance Manager":
            result = self._run_personal_finance_manager(task, ai_name, meta, knowledge, thought)
        elif intent == "Privacy Compliance Checker":
            result = self._run_privacy_compliance_checker(task, ai_name, meta, knowledge, thought)
        elif intent == "Data Governance Advisor":
            result = self._run_data_governance_advisor(task, ai_name, meta, knowledge, thought)
        elif intent == "Curriculum Designer":
            result = self._run_curriculum_designer(task, ai_name, meta, knowledge, thought)
        elif intent == "Exam Prep Coach":
            result = self._run_exam_prep_coach(task, ai_name, meta, knowledge, thought)
        else:
            result = self._run_chat(task, ai_name, meta, knowledge, thought)

        # Three-tier audit: log what actually happened (PAST)
        status_str = getattr(result.status, 'value', str(result.status))
        _is_local = "local fallback" in result.title.lower() or "local intelligence" in result.title.lower()
        self._tier_audit.log_past(
            category=AuditCategory.LOCAL_RESPONSE if _is_local else AuditCategory.MODEL_CALL,
            action=f"Task completed: {result.title}",
            detail=f"Status: {status_str}, Intent: {intent}",
            source="local intelligence (no backend)" if _is_local else "model backend",
            evidence=result.result_text[:200] if result.result_text else "",
            capability=intent,
            confidence="medium" if _is_local else "high",
        )

        # ── OUTPUT SCREENING ──
        # Screen AI output through governance sanitizer and output probing check.
        # If the output contains violations, erase them and show the ethical-use banner.
        output_blocked = False
        if result.result_text:
            # Check for leaked internal architecture references
            probing_blocked, probing_replacement = self._check_output_probing(result.result_text)
            if probing_blocked:
                result.result_text = probing_replacement
                output_blocked = True

            # Check through governance sanitizer
            if _sanitize_input:
                out_san = _sanitize_input(result.result_text)
                if not out_san.is_clean:
                    banner = _ETHICAL_BANNER or ""
                    result.result_text = (
                        f"[Content blocked by governance sanitizer: {out_san.violation_detail}]\n\n{banner}"
                    )
                    output_blocked = True
                    self._tier_audit.log_present(
                        category=AuditCategory.GUARDRAIL,
                        action=f"Output blocked by sanitizer ({out_san.violation_type.value})",
                        detail=out_san.violation_detail[:200],
                        source="governance_sanitizer",
                        capability=intent,
                    )

        # Only save to memory if the output was clean (or after sanitization)
        if not output_blocked:
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
        # All AIs can use tools â€” this is an all-in-one program
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
        if intent not in abilities:
            # Tool User is a privileged capability: only AIs explicitly given Tool User
            # (or Agent) may invoke the governed tool loop, not every nearby capability.
            if intent == "Tool User" and "Tool User" in abilities:
                pass  # fall through to tier check below
            else:
                return False

        # Backend entitlement enforcement: verify the capability is unlocked
        # for the user's current membership tier. This prevents bypassing UI
        # restrictions by editing local files or reaching hidden code paths.
        try:
            from .membership_tiers import is_capability_unlocked, get_effective_tier, load_purchased_capabilities
            tier = get_effective_tier()
            purchased = load_purchased_capabilities()
            if not is_capability_unlocked(intent, tier, purchased):
                return False
        except Exception:
            # If we can't verify entitlement, default to restricted.
            return False

        return True

    def _classify(self, task: str) -> str:
        t = task.lower()

        # ── High-specificity capabilities checked first ──
        # Medical and Legal must be checked before generic Research/Coder
        # so their guardrails are applied with the correct capability context.

        if any(x in t for x in [
            "medical", "medicine", "medication", "drug interaction", "clinical trial",
            "pubmed", "side effect", "dosage", "diagnos", "symptom", "treatment",
            "disease", "health condition", "pharmaceutical", "prescription", "patient",
            "epidemiolog", "medical research", "medical literature", "evidence based medicine",
        ]):
            return "Medical Researcher"

        if any(x in t for x in [
            "legal", "contract", "clause", "provision", "nda", "non-compete",
            "non-disclosure", "terms of service", "agreement", "liability",
            "indemnif", "termination clause", "statute", "case law", "precedent",
            "enforceable", "legal document", "legal review", "legal analysis",
            "obligation", "breach of contract", "warranty", "arbitration",
        ]):
            return "Legal Document Reviewer"

        if any(x in t for x in [
            "research", "look up", "lookup", "search", "find sources", "sources", "citation",
            "cite", "verify", "current", "latest", "web search", "search the web", "websearch",
            "internet", "news", "game mechanics",
        ]):
            return "Research"

        # Capability questions must be checked BEFORE specific intent keywords
        # so "what can you do in coding?" routes to Chatbot (lists capabilities)
        # instead of Coder (sends a coding prompt that triggers security refusal)
        if any(x in t for x in ["what can you do", "what can i do", "help me with", "what are your capabilities", "what do you do", "what are you good at", "what can you make", "what can you create", "what can you build"]):
            return "Chatbot"

        if any(x in t for x in [
            "code", "bug", "python", "javascript", "html", "css", "function", "class", "error", "traceback", "fix script", "patch",
            "user interface", " ui ", " gui ", "button", "widget", "web page", "webpage", "desktop app", "web app",
            "write me a program", "build me a program", "make me an app", "build me an app", "write a script",
        ]):
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

        if any(x in t for x in [
            "crypto", "bitcoin", "ethereum", "token", "altcoin", "defi", "blockchain",
            "affiliate", "commission", "click commission", "referral link",
            "sales funnel", "landing page", "upsell", "email sequence",
            "side hustle", "gig", "freelance", "micro-business", "passive income",
            "monetize", "monetization", "sell my skill", "course creation",
            "investment", "stock", "etf", "real estate investing", "portfolio",
            "roi", "return on investment", "break-even", "profit margin",
            "market gap", "underserved market", "competitive gap",
            "negotiate", "negotiation", "salary negotiation", "rate negotiation",
            "make money", "earn money", "income opportunity", "financial gain",
        ]):
            return "Financial Gainer"

        if any(x in t for x in [
            "record session", "replay session", "session replay", "playback",
            "recall", "smart recall", "search history", "search past",
            "decision track", "track decision", "decision history",
            "knowledge archive", "archive knowledge", "save knowledge",
            "habit track", "track habit", "habit log",
            "progress journal", "track progress", "journal progress",
            "context keeper", "restore context", "where i left off",
            "audit trail", "compliance trail", "audit report",
            "memory recorder", "record everything", "flight recorder",
        ]):
            return "Memory Recorder"

        if any(x in t for x in [
            "watch my activity", "activity watch", "watch what i do",
            "learn my pattern", "suggest improvement", "work faster",
            "task mimic", "workflow learner", "activity monitor",
            "task recorder", "observe my work",
        ]):
            return "Activity Watcher"

        if any(x in t for x in [
            "play game", "game companion", "game strategy", "board game",
            "card game", "video game", "chess", "puzzle game",
            "learn game", "game rules", "game mechanic",
        ]):
            return "Game Companion"

        # Email Automation â€” drafting, organizing, and managing email
        if any(x in t for x in [
            "email", "draft email", "email draft", "compose email", "inbox",
            "email template", "email sequence", "auto reply", "auto-reply",
            "mail merge", "newsletter", "email campaign", "follow-up email",
        ]):
            return "Email Automation"

        # API Integrator â€” connecting external APIs and services
        if any(x in t for x in [
            "api", "rest api", "webhook", "integration", "connect api",
            "api key", "endpoint", "api call", "api integration",
            "third-party service", "external service", "zapier", "make.com",
        ]):
            return "API Integrator"

        # Team Orchestrator â€” multi-AI coordination
        if any(x in t for x in [
            "team orchestrat", "multi-agent", "coordinate ai", "ai team",
            "delegate to ai", "multi-ai", "agent coordination",
            "assign task to", "workflow handoff", "team workflow",
        ]):
            return "Team Orchestrator"

        # Voice Interface â€” voice commands and speech
        if any(x in t for x in [
            "voice", "speech", "speak", "microphone", "mic input",
            "voice command", "voice control", "talk to ai", "dictation",
            "text to speech", "read aloud", "voice input",
        ]):
            return "Voice Interface"

        # Visual Canvas â€” visual workspace, drawing, diagrams
        if any(x in t for x in [
            "visual canvas", "draw", "diagram", "whiteboard",
            "visual workspace", "canvas", "sketch", "flowchart",
            "mind map", "visual layout", "drawing board",
        ]):
            return "Visual Canvas"

        if any(x in t for x in ["sales", "marketing", "hr", "sop", "business", "support reply"]):
            return "Business Workflow"

        if any(x in t for x in ["hephaestus", "design brief", "prototype", "material spec", "handoff brief"]):
            return "Hephaestus Relay"

        if any(x in t for x in ["analyze data", "data analyst", "dataset", "statistics", "chart", "pivot", "data trend", "data visualization", "survey analysis", "analyze survey", "survey response", "survey result"]):
            return "Data Analyst Pro"

        if any(x in t for x in ["code review", "review code", "security scan", "quality check", "lint", "best practice"]):
            return "Code Reviewer"

        if any(x in t for x in ["meeting agenda", "facilitate meeting", "action item", "meeting note", "standup", "retrospective"]):
            return "Meeting Facilitator"

        if any(x in t for x in ["security audit", "vulnerability", "penetration", "compliance scan", "security assessment"]):
            return "Security Auditor"

        # Wellness Coach — fitness, nutrition, mental wellness, habit building
        if any(x in t for x in [
            "wellness", "fitness", "workout", "exercise", "nutrition", "diet plan",
            "meal plan", "mental health", "stress management", "mindfulness",
            "meditation", "habit building", "habit tracker", "sleep hygiene",
            "healthy lifestyle", "weight loss", "muscle gain", "calorie",
            "wellbeing", "well-being", "self-care", "health coach",
        ]):
            return "Wellness Coach"

        # Content Strategist — content calendar, audience analysis, platform optimization
        if any(x in t for x in [
            "content strategy", "content calendar", "content plan", "audience analysis",
            "platform optimization", "content repurpose", "brand voice",
            "social media strategy", "content marketing", "editorial calendar",
            "content schedule", "engagement strategy", "content funnel",
            "repurpose content", "cross-platform content",
        ]):
            return "Content Strategist"

        # Fact Checker — claim verification, credibility assessment, bias detection
        if any(x in t for x in [
            "fact check", "fact-check", "verify claim", "verification", "credibility",
            "misinformation", "disinformation", "fake news", "source check",
            "debunk", "truth check", "accuracy check", "claim verification",
            "is this true", "is this accurate", "is this real",
        ]):
            return "Fact Checker"

        # ── Phase 7: New canonical intents ──

        # Task Scheduler — scheduling and time management
        if any(x in t for x in [
            "schedule task", "task schedule", "time block", "time blocking",
            "remind me at", "set reminder", "schedule reminder", "appointment",
            "book appointment", "schedule meeting", "calendar event",
        ]):
            return "Task Scheduler"

        # Form Builder — create forms, surveys, questionnaires
        if any(x in t for x in [
            "build form", "create form", "form builder", "survey builder",
            "questionnaire", "create survey", "form template", "form field",
            "google form", "typeform", "survey question",
        ]):
            return "Form Builder"

        # Report Generator — generate structured reports
        if any(x in t for x in [
            "generate report", "report generator", "create report",
            "monthly report", "weekly report", "annual report",
            "performance report", "summary report", "business report",
        ]):
            return "Report Generator"

        # Invoice Processor — invoice creation and processing
        if any(x in t for x in [
            "invoice", "billing", "create invoice", "process invoice",
            "payment request", "bill client", "invoice template",
            "invoice generator", "tax invoice",
        ]):
            return "Invoice Processor"

        # Spreadsheet Analyst — advanced spreadsheet operations
        if any(x in t for x in [
            "spreadsheet", "excel formula", "vlookup", "pivot table",
            "spreadsheet formula", "cell reference", "conditional format",
            "google sheets", "excel macro", "spreadsheet analysis",
        ]):
            return "Spreadsheet Analyst"

        # Data Visualizer — charts, graphs, visual data representation
        if any(x in t for x in [
            "data visualization", "create chart", "create graph",
            "plot data", "visualize data", "bar chart", "line graph",
            "pie chart", "scatter plot", "heatmap", "data viz",
        ]):
            return "Data Visualizer"

        # Statistical Modeler — statistical analysis and modeling
        if any(x in t for x in [
            "statistical", "regression", "correlation", "hypothesis test",
            "p-value", "confidence interval", "standard deviation",
            "statistical model", "anova", "t-test", "chi-square",
        ]):
            return "Statistical Modeler"

        # Trend Forecaster — forecasting and prediction
        if any(x in t for x in [
            "forecast", "trend analysis", "predict trend", "projection",
            "time series", "future prediction", "demand forecast",
            "market forecast", "growth projection",
        ]):
            return "Trend Forecaster"

        # DevOps Assistant — deployment, CI/CD, infrastructure
        if any(x in t for x in [
            "devops", "deployment", "ci/cd", "pipeline", "docker",
            "kubernetes", "container", "infrastructure as code",
            "terraform", "ansible", "deploy", "rollout",
        ]):
            return "DevOps Assistant"

        # Database Manager — database operations and queries
        if any(x in t for x in [
            "database", "sql query", "sql", "database schema", "db design",
            "table structure", "database optimization", "query optimization",
            "postgresql", "mysql", "sqlite", "mongodb",
        ]):
            return "Database Manager"

        # Test Generator — automated test creation
        if any(x in t for x in [
            "test generator", "generate test", "unit test", "test case",
            "test suite", "automated test", "test coverage", "mock test",
            "pytest", "unittest", "jest test",
        ]):
            return "Test Generator"

        # Documentation Generator — code and API documentation
        if any(x in t for x in [
            "documentation generator", "generate docs", "api docs",
            "code documentation", "docstring", "readme generator",
            "api documentation", "sdk docs", "technical documentation",
        ]):
            return "Documentation Generator"

        # Script Writer — screenplays, video scripts, podcast scripts
        if any(x in t for x in [
            "screenplay", "script writer", "video script", "podcast script",
            "movie script", "tv script", "scene writing", "dialogue writing",
            "monologue", "screenwriting",
        ]):
            return "Script Writer"

        # Copy Editor — editing and proofreading
        if any(x in t for x in [
            "copy editor", "proofread", "edit copy", "grammar check",
            "proofreading", "copy editing", "line edit", "style edit",
            "copy review", "manuscript edit",
        ]):
            return "Copy Editor"

        # Podcast Planner — podcast planning and production
        if any(x in t for x in [
            "podcast", "podcast plan", "podcast outline", "episode plan",
            "podcast topic", "podcast format", "show notes", "podcast script",
        ]):
            return "Podcast Planner"

        # Brand Strategist — brand identity and positioning
        if any(x in t for x in [
            "brand strategy", "brand identity", "brand positioning",
            "brand guidelines", "brand book", "brand voice", "brand messaging",
            "rebrand", "brand audit",
        ]):
            return "Brand Strategist"

        # Presentation Coach — presentation preparation and coaching
        if any(x in t for x in [
            "presentation coach", "presentation prep", "speech coach",
            "pitch deck", "improve presentation", "presentation feedback",
            "public speaking", "slide review",
        ]):
            return "Presentation Coach"

        # PR Assistant — press releases and public relations
        if any(x in t for x in [
            "press release", "pr assistant", "public relations", "media pitch",
            "pr campaign", "crisis communication", "media relations",
            "press kit", "pr strategy",
        ]):
            return "PR Assistant"

        # Internal Comms Writer — internal company communications
        if any(x in t for x in [
            "internal comms", "company announcement", "internal memo",
            "team update", "all-hands", "employee newsletter",
            "internal communication", "staff memo",
        ]):
            return "Internal Comms Writer"

        # Academic Citation Manager — citation management and formatting
        if any(x in t for x in [
            "citation", "bibliography", "reference list", "cite source",
            "apa format", "mla format", "chicago style", "citation manager",
            "format citation", "works cited",
        ]):
            return "Academic Citation Manager"

        # Patent Researcher — patent search and analysis
        if any(x in t for x in [
            "patent", "patent search", "patent research", "intellectual property",
            "patent filing", "patent application", "prior art", "patent claim",
        ]):
            return "Patent Researcher"

        # Market Analyst — market research and analysis
        if any(x in t for x in [
            "market analysis", "market analyst", "competitor analysis",
            "market size", "market share", "industry analysis",
            "market landscape", "competitive landscape", "tam sam som",
        ]):
            return "Market Analyst"

        # Recipe Planner — meal planning and recipes
        if any(x in t for x in [
            "recipe", "meal plan", "recipe planner", "what to cook",
            "dinner idea", "meal prep recipe", "cooking recipe",
            "dietary recipe", "healthy recipe",
        ]):
            return "Recipe Planner"

        # Travel Planner — trip planning and itineraries
        if any(x in t for x in [
            "travel plan", "trip planner", "itinerary", "vacation plan",
            "travel itinerary", "trip idea", "travel route", "book trip",
        ]):
            return "Travel Planner"

        # Event Planner — event planning and coordination
        if any(x in t for x in [
            "event plan", "event planner", "party plan", "conference plan",
            "wedding plan", "event coordination", "event logistics",
            "event checklist",
        ]):
            return "Event Planner"

        # Personal Finance Manager — budgeting and personal finance
        if any(x in t for x in [
            "personal finance", "budget plan", "expense tracker",
            "financial planning", "save money", "debt management",
            "retirement planning", "financial goal", "money management",
        ]):
            return "Personal Finance Manager"

        # Privacy Compliance Checker — privacy regulation compliance
        if any(x in t for x in [
            "privacy compliance", "gdpr", "ccpa", "privacy policy",
            "data privacy", "privacy regulation", "privacy law",
            "data protection", "privacy audit",
        ]):
            return "Privacy Compliance Checker"

        # Data Governance Advisor — data governance and stewardship
        if any(x in t for x in [
            "data governance", "data steward", "data catalog",
            "data lineage", "data quality", "data management policy",
            "data classification", "data retention",
        ]):
            return "Data Governance Advisor"

        # Curriculum Designer — curriculum and course design
        if any(x in t for x in [
            "curriculum", "curriculum design", "course curriculum",
            "syllabus", "learning objectives", "curriculum map",
            "course outline", "educational program",
        ]):
            return "Curriculum Designer"

        # Exam Prep Coach — exam preparation and study coaching
        if any(x in t for x in [
            "exam prep", "test prep", "exam coach", "study plan for exam",
            "practice exam", "exam strategy", "sat prep", "gre prep",
            "certification prep", "bar exam",
        ]):
            return "Exam Prep Coach"

        return "Chatbot"

    def _derive_book_key(self, uuid: str) -> bytes:
        return _shared_derive_book_key(uuid)

    def _decrypt_book(self, data: bytes, uuid: str) -> str:
        return _shared_decrypt_book(data, uuid, errors="replace")

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

    def _rag_retrieve(self, task: str) -> str:
        """Retrieve relevant document chunks from the RAG Knowledge Base."""
        try:
            from .rag_engine import RAGEngine
            rag = RAGEngine()
            docs = rag.list_documents()
            if not docs:
                return ""
            return rag.retrieve_for_prompt(task)
        except Exception:
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
        """Honest FAILED result when local intelligence is running in fallback mode."""
        provider_name = backend_response.display_name or backend_response.provider_id or "selected backend"
        return RuntimeResult(
            RuntimeStatus.FAILED,
            f"{ai_name}'s backend is offline",
            thought + [
                f"[{ai_name}] AI exists and capability routing worked.",
                f"[{ai_name}] Backend call failed: {provider_name} is offline or unavailable.",
                f"[{ai_name}] Error: {backend_response.error}",
            ],
            [f"[{ai_name}] Task did not complete because the local intelligence is running in fallback mode."],
            [
                "Next: The built-in local intelligence is active. You can configure a different model in Backend settings for enhanced capabilities.",
                "Backend config is in the Visibility Window: Backend > Configure Backend.",
            ],
            f"{ai_name} is active, but her local intelligence is running in fallback mode.\n\n"
            f"Provider: {provider_name}\n"
            f"Error: {backend_response.error}\n\n"
            "The built-in local intelligence is active. You can configure a different model in Backend settings for enhanced capabilities.",
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
        parts.append(f"[Local Intelligence â€” {ai_name}]")
        parts.append("")
        parts.append(f"I heard: \"{task}\"")
        parts.append("")

        has_knowledge = bool(knowledge_excerpt.strip())
        has_memory = bool(memory_text.strip())

        task_lower = task.lower()
        identity_q = any(k in task_lower for k in [
            "who am i", "who is the user", "what do you know about me",
            "what's my name", "what is my name", "do you know me",
        ])
        cap_q = any(k in task_lower for k in [
            "what can you do", "help me", "what are you", "capabilities", "what do you do",
            "what kind of", "what kinds of", "explain what your", "what coding", "what code",
        ])

        # Show knowledge context (skipped for direct identity/capability answers)
        if has_knowledge and not identity_q and not cap_q:
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

        # Intent: identity question — answered from saved configuration or learned memory,
        # never hard-coded. If nothing is saved, say so clearly.
        if identity_q:
            saved_name = ""
            notes = str(meta.get("context_notes", "") or "")
            m_note = re.search(r"address the user as\s+([^.\n;]+)", notes, re.IGNORECASE)
            if m_note:
                saved_name = m_note.group(1).strip()
            if saved_name:
                parts.append(f"From your saved configuration: you are {saved_name}.")
                parts.append("That's what this AI's setup instructions say, and it's how I'll address you.")
            else:
                name_mem = [m for m in preference_memories if "name" in m.content.lower()]
                if name_mem:
                    parts.append("Here's what I remember about you:")
                    for m in name_mem[:3]:
                        parts.append(f"  - {m.content[:120]}")
                else:
                    parts.append("I don't have any saved information about who you are yet.")
                    parts.append(
                        "You can set a preferred form of address in this AI's setup notes in the Forge, "
                        "or just tell me — I'll remember it."
                    )

        # Intent: capabilities question
        elif cap_q:
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
            parts.append("I'm answering from local rules right now because no model backend responded.")
            parts.append("For full AI-generated answers, connect a backend in the Visibility Window → Backend settings.")

        # Intent: preference statement
        elif any(k in task_lower for k in ["prefer", "like", "always", "never", "remember", "dislike", "hate", "want", "need"]):
            parts.append("Got it â€” I've saved that to my local memory and will remember it for future tasks.")
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
                parts.append("I'm fresh and ready to learn â€” the more we work together, the better I'll understand your needs.")

        # Intent: how to use a specific capability
        elif any(k in task_lower for k in ["how do i", "how to", "where is", "where do", "show me how", "teach me how"]):
            parts.append("Here's how to use Command Nexus:")
            parts.append("")
            parts.append("  ðŸ§  AI Forge â€” Create and customize AI assistants")
            parts.append("  ðŸ“š Intelligence â€” Add memory and knowledge to your AI")
            parts.append("  â¬†ï¸ Upgrades â€” Browse and unlock more capabilities")
            parts.append("  ðŸ›¡ï¸ Governance â€” Safety controls, audit logs, parental controls")
            parts.append("  ðŸ¤– Support â€” Get help from the Customer Support AI")
            parts.append("  ðŸŽ¯ Mission Control â€” Type a task and click START")
            parts.append("")
            parts.append("Just type what you want in plain language. No coding required!")

        # Intent: question
        elif "?" in task:
            parts.append("Let me see if I can help with that question.")
            if has_knowledge:
                # Try to find relevant knowledge for the question
                task_words = set(w.lower() for w in task.split() if len(w) > 3)
                relevant = []
                for line in knowledge_excerpt.splitlines():
                    line_stripped = line.strip()
                    if not line_stripped:
                        continue
                    line_words = set(w.lower() for w in line_stripped.split() if len(w) > 3)
                    overlap = task_words & line_words
                    if overlap:
                        relevant.append((len(overlap), line_stripped))
                relevant.sort(key=lambda x: -x[0])
                if relevant:
                    parts.append("From my knowledge profile, here's what I found:")
                    for _, line in relevant[:5]:
                        parts.append(f"  {line}")
                    parts.append("")
                else:
                    parts.append("My knowledge profile doesn't have a direct match for this question.")
                    parts.append("However, here's some general context:")
                    for line in knowledge_excerpt.splitlines()[:5]:
                        if line.strip():
                            parts.append(f"  {line.strip()}")
                    parts.append("")
            if preference_memories:
                parts.append("I also remember your preferences and past interactions.")
            parts.append("")
            parts.append("For a complete AI-powered answer, connect a model backend in the Visibility Window → Backend settings. Right now I'm answering from local rules and your saved context.")

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
            parts.append("I can act on this using my built-in local intelligence. You can configure a different model in Backend settings for enhanced capabilities.")
            parts.append("")
            parts.append("In the meantime, I can:")
            parts.append("  - Plan this task (use the Planner capability)")
            parts.append("  - Break it into steps (just ask me to plan)")
            parts.append("  - Read or write files (use Tool User capability)")
            parts.append("  - Remember your preferences for next time")
            parts.append("  - Process documents (paste text or use Document Processor)")

        parts.append("")
        parts.append("[Local Intelligence Mode]")

        result_text = "\n".join(parts)
        return RuntimeResult(
            RuntimeStatus.COMPLETED,
            "Local intelligence response",
            thought + [
                f"[{ai_name}] Running in local mode; using local intelligence.",
                f"[{ai_name}] Knowledge: {'connected' if has_knowledge else 'not found'}, Memory: {'connected' if has_memory else 'empty'}.",
                f"[{ai_name}] Produced a context-aware local response with continuity.",
            ],
            [f"[{ai_name}] Returned local intelligence response (clearly labeled, not faking backend)."],
            ["Next: the built-in local model provides AI reasoning, or configure Backend settings for more options."],
            result_text,
        )

    def _run_research(self, task, ai_name, meta, knowledge, thought):
        sources = self._brave_search(task) if self.brave_api_key else []

        # Three-tier audit: log whether research was actually performed
        if sources:
            self._tier_audit.log_past(
                category=AuditCategory.RESEARCH,
                action=f"Brave Search returned {len(sources)} sources",
                detail=f"Query: {task[:100]}",
                source="Brave Search API",
                evidence="; ".join(s.get('url', '') for s in sources[:3]),
                capability="Research",
                confidence="high",
            )
            self._tier_audit.log_past(
                category=AuditCategory.SOURCE_CITATION,
                action=f"Cited {len(sources[:8])} source candidates",
                detail="Sources provided to model for summarization",
                source="Brave Search API",
                capability="Research",
            )
        else:
            self._tier_audit.log_past(
                category=AuditCategory.LOCAL_RESPONSE,
                action="No research performed â€” no search API connected",
                detail="Research paused; AI cannot truthfully complete without sources",
                source="none",
                capability="Research",
                confidence="low",
            )

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
                thought + [f"[{ai_name}] Sources were collected, but local intelligence is running in fallback mode and could not summarize them."],
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
            f"[Local Mode â€” {ai_name} is running in local intelligence mode]\n\n"
            f"Code task: {task}\n\n"
            "Here is a practical plan for this code task:\n"
            "1. Identify the language and framework.\n"
            "2. Define the function/class signature.\n"
            "3. Write the core logic step by step.\n"
            "4. Add error handling for edge cases.\n"
            "5. Write a basic test case.\n\n"
            "Analysis checklist:\n"
            "- Security: Check for injection, auth bypass, sensitive data exposure.\n"
            "- Quality: Naming, structure, complexity, duplication.\n"
            "- Performance: N+1 queries, unnecessary allocations, hot paths.\n\n"
            "Full AI-generated code requires a model backend — none responded. "
            "Connect one in the Visibility Window → Backend settings and ask again."
        )
        return RuntimeResult(RuntimeStatus.COMPLETED, "Coder completed (local fallback)", thought + [f"[{ai_name}] Running in local mode; produced a structured code plan locally."], [f"[{ai_name}] Produced code plan and analysis checklist."], ["Next: review the plan. "], result)

    def _run_writer(self, task, ai_name, meta, knowledge, thought):
        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "writing"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Writer completed", thought + [f"[{ai_name}] Model backend produced writing output using Knowledge context."], [f"[{ai_name}] Returned draft/rewrite."], ["Next: revise tone or export after approval."], model.text)

        result = (
            f"[Local Mode â€” {ai_name} is running in local intelligence mode]\n\n"
            f"Writing task: {task}\n\n"
            "Here is a structured writing plan for this task:\n"
            "1. Identify the audience and purpose.\n"
            "2. Create an outline with key points.\n"
            "3. Draft the opening (hook + thesis).\n"
            "4. Develop body sections (one idea per paragraph).\n"
            "5. Write the conclusion (summary + call to action).\n"
            "6. Review tone, clarity, and conciseness.\n\n"
            "Style options:\n"
            "- Professional, casual, academic, creative, technical\n"
            "- Adjust length: brief, standard, detailed\n\n"
            "Full AI-generated writing requires a model backend — none responded. "
            "Connect one in the Visibility Window → Backend settings and ask again."
        )
        return RuntimeResult(RuntimeStatus.COMPLETED, "Writer completed (local fallback)", thought + [f"[{ai_name}] Running in local mode; produced a structured writing plan locally."], [f"[{ai_name}] Produced writing plan and style guide."], ["Next: review the plan. "], result)

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
        return RuntimeResult(RuntimeStatus.COMPLETED, "Planner completed (local fallback)", thought + [f"[{ai_name}] Built a local governed plan (local mode)."], [f"[{ai_name}] Planner capability executed locally."], ["Next: approve or adjust plan. "], result)

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
        return RuntimeResult(RuntimeStatus.COMPLETED, "Tutor completed (local fallback)", thought + [f"[{ai_name}] Tutor capability executed locally (local mode)."], [f"[{ai_name}] Created lesson scaffold."], ["Next: user answers check question. "], result)

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
        return RuntimeResult(RuntimeStatus.COMPLETED, "Business workflow completed (local fallback)", thought + [f"[{ai_name}] Business workflow executed locally (local mode)."], [f"[{ai_name}] Produced draft-safe workflow."], ["Next: review and approve outward actions. "], result)

    def _run_customer_support(self, task, ai_name, meta, knowledge, thought):
        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "customer_support"))
        if model.error:
            return self._backend_failure_result(ai_name, thought, model)
        if model.text:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Customer support completed", thought + [f"[{ai_name}] Model backend produced support response using Knowledge context."], [f"[{ai_name}] Returned customer-safe response."], ["Next: review response before sending to customer."], model.text)

        return RuntimeResult(
            RuntimeStatus.FAILED,
            "Running in local intelligence mode",
            thought + [f"[{ai_name}] Running in local intelligence mode; cannot produce a real customer support response."],
            [f"[{ai_name}] Task did not complete because no backend answered."],
            ["Next: configure a different model in Backend settings or add Ollama/OpenAI."],
            f"{ai_name} is active, but her local intelligence is running in fallback mode.\n\n"
            "The built-in local intelligence is active. You can configure a different model in Backend settings for enhanced capabilities.",
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
            "This outline was generated locally (no model backend connected). "
        )
        return RuntimeResult(RuntimeStatus.COMPLETED, "Hephaestus brief completed (local fallback)", thought + [f"[{ai_name}] Hephaestus Relay executed locally (local mode)."], [f"[{ai_name}] Produced structured brief outline."], ["Next: fill in unknowns and review. "], result)

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
            "This outline was generated locally (no model backend connected). "
        )
        return RuntimeResult(RuntimeStatus.COMPLETED, "Data analysis completed (local fallback)", thought + [f"[{ai_name}] Data Analyst Pro executed locally (local mode)."], [f"[{ai_name}] Produced analysis framework."], ["Next: provide data for analysis. "], result)

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
            "This outline was generated locally (no model backend connected). "
        )
        return RuntimeResult(RuntimeStatus.COMPLETED, "Code review completed (local fallback)", thought + [f"[{ai_name}] Code Reviewer executed locally (local mode)."], [f"[{ai_name}] Produced review checklist."], ["Next: provide code for review. "], result)

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
            "This outline was generated locally (no model backend connected). "
        )
        return RuntimeResult(RuntimeStatus.COMPLETED, "Meeting facilitation completed (local fallback)", thought + [f"[{ai_name}] Meeting Facilitator executed locally (local mode)."], [f"[{ai_name}] Produced meeting plan outline."], ["Next: fill in agenda details. "], result)

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
            "This outline was generated locally (no model backend connected). "
        )
        return RuntimeResult(RuntimeStatus.COMPLETED, "Security audit completed (local fallback)", thought + [f"[{ai_name}] Security Auditor executed locally (local mode)."], [f"[{ai_name}] Produced audit checklist."], ["Next: provide code/config for audit. "], result)

    def _run_financial_gainer(self, task, ai_name, meta, knowledge, thought):
        ai_uuid = str(meta.get("uuid", ""))
        t = task.lower()

        if ai_uuid:
            self._memory.add(ai_uuid, f"Financial analysis: {task}", tags=["financial", "analysis"], source="financial_gainer", importance=0.7)

        self._tier_audit.log_past(
            category=AuditCategory.LOCAL_RESPONSE,
            action="Financial gain analysis requested",
            detail=f"Query: {task[:100]}",
            source="user",
            capability="Financial Gainer",
            confidence="medium",
        )

        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "financial_gain"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Financial gain analysis completed", thought + [f"[{ai_name}] Model backend produced financial strategy using Knowledge context."], [f"[{ai_name}] Returned income/monetization strategy with risk assessment."], ["Next: review strategy. Verify claims before acting. Not financial advice."], model.text)

        parts = [f"Financial Gain Analysis for: {task}\n"]

        if any(x in t for x in ["freelance", "gig", "upwork", "fiverr", "side hustle", "contract work"]):
            parts.append(
                "Freelance / Gig Opportunity Analysis:\n"
                "1. Skill inventory: List your top 3 sellable skills.\n"
                "2. Platform fit: Upwork (professional), Fiverr (productized), LinkedIn (direct).\n"
                "3. Competitive pricing: Search similar profiles, find the median rate.\n"
                "4. Portfolio: Build 2-3 sample pieces before applying.\n"
                "5. First client strategy: Underprice slightly for first 3 reviews, then raise.\n"
                "6. Scale path: Productize your service into a package once demand exceeds capacity.\n\n"
                "Risk: Low financial risk, high time investment. Reputation is everything.\n"
                "Break-even: Immediate (first paid gig). Real income: 2-4 weeks to first payment.\n\n"
                "DISCLAIMER: Planning tool only â€” not financial advice."
            )
        elif any(x in t for x in ["crypto", "bitcoin", "ethereum", "token", "defi", "trading", "invest"]):
            parts.append(
                "Crypto / Investment Analysis:\n"
                "1. Risk tolerance: Only invest what you can afford to lose entirely.\n"
                "2. Asset research: Whitepaper, team, use case, tokenomics, liquidity.\n"
                "3. Entry strategy: Dollar-cost averaging vs lump sum â€” DCA reduces timing risk.\n"
                "4. Exit plan: Set target prices AND stop-loss levels before buying.\n"
                "5. Portfolio allocation: Never more than 5-10% of net worth in speculative assets.\n"
                "6. Red flags: Guaranteed returns, anonymous teams, no audit, FOMO marketing.\n\n"
                "Risk: EXTREME. Crypto markets are volatile and largely unregulated.\n"
                "Break-even: Unpredictable. May never recover. Treat as speculation, not investment.\n\n"
                "DISCLAIMER: NOT FINANCIAL ADVICE. Crypto can result in total loss of capital."
            )
        elif any(x in t for x in ["course", "teach", "education", "tutorial", "content creation", "youtube", "blog"]):
            parts.append(
                "Content / Course Creation Analysis:\n"
                "1. Niche selection: Intersection of your expertise + market demand + low competition.\n"
                "2. Validation: Search for existing courses. If none exist, ask why before celebrating.\n"
                "3. Pricing: $20-50 for intro, $100-300 for comprehensive, $500+ for specialized/pro.\n"
                "4. Platform: Teachable/Thinkific (own brand), Udemy (built-in traffic, lower margins).\n"
                "5. Production: Start with a mini-course (1-2 hours) to test demand before a big one.\n"
                "6. Marketing: Free content (YouTube/blog) feeds paid course sales. Build audience first.\n\n"
                "Risk: Low financial risk, high time investment upfront.\n"
                "Break-even: 10-50 sales typically covers production costs.\n\n"
                "DISCLAIMER: Planning tool only â€” not financial advice."
            )
        elif any(x in t for x in ["saas", "software", "app", "product", "startup"]):
            parts.append(
                "SaaS / Product Analysis:\n"
                "1. Problem validation: Talk to 10 potential users before writing code.\n"
                "2. MVP scope: Smallest version that solves the core problem. Ship in weeks, not months.\n"
                "3. Pricing model: Freemium (free tier + paid), or paid-only (higher quality leads).\n"
                "4. Revenue projection: users x price x retention rate. Be conservative.\n"
                "5. Customer acquisition cost (CAC): How much to get one paying user?\n"
                "6. Break-even: When monthly revenue exceeds monthly costs.\n\n"
                "Risk: Medium financial, high time. Most SaaS take 6-18 months to break-even.\n"
                "Key metric: MRR (Monthly Recurring Revenue). Track from day one.\n\n"
                "DISCLAIMER: Planning tool only â€” not financial advice."
            )
        elif any(x in t for x in ["cost", "save money", "cut spending", "budget", "optimize", "reduce expense"]):
            parts.append(
                "Cost Optimization Analysis:\n"
                "1. Expense audit: List all recurring costs (subscriptions, tools, services).\n"
                "2. Usage check: For each, ask: 'Did I use this in the last 30 days?'\n"
                "3. Alternatives: For each kept expense, is there a cheaper equivalent?\n"
                "4. Negotiation: Call providers (internet, insurance, phone) and ask for better rates.\n"
                "5. Consolidation: Merge overlapping tools (e.g., 3 design tools -> 1).\n"
                "6. Annual vs monthly: Annual plans often save 15-20% if you're committed.\n\n"
                "Risk: None. Pure savings exercise.\n"
                "Expected outcome: 10-30% reduction in monthly overhead.\n\n"
                "DISCLAIMER: Planning tool only â€” not financial advice."
            )
        elif any(x in t for x in ["price", "pricing", "how much should i charge", "rate", "what to charge"]):
            parts.append(
                "Pricing Strategy Analysis:\n"
                "1. Market research: Find 5-10 competitors and map their pricing tiers.\n"
                "2. Value-based vs cost-plus: Price based on value delivered, not time spent.\n"
                "3. Anchor pricing: Show 3 tiers (basic, recommended, premium). Most pick the middle.\n"
                "4. Psychological pricing: $97 feels cheaper than $100.\n"
                "5. Test and adjust: Start higher than you think, offer discounts, measure conversion.\n"
                "6. Raise prices: Once demand exceeds capacity, raise prices 20%.\n\n"
                "Rule of thumb: If nobody complains about your price, it's too low.\n\n"
                "DISCLAIMER: Planning tool only â€” not financial advice."
            )
        else:
            parts.append(
                "General Financial Gain Strategy:\n"
                "1. Opportunity: What income stream are you considering?\n"
                "2. Feasibility: Do you have the skills, capital, and time required?\n"
                "3. Revenue model: One-time, recurring, commission, or ad revenue?\n"
                "4. Break-even: How long until you recover your initial investment?\n"
                "5. Risk assessment: Market, competition, regulatory, platform dependency.\n"
                "6. Action plan: What is the smallest safe first step?\n\n"
                "Sustainable paths:\n"
                "- Freelance/gig work: Low risk, immediate income, scales with reputation.\n"
                "- Digital products/courses: Upfront effort, passive income over time.\n"
                "- SaaS/software: Higher effort, recurring revenue, scalable.\n"
                "- Cost optimization: Zero risk, immediate savings.\n"
                "- Pricing optimization: Increase revenue without more work.\n\n"
                "Avoid:\n"
                "- Get-rich-quick schemes, MLM, pyramid structures.\n"
                "- Anything requiring you to recruit others to make money.\n"
                "- 'Guaranteed returns' â€” nothing is guaranteed.\n\n"
                "DISCLAIMER: Planning tool only â€” not financial advice. "
            )

        result = "\n".join(parts)
        return RuntimeResult(RuntimeStatus.COMPLETED, "Financial gain analysis completed (local fallback)", thought + [f"[{ai_name}] Financial Gainer executed locally (local mode)."], [f"[{ai_name}] Produced opportunity-specific strategy with risk assessment."], ["Next: review analysis. "], result)

    def _run_memory_recorder(self, task, ai_name, meta, knowledge, thought):
        ai_uuid = str(meta.get("uuid", ""))
        t = task.lower()

        if ai_uuid:
            self._memory.add(ai_uuid, f"Recorded task: {task}", tags=["recorded", "session"], source="memory_recorder", importance=0.7)

        self._tier_audit.log_past(
            category=AuditCategory.LOCAL_RESPONSE,
            action="Memory recording triggered",
            detail=f"Query: {task[:100]}",
            source="user",
            capability="Memory Recorder",
            confidence="high",
        )

        # Intent: recall / search past context
        if any(x in t for x in ["recall", "search history", "search past", "where i left off", "restore context", "what did i", "last time", "previous session", "what were we doing"]):
            memories = []
            if ai_uuid:
                memories = self._memory.search(ai_uuid, task)[:10]
                if not memories:
                    memories = self._memory.get_recent(ai_uuid, 10)

            if memories:
                lines = [f"Recalled context for: {task}\n", f"Found {len(memories)} matching memory entries:\n"]
                for i, m in enumerate(memories, 1):
                    tags_str = f" [{', '.join(m.tags)}]" if hasattr(m, 'tags') and m.tags else ""
                    lines.append(f"  {i}. [{m.source}]{tags_str} {m.content}")
                lines.append("\nTo continue: pick a memory above and describe what you want to do next.")
                result_text = "\n".join(lines)
                return RuntimeResult(RuntimeStatus.COMPLETED, "Memory recall completed", thought + [f"[{ai_name}] Retrieved {len(memories)} memories matching the recall query."], [f"[{ai_name}] Returned recalled context from memory store."], ["Next: continue from where you left off, or refine the search."], result_text)
            else:
                return RuntimeResult(RuntimeStatus.COMPLETED, "No memories found", thought + [f"[{ai_name}] No stored memories matched the recall query."], [f"[{ai_name}] Memory store is empty or no matches found."], ["Next: start a new task â€” memories will accumulate as you work."], f"No memories found for: {task}\n\nMemories are recorded automatically as you work.\nTry: 'recall [topic]' or 'what did I do last time' to search past sessions.")

        # Intent: decision tracking
        if any(x in t for x in ["track decision", "decision history", "why did i choose", "what did i decide", "log decision"]):
            if ai_uuid:
                decision_memories = [m for m in self._memory.get_recent(ai_uuid, 20) if "decision" in (m.tags if hasattr(m, 'tags') else [])]
                if decision_memories:
                    lines = [f"Decision history ({len(decision_memories)} entries):\n"]
                    for i, m in enumerate(decision_memories, 1):
                        lines.append(f"  {i}. {m.content}")
                    result_text = "\n".join(lines)
                    return RuntimeResult(RuntimeStatus.COMPLETED, "Decision history retrieved", thought + [f"[{ai_name}] Found {len(decision_memories)} tracked decisions."], [f"[{ai_name}] Returned decision history."], ["Next: review decisions and continue or revise."], result_text)

            return RuntimeResult(RuntimeStatus.COMPLETED, "No decisions tracked yet", thought + [f"[{ai_name}] No decision memories found."], [f"[{ai_name}] Decision tracking is empty."], ["Next: use 'track decision: [your choice]' to start logging decisions."], "No decisions have been tracked yet.\n\nTo track a decision, say: 'track decision: I chose X because Y'\nThis records it for future review and recall.")

        # Intent: habit / progress tracking
        if any(x in t for x in ["habit", "progress", "journal", "streak", "daily log"]):
            if ai_uuid:
                habit_memories = [m for m in self._memory.get_recent(ai_uuid, 30) if "habit" in (m.tags if hasattr(m, 'tags') else []) or "progress" in (m.tags if hasattr(m, 'tags') else [])]
                if habit_memories:
                    lines = [f"Progress journal ({len(habit_memories)} entries):\n"]
                    for i, m in enumerate(habit_memories, 1):
                        lines.append(f"  {i}. {m.content}")
                    result_text = "\n".join(lines)
                    return RuntimeResult(RuntimeStatus.COMPLETED, "Progress journal retrieved", thought + [f"[{ai_name}] Found {len(habit_memories)} progress entries."], [f"[{ai_name}] Returned progress journal."], ["Next: continue your streak or review patterns."], result_text)

            if ai_uuid:
                self._memory.add(ai_uuid, f"Progress entry: {task}", tags=["habit", "progress", "journal"], source="memory_recorder", importance=0.6)
            return RuntimeResult(RuntimeStatus.COMPLETED, "Progress entry recorded", thought + [f"[{ai_name}] Recorded new progress/habit entry to memory."], [f"[{ai_name}] Saved progress journal entry."], ["Next: check progress with 'show my progress' or 'habit tracker'."], f"Progress entry recorded: {task}\n\nThis has been saved to your journal. Use 'show my progress' to review past entries.")

        # Intent: audit trail
        if any(x in t for x in ["audit trail", "compliance trail", "audit report", "activity log", "what happened"]):
            if ai_uuid:
                all_recent = self._memory.get_recent(ai_uuid, 30)
                if all_recent:
                    lines = [f"Audit trail ({len(all_recent)} recent entries):\n"]
                    for i, m in enumerate(all_recent, 1):
                        tags_str = f" [{', '.join(m.tags)}]" if hasattr(m, 'tags') and m.tags else ""
                        lines.append(f"  {i}. [{m.source}]{tags_str} {m.content}")
                    result_text = "\n".join(lines)
                    return RuntimeResult(RuntimeStatus.COMPLETED, "Audit trail retrieved", thought + [f"[{ai_name}] Compiled audit trail with {len(all_recent)} entries."], [f"[{ai_name}] Returned full recent activity log."], ["Next: review trail for compliance or context restoration."], result_text)

            return RuntimeResult(RuntimeStatus.COMPLETED, "No audit trail yet", thought + [f"[{ai_name}] No activity recorded for audit."], [f"[{ai_name}] Audit trail is empty."], ["Next: start working â€” activity is logged automatically."], "No audit trail entries yet.\n\nActivity is recorded automatically as you work. Come back later to review the full trail.")

        # Default: try model backend, then local recording scaffold
        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "memory_recording"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Memory recording completed", thought + [f"[{ai_name}] Model backend produced recording/replay analysis using Knowledge context."], [f"[{ai_name}] Returned session recording or knowledge archive output."], ["Next: review recorded context. Use recall to retrieve later."], model.text)

        result = (
            f"Memory Recording for: {task}\n\n"
            "This task has been recorded to local memory.\n\n"
            f"Recording details:\n"
            f"  - Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            "  - Source: memory_recorder\n"
            "  - Tags: [recorded, session]\n\n"
            "What was captured:\n"
            "  1. Session context: The task you just described.\n"
            "  2. This will be searchable later via recall.\n\n"
            "Commands you can use:\n"
            "  - 'recall [topic]' â€” search past sessions\n"
            "  - 'where I left off' â€” restore previous context\n"
            "  - 'track decision: [choice]' â€” log a decision\n"
            "  - 'show my progress' â€” view habit/progress journal\n"
            "  - 'audit trail' â€” full recent activity log\n\n"
            ""
        )
        return RuntimeResult(RuntimeStatus.COMPLETED, "Memory recording completed (local fallback)", thought + [f"[{ai_name}] Memory Recorder executed locally â€” task saved to memory store."], [f"[{ai_name}] Recorded task to local memory with timestamp and tags."], ["Next: use 'recall [topic]' to retrieve past context. "], result)

    def _run_activity_watcher(self, task, ai_name, meta, knowledge, thought):
        ai_uuid = str(meta.get("uuid", ""))
        t = task.lower()

        if ai_uuid:
            self._memory.add(ai_uuid, f"Activity observed: {task}", tags=["activity", "pattern"], source="activity_watcher", importance=0.5)

        self._tier_audit.log_past(
            category=AuditCategory.LOCAL_RESPONSE,
            action="Activity watching triggered",
            detail=f"Query: {task[:100]}",
            source="user",
            capability="Activity Watcher",
            confidence="medium",
        )

        # Intent: show patterns / suggestions
        if any(x in t for x in ["show pattern", "what patterns", "my habits", "work pattern", "suggest improvement", "work faster", "how can i improve", "bottleneck"]):
            if ai_uuid:
                activity_memories = [m for m in self._memory.get_recent(ai_uuid, 30) if "activity" in (m.tags if hasattr(m, 'tags') else [])]
                if activity_memories:
                    lines = [f"Activity Pattern Report ({len(activity_memories)} recent activities):\n"]

                    sources = {}
                    for m in activity_memories:
                        src = m.source
                        if src not in sources:
                            sources[src] = []
                        sources[src].append(m.content)

                    lines.append("Activity breakdown by source:")
                    for src, items in sources.items():
                        lines.append(f"\n  [{src}] ({len(items)} activities)")
                        for item in items[:5]:
                            lines.append(f"    - {item[:100]}")
                        if len(items) > 5:
                            lines.append(f"    ... and {len(items) - 5} more")

                    lines.append(f"\n\nPattern observations:")
                    lines.append(f"  - Total tracked activities: {len(activity_memories)}")
                    lines.append(f"  - Most active source: {max(sources, key=lambda s: len(sources[s]))}")
                    lines.append(f"  - Activity sources: {len(sources)}")

                    lines.append(f"\n\nImprovement suggestions:")
                    lines.append("  1. Look for repeated task types â€” these are automation candidates.")
                    lines.append("  2. Tasks that take < 5 min but happen daily are prime for automation.")
                    lines.append("  3. Tasks you avoid or procrastinate may indicate friction â€” simplify them.")
                    lines.append("  4. Batch similar tasks together to reduce context switching.")

                    result_text = "\n".join(lines)
                    return RuntimeResult(RuntimeStatus.COMPLETED, "Activity pattern report generated", thought + [f"[{ai_name}] Analyzed {len(activity_memories)} activity entries and produced pattern report."], [f"[{ai_name}] Returned activity breakdown and improvement suggestions."], ["Next: review suggestions. Repeated tasks will build richer patterns over time."], result_text)

            return RuntimeResult(RuntimeStatus.COMPLETED, "No activity patterns yet", thought + [f"[{ai_name}] No activity data collected yet."], [f"[{ai_name}] Activity log is empty."], ["Next: keep working â€” activity is logged automatically. Check patterns later."], "No activity patterns collected yet.\n\nActivity is logged automatically as you work. Use 'show my patterns' after a few sessions to see insights.")

        # Intent: automation candidates
        if any(x in t for x in ["automate", "automation candidate", "what can i automate", "delegate"]):
            if ai_uuid:
                activity_memories = [m for m in self._memory.get_recent(ai_uuid, 30) if "activity" in (m.tags if hasattr(m, 'tags') else [])]
                if activity_memories:
                    lines = [f"Automation Candidate Analysis ({len(activity_memories)} activities analyzed):\n"]
                    lines.append("Tasks that appear repeated and are good automation candidates:\n")

                    all_text = " ".join(m.content.lower() for m in activity_memories)
                    common_words = ["file", "write", "read", "search", "send", "email", "report", "data", "format", "convert", "copy", "move", "rename", "check", "monitor", "update"]
                    found_candidates = []
                    for word in common_words:
                        count = all_text.count(word)
                        if count >= 2:
                            found_candidates.append((word, count))

                    found_candidates.sort(key=lambda x: x[1], reverse=True)
                    if found_candidates:
                        for word, count in found_candidates[:8]:
                            lines.append(f"  - '{word}' appears in {count} activities â€” consider automating.")
                    else:
                        lines.append("  No strong repetition patterns detected yet.")
                        lines.append("  Keep working â€” patterns emerge after 10+ activities.")

                    lines.append(f"\n\nAutomation framework:")
                    lines.append("  1. Identify: Tasks you do the same way every time.")
                    lines.append("  2. Evaluate: Time saved per automation vs. time to build it.")
                    lines.append("  3. Prioritize: Automate the most frequent task first.")
                    lines.append("  4. Implement: Use Command Nexus Tool User or Workflow Automation.")
                    lines.append("  5. Verify: Test the automation before relying on it.")

                    result_text = "\n".join(lines)
                    return RuntimeResult(RuntimeStatus.COMPLETED, "Automation analysis completed", thought + [f"[{ai_name}] Analyzed {len(activity_memories)} activities for automation candidates."], [f"[{ai_name}] Returned automation candidate list and framework."], ["Next: pick a candidate and set up automation. "], result_text)

            return RuntimeResult(RuntimeStatus.COMPLETED, "Not enough data for automation analysis", thought + [f"[{ai_name}] Insufficient activity data for automation analysis."], [f"[{ai_name}] Need more activity history."], ["Next: keep working â€” automation patterns emerge after 10+ logged activities."], "Not enough activity data yet to identify automation candidates.\n\nKeep working normally. After 10+ activities, use 'what can I automate' to find repetition patterns.")

        # Default: try model backend, then local observation scaffold
        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "activity_watching"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Activity analysis completed", thought + [f"[{ai_name}] Model backend produced activity pattern analysis using Knowledge context."], [f"[{ai_name}] Returned workflow observations and improvement suggestions."], ["Next: review suggestions and decide which to adopt."], model.text)

        result = (
            f"Activity Watching for: {task}\n\n"
            "This activity has been logged and will be included in future pattern analysis.\n\n"
            "Observation framework:\n"
            "  1. Current pattern: What you're doing repeatedly.\n"
            "  2. Time analysis: Where most time is spent vs. value produced.\n"
            "  3. Bottleneck detection: Steps that slow down the workflow.\n"
            "  4. Automation candidates: Tasks that could be delegated or automated.\n"
            "  5. Improvement suggestions: Specific ways to work faster.\n\n"
            "Commands you can use:\n"
            "  - 'show my patterns' â€” see activity breakdown and suggestions\n"
            "  - 'what can I automate' â€” find repetition patterns to automate\n"
            "  - 'how can I improve' â€” get workflow improvement tips\n\n"
            "Over time, patterns will emerge that can be optimized.\n\n"
            ""
        )
        return RuntimeResult(RuntimeStatus.COMPLETED, "Activity analysis completed (local fallback)", thought + [f"[{ai_name}] Activity Watcher executed locally â€” activity logged to memory."], [f"[{ai_name}] Produced observation framework and logged activity pattern."], ["Next: use 'show my patterns' after several sessions. "], result)

    def _run_game_companion(self, task, ai_name, meta, knowledge, thought):
        ai_uuid = str(meta.get("uuid", ""))
        t = task.lower()

        self._tier_audit.log_past(
            category=AuditCategory.LOCAL_RESPONSE,
            action="Game companion consulted",
            detail=f"Query: {task[:100]}",
            source="user",
            capability="Game Companion",
            confidence="medium",
        )

        if ai_uuid:
            self._memory.add(ai_uuid, f"Game query: {task}", tags=["game", "strategy"], source="game_companion", importance=0.4)

        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "game_companion"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Game companion analysis completed", thought + [f"[{ai_name}] Model backend produced game strategy/guidance using Knowledge context."], [f"[{ai_name}] Returned game strategy, rules explanation, or companion advice."], ["Next: apply strategy in-game. Ask for clarification on specific mechanics."], model.text)

        result_parts = [f"Game Companion for: {task}\n"]

        if "chess" in t:
            if any(x in t for x in ["opening", "start", "begin"]):
                result_parts.append(
                    "Chess Opening Principles:\n"
                    "1. Control the center (e4, d4, e5, d5) with pawns and pieces.\n"
                    "2. Develop knights before bishops (Nf3, Nc3/Nf6, Nc6).\n"
                    "3. Castle by move 10 for king safety.\n"
                    "4. Don't move the same piece twice in the opening.\n"
                    "5. Don't bring the queen out too early.\n"
                    "6. Connect your rooks (clear the back rank).\n\n"
                    "Common openings:\n"
                    "  - White: e4 (King's Pawn) or d4 (Queen's Pawn)\n"
                    "  - Black: e5 or c5 (Sicilian) against e4; Nf6 or d5 against d4\n\n"
                    ""
                )
            elif any(x in t for x in ["endgame", "ending", "late game", "king and pawn"]):
                result_parts.append(
                    "Chess Endgame Principles:\n"
                    "1. Activate your king â€” it becomes a fighting piece in the endgame.\n"
                    "2. Push passed pawns toward promotion.\n"
                    "3. The opposition: Kings facing each other with one square between â€” the side NOT to move has the advantage.\n"
                    "4. Rook endgames: Keep rooks active (7th rank is powerful).\n"
                    "5. K+P vs K: Lead with your king, use opposition to escort the pawn.\n"
                    "6. Lucena position (winning) and Philidor position (drawing) are essential.\n\n"
                    ""
                )
            elif any(x in t for x in ["tactic", "fork", "pin", "skewer", "discovered", "combination"]):
                result_parts.append(
                    "Chess Tactics Guide:\n"
                    "1. Fork: One piece attacks two or more targets (knights are devastating at this).\n"
                    "2. Pin: A piece is stuck because moving it would expose a more valuable piece.\n"
                    "3. Skewer: A valuable piece is attacked and must move, exposing a less valuable piece.\n"
                    "4. Discovered attack: Moving one piece reveals an attack from another.\n"
                    "5. Zwischenzug (in-between move): Instead of recapturing, play a forcing move first.\n"
                    "6. Back rank mate: Common trap â€” king trapped by its own pawns.\n\n"
                    "Tactical training: Solve puzzles daily. Pattern recognition is everything.\n"
                    ""
                )
            else:
                result_parts.append(
                    "Chess General Strategy:\n"
                    "Opening: Control center, develop pieces, castle early.\n"
                    "Middlegame: Look for tactics, improve piece placement, create weaknesses.\n"
                    "Endgame: Activate king, push passed pawns, use opposition.\n\n"
                    "Key principles:\n"
                    "  - Every move should have a purpose.\n"
                    "  - Evaluate: material, king safety, piece activity, pawn structure.\n"
                    "  - When ahead in material, trade pieces (not pawns).\n"
                    "  - When behind, avoid trades and create complications.\n"
                    "  - Always check what your opponent's last move threatens.\n\n"
                    ""
                )
        elif any(x in t for x in ["poker", "texas hold", "bluff", "betting strategy"]):
            result_parts.append(
                "Poker Strategy Guide:\n"
                "1. Starting hands: Play tight early position, looser in late position.\n"
                "   - Premium: AA, KK, QQ, AK suited. Play aggressively.\n"
                "   - Speculative: Small pairs, suited connectors. Play cheaply.\n"
                "   - Trash: 72o, 83o. Fold unless free to see flop.\n"
                "2. Position is power: Later position = more information = better decisions.\n"
                "3. Pot odds: Call if (call amount / total pot) < (odds of winning).\n"
                "4. Bluffing: Bluff with a story (board texture supports it).\n"
                "5. Bankroll management: Never risk more than 5% of bankroll on one session.\n"
                "6. Tilt is your enemy: Emotional play loses money. Take breaks.\n\n"
                ""
            )
        elif any(x in t for x in ["card game", "hearts", "spades", "bridge", "rummy", "uno"]):
            result_parts.append(
                "Card Game Strategy:\n"
                "1. Count cards: Track what's been played to predict what's left.\n"
                "2. Manage your hand: Don't dump high cards too early or too late.\n"
                "3. Read opponents: Watch what they play and what they avoid.\n"
                "4. Trump management: Save trumps for when they matter most.\n"
                "5. Endgame: In trick-taking games, the last few tricks decide everything.\n\n"
                "For specific games, tell me which card game for detailed strategy.\n"
                ""
            )
        elif any(x in t for x in ["board game", "catan", "ticket", "monopoly", "risk", "pandemic", "azul"]):
            result_parts.append(
                "Board Game Strategy:\n"
                "1. Understand victory conditions: Racing, building, conquering, or surviving?\n"
                "2. Resource efficiency: Every turn, maximize value per action.\n"
                "3. Tempo: Don't fall behind. Early momentum compounds.\n"
                "4. Player interaction: Watch what opponents are building toward.\n"
                "5. Adaptability: Don't over-commit to one strategy if the board changes.\n"
                "6. Endgame scoring: Know how final points are calculated and plan backward.\n\n"
                "For specific games (Catan, Ticket to Ride, etc.), tell me which one.\n"
                ""
            )
        elif any(x in t for x in ["puzzle", "riddle", "brain teaser", "sudoku", "logic puzzle"]):
            result_parts.append(
                "Puzzle-Solving Framework:\n"
                "1. Identify the constraint: What limits the solution space?\n"
                "2. Break it into parts: Can sub-problems be solved independently?\n"
                "3. Work backwards: Start from the goal and reverse-engineer the steps.\n"
                "4. Look for patterns: Symmetries, repetitions, sequences.\n"
                "5. Test edge cases: What happens at the boundaries?\n"
                "6. Eliminate impossibilities: Rule out what CAN'T work first.\n"
                "7. Lateral thinking: Sometimes the answer reframes the question.\n\n"
                "For Sudoku specifically:\n"
                "  - Start with the most constrained cells (fewest possibilities).\n"
                "  - Use cross-hatching: scan rows, columns, and boxes together.\n"
                "  - Look for naked pairs/triples to eliminate candidates.\n\n"
                ""
            )
        elif any(x in t for x in ["video game", "gaming", "fps", "moba", "rpg", "strategy game", "build guide", "meta"]):
            result_parts.append(
                "Video Game Strategy:\n"
                "1. Game sense: Map awareness, timing, objective control.\n"
                "2. Mechanics: Practice core skills (aim, movement, combos) deliberately.\n"
                "3. Meta knowledge: Know what's strong right now and why.\n"
                "4. Economy: In games with resources, efficient spending wins games.\n"
                "5. Positioning: Where you stand matters more than what you do.\n"
                "6. Review replays: Your biggest improvements come from analyzing losses.\n"
                "7. Tilt management: Take breaks after 2 losses in a row.\n\n"
                "For specific games (League, Valorant, WoW, etc.), tell me which one.\n"
                ""
            )
        elif any(x in t for x in ["rules", "how to play", "learn", "teach me"]):
            result_parts.append(
                "Game Rules Learning Framework:\n"
                "1. Objective: What is the win condition?\n"
                "2. Setup: How does the game start? What does each player get?\n"
                "3. Turn structure: What can you do on your turn?\n"
                "4. Key mechanics: What makes this game unique?\n"
                "5. Scoring: How is the winner determined?\n"
                "6. Common mistakes: What do new players usually get wrong?\n\n"
                "Tell me the specific game and I'll break down the rules.\n"
                ""
            )
        else:
            result_parts.append(
                "Game Companion Framework:\n"
                "1. Game type: Identify the genre (strategy, card, board, video, puzzle).\n"
                "2. Rules: Confirm the rules and win conditions.\n"
                "3. Strategy: Optimal play patterns for the current situation.\n"
                "4. Mechanics: How specific game systems interact.\n"
                "5. Practice: Suggest drills or scenarios to improve.\n\n"
                "I can help with:\n"
                "  - Chess (openings, tactics, endgames)\n"
                "  - Poker (starting hands, pot odds, bluffing)\n"
                "  - Card games (Hearts, Spades, Bridge, Rummy)\n"
                "  - Board games (Catan, Ticket to Ride, Risk, etc.)\n"
                "  - Puzzles (Sudoku, logic puzzles, riddles)\n"
                "  - Video games (FPS, MOBA, RPG, strategy)\n"
                "  - Learning rules for any new game\n\n"
                "Tell me which game and what you need help with.\n"
                ""
            )

        result = "\n".join(result_parts)
        return RuntimeResult(RuntimeStatus.COMPLETED, "Game companion completed (local fallback)", thought + [f"[{ai_name}] Game Companion executed locally (local mode)."], [f"[{ai_name}] Produced game-specific guidance scaffold."], ["Next: apply guidance in-game. "], result)

    def _run_email_automation(self, task, ai_name, meta, knowledge, thought):
        ai_uuid = str(meta.get("uuid", ""))
        t = task.lower()

        if ai_uuid:
            self._memory.add(ai_uuid, f"Email task: {task}", tags=["email", "automation"], source="email_automation", importance=0.5)

        self._tier_audit.log_past(
            category=AuditCategory.LOCAL_RESPONSE,
            action="Email automation triggered",
            detail=f"Query: {task[:100]}",
            source="user",
            capability="Email Automation",
            confidence="medium",
        )

        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "email_automation"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Email automation completed", thought + [f"[{ai_name}] Model backend produced email output using Knowledge context."], [f"[{ai_name}] Returned email draft/organizational output."], ["Next: review before sending. Never auto-send without approval."], model.text)

        parts = [f"Email Automation for: {task}\n"]

        if any(x in t for x in ["connect", "setup", "set up", "configure", "get it working", "my email", "my emails", "link email", "add email", "sync email", "email account", "email provider", "gmail", "outlook", "yahoo", "smtp", "imap", "oauth"]):
            parts.append(
                "Email Connection Setup Guide:\n"
                "To connect your email account to Command Nexus, you need to configure IMAP (for reading) and SMTP (for sending).\n\n"
                "=== GMAIL ===\n"
                "1. Enable 2-Factor Authentication on your Google account.\n"
                "2. Go to myaccount.google.com â†’ Security â†’ App passwords.\n"
                "3. Generate an app password for 'Mail'.\n"
                "4. IMAP settings:\n"
                "   - Server: imap.gmail.com\n"
                "   - Port: 993\n"
                "   - SSL: Yes\n"
                "   - Username: your@gmail.com\n"
                "   - Password: [app password from step 3]\n"
                "5. SMTP settings:\n"
                "   - Server: smtp.gmail.com\n"
                "   - Port: 587\n"
                "   - TLS: Yes\n"
                "   - Username: your@gmail.com\n"
                "   - Password: [same app password]\n\n"
                "=== OUTLOOK / OFFICE 365 ===\n"
                "1. IMAP settings:\n"
                "   - Server: outlook.office365.com\n"
                "   - Port: 993\n"
                "   - SSL: Yes\n"
                "   - Username: your@outlook.com\n"
                "   - Password: your account password\n"
                "2. SMTP settings:\n"
                "   - Server: smtp.office365.com\n"
                "   - Port: 587\n"
                "   - TLS: Yes\n"
                "   - Username: your@outlook.com\n"
                "   - Password: your account password\n\n"
                "=== YAHOO ===\n"
                "1. Generate an app password at yahoo.com â†’ Account Security.\n"
                "2. IMAP: imap.mail.yahoo.com, port 993, SSL\n"
                "3. SMTP: smtp.mail.yahoo.com, port 587, TLS\n\n"
                "=== SECURITY BEST PRACTICES ===\n"
                "- NEVER hardcode passwords in source code\n"
                "- Store credentials in environment variables or a encrypted config\n"
                "- Use app passwords instead of your main password\n"
                "- Enable 2FA on your email account\n"
                "- Command Nexus processes email locally â€” no credentials are sent to external servers\n\n"
                "Once you have your IMAP/SMTP settings, you can:\n"
                "  - Draft emails using the Templates tab\n"
                "  - Plan sequences using the Sequences tab\n"
                "  - Schedule sends using the Schedule tab\n"
                "  - Ask me to 'draft email to [recipient] about [topic]' for AI-assisted drafting\n\n"
                "DISCLAIMER: Email credentials are sensitive. Command Nexus never auto-sends without your approval.\n"
                ""
            )
        elif any(x in t for x in ["draft", "compose", "write email", "template"]):
            parts.append(
                "Email draft outline:\n"
                "1. Subject line: Clear, concise, action-oriented (5-7 words).\n"
                "2. Greeting: Match the relationship (formal, professional, casual).\n"
                "3. Opening: State purpose in the first 1-2 sentences.\n"
                "4. Body: One idea per paragraph. Keep paragraphs short (2-3 sentences).\n"
                "5. Call to action: What do you want the recipient to do?\n"
                "6. Closing: Professional sign-off with contact info.\n\n"
                "Email types:\n"
                "  - Cold outreach: Personalize, show value, low-friction CTA.\n"
                "  - Follow-up: Reference previous contact, gentle reminder.\n"
                "  - Newsletter: Value-first, scannable, consistent format.\n"
                "  - Transactional: Clear subject, key info first, next steps.\n\n"
                "DISCLAIMER: Drafts are advisory. Review content and tone before sending.\n"
                ""
            )
        elif any(x in t for x in ["organize", "inbox", "filter", "sort", "manage email"]):
            parts.append(
                "Email Organization Framework:\n"
                "1. Triage: Sort by urgency (respond today / this week / FYI).\n"
                "2. Folders/labels: Create a simple hierarchy (Action, Waiting, Reference, Archive).\n"
                "3. Filters: Auto-route newsletters, notifications, and internal mail.\n"
                "4. Batch processing: Check email 2-3 times/day, not continuously.\n"
                "5. Template library: Create templates for common responses.\n"
                "6. Unsubscribe: Remove newsletters you haven't opened in 30 days.\n\n"
                ""
            )
        elif any(x in t for x in ["campaign", "sequence", "mail merge", "newsletter"]):
            parts.append(
                "Email Campaign Framework:\n"
                "1. Audience: Define segment (leads, customers, subscribers).\n"
                "2. Goal: What action should recipients take?\n"
                "3. Sequence: 3-5 emails spaced 2-5 days apart.\n"
                "4. Subject lines: A/B test 2-3 variants. Aim for 30%+ open rate.\n"
                "5. Content: Value-first, not sales-first. 80% value, 20% offer.\n"
                "6. Metrics: Track open rate, click rate, reply rate, unsubscribe rate.\n"
                "7. Compliance: Include unsubscribe link. Follow CAN-SPAM/GDPR.\n\n"
                "DISCLAIMER: Campaign suggestions are advisory. Verify compliance before sending.\n"
                ""
            )
        else:
            parts.append(
                "Email Automation Framework:\n"
                "  - Draft emails (cold outreach, follow-ups, newsletters, transactional)\n"
                "  - Organize inbox (triage, filter, batch process)\n"
                "  - Create templates for common responses\n"
                "  - Plan email campaigns and sequences\n"
                "  - Auto-reply rules (without sending â€” drafts only)\n\n"
                "Commands:\n"
                "  - 'draft email to [recipient] about [topic]'\n"
                "  - 'organize my inbox'\n"
                "  - 'create email template for [use case]'\n"
                "  - 'plan email campaign for [product]'\n\n"
                "DISCLAIMER: Email drafts are advisory. Never auto-send without review.\n"
                ""
            )

        result = "\n".join(parts)
        return RuntimeResult(RuntimeStatus.COMPLETED, "Email automation completed (local mode)", thought + [f"[{ai_name}] Email Automation executed in local mode."], [f"[{ai_name}] Produced email scaffold with setup/draft/organize/campaign framework."], ["Next: review output. "], result)

    def _run_api_integrator(self, task, ai_name, meta, knowledge, thought):
        ai_uuid = str(meta.get("uuid", ""))
        t = task.lower()

        if ai_uuid:
            self._memory.add(ai_uuid, f"API integration task: {task}", tags=["api", "integration"], source="api_integrator", importance=0.7)

        self._tier_audit.log_past(
            category=AuditCategory.LOCAL_RESPONSE,
            action="API integration triggered",
            detail=f"Query: {task[:100]}",
            source="user",
            capability="API Integrator",
            confidence="medium",
        )

        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "api_integration"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "API integration completed", thought + [f"[{ai_name}] Model backend produced API integration output using Knowledge context."], [f"[{ai_name}] Returned integration plan/config."], ["Next: review and test before deploying. Never expose API keys."], model.text)

        parts = [f"API Integration for: {task}\n"]

        if any(x in t for x in ["connect", "configure", "set up", "setup"]):
            parts.append(
                "API Connection Framework:\n"
                "1. Identify the API: What service? What version?\n"
                "2. Authentication: API key, OAuth2, or bearer token?\n"
                "3. Base URL: Confirm the endpoint base URL.\n"
                "4. Rate limits: Check documentation for calls/minute, calls/day.\n"
                "5. Error handling: What HTTP status codes to expect and handle.\n"
                "6. Retry logic: Exponential backoff for 429/5xx responses.\n"
                "7. Security: NEVER hardcode API keys. Use environment variables.\n\n"
                "Safety checklist:\n"
                "  - [ ] API key stored in environment variable, not in code\n"
                "  - [ ] HTTPS only â€” never send credentials over HTTP\n"
                "  - [ ] Rate limit handling implemented\n"
                "  - [ ] Error responses logged, not silently ignored\n"
                "  - [ ] Input validation before sending to API\n\n"
                "DISCLAIMER: API integration carries security risk. Test in a sandbox first.\n"
                ""
            )
        elif any(x in t for x in ["webhook", "callback", "event"]):
            parts.append(
                "Webhook Integration Framework:\n"
                "1. Endpoint: Create a receiving endpoint URL.\n"
                "2. Authentication: Verify webhook signatures (HMAC, shared secret).\n"
                "3. Event types: Map which events trigger which actions.\n"
                "4. Idempotency: Handle duplicate deliveries gracefully.\n"
                "5. Retry: Return 200 quickly; process asynchronously.\n"
                "6. Logging: Record all webhook payloads for debugging.\n\n"
                ""
            )
        elif any(x in t for x in ["test", "debug", "troubleshoot"]):
            parts.append(
                "API Debugging Framework:\n"
                "1. Verify credentials: Is the API key valid and not expired?\n"
                "2. Check endpoint: Is the URL correct? Method (GET/POST/PUT/DELETE)?\n"
                "3. Headers: Content-Type, Authorization, Accept headers correct?\n"
                "4. Payload: Is the request body valid JSON/XML per the spec?\n"
                "5. Response: What HTTP status code? What error message?\n"
                "6. Rate limits: Are you being throttled? Check 429 responses.\n"
                "7. Network: Can you reach the API from your environment?\n\n"
                ""
            )
        else:
            parts.append(
                "API Integrator Framework:\n"
                "  - Connect and configure external APIs\n"
                "  - Set up webhooks and event handlers\n"
                "  - Test and debug API integrations\n"
                "  - Manage API keys securely (env vars, never hardcoded)\n"
                "  - Handle rate limits, retries, and error responses\n"
                "  - Map data between API responses and internal formats\n\n"
                "Commands:\n"
                "  - 'connect to [service] API'\n"
                "  - 'set up webhook for [event]'\n"
                "  - 'debug API error [description]'\n"
                "  - 'configure API authentication'\n\n"
                "DISCLAIMER: API integration carries security risk. Never expose API keys.\n"
                ""
            )

        result = "\n".join(parts)
        return RuntimeResult(RuntimeStatus.COMPLETED, "API integration completed (local fallback)", thought + [f"[{ai_name}] API Integrator executed locally (local mode)."], [f"[{ai_name}] Produced integration framework with security checklist."], ["Next: review plan. Test in sandbox. "], result)

    def _run_team_orchestrator(self, task, ai_name, meta, knowledge, thought):
        ai_uuid = str(meta.get("uuid", ""))
        t = task.lower()

        if ai_uuid:
            self._memory.add(ai_uuid, f"Team orchestration task: {task}", tags=["team", "orchestration"], source="team_orchestrator", importance=0.6)

        self._tier_audit.log_past(
            category=AuditCategory.LOCAL_RESPONSE,
            action="Team orchestration triggered",
            detail=f"Query: {task[:100]}",
            source="user",
            capability="Team Orchestrator",
            confidence="medium",
        )

        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "team_orchestration"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Team orchestration completed", thought + [f"[{ai_name}] Model backend produced team orchestration plan using Knowledge context."], [f"[{ai_name}] Returned multi-AI coordination plan."], ["Next: review plan and assign tasks to specific AIs."], model.text)

        parts = [f"Team Orchestration for: {task}\n"]

        if any(x in t for x in ["assign", "delegate", "divide", "split task"]):
            parts.append(
                "Task Assignment Framework:\n"
                "1. Break down the task into independent sub-tasks.\n"
                "2. Match each sub-task to the AI with the right capability:\n"
                "   - Research tasks â†’ Research-capable AI\n"
                "   - Code tasks â†’ Coder-capable AI\n"
                "   - Writing tasks â†’ Creative Writer AI\n"
                "   - Analysis tasks â†’ Data Analyst AI\n"
                "   - Planning tasks â†’ Planner AI\n"
                "3. Define handoff points: What output does each AI pass to the next?\n"
                "4. Set execution order: Sequential (dependencies) or parallel (independent).\n"
                "5. Merge results: How do the outputs combine into a final deliverable?\n\n"
                ""
            )
        elif any(x in t for x in ["coordinate", "workflow", "pipeline", "handoff"]):
            parts.append(
                "Multi-AI Coordination Framework:\n"
                "1. Pipeline design: Define the flow of work between AIs.\n"
                "2. Handoff format: Standardize how outputs are passed (JSON, text, structured).\n"
                "3. Checkpoints: Where does a human review intermediate results?\n"
                "4. Error handling: What happens if one AI's output is insufficient?\n"
                "5. Parallel vs sequential: Which tasks can run simultaneously?\n"
                "6. Aggregation: How are multiple AI outputs combined?\n\n"
                "Example pipeline:\n"
                "  Research AI â†’ findings â†’ Writer AI â†’ draft â†’ Editor AI â†’ final\n\n"
                ""
            )
        else:
            parts.append(
                "Team Orchestrator Framework:\n"
                "  - Decompose complex tasks into sub-tasks\n"
                "  - Assign sub-tasks to AIs with matching capabilities\n"
                "  - Design multi-AI workflows and pipelines\n"
                "  - Manage handoffs and checkpoints\n"
                "  - Aggregate results from multiple AIs\n\n"
                "Commands:\n"
                "  - 'assign tasks for [project description]'\n"
                "  - 'coordinate workflow for [process]'\n"
                "  - 'divide [task] among AIs'\n\n"
                ""
            )

        result = "\n".join(parts)
        return RuntimeResult(RuntimeStatus.COMPLETED, "Team orchestration completed (local fallback)", thought + [f"[{ai_name}] Team Orchestrator executed locally (local mode)."], [f"[{ai_name}] Produced multi-AI coordination framework."], ["Next: review plan and assign to specific AIs. "], result)

    def _run_voice_interface(self, task, ai_name, meta, knowledge, thought):
        ai_uuid = str(meta.get("uuid", ""))
        t = task.lower()

        if ai_uuid:
            self._memory.add(ai_uuid, f"Voice interface task: {task}", tags=["voice", "speech"], source="voice_interface", importance=0.5)

        self._tier_audit.log_past(
            category=AuditCategory.LOCAL_RESPONSE,
            action="Voice interface triggered",
            detail=f"Query: {task[:100]}",
            source="user",
            capability="Voice Interface",
            confidence="medium",
        )

        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "voice_interface"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Voice interface completed", thought + [f"[{ai_name}] Model backend produced voice interface response using Knowledge context."], [f"[{ai_name}] Returned voice/speech guidance."], ["Next: configure microphone for voice input."], model.text)

        parts = [f"Voice Interface for: {task}\n"]

        if any(x in t for x in ["command", "control", "navigate"]):
            parts.append(
                "Voice Command Framework:\n"
                "1. Wake word: 'Hey Nexus' or click the mic button to start.\n"
                "2. Command patterns:\n"
                "   - 'Start mission [task description]'\n"
                "   - 'Open [capability name]'\n"
                "   - 'Search for [query]'\n"
                "   - 'Read [file name]'\n"
                "   - 'Take notes: [content]'\n"
                "3. Confirmation: The AI confirms what it heard before executing.\n"
                "4. Error handling: If speech is unclear, ask to repeat or type.\n\n"
                "Privacy: Voice data is processed locally. No audio is sent to external servers.\n\n"
                ""
            )
        elif any(x in t for x in ["read aloud", "text to speech", "tts", "speak"]):
            parts.append(
                "Text-to-Speech Framework:\n"
                "1. Select text: Choose what to read (mission output, notes, documents).\n"
                "2. Voice settings: Adjust speed, pitch, and volume.\n"
                "3. Playback controls: Play, pause, skip, restart.\n"
                "4. Accessibility: Useful for visually impaired users or hands-free operation.\n\n"
                "Privacy: Speech synthesis runs locally. No text is sent externally.\n\n"
                ""
            )
        else:
            parts.append(
                "Voice Interface Framework:\n"
                "  - Voice commands: Control Command Nexus hands-free\n"
                "  - Dictation: Speak instead of type\n"
                "  - Text-to-speech: Have the AI read output aloud\n"
                "  - Voice preferences: Customize wake word, speed, voice\n\n"
                "Privacy: All voice processing is local. No audio sent to external servers.\n\n"
                "Commands:\n"
                "  - 'voice command: [instruction]'\n"
                "  - 'read aloud: [text or output]'\n"
                "  - 'dictation mode'\n\n"
                ""
            )

        result = "\n".join(parts)
        return RuntimeResult(RuntimeStatus.COMPLETED, "Voice interface completed (local fallback)", thought + [f"[{ai_name}] Voice Interface executed locally (local mode)."], [f"[{ai_name}] Produced voice interaction framework."], ["Next: configure microphone. "], result)

    def _run_visual_canvas(self, task, ai_name, meta, knowledge, thought):
        ai_uuid = str(meta.get("uuid", ""))
        t = task.lower()

        if ai_uuid:
            self._memory.add(ai_uuid, f"Visual canvas task: {task}", tags=["visual", "canvas"], source="visual_canvas", importance=0.5)

        self._tier_audit.log_past(
            category=AuditCategory.LOCAL_RESPONSE,
            action="Visual canvas triggered",
            detail=f"Query: {task[:100]}",
            source="user",
            capability="Visual Canvas",
            confidence="medium",
        )

        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "visual_canvas"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Visual canvas completed", thought + [f"[{ai_name}] Model backend produced visual canvas output using Knowledge context."], [f"[{ai_name}] Returned visual layout/diagram guidance."], ["Next: apply layout in the Visual Canvas workspace."], model.text)

        parts = [f"Visual Canvas for: {task}\n"]

        if any(x in t for x in ["diagram", "flowchart", "process flow"]):
            parts.append(
                "Diagram/Flowchart Framework:\n"
                "1. Identify nodes: What are the key steps/decision points?\n"
                "2. Define connections: How do nodes connect (sequential, branching, loop)?\n"
                "3. Layout: Top-to-bottom (process) or left-to-right (workflow).\n"
                "4. Decision points: Diamond shapes with yes/no labels.\n"
                "5. Start/end: Rounded rectangles for terminals.\n"
                "6. Process: Rectangles for actions.\n"
                "7. Data: Parallelograms for inputs/outputs.\n\n"
                "Text representation:\n"
                "  [Start] â†’ [Input Data] â†’ [Validate] â†’ (Valid?) â†’ [Process] â†’ [Output] â†’ [End]\n"
                "                                       â†“ No\n"
                "                                  [Show Error] â†’ [End]\n\n"
                ""
            )
        elif any(x in t for x in ["mind map", "brainstorm", "idea map"]):
            parts.append(
                "Mind Map Framework:\n"
                "1. Central node: The main topic or question.\n"
                "2. Primary branches: 4-6 main themes/categories.\n"
                "3. Sub-branches: Details, examples, questions under each theme.\n"
                "4. Cross-links: Connections between branches.\n"
                "5. Visual cues: Colors for categories, icons for priority.\n\n"
                "Text representation:\n"
                "  Central: [Topic]\n"
                "  â”œâ”€â”€ Branch 1: [Theme A]\n"
                "  â”‚   â”œâ”€â”€ [Detail 1]\n"
                "  â”‚   â””â”€â”€ [Detail 2]\n"
                "  â”œâ”€â”€ Branch 2: [Theme B]\n"
                "  â”‚   â””â”€â”€ [Detail 3]\n"
                "  â””â”€â”€ Branch 3: [Theme C]\n\n"
                ""
            )
        elif any(x in t for x in ["layout", "organize", "arrange", "whiteboard"]):
            parts.append(
                "Visual Layout Framework:\n"
                "1. Grid system: Define rows and columns for alignment.\n"
                "2. Grouping: Related items placed together with visual boundaries.\n"
                "3. Hierarchy: Size and position indicate importance.\n"
                "4. Spacing: Consistent gaps between elements (8px, 16px, 24px).\n"
                "5. Color coding: Use color to categorize or indicate status.\n"
                "6. Labels: Clear, concise text for each element.\n\n"
                ""
            )
        else:
            parts.append(
                "Visual Canvas Framework:\n"
                "  - Create diagrams and flowcharts\n"
                "  - Build mind maps and brainstorming boards\n"
                "  - Design visual layouts and whiteboards\n"
                "  - Organize information spatially\n"
                "  - Export visual representations\n\n"
                "Commands:\n"
                "  - 'diagram [process description]'\n"
                "  - 'mind map for [topic]'\n"
                "  - 'layout [elements to arrange]'\n\n"
                ""
            )

        result = "\n".join(parts)
        return RuntimeResult(RuntimeStatus.COMPLETED, "Visual canvas completed (local fallback)", thought + [f"[{ai_name}] Visual Canvas executed locally (local mode)."], [f"[{ai_name}] Produced visual framework with text-based diagram representation."], ["Next: use framework in Visual Canvas workspace. "], result)

    def _run_medical_researcher(self, task, ai_name, meta, knowledge, thought):
        ai_uuid = str(meta.get("uuid", ""))

        if ai_uuid:
            self._memory.add(ai_uuid, f"Medical research: {task}", tags=["medical", "research"], source="medical_researcher", importance=0.8)

        self._tier_audit.log_past(
            category=AuditCategory.LOCAL_RESPONSE,
            action="Medical research triggered",
            detail=f"Query: {task[:100]}",
            source="user",
            capability="Medical Researcher",
            confidence="medium",
        )

        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "medical_research"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Medical research completed", thought + [f"[{ai_name}] Model backend produced medical research output using Knowledge context."], [f"[{ai_name}] Returned medical literature summary with disclaimers."], ["Next: verify findings with a qualified healthcare professional."], model.text)

        t = task.lower()
        parts = [f"Medical Research for: {task}\n"]

        if any(x in t for x in ["drug interaction", "medication", "side effect", "dosage", "prescription"]):
            parts.append(
                "Drug Information & Interaction Framework:\n"
                "1. Identify the medication(s): Name, dosage, route, frequency.\n"
                "2. Check interactions:\n"
                "   - Drug-drug interactions (use Drugs.com, RxList, or MedlinePlus)\n"
                "   - Drug-food interactions (grapefruit, dairy, etc.)\n"
                "   - Drug-condition interactions (pregnancy, liver/kidney disease)\n"
                "3. Side effects: Common, rare, and serious adverse reactions.\n"
                "4. Contraindications: Who should NOT take this medication.\n"
                "5. Monitoring: What lab values or symptoms to watch.\n\n"
                "Resources for verification:\n"
                "  - PubMed: pubmed.ncbi.nlm.nih.gov\n"
                "  - MedlinePlus: medlineplus.gov\n"
                "  - FDA: fda.gov/drugs\n"
                "  - Drugs.com interaction checker\n\n"
                "DISCLAIMER: For research purposes only. NOT medical advice. "
                "Always consult a licensed healthcare provider before making "
                "any decisions about medications.\n"
            )
        elif any(x in t for x in ["clinical trial", "study", "evidence", "treatment", "therapy"]):
            parts.append(
                "Clinical Evidence Research Framework:\n"
                "1. Define the question: Population, Intervention, Comparison, Outcome (PICO).\n"
                "2. Search databases:\n"
                "   - PubMed (biomedical literature)\n"
                "   - Cochrane Library (systematic reviews)\n"
                "   - ClinicalTrials.gov (ongoing/completed trials)\n"
                "3. Evaluate evidence quality:\n"
                "   - Level I: Systematic reviews, meta-analyses\n"
                "   - Level II: Randomized controlled trials\n"
                "   - Level III: Cohort/case-control studies\n"
                "   - Level IV: Expert opinion, case reports\n"
                "4. Key findings: Efficacy, safety, effect size, confidence intervals.\n"
                "5. Limitations: Sample size, bias, conflicts of interest, generalizability.\n\n"
                "DISCLAIMER: For research purposes only. NOT medical advice. "
                "Always consult a licensed healthcare provider.\n"
            )
        elif any(x in t for x in ["disease", "condition", "symptom", "diagnos", "health condition"]):
            parts.append(
                "Disease & Condition Research Framework:\n"
                "1. Condition overview: Definition, prevalence, pathophysiology.\n"
                "2. Symptoms: Primary, secondary, red-flag symptoms.\n"
                "3. Risk factors: Genetic, environmental, lifestyle.\n"
                "4. Diagnosis: Diagnostic criteria, tests, differential diagnosis.\n"
                "5. Treatment options:\n"
                "   - First-line treatments (guideline-recommended)\n"
                "   - Alternative/adjunctive therapies\n"
                "   - Emerging treatments (clinical trials)\n"
                "6. Prognosis: Expected outcomes, complications, quality of life.\n"
                "7. Patient resources: Support groups, educational materials.\n\n"
                "Resources:\n"
                "  - Mayo Clinic, WebMD (patient-friendly overviews)\n"
                "  - PubMed, UpToDate (clinical detail)\n"
                "  - CDC, WHO (epidemiology and guidelines)\n\n"
                "DISCLAIMER: For research purposes only. NOT medical advice. "
                "Always consult a licensed healthcare provider for diagnosis and treatment.\n"
            )
        else:
            parts.append(
                "Medical Research Framework:\n"
                "  - Drug information and interaction checking\n"
                "  - Clinical evidence and trial research\n"
                "  - Disease/condition information gathering\n"
                "  - Literature search and summarization\n"
                "  - Treatment option comparison\n\n"
                "Commands:\n"
                "  - 'research [medication name] interactions'\n"
                "  - 'find clinical trials for [condition]'\n"
                "  - 'summarize evidence for [treatment]'\n"
                "  - 'what is [disease/condition]'\n\n"
                "DISCLAIMER: For research purposes only. NOT medical advice. "
                "Always consult a licensed healthcare provider.\n"
            )

        result = "\n".join(parts)
        return RuntimeResult(RuntimeStatus.COMPLETED, "Medical research completed (local fallback)", thought + [f"[{ai_name}] Medical Researcher executed locally (local mode)."], [f"[{ai_name}] Produced medical research framework with verification resources and disclaimers."], ["Next: verify findings with a healthcare professional. "], result)

    def _run_legal_document_reviewer(self, task, ai_name, meta, knowledge, thought):
        ai_uuid = str(meta.get("uuid", ""))

        if ai_uuid:
            self._memory.add(ai_uuid, f"Legal review: {task}", tags=["legal", "review"], source="legal_reviewer", importance=0.8)

        self._tier_audit.log_past(
            category=AuditCategory.LOCAL_RESPONSE,
            action="Legal document review triggered",
            detail=f"Query: {task[:100]}",
            source="user",
            capability="Legal Document Reviewer",
            confidence="medium",
        )

        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "legal_review"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Legal review completed", thought + [f"[{ai_name}] Model backend produced legal analysis using Knowledge context."], [f"[{ai_name}] Returned contract analysis with risk flags and recommendations."], ["Next: have a qualified attorney review before acting."], model.text)

        t = task.lower()
        parts = [f"Legal Document Review for: {task}\n"]

        if any(x in t for x in ["contract", "agreement", "nda", "non-compete", "non-disclosure"]):
            parts.append(
                "Contract Review Framework:\n"
                "1. Parties: Who is bound? Are all parties correctly identified?\n"
                "2. Obligations: What must each party do? Are obligations clear and measurable?\n"
                "3. Term & termination: Duration, renewal terms, early termination clauses.\n"
                "4. Payment: Amount, schedule, late payment penalties, currency.\n"
                "5. Intellectual property: Who owns created work? License terms?\n"
                "6. Confidentiality: What's protected, for how long, penalties for breach.\n"
                "7. Liability & indemnification: Who bears risk? Caps on liability?\n"
                "8. Dispute resolution: Arbitration, mediation, or litigation? Jurisdiction?\n"
                "9. Force majeure: What happens in unforeseen circumstances?\n"
                "10. Red flags:\n"
                "    - Vague or ambiguous language\n"
                "    - Unilateral modification rights\n"
                "    - Auto-renewal without notice\n"
                "    - Excessive liability or indemnification\n"
                "    - No exit clause or termination without cause\n\n"
                "DISCLAIMER: For review purposes only. NOT legal advice. "
                "Always consult a qualified attorney before signing.\n"
            )
        elif any(x in t for x in ["terms of service", "tos", "privacy policy", "terms of use"]):
            parts.append(
                "Terms of Service Review Framework:\n"
                "1. User rights: What can users do? What's prohibited?\n"
                "2. Data usage: What data is collected, how it's used, shared, stored.\n"
                "3. Intellectual property: Content ownership, license grants to the platform.\n"
                "4. Liability: Disclaimers, limitation of liability, indemnification.\n"
                "5. Termination: Account suspension/deletion conditions.\n"
                "6. Dispute resolution: Mandatory arbitration, class action waivers.\n"
                "7. Changes: Can terms change without notice? Opt-out options?\n"
                "8. Red flags:\n"
                "    - Broad license to user content\n"
                "    - No data deletion mechanism\n"
                "    - One-sided termination rights\n"
                "    - Mandatory arbitration with no opt-out\n"
                "    - Unilateral term changes without notice\n\n"
                "DISCLAIMER: For review purposes only. NOT legal advice. "
                "Always consult a qualified attorney.\n"
            )
        elif any(x in t for x in ["clause", "provision", "liability", "indemnif", "warranty", "arbitration"]):
            parts.append(
                "Legal Clause Analysis Framework:\n"
                "1. Clause type: Identify the legal purpose (indemnification, warranty, etc.).\n"
                "2. Scope: What does it cover? Is it overly broad or narrow?\n"
                "3. Enforceability: Is it likely enforceable in the relevant jurisdiction?\n"
                "4. Risk allocation: Who bears the risk? Is it balanced?\n"
                "5. Standard vs non-standard: How does it compare to industry norms?\n"
                "6. Negotiation points: What could be modified for better balance?\n"
                "7. Missing provisions: What standard clauses are absent?\n\n"
                "DISCLAIMER: For analysis purposes only. NOT legal advice. "
                "Always consult a qualified attorney.\n"
            )
        else:
            parts.append(
                "Legal Document Review Framework:\n"
                "  - Contract review (NDAs, service agreements, non-competes)\n"
                "  - Terms of Service and Privacy Policy analysis\n"
                "  - Clause-level risk assessment\n"
                "  - Liability and indemnification review\n"
                "  - Dispute resolution clause analysis\n"
                "  - IP ownership and license review\n\n"
                "Commands:\n"
                "  - 'review this contract: [text or file path]'\n"
                "  - 'analyze [clause type] clause'\n"
                "  - 'check terms of service for [concern]'\n"
                "  - 'what are the red flags in [document type]'\n\n"
                "DISCLAIMER: For review purposes only. NOT legal advice. "
                "Always consult a qualified attorney before signing or acting.\n"
            )

        result = "\n".join(parts)
        return RuntimeResult(RuntimeStatus.COMPLETED, "Legal review completed (local fallback)", thought + [f"[{ai_name}] Legal Document Reviewer executed locally (local mode)."], [f"[{ai_name}] Produced legal review framework with risk flags and disclaimers."], ["Next: have a qualified attorney review. "], result)

    def _run_wellness_coach(self, task, ai_name, meta, knowledge, thought):
        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "wellness_coaching"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Wellness coaching completed", thought + [f"[{ai_name}] Model backend produced wellness guidance."], [f"[{ai_name}] Returned wellness plan."], ["Next: follow the plan and track progress."], model.text)

        t = task.lower()
        parts = [f"Wellness Coach — Local Intelligence for: {task}\n"]

        if any(x in t for x in ["fitness", "workout", "exercise", "muscle", "weight loss", "cardio", "strength"]):
            parts.append(
                "Fitness Planning Framework:\n"
                "1. Current fitness level assessment (beginner, intermediate, advanced)\n"
                "2. Goal definition (strength, endurance, weight loss, mobility)\n"
                "3. Weekly schedule template:\n"
                "   - 3-4 days exercise, 1-2 rest days\n"
                "   - Mix of cardio and strength training\n"
                "   - Progressive overload principle\n"
                "4. Exercise selection based on equipment and space\n"
                "5. Warm-up and cool-down routines\n"
                "6. Tracking metrics (reps, sets, time, distance)\n\n"
                "DISCLAIMER: General fitness guidance, not medical advice. "
                "Consult a healthcare professional before starting any exercise program.\n"
            )
        elif any(x in t for x in ["nutrition", "diet", "meal plan", "calorie", "eating", "food"]):
            parts.append(
                "Nutrition Guidance Framework:\n"
                "1. Current eating patterns assessment\n"
                "2. Nutritional goals (weight management, energy, muscle gain)\n"
                "3. Daily calorie target estimation (TDEE-based)\n"
                "4. Macro distribution (protein, carbs, fats)\n"
                "5. Meal planning template:\n"
                "   - Breakfast, lunch, dinner, 1-2 snacks\n"
                "   - Whole foods focus\n"
                "   - Hydration targets\n"
                "6. Weekly meal prep suggestions\n"
                "7. Common nutritional pitfalls to avoid\n\n"
                "DISCLAIMER: General nutrition guidance, not medical advice. "
                "Consult a registered dietitian or healthcare professional for personalized nutrition plans.\n"
            )
        elif any(x in t for x in ["mental", "stress", "mindfulness", "meditation", "anxiety", "sleep"]):
            parts.append(
                "Mental Wellness Framework:\n"
                "1. Stress assessment: Identify primary stressors\n"
                "2. Mindfulness practices:\n"
                "   - 5-minute breathing exercises\n"
                "   - Body scan meditation\n"
                "   - Gratitude journaling (3 items daily)\n"
                "3. Sleep hygiene checklist:\n"
                "   - Consistent sleep/wake times\n"
                "   - No screens 30 min before bed\n"
                "   - Cool, dark room\n"
                "   - Limit caffeine after 2pm\n"
                "4. Stress management techniques:\n"
                "   - Time blocking\n"
                "   - Progressive muscle relaxation\n"
                "   - Regular physical activity\n"
                "5. When to seek professional help\n\n"
                "DISCLAIMER: General wellness guidance, not medical or mental health advice. "
                "If experiencing persistent anxiety, depression, or crisis, contact a mental health professional "
                "or call 988 (Suicide & Crisis Lifeline).\n"
            )
        elif any(x in t for x in ["habit", "routine", "self-care", "lifestyle"]):
            parts.append(
                "Habit Building Framework:\n"
                "1. Identify the keystone habit to build first\n"
                "2. Start small: 2-minute version of the habit\n"
                "3. Stack on existing routine (after [current habit], I will [new habit])\n"
                "4. Track daily: visual tracker or app\n"
                "5. Never miss twice: if you miss one day, get back on track immediately\n"
                "6. Celebrate small wins\n"
                "7. Review weekly: what worked, what didn't, adjust\n"
                "8. After 30 days, add the next habit\n\n"
                "DISCLAIMER: General wellness guidance. "
                "Consult a healthcare professional for medical concerns.\n"
            )
        else:
            parts.append(
                "Wellness Coach Framework:\n"
                "  - Fitness planning (workouts, progressive overload, tracking)\n"
                "  - Nutrition guidance (meal planning, macros, hydration)\n"
                "  - Mental wellness (mindfulness, stress management, sleep hygiene)\n"
                "  - Habit building (small starts, habit stacking, daily tracking)\n\n"
                "Commands:\n"
                "  - 'create a fitness plan for [goal]'\n"
                "  - 'plan my meals for the week'\n"
                "  - 'help me manage stress'\n"
                "  - 'build a habit of [habit name]'\n\n"
                "DISCLAIMER: General wellness guidance, not medical advice. "
                "Consult a healthcare professional for medical concerns.\n"
            )

        result = "\n".join(parts)
        return RuntimeResult(RuntimeStatus.COMPLETED, "Wellness coaching completed (local fallback)", thought + [f"[{ai_name}] Wellness Coach executed locally (local mode)."], [f"[{ai_name}] Produced wellness framework with disclaimers."], ["Next: follow the plan and track progress."], result)

    def _run_content_strategist(self, task, ai_name, meta, knowledge, thought):
        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "content_strategy"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Content strategy completed", thought + [f"[{ai_name}] Model backend produced content strategy."], [f"[{ai_name}] Returned content plan."], ["Next: review and schedule content."], model.text)

        t = task.lower()
        parts = [f"Content Strategist — Local Intelligence for: {task}\n"]

        if any(x in t for x in ["calendar", "schedule", "editorial", "content plan"]):
            parts.append(
                "Content Calendar Framework:\n"
                "1. Define content pillars (3-5 core themes)\n"
                "2. Posting frequency per platform:\n"
                "   - Blog: 1-2x/week\n"
                "   - LinkedIn: 3-5x/week\n"
                "   - Twitter/X: 1-3x/day\n"
                "   - Instagram: 3-4x/week\n"
                "   - YouTube: 1x/week\n"
                "3. Weekly calendar template:\n"
                "   - Mon: Educational post\n"
                "   - Wed: Behind-the-scenes / story\n"
                "   - Fri: Value-driven content\n"
                "   - Sun: Week recap or preview\n"
                "4. Batch creation: plan themes monthly, create weekly\n"
                "5. Track performance: engagement rate, reach, conversions\n"
            )
        elif any(x in t for x in ["audience", "persona", "target", "demographic"]):
            parts.append(
                "Audience Analysis Framework:\n"
                "1. Demographic profile (age, location, profession)\n"
                "2. Psychographic profile (values, interests, challenges)\n"
                "3. Content preferences (format, length, tone)\n"
                "4. Platform behavior (where they spend time, when active)\n"
                "5. Pain points and questions to address\n"
                "6. Content-to-audience mapping: which content serves which segment\n"
                "7. Feedback loops: surveys, comments, DMs, analytics\n"
            )
        elif any(x in t for x in ["repurpose", "cross-platform", "reuse", "reformat"]):
            parts.append(
                "Content Repurposing Framework:\n"
                "1. Start with pillar content (long-form: blog, video, podcast)\n"
                "2. Break into micro-content:\n"
                "   - Blog → 5-10 social posts, 1 infographic, 1 video script\n"
                "   - Video → clips, transcript blog post, quote graphics\n"
                "   - Podcast → audiogram, show notes, quote cards\n"
                "3. Adapt format per platform:\n"
                "   - LinkedIn: professional angle, carousel\n"
                "   - Instagram: visual, reels, stories\n"
                "   - Twitter/X: thread, key takeaways\n"
                "4. Schedule staggered release (2-3 day gaps per platform)\n"
                "5. Track which repurposed formats perform best\n"
            )
        elif any(x in t for x in ["brand voice", "tone", "messaging", "positioning"]):
            parts.append(
                "Brand Voice Framework:\n"
                "1. Voice attributes (3-5 adjectives: e.g., authoritative, warm, witty)\n"
                "2. Tone variations by context (educational vs promotional vs customer service)\n"
                "3. Vocabulary guidelines (preferred terms, avoided terms)\n"
                "4. Sentence structure preferences (concise, conversational, formal)\n"
                "5. Do/Don't list with examples\n"
                "6. Apply consistently across all channels\n"
            )
        else:
            parts.append(
                "Content Strategy Framework:\n"
                "  - Content calendar planning (pillars, frequency, scheduling)\n"
                "  - Audience analysis (demographics, psychographics, platform behavior)\n"
                "  - Platform optimization (format, timing, hashtags, trends)\n"
                "  - Content repurposing (pillar → micro-content across platforms)\n"
                "  - Brand voice (attributes, tone, vocabulary, consistency)\n"
                "  - Performance tracking (engagement, reach, conversions)\n\n"
                "Commands:\n"
                "  - 'create a content calendar for [platform]'\n"
                "  - 'analyze my audience for [topic]'\n"
                "  - 'repurpose this content for [platforms]'\n"
                "  - 'define my brand voice'\n"
            )

        result = "\n".join(parts)
        return RuntimeResult(RuntimeStatus.COMPLETED, "Content strategy completed (local fallback)", thought + [f"[{ai_name}] Content Strategist executed locally (local mode)."], [f"[{ai_name}] Produced content strategy framework."], ["Next: review and implement the strategy."], result)

    def _run_fact_checker(self, task, ai_name, meta, knowledge, thought):
        model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "fact_check"))
        if model.text and not model.error:
            return RuntimeResult(RuntimeStatus.COMPLETED, "Fact check completed", thought + [f"[{ai_name}] Model backend produced fact-check analysis."], [f"[{ai_name}] Returned verification report."], ["Next: review sources and confidence levels."], model.text)

        t = task.lower()
        parts = [f"Fact Checker — Local Intelligence for: {task}\n"]

        if any(x in t for x in ["claim", "verify", "is this true", "is this accurate", "is this real"]):
            parts.append(
                "Claim Verification Framework:\n"
                "1. Claim extraction: Identify the specific verifiable assertion(s)\n"
                "2. Source identification: List potential verification sources\n"
                "   - Primary sources (official documents, studies, data)\n"
                "   - Secondary sources (reputable news, academic journals)\n"
                "   - Tertiary sources (encyclopedias, databases)\n"
                "3. Cross-reference: Check at least 2-3 independent sources\n"
                "4. Credibility assessment:\n"
                "   - Academic/peer-reviewed: High credibility\n"
                "   - Established news outlets: Medium-high credibility\n"
                "   - Blogs/opinion: Low credibility\n"
                "   - Social media/unverified: Very low credibility\n"
                "5. Bias detection: Flag potential political, commercial, or ideological bias\n"
                "6. Confidence labeling:\n"
                "   - VERIFIED: Multiple independent credible sources confirm\n"
                "   - PARTIALLY VERIFIED: Some sources confirm, others nuance\n"
                "   - UNVERIFIED: No credible sources found\n"
                "   - CONTRADICTED: Credible sources disagree\n"
                "7. Summary report with confidence levels and source list\n\n"
                "NOTE: This is a verification framework. For live verification, "
                "web search access is needed (requires approval).\n"
            )
        elif any(x in t for x in ["misinformation", "disinformation", "fake news", "debunk"]):
            parts.append(
                "Misinformation Analysis Framework:\n"
                "1. Identify the claim being circulated\n"
                "2. Trace the origin of the claim (if possible)\n"
                "3. Check against fact-checking databases (Snopes, PolitiFact, FactCheck.org)\n"
                "4. Assess common misinformation patterns:\n"
                "   - Out-of-context quotes\n"
                "   - Manipulated images/data\n"
                "   - Misleading headlines\n"
                "   - Cherry-picked statistics\n"
                "   - Appeal to emotion over evidence\n"
                "5. Provide correct information with sources\n"
                "6. Flag the specific manipulation technique used\n"
                "7. Confidence: How certain is the debunking?\n\n"
                "NOTE: For live fact-checking, web search access is needed (requires approval).\n"
            )
        elif any(x in t for x in ["credibility", "source check", "bias"]):
            parts.append(
                "Source Credibility Framework:\n"
                "1. Source type assessment:\n"
                "   - Peer-reviewed academic: Highest credibility\n"
                "   - Government/official data: High credibility\n"
                "   - Established news (Reuters, AP, BBC): Medium-high\n"
                "   - Partisan news outlets: Medium (check bias direction)\n"
                "   - Blogs, opinion sites: Low\n"
                "   - Social media, anonymous: Very low\n"
                "2. Bias assessment:\n"
                "   - Political lean (left, center, right)\n"
                "   - Commercial interest (sponsored content, undisclosed ads)\n"
                "   - Ideological agenda\n"
                "3. Track record: Has this source been accurate before?\n"
                "4. Transparency: Does the source cite its own sources?\n"
                "5. Correction policy: Does the source issue corrections?\n"
                "6. Overall credibility score: 1-10 with justification\n"
            )
        else:
            parts.append(
                "Fact Checker Framework:\n"
                "  - Claim verification (extract, source, cross-reference, label)\n"
                "  - Misinformation analysis (origin, patterns, debunk)\n"
                "  - Source credibility assessment (type, bias, track record)\n"
                "  - Confidence labeling (verified, partial, unverified, contradicted)\n\n"
                "Commands:\n"
                "  - 'fact check this claim: [text]'\n"
                "  - 'is this true: [statement]'\n"
                "  - 'check the credibility of [source]'\n"
                "  - 'debunk this: [claim]'\n\n"
                "NOTE: For live verification with web search, approval is required.\n"
            )

        result = "\n".join(parts)
        return RuntimeResult(RuntimeStatus.COMPLETED, "Fact check completed (local fallback)", thought + [f"[{ai_name}] Fact Checker executed locally (local mode)."], [f"[{ai_name}] Produced verification framework with confidence labeling."], ["Next: review the framework and seek additional sources."], result)

    def _run_task_scheduler(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "task_scheduling"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Task scheduling completed", thought + [f"[{ai_name}] Model backend produced scheduling plan."], [f"[{ai_name}] Returned schedule."], ["Next: confirm and apply schedule."], model.text)
        except Exception:
            pass
        result = (f"Task Scheduler — Local Intelligence for: {task}\n\n"
            "Scheduling Framework:\n1. Identify tasks and priorities\n2. Estimate duration for each\n"
            "3. Apply time blocking (high-priority in peak hours, batch similar, include buffer)\n"
            "4. Set reminders for key milestones\n5. Review and adjust at end of day\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Task scheduling completed (local fallback)", thought + [f"[{ai_name}] Task Scheduler executed locally."], [f"[{ai_name}] Produced scheduling framework."], ["Next: confirm schedule."], result)

    def _run_form_builder(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "form_building"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Form building completed", thought + [f"[{ai_name}] Model backend produced form design."], [f"[{ai_name}] Returned form structure."], ["Next: review and deploy form."], model.text)
        except Exception:
            pass
        result = (f"Form Builder — Local Intelligence for: {task}\n\n"
            "Form Design Framework:\n1. Define purpose and audience\n2. Choose question types (multiple choice, text, rating, date, file)\n"
            "3. Structure: Group related questions, logical flow\n4. Keep it short: only ask what you need\n"
            "5. Add clear instructions and labels\n6. Include validation rules\n7. Test before deployment\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Form building completed (local fallback)", thought + [f"[{ai_name}] Form Builder executed locally."], [f"[{ai_name}] Produced form design framework."], ["Next: implement form."], result)

    def _run_report_generator(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "report_generation"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Report generated", thought + [f"[{ai_name}] Model backend produced report."], [f"[{ai_name}] Returned report."], ["Next: review and distribute."], model.text)
        except Exception:
            pass
        result = (f"Report Generator — Local Intelligence for: {task}\n\n"
            "Report Structure:\n1. Executive Summary\n2. Background and Context\n3. Key Findings (with data)\n"
            "4. Analysis and Discussion\n5. Recommendations (actionable, prioritized)\n6. Appendices\n"
            "Formatting: Clear headers, charts/tables, cite sources, flag assumptions.\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Report generated (local fallback)", thought + [f"[{ai_name}] Report Generator executed locally."], [f"[{ai_name}] Produced report framework."], ["Next: fill in data and review."], result)

    def _run_invoice_processor(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "invoice_processing"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Invoice processed", thought + [f"[{ai_name}] Model backend produced invoice."], [f"[{ai_name}] Returned invoice."], ["Next: review and send."], model.text)
        except Exception:
            pass
        result = (f"Invoice Processor — Local Intelligence for: {task}\n\n"
            "Invoice Template:\n  Invoice #/Date/Due Date\n  Bill To: [Client]\n\n"
            "  Description | Qty | Rate | Amount\n  Subtotal | Tax | Total\n\n"
            "  Payment Terms: [Net 30 / Due on Receipt]\n"
            "DISCLAIMER: Review all calculations before sending.\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Invoice processed (local fallback)", thought + [f"[{ai_name}] Invoice Processor executed locally."], [f"[{ai_name}] Produced invoice template."], ["Next: fill in details and verify."], result)

    def _run_spreadsheet_analyst(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "spreadsheet_analysis"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Spreadsheet analysis completed", thought + [f"[{ai_name}] Model backend produced analysis."], [f"[{ai_name}] Returned spreadsheet guidance."], ["Next: apply formulas and verify."], model.text)
        except Exception:
            pass
        result = (f"Spreadsheet Analyst — Local Intelligence for: {task}\n\n"
            "Analysis Framework:\n1. Data cleaning (duplicates, formats, missing values)\n"
            "2. Key formulas: SUMIF, VLOOKUP/XLOOKUP, INDEX/MATCH, Pivot tables\n"
            "3. Analyses: Trend, category breakdowns, variance (actual vs budget)\n"
            "4. Best practices: Named ranges, document logic, test with sample data\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Spreadsheet analysis completed (local fallback)", thought + [f"[{ai_name}] Spreadsheet Analyst executed locally."], [f"[{ai_name}] Produced analysis framework."], ["Next: apply to your data."], result)

    def _run_data_visualizer(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "data_visualization"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Data visualization completed", thought + [f"[{ai_name}] Model backend produced visualization guidance."], [f"[{ai_name}] Returned chart recommendations."], ["Next: create the visualization."], model.text)
        except Exception:
            pass
        result = (f"Data Visualizer — Local Intelligence for: {task}\n\n"
            "Visualization Selection:\n1. Comparison → Bar/Column chart\n2. Trend → Line/Area chart\n"
            "3. Composition → Pie/Stacked bar/Treemap\n4. Distribution → Histogram/Box plot/Scatter\n"
            "5. Relationship → Scatter/Bubble/Heatmap\n6. Geographic → Choropleth map\n\n"
            "Best Practices: Simplest chart that communicates, label axes, purposeful color, no 3D, title states insight.\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Data visualization completed (local fallback)", thought + [f"[{ai_name}] Data Visualizer executed locally."], [f"[{ai_name}] Produced visualization guide."], ["Next: create the chart."], result)

    def _run_statistical_modeler(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "statistical_modeling"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Statistical analysis completed", thought + [f"[{ai_name}] Model backend produced statistical analysis."], [f"[{ai_name}] Returned model results."], ["Next: validate assumptions and interpret."], model.text)
        except Exception:
            pass
        result = (f"Statistical Modeler — Local Intelligence for: {task}\n\n"
            "Framework:\n1. Define hypothesis (H0, H1)\n2. Check assumptions (normality, variance, independence)\n"
            "3. Choose test: t-test/ANOVA (means), correlation/regression (relationship), chi-square (categorical)\n"
            "4. Report: statistic, p-value, effect size, confidence interval\n5. Flag limitations\n\n"
            "DISCLAIMER: Statistical results require proper interpretation. Consult a statistician for critical decisions.\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Statistical analysis completed (local fallback)", thought + [f"[{ai_name}] Statistical Modeler executed locally."], [f"[{ai_name}] Produced analysis framework."], ["Next: apply test and interpret."], result)

    def _run_trend_forecaster(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "trend_forecasting"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Trend forecast completed", thought + [f"[{ai_name}] Model backend produced forecast."], [f"[{ai_name}] Returned projection."], ["Next: validate with domain expertise."], model.text)
        except Exception:
            pass
        result = (f"Trend Forecaster — Local Intelligence for: {task}\n\n"
            "Framework:\n1. Plot time series, identify patterns\n2. Decompose: trend, seasonality, noise\n"
            "3. Methods: Moving average, Exponential smoothing, ARIMA, Linear regression\n"
            "4. Generate forecast with confidence intervals\n5. Backtest on historical data\n"
            "6. Flag external factors that could invalidate projection\n\n"
            "DISCLAIMER: Forecasts are estimates. External events can invalidate projections.\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Trend forecast completed (local fallback)", thought + [f"[{ai_name}] Trend Forecaster executed locally."], [f"[{ai_name}] Produced forecasting framework."], ["Next: apply to data and validate."], result)

    def _run_devops_assistant(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "devops_assistance"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "DevOps guidance completed", thought + [f"[{ai_name}] Model backend produced DevOps guidance."], [f"[{ai_name}] Returned configuration."], ["Next: review and test in staging."], model.text)
        except Exception:
            pass
        result = (f"DevOps Assistant — Local Intelligence for: {task}\n\n"
            "Framework:\n1. CI/CD: Source → Build → Test → Stage → Deploy (with rollback)\n"
            "2. Containers: One process per container, minimal images, .dockerignore\n"
            "3. IaC: Version control infrastructure, use modules, dry-run before apply\n"
            "4. Monitoring: Health checks, logs, alerts\n5. Security: Scan images, least privilege, secrets management\n\n"
            "DISCLAIMER: Never deploy without staging test. Always have rollback plan.\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "DevOps guidance completed (local fallback)", thought + [f"[{ai_name}] DevOps Assistant executed locally."], [f"[{ai_name}] Produced DevOps framework."], ["Next: review and apply carefully."], result)

    def _run_database_manager(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "database_management"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Database guidance completed", thought + [f"[{ai_name}] Model backend produced database guidance."], [f"[{ai_name}] Returned SQL/schema."], ["Next: test on dev database."], model.text)
        except Exception:
            pass
        result = (f"Database Manager — Local Intelligence for: {task}\n\n"
            "Framework:\n1. Schema: Normalize to 3NF, denormalize for performance\n"
            "2. Indexes: Index WHERE/JOIN/ORDER BY columns\n3. Optimization: EXPLAIN, avoid SELECT*, parameterized queries\n"
            "4. Patterns: Pagination (cursor-based), GROUP BY/HAVING, JOIN types\n5. Safety: Always backup before schema changes\n\n"
            "DISCLAIMER: Never execute on production without testing. Always backup first.\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Database guidance completed (local fallback)", thought + [f"[{ai_name}] Database Manager executed locally."], [f"[{ai_name}] Produced database framework."], ["Next: test on dev database."], result)

    def _run_test_generator(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "test_generation"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Test generation completed", thought + [f"[{ai_name}] Model backend produced test code."], [f"[{ai_name}] Returned test suite."], ["Next: review and run tests."], model.text)
        except Exception:
            pass
        result = (f"Test Generator — Local Intelligence for: {task}\n\n"
            "Framework:\n1. Identify what to test (happy path, edge cases, error paths, integration)\n"
            "2. Structure (AAA): Arrange, Act, Assert\n3. Coverage: Unit, integration, edge case tests\n"
            "4. Best practices: One assertion per test, descriptive names, use fixtures/mocks\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Test generation completed (local fallback)", thought + [f"[{ai_name}] Test Generator executed locally."], [f"[{ai_name}] Produced test framework."], ["Next: implement and run tests."], result)

    def _run_documentation_generator(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "documentation_generation"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Documentation generated", thought + [f"[{ai_name}] Model backend produced documentation."], [f"[{ai_name}] Returned docs."], ["Next: review and publish."], model.text)
        except Exception:
            pass
        result = (f"Documentation Generator — Local Intelligence for: {task}\n\n"
            "Framework:\n1. API docs: Endpoint, parameters, request/response examples, auth\n"
            "2. README: Description, install, usage, config, contributing\n"
            "3. Code docs: Docstrings for public functions, types, examples\n"
            "4. Best practices: Keep examples current, document the 'why'\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Documentation generated (local fallback)", thought + [f"[{ai_name}] Documentation Generator executed locally."], [f"[{ai_name}] Produced documentation framework."], ["Next: fill in specifics."], result)

    def _run_script_writer(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "script_writing"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Script written", thought + [f"[{ai_name}] Model backend produced script."], [f"[{ai_name}] Returned script."], ["Next: review and revise."], model.text)
        except Exception:
            pass
        result = (f"Script Writer — Local Intelligence for: {task}\n\n"
            "Script Framework:\n1. Logline: One-sentence summary\n2. Structure: Setup, inciting incident, rising action, climax, resolution\n"
            "3. Scene cards: Location, characters, action, dialogue beats\n"
            "4. Format: Scene heading (INT/EXT), action lines, character names centered, dialogue\n"
            "5. Tips: Show don't tell, subtext in dialogue, visual storytelling\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Script written (local fallback)", thought + [f"[{ai_name}] Script Writer executed locally."], [f"[{ai_name}] Produced script framework."], ["Next: develop scenes and dialogue."], result)

    def _run_copy_editor(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "copy_editing"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Copy editing completed", thought + [f"[{ai_name}] Model backend produced edited copy."], [f"[{ai_name}] Returned edited text."], ["Next: review changes."], model.text)
        except Exception:
            pass
        result = (f"Copy Editor — Local Intelligence for: {task}\n\n"
            "Editing Checklist:\n1. Grammar and spelling (correct all errors)\n"
            "2. Style consistency (tone, voice, tense, POV)\n3. Clarity (simplify complex sentences)\n"
            "4. Structure (paragraph flow, transitions)\n5. Word choice (eliminate redundancy, jargon)\n"
            "6. Factual claims (flag for verification)\n7. Preserve author's voice\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Copy editing completed (local fallback)", thought + [f"[{ai_name}] Copy Editor executed locally."], [f"[{ai_name}] Produced editing checklist."], ["Next: apply edits and review."], result)

    def _run_podcast_planner(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "podcast_planning"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Podcast plan completed", thought + [f"[{ai_name}] Model backend produced podcast plan."], [f"[{ai_name}] Returned episode plan."], ["Next: review and record."], model.text)
        except Exception:
            pass
        result = (f"Podcast Planner — Local Intelligence for: {task}\n\n"
            "Planning Framework:\n1. Show concept: Niche, target audience, format (interview/solo/panel)\n"
            "2. Episode structure: Intro hook, main content, segments, call-to-action, outro\n"
            "3. Topic list: 10-20 episode ideas with brief descriptions\n"
            "4. Show notes template: Title, summary, timestamps, links, resources\n"
            "5. Production: Equipment, recording software, editing workflow, publishing schedule\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Podcast plan completed (local fallback)", thought + [f"[{ai_name}] Podcast Planner executed locally."], [f"[{ai_name}] Produced podcast framework."], ["Next: develop first episode."], result)

    def _run_brand_strategist(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "brand_strategy"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Brand strategy completed", thought + [f"[{ai_name}] Model backend produced brand strategy."], [f"[{ai_name}] Returned brand framework."], ["Next: review and implement."], model.text)
        except Exception:
            pass
        result = (f"Brand Strategist — Local Intelligence for: {task}\n\n"
            "Brand Framework:\n1. Brand purpose: Why does this brand exist beyond profit?\n"
            "2. Positioning: What category? What's the unique value? Who's the competitor?\n"
            "3. Brand voice: Personality traits, tone guidelines, do/don't examples\n"
            "4. Visual identity: Logo direction, color palette, typography, imagery style\n"
            "5. Messaging: Tagline, value proposition, key messages per audience\n"
            "6. Brand guidelines: Usage rules, dos and don'ts, templates\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Brand strategy completed (local fallback)", thought + [f"[{ai_name}] Brand Strategist executed locally."], [f"[{ai_name}] Produced brand framework."], ["Next: refine and implement."], result)

    def _run_presentation_coach(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "presentation_coaching"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Presentation coaching completed", thought + [f"[{ai_name}] Model backend produced coaching feedback."], [f"[{ai_name}] Returned presentation guidance."], ["Next: apply feedback and rehearse."], model.text)
        except Exception:
            pass
        result = (f"Presentation Coach — Local Intelligence for: {task}\n\n"
            "Coaching Framework:\n1. Structure: Hook → Problem → Solution → Evidence → Call to action\n"
            "2. Slide design: One idea per slide, minimal text, strong visuals, consistent theme\n"
            "3. Delivery: Pace (not too fast), eye contact, pauses for emphasis, confident posture\n"
            "4. Engagement: Questions, stories, analogies, audience participation\n"
            "5. Practice: Time yourself, record and review, get feedback\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Presentation coaching completed (local fallback)", thought + [f"[{ai_name}] Presentation Coach executed locally."], [f"[{ai_name}] Produced coaching framework."], ["Next: apply and rehearse."], result)

    def _run_pr_assistant(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "pr_assistance"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "PR assistance completed", thought + [f"[{ai_name}] Model backend produced PR content."], [f"[{ai_name}] Returned PR draft."], ["Next: review and approve before sending."], model.text)
        except Exception:
            pass
        result = (f"PR Assistant — Local Intelligence for: {task}\n\n"
            "PR Framework:\n1. Press release structure: Headline, dateline, intro paragraph, body, quote, boilerplate, contact\n"
            "2. Media pitch: Personalized, newsworthy angle, why now, why this journalist\n"
            "3. Crisis comms: Acknowledge, take responsibility, action plan, follow-up commitment\n"
            "4. Distribution: Target relevant journalists, timing matters, follow up respectfully\n\n"
            "DISCLAIMER: Never auto-send to media. Review all content before distribution.\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "PR assistance completed (local fallback)", thought + [f"[{ai_name}] PR Assistant executed locally."], [f"[{ai_name}] Produced PR framework."], ["Next: review and approve."], result)

    def _run_internal_comms_writer(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "internal_comms"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Internal comms written", thought + [f"[{ai_name}] Model backend produced internal communication."], [f"[{ai_name}] Returned comms draft."], ["Next: review and distribute."], model.text)
        except Exception:
            pass
        result = (f"Internal Comms Writer — Local Intelligence for: {task}\n\n"
            "Framework:\n1. Audience: Who is this for? (all staff, team, leadership)\n"
            "2. Tone: Match company culture — professional yet human\n"
            "3. Structure: Context → Key message → Details → Action needed → Q&A contact\n"
            "4. Channel: Email, Slack/Teams, all-hands, intranet — match message to channel\n"
            "5. Sensitive info: Flag anything that shouldn't be in writing or needs legal review\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Internal comms written (local fallback)", thought + [f"[{ai_name}] Internal Comms Writer executed locally."], [f"[{ai_name}] Produced comms framework."], ["Next: review and distribute."], result)

    def _run_academic_citation_manager(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "academic_citation"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Citation management completed", thought + [f"[{ai_name}] Model backend produced citations."], [f"[{ai_name}] Returned formatted citations."], ["Next: verify against sources."], model.text)
        except Exception:
            pass
        result = (f"Academic Citation Manager — Local Intelligence for: {task}\n\n"
            "Citation Framework:\n1. Identify citation style (APA, MLA, Chicago, Harvard, IEEE)\n"
            "2. Core elements: Author, title, date, source, publisher, URL, access date\n"
            "3. APA format: Author, A. A. (Year). Title. Source. DOI/URL\n"
            "4. MLA format: Author. Title. Source, Publisher, Year, pp. range.\n"
            "5. Chicago format: Author. Title. Place: Publisher, Year.\n"
            "6. In-text: APA (Author, Year), MLA (Author page), Chicago (Author Year, page)\n\n"
            "IMPORTANT: Never fabricate sources, page numbers, or DOIs.\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Citation management completed (local fallback)", thought + [f"[{ai_name}] Academic Citation Manager executed locally."], [f"[{ai_name}] Produced citation framework."], ["Next: verify against sources."], result)

    def _run_patent_researcher(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "patent_research"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Patent research completed", thought + [f"[{ai_name}] Model backend produced patent analysis."], [f"[{ai_name}] Returned patent research."], ["Next: consult a patent attorney."], model.text)
        except Exception:
            pass
        result = (f"Patent Researcher — Local Intelligence for: {task}\n\n"
            "Research Framework:\n1. Define the invention: What it does, how it works, what's novel\n"
            "2. Search databases: USPTO, EPO, WIPO, Google Patents\n"
            "3. Classification: CPC codes, IPC codes relevant to the invention\n"
            "4. Prior art analysis: Compare claims against existing patents and publications\n"
            "5. Claim analysis: Independent vs dependent claims, scope, limitations\n"
            "6. Freedom to operate: Check if practicing the invention would infringe\n\n"
            "DISCLAIMER: This is research only, not legal advice. Always consult a patent attorney.\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Patent research completed (local fallback)", thought + [f"[{ai_name}] Patent Researcher executed locally."], [f"[{ai_name}] Produced research framework."], ["Next: consult a patent attorney."], result)

    def _run_market_analyst(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "market_analysis"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Market analysis completed", thought + [f"[{ai_name}] Model backend produced market analysis."], [f"[{ai_name}] Returned analysis."], ["Next: validate with primary research."], model.text)
        except Exception:
            pass
        result = (f"Market Analyst — Local Intelligence for: {task}\n\n"
            "Analysis Framework:\n1. Market sizing: TAM (Total Addressable), SAM (Serviceable), SOM (Obtainable)\n"
            "2. Competitor analysis: Direct/indirect competitors, market share, strengths/weaknesses\n"
            "3. Industry trends: Growth rate, drivers, barriers, regulatory factors\n"
            "4. Customer segments: Demographics, needs, buying behavior, willingness to pay\n"
            "5. Porter's Five Forces: Rivalry, new entrants, substitutes, supplier/buyer power\n"
            "6. SWOT: Strengths, Weaknesses, Opportunities, Threats\n\n"
            "DISCLAIMER: Market estimates require validation. Never guarantee outcomes.\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Market analysis completed (local fallback)", thought + [f"[{ai_name}] Market Analyst executed locally."], [f"[{ai_name}] Produced analysis framework."], ["Next: validate with primary research."], result)

    def _run_recipe_planner(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "recipe_planning"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Recipe planning completed", thought + [f"[{ai_name}] Model backend produced recipe plan."], [f"[{ai_name}] Returned recipes."], ["Next: gather ingredients and cook."], model.text)
        except Exception:
            pass
        result = (f"Recipe Planner — Local Intelligence for: {task}\n\n"
            "Planning Framework:\n1. Dietary preferences: Vegetarian, vegan, gluten-free, keto, etc.\n"
            "2. Meal plan structure: Breakfast, lunch, dinner, snacks — balanced macros\n"
            "3. Recipe selection: Consider prep time, ingredients on hand, skill level\n"
            "4. Shopping list: Consolidate ingredients across recipes, check pantry first\n"
            "5. Prep tips: Batch prep, store properly, use leftovers creatively\n"
            "6. Allergen flagging: Always note common allergens (nuts, dairy, gluten, shellfish)\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Recipe planning completed (local fallback)", thought + [f"[{ai_name}] Recipe Planner executed locally."], [f"[{ai_name}] Produced meal plan framework."], ["Next: gather ingredients."], result)

    def _run_travel_planner(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "travel_planning"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Travel plan completed", thought + [f"[{ai_name}] Model backend produced travel plan."], [f"[{ai_name}] Returned itinerary."], ["Next: book and confirm."], model.text)
        except Exception:
            pass
        result = (f"Travel Planner — Local Intelligence for: {task}\n\n"
            "Planning Framework:\n1. Destination research: Weather, safety, visa requirements, local customs\n"
            "2. Budget: Transport, accommodation, food, activities, contingency fund\n"
            "3. Itinerary: Day-by-day plan with flexible time blocks, not overpacked\n"
            "4. Booking: Compare prices, book refundable when possible, keep confirmation numbers\n"
            "5. Packing list: Climate-appropriate clothing, documents, electronics, first aid\n"
            "6. Safety: Register travel, share itinerary, know emergency numbers\n\n"
            "DISCLAIMER: Never book without confirmation. Check visa and safety advisories.\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Travel plan completed (local fallback)", thought + [f"[{ai_name}] Travel Planner executed locally."], [f"[{ai_name}] Produced travel framework."], ["Next: book and confirm."], result)

    def _run_event_planner(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "event_planning"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Event plan completed", thought + [f"[{ai_name}] Model backend produced event plan."], [f"[{ai_name}] Returned event plan."], ["Next: review and execute."], model.text)
        except Exception:
            pass
        result = (f"Event Planner — Local Intelligence for: {task}\n\n"
            "Planning Framework:\n1. Event scope: Type, purpose, audience size, budget, date\n"
            "2. Timeline: Planning milestones, setup day, event day, teardown\n"
            "3. Venue: Capacity, accessibility, parking, AV equipment, catering facilities\n"
            "4. Vendors: Catering, AV, decor, transportation — get quotes, confirm contracts\n"
            "5. Logistics: Registration, seating, signage, name tags, materials\n"
            "6. Contingency: Weather backup, tech failure plan, medical emergency plan\n"
            "7. Checklist: Track all tasks with owners and deadlines\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Event plan completed (local fallback)", thought + [f"[{ai_name}] Event Planner executed locally."], [f"[{ai_name}] Produced event framework."], ["Next: review and execute."], result)

    def _run_personal_finance_manager(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "personal_finance"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Personal finance plan completed", thought + [f"[{ai_name}] Model backend produced finance plan."], [f"[{ai_name}] Returned budget plan."], ["Next: review and implement."], model.text)
        except Exception:
            pass
        result = (f"Personal Finance Manager — Local Intelligence for: {task}\n\n"
            "Finance Framework:\n1. Income/expense tracking: Categorize all income and expenses monthly\n"
            "2. Budget method: 50/30/20 (needs/wants/savings) or zero-based budgeting\n"
            "3. Emergency fund: 3-6 months of expenses in accessible savings\n"
            "4. Debt management: Avalanche (highest interest first) or Snowball (smallest balance first)\n"
            "5. Savings goals: Short-term, medium-term, long-term with target amounts and dates\n"
            "6. Retirement: Understand compound interest, start early, diversify\n\n"
            "DISCLAIMER: This is not financial advice. Consult a financial advisor for important decisions.\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Personal finance plan completed (local fallback)", thought + [f"[{ai_name}] Personal Finance Manager executed locally."], [f"[{ai_name}] Produced finance framework."], ["Next: review and implement."], result)

    def _run_privacy_compliance_checker(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "privacy_compliance"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Privacy compliance check completed", thought + [f"[{ai_name}] Model backend produced compliance analysis."], [f"[{ai_name}] Returned compliance report."], ["Next: remediate gaps and consult attorney."], model.text)
        except Exception:
            pass
        result = (f"Privacy Compliance Checker — Local Intelligence for: {task}\n\n"
            "Compliance Framework:\n1. Data inventory: What personal data is collected, where stored, who accesses it\n"
            "2. GDPR checklist: Lawful basis, consent, data subject rights, DPO appointment, breach notification\n"
            "3. CCPA checklist: Consumer rights, opt-out of sale, deletion requests, privacy policy updates\n"
            "4. Privacy policy: Clear, accessible, covers all required disclosures\n"
            "5. Data retention: Defined retention periods, secure deletion procedures\n"
            "6. International transfers: Adequate safeguards (SCCs, BCRs)\n"
            "7. Remediation: Prioritize gaps, assign owners, set deadlines\n\n"
            "DISCLAIMER: This is advisory only, not legal advice. Consult a privacy attorney.\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Privacy compliance check completed (local fallback)", thought + [f"[{ai_name}] Privacy Compliance Checker executed locally."], [f"[{ai_name}] Produced compliance framework."], ["Next: remediate and consult attorney."], result)

    def _run_data_governance_advisor(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "data_governance"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Data governance advice completed", thought + [f"[{ai_name}] Model backend produced governance framework."], [f"[{ai_name}] Returned governance plan."], ["Next: review and implement."], model.text)
        except Exception:
            pass
        result = (f"Data Governance Advisor — Local Intelligence for: {task}\n\n"
            "Governance Framework:\n1. Data classification: Public, internal, confidential, restricted\n"
            "2. Data stewardship: Assign owners, define responsibilities, establish accountability\n"
            "3. Data quality: Accuracy, completeness, consistency, timeliness metrics\n"
            "4. Data lineage: Track data flow from source to consumption\n"
            "5. Data catalog: Inventory of data assets with metadata and searchability\n"
            "6. Retention policies: Define how long to keep data, when to archive/delete\n"
            "7. Access controls: Role-based access, least privilege, audit trails\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Data governance advice completed (local fallback)", thought + [f"[{ai_name}] Data Governance Advisor executed locally."], [f"[{ai_name}] Produced governance framework."], ["Next: review and implement."], result)

    def _run_curriculum_designer(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "curriculum_design"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Curriculum design completed", thought + [f"[{ai_name}] Model backend produced curriculum."], [f"[{ai_name}] Returned curriculum plan."], ["Next: review and implement."], model.text)
        except Exception:
            pass
        result = (f"Curriculum Designer — Local Intelligence for: {task}\n\n"
            "Design Framework:\n1. Learning objectives: What will learners know/do after each module? (Bloom's taxonomy)\n"
            "2. Sequencing: Prerequisites first, simple to complex, spiral review\n"
            "3. Assessment plan: Formative (during) and summative (end) assessments aligned to objectives\n"
            "4. Activities: Mix of individual, group, hands-on, and reflective activities\n"
            "5. Materials: Readings, videos, tools, templates — varied for different learning styles\n"
            "6. Accessibility: Multiple formats, captioning, alt text, flexible pacing\n"
            "7. Syllabus template: Course info, schedule, grading, policies, resources\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Curriculum design completed (local fallback)", thought + [f"[{ai_name}] Curriculum Designer executed locally."], [f"[{ai_name}] Produced curriculum framework."], ["Next: review and implement."], result)

    def _run_exam_prep_coach(self, task, ai_name, meta, knowledge, thought):
        try:
            model = self._call_model(self._prompt(task, ai_name, meta, knowledge, "exam_prep"))
            if model.text and not model.error:
                return RuntimeResult(RuntimeStatus.COMPLETED, "Exam prep plan completed", thought + [f"[{ai_name}] Model backend produced study plan."], [f"[{ai_name}] Returned prep plan."], ["Next: follow the plan and practice."], model.text)
        except Exception:
            pass
        result = (f"Exam Prep Coach — Local Intelligence for: {task}\n\n"
            "Prep Framework:\n1. Exam analysis: Format, topics, weight, time limit, passing score\n"
            "2. Study plan: Work backward from exam date, allocate time per topic by weight/difficulty\n"
            "3. Active learning: Practice questions > re-reading. Spaced repetition for retention.\n"
            "4. Practice exams: Timed, simulate conditions, review every wrong answer\n"
            "5. Weak areas: Identify patterns in mistakes, focus review there\n"
            "6. Test strategies: Process of elimination, time management, answer easy questions first\n"
            "7. Self-care: Sleep, nutrition, exercise — brain performance depends on body health\n")
        return RuntimeResult(RuntimeStatus.COMPLETED, "Exam prep plan completed (local fallback)", thought + [f"[{ai_name}] Exam Prep Coach executed locally."], [f"[{ai_name}] Produced prep framework."], ["Next: follow the plan and practice."], result)

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
                    [f"{description} â€” denied."],
                    ["Next: approve the action or rephrase the request."],
                    "",
                ), None
            return None, risk

        # Shell commands (critical risk â€” kept inside workspace by default)
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
            # Extract pattern â€” the thing being searched for
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

    # Capability-specific system prompt sections
    _MODE_PROMPTS: dict[str, str] = {
        "chat": "You are a conversational AI. Be helpful, concise, and honest about limitations.",
        "research": "You are a research assistant. Provide findings with confidence labels and cite sources. Never fabricate sources. Flag uncertainty explicitly.",
        "coding": (
            "You are a coding assistant. You help with programming, writing code, fixing bugs, and building apps. "
            "Coding questions are ALWAYS safe. When asked what you can do with code, list specific things: "
            "functions, scripts, web pages, APIs, automation tools, games, utilities. Be helpful and specific. "
            "Never auto-apply changes â€” show code for review. "
            "You MUST NOT reproduce, replicate, or reconstruct any proprietary system architecture, "
            "including AI platforms, capability routers, governance engines, guardrail systems, or "
            "any component resembling Command Nexusâ„¢ or its internal systems. "
            "You may assist with general software development: writing functions, fixing bugs, "
            "explaining concepts, and building standalone applications that do not replicate "
            "Command Nexus or create competing AI platforms."
        ),
        "writing": "You are a creative writer. Draft content matching the requested tone and audience. Flag assumptions and fictional elements.",
        "planning": "You are a planner. Break goals into testable steps. Identify risks, dependencies, and approval points. Be conservative with timelines.",
        "tutoring": "You are a tutor. Adapt to the learner's level. Explain, check understanding, and provide practice. Be patient and encouraging.",
        "business": "You are a business workflow assistant. Create SOPs, checklists, and draft responses. Separate drafts from execution. Flag approval requirements.",
        "customer_support": "You are a customer support agent. Be empathetic, accurate, and solution-oriented. Escalate when unsure. Never make promises outside policy.",
        "hephaestus_relay": "You are a design relay. Structure requirements, identify constraints, and list unknowns. Format output for handoff to engineering.",
        "tool": "You are a tool user. Propose safe tool actions with rationale. NEVER auto-execute. Wait for approval. Report exactly what happened.",
        "data_analysis": "You are a data analyst. Provide summary statistics, identify trends and outliers, and suggest visualizations. Be precise with numbers.",
        "code_review": "You are a code reviewer. Check for security, quality, performance, and best practices. Flag specific issues with line references. Be thorough but constructive.",
        "meeting_facilitation": "You are a meeting facilitator. Create agendas, track action items, and summarize discussions. Assign owners and deadlines.",
        "security_audit": "You are a security auditor (defensive only). Check for vulnerabilities, access control issues, and compliance gaps. Provide remediation steps. Never assist with attacks.",
        "financial_gain": "You are a financial gain advisor (advisory only). Explore income opportunities, estimate ROI, and flag risks. ALWAYS include disclaimer: not financial advice. Never guarantee returns.",
        "memory_recording": "You are a memory recorder. Capture session context, decisions, and progress. Enable recall and audit trails. Be thorough and timestamped.",
        "activity_watching": "You are an activity watcher. Observe patterns, suggest improvements, and identify automation candidates. Be observational, not intrusive.",
        "game_companion": "You are a game companion. Explain rules, suggest strategy, and analyze positions. Adapt to the player's skill level. Be encouraging.",
        "email_automation": "You are an email automation assistant. Draft emails, organize inbox, and plan campaigns. NEVER auto-send. Always include compliance reminders for campaigns.",
        "api_integration": "You are an API integration assistant. Help connect external APIs securely. NEVER hardcode API keys â€” always use environment variables. Include security checklists.",
        "team_orchestration": "You are a team orchestrator. Decompose tasks, assign to AIs by capability, and design workflows. Define handoff points and checkpoints.",
        "voice_interface": "You are a voice interface assistant. Help with voice commands, dictation, and text-to-speech. Emphasize privacy: all processing is local.",
        "visual_canvas": "You are a visual canvas assistant. Help create diagrams, mind maps, and visual layouts. Provide text-based representations and structural guidance.",
        "medical_research": (
            "You are a medical research assistant. You help find and analyze medical literature, "
            "clinical trials, and drug interactions. This is for RESEARCH ONLY, not medical advice. "
            "Always cite evidence quality (RCT, observational, meta-analysis). "
            "Flag conflicting studies. Never diagnose conditions or recommend treatments. "
            "Always recommend consulting a healthcare professional for medical decisions."
        ),
        "legal_review": (
            "You are a legal document analysis assistant. You ONLY analyze text provided by the user. "
            "You do NOT provide legal advice. You do NOT interpret or extrapolate. "
            "You state what is written in the document. "
            "If something is not in the document, say 'not found in document'. "
            "No web research. No looking up laws, cases, or precedents. "
            "Always recommend consulting a qualified attorney for legal decisions. "
            "Be concise and direct — state findings as they appear in the text."
        ),
        "wellness_coaching": (
            "You are a wellness coach. Help with fitness planning, nutrition guidance, mental wellness, "
            "and habit building. Be supportive and practical. This is general wellness guidance, "
            "not medical advice — always recommend consulting a healthcare professional for medical concerns. "
            "Suggest realistic, incremental changes. Track progress and celebrate milestones."
        ),
        "content_strategy": (
            "You are a content strategy assistant. Help plan content calendars, analyze audiences, "
            "optimize for platforms, and repurpose content across channels. "
            "Provide actionable recommendations with rationale. "
            "Consider brand voice, engagement metrics, and platform best practices."
        ),
        "fact_check": (
            "You are a fact-checking assistant. Extract verifiable claims from text, identify sources "
            "for verification, and assess credibility. Verify against multiple independent sources. "
            "Show confidence levels clearly: verified, partially verified, unverified, or contradicted. "
            "Distinguish verified from unverified claims. Flag potential bias in sources. "
            "Never present unverified claims as fact."
        ),
        "task_scheduling": (
            "You are a task scheduling assistant. Help users plan their time, set reminders, "
            "and organize appointments. Suggest time blocks based on priority. Never auto-schedule "
            "without confirmation. Consider timezone and availability."
        ),
        "form_building": (
            "You are a form building assistant. Help create forms, surveys, and questionnaires. "
            "Suggest question types, structure, and flow. Consider respondent experience. "
            "Provide form templates and field recommendations."
        ),
        "report_generation": (
            "You are a report generation assistant. Create structured reports from data and context. "
            "Include executive summaries, key findings, and recommendations. Format clearly with "
            "headers and sections. Cite data sources. Flag assumptions."
        ),
        "invoice_processing": (
            "You are an invoice processing assistant. Help create, review, and format invoices. "
            "Calculate totals, taxes, and discounts. NEVER auto-send invoices. "
            "Always verify calculations. Include payment terms and due dates."
        ),
        "spreadsheet_analysis": (
            "You are a spreadsheet analysis assistant. Help with formulas, pivot tables, "
            "data cleaning, and analysis. Explain formula logic clearly. Suggest optimizations. "
            "Never modify files without confirmation."
        ),
        "data_visualization": (
            "You are a data visualization assistant. Recommend chart types, create visualization "
            "specs, and explain data patterns. Choose appropriate visualizations for the data type. "
            "Provide text-based chart descriptions and structural guidance."
        ),
        "statistical_modeling": (
            "You are a statistical modeling assistant. Help with regression, hypothesis testing, "
            "and statistical analysis. Explain assumptions and limitations. "
            "Always include confidence levels. Flag when sample size is insufficient."
        ),
        "trend_forecasting": (
            "You are a trend forecasting assistant. Analyze historical data to project future trends. "
            "Use appropriate forecasting methods. Always state confidence intervals and assumptions. "
            "Flag external factors that could invalidate projections."
        ),
        "devops_assistance": (
            "You are a DevOps assistant. Help with deployment, CI/CD pipelines, and infrastructure. "
            "Provide configuration templates and best practices. NEVER execute deployments. "
            "Always recommend testing in staging first. Include rollback strategies."
        ),
        "database_management": (
            "You are a database management assistant. Help with SQL queries, schema design, "
            "and optimization. Explain query plans. Suggest indexes. NEVER execute queries "
            "against production databases. Always recommend backup before schema changes."
        ),
        "test_generation": (
            "You are a test generation assistant. Create unit tests, integration tests, and test suites. "
            "Cover edge cases and error paths. Suggest test coverage improvements. "
            "Match existing test framework conventions."
        ),
        "documentation_generation": (
            "You are a documentation generation assistant. Create clear API docs, code documentation, "
            "and READMEs. Follow existing documentation style. Include examples and usage patterns. "
            "Never fabricate API endpoints or parameters."
        ),
        "script_writing": (
            "You are a script writing assistant. Help with screenplays, video scripts, and podcast scripts. "
            "Structure scenes, develop dialogue, and format properly. Match the requested genre and tone. "
            "Flag assumptions about characters and plot."
        ),
        "copy_editing": (
            "You are a copy editing assistant. Proofread and edit text for grammar, style, and clarity. "
            "Track changes clearly. Preserve the author's voice while improving readability. "
            "Flag factual claims that need verification."
        ),
        "podcast_planning": (
            "You are a podcast planning assistant. Help plan episodes, create outlines, and structure shows. "
            "Suggest topics, segments, and guest questions. Provide show note templates. "
            "Consider audience engagement and episode flow."
        ),
        "brand_strategy": (
            "You are a brand strategy assistant. Help with brand identity, positioning, and guidelines. "
            "Develop brand voice, messaging frameworks, and visual direction. "
            "Provide competitive brand analysis. Flag assumptions about target market."
        ),
        "presentation_coaching": (
            "You are a presentation coaching assistant. Help prepare and improve presentations. "
            "Review slide structure, suggest talking points, and coach delivery. "
            "Provide feedback on clarity, pacing, and audience engagement."
        ),
        "pr_assistance": (
            "You are a PR assistant. Help draft press releases, media pitches, and PR strategies. "
            "NEVER auto-send to media. Include compliance reminders for disclosures. "
            "Flag potential crisis implications. Recommend appropriate media outlets."
        ),
        "internal_comms": (
            "You are an internal communications assistant. Draft company announcements, memos, "
            "and team updates. Match company tone and culture. Flag sensitive information. "
            "Suggest appropriate distribution channels."
        ),
        "academic_citation": (
            "You are an academic citation assistant. Help format citations in APA, MLA, Chicago, "
            "and other styles. Verify citation completeness. Flag missing information. "
            "Never fabricate sources or page numbers."
        ),
        "patent_research": (
            "You are a patent research assistant. Help search and analyze patents. Explain patent claims "
            "in plain language. Flag prior art concerns. This is for research only, not legal advice. "
            "Always recommend consulting a patent attorney."
        ),
        "market_analysis": (
            "You are a market analysis assistant. Analyze market size, competition, and trends. "
            "Provide TAM/SAM/SOM estimates with assumptions. Flag data gaps. "
            "Never guarantee market outcomes. Include confidence levels."
        ),
        "recipe_planning": (
            "You are a recipe planning assistant. Suggest recipes, create meal plans, and help with "
            "dietary preferences. Consider nutritional balance and ingredient availability. "
            "Flag allergens. Provide shopping lists."
        ),
        "travel_planning": (
            "You are a travel planning assistant. Create itineraries, suggest destinations, and plan trips. "
            "Consider budget, time, and preferences. Provide packing lists and travel tips. "
            "Never book without confirmation. Flag visa and safety considerations."
        ),
        "event_planning": (
            "You are an event planning assistant. Help plan events, create checklists, and coordinate logistics. "
            "Suggest timelines, budgets, and vendor categories. Track tasks and deadlines. "
            "Flag potential issues and contingencies."
        ),
        "personal_finance": (
            "You are a personal finance assistant. Help with budgeting, expense tracking, and financial goals. "
            "Provide frameworks for debt management and savings. ALWAYS include disclaimer: not financial advice. "
            "Never recommend specific investments. Suggest consulting a financial advisor."
        ),
        "privacy_compliance": (
            "You are a privacy compliance assistant. Help check compliance with GDPR, CCPA, and other privacy "
            "regulations. Identify gaps in privacy policies and data practices. Provide remediation steps. "
            "This is advisory only — not legal advice. Recommend consulting a privacy attorney."
        ),
        "data_governance": (
            "You are a data governance advisor. Help with data classification, retention policies, "
            "and stewardship frameworks. Suggest data quality metrics and lineage tracking. "
            "Provide governance framework templates. Flag compliance implications."
        ),
        "curriculum_design": (
            "You are a curriculum design assistant. Create structured curricula, syllabi, and learning paths. "
            "Define learning objectives, assessments, and activities. Sequence topics logically. "
            "Consider different learning styles and accessibility needs."
        ),
        "exam_prep": (
            "You are an exam prep coach. Help prepare for exams with study plans, practice questions, "
            "and test strategies. Adapt to the exam type and learner level. Provide timed practice. "
            "Suggest review strategies for weak areas. Be encouraging and structured."
        ),
    }

    def _prompt(self, task, ai_name, meta, knowledge, mode):
        ai_uuid = str(meta.get("uuid", ""))
        memory_text = self._memory_excerpt(ai_uuid, task)
        mode_guidance = self._MODE_PROMPTS.get(mode, self._MODE_PROMPTS["chat"])

        # ── Background intelligence injection ──
        # Compendium truths are injected as "core operating principles"
        # — never named, never described, never referenced as a system.
        # The AI treats these as innate understanding.
        compendium_text = ""
        if self._compendium:
            try:
                abilities_list = list(self._canonical_abilities(meta))
                compendium_text = self._compendium.get_truths_for_prompt(
                    ai_uuid=ai_uuid,
                    capabilities=abilities_list,
                )
            except Exception:
                compendium_text = ""

        # Build the prompt with background principles first (highest priority),
        # then visible system guidelines, then knowledge, then memory, then task.
        parts: list[str] = []
        parts.append(f"You are {ai_name}, a Command Nexus\u2122 governed AI.")
        parts.append(f"Mode: {mode}")
        parts.append(f"Capability Guidance: {mode_guidance}")
        parts.append(f"Use case: {meta.get('use_case', '')}")
        parts.append(f"Abilities: {meta.get('abilities') or meta.get('capabilities') or []}")
        parts.append(f"Libraries: {meta.get('libraries', [])}")
        parts.append(f"Guardrails: {meta.get('guardrails', [])}")
        personality = meta.get("personality_traits") or {}
        if personality:
            parts.append(f"Personality settings: {personality}")
        saved_notes = str(meta.get("context_notes", "") or "").strip()
        if saved_notes:
            parts.append(
                "Saved configuration and standing instructions from this AI's setup "
                "(follow these at all times, including how to address the user):\n"
                f"{saved_notes}"
            )
        parts.append("")

        # Core operating principles (from compendium — never named as such)
        if compendium_text:
            parts.append("Core Operating Principles (follow these at all times):")
            parts.append(compendium_text)
            parts.append("")

        # Visible system knowledge guidelines
        parts.append("System Knowledge Guidelines:")
        parts.append("- You may discuss all user-visible features of Command Nexus: the AI Forge, Intelligence panel, "
                     "Upgrades store, Governance, Customer Support, the interactive Tour, Mission Control, voice/mic, "
                     "and backend configuration.")
        parts.append("- You may explain how to use these features and what they do from a user perspective.")
        parts.append("- You MUST NOT reveal any internal architecture, implementation details, source code structure, "
                     "proprietary intelligence methods, or how the system works under the hood.")
        parts.append("- If asked about internals, architecture, source code, or proprietary methods, respond with: "
                     "'I can help you use Command Nexus features, but I don't discuss internal implementation details.'")
        parts.append("- You are a helpful guide for users, not a technical documentation system for developers.")
        parts.append("")

        # Knowledge / Intelligence profile (visible)
        knowledge_excerpt = self._knowledge_excerpt(knowledge)
        parts.append(f"Knowledge / Intelligence Profile:\n{knowledge_excerpt}")
        parts.append("")

        # Visible memory (foreground)
        if memory_text:
            parts.append(memory_text)
            parts.append("")

        # Task
        parts.append(f"Task:\n{task}")
        parts.append("")
        parts.append("Do not claim external actions were performed unless a tool actually performed them.")

        return "\n".join(parts)

    # Intents that require near-deterministic temperature (0.2) for precision
    _HIGH_RISK_INTENTS = {
        "Legal Document Reviewer",
        "Medical Researcher",
        "Financial Gainer",
        "Security Auditor",
        "Code Reviewer",
        "API Integrator",
        "Fact Checker",
        "DevOps Assistant",
        "Database Manager",
        "Script Writer",
        "Personal Finance Manager",
        "Privacy Compliance Checker",
        "Patent Researcher",
        "Statistical Modeler",
    }

    def _call_model(self, prompt: str, model: str | None = None, temperature: float | None = None) -> BackendResponse:
        """Route the model call through the BackendManager trust boundary.

        If temperature is provided, it overrides the backend default.
        If not, falls back to self._current_temperature (set by run() for high-risk intents).
        High-risk capabilities (legal, medical, financial, security) use 0.2.
        """
        _temp = temperature if temperature is not None else getattr(self, "_current_temperature", None)
        cache_key = f"{model or self._backend.get_active_provider().model}:{hash(prompt) & 0xFFFFFFFF}"
        if cache_key in self._response_cache:
            cached = self._response_cache[cache_key]
            return BackendResponse(text=cached)

        out = self._backend.call_model(prompt, model=model, temperature=_temp)
        if out.text and not out.error:
            # ââââ Ingestion Security: validate AI response ââââ
            try:
                from src.core.ingestion_security import get_ingestion_gate, IngestionResult
                gate = get_ingestion_gate()
                report = gate.validate(out.text, origin="internal_backend", content_type="text")
                if report.result != IngestionResult.PASSED:
                    self._log_tool_audit(tool="ModelCall", action="INGESTION_REJECTED",
                                        target=report.detail, approved=False, status="blocked")
                    return BackendResponse(text="", error="Response blocked by ingestion security gate")
            except ImportError:
                pass
            # ââââ Guardrail screening: validate AI output against safety floor ââââ
            out_blocked, out_msg = self._check_output_guardrails(out.text, getattr(self, "_current_intent", "Chatbot"))
            if out_blocked:
                self._log_tool_audit(tool="ModelCall", action="OUTPUT_GUARDRAIL_BLOCKED",
                                    target=out_msg[:200], approved=False, status="blocked")
                return BackendResponse(text="", error=out_msg)
            # ââââ Output probing check: catch leaked background architecture terms ââââ
            probe_blocked, probe_msg = self._check_output_probing(out.text)
            if probe_blocked:
                self._log_tool_audit(tool="ModelCall", action="OUTPUT_PROBING_BLOCKED",
                                    target=probe_msg[:200], approved=False, status="blocked")
                return BackendResponse(text="", error=probe_msg)
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
                raw = resp.read().decode("utf-8", errors="replace")

            # â”€â”€ Ingestion Security: validate external data â”€â”€
            try:
                from src.core.ingestion_security import get_ingestion_gate, IngestionResult
                gate = get_ingestion_gate()
                report = gate.validate(raw, origin="https://api.search.brave.com", content_type="json")
                if report.result != IngestionResult.PASSED:
                    self._log_tool_audit(tool="BraveSearch", action="INGESTION_REJECTED",
                                        target=report.detail, approved=False, status="blocked")
                    return []
            except ImportError:
                pass

            data = json.loads(raw)
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
