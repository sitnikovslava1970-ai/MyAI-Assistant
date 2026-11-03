"""Parametric first-pass solid model for the 7-inch Classic-X FPV frame.

The module imports build123d lazily so its dimensional helpers and tests can run
without loading the OpenCascade graphics stack. Geometry is a prototype only:
verify fastener access, laminate edge distances, camera/battery clearances and
structural performance before CNC manufacture or flight.
"""
from dataclasses import dataclass
from math import atan2, hypot, sqrt
from pathlib import Path
from typing import Any

from .fpv_frame import FPVFrameSpec


@dataclass(frozen=True)
class FPVFrameSolidSpec:
    """Manufacturing-oriented dimensions not yet fixed by the base frame brief."""

    arm_root_overlap_mm: float = 30.0
    motor_pad_size_mm: float = 28.0
    arm_root_hole_diameter_mm: float = 3.2
    arm_root_hole_longitudinal_pitch_mm: float = 16.0
    arm_root_hole_transverse_spacing_mm: float = 9.0
    stack_hole_diameter_mm: float = 3.2
    standoff_x_offset_mm: float = 65.0
    standoff_y_offset_mm: float = 27.5
    standoff_outer_diameter_mm: float = 6.0

    def validate(self, frame: FPVFrameSpec) -> None:
        frame.validate()
        for name, value in self.__dict__.items():
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        if self.arm_root_overlap_mm >= frame.wheelbase_mm / 2:
            raise ValueError("Arm root overlap is too large")
        if self.motor_pad_size_mm < frame.motor_mount_spacing_mm + frame.motor_hole_diameter_mm:
            raise ValueError("Motor pad is too small for the motor hole pattern")
        if self.arm_root_hole_transverse_spacing_mm + self.arm_root_hole_diameter_mm >= frame.arm_width_mm:
            raise ValueError("Arm root bolt rows do not fit within the arm width")
        if self.standoff_x_offset_mm >= frame.top_plate_length_mm / 2:
            raise ValueError("Standoff X position is outside the center plate")
        if self.standoff_y_offset_mm >= frame.plate_width_mm / 2:
            raise ValueError("Standoff Y position is outside the center plate")


def arm_root_centers(frame: FPVFrameSpec) -> dict[str, tuple[float, float]]:
    """Intersection of each motor arm centerline with the center-plate envelope."""
    frame.validate()
    half_x = frame.top_plate_length_mm / 2
    half_y = frame.plate_width_mm / 2
    roots = {}
    for name, (mx, my) in frame.motor_centers().items():
        length = hypot(mx, my)
        ux, uy = mx / length, my / length
        scale = min(half_x / abs(ux), half_y / abs(uy))
        roots[name] = (ux * scale, uy * scale)
    return roots


def arm_root_bolt_centers(
    frame: FPVFrameSpec, solid: FPVFrameSolidSpec | None = None
) -> dict[str, list[tuple[float, float]]]:
    """Four M3 clearance-hole centers per arm, in a provisional 2 x 2 pattern.

    The two rows are placed in the arm overlap beneath the lower center plate.
    Longitudinal station spacing and transverse row spacing are configurable.
    """
    solid = solid or FPVFrameSolidSpec()
    solid.validate(frame)
    result = {}
    roots = arm_root_centers(frame)
    for name, (mx, my) in frame.motor_centers().items():
        length = hypot(mx, my)
        ux, uy = mx / length, my / length
        nx, ny = -uy, ux
        rx, ry = roots[name]
        stations = (
            -solid.arm_root_overlap_mm + solid.arm_root_hole_longitudinal_pitch_mm / 2,
            -solid.arm_root_overlap_mm + 1.5 * solid.arm_root_hole_longitudinal_pitch_mm,
        )
        points = []
        for station in stations:
            for side in (-1, 1):
                points.append((
                    rx + ux * station + nx * side * solid.arm_root_hole_transverse_spacing_mm / 2,
                    ry + uy * station + ny * side * solid.arm_root_hole_transverse_spacing_mm / 2,
                ))
        result[name] = points
    return result


def standoff_centers(solid: FPVFrameSolidSpec | None = None) -> list[tuple[float, float]]:
    solid = solid or FPVFrameSolidSpec()
    return [
        (-solid.standoff_x_offset_mm, -solid.standoff_y_offset_mm),
        (-solid.standoff_x_offset_mm, solid.standoff_y_offset_mm),
        (solid.standoff_x_offset_mm, -solid.standoff_y_offset_mm),
        (solid.standoff_x_offset_mm, solid.standoff_y_offset_mm),
    ]


def build_fpv_frame_parts(
    frame: FPVFrameSpec | None = None,
    solid: FPVFrameSolidSpec | None = None,
) -> dict[str, Any]:
    """Build separate STEP-ready solids: plates, arms and four standoffs."""
    # Lazy import avoids loading OCP for dimension-only use and unit tests.
    from build123d import Align, Box, Cylinder, Pos, Rot

    frame = frame or FPVFrameSpec()
    solid = solid or FPVFrameSolidSpec()
    frame.validate()
    solid.validate(frame)

    def drill(shape: Any, centers: list[tuple[float, float]], diameter: float,
              z0: float, depth: float) -> Any:
        for x, y in centers:
            cutter = Pos(x, y, z0) * Cylinder(
                diameter / 2, depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            shape = shape - cutter
        return shape

    # Two stack patterns (20 x 20 and 30.5 x 30.5) share the center origin.
    stack_centers = []
    for spacing in (20.0, 30.5):
        half = spacing / 2
        stack_centers.extend([
            (-half, -half), (-half, half), (half, -half), (half, half)
        ])
    roots = arm_root_centers(frame)
    root_holes_by_arm = arm_root_bolt_centers(frame, solid)
    root_holes = [point for points in root_holes_by_arm.values() for point in points]
    stands = standoff_centers(solid)

    plate_outline = (frame.top_plate_length_mm, frame.plate_width_mm)
    lower = Box(*plate_outline, frame.plate_thickness_mm,
                align=(Align.CENTER, Align.CENTER, Align.MIN))
    lower = drill(lower, stack_centers, solid.stack_hole_diameter_mm,
                  -1.0, frame.plate_thickness_mm + 2.0)
    lower = drill(lower, stands, frame.motor_hole_diameter_mm,
                  -1.0, frame.plate_thickness_mm + 2.0)
    lower = drill(lower, root_holes, solid.arm_root_hole_diameter_mm,
                  -1.0, frame.plate_thickness_mm + 2.0)

    upper_z = frame.standoff_height_mm + frame.plate_thickness_mm
    upper = Pos(0, 0, upper_z) * Box(
        *plate_outline, frame.plate_thickness_mm,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    upper = drill(upper, stack_centers, solid.stack_hole_diameter_mm,
                  upper_z - 1.0, frame.plate_thickness_mm + 2.0)
    upper = drill(upper, stands, frame.motor_hole_diameter_mm,
                  upper_z - 1.0, frame.plate_thickness_mm + 2.0)

    parts: dict[str, Any] = {"PLATE_BOTTOM": lower, "PLATE_TOP": upper}
    arm_z = frame.plate_thickness_mm
    for name, (mx, my) in frame.motor_centers().items():
        root_x, root_y = roots[name]
        ux, uy = mx / hypot(mx, my), my / hypot(mx, my)
        start_x = root_x - ux * solid.arm_root_overlap_mm
        start_y = root_y - uy * solid.arm_root_overlap_mm
        dx, dy = mx - start_x, my - start_y
        arm_length = hypot(dx, dy)
        angle_deg = atan2(dy, dx) * 180.0 / 3.141592653589793
        mid_x, mid_y = (start_x + mx) / 2, (start_y + my) / 2
        beam = Pos(mid_x, mid_y, arm_z) * Rot(0, 0, angle_deg) * Box(
            arm_length, frame.arm_width_mm, frame.arm_thickness_mm,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        motor_pad = Pos(mx, my, arm_z) * Box(
            solid.motor_pad_size_mm, solid.motor_pad_size_mm,
            frame.arm_thickness_mm,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        arm = beam + motor_pad
        arm = drill(arm, root_holes_by_arm[name],
                    solid.arm_root_hole_diameter_mm, arm_z - 1.0,
                    frame.arm_thickness_mm + 2.0)
        motor_holes = []
        half_pattern = frame.motor_mount_spacing_mm / 2
        for sx in (-half_pattern, half_pattern):
            for sy in (-half_pattern, half_pattern):
                motor_holes.append((mx + sx, my + sy))
        arm = drill(arm, motor_holes, frame.motor_hole_diameter_mm,
                    arm_z - 1.0, frame.arm_thickness_mm + 2.0)
        parts["ARM_" + name.upper()] = arm

    stand_z = frame.plate_thickness_mm
    for index, (x, y) in enumerate(stands, start=1):
        parts[f"STANDOFF_{index}"] = Pos(x, y, stand_z) * Cylinder(
            solid.standoff_outer_diameter_mm / 2,
            frame.standoff_height_mm,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    return parts


def export_fpv_frame_step(
    path: str | Path,
    frame: FPVFrameSpec | None = None,
    solid: FPVFrameSolidSpec | None = None,
) -> Path:
    """Export the multi-part frame assembly as a STEP compound."""
    from build123d import Compound, export_step

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    parts = build_fpv_frame_parts(frame, solid)
    assembly = Compound(children=list(parts.values()))
    export_step(assembly, str(path))
    return path
