"""
AI Assistant for the Prototyper module.

Interprets natural language instructions from the user and applies
edits to shapes on the canvas. Also provides engineering recommendations
using the EngineeringKB.

Examples of what the AI can understand:
- "Make this part 20mm wider"
- "Change the material to PETG"
- "Add a cylinder here that's 30mm tall"
- "What motor do I need for a 500g drone?"
- "Help me design the exterior for my robot"
- "Analyze the aerodynamics of this shape"
- "Round the edges of this box"
- "Make this hollow with 2mm walls"
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Optional
from enum import Enum, auto

from PyQt6.QtCore import QObject, pyqtSignal

from .grid_canvas import PrototypeShape, ShapeType
from .engineering_kb import EngineeringKB, MATERIALS, MOTORS, BATTERIES


class AICommandType(Enum):
    RESIZE = auto()
    MOVE = auto()
    CHANGE_MATERIAL = auto()
    CHANGE_COLOR = auto()
    CHANGE_SHAPE = auto()
    ADD_SHAPE = auto()
    DELETE_SHAPE = auto()
    ROTATE = auto()
    RENAME = auto()
    RECOMMEND_MOTOR = auto()
    RECOMMEND_BATTERY = auto()
    RECOMMEND_MATERIAL = auto()
    AERODYNAMICS = auto()
    WEIGHT_ESTIMATE = auto()
    EXTERIOR_COMPLETION = auto()
    HOLLOW = auto()
    FILLET = auto()
    DUPLICATE = auto()
    INFO = auto()
    UNKNOWN = auto()


@dataclass
class AICommand:
    """Parsed AI command from user text."""
    command_type: AICommandType
    raw_text: str
    params: dict
    response: str = ""


class PrototyperAI(QObject):
    """
    AI assistant that parses natural language and applies edits.
    Emits signals when shapes should be modified or when text responses are ready.
    """

    # Signals for UI to act on
    shape_modified = pyqtSignal(str)  # shape_id
    shape_added = pyqtSignal(PrototypeShape)
    shape_deleted = pyqtSignal(str)
    response_ready = pyqtSignal(str)  # text response to display
    analysis_ready = pyqtSignal(dict)  # structured analysis result

    def __init__(self, parent=None):
        super().__init__(parent)
        self._kb = EngineeringKB()

    def process_instruction(
        self,
        text: str,
        selected_shapes: list[PrototypeShape],
        all_shapes: list[PrototypeShape],
        selection_area: tuple[float, float, float, float] | None = None,
    ) -> AICommand:
        """
        Parse a natural language instruction and execute it.

        Args:
            text: User's instruction text
            selected_shapes: Currently selected shapes
            all_shapes: All shapes on canvas
            selection_area: (x, y, w, h) of rubber-band selection if any

        Returns:
            AICommand with results
        """
        text_lower = text.lower().strip()
        cmd = self._parse(text_lower, text, selected_shapes, all_shapes, selection_area)

        if cmd.command_type == AICommandType.UNKNOWN:
            cmd.response = (
                "I didn't understand that. Try things like:\n"
                "• \"Make this 20mm wider\"\n"
                "• \"Change material to PETG\"\n"
                "• \"Add a cylinder here, 30mm tall\"\n"
                "• \"What motor for a 500g drone?\"\n"
                "• \"Analyze aerodynamics\"\n"
                "• \"Help me design the exterior\"\n"
                "• \"Make this hollow with 2mm walls\""
            )
            self.response_ready.emit(cmd.response)
            return cmd

        # Execute the command
        self._execute(cmd, selected_shapes, all_shapes)
        return cmd

    def _parse(
        self,
        text_lower: str,
        original: str,
        selected: list[PrototypeShape],
        all_shapes: list[PrototypeShape],
        selection_area: tuple | None,
    ) -> AICommand:
        """Parse text into a command."""

        # ── Resize ─────────────────────────────────────────────────────────
        resize_match = re.search(
            r"(?:make|set|change|resize|shrink|enlarge|grow).*?"
            r"(?:this|it|that|the|selected)?\s*"
            r"(?:(width|w|wide|wider|breadth)|"
            r"(height|h|tall|taller)|"
            r"(depth|d|deep|deeper|thick|thicker|length|long|longer))?\s*"
            r"(?:to|=)?\s*(\d+(?:\.\d+)?)\s*(mm|cm)?",
            text_lower
        )
        if resize_match and any(k in text_lower for k in ["wider", "taller", "deeper", "thicker",
                                                            "longer", "resize", "shrink", "enlarge",
                                                            "width", "height", "depth", "make", "set"]):
            dimension = resize_match.group(1) or resize_match.group(2) or resize_match.group(3)
            value = float(resize_match.group(4))
            unit = resize_match.group(5)
            if unit == "cm":
                value *= 10

            dim_map = {
                "width": "width", "w": "width", "wide": "width", "wider": "width", "breadth": "width",
                "height": "height", "h": "height", "tall": "height", "taller": "height",
                "depth": "depth", "d": "depth", "deep": "depth", "deeper": "depth",
                "thick": "depth", "thicker": "depth", "length": "depth", "long": "depth", "longer": "depth",
            }
            dim_name = dim_map.get(dimension, "width")

            # Check for relative changes ("wider by 10mm" or "10mm wider")
            if "by" in text_lower or (any(w in text_lower for w in ["wider", "taller", "deeper", "thicker", "longer"]) and "to" not in text_lower):
                relative = value
            else:
                relative = None

            return AICommand(
                AICommandType.RESIZE, original,
                {"dimension": dim_name, "value": value, "relative": relative}
            )

        # ── Change material ────────────────────────────────────────────────
        for mat_name in MATERIALS:
            if mat_name.lower() in text_lower and any(k in text_lower for k in ["material", "change", "switch", "use", "print"]):
                return AICommand(
                    AICommandType.CHANGE_MATERIAL, original,
                    {"material": mat_name}
                )

        # ── Change color ───────────────────────────────────────────────────
        color_match = re.search(r"(?:color|colour|paint)\s+(?:to\s+)?(?:#)?([0-9a-f]{6}|red|blue|green|yellow|orange|purple|white|black|gray|grey|cyan|magenta|pink|lime|teal|navy|coral|gold)", text_lower)
        if color_match:
            color_val = color_match.group(1)
            color_map = {
                "red": "#f85149", "blue": "#58a6ff", "green": "#3fb950",
                "yellow": "#d29922", "orange": "#db6d28", "purple": "#a371f7",
                "white": "#ffffff", "black": "#000000", "gray": "#8b949e",
                "grey": "#8b949e", "cyan": "#39c5cf", "magenta": "#f778ba",
                "pink": "#f778ba", "lime": "#7ee787", "teal": "#39c5cf",
                "navy": "#1f6feb", "coral": "#f85149", "gold": "#d29922",
            }
            if color_val in color_map:
                color = color_map[color_val]
            elif len(color_val) == 6:
                color = f"#{color_val}"
            else:
                color = "#58a6ff"
            return AICommand(AICommandType.CHANGE_COLOR, original, {"color": color})

        # ── Add shape ──────────────────────────────────────────────────────
        add_match = re.search(
            r"(?:add|create|place|put|make|new)\s+(?:a\s+)?"
            r"(box|cube|cylinder|cylinder|circle|sphere|ball|cone|pyramid|triangle)\s*"
            r"(?:here|there|at center)?\s*"
            r"(?:(\d+(?:\.\d+)?)\s*(?:x|by)\s*)?"
            r"(?:(\d+(?:\.\d+)?)\s*(?:x|by)\s*)?"
            r"(?:(\d+(?:\.\d+)?)\s*(?:mm|cm)?)?",
            text_lower
        )
        if add_match:
            shape_word = add_match.group(1)
            shape_map = {
                "box": ShapeType.BOX, "cube": ShapeType.BOX,
                "cylinder": ShapeType.CYLINDER, "circle": ShapeType.CYLINDER,
                "sphere": ShapeType.SPHERE, "ball": ShapeType.SPHERE,
                "cone": ShapeType.CONE, "pyramid": ShapeType.PYRAMID,
                "triangle": ShapeType.CONE,
            }
            shape_type = shape_map.get(shape_word, ShapeType.BOX)

            dims = [add_match.group(2), add_match.group(3), add_match.group(4)]
            dims = [float(d) if d else None for d in dims]
            w = dims[0] or 50.0
            h = dims[1] or w
            d = dims[2] or w

            # Position: use selection area center or origin
            if selection_area:
                x = selection_area[0] + selection_area[2] / 2 - w / 2
                y = selection_area[1] + selection_area[3] / 2 - h / 2
            else:
                x = 0
                y = 0

            return AICommand(
                AICommandType.ADD_SHAPE, original,
                {"shape_type": shape_type, "x": x, "y": y, "width": w, "height": h, "depth": d}
            )

        # ── Delete ─────────────────────────────────────────────────────────
        if any(k in text_lower for k in ["delete", "remove", "erase", "get rid of"]) and not "material" in text_lower:
            return AICommand(AICommandType.DELETE_SHAPE, original, {})

        # ── Rotate ─────────────────────────────────────────────────────────
        rot_match = re.search(r"(?:rotate|turn|spin)\s+(?:this|it|the)?\s*(?:by\s+)?(\d+(?:\.\d+)?)\s*(?:degrees?|deg)?", text_lower)
        if rot_match:
            angle = float(rot_match.group(1))
            return AICommand(AICommandType.ROTATE, original, {"angle": angle})

        # ── Rename ─────────────────────────────────────────────────────────
        rename_match = re.search(r"(?:rename|name|call)\s+(?:this|it|the)?\s*(?:to\s+)?[\"']?([^\"']+?)[\"']?$", text_lower)
        if rename_match:
            return AICommand(AICommandType.RENAME, original, {"name": rename_match.group(1).strip()})

        # ── Hollow ─────────────────────────────────────────────────────────
        hollow_match = re.search(r"(?:hollow|shell|empty|hollow out)\s*(?:this|it|the)?\s*(?:(\d+(?:\.\d+)?)\s*mm\s*walls?)?", text_lower)
        if hollow_match:
            wall = float(hollow_match.group(1)) if hollow_match.group(1) else 2.0
            return AICommand(AICommandType.HOLLOW, original, {"wall_thickness": wall})

        # ── Fillet / Round edges ───────────────────────────────────────────
        if any(k in text_lower for k in ["fillet", "round edge", "round corner", "bevel", "chamfer", "smooth edge"]):
            radius_match = re.search(r"(\d+(?:\.\d+)?)\s*mm", text_lower)
            radius = float(radius_match.group(1)) if radius_match else 3.0
            return AICommand(AICommandType.FILLET, original, {"radius": radius})

        # ── Duplicate ──────────────────────────────────────────────────────
        if any(k in text_lower for k in ["duplicate", "copy", "clone", "make another"]):
            return AICommand(AICommandType.DUPLICATE, original, {})

        # ── Recommend motor ────────────────────────────────────────────────
        if any(k in text_lower for k in ["motor", "propeller", "thrust"]):
            weight_match = re.search(r"(\d+(?:\.\d+)?)\s*(g|gram|kg|kilo|lb|pound)", text_lower)
            weight_g = 500.0
            if weight_match:
                weight_g = float(weight_match.group(1))
                unit = weight_match.group(2)
                if unit in ("kg", "kilo"):
                    weight_g *= 1000
                elif unit in ("lb", "pound"):
                    weight_g *= 453.6

            app = "drone"
            if "car" in text_lower or "robot" in text_lower and "arm" not in text_lower:
                app = "robot_car"
            elif "arm" in text_lower:
                app = "robotic_arm"
            elif "plane" in text_lower or "airplane" in text_lower or "aircraft" in text_lower:
                app = "rc_plane"

            return AICommand(AICommandType.RECOMMEND_MOTOR, original, {"weight_g": weight_g, "application": app})

        # ── Recommend battery ──────────────────────────────────────────────
        if "battery" in text_lower or "power source" in text_lower:
            time_match = re.search(r"(\d+(?:\.\d+)?)\s*(min|minute|hour|hr)", text_lower)
            flight_time = 10.0
            if time_match:
                flight_time = float(time_match.group(1))
                if time_match.group(2) in ("hour", "hr"):
                    flight_time *= 60

            return AICommand(AICommandType.RECOMMEND_BATTERY, original, {"flight_time_min": flight_time})

        # ── Recommend material ─────────────────────────────────────────────
        if "material" in text_lower and any(k in text_lower for k in ["recommend", "best", "which", "what", "should i use", "suggest"]):
            outdoor = "outdoor" in text_lower or "water" in text_lower or "weather" in text_lower
            flexible = "flex" in text_lower or "rubber" in text_lower or "bend" in text_lower
            high_detail = "detail" in text_lower or "smooth" in text_lower or "miniature" in text_lower
            return AICommand(AICommandType.RECOMMEND_MATERIAL, original,
                             {"outdoor": outdoor, "flexible": flexible, "high_detail": high_detail})

        # ── Aerodynamics ───────────────────────────────────────────────────
        if any(k in text_lower for k in ["aerodynamic", "drag", "wind", "airflow", "streamline", "lift"]):
            return AICommand(AICommandType.AERODYNAMICS, original, {})

        # ── Weight estimate ────────────────────────────────────────────────
        if any(k in text_lower for k in ["weight", "weigh", "mass", "how heavy", "total weight"]):
            return AICommand(AICommandType.WEIGHT_ESTIMATE, original, {})

        # ── Exterior completion ────────────────────────────────────────────
        if any(k in text_lower for k in ["exterior", "shell", "enclosure", "housing", "case", "body", "finish the", "complete the"]):
            style = "functional"
            if "aero" in text_lower or "streamline" in text_lower:
                style = "aerodynamic"
            elif "compact" in text_lower or "small" in text_lower or "tight" in text_lower:
                style = "compact"
            elif "rugged" in text_lower or "tough" in text_lower or "durable" in text_lower or "drop" in text_lower:
                style = "rugged"
            return AICommand(AICommandType.EXTERIOR_COMPLETION, original, {"style": style})

        # ── Info ───────────────────────────────────────────────────────────
        if any(k in text_lower for k in ["info", "details", "properties", "specs", "tell me about", "what is"]):
            return AICommand(AICommandType.INFO, original, {})

        return AICommand(AICommandType.UNKNOWN, original, {})

    def _execute(
        self,
        cmd: AICommand,
        selected: list[PrototypeShape],
        all_shapes: list[PrototypeShape],
    ):
        """Execute the parsed command on the selected shapes."""

        if cmd.command_type == AICommandType.RESIZE:
            dim = cmd.params["dimension"]
            val = cmd.params["value"]
            rel = cmd.params.get("relative")

            if not selected:
                cmd.response = "Select a shape first, then tell me how to resize it."
                self.response_ready.emit(cmd.response)
                return

            for shape in selected:
                if rel is not None:
                    current = getattr(shape, dim)
                    setattr(shape, dim, current + rel)
                else:
                    setattr(shape, dim, val)
                self.shape_modified.emit(shape.id)

            action = "increased" if (rel and rel > 0) or (not rel) else "decreased"
            cmd.response = f"✅ {len(selected)} shape(s) {action} {dim} to {val}mm"
            if rel:
                cmd.response = f"✅ {len(selected)} shape(s) {dim} changed by {rel}mm"
            self.response_ready.emit(cmd.response)

        elif cmd.command_type == AICommandType.CHANGE_MATERIAL:
            mat = cmd.params["material"]
            if not selected:
                cmd.response = "Select a shape first, then tell me which material to use."
                self.response_ready.emit(cmd.response)
                return
            for shape in selected:
                shape.material = mat
                self.shape_modified.emit(shape.id)
            spec = MATERIALS[mat]
            cmd.response = f"✅ Material changed to {mat}.\n📄 {spec.description}\n🖨 Print temp: {spec.print_temp_c[0]}-{spec.print_temp_c[1]}°C\n💰 Cost: ${spec.cost_per_kg}/kg"
            self.response_ready.emit(cmd.response)

        elif cmd.command_type == AICommandType.CHANGE_COLOR:
            color = cmd.params["color"]
            if not selected:
                cmd.response = "Select a shape first, then tell me the color."
                self.response_ready.emit(cmd.response)
                return
            for shape in selected:
                shape.color = color
                self.shape_modified.emit(shape.id)
            cmd.response = f"✅ Color changed to {color}"
            self.response_ready.emit(cmd.response)

        elif cmd.command_type == AICommandType.ADD_SHAPE:
            p = cmd.params
            shape = PrototypeShape(
                id=str(uuid.uuid4())[:8],
                shape_type=p["shape_type"],
                x=p["x"], y=p["y"],
                width=p["width"], height=p["height"], depth=p["depth"],
                material="PLA",
                name=p["shape_type"].name.title(),
            )
            self.shape_added.emit(shape)
            cmd.response = f"✅ Added {p['shape_type'].name.lower()} ({p['width']}×{p['height']}×{p['depth']}mm)"
            self.response_ready.emit(cmd.response)

        elif cmd.command_type == AICommandType.DELETE_SHAPE:
            if not selected:
                cmd.response = "Select a shape to delete first."
                self.response_ready.emit(cmd.response)
                return
            for shape in selected:
                self.shape_deleted.emit(shape.id)
            cmd.response = f"✅ Deleted {len(selected)} shape(s)"
            self.response_ready.emit(cmd.response)

        elif cmd.command_type == AICommandType.ROTATE:
            angle = cmd.params["angle"]
            if not selected:
                cmd.response = "Select a shape to rotate first."
                self.response_ready.emit(cmd.response)
                return
            for shape in selected:
                shape.rotation = (shape.rotation + angle) % 360
                self.shape_modified.emit(shape.id)
            cmd.response = f"✅ Rotated {len(selected)} shape(s) by {angle}°"
            self.response_ready.emit(cmd.response)

        elif cmd.command_type == AICommandType.RENAME:
            name = cmd.params["name"]
            if not selected:
                cmd.response = "Select a shape to rename first."
                self.response_ready.emit(cmd.response)
                return
            for shape in selected:
                shape.name = name
                self.shape_modified.emit(shape.id)
            cmd.response = f"✅ Renamed to '{name}'"
            self.response_ready.emit(cmd.response)

        elif cmd.command_type == AICommandType.HOLLOW:
            wall = cmd.params["wall_thickness"]
            if not selected:
                cmd.response = "Select a shape to hollow out first."
                self.response_ready.emit(cmd.response)
                return
            for shape in selected:
                shape.notes = f"Hollow, wall={wall}mm"
                self.shape_modified.emit(shape.id)
            # Weight savings estimate
            cmd.response = f"✅ Marked {len(selected)} shape(s) as hollow with {wall}mm walls.\n💡 This reduces material usage by ~60-80% depending on size."
            self.response_ready.emit(cmd.response)

        elif cmd.command_type == AICommandType.FILLET:
            radius = cmd.params["radius"]
            if not selected:
                cmd.response = "Select a shape to round edges first."
                self.response_ready.emit(cmd.response)
                return
            for shape in selected:
                shape.notes = f"Fillet r={radius}mm"
                self.shape_modified.emit(shape.id)
            cmd.response = f"✅ Rounded edges with {radius}mm radius on {len(selected)} shape(s).\n💡 Rounded edges improve print quality and reduce stress concentrations."
            self.response_ready.emit(cmd.response)

        elif cmd.command_type == AICommandType.DUPLICATE:
            if not selected:
                cmd.response = "Select a shape to duplicate first."
                self.response_ready.emit(cmd.response)
                return
            for shape in selected:
                new_shape = PrototypeShape(
                    id=str(uuid.uuid4())[:8],
                    shape_type=shape.shape_type,
                    x=shape.x + shape.width + 10,
                    y=shape.y,
                    z=shape.z,
                    width=shape.width, height=shape.height, depth=shape.depth,
                    rotation=shape.rotation,
                    color=shape.color,
                    material=shape.material,
                    name=f"{shape.name} (copy)",
                    notes=shape.notes,
                )
                self.shape_added.emit(new_shape)
            cmd.response = f"✅ Duplicated {len(selected)} shape(s)"
            self.response_ready.emit(cmd.response)

        elif cmd.command_type == AICommandType.RECOMMEND_MOTOR:
            weight = cmd.params["weight_g"]
            app = cmd.params["application"]
            results = self._kb.recommend_motor(weight, application=app)

            if not results:
                cmd.response = f"No suitable motors found for a {weight}g {app}. Try adjusting your requirements."
            else:
                lines = [f"🔧 Motor Recommendations for {weight}g {app.replace('_', ' ')}:\n"]
                for i, r in enumerate(results[:5]):
                    m = r["motor"]
                    lines.append(f"{i+1}. **{m.name}** — ${m.cost_usd:.2f} each (×{r['quantity']} = ${r['total_cost']:.2f})")
                    lines.append(f"   {r['reason']}")
                    lines.append(f"   Specs: {m.voltage}V, {m.rpm}RPM, {m.torque_kg_cm}kg·cm torque, {m.power_w}W")
                    lines.append("")
                lines.append("💡 Tip: Always use an ESC (Electronic Speed Controller) with brushless motors.")
                cmd.response = "\n".join(lines)
            self.response_ready.emit(cmd.response)

        elif cmd.command_type == AICommandType.RECOMMEND_BATTERY:
            flight_time = cmd.params["flight_time_min"]
            # Use selected shapes to estimate weight, then recommend
            weight_data = self._kb.weight_estimate([
                {"width": s.width, "height": s.height, "depth": s.depth, "material": s.material}
                for s in all_shapes
            ])
            total_weight = weight_data["total_weight_g"]

            # Get motor recommendations first to know power draw
            motor_results = self._kb.recommend_motor(total_weight, application="drone")
            if motor_results:
                motors = [motor_results[0]["motor"]] * motor_results[0]["quantity"]
            else:
                motors = list(MOTORS.values())[:4]

            results = self._kb.recommend_battery(motors, flight_time_min=flight_time)

            if not results:
                cmd.response = f"No suitable batteries found for {flight_time}min runtime."
            else:
                lines = [f"🔋 Battery Recommendations for ~{flight_time}min runtime:\n"]
                lines.append(f"Estimated total weight: {total_weight:.0f}g\n")
                for i, r in enumerate(results[:3]):
                    b = r["battery"]
                    lines.append(f"{i+1}. **{b.name}** — ${b.cost_usd:.2f}")
                    lines.append(f"   {r['reason']}")
                    lines.append(f"   Specs: {b.voltage}V, {b.capacity_mah}mAh, {b.weight_g}g")
                    lines.append("")
                cmd.response = "\n".join(lines)
            self.response_ready.emit(cmd.response)

        elif cmd.command_type == AICommandType.RECOMMEND_MATERIAL:
            results = self._kb.recommend_material(
                outdoor=cmd.params["outdoor"],
                flexible=cmd.params["flexible"],
                high_detail=cmd.params["high_detail"],
            )
            if not results:
                cmd.response = "No materials matched your requirements."
            else:
                lines = ["🧪 Material Recommendations:\n"]
                for i, r in enumerate(results[:5]):
                    m = r["material"]
                    lines.append(f"{i+1}. **{m.name}** — ${m.cost_per_kg}/kg (Difficulty: {m.difficulty})")
                    for reason in r["reasons"]:
                        lines.append(f"   • {reason}")
                    lines.append(f"   Density: {m.density_g_cm3} g/cm³, Tensile: {m.tensile_strength_mpa} MPa")
                    lines.append("")
                cmd.response = "\n".join(lines)
            self.response_ready.emit(cmd.response)

        elif cmd.command_type == AICommandType.AERODYNAMICS:
            if not selected:
                cmd.response = "Select a shape to analyze its aerodynamics."
                self.response_ready.emit(cmd.response)
                return
            shape = selected[0]
            result = self._kb.aerodynamics_analysis(
                width_mm=shape.width,
                height_mm=shape.height,
                depth_mm=shape.depth,
                shape=shape.shape_type.name.lower(),
            )
            lines = [
                f"🌪 Aerodynamics Analysis for '{shape.name}':\n",
                f"Shape: {shape.shape_type.name.title()}",
                f"Dimensions: {shape.width}×{shape.height}×{shape.depth}mm",
                f"Drag Coefficient (Cd): {result['drag_coefficient']:.2f}",
                f"Frontal Area: {result['frontal_area_m2']*10000:.1f} cm²",
                f"Drag Force @ 10m/s: {result['drag_force_n']:.2f} N",
                f"Power Required: {result['power_required_w']:.1f} W",
                f"Reynolds Number: {result['reynolds_number']:.0f}",
                "",
                "Recommendations:",
            ]
            for rec in result["recommendations"]:
                lines.append(f"  • {rec}")
            cmd.response = "\n".join(lines)
            self.response_ready.emit(cmd.response)
            self.analysis_ready.emit(result)

        elif cmd.command_type == AICommandType.WEIGHT_ESTIMATE:
            shape_dicts = [
                {"width": s.width, "height": s.height, "depth": s.depth, "material": s.material}
                for s in all_shapes
            ]
            result = self._kb.weight_estimate(shape_dicts)
            lines = [
                "⚖️ Weight Estimate:\n",
                f"Total Weight: {result['total_weight_g']:.1f}g ({result['total_weight_kg']:.3f}kg)",
                "",
                "Breakdown:",
            ]
            for item in result["breakdown"]:
                lines.append(f"  • {item['material']}: {item['volume_cm3']:.1f}cm³ → {item['weight_g']:.1f}g")

            if result["total_weight_g"] > 0:
                lines.append("")
                # Quick motor recommendation
                motor_recs = self._kb.recommend_motor(result["total_weight_g"])
                if motor_recs:
                    m = motor_recs[0]["motor"]
                    lines.append(f"💡 For this weight, consider: {m.name} ({m.cost_usd:.2f} each)")

            cmd.response = "\n".join(lines)
            self.response_ready.emit(cmd.response)

        elif cmd.command_type == AICommandType.EXTERIOR_COMPLETION:
            style = cmd.params["style"]
            existing = [
                {"name": s.name, "width": s.width, "height": s.height, "depth": s.depth,
                 "x": s.x, "y": s.y}
                for s in all_shapes
            ]
            suggestions = self._kb.exterior_completion(existing, {}, style=style)

            if not suggestions:
                cmd.response = "Add some internal components first, then I can help design the exterior around them."
            else:
                lines = [f"🏗 Exterior Design Suggestions ({style} style):\n"]
                for sug in suggestions:
                    lines.append(f"• **{sug['name']}** ({sug['shape']}, {sug['material']})")
                    lines.append(f"  Size: {sug['width']:.0f}×{sug['height']:.0f}×{sug['depth']:.0f}mm")
                    lines.append(f"  {sug['reason']}")
                    lines.append("")
                lines.append("💡 I can add these shapes to your canvas automatically. Click 'Apply Suggestions' below.")
                cmd.response = "\n".join(lines)
            self.response_ready.emit(cmd.response)

        elif cmd.command_type == AICommandType.INFO:
            if not selected:
                cmd.response = "Select a shape to see its properties."
                self.response_ready.emit(cmd.response)
                return
            shape = selected[0]
            mat = MATERIALS.get(shape.material, MATERIALS["PLA"])
            lines = [
                f"📋 Shape Properties — '{shape.name}':\n",
                f"Type: {shape.shape_type.name.title()}",
                f"Position: ({shape.x:.1f}, {shape.y:.1f})",
                f"Size: {shape.width}×{shape.height}×{shape.depth}mm",
                f"Rotation: {shape.rotation}°",
                f"Color: {shape.color}",
                f"Material: {mat.name}",
                f"  Density: {mat.density_g_cm3} g/cm³",
                f"  Tensile: {mat.tensile_strength_mpa} MPa",
                f"  Print temp: {mat.print_temp_c[0]}-{mat.print_temp_c[1]}°C",
                f"  Cost: ${mat.cost_per_kg}/kg",
            ]
            if shape.notes:
                lines.append(f"Notes: {shape.notes}")

            # Weight of this single shape
            vol_cm3 = (shape.width * shape.height * shape.depth) / 1000
            weight_g = vol_cm3 * mat.density_g_cm3
            lines.append(f"Estimated weight: {weight_g:.1f}g")

            cmd.response = "\n".join(lines)
            self.response_ready.emit(cmd.response)
