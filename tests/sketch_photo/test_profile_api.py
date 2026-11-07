from fastapi.testclient import TestClient

from cad.api.main import app


client = TestClient(app)


def test_build_profile_api_returns_planar_profile_metadata():
    response = client.post(
        "/cad/sketch/build-profile",
        json={
            "features": [
                {
                    "kind": "rectangle", "operation": "add",
                    "center_x_mm": 0, "center_y_mm": 0,
                    "width_mm": 40, "height_mm": 20,
                },
                {
                    "kind": "circle", "operation": "subtract",
                    "center_x_mm": 0, "center_y_mm": 0,
                    "radius_mm": 2,
                },
            ]
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "profile_built"
    assert payload["units"] == "mm"
    assert payload["area_mm2"] > 780
    assert payload["face_count"] == 1
    assert payload["is_3d_solid"] is False


def test_build_profile_api_rejects_subtractive_first_feature():
    response = client.post(
        "/cad/sketch/build-profile",
        json={
            "features": [
                {
                    "kind": "circle", "operation": "subtract",
                    "center_x_mm": 0, "center_y_mm": 0, "radius_mm": 2,
                }
            ]
        },
    )
    assert response.status_code == 422
