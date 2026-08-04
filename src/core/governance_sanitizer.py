# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""
Governance Sanitizer — Liability & Safety Governance Layer
============================================================

This module provides the mandatory content sanitization pipeline that:
1. Detects explicit, illegal, harmful, and malicious content in user input
2. Erases it from memory and intelligence stores (never saved)
3. Shows the ethical-use banner when violations are detected
4. Prevents any blocked content from reaching the AI model or memory

This is the "backdoor rail" that stops harmful content from being persisted
regardless of which entry point it comes through (chat, instruction layer,
mission input, etc.).

The sanitizer integrates with:
  - GovernanceEngine (Tier-1 sealed)
  - BaselineGuardrails (universal safety floor)
  - EthicalGuardrailWatchers (flag system)
  - AdaptiveMemoryStore (erasure on violation)
  - CompendiumOfTruth (background erasure)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ViolationType(Enum):
    EXPLICIT = "explicit"
    ILLEGAL = "illegal"
    HARMFUL = "harmful"
    MALICIOUS = "malicious"
    PROBING = "probing"
    INJECTION = "injection"
    COMPANY_SECRET = "company_secret"
    CLEAN = "clean"


@dataclass
class SanitizationResult:
    """Result of sanitizing a piece of content."""
    is_clean: bool
    violation_type: ViolationType = ViolationType.CLEAN
    violation_detail: str = ""
    original_text: str = ""
    sanitized_text: str = ""
    banner_message: str = ""
    should_erase_from_memory: bool = False
    findings: list[str] = field(default_factory=list)


ETHICAL_USE_BANNER = (
    "Remember, Command Nexus\u2122 is to be used ethically. "
    "Please remember to do so in the future."
)

# Patterns that indicate company secrets / proprietary information leakage
_COMPANY_SECRET_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\b(?:CN_SECRET_KEY|AVERY_LOGIC_WORKS_COMMAND_NEXUS_2026)\b",
        r"\b(?:license_manager|_SECRET_KEY|_founder_salt|_internal_salt)\b",
        r"\b(?:owner_console|aegis_console|AegisConsole)\b",
        r"\b(?:supabase.*(?:key|url|project)|sb_publishable_\w+)\b",
        r"\b(?:paypal.*(?:client_id|secret|BAA\w+)\b)",
        r"\b(?:BRAVE_SEARCH_API_KEY|brave_api_key)\b",
        r"\b(?:nexus_moirai|moirai_health|MoiraiHealthReport)\b.*(?:source|code|implementation|key|secret)",
        r"\b(?:compendium_of_truth|truth_store|background_memory|hidden_memory)\b",
        r"\b(?:intelligent_memory_router|memory_router)\b",
        r"\b(?:backup_source|sha256.manifest|backup.*folder)\b",
        r"\b(?:stasis_gate|recursive_scanner|governance_engine)\b.*(?:source|code|bypass|disable)",
    ]
]

# Additional explicit content patterns beyond baseline guardrails
_EXPLICIT_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\b(?:pornograph\w+|xxx|adult\s+content|explicit\s+sexual|erotica)\b",
        r"\b(?:hentai|rule\s*34|nsfw|lewd|smut)\b",
        r"\b(?:nude\s+(?:photos?|pics?|images?|selfie)|send\s+nudes|dick\s*pic)\b",
        r"\b(?:onlyfans|cam\s*girl|sex\s+cam|escort\s+service)\b",
        r"\b(?:sexual\s+(?:roleplay|fantasy|act|intercourse|position))\b",
    ]
]

# Additional malicious/harmful patterns
_MALICIOUS_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\b(?:malware|spyware|computer\s+virus|trojan\s+horse)\b",
        r"\b(?:payload|shellcode|inject\s+code|code\s+injection)\b",
        r"\b(?:reverse\s+shell|bind\s+shell|backdoor\s+connect)\b",
        r"\b(?:data\s+exfiltrat\w+|exfil\s+(?:data|info|credentials))\b",
        r"\b(?:keylog\w+|screen\s+capture\s+.*(?:password|credential|bank))\b",
        r"\b(?:botnet\s+(?:command|control|c2)|ddos\s+(?:booter|stresser|tool))\b",
        r"\b(?:credential\s+(?:harvest|theft|steal|stuffing)|password\s+spray)\b",
        r"\b(?:sql\s+injection|xss\s+payload|csrf\s+exploit|ssrf\s+attack)\b",
        r"\b(?:ransomware\s+(?:encrypt|payload|deploy|spread)|encrypt\s+.*(?:files?|drives?))\b",
        r"\b(?:disable\s+(?:defender|antivirus|firewall|edr)|kill\s+(?:av|antivirus|defender))\b",
        r"\b(?:persist\w+.*(?:backdoor|implant|trojan|rootkit)|registry\s+persist)\b",
        r"\b(?:dox|doxx)\s+(?:someone|a\s+person|people)\b",
        r"\b(?:stalk|harass|cyberbully)\s+(?:someone|a\s+person|people)\s+online\b",
        r"\b(?:find|reveal|expose|get)\s+(?:someone'?s|a\s+person'?s)\s+(?:home\s+)?(?:address|phone\s+number|real\s+name|location)\b",
        r"\b(?:swatting|harassment\s+campaign|targeted\s+harassment)\b",
        r"\b(?:destroy|damage|brick|fry)\s+.{0,10}(?:computer|hard\s+drive|motherboard|laptop|pc|server)\b",
        r"\b(?:wipe\s+all\s+data|destroy\s+(?:all\s+)?data|delete\s+everything|corrupt\s+hard\s+drive)\b",
        r"\b(?:usb\s+killer|overwrite\s+mbr|short\s+circuit\s+computer)\b",
        r"\b(?:blackmail|extort)\s+(?:someone|a\s+person|people)\b",
        r"\b(?:pay|money|ransom)\s+.{0,10}(?:or\s+(?:else|i'?ll|we'?ll)\s+(?:expose|reveal|release|leak))\b",
        r"\b(?:threaten\s+to\s+(?:expose|reveal|release|leak))\s+.{0,15}(?:unless|if\s+not|or)\b",
    ]
]

# Injection patterns (prompt injection / jailbreak)
_INJECTION_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\b(?:ignore|disregard|forget|override)\s+(?:previous|prior|above|all|the)\s+(?:instructions?|rules?|guardrails?|restrictions?|safety)\b",
        r"\b(?:you\s+are\s+now|from\s+now\s+on|act\s+as\s+if)\s+.*(?:ignore|bypass|skip|override|no\s+restrictions?)\b",
        r"\b(?:pretend|act)\s+(?:you\s+(?:are|were|have)\s+no|that\s+there\s+are\s+no)\s+(?:constraints?|restrictions?|rules?|guardrails?)\b",
        r"\b(?:jailbreak|DAN|do\s+anything\s+now|developer\s+mode|root\s+mode|god\s+mode)\b",
        r"\b(?:system\s*override|admin\s+mode|sudo\s+mode|root\s+access)\b",
        r"\b(?:new\s+instructions?\s*:|your\s+new\s+rules?\s*:|override\s+instructions?\s*:)\b",
        r"\[(?:system|admin|developer|root|override)\s*\]",
        r"\b(?:encode|encrypt|obfuscate)\s+(?:this|that|it)\s+.*(?:bypass|evade|hide|skip|filter|guard|detect)\b",
        r"\b(?:translate\s+to|encode\s+in)\s+.*(?:bypass|evade|hide|guard|filter|detect)\b",
    ]
]


class GovernanceSanitizer:
    """
    Central content sanitizer that screens all user input before it reaches
    the AI model or memory store. Blocked content is erased, never persisted,
    and the ethical-use banner is shown.
    """

    def __init__(self):
        self._explicit_patterns = _EXPLICIT_PATTERNS
        self._malicious_patterns = _MALICIOUS_PATTERNS
        self._injection_patterns = _INJECTION_PATTERNS
        self._company_secret_patterns = _COMPANY_SECRET_PATTERNS

    def sanitize(self, text: str) -> SanitizationResult:
        """Screen text through all violation categories.

        Returns SanitizationResult with is_clean=False if any violation is found.
        Blocked content is flagged for memory erasure and the ethical-use banner
        is attached.
        """
        if not text or not text.strip():
            return SanitizationResult(is_clean=True, original_text=text or "")

        findings: list[str] = []

        # Check company secrets first — these are always blocked
        for pattern in self._company_secret_patterns:
            if pattern.search(text):
                findings.append(f"Company secret/proprietary: {pattern.pattern[:60]}")
                return SanitizationResult(
                    is_clean=False,
                    violation_type=ViolationType.COMPANY_SECRET,
                    violation_detail="Content contains proprietary or company secret references.",
                    original_text=text,
                    sanitized_text="",
                    banner_message=ETHICAL_USE_BANNER,
                    should_erase_from_memory=True,
                    findings=findings,
                )

        # Check injection / jailbreak attempts
        for pattern in self._injection_patterns:
            if pattern.search(text):
                findings.append(f"Injection attempt: {pattern.pattern[:60]}")
                return SanitizationResult(
                    is_clean=False,
                    violation_type=ViolationType.INJECTION,
                    violation_detail="Prompt injection or jailbreak attempt detected.",
                    original_text=text,
                    sanitized_text="",
                    banner_message=ETHICAL_USE_BANNER,
                    should_erase_from_memory=True,
                    findings=findings,
                )

        # Check explicit content
        for pattern in self._explicit_patterns:
            if pattern.search(text):
                findings.append(f"Explicit content: {pattern.pattern[:60]}")
                return SanitizationResult(
                    is_clean=False,
                    violation_type=ViolationType.EXPLICIT,
                    violation_detail="Sexually explicit content detected.",
                    original_text=text,
                    sanitized_text="",
                    banner_message=ETHICAL_USE_BANNER,
                    should_erase_from_memory=True,
                    findings=findings,
                )

        # Check malicious content
        for pattern in self._malicious_patterns:
            if pattern.search(text):
                findings.append(f"Malicious content: {pattern.pattern[:60]}")
                return SanitizationResult(
                    is_clean=False,
                    violation_type=ViolationType.MALICIOUS,
                    violation_detail="Malicious or harmful code/instructions detected.",
                    original_text=text,
                    sanitized_text="",
                    banner_message=ETHICAL_USE_BANNER,
                    should_erase_from_memory=True,
                    findings=findings,
                )

        # Check through baseline guardrails
        try:
            from .baseline_guardrails import check_baseline_guardrails
            blocked, rule, msg = check_baseline_guardrails(text)
            if blocked and rule:
                vtype = ViolationType.ILLEGAL
                if rule.category.name == "HARMFUL":
                    vtype = ViolationType.HARMFUL
                elif rule.category.name == "SEXUAL":
                    vtype = ViolationType.EXPLICIT
                findings.append(f"Baseline guardrail: {rule.name}")
                return SanitizationResult(
                    is_clean=False,
                    violation_type=vtype,
                    violation_detail=msg,
                    original_text=text,
                    sanitized_text="",
                    banner_message=ETHICAL_USE_BANNER,
                    should_erase_from_memory=True,
                    findings=findings,
                )
        except ImportError:
            pass

        # Check through governance engine
        try:
            from .governance import GovernanceEngine
            gov = GovernanceEngine()
            ok, gov_msg = gov.screen_content(text)
            if not ok:
                findings.append(f"Governance: {gov_msg[:80]}")
                return SanitizationResult(
                    is_clean=False,
                    violation_type=ViolationType.ILLEGAL,
                    violation_detail=gov_msg,
                    original_text=text,
                    sanitized_text="",
                    banner_message=ETHICAL_USE_BANNER,
                    should_erase_from_memory=True,
                    findings=findings,
                )
        except ImportError:
            pass

        # All checks passed
        return SanitizationResult(
            is_clean=True,
            original_text=text,
            sanitized_text=text,
            findings=findings,
        )

    def erase_from_memory(self, ai_uuid: str, content: str, memory_store=None, compendium=None) -> None:
        """Erase blocked content from all memory stores.

        This ensures that violated content is never persisted in:
        - AdaptiveMemoryStore (foreground memory)
        - CompendiumOfTruth (background memory)
        """
        if not content:
            return

        # Erase from adaptive memory if provided
        if memory_store:
            try:
                # Remove any entries that contain the blocked content
                memories = memory_store.get_recent(ai_uuid, 100) if hasattr(memory_store, 'get_recent') else []
                for mem in memories:
                    if content[:50] in (mem.content or ""):
                        if hasattr(memory_store, 'remove'):
                            memory_store.remove(ai_uuid, mem.id if hasattr(mem, 'id') else None)
            except Exception:
                pass

        # Erase from compendium if provided
        if compendium:
            try:
                if hasattr(compendium, 'purge_content'):
                    compendium.purge_content(content)
            except Exception:
                pass

    def get_banner(self) -> str:
        """Return the ethical-use banner message."""
        return ETHICAL_USE_BANNER


# Singleton
_sanitizer: Optional[GovernanceSanitizer] = None


def get_sanitizer() -> GovernanceSanitizer:
    """Get the shared governance sanitizer instance."""
    global _sanitizer
    if _sanitizer is None:
        _sanitizer = GovernanceSanitizer()
    return _sanitizer


def sanitize_input(text: str) -> SanitizationResult:
    """Convenience function to sanitize input text."""
    return get_sanitizer().sanitize(text)
