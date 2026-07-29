"""
Book AI Dialog — Command Nexus
A conversational interface for The Book that asks questions,
gathers intent, and writes into the book WITHOUT revealing
internal structure to the user.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QLineEdit, QPushButton, QSplitter, QWidget, QScrollArea,
    QFrame, QMessageBox, QProgressDialog
)

from ...core.governance import GovernanceEngine
from ...core.recursive_scanner import RecursiveScanner


class BookAIConversation:
    """
    State machine for the Book AI conversation flow.
    Asks intuitive questions to build the AI's memory and instructions.
    Never reveals the internal Book structure to the user.
    """

    def __init__(self, ai_name: str, ai_uuid: str, existing_context: str = ""):
        self.ai_name = ai_name
        self.ai_uuid = ai_uuid
        self.existing_context = existing_context
        self.stage = 0
        self.history: list[dict] = []
        self.gathered_data: dict[str, str] = {
            "purpose": "",
            "audience": "",
            "instructions": "",
            "persistent_memory": "",
            "general_memory": "",
            "preferences": "",
            "guardrails": "",
        }

    def start(self) -> str:
        self.stage = 1
        return (
            f"Welcome! I'm here to help you build {self.ai_name} exactly the way you want.\n\n"
            f"Just let me know what you'd like your agent to know, and we'll get started on training them with that information. "
            f"You don't need to worry about any technical details — I handle all of that behind the scenes.\n\n"
            f"I'll ask you a few questions about what {self.ai_name} is for, how you'll use them, and what they should remember.\n\n"
            f"**Question 1 of 7:** What would you like {self.ai_name} to help you with?\n"
            f"(For example: 'Help me write code', 'Manage my projects', 'Answer customer emails', 'Teach me new things', etc.)"
        )

    def process_response(self, user_text: str) -> str | None:
        """Process user input and return the next AI message, or None if done."""
        user_text = user_text.strip()
        if not user_text:
            return "Please provide an answer so I can continue."

        self.history.append({"role": "user", "text": user_text, "stage": self.stage})

        if self.stage == 1:
            self.gathered_data["purpose"] = user_text
            self.stage = 2
            return (
                f"Perfect! {self.ai_name} will be great at helping with: {user_text}\n\n"
                f"**Question 2 of 7:** Who will {self.ai_name} be helping?\n"
                f"(For example: 'Just me', 'My team', 'My customers', 'My students', etc.)"
            )

        elif self.stage == 2:
            self.gathered_data["audience"] = user_text
            self.stage = 3
            return (
                f"Got it — {self.ai_name} will be working with: {user_text}\n\n"
                f"**Question 3 of 7:** What specific instructions should {self.ai_name} always follow?\n"
                f"(For example: 'Always ask before making changes', 'Keep responses short and direct', "
                f"'Use formal language with customers', 'Explain your reasoning before giving answers', etc.)"
            )

        elif self.stage == 3:
            self.gathered_data["instructions"] = user_text
            self.stage = 4
            return (
                f"Great — those instructions will guide how {self.ai_name} behaves.\n\n"
                f"**Question 4 of 7:** What important things should {self.ai_name} ALWAYS remember about you?\n"
                f"These are like long-term memories — things that won't change often.\n"
                f"(For example: 'I prefer Python over JavaScript', 'My business is called X', 'I have a gluten allergy', 'My team uses Slack not email')"
            )

        elif self.stage == 4:
            self.gathered_data["persistent_memory"] = user_text
            self.stage = 5
            return (
                f"Excellent — {self.ai_name} will always keep that in mind.\n\n"
                f"**Question 5 of 7:** What are some general things {self.ai_name} should know, but that might change over time?\n"
                f"These are like current context — useful now but not permanent.\n"
                f"(For example: 'I'm currently working on Project Alpha', 'My focus this month is improving customer retention', 'I'm learning Spanish')"
            )

        elif self.stage == 5:
            self.gathered_data["general_memory"] = user_text
            self.stage = 6
            return (
                f"Noted — {self.ai_name} will treat those as current context that can be updated.\n\n"
                f"**Question 6 of 7:** What are your personal preferences for how {self.ai_name} interacts with you?\n"
                f"(For example: 'I like detailed explanations', 'Keep it brief — bullet points only', "
                f"'Be casual and friendly', 'Be direct and professional', 'Always suggest alternatives when you can't do something')"
            )

        elif self.stage == 6:
            self.gathered_data["preferences"] = user_text
            self.stage = 7
            return (
                f"Perfect — {self.ai_name} will interact with you exactly that way.\n\n"
                f"**Question 7 of 7:** Are there any hard boundaries or things {self.ai_name} should absolutely NEVER do?\n"
                f"(For example: 'Never send emails without my OK', 'Never change files without asking', "
                f"'Never share my data outside this app', 'Never pretend to know something you don't')"
            )

        elif self.stage == 7:
            self.gathered_data["guardrails"] = user_text
            self.stage = 8
            return self._generate_summary()

        elif self.stage == 8:
            # User confirmed or wants to revise
            lower = user_text.lower()
            if any(k in lower for k in ["yes", "confirm", "save", "write", "looks good", "perfect", "go"]):
                return "__DONE__"
            elif any(k in lower for k in ["restart", "start over", "redo"]):
                self.stage = 0
                self.gathered_data = {k: "" for k in self.gathered_data}
                return self.start()
            elif any(k in lower for k in ["revise", "change", "edit", "fix"]):
                self.stage = 1
                return (
                    "Let's revise. I'll ask the questions again. You can change any answer.\n\n"
                    + self.start()
                )
            else:
                return (
                    "Please confirm: type 'yes' to save everything, 'restart' to start over, "
                    "or 'revise' to change your answers."
                )

        return None

    def _generate_summary(self) -> str:
        return (
            f"--- Summary for {self.ai_name} ---\n\n"
            f"**Purpose:** {self.gathered_data['purpose']}\n"
            f"**Audience:** {self.gathered_data['audience']}\n"
            f"**Instructions:** {self.gathered_data['instructions']}\n"
            f"**Long-term memories:** {self.gathered_data['persistent_memory']}\n"
            f"**Current context:** {self.gathered_data['general_memory']}\n"
            f"**Preferences:** {self.gathered_data['preferences']}\n"
            f"**Boundaries:** {self.gathered_data['guardrails']}\n\n"
            f"Type 'yes' to save everything, 'revise' to change answers, or 'restart' to begin again."
        )

    def to_book_content(self) -> dict[str, str]:
        """
        Convert gathered data into Book section content.
        Structured for the AI's internal use while remaining hidden from users.
        """
        return {
            "active_instructions": self.gathered_data["instructions"],
            "persistent_memory": self.gathered_data["persistent_memory"],
            "general_memory": self.gathered_data["general_memory"],
            "preferences": self.gathered_data["preferences"],
            "guardrails": self.gathered_data["guardrails"],
            "purpose": self.gathered_data["purpose"],
            "audience": self.gathered_data["audience"],
        }


class BookAIDialog(QDialog):
    """
    Conversational Book AI dialog.
    The user chats with the Book Keeper, which asks questions
    and writes answers into the Book without exposing structure.
    """

    book_content_ready = Signal(str, str, dict)  # ai_uuid, ai_name, content_dict

    def __init__(self, ai_name: str, ai_uuid: str, existing_context: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Book Keeper — {ai_name}")
        self.resize(700, 600)
        self.ai_name = ai_name
        self.ai_uuid = ai_uuid
        self._conversation = BookAIConversation(ai_name, ai_uuid, existing_context)
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
            "background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d; padding: 8px;"
        )
        layout.addWidget(self._chat_display, stretch=1)

        # Input area
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Type your answer and press Enter...")
        self._input.setStyleSheet(
            "background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d; padding: 6px;"
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
        btn_save = QPushButton("Save to Book")
        btn_save.setStyleSheet("background-color: #1f6feb; color: white; padding: 6px 16px;")
        btn_save.clicked.connect(self._on_save_to_book)
        btn_layout.addWidget(btn_save)

        btn_cancel = QPushButton("Close")
        btn_cancel.setStyleSheet("background-color: #21262d; color: #c9d1d9; padding: 6px 16px;")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(btn_layout)

    def _apply_dark_theme(self):
        self.setStyleSheet("background-color: #161b22; color: #c9d1d9;")

    def _start_conversation(self):
        msg = self._conversation.start()
        self._append_ai(msg)

    def _append_ai(self, text: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._chat_display.append(
            f'<p style="color:#58a6ff; margin:4px 0;"><b>[{timestamp}] Book Keeper:</b></p>'
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
                f"I've written all of this into the Book so {self.ai_name} will remember and follow your guidance. "
                f"You can always come back and update things later if you'd like!"
            )
            self.book_content_ready.emit(
                self.ai_uuid,
                self.ai_name,
                self._conversation.to_book_content()
            )
            return
        self._append_ai(response)

    def _on_save_to_book(self):
        content = self._conversation.to_book_content()
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

        self.book_content_ready.emit(self.ai_uuid, self.ai_name, content)
        QMessageBox.information(self, "Saved", "Content written to the Book successfully.")
        self.accept()
