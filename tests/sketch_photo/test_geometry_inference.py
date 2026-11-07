from io import BytesIO

from PIL import Image, ImageDraw
import pytest

from cad.sketch_photo.feature_detection import detect_sketch_features
from cad.sketch_photo.geometry_inference import infer_profile_proposals


def image_bytes(shape):
    image = Image.new("RGB", (120, 100), "white")
    draw = ImageDraw.Draw(image)
    if shape == "rectangle":
        # Center the synthetic rectangle on the image origin.
        draw.rectangle((24, 24, 95, 75), outline="black", width=3)
    elif shape == "circle":
        draw.ellipse((35, 25, 85, 75), outline="black", width=3)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_rectangle_proposal_is_scaled_to_mm_and_centered():
    observation = detect_sketch_features(image_bytes("rectangle"))
    proposals = infer_profile_proposals(observation, scale_px_per_mm=4)
    rectangle = next(item for item in proposals if item.kind == "rectangle")

    assert rectangle.center_x_mm == pytest.approx(0, abs=0.5)
    assert rectangle.center_y_mm == pytest.approx(0, abs=0.5)
    assert rectangle.width_mm == pytest.approx(18, abs=1)
    assert rectangle.height_mm == pytest.approx(13, abs=1)
    assert rectangle.radius_mm is None


def test_circle_proposal_is_scaled_and_uses_cartesian_y_axis():
    observation = detect_sketch_features(image_bytes("circle"))
    proposals = infer_profile_proposals(observation, scale_px_per_mm=5)
    circle = next(item for item in proposals if item.kind == "circle")

    assert circle.center_x_mm == pytest.approx(0, abs=0.5)
    assert circle.center_y_mm == pytest.approx(0, abs=0.5)
    assert circle.radius_mm == pytest.approx(5, abs=0.6)
    assert circle.width_mm == pytest.approx(10, abs=1.2)
    assert circle.height_mm == circle.width_mm


def test_profile_inference_rejects_missing_or_invalid_scale():
    observation = detect_sketch_features(image_bytes("rectangle"))
    with pytest.raises(ValueError, match="scale_px_per_mm"):
        infer_profile_proposals(observation, 0)


def test_empty_observation_produces_no_profile_proposals():
    observation = detect_sketch_features(image_bytes("empty"))
    assert infer_profile_proposals(observation, 4) == ()
