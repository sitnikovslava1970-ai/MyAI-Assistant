"""Parametric two-blade propeller planform helpers.

The generated outline is a preliminary 2D envelope, not an aerodynamic or
production-ready propeller blade. Pitch, airfoil, twist, material and stress
analysis must be engineered and validated separately.
"""
from dataclasses import asdict, dataclass
from math import cos, pi, sin


@dataclass(frozen=True)
class PropellerSpec:
    diameter_in: float = 7.0
    blade_count: int = 2
    bore_diameter_mm: float = 5.0
    hub_diameter_mm: float = 16.0
    hub_thickness_mm: float = 7.0
    root_chord_mm: float = 18.0
    tip_chord_mm: float = 8.0
    sweep_mm: float = 8.0

    @property
    def diameter_mm(self) -> float:
        return self.diameter_in * 25.4

    def validate(self) -> None:
        if self.diameter_in <= 0 or self.blade_count != 2:
            raise ValueError("This first generator supports a positive diameter and exactly 2 blades")
        for key, value in asdict(self).items():
            if key != "blade_count" and value <= 0:
                raise ValueError(f"{key} must be positive")
        if self.bore_diameter_mm >= self.hub_diameter_mm:
            raise ValueError("Bore diameter must be smaller than hub diameter")
        if self.hub_diameter_mm >= self.diameter_mm:
            raise ValueError("Hub diameter must be smaller than propeller diameter")

    def blade_outline(self, samples: int = 24) -> list[tuple[float, float]]:
        """Return one blade outline in XY using a simple swept planform envelope."""
        self.validate()
        if samples < 4:
            raise ValueError("At least four stations are required")
        hub_r = self.hub_diameter_mm / 2
        tip_r = self.diameter_mm / 2
        span = tip_r - hub_r
        leading, trailing = [], []
        for i in range(samples + 1):
            t = i / samples
            radius = hub_r + span * t
            chord = self.root_chord_mm + (self.tip_chord_mm - self.root_chord_mm) * t
            sweep = self.sweep_mm * t * t
            leading.append((sweep, radius))
            trailing.append((sweep + chord, radius))
        return leading + list(reversed(trailing))

    def to_dict(self) -> dict:
        self.validate()
        return {**asdict(self), "diameter_mm": self.diameter_mm, "units": "mm",
                "blade_outline_xy_mm": self.blade_outline(),
                "note": "Preliminary planform only; not safe for manufacture or flight without full blade design and testing."}


def rotate_points(points: list[tuple[float, float]], angle_rad: float):
    c, s = cos(angle_rad), sin(angle_rad)
    return [(x*c-y*s, x*s+y*c) for x, y in points]
