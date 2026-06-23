"""
AI Forge — Data models for AI creation, storage, and runtime registration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional

from ...core.constants import UseCaseClass


class AISource(Enum):
    CREATED = "Created"
    DROPPED_IN = "Dropped-In"


@dataclass
class NexusLibrary:
    """A knowledge pack, template set, or workflow module an AI can access."""
    id: str
    name: str
    description: str
    category: str = "General"
    applies_to: List[str] = field(default_factory=list)
    enabled_by_default: bool = False
    integration_target: str = ""
    proprietary: bool = False
    external_license: str = ""
    attribution_required: bool = False
    risk_level: str = "Low"


@dataclass
class AIUnit:
    """A single AI unit within Command Nexus."""
    uuid: str
    name: str
    use_case: UseCaseClass
    source: AISource
    capabilities: List[str] = field(default_factory=list)
    abilities: List[str] = field(default_factory=list)
    personality_traits: Dict[str, int] = field(default_factory=dict)
    locked: bool = True  # Cannot be extracted once in the system
    created_at: datetime = field(default_factory=datetime.now)
    activated: bool = False  # Whether it is running in the Visibility Window
    enabled: bool = True      # Whether this tool/agent is allowed to run
    context_notes: str = ""
    archive_path: str = ""
    ability_book_path: str = ""
    ability_surfaces: Dict[str, str] = field(default_factory=dict)
    starter_workflows: List[str] = field(default_factory=list)
    guardrails: List[str] = field(default_factory=list)
    book_defaults_edited: bool = False
    libraries: List[str] = field(default_factory=list)
    is_starter: bool = False  # True for built-in starter templates

    def to_summary(self) -> str:
        status = "RUNNING" if self.activated else "IDLE"
        enabled = "ENABLED" if self.enabled else "DISABLED"
        return f"{self.name} [{self.use_case.value}] — {status} — {enabled}"
