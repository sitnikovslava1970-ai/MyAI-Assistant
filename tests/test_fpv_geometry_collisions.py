"""Solid-level collision regression tests for the FPV assembly."""
from itertools import combinations

from cad.modules.fpv_frame_solid import build_fpv_frame_parts


def test_assembly_components_have_no_unintended_volume_intersections():
    parts = build_fpv_frame_parts()
    collisions = []
    for name_a, name_b in combinations(parts, 2):
        overlap = parts[name_a].intersect(parts[name_b])
        if overlap is None:
            continue
        volume = overlap.volume
        if volume > 1e-5:
            collisions.append((name_a, name_b, volume))

    assert not collisions, "Unintended solid intersections: " + repr(collisions)
