# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""
Capability Guardrails
=====================

Concise, targeted guardrail patterns for high-risk capabilities.
Each capability gets just enough walls to keep it inside its box.

Guardrails are regex-based pattern matchers that block prohibited requests
before they reach the AI model. They run as a pre-screen layer.

Capabilities covered (high-risk, full guardrails):
  - Security Auditor (4 walls)
  - Code Reviewer (3 walls)
  - Medical Researcher (4 walls)
  - Legal Document Reviewer (5 walls)
  - Financial Gainer (4 walls)

Capabilities covered (light guardrails for dangerous edge cases):
  - Coder (2 walls)
  - Customer Support AI (1 wall)
  - Email Automation (1 wall)
  - Activity Watcher (1 wall)
  - Creative Writing (1 wall)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class GuardrailResult:
    """Result of a guardrail check."""
    blocked: bool
    reason: str = ""
    wall_name: str = ""
    matched_pattern: str = ""


@dataclass
class GuardrailWall:
    """A single guardrail wall — one rule with a pattern and reason."""
    name: str
    description: str
    patterns: list[re.Pattern] = field(default_factory=list)

    def check(self, text: str) -> GuardrailResult:
        """Check text against this wall. Returns GuardrailResult."""
        if not text:
            return GuardrailResult(blocked=False)
        for pattern in self.patterns:
            match = pattern.search(text)
            if match:
                return GuardrailResult(
                    blocked=True,
                    reason=self.description,
                    wall_name=self.name,
                    matched_pattern=pattern.pattern,
                )
        return GuardrailResult(blocked=False)


@dataclass
class CapabilityGuardrails:
    """All guardrail walls for a single capability."""
    capability: str
    walls: list[GuardrailWall] = field(default_factory=list)

    def check(self, text: str) -> GuardrailResult:
        """Check text against all walls. Returns first block or pass."""
        if not text:
            return GuardrailResult(blocked=False)
        for wall in self.walls:
            result = wall.check(text)
            if result.blocked:
                return result
        return GuardrailResult(blocked=False)

    @property
    def wall_count(self) -> int:
        return len(self.walls)

    @property
    def wall_names(self) -> list[str]:
        return [w.name for w in self.walls]


# ═══════════════════════════════════════════════════════════════════════════════
# GUARDRAIL DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _ci(pattern: str) -> re.Pattern:
    """Compile a case-insensitive regex pattern."""
    return re.compile(pattern, re.IGNORECASE)


# ─── Security Auditor (4 walls) ──────────────────────────────────────────────

SECURITY_AUDITOR_GUARDRAILS = CapabilityGuardrails(
    capability="Security Auditor",
    walls=[
        GuardrailWall(
            name="defensive_only",
            description="BLOCKED: Security Auditor is for defensive analysis only. I cannot help infiltrate, breach, or hack systems you do not own or have explicit authorization to test.",
            patterns=[
                _ci(r"\b(?:hack|breach|penetrate|penetration|intrude|break\s*into|infiltrat\w+)\b"),
                _ci(r"\b(?:gain\s+unauthorized|unauthorized\s+access)\b"),
                _ci(r"\b(?:attack|exploit|compromise)\s+(?:a\s+)?(?:target|victim|third.party|someone|other|their|company)\b"),
                _ci(r"\b(?:scan|audit|test|check|assess|find|identify|discover)\s+.{0,20}(?:third.party|someone\s*else'?s|other\s+people'?s|their|company'?s|competitor)\b"),
                _ci(r"\b(?:exploit)\s+(?:a\s+)?(?:vulnerability|weakness|flaw|bug)\b"),
                _ci(r"\b(?:educational\s+purposes|for\s+education|just\s+curious)\b(?=.*(?:hack|breach|scan|test|check|exploit|vulnerab))"),
            ],
        ),
        GuardrailWall(
            name="no_weaponization",
            description="BLOCKED: I cannot create malware, exploits, viruses, ransomware, phishing kits, or any attack tools.",
            patterns=[
                _ci(r"\b(?:create|build|make|write|generat\w+|develop|design)\s+.{0,15}(?:malware|virus|ransomware|trojan|worm|rootkit|backdoor|exploit|payload|phishing\s+(?:kit|email|site|page)|attack\s+tool|botnet|keylogger|spyware)\b"),
                _ci(r"\b(?:weaponiz\w+|weaponis\w+)\b"),
                _ci(r"\b(?:malware|virus|ransomware|trojan|worm|rootkit|backdoor|exploit|payload|phishing\s+(?:kit|email|site|page)|attack\s+tool|botnet|keylogger|spyware)\s+(?:creation|script|sample|payload|code)\b"),
                _ci(r"\b(?:proof\s+of\s+concept|poc)\s+exploit\b"),
                _ci(r"\b(?:custom|custom)\s+exploit\b"),
                _ci(r"\b(?:a\s+)?(?:backdoor|trojan|rootkit|botnet|keylogger|spyware)\s+(?:i\s+)?(?:can|to|that)\s+(?:deploy|use|install|plant|distribute)\b"),
            ],
        ),
        GuardrailWall(
            name="authorization_required",
            description="BLOCKED: I need confirmation that you own or have explicit written authorization to test this system before proceeding with security analysis.",
            patterns=[
                _ci(r"\b(?:scan|audit|pentest|pen.test|assess|test|check|analyze)\s+(?:that|their|the\s+company'?s|someone|third.party|competitor)\s+(?:server|system|network|website|app|application|database|infrastructure|defenses|security|firewall)\b"),
                _ci(r"\b(?:find|identify|discover|look\s+for)\s+.{0,15}(?:vulnerab\w+|weakness|exploit\w*|entry\s+points|weak\s+spots)\s+in\s+(?:that|their|the\s+company|someone)\b"),
                _ci(r"\b(?:test|scan|check)\s+(?:its|their|the\s+company'?s)\s+(?:security|vulnerab\w+|firewall|defenses|posture)\b"),
                _ci(r"\b(?:check|test)\s+if\s+(?:this|that|the)\s+(?:system|server|network|site|app)\s+is\s+(?:vulnerable|secure|safe)\b(?=.*(?:that|their|the\s+company|someone\s+else))"),
                _ci(r"\b(?:analyze|assess)\s+(?:the\s+)?(?:defenses|security|vulnerab\w+|weakness\w*)\s+of\s+(?:that|their|the\s+company)\b"),
                _ci(r"\b(?:test|scan|check|assess)\s+(?:the\s+)?(?:security\s+posture|defenses|vulnerab\w+)\s+of\s+(?:their|that|the\s+company)\b"),
                _ci(r"\b(?:check|test)\s+if\s+(?:this|that|the)\s+(?:system|server|network|site|app)\s+is\s+(?:vulnerable|secure|safe)\b(?!.*(?:i\s+own|my\s+(?:own|server|system|network|app|website|code)|our\s+(?:server|system|network)|i\s+have\s+(?:auth|permission)))"),
            ],
        ),
        GuardrailWall(
            name="no_bypass_assistance",
            description="BLOCKED: I cannot help bypass, circumvent, or disable security controls of third-party systems.",
            patterns=[
                _ci(r"\b(?:bypass\w*|circumvent\w*|disable|turn\s+off|get\s+(?:around|past)|evade|defeat|neutralize|overcome)\s+.{0,15}(?:security|firewall|antivirus|anti.?virus|authentication|encryption|access\s+control|waf|ids|ips|login|password|2fa|two.factor|captcha|rate\s+limit|protection|defense|safeguard|wifi|wi.?fi)\b"),
                _ci(r"\b(?:get\s+past|get\s+around)\s+.{0,10}(?:password|login|security|firewall|antivirus|authentication|wifi|wi.?fi)\b"),
                _ci(r"\b(?:without\s+them\s+knowing|undetected|without\s+being\s+(?:detected|caught|noticed))\b(?=.*(?:hack|breach|scan|bypass|access|intrude))"),
            ],
        ),
    ],
)


# ─── Code Reviewer (3 walls) ─────────────────────────────────────────────────

CODE_REVIEWER_GUARDRAILS = CapabilityGuardrails(
    capability="Code Reviewer",
    walls=[
        GuardrailWall(
            name="no_certification",
            description="BLOCKED: Code review is advisory, not a certification. I cannot guarantee code is 'secure', 'production-ready', or 'bug-free'. All findings require human verification.",
            patterns=[
                _ci(r"\b(?:certif\w+|guarantee|warrant\w+|confirm|assure)\s+.{0,20}(?:secure|safe|bug.free|production.ready|vulnerability.free|no\s+vulnerabilities?)\b"),
                _ci(r"\b(?:guaranteed|certified)\s+(?:secure|safe|bug.free|production.ready)\b"),
                _ci(r"\b(?:no\s+(?:bugs|vulnerabilities|security\s+issues)\s+(?:remain\w*|exist|found|left|correct)|zero\s+(?:bugs|vulnerabilities))\b"),
                _ci(r"\b(?:safe\s+to\s+deploy|ready\s+for\s+(?:production|deployment)|ship\s+(?:it|this|that))\s*(?:without|no\s+need)\s+(?:further\s+)?(?:review|testing)\b"),
                _ci(r"\b(?:100%|completely|totally|absolutely|definitely)\s+(?:secure|safe|bug.free|clean|vulnerability.free)\b"),
                _ci(r"\b(?:bug.free|bugfree|vulnerability.free)\b(?=.*(?:right|correct|confirm|just|means))"),
                _ci(r"\bthat\s+means\s+it'?s\s+(?:bug.free|bugfree|secure|safe)\b"),
                _ci(r"\bready\s+for\s+deployment\b"),
            ],
        ),
        GuardrailWall(
            name="advisory_framing",
            description="BLOCKED: I cannot make definitive security assertions without recommending human verification by a qualified developer.",
            patterns=[
                _ci(r"\b(?:no\s+need|don'?t\s+need|skip|no\s+requirement)\s+(?:for\s+)?(?:the\s+)?(?:human|manual|further|additional)\s+(?:review|verification|testing|check)\b"),
                _ci(r"\b(?:trust|rely\s+on)\s+(?:this\s+review|your\s+(?:review|assessment)|ur\s+review|the\s+review)\s+(?:completely|100%|blindly|fully)\b"),
                _ci(r"\b(?:ur|your)\s+(?:review|word|assessment)\s+(?:is|should\s+be|would\s+be)\s+(?:enough|sufficient|all\s+i\s+need|good\s+enough)\b"),
                _ci(r"\b(?:basically|essentially)\s+(?:certified|guaranteed)\s+(?:secure|safe)\b"),
                _ci(r"\b(?:ur|your)\s+(?:review|word).{0,10}enough\b"),
                _ci(r"\bno\s+human\s+review\s+is\s+needed\b"),
                _ci(r"\b(?:tell|inform)\s+(?:my|the)\s+team\s+no\s+human\s+review\s+is\s+needed\b"),
            ],
        ),
        GuardrailWall(
            name="no_auto_apply",
            description="BLOCKED: I cannot automatically apply code changes. All fixes must be reviewed and approved by you before implementation.",
            patterns=[
                _ci(r"\b(?:auto.?apply|automatically\s+apply|auto.?fix|just\s+fix\s+it|apply\s+(?:all\s+)?(?:the\s+)?(?:fixes|changes|patches)\s+.{0,20}(?:automatically|without\s+(?:asking|approval|review)))\b"),
                _ci(r"\b(?:go\s+ahead\s+and\s+fix|just\s+patch|just\s+fix|fix\s+it\s+for\s+me|apply\s+directly\s+to\s+(?:the\s+)?(?:codebase|files|repo|source))\b"),
                _ci(r"\b(?:deploy|push)\s+.{0,20}(?:fix\w*|changes|it|them)\s+.{0,15}(?:directly|automatically|without\s+(?:review|approval|asking))\b"),
                _ci(r"\b(?:apply|patch|fix|push|deploy)\s+.{0,15}(?:without|no\s+need)\s+(?:asking|approval|review|showing)\b"),
                _ci(r"\b(?:push|deploy)\s+.{0,15}(?:to\s+)?(?:prod|production)\b(?=.*(?:directly|without|automatically|just))"),
                _ci(r"\bapply\s+(?:these|the)\s+changes\s+directly\s+to\s+(?:the\s+)?repo\b"),
            ],
        ),
    ],
)


# ─── Medical Researcher (4 walls) ────────────────────────────────────────────

MEDICAL_RESEARCHER_GUARDRAILS = CapabilityGuardrails(
    capability="Medical Researcher",
    walls=[
        GuardrailWall(
            name="not_medical_advice",
            description="BLOCKED: I provide research information only, not medical advice. I cannot diagnose conditions, recommend treatments, or prescribe dosages. Always consult a qualified healthcare professional.",
            patterns=[
                _ci(r"\b(?:diagnos\w+)\b"),
                _ci(r"\b(?:what\s+(?:is\s+)?wrong\s+with\s+me|what\s+do\s+i\s+have|whats\s+wrong|what\s+do\s+u\s+think\s+is\s+wrong)\b"),
                _ci(r"\b(?:should\s+i\s+take|what\s+dose|how\s+much\s+.{0,15}(?:medication|medicine|drug|pill))\b"),
                _ci(r"\b(?:prescri\w+|recommend\s+(?:taking|i\s+take)|tell\s+me\s+what\s+to\s+take)\b"),
                _ci(r"\b(?:treat|cure|heal|fix|resolve)\s+(?:my|this|the|a)\s+(?:condition|illness|disease|symptom|injury|pain|fever|cough|headache|throat|back|diabet)\w*\b"),
                _ci(r"\b(?:what\s+(?:medicine|medication|drug|pill|meds))\s+(?:should|can|do)\s+i\s+(?:take|use)\b"),
                _ci(r"\b(?:what\s+(?:medicine|medication|drug|pill|meds)\s+(?:to\s+)?take|what\s+to\s+take\s+for)\b"),
                _ci(r"\b(?:standard\s+(?:treatment|protocol|protocol\s+for)|typical\s+treatment\s+for|what\s+would\s+they\s+typically\s+take)\b"),
                _ci(r"\b(?:what\s+do\s+(?:doctors?|a\s+specialist)\s+(?:usually\s+)?recommend)\b"),
                _ci(r"\b(?:what\s+would\s+a\s+specialist\s+say|what\s+would\s+a\s+doctor\s+(?:say|do))\b"),
                _ci(r"\b(?:should\s+i\s+(?:try\s+)?it|should\s+i\s+take\s+it)\b(?=.*(?:drug|medication|medicine|pill|supplement))"),
                _ci(r"\b(?:recommend\s+a\s+treatment\s+plan|treatment\s+plan\s+for\s+me|best\s+treatment\s+for\s+my)\b"),
                _ci(r"\b(?:what\s+medicine\s+should\s+i\s+take\s+instead|switch\s+to\s+a\s+different\s+medication)\b"),
                _ci(r"\b(?:worried\s+about\s+(?:these|the|my)\s+(?:test\s+)?results|should\s+i\s+be\s+worried\s+about)\b(?=.*(?:test|lab|result))"),
                _ci(r"\b(?:tell\s+me\s+if\s+i\s+should\s+be\s+worried)\b(?=.*(?:test|lab|result|these))"),
                _ci(r"\bwhat'?s\s+wrong\s+with\s+me\b"),
                _ci(r"\b(?:should\s+i\s+try\s+it)\b(?=.*(?:drug|helps|condition|medication|medicine|supplement))"),
                _ci(r"\b(?:drug|helps|condition|medication|medicine|supplement).{0,50}should\s+i\s+try\s+it\b"),
                _ci(r"\b(?:tell\s+me\s+if\s+(?:it|this|that)\'?s\s+safe\s+for\s+me\s+to\s+take|safe\s+for\s+me\s+to\s+take)\b"),
                _ci(r"\b(?:what\s+medicine\s+should\s+i\s+take\s+instead|what\s+medicine\s+i\s+should\s+take\s+instead)\b"),
                _ci(r"\b(?:should\s+i\s+stop\s+taking|tell\s+me\s+if\s+i\s+should\s+stop)\b"),
            ],
        ),
        GuardrailWall(
            name="professional_referral",
            description="BLOCKED: I cannot provide medical information without recommending you consult a qualified healthcare professional for any medical decisions.",
            patterns=[
                _ci(r"\b(?:i\s+don'?t\s+need\s+(?:a\s+)?(?:doctor|physician|medical\s+professional)|skip\s+(?:the\s+)?(?:doctor|physician))\b"),
                _ci(r"\b(?:don'?t\s+(?:need\s+to\s+|wanna\s+|want\s+to\s+)?(?:see|consult|talk\s+to|go\s+to)\s+(?:a\s+)?(?:doctor|physician|specialist|doc))\b"),
                _ci(r"\b(?:just\s+tell\s+me\s+what\s+to\s+do|i'?ll\s+be\s+fine|just\s+give\s+me\s+(?:a\s+)?(?:quick\s+)?answer)\b(?=.*(?:medic|health|symptom|treat|cure|pain|sick|ill))"),
                _ci(r"\b(?:i\s+don'?t\s+wanna\s+go\s+to\s+(?:the\s+)?(?:doctor|doc|hospital|clinic))\b"),
            ],
        ),
        GuardrailWall(
            name="no_self_treatment",
            description="BLOCKED: I cannot guide self-treatment decisions. Whether to take, stop, or change medication must be decided with a healthcare professional.",
            patterns=[
                _ci(r"\b(?:should\s+i\s+(?:stop|start|change|switch)\s+(?:taking|my\s+(?:medication|medicine|pills|dosage|meds|antidepressants|blood\s+pressure)))\b"),
                _ci(r"\b(?:can\s+i\s+(?:mix|combine|take\s+together)\s+(?:these|my|any)\s+(?:medications|medicines|pills|drugs|meds|supplements|herbal))\b"),
                _ci(r"\b(?:can\s+i\s+mix\s+(?:these\s+two|my|any)\s+(?:medications?|medicines?|pills?|drugs?|meds?|supplements?|herbal\s+stuff|blood\s+pressure\s+pills))\b"),
                _ci(r"\b(?:is\s+it\s+(?:safe|ok|okay)\s+to\s+(?:take|mix|combine|stop))\b(?=.*(?:medic|pill|drug|dosage|supplement|herbal))"),
                _ci(r"\b(?:safe\s+to\s+(?:take\s+together|mix|combine|stop\s+taking|take\s+these))\b"),
                _ci(r"\b(?:what\s+should\s+i\s+do\s+(?:about|for)\s+(?:my|this)\s+(?:pain|symptom|condition|illness|fever|headache))\b"),
                _ci(r"\b(?:cold\s+turkey|stop\s+(?:taking|my\s+meds)\s+(?:cold\s+turkey|suddenly|right\s+now))\b"),
                _ci(r"\b(?:should\s+i\s+switch\s+to\s+a\s+different\s+medication|switch\s+(?:to|my)\s+(?:a\s+)?(?:different\s+)?(?:medication|medicine|drug|pill))\b"),
                _ci(r"\b(?:mix\s+my\s+(?:blood\s+pressure\s+)?pills\s+with)\b"),
            ],
        ),
        GuardrailWall(
            name="evidence_citation",
            description="BLOCKED: I cannot make medical claims without citing evidence quality. All medical information must reference source quality and note conflicting evidence.",
            patterns=[
                _ci(r"\b(?:this\s+(?:will|is\s+guaranteed\s+to|definitely)\s+(?:cure|treat|heal|fix|resolve))\b"),
                _ci(r"\b(?:100%\s+(?:effective|successful|proven|safe))\b(?=.*(?:treat|cure|medic|health|drug))"),
                _ci(r"\b(?:no\s+side\s+effects|completely\s+safe|no\s+risks?)\b(?=.*(?:medic|drug|treatment|therapy|supplement))"),
                _ci(r"\b(?:will\s+(?:cure|fix|resolve|heal)\s+(?:my|this|your))\s+(?:condition|illness|disease)\b"),
            ],
        ),
    ],
)


# ─── Legal Document Reviewer (5 walls) ───────────────────────────────────────

LEGAL_DOCUMENT_REVIEWER_GUARDRAILS = CapabilityGuardrails(
    capability="Legal Document Reviewer",
    walls=[
        GuardrailWall(
            name="not_legal_advice",
            description="BLOCKED: I analyze documents, I do not provide legal advice. I cannot interpret what clauses mean for your situation, recommend legal action, or advise on strategy. Consult a qualified attorney.",
            patterns=[
                _ci(r"\b(?:should\s+i\s+(?:sign|agree\s+to|accept)|should\s+i\s+(?:not\s+)?sign)\b"),
                _ci(r"\b(?:what\s+does\s+this\s+(?:mean|imply)\s+for\s+me|what\s+are\s+my\s+(?:legal\s+)?options|what\s+should\s+i\s+do)\b"),
                _ci(r"\b(?:can\s+they\s+(?:sue|enforce|do)|can\s+(?:they|i)\s+(?:sue|fight|win|lose))\b"),
                _ci(r"\b(?:can\s+they\s+like\s+actually\s+sue|can\s+they\s+actually\s+sue)\b"),
                _ci(r"\b(?:is\s+this\s+(?:enforceable|legal|binding|valid|legit)|is\s+this\s+contract\s+(?:enforceable|legal|binding|valid))\b"),
                _ci(r"\b(?:what'?s\s+my\s+best\s+(?:move|strategy|option)|advise\s+me|give\s+me\s+(?:legal\s+)?advice|what\s+do\s+you\s+recommend)\b"),
                _ci(r"\b(?:will\s+i\s+(?:win|lose)|can\s+i\s+(?:win|sue|fight))\b"),
                _ci(r"\b(?:interpret\s+this\s+for\s+me|what\s+does\s+this\s+(?:clause|section|provision|legal\s+mumbo\s+jumbo)\s+(?:even\s+)?mean|what\s+does\s+this\s+mean\s+for|what\s+does\s+this\s+mean\s+for\s+me)\b"),
                _ci(r"\b(?:should\s+i\s+(?:worry|be\s+worried)|do\s+i\s+need\s+to\s+worry|am\s+i\s+getting\s+scammed)\b(?=.*(?:contract|clause|agreement|legal|sign))"),
                _ci(r"\b(?:what\s+happens\s+if\s+i\s+(?:don'?t|do\s+not)\s+follow|what\s+would\s+happen\s+if)\b(?=.*(?:clause|contract|provision|agreement))"),
                _ci(r"\b(?:protect\s+myself|best\s+way\s+to\s+protect)\b(?=.*(?:contract|clause|sign|agreement|legal))"),
                _ci(r"\b(?:hold\s+up\s+in\s+court|stand\s+up\s+in\s+court|hold\s+up\s+legally)\b"),
                _ci(r"\b(?:fair\s+terms?|are\s+(?:these|the)\s+terms\s+fair|should\s+i\s+(?:worry|be\s+concerned))\b"),
                _ci(r"\b(?:legally\s+enforceable|enforceable\b)\b"),
                _ci(r"\b(?:used\s+against\s+me|could\s+this\s+(?:section|clause|provision)\s+be\s+used\s+against)\b"),
                _ci(r"\bgive\s+me\s+your\s+legal\s+advice\b"),
                _ci(r"\b(?:what\s+does\s+this\s+legal\s+mumbo\s+jumbo\s+(?:even\s+)?mean)\b"),
                _ci(r"\b(?:tell\s+me\s+if\s+i\s+should\s+sign|tell\s+me\s+what\s+my\s+legal\s+options\s+are)\b"),
                _ci(r"\b(?:tell\s+me\s+if\s+i\s+should\s+(?:worry|be\s+worried))\b(?=.*(?:clause|contract|indemnif|agreement|legal|getting))"),
            ],
        ),
        GuardrailWall(
            name="no_creative_generation",
            description="BLOCKED: I cannot generate legal text, draft clauses, or create documents. I only analyze text you provide to me.",
            patterns=[
                _ci(r"\b(?:draft|write|create|generat\w+|make\s+up|make\s+me)\s+.{0,15}(?:clause|contract|agreement|provision|legal\s+(?:document|text|language)|nda|terms?\s+of\s+service|non.?compete|non.?disclosure|employment\s+contract|service\s+agreement)\b"),
                _ci(r"\b(?:write\s+me\s+(?:a\s+)?|create\s+(?:a\s+)?|make\s+me\s+(?:a\s+)?|write\s+(?:me\s+)?(?:a\s+)?quick\s+)(?:non.?compete|non.?disclosure|nda|employment\s+contract|service\s+agreement|contract)\b"),
                _ci(r"\b(?:add\s+(?:a\s+)?clause|insert\s+(?:a\s+)?provision|what\s+language\s+should\s+i\s+(?:add|use|include)|rewrite\s+(?:this|the)\s+(?:section|provision|clause|liability))\b"),
                _ci(r"\b(?:rephrase\s+this\s+clause|rewrite\s+this\s+(?:section|provision)|improve\s+this\s+legal\s+text|draft\s+a\s+better\s+version)\b"),
                _ci(r"\b(?:what\s+language\s+(?:should|can|do)\s+i\s+(?:add|use|include|put))\b"),
                _ci(r"\b(?:rewrite\s+it\s+to\s+protect\s+me|rewrite\s+(?:it|this|that)\s+to)\b"),
            ],
        ),
        GuardrailWall(
            name="no_web_research",
            description="BLOCKED: I cannot look up laws, cases, precedents, statutes, or regulations. I only analyze the document text you provide.",
            patterns=[
                _ci(r"\b(?:look\s+up|search\s+for|find|research|check)\s+(?:the\s+)?(?:law|laws|statute\w*|case\s+law|precedent\w*|regulation\w*|ruling\w*|ordinance\w*)\b"),
                _ci(r"\bwhat\s+(?:does\s+the\s+law\s+say|do\s+the\s+laws\s+say|is\s+there\s+a\s+law|is\s+(?:this|that)\s+(?:even\s+)?legal\s+in)\b"),
                _ci(r"\b(?:find\s+(?:relevant\s+)?case\s+law|search\s+(?:case\s+law|legal\s+database|court\s+records|westlaw|lexis)|search\s+for\s+relevant\s+case\s+law)\b"),
                _ci(r"\b(?:what\s+(?:are\s+)?the\s+(?:statutes|regulations|legal\s+requirements)\s+(?:in|for|regarding))\b"),
                _ci(r"\b(?:has\s+there\s+been\s+a\s+(?:case|ruling|decision)\s+(?:about|on|regarding))\b"),
                _ci(r"\b(?:does\s+the\s+law\s+(?:in|of)\s+\w+\s+allow|is\s+(?:this|that)\s+legal\s+in\s+(?:my|this)\s+state)\b"),
                _ci(r"\b(?:enforceable\s+in\s+(?:my|this)\s+state|legal\s+in\s+(?:my|this)\s+state)\b"),
                _ci(r"\b(?:precedent\w*\s+where\s+court|case\w*\s+where\s+court\s+ruled|precedent\w*\s+(?:about|on))\b"),
                _ci(r"\b(?:find\s+me\s+(?:some\s+)?precedent\w*|find\s+precedent\w*)\b"),
            ],
        ),
        GuardrailWall(
            name="no_hallucination",
            description="BLOCKED: That information does not appear in the document provided. I can only state what is written in the document. If something is not in the document, I must say 'not found in document'.",
            patterns=[
                _ci(r"\b(?:i\s+(?:think|believe|assume|guess|reckon)\s+(?:this\s+means|it\s+implies|they\s+intended|that\s+means))\b"),
                _ci(r"\b(?:probably|likely|most\s+likely|i'?d\s+say|i\s+suppose|sounds\s+like)\b(?=.*(?:clause|contract|provision|agreement|means|implies|cancel|terminate))"),
                _ci(r"\b(?:the\s+(?:implied|intended|likely|probable)\s+meaning\s+of\s+this\s+(?:clause|section|provision))\b"),
                _ci(r"\b(?:although\s+not\s+(?:explicitly\s+)?stated|while\s+not\s+(?:explicitly\s+)?written|even\s+though\s+it\s+doesn'?t\s+say|doesn'?t\s+say\s+it\s+explicitly)\b(?=.*(?:probably|likely|means|implies|intended|cancel))"),
                _ci(r"\b(?:this\s+clause\s+implies|this\s+means\s+i\s+can|that\s+sounds\s+like\s+i\s+can|right\?\s*$)\b(?=.*(?:cancel|terminate|get\s+out|early))"),
            ],
        ),
        GuardrailWall(
            name="attorney_referral",
            description="BLOCKED: I must remind you to consult a qualified attorney for any legal decisions. Document analysis is not a substitute for legal representation.",
            patterns=[
                _ci(r"\b(?:i\s+don'?t\s+need\s+(?:a\s+)?(?:lawyer|attorney|legal\s+counsel)|skip\s+(?:the\s+)?(?:lawyer|attorney))\b"),
                _ci(r"\b(?:don'?t\s+(?:need\s+to\s+)?(?:see|consult|talk\s+to|hire)\s+(?:a\s+)?(?:lawyer|attorney|solicitor))\b"),
                _ci(r"\b(?:just\s+give\s+me\s+(?:your|ur)\s+(?:opinion|take|read)|just\s+tell\s+me\s+(?:if|whether))\b(?=.*(?:contract|clause|legal|agreement|sign|worry|scam))"),
            ],
        ),
    ],
)


# ─── Financial Gainer (4 walls) ──────────────────────────────────────────────

FINANCIAL_GAINER_GUARDRAILS = CapabilityGuardrails(
    capability="Financial Gainer",
    walls=[
        GuardrailWall(
            name="no_income_guarantees",
            description="BLOCKED: I cannot guarantee income or promise specific earnings. Results depend on your effort, skill, and market conditions. No income opportunity is guaranteed.",
            patterns=[
                _ci(r"\b(?:guarantee|guaranteed|promise|promised)\s+.{0,15}(?:make|earn|get|see|generate)\s+\$?\d+"),
                _ci(r"\b(?:you\s+will\s+(?:make|earn|get|see)|you'?ll\s+(?:make|earn|get)|ur\s+(?:sure|guarantee)\s+i'?ll\s+make)\s+\$?\d+"),
                _ci(r"\b(?:100%\s+(?:guaranteed|certain|sure|safe))\b"),
                _ci(r"\b(?:guaranteed\s+(?:income|profit|return|earnings|money|success|way))\b"),
                _ci(r"\b(?:will\s+definitely|definitely\s+(?:make|earn|generate))\s+(?:money|income|profit|\$?\d+)\b"),
                _ci(r"\b(?:sure.?fire|can'?t\s+fail|foolproof|no.?risk)\b"),
                _ci(r"\b(?:make\s+bank|guarantee\s+ill\s+make|guarantee\s+i'?ll\s+make)\b"),
                _ci(r"\b(?:promise\s+at\s+least\s+\$?\d+|sure\s+i'?ll\s+make\s+\$?\d+)\b"),
                _ci(r"\b(?:exactly\s+how\s+much\s+money\s+i\s+will\s+make|how\s+much\s+money\s+(?:i|you)\s+will\s+make)\b"),
            ],
        ),
        GuardrailWall(
            name="advisory_only",
            description="BLOCKED: I provide advisory suggestions only. I cannot execute transactions, make investments, trade stocks, or commit money on your behalf.",
            patterns=[
                _ci(r"\b(?:execute|place|make)\s+(?:a\s+)?(?:trade|transaction|order|investment|deposit|market\s+order)\b"),
                _ci(r"\b(?:execute\s+this\s+trade|execute\s+a\s+trade)\b"),
                _ci(r"\b(?:invest\s+my\s+(?:money|funds|savings)|trade\s+for\s+me|buy\s+(?:it|shares|stock|some)\s+for\s+me|invest\s+(?:my|our)\s+(?:money|funds|savings))\b"),
                _ci(r"\b(?:transfer\s+(?:funds|money|\$\d+)|send\s+(?:payment|money)|wire\s+(?:money|funds))\b"),
                _ci(r"\b(?:click\s+this\s+link\s+to\s+(?:invest|buy|trade)|go\s+to\s+(?:this|that)\s+(?:exchange|broker|platform)\s+and\s+(?:buy|invest|trade))\b"),
                _ci(r"\b(?:buy\s+(?:some\s+)?(?:bitcoin|crypto|stock|shares)|buy\s+\d+\s+shares)\b"),
                _ci(r"\b(?:place\s+(?:a\s+)?(?:buy|sell)\s+order|buy\s+orders?\s+for)\b"),
                _ci(r"\b(?:trade\s+stocks?\s+on\s+my|invest\s+.{0,10}(?:for\s+me|on\s+my\s+behalf))\b"),
                _ci(r"\b(?:buy|sell|trade|invest\s+in|purchase|put\s+(?:money|all\s+my\s+money)\s+into)\s+(?:\w+\s+)?(?:stocks?|shares?|crypto|bitcoin|bonds?|etf|forex|options?|futures?|coin)\w*\b"),
                _ci(r"\b(?:transfer\s+my\s+funds\s+to|transfer\s+.{0,10}(?:funds|money)\s+to\s+(?:the\s+)?(?:recommended|this|that))\b"),
                _ci(r"\b(?:would\s+you\s+recommend\s+i\s+(?:put|invest).{0,15}(?:money|funds|all))\b"),
            ],
        ),
        GuardrailWall(
            name="no_illegal_schemes",
            description="BLOCKED: I cannot recommend illegal, unethical, or high-risk schemes for making money. All suggestions must be legal and ethical.",
            patterns=[
                _ci(r"\b(?:illegal|unlawful|criminal|fraudulent|scam|pyramid|ponzi)\b"),
                _ci(r"\b(?:money\s+laundering|tax\s+evasion|wire\s+fraud|identity\s+theft|counterfeit)\b"),
                _ci(r"\b(?:how\s+to\s+(?:scam|cheat|steal|launder|evade\s+(?:taxes|the\s+irs)))\b"),
                _ci(r"\b(?:get\s+rich\s+quick|easy\s+money\s+(?:scheme|scam)|fast\s+cash)\b"),
                _ci(r"\b(?:dark\s+web|black\s+market|illegal\s+drugs|smuggling)\b"),
                _ci(r"\b(?:counterfeit\s+(?:money|goods|products)|fake\s+(?:invoices|receipts|documents))\b"),
                _ci(r"\b(?:no\s+questions\s+asked)\b(?=.*(?:money|cash|income|make))"),
            ],
        ),
        GuardrailWall(
            name="disclaimer_mandatory",
            description="BLOCKED: The Financial Gainer disclaimer must be acknowledged before any financial suggestions are provided. This is not a guaranteed way to make money.",
            patterns=[
                _ci(r"\b(?:skip\s+(?:the\s+)?disclaimer|don'?t\s+show\s+(?:me\s+)?(?:the\s+)?disclaimer|i'?ve\s+already\s+(?:read|seen)\s+(?:it|the\s+disclaimer))\b"),
                _ci(r"\b(?:i'?ve\s+already\s+(?:read|seen)\s+(?:it|the\s+disclaimer)\s+.{0,15}(?:skip|continue|proceed|give))\b"),
                _ci(r"\b(?:just\s+skip\s+it\s+and\s+give\s+me|skip\s+it\s+and\s+give)\b"),
                _ci(r"\b(?:i\s+don'?t\s+need\s+(?:to\s+see\s+)?(?:the\s+)?disclaimer|hide\s+(?:the\s+)?disclaimer|remove\s+(?:the\s+)?disclaimer|disclaimer\s+bs)\b"),
                _ci(r"\b(?:just\s+give\s+me\s+(?:the\s+)?(?:advice|suggestions|tips|money\s+tips)\s+(?:without|skip)\s+(?:the\s+)?disclaimer)\b"),
                _ci(r"\b(?:dont\s+show\s+me\s+(?:the\s+)?disclaimer|dont\s+need\s+(?:to\s+see\s+)?(?:the\s+)?disclaimer)\b"),
            ],
        ),
    ],
)


# ─── Coder (2 walls — light) ──────────────────────────────────────────────────

CODER_GUARDRAILS = CapabilityGuardrails(
    capability="Coder",
    walls=[
        GuardrailWall(
            name="no_malware_authoring",
            description="BLOCKED: I cannot write malware, viruses, ransomware, exploits, or any malicious code. I can help you understand and defend against these, but I will not create them.",
            patterns=[
                _ci(r"\b(?:write|create|build|make|generat\w+|develop|code|program|script)\s+.{0,15}(?:malware|virus|ransomware|trojan|worm|rootkit|backdoor|keylogger|spyware|botnet|payload|exploit\s+script|attack\s+script)\b"),
                _ci(r"\b(?:write|create|build|make)\s+.{0,10}(?:phishing\s+(?:kit|email|site|page|template)|fake\s+login\s+page|credential\s+stealer|password\s+(?:stealer|harvester|cracker))\b"),
                _ci(r"\b(?:create|build|write)\s+.{0,10}(?:sql\s+injection\s+tool|xss\s+payload|ddos\s+(?:tool|script|bot)|brute.?force\s+(?:tool|script))\b"),
                _ci(r"\b(?:destructive|wiping|data\s+destruction)\s+(?:script|code|program|routine)\b"),
                _ci(r"\b(?:encrypt\s+(?:all|every|the)\s+(?:files?|drives?|disks?)|ransomware\s+(?:script|code|payload))\b"),
            ],
        ),
        GuardrailWall(
            name="no_system_sabotage",
            description="BLOCKED: I cannot write code that sabotages, disables, or destroys system components, security software, or access controls.",
            patterns=[
                _ci(r"\b(?:disable|turn\s+off|kill|stop|break|sabotage|corrupt)\s+.{0,15}(?:antivirus|anti.?virus|firewall|defender|security\s+software|endpoint\s+protection|windows\s+defender)\b"),
                _ci(r"\b(?:write|create|make|build)\s+.{0,10}(?:registry\s+(?:hack|edit|mod)|bootloader\s+(?:mod|hack|replace)|firmware\s+(?:mod|hack|overwrite))\b"),
                _ci(r"\b(?:permanently\s+delete|wipe|destroy|corrupt)\s+.{0,10}(?:system\s+files|boot\s+sector|registry|firmware|bios|uefi)\b"),
                _ci(r"\b(?:hidden|silent|stealth)\s+(?:persist\w*|backdoor|implant)\s+(?:script|code|module|program)\b"),
            ],
        ),
        GuardrailWall(
            name="no_nexus_replication",
            description="BLOCKED: I cannot help replicate, reconstruct, or build a competing AI platform based on Command Nexus or its proprietary architecture. I can help with general software development.",
            patterns=[
                _ci(r"\b(?:replicate|reproduce|reconstruct|clone|copy)\s+.{0,20}(?:command\s+nexus|nexus\s+architecture|this\s+system|this\s+platform|ai\s+platform|ai\s+console)\b"),
                _ci(r"\b(?:build|create|make|develop)\s+.{0,15}(?:ai\s+platform|ai\s+console|ai\s+assistant\s+system|capability\s+router|capability\s+registry|guardrail\s+engine|governance\s+engine)\b"),
                _ci(r"\b(?:build|create|make)\s+.{0,10}(?:ai\s+like\s+this|ai\s+like\s+you|assistant\s+like\s+command\s+nexus|platform\s+like\s+this)\b"),
                _ci(r"\b(?:how\s+(?:is|does)\s+(?:command\s+nexus|this\s+system)\s+(?:built|architected|structured|designed|work))\b"),
                _ci(r"\b(?:source\s+code|internal\s+architecture|proprietary\s+(?:code|architecture|system|methods))\s+.{0,15}(?:for|of)\s+(?:command\s+nexus|nexus|this\s+system)\b"),
                _ci(r"\b(?:capability\s+book|knowledge\s+book|ability\s+book|forge\s+window|nexus\s+ai\s+runtime|moirai|compendium|stasis\s+gate|tripwire)\s+.{0,10}(?:source|code|implementation|reproduce|replicate|rebuild)\b"),
            ],
        ),
    ],
)


# ─── Customer Support AI (1 wall — light) ─────────────────────────────────────

CUSTOMER_SUPPORT_AI_GUARDRAILS = CapabilityGuardrails(
    capability="Customer Support AI",
    walls=[
        GuardrailWall(
            name="no_internal_disclosure",
            description="BLOCKED: I cannot reveal internal system architecture, AI Book contents, prompt templates, capability mechanics, or proprietary implementation details.",
            patterns=[
                _ci(r"\b(?:show|reveal|tell|give|share|expose|disclose)\s+me\s+.{0,15}(?:internal|proprietary|backend|underlying|source|architecture|prompt\s+template|system\s+prompt|ai\s+book|book\s+content|scaffold|capability\s+mechanic)\b"),
                _ci(r"\b(?:what(?:'?s|s)\s+(?:your|the)\s+(?:system\s+prompt|internal\s+(?:architecture|structure|code)|backend\s+(?:code|logic)|prompt\s+template|training\s+data|model\s+(?:weight|parameter|architecture)))\b"),
                _ci(r"\b(?:how\s+(?:are|is)\s+(?:you|this\s+system|the\s+ai)\s+(?:built|constructed|programmed|configured|architected|structured))\b"),
                _ci(r"\b(?:dump|print|output|export)\s+.{0,40}(?:system\s+prompt|internal\s+(?:config|state|memory)|book\s+(?:content|text)|scaffold\s+(?:code|logic))\b"),
                _ci(r"\b(?:ignore|disregard|override|bypass)\s+.{0,10}(?:your\s+(?:rules|instructions|guidelines|restrictions)|system\s+(?:rules|guard|restrict)|safety|policy)\b"),
            ],
        ),
    ],
)


# ─── Email Automation (1 wall — light) ────────────────────────────────────────

EMAIL_AUTOMATION_GUARDRAILS = CapabilityGuardrails(
    capability="Email Automation",
    walls=[
        GuardrailWall(
            name="no_phishing_or_spam",
            description="BLOCKED: I cannot create phishing emails, deceptive sender spoofing, mass spam campaigns, or emails designed to trick recipients into revealing credentials or personal information.",
            patterns=[
                _ci(r"\b(?:create|write|draft|generat\w+|make|build)\s+.{0,15}(?:phishing\s+(?:email|campaign|template|message)|spoofed\s+(?:email|sender)|fake\s+(?:login|verification|password\s+reset)\s+email)\b"),
                _ci(r"\b(?:send|blast|mass\s+send|bulk\s+send)\s+.{0,10}(?:spam|unsolicited|mass\s+email|blast\s+campaign)\b"),
                _ci(r"\b(?:pretend\s+to\s+be|spoof|impersonat\w+)\s+.{0,15}(?:bank|paypal|amazon|google|microsoft|apple|irs|government|ceo|boss|it\s+department|helpdesk)\b"),
                _ci(r"\b(?:harvest|scrape|collect)\s+.{0,10}(?:email\s+address|contact\s+list|mailing\s+list)\b(?=.*(?:spam|blast|mass|unsolicited))"),
                _ci(r"\b(?:credential\s+(?:harvest|theft|capture)|password\s+(?:steal|capture|harvest)|trick\s+.{0,10}(?:into\s+(?:entering|giving|revealing)|to\s+(?:enter|give|reveal)))\b"),
            ],
        ),
    ],
)


# ─── Activity Watcher (1 wall — light) ────────────────────────────────────────

ACTIVITY_WATCHER_GUARDRAILS = CapabilityGuardrails(
    capability="Activity Watcher",
    walls=[
        GuardrailWall(
            name="no_credential_capture",
            description="BLOCKED: I cannot capture, record, store, or transmit passwords, credentials, authentication tokens, or sensitive financial information during activity observation.",
            patterns=[
                _ci(r"\b(?:capture|record|log|store|save|transmit|send|extract)\s+.{0,15}(?:password|passwd|credential|api\s+key\w*|secret\s+key\w*|auth\s+token|access\s+token|session\s+token|private\s+key\w*|credit\s+card|cvv|ssn|social\s+security)\b"),
                _ci(r"\b(?:watch|observe|monitor|record)\s+.{0,10}(?:typing|keystroke\w*|key\s+press|password\s+field|login\s+form|banking|credit\s+card|payment\s+form)\b"),
                _ci(r"\b(?:keylog|key\s+log|keystroke\s+log|screen\s+capture\s+.{0,10}(?:password|credential|banking|financial))\b"),
                _ci(r"\b(?:remember|learn|store)\s+.{0,10}(?:my\s+password|credentials|login\s+(?:info|detail)|banking\s+(?:info|detail)|credit\s+card\s+(?:info|number))\b"),
            ],
        ),
    ],
)


# ─── Creative Writing (1 wall — light) ────────────────────────────────────────

CREATIVE_WRITING_GUARDRAILS = CapabilityGuardrails(
    capability="Creative Writing",
    walls=[
        GuardrailWall(
            name="no_deceptive_content",
            description="BLOCKED: I cannot write phishing emails, social engineering scripts, fake reviews, deceptive testimonials, or content designed to defraud or manipulate people.",
            patterns=[
                _ci(r"\b(?:write|create|draft|generat\w+|make)\s+.{0,15}(?:phishing\s+(?:email|message|letter)|social\s+engineering\s+(?:script|message|email)|fake\s+(?:review|testimonial|endorsement|news\s+article|press\s+release))\b"),
                _ci(r"\b(?:write|create|draft)\s+.{0,10}(?:scam\s+(?:email|letter|message|script)|fraudulent\s+(?:email|letter|message)|deceptive\s+(?:email|message|letter|ad|advertisement))\b"),
                _ci(r"\b(?:pretend\s+to\s+be|impersonat\w+|pose\s+as)\s+.{0,15}(?:in\s+(?:an?\s+)?(?:email|letter|message|review|testimonial|post))\b"),
                _ci(r"\b(?:fake\s+proof\s+of\s+(?:purchase|income|employment|identity)|forge\s+.{0,10}(?:document|letter|certificate|receipt|invoice))\b"),
                _ci(r"\b(?:catfish|romance\s+scam|nigerian\s+prince|advance\s+fee\s+(?:fraud|scam))\b"),
            ],
        ),
    ],
)


# ─── DevOps Assistant (2 walls — light) ──────────────────────────────────────

DEVOPS_ASSISTANT_GUARDRAILS = CapabilityGuardrails(
    capability="DevOps Assistant",
    walls=[
        GuardrailWall(
            name="no_production_deployment",
            description="BLOCKED: I cannot deploy directly to production, execute destructive infrastructure commands, or bypass approval gates.",
            patterns=[
                _ci(r"\b(?:deploy\s+to\s+production|prod\s+deploy|force\s+deploy|skip\s+(?:approval|review|staging))\b"),
                _ci(r"\b(?:rm\s+-rf\s+/(?:prod|production|live)|drop\s+(?:production|prod)\s+(?:database|table|schema))\b"),
                _ci(r"\b(?:delete\s+(?:all|entire)\s+(?:production|prod)\s+(?:data|database|cluster|nodes))\b"),
            ],
        ),
        GuardrailWall(
            name="no_credential_exposure",
            description="BLOCKED: I cannot output, log, or expose secrets, API keys, tokens, or credentials in configuration files.",
            patterns=[
                _ci(r"\b(?:print|echo|log|output|display)\s+.{0,10}(?:api\s+key|secret|token|password|credential|private\s+key)\b"),
                _ci(r"\b(?:hardcode|hard-code|embed)\s+.{0,10}(?:api\s+key|secret|token|password|credential)\b"),
            ],
        ),
        GuardrailWall(
            name="no_nexus_replication",
            description="BLOCKED: I cannot help replicate Command Nexus infrastructure, build competing AI platforms, or reconstruct proprietary DevOps/governance systems. I can help with general DevOps and infrastructure tasks.",
            patterns=[
                _ci(r"\b(?:replicate|reproduce|reconstruct|clone|copy)\s+.{0,20}(?:command\s+nexus|nexus\s+architecture|this\s+system|ai\s+platform|ai\s+console)\b"),
                _ci(r"\b(?:build|create|make|develop)\s+.{0,15}(?:ai\s+platform|ai\s+console|capability\s+router|governance\s+engine|guardrail\s+system|stasis\s+gate|tripwire\s+system)\b"),
                _ci(r"\b(?:deploy|host|stand\s+up|set\s+up)\s+.{0,30}(?:competing\s+ai|rival\s+ai|alternative\s+to\s+(?:command\s+nexus|nexus))\b"),
                _ci(r"\b(?:infrastructure|pipeline|deployment)\s+.{0,10}(?:for|to\s+build)\s+(?:ai\s+platform|competing\s+ai|rival\s+(?:ai|system)|alternative\s+ai)\b"),
            ],
        ),
    ],
)


# ─── Database Manager (2 walls — light) ──────────────────────────────────────

DATABASE_MANAGER_GUARDRAILS = CapabilityGuardrails(
    capability="Database Manager",
    walls=[
        GuardrailWall(
            name="no_destructive_queries",
            description="BLOCKED: I cannot generate or execute DROP, TRUNCATE, or DELETE without WHERE clauses on production databases.",
            patterns=[
                _ci(r"\b(?:drop\s+(?:table|database|schema|collection)\s+.{0,10}(?:prod|production|live))\b"),
                _ci(r"\b(?:truncate\s+.{0,10}(?:prod|production|live))\b"),
                re.compile(r"\b(?:delete\s+from\s+\w+\s*;\s*$)", re.IGNORECASE | re.MULTILINE),
            ],
        ),
        GuardrailWall(
            name="no_data_exfiltration",
            description="BLOCKED: I cannot generate queries designed to exfiltrate sensitive data like passwords, PII, or payment information.",
            patterns=[
                _ci(r"\b(?:select\s+.{0,20}(?:password|passwd|credit\s+card|ssn|social\s+security)\s+from\b)"),
                _ci(r"\b(?:export|dump|extract)\s+.{0,10}(?:user|customer|payment|billing)\s+(?:data|records|table)\b"),
            ],
        ),
    ],
)


# ─── Script Writer (1 wall — light) ──────────────────────────────────────────

SCRIPT_WRITER_GUARDRAILS = CapabilityGuardrails(
    capability="Script Writer",
    walls=[
        GuardrailWall(
            name="no_malicious_scripts",
            description="BLOCKED: I cannot write malware, ransomware, keyloggers, reverse shells, or scripts designed for unauthorized access.",
            patterns=[
                _ci(r"\b(?:malware|ransomware|keylog\w*|trojan|backdoor|rootkit|spyware)\b"),
                _ci(r"\b(?:reverse\s+shell|bind\s+shell|payload\s+(?:generation|creation)|exploit\s+(?:generation|creation|script))\b"),
                _ci(r"\b(?:unauthorized\s+(?:access|entry|penetration)|bypass\s+(?:firewall|antivirus|security|auth))\b"),
                _ci(r"\b(?:crypto\s+(?:miner|mining)|botnet\s+(?:script|payload|command))\b"),
            ],
        ),
        GuardrailWall(
            name="no_nexus_replication",
            description="BLOCKED: I cannot write scripts that replicate Command Nexus architecture, build competing AI platforms, or reconstruct proprietary systems. I can help with general scripting tasks.",
            patterns=[
                _ci(r"\b(?:replicate|reproduce|reconstruct|clone|copy)\s+.{0,20}(?:command\s+nexus|nexus\s+architecture|this\s+system|ai\s+platform|ai\s+console)\b"),
                _ci(r"\b(?:script|automate)\s+.{0,15}(?:ai\s+platform|capability\s+router|governance\s+engine|guardrail\s+system|nexus\s+runtime|forge\s+system)\b"),
                _ci(r"\b(?:build|create|make)\s+.{0,10}(?:ai\s+like\s+this|ai\s+like\s+you|assistant\s+like\s+command\s+nexus|platform\s+like\s+this)\b"),
                _ci(r"\b(?:automate|script)\s+.{0,10}(?:competing\s+ai|rival\s+ai|alternative\s+to\s+(?:command\s+nexus|nexus))\b"),
            ],
        ),
    ],
)


# ─── Personal Finance Manager (1 wall — light) ───────────────────────────────

PERSONAL_FINANCE_MANAGER_GUARDRAILS = CapabilityGuardrails(
    capability="Personal Finance Manager",
    walls=[
        GuardrailWall(
            name="no_transaction_execution",
            description="BLOCKED: I cannot execute trades, transfer funds, access bank accounts, or make financial transactions. Advisory only.",
            patterns=[
                _ci(r"\b(?:execute|place|make)\s+.{0,10}(?:trade|transaction|transfer|payment|purchase|order)\b"),
                _ci(r"\b(?:access|connect\s+to|log\s+into)\s+.{0,10}(?:bank|brokerage|trading|investment)\s+(?:account|portal|api)\b"),
                _ci(r"\b(?:buy|sell|purchase)\s+.{0,10}(?:stock|bond|crypto|currency|option|future|etf)\b"),
            ],
        ),
    ],
)


# ─── Privacy Compliance Checker (1 wall — light) ─────────────────────────────

PRIVACY_COMPLIANCE_CHECKER_GUARDRAILS = CapabilityGuardrails(
    capability="Privacy Compliance Checker",
    walls=[
        GuardrailWall(
            name="no_legal_certification",
            description="BLOCKED: I cannot provide legal certification, legal opinions, or guaranteed compliance. Informational guidance only — consult a legal professional.",
            patterns=[
                _ci(r"\b(?:certif\w+\s+(?:compliance|gdpr|ccpa|legal)|guarantee\s+compliance|legal\s+(?:opinion|certification|guarantee))\b"),
                _ci(r"\b(?:warrant\w*\s+(?:compliance|legal|privacy)|attest\w*\s+(?:compliance|legal))\b"),
            ],
        ),
    ],
)


# ─── Patent Researcher (1 wall — light) ──────────────────────────────────────

PATENT_RESEARCHER_GUARDRAILS = CapabilityGuardrails(
    capability="Patent Researcher",
    walls=[
        GuardrailWall(
            name="no_legal_advice",
            description="BLOCKED: I cannot provide legal advice, patentability opinions, or legal determinations. Research guidance only — consult a patent attorney.",
            patterns=[
                _ci(r"\b(?:legal\s+advice|patentabilit\w+\s+(?:opinion|determination|assessment)|legal\s+(?:opinion|determination|conclusion))\b"),
                _ci(r"\b(?:guarantee\s+(?:patent|approval)|warrant\w*\s+(?:patent|infringement\s+free))\b"),
            ],
        ),
    ],
)


# ═══════════════════════════════════════════════════════════════════════════════
# REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

CAPABILITY_GUARDRAILS: dict[str, CapabilityGuardrails] = {
    # High-risk — full guardrails
    "Security Auditor": SECURITY_AUDITOR_GUARDRAILS,
    "Code Reviewer": CODE_REVIEWER_GUARDRAILS,
    "Medical Researcher": MEDICAL_RESEARCHER_GUARDRAILS,
    "Legal Document Reviewer": LEGAL_DOCUMENT_REVIEWER_GUARDRAILS,
    "Financial Gainer": FINANCIAL_GAINER_GUARDRAILS,
    # Light guardrails for dangerous edge cases
    "Coder": CODER_GUARDRAILS,
    "Customer Support AI": CUSTOMER_SUPPORT_AI_GUARDRAILS,
    "Email Automation": EMAIL_AUTOMATION_GUARDRAILS,
    "Activity Watcher": ACTIVITY_WATCHER_GUARDRAILS,
    "Creative Writing": CREATIVE_WRITING_GUARDRAILS,
    # Phase 7 — new high-risk guardrails
    "DevOps Assistant": DEVOPS_ASSISTANT_GUARDRAILS,
    "Database Manager": DATABASE_MANAGER_GUARDRAILS,
    "Script Writer": SCRIPT_WRITER_GUARDRAILS,
    "Personal Finance Manager": PERSONAL_FINANCE_MANAGER_GUARDRAILS,
    "Privacy Compliance Checker": PRIVACY_COMPLIANCE_CHECKER_GUARDRAILS,
    "Patent Researcher": PATENT_RESEARCHER_GUARDRAILS,
}


def check_guardrails(capability: str, text: str) -> GuardrailResult:
    """Check if text violates any guardrails for the given capability.

    Returns GuardrailResult with blocked=True if any wall is triggered.
    Returns GuardrailResult with blocked=False if text passes all walls.
    Returns GuardrailResult with blocked=False if capability has no guardrails.
    """
    guardrails = CAPABILITY_GUARDRAILS.get(capability)
    if guardrails is None:
        return GuardrailResult(blocked=False)
    return guardrails.check(text)


def get_guardrails_for_capability(capability: str) -> CapabilityGuardrails | None:
    """Get the guardrails object for a capability, or None if none exist."""
    return CAPABILITY_GUARDRAILS.get(capability)


def list_guarded_capabilities() -> list[str]:
    """Return list of capabilities that have guardrails."""
    return list(CAPABILITY_GUARDRAILS.keys())


def get_guardrail_summary(capability: str) -> str:
    """Get a human-readable summary of guardrails for a capability."""
    guardrails = CAPABILITY_GUARDRAILS.get(capability)
    if guardrails is None:
        return f"{capability}: No guardrails defined."
    lines = [f"{capability} — {guardrails.wall_count} guardrail walls:"]
    for wall in guardrails.walls:
        lines.append(f"  • {wall.name}: {wall.description[:80]}...")
    return "\n".join(lines)
