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
    # High-risk specialized capabilities
    "Medical Researcher",
    "Legal Document Reviewer",
    # Phase 6 capabilities
    "Wellness Coach",
    "Content Strategist",
    "Fact Checker",
    # Phase 7 capabilities — expanded capability set
    "Task Scheduler",
    "Form Builder",
    "Report Generator",
    "Invoice Processor",
    "Spreadsheet Analyst",
    "Data Visualizer",
    "Statistical Modeler",
    "Trend Forecaster",
    "DevOps Assistant",
    "Database Manager",
    "Test Generator",
    "Documentation Generator",
    "Script Writer",
    "Copy Editor",
    "Podcast Planner",
    "Brand Strategist",
    "Presentation Coach",
    "PR Assistant",
    "Internal Comms Writer",
    "Academic Citation Manager",
    "Patent Researcher",
    "Market Analyst",
    "Recipe Planner",
    "Travel Planner",
    "Event Planner",
    "Personal Finance Manager",
    "Privacy Compliance Checker",
    "Data Governance Advisor",
    "Curriculum Designer",
    "Exam Prep Coach",
}


# Map every user-facing Forge capability name to its canonical runtime intent.
CAPABILITY_ALIASES: dict[str, str] = {
    # Chat
    "Chat Companion": "Chatbot",
    "Chat": "Chatbot",
    "Customer Support Agent": "Chatbot",
    "Customer Support AI": "Customer Support AI",
    "Email Sifter & Responder": "Email Automation",

    # Research
    "Research Assistant": "Research",
    "Academic Researcher": "Research",
    "Business Intelligence Analyst": "Research",
    "Smart Search": "Research",
    "Fact Checker": "Research",

    # Coder
    "Coding Assistant": "Coder",
    "IT Operations Agent": "Coder",

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

    # Document Processor
    "Document Processor": "Document Processor",
    "Document Generator": "Document Processor",
    "Data Entry Agent": "Document Processor",
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
    "Legal Document Reviewer": "Legal Document Reviewer",
    "Multi-Department Orchestrator": "Business Workflow",
    "Field Analyst": "Business Workflow",
    "Command Support": "Business Workflow",
    "Logistics Coordinator": "Business Workflow",
    "Tactical Advisor": "Business Workflow",
    "Medical Researcher": "Medical Researcher",

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
    "Negotiation Coach": "Financial Gainer",
    "Negotiation Assistant": "Financial Gainer",

    # Memory Recorder — records everything for auditability and recollection
    "Memory Recorder": "Memory Recorder",
    "Session Recorder": "Memory Recorder",
    "Activity Log": "Memory Recorder",
    "Audit Trail": "Memory Recorder",
    "Work Journal": "Memory Recorder",
    # Memory Saver sub-capabilities
    "Session Replay": "Memory Recorder",
    "Session Player": "Memory Recorder",
    "Smart Recall": "Memory Recorder",
    "Memory Search": "Memory Recorder",
    "Decision Tracker": "Memory Recorder",
    "Decision Log": "Memory Recorder",
    "Knowledge Archive": "Memory Recorder",
    "Knowledge Vault": "Memory Recorder",
    "Habit Tracker": "Memory Recorder",
    "Habit Logger": "Memory Recorder",
    "Progress Journal": "Memory Recorder",
    "Progress Tracker": "Memory Recorder",
    "Context Keeper": "Memory Recorder",
    "Context Saver": "Memory Recorder",
    "Audit Trail Builder": "Memory Recorder",
    "Compliance Trail Builder": "Memory Recorder",

    # Game Companion — learn and play games for individual use
    "Game Companion": "Game Companion",
    "Game Learner": "Game Companion",
    "Game Player": "Game Companion",
    "Strategy Gamer": "Game Companion",

    # New capabilities — mapped to existing canonical intents
    "Budget Tracker": "Financial Gainer",
    "Social Media Manager": "Creative Writing",
    "Study Coach": "Tutor",
    "Plagiarism Checker": "Research",
    "Form Builder": "Document Processor",
    "Survey Analyzer": "Data Analyst Pro",
    "Advanced Memory System": "Archive",
    "Custom Model Connector": "Chatbot",

    # Premium capability aliases (from capability_actions.py)
    "AI Team Lead": "Team Orchestrator",
    "Project Coordinator": "Team Orchestrator",
    "Memory Persistence": "Archive",
    "Context Memory": "Archive",
    "Image Generator": "Visual Canvas",
    "AI Artist": "Visual Canvas",
    "Data Science": "Data Analyst Pro",
    "Analytics Pro": "Data Analyst Pro",
    "Code Inspector": "Code Reviewer",
    "Quality Assurance": "Code Reviewer",
    "API Connector": "API Integrator",
    "Integration Builder": "API Integrator",
    "Wiki Builder": "Archive",
    "Documentation Center": "Archive",
    "Meeting Assistant": "Meeting Facilitator",
    "Conference Manager": "Meeting Facilitator",
    "Email Assistant": "Email Automation",
    "Inbox Manager": "Email Automation",
    "Schedule Optimizer": "Planner",
    "Time Manager": "Planner",
    "Report Builder": "Document Processor",
    "PDF Creator": "Document Processor",
    "Language Translator": "Tutor",
    "Multi-language": "Tutor",
    "Slide Deck Builder": "Creative Writing",
    "Keynote Assistant": "Creative Writing",
    "Excel Wizard": "Document Processor",
    "Sheets Expert": "Document Processor",
    "Contract Reviewer": "Legal Document Reviewer",
    "Compliance Checker": "Legal Document Reviewer",
    "Medical Search": "Medical Researcher",
    "Clinical Research": "Medical Researcher",
    "ADA Assistant": "Tutor",
    "Universal Access": "Tutor",
    # Truth Checker and Verification Tool now map to Fact Checker (canonical intent)
    # "Truth Checker": "Fact Checker",  # moved to Fact Checker section above
    # "Verification Tool": "Fact Checker",  # moved to Fact Checker section above
    "Speech Interface": "Voice Interface",
    "Talk to AI": "Voice Interface",
    "No-Code Automation": "Planner",
    "Process Builder": "Planner",
    "Vulnerability Scanner": "Security Auditor",
    "Penetration Testing": "Security Auditor",
    "Market Research": "Research",
    "Strategy Assistant": "Research",
    "Course Builder": "Tutor",
    "Training Designer": "Tutor",
    "Enterprise Search": "Research",
    "AI Search": "Research",

    # Wellness Coach — fitness, nutrition, mental wellness, habit building
    "Wellness Coach": "Wellness Coach",
    "Fitness Planner": "Wellness Coach",
    "Nutrition Advisor": "Wellness Coach",
    "Mental Wellness Guide": "Wellness Coach",
    "Habit Builder": "Wellness Coach",
    "Health Coach": "Wellness Coach",
    "Wellness Advisor": "Wellness Coach",

    # Content Strategist — content calendar, audience analysis, platform optimization
    "Content Strategist": "Content Strategist",
    "Content Calendar Planner": "Content Strategist",
    "Audience Analyzer": "Content Strategist",
    "Platform Optimizer": "Content Strategist",
    "Content Repurposer": "Content Strategist",
    "Brand Voice Tuner": "Content Strategist",
    "Content Strategy": "Content Strategist",

    # Fact Checker — verify claims, assess credibility, detect misinformation
    "Fact Checker": "Fact Checker",
    "Truth Checker": "Fact Checker",
    "Verification Tool": "Fact Checker",
    "Claim Verifier": "Fact Checker",
    "Misinformation Detector": "Fact Checker",

    # Phase 7 — New capability aliases
    "Task Scheduler": "Task Scheduler",
    "Scheduling Assistant": "Task Scheduler",
    "Appointment Scheduler": "Task Scheduler",
    "Form Builder": "Form Builder",
    "Survey Builder": "Form Builder",
    "Questionnaire Builder": "Form Builder",
    "Report Generator": "Report Generator",
    "Business Report Writer": "Report Generator",
    "Invoice Processor": "Invoice Processor",
    "Billing Assistant": "Invoice Processor",
    "Spreadsheet Analyst": "Spreadsheet Analyst",
    "Formula Expert": "Spreadsheet Analyst",
    "Data Visualizer": "Data Visualizer",
    "Chart Builder": "Data Visualizer",
    "Statistical Modeler": "Statistical Modeler",
    "Statistics Assistant": "Statistical Modeler",
    "Trend Forecaster": "Trend Forecaster",
    "Forecasting Assistant": "Trend Forecaster",
    "DevOps Assistant": "DevOps Assistant",
    "Infrastructure Assistant": "DevOps Assistant",
    "Database Manager": "Database Manager",
    "SQL Assistant": "Database Manager",
    "Test Generator": "Test Generator",
    "Test Writer": "Test Generator",
    "Documentation Generator": "Documentation Generator",
    "Docs Generator": "Documentation Generator",
    "Script Writer": "Script Writer",
    "Screenplay Writer": "Script Writer",
    "Copy Editor": "Copy Editor",
    "Proofreader": "Copy Editor",
    "Podcast Planner": "Podcast Planner",
    "Podcast Producer": "Podcast Planner",
    "Brand Strategist": "Brand Strategist",
    "Brand Identity Designer": "Brand Strategist",
    "Presentation Coach": "Presentation Coach",
    "Speech Coach": "Presentation Coach",
    "PR Assistant": "PR Assistant",
    "Press Release Writer": "PR Assistant",
    "Internal Comms Writer": "Internal Comms Writer",
    "Company Memo Writer": "Internal Comms Writer",
    "Academic Citation Manager": "Academic Citation Manager",
    "Citation Formatter": "Academic Citation Manager",
    "Patent Researcher": "Patent Researcher",
    "IP Research Assistant": "Patent Researcher",
    "Market Analyst": "Market Analyst",
    "Market Researcher": "Market Analyst",
    "Recipe Planner": "Recipe Planner",
    "Meal Planner": "Recipe Planner",
    "Travel Planner": "Travel Planner",
    "Trip Planner": "Travel Planner",
    "Event Planner": "Event Planner",
    "Event Coordinator": "Event Planner",
    "Personal Finance Manager": "Personal Finance Manager",
    "Budget Manager": "Personal Finance Manager",
    "Privacy Compliance Checker": "Privacy Compliance Checker",
    "GDPR Checker": "Privacy Compliance Checker",
    "Data Governance Advisor": "Data Governance Advisor",
    "Data Steward Assistant": "Data Governance Advisor",
    "Curriculum Designer": "Curriculum Designer",
    "Course Designer": "Curriculum Designer",
    "Exam Prep Coach": "Exam Prep Coach",
    "Test Prep Coach": "Exam Prep Coach",
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
    "Medical Researcher": ImplementationStatus.PARTIAL,
    "Legal Document Reviewer": ImplementationStatus.PARTIAL,
    "Wellness Coach": ImplementationStatus.PARTIAL,
    "Content Strategist": ImplementationStatus.PARTIAL,
    "Fact Checker": ImplementationStatus.PARTIAL,
    # Phase 7 — new capabilities
    "Task Scheduler": ImplementationStatus.PARTIAL,
    "Form Builder": ImplementationStatus.PARTIAL,
    "Report Generator": ImplementationStatus.PARTIAL,
    "Invoice Processor": ImplementationStatus.PARTIAL,
    "Spreadsheet Analyst": ImplementationStatus.PARTIAL,
    "Data Visualizer": ImplementationStatus.PARTIAL,
    "Statistical Modeler": ImplementationStatus.PARTIAL,
    "Trend Forecaster": ImplementationStatus.PARTIAL,
    "DevOps Assistant": ImplementationStatus.PARTIAL,
    "Database Manager": ImplementationStatus.PARTIAL,
    "Test Generator": ImplementationStatus.PARTIAL,
    "Documentation Generator": ImplementationStatus.PARTIAL,
    "Script Writer": ImplementationStatus.PARTIAL,
    "Copy Editor": ImplementationStatus.PARTIAL,
    "Podcast Planner": ImplementationStatus.PARTIAL,
    "Brand Strategist": ImplementationStatus.PARTIAL,
    "Presentation Coach": ImplementationStatus.PARTIAL,
    "PR Assistant": ImplementationStatus.PARTIAL,
    "Internal Comms Writer": ImplementationStatus.PARTIAL,
    "Academic Citation Manager": ImplementationStatus.PARTIAL,
    "Patent Researcher": ImplementationStatus.PARTIAL,
    "Market Analyst": ImplementationStatus.PARTIAL,
    "Recipe Planner": ImplementationStatus.PARTIAL,
    "Travel Planner": ImplementationStatus.PARTIAL,
    "Event Planner": ImplementationStatus.PARTIAL,
    "Personal Finance Manager": ImplementationStatus.PARTIAL,
    "Privacy Compliance Checker": ImplementationStatus.PARTIAL,
    "Data Governance Advisor": ImplementationStatus.PARTIAL,
    "Curriculum Designer": ImplementationStatus.PARTIAL,
    "Exam Prep Coach": ImplementationStatus.PARTIAL,

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
