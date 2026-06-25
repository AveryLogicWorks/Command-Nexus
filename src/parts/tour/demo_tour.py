"""
Command Nexus™ Demo Tour
===========================
Interactive hands-on tutorial that:
1. Positions instructions AWAY from highlighted UI
2. Waits for user to click highlighted elements
3. Automatically opens windows and guides inside them
4. Runs in sandbox mode - nothing persists
"""
import math
from typing import Callable, Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QEvent, QPoint, QRect
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect, QTextEdit,
    QListWidget,
)
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPolygon, QScreen


class DemoTourOverlay(QWidget):
    """
    Overlay that draws animated highlight AROUND target widget.
    Tooltip is positioned separately (bottom-right) so both are visible.
    """
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.setStyleSheet("background: transparent;")
        
        self._highlight_rect: QRect = None
        self._pulse_animation = 0
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(50)
    
    def highlight_widget(self, widget: QWidget, padding: int = 30):
        """Highlight a widget with animated border AROUND it."""
        if widget and widget.isVisible():
            geo = widget.geometry()
            top_left = widget.mapToGlobal(geo.topLeft())
            bottom_right = widget.mapToGlobal(geo.bottomRight())
            
            if self.parent():
                top_left = self.parent().mapFromGlobal(top_left)
                bottom_right = self.parent().mapFromGlobal(bottom_right)
            
            width = bottom_right.x() - top_left.x()
            height = bottom_right.y() - top_left.y()
            
            # Create highlight rect AROUND the widget (not on it)
            self._highlight_rect = QRect(
                top_left.x() - padding,
                top_left.y() - padding,
                width + padding * 2,
                height + padding * 2
            )
            self.update()
    
    def clear_highlight(self):
        """Clear the highlight."""
        self._highlight_rect = None
        self.update()
    
    def _animate(self):
        """Animate the pulsing effect."""
        self._pulse_animation = (self._pulse_animation + 1) % 20
        self.update()
    
    def paintEvent(self, event):
        """Paint animated border around highlight area."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self._highlight_rect:
            pulse = abs(self._pulse_animation - 10) + 5
            
            # Multiple animated glow layers
            layers = [
                (pulse * 2, QColor(88, 166, 255, 60), 6),
                (pulse, QColor(88, 166, 255, 120), 4),
                (0, QColor(88, 166, 255), 3),
                (-3, QColor(255, 255, 255, 200), 2),
            ]
            
            for offset, color, width in layers:
                rect = self._highlight_rect.adjusted(-offset, -offset, offset, offset)
                pen = QPen(color, width)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(rect, 12, 12)
            
            # Corner accents
            self._draw_corners(painter, self._highlight_rect, QColor(255, 193, 7))
    
    def _draw_corners(self, painter: QPainter, rect: QRect, color: QColor):
        """Draw yellow corner accents."""
        size = 15
        pen = QPen(color, 3)
        painter.setPen(pen)
        
        corners = [
            # Top-left
            (rect.left(), rect.top() + size, rect.left(), rect.top(),
             rect.left(), rect.top(), rect.left() + size, rect.top()),
            # Top-right
            (rect.right() - size, rect.top(), rect.right(), rect.top(),
             rect.right(), rect.top(), rect.right(), rect.top() + size),
            # Bottom-left
            (rect.left(), rect.bottom() - size, rect.left(), rect.bottom(),
             rect.left(), rect.bottom(), rect.left() + size, rect.bottom()),
            # Bottom-right
            (rect.right() - size, rect.bottom(), rect.right(), rect.bottom(),
             rect.right(), rect.bottom(), rect.right(), rect.bottom() - size),
        ]
        
        for x1, y1, x2, y2, x3, y3, x4, y4 in corners:
            painter.drawLine(x1, y1, x2, y2)
            painter.drawLine(x3, y3, x4, y4)
    
    def resize_to_parent(self):
        """Resize to cover parent window."""
        if self.parent():
            self.setGeometry(self.parent().rect())
            self.raise_()


class DemoTourTooltip(QFrame):
    """
    Tour instruction panel positioned in bottom-right corner.
    NEVER covers the highlighted widget.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self._setup_ui()
        self._apply_styling()
    
    def _setup_ui(self):
        """Build the instruction panel UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Step indicator
        self._step_label = QLabel("Step 1 of 10")
        self._step_label.setFont(QFont("Segoe UI", 10))
        self._step_label.setStyleSheet("color: #8b949e;")
        layout.addWidget(self._step_label)
        
        # Title
        self._title_label = QLabel("Tour Title")
        self._title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self._title_label.setWordWrap(True)
        self._title_label.setStyleSheet("color: #58a6ff;")
        layout.addWidget(self._title_label)
        
        # Main instruction
        self._instruction_label = QLabel("Instruction text...")
        self._instruction_label.setFont(QFont("Segoe UI", 12))
        self._instruction_label.setWordWrap(True)
        self._instruction_label.setStyleSheet("color: #ffffff; padding: 5px 0;")
        layout.addWidget(self._instruction_label)
        
        # Action prompt (green box)
        self._action_frame = QFrame()
        self._action_frame.setStyleSheet(
            "background-color: #23863633; border: 2px solid #238636; border-radius: 8px;"
        )
        action_layout = QHBoxLayout(self._action_frame)
        action_layout.setContentsMargins(15, 12, 15, 12)
        
        self._action_label = QLabel("👉 CLICK the button")
        self._action_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self._action_label.setStyleSheet("color: #3fb950;")
        action_layout.addWidget(self._action_label)
        layout.addWidget(self._action_frame)
        
        # Detail text with mouse wheel scrolling
        from PyQt6.QtWidgets import QScrollArea, QWidget
        
        self._detail_scroll = QScrollArea()
        self._detail_scroll.setWidgetResizable(True)
        self._detail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._detail_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._detail_scroll.setStyleSheet("""
            QScrollArea {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 8px;
            }
            QScrollBar:vertical {
                background-color: #21262d;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #30363d;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #484f58;
            }
        """)
        
        self._detail_text = QTextEdit()
        self._detail_text.setReadOnly(True)
        self._detail_text.setFont(QFont("Segoe UI", 11))
        self._detail_text.setStyleSheet("""
            QTextEdit {
                background-color: #161b22;
                border: none;
                color: #c9d1d9;
                padding: 10px;
            }
        """)
        self._detail_text.setMinimumHeight(100)
        self._detail_text.setMaximumHeight(180)
        
        # Enable mouse wheel scrolling
        self._detail_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._detail_text.viewport().setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        
        layout.addWidget(self._detail_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self._back_btn = QPushButton("← Back")
        self._back_btn.setStyleSheet(
            "background-color: #30363d; color: #c9d1d9; padding: 8px 16px; border-radius: 6px;"
        )
        button_layout.addWidget(self._back_btn)
        
        button_layout.addStretch()
        
        self._skip_btn = QPushButton("Skip Tour")
        self._skip_btn.setStyleSheet(
            "background-color: #30363d; color: #8b949e; padding: 8px 16px; border-radius: 6px;"
        )
        button_layout.addWidget(self._skip_btn)
        
        self._next_btn = QPushButton("Next →")
        self._next_btn.setStyleSheet(
            "background-color: #238636; color: white; font-weight: bold; padding: 8px 20px; border-radius: 6px;"
        )
        self._next_btn.setDefault(True)
        button_layout.addWidget(self._next_btn)
        
        layout.addLayout(button_layout)
        
        # Demo mode notice
        demo_notice = QLabel("🎮 DEMO MODE - Nothing you do will be saved")
        demo_notice.setFont(QFont("Segoe UI", 10))
        demo_notice.setStyleSheet("color: #ffee58; padding-top: 10px;")
        demo_notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(demo_notice)
    
    def _apply_styling(self):
        """Apply dark theme styling."""
        self.setStyleSheet("""
            DemoTourTooltip {
                background-color: #0d1117;
                border: 2px solid #30363d;
                border-radius: 12px;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 255))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)
    
    def update_content(self, step_num: int, total_steps: int, title: str,
                      instruction: str, action_prompt: str, detail_html: str,
                      wait_for_click: bool = False):
        """Update tooltip content."""
        self._step_label.setText(f"Step {step_num} of {total_steps}")
        self._title_label.setText(title)
        self._instruction_label.setText(instruction)
        self._action_label.setText(action_prompt)
        self._detail_text.setHtml(detail_html)
        
        if wait_for_click:
            self._next_btn.setText("Waiting for click...")
            self._next_btn.setEnabled(False)
            self._next_btn.setStyleSheet(
                "background-color: #484f58; color: #8b949e; padding: 8px 20px; border-radius: 6px;"
            )
        else:
            self._next_btn.setText("Next →")
            self._next_btn.setEnabled(True)
            self._next_btn.setStyleSheet(
                "background-color: #238636; color: white; font-weight: bold; padding: 8px 20px; border-radius: 6px;"
            )
    
    def set_buttons(self, on_back=None, on_next=None, on_skip=None):
        """Connect button signals."""
        if on_back:
            self._back_btn.clicked.connect(on_back)
            self._back_btn.setVisible(True)
        else:
            self._back_btn.setVisible(False)
        
        if on_next:
            self._next_btn.clicked.connect(on_next)
        
        if on_skip:
            self._skip_btn.clicked.connect(on_skip)
    
    def position_bottom_right(self):
        """Position in bottom-right corner of screen."""
        self.adjustSize()
        size = self.size()
        screen = QApplication.primaryScreen().geometry()
        
        x = screen.width() - size.width() - 20
        y = screen.height() - size.height() - 80
        
        self.move(x, y)


class DemoTourStep:
    """A single step in the demo tour."""
    
    def __init__(
        self,
        title: str,
        instruction: str,
        detail_html: str = "",
        target_widget_name: str = None,
        target_getter: Callable = None,
        action_prompt: str = "",
        wait_for_click: bool = True,
        on_target_clicked: Callable = None,
        auto_advance_delay: int = 0
    ):
        self.title = title
        self.instruction = instruction
        self.detail_html = detail_html
        self.target_widget_name = target_widget_name
        self.target_getter = target_getter
        self.action_prompt = action_prompt
        self.wait_for_click = wait_for_click
        self.on_target_clicked = on_target_clicked
        self.auto_advance_delay = auto_advance_delay
        self.completed = False


class DemoTourController(QWidget):
    """
    Demo tour that:
    1. Shows instructions in bottom-right (never covers UI)
    2. Highlights target widget with animated border
    3. Waits for user to click target (if wait_for_click=True)
    4. Can trigger window opens and guide inside them
    5. Runs in demo mode - nothing persists
    """
    
    tour_completed = pyqtSignal()
    tour_skipped = pyqtSignal()
    step_changed = pyqtSignal(int, int)
    
    def __init__(self, main_window: QMainWindow, audit_logger=None, demo_mode: bool = True):
        super().__init__(main_window)
        self._main_window = main_window
        self._audit = audit_logger
        self._demo_mode = demo_mode
        self._current_step = 0
        self._steps: list[DemoTourStep] = []
        self._overlay: DemoTourOverlay = None
        self._tooltip: DemoTourTooltip = None
        self._event_filter_installed = False
        self._pending_click_target = None
        self._setup_steps()
    
    def _find_forge_window(self) -> Optional[QMainWindow]:
        """Find the open AI Forge window, if it exists."""
        for w in QApplication.topLevelWidgets():
            if isinstance(w, QMainWindow) and "Forge" in w.windowTitle():
                return w
        return None

    def _find_forge_ai_list(self) -> Optional[QWidget]:
        forge = self._find_forge_window()
        if forge is None:
            return None
        return forge.findChild(QListWidget, "forge_ai_list")

    def _find_forge_deploy_button(self) -> Optional[QWidget]:
        forge = self._find_forge_window()
        if forge is None:
            return None
        return forge.findChild(QPushButton, "forge_deploy_button")

    def _setup_steps(self):
        """Define the interactive demo tour steps using real, clickable widgets."""
        self._steps = [
            DemoTourStep(
                title="👋 Welcome to Command Nexus",
                instruction="This tour will show you how to build and deploy an AI assistant.",
                detail_html="""<p>By the end of this tour, you'll know how to:</p>
                <ul>
                    <li>🧠 <b>Open</b> the AI Forge</li>
                    <li>⚡ <b>Select</b> an AI and deploy it</li>
                    <li>🎯 <b>Give</b> your AI a mission</li>
                </ul>
                <p><b>Clickable targets are highlighted.</b> The tour waits for you to click them.</p>
                <p><i>If a window isn't available, the tour will skip that step.</i></p>""",
                action_prompt="Click 'Next' to start",
                wait_for_click=False,
            ),

            DemoTourStep(
                title="🧠 Step 1: Open the AI Forge",
                instruction="The AI Forge is where you build AI assistants. Click the AI Forge button to open it.",
                detail_html="""<p>The <b>AI Forge</b> is your workshop. Here you'll create and customize AI assistants.</p>
                <p>Click the <b>AI Forge</b> button in the navigation bar.</p>""",
                target_widget_name="nav_forge",
                action_prompt="👉 CLICK 'AI Forge'",
                wait_for_click=True,
            ),

            DemoTourStep(
                title="📋 Step 2: Select an AI",
                instruction="In the AI Forge, select an AI from the library list.",
                detail_html="""<p>The AI library shows the AIs you have created. Click one to select it.</p>
                <p><i>If the Forge window did not open, click Next to skip.</i></p>""",
                target_getter=self._find_forge_ai_list,
                action_prompt="👉 CLICK an AI in the list",
                wait_for_click=True,
            ),

            DemoTourStep(
                title="🚀 Step 3: Deploy to Command Center",
                instruction="Click 'Deploy to Command Center' to activate the selected AI.",
                detail_html="""<p>Deploying makes the AI appear in the Active AI selector in the main window.</p>
                <p><i>If the Forge window is not visible, click Next to skip.</i></p>""",
                target_getter=self._find_forge_deploy_button,
                action_prompt="👉 CLICK 'Deploy to Command Center'",
                wait_for_click=True,
            ),

            DemoTourStep(
                title="🎯 Step 4: Give Your AI a Mission",
                instruction="Type a mission in the Mission Control box, then click START.",
                detail_html="""<p>The Active AI is shown in the selector. Type a task like:</p>
                <ul>
                    <li>"Write file notes.txt content: hello"</li>
                    <li>"Plan my day"</li>
                    <li>"Summarize this document: [paste text]"</li>
                </ul>
                <p>Click the START button when ready.</p>""",
                target_widget_name="mission_start_button",
                action_prompt="👉 TYPE a mission, then click START",
                wait_for_click=True,
            ),

            DemoTourStep(
                title="✅ Tour Complete!",
                instruction="You've completed the interactive tour.",
                detail_html="""<h3>🎉 You now know how to:</h3>
                <ul>
                    <li>✅ Open the AI Forge</li>
                    <li>✅ Select and deploy an AI</li>
                    <li>✅ Give the AI a mission</li>
                </ul>
                <p><b>Some capabilities are real, some are partial, and some are paused.</b>
                Command Nexus will always tell you honestly instead of faking work.</p>
                <p>Click 'Finish' to close the tutorial.</p>""",
                action_prompt="Click 'Finish' to close",
                wait_for_click=False,
            ),
        ]

    def start_tour(self):
        """Start the demo tour."""
        self._current_step = 0
        self._create_overlay()
        self._create_tooltip()
        self._show_current_step()
        
        if self._audit:
            self._audit.log(tool="DemoTour", action="DEMO_STARTED", 
                          target="Interactive demo tour started", approved=True, status="info")
    
    def _create_overlay(self):
        """Create the highlight overlay."""
        if self._overlay:
            self._overlay.deleteLater()
        self._overlay = DemoTourOverlay(self._main_window)
        self._overlay.resize_to_parent()
        self._overlay.show()
        self._overlay.raise_()
    
    def _create_tooltip(self):
        """Create the instruction tooltip."""
        if self._tooltip:
            self._tooltip.deleteLater()
        self._tooltip = DemoTourTooltip(None)
        self._tooltip.set_buttons(
            on_back=self._on_back if self._current_step > 0 else None,
            on_next=self._on_next,
            on_skip=self._on_skip
        )
        self._tooltip.show()
        self._tooltip.raise_()
    
    def _show_current_step(self):
        """Display current step with highlight and instructions."""
        if self._current_step >= len(self._steps):
            self._complete_tour()
            return
        
        step = self._steps[self._current_step]
        self.step_changed.emit(self._current_step + 1, len(self._steps))
        
        # Clear previous
        self._overlay.clear_highlight()
        self._remove_event_filter()
        
        # Find target widget
        target = self._find_target(step)
        target_missing = step.wait_for_click and target is None

        if target:
            # Highlight it
            self._overlay.highlight_widget(target)

            # If waiting for click, install event filter
            if step.wait_for_click:
                self._pending_click_target = target
                self._install_event_filter()

        # Update tooltip; if target is missing, explain that the step is skipped.
        action_prompt = step.action_prompt
        detail_html = step.detail_html
        if target_missing:
            action_prompt = "⚠️ Target not available — click Next to skip"
            detail_html += "<p><i>This step is skipped because the target window or widget is not available.</i></p>"

        self._tooltip.update_content(
            step_num=self._current_step + 1,
            total_steps=len(self._steps),
            title=step.title,
            instruction=step.instruction,
            action_prompt=action_prompt,
            detail_html=detail_html,
            wait_for_click=step.wait_for_click and target is not None
        )
        
        # Reconnect buttons for current step
        self._tooltip._next_btn.clicked.disconnect() if self._tooltip._next_btn.receivers(self._tooltip._next_btn.clicked) > 0 else None
        self._tooltip._next_btn.clicked.connect(self._on_next)
        
        self._tooltip._back_btn.clicked.disconnect() if self._tooltip._back_btn.receivers(self._tooltip._back_btn.clicked) > 0 else None
        if self._current_step > 0:
            self._tooltip._back_btn.setVisible(True)
            self._tooltip._back_btn.clicked.connect(self._on_back)
        else:
            self._tooltip._back_btn.setVisible(False)
        
        # Position tooltip in bottom-right
        self._tooltip.position_bottom_right()
    
    def _find_target(self, step: DemoTourStep) -> Optional[QWidget]:
        """Find the target widget for a step."""
        if step.target_getter:
            return step.target_getter()
        if step.target_widget_name:
            return self._main_window.findChild(QWidget, step.target_widget_name)
        return None
    
    def _install_event_filter(self):
        """Install event filter to watch for clicks on target."""
        if not self._event_filter_installed and self._pending_click_target:
            self._pending_click_target.installEventFilter(self)
            self._event_filter_installed = True
    
    def _remove_event_filter(self):
        """Remove event filter."""
        if self._event_filter_installed and self._pending_click_target:
            self._pending_click_target.removeEventFilter(self)
            self._event_filter_installed = False
            self._pending_click_target = None
    
    def eventFilter(self, obj, event):
        """Watch for click events on target widget."""
        if obj == self._pending_click_target and event.type() == QEvent.Type.MouseButtonRelease:
            # User clicked the target!
            if self._current_step < len(self._steps):
                step = self._steps[self._current_step]
                if step.on_target_clicked:
                    step.on_target_clicked()
                
                # Auto-advance after click
                QTimer.singleShot(500, self._on_next)
                
                if self._audit:
                    self._audit.log(tool="DemoTour", action="STEP_ACTION_COMPLETED",
                                  target=f"Step {self._current_step + 1}: {step.title}",
                                  approved=True, status="info")
            
            return True
        
        return super().eventFilter(obj, event)
    
    def _on_next(self):
        """Go to next step."""
        self._current_step += 1
        self._show_current_step()
    
    def _on_back(self):
        """Go to previous step."""
        if self._current_step > 0:
            self._current_step -= 1
            self._show_current_step()
    
    def _on_skip(self):
        """Skip the tour."""
        if self._audit:
            self._audit.log(tool="DemoTour", action="DEMO_SKIPPED",
                          target=f"Skipped at step {self._current_step}", approved=True, status="info")
        self._cleanup()
        self.tour_skipped.emit()
    
    def _complete_tour(self):
        """Complete the tour."""
        if self._audit:
            self._audit.log(tool="DemoTour", action="DEMO_COMPLETED",
                          target="Full demo completed", approved=True, status="info")
        self._cleanup()
        self.tour_completed.emit()
    
    def _cleanup(self):
        """Clean up resources."""
        self._remove_event_filter()
        if self._overlay:
            self._overlay.deleteLater()
            self._overlay = None
        if self._tooltip:
            self._tooltip.deleteLater()
            self._tooltip = None


def start_demo_tour(main_window: QMainWindow, audit_logger=None) -> DemoTourController:
    """Start the interactive demo tour."""
    controller = DemoTourController(main_window, audit_logger, demo_mode=True)
    controller.start_tour()
    return controller
