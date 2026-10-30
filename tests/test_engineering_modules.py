import pytest
from cad.modules.assembly import AssemblyItem, bill_of_materials
from cad.modules.dimensions import rectangular_hole_pattern
from cad.modules.fpv_frame import FPVFrameSpec
from cad.modules.propeller import PropellerSpec


def test_classic_x_frame_motor_centers_match_diagonal_wheelbase():
    spec = FPVFrameSpec()
    centers = spec.motor_centers()
    front_left = centers["front_left"]
    rear_right = centers["rear_right"]
    diagonal = ((front_left[0] - rear_right[0]) ** 2 +
                (front_left[1] - rear_right[1]) ** 2) ** 0.5
    assert diagonal == pytest.approx(315.0)
    assert len(spec.motor_holes()["front_left"]) == 4


def test_propeller_default_is_seven_inch_with_five_mm_bore():
    spec = PropellerSpec()
    spec.validate()
    assert spec.diameter_mm == pytest.approx(177.8)
    assert spec.bore_diameter_mm == 5
    assert len(spec.blade_outline()) == 50


def test_rectangular_hole_pattern_has_four_holes():
    pattern = rectangular_hole_pattern(100, 60, 10, 5)
    assert len(pattern.centers) == 4
    assert pattern.diameter_mm == 5


def test_bom_rejects_duplicate_part_ids():
    items = [AssemblyItem("ARM", "Arm", 4), AssemblyItem("ARM", "Spare arm", 1)]
    with pytest.raises(ValueError):
        bill_of_materials(items)
