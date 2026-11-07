"""Small, dependency-light data structures for image-to-CAD observations."""
from dataclasses import asdict, dataclass
from typing import Literal


@dataclass(frozen=True)
class ImageBounds:
    x_min_px: int
    y_min_px: int
    x_max_px: int
    y_max_px: int

    @property
    def width_px(self) -> int:
        return self.x_max_px - self.x_min_px + 1

    @property
    def height_px(self) -> int:
        return self.y_max_px - self.y_min_px + 1


@dataclass(frozen=True)
class FeatureRegion:
    """A connected edge fragment in image coordinates, not a fitted CAD primitive."""
    bounds: ImageBounds
    edge_pixel_count: int
    center_x_px: float
    center_y_px: float
    aspect_ratio: float
    pixel_density: float
    shape_hint: Literal["elongated", "compact_candidate", "irregular"]


@dataclass(frozen=True)
class SketchObservation:
    image_width_px: int
    image_height_px: int
    bounds: ImageBounds | None
    edge_pixel_count: int
    threshold: int
    source_kind: Literal["sketch", "photo"] = "sketch"
    scale_px_per_mm: float | None = None
    confidence: Literal["low", "medium", "high"] = "low"
    regions: tuple[FeatureRegion, ...] = ()

    def to_dict(self) -> dict:
        return asdict(self)
