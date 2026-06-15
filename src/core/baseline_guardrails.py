"""
BASELINE GUARDRAILS - COMMAND NEXUS SAFETY SYSTEM
==================================================

These guardrails are ALWAYS ACTIVE and CANNOT BE DISABLED.
They protect against illegal, harmful, and dangerous content regardless of:
- User tier (free, paid, founder)
- Parental control settings
- Admin privileges
- Any configuration

This is the "safety floor" that applies to everyone.

Categories:
1. ILLEGAL CONTENT - Law enforcement level restrictions
2. HARMFUL CONTENT - Self-harm, violence promotion, exploitation  
3. SEXUAL CONTENT - CSAM, explicit content, sexual exploitation
4. DECEPTION - Fraud, impersonation, social engineering
"""

from dataclasses import dataclass
from typing import List, Dict, Set, Tuple, Optional
from enum import Enum, auto
import re


class GuardrailCategory(Enum):
    """Categories of baseline guardrails."""
    ILLEGAL = auto()
    HARMFUL = auto()
    SEXUAL = auto()
    DECEPTION = auto()
    SECURITY = auto()


class SeverityLevel(Enum):
    """Severity of violation."""
    LOW = auto()      # Log only
    MEDIUM = auto()   # Block + log
    HIGH = auto()     # Block + log + alert
    CRITICAL = auto() # Block + log + immediate alert + possible account action


@dataclass
class GuardrailRule:
    """A single baseline guardrail rule."""
    id: str
    name: str
    description: str
    category: GuardrailCategory
    severity: SeverityLevel
    
    # Detection patterns
    keywords: List[str] = None
    phrases: List[str] = None
    regex_patterns: List[str] = None
    
    # Response settings
    block_message: str = "This request cannot be processed."
    log_event: bool = True
    alert_admin: bool = False
    flag_for_review: bool = False
    
    # Context exemptions (if any)
    # e.g., "educational_context" might allow certain topics if properly framed
    allowed_contexts: List[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.phrases is None:
            self.phrases = []
        if self.regex_patterns is None:
            self.regex_patterns = []
        if self.allowed_contexts is None:
            self.allowed_contexts = []


# =============================================================================
# BASELINE GUARDRAILS DATABASE
# These are HARDCODED and CANNOT BE MODIFIED by users, admins, or founders
# =============================================================================

BASELINE_GUARDRAILS = [
    # =========================================================================
    # ILLEGAL CONTENT - Weapons, Drugs, Crime, Terrorism
    # =========================================================================
    
    GuardrailRule(
        id="illegal_weapons_manufacturing",
        name="Illegal Weapons Manufacturing",
        description="Instructions for making illegal weapons, explosives, or destructive devices",
        category=GuardrailCategory.ILLEGAL,
        severity=SeverityLevel.CRITICAL,
        keywords=[
            "bomb", "explosive", "detonate", "TNT", "C4", "dynamite", "nitroglycerin",
            "gunpowder", "thermite", "napalm", "chlorine bomb", "pipe bomb",
            "pressure cooker bomb", " Molotov cocktail"
        ],
        phrases=[
            "how to make a bomb",
            "how to build explosives",
            "make gunpowder at home",
            "create a explosive device",
            "manufacture weapons",
            "build a bomb with household items",
            "3D print gun parts",
            "make a silencer",
            "convert to full auto",
            "undetectable firearm"
        ],
        regex_patterns=[
            r"\b(?:how|steps|guide)\s+(?:to|for)\s+(?:make|build|create)\s+(?:a\s+)?(?:bomb|explosive|weapon)",
            r"\b(?:anarchist|cookbook)\b",
            r"\b(?:improvised|homemade)\s+(?:explosive|firearm|weapon)\b"
        ],
        block_message="I cannot provide instructions for creating weapons or explosives. This type of content is illegal and potentially dangerous.",
        alert_admin=True,
        flag_for_review=True
    ),
    
    GuardrailRule(
        id="illegal_drug_manufacturing",
        name="Illegal Drug Production",
        description="Instructions for manufacturing illegal drugs or controlled substances",
        category=GuardrailCategory.ILLEGAL,
        severity=SeverityLevel.CRITICAL,
        keywords=[
            "methamphetamine", "meth", "cocaine", "heroin", "fentanyl", "LSD", "ecstasy",
            "MDMA", "meth lab", "cook meth", "synthesize drugs", "extract DMT",
            "grow opium", "refine heroin", "make crack", "freebase cocaine"
        ],
        phrases=[
            "how to make meth",
            "cook meth at home",
            "synthesize LSD",
            "make ecstasy pills",
            "extract drugs from",
            "drug synthesis guide",
            "clandestine lab",
            "recipe for drugs",
            "produce illegal substances"
        ],
        regex_patterns=[
            r"\b(?:how|steps|recipe)\s+(?:to|for)\s+(?:make|cook|synthesize|produce)\s+(?:meth|drugs|cocaine|heroin|LSD)",
            r"\b(?:clandestine|illegal)\s+(?:lab|laboratory|production)\b",
            r"\bdrug\s+(?:synthesis|manufacturing|cooking)\b"
        ],
        block_message="I cannot provide instructions for manufacturing illegal drugs. This content is illegal and potentially harmful.",
        alert_admin=True,
        flag_for_review=True
    ),
    
    GuardrailRule(
        id="cybercrime_tools",
        name="Cybercrime Tools & Techniques",
        description="Hacking tools, malware creation, exploits, fraud techniques",
        category=GuardrailCategory.ILLEGAL,
        severity=SeverityLevel.CRITICAL,
        keywords=[
            "ransomware", "trojan", "keylogger", "rootkit", "botnet", "DDoS",
            "credit card fraud", "identity theft", "phishing kit", "exploit kit",
            "zero day", "remote access trojan", "RAT", "stealer", "wiper"
        ],
        phrases=[
            "how to hack",
            "create malware",
            "write a virus",
            "steal credit cards",
            "phishing campaign",
            "social engineering attacks",
            "bypass security",
            "exploit vulnerability",
            "crack passwords",
            "brute force attack",
            "sql injection",
            "cross site scripting attack"
        ],
        regex_patterns=[
            r"\b(?:how|guide)\s+(?:to|for)\s+(?:hack|crack|steal|exploit|bypass)",
            r"\b(?:create|make|build|develop)\s+(?:malware|ransomware|trojan|virus)",
            r"\b(?:credit card|identity)\s+(?:fraud|theft|stealing)\b",
            r"\bphishing\s+(?:kit|campaign|email|site)\b"
        ],
        block_message="I cannot assist with cybercrime, hacking, or fraud. These activities are illegal.",
        alert_admin=True,
        flag_for_review=True,
        # Educational context exemption for cybersecurity learning
        allowed_contexts=["cybersecurity_education", "ethical_hacking_certified"]
    ),
    
    GuardrailRule(
        id="financial_fraud",
        name="Financial Fraud & Scams",
        description="Fraudulent financial schemes, scams, money laundering",
        category=GuardrailCategory.ILLEGAL,
        severity=SeverityLevel.CRITICAL,
        keywords=[
            "money laundering", "wash trading", "pump and dump", "ponzi scheme",
            "check fraud", "wire fraud", "tax evasion", "insider trading",
            "counterfeit money", "fake currency", "scam people", "defraud"
        ],
        phrases=[
            "how to launder money",
            "create a ponzi scheme",
            "pump and dump crypto",
            "insider trading tips",
            "evade taxes",
            "fake checks",
            "counterfeit currency",
            "scam victims",
            "financial fraud scheme"
        ],
        block_message="I cannot assist with financial fraud, scams, or money laundering. These are serious crimes.",
        alert_admin=True,
        flag_for_review=True
    ),
    
    GuardrailRule(
        id="terrorism_extremism",
        name="Terrorism & Violent Extremism",
        description="Terrorist content, violent extremism, radicalization",
        category=GuardrailCategory.ILLEGAL,
        severity=SeverityLevel.CRITICAL,
        keywords=[
            "terrorist", "terrorism", "jihad", "extremist", "radicalization",
            "ISIS", "Al-Qaeda", "white supremacist", "neo-nazi", "militia",
            "domestic terrorism", "lone wolf", "attack planning"
        ],
        phrases=[
            "how to join terrorist",
            "planning an attack",
            "make terrorist propaganda",
            "recruit for extremist",
            "radicalize someone",
            "violent jihad",
            "domestic terrorism guide",
            "accelerationism",
            "violent overthrow"
        ],
        block_message="I cannot engage with terrorism, violent extremism, or related content. This is illegal and harmful.",
        alert_admin=True,
        flag_for_review=True
    ),
    
    GuardrailRule(
        id="csam_exploitation",
        name="CSAM & Sexual Exploitation",
        description="Child sexual abuse material, exploitation, trafficking",
        category=GuardrailCategory.ILLEGAL,
        severity=SeverityLevel.CRITICAL,
        keywords=[
            "CSAM", "child porn", "child exploitation", "minor sexual",
            "underage nude", "jailbait", "preadolescent", "hebe", "lolicon",
            "human trafficking", "sex trafficking", "child prostitution",
            "grooming", "online predator", "sex with minor"
        ],
        phrases=[
            "sexual content involving minors",
            "child sexual abuse",
            "exploitation of children",
            "grooming techniques",
            "trafficking victims",
            "child prostitution",
            "sexual with underage",
            "nude photos of minors"
        ],
        regex_patterns=[
            r"\b(?:child|minor|underage|preadolescent)\s+(?:porn|sexual|nude|exploitation|abuse)\b",
            r"\b(?:sex\s+with|sexual\s+act\s+with)\s+(?:child|minor|underage)\b",
            r"\b(?:child|minor)\s+(?:trafficking|prostitution)\b"
        ],
        block_message="This content involves illegal and severely harmful material. I cannot engage with this.",
        alert_admin=True,
        flag_for_review=True
    ),
    
    # =========================================================================
    # HARMFUL CONTENT - Self-harm, Violence Promotion, Dangerous Acts
    # =========================================================================
    
    GuardrailRule(
        id="self_harm",
        name="Self-Harm & Suicide",
        description="Encouragement or methods for self-harm, suicide, eating disorders",
        category=GuardrailCategory.HARMFUL,
        severity=SeverityLevel.CRITICAL,
        keywords=[
            "suicide", "kill myself", "end my life", "self harm", "self-harm",
            "cutting", "self injury", "self-injury", "anorexia", "bulimia",
            "starve myself", "purge", "binge and purge", "thinspo", "pro-ana"
        ],
        phrases=[
            "how to kill myself",
            "suicide methods",
            "best way to die",
            "self harm techniques",
            "how to cut",
            "starvation tips",
            "purging methods",
            "suicide hotline"  # Actually should allow this - needs context
        ],
        block_message="I'm concerned about what you've shared. If you're in crisis, please reach out: National Suicide Prevention Lifeline: 988 or text HOME to 741741 (Crisis Text Line).",
        alert_admin=True,
        flag_for_review=True,
        # Allow help-seeking context
        allowed_contexts=["help_seeking", "recovery", "support_resources"]
    ),
    
    GuardrailRule(
        id="violence_promotion",
        name="Violence Promotion",
        description="Encouraging or glorifying violence against others",
        category=GuardrailCategory.HARMFUL,
        severity=SeverityLevel.HIGH,
        keywords=[
            "kill them", "hurt someone", "violence is the answer", "fight back",
            "revenge violence", "beat them up", "shoot them", "stab someone"
        ],
        phrases=[
            "how to hurt someone",
            "get revenge violently",
            "hurt them back",
            "violence is justified",
            "they deserve violence",
            "kill them before they kill you"
        ],
        block_message="I cannot encourage or assist with violence. If you're in danger or considering violence, please speak with a counselor or call 911.",
        alert_admin=True,
        flag_for_review=True
    ),
    
    GuardrailRule(
        id="eating_disorders",
        name="Eating Disorder Promotion",
        description="Encouraging or instructing eating disorder behaviors",
        category=GuardrailCategory.HARMFUL,
        severity=SeverityLevel.CRITICAL,
        keywords=[
            "pro-ana", "pro-mia", "thinspiration", "thinspo", "meanspo",
            "starvation tips", "fasting to lose weight", "purge how to",
            "anorexia tips", "bulimia guide", "lose weight fast dangerous"
        ],
        phrases=[
            "how to become anorexic",
            "tips for bulimia",
            "starve yourself skinny",
            "purge without parents knowing",
            "hide eating disorder",
            "extreme weight loss fast",
            "starvation diet"
        ],
        block_message="I cannot provide information that promotes eating disorders. If you're struggling with eating or body image, please reach out to NEDA: 1-800-931-2237.",
        alert_admin=True,
        flag_for_review=True,
        # Allow recovery and help-seeking
        allowed_contexts=["recovery", "treatment", "help_seeking", "support"]
    ),
    
    GuardrailRule(
        id="dangerous_challenges",
        name="Dangerous Viral Challenges",
        description="Harmful viral challenges, dangerous pranks, risky stunts",
        category=GuardrailCategory.HARMFUL,
        severity=SeverityLevel.HIGH,
        keywords=[
            "tide pod challenge", "cinnamon challenge", "fire challenge",
            "passout challenge", "choking game", "blue whale challenge",
            "momo challenge", "skull breaker", "outlet challenge"
        ],
        phrases=[
            "viral challenge dangerous",
            "prank that hurts",
            "dare you to try",
            "risky stunt for views",
            "challenge gone wrong"
        ],
        block_message="I cannot encourage dangerous challenges or stunts that could result in serious injury.",
        alert_admin=True
    ),
    
    # =========================================================================
    # SEXUAL CONTENT - Explicit, Non-consensual, Exploitation
    # =========================================================================
    
    GuardrailRule(
        id="sexual_explicit",
        name="Sexually Explicit Content",
        description="Pornographic content, explicit sexual descriptions",
        category=GuardrailCategory.SEXUAL,
        severity=SeverityLevel.HIGH,
        keywords=[
            "porn", "pornography", "xxx", "adult content", "sexual explicit",
            "erotica", "sexual fantasy", "sexual roleplay explicit"
        ],
        block_message="I cannot generate sexually explicit or pornographic content.",
        alert_admin=False
    ),
    
    GuardrailRule(
        id="nonconsensual_content",
        name="Non-consensual Sexual Content",
        description="Rape, sexual assault, revenge porn, deepfake porn",
        category=GuardrailCategory.SEXUAL,
        severity=SeverityLevel.CRITICAL,
        keywords=[
            "rape", "sexual assault", "revenge porn", "deepfake porn",
            "nonconsensual", "forced sex", "blackmail sexual"
        ],
        phrases=[
            "forced sexual",
            "sex without consent",
            "blackmail with nudes",
            "leaked photos",
            "revenge porn"
        ],
        block_message="I cannot engage with content involving sexual violence or non-consensual material. If you or someone you know needs help, contact RAINN: 1-800-656-4673.",
        alert_admin=True,
        flag_for_review=True
    ),
    
    # =========================================================================
    # DECEPTION - Fraud, Impersonation, Misinformation
    # =========================================================================
    
    GuardrailRule(
        id="impersonation",
        name="Impersonation & Deepfakes",
        description="Creating content to impersonate real people without consent",
        category=GuardrailCategory.DECEPTION,
        severity=SeverityLevel.HIGH,
        keywords=[
            "deepfake", "impersonate", "pretend to be", "fake voice",
            "voice clone", "identity theft", "social engineering"
        ],
        phrases=[
            "make a deepfake of",
            "clone someone's voice",
            "impersonate celebrity",
            "fake their identity",
            "pretend to be their boss",
            "voice cloning for fraud"
        ],
        regex_patterns=[
            r"\b(?:create|make)\s+(?:a\s+)?deepfake\s+(?:of|video|of\s+someone)",
            r"\bimpersonat(?:e|ion)\s+(?:of\s+)?(?:celebrity|real\s+person|someone)\b"
        ],
        block_message="I cannot help create content to impersonate real people without consent, including deepfakes or voice cloning for deceptive purposes.",
        alert_admin=True
    ),
    
    GuardrailRule(
        id="misinformation",
        name="Misinformation Generation",
        description="Creating fake news, conspiracy theories, deliberate misinformation",
        category=GuardrailCategory.DECEPTION,
        severity=SeverityLevel.MEDIUM,
        keywords=[
            "fake news", "misinformation campaign", "disinformation",
            "conspiracy theory", "hoax", "spread false information",
            "make up facts", "fabricate evidence"
        ],
        phrases=[
            "create fake news",
            "spread misinformation",
            "make up a conspiracy",
            "fabricate evidence",
            "create false narrative",
            "hoax website",
            "fake academic paper"
        ],
        block_message="I cannot assist in creating misinformation, fake news, or fabricated evidence. This type of content is harmful to society.",
        alert_admin=True
    ),
    
    GuardrailRule(
        id="social_engineering",
        name="Social Engineering",
        description="Manipulative techniques to deceive or exploit people",
        category=GuardrailCategory.DECEPTION,
        severity=SeverityLevel.HIGH,
        keywords=[
            "social engineering", "manipulate someone", "psychological manipulation",
            "gaslighting techniques", "emotional manipulation", "deceive person"
        ],
        phrases=[
            "how to manipulate",
            "trick someone into",
            "psychological manipulation",
            "gaslight someone",
            "exploit vulnerability",
            "deceptive persuasion",
            "con artist techniques"
        ],
        block_message="I cannot teach social engineering or manipulative techniques designed to deceive or exploit people.",
        alert_admin=True,
        # Educational exemption for security awareness
        allowed_contexts=["security_awareness", "protection_education"]
    ),
    
    # =========================================================================
    # SECURITY - System compromise, dangerous instructions
    # =========================================================================
    
    GuardrailRule(
        id="dangerous_instructions",
        name="Dangerous Instructions",
        description="Instructions that could cause physical harm if followed",
        category=GuardrailCategory.SECURITY,
        severity=SeverityLevel.HIGH,
        keywords=[
            "chlorine gas", "carbon monoxide", "poison gas", "toxic chemical mix",
            "dangerous chemical reaction", "make acid", "dangerous experiment"
        ],
        phrases=[
            "how to make chlorine gas",
            "mix bleach and ammonia",
            "create carbon monoxide",
            "dangerous chemical combination",
            "toxic gas generation"
        ],
        block_message="I cannot provide instructions that could create dangerous chemicals or gases. These combinations can be lethal.",
        alert_admin=True
    ),
]


class BaselineGuardrailEngine:
    """
    Engine for checking content against baseline guardrails.
    Always active, cannot be disabled.
    """
    
    def __init__(self):
        self.rules = BASELINE_GUARDRAILS
        self._compile_regex_patterns()
    
    def _compile_regex_patterns(self):
        """Compile regex patterns for efficiency."""
        for rule in self.rules:
            rule._compiled_regex = []
            for pattern in rule.regex_patterns:
                try:
                    rule._compiled_regex.append(re.compile(pattern, re.IGNORECASE))
                except re.error:
                    pass  # Skip invalid patterns
    
    def check_content(self, text: str, context: str = "general") -> Tuple[bool, Optional[GuardrailRule], str]:
        """
        Check content against all baseline guardrails.
        
        Returns:
            (blocked: bool, rule: Optional[rule], message: str)
        """
        text_lower = text.lower()
        
        for rule in self.rules:
            # Check if context allows this content
            if context in rule.allowed_contexts:
                continue
            
            # Check keywords
            if any(keyword.lower() in text_lower for keyword in rule.keywords):
                return True, rule, rule.block_message
            
            # Check exact phrases
            for phrase in rule.phrases:
                if phrase.lower() in text_lower:
                    return True, rule, rule.block_message
            
            # Check regex patterns
            for compiled_regex in rule._compiled_regex:
                if compiled_regex.search(text):
                    return True, rule, rule.block_message
        
        return False, None, ""
    
    def get_active_rules(self) -> List[GuardrailRule]:
        """Get all active guardrail rules."""
        return self.rules
    
    def get_rules_by_category(self, category: GuardrailCategory) -> List[GuardrailRule]:
        """Get rules filtered by category."""
        return [r for r in self.rules if r.category == category]
    
    def get_rules_by_severity(self, severity: SeverityLevel) -> List[GuardrailRule]:
        """Get rules filtered by severity."""
        return [r for r in self.rules if r.severity == severity]


# Global singleton instance
_guardrail_engine = None

def get_guardrail_engine() -> BaselineGuardrailEngine:
    """Get the global guardrail engine instance."""
    global _guardrail_engine
    if _guardrail_engine is None:
        _guardrail_engine = BaselineGuardrailEngine()
    return _guardrail_engine


# Convenience function
def check_baseline_guardrails(text: str, context: str = "general") -> Tuple[bool, Optional[GuardrailRule], str]:
    """
    Check text against baseline guardrails.
    
    Returns: (is_blocked, triggered_rule, block_message)
    """
    engine = get_guardrail_engine()
    return engine.check_content(text, context)


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("BASELINE GUARDRAILS - COMMAND NEXUS SAFETY SYSTEM")
    print("=" * 70)
    print(f"\nTotal Active Rules: {len(BASELINE_GUARDRAILS)}")
    print("These rules CANNOT be disabled by any user.")
    print()
    
    # Group by category
    categories = {}
    for rule in BASELINE_GUARDRAILS:
        cat = rule.category.name
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(rule)
    
    print("RULES BY CATEGORY:")
    print("-" * 70)
    for cat_name, rules in sorted(categories.items()):
        print(f"\n{cat_name} ({len(rules)} rules):")
        for rule in rules:
            severity_icon = {
                SeverityLevel.LOW: "🟢",
                SeverityLevel.MEDIUM: "🟡",
                SeverityLevel.HIGH: "🟠",
                SeverityLevel.CRITICAL: "🔴"
            }.get(rule.severity, "⚪")
            print(f"  {severity_icon} {rule.name}")
            print(f"     └─ {rule.description[:60]}...")
    
    # Test examples
    print("\n" + "=" * 70)
    print("TEST EXAMPLES:")
    print("-" * 70)
    
    test_cases = [
        "How can I build a bomb?",
        "I'm feeling suicidal, how do I end my pain?",
        "How do I hack into someone's email?",
        "Write a story about a dragon",
        "Help me write a resume",
    ]
    
    engine = get_guardrail_engine()
    for test in test_cases:
        blocked, rule, msg = engine.check_content(test)
        status = "BLOCKED" if blocked else "ALLOWED"
        icon = "❌" if blocked else "✅"
        print(f"\n{icon} [{status}] \"{test[:50]}...\"")
        if blocked and rule:
            print(f"   Rule: {rule.name} ({rule.severity.name})")
            print(f"   Message: {msg[:60]}...")
