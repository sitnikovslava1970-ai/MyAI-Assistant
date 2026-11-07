"""Build a closed planar CAD sketch from explicitly confirmed profile features.

Image detections are proposals only. This module accepts only features that
have already been reviewed and assigned an ADD or SUBTRACT operation.
"""
from dataclasses import dataclass
from math import isfinite
from typing import Literal

from build123d import BuildSketch, Circle, Locations, Mode, Plane, Rectangle


@dataclass(frozen=True)
class ConfirmedProfileFeature:
    kind: Literal["circle", "rectangle"]
    operation: Literal["add", "subtract"]
    center_x_mm: float
    center_y_mm: float
    width_mm: float = 0.0
    height_mm: float = 0.0
    radius_mm: float = 0.0


def _validate_feature(feature: ConfirmedProfileFeature) -> None:
    values = (feature.center_x_mm, feature.center_y_mm)
    if not all(isfinite(value) for value in values):
        raise ValueError("profile feature coordinates must be finite")
    if feature.kind == "circle":
        if not isfinite(feature.radius_mm) or feature.radius_mm <= 0:
            raise ValueError("circle radius_mm must be finite and greater than zero")
    elif feature.kind == "rectangle":
        if (
            not isfinite(feature.width_mm) or not isfinite(feature.height_mm)
            or feature.width_mm <= 0 or feature.height_mm <= 0
        ):
            raise ValueError("rectangle width_mm and height_mm must be finite and greater than zero")
    else:
        raise ValueError("unsupported profile feature kind")
    if feature.operation not in {"add", "subtract"}:
        raise ValueError("profile operation must be 'add' or 'subtract'")


def build_confirmed_sketch(features: tuple[ConfirmedProfileFeature, ...]):
    """Return a planar XY Sketch after validating explicit feature intent.

    At least one additive outer profile is required. A detected circle is never
    assumed to be a hole: callers must explicitly mark it as subtractive.
    """
    if not features:
        raise ValueError("at least one confirmed profile feature is required")
    for feature in features:
        _validate_feature(feature)
    if features[0].operation != "add":
        raise ValueError("the first profile feature must be additive")

    with BuildSketch(Plane.XY) as profile:
        for feature in features:
            mode = Mode.ADD if feature.operation == "add" else Mode.SUBTRACT
            with Locations((feature.center_x_mm, feature.center_y_mm)):
                if feature.kind == "circle":
                    Circle(feature.radius_mm, mode=mode)
                else:
                    Rectangle(feature.width_mm, feature.height_mm, mode=mode)

    if not profile.sketch.faces():
        raise ValueError("confirmed features did not produce a closed planar profile")
    return profile.sketch
