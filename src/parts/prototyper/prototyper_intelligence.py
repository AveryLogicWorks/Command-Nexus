# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""Prototyper Intelligence Engine — Purpose-built reasoning system."""
from __future__ import annotations
import re, math, uuid
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum, auto
from PyQt6.QtCore import QObject, pyqtSignal
from .grid_canvas import PrototypeShape, ShapeType
from .engineering_kb import (
    EngineeringKB, MATERIALS, MOTORS, BATTERIES, ESCS, PROPS,
    FASTENERS, BEARINGS, SENSORS, TOOLS,
    MaterialSpec, MotorSpec, BatterySpec, MotorType,
)
from .nlp_parser import NLPParser, Intent, ParsedInstruction, ConversationContext

class Intent(Enum):
    RESIZE = auto(); MOVE = auto(); CHANGE_MATERIAL = auto(); CHANGE_COLOR = auto()
    CHANGE_SHAPE = auto(); ADD_SHAPE = auto(); DELETE_SHAPE = auto(); ROTATE = auto()
    RENAME = auto(); RECOMMEND_MOTOR = auto(); RECOMMEND_BATTERY = auto()
    RECOMMEND_MATERIAL = auto(); RECOMMEND_ESC = auto(); RECOMMEND_PROPELLER = auto()
    AERODYNAMICS = auto(); WEIGHT_ESTIMATE = auto(); EXTERIOR_COMPLETION = auto()
    HOLLOW = auto(); FILLET = auto(); DUPLICATE = auto(); INFO = auto()
    PROJECT_SIZE = auto(); TOOLS_NEEDED = auto(); MATERIAL_QUANTITY = auto()
    RESEARCH = auto(); CORRECTION = auto(); HELP = auto(); UNKNOWN = auto()

@dataclass
class ParsedInstruction:
    intent: Intent
    raw_text: str
    params: dict = field(default_factory=dict)
    confidence: float = 1.0
    sub_intents: list = field(default_factory=list)

@dataclass
class ConversationContext:
    last_intent: Intent = Intent.UNKNOWN
    last_motor_recs: list = field(default_factory=list)
    last_material_recs: list = field(default_factory=list)
    last_battery_recs: list = field(default_factory=list)
    last_aero_result: dict = field(default_factory=dict)
    last_weight_result: dict = field(default_factory=dict)
    last_application: str = ""
    last_weight_g: float = 0.0
    history: list[str] = field(default_factory=list)
    corrections: int = 0
    def add_to_history(self, text: str):
        self.history.append(text)
        if len(self.history) > 20:
            self.history.pop(0)


class PrototyperIntelligence(QObject):
    """Purpose-built reasoning engine. No LLM needed for core logic."""
    response_ready = pyqtSignal(str)
    shape_modified = pyqtSignal(str)
    shape_added = pyqtSignal(PrototypeShape)
    shape_deleted = pyqtSignal(str)
    research_needed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.context = ConversationContext()
        self.kb = EngineeringKB()

    def process(self, text, shapes, selected):
        """Main entry: parse text, reason, execute, respond."""
        instruction = NLPParser.parse(text, self.context)
        self.context.last_intent = instruction.intent
        if instruction.sub_intents:
            return "\n\n".join(self._execute(s, shapes, selected) for s in instruction.sub_intents)
        return self._execute(instruction, shapes, selected)

    def _execute(self, inst, shapes, selected):
        i = inst.intent; p = inst.params
        handlers = {
            Intent.RESIZE: lambda: self._h_resize(p, selected),
            Intent.ADD_SHAPE: lambda: self._h_add(p, shapes),
            Intent.DELETE_SHAPE: lambda: self._h_delete(selected),
            Intent.CHANGE_MATERIAL: lambda: self._h_material(p, selected),
            Intent.CHANGE_COLOR: lambda: self._h_color(p, selected),
            Intent.ROTATE: lambda: self._h_rotate(p, selected),
            Intent.RENAME: lambda: self._h_rename(p, selected),
            Intent.DUPLICATE: lambda: self._h_dup(selected),
            Intent.HOLLOW: lambda: self._h_hollow(p, selected),
            Intent.FILLET: lambda: self._h_fillet(selected),
            Intent.RECOMMEND_MOTOR: lambda: self._h_rec_motor(p, shapes),
            Intent.RECOMMEND_BATTERY: lambda: self._h_rec_battery(p, shapes),
            Intent.RECOMMEND_MATERIAL: lambda: self._h_rec_material(p),
            Intent.RECOMMEND_ESC: lambda: self._h_rec_esc(p, shapes),
            Intent.RECOMMEND_PROPELLER: lambda: self._h_rec_prop(p),
            Intent.AERODYNAMICS: lambda: self._h_aero(p, shapes, selected),
            Intent.WEIGHT_ESTIMATE: lambda: self._h_weight(p, shapes),
            Intent.EXTERIOR_COMPLETION: lambda: self._h_exterior(p, shapes),
            Intent.PROJECT_SIZE: lambda: self._h_project_size(shapes),
            Intent.TOOLS_NEEDED: lambda: self._h_tools(p, shapes),
            Intent.MATERIAL_QUANTITY: lambda: self._h_mat_qty(p, shapes),
            Intent.HELP: lambda: self._help(),
            Intent.INFO: lambda: self._h_info(p, shapes),
            Intent.RESEARCH: lambda: self._h_research(inst.raw_text),
            Intent.UNKNOWN: lambda: self._h_unknown(inst.raw_text),
        }
        handler = handlers.get(i)
        if handler:
            return handler()
        return "I didn't understand that. Type 'help' for commands."

    @staticmethod
    def _convert_to_mm(val, unit):
        u = unit.lower()
        if u in ("mm",): return val
        if u in ("cm",): return val * 10
        if u in ("m", "meter"): return val * 1000
        if u in ("in", "inch", "inches"): return val * 25.4
        if u in ("ft", "feet", "foot"): return val * 304.8
        if u in ("um", "micron"): return val / 1000
        return val

    @staticmethod
    def _shapes_to_dicts(shapes):
        return [{"name": s.name, "width": s.width, "height": s.height,
                 "depth": getattr(s, 'depth', s.width), "material": s.material,
                 "x": s.x, "y": s.y, "shape_type": s.shape_type.name.lower()}
                for s in shapes]

    def _h_resize(self, p, sel):
        if not sel: return "Select a shape first."
        ms = p.get("measurements", [])
        d = p.get("direction"); dim = p.get("dimension")
        f = 1.5 if d == "increase" else 0.7 if d == "decrease" else 1.0
        for s in sel:
            if ms:
                v = ms[0]
                if dim == "width": s.width = self._convert_to_mm(v[0], v[1])
                elif dim == "height": s.height = self._convert_to_mm(v[0], v[1])
                elif dim == "depth": s.depth = self._convert_to_mm(v[0], v[1])
                elif len(ms) >= 3:
                    s.width = self._convert_to_mm(*ms[0]); s.height = self._convert_to_mm(*ms[1]); s.depth = self._convert_to_mm(*ms[2])
                else: v2 = self._convert_to_mm(v[0], v[1]); s.width = s.height = s.depth = v2
            elif f != 1.0: s.width *= f; s.height *= f; s.depth *= f
            self.shape_modified.emit(s.id)
        return f"Resized {len(sel)} shape(s)."

    def _h_add(self, p, shapes):
        st = p.get("shape_type", ShapeType.BOX)
        ms = p.get("measurements", [])
        if ms and len(ms) >= 3:
            w = self._convert_to_mm(*ms[0]); h = self._convert_to_mm(*ms[1]); d = self._convert_to_mm(*ms[2])
        elif ms: w = self._convert_to_mm(*ms[0]); h = w; d = w
        else: w = h = d = 40.0
        shape = PrototypeShape(id=str(uuid.uuid4())[:8], name=f"Shape {len(shapes)+1}",
            shape_type=st, x=0, y=0, width=w, height=h, depth=d, material="PLA", color="#58a6ff")
        self.shape_added.emit(shape)
        return f"Added {st.name.lower()} ({w}x{h}x{d}mm)."

    def _h_delete(self, sel):
        if not sel: return "Select shapes to delete."
        n = len(sel)
        for s in sel: self.shape_deleted.emit(s.id)
        return f"Deleted {n} shape(s)."

    def _h_material(self, p, sel):
        if not sel: return "Select a shape first."
        mat = p.get("material")
        if not mat: return f"Available: {', '.join(MATERIALS.keys())}"
        if mat not in MATERIALS: return f"Unknown '{mat}'. Available: {', '.join(MATERIALS.keys())}"
        for s in sel: s.material = mat; self.shape_modified.emit(s.id)
        m = MATERIALS[mat]
        return f"Changed to {m.name}. {m.density_g_cm3} g/cm³, {m.tensile_strength_mpa} MPa. {m.print_notes}"

    def _h_color(self, p, sel):
        if not sel: return "Select a shape first."
        c = p.get("color")
        if not c: return "Colors: red, blue, green, yellow, orange, purple, etc."
        for s in sel: s.color = c; self.shape_modified.emit(s.id)
        return f"Color → {p.get('color_name', c)}."

    def _h_rotate(self, p, sel):
        if not sel: return "Select a shape first."
        a = p.get("rotation", 90.0)
        for s in sel: s.rotation = (s.rotation + a) % 360; self.shape_modified.emit(s.id)
        return f"Rotated {a}°."

    def _h_rename(self, p, sel):
        if not sel: return "Select a shape."
        n = p.get("new_name")
        if not n: return "What name?"
        sel[0].name = n; self.shape_modified.emit(sel[0].id)
        return f"Renamed to '{n}'."

    def _h_dup(self, sel):
        if not sel: return "Select a shape."
        for s in sel:
            new = PrototypeShape(id=str(uuid.uuid4())[:8], name=s.name+" copy",
                shape_type=s.shape_type, x=s.x+20, y=s.y+20, width=s.width,
                height=s.height, depth=s.depth, material=s.material, color=s.color, rotation=s.rotation)
            self.shape_added.emit(new)
        return f"Duplicated {len(sel)} shape(s)."

    def _h_hollow(self, p, sel):
        if not sel: return "Select shapes."
        w = p.get("wall_thickness", 2.0)
        for s in sel: s.hollow = True; s.wall_thickness = w; self.shape_modified.emit(s.id)
        return f"Hollowed {len(sel)} shape(s), {w}mm walls. Weight reduction ~60-80%."

    def _h_fillet(self, sel):
        if not sel: return "Select shapes."
        for s in sel: s.fillet_radius = 3.0; self.shape_modified.emit(s.id)
        return f"3mm fillet on {len(sel)} shape(s). Reduces stress, improves aero."

    def _h_rec_motor(self, p, shapes):
        wr = self.kb.weight_estimate(self._shapes_to_dicts(shapes))
        wg = p.get("weight_g", wr["total_weight_g"] or 500)
        app = p.get("application", "drone")
        recs = self.kb.recommend_motor(wg, app)
        self.context.last_motor_recs = recs
        if not recs: return f"No motors for {app} at {wg}g."
        lines = [f"Motor recommendations ({wg}g {app}):"]
        for i, r in enumerate(recs[:5]):
            m = r["motor"]
            lines.append(f"\n{i+1}. {m.name} — ${m.cost_usd:.0f} x{r['quantity']} = ${r['total_cost']:.0f}")
            lines.append(f"   {r['reason']}")
            lines.append(f"   {m.voltage}V, {m.current_a}A, {m.rpm}RPM, {m.torque_kg_cm} kg·cm")
        return "\n".join(lines)

    def _h_rec_battery(self, p, shapes):
        wr = self.kb.weight_estimate(self._shapes_to_dicts(shapes))
        app = p.get("application", "drone")
        mrecs = self.context.last_motor_recs or self.kb.recommend_motor(wr["total_weight_g"] or 500, app)
        if not mrecs: return "Recommend motors first."
        motors = [r["motor"] for r in mrecs[:3]]
        recs = self.kb.recommend_battery(motors, 10.0, app)
        self.context.last_battery_recs = recs
        if not recs: return "No suitable batteries."
        lines = ["Battery recommendations:"]
        for i, r in enumerate(recs[:3]):
            b = r["battery"]
            lines.append(f"\n{i+1}. {b.name} — ${b.cost_usd}")
            lines.append(f"   {r['reason']}")
        return "\n".join(lines)

    def _h_rec_material(self, p):
        app = p.get("application", "prototype")
        recs = self.kb.recommend_material(app)
        self.context.last_material_recs = recs
        if not recs: return "No materials matched."
        lines = [f"Material recommendations for {app}:"]
        for i, r in enumerate(recs[:5]):
            m = r["material"]
            lines.append(f"\n{i+1}. {m.name} — ${m.cost_per_kg}/kg (score: {r['score']})")
            for reason in r["reasons"]: lines.append(f"   - {reason}")
            lines.append(f"   {m.density_g_cm3} g/cm³, {m.tensile_strength_mpa} MPa")
        return "\n".join(lines)

    def _h_rec_esc(self, p, shapes):
        wr = self.kb.weight_estimate(self._shapes_to_dicts(shapes))
        mrecs = self.context.last_motor_recs or self.kb.recommend_motor(wr["total_weight_g"] or 500, "drone")
        if not mrecs: return "Recommend motors first."
        motors = [r["motor"] for r in mrecs[:3]]
        recs = self.kb.recommend_esc(motors)
        if not recs: return "No suitable ESCs."
        lines = ["ESC recommendations:"]
        for i, r in enumerate(recs[:3]):
            e = r["esc"]
            lines.append(f"\n{i+1}. {e.name} — ${e.cost_usd:.0f} x{r['quantity']} = ${r['total_cost']:.0f}")
            lines.append(f"   {r['reason']}")
        return "\n".join(lines)

    def _h_rec_prop(self, p):
        mrecs = self.context.last_motor_recs
        if not mrecs: return "Recommend motors first."
        motor = mrecs[0]["motor"]
        app = p.get("application", "drone")
        recs = self.kb.recommend_propeller(motor, app)
        if not recs: return "No suitable propellers."
        lines = ["Propeller recommendations:"]
        for i, r in enumerate(recs[:3]):
            prop = r["prop"]
            lines.append(f"\n{i+1}. {prop.name} — ${prop.cost_usd:.0f} x{r['quantity']}")
            lines.append(f"   {r['reason']}")
        return "\n".join(lines)

    def _h_aero(self, p, shapes, sel):
        s = (sel[0] if sel else shapes[0] if shapes else None)
        if not s: return "Add shapes first."
        w, h, d = s.width, s.height, getattr(s, 'depth', s.width)
        sn = s.shape_type.name.lower()
        speed = p.get("speed", [10.0])[0] if "speed" in p else 10.0
        r = self.kb.aerodynamics_analysis(w, h, d, speed, sn)
        self.context.last_aero_result = r
        lines = [f"Aerodynamic Analysis ({w}x{h}x{d}mm at {speed}m/s):"]
        lines.append(f"  Cd: {r['drag_coefficient']} | Area: {r['frontal_area_m2']*10000:.1f}cm²")
        lines.append(f"  Drag: {r['drag_force_n']:.3f}N ({r['drag_force_g']:.1f}g)")
        lines.append(f"  Power: {r['power_required_w']:.1f}W | Re: {r['reynolds_number']:.0f}")
        if r.get("lift_force_g", 0) > 0:
            lines.append(f"  Lift: {r['lift_force_n']:.3f}N ({r['lift_force_g']:.1f}g)")
        lines.append("\nRecommendations:")
        for rec in r["recommendations"]: lines.append(f"  • {rec}")
        return "\n".join(lines)

    def _h_weight(self, p, shapes):
        if not shapes: return "Add shapes first."
        d = self._shapes_to_dicts(shapes)
        hollow = any(getattr(s, 'hollow', False) for s in shapes)
        r = self.kb.weight_estimate(d, hollow=hollow, wall_thickness_mm=p.get("wall_thickness", 2.0))
        self.context.last_weight_result = r
        self.context.last_weight_g = r["total_weight_g"]
        lines = [f"Weight: {r['total_weight_g']:.1f}g ({r['total_weight_kg']:.3f}kg)"]
        for b in r["breakdown"]:
            lines.append(f"  {b['material']}: {b['volume_cm3']:.1f}cm³ → {b['weight_g']:.1f}g")
        return "\n".join(lines)

    def _h_exterior(self, p, shapes):
        if not shapes: return "Add internal components first."
        d = self._shapes_to_dicts(shapes)
        sz = self.kb.project_size(d)
        recs = self.kb.exterior_completion(d,
            {"width": sz["width_mm"], "height": sz["height_mm"], "depth": sz["depth_mm"]},
            style=p.get("application", "functional"))
        lines = ["Exterior suggestions:"]
        for s in recs:
            lines.append(f"\n  {s['name']} ({s['shape']}, {s['material']})")
            lines.append(f"    {s['width']:.0f}x{s['height']:.0f}x{s['depth']:.0f}mm — {s['reason']}")
        return "\n".join(lines)

    def _h_project_size(self, shapes):
        if not shapes: return "No shapes yet."
        d = self._shapes_to_dicts(shapes)
        sz = self.kb.project_size(d)
        return (f"Project Size: {sz['width_mm']}x{sz['height_mm']}x{sz['depth_mm']}mm\n"
                f"  Volume: {sz['volume_cm3']}cm³ | Footprint: {sz['footprint_cm2']}cm²")

    def _h_tools(self, p, shapes):
        has_elec = any("motor" in s.name.lower() or "battery" in s.name.lower() for s in shapes)
        has_fast = len(shapes) > 1
        has_resin = any(s.material == "Resin" for s in shapes)
        recs = self.kb.tools_needed(has_electronics=has_elec, has_fasteners=has_fast,
            has_resin=has_resin, needs_finishing=True)
        lines = ["Tools needed:"]
        for r in recs:
            lines.append(f"  • {r['tool'].name} — ${r['tool'].cost_usd} ({r['reason']})")
        total = sum(r['tool'].cost_usd for r in recs)
        lines.append(f"\nTotal tool cost: ${total:.0f}")
        return "\n".join(lines)

    def _h_mat_qty(self, p, shapes):
        if not shapes: return "Add shapes first."
        d = self._shapes_to_dicts(shapes)
        r = self.kb.material_quantity(d)
        lines = [f"Material needed: {r['total_weight_g']:.1f}g ({r['filament_length_m']:.1f}m)"]
        lines.append(f"  Cost: ~${r['estimated_cost_usd']} | Print time: ~{r['estimated_print_time_h']}h")
        for b in r["breakdown"]:
            lines.append(f"  {b['name']}: {b['volume_cm3']:.1f}cm³, {b['weight_g']:.1f}g ({b['material']})")
        return "\n".join(lines)

    def _h_info(self, p, shapes):
        mat = p.get("material")
        if mat and mat in MATERIALS:
            m = MATERIALS[mat]
            return (f"{m.name}\n  Density: {m.density_g_cm3} g/cm³\n"
                    f"  Tensile: {m.tensile_strength_mpa} MPa\n  Flex: {m.flexural_strength_mpa} MPa\n"
                    f"  Cost: ${m.cost_per_kg}/kg\n  Difficulty: {m.difficulty}\n"
                    f"  Heat: {m.heat_resistant_c}°C\n  Water: {'Yes' if m.water_resistant else 'No'}\n"
                    f"  {m.description}")
        app = p.get("application")
        if app:
            return f"Application: {app}. Use 'recommend motor', 'recommend material' for specific advice."
        if shapes:
            s = shapes[0]
            return (f"Shape: {s.name}\n  Type: {s.shape_type.name}\n  Size: {s.width}x{s.height}x{getattr(s,'depth',s.width)}mm\n"
                    f"  Material: {s.material}\n  Position: ({s.x}, {s.y})\n  Rotation: {s.rotation}°")
        return "What would you like info on? Try 'info PLA' or 'info drone'."

    def _h_research(self, text):
        self.research_needed.emit(text)
        return f"Routing to web research: \"{text}\"..."

    def _h_unknown(self, text):
        return (f"I didn't understand \"{text}\". Type 'help' for commands.\n"
                f"I can: resize, add/delete shapes, change material/color, rotate, "
                f"recommend motors/batteries/ESCs/props/materials, analyze aerodynamics, "
                f"estimate weight/material, suggest tools, and more.")

    def _help(self):
        return """Available commands:
  Shapes: add box/cylinder/sphere/cone, delete, resize, rotate, duplicate, hollow, fillet
  Materials: change to PLA/ABS/PETG/TPU/Nylon/Carbon Fiber/etc.
  Recommendations: recommend motor/battery/ESC/propeller/material
  Analysis: aerodynamics, weight, project size, material quantity, tools needed
  Exterior: complete exterior (functional/aerodynamic/compact/rugged)
  Info: info [material] or info [application]
  Research: search [topic] (uses web/LLM)
  Examples:
    "add a 50mm cylinder"
    "make it wider"
    "change to carbon fiber"
    "recommend motor for drone"
    "analyze aerodynamics at 15 m/s"
    "how much material do I need"
    "what tools do I need to finish"""
