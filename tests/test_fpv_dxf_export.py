import ezdxf

from cad.export_fpv_dxf import export_dxf_package


def test_preliminary_dxf_package_exports_flat_carbon_parts(tmp_path):
    manifest = export_dxf_package(tmp_path)
    assert len(manifest["generated_parts"]) == 9

    readme = (tmp_path / "README_DXF_PRELIMINARY.md").read_text(encoding="utf-8")
    assert "nine exported parts" in readme
    assert "Camera side panels are exported" in readme

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
