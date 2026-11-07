"""Image-guided sketch and photo reconstruction primitives."""

from cad.sketch_photo.dimension_parser import ParsedDimension, parse_dimension_text
from cad.sketch_photo.feature_detection import detect_sketch_features
from cad.sketch_photo.geometry_inference import ProfileProposal, infer_profile_proposals
from cad.sketch_photo.profile_builder import ConfirmedProfileFeature, build_confirmed_sketch
from cad.sketch_photo.scale_calibration import pixels_per_mm, pixels_to_mm
from cad.sketch_photo.solid_builder import build_extruded_solid

__all__ = [
    "ConfirmedProfileFeature",
    "ParsedDimension",
    "ProfileProposal",
    "build_confirmed_sketch",
    "build_extruded_solid",
    "detect_sketch_features",
    "infer_profile_proposals",
    "parse_dimension_text",
    "pixels_per_mm",
    "pixels_to_mm",
]
