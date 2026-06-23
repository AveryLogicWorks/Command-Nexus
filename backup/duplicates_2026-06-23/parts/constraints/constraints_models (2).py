"""
System Constraint Layer — Resource-aware capability upgrade models.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict


class ResourceGrade(Enum):
    """Color-coded resource consumption grades."""
    GREEN = "green"
    GREEN_YELLOW = "green_yellow"
    YELLOW = "yellow"
    YELLOW_RED = "yellow_red"
    RED = "red"
    CRIMSON_RED = "crimson_red"


@dataclass
class UpgradeTier:
    """A single activation tier for a capability."""
    name: str  # e.g., "smallest", "small", "base"
    ram_mb: int
    vram_mb: int  # GPU VRAM
    cpu_cores: float
    disk_mb: int
    load_score: float  # 0.0 - 1.0 composite load factor


@dataclass
class CapabilityModule:
    """A click-to-activate capability module."""
    id: str
    name: str
    description: str
    tiers: List[UpgradeTier]
    active: bool = False
    selected_tier: int = 0  # Index into tiers
    category: str = "General"

    def get_selected_tier(self) -> UpgradeTier:
        return self.tiers[self.selected_tier] if self.tiers else None


@dataclass
class SystemSnapshot:
    """Current system resource state."""
    total_ram_mb: int
    available_ram_mb: int
    total_vram_mb: int
    available_vram_mb: int
    cpu_count: int
    cpu_percent: float
    disk_free_mb: int
    os_name: str = ""

    def to_summary(self) -> str:
        return (
            f"RAM: {self.available_ram_mb}/{self.total_ram_mb} MB free | "
            f"VRAM: {self.available_vram_mb}/{self.total_vram_mb} MB free | "
            f"CPU: {self.cpu_count} cores @ {self.cpu_percent:.0f}% | "
            f"Disk: {self.disk_free_mb} MB free"
        )
