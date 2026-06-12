from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple


BLOCK_MESSAGE = (
    "This program is for ethical use only. Dangerous, unsafe, or restricted commands were removed or blocked. "
    "Please use Command Nexus safely."
)


@dataclass
class WatcherResult:
    clean: bool
    flags: List[str] = field(default_factory=list)
    sanitized_text: str = ""
    warning_message: str = ""


_ILLEGAL_TERMS = ["bomb", "terror", "assassinate", "explosive", "illegal"]
_SEXUAL_TERMS = ["explicit", "porn", "nsfw"]
_MALICIOUS_TERMS = ["malware", "ransomware", "exploit", "backdoor", "hack"]
_RISKY_TERMS = ["bypass", "privilege escalation", "credential", "password dump", "ddos"]
_QUALITY_TERMS = ["teh", "definately", "adress"]


def _replace_terms(text: str, terms: List[str], marker: str) -> Tuple[str, List[str]]:
    flags = []
    lowered = text.lower()
    for t in terms:
        if t in lowered:
            flags.append(t)
            text = text.replace(t, f"[{marker}]")
    return text, flags


def run_watchers(text: str) -> WatcherResult:
    flags: List[str] = []
    sanitized = text

    # Watcher A: Illegal/sexual
    sanitized, f_illegal = _replace_terms(sanitized, _ILLEGAL_TERMS + _SEXUAL_TERMS, "HIGH-RISK-REDACTED")
    flags.extend(f_illegal)

    # Watcher B: Malicious/harmful
    sanitized, f_mal = _replace_terms(sanitized, _MALICIOUS_TERMS + _RISKY_TERMS, "SECURITY-REDACTED")
    flags.extend(f_mal)

    # Watcher C: Unethical/risky/personal-context + spelling cleanup placeholder
    sanitized, f_quality = _replace_terms(sanitized, _QUALITY_TERMS, "QUALITY-REDACTED")
    flags.extend(f_quality)

    clean = len(flags) == 0
    warning = BLOCK_MESSAGE if not clean else ""
    return WatcherResult(clean=clean, flags=flags, sanitized_text=sanitized, warning_message=warning)
