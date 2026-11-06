"""Parametric concept model for FPV Advanced Modular X R01.

Hybrid Deadcat X with four replaceable arms. First-pass geometry only.
"""
from dataclasses import asdict, dataclass
from math import atan2, degrees, hypot
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AdvancedModularXSpec:
    wheelbase_mm: float = 327.0
    front_motor_x_mm: float = 140.0
    rear_motor_x_mm: float = 98.0
    motor_y_mm: float = 112.0
    propeller_diameter_mm: float = 177.8
    min_prop_gap_mm: float = 10.0
    plate_length_mm: float = 160.0
    plate_width_mm: float = 75.0
    bottom_plate_thickness_mm: float = 3.0
    top_plate_thickness_mm: float = 2.0
    arm_width_mm: float = 22.0
    arm_thickness_mm: float = 6.0
    arm_overlap_mm: float = 36.0
    root_hole_station_1_mm: float = -32.0
    root_hole_station_2_mm: float = -16.0
    root_hole_row_spacing_mm: float = 12.0
    root_hole_diameter_mm: float = 3.2
    motor_pattern_mm: float = 19.0
    motor_hole_diameter_mm: float = 3.2
    motor_pad_size_mm: float = 34.0
    standoff_height_mm: float = 25.0
    standoff_x_mm: float = 65.0
    standoff_y_mm: float = 27.5
    standoff_diameter_mm: float = 6.0
    stack_hole_diameter_mm: float = 3.2

    def motor_centers(self) -> dict[str, tuple[float, float]]:
        return {
            "front_left": (-self.front_motor_x_mm, self.motor_y_mm),
            "front_right": (self.front_motor_x_mm, self.motor_y_mm),
            "rear_left": (-self.rear_motor_x_mm, -self.motor_y_mm),
            "rear_right": (self.rear_motor_x_mm, -self.motor_y_mm),
        }

    def diagonal_wheelbase(self) -> float:
        a, b = self.motor_centers()["front_left"], self.motor_centers()["rear_right"]
        return hypot(b[0] - a[0], b[1] - a[1])

    def prop_clearances(self) -> dict[str, float]:
        centers = self.motor_centers()
        names = list(centers)
        gaps = {}
        for i, first in enumerate(names):
            for second in names[i + 1:]:
                distance = hypot(centers[first][0] - centers[second][0],
                                 centers[first][1] - centers[second][1])
                gaps[f"{first}__{second}"] = distance - self.propeller_diameter_mm
        return gaps

    def arm_root_centers(self) -> dict[str, tuple[float, float]]:
        roots = {}
        for name, (mx, my) in self.motor_centers().items():
            length = hypot(mx, my)
            ux, uy = mx / length, my / length
            scale = min((self.plate_length_mm / 2) / abs(ux),
                        (self.plate_width_mm / 2) / abs(uy))
            roots[name] = (ux * scale, uy * scale)
        return roots

    def arm_root_holes(self) -> dict[str, list[tuple[float, float]]]:
        result, roots = {}, self.arm_root_centers()
        for name, (mx, my) in self.motor_centers().items():
            length = hypot(mx, my)
            ux, uy = mx / length, my / length
            nx, ny = -uy, ux
            rx, ry = roots[name]
            points = []
            for station in (self.root_hole_station_1_mm, self.root_hole_station_2_mm):
                for side in (-1, 1):
                    points.append((rx + ux * station + nx * side * self.root_hole_row_spacing_mm / 2,
                                   ry + uy * station + ny * side * self.root_hole_row_spacing_mm / 2))
            result[name] = points
        return result

    def validate(self) -> None:
        dimensions = (
            self.wheelbase_mm, self.front_motor_x_mm, self.rear_motor_x_mm,
            self.motor_y_mm, self.propeller_diameter_mm, self.plate_length_mm,
            self.plate_width_mm, self.bottom_plate_thickness_mm,
            self.top_plate_thickness_mm, self.arm_width_mm, self.arm_thickness_mm,
            self.arm_overlap_mm, self.root_hole_diameter_mm, self.motor_pattern_mm,
            self.motor_hole_diameter_mm, self.motor_pad_size_mm,
            self.standoff_height_mm, self.standoff_x_mm, self.standoff_y_mm,
            self.standoff_diameter_mm, self.stack_hole_diameter_mm,
        )
        if any(v <= 0 for v in dimensions):
            raise ValueError("All principal dimensions must be positive")
        actual = self.diagonal_wheelbase()
        if abs(actual - self.wheelbase_mm) > 1.0:
            raise ValueError(f"Motor layout diagonal is {actual:.2f} mm, target {self.wheelbase_mm:.2f} mm")
        if min(self.prop_clearances().values()) < self.min_prop_gap_mm:
            raise ValueError("7-inch propeller envelopes violate the minimum clearance")
        if self.root_hole_row_spacing_mm + self.root_hole_diameter_mm >= self.arm_width_mm:
            raise ValueError("Arm-root bolt rows are too close to arm edges")
        if self.motor_pad_size_mm < self.motor_pattern_mm + 2 * self.motor_hole_diameter_mm:
            raise ValueError("Motor pad is too small for the selected motor bolt pattern")
        for name, points in self.arm_root_holes().items():
            for x, y in points:
                edge = min(self.plate_length_mm / 2 - abs(x), self.plate_width_mm / 2 - abs(y))
                if edge < self.root_hole_diameter_mm:
                    raise ValueError(f"{name} root bolt lacks plate edge distance")
        if self.standoff_x_mm >= self.plate_length_mm / 2 or self.standoff_y_mm >= self.plate_width_mm / 2:
            raise ValueError("Standoff coordinate is outside center plate")

    def to_dict(self) -> dict:
        self.validate()
        return {
            **asdict(self),
            "units": "mm",
            "actual_diagonal_wheelbase_mm": round(self.diagonal_wheelbase(), 3),
            "motor_centers": self.motor_centers(),
            "propeller_clearances_mm": {k: round(v, 3) for k, v in self.prop_clearances().items()},
            "arm_root_centers": self.arm_root_centers(),
            "arm_root_holes": self.arm_root_holes(),
            "status": "concept_geometry_pending_CAD_and_engineering_review",
        }


def build_advanced_modular_x_parts(spec: AdvancedModularXSpec | None = None) -> dict[str, Any]:
    """Build separate solids for plates, four arms and four standoffs."""
    from build123d import Align, Box, Cylinder, Pos, Rot

    spec = spec or AdvancedModularXSpec()
    spec.validate()

    def drill(shape: Any, holes: list[tuple[float, float]], diameter: float,
              z0: float, depth: float) -> Any:
        for x, y in holes:
            shape = shape - Pos(x, y, z0) * Cylinder(
                diameter / 2, depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
        return shape

    lower = Box(spec.plate_length_mm, spec.plate_width_mm, spec.bottom_plate_thickness_mm,
                align=(Align.CENTER, Align.CENTER, Align.MIN))
    root_holes = [p for group in spec.arm_root_holes().values() for p in group]
    lower = drill(lower, root_holes, spec.root_hole_diameter_mm,
                  -1, spec.bottom_plate_thickness_mm + 2)
    stand_centers = [
        (-spec.standoff_x_mm, -spec.standoff_y_mm),
        (-spec.standoff_x_mm, spec.standoff_y_mm),
        (spec.standoff_x_mm, -spec.standoff_y_mm),
        (spec.standoff_x_mm, spec.standoff_y_mm),
    ]
    lower = drill(lower, stand_centers, spec.stack_hole_diameter_mm,
                  -1, spec.bottom_plate_thickness_mm + 2)

    upper_z = spec.bottom_plate_thickness_mm + spec.standoff_height_mm
    upper = Pos(0, 0, upper_z) * Box(
        spec.plate_length_mm, spec.plate_width_mm, spec.top_plate_thickness_mm,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    stack_holes = []
    for spacing in (20.0, 30.5):
        h = spacing / 2
        stack_holes.extend([(-h, -h), (-h, h), (h, -h), (h, h)])
    upper = drill(upper, stack_holes, spec.stack_hole_diameter_mm,
                  upper_z - 1, spec.top_plate_thickness_mm + 2)
    upper = drill(upper, stand_centers, spec.stack_hole_diameter_mm,
                  upper_z - 1, spec.top_plate_thickness_mm + 2)

    parts: dict[str, Any] = {"PLATE_BOTTOM_3MM": lower, "PLATE_TOP_2MM": upper}
    roots = spec.arm_root_centers()
    for name, (mx, my) in spec.motor_centers().items():
        length = hypot(mx, my)
        ux, uy = mx / length, my / length
        rx, ry = roots[name]
        sx, sy = rx - ux * spec.arm_overlap_mm, ry - uy * spec.arm_overlap_mm
        arm_length = hypot(mx - sx, my - sy)
        angle = degrees(atan2(my - sy, mx - sx))
        arm = Pos((sx + mx) / 2, (sy + my) / 2, spec.bottom_plate_thickness_mm) * Rot(0, 0, angle) * Box(
            arm_length, spec.arm_width_mm, spec.arm_thickness_mm,
            align=(Align.CENTER, Align.CENTER, Align.MIN))
        pad = Pos(mx, my, spec.bottom_plate_thickness_mm) * Box(
            spec.motor_pad_size_mm, spec.motor_pad_size_mm, spec.arm_thickness_mm,
            align=(Align.CENTER, Align.CENTER, Align.MIN))
        arm = arm + pad
        arm = drill(arm, spec.arm_root_holes()[name], spec.root_hole_diameter_mm,
                    spec.bottom_plate_thickness_mm - 1, spec.arm_thickness_mm + 2)
        motor_holes = []
        half = spec.motor_pattern_mm / 2
        for dx in (-half, half):
            for dy in (-half, half):
                motor_holes.append((mx + dx, my + dy))
        arm = drill(arm, motor_holes, spec.motor_hole_diameter_mm,
                    spec.bottom_plate_thickness_mm - 1, spec.arm_thickness_mm + 2)
        parts["ARM_" + name.upper()] = arm

    for index, (x, y) in enumerate((
        (-spec.standoff_x_mm, -spec.standoff_y_mm),
        (-spec.standoff_x_mm, spec.standoff_y_mm),
        (spec.standoff_x_mm, -spec.standoff_y_mm),
        (spec.standoff_x_mm, spec.standoff_y_mm),
    ), 1):
        outer = Cylinder(spec.standoff_diameter_mm / 2, spec.standoff_height_mm,
                         align=(Align.CENTER, Align.CENTER, Align.MIN))
        bore = Cylinder(spec.stack_hole_diameter_mm / 2, spec.standoff_height_mm + 2,
                        align=(Align.CENTER, Align.CENTER, Align.MIN))
        parts[f"STANDOFF_{index}"] = Pos(x, y, spec.bottom_plate_thickness_mm) * (outer - Pos(0, 0, -1) * bore)
    return parts


def export_advanced_modular_x_step(path: str | Path, spec: AdvancedModularXSpec | None = None) -> Path:
    from build123d import Compound, export_step

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    parts = build_advanced_modular_x_parts(spec)
    export_step(Compound(children=list(parts.values())), str(path))
    return path
