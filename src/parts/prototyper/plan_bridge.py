# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""
Plan Bridge — connects the Forge (planning layer) to the Prototyper (implementation layer).

The Forge creates plans and Hephaestus briefs. This module defines the shared data format
and provides utilities to convert them into Prototyper-compatible instructions.

Plan JSON format:
{
    "source": "hephaestus_relay" | "planner",
    "title": "Project name",
    "goal": "What we're building",
    "constraints": "Materials, scale, budget, unknowns",
    "application": "drone" | "robot" | "rocket" | etc,
    "components": [
        {"type": "box", "name": "Frame", "width": 100, "height": 50, "depth": 30, "material": "PLA"},
        ...
    ],
    "recommendations": [
        "recommend motor for drone",
        "recommend battery",
        ...
    ],
    "tasks": [
        {"description": "Build frame", "status": "pending"},
        ...
    ],
    "metadata": {
        "ai_name": "Name of the AI that created this plan",
        "ai_uuid": "UUID",
        "created": "2026-07-01T08:00:00",
    }
}
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class PlanComponent:
    """A single component in a plan."""
    type: str = "box"  # box, cylinder, sphere, cone, pyramid
    name: str = ""
    width: float = 50.0
    height: float = 50.0
    depth: float = 50.0
    material: str = "PLA"
    notes: str = ""


@dataclass
class PlanTask:
    """A task in a plan."""
    description: str = ""
    status: str = "pending"  # pending, in_progress, done
    assigned_to: str = ""


@dataclass
class PrototypePlan:
    """A structured plan that can be sent from the Forge to the Prototyper."""
    source: str = "planner"  # hephaestus_relay or planner
    title: str = ""
    goal: str = ""
    constraints: str = ""
    application: str = ""
    manufacturing: str = "3d_print"  # 3d_print, cnc, either
    components: list[PlanComponent] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    tasks: list[PlanTask] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_json(self) -> str:
        d = asdict(self)
        return json.dumps(d, indent=2, ensure_ascii=False)

    @staticmethod
    def from_json(text: str) -> PrototypePlan:
        d = json.loads(text)
        components = [PlanComponent(**c) for c in d.get("components", [])]
        tasks = [PlanTask(**t) for t in d.get("tasks", [])]
        return PrototypePlan(
            source=d.get("source", "planner"),
            title=d.get("title", ""),
            goal=d.get("goal", ""),
            constraints=d.get("constraints", ""),
            application=d.get("application", ""),
            manufacturing=d.get("manufacturing", "3d_print"),
            components=components,
            recommendations=d.get("recommendations", []),
            tasks=tasks,
            metadata=d.get("metadata", {}),
        )

    def save(self, path: Path):
        path.write_text(self.to_json(), encoding="utf-8")

    @staticmethod
    def load(path: Path) -> PrototypePlan:
        return PrototypePlan.from_json(path.read_text(encoding="utf-8"))


class HephaestusBriefParser:
    """
    Parses a Hephaestus Relay handoff brief into a PrototypePlan.
    Extracts design goal, constraints, materials, scale, and suggested components.
    """

    # Shape keywords → shape types
    _SHAPE_KEYWORDS = {
        "frame": "box", "body": "box", "chassis": "box", "base": "box",
        "enclosure": "box", "case": "box", "housing": "box", "mount": "box",
        "arm": "box", "bracket": "box", "plate": "box",
        "fuselage": "box", "boom": "cylinder", "tail": "box",
        "wing": "box", "fin": "box", "rudder": "box", "elevator": "box",
        "aileron": "box", "flap": "box", "skid": "box", "strut": "cylinder",
        "wheel": "cylinder", "tube": "cylinder", "rod": "cylinder",
        "axle": "cylinder", "spool": "cylinder", "drum": "cylinder",
        "sprocket": "cylinder", "rotor": "cylinder", "propeller": "cylinder",
        "hull": "box", "keel": "box", "deck": "box",
        "dome": "sphere", "ball": "sphere", "canopy": "sphere",
        "nose cone": "cone", "tip": "cone", "funnel": "cone",
        "pyramid": "pyramid", "wedge": "pyramid",
        "gear": "cylinder", "hub": "cylinder", "bearing mount": "box",
        "leg": "cylinder", "foot": "box", "joint": "sphere",
        "gripper": "box", "claw": "box", "end effector": "box",
        "skirt": "box", "envelope": "sphere", "ballast": "cylinder",
        "track": "box", "link": "box",
    }

    # Application keywords — ordered by specificity (most specific first)
    _APP_KEYWORDS = {
        "hexacopter": "drone", "octocopter": "drone",
        "quadcopter": "drone", "drone": "drone", "uav": "drone",
        "vtol": "vtol", "tilt-rotor": "vtol", "tilt rotor": "vtol",
        "ornithopter": "ornithopter", "flapping": "ornithopter",
        "airplane": "airplane", "fixed-wing": "airplane", "fixed wing": "airplane",
        "glider": "glider", "sailplane": "glider",
        "helicopter": "helicopter", "heli": "helicopter",
        "hovercraft": "hovercraft", "surface effect": "hovercraft",
        "blimp": "blimp", "airship": "blimp",
        "rocket": "rocket", "missile": "rocket",
        "submarine": "submarine", "rov": "submarine", "underwater": "submarine",
        "boat": "boat", "hull": "boat", "watercraft": "boat", "jet ski": "boat",
        "amphibious": "amphibious",
        "tracked": "tracked", "tank": "tracked",
        "walker": "walker", "legged": "walker", "hexapod": "walker", "biped": "walker", "quadruped": "walker",
        "robot": "robot", "rover": "robot", "bot": "robot",
        "robotic arm": "robotic_arm", "manipulator": "robotic_arm",
        "cnc": "cnc", "mill": "cnc", "router": "cnc",
        "wearable": "wearable", "helmet": "wearable",
        "enclosure": "enclosure", "case": "enclosure",
        "wind tunnel": "wind_tunnel",
        "sensor pod": "sensor_pod", "sensor station": "sensor_pod",
        "gear": "mechanism", "gearbox": "mechanism", "mechanism": "mechanism",
    }

    # Material keywords
    _MATERIAL_KEYWORDS = {
        "pla": "PLA", "abs": "ABS", "petg": "PETG", "tpu": "TPU",
        "nylon": "Nylon", "resin": "Resin", "aluminum": "Aluminum",
        "carbon": "Carbon Fiber", "carbon fiber": "Carbon Fiber",
        "wood": "Wood PLA", "steel": "Steel", "titanium": "Titanium",
        "foam": "Foam", "balsa": "Balsa", "asa": "ASA",
    }

    @classmethod
    def parse(cls, goal: str, constraints: str, ai_name: str = "", ai_uuid: str = "") -> PrototypePlan:
        """Parse a Hephaestus brief into a structured plan."""
        combined = f"{goal} {constraints}".lower()

        # Detect application — use word boundary to avoid substring matches
        application = ""
        for keyword, app in cls._APP_KEYWORDS.items():
            if re.search(r'\b' + re.escape(keyword) + r'\b', combined):
                application = app
                break

        # Detect manufacturing method
        manufacturing = "3d_print"  # default
        if re.search(r'\bcnc\b', combined) or re.search(r'\bmachin', combined):
            if re.search(r'\b3d\b', combined) or re.search(r'\bprint', combined):
                manufacturing = "either"
            else:
                manufacturing = "cnc"
        elif re.search(r'\baluminum\b', combined) or re.search(r'\bsteel\b', combined) or re.search(r'\btitanium\b', combined):
            manufacturing = "either"  # metals often need CNC

        # Detect materials
        materials_found = []
        for keyword, mat in cls._MATERIAL_KEYWORDS.items():
            if keyword in combined:
                materials_found.append(mat)
        primary_material = materials_found[0] if materials_found else "PLA"

        # Extract dimensions (e.g., "100mm", "50 cm", "2 inches")
        dim_pattern = re.compile(r'(\d+\.?\d*)\s*(mm|cm|m|in|inch|inches|ft|feet)\b', re.I)
        dimensions = []
        for match in dim_pattern.finditer(combined):
            val = float(match.group(1))
            unit = match.group(2).lower()
            if unit in ("cm",):
                val *= 10
            elif unit in ("m", "meter"):
                val *= 1000
            elif unit in ("in", "inch", "inches"):
                val *= 25.4
            elif unit in ("ft", "feet", "foot"):
                val *= 304.8
            dimensions.append(val)

        # Detect components from keywords — use word boundary matching
        components = []
        for keyword, shape_type in cls._SHAPE_KEYWORDS.items():
            if re.search(r'\b' + re.escape(keyword) + r'\b', combined):
                w = dimensions[0] if len(dimensions) > 0 else 50.0
                h = dimensions[1] if len(dimensions) > 1 else 50.0
                d = dimensions[2] if len(dimensions) > 2 else w
                components.append(PlanComponent(
                    type=shape_type,
                    name=keyword.title(),
                    width=w, height=h, depth=d,
                    material=primary_material,
                ))

        # If no components detected, create a default base
        if not components:
            w = dimensions[0] if dimensions else 100.0
            h = dimensions[1] if len(dimensions) > 1 else 50.0
            d = dimensions[2] if len(dimensions) > 2 else 30.0
            components.append(PlanComponent(
                type="box", name="Base Frame",
                width=w, height=h, depth=d,
                material=primary_material,
            ))

        # Generate recommendations based on application
        recommendations = []
        _APP_RECS = {
            "drone": [
                "recommend motor for drone",
                "recommend battery",
                "recommend esc",
                "recommend propeller",
                "analyze aerodynamics at 15 m/s",
            ],
            "vtol": [
                "recommend motor for drone",
                "recommend battery",
                "recommend esc",
                "recommend propeller",
                "analyze aerodynamics at 20 m/s",
                "estimate weight",
            ],
            "ornithopter": [
                "recommend motor for drone",
                "recommend battery",
                "recommend bearings",
                "analyze aerodynamics at 8 m/s",
                "estimate weight",
            ],
            "airplane": [
                "recommend motor for drone",
                "recommend battery",
                "recommend propeller",
                "recommend bearings",
                "analyze aerodynamics at 25 m/s",
                "estimate weight",
            ],
            "glider": [
                "analyze aerodynamics at 15 m/s",
                "estimate weight",
                "recommend bearings",
            ],
            "helicopter": [
                "recommend motor for drone",
                "recommend battery",
                "recommend esc",
                "recommend bearings",
                "analyze aerodynamics at 20 m/s",
                "estimate weight",
            ],
            "hovercraft": [
                "recommend motor for drone",
                "recommend battery",
                "recommend esc",
                "recommend propeller",
                "estimate weight",
            ],
            "blimp": [
                "recommend motor for drone",
                "recommend battery",
                "estimate weight",
            ],
            "rocket": [
                "recommend motor for rocket",
                "analyze aerodynamics at 100 m/s",
                "estimate weight",
            ],
            "submarine": [
                "recommend motor for robot",
                "recommend battery",
                "recommend seals",
                "estimate weight",
            ],
            "boat": [
                "recommend motor for drone",
                "recommend battery",
                "recommend bearings",
                "estimate weight",
            ],
            "amphibious": [
                "recommend motor for robot",
                "recommend battery",
                "recommend bearings",
                "recommend seals",
                "estimate weight",
            ],
            "tracked": [
                "recommend motor for robot",
                "recommend battery",
                "recommend bearings",
                "estimate weight",
            ],
            "walker": [
                "recommend motor for robot",
                "recommend battery",
                "recommend sensors",
                "recommend bearings",
                "estimate weight",
            ],
            "robot": [
                "recommend motor for robot",
                "recommend battery",
                "recommend sensors",
                "recommend bearings",
            ],
            "robotic_arm": [
                "recommend motor for robot",
                "recommend bearings",
                "estimate weight",
            ],
            "cnc": [
                "recommend bearings",
                "what tools do I need",
                "estimate weight",
            ],
            "wearable": [
                "estimate weight",
                "how much material do I need",
            ],
            "enclosure": [
                "estimate weight",
                "how much material do I need",
                "what tools do I need",
            ],
            "wind_tunnel": [
                "analyze aerodynamics at 30 m/s",
                "estimate weight",
            ],
            "sensor_pod": [
                "recommend sensors",
                "recommend battery",
                "estimate weight",
            ],
            "mechanism": [
                "recommend bearings",
                "what tools do I need",
                "estimate weight",
            ],
        }
        recommendations = _APP_RECS.get(application, [
            "estimate weight",
            "how much material do I need",
            "what tools do I need",
        ])

        # Generate tasks
        tasks = [
            PlanTask(description=f"Create {c.name} ({c.type}, {c.width}x{c.height}x{c.depth}mm, {c.material})")
            for c in components
        ]
        for rec in recommendations:
            tasks.append(PlanTask(description=f"AI: {rec}"))
        tasks.append(PlanTask(description="Review and finalize design"))
        mfg_label = {"3d_print": "3D print", "cnc": "CNC machine", "either": "3D print or CNC machine"}
        tasks.append(PlanTask(description=f"Export model for {mfg_label.get(manufacturing, 'manufacturing')}"))

        return PrototypePlan(
            source="hephaestus_relay",
            title=goal[:80] if goal else "Hephaestus Design Project",
            goal=goal,
            constraints=constraints,
            application=application,
            manufacturing=manufacturing,
            components=components,
            recommendations=recommendations,
            tasks=tasks,
            metadata={
                "ai_name": ai_name,
                "ai_uuid": ai_uuid,
                "created": datetime.now().isoformat(),
            },
        )


class PlannerParser:
    """
    Parses a Planner output into a PrototypePlan.
    Extracts goals, tasks, and generates component suggestions.
    """

    @classmethod
    def parse(cls, goal: str, plan_text: str, ai_name: str = "", ai_uuid: str = "") -> PrototypePlan:
        """Parse planner output into a structured plan."""
        combined = f"{goal} {plan_text}".lower()

        # Detect application
        application = ""
        app_keywords = HephaestusBriefParser._APP_KEYWORDS
        for keyword, app in app_keywords.items():
            if keyword in combined:
                application = app
                break

        # Extract tasks from plan text (lines starting with [ ] or Step N:)
        tasks = []
        for line in plan_text.splitlines():
            line = line.strip()
            if line.startswith("[ ]") or line.startswith("Step"):
                tasks.append(PlanTask(description=line))

        # If no tasks found, create basic ones
        if not tasks:
            tasks = [
                PlanTask(description="Define scope and components"),
                PlanTask(description="Create 3D model"),
                PlanTask(description="Review and export"),
            ]

        # Detect if this is a physical project
        physical_keywords = ["build", "make", "create", "design", "prototype", "frame",
                            "body", "structure", "device", "machine", "robot", "drone"]
        is_physical = any(kw in combined for kw in physical_keywords)

        components = []
        recommendations = []
        if is_physical:
            components.append(PlanComponent(
                type="box", name="Main Structure",
                width=100, height=50, depth=30,
                material="PLA",
            ))
            if application == "drone":
                recommendations.extend([
                    "recommend motor for drone",
                    "recommend battery",
                    "recommend propeller",
                ])
            elif application == "robot":
                recommendations.extend([
                    "recommend motor for robot",
                    "recommend battery",
                    "recommend sensors",
                ])
            else:
                recommendations.extend([
                    "estimate weight",
                    "how much material do I need",
                    "what tools do I need",
                ])

        return PrototypePlan(
            source="planner",
            title=goal[:80] if goal else "Planner Project",
            goal=goal,
            constraints="",
            application=application,
            components=components,
            recommendations=recommendations,
            tasks=tasks,
            metadata={
                "ai_name": ai_name,
                "ai_uuid": ai_uuid,
                "created": datetime.now().isoformat(),
            },
        )
