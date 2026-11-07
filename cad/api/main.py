"""Minimal parametric CAD API: sample mounting plate to STEP, STL and DXF."""
from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field
from cad.modules.fpv_frame import FPVFrameSpec
from cad.modules.fpv_frame_solid import FPVFrameSolidSpec, export_fpv_frame_step
from cad.modules.propeller import PropellerSpec
from cad.modules.service import export_fpv_layout_dxf, export_propeller_planform_dxf
from build123d import Align, Box, Cylinder, Pos, export_step, export_stl
from cad.sketch_photo.feature_detection import detect_sketch_features
from cad.sketch_photo.dimension_parser import parse_dimension_text
import ezdxf

app = FastAPI(title="MyAI Assistant CAD API", version="0.1.0")


class PlateParameters(BaseModel):
    length_mm: float = Field(default=100, gt=20, le=500)
    width_mm: float = Field(default=60, gt=20, le=300)
    thickness_mm: float = Field(default=5, gt=1, le=30)
    hole_diameter_mm: float = Field(default=5, gt=1, le=20)
    hole_inset_mm: float = Field(default=10, gt=2, le=100)


class FPVFrameRequest(BaseModel):
    wheelbase_mm: float = Field(default=315, gt=100, le=500)
    arm_width_mm: float = Field(default=18, gt=1, le=30)
    arm_thickness_mm: float = Field(default=5, gt=1, le=30)
    top_plate_length_mm: float = Field(default=160, gt=20, le=300)
    plate_width_mm: float = Field(default=75, gt=20, le=200)
    plate_thickness_mm: float = Field(default=2, gt=0.5, le=10)
    motor_mount_spacing_mm: float = Field(default=19, gt=5, le=40)
    motor_hole_diameter_mm: float = Field(default=3.2, gt=1, le=8)
    standoff_height_mm: float = Field(default=25, gt=5, le=80)
    camera_angle_deg: float = Field(default=30, ge=0, le=60)


class PropellerRequest(BaseModel):
    diameter_in: float = Field(default=7, gt=1, le=20)
    blade_count: int = Field(default=2, ge=2, le=2)
    bore_diameter_mm: float = Field(default=5, gt=1, le=15)
    hub_diameter_mm: float = Field(default=16, gt=6, le=40)
    hub_thickness_mm: float = Field(default=7, gt=2, le=20)
    root_chord_mm: float = Field(default=18, gt=3, le=50)
    tip_chord_mm: float = Field(default=8, gt=2, le=30)
    sweep_mm: float = Field(default=8, ge=0, le=30)


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


@app.post("/cad/fpv-frame/spec")
def fpv_frame_spec(p: FPVFrameRequest):
    spec = FPVFrameSpec(**p.model_dump())
    try:
        return spec.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/cad/fpv-frame/step")
def fpv_frame_step(p: FPVFrameRequest):
    """Export the first-pass multi-part Classic-X assembly as STEP."""
    frame = FPVFrameSpec(**p.model_dump())
    try:
        with TemporaryDirectory() as temp:
            out = export_fpv_frame_step(Path(temp) / "fpv_7in_classic_x.step",
                                        frame, FPVFrameSolidSpec())
            payload = out.read_bytes()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return Response(content=payload, media_type="application/step",
                    headers={"Content-Disposition": 'attachment; filename="fpv_7in_classic_x.step"'})


@app.post("/cad/propeller/spec")
def propeller_spec(p: PropellerRequest):
    spec = PropellerSpec(**p.model_dump())
    try:
        return spec.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/cad/fpv-frame/dxf")
def fpv_frame_dxf(p: FPVFrameRequest):
    spec = FPVFrameSpec(**p.model_dump())
    try:
        with TemporaryDirectory() as temp:
            out = export_fpv_layout_dxf(Path(temp) / "fpv_frame_layout.dxf", spec)
            payload = out.read_bytes()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return Response(content=payload, media_type="application/dxf",
                    headers={"Content-Disposition": 'attachment; filename="fpv_frame_layout.dxf"'})


@app.post("/cad/propeller/dxf")
def propeller_dxf(p: PropellerRequest):
    spec = PropellerSpec(**p.model_dump())
    try:
        with TemporaryDirectory() as temp:
            out = export_propeller_planform_dxf(Path(temp) / "propeller_planform.dxf", spec)
            payload = out.read_bytes()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return Response(content=payload, media_type="application/dxf",
                    headers={"Content-Disposition": 'attachment; filename="propeller_planform.dxf"'})


@app.post("/cad/sketch/parse-dimensions")
def parse_sketch_dimensions(
    ocr_text: str = Form(...),
    default_unit: str = Form(default="mm"),
):
    """Parse OCR text supplied by a recognition provider into reviewable dimensions."""
    try:
        dimensions = parse_dimension_text(ocr_text, default_unit)
        return {
            "dimensions": [item.to_dict() for item in dimensions],
            "requires_user_confirmation": True,
            "ocr_performed": False,
        }
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/cad/sketch/analyze")
async def analyze_sketch_image(
    file: UploadFile = File(...),
    threshold: int = Form(default=48, ge=1, le=254),
    source_kind: str = Form(default="sketch"),
):
    """Analyze a sketch/photo raster and return image-space edge observations."""
    if source_kind not in {"sketch", "photo"}:
        raise HTTPException(status_code=422, detail="source_kind must be 'sketch' or 'photo'")
    try:
        payload = await file.read()
        observation = detect_sketch_features(payload, threshold, source_kind)
        return observation.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        await file.close()
