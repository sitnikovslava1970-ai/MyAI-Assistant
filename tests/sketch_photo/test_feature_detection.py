from io import BytesIO
from PIL import Image, ImageDraw
import pytest

from cad.sketch_photo.feature_detection import detect_sketch_features
from cad.sketch_photo.scale_calibration import pixels_per_mm, pixels_to_mm


def make_test_sketch():
    image = Image.new("RGB", (120, 100), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 20, 90, 70), outline="black", width=3)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def make_circle_sketch():
    image = Image.new("RGB", (100, 100), "white")
    ImageDraw.Draw(image).ellipse((25, 25, 75, 75), outline="black", width=3)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_detects_edges_and_bounds_in_synthetic_sketch():
    result = detect_sketch_features(make_test_sketch())
    assert result.image_width_px == 120
    assert result.image_height_px == 100
    assert result.bounds is not None
    assert result.edge_pixel_count > 0
    assert result.bounds.x_min_px <= 20
    assert result.bounds.x_max_px >= 90


def test_extracts_connected_edge_regions_with_image_coordinates():
    result = detect_sketch_features(make_test_sketch())
    assert result.regions
    region = result.regions[0]
    assert region.bounds.x_min_px <= 20
    assert region.bounds.x_max_px >= 90
    assert region.edge_pixel_count >= 6
    assert region.center_x_px == pytest.approx(
        (region.bounds.x_min_px + region.bounds.x_max_px) / 2
    )
    assert region.shape_hint in {"elongated", "compact_candidate", "irregular"}


def test_fits_circle_candidate_from_synthetic_circle():
    result = detect_sketch_features(make_circle_sketch())
    assert result.circle_candidates
    circle = result.circle_candidates[0]
    assert circle.center_x_px == pytest.approx(50, abs=2)
    assert circle.center_y_px == pytest.approx(50, abs=2)
    assert circle.radius_px == pytest.approx(25, abs=2)
    assert circle.relative_radial_error < 0.045
    assert circle.angular_coverage >= 0.65
    assert circle.confidence in {"medium", "high"}


def test_rectangle_is_not_reported_as_a_circle_candidate():
    result = detect_sketch_features(make_test_sketch())
    assert result.circle_candidates == ()


def test_empty_image_returns_no_regions_or_circles():
    image = Image.new("RGB", (64, 64), "white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    result = detect_sketch_features(buffer.getvalue())
    assert result.bounds is None
    assert result.regions == ()
    assert result.circle_candidates == ()


def test_rejects_invalid_image_payload():
    with pytest.raises(ValueError, match="Unsupported or corrupted"):
        detect_sketch_features(b"not an image")


def test_scale_calibration_uses_confirmed_reference_length():
    scale = pixels_per_mm(100, 25)
    assert scale == pytest.approx(4)
    assert pixels_to_mm(40, scale) == pytest.approx(10)


def test_scale_calibration_rejects_zero_reference():
    with pytest.raises(ValueError):
        pixels_per_mm(100, 0)


def test_sketch_analysis_api_returns_region_proposals():
    from fastapi.testclient import TestClient
    from cad.api.main import app

    response = TestClient(app).post(
        "/cad/sketch/analyze",
        files={"file": ("plate.png", make_test_sketch(), "image/png")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["regions"]
    assert payload["regions"][0]["edge_pixel_count"] >= 6
    assert payload["circle_candidates"] == []


def test_sketch_analysis_api_rejects_invalid_image():
    from fastapi.testclient import TestClient
    from cad.api.main import app

    response = TestClient(app).post(
        "/cad/sketch/analyze",
        files={"file": ("broken.png", b"not an image", "image/png")},
    )
    assert response.status_code == 422
