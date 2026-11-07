# Sketch-to-CAD — stage 1

This module begins photo/sketch reconstruction with a measurable 2D silhouette.
It does not pretend that one photograph contains complete 3D engineering data.

## Capabilities
- PNG/JPEG upload and dominant dark silhouette extraction.
- Simplified editable contour points.
- Optional scale calibration from one known real-world length.
- Heuristic confidence score and explicit limitations.
- DXF export of the closed outer profile in millimetres.

## API
- POST /cad/sketch-to-cad/analyze — multipart image upload; optional reference_length_mm and threshold query parameters.
- POST /cad/sketch-to-cad/dxf — same inputs, returning a DXF outline.

Use a high-contrast orthographic sketch/photo with a plain background and the
whole part visible. The supplied reference dimension is assigned to the longer
side of the detected bounding box.

## Limitations and next stages
Only the largest external contour is traced. Internal holes, slots, separate
parts, perspective correction, feature recognition and STEP solid generation
are not yet implemented. A single view cannot infer depth, hidden faces,
material, threads, wall thickness or assembly relationships. These require
additional views, explicit dimensions or user confirmation. The confidence
score is heuristic, not a probability or manufacturing acceptance metric.

Review dimensions and geometry before using any DXF for CNC.
