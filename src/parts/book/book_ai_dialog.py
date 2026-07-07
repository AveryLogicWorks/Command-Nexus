"""
Knowledge AI Dialog — Command Nexus
A conversational interface for Knowledge that asks questions,
gathers intent, and writes into knowledge WITHOUT revealing
internal structure to the user.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QLineEdit, QPushButton, QSplitter, QWidget, QScrollArea,
    QFrame, QMessageBox, QProgressDialog
)

from ...core.governance import GovernanceEngine
from ...core.recursive_scanner import RecursiveScanner


class KnowledgeAIConversation:
    """Conversational AI that can answer UI questions and help configure AI."""

    def __init__(self, ai_name: str, ai_uuid: str, existing_context: str = ""):
        self.ai_name = ai_name
        self.ai_uuid = ai_uuid
        self.existing_context = existing_context
        self.mode = "greeting"  # greeting, config, help
        self.stage = 0
        self.history: list[dict] = []
        self.gathered_data: dict[str, str] = {
            "purpose": "",
            "audience": "",
            "guardrails": "",
            "capabilities": "",
            "workflow": "",
            "notes": "",
        }
        
        # UI navigation knowledge base
        self.ui_knowledge = {
            "ai factory": "To create an AI, click the 'AI Factory' button in the main navigation. You can create custom AIs or use starter templates there.",
            "ai section": "The AI section is accessed via the 'AI Factory' button in the main navigation. Look for it in the top or side menu.",
            "knowledge": "Knowledge is where you configure your AI's behavior. Click the 'Knowledge' button for your AI to set up instructions, capabilities, and rules.",
            "book": "Knowledge (formerly called Book) is where your AI's instructions live. Access it from your AI's detail page.",
            "close window": "Click the X button in the top-right corner of the window to close it.",
            "start ai": "To start using an AI, go to AI Factory, select a starter AI or create one, then click 'Start' or 'Chat'.",
            "demo mode": "Demo mode lets you explore the interface with limited functionality. Activate a license to unlock full features.",
            "license": "To activate a license, go to Settings > License and enter your key, or use the license dialog on first launch.",
        }

    def start(self) -> str:
        self.mode = "greeting"
        return (
            f"Hello! I'm the Knowledge Guide for {self.ai_name}. I can help you with two things:\n\n"
            f"1. **Configure your AI** — Tell me what you want {self.ai_name} to do, and I'll set up its Knowledge.\n"
            f"2. **Navigate the program** — Ask me how to use Command Nexus, find features, or get around the interface.\n\n"
            f"What would you like help with?"
        )

    def process_response(self, user_text: str) -> str | None:
        """Process user input and return the next AI message, or None if done."""
        user_text = user_text.strip()
        if not user_text:
            return "Please provide an answer so I can continue."

        self.history.append({"role": "user", "text": user_text, "stage": self.stage})
        lower = user_text.lower()

        # Check if user wants to configure AI or ask for help
        if self.mode == "greeting":
            if any(k in lower for k in ["configure", "setup", "build", "create", "train", "my ai"]):
                self.mode = "config"
                self.stage = 1
                return self._ask_config_question(1)
            elif any(k in lower for k in ["help", "where", "how", "navigate", "find", "ui", "interface"]):
                self.mode = "help"
                return self._handle_ui_question(user_text)
            else:
                # Default to config if unclear
                self.mode = "config"
                self.stage = 1
                return (
                    f"I'll help you configure {self.ai_name}. Let's start!\n\n"
                    + self._ask_config_question(1)
                )

        elif self.mode == "help":
            return self._handle_ui_question(user_text)

        elif self.mode == "config":
            return self._handle_config_response(user_text, lower)

        return None

    def _ask_config_question(self, stage: int) -> str:
        """Ask the next configuration question based on stage."""
        if stage == 1:
            return (
                f"**Question 1 of 5:** What would you like {self.ai_name} to help you with?\n"
                f"(For example: 'Help me write code', 'Manage my projects', 'Answer customer emails', 'Teach me new things', etc.)"
            )
        elif stage == 2:
            return (
                f"**Question 2 of 5:** Who will {self.ai_name} be helping?\n"
                f"(For example: 'Just me', 'My team', 'My customers', 'My students', etc.)"
            )
        elif stage == 3:
            return (
                f"**Question 3 of 5:** Are there any things {self.ai_name} should absolutely NEVER do?\n"
                f"(For example: 'Never send emails without my OK', 'Never change files without asking', 'Never share my data outside', etc.)"
            )
        elif stage == 4:
            return (
                f"**Question 4 of 5:** What types of tasks do you want {self.ai_name} to handle?\n"
                f"(For example: 'Writing, research, and planning', 'Coding and debugging', 'Customer support', 'Teaching and explaining', etc.)"
            )
        elif stage == 5:
            return (
                f"**Question 5 of 5:** Anything else you'd like {self.ai_name} to know about you or how you like to work?\n"
                f"(This is your space — add any preferences, quirks, or special instructions!)"
            )
        return ""

    def _handle_config_response(self, user_text: str, lower: str) -> str:
        """Handle responses during configuration mode."""
        # Check if user switches to help mode
        if any(k in lower for k in ["help", "where", "how to", "navigate"]):
            self.mode = "help"
            return self._handle_ui_question(user_text)

        if self.stage == 1:
            self.gathered_data["purpose"] = user_text
            self.stage = 2
            return f"Perfect! {self.ai_name} will be great at helping with: {user_text}\n\n" + self._ask_config_question(2)

        elif self.stage == 2:
            self.gathered_data["audience"] = user_text
            self.stage = 3
            return f"Got it — {self.ai_name} will be working with: {user_text}\n\n" + self._ask_config_question(3)

        elif self.stage == 3:
            self.gathered_data["guardrails"] = user_text
            self.stage = 4
            return f"Great — those boundaries will keep {self.ai_name} safe and helpful.\n\n" + self._ask_config_question(4)

        elif self.stage == 4:
            self.gathered_data["capabilities"] = user_text
            self.stage = 5
            return f"Excellent choices! Those are perfect for {self.ai_name}.\n\n" + self._ask_config_question(5)

        elif self.stage == 5:
            self.gathered_data["notes"] = user_text
            self.stage = 6
            return self._generate_summary()

        elif self.stage == 6:
            # User confirmed or wants to revise
            if any(k in lower for k in ["yes", "confirm", "save", "write", "looks good", "perfect"]):
                return "__DONE__"
            elif any(k in lower for k in ["restart", "start over", "redo"]):
                self.stage = 0
                self.gathered_data = {k: "" for k in self.gathered_data}
                self.mode = "greeting"
                return self.start()
            elif any(k in lower for k in ["revise", "change", "edit", "fix"]):
                self.stage = 1
                return "Let's revise. I'll ask the questions again. You can change any answer.\n\n" + self._ask_config_question(1)
            else:
                return "Please confirm: type 'yes' to save to Knowledge, 'restart' to start over, or 'revise' to change your answers."

        return None

    def _handle_ui_question(self, user_text: str) -> str:
        """Handle questions about the program interface."""
        lower = user_text.lower()
        
        # Check for keywords in our knowledge base
        for keyword, answer in self.ui_knowledge.items():
            if keyword in lower:
                response = answer
                if self.mode == "help":
                    response += "\n\nDo you need help with anything else, or would you like to configure your AI?"
                return response
        
        # Check if user wants to switch back to config
        if any(k in lower for k in ["configure", "setup", "back to config", "my ai"]):
            self.mode = "config"
            self.stage = 1
            return "Sure! Let's configure your AI.\n\n" + self._ask_config_question(1)
        
        # Default helpful response
        return (
            "I can help you navigate Command Nexus. Here are some things I can explain:\n\n"
            "- How to create an AI (ask about 'AI Factory')\n"
            "- Where to find the AI section\n"
            "- How to configure Knowledge\n"
            "- How to close windows\n"
            "- How to start using an AI\n"
            "- Demo mode and licenses\n\n"
            "What would you like to know? Or type 'configure' to set up your AI."
        )

    def _generate_summary(self) -> str:
        return (
            f"--- Summary for {self.ai_name} ---\n\n"
            f"**Purpose:** {self.gathered_data['purpose']}\n"
            f"**Audience:** {self.gathered_data['audience']}\n"
            f"**Hard Rules:** {self.gathered_data['guardrails']}\n"
            f"**Tasks:** {self.gathered_data['capabilities']}\n"
            f"**Notes:** {self.gathered_data['notes']}\n\n"
            f"Type 'yes' to write this into Knowledge, 'revise' to change answers, or 'restart' to begin again."
        )

    def to_knowledge_content(self) -> dict[str, str]:
        """Convert gathered data into Knowledge section content."""
        return {
            "purpose": self.gathered_data["purpose"],
            "audience": self.gathered_data["audience"],
            "guardrails": self.gathered_data["guardrails"],
            "capabilities": self.gathered_data["capabilities"],
            "notes": self.gathered_data["notes"],
        }


class KnowledgeAIDialog(QDialog):
    """
    Conversational Knowledge AI dialog.
    The user chats with the Knowledge Guide, which asks questions
    and writes answers into Knowledge without exposing structure.
    """

    knowledge_content_ready = pyqtSignal(str, str, dict)  # ai_uuid, ai_name, content_dict

    def __init__(self, ai_name: str, ai_uuid: str, existing_context: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Knowledge Guide — {ai_name}")
        self.resize(700, 600)
        self.ai_name = ai_name
        self.ai_uuid = ai_uuid
        self._conversation = KnowledgeAIConversation(ai_name, ai_uuid, existing_context)
        self._setup_ui()
        self._apply_dark_theme()
        self._start_conversation()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header
        header = QLabel(f"Talking to: {self.ai_name}")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #58a6ff;")
        layout.addWidget(header)

        # Subtitle
        subtitle = QLabel(
            "Just tell me what you want your AI to know — I'll handle all the technical details behind the scenes. "
            "Your answers shape how your AI thinks, behaves, and helps you."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #8b949e; font-style: italic;")
        layout.addWidget(subtitle)

        # Chat display
        self._chat_display = QTextEdit()
        self._chat_display.setReadOnly(True)
        self._chat_display.setStyleSheet(
            " color: #c9d1d9; border: 1px solid #30363d; padding: 8px;"
        )
        layout.addWidget(self._chat_display, stretch=1)

        # Input area
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Type your answer and press Enter...")
        self._input.setStyleSheet(
            " color: #c9d1d9; border: 1px solid #30363d; padding: 6px;"
        )
        self._input.returnPressed.connect(self._on_send)
        input_layout.addWidget(self._input, stretch=1)

        btn_send = QPushButton("Send")
        btn_send.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 6px 16px;")
        btn_send.clicked.connect(self._on_send)
        input_layout.addWidget(btn_send)

        layout.addWidget(input_widget)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save to Knowledge")
        btn_save.setStyleSheet("background-color: #1f6feb; color: white; padding: 6px 16px;")
        btn_save.clicked.connect(self._on_save_to_knowledge)
        btn_layout.addWidget(btn_save)

        btn_cancel = QPushButton("Close")
        btn_cancel.setStyleSheet(" color: #c9d1d9; padding: 6px 16px;")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(btn_layout)

    def _apply_dark_theme(self):
        self.setStyleSheet(" color: #c9d1d9;")

    def _start_conversation(self):
        msg = self._conversation.start()
        self._append_ai(msg)

    def _append_ai(self, text: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._chat_display.append(
            f'<p style="color:#58a6ff; margin:4px 0;"><b>[{timestamp}] Knowledge Guide:</b></p>'
            f'<p style="color:#c9d1d9; margin:4px 0 12px 0;">{text.replace(chr(10), "<br>")}</p>'
        )

    def _append_user(self, text: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._chat_display.append(
            f'<p style="color:#3fb950; margin:4px 0; text-align:right;"><b>[{timestamp}] You:</b></p>'
            f'<p style="color:#c9d1d9; margin:4px 0 12px 0; text-align:right;">{text.replace(chr(10), "<br>")}</p>'
        )

    def _on_send(self):
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        self._append_user(text)

        response = self._conversation.process_response(text)
        if response == "__DONE__":
            self._append_ai(
                f"All set! {self.ai_name} is ready to go with everything you've shared. "
                f"I've written all of this into Knowledge so {self.ai_name} will remember and follow your guidance. "
                f"You can always come back and update things later if you'd like!"
            )
            self.knowledge_content_ready.emit(
                self.ai_uuid,
                self.ai_name,
                self._conversation.to_knowledge_content()
            )
            return
        self._append_ai(response)

    def _on_save_to_knowledge(self):
        content = self._conversation.to_knowledge_content()
        if not any(content.values()):
            QMessageBox.warning(self, "Empty", "No content gathered yet. Please answer the questions first.")
            return

        # Run security screening on the gathered content
        combined_text = "\n".join(f"{k}: {v}" for k, v in content.items() if v)
        scan_result = RecursiveScanner.scan(combined_text, "text")

        if not scan_result.is_safe:
            QMessageBox.critical(
                self, "Security Alert",
                "The gathered content contains suspicious patterns and cannot be saved.\n\n"
                f"Findings: {len(scan_result.findings)}\n"
                f"Trust Score: {scan_result.trust_score:.2f}\n\n"
                "Please revise your answers."
            )
            return

        self.knowledge_content_ready.emit(self.ai_uuid, self.ai_name, content)
        QMessageBox.information(self, "Saved", "Content written to Knowledge successfully.")
        self.accept()
