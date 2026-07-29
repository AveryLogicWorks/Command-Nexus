"""
Command Nexus™ Interactive Hands-On Tour
=========================================
A step-by-step tutorial that actually demonstrates features.
Highlights UI elements, shows arrows, and guides users through real actions.
"""
from __future__ import annotations

import math
from PySide6.QtCore import Qt, QTimer, Signal, QPoint, QRect, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGraphicsDropShadowEffect, QApplication,
    QMainWindow, QToolTip, QGraphicsOpacityEffect
)
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPolygon, QScreen, QCursor


class TourOverlay(QWidget):
    """
    Semi-transparent overlay that highlights UI elements during tour.
    Draws arrows, circles, and cutouts to focus attention.
    This is a child widget that covers the parent window.
    """
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        # Make this widget transparent for mouse events so clicks pass through
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        # No default background - we draw it ourselves in paintEvent
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        
        self.setStyleSheet("background: transparent;")
        
        self._highlight_rect: QRect = None
        self._arrow_points: list = []
        self._pulse_radius: int = 0
        self._pulse_animation = 0
        
        # Timer for pulsing animation
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate_pulse)
        self._timer.start(50)
    
    def set_highlight(self, widget: QWidget, padding: int = 25):
        """Set a widget to highlight with a pulsing border around it (not on top)."""
        if widget and widget.isVisible():
            # Get widget geometry in screen coordinates
            geo = widget.geometry()
            top_left = widget.mapToGlobal(geo.topLeft())
            bottom_right = widget.mapToGlobal(geo.bottomRight())
            
            # Convert to parent window coordinates
            if self.parent():
                top_left = self.parent().mapFromGlobal(top_left)
                bottom_right = self.parent().mapFromGlobal(bottom_right)
            
            # Calculate widget size
            width = bottom_right.x() - top_left.x()
            height = bottom_right.y() - top_left.y()
            
            # Create highlight rect with generous padding AROUND the widget
            # so the border doesn't obscure the widget itself
            self._highlight_rect = QRect(
                top_left.x() - padding,
                top_left.y() - padding,
                width + padding * 2,
                height + padding * 2
            )
            self.update()
    
    def set_arrow(self, from_pos: QPoint, to_pos: QPoint):
        """Draw an arrow pointing from one position to another."""
        self._arrow_points = [from_pos, to_pos]
        self.update()
    
    def clear_highlight(self):
        """Clear the current highlight."""
        self._highlight_rect = None
        self._arrow_points = []
        self.update()
    
    def _animate_pulse(self):
        """Animate the pulsing highlight effect."""
        self._pulse_animation = (self._pulse_animation + 1) % 20
        self.update()
    
    def paintEvent(self, event):
        """Paint the animated highlight border and arrows.
        
        Instead of a full dark overlay (which obscures everything),
        we just draw a bright animated border around the target widget.
        This is more reliable and doesn't block the UI.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self._highlight_rect:
            # Calculate pulse animation value (0 to 15)
            pulse = abs(self._pulse_animation - 10) + 5
            
            # Draw multiple concentric animated borders for visibility
            
            # Outer glow (largest, most transparent)
            outer_rect = self._highlight_rect.adjusted(-pulse * 2, -pulse * 2, pulse * 2, pulse * 2)
            outer_pen = QPen(QColor(88, 166, 255, 60), 6)
            painter.setPen(outer_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(outer_rect, 12, 12)
            
            # Middle glow
            mid_rect = self._highlight_rect.adjusted(-pulse, -pulse, pulse, pulse)
            mid_pen = QPen(QColor(88, 166, 255, 120), 4)
            painter.setPen(mid_pen)
            painter.drawRoundedRect(mid_rect, 10, 10)
            
            # Main bright border
            main_pen = QPen(QColor(88, 166, 255), 3)
            painter.setPen(main_pen)
            painter.drawRoundedRect(self._highlight_rect, 8, 8)
            
            # Inner bright border
            inner_rect = self._highlight_rect.adjusted(3, 3, -3, -3)
            inner_pen = QPen(QColor(255, 255, 255, 230), 2)
            painter.setPen(inner_pen)
            painter.drawRoundedRect(inner_rect, 6, 6)
            
            # Draw corner accents
            self._draw_corners(painter, self._highlight_rect, QColor(255, 193, 7))
        
        # Draw arrow
        if len(self._arrow_points) == 2:
            self._draw_arrow(painter, self._arrow_points[0], self._arrow_points[1])
    
    def _draw_corners(self, painter: QPainter, rect: QRect, color: QColor):
        """Draw corner accent marks for extra visibility."""
        corner_size = 15
        pen = QPen(color, 3)
        painter.setPen(pen)
        
        # Top-left corner
        painter.drawLine(rect.left(), rect.top() + corner_size, rect.left(), rect.top())
        painter.drawLine(rect.left(), rect.top(), rect.left() + corner_size, rect.top())
        
        # Top-right corner
        painter.drawLine(rect.right() - corner_size, rect.top(), rect.right(), rect.top())
        painter.drawLine(rect.right(), rect.top(), rect.right(), rect.top() + corner_size)
        
        # Bottom-left corner
        painter.drawLine(rect.left(), rect.bottom() - corner_size, rect.left(), rect.bottom())
        painter.drawLine(rect.left(), rect.bottom(), rect.left() + corner_size, rect.bottom())
        
        # Bottom-right corner
        painter.drawLine(rect.right() - corner_size, rect.bottom(), rect.right(), rect.bottom())
        painter.drawLine(rect.right(), rect.bottom(), rect.right(), rect.bottom() - corner_size)
    
    def _draw_arrow(self, painter: QPainter, start: QPoint, end: QPoint):
        """Draw an animated arrow from start to end point."""
        pen = QPen(QColor(255, 193, 7), 4)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(255, 193, 7)))
        
        # Draw line
        painter.drawLine(start, end)
        
        # Draw arrowhead
        angle = math.atan2(end.y() - start.y(), end.x() - start.x())
        arrow_size = 20
        
        p1 = QPoint(
            int(end.x() - arrow_size * math.cos(angle - math.pi/6)),
            int(end.y() - arrow_size * math.sin(angle - math.pi/6))
        )
        p2 = QPoint(
            int(end.x() - arrow_size * math.cos(angle + math.pi/6)),
            int(end.y() - arrow_size * math.sin(angle + math.pi/6))
        )
        
        arrow_head = QPolygon([end, p1, p2])
        painter.drawPolygon(arrow_head)
    
    def resize_to_parent(self):
        """Resize overlay to cover the entire parent window and raise to top."""
        if self.parent():
            self.setGeometry(self.parent().rect())
            # Ensure overlay is on top of all sibling widgets
            self.raise_()


class HandsOnTourStep:
    """A single step in the hands-on tour with interactive elements."""
    
    def __init__(
        self,
        title: str,
        instruction: str,
        detail_text: str = "",
        target_widget_name: str = None,  # Name of widget to highlight
        target_getter = None,  # Function to get target widget
        action_type: str = "click",  # click, type, select, observe
        action_prompt: str = "Click here",
        auto_advance: bool = False,
        simulate_action = None,  # Function to simulate the action
        tooltip_position: str = "below"  # above, below, left, right
    ):
        self.title = title
        self.instruction = instruction
        self.detail_text = detail_text
        self.target_widget_name = target_widget_name
        self.target_getter = target_getter
        self.action_type = action_type
        self.action_prompt = action_prompt
        self.auto_advance = auto_advance
        self.simulate_action = simulate_action
        self.tooltip_position = tooltip_position
        self.completed = False


class InteractiveTourController(QWidget):
    """
    Controller for the hands-on tour.
    Manages the overlay, tooltips, and step progression.
    """
    
    tour_completed = Signal()
    tour_skipped = Signal()
    step_changed = Signal(int, int)  # current, total
    
    def __init__(self, main_window: QMainWindow, audit_logger=None):
        super().__init__(main_window)
        self._main_window = main_window
        self._audit = audit_logger
        self._current_step = 0
        self._steps: list[HandsOnTourStep] = []
        self._overlay: TourOverlay = None
        self._tooltip_widget: QWidget = None
        self._setup_steps()
        
    def _setup_steps(self):
        """Define the hands-on tour steps with actual UI interactions."""
        self._steps = [
            HandsOnTourStep(
                title="👋 Welcome! Let's Get Started",
                instruction="Welcome to Command Nexus™! This hands-on tour will show you how to create and use AI assistants.",
                detail_text="""<p>By the end of this tour, you'll know how to:</p>
                <ul>
                    <li>🧠 <b>Create</b> your first AI assistant in the Forge</li>
                    <li>⚡ <b>Customize</b> its capabilities and personality</li>
                    <li>💬 <b>Chat</b> with your AI</li>
                    <li>📚 <b>Manage</b> AI memory and knowledge</li>
                </ul>
                <p>The tour will highlight buttons and guide you through each step.</p>
                <p><b>Click 'Next' to start! 👇</b></p>""",
                action_type="observe",
                action_prompt="Click 'Next →' to begin the tour",
                tooltip_position="below",
            ),
            
            HandsOnTourStep(
                title="🧠 Step 1: Open the AI Forge",
                instruction="The AI Forge is where you create and customize AI assistants. Let's open it!",
                detail_text="""<p>The <b>AI Forge</b> is your workshop for building custom AIs.</p>
                <p>You'll choose:</p>
                <ul>
                    <li>A <b>Use Case</b> (Individual, Business, Educational, etc.)</li>
                    <li><b>Capabilities</b> (what your AI can do)</li>
                    <li><b>Personality traits</b> (creativity, caution, etc.)</li>
                </ul>""",
                target_widget_name="nav_forge",
                action_type="click",
                action_prompt="👆 CLICK the 'AI Forge' button",
                tooltip_position="below",
            ),
            
            HandsOnTourStep(
                title="🎯 Step 2: Choose Your Use Case",
                instruction="First, you need to select a Use Case. This determines what capabilities are available.",
                detail_text="""<p>Use cases filter the available capabilities:</p>
                <ul>
                    <li><b>Individual</b> — Personal productivity, creative writing, learning</li>
                    <li><b>Business</b> — Professional tools, email, project management</li>
                    <li><b>Educational</b> — Teaching, tutoring, academic research</li>
                    <li><b>Enterprise</b> — Compliance, security, multi-department</li>
                </ul>
                <p><i>Try clicking on different use cases to see what changes!</i></p>""",
                action_type="observe",
                action_prompt="Click on a Use Case to explore",
            ),
            
            HandsOnTourStep(
                title="⚡ Step 3: Select Capabilities",
                instruction="Now let's add capabilities! These are the skills your AI will have.",
                detail_text="""<p><b>Capabilities</b> are like apps for your AI. Examples include:</p>
                <ul>
                    <li><b>Chatbot</b> — Natural conversation and Q&A</li>
                    <li><b>Coder</b> — Code explanation and drafting</li>
                    <li><b>Research</b> — Information gathering and analysis</li>
                    <li><b>Creative Writing</b> — Drafting stories, scripts, copy</li>
                    <li><b>Customer Support AI</b> — Handle customer inquiries</li>
                </ul>
                <p><i>Click on capabilities to select them. Selected capabilities get checkmarks!</i></p>""",
                action_type="click",
                action_prompt="👆 CLICK on capabilities to select them",
            ),
            
            HandsOnTourStep(
                title="✨ Step 4: Customize Personality",
                instruction="Let's adjust your AI's personality traits to match your needs.",
                detail_text="""<p>These sliders control how your AI behaves:</p>
                <ul>
                    <li><b>Creativity</b> — How original and imaginative (low = conservative, high = innovative)</li>
                    <li><b>Caution</b> — How careful with sensitive topics (low = permissive, high = strict)</li>
                    <li><b>Verbosity</b> — How detailed the responses (low = concise, high = thorough)</li>
                </ul>
                <p><i>Drag the sliders to adjust! Watch the AI description update in real-time.</i></p>""",
                action_type="select",
                action_prompt="👆 ADJUST the personality sliders",
            ),
            
            HandsOnTourStep(
                title="🛡️ Step 5: Set Guardrails",
                instruction="Guardrails keep your AI safe. Let's add some basic safety rules.",
                detail_text="""<p><b>Guardrails</b> are safety boundaries:</p>
                <ul>
                    <li><b>Approval Required</b> — AI asks before taking actions</li>
                    <li><b>Restricted Areas</b> — Topics the AI won't discuss</li>
                    <li><b>Audit Logging</b> — Track what the AI does</li>
                </ul>
                <p>These are especially important for Business and Enterprise use cases.</p>""",
                action_type="click",
                action_prompt="👆 CLICK 'Add Guardrail' to see options",
            ),
            
            HandsOnTourStep(
                title="🚀 Step 6: Create Your AI!",
                instruction="Everything looks good! Now let's actually create the AI.",
                detail_text="""<p>Clicking <b>'Create AI'</b> will:</p>
                <ul>
                    <li>Save your AI configuration</li>
                    <li>Add it to your AI registry</li>
                    <li>Make it available for chatting</li>
                </ul>
                <p><i>Note: Depending on your license tier, you may have a limit on how many AIs you can create.</i></p>""",
                action_type="click",
                action_prompt="👆 CLICK 'Create AI' to finish",
            ),
            
            HandsOnTourStep(
                title="💬 Step 7: Chat With Your AI",
                instruction="Your AI is created! Now let's open the chat and talk to it.",
                detail_text="""<p>The <b>Chat Interface</b> is where you interact with your AI:</p>
                <ul>
                    <li>Type messages in the text box</li>
                    <li>The AI responds based on its capabilities</li>
                    <li>It remembers context from the conversation</li>
                    <li>Use the 'Intelligence' button to give it memory!</li>
                </ul>""",
                target_widget_name="nav_book",
                action_type="click",
                action_prompt="👆 CLICK the 'Intelligence' button to add memory",
            ),
            
            HandsOnTourStep(
                title="📚 Step 8: Give Your AI Knowledge",
                instruction="The Intelligence panel lets you give your AI persistent memory and knowledge.",
                detail_text="""<p>Here you can:</p>
                <ul>
                    <li><b>Add Quick Memory</b> — Notes the AI remembers</li>
                    <li><b>Set Running Memory</b> — How the AI summarizes its knowledge</li>
                    <li><b>Configure Defaults</b> — How the AI starts conversations</li>
                </ul>
                <p><i>This memory is private and never sent to external AI services!</i></p>""",
                action_type="type",
                action_prompt="✏️ TYPE a quick note in the memory box",
            ),
            
            HandsOnTourStep(
                title="🎓 Step 9: Take the Guided Tour",
                instruction="Wait... you're already IN the tour! Let me show you where to find it later.",
                detail_text="""<p>The <b>🎓 Tour</b> button is always available in the navigation bar.</p>
                <p>You can:</p>
                <ul>
                    <li>Retake this tutorial anytime</li>
                    <li>Show new team members how to use Command Nexus</li>
                    <li>Learn about new features as they're added</li>
                </ul>""",
                target_widget_name="nav_tour",
                action_type="click",
                action_prompt="👆 CLICK the '🎓 Tour' button anytime",
            ),
            
            HandsOnTourStep(
                title="✅ You're Ready!",
                instruction="Congratulations! You've completed the hands-on tutorial.",
                detail_text="""<h3>🎉 You now know how to:</h3>
                <ul>
                    <li>✅ Create AI assistants in the Forge</li>
                    <li>✅ Customize capabilities and personality</li>
                    <li>✅ Chat with your AIs</li>
                    <li>✅ Add memory and knowledge</li>
                    <li>✅ Access this tutorial anytime</li>
                </ul>
                <p><b>What's next?</b></p>
                <ul>
                    <li>Explore different use cases and capabilities</li>
                    <li>Create multiple AIs for different tasks</li>
                    <li>Upgrade your license for more features</li>
                    <li>Check the 🤖 Customer Support AI if you need help!</li>
                </ul>
                <p><b>Welcome to Command Nexus™ — Your AI Command Center!</b> 🚀</p>""",
                action_type="observe",
                action_prompt="Click 'Finish' to close the tutorial",
            ),
        ]
    
    def start_tour(self):
        """Start the interactive tour."""
        self._current_step = 0
        self._create_overlay()
        self._show_current_step()
        
        if self._audit:
            self._audit.log(tool="InteractiveTour", action="TOUR_STARTED", target="Hands-on tutorial started", approved=True, status="info")
    
    def _create_overlay(self):
        """Create the highlight overlay on the main window."""
        if self._overlay:
            self._overlay.deleteLater()
        
        self._overlay = TourOverlay(self._main_window)
        self._overlay.resize_to_parent()
        self._overlay.show()
        # Ensure overlay is at the top of the widget stack
        self._overlay.raise_()
    
    def _show_current_step(self):
        """Display the current tour step with highlights and tooltips."""
        if self._current_step >= len(self._steps):
            self.complete_tour()
            return
        
        step = self._steps[self._current_step]
        self.step_changed.emit(self._current_step + 1, len(self._steps))
        
        # Clear previous highlights
        self._overlay.clear_highlight()
        
        # Find and highlight target widget with generous padding around it
        target_widget = self._find_target_widget(step)
        if target_widget:
            self._overlay.set_highlight(target_widget)  # Uses default 25px padding
            
            # Position tooltip near target
            self._show_tooltip_near_target(target_widget, step)
        else:
            # Center tooltip if no target
            self._show_centered_tooltip(step)
    
    def _find_target_widget(self, step: HandsOnTourStep) -> QWidget:
        """Find the target widget for a tour step."""
        if step.target_getter:
            return step.target_getter()
        
        if step.target_widget_name:
            # Search for widget by object name or text
            return self._main_window.findChild(QWidget, step.target_widget_name)
        
        return None
    
    def _show_tooltip_near_target(self, target: QWidget, step: HandsOnTourStep):
        """Show an interactive tooltip near the target widget."""
        if self._tooltip_widget:
            self._tooltip_widget.deleteLater()
        
        # Create tooltip as independent top-level window so it appears above overlay
        self._tooltip_widget = TourTooltip(
            step=step,
            on_next=self.next_step,
            on_skip=self.skip_tour,
            on_back=self.previous_step if self._current_step > 0 else None,
            parent=None  # Top-level window
        )
        
        # Position tooltip
        self._position_tooltip(target, self._tooltip_widget, step.tooltip_position)
        
        # Show and raise to ensure it's on top
        self._tooltip_widget.show()
        self._tooltip_widget.raise_()
    
    def _show_centered_tooltip(self, step: HandsOnTourStep):
        """Show tooltip in center of screen."""
        if self._tooltip_widget:
            self._tooltip_widget.deleteLater()
        
        self._tooltip_widget = TourTooltip(
            step=step,
            on_next=self.next_step,
            on_skip=self.skip_tour,
            on_back=self.previous_step if self._current_step > 0 else None,
            parent=None  # Top-level window
        )
        
        # Center on main window using global coordinates
        main_geo = self._main_window.geometry()
        tooltip_size = self._tooltip_widget.sizeHint()
        x = main_geo.center().x() - tooltip_size.width() // 2
        y = main_geo.center().y() - tooltip_size.height() // 2
        
        # Keep on screen
        screen = QApplication.primaryScreen().geometry()
        x = max(10, min(x, screen.width() - tooltip_size.width() - 10))
        y = max(10, min(y, screen.height() - tooltip_size.height() - 10))
        
        self._tooltip_widget.move(x, y)
        self._tooltip_widget.show()
        self._tooltip_widget.raise_()
    
    def _position_tooltip(self, target: QWidget, tooltip: QWidget, position: str):
        """Position tooltip AWAY from target so both are clearly visible.
        
        Default is bottom-right corner of screen so it never obscures the UI.
        """
        tooltip_size = tooltip.sizeHint()
        screen = QApplication.primaryScreen().geometry()
        
        # Default: place in bottom-right corner with padding, away from main UI
        x = screen.width() - tooltip_size.width() - 30
        y = screen.height() - tooltip_size.height() - 100
        
        # Ensure it stays on screen
        x = max(10, min(x, screen.width() - tooltip_size.width() - 10))
        y = max(10, min(y, screen.height() - tooltip_size.height() - 10))
        
        tooltip.move(x, y)
    
    def next_step(self):
        """Advance to the next tour step."""
        self._current_step += 1
        self._show_current_step()
    
    def previous_step(self):
        """Go back to the previous tour step."""
        if self._current_step > 0:
            self._current_step -= 1
            self._show_current_step()
    
    def skip_tour(self):
        """Skip the tour and clean up."""
        if self._audit:
            self._audit.log(tool="InteractiveTour", action="TOUR_SKIPPED", target=f"Skipped at step {self._current_step}", approved=True, status="info")
        
        self._cleanup()
        self.tour_skipped.emit()
    
    def complete_tour(self):
        """Complete the tour successfully."""
        if self._audit:
            self._audit.log(tool="InteractiveTour", action="TOUR_COMPLETED", target="Full tutorial completed", approved=True, status="info")
        
        self._cleanup()
        self.tour_completed.emit()
    
    def _cleanup(self):
        """Clean up overlay and tooltip."""
        if self._overlay:
            self._overlay.deleteLater()
            self._overlay = None
        
        if self._tooltip_widget:
            self._tooltip_widget.deleteLater()
            self._tooltip_widget = None


class TourTooltip(QFrame):
    """
    Interactive tooltip dialog for tour steps.
    Shows instructions, details, and action buttons.
    """
    
    def __init__(
        self,
        step: HandsOnTourStep,
        on_next,
        on_skip,
        on_back=None,
        parent=None
    ):
        super().__init__(parent)
        self._step = step
        # Make it a top-level window that stays on top but accepts focus for interaction
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        # Accept mouse events
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
        self._setup_ui(on_next, on_skip, on_back)
        self._apply_styling()
    
    def _setup_ui(self, on_next, on_skip, on_back):
        """Build the tooltip UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Step indicator
        step_label = QLabel(f"Step {self._step.title.split(':')[0] if ':' in self._step.title else '▶'}")
        step_label.setFont(QFont("Segoe UI", 10))
        step_label.setStyleSheet("color: #8b949e;")
        layout.addWidget(step_label)
        
        # Title
        title = QLabel(self._step.title)
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setWordWrap(True)
        title.setStyleSheet("color: #58a6ff;")
        layout.addWidget(title)
        
        # Main instruction
        instruction = QLabel(self._step.instruction)
        instruction.setFont(QFont("Segoe UI", 12))
        instruction.setWordWrap(True)
        instruction.setStyleSheet("color: #ffffff; padding: 10px 0;")
        layout.addWidget(instruction)
        
        # Action prompt (highlighted)
        if self._step.action_prompt:
            prompt_frame = QFrame()
            prompt_frame.setStyleSheet("background-color: #23863633; border: 2px solid #238636; border-radius: 8px; padding: 5px;")
            prompt_layout = QHBoxLayout(prompt_frame)
            prompt_layout.setContentsMargins(15, 10, 15, 10)
            
            prompt_label = QLabel(f"👉 {self._step.action_prompt}")
            prompt_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            prompt_label.setStyleSheet("color: #238636;")
            prompt_layout.addWidget(prompt_label)
            
            layout.addWidget(prompt_frame)
        
        # Detail text
        if self._step.detail_text:
            detail = QLabel(self._step.detail_text)
            detail.setFont(QFont("Segoe UI", 10))
            detail.setWordWrap(True)
            detail.setStyleSheet("color: #c9d1d9;  padding: 15px; border-radius: 8px;")
            layout.addWidget(detail)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        if on_back:
            btn_back = QPushButton("← Back")
            btn_back.clicked.connect(on_back)
            btn_back.setStyleSheet(" color: #c9d1d9;")
            btn_layout.addWidget(btn_back)
        
        btn_layout.addStretch()
        
        btn_skip = QPushButton("Skip Tutorial")
        btn_skip.clicked.connect(on_skip)
        btn_skip.setStyleSheet("background-color: transparent; color: #8b949e; border: none;")
        btn_layout.addWidget(btn_skip)
        
        btn_next = QPushButton("Next →" if "Finish" not in self._step.action_prompt else "Finish ✓")
        btn_next.clicked.connect(on_next)
        btn_next.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px 20px;")
        btn_next.setDefault(True)
        btn_layout.addWidget(btn_next)
        
        layout.addLayout(btn_layout)
        
        # Progress bar
        self.setMinimumWidth(400)
        self.setMaximumWidth(500)
    
    def _apply_styling(self):
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QFrame {
                
                border: 2px solid #30363d;
                border-radius: 12px;
            }
            QPushButton {
                background-color: #30363d;
                border: 1px solid #484f58;
                border-radius: 6px;
                padding: 8px 16px;
                color: #c9d1d9;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3d444d;
                border-color: #58a6ff;
            }
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)


def start_interactive_tour(main_window: QMainWindow, audit_logger=None) -> InteractiveTourController:
    """Start the hands-on interactive tour."""
    controller = InteractiveTourController(main_window, audit_logger)
    controller.start_tour()
    return controller


def get_test_license_keys() -> dict:
    """Return test license keys for all tiers (test builds only)."""
    return {
        "FREE": "TEST-FREE-XXXX-XXXX-XXXX",
        "PRO": "TEST-PRO-XXXX-XXXX-XXXX",
        "ENTERPRISE": "TEST-ENT-XXXX-XXXX-XXXX",
        "FOUNDER": "TEST-FDR-XXXX-XXXX-XXXX",
    }
