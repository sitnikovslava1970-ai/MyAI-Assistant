"""Round-trip quality checks for generated mesh exports."""
import math

import pytest
import trimesh
from build123d import export_stl

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


def test_stl_round_trip_preserves_bounds_and_volume(tmp_path):
    solid = _plate_with_center_hole()
    output = tmp_path / "plate.stl"
    export_stl(solid, str(output), tolerance=0.01, angular_tolerance=0.05)

    mesh = trimesh.load(str(output), force="mesh", process=True)

    assert isinstance(mesh, trimesh.Trimesh)
    assert mesh.is_watertight
    assert mesh.is_volume
    assert mesh.bounds[:, 0].min() == pytest.approx(-20, abs=0.02)
    assert mesh.bounds[:, 0].max() == pytest.approx(20, abs=0.02)
    assert mesh.bounds[:, 1].min() == pytest.approx(-10, abs=0.02)
    assert mesh.bounds[:, 1].max() == pytest.approx(10, abs=0.02)
    assert mesh.bounds[:, 2].min() == pytest.approx(0, abs=0.02)
    assert mesh.bounds[:, 2].max() == pytest.approx(3, abs=0.02)

    expected_volume = (40 * 20 - math.pi * 2**2) * 3
    assert mesh.volume == pytest.approx(expected_volume, rel=0.01)


def test_stl_export_is_not_empty(tmp_path):
    output = tmp_path / "plate.stl"
    export_stl(_plate_with_center_hole(), str(output))
    assert output.exists()
    assert output.stat().st_size > 500
