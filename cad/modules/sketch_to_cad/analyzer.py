"""Raster silhouette and internal-cutout extraction for Sketch-to-CAD."""
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
    hole_contours_mm: tuple[tuple[tuple[float, float], ...], ...]
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
            "hole_contours_mm": [[list(p) for p in contour] for contour in self.hole_contours_mm],
            "hole_count": len(self.hole_contours_mm),
            "width_mm": self.width_mm,
            "height_mm": self.height_mm,
            "scale_mm_per_px": self.scale_mm_per_px,
            "area_px2": self.area_px2,
            "confidence": self.confidence,
            "warnings": list(self.warnings),
            "units": "mm" if self.scale_mm_per_px is not None else "pixels",
        }


def _to_model_points(contour: np.ndarray, center_x: float, center_y: float,
                     scale: float, simplify_ratio: float) -> tuple[tuple[float, float], ...]:
    perimeter = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, max(0.5, simplify_ratio * perimeter), True)
    return tuple(
        ((float(point[0][0]) - center_x) * scale,
         (center_y - float(point[0][1])) * scale)
        for point in approx
    )


def analyze_sketch_image(image_bytes: bytes, reference_length_mm: float | None = None,
                         threshold: int = 180, simplify_ratio: float = 0.002) -> SketchAnalysis:
    """Trace the largest dark silhouette and its directly enclosed cutouts."""
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
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if not contours or hierarchy is None:
        raise ValueError("No foreground contour found; check contrast and threshold")

    tree = hierarchy[0]
    outer_indices = [i for i, item in enumerate(tree) if item[3] == -1]
    if not outer_indices:
        raise ValueError("No external silhouette found")
    outer_index = max(outer_indices, key=lambda i: cv2.contourArea(contours[i]))
    contour = contours[outer_index]
    area = float(cv2.contourArea(contour))
    if area < width * height * 0.001:
        raise ValueError("Detected outline is too small or image contrast is insufficient")

    x, y, box_w, box_h = cv2.boundingRect(contour)
    longest_px = float(max(box_w, box_h))
    calibrated = reference_length_mm is not None
    scale = reference_length_mm / longest_px if calibrated else 1.0
    center_x, center_y = x + box_w / 2.0, y + box_h / 2.0
    outer_points = _to_model_points(contour, center_x, center_y, scale, simplify_ratio)
    if len(outer_points) < 3:
        raise ValueError("Could not extract a closed contour with at least 3 points")

    hole_contours: list[tuple[tuple[float, float], ...]] = []
    child_index = int(tree[outer_index][2])
    while child_index != -1:
        child = contours[child_index]
        child_area = float(cv2.contourArea(child))
        if child_area >= max(9.0, area * 0.0005):
            points = _to_model_points(child, center_x, center_y, scale, simplify_ratio)
            if len(points) >= 3:
                hole_contours.append(points)
        child_index = int(tree[child_index][0])

    fill_ratio = min(1.0, area / float(box_w * box_h))
    coverage = area / float(width * height)
    confidence = max(0.0, min(1.0, 0.55 + 0.35 * fill_ratio - 0.2 * coverage))
    warnings = [
        "Only the largest external silhouette and its directly enclosed holes are traced.",
        "A single image cannot determine depth, hidden faces, or wall thickness.",
        "Perspective and lens distortion are not corrected.",
        "Small details below the contour-area filter may be omitted.",
    ]
    if not calibrated:
        warnings.append("No known dimension supplied: coordinates remain in pixel units.")
    if coverage > 0.75:
        warnings.append("The silhouette nearly fills the image; check whether the part is cropped.")
    if len(outer_indices) > 1:
        warnings.append("Additional disconnected foreground objects were ignored.")
    return SketchAnalysis(
        width, height, outer_points, tuple(hole_contours),
        box_w * scale if calibrated else None,
        box_h * scale if calibrated,
        scale if calibrated else None, area, round(confidence, 3), tuple(warnings),
    )


def export_analysis_dxf(analysis: SketchAnalysis, path: str) -> str:
    """Write closed DXF polylines; use millimetres only when the image is calibrated."""
    import ezdxf

    if len(analysis.contour_points_mm) < 3:
        raise ValueError("Analysis has no valid closed contour")
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4 if analysis.scale_mm_per_px is not None else 0
    doc.layers.new("SKETCH_OUTLINE", dxfattribs={"color": 7})
    doc.layers.new("SKETCH_HOLES", dxfattribs={"color": 1})
    msp = doc.modelspace()
    msp.add_lwpolyline(list(analysis.contour_points_mm), close=True,
                       dxfattribs={"layer": "SKETCH_OUTLINE"})
    for hole in analysis.hole_contours_mm:
        if len(hole) >= 3:
            msp.add_lwpolyline(list(hole), close=True,
                               dxfattribs={"layer": "SKETCH_HOLES"})
    doc.saveas(path)
    return path


def export_analysis_solid(analysis: SketchAnalysis, path: str, thickness_mm: float,
                          format_name: str = "step") -> str:
    """Extrude a calibrated 2D profile and subtract detected through-cutouts."""
    if thickness_mm <= 0:
        raise ValueError("thickness_mm must be positive")
    if analysis.scale_mm_per_px is None:
        raise ValueError("A reference dimension is required before 3D export")
    fmt = format_name.lower()
    if fmt not in {"step", "stl"}:
        raise ValueError("format_name must be 'step' or 'stl'")
    if len(analysis.contour_points_mm) < 3:
        raise ValueError("Analysis has no valid outer contour")
    from build123d import Polygon, make_face, extrude, export_step, export_stl

    profile = Polygon(*analysis.contour_points_mm, align=None)
    face = make_face(profile)
    solid = extrude(face, amount=thickness_mm, dir=(0, 0, 1))
    if not solid.is_valid:
        raise ValueError("Generated outer solid is not a valid closed CAD body")

    for index, hole_points in enumerate(analysis.hole_contours_mm, start=1):
        if len(hole_points) < 3:
            raise ValueError(f"Detected cutout {index} has fewer than 3 points")
        hole_profile = Polygon(*hole_points, align=None)
        hole_face = make_face(hole_profile)
        cutter = extrude(hole_face, amount=thickness_mm, dir=(0, 0, 1))
        solid = solid - cutter
        if not solid.is_valid:
            raise ValueError(f"Boolean cut for detected hole {index} produced invalid geometry")

    if fmt == "step":
        export_step(solid, path)
    else:
        export_stl(solid, path, tolerance=0.05, angular_tolerance=0.1)
    return path
