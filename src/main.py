# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

import sys
import os
from pathlib import Path

# Ensure src is on path when run from project root
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Load .env file — checks project root, script dir, and EXE directory
# In a PyInstaller EXE, __file__ is in a temp dir, so we also check next to sys.executable
_env_candidates = [
    project_root / ".env",
    Path(__file__).resolve().parent / ".env",
    Path(sys.executable).resolve().parent / ".env",
]
for _env_file in _env_candidates:
    if _env_file.exists():
        with open(_env_file, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _, _v = _line.partition("=")
                    os.environ.setdefault(_k.strip(), _v.strip())
        break

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMessageBox, QStyleFactory, QDialog,
    QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QLineEdit, QInputDialog
)
from src.parts.visibility.visibility_window import VisibilityWindow, ParentalControlsDialog
from src.parts.forge.forge_window import AIForgeWindow
from src.parts.book.book_window import BookWindow
from src.parts.constraints.constraints_window import ConstraintsWindow
from src.parts.watcher.watcher_window import WatcherEngine
from src.parts.owner.owner_console import OwnerConsole
from src.parts.customer_support.customer_ai_window import CustomerAIWindow
from src.parts.prototyper import PrototyperWindow  # reserved for future Hephaestus integration
from src.parts.tour.demo_tour import start_demo_tour, DemoTourController
from src.core.governance import GovernanceEngine
from src.core.settings_manager import SettingsManager
from src.core.approval_gate import ApprovalGate
from src.core.audit_logger import AuditLogger
from src.core.command_router import CommandRouter, ToolRegistry, LocalCommandServer
from src.core.approval_gate import RiskLevel
from src.core.license_manager import get_license_manager
from src.core.license_dialog import LicenseActivationDialog
from src.core.tripwire_manager import TripwireManager, WatcherMode
from src.core.ip_watermark import get_build_fingerprint, get_watermark_string
from src.core.coherence_matrix import CoherenceMatrix, FlagLevel as LatticeFlag
from src.core.termination_dialog import TerminationDialog
from src.core.ingestion_security import IngestionSecurityGate
from src.core.termination_beacon import launch_beacon, is_beacon_running


class CommandNexusApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle(QStyleFactory.create("Fusion"))
        self.app.setApplicationName("Command Nexus")
        self.app.setApplicationVersion("0.1.0-prototype")
        
        # Apply saved theme
        try:
            from src.core.theme_manager import load_theme_id, get_theme, generate_qss
            t = get_theme(load_theme_id())
            if t:
                self.app.setStyleSheet(generate_qss(t))
        except Exception:
            pass
        
        # Track resources for cleanup on failure
        self._server = None
        self._watcher = None
        self._visibility = None
        self._owner_console = None
        
        try:
            self._governance = GovernanceEngine()
        except Exception as e:
            QMessageBox.critical(None, "Initialization Error", f"Failed to initialize Governance Engine: {e}")
            sys.exit(1)

        # Initialize settings (creates workspace dirs on first run)
        try:
            self._settings = SettingsManager()
            self._settings.initialize()
        except Exception as e:
            QMessageBox.critical(None, "Initialization Error", f"Failed to initialize settings: {e}")
            sys.exit(1)
        
        try:
            self._approval = ApprovalGate(self._settings)
            self._audit = AuditLogger(self._settings)
            self._registry = ToolRegistry()
            self._router = CommandRouter(self._approval, self._audit, self._registry)
        except Exception as e:
            QMessageBox.critical(None, "Initialization Error", f"Failed to initialize core systems: {e}")
            sys.exit(1)

        # Log build fingerprint for IP traceability
        try:
            fp = get_build_fingerprint()
            self._audit.log(tool="System", action="BUILD_FINGERPRINT",
                          target=fp["build_id"], approved=True, status="info")
        except Exception:
            pass

        # License check — non-fatal: degrade to restricted mode if init fails
        try:
            self._license = get_license_manager()
        except Exception as e:
            try:
                self._audit.log(tool="CommandNexusApp", action="LICENSE_INIT_ERROR", target=str(e), approved=False, status="error")
            except Exception:
                pass
            QMessageBox.warning(
                None,
                "License System Warning",
                f"The license system could not be fully initialized: {e}\n\n"
                "Command Nexus will run in restricted mode. Some features may be unavailable.\n"
                "Contact support@averylogicworks.com if this persists.",
            )
            self._license = None

        # ── Watcher / Anti-Tamper Tripwire ───────────────────────────────
        # Initialize the Watcher before any protected UI (license dialog).
        # Release/customer builds auto-start the Watcher armed. Source builds
        # default to DEV mode so normal development does not trip anything.
        #
        # NON-FATAL: If the Watcher fails to initialize, the app continues in
        # degraded mode. One broken security component must not kill the app.
        watcher_mode = TripwireManager.recommended_mode().value
        try:
            self._watcher = WatcherEngine(
                mode=watcher_mode,
                audit_logger=self._audit,
                license_manager=self._license,
            )
            self._tripwire = self._watcher._core

            # In release mode, a failed startup check restricts features but
            # does NOT kill the app. The user gets a warning and degraded mode.
            if watcher_mode == WatcherMode.RELEASE.value:
                if not self._tripwire.is_trusted():
                    QMessageBox.warning(
                        None,
                        "Security Alert",
                        "Command Nexus has detected unauthorized modification or tampering.\n\n"
                        "The application will run in restricted mode. Some features may be blocked.\n"
                        "Contact support@averylogicworks.com if you believe this is an error.",
                    )
                    try:
                        self._audit.log(tool="CommandNexusApp", action="TRIPWIRE_STARTUP_DEGRADED", target=self._tripwire.report(), approved=False, status="critical")
                    except Exception:
                        pass
        except Exception as e:
            try:
                self._audit.log(tool="CommandNexusApp", action="TRIPWIRE_INIT_ERROR", target=str(e), approved=False, status="error")
            except Exception:
                pass
            QMessageBox.warning(
                None,
                "Protection System Warning",
                f"The protection system could not be initialized: {e}\n\n"
                "Command Nexus will continue without file integrity monitoring.\n"
                "Some security features may be unavailable.",
            )
            self._watcher = None
            self._tripwire = None
        # ──────────────────────────────────────────────────────────────────

        # ── Coherence Matrix / Lattice Verification ───────────────────────
        # The lattice weaves all modules into an interdependent web.
        # Removing any single module cascades failures across the lattice.
        # Violations escalate: YELLOW (warning) -> RED (repeat) -> CRIMSON (restricted).
        #
        # NON-FATAL: Lattice failure degrades to warning + license review flag.
        # The app continues running — one broken security layer must not kill it.
        try:
            self._lattice = CoherenceMatrix(
                tripwire=self._tripwire,
                audit=self._audit,
                license_manager=self._license,
            )
            self._lattice.initialize()
            lattice_flag = self._lattice.verify()
            self._audit.log(
                tool="CommandNexusApp",
                action="LATTICE_VERIFY_STARTUP",
                target=f"flag={lattice_flag.value}, nodes={self._lattice.get_node_count()}",
                approved=True,
                status="info",
            )
            # Start background monitoring (only in non-DEV modes)
            if watcher_mode != WatcherMode.DEV.value:
                self._lattice.start_monitor()
            # In release mode, a crimson lattice flag restricts features but
            # does NOT kill the app. License is flagged for review.
            if watcher_mode == WatcherMode.RELEASE.value and lattice_flag == LatticeFlag.CRIMSON:
                QMessageBox.warning(
                    None,
                    "Structural Integrity Alert",
                    "Command Nexus has detected structural inconsistencies.\n\n"
                    "The application will run in restricted mode with reduced functionality.\n"
                    "Contact support@averylogicworks.com if you believe this is an error.",
                )
        except Exception as e:
            # Lattice failure is non-fatal — log and continue in all modes
            try:
                self._audit.log(tool="CommandNexusApp", action="LATTICE_INIT_ERROR", target=str(e), approved=False, status="error")
            except Exception:
                pass
            if watcher_mode == WatcherMode.RELEASE.value:
                QMessageBox.warning(
                    None,
                    "Structural Integrity Warning",
                    f"The structural integrity system could not be initialized: {e}\n\n"
                    "Command Nexus will continue without lattice verification.\n"
                    "Some security features may be unavailable.",
                )
        # ──────────────────────────────────────────────────────────────────

        # ── License Termination Check ─────────────────────────────────────
        # If the license has been terminated (due to accumulated security flags),
        # show the termination dialog and block all access.
        # Also launch the background beacon to phone home the termination report.
        try:
            if self._license is not None and self._license.is_terminated():
                self._audit.log(
                    tool="CommandNexusApp",
                    action="LICENSE_TERMINATED_DETECTED",
                    target="Termination detected at startup — showing dialog + launching beacon",
                    approved=False,
                    status="critical",
                )
                # Launch background beacon — phones home the second they're online
                try:
                    if not is_beacon_running():
                        launch_beacon()
                        self._audit.log(
                            tool="CommandNexusApp",
                            action="TERMINATION_BEACON_LAUNCHED",
                            target="Background beacon launched to phone home termination report",
                            approved=False,
                            status="critical",
                        )
                except Exception as beacon_err:
                    self._audit.log(
                        tool="CommandNexusApp",
                        action="TERMINATION_BEACON_ERROR",
                        target=str(beacon_err),
                        approved=False,
                        status="error",
                    )

                term_dlg = TerminationDialog(
                    license_manager=self._license,
                    audit_logger=self._audit,
                )
                term_dlg.exec()
                sys.exit(1)
            elif self._license is not None and self._license.is_under_review():
                QMessageBox.warning(
                    None,
                    "License Under Review",
                    "Your license is currently under review due to security flags.\n\n"
                    "You may continue using Command Nexus, but certain features may be restricted.\n"
                    "If you believe this is an error, contact averylogicworks@gmail.com.",
                )
                self._audit.log(
                    tool="CommandNexusApp",
                    action="LICENSE_UNDER_REVIEW_STARTUP",
                    target="License under review — user warned",
                    approved=True,
                    status="warning",
                )
        except Exception as e:
            try:
                self._audit.log(tool="CommandNexusApp", action="TERMINATION_CHECK_ERROR", target=str(e), approved=False, status="error")
            except Exception:
                pass
        # ──────────────────────────────────────────────────────────────────

        # ── Ingestion Security Gate ───────────────────────────────────────
        # Multi-layer security for all external data entering the application.
        try:
            self._ingestion_gate = IngestionSecurityGate(
                audit=self._audit,
                tripwire=self._tripwire,
                license_manager=self._license,
                coherence_matrix=self._lattice if hasattr(self, "_lattice") else None,
            )
            self._audit.log(
                tool="CommandNexusApp",
                action="INGESTION_GATE_INIT",
                target="Multi-layer ingestion security gate initialized",
                approved=True,
                status="info",
            )
        except Exception as e:
            try:
                self._audit.log(tool="CommandNexusApp", action="INGESTION_GATE_ERROR", target=str(e), approved=False, status="error")
            except Exception:
                pass
        # ──────────────────────────────────────────────────────────────────

        if self._license is None:
            # License system failed to init — skip activation dialog, run in restricted mode
            pass
        elif not self._license.is_activated:
            try:
                dlg = LicenseActivationDialog(watcher=self._watcher)
                dlg.exec()
            except Exception as e:
                QMessageBox.critical(None, "License Error", f"License dialog failed: {e}")
                sys.exit(1)
            if not self._license.is_activated and not dlg.demo_mode:
                # User closed dialog without activating or selecting demo
                sys.exit(0)
            # Audit log the startup mode
            try:
                if dlg.demo_mode:
                    self._audit.log(tool="CommandNexusApp", action="DEMO_MODE_STARTUP", target="User started in demo mode (no license)", approved=True, status="info")
                elif self._license.is_activated:
                    self._audit.log(tool="CommandNexusApp", action="LICENSE_ACTIVATED_STARTUP", target=f"Tier: {self._license.get_tier_label()}, Days: {self._license.get_days_remaining()}", approved=True, status="info")
            except Exception as e:
                # Non-fatal: just log to console
                print(f"Warning: Failed to log startup mode: {e}")

        try:
            self._server = LocalCommandServer(self._settings)
            self._server.start()
        except Exception as e:
            QMessageBox.critical(None, "Server Error", f"Failed to start local command server: {e}")
            sys.exit(1)

        # Main window
        try:
            self._visibility = VisibilityWindow(self._router, self._registry, self._audit, self._approval, watcher=self._watcher)
            self._visibility.show()
        except Exception as e:
            QMessageBox.critical(None, "Window Error", f"Failed to create main window: {e}")
            self._cleanup()
            sys.exit(1)

        # Navigation signal wiring — MUST be before tour so buttons work during tour
        try:
            nav = self._visibility._nav
            nav.open_forge.connect(self._open_forge)
            nav.open_book.connect(self._open_book)
            nav.open_constraints.connect(self._open_constraints)
            nav.open_governance.connect(self._open_governance)
            nav.open_customer_ai.connect(self._open_customer_ai)
            nav.open_upgrades.connect(self._open_upgrades)
            nav.open_license.connect(self._open_license_manager)
            nav.open_themes.connect(self._open_themes)
            nav.open_models.connect(self._open_models)
            nav.open_knowledge.connect(self._open_knowledge)
            nav.open_voice.connect(self._open_voice)
            nav.open_scheduler.connect(self._open_scheduler)
        except Exception as e:
            QMessageBox.critical(None, "Navigation Error", f"Failed to wire navigation signals: {e}")
            self._cleanup()
            sys.exit(1)

        # Auto-load stored AIs into the Mission Control session selector
        try:
            self._auto_load_ais()
        except Exception as e:
            print(f"Warning: Could not auto-load AIs: {e}")

        # Show governance disclaimer on first run (before tour)
        try:
            from src.parts.tour.governance_disclaimer import GovernanceDisclaimerDialog
            if not GovernanceDisclaimerDialog.show_if_needed(self._visibility):
                # User declined terms — exit
                self._cleanup()
                sys.exit(0)
        except Exception as e:
            QMessageBox.critical(None, "Initialization Error", f"Failed to show governance disclaimer: {e}")
            sys.exit(1)

        # Show guided tour on first run (after signals are wired so buttons work)
        self._maybe_show_tour()

        # Check for updates asynchronously (non-blocking, silent)
        try:
            from src.core.update_checker import check_for_updates_async
            check_for_updates_async(parent=self._visibility, delay_ms=5000)
        except Exception:
            pass

        # Wire the already-created Watcher to the UI and owner console.
        try:
            self._watcher.mode_changed.connect(self._on_watcher_mode_changed)
            self._visibility.connect_watcher(self._watcher)
            self._on_watcher_mode_changed(self._watcher.get_mode())
        except Exception as e:
            QMessageBox.critical(None, "System Error", f"Failed to initialize protection engine: {e}")
            self._cleanup()
            sys.exit(1)

        # Owner-only local control console (Maintenance Console)
        try:
            self._owner_console = OwnerConsole(
                governance=self._governance,
                approval_gate=self._approval,
                watcher=self._watcher,
                audit=self._audit,
                parent=self._visibility,
            )
            self._visibility.set_owner_console(self._owner_console)
        except Exception as e:
            QMessageBox.warning(None, "Owner Console Warning", f"Failed to initialize owner console: {e}\n\nContinuing without owner console.")

        # Sub-windows (lazily instantiated)
        self._forge = None
        self._book = None
        self._constraints = None
        self._customer_ai = None
        self._prototyper = None  # reserved for future Hephaestus integration
        self._tour_controller: DemoTourController = None

    def _maybe_show_tour(self):
        """Show interactive hands-on tour on first run or if test mode is enabled."""
        first_run_marker = Path.home() / ".command_nexus" / "first_run_complete"
        test_mode = getattr(self._settings, 'test_mode', False)
        
        should_show = False
        
        if test_mode:
            should_show = True
        elif not first_run_marker.exists():
            # First run — ask the user if they want a tour
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self._visibility,
                "Welcome to Command Nexus",
                "<h2>Welcome to Command Nexus!</h2>"
                "<p>Would you like to take a quick interactive tour?</p>"
                "<p>It takes about 2 minutes and shows you how to build, deploy, "
                "and use AI assistants — no coding required.</p>"
                "<p><i>You can skip the tour at any time.</i></p>",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            should_show = (reply == QMessageBox.StandardButton.Yes)
            # Mark first run complete regardless — don't force the tour on next launch
            first_run_marker.touch()
        
        if should_show:
            if test_mode:
                self._show_test_keys_dialog()
            self._start_demo_tour()
    
    def _start_demo_tour(self):
        """Start the interactive demo tutorial (nothing persists)."""
        self._tour_controller = DemoTourController(self._visibility, self._audit, demo_mode=True)
        self._tour_controller.tour_completed.connect(self._on_tour_completed)
        self._tour_controller.tour_skipped.connect(self._on_tour_skipped)
        self._tour_controller.start_tour()
        
        if self._audit:
            self._audit.log(tool="CommandNexusApp", action="DEMO_TOUR_STARTED", target="Demo tutorial", approved=True, status="info")
    
    def _on_tour_completed(self):
        """Handle tour completion."""
        first_run_marker = Path.home() / ".command_nexus" / "first_run_complete"
        first_run_marker.touch()
        
        if self._audit:
            self._audit.log(tool="CommandNexusApp", action="INTERACTIVE_TOUR_COMPLETED", target="Tutorial finished", approved=True, status="info")
    
    def _on_tour_skipped(self):
        """Handle tour skip."""
        if self._audit:
            self._audit.log(tool="CommandNexusApp", action="INTERACTIVE_TOUR_SKIPPED", target="Tutorial skipped", approved=True, status="info")
    
    def _show_test_keys_dialog(self):
        """Show test license keys dialog (test mode only)."""
        from src.parts.tour.guided_tour import get_test_license_keys
        
        keys = get_test_license_keys()
        msg = ["<h2>🧪 Test License Keys</h2>", "<p>Use these keys to test different tiers:</p>", "<table style='font-family: monospace;'>"]
        for tier, key in keys.items():
            msg.append(f"<tr><td><b>{tier}</b></td><td>{key}</td></tr>")
        msg.append("</table>")
        msg.append("<p><i>These keys only work in test builds.</i></p>")
        
        dlg = QMessageBox(self._visibility)
        dlg.setWindowTitle("Test License Keys")
        dlg.setText("\n".join(msg))
        dlg.setTextFormat(Qt.TextFormat.RichText)
        dlg.exec()

    def _open_forge(self):
        if self._forge is None:
            self._forge = AIForgeWindow(self._registry, self._audit)
            self._forge.ai_activated.connect(self._on_ai_activated)
            self._forge.book_requested.connect(self._on_book_requested)
        self._forge.show()
        self._forge.raise_()

    def _auto_load_ais(self):
        """Load stored AI units from the Forge's store and register them in Mission Control."""
        import json
        from pathlib import Path
        store_dir = Path.home() / ".command_nexus" / "ai_store"
        if not store_dir.exists():
            return
        for path in sorted(store_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                uuid = data.get("uuid", "")
                name = data.get("name", "Unknown")
                if not uuid:
                    continue
                # Register in the visibility window's session selector
                self._visibility.add_ai_session(uuid, name)
                # Also register in the tool registry so the runtime can access metadata
                if self._registry:
                    self._registry.ensure_enabled(
                        uuid,
                        name=name,
                        use_case=data.get("use_case", "Chat Companion"),
                        abilities=data.get("abilities", ["Chat Companion"]),
                        ability_book_path=data.get("ability_book_path", ""),
                        archive_path=data.get("archive_path", ""),
                        ability_surfaces=data.get("ability_surfaces", []),
                        guardrails=data.get("guardrails", []),
                    )
            except Exception:
                continue

    def _on_book_requested(self, uuid: str, name: str):
        if self._book is None:
            self._book = BookWindow(self._registry, self._audit)
            self._book.defaults_edited.connect(self._on_book_defaults_edited)
            self._book.command_to_ai.connect(self._route_book_command)
        self._book.open_for_ai(uuid, name)

    def _route_book_command(self, command: str):
        """Route a command from the Knowledge window to the AI. Memory is NEVER included."""
        self._router.route(
            action=command,
            tool_uuid="chat",
            description=command,
            rationale="Book command",
            targets=[],
            risk=RiskLevel.LOW,
            require_approval=False,
        )

    def _on_ai_activated(self, uuid: str, name: str):
        self._visibility.add_ai_session(uuid, name)

    def _on_book_defaults_edited(self, uuid: str, edited: bool):
        if self._forge is not None:
            self._forge._on_book_defaults_edited(uuid, edited)

    def _on_watcher_mode_changed(self, mode: str):
        """Log and reflect watcher mode changes. Modes are now canonical (dev/stabilization/release/lockdown)."""
        self._audit.log(tool="CommandNexusApp", action="WATCHER_MODE_CHANGED", target=f"Protection mode is now {mode}", approved=True, status="info")

    def _open_book(self):
        if self._book is None:
            self._book = BookWindow(self._registry, self._audit)
            self._book.defaults_edited.connect(self._on_book_defaults_edited)
            self._book.command_to_ai.connect(self._route_book_command)
        self._book.show()
        self._book.raise_()
        if not self._book._current_ai_uuid:
            self._book.open_first_available()

    def _open_constraints(self):
        if self._constraints is None:
            self._constraints = ConstraintsWindow()
        self._constraints.show()
        self._constraints.raise_()

    def _open_upgrades(self):
        """Open the Upgrades Store dialog."""
        from src.parts.visibility.upgrades_panel import UpgradesDialog
        dlg = UpgradesDialog(self._visibility)
        dlg.exec()

    def _open_themes(self):
        """Open the Visual Themes selector dialog."""
        from src.parts.visibility.theme_dialog import ThemeSelectorDialog
        dlg = ThemeSelectorDialog(app_ref=self.app, parent=self._visibility)
        dlg.exec()

    def _open_license_manager(self):
        """Open the License Manager dialog for upgrading or changing license."""
        from src.core.license_manager_dialog import LicenseManagerDialog
        dlg = LicenseManagerDialog(self._visibility)
        dlg.exec()

    def _open_governance(self):
        """Show Governance Policy dialog with embedded Parental Controls button."""
        dlg = GovernanceRulesDialog(self._governance, self._visibility)
        dlg.exec()

    def _open_models(self):
        """Open the Model Manager panel."""
        from src.parts.visibility.model_manager_panel import ModelManagerDialog
        dlg = ModelManagerDialog(self._visibility)
        dlg.exec()

    def _open_knowledge(self):
        """Open the Knowledge Base (RAG) panel."""
        from src.parts.forge.knowledge_panel import KnowledgeDialog
        dlg = KnowledgeDialog(self._visibility)
        dlg.exec()

    def _open_voice(self):
        """Open the Voice Interaction panel."""
        from src.parts.visibility.voice_panel import VoiceDialog
        dlg = VoiceDialog(self._visibility)
        dlg.exec()

    def _open_scheduler(self):
        """Open the Scheduled Missions panel."""
        from src.core.task_scheduler import TaskScheduler
        from src.parts.visibility.scheduler_panel import SchedulerDialog
        if not hasattr(self, '_scheduler') or self._scheduler is None:
            self._scheduler = TaskScheduler(
                settings=self._settings,
                runtime=self._runtime if hasattr(self, '_runtime') else None,
                audit_logger=self._audit,
            )
            self._scheduler.start()
        dlg = SchedulerDialog(self._scheduler, self._visibility)
        dlg.exec()

    def _open_customer_ai(self):
        """Open the Customer AI support window."""
        if self._customer_ai is None:
            self._customer_ai = CustomerAIWindow(self._audit, self._visibility)
            self._customer_ai.escalation_needed.connect(self._on_customer_escalation)
        self._customer_ai.show()
        self._customer_ai.raise_()

    # Prototyper (Hephaestus) integration reserved for future release
    # def _open_prototyper(self):
    #     """Open the 3D Prototyper workspace."""
    #     if self._prototyper is None:
    #         self._prototyper = PrototyperWindow(self._audit, self._visibility)
    #     self._prototyper.show()
    #     self._prototyper.raise_()

    def _on_customer_escalation(self, customer_id: str, issue_type: str):
        """Handle customer issue escalation."""
        self._audit.log(
            tool="CommandNexusApp",
            action="CUSTOMER_ESCALATION",
            target=f"Customer: {customer_id}, Issue: {issue_type}",
            approved=True,
            status="warning"
        )

    def run(self):
        sys.exit(self.app.exec())

    def _cleanup(self):
        """Cleanup resources on initialization failure."""
        try:
            if self._server and hasattr(self._server, 'stop'):
                self._server.stop()
        except Exception:
            pass
        try:
            if self._watcher and hasattr(self._watcher, 'stop'):
                self._watcher.stop()
        except Exception:
            pass
        try:
            if hasattr(self, "_lattice") and self._lattice:
                self._lattice.stop_monitor()
        except Exception:
            pass
        try:
            if self._visibility and hasattr(self._visibility, 'close'):
                self._visibility.close()
        except Exception:
            pass

    def show_console(self):
        """Show the Maintenance Console (owner-only control)."""
        if hasattr(self, "_owner_console") and self._owner_console is not None:
            self._owner_console.show()
            self._owner_console.raise_()
            self._owner_console.activateWindow()


class GovernanceRulesDialog(QDialog):
    """
    Governance Policy dialog with embedded Parental Controls button.
    Opens when the user clicks the Governance button in the nav bar.
    """

    def __init__(self, governance: GovernanceEngine, parent=None):
        super().__init__(parent)
        self._governance = governance
        self.setWindowTitle("Governance Policy")
        self.setMinimumSize(520, 480)
        self._setup_ui()
        self._apply_dark_theme()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel("COMMAND NEXUS — GOVERNANCE RULES")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #58a6ff;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Policy text
        ok, msg = self._governance.verify_self_integrity()
        if not ok:
            policy_text = f"GOVERNANCE ALERT:\n{msg}"
            policy_color = "#f85149"
        else:
            policy_text = self._governance.get_policy_summary()
            policy_color = "#c9d1d9"

        policy_label = QLabel(policy_text)
        policy_label.setStyleSheet(f"color: {policy_color}; font-size: 13px; padding: 12px;")
        policy_label.setWordWrap(True)
        layout.addWidget(policy_label)

        # Separator
        sep = QLabel("")
        sep.setStyleSheet("border-top: 1px solid #30363d; margin: 8px 0;")
        layout.addWidget(sep)

        # Parental Controls section
        pc_header = QLabel("KID SAFETY — PARENTAL CONTROLS")
        pc_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #d29922;")
        layout.addWidget(pc_header)

        pc_desc = QLabel(
            "Restrict what AIs can discuss, generate, or access. "
            "Set content filters, session limits, and conversation logging for child safety."
        )
        pc_desc.setStyleSheet("color: #8b949e; font-size: 12px;")
        pc_desc.setWordWrap(True)
        layout.addWidget(pc_desc)

        btn_row = QHBoxLayout()
        btn_parental = QPushButton("Open Parental Controls")
        btn_parental.setStyleSheet(
            "background-color: #d29922; color: #0d1117; font-weight: bold; "
            "border: none; border-radius: 8px; padding: 12px 20px;"
        )
        btn_parental.clicked.connect(self._open_parental_controls)
        btn_row.addWidget(btn_parental)

        btn_info = QPushButton("What is this?")
        btn_info.setStyleSheet(
            "background-color: #30363d; color: #c9d1d9; font-weight: bold; "
            "border: 1px solid #30363d; border-radius: 8px; padding: 12px 20px;"
        )
        btn_info.clicked.connect(self._open_parental_info)
        btn_row.addWidget(btn_info)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Separator
        sep2 = QLabel("")
        sep2.setStyleSheet("border-top: 1px solid #30363d; margin: 8px 0;")
        layout.addWidget(sep2)

        # Usage Policy section
        up_header = QLabel("USAGE POLICY — ACCESS & BEHAVIOR CONTROL")
        up_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #58a6ff;")
        layout.addWidget(up_header)

        up_desc = QLabel(
            "Configure how Command Nexus can be used — for families (parental controls), "
            "businesses (enterprise restrictions), or both. Set content filters, session limits, "
            "work-only mode, data exfiltration prevention, compliance logging, and more."
        )
        up_desc.setStyleSheet("color: #8b949e; font-size: 12px;")
        up_desc.setWordWrap(True)
        layout.addWidget(up_desc)

        up_btn_row = QHBoxLayout()
        btn_policy = QPushButton("Open Usage Policy")
        btn_policy.setStyleSheet(
            "background-color: #238636; color: white; font-weight: bold; "
            "border: none; border-radius: 8px; padding: 12px 20px;"
        )
        btn_policy.clicked.connect(self._open_usage_policy)
        up_btn_row.addWidget(btn_policy)

        btn_policy_info = QPushButton("What is this?")
        btn_policy_info.setStyleSheet(
            "background-color: #30363d; color: #c9d1d9; font-weight: bold; "
            "border: 1px solid #30363d; border-radius: 8px; padding: 12px 20px;"
        )
        btn_policy_info.clicked.connect(self._open_usage_policy_info)
        up_btn_row.addWidget(btn_policy_info)
        up_btn_row.addStretch()
        layout.addLayout(up_btn_row)

        layout.addStretch()

        btn_close = QPushButton("CLOSE")
        btn_close.setStyleSheet(
            " color: #c9d1d9; font-weight: bold; "
            "border: 1px solid #30363d; border-radius: 8px; padding: 10px 20px;"
        )
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def _open_parental_controls(self):
        """Prompt for password then open ParentalControlsDialog."""
        try:
            from src.parts.visibility.visibility_window import _load_parental_settings
            settings = _load_parental_settings()
        except Exception as e:
            QMessageBox.warning(self, "Import Error", f"Failed to load parental settings: {e}")
            return
        
        pwd, ok = QInputDialog.getText(
            self, "Parental Controls Locked",
            "Enter password to access Parental Controls.\nHint: Default is 'Nexus'",
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return
        # Use hashed password verification
        try:
            from src.core.parental_controls_enforcer import verify_password
            if not verify_password(pwd, settings):
                QMessageBox.warning(self, "Access Denied", "Incorrect password.")
                return
        except ImportError:
            # Fallback to legacy plaintext check
            if pwd != settings.get("password", "Nexus"):
                QMessageBox.warning(self, "Access Denied", "Incorrect password.")
                return
        dlg = ParentalControlsDialog(self)
        dlg.exec()

    def _open_parental_info(self):
        """Show informational dialog about Parental Controls."""
        try:
            from src.parts.visibility.visibility_window import ParentalControlsInfoDialog
            dlg = ParentalControlsInfoDialog(self)
            dlg.exec()
        except Exception as e:
            QMessageBox.warning(self, "Import Error", f"Failed to open parental controls info: {e}")

    def _open_usage_policy(self):
        """Prompt for password then open UsagePolicyDialog."""
        try:
            from src.core.usage_policy import load_policy_settings, verify_password
            settings = load_policy_settings()
        except Exception as e:
            QMessageBox.warning(self, "Import Error", f"Failed to load usage policy: {e}")
            return

        pwd, ok = QInputDialog.getText(
            self, "Usage Policy Locked",
            "Enter password to access Usage Policy settings.\nHint: Default is 'Nexus'",
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return
        if not verify_password(pwd, settings):
            QMessageBox.warning(self, "Access Denied", "Incorrect password.")
            return
        try:
            from src.parts.visibility.visibility_window import UsagePolicyDialog
            dlg = UsagePolicyDialog(self)
            dlg.exec()
        except Exception as e:
            QMessageBox.warning(self, "Import Error", f"Failed to open usage policy: {e}")

    def _open_usage_policy_info(self):
        """Show informational dialog about Usage Policy."""
        try:
            from src.parts.visibility.visibility_window import UsagePolicyInfoDialog
            dlg = UsagePolicyInfoDialog(self)
            dlg.exec()
        except Exception as e:
            QMessageBox.warning(self, "Import Error", f"Failed to open usage policy info: {e}")

    def _apply_dark_theme(self):
        """Apply the current theme from theme_manager."""
        try:
            from src.core.theme_manager import load_theme_id, get_theme, generate_qss
            t = get_theme(load_theme_id())
            if t:
                self.setStyleSheet(generate_qss(t))
                return
        except Exception:
            pass
        self.setStyleSheet("")


def _run_safe_owner_mode():
    """
    Minimal recovery mode: only the owner console + core systems.
    No VisibilityWindow, no Forge, no Book, no customer UI.
    Used when the main UI is broken or during emergency repair.
    """
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setApplicationName("Command Nexus — Recovery Mode")
    app.setApplicationVersion("0.1.0-prototype")

    governance = GovernanceEngine()
    settings = SettingsManager()
    settings.initialize()
    approval = ApprovalGate(settings)
    audit = AuditLogger(settings)
    watcher = WatcherEngine(mode="REPAIR")

    console = OwnerConsole(
        governance=governance,
        approval_gate=approval,
        watcher=watcher,
        audit=audit,
        parent=None,
    )
    console.show()
    console.raise_()
    console.activateWindow()
    sys.exit(app.exec())


def main():
    args = [a.lower() for a in sys.argv[1:]]

    if "--safe-owner-mode" in args:
        _run_safe_owner_mode()
        return

    app = CommandNexusApp()

    if "--owner-console" in args:
        app.show_console()

    app.run()


if __name__ == "__main__":
    main()
