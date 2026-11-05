"""Parametric specification helpers for a classic-X 7-inch FPV frame.

Coordinate convention: X is transverse; Y is longitudinal and +Y points forward. The center plate is 75 mm in X by 160 mm in Y.

This module calculates layout and mounting coordinates; it does not certify
structural strength, vibration behaviour or CNC manufacturability.
"""
from dataclasses import asdict, dataclass
from math import sqrt


@dataclass(frozen=True)
class FPVFrameSpec:
    wheelbase_mm: float = 315.0
    arm_width_mm: float = 18.0
    arm_thickness_mm: float = 5.0
    top_plate_length_mm: float = 160.0
    plate_width_mm: float = 75.0
    plate_thickness_mm: float = 2.0
    motor_mount_spacing_mm: float = 19.0
    motor_hole_diameter_mm: float = 3.2
    standoff_height_mm: float = 25.0
    camera_angle_deg: float = 30.0

    def validate(self) -> None:
        for key, value in asdict(self).items():
            if value <= 0:
                raise ValueError(f"{key} must be positive")
        if self.motor_mount_spacing_mm >= self.wheelbase_mm:
            raise ValueError("Motor mount spacing is inconsistent with wheelbase")
        if self.motor_hole_diameter_mm >= self.motor_mount_spacing_mm:
            raise ValueError("Motor hole diameter is too large")

    def motor_centers(self) -> dict[str, tuple[float, float]]:
        """Motor centers for a square classic-X layout, diagonal wheelbase."""
        self.validate()
        offset = self.wheelbase_mm / (2 * sqrt(2))
        return {
            "front_left": (-offset, offset),
            "front_right": (offset, offset),
            "rear_left": (-offset, -offset),
            "rear_right": (offset, -offset),
        }

    def motor_holes(self) -> dict[str, list[tuple[float, float]]]:
        half = self.motor_mount_spacing_mm / 2
        result = {}
        for name, (cx, cy) in self.motor_centers().items():
            result[name] = [(cx-half, cy-half), (cx-half, cy+half),
                            (cx+half, cy-half), (cx+half, cy+half)]
        return result

    def to_dict(self) -> dict:
        self.validate()
        return {**asdict(self), "units": "mm", "motor_centers": self.motor_centers(),
                "motor_holes": self.motor_holes(),
                "center_plate_size_xy_mm": [self.plate_width_mm, self.top_plate_length_mm],
                "coordinate_convention": {"x": "transverse", "y": "longitudinal; +Y forward"},
                "note": "Layout reference only; verify all dimensions against actual components."}
