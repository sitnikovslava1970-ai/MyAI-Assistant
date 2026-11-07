"""Pixel-to-millimetre calibration from a user-confirmed reference length."""
from math import isfinite


def pixels_per_mm(pixel_length: float, real_length_mm: float) -> float:
    if not isfinite(pixel_length) or pixel_length <= 0:
        raise ValueError("pixel_length must be finite and greater than zero")
    if not isfinite(real_length_mm) or real_length_mm <= 0:
        raise ValueError("real_length_mm must be finite and greater than zero")
    return pixel_length / real_length_mm


def pixels_to_mm(pixel_distance: float, scale_px_per_mm: float) -> float:
    if not isfinite(scale_px_per_mm) or scale_px_per_mm <= 0:
        raise ValueError("scale_px_per_mm must be finite and greater than zero")
    return pixel_distance / scale_px_per_mm
