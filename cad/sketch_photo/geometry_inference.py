"""Convert fitted image-space primitives into millimetre profile proposals."""
from dataclasses import asdict, dataclass
from math import isfinite
from typing import Literal

from cad.sketch_photo.schemas import SketchObservation


@dataclass(frozen=True)
class ProfileProposal:
    """A scaled 2D primitive proposal; not yet a constrained CAD sketch."""
    kind: Literal["circle", "rectangle"]
    center_x_mm: float
    center_y_mm: float
    width_mm: float
    height_mm: float
    radius_mm: float | None
    confidence: Literal["medium", "high"]
    source_edge_pixel_count: int

    def to_dict(self) -> dict:
        return asdict(self)


def infer_profile_proposals(
    observation: SketchObservation,
    scale_px_per_mm: float,
) -> tuple[ProfileProposal, ...]:
    """Scale fitted primitives into a centered Cartesian XY coordinate system.

    The scale must come from a user-confirmed reference length. Image Y is
    inverted so positive CAD Y points upward. The image center is the origin.
    """
    if not isfinite(scale_px_per_mm) or scale_px_per_mm <= 0:
        raise ValueError("scale_px_per_mm must be finite and greater than zero")

    image_center_x = (observation.image_width_px - 1) / 2
    image_center_y = (observation.image_height_px - 1) / 2
    proposals = []

    for circle in observation.circle_candidates:
        radius_mm = circle.radius_px / scale_px_per_mm
        proposals.append(ProfileProposal(
            kind="circle",
            center_x_mm=round((circle.center_x_px - image_center_x) / scale_px_per_mm, 4),
            center_y_mm=round((image_center_y - circle.center_y_px) / scale_px_per_mm, 4),
            width_mm=round(2 * radius_mm, 4),
            height_mm=round(2 * radius_mm, 4),
            radius_mm=round(radius_mm, 4),
            confidence=circle.confidence,
            source_edge_pixel_count=circle.edge_pixel_count,
        ))

    for rectangle in observation.rectangle_candidates:
        bounds = rectangle.bounds
        center_x_px = (bounds.x_min_px + bounds.x_max_px) / 2
        center_y_px = (bounds.y_min_px + bounds.y_max_px) / 2
        # Use the distance between detected edge coordinates, not pixel count.
        width_px = bounds.x_max_px - bounds.x_min_px
        height_px = bounds.y_max_px - bounds.y_min_px
        proposals.append(ProfileProposal(
            kind="rectangle",
            center_x_mm=round((center_x_px - image_center_x) / scale_px_per_mm, 4),
            center_y_mm=round((image_center_y - center_y_px) / scale_px_per_mm, 4),
            width_mm=round(width_px / scale_px_per_mm, 4),
            height_mm=round(height_px / scale_px_per_mm, 4),
            radius_mm=None,
            confidence=rectangle.confidence,
            source_edge_pixel_count=rectangle.edge_pixel_count,
        ))

    return tuple(proposals)
