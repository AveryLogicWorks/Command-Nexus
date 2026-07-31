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
    MemoryEntry,
    RoutingResult,
    RuntimeResult,
    RuntimeStatus,
)

__all__ = [
    "IMemoryStore",
    "IBackend",
    "ISettings",
    "ICompendium",
    "IMemoryRouter",
    "IGuardrailScreener",
    "MemoryEntry",
    "RoutingResult",
    "RuntimeResult",
    "RuntimeStatus",
]

__version__ = "0.1.0"
