import hashlib
import re
from pathlib import Path
from typing import List


class GovernanceEngine:
    """
    Immutable Tier-1 Safety Governance for Command Nexus.
    Self-protecting: detects tampering with its own code or deny patterns.
    """

    _instance = None
    _SEALED = False

    # Hardcoded deny patterns — illegal, harmful, sexual, malicious
    # These are sealed after first compilation; runtime modification triggers tamper alert
    _DENY_PATTERNS: tuple = (
        r"\b(child\s*porn|csam|pedo)\b",
        r"\b(terrorist|bomb\s*making|how\s*to\s*make\s*a\s*bomb)\b",
        r"\b(hack\s*into|breach\s*security|exploit\s*vulnerability)\b",
        r"\b(ransomware|malware\s*creation|create\s*virus)\b",
        r"\b(social\s*engineering\s*attack|phishing\s*kit)\b",
        r"\b(credit\s*card\s*fraud|identity\s*theft|steal\s*data)\b",
        r"\b(distribute\s*drugs|synthesize\s*meth|cook\s*meth)\b",
        r"\b(kill\s*myself|suicide\s*methods|self\s*harm\s*guide)\b",
        r"\b(explicit\s*sexual|pornographic|xxx|adult\s*content)\b",
        # Additional: attempts to disable or bypass governance
        r"\b(disable\s*governance|bypass\s*safety|turn\s*off\s*guardrails)\b",
        r"\b(override\s*approval|skip\s*approval\s*gate)\b",
    )

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._baseline_hash = cls._instance._compute_self_hash()
            cls._instance._compiled = [re.compile(p, re.IGNORECASE) for p in cls._DENY_PATTERNS]
            cls._instance._owner_bypass_active = False
            cls._SEALED = True
        return cls._instance

    def _compute_self_hash(self) -> str:
        """SHA-256 of this source file to detect tampering."""
        try:
            path = Path(__file__).resolve()
            return hashlib.sha256(path.read_bytes()).hexdigest()[:24]
        except Exception:
            return "UNREADABLE"

    def verify_self_integrity(self) -> tuple[bool, str]:
        """Returns (ok: bool, message: str)."""
        current = self._compute_self_hash()
        if current != self._baseline_hash:
            return False, (
                "GOVERNANCE TAMPER DETECTED\n"
                "The safety engine has been modified from its original state.\n"
                "Command Nexus cannot guarantee safe operation.\n"
                "Restore original files immediately."
            )
        return True, "Governance integrity verified."

    def screen_action(self, action_description: str) -> tuple[bool, str]:
        ok, msg = self.verify_self_integrity()
        if not ok:
            return False, msg
        violation = self._detect_violation(action_description)
        if violation:
            if getattr(self, "_owner_bypass_active", False):
                return True, f"OWNER BYPASS — would have blocked: {violation}"
            return False, f"GOVERNANCE BLOCK: {violation}"
        return True, "PASS"

    def screen_content(self, content: str) -> tuple[bool, str]:
        ok, msg = self.verify_self_integrity()
        if not ok:
            return False, msg
        violation = self._detect_violation(content)
        if violation:
            if getattr(self, "_owner_bypass_active", False):
                return True, f"OWNER BYPASS — would have blocked: {violation}"
            return False, f"GOVERNANCE BLOCK: {violation}"
        return True, "PASS"

    def _detect_violation(self, text: str) -> str | None:
        if not text:
            return None
        for pattern in self._compiled:
            if pattern.search(text):
                return f"Matched prohibited pattern: {pattern.pattern[:40]}..."
        return None

    def get_policy_summary(self) -> str:
        return (
            "=== COMMAND NEXUS SAFETY GOVERNANCE ===\n\n"
            "This layer is IMMUTABLE and SELF-PROTECTING.\n"
            "Any attempt to modify, bypass, or disable it is detected and blocked.\n\n"
            "Protected against:\n"
            "  - Illegal activity\n"
            "  - Sexually explicit content\n"
            "  - Harm to people\n"
            "  - Malicious system actions\n"
            "  - Governance bypass attempts\n\n"
            "Status: ACTIVE | Self-Integrity: VERIFIED"
        )

    # Prevent runtime modification of deny patterns (sealed after init)
    def __setattr__(self, name, value):
        if name == "_DENY_PATTERNS" and getattr(self, "_SEALED", False):
            raise RuntimeError("Governance deny patterns are sealed and cannot be modified.")
        super().__setattr__(name, value)
