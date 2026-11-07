# CAD + 3D browser foundation

This folder contains the first CAD backend and a browser-based STL viewer.

## Runtime note
The browser viewer works on Android and desktop. Parametric CAD generation uses Python and build123d and therefore needs a Python server/runtime; GitHub stores the source but does not execute CAD code. Do not put API keys or private credentials in this repository.

## Run the CAD API
From the repository root, in a Python 3.11+ environment:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r cad/requirements.txt
uvicorn cad.api.main:app --reload
```

Open http://127.0.0.1:8000/docs for the API. The sample endpoint creates a mounting plate and exports STEP, STL and DXF. The FPV assembly endpoint `POST /cad/fpv-frame/step` exports the first-pass Classic-X frame assembly. The separate Advanced Modular X R01 concept is available through `POST /cad/advanced-modular-x/spec` (validated dimensions) and `POST /cad/advanced-modular-x/step` (STEP compound export). Its default geometry is the 327 mm Hybrid Deadcat X layout; it is a separate model from the 315 mm Classic-X endpoint.

## Browser viewer
Open `3d_viewer/index.html` in a modern browser, choose an STL file, and orbit/zoom the model. The viewer loads Three.js modules from jsDelivr, so an internet connection is required. For reliable module loading, serve the repository folder over HTTP rather than opening the file directly.

## Sketch-to-CAD

The first Sketch-to-CAD stage is documented in cad/modules/sketch_to_cad/README.md. It provides PNG/JPEG silhouette analysis, optional scale calibration from one known dimension, and DXF outline export through the /cad/sketch-to-cad/analyze and /cad/sketch-to-cad/dxf endpoints. The API also supports a simple prismatic STEP/STL extrusion when the user supplies a reference dimension and explicit thickness. This is not automatic full 3D reconstruction.

## Initial scope
- Parametric solid modelling with build123d, including a first-pass multi-part 7-inch Classic-X STEP assembly.
- STEP and STL export from the same solid.
- 2D DXF export with ezdxf.
- STL preview with Three.js.
- API validation and health endpoint.

This is a starter foundation, not a production-certified CAD/CAM pipeline. Validate dimensions, tolerances, units, mesh quality and CNC toolpaths independently before manufacturing.
