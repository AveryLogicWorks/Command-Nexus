# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

import sys
from pathlib import Path

# Ensure src is on path when run from project root
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

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


class CommandNexusApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle(QStyleFactory.create("Fusion"))
        self.app.setApplicationName("Command Nexus")
        self.app.setApplicationVersion("0.1.0-prototype")
        
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

        # License check
        try:
            self._license = get_license_manager()
        except Exception as e:
            QMessageBox.critical(None, "Initialization Error", f"Failed to initialize license manager: {e}")
            sys.exit(1)

        # ── Watcher / Anti-Tamper Tripwire ───────────────────────────────
        # Initialize the Watcher before any protected UI (license dialog).
        # Release/customer builds auto-start the Watcher armed. Source builds
        # default to DEV mode so normal development does not trip anything.
        try:
            watcher_mode = TripwireManager.recommended_mode().value
            self._watcher = WatcherEngine(
                mode=watcher_mode,
                audit_logger=self._audit,
                license_manager=self._license,
            )
            self._tripwire = self._watcher._core

            # In release mode, a failed startup check must not silently continue.
            if watcher_mode == WatcherMode.RELEASE.value:
                if not self._tripwire.is_trusted():
                    QMessageBox.critical(
                        None,
                        "Security Alert",
                        "Command Nexus has detected unauthorized modification or tampering.\n\n"
                        "The application is entering lockdown and cannot continue.\n"
                        "Contact support@averylogicworks.com if you believe this is an error.",
                    )
                    try:
                        self._audit.log(tool="CommandNexusApp", action="TRIPWIRE_STARTUP_LOCKDOWN", target=self._tripwire.report(), approved=False, status="critical")
                    except Exception:
                        pass
                    sys.exit(1)
        except Exception as e:
            QMessageBox.critical(None, "Security Error", f"Protection system initialization failed: {e}")
            sys.exit(1)
        # ──────────────────────────────────────────────────────────────────

        if not self._license.is_activated:
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
        from .parts.visibility.upgrades_panel import UpgradesDialog
        dlg = UpgradesDialog(self._visibility)
        dlg.exec()

    def _open_license_manager(self):
        """Open the License Manager dialog for upgrading or changing license."""
        from .core.license_manager_dialog import LicenseManagerDialog
        dlg = LicenseManagerDialog(self._visibility)
        dlg.exec()

    def _open_governance(self):
        """Show Governance Policy dialog with embedded Parental Controls button."""
        dlg = GovernanceRulesDialog(self._governance, self._visibility)
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

        layout.addStretch()

        btn_close = QPushButton("CLOSE")
        btn_close.setStyleSheet(
            "background-color: #21262d; color: #c9d1d9; font-weight: bold; "
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

    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QDialog { background-color: #0d1117; color: #c9d1d9; }
            QLabel { color: #c9d1d9; }
            QPushButton { border: 1px solid #30363d; border-radius: 8px; padding: 10px; }
            QPushButton:hover { border-color: #58a6ff; }
        """)


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
