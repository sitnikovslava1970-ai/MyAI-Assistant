# Engineering modules

All values are millimetres unless a field explicitly says inches.

- `dimensions.py`: reusable dimensional checks and hole patterns.
- `fpv_frame.py`: classic-X motor coordinates and motor mounting-hole coordinates (315 mm wheelbase, 18 mm arm width, 5 mm arm thickness by default).

- `advanced_modular_x.py`: separate 327 mm Hybrid Deadcat X R01 concept with four replaceable 22×6 mm arms, 3 mm lower and 2 mm upper plates, four M3 arm-root holes per arm, 19×19 mm motor pattern, both 20×20 and 30.5×30.5 mm stack patterns, and four bored standoffs. Both stack patterns are cut through both center plates. The dimensional validator also enforces a 2 mm minimum material web between all lower-plate mounting holes and checks that stack and standoff holes retain plate-edge clearance.
- `tests/test_advanced_modular_x.py`: parameter, propeller-envelope, arm-root, stack-hole and STEP-solid/export integration checks for the Advanced Modular X model.

- `fpv_frame_solid.py`: first-pass STEP-ready solids for two center plates, four removable arms, motor pads and four standoffs.
- `propeller.py`: 7-inch two-blade planform envelope and 5 mm bore defaults.
- `assembly.py`: assembly item validation and bill of materials.
- `dxf_export.py`: layered DXF export in millimetres.
- `service.py`: FPV layout and propeller planform DXF generation.

## Engineering limitations

The first FPV DXF remains a 2D layout reference. The new STEP solid builder creates separate top/bottom plate solids, four 18 mm-wide arms with widened motor pads, root and motor clearance holes, both 20 x 20 and 30.5 x 30.5 stack patterns, and four standoffs. The root-bolt pitch, standoff locations and motor-pad size are provisional engineering assumptions, not user-confirmed manufacturing dimensions. Camera side plates, DJI O4 clearances, battery slots, fastener hardware, CNC tool compensation and structural validation are still outstanding.

Only the 7-inch diameter, two blades and 5 mm bore are carried over as previously specified design inputs. Hub diameter/thickness, chord widths and sweep are provisional starter values and must be confirmed before any detailed design.

The propeller DXF is a preliminary 2D planform only. It is not an aerodynamic blade solid: pitch, airfoil section, twist, hub retention, material, balance, stress, fatigue and rotor testing remain to be designed and validated. Do not manufacture or fly from this preliminary outline.

The generic STEP/STL endpoint still creates a sample four-hole plate. The FPV endpoint `POST /cad/fpv-frame/step` now exports the first-pass multi-part frame assembly as STEP. The FPV DXF endpoint remains a preliminary 2D layout; the propeller endpoint remains a planform reference only.
