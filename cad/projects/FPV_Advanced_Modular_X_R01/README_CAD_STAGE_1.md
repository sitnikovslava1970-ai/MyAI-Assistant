# CAD stage 1 — FPV Advanced Modular X R01

The existing CAD stack in this repository is build123d, declared in cad/requirements.txt. This project uses that stack rather than adding a second CAD dependency.

## First-pass geometry
- Hybrid Deadcat X motor layout, four replaceable arms.
- Target diagonal motor-to-motor wheelbase: 327 mm.
- Motor coordinates: front ±140 × +112 mm; rear ±98 × −112 mm.
- Nominal propeller diameter: 177.8 mm. The layout validator checks pairwise propeller-envelope gaps.
- Center plates: 160 × 75 mm; lower plate 3 mm, upper plate 2 mm.
- Arms: 22 mm wide × 6 mm thick.
- Four M3 clearance holes per arm root; root clamp holes are in the lower plate, stack patterns are on the upper plate to keep the two hole systems on separate Z levels.
- Motor pattern: 19 × 19 mm M3. A 16 × 16 mm motor requires a separate adapter; overlapping patterns are not drilled together.
- STEP export creates separately named solids for both plates, four arms and four standoffs.

## Files
- cad/modules/advanced_modular_x.py — dimensions, coordinates, propeller gap and edge-distance checks, solid builder and STEP export.
- cad/tests/test_advanced_modular_x.py — layout regression tests.

## Not a production release
The model still requires execution in Codespaces, CAD kernel validation, fastener/nut-trap detailing, actual motor and electronics envelope checks, propeller swept-volume review, battery and wiring layout, mass properties, laminate specification, structural assessment and manufacturing review. No CNC DXF is released at this stage.
