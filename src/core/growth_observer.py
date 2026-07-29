# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

"""
Growth Observer — Learns from user behavior to improve AI responses over time.

This module observes what the user does within the Command Nexus console:
- Which capabilities they use most frequently
- What types of missions they give their AIs
- Which features they explore (Forge, Intelligence, Models, etc.)
- Time-of-day usage patterns
- Preferred AI personality settings
- Common task patterns and workflows

The learned patterns are stored locally and used to:
1. Suggest relevant capabilities the user hasn't tried yet
2. Pre-fill mission templates based on past usage
3. Adjust AI personality defaults to match user preferences
4. Recommend workflows that combine capabilities the user already uses
5. Provide a "growth profile" showing how the user's usage has evolved

PRIVACY: All observations are stored locally. Nothing is sent to external servers.
The feature is ON by default but can be toggled off in settings.

The observer integrates with:
- AdaptiveMemoryStore (stores growth patterns as tagged memories)
- SettingsManager (persists the enabled/disabled toggle)
- NexusAIRuntime (feeds growth context into prompts)
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from collections import Counter


@dataclass
class UsageEvent:
    """A single observed user action."""
    event_type: str          # "mission", "capability_used", "feature_opened", "ai_created", "model_changed"
    detail: str              # What specifically happened
    ai_name: str = ""        # Which AI was involved (if any)
    timestamp: float = 0.0
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()


@dataclass
class GrowthProfile:
    """Aggregated learning profile for a user."""
    # Capability usage frequency
    capability_counts: dict = field(default_factory=dict)
    # Feature visit frequency
    feature_counts: dict = field(default_factory=dict)
    # Mission type patterns (categorized by intent)
    mission_type_counts: dict = field(default_factory=dict)
    # Time-of-day usage histogram (hour -> count)
    hour_histogram: dict = field(default_factory=dict)
    # AI personality preferences observed
    personality_preferences: dict = field(default_factory=dict)
    # Common task keywords (top words used in missions)
    task_keywords: list = field(default_factory=list)
    # Workflow patterns (sequences of capabilities used together)
    workflow_patterns: list = field(default_factory=list)
    # Total events observed
    total_events: int = 0
    # First seen / last seen
    first_seen: str = ""
    last_seen: str = ""
    # Growth level (0-5 based on breadth of usage)
    growth_level: int = 0

    def to_dict(self) -> dict:
        return {
            "capability_counts": self.capability_counts,
            "feature_counts": self.feature_counts,
            "mission_type_counts": self.mission_type_counts,
            "hour_histogram": self.hour_histogram,
            "personality_preferences": self.personality_preferences,
            "task_keywords": self.task_keywords,
            "workflow_patterns": self.workflow_patterns,
            "total_events": self.total_events,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "growth_level": self.growth_level,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GrowthProfile":
        return cls(
            capability_counts=data.get("capability_counts", {}),
            feature_counts=data.get("feature_counts", {}),
            mission_type_counts=data.get("mission_type_counts", {}),
            hour_histogram=data.get("hour_histogram", {}),
            personality_preferences=data.get("personality_preferences", {}),
            task_keywords=data.get("task_keywords", []),
            workflow_patterns=data.get("workflow_patterns", []),
            total_events=data.get("total_events", 0),
            first_seen=data.get("first_seen", ""),
            last_seen=data.get("last_seen", ""),
            growth_level=data.get("growth_level", 0),
        )


class GrowthObserver:
    """
    Observes user behavior and builds a growth profile over time.

    Usage:
        observer = GrowthObserver(settings_manager)
        observer.record_event("mission", "Plan my day", ai_name="Lily")
        observer.record_event("feature_opened", "AI Forge")
        profile = observer.get_profile()
        suggestions = observer.get_suggestions()
    """

    _instance: Optional["GrowthObserver"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, settings_manager=None):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True
        self._settings = settings_manager
        self._events: list[UsageEvent] = []
        self._profile: GrowthProfile = GrowthProfile()
        self._enabled = True
        self._max_events = 500  # Keep last 500 events in memory
        self._recent_capabilities: list[str] = []  # Track workflow sequences
        self._load()

    def _get_data_path(self) -> Path:
        """Get the path for the growth profile data file."""
        base = Path.home() / ".command_nexus"
        base.mkdir(parents=True, exist_ok=True)
        return base / "growth_profile.json"

    def _load(self):
        """Load the growth profile from disk."""
        # Check if growth observation is enabled in settings
        if self._settings:
            try:
                s = self._settings.get()
                self._enabled = getattr(s, "growth_observer_enabled", True)
            except Exception:
                self._enabled = True

        path = self._get_data_path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self._profile = GrowthProfile.from_dict(data)
            except Exception:
                self._profile = GrowthProfile()

    def _save(self):
        """Save the growth profile to disk."""
        if not self._enabled:
            return
        try:
            path = self._get_data_path()
            path.write_text(
                json.dumps(self._profile.to_dict(), indent=2),
                encoding="utf-8"
            )
        except Exception:
            pass

    def is_enabled(self) -> bool:
        """Check if growth observation is enabled."""
        return self._enabled

    def set_enabled(self, enabled: bool):
        """Enable or disable growth observation."""
        self._enabled = enabled
        if self._settings:
            try:
                self._settings.update(growth_observer_enabled=enabled)
            except Exception:
                pass
        if enabled:
            self._save()
        # Always save the toggle state

    def record_event(self, event_type: str, detail: str, ai_name: str = "", **metadata):
        """Record a user action event.

        Args:
            event_type: Type of event ("mission", "capability_used", "feature_opened",
                        "ai_created", "model_changed", "personality_changed")
            detail: What specifically happened
            ai_name: Which AI was involved (optional)
            **metadata: Additional context about the event
        """
        if not self._enabled:
            return

        event = UsageEvent(
            event_type=event_type,
            detail=detail,
            ai_name=ai_name,
            metadata=metadata,
        )
        self._events.append(event)

        # Trim event history
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]

        # Update profile based on event type
        now = datetime.now(timezone.utc)
        hour = str(now.hour)

        if not self._profile.first_seen:
            self._profile.first_seen = now.isoformat()
        self._profile.last_seen = now.isoformat()
        self._profile.total_events += 1

        # Update hour histogram
        self._profile.hour_histogram[hour] = self._profile.hour_histogram.get(hour, 0) + 1

        if event_type == "capability_used":
            cap = detail.strip()
            self._profile.capability_counts[cap] = self._profile.capability_counts.get(cap, 0) + 1
            # Track workflow patterns (sequences of 2-3 capabilities)
            self._recent_capabilities.append(cap)
            if len(self._recent_capabilities) >= 2:
                workflow = " -> ".join(self._recent_capabilities[-3:])
                if workflow not in self._profile.workflow_patterns:
                    self._profile.workflow_patterns.append(workflow)
                    # Keep only last 20 patterns
                    self._profile.workflow_patterns = self._profile.workflow_patterns[-20:]

        elif event_type == "feature_opened":
            feature = detail.strip()
            self._profile.feature_counts[feature] = self._profile.feature_counts.get(feature, 0) + 1

        elif event_type == "mission":
            # Categorize mission type
            mission_type = self._categorize_mission(detail)
            self._profile.mission_type_counts[mission_type] = \
                self._profile.mission_type_counts.get(mission_type, 0) + 1
            # Extract keywords
            keywords = self._extract_keywords(detail)
            for kw in keywords:
                if kw not in self._profile.task_keywords:
                    self._profile.task_keywords.append(kw)
            # Keep only top 50 keywords
            self._profile.task_keywords = self._profile.task_keywords[-50:]

        elif event_type == "personality_changed":
            self._profile.personality_preferences.update(metadata)

        # Update growth level
        self._update_growth_level()

        # Save periodically (every 10 events)
        if self._profile.total_events % 10 == 0:
            self._save()

    def _categorize_mission(self, task: str) -> str:
        """Categorize a mission into a type based on keywords."""
        lower = task.lower()
        categories = {
            "planning": ["plan", "schedule", "organize", "calendar", "todo", "to-do", "task list"],
            "writing": ["write", "draft", "compose", "create", "story", "poem", "essay", "article", "blog"],
            "research": ["research", "search", "find", "look up", "investigate", "analyze", "compare"],
            "coding": ["code", "program", "function", "bug", "debug", "script", "api", "database"],
            "analysis": ["analyze", "summarize", "review", "evaluate", "assess", "report", "data"],
            "learning": ["explain", "teach", "learn", "understand", "how does", "what is", "tutorial"],
            "communication": ["email", "message", "letter", "response", "reply", "communicate"],
            "business": ["business", "marketing", "sales", "customer", "sop", "workflow", "process"],
            "creative": ["creative", "design", "idea", "brainstorm", "imagine", "invent"],
            "personal": ["personal", "my day", "my week", "help me", "remind"],
        }
        for category, keywords in categories.items():
            if any(kw in lower for kw in keywords):
                return category
        return "general"

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract meaningful keywords from a task string."""
        # Remove common stop words
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "must", "can", "need", "to", "for", "with",
            "about", "into", "from", "and", "or", "but", "not", "no", "yes",
            "me", "my", "we", "our", "you", "your", "it", "its", "this", "that",
            "these", "those", "i", "of", "in", "on", "at", "by", "as",
        }
        words = []
        for word in text.lower().split():
            # Clean punctuation
            clean = word.strip(".,!?;:\"'()[]{}")
            if len(clean) > 3 and clean not in stop_words:
                words.append(clean)
        return words[:5]  # Top 5 keywords

    def _update_growth_level(self):
        """Update the growth level (0-5) based on usage breadth."""
        caps_used = len(self._profile.capability_counts)
        features_visited = len(self._profile.feature_counts)
        mission_types = len(self._profile.mission_type_counts)
        total = self._profile.total_events

        # Level 0: New user (< 5 events)
        # Level 1: Getting started (5+ events, 1+ capability)
        # Level 2: Exploring (10+ events, 2+ capabilities, 2+ features)
        # Level 3: Active user (25+ events, 3+ capabilities, 3+ features)
        # Level 4: Power user (50+ events, 5+ capabilities, 5+ features)
        # Level 5: Expert (100+ events, 7+ capabilities, 7+ features, 5+ mission types)
        if total >= 100 and caps_used >= 7 and features_visited >= 7 and mission_types >= 5:
            self._profile.growth_level = 5
        elif total >= 50 and caps_used >= 5 and features_visited >= 5:
            self._profile.growth_level = 4
        elif total >= 25 and caps_used >= 3 and features_visited >= 3:
            self._profile.growth_level = 3
        elif total >= 10 and caps_used >= 2 and features_visited >= 2:
            self._profile.growth_level = 2
        elif total >= 5 and caps_used >= 1:
            self._profile.growth_level = 1
        else:
            self._profile.growth_level = 0

    def get_profile(self) -> GrowthProfile:
        """Get the current growth profile."""
        return self._profile

    def get_suggestions(self) -> list[str]:
        """Generate suggestions based on the user's growth profile.

        Returns a list of suggestion strings that can be shown to the user
        or fed into the AI prompt to improve responses.
        """
        if not self._enabled or self._profile.total_events < 3:
            return []

        suggestions: list[str] = []
        profile = self._profile

        # Suggest untried capabilities
        all_capabilities = [
            "Chatbot", "Coder", "Research", "Planner", "Document Processor",
            "Tutor", "Business Workflow", "Tool User", "Creative Writing",
            "Data Analyst Pro", "Code Reviewer", "Security Auditor",
            "Financial Gainer", "Email Automation", "Meeting Facilitator",
            "Memory Recorder", "Activity Watcher", "Game Companion",
            "Wellness Coach", "Content Strategist", "Fact Checker",
            "Task Scheduler", "Form Builder", "Report Generator", "Invoice Processor",
            "Spreadsheet Analyst", "Data Visualizer", "Statistical Modeler", "Trend Forecaster",
            "DevOps Assistant", "Database Manager", "Test Generator", "Documentation Generator",
            "Script Writer", "Copy Editor", "Podcast Planner", "Brand Strategist",
            "Presentation Coach", "PR Assistant", "Internal Comms Writer",
            "Academic Citation Manager", "Patent Researcher", "Market Analyst",
            "Recipe Planner", "Travel Planner", "Event Planner",
            "Personal Finance Manager", "Privacy Compliance Checker",
            "Data Governance Advisor", "Curriculum Designer", "Exam Prep Coach",
        ]
        tried = set(profile.capability_counts.keys())
        untried = [c for c in all_capabilities if c not in tried]
        if untried and len(tried) >= 2:
            # Suggest the most relevant untried capability based on mission types
            top_untried = untried[:3]
            suggestions.append(
                f"You haven't tried these capabilities yet: {', '.join(top_untried)}. "
                f"Based on your usage, they might be useful."
            )

        # Suggest workflow combinations
        if len(profile.workflow_patterns) >= 2:
            top_workflow = profile.workflow_patterns[-1]
            suggestions.append(
                f"You often use this workflow: {top_workflow}. "
                f"Consider saving it as a template for quick access."
            )

        # Suggest based on time-of-day patterns
        if profile.hour_histogram:
            peak_hour = max(profile.hour_histogram, key=profile.hour_histogram.get)
            suggestions.append(
                f"You're most active around {peak_hour}:00. "
                f"Consider scheduling recurring missions at this time."
            )

        # Suggest personality adjustments
        if profile.personality_preferences:
            creativity = profile.personality_preferences.get("creativity", 50)
            if creativity > 70:
                suggestions.append(
                    "You prefer creative AI responses. Try the Creative Writing capability for more imaginative output."
                )
            elif creativity < 30:
                suggestions.append(
                    "You prefer precise, factual responses. The Data Analyst Pro capability might be useful for you."
                )

        # Growth level feedback
        if profile.growth_level >= 3:
            suggestions.append(
                f"You're a Level {profile.growth_level} user with {profile.total_events} actions observed. "
                f"You've used {len(profile.capability_counts)} different capabilities."
            )

        return suggestions

    def get_prompt_context(self) -> str:
        """Generate context text to inject into AI prompts.

        This gives the AI awareness of the user's patterns so it can
        tailor its responses accordingly.
        """
        if not self._enabled or self._profile.total_events < 5:
            return ""

        parts: list[str] = []
        profile = self._profile

        parts.append("[User Growth Context]")
        parts.append(f"Experience level: {profile.growth_level}/5 ({profile.total_events} actions observed)")

        if profile.capability_counts:
            top_caps = sorted(profile.capability_counts.items(), key=lambda x: -x[1])[:3]
            parts.append(f"Most used capabilities: {', '.join(c for c, _ in top_caps)}")

        if profile.mission_type_counts:
            top_types = sorted(profile.mission_type_counts.items(), key=lambda x: -x[1])[:3]
            parts.append(f"Common task types: {', '.join(t for t, _ in top_types)}")

        if profile.task_keywords:
            parts.append(f"Frequent keywords: {', '.join(profile.task_keywords[-10:])}")

        if profile.personality_preferences:
            creativity = profile.personality_preferences.get("creativity", 50)
            formality = profile.personality_preferences.get("formality", 50)
            parts.append(f"Preferred style: creativity={creativity}, formality={formality}")

        return "\n".join(parts)

    def get_growth_summary(self) -> str:
        """Get a human-readable summary of the user's growth profile."""
        profile = self._profile
        lines = [
            f"Growth Level: {profile.growth_level}/5",
            f"Total Actions Observed: {profile.total_events}",
            f"Capabilities Used: {len(profile.capability_counts)}",
            f"Features Explored: {len(profile.feature_counts)}",
            f"Mission Types: {len(profile.mission_type_counts)}",
        ]
        if profile.capability_counts:
            top = sorted(profile.capability_counts.items(), key=lambda x: -x[1])[:5]
            lines.append(f"Top Capabilities: {', '.join(f'{c} ({n})' for c, n in top)}")
        if profile.feature_counts:
            top = sorted(profile.feature_counts.items(), key=lambda x: -x[1])[:5]
            lines.append(f"Top Features: {', '.join(f'{f} ({n})' for f, n in top)}")
        if profile.first_seen:
            lines.append(f"First seen: {profile.first_seen[:10]}")
        if profile.last_seen:
            lines.append(f"Last active: {profile.last_seen[:10]}")
        return "\n".join(lines)

    def reset(self):
        """Reset the growth profile (clear all learned data)."""
        self._profile = GrowthProfile()
        self._events.clear()
        self._recent_capabilities.clear()
        self._save()
