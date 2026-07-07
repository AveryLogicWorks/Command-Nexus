# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.2.0

"""
Model Manager Panel — UI for the Basic Model Manager.

Shows installed local models as cards with specs, allows one-click
model selection, shows concurrent model limit, and provides
auto-recommendation based on use case.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QFrame, QProgressBar, QCheckBox,
    QDialog, QDialogButtonBox, QMessageBox, QComboBox, QGroupBox,
    QSpinBox, QSizePolicy, QTextEdit, QListWidget, QListWidgetItem,
    QLineEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

from ...core.model_manager import ModelManager, LocalModelInfo, ModelCategory


# Category display metadata
_CATEGORY_COLORS = {
    ModelCategory.CHAT: "#00897b",
    ModelCategory.CODER: "#5e35b1",
    ModelCategory.PLANNER: "#f57c00",
    ModelCategory.VISION: "#e91e63",
    ModelCategory.SMALL: "#2e7d32",
    ModelCategory.UNKNOWN: "#607d8b",
}

_CATEGORY_LABELS = {
    ModelCategory.CHAT: "Chat & Writing",
    ModelCategory.CODER: "Code & Programming",
    ModelCategory.PLANNER: "Planning & Reasoning",
    ModelCategory.VISION: "Vision & Image",
    ModelCategory.SMALL: "Lightweight",
    ModelCategory.UNKNOWN: "General",
}

_CATEGORY_ICONS = {
    ModelCategory.CHAT: "[~]",
    ModelCategory.CODER: "[</>]",
    ModelCategory.PLANNER: "[::]",
    ModelCategory.VISION: "[img]",
    ModelCategory.SMALL: "[*]",
    ModelCategory.UNKNOWN: "[?]",
}


class ModelCard(QFrame):
    """A single model card showing model info and selection controls."""

    activate_clicked = pyqtSignal(str)  # model name
    concurrent_toggled = pyqtSignal(str, bool)  # model name, checked

    def __init__(self, model: LocalModelInfo, is_active: bool, is_concurrent: bool,
                 can_add_concurrent: bool, parent=None):
        super().__init__(parent)
        self._model = model
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setLineWidth(1)

        color = _CATEGORY_COLORS.get(model.category, "#607d8b")
        icon = _CATEGORY_ICONS.get(model.category, "[?]")
        cat_label = _CATEGORY_LABELS.get(model.category, "General")

        # Highlight active model
        if is_active:
            self.setStyleSheet(f"""
                ModelCard {{
                    border: 2px solid {color};
                    border-radius: 8px;
                    background-color: rgba(0, 137, 123, 0.08);
                    padding: 8px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                ModelCard {{
                    border: 1px solid #30363d;
                    border-radius: 8px;
                    
                    padding: 8px;
                }}
                ModelCard:hover {{
                    border: 1px solid {color};
                }}
            """)

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header: icon + name
        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")
        icon_label.setFixedWidth(40)
        name_label = QLabel(model.name)
        name_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #e6edf3;")
        name_label.setWordWrap(True)
        header.addWidget(icon_label)
        header.addWidget(name_label, 1)
        layout.addLayout(header)

        # Category badge
        cat_label_widget = QLabel(cat_label)
        cat_label_widget.setStyleSheet(f"""
            background-color: {color}; color: white;
            padding: 2px 8px; border-radius: 4px;
            font-size: 10px; font-weight: bold;
        """)
        cat_label_widget.setFixedHeight(20)
        layout.addWidget(cat_label_widget)

        # Specs
        specs = []
        if model.parameter_count:
            specs.append(f"Params: {model.parameter_count}")
        if model.quantization:
            specs.append(f"Quant: {model.quantization}")
        specs.append(f"Size: {model.size_mb:.0f} MB")
        specs.append(f"Min RAM: {model.min_ram_mb} MB")
        specs_label = QLabel("  |  ".join(specs))
        specs_label.setStyleSheet("font-size: 11px; color: #8b949e;")
        specs_label.setWordWrap(True)
        layout.addWidget(specs_label)

        # Recommended for
        if model.recommended_for:
            rec_label = QLabel("Best for: " + ", ".join(model.recommended_for[:4]))
            rec_label.setStyleSheet("font-size: 10px; color: #768390; font-style: italic;")
            rec_label.setWordWrap(True)
            layout.addWidget(rec_label)

        # Buttons
        btn_layout = QHBoxLayout()

        self._btn_activate = QPushButton("Set Active" if not is_active else "Active")
        self._btn_activate.setStyleSheet(f"""
            QPushButton {{
                background-color: {color}; color: white;
                border-radius: 4px; padding: 4px 12px;
                font-weight: bold; font-size: 11px;
            }}
            QPushButton:disabled {{
                background-color: #238636; color: white;
            }}
        """)
        self._btn_activate.setEnabled(not is_active)
        self._btn_activate.clicked.connect(lambda: self.activate_clicked.emit(self._model.name))
        btn_layout.addWidget(self._btn_activate)

        self._chk_concurrent = QCheckBox("Concurrent")
        self._chk_concurrent.setChecked(is_concurrent)
        self._chk_concurrent.setEnabled(can_add_concurrent or is_concurrent)
        self._chk_concurrent.setStyleSheet("color: #8b949e; font-size: 11px;")
        self._chk_concurrent.toggled.connect(
            lambda checked: self.concurrent_toggled.emit(self._model.name, checked)
        )
        btn_layout.addWidget(self._chk_concurrent)

        layout.addLayout(btn_layout)


class ModelManagerPanel(QWidget):
    """Main panel for the Basic Model Manager."""

    model_changed = pyqtSignal(str)  # emits new active model name

    def __init__(self, model_manager: ModelManager, parent=None):
        super().__init__(parent)
        self._mm = model_manager
        self._cards: dict[str, ModelCard] = {}
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Title
        title = QLabel("Model Manager")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e6edf3;")
        layout.addWidget(title)

        subtitle = QLabel("Select which local AI model to use. One click to switch brains.")
        subtitle.setStyleSheet("font-size: 12px; color: #8b949e;")
        layout.addWidget(subtitle)

        # System info bar
        sys_bar = QHBoxLayout()
        self._lbl_ram = QLabel()
        self._lbl_ram.setStyleSheet("font-size: 11px; color: #8b949e;")
        sys_bar.addWidget(self._lbl_ram)

        self._lbl_cores = QLabel()
        self._lbl_cores.setStyleSheet("font-size: 11px; color: #8b949e;")
        sys_bar.addWidget(self._lbl_cores)

        self._lbl_capacity = QLabel()
        self._lbl_capacity.setStyleSheet("font-size: 11px; color: #8b949e;")
        sys_bar.addWidget(self._lbl_capacity)
        sys_bar.addStretch()
        layout.addLayout(sys_bar)

        # Concurrent models bar
        conc_bar = QHBoxLayout()
        conc_label = QLabel("Concurrent Models:")
        conc_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #e6edf3;")
        conc_bar.addWidget(conc_label)

        self._lbl_concurrent = QLabel("0 / 3")
        self._lbl_concurrent.setStyleSheet("font-size: 12px; color: #f0883e; font-weight: bold;")
        conc_bar.addWidget(self._lbl_concurrent)

        conc_bar.addStretch()

        self._btn_clear = QPushButton("Clear All")
        self._btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #da3633; color: white;
                border-radius: 4px; padding: 4px 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #f85149; }
        """)
        self._btn_clear.clicked.connect(self._on_clear_all)
        conc_bar.addWidget(self._btn_clear)

        layout.addLayout(conc_bar)

        # Recommendation bar
        rec_bar = QHBoxLayout()
        rec_bar.addWidget(QLabel("Auto-recommend for:"))
        self._combo_use_case = QComboBox()
        self._combo_use_case.addItems([
            "Chat & Conversation", "Code Generation", "Code Review",
            "Creative Writing", "Research & Analysis", "Planning & Tasks",
            "Email & Communication", "Summarization", "General Purpose",
        ])
        self._combo_use_case.setStyleSheet("padding: 2px 8px;")
        rec_bar.addWidget(self._combo_use_case)

        self._btn_recommend = QPushButton("Recommend")
        self._btn_recommend.setStyleSheet("""
            QPushButton {
                background-color: #1f6feb; color: white;
                border-radius: 4px; padding: 4px 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: #388bfd; }
        """)
        self._btn_recommend.clicked.connect(self._on_recommend)
        rec_bar.addWidget(self._btn_recommend)
        rec_bar.addStretch()
        layout.addLayout(rec_bar)

        # Refresh button
        self._btn_refresh = QPushButton("Rescan Models")
        self._btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #30363d; color: #8b949e;
                border-radius: 4px; padding: 4px 12px;
            }
            QPushButton:hover { background-color: #424a53; color: #e6edf3; }
        """)
        self._btn_refresh.clicked.connect(self._on_rescan)
        layout.addWidget(self._btn_refresh)

        # Scroll area for model cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._cards_container = QWidget()
        self._cards_layout = QGridLayout(self._cards_container)
        self._cards_layout.setSpacing(10)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self._cards_container)
        layout.addWidget(scroll, 1)

        # No models message
        self._lbl_no_models = QLabel(
            "No local models found.\n\n"
            "Place .gguf model files in b:\\local_models\\\n"
            "or ~/local_models/ and click Rescan Models."
        )
        self._lbl_no_models.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_no_models.setStyleSheet("font-size: 14px; color: #8b949e; padding: 40px;")
        self._lbl_no_models.setVisible(False)
        layout.addWidget(self._lbl_no_models)

    def refresh(self):
        """Rebuild the model cards from the current model list."""
        # Clear existing cards
        for card in self._cards.values():
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()

        models = self._mm.list_models()
        active = self._mm.get_active_model()
        concurrent = self._mm.get_concurrent_models()
        max_conc = self._mm.get_max_concurrent()

        # Update system info
        ram = self._mm.get_system_ram_mb()
        cores = self._mm.get_cpu_cores()
        capacity = self._mm.estimate_concurrent_capacity()
        self._lbl_ram.setText(f"System RAM: {ram:,} MB")
        self._lbl_cores.setText(f"CPU Cores: {cores}")
        self._lbl_capacity.setText(f"Est. Capacity: {capacity} models")
        self._lbl_concurrent.setText(f"{len(concurrent)} / {max_conc if max_conc < 999 else '∞'}")

        if not models:
            self._lbl_no_models.setVisible(True)
            return
        self._lbl_no_models.setVisible(False)

        # Build cards in a grid (2 columns)
        for i, model in enumerate(models):
            is_active = model.name == active
            is_concurrent = model.name in concurrent
            can_add = len(concurrent) < max_conc

            card = ModelCard(model, is_active, is_concurrent, can_add)
            card.activate_clicked.connect(self._on_activate)
            card.concurrent_toggled.connect(self._on_concurrent_toggle)
            row = i // 2
            col = i % 2
            self._cards_layout.addWidget(card, row, col)
            self._cards[model.name] = card

    def _on_activate(self, model_name: str):
        if self._mm.set_active_model(model_name):
            self._sync_to_backend(model_name)
            self.refresh()
            self.model_changed.emit(model_name)

    def _sync_to_backend(self, model_name: str):
        """Update the builtin backend provider's model name to match the selected model."""
        try:
            from ...core.settings_manager import SettingsManager
            from ...core.backend_manager import BackendManager
            settings = SettingsManager()
            backend = BackendManager(settings)
            providers = backend.list_providers()
            if "builtin" in providers:
                builtin = providers["builtin"]
                builtin.model = model_name
                backend.save_to_settings()
        except Exception:
            pass  # Non-fatal — model manager works independently

    def _on_concurrent_toggle(self, model_name: str, checked: bool):
        if checked:
            if not self._mm.add_concurrent_model(model_name):
                QMessageBox.warning(
                    self, "Limit Reached",
                    f"You can have at most {self._mm.get_max_concurrent()} concurrent models.\n"
                    "Upgrade to Advanced Model Manager for unlimited concurrent models."
                )
                self.refresh()
        else:
            self._mm.remove_concurrent_model(model_name)
        self.refresh()
        self.model_changed.emit(self._mm.get_active_model())

    def _on_clear_all(self):
        reply = QMessageBox.question(
            self, "Clear All Models",
            "Remove all concurrent models? The active model will be reset.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._mm.clear_concurrent_models()
            self.refresh()
            self.model_changed.emit("")

    def _on_recommend(self):
        use_case = self._combo_use_case.currentText()
        model = self._mm.recommend_for_use_case(use_case)
        if model:
            self._mm.set_active_model(model.name)
            self.refresh()
            self.model_changed.emit(model.name)
            QMessageBox.information(
                self, "Recommended Model",
                f"Based on '{use_case}', recommended:\n\n"
                f"  {model.name}\n"
                f"  Category: {_CATEGORY_LABELS.get(model.category, 'General')}\n"
                f"  Size: {model.size_mb:.0f} MB\n"
                f"  Best for: {', '.join(model.recommended_for[:4])}"
            )
        else:
            QMessageBox.information(self, "No Models", "No models available to recommend.")

    def _on_rescan(self):
        self._mm.scan_models()
        self.refresh()


class AdvancedModelManagerPanel(QWidget):
    """Advanced Model Manager panel — routing, benchmarking, downloads, stats."""

    def __init__(self, mm: "ModelManager", parent=None):
        super().__init__(parent)
        self._mm = mm
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Title
        title = QLabel("Advanced Model Manager")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e6edf3;")
        layout.addWidget(title)

        subtitle = QLabel("Unlimited concurrent models, custom routing, benchmarking, and model downloads.")
        subtitle.setStyleSheet("font-size: 12px; color: #8b949e;")
        layout.addWidget(subtitle)

        # Enable advanced mode
        self._chk_advanced = QCheckBox("Enable Advanced Mode (Enterprise/Unlimited tier)")
        self._chk_advanced.setStyleSheet("font-size: 13px; color: #f0883e; font-weight: bold;")
        self._chk_advanced.setChecked(self._mm.is_advanced())
        self._chk_advanced.toggled.connect(self._on_advanced_toggle)
        layout.addWidget(self._chk_advanced)

        # Stats
        self._lbl_stats = QLabel()
        self._lbl_stats.setStyleSheet("font-size: 12px; color: #8b949e; padding: 4px 0;")
        layout.addWidget(self._lbl_stats)

        # Tab widget for advanced features
        from PyQt6.QtWidgets import QTabWidget
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #21262d; color: #8b949e; padding: 6px 16px; } QTabBar::tab:selected { background: #1f6feb; color: white; }")

        # Tab 1: Model Routing
        routing_tab = QWidget()
        routing_layout = QVBoxLayout(routing_tab)
        routing_layout.addWidget(QLabel("Route specific capabilities to specific models:"))
        self._routing_grid = QGridLayout()
        routing_layout.addLayout(self._routing_grid)
        self._routing_combos: dict[str, QComboBox] = {}
        btn_clear_routing = QPushButton("Clear All Routing")
        btn_clear_routing.setStyleSheet("QPushButton { background-color: #30363d; color: #e6edf3; border-radius: 4px; padding: 4px 12px; } QPushButton:hover { background-color: #424a53; }")
        btn_clear_routing.clicked.connect(self._on_clear_routing)
        routing_layout.addWidget(btn_clear_routing)
        routing_layout.addStretch()
        tabs.addTab(routing_tab, "Routing")

        # Tab 2: Benchmarks
        bench_tab = QWidget()
        bench_layout = QVBoxLayout(bench_tab)
        bench_layout.addWidget(QLabel("Benchmark models to measure performance:"))
        bench_row = QHBoxLayout()
        self._combo_bench = QComboBox()
        self._combo_bench.setStyleSheet("padding: 2px 8px;")
        bench_row.addWidget(self._combo_bench)
        self._btn_bench = QPushButton("Run Benchmark")
        self._btn_bench.setStyleSheet("QPushButton { background-color: #1f6feb; color: white; border-radius: 4px; padding: 4px 16px; font-weight: bold; } QPushButton:hover { background-color: #388bfd; }")
        self._btn_bench.clicked.connect(self._on_benchmark)
        bench_row.addWidget(self._btn_bench)
        bench_layout.addLayout(bench_row)
        self._txt_bench_results = QTextEdit()
        self._txt_bench_results.setReadOnly(True)
        self._txt_bench_results.setStyleSheet(" color: #e6edf3; border: 1px solid #30363d; border-radius: 4px; padding: 8px;")
        bench_layout.addWidget(self._txt_bench_results)
        tabs.addTab(bench_tab, "Benchmarks")

        # Tab 3: Downloads
        dl_tab = QWidget()
        dl_layout = QVBoxLayout(dl_tab)
        dl_layout.addWidget(QLabel("Download recommended models from HuggingFace:"))
        self._dl_list = QListWidget()
        self._dl_list.setStyleSheet("QListWidget {  border: 1px solid #30363d; border-radius: 6px; padding: 4px; } QListWidget::item { padding: 8px; border-bottom: 1px solid #21262d; }")
        dl_layout.addWidget(self._dl_list)
        self._btn_download = QPushButton("Download Selected")
        self._btn_download.setStyleSheet("QPushButton { background-color: #238636; color: white; border-radius: 4px; padding: 6px 16px; font-weight: bold; } QPushButton:hover { background-color: #2ea043; }")
        self._btn_download.clicked.connect(self._on_download)
        dl_layout.addWidget(self._btn_download)
        tabs.addTab(dl_tab, "Downloads")

        # Tab 4: Model Management (delete)
        mgmt_tab = QWidget()
        mgmt_layout = QVBoxLayout(mgmt_tab)
        mgmt_layout.addWidget(QLabel("Delete models from disk (permanent):"))
        self._combo_delete = QComboBox()
        self._combo_delete.setStyleSheet("padding: 2px 8px;")
        mgmt_layout.addWidget(self._combo_delete)
        self._btn_delete = QPushButton("Delete Model")
        self._btn_delete.setStyleSheet("QPushButton { background-color: #da3633; color: white; border-radius: 4px; padding: 6px 16px; font-weight: bold; } QPushButton:hover { background-color: #f85149; }")
        self._btn_delete.clicked.connect(self._on_delete_model)
        mgmt_layout.addWidget(self._btn_delete)
        mgmt_layout.addStretch()
        tabs.addTab(mgmt_tab, "Manage")

        layout.addWidget(tabs, 1)

    def _refresh(self):
        stats = self._mm.get_model_stats()
        self._lbl_stats.setText(
            f"Models: {stats['total_models']} | Size: {stats['total_size_gb']} GB | "
            f"Concurrent: {stats['concurrent_count']}/{stats['max_concurrent']} | "
            f"Routing: {stats['routing_count']} | Benchmarks: {stats['benchmarks_count']}"
        )
        # Populate model combos
        models = self._mm.list_models()
        model_names = [m.name for m in models]
        self._combo_bench.clear()
        self._combo_bench.addItems(model_names)
        self._combo_delete.clear()
        self._combo_delete.addItems(model_names)
        # Populate routing
        self._populate_routing(model_names)
        # Populate download candidates
        self._populate_downloads()
        # Show benchmark results
        self._show_benchmarks()

    def _populate_routing(self, model_names: list[str]):
        # Clear existing
        for combo in self._routing_combos.values():
            combo.setParent(None)
            combo.deleteLater()
        self._routing_combos.clear()
        routing = self._mm.get_model_routing()
        capabilities = ["Chat", "Code Generation", "Code Review", "Research", "Creative Writing", "Planning", "Vision", "Email"]
        for i, cap in enumerate(capabilities):
            label = QLabel(cap)
            label.setStyleSheet("color: #8b949e; font-size: 12px;")
            self._routing_grid.addWidget(label, i, 0)
            combo = QComboBox()
            combo.addItem("— Default —")
            combo.addItems(model_names)
            current = routing.get(cap, "")
            if current and current in model_names:
                combo.setCurrentText(current)
            combo.currentTextChanged.connect(lambda text, c=cap: self._on_routing_changed(c, text))
            combo.setStyleSheet("padding: 2px 8px;")
            self._routing_grid.addWidget(combo, i, 1)
            self._routing_combos[cap] = combo

    def _populate_downloads(self):
        self._dl_list.clear()
        candidates = self._mm.get_download_candidates()
        existing_names = {m.name for m in self._mm.list_models()}
        for c in candidates:
            already = " [INSTALLED]" if any(c["filename"].split(".")[0] in n for n in existing_names) else ""
            item_text = f"{c['name']} ({c['category']}) — {c['size_gb']} GB{already}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, c)
            self._dl_list.addItem(item)

    def _show_benchmarks(self):
        benchmarks = self._mm.get_all_benchmarks()
        if not benchmarks:
            self._txt_bench_results.setPlainText("No benchmarks yet. Run a benchmark to see results.")
            return
        parts = []
        for name, bench in benchmarks.items():
            parts.append(f"=== {name} ===")
            if "error" in bench:
                parts.append(f"  Error: {bench['error']}")
            else:
                parts.append(f"  Load time: {bench.get('load_time_ms', 0)} ms")
                parts.append(f"  Tokens/sec: {bench.get('tokens_per_sec', 0)}")
                parts.append(f"  Memory: {bench.get('memory_usage_mb', 0)} MB")
            parts.append("")
        self._txt_bench_results.setPlainText("\n".join(parts))

    def _on_advanced_toggle(self, enabled: bool):
        self._mm.set_advanced_mode(enabled)
        self._refresh()

    def _on_routing_changed(self, capability: str, model_name: str):
        if model_name == "— Default —":
            return
        self._mm.set_model_routing(capability, model_name)

    def _on_clear_routing(self):
        self._mm.clear_model_routing()
        self._refresh()

    def _on_benchmark(self):
        model_name = self._combo_bench.currentText()
        if not model_name:
            return
        self._btn_bench.setEnabled(False)
        self._btn_bench.setText("Benchmarking...")
        import threading
        def _run():
            result = self._mm.benchmark_model(model_name)
            # Update UI on main thread
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self._benchmark_done(result))
        threading.Thread(target=_run, daemon=True).start()

    def _benchmark_done(self, result):
        self._btn_bench.setEnabled(True)
        self._btn_bench.setText("Run Benchmark")
        self._show_benchmarks()
        if "error" in result:
            QMessageBox.warning(self, "Benchmark Error", result["error"])

    def _on_download(self):
        if not self._mm.is_advanced():
            QMessageBox.warning(self, "Advanced Required", "Enable Advanced Mode to download models.")
            return
        item = self._dl_list.currentItem()
        if not item:
            return
        c = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "Download Model", f"Download {c['name']} ({c['size_gb']} GB)?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._btn_download.setEnabled(False)
        self._btn_download.setText("Downloading...")
        import threading
        def _run():
            success = self._mm.download_model(c["repo_id"], c["filename"])
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self._download_done(success, c["name"]))
        threading.Thread(target=_run, daemon=True).start()

    def _download_done(self, success: bool, name: str):
        self._btn_download.setEnabled(True)
        self._btn_download.setText("Download Selected")
        if success:
            QMessageBox.information(self, "Download Complete", f"Model '{name}' downloaded successfully.")
        else:
            QMessageBox.warning(self, "Download Failed", f"Could not download '{name}'.\nMake sure huggingface_hub is installed.")
        self._refresh()

    def _on_delete_model(self):
        if not self._mm.is_advanced():
            QMessageBox.warning(self, "Advanced Required", "Enable Advanced Mode to delete models.")
            return
        model_name = self._combo_delete.currentText()
        if not model_name:
            return
        reply = QMessageBox.question(self, "Delete Model", f"Permanently delete '{model_name}'?\nThis cannot be undone.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self._mm.delete_model(model_name):
                QMessageBox.information(self, "Deleted", f"Model '{model_name}' deleted.")
                self._refresh()
            else:
                QMessageBox.warning(self, "Error", f"Could not delete '{model_name}'.")


class ModelManagerDialog(QDialog):
    """Dialog wrapper for the Model Manager panel with Basic and Advanced tabs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Model Manager — Command Nexus(TM)")
        self.setMinimumSize(750, 650)
        self.setStyleSheet(" color: #e6edf3;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        from PyQt6.QtWidgets import QTabWidget
        from ...core.model_manager import ModelManager
        self._mm = ModelManager()

        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #30363d; } QTabBar::tab { background: #21262d; color: #8b949e; padding: 6px 16px; font-weight: bold; } QTabBar::tab:selected { background: #0064a8; color: white; }")

        self._basic_panel = ModelManagerPanel(self._mm, self)
        tabs.addTab(self._basic_panel, "Basic")

        self._advanced_panel = AdvancedModelManagerPanel(self._mm, self)
        tabs.addTab(self._advanced_panel, "Advanced")

        layout.addWidget(tabs)

        # Close button
        btn_close = QPushButton("Close")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #30363d; color: #e6edf3;
                border-radius: 4px; padding: 6px 20px; font-weight: bold;
            }
            QPushButton:hover { background-color: #424a53; }
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)
