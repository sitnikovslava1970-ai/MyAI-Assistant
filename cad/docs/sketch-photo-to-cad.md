# Sketch-to-CAD and Photo-to-CAD

## Goal

Add an image-guided CAD workflow that turns engineering sketches, dimensioned drawings, and photographs into editable parametric 3D models. The system must maximize similarity to the supplied reference while clearly separating measured facts from inferred geometry.

This feature supplements, rather than replaces, the existing build123d CAD generation pipeline.

## Input modes

1. **Dimensioned sketch or drawing**
   - Accept raster images and, where supported, vector drawings.
   - Detect line segments, arcs, circles, centerlines, dimensions, leaders, and text.
   - Parse explicit dimensions and units.
   - Build a constrained 2D profile before extrusion or other 3D operations.

2. **Undimensioned sketch**
   - Detect contours and geometric relationships.
   - Ask for at least one known reference dimension when absolute scale is required.
   - Mark estimated dimensions and uncertain features.
   - Allow the user to correct detected geometry before solid generation.

3. **Single photograph**
   - Detect the visible object silhouette, major faces, edges, holes, and repeated features.
   - Estimate camera perspective and object orientation where possible.
   - Do not claim hidden dimensions or unseen geometry are measured.
   - Generate a provisional model with explicit assumptions and confidence metadata.

4. **Multiple photographs**
   - Support front, side, top, and oblique views of the same object.
   - Align views using common landmarks and known dimensions.
   - Reconcile inconsistent observations and flag occluded or ambiguous areas.
   - Prefer multi-view reconstruction over single-view guesses.

## Processing pipeline

1. Validate image format, resolution, orientation, and quality.
2. Correct rotation and, where possible, lens/perspective distortion.
3. Detect object boundaries, edges, primitives, text, and dimension annotations.
4. Establish image scale from explicit dimensions or a user-supplied reference measurement.
5. Build a 2D vector/constraint representation with source coordinates.
6. Infer 3D features using engineering primitives and multi-view evidence.
7. Build editable solids using build123d; retain feature parameters and construction history where feasible.
8. Render the candidate model from matching camera viewpoints.
9. Compare projected model contours and visible features against the reference images.
10. Report deviations, uncertain regions, and assumptions; allow parameter corrections and regeneration.
11. Validate the solid and export STEP, STL, and DXF as appropriate.

## Similarity and accuracy requirements

- Preserve the reference silhouette and major proportions.
- Match explicit dimensions before optimizing visual similarity.
- Use calibrated scale whenever a known dimension is available.
- Track detected, measured, inferred, and user-confirmed values separately.
- Compare rendered silhouettes, edge locations, hole centers, and major feature dimensions.
- Provide per-feature confidence/uncertainty rather than one misleading global accuracy score.
- Never describe a model as manufacturing-ready solely because it visually resembles a photograph.
- Require dimensional review, tolerances, material/process constraints, and CAD validity checks before CNC release.

## Proposed module layout

- `cad/sketch_photo/`
  - `schemas.py` — input, observation, dimension, and confidence data structures.
  - `image_preprocess.py` — image normalization and perspective preparation.
  - `feature_detection.py` — connected edge regions and conservative primitive proposals.
  - `dimension_parser.py` — OCR-assisted dimension and unit extraction.
  - `scale_calibration.py` — pixel-to-unit calibration.
  - `geometry_inference.py` — conversion of observations into parametric feature proposals.
  - `model_builder.py` — build123d solid construction.
  - `similarity_check.py` — view projection and reference comparison.
  - `quality_report.py` — uncertainty, deviations, and validation report.
- `tests/sketch_photo/` — deterministic tests using synthetic drawings and controlled reference images.
- `cad/examples/sketch_photo/` — non-sensitive sample inputs and expected outputs.

## API proposal

- `POST /cad/from-sketch` — create a model from a sketch/drawing.
- `POST /cad/from-photo` — create a provisional model from one or more photographs.
- `POST /cad/compare-reference` — compare a generated model with supplied reference views.
- `GET /cad/jobs/{job_id}` — retrieve processing status and report for asynchronous jobs.

The implemented inspection endpoint is `POST /cad/sketch/analyze`. It returns image-space edge bounds, connected-region proposals, and conservative fitted circle and axis-aligned rectangle candidates; it does not yet confirm holes or return a 3D solid.

## User review workflow

1. Upload sketch, drawing, or photographs.
2. Select units and provide a known dimension if available.
3. Review detected dimensions, contours, and uncertain regions.
4. Confirm or correct the proposed geometry.
5. Generate the editable 3D model.
6. Inspect side-by-side and overlay comparisons.
7. Approve dimensions and export files.

The system should not silently invent missing dimensions. It should ask for clarification when an ambiguity materially changes the geometry.

## Testing

- Dimension parsing and unit conversion, including diameter/radius/thread symbols, repeated quantities, decimal commas, and explicit inch/centimetre conversion.
- Scale calibration with known synthetic references.
- Perspective and rotation normalization.
- Circle, rectangle, line, arc, and contour detection.
- Multi-view consistency and occlusion handling.
- Parametric model validity and export round-trips.
- Similarity metrics on controlled test fixtures.
- Failure cases: no scale reference, blurry image, severe occlusion, conflicting dimensions, and unsupported geometry.

## Implementation stages

1. **Foundation:** schemas, image upload validation, connected edge-region extraction, primitive proposals, and scale calibration.
2. **Dimensioned drawings:** dimension parsing, constrained 2D profiles, and extrusion.
3. **Photographs:** single-view provisional geometry with uncertainty reporting.
4. **Multi-view:** alignment and cross-view geometry reconciliation.
5. **Similarity loop:** render, compare, identify deviations, and regenerate after parameter correction.
6. **Production gates:** CAD validity, tolerance review, export checks, and explicit manufacturing approval.

## Important limitations

A single perspective photograph generally cannot uniquely determine true 3D dimensions or hidden surfaces. Accurate reconstruction requires scale information and preferably multiple calibrated views. Photogrammetry or learned 3D reconstruction may be integrated as optional providers later, but their output must still be converted into and checked as editable CAD geometry.

## Current implementation status

Implemented:
- Raster loading for PNG/JPEG/TIFF with byte and pixel-count limits.
- EXIF orientation correction, grayscale conversion, and contrast normalization.
- Edge-map generation and overall image-space bounds.
- 8-connected edge-region proposals with bounding boxes, centers, pixel counts, aspect ratios, and conservative shape hints.
- Conservative least-squares circle fitting with radial residual and angular-coverage rejection.
- Axis-aligned rectangle proposals requiring sufficient coverage on all four sides, with duplicate-box suppression.
- Explicit pixel-to-millimetre calibration from a user-confirmed reference length.
- Conservative OCR-text dimension parser for diameter, radius, metric thread, repeated-count, and linear annotations; metric thread pitch callouts (for example, M3x0.5) are retained. Explicit inch/centimetre units are normalized to millimetres. Plain unlabelled numbers are ignored. Parsed values remain review-required.
- Conversion of fitted circle and rectangle candidates into millimetre 2D profile proposals using an explicit scale; image center is the coordinate origin and image Y is inverted to Cartesian CAD Y.
- Closed planar build123d sketches from explicitly confirmed additive/subtractive circles and rectangles; detected circles are never assumed to be holes without user confirmation.
- OCR-text dimension parsing for linear, diameter, radius, and thread annotations, repeated quantities, decimal commas, and explicit mm/cm/inch conversion. Bare numbers are ignored to reduce false positives; all parsed dimensions require user confirmation.
- Synthetic-image tests for edge detection, connected regions, circle fitting, rectangle fitting/rejection, empty images, API responses, scale calibration, and 2D profile proposals.

Circle candidates are geometric proposals, not confirmed holes or CAD features. A circle may represent an outer contour, a marking, or a hole; semantic classification and dimensional confirmation remain future work. Rectangle candidates are axis-aligned image-space proposals; rotated and perspective-distorted quadrilaterals are not yet handled. Profile proposals still require review and explicit feature intent before being passed to the closed planar sketch builder; the builder does not yet create 3D solids. Region proposals are not fitted arcs or complete CAD contours. The system still does not perform OCR image recognition itself (the new parser accepts OCR text from a future OCR provider), full general vectorization, or 3D reconstruction, and it does not infer physical dimensions without a scale reference.
