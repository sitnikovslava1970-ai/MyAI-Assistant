import ezdxf
import pytest

from cad.export_fpv_dxf import export_dxf_package, _validate_dxf_cut_geometry


def test_preliminary_dxf_package_exports_flat_carbon_parts(tmp_path, capsys):
    manifest = export_dxf_package(tmp_path)
    captured = capsys.readouterr()
    assert "WARNING, exporting non-planar shape to 2D format." not in captured.out
    assert len(manifest["generated_parts"]) == 9

    readme = (tmp_path / "README_DXF_PRELIMINARY.md").read_text(encoding="utf-8")
    assert "nine exported parts" in readme
    assert "Camera side panels are exported" in readme
    assert not readme.endswith("\\n")

    for item in manifest["generated_parts"]:
        path = tmp_path / item["file"]
        assert path.exists()
        doc = ezdxf.readfile(path)
        assert doc.header["$INSUNITS"] == ezdxf.units.MM
        entities = list(doc.modelspace())
        assert any(entity.dxf.layer == "OUTLINE" for entity in entities)
        assert any(entity.dxf.layer == "HOLES" for entity in entities)
        assert any(entity.dxf.layer == "NOTES" for entity in entities)
        assert item["outer_wire_closed"]
        if item["part_id"].startswith("CAMERA_SIDE_"):
            closed_profiles = [e for e in entities if e.dxftype() == "LWPOLYLINE" and e.closed]
            assert len(closed_profiles) == 3  # one outline and two camera adjustment slots


def test_dxf_cut_geometry_rejects_duplicate_entities():
    doc = ezdxf.new("R2010")
    doc.layers.new("OUTLINE")
    doc.layers.new("HOLES")
    msp = doc.modelspace()
    points = [(0, 0), (10, 0), (10, 10), (0, 10)]
    for start, end in zip(points, points[1:] + points[:1]):
        msp.add_line(start, end, dxfattribs={"layer": "OUTLINE"})
    msp.add_circle((5, 5), 1, dxfattribs={"layer": "HOLES"})
    msp.add_circle((5, 5), 1, dxfattribs={"layer": "HOLES"})
    with pytest.raises(RuntimeError, match="Duplicate DXF cutting entity"):
        _validate_dxf_cut_geometry(doc, "TEST_PART")
