# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.2.0

"""
Task Scheduler — Controlled Scheduled Mission System for Command Nexus.

STRICT GUARDRAILS:
- No external actions (web requests, API calls, emails) without explicit user approval.
- No file deletions or system modifications without explicit user approval.
- All scheduled tasks are visible in the UI with status, next run time, and log.
- Missed tasks are tracked and surfaced to the user, NOT silently executed.
- Every execution is logged with full audit trail.
- Tasks can only run existing nexus_ai_runtime missions — no arbitrary code execution.
- The scheduler is a timer + mission runner, NOT an autonomous agent.
"""
from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Callable

from PyQt6.QtCore import QObject, pyqtSignal, QTimer


# ─── Enums ────────────────────────────────────────────────────────────

class ScheduleStatus(str, Enum):
    PENDING = "pending"        # Scheduled, waiting for trigger time
    APPROVED = "approved"      # User has approved execution
    RUNNING = "running"        # Currently executing
    COMPLETED = "completed"    # Finished successfully
    FAILED = "failed"          # Execution failed
    MISSED = "missed"          # Trigger time passed but wasn't approved in time
    PAUSED = "paused"          # User paused the schedule
    CANCELLED = "cancelled"    # User cancelled the schedule


class ScheduleType(str, Enum):
    ONCE = "once"              # Run one time at a specific datetime
    RECURRING = "recurring"    # Run on a recurring interval


class RecurrencePattern(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    EVERY_N_MINUTES = "every_n_minutes"


# ─── Risk classification ──────────────────────────────────────────────

# Missions that are safe to run without explicit approval each time
SAFE_MISSION_KEYWORDS = [
    "summarize", "explain", "translate", "write", "draft",
    "brainstorm", "outline", "analyze", "review", "plan",
    "research", "study", "describe", "list", "suggest",
]

# Missions that ALWAYS require explicit user approval
RISKY_MISSION_KEYWORDS = [
    "delete", "remove", "send", "email", "upload", "download",
    "install", "execute", "run script", "modify file", "write file",
    "shell", "command", "terminal", "powershell", "cmd",
    "api call", "web request", "http", "url", "ftp",
]


def classify_risk(task_text: str) -> str:
    """Classify a task as 'safe', 'risky', or 'blocked'."""
    text_lower = task_text.lower()
    # Check for blocked keywords (never allowed in scheduler)
    for kw in RISKY_MISSION_KEYWORDS:
        if kw in text_lower:
            return "risky"
    for kw in SAFE_MISSION_KEYWORDS:
        if kw in text_lower:
            return "safe"
    # Default to risky for unknown tasks
    return "risky"


# ─── Data structures ──────────────────────────────────────────────────

@dataclass
class ScheduledTask:
    """A single scheduled task."""
    task_id: str
    name: str
    mission_text: str             # The text to send to the AI runtime
    ai_uuid: str                  # Which AI to use
    ai_name: str                  # AI display name
    schedule_type: ScheduleType
    trigger_time: str             # ISO datetime for ONCE type
    recurrence: RecurrencePattern  # For RECURRING type
    recurrence_interval: int       # N minutes for EVERY_N_MINUTES
    status: ScheduleStatus
    requires_approval: bool        # Whether user must approve each execution
    auto_approve_safe: bool        # Auto-approve safe missions
    last_run: str                  # ISO datetime of last execution
    last_result: str               # Summary of last result
    next_run: str                  # ISO datetime of next scheduled run
    run_count: int                 # Total times this task has run
    created_date: str
    execution_log: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["schedule_type"] = self.schedule_type.value
        d["recurrence"] = self.recurrence.value
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ScheduledTask":
        return cls(
            task_id=d.get("task_id", ""),
            name=d.get("name", ""),
            mission_text=d.get("mission_text", ""),
            ai_uuid=d.get("ai_uuid", ""),
            ai_name=d.get("ai_name", ""),
            schedule_type=ScheduleType(d.get("schedule_type", "once")),
            trigger_time=d.get("trigger_time", ""),
            recurrence=RecurrencePattern(d.get("recurrence", "daily")),
            recurrence_interval=int(d.get("recurrence_interval", 0)),
            status=ScheduleStatus(d.get("status", "pending")),
            requires_approval=d.get("requires_approval", True),
            auto_approve_safe=d.get("auto_approve_safe", False),
            last_run=d.get("last_run", ""),
            last_result=d.get("last_result", ""),
            next_run=d.get("next_run", ""),
            run_count=int(d.get("run_count", 0)),
            created_date=d.get("created_date", ""),
            execution_log=d.get("execution_log", []),
        )


# ─── Scheduler engine ─────────────────────────────────────────────────

class TaskScheduler(QObject):
    """
    Core scheduler engine. Runs on a QTimer tick (every 30 seconds).
    Checks for due tasks, requests user approval if needed, and executes
    missions via the existing nexus_ai_runtime.

    Signals:
        task_due(ScheduledTask): A task is due for execution.
        task_completed(str, str): Task ID and result summary.
        task_failed(str, str): Task ID and error message.
        task_missed(str): Task ID that was missed.
        approval_needed(ScheduledTask): User approval is needed before execution.
        task_list_changed(): The task list has been updated.
    """

    task_due = pyqtSignal(object)  # ScheduledTask
    task_completed = pyqtSignal(str, str)  # task_id, result_summary
    task_failed = pyqtSignal(str, str)  # task_id, error_msg
    task_missed = pyqtSignal(str)  # task_id
    approval_needed = pyqtSignal(object)  # ScheduledTask
    task_list_changed = pyqtSignal()

    CHECK_INTERVAL_MS = 30000  # Check every 30 seconds
    MISSED_THRESHOLD_MINUTES = 60  # Tasks older than 1 hour without approval are "missed"

    def __init__(self, settings=None, runtime=None, audit_logger=None, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._runtime = runtime  # NexusAIRuntime instance
        self._audit = audit_logger
        self._tasks: list[ScheduledTask] = []
        self._lock = threading.Lock()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.setInterval(self.CHECK_INTERVAL_MS)
        self._load_tasks()

    def start(self):
        """Start the scheduler timer."""
        self._timer.start()

    def stop(self):
        """Stop the scheduler timer."""
        self._timer.stop()

    # ─── Persistence ──────────────────────────────────────────────────

    def _state_path(self) -> Path:
        base = Path.home() / ".command_nexus"
        base.mkdir(parents=True, exist_ok=True)
        return base / "scheduler_tasks.json"

    def _load_tasks(self):
        """Load tasks from disk."""
        p = self._state_path()
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                self._tasks = [ScheduledTask.from_dict(d) for d in data.get("tasks", [])]
            except Exception:
                self._tasks = []

    def _save_tasks(self):
        """Save tasks to disk."""
        p = self._state_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({
            "tasks": [t.to_dict() for t in self._tasks],
            "last_saved": datetime.now().isoformat(),
        }, indent=2), encoding="utf-8")

    # ─── Task management ──────────────────────────────────────────────

    def add_task(self, task: ScheduledTask) -> bool:
        """Add a new scheduled task."""
        with self._lock:
            # Check for duplicate task_id
            if any(t.task_id == task.task_id for t in self._tasks):
                return False
            self._tasks.append(task)
            self._save_tasks()
        self.task_list_changed.emit()
        if self._audit:
            self._audit.log(
                tool="TaskScheduler",
                action="TASK_ADDED",
                target=f"Scheduled task '{task.name}' for {task.next_run}",
                approved=True,
                status="info",
            )
        return True

    def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task."""
        with self._lock:
            before = len(self._tasks)
            self._tasks = [t for t in self._tasks if t.task_id != task_id]
            removed = len(self._tasks) < before
            if removed:
                self._save_tasks()
        if removed:
            self.task_list_changed.emit()
            if self._audit:
                self._audit.log(
                    tool="TaskScheduler",
                    action="TASK_REMOVED",
                    target=f"Removed scheduled task {task_id}",
                    approved=True,
                    status="info",
                )
        return removed

    def pause_task(self, task_id: str) -> bool:
        """Pause a scheduled task."""
        with self._lock:
            for t in self._tasks:
                if t.task_id == task_id:
                    t.status = ScheduleStatus.PAUSED
                    self._save_tasks()
                    self.task_list_changed.emit()
                    return True
            return False

    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task."""
        with self._lock:
            for t in self._tasks:
                if t.task_id == task_id and t.status == ScheduleStatus.PAUSED:
                    t.status = ScheduleStatus.PENDING
                    # Recalculate next run
                    t.next_run = self._calculate_next_run(t)
                    self._save_tasks()
                    self.task_list_changed.emit()
                    return True
            return False

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        with self._lock:
            for t in self._tasks:
                if t.task_id == task_id:
                    t.status = ScheduleStatus.CANCELLED
                    self._save_tasks()
                    self.task_list_changed.emit()
                    return True
            return False

    def approve_task(self, task_id: str) -> bool:
        """Approve a task for execution."""
        with self._lock:
            for t in self._tasks:
                if t.task_id == task_id:
                    t.status = ScheduleStatus.APPROVED
                    self._save_tasks()
                    return True
            return False

    def list_tasks(self) -> list[ScheduledTask]:
        """Return all tasks."""
        return list(self._tasks)

    def get_task(self, task_id: str) -> ScheduledTask | None:
        """Get a single task by ID."""
        for t in self._tasks:
            if t.task_id == task_id:
                return t
        return None

    def get_pending_approvals(self) -> list[ScheduledTask]:
        """Get tasks that need user approval."""
        return [t for t in self._tasks if t.status == ScheduleStatus.PENDING and t.requires_approval]

    def get_missed_tasks(self) -> list[ScheduledTask]:
        """Get tasks that were missed."""
        return [t for t in self._tasks if t.status == ScheduleStatus.MISSED]

    # ─── Timer tick ───────────────────────────────────────────────────

    def _tick(self):
        """Check for due tasks on each timer tick."""
        now = datetime.now()
        with self._lock:
            for task in self._tasks:
                if task.status in (ScheduleStatus.COMPLETED, ScheduleStatus.CANCELLED, ScheduleStatus.PAUSED):
                    continue
                if task.status == ScheduleStatus.RUNNING:
                    continue

                # Parse next_run time
                if not task.next_run:
                    continue
                try:
                    next_run = datetime.fromisoformat(task.next_run)
                except ValueError:
                    continue

                # Check if task is due
                if now >= next_run:
                    # Check if this is a missed task (requires approval but not approved)
                    if task.requires_approval and task.status != ScheduleStatus.APPROVED:
                        # Check if it's been more than the missed threshold
                        time_overdue = now - next_run
                        if time_overdue > timedelta(minutes=self.MISSED_THRESHOLD_MINUTES):
                            task.status = ScheduleStatus.MISSED
                            self._save_tasks()
                            self.task_missed.emit(task.task_id)
                            if self._audit:
                                self._audit.log(
                                    tool="TaskScheduler",
                                    action="TASK_MISSED",
                                    target=f"Task '{task.name}' was missed (not approved in time)",
                                    approved=False,
                                    status="warning",
                                )
                        else:
                            # Request approval
                            self.approval_needed.emit(task)
                        continue

                    # Task is approved or doesn't need approval — execute it
                    self._execute_task(task)
                # Check for pending approval requests
                elif task.requires_approval and task.status == ScheduleStatus.PENDING:
                    # Send approval notification if within 5 minutes of due time
                    time_until = next_run - now
                    if time_until <= timedelta(minutes=5):
                        self.approval_needed.emit(task)

    # ─── Task execution ───────────────────────────────────────────────

    def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task using the nexus_ai_runtime."""
        task.status = ScheduleStatus.RUNNING
        task.last_run = datetime.now().isoformat()
        self._save_tasks()

        self.task_due.emit(task)

        if self._audit:
            self._audit.log(
                tool="TaskScheduler",
                action="TASK_EXECUTING",
                target=f"Executing scheduled task '{task.name}'",
                approved=True,
                status="info",
            )

        # Execute in a background thread to avoid blocking the UI
        def _run():
            try:
                result = None
                if self._runtime:
                    result = self._runtime.run(
                        task=task.mission_text,
                        ai_name=task.ai_name,
                        ai_uuid=task.ai_uuid,
                    )
                else:
                    result = None

                # Record result
                summary = ""
                if result:
                    summary = getattr(result, 'title', str(result))
                else:
                    summary = "[No runtime available — task skipped]"

                task.last_result = summary
                task.run_count += 1
                task.execution_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "result": summary,
                    "status": "completed",
                })

                # Calculate next run for recurring tasks
                if task.schedule_type == ScheduleType.RECURRING:
                    task.next_run = self._calculate_next_run(task)
                    task.status = ScheduleStatus.PENDING
                else:
                    task.status = ScheduleStatus.COMPLETED

                self._save_tasks()
                self.task_completed.emit(task.task_id, summary)

                if self._audit:
                    self._audit.log(
                        tool="TaskScheduler",
                        action="TASK_COMPLETED",
                        target=f"Task '{task.name}' completed: {summary[:100]}",
                        approved=True,
                        status="info",
                    )
            except Exception as e:
                error_msg = str(e)
                task.last_result = f"Error: {error_msg}"
                task.status = ScheduleStatus.FAILED
                task.execution_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "result": error_msg,
                    "status": "failed",
                })
                self._save_tasks()
                self.task_failed.emit(task.task_id, error_msg)

                if self._audit:
                    self._audit.log(
                        tool="TaskScheduler",
                        action="TASK_FAILED",
                        target=f"Task '{task.name}' failed: {error_msg[:100]}",
                        approved=False,
                        status="error",
                    )

        threading.Thread(target=_run, daemon=True).start()

    # ─── Scheduling helpers ───────────────────────────────────────────

    @staticmethod
    def _calculate_next_run(task: ScheduledTask) -> str:
        """Calculate the next run time for a recurring task."""
        now = datetime.now()
        if task.recurrence == RecurrencePattern.HOURLY:
            next_time = now + timedelta(hours=1)
        elif task.recurrence == RecurrencePattern.DAILY:
            next_time = now + timedelta(days=1)
        elif task.recurrence == RecurrencePattern.WEEKLY:
            next_time = now + timedelta(weeks=1)
        elif task.recurrence == RecurrencePattern.EVERY_N_MINUTES:
            next_time = now + timedelta(minutes=max(1, task.recurrence_interval))
        else:
            next_time = now + timedelta(days=1)  # Default to daily
        return next_time.isoformat()

    @staticmethod
    def create_task_id() -> str:
        """Generate a unique task ID."""
        import uuid
        return f"task_{uuid.uuid4().hex[:12]}"

    @staticmethod
    def create_task(
        name: str,
        mission_text: str,
        ai_uuid: str = "",
        ai_name: str = "AI",
        schedule_type: ScheduleType = ScheduleType.ONCE,
        trigger_time: datetime | None = None,
        recurrence: RecurrencePattern = RecurrencePattern.DAILY,
        recurrence_interval: int = 0,
        auto_approve_safe: bool = False,
    ) -> ScheduledTask:
        """Create a new ScheduledTask with sensible defaults."""
        task_id = TaskScheduler.create_task_id()
        now = datetime.now()

        # Determine if approval is required based on risk classification
        risk = classify_risk(mission_text)
        requires_approval = True
        if risk == "safe" and auto_approve_safe:
            requires_approval = False

        # Calculate initial next_run
        if schedule_type == ScheduleType.ONCE and trigger_time:
            next_run = trigger_time.isoformat()
        else:
            # For recurring, calculate from now
            dummy = ScheduledTask(
                task_id=task_id, name=name, mission_text=mission_text,
                ai_uuid=ai_uuid, ai_name=ai_name,
                schedule_type=schedule_type, trigger_time="",
                recurrence=recurrence, recurrence_interval=recurrence_interval,
                status=ScheduleStatus.PENDING, requires_approval=requires_approval,
                auto_approve_safe=auto_approve_safe, last_run="", last_result="",
                next_run="", run_count=0, created_date=now.isoformat(),
            )
            next_run = TaskScheduler._calculate_next_run(dummy)

        return ScheduledTask(
            task_id=task_id,
            name=name,
            mission_text=mission_text,
            ai_uuid=ai_uuid,
            ai_name=ai_name,
            schedule_type=schedule_type,
            trigger_time=trigger_time.isoformat() if trigger_time else "",
            recurrence=recurrence,
            recurrence_interval=recurrence_interval,
            status=ScheduleStatus.PENDING,
            requires_approval=requires_approval,
            auto_approve_safe=auto_approve_safe,
            last_run="",
            last_result="",
            next_run=next_run,
            run_count=0,
            created_date=now.isoformat(),
        )
