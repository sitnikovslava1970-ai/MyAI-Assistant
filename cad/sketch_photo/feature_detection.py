"""First-pass raster feature detection; returns observations, not a CAD solid."""
import numpy as np
from scipy import ndimage

from cad.sketch_photo.image_preprocess import edge_map, load_grayscale_image
from cad.sketch_photo.schemas import (
    CircleCandidate, FeatureRegion, ImageBounds, RectangleCandidate,
    SketchObservation,
)

MIN_REGION_PIXELS = 6
MAX_REPORTED_REGIONS = 100
MIN_CIRCLE_PIXELS = 24
MIN_CIRCLE_RADIUS_PX = 5.0
MAX_CIRCLE_RELATIVE_ERROR = 0.045
MIN_CIRCLE_ANGULAR_COVERAGE = 0.65
MIN_RECTANGLE_SIDE_PX = 10
MIN_RECTANGLE_SIDE_COVERAGE = 0.65
RECTANGLE_EDGE_TOLERANCE_PX = 2


def _label_edges(edges):
    edge_array = np.asarray(edges, dtype=np.uint8)
    return ndimage.label(edge_array, structure=np.ones((3, 3), dtype=np.uint8))


def _connected_edge_regions(edges) -> tuple[FeatureRegion, ...]:
    """Group 8-connected edge pixels into image-space region proposals."""
    labels, label_count = _label_edges(edges)
    if label_count == 0:
        return ()

    sizes = np.bincount(labels.ravel(), minlength=label_count + 1)
    sizes[0] = 0
    slices = ndimage.find_objects(labels)
    candidates = [
        (int(sizes[label_id]), label_id, region_slice)
        for label_id, region_slice in enumerate(slices, start=1)
        if region_slice is not None and sizes[label_id] >= MIN_REGION_PIXELS
    ]
    candidates.sort(key=lambda item: (-item[0], item[1]))

    regions = []
    for pixel_count, _label_id, region_slice in candidates[:MAX_REPORTED_REGIONS]:
        y_slice, x_slice = region_slice
        x0, x1 = x_slice.start, x_slice.stop
        y0, y1 = y_slice.start, y_slice.stop
        width, height = x1 - x0, y1 - y0
        aspect_ratio = max(width, height) / max(1, min(width, height))
        density = pixel_count / max(1, width * height)
        if aspect_ratio >= 3.0:
            hint = "elongated"
        elif aspect_ratio <= 1.35:
            hint = "compact_candidate"
        else:
            hint = "irregular"
        regions.append(FeatureRegion(
            bounds=ImageBounds(x0, y0, x1 - 1, y1 - 1),
            edge_pixel_count=pixel_count,
            center_x_px=(x0 + x1 - 1) / 2,
            center_y_px=(y0 + y1 - 1) / 2,
            aspect_ratio=round(float(aspect_ratio), 4),
            pixel_density=round(float(density), 4),
            shape_hint=hint,
        ))
    return tuple(regions)


def _fit_circle_candidates(edges) -> tuple[CircleCandidate, ...]:
    """Fit circles conservatively; residual and angular coverage reject poor fits."""
    labels, label_count = _label_edges(edges)
    if label_count == 0:
        return ()

    candidates = []
    for label_id, region_slice in enumerate(ndimage.find_objects(labels), start=1):
        if region_slice is None:
            continue
        component = labels[region_slice] == label_id
        local_y, local_x = np.nonzero(component)
        if len(local_x) < MIN_CIRCLE_PIXELS:
            continue
        y0, x0 = region_slice[0].start, region_slice[1].start
        x = local_x.astype(float) + x0
        y = local_y.astype(float) + y0
        width, height = float(np.ptp(x) + 1), float(np.ptp(y) + 1)
        if max(width, height) / max(1.0, min(width, height)) > 1.25:
            continue

        matrix = np.column_stack((x, y, np.ones_like(x)))
        target = -(x * x + y * y)
        try:
            a, b, c = np.linalg.lstsq(matrix, target, rcond=None)[0]
        except np.linalg.LinAlgError:
            continue
        center_x, center_y = -a / 2.0, -b / 2.0
        radius_sq = center_x * center_x + center_y * center_y - c
        if not np.isfinite(radius_sq) or radius_sq <= 0:
            continue
        radius = float(np.sqrt(radius_sq))
        if radius < MIN_CIRCLE_RADIUS_PX:
            continue

        residuals = np.hypot(x - center_x, y - center_y) - radius
        rms_error = float(np.sqrt(np.mean(residuals * residuals)))
        relative_error = rms_error / radius
        angles = np.mod(np.arctan2(y - center_y, x - center_x), 2 * np.pi)
        occupied_bins = len(np.unique(np.floor(angles / (2 * np.pi) * 36).astype(int)))
        angular_coverage = occupied_bins / 36.0
        if (relative_error > MAX_CIRCLE_RELATIVE_ERROR
                or angular_coverage < MIN_CIRCLE_ANGULAR_COVERAGE):
            continue

        confidence = "high" if relative_error <= 0.02 and angular_coverage >= 0.85 else "medium"
        candidates.append(CircleCandidate(
            center_x_px=round(float(center_x), 3),
            center_y_px=round(float(center_y), 3),
            radius_px=round(radius, 3),
            radial_rms_error_px=round(rms_error, 4),
            relative_radial_error=round(relative_error, 5),
            angular_coverage=round(angular_coverage, 4),
            edge_pixel_count=len(local_x),
            confidence=confidence,
        ))

    candidates.sort(key=lambda item: (item.relative_radial_error, -item.angular_coverage))
    return tuple(candidates[:MAX_REPORTED_REGIONS])


def _fit_rectangle_candidates(edges) -> tuple[RectangleCandidate, ...]:
    """Detect axis-aligned rectangle proposals using coverage of all four sides.

    Rotated rectangles and perspective-distorted quadrilaterals are intentionally
    not fitted by this first implementation.
    """
    labels, label_count = _label_edges(edges)
    if label_count == 0:
        return ()

    proposals = []
    for label_id, region_slice in enumerate(ndimage.find_objects(labels), start=1):
        if region_slice is None:
            continue
        component = labels[region_slice] == label_id
        local_y, local_x = np.nonzero(component)
        if len(local_x) < MIN_REGION_PIXELS:
            continue
        y0, x0 = region_slice[0].start, region_slice[1].start
        x = local_x.astype(int) + x0
        y = local_y.astype(int) + y0
        x_min, x_max = int(x.min()), int(x.max())
        y_min, y_max = int(y.min()), int(y.max())
        width, height = x_max - x_min + 1, y_max - y_min + 1
        if min(width, height) < MIN_RECTANGLE_SIDE_PX:
            continue

        tol = RECTANGLE_EDGE_TOLERANCE_PX
        left = np.abs(x - x_min) <= tol
        right = np.abs(x - x_max) <= tol
        top = np.abs(y - y_min) <= tol
        bottom = np.abs(y - y_max) <= tol
        left_cov = len(np.unique(y[left])) / height
        right_cov = len(np.unique(y[right])) / height
        top_cov = len(np.unique(x[top])) / width
        bottom_cov = len(np.unique(x[bottom])) / width
        coverage = (left_cov, right_cov, top_cov, bottom_cov)
        if min(coverage) < MIN_RECTANGLE_SIDE_COVERAGE:
            continue

        # A rounded or oval contour can have high edge density but not four
        # independently supported straight sides. Require each side's points
        # to span most of its length and a non-degenerate bounding box.
        score = float(sum(coverage) / 4)
        proposals.append((score, RectangleCandidate(
            bounds=ImageBounds(x_min, y_min, x_max, y_max),
            center_x_px=round((x_min + x_max) / 2, 3),
            center_y_px=round((y_min + y_max) / 2, 3),
            width_px=float(width),
            height_px=float(height),
            side_coverage=tuple(round(float(v), 4) for v in coverage),
            edge_pixel_count=len(local_x),
            confidence="high" if min(coverage) >= 0.85 else "medium",
        )))

    proposals.sort(key=lambda item: (-item[0], -item[1].edge_pixel_count))
    # Multiple parallel edge traces from one thick pencil/CAD stroke can yield
    # nearly identical boxes. Keep only the strongest overlapping proposal.
    selected = []
    for _score, candidate in proposals:
        a = candidate.bounds
        duplicate = False
        for existing in selected:
            b = existing.bounds
            ix = max(0, min(a.x_max_px, b.x_max_px) - max(a.x_min_px, b.x_min_px) + 1)
            iy = max(0, min(a.y_max_px, b.y_max_px) - max(a.y_min_px, b.y_min_px) + 1)
            intersection = ix * iy
            area_a = a.width_px * a.height_px
            area_b = b.width_px * b.height_px
            union = area_a + area_b - intersection
            if union and intersection / union >= 0.80:
                duplicate = True
                break
        if not duplicate:
            selected.append(candidate)
        if len(selected) >= MAX_REPORTED_REGIONS:
            break
    return tuple(selected)


def detect_sketch_features(data: bytes, threshold: int = 48,
                           source_kind: str = "sketch") -> SketchObservation:
    if source_kind not in {"sketch", "photo"}:
        raise ValueError("source_kind must be 'sketch' or 'photo'")
    image = load_grayscale_image(data)
    edges = edge_map(image, threshold)
    pixels = np.asarray(edges, dtype=np.uint8)
    ys, xs = np.nonzero(pixels)
    bounds = None
    if len(xs):
        bounds = ImageBounds(int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    regions = _connected_edge_regions(edges)
    circle_candidates = _fit_circle_candidates(edges)
    rectangle_candidates = _fit_rectangle_candidates(edges)
    confidence = "low" if bounds is None else (
        "medium" if len(xs) >= 30 and regions else "low"
    )
    return SketchObservation(
        image_width_px=image.width,
        image_height_px=image.height,
        bounds=bounds,
        edge_pixel_count=int(len(xs)),
        threshold=threshold,
        source_kind=source_kind,
        confidence=confidence,
        regions=regions,
        circle_candidates=circle_candidates,
        rectangle_candidates=rectangle_candidates,
    )
