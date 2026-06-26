"""
Engineering Knowledge Base for the Prototyper module.

Contains real-world data on:
- Materials (density, tensile strength, print temp, cost, use cases)
- Motors (RPM, torque, voltage, recommended applications)
- Aerodynamics (drag coefficients, lift formulas, Reynolds number basics)
- Component matching (if X size → Y motor, if Y weight → Z battery)

This is the "AI knowledge" that helps users finish their prototypes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum, auto


# ═══════════════════════════════════════════════════════════════════════════════
# MATERIALS DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

class MaterialCategory(Enum):
    PLA = auto()
    ABS = auto()
    PETG = auto()
    TPU = auto()
    NYLON = auto()
    RESIN = auto()
    METAL = auto()
    WOOD = auto()
    CARBON_FIBER = auto()
    COMPOSITE = auto()


@dataclass
class MaterialSpec:
    id: str
    name: str
    category: MaterialCategory
    density_g_cm3: float          # g/cm³
    tensile_strength_mpa: float   # MPa
    flexural_strength_mpa: float  # MPa
    print_temp_c: tuple           # (min, max) °C
    bed_temp_c: tuple             # (min, max) °C
    cost_per_kg: float            # USD
    difficulty: str               # Easy, Medium, Hard
    water_resistant: bool
    heat_resistant_c: float       # max service temp °C
    food_safe: bool
    recyclable: bool
    description: str
    best_for: list[str] = field(default_factory=list)
    print_notes: str = ""


MATERIALS: dict[str, MaterialSpec] = {
    "PLA": MaterialSpec(
        id="PLA", name="PLA (Polylactic Acid)", category=MaterialCategory.PLA,
        density_g_cm3=1.24, tensile_strength_mpa=50, flexural_strength_mpa=80,
        print_temp_c=(190, 220), bed_temp_c=(20, 60),
        cost_per_kg=20.0, difficulty="Easy",
        water_resistant=False, heat_resistant_c=60, food_safe=True, recyclable=True,
        description="Most popular 3D printing material. Easy to print, biodegradable, great for prototypes.",
        best_for=["prototypes", "display models", "low-stress parts", "beginners"],
        print_notes="No heated bed required. Low warping. Not suitable for high-heat applications."
    ),
    "ABS": MaterialSpec(
        id="ABS", name="ABS (Acrylonitrile Butadiene Styrene)", category=MaterialCategory.ABS,
        density_g_cm3=1.04, tensile_strength_mpa=40, flexural_strength_mpa=60,
        print_temp_c=(230, 260), bed_temp_c=(80, 110),
        cost_per_kg=25.0, difficulty="Medium",
        water_resistant=True, heat_resistant_c=105, food_safe=False, recyclable=True,
        description="Durable, impact-resistant. Used in LEGO bricks. Needs enclosed printer.",
        best_for=["functional parts", "automotive", "enclosures", "high-heat"],
        print_notes="Requires heated bed and enclosure. Emits fumes — ventilate area."
    ),
    "PETG": MaterialSpec(
        id="PETG", name="PETG (Polyethylene Terephthalate Glycol)", category=MaterialCategory.PETG,
        density_g_cm3=1.27, tensile_strength_mpa=55, flexural_strength_mpa=70,
        print_temp_c=(220, 250), bed_temp_c=(70, 90),
        cost_per_kg=25.0, difficulty="Easy",
        water_resistant=True, heat_resistant_c=80, food_safe=True, recyclable=True,
        description="Combines ease of PLA with durability of ABS. Great all-rounder.",
        best_for=["functional prototypes", "outdoor parts", "food containers", "mechanical parts"],
        print_notes="Good layer adhesion. Slightly stringy. No enclosure needed."
    ),
    "TPU": MaterialSpec(
        id="TPU", name="TPU (Thermoplastic Polyurethane)", category=MaterialCategory.TPU,
        density_g_cm3=1.21, tensile_strength_mpa=30, flexural_strength_mpa=20,
        print_temp_c=(210, 240), bed_temp_c=(20, 60),
        cost_per_kg=35.0, difficulty="Medium",
        water_resistant=True, heat_resistant_c=80, food_safe=True, recyclable=True,
        description="Flexible, rubber-like material. Great for gaskets, tires, phone cases.",
        best_for=["flexible parts", "gaskets", "tires", "shock absorption", "grippers"],
        print_notes="Print slow (20-30 mm/s). Direct drive extruder recommended."
    ),
    "Nylon": MaterialSpec(
        id="Nylon", name="Nylon (Polyamide)", category=MaterialCategory.NYLON,
        density_g_cm3=1.14, tensile_strength_mpa=70, flexural_strength_mpa=90,
        print_temp_c=(240, 280), bed_temp_c=(70, 100),
        cost_per_kg=45.0, difficulty="Hard",
        water_resistant=True, heat_resistant_c=120, food_safe=False, recyclable=True,
        description="Extremely strong, wear-resistant. Used for gears and mechanical parts.",
        best_for=["gears", "bearings", "mechanical parts", "high-wear components"],
        print_notes="Absorbs moisture — keep dry before printing. Needs high temp."
    ),
    "Resin": MaterialSpec(
        id="Resin", name="UV Resin (Standard)", category=MaterialCategory.RESIN,
        density_g_cm3=1.18, tensile_strength_mpa=55, flexural_strength_mpa=85,
        print_temp_c=(0, 0), bed_temp_c=(0, 0),
        cost_per_kg=60.0, difficulty="Medium",
        water_resistant=True, heat_resistant_c=70, food_safe=False, recyclable=False,
        description="SLA/resin printer material. High detail, smooth surface finish.",
        best_for=["miniatures", "jewelry", "dental", "high-detail models"],
        print_notes="Requires UV curing. Handle with gloves. Resin printer only."
    ),
    "Aluminum": MaterialSpec(
        id="Aluminum", name="Aluminum (6061-T6)", category=MaterialCategory.METAL,
        density_g_cm3=2.70, tensile_strength_mpa=310, flexural_strength_mpa=240,
        print_temp_c=(0, 0), bed_temp_c=(0, 0),
        cost_per_kg=8.0, difficulty="Hard",
        water_resistant=True, heat_resistant_c=200, food_safe=True, recyclable=True,
        description="Lightweight metal. CNC or metal FDM printing. Excellent strength-to-weight.",
        best_for=["drones", "frames", "brackets", "heat sinks", "structural parts"],
        print_notes="Requires CNC or specialized metal 3D printer. Anodize for corrosion resistance."
    ),
    "Carbon Fiber": MaterialSpec(
        id="Carbon Fiber", name="Carbon Fiber Composite", category=MaterialCategory.CARBON_FIBER,
        density_g_cm3=1.55, tensile_strength_mpa=600, flexural_strength_mpa=500,
        print_temp_c=(0, 0), bed_temp_c=(0, 0),
        cost_per_kg=80.0, difficulty="Hard",
        water_resistant=True, heat_resistant_c=150, food_safe=False, recyclable=False,
        description="Ultra-strong, ultra-light. Used in aerospace and racing.",
        best_for=["drones", "aerospace", "racing parts", "high-performance", "lightweight"],
        print_notes="Requires specialized manufacturing (layup or CF-filled filament)."
    ),
    "Wood PLA": MaterialSpec(
        id="Wood PLA", name="Wood-fill PLA", category=MaterialCategory.WOOD,
        density_g_cm3=1.28, tensile_strength_mpa=35, flexural_strength_mpa=50,
        print_temp_c=(190, 220), bed_temp_c=(20, 50),
        cost_per_kg=40.0, difficulty="Easy",
        water_resistant=False, heat_resistant_c=55, food_safe=False, recyclable=True,
        description="PLA mixed with wood fibers. Looks and smells like real wood.",
        best_for=["decorative items", "furniture models", "art", "prototypes needing wood look"],
        print_notes="Can be sanded and stained. May clog nozzles — use 0.4mm+ nozzle."
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# MOTORS DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

class MotorType(Enum):
    DC_BRUSHED = auto()
    DC_BRUSHLESS = auto()
    STEPPER = auto()
    SERVO = auto()
    LINEAR = auto()


@dataclass
class MotorSpec:
    id: str
    name: str
    motor_type: MotorType
    voltage: float           # V
    current_a: float         # A (stall or rated)
    rpm: int                 # RPM at rated voltage
    torque_kg_cm: float      # kg·cm
    power_w: float           # Watts
    weight_g: float          # grams
    shaft_diameter_mm: float
    length_mm: float
    diameter_mm: float
    cost_usd: float
    description: str
    best_for: list[str] = field(default_factory=list)


MOTORS: dict[str, MotorSpec] = {
    "N20-micro": MotorSpec(
        id="N20-micro", name="N20 Micro Gear Motor 6V 200RPM", motor_type=MotorType.DC_BRUSHED,
        voltage=6.0, current_a=0.3, rpm=200, torque_kg_cm=0.8,
        power_w=1.8, weight_g=10, shaft_diameter_mm=3.0, length_mm=25, diameter_mm=10,
        cost_usd=3.0,
        description="Tiny geared motor for small robots, actuators, and mechanisms.",
        best_for=["small robots", "micro actuators", "toys", "camera gimbals (small)"]
    ),
    "TT-motor": MotorSpec(
        id="TT-motor", name="TT Gear Motor 3-6V 200RPM", motor_type=MotorType.DC_BRUSHED,
        voltage=6.0, current_a=0.25, rpm=200, torque_kg_cm=2.0,
        power_w=1.5, weight_g=30, shaft_diameter_mm=6.0, length_mm=40, diameter_mm=20,
        cost_usd=2.5,
        description="Cheap, popular motor for Arduino/robotics projects.",
        best_for=["robot cars", "conveyor belts", "simple robots", "beginner projects"]
    ),
    "28BYJ-48": MotorSpec(
        id="28BYJ-48", name="28BYJ-48 Stepper Motor 5V", motor_type=MotorType.STEPPER,
        voltage=5.0, current_a=0.2, rpm=15, torque_kg_cm=3.0,
        power_w=1.0, weight_g=35, shaft_diameter_mm=5.0, length_mm=19, diameter_mm=28,
        cost_usd=3.0,
        description="Cheap stepper motor for precise positioning. Needs ULN2003 driver.",
        best_for=["precise rotation", "CNC plotters", "curtains", "camera sliders"]
    ),
    "NEMA17": MotorSpec(
        id="NEMA17", name="NEMA 17 Stepper 12V 1.5A", motor_type=MotorType.STEPPER,
        voltage=12.0, current_a=1.5, rpm=300, torque_kg_cm=5.5,
        power_w=18, weight_g=350, shaft_diameter_mm=5.0, length_mm=48, diameter_mm=42,
        cost_usd=15.0,
        description="Standard stepper for 3D printers and CNC machines.",
        best_for=["3D printers", "CNC mills", "linear actuators", "camera sliders (pro)"]
    ),
    "A2212-1000kv": MotorSpec(
        id="A2212-1000kv", name="A2212 1000KV Brushless Motor", motor_type=MotorType.DC_BRUSHLESS,
        voltage=11.1, current_a=14.0, rpm=11100, torque_kg_cm=1.5,
        power_w=155, weight_g=58, shaft_diameter_mm=3.17, length_mm=30, diameter_mm=28,
        cost_usd=8.0,
        description="Popular brushless motor for drones and RC planes. Needs ESC.",
        best_for=["drones", "RC planes", "RC cars", "high-speed applications"]
    ),
    "A2212-2200kv": MotorSpec(
        id="A2212-2200kv", name="A2212 2200KV Brushless Motor", motor_type=MotorType.DC_BRUSHLESS,
        voltage=11.1, current_a=18.0, rpm=24420, torque_kg_cm=0.8,
        power_w=200, weight_g=58, shaft_diameter_mm=3.17, length_mm=30, diameter_mm=28,
        cost_usd=10.0,
        description="High-speed brushless motor for small racing drones.",
        best_for=["racing drones", "EDF jets", "high-speed RC"]
    ),
    "MG996R": MotorSpec(
        id="MG996R", name="MG996R Servo 6V", motor_type=MotorType.SERVO,
        voltage=6.0, current_a=2.5, rpm=0, torque_kg_cm=11.0,
        power_w=15, weight_g=55, shaft_diameter_mm=6.0, length_mm=41, diameter_mm=20,
        cost_usd=8.0,
        description="High-torque metal gear servo for robotics and RC.",
        best_for=["robotic arms", "RC steering", "walking robots", "grippers"]
    ),
    "SG90": MotorSpec(
        id="SG90", name="SG90 Micro Servo 4.8V", motor_type=MotorType.SERVO,
        voltage=4.8, current_a=0.8, rpm=0, torque_kg_cm=1.8,
        power_w=4, weight_g=9, shaft_diameter_mm=4.8, length_mm=22, diameter_mm=12,
        cost_usd=3.0,
        description="Tiny plastic gear servo for small projects.",
        best_for=["small grippers", "micro robots", "flapping wings", "camera tilt"]
    ),
    "B5050-450kv": MotorSpec(
        id="B5050-450kv", name="B5050 450KV Brushless Motor", motor_type=MotorType.DC_BRUSHLESS,
        voltage=22.2, current_a=40.0, rpm=9990, torque_kg_cm=8.0,
        power_w=888, weight_g=180, shaft_diameter_mm=6.0, length_mm=50, diameter_mm=50,
        cost_usd=60.0,
        description="Large brushless motor for big drones, e-bikes, and heavy-lift applications.",
        best_for=["large drones", "e-bikes", "electric skateboards", "heavy-lift"]
    ),
    "12V-775": MotorSpec(
        id="12V-775", name="775 DC Motor 12V 3500RPM", motor_type=MotorType.DC_BRUSHED,
        voltage=12.0, current_a=3.0, rpm=3500, torque_kg_cm=5.0,
        power_w=36, weight_g=300, shaft_diameter_mm=5.0, length_mm=66, diameter_mm=42,
        cost_usd=12.0,
        description="High-power DC motor for power tools and heavy applications.",
        best_for=["power tools", "winches", "large robots", "pumps", "grinders"]
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# BATTERY DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class BatterySpec:
    id: str
    name: str
    chemistry: str
    voltage: float
    capacity_mah: int
    weight_g: float
    cost_usd: float
    c_rating: int
    description: str
    best_for: list[str] = field(default_factory=list)


BATTERIES: dict[str, BatterySpec] = {
    "LiPo-3S-1500": BatterySpec(
        id="LiPo-3S-1500", name="3S LiPo 1500mAh 30C", chemistry="LiPo",
        voltage=11.1, capacity_mah=1500, weight_g=130, cost_usd=20, c_rating=30,
        description="Standard drone battery. 11.1V, good for 250-450 size quads.",
        best_for=["drones", "RC cars", "robots"]
    ),
    "LiPo-3S-5000": BatterySpec(
        id="LiPo-3S-5000", name="3S LiPo 5000mAh 50C", chemistry="LiPo",
        voltage=11.1, capacity_mah=5000, weight_g=400, cost_usd=45, c_rating=50,
        description="Large capacity LiPo for bigger drones and robots.",
        best_for=["large drones", "RC trucks", "robotic arms"]
    ),
    "LiPo-4S-1300": BatterySpec(
        id="LiPo-4S-1300", name="4S LiPo 1300mAh 75C", chemistry="LiPo",
        voltage=14.8, capacity_mah=1300, weight_g=160, cost_usd=25, c_rating=75,
        description="Racing drone battery. 14.8V for high-speed 210-280 quads.",
        best_for=["racing drones", "fast RC"]
    ),
    "18650-3.7V-3000": BatterySpec(
        id="18650-3.7V-3000", name="18650 Li-ion 3000mAh", chemistry="Li-ion",
        voltage=3.7, capacity_mah=3000, weight_g=46, cost_usd=8, c_rating=10,
        description="Standard rechargeable cell for battery packs and power banks.",
        best_for=["robots", "portable projects", "power banks", "flashlights"]
    ),
    "AA-4pack": BatterySpec(
        id="AA-4pack", name="4x AA Alkaline", chemistry="Alkaline",
        voltage=6.0, capacity_mah=2500, weight_g=100, cost_usd=3, c_rating=0,
        description="Simple AA battery pack for low-power projects.",
        best_for=["simple robots", "toys", "prototypes", "beginner projects"]
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# ENGINEERING RECOMMENDATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class EngineeringKB:
    """
    The AI knowledge engine that recommends components based on
    prototype specifications.
    """

    @staticmethod
    def recommend_motor(
        weight_g: float,
        application: str = "drone",
        max_speed_kmh: float | None = None,
        budget_usd: float | None = None,
    ) -> list[dict]:
        """
        Recommend motors based on prototype weight and application.

        Returns list of {motor, reason, quantity} dicts sorted by best match.
        """
        results = []

        if application == "drone":
            # Thrust-to-weight ratio: need at least 2:1 for safe flight
            required_thrust_g = weight_g * 2.0
            # Assume 4 motors for a quadcopter
            thrust_per_motor = required_thrust_g / 4

            for motor in MOTORS.values():
                if motor.motor_type != MotorType.DC_BRUSHLESS:
                    continue
                # Rough thrust estimate: power_w * 7-10 g/W for efficient props
                est_thrust = motor.power_w * 8
                if est_thrust >= thrust_per_motor:
                    if budget_usd and motor.cost_usd * 4 > budget_usd:
                        continue
                    results.append({
                        "motor": motor,
                        "reason": f"Provides ~{est_thrust:.0f}g thrust per motor. "
                                  f"4 motors = ~{est_thrust*4:.0f}g total thrust. "
                                  f"Your drone weighs ~{weight_g}g (2:1 ratio needs {required_thrust_g:.0f}g).",
                        "quantity": 4,
                        "total_cost": motor.cost_usd * 4,
                    })

        elif application == "robot_car":
            # Need enough torque to move the weight
            for motor in MOTORS.values():
                if motor.motor_type in (MotorType.DC_BRUSHED, MotorType.DC_BRUSHLESS):
                    # Rough: need torque to overcome rolling resistance
                    # F = mu * m * g, mu ~ 0.05 for wheels on flat surface
                    required_torque = weight_g * 0.05 * 9.81 / 100  # kg·cm rough
                    if motor.torque_kg_cm >= required_torque / 2:  # 2 motors
                        if budget_usd and motor.cost_usd * 2 > budget_usd:
                            continue
                        results.append({
                            "motor": motor,
                            "reason": f"Torque: {motor.torque_kg_cm} kg·cm. "
                                      f"Estimated needed: {required_torque:.1f} kg·cm total. "
                                      f"2 motors provide {motor.torque_kg_cm*2:.1f} kg·cm combined.",
                            "quantity": 2,
                            "total_cost": motor.cost_usd * 2,
                        })

        elif application == "robotic_arm":
            # Need high torque servos
            for motor in MOTORS.values():
                if motor.motor_type == MotorType.SERVO:
                    # Base joint needs most torque (holds entire arm + load)
                    arm_length_cm = 30  # assume 30cm arm
                    required_torque = (weight_g / 1000) * arm_length_cm  # kg·cm
                    if motor.torque_kg_cm >= required_torque * 0.5:
                        if budget_usd and motor.cost_usd * 4 > budget_usd:
                            continue
                        results.append({
                            "motor": motor,
                            "reason": f"Torque: {motor.torque_kg_cm} kg·cm. "
                                      f"Arm base needs ~{required_torque:.1f} kg·cm for {weight_g}g load at 30cm.",
                            "quantity": 4,
                            "total_cost": motor.cost_usd * 4,
                        })

        elif application == "rc_plane":
            # Thrust should be at least 0.5:1 for a trainer, 1:1 for sport
            required_thrust_g = weight_g * 0.7
            for motor in MOTORS.values():
                if motor.motor_type != MotorType.DC_BRUSHLESS:
                    continue
                est_thrust = motor.power_w * 6  # planes are more efficient
                if est_thrust >= required_thrust_g:
                    if budget_usd and motor.cost_usd > budget_usd:
                        continue
                    results.append({
                        "motor": motor,
                        "reason": f"Provides ~{est_thrust:.0f}g thrust. "
                                  f"Plane weighs ~{weight_g}g (0.7:1 ratio needs {required_thrust_g:.0f}g).",
                        "quantity": 1,
                        "total_cost": motor.cost_usd,
                    })

        # Sort by cost (best value first)
        results.sort(key=lambda r: r["total_cost"])
        return results

    @staticmethod
    def recommend_battery(
        motors: list[MotorSpec],
        flight_time_min: float = 10.0,
        application: str = "drone",
    ) -> list[dict]:
        """Recommend a battery based on motor power requirements."""
        total_power_w = sum(m.power_w for m in motors)
        # Energy needed: P * t / V
        # flight_time_min in minutes, convert to hours
        energy_mah_needed = (total_power_w * (flight_time_min / 60) / 11.1) * 1000  # for 3S

        results = []
        for batt in BATTERIES.values():
            # Check if battery can provide the current
            max_current = batt.capacity_mah * batt.c_rating / 1000 if batt.c_rating > 0 else 999
            motor_current = sum(m.current_a for m in motors)
            if max_current >= motor_current * 0.8:
                est_time = (batt.capacity_mah / 1000) * batt.voltage / total_power_w * 60  # minutes
                results.append({
                    "battery": batt,
                    "reason": f"Capacity: {batt.capacity_mah}mAh at {batt.voltage}V. "
                              f"Estimated runtime: ~{est_time:.1f} minutes. "
                              f"Max discharge: {max_current:.0f}A (motors need {motor_current:.1f}A).",
                    "est_runtime_min": est_time,
                })

        results.sort(key=lambda r: abs(r["est_runtime_min"] - flight_time_min))
        return results

    @staticmethod
    def recommend_material(
        application: str = "prototype",
        load_kg: float = 0.0,
        outdoor: bool = False,
        high_detail: bool = False,
        flexible: bool = False,
        budget_usd_per_kg: float | None = None,
    ) -> list[dict]:
        """Recommend a material based on application requirements."""
        results = []
        for mat in MATERIALS.values():
            score = 0
            reasons = []

            if flexible and mat.category in (MaterialCategory.TPU,):
                score += 50
                reasons.append("Flexible material — perfect for parts that need to bend")
            elif flexible:
                continue

            if high_detail and mat.category in (MaterialCategory.RESIN,):
                score += 40
                reasons.append("Resin gives the highest detail and smoothest surface")
            elif high_detail and mat.category in (MaterialCategory.PLA,):
                score += 20
                reasons.append("PLA prints cleanly with good detail")

            if outdoor and mat.water_resistant:
                score += 20
                reasons.append(f"Water resistant (rated to {mat.heat_resistant_c}°C)")

            if load_kg > 1.0 and mat.tensile_strength_mpa > 50:
                score += 20
                reasons.append(f"High tensile strength ({mat.tensile_strength_mpa} MPa)")

            if application in mat.best_for:
                score += 30
                reasons.append(f"Specifically recommended for {application}")

            if budget_usd_per_kg and mat.cost_per_kg <= budget_usd_per_kg:
                score += 15
                reasons.append(f"Within budget (${mat.cost_per_kg}/kg)")

            if mat.difficulty == "Easy":
                score += 10
                reasons.append("Easy to print — great for beginners")

            if score > 0:
                results.append({
                    "material": mat,
                    "score": score,
                    "reasons": reasons,
                })

        results.sort(key=lambda r: r["score"], reverse=True)
        return results

    @staticmethod
    def aerodynamics_analysis(
        width_mm: float,
        height_mm: float,
        depth_mm: float,
        speed_ms: float = 10.0,
        shape: str = "box",
    ) -> dict:
        """
        Basic aerodynamic analysis of a shape.
        Returns drag force, drag coefficient estimate, and recommendations.
        """
        # Frontal area (m²)
        frontal_area = (width_mm / 1000) * (height_mm / 1000)

        # Air density at sea level
        rho = 1.225  # kg/m³

        # Drag coefficients (approximate)
        cd_map = {
            "box": 1.05,
            "cylinder": 0.82,
            "sphere": 0.47,
            "cone": 0.50,
            "streamlined": 0.04,
            "pyramid": 0.70,
        }
        cd = cd_map.get(shape, 1.0)

        # Drag force: F = 0.5 * rho * v² * Cd * A
        drag_force = 0.5 * rho * speed_ms**2 * cd * frontal_area

        # Reynolds number (characteristic length = width)
        viscosity = 1.81e-5  # Pa·s
        re = (rho * speed_ms * (width_mm / 1000)) / viscosity

        # Power needed to overcome drag
        power_w = drag_force * speed_ms

        recommendations = []
        if cd > 0.8:
            recommendations.append(
                "High drag coefficient. Consider streamlining the shape — "
                "rounded edges, tapered tail, or use a cone/teardrop profile."
            )
        if frontal_area > 0.01:
            recommendations.append(
                f"Large frontal area ({frontal_area*10000:.0f} cm²). "
                "Reducing the cross-section will significantly lower drag."
            )
        if power_w > 50:
            recommendations.append(
                f"High power requirement ({power_w:.0f}W to overcome drag at {speed_ms}m/s). "
                "Consider a more powerful motor or aerodynamic optimization."
            )
        if not recommendations:
            recommendations.append("Aerodynamic profile looks reasonable for this speed.")

        return {
            "drag_coefficient": cd,
            "frontal_area_m2": frontal_area,
            "drag_force_n": drag_force,
            "power_required_w": power_w,
            "reynolds_number": re,
            "recommendations": recommendations,
        }

    @staticmethod
    def weight_estimate(
        shapes: list[dict],
    ) -> dict:
        """
        Estimate total weight from a list of shapes with material assignments.
        Each shape dict: {width, height, depth, material}
        """
        total_weight_g = 0.0
        breakdown = []

        for s in shapes:
            mat = MATERIALS.get(s.get("material", "PLA"))
            if not mat:
                continue
            # Volume in cm³ = (w * h * d) / 1000  (mm → cm)
            volume_cm3 = (s["width"] * s["height"] * s.get("depth", s["width"])) / 1000
            weight_g = volume_cm3 * mat.density_g_cm3
            total_weight_g += weight_g
            breakdown.append({
                "material": mat.name,
                "volume_cm3": volume_cm3,
                "weight_g": weight_g,
            })

        return {
            "total_weight_g": total_weight_g,
            "total_weight_kg": total_weight_g / 1000,
            "breakdown": breakdown,
        }

    @staticmethod
    def exterior_completion(
        existing_parts: list[dict],
        desired_size: dict,
        style: str = "functional",
    ) -> list[dict]:
        """
        Help finish an exterior when the user has internal components but
        doesn't know how to design the shell.

        existing_parts: list of {name, width, height, depth, x, y}
        desired_size: {width, height, depth} of the final product
        style: "functional" | "aerodynamic" | "compact" | "rugged"

        Returns list of suggested exterior shapes to add.
        """
        suggestions = []

        # Calculate bounding box of existing parts
        if not existing_parts:
            return suggestions

        max_x = max(p["x"] + p["width"] for p in existing_parts)
        max_y = max(p["y"] + p["height"] for p in existing_parts)
        min_x = min(p["x"] for p in existing_parts)
        min_y = min(p["y"] for p in existing_parts)

        existing_width = max_x - min_x
        existing_height = max_y - min_y

        target_w = desired_size.get("width", existing_width + 20)
        target_h = desired_size.get("height", existing_height + 20)
        target_d = desired_size.get("depth", 50)

        wall_thickness = 2.0  # mm

        if style == "functional":
            suggestions.append({
                "shape": "box",
                "name": "Bottom Shell",
                "x": min_x - wall_thickness,
                "y": min_y - wall_thickness,
                "width": target_w + wall_thickness * 2,
                "height": target_h + wall_thickness * 2,
                "depth": target_d / 2,
                "material": "PETG",
                "reason": "PETG bottom shell provides durability and easy printing. "
                          "Wall thickness 2mm gives good structural integrity."
            })
            suggestions.append({
                "shape": "box",
                "name": "Top Shell",
                "x": min_x - wall_thickness,
                "y": min_y - wall_thickness,
                "width": target_w + wall_thickness * 2,
                "height": target_h + wall_thickness * 2,
                "depth": target_d / 2,
                "material": "PLA",
                "reason": "Lightweight PLA top shell. Can be painted or decorated."
            })

        elif style == "aerodynamic":
            suggestions.append({
                "shape": "cone",
                "name": "Nose Cone",
                "x": min_x - 30,
                "y": min_y + existing_height / 2 - 15,
                "width": 30,
                "height": 30,
                "depth": 30,
                "material": "PLA",
                "reason": "Cone nose reduces drag by ~40% compared to a flat front. "
                          "PLA is easy to print and sand smooth."
            })
            suggestions.append({
                "shape": "box",
                "name": "Streamlined Body",
                "x": min_x - wall_thickness,
                "y": min_y - wall_thickness,
                "width": existing_width + wall_thickness * 2,
                "height": existing_height + wall_thickness * 2,
                "depth": target_d,
                "material": "PETG",
                "reason": "PETG body with rounded edges. Add fillets in your slicer "
                          "for better aerodynamics and print quality."
            })

        elif style == "compact":
            suggestions.append({
                "shape": "box",
                "name": "Compact Enclosure",
                "x": min_x - wall_thickness,
                "y": min_y - wall_thickness,
                "width": existing_width + wall_thickness * 2,
                "height": existing_height + wall_thickness * 2,
                "depth": target_d,
                "material": "ABS",
                "reason": "ABS for heat resistance in a compact space. "
                          "Minimal extra volume — fits tightly around components."
            })

        elif style == "rugged":
            suggestions.append({
                "shape": "box",
                "name": "Rugged Outer Shell",
                "x": min_x - 5,
                "y": min_y - 5,
                "width": existing_width + 10,
                "height": existing_height + 10,
                "depth": target_d + 4,
                "material": "TPU",
                "reason": "TPU rubber-like shell absorbs impacts. 5mm bumper zone "
                          "around all components for drop protection."
            })

        return suggestions

    @staticmethod
    def get_material_list() -> list[str]:
        return list(MATERIALS.keys())

    @staticmethod
    def get_motor_list() -> list[str]:
        return list(MOTORS.keys())

    @staticmethod
    def get_battery_list() -> list[str]:
        return list(BATTERIES.keys())
