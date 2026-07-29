# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""Theme selector dialog for Command Nexus."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QGroupBox, QFrame, QScrollArea, QWidget,
)
from PySide6.QtCore import Qt
from src.core.theme_manager import (
    THEMES, get_theme, generate_qss, save_theme, load_theme_id, by_cat
)


class ThemeSelectorDialog(QDialog):
    def __init__(self, app_ref=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Command Nexus — Visual Themes")
        self.resize(800, 600)
        self._app = app_ref
        self._current_id = load_theme_id()
        layout = QVBoxLayout(self)
        header = QLabel("Visual Themes Pack")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #58a6ff; padding: 4px;")
        layout.addWidget(header)
        sub = QLabel(f"{len(THEMES)} themes available. Select a theme to apply it instantly.")
        sub.setStyleSheet("font-size: 12px; color: #8b949e; padding: 2px;")
        layout.addWidget(sub)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        for cat in ["Dark", "Light", "Color", "Professional", "Fun"]:
            cat_themes = by_cat(cat)
            if not cat_themes:
                continue
            cat_label = QLabel(f"  {cat} Themes")
            cat_label.setStyleSheet(
                "font-size: 14px; font-weight: bold; color: #f0883e; "
                "padding: 6px 4px 2px; border-bottom: 1px solid #30363d;"
            )
            content_layout.addWidget(cat_label)
            for t in cat_themes:
                content_layout.addWidget(self._build_theme_card(t))
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def _build_theme_card(self, t) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background-color: {t.bg2}; border: 1px solid {t.bd}; "
            f"border-radius: 6px; padding: 6px; margin: 2px; }}"
        )
        cl = QVBoxLayout(card)
        top = QHBoxLayout()
        name = QLabel(t.name)
        name.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {t.t1};")
        top.addWidget(name)
        top.addStretch()
        is_current = t.id == self._current_id
        if is_current:
            tag = QLabel("ACTIVE")
            tag.setStyleSheet(
                f"background-color: {t.ok}; color: {t.bg1}; font-size: 10px; "
                f"font-weight: bold; padding: 2px 8px; border-radius: 3px;"
            )
            top.addWidget(tag)
        else:
            btn = QPushButton("Apply")
            btn.setStyleSheet(
                f"background-color: {t.ac}; color: {t.bg1}; font-weight: bold; "
                f"padding: 4px 16px; border-radius: 4px; border: none;"
            )
            btn.clicked.connect(lambda checked, tid=t.id: self._apply(tid))
            top.addWidget(btn)
        cl.addLayout(top)
        preview = QHBoxLayout()
        for label, color in [("BG", t.bg1), ("Panel", t.bg2), ("Input", t.bg3), ("Accent", t.ac), ("Text", t.t1)]:
            sw = QLabel(f" {label} ")
            sw.setStyleSheet(
                f"background-color: {color}; color: {t.t1}; "
                f"padding: 4px 8px; border-radius: 3px; font-size: 10px;"
            )
            preview.addWidget(sw)
        preview.addStretch()
        cl.addLayout(preview)
        return card

    def _apply(self, tid: str):
        t = get_theme(tid)
        if not t:
            return
        save_theme(tid)
        if self._app:
            self._app.setStyleSheet(generate_qss(t))
        self._current_id = tid
        self.accept()
        dlg = ThemeSelectorDialog(self._app, self.parent())
        dlg.exec()
