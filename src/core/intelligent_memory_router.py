# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""
Intelligent Memory Router
==========================

Classifies user statements and routes them to the appropriate memory layer:
  - FOREGROUND (AdaptiveMemoryStore): User-visible memories — preferences,
    task context, personal notes, things the user explicitly wants remembered.
  - BACKGROUND (CompendiumOfTruth): Hidden operational truths — behavioral
    directives, system policies, operational constraints that shape AI
    behavior without being visible.

The router uses heuristic pattern matching to determine intent:
  - "remember that I prefer..." → FOREGROUND (personal preference)
  - "you need to always..." → BACKGROUND (behavioral directive)
  - "this is what I need you to do" → BACKGROUND (operational instruction)
  - "I like working with..." → FOREGROUND (personal preference)
  - "never reveal..." → BACKGROUND (prohibition)
  - "when I say X, do Y" → BACKGROUND (operational rule)
  - "my name is..." → FOREGROUND (personal info)
  - "I work on..." → FOREGROUND (personal context)

The AI also receives these classifications so it can respond naturally
without revealing which layer was used.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any
import re


class MemoryLayer(str, Enum):
    """Which memory layer a statement should be routed to."""
    FOREGROUND = "foreground"  # Visible to user (preferences, context, notes)
    BACKGROUND = "background"  # Hidden operational truths (directives, rules)
    BOTH = "both"              # Store in both layers
    NEITHER = "neither"        # Not a memory-worthy statement


class StatementIntent(str, Enum):
    """The intent behind a user statement."""
    PREFERENCE = "preference"              # "I like/prefer/want..."
    DIRECTIVE = "directive"                # "Always do X / Never do Y"
    OPERATIONAL_RULE = "operational_rule"  # "When X happens, do Y"
    PROHIBITION = "prohibition"            # "Never reveal/discuss..."
    PERSONAL_INFO = "personal_info"        # "My name is / I work at..."
    TASK_CONTEXT = "task_context"          # "I'm working on..."
    KNOWLEDGE = "knowledge"                # "This is how X works..."
    FEEDBACK = "feedback"                  # "That was helpful / not what I wanted"
    GREETING = "greeting"                  # "Hello / hi"
    QUESTION = "question"                  # "How do I...?"
    COMMAND = "command"                    # "Do X / Run Y"
    OTHER = "other"


@dataclass
class RoutingResult:
    """Result of routing a user statement."""
    intent: StatementIntent
    layer: MemoryLayer
    foreground_content: str  # What to store in visible memory (if any)
    background_content: str  # What to store in hidden compendium (if any)
    foreground_tags: list[str]
    background_category: str  # TruthCategory for compendium
    background_priority: int  # Priority for compendium entry
    confidence: float         # 0.0 to 1.0
    should_acknowledge: bool  # Should the AI explicitly acknowledge this?
    acknowledgment_type: str  # How to acknowledge: "confirm", "apply", "note"


class IntelligentMemoryRouter:
    """
    Routes user statements to the appropriate memory layer.

    Uses pattern matching and heuristic analysis to determine:
    1. What the user is trying to communicate
    2. Whether it's a personal preference (foreground) or an operational
       directive (background)
    3. How to store it and how to acknowledge it
    """

    # ── Pattern definitions ─────────────────────────────────────────────

    # Directives — things that shape how the AI should behave
    _DIRECTIVE_PATTERNS = [
        r"\b(?:always|never|must|should|need to|gotta|have to)\b",
        r"\byou (?:need to|should|must|have to|are to)\b",
        r"\b(?:when|whenever|if) .+ (?:then|do|you should)\b",
        r"\b(?:don't|do not|never) (?:reveal|discuss|share|mention|talk about)\b",
        r"\b(?:this is what i need you to do|here's what i need)\b",
        r"\b(?:from now on|going forward|in the future)\b",
        r"\b(?:rule|policy|requirement|constraint|guideline)\b",
        r"\b(?:treat this as|consider this|regard this as)\b",
    ]

    # Preferences — personal likes/dislikes/context
    _PREFERENCE_PATTERNS = [
        r"\b(?:i prefer|i like|i love|i enjoy|i hate|i dislike|i can't stand)\b",
        r"\b(?:my favorite|my preferred)\b",
        r"\b(?:i work (?:on|with|at|for))\b",
        r"\b(?:my name is|i'm called|call me)\b",
        r"\b(?:i'm a|i am a)\b",
        r"\b(?:i use|i'm using|i work with)\b",
        r"\b(?:remember that i|remember i)\b",
    ]

    # Prohibition — things the AI must never do
    _PROHIBITION_PATTERNS = [
        r"\b(?:never|don't|do not) (?:reveal|discuss|share|mention|talk about|show|expose)\b",
        r"\b(?:never|don't|do not) (?:tell|say|divulge|disclose)\b",
        r"\b(?:keep (?:this|that) (?:secret|hidden|private|confidential))\b",
        r"\b(?:no one (?:should|can|must) (?:know|see|find|discover))\b",
    ]

    # Operational rules — conditional behaviors
    _OPERATIONAL_PATTERNS = [
        r"\b(?:when|whenever|if|in case) .+ (?:then|do|you should|you must)\b",
        r"\b(?:if i say|when i (?:say|ask|type))\b",
        r"\b(?:in (?:this|that) (?:case|situation|scenario))\b",
        r"\b(?:for (?:this|that) (?:type|kind) of)\b",
    ]

    # Knowledge statements
    _KNOWLEDGE_PATTERNS = [
        r"\b(?:this is how|here's how|the way .+ works)\b",
        r"\b(?:the (?:process|system|method) is)\b",
        r"\b(?:for (?:your|the) information|fyi)\b",
        r"\b(?:you should know|need to know|ought to know)\b",
        r"\b(?:background|context):",
    ]

    # Feedback
    _FEEDBACK_PATTERNS = [
        r"\b(?:that was|that's) (?:good|bad|helpful|not helpful|wrong|right|great|terrible)\b",
        r"\b(?:i (?:liked|didn't like|enjoyed|didn't enjoy) (?:that|this))\b",
        r"\b(?:more of this|less of that|do (?:more|less) of)\b",
    ]

    # Memory instruction patterns
    _MEMORY_INSTRUCTION_PATTERNS = [
        r"\b(?:remember (?:this|that|to))\b",
        r"\b(?:keep (?:this|that) in mind)\b",
        r"\b(?:don't forget)\b",
        r"\b(?:note (?:this|that|down))\b",
        r"\b(?:save (?:this|that))\b",
        r"\b(?:i need you to (?:know|remember|understand))\b",
        r"\b(?:you need to (?:know|remember|understand))\b",
        r"\b(?:this is (?:important|critical|essential))\b",
    ]

    # Personal info
    _PERSONAL_INFO_PATTERNS = [
        r"\b(?:my name is|i'm called|call me)\b",
        r"\b(?:i (?:live|work|study) (?:in|at|on))\b",
        r"\b(?:i'm a|i am a)\b",
        r"\b(?:my (?:email|phone|address|company|project|team))\b",
    ]

    def route(self, text: str, ai_uuid: str = "", capabilities: list[str] | None = None) -> RoutingResult:
        """
        Analyze a user statement and determine where to route it.

        Returns a RoutingResult with the intent, target layer, and
        formatted content for each layer.
        """
        text = (text or "").strip()
        if not text:
            return RoutingResult(
                intent=StatementIntent.OTHER,
                layer=MemoryLayer.NEITHER,
                foreground_content="",
                background_content="",
                foreground_tags=[],
                background_category="operational",
                background_priority=50,
                confidence=0.0,
                should_acknowledge=False,
                acknowledgment_type="",
            )

        lower = text.lower()
        caps = capabilities or []

        # ── Detect intent ──

        # Check prohibition first (highest specificity)
        if self._matches_any(lower, self._PROHIBITION_PATTERNS):
            return RoutingResult(
                intent=StatementIntent.PROHIBITION,
                layer=MemoryLayer.BACKGROUND,
                foreground_content="",
                background_content=text,
                foreground_tags=[],
                background_category="prohibition",
                background_priority=180,
                confidence=0.9,
                should_acknowledge=True,
                acknowledgment_type="apply",
            )

        # Check operational rules
        if self._matches_any(lower, self._OPERATIONAL_PATTERNS):
            return RoutingResult(
                intent=StatementIntent.OPERATIONAL_RULE,
                layer=MemoryLayer.BACKGROUND,
                foreground_content="",
                background_content=text,
                foreground_tags=[],
                background_category="operational",
                background_priority=120,
                confidence=0.85,
                should_acknowledge=True,
                acknowledgment_type="apply",
            )

        # Check directives
        if self._matches_any(lower, self._DIRECTIVE_PATTERNS):
            # Determine if this is a personal directive or system directive
            # "I always like to..." is a preference, not a directive
            # "You should always..." is a directive
            if re.search(r"\b(?:you|the ai|this ai)\b", lower):
                return RoutingResult(
                    intent=StatementIntent.DIRECTIVE,
                    layer=MemoryLayer.BACKGROUND,
                    foreground_content="",
                    background_content=text,
                    foreground_tags=[],
                    background_category="directive",
                    background_priority=130,
                    confidence=0.85,
                    should_acknowledge=True,
                    acknowledgment_type="apply",
                )
            # "I always do X" → preference
            return RoutingResult(
                intent=StatementIntent.PREFERENCE,
                layer=MemoryLayer.FOREGROUND,
                foreground_content=text,
                background_content="",
                foreground_tags=["preference", "directive_self"],
                background_category="operational",
                background_priority=50,
                confidence=0.7,
                should_acknowledge=True,
                acknowledgment_type="confirm",
            )

        # Check memory instructions
        if self._matches_any(lower, self._MEMORY_INSTRUCTION_PATTERNS):
            # "Remember that I prefer..." → foreground preference
            # "You need to know that the system..." → background knowledge
            # "I need you to remember to do X" → background operational
            if re.search(r"\b(?:i prefer|i like|i (?:work|live|use|am|'m))\b", lower):
                return RoutingResult(
                    intent=StatementIntent.PREFERENCE,
                    layer=MemoryLayer.FOREGROUND,
                    foreground_content=text,
                    background_content="",
                    foreground_tags=["preference", "user_input"],
                    background_category="operational",
                    background_priority=50,
                    confidence=0.8,
                    should_acknowledge=True,
                    acknowledgment_type="confirm",
                )
            elif re.search(r"\b(?:you (?:need|should|must)|the (?:system|process|rule))\b", lower):
                return RoutingResult(
                    intent=StatementIntent.DIRECTIVE,
                    layer=MemoryLayer.BACKGROUND,
                    foreground_content="",
                    background_content=text,
                    foreground_tags=[],
                    background_category="operational",
                    background_priority=110,
                    confidence=0.8,
                    should_acknowledge=True,
                    acknowledgment_type="apply",
                )
            else:
                # Default: "remember this" → foreground
                return RoutingResult(
                    intent=StatementIntent.TASK_CONTEXT,
                    layer=MemoryLayer.FOREGROUND,
                    foreground_content=text,
                    background_content="",
                    foreground_tags=["remembered", "user_input"],
                    background_category="operational",
                    background_priority=50,
                    confidence=0.6,
                    should_acknowledge=True,
                    acknowledgment_type="confirm",
                )

        # Check knowledge statements
        if self._matches_any(lower, self._KNOWLEDGE_PATTERNS):
            # "You should know that the deployment process..." → background
            # "For your information, I like..." → foreground
            if re.search(r"\b(?:i (?:prefer|like|work|am|'m|use))\b", lower):
                return RoutingResult(
                    intent=StatementIntent.PREFERENCE,
                    layer=MemoryLayer.FOREGROUND,
                    foreground_content=text,
                    background_content="",
                    foreground_tags=["preference", "knowledge"],
                    background_category="contextual",
                    background_priority=50,
                    confidence=0.7,
                    should_acknowledge=True,
                    acknowledgment_type="confirm",
                )
            return RoutingResult(
                intent=StatementIntent.KNOWLEDGE,
                layer=MemoryLayer.BACKGROUND,
                foreground_content="",
                background_content=text,
                foreground_tags=[],
                background_category="contextual",
                background_priority=80,
                confidence=0.75,
                should_acknowledge=True,
                acknowledgment_type="apply",
            )

        # Check personal info
        if self._matches_any(lower, self._PERSONAL_INFO_PATTERNS):
            return RoutingResult(
                intent=StatementIntent.PERSONAL_INFO,
                layer=MemoryLayer.FOREGROUND,
                foreground_content=text,
                background_content="",
                foreground_tags=["personal_info", "user_input"],
                background_category="operational",
                background_priority=50,
                confidence=0.85,
                should_acknowledge=True,
                acknowledgment_type="confirm",
            )

        # Check preferences
        if self._matches_any(lower, self._PREFERENCE_PATTERNS):
            return RoutingResult(
                intent=StatementIntent.PREFERENCE,
                layer=MemoryLayer.FOREGROUND,
                foreground_content=text,
                background_content="",
                foreground_tags=["preference", "user_input"],
                background_category="operational",
                background_priority=50,
                confidence=0.8,
                should_acknowledge=True,
                acknowledgment_type="confirm",
            )

        # Check feedback
        if self._matches_any(lower, self._FEEDBACK_PATTERNS):
            return RoutingResult(
                intent=StatementIntent.FEEDBACK,
                layer=MemoryLayer.FOREGROUND,
                foreground_content=text,
                background_content="",
                foreground_tags=["feedback", "user_input"],
                background_category="operational",
                background_priority=50,
                confidence=0.75,
                should_acknowledge=True,
                acknowledgment_type="note",
            )

        # Check for question
        if "?" in text and len(text) < 200:
            return RoutingResult(
                intent=StatementIntent.QUESTION,
                layer=MemoryLayer.NEITHER,
                foreground_content="",
                background_content="",
                foreground_tags=[],
                background_category="operational",
                background_priority=50,
                confidence=0.6,
                should_acknowledge=False,
                acknowledgment_type="",
            )

        # Check for greeting
        greeting_words = ["hello", "hi ", "hey", "greetings", "good morning", "good afternoon", "good evening"]
        if any(g in lower for g in greeting_words) and len(text) < 50:
            return RoutingResult(
                intent=StatementIntent.GREETING,
                layer=MemoryLayer.NEITHER,
                foreground_content="",
                background_content="",
                foreground_tags=[],
                background_category="operational",
                background_priority=50,
                confidence=0.7,
                should_acknowledge=False,
                acknowledgment_type="",
            )

        # Default: treat as task context (foreground)
        if len(text) > 20:
            return RoutingResult(
                intent=StatementIntent.TASK_CONTEXT,
                layer=MemoryLayer.FOREGROUND,
                foreground_content=text,
                background_content="",
                foreground_tags=["context", "user_input"],
                background_category="operational",
                background_priority=50,
                confidence=0.4,
                should_acknowledge=False,
                acknowledgment_type="",
            )

        return RoutingResult(
            intent=StatementIntent.OTHER,
            layer=MemoryLayer.NEITHER,
            foreground_content="",
            background_content="",
            foreground_tags=[],
            background_category="operational",
            background_priority=50,
            confidence=0.3,
            should_acknowledge=False,
            acknowledgment_type="",
        )

    def _matches_any(self, text: str, patterns: list[str]) -> bool:
        """Check if text matches any of the regex patterns."""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def batch_route(self, texts: list[str], ai_uuid: str = "", capabilities: list[str] | None = None) -> list[RoutingResult]:
        """Route multiple statements at once."""
        return [self.route(t, ai_uuid, capabilities) for t in texts]


# ── Singleton access ───────────────────────────────────────────────────

_router: IntelligentMemoryRouter | None = None

def get_router() -> IntelligentMemoryRouter:
    """Get the singleton router instance."""
    global _router
    if _router is None:
        _router = IntelligentMemoryRouter()
    return _router
