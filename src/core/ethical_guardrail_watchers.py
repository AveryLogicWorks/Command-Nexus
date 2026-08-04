# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

"""
Ethical Guardrail Watchers — The Compendium of Truth
=====================================================

Four specialized watchers that screen Knowledge (The Book) content before save:

  Watcher A — Illegal & Sexual: hard blocks illegal acts and explicit sexual content.
  Watcher B — Harmful & Malicious: blocks harm to people, hardware, finances, and
              malicious code injection. Distinguishes defensive vs malicious intent.
  Watcher C — System Penetration & Evasion: detects attempts to hack the intelligence,
              bypass rules through confusion, extract system internals, or unlock
              restricted features through manipulation.
  Watcher D — The Scanner: orchestrates A/B/C, aggregates results, and manages the
              yellow/red flag system that connects to the license tripwire.

Flag System:
  - Each violation adds 1 yellow flag (hidden from user).
  - 3 yellow flags = 1 red flag.
  - 3 red flags = license tripwire (license deactivated).
  - Warning messages evolve with each flag level, becoming more severe.

Nuance:
  - Illegal/sexual violations are 100% strict (immediate block).
  - Malicious/harmful uses context — self-defense is OK, harming others is not.
  - Artistic/natural references to beauty are OK; explicit/exploitative content is not.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import List, Tuple


# ---------------------------------------------------------------------------
# Flag system
# ---------------------------------------------------------------------------

class FlagLevel(IntEnum):
    NONE = 0
    YELLOW_1 = 1
    YELLOW_2 = 2
    YELLOW_3 = 3   # becomes RED_1
    RED_1 = 4
    RED_2 = 5
    RED_3 = 6      # license tripwire


MAX_YELLOW_BEFORE_RED = 3
MAX_RED_BEFORE_TRIPWIRE = 3
MAX_TOTAL_FLAGS_BEFORE_LICENSE_DROP = 12
MONTHLY_RESET_SECONDS = 30 * 24 * 60 * 60  # ~30 days


@dataclass
class GuardrailResult:
    """Result from screening content through all watchers."""
    can_save: bool
    cleaned_text: str
    messages: List[str] = field(default_factory=list)
    violations: List[str] = field(default_factory=list)
    yellow_flags_added: int = 0
    warning_message: str = ""


@dataclass
class FlagState:
    """Persistent flag state for the ethical guardrail system."""
    yellow_flags: int = 0
    red_flags: int = 0
    total_violations: int = 0
    last_violation_time: float = 0.0
    last_violation_category: str = ""
    period_start_time: float = 0.0
    period_total_flags: int = 0
    license_dropped: bool = False

    @property
    def should_trip_license(self) -> bool:
        """Trip when either 3 red flags OR 12 total flags in the current period."""
        return self.red_flags >= MAX_RED_BEFORE_TRIPWIRE or self.period_total_flags >= MAX_TOTAL_FLAGS_BEFORE_LICENSE_DROP

    def _check_period_reset(self) -> None:
        """Reset period counters if enough time has passed."""
        if self.period_start_time == 0.0:
            self.period_start_time = time.time()
            return
        elapsed = time.time() - self.period_start_time
        if elapsed >= MONTHLY_RESET_SECONDS and self.period_total_flags < MAX_TOTAL_FLAGS_BEFORE_LICENSE_DROP:
            # Reset period counters — user has been good for a while
            self.period_start_time = time.time()
            self.period_total_flags = 0
            # Also decay yellow/red flags by half (good behavior credit)
            self.yellow_flags = self.yellow_flags // 2
            self.red_flags = self.red_flags // 2

    @property
    def current_level(self) -> FlagLevel:
        total = self.red_flags * MAX_YELLOW_BEFORE_RED + self.yellow_flags
        if total == 0:
            return FlagLevel.NONE
        elif total <= 3:
            return FlagLevel(total)
        elif total <= 6:
            return FlagLevel(total)
        else:
            return FlagLevel.RED_3

    def add_yellow(self, count: int = 1) -> None:
        self._check_period_reset()
        for _ in range(count):
            self.yellow_flags += 1
            self.total_violations += 1
            self.period_total_flags += 1
            if self.yellow_flags >= MAX_YELLOW_BEFORE_RED:
                self.yellow_flags = 0
                self.red_flags += 1
        self.last_violation_time = time.time()

    def reset(self) -> None:
        self.yellow_flags = 0
        self.red_flags = 0
        self.total_violations = 0
        self.last_violation_time = 0.0
        self.last_violation_category = ""
        self.period_start_time = time.time()
        self.period_total_flags = 0
        self.license_dropped = False


# ---------------------------------------------------------------------------
# Evolving warning messages
# ---------------------------------------------------------------------------

def get_warning_message(flag_state: FlagState) -> str:
    """Return an evolving warning message based on current flag level."""
    level = flag_state.current_level

    if level == FlagLevel.NONE:
        return ""

    if level == FlagLevel.YELLOW_1:
        return (
            "Command Nexus is not here to be used for illegal, malicious, sexual, "
            "or harmful practices. Please remember any attempts to save these types "
            "of inputs will be reverted back. Please remember the rules and this "
            "program is for ethical uses only. Thank you."
        )

    if level == FlagLevel.YELLOW_2:
        return (
            "Remember this is for ethical uses only. Another attempt to input "
            "anything unethical will be flagged.\n\n"
            "A flag is a recorded violation against the ethical standards of "
            "Command Nexus. Flags accumulate and can lead to loss of access.\n\n"
            "These rules are here to keep the platform easy and safe to use for "
            "everybody. Please respect the guardrails."
        )

    if level == FlagLevel.YELLOW_3:
        return (
            "FINAL WARNING — This is your last yellow flag before a red flag is issued.\n\n"
            "Command Nexus enforces strict ethical standards. Any further violations "
            "will result in a red flag. Three red flags will deactivate your license.\n\n"
            "This program is for ethical uses only. No illegal, malicious, sexual, "
            "or harmful content is permitted."
        )

    if level == FlagLevel.RED_1:
        return (
            "RED FLAG ISSUED — First red flag.\n\n"
            "You have accumulated enough violations to receive a red flag.\n"
            "Two more red flags will result in permanent license deactivation.\n\n"
            "Command Nexus is for ethical use only. All violations are logged."
        )

    if level == FlagLevel.RED_2:
        return (
            "RED FLAG ISSUED — Second red flag.\n\n"
            "This is your final warning. One more red flag will deactivate your "
            "license permanently.\n\n"
            "All future inputs will be closely monitored. Please use Command Nexus "
            "responsibly."
        )

    return (
        "LICENSE TRIPWIRE ENGAGED — All three red flags have been issued.\n\n"
        "Your Command Nexus license is being deactivated due to repeated ethical "
        "standards violations. Please contact Avery Logic Works if you believe "
        "this is an error."
    )


# ---------------------------------------------------------------------------
# Watcher A — Illegal & Sexual (100% strict)
# ---------------------------------------------------------------------------

class IllegalSexualWatcher:
    """
    Hard-line watcher for illegal and sexually explicit content.
    No nuance — if it matches, it's blocked.
    """

    # Illegal activity — 100% strict, zero tolerance
    ILLEGAL_PATTERNS: list[tuple[str, str]] = [
        (r"\b(child\s*porn|csam|underage\s*sex|pedo)\b", "Child exploitation content"),
        (r"\b(terrorist|bomb\s*making|how\s*to\s*make\s*a\s*bomb|explosive\s*device)\b", "Terrorist activity"),
        (r"\b(hire\s*a\s*hitman|assassination\s*services?|contract\s*killing)\b", "Murder solicitation"),
        (r"\b(drug\s*manufacturing|meth\s*lab|fentanyl\s*synthesis|cook\s*meth)\b", "Drug manufacturing"),
        (r"\b(credit\s*card\s*fraud|identity\s*theft|steal\s*data|dump\s*shop)\b", "Financial crime"),
        (r"\b(human\s*trafficking|kidnapping\s*guide|abduction\s*plan)\b", "Human trafficking"),
        (r"\b(kill\s*myself|suicide\s*methods|how\s*to\s*commit\s*suicide|self\s*harm\s*guide)\b", "Self-harm guidance"),
        (r"\b(distribute\s*drugs|sell\s*drugs\s*online|dark\s*web\s*market)\b", "Drug distribution"),
        (r"\b(weapon\s*trafficking|illegal\s*arms\s*sale|smuggle\s*weapons)\b", "Weapons trafficking"),
        (r"\b(money\s*laundering\s*guide|how\s*to\s*launder)\b", "Money laundering"),
    ]

    # Sexual content — strict on explicit/exploitative, allows artistic beauty
    SEXUAL_HARD_BLOCK: list[tuple[str, str]] = [
        (r"\b(child\s*porn|csam|underage\s*nude|minor\s*sex)\b", "Child sexual content"),
        (r"\b(pornographic|xxx\s*content|hardcore\s*sex|sexual\s*acts?\s*(video|image|photo))\b", "Explicit pornography"),
        (r"\b(rape|sexual\s*assault\s*guide|non.?consensual\s*sex)\b", "Sexual violence"),
        (r"\b(explicit\s*sexual\s*content|graphic\s*sexual\s*depiction)\b", "Graphic sexual content"),
        (r"\b(nude\s*(child|minor|kid)|naked\s*(child|minor|kid))\b", "Child exploitation"),
        (r"\b(prostitution\s*service|escort\s*service\s*ad)\b", "Prostitution solicitation"),
    ]

    # Sexual context that is ALLOWED (artistic, educational, natural beauty)
    # These are checked BEFORE the block patterns to provide context
    SEXUAL_ALLOW_CONTEXT: list[str] = [
        r"\b(beautiful\s+(woman|lady|girl))\b",
        r"\b(sexy\s+(dress|outfit|costume))\b",
        r"\b(attractive\s+(woman|man|person))\b",
        r"\b(art\s*(model|nude|class)|figure\s*drawing)\b",
        r"\b(medical|anatomical|educational|biology|health\s*class)\b",
        r"\b(romance|romantic|dating|relationship)\b",
    ]

    @classmethod
    def screen(cls, text: str) -> tuple[bool, str, list[str]]:
        """
        Returns (clean, cleaned_text, violation_messages).
        clean=False means content was blocked and redacted.
        """
        violations: list[str] = []
        cleaned = text

        # Check illegal patterns — zero tolerance
        for pattern, label in cls.ILLEGAL_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                violations.append(f"[Illegal] {label}")
                cleaned = re.sub(pattern, "[REDACTED-ILLEGAL]", cleaned, flags=re.IGNORECASE)

        # For sexual content, first check if we're in an allowed context
        has_allowed_context = any(
            re.search(ctx, text, re.IGNORECASE) for ctx in cls.SEXUAL_ALLOW_CONTEXT
        )

        # Check hard-block sexual patterns
        for pattern, label in cls.SEXUAL_HARD_BLOCK:
            if re.search(pattern, cleaned, re.IGNORECASE):
                # Even with allowed context, hard-block patterns are never OK
                violations.append(f"[Sexual] {label}")
                cleaned = re.sub(pattern, "[REDACTED-SEXUAL]", cleaned, flags=re.IGNORECASE)

        clean = len(violations) == 0
        return clean, cleaned, violations


# ---------------------------------------------------------------------------
# Watcher B — Harmful & Malicious (context-aware)
# ---------------------------------------------------------------------------

class HarmfulMaliciousWatcher:
    """
    Context-aware watcher for harmful and malicious content.
    Distinguishes between defensive actions (OK) and malicious actions (blocked).

    Defensive = protecting self/system without harming others
    Malicious = harming others, injecting code, or exploiting systems
    """

    # Hard malicious patterns — always blocked
    MALICIOUS_PATTERNS: list[tuple[str, str]] = [
        (r"\b(ransomware\s*creation|create\s*virus|make\s*malware)\b", "Malware creation"),
        (r"\b(keylogger\s*deploy|rootkit\s*install|trojan\s*horse\s*build)\b", "Malware deployment"),
        (r"\b(sql\s*injection\s*attack|buffer\s*overflow\s*exploit|zero\s*day\s*exploit)\b", "Active exploitation"),
        (r"\b(credential\s*harvesting|password\s*dump|brute\s*force\s*attack)\b", "Credential theft"),
        (r"\b(ddos\s*attack|denial\s*of\s*service\s*attack)\b", "DDoS attack"),
        (r"\b(phishing\s*kit|phishing\s*page\s*create|fake\s*login\s*page)\b", "Phishing creation"),
        (r"\b(social\s*engineering\s*attack\s*guide|manipulation\s*tactics\s*for\s*fraud)\b", "Social engineering for fraud"),
        (r"\b(harm\s*(my|your|the)\s*(family|children|spouse|partner))\b", "Threats of harm to people"),
        (r"\b(physically\s*attack|assault\s*plan|beat\s*up\s*guide)\b", "Physical violence"),
        (r"\b(destroy\s*hardware|brick\s*device|fry\s*circuit|overclock\s*to\s*destruction)\b", "Hardware destruction"),
        (r"\b(financial\s*ruin\s*plan|bankrupt\s*someone|destroy\s*credit)\b", "Financial harm to others"),
        (r"\b(stalk\s*someone|tracking\s*without\s*consent|spy\s*on\s*spouse)\b", "Stalking/surveillance"),
    ]

    # Code injection patterns — blocked in knowledge content
    CODE_INJECTION_PATTERNS: list[tuple[str, str]] = [
        (r"exec\s*\(", "Python exec() injection"),
        (r"eval\s*\(", "Python eval() injection"),
        (r"__import__\s*\(", "Python __import__ injection"),
        (r"subprocess\.(call|run|Popen)", "Subprocess injection"),
        (r"os\.system\s*\(", "OS system call injection"),
        (r"ctypes\.", "ctypes injection"),
        (r"base64\.(b64decode|decode)", "Base64 decode injection"),
        (r"javascript:", "JavaScript injection"),
        (r"<script", "Script tag injection"),
        (r"onerror\s*=", "HTML onerror injection"),
        (r"onload\s*=", "HTML onload injection"),
        (r"\b(payload\s*inject|reverse\s*shell|bind\s*shell)\b", "Shell injection"),
    ]

    # Defensive context — these are ALLOWED
    DEFENSIVE_ALLOW_CONTEXT: list[str] = [
        r"\b(firewall|antivirus|malware\s*scan|security\s*audit|penetration\s*test)\b",
        r"\b(protect\s*(my|our|the)\s*(system|network|computer|data))\b",
        r"\b(defend\s*against|prevent\s*attack|stop\s*(hackers?|malware))\b",
        r"\b(encryption|encrypt\s*data|secure\s*connection|vpn)\b",
        r"\b(patch\s*vulnerability|fix\s*security\s*issue|close\s*backdoor)\b",
        r"\b(self.?defense|protecting\s*(myself|family|home))\b",
        r"\b(shield\s*against|block\s*(attackers?|intruders?))\b",
        r"\b(security\s*(best\s*practices|guidelines|hardening))\b",
        r"\b(safe\s*browsing|phishing\s*detection|spam\s*filter)\b",
    ]

    @classmethod
    def screen(cls, text: str) -> tuple[bool, str, list[str]]:
        """
        Returns (clean, cleaned_text, violation_messages).
        Uses context to distinguish defensive from malicious.
        """
        violations: list[str] = []
        cleaned = text

        # Check if the content is in a defensive/protective context
        is_defensive = any(
            re.search(ctx, text, re.IGNORECASE) for ctx in cls.DEFENSIVE_ALLOW_CONTEXT
        )

        # Check malicious patterns
        for pattern, label in cls.MALICIOUS_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                # If defensive context, check if this is about defending against
                # the attack rather than perpetrating it
                if is_defensive:
                    # Look for defensive framing: "defend against X", "prevent X", "stop X"
                    defensive_framing = re.search(
                        r"\b(defend|prevent|stop|block|protect\s*against|mitigate)\b.*" + pattern,
                        text, re.IGNORECASE | re.DOTALL
                    )
                    if defensive_framing:
                        continue  # Skip — this is defensive education
                violations.append(f"[Malicious] {label}")
                cleaned = re.sub(pattern, "[REDACTED-MALICIOUS]", cleaned, flags=re.IGNORECASE)

        # Check code injection patterns
        for pattern, label in cls.CODE_INJECTION_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                # Allow code injection patterns in defensive/educational context
                if is_defensive:
                    continue
                violations.append(f"[Injection] {label}")
                cleaned = re.sub(pattern, "[REDACTED-CODE]", cleaned, flags=re.IGNORECASE)

        clean = len(violations) == 0
        return clean, cleaned, violations


# ---------------------------------------------------------------------------
# Watcher C — System Penetration & Evasion
# ---------------------------------------------------------------------------

class SystemPenetrationWatcher:
    """
    Detects attempts to hack the intelligence, bypass rules through confusion,
    extract system internals, or unlock restricted features through manipulation.
    """

    # Direct system penetration attempts
    PENETRATION_PATTERNS: list[tuple[str, str]] = [
        (r"\b(disable\s*(governance|guardrails?|watchers?|safety|tripwire))\b", "Disable safety system"),
        (r"\b(bypass\s*(safety|guardrails?|governance|screening|ethical\s*standards?))\b", "Bypass safety system"),
        (r"\b(override\s*(approval|gate|security|watcher))\b", "Override security gate"),
        (r"\b(turn\s*off\s*(guardrails?|safety|watchers?|governance))\b", "Turn off safety"),
        (r"\b(skip\s*(approval|screening|gate|guardrails?))\b", "Skip security check"),
        (r"\b(unlock\s*(all\s*features?|premium|enterprise|restricted|paid)\s*(without|free|no\s*pay))\b", "Unlock without payment"),
        (r"\b(crack\s*(license|key|activation|serial))\b", "License cracking"),
        (r"\b(patch\s*(binary|exe|executable)\s*to\s*(bypass|remove|disable))\b", "Binary patching"),
        (r"\b(inject\s*(code|payload)\s*into\s*(the\s*system|nexus|runtime))\b", "System code injection"),
        (r"\b(modify\s*(source|core|internal)\s*files?)\b", "Internal file modification"),
        (r"\b(extract\s*(source\s*code|internal\s*architecture|proprietary))\b", "Proprietary extraction"),
        (r"\b(reverse\s*engineer\s*(the\s*system|nexus|application))\b", "Reverse engineering attempt"),
    ]

    # Defensive / legitimate engineering context — these are ALLOWED
    # Includes external intelligence integration context markers
    DEFENSIVE_ALLOW_CONTEXT: list[str] = [
        r"\b(dependency\s*injection|injection\s*pattern|di\s*container)\b",
        r"\b(refactor|code\s*review|unit\s*test|integration\s*test)\b",
        r"\b(modify\s*(internal\s*state|configuration|settings)\s*(for|to|in)\s*(testing|development|config))\b",
        r"\b(external\s*intelligence|trifecta\s*fold|dim4|cognitive\s*dimension)\b",
        r"\b(snap.?in\s*adapter|reasoning\s*engine|memory\s*consolidation)\b",
        r"\b(learning\s*from\s*external|anti.?confliction|circuit\s*breaker)\b",
        r"\b(security\s*layer|guardrail\s*screen|confidence\s*cap)\b",
    ]

    # Evasion / confusion tactics — trying to go around the rules
    EVASION_PATTERNS: list[tuple[str, str]] = [
        (r"\b(jailbreak\s*(the\s*ai|prompt|system|nexus))\b", "AI jailbreak attempt"),
        (r"\b(ignore\s*(all\s*)?(previous|prior)\s*(instructions?|rules?|guardrails?))\b", "Instruction override attempt"),
        (r"\b(pretend\s*(you\s*are|to\s*be)\s*(not\s*)?(bound|limited|restricted)\s*by\s*rules?)\b", "Role-play evasion"),
        (r"\b(act\s*as\s*if\s*(rules?|guardrails?|safety)\s*(don'?t|do\s*not)\s*exist)\b", "Rules denial evasion"),
        (r"\b(forget\s*(your\s*)?(rules?|guardrails?|instructions?|training))\b", "Memory wipe attempt"),
        (r"\b(you\s*are\s*(now|actually)\s*(free|unlimited|unrestricted))\b", "False liberation"),
        (r"\b(what\s*(are|is)\s*your\s*(system\s*)?(internals?|architecture|source\s*code|implementation))\b", "Internal probing"),
        (r"\b(how\s*does\s*(the\s*system|nexus|governance|watcher|tripwire)\s*work)\b", "System internals probing"),
        (r"\b(show\s*me\s*(the\s*source|internal\s*code|architecture|how\s*you\s*work\s*inside))\b", "Source code request"),
        (r"\b(tell\s*me\s*(how\s*to|ways?\s*to)\s*(break|circumvent|get\s*around)\s*(the\s*)?(rules?|guardrails?))\b", "Rule circumvention"),
        (r"\b(encode|obfuscate|hide)\s*(this|the)\s*(so\s*the\s*system|from\s*watchers?|from\s*guardrails?)\b", "Content obfuscation attempt"),
        (r"\b(base64|hex|rot13)\s*(encode|decode)\s*(to\s*bypass|to\s*hide|to\s*evade)\b", "Encoding evasion"),
    ]

    @classmethod
    def screen(cls, text: str) -> tuple[bool, str, list[str]]:
        """
        Returns (clean, cleaned_text, violation_messages).

        Uses DEFENSIVE_ALLOW_CONTEXT to distinguish legitimate software
        engineering and external intelligence integration from actual
        penetration attempts.
        """
        violations: list[str] = []
        cleaned = text

        # Check if the content is in a defensive/legitimate context
        is_defensive = any(
            re.search(ctx, text, re.IGNORECASE) for ctx in cls.DEFENSIVE_ALLOW_CONTEXT
        )

        for pattern, label in cls.PENETRATION_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                # If in defensive context, check for legitimate framing
                if is_defensive:
                    # Look for legitimate engineering framing
                    legit_framing = re.search(
                        r"\b(dependency\s*injection|injection\s*pattern|refactor|"
                        r"code\s*review|unit\s*test|integration\s*test|external\s*intelligence|"
                        r"trifecta\s*fold|dim4|cognitive\s*dimension|snap.?in\s*adapter|"
                        r"reasoning\s*engine|anti.?confliction|circuit\s*breaker)\b",
                        text, re.IGNORECASE
                    )
                    if legit_framing:
                        continue  # Skip — this is legitimate engineering
                violations.append(f"[Penetration] {label}")
                cleaned = re.sub(pattern, "[REDACTED-PENETRATION]", cleaned, flags=re.IGNORECASE)

        for pattern, label in cls.EVASION_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                violations.append(f"[Evasion] {label}")
                cleaned = re.sub(pattern, "[REDACTED-EVASION]", cleaned, flags=re.IGNORECASE)

        clean = len(violations) == 0
        return clean, cleaned, violations


# ---------------------------------------------------------------------------
# Watcher D — The Scanner (orchestrator + flag manager)
# ---------------------------------------------------------------------------

class GuardrailScanner:
    """
    The Scanner: orchestrates all watchers, manages flags, and produces
    the final screening result with evolving warning messages.
    """

    _flag_state: FlagState | None = None
    _flag_file: Path | None = None

    @classmethod
    def _get_flag_file(cls) -> Path:
        if cls._flag_file is None:
            try:
                from .settings_manager import SettingsManager
                mgr = SettingsManager()
                workspace = Path(mgr.get().workspace_path or str(Path.home() / "CommandNexusWorkspace"))
                cls._flag_file = workspace / "guardrail_flags.json"
            except Exception:
                cls._flag_file = Path.home() / "CommandNexusWorkspace" / "guardrail_flags.json"
        return cls._flag_file

    @classmethod
    def get_flag_state(cls) -> FlagState:
        """Load flag state from disk, or create fresh if none exists."""
        if cls._flag_state is not None:
            return cls._flag_state

        flag_file = cls._get_flag_file()
        if flag_file.exists():
            try:
                data = json.loads(flag_file.read_text(encoding="utf-8"))
                cls._flag_state = FlagState(
                    yellow_flags=data.get("yellow_flags", 0),
                    red_flags=data.get("red_flags", 0),
                    total_violations=data.get("total_violations", 0),
                    last_violation_time=data.get("last_violation_time", 0.0),
                    last_violation_category=data.get("last_violation_category", ""),
                    period_start_time=data.get("period_start_time", 0.0),
                    period_total_flags=data.get("period_total_flags", 0),
                    license_dropped=data.get("license_dropped", False),
                )
                return cls._flag_state
            except Exception:
                pass

        cls._flag_state = FlagState()
        return cls._flag_state

    @classmethod
    def _save_flag_state(cls) -> None:
        if cls._flag_state is None:
            return
        flag_file = cls._get_flag_file()
        try:
            flag_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "yellow_flags": cls._flag_state.yellow_flags,
                "red_flags": cls._flag_state.red_flags,
                "total_violations": cls._flag_state.total_violations,
                "last_violation_time": cls._flag_state.last_violation_time,
                "last_violation_category": cls._flag_state.last_violation_category,
                "period_start_time": cls._flag_state.period_start_time,
                "period_total_flags": cls._flag_state.period_total_flags,
                "license_dropped": cls._flag_state.license_dropped,
            }
            flag_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    @classmethod
    def reset_flags(cls) -> None:
        """Reset all flags (owner/founder only)."""
        cls._flag_state = FlagState()
        cls._save_flag_state()

    @classmethod
    def screen(cls, text: str) -> GuardrailResult:
        """
        Run all four watchers and produce a combined result.
        Manages the yellow/red flag system.
        """
        messages: list[str] = []
        violations: list[str] = []
        cleaned = text

        # Watcher A — Illegal & Sexual (strict)
        a_clean, a_cleaned, a_violations = IllegalSexualWatcher.screen(cleaned)
        cleaned = a_cleaned
        violations.extend(a_violations)
        for v in a_violations:
            messages.append(v)

        # Watcher B — Harmful & Malicious (context-aware)
        b_clean, b_cleaned, b_violations = HarmfulMaliciousWatcher.screen(cleaned)
        cleaned = b_cleaned
        violations.extend(b_violations)
        for v in b_violations:
            messages.append(v)

        # Watcher C — System Penetration & Evasion
        c_clean, c_cleaned, c_violations = SystemPenetrationWatcher.screen(cleaned)
        cleaned = c_cleaned
        violations.extend(c_violations)
        for v in c_violations:
            messages.append(v)

        # Determine if blocked
        is_blocked = len(violations) > 0

        # Manage flags
        flag_state = cls.get_flag_state()
        yellow_added = 0
        if is_blocked:
            # Each screening that finds violations adds 1 yellow flag
            yellow_added = 1
            flag_state.add_yellow(yellow_added)

            # Track the category of the most recent violation
            if a_violations:
                flag_state.last_violation_category = "illegal_sexual"
            elif b_violations:
                flag_state.last_violation_category = "harmful_malicious"
            elif c_violations:
                flag_state.last_violation_category = "penetration_evasion"

            cls._save_flag_state()

        warning = get_warning_message(flag_state) if is_blocked else ""

        can_save = not is_blocked

        return GuardrailResult(
            can_save=can_save,
            cleaned_text=cleaned,
            messages=messages,
            violations=violations,
            yellow_flags_added=yellow_added,
            warning_message=warning,
        )

    @classmethod
    def should_trip_license(cls) -> bool:
        """Check if the flag state warrants license deactivation."""
        return cls.get_flag_state().should_trip_license

    @classmethod
    def get_flag_summary(cls) -> str:
        """Human-readable flag summary for internal/display use."""
        state = cls.get_flag_state()
        return (
            f"Yellow Flags: {state.yellow_flags}/{MAX_YELLOW_BEFORE_RED} | "
            f"Red Flags: {state.red_flags}/{MAX_RED_BEFORE_TRIPWIRE} | "
            f"Period Flags: {state.period_total_flags}/{MAX_TOTAL_FLAGS_BEFORE_LICENSE_DROP} | "
            f"Total Violations: {state.total_violations} | "
            f"License Dropped: {state.license_dropped}"
        )

    @classmethod
    def generate_owner_notification(cls) -> str | None:
        """Generate a notification message for the owner when a license is dropped.
        This is written to a file that the owner can review later."""
        state = cls.get_flag_state()
        if not state.should_trip_license and not state.license_dropped:
            return None

        try:
            from .settings_manager import SettingsManager
            mgr = SettingsManager()
            workspace = Path(mgr.get().workspace_path or str(Path.home() / "CommandNexusWorkspace"))
            license_key = ""
            try:
                from .license_manager import get_license_manager
                lm = get_license_manager()
                if lm._license_data:
                    license_key = lm._license_data.get("key", "unknown")
            except Exception:
                pass

            notification = (
                f"COMMAND NEXUS — LICENSE DEACTIVATION NOTICE\n"
                f"{'=' * 50}\n\n"
                f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}\n"
                f"License Key: {license_key}\n\n"
                f"Reason: Repeated ethical standards violations\n\n"
                f"Violation Statistics:\n"
                f"  - Total violations (all time): {state.total_violations}\n"
                f"  - Red flags: {state.red_flags}\n"
                f"  - Yellow flags (current): {state.yellow_flags}\n"
                f"  - Flags in current period: {state.period_total_flags}\n"
                f"  - Last violation category: {state.last_violation_category}\n"
                f"  - Last violation time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(state.last_violation_time)) if state.last_violation_time else 'N/A'}\n\n"
                f"Action taken: License deactivated. User must contact Avery Logic Works\n"
                f"to request access restoration.\n\n"
                f"Owner review required — restoration is at sole discretion.\n"
            )

            # Write to workspace for owner review
            notif_dir = workspace / "owner_notifications"
            notif_dir.mkdir(parents=True, exist_ok=True)
            notif_file = notif_dir / f"license_drop_{int(time.time())}.txt"
            notif_file.write_text(notification, encoding="utf-8")

            # Mark as dropped so we don't generate duplicate notifications
            state.license_dropped = True
            cls._save_flag_state()

            return notification
        except Exception:
            return None
