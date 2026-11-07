"""STEP round-trip quality checks for generated CAD solids."""
import math

import pytest
from build123d import export_step, import_step

from cad.sketch_photo.profile_builder import ConfirmedProfileFeature
from cad.sketch_photo.solid_builder import build_extruded_solid


def _plate_with_center_hole():
    return build_extruded_solid(
        (
            ConfirmedProfileFeature(
                kind="rectangle",
                operation="add",
                center_x_mm=0,
                center_y_mm=0,
                width_mm=40,
                height_mm=20,
            ),
            ConfirmedProfileFeature(
                kind="circle",
                operation="subtract",
                center_x_mm=0,
                center_y_mm=0,
                radius_mm=2,
            ),
        ),
        thickness_mm=3,
    )


def test_step_round_trip_preserves_solid_and_volume(tmp_path):
    solid = _plate_with_center_hole()
    output = tmp_path / "plate.step"

    export_step(solid, str(output))
    assert output.exists()
    assert output.stat().st_size > 500

    restored = import_step(str(output))
    solids = restored.solids()

    assert len(solids) == 1
    assert restored.is_valid
    assert restored.volume == pytest.approx(
        (40 * 20 - math.pi * 2**2) * 3,
        rel=1e-5,
    )

    bounds = restored.bounding_box()
    assert bounds.size.X == pytest.approx(40, abs=0.01)
    assert bounds.size.Y == pytest.approx(20, abs=0.01)
    assert bounds.size.Z == pytest.approx(3, abs=0.01)
