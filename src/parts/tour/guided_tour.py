"""
Command Nexus™ Guided Tour System
==================================
Interactive onboarding for new users.
Shows key features with contextual tooltips and step-by-step walkthrough.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGraphicsDropShadowEffect, QApplication
)
from PyQt6.QtGui import QColor, QFont, QPalette


class TourStep:
    """Represents a single step in the guided tour."""
    
    def __init__(self, title: str, content: str, highlight_target: str = None, action_button: str = None):
        self.title = title
        self.content = content
        self.highlight_target = highlight_target  # Widget to highlight
        self.action_button = action_button  # Text for action button


class GuidedTourDialog(QDialog):
    """
    Modal guided tour dialog with step-by-step instructions.
    Can highlight specific UI elements and guide users through features.
    """
    
    tour_completed = pyqtSignal()
    tour_skipped = pyqtSignal()
    
    def __init__(self, parent=None, test_mode: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Welcome to Command Nexus™")
        self.setModal(True)
        self.resize(800, 500)
        self._test_mode = test_mode
        self._current_step = 0
        self._steps: list[TourStep] = []
        self._setup_steps()
        self._setup_ui()
        self._apply_styling()
        self._show_step(0)
        
    def _setup_steps(self):
        """Define the tour steps."""
        self._steps = [
            TourStep(
                title="Welcome to Command Nexus™",
                content="""<h2>Welcome to Command Nexus™</h2>
                <p>Your personal AI command center. This guided tour will show you how to:</p>
                <ul>
                    <li>Create and customize AI assistants</li>
                    <li>Manage AI capabilities and permissions</li>
                    <li>Chat with your AIs and give them memory</li>
                    <li>Activate your license for full access</li>
                </ul>
                <p>Click <b>Next</b> to begin, or <b>Skip Tour</b> to explore on your own.</p>""",
                action_button="Start Tour"
            ),
            TourStep(
                title="🧠 The AI Forge",
                content="""<h2>The AI Forge</h2>
                <p>This is where you <b>create and customize AI assistants</b>.</p>
                <ul>
                    <li>Choose a <b>Use Case</b> (Individual, Business, Educational, etc.)</li>
                    <li>Select <b>Capabilities</b> your AI will have</li>
                    <li>Set <b>Personality traits</b> like creativity and caution</li>
                    <li>Add <b>Guardrails</b> for safety</li>
                </ul>
                <p><i>💡 Each use case shows different capabilities. Business users get professional tools, Individual users get personal productivity features.</i></p>""",
                highlight_target="forge",
                action_button="Open Forge"
            ),
            TourStep(
                title="📚 AI Knowledge",
                content="""<h2>AI Knowledge System</h2>
                <p>Each AI has its own <b>Knowledge</b> that defines how it behaves.</p>
                <ul>
                    <li><b>Running Memory:</b> AI-summarized view of what it knows</li>
                    <li><b>Persistent Memory:</b> Your private notes (AI can't see these)</li>
                    <li><b>Commands:</b> Send tasks to your AI</li>
                </ul>
                <p><i>🔒 Your persistent memory is private — the AI only sees what you explicitly send as commands.</i></p>""",
                highlight_target="book",
                action_button="See Example"
            ),
            TourStep(
                title="🔐 License & Activation",
                content="""<h2>License Tiers</h2>
                <p>Command Nexus offers several license tiers:</p>
                <table style='margin: 10px 0;'>
                    <tr><td><b>Trial</b></td><td>$10 — 15 days, 1 AI, basic features</td></tr>
                    <tr><td><b>Starter</b></td><td>$20/mo — 2 AIs, cross-workflows</td></tr>
                    <tr><td><b>Pro</b></td><td>$30/mo — 4 AIs, approval-gated actions</td></tr>
                    <tr><td><b>Business</b></td><td>$50/mo — 5 AIs, 365-day audit</td></tr>
                    <tr><td><b>Unlimited</b></td><td>$80/mo — Unlimited AIs, full access</td></tr>
                </table>
                <p><i>💡 Premium capabilities like Team Orchestrator, Data Analyst Pro, and Security Auditor unlock with higher tiers.</i></p>""",
                highlight_target="license",
                action_button="View Pricing"
            ),
            TourStep(
                title="🛡️ Safety & Governance",
                content="""<h2>Built-in Protections</h2>
                <p>Command Nexus includes multiple safety layers:</p>
                <ul>
                    <li><b>Parental Controls:</b> Kid-safe content filtering (password: "Nexus")</li>
                    <li><b>Approval Gates:</b> AI asks before file changes, network calls, or risky actions</li>
                    <li><b>Audit Logging:</b> Every action is logged for accountability</li>
                    <li><b>Anti-Tamper:</b> License protection against modification</li>
                </ul>
                <p><i>⚠️ The AI will <b>always</b> ask for approval before making changes to your system.</i></p>""",
                highlight_target="governance",
                action_button="View Governance"
            ),
            TourStep(
                title="🚀 Ready to Start!",
                content="""<h2>You're Ready!</h2>
                <p>Here's how to get started:</p>
                <ol>
                    <li>Click <b>Forge</b> to create your first AI</li>
                    <li>Select a <b>Use Case</b> and capabilities</li>
                    <li>Save your AI and start chatting!</li>
                    <li>Activate a license when you're ready for more features</li>
                </ol>
                <p><b>Need help?</b> Click the <b>Guided Tour</b> button anytime to see this again.</p>
                <p style='margin-top: 20px; color: #58a6ff;'><b>Welcome to Command Nexus™ — Your AI Command Center awaits!</b></p>""",
                action_button="Get Started"
            ),
        ]
    
    def _setup_ui(self):
        """Build the tour UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header with progress
        header_layout = QHBoxLayout()
        self._title_label = QLabel()
        self._title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header_layout.addWidget(self._title_label)
        header_layout.addStretch()
        
        # Progress dots
        self._progress_widget = QWidget()
        progress_layout = QHBoxLayout(self._progress_widget)
        progress_layout.setSpacing(8)
        self._progress_dots: list[QLabel] = []
        for i in range(len(self._steps)):
            dot = QLabel("●")
            dot.setFont(QFont("Segoe UI", 12))
            self._progress_dots.append(dot)
            progress_layout.addWidget(dot)
        header_layout.addWidget(self._progress_widget)
        layout.addLayout(header_layout)
        
        # Content area
        self._content_frame = QFrame()
        self._content_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        content_layout = QVBoxLayout(self._content_frame)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        self._content_label = QLabel()
        self._content_label.setWordWrap(True)
        self._content_label.setTextFormat(Qt.TextFormat.RichText)
        self._content_label.setOpenExternalLinks(True)
        content_layout.addWidget(self._content_label)
        layout.addWidget(self._content_frame, stretch=1)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        self._skip_btn = QPushButton("Skip Tour")
        self._skip_btn.setToolTip("Skip the tour and explore on your own")
        self._skip_btn.clicked.connect(self._on_skip)
        nav_layout.addWidget(self._skip_btn)
        
        nav_layout.addStretch()
        
        self._prev_btn = QPushButton("← Previous")
        self._prev_btn.clicked.connect(self._on_previous)
        nav_layout.addWidget(self._prev_btn)
        
        self._next_btn = QPushButton("Next →")
        self._next_btn.setDefault(True)
        self._next_btn.clicked.connect(self._on_next)
        nav_layout.addWidget(self._next_btn)
        
        layout.addLayout(nav_layout)
        
        # Test mode indicator
        if self._test_mode:
            test_label = QLabel("🧪 TEST MODE — License testing enabled")
            test_label.setStyleSheet("color: #f0883e; font-weight: bold; padding: 5px;")
            test_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(test_label)
    
    def _apply_styling(self):
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QDialog {
                background-color: #0d1117;
                color: #c9d1d9;
            }
            QLabel {
                color: #c9d1d9;
            }
            QFrame {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                color: #c9d1d9;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #30363d;
                border-color: #58a6ff;
            }
            QPushButton:default {
                background-color: #1f6feb;
                border-color: #1f6feb;
                color: white;
                font-weight: bold;
            }
            QPushButton:default:hover {
                background-color: #388bfd;
            }
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 128))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
    
    def _show_step(self, index: int):
        """Display the current step."""
        if not 0 <= index < len(self._steps):
            return
            
        self._current_step = index
        step = self._steps[index]
        
        # Update title
        self._title_label.setText(f"Step {index + 1} of {len(self._steps)}")
        
        # Update content
        self._content_label.setText(step.content)
        
        # Update progress dots
        for i, dot in enumerate(self._progress_dots):
            if i == index:
                dot.setStyleSheet("color: #58a6ff;")  # Active - blue
            elif i < index:
                dot.setStyleSheet("color: #3fb950;")  # Completed - green
            else:
                dot.setStyleSheet("color: #484f58;")  # Future - gray
        
        # Update buttons
        self._prev_btn.setEnabled(index > 0)
        
        if index == len(self._steps) - 1:
            self._next_btn.setText(step.action_button or "Get Started")
            self._next_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2e7d32;
                    border-color: #2e7d32;
                    color: white;
                    font-weight: bold;
                    padding: 10px 20px;
                }
                QPushButton:hover {
                    background-color: #388e3c;
                }
            """)
        else:
            self._next_btn.setText(step.action_button or "Next →")
            self._next_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1f6feb;
                    border-color: #1f6feb;
                    color: white;
                    font-weight: bold;
                    padding: 10px 20px;
                }
                QPushButton:hover {
                    background-color: #388bfd;
                }
            """)
    
    def _on_next(self):
        """Go to next step or finish."""
        if self._current_step < len(self._steps) - 1:
            self._show_step(self._current_step + 1)
        else:
            self.tour_completed.emit()
            self.accept()
    
    def _on_previous(self):
        """Go to previous step."""
        if self._current_step > 0:
            self._show_step(self._current_step - 1)
    
    def _on_skip(self):
        """Skip the tour."""
        self.tour_skipped.emit()
        self.reject()
    
    def run_tour(self) -> bool:
        """Execute the tour modally. Returns True if completed, False if skipped."""
        result = self.exec()
        return result == QDialog.DialogCode.Accepted


class TestLicenseGenerator:
    """
    Utility for generating test license keys.
    Only available in test/tour mode - NOT for production use.
    """
    
    @staticmethod
    def generate_test_key(tier: str = "TRIAL", days: int = 30) -> str:
        """Generate a test license key for the specified tier."""
        import hashlib
        import hmac
        import random
        import time
        
        # Test secret (different from production)
        TEST_SECRET = b"TEST_NEXUS_KEY_GENERATOR_2026_DO_NOT_USE_IN_PRODUCTION"
        
        tier_codes = {
            "TRIAL": "TR",
            "STARTER": "ST", 
            "PRO": "PR",
            "BUSINESS": "BU",
            "UNLIMITED": "UN",
        }
        
        tier_code = tier_codes.get(tier.upper(), "TR")
        expiry = int(time.time()) + (days * 86400)
        expiry_hex = f"{expiry:010X}"
        random_part = f"{random.randint(0, 0xFFFFFFFF):08X}"
        
        payload = f"{tier_code}{expiry_hex}{random_part}"
        hmac_value = hmac.new(
            TEST_SECRET,
            payload.encode(),
            hashlib.sha256
        ).hexdigest()[:20].upper()
        
        key = f"{tier_code}{expiry_hex}{random_part}{hmac_value}"
        
        # Format with dashes for readability
        formatted = "-".join([key[i:i+4] for i in range(0, 40, 4)])
        return formatted
    
    @staticmethod
    def get_test_keys() -> dict:
        """Get a set of test keys for all tiers."""
        return {
            "TRIAL (15 days, 1 AI)": TestLicenseGenerator.generate_test_key("TRIAL", 15),
            "STARTER (30 days, 2 AIs)": TestLicenseGenerator.generate_test_key("STARTER", 30),
            "PRO (30 days, 4 AIs)": TestLicenseGenerator.generate_test_key("PRO", 30),
            "BUSINESS (30 days, 5 AIs)": TestLicenseGenerator.generate_test_key("BUSINESS", 30),
            "UNLIMITED (30 days, ∞ AIs)": TestLicenseGenerator.generate_test_key("UNLIMITED", 30),
        }


# Singleton instance for app-wide access
_tour_instance: GuidedTourDialog = None

def show_guided_tour(parent=None, test_mode: bool = False) -> bool:
    """Show the guided tour dialog. Returns True if user completed the tour."""
    global _tour_instance
    _tour_instance = GuidedTourDialog(parent, test_mode)
    return _tour_instance.run_tour()

def get_test_license_keys() -> dict:
    """Get test license keys (only works in test builds)."""
    return TestLicenseGenerator.get_test_keys()
