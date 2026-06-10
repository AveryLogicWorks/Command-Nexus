"""Capability Action Registry and Workflow Dialogs."""
from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass, field
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QComboBox, QTabWidget, QWidget,
    QSplitter, QMessageBox, QFileDialog,
)


@dataclass
class CapabilityAction:
    canonical_name: str
    dialog_class: str
    ui_label: str
    approval_required: list[str] = field(default_factory=list)
    book_context_fields: list[str] = field(default_factory=lambda: [
        "identity", "use_case", "capabilities", "libraries", "guardrails", "quickstart"
    ])
    status_messages: dict[str, str] = field(default_factory=dict)


CAPABILITY_REGISTRY: dict[str, CapabilityAction] = {
    "Chatbot": CapabilityAction(
        "Chatbot", "ChatCapabilityDialog", "Open Chat",
        ["outbound messages"],
        status_messages={"ready": "Chat session ready.", "approval_needed": "Action requires approval."},
    ),
    "Chat": CapabilityAction(
        "Chat", "ChatCapabilityDialog", "Open Chat",
        ["outbound messages"],
        status_messages={"ready": "Chat session ready.", "approval_needed": "Action requires approval."},
    ),
    "Coder": CapabilityAction(
        "Coder", "CodingCapabilityDialog", "Open Coding Workflow",
        ["file modifications", "running commands"],
        status_messages={"ready": "Coding workflow ready.", "approval_needed": "File changes require approval."},
    ),
    "Research": CapabilityAction(
        "Research", "ResearchCapabilityDialog", "Open Research Workflow",
        ["external/network searches"],
        status_messages={"ready": "Research workflow ready.", "approval_needed": "External searches require approval."},
    ),
    "Creative Writing": CapabilityAction(
        "Creative Writing", "CreativeWriterCapabilityDialog", "Open Writing Workflow",
        ["publishing externally"],
        status_messages={"ready": "Writing workflow ready.", "approval_needed": "Publishing requires approval."},
    ),
    "Planner": CapabilityAction(
        "Planner", "PlannerCapabilityDialog", "Open Planner",
        ["executing risky steps"],
        status_messages={"ready": "Planner ready.", "approval_needed": "Risky steps require approval."},
    ),
    "Notebook": CapabilityAction(
        "Notebook", "NotebookCapabilityDialog", "Open Notes",
        ["bulk deletions"],
        status_messages={"ready": "Notes workflow ready.", "approval_needed": "Bulk deletion requires approval."},
    ),
    "Document Processor": CapabilityAction(
        "Document Processor", "DocumentProcessorCapabilityDialog", "Open Document Workflow",
        ["exporting summaries"],
        status_messages={"ready": "Document workflow ready.", "approval_needed": "Export requires approval."},
    ),
    "Archive": CapabilityAction(
        "Archive", "ArchiveCapabilityDialog", "Open Archive",
        ["moving archives"],
        status_messages={"ready": "Archive workflow ready.", "approval_needed": "Moving archives requires approval."},
    ),
    "Tool User": CapabilityAction(
        "Tool User", "ToolUserCapabilityDialog", "Open Tool Workflow",
        ["tool invocation"],
        status_messages={"ready": "Tool workflow ready.", "approval_needed": "Tool invocation requires approval."},
    ),
}


def _canonical_ability(name: str) -> str:
    mapping = {
        "Chat Companion": "Chatbot",
        "Customer Support Agent": "Chatbot",
        "Email Sifter & Responder": "Chatbot",
        "Creative Writer": "Creative Writing",
        "Research Assistant": "Research",
        "Academic Researcher": "Research",
        "Business Intelligence Analyst": "Research",
        "Personal Organizer": "Notebook",
        "Meeting Scribe": "Notebook",
        "Task / Project Manager": "Planner",
        "Strategic Planner": "Planner",
        "Workflow Automator": "Planner",
        "Coding Assistant": "Coder",
        "IT Operations Agent": "Coder",
    }
    return mapping.get(name.strip(), name.strip())


def get_capability_action(capability_name: str) -> CapabilityAction | None:
    canonical = _canonical_ability(capability_name)
    return CAPABILITY_REGISTRY.get(canonical)


def get_actions_for_ai(abilities: list[str]) -> list[tuple[str, str, str]]:
    """Return (ui_label, dialog_class_name, original_ability_name) deduped by canonical name."""
    seen: set[str] = set()
    out: list[tuple[str, str, str]] = []
    for ab in abilities:
        c = _canonical_ability(ab)
        if c in seen:
            continue
        seen.add(c)
        reg = CAPABILITY_REGISTRY.get(c)
        if reg:
            out.append((reg.ui_label, reg.dialog_class, ab))
    return out


class BaseCapabilityDialog(QDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(parent)
        self._ai_name = ai_name
        self._ai_uuid = ai_uuid
        self._abilities = abilities or []
        self._book_path = book_path
        self._guardrails = guardrails or []
        self._libraries = libraries or []
        self._use_case = use_case
        self._book_context: dict[str, str] = {}
        self._load_book_context()

    def _load_book_context(self):
        self._book_context = {
            "identity": f"AI Name: {self._ai_name}",
            "use_case": f"Use Case: {self._use_case}",
            "capabilities": f"Capabilities: {', '.join(self._abilities)}",
            "libraries": f"Libraries: {', '.join(self._libraries) if self._libraries else 'None'}",
            "guardrails": f"Guardrails: {', '.join(self._guardrails) if self._guardrails else 'None'}",
            "quickstart": "Open the capability workflow and describe what you need.",
        }
        if self._book_path and Path(self._book_path).exists():
            try:
                text = Path(self._book_path).read_text(encoding="utf-8")
                in_quick = False
                quick_lines: list[str] = []
                for line in text.splitlines():
                    if line.strip().startswith("## Quickstart"):
                        in_quick = True
                        continue
                    if in_quick:
                        if line.strip().startswith("##"):
                            break
                        if line.strip():
                            quick_lines.append(line.strip())
                if quick_lines:
                    self._book_context["quickstart"] = "\n".join(quick_lines)
            except Exception:
                pass

    def _build_context_banner(self) -> str:
        return (
            f"{self._book_context.get('identity', '')}  |  "
            f"{self._book_context.get('use_case', '')}  |  "
            f"{self._book_context.get('capabilities', '')}"
        )


class ChatCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Chat with {ai_name}")
        self.resize(600, 500)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px; background-color: #161b22; border: 1px solid #30363d;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        self._transcript = QTextEdit()
        self._transcript.setReadOnly(True)
        self._transcript.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
        layout.addWidget(self._transcript, stretch=1)
        row = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setPlaceholderText("Type a message to this AI...")
        row.addWidget(self._input, stretch=1)
        send = QPushButton("Send")
        send.clicked.connect(self._on_send)
        row.addWidget(send)
        layout.addLayout(row)
        self._approval_banner = QLabel("")
        self._approval_banner.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 4px; border-radius: 4px;")
        self._approval_banner.setVisible(False)
        layout.addWidget(self._approval_banner)
        self._transcript.append(f"<b>{ai_name}:</b> Hi, I'm {ai_name}. I'm ready to help with: {', '.join(self._abilities) or 'general assistance'}.")
        reg = get_capability_action(self._abilities[0]) if self._abilities else None
        if reg:
            self._transcript.append(f"<b>{ai_name}:</b> {reg.status_messages.get('ready', '')}")
        self._transcript.append(f"<b>{ai_name}:</b> Quickstart: {self._book_context.get('quickstart', 'Ask me anything.')}")

    def _on_send(self):
        msg = self._input.text().strip()
        if not msg:
            return
        self._transcript.append(f"<b>You:</b> {msg}")
        self._approval_banner.setVisible(False)
        reply_parts: list[str] = []
        if any(_canonical_ability(c) == "Coder" for c in self._abilities):
            if any(k in msg.lower() for k in ["code", "function", "bug", "fix", "test", "diff", "patch"]):
                reply_parts.append("I can explain code, draft diffs, or outline tests. I won't modify files or run commands without your approval.")
                self._approval_banner.setText("Approval required: file changes or command execution.")
                self._approval_banner.setVisible(True)
        if any(_canonical_ability(c) == "Research" for c in self._abilities):
            if any(k in msg.lower() for k in ["research", "find", "search", "compare", "source", "cite"]):
                reply_parts.append("I can gather findings and cite sources. External searches require your approval.")
                self._approval_banner.setText("Approval required: external/network searches.")
                self._approval_banner.setVisible(True)
        if any(_canonical_ability(c) == "Creative Writing" for c in self._abilities):
            if any(k in msg.lower() for k in ["write", "draft", "story", "scene", "outline", "tone"]):
                reply_parts.append("I can draft outlines and text. I'll flag invented content and won't auto-publish without approval.")
                self._approval_banner.setText("Approval required: publishing or external distribution.")
                self._approval_banner.setVisible(True)
        if any(_canonical_ability(c) == "Planner" for c in self._abilities):
            if any(k in msg.lower() for k in ["plan", "project", "task", "milestone", "timeline", "goal"]):
                reply_parts.append("I can break goals into steps and flag risks. Risky execution steps require your approval.")
                self._approval_banner.setText("Approval required: risky execution steps or timeline commitments.")
                self._approval_banner.setVisible(True)
        if any(_canonical_ability(c) == "Notebook" for c in self._abilities):
            if any(k in msg.lower() for k in ["note", "notes", "remember", "recall", "tag"]):
                reply_parts.append("I can capture notes, tag them, and recall prior entries.")
        if any(_canonical_ability(c) == "Document Processor" for c in self._abilities):
            if any(k in msg.lower() for k in ["document", "doc", "summary", "summarize", "extract"]):
                reply_parts.append("I can summarize documents and extract action items. External export requires your approval.")
        if not reply_parts:
            reply_parts.append("I'm here to help. Could you clarify which capability you'd like to use (chat, code, research, write, plan, etc.)?")
        reply_parts.append(f"Echo: {msg}")
        self._transcript.append(f"<b>{self._ai_name}:</b> {' '.join(reply_parts)}")
        self._input.clear()


class CodingCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Coding Workflow — {ai_name}")
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px; background-color: #161b22; border: 1px solid #30363d;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        tabs = QTabWidget()
        t1w = QWidget()
        t1 = QVBoxLayout(t1w)
        t1.addWidget(QLabel("Describe what you need (explain, diff, test, refactor):"))
        self._code_prompt = QTextEdit()
        self._code_prompt.setPlaceholderText("Paste code or describe the bug/feature...")
        t1.addWidget(self._code_prompt, stretch=1)
        br = QHBoxLayout()
        for label, act in [("Explain Code", "explain"), ("Draft Diff", "diff"), ("Outline Tests", "test")]:
            b = QPushButton(label)
            b.clicked.connect(lambda checked, a=act: self._run_code_action(a))
            br.addWidget(b)
        t1.addLayout(br)
        self._code_output = QTextEdit()
        self._code_output.setReadOnly(True)
        self._code_output.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
        t1.addWidget(self._code_output, stretch=1)
        tabs.addTab(t1w, "Explain & Draft")
        t2w = QWidget()
        t2 = QVBoxLayout(t2w)
        t2.addWidget(QLabel("Planned files / modules:"))
        self._planned_files = QTextEdit()
        self._planned_files.setPlaceholderText("e.g., src/utils.py, tests/test_utils.py")
        t2.addWidget(self._planned_files, stretch=1)
        tabs.addTab(t2w, "Planned Files")
        t3w = QWidget()
        t3 = QVBoxLayout(t3w)
        t3.addWidget(QLabel("Test commands / validation plan:"))
        self._test_commands = QTextEdit()
        self._test_commands.setPlaceholderText("e.g., pytest tests/test_utils.py -v")
        t3.addWidget(self._test_commands, stretch=1)
        tabs.addTab(t3w, "Test Commands")
        layout.addWidget(tabs, stretch=1)
        footer = QLabel("Approval required before any file edit, command execution, or deployment.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _run_code_action(self, action):
        prompt = self._code_prompt.toPlainText().strip()
        if not prompt:
            self._code_output.setText("Enter a prompt first.")
            return
        if action == "explain":
            self._code_output.setText(
                f"[EXPLANATION for: {prompt[:80]}...]\n\n"
                "1. Identify the function/class purpose.\n"
                "2. Walk through key logic paths.\n"
                "3. Flag potential risks or edge cases.\n"
                "4. Ask clarifying questions if needed.\n\n"
                "(Simulated explanation — backend not connected.)"
            )
        elif action == "diff":
            self._code_output.setText(
                f"[DIFF for: {prompt[:80]}...]\n\n"
                "```diff\n- old_line\n+ new_line\n```\n\n"
                "Review the diff above. If you approve, the changes can be applied to the planned files.\n"
                "(Simulated diff — backend not connected.)"
            )
        elif action == "test":
            self._code_output.setText(
                f"[TEST OUTLINE for: {prompt[:80]}...]\n\n"
                "1. Unit test: happy path\n"
                "2. Unit test: error handling\n"
                "3. Integration test: end-to-end flow\n"
                "4. Edge cases: empty input, max bounds, concurrency\n\n"
                "(Simulated test outline — backend not connected.)"
            )


class ResearchCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Research Workflow — {ai_name}")
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px; background-color: #161b22; border: 1px solid #30363d;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        layout.addWidget(QLabel("Research query (include scope and desired format):"))
        self._research_query = QTextEdit()
        self._research_query.setPlaceholderText("e.g., Compare Python async frameworks for web APIs...")
        self._research_query.setMaximumHeight(100)
        layout.addWidget(self._research_query)
        br = QHBoxLayout()
        for label, act in [("Start Research", "research"), ("Compare", "compare"), ("Find Risks", "risks")]:
            b = QPushButton(label)
            b.clicked.connect(lambda checked, a=act: self._run_research(a))
            br.addWidget(b)
        layout.addLayout(br)
        sp = QSplitter(Qt.Orientation.Horizontal)
        fw = QWidget()
        fvl = QVBoxLayout(fw)
        fvl.addWidget(QLabel("Findings:"))
        self._findings = QTextEdit()
        self._findings.setReadOnly(True)
        self._findings.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
        fvl.addWidget(self._findings)
        sp.addWidget(fw)
        sw = QWidget()
        svl = QVBoxLayout(sw)
        svl.addWidget(QLabel("Sources & Citations:"))
        self._sources = QTextEdit()
        self._sources.setReadOnly(True)
        self._sources.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
        svl.addWidget(self._sources)
        sp.addWidget(sw)
        sp.setSizes([400, 400])
        layout.addWidget(sp, stretch=1)
        footer = QLabel("External/network searches require your approval before execution.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _run_research(self, action):
        query = self._research_query.toPlainText().strip()
        if not query:
            return
        if action == "research":
            self._findings.setText(
                f"[FINDINGS for: {query}]\n\n"
                "1. Key finding A (placeholder)\n"
                "2. Key finding B (placeholder)\n"
                "3. Key finding C (placeholder)\n\n"
                "Confidence: Medium (simulated)\n"
                "Speculation flagged where noted."
            )
            self._sources.setText("[SOURCES]\n\n- Placeholder Source 1 (simulated)\n- Placeholder Source 2 (simulated)")
        elif action == "compare":
            self._findings.setText(
                f"[COMPARISON for: {query}]\n\n"
                "| Criteria | Option A | Option B |\n"
                "| Speed    | Fast     | Moderate |\n"
                "| Safety   | High     | Medium   |\n\n"
                "(Simulated comparison — backend not connected.)"
            )
            self._sources.setText("[SOURCES]\n\nSimulated sources for comparison.")
        elif action == "risks":
            self._findings.setText(
                f"[RISKS for: {query}]\n\n"
                "1. Risk A — mitigation: do X\n"
                "2. Risk B — mitigation: do Y\n\n"
                "(Simulated risk analysis — backend not connected.)"
            )
            self._sources.setText("[SOURCES]\n\nSimulated sources for risk analysis.")


class CreativeWriterCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Writing Workflow — {ai_name}")
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px; background-color: #161b22; border: 1px solid #30363d;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Tone:"))
        self._tone = QComboBox()
        self._tone.addItems(["Professional", "Casual", "Technical", "Persuasive", "Neutral"])
        ctrl.addWidget(self._tone)
        ctrl.addWidget(QLabel("Audience:"))
        self._audience = QLineEdit()
        self._audience.setPlaceholderText("e.g., executive team, customers, developers")
        ctrl.addWidget(self._audience)
        layout.addLayout(ctrl)
        layout.addWidget(QLabel("Describe the piece, goal, and constraints:"))
        self._write_prompt = QTextEdit()
        self._write_prompt.setPlaceholderText("e.g., Draft a product announcement for our new API release...")
        self._write_prompt.setMaximumHeight(100)
        layout.addWidget(self._write_prompt)
        br = QHBoxLayout()
        for label, act in [("Outline", "outline"), ("Draft", "draft"), ("Revise", "revise")]:
            b = QPushButton(label)
            b.clicked.connect(lambda checked, a=act: self._run_write_action(a))
            br.addWidget(b)
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self._copy_output)
        br.addWidget(copy_btn)
        layout.addLayout(br)
        layout.addWidget(QLabel("Output:"))
        self._write_output = QTextEdit()
        self._write_output.setReadOnly(True)
        self._write_output.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
        layout.addWidget(self._write_output, stretch=1)
        footer = QLabel("Publishing or external distribution requires your approval.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _run_write_action(self, action):
        prompt = self._write_prompt.toPlainText().strip()
        tone = self._tone.currentText()
        audience = self._audience.text().strip()
        ctx = f"Tone: {tone}. Audience: {audience or 'general'}.\n\n"
        if action == "outline":
            self._write_output.setText(ctx + f"[OUTLINE for: {prompt[:80]}...]\n\nI. Introduction\nII. Key Points\nIII. Conclusion\n\n(Simulated outline — backend not connected.)")
        elif action == "draft":
            self._write_output.setText(ctx + f"[DRAFT for: {prompt[:80]}...]\n\n[Generated draft text would appear here.]\n\n(Simulated draft — backend not connected.)")
        elif action == "revise":
            self._write_output.setText(ctx + f"[REVISED for: {prompt[:80]}...]\n\n[Revised text with tracked changes would appear here.]\n\n(Simulated revision — backend not connected.)")

    def _copy_output(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self._write_output.toPlainText())
        QMessageBox.information(self, "Copied", "Output copied to clipboard.")


class PlannerCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Planner — {ai_name}")
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px; background-color: #161b22; border: 1px solid #30363d;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        layout.addWidget(QLabel("Goal / Project description:"))
        self._plan_goal = QTextEdit()
        self._plan_goal.setPlaceholderText("e.g., Launch new customer onboarding flow by end of Q3...")
        self._plan_goal.setMaximumHeight(100)
        layout.addWidget(self._plan_goal)
        br = QHBoxLayout()
        for label, act in [("Generate Plan", "plan"), ("Flag Risks", "risks"), ("Convert to Tasks", "tasks")]:
            b = QPushButton(label)
            b.clicked.connect(lambda checked, a=act: self._run_planner(a))
            br.addWidget(b)
        layout.addLayout(br)
        layout.addWidget(QLabel("Plan / Task List:"))
        self._plan_output = QTextEdit()
        self._plan_output.setReadOnly(True)
        self._plan_output.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
        layout.addWidget(self._plan_output, stretch=1)
        footer = QLabel("Risky execution steps or timeline commitments require your approval.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _run_planner(self, action):
        goal = self._plan_goal.toPlainText().strip()
        if not goal:
            return
        if action == "plan":
            self._plan_output.setText(
                f"[PLAN for: {goal}]\n\n"
                "Step 1: Define scope and success criteria\n"
                "Step 2: Identify stakeholders and dependencies\n"
                "Step 3: Draft timeline with milestones\n"
                "Step 4: Flag risks and mitigation strategies\n"
                "Step 5: Assign owners and set check-in cadence\n\n"
                "(Simulated plan — backend not connected.)"
            )
        elif action == "risks":
            self._plan_output.setText(
                f"[RISKS for: {goal}]\n\n"
                "- Dependency risk: external API may delay delivery\n"
                "- Scope risk: requirements may expand mid-project\n"
                "- Resource risk: limited QA bandwidth near deadline\n\n"
                "(Simulated risk analysis — backend not connected.)"
            )
        elif action == "tasks":
            self._plan_output.setText(
                f"[TASK LIST for: {goal}]\n\n"
                "[ ] Task 1 — owner: TBD — due: TBD\n"
                "[ ] Task 2 — owner: TBD — due: TBD\n"
                "[ ] Task 3 — owner: TBD — due: TBD\n\n"
                "(Simulated task list — backend not connected.)"
            )


class NotebookCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Notes — {ai_name}")
        self.resize(700, 500)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px; background-color: #161b22; border: 1px solid #30363d;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        row = QHBoxLayout()
        self._note_title = QLineEdit()
        self._note_title.setPlaceholderText("Note title...")
        row.addWidget(self._note_title)
        self._note_tags = QLineEdit()
        self._note_tags.setPlaceholderText("Tags (comma-separated)...")
        row.addWidget(self._note_tags)
        layout.addLayout(row)
        self._note_body = QTextEdit()
        self._note_body.setPlaceholderText("Write your note here...")
        layout.addWidget(self._note_body, stretch=1)
        br = QHBoxLayout()
        save_btn = QPushButton("Save Note")
        save_btn.clicked.connect(self._save_note)
        br.addWidget(save_btn)
        recall_btn = QPushButton("Recall Notes")
        recall_btn.clicked.connect(self._recall_notes)
        br.addWidget(recall_btn)
        layout.addLayout(br)
        self._notes_output = QTextEdit()
        self._notes_output.setReadOnly(True)
        self._notes_output.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
        layout.addWidget(self._notes_output, stretch=1)
        footer = QLabel("Bulk deletion or external export requires your approval.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _save_note(self):
        title = self._note_title.text().strip()
        tags = self._note_tags.text().strip()
        body = self._note_body.toPlainText().strip()
        if not body:
            QMessageBox.warning(self, "Empty", "Note body is empty.")
            return
        self._notes_output.append(f"Saved: [{title or 'Untitled'}] Tags: {tags or 'none'}\n{body[:200]}...\n---")
        self._note_title.clear()
        self._note_tags.clear()
        self._note_body.clear()

    def _recall_notes(self):
        tag_filter = self._note_tags.text().strip()
        self._notes_output.append(f"Recalling notes (filter: {tag_filter or 'all'})... (Simulated recall — backend not connected.)")


class DocumentProcessorCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Document Workflow — {ai_name}")
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px; background-color: #161b22; border: 1px solid #30363d;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        layout.addWidget(QLabel("Document text or description:"))
        self._doc_input = QTextEdit()
        self._doc_input.setPlaceholderText("Paste document text here, or describe what you need summarized/extracted...")
        self._doc_input.setMaximumHeight(120)
        layout.addWidget(self._doc_input)
        br = QHBoxLayout()
        load_btn = QPushButton("Load from File")
        load_btn.clicked.connect(self._load_doc)
        br.addWidget(load_btn)
        for label, act in [("Summarize", "summarize"), ("Extract Action Items", "extract"), ("Compare", "compare")]:
            b = QPushButton(label)
            b.clicked.connect(lambda checked, a=act: self._run_doc_action(a))
            br.addWidget(b)
        layout.addLayout(br)
        self._doc_output = QTextEdit()
        self._doc_output.setReadOnly(True)
        self._doc_output.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
        layout.addWidget(self._doc_output, stretch=1)
        footer = QLabel("External export or sensitive document access requires your approval.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _load_doc(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Document", "", "Text Files (*.txt);;All Files (*)")
        if path:
            try:
                text = Path(path).read_text(encoding="utf-8", errors="ignore")
                self._doc_input.setPlainText(text)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _run_doc_action(self, action):
        text = self._doc_input.toPlainText().strip()
        if not text:
            self._doc_output.setText("Paste or load a document first.")
            return
        if action == "summarize":
            self._doc_output.setText(f"[SUMMARY]\n\n{text[:200]}...\n\n(Simulated summary — backend not connected.)")
        elif action == "extract":
            self._doc_output.setText(f"[ACTION ITEMS]\n\n- Action 1 (placeholder)\n- Action 2 (placeholder)\n\n(Simulated extraction — backend not connected.)")
        elif action == "compare":
            self._doc_output.setText(f"[COMPARISON]\n\nSimulated comparison against prior document.\n\n(Simulated — backend not connected.)")


class ArchiveCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Archive — {ai_name}")
        self.resize(700, 500)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px; background-color: #161b22; border: 1px solid #30363d;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        layout.addWidget(QLabel("Artifact name / tags:"))
        row = QHBoxLayout()
        self._artifact_name = QLineEdit()
        self._artifact_name.setPlaceholderText("Artifact name...")
        row.addWidget(self._artifact_name)
        self._artifact_tags = QLineEdit()
        self._artifact_tags.setPlaceholderText("Tags...")
        row.addWidget(self._artifact_tags)
        layout.addLayout(row)
        self._artifact_desc = QTextEdit()
        self._artifact_desc.setPlaceholderText("Description or content to archive...")
        layout.addWidget(self._artifact_desc, stretch=1)
        br = QHBoxLayout()
        store_btn = QPushButton("Store Artifact")
        store_btn.clicked.connect(self._store_artifact)
        br.addWidget(store_btn)
        retrieve_btn = QPushButton("Retrieve")
        retrieve_btn.clicked.connect(self._retrieve_artifacts)
        br.addWidget(retrieve_btn)
        layout.addLayout(br)
        self._archive_output = QTextEdit()
        self._archive_output.setReadOnly(True)
        self._archive_output.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
        layout.addWidget(self._archive_output, stretch=1)
        footer = QLabel("Moving, deleting, or bulk exporting archives requires your approval.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _store_artifact(self):
        name = self._artifact_name.text().strip()
        tags = self._artifact_tags.text().strip()
        desc = self._artifact_desc.toPlainText().strip()
        if not desc:
            QMessageBox.warning(self, "Empty", "No content to archive.")
            return
        self._archive_output.append(f"Stored: [{name or 'Untitled'}] Tags: {tags or 'none'}\n{desc[:200]}...\n---")
        self._artifact_name.clear()
        self._artifact_tags.clear()
        self._artifact_desc.clear()

    def _retrieve_artifacts(self):
        tag_filter = self._artifact_tags.text().strip()
        self._archive_output.append(f"Retrieving artifacts (filter: {tag_filter or 'all'})... (Simulated — backend not connected.)")


class ToolUserCapabilityDialog(BaseCapabilityDialog):
    def __init__(self, ai_name, ai_uuid, abilities, book_path=None, guardrails=None, libraries=None, use_case="", parent=None):
        super().__init__(ai_name, ai_uuid, abilities, book_path, guardrails, libraries, use_case, parent)
        self.setWindowTitle(f"Tool Workflow — {ai_name}")
        self.resize(700, 500)
        layout = QVBoxLayout(self)
        banner = QLabel(self._build_context_banner())
        banner.setStyleSheet("color: #58a6ff; font-size: 11px; padding: 4px; background-color: #161b22; border: 1px solid #30363d;")
        banner.setWordWrap(True)
        layout.addWidget(banner)
        layout.addWidget(QLabel("Tool / Action to propose:"))
        self._tool_input = QLineEdit()
        self._tool_input.setPlaceholderText("e.g., run_git_diff, deploy_preview, send_email_draft")
        layout.addWidget(self._tool_input)
        layout.addWidget(QLabel("Rationale:"))
        self._tool_rationale = QTextEdit()
        self._tool_rationale.setPlaceholderText("Why this tool should be used and what the expected outcome is...")
        self._tool_rationale.setMaximumHeight(100)
        layout.addWidget(self._tool_rationale)
        br = QHBoxLayout()
        propose_btn = QPushButton("Propose Tool Use")
        propose_btn.clicked.connect(self._propose_tool)
        br.addWidget(propose_btn)
        list_btn = QPushButton("List Available Tools")
        list_btn.clicked.connect(self._list_tools)
        br.addWidget(list_btn)
        layout.addLayout(br)
        self._tool_output = QTextEdit()
        self._tool_output.setReadOnly(True)
        self._tool_output.setStyleSheet("background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;")
        layout.addWidget(self._tool_output, stretch=1)
        footer = QLabel("Every tool invocation requires your explicit approval.")
        footer.setStyleSheet("color: #ffab70; background-color: #4a2c00; padding: 6px; border-radius: 4px;")
        layout.addWidget(footer)

    def _propose_tool(self):
        tool = self._tool_input.text().strip()
        rationale = self._tool_rationale.toPlainText().strip()
        if not tool:
            self._tool_output.setText("Enter a tool name.")
            return
        self._tool_output.setText(f"[PROPOSAL]\n\nTool: {tool}\nRationale: {rationale[:200]}...\n\nStatus: AWAITING APPROVAL\n\n(Simulated — backend not connected.)")

    def _list_tools(self):
        self._tool_output.setText("[AVAILABLE TOOLS]\n\n- run_git_diff\n- deploy_preview\n- send_email_draft\n- schedule_meeting\n- generate_report\n\n(Simulated list — backend not connected.)")
