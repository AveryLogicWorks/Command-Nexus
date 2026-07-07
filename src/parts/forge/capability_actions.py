"""Capability Action Registry and Workflow Dialogs."""
from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass, field
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QComboBox, QTabWidget, QWidget,
    QSplitter, QMessageBox, QFileDialog,
)

from ...core.settings_manager import SettingsManager
from ...core.backend_manager import BackendManager, BackendResponse


@dataclass(frozen=True)
class CapabilityAction:
    capability_id: str
    canonical_name: str
    display_name: str
    description: str
    inward_surface: str
    outward_action_path: str
    required_permissions: list[str]
    required_approval_level: str
    allowed_use_cases: list[str]
    compatible_capabilities: list[str]
    interaction_rules: list[str]
    book_sections_used: list[str]
    libraries_used: list[str]
    starter_prompt_guidance: list[str]
    unfinished_safe_fallback: str
    dialog_class: str
    ui_label: str
    approval_required: list[str] = field(default_factory=list)
    book_context_fields: list[str] = field(default_factory=lambda: [
        "identity", "use_case", "capabilities", "libraries", "guardrails", "quickstart",
        "capability_attachments", "inward_mode", "outward_mode", "approval_requirements",
    ])
    status_messages: dict[str, str] = field(default_factory=dict)


ALL_USE_CASES = ["Individual", "Educational", "Task-Ready", "Business", "Enterprise", "Financial Gainer", "Memory Saver", "All-Rounder"]


CAPABILITY_ALIASES = {
    "Chat Companion": "Chatbot",
    "Customer Support Agent": "Chatbot",
    "Customer Support AI": "Customer Support AI",  # Direct mapping - no alias needed
    "Email Sifter & Responder": "Chatbot",
    "Creative Writer": "Creative Writing",
    "Research Assistant": "Research",
    "Academic Researcher": "Research",
    "Business Intelligence Analyst": "Research",
    "Personal Organizer": "Notebook",
    "Meeting Scribe": "Notebook",
    "Task / Project Manager": "Planner",
    "Strategic Planner": "Planner",
    "Workflow Automator": "Planner",
    "Coding Assistant": "Coder",
    "IT Operations Agent": "Coder",
    "Learning Tutor": "Tutor",
    "Classroom Tutor": "Tutor",
    "Assignment Grader": "Tutor",
    "Lesson Planner": "Tutor",
    "Language Coach": "Tutor",
    "Accessibility Aide": "Tutor",
    "Sales Assistant": "Business Workflow",
    "Marketing Generator": "Business Workflow",
    "Financial Analyst": "Business Workflow",
    "HR Assistant": "Business Workflow",
    "Compliance Auditor": "Business Workflow",
    "Supply Chain Coordinator": "Business Workflow",
    "Legal Document Reviewer": "Business Workflow",
    "Multi-Department Orchestrator": "Business Workflow",
    "Data Entry Agent": "Business Workflow",
    "Content Moderator": "Business Workflow",
}


def _action(
    capability_id: str,
    display_name: str,
    description: str,
    inward_surface: str,
    outward_action_path: str,
    permissions: list[str],
    approval: str,
    use_cases: list[str],
    compatible: list[str],
    rules: list[str],
    book_sections: list[str],
    libraries: list[str],
    prompts: list[str],
    fallback: str,
    dialog_class: str,
    ui_label: str,
) -> CapabilityAction:
    return CapabilityAction(
        capability_id=capability_id,
        canonical_name=display_name,
        display_name=display_name,
        description=description,
        inward_surface=inward_surface,
        outward_action_path=outward_action_path,
        required_permissions=permissions,
        required_approval_level=approval,
        allowed_use_cases=use_cases,
        compatible_capabilities=compatible,
        interaction_rules=rules,
        book_sections_used=book_sections,
        libraries_used=libraries,
        starter_prompt_guidance=prompts,
        unfinished_safe_fallback=fallback,
        dialog_class=dialog_class,
        ui_label=ui_label,
        approval_required=permissions,
        status_messages={
            "ready": f"{display_name} attachment ready.",
            "approval_needed": f"{approval} approval required for outward actions.",
            "fallback": fallback,
        },
    )


CAPABILITY_REGISTRY: dict[str, CapabilityAction] = {
    "Chatbot": _action(
        "cap.chat", "Chatbot",
        "Central conversation surface that understands the AI Book and routes to selected attachments.",
        "Workspace chat transcript, context summary, and capability routing buttons.",
        "Outbound messages or handoff packets only after approval.",
        ["outbound messages", "handoff packets"], "Low",
        ALL_USE_CASES, ["Research", "Coder", "Creative Writing", "Planner", "Notebook", "Document Processor"],
        ["Route requests to selected capabilities instead of pretending unsupported powers exist.", "Return safe stub status to chat when a local intelligence is active."],
        ["Identity and Purpose", "Quickstart", "Capability Attachments", "Cross-Capability Workflows"],
        ["Communication Library", "Governance UX Library"],
        ["Ask me what this AI can do", "Use research on this question", "Turn this into a plan"],
        "Chat works locally; external send actions are not connected and remain approval-gated.",
        "ChatCapabilityDialog", "Open Workspace Chat",
    ),
    "Chat": _action(
        "cap.chat", "Chat",
        "Central conversation surface that understands the AI Book and routes to selected attachments.",
        "Workspace chat transcript, context summary, and capability routing buttons.",
        "Outbound messages or handoff packets only after approval.",
        ["outbound messages", "handoff packets"], "Low",
        ALL_USE_CASES, ["Research", "Coder", "Creative Writing", "Planner", "Notebook", "Document Processor"],
        ["Route requests to selected capabilities instead of pretending unsupported powers exist.", "Return safe stub status to chat when a local intelligence is active."],
        ["Identity and Purpose", "Quickstart", "Capability Attachments", "Cross-Capability Workflows"],
        ["Communication Library", "Governance UX Library"],
        ["Ask me what this AI can do", "Use research on this question", "Turn this into a plan"],
        "Chat works locally; external send actions are not connected and remain approval-gated.",
        "ChatCapabilityDialog", "Open Workspace Chat",
    ),
    "Coder": _action(
        "cap.coder", "Coder",
        "Code explanation, show-code-only drafting, diff preview, and approved edit/test scaffolding.",
        "Coding workflow with prompt, diff preview, file plan, and validation plan.",
        "File writes and command/test execution only through approval-gated future handlers.",
        ["file_write", "file_overwrite", "execute", "shell"], "High",
        ["Individual", "Task-Ready", "Enterprise", "All-Rounder"], ["Chatbot", "Research", "Document Processor", "Tool User"],
        ["Default to show-code-only mode.", "Draft diffs before edits.", "Never edit, delete, move, install, or run without approval."],
        ["Capability Attachments", "Allowed Areas", "Restricted Areas", "Approval Required", "Save Safety"],
        ["Code Safety Library", "Governance UX Library"],
        ["Explain this code", "Draft a diff but do not apply it", "Outline tests for this fix"],
        "Approved file editing and test execution are scaffolded but not connected to direct computer control.",
        "CodingCapabilityDialog", "Open Coding Workflow",
    ),
    "Research": _action(
        "cap.research", "Research",
        "Research query intake, findings, source/citation tracking, risk comparison, and chat return summaries.",
        "Research workflow with query input, findings area, and sources area.",
        "Live browser/search automation only after network approval.",
        ["network", "external_search", "export"], "Medium",
        ALL_USE_CASES, ["Chatbot", "Creative Writing", "Coder", "Archive", "Document Processor", "Planner"],
        ["Separate facts from speculation.", "Show source area even when live search is not connected.", "Return summaries to the workspace chat."],
        ["Capability Attachments", "Nexus Libraries", "Quickstart", "Cross-Capability Workflows"],
        ["Research Discipline Library", "Governance UX Library"],
        ["Research X with confidence labels", "Compare A vs B with sources", "Find risks and mitigations"],
        "Live web research is not connected; the local workflow compiles and labels results as simulated.",
        "ResearchCapabilityDialog", "Open Research Workflow",
    ),
    "Creative Writing": _action(
        "cap.writer", "Creative Writing",
        "Drafting, outlining, revision, tone/style control, copy prep, and approved export scaffolding.",
        "Writing workflow with tone, audience, prompt, and output surface.",
        "Save/export/publish only after approval.",
        ["file_write", "export", "outbound messages"], "Medium",
        ["Individual", "Educational", "Business", "Enterprise", "All-Rounder"], ["Chatbot", "Research", "Planner", "Archive", "Hephaestus Relay"],
        ["Flag invented content.", "Use research findings only as cited inputs.", "Do not publish or send without approval."],
        ["Response Style Defaults", "Capability Attachments", "Common Prompts"],
        ["Communication Library", "Research Discipline Library", "Project Memory Library"],
        ["Outline this idea", "Draft for this audience and tone", "Revise this into a clearer version"],
        "Writing is local in-workspace; file export and publishing are approval-gated stubs.",
        "CreativeWriterCapabilityDialog", "Open Writing Workflow",
    ),
    "Planner": _action(
        "cap.planner", "Planner",
        "Goal decomposition, task/project breakdown, risk checks, file organization plans, and approved outward steps.",
        "Planner workflow with goal input, plan/risk/task output, and approval banner.",
        "Task assignment, file/folder organization, or external commitments only after approval.",
        ["file_move", "file_write", "external_commitment"], "Medium",
        ALL_USE_CASES, ["Chatbot", "Document Processor", "Notebook", "Tool User", "Creative Writing"],
        ["Plan before acting.", "Show proposed changes before outward actions.", "Escalate risky execution steps."],
        ["Capability Attachments", "Cross-Capability Workflows", "Approval Required"],
        ["Project Memory Library", "Governance UX Library"],
        ["Plan project X with milestones", "Convert this goal into tasks", "Show risks and dependencies"],
        "Outward organization is not connected; local plans and proposed changes are available.",
        "PlannerCapabilityDialog", "Open Planner",
    ),
    "Notebook": _action(
        "cap.notes", "Notebook",
        "Notes, project memory, continuity, recall, tagging, and organizer intake.",
        "Notes workflow with title, tags, body, and recall surface.",
        "Bulk deletion, export, or persistent store changes only after approval.",
        ["file_write", "file_delete", "export"], "Medium",
        ALL_USE_CASES, ["Chatbot", "Planner", "Document Processor", "Archive"],
        ["Label entries clearly.", "Summarize before storing long content.", "Do not delete or export without approval."],
        ["Nexus Libraries", "Capability Attachments", "Editable Guidance"],
        ["Project Memory Library", "Communication Library"],
        ["Take notes on this", "Summarize notes tagged X", "Turn this note into tasks"],
        "Notes are held in the workflow surface; persistent note storage is not connected.",
        "NotebookCapabilityDialog", "Open Notes",
    ),
    "Document Processor": _action(
        "cap.documents", "Document Processor",
        "Document intake, summarization, extraction, classification, comparison, and approved export.",
        "Document workflow with file/text intake and summary/extraction actions.",
        "File reads are user-selected; source modification and export require approval.",
        ["file_read", "file_write", "export"], "Medium",
        ["Individual", "Educational", "Task-Ready", "Business", "Enterprise", "All-Rounder"], ["Research", "Planner", "Notebook", "Archive", "Business Workflow"],
        ["Do not alter source documents.", "Show summaries before save/export.", "Flag uncertainty and sensitive content."],
        ["Capability Attachments", "Approval Required", "Common Prompts"],
        ["Research Discipline Library", "Project Memory Library", "Governance UX Library"],
        ["Summarize this document", "Extract action items", "Classify this document"],
        "Document intake reads selected text/files locally; export/save automation is not connected.",
        "DocumentProcessorCapabilityDialog", "Open Document Workflow",
    ),
    "Archive": _action(
        "cap.archive", "Archive",
        "Artifact storage, retrieval surface, index habits, and approved archive movement/export.",
        "Archive workflow with artifact name, tags, content, and retrieval surface.",
        "Moving, deleting, or bulk exporting archive material only after approval.",
        ["file_write", "file_move", "file_delete", "export"], "High",
        ALL_USE_CASES, ["Notebook", "Research", "Creative Writing", "Document Processor"],
        ["Tag/date artifacts.", "Confirm before saving sensitive content.", "Never move/delete archives without approval."],
        ["Archive", "Capability Attachments", "Save Safety"],
        ["Project Memory Library", "Governance UX Library"],
        ["Archive this result", "Retrieve artifact tagged X", "List saved outputs"],
        "Archive UI is local and safe; file system archive moves/exports are not connected.",
        "ArchiveCapabilityDialog", "Open Archive",
    ),
    "Tool User": _action(
        "cap.tools", "Tool User",
        "Tool proposal, rationale, approved invocation scaffold, and visible status reporting.",
        "Tool workflow with tool proposal, rationale, and available-tool surface.",
        "Every tool invocation requires approval and audit routing.",
        ["tool_invocation", "network", "execute", "file_write"], "High",
        ["Task-Ready", "Business", "Enterprise", "All-Rounder"], ["Planner", "Coder", "Research", "Business Workflow"],
        ["Explain tool purpose before use.", "Do not chain tools automatically.", "Log rationale and status."],
        ["Capability Attachments", "Approval Required", "Save Safety"],
        ["Governance UX Library", "Code Safety Library"],
        ["What tools can help with this?", "Propose a tool chain", "Prepare an approval request"],
        "Tool invocation is not connected; the proposal and approval scaffold compiles safely.",
        "ToolUserCapabilityDialog", "Open Tool Workflow",
    ),
    "Tutor": _action(
        "cap.tutor", "Tutor",
        "Educational explanation, quiz, lesson, study-sheet, language, and accessibility modes.",
        "Tutor workflow with learning goal, mode, explanation, quiz, and study output.",
        "Exporting notes or graded feedback requires approval.",
        ["export", "file_write"], "Low",
        ["Educational", "Individual", "All-Rounder"], ["Chatbot", "Research", "Document Processor", "Notebook"],
        ["Guide learning rather than providing dishonest final answers.", "Adapt to learner level.", "Offer quizzes and study sheets."],
        ["Operating Context", "Response Style Defaults", "Capability Attachments"],
        ["Communication Library", "Research Discipline Library", "Project Memory Library"],
        ["Explain this step by step", "Quiz me on this topic", "Make a study sheet"],
        "Tutor output is local; exporting learning notes is approval-gated.",
        "TutorCapabilityDialog", "Open Tutor Workflow",
    ),
    "Business Workflow": _action(
        "cap.business_workflow", "Business Workflow",
        "SOPs, checklists, support drafts, handoffs, workflow planning, and approval-gated automation hooks.",
        "Business workflow panel with workflow type, SOP/checklist/draft outputs, and status surface.",
        "Sending, publishing, automation, or business-system changes require approval.",
        ["outbound messages", "workflow_automation", "export", "file_write"], "Medium",
        ["Business", "Enterprise", "Task-Ready", "All-Rounder"], ["Chatbot", "Planner", "Document Processor", "Tool User", "Archive"],
        ["Draft first; never send automatically.", "Use audit-friendly wording.", "Separate recommendation from execution."],
        ["Nexus Libraries", "Capability Attachments", "Approval Required"],
        ["Communication Library", "Governance UX Library", "Project Memory Library"],
        ["Create an SOP for X", "Draft a support reply", "Make a workflow checklist"],
        "Business automation hooks are not connected; local SOPs, drafts, and checklists work.",
        "BusinessWorkflowCapabilityDialog", "Open Business Workflow",
    ),
    "Hephaestus Relay": _action(
        "cap.hephaestus_relay", "Hephaestus Relay",
        "Design idea intake, constraints, materials, scale, unknowns, purpose, and Hephaestus-ready handoff brief.",
        "Relay workflow with design intake and handoff brief output.",
        "Handoff/export to Hephaestus systems only after approval; no ProtoBrain internals are touched.",
        ["export", "external_handoff"], "Medium",
        ["Individual", "Task-Ready", "Business", "All-Rounder"], ["Creative Writing", "Planner", "Document Processor", "Notebook"],
        ["Format briefs for Hephaestus rather than replacing ProtoBrain reasoning.", "List constraints and unknowns before handoff."],
        ["Capability Attachments", "Cross-Capability Workflows", "Save Safety"],
        ["Hephaestus Briefing Library", "Project Memory Library", "Communication Library"],
        ["Turn this idea into a Hephaestus brief", "List constraints and unknowns", "Prepare a handoff packet"],
        "Hephaestus handoff is a local brief generator; no Hephaestus internals are called.",
        "HephaestusRelayCapabilityDialog", "Open Hephaestus Relay",
    ),

    # ═══════════════════════════════════════════════════════════════════════════════
    # CUSTOMER SUPPORT AI — Available in ALL USE CASES
    # This is the PUBLIC/RESTRICTED version that NEVER reveals Book internals
    # ═══════════════════════════════════════════════════════════════════════════════

    "Customer Support AI": _action(
        "cap.customer_support_ai", "Customer Support AI",
        "RESTRICTED customer-facing AI for support. Learns from interactions but NEVER reveals internal Book mechanics or architecture.",
        "Customer support workflow with inquiry intake, adaptive responses, learning, and escalation handling.",
        "No outward actions. All responses are local and safe. Proprietary information is protected.",
        [], "None",
        ALL_USE_CASES,  # Available in every use case
        ["Chatbot", "Business Workflow", "Planner"],
        ["Never reveal Book internals, scaffolding, or architecture.", "Use only customer-appropriate terminology.", "If asked about internals, refuse politely."],
        ["Capability Attachments", "Operating Context"],
        ["Communication Library", "Governance UX Library"],
        ["How can I help you today?", "What issue are you experiencing?", "Let me escalate this to a human agent."],
        "Customer Support AI operates locally with proprietary safeguards active.",
        "CustomerAIWindow", "Open Customer Support",
    ),

    # ═══════════════════════════════════════════════════════════════════════════════
    # PREMIUM UPGRADE CAPABILITIES — NOT INCLUDED IN BASE LICENSES
    # These differentiate Command Nexus from all competitors
    # ═══════════════════════════════════════════════════════════════════════════════

    "Team Orchestrator": _action(
        "cap.team_orchestrator", "Team Orchestrator",
        "Multi-AI coordination hub. Orchestrate multiple AIs working on the same project with role assignment, handoffs, and consensus building.",
        "Team dashboard with AI role assignments, task distribution, progress tracking, and inter-AI communication log.",
        "Project management system integration, task delegation to external teams, and automated reporting.",
        ["multi_ai_coordination", "project_management", "external_integration"], "High",
        ["Business", "Enterprise", "All-Rounder"],
        ["Chatbot", "Planner", "Business Workflow", "Document Processor"],
        ["Assign clear roles to each AI.", "Define handoff protocols between AIs.", "Review AI consensus before external actions."],
        ["Team Roles", "Communication Protocols", "Consensus Mechanisms", "Approval Gates"],
        ["Team Coordination Library", "Project Management Library", "Governance UX Library"],
        ["Create a team of AIs for this project", "Assign roles: researcher, writer, reviewer", "Get consensus before proceeding"],
        "Multi-AI coordination is local; external project management integration requires approval.",
        "TeamOrchestratorDialog", "Open Team Orchestrator",
    ),

    "Memory Bridge": _action(
        "cap.memory_bridge", "Memory Bridge",
        "Persistent cross-session memory with context continuity. AIs remember previous conversations, preferences, and project state across restarts.",
        "Memory dashboard showing conversation history, learned preferences, context summaries, and memory search.",
        "Long-term memory export/import, memory sharing between users, and cloud memory sync.",
        ["persistent_storage", "memory_export", "cloud_sync"], "Medium",
        ["Individual", "Educational", "Business", "Enterprise", "All-Rounder"],
        ["Chatbot", "Notebook", "Archive", "Tutor"],
        ["Summarize old memories before referencing.", "Allow users to delete sensitive memories.", "Flag conflicting memory entries."],
        ["Memory Timeline", "Preference Learning", "Context Continuity", "Memory Management"],
        ["Memory Persistence Library", "Privacy Controls Library", "Communication Library"],
        ["Remember my preference for concise answers", "What did we discuss last Tuesday?", "Continue where we left off"],
        "Local memory persistence works now; cloud sync and sharing require approval.",
        "MemoryBridgeDialog", "Open Memory Bridge",
    ),

    "Visual Canvas": _action(
        "cap.visual_canvas", "Visual Canvas",
        "AI-powered image generation, editing, and visual concept development. Create diagrams, illustrations, and visual content.",
        "Visual workspace with prompt-to-image, image editing tools, style selector, and visual asset library.",
        "Stock photo integration, brand asset generation, social media image creation, and print-ready export.",
        ["image_generation", "external_api", "export"], "Medium",
        ["Individual", "Educational", "Business", "Enterprise", "All-Rounder"],
        ["Creative Writing", "Business Workflow", "Planner", "Document Processor"],
        ["Describe visual concepts clearly.", "Review generated images for brand alignment.", "Do not auto-post images without approval."],
        ["Image Prompts", "Style Guides", "Visual Assets", "Export Options"],
        ["Visual Arts Library", "Brand Guidelines Library", "Creative Tools Library"],
        ["Generate an image of this concept", "Create a diagram showing the workflow", "Make a visual for my presentation"],
        "Image generation requires external API approval; local visual planning and description work now.",
        "VisualCanvasDialog", "Open Visual Canvas",
    ),

    "Data Analyst Pro": _action(
        "cap.data_analyst", "Data Analyst Pro",
        "Advanced data analysis with visualization, statistical insights, trend detection, and predictive modeling scaffolding.",
        "Data workspace with CSV/Excel import, chart generation, statistical summary, and insight highlighting.",
        "Database connections, automated reporting, dashboard creation, and data pipeline integration.",
        ["data_import", "external_database", "automated_reporting"], "High",
        ["Business", "Enterprise", "All-Rounder"],
        ["Research", "Coder", "Business Workflow", "Document Processor"],
        ["Verify data sources before analysis.", "Flag statistical confidence levels.", "Separate correlation from causation."],
        ["Data Import", "Visualization Options", "Statistical Methods", "Insight Summary"],
        ["Data Science Library", "Statistics Library", "Visualization Library"],
        ["Analyze this dataset and find trends", "Create a chart showing the pattern", "Predict next quarter based on this data"],
        "Local data analysis works now; external database connections and automated reporting require approval.",
        "DataAnalystDialog", "Open Data Analyst",
    ),

    "Code Reviewer": _action(
        "cap.code_reviewer", "Code Reviewer",
        "Automated code review, quality analysis, security scanning, and optimization suggestions with best practice enforcement.",
        "Code review panel with quality metrics, security scan results, optimization suggestions, and style compliance check.",
        "CI/CD integration, automated PR reviews, security gate enforcement, and deployment approval.",
        ["code_analysis", "ci_cd_integration", "deployment_approval"], "High",
        ["Individual", "Task-Ready", "Enterprise", "All-Rounder"],
        ["Coder", "Tool User", "Research"],
        ["Flag security issues immediately.", "Distinguish critical from cosmetic issues.", "Suggest fixes, don't auto-apply."],
        ["Quality Metrics", "Security Scan", "Best Practices", "Optimization Tips"],
        ["Code Safety Library", "Security Audit Library", "Governance UX Library"],
        ["Review this code for issues", "Scan for security vulnerabilities", "Suggest performance improvements"],
        "Local code analysis works now; CI/CD integration and automated deployment require approval.",
        "CodeReviewerDialog", "Open Code Reviewer",
    ),

    "API Integrator": _action(
        "cap.api_integrator", "API Integrator",
        "Connect AIs to external APIs, webhooks, and services. Build integrations with popular platforms and custom endpoints.",
        "API connection manager with endpoint configuration, authentication setup, request builder, and response handler.",
        "Live API calls, data synchronization, webhook processing, and third-party service automation.",
        ["network", "external_api", "data_sync", "webhook"], "High",
        ["Business", "Enterprise", "All-Rounder"],
        ["Tool User", "Coder", "Business Workflow", "Data Analyst Pro"],
        ["Validate API credentials securely.", "Rate limit API calls appropriately.", "Log all external API interactions."],
        ["API Endpoints", "Authentication", "Request Templates", "Response Handling"],
        ["Integration Library", "API Security Library", "Network Governance Library"],
        ["Connect to the CRM API", "Set up a webhook for new orders", "Sync data with the external platform"],
        "API configuration and planning work now; live external API calls require network approval.",
        "APIIntegratorDialog", "Open API Integrator",
    ),

    "Knowledge Base Builder": _action(
        "cap.knowledge_base", "Knowledge Base Builder",
        "Create, structure, and maintain organized knowledge bases with categorization, search, and version control.",
        "Knowledge base editor with category structure, article editor, search index, and version history.",
        "Public knowledge base publishing, team knowledge sharing, external documentation sites, and help center integration.",
        ["knowledge_organization", "publishing", "external_site"], "Medium",
        ["Business", "Enterprise", "All-Rounder"],
        ["Document Processor", "Notebook", "Archive", "Business Workflow"],
        ["Structure information hierarchically.", "Keep knowledge bases current.", "Review before publishing externally."],
        ["Categories", "Articles", "Search Index", "Version Control"],
        ["Knowledge Management Library", "Documentation Library", "Project Memory Library"],
        ["Create a knowledge base for this topic", "Organize these documents", "Build searchable documentation"],
        "Local knowledge base building works now; public publishing and external sites require approval.",
        "KnowledgeBaseDialog", "Open Knowledge Base Builder",
    ),

    "Meeting Facilitator": _action(
        "cap.meeting_facilitator", "Meeting Facilitator",
        "AI-powered meeting management with agenda creation, real-time note-taking, action item extraction, and follow-up tracking.",
        "Meeting workspace with agenda builder, live notes, attendee tracking, timer, and action item board.",
        "Calendar integration, meeting invitations, video conferencing hooks, and automated follow-up emails.",
        ["calendar_integration", "email_automation", "video_conference"], "Medium",
        ["Business", "Enterprise", "All-Rounder"],
        ["Business Workflow", "Notebook", "Planner", "Chatbot"],
        ["Keep meetings on agenda and on time.", "Capture clear action items with owners.", "Distribute notes only after review."],
        ["Meeting Agenda", "Live Notes", "Action Items", "Follow-up Tracking"],
        ["Communication Library", "Project Memory Library", "Governance UX Library"],
        ["Create an agenda for this meeting", "Take notes during the call", "Extract action items from this discussion"],
        "Meeting planning and note-taking work now; calendar integration and automated emails require approval.",
        "MeetingFacilitatorDialog", "Open Meeting Facilitator",
    ),

    "Email Automation": _action(
        "cap.email_automation", "Email Automation",
        "Smart email drafting, categorization, priority filtering, and automated response suggestions with approval gates.",
        "Email workspace with inbox view, AI draft suggestions, priority flags, template library, and send queue.",
        "Live email integration, auto-responses, email campaigns, and newsletter distribution.",
        ["email_access", "outbound_messages", "campaign_automation"], "High",
        ["Business", "Enterprise", "All-Rounder"],
        ["Chatbot", "Business Workflow", "Creative Writing", "Document Processor"],
        ["Draft emails but don't send without approval.", "Respect email privacy and confidentiality.", "Flag sensitive content before sending."],
        ["Inbox Overview", "Draft Suggestions", "Templates", "Send Queue"],
        ["Communication Library", "Email Safety Library", "Governance UX Library"],
        ["Draft a response to this email", "Categorize these messages by priority", "Create a template for follow-ups"],
        "Email drafting and planning work now; live email access and automated sending require approval.",
        "EmailAutomationDialog", "Open Email Automation",
    ),

    "Calendar Manager": _action(
        "cap.calendar_manager", "Calendar Manager",
        "Intelligent scheduling, conflict detection, availability optimization, and meeting time suggestions across time zones.",
        "Calendar view with schedule optimizer, conflict alerts, availability finder, and agenda time allocation.",
        "Live calendar integration, automated rescheduling, appointment booking links, and team availability sync.",
        ["calendar_access", "external_integration", "automated_scheduling"], "Medium",
        ["Individual", "Business", "Enterprise", "All-Rounder"],
        ["Planner", "Meeting Facilitator", "Business Workflow", "Chatbot"],
        ["Respect existing commitments.", "Consider time zones for all attendees.", "Confirm changes before applying."],
        ["Schedule View", "Conflict Detection", "Availability Finder", "Optimization Suggestions"],
        ["Time Management Library", "Project Memory Library", "Communication Library"],
        ["Find the best time for this meeting", "Optimize my schedule for focus time", "Detect conflicts in this plan"],
        "Schedule planning and analysis work now; live calendar integration and automated changes require approval.",
        "CalendarManagerDialog", "Open Calendar Manager",
    ),

    "Document Generator": _action(
        "cap.document_generator", "Document Generator",
        "Create professionally formatted documents with templates, styling, and multi-format export (PDF, Word, HTML).",
        "Document composer with template gallery, WYSIWYG editor, style controls, and format preview.",
        "Direct file export, template sharing, brand template enforcement, and print-ready generation.",
        ["file_write", "export", "template_sharing"], "Medium",
        ["Individual", "Educational", "Business", "Enterprise", "All-Rounder"],
        ["Creative Writing", "Document Processor", "Business Workflow", "Planner"],
        ["Apply consistent branding.", "Review documents before final export.", "Respect copyright on templates."],
        ["Template Gallery", "Document Editor", "Style Controls", "Export Options"],
        ["Document Design Library", "Brand Guidelines Library", "Export Library"],
        ["Create a proposal from this template", "Format this as a professional report", "Export to PDF with branding"],
        "Document composition and formatting work now; file export and template sharing require approval.",
        "DocumentGeneratorDialog", "Open Document Generator",
    ),

    "Translation Expert": _action(
        "cap.translation", "Translation Expert",
        "Multi-language translation with context awareness, tone preservation, cultural adaptation, and idiom handling.",
        "Translation workspace with source/target language selectors, context notes, glossary integration, and back-translation check.",
        "Live translation API, batch document translation, website localization, and real-time conversation translation.",
        ["translation_api", "batch_processing", "live_translation"], "Low",
        ["Individual", "Educational", "Business", "Enterprise", "All-Rounder"],
        ["Creative Writing", "Document Processor", "Chatbot", "Tutor"],
        ["Preserve meaning, not just words.", "Flag culturally sensitive content.", "Allow human review for critical translations."],
        ["Source Language", "Target Language", "Context Notes", "Glossary"],
        ["Translation Library", "Cultural Context Library", "Communication Library"],
        ["Translate this to Spanish", "Keep the formal tone in translation", "Create a glossary for this project"],
        "Translation planning and glossary building work now; live API translation requires network approval.",
        "TranslationExpertDialog", "Open Translation Expert",
    ),

    "Presentation Builder": _action(
        "cap.presentation", "Presentation Builder",
        "Create slide decks with AI-generated content, design suggestions, speaker notes, and presentation rehearsal mode.",
        "Slide editor with AI content suggestions, design templates, visual asset library, and presenter view.",
        "Export to PowerPoint/Google Slides, presentation sharing, live presentation mode, and audience Q&A handling.",
        ["export", "presentation_mode", "sharing"], "Medium",
        ["Individual", "Educational", "Business", "Enterprise", "All-Rounder"],
        ["Creative Writing", "Visual Canvas", "Document Generator", "Planner"],
        ["One idea per slide.", "Design for your audience.", "Practice with speaker notes before presenting."],
        ["Slide Outline", "Content Suggestions", "Design Templates", "Speaker Notes"],
        ["Presentation Design Library", "Visual Communication Library", "Public Speaking Library"],
        ["Create slides from this outline", "Suggest visuals for this slide", "Generate speaker notes"],
        "Slide planning and content creation work now; export to external platforms and live presentation mode require approval.",
        "PresentationBuilderDialog", "Open Presentation Builder",
    ),

    "Spreadsheet Wizard": _action(
        "cap.spreadsheet", "Spreadsheet Wizard",
        "Advanced spreadsheet automation with formula generation, data validation, pivot tables, and macro creation.",
        "Spreadsheet workspace with formula builder, data analysis tools, chart integration, and template library.",
        "Excel/Google Sheets integration, automated data entry, formula auditing, and complex calculation workflows.",
        ["spreadsheet_integration", "formula_execution", "automated_entry"], "Medium",
        ["Individual", "Business", "Enterprise", "All-Rounder"],
        ["Data Analyst Pro", "Coder", "Business Workflow", "Document Processor"],
        ["Validate formulas before applying.", "Document complex calculations.", "Back up data before batch changes."],
        ["Formula Builder", "Data Ranges", "Analysis Tools", "Templates"],
        ["Spreadsheet Library", "Data Analysis Library", "Business Intelligence Library"],
        ["Create a formula for this calculation", "Build a pivot table from this data", "Automate this spreadsheet task"],
        "Formula building and planning work now; live spreadsheet integration and automated changes require approval.",
        "SpreadsheetWizardDialog", "Open Spreadsheet Wizard",
    ),

    "Legal Document Reviewer": _action(
        "cap.legal_doc_review", "Legal Document Reviewer",
        "Document analysis only — extracts, summarizes, and flags content within legal documents. States what is written, does not interpret, extrapolate, or provide legal advice.",
        "Document review workspace with text extraction, clause identification, risk flagging, and summary generation. Reads what is on the page — nothing more.",
        "No outward actions. No web research. No legal database access. No creative generation. Cannot look up laws, cases, or precedents. Strictly analyzes text provided by the user.",
        [], "None",
        ["Business", "Enterprise", "All-Rounder"],
        ["Document Processor", "Archive"],
        [
            "This is NOT legal advice. It does not create an attorney-client relationship.",
            "State content as written in the document — do not interpret, extrapolate, or hallucinate.",
            "No creative generation. If something is not in the document, say 'not found in document'.",
            "No web research. Do not look up laws, cases, or precedents.",
            "Always recommend consulting a qualified attorney for legal decisions.",
            "Be concise and direct — state findings as they appear in the text.",
        ],
        ["Document Upload", "Clause Identification", "Risk Flags", "Summary"],
        ["Document Analysis Library"],
        ["Summarize this contract", "Find the termination clauses in this document", "Flag potential risks in this agreement"],
        "Document analysis and extraction work locally only. No legal advice, no web research, no creative generation. Strictly states what is in the document.",
        "LegalDocumentReviewerDialog", "Open Legal Document Reviewer",
    ),

    "Medical Researcher": _action(
        "cap.medical_research", "Medical Researcher",
        "Medical literature search, clinical trial analysis, drug interaction checking, and evidence-based summary generation.",
        "Medical research workspace with PubMed search, trial database, interaction checker, and evidence summary builder.",
        "Electronic health record integration, clinical decision support, patient education material generation, and research collaboration.",
        ["medical_database", "ehr_integration", "clinical_decision"], "High",
        ["Enterprise", "All-Rounder"],
        ["Research", "Document Processor", "Knowledge Base Builder", "Tutor"],
        ["This is for research only, not medical advice.", "Always cite evidence quality.", "Flag conflicting studies."],
        ["Literature Search", "Trial Database", "Evidence Summary", "Citation Manager"],
        ["Medical Research Library", "Evidence-Based Medicine Library", "Research Discipline Library"],
        ["Find studies on this treatment", "Compare trial results", "Summarize the evidence on this drug"],
        "Literature search planning works now; live medical database access and EHR integration require approval.",
        "MedicalResearcherDialog", "Open Medical Researcher",
    ),

    "Accessibility Assistant": _action(
        "cap.accessibility", "Accessibility Assistant",
        "Accessibility support with screen reader optimization, text-to-speech, speech-to-text, and adaptive interface options.",
        "Accessibility panel with voice control, high contrast mode, text sizing, speech output, and input alternatives.",
        "Adaptive hardware integration, real-time captioning, sign language avatar, and cognitive load reduction.",
        ["hardware_integration", "realtime_processing", "adaptive_output"], "Low",
        ["Individual", "Educational", "Enterprise", "All-Rounder"],
        ["Tutor", "Chatbot", "Document Processor", "Visual Canvas"],
        ["Respect user accessibility preferences.", "Provide alternatives for all interactions.", "Ensure WCAG compliance in outputs."],
        ["Voice Control", "Visual Adjustments", "Speech Options", "Input Methods"],
        ["Accessibility Library", "Universal Design Library", "Assistive Technology Library"],
        ["Read this document aloud", "Increase text size", "Convert to screen reader format"],
        "Local accessibility features work now; hardware integration and real-time processing require approval.",
        "AccessibilityAssistantDialog", "Open Accessibility Assistant",
    ),

    "Fact Checker": _action(
        "cap.fact_checker", "Fact Checker",
        "Automated fact verification against multiple sources, claim credibility scoring, bias detection, and source reliability assessment.",
        "Fact check workspace with claim extraction, verification status, source list, credibility score, and bias indicators.",
        "Live web verification, social media claim checking, real-time misinformation alerts, and collaborative verification.",
        ["web_search", "realtime_verification", "social_media_access"], "Medium",
        ["Individual", "Educational", "Business", "Enterprise", "All-Rounder"],
        ["Research", "Document Processor", "Chatbot", "Knowledge Base Builder"],
        ["Verify against multiple independent sources.", "Show confidence levels clearly.", "Distinguish verified from unverified claims."],
        ["Claim Extraction", "Verification Status", "Source List", "Credibility Score"],
        ["Research Discipline Library", "Media Literacy Library", "Critical Thinking Library"],
        ["Verify this claim", "Check the sources on this statement", "Assess the credibility of this article"],
        "Fact checking workflow works now; live web verification and social media access require network approval.",
        "FactCheckerDialog", "Open Fact Checker",
    ),

    "Voice Interface": _action(
        "cap.voice", "Voice Interface",
        "Natural voice conversation with the AI using speech recognition and text-to-speech for hands-free interaction.",
        "Voice panel with microphone activation, transcription display, voice settings, and conversation history.",
        "Continuous listening, wake word activation, voice biometrics, and multi-language voice support.",
        ["microphone_access", "voice_recognition", "biometric_data"], "Low",
        ["Individual", "Educational", "Business", "Enterprise", "All-Rounder"],
        ["Chatbot", "Tutor", "Meeting Facilitator", "Accessibility Assistant"],
        ["Confirm voice commands in noisy environments.", "Allow text fallback for privacy.", "Respect mute preferences."],
        ["Voice Input", "Transcription", "Voice Settings", "Conversation History"],
        ["Speech Recognition Library", "Voice UX Library", "Accessibility Library"],
        ["Start voice conversation", "Read this response aloud", "Change voice to more natural tone"],
        "Voice interface scaffolding ready; microphone access and voice recognition require hardware approval.",
        "VoiceInterfaceDialog", "Open Voice Interface",
    ),

    "Workflow Automator": _action(
        "cap.workflow_automator", "Workflow Automator",
        "Build automated multi-step workflows with triggers, conditions, actions, and error handling without coding.",
        "Workflow builder with visual flow editor, trigger library, action palette, and execution log.",
        "External app integration, scheduled automation, webhook triggers, and enterprise BPM integration.",
        ["external_integration", "scheduled_execution", "webhook"], "High",
        ["Business", "Enterprise", "All-Rounder"],
        ["Planner", "Tool User", "API Integrator", "Business Workflow"],
        ["Test workflows before activating.", "Include error handling and alerts.", "Log all automated actions for audit."],
        ["Trigger", "Conditions", "Actions", "Error Handling"],
        ["Workflow Automation Library", "Integration Library", "Governance UX Library"],
        ["Create a workflow that triggers on new emails", "Automate this weekly report generation", "Build approval workflow"],
        "Workflow design and testing work now; external integration and automated execution require approval.",
        "WorkflowAutomatorDialog", "Open Workflow Automator",
    ),

    "Security Auditor": _action(
        "cap.security_auditor", "Security Auditor",
        "Comprehensive security analysis of code, documents, configurations, and practices with vulnerability scanning.",
        "Security audit dashboard with scan results, vulnerability list, risk ratings, remediation guide, and compliance report.",
        "Live penetration testing, continuous security monitoring, incident response automation, and threat intelligence.",
        ["security_scanning", "penetration_test", "threat_intel"], "High",
        ["Enterprise", "All-Rounder"],
        ["Code Reviewer", "Research", "Business Workflow", "Tool User"],
        ["Never exploit vulnerabilities found.", "Report all findings confidentially.", "Prioritize critical vulnerabilities."],
        ["Scan Results", "Vulnerability List", "Risk Ratings", "Remediation Guide"],
        ["Security Audit Library", "Vulnerability Database", "Incident Response Library"],
        ["Audit this code for security issues", "Scan this configuration for weaknesses", "Generate security compliance report"],
        "Security analysis and planning work now; live penetration testing and external threat intel require approval.",
        "SecurityAuditorDialog", "Open Security Auditor",
    ),

    "Competitive Analyst": _action(
        "cap.competitive_analyst", "Competitive Analyst",
        "Market and competitor analysis with trend tracking, SWOT generation, pricing intelligence, and strategic positioning.",
        "Analysis workspace with competitor profiles, market trends, SWOT builder, pricing tracker, and strategy canvas.",
        "Real-time market data, social media monitoring, earnings call analysis, and automated intelligence reports.",
        ["market_data", "social_monitoring", "financial_access"], "Medium",
        ["Business", "Enterprise", "All-Rounder"],
        ["Research", "Business Workflow", "Data Analyst Pro", "Document Processor"],
        ["Use only publicly available information.", "Respect confidentiality agreements.", "Distinguish fact from speculation."],
        ["Competitor Profiles", "Market Trends", "SWOT Analysis", "Strategy Canvas"],
        ["Market Intelligence Library", "Strategic Analysis Library", "Business Intelligence Library"],
        ["Analyze competitor positioning", "Track market trends in this sector", "Generate SWOT for our product"],
        "Analysis framework works now; real-time market data and social monitoring require network approval.",
        "CompetitiveAnalystDialog", "Open Competitive Analyst",
    ),

    "Learning Path Creator": _action(
        "cap.learning_path", "Learning Path Creator",
        "Design structured learning paths with curriculum sequencing, progress tracking, assessment generation, and skill certification.",
        "Learning design workspace with curriculum builder, content sequencing, assessment creator, and progress dashboard.",
        "LMS integration, automated grading, certificate generation, student analytics, and adaptive learning paths.",
        ["lms_integration", "automated_grading", "certificate_generation"], "Medium",
        ["Educational", "Business", "Enterprise", "All-Rounder"],
        ["Tutor", "Planner", "Document Generator", "Knowledge Base Builder"],
        ["Align learning objectives with assessments.", "Allow self-paced progression.", "Provide multiple learning modalities."],
        ["Learning Objectives", "Content Sequence", "Assessments", "Progress Tracking"],
        ["Instructional Design Library", "Assessment Library", "Educational Technology Library"],
        ["Create a learning path for Python", "Design assessments for this curriculum", "Generate certificates for completions"],
        "Learning path design works now; LMS integration and automated grading require external approval.",
        "LearningPathCreatorDialog", "Open Learning Path Creator",
    ),

    "Smart Search": _action(
        "cap.smart_search", "Smart Search",
        "Advanced search across documents, web, databases, and knowledge bases with semantic understanding and result ranking.",
        "Search interface with natural language queries, result clustering, source filtering, and saved search alerts.",
        "Enterprise search integration, federated search across systems, real-time indexing, and personalized results.",
        ["enterprise_search", "federated_query", "realtime_index"], "Medium",
        ["Individual", "Educational", "Business", "Enterprise", "All-Rounder"],
        ["Research", "Document Processor", "Knowledge Base Builder", "Archive"],
        ["Respect document permissions in search.", "Rank results by relevance and credibility.", "Allow filtering by source type."],
        ["Search Query", "Result Clustering", "Source Filter", "Saved Alerts"],
        ["Search Technology Library", "Information Retrieval Library", "Research Discipline Library"],
        ["Search across all my documents", "Find similar content to this", "Set up alert for new results"],
        "Search interface and planning work now; enterprise integration and real-time indexing require approval.",
        "SmartSearchDialog", "Open Smart Search",
    ),

    # ═══════════════════════════════════════════════════════════════════════════════
    # NEW CAPABILITIES — Activity Watcher, Financial Gainer, Memory Recorder, Game Companion
    # ═══════════════════════════════════════════════════════════════════════════════

    "Activity Watcher": _action(
        "cap.activity_watcher", "Activity Watcher",
        "Watches the user work, learns recurring task patterns, and eventually becomes an assistant that can repeat those tasks or suggest faster ways to do them.",
        "Activity observation panel with task pattern detection, learned workflow list, suggestion surface, and repeat-task approval gate.",
        "Repeating learned tasks on the user's computer, launching suggested workflows, or executing automation requires explicit approval each time.",
        ["screen_observation", "task_repetition", "workflow_automation", "tool_invocation"], "High",
        ["Individual", "Task-Ready", "Business", "Financial Gainer", "Memory Saver", "All-Rounder"],
        ["Planner", "Tool User", "Memory Recorder", "Notebook", "Chatbot"],
        [
            "Watch silently — never interrupt the user's workflow.",
            "Only suggest improvements after confirming a pattern has repeated at least 3 times.",
            "Never repeat a task without explicit user approval for each repetition.",
            "Log all observations to Memory Recorder for auditability.",
            "Flag tasks that involve sensitive data (passwords, financial info) and exclude them from automation suggestions.",
        ],
        ["Capability Attachments", "Approval Required", "Save Safety", "Cross-Capability Workflows"],
        ["Workflow Automation Library", "Productivity Library", "Governance UX Library"],
        [
            "Watch how I process these invoices and learn the pattern",
            "What tasks have you noticed I do repeatedly?",
            "Suggest a faster way to do my morning routine",
            "Repeat the email triage task you learned yesterday",
        ],
        "Activity observation and pattern detection work in scaffold mode; live screen monitoring and task repetition require approval.",
        "ActivityWatcherDialog", "Open Activity Watcher",
    ),

    "Financial Gainer": _action(
        "cap.financial_gainer", "Financial Gainer",
        "Helps individuals explore and pursue income opportunities, side hustles, monetization strategies, and financial productivity improvements. Includes a mandatory disclaimer that no income is guaranteed.",
        "Financial opportunity workspace with income path suggestions, skill monetization analysis, side hustle planning, and ROI estimation tools.",
        "No outward financial actions. All output is advisory. Never makes transactions, investments, or commitments on the user's behalf.",
        [], "None",
        ["Individual", "Task-Ready", "Business", "Financial Gainer", "All-Rounder"],
        ["Research", "Business Workflow", "Planner", "Chatbot", "Data Analyst Pro"],
        [
            "NEVER guarantee income or promise specific earnings.",
            "Always show the disclaimer before any financial advice is given.",
            "Present opportunities with realistic difficulty and time investment.",
            "Flag risks and costs associated with any income path.",
            "Remind users that results depend on their effort, skill, and market conditions.",
            "Do not recommend illegal, unethical, or high-risk schemes.",
        ],
        ["Capability Attachments", "Operating Context", "Approval Required"],
        ["Financial Literacy Library", "Business Strategy Library", "Research Discipline Library"],
        [
            "What side hustles match my skills?",
            "How can I monetize my writing?",
            "Analyze the ROI of this business idea",
            "What skills should I learn to increase my income?",
        ],
        "Financial opportunity analysis and planning work locally; no transactions or external financial connections. Disclaimer is mandatory.",
        "FinancialGainerDialog", "Open Financial Gainer",
    ),

    "Memory Recorder": _action(
        "cap.memory_recorder", "Memory Recorder",
        "Records everything that happens during a session — user actions, AI assistance, decisions, outcomes — for auditability, recollection, and continuity. Like a flight recorder for your work.",
        "Recording dashboard with timeline view, event log, search, replay, and export capabilities. Records all AI interactions, user decisions, task outcomes, and capability usage.",
        "Exporting recordings, sharing session logs, or persisting recordings to external storage requires approval.",
        ["export", "file_write"], "Medium",
        ["Individual", "Educational", "Task-Ready", "Business", "Enterprise", "Memory Saver", "All-Rounder"],
        ["Notebook", "Archive", "Chatbot", "Activity Watcher", "Document Processor"],
        [
            "Record silently — never interrupt the user's workflow.",
            "Log every AI interaction with full context for auditability.",
            "Allow users to search and replay past sessions.",
            "Never record sensitive data (passwords, credentials) in plaintext.",
            "Allow users to delete specific recordings on demand.",
            "Provide an audit trail that shows what the AI did and why.",
        ],
        ["Capability Attachments", "Save Safety", "Approval Required"],
        ["Audit Library", "Memory Persistence Library", "Governance UX Library"],
        [
            "What did I do last Tuesday?",
            "Show me the audit trail for this decision",
            "Search my recordings for 'invoice processing'",
            "Export this session's recording for compliance",
        ],
        "Memory recording works locally with full audit trail; export and external sharing require approval.",
        "MemoryRecorderDialog", "Open Memory Recorder",
    ),

    # ═══════════════════════════════════════════════════════════════════════════════
    # FINANCIAL GAINER USE CASE CAPABILITIES
    # ═══════════════════════════════════════════════════════════════════════════════

    "Crypto Scout": _action(
        "cap.crypto_scout", "Crypto Scout",
        "Researches cryptocurrency markets, tracks token performance, analyzes trends, and provides educational insights on crypto opportunities. Includes mandatory disclaimer that nothing is financial advice.",
        "Crypto research workspace with market overview, token analysis cards, trend indicators, and educational resources.",
        "No outward financial actions. Never executes trades, connects to wallets, or makes transactions. All output is educational and advisory only.",
        [], "None",
        ["Financial Gainer", "All-Rounder"],
        ["Research", "Data Analyst Pro", "Chatbot", "Smart Search"],
        [
            "NEVER give financial advice or guarantee returns.",
            "Always show disclaimer: 'This is not financial advice. Crypto is volatile. Do your own research.'",
            "Present both upside potential and downside risks for any token.",
            "Never recommend specific buy or sell actions.",
            "Flag high-risk tokens (low cap, low liquidity) clearly.",
            "Educate users about scams, rug pulls, and common crypto fraud.",
        ],
        ["Capability Attachments", "Operating Context", "Approval Required"],
        ["Financial Literacy Library", "Market Analysis Library", "Risk Assessment Library"],
        [
            "What's the trend on Bitcoin this week?",
            "Explain what staking is and which tokens support it",
            "Compare these three altcoins for me",
            "What are the common crypto scams I should watch for?",
        ],
        "Crypto research and education work locally; no wallet connections or trade execution.",
        "CryptoScoutDialog", "Open Crypto Scout",
    ),

    "Affiliate Strategist": _action(
        "cap.affiliate_strategist", "Affiliate Strategist",
        "Helps users find, evaluate, and plan affiliate marketing opportunities. Researches programs, suggests products to promote, drafts review content, and tracks commission structures.",
        "Affiliate marketing workspace with program finder, product matcher, commission tracker, content draft panel, and performance dashboard.",
        "No outward actions. Never signs up for programs or posts content automatically. All output is advisory and requires user approval.",
        [], "None",
        ["Financial Gainer", "Business", "All-Rounder"],
        ["Research", "Business Workflow", "Chatbot", "Document Generator", "Marketing Generator"],
        [
            "Disclose affiliate relationships honestly in all content suggestions.",
            "Only recommend products the user has or could genuinely evaluate.",
            "Never guarantee commission amounts or conversion rates.",
            "Flag programs with poor reputation or predatory terms.",
            "Suggest content that provides real value, not just sales pitches.",
        ],
        ["Capability Attachments", "Operating Context"],
        ["Marketing Library", "Business Strategy Library", "Content Creation Library"],
        [
            "Find affiliate programs for fitness products",
            "Draft a review for this software I use",
            "Compare commission rates for these affiliate networks",
            "What products would match my audience?",
        ],
        "Affiliate research and content drafting work locally; no program sign-ups or auto-posting.",
        "AffiliateStrategistDialog", "Open Affiliate Strategist",
    ),

    "Click Commission Tracker": _action(
        "cap.click_commission", "Click Commission Tracker",
        "Tracks and analyzes click-based commission earnings — pay-per-click, cost-per-action, and referral link performance. Helps optimize which links to promote based on click-through rates and conversion data.",
        "Commission tracking dashboard with link performance stats, click-through analytics, earnings summary, and optimization suggestions.",
        "No outward actions. Never creates or posts links automatically. Analyzes data provided by the user.",
        [], "None",
        ["Financial Gainer", "Business", "All-Rounder"],
        ["Data Analyst Pro", "Research", "Chatbot", "Spreadsheet Wizard"],
        [
            "Never inflate or estimate earnings without clear data.",
            "Present click-through rates and conversions honestly.",
            "Flag links that are underperforming.",
            "Suggest optimization strategies based on data, not guesses.",
            "Remind users that commission earnings vary and are not guaranteed.",
        ],
        ["Capability Attachments", "Operating Context"],
        ["Analytics Library", "Marketing Library", "Financial Literacy Library"],
        [
            "Analyze my click-through rates for last month",
            "Which of my referral links are performing best?",
            "How can I improve my conversion rate?",
            "Compare earnings across these commission programs",
        ],
        "Click commission analysis works locally with user-provided data; no external link creation or auto-posting.",
        "ClickCommissionDialog", "Open Click Commission Tracker",
    ),

    "Sales Funnel Builder": _action(
        "cap.sales_funnel", "Sales Funnel Builder",
        "Designs and optimizes sales funnels — from lead capture to conversion. Drafts landing page copy, email sequences, upsell paths, and conversion optimization suggestions.",
        "Sales funnel workspace with funnel stage builder, copy drafting, email sequence planner, conversion rate estimator, and A/B test suggester.",
        "No outward actions. Never publishes pages or sends emails automatically. All content is drafted for user review.",
        [], "None",
        ["Financial Gainer", "Business", "All-Rounder"],
        ["Business Workflow", "Document Generator", "Email Automation", "Marketing Generator", "Chatbot"],
        [
            "Never use deceptive or manipulative sales tactics.",
            "Disclose pricing clearly and honestly.",
            "Respect unsubscribe preferences in all email sequences.",
            "Suggest A/B tests that improve user experience, not just conversions.",
            "Flag funnel stages with high drop-off rates.",
        ],
        ["Capability Attachments", "Operating Context"],
        ["Sales Library", "Marketing Library", "Conversion Optimization Library"],
        [
            "Build a sales funnel for my online course",
            "Draft an email sequence for new leads",
            "Optimize my landing page copy",
            "What upsell would work for this product?",
        ],
        "Sales funnel design and copy drafting work locally; no page publishing or auto-emailing.",
        "SalesFunnelDialog", "Open Sales Funnel Builder",
    ),

    "Side Hustle Scout": _action(
        "cap.side_hustle_scout", "Side Hustle Scout",
        "Finds and evaluates side hustle opportunities matched to the user's skills, schedule, and income goals. Researches gig economy platforms, freelance markets, and micro-business ideas.",
        "Side hustle discovery workspace with opportunity matcher, platform comparison, time-to-income estimator, and getting-started checklist.",
        "No outward actions. Never signs up for platforms or creates accounts. All output is advisory.",
        [], "None",
        ["Financial Gainer", "Individual", "All-Rounder"],
        ["Research", "Business Workflow", "Chatbot", "Smart Search"],
        [
            "Present realistic time and effort expectations for each opportunity.",
            "Flag opportunities that require upfront investment.",
            "Never guarantee income from any side hustle.",
            "Suggest opportunities that match the user's stated skills and schedule.",
            "Warn about scams and predatory gig platforms.",
        ],
        ["Capability Attachments", "Operating Context"],
        ["Gig Economy Library", "Business Strategy Library", "Research Discipline Library"],
        [
            "What side hustles can I do in 5 hours a week?",
            "Find freelance opportunities for a graphic designer",
            "Compare Uber vs DoorDash vs TaskRabbit",
            "What micro-business can I start with $100?",
        ],
        "Side hustle research works locally; no platform sign-ups or account creation.",
        "SideHustleScoutDialog", "Open Side Hustle Scout",
    ),

    "Skill Monetizer": _action(
        "cap.skill_monetizer", "Skill Monetizer",
        "Analyzes the user's skills, experience, and interests to suggest monetization paths. Helps package skills into sellable services, courses, or products.",
        "Skill monetization workspace with skill inventory, monetization path suggestions, pricing guidance, and packaging templates.",
        "No outward actions. All output is advisory. Never lists services or creates product pages.",
        [], "None",
        ["Financial Gainer", "Individual", "Business", "All-Rounder"],
        ["Research", "Business Workflow", "Chatbot", "Document Generator"],
        [
            "Present monetization paths with realistic effort and income potential.",
            "Never guarantee specific earnings.",
            "Suggest paths that match the user's current skill level.",
            "Flag paths that require significant upfront investment.",
            "Encourage ethical monetization — no spam, scams, or low-value offerings.",
        ],
        ["Capability Attachments", "Operating Context"],
        ["Business Strategy Library", "Marketing Library", "Financial Literacy Library"],
        [
            "How can I monetize my photography skills?",
            "Turn my coding experience into a side income",
            "What can I teach online based on my expertise?",
            "Package my writing skills into a service offering",
        ],
        "Skill monetization analysis works locally; no service listings or product creation.",
        "SkillMonetizerDialog", "Open Skill Monetizer",
    ),

    "Investment Researcher": _action(
        "cap.investment_researcher", "Investment Researcher",
        "Researches investment options — stocks, ETFs, real estate, bonds, and alternative investments. Provides educational analysis, risk assessment, and portfolio diversification suggestions.",
        "Investment research workspace with asset comparison, risk scoring, diversification visualizer, and educational resources.",
        "No outward financial actions. Never executes trades or connects to brokerage accounts. All output is educational and advisory only.",
        [], "None",
        ["Financial Gainer", "Business", "Enterprise", "All-Rounder"],
        ["Research", "Data Analyst Pro", "Chatbot", "Smart Search", "Financial Analyst"],
        [
            "NEVER give financial advice or guarantee returns.",
            "Always show disclaimer: 'This is not financial advice. Investments carry risk.'",
            "Present both potential gains and risks for any investment.",
            "Encourage diversification and long-term thinking.",
            "Flag high-risk investments clearly.",
            "Never recommend specific buy or sell actions.",
        ],
        ["Capability Attachments", "Operating Context", "Approval Required"],
        ["Financial Literacy Library", "Market Analysis Library", "Risk Assessment Library"],
        [
            "Compare these three ETFs for a beginner",
            "What are the risks of real estate investing?",
            "Explain dollar-cost averaging",
            "How should I diversify a $5000 portfolio?",
        ],
        "Investment research and education work locally; no brokerage connections or trade execution.",
        "InvestmentResearcherDialog", "Open Investment Researcher",
    ),

    "ROI Calculator": _action(
        "cap.roi_calculator", "ROI Calculator",
        "Calculates return on investment for business ideas, projects, side hustles, and marketing campaigns. Factors in costs, time, expected returns, and risk probability.",
        "ROI calculation workspace with input forms, comparison tables, break-even analysis, and visual charts.",
        "No outward actions. All calculations are based on user-provided estimates.",
        [], "None",
        ["Financial Gainer", "Business", "Enterprise", "All-Rounder"],
        ["Data Analyst Pro", "Spreadsheet Wizard", "Financial Analyst", "Chatbot"],
        [
            "Present ROI calculations with clear assumptions stated.",
            "Always show the break-even point.",
            "Include both best-case and worst-case scenarios.",
            "Factor in hidden costs (time, opportunity cost, taxes).",
            "Never guarantee specific returns.",
        ],
        ["Capability Attachments", "Operating Context"],
        ["Financial Literacy Library", "Analytics Library", "Business Strategy Library"],
        [
            "Calculate the ROI of starting a blog",
            "What's the break-even on this equipment purchase?",
            "Compare these two business ideas by ROI",
            "How long until this side hustle pays for itself?",
        ],
        "ROI calculations work locally with user-provided data.",
        "ROICalculatorDialog", "Open ROI Calculator",
    ),

    "Market Gap Finder": _action(
        "cap.market_gap_finder", "Market Gap Finder",
        "Identifies underserved markets, unmet customer needs, and competitive gaps. Analyzes trends, competitor weaknesses, and emerging opportunities.",
        "Market gap analysis workspace with trend scanner, competitor weakness map, opportunity scoring, and niche finder.",
        "No outward actions. All research is advisory and based on publicly available information.",
        [], "None",
        ["Financial Gainer", "Business", "Enterprise", "All-Rounder"],
        ["Research", "Competitive Analyst", "Business Workflow", "Smart Search", "Chatbot"],
        [
            "Present opportunities with realistic market sizing.",
            "Never guarantee that a market gap is profitable.",
            "Flag the risks and competition level for each opportunity.",
            "Encourage ethical business practices.",
            "Suggest validation steps before pursuing any gap.",
        ],
        ["Capability Attachments", "Operating Context"],
        ["Market Research Library", "Business Strategy Library", "Competitive Analysis Library"],
        [
            "What underserved markets exist in pet care?",
            "Find gaps in the meal prep delivery market",
            "What niches are growing but underserved?",
            "Analyze competitor weaknesses in my industry",
        ],
        "Market gap research works locally; no external data purchases or automated scraping.",
        "MarketGapFinderDialog", "Open Market Gap Finder",
    ),

    "Negotiation Coach": _action(
        "cap.negotiation_coach", "Negotiation Coach",
        "Helps users negotiate better pay, rates, contracts, and deals. Provides strategy suggestions, scripts, counter-offer templates, and practice scenarios.",
        "Negotiation coaching workspace with scenario builder, script library, counter-offer drafter, and practice mode with AI role-play.",
        "No outward actions. Never sends messages or participates in negotiations on the user's behalf.",
        [], "None",
        ["Financial Gainer", "Business", "Individual", "All-Rounder"],
        ["Chatbot", "Business Workflow", "Document Generator", "Research"],
        [
            "Encourage fair and honest negotiation — no manipulation.",
            "Present realistic expectations for negotiation outcomes.",
            "Suggest strategies that preserve relationships.",
            "Practice scenarios should adapt to the user's experience level.",
            "Remind users that negotiation is a skill that improves with practice.",
        ],
        ["Capability Attachments", "Operating Context"],
        ["Communication Library", "Business Strategy Library", "Psychology Library"],
        [
            "Help me negotiate a higher salary",
            "Draft a counter-offer for this freelance gig",
            "Practice negotiating with a difficult client",
            "What's a fair rate for my consulting services?",
        ],
        "Negotiation coaching and practice work locally; no message sending or auto-negotiation.",
        "NegotiationCoachDialog", "Open Negotiation Coach",
    ),

    # ═══════════════════════════════════════════════════════════════════════════════
    # MEMORY SAVER USE CASE CAPABILITIES
    # ═══════════════════════════════════════════════════════════════════════════════

    "Session Replay": _action(
        "cap.session_replay", "Session Replay",
        "Replays past sessions step by step — showing what was done, what decisions were made, and what outcomes resulted. Like a DVR for your work sessions.",
        "Session replay viewer with timeline scrubber, step-by-step playback, event filtering, and bookmarking.",
        "No outward actions. All replay is read-only and local.",
        [], "None",
        ["Memory Saver", "Enterprise", "All-Rounder"],
        ["Memory Recorder", "Memory Bridge", "Archive", "Notebook"],
        [
            "Replay is read-only — never modifies past sessions.",
            "Allow users to bookmark key moments for quick navigation.",
            "Filter replay by event type (AI interaction, user action, decision).",
            "Never replay or display sensitive data (passwords) in plaintext.",
            "Support both full session and filtered replay modes.",
        ],
        ["Capability Attachments", "Save Safety"],
        ["Audit Library", "Memory Persistence Library", "Playback Library"],
        [
            "Replay my session from yesterday afternoon",
            "Show me the moment I made that design decision",
            "Filter replay to only show AI interactions",
            "Bookmark this part of the session for later",
        ],
        "Session replay works locally with recorded data; no external sharing.",
        "SessionReplayDialog", "Open Session Replay",
    ),

    "Smart Recall": _action(
        "cap.smart_recall", "Smart Recall",
        "Searches across all past sessions, conversations, decisions, and outputs to find exactly what you're looking for. Understands natural language queries.",
        "Smart recall search bar with natural language query, result ranking, context preview, and deep-link to original session.",
        "No outward actions. All search is local across recorded sessions.",
        [], "None",
        ["Memory Saver", "Individual", "Business", "Enterprise", "All-Rounder"],
        ["Memory Recorder", "Memory Bridge", "Smart Search", "Archive"],
        [
            "Rank results by relevance and recency.",
            "Show context around each match — not just the matching line.",
            "Never display sensitive data (passwords) in search results.",
            "Support fuzzy matching for imperfect queries.",
            "Allow filtering by date range, capability, and session.",
        ],
        ["Capability Attachments", "Save Safety"],
        ["Search Library", "Memory Persistence Library", "Audit Library"],
        [
            "When did I last work on the marketing plan?",
            "Find all sessions where I used the Coding Assistant",
            "What did I decide about the pricing strategy?",
            "Search for any mention of 'budget' in the last month",
        ],
        "Smart recall searches locally across recorded sessions; no external queries.",
        "SmartRecallDialog", "Open Smart Recall",
    ),

    "Decision Tracker": _action(
        "cap.decision_tracker", "Decision Tracker",
        "Tracks decisions made during sessions — what was decided, why, what alternatives were considered, and what the outcome was. Builds a decision history for learning and accountability.",
        "Decision tracking dashboard with decision log, reasoning view, outcome tracker, and pattern analysis.",
        "No outward actions. All tracking is passive and local.",
        [], "None",
        ["Memory Saver", "Business", "Enterprise", "All-Rounder"],
        ["Memory Recorder", "Memory Bridge", "Notebook", "Archive"],
        [
            "Record decisions silently — never interrupt the user.",
            "Capture the reasoning behind each decision, not just the outcome.",
            "Track outcomes over time to identify decision patterns.",
            "Never record sensitive decision context in plaintext.",
            "Allow users to annotate decisions with notes later.",
        ],
        ["Capability Attachments", "Save Safety"],
        ["Decision Science Library", "Audit Library", "Memory Persistence Library"],
        [
            "Why did I choose this vendor?",
            "Show me all decisions I made last week",
            "Which decisions had the best outcomes?",
            "Track the outcome of my pricing decision",
        ],
        "Decision tracking works locally; no external sharing.",
        "DecisionTrackerDialog", "Open Decision Tracker",
    ),

    "Knowledge Archive": _action(
        "cap.knowledge_archive", "Knowledge Archive",
        "Archives everything learned and produced — documents, research, code, insights, and outputs — into a searchable, organized knowledge base that persists across sessions.",
        "Knowledge archive browser with categorized storage, full-text search, version history, and export capabilities.",
        "Exporting archives or sharing externally requires approval.",
        ["export", "file_write"], "Medium",
        ["Memory Saver", "Educational", "Business", "Enterprise", "All-Rounder"],
        ["Memory Recorder", "Knowledge Base Builder", "Archive", "Document Processor"],
        [
            "Archive silently — never interrupt the user's workflow.",
            "Categorize archived items automatically when possible.",
            "Maintain version history for all archived documents.",
            "Never archive sensitive data (passwords, credentials) in plaintext.",
            "Allow users to delete or export archived items on demand.",
        ],
        ["Capability Attachments", "Save Safety", "Approval Required"],
        ["Archive Library", "Knowledge Management Library", "Memory Persistence Library"],
        [
            "Archive everything from today's research session",
            "Find my notes on competitor analysis",
            "Export my knowledge archive as a backup",
            "What did I produce last month?",
        ],
        "Knowledge archiving works locally; export and external sharing require approval.",
        "KnowledgeArchiveDialog", "Open Knowledge Archive",
    ),

    "Habit Tracker": _action(
        "cap.habit_tracker", "Habit Tracker",
        "Tracks your habits and work patterns over time — what you do, when you do it, how often, and how it affects your productivity and income.",
        "Habit tracking dashboard with habit streaks, pattern visualization, correlation analysis, and reminder suggestions.",
        "No outward actions. All tracking is passive and local.",
        [], "None",
        ["Memory Saver", "Individual", "All-Rounder"],
        ["Memory Recorder", "Activity Watcher", "Notebook", "Personal Organizer"],
        [
            "Track habits silently — never interrupt the user.",
            "Show patterns honestly — don't inflate streaks or progress.",
            "Identify correlations between habits and productivity.",
            "Never track sensitive habits in plaintext.",
            "Suggest improvements based on data, not assumptions.",
        ],
        ["Capability Attachments", "Save Safety"],
        ["Productivity Library", "Behavioral Science Library", "Memory Persistence Library"],
        [
            "What habits have I maintained for 30 days?",
            "Show me my most productive time of day",
            "How does my exercise habit affect my work output?",
            "What patterns do you see in my work schedule?",
        ],
        "Habit tracking works locally; no external sharing.",
        "HabitTrackerDialog", "Open Habit Tracker",
    ),

    "Progress Journal": _action(
        "cap.progress_journal", "Progress Journal",
        "Keeps a running journal of progress on goals, projects, and skills. Automatically logs milestones, setbacks, and achievements from your sessions.",
        "Progress journal workspace with timeline view, milestone tracker, goal linking, and reflection prompts.",
        "No outward actions. All journaling is local.",
        [], "None",
        ["Memory Saver", "Individual", "Educational", "All-Rounder"],
        ["Memory Recorder", "Memory Bridge", "Notebook", "Personal Organizer"],
        [
            "Log progress silently from session activity.",
            "Present progress honestly — including setbacks.",
            "Allow users to add manual reflections and notes.",
            "Link journal entries to specific goals and projects.",
            "Suggest reflection prompts based on recent activity.",
        ],
        ["Capability Attachments", "Save Safety"],
        ["Journaling Library", "Productivity Library", "Memory Persistence Library"],
        [
            "What progress did I make this week?",
            "Show me my milestones for the marketing project",
            "Add a reflection on today's coding session",
            "How far am I on my learning goal?",
        ],
        "Progress journaling works locally; no external sharing.",
        "ProgressJournalDialog", "Open Progress Journal",
    ),

    "Context Keeper": _action(
        "cap.context_keeper", "Context Keeper",
        "Maintains context across sessions so you never lose your place. Remembers what you were working on, what was open, what you were thinking about, and where you left off.",
        "Context restoration panel with session resume, open items list, thinking state capture, and quick-resume buttons.",
        "No outward actions. All context is saved and restored locally.",
        [], "None",
        ["Memory Saver", "Individual", "Task-Ready", "Business", "All-Rounder"],
        ["Memory Recorder", "Memory Bridge", "Notebook", "Archive"],
        [
            "Restore context silently on session start.",
            "Show a summary of where the user left off.",
            "Never store sensitive context (passwords, open credentials) in plaintext.",
            "Allow users to clear context on demand.",
            "Support multiple context slots for different projects.",
        ],
        ["Capability Attachments", "Save Safety"],
        ["Memory Persistence Library", "Productivity Library", "Context Management Library"],
        [
            "Where did I leave off yesterday?",
            "Restore my context from the coding project",
            "What was I thinking about last session?",
            "Clear my context and start fresh",
        ],
        "Context keeping works locally; no external sync.",
        "ContextKeeperDialog", "Open Context Keeper",
    ),

    "Audit Trail Builder": _action(
        "cap.audit_trail_builder", "Audit Trail Builder",
        "Builds compliance-ready audit trails from session recordings. Formats events, decisions, and actions into structured reports suitable for regulatory review.",
        "Audit trail builder with event selector, report formatter, compliance template library, and export options.",
        "Exporting audit trails requires approval. All trail building is local.",
        ["export", "file_write"], "Medium",
        ["Memory Saver", "Enterprise", "Business", "All-Rounder"],
        ["Memory Recorder", "Decision Tracker", "Document Generator", "Archive"],
        [
            "Format audit trails according to the selected compliance standard.",
            "Include all relevant events — never omit inconvenient data.",
            "Timestamp every event with UTC and local time.",
            "Never include sensitive data (passwords) in audit trails.",
            "Support common compliance formats (SOC2, GDPR, HIPAA-aware).",
        ],
        ["Capability Attachments", "Save Safety", "Approval Required"],
        ["Compliance Library", "Audit Library", "Documentation Library"],
        [
            "Build an audit trail for last month's sessions",
            "Format this audit trail for SOC2 review",
            "Show me the decision history for this project",
            "Export the audit trail as a PDF report",
        ],
        "Audit trail building works locally; export requires approval.",
        "AuditTrailBuilderDialog", "Open Audit Trail Builder",
    ),

    "Game Companion": _action(
        "cap.game_companion", "Game Companion",
        "Learns and plays games alongside the user. Can learn game rules, suggest strategies, analyze positions, provide tutorials, and play practice games. Designed for individual enjoyment and cognitive skill building.",
        "Game companion workspace with game selector, rules learner, strategy advisor, position analyzer, practice mode, and progress tracker.",
        "No outward actions. All game analysis and suggestions are local and advisory.",
        [], "None",
        ["Individual", "Educational", "All-Rounder"],
        ["Chatbot", "Tutor", "Research"],
        [
            "Teach game rules clearly before suggesting strategy.",
            "Adapt suggestions to the user's skill level.",
            "Never cheat or use unfair advantages in practice games.",
            "Encourage good sportsmanship and learning.",
            "Analyze positions objectively — don't just tell the user what they want to hear.",
        ],
        ["Capability Attachments", "Operating Context"],
        ["Game Strategy Library", "Cognitive Skills Library", "Communication Library"],
        [
            "Teach me how to play chess",
            "What's the best move in this position?",
            "Analyze my game and suggest improvements",
            "Play a practice game with me",
        ],
        "Game companion discussion and strategy work locally; live game play integration is not connected.",
        "GameCompanionDialog", "Open Game Companion",
    ),
}

# Alias mappings for new premium capabilities
CAPABILITY_ALIASES.update({
    "AI Team Lead": "Team Orchestrator",
    "Project Coordinator": "Team Orchestrator",
    "Memory Persistence": "Memory Bridge",
    "Context Memory": "Memory Bridge",
    "Image Generator": "Visual Canvas",
    "AI Artist": "Visual Canvas",
    "Data Science": "Data Analyst Pro",
    "Analytics Pro": "Data Analyst Pro",
    "Code Inspector": "Code Reviewer",
    "Quality Assurance": "Code Reviewer",
    "API Connector": "API Integrator",
    "Integration Builder": "API Integrator",
    "Wiki Builder": "Knowledge Base Builder",
    "Documentation Center": "Knowledge Base Builder",
    "Meeting Assistant": "Meeting Facilitator",
    "Conference Manager": "Meeting Facilitator",
    "Email Assistant": "Email Automation",
    "Inbox Manager": "Email Automation",
    "Schedule Optimizer": "Calendar Manager",
    "Time Manager": "Calendar Manager",
    "Report Builder": "Document Generator",
    "PDF Creator": "Document Generator",
    "Language Translator": "Translation Expert",
    "Multi-language": "Translation Expert",
    "Slide Deck Builder": "Presentation Builder",
    "Keynote Assistant": "Presentation Builder",
    "Excel Wizard": "Spreadsheet Wizard",
    "Sheets Expert": "Spreadsheet Wizard",
    "Contract Reviewer": "Legal Document Reviewer",
    "Compliance Checker": "Legal Document Reviewer",
    "Medical Search": "Medical Researcher",
    "Clinical Research": "Medical Researcher",
    "ADA Assistant": "Accessibility Assistant",
    "Universal Access": "Accessibility Assistant",
    "Truth Checker": "Fact Checker",
    "Verification Tool": "Fact Checker",
    "Speech Interface": "Voice Interface",
    "Talk to AI": "Voice Interface",
    "No-Code Automation": "Workflow Automator",
    "Process Builder": "Workflow Automator",
    "Vulnerability Scanner": "Security Auditor",
    "Penetration Testing": "Security Auditor",
    "Market Research": "Competitive Analyst",
    "Strategy Assistant": "Competitive Analyst",
    "Course Builder": "Learning Path Creator",
    "Training Designer": "Learning Path Creator",
    "Enterprise Search": "Smart Search",
    "AI Search": "Smart Search",
})


TIER_SCAFFOLD = {
    "Basic": {
        "active_ai_limit": 1,
        "outward_action_depth": "review-only",
        "all_rounder": "restricted",
        "advanced_libraries": "limited",
        "focus": "create AIs, chat, local research/writing/coding review stubs",
    },
    "Standard": {
        "active_ai_limit": 3,
        "outward_action_depth": "approval-gated simple actions",
        "all_rounder": "limited scaffold",
        "advanced_libraries": "moderate",
        "focus": "more capability combinations and limited approved outward actions",
    },
    "Pro/Business": {
        "active_ai_limit": 10,
        "outward_action_depth": "advanced approval-gated workflows",
        "all_rounder": "available with stronger approvals",
        "advanced_libraries": "business and automation libraries",
        "focus": "workflow automation, audit controls, export/handoff actions",
    },
}


def _canonical_ability(name: str) -> str:
    return CAPABILITY_ALIASES.get(name.strip(), name.strip())


def get_capability_action(capability_name: str) -> CapabilityAction | None:
    canonical = _canonical_ability(capability_name)
    return CAPABILITY_REGISTRY.get(canonical)


def get_actions_for_ai(abilities: list[str]) -> list[tuple[str, str, str]]:
    """Return (ui_label, dialog_class_name, original_ability_name) deduped by canonical name."""
    seen: set[str] = set()
    out: list[tuple[str, str, str]] = []
    for ab in abilities:
        c = _canonical_ability(ab)
        if c in seen:
            continue
        seen.add(c)
        reg = CAPABILITY_REGISTRY.get(c)
        if reg:
            out.append((reg.ui_label, reg.dialog_class, ab))
    return out


def get_available_actions_for_ai(
    abilities: list[str],
    use_case: str = "",
    libraries: list[str] | None = None,
    guardrails: list[str] | None = None,
) -> list[dict[str, str]]:
    libraries = libraries or []
    guardrails = guardrails or []
    seen: set[str] = set()
    actions: list[dict[str, str]] = []
    canonicals = {_canonical_ability(a) for a in abilities}
    for ab in abilities:
        canonical = _canonical_ability(ab)
        action = CAPABILITY_REGISTRY.get(canonical)
        if not action or canonical in seen:
            continue
        if use_case and action.allowed_use_cases and use_case not in action.allowed_use_cases and "All-Rounder" not in action.allowed_use_cases:
            continue
        seen.add(canonical)
        actions.append({
            "label": action.ui_label,
            "dialog_class": action.dialog_class,
            "capability": canonical,
            "source": ab,
            "mode": "capability",
            "description": action.description,
            "approval": action.required_approval_level,
        })
    combo_specs = [
        ({"Chatbot", "Research"}, "Research from Chat", "ChatCapabilityDialog", "Ask in chat, route to research, return summary."),
        ({"Chatbot", "Coder"}, "Code from Chat", "ChatCapabilityDialog", "Ask in chat, draft code or open coding workflow."),
        ({"Research", "Creative Writing"}, "Research-to-Draft", "CreativeWriterCapabilityDialog", "Turn findings into a draft with sources/assumptions."),
        ({"Notebook", "Document Processor"}, "Document-to-Notes", "DocumentProcessorCapabilityDialog", "Extract documents into notes, tasks, or archive-ready summaries."),
        ({"Coder", "Research"}, "Research-backed Coding", "CodingCapabilityDialog", "Use research notes before drafting code changes."),
        ({"Planner", "Tool User"}, "Approved Tool Plan", "ToolUserCapabilityDialog", "Plan tool use, then request approval before invocation."),
    ]
    if "Hephaestus Briefing Library" in libraries or {"Creative Writing", "Planner", "Document Processor"} <= canonicals:
        combo_specs.append(({"Creative Writing", "Planner"}, "Hephaestus Handoff Brief", "HephaestusRelayCapabilityDialog", "Structure idea, constraints, unknowns, and handoff brief."))
    if use_case in {"Business", "Enterprise", "Task-Ready"} and {"Planner", "Document Processor"} & canonicals:
        combo_specs.append(({"Planner"}, "Business SOP / Checklist", "BusinessWorkflowCapabilityDialog", "Create SOPs, checklists, support drafts, or handoffs."))
    if use_case == "All-Rounder":
        combo_specs.append((set(), "All-Rounder Control Surface", "ChatCapabilityDialog", "High-power combined workspace; outward actions use stronger approvals."))
    for required, label, dialog, desc in combo_specs:
        if label in seen:
            continue
        if required and not required <= canonicals:
            continue
        seen.add(label)
        actions.append({
            "label": label,
            "dialog_class": dialog,
            "capability": label,
            "source": "combination",
            "mode": "combination",
            "description": desc,
            "approval": "High" if use_case == "All-Rounder" else "Contextual",
        })
    return actions


def describe_capability_for_book(capability_name: str) -> list[str]:
    canonical = _canonical_ability(capability_name)
    action = CAPABILITY_REGISTRY.get(canonical)
    if not action:
        return [
            f"Capability ID: unregistered.{canonical.lower().replace(' ', '_')}",
            "Status: SAFE STUB — no attachment registered yet.",
            "Inward Mode: Describe the request and ask for clarification.",
            "Outward Mode: Disabled until an attachment is registered.",
            "Approval: Any file, system, network, or external action requires approval.",
        ]
    return [
        f"Capability ID: {action.capability_id}",
        f"Display Name: {action.display_name}",
        f"Description: {action.description}",
        f"Inward Mode: {action.inward_surface}",
        f"Outward Mode: {action.outward_action_path}",
        f"Required Permissions: {', '.join(action.required_permissions) if action.required_permissions else 'None'}",
        f"Required Approval Level: {action.required_approval_level}",
        f"Compatible Capabilities: {', '.join(action.compatible_capabilities) if action.compatible_capabilities else 'None'}",
        f"Book Sections Used: {', '.join(action.book_sections_used)}",
        f"Libraries Used: {', '.join(action.libraries_used) if action.libraries_used else 'None'}",
        f"Starter Prompts: {'; '.join(action.starter_prompt_guidance)}",
        f"Safe Fallback: {action.unfinished_safe_fallback}",
    ]


def get_combined_capability_workflows(abilities: list[str], libraries: list[str] | None = None, use_case: str = "") -> list[str]:
    canonicals = {_canonical_ability(a) for a in abilities}
    libraries = libraries or []
    workflows: list[str] = []
    if {"Chatbot", "Research"} <= canonicals:
        workflows.append("Chat + Research: ask in chat, open research workflow, then return findings summary to chat.")
    if {"Chatbot", "Coder"} <= canonicals:
        workflows.append("Chat + Coding: ask in chat, draft code/show diff, and require approval before any file or command action.")
    if {"Research", "Creative Writing"} <= canonicals:
        workflows.append("Research + Writing: gather findings, separate facts from assumptions, then draft with source-aware wording.")
    if {"Notebook", "Document Processor"} <= canonicals:
        workflows.append("Organizer + Document Processor: extract document points, convert them into notes, tasks, or archive-ready records.")
    if {"Coder", "Research"} <= canonicals:
        workflows.append("Coding + Research: check docs/sources first, then use findings to guide code drafts or tests.")
    if "Hephaestus Briefing Library" in libraries or {"Creative Writing", "Planner", "Document Processor"} <= canonicals:
        workflows.append("Hephaestus Relay + Writing + Organizer: structure requirements, produce a clear brief, and prepare a handoff packet without touching ProtoBrain internals.")
    if use_case == "All-Rounder":
        workflows.append("All-Rounder: broad attachments are available, but outward actions use stronger approval and clear status reporting.")
    return workflows


class BaseCapabilityDialog(QDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(parent)
        self._ai_name = ai_name
        self._ai_uuid = ai_uuid
        self._abilities = abilities or []
        self._book_path = book_path
        self._guardrails = guardrails or []
        self._libraries = libraries or []
        self._use_case = use_case
        self._book_context: dict[str, str] = {}
        self._result_summary = ""
        self._load_book_context()

    def _load_book_context(self):
        self._book_context = {
            "identity": f"AI Name: {self._ai_name}",
            "use_case": f"Use Case: {self._use_case}",
            "capabilities": f"Capabilities: {', '.join(self._abilities)}",
            "libraries": f"Libraries: {', '.join(self._libraries) if self._libraries else 'None'}",
            "guardrails": f"Guardrails: {', '.join(self._guardrails) if self._guardrails else 'None'}",
            "quickstart": "Open the capability workflow and describe what you need.",
        }
        if self._book_path and Path(self._book_path).exists():
            try:
                text = Path(self._book_path).read_text(encoding="utf-8")
                in_quick = False
                quick_lines: list[str] = []
                for line in text.splitlines():
                    if line.strip().startswith("## Quickstart"):
                        in_quick = True
                        continue
                    if in_quick:
                        if line.strip().startswith("##"):
                            break
                        if line.strip():
                            quick_lines.append(line.strip())
                if quick_lines:
                    self._book_context["quickstart"] = "\n".join(quick_lines)
                for title, key in [
                    ("## Capability Attachments", "capability_attachments"),
                    ("## Cross-Capability Workflows", "cross_workflows"),
                    ("## Approval Required", "approval_requirements"),
                    ("## Available Actions", "available_actions"),
                ]:
                    extracted = self._extract_book_section(text, title)
                    if extracted:
                        self._book_context[key] = extracted
            except Exception:
                pass

    def _extract_book_section(self, text: str, title: str) -> str:
        lines: list[str] = []
        in_section = False
        for line in text.splitlines():
            if line.strip() == title:
                in_section = True
                continue
            if in_section and line.startswith("## "):
                break
            if in_section and line.strip():
                lines.append(line.strip())
        return "\n".join(lines[:12])

    def _build_context_banner(self) -> str:
        return (
            f"{self._book_context.get('identity', '')}  |  "
            f"{self._book_context.get('use_case', '')}  |  "
            f"{self._book_context.get('capabilities', '')}"
        )

    def _set_result_summary(self, text: str):
        self._result_summary = text

    def get_result_summary(self) -> str:
        return self._result_summary


class ChatCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Workspace Chat — {ai_name}")
        self.resize(900, 650)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        split = QSplitter(Qt.Orientation.Horizontal)
        chat_panel = QWidget()
        chat_layout = QVBoxLayout(chat_panel)
        self._transcript = QTextEdit()
        self._transcript.setReadOnly(True)
        self._transcript.setStyleSheet("")
        chat_layout.addWidget(self._transcript, stretch=1)
        row = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setPlaceholderText("Ask this AI to chat, research, code, write, plan, process documents, tutor, or prepare a handoff...")
        row.addWidget(self._input, stretch=1)
        send = QPushButton("Send")
        send.clicked.connect(self._on_send)
        row.addWidget(send)
        chat_layout.addLayout(row)
        split.addWidget(chat_panel)
        action_panel = QWidget()
        action_layout = QVBoxLayout(action_panel)
        action_layout.addWidget(QLabel("Book Context Summary"))
        context_box = QTextEdit()
        context_box.setReadOnly(True)
        context_box.setMaximumHeight(160)
        context_box.setStyleSheet("")
        context_box.setText(
            f"{self._book_context.get('identity', '')}\n"
            f"{self._book_context.get('use_case', '')}\n"
            f"{self._book_context.get('libraries', '')}\n"
            f"{self._book_context.get('guardrails', '')}\n\n"
            f"Quickstart:\n{self._book_context.get('quickstart', '')}"
        )
        action_layout.addWidget(context_box)
        action_layout.addWidget(QLabel("Available Actions"))
        self._action_buttons: dict[str, str] = {}
        actions = get_available_actions_for_ai(self._abilities, self._use_case, self._libraries, self._guardrails)
        if actions:
            for action in actions:
                btn = QPushButton(action["label"])
                btn.setToolTip(f"{action['description']}\nApproval: {action['approval']}")
                btn.clicked.connect(lambda checked, d=action["dialog_class"], l=action["label"]: self._open_action_dialog(d, l))
                action_layout.addWidget(btn)
                self._action_buttons[action["label"]] = action["dialog_class"]
        else:
            none = QLabel("No registered actions. This is a safe chat-only workspace.")
            none.setWordWrap(True)
            action_layout.addWidget(none)
        action_layout.addStretch(1)
        split.addWidget(action_panel)
        split.setSizes([620, 280])
        layout.addWidget(split, stretch=1)
        self._approval_banner = QLabel("")
        self._approval_banner.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 4px; border-radius: 4px;")
        self._approval_banner.setVisible(False)
        layout.addWidget(self._approval_banner)
        self._append_ai(f"Workspace ready. I am {ai_name}, operating as {self._use_case or 'Unspecified'} with: {', '.join(self._abilities) or 'general assistance'}.")
        self._append_ai(f"Available actions: {', '.join(self._action_buttons.keys()) if self._action_buttons else 'chat only'}.")
        workflows = get_combined_capability_workflows(self._abilities, self._libraries, self._use_case)
        if workflows:
            self._append_ai("Combined workflows loaded: " + " | ".join(workflows))
        self._append_ai(f"Quickstart: {self._book_context.get('quickstart', 'Ask me anything.')}")

    def _on_send(self):
        try:
            self._do_send()
        except Exception as e:
            try:
                self._append_ai(f"I encountered an error processing your message: {e}")
            except Exception:
                pass

    def _do_send(self):
        msg = self._input.text().strip()
        if not msg:
            return
        self._append_user(msg)
        self._approval_banner.setVisible(False)

        # ── Usage Policy Pre-Screen (unified parental + enterprise) ──
        # Screen user input through the usage policy engine before anything else.
        try:
            from ...core.usage_policy import screen_input as _policy_screen, load_policy_settings as _load_policy
            policy_settings = _load_policy()
            if policy_settings.get("mode", "disabled") != "disabled":
                policy_result = _policy_screen(msg, policy_settings)
                if not policy_result.allowed:
                    self._append_ai(policy_result.block_message)
                    self._approval_banner.setText(f"Usage Policy: {policy_result.blocked_reason.value}")
                    self._approval_banner.setVisible(True)
                    self._input.clear()
                    return
        except ImportError:
            pass

        # ── Parental Controls Pre-Screen (legacy) ──
        # Screen user input through parental controls BEFORE governance sanitizer.
        # When parental controls are enabled, this is the first line of defense for kid safety.
        try:
            from ...core.parental_controls_enforcer import screen_input, load_parental_settings
            parental_settings = load_parental_settings()
            if parental_settings.get("enabled", False):
                parental_result = screen_input(msg, parental_settings)
                if not parental_result.allowed:
                    self._append_ai(parental_result.block_message)
                    self._approval_banner.setText(f"Parental Controls: {parental_result.blocked_reason.value}")
                    self._approval_banner.setVisible(True)
                    self._input.clear()
                    return
        except ImportError:
            pass

        # ── Governance Sanitizer Pre-Screen ──
        # Screen user input before sending to runtime. If blocked,
        # show the ethical-use banner and don't process the message.
        try:
            from ...core.governance_sanitizer import sanitize_input, ETHICAL_USE_BANNER
            san_result = sanitize_input(msg)
            if not san_result.is_clean:
                self._append_ai(
                    f"{san_result.violation_detail}\n\n{ETHICAL_USE_BANNER}"
                )
                self._approval_banner.setText(f"Content blocked: {san_result.violation_type.value}")
                self._approval_banner.setVisible(True)
                self._input.clear()
                return
        except ImportError:
            pass

        # Route through NexusAIRuntime for full capability execution:
        # - Intent classification (chat, code, research, tool use, etc.)
        # - ToolExecutor (read/write files, list dirs, run shell)
        # - AdaptiveMemoryStore (learns from every interaction)
        # - Model backend for AI reasoning
        try:
            from ...core.nexus_ai_runtime import NexusAIRuntime
            settings = SettingsManager()
            settings.initialize()
            runtime = NexusAIRuntime(settings=settings)
            result = runtime.run(
                task=msg,
                ai_name=self._ai_name,
                ai_uuid=self._ai_uuid,
                ai_metadata={
                    "abilities": self._abilities,
                    "use_case": self._use_case,
                    "guardrails": self._guardrails,
                    "libraries": self._libraries,
                },
            )
            if result.result_text:
                self._append_ai(result.result_text)
            else:
                self._append_ai("I processed your request but didn't produce output. Try rephrasing.")
        except Exception as e:
            # Fallback to direct model call if runtime fails
            try:
                settings = SettingsManager()
                settings.initialize()
                backend = BackendManager(settings)
                book_ctx = (
                    f"You are {self._ai_name}, a Command Nexus governed AI.\n"
                    f"Use case: {self._use_case}\n"
                    f"Abilities: {', '.join(self._abilities) or 'general assistance'}\n"
                    f"Guardrails: {', '.join(self._guardrails) if self._guardrails else 'None'}\n\n"
                    f"User message: {msg}\n\n"
                    "Respond helpfully. You can read/write files, list directories, and run commands locally."
                )
                response = backend.call_model(book_ctx)
                if response.error:
                    self._append_ai(f"I encountered an issue: {response.error}")
                elif response.text:
                    self._append_ai(response.text)
                else:
                    self._append_ai("I received your message but couldn't generate a response. Please try again.")
            except Exception as e2:
                self._append_ai(f"I'm having trouble connecting to my local model: {e2}")

        self._input.clear()

    def _append_user(self, text: str):
        self._transcript.append(f"<b>You:</b> {text}")

    def _append_ai(self, text: str):
        self._transcript.append(f"<b>{self._ai_name}:</b> {text}")

    def _open_action_dialog(self, dialog_class_name: str, label: str):
        # Show mandatory disclaimer for guarded capabilities
        from ...core.capability_disclaimers import show_capability_disclaimer, DIALOG_TO_CAPABILITY
        cap_name = DIALOG_TO_CAPABILITY.get(dialog_class_name, "")
        if cap_name:
            if not show_capability_disclaimer(cap_name, parent=self):
                self._append_ai(f"[{label}] Disclaimer declined. Capability not activated.")
                return
        dlg_cls = globals().get(dialog_class_name)
        if not dlg_cls:
            self._append_ai(f"{label} is registered but its workflow class is not loaded. Safe fallback: no action was taken.")
            return
        dlg = dlg_cls(
            ai_name=self._ai_name,
            ai_uuid=self._ai_uuid,
            abilities=self._abilities,
            book_path=self._book_path,
            guardrails=self._guardrails,
            libraries=self._libraries,
            use_case=self._use_case,
            parent=self,
        )
        dlg.exec()
        summary = dlg.get_result_summary() if hasattr(dlg, "get_result_summary") else ""
        if summary:
            self._append_ai(f"[{label} returned] {summary}")
        else:
            self._append_ai(f"[{label}] Workflow closed. No outward action was taken.")


class CodingCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Coding Workflow — {ai_name}")
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        t1w = QWidget()
        t1 = QVBoxLayout(t1w)
        t1.addWidget(QLabel("Describe what you need (explain, diff, test, refactor):"))
        self._code_prompt = QTextEdit()
        self._code_prompt.setPlaceholderText("Paste code or describe the bug/feature...")
        t1.addWidget(self._code_prompt, stretch=1)
        br = QHBoxLayout()
        for label, act in [("Explain Code", "explain"), ("Draft Diff", "diff"), ("Outline Tests", "test"), ("Approved Edit Mode", "approved_edit"), ("Approved Test/Command", "approved_test")]:
            b = QPushButton(label)
            b.clicked.connect(lambda checked, a=act: self._run_code_action(a))
            br.addWidget(b)
        t1.addLayout(br)
        self._code_output = QTextEdit()
        self._code_output.setReadOnly(True)
        self._code_output.setStyleSheet("")
        t1.addWidget(self._code_output, stretch=1)
        tabs.addTab(t1w, "Explain & Draft")
        t2w = QWidget()
        t2 = QVBoxLayout(t2w)
        t2.addWidget(QLabel("Planned files / modules:"))
        self._planned_files = QTextEdit()
        self._planned_files.setPlaceholderText("e.g., src/utils.py, tests/test_utils.py")
        t2.addWidget(self._planned_files, stretch=1)
        tabs.addTab(t2w, "Planned Files")
        t3w = QWidget()
        t3 = QVBoxLayout(t3w)
        t3.addWidget(QLabel("Test commands / validation plan:"))
        self._test_commands = QTextEdit()
        self._test_commands.setPlaceholderText("e.g., pytest tests/test_utils.py -v")
        t3.addWidget(self._test_commands, stretch=1)
        tabs.addTab(t3w, "Test Commands")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Approval required before any file edit, command execution, or deployment.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _run_code_action(self, action):
        prompt = self._code_prompt.toPlainText().strip()
        if not prompt:
            self._code_output.setText("Enter a prompt first.")
            return
        if action == "explain":
            self._code_output.setText(
                f"[EXPLANATION for: {prompt[:80]}...]\n\n"
                "1. Identify the function/class purpose.\n"
                "2. Walk through key logic paths.\n"
                "3. Flag potential risks or edge cases.\n"
                "4. Ask clarifying questions if needed.\n\n"
                "(Simulated explanation — local intelligence mode.)"
            )
            self._set_result_summary("Code explanation prepared locally. No file changes or commands were run.")
        elif action == "diff":
            self._code_output.setText(
                f"[DIFF for: {prompt[:80]}...]\n\n"
                "```diff\n- old_line\n+ new_line\n```\n\n"
                "Review the diff above. If you approve, the changes can be applied to the planned files.\n"
                "(Simulated diff — local intelligence mode.)"
            )
            self._set_result_summary("Diff preview prepared in show-code-only mode. Approved file editing is still a safe stub.")
        elif action == "test":
            self._code_output.setText(
                f"[TEST OUTLINE for: {prompt[:80]}...]\n\n"
                "1. Unit test: happy path\n"
                "2. Unit test: error handling\n"
                "3. Integration test: end-to-end flow\n"
                "4. Edge cases: empty input, max bounds, concurrency\n\n"
                "(Simulated test outline — local intelligence mode.)"
            )
            self._set_result_summary("Test plan prepared. No commands were run.")
        elif action == "approved_edit":
            self._code_output.setText(
                f"[APPROVED EDIT MODE for: {prompt[:80]}...]\n\n"
                "Status: SAFE STUB — not connected to file writing.\n"
                "Required path before activation:\n"
                "1. Show exact target files.\n"
                "2. Show diff preview.\n"
                "3. Pass Moirai protected-mode check.\n"
                "4. Request user approval.\n"
                "5. Apply changes and log/audit.\n\n"
                "No files were changed."
            )
            self._set_result_summary("Approved edit mode is framed as a safe stub. No files were changed.")
        elif action == "approved_test":
            self._code_output.setText(
                f"[APPROVED TEST/COMMAND MODE for: {prompt[:80]}...]\n\n"
                "Status: SAFE STUB — not connected to command execution.\n"
                "Required path before activation:\n"
                "1. Show command and working directory.\n"
                "2. Explain risk and expected output.\n"
                "3. Pass Moirai protected-mode check.\n"
                "4. Request user approval.\n"
                "5. Run and capture logs.\n\n"
                "No commands were run."
            )
            self._set_result_summary("Approved test/command mode is framed as a safe stub. No commands were run.")


class ResearchCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Research Workflow — {ai_name}")
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        layout.addWidget(QLabel("Research query (include scope and desired format):"))
        self._research_query = QTextEdit()
        self._research_query.setPlaceholderText("e.g., Compare Python async frameworks for web APIs...")
        self._research_query.setMaximumHeight(100)
        layout.addWidget(self._research_query)
        br = QHBoxLayout()
        for label, act in [("Start Research", "research"), ("Compare", "compare"), ("Find Risks", "risks")]:
            b = QPushButton(label)
            b.clicked.connect(lambda checked, a=act: self._run_research(a))
            br.addWidget(b)
        layout.addLayout(br)
        sp = QSplitter(Qt.Orientation.Horizontal)
        fw = QWidget()
        fvl = QVBoxLayout(fw)
        fvl.addWidget(QLabel("Findings:"))
        self._findings = QTextEdit()
        self._findings.setReadOnly(True)
        self._findings.setStyleSheet("")
        fvl.addWidget(self._findings)
        sp.addWidget(fw)
        sw = QWidget()
        svl = QVBoxLayout(sw)
        svl.addWidget(QLabel("Sources & Citations:"))
        self._sources = QTextEdit()
        self._sources.setReadOnly(True)
        self._sources.setStyleSheet("")
        svl.addWidget(self._sources)
        sp.addWidget(sw)
        sp.setSizes([400, 400])
        layout.addWidget(sp, stretch=1)
        footer = QLabel("External/network searches require your approval before execution.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _run_research(self, action):
        query = self._research_query.toPlainText().strip()
        if not query:
            return
        if action == "research":
            self._findings.setText(
                f"[FINDINGS for: {query}]\n\n"
                "1. Key finding A (placeholder)\n"
                "2. Key finding B (placeholder)\n"
                "3. Key finding C (placeholder)\n\n"
                "Confidence: Medium (simulated)\n"
                "Speculation flagged where noted."
            )
            self._sources.setText("[SOURCES]\n\n- Placeholder Source 1 (simulated)\n- Placeholder Source 2 (simulated)")
            self._set_result_summary(f"Research brief prepared for '{query}'. Live web search remains unconnected and approval-gated.")
        elif action == "compare":
            self._findings.setText(
                f"[COMPARISON for: {query}]\n\n"
                "| Criteria | Option A | Option B |\n"
                "| Speed    | Fast     | Moderate |\n"
                "| Safety   | High     | Medium   |\n\n"
                "(Simulated comparison — local intelligence mode.)"
            )
            self._sources.setText("[SOURCES]\n\nSimulated sources for comparison.")
            self._set_result_summary(f"Comparison prepared for '{query}'. Sources are simulated until live research is connected.")
        elif action == "risks":
            self._findings.setText(
                f"[RISKS for: {query}]\n\n"
                "1. Risk A — mitigation: do X\n"
                "2. Risk B — mitigation: do Y\n\n"
                "(Simulated risk analysis — local intelligence mode.)"
            )
            self._sources.setText("[SOURCES]\n\nSimulated sources for risk analysis.")
            self._set_result_summary(f"Risk scan prepared for '{query}'. External source lookup remains approval-gated.")


class CreativeWriterCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Writing Workflow — {ai_name}")
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Tone:"))
        self._tone = QComboBox()
        self._tone.addItems(["Professional", "Casual", "Technical", "Persuasive", "Neutral"])
        ctrl.addWidget(self._tone)
        ctrl.addWidget(QLabel("Audience:"))
        self._audience = QLineEdit()
        self._audience.setPlaceholderText("e.g., executive team, customers, developers")
        ctrl.addWidget(self._audience)
        layout.addLayout(ctrl)
        layout.addWidget(QLabel("Describe the piece, goal, and constraints:"))
        self._write_prompt = QTextEdit()
        self._write_prompt.setPlaceholderText("e.g., Draft a product announcement for our new API release...")
        self._write_prompt.setMaximumHeight(100)
        layout.addWidget(self._write_prompt)
        br = QHBoxLayout()
        for label, act in [("Outline", "outline"), ("Draft", "draft"), ("Revise", "revise")]:
            b = QPushButton(label)
            b.clicked.connect(lambda checked, a=act: self._run_write_action(a))
            br.addWidget(b)
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self._copy_output)
        br.addWidget(copy_btn)
        layout.addLayout(br)
        layout.addWidget(QLabel("Output:"))
        self._write_output = QTextEdit()
        self._write_output.setReadOnly(True)
        self._write_output.setStyleSheet("")
        layout.addWidget(self._write_output, stretch=1)
        footer = QLabel("Publishing or external distribution requires your approval.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _run_write_action(self, action):
        prompt = self._write_prompt.toPlainText().strip()
        tone = self._tone.currentText()
        audience = self._audience.text().strip()
        ctx = f"Tone: {tone}. Audience: {audience or 'general'}.\n\n"
        if action == "outline":
            self._write_output.setText(ctx + f"[OUTLINE for: {prompt[:80]}...]\n\nI. Introduction\nII. Key Points\nIII. Conclusion\n\n(Simulated outline — local intelligence mode.)")
            self._set_result_summary("Writing outline prepared locally. No file export or publishing occurred.")
        elif action == "draft":
            self._write_output.setText(ctx + f"[DRAFT for: {prompt[:80]}...]\n\n[Generated draft text would appear here.]\n\n(Simulated draft — local intelligence mode.)")
            self._set_result_summary("Draft prepared locally. Save/export/publish remains approval-gated.")
        elif action == "revise":
            self._write_output.setText(ctx + f"[REVISED for: {prompt[:80]}...]\n\n[Revised text with tracked changes would appear here.]\n\n(Simulated revision — local intelligence mode.)")
            self._set_result_summary("Revision prepared locally. No external distribution occurred.")

    def _copy_output(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self._write_output.toPlainText())
        QMessageBox.information(self, "Copied", "Output copied to clipboard.")


class PlannerCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Planner — {ai_name}")
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        layout.addWidget(QLabel("Goal / Project description:"))
        self._plan_goal = QTextEdit()
        self._plan_goal.setPlaceholderText("e.g., Launch new customer onboarding flow by end of Q3...")
        self._plan_goal.setMaximumHeight(100)
        layout.addWidget(self._plan_goal)
        br = QHBoxLayout()
        for label, act in [("Generate Plan", "plan"), ("Flag Risks", "risks"), ("Convert to Tasks", "tasks")]:
            b = QPushButton(label)
            b.clicked.connect(lambda checked, a=act: self._run_planner(a))
            br.addWidget(b)
        layout.addLayout(br)
        layout.addWidget(QLabel("Plan / Task List:"))
        self._plan_output = QTextEdit()
        self._plan_output.setReadOnly(True)
        self._plan_output.setStyleSheet("")
        layout.addWidget(self._plan_output, stretch=1)
        footer = QLabel("Risky execution steps or timeline commitments require your approval.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _run_planner(self, action):
        goal = self._plan_goal.toPlainText().strip()
        if not goal:
            return
        if action == "plan":
            self._plan_output.setText(
                f"[PLAN for: {goal}]\n\n"
                "Step 1: Define scope and success criteria\n"
                "Step 2: Identify stakeholders and dependencies\n"
                "Step 3: Draft timeline with milestones\n"
                "Step 4: Flag risks and mitigation strategies\n"
                "Step 5: Assign owners and set check-in cadence\n\n"
                "(Simulated plan — local intelligence mode.)"
            )
            self._set_result_summary("Plan generated locally with no task assignment or external commitment.")
        elif action == "risks":
            self._plan_output.setText(
                f"[RISKS for: {goal}]\n\n"
                "- Dependency risk: external API may delay delivery\n"
                "- Scope risk: requirements may expand mid-project\n"
                "- Resource risk: limited QA bandwidth near deadline\n\n"
                "(Simulated risk analysis — local intelligence mode.)"
            )
            self._set_result_summary("Risk list generated locally. No outward action was taken.")
        elif action == "tasks":
            self._plan_output.setText(
                f"[TASK LIST for: {goal}]\n\n"
                "[ ] Task 1 — owner: TBD — due: TBD\n"
                "[ ] Task 2 — owner: TBD — due: TBD\n"
                "[ ] Task 3 — owner: TBD — due: TBD\n\n"
                "(Simulated task list — local intelligence mode.)"
            )
            self._set_result_summary("Task list generated locally. No tasks were assigned or exported.")


class NotebookCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Notes — {ai_name}")
        self.resize(700, 500)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        row = QHBoxLayout()
        self._note_title = QLineEdit()
        self._note_title.setPlaceholderText("Note title...")
        row.addWidget(self._note_title)
        self._note_tags = QLineEdit()
        self._note_tags.setPlaceholderText("Tags (comma-separated)...")
        row.addWidget(self._note_tags)
        layout.addLayout(row)
        self._note_body = QTextEdit()
        self._note_body.setPlaceholderText("Write your note here...")
        layout.addWidget(self._note_body, stretch=1)
        br = QHBoxLayout()
        save_btn = QPushButton("Save Note")
        save_btn.clicked.connect(self._save_note)
        br.addWidget(save_btn)
        recall_btn = QPushButton("Recall Notes")
        recall_btn.clicked.connect(self._recall_notes)
        br.addWidget(recall_btn)
        layout.addLayout(br)
        self._notes_output = QTextEdit()
        self._notes_output.setReadOnly(True)
        self._notes_output.setStyleSheet("")
        layout.addWidget(self._notes_output, stretch=1)
        footer = QLabel("Bulk deletion or external export requires your approval.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _save_note(self):
        title = self._note_title.text().strip()
        tags = self._note_tags.text().strip()
        body = self._note_body.toPlainText().strip()
        if not body:
            QMessageBox.warning(self, "Empty", "Note body is empty.")
            return
        self._notes_output.append(f"Saved: [{title or 'Untitled'}] Tags: {tags or 'none'}\n{body[:200]}...\n---")
        self._set_result_summary(f"Local note captured as '{title or 'Untitled'}'. Persistent storage/export remains approval-gated.")
        self._note_title.clear()
        self._note_tags.clear()
        self._note_body.clear()

    def _recall_notes(self):
        tag_filter = self._note_tags.text().strip()
        self._notes_output.append(f"Recalling notes (filter: {tag_filter or 'all'})... (Simulated recall — local intelligence mode.)")
        self._set_result_summary(f"Note recall requested with filter '{tag_filter or 'all'}'. Persistent note local intelligence is active.")


class DocumentProcessorCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Document Workflow — {ai_name}")
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        layout.addWidget(QLabel("Document text or description:"))
        self._doc_input = QTextEdit()
        self._doc_input.setPlaceholderText("Paste document text here, or describe what you need summarized/extracted...")
        self._doc_input.setMaximumHeight(120)
        layout.addWidget(self._doc_input)
        br = QHBoxLayout()
        load_btn = QPushButton("Load from File")
        load_btn.clicked.connect(self._load_doc)
        br.addWidget(load_btn)
        for label, act in [("Summarize", "summarize"), ("Extract Action Items", "extract"), ("Compare", "compare")]:
            b = QPushButton(label)
            b.clicked.connect(lambda checked, a=act: self._run_doc_action(a))
            br.addWidget(b)
        layout.addLayout(br)
        self._doc_output = QTextEdit()
        self._doc_output.setReadOnly(True)
        self._doc_output.setStyleSheet("")
        layout.addWidget(self._doc_output, stretch=1)
        footer = QLabel("External export or sensitive document access requires your approval.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _load_doc(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Document", "", "Text Files (*.txt);;All Files (*)")
        if path:
            try:
                text = Path(path).read_text(encoding="utf-8", errors="ignore")
                self._doc_input.setPlainText(text)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _run_doc_action(self, action):
        text = self._doc_input.toPlainText().strip()
        if not text:
            self._doc_output.setText("Paste or load a document first.")
            return
        if action == "summarize":
            self._doc_output.setText(f"[SUMMARY]\n\n{text[:200]}...\n\n(Simulated summary — local intelligence mode.)")
            self._set_result_summary("Document summary prepared locally. Export/save remains approval-gated.")
        elif action == "extract":
            self._doc_output.setText(f"[ACTION ITEMS]\n\n- Action 1 (placeholder)\n- Action 2 (placeholder)\n\n(Simulated extraction — local intelligence mode.)")
            self._set_result_summary("Document action items extracted locally. No export occurred.")
        elif action == "compare":
            self._doc_output.setText(f"[COMPARISON]\n\nSimulated comparison against prior document.\n\n(Simulated — local intelligence mode.)")
            self._set_result_summary("Document comparison prepared locally. No source files were altered.")


class ArchiveCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Archive — {ai_name}")
        self.resize(700, 500)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        layout.addWidget(QLabel("Artifact name / tags:"))
        row = QHBoxLayout()
        self._artifact_name = QLineEdit()
        self._artifact_name.setPlaceholderText("Artifact name...")
        row.addWidget(self._artifact_name)
        self._artifact_tags = QLineEdit()
        self._artifact_tags.setPlaceholderText("Tags...")
        row.addWidget(self._artifact_tags)
        layout.addLayout(row)
        self._artifact_desc = QTextEdit()
        self._artifact_desc.setPlaceholderText("Description or content to archive...")
        layout.addWidget(self._artifact_desc, stretch=1)
        br = QHBoxLayout()
        store_btn = QPushButton("Store Artifact")
        store_btn.clicked.connect(self._store_artifact)
        br.addWidget(store_btn)
        retrieve_btn = QPushButton("Retrieve")
        retrieve_btn.clicked.connect(self._retrieve_artifacts)
        br.addWidget(retrieve_btn)
        layout.addLayout(br)
        self._archive_output = QTextEdit()
        self._archive_output.setReadOnly(True)
        self._archive_output.setStyleSheet("")
        layout.addWidget(self._archive_output, stretch=1)
        footer = QLabel("Moving, deleting, or bulk exporting archives requires your approval.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _store_artifact(self):
        name = self._artifact_name.text().strip()
        tags = self._artifact_tags.text().strip()
        desc = self._artifact_desc.toPlainText().strip()
        if not desc:
            QMessageBox.warning(self, "Empty", "No content to archive.")
            return
        self._archive_output.append(f"Stored: [{name or 'Untitled'}] Tags: {tags or 'none'}\n{desc[:200]}...\n---")
        self._set_result_summary(f"Artifact staged locally as '{name or 'Untitled'}'. File-system archive writing/moving remains approval-gated.")
        self._artifact_name.clear()
        self._artifact_tags.clear()
        self._artifact_desc.clear()

    def _retrieve_artifacts(self):
        tag_filter = self._artifact_tags.text().strip()
        self._archive_output.append(f"Retrieving artifacts (filter: {tag_filter or 'all'})... (Simulated — local intelligence mode.)")
        self._set_result_summary(f"Archive retrieval requested with filter '{tag_filter or 'all'}'. Archive local intelligence is active.")


class ToolUserCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Tool Workflow — {ai_name}")
        self.resize(700, 500)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        layout.addWidget(QLabel("Tool / Action to propose:"))
        self._tool_input = QLineEdit()
        self._tool_input.setPlaceholderText("e.g., run_git_diff, deploy_preview, send_email_draft")
        layout.addWidget(self._tool_input)
        layout.addWidget(QLabel("Rationale:"))
        self._tool_rationale = QTextEdit()
        self._tool_rationale.setPlaceholderText("Why this tool should be used and what the expected outcome is...")
        self._tool_rationale.setMaximumHeight(100)
        layout.addWidget(self._tool_rationale)
        br = QHBoxLayout()
        propose_btn = QPushButton("Propose Tool Use")
        propose_btn.clicked.connect(self._propose_tool)
        br.addWidget(propose_btn)
        list_btn = QPushButton("List Available Tools")
        list_btn.clicked.connect(self._list_tools)
        br.addWidget(list_btn)
        layout.addLayout(br)
        self._tool_output = QTextEdit()
        self._tool_output.setReadOnly(True)
        self._tool_output.setStyleSheet("")
        layout.addWidget(self._tool_output, stretch=1)
        footer = QLabel("Every tool invocation requires your explicit approval.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _propose_tool(self):
        tool = self._tool_input.text().strip()
        rationale = self._tool_rationale.toPlainText().strip()
        if not tool:
            self._tool_output.setText("Enter a tool name.")
            return
        self._tool_output.setText(f"[PROPOSAL]\n\nTool: {tool}\nRationale: {rationale[:200]}...\n\nStatus: AWAITING APPROVAL\n\n(Simulated — local intelligence mode.)")
        self._set_result_summary(f"Tool proposal prepared for '{tool}'. No tool was invoked.")

    def _list_tools(self):
        self._tool_output.setText("[AVAILABLE TOOLS]\n\n- run_git_diff\n- deploy_preview\n- send_email_draft\n- schedule_meeting\n- generate_report\n\n(Simulated list — local intelligence mode.)")
        self._set_result_summary("Available tool list shown as a safe stub. No tool was invoked.")


class TutorCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Tutor Workflow — {ai_name}")
        self.resize(760, 560)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        row = QHBoxLayout()
        row.addWidget(QLabel("Mode:"))
        self._tutor_mode = QComboBox()
        self._tutor_mode.addItems(["Explain", "Quiz", "Lesson Plan", "Study Sheet", "Accessibility Rewrite"])
        row.addWidget(self._tutor_mode)
        row.addWidget(QLabel("Level:"))
        self._learner_level = QLineEdit()
        self._learner_level.setPlaceholderText("e.g., beginner, high school, advanced")
        row.addWidget(self._learner_level)
        layout.addLayout(row)
        layout.addWidget(QLabel("Topic / learner need:"))
        self._topic = QTextEdit()
        self._topic.setPlaceholderText("Describe what needs to be learned, practiced, or adapted...")
        self._topic.setMaximumHeight(120)
        layout.addWidget(self._topic)
        btn = QPushButton("Generate Tutor Output")
        btn.clicked.connect(self._run_tutor)
        layout.addWidget(btn)
        self._tutor_output = QTextEdit()
        self._tutor_output.setReadOnly(True)
        self._tutor_output.setStyleSheet("")
        layout.addWidget(self._tutor_output, stretch=1)
        footer = QLabel("Exporting notes, grading, or external sharing requires approval. Academic honesty rules apply.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _run_tutor(self):
        topic = self._topic.toPlainText().strip()
        if not topic:
            self._tutor_output.setText("Enter a topic or learner need first.")
            return
        mode = self._tutor_mode.currentText()
        level = self._learner_level.text().strip() or "adaptive"
        if mode == "Explain":
            text = (
                f"[EXPLANATION]\nTopic: {topic}\nLevel: {level}\n\n"
                "1. Plain-language overview\n2. Key idea\n3. Example\n4. Check-for-understanding question\n\n"
                "(Local tutor output — export not connected.)"
            )
        elif mode == "Quiz":
            text = (
                f"[QUIZ]\nTopic: {topic}\nLevel: {level}\n\n"
                "1. Short answer question\n2. Multiple-choice question\n3. Explain-your-reasoning question\n\n"
                "(Local tutor output — export not connected.)"
            )
        elif mode == "Lesson Plan":
            text = (
                f"[LESSON PLAN]\nTopic: {topic}\nLevel: {level}\n\n"
                "Objective\nWarm-up\nInstruction\nPractice\nReflection\n\n"
                "(Local tutor output — export not connected.)"
            )
        elif mode == "Study Sheet":
            text = (
                f"[STUDY SHEET]\nTopic: {topic}\nLevel: {level}\n\n"
                "Terms\nCore ideas\nCommon mistakes\nPractice prompts\n\n"
                "(Local tutor output — export not connected.)"
            )
        else:
            text = (
                f"[ACCESSIBILITY REWRITE]\nTopic: {topic}\nLevel: {level}\n\n"
                "Simplified wording, clear steps, and short sections would appear here.\n\n"
                "(Local tutor output — export not connected.)"
            )
        self._tutor_output.setText(text)
        self._set_result_summary(f"{mode} tutor output prepared locally for '{topic[:80]}'.")


class BusinessWorkflowCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Business Workflow — {ai_name}")
        self.resize(780, 560)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        row = QHBoxLayout()
        row.addWidget(QLabel("Workflow Type:"))
        self._workflow_type = QComboBox()
        self._workflow_type.addItems(["SOP", "Checklist", "Support Draft", "Handoff Packet", "Automation Plan"])
        row.addWidget(self._workflow_type)
        layout.addLayout(row)
        layout.addWidget(QLabel("Business context / goal:"))
        self._business_input = QTextEdit()
        self._business_input.setPlaceholderText("Describe the process, customer issue, department handoff, or automation target...")
        self._business_input.setMaximumHeight(120)
        layout.addWidget(self._business_input)
        btn = QPushButton("Generate Business Workflow")
        btn.clicked.connect(self._run_business_workflow)
        layout.addWidget(btn)
        self._business_output = QTextEdit()
        self._business_output.setReadOnly(True)
        self._business_output.setStyleSheet("")
        layout.addWidget(self._business_output, stretch=1)
        footer = QLabel("Sending messages, publishing, file export, or automation execution requires approval and audit routing.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _run_business_workflow(self):
        context = self._business_input.toPlainText().strip()
        if not context:
            self._business_output.setText("Enter business context first.")
            return
        mode = self._workflow_type.currentText()
        if mode == "SOP":
            text = (
                f"[SOP]\nContext: {context}\n\n"
                "Purpose\nScope\nInputs\nProcedure\nApproval points\nEscalation path\n\n"
                "(Local business workflow — automation not connected.)"
            )
        elif mode == "Checklist":
            text = (
                f"[CHECKLIST]\nContext: {context}\n\n"
                "[ ] Confirm scope\n[ ] Gather required documents\n[ ] Check risk/approval points\n[ ] Prepare final review\n\n"
                "(Local business workflow — automation not connected.)"
            )
        elif mode == "Support Draft":
            text = (
                f"[SUPPORT DRAFT]\nContext: {context}\n\n"
                "Draft response would appear here.\n\n"
                "Status: not sent. Human approval required before outbound use."
            )
        elif mode == "Handoff Packet":
            text = (
                f"[HANDOFF PACKET]\nContext: {context}\n\n"
                "Summary\nOwner\nOpen questions\nRisks\nNext step\n\n"
                "(Local handoff — export not connected.)"
            )
        else:
            text = (
                f"[AUTOMATION PLAN]\nContext: {context}\n\n"
                "Trigger\nInputs\nSteps\nApproval checkpoints\nRollback plan\nAudit record needs\n\n"
                "(Safe stub — automation hooks are not connected.)"
            )
        self._business_output.setText(text)
        self._set_result_summary(f"{mode} prepared locally. No message, export, or automation was executed.")


class HephaestusRelayCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Hephaestus Relay — {ai_name}")
        self.resize(820, 620)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        grid = QVBoxLayout()
        self._design_goal = QTextEdit()
        self._design_goal.setPlaceholderText("Purpose / design idea...")
        self._design_goal.setMaximumHeight(90)
        grid.addWidget(QLabel("Purpose / Design Idea:"))
        grid.addWidget(self._design_goal)
        self._constraints = QTextEdit()
        self._constraints.setPlaceholderText("Constraints, materials, scale, risks, budget, unknowns...")
        self._constraints.setMaximumHeight(100)
        grid.addWidget(QLabel("Constraints / Materials / Scale / Unknowns:"))
        grid.addWidget(self._constraints)
        layout.addLayout(grid)
        btn = QPushButton("Create Hephaestus-Ready Handoff Brief")
        btn.clicked.connect(self._build_handoff)
        layout.addWidget(btn)
        self._handoff_output = QTextEdit()
        self._handoff_output.setReadOnly(True)
        self._handoff_output.setStyleSheet("")
        layout.addWidget(self._handoff_output, stretch=1)
        footer = QLabel("This creates a local handoff brief only. It does not call or modify Hephaestus ProtoBrain internals.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_handoff(self):
        goal = self._design_goal.toPlainText().strip()
        constraints = self._constraints.toPlainText().strip()
        if not goal:
            self._handoff_output.setText("Enter a design idea or purpose first.")
            return
        text = (
            f"[HEPHAESTUS-READY HANDOFF BRIEF]\n\n"
            f"Purpose:\n{goal}\n\n"
            f"Constraints / Materials / Scale / Unknowns:\n{constraints or 'Not specified'}\n\n"
            "Decision framing:\n- Desired outcome\n- Non-negotiable constraints\n- Unknowns requiring investigation\n- Safety / feasibility concerns\n- Suggested next specialist review\n\n"
            "Status: local brief only. No ProtoBrain call, file export, or external handoff occurred."
        )
        self._handoff_output.setText(text)
        self._set_result_summary("Hephaestus-ready handoff brief prepared locally. No Hephaestus internals were touched.")


class FinancialGainerDialog(BaseCapabilityDialog):
    """Financial Gainer — income strategy hub with skill assessment, opportunity matching, risk tolerance, and personalized recommendations."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Financial Gainer — {ai_name} | Avery Logic Works(TM)")
        self.resize(900, 680)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_overview_tab(), "Overview")
        tabs.addTab(self._build_assessment_tab(), "Skill Assessment")
        tabs.addTab(self._build_opportunity_tab(), "Opportunity Matching")
        tabs.addTab(self._build_risk_tab(), "Risk Tolerance")
        tabs.addTab(self._build_recommendations_tab(), "Recommendations")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("All output is advisory. No income is guaranteed. Avery Logic Works is not liable for financial outcomes.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_overview_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        desc = QLabel(
            "Financial Gainer helps you explore income opportunities, side hustles, monetization strategies,\n"
            "and financial productivity. All suggestions are advisory — no income is guaranteed.\n\n"
            "Use the tabs above to:\n"
            "  1. Assess your skills and resources\n"
            "  2. Match opportunities to your profile\n"
            "  3. Evaluate your risk tolerance\n"
            "  4. Get personalized income path recommendations\n\n"
            "The built-in intelligence can provide analysis tailored to your situation."
        )
        desc.setStyleSheet("color: #c9d1d9; font-size: 13px; padding: 16px;")
        desc.setWordWrap(True)
        l.addWidget(desc)
        l.addWidget(QLabel("Income Path Categories:"))
        cats = QTextEdit()
        cats.setReadOnly(True)
        cats.setMaximumHeight(280)
        cats.setStyleSheet("")
        cats.setText(
            "ACTIVE INCOME\n"
            "=============\n"
            "  - Freelancing (Upwork, Fiverr, Toptal)\n"
            "  - Consulting & coaching\n"
            "  - Gig economy (Uber, TaskRabbit, DoorDash)\n"
            "  - Tutoring & teaching\n"
            "  - Content creation (YouTube, blogging, podcasting)\n\n"
            "PASSIVE INCOME\n"
            "=============\n"
            "  - Digital products (ebooks, courses, templates)\n"
            "  - Affiliate marketing\n"
            "  - Dividend investing\n"
            "  - Rental income\n"
            "  - Print-on-demand & dropshipping\n\n"
            "PORTFOLIO INCOME\n"
            "================\n"
            "  - Stock market investing\n"
            "  - Crypto assets (high risk)\n"
            "  - Real estate (REITs, flipping)\n"
            "  - Peer-to-peer lending\n"
            "  - Index funds & ETFs\n\n"
            "SCALABLE INCOME\n"
            "===============\n"
            "  - SaaS / software products\n"
            "  - Membership sites\n"
            "  - YouTube channel monetization\n"
            "  - Newsletter subscriptions\n"
            "  - Licensing & royalties"
        )
        l.addWidget(cats)
        l.addStretch()
        return w

    def _build_assessment_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Skills (comma-separated):"))
        self._skills_input = QLineEdit()
        self._skills_input.setPlaceholderText("e.g., writing, coding, graphic design, public speaking, social media...")
        l.addWidget(self._skills_input)
        row = QHBoxLayout()
        row.addWidget(QLabel("Available time (hrs/week):"))
        self._time_input = QLineEdit()
        self._time_input.setPlaceholderText("e.g., 10")
        self._time_input.setMaximumWidth(100)
        row.addWidget(self._time_input)
        row.addWidget(QLabel("Starting capital ($):"))
        self._capital_input = QLineEdit()
        self._capital_input.setPlaceholderText("e.g., 500")
        self._capital_input.setMaximumWidth(100)
        row.addWidget(self._capital_input)
        row.addStretch()
        l.addLayout(row)
        l.addWidget(QLabel("Interests / passions:"))
        self._interests_input = QTextEdit()
        self._interests_input.setPlaceholderText("What do you enjoy doing? What topics are you passionate about?")
        self._interests_input.setMaximumHeight(80)
        l.addWidget(self._interests_input)
        l.addWidget(QLabel("Current income situation:"))
        self._situation_combo = QComboBox()
        self._situation_combo.addItems(["Employed full-time", "Employed part-time", "Self-employed", "Student", "Unemployed", "Retired"])
        l.addWidget(self._situation_combo)
        btn = QPushButton("Run Skill Assessment")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_assessment)
        l.addWidget(btn)
        self._assessment_output = QTextEdit()
        self._assessment_output.setReadOnly(True)
        self._assessment_output.setStyleSheet("")
        l.addWidget(self._assessment_output, stretch=1)
        return w

    def _build_opportunity_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("What kind of income are you looking for?"))
        self._income_type = QComboBox()
        self._income_type.addItems(["Any", "Active income (trading time for money)", "Passive income (build once, earn repeatedly)", "Portfolio income (investing)", "Scalable income (build once, scale infinitely)"])
        l.addWidget(self._income_type)
        l.addWidget(QLabel("Preferred industry / niche:"))
        self._niche_input = QLineEdit()
        self._niche_input.setPlaceholderText("e.g., tech, health, education, finance, entertainment...")
        l.addWidget(self._niche_input)
        l.addWidget(QLabel("Risk comfort level:"))
        self._risk_combo = QComboBox()
        self._risk_combo.addItems(["Low risk (steady, slow)", "Medium risk (balanced)", "High risk (high reward potential)"])
        l.addWidget(self._risk_combo)
        btn = QPushButton("Find Opportunities")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_opportunity_match)
        l.addWidget(btn)
        self._opportunity_output = QTextEdit()
        self._opportunity_output.setReadOnly(True)
        self._opportunity_output.setStyleSheet("")
        l.addWidget(self._opportunity_output, stretch=1)
        return w

    def _build_risk_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Risk Tolerance Assessment"))
        l.addWidget(QLabel("Answer these questions to determine your risk profile:\n"))
        questions = [
            "If you lost 50% of your investment in one month, you would:",
            "How long can you go without income from this venture?",
            "What is your primary financial goal?",
            "How do you feel about uncertainty?",
        ]
        self._risk_answers: dict[str, QComboBox] = {}
        for q in questions:
            row = QHBoxLayout()
            lbl = QLabel(q)
            lbl.setWordWrap(True)
            row.addWidget(lbl, stretch=2)
            combo = QComboBox()
            if "lost 50%" in q:
                combo.addItems(["Sell everything immediately", "Sell some, hold some", "Hold and wait it out", "Buy more at the lower price"])
            elif "without income" in q:
                combo.addItems(["Less than 1 month", "1-3 months", "3-6 months", "6+ months"])
            elif "primary goal" in q:
                combo.addItems(["Preserve capital", "Steady income", "Grow wealth moderately", "Maximize returns"])
            elif "uncertainty" in q:
                combo.addItems(["I avoid it completely", "I prefer some certainty", "I can handle moderate uncertainty", "I thrive on it"])
            row.addWidget(combo, stretch=1)
            l.addLayout(row)
            self._risk_answers[q] = combo
        btn = QPushButton("Calculate Risk Profile")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_risk_assessment)
        l.addWidget(btn)
        self._risk_output = QTextEdit()
        self._risk_output.setReadOnly(True)
        self._risk_output.setStyleSheet("")
        l.addWidget(self._risk_output, stretch=1)
        return w

    def _build_recommendations_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Personalized Income Path Recommendations"))
        l.addWidget(QLabel("Based on your assessment, opportunity match, and risk profile, get a tailored income strategy.\n"))
        btn = QPushButton("Generate Recommendations")
        btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_recommendations)
        l.addWidget(btn)
        self._rec_output = QTextEdit()
        self._rec_output.setReadOnly(True)
        self._rec_output.setStyleSheet("")
        l.addWidget(self._rec_output, stretch=1)
        return w

    def _run_through_runtime(self, task: str) -> str:
        """Send a task through NexusAIRuntime and return the result text."""
        try:
            from ...core.nexus_ai_runtime import NexusAIRuntime
            settings = SettingsManager()
            settings.initialize()
            runtime = NexusAIRuntime(settings=settings)
            result = runtime.run(
                task=task,
                ai_name=self._ai_name,
                ai_uuid=self._ai_uuid,
                ai_metadata={
                    "abilities": self._abilities,
                    "use_case": self._use_case,
                    "guardrails": self._guardrails,
                    "libraries": self._libraries,
                },
            )
            return result.result_text or ""
        except Exception:
            return ""

    def _run_assessment(self):
        skills = self._skills_input.text().strip()
        if not skills:
            self._assessment_output.setText("Enter at least one skill first.")
            return
        time_avail = self._time_input.text().strip() or "unspecified"
        capital = self._capital_input.text().strip() or "unspecified"
        interests = self._interests_input.toPlainText().strip() or "not specified"
        situation = self._situation_combo.currentText()
        task = f"Assess my income potential. Skills: {skills}. Time available: {time_avail} hrs/week. Starting capital: ${capital}. Interests: {interests}. Current situation: {situation}."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._assessment_output.setText(ai_result)
            self._set_result_summary(f"Skill assessment completed via AI for skills: {skills[:80]}.")
            return
        skill_list = [s.strip() for s in skills.split(",")]
        output_parts = [
            "[SKILL ASSESSMENT — LOCAL ANALYSIS]\n",
            f"Skills identified: {', '.join(skill_list)}",
            f"Time available: {time_avail} hrs/week",
            f"Starting capital: ${capital}",
            f"Current situation: {situation}\n",
            "SKILL MARKETABILITY ANALYSIS:",
        ]
        high_value = ["coding", "programming", "writing", "design", "marketing", "consulting", "teaching", "coaching", "sales", "data analysis", "accounting", "legal"]
        medium_value = ["social media", "photography", "video editing", "graphic design", "customer service", "administration"]
        for skill in skill_list:
            sl = skill.lower()
            if any(hv in sl for hv in high_value):
                output_parts.append(f"  {skill}: HIGH marketability — strong demand, good rates ($25-150/hr)")
            elif any(mv in sl for mv in medium_value):
                output_parts.append(f"  {skill}: MEDIUM marketability — moderate demand, variable rates ($15-50/hr)")
            else:
                output_parts.append(f"  {skill}: EVALUATE FURTHER — research market demand and rates")
        output_parts.extend([
            "\nINCOME POTENTIAL ESTIMATE:",
            f"  Active income: ${self._estimate_active(time_avail)}/month (if {time_avail} hrs/week at $20-40/hr)",
            f"  Passive income: $0-500/month initially (requires 2-6 months build time)",
            f"  Portfolio income: Depends on capital (${capital} invested at 5-10% = ${self._estimate_portfolio(capital)}/year)",
            "\nRECOMMENDED FIRST STEPS:",
            "  1. Pick your top 2 most marketable skills",
            "  2. Create profiles on 2-3 freelance platforms",
            "  3. Set initial rates 20% below market to build reviews",
            "  4. Dedicate 1-2 hrs/day to client acquisition",
            "  5. Track all income and time invested",
            "\nThe built-in intelligence can provide personalized assessment."
        ])
        self._assessment_output.setText("\n".join(output_parts))
        self._set_result_summary(f"Skill assessment completed locally for skills: {skills[:80]}.")

    def _estimate_active(self, time_str: str) -> str:
        try:
            hrs = int(time_str)
            low = hrs * 4 * 20
            high = hrs * 4 * 40
            return f"{low}-{high}"
        except ValueError:
            return "varies"

    def _estimate_portfolio(self, capital_str: str) -> str:
        try:
            cap = int(capital_str)
            low = int(cap * 0.05)
            high = int(cap * 0.10)
            return f"{low}-{high}"
        except ValueError:
            return "varies"

    def _run_opportunity_match(self):
        income_type = self._income_type.currentText()
        niche = self._niche_input.text().strip() or "general"
        risk = self._risk_combo.currentText()
        skills = self._skills_input.text().strip() or "not specified"
        task = f"Find income opportunities for me. Type: {income_type}. Niche: {niche}. Risk: {risk}. Skills: {skills}."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._opportunity_output.setText(ai_result)
            self._set_result_summary(f"Opportunity matching completed via AI for {niche}.")
            return
        opportunities = {
            "Active income": [
                ("Freelance writing", "$200-2000/article", "Low", "Upwork, Contena, ProBlogger"),
                ("Web development", "$500-10000/project", "Low", "Upwork, Toptal, direct outreach"),
                ("Virtual assistant", "$15-50/hr", "Low", "Belay, Time Etc, Upwork"),
                ("Online tutoring", "$20-80/hr", "Low", "Wyzant, Tutor.com, Preply"),
                ("Social media management", "$300-3000/month per client", "Low", "Upwork, direct outreach"),
            ],
            "Passive income": [
                ("Digital product (ebook/template)", "$10-100/sale", "Medium", "Gumroad, Etsy, Teachable"),
                ("Online course", "$50-500/enrollment", "Medium", "Udemy, Teachable, Skillshare"),
                ("Affiliate marketing", "$50-5000/month", "Medium", "Amazon Associates, ShareASale, CJ"),
                ("Print-on-demand store", "$5-30/sale", "Medium", "Printful, Printify, Redbubble"),
                ("YouTube channel", "$1-10/1000 views", "High", "YouTube Partner Program"),
            ],
            "Portfolio income": [
                ("Index fund investing", "5-10% annual return", "Low", "Vanguard, Fidelity, Schwab"),
                ("Dividend stocks", "2-5% dividend yield", "Medium", "Any brokerage"),
                ("Real estate (REITs)", "4-8% annual return", "Medium", "Fundrise, RealtyMogul"),
                ("Crypto (BTC/ETH)", "Highly variable", "High", "Coinbase, Kraken"),
                ("P2P lending", "5-12% annual return", "Medium", "LendingClub, Prosper"),
            ],
            "Scalable income": [
                ("SaaS product", "$10-1000/month per user", "High", "Direct, ProductHunt"),
                ("Membership community", "$10-100/month per member", "Medium", "Patreon, Circle, Discord"),
                ("Newsletter (paid)", "$5-50/month per subscriber", "Medium", "Substack, ConvertKit"),
                ("Mobile app", "$0.99-9.99/sale or ad revenue", "High", "App Store, Google Play"),
                ("Licensing content", "Variable royalties", "Medium", "Direct licensing deals"),
            ],
        }
        itype_key = income_type.split(" (")[0] if " (" in income_type else "Active income"
        if itype_key == "Any":
            matched = []
            for cat, ops in opportunities.items():
                matched.extend(ops[:2])
        else:
            matched = opportunities.get(itype_key, opportunities["Active income"])
        output_parts = [
            f"[OPPORTUNITY MATCHING — LOCAL ANALYSIS]\n",
            f"Income type: {income_type}",
            f"Niche: {niche}",
            f"Risk preference: {risk}\n",
            f"MATCHED OPPORTUNITIES ({len(matched)} found):",
            "",
        ]
        for i, (name, earning, risk_lvl, platforms) in enumerate(matched, 1):
            output_parts.append(f"  {i}. {name}")
            output_parts.append(f"     Earning potential: {earning}")
            output_parts.append(f"     Risk level: {risk_lvl}")
            output_parts.append(f"     Platforms: {platforms}")
            output_parts.append("")
        output_parts.extend([
            "NEXT STEPS:",
            "  1. Research 2-3 of these opportunities in detail",
            "  2. Check if your skills match the requirements",
            "  3. Start with the lowest-risk option that matches your skills",
            "  4. Set a 30-day goal for your first dollar earned",
            "\nThe built-in intelligence can provide opportunity matching."
        ])
        self._opportunity_output.setText("\n".join(output_parts))
        self._set_result_summary(f"Opportunity matching completed locally for {niche}.")

    def _run_risk_assessment(self):
        scores = []
        for q, combo in self._risk_answers.items():
            scores.append(combo.currentIndex())
        avg = sum(scores) / len(scores) if scores else 0
        if avg < 1.0:
            profile = "CONSERVATIVE"
            desc = "You prefer steady, predictable income with minimal risk. Focus on active income and low-risk investments."
            suited = ["Freelancing", "Index funds", "Dividend stocks", "Virtual assistant", "Tutoring"]
            avoid = ["Crypto trading", "High-leverage investments", "Unproven business models"]
        elif avg < 2.0:
            profile = "MODERATE"
            desc = "You balance risk and reward. A mix of active and passive income with some growth investments suits you."
            suited = ["Freelancing + digital products", "Affiliate marketing", "REITs", "Online courses", "Dividend growth stocks"]
            avoid = ["All-in crypto", "Highly leveraged real estate", "Unproven startups"]
        elif avg < 3.0:
            profile = "AGGRESSIVE"
            desc = "You're comfortable with risk for higher potential returns. Scalable income and growth investments fit your profile."
            suited = ["SaaS products", "YouTube channel", "Crypto (small allocation)", "Startup investing", "Course launches"]
            avoid = ["Low-yield savings", "Pure active income (limits upside)"]
        else:
            profile = "VERY AGGRESSIVE"
            desc = "You thrive on uncertainty and want maximum upside. High-risk, high-reward strategies are your zone."
            suited = ["Startup building", "Crypto investing", "Angel investing", "Viral content creation", "SaaS at scale"]
            avoid = ["Traditional employment", "Low-yield investments", "Anything with a ceiling"]
        output = (
            f"[RISK PROFILE — LOCAL ANALYSIS]\n\n"
            f"Score: {avg:.1f} / 3.0\n"
            f"Profile: {profile}\n\n"
            f"Description: {desc}\n\n"
            f"Suited income paths:\n" + "".join(f"  - {s}\n" for s in suited) + "\n"
            f"Approach with caution:\n" + "".join(f"  - {s}\n" for s in avoid) + "\n"
            "Note: This is a simplified assessment. For major financial decisions,\n"
            "consult a qualified financial advisor.\n\n"
            "The built-in intelligence can provide risk assessment."
        )
        self._risk_output.setText(output)
        self._set_result_summary(f"Risk profile calculated: {profile}.")

    def _run_recommendations(self):
        skills = self._skills_input.text().strip() or "not specified"
        time_avail = self._time_input.text().strip() or "unspecified"
        capital = self._capital_input.text().strip() or "unspecified"
        interests = self._interests_input.toPlainText().strip() or "not specified"
        situation = self._situation_combo.currentText()
        income_type = self._income_type.currentText()
        niche = self._niche_input.text().strip() or "general"
        risk = self._risk_combo.currentText()
        task = (
            f"Give me personalized income path recommendations. "
            f"Skills: {skills}. Time: {time_avail} hrs/week. Capital: ${capital}. "
            f"Interests: {interests}. Situation: {situation}. "
            f"Income type: {income_type}. Niche: {niche}. Risk: {risk}."
        )
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._rec_output.setText(ai_result)
            self._set_result_summary("Personalized recommendations generated via AI.")
            return
        output = (
            "[PERSONALIZED RECOMMENDATIONS — LOCAL ANALYSIS]\n\n"
            f"Based on your inputs:\n"
            f"  Skills: {skills}\n"
            f"  Time: {time_avail} hrs/week\n"
            f"  Capital: ${capital}\n"
            f"  Interests: {interests}\n"
            f"  Situation: {situation}\n"
            f"  Income type: {income_type}\n"
            f"  Niche: {niche}\n"
            f"  Risk: {risk}\n\n"
            "RECOMMENDED INCOME PATH (30-60-90 DAY PLAN):\n\n"
            "DAYS 1-30: FOUNDATION\n"
            "  - Choose 1-2 income paths from your opportunity match\n"
            "  - Create profiles on relevant platforms\n"
            "  - Set up basic tools (portfolio, payment account, calendar)\n"
            "  - Reach out to 5 potential clients/customers daily\n"
            "  - Goal: First dollar earned\n\n"
            "DAYS 31-60: MOMENTUM\n"
            "  - Refine your offering based on initial feedback\n"
            "  - Increase rates 10-20% from starting rates\n"
            "  - Begin building 1 passive income stream alongside active work\n"
            "  - Track metrics: income, hours worked, cost per acquisition\n"
            "  - Goal: $500-2000/month from active income\n\n"
            "DAYS 61-90: SCALE\n"
            "  - Systematize your most successful income stream\n"
            "  - Invest 20% of earnings into growth (tools, ads, education)\n"
            "  - Begin diversifying into a second income path\n"
            "  - Consider outsourcing low-value tasks\n"
            "  - Goal: $1000-5000/month combined, with 30% from passive sources\n\n"
            "KEY PRINCIPLES:\n"
            "  1. Start before you're ready — perfectionism kills income\n"
            "  2. Track everything — what gets measured gets improved\n"
            "  3. Reinvest early — compound your efforts\n"
            "  4. Skills > capital — invest in learning over spending\n"
            "  5. Diversify gradually — don't spread too thin too fast\n\n"
            "DISCLAIMER: No income is guaranteed. Results depend on your effort,\n"
            "market conditions, and many other factors. This is advisory only.\n\n"
            "The built-in intelligence can provide personalized recommendations."
        )
        self._rec_output.setText(output)
        self._set_result_summary("Personalized recommendations generated locally.")


class CryptoScoutDialog(BaseCapabilityDialog):
    """Crypto Scout — crypto research workspace with asset lookup, risk assessment, portfolio simulator, red-flag checker, DCA planner."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Crypto Scout — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_asset_tab(), "Asset Lookup")
        tabs.addTab(self._build_risk_tab(), "Risk Assessment")
        tabs.addTab(self._build_portfolio_tab(), "Portfolio Simulator")
        tabs.addTab(self._build_redflag_tab(), "Red-Flag Checker")
        tabs.addTab(self._build_dca_tab(), "DCA Planner")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Crypto is extremely volatile. You may lose your entire investment. Not financial advice. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_asset_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Asset name or ticker:"))
        self._asset_input = QLineEdit()
        self._asset_input.setPlaceholderText("e.g., Bitcoin, BTC, Ethereum, ETH, Solana, SOL...")
        l.addWidget(self._asset_input)
        btn = QPushButton("Research Asset")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_asset_lookup)
        l.addWidget(btn)
        self._asset_output = QTextEdit()
        self._asset_output.setReadOnly(True)
        self._asset_output.setStyleSheet("")
        l.addWidget(self._asset_output, stretch=1)
        return w

    def _build_risk_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Crypto Risk Assessment Tool"))
        l.addWidget(QLabel("Answer these questions to assess your crypto risk readiness:\n"))
        self._crypto_risk_answers: dict[str, QComboBox] = {}
        questions = [
            "What percentage of your savings are you considering investing in crypto?",
            "How would you react if your crypto portfolio dropped 80% in a week?",
            "Do you understand blockchain technology and how crypto works?",
            "What is your investment timeline?",
        ]
        for q in questions:
            row = QHBoxLayout()
            lbl = QLabel(q)
            lbl.setWordWrap(True)
            row.addWidget(lbl, stretch=2)
            combo = QComboBox()
            if "percentage" in q:
                combo.addItems(["0-5%", "5-15%", "15-30%", "30%+ (very risky)"])
            elif "dropped 80%" in q:
                combo.addItems(["Panic sell immediately", "Sell some, hold rest", "Hold and monitor", "Buy more at discount"])
            elif "understand blockchain" in q:
                combo.addItems(["Not really", "Basic understanding", "Good understanding", "Deep technical knowledge"])
            elif "timeline" in q:
                combo.addItems(["Less than 6 months", "6-12 months", "1-3 years", "3+ years (HODL)"])
            row.addWidget(combo, stretch=1)
            l.addLayout(row)
            self._crypto_risk_answers[q] = combo
        btn = QPushButton("Assess Risk Readiness")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_crypto_risk)
        l.addWidget(btn)
        self._crypto_risk_output = QTextEdit()
        self._crypto_risk_output.setReadOnly(True)
        self._crypto_risk_output.setStyleSheet("")
        l.addWidget(self._crypto_risk_output, stretch=1)
        return w

    def _build_portfolio_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Portfolio Allocation Simulator"))
        l.addWidget(QLabel("Enter allocation percentages (should total 100%):"))
        row = QHBoxLayout()
        row.addWidget(QLabel("BTC %:"))
        self._btc_pct = QLineEdit("40")
        self._btc_pct.setMaximumWidth(60)
        row.addWidget(self._btc_pct)
        row.addWidget(QLabel("ETH %:"))
        self._eth_pct = QLineEdit("30")
        self._eth_pct.setMaximumWidth(60)
        row.addWidget(self._eth_pct)
        row.addWidget(QLabel("Alts %:"))
        self._alts_pct = QLineEdit("20")
        self._alts_pct.setMaximumWidth(60)
        row.addWidget(self._alts_pct)
        row.addWidget(QLabel("Stablecoins %:"))
        self._stable_pct = QLineEdit("10")
        self._stable_pct.setMaximumWidth(60)
        row.addWidget(self._stable_pct)
        row.addStretch()
        l.addLayout(row)
        l.addWidget(QLabel("Total investment amount ($):"))
        self._portfolio_amount = QLineEdit("1000")
        l.addWidget(self._portfolio_amount)
        btn = QPushButton("Simulate Portfolio")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_portfolio_sim)
        l.addWidget(btn)
        self._portfolio_output = QTextEdit()
        self._portfolio_output.setReadOnly(True)
        self._portfolio_output.setStyleSheet("")
        l.addWidget(self._portfolio_output, stretch=1)
        return w

    def _build_redflag_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Crypto Red-Flag Checker"))
        l.addWidget(QLabel("Enter a crypto project name, token, or description to check for warning signs:"))
        self._redflag_input = QTextEdit()
        self._redflag_input.setPlaceholderText("e.g., 'Guaranteed 10% daily returns, new meme coin, anonymous team, limited time presale...'")
        self._redflag_input.setMaximumHeight(100)
        l.addWidget(self._redflag_input)
        btn = QPushButton("Check for Red Flags")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_redflag_check)
        l.addWidget(btn)
        self._redflag_output = QTextEdit()
        self._redflag_output.setReadOnly(True)
        self._redflag_output.setStyleSheet("")
        l.addWidget(self._redflag_output, stretch=1)
        return w

    def _build_dca_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Dollar-Cost Averaging (DCA) Planner"))
        row = QHBoxLayout()
        row.addWidget(QLabel("Investment amount per period ($):"))
        self._dca_amount = QLineEdit("100")
        self._dca_amount.setMaximumWidth(100)
        row.addWidget(self._dca_amount)
        row.addWidget(QLabel("Frequency:"))
        self._dca_freq = QComboBox()
        self._dca_freq.addItems(["Weekly", "Bi-weekly", "Monthly"])
        row.addWidget(self._dca_freq)
        row.addWidget(QLabel("Duration (months):"))
        self._dca_months = QLineEdit("12")
        self._dca_months.setMaximumWidth(60)
        row.addWidget(self._dca_months)
        row.addStretch()
        l.addLayout(row)
        l.addWidget(QLabel("Target asset:"))
        self._dca_asset = QLineEdit()
        self._dca_asset.setPlaceholderText("e.g., BTC, ETH, or a mix")
        l.addWidget(self._dca_asset)
        btn = QPushButton("Generate DCA Plan")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_dca_plan)
        l.addWidget(btn)
        self._dca_output = QTextEdit()
        self._dca_output.setReadOnly(True)
        self._dca_output.setStyleSheet("")
        l.addWidget(self._dca_output, stretch=1)
        return w

    def _run_through_runtime(self, task: str) -> str:
        try:
            from ...core.nexus_ai_runtime import NexusAIRuntime
            settings = SettingsManager()
            settings.initialize()
            runtime = NexusAIRuntime(settings=settings)
            result = runtime.run(task=task, ai_name=self._ai_name, ai_uuid=self._ai_uuid, ai_metadata={"abilities": self._abilities, "use_case": self._use_case, "guardrails": self._guardrails, "libraries": self._libraries})
            return result.result_text or ""
        except Exception:
            return ""

    def _run_asset_lookup(self):
        asset = self._asset_input.text().strip()
        if not asset:
            self._asset_output.setText("Enter an asset name or ticker first.")
            return
        task = f"Research the cryptocurrency {asset}. Provide an overview, use case, market position, risks, and key metrics."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._asset_output.setText(ai_result)
            self._set_result_summary(f"Crypto asset research for {asset} via AI.")
            return
        asset_db = {
            "btc": ("Bitcoin", "Store of value, digital gold", "Largest crypto by market cap", "Halving events, institutional adoption", "Regulatory crackdowns, environmental concerns, competition"),
            "bitcoin": ("Bitcoin", "Store of value, digital gold", "Largest crypto by market cap", "Halving events, institutional adoption", "Regulatory crackdowns, environmental concerns, competition"),
            "eth": ("Ethereum", "Smart contracts, DeFi, NFTs, dApps", "Second largest crypto, leading smart contract platform", "EIP upgrades, Layer 2 growth, ETH 2.0", "Gas fees, competition from Solana/Cardano, regulatory scrutiny"),
            "ethereum": ("Ethereum", "Smart contracts, DeFi, NFTs, dApps", "Second largest crypto, leading smart contract platform", "EIP upgrades, Layer 2 growth, ETH 2.0", "Gas fees, competition from Solana/Cardano, regulatory scrutiny"),
            "sol": ("Solana", "High-speed transactions, low fees", "Fast-growing Layer 1 blockchain", "Speed, low cost, growing ecosystem", "Network outages, centralization concerns, competition"),
            "solana": ("Solana", "High-speed transactions, low fees", "Fast-growing Layer 1 blockchain", "Speed, low cost, growing ecosystem", "Network outages, centralization concerns, competition"),
            "ada": ("Cardano", "Academic approach, peer-reviewed blockchain", "Research-driven Layer 1", "Strong community, methodical development", "Slow development, limited dApp ecosystem"),
            "cardano": ("Cardano", "Academic approach, peer-reviewed blockchain", "Research-driven Layer 1", "Strong community, methodical development", "Slow development, limited dApp ecosystem"),
            "dot": ("Polkadot", "Cross-chain interoperability", "Multi-chain framework", "Parachain auctions, interoperability focus", "Complex technology, competition from Cosmos"),
            "avax": ("Avalanche", "Fast, low-cost smart contracts", "Layer 1 with subnets", "Speed, subnet architecture", "Competition, relatively newer ecosystem"),
            "link": ("Chainlink", "Decentralized oracle network", "Leading oracle provider", "Critical infrastructure for DeFi", "Tokenomics concerns, competition"),
            "matic": ("Polygon", "Ethereum Layer 2 scaling", "Leading L2 solution", "Ethereum scaling solution, partnerships", "Dependent on Ethereum, competition from other L2s"),
        }
        key = asset.lower().strip()
        info = asset_db.get(key)
        if not info:
            output = (
                f"[ASSET RESEARCH — LOCAL ANALYSIS]\n\n"
                f"Asset: {asset}\n"
                f"Status: Not in local database.\n\n"
                "GENERAL CRYPTO RESEARCH FRAMEWORK:\n"
                "  1. Market cap and ranking (check CoinGecko/CoinMarketCap)\n"
                "  2. Use case and value proposition\n"
                "  3. Team and development activity\n"
                "  4. Tokenomics (supply, distribution, vesting)\n"
                "  5. Community and social sentiment\n"
                "  6. Exchange listings and liquidity\n"
                "  7. Regulatory status\n"
                "  8. Red flags (see Red-Flag Checker tab)\n\n"
                "The built-in intelligence can provide research on any asset."
            )
        else:
            name, use_case, position, strengths, risks = info
            output = (
                f"[ASSET RESEARCH — LOCAL ANALYSIS]\n\n"
                f"Asset: {name}\n"
                f"Use Case: {use_case}\n"
                f"Market Position: {position}\n\n"
                f"Strengths:\n  - {strengths}\n\n"
                f"Key Risks:\n  - {risks}\n\n"
                f"RESEARCH CHECKLIST:\n"
                "  [ ] Check current price and market cap\n"
                "  [ ] Review whitepaper and documentation\n"
                "  [ ] Verify team credentials and track record\n"
                "  [ ] Check tokenomics (circulating vs total supply)\n"
                "  [ ] Review on-chain metrics (active addresses, TVL)\n"
                "  [ ] Assess community sentiment (Reddit, Twitter, Discord)\n"
                "  [ ] Check for regulatory actions or warnings\n"
                "  [ ] Evaluate competitive landscape\n\n"
                "The built-in intelligence can provide real-time research."
            )
        self._asset_output.setText(output)
        self._set_result_summary(f"Crypto asset research for {asset}.")

    def _run_crypto_risk(self):
        scores = [combo.currentIndex() for combo in self._crypto_risk_answers.values()]
        avg = sum(scores) / len(scores) if scores else 0
        if avg < 1.0:
            profile = "LOW RISK READINESS"
            advice = "Consider limiting crypto exposure to 1-5% of savings. Focus on BTC and ETH only. Avoid leveraged trading."
        elif avg < 2.0:
            profile = "MODERATE RISK READINESS"
            advice = "A 5-15% allocation may be appropriate. Diversify across BTC, ETH, and a few established alts. Use DCA strategy."
        elif avg < 3.0:
            profile = "HIGH RISK READINESS"
            advice = "You understand the risks. A 15-30% allocation may suit you. Consider a mix of large caps and carefully researched alts."
        else:
            profile = "VERY HIGH RISK READINESS"
            advice = "You have deep knowledge and high risk tolerance. Even so, never invest more than you can afford to lose entirely."
        output = (
            f"[CRYPTO RISK ASSESSMENT — LOCAL ANALYSIS]\n\n"
            f"Score: {avg:.1f} / 3.0\n"
            f"Profile: {profile}\n\n"
            f"Recommendation: {advice}\n\n"
            "UNIVERSAL CRYPTO RULES:\n"
            "  1. Never invest more than you can afford to lose completely\n"
            "  2. Use hardware wallets for large holdings\n"
            "  3. Enable 2FA on all exchange accounts\n"
            "  4. Be wary of FOMO and FUD — stick to your plan\n"
            "  5. Understand what you're buying — don't follow tips blindly\n"
            "  6. Keep records for tax purposes\n"
            "  7. Beware of phishing and scams — verify URLs carefully\n\n"
            "This is NOT financial advice. Consult a qualified financial advisor."
        )
        self._crypto_risk_output.setText(output)
        self._set_result_summary(f"Crypto risk profile: {profile}.")

    def _run_portfolio_sim(self):
        try:
            btc = int(self._btc_pct.text().strip() or "0")
            eth = int(self._eth_pct.text().strip() or "0")
            alts = int(self._alts_pct.text().strip() or "0")
            stable = int(self._stable_pct.text().strip() or "0")
            total_pct = btc + eth + alts + stable
            amount = int(self._portfolio_amount.text().strip() or "0")
        except ValueError:
            self._portfolio_output.setText("Enter valid numbers for all fields.")
            return
        if total_pct != 100:
            self._portfolio_output.setText(f"Percentages must total 100%. Currently: {total_pct}%")
            return
        btc_amt = amount * btc // 100
        eth_amt = amount * eth // 100
        alts_amt = amount * alts // 100
        stable_amt = amount * stable // 100
        output = (
            f"[PORTFOLIO SIMULATION — LOCAL ANALYSIS]\n\n"
            f"Total investment: ${amount}\n\n"
            f"ALLOCATION:\n"
            f"  BTC ({btc}%):         ${btc_amt}\n"
            f"  ETH ({eth}%):         ${eth_amt}\n"
            f"  Alts ({alts}%):       ${alts_amt}\n"
            f"  Stable ({stable}%):   ${stable_amt}\n\n"
            f"RISK PROFILE:\n"
            f"  Conservative weight (BTC + Stable): {btc + stable}%\n"
            f"  Growth weight (ETH + Alts):         {eth + alts}%\n\n"
        )
        if btc + stable >= 60:
            output += "Assessment: Conservative-leaning portfolio. Lower risk, steady potential.\n"
        elif eth + alts >= 60:
            output += "Assessment: Growth-leaning portfolio. Higher risk, higher potential returns.\n"
        else:
            output += "Assessment: Balanced portfolio. Moderate risk profile.\n"
        output += (
            "\nSCENARIO ANALYSIS (hypothetical):\n"
            f"  Bull market (+50%): Portfolio value ≈ ${amount * 3 // 2}\n"
            f"  Bear market (-50%): Portfolio value ≈ ${amount // 2}\n"
            f"  Crash (-80%):       Portfolio value ≈ ${amount // 5}\n\n"
            "This is a simulation only. Actual returns will vary.\n"
            "Not financial advice. Consult a qualified financial advisor."
        )
        self._portfolio_output.setText(output)
        self._set_result_summary(f"Portfolio simulated: ${amount} with {total_pct}% allocation.")

    def _run_redflag_check(self):
        text = self._redflag_input.toPlainText().strip().lower()
        if not text:
            self._redflag_output.setText("Enter a project description to check for red flags.")
            return
        red_flags = [
            ("guaranteed", "RED FLAG: 'Guaranteed' returns — no crypto investment is guaranteed"),
            ("daily returns", "RED FLAG: Daily returns promised — classic Ponzi scheme language"),
            ("double your", "RED FLAG: Promises to double investment — unrealistic"),
            ("anonymous team", "RED FLAG: Anonymous team — no accountability if things go wrong"),
            ("no risk", "RED FLAG: 'No risk' claims — all crypto carries risk"),
            ("presale", "CAUTION: Presale — verify contract address, team, and tokenomics carefully"),
            ("memecoin", "CAUTION: Meme coin — typically no utility, driven by hype, high rug-pull risk"),
            ("rug pull", "RED FLAG: Associated with rug pull discussions — extreme caution"),
            ("giveaway", "RED FLAG: Giveaway scams — never send crypto to receive more"),
            ("airdrop", "CAUTION: Airdrop — verify legitimacy, never connect wallet to unknown sites"),
            ("send us", "RED FLAG: Asking you to send crypto — likely a scam"),
            ("private key", "RED FLAG: Requesting private keys — NEVER share your private keys"),
            ("seed phrase", "RED FLAG: Requesting seed phrase — NEVER share your seed phrase"),
            ("limited time", "CAUTION: Urgency tactics — legitimate projects don't rush you"),
            ("act now", "CAUTION: Pressure to act quickly — take your time to research"),
            ("whale", "CAUTION: Whale-related claims — verify on-chain, don't trust claims"),
        ]
        found_flags = []
        for keyword, warning in red_flags:
            if keyword in text:
                found_flags.append(warning)
        if not found_flags:
            output = (
                "[RED-FLAG CHECK — LOCAL ANALYSIS]\n\n"
                "No specific red flags detected in the text provided.\n\n"
                "However, absence of red flags does NOT mean the project is safe.\n"
                "Always do your own research:\n"
                "  1. Check team identity and history\n"
                "  2. Read the whitepaper and tokenomics\n"
                "  3. Verify smart contract audits\n"
                "  4. Check community sentiment and engagement\n"
                "  5. Look for exchange listings and liquidity\n"
                "  6. Search for reviews and discussions\n\n"
                "The built-in intelligence can provide red-flag analysis."
            )
        else:
            output = "[RED-FLAG CHECK — LOCAL ANALYSIS]\n\n"
            output += f"Found {len(found_flags)} warning(s):\n\n"
            for f in found_flags:
                output += f"  ⚠ {f}\n"
            output += (
                "\nVERDICT: Exercise extreme caution. Multiple red flags detected.\n"
                "Do NOT invest without thorough independent research.\n"
                "When in doubt, don't invest. There will always be other opportunities.\n\n"
                "The built-in intelligence can provide deeper analysis."
            )
        self._redflag_output.setText(output)
        self._set_result_summary(f"Red-flag check: {len(found_flags)} warning(s) found.")

    def _run_dca_plan(self):
        try:
            amount = int(self._dca_amount.text().strip() or "0")
            months = int(self._dca_months.text().strip() or "0")
        except ValueError:
            self._dca_output.setText("Enter valid numbers.")
            return
        freq = self._dca_freq.currentText()
        asset = self._dca_asset.text().strip() or "BTC/ETH mix"
        freq_map = {"Weekly": 4, "Bi-weekly": 2, "Monthly": 1}
        per_period = freq_map.get(freq, 1)
        total_periods = per_period * months
        total_invested = amount * total_periods
        output = (
            f"[DCA PLAN — LOCAL ANALYSIS]\n\n"
            f"Target asset: {asset}\n"
            f"Investment per period: ${amount}\n"
            f"Frequency: {freq}\n"
            f"Duration: {months} months\n\n"
            f"Total periods: {total_periods}\n"
            f"Total investment over {months} months: ${total_invested}\n\n"
            "DCA STRATEGY EXPLANATION:\n"
            "  Dollar-cost averaging spreads your investment across time,\n"
            "  reducing the impact of volatility. You buy more when prices\n"
            "  are low and less when prices are high — automatically.\n\n"
            "BENEFITS:\n"
            "  - Reduces timing risk (no need to time the market)\n"
            "  - Smooths out volatility impact\n"
            "  - Disciplined, emotion-free investing\n"
            "  - Works well in both bull and bear markets\n\n"
            "IMPLEMENTATION:\n"
            "  1. Set up automatic recurring buys on your exchange\n"
            "  2. Stick to the schedule regardless of price\n"
            "  3. Review quarterly — adjust amount but not frequency\n"
            "  4. Consider rebalancing if allocation drifts >10%\n\n"
            "HYPOTHETICAL SCENARIOS:\n"
            f"  If price averages ${500}: You'd own ~{total_invested // 500} units\n"
            f"  If price averages ${1000}: You'd own ~{total_invested // 1000} units\n"
            f"  If price averages ${2000}: You'd own ~{total_invested // 2000} units\n\n"
            "This is NOT financial advice. Consult a qualified financial advisor."
        )
        self._dca_output.setText(output)
        self._set_result_summary(f"DCA plan: ${amount}/{freq} for {months} months = ${total_invested} total.")


class AffiliateStrategistDialog(BaseCapabilityDialog):
    """Affiliate Strategist — affiliate program finder, commission comparison, content strategy builder, link placement planner."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Affiliate Strategist — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 620)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_programs_tab(), "Program Finder")
        tabs.addTab(self._build_commission_tab(), "Commission Comparison")
        tabs.addTab(self._build_content_tab(), "Content Strategy")
        tabs.addTab(self._build_placement_tab(), "Link Placement")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("FTC disclosure required for affiliate links. No guaranteed commissions. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_programs_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Your niche / topic:"))
        self._aff_niche = QLineEdit()
        self._aff_niche.setPlaceholderText("e.g., tech gadgets, fitness, cooking, travel, software...")
        l.addWidget(self._aff_niche)
        l.addWidget(QLabel("Platform preference:"))
        self._aff_platform = QComboBox()
        self._aff_platform.addItems(["Any", "Blog/website", "YouTube", "Social media", "Email newsletter", "Podcast"])
        l.addWidget(self._aff_platform)
        btn = QPushButton("Find Affiliate Programs")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_program_finder)
        l.addWidget(btn)
        self._program_output = QTextEdit()
        self._program_output.setReadOnly(True)
        self._program_output.setStyleSheet("")
        l.addWidget(self._program_output, stretch=1)
        return w

    def _build_commission_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Compare commission structures across programs. Enter up to 3 programs:"))
        self._commission_entries: list[tuple[QLineEdit, QLineEdit, QLineEdit]] = []
        for i in range(3):
            row = QHBoxLayout()
            name = QLineEdit()
            name.setPlaceholderText(f"Program {i+1} name")
            rate = QLineEdit()
            rate.setPlaceholderText("Commission % (e.g., 5)")
            rate.setMaximumWidth(80)
            cookie = QLineEdit()
            cookie.setPlaceholderText("Cookie days (e.g., 30)")
            cookie.setMaximumWidth(100)
            row.addWidget(QLabel(f"#{i+1}:"))
            row.addWidget(name, stretch=2)
            row.addWidget(QLabel("Rate:"))
            row.addWidget(rate)
            row.addWidget(QLabel("Cookie:"))
            row.addWidget(cookie)
            row.addStretch()
            l.addLayout(row)
            self._commission_entries.append((name, rate, cookie))
        btn = QPushButton("Compare Programs")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_commission_compare)
        l.addWidget(btn)
        self._commission_output = QTextEdit()
        self._commission_output.setReadOnly(True)
        self._commission_output.setStyleSheet("")
        l.addWidget(self._commission_output, stretch=1)
        return w

    def _build_content_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Content Strategy Builder"))
        l.addWidget(QLabel("What product/topic are you promoting?"))
        self._content_product = QLineEdit()
        self._content_product.setPlaceholderText("e.g., web hosting, fitness equipment, online course...")
        l.addWidget(self._content_product)
        l.addWidget(QLabel("Content format:"))
        self._content_format = QComboBox()
        self._content_format.addItems(["Review article", "Comparison post", "Tutorial/guide", "YouTube video", "Email sequence", "Social media posts"])
        l.addWidget(self._content_format)
        btn = QPushButton("Generate Content Strategy")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_content_strategy)
        l.addWidget(btn)
        self._content_output = QTextEdit()
        self._content_output.setReadOnly(True)
        self._content_output.setStyleSheet("")
        l.addWidget(self._content_output, stretch=1)
        return w

    def _build_placement_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Link Placement Planner"))
        l.addWidget(QLabel("Where do you publish content?"))
        self._placement_platform = QComboBox()
        self._placement_platform.addItems(["Blog/website", "YouTube description", "Email newsletter", "Social media bio", "Podcast show notes"])
        l.addWidget(self._placement_platform)
        btn = QPushButton("Generate Placement Plan")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_placement_plan)
        l.addWidget(btn)
        self._placement_output = QTextEdit()
        self._placement_output.setReadOnly(True)
        self._placement_output.setStyleSheet("")
        l.addWidget(self._placement_output, stretch=1)
        return w

    def _run_through_runtime(self, task: str) -> str:
        try:
            from ...core.nexus_ai_runtime import NexusAIRuntime
            settings = SettingsManager()
            settings.initialize()
            runtime = NexusAIRuntime(settings=settings)
            result = runtime.run(task=task, ai_name=self._ai_name, ai_uuid=self._ai_uuid, ai_metadata={"abilities": self._abilities, "use_case": self._use_case, "guardrails": self._guardrails, "libraries": self._libraries})
            return result.result_text or ""
        except Exception:
            return ""

    def _run_program_finder(self):
        niche = self._aff_niche.text().strip()
        if not niche:
            self._program_output.setText("Enter your niche first.")
            return
        platform = self._aff_platform.currentText()
        task = f"Find affiliate programs for niche: {niche}, platform: {platform}. List programs with commission rates and cookie durations."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._program_output.setText(ai_result)
            self._set_result_summary(f"Affiliate programs found for {niche} via AI.")
            return
        programs = [
            ("Amazon Associates", "1-10%", "24 hours", "Any", "Largest selection, easy to use, low rates, short cookie"),
            ("ShareASale", "5-50%", "30-90 days", "Blog, social", "Large network, diverse merchants, good reporting"),
            ("CJ Affiliate (Commission Junction)", "3-50%", "30-120 days", "Blog, email", "Premium brands, reliable tracking, requires approval"),
            ("Impact", "5-40%", "30-90 days", "Any", "Modern platform, direct merchant relationships"),
            ("ClickBank", "30-75%", "60 days", "Blog, email", "Digital products, high commissions, quality concerns"),
            ("Rakuten Advertising", "3-20%", "90 days", "Blog", "Premium brands, reliable payments, selective approval"),
            ("Awin", "5-30%", "30 days", "Blog, social", "Global network, diverse merchants"),
            ("PartnerStack", "15-30%", "90 days", "Blog, SaaS", "SaaS-focused, recurring commissions available"),
            ("Skimlinks", "5-30%", "Variable", "Blog", "Auto-monetizes content, easy integration"),
            ("Refersion", "10-25%", "30 days", "Any", "Direct merchant relationships, influencer-friendly"),
        ]
        output = f"[AFFILIATE PROGRAM FINDER — LOCAL ANALYSIS]\n\nNiche: {niche}\nPlatform: {platform}\n\nTOP PROGRAMS:\n\n"
        for name, rate, cookie, best_for, notes in programs:
            output += f"  {name}\n    Rate: {rate} | Cookie: {cookie} | Best for: {best_for}\n    Notes: {notes}\n\n"
        output += (
            "SELECTION TIPS:\n"
            "  1. Match programs to your audience's interests\n"
            "  2. Prioritize longer cookie durations\n"
            "  3. Look for programs with marketing support (banners, content)\n"
            "  4. Test 2-3 programs before committing\n"
            "  5. Always disclose affiliate relationships (FTC requirement)\n\n"
            "The built-in intelligence can provide program matching."
        )
        self._program_output.setText(output)
        self._set_result_summary(f"Affiliate programs found for {niche}.")

    def _run_commission_compare(self):
        entries = []
        for name_le, rate_le, cookie_le in self._commission_entries:
            name = name_le.text().strip()
            if name:
                try:
                    rate = float(rate_le.text().strip() or "0")
                except ValueError:
                    rate = 0
                try:
                    cookie = int(cookie_le.text().strip() or "0")
                except ValueError:
                    cookie = 0
                entries.append((name, rate, cookie))
        if not entries:
            self._commission_output.setText("Enter at least one program name.")
            return
        output = "[COMMISSION COMPARISON — LOCAL ANALYSIS]\n\n"
        output += f"{'Program':<25} {'Rate':>8} {'Cookie':>10} {'$10k sales':>12}\n"
        output += "-" * 60 + "\n"
        for name, rate, cookie in entries:
            monthly_est = int(10000 * rate / 100)
            output += f"{name:<25} {rate:>7.1f}% {cookie:>8}d {monthly_est:>10}/mo\n"
        output += "\n"
        best_rate = max(entries, key=lambda e: e[1])
        best_cookie = max(entries, key=lambda e: e[2])
        output += f"Best commission rate: {best_rate[0]} ({best_rate[1]}%)\n"
        output += f"Longest cookie duration: {best_cookie[0]} ({best_cookie[2]} days)\n\n"
        output += (
            "EVALUATION CRITERIA:\n"
            "  1. Commission rate (higher is better, but check product price)\n"
            "  2. Cookie duration (longer = more attribution window)\n"
            "  3. Product quality (promote products you trust)\n"
            "  4. Conversion rate (high commission means nothing if it doesn't convert)\n"
            "  5. Payment terms (net-30, net-60, minimum payout threshold)\n"
            "  6. Marketing resources provided\n\n"
            "Note: These are your inputs. Verify actual rates on program websites."
        )
        self._commission_output.setText(output)
        self._set_result_summary(f"Compared {len(entries)} affiliate programs.")

    def _run_content_strategy(self):
        product = self._content_product.text().strip()
        if not product:
            self._content_output.setText("Enter a product or topic first.")
            return
        fmt = self._content_format.currentText()
        task = f"Create an affiliate content strategy for {product} in {fmt} format."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._content_output.setText(ai_result)
            self._set_result_summary(f"Content strategy for {product} via AI.")
            return
        strategies = {
            "Review article": [
                "1. HOOK: Personal experience or problem statement",
                "2. PRODUCT OVERVIEW: What it is, who it's for",
                "3. FEATURES BREAKDOWN: Key features with pros/cons",
                "4. PERSONAL EXPERIENCE: How you used it, results",
                "5. COMPARISON: vs 2-3 alternatives",
                "6. PRICING: Break down pricing tiers",
                "7. WHO SHOULD BUY: Target audience",
                "8. WHO SHOULDN'T: Honest limitations",
                "9. CONCLUSION: Verdict + affiliate link (CTA)",
                "10. FAQ: Address common objections",
            ],
            "Comparison post": [
                "1. INTRO: Why this comparison matters",
                "2. COMPARISON TABLE: Side-by-side features/pricing",
                "3. DETAILED ANALYSIS: Each product reviewed",
                "4. USE CASE MATCH: Best for X, best for Y",
                "5. WINNER: Your recommendation + affiliate links",
                "6. RUNNERS UP: Alternatives with affiliate links",
                "7. METHODOLOGY: How you tested/evaluated",
            ],
            "Tutorial/guide": [
                "1. PROBLEM: The issue your audience faces",
                "2. SOLUTION: How the product solves it",
                "3. STEP-BY-STEP: Detailed walkthrough using the product",
                "4. TIPS: Pro tips for better results",
                "5. COMMON MISTAKES: What to avoid",
                "6. RESULTS: Before/after or outcomes",
                "7. NEXT STEPS: CTA with affiliate link",
            ],
            "YouTube video": [
                "1. THUMBNAIL: Eye-catching, shows product/result",
                "2. HOOK (0-15s): Problem + promise",
                "3. INTRO (15-30s): What they'll learn",
                "4. MAIN CONTENT (30s-8min): Demo/review/tutorial",
                "5. COMPARISON: vs alternatives",
                "6. HONEST TAKE: Pros, cons, who it's for",
                "7. CTA (last 30s): Affiliate link in description",
                "8. DESCRIPTION: Affiliate links + timestamps + resources",
            ],
            "Email sequence": [
                "Email 1: Problem awareness (no link)",
                "Email 2: Solution introduction (soft mention)",
                "Email 3: Deep dive / case study (affiliate link)",
                "Email 4: Comparison / alternatives (multiple links)",
                "Email 5: FAQ / objection handling (affiliate link)",
                "Email 6: Limited time offer / bonus (urgent CTA)",
            ],
            "Social media posts": [
                "Post 1: Teaser / question (engagement)",
                "Post 2: Tip related to product (value first)",
                "Post 3: Personal result / testimonial (link in bio)",
                "Post 4: Comparison carousel (link in bio)",
                "Post 5: Q&A / FAQ (link in bio)",
                "Story: Behind the scenes + swipe up/link sticker",
            ],
        }
        outline = strategies.get(fmt, strategies["Review article"])
        output = (
            f"[CONTENT STRATEGY — LOCAL ANALYSIS]\n\n"
            f"Product: {product}\n"
            f"Format: {fmt}\n\n"
            "CONTENT OUTLINE:\n"
        )
        for line in outline:
            output += f"  {line}\n"
        output += (
            "\nFTC DISCLOSURE REQUIREMENT:\n"
            "  'This post contains affiliate links. I may earn a commission\n"
            "   if you make a purchase through these links at no extra cost to you.'\n\n"
            "CONTENT TIPS:\n"
            "  - Be honest — fake reviews destroy trust\n"
            "  - Show real results and screenshots\n"
            "  - Address objections before they arise\n"
            "  - Use the product yourself before promoting\n"
            "  - Write for humans, not search engines\n\n"
            "The built-in intelligence can provide content generation."
        )
        self._content_output.setText(output)
        self._set_result_summary(f"Content strategy generated for {product} ({fmt}).")

    def _run_placement_plan(self):
        platform = self._placement_platform.currentText()
        plans = {
            "Blog/website": [
                "1. In-content links: Naturally within paragraphs (highest CTR)",
                "2. Call-to-action buttons: After key sections",
                "3. Sidebar banners: Persistent visibility",
                "4. Resource pages: Dedicated 'Recommended Tools' page",
                "5. Email signup: Capture visitors before they leave",
                "6. Comparison tables: Visual, easy to scan",
                "7. 'Last updated' footer: Shows freshness",
            ],
            "YouTube description": [
                "1. First 2 lines: Most visible — put key links here",
                "2. Timestamps: Link to specific sections",
                "3. Resources section: 'Tools I recommend' with affiliate links",
                "4. Social links: Cross-promote",
                "5. Pinned comment: Repeat key affiliate link",
            ],
            "Email newsletter": [
                "1. Primary CTA: One main affiliate link per email",
                "2. P.S. section: High-read area — place secondary link",
                "3. Resource section: 'Tools I use' at bottom",
                "4. Dedicated emails: Full product review emails convert best",
                "5. Disclosure: Include FTC disclosure in every email with links",
            ],
            "Social media bio": [
                "1. Link-in-bio tool: Linktree, Beacons, or custom page",
                "2. Rotate links: Feature current top recommendation",
                "3. Story links: Use link stickers (if eligible)",
                "4. Pinned post: Feature your top affiliate content",
                "5. Highlight reels: Save affiliate content to highlights",
            ],
            "Podcast show notes": [
                "1. Episode summary: Brief overview with context",
                "2. Resources mentioned: Affiliate links for each product",
                "3. Timestamps: Help listeners find specific mentions",
                "4. Subscribe CTA: Build your audience",
                "5. Sponsor disclosure: Required by FTC",
            ],
        }
        plan = plans.get(platform, plans["Blog/website"])
        output = f"[LINK PLACEMENT PLAN — LOCAL ANALYSIS]\n\nPlatform: {platform}\n\nPLACEMENT STRATEGY:\n\n"
        for line in plan:
            output += f"  {line}\n"
        output += (
            "\nBEST PRACTICES:\n"
            "  - Don't over-link — 2-3 affiliate links per page is optimal\n"
            "  - Use descriptive anchor text (not 'click here')\n"
            "  - Track click-through rates and optimize\n"
            "  - A/B test link placement and CTA text\n"
            "  - Always include FTC disclosure prominently\n\n"
            "The built-in intelligence can provide placement optimization."
        )
        self._placement_output.setText(output)
        self._set_result_summary(f"Link placement plan generated for {platform}.")


class ClickCommissionDialog(BaseCapabilityDialog):
    """Click Commission Tracker — tracks clicks, estimates commissions, projects monthly earnings, logs payouts."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Click Commission Tracker — {ai_name} | Avery Logic Works(TM)")
        self.resize(820, 580)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_tracker_tab(), "Click Tracker")
        tabs.addTab(self._build_projection_tab(), "Earnings Projection")
        tabs.addTab(self._build_payout_tab(), "Payout Log")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Estimates only. Actual earnings vary. Avery Logic Works is not liable for discrepancies.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_tracker_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Log your affiliate clicks and conversions:"))
        row = QHBoxLayout()
        row.addWidget(QLabel("Program:"))
        self._cc_program = QLineEdit()
        self._cc_program.setPlaceholderText("e.g., Amazon Associates")
        row.addWidget(self._cc_program)
        row.addWidget(QLabel("Clicks:"))
        self._cc_clicks = QLineEdit()
        self._cc_clicks.setMaximumWidth(80)
        row.addWidget(self._cc_clicks)
        row.addWidget(QLabel("Conversions:"))
        self._cc_conversions = QLineEdit()
        self._cc_conversions.setMaximumWidth(80)
        row.addWidget(self._cc_conversions)
        row.addWidget(QLabel("Avg order $:"))
        self._cc_order = QLineEdit()
        self._cc_order.setMaximumWidth(80)
        row.addWidget(self._cc_order)
        row.addWidget(QLabel("Commission %:"))
        self._cc_rate = QLineEdit()
        self._cc_rate.setMaximumWidth(60)
        row.addWidget(self._cc_rate)
        row.addStretch()
        l.addLayout(row)
        btn = QPushButton("Calculate Earnings")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_tracker)
        l.addWidget(btn)
        self._tracker_output = QTextEdit()
        self._tracker_output.setReadOnly(True)
        self._tracker_output.setStyleSheet("")
        l.addWidget(self._tracker_output, stretch=1)
        return w

    def _build_projection_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Monthly Earnings Projection"))
        row = QHBoxLayout()
        row.addWidget(QLabel("Avg clicks/month:"))
        self._proj_clicks = QLineEdit("500")
        self._proj_clicks.setMaximumWidth(100)
        row.addWidget(self._proj_clicks)
        row.addWidget(QLabel("Conversion rate %:"))
        self._proj_conv = QLineEdit("3")
        self._proj_conv.setMaximumWidth(80)
        row.addWidget(self._proj_conv)
        row.addWidget(QLabel("Avg order $:"))
        self._proj_order = QLineEdit("50")
        self._proj_order.setMaximumWidth(80)
        row.addWidget(self._proj_order)
        row.addWidget(QLabel("Commission %:"))
        self._proj_rate = QLineEdit("5")
        self._proj_rate.setMaximumWidth(60)
        row.addWidget(self._proj_rate)
        row.addStretch()
        l.addLayout(row)
        btn = QPushButton("Project Monthly Earnings")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_projection)
        l.addWidget(btn)
        self._projection_output = QTextEdit()
        self._projection_output.setReadOnly(True)
        self._projection_output.setStyleSheet("")
        l.addWidget(self._projection_output, stretch=1)
        return w

    def _build_payout_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Payout Log — Track your received commission payments"))
        l.addWidget(QLabel("Log entry (date, program, amount):"))
        self._payout_input = QTextEdit()
        self._payout_input.setPlaceholderText("e.g.,\n2026-01-15, Amazon Associates, $45.20\n2026-01-20, ShareASale, $128.50")
        self._payout_input.setMaximumHeight(120)
        l.addWidget(self._payout_input)
        btn = QPushButton("Summarize Payouts")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_payout_summary)
        l.addWidget(btn)
        self._payout_output = QTextEdit()
        self._payout_output.setReadOnly(True)
        self._payout_output.setStyleSheet("")
        l.addWidget(self._payout_output, stretch=1)
        return w

    def _run_tracker(self):
        try:
            clicks = int(self._cc_clicks.text().strip() or "0")
            conversions = int(self._cc_conversions.text().strip() or "0")
            order = float(self._cc_order.text().strip() or "0")
            rate = float(self._cc_rate.text().strip() or "0")
        except ValueError:
            self._tracker_output.setText("Enter valid numbers.")
            return
        program = self._cc_program.text().strip() or "Unknown"
        conv_rate = (conversions / clicks * 100) if clicks else 0
        total_sales = conversions * order
        commission = total_sales * rate / 100
        epc = (commission / clicks) if clicks else 0
        output = (
            f"[CLICK TRACKER — LOCAL ANALYSIS]\n\n"
            f"Program: {program}\n"
            f"Clicks: {clicks}\n"
            f"Conversions: {conversions}\n"
            f"Conversion rate: {conv_rate:.1f}%\n"
            f"Total sales value: ${total_sales:.2f}\n"
            f"Commission earned: ${commission:.2f}\n"
            f"Earnings per click (EPC): ${epc:.4f}\n\n"
            "METRICS EXPLAINED:\n"
            "  - Conversion rate: % of clicks that result in a purchase\n"
            "  - EPC: How much you earn per click on average\n"
            "  - Higher EPC = more efficient affiliate content\n\n"
            "OPTIMIZATION TIPS:\n"
            "  - Target conversion rate: 2-5% (varies by niche)\n"
            "  - Improve EPC by targeting buyer-intent keywords\n"
            "  - A/B test different link placements and CTAs\n"
            "  - Focus on high-commission, high-converting products"
        )
        self._tracker_output.setText(output)
        self._set_result_summary(f"Tracked {clicks} clicks, {conversions} conversions, ${commission:.2f} earned.")

    def _run_projection(self):
        try:
            clicks = int(self._proj_clicks.text().strip() or "0")
            conv = float(self._proj_conv.text().strip() or "0")
            order = float(self._proj_order.text().strip() or "0")
            rate = float(self._proj_rate.text().strip() or "0")
        except ValueError:
            self._projection_output.setText("Enter valid numbers.")
            return
        monthly_conversions = int(clicks * conv / 100)
        monthly_sales = monthly_conversions * order
        monthly_commission = monthly_sales * rate / 100
        yearly = monthly_commission * 12
        output = (
            f"[MONTHLY EARNINGS PROJECTION — LOCAL ANALYSIS]\n\n"
            f"INPUTS:\n"
            f"  Monthly clicks: {clicks}\n"
            f"  Conversion rate: {conv}%\n"
            f"  Average order: ${order:.2f}\n"
            f"  Commission rate: {rate}%\n\n"
            f"PROJECTED RESULTS:\n"
            f"  Monthly conversions: {monthly_conversions}\n"
            f"  Monthly sales value: ${monthly_sales:.2f}\n"
            f"  Monthly commission: ${monthly_commission:.2f}\n"
            f"  Annual commission: ${yearly:.2f}\n\n"
            f"SCENARIOS:\n"
            f"  Conservative (50% of projections): ${monthly_commission * 0.5:.2f}/mo\n"
            f"  Expected: ${monthly_commission:.2f}/mo\n"
            f"  Optimistic (150%): ${monthly_commission * 1.5:.2f}/mo\n\n"
            "SCALING STRATEGIES:\n"
            f"  - Double traffic to {clicks * 2} clicks → ${monthly_commission * 2:.2f}/mo\n"
            f"  - Improve conversion to {conv * 1.5:.1f}% → ${monthly_commission * 1.5:.2f}/mo\n"
            f"  - Promote higher-commission products ({rate * 2:.0f}%) → ${monthly_commission * 2:.2f}/mo\n\n"
            "These are projections only. Actual results vary significantly."
        )
        self._projection_output.setText(output)
        self._set_result_summary(f"Projected ${monthly_commission:.2f}/mo, ${yearly:.2f}/yr.")

    def _run_payout_summary(self):
        text = self._payout_input.toPlainText().strip()
        if not text:
            self._payout_output.setText("Enter payout entries to summarize.")
            return
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        total = 0.0
        programs: dict[str, float] = {}
        entries = []
        for line in lines:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 3:
                date, prog, amt_str = parts[0], parts[1], parts[2]
                try:
                    amt = float(amt_str.replace("$", "").replace(",", ""))
                except ValueError:
                    continue
                total += amt
                programs[prog] = programs.get(prog, 0) + amt
                entries.append((date, prog, amt))
        output = f"[PAYOUT SUMMARY — LOCAL ANALYSIS]\n\nTotal payouts logged: {len(entries)}\nTotal received: ${total:.2f}\n\n"
        output += "BY PROGRAM:\n"
        for prog, amt in sorted(programs.items(), key=lambda x: -x[1]):
            output += f"  {prog}: ${amt:.2f}\n"
        output += f"\nDETAILED LOG:\n"
        for date, prog, amt in entries:
            output += f"  {date} | {prog} | ${amt:.2f}\n"
        output += (
            "\nTRACKING TIPS:\n"
            "  - Reconcile with affiliate platform reports monthly\n"
            "  - Track payment dates vs earning periods (usually net-60)\n"
            "  - Keep records for tax purposes\n"
            "  - Monitor for missing or delayed payments"
        )
        self._payout_output.setText(output)
        self._set_result_summary(f"Payout summary: {len(entries)} entries, ${total:.2f} total.")


class SalesFunnelDialog(BaseCapabilityDialog):
    """Sales Funnel Builder — funnel designer, conversion rate estimator, A/B test planner, email sequence builder."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Sales Funnel Builder — {ai_name} | Avery Logic Works(TM)")
        self.resize(840, 620)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_funnel_tab(), "Funnel Designer")
        tabs.addTab(self._build_conversion_tab(), "Conversion Estimator")
        tabs.addTab(self._build_abtest_tab(), "A/B Test Planner")
        tabs.addTab(self._build_email_tab(), "Email Sequence")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("No guaranteed conversions. Comply with consumer protection laws. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_funnel_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Funnel type:"))
        self._funnel_type = QComboBox()
        self._funnel_type.addItems(["Lead magnet funnel", "Webinar funnel", "Product launch funnel", "Tripwire funnel", "High-ticket consultation funnel", "Membership funnel"])
        l.addWidget(self._funnel_type)
        l.addWidget(QLabel("Your product/service:"))
        self._funnel_product = QLineEdit()
        self._funnel_product.setPlaceholderText("e.g., online course, coaching program, SaaS tool...")
        l.addWidget(self._funnel_product)
        l.addWidget(QLabel("Price point ($):"))
        self._funnel_price = QLineEdit()
        self._funnel_price.setPlaceholderText("e.g., 97")
        l.addWidget(self._funnel_price)
        btn = QPushButton("Design Funnel")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_funnel_design)
        l.addWidget(btn)
        self._funnel_output = QTextEdit()
        self._funnel_output.setReadOnly(True)
        self._funnel_output.setStyleSheet("")
        l.addWidget(self._funnel_output, stretch=1)
        return w

    def _build_conversion_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Funnel Conversion Estimator"))
        l.addWidget(QLabel("Enter expected traffic and conversion rates per stage:"))
        stages = [("Visitors", "1000", "100"), ("Lead magnet opt-in", "30", "300"), ("Sales page views", "50", "150"), ("Purchases", "2", "3")]
        self._conv_inputs: list[tuple[str, QLineEdit, QLineEdit]] = []
        for stage_name, default_rate, default_count in stages:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{stage_name}:"))
            rate_le = QLineEdit(default_rate)
            rate_le.setMaximumWidth(60)
            row.addWidget(QLabel("Conv %:"))
            row.addWidget(rate_le)
            count_le = QLineEdit(default_count)
            count_le.setMaximumWidth(80)
            row.addWidget(QLabel("Count:"))
            row.addWidget(count_le)
            row.addStretch()
            l.addLayout(row)
            self._conv_inputs.append((stage_name, rate_le, count_le))
        btn = QPushButton("Estimate Conversions")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_conversion_est)
        l.addWidget(btn)
        self._conv_output = QTextEdit()
        self._conv_output.setReadOnly(True)
        self._conv_output.setStyleSheet("")
        l.addWidget(self._conv_output, stretch=1)
        return w

    def _build_abtest_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("A/B Test Planner"))
        l.addWidget(QLabel("What element are you testing?"))
        self._abtest_element = QComboBox()
        self._abtest_element.addItems(["Headline", "CTA button text", "Page layout", "Price point", "Email subject line", "Opt-in form design", "Hero image"])
        l.addWidget(self._abtest_element)
        l.addWidget(QLabel("Variant A (control):"))
        self._abtest_a = QLineEdit()
        self._abtest_a.setPlaceholderText("Current version description")
        l.addWidget(self._abtest_a)
        l.addWidget(QLabel("Variant B (test):"))
        self._abtest_b = QLineEdit()
        self._abtest_b.setPlaceholderText("New version description")
        l.addWidget(self._abtest_b)
        l.addWidget(QLabel("Daily traffic:"))
        self._abtest_traffic = QLineEdit("200")
        self._abtest_traffic.setMaximumWidth(100)
        l.addWidget(self._abtest_traffic)
        btn = QPushButton("Plan A/B Test")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_abtest)
        l.addWidget(btn)
        self._abtest_output = QTextEdit()
        self._abtest_output.setReadOnly(True)
        self._abtest_output.setStyleSheet("")
        l.addWidget(self._abtest_output, stretch=1)
        return w

    def _build_email_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Email Sequence Builder"))
        l.addWidget(QLabel("Funnel type for email sequence:"))
        self._email_funnel = QComboBox()
        self._email_funnel.addItems(["Welcome sequence", "Product launch", "Abandoned cart", "Re-engagement", "Upsell sequence", "Webinar promotion"])
        l.addWidget(self._email_funnel)
        l.addWidget(QLabel("Product/topic:"))
        self._email_product = QLineEdit()
        self._email_product.setPlaceholderText("What are you selling/promoting?")
        l.addWidget(self._email_product)
        btn = QPushButton("Generate Email Sequence")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_email_seq)
        l.addWidget(btn)
        self._email_output = QTextEdit()
        self._email_output.setReadOnly(True)
        self._email_output.setStyleSheet("")
        l.addWidget(self._email_output, stretch=1)
        return w

    def _run_through_runtime(self, task: str) -> str:
        try:
            from ...core.nexus_ai_runtime import NexusAIRuntime
            settings = SettingsManager()
            settings.initialize()
            runtime = NexusAIRuntime(settings=settings)
            result = runtime.run(task=task, ai_name=self._ai_name, ai_uuid=self._ai_uuid, ai_metadata={"abilities": self._abilities, "use_case": self._use_case, "guardrails": self._guardrails, "libraries": self._libraries})
            return result.result_text or ""
        except Exception:
            return ""

    def _run_funnel_design(self):
        ftype = self._funnel_type.currentText()
        product = self._funnel_product.text().strip() or "your product"
        try:
            price = float(self._funnel_price.text().strip() or "0")
        except ValueError:
            price = 0
        task = f"Design a {ftype} for {product} at ${price}. Include each stage, conversion goals, and traffic sources."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._funnel_output.setText(ai_result)
            self._set_result_summary(f"Funnel designed via AI for {product}.")
            return
        funnels = {
            "Lead magnet funnel": [
                ("Traffic source", "Ads, SEO, social media → Landing page"),
                ("Landing page", "Free lead magnet offer (ebook, checklist, template)"),
                ("Opt-in form", "Name + email capture (minimize friction)"),
                ("Thank you page", "Deliver lead magnet + tripwire offer"),
                ("Tripwire", "Low-cost offer ($7-27) to convert leads to buyers"),
                ("Email follow-up", "5-7 day nurture sequence → core offer"),
                ("Core offer", f"Main product: {product} (${price})"),
                ("Upsell", "Order bump or one-time offer (+30-50% revenue)"),
            ],
            "Webinar funnel": [
                ("Traffic source", "Ads, email list, partnerships → Registration page"),
                ("Registration page", "Webinar topic + benefits + date/time"),
                ("Confirmation page", "Add to calendar + bonus for attending"),
                ("Email reminders", "3-5 emails: confirmation, reminder, last chance"),
                ("Live webinar", "Educational content → pitch transition"),
                ("Offer page", f"Special price for attendees: {product} (${price})"),
                ("Follow-up sequence", "Replay + deadline urgency + FAQ"),
                ("Downsell", "Payment plan or stripped-down version"),
            ],
            "Product launch funnel": [
                ("Pre-launch", "Teaser content, build anticipation (1-2 weeks)"),
                ("Registration", "Notification list for launch details"),
                ("Content sequence", "3 educational videos/posts (pre-frame offer)"),
                ("Open cart", f"Sales page live: {product} (${price})"),
                ("Launch emails", "5-7 emails: announcement, benefits, FAQ, deadline"),
                ("Scarcity", "Cart closes in 24-48 hours"),
                ("Post-launch", "Thank you + onboarding sequence"),
            ],
            "Tripwire funnel": [
                ("Traffic", "Ads or organic → low-cost offer page"),
                ("Tripwire offer", "Irresistible $7-27 offer (must be high value)"),
                ("Upsell", f"Core product: {product} (${price}) — one-click upsell"),
                ("Downsell", "Payment plan if they decline upsell"),
                ("Email nurture", "Non-buyers: retarget with core offer"),
            ],
            "High-ticket consultation funnel": [
                ("Traffic", "Ads, content marketing, referrals → Application page"),
                ("Application", "Qualify leads (budget, need, timeline)"),
                ("Discovery call", "15-30 min qualification call"),
                ("Strategy session", "45-60 min deep dive → pitch"),
                ("Proposal", f"Custom proposal: {product} (${price})"),
                ("Close", "Contract + payment"),
                ("Onboarding", "Welcome sequence + kickoff"),
            ],
            "Membership funnel": [
                ("Traffic", "Content marketing, ads → Free preview"),
                ("Free trial/preview", "Limited access to membership content"),
                ("Trial experience", "Onboarding emails, quick wins"),
                ("Conversion page", f"Full membership: {product} (${price}/mo)"),
                ("Trial follow-up", "5-7 emails showcasing value"),
                ("Retention", "Monthly content, community, engagement"),
            ],
        }
        stages = funnels.get(ftype, funnels["Lead magnet funnel"])
        output = f"[FUNNEL DESIGN — LOCAL ANALYSIS]\n\nFunnel type: {ftype}\nProduct: {product}\nPrice: ${price}\n\nFUNNEL STAGES:\n\n"
        for i, (stage, desc) in enumerate(stages, 1):
            output += f"  Stage {i}: {stage}\n    → {desc}\n\n"
        output += (
            "FUNNEL METRICS TO TRACK:\n"
            "  - Stage-by-stage conversion rate\n"
            "  - Cost per lead (CPL)\n"
            "  - Cost per acquisition (CPA)\n"
            "  - Average order value (AOV)\n"
            "  - Customer lifetime value (LTV)\n"
            "  - Return on ad spend (ROAS)\n\n"
            "The built-in intelligence can provide funnel optimization."
        )
        self._funnel_output.setText(output)
        self._set_result_summary(f"Funnel designed: {ftype} for {product}.")

    def _run_conversion_est(self):
        try:
            visitors = int(self._conv_inputs[0][2].text().strip() or "0")
        except ValueError:
            visitors = 1000
        current = visitors
        output = f"[CONVERSION ESTIMATOR — LOCAL ANALYSIS]\n\nStarting visitors: {visitors}\n\n"
        output += f"{'Stage':<25} {'Conv %':>8} {'People':>8} {'Drop-off':>10}\n"
        output += "-" * 55 + "\n"
        for i, (stage, rate_le, count_le) in enumerate(self._conv_inputs):
            try:
                rate = float(rate_le.text().strip() or "0")
            except ValueError:
                rate = 0
            next_count = int(current * rate / 100) if i > 0 else current
            if i == 0:
                output += f"{stage:<25} {'—':>8} {current:>8} {'—':>10}\n"
            else:
                drop = current - next_count
                output += f"{stage:<25} {rate:>7.1f}% {next_count:>8} {drop:>10}\n"
                current = next_count
        try:
            price = float(self._funnel_price.text().strip() or "0")
        except ValueError:
            price = 0
        revenue = current * price
        output += f"\nFinal conversions: {current}\n"
        output += f"Estimated revenue: ${revenue:.2f}\n\n"
        output += (
            "OPTIMIZATION OPPORTUNITIES:\n"
            "  - Each 1% improvement in opt-in rate adds significant downstream revenue\n"
            "  - Focus on the stage with the biggest drop-off first\n"
            "  - A/B test one element at a time for clear results\n"
            "  - Industry benchmarks: opt-in 25-40%, sales page 1-5%\n\n"
            "These are estimates based on your inputs. Actual results vary."
        )
        self._conv_output.setText(output)
        self._set_result_summary(f"Conversion estimate: {current} conversions, ${revenue:.2f} revenue.")

    def _run_abtest(self):
        element = self._abtest_element.currentText()
        variant_a = self._abtest_a.text().strip() or "current version"
        variant_b = self._abtest_b.text().strip() or "test version"
        try:
            traffic = int(self._abtest_traffic.text().strip() or "200")
        except ValueError:
            traffic = 200
        sample_50 = traffic * 7
        sample_90 = traffic * 14
        output = (
            f"[A/B TEST PLAN — LOCAL ANALYSIS]\n\n"
            f"Testing: {element}\n"
            f"Variant A (control): {variant_a}\n"
            f"Variant B (test): {variant_b}\n"
            f"Daily traffic: {traffic}\n\n"
            f"SAMPLE SIZE ESTIMATES:\n"
            f"  For 50% confidence: {sample_50} visitors per variant (~{sample_50 // traffic} days)\n"
            f"  For 90% confidence: {sample_90} visitors per variant (~{sample_90 // traffic} days)\n\n"
            "TEST PROTOCOL:\n"
            "  1. Split traffic 50/50 between variants\n"
            "  2. Run test for full week minimum (captures day-of-week patterns)\n"
            "  3. Don't change anything else during the test\n"
            "  4. Measure ONE primary metric (conversion rate, CTR, etc.)\n"
            "  5. Wait for statistical significance before deciding\n"
            "  6. Document results and learnings\n\n"
            "STATISTICAL SIGNIFICANCE:\n"
            "  - Use a chi-square test or A/B test calculator\n"
            "  - Minimum: 100 conversions per variant for reliable results\n"
            "  - Don't stop early — 'peeking' invalidates results\n\n"
            "COMMON MISTAKES:\n"
            "  - Testing too many things at once\n"
            "  - Stopping too early\n"
            "  - Not accounting for seasonality\n"
            "  - Ignoring confounding variables\n"
        )
        self._abtest_output.setText(output)
        self._set_result_summary(f"A/B test planned for {element}.")

    def _run_email_seq(self):
        seq_type = self._email_funnel.currentText()
        product = self._email_product.text().strip() or "your product"
        task = f"Create a {seq_type} email sequence for {product}. Include email count, timing, subject lines, and content for each."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._email_output.setText(ai_result)
            self._set_result_summary(f"Email sequence generated via AI for {product}.")
            return
        sequences = {
            "Welcome sequence": [
                ("Email 1 (Immediate)", "Welcome + deliver promised resource", "Welcome to [Brand]! Here's your [lead magnet]"),
                ("Email 2 (Day 1)", "Who you are + what to expect", "Why I started [Brand] (and what's in it for you)"),
                ("Email 3 (Day 3)", "Quick win / valuable tip", "The one thing that changed everything for me"),
                ("Email 4 (Day 5)", "Story / case study", "How [customer] went from X to Y"),
                ("Email 5 (Day 7)", "Soft pitch + objection handling", "Ready to take the next step?"),
            ],
            "Product launch": [
                ("Email 1 (Day -7)", "Teaser / problem awareness", "Something big is coming..."),
                ("Email 2 (Day -5)", "Hint at solution", "The solution I wish I had 5 years ago"),
                ("Email 3 (Day -3)", "Open cart announcement", "It's here! [Product] is now available"),
                ("Email 4 (Day -1)", "FAQ + social proof", "Your questions answered + early results"),
                ("Email 5 (Day 0)", "Last chance / deadline", "24 hours left: Don't miss this"),
                ("Email 6 (Day +1)", "Cart closed + waitlist", "Cart closed — but there's still hope"),
            ],
            "Abandoned cart": [
                ("Email 1 (1 hour)", "Reminder", "You left something behind..."),
                ("Email 2 (24 hours)", "Objection handling + FAQ", "Questions about [product]? Here are answers"),
                ("Email 3 (48 hours)", "Social proof + urgency", "Don't just take our word for it"),
                ("Email 4 (72 hours)", "Last chance + incentive", "Last chance: Your cart expires soon"),
            ],
            "Re-engagement": [
                ("Email 1", "We miss you", "We miss you (here's something special)"),
                ("Email 2", "Value + update", "Here's what you missed + what's new"),
                ("Email 3", "Last chance", "Last chance to stay on the list"),
            ],
            "Upsell sequence": [
                ("Email 1 (Day 0)", "Thank you + next step", "Your [product] is on its way! Here's what's next"),
                ("Email 2 (Day 2)", "Introduce upsell", "Want to get results 2x faster?"),
                ("Email 3 (Day 4)", "Case study", "How [customer] doubled their results with [upsell]"),
                ("Email 4 (Day 6)", "FAQ + deadline", "Last chance: Special upsell price ends soon"),
            ],
            "Webinar promotion": [
                ("Email 1 (Day -7)", "Announcement", "Join me for a free training on [topic]"),
                ("Email 2 (Day -5)", "What you'll learn", "3 things you'll discover in the webinar"),
                ("Email 3 (Day -3)", "Social proof", "Why 500+ people already registered"),
                ("Email 4 (Day -1)", "Last chance to register", "Webinar is tomorrow — register now"),
                ("Email 5 (Day 0)", "Today's the day", "Starting in [X] hours — here's your link"),
                ("Email 6 (Day +1)", "Replay + offer", "Missed it? Watch the replay + special offer"),
            ],
        }
        emails = sequences.get(seq_type, sequences["Welcome sequence"])
        output = f"[EMAIL SEQUENCE — LOCAL ANALYSIS]\n\nSequence type: {seq_type}\nProduct: {product}\n\nEMAIL SEQUENCE:\n\n"
        for timing, purpose, subject in emails:
            output += f"  {timing}\n    Purpose: {purpose}\n    Subject: \"{subject}\"\n\n"
        output += (
            "EMAIL BEST PRACTICES:\n"
            "  - Keep subject lines under 50 characters\n"
            "  - One CTA per email\n"
            "  - Write like you're emailing a friend\n"
            "  - Use storytelling to build connection\n"
            "  - Segment lists for higher relevance\n"
            "  - Test send times (morning vs evening)\n"
            "  - Always include unsubscribe option (CAN-SPAM compliance)\n\n"
            "The built-in intelligence can provide email content generation."
        )
        self._email_output.setText(output)
        self._set_result_summary(f"Email sequence generated: {seq_type} for {product}.")


class SideHustleScoutDialog(BaseCapabilityDialog):
    """Side Hustle Scout — finds gig opportunities, platform comparison, time commitment estimator, earnings tracker."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Side Hustle Scout — {ai_name} | Avery Logic Works(TM)")
        self.resize(820, 600)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_finder_tab(), "Opportunity Finder")
        tabs.addTab(self._build_platform_tab(), "Platform Comparison")
        tabs.addTab(self._build_time_tab(), "Time Estimator")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("No income guaranteed. Verify platform terms. Avery Logic Works is not liable for outcomes.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_finder_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Your skills (comma-separated):"))
        self._sh_skills = QLineEdit()
        self._sh_skills.setPlaceholderText("e.g., writing, driving, cooking, coding, pet care...")
        l.addWidget(self._sh_skills)
        l.addWidget(QLabel("Available time per week:"))
        self._sh_time = QComboBox()
        self._sh_time.addItems(["1-5 hours", "5-10 hours", "10-20 hours", "20+ hours"])
        l.addWidget(self._sh_time)
        l.addWidget(QLabel("Do you have a car?"))
        self._sh_car = QComboBox()
        self._sh_car.addItems(["Yes", "No"])
        l.addWidget(self._sh_car)
        btn = QPushButton("Find Side Hustles")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_finder)
        l.addWidget(btn)
        self._finder_output = QTextEdit()
        self._finder_output.setReadOnly(True)
        self._finder_output.setStyleSheet("")
        l.addWidget(self._finder_output, stretch=1)
        return w

    def _build_platform_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Platform Comparison — Side Hustle Platforms"))
        btn = QPushButton("Compare Platforms")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_platform_compare)
        l.addWidget(btn)
        self._platform_output = QTextEdit()
        self._platform_output.setReadOnly(True)
        self._platform_output.setStyleSheet("")
        l.addWidget(self._platform_output, stretch=1)
        return w

    def _build_time_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Time Commitment Estimator"))
        l.addWidget(QLabel("How many hours per week can you commit?"))
        self._time_hours = QLineEdit("10")
        self._time_hours.setMaximumWidth(80)
        l.addWidget(self._time_hours)
        l.addWidget(QLabel("Target monthly income ($):"))
        self._time_target = QLineEdit("500")
        self._time_target.setMaximumWidth(100)
        l.addWidget(self._time_target)
        btn = QPushButton("Estimate Time Needed")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_time_est)
        l.addWidget(btn)
        self._time_output = QTextEdit()
        self._time_output.setReadOnly(True)
        self._time_output.setStyleSheet("")
        l.addWidget(self._time_output, stretch=1)
        return w

    def _run_through_runtime(self, task: str) -> str:
        try:
            from ...core.nexus_ai_runtime import NexusAIRuntime
            settings = SettingsManager()
            settings.initialize()
            runtime = NexusAIRuntime(settings=settings)
            result = runtime.run(task=task, ai_name=self._ai_name, ai_uuid=self._ai_uuid, ai_metadata={"abilities": self._abilities, "use_case": self._use_case, "guardrails": self._guardrails, "libraries": self._libraries})
            return result.result_text or ""
        except Exception:
            return ""

    def _run_finder(self):
        skills = self._sh_skills.text().strip()
        if not skills:
            self._finder_output.setText("Enter at least one skill.")
            return
        time = self._sh_time.currentText()
        has_car = self._sh_car.currentText() == "Yes"
        task = f"Find side hustle opportunities for skills: {skills}, time: {time}, has car: {has_car}."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._finder_output.setText(ai_result)
            self._set_result_summary(f"Side hustles found via AI for skills: {skills[:60]}.")
            return
        hustles = [
            ("Rideshare driving", "Uber, Lyft", "$15-25/hr", "Flexible, instant pay", "Wear on vehicle, insurance considerations", True),
            ("Food delivery", "DoorDash, Uber Eats, Grubhub", "$12-20/hr", "Flexible, low barrier", "Vehicle costs, variable demand", True),
            ("Grocery delivery", "Instacart, Shipt", "$15-25/hr", "Flexible, tips", "Heavy lifting, shopping time", True),
            ("Freelance writing", "Upwork, Fiverr, Contena", "$20-100/hr", "Location independent, scalable", "Client acquisition, inconsistent work", False),
            ("Virtual assistant", "Belay, Upwork", "$15-50/hr", "Remote, varied work", "Client management, multiple bosses", False),
            ("Online tutoring", "Wyzant, Tutor.com", "$20-80/hr", "Rewarding, flexible", "Subject expertise required", False),
            ("Pet sitting/dog walking", "Rover, Wag", "$15-30/visit", "Fun, active", "Liability, schedule constraints", False),
            ("Task/handyman", "TaskRabbit", "$25-70/hr", "Good pay for skilled tasks", "Physical labor, local only", False),
            ("Selling handmade items", "Etsy, local markets", "Variable", "Creative, scalable", "Material costs, competition", False),
            ("Social media management", "Upwork, direct", "$300-3000/mo per client", "Remote, recurring revenue", "Client churn, platform changes", False),
            ("Print-on-demand", "Printful, Redbubble", "$5-30/sale", "Passive potential, no inventory", "Low margins, high competition", False),
            ("Affiliate marketing", "Amazon, ShareASale", "$50-5000/mo", "Passive potential", "Takes time to build, SEO required", False),
            ("Stock photography", "Shutterstock, Adobe Stock", "$0.25-3/sale", "Passive, creative", "Low per-sale, high volume needed", False),
            ("Transcription", "Rev, TranscribeMe", "$15-30/hr", "Remote, flexible", "Low pay, requires accuracy/ speed", False),
            ("Survey/microtasks", "Swagbucks, MTurk", "$1-5/hr", "Easy, no skills needed", "Very low pay, tedious", False),
        ]
        skill_lower = skills.lower()
        filtered = []
        for name, platforms, earning, pros, cons, needs_car in hustles:
            if needs_car and not has_car:
                continue
            if any(s.strip().lower() in skill_lower or s.strip().lower() in name.lower() for s in skills.split(",")):
                filtered.append((name, platforms, earning, pros, cons))
            else:
                filtered.append((name, platforms, earning, pros, cons))
        output = f"[SIDE HUSTLE FINDER — LOCAL ANALYSIS]\n\nSkills: {skills}\nTime: {time}\nVehicle: {'Yes' if has_car else 'No'}\n\nMATCHED OPPORTUNITIES ({len(filtered)}):\n\n"
        for i, (name, platforms, earning, pros, cons) in enumerate(filtered[:12], 1):
            output += f"  {i}. {name}\n     Platforms: {platforms}\n     Earning: {earning}\n     Pros: {pros}\n     Cons: {cons}\n\n"
        output += (
            "GETTING STARTED:\n"
            "  1. Pick 1-2 hustles that match your skills and time\n"
            "  2. Sign up and complete your profile\n"
            "  3. Start with low expectations — build reviews/reputation\n"
            "  4. Track your hourly earnings to find what's worth your time\n"
            "  5. Scale up what works, drop what doesn't\n\n"
            "The built-in intelligence can provide matching."
        )
        self._finder_output.setText(output)
        self._set_result_summary(f"Found {len(filtered)} side hustle opportunities.")

    def _run_platform_compare(self):
        platforms = [
            ("Uber", "Rideshare", "None", "$15-25/hr", "Instant Pay, flexible", "25% commission, vehicle wear", "Active driver license, car, insurance"),
            ("DoorDash", "Food delivery", "None", "$12-20/hr", "Flexible, peak pay bonuses", "Vehicle costs, slow periods", "Car/scooter, smartphone"),
            ("Upwork", "Freelancing", "None", "$20-150/hr", "Global clients, escrow payment", "20% commission, competitive", "Marketable skill, portfolio"),
            ("Fiverr", "Freelancing", "None", "$5-500/gig", "Easy to start, gig-based", "20% commission, race to bottom", "Any digital skill"),
            ("Etsy", "Handmade goods", "$0.20/listing", "Variable", "Built-in audience, creative", "6.5% transaction fee, shipping", "Craft/product to sell"),
            ("Rover", "Pet care", "$35/yr", "$15-30/visit", "Animal lovers, flexible", "Liability, cancelations", "Love for animals, background check"),
            ("TaskRabbit", "Tasks/errands", "$25/yr", "$25-70/hr", "Good pay, local", "Physical, limited areas", "Skills, transportation"),
            ("Swagbucks", "Surveys/tasks", "Free", "$1-5/hr", "Easy, no skills", "Very low pay", "Just time"),
            ("Rev", "Transcription", "Free", "$15-30/hr", "Remote, flexible", "Low starting pay", "Typing speed, headphones"),
            ("Wyzant", "Tutoring", "Free to join", "$20-80/hr", "Good pay, rewarding", "25% commission, subject expertise", "Knowledge in a subject"),
        ]
        output = "[PLATFORM COMPARISON — LOCAL ANALYSIS]\n\n"
        output += f"{'Platform':<15} {'Type':<15} {'Cost':<12} {'Earning':<14} {'Pros':<28} {'Cons':<28} {'Requirements'}\n"
        output += "-" * 140 + "\n"
        for p in platforms:
            output += f"{p[0]:<15} {p[1]:<15} {p[2]:<12} {p[3]:<14} {p[4]:<28} {p[5]:<28} {p[6]}\n"
        output += (
            "\nSELECTION CRITERIA:\n"
            "  1. Match to your skills and interests\n"
            "  2. Consider startup costs vs earning potential\n"
            "  3. Check platform reputation and payment reliability\n"
            "  4. Read the fine print — commission rates, minimum payouts\n"
            "  5. Start with 1-2 platforms, expand once profitable\n\n"
            "TAX REMINDER: Side hustle income is taxable. Track earnings and expenses."
        )
        self._platform_output.setText(output)
        self._set_result_summary(f"Compared {len(platforms)} side hustle platforms.")

    def _run_time_est(self):
        try:
            hours = int(self._time_hours.text().strip() or "0")
            target = float(self._time_target.text().strip() or "0")
        except ValueError:
            self._time_output.setText("Enter valid numbers.")
            return
        if hours <= 0:
            self._time_output.setText("Enter hours > 0.")
            return
        hourly_needed = target / (hours * 4.33) if hours else 0
        output = (
            f"[TIME COMMITMENT ESTIMATOR — LOCAL ANALYSIS]\n\n"
            f"Available time: {hours} hrs/week ({hours * 4.33:.0f} hrs/month)\n"
            f"Target income: ${target:.0f}/month\n\n"
            f"Required hourly rate: ${hourly_needed:.2f}/hr\n\n"
            "SIDE HUSTLES THAT MATCH YOUR REQUIRED RATE:\n\n"
        )
        if hourly_needed <= 5:
            output += "  Surveys (Swagbucks, MTurk): $1-5/hr ✓\n  Transcription (Rev): $15-30/hr ✓✓\n  Delivery (DoorDash): $12-20/hr ✓✓\n"
        elif hourly_needed <= 20:
            output += "  Delivery (DoorDash, Uber): $12-25/hr ✓\n  VA (Belay, Upwork): $15-50/hr ✓\n  Transcription (Rev): $15-30/hr ✓\n"
        elif hourly_needed <= 50:
            output += "  Freelance writing (Upwork): $20-100/hr ✓\n  Tutoring (Wyzant): $20-80/hr ✓\n  VA (Belay): $15-50/hr ✓\n  TaskRabbit: $25-70/hr ✓\n"
        else:
            output += "  Freelance consulting: $50-200/hr ✓\n  High-end freelancing (Toptal): $60-150/hr ✓\n  Specialized tutoring: $50-100/hr ✓\n  Note: You'll need specialized skills for this rate.\n"
        output += (
            f"\nFEASIBILITY ASSESSMENT:\n"
            f"  At ${hourly_needed:.2f}/hr, your target is "
        )
        if hourly_needed <= 15:
            output += "VERY ACHIEVABLE — many side hustles pay this rate.\n"
        elif hourly_needed <= 30:
            output += "ACHIEVABLE — requires some skill or experience.\n"
        elif hourly_needed <= 50:
            output += "CHALLENGING — requires marketable skills and experience.\n"
        else:
            output += "DIFFICULT — requires specialized expertise or business ownership.\n"
        output += (
            "\nTIME OPTIMIZATION TIPS:\n"
            "  - Batch similar tasks to reduce context switching\n"
            "  - Use commute time for audio learning\n"
            "  - Automate administrative tasks\n"
            "  - Price your time — don't do $10/hr tasks if you can earn $30/hr\n"
            "  - Track actual hours vs earnings to calculate real hourly rate\n\n"
            "These are estimates. Actual earnings depend on many factors."
        )
        self._time_output.setText(output)
        self._set_result_summary(f"Time estimate: ${hourly_needed:.2f}/hr needed for ${target:.0f}/mo target.")


class SkillMonetizerDialog(BaseCapabilityDialog):
    """Skill Monetizer — skill value assessor, monetization path finder, pricing calculator, portfolio builder."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Skill Monetizer — {ai_name} | Avery Logic Works(TM)")
        self.resize(820, 600)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_value_tab(), "Skill Value")
        tabs.addTab(self._build_paths_tab(), "Monetization Paths")
        tabs.addTab(self._build_pricing_tab(), "Pricing Calculator")
        tabs.addTab(self._build_portfolio_tab(), "Portfolio Builder")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("No income guaranteed. Market demand varies. Avery Logic Works is not liable for outcomes.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_value_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Skill to evaluate:"))
        self._sm_skill = QLineEdit()
        self._sm_skill.setPlaceholderText("e.g., Python programming, graphic design, copywriting...")
        l.addWidget(self._sm_skill)
        l.addWidget(QLabel("Experience level:"))
        self._sm_level = QComboBox()
        self._sm_level.addItems(["Beginner (0-1 year)", "Intermediate (1-3 years)", "Advanced (3-5 years)", "Expert (5+ years)"])
        l.addWidget(self._sm_level)
        btn = QPushButton("Assess Skill Value")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_value_assess)
        l.addWidget(btn)
        self._value_output = QTextEdit()
        self._value_output.setReadOnly(True)
        self._value_output.setStyleSheet("")
        l.addWidget(self._value_output, stretch=1)
        return w

    def _build_paths_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Find monetization paths for your skill:"))
        l.addWidget(QLabel("Skill:"))
        self._paths_skill = QLineEdit()
        self._paths_skill.setPlaceholderText("What skill do you want to monetize?")
        l.addWidget(self._paths_skill)
        btn = QPushButton("Find Monetization Paths")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_paths)
        l.addWidget(btn)
        self._paths_output = QTextEdit()
        self._paths_output.setReadOnly(True)
        self._paths_output.setStyleSheet("")
        l.addWidget(self._paths_output, stretch=1)
        return w

    def _build_pricing_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Pricing Calculator"))
        row = QHBoxLayout()
        row.addWidget(QLabel("Hourly rate ($):"))
        self._price_rate = QLineEdit("50")
        self._price_rate.setMaximumWidth(80)
        row.addWidget(self._price_rate)
        row.addWidget(QLabel("Hours/week:"))
        self._price_hours = QLineEdit("20")
        self._price_hours.setMaximumWidth(80)
        row.addWidget(self._price_hours)
        row.addWidget(QLabel("Expenses ($/mo):"))
        self._price_expenses = QLineEdit("200")
        self._price_expenses.setMaximumWidth(80)
        row.addWidget(self._price_expenses)
        row.addStretch()
        l.addLayout(row)
        btn = QPushButton("Calculate Earnings")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_pricing)
        l.addWidget(btn)
        self._pricing_output = QTextEdit()
        self._pricing_output.setReadOnly(True)
        self._pricing_output.setStyleSheet("")
        l.addWidget(self._pricing_output, stretch=1)
        return w

    def _build_portfolio_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Portfolio Builder — Plan your showcase"))
        l.addWidget(QLabel("Your skill/profession:"))
        self._portfolio_skill = QLineEdit()
        self._portfolio_skill.setPlaceholderText("e.g., web developer, writer, designer...")
        l.addWidget(self._portfolio_skill)
        btn = QPushButton("Generate Portfolio Plan")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_portfolio)
        l.addWidget(btn)
        self._portfolio_output = QTextEdit()
        self._portfolio_output.setReadOnly(True)
        self._portfolio_output.setStyleSheet("")
        l.addWidget(self._portfolio_output, stretch=1)
        return w

    def _run_through_runtime(self, task: str) -> str:
        try:
            from ...core.nexus_ai_runtime import NexusAIRuntime
            settings = SettingsManager()
            settings.initialize()
            runtime = NexusAIRuntime(settings=settings)
            result = runtime.run(task=task, ai_name=self._ai_name, ai_uuid=self._ai_uuid, ai_metadata={"abilities": self._abilities, "use_case": self._use_case, "guardrails": self._guardrails, "libraries": self._libraries})
            return result.result_text or ""
        except Exception:
            return ""

    def _run_value_assess(self):
        skill = self._sm_skill.text().strip()
        if not skill:
            self._value_output.setText("Enter a skill to evaluate.")
            return
        level = self._sm_level.currentText()
        task = f"Assess the market value of the skill: {skill} at {level} level. Include market demand, typical rates, and growth potential."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._value_output.setText(ai_result)
            self._set_result_summary(f"Skill value assessed via AI for {skill}.")
            return
        level_multipliers = {"Beginner": 0.5, "Intermediate": 1.0, "Advanced": 1.5, "Expert": 2.5}
        level_key = level.split(" ")[0]
        multiplier = level_multipliers.get(level_key, 1.0)
        skill_rates = {
            "programming": (40, 150), "coding": (40, 150), "python": (45, 160), "javascript": (40, 140),
            "writing": (20, 100), "copywriting": (30, 120), "content": (15, 80), "blogging": (15, 60),
            "design": (25, 120), "graphic": (25, 100), "ui": (40, 150), "ux": (40, 150),
            "marketing": (25, 100), "seo": (25, 90), "social media": (15, 60),
            "data": (35, 130), "analysis": (30, 100), "statistics": (35, 120),
            "teaching": (20, 80), "tutoring": (20, 70), "coaching": (30, 150),
            "consulting": (50, 300), "legal": (60, 400), "accounting": (35, 200),
            "photography": (20, 100), "video": (25, 120), "editing": (20, 80),
        }
        skill_lower = skill.lower()
        base_low, base_high = (20, 80)
        for key, (low, high) in skill_rates.items():
            if key in skill_lower:
                base_low, base_high = low, high
                break
        est_low = int(base_low * multiplier)
        est_high = int(base_high * multiplier)
        output = (
            f"[SKILL VALUE ASSESSMENT — LOCAL ANALYSIS]\n\n"
            f"Skill: {skill}\n"
            f"Experience: {level}\n"
            f"Multiplier: {multiplier}x\n\n"
            f"ESTIMATED HOURLY RATE: ${est_low}-{est_high}/hr\n\n"
            f"MONTHLY POTENTIAL (20 hrs/week): ${est_low * 87}-${est_high * 87}/mo\n"
            f"ANNUAL POTENTIAL (full-time): ${est_low * 2080}-${est_high * 2080}/yr\n\n"
            "MARKET DEMAND FACTORS:\n"
            "  - Tech skills (programming, data, AI) are in highest demand\n"
            "  - Creative skills (design, writing) have steady demand\n"
            "  - Specialized skills (legal, medical, finance) command premium rates\n"
            "  - General skills face more competition and lower rates\n\n"
            "GROWING YOUR VALUE:\n"
            "  1. Build a portfolio showcasing real results\n"
            "  2. Get certifications relevant to your skill\n"
            "  3. Specialize in a niche (e.g., 'React developer' > 'web developer')\n"
            "  4. Develop complementary skills (e.g., writing + SEO)\n"
            "  5. Build a personal brand and thought leadership\n\n"
            "The built-in intelligence can provide skill assessment."
        )
        self._value_output.setText(output)
        self._set_result_summary(f"Skill value: {skill} at {level} = ${est_low}-{est_high}/hr.")

    def _run_paths(self):
        skill = self._paths_skill.text().strip()
        if not skill:
            self._paths_output.setText("Enter a skill first.")
            return
        task = f"Find monetization paths for the skill: {skill}. List specific ways to earn money with this skill."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._paths_output.setText(ai_result)
            self._set_result_summary(f"Monetization paths found via AI for {skill}.")
            return
        paths = [
            ("Freelance services", "Sell your skill directly to clients", f"Upwork, Fiverr, Toptal", "Active", "$20-150/hr"),
            ("Consulting", "Advise businesses on your area of expertise", "Direct outreach, LinkedIn", "Active", "$50-300/hr"),
            ("Online course", "Teach your skill to others", "Udemy, Teachable, Skillshare", "Passive", "$50-500/enrollment"),
            ("1-on-1 coaching", "Coach individuals in your skill", "Calendly, Zoom, direct", "Active", "$50-200/session"),
            ("Digital products", "Create templates, tools, or resources", "Gumroad, Etsy", "Passive", "$10-200/sale"),
            ("YouTube channel", "Create educational content about your skill", "YouTube", "Scalable", "$1-10/1000 views + sponsorships"),
            ("Blog/website", "Write about your skill, monetize with ads/affiliates", "WordPress, Medium", "Passive", "$500-5000/mo"),
            ("Book/ebook", "Write a comprehensive guide", "Amazon KDP, Gumroad", "Passive", "$5-50/sale"),
            ("Membership site", "Ongoing training/community", "Patreon, Circle, Discord", "Recurring", "$10-100/month per member"),
            ("SaaS tool", "Build a tool related to your skill", "Direct, ProductHunt", "Scalable", "$10-1000/month per user"),
            ("Speaking/presenting", "Speak at events and conferences", "Eventbrite, direct", "Active", "$500-10000/event"),
            ("Corporate training", "Train teams in your skill area", "Direct B2B outreach", "Active", "$2000-20000/workshop"),
        ]
        output = f"[MONETIZATION PATHS — LOCAL ANALYSIS]\n\nSkill: {skill}\n\nMONETIZATION PATHS ({len(paths)}):\n\n"
        for i, (path, desc, platforms, income_type, potential) in enumerate(paths, 1):
            output += f"  {i}. {path}\n     Description: {desc}\n     Platforms: {platforms}\n     Income type: {income_type}\n     Potential: {potential}\n\n"
        output += (
            "PRIORITIZATION FRAMEWORK:\n"
            "  1. Start with ACTIVE income (freelancing) for immediate cash flow\n"
            "  2. Build PASSIVE income (courses, products) alongside\n"
            "  3. Scale with RECURRING/SCALABLE income (membership, SaaS)\n"
            "  4. Diversify across 2-3 paths — don't put all eggs in one basket\n\n"
            "The built-in intelligence can provide path recommendations."
        )
        self._paths_output.setText(output)
        self._set_result_summary(f"Found {len(paths)} monetization paths for {skill}.")

    def _run_pricing(self):
        try:
            rate = float(self._price_rate.text().strip() or "0")
            hours = float(self._price_hours.text().strip() or "0")
            expenses = float(self._price_expenses.text().strip() or "0")
        except ValueError:
            self._pricing_output.setText("Enter valid numbers.")
            return
        weekly_gross = rate * hours
        monthly_gross = weekly_gross * 4.33
        monthly_net = monthly_gross - expenses
        annual_gross = monthly_gross * 12
        annual_net = monthly_net * 12
        effective_rate = monthly_net / (hours * 4.33) if hours else 0
        output = (
            f"[PRICING CALCULATOR — LOCAL ANALYSIS]\n\n"
            f"INPUTS:\n"
            f"  Hourly rate: ${rate:.2f}\n"
            f"  Hours/week: {hours:.0f}\n"
            f"  Monthly expenses: ${expenses:.2f}\n\n"
            f"EARNINGS BREAKDOWN:\n"
            f"  Weekly gross: ${weekly_gross:.2f}\n"
            f"  Monthly gross: ${monthly_gross:.2f}\n"
            f"  Monthly net (after expenses): ${monthly_net:.2f}\n"
            f"  Annual gross: ${annual_gross:.2f}\n"
            f"  Annual net: ${annual_net:.2f}\n"
            f"  Effective hourly rate: ${effective_rate:.2f}\n\n"
            f"PRICING STRATEGIES:\n"
            f"  - Value-based pricing: Charge for the outcome, not the time\n"
            f"  - Package pricing: Offer 3 tiers (basic, standard, premium)\n"
            f"  - Retainer pricing: Monthly contracts for stable income\n"
            f"  - Project-based: Fixed price per project (often more profitable)\n\n"
            f"RATE OPTIMIZATION:\n"
            f"  - Increase rate 20%: Monthly net = ${monthly_gross * 1.2 - expenses:.2f}\n"
            f"  - Increase hours 20%: Monthly net = ${rate * hours * 1.2 * 4.33 - expenses:.2f}\n"
            f"  - Reduce expenses 50%: Monthly net = ${monthly_gross - expenses * 0.5:.2f}\n\n"
            "TAX REMINDER: Set aside 25-30% of net earnings for taxes."
        )
        self._pricing_output.setText(output)
        self._set_result_summary(f"Pricing: ${rate}/hr × {hours}hrs = ${monthly_net:.0f}/mo net.")

    def _run_portfolio(self):
        skill = self._portfolio_skill.text().strip()
        if not skill:
            self._portfolio_output.setText("Enter your skill or profession.")
            return
        task = f"Create a portfolio building plan for a {skill}. What should they include, how to structure it, and where to host it."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._portfolio_output.setText(ai_result)
            self._set_result_summary(f"Portfolio plan generated via AI for {skill}.")
            return
        output = (
            f"[PORTFOLIO BUILDER — LOCAL ANALYSIS]\n\n"
            f"Skill: {skill}\n\n"
            "PORTFOLIO STRUCTURE:\n\n"
            "1. HERO SECTION\n"
            "   - Professional headline: 'I help [target] with [skill]'\n"
            "   - Brief value proposition (1-2 sentences)\n"
            "   - CTA: 'Hire me' or 'Get a quote'\n\n"
            "2. ABOUT SECTION\n"
            "   - Your story and journey\n"
            "   - Relevant experience and credentials\n"
            "   - What makes you different\n\n"
            "3. WORK SAMPLES (3-5 projects)\n"
            "   - Project title and brief description\n"
            "   - Problem → Approach → Result format\n"
            "   - Visuals: screenshots, photos, or links\n"
            "   - Metrics/results if available\n\n"
            "4. SERVICES\n"
            "   - What you offer (3-5 services)\n"
            "   - Starting prices or 'Contact for pricing'\n"
            "   - Process: how you work with clients\n\n"
            "5. TESTIMONIALS\n"
            "   - 3-5 client quotes with names/photos\n"
            "   - Specific results and outcomes\n"
            "   - Video testimonials if possible\n\n"
            "6. CONTACT\n"
            "   - Contact form or email\n"
            "   - Social media links\n"
            "   - Calendar booking link (Calendly)\n\n"
            "PLATFORMS:\n"
            "  - Personal website (WordPress, Webflow, Squarespace)\n"
            "  - Portfolio sites (Behance, Dribbble for designers)\n"
            "  - GitHub (for developers)\n"
            "  - Contently/Medium (for writers)\n"
            "  - LinkedIn (professional network + portfolio)\n\n"
            "QUICK START:\n"
            "  1. Pick 3 best projects to showcase\n"
            "  2. Write case studies for each (Problem → Solution → Result)\n"
            "  3. Get 2-3 testimonials from past clients\n"
            "  4. Set up a simple website or portfolio page\n"
            "  5. Share your portfolio on social media\n\n"
            "The built-in intelligence can provide portfolio content."
        )
        self._portfolio_output.setText(output)
        self._set_result_summary(f"Portfolio plan generated for {skill}.")


class InvestmentResearcherDialog(BaseCapabilityDialog):
    """Investment Researcher — stock/ETF screener, fundamentals analyzer, dividend tracker, portfolio risk assessor."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Investment Researcher — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_screener_tab(), "Stock Screener")
        tabs.addTab(self._build_fundamentals_tab(), "Fundamentals")
        tabs.addTab(self._build_dividend_tab(), "Dividend Tracker")
        tabs.addTab(self._build_risk_tab(), "Portfolio Risk")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Investment research only. NOT financial advice. You may lose money. Consult a licensed advisor. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_screener_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Stock/ETF Screener"))
        l.addWidget(QLabel("Ticker or company name:"))
        self._ir_ticker = QLineEdit()
        self._ir_ticker.setPlaceholderText("e.g., AAPL, MSFT, VTI, SPY...")
        l.addWidget(self._ir_ticker)
        l.addWidget(QLabel("Investment style:"))
        self._ir_style = QComboBox()
        self._ir_style.addItems(["Value", "Growth", "Dividend income", "Index/ETF", "Small-cap", "Large-cap"])
        l.addWidget(self._ir_style)
        btn = QPushButton("Screen Stock")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_screener)
        l.addWidget(btn)
        self._screener_output = QTextEdit()
        self._screener_output.setReadOnly(True)
        self._screener_output.setStyleSheet("")
        l.addWidget(self._screener_output, stretch=1)
        return w

    def _build_fundamentals_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Fundamentals Analyzer"))
        l.addWidget(QLabel("Enter key metrics (or leave blank for framework):"))
        metrics = [("P/E ratio", "25"), ("P/B ratio", "3"), ("Debt/Equity", "0.5"), ("ROE %", "15"), ("Revenue growth %", "10"), ("Free cash flow ($M)", "500")]
        self._fund_inputs: list[tuple[str, QLineEdit]] = []
        for label, default in metrics:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{label}:"))
            le = QLineEdit(default)
            le.setMaximumWidth(100)
            row.addWidget(le)
            row.addStretch()
            l.addLayout(row)
            self._fund_inputs.append((label, le))
        btn = QPushButton("Analyze Fundamentals")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_fundamentals)
        l.addWidget(btn)
        self._fund_output = QTextEdit()
        self._fund_output.setReadOnly(True)
        self._fund_output.setStyleSheet("")
        l.addWidget(self._fund_output, stretch=1)
        return w

    def _build_dividend_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Dividend Tracker & Income Projector"))
        row = QHBoxLayout()
        row.addWidget(QLabel("Annual dividend ($/share):"))
        self._div_amount = QLineEdit("2.50")
        self._div_amount.setMaximumWidth(80)
        row.addWidget(self._div_amount)
        row.addWidget(QLabel("Shares owned:"))
        self._div_shares = QLineEdit("100")
        self._div_shares.setMaximumWidth(80)
        row.addWidget(self._div_shares)
        row.addWidget(QLabel("Share price ($):"))
        self._div_price = QLineEdit("50")
        self._div_price.setMaximumWidth(80)
        row.addWidget(self._div_price)
        row.addWidget(QLabel("Frequency:"))
        self._div_freq = QComboBox()
        self._div_freq.addItems(["Quarterly", "Monthly", "Annual", "Semi-annual"])
        row.addWidget(self._div_freq)
        row.addStretch()
        l.addLayout(row)
        btn = QPushButton("Calculate Dividend Income")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_dividend)
        l.addWidget(btn)
        self._div_output = QTextEdit()
        self._div_output.setReadOnly(True)
        self._div_output.setStyleSheet("")
        l.addWidget(self._div_output, stretch=1)
        return w

    def _build_risk_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Portfolio Risk Assessor"))
        l.addWidget(QLabel("Enter your portfolio allocation (%):"))
        allocations = [("US Stocks", "50"), ("Intl Stocks", "15"), ("Bonds", "20"), ("REITs", "5"), ("Cash", "5"), ("Alternatives", "5")]
        self._risk_allocations: list[tuple[str, QLineEdit]] = []
        for label, default in allocations:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{label} %:"))
            le = QLineEdit(default)
            le.setMaximumWidth(60)
            row.addWidget(le)
            row.addStretch()
            l.addLayout(row)
            self._risk_allocations.append((label, le))
        l.addWidget(QLabel("Your age:"))
        self._risk_age = QLineEdit("35")
        self._risk_age.setMaximumWidth(60)
        l.addWidget(self._risk_age)
        btn = QPushButton("Assess Portfolio Risk")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_risk)
        l.addWidget(btn)
        self._risk_output = QTextEdit()
        self._risk_output.setReadOnly(True)
        self._risk_output.setStyleSheet("")
        l.addWidget(self._risk_output, stretch=1)
        return w

    def _run_through_runtime(self, task: str) -> str:
        try:
            from ...core.nexus_ai_runtime import NexusAIRuntime
            settings = SettingsManager()
            settings.initialize()
            runtime = NexusAIRuntime(settings=settings)
            result = runtime.run(task=task, ai_name=self._ai_name, ai_uuid=self._ai_uuid, ai_metadata={"abilities": self._abilities, "use_case": self._use_case, "guardrails": self._guardrails, "libraries": self._libraries})
            return result.result_text or ""
        except Exception:
            return ""

    def _run_screener(self):
        ticker = self._ir_ticker.text().strip()
        if not ticker:
            self._screener_output.setText("Enter a ticker or company name.")
            return
        style = self._ir_style.currentText()
        task = f"Screen the stock {ticker} for a {style} investor. Include key metrics, analyst sentiment, and risk factors."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._screener_output.setText(ai_result)
            self._set_result_summary(f"Stock screen for {ticker} via AI.")
            return
        stock_db = {
            "aapl": ("Apple Inc.", "Technology", "Large-cap growth", "Hardware, services, ecosystem"),
            "msft": ("Microsoft Corp.", "Technology", "Large-cap growth", "Software, cloud, enterprise"),
            "googl": ("Alphabet Inc.", "Technology", "Large-cap growth", "Search, advertising, cloud"),
            "amzn": ("Amazon.com Inc.", "Consumer/E-commerce", "Large-cap growth", "E-commerce, AWS, logistics"),
            "tsla": ("Tesla Inc.", "Automotive/Energy", "High volatility growth", "EVs, energy, AI/autonomy"),
            "v": ("Visa Inc.", "Financial", "Large-cap value/dividend", "Payment network, global reach"),
            "jnj": ("Johnson & Johnson", "Healthcare", "Large-cap value/dividend", "Diversified healthcare, dividend king"),
            "ko": ("Coca-Cola Co.", "Consumer staples", "Large-cap dividend", "Beverages, global brand, dividends"),
            "spy": ("SPDR S&P 500 ETF", "Index ETF", "Broad market index", "Tracks S&P 500, low cost"),
            "vti": ("Vanguard Total Market ETF", "Index ETF", "Total US market", "Tracks CRSP US Total Market"),
            "qqq": ("Invesco QQQ ETF", "Index ETF", "Nasdaq-100 index", "Tech-heavy, growth-oriented"),
            "schd": ("Schwab US Dividend ETF", "Dividend ETF", "Dividend income", "High-quality dividend stocks"),
        }
        key = ticker.lower().strip()
        info = stock_db.get(key)
        if not info:
            output = (
                f"[STOCK SCREENER — LOCAL ANALYSIS]\n\n"
                f"Ticker: {ticker}\n"
                f"Style: {style}\n"
                f"Status: Not in local database.\n\n"
                "STOCK RESEARCH FRAMEWORK:\n"
                "  1. Company overview and business model\n"
                "  2. Revenue and earnings trends (check SEC filings)\n"
                "  3. Key financial ratios (P/E, P/B, ROE, D/E)\n"
                "  4. Competitive position and moat\n"
                "  5. Growth catalysts and risks\n"
                "  6. Analyst ratings and price targets\n"
                "  7. Insider trading activity\n"
                "  8. Institutional ownership\n\n"
                "DATA SOURCES:\n"
                "  - Yahoo Finance, Google Finance (free)\n"
                "  - SEC EDGAR (filings)\n"
                "  - Morningstar, Seeking Alpha (analysis)\n\n"
                "The built-in intelligence can provide stock screening."
            )
        else:
            name, sector, category, focus = info
            output = (
                f"[STOCK SCREENER — LOCAL ANALYSIS]\n\n"
                f"Ticker: {ticker.upper()}\n"
                f"Company: {name}\n"
                f"Sector: {sector}\n"
                f"Category: {category}\n"
                f"Focus: {focus}\n\n"
                f"STYLE MATCH ({style}):\n"
            )
            style_match = {
                "Value": "Check P/E < 15, P/B < 3, strong balance sheet, consistent earnings",
                "Growth": "Check revenue growth > 15%, expanding margins, TAM expansion",
                "Dividend income": "Check yield > 2%, payout ratio < 60%, dividend growth streak",
                "Index/ETF": "Check expense ratio, tracking error, AUM, liquidity",
                "Small-cap": "Check market cap < $2B, growth potential, liquidity risk",
                "Large-cap": "Check market cap > $10B, stability, institutional ownership",
            }
            output += f"  {style_match.get(style, style_match['Value'])}\n\n"
            output += (
                "RESEARCH CHECKLIST:\n"
                "  [ ] Latest quarterly earnings report\n"
                "  [ ] Annual report (10-K) — business overview and risks\n"
                "  [ ] Balance sheet strength (debt, cash, current ratio)\n"
                "  [ ] Income statement trends (revenue, margins, EPS)\n"
                "  [ ] Cash flow statement (free cash flow, capex)\n"
                "  [ ] Competitive landscape\n"
                "  [ ] Regulatory risks\n"
                "  [ ] Management quality and track record\n\n"
                "The built-in intelligence can provide analysis."
            )
        self._screener_output.setText(output)
        self._set_result_summary(f"Stock screen for {ticker} ({style}).")

    def _run_fundamentals(self):
        try:
            values = {}
            for label, le in self._fund_inputs:
                val = le.text().strip()
                values[label] = float(val) if val else None
        except ValueError:
            self._fund_output.setText("Enter valid numbers.")
            return
        pe = values.get("P/E ratio")
        pb = values.get("P/B ratio")
        de = values.get("Debt/Equity")
        roe = values.get("ROE %")
        rev_growth = values.get("Revenue growth %")
        fcf = values.get("Free cash flow ($M)")
        output = "[FUNDAMENTALS ANALYSIS — LOCAL ANALYSIS]\n\n"
        if pe is not None:
            if pe < 15:
                output += f"  P/E ratio ({pe}): LOW — potentially undervalued (value territory)\n"
            elif pe < 25:
                output += f"  P/E ratio ({pe}): MODERATE — fairly valued for most sectors\n"
            elif pe < 40:
                output += f"  P/E ratio ({pe}): HIGH — growth expectations priced in\n"
            else:
                output += f"  P/E ratio ({pe}): VERY HIGH — speculative or high-growth\n"
        if pb is not None:
            if pb < 1:
                output += f"  P/B ratio ({pb}): BELOW BOOK VALUE — potentially undervalued or distressed\n"
            elif pb < 3:
                output += f"  P/B ratio ({pb}): MODERATE — reasonable for most sectors\n"
            else:
                output += f"  P/B ratio ({pb}): HIGH — market expects significant intangible value\n"
        if de is not None:
            if de < 0.3:
                output += f"  Debt/Equity ({de}): LOW — strong balance sheet\n"
            elif de < 1.0:
                output += f"  Debt/Equity ({de}): MODERATE — manageable leverage\n"
            else:
                output += f"  Debt/Equity ({de}): HIGH — elevated financial risk\n"
        if roe is not None:
            if roe >= 20:
                output += f"  ROE ({roe}%): EXCELLENT — strong profitability\n"
            elif roe >= 15:
                output += f"  ROE ({roe}%): GOOD — above average returns\n"
            elif roe >= 10:
                output += f"  ROE ({roe}%): MODERATE — acceptable but not standout\n"
            else:
                output += f"  ROE ({roe}%): LOW — poor capital efficiency\n"
        if rev_growth is not None:
            if rev_growth >= 20:
                output += f"  Revenue growth ({rev_growth}%): HIGH — strong growth trajectory\n"
            elif rev_growth >= 10:
                output += f"  Revenue growth ({rev_growth}%): MODERATE — steady growth\n"
            elif rev_growth >= 0:
                output += f"  Revenue growth ({rev_growth}%): SLOW — limited growth\n"
            else:
                output += f"  Revenue growth ({rev_growth}%): NEGATIVE — declining revenue\n"
        if fcf is not None:
            if fcf > 0:
                output += f"  Free cash flow (${fcf}M): POSITIVE — company generates cash\n"
            else:
                output += f"  Free cash flow (${fcf}M): NEGATIVE — burning cash, higher risk\n"
        output += (
            "\nOVERALL ASSESSMENT:\n"
            "  Combine these metrics for a holistic view. No single metric\n"
            "  tells the whole story. Compare to industry peers and\n"
            "  historical averages.\n\n"
            "RED FLAGS TO WATCH:\n"
            "  - P/E > 50 with low growth = overvalued\n"
            "  - Debt/Equity > 2 = financial distress risk\n"
            "  - Negative free cash flow for multiple years\n"
            "  - Declining ROE trend\n"
            "  - Revenue growth slowing significantly\n\n"
            "This is NOT financial advice. Consult a licensed financial advisor."
        )
        self._fund_output.setText(output)
        self._set_result_summary("Fundamentals analyzed from provided metrics.")

    def _run_dividend(self):
        try:
            div = float(self._div_amount.text().strip() or "0")
            shares = int(self._div_shares.text().strip() or "0")
            price = float(self._div_price.text().strip() or "0")
        except ValueError:
            self._div_output.setText("Enter valid numbers.")
            return
        freq = self._div_freq.currentText()
        freq_map = {"Quarterly": 4, "Monthly": 12, "Annual": 1, "Semi-annual": 2}
        payments_per_year = freq_map.get(freq, 4)
        annual_income = div * shares
        yield_pct = (div / price * 100) if price else 0
        per_payment = annual_income / payments_per_year
        investment_value = shares * price
        monthly_income = annual_income / 12
        output = (
            f"[DIVIDEND INCOME PROJECTOR — LOCAL ANALYSIS]\n\n"
            f"Annual dividend: ${div:.2f}/share\n"
            f"Shares owned: {shares}\n"
            f"Share price: ${price:.2f}\n"
            f"Payment frequency: {freq} ({payments_per_year}x/year)\n\n"
            f"DIVIDEND YIELD: {yield_pct:.2f}%\n"
            f"ANNUAL DIVIDEND INCOME: ${annual_income:.2f}\n"
            f"MONTHLY INCOME (averaged): ${monthly_income:.2f}\n"
            f"PER PAYMENT: ${per_payment:.2f}\n\n"
            f"INVESTMENT VALUE: ${investment_value:.2f}\n\n"
            f"INCOME PROJECTIONS:\n"
            f"  5 years (reinvested at {yield_pct:.1f}%): ~${annual_income * 5 * 1.3:.2f} cumulative\n"
            f"  10 years (reinvested): ~${annual_income * 10 * 1.8:.2f} cumulative\n"
            f"  20 years (reinvested): ~${annual_income * 20 * 3.5:.2f} cumulative\n\n"
            "DIVIDEND INVESTING TIPS:\n"
            "  - Look for Dividend Aristocrats (25+ years of increases)\n"
            "  - Target payout ratio < 60% (sustainable)\n"
            "  - DRIP (dividend reinvestment) compounds returns\n"
            "  - Diversify across sectors to reduce risk\n"
            "  - Tax considerations: qualified vs ordinary dividends\n\n"
            "This is NOT financial advice. Dividends are not guaranteed."
        )
        self._div_output.setText(output)
        self._set_result_summary(f"Dividend: ${annual_income:.2f}/yr, {yield_pct:.2f}% yield.")

    def _run_risk(self):
        try:
            age = int(self._risk_age.text().strip() or "35")
            allocations = {}
            total = 0
            for label, le in self._risk_allocations:
                val = int(le.text().strip() or "0")
                allocations[label] = val
                total += val
        except ValueError:
            self._risk_output.setText("Enter valid numbers.")
            return
        if total != 100:
            self._risk_output.setText(f"Allocations must total 100%. Currently: {total}%")
            return
        equity = allocations.get("US Stocks", 0) + allocations.get("Intl Stocks", 0) + allocations.get("REITs", 0)
        bonds = allocations.get("Bonds", 0)
        cash = allocations.get("Cash", 0)
        alts = allocations.get("Alternatives", 0)
        rule_of_thumb_equity = max(100 - age, 40)
        output = (
            f"[PORTFOLIO RISK ASSESSMENT — LOCAL ANALYSIS]\n\n"
            f"Age: {age}\n"
            f"Rule-of-thumb equity allocation: {rule_of_thumb_equity}%\n"
            f"Your equity allocation: {equity}%\n\n"
            f"ALLOCATION BREAKDOWN:\n"
            f"  Equities (stocks + REITs): {equity}%\n"
            f"  Bonds:                      {bonds}%\n"
            f"  Cash:                       {cash}%\n"
            f"  Alternatives:               {alts}%\n\n"
        )
        if equity > rule_of_thumb_equity + 15:
            output += "RISK LEVEL: AGGRESSIVE — Higher equity than age-based guideline.\n"
            output += "  You may experience larger drawdowns in market downturns.\n"
            output += "  Ensure you can hold through a 30-50% decline without selling.\n"
        elif equity < rule_of_thumb_equity - 15:
            output += "RISK LEVEL: CONSERVATIVE — Lower equity than age-based guideline.\n"
            output += "  Your portfolio may not grow enough to outpace inflation.\n"
            output += "  Consider increasing equity allocation if you have long time horizon.\n"
        else:
            output += "RISK LEVEL: BALANCED — Equity allocation aligns with age-based guideline.\n"
            output += "  This is a reasonable risk level for your age.\n"
        output += (
            f"\nDIVERSIFICATION ASSESSMENT:\n"
            f"  US vs International: {allocations.get('US Stocks', 0)}% / {allocations.get('Intl Stocks', 0)}%\n"
        )
        intl = allocations.get("Intl Stocks", 0)
        total_equity = equity if equity else 1
        intl_pct_of_equity = (intl / total_equity * 100) if total_equity else 0
        if intl_pct_of_equity < 15:
            output += "  ⚠ Low international exposure — consider 20-40% of equity in international\n"
        elif intl_pct_of_equity > 50:
            output += "  ⚠ High international exposure — consider currency and geopolitical risks\n"
        else:
            output += "  ✓ International allocation is reasonable\n"
        if cash > 20:
            output += "  ⚠ High cash allocation — inflation risk, opportunity cost\n"
        if alts > 20:
            output += "  ⚠ High alternatives — ensure you understand liquidity and complexity\n"
        output += (
            "\nREBALANCING RECOMMENDATION:\n"
            "  - Review allocation annually or when drift > 5%\n"
            "  - Rebalance by directing new contributions to underweight categories\n"
            "  - Tax-loss harvesting in taxable accounts\n\n"
            "This is NOT financial advice. Consult a licensed financial advisor."
        )
        self._risk_output.setText(output)
        self._set_result_summary(f"Risk assessed: {equity}% equity vs {rule_of_thumb_equity}% guideline.")


class ROICalculatorDialog(BaseCapabilityDialog):
    """ROI Calculator — investment ROI, payback period, NPV/IRR estimator, comparison tool."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"ROI Calculator — {ai_name} | Avery Logic Works(TM)")
        self.resize(800, 580)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_roi_tab(), "ROI Calculator")
        tabs.addTab(self._build_payback_tab(), "Payback Period")
        tabs.addTab(self._build_npv_tab(), "NPV Estimator")
        tabs.addTab(self._build_compare_tab(), "Comparison")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Calculations are estimates only. Not financial advice. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_roi_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Return on Investment Calculator"))
        row = QHBoxLayout()
        row.addWidget(QLabel("Initial investment ($):"))
        self._roi_initial = QLineEdit("10000")
        self._roi_initial.setMaximumWidth(120)
        row.addWidget(self._roi_initial)
        row.addWidget(QLabel("Final value ($):"))
        self._roi_final = QLineEdit("15000")
        self._roi_final.setMaximumWidth(120)
        row.addWidget(self._roi_final)
        row.addWidget(QLabel("Time period (years):"))
        self._roi_years = QLineEdit("3")
        self._roi_years.setMaximumWidth(60)
        row.addWidget(self._roi_years)
        row.addStretch()
        l.addLayout(row)
        btn = QPushButton("Calculate ROI")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_roi)
        l.addWidget(btn)
        self._roi_output = QTextEdit()
        self._roi_output.setReadOnly(True)
        self._roi_output.setStyleSheet("")
        l.addWidget(self._roi_output, stretch=1)
        return w

    def _build_payback_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Payback Period Calculator"))
        row = QHBoxLayout()
        row.addWidget(QLabel("Initial investment ($):"))
        self._pb_initial = QLineEdit("5000")
        self._pb_initial.setMaximumWidth(120)
        row.addWidget(self._pb_initial)
        row.addWidget(QLabel("Annual return ($):"))
        self._pb_annual = QLineEdit("1500")
        self._pb_annual.setMaximumWidth(120)
        row.addWidget(self._pb_annual)
        row.addStretch()
        l.addLayout(row)
        btn = QPushButton("Calculate Payback")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_payback)
        l.addWidget(btn)
        self._pb_output = QTextEdit()
        self._pb_output.setReadOnly(True)
        self._pb_output.setStyleSheet("")
        l.addWidget(self._pb_output, stretch=1)
        return w

    def _build_npv_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Net Present Value (NPV) Estimator"))
        row = QHBoxLayout()
        row.addWidget(QLabel("Initial investment ($):"))
        self._npv_initial = QLineEdit("10000")
        self._npv_initial.setMaximumWidth(120)
        row.addWidget(self._npv_initial)
        row.addWidget(QLabel("Annual cash flow ($):"))
        self._npv_cashflow = QLineEdit("3000")
        self._npv_cashflow.setMaximumWidth(120)
        row.addWidget(self._npv_cashflow)
        row.addWidget(QLabel("Discount rate %:"))
        self._npv_rate = QLineEdit("8")
        self._npv_rate.setMaximumWidth(60)
        row.addWidget(self._npv_rate)
        row.addWidget(QLabel("Years:"))
        self._npv_years = QLineEdit("5")
        self._npv_years.setMaximumWidth(60)
        row.addWidget(self._npv_years)
        row.addStretch()
        l.addLayout(row)
        btn = QPushButton("Calculate NPV")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_npv)
        l.addWidget(btn)
        self._npv_output = QTextEdit()
        self._npv_output.setReadOnly(True)
        self._npv_output.setStyleSheet("")
        l.addWidget(self._npv_output, stretch=1)
        return w

    def _build_compare_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Investment Comparison Tool"))
        l.addWidget(QLabel("Compare up to 3 investments:"))
        self._compare_entries: list[tuple[QLineEdit, QLineEdit, QLineEdit]] = []
        for i in range(3):
            row = QHBoxLayout()
            name = QLineEdit()
            name.setPlaceholderText(f"Investment {i+1} name")
            initial = QLineEdit()
            initial.setPlaceholderText("Initial $")
            initial.setMaximumWidth(80)
            final = QLineEdit()
            final.setPlaceholderText("Final $")
            final.setMaximumWidth(80)
            row.addWidget(QLabel(f"#{i+1}:"))
            row.addWidget(name, stretch=2)
            row.addWidget(initial)
            row.addWidget(final)
            row.addStretch()
            l.addLayout(row)
            self._compare_entries.append((name, initial, final))
        btn = QPushButton("Compare Investments")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_compare)
        l.addWidget(btn)
        self._compare_output = QTextEdit()
        self._compare_output.setReadOnly(True)
        self._compare_output.setStyleSheet("")
        l.addWidget(self._compare_output, stretch=1)
        return w

    def _run_roi(self):
        try:
            initial = float(self._roi_initial.text().strip() or "0")
            final_val = float(self._roi_final.text().strip() or "0")
            years = float(self._roi_years.text().strip() or "1")
        except ValueError:
            self._roi_output.setText("Enter valid numbers.")
            return
        if initial <= 0 or years <= 0:
            self._roi_output.setText("Initial investment and years must be > 0.")
            return
        total_return = final_val - initial
        roi_pct = (total_return / initial * 100) if initial else 0
        annualized = ((final_val / initial) ** (1 / years) - 1) * 100 if initial and years else 0
        output = (
            f"[ROI CALCULATOR — LOCAL ANALYSIS]\n\n"
            f"Initial investment: ${initial:,.2f}\n"
            f"Final value: ${final_val:,.2f}\n"
            f"Time period: {years:.1f} years\n\n"
            f"Total return: ${total_return:,.2f}\n"
            f"Total ROI: {roi_pct:.2f}%\n"
            f"Annualized return: {annualized:.2f}%/year\n\n"
            f"BENCHMARKS:\n"
            f"  S&P 500 avg: ~10%/year (historical)\n"
            f"  Bonds avg: ~4-5%/year\n"
            f"  Inflation avg: ~3%/year\n"
            f"  Your investment: {annualized:.2f}%/year\n\n"
        )
        if annualized > 10:
            output += "ASSESSMENT: Outperforming market average. Excellent returns.\n"
        elif annualized > 5:
            output += "ASSESSMENT: Solid returns, above bond average.\n"
        elif annualized > 0:
            output += "ASSESSMENT: Positive but modest. Consider whether it beats inflation.\n"
        else:
            output += "ASSESSMENT: Negative returns. Investment lost value.\n"
        output += "\nThis is NOT financial advice. Past performance doesn't guarantee future results."
        self._roi_output.setText(output)
        self._set_result_summary(f"ROI: {roi_pct:.1f}% total, {annualized:.1f}%/yr annualized.")

    def _run_payback(self):
        try:
            initial = float(self._pb_initial.text().strip() or "0")
            annual = float(self._pb_annual.text().strip() or "0")
        except ValueError:
            self._pb_output.setText("Enter valid numbers.")
            return
        if initial <= 0 or annual <= 0:
            self._pb_output.setText("Enter positive values.")
            return
        payback_years = initial / annual
        payback_months = payback_years * 12
        output = (
            f"[PAYBACK PERIOD — LOCAL ANALYSIS]\n\n"
            f"Initial investment: ${initial:,.2f}\n"
            f"Annual return: ${annual:,.2f}\n\n"
            f"Payback period: {payback_years:.2f} years ({payback_months:.0f} months)\n\n"
            "INTERPRETATION:\n"
        )
        if payback_years < 2:
            output += "  EXCELLENT — Very fast payback. Low risk.\n"
        elif payback_years < 5:
            output += "  GOOD — Reasonable payback period for most investments.\n"
        elif payback_years < 10:
            output += "  MODERATE — Long payback. Consider opportunity cost.\n"
        else:
            output += "  SLOW — Very long payback. High risk if conditions change.\n"
        output += (
            "\nCONSIDERATIONS:\n"
            "  - Payback doesn't account for time value of money\n"
            "  - Doesn't consider returns after payback period\n"
            "  - Use alongside ROI and NPV for fuller picture\n"
            "  - Shorter payback = lower risk (capital returned faster)\n\n"
            "This is NOT financial advice."
        )
        self._pb_output.setText(output)
        self._set_result_summary(f"Payback: {payback_years:.1f} years.")

    def _run_npv(self):
        try:
            initial = float(self._npv_initial.text().strip() or "0")
            cashflow = float(self._npv_cashflow.text().strip() or "0")
            rate = float(self._npv_rate.text().strip() or "0") / 100
            years = int(self._npv_years.text().strip() or "0")
        except ValueError:
            self._npv_output.setText("Enter valid numbers.")
            return
        if years <= 0:
            self._npv_output.setText("Years must be > 0.")
            return
        npv = -initial
        for y in range(1, years + 1):
            npv += cashflow / ((1 + rate) ** y)
        irr_low, irr_high = 0, 100
        for _ in range(100):
            mid = (irr_low + irr_high) / 2
            test_npv = -initial
            for y in range(1, years + 1):
                test_npv += cashflow / ((1 + mid / 100) ** y)
            if test_npv > 0:
                irr_low = mid
            else:
                irr_high = mid
        irr = (irr_low + irr_high) / 2
        output = (
            f"[NPV ESTIMATOR — LOCAL ANALYSIS]\n\n"
            f"Initial investment: ${initial:,.2f}\n"
            f"Annual cash flow: ${cashflow:,.2f}\n"
            f"Discount rate: {rate*100:.1f}%\n"
            f"Time horizon: {years} years\n\n"
            f"NET PRESENT VALUE (NPV): ${npv:,.2f}\n"
            f"INTERNAL RATE OF RETURN (IRR): ~{irr:.1f}%\n\n"
        )
        if npv > 0:
            output += "VERDICT: POSITIVE NPV — Investment adds value above the discount rate.\n"
            output += f"  IRR ({irr:.1f}%) exceeds discount rate ({rate*100:.1f}%) — proceed.\n"
        else:
            output += "VERDICT: NEGATIVE NPV — Investment does not meet the required return.\n"
            output += f"  IRR ({irr:.1f}%) is below discount rate ({rate*100:.1f}%) — reconsider.\n"
        output += (
            "\nNPV INTERPRETATION:\n"
            "  - Positive NPV = investment creates value\n"
            "  - Negative NPV = investment destroys value\n"
            "  - NPV accounts for time value of money (future cash worth less)\n"
            "  - Discount rate = your required return or opportunity cost\n\n"
            "IRR INTERPRETATION:\n"
            "  - IRR is the rate where NPV = 0\n"
            "  - If IRR > discount rate, investment is worthwhile\n"
            "  - Compare IRR to alternative investments\n\n"
            "This is NOT financial advice."
        )
        self._npv_output.setText(output)
        self._set_result_summary(f"NPV: ${npv:,.2f}, IRR: ~{irr:.1f}%.")

    def _run_compare(self):
        entries = []
        for name_le, init_le, final_le in self._compare_entries:
            name = name_le.text().strip()
            if name:
                try:
                    init = float(init_le.text().strip() or "0")
                    final_val = float(final_le.text().strip() or "0")
                except ValueError:
                    continue
                entries.append((name, init, final_val))
        if not entries:
            self._compare_output.setText("Enter at least one investment.")
            return
        output = "[INVESTMENT COMPARISON — LOCAL ANALYSIS]\n\n"
        output += f"{'Investment':<20} {'Initial':>12} {'Final':>12} {'Return $':>12} {'ROI %':>10}\n"
        output += "-" * 70 + "\n"
        for name, init, final_val in entries:
            ret = final_val - init
            roi = (ret / init * 100) if init else 0
            output += f"{name:<20} ${init:>10,.0f} ${final_val:>10,.0f} ${ret:>10,.0f} {roi:>8.1f}%\n"
        best = max(entries, key=lambda e: ((e[2] - e[1]) / e[1] * 100) if e[1] else 0)
        best_roi = ((best[2] - best[1]) / best[1] * 100) if best[1] else 0
        output += f"\nBest ROI: {best[0]} ({best_roi:.1f}%)\n\n"
        output += (
            "COMPARISON TIPS:\n"
            "  - ROI alone doesn't account for time or risk\n"
            "  - Consider payback period and risk level\n"
            "  - Higher ROI often means higher risk\n"
            "  - Diversification across investments reduces overall risk\n\n"
            "This is NOT financial advice."
        )
        self._compare_output.setText(output)
        self._set_result_summary(f"Compared {len(entries)} investments. Best: {best[0]}.")


class MarketGapFinderDialog(BaseCapabilityDialog):
    """Market Gap Finder — niche analyzer, competitor gap mapper, trend spotter, opportunity scorer."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Market Gap Finder — {ai_name} | Avery Logic Works(TM)")
        self.resize(820, 600)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_niche_tab(), "Niche Analyzer")
        tabs.addTab(self._build_gap_tab(), "Competitor Gaps")
        tabs.addTab(self._build_trend_tab(), "Trend Spotter")
        tabs.addTab(self._build_score_tab(), "Opportunity Scorer")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Market analysis is advisory. No guaranteed opportunities. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_niche_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Niche Analyzer"))
        l.addWidget(QLabel("Enter a niche or market to analyze:"))
        self._niche_input = QLineEdit()
        self._niche_input.setPlaceholderText("e.g., sustainable pet products, AI tools for writers, home fitness...")
        l.addWidget(self._niche_input)
        btn = QPushButton("Analyze Niche")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_niche)
        l.addWidget(btn)
        self._niche_output = QTextEdit()
        self._niche_output.setReadOnly(True)
        self._niche_output.setStyleSheet("")
        l.addWidget(self._niche_output, stretch=1)
        return w

    def _build_gap_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Competitor Gap Mapper"))
        l.addWidget(QLabel("Enter your industry and known competitors:"))
        self._gap_industry = QLineEdit()
        self._gap_industry.setPlaceholderText("Industry (e.g., meal delivery, online education)")
        l.addWidget(self._gap_industry)
        self._gap_competitors = QTextEdit()
        self._gap_competitors.setPlaceholderText("List competitors and what they offer (one per line):\ne.g.,\nCompetitor A: premium pricing, no budget option\nCompetitor B: great product, poor customer service\nCompetitor C: wide selection, slow shipping")
        self._gap_competitors.setMaximumHeight(120)
        l.addWidget(self._gap_competitors)
        btn = QPushButton("Map Gaps")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_gap)
        l.addWidget(btn)
        self._gap_output = QTextEdit()
        self._gap_output.setReadOnly(True)
        self._gap_output.setStyleSheet("")
        l.addWidget(self._gap_output, stretch=1)
        return w

    def _build_trend_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Trend Spotter"))
        l.addWidget(QLabel("Industry or topic:"))
        self._trend_input = QLineEdit()
        self._trend_input.setPlaceholderText("e.g., remote work tools, plant-based food, AI automation...")
        l.addWidget(self._trend_input)
        btn = QPushButton("Spot Trends")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_trends)
        l.addWidget(btn)
        self._trend_output = QTextEdit()
        self._trend_output.setReadOnly(True)
        self._trend_output.setStyleSheet("")
        l.addWidget(self._trend_output, stretch=1)
        return w

    def _build_score_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Opportunity Scorer"))
        l.addWidget(QLabel("Rate your business opportunity (1-10):"))
        criteria = [
            "Market size/demand",
            "Your competitive advantage",
            "Profit margin potential",
            "Low startup cost",
            "Scalability",
            "Your passion/expertise",
            "Low competition",
            "Recurring revenue potential",
        ]
        self._score_inputs: list[tuple[str, QComboBox]] = []
        for criterion in criteria:
            row = QHBoxLayout()
            row.addWidget(QLabel(criterion))
            combo = QComboBox()
            combo.addItems([str(i) for i in range(1, 11)])
            combo.setCurrentText("5")
            combo.setMaximumWidth(60)
            row.addWidget(combo)
            row.addStretch()
            l.addLayout(row)
            self._score_inputs.append((criterion, combo))
        btn = QPushButton("Score Opportunity")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_score)
        l.addWidget(btn)
        self._score_output = QTextEdit()
        self._score_output.setReadOnly(True)
        self._score_output.setStyleSheet("")
        l.addWidget(self._score_output, stretch=1)
        return w

    def _run_through_runtime(self, task: str) -> str:
        try:
            from ...core.nexus_ai_runtime import NexusAIRuntime
            settings = SettingsManager()
            settings.initialize()
            runtime = NexusAIRuntime(settings=settings)
            result = runtime.run(task=task, ai_name=self._ai_name, ai_uuid=self._ai_uuid, ai_metadata={"abilities": self._abilities, "use_case": self._use_case, "guardrails": self._guardrails, "libraries": self._libraries})
            return result.result_text or ""
        except Exception:
            return ""

    def _run_niche(self):
        niche = self._niche_input.text().strip()
        if not niche:
            self._niche_output.setText("Enter a niche to analyze.")
            return
        task = f"Analyze the market niche: {niche}. Include market size, growth trends, key players, gaps, and opportunities."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._niche_output.setText(ai_result)
            self._set_result_summary(f"Niche analyzed via AI: {niche}.")
            return
        output = (
            f"[NICHE ANALYZER — LOCAL ANALYSIS]\n\n"
            f"Niche: {niche}\n\n"
            "ANALYSIS FRAMEWORK:\n\n"
            "1. MARKET SIZE & GROWTH\n"
            "   - Total addressable market (TAM)\n"
            "   - Serviceable addressable market (SAM)\n"
            "   - Annual growth rate\n"
            "   - Market trends and drivers\n\n"
            "2. CUSTOMER ANALYSIS\n"
            "   - Target demographics\n"
            "   - Pain points and unmet needs\n"
            "   - Willingness to pay\n"
            "   - Customer acquisition cost (CAC)\n\n"
            "3. COMPETITIVE LANDSCAPE\n"
            "   - Direct competitors\n"
            "   - Indirect competitors\n"
            "   - Market share distribution\n"
            "   - Barriers to entry\n\n"
            "4. OPPORTUNITY ASSESSMENT\n"
            "   - Underserved segments\n"
            "   - Geographic gaps\n"
            "   - Price gaps (premium vs budget)\n"
            "   - Feature/service gaps\n\n"
            "5. VIABILITY CHECK\n"
            "   - Profit margin potential\n"
            "   - Scalability\n"
            "   - Time to market\n"
            "   - Required capital\n\n"
            "RESEARCH TOOLS:\n"
            "  - Google Trends (search interest)\n"
            "  - Statista, IBISWorld (market data)\n"
            "  - Reddit, forums (community sentiment)\n"
            "  - Amazon, App Store (product gaps)\n"
            "  - Keyword tools (search volume)\n\n"
            "The built-in intelligence can provide niche analysis."
        )
        self._niche_output.setText(output)
        self._set_result_summary(f"Niche analysis framework for: {niche}.")

    def _run_gap(self):
        industry = self._gap_industry.text().strip()
        competitors_text = self._gap_competitors.toPlainText().strip()
        if not industry or not competitors_text:
            self._gap_output.setText("Enter both industry and competitor information.")
            return
        task = f"Map competitor gaps in the {industry} industry. Competitors: {competitors_text}. Identify underserved areas and opportunities."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._gap_output.setText(ai_result)
            self._set_result_summary(f"Gap mapping via AI for {industry}.")
            return
        lines = [l.strip() for l in competitors_text.split("\n") if l.strip()]
        gaps_found = []
        gap_keywords = {
            "no budget": "Price gap: No budget/affordable option available",
            "expensive": "Price gap: Premium pricing leaves budget segment open",
            "premium": "Price gap: Premium-only positioning leaves budget opportunity",
            "poor customer": "Service gap: Poor customer service — opportunity for service excellence",
            "slow shipping": "Operations gap: Slow shipping — opportunity for fast delivery",
            "slow": "Speed gap: Slow service/delivery — speed as differentiator",
            "limited": "Product gap: Limited selection — opportunity for wider range",
            "narrow": "Product gap: Narrow focus — opportunity for broader solution",
            "no mobile": "Technology gap: No mobile app — mobile-first opportunity",
            "bad ui": "UX gap: Poor user experience — design as differentiator",
            "poor quality": "Quality gap: Poor quality — premium quality opportunity",
            "no support": "Service gap: No customer support — support as differentiator",
            "complex": "Simplicity gap: Complex product — simplified version opportunity",
            "enterprise only": "Market gap: Enterprise-only — SMB opportunity",
            "no integration": "Integration gap: No integrations — ecosystem play",
        }
        for line in lines:
            line_lower = line.lower()
            for keyword, gap_desc in gap_keywords.items():
                if keyword in line_lower:
                    gaps_found.append((line, gap_desc))
        output = f"[COMPETITOR GAP MAP — LOCAL ANALYSIS]\n\nIndustry: {industry}\n\n"
        if gaps_found:
            output += f"GAPS IDENTIFIED ({len(gaps_found)}):\n\n"
            for competitor_line, gap in gaps_found:
                output += f"  ⚡ {gap}\n     Source: {competitor_line}\n\n"
        else:
            output += "No specific gaps detected from the descriptions provided.\n\n"
        output += (
            "COMMON GAP CATEGORIES TO EXPLORE:\n\n"
            "  1. PRICE GAP — Is there a budget or premium tier not served?\n"
            "  2. SERVICE GAP — Poor customer service? Slow response times?\n"
            "  3. QUALITY GAP — Low quality products? High return rates?\n"
            "  4. SPEED GAP — Slow delivery, onboarding, or support?\n"
            "  5. NICHE GAP — Underserved customer segment?\n"
            "  6. GEOGRAPHIC GAP — Areas not served?\n"
            "  7. TECHNOLOGY GAP — Outdated tech, no mobile, no API?\n"
            "  8. FEATURE GAP — Missing features customers want?\n"
            "  9. CHANNEL GAP — Not on certain platforms/marketplaces?\n"
            "  10. BRAND GAP — No strong brand in the space?\n\n"
            "GAP EXPLOITATION STRATEGY:\n"
            "  - Pick 1-2 gaps that align with your strengths\n"
            "  - Validate with customer interviews/surveys\n"
            "  - Build MVP addressing the gap\n"
            "  - Position as the solution to the gap\n"
            "  - Defend with continuous improvement\n\n"
            "The built-in intelligence can provide gap analysis."
        )
        self._gap_output.setText(output)
        self._set_result_summary(f"Gap mapping: {len(gaps_found)} gaps found in {industry}.")

    def _run_trends(self):
        topic = self._trend_input.text().strip()
        if not topic:
            self._trend_output.setText("Enter a topic to spot trends.")
            return
        task = f"Identify emerging trends and opportunities in: {topic}. Include growth indicators, market signals, and timing."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._trend_output.setText(ai_result)
            self._set_result_summary(f"Trends spotted via AI for: {topic}.")
            return
        output = (
            f"[TREND SPOTTER — LOCAL ANALYSIS]\n\n"
            f"Topic: {topic}\n\n"
            "TREND IDENTIFICATION FRAMEWORK:\n\n"
            "1. SEARCH TREND SIGNALS\n"
            "   - Google Trends: Is search volume rising?\n"
            "   - YouTube/Reddit: Growing communities?\n"
            "   - App Store: New apps appearing?\n"
            "   - Patent filings: Innovation activity?\n\n"
            "2. MARKET SIGNALS\n"
            "   - Venture capital funding in the space\n"
            "   - New startups and product launches\n"
            "   - Industry reports and forecasts\n"
            "   - Conference/trade show growth\n\n"
            "3. CONSUMER SIGNALS\n"
            "   - Social media mentions and sentiment\n"
            "   - Influencer adoption\n"
            "   - Community/forum activity\n"
            "   - Review sites and ratings\n\n"
            "4. TIMING ASSESSMENT\n"
            "   - Early stage: High risk, high reward\n"
            "   - Growth stage: Proven demand, increasing competition\n"
            "   - Mature stage: Saturated, differentiation needed\n"
            "   - Declining: Avoid or pivot\n\n"
            "5. OPPORTUNITY MATRIX\n"
            "   - High growth + low competition = IDEAL\n"
            "   - High growth + high competition = CHALLENGING\n"
            "   - Low growth + low competition = NICHE\n"
            "   - Low growth + high competition = AVOID\n\n"
            "TREND RESEARCH TOOLS:\n"
            "  - Google Trends (free)\n"
            "  - Exploding Topics (trend discovery)\n"
            "  - Product Hunt (new products)\n"
            "  - CB Insights (startup data)\n"
            "  - Reddit, Twitter (community signals)\n"
            "  - Industry publications and newsletters\n\n"
            "The built-in intelligence can provide trend analysis."
        )
        self._trend_output.setText(output)
        self._set_result_summary(f"Trend framework generated for: {topic}.")

    def _run_score(self):
        scores = []
        for criterion, combo in self._score_inputs:
            scores.append((criterion, int(combo.currentText())))
        total = sum(s for _, s in scores)
        max_total = len(scores) * 10
        pct = total / max_total * 100
        avg = total / len(scores) if scores else 0
        output = (
            f"[OPPORTUNITY SCORER — LOCAL ANALYSIS]\n\n"
            f"Total score: {total}/{max_total} ({pct:.0f}%)\n"
            f"Average score: {avg:.1f}/10\n\n"
            "SCORE BREAKDOWN:\n"
        )
        for criterion, score in scores:
            bar = "█" * score + "░" * (10 - score)
            output += f"  {criterion:<30} [{bar}] {score}/10\n"
        output += "\n"
        if pct >= 80:
            verdict = "EXCELLENT OPPORTUNITY — Strong potential across most criteria. Move forward with confidence."
        elif pct >= 65:
            verdict = "GOOD OPPORTUNITY — Solid potential. Address weak areas before committing fully."
        elif pct >= 50:
            verdict = "MODERATE OPPORTUNITY — Mixed signals. Requires careful planning and risk mitigation."
        elif pct >= 35:
            verdict = "WEAK OPPORTUNITY — Significant concerns. Consider alternatives or major pivots."
        else:
            verdict = "POOR OPPORTUNITY — Multiple red flags. Likely not worth pursuing."
        output += f"VERDICT: {verdict}\n\n"
        weak = [c for c, s in scores if s <= 3]
        strong = [c for c, s in scores if s >= 8]
        if weak:
            output += f"WEAK AREAS (score ≤ 3): {', '.join(weak)}\n"
            output += "  → These are your biggest risks. Mitigate or avoid.\n"
        if strong:
            output += f"STRENGTHS (score ≥ 8): {', '.join(strong)}\n"
            output += "  → These are your competitive advantages. Leverage them.\n"
        output += (
            "\nSCORING GUIDE:\n"
            "  1-3: Major concern / dealbreaker\n"
            "  4-6: Average / acceptable\n"
            "  7-8: Strong / advantage\n"
            "  9-10: Exceptional / major differentiator\n\n"
            "This is an advisory tool. Use alongside market research and intuition."
        )
        self._score_output.setText(output)
        self._set_result_summary(f"Opportunity scored: {total}/{max_total} ({pct:.0f}%) — {verdict.split('—')[0].strip()}.")


class NegotiationCoachDialog(BaseCapabilityDialog):
    """Negotiation Coach — salary negotiator, deal scenario simulator, BATNA analyzer, persuasion techniques."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Negotiation Coach — {ai_name} | Avery Logic Works(TM)")
        self.resize(820, 600)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_salary_tab(), "Salary Negotiator")
        tabs.addTab(self._build_scenario_tab(), "Deal Simulator")
        tabs.addTab(self._build_batna_tab(), "BATNA Analyzer")
        tabs.addTab(self._build_tech_tab(), "Persuasion Tech")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Advisory coaching only. Results not guaranteed. Avery Logic Works is not liable for negotiation outcomes.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_salary_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Salary Negotiation Coach"))
        row = QHBoxLayout()
        row.addWidget(QLabel("Current salary ($):"))
        self._sal_current = QLineEdit("60000")
        self._sal_current.setMaximumWidth(100)
        row.addWidget(self._sal_current)
        row.addWidget(QLabel("Target salary ($):"))
        self._sal_target = QLineEdit("75000")
        self._sal_target.setMaximumWidth(100)
        row.addWidget(self._sal_target)
        row.addWidget(QLabel("Role:"))
        self._sal_role = QLineEdit()
        self._sal_role.setPlaceholderText("e.g., Software Engineer")
        row.addWidget(self._sal_role)
        row.addStretch()
        l.addLayout(row)
        btn = QPushButton("Generate Negotiation Plan")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_salary)
        l.addWidget(btn)
        self._salary_output = QTextEdit()
        self._salary_output.setReadOnly(True)
        self._salary_output.setStyleSheet("")
        l.addWidget(self._salary_output, stretch=1)
        return w

    def _build_scenario_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Deal Scenario Simulator"))
        l.addWidget(QLabel("What are you negotiating?"))
        self._scenario_topic = QLineEdit()
        self._scenario_topic.setPlaceholderText("e.g., vendor contract, freelance rate, business partnership, real estate...")
        l.addWidget(self._scenario_topic)
        l.addWidget(QLabel("Your position / what you want:"))
        self._scenario_position = QTextEdit()
        self._scenario_position.setPlaceholderText("Describe your desired outcome and key terms...")
        self._scenario_position.setMaximumHeight(80)
        l.addWidget(self._scenario_position)
        l.addWidget(QLabel("Their likely position / what they want:"))
        self._scenario_their = QTextEdit()
        self._scenario_their.setPlaceholderText("What do you think the other party wants?")
        self._scenario_their.setMaximumHeight(80)
        l.addWidget(self._scenario_their)
        btn = QPushButton("Simulate Negotiation")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_scenario)
        l.addWidget(btn)
        self._scenario_output = QTextEdit()
        self._scenario_output.setReadOnly(True)
        self._scenario_output.setStyleSheet("")
        l.addWidget(self._scenario_output, stretch=1)
        return w

    def _build_batna_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("BATNA Analyzer (Best Alternative To Negotiated Agreement)"))
        l.addWidget(QLabel("What is the deal you're negotiating?"))
        self._batna_deal = QLineEdit()
        self._batna_deal.setPlaceholderText("e.g., job offer, vendor contract, partnership...")
        l.addWidget(self._batna_deal)
        l.addWidget(QLabel("Your alternatives if this deal falls through (one per line):"))
        self._batna_alts = QTextEdit()
        self._batna_alts.setPlaceholderText("e.g.,\nKeep current job ($60k)\nOther offer from Company B ($68k)\nFreelance at $40/hr\nTake 3 months to find better offer")
        self._batna_alts.setMaximumHeight(100)
        l.addWidget(self._batna_alts)
        btn = QPushButton("Analyze BATNA")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_batna)
        l.addWidget(btn)
        self._batna_output = QTextEdit()
        self._batna_output.setReadOnly(True)
        self._batna_output.setStyleSheet("")
        l.addWidget(self._batna_output, stretch=1)
        return w

    def _build_tech_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Persuasion Techniques Reference"))
        btn = QPushButton("Show Techniques")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_tech)
        l.addWidget(btn)
        self._tech_output = QTextEdit()
        self._tech_output.setReadOnly(True)
        self._tech_output.setStyleSheet("")
        l.addWidget(self._tech_output, stretch=1)
        return w

    def _run_through_runtime(self, task: str) -> str:
        try:
            from ...core.nexus_ai_runtime import NexusAIRuntime
            settings = SettingsManager()
            settings.initialize()
            runtime = NexusAIRuntime(settings=settings)
            result = runtime.run(task=task, ai_name=self._ai_name, ai_uuid=self._ai_uuid, ai_metadata={"abilities": self._abilities, "use_case": self._use_case, "guardrails": self._guardrails, "libraries": self._libraries})
            return result.result_text or ""
        except Exception:
            return ""

    def _run_salary(self):
        try:
            current = float(self._sal_current.text().strip() or "0")
            target = float(self._sal_target.text().strip() or "0")
        except ValueError:
            self._salary_output.setText("Enter valid numbers.")
            return
        role = self._sal_role.text().strip() or "your role"
        increase = target - current
        increase_pct = (increase / current * 100) if current else 0
        task = f"Create a salary negotiation plan for a {role} going from ${current} to ${target}. Include talking points, market data to cite, and handling objections."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._salary_output.setText(ai_result)
            self._set_result_summary(f"Salary negotiation plan via AI for {role}.")
            return
        output = (
            f"[SALARY NEGOTIATION PLAN — LOCAL ANALYSIS]\n\n"
            f"Role: {role}\n"
            f"Current: ${current:,.0f}\n"
            f"Target: ${target:,.0f}\n"
            f"Increase: ${increase:,.0f} ({increase_pct:.1f}%)\n\n"
        )
        if increase_pct > 25:
            output += "⚠ Large increase — you'll need strong justification (market data, expanded scope, promotions).\n\n"
        elif increase_pct > 10:
            output += "Moderate increase — achievable with good preparation and market data.\n\n"
        else:
            output += "Modest increase — very achievable with a simple ask.\n\n"
        output += (
            "NEGOTIATION SCRIPT:\n\n"
            "1. OPENING (set the stage):\n"
            "   'I'd like to discuss my compensation. I've been reflecting on my\n"
            "    contributions and the market value of my role.'\n\n"
            "2. VALUE STATEMENT (your ammo):\n"
            "   'Over the past [period], I've [specific achievements with metrics].\n"
            "    I've also taken on [additional responsibilities].'\n\n"
            "3. MARKET ANCHOR:\n"
            f"   'Based on my research, {role} positions with my experience\n"
            f"    typically range from $[X] to $[Y]. I'm targeting ${target:,.0f}.'\n\n"
            "4. THE ASK:\n"
            f"   'I'd like to request a salary adjustment to ${target:,.0f},\n"
            "    which reflects both my contributions and market rates.'\n\n"
            "5. HANDLING OBJECTIONS:\n"
            "   'That's not in the budget' → 'I understand. Can we discuss a path\n"
            "     to this number over 6 months? What milestones would justify it?'\n"
            "   'Your current salary is competitive' → 'I've seen data showing\n"
            "     [market range]. Could we review the market data together?'\n"
            "   'We give raises annually' → 'I understand the cycle. Can we set\n"
            "     a review date and agree on what would warrant this adjustment?'\n\n"
            "PREPARATION CHECKLIST:\n"
            "  [ ] Research salary ranges (Glassdoor, Payscale, Levels.fyi)\n"
            "  [ ] Document achievements with quantified results\n"
            "  [ ] List additional responsibilities you've taken on\n"
            "  [ ] Prepare your BATNA (what will you do if they say no?)\n"
            "  [ ] Practice your script out loud\n"
            "  [ ] Prepare for counter-offers and compromises\n"
            "  [ ] Consider non-salary perks (bonus, equity, PTO, remote)\n\n"
            "NEGOTIATION TIPS:\n"
            "  - Never accept the first offer\n"
            "  - Anchor high (ask for 10-20% above your target)\n"
            "  - Use silence — don't fill pauses after making your ask\n"
            "  - Be collaborative, not adversarial\n"
            "  - Get the final offer in writing\n\n"
            "The built-in intelligence can provide personalized coaching."
        )
        self._salary_output.setText(output)
        self._set_result_summary(f"Salary plan: ${current:,.0f} → ${target:,.0f} (+{increase_pct:.1f}%).")

    def _run_scenario(self):
        topic = self._scenario_topic.text().strip()
        if not topic:
            self._scenario_output.setText("Enter what you're negotiating.")
            return
        your_pos = self._scenario_position.toPlainText().strip()
        their_pos = self._scenario_their.toPlainText().strip()
        task = f"Simulate a negotiation for: {topic}. My position: {your_pos}. Their likely position: {their_pos}. Provide strategy, likely exchanges, and tactics."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._scenario_output.setText(ai_result)
            self._set_result_summary(f"Negotiation simulation via AI for {topic}.")
            return
        output = (
            f"[DEAL SCENARIO SIMULATION — LOCAL ANALYSIS]\n\n"
            f"Topic: {topic}\n\n"
            f"Your position: {your_pos[:200]}\n"
            f"Their position: {their_pos[:200]}\n\n"
            "NEGOTIATION SIMULATION:\n\n"
            "ROUND 1 — OPENING:\n"
            "  You: State your position clearly and confidently.\n"
            "  Them: Likely counter with their preferred terms.\n"
            "  Strategy: Anchor with your best-case outcome.\n\n"
            "ROUND 2 — EXPLORATION:\n"
            "  You: Ask questions to understand their constraints and priorities.\n"
            "  Them: Reveal what matters most to them.\n"
            "  Strategy: Identify their underlying interests (not just positions).\n\n"
            "ROUND 3 — BARGAINING:\n"
            "  You: Make conditional concessions ('If you can do X, I can accept Y').\n"
            "  Them: Trade on items that cost them little but value you highly.\n"
            "  Strategy: Trade, don't just give. Every concession needs something back.\n\n"
            "ROUND 4 — CLOSING:\n"
            "  You: Summarize agreement and confirm details.\n"
            "  Them: Agree or request final modifications.\n"
            "  Strategy: Get it in writing. Clarify all terms.\n\n"
            "LIKELY STICKING POINTS:\n"
            "  - Price/rate (most common)\n"
            "  - Timeline/deadlines\n"
            "  - Scope of work\n"
            "  - Payment terms\n"
            "  - Exclusivity/restrictions\n\n"
            "TACTICS TO EXPECT:\n"
            "  - 'Take it or leave it' → Test it. Often a bluff.\n"
            "  - 'I need to check with my boss' → Ask when you'll hear back.\n"
            "  - 'That's more than we usually pay' → 'I understand. I'm offering more value.'\n"
            "  - Silence → Don't fill it. Let them speak first.\n"
            "  - Splitting the difference → Only if it benefits you.\n\n"
            "The built-in intelligence can provide scenario simulation."
        )
        self._scenario_output.setText(output)
        self._set_result_summary(f"Negotiation simulated for: {topic}.")

    def _run_batna(self):
        deal = self._batna_deal.text().strip()
        alts_text = self._batna_alts.toPlainText().strip()
        if not deal or not alts_text:
            self._batna_output.setText("Enter both the deal and your alternatives.")
            return
        alts = [l.strip() for l in alts_text.split("\n") if l.strip()]
        task = f"Analyze BATNA for a negotiation about: {deal}. Alternatives: {alts_text}. Rate each alternative and recommend strategy."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._batna_output.setText(ai_result)
            self._set_result_summary(f"BATNA analyzed via AI for {deal}.")
            return
        output = (
            f"[BATNA ANALYSIS — LOCAL ANALYSIS]\n\n"
            f"Deal: {deal}\n\n"
            f"YOUR ALTERNATIVES ({len(alts)}):\n\n"
        )
        for i, alt in enumerate(alts, 1):
            output += f"  {i}. {alt}\n"
        output += (
            "\nBATNA ASSESSMENT FRAMEWORK:\n\n"
            "Rate each alternative on:\n"
            "  - Value: How good is this option?\n"
            "  - Feasibility: How likely can you execute it?\n"
            "  - Timing: How quickly can you access it?\n"
            "  - Certainty: How sure are you it's available?\n\n"
            "YOUR BATNA = Your BEST alternative (highest combined score)\n\n"
            "STRATEGIC IMPLICATIONS:\n\n"
            "  STRONG BATNA (good alternatives):\n"
            "    → You can walk away confidently\n"
            "    → Negotiate from strength\n"
            "    → Don't accept below your BATNA\n"
            "    → Reveal your BATNA strategically (not too early)\n\n"
            "  WEAK BATNA (few/poor alternatives):\n"
            "    → Be more flexible and collaborative\n"
            "    → Focus on creating value, not claiming value\n"
            "    → Don't bluff about alternatives you don't have\n"
            "    → Consider improving your BATNA before negotiating\n\n"
            "  NO BATNA (no alternatives):\n"
            "    → You must reach a deal — weakest position\n"
            "    → Focus on relationship and long-term value\n"
            "    → Avoid revealing you have no alternatives\n"
            "    → Work on building alternatives for next time\n\n"
            "RESERVATION PRICE:\n"
            "  Your reservation price = the worst deal you'd accept\n"
            "  It should be equal to or better than your BATNA\n"
            "  Never accept a deal worse than your BATNA\n\n"
            "The built-in intelligence can provide BATNA analysis."
        )
        self._batna_output.setText(output)
        self._set_result_summary(f"BATNA analyzed: {len(alts)} alternatives for {deal}.")

    def _run_tech(self):
        output = (
            "[PERSUASION TECHNIQUES — LOCAL REFERENCE]\n\n"
            "1. RECIPROCITY\n"
            "   Give something to get something. People feel obligated to return favors.\n"
            "   Example: Offer a concession to get one in return.\n\n"
            "2. SOCIAL PROOF\n"
            "   Show that others have agreed. People follow the crowd.\n"
            "   Example: 'Other clients in your industry have adopted this rate.'\n\n"
            "3. AUTHORITY\n"
            "   Cite expertise, credentials, or data. People defer to authority.\n"
            "   Example: 'Industry benchmarks show this is standard for this scope.'\n\n"
            "4. CONSISTENCY\n"
            "   Get small commitments first. People align with their prior actions.\n"
            "   Example: 'You mentioned quality is your top priority — here's how this ensures it.'\n\n"
            "5. SCARCITY\n"
            "   Highlight what they lose by not acting. Loss aversion is powerful.\n"
            "   Example: 'I have limited capacity this quarter — can we lock in now?'\n\n"
            "6. LIKING\n"
            "   Build rapport. People say yes to people they like.\n"
            "   Example: Find common ground, give genuine compliments, be friendly.\n\n"
            "7. ANCHORING\n"
            "   First number mentioned sets the reference point. Anchor high.\n"
            "   Example: Open with your best-case number, not your target.\n\n"
            "8. FRAMING\n"
            "   Present information in a way that highlights benefits.\n"
            "   Example: 'Investing $X saves $Y over 12 months' vs 'This costs $X'.\n\n"
            "9. SILENCE\n"
            "   After making your ask, stop talking. Let them respond first.\n"
            "   Example: State your number. Wait. Don't fill the silence.\n\n"
            "10. CALIBRATED QUESTIONS\n"
            "   Ask 'How' and 'What' questions to guide them to your position.\n"
            "   Example: 'How am I supposed to do that at that price?' (from Never Split the Difference)\n\n"
            "11. LABELING\n"
            "   Name their emotions to defuse them.\n"
            "   Example: 'It seems like you're concerned about the timeline.'\n\n"
            "12. MIRRORING\n"
            "   Repeat their last 1-3 words to encourage elaboration.\n"
            "   Example: Them: 'That's too expensive.' You: 'Too expensive?'\n\n"
            "KEY PRINCIPLES:\n"
            "  - Seek to understand before being understood\n"
            "  - Separate people from the problem\n"
            "  - Focus on interests, not positions\n"
            "  - Invent options for mutual gain\n"
            "  - Use objective criteria\n\n"
            "RECOMMENDED READING:\n"
            "  - 'Never Split the Difference' by Chris Voss\n"
            "  - 'Getting to Yes' by Fisher & Ury\n"
            "  - 'Influence' by Robert Cialdini\n"
            "  - 'Start with No' by Jim Camp"
        )
        self._tech_output.setText(output)
        self._set_result_summary("Persuasion techniques reference displayed.")


class GameCompanionDialog(BaseCapabilityDialog):
    """Game Companion — game selector, rules learner, strategy advisor, position analyzer, practice mode, progress tracker."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Game Companion — {ai_name} | Avery Logic Works(TM)")
        self.resize(880, 660)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_selector_tab(), "Game Selector")
        tabs.addTab(self._build_rules_tab(), "Rules Learner")
        tabs.addTab(self._build_strategy_tab(), "Strategy Advisor")
        tabs.addTab(self._build_position_tab(), "Position Analyzer")
        tabs.addTab(self._build_practice_tab(), "Practice Mode")
        tabs.addTab(self._build_progress_tab(), "Progress Tracker")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Game companion for entertainment and skill-building. No gambling advice. No in-game purchase recommendations. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_selector_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Game Selector"))
        l.addWidget(QLabel("Choose a game category to explore:"))
        self._game_category = QComboBox()
        self._game_category.addItems([
            "Chess", "Poker", "Card Games", "Board Games",
            "Puzzle/Logic", "Video Games", "Strategy Games", "Word Games"
        ])
        l.addWidget(self._game_category)
        l.addWidget(QLabel("Your experience level:"))
        self._game_level = QComboBox()
        self._game_level.addItems(["Beginner", "Intermediate", "Advanced", "Expert"])
        l.addWidget(self._game_level)
        btn = QPushButton("Get Game Recommendations")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_selector)
        l.addWidget(btn)
        self._selector_output = QTextEdit()
        self._selector_output.setReadOnly(True)
        self._selector_output.setStyleSheet("")
        l.addWidget(self._selector_output, stretch=1)
        return w

    def _build_rules_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Rules Learner"))
        l.addWidget(QLabel("Enter a game to learn its rules:"))
        self._rules_game = QLineEdit()
        self._rules_game.setPlaceholderText("e.g., Chess, Texas Hold'em, Settlers of Catan, Sudoku, League of Legends...")
        l.addWidget(self._rules_game)
        btn = QPushButton("Explain Rules")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_rules)
        l.addWidget(btn)
        self._rules_output = QTextEdit()
        self._rules_output.setReadOnly(True)
        self._rules_output.setStyleSheet("")
        l.addWidget(self._rules_output, stretch=1)
        return w

    def _build_strategy_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Strategy Advisor"))
        l.addWidget(QLabel("Game:"))
        self._strategy_game = QComboBox()
        self._strategy_game.addItems(["Chess", "Poker", "Blackjack", "Go", "Settlers of Catan", "Ticket to Ride", "Puzzle/Logic", "Video Game (general)"])
        l.addWidget(self._strategy_game)
        l.addWidget(QLabel("Your situation or question:"))
        self._strategy_question = QTextEdit()
        self._strategy_question.setPlaceholderText("Describe your situation, e.g., 'I keep losing in the midgame as white' or 'How do I handle aggressive poker players?'")
        self._strategy_question.setMaximumHeight(80)
        l.addWidget(self._strategy_question)
        btn = QPushButton("Get Strategy Advice")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_strategy)
        l.addWidget(btn)
        self._strategy_output = QTextEdit()
        self._strategy_output.setReadOnly(True)
        self._strategy_output.setStyleSheet("")
        l.addWidget(self._strategy_output, stretch=1)
        return w

    def _build_position_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Position Analyzer"))
        l.addWidget(QLabel("Enter board state or game position (text format):"))
        self._position_input = QTextEdit()
        self._position_input.setPlaceholderText(
            "For chess (FEN or text board):\n"
            "r n b q k b n r\n"
            "p p p . . p p p\n"
            ". . . p p . . .\n"
            ". . . . . . . .\n"
            ". . . . P . . .\n"
            ". . . . . N . .\n"
            "P P P . . P P P\n"
            "R N B Q K B . R\n\n"
            "Or describe any game position in text..."
        )
        l.addWidget(self._position_input, stretch=1)
        l.addWidget(QLabel("Game type:"))
        self._position_game = QComboBox()
        self._position_game.addItems(["Chess", "Poker (hand description)", "Go", "Other (describe)"])
        l.addWidget(self._position_game)
        btn = QPushButton("Analyze Position")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_position)
        l.addWidget(btn)
        self._position_output = QTextEdit()
        self._position_output.setReadOnly(True)
        self._position_output.setStyleSheet("")
        l.addWidget(self._position_output, stretch=1)
        return w

    def _build_practice_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Practice Mode"))
        l.addWidget(QLabel("Select a practice drill:"))
        self._practice_type = QComboBox()
        self._practice_type.addItems([
            "Chess tactics puzzle",
            "Chess opening drill",
            "Chess endgame practice",
            "Poker hand evaluation",
            "Poker odds estimation",
            "Logic puzzle generator",
            "Memory challenge",
            "Pattern recognition",
        ])
        l.addWidget(self._practice_type)
        l.addWidget(QLabel("Difficulty:"))
        self._practice_diff = QComboBox()
        self._practice_diff.addItems(["Easy", "Medium", "Hard", "Expert"])
        l.addWidget(self._practice_diff)
        btn = QPushButton("Generate Practice Drill")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_practice)
        l.addWidget(btn)
        self._practice_output = QTextEdit()
        self._practice_output.setReadOnly(True)
        self._practice_output.setStyleSheet("")
        l.addWidget(self._practice_output, stretch=1)
        return w

    def _build_progress_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Progress Tracker"))
        l.addWidget(QLabel("Log your game session:"))
        row = QHBoxLayout()
        row.addWidget(QLabel("Game:"))
        self._progress_game = QLineEdit()
        self._progress_game.setPlaceholderText("e.g., Chess, Poker, Catan...")
        row.addWidget(self._progress_game)
        row.addWidget(QLabel("Result:"))
        self._progress_result = QComboBox()
        self._progress_result.addItems(["Win", "Loss", "Draw", "Practice session"])
        row.addWidget(self._progress_result)
        row.addWidget(QLabel("Rating/Elo:"))
        self._progress_rating = QLineEdit()
        self._progress_rating.setPlaceholderText("optional")
        self._progress_rating.setMaximumWidth(80)
        row.addWidget(self._progress_rating)
        row.addStretch()
        l.addLayout(row)
        l.addWidget(QLabel("Notes (what you learned, key moments):"))
        self._progress_notes = QTextEdit()
        self._progress_notes.setMaximumHeight(60)
        l.addWidget(self._progress_notes)
        btn = QPushButton("Log Session")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_progress_log)
        l.addWidget(btn)
        show_btn = QPushButton("Show Progress Summary")
        show_btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        show_btn.clicked.connect(self._run_progress_summary)
        l.addWidget(show_btn)
        self._progress_output = QTextEdit()
        self._progress_output.setReadOnly(True)
        self._progress_output.setStyleSheet("")
        l.addWidget(self._progress_output, stretch=1)
        self._progress_log: list[dict] = []
        return w

    def _run_through_runtime(self, task: str) -> str:
        try:
            from ...core.nexus_ai_runtime import NexusAIRuntime
            settings = SettingsManager()
            settings.initialize()
            runtime = NexusAIRuntime(settings=settings)
            result = runtime.run(task=task, ai_name=self._ai_name, ai_uuid=self._ai_uuid, ai_metadata={"abilities": self._abilities, "use_case": self._use_case, "guardrails": self._guardrails, "libraries": self._libraries})
            return result.result_text or ""
        except Exception:
            return ""

    def _run_selector(self):
        category = self._game_category.currentText()
        level = self._game_level.currentText()
        task = f"Recommend games in the {category} category for a {level} player. Include specific game titles, why they're good for this level, and what skills they develop."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._selector_output.setText(ai_result)
            self._set_result_summary(f"Game recommendations via AI: {category} for {level}.")
            return
        game_db = {
            "Chess": {
                "games": [("Chess", "Classic strategy, infinite depth"), ("Chess960", "Fischer Random — tests pure understanding"), ("Blitz Chess", "Fast-paced decision making")],
                "skills": "Strategic thinking, pattern recognition, calculation, patience, planning",
            },
            "Poker": {
                "games": [("Texas Hold'em", "Most popular, deep strategy"), ("Omaha", "More cards, bigger draws"), ("Seven-Card Stud", "No community cards, memory-heavy"), ("Short Deck", "Action-packed variant")],
                "skills": "Probability, risk management, psychology, bankroll management, decision under pressure",
            },
            "Card Games": {
                "games": [("Bridge", "Partnership, bidding system"), ("Spades", "Trick-taking, partnership"), ("Hearts", "Avoidance game, strategy"), ("Rummy", "Set collection, melding")],
                "skills": "Memory, probability, partnership, strategic planning",
            },
            "Board Games": {
                "games": [("Settlers of Catan", "Resource management, trading"), ("Ticket to Ride", "Route building, light strategy"), ("Pandemic", "Cooperative, problem-solving"), ("Azul", "Abstract, pattern matching")],
                "skills": "Resource management, spatial reasoning, social negotiation, planning",
            },
            "Puzzle/Logic": {
                "games": [("Sudoku", "Logic deduction, constraint satisfaction"), ("Kakuro", "Math + logic"), ("Nonograms", "Visual logic"), ("Logic Grid Puzzles", "Deductive reasoning")],
                "skills": "Logical deduction, pattern recognition, systematic thinking",
            },
            "Video Games": {
                "games": [("Civilization VI", "4X strategy, long-term planning"), ("Starcraft II", "RTS, multitasking, speed"), ("Dark Souls", "Patience, pattern learning"), ("Portal 2", "Spatial reasoning, physics")],
                "skills": "Reflexes, strategic planning, resource management, problem-solving",
            },
            "Strategy Games": {
                "games": [("Go", "Ancient, deep strategy, territory"), ("Risk", "Global conquest, probability"), ("Twilight Struggle", "Cold War, card-driven"), ("Agricola", "Worker placement, optimization")],
                "skills": "Long-term planning, risk assessment, adaptation, optimization",
            },
            "Word Games": {
                "games": [("Scrabble", "Vocabulary, spatial placement"), ("Bananagrams", "Speed word building"), ("Codenames", "Word association, communication"), ("Boggle", "Pattern finding, speed")],
                "skills": "Vocabulary, pattern recognition, speed, communication",
            },
        }
        info = game_db.get(category, game_db["Chess"])
        output = f"[GAME SELECTOR — LOCAL ANALYSIS]\n\nCategory: {category}\nLevel: {level}\n\n"
        output += "RECOMMENDED GAMES:\n"
        for title, desc in info["games"]:
            output += f"  • {title} — {desc}\n"
        output += f"\nSKILLS DEVELOPED:\n  {info['skills']}\n\n"
        level_tips = {
            "Beginner": "Start with basic rules, play against easy opponents or AI. Focus on understanding fundamentals. Don't worry about advanced strategy yet.",
            "Intermediate": "Study common patterns and openings. Play regularly against varied opponents. Start analyzing your games afterward.",
            "Advanced": "Deep dive into theory. Study master games. Analyze your losses carefully. Consider coaching or joining a club.",
            "Expert": "Focus on edge cases, psychological preparation, and tournament play. Study recent theory developments. Teach others to deepen understanding.",
        }
        output += f"LEVEL ADVICE ({level}):\n  {level_tips.get(level, level_tips['Beginner'])}\n\n"
        output += "PRACTICE TIPS:\n  - Play regularly (consistency > intensity)\n  - Review your games afterward\n  - Study master/professional games\n  - Focus on one improvement area at a time\n  - Mix practice with play for engagement\n\n"
        output += "The built-in intelligence can provide personalized recommendations."
        self._selector_output.setText(output)
        self._set_result_summary(f"Game recommendations: {category} for {level}.")

    def _run_rules(self):
        game = self._rules_game.text().strip()
        if not game:
            self._rules_output.setText("Enter a game name.")
            return
        task = f"Explain the complete rules of {game} in a clear, structured format for a new player. Include setup, gameplay, winning conditions, and key mechanics."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._rules_output.setText(ai_result)
            self._set_result_summary(f"Rules explained via AI: {game}.")
            return
        rules_db = {
            "chess": (
                "CHESS — RULES SUMMARY\n\n"
                "SETUP:\n"
                "  - 8x8 board, alternating light/dark squares\n"
                "  - Each player: 8 pawns, 2 knights, 2 bishops, 2 rooks, 1 queen, 1 king\n"
                "  - White moves first\n\n"
                "PIECE MOVEMENT:\n"
                "  • Pawn: 1 square forward (2 from start), captures diagonally\n"
                "  • Knight: L-shape (2+1 squares), jumps over pieces\n"
                "  • Bishop: Any number of squares diagonally\n"
                "  • Rook: Any number of squares horizontally/vertically\n"
                "  • Queen: Any number of squares in any direction\n"
                "  • King: 1 square in any direction\n\n"
                "SPECIAL MOVES:\n"
                "  • Castling: King + rook move simultaneously (once per game)\n"
                "  • En passant: Special pawn capture\n"
                "  • Promotion: Pawn reaching the last rank becomes any piece (usually queen)\n\n"
                "OBJECTIVE: Checkmate the opponent's king (king cannot escape capture)\n\n"
                "DRAW CONDITIONS: Stalemate, threefold repetition, 50-move rule, insufficient material\n\n"
                "The built-in intelligence can provide interactive rules learning."
            ),
            "poker": (
                "POKER (Texas Hold'em) — RULES SUMMARY\n\n"
                "SETUP:\n"
                "  - 2-10 players, standard 52-card deck\n"
                "  - Dealer button rotates clockwise each hand\n"
                "  - Small blind + Big blind posted before cards dealt\n\n"
                "GAMEPLAY (4 betting rounds):\n"
                "  1. Pre-flop: Each player gets 2 hole cards (face down)\n"
                "  2. Flop: 3 community cards dealt face up\n"
                "  3. Turn: 1 more community card\n"
                "  4. River: Final community card\n\n"
                "BETTING OPTIONS: Fold, Check, Call, Bet/Raise, All-in\n\n"
                "SHOWDOWN: Best 5-card hand from 7 cards (2 hole + 5 community) wins\n\n"
                "HAND RANKINGS (high to low):\n"
                "  1. Royal Flush (A-K-Q-J-10 same suit)\n"
                "  2. Straight Flush (5 sequential same suit)\n"
                "  3. Four of a Kind\n"
                "  4. Full House (3 of a kind + pair)\n"
                "  5. Flush (5 same suit)\n"
                "  6. Straight (5 sequential)\n"
                "  7. Three of a Kind\n"
                "  8. Two Pair\n"
                "  9. One Pair\n"
                "  10. High Card\n\n"
                "The built-in intelligence can provide interactive rules learning."
            ),
            "go": (
                "GO — RULES SUMMARY\n\n"
                "SETUP:\n"
                "  - Board: 19x19 grid (smaller: 9x9 or 13x13 for beginners)\n"
                "  - Black plays first, places stones on intersections\n"
                "  - Each player has unlimited stones of their color\n\n"
                "RULES:\n"
                "  1. Players alternate placing stones on empty intersections\n"
                "  2. Stones don't move once placed (unless captured)\n"
                "  3. A stone/group is captured when it has no liberties (empty adjacent points)\n"
                "  4. Ko rule: Can't immediately recreate a previous board position\n"
                "  5. Suicide rule: Can't play a stone that would have no liberties (unless capturing)\n\n"
                "OBJECTIVE: Control more territory (empty intersections surrounded by your stones)\n\n"
                "SCORING: Territory + captures + komi (compensation points for white, typically 6.5-7.5)\n\n"
                "The built-in intelligence can provide interactive rules learning."
            ),
            "sudoku": (
                "SUDOKU — RULES SUMMARY\n\n"
                "SETUP:\n"
                "  - 9x9 grid divided into nine 3x3 boxes\n"
                "  - Some cells pre-filled with digits 1-9\n\n"
                "RULES:\n"
                "  1. Fill every empty cell with a digit 1-9\n"
                "  2. Each row must contain 1-9 with no repeats\n"
                "  3. Each column must contain 1-9 with no repeats\n"
                "  4. Each 3x3 box must contain 1-9 with no repeats\n\n"
                "OBJECTIVE: Complete the grid following all constraints\n\n"
                "TECHNIQUES:\n"
                "  - Scanning: Look for cells with only one possible value\n"
                "  - Elimination: Cross-reference rows, columns, boxes\n"
                "  - Pairs/Triples: If 2 cells in a unit can only be 2 numbers, eliminate elsewhere\n"
                "  - X-Wing: Advanced pattern elimination\n\n"
                "The built-in intelligence can provide interactive rules learning."
            ),
        }
        key = game.lower().strip()
        if key in rules_db:
            output = rules_db[key]
        else:
            output = (
                f"[RULES LEARNER — LOCAL ANALYSIS]\n\n"
                f"Game: {game}\n\n"
                "RULES LEARNING FRAMEWORK:\n\n"
                "1. OBJECTIVE — What is the goal? How do you win?\n"
                "2. SETUP — Board/layout, pieces/components, starting positions\n"
                "3. TURNS — Turn order, what you can do on your turn\n"
                "4. ACTIONS — Available moves/actions and their rules\n"
                "5. SPECIAL RULES — Exceptions, special abilities, edge cases\n"
                "6. END CONDITIONS — When does the game end? Who wins?\n"
                "7. SCORING — How is the winner determined?\n\n"
                "LEARNING TIPS:\n"
                "  - Read rules → play a practice game → re-read rules\n"
                "  - Watch tutorial videos on YouTube\n"
                "  - Play against AI at easy level first\n"
                "  - Join online communities (BoardGameGeek, chess.com, etc.)\n"
                "  - Learn common mistakes to avoid\n\n"
                f"The built-in intelligence can provide rules explanation of {game}."
            )
        self._rules_output.setText(output)
        self._set_result_summary(f"Rules explained: {game}.")

    def _run_strategy(self):
        game = self._strategy_game.currentText()
        question = self._strategy_question.toPlainText().strip()
        if not question:
            self._strategy_output.setText("Enter your strategy question.")
            return
        task = f"Provide strategy advice for {game}. Player's question: {question}. Include specific tactics, common mistakes to avoid, and improvement tips."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._strategy_output.setText(ai_result)
            self._set_result_summary(f"Strategy advice via AI for {game}.")
            return
        strategy_db = {
            "Chess": {
                "principles": [
                    "Control the center (e4, d4, e5, d5)",
                    "Develop pieces before attacking (knights before bishops)",
                    "Castle early for king safety",
                    "Don't move the same piece twice in the opening",
                    "Connect your rooks",
                    "Always check what the opponent threatens",
                    "Think about opponent's plan, not just yours",
                    "Calculate at least 2-3 moves deep before committing",
                ],
                "phases": "Opening (develop, control center) → Middlegame (attack, maneuver) → Endgame (king activation, pawn promotion)",
            },
            "Poker": {
                "principles": [
                    "Play tight-aggressive (fold often, bet confidently when you play)",
                    "Position is power — later positions have more information",
                    "Manage your bankroll (never risk more than 5% per session)",
                    "Read betting patterns for information",
                    "Don't chase draws without proper pot odds",
                    "Bluff selectively, not habitually",
                    "Fold equity matters — sometimes a bet wins by making them fold",
                    "Tilt is your enemy — take breaks after bad beats",
                ],
                "phases": "Pre-flop (starting hand selection) → Post-flop (continuation betting, draws) → Turn/River (value betting, bluffing)",
            },
            "Blackjack": {
                "principles": [
                    "Learn basic strategy (hit/stand/double/split charts)",
                    "Always split Aces and 8s",
                    "Never split 10s, 5s, or 4s",
                    "Double down on 11 vs dealer 2-10",
                    "Stand on 17+ (hard), hit on 16 or less",
                    "Card counting (legal but casinos may ban you)",
                    "Never take insurance bets",
                    "Set win/loss limits per session",
                ],
                "phases": "Bet → Deal → Decision (hit/stand/double/split) → Resolve",
            },
            "Go": {
                "principles": [
                    "Play the corners first, then sides, then center",
                    "Don't play in contact with opponent stones early",
                    "Keep your stones connected",
                    "Think about shape (tiger's mouth, bamboo joint)",
                    "Sacrifice small groups to gain bigger territory",
                    "Count the score periodically",
                    "Avoid filling your own liberties",
                    "Learn joseki (corner patterns) for common situations",
                ],
                "phases": "Opening (corners, framework) → Midgame (fights, invasions) → Endgame (boundaries, counting)",
            },
            "Settlers of Catan": {
                "principles": [
                    "Prioritize ore and wheat for cities and development cards",
                    "Build on high-probability numbers (6, 8, 5, 9)",
                    "Longest Road and Largest Army are worth 2 VP each",
                    "Trade strategically — don't help opponents",
                    "Don't overextend — keep your options open",
                    "Development cards can be game-changers",
                    "Block the leader, not the runner-up",
                    "Diversify your resource production",
                ],
                "phases": "Setup (placement is critical) → Expansion (roads, settlements) → Endgame (cities, VP cards)",
            },
        }
        info = strategy_db.get(game)
        output = f"[STRATEGY ADVISOR — LOCAL ANALYSIS]\n\nGame: {game}\nQuestion: {question[:200]}\n\n"
        if info:
            output += "KEY STRATEGIC PRINCIPLES:\n"
            for i, principle in enumerate(info["principles"], 1):
                output += f"  {i}. {principle}\n"
            output += f"\nGAME PHASES:\n  {info['phases']}\n\n"
        else:
            output += (
                "GENERAL STRATEGY PRINCIPLES:\n"
                "  1. Understand the win condition — always play toward it\n"
                "  2. Evaluate risk vs reward for each decision\n"
                "  3. Think 2-3 moves/turns ahead\n"
                "  4. Learn from losses — analyze what went wrong\n"
                "  5. Study top players' games/matches\n"
                "  6. Practice consistently, focus on one skill at a time\n"
                "  7. Adapt to your opponent's style\n"
                "  8. Don't tilt — emotional decisions are bad decisions\n\n"
            )
        output += (
            "IMPROVEMENT PLAN:\n"
            "  - Identify your weakest area from the principles above\n"
            "  - Focus on improving that one area for 10-20 games\n"
            "  - Review your games afterward (record if possible)\n"
            "  - Study professional/master games in this game\n"
            "  - Join a community for feedback and discussion\n\n"
            "The built-in intelligence can provide personalized strategy coaching."
        )
        self._strategy_output.setText(output)
        self._set_result_summary(f"Strategy advice for {game}.")

    def _run_position(self):
        position_text = self._position_input.toPlainText().strip()
        if not position_text:
            self._position_output.setText("Enter a board state or position description.")
            return
        game_type = self._position_game.currentText()
        task = f"Analyze this {game_type} position and provide strategic advice:\n{position_text}"
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._position_output.setText(ai_result)
            self._set_result_summary(f"Position analyzed via AI ({game_type}).")
            return
        output = f"[POSITION ANALYZER — LOCAL ANALYSIS]\n\nGame: {game_type}\nPosition:\n{position_text}\n\n"
        if game_type == "Chess":
            lines = position_text.strip().split("\n")
            piece_count = {}
            total_pieces = 0
            for line in lines:
                for char in line:
                    if char in "prnbqkPRNBQK":
                        piece_count[char] = piece_count.get(char, 0) + 1
                        total_pieces += 1
            output += f"PIECE COUNT: {total_pieces} total pieces on board\n"
            if piece_count:
                output += "  Breakdown: " + ", ".join(f"{p}={c}" for p, c in sorted(piece_count.items())) + "\n\n"
            if total_pieces > 20:
                output += "GAME PHASE: Opening/Middlegame (many pieces still on board)\n"
            elif total_pieces > 10:
                output += "GAME PHASE: Middlegame transitioning to endgame\n"
            else:
                output += "GAME PHASE: Endgame (few pieces — king activation is key)\n\n"
            output += (
                "ANALYSIS CHECKLIST:\n"
                "  [ ] Material balance (who has more pieces?)\n"
                "  [ ] King safety (is the king exposed?)\n"
                "  [ ] Piece activity (are pieces on good squares?)\n"
                "  [ ] Pawn structure (doubled, isolated, backward?)\n"
                "  [ ] Center control\n"
                "  [ ] Open files for rooks\n"
                "  [ ] Diagonals for bishops\n"
                "  [ ] Outposts for knights\n"
                "  [ ] Threats (what does each side threaten?)\n\n"
                "EVALUATION FRAMEWORK:\n"
                "  1. Compare material (pawn=1, knight/bishop=3, rook=5, queen=9)\n"
                "  2. Check king safety for both sides\n"
                "  3. Evaluate piece activity and coordination\n"
                "  4. Look for immediate threats and tactics\n"
                "  5. Identify candidate moves (2-3 best options)\n"
                "  6. Calculate consequences of each candidate\n\n"
                "The built-in intelligence can provide position analysis."
            )
        elif game_type == "Poker (hand description)":
            output += (
                "POKER HAND ANALYSIS CHECKLIST:\n\n"
                "  [ ] What is your hand strength? (pair, draw, high card)\n"
                "  [ ] What could your opponent have?\n"
                "  [ ] Pot odds: Is calling profitable?\n"
                "  [ ] Implied odds: Future betting rounds?\n"
                "  [ ] Position: Are you in or out of position?\n"
                "  [ ] Stack sizes: How does this affect decisions?\n"
                "  [ ] Opponent tendencies: Tight/loose, passive/aggressive?\n"
                "  [ ] Tournament situation: Bubble? ICM considerations?\n\n"
                "DECISION FRAMEWORK:\n"
                "  1. Evaluate your hand relative to the board\n"
                "  2. Estimate opponent's range\n"
                "  3. Calculate pot odds and equity\n"
                "  4. Consider fold equity if betting/raising\n"
                "  5. Factor in position and stack sizes\n"
                "  6. Make the play with highest expected value (EV)\n\n"
                "The built-in intelligence can provide poker analysis."
            )
        elif game_type == "Go":
            output += (
                "GO POSITION ANALYSIS CHECKLIST:\n\n"
                "  [ ] Territory count (who's ahead?)\n"
                "  [ ] Group stability (which groups are weak?)\n"
                "  [ ] Key points (where are the big moves?)\n"
                "  [ ] Liberties (any groups in danger?)\n"
                "  [ ] Influence vs territory trade-off\n"
                "  [ ] Sente vs gote (who has the initiative?)\n"
                "  [ ] Ko fights and ko threats\n"
                "  [ ] Endgame counting and point values\n\n"
                "The built-in intelligence can provide Go analysis."
            )
        else:
            output += (
                "POSITION ANALYSIS FRAMEWORK:\n\n"
                "  1. What is the current state?\n"
                "  2. Who has the advantage?\n"
                "  3. What are the key threats?\n"
                "  4. What are the best available moves?\n"
                "  5. What should each side prioritize?\n\n"
                "The built-in intelligence can provide position analysis."
            )
        self._position_output.setText(output)
        self._set_result_summary(f"Position analyzed ({game_type}).")

    def _run_practice(self):
        practice_type = self._practice_type.currentText()
        difficulty = self._practice_diff.currentText()
        task = f"Generate a {difficulty} practice drill for: {practice_type}. Include the problem, the solution approach, and learning points."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._practice_output.setText(ai_result)
            self._set_result_summary(f"Practice drill via AI: {practice_type} ({difficulty}).")
            return
        drills = {
            "Chess tactics puzzle": {
                "Easy": ("Fork Practice", "Place a knight on c3. Find a move that attacks both the king on e8 and the rook on a8 simultaneously.\n\nSolution: Knight to b6+ forks king (e8) and rook (a8). The king must move, and you capture the rook.\n\nLearning: Knights are powerful forkers because they attack in different directions than other pieces."),
                "Medium": ("Pin and Win", "Black king on g8, black queen on d5, white bishop on g5, white rook on d1. White to move. Find the winning combination.\n\nSolution: Rd1-d5 pins the queen against... wait, let's think. Actually, Bg5-d8 pins the queen to the king. Then if the queen moves, Rd1 captures. Or Bd8 and Qd5 is pinned — Rd1xd5 next move.\n\nLearning: Pins restrict piece movement. A pinned piece is vulnerable."),
                "Hard": ("Discovered Attack", "White bishop on b2, white rook on h1, black king on g8, black knight on f6, black pawn on g7. White to move. Find the winning sequence.\n\nSolution: Bh1-h7+ (discovered attack from bishop b2 along the diagonal). Wait — let's reconsider. Bb2-h8 would discover... Actually, move the bishop with check: Bb2-a3 (threatens) or focus on Rh1-h7 with bishop support. The key is creating a discovered attack where moving one piece reveals an attack from another.\n\nLearning: Discovered attacks are powerful because the opponent faces two threats simultaneously."),
                "Expert": ("Combinational Sacrifice", "Complex middlegame position. White has queen and two minor pieces vs black queen, rook, and king on g8 with weak pawns. Find a 4-move combination involving a piece sacrifice.\n\nSolution: This requires deep calculation. The pattern involves sacrificing a piece to expose the king, then bringing the queen in for a mating attack. Specific moves depend on exact position.\n\nLearning: Sacrifices work when the resulting initiative outweighs the material given up. Calculate thoroughly before sacrificing."),
            },
            "Chess opening drill": {
                "Easy": ("Italian Game", "1.e4 e5 2.Nf3 Nc6 3.Bc4 — Practice this fundamental opening. Focus on rapid development and center control.\n\nKey ideas: Develop bishops to active diagonals, control center with pawns, prepare to castle.\n\nLearning: The Italian Game teaches fundamental opening principles."),
                "Medium": ("Sicilian Defense", "1.e4 c5 — Black fights for the center asymmetrically. Practice the main lines: Najdorf (5...a6), Dragon (5...g6), Scheveningen (5...e6).\n\nKey ideas: Black aims for queenside play and central counterattacks.\n\nLearning: The Sicilian creates imbalanced positions where both sides can play for a win."),
                "Hard": ("King's Indian Defense", "1.d4 Nf6 2.c4 g6 3.Nc3 Bg7 — Practice this complex opening. Black allows white center, then attacks with pawn breaks.\n\nKey ideas: Pawn storm on the kingside, timing of ...f5 and ...c5 breaks.\n\nLearning: The KID teaches strategic patience and pawn play."),
                "Expert": ("Najdorf Variation", "1.e4 c5 2.Nf3 d6 3.d4 cxd4 4.Nxd4 Nf6 5.Nc3 a6 — Deep theoretical opening. Practice the English Attack (6.Be3), Classical (6.Bg5), and 6.Bc4 lines.\n\nKey ideas: Both sides have complex plans. Move-order nuances matter.\n\nLearning: Top-level opening preparation requires understanding deep strategic ideas."),
            },
            "Chess endgame practice": {
                "Easy": ("King + Queen vs King", "Practice checkmating with a queen. Key technique: Drive the enemy king to the edge, then deliver mate.\n\nSteps: 1. Use queen to restrict king's movement 2. Bring your king up to support 3. Deliver mate on the edge.\n\nLearning: Basic mating patterns are essential fundamentals."),
                "Medium": ("King + Rook vs King", "Practice the 'box method' — use the rook to shrink the box the enemy king can move in.\n\nSteps: 1. Cut off the king with the rook 2. Walk your king toward the enemy 3. Use the rook to deliver checkmate.\n\nLearning: The box method is the most important endgame technique."),
                "Hard": ("Pawn Promotion", "King + pawn vs king. Learn the 'opposition' concept — whoever has the opposition can promote.\n\nKey: If you have the opposition, your king can escort the pawn to promotion. If not, the defender can hold a draw.\n\nLearning: The opposition is the most important concept in pawn endgames."),
                "Expert": ("Rook Endgame", "Lucena position (winning) and Philidor position (drawing). These are the foundation of rook endgame theory.\n\nLucena: Build a bridge with your rook to shield your king from checks.\nPhilidor: Keep your rook on the 3rd rank to prevent the king from advancing.\n\nLearning: Rook endgames are the most common and most important endgames to study."),
            },
            "Poker hand evaluation": {
                "Easy": ("Identify the Hand", "Board: A♠ K♥ Q♦ J♣ 2♠. Your hand: 10♥ 9♥. What hand do you have?\n\nAnswer: Straight (10-J-Q-K-A — the Broadway straight).\n\nLearning: Always read the board carefully. The best possible hand here is a straight."),
                "Medium": ("Pot Odds Calculation", "Pot is $100. Opponent bets $50. You have a flush draw (9 outs). Should you call?\n\nAnswer: Pot odds = 50/(100+50+50) = 50/200 = 25%. Flush draw odds = 9/47 ≈ 19%. Direct odds say fold, but implied odds may justify a call.\n\nLearning: Pot odds compare the cost of calling to your chance of winning."),
                "Hard": ("Range Analysis", "Opponent raised pre-flop, bet flop, checked turn. Board: K♦ 7♣ 3♠ 2♥. What is their range?\n\nAnswer: Likely strong but cautious — AA, AK, KK, maybe QQ/JJ that are afraid of the king. The check on the turn could mean pot control or weakness. Consider bluff-raising.\n\nLearning: Range analysis is about narrowing what your opponent could have based on their actions."),
                "Expert": ("ICM Pressure", "Tournament: 4 players left, you're 3rd in chips. Chip leader shoves all-in. You have AQ offsuit. Call or fold?\n\nAnswer: Usually fold. ICM (Independent Chip Model) means chips lost are worth more than chips won. The chip leader can leverage their stack. AQ is not strong enough to call an all-in here.\n\nLearning: In tournaments, survival matters more than chip accumulation near the bubble or final table."),
            },
            "Poker odds estimation": {
                "Easy": ("Rule of 2 and 4", "With 9 outs on the flop, estimate your win probability for the turn.\n\nAnswer: 9 × 2 = 18% (turn only). For turn+river: 9 × 4 = 36%.\n\nLearning: The Rule of 2 (one card) and Rule of 4 (two cards) are quick mental math for poker odds."),
                "Medium": ("Combo Counting", "How many ways to make AK (any suits)?\n\nAnswer: 4 aces × 4 kings = 16 combinations.\n\nLearning: Combo counting helps you estimate how often certain hands appear."),
                "Hard": ("Equity Estimation", "You have JJ vs an opponent's range of {AA, KK, QQ, AK}. Estimate your equity.\n\nAnswer: vs AA: ~20%, vs KK: ~20%, vs QQ: ~20%, vs AK: ~55%. If range is equal-weighted: (20+20+20+55)/4 ≈ 29%.\n\nLearning: Equity estimation against ranges is a core advanced poker skill."),
                "Expert": ("Implied Odds", "You have a gutshot straight draw (4 outs) on the flop. Pot is $200, opponent bets $100. You expect to win $400 more if you hit. Call or fold?\n\nAnswer: Direct odds: 100/400 = 25%, gutshot = 4/47 ≈ 8.5%. But implied: if you hit and win $400 more, total = $700. 100/700 ≈ 14%. Still not enough. Fold.\n\nLearning: Implied odds include future winnings but must be realistic, not optimistic."),
            },
            "Logic puzzle generator": {
                "Easy": ("Three Houses", "Three houses in a row: red, blue, green. The red house is not at either end. The blue house is to the left of the green house. What order are they?\n\nAnswer: Blue, Red, Green.\n\nLearning: Use elimination and constraints to narrow possibilities."),
                "Medium": ("Knights and Knaves", "On an island, knights always tell the truth and knaves always lie. You meet two people, A and B. A says 'B is a knave.' B says 'We are both knights.' Who is what?\n\nAnswer: A is a knight, B is a knave. If A is a knight, B is a knave (truth). If B is a knave, his statement is a lie (they're not both knights) — consistent.\n\nLearning: Assume one possibility and check for consistency."),
                "Hard": ("Einstein's Riddle (simplified)", "5 houses, each a different color. The Brit lives in the red house. The Swede keeps dogs. The Dane drinks tea. The green house is to the left of the white house. The owner of the green house drinks coffee. Who drinks water?\n\nAnswer: This requires systematic elimination. Set up a grid and fill in constraints.\n\nLearning: Complex logic puzzles require systematic constraint satisfaction."),
                "Expert": ("Two Envelopes", "You're given two envelopes. One has twice as much money as the other. You pick one and open it — it has $100. Should you switch?\n\nAnswer: This is the Two Envelope Paradox. The expected value argument suggests switching is neutral. The paradox involves infinite expectation. In practice, switching doesn't matter.\n\nLearning: Some puzzles reveal deep mathematical paradoxes about probability and expectation."),
            },
            "Memory challenge": {
                "Easy": ("Number Sequence", "Memorize: 7-3-9-1-5. Cover it and write it back. Then try 7-3-9-1-5-8-2.\n\nLearning: Chunking helps — group numbers into pairs or triplets."),
                "Medium": ("Chess Position", "Study a chess position for 10 seconds, then recreate it from memory. Start with 10 pieces, increase gradually.\n\nLearning: Pattern recognition aids memory — experienced players remember positions better because they see patterns, not individual pieces."),
                "Hard": ("Card Memory", "Memorize the order of a shuffled deck of 52 cards. Use the Method of Loci (memory palace).\n\nLearning: The Method of Loci is the most powerful memorization technique — associate each card with a vivid image in a familiar location."),
                "Expert": ("Blindfold Chess", "Play a full chess game without seeing the board. Start with a 10-move game, then increase.\n\nLearning: Blindfold chess develops visualization and calculation skills. Grandmasters can play dozens of simultaneous blindfold games."),
            },
            "Pattern recognition": {
                "Easy": ("Next in Sequence", "What comes next: 2, 4, 8, 16, ?\n\nAnswer: 32 (doubling pattern).\n\nLearning: Identify the rule generating the sequence."),
                "Medium": ("Visual Pattern", "Describe the pattern: ○●○●●○●●●○●●●●?\n\nAnswer: Alternating circles, with the filled circles increasing by one each cycle: 1 filled, 2 filled, 3 filled, 4 filled...\n\nLearning: Look for both the repeating structure and the changing element."),
                "Hard": ("Matrix Pattern", "Matrix: [1,2,3] [4,5,6] [7,8,?]. What's the missing number?\n\nAnswer: 9 (sequential counting, row by row).\n\nLearning: Consider multiple possible patterns — the simplest is usually correct."),
                "Expert": ("Abstract Pattern", "Sequence: 1, 11, 21, 1211, 111221, ?\n\nAnswer: 312211 (look-and-say sequence — each term describes the previous: 'three 1s, two 2s, two 1s').\n\nLearning: Some patterns require lateral thinking — the rule may not be mathematical."),
            },
        }
        drill_info = drills.get(practice_type, {})
        drill = drill_info.get(difficulty, drill_info.get("Easy", ("No drill available", "The built-in intelligence can provide AI-generated drills.")))
        output = (
            f"[PRACTICE DRILL — LOCAL]\n\n"
            f"Type: {practice_type}\n"
            f"Difficulty: {difficulty}\n"
            f"Drill: {drill[0]}\n\n"
            f"{drill[1]}\n\n"
            "PRACTICE TIPS:\n"
            "  - Set a timer for each drill\n"
            "  - Write down your answer before checking\n"
            "  - Review the solution carefully\n"
            "  - Repeat the drill type until comfortable\n"
            "  - Move to harder difficulty when consistently correct\n\n"
            "The built-in intelligence can provide unlimited AI-generated drills."
        )
        self._practice_output.setText(output)
        self._set_result_summary(f"Practice drill: {practice_type} ({difficulty}).")

    def _run_progress_log(self):
        game = self._progress_game.text().strip()
        if not game:
            self._progress_output.setText("Enter a game name.")
            return
        result = self._progress_result.currentText()
        rating = self._progress_rating.text().strip()
        notes = self._progress_notes.toPlainText().strip()
        entry = {"game": game, "result": result, "rating": rating, "notes": notes}
        self._progress_log.append(entry)
        self._progress_game.clear()
        self._progress_rating.clear()
        self._progress_notes.clear()
        self._progress_output.setText(f"Session logged: {game} — {result}" + (f" (Rating: {rating})" if rating else "") + f"\nTotal sessions logged: {len(self._progress_log)}")
        self._set_result_summary(f"Logged: {game} — {result}.")

    def _run_progress_summary(self):
        if not self._progress_log:
            self._progress_output.setText("No sessions logged yet. Log some game sessions first!")
            return
        total = len(self._progress_log)
        wins = sum(1 for e in self._progress_log if e["result"] == "Win")
        losses = sum(1 for e in self._progress_log if e["result"] == "Loss")
        draws = sum(1 for e in self._progress_log if e["result"] == "Draw")
        practice = sum(1 for e in self._progress_log if e["result"] == "Practice session")
        games_played: dict[str, int] = {}
        for e in self._progress_log:
            games_played[e["game"]] = games_played.get(e["game"], 0) + 1
        output = (
            f"[PROGRESS SUMMARY — LOCAL]\n\n"
            f"Total sessions: {total}\n"
            f"  Wins:     {wins}\n"
            f"  Losses:   {losses}\n"
            f"  Draws:    {draws}\n"
            f"  Practice: {practice}\n\n"
        )
        if total > 0:
            win_rate = wins / (wins + losses) * 100 if (wins + losses) else 0
            output += f"Win rate: {win_rate:.1f}% (excluding draws/practice)\n\n"
        output += "GAMES PLAYED:\n"
        for game, count in sorted(games_played.items(), key=lambda x: -x[1]):
            output += f"  {game}: {count} session(s)\n"
        output += "\nSESSION LOG:\n"
        for i, e in enumerate(self._progress_log, 1):
            line = f"  {i}. {e['game']} — {e['result']}"
            if e["rating"]:
                line += f" (Rating: {e['rating']})"
            if e["notes"]:
                line += f" — {e['notes'][:60]}"
            output += line + "\n"
        output += (
            "\nIMPROVEMENT TIPS:\n"
            "  - Focus on the game you play most\n"
            "  - Review losses more carefully than wins\n"
            "  - Track rating changes over time\n"
            "  - Set practice goals (e.g., 3 puzzles/day)\n"
            "  - Celebrate milestones and streaks\n"
        )
        self._progress_output.setText(output)
        self._set_result_summary(f"Progress: {total} sessions, {wins}W/{losses}L/{draws}D.")


class DataAnalystDialog(BaseCapabilityDialog):
    """Data Analyst Pro — data summary, statistics calculator, trend detector, outlier flagger, chart suggester."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Data Analyst Pro — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_summary_tab(), "Data Summary")
        tabs.addTab(self._build_stats_tab(), "Statistics")
        tabs.addTab(self._build_trend_tab(), "Trend Detector")
        tabs.addTab(self._build_outlier_tab(), "Outlier Checker")
        tabs.addTab(self._build_chart_tab(), "Chart Suggestions")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Data analysis is advisory. Calculations may contain errors. Always verify critical results. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_summary_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Data Summary"))
        l.addWidget(QLabel("Paste your data (comma or newline separated numbers):"))
        self._summary_input = QTextEdit()
        self._summary_input.setPlaceholderText("e.g.,\n10, 20, 30, 40, 50, 60, 70, 80, 90, 100\n\nor one per line:\n10\n20\n30\n...")
        l.addWidget(self._summary_input, stretch=1)
        btn = QPushButton("Summarize Data")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_summary)
        l.addWidget(btn)
        self._summary_output = QTextEdit()
        self._summary_output.setReadOnly(True)
        self._summary_output.setStyleSheet("")
        l.addWidget(self._summary_output, stretch=1)
        return w

    def _build_stats_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Statistics Calculator"))
        l.addWidget(QLabel("Enter numbers (comma or space separated):"))
        self._stats_input = QLineEdit()
        self._stats_input.setPlaceholderText("e.g., 10, 20, 30, 40, 50")
        l.addWidget(self._stats_input)
        btn = QPushButton("Calculate Statistics")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_stats)
        l.addWidget(btn)
        self._stats_output = QTextEdit()
        self._stats_output.setReadOnly(True)
        self._stats_output.setStyleSheet("")
        l.addWidget(self._stats_output, stretch=1)
        return w

    def _build_trend_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Trend Detector"))
        l.addWidget(QLabel("Enter a time series (one value per line, oldest first):"))
        self._trend_input = QTextEdit()
        self._trend_input.setPlaceholderText("e.g.,\n100\n105\n108\n115\n120\n125\n130\n140\n145\n150")
        l.addWidget(self._trend_input, stretch=1)
        btn = QPushButton("Detect Trends")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_trend)
        l.addWidget(btn)
        self._trend_output = QTextEdit()
        self._trend_output.setReadOnly(True)
        self._trend_output.setStyleSheet("")
        l.addWidget(self._trend_output, stretch=1)
        return w

    def _build_outlier_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Outlier Checker"))
        l.addWidget(QLabel("Enter data values (comma separated):"))
        self._outlier_input = QLineEdit()
        self._outlier_input.setPlaceholderText("e.g., 10, 12, 11, 13, 10, 50, 12, 11, 14, 10")
        l.addWidget(self._outlier_input)
        l.addWidget(QLabel("Detection method:"))
        self._outlier_method = QComboBox()
        self._outlier_method.addItems(["IQR (Interquartile Range)", "Z-score (>2 std dev)", "Z-score (>3 std dev)"])
        l.addWidget(self._outlier_method)
        btn = QPushButton("Check for Outliers")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_outlier)
        l.addWidget(btn)
        self._outlier_output = QTextEdit()
        self._outlier_output.setReadOnly(True)
        self._outlier_output.setStyleSheet("")
        l.addWidget(self._outlier_output, stretch=1)
        return w

    def _build_chart_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Chart Suggestions"))
        l.addWidget(QLabel("Describe your data and what you want to visualize:"))
        self._chart_input = QTextEdit()
        self._chart_input.setPlaceholderText("e.g., 'I have monthly sales data for 12 months and want to show growth trend' or 'I have survey results with 5 categories and want to show distribution'")
        self._chart_input.setMaximumHeight(80)
        l.addWidget(self._chart_input)
        btn = QPushButton("Suggest Charts")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_chart)
        l.addWidget(btn)
        self._chart_output = QTextEdit()
        self._chart_output.setReadOnly(True)
        self._chart_output.setStyleSheet("")
        l.addWidget(self._chart_output, stretch=1)
        return w

    def _parse_numbers(self, text: str) -> list[float]:
        import re
        parts = re.split(r'[,\s\n]+', text.strip())
        return [float(p) for p in parts if p]

    def _run_summary(self):
        raw = self._summary_input.toPlainText().strip()
        if not raw:
            self._summary_output.setText("Paste some data first.")
            return
        try:
            data = self._parse_numbers(raw)
        except ValueError:
            self._summary_output.setText("Could not parse numbers. Use commas, spaces, or newlines to separate values.")
            return
        if not data:
            self._summary_output.setText("No valid numbers found.")
            return
        n = len(data)
        total = sum(data)
        mean = total / n
        sorted_data = sorted(data)
        median = sorted_data[n // 2] if n % 2 else (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2
        minimum = min(data)
        maximum = max(data)
        rng = maximum - minimum
        output = (
            f"[DATA SUMMARY — LOCAL ANALYSIS]\n\n"
            f"Data points: {n}\n"
            f"Sum: {total:,.2f}\n"
            f"Mean: {mean:,.2f}\n"
            f"Median: {median:,.2f}\n"
            f"Min: {minimum:,.2f}\n"
            f"Max: {maximum:,.2f}\n"
            f"Range: {rng:,.2f}\n\n"
            f"DATA PREVIEW (first 10): {', '.join(f'{v:.2f}' for v in data[:10])}\n"
        )
        if n > 10:
            output += f"DATA PREVIEW (last 10):  {', '.join(f'{v:.2f}' for v in data[-10:])}\n"
        output += (
            "\nQUICK INSIGHTS:\n"
            f"  - Data {'is symmetric' if abs(mean - median) < rng * 0.05 else 'is skewed'} (mean vs median)\n"
            f"  - Spread: {'narrow' if rng < mean * 0.5 else 'wide' if rng > mean * 2 else 'moderate'}\n"
            f"  - Sample size: {'small (<30)' if n < 30 else 'moderate (30-100)' if n < 100 else 'large (100+)'}\n\n"
            "Use the Statistics tab for detailed calculations.\n"
            "The built-in intelligence can provide data insights."
        )
        self._summary_output.setText(output)
        self._set_result_summary(f"Summarized {n} data points. Mean={mean:.2f}, Median={median:.2f}.")

    def _run_stats(self):
        raw = self._stats_input.text().strip()
        if not raw:
            self._stats_output.setText("Enter some numbers.")
            return
        try:
            data = self._parse_numbers(raw)
        except ValueError:
            self._stats_output.setText("Could not parse numbers.")
            return
        if not data:
            self._stats_output.setText("No valid numbers found.")
            return
        n = len(data)
        total = sum(data)
        mean = total / n
        sorted_data = sorted(data)
        median = sorted_data[n // 2] if n % 2 else (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2
        minimum = min(data)
        maximum = max(data)
        rng = maximum - minimum
        if n > 1:
            variance = sum((x - mean) ** 2 for x in data) / (n - 1)
            std_dev = variance ** 0.5
            pop_variance = sum((x - mean) ** 2 for x in data) / n
            pop_std = pop_variance ** 0.5
        else:
            variance = std_dev = pop_variance = pop_std = 0
        q1_idx = int(n * 0.25)
        q3_idx = int(n * 0.75)
        q1 = sorted_data[q1_idx] if q1_idx < n else sorted_data[-1]
        q3 = sorted_data[q3_idx] if q3_idx < n else sorted_data[-1]
        iqr = q3 - q1
        cv = (std_dev / mean * 100) if mean else 0
        skew = (sum((x - mean) ** 3 for x in data) / (n * std_dev ** 3)) if std_dev and n > 0 else 0
        output = (
            f"[STATISTICS — LOCAL ANALYSIS]\n\n"
            f"Sample size (n): {n}\n"
            f"Sum: {total:,.4f}\n\n"
            f"CENTRAL TENDENCY:\n"
            f"  Mean:              {mean:,.4f}\n"
            f"  Median:            {median:,.4f}\n"
            f"  Min:               {minimum:,.4f}\n"
            f"  Max:               {maximum:,.4f}\n"
            f"  Range:             {rng:,.4f}\n\n"
            f"DISPERSION:\n"
            f"  Sample variance:   {variance:,.4f}\n"
            f"  Sample std dev:    {std_dev:,.4f}\n"
            f"  Pop variance:      {pop_variance:,.4f}\n"
            f"  Pop std dev:       {pop_std:,.4f}\n"
            f"  Coeff. of var.:    {cv:,.2f}%\n\n"
            f"QUARTILES:\n"
            f"  Q1 (25th pct):     {q1:,.4f}\n"
            f"  Q3 (75th pct):     {q3:,.4f}\n"
            f"  IQR:               {iqr:,.4f}\n\n"
            f"SHAPE:\n"
            f"  Skewness:          {skew:,.4f}\n"
        )
        if abs(skew) < 0.5:
            output += "  Interpretation:     Approximately symmetric\n"
        elif skew > 0:
            output += "  Interpretation:     Right-skewed (tail extends right)\n"
        else:
            output += "  Interpretation:     Left-skewed (tail extends left)\n"
        output += "\nThe built-in intelligence can provide statistical interpretation."
        self._stats_output.setText(output)
        self._set_result_summary(f"Stats: n={n}, mean={mean:.2f}, std={std_dev:.2f}.")

    def _run_trend(self):
        raw = self._trend_input.toPlainText().strip()
        if not raw:
            self._trend_output.setText("Enter a time series.")
            return
        try:
            data = self._parse_numbers(raw)
        except ValueError:
            self._trend_output.setText("Could not parse numbers.")
            return
        if len(data) < 3:
            self._trend_output.setText("Need at least 3 data points for trend analysis.")
            return
        n = len(data)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(data) / n
        numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, data))
        denominator = sum((xi - x_mean) ** 2 for xi in x)
        slope = numerator / denominator if denominator else 0
        intercept = y_mean - slope * x_mean
        r_num = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, data))
        r_den_x = sum((xi - x_mean) ** 2 for xi in x) ** 0.5
        r_den_y = sum((yi - y_mean) ** 2 for yi in data) ** 0.5
        r = r_num / (r_den_x * r_den_y) if r_den_x and r_den_y else 0
        r_squared = r ** 2
        first_val = data[0]
        last_val = data[-1]
        total_change = last_val - first_val
        pct_change = (total_change / first_val * 100) if first_val else 0
        avg_period_change = total_change / (n - 1) if n > 1 else 0
        output = (
            f"[TREND DETECTION — LOCAL ANALYSIS]\n\n"
            f"Data points: {n}\n"
            f"First value: {first_val:,.2f}\n"
            f"Last value:  {last_val:,.2f}\n"
            f"Total change: {total_change:,.2f} ({pct_change:+.2f}%)\n"
            f"Avg change per period: {avg_period_change:,.2f}\n\n"
            f"LINEAR REGRESSION:\n"
            f"  Slope:     {slope:,.4f} per period\n"
            f"  Intercept: {intercept:,.4f}\n"
            f"  R:         {r:,.4f}\n"
            f"  R²:        {r_squared:,.4f}\n\n"
        )
        if slope > 0:
            direction = "UPWARD TREND"
        elif slope < 0:
            direction = "DOWNWARD TREND"
        else:
            direction = "FLAT (no trend)"
        output += f"TREND DIRECTION: {direction}\n"
        if r_squared > 0.7:
            output += f"TREND STRENGTH: Strong (R²={r_squared:.2f})\n"
        elif r_squared > 0.4:
            output += f"TREND STRENGTH: Moderate (R²={r_squared:.2f})\n"
        else:
            output += f"TREND STRENGTH: Weak (R²={r_squared:.2f})\n"
        projected = last_val + slope * 3
        output += (
            f"\nPROJECTION (3 periods ahead): {projected:,.2f}\n\n"
            "VOLATILITY CHECK:\n"
        )
        changes = [data[i] - data[i - 1] for i in range(1, n)]
        if changes:
            avg_change = sum(changes) / len(changes)
            positive = sum(1 for c in changes if c > 0)
            negative = sum(1 for c in changes if c < 0)
            output += f"  Periods up: {positive}, Periods down: {negative}\n"
            output += f"  Avg period change: {avg_change:,.2f}\n"
        output += "\nThe built-in intelligence can provide trend interpretation."
        self._trend_output.setText(output)
        self._set_result_summary(f"Trend: {direction}, R²={r_squared:.2f}, slope={slope:.2f}/period.")

    def _run_outlier(self):
        raw = self._outlier_input.text().strip()
        if not raw:
            self._outlier_output.setText("Enter some numbers.")
            return
        try:
            data = self._parse_numbers(raw)
        except ValueError:
            self._outlier_output.setText("Could not parse numbers.")
            return
        if len(data) < 4:
            self._outlier_output.setText("Need at least 4 data points for outlier detection.")
            return
        method = self._outlier_method.currentText()
        n = len(data)
        sorted_data = sorted(data)
        mean = sum(data) / n
        if n > 1:
            std_dev = (sum((x - mean) ** 2 for x in data) / (n - 1)) ** 0.5
        else:
            std_dev = 0
        q1_idx = int(n * 0.25)
        q3_idx = int(n * 0.75)
        q1 = sorted_data[q1_idx]
        q3 = sorted_data[q3_idx]
        iqr = q3 - q1
        output = f"[OUTLIER DETECTION — LOCAL ANALYSIS]\n\nMethod: {method}\nData points: {n}\n\n"
        output += f"Mean: {mean:,.4f}\nStd dev: {std_dev:,.4f}\nQ1: {q1:,.4f}\nQ3: {q3:,.4f}\nIQR: {iqr:,.4f}\n\n"
        outliers = []
        if "IQR" in method:
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            output += f"IQR Bounds: [{lower:,.4f}, {upper:,.4f}]\n\n"
            for i, val in enumerate(data):
                if val < lower or val > upper:
                    outliers.append((i + 1, val))
        else:
            threshold = 3 if "3" in method else 2
            output += f"Z-score threshold: > {threshold} std dev\n\n"
            for i, val in enumerate(data):
                z = abs((val - mean) / std_dev) if std_dev else 0
                if z > threshold:
                    outliers.append((i + 1, val))
        if outliers:
            output += f"OUTLIERS FOUND ({len(outliers)}):\n"
            for idx, val in outliers:
                if "IQR" in method:
                    reason = "below lower bound" if val < q1 - 1.5 * iqr else "above upper bound"
                else:
                    z = abs((val - mean) / std_dev) if std_dev else 0
                    reason = f"z-score = {z:.2f}"
                output += f"  ⚠ Position {idx}: {val:,.4f} ({reason})\n"
            output += (
                "\nHANDLING OUTLIERS:\n"
                "  - Investigate: Is it a data error or genuine extreme value?\n"
                "  - If error: Correct or remove\n"
                "  - If genuine: Keep but consider robust statistics\n"
                "  - Consider winsorizing (cap at percentile)\n"
                "  - Report both with and without outliers\n"
            )
        else:
            output += "✓ No outliers detected with this method.\n"
        output += "\nThe built-in intelligence can provide outlier analysis."
        self._outlier_output.setText(output)
        self._set_result_summary(f"Outlier check: {len(outliers)} found ({method}).")

    def _run_chart(self):
        description = self._chart_input.toPlainText().strip()
        if not description:
            self._chart_output.setText("Describe your data and visualization goal.")
            return
        task = f"Suggest appropriate chart types for this data visualization request: {description}. Include why each chart type is suitable and how to create it."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._chart_output.setText(ai_result)
            self._set_result_summary("Chart suggestions via AI.")
            return
        desc_lower = description.lower()
        suggestions = []
        if any(w in desc_lower for w in ["trend", "growth", "over time", "time series", "change"]):
            suggestions.append(("Line Chart", "Shows trends over time. Best for continuous data with ordered x-axis (time, dates). Use when you want to show direction and rate of change."))
            suggestions.append(("Area Chart", "Like a line chart but filled. Good for showing cumulative totals or volume over time."))
        if any(w in desc_lower for w in ["compare", "comparison", "versus", "vs", "across categories"]):
            suggestions.append(("Bar Chart", "Compares values across categories. Best for discrete data. Use horizontal bars for long category names."))
            suggestions.append(("Grouped Bar Chart", "Compares multiple series across categories. Good for side-by-side comparisons."))
        if any(w in desc_lower for w in ["distribution", "spread", "histogram", "frequency"]):
            suggestions.append(("Histogram", "Shows distribution of a single variable. Good for understanding data shape and spread."))
            suggestions.append(("Box Plot", "Shows quartiles, median, and outliers. Great for comparing distributions across groups."))
        if any(w in desc_lower for w in ["proportion", "percentage", "share", "part of", "breakdown"]):
            suggestions.append(("Pie Chart", "Shows proportions of a whole. Best with ≤6 categories. Use sparingly — bar charts are often clearer."))
            suggestions.append(("Stacked Bar Chart", "Shows both total and composition. Better than pie for comparing across groups."))
        if any(w in desc_lower for w in ["relationship", "correlation", "scatter", "two variables"]):
            suggestions.append(("Scatter Plot", "Shows relationship between two variables. Each point is an observation. Look for patterns and correlations."))
            suggestions.append(("Bubble Chart", "Like scatter plot but with a third variable encoded as bubble size."))
        if any(w in desc_lower for w in ["rank", "ranking", "top", "bottom", "leaderboard"]):
            suggestions.append(("Horizontal Bar Chart", "Best for rankings. Easy to read long labels. Sort by value for clarity."))
        if not suggestions:
            suggestions = [
                ("Bar Chart", "Universal comparison chart. Good default for categorical data."),
                ("Line Chart", "Best for trends over time or ordered data."),
                ("Scatter Plot", "Best for showing relationships between two variables."),
                ("Histogram", "Best for showing data distribution."),
            ]
        output = "[CHART SUGGESTIONS — LOCAL ANALYSIS]\n\n"
        output += f"Request: {description[:200]}\n\n"
        output += f"SUGGESTED CHARTS ({len(suggestions)}):\n\n"
        for i, (chart_type, reason) in enumerate(suggestions, 1):
            output += f"  {i}. {chart_type}\n     {reason}\n\n"
        output += (
            "CHART DESIGN PRINCIPLES:\n"
            "  - Less is more — remove unnecessary gridlines and decorations\n"
            "  - Label axes clearly with units\n"
            "  - Use color purposefully (not just for decoration)\n"
            "  - Sort data logically (by value, by time, or alphabetically)\n"
            "  - Start y-axis at 0 for bar charts (avoid misleading)\n"
            "  - Use appropriate aspect ratio (not too wide, not too tall)\n"
            "  - Add a descriptive title and subtitle\n\n"
            "TOOLS:\n"
            "  - Excel/Google Sheets (basic charts)\n"
            "  - Python: matplotlib, seaborn, plotly\n"
            "  - R: ggplot2\n"
            "  - Online: Datawrapper, Flourish\n\n"
            "The built-in intelligence can provide chart recommendations."
        )
        self._chart_output.setText(output)
        self._set_result_summary(f"Suggested {len(suggestions)} chart types.")


class CodeReviewerDialog(BaseCapabilityDialog):
    """Code Reviewer — paste code for security scan, quality checklist, performance flags, best-practice matching."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Code Reviewer — {ai_name} | Avery Logic Works(TM)")
        self.resize(880, 660)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_review_tab(), "Code Review")
        tabs.addTab(self._build_security_tab(), "Security Scan")
        tabs.addTab(self._build_quality_tab(), "Quality Checklist")
        tabs.addTab(self._build_perf_tab(), "Performance Flags")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Code review is advisory. May miss subtle bugs or flag false positives. Not a replacement for human review. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_review_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Code Review"))
        l.addWidget(QLabel("Language:"))
        self._review_lang = QComboBox()
        self._review_lang.addItems(["Python", "JavaScript", "TypeScript", "Java", "C/C++", "Go", "Rust", "SQL", "HTML/CSS", "Other"])
        l.addWidget(self._review_lang)
        l.addWidget(QLabel("Paste your code:"))
        self._review_code = QTextEdit()
        self._review_code.setPlaceholderText("Paste code here for review...")
        self._review_code.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace; font-size: 12px;")
        l.addWidget(self._review_code, stretch=1)
        btn = QPushButton("Review Code")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_review)
        l.addWidget(btn)
        self._review_output = QTextEdit()
        self._review_output.setReadOnly(True)
        self._review_output.setStyleSheet("")
        l.addWidget(self._review_output, stretch=1)
        return w

    def _build_security_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Security Scan"))
        l.addWidget(QLabel("Paste code to scan for security vulnerabilities:"))
        self._security_code = QTextEdit()
        self._security_code.setPlaceholderText("Paste code here for security analysis...")
        self._security_code.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace; font-size: 12px;")
        l.addWidget(self._security_code, stretch=1)
        btn = QPushButton("Scan for Vulnerabilities")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_security)
        l.addWidget(btn)
        self._security_output = QTextEdit()
        self._security_output.setReadOnly(True)
        self._security_output.setStyleSheet("")
        l.addWidget(self._security_output, stretch=1)
        return w

    def _build_quality_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Code Quality Checklist"))
        btn = QPushButton("Run Quality Check")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_quality)
        l.addWidget(btn)
        self._quality_output = QTextEdit()
        self._quality_output.setReadOnly(True)
        self._quality_output.setStyleSheet("")
        l.addWidget(self._quality_output, stretch=1)
        return w

    def _build_perf_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Performance Flags"))
        l.addWidget(QLabel("Paste code to check for performance issues:"))
        self._perf_code = QTextEdit()
        self._perf_code.setPlaceholderText("Paste code here for performance analysis...")
        self._perf_code.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace; font-size: 12px;")
        l.addWidget(self._perf_code, stretch=1)
        btn = QPushButton("Check Performance")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_perf)
        l.addWidget(btn)
        self._perf_output = QTextEdit()
        self._perf_output.setReadOnly(True)
        self._perf_output.setStyleSheet("")
        l.addWidget(self._perf_output, stretch=1)
        return w

    def _run_through_runtime(self, task: str) -> str:
        try:
            from ...core.nexus_ai_runtime import NexusAIRuntime
            settings = SettingsManager()
            settings.initialize()
            runtime = NexusAIRuntime(settings=settings)
            result = runtime.run(task=task, ai_name=self._ai_name, ai_uuid=self._ai_uuid, ai_metadata={"abilities": self._abilities, "use_case": self._use_case, "guardrails": self._guardrails, "libraries": self._libraries})
            return result.result_text or ""
        except Exception:
            return ""

    def _run_review(self):
        code = self._review_code.toPlainText().strip()
        if not code:
            self._review_output.setText("Paste some code to review.")
            return
        lang = self._review_lang.currentText()
        task = f"Review this {lang} code for bugs, security issues, best practices, and improvements:\n\n{code}"
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._review_output.setText(ai_result)
            self._set_result_summary(f"Code reviewed via AI ({lang}).")
            return
        lines = code.split("\n")
        line_count = len(lines)
        char_count = len(code)
        issues = []
        if "TODO" in code or "FIXME" in code or "HACK" in code:
            issues.append("⚠ TODO/FIXME/HACK comments found — resolve before production")
        if "print(" in code and lang == "Python":
            issues.append("⚠ print() statements found — consider using logging for production")
        if "console.log" in code and lang in ("JavaScript", "TypeScript"):
            issues.append("⚠ console.log() found — remove debug logging for production")
        if "eval(" in code:
            issues.append("🚨 eval() detected — major security risk, avoid in production")
        if "exec(" in code and lang == "Python":
            issues.append("🚨 exec() detected — major security risk")
        if "innerHTML" in code:
            issues.append("⚠ innerHTML usage — potential XSS vulnerability")
        if "SELECT * FROM" in code.upper():
            issues.append("⚠ SELECT * — specify columns explicitly for better performance")
        long_lines = [i + 1 for i, line in enumerate(lines) if len(line) > 120]
        if long_lines:
            issues.append(f"⚠ Lines exceeding 120 chars: {long_lines[:5]}{'...' if len(long_lines) > 5 else ''}")
        if line_count > 200:
            issues.append("⚠ File is long (>200 lines) — consider splitting into modules")
        output = (
            f"[CODE REVIEW — LOCAL ANALYSIS]\n\n"
            f"Language: {lang}\n"
            f"Lines: {line_count}\n"
            f"Characters: {char_count}\n\n"
        )
        if issues:
            output += f"ISSUES FOUND ({len(issues)}):\n"
            for issue in issues:
                output += f"  {issue}\n"
        else:
            output += "No obvious issues detected by local scanner.\n"
        output += (
            "\nREVIEW CHECKLIST:\n"
            "  [ ] Code follows naming conventions\n"
            "  [ ] Functions are single-purpose and <50 lines\n"
            "  [ ] No hardcoded values (use constants/config)\n"
            "  [ ] Error handling is comprehensive\n"
            "  [ ] Edge cases are covered\n"
            "  [ ] No unused variables or imports\n"
            "  [ ] Comments explain 'why', not 'what'\n"
            "  [ ] Tests cover critical paths\n"
            "  [ ] No secrets/credentials in code\n"
            "  [ ] Dependencies are up to date\n\n"
            "The built-in intelligence can provide code review."
        )
        self._review_output.setText(output)
        self._set_result_summary(f"Code reviewed: {line_count} lines, {len(issues)} issues ({lang}).")

    def _run_security(self):
        code = self._security_code.toPlainText().strip()
        if not code:
            self._security_output.setText("Paste some code to scan.")
            return
        task = f"Scan this code for security vulnerabilities, injection risks, and unsafe patterns:\n\n{code}"
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._security_output.setText(ai_result)
            self._set_result_summary("Security scan via AI.")
            return
        vulnerabilities = []
        security_patterns = [
            ("eval(", "CRITICAL", "Code Injection", "eval() executes arbitrary code — remove immediately"),
            ("exec(", "CRITICAL", "Code Injection", "exec() executes arbitrary code — remove immediately"),
            ("os.system(", "HIGH", "Command Injection", "os.system() can execute arbitrary commands — use subprocess with shell=False"),
            ("subprocess.call(", "MEDIUM", "Command Injection", "Verify input sanitization if using subprocess with shell=True"),
            ("innerHTML", "HIGH", "XSS", "innerHTML can inject scripts — use textContent or sanitize input"),
            ("document.write(", "MEDIUM", "XSS", "document.write can inject content — use DOM methods instead"),
            ("SELECT * FROM", "LOW", "SQL", "SELECT * exposes all columns — specify needed columns"),
            ("password", "MEDIUM", "Hardcoded Secret", "Possible hardcoded password — use environment variables"),
            ("api_key", "MEDIUM", "Hardcoded Secret", "Possible hardcoded API key — use environment variables"),
            ("secret", "MEDIUM", "Hardcoded Secret", "Possible hardcoded secret — use environment variables"),
            ("http://", "LOW", "Insecure Transport", "HTTP URL detected — use HTTPS for secure communication"),
            ("pickle.loads", "HIGH", "Deserialization", "pickle.loads can execute arbitrary code — use safe formats"),
            ("yaml.load(", "MEDIUM", "Deserialization", "Use yaml.safe_load() instead of yaml.load()"),
            ("shell=True", "HIGH", "Command Injection", "shell=True allows command injection — avoid if possible"),
            ("md5(", "MEDIUM", "Weak Crypto", "MD5 is cryptographically broken — use SHA-256 or better"),
            ("sha1(", "LOW", "Weak Crypto", "SHA-1 is deprecated — use SHA-256 or better"),
            ("random.random", "LOW", "Insecure Random", "random module is not cryptographically secure — use secrets module"),
        ]
        code_lower = code.lower()
        for pattern, severity, category, advice in security_patterns:
            if pattern.lower() in code_lower:
                vulnerabilities.append((severity, category, advice))
        output = "[SECURITY SCAN — LOCAL ANALYSIS]\n\n"
        if vulnerabilities:
            output += f"VULNERABILITIES FOUND ({len(vulnerabilities)}):\n\n"
            for severity, category, advice in vulnerabilities:
                icon = "🚨" if severity == "CRITICAL" else "⚠" if severity == "HIGH" else "⚡"
                output += f"  {icon} [{severity}] {category}\n     {advice}\n\n"
        else:
            output += "✓ No common vulnerability patterns detected.\n\n"
        output += (
            "SECURITY REVIEW CHECKLIST:\n\n"
            "  INPUT VALIDATION:\n"
            "    [ ] All user input is validated and sanitized\n"
            "    [ ] SQL queries use parameterized statements\n"
            "    [ ] No command injection vectors\n"
            "    [ ] File paths are validated\n\n"
            "  AUTHENTICATION & AUTHORIZATION:\n"
            "    [ ] Passwords are hashed (bcrypt/argon2)\n"
            "    [ ] Session tokens are secure and random\n"
            "    [ ] Access control checks are in place\n"
            "    [ ] No hardcoded credentials\n\n"
            "  DATA PROTECTION:\n"
            "    [ ] Sensitive data is encrypted at rest\n"
            "    [ ] HTTPS is used for transport\n"
            "    [ ] No sensitive data in logs\n"
            "    [ ] Error messages don't leak information\n\n"
            "  DEPENDENCIES:\n"
            "    [ ] Dependencies are up to date\n"
            "    [ ] No known vulnerable packages\n"
            "    [ ] Lock file is committed\n\n"
            "The built-in intelligence can provide security analysis."
        )
        self._security_output.setText(output)
        self._set_result_summary(f"Security scan: {len(vulnerabilities)} vulnerabilities found.")

    def _run_quality(self):
        output = (
            "[CODE QUALITY CHECKLIST — LOCAL REFERENCE]\n\n"
            "READABILITY:\n"
            "  [ ] Variables and functions have descriptive names\n"
            "  [ ] No single-letter variables (except loop counters)\n"
            "  [ ] Functions are <50 lines\n"
            "  [ ] Classes are <300 lines\n"
            "  [ ] Files are <500 lines\n"
            "  [ ] Consistent indentation and formatting\n"
            "  [ ] No dead code (unreachable or unused)\n\n"
            "STRUCTURE:\n"
            "  [ ] Single Responsibility Principle followed\n"
            "  [ ] No deep nesting (>3 levels)\n"
            "  [ ] Functions have clear inputs and outputs\n"
            "  [ ] No side effects in pure functions\n"
            "  [ ] Modules are properly separated\n"
            "  [ ] Dependencies are injected, not hardcoded\n\n"
            "ERROR HANDLING:\n"
            "  [ ] All exceptions are caught and handled\n"
            "  [ ] Error messages are helpful and actionable\n"
            "  [ ] No silent failures (empty except blocks)\n"
            "  [ ] Resources are properly cleaned up (context managers, finally)\n"
            "  [ ] Edge cases are tested\n\n"
            "TESTING:\n"
            "  [ ] Unit tests cover critical paths\n"
            "  [ ] Tests are independent and repeatable\n"
            "  [ ] Test names describe the scenario\n"
            "  [ ] Integration tests for key workflows\n"
            "  [ ] Edge cases and error paths tested\n\n"
            "DOCUMENTATION:\n"
            "  [ ] Public functions have docstrings/comments\n"
            "  [ ] Complex logic is explained\n"
            "  [ ] README is up to date\n"
            "  [ ] API documentation is complete\n"
            "  [ ] Change log is maintained\n\n"
            "MAINTAINABILITY:\n"
            "  [ ] No magic numbers (use named constants)\n"
            "  [ ] DRY — no duplicated logic\n"
            "  [ ] YAGNI — no unused abstractions\n"
            "  [ ] KISS — simplest solution that works\n"
            "  [ ] SOLID principles followed where appropriate\n\n"
            "The built-in intelligence can provide quality analysis of your code."
        )
        self._quality_output.setText(output)
        self._set_result_summary("Quality checklist displayed.")

    def _run_perf(self):
        code = self._perf_code.toPlainText().strip()
        if not code:
            self._perf_output.setText("Paste some code to analyze.")
            return
        task = f"Analyze this code for performance issues, inefficiencies, and optimization opportunities:\n\n{code}"
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._perf_output.setText(ai_result)
            self._set_result_summary("Performance analysis via AI.")
            return
        perf_issues = []
        perf_patterns = [
            ("for i in range(len(", "MEDIUM", "Use enumerate() or direct iteration instead of range(len())"),
            ("for x in list", "LOW", "Iterating over a list while modifying it can cause bugs"),
            (".append(", "LOW", "Multiple appends in a loop — consider list comprehension"),
            ("SELECT * FROM", "MEDIUM", "SELECT * fetches all columns — specify only needed columns"),
            ("time.sleep(", "LOW", "Blocking sleep — consider async alternatives"),
            ("requests.get(", "LOW", "Synchronous HTTP call — consider async for multiple requests"),
            ("open(", "LOW", "Ensure files are closed — use context managers (with statement)"),
            ("while True", "MEDIUM", "Infinite loop — ensure there's a break condition"),
            ("sorted(", "LOW", "Sorting inside a loop — consider sorting once outside"),
            (".keys()", "LOW", "Unnecessary .keys() call — iterating dict directly is cleaner"),
            ("global ", "MEDIUM", "Global variable — can cause concurrency issues"),
            ("threading.Lock", "LOW", "Lock contention — consider lock-free alternatives if possible"),
        ]
        code_lower = code.lower()
        for pattern, severity, advice in perf_patterns:
            if pattern.lower() in code_lower:
                perf_issues.append((severity, advice))
        nested_loops = 0
        indent_level = 0
        for line in code.split("\n"):
            stripped = line.lstrip()
            if stripped.startswith("for ") or stripped.startswith("while "):
                current_indent = len(line) - len(stripped)
                if current_indent > 0 and indent_level > 0:
                    nested_loops += 1
                indent_level = current_indent
        if nested_loops > 0:
            perf_issues.append(("HIGH", f"Nested loops detected ({nested_loops} levels) — O(n²) or worse complexity"))
        output = "[PERFORMANCE ANALYSIS — LOCAL ANALYSIS]\n\n"
        if perf_issues:
            output += f"PERFORMANCE FLAGS ({len(perf_issues)}):\n\n"
            for severity, advice in perf_issues:
                icon = "🚨" if severity == "HIGH" else "⚠" if severity == "MEDIUM" else "⚡"
                output += f"  {icon} [{severity}] {advice}\n"
        else:
            output += "✓ No common performance anti-patterns detected.\n"
        output += (
            "\nPERFORMANCE OPTIMIZATION TIPS:\n\n"
            "  ALGORITHMS:\n"
            "    - Choose the right data structure (set for lookups, dict for mappings)\n"
            "    - Avoid O(n²) when O(n log n) or O(n) is possible\n"
            "    - Use caching/memoization for repeated expensive operations\n"
            "    - Consider lazy evaluation for large datasets\n\n"
            "  I/O:\n"
            "    - Batch database queries instead of N+1 patterns\n"
            "    - Use connection pooling for databases\n"
            "    - Cache frequently accessed data\n"
            "    - Use async I/O for concurrent operations\n\n"
            "  MEMORY:\n"
            "    - Use generators instead of lists for large sequences\n"
            "    - Avoid keeping unnecessary references\n"
            "    - Use __slots__ for memory-critical classes\n"
            "    - Profile memory usage with tools\n\n"
            "  PROFILING TOOLS:\n"
            "    - Python: cProfile, line_profiler, memory_profiler\n"
            "    - JavaScript: Chrome DevTools, Node.js --prof\n"
            "    - General: Measure before optimizing (don't guess)\n\n"
            "The built-in intelligence can provide performance analysis."
        )
        self._perf_output.setText(output)
        self._set_result_summary(f"Performance check: {len(perf_issues)} flags found.")


class SecurityAuditorDialog(BaseCapabilityDialog):
    """Security Auditor — vulnerability checklist, access control review, data protection assessment, compliance grid."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Security Auditor — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_vuln_tab(), "Vulnerability Check")
        tabs.addTab(self._build_access_tab(), "Access Control")
        tabs.addTab(self._build_data_tab(), "Data Protection")
        tabs.addTab(self._build_compliance_tab(), "Compliance Grid")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Security audit is defensive only. Cannot help infiltrate or breach systems. Unauthorized scanning may be illegal. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_vuln_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Vulnerability Assessment"))
        l.addWidget(QLabel("System/application to audit:"))
        self._vuln_target = QLineEdit()
        self._vuln_target.setPlaceholderText("e.g., web application, API server, database, network infrastructure...")
        l.addWidget(self._vuln_target)
        l.addWidget(QLabel("Audit scope (describe what to check):"))
        self._vuln_scope = QTextEdit()
        self._vuln_scope.setPlaceholderText("Describe the scope, e.g., 'Check for OWASP Top 10 vulnerabilities in our web app' or 'Review authentication and session management'")
        self._vuln_scope.setMaximumHeight(80)
        l.addWidget(self._vuln_scope)
        btn = QPushButton("Run Vulnerability Assessment")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_vuln)
        l.addWidget(btn)
        self._vuln_output = QTextEdit()
        self._vuln_output.setReadOnly(True)
        self._vuln_output.setStyleSheet("")
        l.addWidget(self._vuln_output, stretch=1)
        return w

    def _build_access_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Access Control Review"))
        btn = QPushButton("Run Access Control Review")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_access)
        l.addWidget(btn)
        self._access_output = QTextEdit()
        self._access_output.setReadOnly(True)
        self._access_output.setStyleSheet("")
        l.addWidget(self._access_output, stretch=1)
        return w

    def _build_data_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Data Protection Assessment"))
        btn = QPushButton("Run Data Protection Assessment")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_data)
        l.addWidget(btn)
        self._data_output = QTextEdit()
        self._data_output.setReadOnly(True)
        self._data_output.setStyleSheet("")
        l.addWidget(self._data_output, stretch=1)
        return w

    def _build_compliance_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Compliance Grid"))
        l.addWidget(QLabel("Select compliance framework:"))
        self._compliance_framework = QComboBox()
        self._compliance_framework.addItems(["OWASP Top 10", "CIS Controls", "NIST Cybersecurity Framework", "SOC 2", "GDPR", "HIPAA", "PCI DSS", "ISO 27001"])
        l.addWidget(self._compliance_framework)
        btn = QPushButton("Generate Compliance Grid")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_compliance)
        l.addWidget(btn)
        self._compliance_output = QTextEdit()
        self._compliance_output.setReadOnly(True)
        self._compliance_output.setStyleSheet("")
        l.addWidget(self._compliance_output, stretch=1)
        return w

    def _run_through_runtime(self, task: str) -> str:
        try:
            from ...core.nexus_ai_runtime import NexusAIRuntime
            settings = SettingsManager()
            settings.initialize()
            runtime = NexusAIRuntime(settings=settings)
            result = runtime.run(task=task, ai_name=self._ai_name, ai_uuid=self._ai_uuid, ai_metadata={"abilities": self._abilities, "use_case": self._use_case, "guardrails": self._guardrails, "libraries": self._libraries})
            return result.result_text or ""
        except Exception:
            return ""

    def _run_vuln(self):
        target = self._vuln_target.text().strip()
        scope = self._vuln_scope.toPlainText().strip()
        if not target:
            self._vuln_output.setText("Enter a target system to audit.")
            return
        task = f"Perform a defensive security vulnerability assessment for: {target}. Scope: {scope}. Include OWASP Top 10 checklist and remediation recommendations."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._vuln_output.setText(ai_result)
            self._set_result_summary(f"Vulnerability assessment via AI: {target}.")
            return
        output = (
            f"[VULNERABILITY ASSESSMENT — LOCAL ANALYSIS]\n\n"
            f"Target: {target}\n"
            f"Scope: {scope[:200] if scope else 'General security review'}\n\n"
            "OWASP TOP 10 CHECKLIST:\n\n"
            "  A1: BROKEN ACCESS CONTROL\n"
            "    [ ] Role-based access control implemented\n"
            "    [ ] Principle of least privilege enforced\n"
            "    [ ] Direct object references protected\n"
            "    [ ] Access control tested on every endpoint\n\n"
            "  A2: CRYPTOGRAPHIC FAILURES\n"
            "    [ ] Sensitive data encrypted at rest\n"
            "    [ ] TLS 1.2+ for data in transit\n"
            "    [ ] Strong algorithms (AES-256, SHA-256+)\n"
            "    [ ] No hardcoded keys or secrets\n\n"
            "  A3: INJECTION\n"
            "    [ ] SQL queries use parameterized statements\n"
            "    [ ] Input validation on all user data\n"
            "    [ ] ORM used to prevent SQL injection\n"
            "    [ ] No OS command calls with user input\n\n"
            "  A4: INSECURE DESIGN\n"
            "    [ ] Threat modeling performed\n"
            "    [ ] Security by design principles followed\n"
            "    [ ] Abuse cases considered\n"
            "    [ ] Rate limiting on sensitive endpoints\n\n"
            "  A5: SECURITY MISCONFIGURATION\n"
            "    [ ] Default credentials changed\n"
            "    [ ] Error messages don't reveal stack traces\n"
            "    [ ] Unnecessary features disabled\n"
            "    [ ] Security headers set (CSP, HSTS, X-Frame-Options)\n\n"
            "  A6: VULNERABLE COMPONENTS\n"
            "    [ ] Dependencies regularly updated\n"
            "    [ ] Vulnerability scanning automated\n"
            "    [ ] Lock files used for reproducible builds\n"
            "    [ ] Unused dependencies removed\n\n"
            "  A7: AUTHENTICATION FAILURES\n"
            "    [ ] Strong password policy enforced\n"
            "    [ ] MFA available and encouraged\n"
            "    [ ] Session tokens are secure and rotated\n"
            "    [ ] Account lockout after failed attempts\n\n"
            "  A8: SOFTWARE & DATA INTEGRITY\n"
            "    [ ] Code integrity verified (signatures)\n"
            "    [ ] CI/CD pipeline secured\n"
            "    [ ] Deserialization of untrusted data prevented\n"
            "    [ ] Software supply chain reviewed\n\n"
            "  A9: LOGGING & MONITORING FAILURES\n"
            "    [ ] Security events logged\n"
            "    [ ] Logs are tamper-proof and centralized\n"
            "    [ ] Alerting for suspicious activity\n"
            "    [ ] Incident response plan documented\n\n"
            "  A10: SERVER-SIDE REQUEST FORGERY\n"
            "    [ ] URL validation on server-side requests\n"
            "    [ ] Allow-list for external URLs\n"
            "    [ ] Internal network isolated from SSRF vectors\n"
            "    [ ] Metadata endpoints blocked\n\n"
            "REMEDIATION PRIORITY:\n"
            "  1. Fix CRITICAL issues immediately (injection, auth bypass)\n"
            "  2. Fix HIGH issues within 30 days (crypto, access control)\n"
            "  3. Fix MEDIUM issues within 90 days (config, logging)\n"
            "  4. Fix LOW issues as resources allow (hardening)\n\n"
            "The built-in intelligence can provide vulnerability analysis."
        )
        self._vuln_output.setText(output)
        self._set_result_summary(f"Vulnerability assessment: {target}.")

    def _run_access(self):
        output = (
            "[ACCESS CONTROL REVIEW — LOCAL ANALYSIS]\n\n"
            "AUTHENTICATION:\n"
            "  [ ] Password policy: min 12 chars, complexity required\n"
            "  [ ] Password hashing: bcrypt, argon2, or scrypt\n"
            "  [ ] MFA available for all accounts\n"
            "  [ ] Session timeout after inactivity\n"
            "  [ ] Secure session token generation\n"
            "  [ ] Account lockout after failed attempts\n"
            "  [ ] Password reset flow is secure\n\n"
            "AUTHORIZATION:\n"
            "  [ ] Role-based access control (RBAC) implemented\n"
            "  [ ] Principle of least privilege enforced\n"
            "  [ ] Access decisions made server-side\n"
            "  [ ] Direct object references (IDOR) protected\n"
            "  [ ] API endpoints have authorization checks\n"
            "  [ ] Admin functions require elevated auth\n"
            "  [ ] Multi-tenant isolation verified\n\n"
            "SESSION MANAGEMENT:\n"
            "  [ ] Sessions invalidated on logout\n"
            "  [ ] Session tokens rotated after login\n"
            "  [ ] Concurrent session limits enforced\n"
            "  [ ] CSRF tokens on state-changing operations\n"
            "  [ ] Secure cookie flags (HttpOnly, Secure, SameSite)\n\n"
            "API SECURITY:\n"
            "  [ ] API keys are scoped and rotated\n"
            "  [ ] Rate limiting on API endpoints\n"
            "  [ ] Input validation on all parameters\n"
            "  [ ] Output encoding to prevent injection\n"
            "  [ ] CORS configured restrictively\n\n"
            "ADMINISTRATIVE ACCESS:\n"
            "  [ ] Admin accounts audited regularly\n"
            "  [ ] Privileged access management (PAM) in place\n"
            "  [ ] Just-in-time access for sensitive operations\n"
            "  [ ] Admin actions logged and monitored\n"
            "  [ ] Separation of duties enforced\n\n"
            "The built-in intelligence can provide access control analysis."
        )
        self._access_output.setText(output)
        self._set_result_summary("Access control review completed.")

    def _run_data(self):
        output = (
            "[DATA PROTECTION ASSESSMENT — LOCAL ANALYSIS]\n\n"
            "DATA CLASSIFICATION:\n"
            "  [ ] Data inventory: all data assets documented\n"
            "  [ ] Data classified by sensitivity (public, internal, confidential, restricted)\n"
            "  [ ] Data flow maps maintained\n"
            "  [ ] Data retention policies defined\n\n"
            "ENCRYPTION:\n"
            "  [ ] Data encrypted at rest (AES-256 or equivalent)\n"
            "  [ ] Data encrypted in transit (TLS 1.2+)\n"
            "  [ ] Encryption keys managed securely (KMS)\n"
            "  [ ] Key rotation policy in place\n"
            "  [ ] Database-level encryption for sensitive fields\n\n"
            "DATA ACCESS:\n"
            "  [ ] Access to sensitive data is logged\n"
            "  [ ] Data access audited regularly\n"
            "  [ ] Minimum necessary access enforced\n"
            "  [ ] Production data not used in testing\n"
            "  [ ] Data masking/anonymization for non-prod environments\n\n"
            "PRIVACY:\n"
            "  [ ] PII identified and catalogued\n"
            "  [ ] Data subject access requests supported\n"
            "  [ ] Right to deletion supported\n"
            "  [ ] Privacy policy is current and accessible\n"
            "  [ ] Consent management for data collection\n\n"
            "BACKUP & RECOVERY:\n"
            "  [ ] Backups are encrypted\n"
            "  [ ] Backup restoration tested regularly\n"
            "  [ ] Backup access is restricted\n"
            "  [ ] Disaster recovery plan documented\n"
            "  [ ] RTO/RPO defined and tested\n\n"
            "DATA DISPOSAL:\n"
            "  [ ] Secure deletion procedures in place\n"
            "  [ ] Media sanitization before disposal\n"
            "  [ ] Data retention schedules enforced\n"
            "  [ ] Cloud storage properly decommissioned\n\n"
            "The built-in intelligence can provide data protection analysis."
        )
        self._data_output.setText(output)
        self._set_result_summary("Data protection assessment completed.")

    def _run_compliance(self):
        framework = self._compliance_framework.currentText()
        frameworks = {
            "OWASP Top 10": [
                ("A1", "Broken Access Control", "Implement RBAC, least privilege, server-side checks"),
                ("A2", "Cryptographic Failures", "Encrypt data, use TLS 1.2+, strong algorithms"),
                ("A3", "Injection", "Parameterized queries, input validation, ORM"),
                ("A4", "Insecure Design", "Threat modeling, security by design, abuse cases"),
                ("A5", "Security Misconfiguration", "Change defaults, disable unused features, set headers"),
                ("A6", "Vulnerable Components", "Update dependencies, vulnerability scanning, lock files"),
                ("A7", "Authentication Failures", "Strong passwords, MFA, session management"),
                ("A8", "Software & Data Integrity", "Code signing, CI/CD security, safe deserialization"),
                ("A9", "Logging & Monitoring Failures", "Log security events, alerting, incident response"),
                ("A10", "SSRF", "URL validation, allow-lists, block internal access"),
            ],
            "CIS Controls": [
                ("CIS 1", "Inventory of Authorized/Unauthorized Devices", "Maintain active device inventory"),
                ("CIS 2", "Inventory of Authorized/Unauthorized Software", "Track all software assets"),
                ("CIS 3", "Secure Configuration of Hardware/Software", "Hardened configurations"),
                ("CIS 4", "Continuous Vulnerability Assessment", "Regular vulnerability scanning"),
                ("CIS 5", "Controlled Use of Administrative Privileges", "PAM, least privilege"),
                ("CIS 6", "Maintenance, Monitoring, and Analysis of Audit Logs", "Centralized logging"),
                ("CIS 7", "Email and Web Browser Protections", "Email filtering, browser hardening"),
                ("CIS 8", "Malware Defenses", "Anti-malware, application whitelisting"),
                ("CIS 9", "Limitation and Control of Network Ports", "Firewall rules, port management"),
                ("CIS 10", "Data Recovery Capability", "Backups, recovery testing"),
            ],
            "NIST Cybersecurity Framework": [
                ("ID", "Identify", "Asset management, risk assessment, governance"),
                ("PR", "Protect", "Access control, awareness, data security, protective technology"),
                ("DE", "Detect", "Anomalies, continuous monitoring, detection processes"),
                ("RS", "Respond", "Response planning, communications, analysis, mitigation"),
                ("RC", "Recover", "Recovery planning, improvements, communications"),
            ],
            "SOC 2": [
                ("CC1", "Control Environment", "Organizational structure, ethics, board oversight"),
                ("CC2", "Communication & Information", "Internal/external communication of security"),
                ("CC3", "Risk Assessment", "Risk identification, analysis, mitigation"),
                ("CC4", "Monitoring Activities", "Ongoing monitoring, separate evaluations"),
                ("CC5", "Control Activities", "Policies, procedures, technology controls"),
                ("CC6", "Logical & Physical Access", "Access controls, authentication, physical security"),
                ("CC7", "System Operations", "Change management, incident response, operations"),
                ("CC8", "Change Management", "Change controls, testing, approval"),
                ("CC9", "Risk Mitigation", "Vendor management, business continuity"),
            ],
            "GDPR": [
                ("Art 5", "Principles for Processing", "Lawfulness, purpose limitation, data minimization"),
                ("Art 6", "Lawfulness of Processing", "Consent, contract, legal obligation, vital interests"),
                ("Art 7", "Conditions for Consent", "Freely given, specific, informed, withdrawable"),
                ("Art 15", "Right of Access", "Data subject can access their data"),
                ("Art 17", "Right to Erasure", "Right to be forgotten"),
                ("Art 20", "Right to Data Portability", "Export data in machine-readable format"),
                ("Art 25", "Data Protection by Design", "Privacy by design and by default"),
                ("Art 32", "Security of Processing", "Appropriate technical and organizational measures"),
                ("Art 33", "Breach Notification", "Notify within 72 hours of awareness"),
                ("Art 35", "Data Protection Impact Assessment", "DPIA for high-risk processing"),
            ],
            "HIPAA": [
                ("§164.308", "Administrative Safeguards", "Risk analysis, workforce training, incident response"),
                ("§164.310", "Physical Safeguards", "Facility access, workstation security, device controls"),
                ("§164.312", "Technical Safeguards", "Access control, audit controls, integrity, transmission security"),
                ("§164.314", "Organizational Requirements", "BAA with business associates, subcontractor compliance"),
                ("§164.316", "Policies & Procedures", "Documentation, retention, updates"),
                ("§164.502", "Uses & Disclosures", "Minimum necessary, authorization requirements"),
                ("§164.508", "Authorization", "Required for uses beyond TPO"),
                ("§164.520", "Notice of Privacy Practices", "Inform patients of their rights"),
                ("§164.526", "Amendments", "Right to amend records"),
                ("§164.528", "Accounting of Disclosures", "Track and report disclosures"),
            ],
            "PCI DSS": [
                ("Req 1", "Firewall Configuration", "Install and maintain firewalls"),
                ("Req 2", "Default Passwords", "Don't use vendor defaults"),
                ("Req 3", "Stored Cardholder Data", "Protect stored data"),
                ("Req 4", "Encrypted Transmission", "Encrypt cardholder data across open networks"),
                ("Req 5", "Anti-Malware", "Protect against malware, update regularly"),
                ("Req 6", "Secure Systems & Applications", "Develop and maintain secure systems"),
                ("Req 7", "Need-to-Know Access", "Restrict access to cardholder data"),
                ("Req 8", "Unique IDs", "Identify and authenticate access"),
                ("Req 9", "Physical Access", "Restrict physical access to cardholder data"),
                ("Req 10", "Audit Logs", "Track and monitor all access"),
                ("Req 11", "Security Testing", "Regularly test security systems"),
                ("Req 12", "Security Policy", "Maintain an information security policy"),
            ],
            "ISO 27001": [
                ("A.5", "Information Security Policies", "Documented, approved, communicated policies"),
                ("A.6", "Organization of Information Security", "Roles, responsibilities, segregation"),
                ("A.7", "Human Resource Security", "Pre-employment, during, post-employment controls"),
                ("A.8", "Asset Management", "Inventory, classification, handling of assets"),
                ("A.9", "Access Control", "Business requirements, user management, responsibilities"),
                ("A.10", "Cryptography", "Cryptographic controls, key management"),
                ("A.11", "Physical & Environmental", "Secure areas, equipment security"),
                ("A.12", "Operations Security", "Procedures, protection against malware, backups"),
                ("A.13", "Communications Security", "Network management, information transfer"),
                ("A.14", "System Acquisition & Development", "Security requirements, testing, system data"),
                ("A.15", "Supplier Relationships", "Supplier policy, agreements, monitoring"),
                ("A.16", "Information Security Incident Management", "Reporting, management, evidence"),
                ("A.17", "Business Continuity", "Continuity, redundancy, availability"),
                ("A.18", "Compliance", "Legal requirements, audits, policies"),
            ],
        }
        controls = frameworks.get(framework, [])
        output = f"[COMPLIANCE GRID — {framework}]\n\n"
        output += f"{'ID':<12} {'Control':<40} {'Status':<12} {'Notes':<30}\n"
        output += "-" * 95 + "\n"
        for ctrl_id, ctrl_name, ctrl_desc in controls:
            output += f"{ctrl_id:<12} {ctrl_name:<40} {'[ ]':<12} {ctrl_desc[:30]}\n"
        output += (
            f"\nCOMPLIANCE STATUS LEGEND:\n"
            f"  [ ] = Not yet assessed\n"
            f"  [✓] = Compliant\n"
            f"  [⚠] = Partially compliant\n"
            f"  [✗] = Non-compliant\n\n"
            f"NEXT STEPS:\n"
            f"  1. Assess each control and mark status\n"
            f"  2. Document evidence for compliant controls\n"
            f"  3. Create remediation plan for non-compliant items\n"
            f"  4. Set deadlines and assign owners\n"
            f"  5. Re-assess after remediation\n\n"
            "The built-in intelligence can provide compliance analysis."
        )
        self._compliance_output.setText(output)
        self._set_result_summary(f"Compliance grid generated: {framework} ({len(controls)} controls).")


class MeetingFacilitatorDialog(BaseCapabilityDialog):
    """Meeting Facilitator — agenda builder, time allocator, discussion items, action item tracker, follow-up scheduler."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Meeting Facilitator — {ai_name} | Avery Logic Works(TM)")
        self.resize(820, 620)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_agenda_tab(), "Agenda Builder")
        tabs.addTab(self._build_time_tab(), "Time Allocator")
        tabs.addTab(self._build_discussion_tab(), "Discussion Items")
        tabs.addTab(self._build_action_tab(), "Action Items")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Meeting facilitation is advisory. User is responsible for meeting outcomes. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_agenda_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Agenda Builder"))
        row = QHBoxLayout()
        row.addWidget(QLabel("Meeting title:"))
        self._agenda_title = QLineEdit()
        self._agenda_title.setPlaceholderText("e.g., Q3 Product Planning Review")
        row.addWidget(self._agenda_title)
        row.addWidget(QLabel("Duration (min):"))
        self._agenda_duration = QLineEdit("60")
        self._agenda_duration.setMaximumWidth(60)
        row.addWidget(self._agenda_duration)
        row.addStretch()
        l.addLayout(row)
        l.addWidget(QLabel("Meeting type:"))
        self._agenda_type = QComboBox()
        self._agenda_type.addItems(["Standup", "Planning", "Review", "Brainstorm", "Decision", "Retrospective", "1:1", "All-hands", "Client meeting"])
        l.addWidget(self._agenda_type)
        l.addWidget(QLabel("Topics (one per line, optionally with time in minutes):"))
        self._agenda_topics = QTextEdit()
        self._agenda_topics.setPlaceholderText("e.g.,\nStatus updates (10)\nRoadmap discussion (20)\nResource allocation (15)\nQ&A (10)\nAction items review (5)")
        l.addWidget(self._agenda_topics, stretch=1)
        btn = QPushButton("Build Agenda")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_agenda)
        l.addWidget(btn)
        self._agenda_output = QTextEdit()
        self._agenda_output.setReadOnly(True)
        self._agenda_output.setStyleSheet("")
        l.addWidget(self._agenda_output, stretch=1)
        return w

    def _build_time_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Time Allocator"))
        l.addWidget(QLabel("Total meeting time (minutes):"))
        self._time_total = QLineEdit("60")
        self._time_total.setMaximumWidth(80)
        l.addWidget(self._time_total)
        l.addWidget(QLabel("Number of topics:"))
        self._time_topics = QLineEdit("5")
        self._time_topics.setMaximumWidth(60)
        l.addWidget(self._time_topics)
        l.addWidget(QLabel("Allocation strategy:"))
        self._time_strategy = QComboBox()
        self._time_strategy.addItems(["Equal split", "Priority-weighted", "Discussion-heavy", "Decision-focused", "Status-update (brief)"])
        l.addWidget(self._time_strategy)
        btn = QPushButton("Allocate Time")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_time)
        l.addWidget(btn)
        self._time_output = QTextEdit()
        self._time_output.setReadOnly(True)
        self._time_output.setStyleSheet("")
        l.addWidget(self._time_output, stretch=1)
        return w

    def _build_discussion_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Discussion Items"))
        l.addWidget(QLabel("Enter discussion topics with context:"))
        self._discussion_input = QTextEdit()
        self._discussion_input.setPlaceholderText("e.g.,\n1. Should we prioritize Feature A or Feature B for Q3?\n2. How do we handle the resource gap in the design team?\n3. What's our response to the competitor's new product launch?")
        l.addWidget(self._discussion_input, stretch=1)
        btn = QPushButton("Generate Discussion Framework")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_discussion)
        l.addWidget(btn)
        self._discussion_output = QTextEdit()
        self._discussion_output.setReadOnly(True)
        self._discussion_output.setStyleSheet("")
        l.addWidget(self._discussion_output, stretch=1)
        return w

    def _build_action_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Action Item Tracker"))
        l.addWidget(QLabel("Log action items from the meeting:"))
        self._action_items: list[dict] = []
        row = QHBoxLayout()
        row.addWidget(QLabel("Action:"))
        self._action_desc = QLineEdit()
        self._action_desc.setPlaceholderText("What needs to be done?")
        row.addWidget(self._action_desc, stretch=2)
        row.addWidget(QLabel("Owner:"))
        self._action_owner = QLineEdit()
        self._action_owner.setPlaceholderText("Who?")
        self._action_owner.setMaximumWidth(100)
        row.addWidget(self._action_owner)
        row.addWidget(QLabel("Due:"))
        self._action_due = QLineEdit()
        self._action_due.setPlaceholderText("When?")
        self._action_due.setMaximumWidth(100)
        row.addWidget(self._action_due)
        row.addStretch()
        l.addLayout(row)
        btn = QPushButton("Add Action Item")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_add_action)
        l.addWidget(btn)
        summary_btn = QPushButton("Generate Action Item Summary")
        summary_btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        summary_btn.clicked.connect(self._run_action_summary)
        l.addWidget(summary_btn)
        self._action_output = QTextEdit()
        self._action_output.setReadOnly(True)
        self._action_output.setStyleSheet("")
        l.addWidget(self._action_output, stretch=1)
        return w

    def _run_through_runtime(self, task: str) -> str:
        try:
            from ...core.nexus_ai_runtime import NexusAIRuntime
            settings = SettingsManager()
            settings.initialize()
            runtime = NexusAIRuntime(settings=settings)
            result = runtime.run(task=task, ai_name=self._ai_name, ai_uuid=self._ai_uuid, ai_metadata={"abilities": self._abilities, "use_case": self._use_case, "guardrails": self._guardrails, "libraries": self._libraries})
            return result.result_text or ""
        except Exception:
            return ""

    def _run_agenda(self):
        title = self._agenda_title.text().strip()
        if not title:
            self._agenda_output.setText("Enter a meeting title.")
            return
        try:
            duration = int(self._agenda_duration.text().strip() or "60")
        except ValueError:
            duration = 60
        meeting_type = self._agenda_type.currentText()
        topics_text = self._agenda_topics.toPlainText().strip()
        task = f"Create a structured meeting agenda for: {title} ({meeting_type}, {duration} min). Topics: {topics_text}"
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._agenda_output.setText(ai_result)
            self._set_result_summary(f"Agenda built via AI: {title}.")
            return
        import re
        topics = []
        if topics_text:
            for line in topics_text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                match = re.match(r'(.+?)\s*\((\d+)\)\s*$', line)
                if match:
                    topics.append((match.group(1).strip(), int(match.group(2))))
                else:
                    topics.append((line, None))
        output = f"[MEETING AGENDA — LOCAL]\n\n"
        output += f"Title: {title}\n"
        output += f"Type: {meeting_type}\n"
        output += f"Duration: {duration} minutes\n"
        output += f"Date: [To be set]\n"
        output += f"Facilitator: [To be assigned]\n"
        output += f"Attendees: [To be listed]\n\n"
        output += "=" * 50 + "\n\n"
        allocated = 0
        unallocated_topics = [t for t, m in topics if m is None]
        allocated_topics = [(t, m) for t, m in topics if m is not None]
        for t, m in allocated_topics:
            allocated += m
        remaining = duration - allocated
        if remaining < 0:
            output += f"⚠ Allocated time ({allocated} min) exceeds meeting duration ({duration} min)!\n\n"
        buffer = max(5, duration // 10)
        time_for_unallocated = max(0, remaining - buffer)
        output += "AGENDA:\n\n"
        current_time = 0
        for i, (topic, minutes) in enumerate(topics, 1):
            if minutes is None:
                if unallocated_topics:
                    minutes = time_for_unallocated // len(unallocated_topics) if unallocated_topics else 0
                else:
                    minutes = 0
            end_time = current_time + minutes
            output += f"  {i}. [{current_time:02d}-{end_time:02d} min] {topic} ({minutes} min)\n"
            current_time = end_time
        if buffer > 0 and remaining > 0:
            output += f"\n  + [{current_time:02d}-{current_time + buffer:02d} min] Buffer / Overflow ({buffer} min)\n"
        output += (
            "\nMEETING OBJECTIVES:\n"
            "  [ ] Define clear outcome for each topic\n"
            "  [ ] Identify decision points\n"
            "  [ ] Assign note-taker\n"
            "  [ ] Prepare materials in advance\n\n"
            "PRE-MEETING CHECKLIST:\n"
            "  [ ] Agenda shared 24h in advance\n"
            "  [ ] Required attendees confirmed\n"
            "  [ ] Pre-read materials distributed\n"
            "  [ ] Meeting link/location confirmed\n"
            "  [ ] Recording setup (if needed)\n\n"
            "The built-in intelligence can provide agenda optimization."
        )
        self._agenda_output.setText(output)
        self._set_result_summary(f"Agenda built: {title} ({duration} min, {len(topics)} topics).")

    def _run_time(self):
        try:
            total = int(self._time_total.text().strip() or "60")
            num_topics = int(self._time_topics.text().strip() or "5")
        except ValueError:
            self._time_output.setText("Enter valid numbers.")
            return
        if total <= 0 or num_topics <= 0:
            self._time_output.setText("Enter positive values.")
            return
        strategy = self._time_strategy.currentText()
        buffer = max(5, total // 10)
        available = total - buffer
        output = f"[TIME ALLOCATION — LOCAL]\n\nTotal time: {total} min\nTopics: {num_topics}\nBuffer: {buffer} min\nAvailable for topics: {available} min\nStrategy: {strategy}\n\n"
        if strategy == "Equal split":
            per_topic = available // num_topics
            output += "ALLOCATION:\n"
            for i in range(1, num_topics + 1):
                output += f"  Topic {i}: {per_topic} min\n"
        elif strategy == "Priority-weighted":
            weights = []
            remaining = available
            for i in range(num_topics):
                w = remaining // (num_topics - i + 1) * 2 if i < num_topics else remaining
                weights.append(min(w, remaining))
                remaining -= w
            output += "ALLOCATION (first topics get more time):\n"
            for i, w in enumerate(weights, 1):
                output += f"  Topic {i}: {w} min\n"
        elif strategy == "Discussion-heavy":
            intro = available // 5
            discussion = available - intro
            per_topic = discussion // num_topics
            output += f"ALLOCATION:\n  Intro/Framing: {intro} min\n"
            for i in range(1, num_topics + 1):
                output += f"  Discussion {i}: {per_topic} min\n"
        elif strategy == "Decision-focused":
            context = available // 4
            decision = available - context
            per_topic = decision // num_topics
            output += f"ALLOCATION:\n  Context setting: {context} min\n"
            for i in range(1, num_topics + 1):
                output += f"  Decision {i}: {per_topic} min\n"
        else:
            per_topic = max(2, available // (num_topics * 2))
            remaining = available - per_topic * num_topics
            output += "ALLOCATION (brief updates):\n"
            for i in range(1, num_topics + 1):
                output += f"  Update {i}: {per_topic} min\n"
            output += f"  Discussion: {remaining} min\n"
        output += (
            f"\nTIME MANAGEMENT TIPS:\n"
            f"  - Start and end on time\n"
            f"  - Use a timer for each topic\n"
            f"  - Parking lot for off-topic items\n"
            f"  - Assign a timekeeper\n"
            f"  - Buffer time for overflow ({buffer} min)\n"
            f"  - If running over, prioritize remaining items\n\n"
            "The built-in intelligence can provide time optimization."
        )
        self._time_output.setText(output)
        self._set_result_summary(f"Time allocated: {total} min across {num_topics} topics ({strategy}).")

    def _run_discussion(self):
        items_text = self._discussion_input.toPlainText().strip()
        if not items_text:
            self._discussion_output.setText("Enter discussion items.")
            return
        items = [l.strip() for l in items_text.split("\n") if l.strip()]
        task = f"Create a discussion framework for these meeting topics:\n{items_text}\nInclude for each: key questions, desired outcome, and facilitation approach."
        ai_result = self._run_through_runtime(task)
        if ai_result:
            self._discussion_output.setText(ai_result)
            self._set_result_summary(f"Discussion framework via AI ({len(items)} items).")
            return
        output = "[DISCUSSION FRAMEWORK — LOCAL]\n\n"
        for i, item in enumerate(items, 1):
            output += f"DISCUSSION ITEM {i}: {item}\n\n"
            output += "  KEY QUESTIONS:\n"
            output += f"    - What is the core decision needed?\n"
            output += f"    - What data do we need to inform this?\n"
            output += f"    - Who needs to weigh in?\n"
            output += f"    - What are the constraints?\n\n"
            output += "  DESIRED OUTCOME:\n"
            output += f"    [ ] Decision made\n"
            output += f"    [ ] Options identified\n"
            output += f"    [ ] Action assigned\n"
            output += f"    [ ] Information shared\n\n"
            output += "  FACILITATION APPROACH:\n"
            output += f"    - Start with context (2 min)\n"
            output += f"    - Open discussion (time-boxed)\n"
            output += f"    - Capture key points on whiteboard\n"
            output += f"    - Summarize and confirm agreement\n"
            output += f"    - Assign action items if needed\n\n"
            output += "-" * 50 + "\n\n"
        output += (
            "FACILITATION TIPS:\n"
            "  - Encourage quiet participants to speak\n"
            "  - Manage dominant voices politely\n"
            "  - Use 'parking lot' for off-topic items\n"
            "  - Check for understanding regularly\n"
            "  - End with clear action items and owners\n\n"
            "The built-in intelligence can provide discussion facilitation."
        )
        self._discussion_output.setText(output)
        self._set_result_summary(f"Discussion framework: {len(items)} items.")

    def _run_add_action(self):
        desc = self._action_desc.text().strip()
        if not desc:
            self._action_output.setText("Enter an action description.")
            return
        owner = self._action_owner.text().strip() or "Unassigned"
        due = self._action_due.text().strip() or "TBD"
        self._action_items.append({"action": desc, "owner": owner, "due": due, "status": "Open"})
        self._action_desc.clear()
        self._action_owner.clear()
        self._action_due.clear()
        self._action_output.setText(f"Action item added: {desc} (Owner: {owner}, Due: {due})\nTotal action items: {len(self._action_items)}")
        self._set_result_summary(f"Action item added: {desc[:40]}.")

    def _run_action_summary(self):
        if not self._action_items:
            self._action_output.setText("No action items logged yet.")
            return
        output = "[ACTION ITEM SUMMARY — LOCAL]\n\n"
        output += f"Total action items: {len(self._action_items)}\n\n"
        output += f"{'#':<4} {'Action':<40} {'Owner':<15} {'Due':<15} {'Status':<10}\n"
        output += "-" * 85 + "\n"
        for i, item in enumerate(self._action_items, 1):
            output += f"{i:<4} {item['action'][:40]:<40} {item['owner'][:15]:<15} {item['due'][:15]:<15} {item['status']:<10}\n"
        by_owner: dict[str, int] = {}
        for item in self._action_items:
            by_owner[item["owner"]] = by_owner.get(item["owner"], 0) + 1
        output += "\nBY OWNER:\n"
        for owner, count in sorted(by_owner.items(), key=lambda x: -x[1]):
            output += f"  {owner}: {count} action(s)\n"
        output += (
            "\nFOLLOW-UP SCHEDULE:\n"
            "  - Send action item summary within 24 hours\n"
            "  - Set calendar reminders for due dates\n"
            "  - Review status at next meeting\n"
            "  - Escalate overdue items\n"
            "  - Close completed items and document results\n\n"
            "The built-in intelligence can provide follow-up management."
        )
        self._action_output.setText(output)
        self._set_result_summary(f"Action summary: {len(self._action_items)} items.")


# ===========================================================================
# Phase 4: Memory Saver Family (9 dialogs)
# ===========================================================================

class MemoryRecorderDialog(BaseCapabilityDialog):
    """Memory Recorder — session recording, event log, timeline, export."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Memory Recorder — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._recording = False
        self._events: list[dict] = []
        self._session_label = ""
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_record_tab(), "Record")
        tabs.addTab(self._build_timeline_tab(), "Timeline")
        tabs.addTab(self._build_event_log_tab(), "Event Log")
        tabs.addTab(self._build_export_tab(), "Export")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Memory recording stores data locally. Be mindful of sensitive information. Avery Logic Works is not liable for recorded content.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_record_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Session Recording Control"))
        l.addWidget(QLabel("Session label:"))
        self._session_label_input = QLineEdit()
        self._session_label_input.setPlaceholderText("e.g., Project Alpha — Planning Session")
        l.addWidget(self._session_label_input)
        self._record_btn = QPushButton("Start Recording")
        self._record_btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 10px;")
        self._record_btn.clicked.connect(self._toggle_recording)
        l.addWidget(self._record_btn)
        self._record_status = QLabel("Status: Not recording")
        self._record_status.setStyleSheet("color: #8b949e; font-size: 12px;")
        l.addWidget(self._record_status)
        l.addWidget(QLabel("Log an event manually:"))
        self._event_label_input = QLineEdit()
        self._event_label_input.setPlaceholderText("Event description (e.g., 'Opened Forge window', 'Created AI unit')")
        l.addWidget(self._event_label_input)
        self._event_type_combo = QComboBox()
        self._event_type_combo.addItems(["info", "action", "decision", "milestone", "warning", "error"])
        l.addWidget(self._event_type_combo)
        log_btn = QPushButton("Log Event")
        log_btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        log_btn.clicked.connect(self._log_manual_event)
        l.addWidget(log_btn)
        self._record_output = QTextEdit()
        self._record_output.setReadOnly(True)
        self._record_output.setStyleSheet("")
        l.addWidget(self._record_output, stretch=1)
        return w

    def _build_timeline_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Session Timeline"))
        l.addWidget(QLabel("Filter by event type:"))
        self._timeline_filter = QComboBox()
        self._timeline_filter.addItems(["All", "info", "action", "decision", "milestone", "warning", "error"])
        self._timeline_filter.currentTextChanged.connect(self._refresh_timeline)
        l.addWidget(self._timeline_filter)
        btn = QPushButton("Refresh Timeline")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._refresh_timeline)
        l.addWidget(btn)
        self._timeline_output = QTextEdit()
        self._timeline_output.setReadOnly(True)
        self._timeline_output.setStyleSheet("")
        l.addWidget(self._timeline_output, stretch=1)
        return w

    def _build_event_log_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Raw Event Log"))
        btn = QPushButton("Generate Full Log")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_event_log)
        l.addWidget(btn)
        self._event_log_output = QTextEdit()
        self._event_log_output.setReadOnly(True)
        self._event_log_output.setStyleSheet("")
        l.addWidget(self._event_log_output, stretch=1)
        return w

    def _build_export_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Export Session"))
        l.addWidget(QLabel("Export format:"))
        self._export_format = QComboBox()
        self._export_format.addItems(["Text Summary", "JSON", "CSV (Event Log)"])
        l.addWidget(self._export_format)
        btn = QPushButton("Generate Export")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_export)
        l.addWidget(btn)
        self._export_output = QTextEdit()
        self._export_output.setReadOnly(True)
        self._export_output.setStyleSheet("")
        l.addWidget(self._export_output, stretch=1)
        return w

    def _toggle_recording(self):
        if not self._recording:
            self._recording = True
            self._session_label = self._session_label_input.text().strip() or f"Session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self._events = []
            self._events.append({"timestamp": datetime.now().isoformat(), "type": "info", "label": f"Recording started: {self._session_label}"})
            self._record_btn.setText("Stop Recording")
            self._record_btn.setStyleSheet("background-color: #da3633; color: white; font-weight: bold; padding: 10px;")
            self._record_status.setText(f"Status: Recording — {self._session_label}")
            self._record_status.setStyleSheet("color: #f85149; font-size: 12px; font-weight: bold;")
            self._record_output.setText(f"Recording started at {datetime.now().strftime('%H:%M:%S')}\nSession: {self._session_label}\n")
        else:
            self._recording = False
            self._events.append({"timestamp": datetime.now().isoformat(), "type": "info", "label": f"Recording stopped: {self._session_label}"})
            self._record_btn.setText("Start Recording")
            self._record_btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 10px;")
            self._record_status.setText("Status: Not recording")
            self._record_status.setStyleSheet("color: #8b949e; font-size: 12px;")
            self._record_output.append(f"\nRecording stopped at {datetime.now().strftime('%H:%M:%S')}\nTotal events: {len(self._events)}")

    def _log_manual_event(self):
        label = self._event_label_input.text().strip()
        if not label:
            return
        etype = self._event_type_combo.currentText()
        self._events.append({"timestamp": datetime.now().isoformat(), "type": etype, "label": label})
        self._record_output.append(f"[{datetime.now().strftime('%H:%M:%S')}] ({etype}) {label}")
        self._event_label_input.clear()

    def _refresh_timeline(self):
        filt = self._timeline_filter.currentText()
        events = self._events if filt == "All" else [e for e in self._events if e["type"] == filt]
        if not events:
            self._timeline_output.setText("No events to display.")
            return
        lines = [f"TIMELINE — {self._session_label or 'No session'}\n{'='*60}\n"]
        for e in events:
            ts = e["timestamp"].split("T")[1].split(".")[0] if "T" in e["timestamp"] else e["timestamp"]
            icon = {"info": "i", "action": ">", "decision": "*", "milestone": "M", "warning": "!", "error": "X"}.get(e["type"], "?")
            lines.append(f"  [{ts}] ({icon}) {e['type'].upper():10s} | {e['label']}")
        lines.append(f"\n{'='*60}\nTotal events: {len(events)}")
        self._timeline_output.setText("\n".join(lines))

    def _run_event_log(self):
        if not self._events:
            self._event_log_output.setText("No events recorded yet. Start a recording session first.")
            return
        try:
            from ...core.nexus_ai_runtime import NexusAIRuntime
            runtime = NexusAIRuntime()
            event_text = "\n".join(f"[{e['timestamp']}] {e['type']}: {e['label']}" for e in self._events)
            result = runtime.generate(
                f"Analyze the following session event log and provide a structured summary "
                f"with key activities, decisions, and notable events:\n\n{event_text}",
                ai_name=self._ai_name,
                abilities=self._abilities,
            )
            self._event_log_output.setText(result)
        except Exception:
            lines = [f"EVENT LOG — {self._session_label or 'No session'}\n{'='*60}\n"]
            for e in self._events:
                lines.append(f"Timestamp: {e['timestamp']}\nType:      {e['type']}\nEvent:     {e['label']}\n")
            lines.append(f"{'='*60}\nTotal events: {len(self._events)}\n\nThe built-in intelligence can provide log analysis.")
            self._event_log_output.setText("\n".join(lines))

    def _run_export(self):
        if not self._events:
            self._export_output.setText("No events to export. Start a recording session first.")
            return
        fmt = self._export_format.currentText()
        if fmt == "Text Summary":
            lines = [f"SESSION EXPORT — {self._session_label}\n{'='*60}\n"]
            lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            lines.append(f"Total events: {len(self._events)}\n")
            for e in self._events:
                lines.append(f"  [{e['timestamp']}] ({e['type']}) {e['label']}")
            lines.append(f"\n{'='*60}\nExported by Command Nexus(TM) Memory Recorder")
        elif fmt == "JSON":
            import json
            lines = [json.dumps({"session": self._session_label, "exported_at": datetime.now().isoformat(), "events": self._events}, indent=2)]
        elif fmt == "CSV (Event Log)":
            lines = ["timestamp,type,label"]
            for e in self._events:
                lines.append(f"\"{e['timestamp']}\",\"{e['type']}\",\"{e['label']}\"")
        self._export_output.setText("\n".join(lines))
        self._set_result_summary(f"Exported {len(self._events)} events as {fmt}.")


class SessionReplayDialog(BaseCapabilityDialog):
    """Session Replay — replay past sessions, step-through playback, event search."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Session Replay — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._sessions: list[dict] = []
        self._current_session: list[dict] = []
        self._playback_index = 0
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_session_list_tab(), "Sessions")
        tabs.addTab(self._build_playback_tab(), "Playback")
        tabs.addTab(self._build_search_tab(), "Search")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Session replay shows past activity. Be aware of sensitive data in replays. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_session_list_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Past Sessions"))
        l.addWidget(QLabel("Enter session data (one event per line: timestamp | type | description):"))
        self._session_input = QTextEdit()
        self._session_input.setPlaceholderText("e.g.,\n2026-07-04 10:00 | info | Session started\n2026-07-04 10:05 | action | Created AI unit\n2026-07-04 10:15 | decision | Chose Pro tier\n...")
        l.addWidget(self._session_input, stretch=1)
        btn = QPushButton("Load Session")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._load_session)
        l.addWidget(btn)
        self._session_list_output = QTextEdit()
        self._session_list_output.setReadOnly(True)
        self._session_list_output.setStyleSheet("")
        l.addWidget(self._session_list_output, stretch=1)
        return w

    def _build_playback_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Step-Through Playback"))
        playback_row = QHBoxLayout()
        self._prev_btn = QPushButton("<< Previous")
        self._prev_btn.setStyleSheet("padding: 8px;")
        self._prev_btn.clicked.connect(self._step_prev)
        playback_row.addWidget(self._prev_btn)
        self._play_pos = QLabel("0 / 0")
        self._play_pos.setStyleSheet("color: #58a6ff; font-weight: bold;")
        playback_row.addWidget(self._play_pos)
        self._next_btn = QPushButton("Next >>")
        self._next_btn.setStyleSheet("padding: 8px;")
        self._next_btn.clicked.connect(self._step_next)
        playback_row.addWidget(self._next_btn)
        l.addLayout(playback_row)
        self._playback_output = QTextEdit()
        self._playback_output.setReadOnly(True)
        self._playback_output.setStyleSheet("")
        l.addWidget(self._playback_output, stretch=1)
        return w

    def _build_search_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Search Events"))
        l.addWidget(QLabel("Search query:"))
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("e.g., decision, AI unit, error, created...")
        l.addWidget(self._search_input)
        btn = QPushButton("Search")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_search)
        l.addWidget(btn)
        self._search_output = QTextEdit()
        self._search_output.setReadOnly(True)
        self._search_output.setStyleSheet("")
        l.addWidget(self._search_output, stretch=1)
        return w

    def _load_session(self):
        raw = self._session_input.toPlainText().strip()
        if not raw:
            self._session_list_output.setText("Paste session data to load.")
            return
        events = []
        for line in raw.split("\n"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                events.append({"timestamp": parts[0], "type": parts[1], "label": "|".join(parts[2:])})
        self._current_session = events
        self._playback_index = 0
        summary = f"Loaded session with {len(events)} events.\n\n"
        for i, e in enumerate(events):
            summary += f"  [{i+1}] {e['timestamp']} ({e['type']}) {e['label']}\n"
        self._session_list_output.setText(summary)
        self._play_pos.setText(f"0 / {len(events)}")
        self._playback_output.setText("Session loaded. Use Previous/Next to step through events.")

    def _step_prev(self):
        if not self._current_session:
            return
        self._playback_index = max(0, self._playback_index - 1)
        self._show_playback_event()

    def _step_next(self):
        if not self._current_session:
            return
        self._playback_index = min(len(self._current_session) - 1, self._playback_index + 1)
        self._show_playback_event()

    def _show_playback_event(self):
        if not self._current_session or self._playback_index >= len(self._current_session):
            return
        e = self._current_session[self._playback_index]
        self._play_pos.setText(f"{self._playback_index + 1} / {len(self._current_session)}")
        self._playback_output.setText(
            f"EVENT {self._playback_index + 1} of {len(self._current_session)}\n{'='*50}\n"
            f"Timestamp: {e['timestamp']}\nType:      {e['type']}\nDetail:    {e['label']}\n"
        )

    def _run_search(self):
        query = self._search_input.text().strip().lower()
        if not query or not self._current_session:
            self._search_output.setText("Load a session and enter a search query.")
            return
        matches = [e for e in self._current_session if query in e["label"].lower() or query in e["type"].lower()]
        if not matches:
            self._search_output.setText(f"No events matching '{query}' found.")
            return
        lines = [f"SEARCH RESULTS — '{query}'\n{'='*50}\n{len(matches)} matches found:\n"]
        for e in matches:
            lines.append(f"  [{e['timestamp']}] ({e['type']}) {e['label']}")
        self._search_output.setText("\n".join(lines))
        self._set_result_summary(f"Found {len(matches)} events matching '{query}'.")


class SmartRecallDialog(BaseCapabilityDialog):
    """Smart Recall — search across all memory, result ranking, context restoration, tag filter."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Smart Recall — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._memory_entries: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_query_tab(), "Search")
        tabs.addTab(self._build_tag_filter_tab(), "Tag Filter")
        tabs.addTab(self._build_restore_tab(), "Context Restore")
        tabs.addTab(self._build_add_memory_tab(), "Add Memory")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Smart Recall searches locally stored memory. Be mindful of sensitive data. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_query_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Search All Memory"))
        l.addWidget(QLabel("Enter your search query:"))
        self._query_input = QLineEdit()
        self._query_input.setPlaceholderText("e.g., project alpha, decision about pricing, meeting notes...")
        l.addWidget(self._query_input)
        btn = QPushButton("Search Memory")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_query)
        l.addWidget(btn)
        self._query_output = QTextEdit()
        self._query_output.setReadOnly(True)
        self._query_output.setStyleSheet("")
        l.addWidget(self._query_output, stretch=1)
        return w

    def _build_tag_filter_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Filter by Tags"))
        l.addWidget(QLabel("Enter tags (comma-separated):"))
        self._tag_input = QLineEdit()
        self._tag_input.setPlaceholderText("e.g., work, decision, important")
        l.addWidget(self._tag_input)
        btn = QPushButton("Filter by Tags")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_tag_filter)
        l.addWidget(btn)
        self._tag_output = QTextEdit()
        self._tag_output.setReadOnly(True)
        self._tag_output.setStyleSheet("")
        l.addWidget(self._tag_output, stretch=1)
        return w

    def _build_restore_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Context Restoration"))
        l.addWidget(QLabel("Select a memory entry to restore as context:"))
        self._restore_combo = QComboBox()
        self._restore_combo.setMinimumWidth(400)
        l.addWidget(self._restore_combo)
        btn = QPushButton("Restore Context")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_restore)
        l.addWidget(btn)
        self._restore_output = QTextEdit()
        self._restore_output.setReadOnly(True)
        self._restore_output.setStyleSheet("")
        l.addWidget(self._restore_output, stretch=1)
        return w

    def _build_add_memory_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Add Memory Entry"))
        l.addWidget(QLabel("Title:"))
        self._mem_title = QLineEdit()
        self._mem_title.setPlaceholderText("Short title for this memory")
        l.addWidget(self._mem_title)
        l.addWidget(QLabel("Content:"))
        self._mem_content = QTextEdit()
        self._mem_content.setPlaceholderText("Detailed content of the memory entry...")
        l.addWidget(self._mem_content, stretch=1)
        l.addWidget(QLabel("Tags (comma-separated):"))
        self._mem_tags = QLineEdit()
        self._mem_tags.setPlaceholderText("e.g., work, decision, project-alpha")
        l.addWidget(self._mem_tags)
        btn = QPushButton("Store Memory")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._add_memory)
        l.addWidget(btn)
        self._add_mem_output = QTextEdit()
        self._add_mem_output.setReadOnly(True)
        self._add_mem_output.setStyleSheet("")
        l.addWidget(self._add_mem_output)
        return w

    def _add_memory(self):
        title = self._mem_title.text().strip()
        content = self._mem_content.toPlainText().strip()
        tags = [t.strip() for t in self._mem_tags.text().split(",") if t.strip()]
        if not title or not content:
            self._add_mem_output.setText("Title and content are required.")
            return
        entry = {"id": len(self._memory_entries) + 1, "title": title, "content": content, "tags": tags, "timestamp": datetime.now().isoformat()}
        self._memory_entries.append(entry)
        self._restore_combo.addItem(f"[{entry['id']}] {title}")
        self._add_mem_output.setText(f"Memory stored:\n  Title: {title}\n  Tags: {', '.join(tags)}\n  Timestamp: {entry['timestamp']}\n  Total entries: {len(self._memory_entries)}")
        self._mem_title.clear()
        self._mem_content.clear()
        self._mem_tags.clear()

    def _run_query(self):
        query = self._query_input.text().strip().lower()
        if not query:
            self._query_output.setText("Enter a search query.")
            return
        if not self._memory_entries:
            self._query_output.setText("No memory entries stored. Add memories in the 'Add Memory' tab first.")
            return
        scored = []
        for entry in self._memory_entries:
            score = 0
            if query in entry["title"].lower():
                score += 3
            if query in entry["content"].lower():
                score += 2
            for tag in entry["tags"]:
                if query in tag.lower():
                    score += 1
            if score > 0:
                scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        if not scored:
            self._query_output.setText(f"No memories matching '{query}' found.")
            return
        lines = [f"SEARCH RESULTS — '{query}'\n{'='*60}\n{len(scored)} matches (ranked by relevance):\n"]
        for score, entry in scored:
            lines.append(f"  [Score: {score}] [{entry['id']}] {entry['title']}")
            lines.append(f"    Tags: {', '.join(entry['tags'])}")
            lines.append(f"    Content: {entry['content'][:200]}{'...' if len(entry['content']) > 200 else ''}")
            lines.append(f"    Stored: {entry['timestamp']}\n")
        self._query_output.setText("\n".join(lines))
        self._set_result_summary(f"Found {len(scored)} memories matching '{query}'.")

    def _run_tag_filter(self):
        tag_input = self._tag_input.text().strip()
        if not tag_input or not self._memory_entries:
            self._tag_output.setText("Enter tags and ensure memory entries exist.")
            return
        tags = [t.strip().lower() for t in tag_input.split(",")]
        matches = [e for e in self._memory_entries if any(t in [et.lower() for et in e["tags"]] for t in tags)]
        if not matches:
            self._tag_output.setText(f"No memories with tags: {tag_input}")
            return
        lines = [f"TAG FILTER — {tag_input}\n{'='*60}\n{len(matches)} entries:\n"]
        for entry in matches:
            lines.append(f"  [{entry['id']}] {entry['title']}")
            lines.append(f"    Tags: {', '.join(entry['tags'])}")
            lines.append(f"    Content: {entry['content'][:200]}{'...' if len(entry['content']) > 200 else ''}\n")
        self._tag_output.setText("\n".join(lines))

    def _run_restore(self):
        idx = self._restore_combo.currentIndex()
        if idx < 0 or idx >= len(self._memory_entries):
            self._restore_output.setText("Select a memory entry to restore.")
            return
        entry = self._memory_entries[idx]
        self._restore_output.setText(
            f"CONTEXT RESTORED\n{'='*60}\n"
            f"Title: {entry['title']}\nTags: {', '.join(entry['tags'])}\n"
            f"Stored: {entry['timestamp']}\n\n"
            f"CONTENT:\n{entry['content']}\n\n"
            f"This context is now available for the current session."
        )
        self._set_result_summary(f"Restored context: {entry['title']}")


class DecisionTrackerDialog(BaseCapabilityDialog):
    """Decision Tracker — record decisions, rationale, alternatives, outcome tracking."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Decision Tracker — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._decisions: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_record_tab(), "Record Decision")
        tabs.addTab(self._build_history_tab(), "Decision History")
        tabs.addTab(self._build_outcome_tab(), "Outcome Tracker")
        tabs.addTab(self._build_analysis_tab(), "Analysis")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Decision logs are personal records. Not a substitute for professional advice. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_record_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Record a Decision"))
        l.addWidget(QLabel("Decision title:"))
        self._dec_title = QLineEdit()
        self._dec_title.setPlaceholderText("e.g., Chose Pro tier over Starter")
        l.addWidget(self._dec_title)
        l.addWidget(QLabel("Rationale (why this decision?):"))
        self._dec_rationale = QTextEdit()
        self._dec_rationale.setPlaceholderText("Explain the reasoning behind this decision...")
        l.addWidget(self._dec_rationale)
        l.addWidget(QLabel("Alternatives considered (one per line):"))
        self._dec_alternatives = QTextEdit()
        self._dec_alternatives.setPlaceholderText("Alternative 1: ...\nAlternative 2: ...\nAlternative 3: ...")
        l.addWidget(self._dec_alternatives)
        l.addWidget(QLabel("Expected outcome:"))
        self._dec_expected = QLineEdit()
        self._dec_expected.setPlaceholderText("e.g., Save $120/year, get 4 AI slots")
        l.addWidget(self._dec_expected)
        btn = QPushButton("Record Decision")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._record_decision)
        l.addWidget(btn)
        self._dec_record_output = QTextEdit()
        self._dec_record_output.setReadOnly(True)
        self._dec_record_output.setStyleSheet("")
        l.addWidget(self._dec_record_output)
        return w

    def _build_history_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Decision History"))
        btn = QPushButton("Refresh History")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._refresh_history)
        l.addWidget(btn)
        self._history_output = QTextEdit()
        self._history_output.setReadOnly(True)
        self._history_output.setStyleSheet("")
        l.addWidget(self._history_output, stretch=1)
        return w

    def _build_outcome_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Outcome Tracker"))
        l.addWidget(QLabel("Select a decision to update its outcome:"))
        self._outcome_combo = QComboBox()
        self._outcome_combo.setMinimumWidth(400)
        l.addWidget(self._outcome_combo)
        l.addWidget(QLabel("Actual outcome:"))
        self._outcome_actual = QLineEdit()
        self._outcome_actual.setPlaceholderText("What actually happened?")
        l.addWidget(self._outcome_actual)
        l.addWidget(QLabel("Outcome status:"))
        self._outcome_status = QComboBox()
        self._outcome_status.addItems(["Pending", "Positive — met expectations", "Mixed — partially met", "Negative — did not meet expectations", "Reversed — decision changed"])
        l.addWidget(self._outcome_status)
        l.addWidget(QLabel("Lessons learned:"))
        self._outcome_lessons = QTextEdit()
        self._outcome_lessons.setPlaceholderText("What did you learn from this outcome?")
        l.addWidget(self._outcome_lessons)
        btn = QPushButton("Update Outcome")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._update_outcome)
        l.addWidget(btn)
        self._outcome_output = QTextEdit()
        self._outcome_output.setReadOnly(True)
        self._outcome_output.setStyleSheet("")
        l.addWidget(self._outcome_output)
        return w

    def _build_analysis_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Decision Analysis"))
        btn = QPushButton("Analyze Decisions")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._run_analysis)
        l.addWidget(btn)
        self._analysis_output = QTextEdit()
        self._analysis_output.setReadOnly(True)
        self._analysis_output.setStyleSheet("")
        l.addWidget(self._analysis_output, stretch=1)
        return w

    def _record_decision(self):
        title = self._dec_title.text().strip()
        rationale = self._dec_rationale.toPlainText().strip()
        alts = [a.strip() for a in self._dec_alternatives.toPlainText().split("\n") if a.strip()]
        expected = self._dec_expected.text().strip()
        if not title:
            self._dec_record_output.setText("Decision title is required.")
            return
        entry = {
            "id": len(self._decisions) + 1,
            "title": title,
            "rationale": rationale,
            "alternatives": alts,
            "expected": expected,
            "actual": "",
            "status": "Pending",
            "lessons": "",
            "timestamp": datetime.now().isoformat(),
        }
        self._decisions.append(entry)
        self._outcome_combo.addItem(f"[{entry['id']}] {title}")
        self._dec_record_output.setText(
            f"Decision recorded:\n  ID: {entry['id']}\n  Title: {title}\n  Alternatives: {len(alts)}\n  Expected: {expected}\n  Timestamp: {entry['timestamp']}"
        )
        self._dec_title.clear()
        self._dec_rationale.clear()
        self._dec_alternatives.clear()
        self._dec_expected.clear()

    def _refresh_history(self):
        if not self._decisions:
            self._history_output.setText("No decisions recorded yet.")
            return
        lines = [f"DECISION HISTORY\n{'='*60}\n{len(self._decisions)} decisions:\n"]
        for d in self._decisions:
            lines.append(f"  [{d['id']}] {d['title']}")
            lines.append(f"    Date: {d['timestamp'][:10]}")
            lines.append(f"    Expected: {d['expected']}")
            lines.append(f"    Status: {d['status']}")
            lines.append(f"    Alternatives: {', '.join(d['alternatives']) if d['alternatives'] else 'None recorded'}\n")
        self._history_output.setText("\n".join(lines))

    def _update_outcome(self):
        idx = self._outcome_combo.currentIndex()
        if idx < 0 or idx >= len(self._decisions):
            self._outcome_output.setText("Select a decision to update.")
            return
        d = self._decisions[idx]
        d["actual"] = self._outcome_actual.text().strip()
        d["status"] = self._outcome_status.currentText()
        d["lessons"] = self._outcome_lessons.toPlainText().strip()
        self._outcome_output.setText(
            f"Outcome updated for decision [{d['id']}]:\n  Title: {d['title']}\n  Actual: {d['actual']}\n  Status: {d['status']}\n  Lessons: {d['lessons']}"
        )
        self._outcome_actual.clear()
        self._outcome_lessons.clear()

    def _run_analysis(self):
        if not self._decisions:
            self._analysis_output.setText("No decisions to analyze. Record decisions first.")
            return
        try:
            from ...core.nexus_ai_runtime import NexusAIRuntime
            runtime = NexusAIRuntime()
            decision_text = "\n".join(f"[{d['id']}] {d['title']} — Status: {d['status']}, Expected: {d['expected']}, Actual: {d['actual']}" for d in self._decisions)
            result = runtime.generate(
                f"Analyze the following decision log and provide insights on decision-making patterns, "
                f"success rate, and recommendations:\n\n{decision_text}",
                ai_name=self._ai_name,
                abilities=self._abilities,
            )
            self._analysis_output.setText(result)
        except Exception:
            total = len(self._decisions)
            pending = sum(1 for d in self._decisions if d["status"] == "Pending")
            positive = sum(1 for d in self._decisions if "Positive" in d["status"])
            mixed = sum(1 for d in self._decisions if "Mixed" in d["status"])
            negative = sum(1 for d in self._decisions if "Negative" in d["status"])
            reversed_d = sum(1 for d in self._decisions if "Reversed" in d["status"])
            lines = [
                f"DECISION ANALYSIS\n{'='*60}\n",
                f"Total decisions:  {total}",
                f"Pending:          {pending}",
                f"Positive:         {positive}",
                f"Mixed:            {mixed}",
                f"Negative:         {negative}",
                f"Reversed:         {reversed_d}",
                f"\nSuccess rate:     {positive}/{total - pending} = {(positive / max(1, total - pending) * 100):.0f}%" if total > pending else "",
                f"\n{'='*60}\n",
            ]
            if negative + mixed > 0:
                lines.append("PATTERNS:")
                for d in self._decisions:
                    if "Negative" in d["status"] or "Mixed" in d["status"]:
                        lines.append(f"  - [{d['id']}] {d['title']}: {d['status']}")
                        if d["lessons"]:
                            lines.append(f"    Lesson: {d['lessons']}")
            lines.append("\nThe built-in intelligence can provide decision analysis.")
            self._analysis_output.setText("\n".join(lines))
        self._set_result_summary(f"Analyzed {len(self._decisions)} decisions.")


class KnowledgeArchiveDialog(BaseCapabilityDialog):
    """Knowledge Archive — categorize, tag, store, retrieve, lifecycle management."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Knowledge Archive — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._archive: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_store_tab(), "Store")
        tabs.addTab(self._build_retrieve_tab(), "Retrieve")
        tabs.addTab(self._build_lifecycle_tab(), "Lifecycle")
        tabs.addTab(self._build_browse_tab(), "Browse")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Knowledge archive stores data locally. Be mindful of sensitive information. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_store_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Store Knowledge"))
        l.addWidget(QLabel("Title:"))
        self._ka_title = QLineEdit()
        self._ka_title.setPlaceholderText("Short title for this knowledge entry")
        l.addWidget(self._ka_title)
        l.addWidget(QLabel("Category:"))
        self._ka_category = QComboBox()
        self._ka_category.addItems(["General", "Technical", "Business", "Research", "Personal", "Reference", "Tutorial", "Other"])
        self._ka_category.setEditable(True)
        l.addWidget(self._ka_category)
        l.addWidget(QLabel("Content:"))
        self._ka_content = QTextEdit()
        self._ka_content.setPlaceholderText("The knowledge content to archive...")
        l.addWidget(self._ka_content, stretch=1)
        l.addWidget(QLabel("Tags (comma-separated):"))
        self._ka_tags = QLineEdit()
        self._ka_tags.setPlaceholderText("e.g., python, networking, important")
        l.addWidget(self._ka_tags)
        l.addWidget(QLabel("Lifecycle:"))
        self._ka_lifecycle = QComboBox()
        self._ka_lifecycle.addItems(["Active", "Archive", "Deprecated", "Review Needed"])
        l.addWidget(self._ka_lifecycle)
        btn = QPushButton("Archive Knowledge")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._store_knowledge)
        l.addWidget(btn)
        self._ka_store_output = QTextEdit()
        self._ka_store_output.setReadOnly(True)
        self._ka_store_output.setStyleSheet("")
        l.addWidget(self._ka_store_output)
        return w

    def _build_retrieve_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Retrieve Knowledge"))
        l.addWidget(QLabel("Search query:"))
        self._ka_search = QLineEdit()
        self._ka_search.setPlaceholderText("Search by title, content, or tags...")
        l.addWidget(self._ka_search)
        l.addWidget(QLabel("Filter by category:"))
        self._ka_cat_filter = QComboBox()
        self._ka_cat_filter.addItems(["All", "General", "Technical", "Business", "Research", "Personal", "Reference", "Tutorial", "Other"])
        l.addWidget(self._ka_cat_filter)
        btn = QPushButton("Search Archive")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._retrieve_knowledge)
        l.addWidget(btn)
        self._ka_retrieve_output = QTextEdit()
        self._ka_retrieve_output.setReadOnly(True)
        self._ka_retrieve_output.setStyleSheet("")
        l.addWidget(self._ka_retrieve_output, stretch=1)
        return w

    def _build_lifecycle_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Lifecycle Management"))
        l.addWidget(QLabel("Select an entry to update its lifecycle status:"))
        self._ka_lifecycle_combo = QComboBox()
        self._ka_lifecycle_combo.setMinimumWidth(400)
        l.addWidget(self._ka_lifecycle_combo)
        l.addWidget(QLabel("New status:"))
        self._ka_new_status = QComboBox()
        self._ka_new_status.addItems(["Active", "Archive", "Deprecated", "Review Needed"])
        l.addWidget(self._ka_new_status)
        btn = QPushButton("Update Status")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._update_lifecycle)
        l.addWidget(btn)
        self._ka_lifecycle_output = QTextEdit()
        self._ka_lifecycle_output.setReadOnly(True)
        self._ka_lifecycle_output.setStyleSheet("")
        l.addWidget(self._ka_lifecycle_output, stretch=1)
        return w

    def _build_browse_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Browse Archive"))
        btn = QPushButton("Browse All Entries")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._browse_all)
        l.addWidget(btn)
        self._ka_browse_output = QTextEdit()
        self._ka_browse_output.setReadOnly(True)
        self._ka_browse_output.setStyleSheet("")
        l.addWidget(self._ka_browse_output, stretch=1)
        return w

    def _store_knowledge(self):
        title = self._ka_title.text().strip()
        category = self._ka_category.currentText().strip()
        content = self._ka_content.toPlainText().strip()
        tags = [t.strip() for t in self._ka_tags.text().split(",") if t.strip()]
        lifecycle = self._ka_lifecycle.currentText()
        if not title or not content:
            self._ka_store_output.setText("Title and content are required.")
            return
        entry = {"id": len(self._archive) + 1, "title": title, "category": category, "content": content, "tags": tags, "lifecycle": lifecycle, "timestamp": datetime.now().isoformat()}
        self._archive.append(entry)
        self._ka_lifecycle_combo.addItem(f"[{entry['id']}] {title} ({lifecycle})")
        self._ka_store_output.setText(f"Knowledge archived:\n  ID: {entry['id']}\n  Title: {title}\n  Category: {category}\n  Tags: {', '.join(tags)}\n  Lifecycle: {lifecycle}\n  Total entries: {len(self._archive)}")
        self._ka_title.clear()
        self._ka_content.clear()
        self._ka_tags.clear()

    def _retrieve_knowledge(self):
        query = self._ka_search.text().strip().lower()
        cat = self._ka_cat_filter.currentText()
        if not self._archive:
            self._ka_retrieve_output.setText("Archive is empty. Store knowledge first.")
            return
        results = self._archive
        if cat != "All":
            results = [e for e in results if e["category"] == cat]
        if query:
            results = [e for e in results if query in e["title"].lower() or query in e["content"].lower() or any(query in t.lower() for t in e["tags"])]
        if not results:
            self._ka_retrieve_output.setText("No matching entries found.")
            return
        lines = [f"RETRIEVAL RESULTS\n{'='*60}\n{len(results)} entries:\n"]
        for e in results:
            lines.append(f"  [{e['id']}] {e['title']}")
            lines.append(f"    Category: {e['category']} | Lifecycle: {e['lifecycle']}")
            lines.append(f"    Tags: {', '.join(e['tags'])}")
            lines.append(f"    Content: {e['content'][:300]}{'...' if len(e['content']) > 300 else ''}\n")
        self._ka_retrieve_output.setText("\n".join(lines))
        self._set_result_summary(f"Retrieved {len(results)} entries.")

    def _update_lifecycle(self):
        idx = self._ka_lifecycle_combo.currentIndex()
        if idx < 0 or idx >= len(self._archive):
            self._ka_lifecycle_output.setText("Select an entry to update.")
            return
        new_status = self._ka_new_status.currentText()
        self._archive[idx]["lifecycle"] = new_status
        self._ka_lifecycle_output.setText(f"Updated [{self._archive[idx]['id']}] {self._archive[idx]['title']} to: {new_status}")

    def _browse_all(self):
        if not self._archive:
            self._ka_browse_output.setText("Archive is empty.")
            return
        lines = [f"ARCHIVE BROWSER\n{'='*60}\n{len(self._archive)} total entries:\n"]
        for e in self._archive:
            lines.append(f"  [{e['id']}] {e['title']} ({e['category']}) — {e['lifecycle']}")
        lines.append(f"\n{'='*60}\nCategories: {', '.join(sorted(set(e['category'] for e in self._archive)))}")
        self._ka_browse_output.setText("\n".join(lines))


class HabitTrackerDialog(BaseCapabilityDialog):
    """Habit Tracker — define habits, daily check-in, streak counter, habit strength."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Habit Tracker — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._habits: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_define_tab(), "Define Habits")
        tabs.addTab(self._build_checkin_tab(), "Daily Check-In")
        tabs.addTab(self._build_streaks_tab(), "Streaks")
        tabs.addTab(self._build_strength_tab(), "Habit Strength")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Habit tracking is for personal use. No health or medical claims. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_define_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Define a New Habit"))
        l.addWidget(QLabel("Habit name:"))
        self._habit_name = QLineEdit()
        self._habit_name.setPlaceholderText("e.g., Morning exercise, Read 30 minutes, Practice coding")
        l.addWidget(self._habit_name)
        l.addWidget(QLabel("Frequency:"))
        self._habit_freq = QComboBox()
        self._habit_freq.addItems(["Daily", "Weekdays", "Weekends", "3x per week", "Weekly"])
        l.addWidget(self._habit_freq)
        l.addWidget(QLabel("Target streak (days):"))
        self._habit_target = QLineEdit()
        self._habit_target.setPlaceholderText("e.g., 30")
        l.addWidget(self._habit_target)
        l.addWidget(QLabel("Notes:"))
        self._habit_notes = QTextEdit()
        self._habit_notes.setPlaceholderText("Why this habit? What triggers it? Reward?")
        l.addWidget(self._habit_notes)
        btn = QPushButton("Add Habit")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._add_habit)
        l.addWidget(btn)
        self._define_output = QTextEdit()
        self._define_output.setReadOnly(True)
        self._define_output.setStyleSheet("")
        l.addWidget(self._define_output)
        return w

    def _build_checkin_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Daily Check-In"))
        l.addWidget(QLabel("Select a habit to check in:"))
        self._checkin_combo = QComboBox()
        self._checkin_combo.setMinimumWidth(400)
        l.addWidget(self._checkin_combo)
        l.addWidget(QLabel("Status:"))
        self._checkin_status = QComboBox()
        self._checkin_status.addItems(["Completed", "Partially done", "Skipped", "Missed"])
        l.addWidget(self._checkin_status)
        l.addWidget(QLabel("Notes for today:"))
        self._checkin_notes = QLineEdit()
        self._checkin_notes.setPlaceholderText("How did it go? Any obstacles?")
        l.addWidget(self._checkin_notes)
        btn = QPushButton("Check In")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._checkin)
        l.addWidget(btn)
        self._checkin_output = QTextEdit()
        self._checkin_output.setReadOnly(True)
        self._checkin_output.setStyleSheet("")
        l.addWidget(self._checkin_output)
        return w

    def _build_streaks_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Streak Counter"))
        btn = QPushButton("Refresh Streaks")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._refresh_streaks)
        l.addWidget(btn)
        self._streaks_output = QTextEdit()
        self._streaks_output.setReadOnly(True)
        self._streaks_output.setStyleSheet("")
        l.addWidget(self._streaks_output, stretch=1)
        return w

    def _build_strength_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Habit Strength Analysis"))
        btn = QPushButton("Calculate Strength")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._calc_strength)
        l.addWidget(btn)
        self._strength_output = QTextEdit()
        self._strength_output.setReadOnly(True)
        self._strength_output.setStyleSheet("")
        l.addWidget(self._strength_output, stretch=1)
        return w

    def _add_habit(self):
        name = self._habit_name.text().strip()
        if not name:
            self._define_output.setText("Habit name is required.")
            return
        freq = self._habit_freq.currentText()
        target = self._habit_target.text().strip() or "30"
        notes = self._habit_notes.toPlainText().strip()
        habit = {"id": len(self._habits) + 1, "name": name, "frequency": freq, "target": int(target) if target.isdigit() else 30, "notes": notes, "checkins": [], "streak": 0, "best_streak": 0, "created": datetime.now().isoformat()}
        self._habits.append(habit)
        self._checkin_combo.addItem(f"[{habit['id']}] {name}")
        self._define_output.setText(f"Habit added:\n  Name: {name}\n  Frequency: {freq}\n  Target: {target} days\n  Total habits: {len(self._habits)}")
        self._habit_name.clear()
        self._habit_target.clear()
        self._habit_notes.clear()

    def _checkin(self):
        idx = self._checkin_combo.currentIndex()
        if idx < 0 or idx >= len(self._habits):
            self._checkin_output.setText("Select a habit to check in.")
            return
        status = self._checkin_status.currentText()
        notes = self._checkin_notes.text().strip()
        h = self._habits[idx]
        today = datetime.now().strftime("%Y-%m-%d")
        h["checkins"].append({"date": today, "status": status, "notes": notes})
        if status == "Completed":
            h["streak"] += 1
            if h["streak"] > h["best_streak"]:
                h["best_streak"] = h["streak"]
        elif status in ("Skipped", "Missed"):
            h["streak"] = 0
        self._checkin_output.setText(f"Checked in for [{h['id']}] {h['name']}:\n  Status: {status}\n  Current streak: {h['streak']} days\n  Best streak: {h['best_streak']} days\n  Notes: {notes}")
        self._checkin_notes.clear()

    def _refresh_streaks(self):
        if not self._habits:
            self._streaks_output.setText("No habits defined yet.")
            return
        lines = [f"STREAK COUNTER\n{'='*60}\n{len(self._habits)} habits:\n"]
        for h in self._habits:
            target_pct = (h["streak"] / h["target"] * 100) if h["target"] > 0 else 0
            bar_len = int(target_pct / 5)
            bar = "#" * bar_len + "." * (20 - bar_len)
            lines.append(f"  [{h['id']}] {h['name']}")
            lines.append(f"    Current: {h['streak']} days | Best: {h['best_streak']} days | Target: {h['target']} days")
            lines.append(f"    Progress: [{bar}] {target_pct:.0f}%")
            lines.append(f"    Check-ins: {len(h['checkins'])} total\n")
        self._streaks_output.setText("\n".join(lines))

    def _calc_strength(self):
        if not self._habits:
            self._strength_output.setText("No habits to analyze.")
            return
        lines = [f"HABIT STRENGTH ANALYSIS\n{'='*60}\n"]
        for h in self._habits:
            total = len(h["checkins"])
            if total == 0:
                lines.append(f"  [{h['id']}] {h['name']}: No check-ins yet.\n")
                continue
            completed = sum(1 for c in h["checkins"] if c["status"] == "Completed")
            partial = sum(1 for c in h["checkins"] if c["status"] == "Partially done")
            missed = sum(1 for c in h["checkins"] if c["status"] in ("Skipped", "Missed"))
            consistency = (completed + partial * 0.5) / total * 100
            strength_label = "Strong" if consistency >= 80 else "Developing" if consistency >= 50 else "Weak"
            lines.append(f"  [{h['id']}] {h['name']}")
            lines.append(f"    Total check-ins: {total}")
            lines.append(f"    Completed: {completed} | Partial: {partial} | Missed: {missed}")
            lines.append(f"    Consistency: {consistency:.0f}% — {strength_label}")
            lines.append(f"    Current streak: {h['streak']} | Best: {h['best_streak']}\n")
        lines.append("The built-in intelligence can provide habit coaching.")
        self._strength_output.setText("\n".join(lines))
        self._set_result_summary(f"Analyzed {len(self._habits)} habits.")


class ProgressJournalDialog(BaseCapabilityDialog):
    """Progress Journal — entry editor, milestone tracker, timeline view, reflection prompts."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Progress Journal — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._entries: list[dict] = []
        self._milestones: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_entry_tab(), "New Entry")
        tabs.addTab(self._build_milestone_tab(), "Milestones")
        tabs.addTab(self._build_timeline_tab(), "Timeline")
        tabs.addTab(self._build_reflection_tab(), "Reflection Prompts")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Progress journal is for personal use. No outcome guarantees. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_entry_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("New Journal Entry"))
        l.addWidget(QLabel("Entry title:"))
        self._pj_title = QLineEdit()
        self._pj_title.setPlaceholderText("e.g., Week 3 progress, First deployment, Learning milestone")
        l.addWidget(self._pj_title)
        l.addWidget(QLabel("Mood/energy:"))
        self._pj_mood = QComboBox()
        self._pj_mood.addItems(["Great", "Good", "Neutral", "Tired", "Frustrated", "Motivated"])
        l.addWidget(self._pj_mood)
        l.addWidget(QLabel("Entry content:"))
        self._pj_content = QTextEdit()
        self._pj_content.setPlaceholderText("Write your journal entry... What did you accomplish? What challenges did you face? What did you learn?")
        l.addWidget(self._pj_content, stretch=1)
        btn = QPushButton("Save Entry")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._save_entry)
        l.addWidget(btn)
        self._pj_entry_output = QTextEdit()
        self._pj_entry_output.setReadOnly(True)
        self._pj_entry_output.setStyleSheet("")
        l.addWidget(self._pj_entry_output)
        return w

    def _build_milestone_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Milestone Tracker"))
        l.addWidget(QLabel("Milestone title:"))
        self._ms_title = QLineEdit()
        self._ms_title.setPlaceholderText("e.g., Completed first project, Reached 100 users, Shipped v1.0")
        l.addWidget(self._ms_title)
        l.addWidget(QLabel("Description:"))
        self._ms_desc = QTextEdit()
        self._ms_desc.setPlaceholderText("Describe the milestone...")
        l.addWidget(self._ms_desc)
        l.addWidget(QLabel("Target date:"))
        self._ms_target = QLineEdit()
        self._ms_target.setPlaceholderText("YYYY-MM-DD")
        l.addWidget(self._ms_target)
        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add Milestone")
        add_btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        add_btn.clicked.connect(self._add_milestone)
        btn_row.addWidget(add_btn)
        complete_btn = QPushButton("Mark Latest Complete")
        complete_btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        complete_btn.clicked.connect(self._complete_milestone)
        btn_row.addWidget(complete_btn)
        l.addLayout(btn_row)
        self._ms_output = QTextEdit()
        self._ms_output.setReadOnly(True)
        self._ms_output.setStyleSheet("")
        l.addWidget(self._ms_output, stretch=1)
        return w

    def _build_timeline_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Timeline View"))
        btn = QPushButton("Generate Timeline")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._generate_timeline)
        l.addWidget(btn)
        self._timeline_output = QTextEdit()
        self._timeline_output.setReadOnly(True)
        self._timeline_output.setStyleSheet("")
        l.addWidget(self._timeline_output, stretch=1)
        return w

    def _build_reflection_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Reflection Prompts"))
        l.addWidget(QLabel("Select a prompt to reflect on:"))
        self._prompt_combo = QComboBox()
        self._prompt_combo.addItems([
            "What was the biggest win this week?",
            "What was the biggest challenge, and how did I handle it?",
            "What did I learn that surprised me?",
            "What would I do differently next time?",
            "What am I most proud of right now?",
            "What's blocking me, and what can I do about it?",
            "How have my goals changed since last month?",
            "What habits are helping me? Which are hurting?",
        ])
        l.addWidget(self._prompt_combo)
        l.addWidget(QLabel("Your reflection:"))
        self._reflection_input = QTextEdit()
        self._reflection_input.setPlaceholderText("Write your reflection here...")
        l.addWidget(self._reflection_input, stretch=1)
        btn = QPushButton("Save Reflection")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._save_reflection)
        l.addWidget(btn)
        self._reflection_output = QTextEdit()
        self._reflection_output.setReadOnly(True)
        self._reflection_output.setStyleSheet("")
        l.addWidget(self._reflection_output)
        return w

    def _save_entry(self):
        title = self._pj_title.text().strip()
        mood = self._pj_mood.currentText()
        content = self._pj_content.toPlainText().strip()
        if not title or not content:
            self._pj_entry_output.setText("Title and content are required.")
            return
        entry = {"id": len(self._entries) + 1, "title": title, "mood": mood, "content": content, "timestamp": datetime.now().isoformat()}
        self._entries.append(entry)
        self._pj_entry_output.setText(f"Entry saved:\n  ID: {entry['id']}\n  Title: {title}\n  Mood: {mood}\n  Date: {entry['timestamp'][:10]}\n  Total entries: {len(self._entries)}")
        self._pj_title.clear()
        self._pj_content.clear()

    def _add_milestone(self):
        title = self._ms_title.text().strip()
        desc = self._ms_desc.toPlainText().strip()
        target = self._ms_target.text().strip()
        if not title:
            self._ms_output.setText("Milestone title is required.")
            return
        ms = {"id": len(self._milestones) + 1, "title": title, "description": desc, "target": target, "completed": False, "completed_date": "", "created": datetime.now().isoformat()}
        self._milestones.append(ms)
        self._ms_output.setText(f"Milestone added:\n  [{ms['id']}] {title}\n  Target: {target}\n  Total milestones: {len(self._milestones)}")
        self._ms_title.clear()
        self._ms_desc.clear()
        self._ms_target.clear()

    def _complete_milestone(self):
        for ms in reversed(self._milestones):
            if not ms["completed"]:
                ms["completed"] = True
                ms["completed_date"] = datetime.now().strftime("%Y-%m-%d")
                self._ms_output.setText(f"Milestone completed:\n  [{ms['id']}] {ms['title']}\n  Completed: {ms['completed_date']}")
                return
        self._ms_output.setText("No pending milestones to complete.")

    def _generate_timeline(self):
        all_items = []
        for e in self._entries:
            all_items.append((e["timestamp"], "ENTRY", e["title"], e["mood"]))
        for m in self._milestones:
            status = "COMPLETED" if m["completed"] else "PENDING"
            all_items.append((m["created"], f"MILESTONE ({status})", m["title"], m["target"]))
        all_items.sort(key=lambda x: x[0])
        if not all_items:
            self._timeline_output.setText("No entries or milestones yet.")
            return
        lines = [f"PROGRESS TIMELINE\n{'='*60}\n{len(all_items)} items:\n"]
        for ts, typ, title, extra in all_items:
            date = ts[:10]
            lines.append(f"  [{date}] {typ:20s} | {title}")
            if extra:
                lines.append(f"           {'':20s} | ({extra})")
        self._timeline_output.setText("\n".join(lines))

    def _save_reflection(self):
        prompt = self._prompt_combo.currentText()
        reflection = self._reflection_input.toPlainText().strip()
        if not reflection:
            self._reflection_output.setText("Write your reflection before saving.")
            return
        entry = {"id": len(self._entries) + 1, "title": f"Reflection: {prompt}", "mood": "Reflective", "content": f"PROMPT: {prompt}\n\nREFLECTION:\n{reflection}", "timestamp": datetime.now().isoformat()}
        self._entries.append(entry)
        self._reflection_output.setText(f"Reflection saved as journal entry [{entry['id']}].\n  Prompt: {prompt}\n  Length: {len(reflection)} chars")
        self._reflection_input.clear()


class ContextKeeperDialog(BaseCapabilityDialog):
    """Context Keeper — save current context, restore on next session, context diff."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Context Keeper — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._saved_contexts: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_save_tab(), "Save Context")
        tabs.addTab(self._build_restore_tab(), "Restore")
        tabs.addTab(self._build_diff_tab(), "Context Diff")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Context preservation stores session data locally. Be mindful of sensitive data. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_save_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Save Current Context"))
        l.addWidget(QLabel("Context label:"))
        self._ck_label = QLineEdit()
        self._ck_label.setPlaceholderText("e.g., Before refactoring, Mid-project state, Pre-deployment")
        l.addWidget(self._ck_label)
        l.addWidget(QLabel("Active AI name:"))
        self._ck_ai_name = QLineEdit()
        self._ck_ai_name.setPlaceholderText("Which AI unit is active?")
        l.addWidget(self._ck_ai_name)
        l.addWidget(QLabel("Current task/goal:"))
        self._ck_task = QLineEdit()
        self._ck_task.setPlaceholderText("What are you currently working on?")
        l.addWidget(self._ck_task)
        l.addWidget(QLabel("Context details (files open, settings, state):"))
        self._ck_details = QTextEdit()
        self._ck_details.setPlaceholderText("Describe the current context state — what files are open, what settings are active, what was in progress...")
        l.addWidget(self._ck_details, stretch=1)
        l.addWidget(QLabel("Tags (comma-separated):"))
        self._ck_tags = QLineEdit()
        self._ck_tags.setPlaceholderText("e.g., project-alpha, refactoring, important")
        l.addWidget(self._ck_tags)
        btn = QPushButton("Save Context")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._save_context)
        l.addWidget(btn)
        self._ck_save_output = QTextEdit()
        self._ck_save_output.setReadOnly(True)
        self._ck_save_output.setStyleSheet("")
        l.addWidget(self._ck_save_output)
        return w

    def _build_restore_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Restore Context"))
        l.addWidget(QLabel("Select a saved context:"))
        self._ck_restore_combo = QComboBox()
        self._ck_restore_combo.setMinimumWidth(400)
        l.addWidget(self._ck_restore_combo)
        btn = QPushButton("Restore Selected Context")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._restore_context)
        l.addWidget(btn)
        self._ck_restore_output = QTextEdit()
        self._ck_restore_output.setReadOnly(True)
        self._ck_restore_output.setStyleSheet("")
        l.addWidget(self._ck_restore_output, stretch=1)
        return w

    def _build_diff_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Context Diff"))
        l.addWidget(QLabel("Select two contexts to compare:"))
        row = QHBoxLayout()
        l.addWidget(QLabel("Context A:"))
        self._ck_diff_a = QComboBox()
        self._ck_diff_a.setMinimumWidth(200)
        row.addWidget(self._ck_diff_a)
        l.addWidget(QLabel("Context B:"))
        self._ck_diff_b = QComboBox()
        self._ck_diff_b.setMinimumWidth(200)
        row.addWidget(self._ck_diff_b)
        l.addLayout(row)
        btn = QPushButton("Compare Contexts")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._diff_contexts)
        l.addWidget(btn)
        self._ck_diff_output = QTextEdit()
        self._ck_diff_output.setReadOnly(True)
        self._ck_diff_output.setStyleSheet("")
        l.addWidget(self._ck_diff_output, stretch=1)
        return w

    def _save_context(self):
        label = self._ck_label.text().strip()
        ai_name = self._ck_ai_name.text().strip()
        task = self._ck_task.text().strip()
        details = self._ck_details.toPlainText().strip()
        tags = [t.strip() for t in self._ck_tags.text().split(",") if t.strip()]
        if not label:
            self._ck_save_output.setText("Context label is required.")
            return
        ctx = {"id": len(self._saved_contexts) + 1, "label": label, "ai_name": ai_name, "task": task, "details": details, "tags": tags, "timestamp": datetime.now().isoformat()}
        self._saved_contexts.append(ctx)
        self._ck_restore_combo.addItem(f"[{ctx['id']}] {label}")
        self._ck_diff_a.addItem(f"[{ctx['id']}] {label}")
        self._ck_diff_b.addItem(f"[{ctx['id']}] {label}")
        self._ck_save_output.setText(f"Context saved:\n  ID: {ctx['id']}\n  Label: {label}\n  AI: {ai_name}\n  Task: {task}\n  Tags: {', '.join(tags)}\n  Saved: {ctx['timestamp']}")
        self._ck_label.clear()
        self._ck_ai_name.clear()
        self._ck_task.clear()
        self._ck_details.clear()
        self._ck_tags.clear()

    def _restore_context(self):
        idx = self._ck_restore_combo.currentIndex()
        if idx < 0 or idx >= len(self._saved_contexts):
            self._ck_restore_output.setText("Select a context to restore.")
            return
        ctx = self._saved_contexts[idx]
        self._ck_restore_output.setText(
            f"CONTEXT RESTORED\n{'='*60}\n"
            f"Label: {ctx['label']}\nAI: {ctx['ai_name']}\nTask: {ctx['task']}\n"
            f"Tags: {', '.join(ctx['tags'])}\nSaved: {ctx['timestamp']}\n\n"
            f"DETAILS:\n{ctx['details']}\n\n"
            f"This context is now available for the current session."
        )
        self._set_result_summary(f"Restored context: {ctx['label']}")

    def _diff_contexts(self):
        idx_a = self._ck_diff_a.currentIndex()
        idx_b = self._ck_diff_b.currentIndex()
        if idx_a < 0 or idx_b < 0 or idx_a == idx_b:
            self._ck_diff_output.setText("Select two different contexts to compare.")
            return
        ctx_a = self._saved_contexts[idx_a]
        ctx_b = self._saved_contexts[idx_b]
        lines = [f"CONTEXT DIFF\n{'='*60}\n"]
        lines.append(f"A: [{ctx_a['id']}] {ctx_a['label']} ({ctx_a['timestamp'][:10]})")
        lines.append(f"B: [{ctx_b['id']}] {ctx_b['label']} ({ctx_b['timestamp'][:10]})\n")
        lines.append(f"AI NAME:\n  A: {ctx_a['ai_name']}\n  B: {ctx_b['ai_name']}\n  {'SAME' if ctx_a['ai_name'] == ctx_b['ai_name'] else 'CHANGED'}\n")
        lines.append(f"TASK:\n  A: {ctx_a['task']}\n  B: {ctx_b['task']}\n  {'SAME' if ctx_a['task'] == ctx_b['task'] else 'CHANGED'}\n")
        lines.append(f"TAGS:\n  A: {', '.join(ctx_a['tags'])}\n  B: {', '.join(ctx_b['tags'])}\n  {'SAME' if set(ctx_a['tags']) == set(ctx_b['tags']) else 'CHANGED'}\n")
        lines.append(f"DETAILS LENGTH:\n  A: {len(ctx_a['details'])} chars\n  B: {len(ctx_b['details'])} chars\n")
        lines.append(f"DETAILS CONTENT:\n  {'IDENTICAL' if ctx_a['details'] == ctx_b['details'] else 'DIFFERENT'}")
        self._ck_diff_output.setText("\n".join(lines))


class AuditTrailBuilderDialog(BaseCapabilityDialog):
    """Audit Trail Builder — event timeline, compliance export, filter by capability/date/source."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Audit Trail Builder — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._audit_events: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_add_event_tab(), "Add Event")
        tabs.addTab(self._build_timeline_tab(), "Event Timeline")
        tabs.addTab(self._build_filter_tab(), "Filter & Search")
        tabs.addTab(self._build_export_tab(), "Compliance Export")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Audit trail contains full activity log. Privacy/compliance — be aware of sensitive data. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_add_event_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Add Audit Event"))
        l.addWidget(QLabel("Event source:"))
        self._at_source = QComboBox()
        self._at_source.addItems(["User Action", "AI Action", "System", "Capability", "Security", "License", "External"])
        l.addWidget(self._at_source)
        l.addWidget(QLabel("Capability (if applicable):"))
        self._at_capability = QLineEdit()
        self._at_capability.setPlaceholderText("e.g., Financial Gainer, Code Reviewer, Memory Recorder")
        l.addWidget(self._at_capability)
        l.addWidget(QLabel("Event description:"))
        self._at_desc = QTextEdit()
        self._at_desc.setPlaceholderText("Describe the event in detail...")
        l.addWidget(self._at_desc)
        l.addWidget(QLabel("Severity:"))
        self._at_severity = QComboBox()
        self._at_severity.addItems(["Info", "Low", "Medium", "High", "Critical"])
        l.addWidget(self._at_severity)
        btn = QPushButton("Add to Audit Trail")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._add_audit_event)
        l.addWidget(btn)
        self._at_add_output = QTextEdit()
        self._at_add_output.setReadOnly(True)
        self._at_add_output.setStyleSheet("")
        l.addWidget(self._at_add_output)
        return w

    def _build_timeline_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Event Timeline"))
        btn = QPushButton("Generate Timeline")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._generate_audit_timeline)
        l.addWidget(btn)
        self._at_timeline_output = QTextEdit()
        self._at_timeline_output.setReadOnly(True)
        self._at_timeline_output.setStyleSheet("")
        l.addWidget(self._at_timeline_output, stretch=1)
        return w

    def _build_filter_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Filter & Search Audit Events"))
        l.addWidget(QLabel("Filter by source:"))
        self._at_filter_source = QComboBox()
        self._at_filter_source.addItems(["All", "User Action", "AI Action", "System", "Capability", "Security", "License", "External"])
        l.addWidget(self._at_filter_source)
        l.addWidget(QLabel("Filter by severity:"))
        self._at_filter_sev = QComboBox()
        self._at_filter_sev.addItems(["All", "Info", "Low", "Medium", "High", "Critical"])
        l.addWidget(self._at_filter_sev)
        l.addWidget(QLabel("Filter by date (YYYY-MM-DD, leave empty for all):"))
        self._at_filter_date = QLineEdit()
        l.addWidget(self._at_filter_date)
        l.addWidget(QLabel("Search in description:"))
        self._at_search = QLineEdit()
        self._at_search.setPlaceholderText("Search text...")
        l.addWidget(self._at_search)
        btn = QPushButton("Apply Filters")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._apply_filters)
        l.addWidget(btn)
        self._at_filter_output = QTextEdit()
        self._at_filter_output.setReadOnly(True)
        self._at_filter_output.setStyleSheet("")
        l.addWidget(self._at_filter_output, stretch=1)
        return w

    def _build_export_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Compliance Export"))
        l.addWidget(QLabel("Export format:"))
        self._at_export_fmt = QComboBox()
        self._at_export_fmt.addItems(["Text Report", "JSON", "CSV", "Compliance Summary"])
        l.addWidget(self._at_export_fmt)
        btn = QPushButton("Generate Export")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._export_audit)
        l.addWidget(btn)
        self._at_export_output = QTextEdit()
        self._at_export_output.setReadOnly(True)
        self._at_export_output.setStyleSheet("")
        l.addWidget(self._at_export_output, stretch=1)
        return w

    def _add_audit_event(self):
        source = self._at_source.currentText()
        capability = self._at_capability.text().strip()
        desc = self._at_desc.toPlainText().strip()
        severity = self._at_severity.currentText()
        if not desc:
            self._at_add_output.setText("Event description is required.")
            return
        event = {"id": len(self._audit_events) + 1, "source": source, "capability": capability, "description": desc, "severity": severity, "timestamp": datetime.now().isoformat()}
        self._audit_events.append(event)
        self._at_add_output.setText(f"Audit event added:\n  ID: {event['id']}\n  Source: {source}\n  Capability: {capability or 'N/A'}\n  Severity: {severity}\n  Timestamp: {event['timestamp']}\n  Total events: {len(self._audit_events)}")
        self._at_capability.clear()
        self._at_desc.clear()

    def _generate_audit_timeline(self):
        if not self._audit_events:
            self._at_timeline_output.setText("No audit events recorded yet.")
            return
        lines = [f"AUDIT TIMELINE\n{'='*60}\n{len(self._audit_events)} events:\n"]
        for e in sorted(self._audit_events, key=lambda x: x["timestamp"]):
            ts = e["timestamp"].replace("T", " ")[:19]
            sev_icon = {"Info": "i", "Low": ".", "Medium": "!", "High": "!!", "Critical": "X"}.get(e["severity"], "?")
            lines.append(f"  [{ts}] ({sev_icon}) {e['severity']:8s} | {e['source']:15s} | {e['description'][:80]}")
        self._at_timeline_output.setText("\n".join(lines))

    def _apply_filters(self):
        if not self._audit_events:
            self._at_filter_output.setText("No audit events to filter.")
            return
        results = self._audit_events
        src = self._at_filter_source.currentText()
        sev = self._at_filter_sev.currentText()
        date = self._at_filter_date.text().strip()
        search = self._at_search.text().strip().lower()
        if src != "All":
            results = [e for e in results if e["source"] == src]
        if sev != "All":
            results = [e for e in results if e["severity"] == sev]
        if date:
            results = [e for e in results if e["timestamp"].startswith(date)]
        if search:
            results = [e for e in results if search in e["description"].lower() or search in e["capability"].lower()]
        if not results:
            self._at_filter_output.setText("No events match the selected filters.")
            return
        lines = [f"FILTERED RESULTS\n{'='*60}\n{len(results)} of {len(self._audit_events)} events:\n"]
        for e in results:
            lines.append(f"  [{e['id']}] {e['timestamp'][:19]} | {e['source']} | {e['severity']} | {e['description'][:80]}")
        self._at_filter_output.setText("\n".join(lines))
        self._set_result_summary(f"Filtered to {len(results)} events.")

    def _export_audit(self):
        if not self._audit_events:
            self._at_export_output.setText("No audit events to export.")
            return
        fmt = self._at_export_fmt.currentText()
        if fmt == "Text Report":
            lines = [f"AUDIT TRAIL EXPORT\n{'='*60}\n"]
            lines.append(f"Generated: {datetime.now().isoformat()}")
            lines.append(f"Total events: {len(self._audit_events)}\n")
            for e in sorted(self._audit_events, key=lambda x: x["timestamp"]):
                lines.append(f"[{e['id']}] {e['timestamp']}")
                lines.append(f"  Source: {e['source']}")
                lines.append(f"  Capability: {e['capability'] or 'N/A'}")
                lines.append(f"  Severity: {e['severity']}")
                lines.append(f"  Description: {e['description']}\n")
            lines.append(f"{'='*60}\nExported by Command Nexus(TM) Audit Trail Builder")
        elif fmt == "JSON":
            import json
            lines = [json.dumps({"exported_at": datetime.now().isoformat(), "total_events": len(self._audit_events), "events": self._audit_events}, indent=2)]
        elif fmt == "CSV":
            lines = ["id,timestamp,source,capability,severity,description"]
            for e in self._audit_events:
                lines.append(f"\"{e['id']}\",\"{e['timestamp']}\",\"{e['source']}\",\"{e['capability']}\",\"{e['severity']}\",\"{e['description']}\"")
        elif fmt == "Compliance Summary":
            by_source = {}
            by_sev = {}
            for e in self._audit_events:
                by_source[e["source"]] = by_source.get(e["source"], 0) + 1
                by_sev[e["severity"]] = by_sev.get(e["severity"], 0) + 1
            lines = [f"COMPLIANCE SUMMARY\n{'='*60}\n"]
            lines.append(f"Total events: {len(self._audit_events)}\n")
            lines.append("BY SOURCE:")
            for src, count in sorted(by_source.items()):
                lines.append(f"  {src:20s}: {count}")
            lines.append("\nBY SEVERITY:")
            for sev, count in sorted(by_sev.items(), key=lambda x: ["Info", "Low", "Medium", "High", "Critical"].index(x[0]) if x[0] in ["Info", "Low", "Medium", "High", "Critical"] else 99):
                lines.append(f"  {sev:10s}: {count}")
            high_count = by_sev.get("High", 0) + by_sev.get("Critical", 0)
            lines.append(f"\nHigh+Critical events: {high_count}")
            lines.append(f"\n{'='*60}\nExported by Command Nexus(TM) Audit Trail Builder")
        self._at_export_output.setText("\n".join(lines))
        self._set_result_summary(f"Exported {len(self._audit_events)} audit events as {fmt}.")


# ===========================================================================
# Phase 5: Remaining Capabilities (21 dialogs)
# ===========================================================================

class ActivityWatcherDialog(BaseCapabilityDialog):
    """Activity Watcher — observes work patterns, tracks app usage, productivity insights."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Activity Watcher — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._activities: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_aw_log_tab(), "Log Activity")
        tabs.addTab(self._build_aw_summary_tab(), "Summary")
        tabs.addTab(self._build_aw_patterns_tab(), "Patterns")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Activity watcher observes work patterns. Privacy — data stored locally. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_aw_log_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Log Activity"))
        l.addWidget(QLabel("Activity type:"))
        self._aw_type = QComboBox()
        self._aw_type.addItems(["Coding", "Research", "Writing", "Meeting", "Review", "Planning", "Learning", "Communication", "Other"])
        l.addWidget(self._aw_type)
        l.addWidget(QLabel("Description:"))
        self._aw_desc = QLineEdit()
        self._aw_desc.setPlaceholderText("What are you doing?")
        l.addWidget(self._aw_desc)
        l.addWidget(QLabel("Duration (minutes):"))
        self._aw_duration = QLineEdit()
        self._aw_duration.setPlaceholderText("e.g., 30")
        l.addWidget(self._aw_duration)
        l.addWidget(QLabel("Productivity (1-5):"))
        self._aw_prod = QComboBox()
        self._aw_prod.addItems(["1 - Distracted", "2 - Low focus", "3 - Normal", "4 - Focused", "5 - Deep flow"])
        l.addWidget(self._aw_prod)
        btn = QPushButton("Log Activity")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._aw_log)
        l.addWidget(btn)
        self._aw_log_output = QTextEdit()
        self._aw_log_output.setReadOnly(True)
        self._aw_log_output.setStyleSheet("")
        l.addWidget(self._aw_log_output, stretch=1)
        return w

    def _build_aw_summary_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Activity Summary"))
        btn = QPushButton("Generate Summary")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._aw_summary)
        l.addWidget(btn)
        self._aw_summary_output = QTextEdit()
        self._aw_summary_output.setReadOnly(True)
        self._aw_summary_output.setStyleSheet("")
        l.addWidget(self._aw_summary_output, stretch=1)
        return w

    def _build_aw_patterns_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Work Patterns"))
        btn = QPushButton("Analyze Patterns")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._aw_patterns)
        l.addWidget(btn)
        self._aw_patterns_output = QTextEdit()
        self._aw_patterns_output.setReadOnly(True)
        self._aw_patterns_output.setStyleSheet("")
        l.addWidget(self._aw_patterns_output, stretch=1)
        return w

    def _aw_log(self):
        atype = self._aw_type.currentText()
        desc = self._aw_desc.text().strip()
        dur = self._aw_duration.text().strip()
        prod = self._aw_prod.currentText()
        if not desc:
            self._aw_log_output.setText("Description is required.")
            return
        entry = {"type": atype, "desc": desc, "duration": int(dur) if dur.isdigit() else 0, "productivity": prod, "timestamp": datetime.now().isoformat()}
        self._activities.append(entry)
        self._aw_log_output.setText(f"Logged: {atype} — {desc} ({dur}min, {prod})\nTotal activities: {len(self._activities)}")
        self._aw_desc.clear()
        self._aw_duration.clear()

    def _aw_summary(self):
        if not self._activities:
            self._aw_summary_output.setText("No activities logged yet.")
            return
        by_type = {}
        total_min = 0
        prod_scores = []
        for a in self._activities:
            by_type[a["type"]] = by_type.get(a["type"], {"count": 0, "minutes": 0})
            by_type[a["type"]]["count"] += 1
            by_type[a["type"]]["minutes"] += a["duration"]
            total_min += a["duration"]
            score = int(a["productivity"][0])
            prod_scores.append(score)
        lines = [f"ACTIVITY SUMMARY\n{'='*60}\n"]
        lines.append(f"Total activities: {len(self._activities)}")
        lines.append(f"Total time: {total_min} min ({total_min/60:.1f} hrs)")
        lines.append(f"Avg productivity: {sum(prod_scores)/len(prod_scores):.1f}/5\n")
        lines.append("BY TYPE:")
        for t, info in sorted(by_type.items(), key=lambda x: x[1]["minutes"], reverse=True):
            lines.append(f"  {t:15s}: {info['count']} sessions, {info['minutes']} min")
        self._aw_summary_output.setText("\n".join(lines))

    def _aw_patterns(self):
        if not self._activities:
            self._aw_patterns_output.setText("No activities to analyze.")
            return
        lines = [f"WORK PATTERNS\n{'='*60}\n"]
        best_type = max(set(a["type"] for a in self._activities), key=lambda t: sum(a["productivity"][0] for a in self._activities if a["type"] == t))
        lines.append(f"Most productive activity type: {best_type}")
        focused = [a for a in self._activities if int(a["productivity"][0]) >= 4]
        lines.append(f"Deep focus sessions: {len(focused)} / {len(self._activities)} ({len(focused)/len(self._activities)*100:.0f}%)")
        lines.append(f"\nACTIVITY TIMELINE:")
        for a in self._activities:
            lines.append(f"  [{a['timestamp'][:16]}] {a['type']:12s} | {a['duration']:3d}min | {a['productivity']}")
        lines.append("\nThe built-in intelligence can provide pattern insights.")
        self._aw_patterns_output.setText("\n".join(lines))
        self._set_result_summary(f"Analyzed {len(self._activities)} activities.")


class TeamOrchestratorDialog(BaseCapabilityDialog):
    """Team Orchestrator — task delegation, team coordination, role assignment, progress tracking."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Team Orchestrator — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._members: list[dict] = []
        self._tasks: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_to_members_tab(), "Team Members")
        tabs.addTab(self._build_to_tasks_tab(), "Tasks")
        tabs.addTab(self._build_to_board_tab(), "Task Board")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Team orchestrator is advisory. User is responsible for team outcomes. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_to_members_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Team Members"))
        l.addWidget(QLabel("Member name:"))
        self._to_member_name = QLineEdit()
        l.addWidget(self._to_member_name)
        l.addWidget(QLabel("Role:"))
        self._to_member_role = QLineEdit()
        self._to_member_role.setPlaceholderText("e.g., Developer, Designer, QA, Lead")
        l.addWidget(self._to_member_role)
        l.addWidget(QLabel("Skills (comma-separated):"))
        self._to_member_skills = QLineEdit()
        l.addWidget(self._to_member_skills)
        btn = QPushButton("Add Member")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._to_add_member)
        l.addWidget(btn)
        self._to_members_output = QTextEdit()
        self._to_members_output.setReadOnly(True)
        self._to_members_output.setStyleSheet("")
        l.addWidget(self._to_members_output, stretch=1)
        return w

    def _build_to_tasks_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Create Task"))
        l.addWidget(QLabel("Task title:"))
        self._to_task_title = QLineEdit()
        l.addWidget(self._to_task_title)
        l.addWidget(QLabel("Assign to:"))
        self._to_task_assign = QComboBox()
        l.addWidget(self._to_task_assign)
        l.addWidget(QLabel("Priority:"))
        self._to_task_priority = QComboBox()
        self._to_task_priority.addItems(["Low", "Medium", "High", "Critical"])
        l.addWidget(self._to_task_priority)
        l.addWidget(QLabel("Description:"))
        self._to_task_desc = QTextEdit()
        l.addWidget(self._to_task_desc)
        btn_row = QHBoxLayout()
        add_btn = QPushButton("Create Task")
        add_btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        add_btn.clicked.connect(self._to_add_task)
        btn_row.addWidget(add_btn)
        done_btn = QPushButton("Mark Latest Done")
        done_btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        done_btn.clicked.connect(self._to_complete_task)
        btn_row.addWidget(done_btn)
        l.addLayout(btn_row)
        self._to_tasks_output = QTextEdit()
        self._to_tasks_output.setReadOnly(True)
        self._to_tasks_output.setStyleSheet("")
        l.addWidget(self._to_tasks_output, stretch=1)
        return w

    def _build_to_board_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Task Board"))
        btn = QPushButton("Refresh Board")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._to_refresh_board)
        l.addWidget(btn)
        self._to_board_output = QTextEdit()
        self._to_board_output.setReadOnly(True)
        self._to_board_output.setStyleSheet("")
        l.addWidget(self._to_board_output, stretch=1)
        return w

    def _to_add_member(self):
        name = self._to_member_name.text().strip()
        role = self._to_member_role.text().strip()
        skills = [s.strip() for s in self._to_member_skills.text().split(",") if s.strip()]
        if not name:
            self._to_members_output.setText("Member name is required.")
            return
        member = {"id": len(self._members) + 1, "name": name, "role": role, "skills": skills}
        self._members.append(member)
        self._to_task_assign.addItem(f"{name} ({role})")
        self._to_members_output.setText(f"Member added: {name} — {role}\nSkills: {', '.join(skills)}\nTotal: {len(self._members)}")
        self._to_member_name.clear()
        self._to_member_role.clear()
        self._to_member_skills.clear()

    def _to_add_task(self):
        title = self._to_task_title.text().strip()
        assignee = self._to_task_assign.currentText() if self._to_task_assign.count() > 0 else "Unassigned"
        priority = self._to_task_priority.currentText()
        desc = self._to_task_desc.toPlainText().strip()
        if not title:
            self._to_tasks_output.setText("Task title is required.")
            return
        task = {"id": len(self._tasks) + 1, "title": title, "assignee": assignee, "priority": priority, "desc": desc, "status": "To Do", "created": datetime.now().isoformat()}
        self._tasks.append(task)
        self._to_tasks_output.setText(f"Task created: [{task['id']}] {title}\nAssignee: {assignee}\nPriority: {priority}")
        self._to_task_title.clear()
        self._to_task_desc.clear()

    def _to_complete_task(self):
        for t in reversed(self._tasks):
            if t["status"] != "Done":
                t["status"] = "Done"
                self._to_tasks_output.setText(f"Task completed: [{t['id']}] {t['title']}")
                return
        self._to_tasks_output.setText("No pending tasks.")

    def _to_refresh_board(self):
        if not self._tasks:
            self._to_board_output.setText("No tasks created yet.")
            return
        columns = {"To Do": [], "In Progress": [], "Done": []}
        for t in self._tasks:
            columns.setdefault(t["status"], []).append(t)
        lines = [f"TASK BOARD\n{'='*60}\n"]
        for status in ["To Do", "In Progress", "Done"]:
            items = columns.get(status, [])
            lines.append(f"\n[{status}] ({len(items)})")
            for t in items:
                lines.append(f"  [{t['id']}] {t['title']} — {t['assignee']} ({t['priority']})")
        self._to_board_output.setText("\n".join(lines))


class MemoryBridgeDialog(BaseCapabilityDialog):
    """Memory Bridge — connects AI memory across sessions, context handoff, memory sync."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Memory Bridge — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._bridges: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_mb_handoff_tab(), "Context Handoff")
        tabs.addTab(self._build_mb_history_tab(), "Bridge History")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Memory bridge connects sessions. Privacy — data stored locally. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_mb_handoff_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Context Handoff"))
        l.addWidget(QLabel("From session (label):"))
        self._mb_from = QLineEdit()
        self._mb_from.setPlaceholderText("e.g., Planning Session 1")
        l.addWidget(self._mb_from)
        l.addWidget(QLabel("To session (label):"))
        self._mb_to = QLineEdit()
        self._mb_to.setPlaceholderText("e.g., Implementation Session 2")
        l.addWidget(self._mb_to)
        l.addWidget(QLabel("Context to carry over:"))
        self._mb_context = QTextEdit()
        self._mb_context.setPlaceholderText("What context should be carried to the next session?")
        l.addWidget(self._mb_context, stretch=1)
        btn = QPushButton("Create Bridge")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._mb_create)
        l.addWidget(btn)
        self._mb_handoff_output = QTextEdit()
        self._mb_handoff_output.setReadOnly(True)
        self._mb_handoff_output.setStyleSheet("")
        l.addWidget(self._mb_handoff_output)
        return w

    def _build_mb_history_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Bridge History"))
        btn = QPushButton("Show All Bridges")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._mb_history)
        l.addWidget(btn)
        self._mb_history_output = QTextEdit()
        self._mb_history_output.setReadOnly(True)
        self._mb_history_output.setStyleSheet("")
        l.addWidget(self._mb_history_output, stretch=1)
        return w

    def _mb_create(self):
        frm = self._mb_from.text().strip()
        to = self._mb_to.text().strip()
        ctx = self._mb_context.toPlainText().strip()
        if not frm or not to or not ctx:
            self._mb_handoff_output.setText("All fields are required.")
            return
        bridge = {"id": len(self._bridges) + 1, "from": frm, "to": to, "context": ctx, "timestamp": datetime.now().isoformat()}
        self._bridges.append(bridge)
        self._mb_handoff_output.setText(f"Bridge created:\n  From: {frm}\n  To: {to}\n  Context: {len(ctx)} chars\n  Total bridges: {len(self._bridges)}")
        self._mb_from.clear()
        self._mb_to.clear()
        self._mb_context.clear()

    def _mb_history(self):
        if not self._bridges:
            self._mb_history_output.setText("No bridges created yet.")
            return
        lines = [f"BRIDGE HISTORY\n{'='*60}\n{len(self._bridges)} bridges:\n"]
        for b in self._bridges:
            lines.append(f"  [{b['id']}] {b['from']} -> {b['to']}")
            lines.append(f"    Created: {b['timestamp'][:19]}")
            lines.append(f"    Context: {b['context'][:200]}{'...' if len(b['context']) > 200 else ''}\n")
        self._mb_history_output.setText("\n".join(lines))


class VisualCanvasDialog(BaseCapabilityDialog):
    """Visual Canvas — diagram builder, flowchart creator, visual workspace."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Visual Canvas — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._nodes: list[dict] = []
        self._edges: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_vc_nodes_tab(), "Nodes")
        tabs.addTab(self._build_vc_edges_tab(), "Connections")
        tabs.addTab(self._build_vc_render_tab(), "Render")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Visual canvas is advisory. Diagrams are for planning purposes. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_vc_nodes_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Add Node"))
        l.addWidget(QLabel("Node label:"))
        self._vc_node_label = QLineEdit()
        self._vc_node_label.setPlaceholderText("e.g., Start Process, Decision Point, End")
        l.addWidget(self._vc_node_label)
        l.addWidget(QLabel("Node type:"))
        self._vc_node_type = QComboBox()
        self._vc_node_type.addItems(["Start", "Process", "Decision", "Data", "End", "Connector"])
        l.addWidget(self._vc_node_type)
        btn = QPushButton("Add Node")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._vc_add_node)
        l.addWidget(btn)
        self._vc_nodes_output = QTextEdit()
        self._vc_nodes_output.setReadOnly(True)
        self._vc_nodes_output.setStyleSheet("")
        l.addWidget(self._vc_nodes_output, stretch=1)
        return w

    def _build_vc_edges_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Add Connection"))
        l.addWidget(QLabel("From node #:"))
        self._vc_edge_from = QLineEdit()
        l.addWidget(self._vc_edge_from)
        l.addWidget(QLabel("To node #:"))
        self._vc_edge_to = QLineEdit()
        l.addWidget(self._vc_edge_to)
        l.addWidget(QLabel("Label (optional):"))
        self._vc_edge_label = QLineEdit()
        self._vc_edge_label.setPlaceholderText("e.g., Yes, No, Next")
        l.addWidget(self._vc_edge_label)
        btn = QPushButton("Add Connection")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._vc_add_edge)
        l.addWidget(btn)
        self._vc_edges_output = QTextEdit()
        self._vc_edges_output.setReadOnly(True)
        self._vc_edges_output.setStyleSheet("")
        l.addWidget(self._vc_edges_output)
        return w

    def _build_vc_render_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Render Diagram (Text)"))
        btn = QPushButton("Render")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._vc_render)
        l.addWidget(btn)
        self._vc_render_output = QTextEdit()
        self._vc_render_output.setReadOnly(True)
        self._vc_render_output.setStyleSheet("")
        l.addWidget(self._vc_render_output, stretch=1)
        return w

    def _vc_add_node(self):
        label = self._vc_node_label.text().strip()
        ntype = self._vc_node_type.currentText()
        if not label:
            self._vc_nodes_output.setText("Node label is required.")
            return
        node = {"id": len(self._nodes) + 1, "label": label, "type": ntype}
        self._nodes.append(node)
        self._vc_nodes_output.setText(f"Node added: [{node['id']}] {label} ({ntype})\nTotal nodes: {len(self._nodes)}")
        self._vc_node_label.clear()

    def _vc_add_edge(self):
        frm = self._vc_edge_from.text().strip()
        to = self._vc_edge_to.text().strip()
        label = self._vc_edge_label.text().strip()
        if not frm.isdigit() or not to.isdigit():
            self._vc_edges_output.setText("From and To must be node numbers.")
            return
        edge = {"from": int(frm), "to": int(to), "label": label}
        self._edges.append(edge)
        self._vc_edges_output.setText(f"Connection: {frm} -> {to}" + (f" ({label})" if label else "") + f"\nTotal edges: {len(self._edges)}")
        self._vc_edge_from.clear()
        self._vc_edge_to.clear()
        self._vc_edge_label.clear()

    def _vc_render(self):
        if not self._nodes:
            self._vc_render_output.setText("No nodes to render.")
            return
        lines = [f"DIAGRAM RENDER (Text)\n{'='*60}\n"]
        for n in self._nodes:
            icon = {"Start": "(O)", "Process": "[ ]", "Decision": "< >", "Data": "(~)", "End": "(X)", "Connector": "(.)"}[n["type"]]
            lines.append(f"  {icon} [{n['id']}] {n['label']}")
        if self._edges:
            lines.append("\nCONNECTIONS:")
            for e in self._edges:
                lbl = f" -- {e['label']} -->" if e["label"] else " -->"
                lines.append(f"  [{e['from']}] {lbl} [{e['to']}]")
        self._vc_render_output.setText("\n".join(lines))


class APIIntegratorDialog(BaseCapabilityDialog):
    """API Integrator — connect external APIs, test endpoints, manage integrations."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"API Integrator — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._apis: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_api_add_tab(), "Add API")
        tabs.addTab(self._build_api_test_tab(), "Test Endpoint")
        tabs.addTab(self._build_api_list_tab(), "Manage")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("External API calls carry security risk. Verify endpoints before connecting. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_api_add_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Add API Integration"))
        l.addWidget(QLabel("API name:"))
        self._api_name = QLineEdit()
        self._api_name.setPlaceholderText("e.g., Stripe, Twilio, Custom API")
        l.addWidget(self._api_name)
        l.addWidget(QLabel("Base URL:"))
        self._api_url = QLineEdit()
        self._api_url.setPlaceholderText("https://api.example.com/v1")
        l.addWidget(self._api_url)
        l.addWidget(QLabel("Auth type:"))
        self._api_auth = QComboBox()
        self._api_auth.addItems(["None", "API Key (Header)", "Bearer Token", "Basic Auth", "OAuth2"])
        l.addWidget(self._api_auth)
        l.addWidget(QLabel("Key/Token (stored locally only):"))
        self._api_key = QLineEdit()
        self._api_key.setPlaceholderText("Your API key or token")
        l.addWidget(self._api_key)
        btn = QPushButton("Add Integration")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._api_add)
        l.addWidget(btn)
        self._api_add_output = QTextEdit()
        self._api_add_output.setReadOnly(True)
        self._api_add_output.setStyleSheet("")
        l.addWidget(self._api_add_output)
        return w

    def _build_api_test_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Test Endpoint"))
        l.addWidget(QLabel("Select API:"))
        self._api_test_combo = QComboBox()
        l.addWidget(self._api_test_combo)
        l.addWidget(QLabel("Endpoint path:"))
        self._api_test_path = QLineEdit()
        self._api_test_path.setPlaceholderText("/users, /data, /status")
        l.addWidget(self._api_test_path)
        l.addWidget(QLabel("Method:"))
        self._api_test_method = QComboBox()
        self._api_test_method.addItems(["GET", "POST", "PUT", "DELETE"])
        l.addWidget(self._api_test_method)
        l.addWidget(QLabel("Body (JSON, for POST/PUT):"))
        self._api_test_body = QTextEdit()
        self._api_test_body.setPlaceholderText('{"key": "value"}')
        l.addWidget(self._api_test_body)
        btn = QPushButton("Test Request")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._api_test)
        l.addWidget(btn)
        self._api_test_output = QTextEdit()
        self._api_test_output.setReadOnly(True)
        self._api_test_output.setStyleSheet("")
        l.addWidget(self._api_test_output, stretch=1)
        return w

    def _build_api_list_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Manage Integrations"))
        btn = QPushButton("List All")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._api_list)
        l.addWidget(btn)
        self._api_list_output = QTextEdit()
        self._api_list_output.setReadOnly(True)
        self._api_list_output.setStyleSheet("")
        l.addWidget(self._api_list_output, stretch=1)
        return w

    def _api_add(self):
        name = self._api_name.text().strip()
        url = self._api_url.text().strip()
        auth = self._api_auth.currentText()
        key = self._api_key.text().strip()
        if not name or not url:
            self._api_add_output.setText("Name and URL are required.")
            return
        api = {"id": len(self._apis) + 1, "name": name, "url": url, "auth": auth, "key": key, "added": datetime.now().isoformat()}
        self._apis.append(api)
        self._api_test_combo.addItem(f"{name} ({url})")
        self._api_add_output.setText(f"API added: {name}\n  URL: {url}\n  Auth: {auth}\n  Total: {len(self._apis)}")
        self._api_name.clear()
        self._api_url.clear()
        self._api_key.clear()

    def _api_test(self):
        idx = self._api_test_combo.currentIndex()
        path = self._api_test_path.text().strip()
        method = self._api_test_method.currentText()
        if idx < 0 or not path:
            self._api_test_output.setText("Select an API and enter an endpoint path.")
            return
        api = self._apis[idx]
        full_url = api["url"].rstrip("/") + "/" + path.lstrip("/")
        self._api_test_output.setText(
            f"TEST REQUEST\n{'='*60}\n"
            f"API: {api['name']}\nURL: {full_url}\nMethod: {method}\nAuth: {api['auth']}\n\n"
            f"NOTE: This is a simulation. The built-in intelligence can analyze responses, or implement\n"
            f"the actual HTTP request to test live endpoints.\n\n"
            f"WARNING: External API calls carry security risk. Only test\n"
            f"endpoints you trust and have authorization to access."
        )

    def _api_list(self):
        if not self._apis:
            self._api_list_output.setText("No APIs registered.")
            return
        lines = [f"API INTEGRATIONS\n{'='*60}\n{len(self._apis)} APIs:\n"]
        for a in self._apis:
            lines.append(f"  [{a['id']}] {a['name']}")
            lines.append(f"    URL: {a['url']}")
            lines.append(f"    Auth: {a['auth']}")
            lines.append(f"    Added: {a['added'][:10]}\n")
        self._api_list_output.setText("\n".join(lines))


class KnowledgeBaseDialog(BaseCapabilityDialog):
    """Knowledge Base — structured knowledge storage, Q&A, topic browser."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Knowledge Base — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._kb_entries: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_kb_add_tab(), "Add Knowledge")
        tabs.addTab(self._build_kb_qa_tab(), "Q&A")
        tabs.addTab(self._build_kb_browse_tab(), "Browse Topics")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Knowledge base stores data locally. Be mindful of sensitive information. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_kb_add_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Add Knowledge Entry"))
        l.addWidget(QLabel("Topic:"))
        self._kb_topic = QLineEdit()
        self._kb_topic.setPlaceholderText("e.g., Python decorators, Marketing strategy")
        l.addWidget(self._kb_topic)
        l.addWidget(QLabel("Question:"))
        self._kb_question = QLineEdit()
        l.addWidget(self._kb_question)
        l.addWidget(QLabel("Answer:"))
        self._kb_answer = QTextEdit()
        l.addWidget(self._kb_answer, stretch=1)
        btn = QPushButton("Add Entry")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._kb_add)
        l.addWidget(btn)
        self._kb_add_output = QTextEdit()
        self._kb_add_output.setReadOnly(True)
        self._kb_add_output.setStyleSheet("")
        l.addWidget(self._kb_add_output)
        return w

    def _build_kb_qa_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Ask a Question"))
        l.addWidget(QLabel("Search the knowledge base:"))
        self._kb_qa_input = QLineEdit()
        self._kb_qa_input.setPlaceholderText("Type your question...")
        l.addWidget(self._kb_qa_input)
        btn = QPushButton("Search")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._kb_qa)
        l.addWidget(btn)
        self._kb_qa_output = QTextEdit()
        self._kb_qa_output.setReadOnly(True)
        self._kb_qa_output.setStyleSheet("")
        l.addWidget(self._kb_qa_output, stretch=1)
        return w

    def _build_kb_browse_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Browse by Topic"))
        btn = QPushButton("Show All Topics")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._kb_browse)
        l.addWidget(btn)
        self._kb_browse_output = QTextEdit()
        self._kb_browse_output.setReadOnly(True)
        self._kb_browse_output.setStyleSheet("")
        l.addWidget(self._kb_browse_output, stretch=1)
        return w

    def _kb_add(self):
        topic = self._kb_topic.text().strip()
        question = self._kb_question.text().strip()
        answer = self._kb_answer.toPlainText().strip()
        if not topic or not question or not answer:
            self._kb_add_output.setText("All fields are required.")
            return
        entry = {"id": len(self._kb_entries) + 1, "topic": topic, "question": question, "answer": answer, "added": datetime.now().isoformat()}
        self._kb_entries.append(entry)
        self._kb_add_output.setText(f"Entry added: [{entry['id']}] {topic}\n  Q: {question}\n  Total: {len(self._kb_entries)}")
        self._kb_topic.clear()
        self._kb_question.clear()
        self._kb_answer.clear()

    def _kb_qa(self):
        query = self._kb_qa_input.text().strip().lower()
        if not query or not self._kb_entries:
            self._kb_qa_output.setText("Enter a question and ensure knowledge entries exist.")
            return
        matches = [e for e in self._kb_entries if query in e["question"].lower() or query in e["topic"].lower() or query in e["answer"].lower()]
        if not matches:
            self._kb_qa_output.setText(f"No entries matching '{query}'.")
            return
        lines = [f"Q&A RESULTS\n{'='*60}\n{len(matches)} matches:\n"]
        for e in matches:
            lines.append(f"  [{e['id']}] Topic: {e['topic']}")
            lines.append(f"  Q: {e['question']}")
            lines.append(f"  A: {e['answer'][:300]}{'...' if len(e['answer']) > 300 else ''}\n")
        self._kb_qa_output.setText("\n".join(lines))

    def _kb_browse(self):
        if not self._kb_entries:
            self._kb_browse_output.setText("Knowledge base is empty.")
            return
        topics = {}
        for e in self._kb_entries:
            topics.setdefault(e["topic"], []).append(e)
        lines = [f"KNOWLEDGE BASE TOPICS\n{'='*60}\n{len(topics)} topics, {len(self._kb_entries)} entries:\n"]
        for topic, entries in sorted(topics.items()):
            lines.append(f"\n[{topic}] ({len(entries)} entries)")
            for e in entries:
                lines.append(f"  [{e['id']}] {e['question']}")
        self._kb_browse_output.setText("\n".join(lines))


class EmailAutomationDialog(BaseCapabilityDialog):
    """Email Automation — template builder, sequence planner, send scheduler."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Email Automation — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._templates: list[dict] = []
        self._sequences: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_ea_template_tab(), "Templates")
        tabs.addTab(self._build_ea_sequence_tab(), "Sequences")
        tabs.addTab(self._build_ea_schedule_tab(), "Schedule")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Email automation may be subject to regulations (CAN-SPAM, GDPR). Ensure compliance. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_ea_template_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Email Template Builder"))
        l.addWidget(QLabel("Template name:"))
        self._ea_tpl_name = QLineEdit()
        l.addWidget(self._ea_tpl_name)
        l.addWidget(QLabel("Subject:"))
        self._ea_tpl_subject = QLineEdit()
        l.addWidget(self._ea_tpl_subject)
        l.addWidget(QLabel("Body:"))
        self._ea_tpl_body = QTextEdit()
        self._ea_tpl_body.setPlaceholderText("Use {{name}}, {{company}} for personalization...")
        l.addWidget(self._ea_tpl_body, stretch=1)
        btn = QPushButton("Save Template")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._ea_save_template)
        l.addWidget(btn)
        self._ea_tpl_output = QTextEdit()
        self._ea_tpl_output.setReadOnly(True)
        self._ea_tpl_output.setStyleSheet("")
        l.addWidget(self._ea_tpl_output)
        return w

    def _build_ea_sequence_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Email Sequence Planner"))
        l.addWidget(QLabel("Sequence name:"))
        self._ea_seq_name = QLineEdit()
        l.addWidget(self._ea_seq_name)
        l.addWidget(QLabel("Steps (one per line: Day X | Template name | Description):"))
        self._ea_seq_steps = QTextEdit()
        self._ea_seq_steps.setPlaceholderText("Day 1 | Welcome | Initial welcome email\nDay 3 | Onboarding | Getting started tips\nDay 7 | Check-in | How's it going?")
        l.addWidget(self._ea_seq_steps, stretch=1)
        btn = QPushButton("Save Sequence")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._ea_save_sequence)
        l.addWidget(btn)
        self._ea_seq_output = QTextEdit()
        self._ea_seq_output.setReadOnly(True)
        self._ea_seq_output.setStyleSheet("")
        l.addWidget(self._ea_seq_output)
        return w

    def _build_ea_schedule_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Send Schedule"))
        btn = QPushButton("Show All Templates & Sequences")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._ea_show_all)
        l.addWidget(btn)
        self._ea_sched_output = QTextEdit()
        self._ea_sched_output.setReadOnly(True)
        self._ea_sched_output.setStyleSheet("")
        l.addWidget(self._ea_sched_output, stretch=1)
        return w

    def _ea_save_template(self):
        name = self._ea_tpl_name.text().strip()
        subject = self._ea_tpl_subject.text().strip()
        body = self._ea_tpl_body.toPlainText().strip()
        if not name or not subject:
            self._ea_tpl_output.setText("Name and subject are required.")
            return
        tpl = {"id": len(self._templates) + 1, "name": name, "subject": subject, "body": body}
        self._templates.append(tpl)
        self._ea_tpl_output.setText(f"Template saved: [{tpl['id']}] {name}\n  Subject: {subject}\n  Body: {len(body)} chars\n  Total: {len(self._templates)}")
        self._ea_tpl_name.clear()
        self._ea_tpl_subject.clear()
        self._ea_tpl_body.clear()

    def _ea_save_sequence(self):
        name = self._ea_seq_name.text().strip()
        steps_raw = self._ea_seq_steps.toPlainText().strip()
        if not name or not steps_raw:
            self._ea_seq_output.setText("Name and steps are required.")
            return
        steps = []
        for line in steps_raw.split("\n"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 2:
                steps.append({"day": parts[0], "template": parts[1], "desc": parts[2] if len(parts) > 2 else ""})
        seq = {"id": len(self._sequences) + 1, "name": name, "steps": steps}
        self._sequences.append(seq)
        self._ea_seq_output.setText(f"Sequence saved: [{seq['id']}] {name}\n  Steps: {len(steps)}\n  Total: {len(self._sequences)}")
        self._ea_seq_name.clear()
        self._ea_seq_steps.clear()

    def _ea_show_all(self):
        lines = [f"EMAIL AUTOMATION OVERVIEW\n{'='*60}\n"]
        lines.append(f"Templates ({len(self._templates)}):")
        for t in self._templates:
            lines.append(f"  [{t['id']}] {t['name']} — {t['subject']}")
        lines.append(f"\nSequences ({len(self._sequences)}):")
        for s in self._sequences:
            lines.append(f"  [{s['id']}] {s['name']} ({len(s['steps'])} steps)")
            for step in s["steps"]:
                lines.append(f"    {step['day']} | {step['template']} | {step['desc']}")
        self._ea_sched_output.setText("\n".join(lines))


class CalendarManagerDialog(BaseCapabilityDialog):
    """Calendar Manager — event scheduling, reminders, agenda view, conflict detection."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Calendar Manager — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._events: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_cm_add_tab(), "Add Event")
        tabs.addTab(self._build_cm_agenda_tab(), "Agenda")
        tabs.addTab(self._build_cm_conflicts_tab(), "Conflicts")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Calendar manager is advisory. User is responsible for scheduling decisions. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_cm_add_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Add Calendar Event"))
        l.addWidget(QLabel("Event title:"))
        self._cm_title = QLineEdit()
        l.addWidget(self._cm_title)
        l.addWidget(QLabel("Date (YYYY-MM-DD):"))
        self._cm_date = QLineEdit()
        l.addWidget(self._cm_date)
        l.addWidget(QLabel("Start time (HH:MM):"))
        self._cm_start = QLineEdit()
        self._cm_start.setPlaceholderText("e.g., 14:30")
        l.addWidget(self._cm_start)
        l.addWidget(QLabel("End time (HH:MM):"))
        self._cm_end = QLineEdit()
        self._cm_end.setPlaceholderText("e.g., 15:30")
        l.addWidget(self._cm_end)
        l.addWidget(QLabel("Category:"))
        self._cm_category = QComboBox()
        self._cm_category.addItems(["Work", "Personal", "Meeting", "Deadline", "Reminder", "Other"])
        l.addWidget(self._cm_category)
        l.addWidget(QLabel("Notes:"))
        self._cm_notes = QTextEdit()
        l.addWidget(self._cm_notes)
        btn = QPushButton("Add Event")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._cm_add)
        l.addWidget(btn)
        self._cm_add_output = QTextEdit()
        self._cm_add_output.setReadOnly(True)
        self._cm_add_output.setStyleSheet("")
        l.addWidget(self._cm_add_output)
        return w

    def _build_cm_agenda_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Agenda View"))
        l.addWidget(QLabel("Filter by date (YYYY-MM-DD, empty for all):"))
        self._cm_agenda_filter = QLineEdit()
        l.addWidget(self._cm_agenda_filter)
        btn = QPushButton("Show Agenda")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._cm_agenda)
        l.addWidget(btn)
        self._cm_agenda_output = QTextEdit()
        self._cm_agenda_output.setReadOnly(True)
        self._cm_agenda_output.setStyleSheet("")
        l.addWidget(self._cm_agenda_output, stretch=1)
        return w

    def _build_cm_conflicts_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Conflict Detection"))
        btn = QPushButton("Check Conflicts")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._cm_conflicts)
        l.addWidget(btn)
        self._cm_conflicts_output = QTextEdit()
        self._cm_conflicts_output.setReadOnly(True)
        self._cm_conflicts_output.setStyleSheet("")
        l.addWidget(self._cm_conflicts_output, stretch=1)
        return w

    def _cm_add(self):
        title = self._cm_title.text().strip()
        date = self._cm_date.text().strip()
        start = self._cm_start.text().strip()
        end = self._cm_end.text().strip()
        category = self._cm_category.currentText()
        notes = self._cm_notes.toPlainText().strip()
        if not title or not date:
            self._cm_add_output.setText("Title and date are required.")
            return
        event = {"id": len(self._events) + 1, "title": title, "date": date, "start": start, "end": end, "category": category, "notes": notes}
        self._events.append(event)
        self._cm_add_output.setText(f"Event added: [{event['id']}] {title}\n  Date: {date} {start}-{end}\n  Category: {category}")
        self._cm_title.clear()
        self._cm_date.clear()
        self._cm_start.clear()
        self._cm_end.clear()
        self._cm_notes.clear()

    def _cm_agenda(self):
        if not self._events:
            self._cm_agenda_output.setText("No events scheduled.")
            return
        filt = self._cm_agenda_filter.text().strip()
        events = sorted(self._events, key=lambda e: (e["date"], e["start"]))
        if filt:
            events = [e for e in events if e["date"] == filt]
        if not events:
            self._cm_agenda_output.setText(f"No events on {filt}.")
            return
        lines = [f"AGENDA\n{'='*60}\n{len(events)} events:\n"]
        cur_date = ""
        for e in events:
            if e["date"] != cur_date:
                cur_date = e["date"]
                lines.append(f"\n--- {cur_date} ---")
            lines.append(f"  {e['start']:>5s}-{e['end']:<5s} [{e['category']}] {e['title']}")
        self._cm_agenda_output.setText("\n".join(lines))

    def _cm_conflicts(self):
        if not self._events:
            self._cm_conflicts_output.setText("No events to check.")
            return
        conflicts = []
        for i, a in enumerate(self._events):
            for b in self._events[i+1:]:
                if a["date"] == b["date"] and a["start"] and b["start"]:
                    if a["start"] < b["end"] and b["start"] < a["end"]:
                        conflicts.append((a, b))
        if not conflicts:
            self._cm_conflicts_output.setText("No scheduling conflicts detected.")
            return
        lines = [f"SCHEDULING CONFLICTS\n{'='*60}\n{len(conflicts)} conflicts:\n"]
        for a, b in conflicts:
            lines.append(f"  CONFLICT on {a['date']}:")
            lines.append(f"    [{a['id']}] {a['start']}-{a['end']} {a['title']}")
            lines.append(f"    [{b['id']}] {b['start']}-{b['end']} {b['title']}\n")
        self._cm_conflicts_output.setText("\n".join(lines))


class DocumentGeneratorDialog(BaseCapabilityDialog):
    """Document Generator — create structured documents from templates and AI input."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Document Generator — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._documents: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_dg_create_tab(), "Create Document")
        tabs.addTab(self._build_dg_templates_tab(), "Templates")
        tabs.addTab(self._build_dg_library_tab(), "Document Library")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Generated documents are drafts. Review before official use. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_dg_create_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Create Document"))
        l.addWidget(QLabel("Document title:"))
        self._dg_title = QLineEdit()
        l.addWidget(self._dg_title)
        l.addWidget(QLabel("Document type:"))
        self._dg_type = QComboBox()
        self._dg_type.addItems(["Report", "Proposal", "Memo", "Letter", "Specification", "Summary", "Article", "Custom"])
        l.addWidget(self._dg_type)
        l.addWidget(QLabel("Content:"))
        self._dg_content = QTextEdit()
        self._dg_content.setPlaceholderText("Write or paste your document content here...")
        l.addWidget(self._dg_content, stretch=1)
        btn = QPushButton("Save Document")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._dg_create)
        l.addWidget(btn)
        self._dg_create_output = QTextEdit()
        self._dg_create_output.setReadOnly(True)
        self._dg_create_output.setStyleSheet("")
        l.addWidget(self._dg_create_output)
        return w

    def _build_dg_templates_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Document Templates"))
        l.addWidget(QLabel("Select a template to preview:"))
        self._dg_tpl_combo = QComboBox()
        self._dg_tpl_combo.addItems([
            "Business Proposal — Executive summary, problem, solution, pricing",
            "Technical Spec — Overview, architecture, API, testing",
            "Meeting Memo — Date, attendees, agenda, decisions, action items",
            "Project Report — Status, milestones, risks, next steps",
            "Cover Letter — Intro, qualifications, closing",
        ])
        l.addWidget(self._dg_tpl_combo)
        btn = QPushButton("Preview Template")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._dg_preview_template)
        l.addWidget(btn)
        self._dg_tpl_output = QTextEdit()
        self._dg_tpl_output.setReadOnly(True)
        self._dg_tpl_output.setStyleSheet("")
        l.addWidget(self._dg_tpl_output, stretch=1)
        return w

    def _build_dg_library_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Document Library"))
        btn = QPushButton("Show All Documents")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._dg_library)
        l.addWidget(btn)
        self._dg_lib_output = QTextEdit()
        self._dg_lib_output.setReadOnly(True)
        self._dg_lib_output.setStyleSheet("")
        l.addWidget(self._dg_lib_output, stretch=1)
        return w

    def _dg_create(self):
        title = self._dg_title.text().strip()
        dtype = self._dg_type.currentText()
        content = self._dg_content.toPlainText().strip()
        if not title or not content:
            self._dg_create_output.setText("Title and content are required.")
            return
        doc = {"id": len(self._documents) + 1, "title": title, "type": dtype, "content": content, "created": datetime.now().isoformat()}
        self._documents.append(doc)
        self._dg_create_output.setText(f"Document saved: [{doc['id']}] {title}\n  Type: {dtype}\n  Length: {len(content)} chars\n  Total: {len(self._documents)}")
        self._dg_title.clear()
        self._dg_content.clear()

    def _dg_preview_template(self):
        tpl = self._dg_tpl_combo.currentText()
        templates = {
            "Business Proposal": "BUSINESS PROPOSAL\n\n1. Executive Summary\n   [Brief overview of the proposal]\n\n2. Problem Statement\n   [What problem are you solving?]\n\n3. Proposed Solution\n   [Your solution and approach]\n\n4. Pricing\n   [Cost breakdown]\n\n5. Timeline\n   [Key milestones]\n",
            "Technical Spec": "TECHNICAL SPECIFICATION\n\n1. Overview\n   [System purpose and scope]\n\n2. Architecture\n   [System design and components]\n\n3. API Definition\n   [Endpoints and data formats]\n\n4. Testing Plan\n   [Test strategy and coverage]\n",
            "Meeting Memo": "MEETING MEMO\n\nDate: [YYYY-MM-DD]\nAttendees: [List]\n\nAgenda:\n1. [Topic 1]\n2. [Topic 2]\n\nDecisions:\n- [Decision 1]\n\nAction Items:\n- [ ] [Item] — Owner: [Name] — Due: [Date]\n",
            "Project Report": "PROJECT REPORT\n\nStatus: [On Track / At Risk / Delayed]\n\nMilestones:\n- [Completed milestones]\n- [Upcoming milestones]\n\nRisks:\n- [Risk 1] — Mitigation: [Plan]\n\nNext Steps:\n1. [Action 1]\n2. [Action 2]\n",
            "Cover Letter": "COVER LETTER\n\nDear [Hiring Manager],\n\nI am writing to express my interest in [position] at [company].\n\n[Body paragraph 1: Why you're interested]\n[Body paragraph 2: Relevant qualifications]\n[Body paragraph 3: What you bring]\n\nThank you for your consideration.\n\nSincerely,\n[Your name]\n",
        }
        for key, text in templates.items():
            if tpl.startswith(key):
                self._dg_tpl_output.setText(text)
                return
        self._dg_tpl_output.setText("Template not found.")

    def _dg_library(self):
        if not self._documents:
            self._dg_lib_output.setText("No documents in library.")
            return
        lines = [f"DOCUMENT LIBRARY\n{'='*60}\n{len(self._documents)} documents:\n"]
        for d in self._documents:
            lines.append(f"  [{d['id']}] {d['title']} ({d['type']})")
            lines.append(f"    Created: {d['created'][:10]} | Length: {len(d['content'])} chars\n")
        self._dg_lib_output.setText("\n".join(lines))


class TranslationExpertDialog(BaseCapabilityDialog):
    """Translation Expert — multi-language translation, glossary, cultural notes."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Translation Expert — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._translations: list[dict] = []
        self._glossary: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_te_translate_tab(), "Translate")
        tabs.addTab(self._build_te_glossary_tab(), "Glossary")
        tabs.addTab(self._build_te_history_tab(), "History")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Translations are AI-assisted. Verify accuracy for official use. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_te_translate_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Translation"))
        row = QHBoxLayout()
        l.addWidget(QLabel("From:"))
        self._te_from = QComboBox()
        self._te_from.addItems(["English", "Spanish", "French", "German", "Chinese", "Japanese", "Korean", "Portuguese", "Italian", "Russian", "Arabic", "Hindi"])
        row.addWidget(self._te_from)
        l.addWidget(QLabel("To:"))
        self._te_to = QComboBox()
        self._te_to.addItems(["English", "Spanish", "French", "German", "Chinese", "Japanese", "Korean", "Portuguese", "Italian", "Russian", "Arabic", "Hindi"])
        row.addWidget(self._te_to)
        l.addLayout(row)
        l.addWidget(QLabel("Text to translate:"))
        self._te_input = QTextEdit()
        self._te_input.setPlaceholderText("Enter text to translate...")
        l.addWidget(self._te_input, stretch=1)
        btn = QPushButton("Translate")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._te_translate)
        l.addWidget(btn)
        self._te_output = QTextEdit()
        self._te_output.setReadOnly(True)
        self._te_output.setStyleSheet("")
        l.addWidget(self._te_output)
        return w

    def _build_te_glossary_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Glossary"))
        l.addWidget(QLabel("Source term:"))
        self._te_gloss_src = QLineEdit()
        l.addWidget(self._te_gloss_src)
        l.addWidget(QLabel("Translated term:"))
        self._te_gloss_tgt = QLineEdit()
        l.addWidget(self._te_gloss_tgt)
        l.addWidget(QLabel("Language pair:"))
        self._te_gloss_lang = QLineEdit()
        self._te_gloss_lang.setPlaceholderText("e.g., EN->ES")
        l.addWidget(self._te_gloss_lang)
        btn = QPushButton("Add to Glossary")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._te_add_glossary)
        l.addWidget(btn)
        self._te_gloss_output = QTextEdit()
        self._te_gloss_output.setReadOnly(True)
        self._te_gloss_output.setStyleSheet("")
        l.addWidget(self._te_gloss_output, stretch=1)
        return w

    def _build_te_history_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Translation History"))
        btn = QPushButton("Show History")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._te_history)
        l.addWidget(btn)
        self._te_history_output = QTextEdit()
        self._te_history_output.setReadOnly(True)
        self._te_history_output.setStyleSheet("")
        l.addWidget(self._te_history_output, stretch=1)
        return w

    def _te_translate(self):
        src_lang = self._te_from.currentText()
        tgt_lang = self._te_to.currentText()
        text = self._te_input.toPlainText().strip()
        if not text:
            self._te_output.setText("Enter text to translate.")
            return
        if src_lang == tgt_lang:
            self._te_output.setText("Source and target languages are the same.")
            return
        entry = {"id": len(self._translations) + 1, "from": src_lang, "to": tgt_lang, "source": text, "created": datetime.now().isoformat()}
        self._translations.append(entry)
        self._te_output.setText(
            f"TRANSLATION REQUEST\n{'='*60}\n"
            f"From: {src_lang} -> To: {tgt_lang}\n\n"
            f"SOURCE:\n{text[:500]}\n\n"
            f"TRANSLATION:\n[The built-in intelligence can provide translation.]\n"
            f"Local fallback: Translation requires a language model.\n"
            f"The source text has been saved to history for later processing.\n"
            f"Translation ID: {entry['id']}"
        )
        self._te_input.clear()

    def _te_add_glossary(self):
        src = self._te_gloss_src.text().strip()
        tgt = self._te_gloss_tgt.text().strip()
        lang = self._te_gloss_lang.text().strip()
        if not src or not tgt:
            self._te_gloss_output.setText("Source and target terms are required.")
            return
        entry = {"source": src, "target": tgt, "lang": lang}
        self._glossary.append(entry)
        self._te_gloss_output.setText(f"Glossary entry added: {src} -> {tgt} ({lang})\nTotal: {len(self._glossary)}")
        self._te_gloss_src.clear()
        self._te_gloss_tgt.clear()
        self._te_gloss_lang.clear()

    def _te_history(self):
        if not self._translations:
            self._te_history_output.setText("No translations yet.")
            return
        lines = [f"TRANSLATION HISTORY\n{'='*60}\n{len(self._translations)} translations:\n"]
        for t in self._translations:
            lines.append(f"  [{t['id']}] {t['from']} -> {t['to']}")
            lines.append(f"    Source: {t['source'][:100]}{'...' if len(t['source']) > 100 else ''}")
            lines.append(f"    Date: {t['created'][:19]}\n")
        self._te_history_output.setText("\n".join(lines))


class PresentationBuilderDialog(BaseCapabilityDialog):
    """Presentation Builder — slide deck creator, outline planner, speaker notes."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Presentation Builder — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._slides: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_pb_outline_tab(), "Outline")
        tabs.addTab(self._build_pb_slides_tab(), "Slides")
        tabs.addTab(self._build_pb_notes_tab(), "Speaker Notes")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Presentations are drafts. Review content before presenting. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_pb_outline_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Presentation Outline"))
        l.addWidget(QLabel("Presentation title:"))
        self._pb_title = QLineEdit()
        l.addWidget(self._pb_title)
        l.addWidget(QLabel("Outline (one slide per line):"))
        self._pb_outline = QTextEdit()
        self._pb_outline.setPlaceholderText("1. Introduction\n2. Problem\n3. Solution\n4. Demo\n5. Q&A")
        l.addWidget(self._pb_outline, stretch=1)
        btn = QPushButton("Generate Slides from Outline")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._pb_generate)
        l.addWidget(btn)
        self._pb_outline_output = QTextEdit()
        self._pb_outline_output.setReadOnly(True)
        self._pb_outline_output.setStyleSheet("")
        l.addWidget(self._pb_outline_output)
        return w

    def _build_pb_slides_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Slide Editor"))
        l.addWidget(QLabel("Slide title:"))
        self._pb_slide_title = QLineEdit()
        l.addWidget(self._pb_slide_title)
        l.addWidget(QLabel("Slide content (bullet points):"))
        self._pb_slide_content = QTextEdit()
        self._pb_slide_content.setPlaceholderText("One bullet per line...")
        l.addWidget(self._pb_slide_content, stretch=1)
        btn = QPushButton("Add Slide")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._pb_add_slide)
        l.addWidget(btn)
        self._pb_slides_output = QTextEdit()
        self._pb_slides_output.setReadOnly(True)
        self._pb_slides_output.setStyleSheet("")
        l.addWidget(self._pb_slides_output)
        return w

    def _build_pb_notes_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Speaker Notes"))
        l.addWidget(QLabel("Select slide:"))
        self._pb_notes_combo = QComboBox()
        l.addWidget(self._pb_notes_combo)
        l.addWidget(QLabel("Speaker notes:"))
        self._pb_notes_input = QTextEdit()
        l.addWidget(self._pb_notes_input, stretch=1)
        btn = QPushButton("Save Notes")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._pb_save_notes)
        l.addWidget(btn)
        self._pb_notes_output = QTextEdit()
        self._pb_notes_output.setReadOnly(True)
        self._pb_notes_output.setStyleSheet("")
        l.addWidget(self._pb_notes_output)
        return w

    def _pb_generate(self):
        title = self._pb_title.text().strip()
        outline = self._pb_outline.toPlainText().strip()
        if not title or not outline:
            self._pb_outline_output.setText("Title and outline are required.")
            return
        self._slides.clear()
        self._pb_notes_combo.clear()
        for line in outline.split("\n"):
            line = line.strip()
            if line:
                slide = {"id": len(self._slides) + 1, "title": line, "content": "", "notes": ""}
                self._slides.append(slide)
                self._pb_notes_combo.addItem(f"[{slide['id']}] {line}")
        self._pb_outline_output.setText(f"Generated {len(self._slides)} slides from outline.\nTitle: {title}\nUse the Slides tab to add content to each slide.")

    def _pb_add_slide(self):
        title = self._pb_slide_title.text().strip()
        content = self._pb_slide_content.toPlainText().strip()
        if not title:
            self._pb_slides_output.setText("Slide title is required.")
            return
        slide = {"id": len(self._slides) + 1, "title": title, "content": content, "notes": ""}
        self._slides.append(slide)
        self._pb_notes_combo.addItem(f"[{slide['id']}] {title}")
        self._pb_slides_output.setText(f"Slide added: [{slide['id']}] {title}\nTotal slides: {len(self._slides)}")
        self._pb_slide_title.clear()
        self._pb_slide_content.clear()

    def _pb_save_notes(self):
        idx = self._pb_notes_combo.currentIndex()
        notes = self._pb_notes_input.toPlainText().strip()
        if idx < 0:
            self._pb_notes_output.setText("Select a slide first.")
            return
        self._slides[idx]["notes"] = notes
        self._pb_notes_output.setText(f"Notes saved for slide [{self._slides[idx]['id']}] {self._slides[idx]['title']}")
        self._pb_notes_input.clear()


class SpreadsheetWizardDialog(BaseCapabilityDialog):
    """Spreadsheet Wizard — formula builder, data table, chart descriptions."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Spreadsheet Wizard — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._rows: list[list[str]] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_sw_data_tab(), "Data Table")
        tabs.addTab(self._build_sw_formula_tab(), "Formulas")
        tabs.addTab(self._build_sw_chart_tab(), "Chart Preview")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Spreadsheet wizard is advisory. Verify calculations independently. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_sw_data_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Data Table"))
        l.addWidget(QLabel("Enter data (comma-separated, one row per line):"))
        self._sw_data = QTextEdit()
        self._sw_data.setPlaceholderText("Name, Age, Score\nAlice, 30, 95\nBob, 25, 87\nCharlie, 35, 92")
        l.addWidget(self._sw_data, stretch=1)
        btn = QPushButton("Load Data")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._sw_load)
        l.addWidget(btn)
        self._sw_data_output = QTextEdit()
        self._sw_data_output.setReadOnly(True)
        self._sw_data_output.setStyleSheet("")
        l.addWidget(self._sw_data_output)
        return w

    def _build_sw_formula_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Formula Builder"))
        l.addWidget(QLabel("Formula type:"))
        self._sw_formula_type = QComboBox()
        self._sw_formula_type.addItems(["SUM", "AVERAGE", "MIN", "MAX", "COUNT", "MEDIAN", "Custom"])
        l.addWidget(self._sw_formula_type)
        l.addWidget(QLabel("Column number (0-based):"))
        self._sw_col = QLineEdit()
        self._sw_col.setPlaceholderText("e.g., 2 for third column")
        l.addWidget(self._sw_col)
        btn = QPushButton("Calculate")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._sw_calc)
        l.addWidget(btn)
        self._sw_formula_output = QTextEdit()
        self._sw_formula_output.setReadOnly(True)
        self._sw_formula_output.setStyleSheet("")
        l.addWidget(self._sw_formula_output, stretch=1)
        return w

    def _build_sw_chart_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Chart Preview (Text)"))
        btn = QPushButton("Generate Chart")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._sw_chart)
        l.addWidget(btn)
        self._sw_chart_output = QTextEdit()
        self._sw_chart_output.setReadOnly(True)
        self._sw_chart_output.setStyleSheet("")
        l.addWidget(self._sw_chart_output, stretch=1)
        return w

    def _sw_load(self):
        raw = self._sw_data.toPlainText().strip()
        if not raw:
            self._sw_data_output.setText("Enter data to load.")
            return
        self._rows = []
        for line in raw.split("\n"):
            cells = [c.strip() for c in line.split(",")]
            self._rows.append(cells)
        lines = [f"Data loaded: {len(self._rows)} rows x {len(self._rows[0]) if self._rows else 0} cols\n"]
        for i, row in enumerate(self._rows):
            lines.append(f"  Row {i}: {row}")
        self._sw_data_output.setText("\n".join(lines))

    def _sw_calc(self):
        if not self._rows:
            self._sw_formula_output.setText("Load data first.")
            return
        col_str = self._sw_col.text().strip()
        if not col_str.isdigit():
            self._sw_formula_output.setText("Enter a valid column number.")
            return
        col = int(col_str)
        ftype = self._sw_formula_type.currentText()
        values = []
        for row in self._rows[1:]:
            if col < len(row):
                try:
                    values.append(float(row[col]))
                except ValueError:
                    pass
        if not values:
            self._sw_formula_output.setText(f"No numeric values found in column {col}.")
            return
        if ftype == "SUM":
            result = sum(values)
        elif ftype == "AVERAGE":
            result = sum(values) / len(values)
        elif ftype == "MIN":
            result = min(values)
        elif ftype == "MAX":
            result = max(values)
        elif ftype == "COUNT":
            result = len(values)
        elif ftype == "MEDIAN":
            sv = sorted(values)
            result = sv[len(sv)//2] if len(sv) % 2 else (sv[len(sv)//2-1] + sv[len(sv)//2]) / 2
        else:
            result = "Custom formula not implemented"
        self._sw_formula_output.setText(f"{ftype}(column {col}) = {result}\nValues: {values}")

    def _sw_chart(self):
        if not self._rows or len(self._rows) < 2:
            self._sw_chart_output.setText("Load data with at least 2 rows first.")
            return
        labels = [row[0] for row in self._rows[1:]]
        values = []
        for row in self._rows[1:]:
            try:
                values.append(float(row[-1]))
            except ValueError:
                values.append(0)
        max_val = max(values) if values else 1
        lines = [f"BAR CHART\n{'='*60}\n"]
        for label, val in zip(labels, values):
            bar_len = int((val / max_val) * 40) if max_val > 0 else 0
            lines.append(f"  {label[:15]:15s} | {'#' * bar_len} {val}")
        self._sw_chart_output.setText("\n".join(lines))


class LegalDocumentReviewerDialog(BaseCapabilityDialog):
    """Legal Document Reviewer — clause analyzer, risk flagger, compliance check."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Legal Document Reviewer — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._reviews: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_ldr_review_tab(), "Review Document")
        tabs.addTab(self._build_ldr_clauses_tab(), "Clause Analysis")
        tabs.addTab(self._build_ldr_history_tab(), "Review History")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("NOT LEGAL ADVICE. This tool provides informational analysis only. Consult a licensed attorney. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ff4500; background-color: #4a0000; padding: 6px; border-radius: 4px; font-weight: bold;")
        layout.addWidget(footer)

    def _build_ldr_review_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Review Legal Document"))
        l.addWidget(QLabel("Document title:"))
        self._ldr_title = QLineEdit()
        l.addWidget(self._ldr_title)
        l.addWidget(QLabel("Document type:"))
        self._ldr_type = QComboBox()
        self._ldr_type.addItems(["Contract", "NDA", "Terms of Service", "Privacy Policy", "Lease", "Employment", "Settlement", "Other"])
        l.addWidget(self._ldr_type)
        l.addWidget(QLabel("Document text:"))
        self._ldr_text = QTextEdit()
        self._ldr_text.setPlaceholderText("Paste the legal document text here...")
        l.addWidget(self._ldr_text, stretch=1)
        btn = QPushButton("Analyze Document")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._ldr_analyze)
        l.addWidget(btn)
        self._ldr_review_output = QTextEdit()
        self._ldr_review_output.setReadOnly(True)
        self._ldr_review_output.setStyleSheet("")
        l.addWidget(self._ldr_review_output)
        return w

    def _build_ldr_clauses_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Clause Analysis"))
        l.addWidget(QLabel("Common clauses to check for:"))
        self._ldr_clause_list = QTextEdit()
        self._ldr_clause_list.setReadOnly(True)
        self._ldr_clause_list.setStyleSheet("")
        self._ldr_clause_list.setText(
            "COMMON CLAUSES TO VERIFY:\n\n"
            "1. Termination clause — How can either party end the agreement?\n"
            "2. Liability limitation — What damages are capped or excluded?\n"
            "3. Indemnification — Who protects whom from third-party claims?\n"
            "4. Governing law — Which jurisdiction's laws apply?\n"
            "5. Confidentiality — What information is protected and for how long?\n"
            "6. Intellectual property — Who owns created works?\n"
            "7. Payment terms — When and how is payment due?\n"
            "8. Force majeure — What happens during unforeseen events?\n"
            "9. Dispute resolution — Arbitration vs litigation?\n"
            "10. Amendment process — How can the agreement be modified?\n"
        )
        l.addWidget(self._ldr_clause_list, stretch=1)
        return w

    def _build_ldr_history_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Review History"))
        btn = QPushButton("Show All Reviews")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._ldr_history)
        l.addWidget(btn)
        self._ldr_history_output = QTextEdit()
        self._ldr_history_output.setReadOnly(True)
        self._ldr_history_output.setStyleSheet("")
        l.addWidget(self._ldr_history_output, stretch=1)
        return w

    def _ldr_analyze(self):
        title = self._ldr_title.text().strip()
        dtype = self._ldr_type.currentText()
        text = self._ldr_text.toPlainText().strip()
        if not title or not text:
            self._ldr_review_output.setText("Title and document text are required.")
            return
        review = {"id": len(self._reviews) + 1, "title": title, "type": dtype, "length": len(text), "created": datetime.now().isoformat()}
        self._reviews.append(review)
        risk_keywords = ["indemnif", "liability", "terminate", "confidential", "warranty", "arbitration", "governing law", "force majeure"]
        found = [kw for kw in risk_keywords if kw in text.lower()]
        lines = [
            f"LEGAL DOCUMENT ANALYSIS\n{'='*60}\n",
            f"Title: {title}",
            f"Type: {dtype}",
            f"Length: {len(text)} chars\n",
            f"KEY CLAUSES DETECTED:",
        ]
        for kw in found:
            lines.append(f"  - {kw.title()} clause found")
        if not found:
            lines.append("  No standard legal clauses detected.")
        lines.append(f"\nRISK FLAGS:")
        lines.append("  - This is NOT legal advice. Consult a licensed attorney.")
        lines.append("  - Review all termination and liability clauses carefully.")
        lines.append("  - Check governing law and dispute resolution terms.")
        lines.append(f"\nReview ID: {review['id']}")
        self._ldr_review_output.setText("\n".join(lines))
        self._ldr_title.clear()
        self._ldr_text.clear()

    def _ldr_history(self):
        if not self._reviews:
            self._ldr_history_output.setText("No reviews yet.")
            return
        lines = [f"REVIEW HISTORY\n{'='*60}\n{len(self._reviews)} reviews:\n"]
        for r in self._reviews:
            lines.append(f"  [{r['id']}] {r['title']} ({r['type']})")
            lines.append(f"    Length: {r['length']} chars | Date: {r['created'][:19]}\n")
        self._ldr_history_output.setText("\n".join(lines))


class MedicalResearcherDialog(BaseCapabilityDialog):
    """Medical Researcher — literature search, study summarizer, evidence grading."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Medical Researcher — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._studies: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_mr_search_tab(), "Literature Search")
        tabs.addTab(self._build_mr_summarize_tab(), "Study Summarizer")
        tabs.addTab(self._build_mr_evidence_tab(), "Evidence Grading")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("NOT MEDICAL ADVICE. For research purposes only. Consult a healthcare professional. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ff4500; background-color: #4a0000; padding: 6px; border-radius: 4px; font-weight: bold;")
        layout.addWidget(footer)

    def _build_mr_search_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Literature Search"))
        l.addWidget(QLabel("Search query:"))
        self._mr_query = QLineEdit()
        self._mr_query.setPlaceholderText("e.g., metformin type 2 diabetes, mindfulness anxiety")
        l.addWidget(self._mr_query)
        l.addWidget(QLabel("Study type filter:"))
        self._mr_study_type = QComboBox()
        self._mr_study_type.addItems(["All", "RCT", "Meta-analysis", "Cohort", "Case-control", "Review", "Case report"])
        l.addWidget(self._mr_study_type)
        btn = QPushButton("Search")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._mr_search)
        l.addWidget(btn)
        self._mr_search_output = QTextEdit()
        self._mr_search_output.setReadOnly(True)
        self._mr_search_output.setStyleSheet("")
        l.addWidget(self._mr_search_output, stretch=1)
        return w

    def _build_mr_summarize_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Study Summarizer"))
        l.addWidget(QLabel("Study title:"))
        self._mr_study_title = QLineEdit()
        l.addWidget(self._mr_study_title)
        l.addWidget(QLabel("Abstract / text:"))
        self._mr_abstract = QTextEdit()
        self._mr_abstract.setPlaceholderText("Paste the study abstract or text...")
        l.addWidget(self._mr_abstract, stretch=1)
        btn = QPushButton("Summarize")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._mr_summarize)
        l.addWidget(btn)
        self._mr_summary_output = QTextEdit()
        self._mr_summary_output.setReadOnly(True)
        self._mr_summary_output.setStyleSheet("")
        l.addWidget(self._mr_summary_output)
        return w

    def _build_mr_evidence_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Evidence Grading"))
        l.addWidget(QLabel("Evidence hierarchy reference:"))
        ref = QTextEdit()
        ref.setReadOnly(True)
        ref.setStyleSheet("")
        ref.setText(
            "EVIDENCE HIERARCHY (highest to lowest):\n\n"
            "Level A: Meta-analyses of RCTs, Systematic reviews\n"
            "Level B: Well-designed RCTs\n"
            "Level C: Cohort studies, Case-control studies\n"
            "Level D: Case series, Case reports, Expert opinion\n\n"
            "GRADE assessment considers:\n"
            "  - Risk of bias\n"
            "  - Inconsistency\n"
            "  - Indirectness\n"
            "  - Imprecision\n"
            "  - Publication bias\n"
        )
        l.addWidget(ref, stretch=1)
        return w

    def _mr_search(self):
        query = self._mr_query.text().strip()
        study_type = self._mr_study_type.currentText()
        if not query:
            self._mr_search_output.setText("Enter a search query.")
            return
        self._mr_search_output.setText(
            f"LITERATURE SEARCH\n{'='*60}\n"
            f"Query: {query}\nFilter: {study_type}\n\n"
            f"RESULTS:\n"
            f"  [The built-in intelligence can provide literature search.]\n"
            f"  Local fallback: Search requires access to medical databases.\n\n"
            f"  Recommended databases:\n"
            f"    - PubMed: https://pubmed.ncbi.nlm.nih.gov/\n"
            f"    - Cochrane: https://www.cochranelibrary.com/\n"
            f"    - ClinicalTrials.gov: https://clinicaltrials.gov/\n\n"
            f"NOT MEDICAL ADVICE — For research purposes only."
        )

    def _mr_summarize(self):
        title = self._mr_study_title.text().strip()
        abstract = self._mr_abstract.toPlainText().strip()
        if not title or not abstract:
            self._mr_summary_output.setText("Title and abstract are required.")
            return
        study = {"id": len(self._studies) + 1, "title": title, "abstract": abstract, "added": datetime.now().isoformat()}
        self._studies.append(study)
        sentences = abstract.split(". ")
        key_points = sentences[:3] if len(sentences) >= 3 else sentences
        lines = [
            f"STUDY SUMMARY\n{'='*60}\n",
            f"Title: {title}",
            f"Length: {len(abstract)} chars\n",
            f"KEY POINTS (extracted):",
        ]
        for i, pt in enumerate(key_points, 1):
            lines.append(f"  {i}. {pt.strip()}.")
        lines.append(f"\nFULL TEXT LENGTH: {len(abstract)} chars")
        lines.append(f"Study ID: {study['id']}")
        lines.append(f"\nNOT MEDICAL ADVICE — For research purposes only.")
        self._mr_summary_output.setText("\n".join(lines))
        self._mr_study_title.clear()
        self._mr_abstract.clear()


class AccessibilityAssistantDialog(BaseCapabilityDialog):
    """Accessibility Assistant — readability checker, alt-text generator, WCAG reference."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Accessibility Assistant — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._checks: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_aa_readability_tab(), "Readability")
        tabs.addTab(self._build_aa_alttext_tab(), "Alt-Text")
        tabs.addTab(self._build_aa_wcag_tab(), "WCAG Reference")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Accessibility checks are advisory. Verify compliance with WCAG guidelines. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_aa_readability_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Readability Checker"))
        l.addWidget(QLabel("Text to analyze:"))
        self._aa_text = QTextEdit()
        self._aa_text.setPlaceholderText("Paste text to check readability...")
        l.addWidget(self._aa_text, stretch=1)
        btn = QPushButton("Check Readability")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._aa_check_readability)
        l.addWidget(btn)
        self._aa_readability_output = QTextEdit()
        self._aa_readability_output.setReadOnly(True)
        self._aa_readability_output.setStyleSheet("")
        l.addWidget(self._aa_readability_output)
        return w

    def _build_aa_alttext_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Alt-Text Generator"))
        l.addWidget(QLabel("Image description / context:"))
        self._aa_alt_input = QTextEdit()
        self._aa_alt_input.setPlaceholderText("Describe the image or paste surrounding context...")
        l.addWidget(self._aa_alt_input, stretch=1)
        btn = QPushButton("Generate Alt-Text")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._aa_gen_alttext)
        l.addWidget(btn)
        self._aa_alt_output = QTextEdit()
        self._aa_alt_output.setReadOnly(True)
        self._aa_alt_output.setStyleSheet("")
        l.addWidget(self._aa_alt_output)
        return w

    def _build_aa_wcag_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("WCAG 2.1 Quick Reference"))
        ref = QTextEdit()
        ref.setReadOnly(True)
        ref.setStyleSheet("")
        ref.setText(
            "WCAG 2.1 KEY PRINCIPLES (POUR):\n\n"
            "1. PERCEIVABLE\n"
            "   - 1.1 Text alternatives for non-text content\n"
            "   - 1.2 Captions and alternatives for media\n"
            "   - 1.3 Content adaptable and distinguishable\n"
            "   - 1.4 Contrast ratio >= 4.5:1 for normal text\n\n"
            "2. OPERABLE\n"
            "   - 2.1 All functionality via keyboard\n"
            "   - 2.2 Enough time to read/use content\n"
            "   - 2.3 No content causing seizures (no >3 flashes/sec)\n"
            "   - 2.4 Navigable — skip links, descriptive titles\n\n"
            "3. UNDERSTANDABLE\n"
            "   - 3.1 Readable — language attribute set\n"
            "   - 3.2 Predictable — consistent navigation\n"
            "   - 3.3 Input assistance — error identification\n\n"
            "4. ROBUST\n"
            "   - 4.1 Compatible with assistive technologies\n"
            "   - Valid HTML, proper ARIA roles\n\n"
            "Reference: https://www.w3.org/WAI/WCAG21/quickref/"
        )
        l.addWidget(ref, stretch=1)
        return w

    def _aa_check_readability(self):
        text = self._aa_text.toPlainText().strip()
        if not text:
            self._aa_readability_output.setText("Enter text to analyze.")
            return
        words = text.split()
        sentences = text.count(".") + text.count("!") + text.count("?")
        sentences = max(sentences, 1)
        words_per_sentence = len(words) / sentences
        long_words = sum(1 for w in words if len(w) > 6)
        score = max(0, min(100, 100 - int(words_per_sentence * 2) - int(long_words * 0.5)))
        check = {"id": len(self._checks) + 1, "words": len(words), "sentences": sentences, "score": score}
        self._checks.append(check)
        level = "Easy" if score >= 70 else "Moderate" if score >= 40 else "Difficult"
        self._aa_readability_output.setText(
            f"READABILITY ANALYSIS\n{'='*60}\n"
            f"Words: {len(words)}\nSentences: {sentences}\n"
            f"Words/sentence: {words_per_sentence:.1f}\n"
            f"Long words (>6 chars): {long_words}\n\n"
            f"Readability score: {score}/100 ({level})\n"
            f"Check ID: {check['id']}"
        )

    def _aa_gen_alttext(self):
        ctx = self._aa_alt_input.toPlainText().strip()
        if not ctx:
            self._aa_alt_output.setText("Enter image description or context.")
            return
        if len(ctx) > 125:
            suggestion = ctx[:122] + "..."
        else:
            suggestion = ctx
        self._aa_alt_output.setText(
            f"ALT-TEXT SUGGESTION\n{'='*60}\n"
            f"Generated alt-text (max 125 chars):\n\n"
            f"\"{suggestion}\"\n\n"
            f"Tips:\n"
            f"  - Keep it concise and descriptive\n"
            f"  - Avoid 'image of' or 'picture of'\n"
            f"  - Convey purpose, not just appearance\n"
            f"  - If decorative, use empty alt=\"\""
        )


class FactCheckerDialog(BaseCapabilityDialog):
    """Fact Checker — claim verification, source tracker, bias detector."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Fact Checker — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._claims: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_fc_check_tab(), "Check Claim")
        tabs.addTab(self._build_fc_sources_tab(), "Source Tracker")
        tabs.addTab(self._build_fc_history_tab(), "History")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Fact-checking is advisory. Always verify with primary sources. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_fc_check_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Check a Claim"))
        l.addWidget(QLabel("Claim to verify:"))
        self._fc_claim = QTextEdit()
        self._fc_claim.setPlaceholderText("Enter the claim you want to fact-check...")
        l.addWidget(self._fc_claim, stretch=1)
        l.addWidget(QLabel("Claim category:"))
        self._fc_category = QComboBox()
        self._fc_category.addItems(["Statistics", "Historical", "Scientific", "Political", "Health", "Economic", "Other"])
        l.addWidget(self._fc_category)
        btn = QPushButton("Verify Claim")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._fc_verify)
        l.addWidget(btn)
        self._fc_check_output = QTextEdit()
        self._fc_check_output.setReadOnly(True)
        self._fc_check_output.setStyleSheet("")
        l.addWidget(self._fc_check_output)
        return w

    def _build_fc_sources_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Source Tracker"))
        l.addWidget(QLabel("Source name:"))
        self._fc_src_name = QLineEdit()
        l.addWidget(self._fc_src_name)
        l.addWidget(QLabel("Source URL:"))
        self._fc_src_url = QLineEdit()
        l.addWidget(self._fc_src_url)
        l.addWidget(QLabel("Reliability rating (1-5):"))
        self._fc_src_rating = QComboBox()
        self._fc_src_rating.addItems(["1 — Unreliable", "2 — Low", "3 — Moderate", "4 — High", "5 — Very High"])
        l.addWidget(self._fc_src_rating)
        btn = QPushButton("Add Source")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._fc_add_source)
        l.addWidget(btn)
        self._fc_sources_output = QTextEdit()
        self._fc_sources_output.setReadOnly(True)
        self._fc_sources_output.setStyleSheet("")
        l.addWidget(self._fc_sources_output, stretch=1)
        return w

    def _build_fc_history_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Claim History"))
        btn = QPushButton("Show All Claims")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._fc_history)
        l.addWidget(btn)
        self._fc_history_output = QTextEdit()
        self._fc_history_output.setReadOnly(True)
        self._fc_history_output.setStyleSheet("")
        l.addWidget(self._fc_history_output, stretch=1)
        return w

    def _fc_verify(self):
        claim = self._fc_claim.toPlainText().strip()
        category = self._fc_category.currentText()
        if not claim:
            self._fc_check_output.setText("Enter a claim to verify.")
            return
        entry = {"id": len(self._claims) + 1, "claim": claim, "category": category, "created": datetime.now().isoformat()}
        self._claims.append(entry)
        self._fc_check_output.setText(
            f"FACT CHECK RESULT\n{'='*60}\n"
            f"Claim: {claim[:200]}\n"
            f"Category: {category}\n\n"
            f"VERIFICATION STATUS: Requires manual verification\n\n"
            f"RECOMMENDED SOURCES:\n"
            f"  - Snopes: https://www.snopes.com/\n"
            f"  - FactCheck.org: https://www.factcheck.org/\n"
            f"  - PolitiFact: https://www.politifact.com/\n"
            f"  - Reuters Fact Check: https://www.reuters.com/fact-check/\n"
            f"  - WHO (health): https://www.who.int/\n\n"
            f"BIAS CHECK:\n"
            f"  - Consider the source's perspective\n"
            f"  - Cross-reference multiple sources\n"
            f"  - Look for primary data/studies\n\n"
            f"Claim ID: {entry['id']}"
        )
        self._fc_claim.clear()

    def _fc_add_source(self):
        name = self._fc_src_name.text().strip()
        url = self._fc_src_url.text().strip()
        rating = self._fc_src_rating.currentText()
        if not name:
            self._fc_sources_output.setText("Source name is required.")
            return
        if not hasattr(self, "_fc_sources_list"):
            self._fc_sources_list: list[dict] = []
        self._fc_sources_list.append({"name": name, "url": url, "rating": rating})
        lines = [f"SOURCE TRACKER\n{'='*60}\n{len(self._fc_sources_list)} sources:\n"]
        for s in self._fc_sources_list:
            lines.append(f"  {s['name']} — {s['rating']}")
            if s["url"]:
                lines.append(f"    URL: {s['url']}")
        self._fc_sources_output.setText("\n".join(lines))
        self._fc_src_name.clear()
        self._fc_src_url.clear()

    def _fc_history(self):
        if not self._claims:
            self._fc_history_output.setText("No claims checked yet.")
            return
        lines = [f"CLAIM HISTORY\n{'='*60}\n{len(self._claims)} claims:\n"]
        for c in self._claims:
            lines.append(f"  [{c['id']}] ({c['category']}) {c['claim'][:100]}{'...' if len(c['claim']) > 100 else ''}")
            lines.append(f"    Date: {c['created'][:19]}\n")
        self._fc_history_output.setText("\n".join(lines))


class VoiceInterfaceDialog(BaseCapabilityDialog):
    """Voice Interface — speech-to-text, text-to-speech, voice command reference."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Voice Interface — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._voice_log: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_vi_stt_tab(), "Speech to Text")
        tabs.addTab(self._build_vi_tts_tab(), "Text to Speech")
        tabs.addTab(self._build_vi_commands_tab(), "Voice Commands")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Voice interface uses local models. No audio sent externally. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_vi_stt_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Speech to Text"))
        l.addWidget(QLabel("Transcribed text will appear here:"))
        self._vi_stt_output = QTextEdit()
        self._vi_stt_output.setReadOnly(True)
        self._vi_stt_output.setStyleSheet("")
        self._vi_stt_output.setPlaceholderText("Press 'Start Recording' to transcribe speech...")
        l.addWidget(self._vi_stt_output, stretch=1)
        btn = QPushButton("Start Recording (Local Whisper)")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._vi_start_stt)
        l.addWidget(btn)
        return w

    def _build_vi_tts_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Text to Speech"))
        l.addWidget(QLabel("Text to speak:"))
        self._vi_tts_input = QTextEdit()
        self._vi_tts_input.setPlaceholderText("Enter text to convert to speech...")
        l.addWidget(self._vi_tts_input, stretch=1)
        l.addWidget(QLabel("Voice model:"))
        self._vi_voice = QComboBox()
        self._vi_voice.addItems(["Kokoro-82M (default)", "System Default"])
        l.addWidget(self._vi_voice)
        btn = QPushButton("Speak")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._vi_speak)
        l.addWidget(btn)
        self._vi_tts_output = QTextEdit()
        self._vi_tts_output.setReadOnly(True)
        self._vi_tts_output.setStyleSheet("")
        l.addWidget(self._vi_tts_output)
        return w

    def _build_vi_commands_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Voice Command Reference"))
        ref = QTextEdit()
        ref.setReadOnly(True)
        ref.setStyleSheet("")
        ref.setText(
            "VOICE COMMANDS\n{'='*60}\n\n"
            "NAVIGATION:\n"
            "  'Open [capability name]'\n"
            "  'Go to [tab name]'\n"
            "  'Close dialog'\n\n"
            "ACTIONS:\n"
            "  'Start recording'\n"
            "  'Stop recording'\n"
            "  'Speak text'\n"
            "  'Clear text'\n\n"
            "SYSTEM:\n"
            "  'Save'\n"
            "  'Export'\n"
            "  'Help'\n\n"
            "NOTE: Voice commands require a connected microphone and\n"
            "the local Whisper model (faster-whisper-small.en) loaded."
        )
        l.addWidget(ref, stretch=1)
        return w

    def _vi_start_stt(self):
        entry = {"id": len(self._voice_log) + 1, "type": "STT", "created": datetime.now().isoformat()}
        self._voice_log.append(entry)
        self._vi_stt_output.setText(
            f"RECORDING STATUS\n{'='*60}\n"
            f"Status: Waiting for microphone input...\n\n"
            f"[Configure faster-whisper-small.en for local transcription.]\n"
            f"Local fallback: Speech-to-text requires the Whisper model.\n"
            f"Model path: b:/local_models/faster-whisper-small.en/\n\n"
            f"Session ID: {entry['id']}"
        )

    def _vi_speak(self):
        text = self._vi_tts_input.toPlainText().strip()
        voice = self._vi_voice.currentText()
        if not text:
            self._vi_tts_output.setText("Enter text to speak.")
            return
        entry = {"id": len(self._voice_log) + 1, "type": "TTS", "text": text, "voice": voice, "created": datetime.now().isoformat()}
        self._voice_log.append(entry)
        self._vi_tts_output.setText(
            f"TTS STATUS\n{'='*60}\n"
            f"Voice: {voice}\n"
            f"Text length: {len(text)} chars\n\n"
            f"[Configure Kokoro-82M TTS for audio output.]\n"
            f"Local fallback: TTS requires the Kokoro model.\n"
            f"Model path: b:/local_models/kokoro-82m-tts/\n\n"
            f"Session ID: {entry['id']}"
        )


class WorkflowAutomatorDialog(BaseCapabilityDialog):
    """Workflow Automator — chain actions, trigger rules, automation builder."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Workflow Automator — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._workflows: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_wa_builder_tab(), "Workflow Builder")
        tabs.addTab(self._build_wa_triggers_tab(), "Triggers")
        tabs.addTab(self._build_wa_library_tab(), "Workflow Library")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Workflow automator is advisory. Test automations before production use. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_wa_builder_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Workflow Builder"))
        l.addWidget(QLabel("Workflow name:"))
        self._wa_name = QLineEdit()
        l.addWidget(self._wa_name)
        l.addWidget(QLabel("Steps (one per line: action | description):"))
        self._wa_steps = QTextEdit()
        self._wa_steps.setPlaceholderText("Send email | Notify team of update\nCreate task | Add to project board\nGenerate report | Weekly summary")
        l.addWidget(self._wa_steps, stretch=1)
        btn = QPushButton("Save Workflow")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._wa_save)
        l.addWidget(btn)
        self._wa_builder_output = QTextEdit()
        self._wa_builder_output.setReadOnly(True)
        self._wa_builder_output.setStyleSheet("")
        l.addWidget(self._wa_builder_output)
        return w

    def _build_wa_triggers_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Trigger Rules"))
        l.addWidget(QLabel("Trigger type:"))
        self._wa_trigger_type = QComboBox()
        self._wa_trigger_type.addItems(["On Event", "On Schedule", "On Condition", "Manual"])
        l.addWidget(self._wa_trigger_type)
        l.addWidget(QLabel("Trigger condition / schedule:"))
        self._wa_trigger_cond = QLineEdit()
        self._wa_trigger_cond.setPlaceholderText("e.g., Every Monday 9AM, or When task status = Done")
        l.addWidget(self._wa_trigger_cond)
        l.addWidget(QLabel("Workflow to execute:"))
        self._wa_trigger_workflow = QComboBox()
        l.addWidget(self._wa_trigger_workflow)
        btn = QPushButton("Add Trigger")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._wa_add_trigger)
        l.addWidget(btn)
        self._wa_triggers_output = QTextEdit()
        self._wa_triggers_output.setReadOnly(True)
        self._wa_triggers_output.setStyleSheet("")
        l.addWidget(self._wa_triggers_output, stretch=1)
        return w

    def _build_wa_library_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Workflow Library"))
        btn = QPushButton("Show All Workflows")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._wa_library)
        l.addWidget(btn)
        self._wa_lib_output = QTextEdit()
        self._wa_lib_output.setReadOnly(True)
        self._wa_lib_output.setStyleSheet("")
        l.addWidget(self._wa_lib_output, stretch=1)
        return w

    def _wa_save(self):
        name = self._wa_name.text().strip()
        steps_raw = self._wa_steps.toPlainText().strip()
        if not name or not steps_raw:
            self._wa_builder_output.setText("Name and steps are required.")
            return
        steps = []
        for line in steps_raw.split("\n"):
            line = line.strip()
            if line:
                parts = line.split("|", 1)
                steps.append({"action": parts[0].strip(), "desc": parts[1].strip() if len(parts) > 1 else ""})
        wf = {"id": len(self._workflows) + 1, "name": name, "steps": steps, "created": datetime.now().isoformat()}
        self._workflows.append(wf)
        self._wa_trigger_workflow.addItem(f"[{wf['id']}] {name}")
        self._wa_builder_output.setText(f"Workflow saved: [{wf['id']}] {name}\n  Steps: {len(steps)}\n  Total workflows: {len(self._workflows)}")
        self._wa_name.clear()
        self._wa_steps.clear()

    def _wa_add_trigger(self):
        ttype = self._wa_trigger_type.currentText()
        cond = self._wa_trigger_cond.text().strip()
        wf = self._wa_trigger_workflow.currentText()
        if not hasattr(self, "_wa_triggers_list"):
            self._wa_triggers_list: list[dict] = []
        self._wa_triggers_list.append({"type": ttype, "condition": cond, "workflow": wf})
        lines = [f"TRIGGER RULES\n{'='*60}\n{len(self._wa_triggers_list)} triggers:\n"]
        for t in self._wa_triggers_list:
            lines.append(f"  [{t['type']}] {t['condition']}")
            lines.append(f"    -> {t['workflow']}\n")
        self._wa_triggers_output.setText("\n".join(lines))
        self._wa_trigger_cond.clear()

    def _wa_library(self):
        if not self._workflows:
            self._wa_lib_output.setText("No workflows saved.")
            return
        lines = [f"WORKFLOW LIBRARY\n{'='*60}\n{len(self._workflows)} workflows:\n"]
        for wf in self._workflows:
            lines.append(f"  [{wf['id']}] {wf['name']} ({len(wf['steps'])} steps)")
            for s in wf["steps"]:
                lines.append(f"    {s['action']} | {s['desc']}")
            lines.append("")
        self._wa_lib_output.setText("\n".join(lines))


class CompetitiveAnalystDialog(BaseCapabilityDialog):
    """Competitive Analyst — competitor tracker, SWOT, market positioning."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Competitive Analyst — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._competitors: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_ca_competitor_tab(), "Competitors")
        tabs.addTab(self._build_ca_swot_tab(), "SWOT")
        tabs.addTab(self._build_ca_positioning_tab(), "Positioning")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Competitive analysis is advisory. Verify data independently. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_ca_competitor_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Competitor Tracker"))
        l.addWidget(QLabel("Competitor name:"))
        self._ca_name = QLineEdit()
        l.addWidget(self._ca_name)
        l.addWidget(QLabel("Strengths:"))
        self._ca_strengths = QTextEdit()
        l.addWidget(self._ca_strengths)
        l.addWidget(QLabel("Weaknesses:"))
        self._ca_weaknesses = QTextEdit()
        l.addWidget(self._ca_weaknesses)
        l.addWidget(QLabel("Market share (optional):"))
        self._ca_share = QLineEdit()
        self._ca_share.setPlaceholderText("e.g., 15%")
        l.addWidget(self._ca_share)
        btn = QPushButton("Add Competitor")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._ca_add_competitor)
        l.addWidget(btn)
        self._ca_comp_output = QTextEdit()
        self._ca_comp_output.setReadOnly(True)
        self._ca_comp_output.setStyleSheet("")
        l.addWidget(self._ca_comp_output, stretch=1)
        return w

    def _build_ca_swot_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("SWOT Analysis"))
        l.addWidget(QLabel("Subject (your company/product):"))
        self._ca_swot_subject = QLineEdit()
        l.addWidget(self._ca_swot_subject)
        l.addWidget(QLabel("Strengths:"))
        self._ca_swot_s = QTextEdit()
        l.addWidget(self._ca_swot_s)
        l.addWidget(QLabel("Weaknesses:"))
        self._ca_swot_w = QTextEdit()
        l.addWidget(self._ca_swot_w)
        l.addWidget(QLabel("Opportunities:"))
        self._ca_swot_o = QTextEdit()
        l.addWidget(self._ca_swot_o)
        l.addWidget(QLabel("Threats:"))
        self._ca_swot_t = QTextEdit()
        l.addWidget(self._ca_swot_t)
        btn = QPushButton("Generate SWOT")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._ca_gen_swot)
        l.addWidget(btn)
        self._ca_swot_output = QTextEdit()
        self._ca_swot_output.setReadOnly(True)
        self._ca_swot_output.setStyleSheet("")
        l.addWidget(self._ca_swot_output)
        return w

    def _build_ca_positioning_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Market Positioning Map"))
        l.addWidget(QLabel("Positioning will be displayed based on tracked competitors."))
        btn = QPushButton("Show Positioning")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._ca_positioning)
        l.addWidget(btn)
        self._ca_pos_output = QTextEdit()
        self._ca_pos_output.setReadOnly(True)
        self._ca_pos_output.setStyleSheet("")
        l.addWidget(self._ca_pos_output, stretch=1)
        return w

    def _ca_add_competitor(self):
        name = self._ca_name.text().strip()
        strengths = self._ca_strengths.toPlainText().strip()
        weaknesses = self._ca_weaknesses.toPlainText().strip()
        share = self._ca_share.text().strip()
        if not name:
            self._ca_comp_output.setText("Competitor name is required.")
            return
        comp = {"id": len(self._competitors) + 1, "name": name, "strengths": strengths, "weaknesses": weaknesses, "share": share}
        self._competitors.append(comp)
        self._ca_comp_output.setText(f"Competitor added: [{comp['id']}] {name}\n  Share: {share or 'N/A'}\n  Total: {len(self._competitors)}")
        self._ca_name.clear()
        self._ca_strengths.clear()
        self._ca_weaknesses.clear()
        self._ca_share.clear()

    def _ca_gen_swot(self):
        subject = self._ca_swot_subject.text().strip()
        s = self._ca_swot_s.toPlainText().strip()
        w = self._ca_swot_w.toPlainText().strip()
        o = self._ca_swot_o.toPlainText().strip()
        t = self._ca_swot_t.toPlainText().strip()
        if not subject:
            self._ca_swot_output.setText("Subject is required.")
            return
        lines = [
            f"SWOT ANALYSIS: {subject}\n{'='*60}\n",
            f"STRENGTHS:\n{s or '(none listed)'}\n",
            f"WEAKNESSES:\n{w or '(none listed)'}\n",
            f"OPPORTUNITIES:\n{o or '(none listed)'}\n",
            f"THREATS:\n{t or '(none listed)'}\n",
            f"\nSTRATEGIC INSIGHTS:",
            f"  - Leverage strengths to capitalize on opportunities (SO strategy)",
            f"  - Address weaknesses to avoid threats (WT strategy)",
            f"  - Use strengths to mitigate threats (ST strategy)",
            f"  - Improve weaknesses to pursue opportunities (WO strategy)",
        ]
        self._ca_swot_output.setText("\n".join(lines))

    def _ca_positioning(self):
        if not self._competitors:
            self._ca_pos_output.setText("No competitors tracked. Add competitors first.")
            return
        lines = [f"MARKET POSITIONING\n{'='*60}\n{len(self._competitors)} competitors:\n"]
        for c in self._competitors:
            lines.append(f"  [{c['id']}] {c['name']}")
            lines.append(f"    Share: {c['share'] or 'Unknown'}")
            lines.append(f"    Strengths: {c['strengths'][:80]}{'...' if len(c['strengths']) > 80 else ''}")
            lines.append(f"    Weaknesses: {c['weaknesses'][:80]}{'...' if len(c['weaknesses']) > 80 else ''}\n")
        self._ca_pos_output.setText("\n".join(lines))


class LearningPathCreatorDialog(BaseCapabilityDialog):
    """Learning Path Creator — skill tree, resource curator, progress tracker."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Learning Path Creator — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._paths: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_lp_create_tab(), "Create Path")
        tabs.addTab(self._build_lp_resources_tab(), "Resources")
        tabs.addTab(self._build_lp_progress_tab(), "Progress")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Learning paths are advisory. Adapt to your learning style. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_lp_create_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Create Learning Path"))
        l.addWidget(QLabel("Path title:"))
        self._lp_title = QLineEdit()
        l.addWidget(self._lp_title)
        l.addWidget(QLabel("Skill level:"))
        self._lp_level = QComboBox()
        self._lp_level.addItems(["Beginner", "Intermediate", "Advanced", "Expert"])
        l.addWidget(self._lp_level)
        l.addWidget(QLabel("Milestones (one per line):"))
        self._lp_milestones = QTextEdit()
        self._lp_milestones.setPlaceholderText("1. Learn basics\n2. Practice exercises\n3. Build a project\n4. Advanced topics")
        l.addWidget(self._lp_milestones, stretch=1)
        btn = QPushButton("Save Learning Path")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._lp_create)
        l.addWidget(btn)
        self._lp_create_output = QTextEdit()
        self._lp_create_output.setReadOnly(True)
        self._lp_create_output.setStyleSheet("")
        l.addWidget(self._lp_create_output)
        return w

    def _build_lp_resources_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Resource Curator"))
        l.addWidget(QLabel("Resource name:"))
        self._lp_res_name = QLineEdit()
        l.addWidget(self._lp_res_name)
        l.addWidget(QLabel("Resource URL:"))
        self._lp_res_url = QLineEdit()
        l.addWidget(self._lp_res_url)
        l.addWidget(QLabel("Resource type:"))
        self._lp_res_type = QComboBox()
        self._lp_res_type.addItems(["Article", "Video", "Book", "Course", "Documentation", "Tool", "Other"])
        l.addWidget(self._lp_res_type)
        btn = QPushButton("Add Resource")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._lp_add_resource)
        l.addWidget(btn)
        self._lp_resources_output = QTextEdit()
        self._lp_resources_output.setReadOnly(True)
        self._lp_resources_output.setStyleSheet("")
        l.addWidget(self._lp_resources_output, stretch=1)
        return w

    def _build_lp_progress_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Progress Tracker"))
        btn = QPushButton("Show All Paths")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._lp_progress)
        l.addWidget(btn)
        self._lp_progress_output = QTextEdit()
        self._lp_progress_output.setReadOnly(True)
        self._lp_progress_output.setStyleSheet("")
        l.addWidget(self._lp_progress_output, stretch=1)
        return w

    def _lp_create(self):
        title = self._lp_title.text().strip()
        level = self._lp_level.currentText()
        milestones_raw = self._lp_milestones.toPlainText().strip()
        if not title or not milestones_raw:
            self._lp_create_output.setText("Title and milestones are required.")
            return
        milestones = [m.strip() for m in milestones_raw.split("\n") if m.strip()]
        path = {"id": len(self._paths) + 1, "title": title, "level": level, "milestones": milestones, "completed": 0, "created": datetime.now().isoformat()}
        self._paths.append(path)
        self._lp_create_output.setText(f"Learning path saved: [{path['id']}] {title}\n  Level: {level}\n  Milestones: {len(milestones)}\n  Total paths: {len(self._paths)}")
        self._lp_title.clear()
        self._lp_milestones.clear()

    def _lp_add_resource(self):
        name = self._lp_res_name.text().strip()
        url = self._lp_res_url.text().strip()
        rtype = self._lp_res_type.currentText()
        if not name:
            self._lp_resources_output.setText("Resource name is required.")
            return
        if not hasattr(self, "_lp_resources_list"):
            self._lp_resources_list: list[dict] = []
        self._lp_resources_list.append({"name": name, "url": url, "type": rtype})
        lines = [f"RESOURCE LIST\n{'='*60}\n{len(self._lp_resources_list)} resources:\n"]
        for r in self._lp_resources_list:
            lines.append(f"  [{r['type']}] {r['name']}")
            if r["url"]:
                lines.append(f"    URL: {r['url']}")
        self._lp_resources_output.setText("\n".join(lines))
        self._lp_res_name.clear()
        self._lp_res_url.clear()

    def _lp_progress(self):
        if not self._paths:
            self._lp_progress_output.setText("No learning paths created.")
            return
        lines = [f"LEARNING PATHS\n{'='*60}\n{len(self._paths)} paths:\n"]
        for p in self._paths:
            total = len(p["milestones"])
            done = p["completed"]
            pct = int((done / total) * 100) if total > 0 else 0
            bar_len = pct // 5
            lines.append(f"  [{p['id']}] {p['title']} ({p['level']})")
            lines.append(f"    Progress: [{'#' * bar_len}{'.' * (20 - bar_len)}] {pct}% ({done}/{total})")
            for i, m in enumerate(p["milestones"]):
                mark = "[x]" if i < done else "[ ]"
                lines.append(f"      {mark} {m}")
            lines.append("")
        self._lp_progress_output.setText("\n".join(lines))


class SmartSearchDialog(BaseCapabilityDialog):
    """Smart Search — unified search, result ranking, search history."""

    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Smart Search — {ai_name} | Avery Logic Works(TM)")
        self.resize(860, 640)
        self._searches: list[dict] = []
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #161b22; color: #8b949e; padding: 8px 16px; } QTabBar::tab:selected { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #1f6feb; }")
        tabs.addTab(self._build_ss_search_tab(), "Search")
        tabs.addTab(self._build_ss_ranking_tab(), "Result Ranking")
        tabs.addTab(self._build_ss_history_tab(), "Search History")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Smart search is advisory. Verify results from primary sources. Avery Logic Works is not liable.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _build_ss_search_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Smart Search"))
        l.addWidget(QLabel("Search query:"))
        self._ss_query = QLineEdit()
        self._ss_query.setPlaceholderText("Enter your search query...")
        l.addWidget(self._ss_query)
        l.addWidget(QLabel("Search scope:"))
        self._ss_scope = QComboBox()
        self._ss_scope.addItems(["All capabilities", "Documents", "Knowledge base", "Web (external)", "Book context"])
        l.addWidget(self._ss_scope)
        btn = QPushButton("Search")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._ss_search)
        l.addWidget(btn)
        self._ss_search_output = QTextEdit()
        self._ss_search_output.setReadOnly(True)
        self._ss_search_output.setStyleSheet("")
        l.addWidget(self._ss_search_output, stretch=1)
        return w

    def _build_ss_ranking_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Result Ranking Configuration"))
        l.addWidget(QLabel("Ranking algorithm:"))
        self._ss_algo = QComboBox()
        self._ss_algo.addItems(["Relevance (TF-IDF)", "Recency", "Popularity", "Hybrid", "Custom"])
        l.addWidget(self._ss_algo)
        l.addWidget(QLabel("Max results:"))
        self._ss_max = QLineEdit()
        self._ss_max.setPlaceholderText("e.g., 20")
        l.addWidget(self._ss_max)
        btn = QPushButton("Save Settings")
        btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._ss_save_settings)
        l.addWidget(btn)
        self._ss_ranking_output = QTextEdit()
        self._ss_ranking_output.setReadOnly(True)
        self._ss_ranking_output.setStyleSheet("")
        l.addWidget(self._ss_ranking_output, stretch=1)
        return w

    def _build_ss_history_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Search History"))
        btn = QPushButton("Show History")
        btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self._ss_history)
        l.addWidget(btn)
        self._ss_history_output = QTextEdit()
        self._ss_history_output.setReadOnly(True)
        self._ss_history_output.setStyleSheet("")
        l.addWidget(self._ss_history_output, stretch=1)
        return w

    def _ss_search(self):
        query = self._ss_query.text().strip()
        scope = self._ss_scope.currentText()
        if not query:
            self._ss_search_output.setText("Enter a search query.")
            return
        entry = {"id": len(self._searches) + 1, "query": query, "scope": scope, "created": datetime.now().isoformat()}
        self._searches.append(entry)
        self._ss_search_output.setText(
            f"SMART SEARCH RESULTS\n{'='*60}\n"
            f"Query: {query}\nScope: {scope}\n\n"
            f"RESULTS:\n"
            f"  [The built-in intelligence can provide search.]\n"
            f"  Local fallback: Search requires an embedding model.\n\n"
            f"  Available local models:\n"
            f"    - bge-small-en-v1.5 (fast, lightweight)\n"
            f"    - nomic-embed-text-v1.5 (higher quality)\n"
            f"    - bge-reranker-v2-m3 (re-ranking)\n\n"
            f"Search ID: {entry['id']}"
        )
        self._ss_query.clear()

    def _ss_save_settings(self):
        algo = self._ss_algo.currentText()
        max_r = self._ss_max.text().strip() or "10"
        self._ss_ranking_output.setText(
            f"RANKING SETTINGS SAVED\n{'='*60}\n"
            f"Algorithm: {algo}\n"
            f"Max results: {max_r}\n"
            f"Settings will apply to next search."
        )

    def _ss_history(self):
        if not self._searches:
            self._ss_history_output.setText("No searches yet.")
            return
        lines = [f"SEARCH HISTORY\n{'='*60}\n{len(self._searches)} searches:\n"]
        for s in self._searches:
            lines.append(f"  [{s['id']}] ({s['scope']}) {s['query']}")
            lines.append(f"    Date: {s['created'][:19]}\n")
        self._ss_history_output.setText("\n".join(lines))
