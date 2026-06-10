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
}


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
        reply_parts: list[str] = []
        msg_l = msg.lower()
        canonicals = {_canonical_ability(c) for c in self._abilities}
        if "Research" in canonicals and any(k in msg_l for k in ["research", "find", "search", "compare", "source", "cite"]):
            reply_parts.append("[Research result] Live web research is not connected. I can prepare a local research brief, source checklist, risk list, and open the Research workflow for approved external search later.")
            self._approval_banner.setText("Approval required before external/network research.")
            self._approval_banner.setVisible(True)
        if "Coder" in canonicals and any(k in msg_l for k in ["code", "function", "bug", "fix", "test", "diff", "patch"]):
            reply_parts.append("[Coding result] I can operate in show-code-only mode now: explain, draft a diff, or outline tests. File edits and commands stay disabled until approval.")
            self._approval_banner.setText("Approval required before file changes or command/test execution.")
            self._approval_banner.setVisible(True)
        if "Creative Writing" in canonicals and any(k in msg_l for k in ["write", "draft", "story", "scene", "outline", "tone", "polish"]):
            reply_parts.append("[Writing result] I can outline, draft, revise, tone-shift, or polish in this workspace. Saving/exporting is approval-gated.")
            if "Research" in canonicals:
                reply_parts.append("[Research + Writing] If you provide findings or use the Research action first, I can turn them into a source-aware draft.")
        if "Planner" in canonicals and any(k in msg_l for k in ["plan", "project", "task", "milestone", "timeline", "goal", "organize"]):
            reply_parts.append("[Planner result] I can break this into goals, tasks, risks, dependencies, and proposed file/folder moves. Actual moves require approval.")
            self._approval_banner.setText("Approval required before executing organization or external commitments.")
            self._approval_banner.setVisible(True)
        if "Notebook" in canonicals and any(k in msg_l for k in ["note", "notes", "remember", "recall", "tag"]):
            reply_parts.append("[Notes result] I can capture a local note, tag it, and prepare it for archive or task conversion.")
        if "Document Processor" in canonicals and any(k in msg_l for k in ["document", "doc", "summary", "summarize", "extract", "classify"]):
            reply_parts.append("[Document result] I can intake selected text/files, summarize, extract actions, classify, and prepare exports after approval.")
        if "Tutor" in canonicals and any(k in msg_l for k in ["teach", "tutor", "lesson", "quiz", "study", "explain"]):
            reply_parts.append("[Tutor result] I can explain step by step, quiz you, create a study sheet, or adapt the explanation level.")
        if "Business Workflow" in canonicals and any(k in msg_l for k in ["sop", "workflow", "business", "support", "checklist", "handoff"]):
            reply_parts.append("[Business workflow result] I can draft SOPs, checklists, support replies, and handoff packets. Sending or automation requires approval.")
        if ("Hephaestus Relay" in canonicals or "Hephaestus Briefing Library" in self._libraries) and any(k in msg_l for k in ["hephaestus", "design", "prototype", "material", "handoff", "brief"]):
            reply_parts.append("[Hephaestus Relay result] I can structure purpose, constraints, scale, materials, unknowns, and a Hephaestus-ready brief without touching ProtoBrain internals.")
        if not reply_parts:
            reply_parts.append("I can help from this workspace. Use one of the Available Actions, or ask me to chat, research, code, write, plan, process documents, tutor, or prepare a handoff based on this AI's selected capabilities.")
        self._append_ai(" ".join(reply_parts))
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
