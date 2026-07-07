"""Shared capability honesty registry for Command Nexus.

Maps every visible Forge capability to:
- its canonical runtime intent
- whether it is fully wired (real), local-only/partial, or honestly paused
- what backend or option it needs

This keeps the runtime, the Forge, and the tutorial in sync so no capability
can pretend to be finished when it is not.
"""
from __future__ import annotations

# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

from enum import Enum


class ImplementationStatus(str, Enum):
    REAL = "real"           # Wired through the runtime/tool loop; executes locally
    PARTIAL = "partial"     # Local scaffold/fallback works; full output needs model/API
    PAUSED = "paused"       # Not implemented in this build; returns an honest pause


# Canonical runtime intents that the NexusAIRuntime dispatches on.
RUNTIME_INTENTS = {
    "Chatbot",
    "Research",
    "Coder",
    "Creative Writing",
    "Planner",
    "Document Processor",
    "Notebook",
    "Archive",
    "Tutor",
    "Business Workflow",
    "Tool User",
    "Customer Support AI",
    "Data Analyst Pro",
    "Code Reviewer",
    "Meeting Facilitator",
    "Security Auditor",
    # Phase 3-4 capabilities
    "Activity Watcher",
    "Financial Gainer",
    "Memory Recorder",
    "Game Companion",
    # Phase 5 capabilities
    "Email Automation",
    "API Integrator",
    "Team Orchestrator",
    "Voice Interface",
    "Visual Canvas",
}


# Map every user-facing Forge capability name to its canonical runtime intent.
CAPABILITY_ALIASES: dict[str, str] = {
    # Chat
    "Chat Companion": "Chatbot",
    "Chat": "Chatbot",
    "Customer Support Agent": "Chatbot",
    "Customer Support AI": "Customer Support AI",
    "Email Sifter & Responder": "Chatbot",

    # Research
    "Research Assistant": "Research",
    "Academic Researcher": "Research",
    "Business Intelligence Analyst": "Research",
    "Smart Search": "Research",
    "Fact Checker": "Research",

    # Coder
    "Coding Assistant": "Coder",
    "IT Operations Agent": "Coder",
    "Code Reviewer": "Coder",

    # Creative Writing
    "Creative Writer": "Creative Writing",
    "Marketing Generator": "Creative Writing",
    "Author": "Creative Writing",

    # Notebook
    "Personal Organizer": "Notebook",
    "Meeting Scribe": "Notebook",
    "Memory": "Notebook",
    "Notebook": "Notebook",
    "Knowledge": "Notebook",
    "Notes": "Notebook",

    # Planner
    "Task / Project Manager": "Planner",
    "Strategic Planner": "Planner",
    "Workflow Automator": "Planner",
    "Calendar Manager": "Planner",
    "Meeting Facilitator": "Planner",
    "Task / Project Manager": "Planner",

    # Document Processor
    "Document Processor": "Document Processor",
    "Document Generator": "Document Processor",
    "Data Entry Agent": "Document Processor",
    "Data Analyst Pro": "Document Processor",
    "Content Moderator": "Document Processor",

    # Archive
    "Archive": "Archive",
    "Memory Bridge": "Archive",
    "Knowledge Base Builder": "Archive",

    # Tutor
    "Learning Tutor": "Tutor",
    "Classroom Tutor": "Tutor",
    "Assignment Grader": "Tutor",
    "Lesson Planner": "Tutor",
    "Language Coach": "Tutor",
    "Accessibility Aide": "Tutor",
    "Learning Path Creator": "Tutor",
    "Translation Expert": "Tutor",
    "Accessibility Assistant": "Tutor",

    # Business Workflow
    "Sales Assistant": "Business Workflow",
    "Financial Analyst": "Business Workflow",
    "HR Assistant": "Business Workflow",
    "Compliance Auditor": "Business Workflow",
    "Supply Chain Coordinator": "Business Workflow",
    "Legal Document Reviewer": "Business Workflow",
    "Multi-Department Orchestrator": "Business Workflow",
    "Content Moderator": "Business Workflow",
    "Field Analyst": "Business Workflow",
    "Command Support": "Business Workflow",
    "Logistics Coordinator": "Business Workflow",
    "Tactical Advisor": "Business Workflow",
    "Medical Researcher": "Business Workflow",

    # Tool User
    "Tool User": "Tool User",
    "Agent": "Tool User",

    # Hephaestus Relay
    "Hephaestus Relay": "Hephaestus Relay",

    # Vision & Voice
    "Vision": "Visual Canvas",
    "Visibility": "Visual Canvas",
    "Visual Canvas": "Visual Canvas",
    "Voice Interface": "Voice Interface",
    "Voice": "Voice Interface",

    # Premium upgrade capabilities — mapped to canonical intents
    "Data Analyst Pro": "Data Analyst Pro",
    "Code Reviewer": "Code Reviewer",
    "Meeting Facilitator": "Meeting Facilitator",
    "Security Auditor": "Security Auditor",

    # Browser/Network/External
    "Browser Automation": "Browser",
    "Email Automation": "Email Automation",
    "API Integrator": "API Integrator",
    "Team Orchestrator": "Team Orchestrator",
    "Competitive Analyst": "Research",
    "Spreadsheet Wizard": "Document Processor",
    "Presentation Builder": "Creative Writing",

    # Activity Watcher — watches user work, learns tasks, suggests improvements
    "Activity Watcher": "Activity Watcher",
    "Task Mimic": "Activity Watcher",
    "Workflow Learner": "Activity Watcher",
    "Activity Monitor": "Activity Watcher",
    "Task Recorder": "Activity Watcher",

    # Financial Gainer — helps individuals explore money-making opportunities
    "Financial Gainer": "Financial Gainer",
    "Money Maker": "Financial Gainer",
    "Income Builder": "Financial Gainer",
    "Side Hustle Advisor": "Financial Gainer",
    "Monetization Assistant": "Financial Gainer",
    # Financial Gainer sub-capabilities
    "Crypto Scout": "Research",
    "Crypto Analyst": "Research",
    "Token Scout": "Research",
    "Affiliate Strategist": "Business Workflow",
    "Affiliate Planner": "Business Workflow",
    "Click Commission Tracker": "Data Analyst Pro",
    "Commission Tracker": "Data Analyst Pro",
    "Sales Funnel Builder": "Business Workflow",
    "Funnel Builder": "Business Workflow",
    "Side Hustle Scout": "Research",
    "Gig Finder": "Research",
    "Skill Monetizer": "Business Workflow",
    "Skill Profit Analyzer": "Business Workflow",
    "Investment Researcher": "Research",
    "Investment Scout": "Research",
    "ROI Calculator": "Data Analyst Pro",
    "ROI Tool": "Data Analyst Pro",
    "Market Gap Finder": "Research",
    "Opportunity Finder": "Research",
    "Negotiation Coach": "Chatbot",
    "Negotiation Assistant": "Chatbot",

    # Memory Recorder — records everything for auditability and recollection
    "Memory Recorder": "Memory Recorder",
    "Session Recorder": "Memory Recorder",
    "Activity Log": "Memory Recorder",
    "Audit Trail": "Memory Recorder",
    "Work Journal": "Memory Recorder",
    # Memory Saver sub-capabilities
    "Session Replay": "Memory Recorder",
    "Session Player": "Memory Recorder",
    "Smart Recall": "Archive",
    "Memory Search": "Archive",
    "Decision Tracker": "Notebook",
    "Decision Log": "Notebook",
    "Knowledge Archive": "Archive",
    "Knowledge Vault": "Archive",
    "Habit Tracker": "Notebook",
    "Habit Logger": "Notebook",
    "Progress Journal": "Notebook",
    "Progress Tracker": "Notebook",
    "Context Keeper": "Archive",
    "Context Saver": "Archive",
    "Audit Trail Builder": "Archive",
    "Compliance Trail Builder": "Archive",

    # Game Companion — learn and play games for individual use
    "Game Companion": "Game Companion",
    "Game Learner": "Game Companion",
    "Game Player": "Game Companion",
    "Strategy Gamer": "Game Companion",
}


# Status of each canonical runtime intent.
CAPABILITY_STATUS: dict[str, ImplementationStatus] = {
    # Real: executes through the runtime / tool loop without pretending
    "Chatbot": ImplementationStatus.REAL,
    "Document Processor": ImplementationStatus.REAL,
    "Notebook": ImplementationStatus.REAL,
    "Archive": ImplementationStatus.REAL,
    "Tool User": ImplementationStatus.REAL,
    "Customer Support AI": ImplementationStatus.REAL,
    "Memory Recorder": ImplementationStatus.REAL,

    # Partial: local scaffold works with full dialog UI; full quality needs a model or optional API
    "Research": ImplementationStatus.PARTIAL,
    "Coder": ImplementationStatus.PARTIAL,
    "Creative Writing": ImplementationStatus.PARTIAL,
    "Planner": ImplementationStatus.PARTIAL,
    "Tutor": ImplementationStatus.PARTIAL,
    "Business Workflow": ImplementationStatus.PARTIAL,
    "Data Analyst Pro": ImplementationStatus.PARTIAL,
    "Code Reviewer": ImplementationStatus.PARTIAL,
    "Meeting Facilitator": ImplementationStatus.PARTIAL,
    "Security Auditor": ImplementationStatus.PARTIAL,
    "Activity Watcher": ImplementationStatus.PARTIAL,
    "Financial Gainer": ImplementationStatus.PARTIAL,
    "Game Companion": ImplementationStatus.PARTIAL,
    "Email Automation": ImplementationStatus.PARTIAL,
    "API Integrator": ImplementationStatus.PARTIAL,
    "Team Orchestrator": ImplementationStatus.PARTIAL,
    "Voice Interface": ImplementationStatus.PARTIAL,
    "Visual Canvas": ImplementationStatus.PARTIAL,

    # Paused: not wired in this build
    "Hephaestus Relay": ImplementationStatus.PAUSED,
    "Browser": ImplementationStatus.PAUSED,
}


# Human-readable explanation shown when a paused capability is requested.
PAUSED_MESSAGES: dict[str, str] = {
    "Browser": "Live browser automation is not connected in this build. The request was paused rather than faked.",
    "Hephaestus Relay": "Hephaestus Proto-Brain integration is not connected in this build. The relay will be enabled when Hephaestus is ready.",
}


def canonical_intent(capability_name: str) -> str:
    """Return the canonical runtime intent for a user-facing capability name."""
    name = capability_name.strip()
    return CAPABILITY_ALIASES.get(name, name)


def capability_status(intent: str) -> ImplementationStatus:
    """Return the implementation status of a canonical runtime intent."""
    return CAPABILITY_STATUS.get(intent, ImplementationStatus.PAUSED)


def is_real(intent: str) -> bool:
    return capability_status(intent) == ImplementationStatus.REAL


def is_partial(intent: str) -> bool:
    return capability_status(intent) == ImplementationStatus.PARTIAL


def is_paused(intent: str) -> bool:
    return capability_status(intent) == ImplementationStatus.PAUSED
