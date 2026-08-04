# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Apex Glaux — Portable Cognitive Intelligence Architecture.

A self-contained intelligence engine that can be integrated into any AI host,
providing Trifecta Folding cognition, hierarchical memory, frontier reasoning,
and three-stage reversible knowledge — with far less compute than an LLM.

Proprietary to Avery Logic Works.
"""

from .core.engine import ApexGlauxEngine
from .core.interfaces import (
    IHostAdapter,
    HostCapability,
    CognitionResult,
    MemoryEntry,
    HostContext,
)
from .core.provenance import ProvenanceManager, InertMode
from .core.breeder import GlauxBreeder, Tier, TierSnapshot
from .core.host_comprehension import (
    HostComprehension,
    ASTAnalyzer,
    ComponentType,
    ComponentInfo,
    ComprehensionResult,
)
from .core.diagnostic_sentinel_adapter import DiagnosticSentinelHostAdapter

__version__ = "1.1.0"
__author__ = "Avery Logic Works"
__trademark__ = "Apex Glaux(TM)"

__all__ = [
    "ApexGlauxEngine",
    "IHostAdapter",
    "HostCapability",
    "CognitionResult",
    "MemoryEntry",
    "HostContext",
    "ProvenanceManager",
    "InertMode",
    "GlauxBreeder",
    "Tier",
    "TierSnapshot",
    "HostComprehension",
    "ASTAnalyzer",
    "ComponentType",
    "ComponentInfo",
    "ComprehensionResult",
    "DiagnosticSentinelHostAdapter",
]
