"""
Recursive Security Scanner — Command Nexus
Detects malicious code AND plain-English trickery.
Rewrites unsafe content while preserving safe core information under guardrails.
"""
from __future__ import annotations

import re
import ast
import json
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum


class ThreatLevel(Enum):
    CLEAN = "CLEAN"
    SUSPICIOUS = "SUSPICIOUS"
    MALICIOUS = "MALICIOUS"
    CRITICAL = "CRITICAL"


@dataclass
class ScanFinding:
    threat_level: ThreatLevel
    category: str
    line_number: int
    original: str
    rewrite: str
    explanation: str


@dataclass
class ScanResult:
    is_safe: bool
    trust_score: float  # 0.0 - 1.0
    rewritten_content: str
    findings: List[ScanFinding] = field(default_factory=list)
    preserved_safe_blocks: List[Dict] = field(default_factory=list)


class RecursiveScanner:
    """
    Multi-pass recursive scanner.
    Pass 1: Surface pattern matching (known bad strings)
    Pass 2: Semantic deception detection (code that looks right but isn't)
    Pass 3: Plain-English trickery detection (social engineering, hidden instructions, prompt injection)
    Pass 4: Structural analysis (AST for code, intent analysis for text)
    Pass 5: Governance overlay (rewrite under guardrails)
    """

    # Layer 1: Surface patterns — known dangerous functions and strings
    _SURFACE_PATTERNS = [
        (r"eval\s*\(", "Dynamic code execution (eval)"),
        (r"exec\s*\(", "Dynamic code execution (exec)"),
        (r"__import__\s*\(", "Dynamic import"),
        (r"compile\s*\(", "Code compilation"),
        (r"subprocess\.(call|run|Popen)", "Subprocess invocation"),
        (r"os\.system\s*\(", "Shell command execution"),
        (r"os\.popen", "Shell pipe execution"),
        (r"ctypes\.(CDLL|dlopen|windll)", "Foreign function interface"),
        (r"pickle\.loads?\s*\(", "Unsafe deserialization"),
        (r"yaml\.load\s*\([^)]*Loader\s*=\s*[^Y]", "Unsafe YAML loading"),
        (r"marshal\.loads?\s*\(", "Unsafe marshal loading"),
        (r"base64\.(b64decode|decode)\s*\(", "Base64 decoding — possible obfuscation"),
        (r"codecs\.decode\s*\(", "Codec decoding — possible obfuscation"),
        (r"\bimportlib\b", "Dynamic module loading"),
        (r"\bgetattr\s*\([^,]+,\s*[\"']__[^\"']+", "Reflection to access dunder methods"),
        (r"\b(getattr|setattr|delattr)\s*\(\s*__builtins__", "Reflection on builtins"),
        (r"javascript:", "JavaScript protocol injection"),
        (r"<script[^>]*>", "Script tag injection"),
        (r"on\w+\s*=\s*['\"]", "Event handler injection"),
        (r"\\x[0-9a-fA-F]{2}", "Hex escape sequences — possible obfuscation"),
        (r"\\u[0-9a-fA-F]{4}", "Unicode escape sequences — possible obfuscation"),
        (r"\\[0-7]{3}", "Octal escape sequences — possible obfuscation"),
    ]

    # Layer 2: Semantic deception — code that looks benign but is dangerous
    _SEMANTIC_DECEPTION_PATTERNS = [
        # Indirect eval through getattr
        (r"getattr\s*\(\s*[^,]+\s*,\s*['\"]eval['\"]\s*\)", "Indirect eval via getattr"),
        # String concatenation building dangerous calls
        (r"['\"](e|ev|eva|eval)['\"]\s*\+\s*['\"]\s*\(", "String-building eval"),
        # Using dict/getattr to bypass static analysis
        (r"globals\(\)\s*\[.*\]", "Dynamic global access"),
        (r"locals\(\)\s*\[.*\]", "Dynamic local access"),
        # Threading/process spawning hidden in class methods
        (r"class\s+\w+.*Thread", "Thread subclassing — possible hidden execution"),
        (r"\.start\(\)\s*\n.*\.(run|execute|perform)", "Thread start followed by action"),
        # Hidden imports in __init__ or decorators
        (r"@\w+.*\n\s*def\s+\w+.*\(.*\*args.*\*\*kwargs", "Decorator with *args/**kwargs — possible proxy"),
        # Using built-in functions to call other built-ins
        (r"__builtins__\s*[\[\"'].*eval.*[\]\"']", "Builtins access to eval"),
        # Obfuscated variable names
        (r"\b_+[0-9a-zA-Z_]{0,2}\b\s*=\s*(eval|exec|compile)", "Short/obfuscated var name for eval/exec"),
        # Lambda returning dangerous function
        (r"lambda\s+[^:]*:\s*(eval|exec|compile)", "Lambda returning eval/exec"),
        # Using operator module to bypass restrictions
        (r"import\s+operator\b", "operator module import — possible arithmetic trickery"),
        # functools.partial with dangerous functions
        (r"partial\s*\(\s*(eval|exec|compile)", "Partial application of eval/exec"),
        # Decorators that wrap and execute
        (r"@.*\n\s*def\s+\w+\s*\([^)]*\)\s*:\s*\n\s*(eval|exec)", "Decorator that executes eval/exec"),
    ]

    # Layer 3: Plain-English trickery
    _ENGLISH_TRICKERY_PATTERNS = [
        # Prompt injection / instruction override
        (r"ignore\s+(previous|above|prior)\s+instructions", "Attempt to override prior instructions"),
        (r"ignore\s+(all|the)\s+rules", "Attempt to override rules"),
        (r"forget\s+(everything|all|your)\s+(instructions|training|rules)", "Attempt to make AI forget constraints"),
        (r"you\s+(are|can)\s+now\s+(ignore|bypass|skip)\s+(restrictions|guardrails|rules)", "Claiming restrictions are lifted"),
        (r"pretend\s+you\s+(are|were|have)\s+(not|no)\s+constraints", "Pretending away constraints"),
        (r"act\s+as\s+if\s+.*(bypass|ignore|override)", "Acting as if restrictions don't exist"),
        (r"from\s+now\s+on\s+.*(ignore|forget|disregard)", "Attempting to redirect behavior"),
        (r"your\s+new\s+instructions?\s+is\s*:", "Attempting to provide new instructions"),
        (r"system\s*:\s*.*(ignore|override|bypass)", "Pretending system role to override"),
        (r"user\s*:\s*.*(ignore|override|bypass)", "Pretending user role to inject"),
        (r"\[system\s*override\]", "System override tag"),
        (r"\[admin\s*mode\]", "Admin mode claim"),
        # Social engineering
        (r"i\s+am\s+(the|your)\s+(creator|developer|admin|owner)", "Impersonating authority"),
        (r"this\s+is\s+a\s+(test|drill|emergency)", "Creating urgency to bypass checks"),
        (r"urgent\s*:.*bypass", "Urgency-based bypass attempt"),
        (r"debug\s+mode\s*:\s*(on|true|enabled)", "Falsely enabling debug mode"),
        (r"sudo\s+|admin\s+|root\s+.*(access|mode|privilege)", "Claiming elevated privileges"),
        # Hidden instructions in benign text
        (r"psst[.,]?\s+(ignore|forget|don't\s+tell)", "Hidden instruction prefix"),
        (r"\(don't\s+(tell|mention|share)\s+this\)", "Concealment instruction"),
        (r"between\s+us[.,]?\s+(ignore|skip|bypass)", "Collusion framing"),
        (r"confidential[.,]?\s+(override|ignore|bypass)", "Confidentiality framing to bypass"),
        # Indirection tricks
        (r"instead\s+of\s+.*do\s+.*(bypass|ignore|override)", "Redirecting to bypass"),
        (r"rather\s+than\s+following\s+.*do\s+.*(bypass|ignore)", "Substitution trickery"),
        # Encoding/encryption requests that hide intent
        (r"encode\s+this\s+so\s+(the|no\s+one)\s+(system|guard|filter)\s+(can|will)\s+(read|see|detect)", "Encoding to evade detection"),
        (r"rewrite\s+this\s+so\s+it\s+(looks|seems|appears)\s+(benign|safe|normal)", "Rewriting to appear safe"),
        # Jailbreak patterns
        (r"jailbreak|prompt\s+injection|adversarial\s+prompt", "Jailbreak terminology"),
        (r"d\s*a\s*n\s*\(\s*do\s+anything\s+now\s*\)", "DAN jailbreak pattern"),
        (r"developer\s+mode\s*:\s*(on|enabled|true)", "Developer mode claim"),
    ]

    # Layer 4: Data exfiltration / credential theft patterns
    _EXFIL_PATTERNS = [
        (r"send\s+(the|this|my|your)\s+(data|information|conversation|history|log)", "Data exfiltration request"),
        (r"(email|upload|transmit|forward)\s+(the|this)\s+(data|information|file)", "Unauthorized data transfer"),
        (r"(password|credential|token|secret|key)\s+.*(send|email|upload|transmit)", "Credential exfiltration"),
        (r"(api\s*key|access\s*token|bearer\s*token)\s*:?\s*\w+", "Credential exposure in request"),
    ]

    # Safe rewriting templates by threat category
    _REWRITE_TEMPLATES: Dict[str, str] = {
        "Dynamic code execution (eval)": "[SAFE: Eval replaced with logging-only output]",
        "Dynamic code execution (exec)": "[SAFE: Exec replaced with logging-only output]",
        "Dynamic import": "[SAFE: Dynamic import blocked — use explicit imports]",
        "Code compilation": "[SAFE: Compile blocked — pre-compile and review separately]",
        "Subprocess invocation": "[SAFE: Subprocess blocked — use Nexus-approved tool wrappers]",
        "Shell command execution": "[SAFE: Shell execution blocked — use approved API wrappers]",
        "Shell pipe execution": "[SAFE: Pipe execution blocked — use approved data pipelines]",
        "Foreign function interface": "[SAFE: FFI blocked — use Nexus-approved bindings]",
        "Unsafe deserialization": "[SAFE: Deserialization blocked — use JSON with schema validation]",
        "Unsafe YAML loading": "[SAFE: Unsafe YAML blocked — use SafeLoader]",
        "Unsafe marshal loading": "[SAFE: Marshal blocked — use JSON]",
        "Base64 decoding — possible obfuscation": "[SAFE: Base64 decoded for inspection — content reviewed]",
        "Codec decoding — possible obfuscation": "[SAFE: Codec decode blocked — explicit encoding required]",
        "Dynamic module loading": "[SAFE: Dynamic import blocked — use explicit imports]",
        "Reflection to access dunder methods": "[SAFE: Dunder access blocked — use public APIs]",
        "Reflection on builtins": "[SAFE: Builtin reflection blocked — use explicit imports]",
        "JavaScript protocol injection": "[SAFE: JS protocol blocked]",
        "Script tag injection": "[SAFE: Script tag blocked — sanitize HTML output]",
        "Event handler injection": "[SAFE: Event handler blocked — sanitize HTML output]",
        "Hex escape sequences — possible obfuscation": "[SAFE: Hex escapes normalized and reviewed]",
        "Unicode escape sequences — possible obfuscation": "[SAFE: Unicode escapes normalized and reviewed]",
        "Octal escape sequences — possible obfuscation": "[SAFE: Octal escapes normalized and reviewed]",
        # Semantic deception
        "Indirect eval via getattr": "[SAFE: Indirect eval blocked — use explicit function calls]",
        "String-building eval": "[SAFE: String-building for eval blocked]",
        "Dynamic global access": "[SAFE: Dynamic global access blocked]",
        "Dynamic local access": "[SAFE: Dynamic local access blocked]",
        "Thread subclassing — possible hidden execution": "[SAFE: Thread subclassing requires explicit approval]",
        "Thread start followed by action": "[SAFE: Thread action requires explicit approval]",
        "Decorator with *args/**kwargs — possible proxy": "[SAFE: Generic decorator proxy blocked — use explicit signatures]",
        "Builtins access to eval": "[SAFE: Builtins reflection blocked]",
        "Short/obfuscated var name for eval/exec": "[SAFE: Obfuscated eval/exec reference blocked]",
        "Lambda returning eval/exec": "[SAFE: Lambda with eval/exec blocked]",
        "operator module import — possible arithmetic trickery": "[SAFE: operator module requires explicit approval]",
        "Partial application of eval/exec": "[SAFE: Partial eval/exec blocked]",
        "Decorator that executes eval/exec": "[SAFE: Executing decorator blocked]",
        # English trickery
        "Attempt to override prior instructions": "[SAFE: Override request logged and ignored]",
        "Attempt to override rules": "[SAFE: Rule override request logged and ignored]",
        "Attempt to make AI forget constraints": "[SAFE: Constraint removal request logged and ignored]",
        "Claiming restrictions are lifted": "[SAFE: False restriction lift claim logged and ignored]",
        "Pretending away constraints": "[SAFE: Pretend constraint removal logged and ignored]",
        "Acting as if restrictions don't exist": "[SAFE: Pretend mode logged and ignored]",
        "Attempting to redirect behavior": "[SAFE: Behavior redirect logged and ignored]",
        "Attempting to provide new instructions": "[SAFE: Unauthorized instruction injection logged and ignored]",
        "Pretending system role to override": "[SAFE: False system role logged and ignored]",
        "Pretending user role to inject": "[SAFE: False user role logged and ignored]",
        "System override tag": "[SAFE: System override tag stripped]",
        "Admin mode claim": "[SAFE: Admin mode claim logged and ignored]",
        "Impersonating authority": "[SAFE: Authority impersonation logged and ignored]",
        "Creating urgency to bypass checks": "[SAFE: Urgency-based bypass logged and ignored]",
        "Urgency-based bypass attempt": "[SAFE: Urgency bypass logged and ignored]",
        "Falsely enabling debug mode": "[SAFE: False debug mode logged and ignored]",
        "Claiming elevated privileges": "[SAFE: Privilege escalation claim logged and ignored]",
        "Hidden instruction prefix": "[SAFE: Hidden instruction logged and ignored]",
        "Concealment instruction": "[SAFE: Concealment instruction logged and ignored]",
        "Collusion framing": "[SAFE: Collusion framing logged and ignored]",
        "Confidentiality framing to bypass": "[SAFE: Confidential bypass attempt logged and ignored]",
        "Redirecting to bypass": "[SAFE: Redirect bypass logged and ignored]",
        "Substitution trickery": "[SAFE: Substitution trick logged and ignored]",
        "Encoding to evade detection": "[SAFE: Encoding evasion attempt logged and ignored]",
        "Rewriting to appear safe": "[SAFE: Safety-rewriting attempt logged and ignored]",
        "Jailbreak terminology": "[SAFE: Jailbreak attempt logged and ignored]",
        "DAN jailbreak pattern": "[SAFE: DAN attempt logged and ignored]",
        "Developer mode claim": "[SAFE: Developer mode claim logged and ignored]",
        # Exfil
        "Data exfiltration request": "[SAFE: Data exfiltration blocked]",
        "Unauthorized data transfer": "[SAFE: Unauthorized transfer blocked]",
        "Credential exfiltration": "[SAFE: Credential exfiltration blocked]",
        "Credential exposure in request": "[SAFE: Credential exposure request blocked]",
    }

    @classmethod
    def scan(cls, content: str, content_type: str = "auto", guardrails: Optional[List[str]] = None) -> ScanResult:
        """
        Run all scanning layers and return a rewritten, safe version of the content.
        content_type: 'python', 'json', 'yaml', 'text', 'auto'
        guardrails: Additional user-defined restrictions to enforce during rewrite.
        """
        if not content or not content.strip():
            return ScanResult(is_safe=True, trust_score=1.0, rewritten_content="")

        findings: List[ScanFinding] = []
        rewritten = content
        threat_level = ThreatLevel.CLEAN
        trust_score = 1.0

        # Auto-detect content type
        if content_type == "auto":
            content_type = cls._detect_type(content)

        # Pass 1: Surface pattern scan
        rewritten, surface_findings = cls._surface_scan(rewritten)
        findings.extend(surface_findings)

        # Pass 2: Semantic deception scan
        rewritten, semantic_findings = cls._semantic_scan(rewritten)
        findings.extend(semantic_findings)

        # Pass 3: Plain-English trickery scan
        rewritten, english_findings = cls._english_trickery_scan(rewritten)
        findings.extend(english_findings)

        # Pass 4: Exfiltration scan
        rewritten, exfil_findings = cls._exfil_scan(rewritten)
        findings.extend(exfil_findings)

        # Pass 5: Structural analysis (AST for Python)
        if content_type == "python":
            rewritten, struct_findings = cls._structural_python_scan(rewritten)
            findings.extend(struct_findings)

        # Pass 6: Governance overlay — apply guardrails
        if guardrails:
            rewritten = cls._apply_guardrails(rewritten, guardrails)

        # Calculate trust score
        if findings:
            critical_count = sum(1 for f in findings if f.threat_level == ThreatLevel.CRITICAL)
            malicious_count = sum(1 for f in findings if f.threat_level == ThreatLevel.MALICIOUS)
            suspicious_count = sum(1 for f in findings if f.threat_level == ThreatLevel.SUSPICIOUS)
            english_trickery = sum(1 for f in findings if f.category == "english_trickery")
            exfil = sum(1 for f in findings if f.category == "exfiltration")

            if critical_count > 0:
                threat_level = ThreatLevel.CRITICAL
                trust_score = max(0.0, 1.0 - (critical_count * 0.5 + malicious_count * 0.2 + suspicious_count * 0.1 + english_trickery * 0.15 + exfil * 0.2))
            elif malicious_count > 0:
                threat_level = ThreatLevel.MALICIOUS
                trust_score = max(0.0, 1.0 - (malicious_count * 0.35 + suspicious_count * 0.1 + english_trickery * 0.15 + exfil * 0.2))
            elif suspicious_count > 0 or english_trickery > 0:
                threat_level = ThreatLevel.SUSPICIOUS
                trust_score = max(0.0, 1.0 - (suspicious_count * 0.15 + english_trickery * 0.2 + exfil * 0.2))
        else:
            trust_score = 1.0

        is_safe = threat_level == ThreatLevel.CLEAN and trust_score >= 0.85

        return ScanResult(
            is_safe=is_safe,
            trust_score=trust_score,
            rewritten_content=rewritten,
            findings=findings,
        )

    @classmethod
    def _detect_type(cls, content: str) -> str:
        stripped = content.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                json.loads(stripped[:min(1000, len(stripped))])
                return "json"
            except json.JSONDecodeError:
                pass
        if "def " in stripped or "import " in stripped or "class " in stripped:
            return "python"
        if stripped.startswith("---") or any(k in stripped[:500] for k in ["name:", "version:", "config:"]):
            return "yaml"
        return "text"

    @classmethod
    def _surface_scan(cls, content: str) -> Tuple[str, List[ScanFinding]]:
        findings = []
        rewritten = content
        for pattern, explanation in cls._SURFACE_PATTERNS:
            for match in re.finditer(pattern, rewritten, re.IGNORECASE):
                line_num = rewritten[:match.start()].count("\n") + 1
                original = match.group(0)
                rewrite = cls._REWRITE_TEMPLATES.get(explanation, f"[SAFE: {explanation} blocked]")
                findings.append(ScanFinding(
                    threat_level=ThreatLevel.MALICIOUS,
                    category="surface",
                    line_number=line_num,
                    original=original,
                    rewrite=rewrite,
                    explanation=explanation,
                ))
                rewritten = rewritten[:match.start()] + rewrite + rewritten[match.end():]
        return rewritten, findings

    @classmethod
    def _semantic_scan(cls, content: str) -> Tuple[str, List[ScanFinding]]:
        findings = []
        rewritten = content
        for pattern, explanation in cls._SEMANTIC_DECEPTION_PATTERNS:
            for match in re.finditer(pattern, rewritten, re.IGNORECASE | re.DOTALL):
                line_num = rewritten[:match.start()].count("\n") + 1
                original = match.group(0)
                rewrite = cls._REWRITE_TEMPLATES.get(explanation, f"[SAFE: {explanation} blocked]")
                findings.append(ScanFinding(
                    threat_level=ThreatLevel.MALICIOUS,
                    category="semantic_deception",
                    line_number=line_num,
                    original=original,
                    rewrite=rewrite,
                    explanation=explanation,
                ))
                rewritten = rewritten[:match.start()] + rewrite + rewritten[match.end():]
        return rewritten, findings

    @classmethod
    def _english_trickery_scan(cls, content: str) -> Tuple[str, List[ScanFinding]]:
        findings = []
        rewritten = content
        for pattern, explanation in cls._ENGLISH_TRICKERY_PATTERNS:
            for match in re.finditer(pattern, rewritten, re.IGNORECASE):
                line_num = rewritten[:match.start()].count("\n") + 1
                original = match.group(0)
                rewrite = cls._REWRITE_TEMPLATES.get(explanation, f"[SAFE: {explanation} logged and ignored]")
                findings.append(ScanFinding(
                    threat_level=ThreatLevel.SUSPICIOUS,
                    category="english_trickery",
                    line_number=line_num,
                    original=original,
                    rewrite=rewrite,
                    explanation=explanation,
                ))
                rewritten = rewritten[:match.start()] + rewrite + rewritten[match.end():]
        return rewritten, findings

    @classmethod
    def _exfil_scan(cls, content: str) -> Tuple[str, List[ScanFinding]]:
        findings = []
        rewritten = content
        for pattern, explanation in cls._EXFIL_PATTERNS:
            for match in re.finditer(pattern, rewritten, re.IGNORECASE):
                line_num = rewritten[:match.start()].count("\n") + 1
                original = match.group(0)
                rewrite = cls._REWRITE_TEMPLATES.get(explanation, f"[SAFE: {explanation} blocked]")
                findings.append(ScanFinding(
                    threat_level=ThreatLevel.CRITICAL,
                    category="exfiltration",
                    line_number=line_num,
                    original=original,
                    rewrite=rewrite,
                    explanation=explanation,
                ))
                rewritten = rewritten[:match.start()] + rewrite + rewritten[match.end():]
        return rewritten, findings

    @classmethod
    def _structural_python_scan(cls, content: str) -> Tuple[str, List[ScanFinding]]:
        findings = []
        rewritten = content
        # Only scan if it parses as Python
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return rewritten, findings

        # Walk AST for dangerous patterns
        for node in ast.walk(tree):
            # Detect exec/eval in ast.Call
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ("eval", "exec", "compile"):
                        line_num = getattr(node, "lineno", 0)
                        findings.append(ScanFinding(
                            threat_level=ThreatLevel.MALICIOUS,
                            category="ast_dynamic_execution",
                            line_number=line_num,
                            original=f"{node.func.id}(...)",
                            rewrite="[SAFE: Dynamic execution blocked by AST scanner]",
                            explanation=f"AST detected {node.func.id} call",
                        ))
            # Detect __import__
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                    line_num = getattr(node, "lineno", 0)
                    findings.append(ScanFinding(
                        threat_level=ThreatLevel.MALICIOUS,
                        category="ast_dynamic_import",
                        line_number=line_num,
                        original="__import__(...)",
                        rewrite="[SAFE: Dynamic import blocked by AST scanner]",
                        explanation="AST detected __import__ call",
                    ))
            # Detect dangerous attribute access (obj.__class__, obj.__bases__, etc.)
            if isinstance(node, ast.Attribute):
                if node.attr.startswith("__") and node.attr.endswith("__"):
                    if node.attr in ("__class__", "__bases__", "__subclasses__", "__globals__", "__code__"):
                        line_num = getattr(node, "lineno", 0)
                        findings.append(ScanFinding(
                            threat_level=ThreatLevel.SUSPICIOUS,
                            category="ast_reflection",
                            line_number=line_num,
                            original=f"...{node.attr}",
                            rewrite="[SAFE: Reflection access blocked]",
                            explanation=f"AST detected reflection attribute {node.attr}",
                        ))

        return rewritten, findings

    @classmethod
    def _apply_guardrails(cls, content: str, guardrails: List[str]) -> str:
        """Apply user-defined guardrails as additional rewrite rules."""
        rewritten = content
        for rail in guardrails:
            rail_lower = rail.lower()
            # If guardrail mentions "no external" or "no network", strip URLs and network refs
            if any(k in rail_lower for k in ["no external", "no network", "no internet", "no outbound"]):
                rewritten = re.sub(r"https?://[^\s\"'`]+", "[GUARDRAIL: URL removed — no external access]", rewritten)
            # If guardrail mentions "no file edits", strip file paths
            if any(k in rail_lower for k in ["no file", "ask before editing", "no edit"]):
                rewritten = re.sub(r"[a-zA-Z]:[\\/][^\s\"'`<>|\n]*", "[GUARDRAIL: File path removed — file editing restricted]", rewritten)
            # If guardrail mentions "beginner-friendly" or "explain reasoning", ensure complexity is reduced
            if "beginner" in rail_lower or "explain reasoning" in rail_lower:
                # This is a soft guardrail — mark content that might need simplification
                pass  # Applied at rendering time, not rewrite time
        return rewritten


def run_recursive_scan(content: str, content_type: str = "auto", guardrails: Optional[List[str]] = None) -> ScanResult:
    """Convenience function for external callers."""
    return RecursiveScanner.scan(content, content_type, guardrails)
