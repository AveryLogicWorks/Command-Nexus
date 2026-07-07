"""
Command Nexus — Prototyper Window

The main 3D prototyping workspace. Combines:
- Zoomable grid canvas (grid_canvas.py)
- AI assistant for natural language editing (ai_assistant.py)
- Engineering knowledge base (engineering_kb.py)
- Tool palette (add shapes, materials, colors)
- Export to STL/OBJ for 3D printing and CAD
- Properties panel for selected shape
- AI chat panel for instructions

Architecture follows the existing Command Nexus pattern:
- QMainWindow with dark theme
- Lazy instantiation from main.py
- Signal-based navigation
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal, QSize
from PyQt6.QtGui import (
    QFont, QColor, QPen, QBrush, QAction, QKeySequence, QIcon
)
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QLineEdit, QTextEdit, QListWidget,
    QListWidgetItem, QGroupBox, QFormLayout, QCheckBox, QSlider,
    QFileDialog, QMessageBox, QSplitter, QFrame,
    QDialog, QDialogButtonBox, QGridLayout, QScrollArea, QMenu,
    QToolBar, QStatusBar, QSpinBox, QDoubleSpinBox, QApplication
)

from .grid_canvas import (
    PrototypeView, PrototypeScene, PrototypeShape,
    GridShapeItem, ShapeType
)
from .ai_assistant import PrototyperAI, AICommandType
from .engineering_kb import EngineeringKB, MATERIALS, MOTORS, BATTERIES


class PrototyperWindow(QMainWindow):
    """
    Command Nexus — 3D Prototyper Workspace.

    An easy-to-use 3D model editor with AI assistance, zoomable grid,
    engineering knowledge base, and export for 3D printing / CAD.
    """

    # Signal for integration with main app
    model_exported = pyqtSignal(str)  # file path

    def __init__(self, audit_logger=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Command Nexus — Prototyper")
        self.resize(1400, 900)
        self._audit = audit_logger
        self._kb = EngineeringKB()
        self._ai = PrototyperAI(self)
        self._selection_area: tuple[float, float, float, float] | None = None
        self._current_file: Path | None = None

        self._setup_ui()
        self._connect_signals()
        self._apply_dark_theme()

    # ═══════════════════════════════════════════════════════════════════════
    # UI SETUP
    # ═══════════════════════════════════════════════════════════════════════

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # ── Toolbar ────────────────────────────────────────────────────────
        self._setup_toolbar()

        # ── Main splitter: left tools | canvas | right panels ──────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Tool palette
        left_panel = self._build_tool_palette()
        splitter.addWidget(left_panel)

        # Center: Canvas
        center_widget = self._build_canvas()
        splitter.addWidget(center_widget)

        # Right: Properties + AI Chat
        right_panel = self._build_right_panel()
        splitter.addWidget(right_panel)

        splitter.setSizes([200, 700, 400])
        main_layout.addWidget(splitter, stretch=1)

        # ── Status bar ─────────────────────────────────────────────────────
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Ready — select a tool and start creating")

    def _setup_toolbar(self):
        toolbar = QToolBar("Tools")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        # File actions
        act_new = QAction("New", self)
        act_new.setShortcut(QKeySequence.StandardKey.New)
        act_new.triggered.connect(self._new_project)
        toolbar.addAction(act_new)

        act_save = QAction("Save", self)
        act_save.setShortcut(QKeySequence.StandardKey.Save)
        act_save.triggered.connect(self._save_project)
        toolbar.addAction(act_save)

        act_load = QAction("Open", self)
        act_load.setShortcut(QKeySequence.StandardKey.Open)
        act_load.triggered.connect(self._load_project)
        toolbar.addAction(act_load)

        toolbar.addSeparator()

        # Export actions
        act_stl = QAction("Export STL", self)
        act_stl.triggered.connect(lambda: self._export_model("stl"))
        toolbar.addAction(act_stl)

        act_obj = QAction("Export OBJ", self)
        act_obj.triggered.connect(lambda: self._export_model("obj"))
        toolbar.addAction(act_obj)

        act_json = QAction("Export JSON", self)
        act_json.triggered.connect(lambda: self._export_model("json"))
        toolbar.addAction(act_json)

        toolbar.addSeparator()

        # View actions
        act_zoom_in = QAction("Zoom +", self)
        act_zoom_in.setShortcut(QKeySequence.StandardKey.ZoomIn)
        act_zoom_in.triggered.connect(self._zoom_in)
        toolbar.addAction(act_zoom_in)

        act_zoom_out = QAction("Zoom -", self)
        act_zoom_out.setShortcut(QKeySequence.StandardKey.ZoomOut)
        act_zoom_out.triggered.connect(self._zoom_out)
        toolbar.addAction(act_zoom_out)

        act_fit = QAction("Fit View", self)
        act_fit.triggered.connect(self._fit_view)
        toolbar.addAction(act_fit)

        toolbar.addSeparator()

        # Help
        act_help = QAction("Help", self)
        act_help.triggered.connect(self._show_help)
        toolbar.addAction(act_help)

    def _build_tool_palette(self) -> QWidget:
        """Build the left tool palette with shape buttons and quick actions."""
        panel = QWidget()
        panel.setMaximumWidth(220)
        panel.setMinimumWidth(180)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Title
        title = QLabel("🛠 Tools")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #58a6ff; padding-bottom: 8px;")
        layout.addWidget(title)

        # Shape buttons
        shapes_group = QGroupBox("Add Shape")
        shapes_layout = QGridLayout(shapes_group)
        shapes_layout.setSpacing(4)

        shape_buttons = [
            ("📦 Box", ShapeType.BOX),
            ("🥫 Cylinder", ShapeType.CYLINDER),
            ("⚪ Sphere", ShapeType.SPHERE),
            ("🔺 Cone", ShapeType.CONE),
            ("🔷 Pyramid", ShapeType.PYRAMID),
        ]

        for i, (label, st) in enumerate(shape_buttons):
            btn = QPushButton(label)
            btn.setStyleSheet("""
                QPushButton {
                     color: #c9d1d9;
                    border: 1px solid #30363d; border-radius: 4px;
                    padding: 8px; font-size: 12px; text-align: left;
                }
                QPushButton:hover { background-color: #30363d; }
                QPushButton:pressed { background-color: #1f6feb; color: white; }
            """)
            btn.clicked.connect(lambda checked, s=st: self._add_shape(s))
            shapes_layout.addWidget(btn, i, 0)

        layout.addWidget(shapes_group)

        # Quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setSpacing(4)

        for label, action in [
            ("🗑 Delete Selected", self._delete_selected),
            ("📋 Duplicate", self._duplicate_selected),
            ("🔄 Rotate 90°", lambda: self._rotate_selected(90)),
            ("🎨 Random Color", self._random_color),
            ("🧹 Clear All", self._clear_all),
        ]:
            btn = QPushButton(label)
            btn.setStyleSheet("""
                QPushButton {
                     color: #c9d1d9;
                    border: 1px solid #30363d; border-radius: 4px;
                    padding: 6px; font-size: 12px;
                }
                QPushButton:hover { background-color: #30363d; }
            """)
            btn.clicked.connect(action)
            actions_layout.addWidget(btn)

        layout.addWidget(actions_group)

        # Grid size control
        grid_group = QGroupBox("Grid Size")
        grid_layout = QVBoxLayout(grid_group)
        self._grid_slider = QSlider(Qt.Orientation.Horizontal)
        self._grid_slider.setMinimum(5)
        self._grid_slider.setMaximum(50)
        self._grid_slider.setValue(20)
        self._grid_slider.valueChanged.connect(self._on_grid_changed)
        grid_layout.addWidget(self._grid_slider)
        self._grid_label = QLabel("20mm")
        self._grid_label.setStyleSheet("color: #8b949e; font-size: 11px;")
        grid_layout.addWidget(self._grid_label)
        layout.addWidget(grid_group)

        # Zoom indicator
        zoom_group = QGroupBox("Zoom")
        zoom_layout = QVBoxLayout(zoom_group)
        self._zoom_label = QLabel("100%")
        self._zoom_label.setStyleSheet("color: #58a6ff; font-size: 14px; font-weight: bold;")
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        zoom_layout.addWidget(self._zoom_label)
        layout.addWidget(zoom_group)

        layout.addStretch()

        return panel

    def _build_canvas(self) -> QWidget:
        """Build the center canvas area."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Canvas label
        header = QLabel("📐 Prototyping Canvas — scroll to zoom, drag to select, right-click for menu")
        header.setStyleSheet("color: #8b949e; font-size: 11px; padding: 4px;")
        layout.addWidget(header)

        # Graphics scene + view
        self._scene = PrototypeScene()
        self._view = PrototypeView(self._scene)
        layout.addWidget(self._view, stretch=1)

        # Selection info bar
        self._selection_info = QLabel("No selection")
        self._selection_info.setStyleSheet("""
            color: #c9d1d9; font-size: 11px; padding: 4px 8px;
             border-top: 1px solid #30363d;
        """)
        layout.addWidget(self._selection_info)

        return widget

    def _build_right_panel(self) -> QWidget:
        """Build the right panel with properties and AI chat."""
        panel = QWidget()
        panel.setMaximumWidth(420)
        panel.setMinimumWidth(320)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # AI Chat section
        ai_group = QGroupBox("🤖 AI Assistant")
        ai_group.setStyleSheet("QGroupBox { color: #58a6ff; font-weight: bold; }")
        ai_layout = QVBoxLayout(ai_group)
        ai_layout.setSpacing(6)

        # AI response display
        self._ai_display = QTextEdit()
        self._ai_display.setReadOnly(True)
        self._ai_display.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._ai_display.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._ai_display.setStyleSheet("""
            QTextEdit {
                 color: #c9d1d9;
                border: 1px solid #30363d; border-radius: 6px;
                padding: 8px; font-size: 12px;
            }
        """)
        self._ai_display.setMaximumHeight(250)
        self._ai_display.setPlaceholderText(
            "Ask me anything about your prototype...\n\n"
            "Examples:\n"
            "• Make this 20mm wider\n"
            "• What motor for a 500g drone?\n"
            "• Analyze aerodynamics\n"
            "• Help me design the exterior\n"
            "• Change material to PETG"
        )
        ai_layout.addWidget(self._ai_display)

        # AI input
        ai_input_row = QHBoxLayout()
        self._ai_input = QLineEdit()
        self._ai_input.setPlaceholderText("Tell the AI what to do...")
        self._ai_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a; color: #e2e8f0;
                border: 1px solid #334155; padding: 8px;
                border-radius: 4px; font-size: 12px;
            }
            QLineEdit:focus { border-color: #58a6ff; }
        """)
        self._ai_input.returnPressed.connect(self._on_ai_submit)
        ai_input_row.addWidget(self._ai_input, stretch=1)

        self._ai_btn = QPushButton("Send")
        self._ai_btn.setStyleSheet("""
            QPushButton {
                background-color: #238636; color: white;
                border: none; border-radius: 4px;
                padding: 8px 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2ea043; }
        """)
        self._ai_btn.clicked.connect(self._on_ai_submit)
        ai_input_row.addWidget(self._ai_btn)
        ai_layout.addLayout(ai_input_row)

        # Quick AI buttons
        quick_row = QHBoxLayout()
        for label, prompt in [
            ("⚖️ Weight", "estimate the total weight"),
            ("🌪 Aero", "analyze aerodynamics"),
            ("🔧 Motor", "what motor do I need?"),
        ]:
            btn = QPushButton(label)
            btn.setStyleSheet("""
                QPushButton {
                     color: #c9d1d9;
                    border: 1px solid #30363d; border-radius: 4px;
                    padding: 4px 8px; font-size: 11px;
                }
                QPushButton:hover { background-color: #30363d; }
            """)
            btn.clicked.connect(lambda checked, p=prompt: self._quick_ai(p))
            quick_row.addWidget(btn)
        ai_layout.addLayout(quick_row)

        layout.addWidget(ai_group)

        # Properties section
        props_group = QGroupBox("📋 Properties")
        props_group.setStyleSheet("QGroupBox { color: #58a6ff; font-weight: bold; }")
        props_layout = QFormLayout(props_group)
        props_layout.setSpacing(4)

        self._prop_name = QLineEdit()
        self._prop_name.setStyleSheet(" color: #c9d1d9; border: 1px solid #30363d; padding: 4px; border-radius: 3px;")
        self._prop_name.editingFinished.connect(self._on_prop_changed)
        props_layout.addRow("Name:", self._prop_name)

        self._prop_material = QComboBox()
        self._prop_material.addItems(list(MATERIALS.keys()))
        self._prop_material.setStyleSheet(" color: #c9d1d9; border: 1px solid #30363d; padding: 4px;")
        self._prop_material.currentTextChanged.connect(self._on_prop_changed)
        props_layout.addRow("Material:", self._prop_material)

        self._prop_width = QDoubleSpinBox()
        self._prop_width.setRange(0.1, 9999)
        self._prop_width.setSuffix(" mm")
        self._prop_width.setStyleSheet(" color: #c9d1d9; border: 1px solid #30363d; padding: 4px;")
        self._prop_width.valueChanged.connect(self._on_prop_changed)
        props_layout.addRow("Width:", self._prop_width)

        self._prop_height = QDoubleSpinBox()
        self._prop_height.setRange(0.1, 9999)
        self._prop_height.setSuffix(" mm")
        self._prop_height.setStyleSheet(" color: #c9d1d9; border: 1px solid #30363d; padding: 4px;")
        self._prop_height.valueChanged.connect(self._on_prop_changed)
        props_layout.addRow("Height:", self._prop_height)

        self._prop_depth = QDoubleSpinBox()
        self._prop_depth.setRange(0.1, 9999)
        self._prop_depth.setSuffix(" mm")
        self._prop_depth.setStyleSheet(" color: #c9d1d9; border: 1px solid #30363d; padding: 4px;")
        self._prop_depth.valueChanged.connect(self._on_prop_changed)
        props_layout.addRow("Depth:", self._prop_depth)

        self._prop_rotation = QDoubleSpinBox()
        self._prop_rotation.setRange(0, 360)
        self._prop_rotation.setSuffix(" °")
        self._prop_rotation.setStyleSheet(" color: #c9d1d9; border: 1px solid #30363d; padding: 4px;")
        self._prop_rotation.valueChanged.connect(self._on_prop_changed)
        props_layout.addRow("Rotation:", self._prop_rotation)

        self._prop_color_btn = QPushButton()
        self._prop_color_btn.setStyleSheet("background-color: #58a6ff; min-height: 24px; border-radius: 4px;")
        self._prop_color_btn.clicked.connect(self._pick_color)
        props_layout.addRow("Color:", self._prop_color_btn)

        self._prop_notes = QTextEdit()
        self._prop_notes.setMaximumHeight(60)
        self._prop_notes.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._prop_notes.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._prop_notes.setStyleSheet(" color: #c9d1d9; border: 1px solid #30363d; padding: 4px; border-radius: 3px;")
        self._prop_notes.setPlaceholderText("Notes...")
        props_layout.addRow("Notes:", self._prop_notes)

        layout.addWidget(props_group)

        # Shape list
        list_group = QGroupBox("📚 Shapes")
        list_group.setStyleSheet("QGroupBox { color: #58a6ff; font-weight: bold; }")
        list_layout = QVBoxLayout(list_group)
        self._shape_list = QListWidget()
        self._shape_list.setStyleSheet(" color: #c9d1d9; border: 1px solid #30363d;")
        self._shape_list.itemClicked.connect(self._on_shape_list_clicked)
        list_layout.addWidget(self._shape_list)
        layout.addWidget(list_group)

        return panel

    # ═══════════════════════════════════════════════════════════════════════
    # SIGNAL CONNECTIONS
    # ═══════════════════════════════════════════════════════════════════════

    def _connect_signals(self):
        self._view.area_selected.connect(self._on_area_selected)
        self._view.shape_selected.connect(self._on_shape_selected)
        self._view.zoom_changed.connect(self._on_zoom_changed)
        self._view.context_menu_requested.connect(self._on_context_menu)

        self._ai.response_ready.connect(self._on_ai_response)
        self._ai.shape_modified.connect(self._on_shape_modified_by_ai)
        self._ai.shape_added.connect(self._on_shape_added_by_ai)
        self._ai.shape_deleted.connect(self._on_shape_deleted_by_ai)

    # ═══════════════════════════════════════════════════════════════════════
    # SHAPE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════

    def _add_shape(self, shape_type: ShapeType):
        """Add a new shape at the center of the current view."""
        center = self._view.mapToScene(self._view.viewport().rect().center())
        gs = self._scene.grid_size
        # Snap to grid
        x = round(center.x() / gs) * gs - 25
        y = round(center.y() / gs) * gs - 25

        shape = PrototypeShape(
            id=str(uuid.uuid4())[:8],
            shape_type=shape_type,
            x=x, y=y,
            width=50, height=50, depth=50,
            material="PLA",
            name=shape_type.name.title(),
        )
        self._scene.add_shape(shape)
        self._refresh_shape_list()
        self._select_shape(shape.id)
        self._status.showMessage(f"Added {shape_type.name.title()} shape")
        if self._audit:
            self._audit.log(tool="Prototyper", action="ADD_SHAPE",
                          target=shape_type.name, approved=True, status="info")

    def _delete_selected(self):
        shapes = self._get_selected_shapes()
        for s in shapes:
            self._scene.remove_shape(s.id)
        self._refresh_shape_list()
        self._clear_properties()
        self._status.showMessage(f"Deleted {len(shapes)} shape(s)")

    def _duplicate_selected(self):
        shapes = self._get_selected_shapes()
        for s in shapes:
            new_shape = PrototypeShape(
                id=str(uuid.uuid4())[:8],
                shape_type=s.shape_type,
                x=s.x + s.width + 10,
                y=s.y,
                z=s.z,
                width=s.width, height=s.height, depth=s.depth,
                rotation=s.rotation,
                color=s.color,
                material=s.material,
                name=f"{s.name} (copy)",
                notes=s.notes,
            )
            self._scene.add_shape(new_shape)
        self._refresh_shape_list()
        self._status.showMessage(f"Duplicated {len(shapes)} shape(s)")

    def _rotate_selected(self, angle: float):
        shapes = self._get_selected_shapes()
        for s in shapes:
            s.rotation = (s.rotation + angle) % 360
            item = self._scene.get_shape(s.id)
            if item:
                item._update_appearance()
        self._status.showMessage(f"Rotated {len(shapes)} shape(s) by {angle}°")

    def _random_color(self):
        import random
        colors = ["#f85149", "#58a6ff", "#3fb950", "#d29922", "#db6d28",
                  "#a371f7", "#39c5cf", "#f778ba", "#7ee787", "#1f6feb"]
        shapes = self._get_selected_shapes()
        for s in shapes:
            s.color = random.choice(colors)
            item = self._scene.get_shape(s.id)
            if item:
                item._update_appearance()
        self._status.showMessage(f"Changed color on {len(shapes)} shape(s)")

    def _clear_all(self):
        reply = QMessageBox.question(
            self, "Clear All",
            "Remove all shapes from the canvas?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._scene.clear_shapes()
            self._refresh_shape_list()
            self._clear_properties()
            self._status.showMessage("Canvas cleared")

    def _get_selected_shapes(self) -> list[PrototypeShape]:
        return [s for s in self._scene.get_all_shapes() if s.selected]

    def _select_shape(self, shape_id: str):
        for s in self._scene.get_all_shapes():
            s.selected = (s.id == shape_id)
            item = self._scene.get_shape(s.id)
            if item:
                item._update_appearance()
        self._update_properties()

    # ═══════════════════════════════════════════════════════════════════════
    # CANVAS EVENT HANDLERS
    # ═══════════════════════════════════════════════════════════════════════

    def _on_area_selected(self, rect: QRectF):
        """User dragged to select an area on the canvas."""
        self._selection_area = (rect.x(), rect.y(), rect.width(), rect.height())
        selected = self._get_selected_shapes()
        self._selection_info.setText(
            f"Selection: {rect.width():.0f}×{rect.height():.0f}mm at ({rect.x():.0f}, {rect.y():.0f}) — "
            f"{len(selected)} shape(s) selected"
        )
        if selected:
            self._update_properties()
        self._status.showMessage(
            f"Selected area: {rect.width():.0f}×{rect.height():.0f}mm. "
            f"Tell the AI what to do with it."
        )

    def _on_shape_selected(self, shape_id: str):
        """User clicked on a single shape."""
        self._selection_area = None
        shape = None
        for s in self._scene.get_all_shapes():
            if s.id == shape_id:
                shape = s
                break
        if shape:
            self._selection_info.setText(f"Selected: {shape.name} ({shape.shape_type.name})")
            self._update_properties()
        self._refresh_shape_list()

    def _on_zoom_changed(self, factor: float):
        self._zoom_label.setText(f"{factor*100:.0f}%")

    def _on_context_menu(self, pos: QPointF):
        """Right-click context menu on canvas."""
        menu = QMenu(self)
        menu.setStyleSheet("QMenu {  color: #c9d1d9; border: 1px solid #30363d; }")

        act_add_box = menu.addAction("Add Box Here")
        act_add_cyl = menu.addAction("Add Cylinder Here")
        menu.addSeparator()
        act_delete = menu.addAction("Delete Selected")
        act_duplicate = menu.addAction("Duplicate Selected")
        menu.addSeparator()
        act_analyze = menu.addAction("Analyze Aerodynamics")
        act_weight = menu.addAction("Estimate Weight")

        action = menu.exec(self._view.mapToGlobal(self._view.mapFromScene(pos)))

        if action == act_add_box:
            self._add_shape_at(ShapeType.BOX, pos)
        elif action == act_add_cyl:
            self._add_shape_at(ShapeType.CYLINDER, pos)
        elif action == act_delete:
            self._delete_selected()
        elif action == act_duplicate:
            self._duplicate_selected()
        elif action == act_analyze:
            self._quick_ai("analyze aerodynamics")
        elif action == act_weight:
            self._quick_ai("estimate the total weight")

    def _add_shape_at(self, shape_type: ShapeType, pos: QPointF):
        gs = self._scene.grid_size
        x = round(pos.x() / gs) * gs - 25
        y = round(pos.y() / gs) * gs - 25
        shape = PrototypeShape(
            id=str(uuid.uuid4())[:8],
            shape_type=shape_type,
            x=x, y=y,
            width=50, height=50, depth=50,
            material="PLA",
            name=shape_type.name.title(),
        )
        self._scene.add_shape(shape)
        self._refresh_shape_list()
        self._select_shape(shape.id)

    # ═══════════════════════════════════════════════════════════════════════
    # AI ASSISTANT
    # ═══════════════════════════════════════════════════════════════════════

    def _on_ai_submit(self):
        text = self._ai_input.text().strip()
        if not text:
            return
        self._ai_input.clear()
        self._ai_display.append(f"<b>You:</b> {text}")
        selected = self._get_selected_shapes()
        all_shapes = self._scene.get_all_shapes()
        self._ai.process_instruction(text, selected, all_shapes, self._selection_area)

    def _quick_ai(self, prompt: str):
        self._ai_display.append(f"<b>You:</b> {prompt}")
        selected = self._get_selected_shapes()
        all_shapes = self._scene.get_all_shapes()
        self._ai.process_instruction(prompt, selected, all_shapes, self._selection_area)

    def _on_ai_response(self, text: str):
        self._ai_display.append(f"<b>AI:</b> {text}")
        self._ai_display.append("")  # spacing

    def _on_shape_modified_by_ai(self, shape_id: str):
        item = self._scene.get_shape(shape_id)
        if item:
            item._update_appearance()
        self._refresh_shape_list()
        self._update_properties()

    def _on_shape_added_by_ai(self, shape: PrototypeShape):
        self._scene.add_shape(shape)
        self._refresh_shape_list()
        self._select_shape(shape.id)

    def _on_shape_deleted_by_ai(self, shape_id: str):
        self._scene.remove_shape(shape_id)
        self._refresh_shape_list()
        self._clear_properties()

    # ═══════════════════════════════════════════════════════════════════════
    # PROPERTIES PANEL
    # ═══════════════════════════════════════════════════════════════════════

    def _update_properties(self):
        shapes = self._get_selected_shapes()
        if not shapes:
            self._clear_properties()
            return
        s = shapes[0]  # Show first selected
        self._prop_name.blockSignals(True)
        self._prop_name.setText(s.name)
        self._prop_name.blockSignals(False)

        self._prop_material.blockSignals(True)
        idx = self._prop_material.findText(s.material)
        if idx >= 0:
            self._prop_material.setCurrentIndex(idx)
        self._prop_material.blockSignals(False)

        self._prop_width.blockSignals(True)
        self._prop_width.setValue(s.width)
        self._prop_width.blockSignals(False)

        self._prop_height.blockSignals(True)
        self._prop_height.setValue(s.height)
        self._prop_height.blockSignals(False)

        self._prop_depth.blockSignals(True)
        self._prop_depth.setValue(s.depth)
        self._prop_depth.blockSignals(False)

        self._prop_rotation.blockSignals(True)
        self._prop_rotation.setValue(s.rotation)
        self._prop_rotation.blockSignals(False)

        self._prop_color_btn.setStyleSheet(
            f"background-color: {s.color}; min-height: 24px; border-radius: 4px;"
        )

        self._prop_notes.blockSignals(True)
        self._prop_notes.setPlainText(s.notes)
        self._prop_notes.blockSignals(False)

    def _clear_properties(self):
        self._prop_name.clear()
        self._prop_width.setValue(0)
        self._prop_height.setValue(0)
        self._prop_depth.setValue(0)
        self._prop_rotation.setValue(0)
        self._prop_notes.clear()
        self._selection_info.setText("No selection")

    def _on_prop_changed(self):
        shapes = self._get_selected_shapes()
        if not shapes:
            return
        s = shapes[0]
        s.name = self._prop_name.text()
        s.material = self._prop_material.currentText()
        s.width = self._prop_width.value()
        s.height = self._prop_height.value()
        s.depth = self._prop_depth.value()
        s.rotation = self._prop_rotation.value()
        s.notes = self._prop_notes.toPlainText()
        item = self._scene.get_shape(s.id)
        if item:
            item._update_appearance()
        self._refresh_shape_list()

    def _pick_color(self):
        from PyQt6.QtWidgets import QColorDialog
        shapes = self._get_selected_shapes()
        if not shapes:
            return
        color = QColorDialog.getColor(QColor(shapes[0].color), self, "Pick Color")
        if color.isValid():
            hex_color = color.name()
            for s in shapes:
                s.color = hex_color
                item = self._scene.get_shape(s.id)
                if item:
                    item._update_appearance()
            self._prop_color_btn.setStyleSheet(
                f"background-color: {hex_color}; min-height: 24px; border-radius: 4px;"
            )

    # ═══════════════════════════════════════════════════════════════════════
    # SHAPE LIST
    # ═══════════════════════════════════════════════════════════════════════

    def _refresh_shape_list(self):
        self._shape_list.clear()
        for s in self._scene.get_all_shapes():
            label = f"{s.name} — {s.width}×{s.height}×{s.depth}mm ({s.material})"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, s.id)
            if s.selected:
                item.setBackground(QBrush(QColor("#1f6feb")))
            self._shape_list.addItem(item)

    def _on_shape_list_clicked(self, item: QListWidgetItem):
        shape_id = item.data(Qt.ItemDataRole.UserRole)
        self._select_shape(shape_id)

    # ═══════════════════════════════════════════════════════════════════════
    # VIEW CONTROLS
    # ═══════════════════════════════════════════════════════════════════════

    def _zoom_in(self):
        self._view.set_zoom(self._view.zoom * 1.25)

    def _zoom_out(self):
        self._view.set_zoom(self._view.zoom * 0.8)

    def _fit_view(self):
        shapes = self._scene.get_all_shapes()
        if not shapes:
            self._view.set_zoom(1.0)
            self._view.centerOn(QPointF(0, 0))
            return
        min_x = min(s.x for s in shapes)
        min_y = min(s.y for s in shapes)
        max_x = max(s.x + s.width for s in shapes)
        max_y = max(s.y + s.height for s in shapes)
        rect = QRectF(min_x - 50, min_y - 50, max_x - min_x + 100, max_y - min_y + 100)
        self._view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        self._on_zoom_changed(self._view.zoom)

    def _on_grid_changed(self, value: int):
        self._scene.grid_size = float(value)
        self._grid_label.setText(f"{value}mm")

    # ═══════════════════════════════════════════════════════════════════════
    # FILE OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════

    def _new_project(self):
        reply = QMessageBox.question(
            self, "New Project",
            "Create a new project? Unsaved changes will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._scene.clear_shapes()
            self._refresh_shape_list()
            self._clear_properties()
            self._current_file = None
            self._status.showMessage("New project created")

    def _save_project(self):
        if self._current_file is None:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Project", "", "Prototyper Project (*.proto.json)"
            )
            if not path:
                return
            self._current_file = Path(path)

        data = {
            "version": "1.0",
            "shapes": [
                {
                    "id": s.id, "name": s.name,
                    "shape_type": s.shape_type.name,
                    "x": s.x, "y": s.y, "z": s.z,
                    "width": s.width, "height": s.height, "depth": s.depth,
                    "rotation": s.rotation, "color": s.color,
                    "material": s.material, "notes": s.notes,
                }
                for s in self._scene.get_all_shapes()
            ]
        }
        self._current_file.write_text(json.dumps(data, indent=2))
        self._status.showMessage(f"Saved to {self._current_file.name}")

    def _load_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "Prototyper Project (*.proto.json)"
        )
        if not path:
            return
        self._current_file = Path(path)
        data = json.loads(self._current_file.read_text())
        self._scene.clear_shapes()
        for s_data in data.get("shapes", []):
            shape = PrototypeShape(
                id=s_data["id"],
                name=s_data.get("name", ""),
                shape_type=ShapeType[s_data["shape_type"]],
                x=s_data["x"], y=s_data["y"], z=s_data.get("z", 0),
                width=s_data["width"], height=s_data["height"], depth=s_data["depth"],
                rotation=s_data.get("rotation", 0),
                color=s_data.get("color", "#58a6ff"),
                material=s_data.get("material", "PLA"),
                notes=s_data.get("notes", ""),
            )
            self._scene.add_shape(shape)
        self._refresh_shape_list()
        self._fit_view()
        self._status.showMessage(f"Loaded {self._current_file.name}")

    # ═══════════════════════════════════════════════════════════════════════
    # EXPORT
    # ═══════════════════════════════════════════════════════════════════════

    def _export_model(self, format: str):
        shapes = self._scene.get_all_shapes()
        if not shapes:
            QMessageBox.warning(self, "Nothing to Export", "Add some shapes first.")
            return

        filter_map = {
            "stl": "STL 3D Print File (*.stl)",
            "obj": "OBJ 3D Model (*.obj)",
            "json": "JSON Data (*.json)",
        }
        ext_map = {"stl": ".stl", "obj": ".obj", "json": ".json"}

        path, _ = QFileDialog.getSaveFileName(
            self, f"Export {format.upper()}", "", filter_map[format]
        )
        if not path:
            return

        if not path.endswith(ext_map[format]):
            path += ext_map[format]

        try:
            if format == "stl":
                self._export_stl(path)
            elif format == "obj":
                self._export_obj(path)
            elif format == "json":
                self._export_json(path)

            self._status.showMessage(f"Exported to {Path(path).name}")
            self.model_exported.emit(path)
            if self._audit:
                self._audit.log(tool="Prototyper", action="EXPORT",
                              target=format.upper(), approved=True, status="info")
            QMessageBox.information(self, "Export Complete",
                                    f"Model exported to:\n{path}\n\n"
                                    f"Format: {format.upper()}\n"
                                    f"Shapes: {len(shapes)}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export: {e}")

    def _export_stl(self, path: str):
        """Export shapes as a simple STL file (ASCII format)."""
        lines = ["solid prototyper_export"]
        for s in self._scene.get_all_shapes():
            x, y = s.x, s.y
            w, h, d = s.width, s.height, s.depth
            z = getattr(s, 'z', 0)

            # Define 8 vertices of a box
            v = [
                (x, y, z), (x+w, y, z), (x+w, y+h, z), (x, y+h, z),
                (x, y, z+d), (x+w, y, z+d), (x+w, y+h, z+d), (x, y+h, z+d),
            ]

            # 12 triangles (2 per face × 6 faces)
            faces = [
                (0, 1, 2), (0, 2, 3),  # bottom
                (4, 6, 5), (4, 7, 6),  # top
                (0, 5, 1), (0, 4, 5),  # front
                (2, 6, 7), (2, 7, 3),  # back
                (1, 5, 6), (1, 6, 2),  # right
                (0, 3, 7), (0, 7, 4),  # left
            ]

            for tri in faces:
                # Calculate normal
                p0, p1, p2 = v[tri[0]], v[tri[1]], v[tri[2]]
                ux, uy, uz = p1[0]-p0[0], p1[1]-p0[1], p1[2]-p0[2]
                vx, vy, vz = p2[0]-p0[0], p2[1]-p0[1], p2[2]-p0[2]
                nx = uy*vz - uz*vy
                ny = uz*vx - ux*vz
                nz = ux*vy - uy*vx
                length = (nx*nx + ny*ny + nz*nz) ** 0.5
                if length > 0:
                    nx, ny, nz = nx/length, ny/length, nz/length

                lines.append(f"  facet normal {nx:.6f} {ny:.6f} {nz:.6f}")
                lines.append("    outer loop")
                lines.append(f"      vertex {p0[0]:.6f} {p0[1]:.6f} {p0[2]:.6f}")
                lines.append(f"      vertex {p1[0]:.6f} {p1[1]:.6f} {p1[2]:.6f}")
                lines.append(f"      vertex {p2[0]:.6f} {p2[1]:.6f} {p2[2]:.6f}")
                lines.append("    endloop")
                lines.append("  endfacet")

        lines.append("endsolid prototyper_export")
        Path(path).write_text("\n".join(lines))

    def _export_obj(self, path: str):
        """Export shapes as a simple OBJ file."""
        lines = ["# Prototyper Export"]
        vertex_count = 0

        for s in self._scene.get_all_shapes():
            x, y = s.x, s.y
            w, h, d = s.width, s.height, s.depth
            z = getattr(s, 'z', 0)
            name = s.name or s.shape_type.name

            lines.append(f"o {name}")

            # 8 vertices
            verts = [
                (x, y, z), (x+w, y, z), (x+w, y+h, z), (x, y+h, z),
                (x, y, z+d), (x+w, y, z+d), (x+w, y+h, z+d), (x, y+h, z+d),
            ]
            for vx, vy, vz in verts:
                lines.append(f"v {vx:.6f} {vy:.6f} {vz:.6f}")

            # Faces (1-indexed)
            base = vertex_count + 1
            faces = [
                (1, 2, 3, 4),    # bottom
                (5, 8, 7, 6),    # top
                (1, 5, 6, 2),    # front
                (3, 7, 8, 4),    # back
                (2, 6, 7, 3),    # right
                (1, 4, 8, 5),    # left
            ]
            for f in faces:
                lines.append(f"f {base+f[0]-1} {base+f[1]-1} {base+f[2]-1} {base+f[3]-1}")

            vertex_count += 8
            lines.append("")

        Path(path).write_text("\n".join(lines))

    def _export_json(self, path: str):
        """Export as structured JSON with all shape data."""
        data = {
            "version": "1.0",
            "application": "Command Nexus Prototyper",
            "shapes": [
                {
                    "id": s.id, "name": s.name,
                    "shape_type": s.shape_type.name,
                    "position": {"x": s.x, "y": s.y, "z": getattr(s, 'z', 0)},
                    "dimensions": {"width": s.width, "height": s.height, "depth": s.depth},
                    "rotation": s.rotation,
                    "color": s.color,
                    "material": s.material,
                    "notes": s.notes,
                }
                for s in self._scene.get_all_shapes()
            ]
        }
        Path(path).write_text(json.dumps(data, indent=2))

    # ═══════════════════════════════════════════════════════════════════════
    # HELP & THEME
    # ═══════════════════════════════════════════════════════════════════════

    def _show_help(self):
        help_text = """
        <h2 style="color: #58a6ff;">Command Nexus Prototyper — Help</h2>

        <h3 style="color: #c9d1d9;">Getting Started</h3>
        <p>Click a shape button on the left to add it to the canvas.
        Use the mouse wheel to zoom in and out. Middle-click drag to pan.</p>

        <h3 style="color: #c9d1d9;">Selecting</h3>
        <p>Click on a shape to select it. Drag to draw a selection box around multiple shapes.
        Right-click for a context menu.</p>

        <h3 style="color: #c9d1d9;">AI Assistant</h3>
        <p>Type instructions in the AI panel (bottom right). Examples:</p>
        <ul>
            <li><b>"Make this 20mm wider"</b> — resizes selected shape</li>
            <li><b>"Change material to PETG"</b> — changes material</li>
            <li><b>"Add a cylinder here, 30mm tall"</b> — adds shape at selection</li>
            <li><b>"What motor for a 500g drone?"</b> — engineering recommendation</li>
            <li><b>"Analyze aerodynamics"</b> — drag analysis of selected shape</li>
            <li><b>"Help me design the exterior"</b> — suggests shell around components</li>
            <li><b>"Estimate weight"</b> — total weight from all shapes</li>
        </ul>

        <h3 style="color: #c9d1d9;">Export</h3>
        <p>Use <b>Export STL</b> for 3D printing, <b>Export OBJ</b> for CAD import,
        or <b>Export JSON</b> for data exchange.</p>

        <h3 style="color: #c9d1d9;">Keyboard Shortcuts</h3>
        <ul>
            <li><b>Ctrl+N</b> — New project</li>
            <li><b>Ctrl+S</b> — Save project</li>
            <li><b>Ctrl+O</b> — Open project</li>
            <li><b>Ctrl++</b> — Zoom in</li>
            <li><b>Ctrl+-</b> — Zoom out</li>
        </ul>
        """
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Prototyper Help")
        dlg.setText(help_text)
        dlg.setTextFormat(Qt.TextFormat.RichText)
        dlg.exec()

    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {  }
            QWidget { color: #c9d1d9; }
            QGroupBox {
                border: 1px solid #30363d; border-radius: 6px;
                margin-top: 12px; padding-top: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 10px;
                padding: 0 4px;
            }
            QPushButton {
                 color: #c9d1d9;
                border: 1px solid #30363d; border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #30363d; }
            QPushButton:pressed { background-color: #1f6feb; }
            QToolBar {  border-bottom: 1px solid #30363d; }
            QToolBar QToolButton { color: #c9d1d9; }
            QListWidget {
                 color: #c9d1d9;
                border: 1px solid #30363d;
            }
            QStatusBar {  color: #8b949e; }
            QScrollBar:vertical { border: none; background: #0d1117; width: 8px; }
            QScrollBar::handle:vertical { background: #30363d; border-radius: 4px; }
            QScrollBar:horizontal { border: none; background: #0d1117; height: 8px; }
            QScrollBar::handle:horizontal { background: #30363d; border-radius: 4px; }
            QLabel { color: #c9d1d9; }
            QComboBox {  color: #c9d1d9; border: 1px solid #30363d; padding: 4px; }
            QDoubleSpinBox, QSpinBox {  color: #c9d1d9; border: 1px solid #30363d; padding: 4px; }
        """)
