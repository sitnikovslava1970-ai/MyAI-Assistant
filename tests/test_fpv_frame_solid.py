import pytest

from cad.modules.fpv_frame import FPVFrameSpec
from cad.modules.fpv_frame_solid import (
    FPVFrameSolidSpec,
    arm_root_bolt_centers,
    arm_root_centers,
    standoff_centers,
    battery_strap_slot_centers,
    air_unit_mount_centers,
    camera_base_mount_centers,
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



def test_root_bolt_holes_keep_full_diameter_inside_lower_plate():
    frame = FPVFrameSpec(arm_width_mm=18.0)
    solid = FPVFrameSolidSpec()
    holes = arm_root_bolt_centers(frame, solid)
    half_x = frame.top_plate_length_mm / 2
    half_y = frame.plate_width_mm / 2
    radius = solid.arm_root_hole_diameter_mm / 2
    for points in holes.values():
        for x, y in points:
            assert abs(x) + radius <= half_x
            assert abs(y) + radius <= half_y



def test_accessory_mount_patterns_fit_their_plate_envelopes():
    frame = FPVFrameSpec(arm_width_mm=18.0)
    solid = FPVFrameSolidSpec()
    solid.validate(frame)

    for x, y in battery_strap_slot_centers(solid):
        assert abs(x) + solid.battery_strap_slot_width_mm / 2 < frame.top_plate_length_mm / 2
        assert abs(y) + solid.battery_strap_slot_length_mm / 2 < frame.plate_width_mm / 2

    for x, y in air_unit_mount_centers(solid):
        assert abs(x) + solid.air_unit_hole_diameter_mm / 2 < frame.top_plate_length_mm / 2
        assert abs(y) + solid.air_unit_hole_diameter_mm / 2 < frame.plate_width_mm / 2

    for x, y in camera_base_mount_centers(solid):
        assert abs(x) + solid.camera_base_hole_diameter_mm / 2 < frame.top_plate_length_mm / 2
        assert abs(y) + solid.camera_base_hole_diameter_mm / 2 < frame.plate_width_mm / 2


def test_camera_bracket_side_spacing_clears_o4_pro_camera_envelope():
    solid = FPVFrameSolidSpec()
    side_center = (
        solid.camera_module_width_mm / 2
        + solid.camera_side_clearance_mm
        + solid.camera_side_plate_thickness_mm / 2
    )
    inner_face = side_center - solid.camera_side_plate_thickness_mm / 2
    assert inner_face - solid.camera_module_width_mm / 2 == pytest.approx(
        solid.camera_side_clearance_mm
    )


def test_camera_base_mount_holes_clear_arm_root_bolts():
    frame = FPVFrameSpec(arm_width_mm=18.0)
    solid = FPVFrameSolidSpec()
    root_holes = [
        point
        for points in arm_root_bolt_centers(frame, solid).values()
        for point in points
    ]
    for x, y in camera_base_mount_centers(solid):
        nearest = min(((x-rx)**2 + (y-ry)**2)**0.5 for rx, ry in root_holes)
        assert nearest > (
            solid.camera_base_hole_diameter_mm + solid.arm_root_hole_diameter_mm
        ) / 2



def test_o4_mount_holes_are_clear_of_both_fc_stack_patterns():
    solid = FPVFrameSolidSpec()
    stack_centers = []
    for spacing in (20.0, 30.5):
        half = spacing / 2
        stack_centers.extend([
            (-half, -half), (-half, half), (half, -half), (half, half)
        ])
    air_holes = air_unit_mount_centers(solid)
    minimum_clearance = min(
        ((ax-sx)**2 + (ay-sy)**2)**0.5
        - (solid.air_unit_hole_diameter_mm + solid.stack_hole_diameter_mm) / 2
        for ax, ay in air_holes
        for sx, sy in stack_centers
    )
    assert minimum_clearance > 0
