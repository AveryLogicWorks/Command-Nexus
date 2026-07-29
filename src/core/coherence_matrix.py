# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""
Coherence Matrix — Structural Integrity Lattice for Command Nexus
==================================================================

Every module in the system is a node in the lattice. Each node validates
the presence and integrity of other nodes. Removing any single node
cascades failures across multiple dependent nodes, making tampering
non-localized.

The matrix uses security-suggestive naming throughout to deter casual
modification. Names like "resonance", "harmonic", "phase", and "anchor"
imply delicate interconnections without revealing exact mechanisms.

Tripwire Integration:
  - First violation: YELLOW flag (license review, warning logged)
  - Repeat violation within cooldown window: RED flag (license review,
    lockdown escalation)
  - Each subsequent violation within the window compounds severity

Upgrade Safety:
  - The founder can issue a signed upgrade token that temporarily
    suspends lattice verification while files are replaced.
  - After upgrade, the lattice re-baselines and resumes monitoring.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional


# ─── Lattice Phases (security-suggestive naming) ──────────────────────

class LatticePhase(str, Enum):
    """Each phase represents a layer of structural coherence."""
    RESONANCE = "resonance"        # Core runtime integrity
    HARMONIC = "harmonic"          # Inter-module dependency chains
    ANCHOR = "anchor"              # File presence and hash verification
    PHASE_LOCK = "phase_lock"      # Startup-time full lattice verification
    CASCADE = "cascade"            # Runtime cross-check propagation


class FlagLevel(str, Enum):
    """Escalation levels for lattice violations."""
    GREEN = "green"        # All nodes coherent
    YELLOW = "yellow"      # First violation — license review triggered
    RED = "red"            # Repeat violation within cooldown — escalation
    CRIMSON = "crimson"    # Multiple repeat violations — lockdown


@dataclass
class LatticeNode:
    """A single node in the coherence lattice."""
    node_id: str
    module_path: str           # Relative path like "src/core/governance.py"
    phase: LatticePhase
    depends_on: list[str]      # node_ids this node requires to exist
    expected_hash: str = ""    # SHA-256 of the file at baseline
    last_checked: float = 0.0
    violations: int = 0
    last_violation_time: float = 0.0

    def __post_init__(self):
        if not self.node_id:
            raise ValueError("LatticeNode requires a node_id")


@dataclass
class LatticeViolation:
    """Record of a single lattice coherence failure."""
    node_id: str
    phase: LatticePhase
    detail: str
    timestamp: float
    flag: FlagLevel
    dependent_failures: list[str] = field(default_factory=list)


# ─── Cooldown windows for escalation ───────────────────────────────────
# Rapid escalation: hackers and AI automate attempts quickly.
# 1st violation: YELLOW
# 2nd violation within 2 hours: RED (skip 3-yellow threshold)
# 3rd violation within 2 hours: CRIMSON (immediate termination)

RAPID_ESCALATION_WINDOW = 7200     # 2 hours — all violations within this window escalate
YELLOW_COOLDOWN_SECONDS = 7200     # 2 hours — repeat within this = RED
RED_COOLDOWN_SECONDS = 7200        # 2 hours — repeat within this = CRIMSON


class CoherenceMatrix:
    """
    The structural integrity lattice.

    Weaves all Command Nexus modules into an interdependent web where
    removing any single module breaks multiple lattice paths. Every
    violation is reported to the TripwireManager for license impact.

    Usage:
        matrix = CoherenceMatrix(tripwire=tw, audit=audit_logger)
        matrix.initialize()     # Build baseline at startup
        matrix.verify()         # Full lattice check
        matrix.start_monitor()  # Background periodic checks
    """

    _instance: Optional["CoherenceMatrix"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(
        self,
        tripwire: Any | None = None,
        audit: Any | None = None,
        license_manager: Any | None = None,
    ):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        self._tripwire = tripwire
        self._audit = audit
        self._license_manager = license_manager
        self._project_root = Path(__file__).resolve().parent.parent.parent

        self._nodes: dict[str, LatticeNode] = {}
        self._violations: list[LatticeViolation] = []
        self._flag: FlagLevel = FlagLevel.GREEN
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._monitor_interval = 15.0  # seconds between checks
        self._upgrade_mode = False
        self._upgrade_token_hash: str = ""
        self._violation_history: dict[str, list[float]] = {}  # node_id -> [timestamps]
        self._termination_callbacks: list[Callable[[], None]] = []

        self._build_lattice()
        self._log("matrix_init", f"Coherence matrix initialized with {len(self._nodes)} nodes")

    # ─── Lattice Construction ──────────────────────────────────────────

    def _build_lattice(self) -> None:
        """Define the full interdependency lattice.

        Each node lists which other nodes it depends on. This creates
        a web where removing one node breaks all nodes that depend on it,
        which in turn breaks nodes that depend on THOSE, etc.
        """
        nodes = [
            # ── RESONANCE PHASE: Core runtime ──────────────────────────
            LatticeNode(
                node_id="resonance_runtime",
                module_path="src/core/nexus_ai_runtime.py",
                phase=LatticePhase.RESONANCE,
                depends_on=["harmonic_governance", "harmonic_approval", "anchor_settings", "cascade_compendium", "cascade_memory_router", "harmonic_governance_sanitizer", "harmonic_parental_controls", "harmonic_usage_policy"],
            ),
            LatticeNode(
                node_id="resonance_executor",
                module_path="src/core/runtime_executor.py",
                phase=LatticePhase.RESONANCE,
                depends_on=["resonance_runtime", "harmonic_tool_exec", "anchor_audit"],
            ),
            LatticeNode(
                node_id="resonance_backend",
                module_path="src/core/backend_manager.py",
                phase=LatticePhase.RESONANCE,
                depends_on=["resonance_runtime", "harmonic_model_registry", "anchor_settings"],
            ),

            # ── HARMONIC PHASE: Inter-module chains ────────────────────
            LatticeNode(
                node_id="harmonic_governance",
                module_path="src/core/governance.py",
                phase=LatticePhase.HARMONIC,
                depends_on=["anchor_audit", "harmonic_baseline"],
            ),
            LatticeNode(
                node_id="harmonic_approval",
                module_path="src/core/approval_gate.py",
                phase=LatticePhase.HARMONIC,
                depends_on=["anchor_audit", "harmonic_governance"],
            ),
            LatticeNode(
                node_id="harmonic_tool_exec",
                module_path="src/core/tool_executor.py",
                phase=LatticePhase.HARMONIC,
                depends_on=["harmonic_approval", "anchor_audit"],
            ),
            LatticeNode(
                node_id="harmonic_baseline",
                module_path="src/core/baseline_guardrails.py",
                phase=LatticePhase.HARMONIC,
                depends_on=["harmonic_governance", "anchor_ethical"],
            ),
            LatticeNode(
                node_id="harmonic_ethical",
                module_path="src/core/ethical_guardrail_watchers.py",
                phase=LatticePhase.HARMONIC,
                depends_on=["harmonic_governance", "harmonic_baseline", "anchor_audit"],
            ),
            LatticeNode(
                node_id="harmonic_model_registry",
                module_path="src/core/model_registry.py",
                phase=LatticePhase.HARMONIC,
                depends_on=["anchor_settings", "resonance_backend"],
            ),
            LatticeNode(
                node_id="harmonic_capability",
                module_path="src/core/capability_registry.py",
                phase=LatticePhase.HARMONIC,
                depends_on=["harmonic_governance", "anchor_settings"],
            ),
            LatticeNode(
                node_id="harmonic_scanner",
                module_path="src/core/recursive_scanner.py",
                phase=LatticePhase.HARMONIC,
                depends_on=["harmonic_governance", "anchor_audit"],
            ),
            LatticeNode(
                node_id="harmonic_stasis",
                module_path="src/core/stasis_gate.py",
                phase=LatticePhase.HARMONIC,
                depends_on=["harmonic_scanner", "harmonic_governance"],
            ),
            LatticeNode(
                node_id="harmonic_governance_sanitizer",
                module_path="src/core/governance_sanitizer.py",
                phase=LatticePhase.HARMONIC,
                depends_on=["harmonic_governance", "harmonic_baseline", "anchor_ethical"],
            ),
            LatticeNode(
                node_id="harmonic_export_review",
                module_path="src/core/export_review.py",
                phase=LatticePhase.HARMONIC,
                depends_on=["harmonic_governance_sanitizer", "harmonic_stasis", "harmonic_baseline"],
            ),
            LatticeNode(
                node_id="harmonic_parental_controls",
                module_path="src/core/parental_controls_enforcer.py",
                phase=LatticePhase.HARMONIC,
                depends_on=["harmonic_governance_sanitizer"],
            ),
            LatticeNode(
                node_id="harmonic_usage_policy",
                module_path="src/core/usage_policy.py",
                phase=LatticePhase.HARMONIC,
                depends_on=["harmonic_governance_sanitizer", "harmonic_parental_controls"],
            ),
            LatticeNode(
                node_id="harmonic_command",
                module_path="src/core/command_router.py",
                phase=LatticePhase.HARMONIC,
                depends_on=["harmonic_approval", "harmonic_tool_exec", "anchor_audit"],
            ),

            # ── ANCHOR PHASE: File presence & integrity ─────────────────
            LatticeNode(
                node_id="anchor_settings",
                module_path="src/core/settings_manager.py",
                phase=LatticePhase.ANCHOR,
                depends_on=[],
            ),
            LatticeNode(
                node_id="anchor_audit",
                module_path="src/core/audit_logger.py",
                phase=LatticePhase.ANCHOR,
                depends_on=["anchor_settings"],
            ),
            LatticeNode(
                node_id="anchor_ethical",
                module_path="src/core/ethical_guardrail_watchers.py",
                phase=LatticePhase.ANCHOR,
                depends_on=["anchor_settings"],
            ),
            LatticeNode(
                node_id="anchor_license",
                module_path="src/core/license_manager.py",
                phase=LatticePhase.ANCHOR,
                depends_on=["anchor_settings", "anchor_audit"],
            ),
            LatticeNode(
                node_id="anchor_tripwire",
                module_path="src/core/tripwire_manager.py",
                phase=LatticePhase.ANCHOR,
                depends_on=["anchor_settings", "anchor_audit", "anchor_license"],
            ),
            LatticeNode(
                node_id="anchor_ip",
                module_path="src/core/ip_watermark.py",
                phase=LatticePhase.ANCHOR,
                depends_on=[],
            ),
            LatticeNode(
                node_id="anchor_obfuscation",
                module_path="src/core/obfuscation_manager.py",
                phase=LatticePhase.ANCHOR,
                depends_on=["anchor_settings"],
            ),
            LatticeNode(
                node_id="anchor_membership",
                module_path="src/core/membership_tiers.py",
                phase=LatticePhase.ANCHOR,
                depends_on=["anchor_settings"],
            ),
            LatticeNode(
                node_id="anchor_paypal",
                module_path="src/core/paypal_integration.py",
                phase=LatticePhase.ANCHOR,
                depends_on=["anchor_settings", "anchor_membership"],
            ),
            LatticeNode(
                node_id="anchor_moirai",
                module_path="src/core/moirai_ledger.py",
                phase=LatticePhase.ANCHOR,
                depends_on=["anchor_settings", "anchor_audit"],
            ),
            LatticeNode(
                node_id="anchor_adaptive",
                module_path="src/core/adaptive_memory.py",
                phase=LatticePhase.ANCHOR,
                depends_on=["anchor_settings"],
            ),
            LatticeNode(
                node_id="anchor_tts",
                module_path="src/core/tts_engine.py",
                phase=LatticePhase.ANCHOR,
                depends_on=["anchor_settings"],
            ),
            LatticeNode(
                node_id="anchor_watcher_service",
                module_path="src/core/watcher_service.py",
                phase=LatticePhase.ANCHOR,
                depends_on=["anchor_settings", "anchor_audit"],
            ),

            # ── PHASE_LOCK: UI and parts modules ────────────────────────
            LatticeNode(
                node_id="phase_lock_main",
                module_path="src/main.py",
                phase=LatticePhase.PHASE_LOCK,
                depends_on=[
                    "resonance_runtime", "harmonic_governance", "harmonic_approval",
                    "anchor_license", "anchor_tripwire", "anchor_ip",
                    "phase_lock_visibility", "phase_lock_forge", "phase_lock_book",
                    "phase_lock_constraints", "phase_lock_watcher", "phase_lock_owner",
                    "phase_lock_customer", "phase_lock_tour",
                ],
            ),
            LatticeNode(
                node_id="phase_lock_visibility",
                module_path="src/parts/visibility/visibility_window.py",
                phase=LatticePhase.PHASE_LOCK,
                depends_on=["anchor_settings", "harmonic_governance", "anchor_membership"],
            ),
            LatticeNode(
                node_id="phase_lock_forge",
                module_path="src/parts/forge/forge_window.py",
                phase=LatticePhase.PHASE_LOCK,
                depends_on=["harmonic_capability", "resonance_runtime", "anchor_settings"],
            ),
            LatticeNode(
                node_id="phase_lock_book",
                module_path="src/parts/book/book_window.py",
                phase=LatticePhase.PHASE_LOCK,
                depends_on=["anchor_adaptive", "harmonic_governance", "anchor_settings"],
            ),
            LatticeNode(
                node_id="phase_lock_constraints",
                module_path="src/parts/constraints/constraints_window.py",
                phase=LatticePhase.PHASE_LOCK,
                depends_on=["harmonic_baseline", "harmonic_governance", "anchor_settings"],
            ),
            LatticeNode(
                node_id="phase_lock_watcher",
                module_path="src/parts/watcher/watcher_window.py",
                phase=LatticePhase.PHASE_LOCK,
                depends_on=["anchor_tripwire", "anchor_audit", "anchor_settings"],
            ),
            LatticeNode(
                node_id="phase_lock_owner",
                module_path="src/parts/owner/owner_console.py",
                phase=LatticePhase.PHASE_LOCK,
                depends_on=["anchor_tripwire", "anchor_license", "anchor_audit"],
            ),
            LatticeNode(
                node_id="phase_lock_customer",
                module_path="src/parts/customer_support/customer_ai_window.py",
                phase=LatticePhase.PHASE_LOCK,
                depends_on=["resonance_runtime", "anchor_settings"],
            ),
            LatticeNode(
                node_id="phase_lock_tour",
                module_path="src/parts/tour/demo_tour.py",
                phase=LatticePhase.PHASE_LOCK,
                depends_on=["phase_lock_visibility", "phase_lock_forge", "anchor_settings"],
            ),

            # ── CASCADE: Cross-cutting concerns ─────────────────────────
            LatticeNode(
                node_id="cascade_coherence",
                module_path="src/core/coherence_matrix.py",
                phase=LatticePhase.CASCADE,
                depends_on=[
                    "anchor_tripwire", "anchor_audit", "anchor_license",
                    "anchor_ip", "anchor_settings",
                ],
            ),
            LatticeNode(
                node_id="cascade_translator",
                module_path="src/core/translator.py",
                phase=LatticePhase.CASCADE,
                depends_on=["anchor_settings"],
            ),
            LatticeNode(
                node_id="cascade_nexus_moirai",
                module_path="src/core/nexus_moirai.py",
                phase=LatticePhase.CASCADE,
                depends_on=["anchor_moirai", "anchor_settings"],
            ),
            LatticeNode(
                node_id="cascade_use_lockafire",
                module_path="src/core/nexus_use_lockafire.py",
                phase=LatticePhase.CASCADE,
                depends_on=["anchor_settings", "anchor_audit"],
            ),
            LatticeNode(
                node_id="cascade_compendium",
                module_path="src/core/compendium_of_truth.py",
                phase=LatticePhase.CASCADE,
                depends_on=["anchor_settings", "anchor_adaptive"],
            ),
            LatticeNode(
                node_id="cascade_memory_router",
                module_path="src/core/intelligent_memory_router.py",
                phase=LatticePhase.CASCADE,
                depends_on=["anchor_settings", "cascade_compendium", "anchor_adaptive"],
            ),
        ]

        for node in nodes:
            self._nodes[node.node_id] = node

    # ─── Baseline / Hash Management ────────────────────────────────────

    def _hash_file(self, path: Path) -> str:
        try:
            return hashlib.sha256(path.read_bytes()).hexdigest()
        except Exception:
            return ""

    def initialize(self) -> None:
        """Build the initial hash baseline for all lattice nodes."""
        for node in self._nodes.values():
            path = self._project_root / node.module_path
            if path.exists():
                node.expected_hash = self._hash_file(path)
            node.last_checked = time.time()
        self._log("matrix_baseline", f"Baseline established for {len(self._nodes)} nodes")

    def accept_current_baseline(self) -> None:
        """Re-baseline all nodes with current file contents.

        Used after a legitimate upgrade to accept new file hashes.
        Requires upgrade mode to be active.
        """
        if not self._upgrade_mode:
            self._log("matrix_baseline_denied", "Re-baseline requires active upgrade mode")
            return
        self.initialize()
        self._flag = FlagLevel.GREEN
        self._violations.clear()
        self._violation_history.clear()
        for node in self._nodes.values():
            node.violations = 0
            node.last_violation_time = 0.0
        self._log("matrix_baseline_accepted", "New baseline accepted after upgrade")

    # ─── Verification Engine ───────────────────────────────────────────

    def verify(self) -> FlagLevel:
        """Run a full lattice verification pass.

        Checks each node for:
        1. File existence
        2. File hash integrity
        3. Dependency chain coherence (all dependencies must also be valid)

        Returns the current flag level after verification.
        """
        if self._upgrade_mode:
            self._log("matrix_verify_skipped", "Upgrade mode active — verification suspended")
            return FlagLevel.GREEN

        now = time.time()
        failed_nodes: set[str] = set()
        node_results: dict[str, bool] = {}

        # Pass 1: Check file existence and hash
        for node_id, node in self._nodes.items():
            path = self._project_root / node.module_path
            exists = path.exists()
            hash_ok = False
            if exists and node.expected_hash:
                actual = self._hash_file(path)
                hash_ok = (actual == node.expected_hash)
            elif exists and not node.expected_hash:
                hash_ok = True  # No baseline yet, accept
            node.last_checked = now
            node_results[node_id] = exists and hash_ok
            if not node_results[node_id]:
                failed_nodes.add(node_id)

        # Pass 2: Check dependency chains — a node fails if any dependency fails
        cascade_changed = True
        while cascade_changed:
            cascade_changed = False
            for node_id, node in self._nodes.items():
                if node_id in failed_nodes:
                    continue
                for dep_id in node.depends_on:
                    if dep_id in failed_nodes or not node_results.get(dep_id, False):
                        failed_nodes.add(node_id)
                        node_results[node_id] = False
                        cascade_changed = True

        # Pass 3: Record violations and escalate
        if not failed_nodes:
            if self._flag != FlagLevel.GREEN:
                self._log("matrix_restored", "All lattice nodes coherent — flag cleared")
            self._flag = FlagLevel.GREEN
            return self._flag

        # Process each failure
        for failed_id in failed_nodes:
            node = self._nodes.get(failed_id)
            if not node:
                continue

            # Track violation history for escalation
            # Rapid escalation: hackers and AI attempt multiple times quickly
            # 1st violation: YELLOW
            # 2nd violation within 2 hours: RED
            # 3rd violation within 2 hours: CRIMSON (immediate termination)
            history = self._violation_history.setdefault(failed_id, [])
            history.append(now)
            # Prune entries outside the 2-hour rapid escalation window
            history[:] = [t for t in history if (now - t) < RAPID_ESCALATION_WINDOW]

            violation_count = len(history)

            # Determine flag level based on rapid escalation rules
            if violation_count >= 3:
                # 3rd violation within 2 hours = CRIMSON (skip red, go straight to kill)
                flag = FlagLevel.CRIMSON
            elif violation_count >= 2:
                # 2nd violation within 2 hours = RED (skip 3-yellow threshold)
                flag = FlagLevel.RED
            else:
                # 1st violation = YELLOW
                flag = FlagLevel.YELLOW

            # Find which dependent nodes also broke (cascade)
            cascade_failures = [
                nid for nid, n in self._nodes.items()
                if nid != failed_id and failed_id in n.depends_on and nid in failed_nodes
            ]

            violation = LatticeViolation(
                node_id=failed_id,
                phase=node.phase,
                detail=f"Module {node.module_path} missing or modified",
                timestamp=now,
                flag=flag,
                dependent_failures=cascade_failures,
            )
            self._violations.append(violation)
            node.violations += 1
            node.last_violation_time = now

            # Escalate the global flag
            if flag == FlagLevel.CRIMSON and self._flag != FlagLevel.CRIMSON:
                self._flag = FlagLevel.CRIMSON
            elif flag == FlagLevel.RED and self._flag not in (FlagLevel.RED, FlagLevel.CRIMSON):
                self._flag = FlagLevel.RED
            elif flag == FlagLevel.YELLOW and self._flag == FlagLevel.GREEN:
                self._flag = FlagLevel.YELLOW

            # Report to tripwire system
            self._report_to_tripwire(violation)

        # Trim violation log to prevent unbounded growth
        if len(self._violations) > 200:
            self._violations = self._violations[-200:]

        self._log(
            "matrix_violation",
            f"{len(failed_nodes)} nodes failed — flag={self._flag.value}",
        )
        return self._flag

    # ─── Tripwire Integration ──────────────────────────────────────────

    def _report_to_tripwire(self, violation: LatticeViolation) -> None:
        """Report a lattice violation independently.

        The CoherenceMatrix escalates on its own — it does NOT trigger
        TripwireManager lockdown. Each security system escalates independently
        so one broken layer cannot cascade into another.

        YELLOW: logged as warning, license review flagged
        RED:    logged as critical, license review escalated
        CRIMSON: license review escalated to maximum severity

        License flagging happens regardless of whether a tripwire is set,
        so violations always escalate the license even without a tripwire.
        """
        severity_map = {
            FlagLevel.YELLOW: "yellow",
            FlagLevel.RED: "red",
            FlagLevel.CRIMSON: "crimson",
        }
        severity = severity_map.get(violation.flag, "yellow")
        self._flag_license_review(severity, violation)

        # Log to audit only — do NOT call tripwire._enter_lockdown().
        # The tripwire has its own independent monitoring and lockdown path.
        # Coupling them creates a single point of failure where one system
        # can trigger a cascade in the other.
        try:
            self._log(
                f"matrix_violation_{severity}",
                f"{violation.node_id}: {violation.detail} (cascade: {len(violation.dependent_failures)})",
                "critical" if severity != "yellow" else "warning",
            )
        except Exception:
            pass

        # Phone home for RED and CRIMSON violations (not YELLOW — too noisy)
        if violation.flag in (FlagLevel.RED, FlagLevel.CRIMSON):
            try:
                from src.core.termination_beacon import launch_security_beacon, is_beacon_running
                if not is_beacon_running():
                    launch_security_beacon(
                        event_type=f"lattice_{severity}",
                        reason=f"Structural integrity {severity}: {violation.node_id} ({violation.phase.value})",
                        detail=f"{violation.detail} — cascade failures: {len(violation.dependent_failures)}",
                    )
            except Exception:
                pass

    def _flag_license_review(self, severity: str, violation: LatticeViolation) -> None:
        """Flag the license for review based on lattice violation severity."""
        if self._license_manager is None:
            return
        try:
            # Mark license for review — the license manager can check this
            # and display warnings or restrict features accordingly
            if hasattr(self._license_manager, "flag_for_review"):
                self._license_manager.flag_for_review(
                    reason=f"lattice_{severity}",
                    detail=f"{violation.node_id} ({violation.phase.value})",
                )
        except Exception:
            pass

    # ─── Monitoring ────────────────────────────────────────────────────

    def start_monitor(self, interval: float | None = None) -> None:
        """Start background lattice monitoring."""
        if interval is not None:
            self._monitor_interval = interval
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        self._log("matrix_monitor_start", f"Background monitoring started (interval={self._monitor_interval}s)")

    def stop_monitor(self) -> None:
        """Stop background monitoring."""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
        self._log("matrix_monitor_stop", "Background monitoring stopped")

    def _monitor_loop(self) -> None:
        while not self._stop_event.wait(self._monitor_interval):
            flag = self.verify()
            # If license was terminated during verification, trigger callback + beacon
            if flag == FlagLevel.CRIMSON and self._license_manager:
                try:
                    if hasattr(self._license_manager, "is_terminated") and self._license_manager.is_terminated():
                        self._log("matrix_termination_triggered", "License terminated during runtime monitoring")
                        # Launch background beacon to phone home the termination
                        try:
                            from src.core.termination_beacon import launch_beacon, is_beacon_running
                            if not is_beacon_running():
                                launch_beacon()
                                self._log("matrix_beacon_launched", "Termination beacon launched from runtime monitor")
                        except Exception:
                            pass
                        # Fire termination callbacks (e.g. show dialog)
                        for cb in self._termination_callbacks:
                            try:
                                cb()
                            except Exception:
                                pass
                except Exception:
                    pass

    def add_termination_callback(self, callback: Callable[[], None]) -> None:
        """Register a callback to fire when the license is terminated during runtime."""
        self._termination_callbacks.append(callback)

    # ─── Upgrade Mode ──────────────────────────────────────────────────

    UPGRADE_SECRET = os.environ.get("CN_UPGRADE_SECRET", "")

    def enter_upgrade_mode(self, token: str) -> bool:
        """Temporarily suspend lattice verification for a legitimate upgrade.

        The token must match the upgrade secret. This allows the founder
        to replace files without triggering tripwire violations.
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expected = hashlib.sha256(self.UPGRADE_SECRET.encode()).hexdigest()
        if token_hash != expected:
            self._log("matrix_upgrade_denied", "Invalid upgrade token")
            return False
        self._upgrade_mode = True
        self.stop_monitor()
        self._log("matrix_upgrade_entered", "Upgrade mode active — lattice verification suspended")
        return True

    def exit_upgrade_mode(self, token: str) -> bool:
        """Exit upgrade mode and re-baseline the lattice."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expected = hashlib.sha256(self.UPGRADE_SECRET.encode()).hexdigest()
        if token_hash != expected:
            self._log("matrix_upgrade_exit_denied", "Invalid upgrade token")
            return False
        self._upgrade_mode = False
        self.accept_current_baseline()
        self.start_monitor()
        self._log("matrix_upgrade_exited", "Upgrade complete — lattice re-baselined and monitoring resumed")
        return True

    # ─── Status / Reporting ────────────────────────────────────────────

    def get_flag(self) -> FlagLevel:
        return self._flag

    def is_coherent(self) -> bool:
        return self._flag == FlagLevel.GREEN

    def get_violations(self) -> list[LatticeViolation]:
        return list(self._violations)

    def get_node_count(self) -> int:
        return len(self._nodes)

    def get_failed_nodes(self) -> list[str]:
        """Return node_ids that are currently failing."""
        failed = []
        for node_id, node in self._nodes.items():
            path = self._project_root / node.module_path
            if not path.exists():
                failed.append(node_id)
                continue
            if node.expected_hash and self._hash_file(path) != node.expected_hash:
                failed.append(node_id)
        return failed

    def report(self) -> str:
        lines = [
            "Coherence Matrix Report",
            "=" * 50,
            f"Nodes: {len(self._nodes)} | Flag: {self._flag.value.upper()}",
            f"Violations: {len(self._violations)}",
            f"Upgrade Mode: {'ACTIVE' if self._upgrade_mode else 'INACTIVE'}",
            "",
            "Node Status:",
            "-" * 50,
        ]
        for node_id, node in sorted(self._nodes.items()):
            path = self._project_root / node.module_path
            status = "OK" if path.exists() else "MISSING"
            if status == "OK" and node.expected_hash:
                actual = self._hash_file(path)
                if actual != node.expected_hash:
                    status = "MODIFIED"
            deps = ", ".join(node.depends_on) if node.depends_on else "(none)"
            lines.append(f"  [{node.phase.value:12s}] {node_id:30s} {status:8s} deps: {deps}")
        if self._violations:
            lines.append("")
            lines.append("Recent Violations:")
            lines.append("-" * 50)
            for v in self._violations[-10:]:
                ts = time.strftime("%H:%M:%S", time.localtime(v.timestamp))
                lines.append(f"  [{ts}] {v.flag.value:7s} {v.node_id}: {v.detail}")
        return "\n".join(lines)

    # ─── Internal ──────────────────────────────────────────────────────

    def _log(self, action: str, detail: str, status: str = "") -> None:
        if self._audit is None:
            return
        try:
            self._audit.log(
                tool="CoherenceMatrix",
                action=action,
                target=detail,
                agent="lattice",
                approved=True,
                status=status,
            )
        except Exception:
            pass

    # ─── Dependency Injection (for late wiring) ────────────────────────

    def set_tripwire(self, tripwire: Any) -> None:
        self._tripwire = tripwire

    def set_audit(self, audit: Any) -> None:
        self._audit = audit

    def set_license_manager(self, lm: Any) -> None:
        self._license_manager = lm


# ─── Convenience singleton accessor ────────────────────────────────────

def get_coherence_matrix() -> CoherenceMatrix:
    """Get the singleton CoherenceMatrix instance."""
    return CoherenceMatrix()


if __name__ == "__main__":
    matrix = CoherenceMatrix()
    matrix.initialize()
    flag = matrix.verify()
    print(matrix.report())
    print(f"\nFlag: {flag.value.upper()}")
    sys.exit(0 if flag == FlagLevel.GREEN else 1)
