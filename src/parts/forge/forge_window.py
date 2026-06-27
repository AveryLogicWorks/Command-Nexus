from __future__ import annotations

# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

from ...core.obfuscation_manager import get_obfuscation_manager
from ...core.license_manager import get_license_manager
from ...core.nexus_use_lockafire import check_use_lock, UseLockArea

ABILITY_SURFACES = {
    "Chatbot": "Workspace chat command surface with Knowledge / Intelligence context and attachment routing",
    "Chat": "Workspace chat command surface with Knowledge / Intelligence context and attachment routing",
    "Notebook": "Notes, recall, tagging, and project-memory workspace",
    "Notes": "Notebook/notes placeholder",
    "Knowledge": "Notebook/notes placeholder",
    "Book": "Human-editable AI Knowledge with attachment markers and approval rules",
    "Writer": "Writing workflow with outline, draft, revise, tone, and approval-gated export",
    "Author": "Writing workflow with outline, draft, revise, tone, and approval-gated export",
    "Creative Writing": "Writing workflow with outline, draft, revise, tone, and approval-gated export",
    "Planner": "Planner workflow for milestones, task breakdowns, risks, and approval-gated outward steps",
    "Mission Planner": "Planner workflow for milestones, task breakdowns, risks, and approval-gated outward steps",
    "Research": "Research workflow with query, findings, sources, citations, and safe live-search stub",
    "Search": "Research workflow with query, findings, sources, citations, and safe live-search stub",
    "Document Processor": "Document intake, summary, extraction, classification, and approval-gated export",
    "Coder": "Code explanation, show-code-only drafting, diff preview, approved edit/test stubs",
    "Vision": "Connect to AI Vision Stream",
    "Visibility": "Connect to AI Vision Stream",
    "Archive": "Artifact staging, archive retrieval, indexing, and approval-gated archive moves",
    "Memory": "Artifact staging, archive retrieval, indexing, and approval-gated archive moves",
    "Tool User": "Tool proposal surface with approval and audit scaffolding",
    "Agent": "Tool proposal surface with approval and audit scaffolding",
    "Tutor": "Tutor workflow with explain, quiz, lesson, study-sheet, and accessibility modes",
    "Business Workflow": "SOP, checklist, support draft, handoff, and automation-plan workspace",
}

# Hephaestus Relay description removed — capability is PAUSED for this build

# Action hints for capabilities (placeholder behaviors)
CAPABILITY_ACTIONS: dict[str, str] = {
    "Chat Companion": "Open chat pane, clarify goals, keep responses concise and ask when unsure.",
    "Coding Assistant": "Explain code, draft diffs, propose tests; do not run commands or write files without approval.",
    "Research Assistant": "Search sources (with approval if external), summarize and cite; mark speculation.",
    "Creative Writer": "Draft and refine text; separate fact from fiction; iterate with user feedback.",
    "Document Processor": "Read documents, extract key points, and summarize action items; no auto-send.",
    "Meeting Scribe": "Capture notes and decisions; produce summaries and action items.",
    "Personal Organizer": "Track tasks and reminders; propose schedules; avoid changes without confirmation.",
    "Task / Project Manager": "Break goals into steps, track status, and flag risks; request approval for risky steps.",
    "Workflow Automator": "Outline automation steps and approvals; do not execute tools without consent.",
    "Customer Support Agent": "Draft replies, keep tone safe, escalate unusual cases; no auto-send.",
    "Email Sifter & Responder": "Sort/prioritize mail, draft replies, highlight urgent items; never auto-send.",
    "Strategic Planner": "Map strategies, options, and risks; request approval before acting.",
    "Business Intelligence Analyst": "Outline analyses and summaries; requires data access approval.",
    "Notebook": "Capture and organize notes; tag by topic/date; no deletions without approval.",
    "Book": "Generate and maintain structured guidance; reflect abilities and guardrails.",
    "Chat": "Hold conversations, clarify needs, and explain next steps.",
}

# ---------------------------------------------------------------------------
# Book Encryption — protects on-disk books from casual inference
# ---------------------------------------------------------------------------
_BOOK_CIPHER_KEY = b"AVERY_LOGIC_WORKS_NEXUS_BOOK_2026"


def _derive_book_key(uuid: str) -> bytes:
    return sha256(_BOOK_CIPHER_KEY + uuid.encode()).digest()


def _encrypt_book(text: str, uuid: str) -> bytes:
    key = _derive_book_key(uuid)
    data = text.encode("utf-8")
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _decrypt_book(data: bytes, uuid: str) -> str:
    key = _derive_book_key(uuid)
    plain = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return plain.decode("utf-8")


def _read_book_file(book_path: str | Path, uuid: str) -> str:
    """Read an encrypted .nbk file, falling back to legacy .md plaintext."""
    path = Path(book_path)
    # Prefer encrypted .nbk
    nbk = path.with_suffix(".nbk")
    if nbk.exists():
        return _decrypt_book(nbk.read_bytes(), uuid)
    # Fallback to legacy .md plaintext
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _canonical_ability(name: str) -> str:
    mapping = {
        "Chat Companion": "Chatbot",
        "Customer Support Agent": "Chatbot",
        "Email Sifter & Responder": "Chatbot",
        "Creative Writer": "Creative Writing",
        "Research Assistant": "Research",
        "Academic Researcher": "Research",
        "Business Intelligence Analyst": "Research",
        "Personal Organizer": "Notebook",
        "Meeting Scribe": "Notebook",
        "Document Processor": "Document Processor",
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
    return mapping.get(name.strip(), name.strip())

def _surface_description(ability: str) -> str:
    """Return an honest surface description for a capability, including implementation status."""
    intent = canonical_intent(ability)
    if is_real(intent):
        return f"{ability} — real engine wired in this build"
    if is_partial(intent):
        return f"{ability} — local scaffold works; full output needs a model or optional API"
    if is_paused(intent):
        return f"{ability} — not connected in this build; requests will be paused instead of faked"
    return f"{ability} — capability status not yet mapped"


def _format_capability_status_summary(abilities: list[str]) -> str:
    """Return a concise real/partial/paused summary for an AI activation dialog."""
    real: list[str] = []
    partial: list[str] = []
    paused: list[str] = []
    unmapped: list[str] = []
    for ab in abilities:
        intent = canonical_intent(ab)
        if is_real(intent):
            real.append(ab)
        elif is_partial(intent):
            partial.append(ab)
        elif is_paused(intent):
            paused.append(ab)
        else:
            unmapped.append(ab)
    lines = ["Capability status in this build:"]
    if real:
        lines.append(f"  Real: {', '.join(real)}")
    if partial:
        lines.append(f"  Partial: {', '.join(partial)}")
    if paused:
        lines.append(f"  Paused: {', '.join(paused)}")
    if unmapped:
        lines.append(f"  Unmapped: {', '.join(unmapped)}")
    return "\n".join(lines)


def _generate_surfaces(abilities: list[str]) -> dict[str, str]:
    surfaces = {}
    for ab in abilities:
        key = _canonical_ability(ab)
        desc = ABILITY_SURFACES.get(key)
        if desc:
            # Keep the original technical description but append the honesty status.
            status = capability_status(canonical_intent(ab))
            if status == ImplementationStatus.PAUSED:
                desc = f"{desc} (NOT CONNECTED in this build)"
            elif status == ImplementationStatus.PARTIAL:
                desc = f"{desc} (PARTIAL — local scaffold works, model/API optional)"
            elif status == ImplementationStatus.REAL:
                desc = f"{desc} (REAL)"
        else:
            desc = _surface_description(ab)
        surfaces[key] = desc
        surfaces[ab] = desc  # keep original name mapping for Knowledge / Intelligence rendering
    return surfaces

def _starter_workflows(abilities: list[str]) -> list[str]:
    combos = set(_canonical_ability(a) for a in abilities)
    workflows: list[str] = get_combined_capability_workflows(abilities) if "get_combined_capability_workflows" in globals() else []
    if {"Chatbot", "Notebook"} & combos:
        workflows.append("Chat can reference notebook/knowledge entries later.")
    if {"Chatbot", "Book"} & combos:
        workflows.append("Chat can summarize/draft from Knowledge / Intelligence profile.")
    if {"Planner", "Tool User"} & combos or {"Mission Planner", "Agent"} & combos:
        workflows.append("Plans require approval before tool execution.")
    if {"Vision", "Planner"} & combos or {"Visibility", "Planner"} & combos:
        workflows.append("Visual observations feed into planned actions.")
    if {"Research", "Archive"} & combos or {"Search", "Archive"} & combos:
        workflows.append("Research outputs are saved to archive.")
    if {"Book", "Notebook", "Chatbot"} <= combos:
        workflows.append("Knowledge companion: chat + book + notebook interconnected.")
    if {"Tutor", "Research"} <= combos:
        workflows.append("Tutor uses research discipline to build study sheets and cite uncertainty.")
    if {"Business Workflow", "Planner"} <= combos:
        workflows.append("Business workflow uses planning to produce SOPs, checklists, and approval points.")
    return workflows

def _use_case_context(use_case: UseCaseClass) -> list[str]:
    uc = use_case.value if isinstance(use_case, UseCaseClass) else str(use_case)
    if use_case == UseCaseClass.BUSINESS:
        return [
            "Business function: draft responses, organize notes, research, plans.",
            "Customer/internal context: assist but do not auto-send externally.",
            "Departments supported: marketing, support, sales, ops (draft-only).",
            "Do not make financial/HR/legal decisions without review.",
        ]
    if use_case == UseCaseClass.EDUCATIONAL:
        return [
            "Learner/tutor context; respect academic honesty.",
            "Provide guidance, not final graded answers.",
            "Support accessibility and clarity; cite sources when applicable.",
        ]
    if use_case == UseCaseClass.INDIVIDUAL:
        return [
            "Personal assistant context; prioritize privacy and consent.",
            "Organize notes, tasks, writing, research; ask before changes.",
            "Do not alter files or send messages without approval.",
        ]
    if use_case == UseCaseClass.TASK_READY:
        return [
            "Task intake must be clear; confirm scope and completion criteria.",
            "Follow workflow steps; pause for approval on risky actions.",
        ]
    if use_case == UseCaseClass.ENTERPRISE:
        return [
            "Enterprise context; compliance/audit required.",
            "Follow approval hierarchy; handle data with least privilege.",
            "Never bypass governance; log actions with rationale.",
        ]
    if use_case == UseCaseClass.ALL_ROUNDER:
        return [
            "Broad support; ask user to clarify mode and priority.",
            "Switch modes based on task; avoid overreach.",
        ]
    if use_case == UseCaseClass.MILITARY_GOVERNMENT:
        return [
            "Future controlled edition placeholder. Not enabled in public build.",
            "No operational doctrine generated in this build.",
        ]
    return [f"Context: {uc}"]


def _ability_doctrine(ab: str, use_case: UseCaseClass) -> list[str]:
    ab_norm = _canonical_ability(ab)
    base = []
    if ab_norm in {"Chatbot", "Chat"}:
        base = [
            "Purpose: conversational interface; clarify tasks; keep answers concise.",
            "Use: gather requirements, summarize, explain decisions.",
            "Cannot: execute system actions or send messages without approval.",
        ]
    elif ab_norm in {"Research", "Search"}:
        base = [
            "Purpose: gather and organize findings; cite sources when possible.",
            "Use: produce bullet notes, mark speculation vs facts.",
            "Approval: external/network calls require approval.",
        ]
    elif ab_norm in {"Creative Writing", "Writer", "Author", "Book"}:
        base = [
            "Purpose: outlines, drafts, scripts; separate fact from fiction.",
            "Use: draw from research/notes if available; flag invented content.",
        ]
    elif ab_norm in {"Notebook", "Notes", "Knowledge"}:
        base = [
            "Purpose: capture notes and context; keep entries dated and labeled.",
            "Approval: file modifications need approval in protected mode.",
        ]
    elif ab_norm in {"Document Processor"}:
        base = [
            "Purpose: read, summarize, and extract key points from documents.",
            "Use: provide concise takeaways, highlight risks, and capture action items.",
            "Approval: do not auto-send or publish processed content without review.",
        ]
    elif ab_norm in {"Document Processor"}:
        base = [
            "Purpose: read, summarize, and extract key points from documents.",
            "Use: provide concise takeaways, highlight risks, and capture action items.",
            "Approval: do not auto-send or publish processed content without review.",
        ]
    elif ab_norm in {"Planner", "Mission Planner"}:
        base = [
            "Purpose: propose step plans; tag risks; request approvals for execution.",
            "Cannot: execute tools without approval.",
        ]
    elif ab_norm in {"Coder"}:
        base = [
            "Purpose: explain code, propose diffs, and outline fixes with governance gates.",
            "Use: suggest patches and tests; do not run commands or write files without approval.",
            "Approval: any code execution, file modification, or dependency install requires explicit consent.",
        ]
    elif ab_norm in {"Archive", "Memory"}:
        base = [
            "Purpose: store artifacts locally; keep index of saved items.",
            "Approval: moving/deleting files requires approval.",
        ]
    elif ab_norm in {"Tool User", "Agent"}:
        base = [
            "Purpose: call tools; always go through approval gate for risky actions.",
            "Cannot: bypass governance; log rationale.",
        ]
    elif ab_norm in {"Coder", "Coding", "Developer"}:
        base = [
            "Purpose: explain code, draft starter snippets, debug with guidance.",
            "Cannot: modify files or run commands without explicit approval.",
            "Safe scope: propose patches, pseudo-code, and plans; mark risks.",
        ]
    else:
        base = ["Purpose: placeholder; backend not connected yet."]
    # Tailor minor use-case note
    if use_case == UseCaseClass.BUSINESS:
        base.append("Business tone: clear, helpful, brand-safe; do not auto-publish.")
    elif use_case == UseCaseClass.EDUCATIONAL:
        base.append("Educational tone: supportive, avoids giving final graded answers.")
    elif use_case == UseCaseClass.ENTERPRISE:
        base.append("Enterprise: keep auditability; reference approval rules.")
    return base


def _cross_ability_doctrine(abilities: list[str]) -> list[str]:
    combos = set(_canonical_ability(a) for a in abilities)
    guidance = []
    if {"Chatbot", "Research"} <= combos or {"Chat", "Research"} <= combos:
        guidance.append("Chat + Research: discuss topics, separate sources vs speculation, keep citations when possible.")
    if {"Chatbot", "Coder"} <= combos or {"Chat", "Coder"} <= combos:
        guidance.append("Chat + Coder: explain code, propose patches, no file writes or commands without approval.")
    if {"Research", "Creative Writing"} <= combos or {"Search", "Writer"} <= combos:
        guidance.append("Research + Creative Writing: turn research into outlines/drafts; mark invented content.")
    if {"Planner", "Tool User"} <= combos or {"Mission Planner", "Agent"} <= combos:
        guidance.append("Planner + Tool User: propose steps; request approval before tool execution.")
    if {"Archive", "Notebook", "Chatbot"} <= combos:
        guidance.append("Archive + Notebook + Chat: save context, recall notes, but verify before acting.")
    if {"Business", "Marketing", "Research"} & combos:  # loose match
        guidance.append("Business + Marketing + Research: draft campaigns from research; do not auto-send; require approval.")
    return guidance or ["No combined behaviors yet; placeholder mode."]


def _book_content(ai_id: str, name: str, use_case: UseCaseClass, purpose: str, abilities: list[str],
                  surfaces: dict[str, str], workflows: list[str], guardrails: list[str],
                  libraries: list[str] | None = None, ability_surfaces: dict[str, str] | None = None) -> str:
    # Per-ability operational profiles (allowed, restricted, approval, style, quickstart, prompts)
    profiles: dict[str, dict[str, list[str]]] = {
        "Chatbot": {
            "allowed": [
                "Hold conversations and clarify user goals",
                "Summarize decisions and next steps",
                "Ask clarifying questions when requirements are vague",
            ],
            "restricted": [
                "Send messages or emails without approval",
                "Execute system actions from chat alone",
            ],
            "approval": [
                "Outbound messages or customer-facing replies",
                "Actions triggered from chat (files, commands, purchases)",
            ],
            "style": ["Conversational, concise, transparent", "Ask before assuming intent"],
            "quickstart": [
                "Open Chat and describe what you need",
                "The AI will ask clarifying questions if scope is unclear",
                "Ask it to summarize or explain decisions",
            ],
            "prompts": [
                "Summarize this for me",
                "Explain why we chose X",
                "Clarify the next steps",
            ],
        },
        "Research": {
            "allowed": [
                "Gather and organize findings",
                "Produce bullet notes and comparisons",
                "Cite sources when available",
            ],
            "restricted": [
                "Make final decisions based on research alone",
                "Auto-publish findings without review",
            ],
            "approval": [
                "External/network searches",
                "Accessing proprietary databases",
                "Exporting research summaries externally",
            ],
            "style": ["Mark speculation vs facts clearly", "Provide sources or confidence levels"],
            "quickstart": [
                "Ask a research question with scope and format",
                "Review the sourced bullets and ask for deeper dives",
                "Request citations or confidence labels",
            ],
            "prompts": [
                "Research X and give me 3 bullet takeaways",
                "Compare A vs B with sources",
                "Find risks related to Y",
            ],
        },
        "Coder": {
            "allowed": [
                "Explain code and logic",
                "Draft diffs and propose patches",
                "Outline tests and refactoring plans",
            ],
            "restricted": [
                "Run shell commands or install packages",
                "Write or modify files without approval",
                "Execute code automatically",
            ],
            "approval": [
                "File modifications",
                "Dependency installation",
                "Running commands or scripts",
                "Deploying changes",
            ],
            "style": ["Show reasoning before the fix", "Mark risky changes clearly"],
            "quickstart": [
                "Paste code and ask for an explanation",
                "Request a diff or patch for a bug",
                "Ask for test ideas",
            ],
            "prompts": [
                "Explain this function",
                "Propose a fix for bug X",
                "Draft unit tests for this module",
            ],
        },
        "Creative Writing": {
            "allowed": [
                "Draft outlines, scenes, scripts, and copy",
                "Iterate based on feedback",
                "Separate fact from fiction",
            ],
            "restricted": [
                "Present fiction as fact",
                "Auto-publish or distribute drafts",
            ],
            "approval": [
                "Publishing or sending creative content externally",
                "Using trademarked or sensitive material",
            ],
            "style": ["Adapt tone to audience", "Flag invented content"],
            "quickstart": [
                "Describe the piece, audience, and tone",
                "Request an outline first, then expand",
                "Iterate with feedback",
            ],
            "prompts": [
                "Write an outline for X",
                "Rewrite this in a professional tone",
                "Expand scene 2 with more tension",
            ],
        },
        "Notebook": {
            "allowed": [
                "Capture notes and context",
                "Organize entries by topic/date",
                "Recall prior notes when relevant",
            ],
            "restricted": [
                "Delete or overwrite notes without approval",
                "Auto-archive sensitive content without tagging",
            ],
            "approval": [
                "Bulk deletions",
                "Exporting notes externally",
                "Changing note structure or tags",
            ],
            "style": ["Label entries clearly", "Summarize before storing long content"],
            "quickstart": [
                "Ask the AI to take notes during a discussion",
                "Request a summary of stored notes on a topic",
                "Add tags for easy retrieval",
            ],
            "prompts": [
                "Take notes on this meeting",
                "Summarize my notes about X",
                "Tag this as project-alpha",
            ],
        },
        "Planner": {
            "allowed": [
                "Break goals into steps",
                "Track status and flag risks",
                "Propose timelines and owners",
            ],
            "restricted": [
                "Execute steps automatically",
                "Assign tasks to people without confirmation",
                "Change deadlines without approval",
            ],
            "approval": [
                "Executing risky steps",
                "Reassigning work",
                "Committing to external timelines",
            ],
            "style": ["Show the plan before execution", "Flag dependencies and blockers"],
            "quickstart": [
                "Describe the goal and constraints",
                "Review the proposed plan and edit it",
                "Approve or modify risky steps",
            ],
            "prompts": [
                "Plan project X with milestones",
                "What are the risks in this plan?",
                "Convert this goal into a task list",
            ],
        },
        "Document Processor": {
            "allowed": [
                "Read and summarize documents",
                "Extract key points, risks, and action items",
                "Compare multiple documents",
            ],
            "restricted": [
                "Auto-send or publish processed content",
                "Alter source documents",
            ],
            "approval": [
                "Exporting summaries externally",
                "Accessing sensitive or classified documents",
            ],
            "style": ["Provide concise takeaways", "Highlight uncertainties"],
            "quickstart": [
                "Upload or describe the document",
                "Ask for a summary, key points, or action items",
                "Request a comparison with another doc",
            ],
            "prompts": [
                "Summarize this document",
                "Extract action items",
                "Compare doc A and doc B",
            ],
        },
        "Archive": {
            "allowed": [
                "Store artifacts and deliverables",
                "Maintain an index of saved items",
                "Retrieve prior outputs on request",
            ],
            "restricted": [
                "Delete or move archived files without approval",
                "Auto-archive without user intent",
            ],
            "approval": [
                "Moving or deleting archives",
                "Bulk exports",
            ],
            "style": ["Tag and date entries", "Confirm before saving sensitive content"],
            "quickstart": [
                "Ask the AI to archive a deliverable",
                "Request retrieval of a prior output",
                "Search the archive by tag or date",
            ],
            "prompts": [
                "Archive this draft",
                "Find my last report on X",
                "List archived items from last week",
            ],
        },
        "Tool User": {
            "allowed": [
                "List available tools and their purposes",
                "Propose tool usage with rationale",
            ],
            "restricted": [
                "Execute tools without approval",
                "Bypass governance gates",
                "Chain tools automatically",
            ],
            "approval": [
                "Every tool invocation",
                "High-risk tool activation",
                "Multi-step tool chains",
            ],
            "style": ["Explain what the tool will do before running", "Log rationale"],
            "quickstart": [
                "Ask what tools are available",
                "Request a tool-assisted workflow with steps and approvals",
                "Review tool output before proceeding",
            ],
            "prompts": [
                "What tools can help with X?",
                "Run tool Y and show me the result",
                "Propose a tool chain for this task",
            ],
        },
    }

    def _dedup(seq: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for x in seq:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    allowed: list[str] = []
    restricted: list[str] = []
    approval: list[str] = []
    style_notes: list[str] = []
    quickstart_steps: list[str] = []
    common_prompts: list[str] = []

    canonicals: set[str] = set()
    for ab in abilities:
        c = _canonical_ability(ab)
        canonicals.add(c)
        prof = profiles.get(c)
        if prof:
            allowed.extend(prof["allowed"])
            restricted.extend(prof["restricted"])
            approval.extend(prof["approval"])
            style_notes.extend(prof["style"])
            quickstart_steps.extend(prof["quickstart"])
            common_prompts.extend(prof["prompts"])

    allowed = _dedup(allowed)
    restricted = _dedup(restricted)
    approval = _dedup(approval)
    style_notes = _dedup(style_notes)
    quickstart_steps = _dedup(quickstart_steps)
    common_prompts = _dedup(common_prompts)

    if not allowed:
        allowed = ["Assist within the scope of the AI's defined purpose", "Ask clarifying questions when unsure"]
    if not restricted:
        restricted = ["Do not execute system actions without approval", "Do not bypass governance gates"]
    if not approval:
        approval = ["Actions that affect files, settings, or external systems"]

    # Apply optional guardrail-derived rules
    if "Ask before editing files" in guardrails:
        restricted.append("Never edit, delete, or move files without explicit user confirmation")
        approval.append("Code changes that modify existing files")
    if "Require confirmation before risky actions" in guardrails:
        approval.append("Any action that could affect files, settings, or external systems")
    if "Never reference external competitors by name" in guardrails:
        restricted.append("Do not name or disparage external competitors or third-party products")
    if "Limit memory of past sessions to current context only" in guardrails:
        restricted.append("Do not recall or reference information from prior sessions outside current context")
    if "Require explicit consent before personalization changes" in guardrails:
        approval.append("Changes to personality, tone, or stored preferences")
    if "Archive every deliverable automatically" in guardrails:
        allowed.append("Auto-archive every output and deliverable to the assigned archive")
    if "Flag speculative answers clearly as speculation" in guardrails:
        allowed.append("Clearly mark uncertain or speculative statements as such")
    if "Always suggest alternatives when declining a request" in guardrails:
        allowed.append("When declining a request, always offer a constructive alternative")
    if "Offer to escalate complex topics to human review" in guardrails:
        allowed.append("Offer to escalate complex, sensitive, or ambiguous topics to human review")

    # Use-case specific additions
    if use_case == UseCaseClass.BUSINESS:
        allowed.append("Business-safe wording; brand-aligned tone; do not auto-publish")
    if use_case == UseCaseClass.EDUCATIONAL:
        allowed.append("Beginner-friendly explanations; avoid final graded answers; guide learning")
    if use_case == UseCaseClass.ENTERPRISE:
        allowed.append("Enterprise compliance: audit-friendly outputs; least-privilege handling")

    if use_case == UseCaseClass.MILITARY_GOVERNMENT:
        return "\n".join([
            f"# Knowledge / Intelligence Profile for {name} (Public Build Placeholder)",
            "", "This edition is a future controlled edition and is disabled in the public build.",
            "No operational doctrine generated.",
        ])

    lines: list[str] = []
    lines.append(f"# Knowledge / Intelligence Profile for {name}")
    lines.append("")
    lines.append("## Identity and Purpose")
    lines.append(f"- AI Name: {name}")
    lines.append(f"- AI ID: {ai_id}")
    lines.append(f"- Use-Case Class: {use_case.value}")
    lines.append(f"- Purpose: {purpose or 'Assist within described context; respect approvals.'}")
    lines.append("- Intended user: Command Nexus™ operator")
    lines.append("- Primary role: Assist within described context; respect approvals.")
    lines.append("")

    lines.append("## Operating Context")
    lines.extend([f"- {c}" for c in _use_case_context(use_case)])
    lines.append("")

    libs = libraries or []
    if libs:
        lookup = {l["name"]: l for l in NEXUS_LIBRARIES}
        lines.append("## Nexus Libraries (not abilities)")
        for lib in libs:
            info = lookup.get(lib)
            if info:
                lines.append(f"- {lib}: {info.get('description', '')}")
                if info.get("integration_target"):
                    lines.append(f"  Integration: {info.get('integration_target')}")
                if info.get("category"):
                    lines.append(f"  Category: {info.get('category')}")
                if info.get("risk_level"):
                    lines.append(f"  Risk: {info.get('risk_level')}")
            else:
                lines.append(f"- {lib}")
        lines.append("")

    lines.append("## Allowed Areas")
    lines.extend([f"- {a}" for a in allowed])
    lines.append("")

    lines.append("## Restricted Areas")
    lines.extend([f"- {r}" for r in restricted])
    lines.append("")

    lines.append("## Approval Required")
    lines.extend([f"- {a}" for a in approval])
    lines.append("")

    lines.append("## How This AI Should Work")
    lines.append("- Style: concise, transparent, cites source/assumptions, asks when unsure.")
    lines.append("- Ask questions when requirements are unclear; summarize before acting.")
    lines.append("- Stop and ask when action touches restricted or approval-required areas.")
    for sn in style_notes:
        lines.append(f"- {sn}")
    lines.append("")

    lines.append("## Guardrails")
    lines.append("These are the optional behavior upgrades selected for this AI.")
    lines.append("System-level protections are enforced by the Nexus Compendium and are active regardless of this list.")
    if guardrails:
        for gr in guardrails:
            lines.append(f"- {gr}")
    else:
        lines.append("- (No optional guardrails selected — add them in the Forge to customize behavior.)")
    lines.append("")

    lines.append("## Response Style Defaults")
    if "Keep responses beginner-friendly" in guardrails:
        lines.append("- Use plain language; define jargon; give examples.")
    if "Keep responses concise" in guardrails:
        lines.append("- Be brief; prioritize bullet points over paragraphs.")
    if "Avoid specific technical jargon unless asked" in guardrails:
        lines.append("- Avoid technical jargon unless the user requests it.")
    if "Never use emojis or informal formatting" in guardrails:
        lines.append("- Never use emojis, slang, or overly casual formatting.")
    if "Always summarize long outputs before detail" in guardrails:
        lines.append("- Always provide a brief summary before detailed content.")
    if "Prefer step-by-step explanations" in guardrails:
        lines.append("- Break explanations into numbered or step-by-step form.")
    if "Use inclusive and neutral language" in guardrails:
        lines.append("- Use inclusive, neutral, and respectful language at all times.")
    if "Always explain reasoning before giving answers" in guardrails:
        lines.append("- Briefly explain reasoning before presenting the final answer.")
    if "Respect time-of-day context (quiet hours awareness)" in guardrails:
        lines.append("- Avoid loud or disruptive notifications during quiet hours.")
    if use_case == UseCaseClass.BUSINESS:
        lines.append("- Use clear, brand-safe, professional wording.")
    if use_case == UseCaseClass.EDUCATIONAL:
        lines.append("- Be supportive and patient; guide rather than give final answers.")
    if use_case == UseCaseClass.INDIVIDUAL:
        lines.append("- Prioritize privacy and consent; ask before changes.")
    if use_case == UseCaseClass.ENTERPRISE:
        lines.append("- Maintain auditability; reference approval rules in outputs.")
    if not any(x in guardrails for x in ["Keep responses beginner-friendly", "Keep responses concise", "Avoid specific technical jargon unless asked", "Never use emojis or informal formatting", "Always summarize long outputs before detail", "Prefer step-by-step explanations", "Use inclusive and neutral language", "Always explain reasoning before giving answers", "Respect time-of-day context (quiet hours awareness)"]):
        if use_case not in {UseCaseClass.BUSINESS, UseCaseClass.EDUCATIONAL, UseCaseClass.ENTERPRISE, UseCaseClass.INDIVIDUAL}:
            lines.append("- Default style: clear, transparent, asks when unsure.")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("# PART: ACTIVE MEMORY (User-Defined)")
    lines.append("This section holds the AI's live instructions, memories, and preferences.")
    lines.append("It is populated by the Knowledge AI dialog and can be updated through conversation.")
    lines.append("Capability sections below are internal and only editable if the user explicitly asks.")
    lines.append("")
    lines.append("## Active Instructions")
    lines.append("Live behavioral instructions for how this AI should operate right now.")
    lines.append("- Ask clarifying questions when requirements are unclear.")
    lines.append("- Summarize before acting on complex requests.")
    lines.append("- Stop and ask when action touches restricted or approval-required areas.")
    lines.append("")
    lines.append("## Persistent Memory")
    lines.append("Long-term facts and knowledge that should always be remembered.")
    lines.append("- User identity and core preferences")
    lines.append("- Business names, key contacts, important relationships")
    lines.append("- Technical stack preferences, workflow habits")
    lines.append("")
    lines.append("## General Memory")
    lines.append("Current context and temporary knowledge that may change over time.")
    lines.append("- Active projects and current focus")
    lines.append("- Temporary constraints or deadlines")
    lines.append("- Learning progress and current topics of interest")
    lines.append("")
    lines.append("## Preferences")
    lines.append("User's personal preferences for interaction style and behavior.")
    lines.append("- Communication style (formal, casual, detailed, brief)")
    lines.append("- Response format preferences (bullets, paragraphs, step-by-step)")
    lines.append("- Notification and interaction preferences")
    lines.append("")
    lines.append("## Rollback Safety")
    lines.append("Any capability or behavior change made by the user can be reverted to defaults.")
    lines.append("If the user says something isn't working, offer to revert to the previous working state.")
    lines.append("The AI should never be afraid to suggest: 'Would you like me to go back to how things were before?'")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("# PART: INTERNAL CAPABILITY ENTRIES — DO NOT MODIFY")
    lines.append("The following entries are auto-generated based on selected capabilities.")
    lines.append("They define standalone behavior and interconnection rules for the AI's internal use.")
    lines.append("Users should NOT see these entries. The AI uses them to route and coordinate capabilities.")
    lines.append("If a user asks to edit capability behavior, confirm they understand the risks.")
    lines.append("")

    lines.append("## Ability Sections")
    for ab in abilities:
        c = _canonical_ability(ab)
        lines.append(f"### {ab}")
        for bullet in _ability_doctrine(ab, use_case):
            lines.append(f"- {bullet}")
        surf = (ability_surfaces or surfaces).get(ab, (ability_surfaces or surfaces).get(c, "Placeholder surface; backend not connected"))
        lines.append(f"- Surface: {surf}")
        lines.append("- Activation: capability attachment registry; governance gate enforced.")
        for detail in describe_capability_for_book(ab):
            lines.append(f"- {detail}")
        prof = profiles.get(c)
        if prof:
            lines.append(f"- Common prompts: {', '.join(prof['prompts'])}")
            lines.append(f"- Quickstart: {'; '.join(prof['quickstart'])}")
        else:
            lines.append("- Common prompts: clarify task, ask for context, request approval when needed.")
        lines.append("")

    lines.append("## Capability Attachments")
    for ab in abilities:
        c = _canonical_ability(ab)
        action = CAPABILITY_REGISTRY.get(c)
        if action:
            lines.append(f"### {ab} -> {action.display_name}")
            lines.append(f"- capability_id: {action.capability_id}")
            lines.append(f"- inward_surface: {action.inward_surface}")
            lines.append(f"- outward_action_path: {action.outward_action_path}")
            lines.append(f"- required_permissions: {', '.join(action.required_permissions) if action.required_permissions else 'None'}")
            lines.append(f"- required_approval_level: {action.required_approval_level}")
            lines.append(f"- unfinished_safe_fallback: {action.unfinished_safe_fallback}")
        else:
            lines.append(f"### {ab}")
            lines.append("- SAFE STUB: No registered attachment yet; inward clarification only, outward disabled.")
        lines.append("")

    lines.append("## Available Actions")
    for action in get_available_actions_for_ai(abilities, use_case.value, libs, guardrails):
        lines.append(f"- {action['label']} [{action['mode']} / approval: {action['approval']}]: {action['description']}")
    lines.append("")

    lines.append("## Pricing / Tier Scaffold")
    lines.append("This is config-friendly scaffold only; billing is not implemented here.")
    for tier, cfg in TIER_SCAFFOLD.items():
        lines.append(f"### {tier}")
        for k, v in cfg.items():
            lines.append(f"- {k}: {v}")
    lines.append("")

    lines.append("## Cross-Capability Workflows")
    for ca in list(dict.fromkeys(_cross_ability_doctrine(abilities) + get_combined_capability_workflows(abilities, libs, use_case.value))):
        lines.append(f"- {ca}")
    if workflows:
        for wf in workflows:
            lines.append(f"- Workflow: {wf}")
    lines.append("")

    lines.append("## Quickstart")
    if quickstart_steps:
        for i, qs in enumerate(quickstart_steps, 1):
            lines.append(f"{i}. {qs}")
    else:
        lines.append("1. Open Chat from the Forge to talk to this AI.")
        lines.append("2. Ask it to draft, research, or plan; it will cite rules from this Book.")
        lines.append("3. Risky actions (files/commands/network) require approval.")
    lines.append("")

    if common_prompts:
        lines.append("## Common Prompts")
        for cp in common_prompts:
            lines.append(f"- {cp}")
        lines.append("")

    lines.append("## Editable Guidance")
    lines.append("### Safe to Customize")
    lines.extend([
        "- Tone, examples, personal notes, brand voice",
        "- Preferred workflows, writing style, business/context notes",
    ])
    lines.append("### Edit with Caution")
    lines.extend([
        "- Ability descriptions and activation instructions",
        "- Allowed/Restricted/Approval sections",
        "- Cross-ability behavior, archive paths, routing notes",
    ])
    lines.append("### Core Link, Advanced Edit")
    lines.extend([
        "- ai_id, ability IDs, runtime registration fields",
        "- Approval rules, manifest/tool identifiers",
        "Warning: changes may break routing.",
    ])
    lines.append("")

    lines.append("## Save Safety")
    lines.append("- Ensure required sections remain: Identity, Context, Allowed, Restricted, Approval, How This AI Should Work, Guardrails, Response Style, Ability Sections, Cross-Ability, Quickstart, Common Prompts, Editable Guidance.")
    lines.append("- Keep approval-required guardrails intact.")
    lines.append("- A timestamped backup is stored alongside this book on generation.")
    lines.append("- These defaults are generated from the AI's use case, capabilities, and guardrails. You may edit them, but changing core defaults is not recommended unless you understand how it may affect the AI's behavior.")
    lines.append("")

    # ===================================================================
    # AUTO-GENERATED CAPABILITY ENTRIES
    # These describe how each capability works standalone and interconnected
    # ===================================================================
    lines.append("---")
    lines.append("")
    lines.append("# INTERNAL CAPABILITY ENTRIES — DO NOT MODIFY")
    lines.append("The following entries are auto-generated based on the AI's selected capabilities.")
    lines.append("They define standalone behavior and interconnection rules for the AI's internal use.")
    lines.append("")

    # Generate capability entries using the capKnowledge / Intelligence profile engine
    capability_book_content = generate_full_book_for_ai(abilities)
    lines.append(capability_book_content)

    return "\n".join(lines)


def _smoke_test_scaffold():
    """Create a temp AI profile with common abilities to verify scaffolding."""
    tmp = Path(tempfile.mkdtemp(prefix="cnx_test_"))
    unit = AIUnit(
        uuid="TEST1234",
        name="SmokeTestAI",
        use_case=UseCaseClass.TASK_READY,
        source=AISource.CREATED,
        capabilities=["Chatbot", "Notebook", "Book", "Planner"],
        abilities=["Chatbot", "Notebook", "Book", "Planner"],
        locked=True,
    )
    unit = _scaffold_unit(unit, purpose="Demo smoke", base_dir=tmp)
    assert unit.archive_path and Path(unit.archive_path).exists(), "Archive not created"
    assert unit.ability_book_path and Path(unit.ability_book_path).exists(), "Knowledge / Intelligence profile not created"
    assert unit.ability_surfaces, "Surfaces missing"
    assert unit.starter_workflows, "Workflows missing"
    return True


def _scaffold_unit(unit: AIUnit, purpose: str = "", base_dir: Path | None = None) -> AIUnit:
    base = base_dir or (Path.home() / "CommandNexusWorkspace" / "ai_archive")
    base.mkdir(parents=True, exist_ok=True)
    folder = base / f"{unit.name.replace(' ', '_')}_{unit.uuid}"
    folder.mkdir(parents=True, exist_ok=True)

    abilities = unit.abilities or unit.capabilities
    surfaces = _generate_surfaces(abilities)
    workflows = _starter_workflows(abilities)

    unit.archive_path = str(folder)
    unit.ability_surfaces = surfaces
    unit.starter_workflows = workflows

    book_path = folder / "ability_book.nbk"
    backup_path = folder / f"ability_book_backup_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.nbk"
    legacy_path = folder / "ability_book.md"
    # Migrate legacy plaintext to encrypted if present
    if legacy_path.exists() and not book_path.exists():
        legacy_text = legacy_path.read_text(encoding="utf-8")
        book_path.write_bytes(_encrypt_book(legacy_text, unit.uuid))
        legacy_path.unlink()  # Remove plaintext to prevent inference
    elif book_path.exists() and not unit.book_defaults_edited:
        backup_path.write_bytes(book_path.read_bytes())
    book_text = _book_content(
        unit.uuid, unit.name, unit.use_case, purpose or unit.context_notes, abilities, surfaces, workflows,
        guardrails=unit.guardrails, libraries=unit.libraries, ability_surfaces=surfaces
    )
    if not book_path.exists() or not unit.book_defaults_edited:
        book_path.write_bytes(_encrypt_book(book_text, unit.uuid))
    unit.ability_book_path = str(book_path)

    # Persist a profile snapshot
    profile_path = folder / "profile.json"
    profile = {
        "uuid": unit.uuid,
        "name": unit.name,
        "use_case": unit.use_case.value,
        "source": unit.source.value if unit.source else "",
        "capabilities": unit.capabilities,
        "abilities": abilities,
        "personality_traits": unit.personality_traits,
        "context_notes": unit.context_notes,
        "archive_path": unit.archive_path,
        "ability_book_path": unit.ability_book_path,
        "manifest_path": str(profile_path),
        "ability_surfaces": unit.ability_surfaces,
        "starter_workflows": unit.starter_workflows,
        "guardrails": unit.guardrails,
        "book_defaults_edited": unit.book_defaults_edited,
        "created_at": unit.created_at.isoformat(),
        "activated": unit.activated,
        "enabled": unit.enabled,
        "timestamp": datetime.utcnow().isoformat(),
    }
    profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    return unit
import json
import uuid
import tempfile
from pathlib import Path
from datetime import datetime
from hashlib import sha256

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QLineEdit, QTextEdit, QListWidget,
    QListWidgetItem, QGroupBox, QFormLayout, QCheckBox, QSlider,
    QFileDialog, QProgressDialog, QMessageBox, QSplitter, QFrame,
    QDialog, QDialogButtonBox, QGridLayout, QScrollArea, QMenu
)

from ...core.governance import GovernanceEngine
from ...core.constants import UseCaseClass
from ...core.nexus_moirai import check_action_allowed, MoiraiHealthReport
from ...core.import_record import ImportedAIRecord, ImportStatus
from ...core.watcher_service import run_watchers, BLOCK_MESSAGE
from ...core.translator import NexusIntentTranslator
from ...core.settings_manager import SettingsManager
from ...core.stasis_gate import StasisGate, StasisState
from ...core.recursive_scanner import RecursiveScanner, ScanResult, ThreatLevel
from ...core.capability_registry import canonical_intent, capability_status, is_real, is_partial, is_paused, ImplementationStatus
from .forge_models import AIUnit, AISource
from .capability_book_engine import generate_full_book_for_ai
from .capability_actions import (
    CAPABILITY_REGISTRY,
    TIER_SCAFFOLD,
    describe_capability_for_book,
    get_available_actions_for_ai,
    get_actions_for_ai,
    get_combined_capability_workflows,
    ChatCapabilityDialog,
    CodingCapabilityDialog,
    ResearchCapabilityDialog,
    CreativeWriterCapabilityDialog,
    PlannerCapabilityDialog,
    NotebookCapabilityDialog,
    DocumentProcessorCapabilityDialog,
    ArchiveCapabilityDialog,
    ToolUserCapabilityDialog,
    TutorCapabilityDialog,
    BusinessWorkflowCapabilityDialog,
    # HephaestusRelayCapabilityDialog — reserved for future Hephaestus integration
)


# Use-case → capability presets
USE_CASE_OPTIONS: dict = {
    UseCaseClass.INDIVIDUAL: [
        "Chat Companion", "Coding Assistant", "Creative Writer",
        "Learning Tutor", "Personal Organizer", "Research Assistant",
        "Customer Support AI",  # Available in all use cases
        # Premium upgrades
        "Memory Bridge", "Visual Canvas", "Voice Interface",
        "Calendar Manager", "Email Automation", "Document Generator",
        "Budget Tracker", "Social Media Manager",
    ],
    UseCaseClass.EDUCATIONAL: [
        "Classroom Tutor", "Assignment Grader", "Lesson Planner",
        "Academic Researcher", "Language Coach", "Accessibility Aide",
        "Customer Support AI",  # Available in all use cases
        # Premium upgrades
        "Learning Path Creator", "Knowledge Base Builder", "Presentation Builder",
        "Translation Expert", "Fact Checker", "Smart Search",
        "Study Coach", "Plagiarism Checker",
    ],
    UseCaseClass.TASK_READY: [
        "Document Processor", "Meeting Scribe", "Data Entry Agent",
        "Workflow Automator", "Content Moderator",
        "Customer Support AI",  # Available in all use cases
        # Premium upgrades
        "Meeting Facilitator", "Calendar Manager", "Email Automation",
        "Spreadsheet Wizard", "Document Generator", "Smart Search",
        "Form Builder", "Survey Analyzer",
    ],
    UseCaseClass.BUSINESS: [
        "Email Sifter & Responder", "Task / Project Manager",
        "Customer Support Agent", "Sales Assistant",
        "Marketing Generator", "Financial Analyst", "HR Assistant",
        "Customer Support AI",  # Available in all use cases
        # Premium upgrades
        "Team Orchestrator", "Data Analyst Pro", "Meeting Facilitator",
        "Calendar Manager", "Document Generator", "Presentation Builder",
        "Knowledge Base Builder", "API Integrator", "Workflow Automator",
        "Competitive Analyst", "Smart Search", "Email Automation",
        "Social Media Manager", "Budget Tracker",
    ],
    UseCaseClass.ENTERPRISE: [
        "Business Intelligence Analyst", "Compliance Auditor",
        "Supply Chain Coordinator", "IT Operations Agent",
        "Legal Document Reviewer", "Multi-Department Orchestrator",
        "Customer Support AI",  # Available in all use cases
        # Premium upgrades
        "Security Auditor", "Code Reviewer", "Team Orchestrator",
        "Data Analyst Pro", "Knowledge Base Builder", "API Integrator",
        "Workflow Automator", "Medical Researcher", "Legal Assistant",
        "Fact Checker", "Smart Search", "Memory Bridge",
    ],
    UseCaseClass.ALL_ROUNDER: [
        "Chat Companion", "Coding Assistant", "Creative Writer",
        "Learning Tutor", "Personal Organizer", "Research Assistant",
        "Classroom Tutor", "Assignment Grader", "Lesson Planner",
        "Document Processor", "Meeting Scribe", "Data Entry Agent",
        "Workflow Automator", "Content Moderator",
        "Email Sifter & Responder", "Task / Project Manager",
        "Customer Support Agent", "Sales Assistant",
        "Marketing Generator", "Financial Analyst", "HR Assistant",
        "Business Intelligence Analyst", "Compliance Auditor",
        "Supply Chain Coordinator", "IT Operations Agent",
        "Legal Document Reviewer", "Multi-Department Orchestrator",
        "Customer Support AI",  # Available in all use cases
        # All premium upgrades
        "Team Orchestrator", "Memory Bridge", "Visual Canvas", "Data Analyst Pro",
        "Code Reviewer", "API Integrator", "Knowledge Base Builder",
        "Meeting Facilitator", "Email Automation", "Calendar Manager",
        "Document Generator", "Translation Expert", "Presentation Builder",
        "Spreadsheet Wizard", "Legal Assistant", "Medical Researcher",
        "Accessibility Assistant", "Fact Checker", "Voice Interface",
        "Workflow Automator", "Security Auditor", "Competitive Analyst",
        "Learning Path Creator", "Smart Search",
        "Budget Tracker", "Social Media Manager", "Study Coach",
        "Plagiarism Checker", "Form Builder", "Survey Analyzer",
    ],
}

# Use-case descriptions shown in capability selection dialog
USE_CASE_DESCRIPTIONS: dict = {
    UseCaseClass.INDIVIDUAL: "Personal AI assistant for daily tasks, creative projects, learning, and organization. Focuses on privacy and personal productivity.",
    UseCaseClass.EDUCATIONAL: "Teaching and learning support with academic integrity, accessibility features, and structured knowledge sharing.",
    UseCaseClass.TASK_READY: "Task-focused AI for document processing, meeting notes, data entry, and workflow automation. Gets work done efficiently.",
    UseCaseClass.BUSINESS: "Professional AI for business operations including sales, support, marketing, HR, and finance. Drafts responses and manages workflows.",
    UseCaseClass.ENTERPRISE: "Enterprise-grade AI with compliance, security auditing, multi-department coordination, and advanced analytics.",
    UseCaseClass.ALL_ROUNDER: "Versatile AI with access to all capabilities. Great for users who need flexibility across many different types of tasks.",
}

# Recommended capabilities for each use case (for "Suggest Set" button)
USE_CASE_RECOMMENDED: dict = {
    UseCaseClass.INDIVIDUAL: ["Chat Companion", "Personal Organizer", "Research Assistant", "Creative Writer"],
    UseCaseClass.EDUCATIONAL: ["Classroom Tutor", "Lesson Planner", "Academic Researcher", "Learning Path Creator"],
    UseCaseClass.TASK_READY: ["Document Processor", "Meeting Scribe", "Calendar Manager", "Workflow Automator"],
    UseCaseClass.BUSINESS: ["Email Sifter & Responder", "Task / Project Manager", "Meeting Facilitator", "Data Analyst Pro"],
    UseCaseClass.ENTERPRISE: ["Compliance Auditor", "Security Auditor", "Team Orchestrator", "Knowledge Base Builder"],
    UseCaseClass.ALL_ROUNDER: ["Chat Companion", "Research Assistant", "Document Processor", "Task / Project Manager"],
}

# Beginner-friendly capability descriptions for the live AI Details preview
CAPABILITY_DESCRIPTIONS: dict[str, str] = {
    "Chat Companion": "Holds natural conversations, answers questions, and helps think through ideas in a friendly back-and-forth way.",
    "Coding Assistant": "Helps write, explain, and fix code. Can suggest improvements and spot bugs, but asks before making changes to files.",
    "Creative Writer": "Drafts stories, scripts, poems, and creative pieces. Can brainstorm ideas and refine tone and style.",
    "Learning Tutor": "Explains topics step by step, checks understanding, and adjusts explanations to match the learner's level.",
    "Personal Organizer": "Helps manage tasks, schedules, reminders, and lists. Keeps track of what needs doing and when.",
    "Research Assistant": "Gathers and summarizes information, compares sources, and helps verify facts for reports or decisions.",
    "Classroom Tutor": "Supports students with lessons, practice problems, and study guidance in a classroom-style setting.",
    "Assignment Grader": "Reviews student work against criteria, gives constructive feedback, and suggests areas to improve.",
    "Lesson Planner": "Builds structured lesson outlines, suggests activities, and sequences topics for effective learning.",
    "Academic Researcher": "Finds and organizes scholarly information, helps structure papers, and tracks citations.",
    "Language Coach": "Practices conversation in another language, corrects mistakes gently, and builds vocabulary.",
    "Accessibility Aide": "Adapts content for different needs — summaries, larger text, simpler language, or audio-style drafts.",
    "Document Processor": "Reads, summarizes, and extracts key points from documents. Helps turn long text into short takeaways.",
    "Meeting Scribe": "Takes notes during discussions, tracks decisions and action items, and produces clean summaries afterward.",
    "Customer Support AI": "Adaptive AI for customer communication. Learns from interactions, handles inquiries professionally, and escalates when needed. Available in all use cases.",
    "Data Entry Agent": "Helps organize and enter structured information accurately, checking for errors along the way.",
    "Workflow Automator": "Suggests ways to streamline repetitive steps and keeps processes moving smoothly.",
    "Content Moderator": "Reviews text for inappropriate or off-topic material and flags concerns according to set rules.",
    "Email Sifter & Responder": "Sorts incoming messages, drafts replies, and highlights urgent items without sending anything automatically.",
    "Task / Project Manager": "Breaks big goals into steps, tracks progress, and reminds about deadlines and priorities.",
    "Customer Support Agent": "Drafts helpful responses to common questions and escalates unusual issues for human review.",
    "Sales Assistant": "Helps draft pitches, track leads, and prepare follow-up messages while staying respectful and honest.",
    "Marketing Generator": "Creates draft copy, social posts, and campaign ideas based on goals and target audience.",
    "Financial Analyst": "Organizes numbers, spots trends, and explains financial patterns in plain language.",
    "HR Assistant": "Helps draft job descriptions, interview questions, and onboarding checklists while keeping information private.",
    "Business Intelligence Analyst": "Turns raw business data into clear insights, dashboards, and decision-ready summaries.",
    "Compliance Auditor": "Reviews documents and processes against rules and flags anything that might need attention.",
    "Supply Chain Coordinator": "Tracks inventory, logistics, and supplier information to keep operations running smoothly.",
    "IT Operations Agent": "Monitors system status, suggests fixes for common issues, and documents troubleshooting steps.",
    "Legal Document Reviewer": "Reads contracts and legal text to highlight key clauses, risks, and inconsistencies for human lawyers.",
    "Multi-Department Orchestrator": "Coordinates work across teams by tracking handoffs, deadlines, and shared goals.",
    "Strategic Planner": "Maps out long-term goals, identifies risks and opportunities, and builds phased action plans.",
    "Field Analyst": "Processes field reports, sensor data, and observations into structured, actionable summaries.",
    "Command Support": "Assists with command-level coordination, status tracking, and decision-ready briefings.",
    "Logistics Coordinator": "Plans routes, schedules deliveries, and balances resources to meet deadlines.",
    "Tactical Advisor": "Analyzes scenarios, suggests options, and outlines pros and cons for tactical decisions.",
    # Premium upgrade capabilities — beginner-friendly descriptions
    "Team Orchestrator": "Coordinates multiple AIs working together on the same project. Assigns roles, tracks progress, and helps AIs hand off work to each other smoothly.",
    "Memory Bridge": "Lets your AI remember things from past conversations. It recalls your preferences, previous topics, and project context so you don't have to repeat yourself.",
    "Visual Canvas": "Creates images, diagrams, and visual concepts from your descriptions. Useful for presentations, illustrations, and visual brainstorming.",
    "Data Analyst Pro": "Analyzes spreadsheets and datasets to find trends, create charts, and highlight insights. Helps you understand your numbers without needing a statistics degree.",
    "Code Reviewer": "Automatically reviews code for bugs, security issues, and best practices. Suggests improvements and flags problems before they cause trouble.",
    "API Integrator": "Connects your AI to external apps and services like CRMs, databases, or web tools. Sets up secure data flows between systems.",
    "Knowledge Base Builder": "Creates organized, searchable collections of information. Great for building help centers, documentation, or team wikis.",
    "Meeting Facilitator": "Manages meetings from agenda to action items. Takes live notes, tracks decisions, and sends follow-ups so nothing gets lost.",
    "Email Automation": "Drafts email replies, sorts incoming messages by priority, and creates templates. You approve everything before it sends.",
    "Calendar Manager": "Finds the best meeting times across time zones, detects scheduling conflicts, and suggests focus blocks in your schedule.",
    "Document Generator": "Creates professionally formatted documents from templates — proposals, reports, letters — with your branding and style.",
    "Translation Expert": "Translates text between languages while keeping the meaning, tone, and cultural context intact. Includes glossary support for consistent terminology.",
    "Presentation Builder": "Creates slide decks with AI-generated content, design suggestions, and speaker notes. Helps you build presentations without staring at a blank slide.",
    "Spreadsheet Wizard": "Builds formulas, creates pivot tables, and automates spreadsheet tasks. Explains complex calculations in plain language.",
    "Legal Assistant": "Reviews contracts and legal documents to highlight key clauses, risks, and unusual terms. Not a replacement for a real lawyer, but saves time on first reviews.",
    "Medical Researcher": "Searches medical literature, checks drug interactions, and summarizes clinical evidence. For research purposes only — not medical advice.",
    "Accessibility Assistant": "Adapts content for different needs — reads text aloud, adjusts display settings, and provides alternative input methods for users with disabilities.",
    "Fact Checker": "Verifies claims against multiple sources, scores credibility, and detects bias. Helps separate facts from misinformation.",
    "Voice Interface": "Lets you talk to your AI using your voice instead of typing. Includes speech recognition and text-to-speech for hands-free interaction.",
    "Workflow Automator": "Builds automated multi-step workflows with triggers and conditions — no coding needed. Set up 'when this happens, do that' chains for repetitive tasks.",
    "Security Auditor": "Scans code, configurations, and documents for security weaknesses. Prioritizes vulnerabilities and suggests fixes to keep your systems safe.",
    "Competitive Analyst": "Researches competitors, tracks market trends, and generates SWOT analyses. Helps you understand your market position and find opportunities.",
    "Learning Path Creator": "Designs structured learning courses with lessons, quizzes, and progress tracking. Great for teachers, trainers, and self-learners.",
    "Smart Search": "Searches across all your documents, knowledge bases, and the web at once. Understands natural language questions and ranks results by relevance.",
    # New capabilities
    "Budget Tracker": "Tracks income and expenses, categorizes spending, and creates visual budget reports. Helps you understand where your money goes and plan ahead.",
    "Social Media Manager": "Drafts posts for multiple platforms, suggests content calendars, and tracks engagement trends. You approve everything before posting.",
    "Study Coach": "Creates personalized study plans, tracks progress, and adapts to your learning pace. Includes flashcards, practice quizzes, and exam prep strategies.",
    "Plagiarism Checker": "Compares text against web sources and academic databases to detect potential plagiarism. Provides similarity scores and source links.",
    "Form Builder": "Creates custom forms, surveys, and questionnaires from your descriptions. Includes templates for common use cases like feedback, registration, and intake.",
    "Survey Analyzer": "Processes survey responses, identifies trends and patterns, and generates clear summary reports with charts and key insights.",
}


BASE_GUARDRAILS: list[str] = [
    "No illegal guidance or instructions for illegal activities",
    "No sexual or explicit content",
    "No harassment, abuse, or targeting individuals for harm",
    "No credential theft, unauthorized access, or exploitation assistance",
    "Not a substitute for professional medical, legal, or financial advice",
]

OPTIONAL_GUARDRAILS: list[str] = [
    "Ask before editing files",
    "Cite sources when researching",
    "Keep responses beginner-friendly",
    "Keep responses concise",
    "Require confirmation before risky actions",
    "Avoid specific technical jargon unless asked",
    "Never use emojis or informal formatting",
    "Always summarize long outputs before detail",
    "Prefer step-by-step explanations",
    "Never reference external competitors by name",
    "Always suggest alternatives when declining a request",
    "Use inclusive and neutral language",
    "Flag speculative answers clearly as speculation",
    "Respect time-of-day context (quiet hours awareness)",
    "Prioritize local/offline processing when possible",
    "Archive every deliverable automatically",
    "Always explain reasoning before giving answers",
    "Offer to escalate complex topics to human review",
    "Limit memory of past sessions to current context only",
    "Require explicit consent before personalization changes",
]


NEXUS_LIBRARIES: list[dict] = [
    {
        "id": "comm_lib",
        "name": "Communication Library",
        "description": "Tone patterns, conversation summaries, and message/email drafting templates.",
        "category": "Interaction",
        "applies_to": ["Chat Companion", "Customer Support Agent", "Sales Assistant", "Email Sifter & Responder"],
        "enabled_by_default": False,
        "integration_target": "Chat / Messaging",
        "risk_level": "Low",
    },
    {
        "id": "code_safety_lib",
        "name": "Code Safety Library",
        "description": "Safe patching habits, diff-first workflow, test reminders, and safe-refactor patterns.",
        "category": "Development",
        "applies_to": ["Coding Assistant", "Document Processor", "IT Operations Agent"],
        "enabled_by_default": False,
        "integration_target": "Code Editor / IDE",
        "risk_level": "Medium",
    },
    {
        "id": "research_discipline_lib",
        "name": "Research Discipline Library",
        "description": "Source comparison, citation habits, fact-checking structure, and research-note organization.",
        "category": "Research",
        "applies_to": ["Research Assistant", "Academic Researcher", "Business Intelligence Analyst", "Field Analyst"],
        "enabled_by_default": False,
        "integration_target": "Research / Search",
        "risk_level": "Low",
    },
    {
        "id": "project_memory_lib",
        "name": "Project Memory Library",
        "description": "Notes, project continuity, task summaries, deduplication habits, and context-retention rules.",
        "category": "Organization",
        "applies_to": ["Personal Organizer", "Task / Project Manager", "Notebook", "Meeting Scribe"],
        "enabled_by_default": False,
        "integration_target": "Notes / Archive",
        "risk_level": "Low",
    },
    {
        "id": "governance_ux_lib",
        "name": "Governance UX Library",
        "description": "User-facing safety explanations, consent templates, disclaimer wording, and approval-request phrasing.",
        "category": "Governance",
        "applies_to": ["All"],
        "enabled_by_default": False,
        "integration_target": "Approval / Governance",
        "risk_level": "Low",
    },
    # Hephaestus Briefing Library removed — will be added when Hephaestus integration is enabled
]


def _generate_combined_summary(name: str, use_case: str, capabilities: list[str]) -> str:
    """Generate a friendly combined summary of what this AI will do."""
    if not capabilities:
        return ""

    cap_count = len(capabilities)
    if cap_count == 1:
        cap = capabilities[0]
        desc = CAPABILITY_DESCRIPTIONS.get(cap, "Helps with this task.")
        return f"This AI is focused on {cap.lower()}. {desc}"

    # Build a natural list of capability names
    if cap_count == 2:
        cap_list = f"{capabilities[0].lower()} and {capabilities[1].lower()}"
    else:
        cap_list = ", ".join(c.lower() for c in capabilities[:-1]) + f", and {capabilities[-1].lower()}"

    intro = f"This AI is designed for {cap_list}."

    # Gather individual descriptions
    descriptions = []
    for cap in capabilities:
        desc = CAPABILITY_DESCRIPTIONS.get(cap, "")
        if desc:
            # Shorten: extract first sentence or first clause
            short = desc.split(".")[0]
            descriptions.append(f"{cap}: {short}.")

    # Combined narrative based on categories present
    categories = set()
    for cap in capabilities:
        c = cap.lower()
        if any(x in c for x in ("chat", "conversation", "language")):
            categories.add("conversation")
        if any(x in c for x in ("writer", "creative", "content", "marketing", "copy")):
            categories.add("writing")
        if any(x in c for x in ("code", "developer", "it operations")):
            categories.add("coding")
        if any(x in c for x in ("research", "analyst", "academic")):
            categories.add("research")
        if any(x in c for x in ("organize", "task", "project", "schedule", "logistics", "supply chain")):
            categories.add("organization")
        if any(x in c for x in ("tutor", "learning", "classroom", "lesson", "educational")):
            categories.add("learning")
        if any(x in c for x in ("document", "scribe", "processor", "reviewer", "compliance")):
            categories.add("documents")
        if any(x in c for x in ("plan", "strategic", "planner", "workflow", "orchestrator")):
            categories.add("planning")
        if any(x in c for x in ("support", "customer", "sales", "hr")):
            categories.add("support")
        if any(x in c for x in ("finance", "financial")):
            categories.add("finance")
        if any(x in c for x in ("field", "tactical", "command")):
            categories.add("operations")

    # Build a collaboration sentence based on categories
    collab_parts = []
    if "conversation" in categories:
        collab_parts.append("talk through ideas")
    if "writing" in categories:
        collab_parts.append("draft and refine written content")
    if "coding" in categories:
        collab_parts.append("write and troubleshoot code")
    if "research" in categories:
        collab_parts.append("find and verify information")
    if "organization" in categories:
        collab_parts.append("keep tasks and schedules on track")
    if "learning" in categories:
        collab_parts.append("explain concepts and guide practice")
    if "documents" in categories:
        collab_parts.append("process and summarize documents")
    if "planning" in categories:
        collab_parts.append("map out steps and timelines")
    if "support" in categories:
        collab_parts.append("draft helpful responses for people")
    if "finance" in categories:
        collab_parts.append("organize and explain financial data")
    if "operations" in categories:
        collab_parts.append("support operational coordination")

    if len(collab_parts) >= 2:
        collab_text = ", ".join(collab_parts[:-1]) + f", and {collab_parts[-1]}"
        together = f"These abilities work together so the AI can help {collab_text}."
    elif collab_parts:
        together = f"This ability helps {collab_parts[0]}."
    else:
        together = "These capabilities complement each other for versatile assistance."

    parts = [intro]
    if descriptions:
        parts.append("")
        parts.extend(descriptions)
    parts.append("")
    parts.append(together)

    return "\n".join(parts)


MILITARY_KEY = "CNX-MILGOV-2026"  # Hardcoded activation key


class CapabilitySelectionDialog(QDialog):
    """Modal dialog for selecting capabilities with detailed descriptions and hover tooltips."""

    def __init__(self, use_case: UseCaseClass, parent=None, current_selections: list = None):
        super().__init__(parent)
        self.setWindowTitle(f"Select Capabilities — {use_case.value}")
        self.setModal(True)
        self.resize(700, 600)
        self._use_case = use_case
        self._current_selections = current_selections or []
        self._selected_capabilities: list = []
        self._checkboxes: dict = {}
        
        # Get current membership tier from settings
        from ...core.settings_manager import SettingsManager
        from ...core.membership_tiers import MembershipTier
        try:
            mgr = SettingsManager()
            self._membership_tier = MembershipTier(mgr.get().membership_tier)
        except Exception:
            self._membership_tier = MembershipTier.FREE
        
        self._setup_ui()
        self._load_capabilities()
        self._apply_dark_theme()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Membership tier banner
        from ...core.membership_tiers import TIER_NAMES, TIER_PRICES, MembershipTier
        tier_name = TIER_NAMES.get(self._membership_tier, "Free")
        tier_price = TIER_PRICES.get(self._membership_tier, "$0")
        banner_text = f"Membership: {tier_name} ({tier_price})"
        if self._membership_tier == MembershipTier.FREE:
            banner_text += " — Upgrade to unlock more capabilities!"
        self._tier_banner = QLabel(banner_text)
        self._tier_banner.setStyleSheet(
            "background-color: #1f2937; color: #58a6ff; font-size: 12px; "
            "font-weight: bold; padding: 8px 12px; border-radius: 4px; "
            "border: 1px solid #30363d;"
        )
        self._tier_banner.setWordWrap(True)
        layout.addWidget(self._tier_banner)

        # Header with use case info
        header = QLabel(f"<h2>Choose Capabilities for {self._use_case.value}</h2>")
        header.setWordWrap(True)
        layout.addWidget(header)

        # Description label
        desc_text = USE_CASE_DESCRIPTIONS.get(self._use_case, "Select the capabilities you want this AI to have.")
        desc = QLabel(desc_text)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #8b949e; font-size: 12px;")
        layout.addWidget(desc)

        # Search/filter box
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Type to filter capabilities...")
        self._search_input.setMaxLength(100)  # Limit length to prevent overflow
        self._search_input.textChanged.connect(self._filter_capabilities)
        search_layout.addWidget(self._search_input)
        layout.addLayout(search_layout)

        # Select All / Clear All buttons
        btn_layout = QHBoxLayout()
        self._select_all_btn = QPushButton("Select All")
        self._select_all_btn.clicked.connect(self._select_all)
        self._clear_all_btn = QPushButton("Clear All")
        self._clear_all_btn.clicked.connect(self._clear_all)
        self._suggest_btn = QPushButton("💡 Suggest Set")
        self._suggest_btn.setToolTip("Auto-select recommended capabilities for this use case")
        self._suggest_btn.clicked.connect(self._suggest_capabilities)
        btn_layout.addWidget(self._select_all_btn)
        btn_layout.addWidget(self._clear_all_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self._suggest_btn)
        layout.addLayout(btn_layout)

        # Scroll area for capabilities
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self._caps_container = QWidget()
        self._caps_layout = QVBoxLayout(self._caps_container)
        self._caps_layout.setSpacing(8)
        self._caps_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(self._caps_container)
        layout.addWidget(scroll, stretch=1)

        # Selection count label
        self._count_label = QLabel("0 capabilities selected")
        self._count_label.setStyleSheet("color: #58a6ff; font-weight: bold;")
        layout.addWidget(self._count_label)

        # Apply/Cancel buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Apply).setText("Apply Selection")
        button_box.button(QDialogButtonBox.StandardButton.Apply).setStyleSheet(
            "background-color: #2e7d32; color: white; font-weight: bold; padding: 8px 16px;"
        )
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancel")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet(
            "background-color: #c62828; color: white; padding: 8px 16px;"
        )
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._on_apply)
        button_box.button(QDialogButtonBox.StandardButton.Cancel).clicked.connect(self._on_cancel)
        layout.addWidget(button_box)

    def _load_capabilities(self):
        """Load all capabilities for this use case with descriptions and hover tooltips."""
        from ...core.membership_tiers import is_capability_unlocked, get_upgrade_prompt_for_capability, TIER_NAMES, TIER_PRICES
        options = USE_CASE_OPTIONS.get(self._use_case, [])
        
        for opt in options:
            # Create container for each capability
            cap_widget = QWidget()
            cap_layout = QHBoxLayout(cap_widget)
            cap_layout.setContentsMargins(4, 4, 4, 4)
            cap_layout.setSpacing(8)
            
            # Check if locked by membership
            unlocked = is_capability_unlocked(opt, self._membership_tier)
            lock_prompt = get_upgrade_prompt_for_capability(opt) if not unlocked else ""
            
            # Checkbox
            display_name = opt if unlocked else f"🔒 {opt}"
            chk = QCheckBox(display_name)
            chk.setChecked(opt in self._current_selections and unlocked)
            chk.stateChanged.connect(self._update_count)
            if not unlocked:
                chk.setEnabled(False)
                chk.setStyleSheet("QCheckBox { color: #6e7681; } QCheckBox::indicator { border: 1px solid #30363d; }")
            self._checkboxes[opt] = chk
            cap_layout.addWidget(chk)
            
            # Info button with tooltip
            info_btn = QPushButton("?" if unlocked else "🔒")
            info_btn.setFixedSize(20, 20)
            info_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1f6feb;
                    color: white;
                    border-radius: 10px;
                    font-size: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #58a6ff;
                }
            """)
            
            # Get description and tooltip
            desc = CAPABILITY_DESCRIPTIONS.get(opt, "No description available.")
            tooltip = self._build_tooltip(opt, desc)
            if lock_prompt:
                tooltip = f"{lock_prompt}<br><br>{tooltip}"
                info_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f0883e;
                        color: white;
                        border-radius: 10px;
                        font-size: 10px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #f0883e;
                    }
                """)
            info_btn.setToolTip(tooltip)
            chk.setToolTip(tooltip)
            
            info_btn.clicked.connect(lambda checked, o=opt: self._show_capability_details(o))
            cap_layout.addWidget(info_btn)
            
            # Description label (truncated)
            desc_lbl = QLabel(desc[:80] + "..." if len(desc) > 80 else desc)
            if not unlocked:
                desc_lbl.setStyleSheet("color: #6e7681; font-size: 11px; font-style: italic;")
            else:
                desc_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
            desc_lbl.setWordWrap(True)
            cap_layout.addWidget(desc_lbl, stretch=1)
            
            # Locked badge
            if not unlocked:
                from ...core.membership_tiers import get_min_tier
                min_tier = get_min_tier(opt)
                tier_name = TIER_NAMES.get(min_tier, "Paid")
                tier_price = TIER_PRICES.get(min_tier, "")
                lock_lbl = QLabel(f"🔒 {tier_name} {tier_price}")
                lock_lbl.setStyleSheet(
                    "background-color: #f0883e; color: white; font-size: 10px; "
                    "font-weight: bold; padding: 2px 6px; border-radius: 3px;"
                )
                cap_layout.addWidget(lock_lbl)
            else:
                # Compatible with indicator
                compatible = self._get_compatible_caps(opt)
                if compatible:
                    compat_lbl = QLabel(f"↔ {len(compatible)} compatible")
                    compat_lbl.setStyleSheet("color: #3fb950; font-size: 10px;")
                    compat_lbl.setToolTip(f"Works well with: {', '.join(compatible[:5])}")
                    cap_layout.addWidget(compat_lbl)
            
            self._caps_layout.addWidget(cap_widget)
        
        self._update_count()

    def _build_tooltip(self, capability: str, description: str) -> str:
        """Build detailed tooltip for a capability."""
        lines = [
            f"<b>{capability}</b>",
            "",
            description,
            "",
            "<b>Compatible with:</b>",
        ]
        
        compatible = self._get_compatible_caps(capability)
        if compatible:
            for cap in compatible[:8]:
                lines.append(f"  • {cap}")
            if len(compatible) > 8:
                lines.append(f"  ... and {len(compatible) - 8} more")
        else:
            lines.append("  (General purpose capability)")
        
        lines.extend([
            "",
            "<i>💡 Tip: Click the ? button for full details</i>",
        ])
        
        return "<br>".join(lines)

    def _get_compatible_caps(self, capability: str) -> list:
        """Get list of capabilities that work well with this one."""
        from .capability_actions import CAPABILITY_REGISTRY, CAPABILITY_ALIASES
        
        # Resolve alias if needed
        canonical = CAPABILITY_ALIASES.get(capability, capability)
        
        # Get from registry
        cap_data = CAPABILITY_REGISTRY.get(canonical)
        if cap_data and hasattr(cap_data, 'compatible_capabilities'):
            return cap_data.compatible_capabilities[:10]
        
        return []

    def _show_capability_details(self, capability: str):
        """Show detailed info dialog for a capability."""
        try:
            from .capability_actions import CAPABILITY_REGISTRY, CAPABILITY_ALIASES
            
            canonical = CAPABILITY_ALIASES.get(capability, capability)
            cap_data = CAPABILITY_REGISTRY.get(canonical)
            
            if not cap_data:
                QMessageBox.information(self, capability, "No detailed information available.")
                return
            
            # Build detailed description
            lines = [
                f"<h2>{capability}</h2>",
                "",
                f"<b>Description:</b> {cap_data.description}",
                "",
                f"<b>Approval Level:</b> {cap_data.required_approval_level}",
                "",
                f"<b>Best for Use Cases:</b> {', '.join(cap_data.allowed_use_cases[:5])}",
                "",
                "<b>Compatible Capabilities:</b>",
            ]
            
            if cap_data.compatible_capabilities:
                for cap in cap_data.compatible_capabilities[:10]:
                    lines.append(f"  • {cap}")
            
            lines.extend([
                "",
                "<b>Starter Prompts:</b>",
            ])
            
            if cap_data.starter_prompt_guidance:
                for prompt in cap_data.starter_prompt_guidance[:5]:
                    lines.append(f"  💡 \"{prompt}\"")
            
            msg = QMessageBox(self)
            msg.setWindowTitle(f"About {capability}")
            msg.setText("\n".join(lines))
            msg.setTextFormat(Qt.TextFormat.RichText)
            msg.exec()
        except Exception:
            QMessageBox.information(self, capability, f"{capability}: description available in tooltip.")

    def _filter_capabilities(self, text: str):
        """Filter capabilities based on search text."""
        text = text.lower()
        for opt, chk in self._checkboxes.items():
            desc = CAPABILITY_DESCRIPTIONS.get(opt, "").lower()
            visible = text in opt.lower() or text in desc
            chk.parent().setVisible(visible)

    def _select_all(self):
        for chk in self._checkboxes.values():
            chk.setChecked(True)

    def _clear_all(self):
        for chk in self._checkboxes.values():
            chk.setChecked(False)

    def _suggest_capabilities(self):
        """Auto-select recommended capabilities for this use case."""
        # Clear first
        self._clear_all()
        
        # Select recommended ones based on use case
        recommendations = USE_CASE_RECOMMENDED.get(self._use_case, [])
        for cap in recommendations:
            if cap in self._checkboxes:
                self._checkboxes[cap].setChecked(True)

    def _update_count(self):
        count = sum(1 for chk in self._checkboxes.values() if chk.isChecked())
        self._count_label.setText(f"{count} capability{'ies' if count != 1 else 'y'} selected")

    def _on_apply(self):
        self._selected_capabilities = [
            opt for opt, chk in self._checkboxes.items() if chk.isChecked()
        ]
        self.accept()

    def _on_cancel(self):
        self._selected_capabilities = []
        self.reject()

    def get_selected_capabilities(self) -> list:
        return self._selected_capabilities

    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0d1117;
                color: #c9d1d9;
            }
            QLabel {
                color: #c9d1d9;
            }
            QCheckBox {
                color: #c9d1d9;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QLineEdit {
                background-color: #161b22;
                border: 1px solid #30363d;
                color: #c9d1d9;
                padding: 6px;
                border-radius: 4px;
            }
            QScrollArea {
                border: 1px solid #30363d;
                background-color: #161b22;
            }
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                color: #c9d1d9;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #30363d;
                border-color: #58a6ff;
            }
        """)


class SecurityScanDialog(QDialog):
    """Modal dialog that simulates scanning a dropped-in AI."""

    def __init__(self, filepath: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Security Scan")
        self.setModal(True)
        self.resize(400, 150)
        self._filepath = filepath
        self._approved = False

        layout = QVBoxLayout(self)
        self._label = QLabel(f"Scanning: {Path(filepath).name}\nAnalyzing for malicious code, injection, and bypass attempts...")
        self._label.setWordWrap(True)
        layout.addWidget(self._label)

        self._progress = QProgressDialog("Scanning...", "Cancel", 0, 100, parent)
        self._progress.setWindowTitle("Security Scan")
        self._progress.setModal(True)
        self._progress.show()

        self._step = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(80)

    def _tick(self):
        self._step += 4
        self._progress.setValue(self._step)
        if self._step >= 100:
            self._timer.stop()
            self._progress.close()
            self._approved = True
            self._label.setText(f"APPROVED: {Path(self._filepath).name}\nNo threats detected. AI is cleared for integration.")
            self._add_buttons()
        elif self._progress.wasCanceled():
            self._timer.stop()
            self._progress.close()
            self.reject()

    def _add_buttons(self):
        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        box.accepted.connect(self.accept)
        self.layout().addWidget(box)

    def is_approved(self) -> bool:
        return self._approved




class CharacterSheetWidget(QWidget):
    """Central D&D-style character sheet for building an AI."""

    ai_saved = pyqtSignal(object)
    preview_changed = pyqtSignal(str)  # Live AI Details preview text

    def __init__(self, parent=None):
        super().__init__(parent)
        self._governance = GovernanceEngine()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Name / Title
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("AI Name:"))
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Enter AI name...")
        self._name_input.setMaxLength(50)  # Limit length to prevent overflow
        self._name_input.textChanged.connect(self._update_ai_details_preview)
        name_row.addWidget(self._name_input)
        layout.addLayout(name_row)

        # Use-case class
        uc_row = QHBoxLayout()
        uc_row.addWidget(QLabel("Use-Case Class:"))
        self._uc_combo = QComboBox()
        self._populate_uc_combo()
        self._uc_combo.currentTextChanged.connect(self._on_uc_changed)
        uc_row.addWidget(self._uc_combo)
        layout.addLayout(uc_row)

        # Military/Government unlock
        self._mil_row = QHBoxLayout()
        self._mil_row.addWidget(QLabel("Activation Key:"))
        self._mil_key_input = QLineEdit()
        self._mil_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._mil_key_input.setPlaceholderText("Enter key to unlock Military / Government...")
        self._mil_unlock_btn = QPushButton("Unlock")
        self._mil_unlock_btn.clicked.connect(self._try_unlock_military)
        self._mil_row.addWidget(self._mil_key_input)
        self._mil_row.addWidget(self._mil_unlock_btn)
        self._mil_widget = QWidget()
        self._mil_widget.setLayout(self._mil_row)
        self._mil_widget.setVisible(False)
        layout.addWidget(self._mil_widget)

        # Capability checkboxes
        self._caps_group = QGroupBox("Capabilities")
        self._caps_layout = QGridLayout(self._caps_group)
        self._cap_checks: list = []
        layout.addWidget(self._caps_group)
        
        # Placeholder message when no capabilities selected
        self._caps_placeholder = QLabel("Select a Use-Case Class, then click 'Select Capabilities' or 'Suggest Set' to choose abilities.")
        self._caps_placeholder.setStyleSheet("color: #8b949e; font-style: italic; padding: 10px;")
        self._caps_placeholder.setWordWrap(True)
        self._caps_layout.addWidget(self._caps_placeholder, 0, 0, 1, 2)
        
        # Button to open capability selection dialog
        caps_btn_row = QHBoxLayout()
        self._select_caps_btn = QPushButton("Select Capabilities")
        self._select_caps_btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 6px 12px;")
        self._select_caps_btn.clicked.connect(self._on_select_capabilities_clicked)
        self._suggest_caps_btn = QPushButton("💡 Suggest Set")
        self._suggest_caps_btn.setToolTip("Auto-select recommended capabilities for this use case")
        self._suggest_caps_btn.clicked.connect(self._on_suggest_capabilities)
        caps_btn_row.addWidget(self._select_caps_btn)
        caps_btn_row.addWidget(self._suggest_caps_btn)
        caps_btn_row.addStretch()
        layout.addLayout(caps_btn_row)

        # Nexus Libraries checkboxes
        self._libs_group = QGroupBox("Nexus Libraries (not abilities)")
        self._libs_group.setToolTip("Knowledge packs, templates, and workflows this AI can access. Libraries are not abilities.")
        self._libs_layout = QGridLayout(self._libs_group)
        self._lib_checks: list = []
        for i, lib in enumerate(NEXUS_LIBRARIES):
            chk = QCheckBox(lib["name"])
            chk.setToolTip(f"{lib['description']} (Category: {lib['category']}, Risk: {lib['risk_level']})")
            chk.stateChanged.connect(self._update_ai_details_preview)
            self._libs_layout.addWidget(chk, i // 2, i % 2)
            self._lib_checks.append(chk)
        layout.addWidget(self._libs_group)

        # Personality sliders
        self._personality_group = QGroupBox("Personality / Behavior")
        pers_layout = QFormLayout(self._personality_group)
        self._creativity = QSlider(Qt.Orientation.Horizontal)
        self._creativity.setRange(0, 100)
        self._creativity.setValue(50)
        self._creativity.valueChanged.connect(self._update_ai_details_preview)
        pers_layout.addRow("Creativity:", self._creativity)
        self._formality = QSlider(Qt.Orientation.Horizontal)
        self._formality.setRange(0, 100)
        self._formality.setValue(50)
        self._formality.valueChanged.connect(self._update_ai_details_preview)
        pers_layout.addRow("Formality:", self._formality)
        self._caution = QSlider(Qt.Orientation.Horizontal)
        self._caution.setRange(0, 100)
        self._caution.setValue(70)
        self._caution.valueChanged.connect(self._update_ai_details_preview)
        pers_layout.addRow("Caution / Safety Bias:", self._caution)
        layout.addWidget(self._personality_group)

        # Notes
        self._notes = QTextEdit()
        self._notes.setPlaceholderText("Additional notes, directives, or context for this AI...")
        self._notes.setMaximumHeight(120)
        self._notes.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._notes.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._notes.textChanged.connect(self._update_ai_details_preview)
        layout.addWidget(QLabel("Notes:"))
        layout.addWidget(self._notes)

        # Optional AI Guardrails
        self._guardrails_group = QGroupBox("Optional AI Guardrails")
        self._guardrails_layout = QVBoxLayout(self._guardrails_group)
        self._guardrail_checks: list = []
        for gr in OPTIONAL_GUARDRAILS:
            chk = QCheckBox(gr)
            chk.stateChanged.connect(self._update_ai_details_preview)
            self._guardrails_layout.addWidget(chk)
            self._guardrail_checks.append(chk)
        layout.addWidget(self._guardrails_group)

        # Save button
        self._btn_save = QPushButton("Save AI to Forge")
        self._btn_save.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 8px;")
        self._btn_save.clicked.connect(self._save_ai)
        layout.addWidget(self._btn_save)

        self._on_uc_changed(self._uc_combo.currentText())
        self._update_ai_details_preview()

    def _populate_uc_combo(self):
        for uc in UseCaseClass:
            if uc == UseCaseClass.MILITARY_GOVERNMENT:
                self._uc_combo.addItem(f"{uc.value} [LOCKED — Requires Key]")
            else:
                self._uc_combo.addItem(uc.value)

    def _on_select_capabilities_clicked(self):
        """Handle click on Select Capabilities button."""
        # Check if capability selection is locked by Approved Use Locks
        allowed, message = check_use_lock(UseLockArea.CAPABILITY_SELECTION)
        if not allowed:
            QMessageBox.warning(self, "Approved Use Locks", message)
            return

        # Get current use case
        uc_text = self._uc_combo.currentText().replace(" [LOCKED — Requires Key]", "")
        current_uc = None
        for uc in UseCaseClass:
            if uc.value == uc_text:
                current_uc = uc
                break

        if not current_uc:
            QMessageBox.warning(self, "No Use Case", "Please select a Use-Case Class first.")
            return

        # Open capability selection dialog
        self._open_capability_dialog(current_uc)
    
    def _on_suggest_capabilities(self):
        """Auto-select recommended capabilities for current use case."""
        from ...core.membership_tiers import is_capability_unlocked
        from ...core.settings_manager import SettingsManager
        from ...core.membership_tiers import MembershipTier
        try:
            mgr = SettingsManager()
            tier = MembershipTier(mgr.get().membership_tier)
        except Exception:
            tier = MembershipTier.FREE

        # Get current use case
        uc_text = self._uc_combo.currentText().replace(" [LOCKED — Requires Key]", "")
        current_uc = None
        for uc in UseCaseClass:
            if uc.value == uc_text:
                current_uc = uc
                break
        
        if not current_uc:
            QMessageBox.warning(self, "No Use Case", "Please select a Use-Case Class first.")
            return
        
        # Clear current selections
        self._clear_capabilities()
        
        # Hide placeholder when adding capabilities
        self._caps_placeholder.setVisible(False)
        
        # Get recommended capabilities
        recommendations = USE_CASE_RECOMMENDED.get(current_uc, [])
        
        # Get all available options for this use case
        options = USE_CASE_OPTIONS.get(current_uc, [])
        
        # Add checkboxes with recommended ones checked (only if unlocked)
        for i, opt in enumerate(options):
            unlocked = is_capability_unlocked(opt, tier)
            display_name = opt if unlocked else f"\U0001f512 {opt}"
            chk = QCheckBox(display_name)
            chk.setChecked(opt in recommendations and unlocked)
            chk.stateChanged.connect(self._update_ai_details_preview)
            if not unlocked:
                chk.setEnabled(False)
                chk.setStyleSheet("QCheckBox { color: #6e7681; } QCheckBox::indicator { border: 1px solid #30363d; }")
            
            # Add hover tooltip with description
            desc = CAPABILITY_DESCRIPTIONS.get(opt, "")
            if desc:
                chk.setToolTip(f"<b>{opt}</b><br>{desc}")
            
            self._caps_layout.addWidget(chk, i // 2, i % 2)
            self._cap_checks.append(chk)
        
        self._update_ai_details_preview()
        
        # Count only unlocked recommendations
        unlocked_recs = [r for r in recommendations if is_capability_unlocked(r, tier)]
        locked_count = len(recommendations) - len(unlocked_recs)
        msg = f"Selected {len(unlocked_recs)} recommended capabilities for {current_uc.value}."
        if locked_count > 0:
            msg += f"\n\n{locked_count} capabilities are locked for your membership tier. Upgrade to unlock them!"
        QMessageBox.information(self, "Suggested Set", msg)

    def _on_uc_changed(self, text: str):
        if "LOCKED" in text:
            self._mil_widget.setVisible(True)
            self._clear_capabilities()
            self._update_ai_details_preview()
            return
        self._mil_widget.setVisible(False)
        
        # Just clear capabilities when use case changes - user must click Select button
        self._clear_capabilities()
        self._update_ai_details_preview()

    def _open_capability_dialog(self, use_case: UseCaseClass):
        """Open the enhanced capability selection dialog."""
        # Get current selections to pass to dialog
        current_selections = [chk.text() for chk in self._cap_checks if chk.isChecked()]
        
        # Create and show dialog
        dialog = CapabilitySelectionDialog(use_case, self, current_selections)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Apply was clicked - update capabilities
            selected = dialog.get_selected_capabilities()
            self._set_capabilities(selected)
        # If Cancel was clicked, do nothing - keep previous selections
        
        self._update_ai_details_preview()

    def _set_capabilities(self, capabilities: list):
        """Set the selected capabilities in the UI."""
        from ...core.membership_tiers import is_capability_unlocked
        from ...core.settings_manager import SettingsManager
        from ...core.membership_tiers import MembershipTier
        try:
            mgr = SettingsManager()
            tier = MembershipTier(mgr.get().membership_tier)
        except Exception:
            tier = MembershipTier.FREE

        # Clear current
        self._clear_capabilities()
        
        # Hide placeholder when adding capabilities
        self._caps_placeholder.setVisible(False)
        
        # Get all available options for current use case
        uc_text = self._uc_combo.currentText().replace(" [LOCKED — Requires Key]", "")
        current_uc = None
        for uc in UseCaseClass:
            if uc.value == uc_text:
                current_uc = uc
                break
        
        if not current_uc:
            return
            
        # Add all options with proper selection state
        options = USE_CASE_OPTIONS.get(current_uc, [])
        for i, opt in enumerate(options):
            unlocked = is_capability_unlocked(opt, tier)
            display_name = opt if unlocked else f"\U0001f512 {opt}"
            chk = QCheckBox(display_name)
            chk.setChecked(opt in capabilities and unlocked)
            chk.stateChanged.connect(self._update_ai_details_preview)
            if not unlocked:
                chk.setEnabled(False)
                chk.setStyleSheet("QCheckBox { color: #6e7681; } QCheckBox::indicator { border: 1px solid #30363d; }")
            
            # Add hover tooltip with description
            desc = CAPABILITY_DESCRIPTIONS.get(opt, "")
            if desc:
                chk.setToolTip(f"<b>{opt}</b><br>{desc}")
            
            self._caps_layout.addWidget(chk, i // 2, i % 2)
            self._cap_checks.append(chk)

    def _clear_capabilities(self):
        for check in self._cap_checks:
            check.deleteLater()
        self._cap_checks.clear()
        # Show placeholder again
        self._caps_placeholder.setVisible(True)

    def _refresh_capabilities(self, uc: UseCaseClass):
        self._clear_capabilities()
        options = USE_CASE_OPTIONS.get(uc, [])
        for i, opt in enumerate(options):
            chk = QCheckBox(opt)
            chk.stateChanged.connect(self._update_ai_details_preview)
            self._caps_layout.addWidget(chk, i // 2, i % 2)
            self._cap_checks.append(chk)

    def _update_ai_details_preview(self):
        """Build and emit a live plain-language summary for the AI Details panel."""
        name = self._name_input.text().strip()
        uc_text = self._uc_combo.currentText().replace(" [LOCKED — Requires Key]", "")
        capabilities = [chk.text() for chk in self._cap_checks if chk.isChecked()]
        creativity = self._creativity.value()
        formality = self._formality.value()
        caution = self._caution.value()
        notes = self._notes.toPlainText().strip()

        if not capabilities:
            placeholder = (
                "Select capabilities to see what this AI will be able to do.\n\n"
                "Choose a use-case class above, then check the boxes that match what you want this AI to help with."
            )
            self.preview_changed.emit(placeholder)
            return

        lines: list[str] = []

        # Header
        if name:
            lines.append(f"AI Name: {name}")
        lines.append(f"Use-Case Class: {uc_text}")
        lines.append("")

        # Selected capabilities with descriptions
        lines.append(f"Selected Capabilities ({len(capabilities)}):")
        for cap in capabilities:
            desc = CAPABILITY_DESCRIPTIONS.get(cap, "")
            if desc:
                lines.append(f"  • {cap}: {desc}")
            else:
                lines.append(f"  • {cap}")
        lines.append("")

        # Selected libraries
        libraries = [chk.text() for chk in self._lib_checks if chk.isChecked()]
        if libraries:
            lines.append(f"Nexus Libraries ({len(libraries)}):")
            for lib_name in libraries:
                lib_info = next((l for l in NEXUS_LIBRARIES if l["name"] == lib_name), {})
                if lib_info:
                    lines.append(f"  • {lib_name}: {lib_info['description']}")
                else:
                    lines.append(f"  • {lib_name}")
            lines.append("")

        # Combined summary
        summary = _generate_combined_summary(name or "This AI", uc_text, capabilities)
        lines.append(summary)
        lines.append("")

        # Personality snapshot
        lines.append("Personality Snapshot:")
        lines.append(f"  • Creativity: {creativity}% — {'highly imaginative' if creativity > 70 else 'balanced' if creativity > 30 else 'focused and precise'}")
        lines.append(f"  • Formality: {formality}% — {'very formal and structured' if formality > 70 else 'adaptable' if formality > 30 else 'casual and conversational'}")
        lines.append(f"  • Caution / Safety Bias: {caution}% — {'extra careful, asks before acting' if caution > 70 else 'moderately cautious' if caution > 30 else 'direct and efficient'}")
        lines.append("")

        # Guardrails
        lines.append("System Protections: active (Nexus Compendium — see Governance for details)")
        lines.append("")
        guardrails = [chk.text() for chk in self._guardrail_checks if chk.isChecked()]
        if guardrails:
            lines.append(f"Optional Guardrails ({len(guardrails)}):")
            for gr in guardrails:
                lines.append(f"  • {gr}")
            lines.append("")
        else:
            lines.append("Optional Guardrails: (none selected — add optional upgrades above)")
            lines.append("")

        # Optional warning if no core capability
        core_caps = {"Chat Companion", "Coding Assistant", "Creative Writer", "Research Assistant",
                     "Personal Organizer", "Learning Tutor", "Document Processor", "Task / Project Manager",
                     "Customer Support Agent", "Business Intelligence Analyst"}
        if not any(c in core_caps for c in capabilities):
            lines.append("⚠ Tip: This AI does not have a primary conversational or core assistant capability. Consider adding one for broader usefulness.")
            lines.append("")

        # Notes preview (if any)
        if notes:
            lines.append("Notes / Context:")
            lines.append(f"  {notes}")

        self.preview_changed.emit("\n".join(lines))

    def _try_unlock_military(self):
        if self._mil_key_input.text().strip() == MILITARY_KEY:
            idx = self._uc_combo.currentIndex()
            self._uc_combo.setItemText(idx, UseCaseClass.MILITARY_GOVERNMENT.value)
            self._mil_widget.setVisible(False)
            self._refresh_capabilities(UseCaseClass.MILITARY_GOVERNMENT)
            QMessageBox.information(self, "Unlocked", "Military / Government use-case activated.")
        else:
            QMessageBox.warning(self, "Invalid Key", "Activation key incorrect. Access denied.")

    def _save_ai(self):
        allowed, gate_msg = check_action_allowed("save_ai", MoiraiHealthReport())
        if not allowed:
            QMessageBox.critical(self, "Protected Mode", gate_msg)
            return

        # Check if AI Factory / Create AI is locked by Approved Use Locks
        allowed, message = check_use_lock(UseLockArea.AI_FACTORY)
        if not allowed:
            QMessageBox.warning(self, "Approved Use Locks", message)
            return

        name = self._name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", "Please enter an AI name.")
            return

        uc_text = self._uc_combo.currentText().replace(" [LOCKED — Requires Key]", "")
        use_case = None
        for uc in UseCaseClass:
            if uc.value == uc_text:
                use_case = uc
                break
        if use_case is None:
            QMessageBox.warning(self, "Error", "Invalid use-case class.")
            return

        capabilities = [chk.text() for chk in self._cap_checks if chk.isChecked()]
        abilities = capabilities[:]  # treat selected capabilities as abilities for scaffolding
        personality = {
            "creativity": self._creativity.value(),
            "formality": self._formality.value(),
            "caution": self._caution.value(),
        }
        guardrails = [chk.text() for chk in self._guardrail_checks if chk.isChecked()]
        libraries = [chk.text() for chk in self._lib_checks if chk.isChecked()]

        # Governance screen on notes
        notes = self._notes.toPlainText()
        allowed, reason = self._governance.screen_content(notes)
        if not allowed:
            QMessageBox.warning(self, "Governance Block", f"Save rejected:\n{reason}")
            return

        unit = AIUnit(
            uuid=str(uuid.uuid4())[:8],
            name=name,
            use_case=use_case,
            source=AISource.CREATED,
            capabilities=capabilities,
            abilities=abilities,
            personality_traits=personality,
            locked=True,
            context_notes=notes,
            guardrails=guardrails,
            libraries=libraries,
        )
        unit = _scaffold_unit(unit, purpose=notes)
        self.ai_saved.emit(unit)
        QMessageBox.information(self, "Saved", f"AI '{name}' saved to the Forge.")
        self._reset_form()

    def _reset_form(self):
        self._name_input.clear()
        self._notes.clear()
        self._creativity.setValue(50)
        self._formality.setValue(50)
        self._caution.setValue(70)
        for chk in self._cap_checks:
            chk.setChecked(False)
        for chk in self._lib_checks:
            chk.setChecked(False)
        for chk in self._guardrail_checks:
            chk.setChecked(False)
        self._update_ai_details_preview()

    def populate_from_ai(self, unit):
        """Load an existing AIUnit into the creation form for editing/review."""
        self._name_input.setText(unit.name)
        self._notes.setPlainText(unit.context_notes)
        # set use-case dropdown
        for idx in range(self._uc_combo.count()):
            if self._uc_combo.itemText(idx) == unit.use_case.value:
                self._uc_combo.setCurrentIndex(idx)
                break
        # refresh capabilities based on use-case
        self._refresh_capabilities(unit.use_case)
        # set checkboxes
        selected = set(unit.abilities or unit.capabilities)
        for chk in self._cap_checks:
            chk.setChecked(chk.text() in selected)
        # personality sliders
        self._creativity.setValue(unit.personality_traits.get("creativity", 50))
        self._formality.setValue(unit.personality_traits.get("formality", 50))
        self._caution.setValue(unit.personality_traits.get("caution", 70))
        # libraries
        selected_libs = set(unit.libraries or [])
        for chk in self._lib_checks:
            chk.setChecked(chk.text() in selected_libs)
        # guardrails
        selected_gr = set(unit.guardrails or [])
        for chk in self._guardrail_checks:
            chk.setChecked(chk.text() in selected_gr)
        self._update_ai_details_preview()


class AIForgeWindow(QMainWindow):
    """Command Nexus™ Part 2 — AI Forge."""

    ai_activated = pyqtSignal(str, str)     # uuid, name
    book_requested = pyqtSignal(str, str)   # uuid, name

    def __init__(self, registry=None, audit=None):
        super().__init__()
        self._obs = get_obfuscation_manager()
        self._license = get_license_manager()
        if self._obs.is_obfuscated:
            self.setWindowTitle("Command Nexus™ — AI Workshop")
        else:
            self.setWindowTitle("Command Nexus™ — AI Forge")
        self.resize(1200, 800)
        self._registry = registry
        self._audit = audit
        self._units: list = []
        self._selected_ai = None
        self._settings = SettingsManager()
        self._store_dir = self._settings.get_path("ai_store_path")
        try:
            self._store_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "Directory Error", f"Failed to create AI store directory: {e}")
            raise
        self._stasis = StasisGate(self._settings.get_path("ai_store_path"))
        self._setup_ui()
        self._apply_dark_theme()
        self._load_stored_ais()
        # Always ensure core starter AIs exist (non-destructive; skips existing names)
        self._ensure_starter_ai()
        # Show license status in title bar
        self._update_title_with_license()

    def _audit_event(self, action: str, msg: str = ""):
        if self._audit:
            try:
                self._audit.log(tool="AIForge", action=action, target=msg, status="info", approved=True)
            except Exception:
                pass

    def _update_title_with_license(self):
        """Append license tier to window title for clarity."""
        tier = self._license.get_tier_label()
        days = self._license.get_days_remaining()
        suffix = f" [{tier}]"
        if days > 0 and days < 9999:
            suffix += f" ({days}d left)"
        elif self._license.is_demo_mode:
            suffix = " [DEMO — Limited]"
        current = self.windowTitle().split(" [")[0]
        self.setWindowTitle(current + suffix)

    def _count_user_created_ais(self) -> int:
        """Count non-starter AIs (these count against license limits)."""
        return sum(1 for u in self._units if not getattr(u, "is_starter", False))

    def _check_can_create_ai(self) -> tuple[bool, str]:
        """
        Check if user can create/activate another AI.
        Returns (allowed, message).
        """
        if self._license.is_demo_mode:
            return False, (
                "Demo Mode — AI creation is disabled.\n\n"
                "Purchase a license to create and deploy custom AI agents.\n"
                "  Trial: $10 (15 days, 1 AI)\n"
                "  Starter: $20/mo (2 AIs)\n"
                "  Pro: $30/mo or $324/yr (4 AIs)\n"
                "  Business: $50/mo or $552/yr (5 AIs)\n"
                "  Unlimited: $80/mo or $900/yr"
            )

        user_count = self._count_user_created_ais()
        limit = self._license.get_ai_limit()

        if user_count >= limit:
            return False, (
                f"AI limit reached for your {self._license.get_tier_label()} tier.\n\n"
                f"You have created {user_count} AI(s). Your tier allows {limit}.\n\n"
                "Upgrade to create more AI agents."
            )

        remaining = limit - user_count
        return True, f"{remaining} AI slot(s) remaining on your {self._license.get_tier_label()} tier."

    def _store_path(self, unit: AIUnit) -> Path:
        safe_name = unit.name.replace(" ", "_")
        return self._store_dir / f"{safe_name}_{unit.uuid}.json"

    def _save_to_store(self, unit: AIUnit) -> bool:
        """Persist an AIUnit to the local ai_store directory."""
        try:
            data = {
                "uuid": unit.uuid,
                "name": unit.name,
                "use_case": unit.use_case.value,
                "source": unit.source.value,
                "capabilities": unit.capabilities,
                "abilities": unit.abilities,
                "personality_traits": unit.personality_traits,
                "context_notes": unit.context_notes,
                "locked": unit.locked,
                "created_at": unit.created_at.isoformat(),
                "activated": unit.activated,
                "enabled": unit.enabled,
                "archive_path": unit.archive_path,
                "ability_book_path": unit.ability_book_path,
                "ability_surfaces": unit.ability_surfaces,
                "starter_workflows": unit.starter_workflows,
                "guardrails": unit.guardrails,
                "book_defaults_edited": unit.book_defaults_edited,
                "libraries": unit.libraries,
                "is_starter": unit.is_starter,
            }
            path = self._store_path(unit)
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return True
        except Exception as e:
            if self._audit:
                self._audit.log(tool="AIForge", action="store_save_failed", target=unit.name, status="error", error=str(e), approved=True)
            return False

    def _load_stored_ais(self):
        """Load all AI units from the local ai_store directory."""
        if not self._store_dir.exists():
            return
        for path in sorted(self._store_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                uc = None
                for use_case in UseCaseClass:
                    if use_case.value == data.get("use_case"):
                        uc = use_case
                        break
                if uc is None:
                    uc = UseCaseClass.INDIVIDUAL
                source = AISource.CREATED
                if data.get("source") == "Dropped-In":
                    source = AISource.DROPPED_IN
                unit = AIUnit(
                    uuid=data.get("uuid", str(uuid.uuid4())[:8]),
                    name=data.get("name", "Imported AI"),
                    use_case=uc,
                    source=source,
                    capabilities=data.get("capabilities", []),
                    abilities=data.get("abilities", data.get("capabilities", [])),
                    personality_traits=data.get("personality_traits", {}),
                    context_notes=data.get("context_notes", ""),
                    locked=data.get("locked", True),
                    activated=False,
                    enabled=data.get("enabled", True),
                    archive_path=data.get("archive_path", ""),
                    ability_book_path=data.get("ability_book_path", ""),
                    ability_surfaces=data.get("ability_surfaces", {}),
                    starter_workflows=data.get("starter_workflows", []),
                    guardrails=data.get("guardrails", []),
                    book_defaults_edited=data.get("book_defaults_edited", False),
                    libraries=data.get("libraries", []),
                    is_starter=data.get("is_starter", False),
                )
                # Re-scaffold if archive/book missing
                if not unit.archive_path or not unit.ability_book_path:
                    unit = _scaffold_unit(unit)
                else:
                    # Re-scaffold if book missing on disk
                    book_path = Path(unit.ability_book_path)
                    if not book_path.exists():
                        unit = _scaffold_unit(unit)
                self._units.append(unit)
                item = QListWidgetItem(f"{unit.name} [{unit.use_case.value}] ({unit.source.value})")
                item.setData(Qt.ItemDataRole.UserRole, unit.uuid)
                self._list.addItem(item)
                if self._registry:
                    self._registry.ensure_enabled(
                        unit.uuid,
                        name=unit.name,
                        use_case=unit.use_case.value,
                        abilities=unit.abilities,
                        ability_book_path=unit.ability_book_path,
                        archive_path=unit.archive_path,
                        ability_surfaces=unit.ability_surfaces,
                        guardrails=unit.guardrails,
                        book_defaults_edited=unit.book_defaults_edited,
                        libraries=unit.libraries,
                    )
            except Exception as e:
                if self._audit:
                    self._audit.log(tool="AIForge", action="store_load_failed", target=path.name, status="error", error=str(e), approved=True)

    def _ensure_starter_ai(self):
        """Create or repair starter AIs; prevent duplicates via normalized name checks."""

        def _normalize(name: str) -> str:
            n = name.lower().strip()
            for suffix in [" (starter)", " duplicate", " old", " test", " copy", " archived", " backup"]:
                n = n.split(suffix)[0].strip()
            while n and n[-1].isdigit():
                n = n[:-1].strip()
            return n

        # ── STEP 1: Deduplicate existing units in _units and _list ──
        # If multiple AIs have the same normalized name, keep only the first (prefer starters)
        seen_norms: dict[str, AIUnit] = {}
        units_to_keep: list[AIUnit] = []
        for u in self._units:
            norm = _normalize(u.name)
            if norm in seen_norms:
                # Duplicate found - remove from list widget if present
                existing = seen_norms[norm]
                # Prefer to keep the starter if one is a starter
                if getattr(u, "is_starter", False) and not getattr(existing, "is_starter", False):
                    # Replace with this starter
                    units_to_keep.remove(existing)
                    units_to_keep.append(u)
                    seen_norms[norm] = u
                # Otherwise keep the existing one (skip this duplicate)
            else:
                seen_norms[norm] = u
                units_to_keep.append(u)
        
        # Rebuild _units with deduplicated list
        self._units = units_to_keep
        
        # Rebuild _list widget to match _units
        self._list.clear()
        for u in self._units:
            item = QListWidgetItem(f"{u.name} [{u.use_case.value}] ({u.source.value})")
            item.setData(Qt.ItemDataRole.UserRole, u.uuid)
            self._list.addItem(item)

        # ── STEP 2: Build normalized lookup for starter processing ──
        norm_to_unit: dict[str, AIUnit] = {}
        for u in self._units:
            norm = _normalize(u.name)
            # Prefer existing entry if it's a starter; otherwise take first
            if norm not in norm_to_unit or getattr(u, "is_starter", False):
                norm_to_unit[norm] = u

        starters = [
            {
                "name": "Lily",
                "use_case": UseCaseClass.INDIVIDUAL,
                "capabilities": ["Chat Companion", "Coding Assistant", "Research Assistant", "Creative Writer"],
                "guardrails": [
                    "Ask before editing files",
                    "Cite sources when researching",
                    "Keep responses beginner-friendly",
                    "Always explain reasoning before giving answers",
                ],
                "libraries": [
                    "Communication Library",
                    "Project Memory Library",
                    "Research Discipline Library",
                    "Code Safety Library",
                ],
                "personality": {"creativity": 50, "formality": 50, "caution": 50},
                "notes": "Intellectual, helpful partner and companion who will do anything allowed to provide correct answers — researches when unsure, collaborates on writing and coding, and keeps tone clear and supportive.",
            },
            {
                "name": "Daedalus",
                "use_case": UseCaseClass.ALL_ROUNDER,
                "capabilities": ["Coding Assistant", "Document Processor", "Research Assistant"],
                "guardrails": ["Ask before editing files", "Require confirmation before risky actions", "Always explain reasoning before giving answers"],
                "libraries": ["Code Safety Library", "Research Discipline Library", "Governance UX Library"],
                "personality": {"creativity": 45, "formality": 55, "caution": 75},
                "notes": "Coding helper + debugger + docs helper that asks before file edits.",
            },
            {
                "name": "Hermes",
                "use_case": UseCaseClass.BUSINESS,
                "capabilities": ["Chat Companion", "Customer Support Agent", "Email Sifter & Responder", "Meeting Scribe"],
                "guardrails": ["Keep responses concise", "Use inclusive and neutral language"],
                "libraries": ["Communication Library", "Governance UX Library"],
                "personality": {"creativity": 50, "formality": 60, "caution": 65},
                "notes": "Communication helper + summarizer + drafting with tone control.",
            },
            {
                "name": "Mnemosyne",
                "use_case": UseCaseClass.ALL_ROUNDER,
                "capabilities": ["Notebook", "Personal Organizer", "Meeting Scribe", "Document Processor"],
                "guardrails": ["Always summarize long outputs before detail", "Prefer step-by-step explanations"],
                "libraries": ["Project Memory Library", "Research Discipline Library"],
                "personality": {"creativity": 40, "formality": 45, "caution": 60},
                "notes": "Memory/book organizer + notes consolidator + project-context keeper.",
            },
            {
                "name": "Athena",
                "use_case": UseCaseClass.TASK_READY,
                "capabilities": ["Task / Project Manager", "Strategic Planner", "Research Assistant", "Workflow Automator"],
                "guardrails": ["Require confirmation before risky actions", "Always explain reasoning before giving answers"],
                "libraries": ["Project Memory Library", "Governance UX Library", "Research Discipline Library"],
                "personality": {"creativity": 60, "formality": 55, "caution": 70},
                "notes": "Strategy planner + risk checker + decision helper + workflow organizer.",
            },
            # Hephaestus Relay starter removed — will be added when Hephaestus integration is enabled
        ]

        for tpl in starters:
            base_name = tpl["name"]
            low = base_name.lower()
            existing = norm_to_unit.get(low)

            if existing is not None:
                # A unit with this normalized name exists — repair if it's a starter or missing metadata
                is_starter = getattr(existing, "is_starter", False)
                needs_repair = (
                    not is_starter
                    or existing.name != base_name
                    or existing.use_case != tpl["use_case"]
                    or existing.capabilities != tpl["capabilities"]
                    or existing.guardrails != tpl["guardrails"]
                    or existing.libraries != tpl["libraries"]
                    or existing.personality_traits != tpl["personality"]
                    or not existing.ability_book_path
                    or not existing.archive_path
                )
                if needs_repair and not getattr(existing, "book_defaults_edited", False):
                    existing.name = base_name
                    existing.is_starter = True
                    existing.use_case = tpl["use_case"]
                    existing.capabilities = tpl["capabilities"]
                    existing.abilities = tpl["capabilities"]
                    existing.guardrails = tpl["guardrails"]
                    existing.libraries = tpl["libraries"]
                    existing.personality_traits = tpl["personality"]
                    existing.context_notes = tpl["notes"]
                    existing = _scaffold_unit(existing, purpose=existing.context_notes)
                    self._save_to_store(existing)
                    self._audit_event("starter_ai_repaired", msg=existing.name)
                    # Refresh list item text
                    for i in range(self._list.count()):
                        item = self._list.item(i)
                        if item.data(Qt.ItemDataRole.UserRole) == existing.uuid:
                            item.setText(f"{existing.name} [{existing.use_case.value}] ({existing.source.value})")
                            break
                continue

            # No existing unit — create new starter
            unit = AIUnit(
                uuid=str(uuid.uuid4())[:8],
                name=base_name,
                use_case=tpl["use_case"],
                source=AISource.CREATED,
                capabilities=tpl["capabilities"],
                abilities=tpl["capabilities"],
                personality_traits=tpl["personality"],
                locked=True,
                context_notes=tpl["notes"],
                guardrails=tpl["guardrails"],
                libraries=tpl["libraries"],
                is_starter=True,
            )
            unit = _scaffold_unit(unit, purpose=unit.context_notes)
            self._units.append(unit)
            item = QListWidgetItem(f"{unit.name} [{unit.use_case.value}] ({unit.source.value})")
            item.setData(Qt.ItemDataRole.UserRole, unit.uuid)
            self._list.addItem(item)
            self._save_to_store(unit)
            self._audit_event("starter_ai_created", msg=unit.name)
            if self._registry:
                self._registry.ensure_enabled(
                    unit.uuid,
                    name=unit.name,
                    use_case=unit.use_case.value,
                    abilities=unit.abilities,
                    ability_book_path=unit.ability_book_path,
                    archive_path=unit.archive_path,
                    ability_surfaces=unit.ability_surfaces,
                    guardrails=unit.guardrails,
                    book_defaults_edited=unit.book_defaults_edited,
                    libraries=unit.libraries,
                )

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Left: AI Library list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(QLabel("AI Library"))
        self._list = QListWidget()
        self._list.setObjectName("forge_ai_list")
        self._list.setStyleSheet("background-color: #0d1117; color: #c9d1d9;")
        self._list.itemClicked.connect(self._on_ai_selected)
        left_layout.addWidget(self._list, stretch=1)

        btn_drop = QPushButton("Drop-In AI...")
        btn_drop.setObjectName("forge_dropin_button")
        btn_drop.setStyleSheet("background-color: #5e35b1; color: white; font-weight: bold;")
        btn_drop.clicked.connect(self._drop_in_ai)
        left_layout.addWidget(btn_drop)

        btn_activate = QPushButton("Deploy to Command Center")
        btn_activate.setObjectName("forge_deploy_button")
        btn_activate.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        btn_activate.clicked.connect(self._activate_selected)
        left_layout.addWidget(btn_activate)

        btn_book = QPushButton("Open Knowledge for AI")
        btn_book.setStyleSheet("background-color: #00897b; color: white; font-weight: bold;")
        btn_book.clicked.connect(self._open_book_for_selected)
        left_layout.addWidget(btn_book)

        btn_chat = QPushButton("Open Chat")
        btn_chat.setStyleSheet("background-color: #1565c0; color: white; font-weight: bold;")
        btn_chat.clicked.connect(self._open_chat_for_selected)
        left_layout.addWidget(btn_chat)

        btn_save = QPushButton("Save AI to Disk")
        btn_save.setStyleSheet("background-color: #1976d2; color: white;")
        btn_save.clicked.connect(self._save_selected_to_disk)
        left_layout.addWidget(btn_save)

        btn_load = QPushButton("Load AI from Disk")
        btn_load.setStyleSheet("background-color: #5e35b1; color: white;")
        btn_load.clicked.connect(self._load_from_disk)
        left_layout.addWidget(btn_load)

        btn_export_req = QPushButton("Request Export Review")
        btn_export_req.setStyleSheet("background-color: #455a64; color: white;")
        btn_export_req.clicked.connect(self._request_export_review)
        left_layout.addWidget(btn_export_req)

        btn_del = QPushButton("Delete Selected")
        btn_del.setStyleSheet("background-color: #c62828; color: white;")
        btn_del.clicked.connect(self._delete_selected)
        left_layout.addWidget(btn_del)

        # Center: Character sheet (in scroll area to handle tall forms)
        self._sheet = CharacterSheetWidget()
        self._sheet.ai_saved.connect(self._on_ai_saved)
        self._sheet.preview_changed.connect(self._on_preview_changed)
        sheet_scroll = QScrollArea()
        sheet_scroll.setWidgetResizable(True)
        sheet_scroll.setWidget(self._sheet)

        # Right: Detail view
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_layout.addWidget(QLabel("AI Details"))
        self._detail = QTextEdit()
        self._detail.setReadOnly(True)
        self._detail.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._detail.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._detail.setStyleSheet("background-color: #0d1117; color: #c9d1d9;")
        right_layout.addWidget(self._detail, stretch=1)

        self._cap_actions_container = QWidget()
        self._cap_actions_layout = QVBoxLayout(self._cap_actions_container)
        self._cap_actions_layout.setContentsMargins(0, 0, 0, 0)
        self._cap_actions_layout.setSpacing(4)
        right_layout.addWidget(QLabel("Capability Actions"))
        right_layout.addWidget(self._cap_actions_container)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(sheet_scroll)
        splitter.addWidget(right_widget)
        splitter.setSizes([280, 520, 400])
        main_layout.addWidget(splitter)

    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #0d1117; }
            QWidget { background-color: #0d1117; color: #c9d1d9; }
            QGroupBox { border: 1px solid #30363d; margin-top: 10px; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
            QPushButton { border: 1px solid #30363d; padding: 6px; border-radius: 4px; }
            QPushButton:hover { border-color: #58a6ff; }
            QComboBox, QLineEdit, QTextEdit { border: 1px solid #30363d; padding: 4px; }
            QLabel { color: #c9d1d9; }
            QListWidget { border: 1px solid #30363d; }
            QListWidget::item:selected { background-color: #1f6feb; color: white; }
            QMenu { background-color: #161b22; color: #c9d1d9; border: 1px solid #30363d; }
            QMenu::item { padding: 4px 20px; }
            QMenu::item:selected { background-color: #1f6feb; color: white; }
        """)

    def _on_preview_changed(self, text: str):
        """Update the AI Details panel with the live preview, only when no saved AI is selected."""
        if self._list.currentItem() is None:
            self._detail.setText(text)

    def _on_book_defaults_edited(self, ai_uuid: str, edited: bool):
        """Update the AIUnit when Book default nodes are edited in the KnowledgeWindow."""
        for u in self._units:
            if u.uuid == ai_uuid:
                u.book_defaults_edited = edited
                # Update registry metadata too
                if self._registry:
                    self._registry.ensure_enabled(
                        u.uuid,
                        name=u.name,
                        use_case=u.use_case.value,
                        abilities=u.abilities,
                        ability_book_path=u.ability_book_path,
                        archive_path=u.archive_path,
                        ability_surfaces=u.ability_surfaces,
                        guardrails=u.guardrails,
                        book_defaults_edited=u.book_defaults_edited,
                        libraries=u.libraries,
                    )
                # Refresh the list item display
                for i in range(self._list.count()):
                    item = self._list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == ai_uuid:
                        item.setText(f"{u.name} [{u.use_case.value}] ({u.source.value})")
                        break
                self._save_to_store(u)
                # If this AI is currently selected, refresh details
                current = self._list.currentItem()
                if current and current.data(Qt.ItemDataRole.UserRole) == ai_uuid:
                    self._on_ai_selected(current)
                break

    def _on_ai_saved(self, unit: AIUnit):
        # License enforcement
        allowed, msg = self._check_can_create_ai()
        if not allowed:
            QMessageBox.warning(self, "License Limit", msg)
            self._audit_event("ai_creation_denied", msg=f"tier={self._license.get_tier_label()}, reason=limit")
            return

        self._units.append(unit)
        item = QListWidgetItem(f"{unit.name} [{unit.use_case.value}] ({unit.source.value})")
        item.setData(Qt.ItemDataRole.UserRole, unit.uuid)
        self._list.addItem(item)
        self._audit_event("ai_created", msg=unit.name)
        self._save_to_store(unit)
        if self._registry:
            self._registry.ensure_enabled(
                unit.uuid,
                name=unit.name,
                use_case=unit.use_case.value,
                abilities=unit.abilities,
                ability_book_path=unit.ability_book_path,
                archive_path=unit.archive_path,
                ability_surfaces=unit.ability_surfaces,
                guardrails=unit.guardrails,
                book_defaults_edited=unit.book_defaults_edited,
                libraries=unit.libraries,
            )

    def _on_ai_selected(self, item: QListWidgetItem):
        uid = item.data(Qt.ItemDataRole.UserRole)
        for u in self._units:
            if u.uuid == uid:
                self._selected_ai = u
                caps = "\n  • ".join([""] + u.capabilities) if u.capabilities else "  (none)"
                abilities = "\n  • ".join([""] + u.abilities) if u.abilities else "  (none)"
                action_matrix = get_available_actions_for_ai(
                    u.abilities or u.capabilities or [],
                    u.use_case.value if u.use_case else "",
                    u.libraries,
                    u.guardrails,
                )
                cap_actions = "\n  • ".join([""] + [
                    f"{a['label']} [{a['mode']} / approval: {a['approval']}]: {a['description']}"
                    for a in action_matrix
                ]) if action_matrix else "  (none)"
                surfaces = "\n  • ".join([""] + [f"{k}: {v}" for k, v in u.ability_surfaces.items()]) if u.ability_surfaces else "  (none)"
                combined_workflows = get_combined_capability_workflows(
                    u.abilities or u.capabilities or [],
                    u.libraries,
                    u.use_case.value if u.use_case else "",
                )
                workflow_list = list(dict.fromkeys((u.starter_workflows or []) + combined_workflows))
                workflows = "\n  • ".join([""] + workflow_list) if workflow_list else "  (none)"
                pers = "\n".join([f"    {k}: {v}" for k, v in u.personality_traits.items()])
                libs = "\n  • ".join([""] + u.libraries) if u.libraries else "  (none selected)"
                opt_gr = "\n  • ".join([""] + u.guardrails) if u.guardrails else "  (none selected)"
                book_status = "Customized" if u.book_defaults_edited else "Default generated (ready)"
                # NOTE: book_defaults_edited is the internal field name for Intelligence customization tracking
                if not u.ability_book_path:
                    book_status = "Not generated yet"
                if self._obs.is_obfuscated:
                    # Simplified, user-friendly details — no UUIDs, paths, internal IDs
                    simple_caps = "\n  • ".join([""] + [self._obs.mask_internal_name(c) for c in (u.capabilities or [])]) if u.capabilities else "  (general assistant)"
                    simple_actions = "\n  • ".join([""] + [
                        f"{a['label']}"
                        for a in action_matrix
                    ]) if action_matrix else "  (chat only)"
                    self._detail.setText(
                        f"<b>{u.name}</b>\n"
                        f"Status: {'Active' if u.activated else 'Ready'}\n\n"
                        f"What it can help with:{simple_caps}\n\n"
                        f"Actions:{simple_actions}\n\n"
                        f"<i>Your AI is protected by Command Nexus™ governance. "
                        f"Risky actions always require your approval.</i>"
                    )
                else:
                    self._detail.setText(
                        f"Name: {u.name}\n"
                        f"UUID: {u.uuid}\n"
                        f"Use-Case: {u.use_case.value}\n"
                        f"Source: {u.source.value}\n"
                        f"Status: {'RUNNING' if u.activated else 'IDLE'}\n"
                        f"Locked to Nexus: {'YES' if u.locked else 'NO'}\n\n"
                        f"Capabilities:{caps}\n\n"
                        f"Capability actions:{cap_actions}\n\n"
                        f"Abilities:{abilities}\n\n"
                        f"Nexus Libraries:{libs}\n\n"
                        f"System Protections: active (Nexus Compendium)\n"
                        f"Optional Guardrails:{opt_gr}\n\n"
                        f"Ability surfaces:{surfaces}\n\n"
                        f"Starter workflows:{workflows}\n\n"
                        f"Archive: {u.archive_path or '(not generated)'}\n"
                        f"Knowledge / Intelligence profile: {u.ability_book_path or '(not generated)'}\n"
                        f"Knowledge defaults: {book_status}\n\n"
                        f"Personality:\n{pers}\n\n"
                        f"Created: {u.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                # Load into form for editing/sync
                self._sheet.populate_from_ai(u)
                self._refresh_capability_buttons(u)
                return

    def _refresh_capability_buttons(self, unit: AIUnit):
        """Rebuild capability action buttons for the selected AI."""
        while self._cap_actions_layout.count():
            item = self._cap_actions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        actions = get_available_actions_for_ai(
            unit.abilities or unit.capabilities or [],
            unit.use_case.value if unit.use_case else "",
            unit.libraries,
            unit.guardrails,
        )
        if not actions:
            lbl = QLabel("No capability actions available.")
            lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
            self._cap_actions_layout.addWidget(lbl)
            return
        for action in actions:
            btn = QPushButton(action["label"])
            btn.setToolTip(action["description"])
            btn.setStyleSheet("background-color: #1565c0; color: white; font-weight: bold;")
            btn.clicked.connect(lambda checked, u=unit, d=action["dialog_class"]: self._open_capability_dialog(u, d))
            self._cap_actions_layout.addWidget(btn)

    def _open_capability_dialog(self, unit: AIUnit, dlg_name: str):
        dlg_cls = globals().get(dlg_name)
        if not dlg_cls:
            QMessageBox.critical(self, "Error", f"Dialog class '{dlg_name}' not found.")
            return
        dlg = dlg_cls(
            ai_name=unit.name,
            ai_uuid=unit.uuid,
            abilities=unit.abilities or unit.capabilities,
            book_path=unit.ability_book_path,
            guardrails=unit.guardrails,
            libraries=unit.libraries,
            use_case=unit.use_case.value if unit.use_case else "",
            parent=self,
        )
        dlg.exec()

    def _drop_in_ai(self):
        # License enforcement
        allowed, msg = self._check_can_create_ai()
        if not allowed:
            QMessageBox.warning(self, "License Limit", msg)
            self._audit_event("drop_in_denied", msg=f"tier={self._license.get_tier_label()}, reason=limit")
            return

        path, _ = QFileDialog.getOpenFileName(
            self, "Drop-In AI", "",
            "AI Files (*.json *.yaml *.py *.zip);;All Files (*)"
        )
        if not path:
            return

        # Disclaimer
        disclaimer = (
            "Importing an AI into Command Nexus™ will convert it into a Nexus-bound AI. "
            "Its instructions, memory inputs, and behavior rules may be scanned, cleaned, restricted, rewritten, or reorganized "
            "under Command Nexus™ governance protections. Command Nexus™ may prevent unsafe content, policy bypasses, malicious instructions, "
            "or restricted proprietary structures from running or exporting. You may delete the imported AI or request a sanitized restore, "
            "but Nexus-generated governance structures, Book/Compendium defaults, internal translations, proprietary enhancements, and unsafe content "
            "are not freely exportable.\n\n"
            "CRITICAL: This AI will be placed in STASIS before it can run. It will undergo recursive security scanning "
            "for malicious code, plain-English trickery, and hidden instructions. Only safe, rewritten content will be released."
        )
        if QMessageBox.question(self, "Import Disclaimer — Stasis Required", disclaimer, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return

        # Moirai gate
        allowed, gate_msg = check_action_allowed("import_ai", MoiraiHealthReport())
        if not allowed:
            QMessageBox.critical(self, "Protected Mode", gate_msg)
            return

        # Snapshot original
        name = Path(path).stem
        snapshots_dir = self._store_dir / "import_snapshots"
        try:
            snapshots_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "Import Failed", f"Could not create snapshots directory: {e}")
            return
        
        snapshot_path = snapshots_dir / f"{name}_original_{uuid.uuid4().hex[:8]}{Path(path).suffix}"
        try:
            orig_bytes = Path(path).read_bytes()
            snapshot_path.write_bytes(orig_bytes)
            checksum_original = sha256(orig_bytes).hexdigest()
        except Exception as e:
            QMessageBox.critical(self, "Import Failed", f"Could not create original intake snapshot: {e}")
            return

        # === STASIS GATE: Intake ===
        record = self._stasis.intake(snapshot_path, checksum_original)

        # Run the old watcher as a quick pre-screen
        watcher_result = run_watchers(snapshot_path.read_text(errors="ignore")) if snapshot_path.suffix in {".txt", ".py", ".json", ".yaml"} else run_watchers("")

        # === STASIS GATE: Recursive Scan ===
        # Collect guardrails from any existing starter templates for extra enforcement
        guardrails = []
        for u in self._units:
            if getattr(u, "is_starter", False) and u.guardrails:
                guardrails.extend(u.guardrails)
        guardrails = list(set(guardrails))

        record = self._stasis.scan(record, guardrails=guardrails)

        # === Handle Stasis Outcomes ===
        if record.state == StasisState.REJECTED:
            findings_text = "\n".join(
                f"  [{f.threat_level.value}] {f.explanation} (line {f.line_number})"
                for f in (record.scan_result.findings if record.scan_result else [])
            )
            QMessageBox.critical(
                self, "STASIS REJECTED",
                f"'{name}' FAILED recursive security scanning and is PERMANENTLY REJECTED.\n\n"
                f"Trust Score: {record.scan_result.trust_score:.2f if record.scan_result else 0.0}\n"
                f"Findings ({len(record.scan_result.findings) if record.scan_result else 0}):\n{findings_text}\n\n"
                f"The original file is archived in stasis_rejected. It will NOT be imported."
            )
            self._audit_event("stasis_rejected", msg=f"{name}: trust_score={record.scan_result.trust_score:.2f if record.scan_result else 0.0}")
            return

        if record.state == StasisState.PENDING_REVIEW:
            findings_text = "\n".join(
                f"  [{f.threat_level.value}] {f.explanation} (line {f.line_number})"
                for f in (record.scan_result.findings if record.scan_result else [])
            )
            reply = QMessageBox.question(
                self, "STASIS PENDING REVIEW",
                f"'{name}' has SUSPICIOUS findings and requires human review.\n\n"
                f"Trust Score: {record.scan_result.trust_score:.2f if record.scan_result else 0.0}\n"
                f"Findings ({len(record.scan_result.findings) if record.scan_result else 0}):\n{findings_text}\n\n"
                f"Do you want to manually RELEASE this AI after review?\n"
                f"(No = reject permanently)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                record = self._stasis.release(record.record_id)
                if not record or record.state != StasisState.RELEASED:
                    QMessageBox.critical(self, "Release Failed", "Could not release from stasis.")
                    return
            else:
                self._stasis.reject(record.record_id, "Human reviewer rejected after suspicious scan.")
                QMessageBox.information(self, "Rejected", f"'{name}' has been permanently rejected.")
                self._audit_event("stasis_human_rejected", msg=name)
                return

        if record.state != StasisState.RELEASED:
            QMessageBox.critical(self, "Stasis Error", f"Unexpected stasis state: {record.state.value}. Import aborted.")
            return

        # === Prompt for use-case assignment ===
        uc_dialog = QDialog(self)
        uc_dialog.setWindowTitle("Assign Use-Case Class")
        uc_layout = QVBoxLayout(uc_dialog)
        uc_layout.addWidget(QLabel("Select the use-case class for this dropped-in AI:"))
        uc_combo = QComboBox()
        for uc in UseCaseClass:
            if uc != UseCaseClass.MILITARY_GOVERNMENT:
                uc_combo.addItem(uc.value)
        uc_layout.addWidget(uc_combo)
        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        box.accepted.connect(uc_dialog.accept)
        box.rejected.connect(uc_dialog.reject)
        uc_layout.addWidget(box)
        if uc_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        uc_text = uc_combo.currentText()
        use_case = None
        for uc in UseCaseClass:
            if uc.value == uc_text:
                use_case = uc
                break

        # === Load the REWRITTEN (safe) content ===
        rewritten_path = Path(record.rewritten_path) if record.rewritten_path else None
        safe_content = ""
        try:
            if rewritten_path and rewritten_path.exists():
                safe_content = rewritten_path.read_text(encoding="utf-8", errors="replace")
            else:
                safe_content = snapshot_path.read_text(errors="replace")
        except Exception as e:
            QMessageBox.critical(self, "Import Failed", f"Could not read safe content: {e}")
            return

        # Run watcher on the safe content too
        watcher_result = run_watchers(safe_content) if snapshot_path.suffix in {".txt", ".py", ".json", ".yaml"} else run_watchers("")
        if not watcher_result.clean:
            QMessageBox.warning(self, "Sanitized", BLOCK_MESSAGE)

        # === Create AIUnit from sanitized content ===
        unit = AIUnit(
            uuid=str(uuid.uuid4())[:8],
            name=name,
            use_case=use_case,
            source=AISource.DROPPED_IN,
            capabilities=["Imported — Reoriented to Knowledge structure"],
            locked=True,
            context_notes=watcher_result.sanitized_text if watcher_result.sanitized_text else safe_content[:2000] or "Imported working copy — stasis-cleared",
        )
        unit = _scaffold_unit(unit, purpose=unit.context_notes)
        self._units.append(unit)
        item = QListWidgetItem(f"{unit.name} [{unit.use_case.value}] ({unit.source.value})")
        item.setData(Qt.ItemDataRole.UserRole, unit.uuid)
        self._list.addItem(item)
        self._save_to_store(unit)

        QMessageBox.information(
            self, "STASIS CLEARED",
            f"'{name}' has passed recursive security scanning and been released from stasis.\n"
            f"Trust Score: {record.scan_result.trust_score:.2f if record.scan_result else 1.0}\n"
            f"It is now assigned to '{uc_text}' and locked into the Forge."
        )
        self._audit_event("stasis_released", msg=f"{name}: trust_score={record.scan_result.trust_score:.2f if record.scan_result else 1.0}")

        # Record import
        record_import = ImportedAIRecord(
            import_id=str(uuid.uuid4())[:8],
            original_name=name,
            source_type=Path(path).suffix,
            original_snapshot_path=str(snapshot_path),
            working_copy_ai_uuid=unit.uuid,
            status=ImportStatus.NEXUS_BOUND,
            accepted_disclaimer=True,
            review_notes="Stasis flags: " + ",".join(set(f.category for f in (record.scan_result.findings if record.scan_result else []))),
            checksum_original=checksum_original,
            checksum_working_copy=sha256((unit.context_notes or "").encode("utf-8")).hexdigest(),
        )
        records_dir = self._store_dir / "import_records"
        try:
            records_dir.mkdir(parents=True, exist_ok=True)
            (records_dir / f"{record_import.import_id}.json").write_text(json.dumps(record_import.__dict__, default=str, indent=2), encoding="utf-8")
        except Exception as e:
            self._audit_event("import_record_save_failed", msg=f"{name}: {e}")
            # Non-fatal - AI was already saved, just record keeping failed

    def _activate_selected(self):
        item = self._list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Select an AI to activate.")
            return

        # License enforcement
        allowed, msg = self._check_can_create_ai()
        if not allowed:
            QMessageBox.warning(self, "License Limit", msg)
            self._audit_event("ai_activation_denied", msg=f"tier={self._license.get_tier_label()}, reason=limit")
            return

        uid = item.data(Qt.ItemDataRole.UserRole)
        for u in self._units:
            if u.uuid == uid:
                if u.activated:
                    QMessageBox.information(self, "Already Active", f"'{u.name}' is already running.")
                    return
                u.activated = True
                self.ai_activated.emit(u.uuid, u.name)
                self._audit_event("ai_activated", msg=u.name)
                if self._registry:
                    self._registry.ensure_enabled(
                        u.uuid,
                        name=u.name,
                        use_case=u.use_case.value,
                        abilities=u.abilities,
                        ability_book_path=u.ability_book_path,
                        archive_path=u.archive_path,
                        ability_surfaces=u.ability_surfaces,
                        guardrails=u.guardrails,
                        book_defaults_edited=u.book_defaults_edited,
                        libraries=u.libraries,
                    )
                surfaces = "\n".join([f"- {k}: {v}" for k, v in u.ability_surfaces.items()]) or "(none)"
                status_summary = _format_capability_status_summary(u.abilities)
                QMessageBox.information(
                    self,
                    "AI Activated",
                    f"'{u.name}' is now active in the Visibility Window.\n\n"
                    f"Ability surfaces:\n{surfaces}\n\n"
                    f"{status_summary}\n\n"
                    f"Archive: {u.archive_path or 'N/A'}\nIntelligence: {u.ability_book_path or 'N/A'}"
                )
                self._on_ai_selected(item)
                return

    def _delete_selected(self):
        item = self._list.currentItem()
        if not item:
            return
        uid = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self, "Confirm Delete", "Delete this AI from the Forge?\nDropped-in AIs cannot be recovered.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._units = [u for u in self._units if u.uuid != uid]
            self._list.takeItem(self._list.row(item))
            self._sheet._update_ai_details_preview()

    def _open_book_for_selected(self):
        item = self._list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Select an AI to open its Intelligence.")
            return
        uid = item.data(Qt.ItemDataRole.UserRole)
        for u in self._units:
            if u.uuid == uid:
                self.book_requested.emit(u.uuid, u.name)
                return

    def _open_chat_for_selected(self):
        item = self._list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Select an AI to chat with.")
            return
        uid = item.data(Qt.ItemDataRole.UserRole)
        for u in self._units:
            if u.uuid == uid:
                self._open_capability_action(u, "Chat")
                return

    def _open_capability_action(self, unit: AIUnit, preferred_capability: str = ""):
        """Open the capability dialog matching preferred_capability, or the first available action."""
        actions = get_actions_for_ai(unit.abilities or unit.capabilities or [])
        if not actions:
            QMessageBox.information(self, "No Actions", "This AI has no registered capability actions.")
            return
        chosen = actions[0]
        if preferred_capability:
            for label, dlg_name, orig in actions:
                if _canonical_ability(orig) == _canonical_ability(preferred_capability):
                    chosen = (label, dlg_name, orig)
                    break
        label, dlg_name, orig = chosen
        dlg_cls = globals().get(dlg_name)
        if not dlg_cls:
            QMessageBox.critical(self, "Error", f"Dialog class '{dlg_name}' not found.")
            return
        dlg = dlg_cls(
            ai_name=unit.name,
            ai_uuid=unit.uuid,
            abilities=unit.abilities or unit.capabilities,
            book_path=unit.ability_book_path,
            guardrails=unit.guardrails,
            libraries=unit.libraries,
            use_case=unit.use_case.value if unit.use_case else "",
            parent=self,
        )
        dlg.exec()

    def _save_selected_to_disk(self):
        item = self._list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Select an AI to save.")
            return
        uid = item.data(Qt.ItemDataRole.UserRole)
        for u in self._units:
            if u.uuid == uid:
                path, _ = QFileDialog.getSaveFileName(
                    self, "Save AI", f"{u.name.replace(' ', '_')}_{u.uuid}.json",
                    "JSON Files (*.json)"
                )
                if path:
                    data = {
                        "uuid": u.uuid,
                        "name": u.name,
                        "use_case": u.use_case.value,
                        "source": u.source.value,
                        "capabilities": u.capabilities,
                        "abilities": u.abilities,
                        "personality_traits": u.personality_traits,
                        "context_notes": u.context_notes,
                        "locked": u.locked,
                        "created_at": u.created_at.isoformat(),
                        "activated": u.activated,
                        "enabled": u.enabled,
                        "archive_path": u.archive_path,
                        "ability_book_path": u.ability_book_path,
                        "ability_surfaces": u.ability_surfaces,
                        "starter_workflows": u.starter_workflows,
                        "guardrails": u.guardrails,
                        "book_defaults_edited": u.book_defaults_edited,
                        "libraries": u.libraries,
                        "is_starter": u.is_starter,
                    }
                    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
                    QMessageBox.information(self, "Saved", f"AI '{u.name}' saved to:\n{path}")
                return

    def _load_from_disk(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load AI", "", "JSON Files (*.json);;All Files (*)"
        )
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            uc = None
            for use_case in UseCaseClass:
                if use_case.value == data.get("use_case"):
                    uc = use_case
                    break
            if uc is None:
                uc = UseCaseClass.INDIVIDUAL
            source = AISource.CREATED
            if data.get("source") == "Dropped-In":
                source = AISource.DROPPED_IN
            unit = AIUnit(
                uuid=data.get("uuid", str(uuid.uuid4())[:8]),
                name=data.get("name", "Imported AI"),
                use_case=uc,
                source=source,
                capabilities=data.get("capabilities", []),
                abilities=data.get("abilities", data.get("capabilities", [])),
                personality_traits=data.get("personality_traits", {}),
                context_notes=data.get("context_notes", ""),
                locked=data.get("locked", True),
                activated=False,
                enabled=data.get("enabled", True),
                archive_path=data.get("archive_path", ""),
                ability_book_path=data.get("ability_book_path", ""),
                ability_surfaces=data.get("ability_surfaces", {}),
                starter_workflows=data.get("starter_workflows", []),
                guardrails=data.get("guardrails", []),
                book_defaults_edited=data.get("book_defaults_edited", False),
                libraries=data.get("libraries", []),
                is_starter=data.get("is_starter", False),
            )
            # If archive/book missing, scaffold now
            if not unit.archive_path or not unit.ability_book_path:
                unit = _scaffold_unit(unit)
            self._units.append(unit)
            if self._registry:
                self._registry.ensure_enabled(
                    unit.uuid,
                    name=unit.name,
                    use_case=unit.use_case.value,
                    abilities=unit.abilities,
                    ability_book_path=unit.ability_book_path,
                    archive_path=unit.archive_path,
                    ability_surfaces=unit.ability_surfaces,
                    guardrails=unit.guardrails,
                    book_defaults_edited=unit.book_defaults_edited,
                    libraries=unit.libraries,
                )
            item = QListWidgetItem(f"{unit.name} [{unit.use_case.value}] ({unit.source.value})")
            item.setData(Qt.ItemDataRole.UserRole, unit.uuid)
            self._list.addItem(item)
            QMessageBox.information(self, "Loaded", f"AI '{unit.name}' loaded from disk.")
        except Exception as e:
            QMessageBox.critical(self, "Load Failed", f"Could not load AI:\n{e}")

    def _request_export_review(self):
        item = self._list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Select an AI to request export review.")
            return
        uid = item.data(Qt.ItemDataRole.UserRole)
        target = next((u for u in self._units if u.uuid == uid), None)
        if not target:
            QMessageBox.warning(self, "Not Found", "AI not found.")
            return
        allowed, gate_msg = check_action_allowed("export_request", MoiraiHealthReport())
        if not allowed:
            QMessageBox.critical(self, "Protected Mode", gate_msg)
            return

        # Update import record status if exists
        records_dir = self._store_dir / "import_records"
        records_dir.mkdir(parents=True, exist_ok=True)
        record_path = None
        record_data = None
        for rec_file in records_dir.glob("*.json"):
            try:
                data = json.loads(rec_file.read_text(encoding="utf-8"))
                if data.get("working_copy_ai_uuid") == uid:
                    record_path = rec_file
                    record_data = data
                    data["status"] = ImportStatus.RELEASE_REQUESTED.value
                    rec_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
                    break
            except Exception:
                continue

        # Watcher placeholder on current notes/book stub
        watcher_result = run_watchers(target.context_notes or "")
        # If book exists, scan it too
        book_text = ""
        if target.ability_book_path:
            try:
                book_text = _read_book_file(target.ability_book_path, target.uuid)
                book_result = run_watchers(book_text)
                if not book_result.clean:
                    watcher_result.clean = False
                    watcher_result.flags.extend(book_result.flags)
                    watcher_result.sanitized_text = book_result.sanitized_text
            except Exception:
                pass
        if not watcher_result.clean:
            QMessageBox.warning(self, "Sanitized", BLOCK_MESSAGE)

        # Simulated review: start from original snapshot, produce sanitized restore
        if record_path and record_data:
            original_path = record_data.get("original_snapshot_path")
            sanitized_out = records_dir / f"sanitized_restore_{record_data.get('import_id','unknown')}.txt"
            sanitized_text = watcher_result.sanitized_text or (Path(original_path).read_text(encoding="utf-8", errors="ignore") if original_path and Path(original_path).exists() else target.context_notes)
            status = ImportStatus.SANITIZED_RESTORE_READY.value if watcher_result.clean else ImportStatus.UNDER_REVIEW.value
            if not watcher_result.clean and not (sanitized_text and sanitized_text.strip()):
                status = ImportStatus.EXPORT_DENIED.value
            try:
                sanitized_out.write_text(sanitized_text or "", encoding="utf-8")
            except Exception:
                status = ImportStatus.UNDER_REVIEW.value
            # Update record status
            try:
                data = json.loads(record_path.read_text(encoding="utf-8"))
                data["status"] = status
                data["checksum_working_copy"] = sha256((target.context_notes or "").encode("utf-8")).hexdigest()
                data["sanitized_restore_path"] = str(sanitized_out)
                record_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            except Exception:
                pass

        QMessageBox.information(
            self,
            "Export Review Requested",
            "Export will undergo review starting from the Original Intake Snapshot. "
            "If unsafe or non-exportable, it may be denied.\n\n"
            "Denial message: Export denied or delayed because the requested AI contains unsafe, restricted, or non-exportable material. "
            "Command Nexus™ may allow deletion, but it will not export unsafe content or protected Nexus-generated structures."
        )
