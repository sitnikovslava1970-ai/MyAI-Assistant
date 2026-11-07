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
    unit_source: Literal["explicit", "document_default", "thread_designation"]
    requires_confirmation: bool = True
    pitch_mm: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


# Repeated-count dimensions, e.g. 4x Ø3.2 mm.
_DIMENSION_RE = re.compile(
    r"(?<![A-Za-z])(?P<count>\\d+)\\s*[xх×]\\s*"
    r"(?P<symbol>Ø|⌀|φ|Φ|DIA|R|M)?\\s*"
    r"(?P<value>\\d+(?:[.,]\\d+)?)\\s*"
    r"(?P<unit>mm|毫米|厘米|cm|inches|inch|in|мм|см|\")?",
    re.IGNORECASE,
)
# ISO metric thread callout with pitch, e.g. M3x0.5 or M6 x 1 mm.
_THREAD_PITCH_RE = re.compile(
    r"(?<![A-Za-z])M\\s*(?P<major>\\d+(?:[.,]\\d+)?)\\s*[x×]\\s*"
    r"(?P<pitch>\\d+(?:[.,]\\d+)?)(?:\\s*(?P<unit>mm|мм))?",
    re.IGNORECASE,
)
_SINGLE_RE = re.compile(
    r"(?<![A-Za-z])(?P<symbol>Ø|⌀|φ|Φ|DIA|R|M)\\s*"
    r"(?P<value>\\d+(?:[.,]\\d+)?)\\s*"
    r"(?P<unit>mm|毫米|厘米|cm|inches|inch|in|мм|см|\")?"
    r"|(?<![A-Za-z])(?P<plain>\\d+(?:[.,]\\d+)?)\\s*"
    r"(?P<plain_unit>mm|毫米|厘米|cm|inches|inch|in|мм|см|\")",
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

    Explicit diameter/radius symbols may omit units. ISO M-thread callouts are
    metric by definition. Plain values need an explicit unit to avoid treating
    drawing labels as dimensions.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not isinstance(default_unit, str) or default_unit.lower() not in {"mm", "cm", "in"}:
        raise ValueError("default_unit must be 'mm', 'cm', or 'in'")

    normalized = text.replace("⌀", "Ø")
    results: list[ParsedDimension] = []
    occupied: list[tuple[int, int]] = []

    # Parse metric thread pitch before repeated-count patterns so M3x0.5
    # cannot be misread as a quantity of three 0.5-unit features.
    for match in _THREAD_PITCH_RE.finditer(normalized):
        results.append(ParsedDimension(
            kind="thread", value_mm=round(float(match.group("major").replace(",", ".")), 4),
            count=1, source_text=match.group(0), confidence="high",
            unit_source="thread_designation",
            pitch_mm=round(float(match.group("pitch").replace(",", ".")), 4),
        ))
        occupied.append(match.span())

    for match in _DIMENSION_RE.finditer(normalized):
        if any(start <= match.start() < end for start, end in occupied):
            continue
        symbol = (match.group("symbol") or "").upper()
        unit = match.group("unit")
        if symbol == "M" and unit is None:
            factor, explicit = 1.0, True
            unit_source = "thread_designation"
        else:
            factor, explicit = _unit_factor(unit, default_unit)
            unit_source = "explicit" if explicit else "document_default"
        value = float(match.group("value").replace(",", ".")) * factor
        kind = "diameter" if symbol in {"Ø", "Φ", "DIA"} else (
            "radius" if symbol == "R" else "thread" if symbol == "M" else "linear"
        )
        results.append(ParsedDimension(
            kind=kind, value_mm=round(value, 4), count=int(match.group("count")),
            source_text=match.group(0), confidence="high" if explicit else "medium",
            unit_source=unit_source,
        ))
        occupied.append(match.span())

    for match in _SINGLE_RE.finditer(normalized):
        if any(start <= match.start() < end for start, end in occupied):
            continue
        symbol = (match.group("symbol") or "").upper()
        value_text = match.group("value") or match.group("plain")
        unit = match.group("unit") or match.group("plain_unit")
        if symbol == "M" and unit is None:
            factor, explicit = 1.0, True
            unit_source = "thread_designation"
        else:
            factor, explicit = _unit_factor(unit, default_unit)
            unit_source = "explicit" if explicit else "document_default"
        kind = "diameter" if symbol in {"Ø", "Φ", "DIA"} else (
            "radius" if symbol == "R" else "thread" if symbol == "M" else "linear"
        )
        results.append(ParsedDimension(
            kind=kind, value_mm=round(float(value_text.replace(",", ".")) * factor, 4),
            count=1, source_text=match.group(0),
            confidence="high" if explicit else "medium", unit_source=unit_source,
        ))
        occupied.append(match.span())

    return tuple(sorted(results, key=lambda item: normalized.find(item.source_text)))
