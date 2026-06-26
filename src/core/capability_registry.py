"""Shared capability honesty registry for Command Nexus.

Maps every visible Forge capability to:
- its canonical runtime intent
- whether it is fully wired (real), local-only/partial, or honestly paused
- what backend or option it needs

This keeps the runtime, the Forge, and the tutorial in sync so no capability
can pretend to be finished when it is not.
"""
from __future__ import annotations

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
    "Legal Assistant": "Business Workflow",
    "Medical Researcher": "Business Workflow",

    # Tool User
    "Tool User": "Tool User",
    "Agent": "Tool User",

    # Hephaestus Relay
    "Hephaestus Relay": "Hephaestus Relay",

    # Vision
    "Vision": "Vision",
    "Visibility": "Vision",
    "Visual Canvas": "Vision",
    "Voice Interface": "Voice",

    # Premium upgrade capabilities — mapped to canonical intents
    "Data Analyst Pro": "Data Analyst Pro",
    "Code Reviewer": "Code Reviewer",
    "Meeting Facilitator": "Meeting Facilitator",
    "Security Auditor": "Security Auditor",

    # Browser/Network/External (not wired)
    "Browser Automation": "Browser",
    "Email Automation": "Email",
    "API Integrator": "API",
    "Team Orchestrator": "Team",
    "Competitive Analyst": "Research",
    "Spreadsheet Wizard": "Document Processor",
    "Presentation Builder": "Creative Writing",
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

    # Partial: local scaffold works, but full quality needs a model or optional API
    "Research": ImplementationStatus.PARTIAL,
    "Coder": ImplementationStatus.PARTIAL,
    "Creative Writing": ImplementationStatus.PARTIAL,
    "Planner": ImplementationStatus.PARTIAL,
    "Tutor": ImplementationStatus.PARTIAL,
    "Business Workflow": ImplementationStatus.PARTIAL,
    "Hephaestus Relay": ImplementationStatus.PAUSED,
    "Vision": ImplementationStatus.PARTIAL,
    "Voice": ImplementationStatus.PARTIAL,
    "Data Analyst Pro": ImplementationStatus.PARTIAL,
    "Code Reviewer": ImplementationStatus.PARTIAL,
    "Meeting Facilitator": ImplementationStatus.PARTIAL,
    "Security Auditor": ImplementationStatus.PARTIAL,

    # Paused: not wired in this build
    "Browser": ImplementationStatus.PAUSED,
    "Email": ImplementationStatus.PAUSED,
    "API": ImplementationStatus.PAUSED,
    "Team": ImplementationStatus.PAUSED,
}


# Human-readable explanation shown when a paused capability is requested.
PAUSED_MESSAGES: dict[str, str] = {
    "Browser": "Live browser automation is not connected in this build. The request was paused rather than faked.",
    "Email": "Email access and automated sending are not connected in this build. Drafts can be produced, but sending is paused.",
    "API": "Live external API integration is not connected in this build. Configuration and planning work, but calls are paused.",
    "Team": "Multi-AI team orchestration is not connected in this build. Single-AI workflows work; team handoffs are paused.",
    "Hephaestus Relay": "Hephaestus Proto-Brain integration is not connected in this build. The relay will be enabled when Hephaestus is ready.",
    "Vision": "AI Vision analysis is limited to screen capture in this build. Visual understanding is paused.",
    "Voice": "Voice interface is not connected in this build. Text input works; voice control is paused.",
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
