from pathlib import Path
import shutil
import sys

ROOT = Path.cwd()
TARGET = ROOT / "src" / "parts" / "visibility" / "visibility_window.py"

if not TARGET.exists():
    print("ERROR: visibility_window.py not found.")
    print(r'Run from: B:\Documents\GitHub\Command Nexus')
    sys.exit(1)

text = TARGET.read_text(encoding="utf-8")
original = text

backup = TARGET.with_suffix(".py.lily_runtime_backup")
if not backup.exists():
    shutil.copy2(TARGET, backup)

def patch(old, new, label):
    global text
    if old in text:
        text = text.replace(old, new, 1)
        print("PATCH:", label)
        return True
    print("SKIP:", label)
    return False

# Add runtime helper methods before _setup_ui.
helper = '''    def _has_real_runtime_executor(self, uuid: str) -> bool:
        """
        Registry enabled means selectable. It does NOT mean Lily has a real executor.
        Until an LLM/local backend bridge is wired, missions use visible TEST-RUNTIME.
        """
        if not self._registry:
            return False
        try:
            meta = self._registry.get(uuid) or {}
        except Exception:
            return False

        runtime_keys = (
            "executor",
            "runtime",
            "backend",
            "llm_backend",
            "callable",
            "command_handler",
            "agent_runtime",
        )
        return any(bool(meta.get(k)) for k in runtime_keys)

    def _append_visible_test_runtime_step(self, task: Task, session: AISession):
        """
        Visible fallback execution for Forge AIs like Lily when no real backend exists yet.
        This does not pretend to be a real LLM. It proves the command path, task queue,
        viewport, and audit panes are alive.
        """
        step = self._mission_progress
        idx = min(max(step - 1, 0), 5)

        thoughts = [
            f"[{session.name}] Received mission: {task.name}",
            f"[{session.name}] Reading configured abilities and safe operating limits.",
            f"[{session.name}] Building a local test plan for this request.",
            f"[{session.name}] Checking what would require approval before real action.",
            f"[{session.name}] Producing visible test output in the command window.",
            f"[{session.name}] Preparing to finish the test mission cleanly.",
        ]

        actions = [
            f"[{session.name}] TEST-RUNTIME: mission accepted.",
            f"[{session.name}] TEST-RUNTIME: registry/session path confirmed.",
            f"[{session.name}] TEST-RUNTIME: task queue and status loop confirmed.",
            f"[{session.name}] TEST-RUNTIME: viewport/audit panes confirmed.",
            f"[{session.name}] TEST-RUNTIME: no real backend executor attached yet.",
            f"[{session.name}] TEST-RUNTIME: returning result to Visibility Window.",
        ]

        trajectories = [
            "Next: parse request -> create safe local plan.",
            "Next: update Thought, Action, and Trajectory panes.",
            "Next: keep user approval-gated before real file/system action.",
            "Next: show visible output instead of silent placeholder behavior.",
            "Next: report that real Lily backend still needs an executor bridge.",
            "Next: complete test mission and return AI to idle.",
        ]

        self._thought_pane.append(thoughts[idx])
        self._action_pane.append(actions[idx])
        self._trajectory_pane.append(trajectories[idx])

'''

if "_has_real_runtime_executor" not in text:
    patch(
'''    def _setup_ui(self):
''',
helper + '''
    def _setup_ui(self):
''',
"add Lily/test runtime helper methods"
)
else:
    print("SKIP: helper methods already present")

# When starting a mission, do not stop all visible activity if there is no executor.
patch(
'''        self._viewport.start_stream("MISSION")
        self._sim.stop()
        self._update_status_display(AIStatus.RUNNING)
''',
'''        self._viewport.start_stream("MISSION")
        if self._has_real_runtime_executor(uuid):
            self._sim.stop()
        else:
            self._sim.start()
            self._thought_pane.append(f"[SYSTEM] {session.name} has no real backend executor connected yet.")
            self._action_pane.append("[SYSTEM] Running visible TEST-RUNTIME so the mission does not silently fake completion.")
            self._trajectory_pane.append("[SYSTEM] Next: wire Lily to a real local/API executor. For now, visible test lifecycle is active.")
        self._update_status_display(AIStatus.RUNNING)
''',
"show visible runtime start for Lily/no-backend"
)

# Replace the mission tick behavior so Forge AIs without executors visibly do something.
patch(
'''        if not self._registry:
            # No backend connected — fail fast with clear message
            self._mission_timer.stop()
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            session.current_task = None
            session.status = AIStatus.IDLE
            self._thought_pane.append("[SYSTEM] Backend not connected — no AI runtime available to execute this mission.")
            self._action_pane.append("[SYSTEM] Task failed. Deploy an AI from the Forge first, or connect a backend.")
            self._speak("Backend not connected. Please deploy an AI from the Forge first, or connect a backend.")
            self._update_status_display(AIStatus.FAILED)
            self._set_presence(PresenceState.BACKEND_NOT_CONNECTED, "Backend not connected")
            self._refresh_task_queue()
            self._btn_cancel.setEnabled(False)
            self._audit_event("mission_failed", msg="Backend not connected")
            return

        if self._mission_progress < 3:
            self._thought_pane.append(f"[SYSTEM] Executing step {self._mission_progress}...")
        else:
''',
'''        if not self._has_real_runtime_executor(uuid):
            if self._mission_progress <= 6:
                self._append_visible_test_runtime_step(task, session)
            else:
                self._mission_timer.stop()
                self._sim.stop()
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                session.task_history.append(task)
                session.current_task = None
                session.status = AIStatus.IDLE
                self._action_pane.append(f"[SYSTEM] TEST-RUNTIME completed '{task.name}' for {session.name}.")
                self._trajectory_pane.append("[SYSTEM] Test complete. This AI is selectable and routed, but still needs a real executor bridge.")
                self._speak(f"Test mission {task.name} completed.")
                self._update_status_display(AIStatus.IDLE)
                self._set_presence(PresenceState.IDLE, "Idle / ready")
                self._refresh_task_queue()
                self._btn_cancel.setEnabled(False)
                self._viewport.stop_stream()
                self._audit_event("mission_test_complete", msg=task.name)
            return

        if self._mission_progress < 3:
            self._append_visible_test_runtime_step(task, session)
        else:
''',
"replace silent placeholder tick with visible Lily test-runtime"
)

if text == original:
    print("No changes made. Either already patched or text structure changed.")
else:
    TARGET.write_text(text, encoding="utf-8")
    print()
    print("DONE. Patched:", TARGET)
    print("Backup made:", backup)
    print("Restart Command Nexus and run Lily again.")
