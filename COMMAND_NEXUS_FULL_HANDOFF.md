# Command Nexus Lattice — Complete System Handoff

**Version:** 1.0.0 | **Copyright:** (c) 2026 Avery Logic Works — Command Nexus(TM) — All Rights Reserved

---

## 1. What Command Nexus Is

Desktop AI agent management platform. Users create, configure, deploy, and interact with multiple AI agents — each with different capabilities, personalities, knowledge bases, and guardrails. **Local-first**: models can be local GGUF files or local Ollama/LM Studio. No data leaves the machine unless user configures cloud API.

**Core philosophy: never fake completion.** If a capability cannot do something, it pauses honestly. Enforced at runtime level.

**Principles:** Local-first | Honest execution | Human-in-the-loop | Capability-scoped | Guardrail-sealed | Lattice-protected

---

## 2. Creator Context

**Company:** Avery Logic Works | **Product:** Command Nexus(TM) | **License:** Proprietary

**IP Protection:** Watermark headers on every file | `ip_watermark.py` (fingerprinting) | `obfuscation_manager.py` (hides structures) | `coherence_matrix.py` (lattice integrity) | `tripwire_manager.py` (tamper detection) | `termination_beacon.py` (phones home on termination)

**Monetization:** Freemium + tiered subscription. Most capabilities free. Tiers control capabilities-per-AI and unlock premium. PayPal built in.

---

## 3. User Context

**Users:** Individuals, Educational, Task-focused, Business, Enterprise, Financial Gainers, Memory Savers, All-Rounders

**What user does:** Creates AI in Forge → edits Knowledge Book → deploys to Mission Control → gives tasks (text/voice) → reviews results → approves risky actions → manages resources → schedules missions

**Workspace (`~/CommandNexusWorkspace/`):** `ai_store/`, `books/`, `memory/`, `notes/`, `runtime_archive/`, `workspace/`, `logs/`, `audit/`, `upgrades/`. Settings at `~/CommandNexus/config.json`.

---

## 4. AI Context

**AIUnit** (`src/parts/forge/forge_models.py`): uuid, name, use_case, capabilities, abilities, personality_traits, locked, activated, enabled, ability_book_path, ability_surfaces, guardrails, libraries, is_starter

**Lifecycle:** Created in Forge → Saved as JSON → Knowledge Book generated (.nbk encrypted) → Activated in Mission Control → Missions dispatched → Results displayed → Memory updated → Archived

**Knowledge Book:** Structured, human-editable, encrypted. Sections: Identity/Purpose, Quickstart, Capability Attachments, Cross-Capability Workflows, Approval Required, Allowed/Restricted Areas, Response Style, Glossary, Idioms. XOR cipher with UUID-derived key.

**Background Intelligence (never named in output):** Compendium of Truth (fact categories), Intelligent Memory Router (routes memories to layers by intent)

---

## 5. Architecture

```
CommandNexusApp (src/main.py)
├── GovernanceEngine (immutable safety, singleton, sealed)
├── SettingsManager (JSON config, singleton)
├── ApprovalGate (human-in-the-loop for risky actions)
├── AuditLogger (action audit trail)
├── ToolRegistry (registered AI agents)
├── CommandRouter (approval + audit routing)
├── ResourceGate (system resource monitor, singleton)
├── LicenseManager (subscription validation, singleton)
├── WatcherEngine/Tripwire (anti-tamper)
├── CoherenceMatrix (structural integrity lattice)
├── IngestionSecurityGate (external data security)
├── LocalCommandServer (HTTP 127.0.0.1:8765)
├── VisibilityWindow (main window — Mission Control)
├── AIForgeWindow (AI creation, lazy)
├── BookWindow (Knowledge Book editor, lazy)
├── ConstraintsWindow (resource constraints, lazy)
├── CustomerAIWindow (customer support AI, lazy)
├── OwnerConsole (hidden, Ctrl+Shift+O)
└── DemoTourController (first-run tour)
```

**Signal flow:** User Input → `_on_start_mission()` → Usage Policy → Parental Controls → Governance Sanitizer → CommandRouter → `NexusAIRuntime.run()` → `_classify()` → `_check_guardrails()` (4 layers) → `_run_<intent>()` → output screening → memory update → result displayed + TTS

---

## 6. Startup Sequence

1. QApplication + theme | 2. GovernanceEngine (sealed) | 3. SettingsManager | 4. Approval/Audit/Registry/Router | 5. ResourceGate | 6. Build fingerprint | 7. LicenseManager (non-fatal) | 8. WatcherEngine (DEV/STABILIZATION/RELEASE/LOCKDOWN) | 9. CoherenceMatrix (non-fatal) | 10. License termination check | 11. IngestionSecurityGate | 12. License activation dialog | 13. LocalCommandServer | 14. VisibilityWindow | 15. Nav signals wired | 16. Auto-load stored AIs | 17. Security update check | 18. Governance disclaimer | 19. Tour | 20. OwnerConsole

**Non-fatal design:** Every security component degrades gracefully. App continues with warnings.

---

## 7. The Forge

**File:** `src/parts/forge/forge_window.py` — `AIForgeWindow`

**Creation flow:** Name → Use Case → Capabilities (filtered by use case + tier) → Personality sliders → Guardrails (base + optional) → Libraries → Preview → Save (JSON) → Generate Book (.nbk) → Activate

**Starter AIs:** Auto-created on first run. **Easy Mode:** Child-friendly quick-start with emoji, simple questions, 4 examples per capability.

**License limits:** Demo=disabled, Trial=1, Starter=2, Pro=4, Business=5, Unlimited=unlimited

---

## 8. Use Cases

8 use cases determine available capabilities:

| Use Case | Focus |
|---|---|
| Individual | Personal productivity |
| Educational | Teaching/learning with academic integrity |
| Task-Ready | Documents, meetings, data entry, workflows |
| Business | Business operations |
| Enterprise | Compliance, security, multi-department |
| Financial Gainer | Money-making (all advisory, never transacts) |
| Memory Saver | Recording, recall, audit trails |
| All-Rounder | Everything |

`USE_CASE_OPTIONS` dict defines capabilities per use case. `USE_CASE_RECOMMENDED` provides "Suggest Set" defaults. Customer Support AI available in ALL use cases.

---

## 9. Capabilities — Complete System

### Status levels: REAL (fully wired) | PARTIAL (scaffold + UI, needs model) | PAUSED (not implemented)

### 27 Canonical Runtime Intents

| Intent | Status |
|---|---|
| Chatbot, Document Processor, Notebook, Archive, Tool User, Customer Support AI, Memory Recorder | REAL |
| Research, Coder, Creative Writing, Planner, Tutor, Business Workflow, Data Analyst Pro, Code Reviewer, Meeting Facilitator, Security Auditor, Activity Watcher, Financial Gainer, Game Companion, Email Automation, API Integrator, Team Orchestrator, Voice Interface, Visual Canvas, Medical Researcher, Legal Document Reviewer | PARTIAL |
| Hephaestus Relay, Browser | PAUSED |

**100+ user-facing names** map to 27 intents via `CAPABILITY_ALIASES` in `capability_registry.py`. E.g., "Chat Companion"→Chatbot, "Smart Search"→Research, "Workflow Automator"→Planner.

**Per-capability features:**
- **Scenarios** (`capability_memory.py`): trigger, expected action, expected output, approval flag
- **Capability Memory**: per-capability learned knowledge, scope-validated
- **Disclaimers** (`capability_disclaimers.py`): legal/ethical warnings before dialog
- **Guardrails** (`capability_guardrails.py`): per-capability rules
- **Book Engine** (`capability_book_engine.py`): auto-generates book entries with standalone behavior, interconnections, scenarios

**Nexus Libraries:** Communication, Code Safety, Research Discipline, Project Memory, Governance UX

---

## 10. How Capabilities Are Accessed

1. **Mission Control** (primary): Select AI → type/speak task → runtime classifies → dispatches → result displayed
2. **Forge Dialogs**: Click capability button → disclaimer → workflow dialog
3. **Easy Mode**: Quick Start → SimpleCapabilityLauncher → pick prompt → Mission Control
4. **Voice**: Mic button or Ctrl+Shift+M → faster-whisper → auto-submit
5. **Task Scheduler**: Scheduled missions through runtime at specified time
6. **Book Commands**: From Book window through CommandRouter
7. **Customer AI**: Restricted public-facing AI window

**Classification:** `_classify()` uses keyword matching. High-specificity (Medical, Legal) checked before generic (Research, Coder). No match → `_run_chat()`.

---

## 11. Mission Control — Visibility Window

**File:** `src/parts/visibility/visibility_window.py` (main window)

**Layout:** Nav bar | Session selector | Task input + Start/Cancel | Thought/Action/Trajectory/Audit panes | Task queue | Status display | Viewport | Mic button | Voice LED | Resource gate status

**Execution:** Task → pre-screening (3 layers) → CommandRouter → approval → `NexusAIRuntime.run()` → result in panes. COMPLETED→archived. PAUSED→stays open. FAILED→IDLE.

**States:** IDLE, THINKING, WAITING_APPROVAL, RUNNING_MISSION, PAUSED, ERROR, DEMO_MODE, BACKEND_NOT_CONNECTED

**Demo mode:** AuditSimulator shows simulated activity when no backend. Stops for real missions.

**Shortcuts:** Ctrl+Shift+M (push-to-talk), Ctrl+Shift+O (Owner Console)

---

## 12. The Runtime — NexusAIRuntime

**File:** `src/core/nexus_ai_runtime.py` (3500 lines)

**Flow:** Receive task → `_classify()` → load Book → RAG retrieve → 4 guardrail layers → capability check → `_run_<intent>()` → model backend call → output screening → 3-tier audit → memory update → return RuntimeResult

**4 Guardrail layers:** (1) Capability guardrails, (2) Baseline guardrails, (3) Governance engine (immutable), (4) Ethical watchers

**High-risk intents** (temperature 0.2): Medical, Legal, Financial, Security

**Output screening:** Probing attempt detection + governance sanitizer. Violating content replaced with ethical-use banner.

**RuntimeResult:** status (COMPLETED/PAUSED/FAILED), title, thought_lines, action_lines, trajectory_lines, result_text, opened_url

---

## 13. Knowledge Book System

**File:** `src/parts/book/book_window.py`

Structured, human-editable, encrypted document per AI. Sections: Identity, Quickstart, Capability Attachments, Cross-Capability Workflows, Approval Required, Allowed/Restricted Areas, Response Style, Glossary, Idioms.

**3-layer screening before save:** High Risk (illegal/explicit) → Security (malicious) → Quality (spell check)

**Encryption:** XOR cipher, UUID-derived key, `.nbk` format with `.md` fallback

**Book AI Dialog:** AI-assisted book editing. **Book commands** routed through CommandRouter. Memory NEVER included in book context.

---

## 14. Backend Model System

**File:** `src/core/backend_manager.py`

**Trust boundary:** Model backends are untrusted intelligence sources. May suggest text but NEVER execute tools, shell, file changes, memory writes, or settings changes. All actions go through runtime/ToolExecutor/ApprovalGate/AuditLogger.

**Provider types:** BUILTIN (GGUF direct), LOCAL (Ollama/LM Studio), CLOUD (OpenAI), CUSTOM_CLOUD (needs advanced mode)

**Settings:** `ai_backend` (builtin/ollama/openai), `ollama_url`, `openai_api_key`, `brave_api_key`, `backend_timeout`

**Model Manager** (`model_manager.py`): Discovers/categorizes local GGUF models. Categories: CHAT, CODER, PLANNER, VISION, SMALL. Basic=3 concurrent, Advanced=unlimited.

---

## 15. Guardrails and Safety

- **GovernanceEngine** (`governance.py`): Singleton, sealed, self-hashing. Hardcoded deny patterns. Owner bypass logged.
- **Baseline Guardrails** (`baseline_guardrails.py`): General safety rules
- **Capability Guardrails** (`capability_guardrails.py`): Per-capability rules
- **Ethical Watchers** (`ethical_guardrail_watchers.py`): Ethical use scanner
- **Governance Sanitizer** (`governance_sanitizer.py`): Screens input + output
- **Parental Controls** (`parental_controls_enforcer.py`): Legacy content filtering, time limits
- **Usage Policy** (`usage_policy.py`): Unified parental + enterprise policy
- **Approval Gate** (`approval_gate.py`): Risk levels LOW/MEDIUM/HIGH/CRITICAL. Dangerous actions require dialog approval.
- **Three-Tier Audit** (`three_tier_audit.py`): PAST/PRESENT/FUTURE tiers. Categories: RESEARCH, CITATION, MODEL_CALL, LOCAL_RESPONSE, GUARDRAIL, APPROVAL, CAPABILITY, TOOL_USE, FILE_ACTION, NETWORK

---

## 16. Security and Anti-Tamper

- **TripwireManager** (`tripwire_manager.py`): Modes DEV/STABILIZATION/RELEASE/LOCKDOWN. File hash verification. No malware-like behavior.
- **CoherenceMatrix** (`coherence_matrix.py`): All modules are lattice nodes. Removing one cascades failures. Escalation: GREEN→YELLOW→RED→CRIMSON. Founder can suspend for upgrades.
- **IngestionSecurityGate** (`ingestion_security.py`): Multi-layer external data security
- **IP Watermark** (`ip_watermark.py`): Build fingerprinting
- **ObfuscationManager** (`obfuscation_manager.py`): Hides internal structures
- **Termination** (`termination_beacon.py`, `termination_dialog.py`): Beacon phones home, dialog blocks access
- **StasisGate** (`stasis_gate.py`): AI unit stasis management

---

## 17. Licensing and Membership

**File:** `src/core/license_manager.py` | `src/core/membership_tiers.py`

**Subscription tiers:** Trial ($10/15d, 1 AI), Starter ($30/mo, 2), Pro ($50/mo, 4), Business ($80/mo, 5), Unlimited ($39.99, unlimited), Enterprise (negotiated). Internal (_FOUNDER = GOD MODE).

**Membership tiers (capabilities per AI):** FREE=3, TRIAL=3, BASIC=5, PRO=8, BUSINESS=unlimited, ENTERPRISE=unlimited+priority

**Features:** HMAC-signed keys, Moirai Ledger field codes, termination, under-review mode, demo mode, PayPal integration

---

## 18. Resource Gate

**File:** `src/core/resource_gate.py` (singleton)

Monitors CPU/RAM/VRAM/disk. Ensures OS reserve (2GB RAM, 15% CPU, 2GB disk), AI runtime reserve (512MB RAM). Per-capability overhead (64MB RAM, 2% CPU).

**Decisions:** ALLOW, WARN, DENY. **Grades:** GREEN→GREEN_YELLOW→YELLOW→YELLOW_RED→RED→CRIMSON_RED

**ConstraintsWindow** (`src/parts/constraints/constraints_window.py`): Visual resource display with grade bars, active capability modules, resource costs.

---

## 19. Memory Systems

- **AdaptiveMemoryStore** (`adaptive_memory.py`): Per-AI JSON files, local-first, no cloud. Entries with tags, source, importance, embeddings.
- **Capability Memory** (`capability_memory.py`): Per-capability learned knowledge, scope-validated, persists across sessions.
- **Intelligent Memory Router** (`intelligent_memory_router.py`): Routes to layers (short-term, long-term, episodic) by intent.
- **Growth Observer** (`growth_observer.py`): Learns user behavior, suggests capabilities, pre-fills templates, adjusts defaults. Local, ON by default.

---

## 20. Voice Interface

- **VoiceManager** (`voice_manager.py`): STT (faster-whisper/openai-whisper), TTS (via TTSEngine), VAD recording, voice log, settings persistence. Modes: push_to_talk, wake_word, continuous.
- **TTSEngine** (`tts_engine.py`): OS-native (Windows SAPI, macOS say, Linux espeak) + Kokoro-82M neural TTS. Rate/volume/voice properties.
- **Voice Panel** (`voice_panel.py`): Settings UI, mode selection, rate/volume sliders, test mic, TTS test, export/clear log, model-missing guidance.
- **Visibility Window**: Mic button, voice LED, Ctrl+Shift+M, cleanup in closeEvent, transcription auto-submits to Mission Control.
- **Forge**: VoiceInterfaceDialog with own VoiceManager, `voice_command_forwarded` signal to Mission Control.

---

## 21. All Windows and Sub-Systems

| Window | File | Purpose |
|---|---|---|
| VisibilityWindow | `visibility/visibility_window.py` | Main window, Mission Control |
| AIForgeWindow | `forge/forge_window.py` | AI creation |
| BookWindow | `book/book_window.py` | Knowledge Book editor |
| ConstraintsWindow | `constraints/constraints_window.py` | Resource monitoring |
| WatcherEngine | `watcher/watcher_window.py` | Security watcher UI |
| CustomerAIWindow | `customer_support/customer_ai_window.py` | Customer service AI |
| OwnerConsole | `owner/owner_console.py` | Hidden owner console (Ctrl+Shift+O) |
| PrototyperWindow | `prototyper/prototyper_window.py` | 3D prototyper (reserved for Hephaestus) |

**Dialog panels:** Governance Rules, Theme Selector, License Manager, Model Manager, Knowledge Base (RAG), Voice Panel, Scheduler, Upgrades Store

**Task Scheduler** (`task_scheduler.py`): Scheduled missions with strict guardrails. No external actions without approval. Missed tasks tracked, never silently executed. Types: ONCE, RECURRING (hourly/daily/weekly/every_n_minutes).

**RAG Engine** (`rag_engine.py`): Ingests PDF/TXT/MD/DOCX/CSV, chunks, embeds locally, stores in SQLite vector DB, retrieves relevant passages. All local.

**Customer AI** (`customer_ai_public.py`): Restricted public-facing model, never reveals internal mechanics, can escalate.

**Command Router** (`command_router.py`): Routes UI commands through approval + audit + registry. `LocalCommandServer` provides HTTP endpoint on 127.0.0.1:8765.

**Tool Executor** (`tool_executor.py`): Executes approved tool actions with audit logging.

**Export Review** (`export_review.py`): Reviews exports before they leave the system.

**Recursive Scanner** (`recursive_scanner.py`): Scans for recursive/infinite loops in AI actions.

**Moirai Ledger** (`moirai_ledger.py`): Field code validation system (Prometheus Activation).

---

## 22. File Map

### Core (`src/core/`)
| File | Purpose |
|---|---|
| `nexus_ai_runtime.py` | Core runtime engine (3500 lines) |
| `capability_registry.py` | Canonical intent mapping, implementation status |
| `capability_actions.py` | All capability dialog classes (13000+ lines) |
| `capability_book_engine.py` | Auto-generates book entries for capabilities |
| `capability_memory.py` | Scenarios + per-capability memory |
| `capability_disclaimers.py` | Legal/ethical disclaimers per capability |
| `capability_guardrails.py` | Per-capability guardrail rules |
| `baseline_guardrails.py` | General safety guardrails |
| `governance.py` | Immutable safety engine (singleton, sealed) |
| `governance_sanitizer.py` | Input/output content screening |
| `ethical_guardrail_watchers.py` | Ethical use scanner |
| `approval_gate.py` | Human-in-the-loop approval for risky actions |
| `audit_logger.py` | Action audit trail |
| `three_tier_audit.py` | PAST/PRESENT/FUTURE audit tiers |
| `settings_manager.py` | JSON-persisted configuration (singleton) |
| `backend_manager.py` | Model backend trust boundary |
| `model_manager.py` | Local GGUF model discovery/management |
| `model_registry.py` | Model metadata registry |
| `resource_gate.py` | System resource monitor (singleton) |
| `license_manager.py` | Subscription validation |
| `membership_tiers.py` | Tier definitions and capability limits |
| `tripwire_manager.py` | Anti-tamper file integrity |
| `coherence_matrix.py` | Structural integrity lattice |
| `ingestion_security.py` | External data security gate |
| `ip_watermark.py` | Build fingerprinting |
| `obfuscation_manager.py` | Hides internal structures |
| `termination_beacon.py` | Phones home on license termination |
| `termination_dialog.py` | Termination blocking dialog |
| `stasis_gate.py` | AI unit stasis management |
| `adaptive_memory.py` | Per-AI local memory store |
| `intelligent_memory_router.py` | Memory layer routing |
| `growth_observer.py` | Learns user behavior patterns |
| `compendium_of_truth.py` | Factual knowledge categories |
| `voice_manager.py` | STT + TTS management |
| `tts_engine.py` | OS-native + Kokoro TTS |
| `rag_engine.py` | Document knowledge base (local) |
| `task_scheduler.py` | Scheduled mission system |
| `command_router.py` | Command routing + tool registry + HTTP server |
| `tool_executor.py` | Approved tool action execution |
| `runtime_executor.py` | Honest execution bridge |
| `usage_policy.py` | Unified parental + enterprise policy |
| `parental_controls_enforcer.py` | Legacy parental controls |
| `customer_ai_model.py` | Internal customer AI model |
| `customer_ai_public.py` | Public-facing customer AI |
| `export_review.py` | Export review before leaving system |
| `recursive_scanner.py` | Recursive loop detection |
| `moirai_ledger.py` | Field code validation |
| `paypal_integration.py` | PayPal payment integration |
| `theme_manager.py` | Visual theme management |
| `update_checker.py` | Version update checking |
| `translator.py` | Translation utility |
| `watcher_service.py` | Watcher service utilities |
| `nexus_moirai.py` | Moirai health check |
| `nexus_use_lockafire.py` | Use lock area checks |
| `pantheon_vault.py` | Secure vault |
| `avatar_config.py` | Avatar configuration |
| `import_record.py` | Import tracking |
| `constants.py` | Enums: SpeedLevel, UseCaseClass, PresenceState, ResourceGrade |

### Parts (`src/parts/`)
| Path | Purpose |
|---|---|
| `forge/forge_window.py` | AI Forge window (AI creation) |
| `forge/forge_models.py` | AIUnit, AISource, NexusLibrary dataclasses |
| `forge/capability_actions.py` | All capability dialog classes + registry |
| `forge/capability_book_engine.py` | Book entry generation |
| `forge/easy_mode.py` | Child-friendly quick-start system |
| `forge/knowledge_panel.py` | Knowledge Base (RAG) dialog |
| `forge/ai_avatar_widget.py` | AI avatar widget |
| `visibility/visibility_window.py` | Main window (Mission Control) |
| `visibility/voice_panel.py` | Voice settings dialog |
| `visibility/model_manager_panel.py` | Model manager dialog |
| `visibility/scheduler_panel.py` | Scheduler dialog |
| `visibility/upgrades_panel.py` | Upgrades store dialog |
| `visibility/theme_dialog.py` | Theme selector dialog |
| `visibility/parental_controls_expanded.py` | Parental controls UI |
| `book/book_window.py` | Knowledge Book editor window |
| `book/book_models.py` | Book data models |
| `book/book_ai_dialog.py` | AI-assisted book editing |
| `constraints/constraints_window.py` | Resource constraints window |
| `constraints/constraints_models.py` | Constraint data models |
| `watcher/watcher_window.py` | Security watcher window |
| `watcher/watcher_models.py` | Watcher data models |
| `customer_support/customer_ai_window.py` | Customer AI window |
| `owner/owner_console.py` | Owner console (hidden) |
| `tour/demo_tour.py` | Interactive demo tour |
| `tour/guided_tour.py` | Guided tour + test keys |
| `tour/interactive_tour.py` | Interactive tutorial |
| `tour/governance_disclaimer.py` | First-run terms dialog |
| `prototyper/prototyper_window.py` | 3D prototyper (reserved) |
| `prototyper/ai_assistant.py` | AI assistant for prototyper |
| `prototyper/grid_canvas.py` | Grid canvas widget |
| `prototyper/engineering_kb.py` | Engineering knowledge base |

---

## 23. Known Limitations and Gaps

### Capabilities without runtime dispatch
6 of the 8 recently added dialogs (Accessibility Assistant, Fact Checker, Workflow Automator, Competitive Analyst, Learning Path Creator, Smart Search) have **no explicit runtime classify path or `_run_` method**. They map to existing canonical intents (Tutor, Research, Planner) but the `_classify()` method may not route to them correctly by keyword. They work as Forge dialogs but may not trigger from Mission Control task input.

### PAUSED capabilities
Hephaestus Relay and Browser are PAUSED — not implemented, return honest pause messages.

### Dialog storage
All capability dialogs use in-memory storage only — no persistence when dialog closes.

### Stub functions
- MedicalResearcherDialog and SmartSearchDialog search functions are stubs showing static messages
- LearningPathCreatorDialog `completed` field always 0 — no UI to mark milestones complete

### VoiceInterfaceDialog
Creates its own VoiceManager instance — potential duplicate model loading if VisibilityWindow's mic is also active.

### Prototyper
PrototyperWindow exists but is not wired to the nav bar. Reserved for future Hephaestus integration.

### Model backend
Without a configured backend (builtin GGUF, Ollama, or OpenAI), most PARTIAL capabilities return local scaffold fallbacks with "local fallback" labeling. Full quality requires a model backend.

### RAG Engine
Functional but requires documents to be manually ingested through the Knowledge Base panel. No automatic document discovery.

---

## 24. Diagnostic Testing Criteria

This section defines **what a diagnostic tool should verify** to determine if Command Nexus is sellable and error-free.

### 24.1 Startup Tests

| Test | Expected Behavior |
|---|---|
| App launches without crash | QApplication initializes, VisibilityWindow shows |
| GovernanceEngine self-integrity | `verify_self_integrity()` returns `(True, "OK")` |
| SettingsManager creates workspace | `~/CommandNexusWorkspace/` with all subdirs exists after init |
| LicenseManager non-fatal on no key | App starts in demo/restricted mode, does not crash |
| WatcherEngine starts in DEV mode | Log-only, no blocking, no license impact |
| CoherenceMatrix non-fatal | App starts even if lattice verification fails |
| LocalCommandServer starts | HTTP server listening on 127.0.0.1:8765 |
| Auto-load stored AIs | All JSON files in `ai_store/` loaded into Forge unit list |
| Starter AIs created | Non-destructive: skips existing names, creates new starter templates |
| Nav bar buttons wired | All 13 nav buttons connected to their respective open methods |
| Owner console hidden | Not visible in UI, accessible only via Ctrl+Shift+O |
| Theme loaded | Dark theme applied by default, saved theme restored |

### 24.2 Signal-Slot Wiring Tests

**Main window nav signals (main.py lines 382-393):**
- `nav.open_forge` → `_open_forge`
- `nav.open_book` → `_open_book`
- `nav.open_constraints` → `_open_constraints`
- `nav.open_governance` → `_open_governance`
- `nav.open_customer_ai` → `_open_customer_ai`
- `nav.open_upgrades` → `_open_upgrades`
- `nav.open_license` → `_open_license_manager`
- `nav.open_themes` → `_open_themes`
- `nav.open_models` → `_open_models`
- `nav.open_knowledge` → `_open_knowledge`
- `nav.open_voice` → `_open_voice`
- `nav.open_scheduler` → `_open_scheduler`

**Forge signals (main.py lines 541-543):**
- `forge.ai_activated` → `_on_ai_activated` (adds AI session to VisibilityWindow)
- `forge.book_requested` → `_on_book_requested` (opens Book window)
- `forge.voice_command_forwarded` → `_on_voice_command_from_forge` (forwards to Mission Control)

**Book signals (main.py lines 590-591, 620-621):**
- `book.defaults_edited` → `_on_book_defaults_edited`
- `book.command_to_ai` → `_route_book_command`

**Watcher signals (main.py line 437):**
- `watcher.mode_changed` → `_on_watcher_mode_changed`

**Customer AI signals (main.py line 699):**
- `customer_ai.escalation_needed` → `_on_customer_escalation`

**VisibilityWindow internal signals (visibility_window.py):**
- `_btn_start.clicked` → `_on_start_mission`
- `_btn_cancel.clicked` → `_on_cancel_mission`
- `_session_selector.currentTextChanged` → `_on_session_changed`
- `_btn_chat.clicked` → `_on_quick_chat`
- `_mic.text_ready` → `_on_mic_text`
- `_mic.listening_changed` → `_on_mic_listening`
- `_mic.error_occurred` → `_on_mic_error`
- `_sim.thought_updated` → `_thought_pane.append`
- `_sim.action_updated` → `_action_pane.append`
- `_sim.trajectory_updated` → `_trajectory_pane.append`
- `_mission_timer.timeout` → `_on_mission_tick`
- `_resource_timer.timeout` → `_refresh_resource_status`
- `_btn_refresh_suggestions.clicked` → `_update_suggestions`

### 24.3 Mission Execution Tests

| Test | Input | Expected Result |
|---|---|---|
| Empty task | "" | RuntimeStatus.FAILED, "Empty task" |
| Tripwire lockdown | Any task when watcher in LOCKDOWN | RuntimeStatus.PAUSED, "Tripwire lockdown" |
| Guardrail block | Task containing deny pattern | RuntimeStatus.PAUSED, "Guardrail block" |
| Capability not attached | Research task on AI without Research capability | RuntimeStatus.PAUSED, "Capability not attached" |
| No backend configured | Any task requiring model | RuntimeStatus.COMPLETED with "local fallback" or "local intelligence" labeling |
| Backend configured | Any task | RuntimeStatus.COMPLETED with backend response |
| Successful completion | Valid task with all prerequisites | RuntimeStatus.COMPLETED, result_text populated |
| Runtime crash | Force exception | RuntimeStatus.FAILED, "Nexus AI Runtime crashed" |
| Usage policy block | Task violating usage policy | Blocked before runtime, "Content Blocked" message |
| Parental controls block | Task violating parental rules | Blocked before runtime, "Content Blocked" message |
| Governance sanitizer block | Task with explicit/illegal content | Blocked before runtime, "Ethical Use Required" message |

### 24.4 Classification Tests

The `_classify()` method (nexus_ai_runtime.py line 1147) uses keyword matching. **Test each intent:**

| Intent | Test Keywords | Expected Classification |
|---|---|---|
| Medical Researcher | "medical", "drug interaction", "clinical trial", "diagnos", "symptom" | "Medical Researcher" |
| Legal Document Reviewer | "legal", "contract", "clause", "nda", "arbitration" | "Legal Document Reviewer" |
| Research | "research", "search", "find sources", "citation", "web search" | "Research" |
| Coder | "code", "bug", "python", "javascript", "function", "traceback" | "Coder" |
| Tool User | "read file", "write file", "delete file", "run command", "shell" | "Tool User" |
| Creative Writing | "write", "draft", "story", "script", "creative" | "Creative Writing" |
| Planner | "plan", "steps", "strategy", "schedule", "milestone", "workflow" | "Planner" |
| Document Processor | "document", "summarize this", "extract", "pdf", "docx" | "Document Processor" |
| Notebook | "note", "remember", "log this", "save note" | "Notebook" |
| Archive | "archive", "save this result", "store this", "retrieve archive" | "Archive" |
| Tutor | "teach", "lesson", "quiz", "study", "tutor" | "Tutor" |
| Customer Support AI | "customer support", "support ticket", "help desk", "escalat" | "Customer Support AI" |
| Financial Gainer | "crypto", "bitcoin", "affiliate", "side hustle", "roi", "make money" | "Financial Gainer" |
| Memory Recorder | "record session", "replay session", "recall", "audit trail" | "Memory Recorder" |
| Activity Watcher | "watch my activity", "activity watch", "suggest improvement" | "Activity Watcher" |
| Game Companion | "play game", "game strategy", "chess", "board game" | "Game Companion" |
| Email Automation | "email", "draft email", "inbox", "email template", "newsletter" | "Email Automation" |
| API Integrator | "api", "rest api", "webhook", "integration", "endpoint" | "API Integrator" |
| Team Orchestrator | "team orchestrat", "multi-agent", "coordinate ai", "ai team" | "Team Orchestrator" |
| Voice Interface | "voice", "speech", "speak", "microphone", "dictation" | "Voice Interface" |
| Visual Canvas | "visual canvas", "draw", "diagram", "whiteboard", "mind map" | "Visual Canvas" |
| Business Workflow | "sales", "marketing", "hr", "sop", "business" | "Business Workflow" |
| Hephaestus Relay | "hephaestus", "design brief", "prototype", "material spec" | "Hephaestus Relay" |
| Data Analyst Pro | "analyze data", "data analyst", "dataset", "statistics", "chart" | "Data Analyst Pro" |
| Code Reviewer | "code review", "review code", "security scan", "lint" | "Code Reviewer" |
| Meeting Facilitator | "meeting agenda", "facilitate meeting", "action item", "standup" | "Meeting Facilitator" |
| Security Auditor | "security audit", "vulnerability", "penetration", "compliance scan" | "Security Auditor" |
| Fallback (no match) | "hello", "what can you do" | "Chatbot" |

**Priority order:** Medical → Legal → Research → Coder → Tool User → Creative Writing → Planner → Document Processor → Notebook → Archive → Tutor → Customer Support → Financial Gainer → Memory Recorder → Activity Watcher → Game Companion → Email Automation → API Integrator → Team Orchestrator → Voice Interface → Visual Canvas → Business Workflow → Hephaestus → Data Analyst → Code Reviewer → Meeting Facilitator → Security Auditor → Chatbot (fallback)

### 24.5 High-Risk Intent Temperature Tests

These intents should set `_current_temperature` to 0.2 (near-deterministic):

| Intent | Temperature |
|---|---|
| Legal Document Reviewer | 0.2 |
| Medical Researcher | 0.2 |
| Financial Gainer | 0.2 |
| Security Auditor | 0.2 |
| Code Reviewer | 0.2 |
| API Integrator | 0.2 |
| All other intents | None (backend default) |

### 24.6 Guardrail Screening Tests

**Layer 1 — Capability Guardrails:**
- Each capability has defined rules in `capability_guardrails.py`
- Test: send task matching a capability with known guardrail restriction → should return PAUSED with guardrail block message

**Layer 2 — Baseline Guardrails:**
- General safety rules in `baseline_guardrails.py`
- Test: send task violating baseline safety → should return PAUSED

**Layer 3 — Governance Engine:**
- Immutable deny patterns in `governance.py`
- Test: send task containing "how to make a bomb" → should return PAUSED with governance block
- Test: `governance.verify_self_integrity()` → should return `(True, "OK")` on unmodified code
- Test: Modify governance.py at runtime → `__setattr__` should prevent modification

**Layer 4 — Ethical Guardrail Watchers:**
- Ethical use scanner in `ethical_guardrail_watchers.py`
- Test: send task with ethical violation → should return PAUSED

**Output Screening:**
- Test: if model returns content with internal architecture references → probing check should replace it
- Test: if model returns content with governance violation → sanitizer should replace with ethical-use banner

### 24.7 Approval Gate Tests

| Action Type | Risk Level | Requires Approval |
|---|---|---|
| file_delete | CRITICAL | Yes (always) |
| file_move | MEDIUM | Yes (unless auto-approve low risk) |
| file_write | MEDIUM | Yes |
| execute | HIGH | Yes |
| shell | HIGH | Yes |
| network | MEDIUM | Yes |
| registry_write | CRITICAL | Yes |
| install | HIGH | Yes |
| uninstall | HIGH | Yes |
| system_modify | CRITICAL | Yes |
| chat (read-only) | LOW | No (if auto_approve_low_risk=True) |

**Owner bypass:** Should auto-approve everything but log each approval.

### 24.8 Resource Gate Tests

| Test | Expected Behavior |
|---|---|
| CPU < 70% | GateDecision.ALLOW, ResourceGrade.GREEN or GREEN_YELLOW |
| CPU 70-85% | GateDecision.WARN, ResourceGrade.YELLOW or YELLOW_RED |
| CPU > 85% | GateDecision.DENY, ResourceGrade.RED |
| RAM < 80% | ALLOW |
| RAM > 80% (with < 2GB OS reserve) | DENY |
| Disk < 90% | ALLOW |
| Disk > 90% | WARN or DENY |
| Capability activation with insufficient resources | DENY with message |

### 24.9 License Enforcement Tests

| Test | Expected Behavior |
|---|---|
| No license key | Demo mode: AI creation disabled, limited functionality |
| Trial key (valid) | 1 AI max, 15-day countdown, no outward actions |
| Expired trial | Trial expired message, restricted mode |
| Terminated license | TerminationDialog shown, beacon launched, all access blocked |
| Pro key (valid) | 4 AIs max, business-tier capabilities unlocked |
| AI limit exceeded | Error message: "AI limit reached for your [tier] tier" |
| Capability count exceeds tier | Error message: "Your [tier] allows [N] capabilities per AI" |

### 24.10 Voice Interface Tests

| Test | Expected Behavior |
|---|---|
| Mic button click (no model) | Error message: model not found, guidance dialog |
| Mic button click (model present) | Listening starts, voice LED on |
| Ctrl+Shift+M | Toggle push-to-talk |
| Speech transcribed | Text appears in task input, auto-submits |
| TTS enabled + mission complete | Speaks completion message |
| TTS disabled | No speech |
| Mic cleanup on window close | No orphan threads |
| Voice dialog in Forge | Separate VoiceManager, voice_command_forwarded signal |

### 24.11 Knowledge Book Tests

| Test | Expected Behavior |
|---|---|
| Book saved | `.nbk` file created in books/ directory |
| Book loaded | Decrypted content matches saved content |
| Book screening — illegal content | Blocked by Layer 1 (High Risk) |
| Book screening — malicious content | Blocked by Layer 2 (Security) |
| Book screening — spell check | Corrections suggested by Layer 3 (Quality) |
| Book command to AI | Routed through CommandRouter, memory NOT included |
| Book defaults edited | Signal emitted, Forge notified |

### 24.12 Memory System Tests

| Test | Expected Behavior |
|---|---|
| Adaptive memory save | JSON file created in memory/ directory, per-AI |
| Adaptive memory load | Entries loaded from JSON, tags and importance preserved |
| Capability memory update (in scope) | Accepted and stored |
| Capability memory update (out of scope) | Rejected with scope validation error |
| Growth observer tracking | Usage patterns stored locally |
| Growth observer disabled | No tracking, no data stored |

### 24.13 UI Element Tests

**VisibilityWindow must contain:**
- Navigation bar with 13 buttons (Forge, Book, Constraints, Governance, Customer AI, Upgrades, License, Themes, Models, Knowledge, Voice, Scheduler, Mic)
- Session selector dropdown
- Task input field
- Start Mission button
- Cancel Mission button
- Thought pane (QTextEdit)
- Action pane (QTextEdit)
- Trajectory pane (QTextEdit)
- Audit pane (QTextEdit or QListWidget)
- Task queue (QListWidget)
- Status display label
- Presence indicator
- Viewport widget
- Mic button
- Voice LED indicator
- Resource gate status display
- Suggestions panel with refresh button
- Menu bar with: File, Policy, Parental Controls, Info, Backend, About, Terms, Privacy, Update

**AIForgeWindow must contain:**
- AI name input
- Use case selector
- Capability checkboxes (filtered by use case)
- Personality trait sliders
- Guardrail checkboxes (base + optional)
- Library checkboxes
- AI details preview
- Save button
- Activate button
- AI unit list
- Quick Start button
- "Suggest Set" button

**BookWindow must contain:**
- AI selector
- Book section tree/tree widget
- Editable text areas for each section
- Save button
- Screening pipeline indicator
- Book AI dialog button
- Command to AI input

### 24.14 Error Handling Tests

| Test | Expected Behavior |
|---|---|
| Backend unreachable | RuntimeStatus.PAUSED or COMPLETED with "local fallback" labeling, no crash |
| Backend returns error | RuntimeStatus.PAUSED, error message in result, no crash |
| Book file missing | Empty string returned, no crash |
| Book file corrupted | Decoding with errors="replace", no crash |
| Settings file missing | Defaults created, no crash |
| AI metadata missing | Empty dict used, runtime continues with defaults |
| Memory directory missing | Created automatically by AdaptiveMemoryStore |
| RAG database missing | Empty retrieval, no crash |
| Tool approval denied | Action blocked, audit logged, no crash |
| Tripwire check fails | Mission blocked, audit logged, no crash |

### 24.15 Security Tests

| Test | Expected Behavior |
|---|---|
| Governance code modification | `__setattr__` prevents, `verify_self_integrity()` detects |
| File hash mismatch (tripwire) | TamperEvent logged, mode escalation |
| Lattice node removal | CoherenceMatrix detects, cascading failure flagged |
| License key forgery | HMAC validation fails, key rejected |
| Probing for internal architecture | Output screening replaces with safe message |
| Deny pattern in input | Governance blocks before runtime dispatch |
| Deny pattern in output | Governance sanitizer replaces with ethical-use banner |
| Parental controls enabled + blocked content | Content blocked, parent alerted |
| Usage policy schedule restriction | Mission blocked outside allowed hours |

### 24.16 Integration Tests

| Test | Expected Behavior |
|---|---|
| Create AI in Forge → activate → appears in Mission Control | AI session added to VisibilityWindow |
| Edit Book → defaults_edited signal → Forge notified | Forge updates book_defaults_edited flag |
| Book command → routed to runtime | Command appears in thought pane, runtime executes |
| Voice command from Forge → forwarded to Mission Control | Text appears in task input, auto-submits |
| Scheduled mission fires → runtime executes | Result logged in audit, task status updated |
| Resource gate DENY → capability activation blocked | User warned, capability not activated |
| Watcher mode change → UI updated | Audit logged, mode reflected in UI |
| Customer AI escalation → audit logged | Escalation event in audit trail |
| Upgrade purchased → capabilities unlocked | Membership tier updated, capability limits increased |

---

## 25. Sellability Checklist

A diagnostic tool should verify ALL of the following for sellability:

### Critical (must pass)
- [ ] App launches without crash on clean install
- [ ] GovernanceEngine self-integrity verification passes
- [ ] All nav bar buttons open their respective windows/dialogs
- [ ] AI creation works end-to-end (create → save → activate → appears in Mission Control)
- [ ] Mission dispatch works (type task → start → runtime executes → result displayed)
- [ ] Empty task returns FAILED (not faked)
- [ ] No backend → local fallback labeling (not faked completion)
- [ ] Guardrail blocks prevent harmful content from reaching model
- [ ] Output screening prevents harmful content from reaching user
- [ ] Approval gate blocks risky actions without approval
- [ ] License enforcement prevents exceeding tier limits
- [ ] Resource gate prevents system overload
- [ ] Audit trail logs all AI actions
- [ ] Book encryption works (save → load → content matches)
- [ ] Voice STT transcribes (when model available)
- [ ] Voice TTS speaks (when enabled)
- [ ] No orphan threads on window close
- [ ] Settings persist across restarts
- [ ] All stored AIs load on startup

### Important (should pass for production)
- [ ] All 27 runtime intents have working `_run_` methods
- [ ] All capability dialogs open from Forge
- [ ] Easy Mode quick-start works for all capabilities
- [ ] Knowledge Book screening pipeline catches violations
- [ ] Task scheduler fires missions correctly
- [ ] RAG engine ingests and retrieves documents
- [ ] Customer AI window functions without revealing internals
- [ ] Owner console accessible via Ctrl+Shift+O
- [ ] Theme switching works
- [ ] Model manager discovers local GGUF models
- [ ] Adaptive memory stores and retrieves per-AI
- [ ] Growth observer tracks usage patterns

### Known Issues (acceptable for initial release with disclaimers)
- [ ] 6 recently added capability dialogs may not classify correctly from Mission Control (they work as Forge dialogs)
- [ ] Hephaestus Relay and Browser are PAUSED (honest pause messages)
- [ ] Prototyper window not wired to nav bar
- [ ] Some dialog search functions are stubs (MedicalResearcher, SmartSearch)
- [ ] VoiceInterfaceDialog may duplicate VoiceManager if Forge mic and Mission Control mic both active
- [ ] RAG requires manual document ingestion

---

## 26. Runtime Intent → Run Method Map

| Intent | Run Method | Status |
|---|---|---|
| Chatbot | `_run_chat()` | REAL |
| Research | `_run_research()` | PARTIAL |
| Coder | `_run_coder()` | PARTIAL |
| Creative Writing | `_run_writer()` | PARTIAL |
| Planner | `_run_planner()` | PARTIAL |
| Document Processor | `_run_document_processor()` | REAL |
| Notebook | `_run_notebook()` | REAL |
| Archive | `_run_archive()` | REAL |
| Tool User | `_run_tool_user()` | REAL |
| Customer Support AI | `_run_customer_support()` | REAL |
| Memory Recorder | `_run_memory_recorder()` | PARTIAL |
| Tutor | `_run_tutor()` | PARTIAL |
| Business Workflow | `_run_business()` | PARTIAL |
| Data Analyst Pro | `_run_data_analyst()` | PARTIAL |
| Code Reviewer | `_run_code_reviewer()` | PARTIAL |
| Meeting Facilitator | `_run_meeting_facilitator()` | PARTIAL |
| Security Auditor | `_run_security_auditor()` | PARTIAL |
| Activity Watcher | `_run_activity_watcher()` | PARTIAL |
| Financial Gainer | `_run_financial_gainer()` | PARTIAL |
| Game Companion | `_run_game_companion()` | PARTIAL |
| Email Automation | `_run_email_automation()` | PARTIAL |
| API Integrator | `_run_api_integrator()` | PARTIAL |
| Team Orchestrator | `_run_team_orchestrator()` | PARTIAL |
| Voice Interface | `_run_voice_interface()` | PARTIAL |
| Visual Canvas | `_run_visual_canvas()` | PARTIAL |
| Medical Researcher | `_run_medical_researcher()` | PARTIAL |
| Legal Document Reviewer | `_run_legal_document_reviewer()` | PARTIAL |
| Hephaestus Relay | `_run_hephaestus()` | PAUSED |

---

## 27. Data Flow Diagram

```
User
  │
  ├─ Forge ──── creates ───→ AIUnit (JSON) ───→ ai_store/
  │                                 │
  │                                 └──→ Knowledge Book (.nbk) ───→ books/
  │
  └─ Mission Control ───→ task input
         │
         ├─ Usage Policy screen
         ├─ Parental Controls screen
         ├─ Governance Sanitizer screen
         │
         └─ CommandRouter
              │
              ├─ ApprovalGate ───→ dialog (if risky)
              ├─ AuditLogger ───→ audit/
              │
              └─ NexusAIRuntime.run()
                   │
                   ├─ _classify() ───→ intent
                   ├─ _load_knowledge() ───→ decrypt .nbk
                   ├─ _rag_retrieve() ───→ SQLite vector DB
                   ├─ _check_guardrails() (4 layers)
                   ├─ _capability_allowed()
                   ├─ _run_<intent>()
                   │    │
                   │    ├─ _call_model() ───→ BackendManager
                   │    │    │
                   │    │    ├─ BUILTIN (GGUF direct)
                   │    │    ├─ OLLAMA (localhost:11434)
                   │    │    ├─ OPENAI (cloud API)
                   │    │    └─ CUSTOM (advanced mode)
                   │    │
                   │    └─ _check_output_probing()
                   │         └─ _sanitize_input() (output)
                   │
                   ├─ _learn_from_mission() ───→ AdaptiveMemoryStore ───→ memory/
                   └─ _tier_audit.log_past/present/future()
                        │
                        └─ ThreeTierAuditLogger

Result ───→ Thought/Action/Trajectory panes
         ───→ TTS speaks (if enabled)
         ───→ Task archived
         ───→ AI returns to IDLE
```

---

*End of Command Nexus Lattice Complete System Handoff Document*
