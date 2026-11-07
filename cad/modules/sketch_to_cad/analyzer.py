"""Raster silhouette extraction for the first Sketch-to-CAD stage."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import cv2
import numpy as np


@dataclass(frozen=True)
class SketchAnalysis:
    image_width_px: int
    image_height_px: int
    contour_points_mm: tuple[tuple[float, float], ...]
    width_mm: float | None
    height_mm: float | None
    scale_mm_per_px: float | None
    area_px2: float
    confidence: float
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "image_width_px": self.image_width_px,
            "image_height_px": self.image_height_px,
            "contour_points_mm": [list(p) for p in self.contour_points_mm],
            "width_mm": self.width_mm, "height_mm": self.height_mm,
            "scale_mm_per_px": self.scale_mm_per_px, "area_px2": self.area_px2,
            "confidence": self.confidence, "warnings": list(self.warnings),
            "units": "mm" if self.scale_mm_per_px is not None else "pixels",
        }


def analyze_sketch_image(image_bytes: bytes, reference_length_mm: float | None = None,
                         threshold: int = 180, simplify_ratio: float = 0.002) -> SketchAnalysis:
    """Trace the largest dark silhouette; calibrate its longer side if a dimension is supplied."""
    if not image_bytes:
        raise ValueError("Image file is empty")
    if reference_length_mm is not None and reference_length_mm <= 0:
        raise ValueError("reference_length_mm must be positive")
    if not 0 <= threshold <= 255:
        raise ValueError("threshold must be between 0 and 255")
    if not 0 < simplify_ratio <= 0.05:
        raise ValueError("simplify_ratio must be in the range (0, 0.05]")
    image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Unsupported or corrupted image; use PNG or JPEG")
    height, width = image.shape[:2]
    if width < 32 or height < 32:
        raise ValueError("Image is too small; minimum size is 32 x 32 pixels")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    _, mask = cv2.threshold(blurred, threshold, 255, cv2.THRESH_BINARY_INV)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError("No foreground contour found; check contrast and threshold")
    contour = max(contours, key=cv2.contourArea)
    area = float(cv2.contourArea(contour))
    if area < width * height * 0.001:
        raise ValueError("Detected outline is too small or image contrast is insufficient")
    perimeter = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, max(0.5, simplify_ratio * perimeter), True)
    points_px = [(float(p[0][0]), float(p[0][1])) for p in approx]
    if len(points_px) < 3:
        raise ValueError("Could not extract a closed contour with at least 3 points")
    x, y, box_w, box_h = cv2.boundingRect(contour)
    longest_px = float(max(box_w, box_h))
    calibrated = reference_length_mm is not None
    scale = reference_length_mm / longest_px if calibrated else 1.0
    cx, cy = x + box_w / 2.0, y + box_h / 2.0
    points = tuple(((px - cx) * scale, (cy - py) * scale) for px, py in points_px)
    fill_ratio = min(1.0, area / float(box_w * box_h))
    coverage = area / float(width * height)
    confidence = max(0.0, min(1.0, 0.55 + 0.35 * fill_ratio - 0.2 * coverage))
    warnings = [
        "Only the largest external silhouette is traced; internal holes are not detected.",
        "A single image cannot determine depth, hidden faces, or wall thickness.",
        "Perspective and lens distortion are not corrected.",
    ]
    if not calibrated:
        warnings.append("No known dimension supplied: coordinates remain in pixel units.")
    if coverage > 0.75:
        warnings.append("The silhouette nearly fills the image; check whether the part is cropped.")
    return SketchAnalysis(width, height, points,
        box_w * scale if calibrated else None,
        box_h * scale if calibrated,
        scale if calibrated else None, area, round(confidence, 3), tuple(warnings))


def export_analysis_dxf(analysis: SketchAnalysis, path: str) -> str:
    """Write the traced closed contour as a millimetre DXF polyline."""
    import ezdxf
    if len(analysis.contour_points_mm) < 3:
        raise ValueError("Analysis has no valid closed contour")
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4
    doc.layers.new("SKETCH_OUTLINE", dxfattribs={"color": 7})
    doc.modelspace().add_lwpolyline(list(analysis.contour_points_mm), close=True,
                                    dxfattribs={"layer": "SKETCH_OUTLINE"})
    doc.saveas(path)
    return path



def export_analysis_solid(analysis: SketchAnalysis, path: str, thickness_mm: float,
                          format_name: str = "step") -> str:
    """Extrude a calibrated closed 2D outline into a simple STEP or STL solid.

    Thickness is an explicit user-supplied engineering dimension; it is never
    guessed from the photograph. Internal cut-outs are not included in stage 1.
    """
    if thickness_mm <= 0:
        raise ValueError("thickness_mm must be positive")
    if analysis.scale_mm_per_px is None:
        raise ValueError("A reference dimension is required before 3D export")
    fmt = format_name.lower()
    if fmt not in {"step", "stl"}:
        raise ValueError("format_name must be 'step' or 'stl'")
    from build123d import Polygon, make_face, extrude, export_step, export_stl

    profile = Polygon(*analysis.contour_points_mm, align=None)
    face = make_face(profile)
    solid = extrude(face, amount=thickness_mm)
    if not solid.is_valid:
        raise ValueError("Generated solid is not a valid closed CAD body")
    if fmt == "step":
        export_step(solid, path)
    else:
        export_stl(solid, path, tolerance=0.05, angular_tolerance=0.1)
    return path
