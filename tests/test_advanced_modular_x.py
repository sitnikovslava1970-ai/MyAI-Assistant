"""Dimensional validation tests for the Advanced Modular X R01 concept."""

from dataclasses import replace
import math

import pytest

from cad.modules.advanced_modular_x import AdvancedModularXSpec


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
