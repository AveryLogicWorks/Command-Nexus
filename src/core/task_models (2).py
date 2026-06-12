"""
Task models for Command Nexus — mission queue, AI status, and activity tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class TaskStatus(Enum):
    PENDING = "Pending"
    WAITING_APPROVAL = "Waiting Approval"
    RUNNING = "Running"
    PAUSED = "Paused"
    FAILED = "Failed"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class AIStatus(Enum):
    IDLE = "Idle"
    WAITING_APPROVAL = "Waiting Approval"
    RUNNING = "Running"
    PAUSED = "Paused"
    FAILED = "Failed"
    COMPLETED = "Completed"


@dataclass
class Task:
    id: str
    name: str
    description: str
    assigned_ai_uuid: str
    assigned_ai_name: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    audit_log: List[str] = field(default_factory=list)

    def to_display(self) -> str:
        return f"[{self.status.value}] {self.name} — {self.assigned_ai_name}"


@dataclass
class AISession:
    uuid: str
    name: str
    status: AIStatus = AIStatus.IDLE
    current_task: Optional[Task] = None
    task_history: List[Task] = field(default_factory=list)
    activated_at: datetime = field(default_factory=datetime.now)

    def to_display(self) -> str:
        return f"{self.name} ({self.uuid}) — {self.status.value}"
