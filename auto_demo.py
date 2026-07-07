# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0

"""
Command Nexus™ — Automated Demo Script
=======================================
Launches Command Nexus and auto-drives through all 5 parts with on-screen
narration overlays. Designed for screen recording with OBS.

Usage:
    python auto_demo.py

Requirements:
    - Command Nexus must be runnable (pip install -r requirements.txt)
    - OBS or similar screen recorder running at 1080p+ 60fps
    - A license must be activated OR select "Demo Mode" in the license dialog

Before running:
    - Delete ~/.command_nexus/first_run_complete to reset the tour, OR
    - Just skip the first-run tour when it appears (click "No")
    - The automated demo will start 2 seconds after the main window loads

The demo takes approximately 4-5 minutes to complete.
Press Ctrl+C in the terminal to stop early.
"""

import sys
import math
import time
from pathlib import Path

# Ensure src is on path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QPoint, QRect, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGraphicsDropShadowEffect, QTextEdit, QListWidget, QCheckBox,
    QProgressBar, QSizePolicy, QMainWindow, QComboBox, QLineEdit, QSlider,
    QTextEdit as QTE,
)
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPainterPath


# ─── Narration Overlay ────────────────────────────────────────────────

class NarrationOverlay(QWidget):
    """
    Bottom-of-screen narration banner that shows what's happening during the demo.
    Semi-transparent dark bar with large readable text.
    """

    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._text = ""
        self._subtitle = ""
        self._fade = 0.0
        self._target_fade = 0.0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(16)

        # Position at bottom of primary screen
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(0, screen.height() - 140, screen.width(), 140)

    def show_text(self, text: str, subtitle: str = ""):
        self._text = text
        self._subtitle = subtitle
        self._target_fade = 1.0
        self.show()
        self.raise_()

    def hide_text(self):
        self._target_fade = 0.0

    def _animate(self):
        # Smooth fade
        diff = self._target_fade - self._fade
        if abs(diff) > 0.01:
            self._fade += diff * 0.12
        elif self._target_fade == 0.0 and self._fade < 0.05:
            self._fade = 0.0
        self.update()

    def paintEvent(self, event):
        if self._fade < 0.01:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Background bar
        bg_alpha = int(220 * self._fade)
        painter.fillRect(0, 0, w, h, QColor(13, 17, 23, bg_alpha))

        # Top accent line
        accent_alpha = int(255 * self._fade)
        painter.fillRect(0, 0, w, 3, QColor(35, 134, 54, accent_alpha))

        # Main text
        font = QFont("Segoe UI", 18, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255, accent_alpha))
        painter.drawText(QRect(40, 20, w - 80, 50), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._text)

        # Subtitle
        if self._subtitle:
            font2 = QFont("Segoe UI", 12)
            painter.setFont(font2)
            painter.setPen(QColor(139, 148, 158, accent_alpha))
            painter.drawText(QRect(40, 70, w - 80, 40), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._subtitle)

        painter.end()


# ─── Highlight Overlay ────────────────────────────────────────────────

class HighlightOverlay(QWidget):
    """
    Screen-wide overlay that highlights a widget with an animated border.
    """

    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._target_widget = None
        self._highlight_rect = None
        self._pulse = 0.0
        self._padding = 16

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(16)

        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

    def highlight(self, widget, padding=16):
        if widget and widget.isVisible():
            self._target_widget = widget
            self._padding = padding
            self.show()
            self.raise_()
        else:
            self.clear()

    def clear(self):
        self._target_widget = None
        self._highlight_rect = None
        self.hide()

    def _animate(self):
        self._pulse += 0.05
        if self._pulse > 6.28:
            self._pulse = 0.0
        if self._target_widget:
            try:
                if not self._target_widget.isVisible():
                    self.clear()
                    return
                tl = self._target_widget.mapToGlobal(QPoint(0, 0))
                origin = self.geometry().topLeft()
                x = tl.x() - origin.x() - self._padding
                y = tl.y() - origin.y() - self._padding
                w = self._target_widget.width() + self._padding * 2
                h = self._target_widget.height() + self._padding * 2
                self._highlight_rect = QRect(x, y, w, h)
            except RuntimeError:
                self.clear()
                return
        self.update()

    def paintEvent(self, event):
        if not self._highlight_rect:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dim everything outside the highlight
        painter.fillRect(self.rect(), QColor(0, 0, 0, 80))

        # Cut out the highlight area
        path = QPainterPath()
        path.addRect(self.rect().x(), self.rect().y(), self.rect().width(), self.rect().height())
        path.addRoundedRect(self._highlight_rect.x(), self._highlight_rect.y(),
                           self._highlight_rect.width(), self._highlight_rect.height(), 8, 8)
        painter.fillPath(path, QColor(0, 0, 0, 0))

        # Animated border
        pulse_alpha = int(180 + 75 * (0.5 + 0.5 * math.sin(self._pulse)))
        pen = QPen(QColor(35, 134, 54, pulse_alpha), 3)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(self._highlight_rect, 8, 8)

        painter.end()


# ─── Demo Controller ──────────────────────────────────────────────────

class AutoDemoController(QObject):
    """
    Orchestrates the automated demo by scheduling timed actions.
    """

    def __init__(self, app: CommandNexusApp):
        super().__init__()
        self._app = app
        self._narration = NarrationOverlay()
        self._highlight = HighlightOverlay()
        self._step = 0
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._next_step)

    def start(self):
        self._narration.show()
        self._narration.raise_()
        self._next_step()

    def _schedule_next(self, delay_ms: int):
        self._timer.start(delay_ms)

    def _narrate(self, text: str, subtitle: str = "", duration_ms: int = 3000):
        self._narration.show_text(text, subtitle)
        self._schedule_next(duration_ms)

    def _highlight_widget(self, widget, duration_ms: int = 2000):
        self._highlight.highlight(widget)
        self._schedule_next(duration_ms)

    def _clear_highlight_and_narrate(self, text: str, subtitle: str = "", duration_ms: int = 3000):
        self._highlight.clear()
        self._narrate(text, subtitle, duration_ms)

    def _click_button_by_text(self, parent_widget, text: str) -> bool:
        """Find and click a QPushButton by its text."""
        if not parent_widget:
            return False
        for child in parent_widget.findChildren(QPushButton):
            if child.text() == text and child.isEnabled():
                child.click()
                return True
        return False

    def _find_button(self, parent_widget, text: str):
        """Find a QPushButton by text, return it or None."""
        if not parent_widget:
            return None
        for child in parent_widget.findChildren(QPushButton):
            if child.text() == text:
                return child
        return None

    def _next_step(self):
        steps = [
            self._step_0_intro,
            self._step_1_forge_open,
            self._step_2_forge_name,
            self._step_3_forge_usecase,
            self._step_4_forge_capabilities,
            self._step_5_forge_personality,
            self._step_6_forge_save,
            self._step_7_forge_deploy,
            self._step_8_book_open,
            self._step_9_book_keeper,
            self._step_10_visibility_mission,
            self._step_11_visibility_start,
            self._step_12_visibility_audit,
            self._step_13_upgrades_open,
            self._step_14_upgrades_show,
            self._step_15_watcher,
            self._step_16_avatar,
            self._step_17_pricing,
            self._step_18_close,
        ]

        if self._step < len(steps):
            steps[self._step]()
            self._step += 1
        else:
            self._narration.hide_text()
            self._highlight.clear()
            self._timer.stop()

    # ─── Step 0: Intro ────────────────────────────────────────────────
    def _step_0_intro(self):
        vis = self._app._visibility
        if vis:
            vis.show()
            vis.raise_()
        self._narrate(
            "Command Nexus™ — Command Your AI Army",
            "The desktop mission control for building, governing, and deploying AI agents. Runs on your machine. No cloud required.",
            4000
        )

    # ─── Step 1: Open Forge ───────────────────────────────────────────
    def _step_1_forge_open(self):
        vis = self._app._visibility
        nav = vis._nav if vis else None
        forge_btn = self._find_button(nav, "AI Forge") if nav else None
        if forge_btn:
            self._highlight.highlight(forge_btn)
            self._narrate(
                "Part 1: AI Forge — The Builder",
                "Build custom AI agents with a character sheet. No code required.",
                3000
            )
            QTimer.singleShot(1500, forge_btn.click)
        else:
            self._narrate("Opening AI Forge...", "", 2000)
            self._app._open_forge()
        self._schedule_next(3500)

    # ─── Step 2: Fill AI Name ─────────────────────────────────────────
    def _step_2_forge_name(self):
        forge = self._app._forge
        if forge and forge._sheet:
            name_input = forge._sheet._name_input
            self._highlight.highlight(name_input)
            self._narrate(
                "Name your AI",
                "Give it a name. This is your agent — you own it.",
                2500
            )
            QTimer.singleShot(1000, lambda: name_input.setText("Scout"))
        else:
            self._narrate("Setting AI name...", "", 2000)
        self._schedule_next(3000)

    # ─── Step 3: Select Use Case ──────────────────────────────────────
    def _step_3_forge_usecase(self):
        forge = self._app._forge
        if forge and forge._sheet:
            uc_combo = forge._sheet._uc_combo
            self._highlight.highlight(uc_combo)
            self._narrate(
                "Choose a use-case class",
                "7 classes available: Individual, Educational, Task-Ready, Business, Enterprise, All-Rounder, Military/Gov.",
                3000
            )
            QTimer.singleShot(1200, lambda: uc_combo.setCurrentText("Task-Ready"))
        else:
            self._narrate("Selecting use case...", "", 2000)
        self._schedule_next(3500)

    # ─── Step 4: Select Capabilities ──────────────────────────────────
    def _step_4_forge_capabilities(self):
        forge = self._app._forge
        if forge and forge._sheet:
            suggest_btn = forge._sheet._suggest_caps_btn
            self._highlight.highlight(suggest_btn)
            self._narrate(
                "Auto-select recommended capabilities",
                "24 capability modules across 12 categories. Or pick them individually.",
                3000
            )
            QTimer.singleShot(1200, suggest_btn.click)
        else:
            self._narrate("Selecting capabilities...", "", 2000)
        self._schedule_next(3500)

    # ─── Step 5: Adjust Personality ───────────────────────────────────
    def _step_5_forge_personality(self):
        forge = self._app._forge
        if forge and forge._sheet:
            creativity = forge._sheet._creativity
            self._highlight.highlight(creativity)
            self._narrate(
                "Dial in the personality",
                "Creativity, formality, and caution sliders. Your AI, your tuning.",
                3000
            )
            QTimer.singleShot(1000, lambda: creativity.setValue(75))
            QTimer.singleShot(2000, lambda: forge._sheet._caution.setValue(60))
        else:
            self._narrate("Adjusting personality...", "", 2000)
        self._schedule_next(3500)

    # ─── Step 6: Save AI ──────────────────────────────────────────────
    def _step_6_forge_save(self):
        forge = self._app._forge
        if forge and forge._sheet:
            save_btn = forge._sheet._btn_save
            self._highlight.highlight(save_btn)
            self._narrate(
                "Save AI to Forge",
                "Your AI is saved as portable JSON. Build it, share it, sell it — it's yours.",
                3000
            )
            QTimer.singleShot(1500, save_btn.click)
        else:
            self._narrate("Saving AI...", "", 2000)
        self._schedule_next(4000)

    # ─── Step 7: Deploy to Command Center ─────────────────────────────
    def _step_7_forge_deploy(self):
        forge = self._app._forge
        if forge:
            deploy_btn = self._find_button(forge, "Deploy to Command Center")
            if deploy_btn:
                self._highlight.highlight(deploy_btn)
                self._narrate(
                    "Deploy to Command Center",
                    "One click sends your AI to the Visibility Window for mission assignment.",
                    3000
                )
                QTimer.singleShot(1500, deploy_btn.click)
            else:
                self._narrate("Deploying to Command Center...", "", 2000)
        else:
            self._narrate("Deploying...", "", 2000)
        self._schedule_next(4000)

    # ─── Step 8: Open Book ────────────────────────────────────────────
    def _step_8_book_open(self):
        forge = self._app._forge
        if forge:
            book_btn = self._find_button(forge, "Open Knowledge for AI")
            if book_btn:
                self._highlight.highlight(book_btn)
                self._narrate(
                    "Part 2: The Book — The AI's Memory",
                    "Each AI gets its own knowledge compendium. Not a shared brain — a private memory you author.",
                    3000
                )
                QTimer.singleShot(1500, book_btn.click)
            else:
                self._narrate("Opening Knowledge...", "", 2000)
                self._app._open_book()
        else:
            self._app._open_book()
            self._narrate("Opening Knowledge...", "", 2000)
        self._schedule_next(4000)

    # ─── Step 9: Book Keeper ──────────────────────────────────────────
    def _step_9_book_keeper(self):
        book = self._app._book
        if book:
            keeper_btn = self._find_button(book, "Talk to Knowledge Guide")
            if keeper_btn:
                self._highlight.highlight(keeper_btn)
                self._narrate(
                    "Talk to the Knowledge Guide",
                    "Answer 7 questions in plain English. The Guide writes the governance document for you.",
                    3500
                )
                # Don't auto-click — just show it. The dialog is interactive.
            else:
                self._narrate(
                    "The Book — per-AI knowledge compendium",
                    "Tree-structured: Parts → Chapters → Sections. Rollback safety on every change.",
                    3000
                )
        else:
            self._narrate("Knowledge system...", "", 2000)
        self._schedule_next(4000)

    # ─── Step 10: Visibility — Mission Input ──────────────────────────
    def _step_10_visibility_mission(self):
        vis = self._app._visibility
        if vis:
            vis.show()
            vis.raise_()
            task_input = vis._task_input
            self._highlight.highlight(task_input)
            self._narrate(
                "Part 3: Visibility Window — The Command Center",
                "Live viewport, audit panes, mission control. See what your AI sees.",
                3000
            )
            QTimer.singleShot(1500, lambda: task_input.setText("Research the top 5 Python web frameworks and summarize their pros and cons"))
        else:
            self._narrate("Command Center...", "", 2000)
        self._schedule_next(4000)

    # ─── Step 11: Start Mission ───────────────────────────────────────
    def _step_11_visibility_start(self):
        vis = self._app._visibility
        if vis:
            start_btn = vis._btn_start
            self._highlight.highlight(start_btn)
            self._narrate(
                "START — Dispatch your AI on a mission",
                "Approval gates handle safety. You approve every risky move.",
                3000
            )
            QTimer.singleShot(2000, start_btn.click)
        else:
            self._narrate("Starting mission...", "", 2000)
        self._schedule_next(5000)

    # ─── Step 12: Audit Panes ─────────────────────────────────────────
    def _step_12_visibility_audit(self):
        vis = self._app._visibility
        if vis:
            # Highlight the thought pane
            thought = getattr(vis, '_thought_pane', None)
            if thought:
                self._highlight.highlight(thought)
            self._narrate(
                "Real-time audit panes: Thought, Action, Trajectory",
                "You see what your AI is thinking, doing, and planning — in real time. You're still the general.",
                4000
            )
        else:
            self._narrate("Audit panes...", "", 2000)
        self._schedule_next(4500)

    # ─── Step 13: Open Upgrades ───────────────────────────────────────
    def _step_13_upgrades_open(self):
        vis = self._app._visibility
        nav = vis._nav if vis else None
        upgrades_btn = self._find_button(nav, "Upgrades") if nav else None
        if upgrades_btn:
            self._highlight.highlight(upgrades_btn)
            self._narrate(
                "Part 4: Upgrades — Capability System",
                "24 capability modules. 3 tiers each. One system resource bar prevents overload.",
                3000
            )
            QTimer.singleShot(1500, upgrades_btn.click)
        else:
            self._narrate("Opening Upgrades...", "", 2000)
        self._schedule_next(4000)

    # ─── Step 14: Show Upgrades Detail ────────────────────────────────
    def _step_14_upgrades_show(self):
        self._highlight.clear()
        self._narrate(
            "24 skills. 3 power levels. One resource bar. No surprises.",
            "Green = fine. Yellow = heavy load. Crimson red = auto-block. Your machine won't choke.",
            4000
        )
        self._schedule_next(4500)

    # ─── Step 15: Watcher ─────────────────────────────────────────────
    def _step_15_watcher(self):
        vis = self._app._visibility
        if vis:
            watcher_label = getattr(vis, '_watcher_trust_label', None)
            if watcher_label:
                self._highlight.highlight(watcher_label)
        self._narrate(
            "Part 5: The Watcher — Background Defense",
            "Always-on. No UI. No pause button. SHA-256 file integrity scans every 5 seconds. While you sleep, it watches.",
            4000
        )
        self._schedule_next(4500)

    # ─── Step 16: Avatar ──────────────────────────────────────────────
    def _step_16_avatar(self):
        self._highlight.clear()
        self._narrate(
            "Your AI Has a Face",
            "3D animated avatar — idle, listening, thinking, talking. It's not a chatbot. It's a presence.",
            4000
        )
        self._schedule_next(4500)

    # ─── Step 17: Pricing ─────────────────────────────────────────────
    def _step_17_pricing(self):
        self._narrate(
            "Try it for $10 — one-time, 15 days, every capability unlocked.",
            "Paid tiers from $20/mo. Annual plan: $50/year for 5 AIs. Unlimited: $80/mo.",
            5000
        )
        self._schedule_next(5500)

    # ─── Step 18: Close ───────────────────────────────────────────────
    def _step_18_close(self):
        self._narrate(
            "Other platforms let you USE AI. Command Nexus lets you COMMAND it.",
            "Download today. Build your army. Avery Logic Works™.",
            5000
        )
        self._schedule_next(6000)


# ─── Main Entry Point ─────────────────────────────────────────────────

def main():
    # We need to import and run Command Nexus, then hook in our demo controller
    from src.main import CommandNexusApp

    app = CommandNexusApp()

    # Wait for the main window to be fully shown, then start the demo
    def start_demo():
        demo = AutoDemoController(app)
        demo.start()

    # Delay demo start to let license dialogs / first-run dialogs clear
    QTimer.singleShot(2000, start_demo)

    app.run()


if __name__ == "__main__":
    main()
