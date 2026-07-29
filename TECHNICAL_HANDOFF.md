<!-- INTERNAL TECHNICAL SPECIFICATION -->
<!-- NOT FOR PUBLIC RELEASE -->
<!-- For agent use only. Customer-facing content must be curated from this. -->

# Command Nexus — Complete Technical Handoff

**Version:** 0.1.0-prototype  
**Author:** Chad Harris / Pantheon Forge  
**Classification:** Internal — Agent Use Only  
**Last Updated:** June 2026

---

## 1. Executive Summary

Command Nexus is a **local-first, privacy-first desktop AI orchestration platform**. It allows users to create, configure, deploy, and command multiple specialized AI agents from a single unified interface. All data stays on the user's machine. All actions are approval-gated. The system is designed around a "command center" metaphor where the user is the supreme authority (the Owner/Operator) and the AIs are subordinate agents.

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    COMMAND NEXUS                             │
│                     (Desktop App)                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Part 1:    │  │  Part 2:    │  │  Part 3:            │ │
│  │  Visibility │  │  AI Forge   │  │  The Book           │ │
│  │  (Mission   │  │  (Creation  │  │  (Memory &          │ │
│  │   Control)  │  │   Studio)   │  │   Configuration)    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Part 4:    │  │  Core       │  │  Part 5:            │ │
│  │  Upgrades   │  │  Systems    │  │  Aegis Console      │ │
│  │  (Settings) │  │  (Governance│  │  (Owner Control)    │ │
│  └─────────────┘  │   Router    │  └─────────────────────┘ │
│                   │   Audit     │                            │
│                   │   Approval  │                            │
│                   │   License)  │                            │
│                   └─────────────┘                            │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           AI Backend Connectors (External)               │ │
│  │   OpenAI API  |  Anthropic API  |  Local LLM (Ollama)   │ │
│  │   All prompt/response traffic; no file access.          │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

| Layer | Technology |
|-------|-----------|
| UI Framework | PySide6 (Qt 6.11) |
| Language | Python 3.11+ |
| Screen Capture | mss (multi-monitor safe) |
| System Monitoring | psutil |
| Data Storage | JSON files (local filesystem) |
| License Validation | HMAC-SHA256 shared secret |
| AI Backends | External APIs (OpenAI, Anthropic, local) |

### 2.3 Application Entry Point

**File:** `src/main.py`

```
main()
  ├── CommandNexusApp (normal mode)
  │     ├── QApplication + Fusion style
  │     ├── GovernanceEngine
  │     ├── SettingsManager (creates workspace dirs)
  │     ├── ApprovalGate
  │     ├── AuditLogger
  │     ├── ToolRegistry + CommandRouter
  │     ├── LicenseManager (activation check)
  │     ├── LocalCommandServer (starts background)
  │     ├── VisibilityWindow (main window)
  │     ├── WatcherEngine (STABILIZATION mode)
  │     └── OwnerConsole (hidden, Ctrl+Shift+O)
  │
  └── _run_safe_owner_mode (recovery mode)
        └── OwnerConsole only (no customer UI)
```

**Launch scripts:**
- `launch.bat` — Windows double-click launcher
- `python -m src.main` — Direct Python execution
- `python -m src.main --safe-owner-mode` — Emergency recovery
- `python -m src.main --owner-console` — Start with console visible

---

## 3. The Five Parts

### 3.1 Part 1: Visibility Window (`src/parts/visibility/visibility_window.py`)

**Purpose:** Mission control dashboard. The user's primary interface after creating AIs.

**Key Components:**
- **AI Session Selector:** Dropdown of deployed AIs. Selecting one makes it active.
- **Task Queue:** List of missions assigned to the active AI.
- **Mission Control Bar:** STOP, PAUSE/RESUME, REDIRECT, DEMONSTRATE buttons + speed governor.
- **Status Display:** Shows AI state (IDLE, RUNNING, PAUSED, FAILED, COMPLETED).
- **Audit Panes:**
  - Thought Pane — real-time reasoning stream (simulated in prototype)
  - Action Pane — executed actions log
  - Trajectory Pane — high-level mission timeline
- **Viewport Stream:** Live screen capture showing what the AI "sees" (via mss/PIL)
- **Watcher Trust Indicator:** Passive security status (STABILIZATION mode = passive)
- **Navigation Bar:** Buttons to open Forge, Book, Constraints, Governance

**Signals:**
- `open_forge`, `open_book`, `open_constraints`, `open_governance`
- Connected in `main.py` to `_open_forge()`, `_open_book()`, etc.

**Mission Lifecycle:**
1. User selects AI + enters task description
2. `check_action_allowed("mission_start", ...)` — Moirai gate check
3. `CommandRouter.route(...)` — approval gate + audit log
4. Mission timer ticks (simulated execution)
5. At completion: AI returns to IDLE, task marked COMPLETED
6. User can CANCEL mid-mission (AI returns to IDLE)

**Hidden Feature:** Ctrl+Shift+O opens the Owner Console (Aegis Console).

### 3.2 Part 2: AI Forge (`src/parts/forge/forge_window.py`)

**Purpose:** AI creation studio. Where users build and configure their AI agents.

**AI Creation Flow:**
1. User selects Use Case (Individual, Educational, Business, Enterprise, etc.)
2. System suggests capabilities based on use case
3. User customizes:
   - Name and personality traits ( sliders: creativity, formality, caution )
   - Capabilities (multi-select from 30+ options)
   - Guardrails (checkboxes from base + optional lists)
   - Libraries (specialized knowledge packs)
   - Context notes (free-form description)
4. System generates:
   - `AIUnit` data model
   - Ability Book (markdown file)
   - Profile JSON (saved to `ai_store/`)
5. AI appears in Forge list, ready to deploy

**Data Model: `AIUnit` (`src/parts/forge/forge_models.py`)**
```
AIUnit:
  uuid: str (8-char hex)
  name: str
  use_case: UseCaseClass enum
  source: AISource enum (CREATED, DROPPED_IN, IMPORTED)
  capabilities: list[str] (display names)
  abilities: list[str] (canonical names)
  personality_traits: dict (creativity, formality, caution)
  context_notes: str
  guardrails: list[str]
  libraries: list[str]
  locked: bool (protects starter AIs)
  activated: bool
  enabled: bool
  archive_path: str
  ability_book_path: str
  book_defaults_edited: bool
  is_starter: bool
  created_at: datetime
```

**Starter AIs (Pre-Built):**
- Sentinel (General assistant)
- Scholar (Research + analysis)
- Scribe (Writing + creative)
- Tactician (Planning + strategy)
- Hephaestus Relay (Design brief handoff)

Each starter is auto-generated on first run and self-repairs if metadata is missing.

**License Enforcement:**
- Demo mode: Cannot create AIs. Shows pricing.
- Trial: 1 AI max, 15 days
- Starter: 2 AIs max
- Pro: 4 AIs max
- Business: 5 AIs max
- Unlimited: Unlimited AIs

**Key Methods:**
- `_check_ai_creation_allowed()` — license + tier limit check
- `_save_to_store()` — persist AIUnit to JSON
- `_load_stored_ais()` — load all AIs from `ai_store/` on startup
- `_generate_ability_book()` — creates markdown book for the AI

### 3.3 Part 3: The Book (`src/parts/book/book_window.py`)

**Purpose:** The AI's memory, instructions, guardrails, and configuration — all in one editable document.

**Book Structure (Internal):**
```
Book:
├── PART: ACTIVE MEMORY (User-Defined)  ← VISIBLE TO USER
│   ├── Active Instructions (live behavioral rules)
│   ├── Persistent Memory (long-term facts)
│   ├── General Memory (current context)
│   ├── Preferences (communication style, format)
│   └── Rollback Safety (revert instructions)
│
├── PART: INTERNAL CAPABILITY ENTRIES  ← HIDDEN FROM USER
│   ├── Capability Doctrines (allowed/restricted/approval actions)
│   ├── Available Actions (registered capability actions)
│   ├── Pricing Scaffold (tier info)
│   ├── Cross-Capability Workflows
│   ├── Quickstart Steps
│   ├── Common Prompts
│   ├── Editable Guidance (safe vs caution areas)
│   └── Obfuscation Warning (DO NOT MODIFY)
│
└── PART: [Generated capability sections]
    ├── Chatbot surface
    ├── Research surface
    ├── Writer surface
    └── ... (one per ability)
```

**User Interface:**
- Tree view (left): Parts → Chapters → Sections
- Editor (right): Markdown editor for selected node
- Toolbar: Save, Book AI (dialog), Revert, Export

**Book AI Dialog (`src/parts/book/book_ai_dialog.py`):**
Conversational wizard with 7 questions:
1. Purpose — What will this AI primarily do?
2. Audience — Who will it interact with?
3. Instructions — How should it behave?
4. Persistent Memory — What should it always remember?
5. General Memory — What's the current context?
6. Preferences — Communication style preferences
7. Boundaries — What should it never do?

Answers are parsed and structured into the Active Memory part.

**Snapshot & Rollback:**
- `_store_book_snapshot()` — deep copies current book state
- `_revert_book_to_defaults()` — restores from snapshot
- Triggered when user opens Book AI dialog; they can revert after experimenting

**Obfuscation Guardrails:**
- AI NEVER reveals internal capability entries to users
- Users see only Active Memory sections in natural language
- If user asks about "internal structure," AI redirects to conversational guidance

### 3.4 Part 4: Upgrades (Constraints Window) (`src/parts/constraints/constraints_window.py`)

**Purpose:** Settings, preferences, and system configuration.

**Current Features:**
- Basic settings placeholder (UI scaffolded)
- Prepared for future: plugin management, feature toggles, theme settings

**Future Plans:**
- Library marketplace (download specialized knowledge packs)
- Theme customization
- Integration connectors (Slack, Discord, email)
- Backup/restore settings

### 3.5 Part 5: Aegis Console (Owner Console) (`src/parts/owner/owner_console.py`)

**Purpose:** Hidden owner-only control panel for system administration and emergency operations.

**Access:** Ctrl+Shift+O from Visibility Window

**Features:**
- Governance policy viewer
- Approval gate override
- Watcher mode control (STABILIZATION → ACTIVE → REPAIR)
- Audit log viewer
- License management
- System diagnostics
- Emergency shutdown / safe mode activation

**Security:** Only accessible to the owner. No customer-facing documentation.

---

## 4. Core Systems

### 4.1 Governance Engine (`src/core/governance.py`)

**Purpose:** Define and enforce system-wide policies.

**Functions:**
- `verify_self_integrity()` — checks for unauthorized modifications
- `get_policy_summary()` — returns human-readable policy text
- Stores policy as internal string; extensible for future rule-based governance

### 4.2 Command Router (`src/core/command_router.py`)

**Purpose:** Central dispatch for all AI actions. Every outward action routes through here.

**Components:**
- `ToolRegistry` — registers AIs and their capabilities
- `CommandRouter` — routes actions with approval + audit
- `LocalCommandServer` — background server for local tool execution

**Route Flow:**
```
1. Action proposed (e.g., "write file", "send email")
2. Risk assessment (LOW / MEDIUM / HIGH / CRITICAL)
3. Approval gate check (auto-approve vs user prompt)
4. If approved: execute + audit log
5. If denied: return error + log denial
```

**Approval Levels:**
- LOW: Auto-approved (logging only)
- MEDIUM: User prompt (Yes/No dialog)
- HIGH: User prompt with rationale requirement
- CRITICAL: Blocked, requires owner override

### 4.3 Audit Logger (`src/core/audit_logger.py`)

**Purpose:** Immutable log of all significant events.

**Logged Events:**
- AI creation, activation, deletion
- Mission start, completion, cancellation
- Approval granted/denied
- File operations (if any)
- License activation/deactivation
- Security alerts (Watcher)
- Book edits and reverts

**Storage:** JSON lines in workspace directory. Retention varies by tier.

### 4.4 Approval Gate (`src/core/approval_gate.py`)

**Purpose:** User-facing confirmation system for risky actions.

**Features:**
- Configurable per-tier (Trial = strict, Unlimited = relaxed)
- Dialog with rationale, targets, and undo capability
- Timeout handling
- Audit trail integration

### 4.5 License Manager (`src/core/license_manager.py`)

**Purpose:** Subscription validation, tier enforcement, key management.

**License Key Format:**
```
TIER_CODE(2) + EXPIRY_HEX(10) + RANDOM(8) + HMAC(20) = 40 chars
Example: "ST64A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8S9T0"
```

**Tiers:**
| Tier | Monthly | Yearly | AIs | Outward Actions | Workflows |
|------|---------|--------|-----|-----------------|-----------|
| Trial | $10 (one-time) | — | 1 | No | No |
| Starter | $20 | — | 2 | No | Yes |
| Pro | $30 | $324 | 4 | Yes | Yes |
| Business | $50 | $552 | 5 | Yes | Yes |
| Unlimited | $80 | $900 | ∞ | Yes | Yes |

**Yearly Discount Logic:**
- Pro: $30×12 = $360 − $36 = $324 (10% discount)
- Business: $50×12 = $600 − $48 = $552 (8% discount)
- Unlimited: $80×12 = $960 − $60 = $900 (6.25% discount)

### 4.6 Watcher Engine (`src/core/watcher_service.py` + `src/parts/watcher/watcher_window.py`)

**Purpose:** File integrity monitoring and security alerting.

**Modes:**
- **STABILIZATION** (default): Passive monitoring, alerts only on critical changes
- **ACTIVE**: Active scanning, blocks unauthorized modifications
- **REPAIR**: Recovery mode, validates and repairs corrupted files
- **CREATION**: Dev mode, relaxed rules for building
- **DEMO**: Demo mode, minimal monitoring

**Trust System:**
- Baseline hash of critical files
- Periodic re-scan
- If hash mismatch detected → BREACH DETECTED alert
- If all match → TRUSTED status

### 4.7 Stasis Gate (`src/core/stasis_gate.py`)

**Purpose:** Emergency system halt. Like a "big red button."

**States:**
- ACTIVE: Normal operation
- STASIS: All outward actions paused
- LOCKDOWN: Full system lock, owner intervention required

### 4.8 Recursive Scanner (`src/core/recursive_scanner.py`)

**Purpose:** Deep inspection of file system for anomalies.

**Use Cases:**
- Pre-mission workspace validation
- Post-incident forensics
- Startup integrity check

**Threat Levels:** NONE, LOW, MEDIUM, HIGH, CRITICAL

### 4.9 Moirai Health Check (`src/core/nexus_moirai.py`)

**Purpose:** Pre-action health validation. Named after the Fates — checks if an action is "fated" to proceed.

**Checks:**
- System integrity (Watcher trust status)
- License validity
- Stasis gate state
- Required permissions for action

**Usage:** `check_action_allowed(action_name, health_report) → (bool, message)`

---

## 5. AI Avatar System (`src/parts/forge/ai_avatar_widget.py`)

**Purpose:** Visual representation of AI state next to chat interface.

**States:**
- IDLE — green dot, idle animation (breathing/looping)
- LISTENING — blue dot, idle animation
- THINKING — purple dot, idle animation
- TALKING — amber dot, talking animation

**Asset Types (priority order):**
1. **Idle Video** — body movement / breathing loop (`.mp4`, `.webm`, `.mov`)
2. **Talking Video** — head/mouth movement when speaking
3. **GIF Animation** — fallback animated image
4. **Pose Frames** — sequence of images cycled at ~7fps
5. **Static Image** — placeholder with AI initials

**Implementation:**
- `QStackedWidget` with 3 pages: static image, idle video, talking video
- Separate `QMediaPlayer` instances for idle and talking videos
- `set_state(state)` switches pages and starts/stops media

**Factory Function:** `avatar_for_ai(ai_name, avatar_dir)`
- Searches `avatar_dir` for: `body.mp4`/`idle.mp4` (idle), `head.mp4`/`talking.mp4` (talking), `talking.gif`, `pose_*.png`
- Falls back gracefully if videos not found

**Configuration:** `src/core/avatar_config.py`
- Maps specific video files to idle/talking slots
- Currently points to user's 3D motion video files

---

## 6. Data Flows

### 6.1 AI Creation Flow
```
User opens Forge
  → Selects Use Case
    → System suggests capabilities
      → User customizes name, personality, guardrails
        → Click "Save"
          → AIUnit created
            → Ability Book generated (markdown)
              → Profile JSON saved to ai_store/
                → AI appears in Forge list
                  → Can be "Deployed" to Visibility Window
```

### 6.2 Mission Execution Flow
```
User selects AI in Visibility Window
  → Enters task description
    → Clicks "Start Mission"
      → Moirai health check
        → Approval gate (if required)
          → CommandRouter.route()
            → Audit log: MISSION_STARTED
              → Mission timer begins (simulated in prototype)
                → Thought/Action/Trajectory panes update
                  → On completion:
                    → Audit log: MISSION_COMPLETE
                      → AI returns to IDLE
```

### 6.3 Book Edit Flow
```
User opens Book for an AI
  → Views Active Memory sections
    → Makes edits in markdown editor
      → Clicks "Save"
        → Book JSON updated
          → Audit log: BOOK_EDITED
            → If user wants to revert:
              → "Revert to Defaults" button
                → Restores from snapshot
                  → Audit log: BOOK_REVERTED
```

### 6.4 Book AI Dialog Flow
```
User clicks "Book AI" in Book window
  → Dialog opens with 7 questions
    → User answers conversationally
      → System parses answers
        → Structures into Active Memory sections
          → User reviews
            → Clicks "Save to Book"
              → Book updated with new content
                → Snapshot stored for rollback
```

---

## 7. File Structure

```
Command_Nexus/
├── src/
│   ├── main.py                    # Application entry point
│   ├── core/                      # Shared infrastructure
│   │   ├── approval_gate.py
│   │   ├── audit_logger.py
│   │   ├── avatar_config.py       # Avatar video paths
│   │   ├── command_router.py
│   │   ├── constants.py           # Enums, defaults
│   │   ├── governance.py
│   │   ├── license_dialog.py
│   │   ├── license_manager.py
│   │   ├── nexus_moirai.py        # Health checks
│   │   ├── settings_manager.py    # Workspace + config
│   │   ├── stasis_gate.py         # Emergency halt
│   │   ├── recursive_scanner.py   # File anomaly scan
│   │   ├── watcher_service.py     # File integrity
│   │   └── ...
│   ├── parts/                     # UI modules
│   │   ├── visibility/
│   │   │   └── visibility_window.py
│   │   ├── forge/
│   │   │   ├── forge_window.py
│   │   │   ├── ai_avatar_widget.py
│   │   │   ├── capability_actions.py
│   │   │   ├── capability_book_engine.py
│   │   │   └── forge_models.py
│   │   ├── book/
│   │   │   ├── book_window.py
│   │   │   ├── book_ai_dialog.py
│   │   │   └── book_models.py
│   │   ├── constraints/
│   │   │   └── constraints_window.py
│   │   ├── watcher/
│   │   │   └── watcher_window.py
│   │   └── owner/
│   │       └── owner_console.py
│   └── __init__.py
│
├── docs/
│   └── legal/                     # Legal documents
│       ├── TERMS_OF_USE.md
│       ├── PRIVACY_POLICY.md
│       ├── EULA.md
│       ├── TRADEMARK_GUIDE.md
│       ├── LEGAL_README.md
│       ├── ACCEPTABLE_USE_POLICY.md
│       └── DISCLAIMER.md
│
├── ai_store/                      # AI unit JSON files (runtime)
├── books/                         # AI ability books (runtime)
├── archives/                      # AI archives (runtime)
├── logs/                          # Audit logs (runtime)
│
├── AGENT_HANDOFF.md               # Customer-facing brief
├── TECHNICAL_HANDOFF.md           # This document
├── NOTICE-PROPRIETARY.txt         # IP notice
├── requirements.txt               # Python deps
├── launch.bat                     # Windows launcher
└── README.md                      # Project overview
```

**Workspace Directory** (created on first run):
```
%USERPROFILE%/.command_nexus/
├── license.json           # Active license
├── settings.json          # User preferences
├── workspace/             # User data
│   ├── ai_store/         # AI unit profiles
│   ├── books/            # Ability books
│   ├── archives/         # AI archives
│   └── logs/             # Audit trails
```

---

## 8. Security Model

### 8.1 Threat Model

**Trusted:**
- Owner (has owner console access)
- Local filesystem (data never leaves machine by default)

**Untrusted:**
- AI Backends (external APIs — prompts go out, responses come in)
- Network (mitigated by local-first design)
- Third-party integrations (if added later)

### 8.2 Defensive Layers

1. **Approval Gate** — No outward action without user consent
2. **Watcher Engine** — Detects unauthorized file modifications
3. **Stasis Gate** — Emergency halt capability
4. **Moirai Health Check** — Validates system state before actions
5. **Recursive Scanner** — Anomaly detection in workspace
6. **License Validation** — Prevents unauthorized use
7. **Obfuscation Manager** — Hides internal structures from users/AIs

### 8.3 Data Privacy

- All user data stored locally in JSON files
- No telemetry or analytics without explicit opt-in
- AI Backend traffic is the only external data flow
- User controls which backend to connect (OpenAI, Anthropic, local)

---

## 9. Capability System

### 9.1 Capability Registry

30+ capabilities organized by category:
- **Communication:** Chat Companion, Email Sifter, Customer Support
- **Creative:** Creative Writer, Marketing Generator
- **Research:** Research Assistant, Academic Researcher, Business Intelligence
- **Development:** Coding Assistant, IT Operations, Document Processor
- **Education:** Learning Tutor, Classroom Tutor, Lesson Planner
- **Business:** Task/Project Manager, Strategic Planner, Compliance Auditor
- **Specialized:** Legal Document Reviewer, Multi-Department Orchestrator, Hephaestus Relay

### 9.2 Capability Actions

Each capability maps to actions with:
- `inward_surface` — how the AI receives instructions
- `outward_action_path` — what the AI can propose to do
- `required_permissions` — what permissions it needs
- `required_approval_level` — LOW, MEDIUM, HIGH
- `unfinished_safe_fallback` — safe behavior if interrupted

### 9.3 Libraries

Specialized knowledge packs that extend capabilities:
- Communication Library — tone patterns, templates
- Code Safety Library — safe patching, diff workflow
- Research Discipline Library — citations, fact-checking
- Project Memory Library — notes, continuity, context retention
- Hephaestus Briefing Library — design brief formatting

---

## 10. AI Backend Integration

### 10.1 Architecture

Command Nexus is an **orchestration layer**, not an AI model. It:
- Manages AI configurations and memory
- Routes user prompts to the selected backend
- Receives responses and formats them
- Enforces guardrails and approval gates
- Logs all interactions

### 10.2 Supported Backends

| Backend | Connection | Data Flow |
|---------|-----------|-------------|
| OpenAI API | HTTP/HTTPS | Prompts out, completions in |
| Anthropic API | HTTP/HTTPS | Prompts out, completions in |
| Local LLM (Ollama) | Local HTTP | Same machine, no external network |
| Future: Local GPU | Direct | Fully offline |

### 10.3 Prompt Engineering

The Book's Active Memory sections are prepended to every prompt:
1. Active Instructions (behavioral rules)
2. Persistent Memory (long-term facts)
3. General Memory (current context)
4. Preferences (style, format)
5. Guardrails (restrictions)
6. User's actual message

This gives the AI full context without the user re-explaining themselves every time.

---

## 11. Pricing & Licensing (Technical Details)

### 11.1 Tier Comparison

| Feature | Trial | Starter | Pro | Business | Unlimited |
|---------|-------|---------|-----|----------|-----------|
| Price (mo) | $10 | $20 | $30 | $50 | $80 |
| Price (yr) | — | — | $324 | $552 | $900 |
| Max AIs | 1 | 2 | 4 | 5 | ∞ |
| Max Sessions | 1 | 2 | 4 | 5 | ∞ |
| Outward Actions | No | No | Yes | Yes | Yes |
| Cross-Workflows | No | Yes | Yes | Yes | Yes |
| Audit Retention | 7 days | 30 days | 90 days | 365 days | ∞ |
| Libraries | Basic | Basic | Basic+Adv | Basic+Adv | All |
| Duration | 15 days | 30 days | 30 days | 30 days | 30 days |

### 11.2 License Key Generation

```python
import hmac, hashlib, time

def generate_key(tier_code: str, duration_days: int) -> str:
    expiry = int(time.time()) + (duration_days * 86400)
    expiry_hex = f"{expiry:010x}".upper()
    random_part = os.urandom(4).hex().upper()
    payload = f"{tier_code}{expiry_hex}{random_part}"
    hmac_sig = hmac.new(SECRET_KEY, payload.encode(), hashlib.sha256).hexdigest()[:20].upper()
    return f"{tier_code}{expiry_hex}{random_part}{hmac_sig}"
```

**Tier codes:** TR, ST, PR, BU, UN

---

## 12. Future Roadmap

### 12.1 Near-Term (Next 2-4 Weeks)
- [ ] Real AI backend integration (OpenAI/Anthropic connectors)
- [ ] Avatar video integration (3D motion videos)
- [ ] Real mission execution (not simulated)
- [ ] File system operations (with approval gates)
- [ ] Export functionality (PDF, DOCX, etc.)

### 12.2 Medium-Term (2-3 Months)
- [ ] Plugin system for third-party libraries
- [ ] Multi-monitor screen capture
- [ ] Voice input/output
- [ ] Team/shared workspace mode
- [ ] Mobile companion app

### 12.3 Long-Term (6+ Months)
- [ ] Local LLM hosting (fully offline)
- [ ] AI-to-AI communication protocols
- [ ] Custom capability builder (user-defined actions)
- [ ] Marketplace for AI personalities and libraries
- [ ] Enterprise SSO and RBAC

---

## 13. Known Limitations (Prototype Stage)

1. **Simulated Mission Execution** — Mission timer ticks but doesn't execute real actions
2. **No Real AI Backend** — Chat dialogs are UI scaffolded, not connected to LLMs
3. **Avatar Videos Not Wired** — Config exists but paths need user verification
4. **Single User Only** — No multi-user or team support yet
5. **Windows Primary** — launch.bat is Windows-only; Mac/Linux need shell scripts
6. **No Cloud Sync** — Data is purely local; no backup to cloud
7. **License Key Distribution** — Manual generation; no payment processor integration

---

## 14. How to Extend

### 14.1 Adding a New Capability

1. Add to `CAPABILITY_REGISTRY` in `capability_actions.py`
2. Add description to `CAPABILITY_DESCRIPTIONS` in `forge_window.py`
3. Add doctrine to `_ability_doctrine()` in `forge_window.py`
4. Add capability dialog class (optional, for rich UI)
5. Add to `USE_CASE_OPTIONS` for relevant use cases
6. Regenerate ability books for existing AIs

### 14.2 Adding a New Library

1. Define in `NEXUS_LIBRARIES` in `forge_window.py`
2. Add `enabled_by_default` flag
3. Add integration logic in capability execution
4. Update Book generation to include library rules

### 14.3 Adding a New Part (Window)

1. Create `src/parts/newpart/newpart_window.py`
2. Add navigation button in `NavigationBar`
3. Wire signal in `main.py` `_open_newpart()`
4. Add to safe-owner-mode if applicable

---

## 15. Contact & Support

**Project Lead:** Chad Harris  
**Organization:** Pantheon Forge  
**Email:** [To be configured]  
**Website:** [To be configured]

---

*This document is internal and proprietary. Do not distribute. Customer-facing content must be extracted and curated by the agent per owner instructions.*
