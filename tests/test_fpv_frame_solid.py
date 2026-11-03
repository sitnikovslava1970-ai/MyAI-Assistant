import pytest

from cad.modules.fpv_frame import FPVFrameSpec
from cad.modules.fpv_frame_solid import (
    FPVFrameSolidSpec,
    arm_root_bolt_centers,
    arm_root_centers,
    standoff_centers,
)


def test_arm_root_centers_are_symmetric_and_on_plate_boundary():
    frame = FPVFrameSpec(arm_width_mm=18.0)
    roots = arm_root_centers(frame)
    assert roots["front_left"] == pytest.approx((-37.5, 37.5))
    assert roots["front_right"] == pytest.approx((37.5, 37.5))
    assert roots["rear_left"] == pytest.approx((-37.5, -37.5))
    assert roots["rear_right"] == pytest.approx((37.5, -37.5))


def test_each_arm_has_four_root_bolt_holes():
    frame = FPVFrameSpec(arm_width_mm=18.0)
    holes = arm_root_bolt_centers(frame)
    assert set(holes) == {"front_left", "front_right", "rear_left", "rear_right"}
    assert all(len(points) == 4 for points in holes.values())


def test_default_solid_spec_fits_18mm_arm_and_plate():
    frame = FPVFrameSpec(arm_width_mm=18.0)
    solid = FPVFrameSolidSpec()
    solid.validate(frame)
    assert len(standoff_centers(solid)) == 4


def test_motor_pad_is_wide_enough_for_19mm_pattern():
    frame = FPVFrameSpec(arm_width_mm=18.0)
    solid = FPVFrameSolidSpec()
    assert solid.motor_pad_size_mm >= (
        frame.motor_mount_spacing_mm + frame.motor_hole_diameter_mm
    )


def test_invalid_root_bolt_row_spacing_is_rejected():
    frame = FPVFrameSpec(arm_width_mm=18.0)
    solid = FPVFrameSolidSpec(arm_root_hole_transverse_spacing_mm=16.0)
    with pytest.raises(ValueError):
        solid.validate(frame)
