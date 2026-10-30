"""Shared dimensional validation and hole-pattern helpers. All dimensions are mm."""
from dataclasses import dataclass


@dataclass(frozen=True)
class HolePattern:
    centers: tuple[tuple[float, float], ...]
    diameter_mm: float


def rectangular_hole_pattern(length_mm: float, width_mm: float, inset_mm: float,
                              diameter_mm: float) -> HolePattern:
    values = (length_mm, width_mm, inset_mm, diameter_mm)
    if any(v <= 0 for v in values):
        raise ValueError("All dimensions must be positive")
    if inset_mm * 2 >= min(length_mm, width_mm):
        raise ValueError("Inset leaves no usable plate area")
    if diameter_mm >= min(length_mm, width_mm) - 2 * inset_mm:
        raise ValueError("Hole diameter does not fit inside the inset boundary")
    x = length_mm / 2 - inset_mm
    y = width_mm / 2 - inset_mm
    return HolePattern(((-x, -y), (-x, y), (x, -y), (x, y)), diameter_mm)


def validate_positive_dimensions(**dimensions: float) -> None:
    invalid = [name for name, value in dimensions.items() if value <= 0]
    if invalid:
        raise ValueError("Dimensions must be positive: " + ", ".join(invalid))
