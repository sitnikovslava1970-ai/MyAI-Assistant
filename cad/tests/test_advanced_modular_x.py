from cad.modules.advanced_modular_x import AdvancedModularXSpec


def test_deadcat_motor_layout_matches_target_diagonal():
    spec = AdvancedModularXSpec()
    spec.validate()
    assert abs(spec.diagonal_wheelbase() - 327.0) <= 1.0


def test_seven_inch_propellers_have_minimum_clearance():
    spec = AdvancedModularXSpec()
    assert min(spec.prop_clearances().values()) >= spec.min_prop_gap_mm


def test_each_arm_has_four_root_fastener_holes():
    holes = AdvancedModularXSpec().arm_root_holes()
    assert set(holes) == {"front_left", "front_right", "rear_left", "rear_right"}
    assert all(len(points) == 4 for points in holes.values())


def test_root_holes_remain_inside_bottom_plate():
    spec = AdvancedModularXSpec()
    for points in spec.arm_root_holes().values():
        for x, y in points:
            assert abs(x) + spec.root_hole_diameter_mm / 2 < spec.plate_length_mm / 2
            assert abs(y) + spec.root_hole_diameter_mm / 2 < spec.plate_width_mm / 2


def test_parametric_assembly_builds_all_separate_parts_with_positive_volume():
    from cad.modules.advanced_modular_x import build_advanced_modular_x_parts

    parts = build_advanced_modular_x_parts()
    expected = {
        "PLATE_BOTTOM_3MM", "PLATE_TOP_2MM",
        "ARM_FRONT_LEFT", "ARM_FRONT_RIGHT", "ARM_REAR_LEFT", "ARM_REAR_RIGHT",
        "STANDOFF_1", "STANDOFF_2", "STANDOFF_3", "STANDOFF_4",
    }
    assert set(parts) == expected
    assert all(part.volume > 0 for part in parts.values())
