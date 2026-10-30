"""DXF export helpers for parametric outlines, in millimetres."""
from pathlib import Path
import ezdxf
from ezdxf.enums import TextEntityAlignment


def export_outline_dxf(path: str | Path, outlines: dict[str, list[tuple[float, float]]],
                       circles: list[tuple[float, float, float]] | None = None) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4
    for layer in outlines:
        if layer not in doc.layers:
            doc.layers.new(layer)
    if "HOLES" not in doc.layers:
        doc.layers.new("HOLES")
    if "NOTES" not in doc.layers:
        doc.layers.new("NOTES")
    msp = doc.modelspace()
    for layer, points in outlines.items():
        if len(points) < 3:
            raise ValueError(f"Outline {layer} must contain at least 3 points")
        msp.add_lwpolyline(points, close=True, dxfattribs={"layer": layer})
    for x, y, radius in circles or []:
        if radius <= 0:
            raise ValueError("Circle radius must be positive")
        msp.add_circle((x, y), radius, dxfattribs={"layer": "HOLES"})
    msp.add_text("UNITS: mm | VERIFY DIMENSIONS BEFORE MANUFACTURE",
                 height=2.5, dxfattribs={"layer": "NOTES"}).set_placement(
                     (0, -10), align=TextEntityAlignment.LEFT)
    doc.saveas(path)
    return path
