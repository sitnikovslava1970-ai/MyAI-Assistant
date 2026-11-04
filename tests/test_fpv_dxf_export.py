import ezdxf

from cad.export_fpv_dxf import export_dxf_package


def test_preliminary_dxf_package_exports_flat_carbon_parts(tmp_path):
    manifest = export_dxf_package(tmp_path)
    assert len(manifest["generated_parts"]) == 7

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
