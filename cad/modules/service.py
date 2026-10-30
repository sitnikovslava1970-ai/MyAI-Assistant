"""High-level engineering exports for parametric outline modules."""
from pathlib import Path
from .dxf_export import export_outline_dxf
from .fpv_frame import FPVFrameSpec
from .propeller import PropellerSpec, rotate_points
from math import pi


def export_fpv_layout_dxf(path: str | Path, spec: FPVFrameSpec | None = None) -> Path:
    spec = spec or FPVFrameSpec()
    spec.validate()
    outlines = {}
    # Reference envelopes for the central plates. Arm solids and laminate contours
    # require the final selected geometry and fastener clearances.
    l, w = spec.top_plate_length_mm / 2, spec.plate_width_mm / 2
    outlines["CENTER_PLATE"] = [(-l, -w), (l, -w), (l, w), (-l, w)]
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
