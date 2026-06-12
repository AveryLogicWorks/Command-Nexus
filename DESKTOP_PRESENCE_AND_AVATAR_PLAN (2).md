---
description: Desktop presence and avatar scaffold plan
---

# Command Nexus Desktop Presence / Avatar Scaffold

## Current Scaffold (this build)
- Presence state model: IDLE, THINKING, WAITING_APPROVAL, RUNNING_MISSION, PAUSED, ERROR, DEMO_MODE, BACKEND_NOT_CONNECTED.
- Settings (all default false): desktop_presence_enabled, floating_widget_enabled, avatar_enabled, avatar_mode (none/status_widget/future_avatar), selected_avatar_path, launch_on_startup.
- UI placeholder: Visibility window shows a "Desktop Presence (Scaffold)" block explaining the optional status widget/future avatar. No avatar body is running.
- Presence updates: mission start, waiting approval, running, paused, demo mode, idle/cancel set the presence label. Errors set ERROR.
- Governance: Presence is visual/status only; no actions bypass Approval Gate, Command Router, or Audit Logger.

## Optional Floating Status Widget (future toggle)
- Purpose: small on-screen indicator for Active AI, state, current task summary, waiting-approval badge, open Command Nexus, hide/disable.
- Not enabled or running by default. Should respect desktop_presence_enabled + floating_widget_enabled when built.

## Future 2D/3D Avatar Body (not implemented)
- Later: skin/avatar layer that reflects presence states.
- Future image/3D-model-to-avatar conversion pipeline (local-first, no cloud by default).
- Must remain behind approval/governance and be user-controlled; no auto-start.

## Privacy / Local-First Expectations
- No background launch by default (launch_on_startup=false).
- No cloud calls added by this scaffold.
- Presence must not collect extra data; status-only unless routed through Command Router + Approval Gate.

## What is NOT implemented now
- No live floating widget window.
- No 2D/3D avatar rendering.
- No network/model-to-avatar conversion.
- No auto-start desktop agent.

## Next Steps (future work)
- Add an optional floating widget window guarded by settings and approval.
- Wire a compact task summary + approval indicator into the widget.
- Add per-AI avatar selection (local file) when avatar_mode != none.
- Add shortcut/menu to enable/disable presence at runtime.
- Extend Book/runtime manifest to include presence preferences per AI.
- Add tests to confirm presence defaults to off and respects settings.
