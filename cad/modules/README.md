# Engineering modules

All values are millimetres unless a field explicitly says inches.

- `dimensions.py`: reusable dimensional checks and hole patterns.
- `fpv_frame.py`: classic-X motor coordinates and motor mounting-hole coordinates (315 mm wheelbase, 18 mm arm width, 5 mm arm thickness by default). Center plates are 160 mm longitudinal on Y (+Y nose-forward) by 75 mm transverse on X.
- `fpv_frame_solid.py`: first-pass STEP-ready solids for two center plates, four removable arms, motor pads and four standoffs.
- `propeller.py`: 7-inch two-blade planform envelope and 5 mm bore defaults.
- `assembly.py`: assembly item validation and bill of materials.
- `dxf_export.py`: layered DXF export in millimetres.
- `service.py`: FPV layout and propeller planform DXF generation.

## Engineering limitations

The first FPV DXF remains a 2D layout reference. The new STEP solid builder creates separate top/bottom plate solids, four 18 mm-wide arms with widened motor pads, root and motor clearance holes, both 20 x 20 and 30.5 x 30.5 stack patterns, and four standoffs. The approved center-plate orientation is 160 mm longitudinal (Y) by 75 mm transverse (X). Standoffs are provisionally at X=+/-27.5 mm, Y=+/-65 mm. Two battery strap slots are provisionally centered at Y=+/-45 mm and run along X. The root-bolt pitch and motor-pad size remain provisional engineering assumptions, not user-confirmed manufacturing dimensions. Camera side plates, DJI O4 clearances, battery slots, fastener hardware, CNC tool compensation and structural validation are still outstanding.

Only the 7-inch diameter, two blades and 5 mm bore are carried over as previously specified design inputs. Hub diameter/thickness, chord widths and sweep are provisional starter values and must be confirmed before any detailed design.

The propeller DXF is a preliminary 2D planform only. It is not an aerodynamic blade solid: pitch, airfoil section, twist, hub retention, material, balance, stress, fatigue and rotor testing remain to be designed and validated. Do not manufacture or fly from this preliminary outline.

The generic STEP/STL endpoint still creates a sample four-hole plate. The FPV endpoint `POST /cad/fpv-frame/step` now exports the first-pass multi-part frame assembly as STEP. The FPV DXF endpoint remains a preliminary 2D layout; the propeller endpoint remains a planform reference only.
