from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class TrustState(Enum):
    TRUSTED = "TRUSTED"
    WARNING = "WARNING"
    RESTRICTED = "RESTRICTED"
    SAFE_LOCK = "SAFE_LOCK"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"


@dataclass
class MoiraiHealthReport:
    governance_loaded: bool = True
    watchers_loaded: bool = True
    translator_stub_loaded: bool = True
    book_access_ok: bool = True
    compendium_access_ok: bool = True
    export_review_loaded: bool = True
    runtime_gate_loaded: bool = True
    license_state_ok: bool = True
    trust_state: TrustState = TrustState.TRUSTED
    messages: List[str] = field(default_factory=list)

    def ok(self) -> bool:
        return self.trust_state == TrustState.TRUSTED and all([
            self.governance_loaded,
            self.watchers_loaded,
            self.translator_stub_loaded,
            self.book_access_ok,
            self.compendium_access_ok,
            self.export_review_loaded,
            self.runtime_gate_loaded,
            self.license_state_ok,
        ])


def check_action_allowed(action_name: str, health: MoiraiHealthReport | None = None) -> tuple[bool, str]:
    report = health or MoiraiHealthReport()
    if report.trust_state in {TrustState.SAFE_LOCK, TrustState.REVALIDATION_REQUIRED}:
        return False, (
            "Command Nexus has entered protected mode because a required governance/trust component "
            "is missing, altered, or unavailable. Repair or revalidate the installation before using protected features."
        )
    if report.trust_state == TrustState.RESTRICTED:
        return True, f"Action '{action_name}' allowed in restricted mode; additional review may apply."
    if not report.ok():
        return True, f"Action '{action_name}' allowed with warnings: " + "; ".join(report.messages)
    return True, ""


def assert_trusted(action_name: str, health: MoiraiHealthReport | None = None) -> None:
    allowed, msg = check_action_allowed(action_name, health)
    if not allowed:
        raise PermissionError(msg)
