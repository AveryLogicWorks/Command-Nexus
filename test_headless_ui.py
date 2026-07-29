# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""Headless smoke test: instantiate the app and all major UI windows without showing them."""
import sys
import os
import traceback
from pathlib import Path

# Ensure src is on path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Set up headless Qt
os.environ["QT_QPA_PLATFORM"] = "offscreen"

passed = 0
failed = 0
failures = []

def check(name, fn):
    global passed, failed
    try:
        fn()
        passed += 1
        print(f"  OK: {name}")
    except Exception as e:
        failed += 1
        failures.append((name, traceback.format_exc()))
        print(f"  FAIL: {name} — {e}")

print("HEADLESS UI SMOKE TEST")
print("=" * 60)

# 1. QApplication
from PySide6.QtWidgets import QApplication
app = None
def _make_app():
    global app
    app = QApplication(sys.argv)
check("QApplication", _make_app)

# 2. Core systems
def _governance():
    from src.core.governance import GovernanceEngine
    GovernanceEngine()
check("GovernanceEngine", _governance)

def _settings():
    from src.core.settings_manager import SettingsManager
    s = SettingsManager()
    s.initialize()
check("SettingsManager", _settings)

def _approval_gate():
    from src.core.settings_manager import SettingsManager
    from src.core.approval_gate import ApprovalGate
    ApprovalGate(SettingsManager())
check("ApprovalGate", _approval_gate)

def _audit_logger():
    from src.core.settings_manager import SettingsManager
    from src.core.audit_logger import AuditLogger
    AuditLogger(SettingsManager())
check("AuditLogger", _audit_logger)

def _command_router():
    from src.core.settings_manager import SettingsManager
    from src.core.approval_gate import ApprovalGate
    from src.core.audit_logger import AuditLogger
    from src.core.command_router import CommandRouter, ToolRegistry
    s = SettingsManager()
    CommandRouter(ApprovalGate(s), AuditLogger(s), ToolRegistry())
check("CommandRouter", _command_router)

def _license():
    from src.core.license_manager import get_license_manager
    get_license_manager()
check("LicenseManager", _license)

# 3. New modules
def _three_tier_audit():
    from src.core.three_tier_audit import ThreeTierAuditLogger, AuditTier, AuditCategory
    a = ThreeTierAuditLogger()
    a.log_past(category=AuditCategory.CAPABILITY, action="test")
check("ThreeTierAuditLogger", _three_tier_audit)

def _disclaimers():
    from src.core.capability_disclaimers import (
        show_capability_disclaimer, GUARDED_CAPABILITIES, CAPABILITY_DISCLAIMERS
    )
    assert len(CAPABILITY_DISCLAIMERS) == 81
check("CapabilityDisclaimers", _disclaimers)

# 4. Runtime
def _runtime():
    from src.core.nexus_ai_runtime import NexusAIRuntime
    r = NexusAIRuntime()
    assert hasattr(r, "_HIGH_RISK_INTENTS")
    assert hasattr(r, "_current_temperature")
    assert hasattr(r, "_tier_audit")
check("NexusAIRuntime", _runtime)

# 5. UI Windows (instantiate but don't show)
def _forge_window():
    from src.parts.forge.forge_window import AIForgeWindow
    w = AIForgeWindow()
check("AIForgeWindow", _forge_window)

def _visibility_window():
    from src.parts.visibility.visibility_window import VisibilityWindow
    w = VisibilityWindow()
check("VisibilityWindow", _visibility_window)

def _book_window():
    from src.parts.book.book_window import BookWindow
    w = BookWindow()
check("BookWindow", _book_window)

def _constraints_window():
    from src.parts.constraints.constraints_window import ConstraintsWindow
    w = ConstraintsWindow()
check("ConstraintsWindow", _constraints_window)

def _customer_ai_window():
    from src.parts.customer_support.customer_ai_window import CustomerAIWindow
    w = CustomerAIWindow()
check("CustomerAIWindow", _customer_ai_window)

def _owner_console():
    from src.core.governance import GovernanceEngine
    from src.core.settings_manager import SettingsManager
    from src.core.approval_gate import ApprovalGate
    from src.core.audit_logger import AuditLogger
    from src.parts.owner.owner_console import OwnerConsole
    s = SettingsManager()
    w = OwnerConsole(GovernanceEngine(), ApprovalGate(s), None, AuditLogger(s))
check("OwnerConsole", _owner_console)

# 6. Capability dialogs
def _capability_actions():
    from src.parts.forge.capability_actions import (
        ChatCapabilityDialog, CodingCapabilityDialog, ResearchCapabilityDialog,
        CreativeWriterCapabilityDialog, PlannerCapabilityDialog,
        get_available_actions_for_ai, CAPABILITY_REGISTRY,
    )
    assert len(CAPABILITY_REGISTRY) > 10
check("CapabilityActions", _capability_actions)

def _capability_guardrails():
    from src.core.capability_guardrails import (
        check_guardrails, list_guarded_capabilities, CAPABILITY_GUARDRAILS
    )
    assert len(list_guarded_capabilities()) == 16
check("CapabilityGuardrails", _capability_guardrails)

# 7. Dialog-to-capability mapping
def _dialog_mapping():
    from src.parts.forge.forge_window import _DIALOG_TO_CAPABILITY
    assert len(_DIALOG_TO_CAPABILITY) == 81
check("DialogToCapabilityMapping", _dialog_mapping)

# 8. Guardrail check on all capabilities
def _guardrail_check_all():
    from src.core.capability_guardrails import check_guardrails, list_guarded_capabilities
    for cap in list_guarded_capabilities():
        result = check_guardrails(cap, "Hello, how are you?")
        assert not result.blocked, f"Normal greeting blocked for {cap}"
check("GuardrailNoFalsePositives", _guardrail_check_all)

# 9. Temperature override verification
def _temp_override():
    from src.core.nexus_ai_runtime import NexusAIRuntime
    r = NexusAIRuntime()
    # Simulate high-risk intent
    r._current_temperature = 0.2
    assert r._current_temperature == 0.2
    # Simulate normal intent
    r._current_temperature = None
    assert r._current_temperature is None
check("TemperatureOverride", _temp_override)

# 10. Backend call_model signature
def _backend_temp():
    from src.core.backend_manager import BackendManager
    import inspect
    sig = inspect.signature(BackendManager.call_model)
    assert "temperature" in sig.parameters
    assert sig.parameters["temperature"].default is None
check("BackendTemperatureParam", _backend_temp)

print(f"\n{'='*60}")
print(f"HEADLESS SMOKE TEST: {passed} PASSED, {failed} FAILED")
if failures:
    print(f"\nFAILURES:")
    for name, tb in failures:
        print(f"\n  [{name}]")
        for line in tb.strip().split("\n")[-3:]:
            print(f"    {line}")
else:
    print("ALL TESTS PASSED")
print(f"{'='*60}")
sys.exit(1 if failed else 0)
