"""
The Watcher — Active Defensive AI data models.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List


class AlertSeverity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class IntegrityStatus(Enum):
    VERIFIED = "VERIFIED"
    MODIFIED = "MODIFIED"
    UNKNOWN = "UNKNOWN"
    MISSING = "MISSING"


@dataclass
class IntegrityRecord:
    """Baseline hash record for a protected file."""
    filepath: str
    expected_hash: str
    last_seen_hash: str = ""
    status: IntegrityStatus = IntegrityStatus.UNKNOWN
    last_checked: datetime = field(default_factory=datetime.now)


@dataclass
class SecurityAlert:
    """A single security event detected by The Watcher."""
    id: str
    timestamp: datetime
    severity: AlertSeverity
    source: str  # e.g., "file_integrity", "code_injection", "memory_tamper"
    description: str
    target: str  # affected file/module
    action_taken: str = ""
    resolved: bool = False

    def to_display(self) -> str:
        ts = self.timestamp.strftime("%H:%M:%S")
        return f"[{ts}] {self.severity.value}: {self.description} ({self.source})"


@dataclass
class WatcherState:
    """Current operational state of The Watcher."""
    active: bool = True
    mode: str = "dev"
    scan_interval_seconds: int = 5
    protected_files: List[str] = field(default_factory=list)
    alerts: List[SecurityAlert] = field(default_factory=list)
    integrity_records: List[IntegrityRecord] = field(default_factory=list)
    total_scans: int = 0
    violations_detected: int = 0
    last_scan: datetime = field(default_factory=datetime.now)
