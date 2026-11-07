import pytest

from cad.sketch_photo.profile_builder import (
    ConfirmedProfileFeature,
    build_confirmed_sketch,
)


def test_builds_closed_rectangle_with_explicit_hole():
    sketch = build_confirmed_sketch((
        ConfirmedProfileFeature(
            kind="rectangle", operation="add",
            center_x_mm=0, center_y_mm=0, width_mm=40, height_mm=20,
        ),
        ConfirmedProfileFeature(
            kind="circle", operation="subtract",
            center_x_mm=0, center_y_mm=0, radius_mm=2,
        ),
    ))
    assert len(sketch.faces()) == 1
    assert sketch.area == pytest.approx(800 - 3.141592653589793 * 4, rel=1e-5)


def test_builds_multiple_additive_profiles():
    sketch = build_confirmed_sketch((
        ConfirmedProfileFeature(
            kind="rectangle", operation="add",
            center_x_mm=-10, center_y_mm=0, width_mm=10, height_mm=10,
        ),
        ConfirmedProfileFeature(
            kind="circle", operation="add",
            center_x_mm=10, center_y_mm=0, radius_mm=5,
        ),
    ))
    assert sketch.area == pytest.approx(100 + 3.141592653589793 * 25, rel=1e-5)


def test_rejects_empty_or_subtractive_first_profile():
    with pytest.raises(ValueError):
        build_confirmed_sketch(())
    with pytest.raises(ValueError):
        build_confirmed_sketch((
            ConfirmedProfileFeature(
                kind="circle", operation="subtract",
                center_x_mm=0, center_y_mm=0, radius_mm=2,
            ),
        ))


def test_rejects_invalid_dimensions():
    with pytest.raises(ValueError):
        build_confirmed_sketch((
            ConfirmedProfileFeature(
                kind="rectangle", operation="add",
                center_x_mm=0, center_y_mm=0, width_mm=0, height_mm=10,
            ),
        ))
