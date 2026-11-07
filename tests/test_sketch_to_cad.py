import cv2
import numpy as np
import pytest
from cad.modules.sketch_to_cad import analyze_sketch_image


def rectangle_image():
    image = np.full((240, 320, 3), 255, dtype=np.uint8)
    cv2.rectangle(image, (60, 50), (260, 190), (0, 0, 0), thickness=-1)
    ok, encoded = cv2.imencode(".png", image)
    assert ok
    return encoded.tobytes()


def test_detects_silhouette_and_calibrates_long_side():
    result = analyze_sketch_image(rectangle_image(), reference_length_mm=100)
    assert len(result.contour_points_mm) >= 4
    assert result.width_mm == pytest.approx(100, abs=1.5)
    assert result.height_mm == pytest.approx(70, abs=1.5)
    assert result.scale_mm_per_px > 0
    assert 0 <= result.confidence <= 1


def test_without_reference_keeps_pixel_units():
    result = analyze_sketch_image(rectangle_image())
    assert result.width_mm is None
    assert result.height_mm is None
    assert result.scale_mm_per_px is None
    assert result.to_dict()["units"] == "pixels"


def test_rejects_invalid_image():
    with pytest.raises(ValueError, match="Unsupported or corrupted"):
        analyze_sketch_image(b"not an image")


def test_rejects_non_positive_reference_length():
    with pytest.raises(ValueError, match="must be positive"):
        analyze_sketch_image(rectangle_image(), reference_length_mm=0)
