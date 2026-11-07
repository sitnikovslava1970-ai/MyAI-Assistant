import cv2
import ezdxf
import numpy as np
import pytest

from cad.modules.sketch_to_cad import analyze_sketch_image, export_analysis_dxf, export_analysis_solid


def encode(image):
    ok, encoded = cv2.imencode(".png", image)
    assert ok
    return encoded.tobytes()


def rectangle_image():
    image = np.full((240, 320, 3), 255, dtype=np.uint8)
    cv2.rectangle(image, (60, 50), (260, 190), (0, 0, 0), thickness=-1)
    return encode(image)


def plate_with_hole_image():
    image = np.full((240, 320, 3), 255, dtype=np.uint8)
    cv2.rectangle(image, (60, 50), (260, 190), (0, 0, 0), thickness=-1)
    cv2.circle(image, (160, 120), 24, (255, 255, 255), thickness=-1)
    return encode(image)


def test_detects_silhouette_and_calibrates_long_side():
    result = analyze_sketch_image(rectangle_image(), reference_length_mm=100)
    assert len(result.contour_points_mm) >= 4
    assert result.width_mm == pytest.approx(100, abs=1.5)
    assert result.height_mm == pytest.approx(70, abs=1.5)
    assert result.scale_mm_per_px > 0
    assert result.hole_contours_mm == ()
    assert 0 <= result.confidence <= 1


def test_detects_internal_hole_and_reports_it():
    result = analyze_sketch_image(plate_with_hole_image(), reference_length_mm=100)
    assert len(result.hole_contours_mm) == 1
    assert len(result.hole_contours_mm[0]) >= 8
    assert result.to_dict()["hole_count"] == 1
    assert result.to_dict()["units"] == "mm"


def test_dxf_contains_outer_contour_and_hole(tmp_path):
    result = analyze_sketch_image(plate_with_hole_image(), reference_length_mm=100)
    path = tmp_path / "plate.dxf"
    export_analysis_dxf(result, str(path))
    doc = ezdxf.readfile(path)
    entities = list(doc.modelspace().query("LWPOLYLINE"))
    assert len(entities) == 2
    assert {entity.dxf.layer for entity in entities} == {"SKETCH_OUTLINE", "SKETCH_HOLES"}
    assert all(entity.closed for entity in entities)



def test_uncalibrated_dxf_is_marked_unitless(tmp_path):
    result = analyze_sketch_image(rectangle_image())
    path = tmp_path / "pixel_profile.dxf"
    export_analysis_dxf(result, str(path))
    doc = ezdxf.readfile(path)
    assert doc.header["$INSUNITS"] == 0

def test_solid_export_refuses_to_drop_detected_holes(tmp_path):
    result = analyze_sketch_image(plate_with_hole_image(), reference_length_mm=100)
    with pytest.raises(ValueError, match="internal holes is not supported"):
        export_analysis_solid(result, str(tmp_path / "plate.step"), 4, "step")


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


def test_rejects_non_positive_thickness():
    result = analyze_sketch_image(rectangle_image(), reference_length_mm=100)
    with pytest.raises(ValueError, match="thickness_mm must be positive"):
        export_analysis_solid(result, "unused.step", 0, "step")
