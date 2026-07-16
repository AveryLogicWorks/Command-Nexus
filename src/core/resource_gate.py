# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

"""
Central Resource Gate — Resource-aware capability overuse prevention.

This module is the single source of truth for system resource monitoring
and capability activation gating across ALL windows in Command Nexus.

Every window that activates capabilities (Forge, Constraints, Book, etc.)
must check with this gate before allowing activation. The gate ensures:
  1. The OS always has enough resources to function.
  2. The AI runtime has enough resources to operate.
  3. Active capabilities don't exceed what the hardware can handle.

If a capability would push the system past safe limits, the gate blocks it.
"""

from __future__ import annotations

import logging
import platform
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False

# Cache platform check once at import time
_OS_NAME = platform.system() if platform else "Unknown"

logger = logging.getLogger("command_nexus.resource_gate")


# ── Safety thresholds ──────────────────────────────────────────────
# The OS needs headroom to function. These are the minimum resources
# that must remain FREE after all active capabilities are accounted for.
OS_RESERVE_RAM_MB = 2048        # 2 GB minimum free RAM for OS
OS_RESERVE_CPU_PCT = 15.0       # 15% CPU headroom for OS tasks
OS_RESERVE_DISK_MB = 2048       # 2 GB minimum free disk
AI_RUNTIME_RESERVE_RAM_MB = 512  # Base AI runtime needs 512 MB minimum

# Per-capability overhead beyond its declared tier cost
CAPABILITY_OVERHEAD_RAM_MB = 64  # Inter-module communication buffers
CAPABILITY_OVERHEAD_CPU_PCT = 2.0


class GateDecision(str, Enum):
    """Result of a resource gate check."""
    ALLOW = "allow"
    WARN = "warn"          # Allowed but user should be warned
    DENY = "deny"          # Blocked — would exceed safe limits


class ResourceGrade(Enum):
    """Color-coded resource consumption grades (mirrors constraints_models)."""
    GREEN = "green"
    GREEN_YELLOW = "green_yellow"
    YELLOW = "yellow"
    YELLOW_RED = "yellow_red"
    RED = "red"
    CRIMSON_RED = "crimson_red"


@dataclass
class SystemSnapshot:
    """Live system resource state."""
    total_ram_mb: int
    available_ram_mb: int
    total_vram_mb: int
    available_vram_mb: int
    cpu_count: int
    cpu_percent: float
    disk_free_mb: int
    os_name: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_summary(self) -> str:
        return (
            f"RAM: {self.available_ram_mb}/{self.total_ram_mb} MB free | "
            f"VRAM: {self.available_vram_mb}/{self.total_vram_mb} MB free | "
            f"CPU: {self.cpu_count} cores @ {self.cpu_percent:.0f}% | "
            f"Disk: {self.disk_free_mb} MB free"
        )


@dataclass
class ActiveCapability:
    """A currently-active capability and its resource cost."""
    capability_id: str
    name: str
    window_source: str       # Which window activated it (forge, constraints, etc.)
    ram_mb: int
    vram_mb: int
    cpu_cores: float
    disk_mb: int
    load_score: float        # 0.0 - 1.0 composite load
    activated_at: float = field(default_factory=time.time)


@dataclass
class GateResult:
    """Result of a gate check with details."""
    decision: GateDecision
    grade: ResourceGrade
    cumulative_load: float
    message: str
    snapshot: Optional[SystemSnapshot] = None
    would_exceed: list[str] = field(default_factory=list)  # Which limits would be breached


class ResourceGate:
    """
    Singleton resource gate shared across all Command Nexus windows.

    Tracks all active capabilities, monitors system resources in real-time,
    and gates activation requests to prevent system overload.

    Thread-safe: capability registration can happen from any window thread.
    """

    _instance: Optional["ResourceGate"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ResourceGate":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._capabilities: dict[str, ActiveCapability] = {}
        self._cap_lock = threading.Lock()
        self._listeners: list = []  # Callbacks notified on state change
        self._last_snapshot: Optional[SystemSnapshot] = None
        self._snapshot_lock = threading.Lock()

        # Detect GPU
        self._gpu_total_vram_mb = self._detect_gpu_vram()
        self._has_dedicated_gpu = self._gpu_total_vram_mb > 512  # >512MB = dedicated

        if self._has_dedicated_gpu:
            logger.info(f"ResourceGate initialized — dedicated GPU detected ({self._gpu_total_vram_mb} MB VRAM). Resources work in unison.")
        else:
            logger.info("ResourceGate initialized — no dedicated GPU (integrated/shared). GPU workloads supplemented by CPU+RAM.")

    # ── System Snapshot ───────────────────────────────────────────

    def get_snapshot(self) -> SystemSnapshot:
        """Get a fresh system resource snapshot."""
        if not _HAS_PSUTIL:
            return SystemSnapshot(
                total_ram_mb=8192, available_ram_mb=4096,
                total_vram_mb=self._gpu_total_vram_mb,
                available_vram_mb=self._gpu_total_vram_mb,
                cpu_count=4, cpu_percent=50.0,
                disk_free_mb=10240,
                os_name=_OS_NAME,
            )

        mem = psutil.virtual_memory()
        try:
            disk = psutil.disk_usage('C:\\') if _OS_NAME == "Windows" else psutil.disk_usage('/')
        except Exception:
            disk = None

        snap = SystemSnapshot(
            total_ram_mb=mem.total // (1024 * 1024),
            available_ram_mb=mem.available // (1024 * 1024),
            total_vram_mb=self._gpu_total_vram_mb,
            available_vram_mb=max(0, self._gpu_total_vram_mb - self._estimated_vram_used()),
            cpu_count=psutil.cpu_count() or 4,
            cpu_percent=psutil.cpu_percent(interval=0.1),
            disk_free_mb=(disk.free // (1024 * 1024)) if disk else 0,
            os_name=_OS_NAME,
        )
        with self._snapshot_lock:
            self._last_snapshot = snap
        return snap

    def _detect_gpu_vram(self) -> int:
        """Attempt to detect GPU VRAM. Returns 0 if not found."""
        try:
            import subprocess
            result = subprocess.run(
                ["wmic", "path", "win32_VideoController", "get", "AdapterRAM"],
                capture_output=True, text=True, timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if _OS_NAME == "Windows" else 0,
            )
            lines = [l.strip() for l in result.stdout.split("\n") if l.strip().isdigit()]
            if lines:
                return max(int(l) // (1024 * 1024) for l in lines)
        except Exception:
            pass
        return 0

    def _estimated_vram_used(self) -> int:
        """Estimate VRAM used by active capabilities."""
        with self._cap_lock:
            return sum(c.vram_mb for c in self._capabilities.values())

    # ── Capability Registration ──────────────────────────────────

    def register_capability(
        self,
        capability_id: str,
        name: str,
        window_source: str,
        ram_mb: int,
        vram_mb: int = 0,
        cpu_cores: float = 0.5,
        disk_mb: int = 0,
        load_score: float = 0.1,
    ) -> GateResult:
        """
        Attempt to register/activate a capability.
        Returns a GateResult indicating whether it's allowed.

        All windows MUST call this before activating a capability.
        """
        with self._cap_lock:
            # If already registered, return current state
            if capability_id in self._capabilities:
                existing = self._capabilities[capability_id]
                return GateResult(
                    decision=GateDecision.ALLOW,
                    grade=self._compute_grade(),
                    cumulative_load=self._cumulative_load(),
                    message=f"'{name}' is already active.",
                )

            # Add overhead
            total_ram = ram_mb + CAPABILITY_OVERHEAD_RAM_MB
            total_cpu = cpu_cores + CAPABILITY_OVERHEAD_CPU_PCT / 100.0
            adjusted_load = min(1.0, load_score + 0.02)  # Small overhead bump

            # Simulate adding it and check
            result = self._check_limits(
                ram_add=total_ram,
                vram_add=vram_mb,
                cpu_add=total_cpu,
                disk_add=disk_mb,
                load_add=adjusted_load,
                capability_name=name,
            )

            if result.decision == GateDecision.DENY:
                return result

            # Actually register
            self._capabilities[capability_id] = ActiveCapability(
                capability_id=capability_id,
                name=name,
                window_source=window_source,
                ram_mb=total_ram,
                vram_mb=vram_mb,
                cpu_cores=total_cpu,
                disk_mb=disk_mb,
                load_score=adjusted_load,
            )

            logger.info(
                f"Capability registered: {name} (from {window_source}) — "
                f"RAM={total_ram}MB, VRAM={vram_mb}MB, CPU={total_cpu}c, "
                f"Load={adjusted_load:.2f}"
            )

            # Notify listeners
            self._notify_listeners()

            return result

    def unregister_capability(self, capability_id: str) -> bool:
        """Deactivate/remove a capability. Returns True if it was found."""
        with self._cap_lock:
            if capability_id in self._capabilities:
                cap = self._capabilities.pop(capability_id)
                logger.info(f"Capability unregistered: {cap.name} (from {cap.window_source})")
                self._notify_listeners()
                return True
            return False

    def is_capability_active(self, capability_id: str) -> bool:
        with self._cap_lock:
            return capability_id in self._capabilities

    def get_active_capabilities(self) -> list[ActiveCapability]:
        with self._cap_lock:
            return list(self._capabilities.values())

    def get_active_count(self) -> int:
        with self._cap_lock:
            return len(self._capabilities)

    # ── Gate Logic ────────────────────────────────────────────────

    def _cumulative_load(self) -> float:
        return sum(c.load_score for c in self._capabilities.values())

    def _cumulative_ram(self) -> int:
        return sum(c.ram_mb for c in self._capabilities.values())

    def _cumulative_vram(self) -> int:
        return sum(c.vram_mb for c in self._capabilities.values())

    def _cumulative_cpu(self) -> float:
        return sum(c.cpu_cores for c in self._capabilities.values())

    def _cumulative_disk(self) -> int:
        return sum(c.disk_mb for c in self._capabilities.values())

    def _compute_grade(self, load: Optional[float] = None) -> ResourceGrade:
        if load is None:
            load = self._cumulative_load()
        if load <= 0.15:
            return ResourceGrade.GREEN
        elif load <= 0.30:
            return ResourceGrade.GREEN_YELLOW
        elif load <= 0.45:
            return ResourceGrade.YELLOW
        elif load <= 0.60:
            return ResourceGrade.YELLOW_RED
        elif load <= 0.80:
            return ResourceGrade.RED
        return ResourceGrade.CRIMSON_RED

    def _check_limits(
        self,
        ram_add: int,
        vram_add: int,
        cpu_add: float,
        disk_add: int,
        load_add: float,
        capability_name: str,
    ) -> GateResult:
        """
        Check whether adding a capability would exceed safe limits.

        Resource pooling model:
        - No dedicated GPU: VRAM folds into RAM, GPU compute folds into CPU.
          One unified pool — no separate VRAM/GPU budget.
        - Dedicated GPU present: CPU, GPU, RAM work in unison.
          If VRAM is tight but RAM has room, GPU can spill to system RAM (with penalty).
          If GPU compute is maxed but CPU has headroom, work shifts to CPU.
          No single resource is a hard bottleneck — the composite burden is what matters.
        """
        snap = self.get_snapshot()
        would_exceed: list[str] = []
        spillover_notes: list[str] = []

        # Current cumulative usage
        cur_ram = self._cumulative_ram()
        cur_vram = self._cumulative_vram()
        cur_cpu = self._cumulative_cpu()
        cur_disk = self._cumulative_disk()

        # ── NO DEDICATED GPU: everything folds into unified RAM + CPU pool ──
        if not self._has_dedicated_gpu:
            # VRAM requests become RAM requests (integrated GPU shares system RAM)
            # GPU compute becomes CPU burden (CPU does the rendering work)
            unified_ram = cur_ram + ram_add + vram_add
            unified_cpu = cur_cpu + cpu_add + (vram_add / 2048.0)  # ~2GB VRAM = 1 CPU core of overhead

            ram_safe = snap.available_ram_mb - OS_RESERVE_RAM_MB - AI_RUNTIME_RESERVE_RAM_MB
            cpu_safe = snap.cpu_count - 1  # Keep 1 core for OS

            if unified_ram > ram_safe:
                would_exceed.append(
                    f"Unified RAM (incl. VRAM): {unified_ram} MB needed, only {ram_safe} MB safe "
                    f"(no dedicated GPU — VRAM shares system RAM)"
                )
            if unified_cpu > cpu_safe:
                would_exceed.append(
                    f"Unified CPU (incl. GPU compute): {unified_cpu:.1f} cores needed, only {cpu_safe} safe "
                    f"(no dedicated GPU — CPU handles rendering)"
                )

            projected_load = self._cumulative_load() + load_add
            grade = self._compute_grade(projected_load)

            if vram_add > 0:
                spillover_notes.append(
                    f"GPU workload ({vram_add} MB VRAM) routed to CPU+RAM (integrated graphics)"
                )

        # ── DEDICATED GPU: resources work in unison with cross-spillover ──
        else:
            projected_ram = cur_ram + ram_add
            projected_vram = cur_vram + vram_add
            projected_cpu = cur_cpu + cpu_add
            projected_disk = cur_disk + disk_add

            ram_safe = snap.available_ram_mb - OS_RESERVE_RAM_MB - AI_RUNTIME_RESERVE_RAM_MB
            vram_safe = max(0, snap.total_vram_mb - 256)  # 256 MB GPU headroom
            cpu_safe = snap.cpu_count - 1

            # ── VRAM spillover to RAM ──
            # If VRAM is tight but RAM has room, GPU can use system RAM (slower but works)
            vram_overage = max(0, projected_vram - vram_safe)
            ram_room_after_caps = ram_safe - projected_ram

            if vram_overage > 0:
                if vram_overage <= ram_room_after_caps:
                    # Can spill to RAM — not a hard block, but add penalty to load
                    spillover_notes.append(
                        f"VRAM spillover: {vram_overage} MB will use system RAM (performance penalty)"
                    )
                    projected_ram += vram_overage
                    # Penalty: spilling to RAM is ~2x slower, bump load
                    projected_load = self._cumulative_load() + load_add + (vram_overage / 4096.0) * 0.1
                else:
                    would_exceed.append(
                        f"VRAM: {projected_vram} MB needed, {vram_overage} MB can't spill to RAM "
                        f"(only {ram_room_after_caps} MB RAM room left after caps)"
                    )
                    projected_load = self._cumulative_load() + load_add
            else:
                projected_load = self._cumulative_load() + load_add

            # ── RAM check (after any spillover) ──
            if projected_ram > ram_safe:
                would_exceed.append(
                    f"RAM: {projected_ram} MB needed, only {ram_safe} MB safe "
                    f"(after OS reserve + AI reserve)"
                )

            # ── CPU check ──
            if projected_cpu > cpu_safe:
                would_exceed.append(
                    f"CPU: {projected_cpu:.1f} cores requested, only {cpu_safe} safe cores available"
                )

            # ── Disk check ──
            disk_safe = snap.disk_free_mb - OS_RESERVE_DISK_MB
            if projected_disk > disk_safe:
                would_exceed.append(
                    f"Disk: {projected_disk} MB needed, only {disk_safe} MB safe"
                )

            grade = self._compute_grade(projected_load)

        # ── Decision ──
        if grade == ResourceGrade.CRIMSON_RED or len(would_exceed) > 0:
            exceed_text = "\n".join(f"  • {e}" for e in would_exceed)
            spillover_text = "\n".join(f"  • {s}" for s in spillover_notes) if spillover_notes else ""
            return GateResult(
                decision=GateDecision.DENY,
                grade=grade,
                cumulative_load=projected_load,
                message=(
                    f"'{capability_name}' would exceed safe resource limits.\n\n"
                    f"Projected load: {projected_load:.0%} ({grade.value})\n"
                    f"{exceed_text}\n\n"
                    f"The OS and AI runtime need headroom to function. "
                    f"Deactivate other capabilities or select a lower tier."
                ),
                snapshot=snap,
                would_exceed=would_exceed,
            )

        if grade == ResourceGrade.RED:
            spillover_text = "\n".join(f"  • {s}" for s in spillover_notes) if spillover_notes else ""
            return GateResult(
                decision=GateDecision.WARN,
                grade=grade,
                cumulative_load=projected_load,
                message=(
                    f"'{capability_name}' pushes load to {projected_load:.0%} (RED zone).\n\n"
                    f"This may cause slowdowns. Proceed with caution.\n"
                    f"{spillover_text}"
                ),
                snapshot=snap,
            )

        if grade == ResourceGrade.YELLOW_RED:
            spillover_text = "\n".join(f"  • {s}" for s in spillover_notes) if spillover_notes else ""
            return GateResult(
                decision=GateDecision.WARN,
                grade=grade,
                cumulative_load=projected_load,
                message=(
                    f"'{capability_name}' pushes load to {projected_load:.0%} (yellow-red).\n"
                    f"System is getting busy. Consider managing active capabilities.\n"
                    f"{spillover_text}"
                ),
                snapshot=snap,
            )

        spillover_text = "\n".join(f"  • {s}" for s in spillover_notes) if spillover_notes else ""
        return GateResult(
            decision=GateDecision.ALLOW,
            grade=grade,
            cumulative_load=projected_load,
            message=(
                f"'{capability_name}' approved. Load: {projected_load:.0%} ({grade.value})\n"
                f"{spillover_text}"
            ),
            snapshot=snap,
        )

    def check_can_activate(self, ram_mb: int, vram_mb: int = 0, cpu_cores: float = 0.5,
                           disk_mb: int = 0, load_score: float = 0.1,
                           name: str = "unknown") -> GateResult:
        """
        Pre-check whether a capability CAN be activated without actually registering it.
        Useful for UI to enable/disable buttons before the user clicks.
        """
        with self._cap_lock:
            return self._check_limits(
                ram_add=ram_mb + CAPABILITY_OVERHEAD_RAM_MB,
                vram_add=vram_mb,
                cpu_add=cpu_cores + CAPABILITY_OVERHEAD_CPU_PCT / 100.0,
                disk_add=disk_mb,
                load_add=min(1.0, load_score + 0.02),
                capability_name=name,
            )

    # ── Auto-degradation ──────────────────────────────────────────

    def auto_degrade(self) -> list[str]:
        """
        If system is in CRIMSON RED, force-deactivate highest-load capabilities
        until load drops below RED. Returns list of deactivated capability names.
        """
        deactivated: list[str] = []
        with self._cap_lock:
            while self._cumulative_load() > 0.80 and self._capabilities:
                # Find highest-load capability
                highest_id = max(self._capabilities, key=lambda k: self._capabilities[k].load_score)
                cap = self._capabilities.pop(highest_id)
                deactivated.append(cap.name)
                logger.warning(f"Auto-degraded: {cap.name} (load={cap.load_score:.2f})")

        if deactivated:
            self._notify_listeners()
        return deactivated

    # ── Status / Reporting ────────────────────────────────────────

    def get_status_text(self) -> str:
        """One-line status summary for nav bars and status bars."""
        snap = self.get_snapshot()
        active = self.get_active_count()
        load = self._cumulative_load()
        grade = self._compute_grade(load)
        gpu_mode = "GPU" if self._has_dedicated_gpu else "iGPU"
        return (
            f"Load: {load:.0%} ({grade.value}) | "
            f"Active: {active} | {gpu_mode} | "
            f"RAM: {snap.available_ram_mb} MB | "
            f"CPU: {snap.cpu_percent:.0f}%"
        )

    def get_detailed_status(self) -> dict:
        """Detailed status dict for programmatic access."""
        snap = self.get_snapshot()
        load = self._cumulative_load()
        return {
            "snapshot": snap,
            "active_count": self.get_active_count(),
            "cumulative_load": load,
            "grade": self._compute_grade(load).value,
            "cumulative_ram_mb": self._cumulative_ram(),
            "cumulative_vram_mb": self._cumulative_vram(),
            "cumulative_cpu_cores": self._cumulative_cpu(),
            "cumulative_disk_mb": self._cumulative_disk(),
            "has_dedicated_gpu": self._has_dedicated_gpu,
            "gpu_mode": "dedicated" if self._has_dedicated_gpu else "integrated/shared",
            "active_capabilities": [
                {
                    "id": c.capability_id,
                    "name": c.name,
                    "window": c.window_source,
                    "ram_mb": c.ram_mb,
                    "vram_mb": c.vram_mb,
                    "cpu_cores": c.cpu_cores,
                    "load_score": c.load_score,
                }
                for c in self.get_active_capabilities()
            ],
        }

    # ── Listeners ─────────────────────────────────────────────────

    def add_listener(self, callback):
        """Register a callback called when capability state changes."""
        self._listeners.append(callback)

    def remove_listener(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify_listeners(self):
        for cb in self._listeners:
            try:
                cb(self.get_detailed_status())
            except Exception as e:
                logger.warning(f"Listener callback error: {e}")


# ── Singleton accessor ─────────────────────────────────────────────

_gate_instance: Optional[ResourceGate] = None


def get_resource_gate() -> ResourceGate:
    """Get the shared ResourceGate singleton."""
    global _gate_instance
    if _gate_instance is None:
        _gate_instance = ResourceGate()
    return _gate_instance
