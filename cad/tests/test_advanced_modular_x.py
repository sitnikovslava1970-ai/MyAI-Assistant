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

def test_step_export_round_trip_preserves_all_ten_valid_solids(tmp_path):
    from build123d import import_step
    from cad.modules.advanced_modular_x import export_advanced_modular_x_step

    output = export_advanced_modular_x_step(tmp_path / "round_trip.step")
    imported = import_step(str(output))
    solids = imported.solids()

    assert len(solids) == 10
    assert all(solid.is_valid for solid in solids)
    assert all(solid.volume > 0 for solid in solids)

def test_lower_plate_has_arm_root_and_standoff_holes_but_no_stack_pattern():
    from math import pi
    from cad.modules.advanced_modular_x import build_advanced_modular_x_parts

    spec = AdvancedModularXSpec()
    lower = build_advanced_modular_x_parts(spec)["PLATE_BOTTOM_3MM"]
    removed_volume = (
        16 * pi * (spec.root_hole_diameter_mm / 2) ** 2
        + 4 * pi * (spec.stack_hole_diameter_mm / 2) ** 2
    ) * spec.bottom_plate_thickness_mm
    expected_volume = (
        spec.plate_length_mm * spec.plate_width_mm * spec.bottom_plate_thickness_mm
        - removed_volume
    )
    assert abs(lower.volume - expected_volume) < 0.1
