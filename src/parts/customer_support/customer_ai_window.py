"""
Command Nexus™ Customer AI Support Window
==========================================
Integrated customer service AI with learning capabilities.
Connects to the adaptive CustomerAIModel and provides a chat interface.
"""
from __future__ import annotations

# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QListWidget, QListWidgetItem,
    QSplitter, QFrame, QComboBox, QGroupBox, QFormLayout, QMessageBox
)
from PySide6.QtGui import QFont, QColor

from ...core.customer_ai_public import CustomerAIPublic, ToneStyle
from ...core.resource_gate import get_resource_gate


class CustomerAIWindow(QMainWindow):
    """
    Customer Service AI interface with learning capabilities.
    Allows real-time customer communication with adaptive responses.
    """
    
    # Signals for integration with main app
    escalation_needed = Signal(str, str)  # customer_id, issue_type
    
    def __init__(self, audit_logger=None, parent=None, resource_gate=None):
        super().__init__(parent)
        self.setWindowTitle("Command Nexus™ — Customer AI")
        self.resize(1000, 700)
        self._audit = audit_logger
        self._resource_gate = resource_gate or get_resource_gate()
        
        # Initialize the RESTRICTED AI model (public/customer-facing)
        # This version NEVER reveals internal Book mechanics
        self._ai = CustomerAIPublic(model_id="customer_service_public")
        
        # Current conversation state
        self._current_customer_id: str = ""
        self._current_customer_name: str = ""
        self._chat_history: list = []
        
        self._setup_ui()
        self._apply_styling()
        
        # Welcome message
        self._add_system_message("Customer AI initialized and ready. Select or create a customer to begin.")
    
    def _setup_ui(self):
        """Build the customer AI interface."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Left panel - Customer list and controls
        left_panel = QWidget()
        left_panel.setMaximumWidth(300)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header = QLabel("🤖 Customer AI")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #58a6ff; padding-bottom: 10px;")
        left_layout.addWidget(header)
        
        # AI Stats
        stats_group = QGroupBox("AI Learning Stats")
        stats_layout = QFormLayout(stats_group)
        self._stats_customers = QLabel("0")
        self._stats_interactions = QLabel("0")
        self._stats_success = QLabel("0%")
        stats_layout.addRow("Customers:", self._stats_customers)
        stats_layout.addRow("Interactions:", self._stats_interactions)
        stats_layout.addRow("Success Rate:", self._stats_success)
        left_layout.addWidget(stats_group)
        
        # New customer section
        new_customer_group = QGroupBox("New Customer")
        new_customer_layout = QVBoxLayout(new_customer_group)
        
        self._new_customer_id = QLineEdit()
        self._new_customer_id.setPlaceholderText("Customer ID (e.g., CUST-001)")
        new_customer_layout.addWidget(self._new_customer_id)
        
        self._new_customer_name = QLineEdit()
        self._new_customer_name.setPlaceholderText("Customer Name")
        new_customer_layout.addWidget(self._new_customer_name)
        
        self._tone_selector = QComboBox()
        self._tone_selector.addItems(["Professional", "Friendly", "Technical", "Empathetic"])
        self._tone_selector.setToolTip("Select the AI's communication tone for this customer")
        new_customer_layout.addWidget(QLabel("Preferred Tone:"))
        new_customer_layout.addWidget(self._tone_selector)
        
        btn_start = QPushButton("Start Conversation")
        btn_start.clicked.connect(self._start_new_conversation)
        btn_start.setStyleSheet("background-color: #238636; color: white; font-weight: bold;")
        new_customer_layout.addWidget(btn_start)
        
        left_layout.addWidget(new_customer_group)
        
        # Recent customers list
        left_layout.addWidget(QLabel("Recent Customers:"))
        self._customer_list = QListWidget()
        self._customer_list.itemClicked.connect(self._on_customer_selected)
        left_layout.addWidget(self._customer_list, stretch=1)
        
        # Refresh button
        btn_refresh = QPushButton("🔄 Refresh Stats")
        btn_refresh.clicked.connect(self._update_stats)
        left_layout.addWidget(btn_refresh)
        
        main_layout.addWidget(left_panel)
        
        # Right panel - Chat interface
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(15, 15, 15, 15)
        
        # Current customer info
        self._customer_info = QLabel("No active customer")
        self._customer_info.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self._customer_info.setStyleSheet("color: #8b949e; padding: 10px;  border-radius: 6px;")
        right_layout.addWidget(self._customer_info)
        
        # Chat display
        self._chat_display = QTextEdit()
        self._chat_display.setReadOnly(True)
        self._chat_display.setPlaceholderText("Conversation will appear here...")
        self._chat_display.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._chat_display.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right_layout.addWidget(self._chat_display, stretch=1)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self._message_input = QLineEdit()
        self._message_input.setPlaceholderText("Type customer message here...")
        self._message_input.returnPressed.connect(self._send_message)
        input_layout.addWidget(self._message_input, stretch=1)
        
        btn_send = QPushButton("Send")
        btn_send.clicked.connect(self._send_message)
        btn_send.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 8px 20px;")
        input_layout.addWidget(btn_send)
        
        right_layout.addLayout(input_layout)
        
        # Quick response buttons
        quick_layout = QHBoxLayout()
        quick_layout.addWidget(QLabel("Quick responses:"))
        
        quick_buttons = [
            ("👋 Greeting", "Hello! Welcome to Command Nexus!"),
            ("💰 Pricing", "Can you tell me about your pricing?"),
            ("🆘 Help", "I need help with something"),
            ("😠 Complaint", "I'm having a problem and I'm frustrated"),
        ]
        
        for label, text in quick_buttons:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, t=text: self._insert_quick_message(t))
            btn.setStyleSheet(" color: #c9d1d9;")
            quick_layout.addWidget(btn)
        
        quick_layout.addStretch()
        right_layout.addLayout(quick_layout)
        
        # Feedback buttons
        feedback_layout = QHBoxLayout()
        feedback_layout.addWidget(QLabel("Was this response helpful?"))
        
        btn_yes = QPushButton("✅ Yes")
        btn_yes.clicked.connect(lambda: self._provide_feedback(True))
        btn_yes.setStyleSheet("background-color: #238636; color: white;")
        feedback_layout.addWidget(btn_yes)
        
        btn_no = QPushButton("❌ No")
        btn_no.clicked.connect(lambda: self._provide_feedback(False))
        btn_no.setStyleSheet("background-color: #da3633; color: white;")
        feedback_layout.addWidget(btn_no)
        
        btn_escalate = QPushButton("⚠️ Escalate")
        btn_escalate.clicked.connect(self._escalate_issue)
        btn_escalate.setStyleSheet("background-color: #f0883e; color: white; font-weight: bold;")
        feedback_layout.addWidget(btn_escalate)
        
        feedback_layout.addStretch()
        right_layout.addLayout(feedback_layout)
        
        main_layout.addWidget(right_panel, stretch=1)
        
        # Load initial stats
        self._update_stats()
        self._load_customer_list()
    
    def _apply_styling(self):
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QMainWindow {
                
            }
            QWidget {
                
                color: #c9d1d9;
            }
            QGroupBox {
                border: 1px solid #30363d;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit, QTextEdit, QComboBox {
                
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 8px;
                color: #c9d1d9;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #58a6ff;
            }
            QListWidget {
                
                border: 1px solid #30363d;
                border-radius: 6px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #21262d;
            }
            QListWidget::item:selected {
                background-color: #1f6feb;
            }
            QPushButton {
                
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 6px 12px;
                color: #c9d1d9;
            }
            QPushButton:hover {
                background-color: #30363d;
                border-color: #58a6ff;
            }
        """)
    
    def _start_new_conversation(self):
        """Start a new conversation with a customer."""
        customer_id = self._new_customer_id.text().strip()
        customer_name = self._new_customer_name.text().strip()
        
        if not customer_id:
            QMessageBox.warning(self, "Missing Information", "Please enter a Customer ID.")
            return
        
        self._current_customer_id = customer_id
        self._current_customer_name = customer_name
        
        # Get selected tone
        tone_map = {
            "Professional": ToneStyle.PROFESSIONAL,
            "Friendly": ToneStyle.FRIENDLY,
            "Technical": ToneStyle.TECHNICAL,
            "Empathetic": ToneStyle.EMPATHETIC,
        }
        tone = tone_map.get(self._tone_selector.currentText(), ToneStyle.PROFESSIONAL)
        
        # Update UI
        self._update_customer_info()
        self._chat_display.clear()
        self._add_system_message(f"Started conversation with {customer_name or customer_id}")
        
        # Audit log
        if self._audit:
            self._audit.log(
                tool="CustomerAI",
                action="CONVERSATION_STARTED",
                target=f"Customer: {customer_id}",
                approved=True,
                status="info"
            )
        
        # Refresh customer list
        self._load_customer_list()
    
    def _on_customer_selected(self, item: QListWidgetItem):
        """Load a previous customer conversation."""
        customer_id = item.data(Qt.ItemDataRole.UserRole)
        if customer_id:
            self._current_customer_id = customer_id
            profile = self._ai.get_or_create_profile(customer_id)
            self._current_customer_name = profile.name or ""
            self._update_customer_info()
            self._load_conversation_history(profile)
    
    def _send_message(self):
        """Send a customer message to the AI."""
        message = self._message_input.text().strip()
        if not message:
            return
        
        if not self._current_customer_id:
            QMessageBox.warning(self, "No Customer", "Please start a new conversation or select a customer first.")
            return
        
        # Add customer message to chat
        self._add_customer_message(message)
        self._message_input.clear()
        
        # Get AI response
        tone_map = {
            "Professional": ToneStyle.PROFESSIONAL,
            "Friendly": ToneStyle.FRIENDLY,
            "Technical": ToneStyle.TECHNICAL,
            "Empathetic": ToneStyle.EMPATHETIC,
        }
        tone = tone_map.get(self._tone_selector.currentText())
        
        result = self._ai.process_message(
            message,
            customer_id=self._current_customer_id,
            customer_name=self._current_customer_name,
            preferred_tone=tone
        )
        
        # ── NEXUS cognitive learning (additive) ──
        try:
            from ...core.nexus_cognitive.snap_in_adapter import get_nexus
            _n = get_nexus()
            if _n:
                _n.learn_from_interaction(
                    self._current_customer_id, message,
                    result.get('intent', 'customer_support'),
                    success=not result.get('escalation_needed', False),
                )
        except Exception:
            pass
        
        # Add AI response to chat
        self._add_ai_message(result['response'], result['intent'], result['tone'])
        
        # Check for escalation
        if result.get('escalation_needed'):
            self._add_system_message("⚠️ This conversation may need escalation to a human agent.")
        
        # Update stats
        self._update_stats()
        
        # Audit log
        if self._audit:
            self._audit.log(
                tool="CustomerAI",
                action="AI_RESPONSE_GENERATED",
                target=f"Intent: {result['intent']}, Customer: {self._current_customer_id}",
                approved=True,
                status="info"
            )
    
    def _insert_quick_message(self, text: str):
        """Insert a quick message template."""
        self._message_input.setText(text)
        self._message_input.setFocus()
    
    def _provide_feedback(self, helpful: bool):
        """Provide feedback on the last AI response."""
        if not self._current_customer_id:
            return
        
        # Get the last interaction from the profile
        profile = self._ai.get_or_create_profile(self._current_customer_id)
        if profile.interaction_history:
            last_interaction = profile.interaction_history[-1]
            self._ai.provide_feedback(
                self._current_customer_id,
                last_interaction.timestamp,
                helpful,
                "User marked as helpful" if helpful else "User marked as not helpful"
            )
            
            self._add_system_message(f"✅ Feedback recorded: {'Helpful' if helpful else 'Not helpful'}")
            self._update_stats()
    
    def _escalate_issue(self):
        """Escalate the current issue to a human agent."""
        if not self._current_customer_id:
            return
        
        self.escalation_needed.emit(self._current_customer_id, "manual_escalation")
        self._add_system_message("🚨 Issue escalated to human support team.")
        
        if self._audit:
            self._audit.log(
                tool="CustomerAI",
                action="ISSUE_ESCALATED",
                target=f"Customer: {self._current_customer_id}",
                approved=True,
                status="warning"
            )
    
    def _update_customer_info(self):
        """Update the customer info display."""
        if self._current_customer_id:
            name = self._current_customer_name or "Unknown"
            self._customer_info.setText(f"👤 {name} (ID: {self._current_customer_id})")
            self._customer_info.setStyleSheet(
                "color: #58a6ff; padding: 10px;  border-radius: 6px; font-weight: bold;"
            )
        else:
            self._customer_info.setText("No active customer")
            self._customer_info.setStyleSheet(
                "color: #8b949e; padding: 10px;  border-radius: 6px;"
            )
    
    def _add_customer_message(self, message: str):
        """Add a customer message to the chat display."""
        self._chat_display.append(
            f'<div style="margin: 10px 0; padding: 10px;  border-radius: 8px; border-left: 3px solid #58a6ff;">'
            f'<b style="color: #58a6ff;">Customer:</b><br>{message}'
            f'</div>'
        )
    
    def _add_ai_message(self, message: str, intent: str, tone: str):
        """Add an AI message to the chat display."""
        self._chat_display.append(
            f'<div style="margin: 10px 0; padding: 10px; background-color: #1f6feb22; border-radius: 8px; border-left: 3px solid #238636;">'
            f'<b style="color: #238636;">🤖 AI ({intent}, {tone}):</b><br>{message}'
            f'</div>'
        )
    
    def _add_system_message(self, message: str):
        """Add a system message to the chat display."""
        self._chat_display.append(
            f'<div style="margin: 10px 0; padding: 8px; text-align: center; color: #8b949e; font-style: italic;">'
            f'— {message} —'
            f'</div>'
        )
    
    def _load_conversation_history(self, profile):
        """Load previous conversation history."""
        self._chat_display.clear()
        
        if not profile.interaction_history:
            self._add_system_message("New customer - no previous history")
            return
        
        self._add_system_message(f"Loaded {len(profile.interaction_history)} previous interactions")
        
        for interaction in profile.interaction_history[-10:]:  # Show last 10
            self._add_customer_message(interaction.query)
            self._add_ai_message(interaction.response, interaction.intent, "historical")
    
    def _update_stats(self):
        """Update the AI statistics display."""
        stats = self._ai.get_stats()
        self._stats_customers.setText(str(stats['total_customers']))
        self._stats_interactions.setText(str(stats['total_interactions']))
        self._stats_success.setText(f"{stats['success_rate']:.0%}")
    
    def _load_customer_list(self):
        """Load the list of recent customers."""
        self._customer_list.clear()
        
        for customer_id, profile in self._ai._profiles.items():
            display_name = profile.name or customer_id
            item = QListWidgetItem(f"{display_name} ({len(profile.interaction_history)} chats)")
            item.setData(Qt.ItemDataRole.UserRole, customer_id)
            self._customer_list.addItem(item)


# Integration with main Command Nexus app
def create_customer_ai_window(audit_logger=None, parent=None) -> CustomerAIWindow:
    """Factory function to create the Customer AI window."""
    return CustomerAIWindow(audit_logger=audit_logger, parent=parent)
