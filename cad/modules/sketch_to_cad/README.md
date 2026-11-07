# Sketch-to-CAD — stage 2

This module reconstructs a measurable 2D profile from a high-contrast sketch or
photograph. It deliberately distinguishes detected geometry from dimensions
that must be supplied by the user.

## Capabilities
- PNG/JPEG upload and dominant dark external silhouette extraction.
- Detection of directly enclosed internal contours (holes/cutouts).
- Simplified editable contour point lists in image-centred coordinates.
- Optional scale calibration from one known real-world length.
- Heuristic confidence score and explicit limitations.
- DXF export with separate `SKETCH_OUTLINE` and `SKETCH_HOLES` layers; calibrated files declare millimetres, while uncalibrated pixel-coordinate files are marked unitless.
- Prismatic STEP/STL export for calibrated profiles without internal holes,
  after the user supplies an explicit thickness.

## API
- `POST /cad/sketch-to-cad/analyze` — multipart image upload; optional
  `reference_length_mm` and `threshold` query parameters. Response includes
  `contour_points_mm`, `hole_contours_mm`, and `hole_count`.
- `POST /cad/sketch-to-cad/dxf` — same inputs, returning outer and internal
  closed profiles on separate DXF layers.
- `POST /cad/sketch-to-cad/solid/{step|stl}` — requires
  `reference_length_mm` and explicit `thickness_mm`.

Use a high-contrast orthographic sketch/photo with a plain background and the
whole part visible. The supplied reference dimension is assigned to the longer
side of the detected outer bounding box.

## Limitations and next stages
The current detector selects the largest connected external silhouette and
its directly enclosed holes. Disconnected parts, nested islands, tiny features,
dimension annotations, perspective correction, lens correction, and multi-view
registration are not implemented. 3D export currently refuses profiles with
holes rather than silently generating an incorrect solid. A single view cannot
infer depth, hidden faces, material, threads, wall thickness, or assembly
relationships. These require additional views, explicit dimensions, or user
confirmation. The confidence score is heuristic, not a probability or a
manufacturing acceptance metric.

Review dimensions and geometry before using any DXF for CNC.
