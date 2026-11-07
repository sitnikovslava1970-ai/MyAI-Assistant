"""First-pass raster feature detection; returns observations, not a CAD solid."""
import numpy as np
from scipy import ndimage

from cad.sketch_photo.image_preprocess import edge_map, load_grayscale_image
from cad.sketch_photo.schemas import FeatureRegion, ImageBounds, SketchObservation

MIN_REGION_PIXELS = 6
MAX_REPORTED_REGIONS = 100


def _connected_edge_regions(edges) -> tuple[FeatureRegion, ...]:
    """Group 8-connected edge pixels into image-space region proposals."""
    edge_array = np.asarray(edges, dtype=np.uint8)
    labels, label_count = ndimage.label(
        edge_array, structure=np.ones((3, 3), dtype=np.uint8)
    )
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
        bounds = ImageBounds(
            int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
        )
    regions = _connected_edge_regions(edges)
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
    )
