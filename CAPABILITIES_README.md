# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.

# Command Nexus™ — Capabilities Guide

> **Avery Logic Works™** — Command Nexus(TM) Capabilities Reference
> Version: 1.0 | Last Updated: 2026-07-04

This guide documents every capability available in Command Nexus™ and how to use each one — **with or without the Chat Companion**.

---

## Table of Contents

1. [Using Capabilities via Chat Companion](#using-capabilities-via-chat-companion)
2. [Using Capabilities via Dedicated Workflow Dialogs](#using-capabilities-via-dedicated-workflow-dialogs)
3. [Core Capabilities](#core-capabilities)
   - [Chat Companion](#chat-companion)
   - [Coding Assistant](#coding-assistant)
   - [Research Assistant](#research-assistant)
   - [Creative Writer](#creative-writer)
   - [Task / Project Manager (Planner)](#task--project-manager-planner)
   - [Personal Organizer (Notebook)](#personal-organizer-notebook)
   - [Document Processor](#document-processor)
   - [Archive](#archive)
   - [Tool User](#tool-user)
   - [Learning Tutor](#learning-tutor)
   - [Business Workflow](#business-workflow)
   - [Hephaestus Relay](#hephaestus-relay)
   - [Customer Support AI](#customer-support-ai)
   - [Enterprise Orchestrator](#enterprise-orchestrator)
4. [Premium Upgrade Capabilities](#premium-upgrade-capabilities)
   - [Team Orchestrator](#team-orchestrator)
   - [Memory Bridge](#memory-bridge)
   - [Visual Canvas](#visual-canvas)
   - [Data Analyst Pro](#data-analyst-pro)
   - [Code Reviewer](#code-reviewer)
   - [API Integrator](#api-integrator)
   - [Knowledge Base Builder](#knowledge-base-builder)
   - [Meeting Facilitator](#meeting-facilitator)
   - [Email Automation](#email-automation)
   - [Calendar Manager](#calendar-manager)
   - [Document Generator](#document-generator)
   - [Translation Expert](#translation-expert)
   - [Presentation Builder](#presentation-builder)
   - [Spreadsheet Wizard](#spreadsheet-wizard)
   - [Legal Assistant](#legal-assistant)
   - [Medical Researcher](#medical-researcher)
   - [Accessibility Assistant](#accessibility-assistant)
   - [Fact Checker](#fact-checker)
   - [Voice Interface](#voice-interface)
   - [Workflow Automator](#workflow-automator)
   - [Security Auditor](#security-auditor)
   - [Competitive Analyst](#competitive-analyst)
   - [Learning Path Creator](#learning-path-creator)
   - [Smart Search](#smart-search)
5. [Approval Gates & Safety](#approval-gates--safety)
6. [Nexus Libraries](#nexus-libraries)

---

## Using Capabilities via Chat Companion

The Chat Companion is the universal interface for ALL capabilities. You don't need to open separate workflow dialogs — just type what you need in the chat.

### How It Works

1. **Type your request** in the chat input field
2. The AI **classifies your intent** (research, code, write, plan, etc.)
3. If the AI needs more information, it **asks you conversationally**:
   - "What would you like me to research?"
   - "What tone? (professional, casual, persuasive)"
   - "Which file are you working with?"
4. **Answer each question** — or type `skip` for optional parameters
5. Once all required info is collected, the AI **executes the capability**
6. Results appear in the chat transcript

### Tips

- **Type `skip`** for optional parameters to use the default
- **Type `cancel`** at any time to abort parameter gathering
- **Be specific** in your initial message to skip the gathering flow entirely
- The AI remembers your preferences across the conversation via Adaptive Memory

### Example Chat Sessions

**Research:**
```
You: Research Python web frameworks
AI: What would you like me to research?
You: Compare FastAPI, Django, and Flask for building REST APIs
AI: Any scope constraints? (e.g., 'last 2 years', 'academic only') — or type 'skip'
You: last 2 years
AI: How would you like the results? (summary, bullet points, comparison table)
You: comparison table
AI: [executes research and returns results]
```

**Coding:**
```
You: I have a bug in my Python script
AI: Describe the code issue or feature you need help with.
You: I'm getting a KeyError when accessing a dictionary key that might not exist
AI: Which file are you working with? (full path, or type 'paste code')
You: C:/Projects/app/main.py
AI: What do you need? (explain, draft diff, outline tests, approved edit)
You: draft diff
AI: [reads the file, drafts a fix, shows the diff]
```

**Creative Writing:**
```
You: Write a blog post about AI privacy
AI: What would you like me to write about?
You: Why local-first AI is better than cloud-based AI for privacy
AI: What tone? (professional, casual, persuasive, technical, humorous)
You: persuasive
AI: Who is the audience? (general public, technical, executive, academic)
You: general public
AI: What format? (article, blog post, email, social media post, script, story)
You: blog post
AI: [generates the blog post]
```

---

## Using Capabilities via Dedicated Workflow Dialogs

If you prefer not to use the Chat Companion, each capability has its own dedicated workflow dialog with structured inputs.

### How to Access

1. **Open AI Forge** — Click "AI Forge" in the navigation bar
2. **Select an AI** — Click on an AI in the AI Library list (left panel)
3. **Open the capability** — Either:
   - Click one of the **action buttons** on the right side of the chat workspace
   - Or open the Chat Companion and click the action button in the "Available Actions" panel

### Workflow Dialog Structure

Each workflow dialog contains:
- **Context banner** at the top showing AI name, use case, and capabilities
- **Input fields** specific to the capability (text areas, dropdowns, buttons)
- **Output area** showing results
- **Approval footer** indicating what requires approval before execution

### Quick Chat Access

From the **Visibility Window** (Command Center):
1. Select an AI from the "Active AI" dropdown
2. Click the **"Quick Chat"** button
3. This opens the Chat Companion directly — no need to go through Forge

---

## Core Capabilities

### Chat Companion

**Dialog:** `ChatCapabilityDialog`
**UI Label:** "Open Workspace Chat"
**Approval Level:** Low
**Use Cases:** All

The central conversation surface. Understands the AI's Book (knowledge compendium) and routes requests to selected capabilities.

**Via Chat:** Just type naturally. The AI figures out what you need.

**Via Dialog:**
1. Open Workspace Chat
2. Type your message in the input field at the bottom
3. Press Send or hit Enter
4. Use the action buttons on the right panel to open specific workflows

**What it does:**
- General conversation and Q&A
- Routes to other capabilities based on your message
- Shows Book Context Summary on the right panel
- Displays available action buttons for the AI's capabilities

---

### Coding Assistant

**Dialog:** `CodingCapabilityDialog`
**UI Label:** "Open Coding Workflow"
**Approval Level:** High (file writes, command execution)
**Use Cases:** Individual, Task-Ready, Enterprise, All-Rounder

Code explanation, diff drafting, test outlining, and approved edit scaffolding.

**Via Chat:** Type something like "fix this bug" or "explain this code" — the AI will ask for the file path and what action you need.

**Via Dialog:**
1. Open Coding Workflow
2. **Tab 1 — Explain & Draft:**
   - Paste code or describe the bug/feature in the text area
   - Click one of: **Explain Code**, **Draft Diff**, **Outline Tests**, **Approved Edit Mode**, **Approved Test/Command**
3. **Tab 2 — Planned Files:** List the files you plan to modify (e.g., `src/utils.py, tests/test_utils.py`)
4. **Tab 3 — Test Commands:** Enter validation commands (e.g., `pytest tests/test_utils.py -v`)

**Actions:**
- **Explain Code** — Walks through purpose, logic paths, and risks
- **Draft Diff** — Shows a proposed diff in show-code-only mode (no files changed)
- **Outline Tests** — Generates a test plan with unit, integration, and edge cases
- **Approved Edit Mode** — Scaffolded path for approved file editing (requires approval)
- **Approved Test/Command** — Scaffolded path for running commands (requires approval)

**Safety:** Defaults to show-code-only mode. Never edits, deletes, or runs anything without explicit approval.

---

### Research Assistant

**Dialog:** `ResearchCapabilityDialog`
**UI Label:** "Open Research Workflow"
**Approval Level:** Medium (network, external search)
**Use Cases:** All

Research query intake, findings, source/citation tracking, and risk comparison.

**Via Chat:** Type "research..." or "look up..." — the AI will ask for scope and format preferences.

**Via Dialog:**
1. Open Research Workflow
2. Enter your research query in the text area (include scope and desired format)
3. Click one of: **Start Research**, **Compare**, **Find Risks**
4. Results appear in the Findings panel (left) and Sources panel (right)

**Actions:**
- **Start Research** — Compiles findings with confidence labels and source citations
- **Compare** — Creates a comparison table between options
- **Find Risks** — Identifies risks and mitigations for the query topic

**Safety:** Live web search is approval-gated. Local research compiles and labels results as simulated when no backend is connected.

---

### Creative Writer

**Dialog:** `CreativeWriterCapabilityDialog`
**UI Label:** "Open Writing Workflow"
**Approval Level:** Medium (file export, publishing)
**Use Cases:** Individual, Educational, Business, Enterprise, All-Rounder

Drafting, outlining, revision, tone/style control, and approved export.

**Via Chat:** Type "write..." or "draft..." — the AI will ask for tone, audience, and format.

**Via Dialog:**
1. Open Writing Workflow
2. Select **Tone** from the dropdown (Professional, Casual, Technical, Persuasive, Neutral)
3. Enter the **Audience** (e.g., "executive team", "customers", "developers")
4. Describe the piece, goal, and constraints in the text area
5. Click one of: **Outline**, **Draft**, **Revise**
6. Click **Copy to Clipboard** to copy the output

**Actions:**
- **Outline** — Generates a structured outline (Introduction, Key Points, Conclusion)
- **Draft** — Produces a full draft in the selected tone for the target audience
- **Revise** — Revises existing text with tracked changes

**Safety:** File export and publishing are approval-gated stubs. Writing is local in-workspace.

---

### Task / Project Manager (Planner)

**Dialog:** `PlannerCapabilityDialog`
**UI Label:** "Open Planner"
**Approval Level:** Medium (task assignment, file organization)
**Use Cases:** All

Goal decomposition, task/project breakdown, risk checks, and approved outward steps.

**Via Chat:** Type "plan..." or "create a roadmap..." — the AI will ask for timeline and constraints.

**Via Dialog:**
1. Open Planner
2. **Optional:** Select a **Project Template** from the dropdown (includes drone builds, robot builds, software projects, and more)
3. Enter your **Goal / Project description** in the text area
4. Click one of: **Generate Plan**, **Flag Risks**, **Convert to Tasks**
5. Click **🛠 Send to Prototyper** to send the plan to the implementation layer

**Actions:**
- **Generate Plan** — Creates a 5-step plan with scope, stakeholders, timeline, risks, and owners
- **Flag Risks** — Identifies dependency, scope, and resource risks with mitigations
- **Convert to Tasks** — Generates a task list with owners and due dates
- **Send to Prototyper** — Sends the plan to the Prototyper (Implementation Layer) for execution

**Project Templates Available:**
- Drone/Quadcopter, Hexacopter, Airplane, Helicopter, Hovercraft, Glider, VTOL, Ornithopter, Rocket, Blimp
- Robot/Rover, Tracked Vehicle, Walker/Legged Robot
- Boat/Hull, Submarine/ROV, Amphibious Vehicle
- Robotic Arm, Enclosure Design, Wearable Device, Custom Prototype

---

### Personal Organizer (Notebook)

**Dialog:** `NotebookCapabilityDialog`
**UI Label:** "Open Notes"
**Approval Level:** Medium (bulk deletion, export)
**Use Cases:** All

Notes, project memory, continuity, recall, tagging, and organizer intake.

**Via Chat:** Type "take notes..." or "remember this..." — the AI will ask for a title and tags.

**Via Dialog:**
1. Open Notes
2. Enter a **Title** for the note
3. Add **Tags** (comma-separated)
4. Enter the note **Body** content
5. Click **Save Note** to store it locally

---

### Document Processor

**Dialog:** `DocumentProcessorCapabilityDialog`
**UI Label:** "Open Document Workflow"
**Approval Level:** Medium (file reads, export)
**Use Cases:** All

Document intake, summarization, extraction, classification, and comparison.

**Via Chat:** Type "summarize this..." or "extract action items..." — the AI will ask for the document text or file path.

**Via Dialog:**
1. Open Document Workflow
2. Paste document text or provide a file path
3. Click one of: **Summarize**, **Extract Action Items**, **Classify**, **Compare**

---

### Archive

**Dialog:** `ArchiveCapabilityDialog`
**UI Label:** "Open Archive"
**Approval Level:** High (file moves, deletion, export)
**Use Cases:** All

Artifact storage, retrieval, indexing, and approved archive movement/export.

**Via Chat:** Type "archive this..." or "save this result..." — the AI will ask for a name and tags.

**Via Dialog:**
1. Open Archive
2. Enter an **Artifact Name**
3. Add **Tags** for retrieval
4. Enter or paste the **Content** to archive
5. Click **Save to Archive**

---

### Tool User

**Dialog:** `ToolUserCapabilityDialog`
**UI Label:** "Open Tool Workflow"
**Approval Level:** High (every tool invocation)
**Use Cases:** Task-Ready, Business, Enterprise, All-Rounder

Tool proposal, rationale, approved invocation scaffold, and status reporting.

**Via Chat:** Type "read file..." or "list files in..." — the AI will ask for confirmation before proceeding.

**Via Dialog:**
1. Open Tool Workflow
2. Describe the tool action you want to perform
3. The AI proposes the tool and explains its purpose
4. Review the rationale and approve/deny

**Safety:** Every tool invocation requires approval and audit routing. No tools are chained automatically.

---

### Learning Tutor

**Dialog:** `TutorCapabilityDialog`
**UI Label:** "Open Tutor Workflow"
**Approval Level:** Low (export only)
**Use Cases:** Educational, Individual, All-Rounder

Educational explanation, quizzes, lessons, study sheets, and accessibility modes.

**Via Chat:** Type "teach me..." or "quiz me on..." — the AI will ask for the topic and your level.

**Via Dialog:**
1. Open Tutor Workflow
2. Enter a **Learning Goal**
3. Select a **Mode** (Explain, Quiz, Study Sheet)
4. The AI generates educational content adapted to your level

---

### Business Workflow

**Dialog:** `BusinessWorkflowCapabilityDialog`
**UI Label:** "Open Business Workflow"
**Approval Level:** Medium (sending, publishing, automation)
**Use Cases:** Business, Enterprise, Task-Ready, All-Rounder

Single-department SOPs, checklists, support drafts, handoffs, and business process planning. **Business Workflow is distinct from Enterprise Orchestrator** — it handles single-department tasks at manager-level approval, while Enterprise handles cross-department coordination at executive-level.

**Sub-Workflows:**

| Sub-Workflow | Trigger Keywords | Description |
|--------------|-----------------|-------------|
| **SOP** | sop, standard operating procedure, procedure | Structured procedures with steps, approval points, escalation paths |
| **Checklist** | checklist, check list, task list, verification list | Operational verification lists with sign-off requirements |
| **Support Draft** | support reply, support response, customer reply | Customer support response drafts (NOT sent — human review required) |
| **Handoff** | handoff, hand off, transition document | Department transition documents with open items and context |
| **Sales** | sales, proposal, outreach, pipeline, CRM, pitch, quota | Sales assets: proposals, outreach templates, pipeline management, pitch scripts |
| **Marketing** | marketing, campaign, content calendar, brand, social media, ad copy, newsletter, SEO | Marketing assets: campaign briefs, content calendars, ad copy, newsletters |
| **Finance** | budget, forecast, invoice, expense, financial, P&L, cash flow, billing | Financial documents: budgets, forecasts, invoices, expense reports |
| **Legal** | contract, NDA, terms of service, privacy policy, legal review, agreement, clause | Legal drafts: contracts, NDAs, terms, policies (requires legal counsel review) |
| **Operations** | process improvement, logistics, supply chain, inventory, quality control, efficiency | Operational plans: process maps, logistics, inventory, quality |
| **HR Draft** | job description, interview guide, performance review template, employee handbook | HR documents: job descriptions, interview guides, performance templates |
| **Automation Plan** | automation, trigger, workflow automation | Automation plans with triggers, steps, approval checkpoints, rollback |

**Via Chat:** Type any of the following — the AI will auto-detect the sub-workflow and ask for the subject:
- "Create an SOP for customer onboarding"
- "Draft a sales proposal for enterprise software"
- "Create a marketing campaign brief for Q3 product launch"
- "Draft a budget forecast for IT department"
- "Create a checklist for server deployment verification"
- "Draft a support reply for a billing inquiry"
- "Create a handoff document for the IT-to-Operations transition"
- "Draft an NDA for a new vendor partnership"

**Via Dialog:**
1. Open Business Workflow
2. Select **Workflow Type** (Auto-Detect, SOP, Checklist, Support Draft, Handoff, Sales, Marketing, Finance, Legal, Operations, HR Draft, Automation Plan)
3. Select **Department** (Auto, Sales, Marketing, Finance, Legal, Operations, HR, IT, Customer Support, Product, Engineering, Administration)
4. Enter the **Business Context / Goal**
5. Click **Generate Business Workflow**
6. Review the structured workflow output with approval gates

**Approval Gates:**
- All business workflows require manager approval before external send, publish, or automation
- Sub-workflow-specific approval chains (e.g., Sales Manager for sales; Legal Counsel for legal; Finance Manager for finance)
- All outputs are draft-safe — nothing is sent or executed without explicit human review

**Safety:**
- Draft-first principle: never send, publish, or execute automatically
- Audit-friendly wording in all outputs
- Separation of recommendation from execution
- Legal drafts must be reviewed by qualified legal counsel before use

---

### Hephaestus Relay

**Dialog:** `HephaestusRelayCapabilityDialog`
**UI Label:** "Open Hephaestus Relay"
**Approval Level:** Medium (export, external handoff)
**Use Cases:** Individual, Task-Ready, Business, All-Rounder

Design idea intake, constraints, materials, scale, unknowns, and Hephaestus-ready handoff brief.

**Via Chat:** Type "design brief..." or "hephaestus..." — the AI will ask for the idea, constraints, and purpose.

**Via Dialog:**
1. Open Hephaestus Relay
2. Describe your **Design Idea**
3. List **Constraints** (materials, size, budget, environment)
4. Describe the **Purpose** or use case
5. Click **Generate Handoff Brief**

---

### Customer Support AI

**Dialog:** `CustomerAIWindow`
**UI Label:** "Open Customer Support"
**Approval Level:** None (all local, safe)
**Use Cases:** All

RESTRICTED customer-facing AI for support. Learns from interactions but NEVER reveals internal Book mechanics or architecture.

**Via Chat:** Type "customer support..." or "help desk..." — the AI will ask for the inquiry and context.

**Via Dialog:**
1. Open Customer Support
2. Enter the customer's **Inquiry**
3. Add **Context** (customer tier, previous tickets, account info)
4. The AI generates an appropriate customer-facing response

**Safety:** Never reveals Book internals, scaffolding, or architecture. Uses only customer-appropriate terminology.

---

### Enterprise Orchestrator

**Dialog:** `EnterpriseOrchestratorCapabilityDialog`
**UI Label:** "Open Enterprise Orchestrator"
**Approval Level:** High (executive approval required for all outward actions)
**Use Cases:** Enterprise, All-Rounder
**Classification:** Company Confidential

Enterprise orchestration layer that routes HR, operations, compliance, policy review, analytics, and cross-department workflows into one organized orchestration layer. **Enterprise is distinct from Business Workflow:**

| Feature | Business Workflow | Enterprise Orchestrator |
|---------|-------------------|------------------------|
| Scope | Single department | Cross-department, company-wide |
| Classification | Internal | Company Confidential |
| Approval | Manager-level | Executive-level |
| Audit Trail | Optional | Mandatory |
| Use Case | SOPs, checklists, drafts | Policy review chains, compliance audits, executive briefs |

**Sub-Workflows:**

| Sub-Workflow | Trigger Keywords | Description |
|--------------|-----------------|-------------|
| **HR Orchestration** | onboarding, offboarding, performance review, grievance, personnel | Personnel actions, HR policy compliance, notification chains |
| **Compliance Audit** | compliance, GDPR, SOC2, HIPAA, PCI, ISO 27001, regulatory | Regulatory checks, gap analysis, remediation tickets, evidence trails |
| **Policy Review** | policy review, policy draft, policy update, governance policy | Versioned policy changes with multi-stage review chain (SME → Dept Head → Legal → Executive) |
| **Operations Coordination** | operations, incident response, deployment, resource allocation | Severity assessment (P1-P4), response team activation, cross-team handoffs |
| **Enterprise Analytics** | KPI, dashboard, executive metrics, trend analysis, quarterly report | Metrics framework, baselines, targets, executive analytics reports |
| **Executive Brief** | executive brief, board prep, leadership summary, decision memo, c-suite | Structured briefs for leadership with review chain (Chief of Staff → Legal → Sponsor) |
| **Cross-Department** | cross-department, coordination, handoff, escalation | Multi-department coordination with shared timelines and handoff protocols |

**Via Chat:** Type any of the following — the AI will auto-detect the sub-workflow and ask for missing details:
- "Run GDPR compliance audit for Q3 data processing"
- "Coordinate onboarding for 15 new hires across HR, IT, and Facilities"
- "Draft policy review chain for updated remote work security policy"
- "Coordinate P1 incident response across Engineering and Customer Support"
- "Generate executive brief for board meeting on Q3 performance"
- "Set up KPI dashboard for enterprise-wide quarterly metrics"

**Via Dialog:**
1. Open Enterprise Orchestrator
2. Select **Workflow Type** (HR, Compliance, Policy Review, Operations, Analytics, Executive Brief, Cross-Department)
3. Set **Department Scope** (All Departments, HR, IT, Security, Operations, Finance, Legal, Compliance, Engineering, Sales, Marketing, or custom)
4. Set **Priority** (P1-Critical, P2-High, P3-Medium, P4-Low)
5. Enter the **Enterprise Task / Objective**
6. Click **Generate Enterprise Workflow**
7. Review the structured workflow output with approval gates and audit trail references

**Approval Gates:**
- All enterprise workflows require executive approval before any outward action
- Sub-workflow-specific approval chains (e.g., HR Director + Legal for HR; Compliance Officer + Legal for Compliance)
- All actions are audit-logged with timestamps, actor IDs, and evidence references

**Safety:**
- Company-confidential classification enforced on all outputs
- No external disclosure of company secrets, internal procedures, or personnel data
- Enterprise workflows are distinct from business workflows — they handle company-secrets-level coordination
- Non-repudiation enforced through audit trail

---

## Premium Upgrade Capabilities

These capabilities are available through the Upgrades store and require a paid tier.

### Team Orchestrator

**Dialog:** `TeamOrchestratorDialog`
**UI Label:** "Open Team Orchestrator"
**Approval Level:** High
**Use Cases:** Business, Enterprise, All-Rounder

Multi-AI coordination hub. Orchestrate multiple AIs working on the same project.

**Via Chat:** Type "team of AI..." or "orchestrate..." — the AI will ask for the project and roles.

**Via Dialog:**
1. Open Team Orchestrator
2. Enter the **Project** description
3. Define **AI Roles** (researcher, writer, reviewer, etc.)
4. Assign tasks and monitor progress
5. Review AI consensus before external actions

---

### Memory Bridge

**Dialog:** `MemoryBridgeDialog`
**UI Label:** "Open Memory Bridge"
**Approval Level:** Medium
**Use Cases:** Individual, Educational, Business, Enterprise, All-Rounder

Persistent cross-session memory with context continuity.

**Via Chat:** Type "remember this..." or "what did we discuss..." — the AI will search its memory.

**Via Dialog:**
1. Open Memory Bridge
2. Select **Action** (Recall, Save, Search, Delete)
3. Enter your **Query** or content
4. View conversation history, learned preferences, and context summaries

---

### Visual Canvas

**Dialog:** `VisualCanvasDialog`
**UI Label:** "Open Visual Canvas"
**Approval Level:** Medium
**Use Cases:** Individual, Educational, Business, Enterprise, All-Rounder

AI-powered image generation, editing, and visual concept development.

**Via Chat:** Type "generate image..." or "create diagram..." — the AI will ask for the concept and style.

**Via Dialog:**
1. Open Visual Canvas
2. Describe the **Visual Concept**
3. Select a **Style** (diagram, illustration, icon, abstract)
4. Generate and review the visual

---

### Data Analyst Pro

**Dialog:** `DataAnalystDialog`
**UI Label:** "Open Data Analyst"
**Approval Level:** High
**Use Cases:** Business, Enterprise, All-Rounder

Advanced data analysis with visualization, statistical insights, and trend detection.

**Via Chat:** Type "analyze data..." or "create a chart..." — the AI will ask for the data source and analysis type.

**Via Dialog:**
1. Open Data Analyst
2. Import data (paste CSV or provide file path)
3. Select **Analysis Type** (trends, summary statistics, comparison, forecast)
4. View charts, statistical summaries, and insights

---

### Code Reviewer

**Dialog:** `CodeReviewerDialog`
**UI Label:** "Open Code Reviewer"
**Approval Level:** High
**Use Cases:** Individual, Task-Ready, Enterprise, All-Rounder

Automated code review, quality analysis, security scanning, and optimization suggestions.

**Via Chat:** Type "review code..." or "security scan..." — the AI will ask for the code and focus area.

**Via Dialog:**
1. Open Code Reviewer
2. Paste code or provide a file path
3. Select **Focus** (security, performance, style, all)
4. View quality metrics, security scan results, and optimization suggestions

---

### API Integrator

**Dialog:** `APIIntegratorDialog`
**UI Label:** "Open API Integrator"
**Approval Level:** High
**Use Cases:** Business, Enterprise, All-Rounder

Connect AIs to external APIs, webhooks, and services.

**Via Chat:** Type "connect API..." or "set up webhook..." — the AI will ask for the service and purpose.

**Via Dialog:**
1. Open API Integrator
2. Enter the **Service/API** name
3. Describe the **Purpose** of the integration
4. Configure endpoint, authentication, and request templates

---

### Knowledge Base Builder

**Dialog:** `KnowledgeBaseDialog`
**UI Label:** "Open Knowledge Base Builder"
**Approval Level:** Medium
**Use Cases:** Business, Enterprise, All-Rounder

Create, structure, and maintain organized knowledge bases.

**Via Chat:** Type "knowledge base..." or "build documentation..." — the AI will ask for the topic and structure.

**Via Dialog:**
1. Open Knowledge Base Builder
2. Enter the **Topic**
3. Select **Structure** (hierarchical, flat, tagged)
4. Build categories, articles, and search index

---

### Meeting Facilitator

**Dialog:** `MeetingFacilitatorDialog`
**UI Label:** "Open Meeting Facilitator"
**Approval Level:** Medium
**Use Cases:** Business, Enterprise, All-Rounder

AI-powered meeting management with agenda creation, note-taking, and action item extraction.

**Via Chat:** Type "meeting agenda..." or "action items..." — the AI will ask for the meeting type and topic.

**Via Dialog:**
1. Open Meeting Facilitator
2. Select **Meeting Type** (planning, standup, retrospective, brainstorming)
3. Enter the **Topic**
4. Set **Duration** (30 min, 1 hour, etc.)
5. Generate agenda, take notes, extract action items

---

### Email Automation

**Dialog:** `EmailAutomationDialog`
**UI Label:** "Open Email Automation"
**Approval Level:** High
**Use Cases:** Business, Enterprise, All-Rounder

Smart email drafting, categorization, priority filtering, and automated response suggestions.

**Via Chat:** Type "draft email..." or "email template..." — the AI will ask for the type, subject, and recipient.

**Via Dialog:**
1. Open Email Automation
2. Select **Email Type** (reply, new message, follow-up, template)
3. Enter the **Subject**
4. Select **Recipient Type** (client, team, vendor, internal)
5. Generate draft — sending requires approval

---

### Calendar Manager

**Dialog:** `CalendarManagerDialog`
**UI Label:** "Open Calendar Manager"
**Approval Level:** Medium
**Use Cases:** Individual, Business, Enterprise, All-Rounder

Intelligent scheduling, conflict detection, and meeting time suggestions.

**Via Chat:** Type "schedule..." or "find meeting time..." — the AI will ask for the details.

**Via Dialog:**
1. Open Calendar Manager
2. Select **Task** (find meeting time, detect conflicts, optimize schedule)
3. Enter **Details** (participants, duration, time range)
4. View suggestions and conflict alerts

---

### Document Generator

**Dialog:** `DocumentGeneratorDialog`
**UI Label:** "Open Document Generator"
**Approval Level:** Medium
**Use Cases:** Individual, Educational, Business, Enterprise, All-Rounder

Create professionally formatted documents with templates and multi-format export.

**Via Chat:** Type "generate report..." or "create proposal..." — the AI will ask for the type, subject, and format.

**Via Dialog:**
1. Open Document Generator
2. Select **Document Type** (proposal, report, memo, letter, contract)
3. Enter the **Subject**
4. Select **Output Format** (PDF, Word, HTML, Markdown)
5. Generate and review before export

---

### Translation Expert

**Dialog:** `TranslationExpertDialog`
**UI Label:** "Open Translation Expert"
**Approval Level:** Low
**Use Cases:** Individual, Educational, Business, Enterprise, All-Rounder

Multi-language translation with context awareness and cultural adaptation.

**Via Chat:** Type "translate..." — the AI will ask for the text and target language.

**Via Dialog:**
1. Open Translation Expert
2. Paste the **Text** to translate
3. Select **Target Language**
4. Select **Tone** preference (optional)
5. Generate translation with back-translation check

---

### Presentation Builder

**Dialog:** `PresentationBuilderDialog`
**UI Label:** "Open Presentation Builder"
**Approval Level:** Medium
**Use Cases:** Individual, Educational, Business, Enterprise, All-Rounder

Create slide decks with AI-generated content, design suggestions, and speaker notes.

**Via Chat:** Type "presentation..." or "slides..." — the AI will ask for the topic, slide count, and audience.

**Via Dialog:**
1. Open Presentation Builder
2. Enter the **Topic**
3. Set **Slide Count** (or auto-determine)
4. Select **Audience** (executive, technical, general, academic)
5. Generate slides with content, design suggestions, and speaker notes

---

### Spreadsheet Wizard

**Dialog:** `SpreadsheetWizardDialog`
**UI Label:** "Open Spreadsheet Wizard"
**Approval Level:** Medium
**Use Cases:** Individual, Business, Enterprise, All-Rounder

Advanced spreadsheet automation with formula generation and data analysis.

**Via Chat:** Type "formula..." or "spreadsheet..." — the AI will ask for the task and data.

**Via Dialog:**
1. Open Spreadsheet Wizard
2. Select **Task** (formula, pivot table, data analysis, automation)
3. Paste or describe the **Data** / ranges
4. Generate formulas, pivot tables, or analysis

---

### Legal Assistant

**Dialog:** `LegalAssistantDialog`
**UI Label:** "Open Legal Assistant"
**Approval Level:** High
**Use Cases:** Business, Enterprise, All-Rounder

Legal document analysis, contract review, clause identification, and compliance checking.

**Via Chat:** Type "legal..." or "contract review..." — the AI will ask for the document and focus.

**Via Dialog:**
1. Open Legal Assistant
2. Paste the **Document** text or provide a file path
3. Select **Focus** (risks, termination clauses, compliance, redline)
4. View clause extraction, risk flags, and compliance checklist

> ⚠️ **NOT a substitute for a licensed attorney.** For research only.

---

### Medical Researcher

**Dialog:** `MedicalResearcherDialog`
**UI Label:** "Open Medical Researcher"
**Approval Level:** High
**Use Cases:** Enterprise, All-Rounder

Medical literature search, clinical trial analysis, and evidence-based summaries.

**Via Chat:** Type "medical research..." or "clinical trial..." — the AI will ask for the topic and focus.

**Via Dialog:**
1. Open Medical Researcher
2. Enter the **Topic** or treatment
3. Select **Focus** (clinical trials, drug interactions, evidence summary)
4. View literature search results and evidence summaries

> ⚠️ **For research only, not medical advice.**

---

### Accessibility Assistant

**Dialog:** `AccessibilityAssistantDialog`
**UI Label:** "Open Accessibility Assistant"
**Approval Level:** Low
**Use Cases:** Individual, Educational, Enterprise, All-Rounder

Accessibility support with screen reader optimization, TTS, and adaptive interface.

**Via Chat:** Type "read aloud..." or "accessibility..." — the AI will ask for the need and content.

**Via Dialog:**
1. Open Accessibility Assistant
2. Select **Need** (read aloud, text resize, screen reader format, simplify)
3. Paste **Content** or provide a file path
4. Receive accessible output

---

### Fact Checker

**Dialog:** `FactCheckerDialog`
**UI Label:** "Open Fact Checker"
**Approval Level:** Medium
**Use Cases:** Individual, Educational, Business, Enterprise, All-Rounder

Automated fact verification, claim credibility scoring, and bias detection.

**Via Chat:** Type "fact check..." or "verify claim..." — the AI will ask for the claim and sources.

**Via Dialog:**
1. Open Fact Checker
2. Enter the **Claim** to verify
3. Add specific **Sources** to check against (optional)
4. View verification status, credibility score, and bias indicators

---

### Voice Interface

**Dialog:** `VoiceInterfaceDialog`
**UI Label:** "Open Voice Interface"
**Approval Level:** Low
**Use Cases:** Individual, Educational, Business, Enterprise, All-Rounder

Natural voice conversation using speech recognition and text-to-speech.

**Via Chat:** Type "voice..." or "read out loud..." — the AI will ask for the action and content.

**Via Dialog:**
1. Open Voice Interface
2. Select **Action** (read text aloud, start voice conversation, change voice settings)
3. Paste text to read or describe the voice interaction
4. Activate microphone and converse

---

### Workflow Automator

**Dialog:** `WorkflowAutomatorDialog`
**UI Label:** "Open Workflow Automator"
**Approval Level:** High
**Use Cases:** Business, Enterprise, All-Rounder

Build automated multi-step workflows with triggers, conditions, and error handling.

**Via Chat:** Type "automate workflow..." or "process automation..." — the AI will ask for the trigger and actions.

**Via Dialog:**
1. Open Workflow Automator
2. Define the **Trigger** (new email, schedule, manual, webhook)
3. Describe the **Actions** step by step
4. Add conditions and error handling
5. Test before activating

---

### Security Auditor

**Dialog:** `SecurityAuditorDialog`
**UI Label:** "Open Security Auditor"
**Approval Level:** High
**Use Cases:** Enterprise, All-Rounder

Comprehensive security analysis of code, documents, and configurations.

**Via Chat:** Type "security audit..." or "vulnerability scan..." — the AI will ask for the target and scope.

**Via Dialog:**
1. Open Security Auditor
2. Paste code/config or provide a file path
3. Select **Scope** (vulnerabilities, compliance, best practices, all)
4. View scan results, vulnerability list, risk ratings, and remediation guide

---

### Competitive Analyst

**Dialog:** `CompetitiveAnalystDialog`
**UI Label:** "Open Competitive Analyst"
**Approval Level:** Medium
**Use Cases:** Business, Enterprise, All-Rounder

Market and competitor analysis with SWOT generation and strategic positioning.

**Via Chat:** Type "competitor analysis..." or "SWOT..." — the AI will ask for the competitor and focus.

**Via Dialog:**
1. Open Competitive Analyst
2. Enter the **Competitor** or market
3. Select **Focus** (positioning, pricing, SWOT, strategy)
4. View competitor profiles, market trends, and SWOT analysis

---

### Learning Path Creator

**Dialog:** `LearningPathCreatorDialog`
**UI Label:** "Open Learning Path Creator"
**Approval Level:** Medium
**Use Cases:** Educational, Business, Enterprise, All-Rounder

Design structured learning paths with curriculum sequencing and assessments.

**Via Chat:** Type "learning path..." or "curriculum..." — the AI will ask for the subject, level, and duration.

**Via Dialog:**
1. Open Learning Path Creator
2. Enter the **Subject**
3. Select **Level** (beginner, intermediate, advanced)
4. Set **Duration** (4 weeks, self-paced, etc.)
5. Generate curriculum with learning objectives, content sequence, and assessments

---

### Smart Search

**Dialog:** `SmartSearchDialog`
**UI Label:** "Open Smart Search"
**Approval Level:** Medium
**Use Cases:** Individual, Educational, Business, Enterprise, All-Rounder

Advanced search across documents, web, databases, and knowledge bases.

**Via Chat:** Type "smart search..." or "search across..." — the AI will ask for the query and sources.

**Via Dialog:**
1. Open Smart Search
2. Enter your **Query** in natural language
3. Select **Sources** (documents, web, knowledge base, all)
4. View clustered, ranked results with source filtering

---

## Approval Gates & Safety

Every capability in Command Nexus™ operates under a layered safety system:

### Approval Levels

| Level | Meaning | Examples |
|-------|---------|----------|
| **None** | All local, no outward actions | Customer Support AI |
| **Low** | Export/file writes gated | Chat, Tutor, Translation, Voice, Accessibility |
| **Medium** | Network, external actions gated | Research, Writing, Planning, Documents, Notes, Business |
| **High** | Every risky action gated | Coding, Tools, Archive, Security, API, Workflow Automator, Enterprise Orchestrator |

### Safety Rules

1. **Show before execute** — All outward actions show what they'll do before doing it
2. **Approval required** — File writes, command execution, network access, and external communication all require explicit approval
3. **Audit logging** — Every action is logged for review
4. **Watcher monitoring** — Background SHA-256 integrity scanning runs every 5 seconds
5. **Safe fallback** — If a backend is not connected, the capability returns a safe stub status instead of pretending

### Moirai Protected Mode

The Moirai system can block actions if:
- Protected mode is active (health check fails)
- Approved Use Locks restrict the capability
- Watcher tripwire is in lockdown

---

## Nexus Libraries

Libraries are knowledge packs, templates, and workflows that AIs can access. They are NOT abilities — they enhance existing capabilities.

| Library | Category | Description |
|---------|----------|-------------|
| Communication Library | Core | Conversation patterns, response formatting |
| Governance UX Library | Core | Approval flows, audit-friendly wording |
| Research Discipline Library | Core | Source citation, speculation flagging |
| Code Safety Library | Core | Secure coding patterns, edit safety |
| Project Memory Library | Core | Continuity, context preservation |
| Hephaestus Briefing Library | Specialized | Design brief formatting, constraint analysis |
| Team Coordination Library | Premium | Multi-AI role assignment, handoff protocols |
| Project Management Library | Premium | Task tracking, milestone planning |
| Memory Persistence Library | Premium | Cross-session memory, preference learning |
| Privacy Controls Library | Premium | Data retention, memory deletion |
| Visual Arts Library | Premium | Image composition, style guides |
| Brand Guidelines Library | Premium | Brand consistency, visual identity |
| Creative Tools Library | Premium | Creative process support |
| Data Science Library | Premium | Statistical methods, data analysis |
| Statistics Library | Premium | Statistical analysis, significance testing |
| Visualization Library | Premium | Chart generation, data visualization |
| Security Audit Library | Premium | Vulnerability patterns, security best practices |
| Vulnerability Database | Premium | Known vulnerability reference |
| Incident Response Library | Premium | Security incident handling |
| Market Intelligence Library | Premium | Market analysis, competitor tracking |
| Strategic Analysis Library | Premium | Strategy frameworks, positioning |
| Business Intelligence Library | Premium | BI reporting, metrics |
| Instructional Design Library | Premium | Curriculum design, learning theory |
| Assessment Library | Premium | Test generation, evaluation |
| Educational Technology Library | Premium | EdTech integration |
| Search Technology Library | Premium | Search algorithms, indexing |
| Information Retrieval Library | Premium | Document retrieval, ranking |
| Integration Library | Premium | API integration patterns |
| API Security Library | Premium | Secure API handling |
| Network Governance Library | Premium | Network access control |
| Knowledge Management Library | Premium | Knowledge organization, tagging |
| Documentation Library | Premium | Documentation patterns, templates |
| Time Management Library | Premium | Schedule optimization |
| Document Design Library | Premium | Document formatting, layout |
| Export Library | Premium | Multi-format export |
| Translation Library | Premium | Translation patterns, glossary |
| Cultural Context Library | Premium | Cultural adaptation, localization |
| Speech Recognition Library | Premium | Voice processing |
| Voice UX Library | Premium | Voice interaction design |
| Accessibility Library | Premium | WCAG compliance, assistive tech |
| Universal Design Library | Premium | Inclusive design patterns |
| Assistive Technology Library | Premium | AT integration |
| Media Literacy Library | Premium | Source evaluation, bias detection |
| Critical Thinking Library | Premium | Argument analysis, logic |
| Workflow Automation Library | Premium | Automation patterns |
| Email Safety Library | Premium | Email security, phishing prevention |
| Spreadsheet Library | Premium | Formula patterns, data organization |
| Data Analysis Library | Premium | Data analysis patterns |
| Legal Research Library | Premium | Legal document patterns |
| Compliance Library | Premium | Regulatory compliance |
| Risk Assessment Library | Premium | Risk identification, scoring |
| Medical Research Library | Premium | Medical literature patterns |
| Evidence-Based Medicine Library | Premium | EBM methodology |
| Presentation Design Library | Premium | Slide design, visual communication |
| Visual Communication Library | Premium | Visual storytelling |
| Public Speaking Library | Premium | Presentation skills, speaker notes |

---

## Quick Reference: Chat Keywords

Type these keywords in the Chat Companion to activate specific capabilities:

| Keyword | Capability |
|---------|-----------|
| research, search, look up | Research |
| code, bug, python, debug | Coding Assistant |
| read file, list files, run command | Tool User |
| write, draft, story, blog | Creative Writer |
| plan, roadmap, milestone | Planner |
| document, summarize, extract | Document Processor |
| note, remember, take notes | Notebook |
| archive, store this | Archive |
| teach, quiz, study, tutor | Learning Tutor |
| customer support, help desk | Customer Support AI |
| sop, checklist, business | Business Workflow |
| compliance audit, policy review, executive brief, enterprise, GDPR, SOC2, cross-department, incident response, KPI dashboard | Enterprise Orchestrator |
| hephaestus, design brief | Hephaestus Relay |
| analyze data, dataset, chart | Data Analyst Pro |
| code review, security scan | Code Reviewer |
| meeting, agenda, standup | Meeting Facilitator |
| security audit, vulnerability | Security Auditor |
| draft email, email template | Email Automation |
| schedule, find meeting time | Calendar Manager |
| generate report, create proposal | Document Generator |
| translate, translation | Translation Expert |
| presentation, slides | Presentation Builder |
| formula, spreadsheet, excel | Spreadsheet Wizard |
| legal, contract review | Legal Assistant |
| medical research, clinical trial | Medical Researcher |
| read aloud, accessibility | Accessibility Assistant |
| fact check, verify claim | Fact Checker |
| voice, speech, read out loud | Voice Interface |
| automate workflow, trigger | Workflow Automator |
| competitor, SWOT, market | Competitive Analyst |
| learning path, curriculum | Learning Path Creator |
| smart search, search across | Smart Search |
| team of ai, orchestrate | Team Orchestrator |
| remember this, recall | Memory Bridge |
| generate image, diagram | Visual Canvas |
| connect api, webhook | API Integrator |
| knowledge base, wiki | Knowledge Base Builder |

---

*Command Nexus™ — Command Your AI Army.*
*Copyright (c) 2026 Avery Logic Works™. All Rights Reserved.*
