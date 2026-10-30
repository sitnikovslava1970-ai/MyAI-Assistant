"""Lightweight assembly manifest and bill-of-materials helpers."""
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class AssemblyItem:
    part_id: str
    name: str
    quantity: int
    material: str = "unspecified"
    thickness_mm: float | None = None

    def validate(self):
        if not self.part_id.strip() or not self.name.strip():
            raise ValueError("Part id and name are required")
        if self.quantity < 1:
            raise ValueError("Quantity must be at least 1")
        if self.thickness_mm is not None and self.thickness_mm <= 0:
            raise ValueError("Thickness must be positive")


def bill_of_materials(items: list[AssemblyItem]) -> list[dict]:
    seen = set()
    rows = []
    for item in items:
        item.validate()
        if item.part_id in seen:
            raise ValueError(f"Duplicate part_id: {item.part_id}")
        seen.add(item.part_id)
        rows.append(asdict(item))
    return rows
