# CAD API

The FastAPI app is intentionally small and safe to extend. It has no authentication and should only be run locally or behind an authenticated gateway. Do not expose it publicly as-is.

Example request:

```bash
curl -X POST http://127.0.0.1:8000/cad/sample-plate/stl \
  -H "Content-Type: application/json" \
  -d '{"length_mm":100,"width_mm":60,"thickness_mm":5,"hole_diameter_mm":5,"hole_inset_mm":10}' \
  --output sample_plate.stl
```

Replace `stl` with `step` or `dxf` for the other exports.
