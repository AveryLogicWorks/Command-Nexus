# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""Command Nexus Theme Engine."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json

@dataclass
class Theme:
    id: str; name: str; cat: str
    bg1: str; bg2: str; bg3: str; bd: str
    t1: str; t2: str; ac: str; ac2: str
    ok: str; wn: str; er: str; bb: str; bt: str

THEMES = [
    Theme("midnight","Midnight","Dark","#0d1117","#161b22","#21262d","#30363d","#c9d1d9","#8b949e","#58a6ff","#1f6feb","#3fb950","#d29922","#f85149","#21262d","#c9d1d9"),
    Theme("deep_ocean","Deep Ocean","Dark","#0a1929","#112240","#1d3557","#233554","#ccd6f6","#8892b0","#64ffda","#0d7377","#3fb950","#e6c07b","#ef476f","#1d3557","#ccd6f6"),
    Theme("matrix","Matrix","Dark","#000","#0a0a0a","#111","#030","#0f0","#080","#0f0","#0c0","#0f0","#cf0","#f00","#011","#0f0"),
    Theme("cyberpunk","Cyberpunk","Dark","#0d0221","#1a0b2e","#241734","#3b1c5a","#f0f0f0","#a0a0b0","#ff006e","#d62aad","#06ffa5","#ffbe0b","#ff006e","#2d1b4e","#f0f0f0"),
    Theme("void","Void","Dark","#000","#0d0d0d","#1a1a1a","#2a2a2a","#e0e0e0","#707070","#9d4edd","#7b2cbf","#06ffa5","#ffd60a","#ff006e","#1a1a1a","#e0e0e0"),
    Theme("clean_slate","Clean Slate","Light","#fff","#f6f8fa","#e1e4e8","#d0d7de","#1f2328","#656d76","#0969da","#218bff","#1a7f37","#9a6700","#cf222e","#f6f8fa","#1f2328"),
    Theme("paper","Paper","Light","#fdf6e3","#eee8d5","#e0dcc8","#d0c8b0","#3b3b3b","#8a8a8a","#268bd2","#1e6bb8","#2aa198","#b58900","#dc322f","#eee8d5","#3b3b3b"),
    Theme("cloud","Cloud","Light","#f0f4f8","#e6edf3","#dbe6f0","#c8d3e0","#2d3748","#718096","#3182ce","#2c5282","#38a169","#d69e2e","#e53e3e","#dbe6f0","#2d3748"),
    Theme("minimalist","Minimalist","Light","#fafafa","#f5f5f5","#eee","#e0e0e0","#212121","#9e9e9e","#424242","#616161","#4caf50","#ff9800","#f44336","#eee","#212121"),
    Theme("sunset","Sunset","Color","#1a0a2e","#2d1b4e","#3d2b5e","#4a3b6e","#f0e6ff","#b8a9c9","#ff6b6b","#ee5a52","#feca57","#ff9f43","#ee5a52","#3d2b5e","#f0e6ff"),
    Theme("ocean_breeze","Ocean Breeze","Color","#001220","#002438","#003656","#005580","#e0f0ff","#80b0d0","#00b4d8","#0096c7","#06ffa5","#ffd60a","#ff006e","#003656","#e0f0ff"),
    Theme("forest","Forest","Color","#0f1f0f","#1a2e1a","#243524","#2d4a2d","#c8e6c9","#81c784","#4caf50","#388e3c","#66bb6a","#fdd835","#e53935","#243524","#c8e6c9"),
    Theme("aurora","Aurora","Color","#0d0d2b","#1a1a3e","#252550","#3a3a6e","#e0e0ff","#9090c0","#7c3aed","#6d28d9","#10b981","#f59e0b","#ef4444","#252550","#e0e0ff"),
    Theme("galaxy","Galaxy","Color","#0b0d17","#131628","#1c2035","#2a2f4a","#d0d4e8","#7780a0","#8b5cf6","#7c3aed","#06ffa5","#fbbf24","#f87171","#1c2035","#d0d4e8"),
    Theme("corporate","Corporate","Professional","#f5f5f5","#e8e8e8","#d6d6d6","#b0b0b0","#1a1a1a","#666","#0055a5","#003d7a","#2e7d32","#e65100","#c62828","#d6d6d6","#1a1a1a"),
    Theme("medical","Medical","Professional","#f8f9fa","#e9ecef","#dee2e6","#ced4da","#212529","#6c757d","#0d6efd","#0b5ed7","#198754","#fd7e14","#dc3545","#dee2e6","#212529"),
    Theme("legal","Legal","Professional","#faf8f0","#f0ede0","#e6e2d0","#d0cbb8","#2d2d2d","#807d70","#8b6914","#6b5210","#556b2f","#b8860b","#8b0000","#e6e2d0","#2d2d2d"),
    Theme("financial","Financial","Professional","#0f1e0f","#1a2e1a","#243524","#2d4a2d","#d4e8d4","#8ab88a","#2e7d32","#1b5e20","#66bb6a","#fdd835","#c62828","#243524","#d4e8d4"),
    Theme("retro_80s","Retro 80s","Fun","#1a0033","#2d0052","#3d0072","#5200a0","#ff00ff","#aa00ff","#00ffff","#00cccc","#ff00aa","#ffaa00","#ff0055","#3d0072","#ff00ff"),
    Theme("steampunk","Steampunk","Fun","#1a1008","#2d1f0f","#3d2a15","#4a3a1f","#d4a05a","#a08040","#c08838","#a06828","#8b6914","#daa520","#8b4513","#3d2a15","#d4a05a"),
    Theme("space","Space","Fun","#000010","#000020","#000030","#000040","#c0c0ff","#8080a0","#4040ff","#2020cc","#00ff80","#ffd700","#ff4040","#000030","#c0c0ff"),
    Theme("nature","Nature","Fun","#1a2e1a","#243524","#2d4a2d","#3a5a3a","#d0e8d0","#80a080","#4a8b4a","#2e6b2e","#6abf6a","#d4a840","#c04040","#2d4a2d","#d0e8d0"),
]

_TF = Path.home() / ".command_nexus" / "theme.json"

def get_theme(tid: str) -> Theme | None:
    for t in THEMES:
        if t.id == tid:
            return t
    return None

def get_default() -> Theme:
    return THEMES[0]

def by_cat(cat: str) -> list[Theme]:
    return [t for t in THEMES if t.cat == cat]

def generate_qss(t: Theme) -> str:
    return f"""
    QMainWindow, QDialog, QWidget {{
        background-color: {t.bg1}; color: {t.t1};
    }}
    QLabel {{ color: {t.t1}; }}
    QGroupBox {{
        border: 1px solid {t.bd}; border-radius: 6px;
        margin-top: 10px; padding-top: 10px; font-weight: bold; color: {t.t1};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin; left: 10px; padding: 0 5px; color: {t.ac};
    }}
    QPushButton {{
        background-color: {t.bb}; border: 1px solid {t.bd};
        border-radius: 6px; padding: 6px 12px; color: {t.bt};
    }}
    QPushButton:hover {{ border-color: {t.ac}; background-color: {t.bg3}; }}
    QPushButton:pressed {{ background-color: {t.ac2}; }}
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        background-color: {t.bg3}; border: 1px solid {t.bd};
        border-radius: 6px; padding: 6px; color: {t.t1};
    }}
    QLineEdit:focus, QTextEdit:focus {{ border-color: {t.ac}; }}
    QListWidget, QTreeWidget, QTableWidget {{
        background-color: {t.bg2}; border: 1px solid {t.bd};
        border-radius: 6px; color: {t.t1};
    }}
    QListWidget::item {{ padding: 6px; border-bottom: 1px solid {t.bg3}; }}
    QListWidget::item:selected {{ background-color: {t.ac}; color: {t.bg1}; }}
    QScrollBar:vertical {{ background: {t.bg2}; width: 10px; border: none; }}
    QScrollBar::handle:vertical {{
        background: {t.bd}; border-radius: 5px; min-height: 20px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {t.ac}; }}
    QTabWidget::pane {{ border: 1px solid {t.bd}; }}
    QTabBar::tab {{
        background: {t.bg2}; color: {t.t2};
        padding: 6px 16px; border: 1px solid {t.bd}; border-bottom: none;
        border-top-left-radius: 4px; border-top-right-radius: 4px;
    }}
    QTabBar::tab:selected {{ background: {t.bg1}; color: {t.ac}; }}
    QProgressBar {{
        border: 1px solid {t.bd}; border-radius: 4px;
        text-align: center; background: {t.bg3}; color: {t.t1};
    }}
    QProgressBar::chunk {{ background-color: {t.ac}; border-radius: 3px; }}
    QCheckBox, QRadioButton {{ color: {t.t1}; }}
    QCheckBox::indicator, QRadioButton::indicator {{
        border: 1px solid {t.bd}; border-radius: 3px; background: {t.bg3};
    }}
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
        background: {t.ac}; border-color: {t.ac};
    }}
    QMenu {{ background-color: {t.bg2}; border: 1px solid {t.bd}; color: {t.t1}; }}
    QMenu::item:selected {{ background-color: {t.ac}; color: {t.bg1}; }}
    QStatusBar {{ background-color: {t.bg2}; color: {t.t2}; }}
    QToolBar {{ background-color: {t.bg2}; border-bottom: 1px solid {t.bd}; }}
    QSplitter::handle {{ background-color: {t.bd}; }}
    QFrame {{ color: {t.t1}; }}
    """

def save_theme(tid: str) -> None:
    try:
        _TF.parent.mkdir(parents=True, exist_ok=True)
        _TF.write_text(json.dumps({"theme": tid}), encoding="utf-8")
    except Exception:
        pass

def load_theme_id() -> str:
    try:
        if _TF.exists():
            data = json.loads(_TF.read_text(encoding="utf-8"))
            tid = data.get("theme", "midnight")
            if get_theme(tid):
                return tid
    except Exception:
        pass
    return "midnight"
