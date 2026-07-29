# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

import psutil
import platform

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QGroupBox, QFormLayout, QProgressBar,
    QSplitter, QListWidget, QListWidgetItem, QMessageBox, QDialog,
    QDialogButtonBox, QGridLayout, QFrame, QScrollArea
)

from .constraints_models import (
    CapabilityModule, UpgradeTier, ResourceGrade as ModelResourceGrade, SystemSnapshot as ModelSnapshot
)
from ...core.obfuscation_manager import get_obfuscation_manager
from ...core.resource_gate import get_resource_gate, GateDecision, ResourceGrade as GateGrade


class ResourceGradeBar(QFrame):
    """Visual grade indicator from green to crimson red."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(24)
        self.setMaximumHeight(24)
        self._grade = ModelResourceGrade.GREEN
        self._pct = 0.0
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("background-color: #4caf50; border-radius: 4px;")

    def set_grade(self, grade: ModelResourceGrade, pct: float):
        self._grade = grade
        self._pct = pct
        colors = {
            ModelResourceGrade.GREEN: "#4caf50",
            ModelResourceGrade.GREEN_YELLOW: "#cddc39",
            ModelResourceGrade.YELLOW: "#ffeb3b",
            ModelResourceGrade.YELLOW_RED: "#ff9800",
            ModelResourceGrade.RED: "#f44336",
            ModelResourceGrade.CRIMSON_RED: "#b71c1c",
        }
        self.setStyleSheet(
            f"background-color: {colors.get(grade, '#4caf50')}; border-radius: 4px;"
        )
        self.setToolTip(f"Load: {pct:.1%} | Grade: {grade.value}")


class SystemMonitorWidget(QGroupBox):
    """Live system resource display."""

    def __init__(self, parent=None):
        super().__init__("System Resources", parent)
        self._setup_ui()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(2000)

    def _setup_ui(self):
        layout = QFormLayout(self)
        self._ram_label = QLabel("--")
        self._cpu_label = QLabel("--")
        self._disk_label = QLabel("--")
        self._os_label = QLabel(platform.system())
        layout.addRow("RAM:", self._ram_label)
        layout.addRow("CPU:", self._cpu_label)
        layout.addRow("Disk:", self._disk_label)
        layout.addRow("OS:", self._os_label)

    def _refresh(self):
        mem = psutil.virtual_memory()
        self._ram_label.setText(f"{mem.available // (1024*1024)} / {mem.total // (1024*1024)} MB free ({mem.percent}% used)")
        self._cpu_label.setText(f"{psutil.cpu_count()} cores | {psutil.cpu_percent():.1f}% current")
        self._disk_label.setText(f"{psutil.disk_usage('/').free // (1024*1024)} MB free")

    def get_snapshot(self) -> ModelSnapshot:
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        return ModelSnapshot(
            total_ram_mb=mem.total // (1024*1024),
            available_ram_mb=mem.available // (1024*1024),
            total_vram_mb=0,  # Placeholder — GPU detection is platform-dependent
            available_vram_mb=0,
            cpu_count=psutil.cpu_count(),
            cpu_percent=psutil.cpu_percent(),
            disk_free_mb=disk.free // (1024*1024),
            os_name=platform.system()
        )


class ModuleCard(QFrame):
    """A single capability module card with tier selector and grade bar."""

    activated = Signal(object)  # CapabilityModule
    deactivated = Signal(object)

    def __init__(self, module: CapabilityModule, parent=None):
        super().__init__(parent)
        self._module = module
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(" border: 1px solid #30363d; border-radius: 6px;")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        header = QHBoxLayout()
        self._name_label = QLabel(f"<b>{self._module.name}</b>")
        self._name_label.setStyleSheet("color: #58a6ff; font-size: 14px;")
        header.addWidget(self._name_label)
        self._status_label = QLabel("OFF")
        self._status_label.setStyleSheet("color: #888888; font-weight: bold;")
        header.addWidget(self._status_label)
        header.addStretch()
        layout.addLayout(header)

        desc = QLabel(self._module.description)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #8b949e; font-size: 11px;")
        layout.addWidget(desc)

        # Tier selector with Low/Medium/High resource labels
        tier_row = QHBoxLayout()
        tier_row.addWidget(QLabel("Tier:"))
        self._tier_combo = QComboBox()
        for t in self._module.tiers:
            level = self._tier_resource_label(t.load_score)
            self._tier_combo.addItem(f"{t.name} — {level} ({t.ram_mb}MB, {t.cpu_cores}c)")
        self._tier_combo.currentIndexChanged.connect(self._on_tier_change)
        tier_row.addWidget(self._tier_combo)
        layout.addLayout(tier_row)

        # Activate button
        self._btn_activate = QPushButton("Activate")
        self._btn_activate.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        self._btn_activate.clicked.connect(self._toggle)
        layout.addWidget(self._btn_activate)

    def _on_tier_change(self, idx: int):
        self._module.selected_tier = idx
        # Refresh combo text to reflect new selection if needed
        self._refresh_combo_text()

    def _refresh_combo_text(self):
        """Refresh tier combo text to show current resource label."""
        idx = self._tier_combo.currentIndex()
        if 0 <= idx < len(self._module.tiers):
            t = self._module.tiers[idx]
            level = self._tier_resource_label(t.load_score)
            self._tier_combo.setItemText(idx, f"{t.name} — {level} ({t.ram_mb}MB, {t.cpu_cores}c)")

    @staticmethod
    def _tier_resource_label(load_score: float) -> str:
        if load_score <= 0.25:
            return "Low Resource"
        elif load_score <= 0.60:
            return "Medium Resource"
        else:
            return "High Resource"

    def _toggle(self):
        if self._module.active:
            self._module.active = False
            self._status_label.setText("OFF")
            self._status_label.setStyleSheet("color: #888888; font-weight: bold;")
            self._btn_activate.setText("Activate")
            self._btn_activate.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
            self.deactivated.emit(self._module)
        else:
            self._module.active = True
            self._status_label.setText("ON")
            self._status_label.setStyleSheet("color: #4caf50; font-weight: bold;")
            self._btn_activate.setText("Deactivate")
            self._btn_activate.setStyleSheet("background-color: #c62828; color: white; font-weight: bold;")
            self.activated.emit(self._module)

    def force_deactivate(self):
        if self._module.active:
            self._toggle()

    def get_module(self) -> CapabilityModule:
        return self._module


class ConstraintsWindow(QMainWindow):
    """Command Nexus Part 4 — System Constraint Layer / Upgrades."""

    def __init__(self, registry=None, audit=None, resource_gate=None):
        super().__init__()
        self._obs = get_obfuscation_manager()
        if self._obs.is_obfuscated:
            self.setWindowTitle("Command Nexus — AI Features")
        else:
            self.setWindowTitle("Command Nexus — Upgrades (System Constraints)")
        self.resize(1200, 800)
        self._registry = registry
        self._audit = audit
        self._resource_gate = resource_gate or get_resource_gate()
        self._modules: list = []
        self._cards: list = []
        self._setup_ui()
        self._apply_dark_theme()
        self._load_default_modules()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        if self._obs.is_obfuscated:
            # Simplified obfuscated view
            self._setup_obfuscated_ui(main_layout)
            return

        # Top: System monitor + Cumulative grade
        top_bar = QHBoxLayout()
        self._sys_monitor = SystemMonitorWidget()
        top_bar.addWidget(self._sys_monitor, stretch=1)

        self._cum_group = QGroupBox("Cumulative Load")
        cum_layout = QVBoxLayout(self._cum_group)
        self._cum_label = QLabel("No modules active")
        self._cum_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        cum_layout.addWidget(self._cum_label)
        self._cum_bar = ResourceGradeBar()
        cum_layout.addWidget(self._cum_bar)
        self._cum_btn = QPushButton("Recalculate")
        self._cum_btn.clicked.connect(self._recalculate)
        cum_layout.addWidget(self._cum_btn)
        top_bar.addWidget(self._cum_group, stretch=1)
        main_layout.addLayout(top_bar)

        # Middle: Module categories
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Category filter + module list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("Categories"))
        self._cat_list = QListWidget()
        self._cat_list.addItem("All")
        self._cat_list.itemClicked.connect(self._filter_by_category)
        left_layout.addWidget(self._cat_list)
        left_layout.addWidget(QLabel("Active Modules"))
        self._active_list = QListWidget()
        left_layout.addWidget(self._active_list)
        splitter.addWidget(left_widget)

        # Right: Scrollable module cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._cards_widget = QWidget()
        self._cards_layout = QGridLayout(self._cards_widget)
        self._cards_layout.setSpacing(12)
        scroll.setWidget(self._cards_widget)
        splitter.addWidget(scroll)
        splitter.setSizes([250, 950])
        main_layout.addWidget(splitter, stretch=1)

    def _setup_obfuscated_ui(self, main_layout):
        """When obfuscated, show only a friendly list of active AI features."""
        welcome = QLabel(
            "Your AI comes with powerful built-in features.\n\n"
            "Features are activated automatically based on what your AI needs to do. "
            "You don't need to manage technical details — Command Nexus handles it safely."
        )
        welcome.setWordWrap(True)
        welcome.setStyleSheet("font-size: 14px; color: #c9d1d9; padding: 20px;")
        main_layout.addWidget(welcome)

        self._obfuscation_active_list = QListWidget()
        self._obfuscation_active_list.setStyleSheet("font-size: 13px;")
        main_layout.addWidget(QLabel("<b>Active AI Features:</b>"))
        main_layout.addWidget(self._obfuscation_active_list, stretch=1)

        # Stub the widgets that normal mode expects
        self._sys_monitor = SystemMonitorWidget()
        self._sys_monitor.hide()
        self._cum_group = QGroupBox()
        self._cum_label = QLabel()
        self._cum_bar = ResourceGradeBar()
        self._cum_btn = QPushButton()
        self._cat_list = QListWidget()
        self._active_list = QListWidget()
        self._cards_widget = QWidget()
        self._cards_layout = QGridLayout(self._cards_widget)

    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {  }
            QWidget {  color: #c9d1d9; }
            QGroupBox { border: 1px solid #30363d; margin-top: 10px; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
            QPushButton { border: 1px solid #30363d; padding: 6px; border-radius: 4px; }
            QPushButton:hover { border-color: #58a6ff; }
            QComboBox, QLineEdit { border: 1px solid #30363d; padding: 4px; }
            QLabel { color: #c9d1d9; }
            QListWidget { border: 1px solid #30363d; }
            QListWidget::item:selected { background-color: #1f6feb; color: white; }
            QFrame { border: 1px solid #30363d; }
            QMenu {  color: #c9d1d9; border: 1px solid #30363d; }
            QMenu::item { padding: 4px 20px; }
            QMenu::item:selected { background-color: #1f6feb; color: white; }
        """)

    def _load_default_modules(self):
        """Load built-in capability modules covering all AI use-case categories."""
        defaults = [
            # --- Communication ---
            CapabilityModule(id="chat", name="Chat Companion",
                description="Natural language conversation and rapport building.", category="Communication",
                tiers=[UpgradeTier("Lite", 256, 0, 0.5, 500, 0.10), UpgradeTier("Standard", 1024, 0, 1.5, 1500, 0.35), UpgradeTier("Pro", 4096, 2048, 3.0, 4000, 0.75)]),
            CapabilityModule(id="email", name="Email Sifter & Responder",
                description="Inbox triage, drafting, and automated responses.", category="Communication",
                tiers=[UpgradeTier("Lite", 200, 0, 0.5, 300, 0.08), UpgradeTier("Standard", 800, 0, 1.5, 1000, 0.30), UpgradeTier("Pro", 2048, 1024, 3.0, 3000, 0.65)]),
            # --- Development ---
            CapabilityModule(id="codegen", name="Code Generation Engine",
                description="Multi-language code synthesis, review, and debugging.", category="Development",
                tiers=[UpgradeTier("Lite", 400, 512, 1.0, 500, 0.12), UpgradeTier("Standard", 1500, 1536, 2.0, 1500, 0.32), UpgradeTier("Pro", 4096, 4096, 3.5, 4000, 0.70)]),
            CapabilityModule(id="codereview", name="Code Review & QA",
                description="Static analysis, security scanning, and PR review.", category="Development",
                tiers=[UpgradeTier("Lite", 300, 256, 0.5, 400, 0.10), UpgradeTier("Standard", 1000, 1024, 1.5, 1200, 0.28), UpgradeTier("Pro", 3000, 3072, 3.0, 3500, 0.62)]),
            # --- Creative ---
            CapabilityModule(id="creative", name="Creative Writer",
                description="Storytelling, copywriting, and content generation.", category="Creative",
                tiers=[UpgradeTier("Lite", 300, 0, 0.5, 400, 0.09), UpgradeTier("Standard", 1200, 0, 1.5, 1200, 0.28), UpgradeTier("Pro", 3072, 1536, 3.0, 3000, 0.60)]),
            CapabilityModule(id="imagegen", name="Image Generation",
                description="Text-to-image synthesis and style transfer.", category="Creative",
                tiers=[UpgradeTier("Lite", 512, 1024, 1.0, 1000, 0.15), UpgradeTier("Standard", 1536, 3072, 2.0, 2500, 0.38), UpgradeTier("Pro", 4096, 8192, 4.0, 6000, 0.80)]),
            # --- Research ---
            CapabilityModule(id="research", name="Research Assistant",
                description="Web search, summarization, and citation tracking.", category="Research",
                tiers=[UpgradeTier("Lite", 256, 0, 0.5, 600, 0.10), UpgradeTier("Standard", 1024, 0, 1.5, 2000, 0.30), UpgradeTier("Pro", 3072, 1536, 3.0, 5000, 0.68)]),
            CapabilityModule(id="academic", name="Academic Researcher",
                description="Paper analysis, hypothesis generation, peer-review support.", category="Research",
                tiers=[UpgradeTier("Lite", 400, 0, 0.8, 800, 0.14), UpgradeTier("Standard", 1536, 1024, 2.0, 2500, 0.36), UpgradeTier("Pro", 4096, 3072, 3.5, 6000, 0.72)]),
            # --- Organization ---
            CapabilityModule(id="organizer", name="Personal Organizer",
                description="Calendar, reminders, and life logistics.", category="Organization",
                tiers=[UpgradeTier("Lite", 128, 0, 0.3, 200, 0.05), UpgradeTier("Standard", 512, 0, 1.0, 800, 0.18), UpgradeTier("Pro", 1536, 0, 2.0, 2000, 0.40)]),
            CapabilityModule(id="taskmgr", name="Task / Project Manager",
                description="Kanban, Gantt, dependency tracking, and resource allocation.", category="Organization",
                tiers=[UpgradeTier("Lite", 200, 0, 0.5, 400, 0.08), UpgradeTier("Standard", 800, 0, 1.5, 1200, 0.26), UpgradeTier("Pro", 2048, 1024, 3.0, 3000, 0.58)]),
            # --- Education ---
            CapabilityModule(id="tutor", name="Classroom Tutor",
                description="Adaptive lesson delivery and progress tracking.", category="Education",
                tiers=[UpgradeTier("Lite", 256, 0, 0.5, 500, 0.09), UpgradeTier("Standard", 1024, 0, 1.5, 1500, 0.28), UpgradeTier("Pro", 2560, 1024, 3.0, 3500, 0.62)]),
            CapabilityModule(id="language", name="Language Coach",
                description="Translation, grammar correction, and fluency training.", category="Education",
                tiers=[UpgradeTier("Lite", 200, 0, 0.5, 400, 0.08), UpgradeTier("Standard", 800, 0, 1.5, 1000, 0.24), UpgradeTier("Pro", 2048, 1024, 3.0, 2500, 0.55)]),
            # --- Document ---
            CapabilityModule(id="docproc", name="Document Processor",
                description="PDF parsing, data extraction, and form filling.", category="Document",
                tiers=[UpgradeTier("Lite", 256, 0, 0.5, 600, 0.10), UpgradeTier("Standard", 1024, 0, 1.5, 1500, 0.28), UpgradeTier("Pro", 2560, 1024, 3.0, 3500, 0.62)]),
            CapabilityModule(id="scribe", name="Meeting Scribe",
                description="Real-time transcription, action items, and summaries.", category="Document",
                tiers=[UpgradeTier("Lite", 300, 0, 0.5, 500, 0.10), UpgradeTier("Standard", 1024, 512, 1.5, 1500, 0.30), UpgradeTier("Pro", 2560, 2048, 3.0, 3500, 0.65)]),
            # --- Business ---
            CapabilityModule(id="support", name="Customer Support Agent",
                description="Ticket routing, knowledge-base answers, and sentiment analysis.", category="Business",
                tiers=[UpgradeTier("Lite", 256, 0, 0.5, 500, 0.09), UpgradeTier("Standard", 1024, 0, 1.5, 1500, 0.28), UpgradeTier("Pro", 2560, 1024, 3.0, 3500, 0.62)]),
            CapabilityModule(id="sales", name="Sales Assistant",
                description="Lead scoring, outreach drafting, and CRM updates.", category="Business",
                tiers=[UpgradeTier("Lite", 200, 0, 0.5, 400, 0.08), UpgradeTier("Standard", 800, 0, 1.5, 1200, 0.26), UpgradeTier("Pro", 2048, 1024, 3.0, 3000, 0.58)]),
            CapabilityModule(id="marketing", name="Marketing Generator",
                description="Campaign copy, SEO, and social media scheduling.", category="Business",
                tiers=[UpgradeTier("Lite", 256, 0, 0.5, 500, 0.09), UpgradeTier("Standard", 1024, 0, 1.5, 1500, 0.28), UpgradeTier("Pro", 2560, 1024, 3.0, 3500, 0.62)]),
            CapabilityModule(id="finance", name="Financial Analyst",
                description="Spreadsheet modeling, trend analysis, and forecasting.", category="Business",
                tiers=[UpgradeTier("Lite", 300, 0, 0.5, 600, 0.10), UpgradeTier("Standard", 1200, 512, 1.5, 1800, 0.30), UpgradeTier("Pro", 3072, 2048, 3.0, 4000, 0.68)]),
            CapabilityModule(id="hr", name="HR Assistant",
                description="Resume screening, interview prep, and policy guidance.", category="Business",
                tiers=[UpgradeTier("Lite", 200, 0, 0.5, 400, 0.08), UpgradeTier("Standard", 800, 0, 1.5, 1200, 0.26), UpgradeTier("Pro", 2048, 1024, 3.0, 3000, 0.58)]),
            # --- Enterprise ---
            CapabilityModule(id="compliance", name="Compliance Auditor",
                description="Regulatory checks, risk assessment, and audit trails.", category="Enterprise",
                tiers=[UpgradeTier("Lite", 400, 0, 0.8, 800, 0.14), UpgradeTier("Standard", 1536, 512, 2.0, 2500, 0.36), UpgradeTier("Pro", 4096, 2048, 3.5, 6000, 0.74)]),
            CapabilityModule(id="itops", name="IT Operations Agent",
                description="Log analysis, anomaly detection, and auto-remediation.", category="Enterprise",
                tiers=[UpgradeTier("Lite", 400, 512, 1.0, 800, 0.15), UpgradeTier("Standard", 1536, 1536, 2.0, 2500, 0.38), UpgradeTier("Pro", 4096, 4096, 3.5, 6000, 0.76)]),
            CapabilityModule(id="legal", name="Legal Document Reviewer",
                description="Contract parsing, clause extraction, and redlining.", category="Enterprise",
                tiers=[UpgradeTier("Lite", 512, 0, 1.0, 1000, 0.16), UpgradeTier("Standard", 2048, 1024, 2.0, 3000, 0.40), UpgradeTier("Pro", 5120, 3072, 3.5, 7000, 0.78)]),
            CapabilityModule(id="orchestrator", name="Multi-Department Orchestrator",
                description="Cross-team coordination, SLA monitoring, and escalation.", category="Enterprise",
                tiers=[UpgradeTier("Lite", 512, 256, 1.0, 1000, 0.15), UpgradeTier("Standard", 2048, 1024, 2.0, 3000, 0.38), UpgradeTier("Pro", 5120, 3072, 3.5, 7000, 0.76)]),
            # --- Audio / Vision / Infrastructure ---
            CapabilityModule(id="whisper", name="Whisper (Voice)",
                description="Speech-to-text and voice interaction.", category="Audio",
                tiers=[UpgradeTier("Lite", 150, 0, 0.5, 200, 0.08), UpgradeTier("Standard", 800, 0, 1.5, 1000, 0.28), UpgradeTier("Pro", 2500, 1024, 3.0, 2500, 0.62)]),
            CapabilityModule(id="tts", name="Text-to-Speech",
                description="Natural voice synthesis for responses.", category="Audio",
                tiers=[UpgradeTier("Lite", 100, 0, 0.3, 100, 0.05), UpgradeTier("Standard", 400, 0, 1.0, 400, 0.18), UpgradeTier("Pro", 1024, 512, 2.5, 1200, 0.42)]),
            CapabilityModule(id="vision", name="Vision (Image Analysis)",
                description="Image recognition, OCR, and scene understanding.", category="Vision",
                tiers=[UpgradeTier("Lite", 400, 512, 1.0, 600, 0.14), UpgradeTier("Standard", 1200, 1536, 2.0, 1800, 0.34), UpgradeTier("Pro", 3072, 4096, 3.5, 4500, 0.72)]),
            CapabilityModule(id="rag", name="RAG (Retrieval Augmented Generation)",
                description="Knowledge-base retrieval with LLM augmentation.", category="Infrastructure",
                tiers=[UpgradeTier("Lite", 256, 0, 0.5, 1000, 0.10), UpgradeTier("Standard", 1024, 512, 1.5, 4000, 0.30), UpgradeTier("Pro", 3072, 2048, 3.0, 10000, 0.68)]),
            CapabilityModule(id="workflow", name="Workflow Automator",
                description="Trigger-based automation and pipeline orchestration.", category="Infrastructure",
                tiers=[UpgradeTier("Lite", 200, 0, 0.5, 500, 0.09), UpgradeTier("Standard", 800, 0, 1.5, 1500, 0.26), UpgradeTier("Pro", 2048, 1024, 3.0, 3500, 0.60)]),
        ]
        self._modules = defaults
        categories = sorted(set(m.category for m in defaults))
        for c in categories:
            self._cat_list.addItem(c)
        self._render_cards()

    def _render_cards(self):
        """Render module cards in the grid."""
        # Clear existing
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()

        selected_cat = self._cat_list.currentItem().text() if self._cat_list.currentItem() else "All"
        filtered = [m for m in self._modules if selected_cat == "All" or m.category == selected_cat]

        for i, mod in enumerate(filtered):
            card = ModuleCard(mod)
            card.activated.connect(self._on_module_activated)
            card.deactivated.connect(self._on_module_deactivated)
            self._cards_layout.addWidget(card, i // 2, i % 2)
            self._cards.append(card)

    def _filter_by_category(self):
        self._render_cards()

    def _on_module_activated(self, module: CapabilityModule):
        if self._obs.is_obfuscated:
            if hasattr(self, "_obfuscation_active_list"):
                self._obfuscation_active_list.addItem(module.name)
            return
        tier = module.get_selected_tier()

        # ── Central resource gate check ──
        result = self._resource_gate.register_capability(
            capability_id=module.id,
            name=module.name,
            window_source="constraints",
            ram_mb=tier.ram_mb,
            vram_mb=tier.vram_mb,
            cpu_cores=tier.cpu_cores,
            disk_mb=tier.disk_mb,
            load_score=tier.load_score,
        )

        if result.decision == GateDecision.DENY:
            # Block activation
            for card in self._cards:
                if card.get_module().id == module.id:
                    card.force_deactivate()
            QMessageBox.critical(
                self, "BLOCKED — Resource Limit Exceeded",
                result.message
            )
            return

        if result.decision == GateDecision.WARN:
            reply = QMessageBox.warning(
                self, "Warning — High Resource Load",
                f"{result.message}\n\nProceed anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                self._resource_gate.unregister_capability(module.id)
                for card in self._cards:
                    if card.get_module().id == module.id:
                        card.force_deactivate()
                return

        self._active_list.addItem(f"{module.name} [{tier.name}]")
        self._recalculate()

    def _on_module_deactivated(self, module: CapabilityModule):
        if self._obs.is_obfuscated:
            if hasattr(self, "_obfuscation_active_list"):
                for i in range(self._obfuscation_active_list.count()):
                    if self._obfuscation_active_list.item(i).text() == module.name:
                        self._obfuscation_active_list.takeItem(i)
                        break
            return
        # Unregister from central gate
        self._resource_gate.unregister_capability(module.id)
        # Remove from active list
        for i in range(self._active_list.count()):
            item = self._active_list.item(i)
            if item.text().startswith(module.name):
                self._active_list.takeItem(i)
                break
        self._recalculate()

    def _recalculate(self):
        if self._obs.is_obfuscated:
            return
        active = [m for m in self._modules if m.active]
        if not active:
            self._cum_label.setText("No modules active")
            self._cum_bar.set_grade(ModelResourceGrade.GREEN, 0.0)
            return

        # Use central gate for cumulative data
        gate_status = self._resource_gate.get_detailed_status()
        total_score = gate_status["cumulative_load"]
        total_ram = gate_status["cumulative_ram_mb"]
        snap = self._resource_gate.get_snapshot()
        grade = gate_status["grade"]

        # Map gate grade to model grade for the bar
        grade_map = {
            "green": ModelResourceGrade.GREEN,
            "green_yellow": ModelResourceGrade.GREEN_YELLOW,
            "yellow": ModelResourceGrade.YELLOW,
            "yellow_red": ModelResourceGrade.YELLOW_RED,
            "red": ModelResourceGrade.RED,
            "crimson_red": ModelResourceGrade.CRIMSON_RED,
        }
        model_grade = grade_map.get(grade, ModelResourceGrade.GREEN)

        self._cum_label.setText(
            f"Active: {len(active)} modules | Total Load: {total_score:.0%} | "
            f"RAM required: {total_ram} MB / {snap.available_ram_mb} MB free"
        )
        self._cum_bar.set_grade(model_grade, total_score)

        # If crimson red is reached, auto-degrade via gate
        if model_grade == ModelResourceGrade.CRIMSON_RED:
            deactivated = self._resource_gate.auto_degrade()
            if deactivated:
                names = ", ".join(deactivated)
                QMessageBox.critical(
                    self, "SYSTEM OVERLOAD",
                    f"CRIMSON RED reached: {total_score:.0%} total load.\n\n"
                    f"Auto-deactivated: {names}\n"
                    f"Your system has been protected."
                )
                # Sync UI with gate state
                for m in active:
                    if m.id not in [c.capability_id for c in self._resource_gate.get_active_capabilities()]:
                        m.active = False
                        for card in self._cards:
                            if card.get_module().id == m.id:
                                card.force_deactivate()
                self._recalculate()
