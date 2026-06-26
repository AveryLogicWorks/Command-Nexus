"""
Zoomable Grid Canvas for the Prototyper module.
Built on QGraphicsView/QGraphicsScene for smooth zoom/pan and mouse selection.

Features:
- Zoom in/out with mouse wheel (grid squares grow/shrink)
- Pan with middle-mouse or space+drag
- Left-click drag to highlight a selection area
- Right-click for context menu
- Grid lines (horizontal + vertical) forming boxes
- Snap-to-grid when placing/editing shapes
- Multiple shape types: box, cylinder, sphere, custom
- Selection signal emitted when user highlights an area
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum, auto

from PyQt6.QtCore import Qt, QPointF, QRectF, QSizeF, pyqtSignal, QSize
from PyQt6.QtGui import (
    QPen, QBrush, QColor, QPainter, QFont, QPolygonF,
    QPainterPath, QLinearGradient, QRadialGradient
)
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsPolygonItem,
    QGraphicsPathItem, QGraphicsTextItem, QGraphicsItemGroup,
    QStyleOptionGraphicsItem, QWidget
)


# ── Shape types ──────────────────────────────────────────────────────────────

class ShapeType(Enum):
    BOX = auto()
    CYLINDER = auto()
    SPHERE = auto()
    CONE = auto()
    PYRAMID = auto()
    CUSTOM = auto()


@dataclass
class PrototypeShape:
    """Data model for a single shape on the canvas."""
    id: str
    shape_type: ShapeType
    x: float          # scene coordinates (mm)
    y: float
    z: float = 0.0
    width: float = 50.0
    height: float = 50.0
    depth: float = 50.0
    rotation: float = 0.0  # degrees around Z
    color: str = "#58a6ff"
    material: str = "PLA"
    name: str = ""
    notes: str = ""
    selected: bool = False


# ── Custom graphics items ────────────────────────────────────────────────────

class GridShapeItem(QGraphicsRectItem):
    """A selectable shape on the canvas that renders differently per type."""

    def __init__(self, shape: PrototypeShape, parent=None):
        super().__init__(shape.x, shape.y, shape.width, shape.height, parent)
        self._shape = shape
        self._update_appearance()

    def _update_appearance(self):
        c = QColor(self._shape.color)
        if self._shape.selected:
            pen = QPen(QColor("#ffd700"), 2)
            brush = QBrush(QColor(c.red(), c.green(), c.blue(), 180))
        else:
            pen = QPen(c.darker(150), 1)
            brush = QBrush(QColor(c.red(), c.green(), c.blue(), 100))
        self.setPen(pen)
        self.setBrush(brush)
        self.setRotation(self._shape.rotation)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

    @property
    def shape_data(self) -> PrototypeShape:
        return self._shape

    def paint(self, painter: QPainter, option, widget=None):
        """Override to draw shape-type-specific outlines."""
        super().paint(painter, option, widget)

        # Draw shape-type indicator
        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.setFont(QFont("Segoe UI", 7))
        label = self._shape.name or self._shape.shape_type.name.title()
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, label)

        if self._shape.shape_type == ShapeType.CYLINDER:
            painter.setPen(QPen(QColor(c := QColor(self._shape.color).lighter(140)), 1, Qt.PenStyle.DashLine))
            painter.drawEllipse(self.rect())
        elif self._shape.shape_type == ShapeType.SPHERE:
            painter.setPen(QPen(QColor(c := QColor(self._shape.color).lighter(140)), 1, Qt.PenStyle.DashLine))
            painter.drawEllipse(self.rect())
        elif self._shape.shape_type == ShapeType.CONE:
            poly = QPolygonF([
                QPointF(self.rect().left(), self.rect().bottom()),
                QPointF(self.rect().right(), self.rect().bottom()),
                QPointF(self.rect().center().x(), self.rect().top()),
            ])
            painter.setPen(QPen(QColor(self._shape.color).lighter(140), 1, Qt.PenStyle.DashLine))
            painter.drawPolygon(poly)
        elif self._shape.shape_type == ShapeType.PYRAMID:
            poly = QPolygonF([
                QPointF(self.rect().left(), self.rect().bottom()),
                QPointF(self.rect().right(), self.rect().bottom()),
                QPointF(self.rect().right(), self.rect().top()),
                QPointF(self.rect().left(), self.rect().top()),
                QPointF(self.rect().center().x(), self.rect().top() - self.rect().height() * 0.3),
                QPointF(self.rect().left(), self.rect().top()),
            ])
            painter.setPen(QPen(QColor(self._shape.color).lighter(140), 1, Qt.PenStyle.DashLine))
            painter.drawPolygon(poly)


class SelectionRectItem(QGraphicsRectItem):
    """Rubber-band selection rectangle drawn while user drags."""

    def __init__(self, rect: QRectF, parent=None):
        super().__init__(rect, parent)
        self.setPen(QPen(QColor("#58a6ff"), 2, Qt.PenStyle.DashLine))
        self.setBrush(QBrush(QColor(88, 166, 255, 30)))
        self.setZValue(1000)


# ── Grid scene ───────────────────────────────────────────────────────────────

class PrototypeScene(QGraphicsScene):
    """Custom scene that draws the grid background."""

    grid_size_changed = pyqtSignal(float)

    DEFAULT_GRID = 20.0  # mm per cell at zoom 1.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(-5000, -5000, 10000, 10000)
        self._grid_size = self.DEFAULT_GRID
        self._shapes: dict[str, GridShapeItem] = {}

    @property
    def grid_size(self) -> float:
        return self._grid_size

    @grid_size.setter
    def grid_size(self, val: float):
        self._grid_size = max(1.0, val)
        self.grid_size_changed.emit(self._grid_size)
        self.invalidate(self.sceneRect(), QGraphicsScene.SceneLayer.BackgroundLayer)

    def drawBackground(self, painter: QPainter, rect: QRectF):
        """Draw the zoomable grid."""
        painter.fillRect(rect, QColor("#0d1117"))

        gs = self._grid_size
        left = int(rect.left() // gs) * gs
        top = int(rect.top() // gs) * gs
        right = rect.right()
        bottom = rect.bottom()

        # Minor grid lines
        painter.setPen(QPen(QColor("#21262d"), 1))
        x = left
        while x < right:
            painter.drawLine(QPointF(x, top), QPointF(x, bottom))
            x += gs
        y = top
        while y < bottom:
            painter.drawLine(QPointF(left, y), QPointF(right, y))
            y += gs

        # Major grid lines (every 5 cells)
        painter.setPen(QPen(QColor("#30363d"), 1))
        x = left
        while x < right:
            painter.drawLine(QPointF(x, top), QPointF(x, bottom))
            x += gs * 5
        y = top
        while y < bottom:
            painter.drawLine(QPointF(left, y), QPointF(right, y))
            y += gs * 5

        # Origin axes
        painter.setPen(QPen(QColor("#f85149"), 2))
        painter.drawLine(QPointF(0, top), QPointF(0, bottom))
        painter.setPen(QPen(QColor("#3fb950"), 2))
        painter.drawLine(QPointF(left, 0), QPointF(right, 0))

        # Axis labels
        painter.setPen(QPen(QColor("#8b949e"), 1))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(5, -5, "0,0")

    def add_shape(self, shape: PrototypeShape) -> GridShapeItem:
        """Add a shape to the scene."""
        item = GridShapeItem(shape)
        self.addItem(item)
        self._shapes[shape.id] = item
        return item

    def remove_shape(self, shape_id: str):
        item = self._shapes.pop(shape_id, None)
        if item:
            self.removeItem(item)

    def get_shape(self, shape_id: str) -> Optional[GridShapeItem]:
        return self._shapes.get(shape_id)

    def get_all_shapes(self) -> list[PrototypeShape]:
        return [item.shape_data for item in self._shapes.values()]

    def clear_shapes(self):
        for item in list(self._shapes.values()):
            self.removeItem(item)
        self._shapes.clear()

    def snap_to_grid(self, pos: QPointF) -> QPointF:
        """Snap a position to the nearest grid intersection."""
        gs = self._grid_size
        return QPointF(round(pos.x() / gs) * gs, round(pos.y() / gs) * gs)


# ── Graphics view with zoom + pan + rubber-band select ───────────────────────

class PrototypeView(QGraphicsView):
    """
    Zoomable, pannable graphics view with rubber-band selection.

    Signals:
    - area_selected(QRectF): emitted when user drags to select an area
    - shape_selected(str):   emitted when a single shape is clicked (shape id)
    - zoom_changed(float):   emitted when zoom level changes
    """

    area_selected = pyqtSignal(QRectF)
    shape_selected = pyqtSignal(str)
    zoom_changed = pyqtSignal(float)
    context_menu_requested = pyqtSignal(QPointF)

    MIN_ZOOM = 0.1
    MAX_ZOOM = 20.0

    def __init__(self, scene: PrototypeScene, parent=None):
        super().__init__(scene, parent)
        self._scene = scene
        self._zoom = 1.0
        self._panning = False
        self._pan_start = QPointF()
        self._rubber_band: Optional[SelectionRectItem] = None
        self._rb_start = QPointF()

        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundBrush(QBrush(QColor("#0d1117")))
        self.setMouseTracking(True)

    @property
    def zoom(self) -> float:
        return self._zoom

    def set_zoom(self, factor: float):
        factor = max(self.MIN_ZOOM, min(self.MAX_ZOOM, factor))
        self._zoom = factor
        self.setTransform(__import__("PyQt6.QtGui", fromlist=["QTransform"]).QTransform.fromScale(factor, factor))
        # Adjust grid size visually
        self._scene.grid_size = PrototypeScene.DEFAULT_GRID
        self.zoom_changed.emit(factor)

    def wheelEvent(self, event):
        """Zoom in/out with mouse wheel."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y() / 1200.0
        else:
            delta = event.angleDelta().y() / 360.0
        factor = self._zoom * (1.0 + delta)
        self.set_zoom(factor)

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())

        if event.button() == Qt.MouseButton.LeftButton:
            # Check if we clicked on an item
            item = self._scene.itemAt(scene_pos, self.transform())
            if isinstance(item, GridShapeItem):
                # Deselect all, select this one
                for s in self._scene._shapes.values():
                    s.shape_data.selected = False
                    s._update_appearance()
                item.shape_data.selected = True
                item._update_appearance()
                self.shape_selected.emit(item.shape_data.id)
                super().mousePressEvent(event)
                return

            # Start rubber-band selection
            self._rb_start = scene_pos
            self._rubber_band = SelectionRectItem(QRectF(scene_pos, scene_pos))
            self._scene.addItem(self._rubber_band)
            return

        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return

        if event.button() == Qt.MouseButton.RightButton:
            self.context_menu_requested.emit(scene_pos)
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            return

        if self._rubber_band:
            scene_pos = self.mapToScene(event.pos())
            rect = QRectF(self._rb_start, scene_pos).normalized()
            self._rubber_band.setRect(rect)
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._panning:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            return

        if self._rubber_band:
            rect = self._rubber_band.rect()
            self._scene.removeItem(self._rubber_band)
            self._rubber_band = None
            if rect.width() > 5 and rect.height() > 5:
                # Select shapes within the rect
                for item in self._scene.items(rect):
                    if isinstance(item, GridShapeItem):
                        item.shape_data.selected = True
                        item._update_appearance()
                self.area_selected.emit(rect)
            return

        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().keyReleaseEvent(event)
