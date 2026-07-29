# Command Nexus — v0.1.0

**Proprietary & Confidential** — See `NOTICE-PROPRIETARY.txt`

## What Is This?

Command Nexus is a governed AI integration console. It is a control center for organizing, controlling, monitoring, and safely operating AI agents, scripts, tools, and workflows from one structured command center. This is not a chatbot UI — it is a mission-control dashboard for AI systems.

## Quick Start

### 1. Install Dependencies (Windows)

Open Command Prompt or PowerShell in this folder and run:

```bash
pip install -r requirements.txt
```

Dependencies: `PySide6>=6.6.0`, `mss>=9.0.0`, `psutil>=5.9.0`

### 2. Launch

Double-click `launch.bat`, or run:

```bash
python -m src.main
```

---

## Architecture (All 5 Parts Implemented)

1. **Visibility Window** — Command center with live viewport, audit panes, mission control (START/CANCEL), task queue, AI status display
2. **AI Forge** — Character-sheet AI builder, JSON save/load, "Deploy to Command Center", "Open Book for AI"
3. **The Book** — Per-AI knowledge compendium (not global), tree editor, screening, Python export
4. **Upgrades** — 24 capability modules across all use-case categories, 3 tiers each (Low / Medium / High resource), one main system resource bar
5. **The Watcher** — Background defensive AI, always active, no UI, file integrity monitoring

## What's Working (MVP)

### Part 1 — Visibility Window (Command Center)
- **Live Desktop Viewport** — real-time screen capture
- **Mission Control** — AI selector with status badge (Idle / Running / Paused / Failed / Completed)
- **START / CANCEL** — Dispatch an AI on a mission with task description; cancel returns AI to idle
- **Task Queue** — Visual list of pending, running, and completed tasks
- **Control Bar** — STOP, PAUSE/RESUME, Redirect, Demonstrate, Speed Governor
- **Three Audit Panes** — Current Thought, Current Action, Planned Trajectory
- **Approval Gate** — Modal human-in-the-loop for risky actions (explains what, why, and targets)
- **Export** — Copy, Print, PDF, `.txt` per audit pane

### Part 2 — AI Forge
- **Character Sheet Builder** — Name, use-case class, capabilities, personality sliders
- **Use-Case Classes** — Individual, Educational, Task-Ready, Business, Enterprise, All-Rounder, Military/Government (locked)
- **Deploy to Command Center** — Sends AI to Visibility Window for mission assignment
- **Open Book for AI** — Opens the per-AI Book compendium for the selected AI
- **Save AI to Disk / Load AI from Disk** — JSON export/import for persistence
- **Drop-In AI** — File import with security scan simulation
- **Governance Screening** — Notes screened before saving

### Part 3 — The Book (Per-AI Compendium)
- **Per-AI Books** — Each AI has its own Book, not a global all-arounder
- **Structured Tree Editor** — Parts, Chapters, Sections, Relations
- **Reference Tabs** — Glossary, Idioms, Abbreviations
- **Save-Gate Screening** — Spelling, safety, and ethical checks
- **Python Export** — Translates Book to a `.py` module for AI consumption

### Part 4 — Upgrades (System Constraint Layer)
- **24 Capability Modules** — Communication, Development, Creative, Research, Organization, Education, Document, Business, Enterprise, Audio, Vision, Infrastructure
- **3 Tiers Per Module** — Lite (Low Resource), Standard (Medium Resource), Pro (High Resource)
- **One Main Resource Bar** — System-wide cumulative load indicator (Green → Crimson Red)
- **Live System Monitor** — RAM, CPU, Disk via `psutil`
- **Red Zone Warning** — Confirmation dialog before heavy activation
- **Crimson Red Hard Block** — Auto-deactivates modules if total load is dangerous

### Part 5 — The Watcher (Background Defensive AI)
- **Always Active, No UI** — Invisible background engine; no pause button
- **File Integrity Monitoring** — SHA-256 baselines; scans every 5 seconds
- **Alert Logging** — Critical alerts on file modification

---

## Deliverables

### 1. Current Project Contains
A PySide6 desktop application with 5 integrated parts: Visibility Window (command center), AI Forge (builder/registry), The Book (per-AI knowledge), Upgrades (capability modules), and The Watcher (background defense).

### 2. What Was Broken or Incomplete
- Missing START button to dispatch AIs on missions
- No task queue or status tracking
- Book was global instead of per-AI
- Only 6 upgrade modules (needed 20+)
- Per-module grade bars instead of one main system bar
- No low/medium/high resource labels on tiers
- No approval gate for risky actions
- No settings/config system
- No save/load for AI units

### 3. What Files Were Changed
- `src/main.py` — Settings init, book wiring
- `src/core/settings_manager.py` — **NEW** JSON config with paths
- `src/core/approval_gate.py` — **NEW** human-in-the-loop dialog
- `src/core/task_models.py` — **NEW** AI status and task models
- `src/parts/visibility/visibility_window.py` — Mission Control, START/CANCEL, task queue, status
- `src/parts/forge/forge_window.py` — Deploy, Open Book, Save/Load JSON
- `src/parts/book/book_window.py` — Per-AI book registry
- `src/parts/constraints/constraints_window.py` — 24 modules, Low/Med/High tiers, one main bar
- `README.md` — Updated documentation

### 4. How to Install Dependencies
```bash
pip install -r requirements.txt
```
Requires: PySide6, mss, psutil

### 5. How to Run Command Nexus
Double-click `launch.bat` or run `python -m src.main` from the project root.

### 6. How to Register a Tool / Agent
1. Open **AI Forge**
2. Fill the character sheet (name, use-case, capabilities, personality)
3. Click **"Save AI to Forge"**
4. Select the AI in the library and click **"Deploy to Command Center"**
5. Or use **"Load AI from Disk"** to import a previously saved JSON

### 7. How Approval Gates Work
When a risky action is initiated (mission start, module activation in red zone, etc.), a modal dialog appears explaining:
- **What** the action is doing
- **Why** it is doing it
- **What files/systems** may be affected
- **Can it be undone?**
The user must click **Approve** or **Deny**.

### 8. Where Logs Are Stored
Default: `%USERPROFILE%\CommandNexusWorkspace\logs\`
Configurable via `settings_manager.py` — edit `config.json` in `%USERPROFILE%\CommandNexus\`

### 9. What Is Working Now
- Launchable desktop app
- AI creation, deployment, and mission dispatch
- Per-AI Book compendium
- 24 upgrade modules with resource-aware activation
- Background file integrity monitoring
- Human approval gates
- Settings persistence
- AI JSON save/load

### 10. What Remains Placeholder
- Real AI backend integration (currently simulated audit streams)
- GPU VRAM detection (currently 0 placeholder)
- Actual dropped-in AI code execution (security scan is simulated)
- Network/API call monitoring in Watcher
- Multi-AI concurrent viewport switching

### 11. Next Best Development Step
Integrate a real LLM backend (local or API) so the Forge-built AIs can execute actual tasks, with the Visibility Window showing real thought/action streams instead of simulated demo data.

---

## File Structure

```
Command_Nexus/
├── launch.bat                     # Windows launcher
├── requirements.txt               # Python dependencies
├── NOTICE-PROPRIETARY.txt         # Legal notice
├── README.md                      # This file
└── src/
    ├── main.py                    # Entry point + orchestration
    ├── core/
    │   ├── constants.py           # Enums, defaults
    │   ├── governance.py          # Immutable safety engine
    │   ├── settings_manager.py    # Config + paths
    │   ├── approval_gate.py       # Human-in-the-loop
    │   └── task_models.py         # AI status + task models
    └── parts/
        ├── visibility/
        │   └── visibility_window.py
        ├── forge/
        │   ├── forge_window.py
        │   └── forge_models.py
        ├── book/
        │   ├── book_window.py
        │   └── book_models.py
        ├── constraints/
        │   ├── constraints_window.py
        │   └── constraints_models.py
        └── watcher/
            ├── watcher_window.py
            └── watcher_models.py
```

## Tech Stack

- **Python 3.10+**
- **PySide6** — desktop UI
- **mss** — screen capture
- **psutil** — system monitoring
- **hashlib** — file integrity
