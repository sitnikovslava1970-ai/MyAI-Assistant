from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from cad.api.main import app


client = TestClient(app)


def _rectangle_image():
    image = Image.new("RGB", (120, 100), "white")
    ImageDraw.Draw(image).rectangle((24, 24, 95, 75), outline="black", width=3)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_propose_profile_api_uses_user_reference_and_requires_confirmation():
    response = client.post(
        "/cad/sketch/propose-profile",
        data={
            "reference_pixel_length": "100",
            "reference_length_mm": "20",
            "source_kind": "sketch",
        },
        files={"file": ("plate.png", _rectangle_image(), "image/png")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["units"] == "mm"
    assert payload["scale_px_per_mm"] == 5
    assert payload["requires_user_confirmation"] is True
    assert payload["automatic_geometry_approval"] is False
    assert any(item["kind"] == "rectangle" for item in payload["profile_proposals"])


def test_propose_profile_api_rejects_missing_reference_length():
    response = client.post(
        "/cad/sketch/propose-profile",
        data={
            "reference_pixel_length": "0",
            "reference_length_mm": "20",
        },
        files={"file": ("plate.png", _rectangle_image(), "image/png")},
    )
    assert response.status_code == 422


def test_propose_profile_api_rejects_unknown_source_kind():
    response = client.post(
        "/cad/sketch/propose-profile",
        data={
            "reference_pixel_length": "100",
            "reference_length_mm": "20",
            "source_kind": "scan",
        },
        files={"file": ("plate.png", _rectangle_image(), "image/png")},
    )
    assert response.status_code == 422
