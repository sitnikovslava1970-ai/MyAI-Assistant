"""Dimensional validation tests for the Advanced Modular X R01 concept."""

from dataclasses import replace

import pytest

from cad.modules.advanced_modular_x import AdvancedModularXSpec


def test_step_ready_parts_build_as_valid_solids():
    from cad.modules.advanced_modular_x import build_advanced_modular_x_parts

    parts = build_advanced_modular_x_parts()
    assert len(parts) == 10
    assert "PLATE_BOTTOM_3MM" in parts
    assert "PLATE_TOP_2MM" in parts
    assert sum(name.startswith("ARM_") for name in parts) == 4
    assert sum(name.startswith("STANDOFF_") for name in parts) == 4
    assert all(part.is_valid for part in parts.values())
    assert all(part.volume > 0 for part in parts.values())


def test_advanced_modular_x_step_export_creates_nonempty_file(tmp_path):
    from cad.modules.advanced_modular_x import export_advanced_modular_x_step

    output = export_advanced_modular_x_step(tmp_path / "advanced_modular_x.step")
    assert output.exists()
    assert output.stat().st_size > 0


def test_default_spec_matches_327_mm_diagonal_and_has_prop_clearance():
    spec = AdvancedModularXSpec()
    spec.validate()

    assert spec.diagonal_wheelbase() == pytest.approx(327.0, abs=1.0)
    assert min(spec.prop_clearances().values()) >= spec.min_prop_gap_mm


def test_default_arm_root_bolt_pattern_is_four_holes_per_arm_inside_plate():
    spec = AdvancedModularXSpec()
    spec.validate()

    holes = spec.arm_root_holes()
    assert set(holes) == {"front_left", "front_right", "rear_left", "rear_right"}
    assert all(len(points) == 4 for points in holes.values())
    for points in holes.values():
        for x, y in points:
            edge_distance = min(
                spec.plate_length_mm / 2 - abs(x),
                spec.plate_width_mm / 2 - abs(y),
            )
            assert edge_distance >= spec.root_hole_diameter_mm


def test_rear_propeller_pair_has_18_2_mm_clearance():
    spec = AdvancedModularXSpec()
    spec.validate()

    clearances = spec.prop_clearances()
    assert clearances["rear_left__rear_right"] == pytest.approx(18.2, abs=0.01)
    assert min(clearances.values()) == pytest.approx(18.2, abs=0.01)


def test_both_stack_mounting_patterns_are_present_and_fit_plate():
    spec = AdvancedModularXSpec()
    spec.validate()

    centers = spec.stack_hole_centers()
    assert len(centers) == 8
    assert len(set(centers)) == 8
    for x, y in centers:
        assert abs(x) + spec.stack_hole_diameter_mm / 2 < spec.plate_length_mm / 2
        assert abs(y) + spec.stack_hole_diameter_mm / 2 < spec.plate_width_mm / 2


def test_arm_root_holes_are_inside_arm_width():
    spec = AdvancedModularXSpec()
    roots = spec.arm_root_centers()
    motors = spec.motor_centers()

    for name, points in spec.arm_root_holes().items():
        mx, my = motors[name]
        rx, ry = roots[name]
        length = (mx * mx + my * my) ** 0.5
        nx, ny = -my / length, mx / length
        for x, y in points:
            transverse_offset = abs((x - rx) * nx + (y - ry) * ny)
            assert transverse_offset + spec.root_hole_diameter_mm / 2 < spec.arm_width_mm / 2


def test_default_motor_layout_is_mirrored():
    centers = AdvancedModularXSpec().motor_centers()

    assert centers["front_left"] == (-centers["front_right"][0], centers["front_right"][1])
    assert centers["rear_left"] == (-centers["rear_right"][0], centers["rear_right"][1])


@pytest.mark.parametrize(
    "changes",
    [
        {"min_prop_gap_mm": 0},
        {"root_hole_row_spacing_mm": 0},
        {"root_hole_row_spacing_mm": -2},
        {"root_hole_station_1_mm": 0},
        {"root_hole_station_2_mm": -40},
        {"root_hole_station_2_mm": -31},
    ],
)
def test_invalid_arm_root_or_clearance_parameters_are_rejected(changes):
    spec = replace(AdvancedModularXSpec(), **changes)

    with pytest.raises(ValueError):
        spec.validate()


def test_propeller_clearance_target_cannot_exceed_actual_clearance():
    spec = replace(AdvancedModularXSpec(), min_prop_gap_mm=60.0)

    with pytest.raises(ValueError, match="propeller envelopes"):
        spec.validate()
