# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

"""
Chat Parameter Gatherer
=======================
Conversational flow that intercepts user messages in the Chat Companion,
classifies intent, asks for any missing parameters the capability needs,
and then executes once everything is collected.

This makes the Chat Companion the universal interface for ALL capabilities.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

# ─── Canonical intent mapping ───────────────────────────────────────
# The runtime's capability_registry.py maps user-facing capability names
# to canonical runtime intents. We must use the SAME canonical names
# so the runtime dispatches correctly.
INTENT_TO_CANONICAL: dict[str, str] = {
    "Chat Companion": "Chatbot",
    "Chat": "Chatbot",
    "Research": "Research",
    "Coder": "Coder",
    "Creative Writing": "Creative Writing",
    "Planner": "Planner",
    "Document Processor": "Document Processor",
    "Notebook": "Notebook",
    "Archive": "Archive",
    "Tutor": "Tutor",
    "Business Workflow": "Business Workflow",
    "Tool User": "Tool User",
    "Customer Support AI": "Customer Support AI",
    "Hephaestus Relay": "Hephaestus Relay",
    "Data Analyst Pro": "Data Analyst Pro",
    "Code Reviewer": "Code Reviewer",
    "Meeting Facilitator": "Meeting Facilitator",
    "Security Auditor": "Security Auditor",
    # These map to PAUSED canonical intents in the runtime:
    "Email Automation": "Email",
    "API Integrator": "API",
    "Team Orchestrator": "Team",
    # These map to existing canonical intents via capability_registry aliases:
    "Calendar Manager": "Planner",
    "Document Generator": "Document Processor",
    "Translation Expert": "Tutor",
    "Presentation Builder": "Creative Writing",
    "Spreadsheet Wizard": "Document Processor",
    "Legal Assistant": "Business Workflow",
    "Medical Researcher": "Business Workflow",
    "Accessibility Assistant": "Tutor",
    "Fact Checker": "Research",
    "Voice Interface": "Voice",
    "Workflow Automator": "Planner",
    "Competitive Analyst": "Research",
    "Learning Path Creator": "Tutor",
    "Smart Search": "Research",
    "Memory Bridge": "Archive",
    "Visual Canvas": "Vision",
    "Knowledge Base Builder": "Archive",
    # Enterprise Orchestrator — distinct from Business Workflow
    "Enterprise Orchestrator": "Enterprise Orchestrator",
    "Policy Review Orchestrator": "Enterprise Orchestrator",
    "Compliance Orchestrator": "Enterprise Orchestrator",
    "Operations Orchestrator": "Enterprise Orchestrator",
    "HR Orchestrator": "Enterprise Orchestrator",
    "Cross-Department Coordinator": "Enterprise Orchestrator",
    "Executive Brief Generator": "Enterprise Orchestrator",
    "Enterprise Analytics": "Enterprise Orchestrator",
}

# Capabilities that are PAUSED in the current build — we still gather params
# but the runtime will return an honest "paused" message.
PAUSED_INTENTS = {"Email", "API", "Team", "Hephaestus Relay", "Browser"}


@dataclass
class ParameterSpec:
    """Definition of a single parameter a capability needs."""
    name: str
    prompt: str
    required: bool = True
    default: str = ""
    placeholder: str = ""
    validator: Optional[Callable[[str], bool]] = None
    hint: str = ""


@dataclass
class GatherState:
    """Tracks an in-progress parameter gathering session."""
    intent: str
    params: dict[str, str] = field(default_factory=dict)
    current_param: str = ""
    waiting: bool = False
    original_message: str = ""


# ─── Intent → Parameter Definitions ───────────────────────────────────

INTENT_PARAMETERS: dict[str, list[ParameterSpec]] = {
    "Research": [
        ParameterSpec(
            name="query",
            prompt="What would you like me to research?",
            required=True,
            hint="Be specific — e.g., 'Compare Python async web frameworks' rather than just 'Python frameworks'.",
        ),
        ParameterSpec(
            name="scope",
            prompt="Any scope constraints? (e.g., 'last 2 years', 'academic only', 'free tools only') — or type 'skip'",
            required=False,
            placeholder="skip",
            hint="Narrowing scope gives you better results.",
        ),
        ParameterSpec(
            name="format",
            prompt="How would you like the results? (summary, bullet points, comparison table) — or type 'skip' for summary",
            required=False,
            default="summary",
            placeholder="summary",
        ),
    ],
    "Coder": [
        ParameterSpec(
            name="description",
            prompt="Describe the code issue or feature you need help with.",
            required=True,
            hint="Paste the error message, describe the bug, or explain what you want to build.",
        ),
        ParameterSpec(
            name="file_path",
            prompt="Which file are you working with? (full path, or type 'paste code' if you'll paste it) — or type 'skip'",
            required=False,
            placeholder="skip",
            hint="Providing a file path lets me read and analyze the actual code.",
        ),
        ParameterSpec(
            name="action",
            prompt="What do you need? (explain, draft diff, outline tests, approved edit) — or type 'skip' for explain",
            required=False,
            default="explain",
            placeholder="explain",
        ),
    ],
    "Creative Writing": [
        ParameterSpec(
            name="topic",
            prompt="What would you like me to write about?",
            required=True,
            hint="The topic, subject, or idea for the content.",
        ),
        ParameterSpec(
            name="tone",
            prompt="What tone? (professional, casual, persuasive, technical, humorous) — or type 'skip' for professional",
            required=False,
            default="professional",
            placeholder="professional",
        ),
        ParameterSpec(
            name="audience",
            prompt="Who is the audience? (general public, technical, executive, academic) — or type 'skip' for general",
            required=False,
            default="general public",
            placeholder="general public",
        ),
        ParameterSpec(
            name="format",
            prompt="What format? (article, blog post, email, social media post, script, story) — or type 'skip' for article",
            required=False,
            default="article",
            placeholder="article",
        ),
    ],
    "Planner": [
        ParameterSpec(
            name="goal",
            prompt="What's the goal or project you want to plan?",
            required=True,
            hint="Be specific about what 'done' looks like.",
        ),
        ParameterSpec(
            name="timeline",
            prompt="Any timeline constraints? (e.g., '2 weeks', 'end of Q3') — or type 'skip'",
            required=False,
            placeholder="skip",
        ),
        ParameterSpec(
            name="constraints",
            prompt="Any known constraints, risks, or dependencies? — or type 'skip'",
            required=False,
            placeholder="skip",
        ),
    ],
    "Document Processor": [
        ParameterSpec(
            name="input",
            prompt="Paste the document text, or provide a file path to process.",
            required=True,
            hint="You can paste text directly or give a full file path like C:/Docs/report.pdf",
        ),
        ParameterSpec(
            name="action",
            prompt="What should I do with it? (summarize, extract action items, classify, compare) — or type 'skip' for summarize",
            required=False,
            default="summarize",
            placeholder="summarize",
        ),
    ],
    "Notebook": [
        ParameterSpec(
            name="title",
            prompt="What title should I give this note?",
            required=True,
        ),
        ParameterSpec(
            name="tags",
            prompt="Any tags? (comma-separated, e.g., 'project, urgent, meeting') — or type 'skip'",
            required=False,
            placeholder="skip",
        ),
        ParameterSpec(
            name="body",
            prompt="What's the content of the note?",
            required=True,
        ),
    ],
    "Archive": [
        ParameterSpec(
            name="artifact_name",
            prompt="What name should I archive this under?",
            required=True,
        ),
        ParameterSpec(
            name="tags",
            prompt="Any tags for retrieval? (comma-separated) — or type 'skip'",
            required=False,
            placeholder="skip",
        ),
        ParameterSpec(
            name="content",
            prompt="What content should I archive? (paste text or describe the result to store)",
            required=True,
        ),
    ],
    "Tutor": [
        ParameterSpec(
            name="topic",
            prompt="What topic would you like to learn about?",
            required=True,
        ),
        ParameterSpec(
            name="mode",
            prompt="What mode? (explain step by step, quiz me, make a study sheet) — or type 'skip' for explain",
            required=False,
            default="explain step by step",
            placeholder="explain step by step",
        ),
        ParameterSpec(
            name="level",
            prompt="What's your current level? (beginner, intermediate, advanced) — or type 'skip' for intermediate",
            required=False,
            default="intermediate",
            placeholder="intermediate",
        ),
    ],
    "Business Workflow": [
        ParameterSpec(
            name="workflow_type",
            prompt="What type of workflow? (SOP, checklist, support reply, handoff document) — or type 'skip' for SOP",
            required=False,
            default="SOP",
            placeholder="SOP",
        ),
        ParameterSpec(
            name="subject",
            prompt="What's the subject or process? (e.g., 'customer onboarding', 'weekly report')",
            required=True,
        ),
        ParameterSpec(
            name="audience",
            prompt="Who is this for? (team, management, customer) — or type 'skip' for team",
            required=False,
            default="team",
            placeholder="team",
        ),
    ],
    "Enterprise Orchestrator": [
        ParameterSpec(
            name="objective",
            prompt="What's the enterprise objective? (e.g., 'coordinate onboarding for 15 new hires', 'run GDPR compliance audit for Q3')",
            required=True,
            hint="Describe the cross-department or enterprise-level task you need orchestrated.",
        ),
        ParameterSpec(
            name="sub_workflow",
            prompt="Which sub-workflow? (HR, Compliance, Policy Review, Operations, Analytics, Executive Brief, Cross-Department) — or type 'skip' for auto-detect",
            required=False,
            default="auto",
            placeholder="auto",
        ),
        ParameterSpec(
            name="department_scope",
            prompt="Which departments are involved? (e.g., 'HR, IT, Facilities') — or type 'skip' for all",
            required=False,
            default="all",
            placeholder="all",
        ),
        ParameterSpec(
            name="priority",
            prompt="What priority level? (P1-Critical, P2-High, P3-Medium, P4-Low) — or type 'skip' for P3",
            required=False,
            default="P3",
            placeholder="P3",
        ),
    ],
    "Tool User": [
        ParameterSpec(
            name="action_description",
            prompt="What action do you want me to perform?",
            required=True,
            hint="e.g., 'read file C:/data.txt', 'list files in D:/projects', 'run command python test.py'",
        ),
        # Note: The runtime has its own approval gate (_request_tool_approval)
        # so we don't need a separate confirmation step in the gatherer.
        # Confirmation is kept as an optional parameter for awareness.
        ParameterSpec(
            name="confirmation",
            prompt="This will require approval before execution. Type 'proceed' to continue, or 'cancel' to abort.",
            required=False,
            default="proceed",
            validator=lambda v: v.lower().strip() in ("proceed", "yes", "y", "go", "ok", "continue"),
            hint="Tool actions are approval-gated for your safety.",
        ),
    ],
    "Customer Support AI": [
        ParameterSpec(
            name="inquiry",
            prompt="What's the customer's question or issue?",
            required=True,
        ),
        ParameterSpec(
            name="context",
            prompt="Any additional context? (customer tier, previous tickets, account info) — or type 'skip'",
            required=False,
            placeholder="skip",
        ),
    ],
    "Hephaestus Relay": [
        ParameterSpec(
            name="idea",
            prompt="Describe the design idea or concept you want to develop.",
            required=True,
        ),
        ParameterSpec(
            name="constraints",
            prompt="Any known constraints? (materials, size, budget, environment) — or type 'skip'",
            required=False,
            placeholder="skip",
        ),
        ParameterSpec(
            name="purpose",
            prompt="What's the intended purpose or use case? — or type 'skip'",
            required=False,
            placeholder="skip",
        ),
    ],
    "Data Analyst Pro": [
        ParameterSpec(
            name="data_source",
            prompt="Where's the data? (paste CSV data, or provide a file path like C:/data/sales.csv)",
            required=True,
        ),
        ParameterSpec(
            name="analysis_type",
            prompt="What kind of analysis? (trends, summary statistics, comparison, forecast) — or type 'skip' for summary",
            required=False,
            default="summary",
            placeholder="summary",
        ),
    ],
    "Code Reviewer": [
        ParameterSpec(
            name="code_input",
            prompt="Paste the code to review, or provide a file path.",
            required=True,
        ),
        ParameterSpec(
            name="focus",
            prompt="Any specific focus? (security, performance, style, all) — or type 'skip' for all",
            required=False,
            default="all",
            placeholder="all",
        ),
    ],
    "Meeting Facilitator": [
        ParameterSpec(
            name="meeting_type",
            prompt="What type of meeting? (planning, standup, retrospective, brainstorming) — or type 'skip' for planning",
            required=False,
            default="planning",
            placeholder="planning",
        ),
        ParameterSpec(
            name="topic",
            prompt="What's the meeting topic or agenda subject?",
            required=True,
        ),
        ParameterSpec(
            name="duration",
            prompt="Expected duration? (e.g., '30 min', '1 hour') — or type 'skip' for 30 min",
            required=False,
            default="30 min",
            placeholder="30 min",
        ),
    ],
    "Security Auditor": [
        ParameterSpec(
            name="target",
            prompt="What should I audit? (paste code/config, or provide a file path)",
            required=True,
        ),
        ParameterSpec(
            name="scope",
            prompt="Audit scope? (vulnerabilities, compliance, best practices, all) — or type 'skip' for all",
            required=False,
            default="all",
            placeholder="all",
        ),
    ],
    "Email Automation": [
        ParameterSpec(
            name="email_type",
            prompt="What type of email? (reply, new message, follow-up, template) — or type 'skip' for new message",
            required=False,
            default="new message",
            placeholder="new message",
        ),
        ParameterSpec(
            name="subject",
            prompt="What's the email subject?",
            required=True,
        ),
        ParameterSpec(
            name="recipient_type",
            prompt="Who's the recipient type? (client, team, vendor, internal) — or type 'skip' for client",
            required=False,
            default="client",
            placeholder="client",
        ),
    ],
    "Calendar Manager": [
        ParameterSpec(
            name="task",
            prompt="What do you need? (find meeting time, detect conflicts, optimize schedule) — or type 'skip' for find meeting time",
            required=False,
            default="find meeting time",
            placeholder="find meeting time",
        ),
        ParameterSpec(
            name="details",
            prompt="Give me the meeting/event details (participants, duration, time range).",
            required=True,
        ),
    ],
    "Document Generator": [
        ParameterSpec(
            name="doc_type",
            prompt="What type of document? (proposal, report, memo, letter, contract) — or type 'skip' for report",
            required=False,
            default="report",
            placeholder="report",
        ),
        ParameterSpec(
            name="subject",
            prompt="What's the document subject?",
            required=True,
        ),
        ParameterSpec(
            name="format",
            prompt="Output format? (PDF, Word, HTML, Markdown) — or type 'skip' for Markdown",
            required=False,
            default="Markdown",
            placeholder="Markdown",
        ),
    ],
    "Translation Expert": [
        ParameterSpec(
            name="text",
            prompt="Paste the text to translate.",
            required=True,
        ),
        ParameterSpec(
            name="target_language",
            prompt="What language should I translate to?",
            required=True,
        ),
        ParameterSpec(
            name="tone",
            prompt="Any tone preference? (formal, casual, technical) — or type 'skip' for matching original",
            required=False,
            placeholder="skip",
        ),
    ],
    "Presentation Builder": [
        ParameterSpec(
            name="topic",
            prompt="What's the presentation topic?",
            required=True,
        ),
        ParameterSpec(
            name="slide_count",
            prompt="How many slides? (or type 'skip' for auto-determine)",
            required=False,
            placeholder="skip",
        ),
        ParameterSpec(
            name="audience",
            prompt="Who's the audience? (executive, technical, general, academic) — or type 'skip' for general",
            required=False,
            default="general",
            placeholder="general",
        ),
    ],
    "Spreadsheet Wizard": [
        ParameterSpec(
            name="task",
            prompt="What do you need? (formula, pivot table, data analysis, automation) — or type 'skip' for formula",
            required=False,
            default="formula",
            placeholder="formula",
        ),
        ParameterSpec(
            name="data",
            prompt="Describe the data or paste the relevant cells/ranges.",
            required=True,
        ),
    ],
    "Legal Assistant": [
        ParameterSpec(
            name="document",
            prompt="Paste the legal document text, or provide a file path.",
            required=True,
        ),
        ParameterSpec(
            name="focus",
            prompt="What should I look for? (risks, termination clauses, compliance, redline) — or type 'skip' for general review",
            required=False,
            default="general review",
            placeholder="general review",
        ),
    ],
    "Medical Researcher": [
        ParameterSpec(
            name="topic",
            prompt="What medical topic or treatment to research?",
            required=True,
        ),
        ParameterSpec(
            name="focus",
            prompt="Specific focus? (clinical trials, drug interactions, evidence summary) — or type 'skip' for evidence summary",
            required=False,
            default="evidence summary",
            placeholder="evidence summary",
        ),
    ],
    "Accessibility Assistant": [
        ParameterSpec(
            name="need",
            prompt="What accessibility support do you need? (read aloud, text resize, screen reader format, simplify)",
            required=True,
        ),
        ParameterSpec(
            name="content",
            prompt="Paste the content, or provide a file path.",
            required=True,
        ),
    ],
    "Fact Checker": [
        ParameterSpec(
            name="claim",
            prompt="What claim should I verify?",
            required=True,
        ),
        ParameterSpec(
            name="sources",
            prompt="Any specific sources to check against? — or type 'skip' for general verification",
            required=False,
            placeholder="skip",
        ),
    ],
    "Voice Interface": [
        ParameterSpec(
            name="action",
            prompt="What voice action? (read text aloud, start voice conversation, change voice settings)",
            required=True,
        ),
        ParameterSpec(
            name="content",
            prompt="Paste text to read aloud, or describe the voice interaction you want. — or type 'skip' if not needed",
            required=False,
            placeholder="skip",
        ),
    ],
    "Workflow Automator": [
        ParameterSpec(
            name="trigger",
            prompt="What triggers the workflow? (new email, schedule, manual, webhook)",
            required=True,
        ),
        ParameterSpec(
            name="actions",
            prompt="What actions should the workflow perform? (describe step by step)",
            required=True,
        ),
    ],
    "Competitive Analyst": [
        ParameterSpec(
            name="competitor",
            prompt="Which competitor or market should I analyze?",
            required=True,
        ),
        ParameterSpec(
            name="focus",
            prompt="Analysis focus? (positioning, pricing, SWOT, strategy) — or type 'skip' for general",
            required=False,
            default="general",
            placeholder="general",
        ),
    ],
    "Learning Path Creator": [
        ParameterSpec(
            name="subject",
            prompt="What subject should the learning path cover?",
            required=True,
        ),
        ParameterSpec(
            name="level",
            prompt="Target learner level? (beginner, intermediate, advanced) — or type 'skip' for beginner",
            required=False,
            default="beginner",
            placeholder="beginner",
        ),
        ParameterSpec(
            name="duration",
            prompt="Expected learning duration? (e.g., '4 weeks', 'self-paced') — or type 'skip' for self-paced",
            required=False,
            default="self-paced",
            placeholder="self-paced",
        ),
    ],
    "Smart Search": [
        ParameterSpec(
            name="query",
            prompt="What are you searching for?",
            required=True,
        ),
        ParameterSpec(
            name="sources",
            prompt="Which sources? (documents, web, knowledge base, all) — or type 'skip' for all",
            required=False,
            default="all",
            placeholder="all",
        ),
    ],
    "Team Orchestrator": [
        ParameterSpec(
            name="project",
            prompt="What project should the AI team work on?",
            required=True,
        ),
        ParameterSpec(
            name="roles",
            prompt="What roles do you need? (e.g., 'researcher, writer, reviewer') — or type 'skip' for auto-assign",
            required=False,
            placeholder="skip",
        ),
    ],
    "Memory Bridge": [
        ParameterSpec(
            name="action",
            prompt="What memory action? (recall, save, search, delete)",
            required=True,
        ),
        ParameterSpec(
            name="query",
            prompt="What do you want to recall, save, or search for?",
            required=True,
        ),
    ],
    "Visual Canvas": [
        ParameterSpec(
            name="concept",
            prompt="What visual concept should I create?",
            required=True,
        ),
        ParameterSpec(
            name="style",
            prompt="Any style preference? (diagram, illustration, icon, abstract) — or type 'skip' for auto",
            required=False,
            placeholder="skip",
        ),
    ],
    "API Integrator": [
        ParameterSpec(
            name="service",
            prompt="Which service/API do you want to connect?",
            required=True,
        ),
        ParameterSpec(
            name="purpose",
            prompt="What should the integration do?",
            required=True,
        ),
    ],
    "Knowledge Base Builder": [
        ParameterSpec(
            name="topic",
            prompt="What topic should the knowledge base cover?",
            required=True,
        ),
        ParameterSpec(
            name="structure",
            prompt="Any structure preference? (hierarchical, flat, tagged) — or type 'skip' for hierarchical",
            required=False,
            default="hierarchical",
            placeholder="hierarchical",
        ),
    ],
    "Chatbot": [],
}


# ─── Keywords that indicate the user is providing a parameter value ───

CANCEL_KEYWORDS = {"cancel", "abort", "nevermind", "never mind", "stop", "quit", "exit"}
SKIP_KEYWORDS = {"skip", "none", "n/a", "na", "no", "default", "whatever", "any"}


# ─── Parameter Gatherer ───────────────────────────────────────────────

class ChatParameterGatherer:
    """
    Stateful parameter gathering for the Chat Companion.

    Usage:
        gatherer = ChatParameterGatherer()
        response = gatherer.process_message(user_message, ai_name, abilities)
        if response.action == "ask":
            # Display response.prompt to user, wait for next message
        elif response.action == "execute":
            # Run the capability with response.enriched_message
        elif response.action == "chat":
            # Normal chat, no gathering needed
    """

    def __init__(self):
        self._state: Optional[GatherState] = None

    @property
    def is_gathering(self) -> bool:
        return self._state is not None and self._state.waiting

    def cancel(self):
        self._state = None

    def process_message(
        self,
        user_message: str,
        ai_name: str,
        abilities: list[str],
        use_case: str = "",
    ) -> "GatherResult":
        msg = user_message.strip()
        msg_lower = msg.lower()

        # If we're in the middle of gathering, treat this as a parameter answer
        if self._state and self._state.waiting:
            return self._handle_parameter_response(msg, ai_name)

        # Not gathering — classify intent and check if we need parameters
        intent = self._classify_intent(msg_lower, abilities)

        # Chatbot intent never needs parameter gathering
        if intent == "Chatbot":
            return GatherResult(action="chat", prompt="", enriched_message=msg)

        # Check if this capability maps to a PAUSED canonical intent
        canonical = INTENT_TO_CANONICAL.get(intent, intent)
        if canonical in PAUSED_INTENTS:
            # Still gather params (user may want to see what's needed),
            # but the runtime will return an honest "paused" message
            pass  # Fall through to normal parameter gathering

        params = INTENT_PARAMETERS.get(intent, [])
        if not params:
            return GatherResult(action="chat", prompt="", enriched_message=msg)

        # Check if the user's original message already contains enough info
        extracted = self._extract_parameters_from_message(msg, intent, params)
        
        # Substance check: if the extracted value for a required parameter is
        # just the trigger keyword itself (e.g., user typed "research" with no
        # actual query), treat it as missing so we ask for real content.
        trigger_keywords = self._trigger_keywords_for_intent(intent)
        for spec in params:
            if not spec.required:
                continue
            val = extracted.get(spec.name, "")
            if val and val.lower().strip() in trigger_keywords:
                del extracted[spec.name]

        missing = [p for p in params if p.required and p.name not in extracted]

        if not missing:
            # All required params found in the original message — execute directly
            enriched = self._build_enriched_message(msg, intent, extracted, params)
            return GatherResult(action="execute", prompt="", enriched_message=enriched, intent=intent)

        # Need to gather missing parameters — start the flow
        self._state = GatherState(
            intent=intent,
            params=extracted,
            original_message=msg,
        )

        # Ask for the first missing required parameter
        first_missing = missing[0]
        self._state.current_param = first_missing.name
        self._state.waiting = True

        prompt = first_missing.prompt
        if first_missing.hint:
            prompt += f"\n💡 {first_missing.hint}"

        return GatherResult(
            action="ask",
            prompt=prompt,
            enriched_message="",
            intent=intent,
        )

    def _handle_parameter_response(self, msg: str, ai_name: str) -> "GatherResult":
        state = self._state
        msg_lower = msg.lower().strip()

        # Check for cancel
        if msg_lower in CANCEL_KEYWORDS:
            self.cancel()
            return GatherResult(
                action="chat",
                prompt=f"Okay, cancelled. What else can I help you with?",
                enriched_message="",
            )

        # Find the current parameter spec
        params = INTENT_PARAMETERS.get(state.intent, [])
        current_spec = next((p for p in params if p.name == state.current_param), None)
        if not current_spec:
            self.cancel()
            return GatherResult(action="chat", prompt="Parameter flow error. Please try again.", enriched_message="")

        # Check for skip on optional params
        if msg_lower in SKIP_KEYWORDS and not current_spec.required:
            if current_spec.default:
                state.params[current_spec.name] = current_spec.default
            # Move to next param
            return self._advance_to_next_param(state, params, ai_name)

        # Validate if validator exists
        if current_spec.validator and not current_spec.validator(msg):
            return GatherResult(
                action="ask",
                prompt=f"That doesn't look right. {current_spec.prompt}",
                enriched_message="",
                intent=state.intent,
            )

        # Store the parameter value
        state.params[current_spec.name] = msg

        # Move to next parameter
        return self._advance_to_next_param(state, params, ai_name)

    def _advance_to_next_param(self, state: GatherState, params: list[ParameterSpec], ai_name: str) -> GatherResult:
        # Find next missing required parameter
        for p in params:
            if p.name not in state.params:
                if p.required:
                    state.current_param = p.name
                    state.waiting = True
                    prompt = p.prompt
                    if p.hint:
                        prompt += f"\n💡 {p.hint}"
                    return GatherResult(
                        action="ask",
                        prompt=prompt,
                        enriched_message="",
                        intent=state.intent,
                    )
                else:
                    # Optional param — still ask, but user can skip
                    state.current_param = p.name
                    state.waiting = True
                    prompt = p.prompt
                    if p.hint:
                        prompt += f"\n💡 {p.hint}"
                    return GatherResult(
                        action="ask",
                        prompt=prompt,
                        enriched_message="",
                        intent=state.intent,
                    )

        # All parameters collected — execute
        enriched = self._build_enriched_message(
            state.original_message, state.intent, state.params, params
        )
        self.cancel()
        return GatherResult(
            action="execute",
            prompt="",
            enriched_message=enriched,
            intent=state.intent,
        )

    def _classify_intent(self, msg_lower: str, abilities: list[str]) -> str:
        """Classify the user's message into a capability intent."""
        # Research
        if any(x in msg_lower for x in [
            "research", "look up", "lookup", "search", "find sources", "citation",
            "cite", "verify", "current", "latest", "web search", "news", "game mechanics",
        ]):
            return "Research"

        # Coder
        if any(x in msg_lower for x in [
            "code", "bug", "python", "javascript", "html", "css", "function", "class",
            "error", "traceback", "fix script", "patch", "refactor", "debug",
        ]):
            return "Coder"

        # Enterprise Orchestrator — check early, before Email/Tool User/Creative Writing/
        # Customer Support/Business Workflow, because enterprise keywords like "draft",
        # "customer support", "policy", "onboarding" would be caught by those classifiers.
        # NOTE: bare "enterprise" is NOT included here because it catches
        # "enterprise software", "enterprise sales", etc. which are Business Workflow.
        if any(x in msg_lower for x in [
            "enterprise orchestrat", "policy review", "compliance audit",
            "compliance check", "gdpr", "soc2", "hipaa", "pci compliance",
            "iso 27001", "regulatory check", "operations coordinat",
            "incident response", "executive brief", "board prep",
            "cross-department", "enterprise analytics", "kpi dashboard",
            "hr orchestrat", "onboarding for", "offboarding for",
            "coordinate onboarding", "coordinate offboarding",
            "enterprise workflow", "company confidential",
            "executive summary", "leadership update", "strategic brief",
            "decision memo", "c-suite", "compliance report",
            "policy draft", "policy update", "policy change",
            "governance policy", "standard operating policy",
        ]):
            return "Enterprise Orchestrator"

        # Email Automation — check before Tool User and Creative Writing
        # so "write email" / "send email" don't get misclassified
        if any(x in msg_lower for x in [
            "draft email", "email response", "email template", "compose email",
            "write email", "email draft", "send email", "email automation",
        ]):
            return "Email Automation"

        # Tool User
        if any(x in msg_lower for x in [
            "read file", "show file", "display file", "open file", "cat file", "view file",
            "write file", "create file", "save file", "write to file", "create a file",
            "list directory", "list files", "list folder", "list dir", "show files",
            "delete file", "delete folder", "remove file", "move file", "rename file",
            "run command", "run shell", "execute ", "shell command", "terminal ",
            "install", "uninstall", "download", "open app", "click", "type into",
            "upload", "publish", "submit",
        ]):
            return "Tool User"

        # Business Workflow — enhanced with sub-workflow keywords
        # Check before Creative Writing so "draft a marketing..." / "draft an NDA..."
        # don't get caught by the "draft" keyword in Creative Writing.
        if any(x in msg_lower for x in [
            "sales", "marketing", "hr ", "sop", "business", "support reply", "checklist",
            "proposal", "outreach", "pipeline", "crm", "cold call", "pitch", "quota",
            "campaign", "content calendar", "brand", "social media", "ad copy",
            "newsletter", "press release", "seo", "go-to-market",
            "budget", "forecast", "invoice", "expense", "financial",
            "cost analysis", "revenue projection", "p&l", "cash flow", "billing",
            "contract", "nda", "terms of service", "privacy policy",
            "legal review", "agreement", "clause",
            "process improvement", "workflow optimization", "logistics",
            "supply chain", "inventory", "quality control", "operational",
            "efficiency", "bottleneck", "process map",
            "job description", "interview guide", "performance review template",
            "employee handbook", "hr draft", "hr policy draft",
            "standard operating procedure", "procedure",
            "check list", "task list", "verification list",
            "support response", "support draft", "customer reply", "response template",
            "handoff", "hand off", "transition document",
        ]):
            return "Business Workflow"

        # Creative Writing
        if any(x in msg_lower for x in [
            "write", "draft", "rewrite", "story", "script", "copy", "article", "post",
            "paragraph", "creative", "blog", "content", "narrative",
        ]):
            return "Creative Writing"

        # Planner
        if any(x in msg_lower for x in [
            "plan", "steps", "strategy", "schedule", "roadmap", "milestone",
            "organize project", "workflow", "project plan", "break down",
        ]):
            return "Planner"

        # Document Processor
        if any(x in msg_lower for x in [
            "document", "summarize this", "extract", "compare document", "pdf", "docx",
        ]):
            return "Document Processor"

        # Notebook
        if any(x in msg_lower for x in [
            "note", "remember", "log this", "save note", "take notes",
        ]):
            return "Notebook"

        # Archive
        if any(x in msg_lower for x in [
            "archive", "save this result", "store this", "retrieve archive",
        ]):
            return "Archive"

        # Tutor
        if any(x in msg_lower for x in [
            "teach", "lesson", "quiz", "study", "explain like", "tutor", "learn",
        ]):
            return "Tutor"

        # Customer Support
        if any(x in msg_lower for x in [
            "customer support", "support ticket", "help desk", "escalat", "customer service",
        ]):
            return "Customer Support AI"

        # Hephaestus
        if any(x in msg_lower for x in [
            "hephaestus", "design brief", "prototype", "material spec", "handoff brief",
        ]):
            return "Hephaestus Relay"

        # Data Analyst
        if any(x in msg_lower for x in [
            "analyze data", "data analyst", "dataset", "statistics", "chart", "pivot",
            "data trend", "data visualization",
        ]):
            return "Data Analyst Pro"

        # Code Reviewer
        if any(x in msg_lower for x in [
            "code review", "review code", "quality check", "lint",
            "best practice",
        ]):
            return "Code Reviewer"

        # Meeting Facilitator
        if any(x in msg_lower for x in [
            "meeting agenda", "facilitate meeting", "action item", "meeting note",
            "standup", "retrospective",
        ]):
            return "Meeting Facilitator"

        # Security Auditor
        if any(x in msg_lower for x in [
            "security audit", "vulnerability", "penetration", "compliance scan",
            "security assessment", "security scan",
        ]):
            return "Security Auditor"

        # Calendar Manager
        if any(x in msg_lower for x in [
            "schedule", "find meeting time", "calendar", "availability", "time slot",
        ]):
            return "Calendar Manager"

        # Document Generator
        if any(x in msg_lower for x in [
            "generate document", "create report", "create proposal", "create memo",
            "generate report", "generate proposal",
        ]):
            return "Document Generator"

        # Translation
        if any(x in msg_lower for x in [
            "translate", "translation", "in spanish", "in french", "in german",
            "in japanese", "in chinese",
        ]):
            return "Translation Expert"

        # Presentation
        if any(x in msg_lower for x in [
            "presentation", "slides", "slide deck", "powerpoint", "keynote",
        ]):
            return "Presentation Builder"

        # Spreadsheet
        if any(x in msg_lower for x in [
            "formula", "spreadsheet", "excel", "google sheets", "pivot table",
        ]):
            return "Spreadsheet Wizard"

        # Legal
        if any(x in msg_lower for x in [
            "legal", "contract review", "clause", "compliance check", "gdpr",
        ]):
            return "Legal Assistant"

        # Medical
        if any(x in msg_lower for x in [
            "medical research", "clinical trial", "drug interaction", "evidence-based",
            "pubmed", "medical literature",
        ]):
            return "Medical Researcher"

        # Accessibility
        if any(x in msg_lower for x in [
            "read aloud", "text to speech", "screen reader", "accessibility",
            "high contrast", "text size",
        ]):
            return "Accessibility Assistant"

        # Fact Checker
        if any(x in msg_lower for x in [
            "fact check", "verify claim", "credibility", "misinformation",
            "check this fact",
        ]):
            return "Fact Checker"

        # Voice
        if any(x in msg_lower for x in [
            "voice", "speech", "read out loud", "talk to me", "listen",
        ]):
            return "Voice Interface"

        # Workflow Automator
        if any(x in msg_lower for x in [
            "automate workflow", "workflow builder", "no-code automation",
            "process automation", "trigger workflow",
        ]):
            return "Workflow Automator"

        # Competitive Analyst
        if any(x in msg_lower for x in [
            "competitor", "market analysis", "swot", "competitive landscape",
            "market research",
        ]):
            return "Competitive Analyst"

        # Learning Path
        if any(x in msg_lower for x in [
            "learning path", "curriculum", "course builder", "training plan",
            "study plan",
        ]):
            return "Learning Path Creator"

        # Smart Search
        if any(x in msg_lower for x in [
            "smart search", "search across", "find documents", "semantic search",
        ]):
            return "Smart Search"

        # Team Orchestrator
        if any(x in msg_lower for x in [
            "team of ai", "multi-ai", "ai team", "orchestrate", "coordinate ai",
        ]):
            return "Team Orchestrator"

        # Memory Bridge
        if any(x in msg_lower for x in [
            "remember this", "recall", "what did we discuss", "memory search",
            "previous conversation",
        ]):
            return "Memory Bridge"

        # Visual Canvas
        if any(x in msg_lower for x in [
            "generate image", "create diagram", "visual concept", "ai art",
            "image generation",
        ]):
            return "Visual Canvas"

        # API Integrator
        if any(x in msg_lower for x in [
            "api integration", "connect api", "webhook", "external service",
        ]):
            return "API Integrator"

        # Knowledge Base
        if any(x in msg_lower for x in [
            "knowledge base", "documentation site", "wiki", "help center",
        ]):
            return "Knowledge Base Builder"

        return "Chatbot"

    def _trigger_keywords_for_intent(self, intent: str) -> set[str]:
        """Return the set of bare keywords that trigger this intent.
        
        If the user's message is JUST one of these keywords with no additional
        content, we treat the primary parameter as missing and ask for real input.
        """
        triggers = {
            "Research": {"research", "look up", "lookup", "search", "find sources",
                         "citation", "cite", "verify", "current", "latest",
                         "web search", "news", "game mechanics"},
            "Coder": {"code", "bug", "python", "javascript", "html", "css",
                      "function", "class", "error", "traceback", "fix script",
                      "patch", "refactor", "debug"},
            "Tool User": {"read file", "show file", "display file", "open file",
                          "write file", "create file", "save file",
                          "list directory", "list files", "list folder",
                          "delete file", "delete folder", "remove file",
                          "move file", "rename file",
                          "run command", "run shell", "shell command",
                          "install", "uninstall", "download",
                          "upload", "publish", "submit"},
            "Creative Writing": {"write", "draft", "rewrite", "story", "script",
                                 "copy", "article", "post", "paragraph",
                                 "creative", "blog", "content", "narrative"},
            "Planner": {"plan", "steps", "strategy", "schedule", "roadmap",
                        "milestone", "organize project", "workflow",
                        "project plan", "break down"},
            "Document Processor": {"document", "summarize this", "extract",
                                   "compare document", "pdf", "docx"},
            "Notebook": {"note", "remember", "log this", "save note", "take notes"},
            "Archive": {"archive", "save this result", "store this", "retrieve archive"},
            "Tutor": {"teach", "lesson", "quiz", "study", "explain like",
                      "tutor", "learn"},
            "Customer Support AI": {"customer support", "support ticket",
                                    "help desk", "escalat", "customer service"},
            "Business Workflow": {"sales", "marketing", "hr ", "sop", "business",
                                  "support reply", "checklist"},
            "Enterprise Orchestrator": {
                "enterprise orchestrat", "policy review", "compliance audit",
                "compliance check", "gdpr", "soc2", "hipaa", "pci compliance",
                "iso 27001", "regulatory check", "operations coordinat",
                "incident response", "executive brief", "board prep",
                "cross-department", "enterprise analytics", "kpi dashboard",
                "hr orchestrat", "onboarding for", "offboarding for",
                "coordinate onboarding", "coordinate offboarding",
                "enterprise workflow", "company confidential",
                "executive summary", "leadership update", "strategic brief",
                "decision memo", "c-suite", "compliance report",
                "policy draft", "policy update", "policy change",
                "governance policy", "standard operating policy",
            },
            "Hephaestus Relay": {"hephaestus", "design brief", "prototype",
                                 "material spec", "handoff brief"},
            "Data Analyst Pro": {"analyze data", "data analyst", "dataset",
                                 "statistics", "chart", "pivot",
                                 "data trend", "data visualization"},
            "Code Reviewer": {"code review", "review code", "quality check",
                              "lint", "best practice"},
            "Meeting Facilitator": {"meeting agenda", "facilitate meeting",
                                    "action item", "meeting note",
                                    "standup", "retrospective"},
            "Security Auditor": {"security audit", "vulnerability",
                                 "penetration", "compliance scan",
                                 "security assessment", "security scan"},
            "Email Automation": {"draft email", "email response", "email template",
                                 "compose email", "write email", "email draft",
                                 "send email", "email automation"},
            "Calendar Manager": {"schedule", "find meeting time", "calendar",
                                 "availability", "time slot"},
            "Document Generator": {"generate document", "create report",
                                   "create proposal", "create memo",
                                   "generate report", "generate proposal"},
            "Translation Expert": {"translate", "translation"},
            "Presentation Builder": {"presentation", "slides", "slide deck",
                                     "powerpoint", "keynote"},
            "Spreadsheet Wizard": {"formula", "spreadsheet", "excel",
                                   "google sheets", "pivot table"},
            "Legal Assistant": {"legal", "contract review", "clause",
                                "compliance check", "gdpr"},
            "Medical Researcher": {"medical research", "clinical trial",
                                   "drug interaction", "evidence-based",
                                   "pubmed", "medical literature"},
            "Accessibility Assistant": {"read aloud", "text to speech",
                                        "screen reader", "accessibility",
                                        "high contrast", "text size"},
            "Fact Checker": {"fact check", "verify claim", "credibility",
                             "misinformation", "check this fact"},
            "Voice Interface": {"voice", "speech", "read out loud",
                                "talk to me", "listen"},
            "Workflow Automator": {"automate workflow", "workflow builder",
                                   "no-code automation",
                                   "process automation", "trigger workflow"},
            "Competitive Analyst": {"competitor", "market analysis", "swot",
                                    "competitive landscape", "market research"},
            "Learning Path Creator": {"learning path", "curriculum",
                                      "course builder", "training plan",
                                      "study plan"},
            "Smart Search": {"smart search", "search across",
                             "find documents", "semantic search"},
            "Team Orchestrator": {"team of ai", "multi-ai", "ai team",
                                  "orchestrate", "coordinate ai"},
            "Memory Bridge": {"remember this", "recall",
                              "what did we discuss", "memory search",
                              "previous conversation"},
            "Visual Canvas": {"generate image", "create diagram",
                              "visual concept", "ai art", "image generation"},
            "API Integrator": {"api integration", "connect api",
                               "webhook", "external service"},
            "Knowledge Base Builder": {"knowledge base",
                                       "documentation site", "wiki",
                                       "help center"},
        }
        return triggers.get(intent, set())

    def _extract_parameters_from_message(
        self, msg: str, intent: str, params: list[ParameterSpec]
    ) -> dict[str, str]:
        """
        Try to extract parameter values from the user's original message.
        For most intents, the message itself serves as the primary parameter.
        """
        extracted: dict[str, str] = {}

        if intent == "Research":
            # The whole message is the query
            extracted["query"] = msg
        elif intent == "Coder":
            extracted["description"] = msg
        elif intent == "Creative Writing":
            extracted["topic"] = msg
        elif intent == "Planner":
            extracted["goal"] = msg
        elif intent == "Document Processor":
            extracted["input"] = msg
        elif intent == "Notebook":
            extracted["body"] = msg
        elif intent == "Archive":
            extracted["content"] = msg
        elif intent == "Tutor":
            extracted["topic"] = msg
        elif intent == "Business Workflow":
            extracted["subject"] = msg
            # Try to detect business sub-workflow from keywords
            msg_lower = msg.lower()
            if any(x in msg_lower for x in ["sales", "proposal", "outreach", "pipeline", "crm", "cold call", "pitch", "quota"]):
                extracted["workflow_type"] = "Sales"
            elif any(x in msg_lower for x in ["marketing", "campaign", "content calendar", "brand", "social media", "ad copy", "newsletter", "press release", "seo"]):
                extracted["workflow_type"] = "Marketing"
            elif any(x in msg_lower for x in ["budget", "forecast", "invoice", "expense", "financial", "cost analysis", "revenue projection", "p&l", "cash flow", "billing"]):
                extracted["workflow_type"] = "Finance"
            elif any(x in msg_lower for x in ["contract", "nda", "terms of service", "privacy policy", "legal review", "agreement", "clause"]):
                extracted["workflow_type"] = "Legal"
            elif any(x in msg_lower for x in ["process improvement", "workflow optimization", "logistics", "supply chain", "inventory", "quality control", "operational", "efficiency", "bottleneck"]):
                extracted["workflow_type"] = "Operations"
            elif any(x in msg_lower for x in ["job description", "interview guide", "performance review template", "hr draft", "employee handbook", "hr policy draft"]):
                extracted["workflow_type"] = "HR Draft"
            elif any(x in msg_lower for x in ["sop", "standard operating procedure", "procedure"]):
                extracted["workflow_type"] = "SOP"
            elif any(x in msg_lower for x in ["checklist", "check list", "task list", "verification list"]):
                extracted["workflow_type"] = "Checklist"
            elif any(x in msg_lower for x in ["support reply", "support response", "support draft", "customer reply", "response template"]):
                extracted["workflow_type"] = "Support Draft"
            elif any(x in msg_lower for x in ["handoff", "hand off", "transition document"]):
                extracted["workflow_type"] = "Handoff"
            # Try to detect audience
            if "management" in msg_lower or "executive" in msg_lower:
                extracted["audience"] = "management"
            elif "customer" in msg_lower:
                extracted["audience"] = "customer"
        elif intent == "Enterprise Orchestrator":
            extracted["objective"] = msg
            # Try to detect sub-workflow from keywords
            msg_lower = msg.lower()
            if any(x in msg_lower for x in ["onboarding", "offboarding", "hr ", "employee", "personnel", "grievance"]):
                extracted["sub_workflow"] = "HR"
            elif any(x in msg_lower for x in ["compliance", "gdpr", "soc2", "hipaa", "regulatory", "audit"]):
                extracted["sub_workflow"] = "Compliance"
            elif any(x in msg_lower for x in ["policy review", "policy draft", "policy update", "policy change"]):
                extracted["sub_workflow"] = "Policy Review"
            elif any(x in msg_lower for x in ["operations", "incident", "deployment", "resource allocation"]):
                extracted["sub_workflow"] = "Operations"
            elif any(x in msg_lower for x in ["kpi", "dashboard", "analytics", "metrics", "trend"]):
                extracted["sub_workflow"] = "Analytics"
            elif any(x in msg_lower for x in ["executive brief", "board prep", "leadership", "c-suite"]):
                extracted["sub_workflow"] = "Executive Brief"
            elif any(x in msg_lower for x in ["cross-department", "cross department", "coordination"]):
                extracted["sub_workflow"] = "Cross-Department"
            # Try to detect priority
            if "p1" in msg_lower or "critical" in msg_lower:
                extracted["priority"] = "P1-Critical"
            elif "p2" in msg_lower or "high" in msg_lower:
                extracted["priority"] = "P2-High"
            elif "p4" in msg_lower or "low" in msg_lower:
                extracted["priority"] = "P4-Low"
        elif intent == "Tool User":
            extracted["action_description"] = msg
        elif intent == "Customer Support AI":
            extracted["inquiry"] = msg
        elif intent == "Hephaestus Relay":
            extracted["idea"] = msg
        elif intent == "Data Analyst Pro":
            extracted["data_source"] = msg
        elif intent == "Code Reviewer":
            extracted["code_input"] = msg
        elif intent == "Meeting Facilitator":
            extracted["topic"] = msg
        elif intent == "Security Auditor":
            extracted["target"] = msg
        elif intent == "Email Automation":
            extracted["subject"] = msg
        elif intent == "Calendar Manager":
            extracted["details"] = msg
        elif intent == "Document Generator":
            extracted["subject"] = msg
        elif intent == "Translation Expert":
            extracted["text"] = msg
        elif intent == "Presentation Builder":
            extracted["topic"] = msg
        elif intent == "Spreadsheet Wizard":
            extracted["data"] = msg
        elif intent == "Legal Assistant":
            extracted["document"] = msg
        elif intent == "Medical Researcher":
            extracted["topic"] = msg
        elif intent == "Accessibility Assistant":
            extracted["content"] = msg
        elif intent == "Fact Checker":
            extracted["claim"] = msg
        elif intent == "Voice Interface":
            extracted["action"] = msg
        elif intent == "Workflow Automator":
            extracted["actions"] = msg
        elif intent == "Competitive Analyst":
            extracted["competitor"] = msg
        elif intent == "Learning Path Creator":
            extracted["subject"] = msg
        elif intent == "Smart Search":
            extracted["query"] = msg
        elif intent == "Team Orchestrator":
            extracted["project"] = msg
        elif intent == "Memory Bridge":
            extracted["query"] = msg
        elif intent == "Visual Canvas":
            extracted["concept"] = msg
        elif intent == "API Integrator":
            extracted["purpose"] = msg
        elif intent == "Knowledge Base Builder":
            extracted["topic"] = msg

        return extracted

    def _build_enriched_message(
        self,
        original: str,
        intent: str,
        params: dict[str, str],
        specs: list[ParameterSpec],
    ) -> str:
        """
        Build a natural-language enriched message that includes the original
        request plus all gathered parameters.

        The format is designed to:
        1. Include a lightweight [Intent: X] tag the runtime can detect
        2. Read as natural language so the runtime's _classify() and
           _run_tool_user() heuristics still work correctly
        3. Not break regex-based path/content extractors in the runtime
        """
        # Fill in defaults for missing optional params
        for spec in specs:
            if spec.name not in params and spec.default:
                params[spec.name] = spec.default

        # Map to canonical intent name for the runtime
        canonical = INTENT_TO_CANONICAL.get(intent, intent)

        # Build a natural-language message, not a structured key:value format
        # The [Intent: X] tag is stripped by the runtime before processing
        parts = [f"[Intent: {canonical}]"]

        # Compose natural language from the gathered parameters
        # This preserves the original message as the core, with context appended
        context_parts: list[str] = []

        for spec in specs:
            val = params.get(spec.name, "")
            if not val or val == original:
                continue
            # Skip if this was the primary content already in the original
            if spec.name in ("query", "description", "topic", "goal", "input",
                             "body", "content", "inquiry", "idea", "claim",
                               "action_description", "data_source", "code_input",
                               "target", "details", "text", "data", "document",
                               "competitor", "project", "concept", "purpose",
                               "subject", "actions", "action", "objective"):
                # These are primary content — already in the original message
                continue
            # Secondary parameters (tone, audience, format, scope, etc.) get appended
            context_parts.append(f"{spec.name}: {val}")

        # The original message is the core text the runtime will process
        if context_parts:
            parts.append(f"{original}\n\nAdditional context: {'; '.join(context_parts)}")
        else:
            parts.append(original)

        return "\n".join(parts)


@dataclass
class GatherResult:
    """Result of processing a message through the parameter gatherer."""
    action: str  # "ask", "execute", or "chat"
    prompt: str  # What to say to the user (if action == "ask")
    enriched_message: str  # Enriched message to send to runtime (if action == "execute")
    intent: str = ""  # The classified intent
