import math

import pytest

from cad.sketch_photo.profile_builder import ConfirmedProfileFeature
from cad.sketch_photo.solid_builder import build_extruded_solid


def test_extrudes_confirmed_plate_profile_with_hole():
    solid = build_extruded_solid((
        ConfirmedProfileFeature(
            kind="rectangle", operation="add",
            center_x_mm=0, center_y_mm=0, width_mm=40, height_mm=20,
        ),
        ConfirmedProfileFeature(
            kind="circle", operation="subtract",
            center_x_mm=0, center_y_mm=0, radius_mm=2,
        ),
    ), thickness_mm=3)
    expected_area = 800 - math.pi * 4
    assert len(solid.solids()) == 1
    assert solid.is_valid
    assert solid.volume == pytest.approx(expected_area * 3, rel=1e-5)


def test_rejects_zero_negative_and_non_finite_thickness():
    feature = ConfirmedProfileFeature(
        kind="rectangle", operation="add",
        center_x_mm=0, center_y_mm=0, width_mm=10, height_mm=10,
    )
    for thickness in (0, -1, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            build_extruded_solid((feature,), thickness)
