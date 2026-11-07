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

## Recheck of corrected STEP package R03

A fresh STEP package generated after the two geometry corrections was imported and checked again. **15 solids were inspected; 0 unintended volume intersections were found.** The former four intersection pairs are now clear in the exported STEP. This verifies the current solid geometry only; it does not verify fastener access, carbon strength or physical fit.

## Corrective changes and CI validation

- Raised the nominal camera center by 2.5 mm to separate the camera envelope from the integrated lower foot pads.
- Added 4 x 4 mm rear-corner relief notches to the camera base plate to clear the front-arm envelopes.
- Added pairwise solid-intersection regression tests; the corrected STEP export has no unintended solid overlaps.
- CI result: 19 tests passed; STEP/STL and preliminary DXF export steps succeeded.
- DXF profiles are generated for 7 flat parts (two center plates, four arms and camera base plate). The files use millimetres and OUTLINE, HOLES and NOTES layers; independent DXF audit found no errors or duplicate entities.

## Camera support redesign — R06

- Split the left and right camera side panels into independent 2 mm carbon parts.
- Added two separate angled support brackets, one per side, with horizontal mounting feet and four total M3 attachment points to the camera base plate.
- The side panels retain two adjustable 4.5 × 2.2 mm slots per side, with 16 mm nominal pitch.
- Added the two flat side panels to the DXF package in their local panel plane (DXF X = local panel Y; DXF Y = local panel Z). The two 3D support brackets remain STEP/STL parts and are not DXF cut profiles.
- The support bracket material is not selected: PA12-CF or 6061 aluminium remain alternatives pending strength, vibration and manufacturing review.
- CI passed for the R06 geometry and DXF export. Separate STL meshes for all physical parts are watertight; the complete assembly STL is a multi-part compound and is not expected to be watertight as one shell.

**Remaining camera verification:** confirm the physical O4 Pro camera screw pattern against the slots, check fastener tool access and cable bend radius, and validate the bracket stiffness and foot edge distances before CNC or flight use.

## R06 — assembly clearance verification (latest exported STEP)

**Artifact:** GitHub Actions run `41846081883`, branch `work/fpv-7in-assembly-package`, commit `69b7ef23c7cd54d75ee6ae9a8b5389bac6d4bd3e`.  
**Method:** imported the exported STEP assembly and all 15 physical component STEP files; checked pairwise solid intersection volumes and minimum shape distances. Reference envelopes for the DJI O4 Pro camera and transmission module were also checked against each physical component.

### Results

- 15 physical components and 2 reference envelopes were present in the exported assembly.
- No positive-volume intersections were found between any pair of physical components.
- No positive-volume intersections were found between the reference envelopes and physical components.
- The closest non-contact clearances are:

| Pair | Minimum distance |
|---|---:|
| Camera base plate — front-left/front-right arms | 1.253 mm |
| DJI O4 Pro transmission-module envelope — rear-left/rear-right arms | 2.000 mm |
| Camera side panels — camera-module envelope | 0.700 mm per side |
| Camera base plate — camera side panels | 2.511 mm |
| Upper center plate — camera side panels | 3.031 mm |

### R06 fastener-hole edge-distance screening

The following are geometric distances from the current R06 hole centers to the nearest nominal part edge. “Remaining material” is center-to-edge distance minus the hole radius; it is not a laminate-strength acceptance criterion.

| Feature | Hole | Minimum center-to-edge | Nominal remaining material |
|---|---:|---:|---:|
| Arm-root holes in center plate | Ø3.2 mm | 5.303 mm | 3.703 mm |
| DJI O4 transmission-module holes in lower plate | Ø2.2 mm | 4.750 mm | 3.650 mm |
| Camera-base mounting holes in lower plate | Ø3.2 mm | 4.000 mm | 2.400 mm |
| Camera-support foot holes in camera base plate | Ø3.2 mm | 4.500 mm | 2.900 mm |
| Motor holes in 28 mm motor pads | Ø3.2 mm | 4.500 mm | 2.900 mm |
| Arm-root holes across 18 mm arm width | Ø3.2 mm | 4.500 mm | 2.900 mm |
| Standoff holes in center plates | Ø3.2 mm | 10.000 mm | 8.400 mm |

The camera-base mounting holes in the lower plate have the smallest nominal remaining edge material in this screening (2.4 mm). Review this location against the chosen carbon laminate, washer/head diameter, local loading and manufacturing tolerances. Do not infer structural adequacy from the table.

### Intended contacts

- Lower center plate to arm roots and camera base plate: face-to-face mounting contact.
- Lower/upper plates to standoffs: face-to-face mounting contact.
- Camera support brackets to camera base plate and side panels: mounting contact.
- DJI O4 Pro transmission-module envelope to underside of lower plate: intended mounting contact.

### Engineering interpretation / open checks

- The 1.253 mm camera-base-to-arm gap is small for a carbon part in a vibrating assembly. Keep it as a review warning; consider increasing the rear-corner relief only after checking remaining material around the M3 holes and the camera-base stiffness.
- The 2.0 mm air-unit-to-rear-arm gap is a geometric clearance only. It does not provide evidence of sufficient cooling or antenna separation.
- The 0.7 mm camera side clearance is nominal CAD clearance. Confirm the actual camera body, screw heads, washers and manufacturing tolerances.
- The support brackets touch the camera reference envelope at their intended support interface but do not penetrate it by volume. Verify the actual housing contact surface and ensure no contact with cable or connector features.
- Battery geometry, battery strap thickness/path, FC/ESC stack bodies, wiring, antenna mounts, connectors and fastener heads are not represented as full solids. Their clearances are **not verified**.
- DJI antenna separation from carbon must be checked against the actual antenna locations and routing; the current model does not establish the required separation.

**R06 status:** geometric no-intersection check passed. This is not a physical-fit, structural, thermal, vibration, CNC or flight approval.

## Earlier correction notes

- Raised the nominal camera center by 2.5 mm to separate the camera envelope from the integrated lower foot pads.
- Added 4 x 4 mm rear-corner relief notches to the camera base plate to clear the front-arm envelopes.
- Added a solid-level pairwise intersection regression test. The first CI attempt exposed a test-harness issue (the CAD kernel returns `None` for disjoint solids); the test now treats that as a valid no-intersection result. The corrected run completed successfully.

**Historical note:** this caveat applied before the R06 redesign. In R06, the two carbon side panels are separate planar parts and the angled support brackets are separate 3D components.

## Next engineering actions

1. Correct the camera foot/camera-envelope interference without compromising the camera angle or fastener edge distances.
2. Relieve the camera base plate rear corners or revise its footprint to clear both front arms.
3. Add automated pairwise solid-intersection checks to the CAD test pipeline; reference envelopes must also remain clear of physical parts unless an intentional contact is documented.
4. Re-run STEP export and verify the new assembly has no unintended solid intersections.
5. Confirm the 160 × 75 mm plate orientation before generating final DXF profiles.
6. Then produce DXF outlines, hole layers, dimensioned drawings, BOM and CNC checklist.

**Release gate:** do not call the design CNC-ready or flight-ready until the coordinate convention, physical component fit, fastener edge distances, laminate details, strength, vibration and thermal/antenna requirements are verified.
