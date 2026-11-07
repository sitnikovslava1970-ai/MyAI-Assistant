"""Parse OCR text from engineering drawings into reviewable dimensions.

This module deliberately parses text only: it does not perform OCR and never
silently treats a parsed value as a manufacturing-approved measurement.
"""
from dataclasses import asdict, dataclass
import re
from typing import Literal


@dataclass(frozen=True)
class ParsedDimension:
    kind: Literal["linear", "diameter", "radius", "thread"]
    value_mm: float
    count: int
    source_text: str
    confidence: Literal["low", "medium", "high"]
    unit_source: Literal["explicit", "document_default"]
    requires_confirmation: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


# Supports common OCR substitutions and both decimal separators.
_DIMENSION_RE = re.compile(
    r"(?P<count>\d+)\s*[xх×]\s*"
    r"(?P<symbol>Ø|⌀|φ|Φ|DIA|R|M)?\s*"
    r"(?P<value>\d+(?:[.,]\d+)?)\s*"
    r"(?P<unit>mm|毫米|厘米|cm|inches|inch|in|мм|см|")?",
    re.IGNORECASE,
)
_SINGLE_RE = re.compile(
    r"(?P<symbol>Ø|⌀|φ|Φ|DIA|R|M)\s*"
    r"(?P<value>\d+(?:[.,]\d+)?)\s*"
    r"(?P<unit>mm|毫米|厘米|cm|inches|inch|in|мм|см|")?"
    r"|(?P<plain>\d+(?:[.,]\d+)?)\s*"
    r"(?P<plain_unit>mm|毫米|厘米|cm|inches|inch|in|мм|см|")",
    re.IGNORECASE,
)


def _unit_factor(unit: str | None, default_unit: str) -> tuple[float, bool]:
    normalized = (unit or default_unit).strip().lower()
    if normalized in {"in", "inch", "inches", '"'}:
        return 25.4, unit is not None
    if normalized in {"cm", "см", "厘米"}:
        return 10.0, unit is not None
    if normalized in {"mm", "мм", "毫米"}:
        return 1.0, unit is not None
    raise ValueError("default_unit must be 'mm', 'cm', or 'in'")


def parse_dimension_text(text: str, default_unit: str = "mm") -> tuple[ParsedDimension, ...]:
    """Extract dimensions from OCR text; bare numbers are not accepted.

    Explicit diameter/radius/thread symbols may omit units. Plain values need
    an explicit unit to avoid interpreting drawing labels as dimensions.
    """
    if default_unit.lower() not in {"mm", "cm", "in"}:
        raise ValueError("default_unit must be 'mm', 'cm', or 'in'")
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    normalized = text.replace(",", ".").replace("⌀", "Ø")
    results: list[ParsedDimension] = []
    occupied: list[tuple[int, int]] = []

    for match in _DIMENSION_RE.finditer(normalized):
        symbol = (match.group("symbol") or "").upper()
        unit = match.group("unit")
        factor, explicit = _unit_factor(unit, default_unit)
        value = float(match.group("value")) * factor
        kind = "diameter" if symbol in {"Ø", "Φ", "DIA"} else (
            "radius" if symbol == "R" else "thread" if symbol == "M" else "linear"
        )
        results.append(ParsedDimension(
            kind=kind, value_mm=round(value, 4), count=int(match.group("count")),
            source_text=match.group(0), confidence="high" if explicit else "medium",
            unit_source="explicit" if explicit else "document_default",
        ))
        occupied.append(match.span())

    for match in _SINGLE_RE.finditer(normalized):
        if any(start <= match.start() < end for start, end in occupied):
            continue
        symbol = (match.group("symbol") or "").upper()
        value_text = match.group("value") or match.group("plain")
        unit = match.group("unit") or match.group("plain_unit")
        factor, explicit = _unit_factor(unit, default_unit)
        kind = "diameter" if symbol in {"Ø", "Φ", "DIA"} else (
            "radius" if symbol == "R" else "thread" if symbol == "M" else "linear"
        )
        results.append(ParsedDimension(
            kind=kind, value_mm=round(float(value_text) * factor, 4), count=1,
            source_text=match.group(0), confidence="high" if explicit else "medium",
            unit_source="explicit" if explicit else "document_default",
        ))
        occupied.append(match.span())

    return tuple(sorted(results, key=lambda item: normalized.find(item.source_text)))
