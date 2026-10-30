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

Open http://127.0.0.1:8000/docs for the API. The first endpoint creates a sample mounting plate and exports STEP, STL and DXF.

## Browser viewer
Open `3d_viewer/index.html` in a modern browser, choose an STL file, and orbit/zoom the model. The viewer loads Three.js modules from jsDelivr, so an internet connection is required. For reliable module loading, serve the repository folder over HTTP rather than opening the file directly.

## Initial scope
- Parametric solid modelling with build123d.
- STEP and STL export from the same solid.
- 2D DXF export with ezdxf.
- STL preview with Three.js.
- API validation and health endpoint.

This is a starter foundation, not a production-certified CAD/CAM pipeline. Validate dimensions, tolerances, units, mesh quality and CNC toolpaths independently before manufacturing.
