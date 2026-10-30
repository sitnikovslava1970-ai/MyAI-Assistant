# Engineering modules

All values are millimetres unless a field explicitly says inches.

- `dimensions.py`: reusable dimensional checks and hole patterns.
- `fpv_frame.py`: classic-X motor coordinates and motor mounting-hole coordinates.
- `propeller.py`: 7-inch two-blade planform envelope and 5 mm bore defaults.
- `assembly.py`: assembly item validation and bill of materials.
- `dxf_export.py`: layered DXF export in millimetres.
- `service.py`: FPV layout and propeller planform DXF generation.

## Engineering limitations

The first FPV DXF is a layout reference containing top/bottom plate envelopes, four arm envelopes and motor mounting holes. It does not yet include the final four-arm root bolt pattern, standoff holes, camera side plates, DJI O4 clearances, battery slots, stack mounting holes or CNC tool compensation.

The propeller DXF is a preliminary 2D planform only. It is not an aerodynamic blade solid: pitch, airfoil section, twist, hub retention, material, balance, stress, fatigue and rotor testing remain to be designed and validated. Do not manufacture or fly from this preliminary outline.

The generic STEP/STL endpoint currently creates a sample four-hole plate. FPV and propeller specific endpoints currently provide JSON parameter/specification output and DXF planform export. Full solid models and assembly STEP export are a subsequent implementation stage.
