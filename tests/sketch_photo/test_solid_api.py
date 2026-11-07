from fastapi.testclient import TestClient

from cad.api.main import app


client = TestClient(app)


def _payload():
    return {
        "thickness_mm": 3,
        "features": [
            {
                "kind": "rectangle", "operation": "add",
                "center_x_mm": 0, "center_y_mm": 0,
                "width_mm": 40, "height_mm": 20,
            },
            {
                "kind": "circle", "operation": "subtract",
                "center_x_mm": 0, "center_y_mm": 0, "radius_mm": 2,
            },
        ],
    }


def test_step_export_returns_step_attachment():
    response = client.post("/cad/sketch/export/step", json=_payload())
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/step")
    assert 'filename="sketch_model.step"' in response.headers["content-disposition"]
    assert len(response.content) > 100


def test_stl_export_returns_stl_attachment():
    response = client.post("/cad/sketch/export/stl", json=_payload())
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("model/stl")
    assert 'filename="sketch_model.stl"' in response.headers["content-disposition"]
    assert len(response.content) > 100


def test_export_rejects_zero_thickness():
    payload = _payload()
    payload["thickness_mm"] = 0
    response = client.post("/cad/sketch/export/step", json=payload)
    assert response.status_code == 422


def test_export_rejects_unsupported_format():
    response = client.post("/cad/sketch/export/dxf", json=_payload())
    assert response.status_code == 400
