import pytest

from cad.sketch_photo.scale_calibration import pixels_per_mm, pixels_to_mm


def test_calibrates_and_converts_pixel_distance():
    scale = pixels_per_mm(120, 30)
    assert scale == 4
    assert pixels_to_mm(80, scale) == 20


@pytest.mark.parametrize("pixel_length,real_length", [
    (0, 10), (-1, 10), (10, 0), (10, -1),
    (float("nan"), 10), (10, float("inf")),
])
def test_rejects_non_positive_or_non_finite_reference_measurements(pixel_length, real_length):
    with pytest.raises(ValueError):
        pixels_per_mm(pixel_length, real_length)


@pytest.mark.parametrize("pixel_distance,scale", [
    (-1, 2), (10, 0), (10, -1), (float("inf"), 2), (10, float("nan")),
])
def test_rejects_invalid_pixel_to_mm_conversion_inputs(pixel_distance, scale):
    with pytest.raises(ValueError):
        pixels_to_mm(pixel_distance, scale)
