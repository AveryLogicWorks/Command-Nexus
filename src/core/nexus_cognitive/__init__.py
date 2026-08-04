"""NEXUS Cognitive Architecture — standalone, self-testing package.

Completely isolated: no existing Command Nexus file imports this package.
When verified, snap-in happens via NexusSnapInAdapter (one-line import swap
per module, additive only, with graceful fallback).
"""

from .interfaces import (
    IMemoryStore,
    IBackend,
    ISettings,
    ICompendium,
    IMemoryRouter,
    IGuardrailScreener,
    IExternalIntelligence,
    MemoryEntry,
    RoutingResult,
    RuntimeResult,
    RuntimeStatus,
)
from .local_reasoning_engine import ExternalIntelligenceGuard
from .quantum_entanglement_cognition import TrifectaFold

__all__ = [
    "IMemoryStore",
    "IBackend",
    "ISettings",
    "ICompendium",
    "IMemoryRouter",
    "IGuardrailScreener",
    "IExternalIntelligence",
    "ExternalIntelligenceGuard",
    "TrifectaFold",
    "MemoryEntry",
    "RoutingResult",
    "RuntimeResult",
    "RuntimeStatus",
]

__version__ = "0.1.0"
