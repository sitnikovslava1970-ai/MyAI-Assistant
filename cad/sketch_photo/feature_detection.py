"""First-pass image feature detection; returns observations, not a CAD solid."""
from cad.sketch_photo.image_preprocess import edge_map, load_grayscale_image
from cad.sketch_photo.schemas import ImageBounds, SketchObservation


def detect_sketch_features(data: bytes, threshold: int = 48,
                           source_kind: str = "sketch") -> SketchObservation:
    if source_kind not in {"sketch", "photo"}:
        raise ValueError("source_kind must be 'sketch' or 'photo'")
    image = load_grayscale_image(data)
    edges = edge_map(image, threshold)
    pixels = edges.load()
    xs, ys = [], []
    for y in range(edges.height):
        for x in range(edges.width):
            if pixels[x, y]:
                xs.append(x)
                ys.append(y)
    bounds = None
    if xs:
        bounds = ImageBounds(min(xs), min(ys), max(xs), max(ys))
    confidence = "low" if bounds is None else (
        "medium" if len(xs) >= 30 else "low"
    )
    return SketchObservation(
        image_width_px=image.width,
        image_height_px=image.height,
        bounds=bounds,
        edge_pixel_count=len(xs),
        threshold=threshold,
        source_kind=source_kind,
        confidence=confidence,
    )
