"""Extrude an explicitly confirmed planar sketch into a validated solid."""
from math import isfinite

from build123d import extrude

from cad.sketch_photo.profile_builder import (
    ConfirmedProfileFeature,
    build_confirmed_sketch,
)


def build_extruded_solid(
    features: tuple[ConfirmedProfileFeature, ...],
    thickness_mm: float,
):
    """Build a positive-Z solid from a confirmed XY profile.

    This is a geometric solid-generation step, not manufacturing approval.
    """
    if not isinstance(thickness_mm, (int, float)) or not isfinite(thickness_mm):
        raise ValueError("thickness_mm must be a finite number")
    if thickness_mm <= 0:
        raise ValueError("thickness_mm must be greater than zero")

    sketch = build_confirmed_sketch(features)
    solid = extrude(sketch, amount=float(thickness_mm))

    solids = solid.solids()
    if len(solids) != 1:
        raise ValueError(f"expected one solid body, got {len(solids)}")
    if not solid.is_valid:
        raise ValueError("generated solid failed CAD validity check")
    if solid.volume <= 0:
        raise ValueError("generated solid has no positive volume")
    return solid
