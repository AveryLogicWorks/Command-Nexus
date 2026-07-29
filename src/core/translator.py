from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class TranslationResult:
    ok: bool
    payload: Dict[str, Any]
    message: str = ""


_ACTION_VERBS = [
    "create", "generate", "build", "make", "write", "draft",
    "analyze", "review", "check", "audit", "inspect", "examine",
    "research", "investigate", "find", "search", "look up",
    "summarize", "condense", "simplify",
    "translate", "convert", "transform",
    "plan", "schedule", "organize", "arrange",
    "test", "debug", "fix", "repair", "patch",
    "explain", "describe", "teach", "tutor",
    "compare", "evaluate", "assess", "score",
    "deploy", "publish", "send", "export", "import",
    "monitor", "watch", "track", "observe",
    "encrypt", "decrypt", "secure", "harden",
    "calculate", "compute", "estimate",
]

_CAPABILITY_KEYWORDS: dict[str, list[str]] = {
    "Coder": ["code", "function", "bug", "debug", "program", "script", "api", "class", "method", "compile", "syntax", "refactor", "diff", "patch"],
    "Research": ["research", "study", "investigate", "fact", "source", "compare", "market", "trend", "analyze data"],
    "Creative Writing": ["write", "story", "article", "blog", "essay", "poem", "content", "copy", "novel", "draft", "outline", "revise"],
    "Planner": ["plan", "schedule", "timeline", "milestone", "task", "project", "goal", "roadmap", "gantt"],
    "Document Processor": ["document", "pdf", "summarize", "extract", "action item", "meeting notes", "report"],
    "Notebook": ["note", "journal", "diary", "remember", "recall", "tag"],
    "Archive": ["archive", "store", "artifact", "preserve", "retrieve"],
    "Tutor": ["teach", "learn", "quiz", "lesson", "study", "explain", "tutor", "course"],
    "Business Workflow": ["sop", "checklist", "workflow", "handoff", "automation", "business", "process", "support draft"],
    "Tool User": ["tool", "run", "execute", "invoke", "command", "script", "deploy", "git"],
    "Chatbot": ["chat", "talk", "converse", "ask", "answer", "question", "help"],
    "Data Analyst Pro": ["data", "chart", "graph", "statistics", "csv", "spreadsheet", "analytics", "visualization"],
    "Code Reviewer": ["review", "code review", "pr review", "pull request", "lint", "quality"],
    "Meeting Facilitator": ["meeting", "agenda", "facilitate", "minutes", "standup", "retrospective"],
    "Security Auditor": ["security", "vulnerability", "audit", "pen test", "harden", "threat", "risk scan"],
    "Financial Gainer": ["income", "money", "earn", "monetize", "side hustle", "freelance", "passive income", "invest"],
    "Email Automation": ["email", "inbox", "reply", "filter", "sift"],
    "Translation Expert": ["translate", "translation", "language", "localize", "i18n"],
}

_APPROVAL_REQUIRED = [
    "deploy", "publish", "send", "export", "execute", "run", "invoke",
    "delete", "remove", "wipe", "purge", "encrypt", "decrypt",
]


class NexusIntentTranslator:
    """Translates approved human intent text into a structured payload.

    Uses BackendManager for NLU-style parsing when available, with a
    rule-based fallback that extracts action, target, capability mapping,
    parameters, confidence, and approval requirements.
    """

    @staticmethod
    def translate(intent_text: str) -> TranslationResult:
        if not intent_text.strip():
            return TranslationResult(ok=False, payload={}, message="Empty intent")

        text = intent_text.strip()
        rule_payload = NexusIntentTranslator._rule_based_parse(text)

        backend_payload = NexusIntentTranslator._backend_parse(text)
        if backend_payload:
            payload = backend_payload
            payload["rule_based_fallback"] = rule_payload
            payload["engine"] = "backend"
        else:
            payload = rule_payload
            payload["engine"] = "rule_based"

        return TranslationResult(ok=True, payload=payload, message="")

    @staticmethod
    def _rule_based_parse(text: str) -> Dict[str, Any]:
        text_lower = text.lower()

        action = "unknown"
        for verb in _ACTION_VERBS:
            if re.search(r'\b' + re.escape(verb) + r'\b', text_lower):
                action = verb
                break

        capability = "Chatbot"
        best_score = 0
        for cap, keywords in _CAPABILITY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > best_score:
                best_score = score
                capability = cap

        requires_approval = any(verb in text_lower for verb in _APPROVAL_REQUIRED)

        target = ""
        for prep in ["for ", "about ", "on ", "regarding ", "to "]:
            idx = text_lower.find(prep)
            if idx >= 0:
                target_candidate = text[idx + len(prep):].strip()
                if target_candidate and len(target_candidate) < 200:
                    target = target_candidate
                    break

        if not target:
            words = text.split()
            if len(words) > 1:
                verb_idx = -1
                for i, w in enumerate(words):
                    if w.lower() in _ACTION_VERBS:
                        verb_idx = i
                        break
                if verb_idx >= 0 and verb_idx + 1 < len(words):
                    target = " ".join(words[verb_idx + 1:])

        confidence = "High" if best_score >= 3 else "Medium" if best_score >= 1 else "Low"

        params: Dict[str, Any] = {}
        param_patterns = [
            (r'in (\w+)', "language"),
            (r'using (\w+)', "tool"),
            (r'with (\w+)', "method"),
            (r'to (\w+)', "destination"),
            (r'from (\w+)', "source"),
            (r'by (\w+)', "approach"),
        ]
        for pattern, key in param_patterns:
            m = re.search(pattern, text_lower)
            if m:
                params[key] = m.group(1)

        return {
            "raw_text": text,
            "action": action,
            "target": target,
            "capability": capability,
            "parameters": params,
            "confidence": confidence,
            "requires_approval": requires_approval,
            "keyword_matches": best_score,
        }

    @staticmethod
    def _backend_parse(text: str) -> Optional[Dict[str, Any]]:
        try:
            from .settings_manager import SettingsManager
            from .backend_manager import BackendManager

            settings = SettingsManager()
            settings.initialize()
            backend = BackendManager(settings)

            system_prompt = (
                "You are an intent translation engine. Parse the user's intent text and return a JSON object with these fields:\n"
                '{"action": "verb", "target": "object of the action", "capability": "one of the canonical capabilities", '
                '"parameters": {}, "confidence": "High|Medium|Low", "requires_approval": true|false}\n\n'
                "Canonical capabilities: Coder, Research, Creative Writing, Planner, Document Processor, Notebook, "
                "Archive, Tutor, Business Workflow, Tool User, Chatbot, Data Analyst Pro, Code Reviewer, "
                "Meeting Facilitator, Security Auditor, Financial Gainer, Email Automation, Translation Expert.\n"
                "requires_approval is true if the action would modify files, send messages, deploy, execute commands, "
                "or otherwise affect external systems.\n"
                "Return ONLY the JSON object, no other text."
            )
            response = backend.call_model(f"{system_prompt}\n\nUser intent:\n{text}", temperature=0.1)
            if response.error or not response.text:
                return None

            import json
            raw = response.text.strip()
            if raw.startswith("```"):
                raw = re.sub(r'^```(?:json)?\s*', '', raw)
                raw = re.sub(r'\s*```$', '', raw)
            parsed = json.loads(raw)
            parsed["raw_text"] = text
            return parsed
        except Exception:
            return None
