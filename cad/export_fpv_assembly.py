"""Build a reviewable STEP/STL package for the first-pass 7-inch Classic-X assembly.

Run from the repository root:
    python -m cad.export_fpv_assembly --output-dir build/fpv_7in_classic_x

This is a geometric prototype, not a CNC release or flight-certified design.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build123d import Compound, export_step, export_stl

from cad.modules.assembly import AssemblyItem, bill_of_materials
from cad.modules.fpv_frame import FPVFrameSpec
from cad.modules.fpv_frame_solid import (
    FPVFrameSolidSpec,
    build_fpv_frame_parts,
)


def build_package(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = FPVFrameSpec()
    solid = FPVFrameSolidSpec()
    frame.validate()
    solid.validate(frame)

    parts = build_fpv_frame_parts(frame, solid)
    assembly = Compound(children=list(parts.values()))

    export_step(assembly, str(output_dir / "FPV_7in_ClassicX_Assembly.step"))
    export_stl(
        assembly,
        str(output_dir / "FPV_7in_ClassicX_Assembly.stl"),
        tolerance=0.05,
        angular_tolerance=0.1,
    )

    for part_name, shape in parts.items():
        export_step(shape, str(output_dir / f"{part_name}.step"))
        export_stl(
            shape,
            str(output_dir / f"{part_name}.stl"),
            tolerance=0.05,
            angular_tolerance=0.1,
        )

    items = [
        AssemblyItem("PLATE_BOTTOM", "Lower center plate", 1, "material to confirm", frame.plate_thickness_mm),
        AssemblyItem("PLATE_TOP", "Upper center plate", 1, "material to confirm", frame.plate_thickness_mm),
    ]
    for name in ("FRONT_LEFT", "FRONT_RIGHT", "REAR_LEFT", "REAR_RIGHT"):
        items.append(
            AssemblyItem(f"ARM_{name}", f"Replaceable arm {name.lower().replace('_', ' ')}", 1,
                         "material to confirm", frame.arm_thickness_mm)
        )
    for index in range(1, 5):
        items.append(AssemblyItem(f"STANDOFF_{index}", f"Standoff {index}", 1, "material to confirm"))

    manifest = {
        "project": "FPV_7in_ClassicX_LongRange_R01",
        "units": "mm",
        "model_status": "first-pass geometric prototype",
        "frame_parameters": frame.to_dict(),
        "solid_parameters": {
            key: value for key, value in solid.__dict__.items()
        },
        "components": bill_of_materials(items),
        "generated_parts": sorted(parts.keys()),
        "generated_files": [
            "FPV_7in_ClassicX_Assembly.step",
            "FPV_7in_ClassicX_Assembly.stl",
        ],
        "not_yet_modeled_or_verified": [
            "DJI O4 camera side plates and actual camera clearance",
            "battery strap slots and battery clearance",
            "FC/ESC stack hardware and exact stack orientation",
            "M3 fastener lengths, washers, nuts and tool access",
            "carbon laminate edge distances and CNC cutter compensation",
            "arm-root and motor-mount structural strength",
            "vibration, fatigue, resonance and flight validation",
        ],
        "manufacturing_warning": (
            "Prototype geometry only. Do not release for CNC manufacture or flight "
            "until component clearances, fasteners, laminate details and structural "
            "performance are independently checked."
        ),
    }
    manifest_path = output_dir / "assembly_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("build/fpv_7in_classic_x"),
    )
    args = parser.parse_args()
    manifest = build_package(args.output_dir)
    print(f"Generated {len(manifest['generated_parts'])} modeled components.")
    print(f"Package: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
