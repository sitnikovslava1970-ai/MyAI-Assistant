"""High-level engineering exports for parametric outline modules."""
from pathlib import Path
from .dxf_export import export_outline_dxf
from .fpv_frame import FPVFrameSpec
from .propeller import PropellerSpec, rotate_points
from math import pi, hypot


def export_fpv_layout_dxf(path: str | Path, spec: FPVFrameSpec | None = None) -> Path:
    spec = spec or FPVFrameSpec()
    spec.validate()
    outlines = {}
    # Reference envelopes for the central plates. Arm solids and laminate contours
    # require the final selected geometry and fastener clearances.
    half_x, half_y = spec.plate_width_mm / 2, spec.top_plate_length_mm / 2
    outlines["TOP_PLATE"] = [(-half_x, -half_y), (half_x, -half_y), (half_x, half_y), (-half_x, half_y)]
    outlines["BOTTOM_PLATE"] = [(-half_x, -half_y), (half_x, -half_y), (half_x, half_y), (-half_x, half_y)]
    # Four arm envelopes connect the central plate boundary to each motor center.
    for motor_name, (mx, my) in spec.motor_centers().items():
        length = hypot(mx, my)
        ux, uy = mx / length, my / length
        px, py = -uy * spec.arm_width_mm / 2, ux * spec.arm_width_mm / 2
        scale = min(half_x / abs(ux), half_y / abs(uy))
        sx, sy = ux * scale, uy * scale
        outlines["ARM_" + motor_name.upper()] = [
            (sx + px, sy + py), (mx + px, my + py),
            (mx - px, my - py), (sx - px, sy - py)
        ]
    holes = []
    for motor_holes in spec.motor_holes().values():
        for x, y in motor_holes:
            holes.append((x, y, spec.motor_hole_diameter_mm / 2))
    return export_outline_dxf(path, outlines, holes)


def export_propeller_planform_dxf(path: str | Path, spec: PropellerSpec | None = None) -> Path:
    spec = spec or PropellerSpec()
    spec.validate()
    blade = spec.blade_outline()
    outlines = {"BLADE_A": blade, "BLADE_B": rotate_points(blade, pi)}
    circles = [(0.0, 0.0, spec.hub_diameter_mm / 2),
               (0.0, 0.0, spec.bore_diameter_mm / 2)]
    return export_outline_dxf(path, outlines, circles)
