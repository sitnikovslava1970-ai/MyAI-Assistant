"""Pixel-to-millimetre calibration from a user-confirmed reference length."""


def pixels_per_mm(pixel_length: float, real_length_mm: float) -> float:
    if pixel_length <= 0:
        raise ValueError("pixel_length must be greater than zero")
    if real_length_mm <= 0:
        raise ValueError("real_length_mm must be greater than zero")
    return pixel_length / real_length_mm


def pixels_to_mm(pixel_distance: float, scale_px_per_mm: float) -> float:
    if scale_px_per_mm <= 0:
        raise ValueError("scale_px_per_mm must be greater than zero")
    return pixel_distance / scale_px_per_mm
