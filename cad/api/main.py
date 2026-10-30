"""Minimal parametric CAD API: sample mounting plate to STEP, STL and DXF."""
from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from build123d import Align, Box, Cylinder, Pos, export_step, export_stl
import ezdxf

app = FastAPI(title="MyAI Assistant CAD API", version="0.1.0")


class PlateParameters(BaseModel):
    length_mm: float = Field(default=100, gt=20, le=500)
    width_mm: float = Field(default=60, gt=20, le=300)
    thickness_mm: float = Field(default=5, gt=1, le=30)
    hole_diameter_mm: float = Field(default=5, gt=1, le=20)
    hole_inset_mm: float = Field(default=10, gt=2, le=100)


@app.get("/health")
def health():
    return {"status": "ok", "module": "cad", "units": "mm"}


@app.post("/cad/sample-plate/{format_name}")
def create_sample_plate(format_name: str, p: PlateParameters):
    """Generate a rectangular four-hole plate as step, stl or dxf."""
    fmt = format_name.lower()
    if fmt not in {"step", "stl", "dxf"}:
        raise HTTPException(status_code=400, detail="Supported formats: step, stl, dxf")
    if p.hole_inset_mm * 2 >= min(p.length_mm, p.width_mm):
        raise HTTPException(status_code=422, detail="Hole inset is too large for the plate")
    if p.hole_diameter_mm >= min(p.length_mm, p.width_mm) - 2 * p.hole_inset_mm:
        raise HTTPException(status_code=422, detail="Hole diameter does not fit the selected inset")

    with TemporaryDirectory() as temp:
        out = Path(temp) / f"sample_plate.{fmt}"
        if fmt in {"step", "stl"}:
            plate = Box(p.length_mm, p.width_mm, p.thickness_mm,
                        align=(Align.CENTER, Align.CENTER, Align.MIN))
            for x in (-p.length_mm / 2 + p.hole_inset_mm,
                      p.length_mm / 2 - p.hole_inset_mm):
                for y in (-p.width_mm / 2 + p.hole_inset_mm,
                          p.width_mm / 2 - p.hole_inset_mm):
                    cutter = Pos(x, y, -1) * Cylinder(
                        p.hole_diameter_mm / 2, p.thickness_mm + 2,
                        align=(Align.CENTER, Align.CENTER, Align.MIN))
                    plate = plate - cutter
            if fmt == "step":
                export_step(plate, str(out))
            else:
                export_stl(plate, str(out), tolerance=0.05, angular_tolerance=0.1)
        else:
            doc = ezdxf.new("R2010")
            msp = doc.modelspace()
            x0, y0 = -p.length_mm / 2, -p.width_mm / 2
            x1, y1 = p.length_mm / 2, p.width_mm / 2
            msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True)
            for x in (-p.length_mm / 2 + p.hole_inset_mm,
                      p.length_mm / 2 - p.hole_inset_mm):
                for y in (-p.width_mm / 2 + p.hole_inset_mm,
                          p.width_mm / 2 - p.hole_inset_mm):
                    msp.add_circle((x, y), p.hole_diameter_mm / 2)
            doc.header["$INSUNITS"] = 4  # millimetres
            doc.saveas(out)
        payload = out.read_bytes()
    return Response(
        content=payload,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="sample_plate.{fmt}"'},
    )
