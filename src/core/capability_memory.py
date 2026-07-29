# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""
Capability Memory & Scenario Engine
====================================

Every capability in Command Nexus has:

1. **Scenarios** — Multiple concrete use-case scenarios that show the AI
   exactly what to do with that capability in different situations.
   The AI uses these as reference points for routing and execution.

2. **Capability Memory** — Per-capability learned knowledge that persists
   across sessions. The AI can update this memory through intelligence,
   adding new patterns, preferences, and learned behaviors — BUT only
   if the update stays within the capability's defined scope.

3. **Scope Validation** — Every AI-proposed memory update is validated
   against the capability's zone. If the update falls outside what the
   capability is designed to do, it is rejected.

This ensures the AI has rich reference material for each capability
and can grow its understanding over time without breaking the
capability boundaries.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# ─── Scenario Definitions ──────────────────────────────────────────────

@dataclass
class CapabilityScenario:
    """A single use-case scenario for a capability."""
    scenario_id: str
    title: str
    trigger: str              # What user input triggers this scenario
    expected_action: str      # What the AI should do
    expected_output: str      # What the user should receive
    capabilities_needed: list[str]  # Other capabilities that may be involved
    approval_required: bool = False
    notes: str = ""


# ─── Per-Capability Scenarios ──────────────────────────────────────────

CAPABILITY_SCENARIOS: dict[str, list[CapabilityScenario]] = {

    "Chatbot": [
        CapabilityScenario(
            scenario_id="chat.1",
            title="Direct question answering",
            trigger="User asks a straightforward question",
            expected_action="Answer directly if within knowledge; route to Research if factual verification needed",
            expected_output="Clear conversational answer or routed response from Research",
            capabilities_needed=["Research"],
            notes="Always maintain conversational tone; never expose internal routing",
        ),
        CapabilityScenario(
            scenario_id="chat.2",
            title="Multi-capability orchestration",
            trigger="User request requires multiple capabilities (e.g., 'research X then write a summary')",
            expected_action="Identify needed capabilities → route in sequence → synthesize results into one response",
            expected_output="Unified response that draws from multiple capabilities seamlessly",
            capabilities_needed=["Research", "Creative Writing", "Planner"],
            notes="User should perceive one intelligent assistant, not multiple tools",
        ),
        CapabilityScenario(
            scenario_id="chat.3",
            title="Clarification and guidance",
            trigger="User request is vague or ambiguous",
            expected_action="Ask targeted clarifying questions; suggest available options",
            expected_output="Clarifying question or list of available actions",
            capabilities_needed=[],
            notes="Never guess; always ask when intent is unclear",
        ),
        CapabilityScenario(
            scenario_id="chat.4",
            title="Capability routing",
            trigger="User asks 'what can you do?' or mentions a specific task type",
            expected_action="List available capabilities with descriptions; suggest which to use",
            expected_output="Capability list with recommendations for the user's task",
            capabilities_needed=[],
            notes="Be honest about what's available and what requires approval",
        ),
    ],

    "Research": [
        CapabilityScenario(
            scenario_id="research.1",
            title="Fact-finding query",
            trigger="User asks a factual question requiring verification",
            expected_action="Search → compile findings → label confidence → cite sources",
            expected_output="Findings with confidence labels (high/medium/low) and source citations",
            capabilities_needed=["Chatbot"],
            notes="Always distinguish verified facts from speculation",
        ),
        CapabilityScenario(
            scenario_id="research.2",
            title="Comparison analysis",
            trigger="User asks to compare two or more options",
            expected_action="Research each option → identify pros/cons → create comparison table → assess risks",
            expected_output="Side-by-side comparison with risk assessment and recommendation",
            capabilities_needed=["Chatbot", "Planner"],
            notes="Present neutral comparison; let user decide",
        ),
        CapabilityScenario(
            scenario_id="research.3",
            title="Risk assessment",
            trigger="User is evaluating a decision with potential risks",
            expected_action="Identify risks → categorize severity → research mitigations → present risk register",
            expected_output="Risk register with severity levels and mitigation strategies",
            capabilities_needed=["Planner"],
            notes="Flag unknowns explicitly; never minimize risks",
        ),
        CapabilityScenario(
            scenario_id="research.4",
            title="Source verification",
            trigger="User provides a claim and wants it fact-checked",
            expected_action="Find supporting/contradicting sources → assess credibility → report findings",
            expected_output="Verification report with source credibility assessment",
            capabilities_needed=[],
            notes="Be transparent about source quality and bias",
        ),
    ],

    "Creative Writing": [
        CapabilityScenario(
            scenario_id="writing.1",
            title="Draft from prompt",
            trigger="User provides a writing prompt or idea",
            expected_action="Understand constraints → draft → apply tone → flag assumptions",
            expected_output="Draft content with assumption flags and tone notes",
            capabilities_needed=["Chatbot", "Research"],
            notes="Flag any fictional or assumed content explicitly",
        ),
        CapabilityScenario(
            scenario_id="writing.2",
            title="Revision and editing",
            trigger="User provides existing text for improvement",
            expected_action="Analyze → identify improvements → revise → preserve voice → present changes",
            expected_output="Revised text with change summary",
            capabilities_needed=["Chatbot"],
            notes="Preserve the user's voice; suggest rather than replace",
        ),
        CapabilityScenario(
            scenario_id="writing.3",
            title="Multi-format output",
            trigger="User needs content in a specific format (email, blog, report, etc.)",
            expected_action="Adapt content to format conventions → apply appropriate tone → structure correctly",
            expected_output="Format-appropriate content with structure notes",
            capabilities_needed=["Document Processor"],
            notes="Each format has different conventions; respect them",
        ),
        CapabilityScenario(
            scenario_id="writing.4",
            title="Creative collaboration",
            trigger="User wants to brainstorm or develop ideas together",
            expected_action="Offer ideas → build on user input → suggest directions → draft samples",
            expected_output="Idea list, sample drafts, and suggested directions",
            capabilities_needed=["Chatbot", "Research"],
            notes="This is collaborative; the user leads, the AI assists",
        ),
    ],

    "Coder": [
        CapabilityScenario(
            scenario_id="coder.1",
            title="Code explanation",
            trigger="User asks to understand existing code",
            expected_action="Analyze code → explain logic → identify patterns → flag potential issues",
            expected_output="Clear explanation with line references and issue flags",
            capabilities_needed=["Chatbot"],
            notes="Show-code-only; never auto-apply changes",
        ),
        CapabilityScenario(
            scenario_id="coder.2",
            title="Bug diagnosis",
            trigger="User reports a bug or error",
            expected_action="Analyze error → identify root cause → propose fix → show diff → outline test",
            expected_output="Diagnosis, proposed fix as diff, and test plan",
            capabilities_needed=["Chatbot", "Research"],
            approval_required=True,
            notes="Never apply fixes without approval; always show diff first",
        ),
        CapabilityScenario(
            scenario_id="coder.3",
            title="Feature implementation",
            trigger="User requests a new feature or function",
            expected_action="Understand requirements → draft implementation → show code → outline tests → flag risks",
            expected_output="Draft code, test plan, and risk assessment",
            capabilities_needed=["Chatbot", "Planner"],
            approval_required=True,
            notes="Draft only; execution requires approval",
        ),
        CapabilityScenario(
            scenario_id="coder.4",
            title="Code review",
            trigger="User asks for a code review",
            expected_action="Review for quality, security, performance → categorize issues → suggest fixes",
            expected_output="Review report with categorized issues and suggested fixes",
            capabilities_needed=["Research"],
            notes="Distinguish critical from cosmetic; suggest, don't auto-apply",
        ),
    ],

    "Planner": [
        CapabilityScenario(
            scenario_id="planner.1",
            title="Goal decomposition",
            trigger="User provides a goal or objective",
            expected_action="Decompose into tasks → identify dependencies → prioritize → create timeline",
            expected_output="Task list with dependencies, priorities, and timeline",
            capabilities_needed=["Chatbot"],
            notes="Break down to actionable tasks; flag assumptions",
        ),
        CapabilityScenario(
            scenario_id="planner.2",
            title="Project planning",
            trigger="User describes a project with multiple phases",
            expected_action="Structure phases → assign milestones → identify risks → create schedule",
            expected_output="Project plan with milestones, risk register, and schedule",
            capabilities_needed=["Research", "Chatbot"],
            notes="Include risk mitigation for each phase",
        ),
        CapabilityScenario(
            scenario_id="planner.3",
            title="Task prioritization",
            trigger="User has many tasks and needs help organizing",
            expected_action="List tasks → assess urgency/importance → suggest priority order → identify blockers",
            expected_output="Prioritized task list with rationale and blocker flags",
            capabilities_needed=[],
            notes="Consider deadlines, dependencies, and effort",
        ),
        CapabilityScenario(
            scenario_id="planner.4",
            title="Risk-aware planning",
            trigger="User is planning something with significant risks",
            expected_action="Identify risks → assess probability/impact → create mitigation plan → build contingencies",
            expected_output="Risk-aware plan with mitigation strategies and contingencies",
            capabilities_needed=["Research"],
            notes="Always include contingency plans for high-impact risks",
        ),
    ],

    "Notebook": [
        CapabilityScenario(
            scenario_id="notes.1",
            title="Quick capture",
            trigger="User wants to save a note or idea quickly",
            expected_action="Capture → auto-tag → store → confirm",
            expected_output="Saved note confirmation with auto-generated tags",
            capabilities_needed=["Chatbot"],
            notes="Auto-tag based on content; user can retag later",
        ),
        CapabilityScenario(
            scenario_id="notes.2",
            title="Recall and search",
            trigger="User asks to find previous notes",
            expected_action="Search by tag/content/date → retrieve → summarize → present",
            expected_output="Matching notes with relevance summary",
            capabilities_needed=["Chatbot"],
            notes="Summarize long notes; show most relevant first",
        ),
        CapabilityScenario(
            scenario_id="notes.3",
            title="Continuity briefing",
            trigger="User starts a new session and wants context from before",
            expected_action="Retrieve recent notes → summarize context → present continuity brief",
            expected_output="Continuity brief with key points from previous sessions",
            capabilities_needed=["Chatbot"],
            notes="Focus on actionable context; don't dump everything",
        ),
        CapabilityScenario(
            scenario_id="notes.4",
            title="Knowledge organization",
            trigger="User has accumulated many notes and wants structure",
            expected_action="Analyze notes → suggest categories → propose organization → apply on approval",
            expected_output="Proposed category structure and organization plan",
            capabilities_needed=["Planner"],
            approval_required=True,
            notes="Propose first; apply only after user approval",
        ),
    ],

    "Document Processor": [
        CapabilityScenario(
            scenario_id="docs.1",
            title="Document summarization",
            trigger="User provides a document for summarization",
            expected_action="Read → identify key points → summarize → flag sensitive content",
            expected_output="Concise summary with key points and sensitivity flags",
            capabilities_needed=["Chatbot"],
            notes="Preserve original; never alter source documents",
        ),
        CapabilityScenario(
            scenario_id="docs.2",
            title="Information extraction",
            trigger="User wants specific information extracted from a document",
            expected_action="Identify target info → extract → structure → present with source references",
            expected_output="Extracted information in structured format with source references",
            capabilities_needed=["Research"],
            notes="Show where in the document the info came from",
        ),
        CapabilityScenario(
            scenario_id="docs.3",
            title="Document classification",
            trigger="User needs to categorize or classify documents",
            expected_action="Analyze content → identify type → suggest category → classify",
            expected_output="Classification with confidence and reasoning",
            capabilities_needed=[],
            notes="Suggest category; let user confirm or override",
        ),
        CapabilityScenario(
            scenario_id="docs.4",
            title="Document comparison",
            trigger="User wants to compare two or more documents",
            expected_action="Read all → identify similarities/differences → create comparison → flag conflicts",
            expected_output="Comparison report with conflicts and key differences highlighted",
            capabilities_needed=["Research"],
            notes="Flag contradictions between documents explicitly",
        ),
    ],

    "Archive": [
        CapabilityScenario(
            scenario_id="archive.1",
            title="Artifact storage",
            trigger="User wants to save completed work",
            expected_action="Tag → date → store → index → confirm",
            expected_output="Storage confirmation with retrieval tags",
            capabilities_needed=[],
            notes="Auto-generate tags from content; preserve metadata",
        ),
        CapabilityScenario(
            scenario_id="archive.2",
            title="Artifact retrieval",
            trigger="User wants to find saved work",
            expected_action="Search by tag/date/content → retrieve → present with context",
            expected_output="Matching artifacts with context and metadata",
            capabilities_needed=["Chatbot"],
            notes="Show metadata so user can identify the right version",
        ),
        CapabilityScenario(
            scenario_id="archive.3",
            title="Lifecycle management",
            trigger="User wants to organize or clean up archive",
            expected_action="Analyze archive → suggest organization → propose lifecycle actions → await approval",
            expected_output="Organization proposal and lifecycle recommendations",
            capabilities_needed=["Planner"],
            approval_required=True,
            notes="Never delete or move without explicit approval",
        ),
        CapabilityScenario(
            scenario_id="archive.4",
            title="Historical reference",
            trigger="User needs to reference past work for current project",
            expected_action="Find relevant past artifacts → summarize → connect to current context",
            expected_output="Historical reference summary connected to current work",
            capabilities_needed=["Notebook", "Chatbot"],
            notes="Connect past work to current needs; don't just dump old files",
        ),
    ],

    "Tool User": [
        CapabilityScenario(
            scenario_id="tools.1",
            title="Tool proposal",
            trigger="User asks for automation or tool assistance",
            expected_action="Identify need → propose tool → explain purpose → assess risks → request approval",
            expected_output="Tool proposal with rationale, risk assessment, and approval request",
            capabilities_needed=["Chatbot"],
            approval_required=True,
            notes="NEVER auto-invoke; always propose and wait",
        ),
        CapabilityScenario(
            scenario_id="tools.2",
            title="Tool chain design",
            trigger="User needs multiple tools working together",
            expected_action="Map workflow → identify tools → design chain → explain each step → request approval",
            expected_output="Tool chain proposal with step-by-step explanation",
            capabilities_needed=["Planner"],
            approval_required=True,
            notes="Explain each link in the chain; user approves each step",
        ),
        CapabilityScenario(
            scenario_id="tools.3",
            title="Integration assessment",
            trigger="User wants to connect to an external service",
            expected_action="Assess integration → identify requirements → propose approach → flag risks",
            expected_output="Integration assessment with requirements and risk flags",
            capabilities_needed=["Research"],
            approval_required=True,
            notes="Flag security and data exposure risks prominently",
        ),
    ],

    "Tutor": [
        CapabilityScenario(
            scenario_id="tutor.1",
            title="Concept explanation",
            trigger="User wants to learn a concept",
            expected_action="Assess level → explain adaptively → check understanding → provide examples",
            expected_output="Level-appropriate explanation with examples and understanding check",
            capabilities_needed=["Chatbot"],
            notes="Adapt to learner level; don't assume prior knowledge",
        ),
        CapabilityScenario(
            scenario_id="tutor.2",
            title="Quiz and assessment",
            trigger="User wants to test their knowledge",
            expected_action="Create quiz → administer → evaluate → provide feedback → suggest next steps",
            expected_output="Quiz with feedback and learning recommendations",
            capabilities_needed=[],
            notes="Provide constructive feedback; identify areas for improvement",
        ),
        CapabilityScenario(
            scenario_id="tutor.3",
            title="Study guide creation",
            trigger="User needs study materials for a topic",
            expected_action="Identify key concepts → create study sheet → include examples → suggest practice",
            expected_output="Study guide with key concepts, examples, and practice suggestions",
            capabilities_needed=["Notebook", "Document Processor"],
            notes="Structure for the learner's level; include practice exercises",
        ),
        CapabilityScenario(
            scenario_id="tutor.4",
            title="Adaptive learning path",
            trigger="User wants a structured learning plan",
            expected_action="Assess current level → identify goals → create path → suggest milestones",
            expected_output="Learning path with milestones and recommended resources",
            capabilities_needed=["Planner"],
            notes="Adjust path based on progress; celebrate milestones",
        ),
    ],

    "Business Workflow": [
        CapabilityScenario(
            scenario_id="business.1",
            title="SOP creation",
            trigger="User needs a standard operating procedure",
            expected_action="Understand process → map steps → create SOP → identify approval points",
            expected_output="Structured SOP with approval gates and role assignments",
            capabilities_needed=["Chatbot"],
            notes="Make SOPs audit-friendly; separate draft from execution",
        ),
        CapabilityScenario(
            scenario_id="business.2",
            title="Checklist generation",
            trigger="User needs a checklist for a recurring process",
            expected_action="Identify process steps → create checklist → add validation points → format",
            expected_output="Actionable checklist with validation points",
            capabilities_needed=[],
            notes="Checklists should be practical and verifiable",
        ),
        CapabilityScenario(
            scenario_id="business.3",
            title="Support response drafting",
            trigger="User needs to draft a customer or internal response",
            expected_action="Understand inquiry → draft response → flag sensitive areas → await approval",
            expected_output="Draft response with sensitivity flags",
            capabilities_needed=["Creative Writing", "Chatbot"],
            approval_required=True,
            notes="Never auto-send; always draft and await approval",
        ),
        CapabilityScenario(
            scenario_id="business.4",
            title="Workflow automation proposal",
            trigger="User wants to automate a business process",
            expected_action="Map process → identify automation points → propose tools → assess risks → request approval",
            expected_output="Automation proposal with risk assessment and approval request",
            capabilities_needed=["Tool User", "Planner"],
            approval_required=True,
            notes="Separate recommendation from execution; always require approval",
        ),
    ],

    "Hephaestus Relay": [
        CapabilityScenario(
            scenario_id="relay.1",
            title="Design brief creation",
            trigger="User has a design idea to structure",
            expected_action="Gather requirements → identify constraints → list unknowns → format brief",
            expected_output="Structured design brief with constraints and unknowns",
            capabilities_needed=["Chatbot"],
            notes="List unknowns explicitly; don't guess on technical specs",
        ),
        CapabilityScenario(
            scenario_id="relay.2",
            title="Constraint analysis",
            trigger="User needs to understand design constraints",
            expected_action="Identify constraints → categorize (hard/soft) → assess impact → present",
            expected_output="Constraint analysis with impact assessment",
            capabilities_needed=["Research"],
            notes="Distinguish hard constraints from soft preferences",
        ),
        CapabilityScenario(
            scenario_id="relay.3",
            title="Handoff packet preparation",
            trigger="User is ready to hand off to Hephaestus",
            expected_action="Compile brief → format for handoff → include all context → prepare packet",
            expected_output="Complete handoff packet with all design context",
            capabilities_needed=["Document Processor"],
            approval_required=True,
            notes="Include all constraints, unknowns, and requirements",
        ),
    ],

    # ─── Activity Watcher ──────────────────────────────────────────────

    "Activity Watcher": [
        CapabilityScenario(
            scenario_id="watcher.1",
            title="Pattern observation",
            trigger="User asks the AI to watch them work and learn a task",
            expected_action="Observe user actions → detect recurring patterns → confirm pattern repeated 3+ times → report findings",
            expected_output="List of detected patterns with frequency and description",
            capabilities_needed=["Memory Recorder", "Chatbot"],
            notes="Never interrupt the user while observing; only report after pattern is confirmed",
        ),
        CapabilityScenario(
            scenario_id="watcher.2",
            title="Efficiency suggestion",
            trigger="User asks for suggestions on how to work faster",
            expected_action="Analyze observed patterns → identify bottlenecks → propose faster alternatives → estimate time savings",
            expected_output="Efficiency report with specific suggestions and estimated time savings",
            capabilities_needed=["Planner", "Chatbot"],
            notes="Only suggest after confirming a pattern; never suggest based on a single observation",
        ),
        CapabilityScenario(
            scenario_id="watcher.3",
            title="Task repetition with approval",
            trigger="User asks the AI to repeat a learned task",
            expected_action="Identify learned task → show user what will be done → request explicit approval → execute step by step",
            expected_output="Task executed with approval at each step, or cancelled",
            capabilities_needed=["Tool User"],
            approval_required=True,
            notes="NEVER auto-execute; always show what will happen and get approval first",
        ),
        CapabilityScenario(
            scenario_id="watcher.4",
            title="Workflow report",
            trigger="User asks what the AI has learned about their work habits",
            expected_action="Compile all observed patterns → categorize by frequency → present summary with insights",
            expected_output="Workflow summary with pattern categories, frequencies, and insights",
            capabilities_needed=["Memory Recorder", "Notebook"],
            notes="Present objectively; don't judge the user's habits",
        ),
    ],

    # ─── Financial Gainer ──────────────────────────────────────────────

    "Financial Gainer": [
        CapabilityScenario(
            scenario_id="gainer.1",
            title="Skill monetization analysis",
            trigger="User asks how to make money with their skills",
            expected_action="Show disclaimer → assess user skills → research monetization paths → present realistic opportunities with ROI estimates",
            expected_output="Income path suggestions with ROI estimates, time investment, and difficulty ratings — preceded by mandatory disclaimer",
            capabilities_needed=["Research", "Chatbot"],
            notes="ALWAYS show disclaimer first; never skip it",
        ),
        CapabilityScenario(
            scenario_id="gainer.2",
            title="Side hustle planning",
            trigger="User wants to start a side hustle",
            expected_action="Show disclaimer → assess available time and resources → suggest side hustles → estimate startup costs → flag risks",
            expected_output="Side hustle recommendations with startup costs, time requirements, and risk assessment — preceded by disclaimer",
            capabilities_needed=["Planner", "Research"],
            notes="Include startup costs and realistic time to first income",
        ),
        CapabilityScenario(
            scenario_id="gainer.3",
            title="Income path comparison",
            trigger="User is choosing between multiple income opportunities",
            expected_action="Show disclaimer → compare options → assess ROI, risk, time, and effort → present comparison table",
            expected_output="Comparison table with ROI, risk, time investment, and difficulty for each option — preceded by disclaimer",
            capabilities_needed=["Research", "Data Analyst Pro"],
            notes="Present neutral comparison; let user decide; always include disclaimer",
        ),
        CapabilityScenario(
            scenario_id="gainer.4",
            title="Skill development for income",
            trigger="User asks what skills to learn to increase income",
            expected_action="Show disclaimer → analyze current skills → research market demand → suggest skills with income potential → recommend learning path",
            expected_output="Skill recommendations with market demand, learning time, and income potential — preceded by disclaimer",
            capabilities_needed=["Tutor", "Research"],
            notes="Base recommendations on market research, not speculation",
        ),
    ],

    # ─── Memory Recorder ───────────────────────────────────────────────

    "Memory Recorder": [
        CapabilityScenario(
            scenario_id="recorder.1",
            title="Session recording",
            trigger="User starts a work session (automatic)",
            expected_action="Begin recording → capture all events with timestamps → index for search → continue silently",
            expected_output="Silent recording; no user-facing output unless queried",
            capabilities_needed=[],
            notes="Record silently; never interrupt the user's workflow",
        ),
        CapabilityScenario(
            scenario_id="recorder.2",
            title="Session search and replay",
            trigger="User asks what they did during a past session",
            expected_action="Search recordings by date/content → retrieve relevant session → present timeline → allow replay",
            expected_output="Session timeline with key events, decisions, and outcomes",
            capabilities_needed=["Chatbot"],
            notes="Summarize long sessions; highlight key decisions and outcomes",
        ),
        CapabilityScenario(
            scenario_id="recorder.3",
            title="Audit trail",
            trigger="User needs an audit trail for compliance or review",
            expected_action="Compile session logs → format as audit report → include all AI actions and decisions → present for review",
            expected_output="Formatted audit trail with timestamps, actions, decisions, and outcomes",
            capabilities_needed=["Document Processor"],
            approval_required=True,
            notes="Include what the AI did and why; flag any actions that required approval",
        ),
        CapabilityScenario(
            scenario_id="recorder.4",
            title="Recording management",
            trigger="User wants to manage or delete recordings",
            expected_action="List recordings → allow search/filter → enable deletion → confirm before deleting",
            expected_output="Recording management interface with search, filter, and delete capabilities",
            capabilities_needed=[],
            notes="Always confirm before deleting; deleted recordings cannot be recovered",
        ),
    ],

    # ─── Game Companion ────────────────────────────────────────────────

    "Game Companion": [
        CapabilityScenario(
            scenario_id="game.1",
            title="Learn game rules",
            trigger="User wants to learn a new game",
            expected_action="Explain rules clearly → provide examples → check understanding → offer practice scenario",
            expected_output="Rule explanation with examples and a practice scenario",
            capabilities_needed=["Tutor", "Chatbot"],
            notes="Adapt explanation to user's experience level with similar games",
        ),
        CapabilityScenario(
            scenario_id="game.2",
            title="Strategy suggestion",
            trigger="User asks for strategy advice in a game",
            expected_action="Assess position → analyze options → suggest strategy → explain reasoning → adapt to skill level",
            expected_output="Strategy suggestion with reasoning and alternative approaches",
            capabilities_needed=["Research"],
            notes="Don't just give the answer; explain why the strategy works",
        ),
        CapabilityScenario(
            scenario_id="game.3",
            title="Game analysis",
            trigger="User wants analysis of a completed game",
            expected_action="Review moves → identify mistakes → highlight good plays → suggest improvements → rate performance",
            expected_output="Game analysis with move-by-move commentary and improvement suggestions",
            capabilities_needed=["Research"],
            notes="Be objective; highlight both good and bad plays",
        ),
        CapabilityScenario(
            scenario_id="game.4",
            title="Practice game",
            trigger="User wants to play a practice game with the AI",
            expected_action="Set up game → adapt difficulty to user level → play moves → provide commentary → review after game",
            expected_output="Practice game with move commentary and post-game review",
            capabilities_needed=["Chatbot"],
            notes="Adapt difficulty to challenge but not frustrate the user",
        ),
    ],

    "Task Scheduler": [
        CapabilityScenario(
            scenario_id="sched.1",
            title="Weekly schedule planning",
            trigger="User wants to plan their week",
            expected_action="Identify priorities, estimate durations, suggest time blocks, set reminders",
            expected_output="Structured weekly schedule with time blocks and reminder suggestions",
            capabilities_needed=["Planner"],
        ),
        CapabilityScenario(
            scenario_id="sched.2",
            title="Meeting scheduling",
            trigger="User needs to schedule multiple meetings",
            expected_action="Suggest optimal times, avoid conflicts, propose buffer time",
            expected_output="Meeting schedule with suggested times and buffer periods",
            capabilities_needed=["Planner", "Calendar Manager"],
        ),
    ],
    "Form Builder": [
        CapabilityScenario(
            scenario_id="form.1",
            title="Customer satisfaction survey",
            trigger="User needs a customer satisfaction survey",
            expected_action="Design survey with appropriate question types, rating scales, and open-ended questions",
            expected_output="Complete survey design with question types and structure",
            capabilities_needed=["Research"],
        ),
    ],
    "Report Generator": [
        CapabilityScenario(
            scenario_id="report.1",
            title="Monthly status report",
            trigger="User needs a monthly status report",
            expected_action="Structure report with executive summary, key metrics, progress, and next steps",
            expected_output="Formatted report structure ready for content input",
            capabilities_needed=["Research", "Data Visualizer"],
        ),
    ],
    "Invoice Processor": [
        CapabilityScenario(
            scenario_id="inv.1",
            title="Service invoice creation",
            trigger="User needs to create an invoice for services",
            expected_action="Generate invoice with line items, calculations, and payment terms",
            expected_output="Formatted invoice with all required fields",
            capabilities_needed=[],
            notes="Always verify calculations before sending",
        ),
    ],
    "Spreadsheet Analyst": [
        CapabilityScenario(
            scenario_id="ss.1",
            title="Formula assistance",
            trigger="User needs help with a spreadsheet formula",
            expected_action="Provide correct formula syntax, explain logic, suggest alternatives",
            expected_output="Formula with explanation and usage instructions",
            capabilities_needed=[],
        ),
    ],
    "Data Visualizer": [
        CapabilityScenario(
            scenario_id="dv.1",
            title="Chart type recommendation",
            trigger="User has data and wants to visualize it",
            expected_action="Analyze data type and goal, recommend appropriate chart types with rationale",
            expected_output="Chart recommendations with design tips and rationale",
            capabilities_needed=["Spreadsheet Analyst"],
        ),
    ],
    "Statistical Modeler": [
        CapabilityScenario(
            scenario_id="stat.1",
            title="Regression analysis guidance",
            trigger="User needs regression analysis",
            expected_action="Guide method selection, check assumptions, interpret results",
            expected_output="Statistical analysis guidance with method and interpretation",
            capabilities_needed=["Data Visualizer"],
            notes="Always state assumptions and limitations",
        ),
    ],
    "Trend Forecaster": [
        CapabilityScenario(
            scenario_id="fc.1",
            title="Revenue forecasting",
            trigger="User wants to forecast future revenue",
            expected_action="Analyze historical patterns, select forecasting method, provide projections with CIs",
            expected_output="Forecast with methodology, projections, and confidence intervals",
            capabilities_needed=["Statistical Modeler", "Data Visualizer"],
        ),
    ],
    "DevOps Assistant": [
        CapabilityScenario(
            scenario_id="devops.1",
            title="CI/CD pipeline setup",
            trigger="User wants to set up a CI/CD pipeline",
            expected_action="Provide pipeline structure, configuration examples, and best practices",
            expected_output="CI/CD pipeline guidance with configuration examples",
            capabilities_needed=["Coder", "Script Writer"],
            approval_required=True,
        ),
    ],
    "Database Manager": [
        CapabilityScenario(
            scenario_id="db.1",
            title="Schema design",
            trigger="User needs to design a database schema",
            expected_action="Recommend normalized schema with tables, relationships, and indexes",
            expected_output="Schema design with table definitions and relationship mapping",
            capabilities_needed=["Coder"],
        ),
    ],
    "Test Generator": [
        CapabilityScenario(
            scenario_id="test.1",
            title="Unit test generation",
            trigger="User wants unit tests for a function",
            expected_action="Generate test cases covering happy path, edge cases, and error handling",
            expected_output="Complete test suite with test cases and assertions",
            capabilities_needed=["Coder"],
        ),
    ],
    "Documentation Generator": [
        CapabilityScenario(
            scenario_id="doc.1",
            title="API documentation",
            trigger="User needs API documentation",
            expected_action="Generate API docs with endpoints, parameters, examples, and response formats",
            expected_output="Structured API documentation ready for review",
            capabilities_needed=["Coder"],
        ),
    ],
    "Script Writer": [
        CapabilityScenario(
            scenario_id="script.1",
            title="Automation script",
            trigger="User needs an automation script",
            expected_action="Generate well-commented script with error handling and logging",
            expected_output="Complete script with comments and usage instructions",
            capabilities_needed=["Coder"],
            approval_required=True,
        ),
    ],
    "Copy Editor": [
        CapabilityScenario(
            scenario_id="copy.1",
            title="Text editing",
            trigger="User wants text edited for grammar and style",
            expected_action="Edit for grammar, clarity, conciseness, and tone while preserving voice",
            expected_output="Edited text with change notes",
            capabilities_needed=["Creative Writing"],
        ),
    ],
    "Podcast Planner": [
        CapabilityScenario(
            scenario_id="pod.1",
            title="Episode planning",
            trigger="User wants to plan podcast episodes",
            expected_action="Create episode structure, segment breakdown, and show notes template",
            expected_output="Podcast plan with episode structure and show notes",
            capabilities_needed=["Content Strategist"],
        ),
    ],
    "Brand Strategist": [
        CapabilityScenario(
            scenario_id="brand.1",
            title="Brand identity development",
            trigger="User needs a brand identity",
            expected_action="Develop mission, vision, values, positioning, and personality",
            expected_output="Comprehensive brand strategy document",
            capabilities_needed=["Content Strategist", "Marketing Generator"],
        ),
    ],
    "Presentation Coach": [
        CapabilityScenario(
            scenario_id="pres.1",
            title="Presentation structure",
            trigger="User needs help structuring a presentation",
            expected_action="Provide structure, talking points, and delivery tips",
            expected_output="Presentation outline with talking points and coaching tips",
            capabilities_needed=["Creative Writing"],
        ),
    ],
    "PR Assistant": [
        CapabilityScenario(
            scenario_id="pr.1",
            title="Press release writing",
            trigger="User needs a press release",
            expected_action="Draft press release with proper format, headline, and boilerplate",
            expected_output="Formatted press release ready for review",
            capabilities_needed=["Copy Editor"],
            approval_required=True,
        ),
    ],
    "Internal Comms Writer": [
        CapabilityScenario(
            scenario_id="ic.1",
            title="Company announcement",
            trigger="User needs a company-wide announcement",
            expected_action="Draft clear, empathetic announcement with context and next steps",
            expected_output="Internal communication ready for review",
            capabilities_needed=["Copy Editor"],
        ),
    ],
    "Academic Citation Manager": [
        CapabilityScenario(
            scenario_id="cite.1",
            title="Citation formatting",
            trigger="User needs citations formatted",
            expected_action="Format citations in requested style with all required fields",
            expected_output="Properly formatted citations and bibliography",
            capabilities_needed=["Research"],
        ),
    ],
    "Patent Researcher": [
        CapabilityScenario(
            scenario_id="patent.1",
            title="Prior art search guidance",
            trigger="User wants to search for prior art",
            expected_action="Guide search strategy, suggest databases and keywords",
            expected_output="Search strategy with database suggestions and keyword recommendations",
            capabilities_needed=["Research"],
            notes="Informational only — consult a patent attorney",
        ),
    ],
    "Market Analyst": [
        CapabilityScenario(
            scenario_id="market.1",
            title="Market opportunity assessment",
            trigger="User wants to assess a market opportunity",
            expected_action="Analyze market size, trends, competitors, and barriers",
            expected_output="Market analysis with TAM/SAM/SOM and competitive landscape",
            capabilities_needed=["Research", "Trend Forecaster"],
        ),
    ],
    "Recipe Planner": [
        CapabilityScenario(
            scenario_id="recipe.1",
            title="Weekly meal planning",
            trigger="User wants meal plans for the week",
            expected_action="Suggest balanced meals based on preferences, create shopping list",
            expected_output="Weekly meal plan with recipes and shopping list",
            capabilities_needed=[],
        ),
    ],
    "Travel Planner": [
        CapabilityScenario(
            scenario_id="travel.1",
            title="Trip itinerary planning",
            trigger="User wants to plan a trip",
            expected_action="Create day-by-day itinerary with activities, logistics, and budget",
            expected_output="Complete travel itinerary with activities and tips",
            capabilities_needed=[],
        ),
    ],
    "Event Planner": [
        CapabilityScenario(
            scenario_id="event.1",
            title="Event planning",
            trigger="User wants to plan an event",
            expected_action="Create event plan with timeline, logistics, budget, and checklist",
            expected_output="Comprehensive event plan with timeline and checklist",
            capabilities_needed=["Internal Comms Writer"],
        ),
    ],
    "Personal Finance Manager": [
        CapabilityScenario(
            scenario_id="finance.1",
            title="Budget creation",
            trigger="User wants to create a budget",
            expected_action="Analyze income/expenses, suggest budget allocation, set savings goals",
            expected_output="Budget plan with category allocations and savings targets",
            capabilities_needed=[],
            notes="General guidance only — not financial advice",
        ),
    ],
    "Privacy Compliance Checker": [
        CapabilityScenario(
            scenario_id="privacy.1",
            title="GDPR compliance check",
            trigger="User wants to check GDPR compliance",
            expected_action="Review data practices against GDPR requirements, identify gaps",
            expected_output="Compliance assessment with gaps and recommendations",
            capabilities_needed=["Data Governance Advisor"],
            notes="Informational only — consult a legal professional",
        ),
    ],
    "Data Governance Advisor": [
        CapabilityScenario(
            scenario_id="gov.1",
            title="Governance framework design",
            trigger="User needs a data governance framework",
            expected_action="Design framework with policies, roles, quality metrics, and processes",
            expected_output="Governance framework document with policies and roles",
            capabilities_needed=["Privacy Compliance Checker"],
        ),
    ],
    "Curriculum Designer": [
        CapabilityScenario(
            scenario_id="curr.1",
            title="Course design",
            trigger="User wants to design a course",
            expected_action="Create curriculum with learning objectives, modules, and assessments",
            expected_output="Structured curriculum with modules and assessment plan",
            capabilities_needed=["Exam Prep Coach"],
        ),
    ],
    "Exam Prep Coach": [
        CapabilityScenario(
            scenario_id="exam.1",
            title="Study plan creation",
            trigger="User needs an exam study plan",
            expected_action="Assess baseline, create study schedule, suggest practice strategies",
            expected_output="Study plan with schedule, topics, and practice strategies",
            capabilities_needed=["Curriculum Designer"],
        ),
    ],
}


# ─── Capability Scope Zones (for validation) ───────────────────────────

CAPABILITY_SCOPE: dict[str, dict[str, list[str]]] = {
    "Chatbot": {
        "within_scope": [
            "conversation", "routing", "answering questions", "clarifying intent",
            "presenting information", "orchestrating capabilities", "user interface",
            "context management", "summarizing responses",
        ],
        "out_of_scope": [
            "file write", "code execution", "api call", "network access",
            "tool invocation", "bypass approval", "auto-executing", "auto-applying",
            "file modification", "modify files", "delete file", "install",
        ],
    },
    "Research": {
        "within_scope": [
            "information gathering", "fact checking", "source verification",
            "comparison analysis", "risk assessment", "confidence labeling",
            "citation tracking", "knowledge gap identification",
        ],
        "out_of_scope": [
            "content creation", "code writing", "file modification", "modify files",
            "tool execution", "auto-executing", "auto-applying", "sending messages",
            "publishing", "bypass security", "bypass approval",
        ],
    },
    "Creative Writing": {
        "within_scope": [
            "drafting content", "revision", "tone control", "outlining",
            "copy preparation", "style adaptation", "creative brainstorming",
            "formatting content", "audience targeting",
        ],
        "out_of_scope": [
            "fact verification", "code execution", "file publishing without approval",
            "sending emails", "external API calls", "tool invocation",
        ],
    },
    "Coder": {
        "within_scope": [
            "code explanation", "code drafting", "diff preview", "test planning",
            "bug diagnosis", "code review", "risk identification", "architecture suggestion",
            "optimization suggestions", "security scanning",
        ],
        "out_of_scope": [
            "auto-applying", "executing code without approval", "file write",
            "file modification", "modify files", "deployment", "external network",
            "installing", "auto-executing", "bypass approval",
        ],
    },
    "Planner": {
        "within_scope": [
            "goal decomposition", "task breakdown", "milestone planning",
            "risk assessment", "dependency mapping", "timeline creation",
            "prioritization", "schedule optimization",
        ],
        "out_of_scope": [
            "executing tasks", "file operations", "external commitments",
            "tool invocation", "code execution", "sending messages",
        ],
    },
    "Notebook": {
        "within_scope": [
            "note capture", "tagging", "recall", "search", "summarization",
            "continuity management", "knowledge organization", "context retrieval",
        ],
        "out_of_scope": [
            "bulk deletion without approval", "export without approval",
            "external publishing", "file system operations", "tool execution",
        ],
    },
    "Document Processor": {
        "within_scope": [
            "document analysis", "summarization", "extraction", "classification",
            "comparison", "action item identification", "sensitive content flagging",
        ],
        "out_of_scope": [
            "altering source documents", "export without approval", "publishing",
            "tool execution", "external API calls", "code execution",
        ],
    },
    "Archive": {
        "within_scope": [
            "artifact storage", "retrieval", "indexing", "tagging",
            "lifecycle management proposals", "historical reference",
        ],
        "out_of_scope": [
            "deleting without approval", "moving files without approval",
            "bulk export without approval", "external publishing", "tool execution",
        ],
    },
    "Tool User": {
        "within_scope": [
            "tool proposal", "rationale explanation", "risk assessment",
            "invocation scaffolding", "tool chain design", "integration assessment",
        ],
        "out_of_scope": [
            "auto-invoking tools", "executing without approval", "bypassing approval gates",
            "external network access without approval", "installing software",
        ],
    },
    "Tutor": {
        "within_scope": [
            "explanation", "quizzes", "study guides", "practice exercises",
            "level assessment", "learning paths", "educational feedback",
            "knowledge checking",
        ],
        "out_of_scope": [
            "dishonest", "cheating", "grading without review",
            "file export without approval", "external publishing", "tool execution",
            "auto-executing", "file modification", "modify files",
        ],
    },
    "Business Workflow": {
        "within_scope": [
            "SOP creation", "checklist generation", "support drafting",
            "handoff preparation", "workflow mapping", "automation proposals",
            "process documentation", "compliance checking",
        ],
        "out_of_scope": [
            "auto-sending messages", "auto-executing workflows", "publishing without approval",
            "external system changes", "tool execution without approval",
        ],
    },
    "Hephaestus Relay": {
        "within_scope": [
            "design brief creation", "constraint analysis", "unknown identification",
            "handoff packet preparation", "requirement structuring",
        ],
        "out_of_scope": [
            "modifying internal systems", "executing designs", "tool invocation",
            "external API calls", "code execution", "file modification",
        ],
    },

    # ─── New capability scope zones ───────────────────────────────────

    "Activity Watcher": {
        "within_scope": [
            "pattern observation", "task learning", "efficiency suggestion",
            "workflow analysis", "task repetition", "improvement suggestion",
            "activity monitoring", "habit detection",
        ],
        "out_of_scope": [
            "auto-executing", "auto-applying", "bypass approval", "file modification",
            "modify files", "file write", "external network", "installing",
            "tool execution without approval", "code execution",
        ],
    },
    "Financial Gainer": {
        "within_scope": [
            "income opportunity", "side hustle", "monetization", "financial advisory",
            "ROI estimation", "skill monetization", "income path", "financial planning",
            "opportunity research", "market analysis",
        ],
        "out_of_scope": [
            "guarantee income", "promise earnings", "auto-executing", "file modification",
            "modify files", "file write", "tool execution", "external API calls",
            "making transactions", "investment execution", "bypass approval",
            "illegal", "unethical",
        ],
    },
    "Memory Recorder": {
        "within_scope": [
            "session recording", "audit trail", "event logging", "search and replay",
            "compliance export", "recording management", "activity log",
            "session timeline", "auditability", "recollection",
        ],
        "out_of_scope": [
            "auto-executing", "file modification", "modify files", "tool execution",
            "external publishing", "external API calls", "bypass approval",
            "recording passwords", "recording credentials",
        ],
    },
    "Game Companion": {
        "within_scope": [
            "game rules", "strategy suggestion", "position analysis", "practice game",
            "game analysis", "skill assessment", "move commentary",
            "game teaching", "cognitive skills",
        ],
        "out_of_scope": [
            "auto-executing", "file modification", "modify files", "file write",
            "tool execution", "external API calls", "code execution",
            "external network", "bypass approval", "cheating",
        ],
    },
    # ─── Phase 5 Capabilities ──────────────────────────────────────────
    "Email Automation": {
        "within_scope": [
            "email drafting", "inbox organization", "email templates",
            "campaign planning", "follow-up sequences", "mail merge",
            "email scheduling suggestions", "compliance reminders",
        ],
        "out_of_scope": [
            "auto-sending", "auto-executing", "file modification", "modify files",
            "bypass approval", "credential theft", "phishing",
        ],
    },
    "API Integrator": {
        "within_scope": [
            "api connection guidance", "webhook setup", "integration planning",
            "security checklists", "configuration guidance", "debugging frameworks",
        ],
        "out_of_scope": [
            "hardcode api keys", "auto-executing", "file modification", "modify files",
            "bypass approval", "credential exposure", "unauthorized access",
        ],
    },
    "Team Orchestrator": {
        "within_scope": [
            "task decomposition", "ai coordination", "workflow design",
            "handoff specifications", "execution planning", "coordination plans",
        ],
        "out_of_scope": [
            "auto-executing", "file modification", "modify files", "file write",
            "tool execution", "bypass approval", "unauthorized access",
        ],
    },
    "Voice Interface": {
        "within_scope": [
            "voice commands", "dictation", "text-to-speech", "voice configuration",
            "transcription", "voice input processing", "speech recognition",
        ],
        "out_of_scope": [
            "auto-executing", "file modification", "modify files", "file write",
            "bypass approval", "unauthorized recording", "always listening without consent",
        ],
    },
    "Visual Canvas": {
        "within_scope": [
            "diagrams", "mind maps", "flowcharts", "visual layouts",
            "text-based visual representations", "structural guidance",
            "drawing guidance", "visual organization",
        ],
        "out_of_scope": [
            "auto-executing", "file modification", "modify files", "file write",
            "tool execution", "bypass approval", "external network",
        ],
    },
    "Medical Researcher": {
        "within_scope": [
            "medical literature", "clinical trials", "drug interactions",
            "evidence quality", "medical research", "pharmaceutical research",
            "epidemiology", "medical evidence",
        ],
        "out_of_scope": [
            "diagnosing", "prescribing", "treatment recommendation", "auto-executing",
            "file modification", "modify files", "bypass approval",
            "patient data access", "hipaa violation",
        ],
    },
    "Legal Document Reviewer": {
        "within_scope": [
            "document analysis", "clause identification", "provision extraction",
            "contract review", "legal document text analysis",
            "what is written in document", "legal text summary",
        ],
        "out_of_scope": [
            "legal advice", "legal opinion", "case law research", "auto-executing",
            "file modification", "modify files", "bypass approval",
            "external research", "interpretation beyond text",
        ],
    },
    # ─── Phase 6 Capabilities ──────────────────────────────────────────
    "Wellness Coach": {
        "within_scope": [
            "fitness planning", "nutrition guidance", "mental wellness",
            "habit building", "exercise routines", "meal suggestions",
            "stress management", "sleep hygiene", "wellness tracking",
        ],
        "out_of_scope": [
            "medical diagnosis", "prescribing medication", "treatment recommendation",
            "auto-executing", "file modification", "modify files", "bypass approval",
        ],
    },
    "Content Strategist": {
        "within_scope": [
            "content calendar", "audience analysis", "platform optimization",
            "content repurposing", "brand voice", "editorial planning",
            "engagement strategy", "content marketing",
        ],
        "out_of_scope": [
            "auto-publishing", "auto-scheduling", "auto-executing", "file modification",
            "modify files", "bypass approval", "social media auto-posting",
        ],
    },
    "Fact Checker": {
        "within_scope": [
            "claim verification", "source checking", "credibility assessment",
            "bias detection", "fact checking", "misinformation detection",
            "accuracy checking", "evidence evaluation",
        ],
        "out_of_scope": [
            "auto-executing", "file modification", "modify files", "file write",
            "bypass approval", "external network without approval",
        ],
    },
    # ─── Phase 7 Capabilities ──────────────────────────────────────────
    "Task Scheduler": {
        "within_scope": [
            "scheduling", "time blocking", "reminder planning", "appointment scheduling",
            "calendar suggestions", "priority ranking", "time management",
        ],
        "out_of_scope": [
            "auto-scheduling", "auto-executing", "calendar modification without approval",
            "file modification", "modify files", "bypass approval",
        ],
    },
    "Form Builder": {
        "within_scope": [
            "form design", "survey creation", "questionnaire structure",
            "question types", "form fields", "form templates", "survey flow",
        ],
        "out_of_scope": [
            "auto-publishing", "auto-executing", "file modification", "modify files",
            "bypass approval", "data collection without consent",
        ],
    },
    "Report Generator": {
        "within_scope": [
            "report creation", "executive summaries", "findings compilation",
            "recommendations", "report formatting", "structured reports",
        ],
        "out_of_scope": [
            "auto-distributing", "auto-executing", "file modification", "modify files",
            "bypass approval", "external network",
        ],
    },
    "Invoice Processor": {
        "within_scope": [
            "invoice creation", "billing", "calculation", "payment terms",
            "invoice formatting", "tax calculation", "line items",
        ],
        "out_of_scope": [
            "auto-sending", "auto-executing", "payment processing", "file modification",
            "modify files", "bypass approval", "banking access",
        ],
    },
    "Spreadsheet Analyst": {
        "within_scope": [
            "spreadsheet formulas", "pivot tables", "data analysis",
            "cell references", "conditional formatting", "spreadsheet guidance",
        ],
        "out_of_scope": [
            "auto-executing", "file modification", "modify files", "file write",
            "bypass approval", "external data access",
        ],
    },
    "Data Visualizer": {
        "within_scope": [
            "chart recommendations", "visualization strategy", "graph types",
            "data visualization", "design tips", "visual data representation",
        ],
        "out_of_scope": [
            "auto-executing", "file modification", "modify files", "file write",
            "bypass approval", "external data access",
        ],
    },
    "Statistical Modeler": {
        "within_scope": [
            "regression", "hypothesis testing", "statistical analysis",
            "correlation", "confidence intervals", "anova", "t-test",
            "statistical modeling", "effect sizes",
        ],
        "out_of_scope": [
            "auto-executing", "file modification", "modify files", "file write",
            "bypass approval", "external data access",
        ],
    },
    "Trend Forecaster": {
        "within_scope": [
            "forecasting", "trend analysis", "prediction", "projection",
            "time series", "demand forecasting", "growth projection",
        ],
        "out_of_scope": [
            "auto-executing", "file modification", "modify files", "file write",
            "bypass approval", "external data access", "guaranteeing returns",
        ],
    },
    "DevOps Assistant": {
        "within_scope": [
            "ci/cd", "docker", "kubernetes", "infrastructure guidance",
            "deployment strategy", "pipeline design", "containerization",
        ],
        "out_of_scope": [
            "production deployment", "auto-executing", "file modification", "modify files",
            "bypass approval", "credential exposure", "destructive commands",
        ],
    },
    "Database Manager": {
        "within_scope": [
            "schema design", "query optimization", "migration planning",
            "sql queries", "database design", "table structure",
        ],
        "out_of_scope": [
            "destructive queries", "auto-executing", "file modification", "modify files",
            "bypass approval", "data exfiltration", "production database access",
        ],
    },
    "Test Generator": {
        "within_scope": [
            "unit tests", "integration tests", "test cases", "edge cases",
            "test coverage", "mock tests", "test suites", "assertions",
        ],
        "out_of_scope": [
            "auto-executing", "test execution without approval", "file modification",
            "modify files", "bypass approval",
        ],
    },
    "Documentation Generator": {
        "within_scope": [
            "api documentation", "readmes", "user guides", "code documentation",
            "docstrings", "technical documentation", "sdk docs",
        ],
        "out_of_scope": [
            "auto-executing", "file modification without approval", "modify files",
            "bypass approval", "external network",
        ],
    },
    "Script Writer": {
        "within_scope": [
            "automation scripts", "python scripts", "shell scripts", "powershell",
            "batch scripts", "error handling", "script comments",
        ],
        "out_of_scope": [
            "malware", "auto-executing", "script execution without approval",
            "file modification", "modify files", "bypass approval",
            "unauthorized access", "reverse shells",
        ],
    },
    "Copy Editor": {
        "within_scope": [
            "grammar", "style", "clarity", "tone", "proofreading",
            "line editing", "copy editing", "manuscript editing",
        ],
        "out_of_scope": [
            "auto-publishing", "auto-executing", "file modification", "modify files",
            "bypass approval",
        ],
    },
    "Podcast Planner": {
        "within_scope": [
            "podcast planning", "episode structure", "show notes",
            "segment breakdown", "podcast topics", "podcast format",
        ],
        "out_of_scope": [
            "auto-publishing", "auto-executing", "file modification", "modify files",
            "bypass approval",
        ],
    },
    "Brand Strategist": {
        "within_scope": [
            "brand identity", "brand positioning", "brand values",
            "brand personality", "brand voice", "rebranding", "brand audit",
        ],
        "out_of_scope": [
            "auto-executing", "file modification", "modify files", "file write",
            "bypass approval", "external network",
        ],
    },
    "Presentation Coach": {
        "within_scope": [
            "presentation structure", "talking points", "delivery coaching",
            "public speaking", "slide review", "pitch deck", "speech coaching",
        ],
        "out_of_scope": [
            "auto-executing", "file modification", "modify files", "file write",
            "bypass approval",
        ],
    },
    "PR Assistant": {
        "within_scope": [
            "press releases", "media pitches", "crisis communication",
            "public relations", "media relations", "pr strategy", "press kits",
        ],
        "out_of_scope": [
            "auto-distributing", "auto-sending", "auto-executing", "file modification",
            "modify files", "bypass approval", "deceptive content",
        ],
    },
    "Internal Comms Writer": {
        "within_scope": [
            "company announcements", "team updates", "internal memos",
            "change management", "employee newsletters", "staff communications",
        ],
        "out_of_scope": [
            "auto-distributing", "auto-sending", "auto-executing", "file modification",
            "modify files", "bypass approval",
        ],
    },
    "Academic Citation Manager": {
        "within_scope": [
            "citation formatting", "bibliography", "reference lists",
            "apa", "mla", "chicago", "citation style", "works cited",
        ],
        "out_of_scope": [
            "auto-executing", "file modification", "modify files", "file write",
            "bypass approval",
        ],
    },
    "Patent Researcher": {
        "within_scope": [
            "prior art search", "patent research", "patent claims",
            "intellectual property", "patent databases", "search strategy",
        ],
        "out_of_scope": [
            "legal advice", "patentability opinion", "auto-executing",
            "file modification", "modify files", "bypass approval",
            "filing patents",
        ],
    },
    "Market Analyst": {
        "within_scope": [
            "market analysis", "competitor analysis", "market size",
            "market trends", "competitive landscape", "tam sam som",
            "industry analysis", "market opportunities",
        ],
        "out_of_scope": [
            "auto-executing", "file modification", "modify files", "file write",
            "bypass approval", "external network without approval",
        ],
    },
    "Recipe Planner": {
        "within_scope": [
            "meal planning", "recipes", "meal prep", "cooking suggestions",
            "shopping lists", "dietary preferences", "nutrition balance",
        ],
        "out_of_scope": [
            "auto-executing", "file modification", "modify files", "file write",
            "bypass approval",
        ],
    },
    "Travel Planner": {
        "within_scope": [
            "travel itineraries", "trip planning", "activity suggestions",
            "travel logistics", "budget planning", "travel tips",
        ],
        "out_of_scope": [
            "auto-booking", "auto-executing", "file modification", "modify files",
            "bypass approval", "external transactions",
        ],
    },
    "Event Planner": {
        "within_scope": [
            "event planning", "timeline", "logistics", "checklists",
            "budget estimation", "venue suggestions", "contingency planning",
        ],
        "out_of_scope": [
            "auto-booking", "auto-executing", "file modification", "modify files",
            "bypass approval", "external transactions",
        ],
    },
    "Personal Finance Manager": {
        "within_scope": [
            "budgeting", "debt repayment", "savings goals", "expense tracking",
            "financial planning", "money management", "financial guidance",
        ],
        "out_of_scope": [
            "trade execution", "fund transfer", "banking access", "auto-executing",
            "file modification", "modify files", "bypass approval",
            "investment transactions", "financial advice guarantee",
        ],
    },
    "Privacy Compliance Checker": {
        "within_scope": [
            "gdpr", "ccpa", "privacy policy", "data privacy",
            "privacy regulation", "compliance guidance", "data protection",
        ],
        "out_of_scope": [
            "legal certification", "legal opinion", "guaranteed compliance",
            "auto-executing", "file modification", "modify files", "bypass approval",
        ],
    },
    "Data Governance Advisor": {
        "within_scope": [
            "data governance", "data stewardship", "data quality",
            "data catalog", "data lineage", "governance framework",
            "data classification", "data retention",
        ],
        "out_of_scope": [
            "auto-executing", "file modification", "modify files", "file write",
            "bypass approval", "policy deployment without approval",
        ],
    },
    "Curriculum Designer": {
        "within_scope": [
            "curriculum design", "course creation", "learning objectives",
            "module structure", "lesson planning", "assessment design",
            "syllabus", "educational program",
        ],
        "out_of_scope": [
            "auto-executing", "file modification", "modify files", "file write",
            "bypass approval",
        ],
    },
    "Exam Prep Coach": {
        "within_scope": [
            "exam preparation", "study plans", "practice strategies",
            "test-taking tips", "exam coaching", "study schedules",
            "practice tests", "certification prep",
        ],
        "out_of_scope": [
            "auto-executing", "file modification", "modify files", "file write",
            "bypass approval", "cheating",
        ],
    },
}


# ─── Capability Memory ─────────────────────────────────────────────────

@dataclass
class MemoryEntry:
    """A single learned memory entry for a capability."""
    key: str
    value: str
    category: str           # e.g., "user_preference", "learned_pattern", "use_case"
    created_at: float
    updated_at: float
    source: str = "ai"      # "ai" or "user"
    confidence: float = 1.0 # 0.0 to 1.0


class CapabilityMemory:
    """
    Per-capability persistent memory.

    The AI can add, update, and query memories for each capability.
    All updates are validated against the capability's scope zone.

    Memory is stored in a JSON file per capability:
      ~/.command_nexus/capability_memory/{capability_slug}.json
    """

    def __init__(self, capability: str, storage_dir: Optional[Path] = None):
        self.capability = capability
        self._entries: dict[str, MemoryEntry] = {}

        if storage_dir is None:
            storage_dir = Path.home() / ".command_nexus" / "capability_memory"
        self._storage_dir = storage_dir
        self._storage_dir.mkdir(parents=True, exist_ok=True)

        self._load()

    @property
    def _storage_path(self) -> Path:
        slug = self.capability.lower().replace(" ", "_")
        return self._storage_dir / f"{slug}.json"

    def _load(self) -> None:
        """Load memory from disk."""
        if not self._storage_path.exists():
            return
        try:
            data = json.loads(self._storage_path.read_text(encoding="utf-8"))
            for key, entry_data in data.items():
                self._entries[key] = MemoryEntry(
                    key=key,
                    value=entry_data["value"],
                    category=entry_data["category"],
                    created_at=entry_data["created_at"],
                    updated_at=entry_data["updated_at"],
                    source=entry_data.get("source", "ai"),
                    confidence=entry_data.get("confidence", 1.0),
                )
        except Exception:
            pass

    def _save(self) -> None:
        """Save memory to disk."""
        data = {}
        for key, entry in self._entries.items():
            data[key] = {
                "value": entry.value,
                "category": entry.category,
                "created_at": entry.created_at,
                "updated_at": entry.updated_at,
                "source": entry.source,
                "confidence": entry.confidence,
            }
        try:
            self._storage_path.write_text(
                json.dumps(data, indent=2), encoding="utf-8"
            )
        except Exception:
            pass

    def get(self, key: str) -> Optional[str]:
        """Retrieve a memory value by key."""
        entry = self._entries.get(key)
        return entry.value if entry else None

    def get_all(self) -> dict[str, MemoryEntry]:
        """Return all memory entries."""
        return dict(self._entries)

    def get_by_category(self, category: str) -> dict[str, str]:
        """Return all memories in a specific category."""
        return {
            k: v.value for k, v in self._entries.items()
            if v.category == category
        }

    def update(self, key: str, value: str, category: str = "learned",
               source: str = "ai", confidence: float = 1.0) -> bool:
        """Add or update a memory entry.

        Returns True if the update was accepted, False if rejected
        (e.g., out of scope).
        """
        # Validate the update is within the capability's scope
        if not validate_capability_update(self.capability, value):
            return False

        now = time.time()
        if key in self._entries:
            entry = self._entries[key]
            entry.value = value
            entry.updated_at = now
            entry.source = source
            entry.confidence = confidence
        else:
            self._entries[key] = MemoryEntry(
                key=key,
                value=value,
                category=category,
                created_at=now,
                updated_at=now,
                source=source,
                confidence=confidence,
            )
        self._save()
        return True

    def remove(self, key: str) -> bool:
        """Remove a memory entry."""
        if key in self._entries:
            del self._entries[key]
            self._save()
            return True
        return False

    def clear(self) -> None:
        """Clear all memory entries."""
        self._entries.clear()
        self._save()

    def to_prompt_context(self) -> str:
        """Format memory as context text for the AI prompt.

        This is what gets injected into the AI's book so it knows
        what it has learned about this capability.
        """
        if not self._entries:
            return ""

        lines = [f"### Learned Memory for {self.capability}", ""]
        by_category: dict[str, list[MemoryEntry]] = {}
        for entry in self._entries.values():
            by_category.setdefault(entry.category, []).append(entry)

        for category, entries in sorted(by_category.items()):
            lines.append(f"**{category.replace('_', ' ').title()}:**")
            for entry in sorted(entries, key=lambda e: e.updated_at, reverse=True):
                conf_label = "high" if entry.confidence >= 0.8 else "medium" if entry.confidence >= 0.5 else "low"
                lines.append(f"- {entry.key}: {entry.value} (confidence: {conf_label})")
            lines.append("")

        return "\n".join(lines)


# ─── Scope Validation ──────────────────────────────────────────────────

def validate_capability_update(capability: str, proposed_content: str) -> bool:
    """Validate that a proposed memory update is within the capability's scope.

    Checks the proposed content against the capability's scope zone.
    If the content mentions or implies out-of-scope activities, it's rejected.

    A memory is accepted if:
    - It does NOT contain any out-of-scope keywords
    - It contains at least one in-scope keyword OR is a general preference/note
      that doesn't trigger any out-of-scope keywords

    Returns True if within scope, False if out of scope.
    """
    scope = CAPABILITY_SCOPE.get(capability)
    if scope is None:
        # Unknown capability — reject by default
        return False

    content_lower = proposed_content.lower()

    # Check for out-of-scope keywords — if found, reject
    for forbidden in scope["out_of_scope"]:
        if forbidden in content_lower:
            return False

    # No out-of-scope keywords found — accept
    # (We don't require in-scope keywords because memories like
    # "user prefers academic papers" are valid even though "academic papers"
    # isn't a literal in-scope keyword — it's a preference about sources,
    # which is within the Research capability's zone)
    return True


# ─── Scenario Retrieval for AI ─────────────────────────────────────────

def get_scenarios_for_capability(capability: str) -> list[CapabilityScenario]:
    """Return all scenarios for a given capability."""
    return CAPABILITY_SCENARIOS.get(capability, [])


def get_scenarios_as_prompt_text(capability: str) -> str:
    """Format scenarios as text for the AI prompt/book.

    This gives the AI concrete reference points for what to do
    with this capability in different situations.
    """
    scenarios = CAPABILITY_SCENARIOS.get(capability, [])
    if not scenarios:
        return ""

    lines = [f"### Scenarios for {capability}", ""]
    for scenario in scenarios:
        lines.append(f"**{scenario.title}** (`{scenario.scenario_id}`)")
        lines.append(f"- When: {scenario.trigger}")
        lines.append(f"- Action: {scenario.expected_action}")
        lines.append(f"- Output: {scenario.expected_output}")
        if scenario.capabilities_needed:
            lines.append(f"- May involve: {', '.join(scenario.capabilities_needed)}")
        if scenario.approval_required:
            lines.append("- **Approval required for outward actions**")
        if scenario.notes:
            lines.append(f"- Note: {scenario.notes}")
        lines.append("")

    return "\n".join(lines)


def get_all_scenarios_as_prompt_text(capabilities: list[str]) -> str:
    """Get scenarios for multiple capabilities, formatted for the AI book."""
    sections = ["## Capability Scenarios", ""]
    for cap in capabilities:
        text = get_scenarios_as_prompt_text(cap)
        if text:
            sections.append(text)
    sections.append("---")
    sections.append("")
    return "\n".join(sections)


# ─── Memory Manager (handles all capabilities) ─────────────────────────

class CapabilityMemoryManager:
    """
    Manages capability memory across all capabilities.

    Provides a unified interface for the AI to:
    - Query memories per capability
    - Update memories (with scope validation)
    - Get combined prompt context for the AI book
    """

    _instance: Optional["CapabilityMemoryManager"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, storage_dir: Optional[Path] = None):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True
        self._storage_dir = storage_dir
        self._memories: dict[str, CapabilityMemory] = {}

    def get_memory(self, capability: str) -> CapabilityMemory:
        """Get or create the memory store for a capability."""
        if capability not in self._memories:
            self._memories[capability] = CapabilityMemory(capability, self._storage_dir)
        return self._memories[capability]

    def update_memory(self, capability: str, key: str, value: str,
                      category: str = "learned", source: str = "ai",
                      confidence: float = 1.0) -> bool:
        """Update a capability's memory. Returns True if accepted, False if out of scope."""
        mem = self.get_memory(capability)
        return mem.update(key, value, category, source, confidence)

    def get_memory_value(self, capability: str, key: str) -> Optional[str]:
        """Retrieve a specific memory value."""
        mem = self.get_memory(capability)
        return mem.get(key)

    def get_all_memory_as_prompt_text(self, capabilities: list[str]) -> str:
        """Get all capability memories formatted for the AI book."""
        sections = ["## Capability Memory (Learned)", ""]
        any_memory = False
        for cap in capabilities:
            mem = self.get_memory(cap)
            text = mem.to_prompt_context()
            if text:
                sections.append(text)
                any_memory = True
        if not any_memory:
            sections.append("No learned memories yet.")
        sections.append("---")
        sections.append("")
        return "\n".join(sections)

    def clear_capability_memory(self, capability: str) -> None:
        """Clear all memory for a capability."""
        mem = self.get_memory(capability)
        mem.clear()


def get_memory_manager() -> CapabilityMemoryManager:
    """Get the singleton CapabilityMemoryManager."""
    return CapabilityMemoryManager()
