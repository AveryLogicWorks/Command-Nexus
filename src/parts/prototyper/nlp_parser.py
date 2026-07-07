# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""NLP parser for prototyper — deep natural language understanding without LLM."""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from .grid_canvas import ShapeType


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


class NLPParser:
    _UNIT_RE = re.compile(r'(\d+\.?\d*)\s*(mm|cm|m|meter|in|inch|inches|ft|feet|foot|um|micron)\b', re.I)
    _WIDTH_RE = re.compile(r'\b(width|wide|wider|narrow|breadth|across)\b', re.I)
    _HEIGHT_RE = re.compile(r'\b(height|tall|taller|short|high)\b', re.I)
    _DEPTH_RE = re.compile(r'\b(depth|deep|thick|thin|length|long|longer)\b', re.I)
    _ROT_RE = re.compile(r'(\d+\.?\d*)\s*(?:degrees?|deg|°)\b', re.I)
    _WEIGHT_RE = re.compile(r'(\d+\.?\d*)\s*(g|gram|kg|kilogram|lb|lbs|pound|oz|ounce)\b', re.I)
    _SPEED_RE = re.compile(r'(\d+\.?\d*)\s*(rpm|rpms|m/s|mph|kph|km/h|fps)\b', re.I)
    _CORRECTION_RE = re.compile(r'\b(no|wrong|actually|instead|not that|i meant|rather|correct|fix)\b', re.I)
    _APP_PATTERNS = {
        'drone': re.compile(r'\b(drone|quadcopter|quad|uav|multicopter|hexacopter|tricopter)\b', re.I),
        'robot_car': re.compile(r'\b(robot car|rover|rc car|robot vehicle|autonomous car|bot car)\b', re.I),
        'robotic_arm': re.compile(r'\b(robotic arm|robot arm|arm|gripper|manipulator|servo arm)\b', re.I),
        'boat': re.compile(r'\b(boat|ship|watercraft|marine|submarine|rover underwater)\b', re.I),
        'plane': re.compile(r'\b(plane|airplane|aircraft|glider|wing|fixed wing|rc plane)\b', re.I),
        'rocket': re.compile(r'\b(rocket|missile|thrust|propulsion)\b', re.I),
        'cnc': re.compile(r'\b(cnc|mill|router|engraver|spindle)\b', re.I),
        '3d_printer': re.compile(r'\b(3d printer|printer|extruder|hotend|print bed)\b', re.I),
        'wearable': re.compile(r'\b(wearable|helmet|bracelet|watch case|band)\b', re.I),
        'enclosure': re.compile(r'\b(enclosure|case|housing|box|container|cabinet|shell)\b', re.I),
        'gear': re.compile(r'\b(gear|gearbox|transmission|sprocket|pulley)\b', re.I),
        'fixture': re.compile(r'\b(fixture|jig|mount|bracket|clamp|holder|stand)\b', re.I),
    }
    _INTENT_PATTERNS = [
        (Intent.RECOMMEND_MOTOR, re.compile(r'\b(motor|propulsion|thrust|drive|actuator)\b.*\b(recommend|suggest|what|which|need|best|pick|choose|find)\b', re.I), 0.9),
        (Intent.RECOMMEND_MOTOR, re.compile(r'\b(recommend|suggest|what|which|need|best|pick|choose|find)\b.*\b(motor|propulsion|thrust|drive|actuator)\b', re.I), 0.9),
        (Intent.RECOMMEND_MOTOR, re.compile(r'\b(what|which|need)\b.*\b(motor|propulsion|thrust)\b', re.I), 0.9),
        (Intent.RECOMMEND_BATTERY, re.compile(r'\b(battery|power source|power supply|cell|lipo|li-ion)\b.*\b(recommend|suggest|what|which|need|best|pick)\b', re.I), 0.9),
        (Intent.RECOMMEND_BATTERY, re.compile(r'\b(recommend|suggest|what|which|need|best|pick)\b.*\b(battery|power source|power supply|cell|lipo|li-ion)\b', re.I), 0.9),
        (Intent.RECOMMEND_BATTERY, re.compile(r'\b(what|which|need)\b.*\b(battery|power|cell)\b', re.I), 0.9),
        (Intent.RECOMMEND_ESC, re.compile(r'\b(esc|electronic speed control|speed controller)\b.*\b(recommend|suggest|what|which|need|best)\b', re.I), 0.9),
        (Intent.RECOMMEND_ESC, re.compile(r'\b(recommend|suggest|what|which|need|best)\b.*\b(esc|electronic speed control|speed controller)\b', re.I), 0.9),
        (Intent.RECOMMEND_PROPELLER, re.compile(r'\b(prop|propeller|blade)\b.*\b(recommend|suggest|what|which|need|best|size)\b', re.I), 0.9),
        (Intent.RECOMMEND_PROPELLER, re.compile(r'\b(recommend|suggest|what|which|need|best|size)\b.*\b(prop|propeller|blade)\b', re.I), 0.9),
        (Intent.RECOMMEND_MATERIAL, re.compile(r'\b(material|filament|plastic|metal|wood)\b.*\b(recommend|suggest|what|which|best|should i)\b', re.I), 0.85),
        (Intent.RECOMMEND_MATERIAL, re.compile(r'\b(recommend|suggest|what|which|best|should i)\b.*\b(material|filament|plastic|metal|wood)\b', re.I), 0.85),
        (Intent.AERODYNAMICS, re.compile(r'\b(aerodynamics?|aero|drag|wind resistance|airflow|streamline|wind tunnel|cd|drag coefficient|lift)\b', re.I), 0.9),
        (Intent.WEIGHT_ESTIMATE, re.compile(r'\b(weight|weigh|mass|heavy|light|lighter|heavier|how much.*weigh)\b', re.I), 0.85),
        (Intent.EXTERIOR_COMPLETION, re.compile(r'\b(exterior|shell|skin|cover|enclose|wrap|finish.*outside|complete.*outside|complete.*model|body|fuselage|fairing)\b', re.I), 0.85),
        (Intent.HOLLOW, re.compile(r'\b(hollow|shell|thin wall|wall thickness|hollow out|empty inside|reduce material)\b', re.I), 0.85),
        (Intent.FILLET, re.compile(r'\b(fillet|round.*edge|chamfer|bevel|smooth.*corner|round.*corner)\b', re.I), 0.85),
        (Intent.PROJECT_SIZE, re.compile(r'\b(project size|overall size|total size|dimensions|how big|footprint|build volume|print volume)\b', re.I), 0.85),
        (Intent.TOOLS_NEEDED, re.compile(r'\b(tools|tool|equipment|what do i need|what.*need.*build|what.*need.*finish|what.*need.*make)\b', re.I), 0.8),
        (Intent.MATERIAL_QUANTITY, re.compile(r'\b(how much material|material.*need|filament.*need|how much.*filament|material.*quantity|amount of material)\b', re.I), 0.85),
        (Intent.RESIZE, re.compile(r'\b(resize|bigger|smaller|larger|wider|narrower|taller|shorter|thicker|thinner|longer|scale|enlarge|shrink|grow|reduce.*size|increase.*size)\b', re.I), 0.85),
        (Intent.ADD_SHAPE, re.compile(r'\b(add|create|new|make|insert|place|put)\b.*\b(box|cube|cylinder|tube|sphere|ball|cone|pyramid|shape|part|component|object|piece)\b', re.I), 0.8),
        (Intent.DELETE_SHAPE, re.compile(r'\b(delete|remove|get rid of|clear|erase|drop)\b', re.I), 0.8),
        (Intent.ROTATE, re.compile(r'\b(rotate|turn|spin|angle|tilt|orient|orientation)\b', re.I), 0.8),
        (Intent.CHANGE_MATERIAL, re.compile(r'\b(change|switch|set|use|make it).*(material|filament|plastic|pla|abs|petg|tpu|nylon|resin|aluminum|carbon|wood|metal)\b', re.I), 0.8),
        (Intent.CHANGE_COLOR, re.compile(r'\b(color|colour|paint|red|blue|green|yellow|orange|purple|black|white|gray|grey|pink|brown|cyan|magenta)\b', re.I), 0.7),
        (Intent.DUPLICATE, re.compile(r'\b(duplicate|copy|clone|repeat|mirror)\b', re.I), 0.85),
        (Intent.RENAME, re.compile(r'\b(rename|call it|name it|label)\b', re.I), 0.85),
        (Intent.MOVE, re.compile(r'\b(move|shift|reposition|place at|center|align|position)\b', re.I), 0.75),
        (Intent.CORRECTION, re.compile(r'\b(no wrong|not that|i meant|actually|instead of|rather than|correction|no,|wrong,)\b', re.I), 0.75),
        (Intent.HELP, re.compile(r'\b(help|how do i|what can you|guide|tutorial|instructions|manual)\b', re.I), 0.7),
        (Intent.RESEARCH, re.compile(r'\b(search|look up|research|find online|google|web|internet|browse)\b', re.I), 0.7),
        (Intent.INFO, re.compile(r'\b(what is|tell me about|info|information|details|specs|specifications|explain)\b', re.I), 0.6),
    ]
    _SHAPE_MAP = {
        'box': ShapeType.BOX, 'cube': ShapeType.BOX, 'block': ShapeType.BOX,
        'cylinder': ShapeType.CYLINDER, 'tube': ShapeType.CYLINDER, 'rod': ShapeType.CYLINDER,
        'sphere': ShapeType.SPHERE, 'ball': ShapeType.SPHERE, 'dome': ShapeType.SPHERE,
        'cone': ShapeType.CONE, 'funnel': ShapeType.CONE,
        'pyramid': ShapeType.PYRAMID, 'wedge': ShapeType.PYRAMID,
    }
    _MATERIAL_ALIASES = {
        'pla': 'PLA', 'abs': 'ABS', 'petg': 'PETG', 'tpu': 'TPU',
        'nylon': 'Nylon', 'resin': 'Resin', 'aluminum': 'Aluminum',
        'aluminium': 'Aluminum', 'carbon': 'Carbon Fiber', 'carbon fiber': 'Carbon Fiber',
        'carbon fibre': 'Carbon Fiber', 'wood': 'Wood PLA', 'wood pla': 'Wood PLA',
    }
    _COLOR_MAP = {
        'red': '#f85149', 'blue': '#58a6ff', 'green': '#3fb950',
        'yellow': '#d29922', 'orange': '#db6d28', 'purple': '#a371f7',
        'black': '#1f2328', 'white': '#f0f6fc', 'gray': '#8b949e',
        'grey': '#8b949e', 'pink': '#f778ba', 'brown': '#8957e0',
        'cyan': '#39c5cf', 'magenta': '#db61a2',
    }

    @classmethod
    def parse(cls, text: str, context: ConversationContext) -> ParsedInstruction:
        text_lower = text.lower().strip()
        context.add_to_history(text)
        if cls._CORRECTION_RE.search(text_lower):
            return cls._parse_correction(text, text_lower, context)
        app = cls._detect_application(text_lower)
        if app:
            context.last_application = app
        intent = Intent.UNKNOWN
        confidence = 0.0
        for matched_intent, pattern, conf in cls._INTENT_PATTERNS:
            if pattern.search(text_lower):
                intent = matched_intent
                confidence = conf
                break
        if intent == Intent.UNKNOWN:
            sub_intents = cls._parse_compound(text, text_lower, context)
            if sub_intents:
                return ParsedInstruction(intent=sub_intents[0].intent, raw_text=text,
                    params=sub_intents[0].params, confidence=0.7, sub_intents=sub_intents)
            return ParsedInstruction(intent=Intent.UNKNOWN, raw_text=text, confidence=0.0)
        params = cls._extract_params(intent, text, text_lower, context)
        return ParsedInstruction(intent=intent, raw_text=text, params=params, confidence=confidence)

    @classmethod
    def _parse_correction(cls, text, text_lower, context):
        context.corrections += 1
        cleaned = cls._CORRECTION_RE.sub('', text_lower).strip()
        if cleaned:
            old_hist = context.history[:]
            context.history = []
            result = cls.parse(cleaned, context)
            context.history = old_hist + context.history
            result.params['is_correction'] = True
            result.params['previous_intent'] = context.last_intent
            return result
        return ParsedInstruction(intent=Intent.CORRECTION, raw_text=text,
            params={'is_correction': True}, confidence=0.6)

    @classmethod
    def _parse_compound(cls, text, text_lower, context):
        parts = re.split(r'\b(and|then|also|after that|,)\b', text_lower)
        if len(parts) <= 1:
            return []
        sub_intents = []
        for part in parts:
            part = part.strip()
            if not part or part in ('and', 'then', 'also', 'after that', ',', ''):
                continue
            for matched_intent, pattern, conf in cls._INTENT_PATTERNS:
                if pattern.search(part):
                    params = cls._extract_params(matched_intent, part, part, context)
                    sub_intents.append(ParsedInstruction(
                        intent=matched_intent, raw_text=part, params=params, confidence=conf))
                    break
        return sub_intents

    @classmethod
    def _detect_application(cls, text_lower: str) -> str:
        for app, pattern in cls._APP_PATTERNS.items():
            if pattern.search(text_lower):
                return app
        return ""

    @classmethod
    def _extract_params(cls, intent, text, text_lower, context) -> dict:
        params = {}
        # Units
        units = cls._UNIT_RE.findall(text_lower)
        if units:
            params['measurements'] = [(float(v), u.lower()) for v, u in units]
        # Rotation
        rot = cls._ROT_RE.search(text_lower)
        if rot:
            params['rotation'] = float(rot.group(1))
        # Weight
        weight = cls._WEIGHT_RE.search(text_lower)
        if weight:
            val, unit = float(weight.group(1)), weight.group(2).lower()
            if unit in ('kg', 'kilogram'): val *= 1000
            elif unit in ('lb', 'lbs', 'pound'): val *= 453.592
            elif unit in ('oz', 'ounce'): val *= 28.3495
            params['weight_g'] = val
        # Speed
        speed = cls._SPEED_RE.search(text_lower)
        if speed:
            params['speed'] = (float(speed.group(1)), speed.group(2).lower())
        # Shape type
        for alias, st in cls._SHAPE_MAP.items():
            if alias in text_lower:
                params['shape_type'] = st
                break
        # Material
        for alias, material in cls._MATERIAL_ALIASES.items():
            if alias in text_lower:
                params['material'] = material
                break
        # Color
        for color_name, hex_val in cls._COLOR_MAP.items():
            if color_name in text_lower:
                params['color'] = hex_val
                params['color_name'] = color_name
                break
        # Dimension direction
        if cls._WIDTH_RE.search(text_lower):
            params['dimension'] = 'width'
        elif cls._HEIGHT_RE.search(text_lower):
            params['dimension'] = 'height'
        elif cls._DEPTH_RE.search(text_lower):
            params['dimension'] = 'depth'
        # Relative size words
        if re.search(r'\b(bigger|larger|wider|taller|thicker|longer|enlarge|grow|increase)\b', text_lower):
            params['direction'] = 'increase'
        elif re.search(r'\b(smaller|narrower|shorter|thinner|shrink|reduce|decrease)\b', text_lower):
            params['direction'] = 'decrease'
        # Application
        app = cls._detect_application(text_lower)
        if app:
            params['application'] = app
        elif context.last_application:
            params['application'] = context.last_application
        # Wall thickness for hollow
        wall_match = re.search(r'(\d+\.?\d*)\s*mm.*wall', text_lower)
        if wall_match:
            params['wall_thickness'] = float(wall_match.group(1))
        # Name extraction
        name_match = re.search(r'\b(?:call it|name it|rename to|label as)\s+[\'"]?([^\'"]+)[\'"]?', text_lower)
        if name_match:
            params['new_name'] = name_match.group(1).strip()
        # "this" / "that" / "selected" — context reference
        if re.search(r'\b(this|that|it|selected|these|those)\b', text_lower):
            params['refers_to_selection'] = True
        return params
