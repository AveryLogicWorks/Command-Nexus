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


ALL_USE_CASES = ["Individual", "Educational", "Task-Ready", "Business", "Enterprise", "All-Rounder"]


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
        ["Route requests to selected capabilities instead of pretending unsupported powers exist.", "Return safe stub status to chat when a backend is not connected."],
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
        ["Route requests to selected capabilities instead of pretending unsupported powers exist.", "Return safe stub status to chat when a backend is not connected."],
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
        "Live browser/search automation only after network approval and backend connection.",
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
        "Local memory persistence works now; cloud sync and sharing require approval and backend connection.",
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

    "Legal Assistant": _action(
        "cap.legal", "Legal Assistant",
        "Legal document analysis, contract review, clause identification, risk flagging, and compliance checking.",
        "Legal workspace with document upload, clause extraction, risk analysis, compliance checklist, and redline suggestions.",
        "Court filing integration, legal research databases, e-discovery support, and client communication automation.",
        ["legal_database", "court_integration", "client_communication"], "High",
        ["Business", "Enterprise", "All-Rounder"],
        ["Document Processor", "Research", "Business Workflow", "Archive"],
        ["This is NOT a substitute for a licensed attorney.", "Flag all legal risks clearly.", "Maintain attorney-client privilege."],
        ["Document Upload", "Clause Analysis", "Risk Flags", "Compliance Check"],
        ["Legal Research Library", "Compliance Library", "Risk Assessment Library"],
        ["Review this contract for risks", "Find the termination clauses", "Check compliance with GDPR"],
        "Document analysis and risk identification work now; legal database access and court integration require approval.",
        "LegalAssistantDialog", "Open Legal Assistant",
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
    "Contract Reviewer": "Legal Assistant",
    "Compliance Checker": "Legal Assistant",
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
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px; background-color: #161b22; border: 1px solid #30363d;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        split = QSplitter(Qt.Orientation.Horizontal)
        chat_panel = QWidget()
        chat_layout = QVBoxLayout(chat_panel)
        self._transcript = QTextEdit()
        self._transcript.setReadOnly(True)
        self._transcript.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
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
        context_box.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
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
        msg = self._input.text().strip()
        if not msg:
            return
        self._append_user(msg)
        self._approval_banner.setVisible(False)
        msg_l = msg.lower()
        canonicals = {_canonical_ability(c) for c in self._abilities}

        # Build a context-aware prompt and call the model backend.
        book_ctx = (
            f"You are {self._ai_name}, a Command Nexus governed AI.\n"
            f"Use case: {self._use_case}\n"
            f"Abilities: {', '.join(self._abilities) or 'general assistance'}\n"
            f"Libraries: {', '.join(self._libraries) if self._libraries else 'None'}\n"
            f"Guardrails: {', '.join(self._guardrails) if self._guardrails else 'None'}\n\n"
            f"Quickstart: {self._book_context.get('quickstart', 'Ask me anything.')}\n\n"
            f"User message: {msg}\n\n"
            "Respond helpfully based on your capabilities. "
            "Do not claim external actions were performed unless a tool actually performed them. "
            "If a capability is not active, you can mention you know about it but cannot use it."
        )

        try:
            settings = SettingsManager()
            settings.initialize()
            backend = BackendManager(settings)
            response = backend.call_model(book_ctx)
        except Exception as e:
            response = BackendResponse(error=f"Backend unavailable: {e}")

        if response.error:
            self._append_ai(
                f"I'm here, but my model backend is offline or unavailable.\n\n"
                f"Provider: {response.display_name or response.provider_id or 'selected backend'}\n"
                f"Error: {response.error}\n\n"
                "Start the selected backend, choose a different backend, or configure Backend settings."
            )
            # Still provide capability routing hints so the user knows what's available.
            reply_parts: list[str] = []
            if "Research" in canonicals and any(k in msg_l for k in ["research", "find", "search", "compare", "source", "cite"]):
                reply_parts.append("[Research capability is attached but backend is offline. Use the Research workflow for local briefs.]")
            if "Coder" in canonicals and any(k in msg_l for k in ["code", "function", "bug", "fix", "test", "diff", "patch"]):
                reply_parts.append("[Coding capability is attached but backend is offline. Use the Coding workflow for local scaffolding.]")
            if "Creative Writing" in canonicals and any(k in msg_l for k in ["write", "draft", "story", "scene", "outline", "tone", "polish"]):
                reply_parts.append("[Writing capability is attached but backend is offline. Use the Writing workflow for local drafts.]")
            if reply_parts:
                self._append_ai(" ".join(reply_parts))
            self._input.clear()
            return

        if response.text:
            self._append_ai(response.text)
        else:
            self._append_ai("I received your message but the model returned an empty response. Please try rephrasing.")

        self._input.clear()

    def _append_user(self, text: str):
        self._transcript.append(f"<b>You:</b> {text}")

    def _append_ai(self, text: str):
        self._transcript.append(f"<b>{self._ai_name}:</b> {text}")

    def _open_action_dialog(self, dialog_class_name: str, label: str):
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
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px; background-color: #161b22; border: 1px solid #30363d;")
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
        self._code_output.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
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
                "(Simulated explanation — backend not connected.)"
            )
            self._set_result_summary("Code explanation prepared locally. No file changes or commands were run.")
        elif action == "diff":
            self._code_output.setText(
                f"[DIFF for: {prompt[:80]}...]\n\n"
                "```diff\n- old_line\n+ new_line\n```\n\n"
                "Review the diff above. If you approve, the changes can be applied to the planned files.\n"
                "(Simulated diff — backend not connected.)"
            )
            self._set_result_summary("Diff preview prepared in show-code-only mode. Approved file editing is still a safe stub.")
        elif action == "test":
            self._code_output.setText(
                f"[TEST OUTLINE for: {prompt[:80]}...]\n\n"
                "1. Unit test: happy path\n"
                "2. Unit test: error handling\n"
                "3. Integration test: end-to-end flow\n"
                "4. Edge cases: empty input, max bounds, concurrency\n\n"
                "(Simulated test outline — backend not connected.)"
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
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px; background-color: #161b22; border: 1px solid #30363d;")
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
        self._findings.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
        fvl.addWidget(self._findings)
        sp.addWidget(fw)
        sw = QWidget()
        svl = QVBoxLayout(sw)
        svl.addWidget(QLabel("Sources & Citations:"))
        self._sources = QTextEdit()
        self._sources.setReadOnly(True)
        self._sources.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
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
                "(Simulated comparison — backend not connected.)"
            )
            self._sources.setText("[SOURCES]\n\nSimulated sources for comparison.")
            self._set_result_summary(f"Comparison prepared for '{query}'. Sources are simulated until live research is connected.")
        elif action == "risks":
            self._findings.setText(
                f"[RISKS for: {query}]\n\n"
                "1. Risk A — mitigation: do X\n"
                "2. Risk B — mitigation: do Y\n\n"
                "(Simulated risk analysis — backend not connected.)"
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
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px; background-color: #161b22; border: 1px solid #30363d;")
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
        self._write_output.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
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
            self._write_output.setText(ctx + f"[OUTLINE for: {prompt[:80]}...]\n\nI. Introduction\nII. Key Points\nIII. Conclusion\n\n(Simulated outline — backend not connected.)")
            self._set_result_summary("Writing outline prepared locally. No file export or publishing occurred.")
        elif action == "draft":
            self._write_output.setText(ctx + f"[DRAFT for: {prompt[:80]}...]\n\n[Generated draft text would appear here.]\n\n(Simulated draft — backend not connected.)")
            self._set_result_summary("Draft prepared locally. Save/export/publish remains approval-gated.")
        elif action == "revise":
            self._write_output.setText(ctx + f"[REVISED for: {prompt[:80]}...]\n\n[Revised text with tracked changes would appear here.]\n\n(Simulated revision — backend not connected.)")
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
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px; background-color: #161b22; border: 1px solid #30363d;")
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
        self._plan_output.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
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
                "(Simulated plan — backend not connected.)"
            )
            self._set_result_summary("Plan generated locally with no task assignment or external commitment.")
        elif action == "risks":
            self._plan_output.setText(
                f"[RISKS for: {goal}]\n\n"
                "- Dependency risk: external API may delay delivery\n"
                "- Scope risk: requirements may expand mid-project\n"
                "- Resource risk: limited QA bandwidth near deadline\n\n"
                "(Simulated risk analysis — backend not connected.)"
            )
            self._set_result_summary("Risk list generated locally. No outward action was taken.")
        elif action == "tasks":
            self._plan_output.setText(
                f"[TASK LIST for: {goal}]\n\n"
                "[ ] Task 1 — owner: TBD — due: TBD\n"
                "[ ] Task 2 — owner: TBD — due: TBD\n"
                "[ ] Task 3 — owner: TBD — due: TBD\n\n"
                "(Simulated task list — backend not connected.)"
            )
            self._set_result_summary("Task list generated locally. No tasks were assigned or exported.")


class NotebookCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Notes — {ai_name}")
        self.resize(700, 500)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px; background-color: #161b22; border: 1px solid #30363d;")
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
        self._notes_output.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
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
        self._notes_output.append(f"Recalling notes (filter: {tag_filter or 'all'})... (Simulated recall — backend not connected.)")
        self._set_result_summary(f"Note recall requested with filter '{tag_filter or 'all'}'. Persistent note backend is not connected.")


class DocumentProcessorCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Document Workflow — {ai_name}")
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px; background-color: #161b22; border: 1px solid #30363d;")
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
        self._doc_output.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
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
            self._doc_output.setText(f"[SUMMARY]\n\n{text[:200]}...\n\n(Simulated summary — backend not connected.)")
            self._set_result_summary("Document summary prepared locally. Export/save remains approval-gated.")
        elif action == "extract":
            self._doc_output.setText(f"[ACTION ITEMS]\n\n- Action 1 (placeholder)\n- Action 2 (placeholder)\n\n(Simulated extraction — backend not connected.)")
            self._set_result_summary("Document action items extracted locally. No export occurred.")
        elif action == "compare":
            self._doc_output.setText(f"[COMPARISON]\n\nSimulated comparison against prior document.\n\n(Simulated — backend not connected.)")
            self._set_result_summary("Document comparison prepared locally. No source files were altered.")


class ArchiveCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Archive — {ai_name}")
        self.resize(700, 500)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px; background-color: #161b22; border: 1px solid #30363d;")
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
        self._archive_output.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
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
        self._archive_output.append(f"Retrieving artifacts (filter: {tag_filter or 'all'})... (Simulated — backend not connected.)")
        self._set_result_summary(f"Archive retrieval requested with filter '{tag_filter or 'all'}'. Archive backend is not connected.")


class ToolUserCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Tool Workflow — {ai_name}")
        self.resize(700, 500)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px; background-color: #161b22; border: 1px solid #30363d;")
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
        self._tool_output.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
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
        self._tool_output.setText(f"[PROPOSAL]\n\nTool: {tool}\nRationale: {rationale[:200]}...\n\nStatus: AWAITING APPROVAL\n\n(Simulated — backend not connected.)")
        self._set_result_summary(f"Tool proposal prepared for '{tool}'. No tool was invoked.")

    def _list_tools(self):
        self._tool_output.setText("[AVAILABLE TOOLS]\n\n- run_git_diff\n- deploy_preview\n- send_email_draft\n- schedule_meeting\n- generate_report\n\n(Simulated list — backend not connected.)")
        self._set_result_summary("Available tool list shown as a safe stub. No tool was invoked.")


class TutorCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Tutor Workflow — {ai_name}")
        self.resize(760, 560)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px; background-color: #161b22; border: 1px solid #30363d;")
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
        self._tutor_output.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
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
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px; background-color: #161b22; border: 1px solid #30363d;")
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
        self._business_output.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
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
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px; background-color: #161b22; border: 1px solid #30363d;")
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
        self._handoff_output.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
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
