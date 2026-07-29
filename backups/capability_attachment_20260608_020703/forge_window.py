from __future__ import annotations

ABILITY_SURFACES = {
    "Chatbot": "Chat panel placeholder",
    "Chat": "Chat panel placeholder",
    "Notebook": "Notebook/notes placeholder",
    "Notes": "Notebook/notes placeholder",
    "Knowledge": "Notebook/notes placeholder",
    "Book": "Ability book placeholder",
    "Writer": "Ability book placeholder",
    "Author": "Ability book placeholder",
    "Creative Writing": "Ability book placeholder",
    "Planner": "Mission planning workflow placeholder",
    "Mission Planner": "Mission planning workflow placeholder",
    "Research": "Research workflow placeholder",
    "Search": "Research workflow placeholder",
    "Document Processor": "Document reading/summarization surface placeholder",
    "Coder": "Code explanation and draft patch surface (no direct writes)",
    "Vision": "Connect to AI Vision Stream",
    "Visibility": "Connect to AI Vision Stream",
    "Archive": "Archive folder and memory store",
    "Memory": "Archive folder and memory store",
    "Tool User": "Tool list with approval scaffold",
    "Agent": "Tool list with approval scaffold",
}

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
    }
    return mapping.get(name.strip(), name.strip())

def _generate_surfaces(abilities: list[str]) -> dict[str, str]:
    surfaces = {}
    for ab in abilities:
        key = _canonical_ability(ab)
        desc = ABILITY_SURFACES.get(key, "Placeholder ability surface (backend not connected yet)")
        surfaces[key] = desc
        surfaces[ab] = desc  # keep original name mapping for book rendering
    return surfaces

def _starter_workflows(abilities: list[str]) -> list[str]:
    combos = set(_canonical_ability(a) for a in abilities)
    workflows: list[str] = []
    if {"Chatbot", "Notebook"} & combos:
        workflows.append("Chat can reference notebook/knowledge entries later.")
    if {"Chatbot", "Book"} & combos:
        workflows.append("Chat can summarize/draft from ability book.")
    if {"Planner", "Tool User"} & combos or {"Mission Planner", "Agent"} & combos:
        workflows.append("Plans require approval before tool execution.")
    if {"Vision", "Planner"} & combos or {"Visibility", "Planner"} & combos:
        workflows.append("Visual observations feed into planned actions.")
    if {"Research", "Archive"} & combos or {"Search", "Archive"} & combos:
        workflows.append("Research outputs are saved to archive.")
    if {"Book", "Notebook", "Chatbot"} <= combos:
        workflows.append("Knowledge companion: chat + book + notebook interconnected.")
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
            f"# Ability Book for {name} (Public Build Placeholder)",
            "", "This edition is a future controlled edition and is disabled in the public build.",
            "No operational doctrine generated.",
        ])

    lines: list[str] = []
    lines.append(f"# Ability Book for {name}")
    lines.append("")
    lines.append("## Identity and Purpose")
    lines.append(f"- AI Name: {name}")
    lines.append(f"- AI ID: {ai_id}")
    lines.append(f"- Use-Case Class: {use_case.value}")
    lines.append(f"- Purpose: {purpose or 'Assist within described context; respect approvals.'}")
    lines.append("- Intended user: Command Nexus operator")
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

    lines.append("## Ability Sections")
    for ab in abilities:
        c = _canonical_ability(ab)
        lines.append(f"### {ab}")
        for bullet in _ability_doctrine(ab, use_case):
            lines.append(f"- {bullet}")
        surf = (ability_surfaces or surfaces).get(ab, (ability_surfaces or surfaces).get(c, "Placeholder surface; backend not connected"))
        lines.append(f"- Surface: {surf}")
        lines.append("- Activation: placeholder scaffold; governance gate enforced.")
        prof = profiles.get(c)
        if prof:
            lines.append(f"- Common prompts: {', '.join(prof['prompts'])}")
            lines.append(f"- Quickstart: {'; '.join(prof['quickstart'])}")
        else:
            lines.append("- Common prompts: clarify task, ask for context, request approval when needed.")
        lines.append("")

    lines.append("## Cross-Ability Doctrine")
    for ca in _cross_ability_doctrine(abilities):
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
    assert unit.ability_book_path and Path(unit.ability_book_path).exists(), "Ability book not created"
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

    book_path = folder / "ability_book.md"
    backup_path = folder / f"ability_book_backup_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.md"
    if book_path.exists() and not unit.book_defaults_edited:
        backup_path.write_text(book_path.read_text(encoding="utf-8"), encoding="utf-8")
    book_text = _book_content(
        unit.uuid, unit.name, unit.use_case, purpose or unit.context_notes, abilities, surfaces, workflows,
        guardrails=unit.guardrails, libraries=unit.libraries, ability_surfaces=surfaces
    )
    if not book_path.exists() or not unit.book_defaults_edited:
        book_path.write_text(book_text, encoding="utf-8")
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

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
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
from .forge_models import AIUnit, AISource
from .capability_actions import (
    CAPABILITY_REGISTRY,
    get_actions_for_ai,
    ChatCapabilityDialog,
    CodingCapabilityDialog,
    ResearchCapabilityDialog,
    CreativeWriterCapabilityDialog,
    PlannerCapabilityDialog,
    NotebookCapabilityDialog,
    DocumentProcessorCapabilityDialog,
    ArchiveCapabilityDialog,
    ToolUserCapabilityDialog,
)


# Use-case → capability presets
USE_CASE_OPTIONS: dict = {
    UseCaseClass.INDIVIDUAL: [
        "Chat Companion", "Coding Assistant", "Creative Writer",
        "Learning Tutor", "Personal Organizer", "Research Assistant"
    ],
    UseCaseClass.EDUCATIONAL: [
        "Classroom Tutor", "Assignment Grader", "Lesson Planner",
        "Academic Researcher", "Language Coach", "Accessibility Aide"
    ],
    UseCaseClass.TASK_READY: [
        "Document Processor", "Meeting Scribe", "Data Entry Agent",
        "Workflow Automator", "Content Moderator"
    ],
    UseCaseClass.BUSINESS: [
        "Email Sifter & Responder", "Task / Project Manager",
        "Customer Support Agent", "Sales Assistant",
        "Marketing Generator", "Financial Analyst", "HR Assistant"
    ],
    UseCaseClass.ENTERPRISE: [
        "Business Intelligence Analyst", "Compliance Auditor",
        "Supply Chain Coordinator", "IT Operations Agent",
        "Legal Document Reviewer", "Multi-Department Orchestrator"
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
        "Legal Document Reviewer", "Multi-Department Orchestrator"
    ],
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
    {
        "id": "hephaestus_brief_lib",
        "name": "Hephaestus Briefing Library",
        "description": "Design brief creation, ideation organization, and Hephaestus ProtoBrain handoff formatting. Does not perform prototype modeling.",
        "category": "Design / Prototype",
        "applies_to": ["Creative Writer", "Strategic Planner", "Workflow Automator"],
        "enabled_by_default": False,
        "integration_target": "Hephaestus ProtoBrain",
        "proprietary": True,
        "risk_level": "Medium",
    },
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

    ai_saved = Signal(object)
    preview_changed = Signal(str)  # Live AI Details preview text

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
        self._notes.textChanged.connect(self._update_ai_details_preview)
        layout.addWidget(QLabel("Notes:"))
        layout.addWidget(self._notes)

        # Optional AI Guardrails
        self._guardrails_group = QGroupBox("Optional AI Guardrails")
        self._guardrails_layout = QGridLayout(self._guardrails_group)
        self._guardrail_checks: list = []
        for i, gr in enumerate(OPTIONAL_GUARDRAILS):
            chk = QCheckBox(gr)
            chk.stateChanged.connect(self._update_ai_details_preview)
            self._guardrails_layout.addWidget(chk, i // 2, i % 2)
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

    def _on_uc_changed(self, text: str):
        if "LOCKED" in text:
            self._mil_widget.setVisible(True)
            self._clear_capabilities()
            self._update_ai_details_preview()
            return
        self._mil_widget.setVisible(False)

        for uc in UseCaseClass:
            if uc.value in text:
                self._refresh_capabilities(uc)
                break
        self._update_ai_details_preview()

    def _clear_capabilities(self):
        for check in self._cap_checks:
            check.deleteLater()
        self._cap_checks.clear()

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
    """Command Nexus Part 2 — AI Forge."""

    ai_activated = Signal(str, str)     # uuid, name
    book_requested = Signal(str, str)   # uuid, name

    def __init__(self, registry=None, audit=None):
        super().__init__()
        self.setWindowTitle("Command Nexus — AI Forge")
        self.resize(1200, 800)
        self._registry = registry
        self._audit = audit
        self._units: list = []
        self._selected_ai = None
        self._settings = SettingsManager()
        self._store_dir = Path(self._settings.get().ai_store_path)
        self._store_dir.mkdir(parents=True, exist_ok=True)
        self._setup_ui()
        self._apply_dark_theme()
        self._load_stored_ais()
        # Always ensure core starter AIs exist (non-destructive; skips existing names)
        self._ensure_starter_ai()

    def _audit_event(self, action: str, msg: str = ""):
        if self._audit:
            try:
                self._audit.log(tool="AIForge", action=action, target=msg, status="info", approved=True)
            except Exception:
                pass

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
        """Create starter AIs if missing; do not overwrite user/starter edits."""
        existing_names = {u.name.lower() for u in self._units}
        existing_starters = {u.name.lower() for u in self._units if getattr(u, "is_starter", False)}

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
            {
                "name": "Hephaestus Relay",
                "use_case": UseCaseClass.ALL_ROUNDER,
                "capabilities": ["Creative Writer", "Strategic Planner", "Workflow Automator", "Document Processor"],
                "guardrails": ["Always summarize long outputs before detail", "Always suggest alternatives when declining a request"],
                "libraries": ["Hephaestus Briefing Library", "Communication Library", "Project Memory Library"],
                "personality": {"creativity": 70, "formality": 50, "caution": 65},
                "notes": "Design-brief assistant + ideation organizer + Hephaestus handoff formatter (amplifies Hephaestus, does not replace it).",
            },
        ]

        for tpl in starters:
            base_name = tpl["name"]
            low = base_name.lower()

            if low in existing_names:
                # If a starter with this name already exists, skip; if only a user AI exists, add a starter variant
                if low in existing_starters:
                    continue
                else:
                    tpl_name = f"{base_name} (Starter)"
            else:
                tpl_name = base_name

            unit = AIUnit(
                uuid=str(uuid.uuid4())[:8],
                name=tpl_name,
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
        self._list.setStyleSheet("background-color: #0d1117; color: #c9d1d9;")
        self._list.itemClicked.connect(self._on_ai_selected)
        left_layout.addWidget(self._list, stretch=1)

        btn_drop = QPushButton("Drop-In AI...")
        btn_drop.setStyleSheet("background-color: #5e35b1; color: white; font-weight: bold;")
        btn_drop.clicked.connect(self._drop_in_ai)
        left_layout.addWidget(btn_drop)

        btn_activate = QPushButton("Deploy to Command Center")
        btn_activate.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        btn_activate.clicked.connect(self._activate_selected)
        left_layout.addWidget(btn_activate)

        btn_book = QPushButton("Open Book for AI")
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
        """Update the AIUnit when Book default nodes are edited in the BookWindow."""
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
                cap_actions = "\n  • ".join([""] + [f"{c}: {CAPABILITY_ACTIONS.get(c,'') or 'See Book'}" for c in u.capabilities]) if u.capabilities else "  (none)"
                surfaces = "\n  • ".join([""] + [f"{k}: {v}" for k, v in u.ability_surfaces.items()]) if u.ability_surfaces else "  (none)"
                workflows = "\n  • ".join([""] + u.starter_workflows) if u.starter_workflows else "  (none)"
                pers = "\n".join([f"    {k}: {v}" for k, v in u.personality_traits.items()])
                libs = "\n  • ".join([""] + u.libraries) if u.libraries else "  (none selected)"
                opt_gr = "\n  • ".join([""] + u.guardrails) if u.guardrails else "  (none selected)"
                book_status = "Customized" if u.book_defaults_edited else "Default generated (ready)"
                if not u.ability_book_path:
                    book_status = "Not generated yet"
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
                    f"Ability book: {u.ability_book_path or '(not generated)'}\n"
                    f"Book defaults: {book_status}\n\n"
                    f"Personality:\n{pers}\n\n"
                    f"Created: {u.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                # Load into form for editing/sync
                self._sheet.populate_from_ai(u)
                self._refresh_capability_buttons(u)
                return

    def _refresh_capability_buttons(self, unit: AIUnit):
        """Rebuild capability action buttons for the selected AI."""
        # Clear existing buttons
        while self._cap_actions_layout.count():
            item = self._cap_actions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        actions = get_actions_for_ai(unit.abilities or unit.capabilities or [])
        if not actions:
            lbl = QLabel("No capability actions available.")
            lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
            self._cap_actions_layout.addWidget(lbl)
            return
        for label, dlg_name, orig in actions:
            btn = QPushButton(label)
            btn.setStyleSheet("background-color: #1565c0; color: white; font-weight: bold;")
            btn.clicked.connect(lambda checked, u=unit, d=dlg_name: self._open_capability_dialog(u, d))
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
        path, _ = QFileDialog.getOpenFileName(
            self, "Drop-In AI", "",
            "AI Files (*.json *.yaml *.py *.zip);;All Files (*)"
        )
        if not path:
            return

        # Disclaimer
        disclaimer = (
            "Importing an AI into Command Nexus will convert it into a Nexus-bound AI. "
            "Its instructions, memory inputs, and behavior rules may be scanned, cleaned, restricted, rewritten, or reorganized "
            "under Command Nexus governance protections. Command Nexus may prevent unsafe content, policy bypasses, malicious instructions, "
            "or restricted proprietary structures from running or exporting. You may delete the imported AI or request a sanitized restore, "
            "but Nexus-generated governance structures, Book/Compendium defaults, internal translations, proprietary enhancements, and unsafe content "
            "are not freely exportable."
        )
        if QMessageBox.question(self, "Import Disclaimer", disclaimer, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return

        dialog = SecurityScanDialog(path, self)
        if dialog.exec() != QDialog.DialogCode.Accepted or not dialog.is_approved():
            QMessageBox.warning(self, "Rejected", "This AI failed security scanning and cannot be imported.")
            return

        # Moirai gate
        allowed, gate_msg = check_action_allowed("import_ai", MoiraiHealthReport())
        if not allowed:
            QMessageBox.critical(self, "Protected Mode", gate_msg)
            return

        # Prompt for use-case assignment
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

        name = Path(path).stem

        # Snapshot original
        snapshots_dir = self._store_dir / "import_snapshots"
        snapshots_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = snapshots_dir / f"{name}_original_{uuid.uuid4().hex[:8]}{Path(path).suffix}"
        try:
            orig_bytes = Path(path).read_bytes()
            snapshot_path.write_bytes(orig_bytes)
            checksum_original = sha256(orig_bytes).hexdigest()
        except Exception:
            QMessageBox.critical(self, "Import Failed", "Could not create original intake snapshot.")
            return

        # Watcher screening (placeholder)
        watcher_result = run_watchers(snapshot_path.read_text(errors="ignore")) if snapshot_path.suffix in {".txt", ".py", ".json", ".yaml"} else run_watchers("")
        if not watcher_result.clean:
            QMessageBox.warning(self, "Sanitized", BLOCK_MESSAGE)

        unit = AIUnit(
            uuid=str(uuid.uuid4())[:8],
            name=name,
            use_case=use_case,
            source=AISource.DROPPED_IN,
            capabilities=["Imported — Reoriented to Book structure"],
            locked=True,
            context_notes=watcher_result.sanitized_text if watcher_result.sanitized_text else "Imported working copy",
        )
        self._units.append(unit)
        item = QListWidgetItem(f"{unit.name} [{unit.use_case.value}] ({unit.source.value})")
        item.setData(Qt.ItemDataRole.UserRole, unit.uuid)
        self._list.addItem(item)
        QMessageBox.information(self, "Imported", f"'{name}' has been scanned, assigned to '{uc_text}', and locked into the Forge.")

        # Record import
        record = ImportedAIRecord(
            import_id=str(uuid.uuid4())[:8],
            original_name=name,
            source_type=Path(path).suffix,
            original_snapshot_path=str(snapshot_path),
            working_copy_ai_uuid=unit.uuid,
            status=ImportStatus.NEXUS_BOUND,
            accepted_disclaimer=True,
            review_notes="Watcher flags: " + ",".join(watcher_result.flags),
            checksum_original=checksum_original,
            checksum_working_copy=sha256((unit.context_notes or "").encode("utf-8")).hexdigest(),
        )
        # Store record alongside AI store
        records_dir = self._store_dir / "import_records"
        records_dir.mkdir(parents=True, exist_ok=True)
        (records_dir / f"{record.import_id}.json").write_text(json.dumps(record.__dict__, default=str, indent=2), encoding="utf-8")

    def _activate_selected(self):
        item = self._list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Select an AI to activate.")
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
                QMessageBox.information(
                    self,
                    "AI Activated",
                    f"'{u.name}' is now active in the Visibility Window.\n\n"
                    f"Ability surfaces:\n{surfaces}\n\n"
                    f"Archive: {u.archive_path or 'N/A'}\nBook: {u.ability_book_path or 'N/A'}\n\n"
                    f"Note: Some abilities are in placeholder mode; backend not connected yet."
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
            QMessageBox.warning(self, "No Selection", "Select an AI to open its Book.")
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
                book_text = Path(target.ability_book_path).read_text(encoding="utf-8")
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
            "Command Nexus may allow deletion, but it will not export unsafe content or protected Nexus-generated structures."
        )
