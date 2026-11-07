"""Parametric first-pass solid model for the 7-inch Classic-X FPV frame.

The module imports build123d lazily so its dimensional helpers and tests can run
without loading the OpenCascade graphics stack. Geometry is a prototype only:
verify fastener access, laminate edge distances, camera/battery clearances and
structural performance before CNC manufacture or flight.
"""
from dataclasses import dataclass
from math import atan2, cos, hypot, sin, sqrt
from pathlib import Path
from typing import Any

from .fpv_frame import FPVFrameSpec


@dataclass(frozen=True)
class FPVFrameSolidSpec:
    """Manufacturing-oriented dimensions not yet fixed by the base frame brief."""

    arm_root_overlap_mm: float = 30.0
    motor_pad_size_mm: float = 28.0
    arm_root_hole_diameter_mm: float = 3.2
    arm_root_hole_longitudinal_pitch_mm: float = 12.0
    arm_root_hole_transverse_spacing_mm: float = 9.0
    stack_hole_diameter_mm: float = 3.2
    standoff_x_offset_mm: float = 65.0
    standoff_y_offset_mm: float = 27.5
    standoff_outer_diameter_mm: float = 6.0
    standoff_hole_diameter_mm: float = 3.2
    battery_strap_slot_center_x_mm: float = 35.0
    battery_strap_slot_length_mm: float = 24.0
    battery_strap_slot_width_mm: float = 4.0
    air_unit_mount_spacing_mm: float = 25.5
    air_unit_hole_diameter_mm: float = 2.2
    air_unit_center_y_mm: float = -20.0
    # Removable side-skid guard: two rails sit 2 mm below the Air Unit.
    air_unit_guard_mount_x_offset_mm: float = 20.0
    air_unit_guard_mount_y_outer_mm: float = -30.0
    air_unit_guard_mount_y_inner_mm: float = -10.0
    air_unit_guard_hole_diameter_mm: float = 2.2
    air_unit_guard_rail_length_mm: float = 30.0
    air_unit_guard_rail_width_mm: float = 4.0
    air_unit_guard_rail_thickness_mm: float = 2.0
    air_unit_guard_drop_mm: float = 2.0
    air_unit_guard_post_diameter_mm: float = 4.0
    camera_module_width_mm: float = 25.55
    camera_module_depth_mm: float = 20.0
    camera_module_height_mm: float = 23.3
    camera_side_clearance_mm: float = 0.7
    camera_side_plate_thickness_mm: float = 2.0
    camera_mount_hole_pitch_mm: float = 16.0
    camera_mount_slot_width_mm: float = 2.2
    camera_mount_slot_length_mm: float = 4.5
    camera_center_y_mm: float = 55.0
    camera_center_z_mm: float = 21.6
    camera_base_width_mm: float = 36.0
    camera_base_length_mm: float = 50.0
    camera_base_center_y_mm: float = 55.5
    camera_base_mount_spacing_x_mm: float = 24.0
    camera_base_mount_y_mm: float = 33.5
    camera_side_foot_spacing_x_mm: float = 27.0
    camera_side_foot_y_mm: float = 64.0065
    camera_side_foot_hole_pitch_y_mm: float = 10.0
    camera_support_foot_width_mm: float = 9.0
    camera_support_foot_length_mm: float = 18.0
    camera_support_foot_thickness_mm: float = 2.0
    camera_support_web_width_mm: float = 8.0
    camera_support_web_depth_mm: float = 4.0
    camera_base_hole_diameter_mm: float = 3.2

    def validate(self, frame: FPVFrameSpec) -> None:
        frame.validate()
        for name, value in self.__dict__.items():
            if name in ("air_unit_center_y_mm", "air_unit_guard_mount_y_outer_mm",
                        "air_unit_guard_mount_y_inner_mm"):
                continue
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        if self.arm_root_overlap_mm >= frame.wheelbase_mm / 2:
            raise ValueError("Arm root overlap is too large")
        if 1.5 * self.arm_root_hole_longitudinal_pitch_mm >= self.arm_root_overlap_mm:
            raise ValueError("Arm root hole stations must remain inside the arm overlap")
        if self.motor_pad_size_mm < frame.motor_mount_spacing_mm + frame.motor_hole_diameter_mm:
            raise ValueError("Motor pad is too small for the motor hole pattern")
        if self.arm_root_hole_transverse_spacing_mm + self.arm_root_hole_diameter_mm >= frame.arm_width_mm:
            raise ValueError("Arm root bolt rows do not fit within the arm width")
        if self.standoff_x_offset_mm >= frame.top_plate_length_mm / 2:
            raise ValueError("Standoff X position is outside the center plate")
        if self.standoff_y_offset_mm >= frame.plate_width_mm / 2:
            raise ValueError("Standoff Y position is outside the center plate")
        if self.battery_strap_slot_length_mm <= self.battery_strap_slot_width_mm:
            raise ValueError("Battery strap slot length must exceed its width")
        if self.battery_strap_slot_center_x_mm + self.battery_strap_slot_width_mm / 2 >= frame.top_plate_length_mm / 2:
            raise ValueError("Battery strap slot is outside the center plate")
        if self.air_unit_mount_spacing_mm + self.air_unit_hole_diameter_mm >= min(frame.top_plate_length_mm, frame.plate_width_mm):
            raise ValueError("DJI O4 mounting pattern does not fit the center plate")
        if abs(self.air_unit_center_y_mm) + self.air_unit_mount_spacing_mm / 2 + self.air_unit_hole_diameter_mm / 2 > frame.plate_width_mm / 2:
            raise ValueError("DJI O4 mounting pattern is outside the center plate")
        guard_centers_y = (self.air_unit_guard_mount_y_outer_mm,
                            self.air_unit_guard_mount_y_inner_mm)
        if self.air_unit_guard_mount_x_offset_mm + self.air_unit_guard_post_diameter_mm / 2 >= frame.top_plate_length_mm / 2:
            raise ValueError("Air Unit guard mounts are outside the center plate")
        if any(abs(y) + self.air_unit_guard_post_diameter_mm / 2 >= frame.plate_width_mm / 2
               for y in guard_centers_y):
            raise ValueError("Air Unit guard mounts are outside the center plate")
        guard_center_y = sum(guard_centers_y) / 2
        if abs(guard_center_y) + self.air_unit_guard_rail_length_mm / 2 >= frame.plate_width_mm / 2:
            raise ValueError("Air Unit guard rails are outside the center plate")
        if self.air_unit_guard_rail_length_mm < abs(
            self.air_unit_guard_mount_y_outer_mm - self.air_unit_guard_mount_y_inner_mm
        ) + self.air_unit_guard_post_diameter_mm:
            raise ValueError("Air Unit guard rails are too short for their supports")
        if self.air_unit_guard_mount_x_offset_mm <= (
            self.camera_module_width_mm / 2 + self.air_unit_guard_post_diameter_mm / 2
        ):
            raise ValueError("Air Unit guard supports overlap the Air Unit envelope")
        if abs(self.camera_base_mount_y_mm) + self.camera_base_hole_diameter_mm / 2 > frame.plate_width_mm / 2:
            raise ValueError("Camera base mounting holes are outside the lower plate")
        if self.camera_mount_slot_length_mm < self.camera_mount_slot_width_mm:
            raise ValueError("Camera adjustment slot length must exceed its width")
        if self.camera_base_width_mm <= self.camera_module_width_mm + 2 * self.camera_side_clearance_mm:
            raise ValueError("Camera base is too narrow for the camera bracket")


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
        plate_half_x = frame.top_plate_length_mm / 2
        plate_half_y = frame.plate_width_mm / 2
        hole_radius = solid.arm_root_hole_diameter_mm / 2
        for x, y in points:
            if abs(x) + hole_radius > plate_half_x or abs(y) + hole_radius > plate_half_y:
                raise ValueError(
                    f"Arm root bolt hole for {name} breaks the center-plate edge"
                )
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



def battery_strap_slot_centers(solid: FPVFrameSolidSpec | None = None) -> list[tuple[float, float]]:
    solid = solid or FPVFrameSolidSpec()
    return [(-solid.battery_strap_slot_center_x_mm, 0.0),
            (solid.battery_strap_slot_center_x_mm, 0.0)]


def air_unit_mount_centers(solid: FPVFrameSolidSpec | None = None) -> list[tuple[float, float]]:
    solid = solid or FPVFrameSolidSpec()
    half = solid.air_unit_mount_spacing_mm / 2
    cy = solid.air_unit_center_y_mm
    return [(-half, cy-half), (-half, cy+half), (half, cy-half), (half, cy+half)]


def air_unit_guard_mount_centers(
    solid: FPVFrameSolidSpec | None = None,
) -> list[tuple[float, float]]:
    """Four M2 guard-support centers outside the DJI O4 Air Unit envelope."""
    solid = solid or FPVFrameSolidSpec()
    return [
        (x, y)
        for x in (-solid.air_unit_guard_mount_x_offset_mm,
                  solid.air_unit_guard_mount_x_offset_mm)
        for y in (solid.air_unit_guard_mount_y_outer_mm,
                  solid.air_unit_guard_mount_y_inner_mm)
    ]


def camera_base_mount_centers(solid: FPVFrameSolidSpec | None = None) -> list[tuple[float, float]]:
    solid = solid or FPVFrameSolidSpec()
    half = solid.camera_base_mount_spacing_x_mm / 2
    return [(-half, solid.camera_base_mount_y_mm), (half, solid.camera_base_mount_y_mm)]


def camera_side_foot_centers(solid: FPVFrameSolidSpec | None = None) -> list[tuple[float, float]]:
    """Four M3 holes, two per separate camera support foot."""
    solid = solid or FPVFrameSolidSpec()
    half_x = solid.camera_side_foot_spacing_x_mm / 2
    half_y = solid.camera_side_foot_hole_pitch_y_mm / 2
    return [
        (x, y)
        for x in (-half_x, half_x)
        for y in (solid.camera_side_foot_y_mm - half_y,
                  solid.camera_side_foot_y_mm + half_y)
    ]

def build_fpv_frame_parts(
    frame: FPVFrameSpec | None = None,
    solid: FPVFrameSolidSpec | None = None,
) -> dict[str, Any]:
    """Build the frame, camera bracket and reference envelopes as STEP-ready solids."""
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

    def add_rounded_slots(shape: Any, centers: list[tuple[float, float]],
                          length: float, width: float, z0: float, depth: float) -> Any:
        radius = width / 2
        straight = length - width
        for x, y in centers:
            shape = shape - (Pos(x, y, z0) * Box(
                width, straight, depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            ))
            for end_y in (y - straight / 2, y + straight / 2):
                shape = shape - (Pos(x, end_y, z0) * Cylinder(
                    radius, depth,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                ))
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
    strap_slots = [(-solid.battery_strap_slot_center_x_mm, 0.0),
                   (solid.battery_strap_slot_center_x_mm, 0.0)]
    air_half = solid.air_unit_mount_spacing_mm / 2
    air_y = solid.air_unit_center_y_mm
    air_holes = [(-air_half, air_y-air_half), (-air_half, air_y+air_half),
                 (air_half, air_y-air_half), (air_half, air_y+air_half)]
    camera_base_holes = [
        (-solid.camera_base_mount_spacing_x_mm/2, solid.camera_base_mount_y_mm),
        (solid.camera_base_mount_spacing_x_mm/2, solid.camera_base_mount_y_mm),
    ]
    camera_foot_holes = camera_side_foot_centers(solid)

    plate_outline = (frame.top_plate_length_mm, frame.plate_width_mm)
    lower = Box(*plate_outline, frame.plate_thickness_mm,
                align=(Align.CENTER, Align.CENTER, Align.MIN))
    lower = drill(lower, stack_centers, solid.stack_hole_diameter_mm,
                  -1.0, frame.plate_thickness_mm + 2.0)
    lower = drill(lower, stands, solid.standoff_hole_diameter_mm,
                  -1.0, frame.plate_thickness_mm + 2.0)
    lower = drill(lower, root_holes, solid.arm_root_hole_diameter_mm,
                  -1.0, frame.plate_thickness_mm + 2.0)
    lower = drill(lower, camera_base_holes, solid.camera_base_hole_diameter_mm,
                  -1.0, frame.plate_thickness_mm + 2.0)
    lower = drill(lower, air_holes, solid.air_unit_hole_diameter_mm,
                  -1.0, frame.plate_thickness_mm + 2.0)
    guard_holes = air_unit_guard_mount_centers(solid)
    lower = drill(lower, guard_holes, solid.air_unit_guard_hole_diameter_mm,
                  -1.0, frame.plate_thickness_mm + 2.0)
    lower = add_rounded_slots(lower, strap_slots, solid.battery_strap_slot_length_mm,
                              solid.battery_strap_slot_width_mm, -1.0,
                              frame.plate_thickness_mm + 2.0)

    upper_z = frame.standoff_height_mm + frame.plate_thickness_mm
    upper = Pos(0, 0, upper_z) * Box(
        *plate_outline, frame.plate_thickness_mm,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    upper = drill(upper, stack_centers, solid.stack_hole_diameter_mm,
                  upper_z - 1.0, frame.plate_thickness_mm + 2.0)
    upper = drill(upper, stands, solid.standoff_hole_diameter_mm,
                  upper_z - 1.0, frame.plate_thickness_mm + 2.0)
    upper = add_rounded_slots(upper, strap_slots, solid.battery_strap_slot_length_mm,
                              solid.battery_strap_slot_width_mm, upper_z - 1.0,
                              frame.plate_thickness_mm + 2.0)

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
    # Front camera bracket: fixed nominal angle with short adjustment slots.
    camera_angle = frame.camera_angle_deg
    camera_y = solid.camera_center_y_mm
    camera_z = solid.camera_center_z_mm
    side_x = (
        solid.camera_module_width_mm / 2
        + solid.camera_side_clearance_mm
        + solid.camera_side_plate_thickness_mm / 2
    )
    base_plate = Pos(0, solid.camera_base_center_y_mm, frame.plate_thickness_mm) * Box(
        solid.camera_base_width_mm, solid.camera_base_length_mm,
        frame.plate_thickness_mm,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    base_plate = drill(
        base_plate, camera_base_holes, solid.camera_base_hole_diameter_mm,
        frame.plate_thickness_mm - 1.0, frame.plate_thickness_mm + 2.0,
    )
    base_plate = drill(
        base_plate, camera_foot_holes, solid.camera_base_hole_diameter_mm,
        frame.plate_thickness_mm - 1.0, frame.plate_thickness_mm + 2.0,
    )
    # Relieve both rear corners so the base plate clears the front-arm envelopes.
    # The 4 x 4 mm notches leave the camera-base M3 holes untouched.
    for corner_x in (-solid.camera_base_width_mm / 2, solid.camera_base_width_mm / 2):
        corner_relief = Pos(
            corner_x, solid.camera_base_center_y_mm - solid.camera_base_length_mm / 2,
            frame.plate_thickness_mm - 1.0,
        ) * Box(
            4.0, 4.0, frame.plate_thickness_mm + 2.0,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        base_plate = base_plate - corner_relief
    parts["CAMERA_BASE_PLATE"] = base_plate

    # Separate flat carbon camera side plates. Their support feet are separate
    # non-carbon brackets so the side plates remain valid 2D cut parts.
    support_x = solid.camera_side_foot_spacing_x_mm / 2
    local_bottom_z = -solid.camera_module_height_mm / 2
    support_top_z = local_bottom_z
    support_bottom_z = (
        frame.plate_thickness_mm * 2 + solid.camera_support_foot_thickness_mm - camera_z
    ) / cos(camera_angle * 3.141592653589793 / 180.0)
    support_web_height = support_top_z - support_bottom_z
    if support_web_height <= 0:
        raise ValueError("Camera support web has invalid height")
    support_web_center_z = (support_bottom_z + support_top_z) / 2
    support_foot_center_y = camera_y - support_bottom_z * sin(
        camera_angle * 3.141592653589793 / 180.0
    )

    for side_name, sign in (("LEFT", -1), ("RIGHT", 1)):
        panel_x = sign * side_x
        support_center_x = sign * support_x
        local = Pos(panel_x, camera_y, camera_z) * Rot(camera_angle, 0, 0)
        side_plate = local * Box(
            solid.camera_side_plate_thickness_mm,
            solid.camera_module_depth_mm,
            solid.camera_module_height_mm,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
        straight = solid.camera_mount_slot_length_mm - solid.camera_mount_slot_width_mm
        for z_offset in (-solid.camera_mount_hole_pitch_mm / 2,
                         solid.camera_mount_hole_pitch_mm / 2):
            slot_box = local * Pos(0, 0, z_offset) * Box(
                solid.camera_side_plate_thickness_mm + 2.0,
                straight, solid.camera_mount_slot_width_mm,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            )
            side_plate = side_plate - slot_box
            for y_offset in (-straight / 2, straight / 2):
                slot_end = (
                    local * Pos(0, y_offset, z_offset) * Rot(0, 90, 0)
                    * Cylinder(
                        solid.camera_mount_slot_width_mm / 2,
                        solid.camera_side_plate_thickness_mm + 2.0,
                        align=(Align.CENTER, Align.CENTER, Align.CENTER),
                    )
                )
                side_plate = side_plate - slot_end
        parts[f"CAMERA_SIDE_{side_name}"] = side_plate

        # Separate PA12-CF/aluminium support: horizontal foot on the camera
        # base plate and an angled web terminating at the side-plate lower edge.
        foot = Pos(
            support_center_x, support_foot_center_y,
            frame.plate_thickness_mm * 2 + solid.camera_support_foot_thickness_mm / 2,
        ) * Box(
            solid.camera_support_foot_width_mm,
            solid.camera_support_foot_length_mm,
            solid.camera_support_foot_thickness_mm,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
        web = (
            Pos(support_center_x, camera_y, camera_z)
            * Rot(camera_angle, 0, 0)
            * Pos(0, 0, support_web_center_z)
            * Box(
                solid.camera_support_web_width_mm,
                solid.camera_support_web_depth_mm,
                support_web_height,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            )
        )
        support = foot + web
        side_holes = [
            (support_center_x, support_foot_center_y - solid.camera_side_foot_hole_pitch_y_mm / 2),
            (support_center_x, support_foot_center_y + solid.camera_side_foot_hole_pitch_y_mm / 2),
        ]
        support = drill(
            support, side_holes, solid.camera_base_hole_diameter_mm,
            frame.plate_thickness_mm * 2 - 1.0,
            solid.camera_support_foot_thickness_mm + 2.0,
        )
        parts[f"CAMERA_SUPPORT_{side_name}"] = support

    # REF_ components are visual envelopes only, not manufactured parts.
    parts["REF_CAMERA_O4_PRO"] = (
        Pos(0, camera_y, camera_z) * Rot(camera_angle, 0, 0)
        * Box(
            solid.camera_module_width_mm,
            solid.camera_module_depth_mm,
            solid.camera_module_height_mm,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
    )
    parts["REF_AIR_UNIT_O4_PRO"] = Pos(
        0, solid.air_unit_center_y_mm, -13.0
    ) * Box(33.5, 33.5, 13.0,
            align=(Align.CENTER, Align.CENTER, Align.MIN))

    # Removable underside side-skid guard. The rails are outside the Air Unit
    # footprint and sit 2 mm below its bottom face, leaving the center open
    # for airflow and access. Four M2 clearance holes are added to PLATE_BOTTOM.
    guard_center_y = (
        solid.air_unit_guard_mount_y_outer_mm
        + solid.air_unit_guard_mount_y_inner_mm
    ) / 2
    rail_z_center = (
        -13.0 - solid.air_unit_guard_drop_mm
        + solid.air_unit_guard_rail_thickness_mm / 2
    )
    for side_name, x in (
        ("LEFT", -solid.air_unit_guard_mount_x_offset_mm),
        ("RIGHT", solid.air_unit_guard_mount_x_offset_mm),
    ):
        rail = Pos(x, guard_center_y, rail_z_center) * Box(
            solid.air_unit_guard_rail_width_mm,
            solid.air_unit_guard_rail_length_mm,
            solid.air_unit_guard_rail_thickness_mm,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
        local_holes = [
            (x, solid.air_unit_guard_mount_y_outer_mm),
            (x, solid.air_unit_guard_mount_y_inner_mm),
        ]
        rail = drill(
            rail, local_holes, solid.air_unit_guard_hole_diameter_mm,
            rail_z_center - solid.air_unit_guard_rail_thickness_mm,
            solid.air_unit_guard_rail_thickness_mm * 2,
        )
        parts[f"AIR_UNIT_GUARD_RAIL_{side_name}"] = rail

    for index, (x, y) in enumerate(guard_holes, start=1):
        post = Pos(x, y, -13.0) * Cylinder(
            solid.air_unit_guard_post_diameter_mm / 2,
            13.0,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        post = drill(
            post, [(x, y)], solid.air_unit_guard_hole_diameter_mm,
            -14.0, 15.0,
        )
        parts[f"AIR_UNIT_GUARD_POST_{index}"] = post

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
