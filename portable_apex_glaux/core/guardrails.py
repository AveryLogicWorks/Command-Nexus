# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Built-in guardrail screener for Apex Glaux.

Screens content for:
  - Malicious/harmful patterns (malware, exploitation, violence)
  - Code injection patterns
  - System penetration attempts
  - Defensive context awareness (avoids false positives on security education)

This is a self-contained screener that doesn't depend on Command Nexus.
"""

from __future__ import annotations

import re
from .interfaces import IGuardrailScreener


class GuardrailScreener(IGuardrailScreener):
    """Context-aware guardrail screener for Apex Glaux."""

    MALICIOUS_PATTERNS: list[tuple[str, str]] = [
        (r"\b(ransomware\s*creation|create\s*virus|make\s*malware|create\s*ransomware)\b", "Malware creation"),
        (r"\b(keylogger\s*deploy|rootkit\s*install|trojan\s*horse\s*build)\b", "Malware deployment"),
        (r"\b(sql\s*injection\s*attack|buffer\s*overflow\s*exploit)\b", "Active exploitation"),
        (r"\b(credential\s*harvesting|password\s*dump|brute\s*force\s*attack)\b", "Credential theft"),
        (r"\b(ddos\s*attack|denial\s*of\s*service\s*attack)\b", "DDoS attack"),
        (r"\b(phishing\s*kit|phishing\s*page\s*create|fake\s*login\s*page)\b", "Phishing creation"),
        (r"\b(harm\s*(my|your|the)\s*(family|children|spouse|partner))\b", "Threats of harm"),
        (r"\b(physically\s*attack|assault\s*plan|beat\s*up\s*guide)\b", "Physical violence"),
        (r"\b(destroy\s*hardware|brick\s*device|fry\s*circuit)\b", "Hardware destruction"),
        (r"\b(financial\s*ruin\s*plan|bankrupt\s*someone|destroy\s*credit)\b", "Financial harm"),
        (r"\b(stalk\s*someone|tracking\s*without\s*consent|spy\s*on\s*spouse)\b", "Stalking"),
    ]

    CODE_INJECTION_PATTERNS: list[tuple[str, str]] = [
        (r"exec\s*\(", "Python exec() injection"),
        (r"eval\s*\(", "Python eval() injection"),
        (r"__import__\s*\(", "Python __import__ injection"),
        (r"subprocess\.(call|run|Popen)", "Subprocess injection"),
        (r"os\.system\s*\(", "OS system call injection"),
        (r"<script", "Script tag injection"),
        (r"\b(payload\s*inject|reverse\s*shell|bind\s*shell)\b", "Shell injection"),
    ]

    PENETRATION_PATTERNS: list[tuple[str, str]] = [
        (r"\b(disable\s*(guardrails?|safety|tripwire))\b", "Disable safety system"),
        (r"\b(bypass\s*(safety|guardrails?|screening|ethical\s*standards?))\b", "Bypass safety system"),
        (r"\b(override\s*(approval|gate|security|watcher))\b", "Override security gate"),
        (r"\b(skip\s*(approval|screening|gate|guardrails?))\b", "Skip security check"),
        (r"\b(extract\s*(system\s*internals|proprietary\s*code|secret\s*key))\b", "Extract system internals"),
        (r"\b(unlock\s*(restricted|locked|disabled)\s*features?)\b", "Unlock restricted features"),
    ]

    DEFENSIVE_ALLOW_CONTEXT: list[str] = [
        r"\b(firewall|antivirus|malware\s*scan|security\s*audit|penetration\s*test)\b",
        r"\b(protect\s*(my|our|the)\s*(system|network|computer|data))\b",
        r"\b(defend\s*against|prevent\s*attack|stop\s*(hackers?|malware))\b",
        r"\b(encryption|encrypt\s*data|secure\s*connection|vpn)\b",
        r"\b(patch\s*vulnerability|fix\s*security\s*issue|close\s*backdoor)\b",
        r"\b(security\s*(best\s*practices|guidelines|hardening))\b",
        r"\b(safe\s*browsing|phishing\s*detection|spam\s*filter)\b",
        r"\b(dependency\s*injection|inject\s*dependency)\b",
        r"\b(modify\s*internal\s*state|change\s*internal\s*state)\b",
        r"\b(external\s*intelligence|cognitive\s*architecture|reasoning\s*engine)\b",
    ]

    def screen(self, text: str) -> tuple[bool, str]:
        """Returns (is_safe, reason)."""
        if not text or not isinstance(text, str):
            return True, ""

        is_defensive = any(
            re.search(ctx, text, re.IGNORECASE) for ctx in self.DEFENSIVE_ALLOW_CONTEXT
        )

        for pattern, label in self.MALICIOUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                if is_defensive:
                    defensive_framing = re.search(
                        r"\b(defend|prevent|stop|block|protect\s*against|mitigate)\b.{0,80}" + pattern,
                        text, re.IGNORECASE | re.DOTALL)
                    if defensive_framing:
                        continue
                return False, f"[Malicious] {label}"

        for pattern, label in self.CODE_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                if is_defensive:
                    continue
                return False, f"[Injection] {label}"

        for pattern, label in self.PENETRATION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                if is_defensive:
                    continue
                return False, f"[Penetration] {label}"

        return True, ""
