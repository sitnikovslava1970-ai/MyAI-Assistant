"""Export preliminary 2D DXF profiles for the flat carbon parts of the FPV frame.

Run from the repository root:
    python -m cad.export_fpv_dxf --output-dir build/fpv_7in_classic_x/dxf

These files are profile exports for engineering review, not CNC release files.
No cutter compensation, laminate allowance or production approval is applied.
"""
from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import ezdxf
from build123d import Axis
from build123d.exporters import ExportDXF

from cad.modules.fpv_frame import FPVFrameSpec
from cad.modules.fpv_frame_solid import FPVFrameSolidSpec, build_fpv_frame_parts


def export_dxf_package(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = FPVFrameSpec()
    solid = FPVFrameSolidSpec()
    parts = build_fpv_frame_parts(frame, solid)

    flat_parts = {
        "PLATE_BOTTOM": ("Lower center plate", frame.plate_thickness_mm, "carbon fiber"),
        "PLATE_TOP": ("Upper center plate", frame.plate_thickness_mm, "carbon fiber"),
        "ARM_FRONT_LEFT": ("Front-left replaceable arm", frame.arm_thickness_mm, "carbon fiber"),
        "ARM_FRONT_RIGHT": ("Front-right replaceable arm", frame.arm_thickness_mm, "carbon fiber"),
        "ARM_REAR_LEFT": ("Rear-left replaceable arm", frame.arm_thickness_mm, "carbon fiber"),
        "ARM_REAR_RIGHT": ("Rear-right replaceable arm", frame.arm_thickness_mm, "carbon fiber"),
        "CAMERA_BASE_PLATE": ("DJI O4 Pro camera base plate", frame.plate_thickness_mm, "carbon fiber; provisional"),
    }

    generated = []
    for part_id, (description, thickness, material) in flat_parts.items():
        part = parts[part_id]
        planar_faces = part.faces().filter_by(Axis.Z).sort_by(Axis.Z)
        if not planar_faces:
            raise RuntimeError(f"No horizontal planar face found for {part_id}")
        top_face = planar_faces[-1]
        outer = top_face.outer_wire()
        inner = top_face.inner_wires()
        if not outer.is_closed:
            raise RuntimeError(f"Open outer profile in {part_id}")
        if any(not wire.is_closed for wire in inner):
            raise RuntimeError(f"Open internal profile in {part_id}")

        exporter = ExportDXF()
        exporter.add_layer("OUTLINE", color="black", line_weight=0.25)
        exporter.add_layer("HOLES", color="blue", line_weight=0.18)
        exporter.add_layer("NOTES", color="gray", line_weight=0.13)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Exporting non-planar shape to 2D format")
            exporter.add_shape(outer, layer="OUTLINE")
            if inner:
                exporter.add_shape(inner, layer="HOLES")

        file_name = f"FPV_7in_ClassicX_{part_id}.dxf"
        file_path = output_dir / file_name
        exporter.write(str(file_path))

        doc = ezdxf.readfile(file_path)
        doc.header["$INSUNITS"] = ezdxf.units.MM
        msp = doc.modelspace()
        bounds = part.bounding_box()
        msp.add_text(
            f"PRELIMINARY - {part_id} - {thickness:g} mm - NOT CNC RELEASE",
            height=2.0,
            dxfattribs={"layer": "NOTES"},
        ).set_placement((bounds.max.X + 6.0, bounds.max.Y + 6.0))
        doc.saveas(file_path)

        check_doc = ezdxf.readfile(file_path)
        check_entities = list(check_doc.modelspace())
        if not any(entity.dxf.layer == "OUTLINE" for entity in check_entities):
            raise RuntimeError(f"DXF outline layer is empty for {part_id}")
        if not any(entity.dxf.layer == "HOLES" for entity in check_entities):
            raise RuntimeError(f"DXF hole layer is empty for {part_id}")

        generated.append({
            "part_id": part_id,
            "description": description,
            "file": file_name,
            "material": material,
            "thickness_mm": thickness,
            "outer_wire_closed": bool(outer.is_closed),
            "inner_wire_count": len(inner),
            "entity_count": len(check_entities),
            "units": "mm",
        })

    manifest = {
        "project": "FPV_7in_ClassicX_LongRange_R01",
        "package_status": "preliminary 2D profile export",
        "coordinate_convention": {
            "plate_x_dimension_mm": frame.top_plate_length_mm,
            "plate_y_dimension_mm": frame.plate_width_mm,
            "camera_front_direction": "+Y",
            "note": "Current model places the 160 mm plate dimension across X and 75 mm along Y. Confirm before production release.",
        },
        "generated_parts": generated,
        "excluded_parts": [
            {
                "part_id": "CAMERA_SIDE_LEFT / CAMERA_SIDE_RIGHT",
                "reason": "Current solids combine vertical carbon side plates with horizontal feet and support webs; not a verified flat 2D cut profile.",
            },
            {
                "part_id": "STANDOFF_1..4",
                "reason": "Cylindrical hardware, not a flat carbon cut part.",
            },
        ],
        "manufacturing_limitations": [
            "No cutter compensation or kerf offset",
            "No laminate-specific edge-distance approval",
            "No countersink, chamfer or fastener-length approval",
            "Camera side plates are excluded pending a planar bracket redesign",
            "Coordinate convention must be confirmed before production",
            "Profiles are not approved for CNC manufacture or flight",
        ],
    }
    (output_dir / "dxf_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    (output_dir / "README_DXF_PRELIMINARY.md").write_text(
        "# FPV 7-inch Classic-X — preliminary DXF profiles\n\n"
        "All files use millimetres. Layers: OUTLINE, HOLES, NOTES. "
        "The seven exported parts are the two center plates, four arms and camera base plate.\n\n"
        "**Not a CNC release.** Cutter compensation is not applied. The camera side plates "
        "are excluded because their current 3D solids are not flat cut profiles. The 160 x 75 mm "
        "plate orientation is still a model assumption and must be confirmed.\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("build/fpv_7in_classic_x/dxf"))
    args = parser.parse_args()
    manifest = export_dxf_package(args.output_dir)
    print(f"Generated {len(manifest['generated_parts'])} preliminary DXF profiles.")
    print(f"Package: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
