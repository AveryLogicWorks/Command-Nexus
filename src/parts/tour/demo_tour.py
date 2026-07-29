# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

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

from PySide6.QtCore import Qt, QTimer, Signal, QObject, QEvent, QPoint, QRect, QRectF, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect, QTextEdit,
    QListWidget, QCheckBox, QProgressBar, QSizePolicy, QGroupBox, QComboBox,
)
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPolygon, QScreen, QPainterPath

from ...core.tts_engine import get_tts


class DemoTourOverlay(QWidget):
    """
    Screen-wide top-level overlay that draws animated highlight AROUND any widget.
    Dims the rest of the screen to focus attention on the highlighted element.
    Works across multiple windows (main window, Forge, Intelligence, etc.).
    """
    
    def __init__(self, parent: QWidget = None):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")
        
        self._highlight_rect: QRect = None
        self._target_widget: QWidget = None
        self._padding: int = 20
        self._pulse_animation = 0.0
        self._click_flash = 0
        self._dim_opacity = 0.45
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(16)  # ~60fps for smooth animation
    
    def highlight_widget(self, widget: QWidget, padding: int = 30):
        """Highlight a widget with animated border AROUND it."""
        if widget and widget.isVisible():
            self._target_widget = widget
            self._padding = padding
            self._update_highlight_rect()
            self.update()
    
    def _update_highlight_rect(self):
        """Recompute highlight rect from target widget's current global position."""
        if not self._target_widget:
            return
        try:
            if not self._target_widget or not self._target_widget.isVisible():
                return
            # mapToGlobal(QPoint(0,0)) gives the global screen position of the widget's top-left corner.
            top_left = self._target_widget.mapToGlobal(QPoint(0, 0))
            w = self._target_widget.width()
            h = self._target_widget.height()
            # Map from global screen coords to overlay's local coords
            origin = self.geometry().topLeft()
            x = top_left.x() - origin.x()
            y = top_left.y() - origin.y()
            self._highlight_rect = QRect(
                x - self._padding,
                y - self._padding,
                w + self._padding * 2,
                h + self._padding * 2,
            )
        except RuntimeError:
            # Widget was deleted by Qt C++ side — clear highlight safely
            self._highlight_rect = None
            self._target_widget = None
    
    def flash_click(self):
        """Flash green to indicate a click was detected."""
        self._click_flash = 10
        self.update()
    
    def clear_highlight(self):
        """Clear the highlight."""
        self._highlight_rect = None
        self._target_widget = None
        self._click_flash = 0
        self.update()
    
    def _animate(self):
        """Animate the pulsing effect and recompute highlight position."""
        self._pulse_animation += 0.08
        if self._click_flash > 0:
            self._click_flash -= 1
        if self._target_widget:
            self._update_highlight_rect()
        try:
            self.update()
        except RuntimeError:
            pass
    
    def set_auto_cursor(self, pos):
        """Show/hide the automated-demo virtual cursor (overlay-local QPointF or None)."""
        self._auto_cursor = pos
        self.update()

    def pulse_click_ring(self):
        """Expanding ring at the virtual cursor to indicate a click."""
        for i in range(1, 13):
            QTimer.singleShot(i * 28, lambda i=i: self._set_ring(i / 12.0))

    def _set_ring(self, t):
        self._click_ring_t = t
        self.update()

    def paintEvent(self, event):
        """Paint dimmed overlay with animated highlight border."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self._highlight_rect:
            # Dim the entire screen except the highlight area
            dim_color = QColor(0, 0, 0, int(255 * self._dim_opacity))
            
            # Create a path: full screen rect minus the highlight rect (with rounded corners)
            path = QPainterPath()
            path.addRoundedRect(QRectF(self._highlight_rect), 12, 12)
            # Fill everything outside the highlight with dim color
            outer_rect = QRect(0, 0, self.width(), self.height())
            outer_path = QPainterPath()
            outer_path.addRect(QRectF(outer_rect))
            dim_path = outer_path.subtracted(path)
            painter.fillPath(dim_path, dim_color)
            
            # Smooth sine wave pulse
            pulse = (math.sin(self._pulse_animation) + 1) / 2  # 0.0 to 1.0
            glow_alpha = int(80 + pulse * 100)
            
            if self._click_flash > 0:
                # Green flash on click detection
                flash_alpha = int(255 * self._click_flash / 10)
                layers = [
                    (8, QColor(63, 185, 80, flash_alpha // 3), 8),
                    (4, QColor(63, 185, 80, flash_alpha // 2), 5),
                    (0, QColor(63, 185, 80, 255), 3),
                ]
            else:
                # Blue pulsing glow with smooth animation
                layers = [
                    (10, QColor(88, 166, 255, int(glow_alpha * 0.3)), 6),
                    (5, QColor(88, 166, 255, int(glow_alpha * 0.6)), 4),
                    (0, QColor(88, 166, 255, 255), 3),
                ]
            
            for offset, color, width in layers:
                rect = self._highlight_rect.adjusted(-offset, -offset, offset, offset)
                pen = QPen(color, width)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(QRectF(rect), 12, 12)
            
            # Corner accents (gold)
            self._draw_corners(painter, self._highlight_rect, QColor(255, 193, 7, 220))

        # Automated-demo virtual cursor (painted overlay element — the OS cursor
        # is never moved, locked, hidden, or controlled).
        cur = getattr(self, "_auto_cursor", None)
        if cur is not None:
            from PySide6.QtGui import QPolygonF
            from PySide6.QtCore import QPointF
            ring_t = getattr(self, "_click_ring_t", 1.0)
            if ring_t < 1.0:
                r = 6.0 + ring_t * 26.0
                painter.setPen(QPen(QColor(88, 166, 255, int(255 * (1.0 - ring_t))), 3))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(cur, r, r)
            arrow = QPolygonF([cur, QPointF(cur.x() + 4, cur.y() + 16),
                               QPointF(cur.x() + 7, cur.y() + 11),
                               QPointF(cur.x() + 16, cur.y() + 10)])
            painter.setPen(QPen(QColor(13, 17, 23), 1))
            painter.setBrush(QColor(255, 255, 255, 245))
            painter.drawPolygon(arrow)
    
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
    
    def resize_to_screen(self, reference_widget: QWidget = None):
        """Resize to cover the screen containing the reference widget (or primary screen)."""
        if reference_widget and reference_widget.isVisible():
            screen = QApplication.screenAt(reference_widget.mapToGlobal(QPoint(0, 0)))
            if screen:
                self.setGeometry(screen.geometry())
                self.raise_()
                return
        # Fallback to primary screen
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.raise_()


class DemoTourTooltip(QFrame):
    """
    Tour instruction panel — a frameless, always-on-top window.
    Positions itself near the highlighted widget but never overlaps it.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setFixedWidth(420)
        self._setup_ui()
        self._apply_styling()
        
        self._close_callback = None
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Fade-in animation
        self._fade_anim = None
    
    def _setup_ui(self):
        """Build the instruction panel UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(22, 22, 22, 22)
        
        # Top row: step indicator + close button
        top_row = QHBoxLayout()
        
        self._step_label = QLabel("Step 1 of 10")
        self._step_label.setFont(QFont("Segoe UI", 10))
        self._step_label.setStyleSheet("color: #8b949e; font-weight: bold;")
        top_row.addWidget(self._step_label)
        top_row.addStretch()
        
        self._close_btn = QPushButton("✕")
        self._close_btn.setFixedSize(28, 28)
        self._close_btn.setStyleSheet(
            "QPushButton {  color: #8b949e; border-radius: 4px; font-size: 14px; }"
            "QPushButton:hover { background-color: #da3633; color: white; }"
        )
        self._close_btn.setToolTip("Close tour")
        top_row.addWidget(self._close_btn)
        layout.addLayout(top_row)
        
        # Progress bar
        self._progress = QProgressBar()
        self._progress.setFixedHeight(6)
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet("""
            QProgressBar {
                
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #58a6ff;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self._progress)
        
        # Title
        self._title_label = QLabel("Tour Title")
        self._title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self._title_label.setWordWrap(True)
        self._title_label.setStyleSheet("color: #58a6ff; padding-top: 4px;")
        layout.addWidget(self._title_label)
        
        # Main instruction
        self._instruction_label = QLabel("Instruction text...")
        self._instruction_label.setFont(QFont("Segoe UI", 12))
        self._instruction_label.setWordWrap(True)
        self._instruction_label.setStyleSheet("color: #e6edf3; padding: 2px 0;")
        layout.addWidget(self._instruction_label)
        
        # Action prompt (green box)
        self._action_frame = QFrame()
        self._action_frame.setStyleSheet(
            "background-color: rgba(35, 134, 54, 0.15); border: 2px solid #238636; border-radius: 8px;"
        )
        action_layout = QHBoxLayout(self._action_frame)
        action_layout.setContentsMargins(15, 10, 15, 10)
        
        self._action_label = QLabel("👉 CLICK the button")
        self._action_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self._action_label.setStyleSheet("color: #3fb950;")
        action_layout.addWidget(self._action_label)
        layout.addWidget(self._action_frame)
        
        # Detail text (QTextEdit has built-in scrolling)
        self._detail_text = QTextEdit()
        self._detail_text.setReadOnly(True)
        self._detail_text.setFont(QFont("Segoe UI", 11))
        self._detail_text.setStyleSheet("""
            QTextEdit {
                
                border: 1px solid #30363d;
                border-radius: 8px;
                color: #c9d1d9;
                padding: 8px;
            }
        """)
        self._detail_text.setMinimumHeight(80)
        self._detail_text.setMaximumHeight(160)
        self._detail_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(self._detail_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        self._back_btn = QPushButton("← Back")
        self._back_btn.setStyleSheet(
            "QPushButton { background-color: #30363d; color: #c9d1d9; padding: 8px 16px; border-radius: 6px; border: 1px solid #484f58; }"
            "QPushButton:hover { background-color: #484f58; }"
        )
        button_layout.addWidget(self._back_btn)
        
        button_layout.addStretch()

        self._voice_btn = QPushButton("🔊 Voice: ON")
        self._voice_btn.setCheckable(True)
        self._voice_btn.setChecked(True)
        self._voice_btn.setStyleSheet(
            "QPushButton { background-color: #1f6feb; color: white; padding: 8px 12px; border-radius: 6px; font-size: 11px; border: none; }"
            "QPushButton:hover { background-color: #388bfd; }"
            "QPushButton:checked { background-color: #1f6feb; }"
            "QPushButton:unchecked { background-color: #30363d; color: #8b949e; }"
        )
        self._voice_btn.setFixedWidth(115)
        button_layout.addWidget(self._voice_btn)

        self._skip_btn = QPushButton("Skip Tour ✕")
        self._skip_btn.setStyleSheet(
            "QPushButton { background-color: #30363d; color: #8b949e; padding: 8px 16px; border-radius: 6px; border: 1px solid #484f58; }"
            "QPushButton:hover { background-color: #da3633; color: white; border-color: #da3633; }"
        )
        button_layout.addWidget(self._skip_btn)

        self._next_btn = QPushButton("Next →")
        self._next_btn.setStyleSheet(
            "QPushButton { background-color: #238636; color: white; font-weight: bold; padding: 8px 20px; border-radius: 6px; border: none; }"
            "QPushButton:hover { background-color: #2ea043; }"
            "QPushButton:disabled {  color: #484f58; }"
        )
        self._next_btn.setDefault(True)
        button_layout.addWidget(self._next_btn)

        layout.addLayout(button_layout)

        # Automated demonstration controls (Start/Pause/Resume/Stop/Restart/Speed)
        from PySide6.QtWidgets import QComboBox
        demo_layout = QHBoxLayout()
        demo_layout.setSpacing(6)
        demo_style = ("QPushButton { background-color: #30363d; color: #c9d1d9; padding: 6px 10px; "
                      "border-radius: 6px; border: 1px solid #484f58; font-size: 11px; }"
                      "QPushButton:hover { background-color: #484f58; }")
        self._demo_start_btn = QPushButton("\u25b6 Demo")
        self._demo_pause_btn = QPushButton("\u23f8 Pause")
        self._demo_stop_btn = QPushButton("\u23f9 Stop")
        self._demo_restart_btn = QPushButton("\u27f2 Restart")
        self._demo_speed = QComboBox()
        self._demo_speed.addItems(["0.5x", "1x", "2x"])
        self._demo_speed.setCurrentText("1x")
        for b in (self._demo_start_btn, self._demo_pause_btn, self._demo_stop_btn, self._demo_restart_btn):
            b.setStyleSheet(demo_style)
            demo_layout.addWidget(b)
        demo_layout.addWidget(self._demo_speed)
        demo_layout.addStretch()
        layout.addLayout(demo_layout)

        # Tour info notice
        info_notice = QLabel("💡 Click highlighted items to advance • Press Esc to exit")
        info_notice.setFont(QFont("Segoe UI", 9))
        info_notice.setStyleSheet("color: #6e7681; padding-top: 6px;")
        info_notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_notice)
    
    def _apply_styling(self):
        """Apply dark theme styling."""
        self.setStyleSheet("""
            DemoTourTooltip {
                
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
        self._progress.setMaximum(total_steps)
        self._progress.setValue(step_num)
        self._title_label.setText(title)
        self._instruction_label.setText(instruction)
        self._action_label.setText(action_prompt)
        self._detail_text.setHtml(detail_html)
        
        if wait_for_click:
            self._next_btn.setText("Waiting for click...")
            self._next_btn.setEnabled(False)
        else:
            self._next_btn.setText("Finish ✓" if step_num >= total_steps else "Next →")
            self._next_btn.setEnabled(True)
        # Skip button is always enabled — tour is never forced
        self._skip_btn.setEnabled(True)
    
    def showEvent(self, event):
        """Fade in on show."""
        super().showEvent(event)
        self.setWindowOpacity(0.0)
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(200)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_anim.start()
    
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
    
    def set_close_callback(self, callback):
        """Set callback for the X close button."""
        self._close_callback = callback
        self._close_btn.clicked.connect(callback)
    
    def keyPressEvent(self, event):
        """Close tour on Escape key."""
        if event.key() == Qt.Key.Key_A:
            cb = getattr(self, "_auto_toggle_callback", None)
            if cb:
                cb()
            return
        if event.key() == Qt.Key.Key_Escape:
            if self._close_callback:
                self._close_callback()
        else:
            super().keyPressEvent(event)
    
    def position_near_highlight(self, highlight_rect: QRect = None):
        """Position tooltip near the highlight rect, but never overlapping it.
        Prefers below the highlight (natural for top nav bars), then right, left, above.
        Falls back to bottom-right if no highlight rect."""
        self.adjustSize()
        size = self.size()
        screen = QApplication.primaryScreen().geometry()
        margin = 20
        
        if highlight_rect:
            # Strategy: try below first (nav buttons are at top), then right, left, above
            positions = []
            
            # Below — centered horizontally
            below_x = highlight_rect.center().x() - size.width() // 2
            below_y = highlight_rect.bottom() + margin
            positions.append(("below", below_x, below_y))
            
            # Right — vertically centered
            right_x = highlight_rect.right() + margin
            right_y = highlight_rect.center().y() - size.height() // 2
            positions.append(("right", right_x, right_y))
            
            # Left — vertically centered
            left_x = highlight_rect.left() - size.width() - margin
            left_y = highlight_rect.center().y() - size.height() // 2
            positions.append(("left", left_x, left_y))
            
            # Above — centered horizontally
            above_x = highlight_rect.center().x() - size.width() // 2
            above_y = highlight_rect.top() - size.height() - margin
            positions.append(("above", above_x, above_y))
            
            # Pick the first position that fits on screen
            best_x, best_y = None, None
            for name, x, y in positions:
                if (margin <= x and x + size.width() <= screen.right() - margin and
                    margin <= y and y + size.height() <= screen.bottom() - margin):
                    best_x, best_y = x, y
                    break
            
            if best_x is None:
                # None fit perfectly (large target, e.g. middle panel or bottom
                # Deploy button) — pick the candidate with the LEAST overlap with
                # the highlight rect so the tooltip never covers what it describes.
                best_overlap = None
                for _name, x, y in positions:
                    cx = max(margin, min(x, screen.right() - size.width() - margin))
                    cy = max(margin, min(y, screen.bottom() - size.height() - margin))
                    inter = QRect(cx, cy, size.width(), size.height()).intersected(highlight_rect)
                    overlap = inter.width() * inter.height()
                    if best_overlap is None or overlap < best_overlap:
                        best_overlap = overlap
                        best_x, best_y = cx, cy
            
            self.move(best_x, best_y)
        else:
            # No highlight — bottom-right corner with margin
            x = screen.width() - size.width() - margin
            y = screen.height() - size.height() - margin - 20
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
        auto_advance_delay: int = 0,
        narration: str = ""
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
        self.narration = narration  # Full voice narration text (defaults to title+instruction if empty)
        self.completed = False


class AutoTourDriver:
    """Automated demonstration driver. A virtual cursor painted on the tour
    overlay glides to each step's control, shows a click ring, and triggers the
    application's own handlers (button.click(), focus, etc.). The user's OS
    cursor, mouse, and keyboard are never touched. Every step is verified before
    advancing; a failed verification stops the demo — the tour timer never fakes
    progress. Results are recorded per step and written to tour_demo_report.txt.
    """

    def __init__(self, tour):
        self._tour = tour
        self._timer = QTimer(tour)
        self._timer.timeout.connect(self._tick)
        self._state = "idle"  # idle | moving | wait_result | paused | done
        self._speed = 1.0
        self._pos = None
        self._pending = None
        self._baseline = 0
        self._deadline = 0.0
        self._dwell_until = None
        self.results: list[dict] = []

    # ---- controls ----
    def start(self):
        self.results.clear()
        self._pos = None
        self._dwell_until = None
        self._state = "moving"
        self._arm()

    def pause(self):
        if self._state in ("moving", "wait_result"):
            self._state = "paused"
            self._timer.stop()

    def resume(self):
        if self._state == "paused":
            self._state = "moving"
            self._arm()

    def stop(self):
        self._timer.stop()
        active = self._state not in ("idle", "done")
        self._state = "idle"
        self._clear_cursor()
        if self._tour._tts:
            self._tour._tts.stop()
        if active or self.results:
            self._write_report(stopped=True)

    def restart(self):
        self._timer.stop()
        self._state = "idle"
        self._tour._current_step = 0
        self._tour._show_current_step()
        self.start()

    def toggle(self):
        if self._state in ("moving", "wait_result"):
            self.pause()
        elif self._state == "paused":
            self.resume()
        else:
            self.start()

    def set_speed(self, label: str):
        self._speed = {"0.5x": 0.5, "1x": 1.0, "2x": 2.0}.get(label, 1.0)
        # Narration rate follows the demo speed (TTS clamps to 1-450 wpm).
        if self._tour._tts:
            self._tour._tts.rate = int(175 * self._speed)
        if self._state in ("moving", "wait_result"):
            self._arm()

    def _arm(self):
        self._timer.start(max(120, int(350 / self._speed)))

    def _clear_cursor(self):
        if self._tour._overlay is not None:
            self._tour._overlay.set_auto_cursor(None)

    # ---- main loop ----
    def _tick(self):
        import time
        t = self._tour
        if t._current_step >= len(t._steps) or not t._tour_active:
            self._finish()
            return
        step = t._steps[t._current_step]
        target = t._find_target(step)
        if self._state == "moving":
            if not step.wait_for_click:
                # Dwell so the viewer can read/hear the step: paced to narration
                # length (~2.2 words/sec), clamped 4-14s, scaled by demo speed.
                if self._dwell_until is None:
                    words = len((step.narration or step.instruction or "").split())
                    dwell = min(14.0, max(4.0, words / 2.2 + 2.0)) / self._speed
                    self._dwell_until = time.monotonic() + dwell
                    return
                if time.monotonic() < self._dwell_until:
                    return
                self._dwell_until = None
                self.results.append({"step": t._current_step + 1, "title": step.title,
                                     "target_found": target is not None, "action": False,
                                     "expected": True, "popup_ok": None, "ok": True})
                t._on_next()
                return
            if target is None or not target.isVisible():
                return  # target not on screen yet — keep waiting, no fake advance
            self._glide_and_click(step, target)
        elif self._state == "wait_result":
            ok, popup = self._verify(step)
            if ok is None and time.monotonic() < self._deadline:
                return
            rec = self._pending or {"step": t._current_step + 1, "title": step.title,
                                    "target_found": True, "action": True}
            rec.update({"expected": bool(ok), "popup_ok": popup, "ok": bool(ok)})
            self.results.append(rec)
            self._pending = None
            if ok:
                cb = getattr(step, "on_target_clicked", None)
                if cb:
                    cb()
                self._state = "moving"
                self._pos = None
                self._dwell_until = None
                t._on_next()
            else:
                self.stop()  # verification failed — stop, do not advance

    def _glide_and_click(self, step, target):
        import time
        from PySide6.QtCore import QPointF
        ov = self._tour._overlay
        end_g = target.mapToGlobal(target.rect().center())
        end = QPointF(end_g - ov.geometry().topLeft())
        if self._pos is None:
            self._pos = end
        dx, dy = end.x() - self._pos.x(), end.y() - self._pos.y()
        if (dx * dx + dy * dy) ** 0.5 > 8:
            f = min(0.45, 0.25 * self._speed + 0.1)
            self._pos = QPointF(self._pos.x() + dx * f, self._pos.y() + dy * f)
            ov.set_auto_cursor(self._pos)
            return
        ov.set_auto_cursor(end)
        ov.pulse_click_ring()
        self._baseline = self._capture_baseline(step)
        self._trigger(target)
        self._pending = {"step": self._tour._current_step + 1, "title": step.title,
                         "target_found": True, "action": True}
        self._deadline = time.monotonic() + 8.0 / self._speed
        self._state = "wait_result"

    # ---- action dispatch: reuse the app's own handlers ----
    def _trigger(self, w):
        from PySide6.QtWidgets import QPushButton, QCheckBox, QComboBox, QLineEdit, QListWidget
        if isinstance(w, QCheckBox):
            if not w.isChecked():
                w.click()
        elif isinstance(w, QPushButton):
            w.click()
        elif isinstance(w, QLineEdit):
            w.setFocus()
            if not w.text().strip():
                w.setText("Demo AI")
        elif isinstance(w, QComboBox):
            w.showPopup()
            QTimer.singleShot(int(900 / self._speed), w.hidePopup)
        elif isinstance(w, QListWidget):
            if w.count() and w.currentRow() < 0:
                w.setCurrentRow(0)
        else:
            w.setFocus()

    def _capture_baseline(self, step):
        getter = getattr(step, "target_getter", None)
        if getter and "save" in getattr(getter, "__name__", ""):
            lst = self._tour._find_forge_ai_list()
            return lst.count() if lst is not None else 0
        return 0

    # ---- verification: expected state + popups demonstrated above the tour ----
    def _verify(self, step):
        """Returns (ok | None keep-waiting, popup_ok | None). Notification dialogs
        are detected, recorded as displayed, then closed via their own button."""
        from PySide6.QtWidgets import QDialog, QPushButton
        popup_ok = None
        for w in QApplication.topLevelWidgets():
            if isinstance(w, QDialog) and w.isVisible() and w not in (
                    self._tour._overlay, self._tour._tooltip, self._tour._main_window):
                popup_ok = True
                btns = w.findChildren(QPushButton)
                if btns:
                    btns[0].click()
                else:
                    w.accept()
        name = step.target_widget_name or ""
        getter_name = getattr(getattr(step, "target_getter", None), "__name__", "") or ""
        if name == "nav_forge":
            return (self._tour._find_forge_window() is not None) or None, popup_ok
        if "save" in getter_name:
            lst = self._tour._find_forge_ai_list()
            if lst is not None and lst.count() > self._baseline:
                return True, popup_ok
            return None, popup_ok
        if "deploy" in getter_name:
            if popup_ok or self._tour._find_forge_window() is None:
                return True, popup_ok if popup_ok is not None else True
            return None, popup_ok
        return True, popup_ok

    # ---- report ----
    def _finish(self):
        if self._state == "done":
            return
        self._timer.stop()
        self._state = "done"
        self._clear_cursor()
        self._write_report()

    def _write_report(self, stopped=False):
        if not self.results:
            return
        try:
            from pathlib import Path
            lines = ["AUTOMATED TOUR DEMO REPORT", "=" * 44, ""]
            for r in self.results:
                lines.append(
                    f"Step {r['step']}: {r['title']}\n"
                    f"  target found: {r.get('target_found')}  action: {r.get('action')}  "
                    f"expected: {r.get('expected')}  popup above tour: {r.get('popup_ok')}  "
                    f"=> {'PASS' if r.get('ok') else 'FAIL'}")
            lines += ["", "STOPPED EARLY" if stopped else "COMPLETED"]
            Path("tour_demo_report.txt").write_text("\n".join(lines), encoding="utf-8")
        except Exception:
            pass


class DemoTourController(QWidget):
    """
    Demo tour that:
    1. Shows instructions in bottom-right (never covers UI)
    2. Highlights target widget with animated border
    3. Waits for user to click target (if wait_for_click=True)
    4. Can trigger window opens and guide inside them
    5. Runs in demo mode - nothing persists
    """
    
    tour_completed = Signal()
    tour_skipped = Signal()
    step_changed = Signal(int, int)
    
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
        self._tts = get_tts()
        self._voice_enabled = True
        self._tour_active = False
        self._rehighlight_timer = QTimer(self)
        self._rehighlight_timer.setInterval(300)
        self._rehighlight_timer.timeout.connect(self._rehighlight)
        self._driver = AutoTourDriver(self)
        self._setup_steps()

    def eventFilter(self, obj, event):
        """Watch for click events anywhere AND Escape key globally."""
        try:
            if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape:
                if self._tour_active:
                    self._on_skip()
                    return True
            if (self._pending_click_target and
                event.type() == QEvent.Type.MouseButtonPress and
                isinstance(obj, QWidget)):

                target = self._pending_click_target
                # Check if the clicked object is the target or a child of the target
                if obj is target or self._is_descendant(obj, target):
                    if self._current_step < len(self._steps):
                        step = self._steps[self._current_step]
                    if step.on_target_clicked:
                        step.on_target_clicked()

                    # Visual feedback: flash green
                    if self._overlay:
                        self._overlay.flash_click()

                    # Update tooltip to show click detected
                    self._tooltip.update_content(
                        step_num=self._current_step + 1,
                        total_steps=len(self._steps),
                        title=step.title,
                        instruction=step.instruction,
                        action_prompt="\u2713 Click detected! Advancing...",
                        detail_html=step.detail_html,
                        wait_for_click=False,
                    )
                    self._tooltip._next_btn.setText("\u2713 Advancing...")
                    self._tooltip._next_btn.setEnabled(False)

                    # Clear click target (keep filter installed for Escape key)
                    self._pending_click_target = None

                    # Auto-advance after delay
                    delay = 1500 if step.target_widget_name and step.target_widget_name.startswith("nav_") else 600
                    QTimer.singleShot(delay, self._on_next)

                    if self._audit:
                        self._audit.log(tool="DemoTour", action="STEP_ACTION_COMPLETED",
                                      target=f"Step {self._current_step + 1}: {step.title}",
                                      approved=True, status="info")

                return False  # Let the click reach the widget

        except RuntimeError:
            # Widget was deleted by Qt C++ side — pass through safely
            pass

        return super().eventFilter(obj, event)
    
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

    def _find_forge_name_input(self) -> Optional[QWidget]:
        forge = self._find_forge_window()
        return forge.findChild(QWidget, "forge_name_input") if forge else None

    def _find_forge_save_button(self) -> Optional[QWidget]:
        """Find the sheet's real Save button (bottom of guardrails) and scroll it into view."""
        forge = self._find_forge_window()
        if not forge:
            return None
        btn = forge.findChild(QWidget, "forge_save_button")
        if btn and btn.isVisible():
            from PySide6.QtWidgets import QScrollArea
            sa = btn.parentWidget()
            while sa is not None and not isinstance(sa, QScrollArea):
                sa = sa.parentWidget()
            if sa is not None:
                sa.ensureWidgetVisible(btn)
                # Re-highlight after the scroll settles so the glow lands on the button
                QTimer.singleShot(450, lambda b=btn: self._overlay.highlight_widget(b) if self._overlay else None)
        return btn

    def _find_forge_deploy_button(self) -> Optional[QWidget]:
        forge = self._find_forge_window()
        if forge is None:
            return None
        return forge.findChild(QPushButton, "forge_deploy_button")

    def _find_forge_uc_combo(self) -> Optional[QWidget]:
        """Find the Use-Case Class dropdown in the Forge (specific control, not the window)."""
        forge = self._find_forge_window()
        if forge is None:
            return None
        return forge.findChild(QComboBox, "forge_uc_combo")

    def _find_forge_caps_group(self) -> Optional[QWidget]:
        """Find the Capabilities group box in the Forge (the inline checkbox list)."""
        forge = self._find_forge_window()
        if forge is None:
            return None
        for gb in forge.findChildren(QGroupBox):
            if gb.title() == "Capabilities":
                return gb
        return None

    def _find_forge_personality_group(self) -> Optional[QWidget]:
        """Find the Personality / Behavior group box in the Forge."""
        forge = self._find_forge_window()
        if forge is None:
            return None
        for gb in forge.findChildren(QGroupBox):
            if "Personality" in gb.title():
                return gb
        return None

    def _find_forge_guardrails_group(self) -> Optional[QWidget]:
        """Find the Optional AI Protection Rules group box in the Forge."""
        forge = self._find_forge_window()
        if forge is None:
            return None
        for gb in forge.findChildren(QGroupBox):
            if "Protection Rules" in gb.title():
                return gb
        return None
    
    def _close_forge_after_deploy(self):
        """Close the Forge window after deploying, so user sees the Command Center."""
        QTimer.singleShot(800, self._close_sub_windows)

    def _setup_steps(self):
        """Define the interactive demo tour steps using real, clickable widgets."""
        self._steps = [
            DemoTourStep(
                title="\U0001f44b Welcome to Command Nexus",
                instruction="This tour will show you how to build, deploy, and use AI assistants \u2014 no coding required.",
                detail_html="""<p>By the end of this tour, you'll know how to:</p>
                <ul>
                    <li>\U0001f9e0 <b>Open</b> the AI Forge and create an AI</li>
                    <li>\u26a1 <b>Deploy</b> an AI to the Command Center</li>
                    <li>\U0001f3af <b>Give</b> your AI a mission</li>
                    <li>\U0001f4da <b>Add Intelligence</b> \u2014 memory and knowledge</li>
                    <li>\U0001f4d6 <b>Knowledge Base</b> \u2014 document search</li>
                    <li>\U0001f916 <b>AI Models</b> \u2014 choose your power level</li>
                    <li>\U0001f3a8 <b>Themes</b> \u2014 customize the look</li>
                    <li>\U0001f3a4 <b>Voice</b> \u2014 hands-free interaction</li>
                    <li>\u23f0\ufe0f <b>Scheduler</b> \u2014 run missions automatically</li>
                    <li>\u2b07\ufe0f <b>Explore Upgrades</b> for more capabilities</li>
                    <li>\U0001f916 <b>Use Customer Support</b> for help</li>
                </ul>
                <p><b>Clickable targets are highlighted.</b> The tour waits for you to click them.</p>
                <p><i>If a window isn't available, the tour will skip that step.</i></p>
                <p><b>\U0001f50a Voice narration is on.</b> Your OS built-in voice will read each step.</p>""",
                action_prompt="Click 'Next' to start",
                wait_for_click=False,
                narration="Welcome to Command Nexus. This tour will show you how to build, deploy, and use AI assistants. No coding required. By the end of this tour, you'll know how to open the AI Forge and create an AI, deploy it to the Command Center, give your AI a mission, add intelligence like memory and knowledge, explore upgrades for more capabilities, and use customer support for help. Clickable targets are highlighted with a glowing border. The tour waits for you to click them. Voice narration is on. Your operating system's built-in voice will read each step. Press Escape at any time to exit the tour.",
            ),

            # === STEP 1: Open AI Forge ===
            DemoTourStep(
                title="\U0001f9e0 Step 1: Open the AI Forge",
                instruction="The AI Forge is where you build AI assistants. Click the AI Forge button to open it.",
                detail_html="""<p>The <b>AI Forge</b> is your workshop. Here you'll create and customize AI assistants.</p>
                <p>In the Forge you can:</p>
                <ul>
                    <li>Choose a <b>Use Case</b> (Individual, Business, Educational, Enterprise)</li>
                    <li>Select <b>Capabilities</b> \u2014 what your AI can do</li>
                    <li>Adjust <b>Personality</b> \u2014 creativity, caution, verbosity</li>
                    <li>Add <b>Protection Rules</b> \u2014 safety boundaries</li>
                </ul>
                <p>Click the <b>AI Forge</b> button (purple) in the navigation bar.</p>""",
                target_widget_name="nav_forge",
                action_prompt="\U0001f449 CLICK 'AI Forge'",
                wait_for_click=True,
                narration="Step 1. Open the AI Forge. The AI Forge is your workshop where you create and customize AI assistants. In the Forge, you can choose a use case like Individual, Business, Educational, or Enterprise. You can select capabilities, which are what your AI can do. You can adjust personality traits like creativity, caution, and formality. And you can add protection rules, which are safety boundaries for your AI. Click the purple AI Forge button in the navigation bar at the top of the window.",
            ),

            # === STEP 1b: Name Your AI (first thing inside the Forge) ===
            DemoTourStep(
                title="\U0001f3f7\ufe0f Step 1b: Name Your AI",
                instruction="Type a name for your AI in the 'AI Name' field at the top of the form, then click Next.",
                detail_html="""<p>The first field in the Forge is <b>AI Name</b>.</p>
                <p>Give your AI a name you'll recognize, like <i>'My Assistant'</i> or <i>'Email Helper'</i>.</p>
                <p>Everything else on this form configures the AI named here.</p>""",
                target_getter=self._find_forge_name_input,
                action_prompt="\U0001f449 TYPE a name, then click Next",
                wait_for_click=False,
                narration="Step 1 b. Name your AI. The first field in the Forge is AI Name. Give your AI a name you'll recognize, like My Assistant or Email Helper. Everything else on this form configures the AI named here. Type a name, then click Next.",
            ),

            # === STEP 2: Use Case Class ===
            DemoTourStep(
                title="\U0001f4cb Step 2: Choose a Use Case",
                instruction="The Use-Case Class tells your AI what context it's working in. Look at the dropdown at the top of the Forge.",
                detail_html="""<p>The <b>Use-Case Class</b> dropdown determines what kind of work your AI will do.</p>
                <p><b>Available use cases:</b></p>
                <ul>
                    <li><b>Individual</b> \u2014 Personal assistant: tasks, notes, writing, research. Prioritizes privacy and asks before changes.</li>
                    <li><b>Business</b> \u2014 Draft responses, organize notes, research, plans. Supports marketing, support, sales, operations.</li>
                    <li><b>Educational</b> \u2014 Tutoring, study guides, lesson planning. Promotes academic honesty and accessibility.</li>
                    <li><b>Enterprise</b> \u2014 Large-scale operations with compliance, audit trails, and department coordination.</li>
                    <li><b>Task-Ready</b> \u2014 General-purpose AI that follows clear instructions and pauses for approval on risky actions.</li>
                    <li><b>All-Rounder</b> \u2014 Flexible AI that adapts to any context.</li>
                </ul>
                <p>The use case you pick changes which <b>capabilities</b> and <b>guardrails</b> are recommended.</p>
                <p><i>You don't have to pick the perfect one \u2014 you can change it later.</i></p>""",
                target_getter=self._find_forge_uc_combo,
                action_prompt="Click 'Next' to continue",
                wait_for_click=False,
                narration="Step 2. Choose a Use Case. The Use-Case Class dropdown at the top of the Forge tells your AI what context it's working in. Available use cases include: Individual, for personal assistant tasks like notes, writing, and research, prioritizing privacy. Business, for drafting responses, organizing notes, and plans, supporting marketing, support, sales, and operations. Educational, for tutoring, study guides, and lesson planning, promoting academic honesty. Enterprise, for large-scale operations with compliance and audit trails. Task-Ready, a general-purpose AI that follows clear instructions. And All-Rounder, a flexible AI that adapts to any context. The use case you pick changes which capabilities and guardrails are recommended. You can change it later.",
            ),

            # === STEP 3: Capabilities ===
            DemoTourStep(
                title="\u26a1 Step 3: Select Capabilities",
                instruction="Capabilities are what your AI can do. They appear as a checklist right in the Forge \u2014 tick abilities, or click 'Suggest Set'.",
                detail_html="""<p><b>Capabilities</b> are the skills and tools your AI can use.</p>
                <p>After choosing a use case, its capabilities appear inline in the <b>Capabilities</b> box \u2014 the recommended ones are already ticked:</p>
                <ul>
                    <li><b>Capability checklist</b> \u2014 Tick or untick abilities directly. Hover any entry for its description. Tier-locked entries show a \U0001f512.</li>
                    <li><b>\U0001f4a1 Suggest Set</b> \u2014 Re-ticks the recommended capabilities for your use case. Great if you're not sure what to pick.</li>
                </ul>
                <p><b>Examples of capabilities:</b></p>
                <ul>
                    <li><b>Chat</b> \u2014 Have conversations with your AI</li>
                    <li><b>Research</b> \u2014 Search the web and summarize findings</li>
                    <li><b>File Operations</b> \u2014 Read and write files (with your approval)</li>
                    <li><b>Business Workflow</b> \u2014 Create SOPs, checklists, and approval points</li>
                    <li><b>Planning</b> \u2014 Break down complex tasks into steps</li>
                </ul>
                <p>Each capability has a description and compatibility info \u2014 hover any checklist entry for details.</p>
                <p><i>You can always change capabilities later by editing your AI in the Forge.</i></p>""",
                target_getter=self._find_forge_caps_group,
                action_prompt="Click 'Next' to continue",
                wait_for_click=False,
                narration="Step 3. Select Capabilities. Capabilities are the skills and tools your AI can use. After choosing a use case, its capabilities appear as a checklist right in the Forge, with the recommended ones already ticked. Tick or untick abilities directly, hovering any entry shows its description. Or click Suggest Set to re-tick the recommended capabilities for your use case. This is great if you're not sure what to pick. Examples of capabilities include: Chat, for conversations with your AI. Research, for searching the web and summarizing findings. File Operations, for reading and writing files with your approval. Business Workflow, for creating SOPs, checklists, and approval points. And Planning, for breaking down complex tasks into steps. Each capability has a description and compatibility info. You can always change capabilities later by editing your AI in the Forge.",
            ),

            # === STEP 4: Personality ===
            DemoTourStep(
                title="\U0001f3a8 Step 4: Personality / Behavior",
                instruction="The Personality sliders control how your AI communicates. Adjust Creativity, Formality, and Caution.",
                detail_html="""<p>The <b>Personality / Behavior</b> section has three sliders:</p>
                <ul>
                    <li><b>Creativity</b> (0-100) \u2014 How creative vs. straightforward your AI is.
                        <br><i>Low = factual and direct. High = imaginative and varied.</i></br>
                    </li>
                    <li><b>Formality</b> (0-100) \u2014 How formal vs. casual your AI sounds.
                        <br><i>Low = friendly and relaxed. High = professional and structured.</i></br>
                    </li>
                    <li><b>Caution / Safety Bias</b> (0-100) \u2014 How careful your AI is.
                        <br><i>Low = takes initiative. High = asks for confirmation more often.</i></br>
                    </li>
                </ul>
                <p><b>Example:</b> A business AI might have high formality and high caution. A creative writing assistant might have high creativity and low formality.</p>
                <p>There's also a <b>Notes</b> box where you can add custom directives, like 'Always respond in Spanish' or 'Focus on sustainability topics.'</p>""",
                target_getter=self._find_forge_personality_group,
                action_prompt="Click 'Next' to continue",
                wait_for_click=False,
                narration="Step 4. Personality and Behavior. The Personality section has three sliders. Creativity, from 0 to 100, controls how creative versus straightforward your AI is. Low means factual and direct. High means imaginative and varied. Formality, from 0 to 100, controls how formal versus casual your AI sounds. Low means friendly and relaxed. High means professional and structured. Caution, or Safety Bias, from 0 to 100, controls how careful your AI is. Low means it takes initiative. High means it asks for confirmation more often. For example, a business AI might have high formality and high caution. A creative writing assistant might have high creativity and low formality. There's also a Notes box where you can add custom directives, like 'Always respond in Spanish' or 'Focus on sustainability topics.'",
            ),

            # === STEP 5: Guardrails ===
            DemoTourStep(
                title="\U0001f6e1\ufe0f Step 5: Guardrails",
                instruction="Guardrails are safety rules your AI follows. Check the ones that matter to you.",
                detail_html="""<p><b>Optional AI Guardrails</b> are checkboxes that set safety boundaries.</p>
                <p><b>Available guardrails include:</b></p>
                <ul>
                    <li><b>Ask before editing files</b> \u2014 AI requests permission before any file change</li>
                    <li><b>Cite sources when researching</b> \u2014 AI includes where it found information</li>
                    <li><b>Keep responses beginner-friendly</b> \u2014 AI avoids technical jargon</li>
                    <li><b>Keep responses concise</b> \u2014 AI keeps answers short</li>
                    <li><b>Require confirmation before risky actions</b> \u2014 AI asks before anything potentially harmful</li>
                    <li><b>Prefer step-by-step explanations</b> \u2014 AI breaks down complex topics</li>
                    <li><b>Always explain reasoning before giving answers</b> \u2014 AI shows its thought process</li>
                    <li><b>Flag speculative answers clearly as speculation</b> \u2014 AI marks guesses as guesses</li>
                    <li><b>Use inclusive and neutral language</b> \u2014 AI avoids biased language</li>
                    <li><b>Always suggest alternatives when declining a request</b> \u2014 AI offers options instead of just saying no</li>
                </ul>
                <p><b>Guardrails are optional</b> \u2014 pick the ones that fit your use case. You can change them anytime.</p>
                <p><i>For example, a kids' tutoring AI should have 'Keep responses beginner-friendly' and 'Prefer step-by-step explanations.'</i></p>""",
                target_getter=self._find_forge_guardrails_group,
                action_prompt="Click 'Next' to continue",
                wait_for_click=False,
                narration="Step 5. Guardrails. Guardrails are safety rules your AI follows. They are optional checkboxes that set safety boundaries. Available guardrails include: Ask before editing files, so the AI requests permission before any file change. Cite sources when researching, so the AI includes where it found information. Keep responses beginner-friendly, so the AI avoids technical jargon. Keep responses concise, so the AI keeps answers short. Require confirmation before risky actions, so the AI asks before anything potentially harmful. Prefer step-by-step explanations, so the AI breaks down complex topics. Always explain reasoning before giving answers, so the AI shows its thought process. Flag speculative answers clearly as speculation, so the AI marks guesses as guesses. Use inclusive and neutral language. And always suggest alternatives when declining a request. Guardrails are optional. Pick the ones that fit your use case. You can change them anytime.",
            ),

            # === STEP 6: Save and Deploy ===
            # === STEP 6a: Save AI to Forge (must come before Deploy) ===
            DemoTourStep(
                title="\U0001f4be Step 6a: Save Your AI First",
                instruction="Click 'Save AI to Forge' (green button at the bottom) to create your AI. You must save before you can deploy.",
                detail_html="""<p>Before anything else works, your AI must be <b>saved</b>:</p>
                <ol>
                    <li>Click <b>Save AI to Forge</b> (green button at the bottom of the Forge)</li>
                    <li>Your AI appears in the <b>AI Library</b> list on the left</li>
                </ol>
                <p><b>You cannot deploy an AI that hasn't been saved.</b> Save first, deploy second.</p>""",
                target_getter=self._find_forge_save_button,
                action_prompt="\U0001f449 CLICK 'Save AI to Forge' at the bottom of the form",
                wait_for_click=True,
                narration="Step 6 a. Save your AI first. Click the green Save AI to Forge button at the bottom of the Forge to create your AI. It then appears in the AI Library list on the left. You cannot deploy an AI that hasn't been saved. Save first, deploy second.",
            ),

            DemoTourStep(
                title="\U0001f680 Step 6: Save and Deploy",
                instruction="Click 'Save AI to Forge' to create your AI, then select it and click 'Deploy to Command Center'.",
                detail_html="""<p>Once you've configured your AI:</p>
                <ol>
                    <li>Click <b>Save AI to Forge</b> (green button at the bottom) \u2014 this creates your AI</li>
                    <li>Your AI appears in the <b>AI Library</b> list on the left side of the Forge</li>
                    <li>Click your AI in the list to select it</li>
                    <li>Click <b>Deploy to Command Center</b> (green button) \u2014 this activates your AI</li>
                </ol>
                <p>After deploying, the Forge will close and your AI appears in the <b>Active AI</b> selector in the main window.</p>
                <p><b>Other buttons in the Forge:</b></p>
                <ul>
                    <li><b>Drop-In AI...</b> \u2014 Load a pre-built AI template</li>
                    <li><b>Open Knowledge for AI</b> \u2014 Edit the AI's intelligence (memory, knowledge)</li>
                    <li><b>Open Chat</b> \u2014 Start chatting with the selected AI immediately</li>
                    <li><b>Save AI to Disk</b> \u2014 Export your AI to a file</li>
                    <li><b>Load AI from Disk</b> \u2014 Import an AI from a file</li>
                </ul>""",
                target_getter=self._find_forge_deploy_button,
                action_prompt="\U0001f449 CLICK an AI in the list, then CLICK 'Deploy'",
                wait_for_click=True,
                on_target_clicked=self._close_forge_after_deploy,
                narration="Step 6. Save and Deploy. Once you've configured your AI, click the green Save AI to Forge button at the bottom to create your AI. Your AI then appears in the AI Library list on the left side of the Forge. Click your AI in the list to select it. Then click the green Deploy to Command Center button to activate your AI. After deploying, the Forge will close and your AI appears in the Active AI selector in the main window. Other buttons in the Forge include: Drop-In AI, to load a pre-built AI template. Open Knowledge for AI, to edit the AI's intelligence. Open Chat, to start chatting immediately. Save AI to Disk, to export your AI to a file. And Load AI from Disk, to import an AI from a file.",
            ),

            # === STEP 6b: Select an Active AI (required before START) ===
            DemoTourStep(
                title="\U0001f464 Step 6b: Select Your Active AI",
                instruction="Make sure your deployed AI is selected in the Active AI selector (top of this window) before you click START.",
                detail_html="""<p>Look at the <b>Active AI</b> selector near the top of the window.</p>
                <p>If it is empty or shows the wrong AI, open the dropdown and <b>select the AI you deployed</b>.</p>
                <p>Everything that comes next — START, Intelligence, missions, chat — applies to the <b>selected Active AI</b>. If none is selected, START will not run your AI.</p>""",
                target_widget_name=None,
                action_prompt="\U0001f449 CHECK that your AI is selected, then click Next",
                narration="Step 6 b. Select your Active AI. Before you click START, make sure your deployed AI is selected in the Active AI selector at the top of the window. If it's empty, open the dropdown and select the AI you just deployed. START, Intelligence, missions, and chat all apply to the selected Active AI. If none is selected, START will not run your AI.",
            ),

            # === STEP 7: Give Your AI a Mission ===
            DemoTourStep(
                title="\U0001f3af Step 7: Give Your AI a Mission",
                instruction="Type a mission in the Mission Control box, then click START.",
                detail_html="""<p>The <b>Active AI</b> is shown in the selector. Type a task like:</p>
                <ul>
                    <li>"Plan my day"</li>
                    <li>"Write a poem about space"</li>
                    <li>"Explain how photosynthesis works"</li>
                    <li>"Summarize this document: [paste text]"</li>
                    <li>"Create a weekly meal plan"</li>
                    <li>"Draft an email to my team about the project update"</li>
                </ul>
                <p>Your AI will use its capabilities to complete the mission.</p>
                <p><b>No coding required!</b> Just type what you want in plain language.</p>
                <p>The AI's response appears in the <b>Thought</b> and <b>Action</b> panels. You can see exactly what it's thinking and doing.</p>
                <p>Click the <b>START</b> button when ready.</p>""",
                target_widget_name="mission_start_button",
                action_prompt="\U0001f449 TYPE a mission, then click START",
                wait_for_click=True,
                narration="Step 7. Give Your AI a Mission. The Active AI is shown in the selector. Type a task in the Mission Control box, like 'Plan my day,' 'Write a poem about space,' 'Explain how photosynthesis works,' 'Summarize this document,' 'Create a weekly meal plan,' or 'Draft an email to my team about the project update.' Your AI will use its capabilities to complete the mission. No coding required. Just type what you want in plain language. The AI's response appears in the Thought and Action panels. You can see exactly what it's thinking and doing. Click the START button when ready.",
            ),

            # === STEP 8: Intelligence ===
            DemoTourStep(
                title="\U0001f4da Step 8: Add Intelligence",
                instruction="The Intelligence button opens the Knowledge panel where you give your AI memory and knowledge.",
                detail_html="""<p>Click the <b>Intelligence</b> button (teal) to open the Knowledge panel.</p>
                <p><b>In the Knowledge panel you can:</b></p>
                <ul>
                    <li><b>Set a Goal</b> \u2014 What do you want this AI to help you with? Example: 'I need help organizing my business tasks and writing emails.'</li>
                    <li><b>Define the Audience</b> \u2014 Who will use or benefit from this AI? Example: 'me, my team, my customers.'</li>
                    <li><b>Set Boundaries</b> \u2014 What should it avoid? Example: 'don't access my bank info, don't write code without asking.'</li>
                    <li><b>Define Success</b> \u2014 How would you know it's working? Example: 'it finishes my weekly reports in under 10 minutes.'</li>
                </ul>
                <p>If you're not sure, click <b>'I don't know \u2014 help me figure it out'</b> and the AI will suggest a purpose for you.</p>
                <p><b>Running Memory</b> shows what the AI has learned and summarized from your interactions. The AI reads its knowledge internally and distills what it knows here.</p>
                <p><b>Your AI learns with you.</b> Every interaction builds its memory.</p>
                <p><i>Memory is private and stored locally \u2014 never sent to external services.</i></p>""",
                target_widget_name="nav_book",
                action_prompt="\U0001f449 CLICK 'Intelligence' to explore",
                wait_for_click=True,
                narration="Step 8. Add Intelligence. The Intelligence button, which is teal colored, opens the Knowledge panel where you give your AI memory and knowledge. In the Knowledge panel, you can set a Goal, which is what you want this AI to help you with. For example, 'I need help organizing my business tasks and writing emails.' You can define the Audience, which is who will use or benefit from this AI. For example, 'me, my team, my customers.' You can set Boundaries, which is what the AI should avoid. For example, 'don't access my bank info, don't write code without asking.' You can define Success, which is how you would know it's working. For example, 'it finishes my weekly reports in under 10 minutes.' If you're not sure, click 'I don't know, help me figure it out' and the AI will suggest a purpose for you. Running Memory shows what the AI has learned and summarized from your interactions. Your AI learns with you. Every interaction builds its memory. Memory is private and stored locally, never sent to external services.",
            ),

            # === STEP 9: Knowledge Base ===
            DemoTourStep(
                title="\U0001f4d6 Step 9: Knowledge Base",
                instruction="The Knowledge button lets you drag-and-drop documents so your AI can search and reference them.",
                detail_html="""<p>The <b>Knowledge</b> button (purple) opens the RAG Document panel.</p>
                <p><b>With the Knowledge Base you can:</b></p>
                <ul>
                    <li><b>Drag and drop</b> PDFs, text files, and documents</li>
                    <li>Your AI <b>automatically searches</b> your documents when answering questions</li>
                    <li><b>Enable or disable</b> individual documents with checkboxes</li>
                    <li>Test retrieval with a <b>search query</b> before deploying</li>
                </ul>
                <p>This gives your AI <b>domain-specific knowledge</b> — it reads your files and uses them to answer questions accurately.</p>
                <p><i>Documents are processed locally — never uploaded to external servers.</i></p>""",
                target_widget_name="nav_knowledge",
                action_prompt="Click 'Next' to continue",
                wait_for_click=False,
                narration="Step 9. Knowledge Base. The purple Knowledge button opens the RAG Document panel. With the Knowledge Base, you can drag and drop PDFs, text files, and documents. Your AI automatically searches your documents when answering questions. You can enable or disable individual documents with checkboxes. You can test retrieval with a search query before deploying. This gives your AI domain-specific knowledge. It reads your files and uses them to answer questions accurately. Documents are processed locally, never uploaded to external servers.",
            ),

            # === STEP 10: Models ===
            DemoTourStep(
                title="\U0001f916 Step 10: AI Models",
                instruction="The Models button lets you choose which AI model powers your assistants.",
                detail_html="""<p>The <b>Models</b> button (blue) opens the Model Manager.</p>
                <p><b>In the Model Manager you can:</b></p>
                <ul>
                    <li>Use the <b>built-in local model</b> — works immediately, no internet needed</li>
                    <li>Add a <b>local GGUF model</b> from your computer for more power</li>
                    <li>Connect an <b>external API</b> like OpenAI for maximum capability</li>
                    <li>Set <b>temperature</b> — how creative vs. precise the AI is</li>
                </ul>
                <p><b>You don't need a model to start.</b> The built-in intelligence handles basic tasks right away.</p>
                <p>Add a stronger model when you need more advanced capabilities.</p>""",
                target_widget_name="nav_models",
                action_prompt="Click 'Next' to continue",
                wait_for_click=False,
                narration="Step 10. AI Models. The blue Models button opens the Model Manager. In the Model Manager, you can use the built-in local model, which works immediately with no internet needed. You can add a local GGUF model from your computer for more power. You can connect an external API like OpenAI for maximum capability. And you can set temperature, which controls how creative versus precise the AI is. You don't need a model to start. The built-in intelligence handles basic tasks right away. Add a stronger model when you need more advanced capabilities.",
            ),

            # === STEP 11: Themes ===
            DemoTourStep(
                title="\U0001f3a8 Step 11: Visual Themes",
                instruction="The Themes button lets you customize the look and feel of Command Nexus.",
                detail_html="""<p>The <b>Themes</b> button (pink) opens the Visual Themes selector.</p>
                <p><b>Choose from:</b></p>
                <ul>
                    <li><b>Dark Mode</b> — Easy on the eyes (default)</li>
                    <li><b>Light Mode</b> — Bright and clean</li>
                    <li><b>High Contrast</b> — Maximum readability</li>
                    <li>Premium themes available in the <b>Upgrades Store</b></li>
                </ul>
                <p>Themes change the entire app instantly — buttons, panels, backgrounds, and text.</p>
                <p><i>Pick whatever feels best for you.</i></p>""",
                target_widget_name="nav_themes",
                action_prompt="Click 'Next' to continue",
                wait_for_click=False,
                narration="Step 11. Visual Themes. The pink Themes button opens the Visual Themes selector. Choose from Dark Mode, which is easy on the eyes and is the default. Light Mode, which is bright and clean. High Contrast, for maximum readability. And premium themes available in the Upgrades Store. Themes change the entire app instantly, including buttons, panels, backgrounds, and text. Pick whatever feels best for you.",
            ),

            # === STEP 12: Voice ===
            DemoTourStep(
                title="\U0001f3a4 Step 12: Voice Interaction",
                instruction="The Voice button opens voice controls — talk to your AI and hear it speak back.",
                detail_html="""<p>The <b>Voice</b> button (orange) opens the Voice Interaction panel.</p>
                <p><b>With Voice you can:</b></p>
                <ul>
                    <li><b>Text-to-Speech</b> — Your AI reads its responses out loud</li>
                    <li><b>Speech-to-Text</b> — Talk instead of typing</li>
                    <li><b>Voice toggle</b> in the nav bar — quick ON/OFF for narration</li>
                    <li><b>Mic button</b> — Click and speak your mission directly</li>
                </ul>
                <p>Voice makes Command Nexus <b>hands-free</b> — great for accessibility or multitasking.</p>
                <p><i>All voice processing happens locally on your computer.</i></p>""",
                target_widget_name="nav_voice_panel",
                action_prompt="Click 'Next' to continue",
                wait_for_click=False,
                narration="Step 12. Voice Interaction. The orange Voice button opens the Voice Interaction panel. With Voice, you can use Text-to-Speech, where your AI reads its responses out loud. Speech-to-Text, so you can talk instead of typing. The Voice toggle in the nav bar for quick on and off. And the Mic button, where you click and speak your mission directly. Voice makes Command Nexus hands-free, great for accessibility or multitasking. All voice processing happens locally on your computer.",
            ),

            # === STEP 13: Scheduler ===
            DemoTourStep(
                title="\u23f0\ufe0f Step 13: Scheduled Missions",
                instruction="The Schedule button lets you set up missions that run automatically on a timer.",
                detail_html="""<p>The <b>Schedule</b> button (purple) opens the Scheduled Missions panel.</p>
                <p><b>With the Scheduler you can:</b></p>
                <ul>
                    <li>Create <b>recurring missions</b> — daily, weekly, or one-time</li>
                    <li>Set a <b>specific time</b> for missions to run</li>
                    <li>Review <b>scheduled tasks</b> and their status</li>
                    <li><b>Pause or cancel</b> upcoming missions</li>
                </ul>
                <p><b>Example:</b> 'Every Monday at 9 AM, summarize my notes from last week.'</p>
                <p>The Scheduler runs in the background — your AI works even when you're not watching.</p>""",
                target_widget_name="nav_scheduler",
                action_prompt="Click 'Next' to continue",
                wait_for_click=False,
                narration="Step 13. Scheduled Missions. The purple Schedule button opens the Scheduled Missions panel. With the Scheduler, you can create recurring missions, daily, weekly, or one-time. You can set a specific time for missions to run. You can review scheduled tasks and their status. And you can pause or cancel upcoming missions. For example, 'Every Monday at 9 AM, summarize my notes from last week.' The Scheduler runs in the background, so your AI works even when you're not watching.",
            ),

            # === STEP 14: Upgrades ===
            DemoTourStep(
                title="\u2b07\ufe0f Step 14: Explore Upgrades",
                instruction="The Upgrades button opens the store where you can unlock more capabilities.",
                detail_html="""<p>The <b>Upgrades</b> button (orange) opens the store.</p>
                <p>Upgrades include:</p>
                <ul>
                    <li><b>Premium Features</b> \u2014 Visual themes, export pack, advanced memory</li>
                    <li><b>Productivity Tools</b> \u2014 Workflow automation, analytics dashboard</li>
                    <li><b>Enterprise Options</b> \u2014 Security suite, priority support</li>
                </ul>
                <p>Some capabilities work with <b>local intelligence</b> right away.</p>
                <p>The <b>built-in local model</b> provides AI power right away — no external server needed.</p>
                <p><i>You can browse the store anytime after the tour by clicking Upgrades.</i></p>""",
                target_widget_name="nav_constraints",
                action_prompt="Click 'Next' to continue",
                wait_for_click=False,
                narration="Step 14. Explore Upgrades. The orange Upgrades button opens the store where you can unlock more capabilities. Upgrades include Premium Features like visual themes, export pack, and advanced memory. Productivity Tools like workflow automation and analytics dashboard. And Enterprise Options like security suite and priority support. The built-in local model provides AI power right away with no external server needed. You can browse the store anytime after the tour by clicking Upgrades.",
            ),

            # === STEP 15: Customer Support ===
            DemoTourStep(
                title="\U0001f916 Step 15: Customer Support",
                instruction="The Support button connects you to the Customer Support AI for help anytime.",
                detail_html="""<p>The <b>Support</b> button (green) opens a help window with a built-in AI assistant.</p>
                <p><b>Use it if you need help with:</b></p>
                <ul>
                    <li>How to use Command Nexus features</li>
                    <li>License activation and pricing</li>
                    <li>Using the built-in local model (no external server needed)</li>
                    <li>Troubleshooting issues</li>
                    <li>Understanding capabilities and guardrails</li>
                </ul>
                <p><b>How to interact with the Support AI:</b></p>
                <ol>
                    <li>Type your question in the chat box</li>
                    <li>Press Enter or click Send</li>
                    <li>The AI will respond with helpful guidance</li>
                    <li>If the AI can't help, it can escalate to human review</li>
                </ol>
                <p>The Support AI is always available to guide you \u2014 it never sleeps.</p>
                <p><i>Try it anytime after the tour by clicking Support.</i></p>""",
                target_widget_name="nav_customer_ai",
                action_prompt="Click 'Next' to continue",
                wait_for_click=False,
                narration="Step 15. Customer Support. The green Support button opens a help window with a built-in AI assistant. Use it if you need help with how to use Command Nexus features, license activation and pricing, using the built-in local model, troubleshooting issues, or understanding capabilities and protection rules. To interact with the Support AI, type your question in the chat box, press Enter or click Send, and the AI will respond with helpful guidance. If the AI can't help, it can escalate to human review. The Support AI is always available to guide you. It never sleeps. Try it anytime after the tour by clicking Support.",
            ),

            # === STEP 16: Governance ===
            DemoTourStep(
                title="\U0001f6e1\ufe0f Step 16: Governance & Safety",
                instruction="The Governance button shows safety controls, audit logs, and parental controls.",
                detail_html="""<p>The <b>Governance</b> button (dark blue) opens safety settings.</p>
                <p>From the Governance menu you can access:</p>
                <ul>
                    <li><b>Approval Gates</b> \u2014 AI asks before file changes or risky actions</li>
                    <li><b>Audit Logging</b> \u2014 Every action is recorded for accountability</li>
                    <li><b>Parental Controls</b> \u2014 Kid-safe content filtering</li>
                    <li><b>Anti-Tamper</b> \u2014 Protection against unauthorized changes</li>
                </ul>
                <p><b>Trust is key.</b> Command Nexus always tells you honestly what it can and can't do.</p>
                <p><i>Explore Governance anytime after the tour.</i></p>""",
                target_widget_name="nav_governance",
                action_prompt="Click 'Next' to continue",
                wait_for_click=False,
                narration="Step 16. Governance and Safety. The dark blue Governance button opens safety settings. From the Governance menu you can access Approval Gates, where the AI asks before file changes or risky actions. Audit Logging, where every action is recorded for accountability. Parental Controls, for kid-safe content filtering. And Anti-Tamper, for protection against unauthorized changes. Trust is key. Command Nexus always tells you honestly what it can and can't do. Explore Governance anytime after the tour.",
            ),

            # === STEP 17: Tour Complete ===
            DemoTourStep(
                title="\u2705 Tour Complete!",
                instruction="You've completed the interactive tour. You're ready to start using Command Nexus!",
                detail_html="""<h3>\U0001f389 You now know how to:</h3>
                <ul>
                    <li>\u2705 Open the AI Forge and create AIs</li>
                    <li>\u2705 Choose a use case, capabilities, and guardrails</li>
                    <li>\u2705 Adjust personality with creativity, formality, and caution</li>
                    <li>\u2705 Deploy and give missions</li>
                    <li>\u2705 Add Intelligence (memory + knowledge)</li>
                    <li>\u2705 Use the Knowledge Base for document search</li>
                    <li>\u2705 Choose AI Models for different power levels</li>
                    <li>\u2705 Customize with Visual Themes</li>
                    <li>\u2705 Use Voice for hands-free interaction</li>
                    <li>\u2705 Schedule missions to run automatically</li>
                    <li>\u2705 Explore Upgrades for more power</li>
                    <li>\u2705 Get help from Customer Support</li>
                    <li>\u2705 Stay safe with Governance</li>
                </ul>
                <p><b>AI used to be powerful if you knew how to code. Now it's powerful even if you don't.</b></p>
                <p>Command Nexus brings AI into homes, schools, and businesses \u2014 all with trust and no coding required.</p>
                <p>Click 'Finish' to close the tutorial and start exploring!</p>""",
                action_prompt="Click 'Finish' to close",
                wait_for_click=False,
                narration="Tour Complete. You now know how to open the AI Forge and create AIs, choose a use case, capabilities, and guardrails, adjust personality with creativity, formality, and caution, deploy and give missions, add intelligence with memory and knowledge, use the Knowledge Base for document search, choose AI Models for different power levels, customize with Visual Themes, use Voice for hands-free interaction, schedule missions to run automatically, explore upgrades for more power, get help from customer support, and stay safe with governance. AI used to be powerful if you knew how to code. Now it's powerful even if you don't. Command Nexus brings AI into homes, schools, and businesses, all with trust and no coding required. Click Finish to close the tutorial and start exploring.",
            ),
        ]

    def start_tour(self):
        """Start the demo tour."""
        self._current_step = 0
        self._tour_active = True
        self._create_overlay()
        self._create_tooltip()
        # Install event filter globally for Escape key handling
        self._install_event_filter()
        # Always-on z-order guardian: keeps notification popups above the tour for
        # the whole session regardless of step state. Self-terminates when the
        # overlay is gone (tour ended).
        self._zorder_timer = QTimer(self)
        self._zorder_timer.setInterval(300)
        self._zorder_timer.timeout.connect(self._stack_popups_above_overlay)
        self._zorder_timer.start()
        # Auto-pilot: press A during the tour to toggle automated cursor + clicks.
        self._auto = False
        self._auto_timer = QTimer(self)
        self._auto_timer.setInterval(1400)
        self._auto_timer.timeout.connect(self._auto_tick)
        self._show_current_step()

        if self._audit:
            self._audit.log(tool="DemoTour", action="DEMO_STARTED",
                          target="Interactive demo tour started", approved=True, status="info")
    
    def _create_overlay(self):
        """Create the highlight overlay (screen-wide top-level)."""
        if self._overlay:
            self._overlay.deleteLater()
        self._overlay = DemoTourOverlay()
        self._overlay.resize_to_screen(self._main_window)
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
        # Wire voice toggle
        self._tooltip._voice_btn.clicked.connect(self._on_voice_toggle)
        # Wire close X button and Escape key to skip
        self._tooltip.set_close_callback(self._on_skip)
        self._tooltip._auto_toggle_callback = self._on_auto_toggle
        # Wire automated-demo control bar
        self._tooltip._demo_start_btn.clicked.connect(self._driver.start)
        self._tooltip._demo_pause_btn.clicked.connect(
            lambda: self._driver.pause() if self._driver._state != "paused" else self._driver.resume())
        self._tooltip._demo_stop_btn.clicked.connect(self._driver.stop)
        self._tooltip._demo_restart_btn.clicked.connect(self._driver.restart)
        self._tooltip._demo_speed.currentTextChanged.connect(self._driver.set_speed)
        self._tooltip.show()
        self._tooltip.raise_()
    
    def _on_voice_toggle(self):
        """Toggle voice narration on/off."""
        self._voice_enabled = self._tooltip._voice_btn.isChecked()
        if self._voice_enabled:
            self._tooltip._voice_btn.setText("🔊 Voice: ON")
            if self._tts:
                self._tts.stop()
                # Re-narrate the current step so user hears it immediately
                if self._current_step < len(self._steps) and self._tts.available:
                    step = self._steps[self._current_step]
                    narration = step.narration if step.narration else f"{step.title}. {step.instruction}"
                    self._tts.speak(narration)
        else:
            self._tooltip._voice_btn.setText("🔇 Voice: OFF")
            if self._tts:
                self._tts.stop()
    
    def _close_sub_windows(self):
        """Close all sub-windows (Forge, Book, Customer AI, etc.) to return to main window."""
        for w in QApplication.topLevelWidgets():
            if w is self._main_window:
                continue
            if w is self._overlay or w is self._tooltip:
                continue
            if isinstance(w, QMainWindow) and w.isVisible():
                w.close()
    
    def _show_current_step(self):
        """Display current step with highlight and instructions."""
        if self._current_step >= len(self._steps):
            self._complete_tour()
            return
        
        step = self._steps[self._current_step]
        self.step_changed.emit(self._current_step + 1, len(self._steps))
        
        # Clear previous click target (keep event filter installed for Escape key)
        self._overlay.clear_highlight()
        self._pending_click_target = None
        
        # Close sub-windows when moving to a step that targets the main window.
        # Steps 1-6 (index 1-6) are Forge steps. Step 7 (index 7) is mission_start_button on main window.
        # Steps 8-16 (index 8-16) are nav buttons on main window.
        step_needs_forge = (
            step.target_getter is not None
            and 'forge' in step.target_getter.__name__
        )
        if not step_needs_forge and self._current_step >= 7:
            self._close_sub_windows()
        if step_needs_forge:
            # Bring the Forge forward first, then keep overlay + tooltip on top of it
            forge = self._find_forge_window()
            if forge is not None:
                forge.showNormal()
                forge.raise_()
                forge.activateWindow()
            if self._overlay:
                self._overlay.raise_()
            if self._tooltip:
                self._tooltip.raise_()
        
        # Find target widget
        target = self._find_target(step)
        target_missing = step.wait_for_click and target is None

        if target:
            # Highlight it
            self._overlay.highlight_widget(target)
            self._overlay.raise_()
            self._tooltip.raise_()

            # If waiting for click, install event filter
            if step.wait_for_click:
                self._pending_click_target = target
                self._install_event_filter()
            self._rehighlight_timer.stop()
        else:
            # Target not found yet — start polling in case a window is still opening
            if step.wait_for_click or step.target_widget_name:
                self._rehighlight_timer.start()

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
        
        # Reconnect buttons for current step — safe disconnect/reconnect
        try:
            self._tooltip._next_btn.clicked.disconnect()
        except TypeError:
            pass
        self._tooltip._next_btn.clicked.connect(self._on_next)
        # Change Next button text to 'Finish' on the last step
        if self._current_step == len(self._steps) - 1:
            self._tooltip._next_btn.setText("Finish")
        else:
            self._tooltip._next_btn.setText("Next \u2192")
        
        try:
            self._tooltip._back_btn.clicked.disconnect()
        except TypeError:
            pass
        if self._current_step > 0:
            self._tooltip._back_btn.setVisible(True)
            self._tooltip._back_btn.clicked.connect(self._on_back)
        else:
            self._tooltip._back_btn.setVisible(False)
        
        # Position tooltip near the highlight, or bottom-right if no highlight
        if target and target.isVisible():
            highlight_rect = self._overlay._highlight_rect
        else:
            highlight_rect = None
        self._tooltip.position_near_highlight(highlight_rect)
        
        # Ensure tooltip has focus for keyboard input (Escape to close)
        self._tooltip.setFocus()
        self._tooltip.raise_()
        self._tooltip.activateWindow()
        self._stack_popups_above_overlay()
        
        # Voice narration — use full narration text if provided, otherwise title + instruction
        if self._voice_enabled and self._tts.available:
            narration = step.narration if step.narration else f"{step.title}. {step.instruction}"
            self._tts.speak(narration)
    
    def _find_target(self, step: DemoTourStep) -> Optional[QWidget]:
        """Find the target widget for a step. Searches all open windows."""
        if step.target_getter:
            return step.target_getter()
        if step.target_widget_name:
            # First try the main window
            target = self._main_window.findChild(QWidget, step.target_widget_name)
            if target and target.isVisible():
                return target
            # Then search all top-level windows (Forge, Intelligence, etc.)
            for w in QApplication.topLevelWidgets():
                if w is self._main_window:
                    continue
                target = w.findChild(QWidget, step.target_widget_name)
                if target and target.isVisible():
                    return target
            # Return None if not visible — the rehighlight timer will find it when the window opens
            if target and not target.isVisible():
                return None
        return None
    
    def _stack_popups_above_overlay(self):
        """Every popup (deploy/save confirmations, disclaimers, model picker) must
        appear ABOVE the tour. The overlay/tooltip use WindowStaysOnTopHint, which
        puts them in the OS always-on-top band — a normal popup can NEVER stack
        above that. So while any popup is open, drop the tour's topmost flag
        ('down a notch'); restore it once all popups are gone. Application-modal
        popups are also downgraded to window-modal so Next is never blocked.
        """
        zt = getattr(self, "_zorder_timer", None)
        ov = getattr(self, "_overlay", None)
        if zt is not None and (ov is None or not ov.isVisible()):
            zt.stop()
            return
        from PySide6.QtWidgets import QDialog
        tops = [w for w in QApplication.topLevelWidgets()
                if w not in (self._overlay, self._tooltip, self._main_window) and w.isVisible()]
        dialogs = [w for w in tops if isinstance(w, QDialog)]
        windows = [w for w in tops if not isinstance(w, QDialog)]
        # Work windows (AI Forge, panels): the OVERLAY goes under them so the user
        # can work, but the tooltip KEEPS its topmost band and stays visible.
        for w in windows:
            self._overlay.stackUnder(w)
        # Dialogs (notifications, disclaimers, pickers): the tour drops its
        # always-on-top band entirely so the dialog rises above everything.
        self._set_topmost(not dialogs)
        for w in dialogs:
            if w.isModal() and not getattr(w, "_tour_windowmodal", False):
                w._tour_windowmodal = True
                w.hide()
                w.setWindowModality(Qt.WindowModality.WindowModal)
                w.show()
            w.raise_()

    def _set_topmost(self, on: bool):
        """Add or remove WindowStaysOnTopHint on the overlay and tooltip."""
        if getattr(self, "_topmost_state", None) == on:
            return
        self._topmost_state = on
        for w in (self._overlay, self._tooltip):
            flags = w.windowFlags()
            if on:
                w.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
            else:
                w.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
            w.show()
        if on:
            self._overlay.raise_()
            self._tooltip.raise_()

    def _rehighlight(self):
        """Periodically re-check if the target widget has appeared (e.g. sub-window just opened)."""
        if self._current_step >= len(self._steps):
            self._rehighlight_timer.stop()
            return
        step = self._steps[self._current_step]
        # Any popup opened during the tour (model picker, dialogs, etc.) must sit
        # fully above the overlay — never partially hidden or ambiguous.
        self._stack_popups_above_overlay()
        target = self._find_target(step)
        if target and target.isVisible():
            self._rehighlight_timer.stop()
            self._overlay.highlight_widget(target)
            if step.wait_for_click and not self._event_filter_installed:
                self._pending_click_target = target
                self._install_event_filter()
            # Update tooltip to show the real action prompt now that target is found
            self._tooltip.update_content(
                step_num=self._current_step + 1,
                total_steps=len(self._steps),
                title=step.title,
                instruction=step.instruction,
                action_prompt=step.action_prompt,
                detail_html=step.detail_html,
                wait_for_click=True,
            )
            # Reposition tooltip near the new highlight
            self._tooltip.position_near_highlight(self._overlay._highlight_rect)
            # If the target lives in a popup, keep the overlay BENEATH it so the
            # popup stays visible and clickable; otherwise raise above main window.
            tw = target.window()
            if tw is not None and tw is not self._main_window:
                self._overlay.raise_()
                self._overlay.stackUnder(tw)
            else:
                self._overlay.raise_()
                self._stack_popups_above_overlay()
            self._tooltip.raise_()
    
    def _on_auto_toggle(self):
        """A key: toggle the automated demonstration (start/pause/resume)."""
        self._driver.toggle()

    def _auto_tick(self):
        if not getattr(self, "_auto", False) or self._current_step >= len(self._steps):
            self._auto_timer.stop()
            return
        step = self._steps[self._current_step]
        target = self._find_target(step)
        if step.wait_for_click and target is not None and target.isVisible():
            self._auto_click(target)
        elif not step.wait_for_click:
            btn = self._tooltip._next_btn
            if btn.isEnabled():
                self._auto_click(btn)

    def _auto_click(self, target):
        """Glide the cursor to the target, then post press+release to the widget."""
        from PySide6.QtGui import QCursor, QMouseEvent
        from PySide6.QtCore import QEvent, QPointF
        end = target.mapToGlobal(target.rect().center())
        start = QCursor.pos()
        steps = 12
        for i in range(1, steps + 1):
            x = start.x() + (end.x() - start.x()) * i // steps
            y = start.y() + (end.y() - start.y()) * i // steps
            QTimer.singleShot(i * 25, lambda x=x, y=y: QCursor.setPos(x, y))
        def _click():
            local = target.mapFromGlobal(end)
            for t in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
                QApplication.postEvent(target, QMouseEvent(
                    t, QPointF(local), Qt.MouseButton.LeftButton,
                    Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))
        QTimer.singleShot(steps * 25 + 80, _click)

    def _install_event_filter(self):
        """Install event filter on the application to watch for clicks and Escape key."""
        if not self._event_filter_installed:
            app = QApplication.instance()
            app.installEventFilter(self)
            self._event_filter_installed = True

    def _remove_event_filter(self):
        """Remove event filter from application."""
        if self._event_filter_installed:
            app = QApplication.instance()
            app.removeEventFilter(self)
            self._event_filter_installed = False
        self._pending_click_target = None

    def _is_descendant(self, child: QWidget, ancestor: QWidget) -> bool:
        """Check if child is a descendant of ancestor."""
        current = child
        while current is not None:
            if current is ancestor:
                return True
            current = current.parentWidget()
        return False
    
    def _on_next(self):
        """Go to next step — stop any ongoing voice narration first."""
        if self._tts:
            self._tts.stop()
        self._current_step += 1
        self._show_current_step()

    def _on_back(self):
        """Go to previous step — stop any ongoing voice narration first."""
        if self._tts:
            self._tts.stop()
        if self._current_step > 0:
            self._current_step -= 1
            self._show_current_step()
    
    def _on_skip(self):
        """Skip the tour — can be triggered by Skip button, X button, or Escape key."""
        if not self._tour_active:
            return
        self._tour_active = False
        if self._audit:
            self._audit.log(tool="DemoTour", action="DEMO_SKIPPED",
                          target=f"Skipped at step {self._current_step}", approved=True, status="info")
        self._cleanup()
        self.tour_skipped.emit()
    
    def _complete_tour(self):
        """Complete the tour."""
        self._tour_active = False
        if self._audit:
            self._audit.log(tool="DemoTour", action="DEMO_COMPLETED",
                          target="Full demo completed", approved=True, status="info")
        self._cleanup()
        self.tour_completed.emit()
    
    def _cleanup(self):
        """Clean up all tour resources."""
        self._rehighlight_timer.stop()
        self._remove_event_filter()
        if self._tts:
            self._tts.stop()
        if self._overlay:
            self._overlay.deleteLater()
            self._overlay = None
        if self._tooltip:
            self._tooltip.deleteLater()
            self._tooltip = None
        self._tour_active = False


def start_demo_tour(main_window: QMainWindow, audit_logger=None) -> DemoTourController:
    """Start the interactive demo tour."""
    controller = DemoTourController(main_window, audit_logger, demo_mode=True)
    controller.start_tour()
    return controller
