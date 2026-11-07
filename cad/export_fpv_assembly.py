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
    camera_side_foot_centers,
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
        if part_name.startswith("REF_"):
            continue
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
    items.extend([
        AssemblyItem("CAMERA_BASE_PLATE", "DJI O4 Pro camera base plate", 1, "2 mm carbon fiber provisional", frame.plate_thickness_mm),
        AssemblyItem("CAMERA_SIDE_LEFT", "DJI O4 Pro left adjustable side plate", 1, "2 mm carbon fiber provisional", solid.camera_side_plate_thickness_mm),
        AssemblyItem("CAMERA_SIDE_RIGHT", "DJI O4 Pro right adjustable side plate", 1, "2 mm carbon fiber provisional", solid.camera_side_plate_thickness_mm),
        AssemblyItem("CAMERA_SUPPORT_LEFT", "Left angled camera support bracket", 1, "PA12-CF or 6061 aluminium; material to validate"),
        AssemblyItem("CAMERA_SUPPORT_RIGHT", "Right angled camera support bracket", 1, "PA12-CF or 6061 aluminium; material to validate"),
        AssemblyItem("ARM_ROOT_M3", "Arm-root M3 fastener", 16, "steel; length to confirm"),
        AssemblyItem("MOTOR_M3", "Motor M3 fastener", 16, "steel; length to confirm"),
        AssemblyItem("CAMERA_BASE_M3", "Camera base M3 fastener", 2, "steel; length to confirm"),
        AssemblyItem("CAMERA_SUPPORT_M3", "Camera support-to-base M3 fastener", 4, "steel; length to confirm"),
        AssemblyItem("CAMERA_M2", "DJI O4 Pro camera M2 fastener", 4, "steel; length to confirm"),
        AssemblyItem("AIR_UNIT_M2", "DJI O4 Pro air-unit M2 fastener", 4, "steel; length to confirm"),
        AssemblyItem("BATTERY_STRAP", "Battery strap", 2, "webbing; length to confirm"),
    ])

    manifest = {
        "project": "FPV_7in_ClassicX_LongRange_R01",
        "units": "mm",
        "model_status": "first-pass geometric prototype",
        "frame_parameters": frame.to_dict(),
        "solid_parameters": {
            key: value for key, value in solid.__dict__.items()
        },
        "components": bill_of_materials(items),
        "generated_parts": sorted(name for name in parts if not name.startswith("REF_")),
        "reference_geometry": [
            {"part_id": "REF_CAMERA_O4_PRO", "description": "DJI O4 Air Unit Pro camera envelope; visual reference only"},
            {"part_id": "REF_AIR_UNIT_O4_PRO", "description": "DJI O4 Air Unit Pro transmission module envelope below the lower plate; visual reference only"},
        ],
        "air_unit_mount": {
            "mounting_face": "underside of lower center plate",
            "hole_spacing_mm": solid.air_unit_mount_spacing_mm,
            "hole_diameter_mm": solid.air_unit_hole_diameter_mm,
            "module_envelope_mm": [33.5, 33.5, 13.0],
            "center_y_mm": solid.air_unit_center_y_mm,
            "note": "Reference envelope only; verify antenna routing, heat transfer and clearance to the rear arms."
        },
        "camera_mount": {
            "nominal_angle_deg": frame.camera_angle_deg,
            "camera_envelope_mm": [solid.camera_module_width_mm, solid.camera_module_depth_mm, solid.camera_module_height_mm],
            "side_plate_thickness_mm": solid.camera_side_plate_thickness_mm,
            "adjustment_slot_length_mm": solid.camera_mount_slot_length_mm,
            "side_panels_are_separate_flat_parts": True,
            "support_brackets": ["CAMERA_SUPPORT_LEFT", "CAMERA_SUPPORT_RIGHT"],
            "note": "Side panels are separate 2 mm carbon parts; angled support brackets are separate 3D parts. Verify actual camera screw positions and physical fit."
        },
        "camera_support_mount": {
            "support_foot_hole_centers_mm": [
                [x, y] for x, y in camera_side_foot_centers(solid)
            ],
            "fastener_count": 4,
            "foot_thickness_mm": solid.camera_support_foot_thickness_mm,
            "foot_width_mm": solid.camera_support_foot_width_mm,
            "foot_length_mm": solid.camera_support_foot_length_mm,
            "material": "PA12-CF or 6061 aluminium; requires strength and fit validation",
        },
        "battery_strap_slots": {
            "count": 2,
            "center_coordinates_mm": [[-solid.battery_strap_slot_center_x_mm, 0.0], [solid.battery_strap_slot_center_x_mm, 0.0]],
            "overall_length_mm": solid.battery_strap_slot_length_mm,
            "width_mm": solid.battery_strap_slot_width_mm,
        },
        "generated_files": [
            "FPV_7in_ClassicX_Assembly.step",
            "FPV_7in_ClassicX_Assembly.stl",
            "dxf/FPV_7in_ClassicX_CAMERA_SIDE_LEFT.dxf",
            "dxf/FPV_7in_ClassicX_CAMERA_SIDE_RIGHT.dxf",
        ],
        "not_yet_modeled_or_verified": [
            "Physical fit and exact screw positions of the DJI O4 Pro camera against the side-plate slots",
            "Actual battery dimensions, strap path and battery-to-camera clearance",
            "FC/ESC stack hardware, stack height and exact stack orientation",
            "Air-unit antenna mounts and DJI-recommended 50 mm separation from carbon and other components",
            "M2/M3 fastener lengths, washers, nuts, thread engagement and tool access",
            "Camera support bracket material, local strength and attachment stiffness",
            "Carbon laminate edge distances, countersinks and CNC cutter compensation",
            "Arm-root, camera-bracket and motor-mount structural strength",
            "Cooling airflow for the DJI O4 Pro transmission module",
            "Vibration, fatigue, resonance and flight validation",
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
