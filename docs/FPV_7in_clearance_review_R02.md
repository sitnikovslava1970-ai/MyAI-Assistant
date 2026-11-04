# FPV 7-inch Classic-X — geometric clearance review R02

**Branch:** `work/fpv-7in-assembly-package`  
**Reviewed artifact:** `FPV_7in_ClassicX_Assembly.step` from assembly package R02  
**Status:** review findings; not a CNC release.

## Coordinate convention found in the current model

- X is the 160 mm center-plate dimension.
- Y is the 75 mm center-plate dimension.
- Camera/front direction is +Y.
- Motor centers are at (+/-111.37, +/-111.37) mm for a 315 mm diagonal wheelbase.
- Therefore the 160 mm plate dimension is transverse to the camera/front direction in the current implementation.

This is an explicit property of the current code, not a verified user-approved orientation. Confirm before final production drawings.

## Exact STEP solid-intersection check

Imported the exported STEP and checked pairwise solid intersections. Four non-zero intersections were found:

| Part A | Part B | Intersection volume | Bounding region (mm) |
|---|---|---:|---|
| CAMERA_SIDE_LEFT | REF_CAMERA_O4_PRO | 5.9397 mm³ | X -12.775…-11.475, Y 51.016…55.610, Z 4.011…6.000 |
| CAMERA_SIDE_RIGHT | REF_CAMERA_O4_PRO | 5.9397 mm³ | X 11.475…12.775, Y 51.016…55.610, Z 4.011…6.000 |
| ARM_FRONT_LEFT | CAMERA_BASE_PLATE | 0.05195 mm³ | X -18.000…-17.772, Y 30.500…30.728, Z 2…4 |
| ARM_FRONT_RIGHT | CAMERA_BASE_PLATE | 0.05195 mm³ | X 17.772…18.000, Y 30.500…30.728, Z 2…4 |

The side-plate intersections occur where the integrated lower foot pads enter the camera reference envelope. The base-plate intersections occur at its two rear corners where it meets the front arm envelopes.

## Preliminary hole-edge observations

- Lower plate arm-root holes: minimum center-to-edge distance 5.303 mm; with Ø3.2 mm holes, nominal remaining edge material is about 3.703 mm.
- Lower plate O4 mounting holes: minimum center-to-edge distance 4.75 mm; with Ø2.2 mm holes, nominal remaining edge material is about 3.65 mm.
- Lower plate camera-base holes: center-to-edge distance 4.0 mm; with Ø3.2 mm holes, nominal remaining edge material is 2.4 mm.
- Camera base side-foot M3 holes are only 3.525 mm from the base plate side edge (about 1.925 mm remaining material outside a Ø3.2 mm hole). Treat this as a design-review item, not an approved carbon edge distance.

These are geometric measurements only. They do not establish laminate strength or suitability for flight loads.

## Next engineering actions

1. Correct the camera foot/camera-envelope interference without compromising the camera angle or fastener edge distances.
2. Relieve the camera base plate rear corners or revise its footprint to clear both front arms.
3. Add automated pairwise solid-intersection checks to the CAD test pipeline; reference envelopes must also remain clear of physical parts unless an intentional contact is documented.
4. Re-run STEP export and verify the new assembly has no unintended solid intersections.
5. Confirm the 160 × 75 mm plate orientation before generating final DXF profiles.
6. Then produce DXF outlines, hole layers, dimensioned drawings, BOM and CNC checklist.

**Release gate:** do not call the design CNC-ready or flight-ready until the coordinate convention, physical component fit, fastener edge distances, laminate details, strength, vibration and thermal/antenna requirements are verified.
