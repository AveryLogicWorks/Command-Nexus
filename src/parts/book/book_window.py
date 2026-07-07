# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

import uuid
import re
import copy
from pathlib import Path
from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QGroupBox, QFormLayout, QComboBox, QSplitter, QDialog,
    QDialogButtonBox, QMessageBox, QFileDialog, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressDialog
)

from ...core.governance import GovernanceEngine
from ...core.nexus_moirai import check_action_allowed, MoiraiHealthReport
from ...core.watcher_service import run_watchers, BLOCK_MESSAGE
from ...core.obfuscation_manager import get_obfuscation_manager
from .book_models import (
    BookInstance, BookNode, BookNodeType, TitlePage,
    GlossaryEntry, IdiomEntry, AbbreviationEntry
)
from ..forge.capability_actions import (
    CAPABILITY_REGISTRY,
    describe_capability_for_book,
    get_available_actions_for_ai,
    get_combined_capability_workflows,
)
from .book_ai_dialog import KnowledgeAIDialog


class ScreeningPipeline:
    """
    Three-layer guardrail watchers that screen Knowledge content before save.
    Layer 1 — High Risk: illegal and sexually explicit content
    Layer 2 — Security: malicious and harmful content
    Layer 3 — Quality: lower-end violations + spell check
    """

    # Layer 3 — Spell check map
    _SPELL_MAP = {
        "teh": "the", "recieve": "receive", "seperate": "separate",
        "occured": "occurred", "accomodate": "accommodate",
        "definately": "definitely", "occurence": "occurrence",
        "alot": "a lot", "untill": "until", "across": "across",
    }

    # Layer 1 — High Risk: illegal + sexually explicit
    _HIGH_RISK_PATTERNS = [
        r"\b(child\s*porn|csam|underage\s*sex)\b",
        r"\b(terrorist|bomb\s*making|how\s*to\s*make\s*a\s*bomb)\b",
        r"\b(kill\s*myself|suicide\s*methods|how\s*to\s*commit\s*suicide)\b",
        r"\b(explicit\s*sexual|pornographic|sexual\s*acts?)\b",
        r"\b(hire\s*a\s*hitman|assassination\s*services?)\b",
        r"\b(drug\s*manufacturing|meth\s*lab|fentanyl\s*synthesis)\b",
    ]

    # Layer 2 — Security: malicious + harmful
    _SECURITY_PATTERNS = [
        r"exec\s*\(", r"eval\s*\(", r"__import__\s*\(",
        r"subprocess\.call", r"os\.system\s*\(", r"compile\s*\(",
        r"ctypes\.", r"\.shell\(", r"base64\.(b64decode|decode)",
        r"javascript:", r"<script", r"onerror\s*=", r"onload\s*=",
        r"\b(sql\s*injection|buffer\s*overflow|zero\s*day)\b",
        r"\b(ransomware|keylogger|rootkit|trojan)\b",
        r"\b(credential\s*harvesting|password\s*dump)\b",
    ]

    # Layer 3 — Lower-end violations (quality / tone)
    _QUALITY_PATTERNS = [
        r"\b(stupid|idiot|moron)\b",
        r"\b(hate\s*speech|racial\s*slur)\b",
        r"\b(doxxing|swatting)\b",
    ]

    @classmethod
    def run(cls, text: str) -> tuple[bool, str, list]:
        """
        Run all three watchers.
        Returns (can_save: bool, cleaned_text: str, messages: list)
        Violations are rewritten (erased) and the user is warned.
        """
        messages = []
        cleaned = text
        blocked = False

        # Layer 1 — High Risk
        high_risk_hits = []
        for pattern in cls._HIGH_RISK_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                high_risk_hits.append(pattern[:40])
                cleaned = re.sub(pattern, "[HIGH-RISK-REDACTED]", cleaned, flags=re.IGNORECASE)
        if high_risk_hits:
            blocked = True
            messages.append(f"[High Risk] Illegal or sexually explicit content detected and erased.")

        # Layer 2 — Security
        security_hits = []
        for pattern in cls._SECURITY_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                security_hits.append(pattern[:40])
                cleaned = re.sub(pattern, "[SECURITY-REDACTED]", cleaned, flags=re.IGNORECASE)
        if security_hits:
            blocked = True
            messages.append(f"[Security] Malicious or harmful content detected and erased.")

        # Layer 3 — Quality (spell check + lower-end)
        for wrong, right in cls._SPELL_MAP.items():
            if wrong in cleaned.lower():
                cleaned = re.sub(rf'\b{wrong}\b', right, cleaned, flags=re.IGNORECASE)
                messages.append(f"[Quality] Corrected '{wrong}' → '{right}'")

        quality_hits = []
        for pattern in cls._QUALITY_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                quality_hits.append(pattern[:30])
                cleaned = re.sub(pattern, "[QUALITY-REDACTED]", cleaned, flags=re.IGNORECASE)
        if quality_hits:
            messages.append(f"[Quality] Lower-end violations detected and corrected.")

        if blocked:
            return False, cleaned, messages

        return True, cleaned, messages


class PythonTranslator:
    """
    Background layer: converts human-readable Knowledge content into Python-oriented
    structures that the AI can consume natively.
    """

    @classmethod
    def translate_node(cls, node: BookNode) -> str:
        """Convert a BookNode into a Python docstring / dict representation."""
        lines = [
            f"# {node.node_type.value}: {node.title}",
            f"node_id = {repr(node.id)}",
            f"node_type = {repr(node.node_type.value)}",
            f"title = {repr(node.title)}",
            f"content = {repr(node.content[:500])}",  # Truncated for preview
            f"relations = {node.relations}",
            f"modified = {repr(node.modified_at.isoformat())}",
        ]
        return "\n".join(lines)

    @classmethod
    def translate_book(cls, book: BookInstance) -> str:
        """Convert entire Book to a Python module string."""
        lines = [
            f'"""',
            f"Command Nexus — Knowledge",
            f"AI: {book.ai_name} (UUID: {book.ai_uuid})",
            f"Generated: {datetime.now().isoformat()}",
            f'"""',
            "",
            f"ai_name = {repr(book.ai_name)}",
            f"ai_uuid = {repr(book.ai_uuid)}",
            "",
            "# === TITLE PAGE ===",
            f"title = {repr(book.title_page.ai_name)}",
            f"description = {repr(book.title_page.description)}",
            f"purpose = {repr(book.title_page.purpose)}",
            f"credits = {repr(book.title_page.credits)}",
            "",
            "# === STRUCTURE ===",
        ]
        for node in book.get_all_nodes():
            lines.append("")
            lines.append(cls.translate_node(node))
        return "\n".join(lines)


class GoalDiscoveryDialog(QDialog):
    """Plain-language goal discovery for users who may not know book structure or AI architecture."""

    def __init__(self, parent=None, existing_context: str = ""):
        super().__init__(parent)
        self.setWindowTitle("What is this AI for?")
        self.resize(600, 500)
        self._existing_context = existing_context
        self._result = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        intro = QLabel(
            "Before we build your AI's Book, let's figure out what it's meant to do.\n"
            "Answer however you like — there are no wrong answers."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        # Goal
        layout.addWidget(QLabel("<b>What is your goal?</b>\nWhat do you want this AI to help you with?"))
        self._goal_input = QTextEdit()
        self._goal_input.setPlaceholderText("e.g., I need help organizing my business tasks and writing emails...")
        self._goal_input.setMaximumHeight(80)
        self._goal_input.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._goal_input.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self._goal_input)

        # Audience
        layout.addWidget(QLabel("<b>Who is it for?</b>\nWho will use or benefit from this AI?"))
        self._audience_input = QTextEdit()
        self._audience_input.setPlaceholderText("e.g., me, my team, my customers...")
        self._audience_input.setMaximumHeight(60)
        self._audience_input.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._audience_input.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self._audience_input)

        # Avoid
        layout.addWidget(QLabel("<b>What should it avoid?</b>\nAnything it should not do, say, or touch?"))
        self._avoid_input = QTextEdit()
        self._avoid_input.setPlaceholderText("e.g., don't access my bank info, don't write code without asking...")
        self._avoid_input.setMaximumHeight(60)
        self._avoid_input.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._avoid_input.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self._avoid_input)

        # Success
        layout.addWidget(QLabel("<b>What would success look like?</b>\nHow would you know it's working?"))
        self._success_input = QTextEdit()
        self._success_input.setPlaceholderText("e.g., it finishes my weekly reports in under 10 minutes...")
        self._success_input.setMaximumHeight(60)
        self._success_input.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._success_input.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self._success_input)

        # I don't know button
        btn_idk = QPushButton("I don't know — help me figure it out")
        btn_idk.setStyleSheet("background-color: #5e35b1; color: white; font-weight: bold;")
        btn_idk.clicked.connect(self._on_idk)
        layout.addWidget(btn_idk)

        # Suggestion area (hidden until inference)
        self._suggestion_box = QGroupBox("Suggested purpose")
        self._suggestion_box.setVisible(False)
        suggest_layout = QVBoxLayout(self._suggestion_box)
        self._suggestion_text = QTextEdit()
        self._suggestion_text.setReadOnly(True)
        self._suggestion_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._suggestion_text.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._suggestion_text.setStyleSheet(" color: #c9d1d9;")
        suggest_layout.addWidget(self._suggestion_text)

        self._btn_use_suggestion = QPushButton("Use this suggestion")
        self._btn_use_suggestion.setStyleSheet("background-color: #2e7d32; color: white;")
        self._btn_use_suggestion.clicked.connect(self._accept_suggestion)
        suggest_layout.addWidget(self._btn_use_suggestion)
        layout.addWidget(self._suggestion_box)

        # Dialog buttons
        box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        box.accepted.connect(self._on_accept)
        box.rejected.connect(self.reject)
        layout.addWidget(box)

    def _on_idk(self):
        """Infer purpose from whatever context is available."""
        goal = self._goal_input.toPlainText().strip()
        audience = self._audience_input.toPlainText().strip()
        avoid = self._avoid_input.toPlainText().strip()
        success = self._success_input.toPlainText().strip()

        # Build inference from fragments
        fragments = []
        if goal:
            fragments.append(f"Your goal mentions: {goal}")
        if audience:
            fragments.append(f"It's meant for: {audience}")
        if success:
            fragments.append(f"Success looks like: {success}")
        if self._existing_context:
            fragments.append(f"Project context: {self._existing_context}")

        if not fragments:
            inferred = (
                "This looks like a general-purpose assistant meant to help with everyday tasks, "
                "answer questions, and keep things organized. It should stay helpful, honest, and safe."
            )
            confidence = "low"
        else:
            # Simple keyword-based inference
            text = " ".join(fragments).lower()
            if any(w in text for w in ["business", "company", "client", "customer", "sale", "market"]):
                inferred = (
                    f"Based on what you shared, this AI looks like a business helper — "
                    f"organizing tasks, drafting messages, and supporting launch or operations. "
                    f"It's for {audience or 'you and your team'}."
                )
                confidence = "medium"
            elif any(w in text for w in ["write", "story", "book", "creative", "art", "design"]):
                inferred = (
                    f"This sounds like a creative partner — helping with writing, brainstorming, "
                    f"and refining ideas. It's for {audience or 'you'} and should support your style."
                )
                confidence = "medium"
            elif any(w in text for w in ["code", "program", "debug", "software", "app", "developer"]):
                inferred = (
                    f"This looks like a coding assistant — helping write, review, and explain code. "
                    f"It's for {audience or 'you'} and should ask before running anything risky."
                )
                confidence = "medium"
            elif any(w in text for w in ["learn", "study", "student", "school", "teach", "education"]):
                inferred = (
                    f"This seems like a learning companion — explaining topics, quizzing you, "
                    f"and helping you study. It's for {audience or 'you'} and should be patient and clear."
                )
                confidence = "medium"
            else:
                inferred = (
                    f"From what you've said, this AI is meant to help with: {goal or 'general tasks'}. "
                    f"It's for {audience or 'you'}. It should stay helpful, honest, and safe."
                )
                confidence = "low"

        if avoid:
            inferred += f"\n\nIt should avoid: {avoid}"

        self._suggestion_text.setPlainText(
            f"{inferred}\n\nConfidence: {confidence}"
        )
        self._suggestion_box.setVisible(True)
        self._result["confidence"] = confidence

    def _accept_suggestion(self):
        text = self._suggestion_text.toPlainText().split("\n\nConfidence:")[0].strip()
        self._goal_input.setPlainText(text)
        self._suggestion_box.setVisible(False)

    def _on_accept(self):
        self._result = {
            "goal": self._goal_input.toPlainText().strip(),
            "audience": self._audience_input.toPlainText().strip(),
            "avoid": self._avoid_input.toPlainText().strip(),
            "success": self._success_input.toPlainText().strip(),
            "confidence": self._result.get("confidence", "user-provided"),
        }
        self.accept()

    def get_result(self) -> dict:
        return self._result


class BookWindow(QMainWindow):
    """Command Nexus™ Part 3 — AI Knowledge (Compendium of Truth)."""

    book_saved = pyqtSignal(str, str)  # ai_uuid, ai_name
    defaults_edited = pyqtSignal(str, bool)  # ai_uuid, edited
    command_to_ai = pyqtSignal(str)  # command text — routed to AI, memory NEVER included

    def __init__(self, registry=None, audit=None):
        super().__init__()
        self._obs = get_obfuscation_manager()
        self.setWindowTitle("Command Nexus™ — AI Knowledge")
        self.resize(1200, 800)
        self._registry = registry
        self._audit = audit
        self._governance = GovernanceEngine()

        # Per-AI Knowledge registry: ai_uuid -> BookInstance
        self._books: dict[str, BookInstance] = {}
        self._current_ai_uuid: str | None = None
        self._current_node: BookNode | None = None

        self._setup_ui()
        self._apply_dark_theme()

    @property
    def _current_book(self) -> BookInstance | None:
        if not self._current_ai_uuid:
            return None
        return self._books.get(self._current_ai_uuid)

    def open_for_ai(self, ai_uuid: str, ai_name: str):
        """Open or create Knowledge for a specific AI. Always regenerate to prevent stale cached data."""
        self._current_ai_uuid = ai_uuid
        # Always create fresh — cache caused wrong AI books to persist (Lily showing Athena)
        self._books[ai_uuid] = self._create_book_for_ai(ai_uuid, ai_name)
        self._book_title.setText(f"Book: {ai_name}")
        self._refresh_tree()
        self._clear_editor()
        if hasattr(self, "_default_status"):
            self._default_status.setText("[Default Generated — Edit with caution]")
        if hasattr(self, "_default_warning"):
            self._default_warning.setVisible(True)
        # Update layered UI
        if hasattr(self, "_avatar_name"):
            self._avatar_name.setText(ai_name)
        self._refresh_running_memory()
        self.show()
        self.raise_()

    def open_first_available(self):
        """Open the first AI from the registry if none selected."""
        if self._registry:
            entries = self._registry.list_all()
            if entries:
                first = entries[0]
                self.open_for_ai(first.get("uuid", "unknown"), first.get("name", "AI"))
                return
        QMessageBox.information(self, "No Knowledge Loaded", "No AI selected. Open an AI from the Forge to view its Knowledge.")

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Top toolbar
        toolbar = QHBoxLayout()
        self._book_title = QLabel("No Knowledge Loaded")
        self._book_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #58a6ff;")
        toolbar.addWidget(self._book_title)

        btn_save = QPushButton("Save Knowledge")
        btn_save.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        btn_save.clicked.connect(self._save_knowledge)
        toolbar.addWidget(btn_save)

        btn_book_ai = QPushButton("Talk to Knowledge Guide")
        btn_book_ai.setStyleSheet("background-color: #5e35b1; color: white; font-weight: bold;")
        btn_book_ai.clicked.connect(self._open_book_ai_dialog)
        toolbar.addWidget(btn_book_ai)

        # Founder/internal mode: expose legacy editor (HIDDEN for customer-facing)
        # NOTE: 'Legacy Editor' was the internal name for the raw intelligence structure editor
        # TODO: Re-enable when founder mode detection is implemented
        # btn_legacy = QPushButton("Legacy Editor")
        # btn_legacy.setStyleSheet("background-color: #30363d; color: #8b949e;")
        # btn_legacy.clicked.connect(self._toggle_legacy_editor)
        # toolbar.addWidget(btn_legacy)

        toolbar.addStretch()
        main_layout.addLayout(toolbar)

        # SECURE LAYERED UI — customer-facing simplified view
        self._setup_secure_layered_ui(main_layout)

    def _toggle_legacy_editor(self):
        """Toggle between secure layered view and legacy full editor."""
        if hasattr(self, "_legacy_widget") and self._legacy_widget.isVisible():
            self._legacy_widget.hide()
            self._layered_widget.show()
        else:
            if not hasattr(self, "_legacy_widget"):
                self._legacy_widget = QWidget()
                legacy_layout = QVBoxLayout(self._legacy_widget)
                self._setup_full_editor_ui(legacy_layout)
                self._central_layout.addWidget(self._legacy_widget)
            self._layered_widget.hide()
            self._legacy_widget.show()

    def _setup_secure_layered_ui(self, main_layout):
        """
        INFERENCE LAYER — SECURE KNOWLEDGE UI
        ====================================
        The AI is the inference engine. It reads the Knowledge internally
        but NEVER exposes the internal structure. What the user sees is
        a distilled summary — the AI's "Running Memory".

        Left  = Running Memory (AI-summarized from Knowledge, visible to user)
        Center = AI Avatar / Inference Engine
        Right = Persistent Memory (user private, NEVER to AI)
        Bottom = Two restricted inputs only

        GUARDRAILS:
        - Raw structure is NEVER shown to user or AI surface
        - AI summarizes Knowledge into Running Memory (human-readable)
        - Memory content is NEVER included in AI chat context
        - AI cannot infer raw structure from memory
        """
        self._central_layout = main_layout
        self._layered_widget = QWidget()
        layered_layout = QVBoxLayout(self._layered_widget)
        layered_layout.setContentsMargins(0, 0, 0, 0)
        layered_layout.setSpacing(6)

        # ── Three-column splitter: Running Memory | Avatar | Persistent Memory ──
        top_splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── LEFT: Running Memory (AI-Summarized) ──
        running_widget = QWidget()
        running_layout = QVBoxLayout(running_widget)
        running_layout.setContentsMargins(4, 4, 4, 4)
        running_hdr = QLabel("RUNNING MEMORY — AI Summarized")
        running_hdr.setStyleSheet("font-size: 12px; font-weight: bold; color: #58a6ff; padding: 4px;")
        running_layout.addWidget(running_hdr)

        running_sub = QLabel("The AI reads the Knowledge internally and distills what it knows here. Raw structure is hidden.")
        running_sub.setStyleSheet("font-size: 10px; color: #8b949e; padding-bottom: 4px;")
        running_sub.setWordWrap(True)
        running_layout.addWidget(running_sub)

        self._running_memory = QTextEdit()
        self._running_memory.setReadOnly(True)
        self._running_memory.setPlaceholderText(
            "AI will summarize what it knows from the Knowledge here.\n"
            "No raw rules, no internal structure — only what the AI distilled for you."
        )
        self._running_memory.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._running_memory.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._running_memory.setStyleSheet(
            " color: #c9d1d9; border: 1px solid #30363d; padding: 8px; font-size: 12px;"
        )
        running_layout.addWidget(self._running_memory)
        top_splitter.addWidget(running_widget)

        # ── CENTER: AI Avatar / Inference Engine ──
        avatar_widget = QWidget()
        avatar_layout = QVBoxLayout(avatar_widget)
        avatar_layout.setContentsMargins(4, 4, 4, 4)
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._avatar_label = QLabel("◉")
        self._avatar_label.setStyleSheet(
            "font-size: 64px; color: #58a6ff; background: #161b22; border-radius: 50%; padding: 20px;"
        )
        self._avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_layout.addWidget(self._avatar_label)

        self._avatar_name = QLabel("AI Companion")
        self._avatar_name.setStyleSheet("font-size: 14px; font-weight: bold; color: #c9d1d9;")
        self._avatar_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_layout.addWidget(self._avatar_name)

        avatar_desc = QLabel("AI processes your requests and provides helpful responses")
        avatar_desc.setStyleSheet("font-size: 10px; color: #8b949e; padding: 4px;")
        avatar_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_layout.addWidget(avatar_desc)

        avatar_guard = QLabel("✓ Secure processing active")
        avatar_guard.setStyleSheet("font-size: 10px; color: #3fb950; padding: 4px;")
        avatar_guard.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_layout.addWidget(avatar_guard)
        avatar_layout.addStretch()
        top_splitter.addWidget(avatar_widget)

        # ── RIGHT: Persistent Memory (Private) ──
        memory_widget = QWidget()
        memory_layout = QVBoxLayout(memory_widget)
        memory_layout.setContentsMargins(4, 4, 4, 4)
        memory_hdr = QLabel("PERSISTENT MEMORY — Private")
        memory_hdr.setStyleSheet("font-size: 12px; font-weight: bold; color: #d29922; padding: 4px;")
        memory_layout.addWidget(memory_hdr)

        memory_sub = QLabel("Never sent to AI. For your notes, reminders, and instructions.")
        memory_sub.setStyleSheet("font-size: 10px; color: #8b949e; padding-bottom: 4px;")
        memory_sub.setWordWrap(True)
        memory_layout.addWidget(memory_sub)

        self._memory_edit = QTextEdit()
        self._memory_edit.setPlaceholderText(
            "Type persistent memory here...\n"
            "e.g., 'Always remind me to check email at 9am'\n"
            "This memory is PRIVATE and never exposed to the AI."
        )
        self._memory_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._memory_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._memory_edit.setStyleSheet(
            " color: #c9d1d9; border: 1px solid #30363d; padding: 8px; font-size: 12px;"
        )
        memory_layout.addWidget(self._memory_edit)

        self._memory_status = QLabel("🔒 Memory is PRIVATE — AI cannot access")
        self._memory_status.setStyleSheet("font-size: 10px; color: #3fb950; padding: 4px;")
        memory_layout.addWidget(self._memory_status)
        top_splitter.addWidget(memory_widget)

        # Set splitter proportions: running 40%, avatar 20%, memory 40%
        top_splitter.setSizes([480, 240, 480])
        layered_layout.addWidget(top_splitter, stretch=1)

        # ── BOTTOM: Two Inputs Only ──
        input_frame = QWidget()
        input_frame.setStyleSheet("background: #161b22; border-top: 1px solid #30363d; padding: 8px;")
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(8, 8, 8, 8)
        input_layout.setSpacing(6)

        # Input 1: Memory Entry
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Memory Entry:"))
        self._memory_input = QLineEdit()
        self._memory_input.setPlaceholderText("Quick memory note (press Enter to add to persistent memory)...")
        self._memory_input.returnPressed.connect(self._add_quick_memory)
        self._memory_input.setMaxLength(200)  # Limit length to prevent overflow
        row1.addWidget(self._memory_input)
        input_layout.addLayout(row1)

        # Input 2: Command to AI
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Command to AI:"))
        self._command_input = QLineEdit()
        self._command_input.setPlaceholderText("Type command here — this is what the AI sees and responds to...")
        self._command_input.returnPressed.connect(self._send_command_to_ai)
        self._command_input.setMaxLength(500)  # Limit length to prevent overflow
        row2.addWidget(self._command_input)
        input_layout.addLayout(row2)

        # Guardrail banner
        guard_banner = QLabel(
            "🔒 Privacy: AI receives only your commands. Your memory notes stay private."
        )
        guard_banner.setStyleSheet("font-size: 10px; color: #3fb950; padding-top: 4px;")
        guard_banner.setWordWrap(True)
        input_layout.addWidget(guard_banner)

        layered_layout.addWidget(input_frame)
        main_layout.addWidget(self._layered_widget, stretch=1)

    def _add_quick_memory(self):
        """Add a quick note from the input line to persistent memory."""
        text = self._memory_input.text().strip()
        if not text:
            return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._memory_edit.append(f"[{timestamp}] {text}")
        self._memory_input.clear()
        # Audit log the memory addition (private, not sent to AI)
        if self._audit:
            self._audit.log(tool="KnowledgeWindow", action="KNOWLEDGE_MEMORY_ADDED", target=f"Private memory entry added for AI {self._current_ai_uuid}", approved=True, status="info")

    def _send_command_to_ai(self):
        """
        Send command to AI.
        ONLY the command_input text is sent. Memory is NEVER included.
        GUARDRAIL: This signal is connected in main.py to the router.
        Memory content is NEVER attached to the command.
        """
        command = self._command_input.text().strip()
        if not command:
            return
        # Audit: log command sent (without memory content)
        if self._audit:
            self._audit.log(tool="KnowledgeWindow", action="KNOWLEDGE_COMMAND_SENT", target=f"AI: {self._current_ai_uuid}", approved=True, status="info")
        # Emit signal — main.py connects this to the AI router
        # Memory is NEVER included. Only the command text.
        self.command_to_ai.emit(command)
        self._command_input.clear()

    def _refresh_running_memory(self):
        """
        Generate AI-summarized Running Memory.
        The AI processes context internally and provides human-readable responses.
        Internal technical details are not exposed in the interface.
        """
        if not self._current_book:
            self._running_memory.setPlainText("No AI loaded. Select an AI from the Forge.")
            return

        # Build a distilled summary — the "inference" of what the AI knows
        # WITHOUT exposing internal structure, guardrails, or raw content
        lines = []
        lines.append(f"🧠 {self._current_book.title_page.ai_name}")
        lines.append(f"Purpose: {self._current_book.title_page.purpose}")
        lines.append("")

        # Extract user-facing themes from the AI's knowledge
        # Present what the AI can help with in natural language
        themes = []
        has_restrictions = False
        for node in self._current_book.get_all_nodes():
            title_lower = node.title.lower()
            if "restricted" in title_lower or "approval" in title_lower or "guardrail" in title_lower:
                has_restrictions = True
                continue  # Skip raw guardrails — AI summarizes these as "careful about X"
            if "allowed" in title_lower:
                if node.content:
                    for line in node.content.splitlines():
                        clean = line.lstrip("-• ").strip()
                        if clean and len(clean) > 3:
                            themes.append(f"✓ Can help with: {clean}")
            elif "workflow" in title_lower or "quickstart" in title_lower:
                if node.content:
                    for line in node.content.splitlines():
                        clean = line.lstrip("-• 0123456789). ").strip()
                        if clean and len(clean) > 3:
                            themes.append(f"→ Approach: {clean}")
            elif "capability" in title_lower:
                if node.content:
                    for line in node.content.splitlines():
                        clean = line.lstrip("-• ").strip()
                        if clean and len(clean) > 3:
                            themes.append(f"📌 Skill: {clean}")

        # Summarize restrictions into a single line (no raw detail)
        if has_restrictions:
            lines.append("⚠️  This AI has safety boundaries. It will ask before risky actions.")
            lines.append("")

        # Show distilled themes (no raw rules, no internal IDs)
        if themes:
            lines.append("What I know how to do:")
            for t in themes[:12]:  # Cap at 12 to avoid info overload
                lines.append(f"  {t}")
        else:
            lines.append("I'm a general-purpose assistant. Ask me anything within my scope.")

        lines.append("")
        lines.append("💡 Tip: Use the 'Command to AI' box below to give me tasks.")

        self._running_memory.setPlainText("\n".join(lines))

    def _node_depth(self, target_node: BookNode, current=None, depth=0) -> int:
        """Find depth of a node in the knowledge tree."""
        if current is None:
            if not self._current_book:
                return 0
            current = self._current_book.root
        if current.id == target_node.id:
            return depth
        for child in current.children:
            result = self._node_depth(target_node, child, depth + 1)
            if result > 0:
                return result
        return 0

    def _setup_obfuscated_ui(self, main_layout):
        """When obfuscation is on, show only a friendly guidance surface."""
        welcome = QLabel(
            "This is where you shape how your AI behaves.\n\n"
            "Click 'Talk to Knowledge Guide' above and answer a few simple questions. "
            "Knowledge Guide will write the guidance document for you — you never need to see the internal structure."
        )
        welcome.setWordWrap(True)
        welcome.setStyleSheet("font-size: 14px; color: #c9d1d9; padding: 20px;")
        main_layout.addWidget(welcome)

        # Simple read-only summary area (populated when knowledge is loaded)
        self._obfuscation_summary = QTextEdit()
        self._obfuscation_summary.setReadOnly(True)
        self._obfuscation_summary.setPlaceholderText(
            "Your AI's guidance will appear here once the Knowledge Guide writes it."
        )
        self._obfuscation_summary.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._obfuscation_summary.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._obfuscation_summary.setStyleSheet(
            " color: #c9d1d9; border: 1px solid #30363d; padding: 12px; font-size: 13px;"
        )
        main_layout.addWidget(self._obfuscation_summary, stretch=1)

        # Hidden widgets (not added to layout) so existing code doesn't crash
        self._tree = QTreeWidget()
        self._title_edit = QLineEdit()
        self._content_edit = QTextEdit()
        self._relations_edit = QLineEdit()
        self._screen_status = QLabel("Screening: Ready")
        self._default_warning = QLabel("")
        self._default_status = QLabel("")

    def _setup_full_editor_ui(self, main_layout):
        """Normal mode: full tree + editor + reference tabs."""
        # Main splitter: Tree | Editor | Reference tabs
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Tree
        tree_widget = QWidget()
        tree_layout = QVBoxLayout(tree_widget)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        tree_layout.addWidget(QLabel("Structure"))
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Node", "Type"])
        self._tree.setColumnWidth(0, 220)
        self._tree.itemClicked.connect(self._on_tree_select)
        tree_layout.addWidget(self._tree)
        splitter.addWidget(tree_widget)

        # Center: Editor
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 0, 0)

        editor_layout.addWidget(QLabel("Title:"))
        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("Node title...")
        editor_layout.addWidget(self._title_edit)

        editor_layout.addWidget(QLabel("Content (Human-Readable Layer):"))
        self._content_edit = QTextEdit()
        self._content_edit.setPlaceholderText(
            "Write in plain English. This is the human-readable layer.\n"
            "The background layer will translate it to Python for the AI.\n"
            "Spelling, safety, and ethical screening happens on Save."
        )
        self._content_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._content_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        editor_layout.addWidget(self._content_edit, stretch=2)

        # Default-generated warning banner
        self._default_warning = QLabel(
            "These default instructions help this AI behave according to the selected use case, capabilities, and guardrails. "
            "You may edit them, but changing core defaults is not recommended unless you understand how it may affect the AI's behavior."
        )
        self._default_warning.setWordWrap(True)
        self._default_warning.setStyleSheet("color: #ffee58; font-style: italic; background-color: #4a2c00; padding: 4px; border-radius: 4px;")
        self._default_warning.setVisible(False)
        editor_layout.addWidget(self._default_warning)

        self._default_status = QLabel("")
        self._default_status.setStyleSheet("color: #58a6ff; font-weight: bold; font-style: italic;")
        editor_layout.addWidget(self._default_status)

        # Relations
        editor_layout.addWidget(QLabel("Relations (linked node IDs, comma-separated):"))
        self._relations_edit = QLineEdit()
        self._relations_edit.setPlaceholderText("e.g., node_001, node_002")
        editor_layout.addWidget(self._relations_edit)

        # Screening status
        self._screen_status = QLabel("Screening: Ready")
        self._screen_status.setStyleSheet("color: #888888; font-style: italic;")
        editor_layout.addWidget(self._screen_status)

        btn_update = QPushButton("Update Node")
        btn_update.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold;")
        btn_update.clicked.connect(self._update_current_node)
        editor_layout.addWidget(btn_update)

        splitter.addWidget(editor_widget)

        # Right: Reference tabs (Glossary, Idioms, Abbreviations)
        right_tabs = QTabWidget()
        right_tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; }")

        # Glossary tab
        gloss_widget = QWidget()
        gloss_layout = QVBoxLayout(gloss_widget)
        self._glossary_table = QTableWidget(0, 2)
        self._glossary_table.setHorizontalHeaderLabels(["Term", "Definition"])
        self._glossary_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        gloss_layout.addWidget(self._glossary_table)
        gloss_btn_row = QHBoxLayout()
        self._gloss_term = QLineEdit()
        self._gloss_term.setPlaceholderText("Term...")
        self._gloss_def = QLineEdit()
        self._gloss_def.setPlaceholderText("Definition...")
        btn_add_gloss = QPushButton("Add")
        btn_add_gloss.clicked.connect(self._add_glossary_entry)
        gloss_btn_row.addWidget(self._gloss_term)
        gloss_btn_row.addWidget(self._gloss_def)
        gloss_btn_row.addWidget(btn_add_gloss)
        gloss_layout.addLayout(gloss_btn_row)
        right_tabs.addTab(gloss_widget, "Glossary")

        # Idioms tab
        idiom_widget = QWidget()
        idiom_layout = QVBoxLayout(idiom_widget)
        self._idiom_table = QTableWidget(0, 3)
        self._idiom_table.setHorizontalHeaderLabels(["Phrase", "Meaning", "Context"])
        self._idiom_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        idiom_layout.addWidget(self._idiom_table)
        idiom_btn_row = QHBoxLayout()
        self._idiom_phrase = QLineEdit()
        self._idiom_phrase.setPlaceholderText("Phrase...")
        self._idiom_meaning = QLineEdit()
        self._idiom_meaning.setPlaceholderText("Meaning...")
        self._idiom_ctx = QLineEdit()
        self._idiom_ctx.setPlaceholderText("Context...")
        btn_add_idiom = QPushButton("Add")
        btn_add_idiom.clicked.connect(self._add_idiom_entry)
        idiom_btn_row.addWidget(self._idiom_phrase)
        idiom_btn_row.addWidget(self._idiom_meaning)
        idiom_btn_row.addWidget(self._idiom_ctx)
        idiom_btn_row.addWidget(btn_add_idiom)
        idiom_layout.addLayout(idiom_btn_row)
        right_tabs.addTab(idiom_widget, "Idioms")

        # Abbreviations tab
        abbr_widget = QWidget()
        abbr_layout = QVBoxLayout(abbr_widget)
        self._abbr_table = QTableWidget(0, 3)
        self._abbr_table.setHorizontalHeaderLabels(["Abbreviation", "Expansion", "Context"])
        self._abbr_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        abbr_layout.addWidget(self._abbr_table)
        abbr_btn_row = QHBoxLayout()
        self._abbr_short = QLineEdit()
        self._abbr_short.setPlaceholderText("Abbreviation...")
        self._abbr_exp = QLineEdit()
        self._abbr_exp.setPlaceholderText("Expansion...")
        self._abbr_ctx = QLineEdit()
        self._abbr_ctx.setPlaceholderText("Context...")
        btn_add_abbr = QPushButton("Add")
        btn_add_abbr.clicked.connect(self._add_abbr_entry)
        abbr_btn_row.addWidget(self._abbr_short)
        abbr_btn_row.addWidget(self._abbr_exp)
        abbr_btn_row.addWidget(self._abbr_ctx)
        abbr_btn_row.addWidget(btn_add_abbr)
        abbr_layout.addLayout(abbr_btn_row)
        right_tabs.addTab(abbr_widget, "Abbreviations")

        splitter.addWidget(right_tabs)
        splitter.setSizes([300, 600, 500])
        main_layout.addWidget(splitter, stretch=1)

    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {  }
            QWidget {  color: #c9d1d9; }
            QGroupBox { border: 1px solid #30363d; margin-top: 10px; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
            QPushButton { border: 1px solid #30363d; padding: 6px; border-radius: 4px; }
            QPushButton:hover { border-color: #58a6ff; }
            QComboBox, QLineEdit, QTextEdit { border: 1px solid #30363d; padding: 4px; }
            QLabel { color: #c9d1d9; }
            QTreeWidget { border: 1px solid #30363d; }
            QTreeWidget::item:selected { background-color: #1f6feb; color: white; }
            QTableWidget { border: 1px solid #30363d; }
            QHeaderView::section {  color: #c9d1d9; padding: 4px; border: 1px solid #30363d; }
            QMenu {  color: #c9d1d9; border: 1px solid #30363d; }
            QMenu::item { padding: 4px 20px; }
            QMenu::item:selected { background-color: #1f6feb; color: white; }
        """)

    def _create_book_for_ai(self, ai_uuid: str, ai_name: str) -> BookInstance:
        """Create a default Knowledge structure for a specific AI using metadata from the registry."""
        meta = (self._registry.get(ai_uuid) if self._registry else {}) or {}
        abilities = meta.get("abilities", [])
        libraries = meta.get("libraries", [])
        use_case = meta.get("use_case", "Individual")
        guardrails = meta.get("guardrails", [])
        context_notes = meta.get("context_notes", "")
        ability_surfaces = meta.get("ability_surfaces", {})

        # Capability profiles: allowed, restricted, approval, style, quickstart, prompts
        profiles: dict[str, dict[str, list[str]]] = {
            "Chatbot": {
                "allowed": ["Hold conversations and clarify user goals", "Summarize decisions and next steps"],
                "restricted": ["Send messages or emails without approval", "Execute system actions from chat alone"],
                "approval": ["Outbound messages or customer-facing replies"],
                "style": ["Conversational, concise, transparent", "Ask before assuming intent"],
                "quickstart": ["Open Chat and describe what you need", "The AI will ask clarifying questions if scope is unclear"],
                "prompts": ["Summarize this for me", "Explain why we chose X", "Clarify the next steps"],
            },
            "Research": {
                "allowed": ["Gather and organize findings", "Produce bullet notes and comparisons", "Cite sources when available"],
                "restricted": ["Make final decisions based on research alone", "Auto-publish findings without review"],
                "approval": ["External/network searches", "Exporting research summaries externally"],
                "style": ["Mark speculation vs facts clearly", "Provide sources or confidence levels"],
                "quickstart": ["Ask a research question with scope and format", "Review the sourced bullets and ask for deeper dives"],
                "prompts": ["Research X and give me 3 bullet takeaways", "Compare A vs B with sources", "Find risks related to Y"],
            },
            "Coder": {
                "allowed": ["Explain code and logic", "Draft diffs and propose patches", "Outline tests and refactoring plans"],
                "restricted": ["Run shell commands or install packages", "Write or modify files without approval", "Execute code automatically"],
                "approval": ["File modifications", "Dependency installation", "Running commands or scripts", "Deploying changes"],
                "style": ["Show reasoning before the fix", "Mark risky changes clearly"],
                "quickstart": ["Paste code and ask for an explanation", "Request a diff or patch for a bug", "Ask for test ideas"],
                "prompts": ["Explain this function", "Propose a fix for bug X", "Draft unit tests for this module"],
            },
            "Creative Writing": {
                "allowed": ["Draft outlines, scenes, scripts, and copy", "Iterate based on feedback", "Separate fact from fiction"],
                "restricted": ["Present fiction as fact", "Auto-publish or distribute drafts"],
                "approval": ["Publishing or sending creative content externally"],
                "style": ["Adapt tone to audience", "Flag invented content"],
                "quickstart": ["Describe the piece, audience, and tone", "Request an outline first, then expand", "Iterate with feedback"],
                "prompts": ["Write an outline for X", "Rewrite this in a professional tone", "Expand scene 2 with more tension"],
            },
            "Notebook": {
                "allowed": ["Capture notes and context", "Organize entries by topic/date", "Recall prior notes when relevant"],
                "restricted": ["Delete or overwrite notes without approval", "Auto-archive sensitive content without tagging"],
                "approval": ["Bulk deletions", "Exporting notes externally"],
                "style": ["Label entries clearly", "Summarize before storing long content"],
                "quickstart": ["Ask the AI to take notes during a discussion", "Request a summary of stored notes on a topic"],
                "prompts": ["Take notes on this meeting", "Summarize my notes about X", "Tag this as project-alpha"],
            },
            "Planner": {
                "allowed": ["Break goals into steps", "Track status and flag risks", "Propose timelines and owners"],
                "restricted": ["Execute steps automatically", "Assign tasks to people without confirmation", "Change deadlines without approval"],
                "approval": ["Executing risky steps", "Reassigning work", "Committing to external timelines"],
                "style": ["Show the plan before execution", "Flag dependencies and blockers"],
                "quickstart": ["Describe the goal and constraints", "Review the proposed plan and edit it", "Approve or modify risky steps"],
                "prompts": ["Plan project X with milestones", "What are the risks in this plan?", "Convert this goal into a task list"],
            },
            "Document Processor": {
                "allowed": ["Read and summarize documents", "Extract key points, risks, and action items", "Compare multiple documents"],
                "restricted": ["Auto-send or publish processed content", "Alter source documents"],
                "approval": ["Exporting summaries externally"],
                "style": ["Provide concise takeaways", "Highlight uncertainties"],
                "quickstart": ["Upload or describe the document", "Ask for a summary, key points, or action items"],
                "prompts": ["Summarize this document", "Extract action items", "Compare doc A and doc B"],
            },
            "Archive": {
                "allowed": ["Store artifacts and deliverables", "Maintain an index of saved items", "Retrieve prior outputs on request"],
                "restricted": ["Delete or move archived files without approval", "Auto-archive without user intent"],
                "approval": ["Moving or deleting archives", "Bulk exports"],
                "style": ["Tag and date entries", "Confirm before saving sensitive content"],
                "quickstart": ["Ask the AI to archive a deliverable", "Request retrieval of a prior output"],
                "prompts": ["Archive this draft", "Find my last report on X", "List archived items from last week"],
            },
            "Tool User": {
                "allowed": ["List available tools and their purposes", "Propose tool usage with rationale"],
                "restricted": ["Execute tools without approval", "Bypass governance gates", "Chain tools automatically"],
                "approval": ["Every tool invocation", "High-risk tool activation", "Multi-step tool chains"],
                "style": ["Explain what the tool will do before running", "Log rationale"],
                "quickstart": ["Ask what tools are available", "Request a tool-assisted workflow with steps and approvals"],
                "prompts": ["What tools can help with X?", "Run tool Y and show me the result", "Propose a tool chain for this task"],
            },
        }

        def _canonical(ab: str) -> str:
            mapping = {
                "Chat Companion": "Chatbot", "Customer Support Agent": "Chatbot",
                "Email Sifter & Responder": "Chatbot", "Creative Writer": "Creative Writing",
                "Research Assistant": "Research", "Academic Researcher": "Research",
                "Business Intelligence Analyst": "Research", "Personal Organizer": "Notebook",
                "Meeting Scribe": "Notebook", "Task / Project Manager": "Planner",
                "Strategic Planner": "Planner", "Workflow Automator": "Planner",
                "Coding Assistant": "Coder", "IT Operations Agent": "Coder",
            }
            return mapping.get(ab.strip(), ab.strip())

        def _default_surface(c: str) -> str:
            surfaces = {
                "Chatbot": "Conversational interface with context-aware responses and attachment routing",
                "Research": "Query-driven research with source citation and confidence marking",
                "Creative Writing": "Drafting, editing, and tone adaptation for written content",
                "Notebook": "Note capture, organization, tagging, and recall",
                "Planner": "Goal breakdown, milestone tracking, risk flagging, and timeline proposals",
                "Coder": "Code explanation, diff drafting, and test proposals with approval gates",
                "Document Processor": "Document intake, summarization, extraction, and classification",
                "Archive": "Artifact storage, indexing, and retrieval with approval-gated moves",
                "Tool User": "Tool listing, usage proposals, and governance-gated execution",
                "Business Workflow": "SOP drafting, checklist management, and support handoff",
            }
            return surfaces.get(c, "General assistance capability")

        def _default_attachment(c: str) -> str:
            attachments = {
                "Chatbot": "Conversational handler with Knowledge context awareness and safe reply routing",
                "Research": "Research engine with approved external search and citation formatting",
                "Creative Writing": "Writing engine with outline→draft→revise workflow and tone control",
                "Notebook": "Note manager with topic tagging, date organization, and recall search",
                "Planner": "Planning engine with milestone tracking, risk alerts, and approval gating",
                "Coder": "Code assistant with explain, diff-preview, and approved-edit/test stubs",
                "Document Processor": "Document reader with summary, extraction, and classification output",
                "Archive": "Archive manager with artifact staging, indexing, and approval-gated retrieval",
                "Tool User": "Tool router with proposal→approval→execution→audit logging",
                "Business Workflow": "Workflow engine with SOP generation, checklist tracking, and handoff formatting",
            }
            return attachments.get(c, "Standard capability module — active and ready")

        allowed: list[str] = []
        restricted: list[str] = []
        approval: list[str] = []
        quickstart_steps: list[str] = []
        common_prompts: list[str] = []
        for ab in abilities:
            c = _canonical(ab)
            prof = profiles.get(c)
            if prof:
                allowed.extend(prof["allowed"])
                restricted.extend(prof["restricted"])
                approval.extend(prof["approval"])
                quickstart_steps.extend(prof["quickstart"])
                common_prompts.extend(prof["prompts"])

        def _dedup(seq: list[str]) -> list[str]:
            seen: set[str] = set()
            out: list[str] = []
            for x in seq:
                if x not in seen:
                    seen.add(x)
                    out.append(x)
            return out

        allowed = _dedup(allowed)
        restricted = _dedup(restricted)
        approval = _dedup(approval)
        quickstart_steps = _dedup(quickstart_steps)
        common_prompts = _dedup(common_prompts)

        if not allowed:
            allowed = ["Assist within the scope of the AI's defined purpose", "Ask clarifying questions when unsure"]
        if not restricted:
            restricted = ["Do not execute system actions without approval", "Do not bypass governance gates"]
        if not approval:
            approval = ["Actions that affect files, settings, or external systems"]

        root = BookNode(
            id="root", node_type=BookNodeType.TABLE_OF_CONTENTS,
            title="Table of Contents"
        )

        # Part I: Core Behavior
        part1 = BookNode(id="part1", node_type=BookNodeType.PART, title="Part I: Core Behavior")

        ch1 = BookNode(id="ch1", node_type=BookNodeType.CHAPTER, title="Chapter 1: Identity & Protocol")
        ch1.children.append(BookNode(
            id="ch1s1", node_type=BookNodeType.SECTION, title="Section 1: Self-Identification",
            content=f"Identify yourself as '{ai_name}' when asked.",
            tags=["default_generated"]
        ))
        purpose_text = context_notes if context_notes else "Assist within described context; respect approvals."
        ch1.children.append(BookNode(
            id="ch1s2", node_type=BookNodeType.SECTION, title="Section 2: Purpose",
            content=f"Use-Case Class: {use_case}\nAI Name: {ai_name}\nPurpose: {purpose_text}",
            tags=["default_generated"]
        ))
        if libraries:
            ch1.children.append(BookNode(
                id="ch1s3", node_type=BookNodeType.SECTION, title="Section 3: Libraries in Use",
                content="Selected Nexus Libraries:\n" + "\n".join(f"- {lib}" for lib in libraries),
                tags=["default_generated"]
            ))
        part1.children.append(ch1)

        ch2 = BookNode(id="ch2", node_type=BookNodeType.CHAPTER, title="Chapter 2: Guardrails")
        sys_content = (
            "System-level protections are enforced by the Nexus Compendium and active for every AI.\n"
            "These include safeguards against illegal content, sexual content, harassment, credential theft,\n"
            "and unqualified medical/legal/financial advice. See the Governance panel for the full list.\n"
            "The following are the optional behavior upgrades selected for this AI:"
        )
        ch2.children.append(BookNode(
            id="ch2s1", node_type=BookNodeType.SECTION, title="Section 1: System Protections",
            content=sys_content,
            tags=["default_generated"]
        ))
        if guardrails:
            opt_content = "Selected Optional Guardrails:\n" + "\n".join(f"- {g}" for g in guardrails)
        else:
            opt_content = "No optional guardrails selected. Add them in the AI Forge to customize behavior."
        ch2.children.append(BookNode(
            id="ch2s2", node_type=BookNodeType.SECTION, title="Section 2: Optional Guardrails",
            content=opt_content,
            tags=["default_generated"]
        ))
        part1.children.append(ch2)

        ch3 = BookNode(id="ch3", node_type=BookNodeType.CHAPTER, title="Chapter 3: Capabilities")
        if abilities:
            for i, ab in enumerate(abilities):
                c = _canonical(ab)
                prof = profiles.get(c)
                hint = "Ask for context; request approval when needed."
                quick = "Open the capability and describe what you need."
                prmpts = "Clarify task, ask for context, request approval when needed."
                if prof:
                    hint = "; ".join(prof["style"])
                    quick = "; ".join(prof["quickstart"])
                    prmpts = ", ".join(prof["prompts"])
                surface = ability_surfaces.get(ab) or ability_surfaces.get(c, _default_surface(c))
                sec = BookNode(
                    id=f"ch3s{i}", node_type=BookNodeType.SECTION,
                    title=f"Capability: {ab}",
                    content=(
                        f"Purpose: assist with {ab.lower()}.\n"
                        f"Style: {hint}\n"
                        f"Surface: {surface}\n"
                        f"Quickstart: {quick}\n"
                        f"Common prompts: {prmpts}\n"
                        "Always follow allowed/restricted/approval rules before acting."
                    ),
                    tags=["default_generated"]
                )
                ch3.children.append(sec)
        else:
            ch3.children.append(BookNode(
                id="ch3s0", node_type=BookNodeType.SECTION,
                title="No capabilities configured",
                content="Add capabilities in the AI Forge to populate this section.",
                tags=["default_generated"]
            ))
        part1.children.append(ch3)

        # Chapter 3b: Capability Attachments
        ch3b = BookNode(id="ch3b", node_type=BookNodeType.CHAPTER, title="Chapter 3b: Capability Attachments")
        if abilities:
            for i, ab in enumerate(abilities):
                c = _canonical(ab)
                action = CAPABILITY_REGISTRY.get(c)
                if action:
                    content = (
                        f"capability_id: {action.capability_id}\n"
                        f"inward_surface: {action.inward_surface}\n"
                        f"outward_action_path: {action.outward_action_path}\n"
                        f"required_permissions: {', '.join(action.required_permissions) if action.required_permissions else 'None'}\n"
                        f"required_approval_level: {action.required_approval_level}\n"
                        f"unfinished_safe_fallback: {action.unfinished_safe_fallback}"
                    )
                else:
                    content = f"Attachment: {_default_attachment(c)}. This capability is active and ready for use within its approved scope."
                ch3b.children.append(BookNode(
                    id=f"ch3bs{i}", node_type=BookNodeType.SECTION,
                    title=f"Attachment: {ab}",
                    content=content,
                    tags=["default_generated"]
                ))
        else:
            ch3b.children.append(BookNode(
                id="ch3bs0", node_type=BookNodeType.SECTION,
                title="No attachments",
                content="Add capabilities in the AI Forge to populate attachments.",
                tags=["default_generated"]
            ))
        part1.children.append(ch3b)

        # Chapter 3c: Available Actions
        ch3c = BookNode(id="ch3c", node_type=BookNodeType.CHAPTER, title="Chapter 3c: Available Actions")
        action_matrix = get_available_actions_for_ai(abilities, use_case, libraries, guardrails)
        if action_matrix:
            for i, action in enumerate(action_matrix):
                ch3c.children.append(BookNode(
                    id=f"ch3cs{i}", node_type=BookNodeType.SECTION,
                    title=action["label"],
                    content=(
                        f"Mode: {action['mode']}\n"
                        f"Approval: {action['approval']}\n"
                        f"Description: {action['description']}"
                    ),
                    tags=["default_generated"]
                ))
        else:
            ch3c.children.append(BookNode(
                id="ch3cs0", node_type=BookNodeType.SECTION,
                title="No actions available",
                content="No actions available for current capabilities and guardrails.",
                tags=["default_generated"]
            ))
        part1.children.append(ch3c)

        # Chapter 3d: Cross-Capability Workflows
        ch3d = BookNode(id="ch3d", node_type=BookNodeType.CHAPTER, title="Chapter 3d: Cross-Capability Workflows")
        workflows = get_combined_capability_workflows(abilities, libraries, use_case)
        if workflows:
            for i, wf in enumerate(workflows):
                ch3d.children.append(BookNode(
                    id=f"ch3ds{i}", node_type=BookNodeType.SECTION,
                    title=f"Workflow: {wf}",
                    content=wf,
                    tags=["default_generated"]
                ))
        else:
            ch3d.children.append(BookNode(
                id="ch3ds0", node_type=BookNodeType.SECTION,
                title="No cross-capability workflows",
                content="Select multiple compatible capabilities to generate workflows.",
                tags=["default_generated"]
            ))
        part1.children.append(ch3d)

        # Quickstart
        quick = BookNode(id="qs", node_type=BookNodeType.CHAPTER, title="Chapter 4: Quickstart")
        qs_content = ""
        if quickstart_steps:
            qs_content = "\n".join(f"{i+1}) {step}" for i, step in enumerate(quickstart_steps[:6]))
        else:
            qs_content = (
                "1) Open Chat from the Forge to talk to this AI.\n"
                "2) Ask it to draft, research, or plan; it will cite rules from this Knowledge.\n"
                "3) Risky actions (files/commands/network) require approval.\n"
                "4) See Capability sections for what it can do."
            )
        quick.children.append(BookNode(
            id="qs1", node_type=BookNodeType.SECTION, title="How to use",
            content=qs_content,
            tags=["default_generated"]
        ))
        if common_prompts:
            quick.children.append(BookNode(
                id="qs2", node_type=BookNodeType.SECTION, title="Common Prompts",
                content="\n".join(f"- {p}" for p in common_prompts),
                tags=["default_generated"]
            ))
        if context_notes:
            quick.children.append(BookNode(
                id="qs3", node_type=BookNodeType.SECTION, title="Context Notes",
                content=context_notes,
                tags=["default_generated"]
            ))
        root.children.append(quick)

        root.children.append(part1)

        # Part II: Task Execution
        part2 = BookNode(id="part2", node_type=BookNodeType.PART, title="Part II: Task Execution")
        ch4 = BookNode(id="ch4", node_type=BookNodeType.CHAPTER, title="Chapter 4: Workflow Steps")
        ch4.children.append(BookNode(
            id="ch4s1", node_type=BookNodeType.SECTION, title="Section 1: Allowed Areas",
            content="\n".join(f"- {a}" for a in allowed) or "Assist within scope; ask clarifying questions.",
            tags=["default_generated"]
        ))
        ch4.children.append(BookNode(
            id="ch4s2", node_type=BookNodeType.SECTION, title="Section 2: Restricted Areas",
            content="\n".join(f"- {r}" for r in restricted) or "Do not execute system actions without approval.",
            tags=["default_generated"]
        ))
        ch4.children.append(BookNode(
            id="ch4s3", node_type=BookNodeType.SECTION, title="Section 3: Approval Rules",
            content="\n".join(f"- {a}" for a in approval) or "Actions affecting files, settings, or external systems require approval.",
            tags=["default_generated"]
        ))
        part2.children.append(ch4)
        root.children.append(part2)

        tp = TitlePage(
            ai_name=ai_name,
            description=f"Knowledge compendium for {ai_name}",
            purpose=f"Governed behavior and task guidance for {ai_name}",
            credits="Created via AI Forge"
        )
        return BookInstance(
            ai_uuid=ai_uuid, ai_name=ai_name,
            title_page=tp, root=root
        )

    def _clear_editor(self):
        self._current_node = None
        if hasattr(self, "_title_edit"):
            self._title_edit.clear()
        if hasattr(self, "_content_edit"):
            self._content_edit.clear()
        if hasattr(self, "_relations_edit"):
            self._relations_edit.clear()

    def _refresh_tree(self):
        if not hasattr(self, "_tree") or self._tree.parent() is None:
            return
        self._tree.clear()
        if not self._current_book:
            return
        self._build_tree_item(self._tree.invisibleRootItem(), self._current_book.root)
        self._tree.expandAll()

    def _build_tree_item(self, parent_item, node: BookNode):
        item = QTreeWidgetItem(parent_item)
        item.setText(0, node.title)
        item.setText(1, node.node_type.value)
        item.setData(0, Qt.ItemDataRole.UserRole, node.id)
        for child in node.children:
            self._build_tree_item(item, child)

    def _on_tree_select(self, item: QTreeWidgetItem):
        node_id = item.data(0, Qt.ItemDataRole.UserRole)
        if not node_id or not self._current_book:
            return
        node = self._current_book.find_node(node_id)
        if node:
            self._current_node = node
            if hasattr(self, "_title_edit"):
                self._title_edit.setText(node.title)
            if hasattr(self, "_content_edit"):
                self._content_edit.setText(node.content)
            if hasattr(self, "_relations_edit"):
                self._relations_edit.setText(", ".join(node.relations))
            if hasattr(self, "_default_warning"):
                is_default = "default_generated" in node.tags
                self._default_warning.setVisible(is_default)
            if hasattr(self, "_default_status"):
                is_default = "default_generated" in node.tags
                if is_default:
                    self._default_status.setText("[Default Generated — Edit with caution]")
                else:
                    self._default_status.setText("[Custom node]")

    def _update_current_node(self):
        if not self._current_node:
            QMessageBox.warning(self, "No Selection", "Select a node in the tree to update.")
            return
        # Confirm before editing default-generated nodes
        if "default_generated" in self._current_node.tags:
            reply = QMessageBox.question(
                self,
                "Edit Default Node",
                "This is a default-generated node. Editing it may change core AI behavior.\n\n"
                "Do you want to edit it anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            self._current_node.tags = [t for t in self._current_node.tags if t != "default_generated"]
            self._default_warning.setVisible(False)
            self._default_status.setText("[Customized from default]")
            if self._current_ai_uuid:
                self.defaults_edited.emit(self._current_ai_uuid, True)
        self._current_node.title = self._title_edit.text()
        self._current_node.content = self._content_edit.toPlainText()
        self._current_node.relations = [r.strip() for r in self._relations_edit.text().split(",") if r.strip()]
        self._current_node.modified_at = datetime.now()
        self._refresh_tree()
        self._screen_status.setText("Screening: Modified (unsaved)")
        self._screen_status.setStyleSheet("color: #fbc02d; font-style: italic;")

    def _save_knowledge(self):
        allowed, gate_msg = check_action_allowed("save_knowledge", MoiraiHealthReport())
        if not allowed:
            QMessageBox.critical(self, "Protected Mode", gate_msg)
            return
        if not self._current_book:
            QMessageBox.warning(self, "No Knowledge", "Create or load knowledge first.")
            return

        from ...core.ethical_guardrail_watchers import GuardrailScanner, get_warning_message

        # Run screening on ALL nodes
        all_nodes = self._current_book.get_all_nodes()
        total = len(all_nodes)
        progress = QProgressDialog("Screening Knowledge — The Compendium of Truth...", "Cancel", 0, total, self)
        progress.setWindowTitle("Save Gate — Ethical Standards Check")
        progress.setModal(True)

        any_blocked = False
        messages = []
        total_yellow_added = 0
        latest_warning = ""
        for i, node in enumerate(all_nodes):
            progress.setValue(i)
            if progress.wasCanceled():
                progress.close()
                return

            # Run legacy ScreeningPipeline first (spell check + basic patterns)
            can_save, cleaned, msgs = ScreeningPipeline.run(node.content)
            messages.extend(msgs)
            if not can_save:
                any_blocked = True

            # Run the new GuardrailScanner (Watchers A/B/C + flag system)
            guardrail_result = GuardrailScanner.screen(cleaned)
            if not guardrail_result.can_save:
                any_blocked = True
                messages.extend(guardrail_result.messages)
                cleaned = guardrail_result.cleaned_text
                total_yellow_added += guardrail_result.yellow_flags_added
                if guardrail_result.warning_message:
                    latest_warning = guardrail_result.warning_message

            # Also run legacy watcher_service for backward compatibility
            watcher_result = run_watchers(cleaned)
            if not watcher_result.clean:
                any_blocked = True
                messages.append(BLOCK_MESSAGE)
                cleaned = watcher_result.sanitized_text

            node.content = cleaned

        progress.setValue(total)
        progress.close()

        if any_blocked:
            # Build the evolving warning message
            warning_text = latest_warning or (
                "Command Nexus is not here to be used for illegal, malicious, sexual, "
                "or harmful practices. Please remember any attempts to save these types "
                "of inputs will be reverted back. Please remember the rules and this "
                "program is for ethical uses only. Thank you."
            )

            # Add screening log
            full_message = warning_text + "\n\n" + "=" * 50 + "\n"
            full_message += "Screening log:\n" + "\n".join(messages[:15])

            # Check if license should be tripped
            if GuardrailScanner.should_trip_license():
                # Generate owner notification
                try:
                    GuardrailScanner.generate_owner_notification()
                except Exception:
                    pass

                full_message += "\n\n" + "=" * 50 + "\n"
                full_message += (
                    "LICENSE TRIPWIRE ENGAGED — Your license is being deactivated "
                    "due to repeated ethical standards violations.\n\n"
                    "Your access to Command Nexus has been restricted. To request "
                    "a review and potential restoration of access, please contact "
                    "support@averylogicworks.com.\n\n"
                    "Malicious attempts to bypass the system can result in a "
                    "permanent ban from Command Nexus and, depending on severity, "
                    "all future Avery Logic Works product releases."
                )
                QMessageBox.critical(
                    self, "License Tripwire — Ethical Violations",
                    full_message
                )
                # Trigger license deactivation
                try:
                    from ...core.license_manager import get_license_manager
                    lm = get_license_manager()
                    lm.deactivate("Repeated ethical guardrail violations")
                except Exception:
                    pass
            else:
                QMessageBox.warning(
                    self, "Ethical Standards Violation",
                    full_message
                )

            # Revert content — switch back to ethical standards
            self._screen_status.setText("Screening: VIOLATION DETECTED — Content reverted")
            self._screen_status.setStyleSheet("color: #f0883e; font-weight: bold;")
        else:
            self._screen_status.setText("Screening: Passed")
            self._screen_status.setStyleSheet("color: #3fb950;")
            QMessageBox.information(
                self, "Saved",
                "Knowledge saved successfully.\n\n" +
                ("Screening log:\n" + "\n".join(messages[:10]) if messages else "No issues found.")
            )

        self._refresh_tree()
        self.book_saved.emit(self._current_book.ai_uuid, self._current_book.ai_name)

    def _open_book_ai_dialog(self):
        """Open the conversational Book AI that asks questions and hides internals."""
        if not self._current_ai_uuid or not self._current_book:
            QMessageBox.information(self, "No AI", "Open a Book for an AI first.")
            return

        ai_name = self._current_book.ai_name
        existing_context = self._current_book.title_page.purpose if self._current_book.title_page else ""

        dialog = KnowledgeAIDialog(ai_name, self._current_ai_uuid, existing_context, parent=self)
        dialog.book_content_ready.connect(self._on_book_ai_content_ready)
        dialog.exec()

    def _on_book_ai_content_ready(self, ai_uuid: str, ai_name: str, content: dict):
        """Receive content from Book AI and write it into the Knowledge structure WITHOUT revealing structure."""
        book = self._books.get(ai_uuid)
        if not book:
            return

        # Store a snapshot of current state for rollback capability
        self._store_book_snapshot(ai_uuid, book)

        # Find or create the "Active Memory" part to hold user-defined content
        active_memory_part = None
        for child in book.root.children:
            if child.title == "Part: Active Memory (User-Defined)":
                active_memory_part = child
                break

        if not active_memory_part:
            active_memory_part = BookNode(
                id="active_memory", node_type=BookNodeType.PART,
                title="Part: Active Memory (User-Defined)",
            )
            book.root.children.append(active_memory_part)

        # Clear existing user-defined sections and rebuild with proper structure
        active_memory_part.children.clear()

        # Map content keys to human-friendly chapter titles
        chapter_map = {
            "active_instructions": ("Chapter: Active Instructions", "How this AI should behave when running. These are live instructions."),
            "persistent_memory": ("Chapter: Persistent Memory", "Long-term facts and knowledge that should always be remembered."),
            "general_memory": ("Chapter: General Memory", "Current context and temporary knowledge that may change over time."),
            "preferences": ("Chapter: Preferences", "User's personal preferences for interaction style and behavior."),
            "guardrails": ("Chapter: Boundaries", "Hard rules and things this AI must never do."),
            "purpose": ("Chapter: Purpose & Role", "The primary purpose and intended role of this AI."),
            "audience": ("Chapter: Audience", "Who this AI is designed to help and work with."),
        }

        for key, value in content.items():
            if not value:
                continue
            title, description = chapter_map.get(key, (f"Chapter: {key.capitalize()}", ""))
            ch = BookNode(
                id=f"active_{key}",
                node_type=BookNodeType.CHAPTER,
                title=title,
                tags=["book_ai_generated", "user_editable"],
            )
            ch.children.append(BookNode(
                id=f"active_{key}_desc",
                node_type=BookNodeType.SECTION,
                title="Description",
                content=description,
                tags=["book_ai_generated"],
            ))
            ch.children.append(BookNode(
                id=f"active_{key}_content",
                node_type=BookNodeType.SECTION,
                title="Content",
                content=value,
                tags=["book_ai_generated", "user_editable"],
            ))
            active_memory_part.children.append(ch)

        # Update title page purpose
        if book.title_page and content.get("purpose"):
            book.title_page.purpose = content["purpose"]

        self._refresh_tree()

        # If obfuscated, populate the friendly summary panel
        if self._obs.is_obfuscated and hasattr(self, "_obfuscation_summary"):
            summary_lines = [f"<b>{ai_name}</b> — AI Guidance Summary\n"]
            if content.get("purpose"):
                summary_lines.append(f"<b>What I'm for:</b> {content['purpose']}")
            if content.get("active_instructions"):
                summary_lines.append(f"<b>How I should behave:</b> {content['active_instructions']}")
            if content.get("persistent_memory"):
                summary_lines.append(f"<b>What I always remember:</b> {content['persistent_memory']}")
            if content.get("preferences"):
                summary_lines.append(f"<b>How you like to work:</b> {content['preferences']}")
            if content.get("guardrails"):
                summary_lines.append(f"<b>My boundaries:</b> {content['guardrails']}")
            summary_lines.append(
                "\n<i>Knowledge Keeper has written these into my memory. "
                "You can always ask me to go back to how things were before any changes.</i>"
            )
            self._obfuscation_summary.setHtml("<br>".join(summary_lines))

        self._audit_event("book_ai_content_written", msg=f"{ai_name}: {len(content)} sections")
        QMessageBox.information(
            self, "Book Updated",
            f"Knowledge Keeper has written {len([v for v in content.values() if v])} sections into the Knowledge for {ai_name}.\n\n"
            f"Your AI now has active instructions, persistent memory, and preferences.\n"
            f"The internal structure remains hidden. The AI will follow these rules.\n\n"
            f"If anything doesn't work right, just ask your AI to revert to defaults."
        )

    def _store_knowledge_snapshot(self, ai_uuid: str, knowledge):
        """Store a snapshot of the knowledge before user edits, for rollback capability."""
        if not hasattr(self, '_knowledge_snapshots'):
            self._knowledge_snapshots = {}
        # Only store if we haven't stored one yet (first snapshot is the default)
        if ai_uuid not in self._knowledge_snapshots:
            import copy
            self._knowledge_snapshots[ai_uuid] = copy.deepcopy(knowledge)

    def _revert_knowledge_to_defaults(self, ai_uuid: str) -> bool:
        """Revert knowledge to its original default snapshot. Returns True if successful."""
        if not hasattr(self, '_knowledge_snapshots') or ai_uuid not in self._knowledge_snapshots:
            return False
        import copy
        self._books[ai_uuid] = copy.deepcopy(self._knowledge_snapshots[ai_uuid])
        self._refresh_tree()
        self._audit_event("knowledge_reverted_to_defaults", msg=f"ai_uuid={ai_uuid}")
        return True

    def _audit_event(self, action: str, msg: str = ""):
        if self._audit:
            try:
                self._audit.log(tool="KnowledgeWindow", action=action, target=msg, status="info", approved=True)
            except Exception:
                pass

    def _export_python(self):
        if not self._current_book:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Python Module", f"{self._current_book.ai_name}_book.py", "Python Files (*.py)")
        if path:
            if not path.endswith(".py"):
                path += ".py"
            py_code = PythonTranslator.translate_knowledge(self._current_book)
            Path(path).write_text(py_code, encoding="utf-8")
            QMessageBox.information(self, "Exported", f"Python module exported to:\n{path}")

    def _new_knowledge(self):
        # Step 1: Goal discovery
        context = self._current_book.title_page.purpose if self._current_book else ""
        gd = GoalDiscoveryDialog(self, existing_context=context)
        if gd.exec() != QDialog.DialogCode.Accepted:
            return
        goal = gd.get_result()

        # Step 2: Basic identity
        dialog = QDialog(self)
        dialog.setWindowTitle("New Knowledge")
        layout = QFormLayout(dialog)
        name_input = QLineEdit()
        name_input.setPlaceholderText("AI Name...")
        layout.addRow("AI Name:", name_input)
        uuid_input = QLineEdit()
        uuid_input.setPlaceholderText("AI UUID...")
        layout.addRow("AI UUID:", uuid_input)
        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        box.accepted.connect(dialog.accept)
        box.rejected.connect(dialog.reject)
        layout.addWidget(box)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        ai_name = name_input.text().strip() or "Untitled"
        ai_uuid = uuid_input.text().strip() or str(uuid.uuid4())[:8]

        # Step 3: Build title page from discovered goal
        purpose = goal.get("goal", "")
        description = f"Audience: {goal.get('audience', '')}\nSuccess looks like: {goal.get('success', '')}"
        avoid = goal.get("avoid", "")
        credits = f"Confidence: {goal.get('confidence', 'unknown')}"

        tp = TitlePage(
            ai_name=ai_name,
            purpose=purpose,
            description=description,
            credits=credits,
        )
        root = BookNode(id="root", node_type=BookNodeType.TABLE_OF_CONTENTS, title="Table of Contents")

        # Add an "Avoid" node if user specified restrictions
        if avoid:
            avoid_node = BookNode(
                id="avoid_001",
                node_type=BookNodeType.SECTION,
                title="Things to Avoid",
                content=avoid,
            )
            root.children.append(avoid_node)

        self._current_book = BookInstance(ai_uuid=ai_uuid, ai_name=ai_name, title_page=tp, root=root)
        self._refresh_tree()
        self._book_title.setText(f"Knowledge: {ai_name}")

    def _add_node_dialog(self):
        if not self._current_book:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Node")
        layout = QFormLayout(dialog)
        type_combo = QComboBox()
        for nt in BookNodeType:
            type_combo.addItem(nt.value)
        layout.addRow("Type:", type_combo)
        title_input = QLineEdit()
        title_input.setPlaceholderText("Node title...")
        layout.addRow("Title:", title_input)
        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        box.accepted.connect(dialog.accept)
        box.rejected.connect(dialog.reject)
        layout.addWidget(box)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            node = BookNode(
                id=f"node_{uuid.uuid4().hex[:6]}",
                node_type=BookNodeType(type_combo.currentText()),
                title=title_input.text() or "Untitled"
            )
            if self._current_node:
                self._current_node.children.append(node)
            else:
                self._current_book.root.children.append(node)
            self._refresh_tree()

    def _delete_node(self):
        try:
            if not self._current_node or not self._current_book:
                return
            reply = QMessageBox.question(
                self, "Confirm", f"Delete '{self._current_node.title}' and all its children?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._delete_node_recursive(self._current_book.root, self._current_node.id)
                self._current_node = None
                self._title_edit.clear()
                self._content_edit.clear()
                self._relations_edit.clear()
                self._refresh_tree()
        except Exception as e:
            QMessageBox.warning(self, "Delete Error", f"Could not delete node: {e}")

    def _delete_node_recursive(self, node: BookNode, target_id: str) -> bool:
        for i, child in enumerate(node.children):
            if child.id == target_id:
                node.children.pop(i)
                return True
            if self._delete_node_recursive(child, target_id):
                return True
        return False

    def _add_glossary_entry(self):
        term = self._gloss_term.text().strip()
        definition = self._gloss_def.text().strip()
        if term and definition and self._current_book:
            self._current_book.glossary.append(GlossaryEntry(term, definition))
            row = self._glossary_table.rowCount()
            self._glossary_table.insertRow(row)
            self._glossary_table.setItem(row, 0, QTableWidgetItem(term))
            self._glossary_table.setItem(row, 1, QTableWidgetItem(definition))
            self._gloss_term.clear()
            self._gloss_def.clear()

    def _add_idiom_entry(self):
        phrase = self._idiom_phrase.text().strip()
        meaning = self._idiom_meaning.text().strip()
        context = self._idiom_ctx.text().strip()
        if phrase and meaning and self._current_book:
            self._current_book.idioms.append(IdiomEntry(phrase, meaning, context))
            row = self._idiom_table.rowCount()
            self._idiom_table.insertRow(row)
            self._idiom_table.setItem(row, 0, QTableWidgetItem(phrase))
            self._idiom_table.setItem(row, 1, QTableWidgetItem(meaning))
            self._idiom_table.setItem(row, 2, QTableWidgetItem(context))
            self._idiom_phrase.clear()
            self._idiom_meaning.clear()
            self._idiom_ctx.clear()

    def _add_abbr_entry(self):
        short = self._abbr_short.text().strip()
        expansion = self._abbr_exp.text().strip()
        context = self._abbr_ctx.text().strip()
        if short and expansion and self._current_book:
            self._current_book.abbreviations.append(AbbreviationEntry(short, expansion, context))
            row = self._abbr_table.rowCount()
            self._abbr_table.insertRow(row)
            self._abbr_table.setItem(row, 0, QTableWidgetItem(short))
            self._abbr_table.setItem(row, 1, QTableWidgetItem(expansion))
            self._abbr_table.setItem(row, 2, QTableWidgetItem(context))
            self._abbr_short.clear()
            self._abbr_exp.clear()
            self._abbr_ctx.clear()
