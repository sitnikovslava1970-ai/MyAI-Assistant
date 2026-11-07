import pytest

from cad.sketch_photo.dimension_parser import parse_dimension_text


def test_parses_diameter_radius_thread_and_linear_dimensions():
    parsed = parse_dimension_text("Ø12 mm R5 M3 25.5 mm")
    assert [(item.kind, item.value_mm) for item in parsed] == [
        ("diameter", 12), ("radius", 5), ("thread", 3), ("linear", 25.5)
    ]


def test_parses_quantity_and_ocr_multiplication_symbols():
    parsed = parse_dimension_text("4x Ø3,2")
    assert len(parsed) == 1
    assert parsed[0].count == 4
    assert parsed[0].kind == "diameter"
    assert parsed[0].value_mm == pytest.approx(3.2)


def test_converts_inches_and_centimetres_to_mm():
    parsed = parse_dimension_text('1.5 in 2 cm')
    assert [item.value_mm for item in parsed] == [38.1, 20.0]
    assert all(item.unit_source == "explicit" for item in parsed)


def test_plain_bare_numbers_are_not_mistaken_for_dimensions():
    assert parse_dimension_text("Detail 2, view 3, page 10") == ()


def test_marks_symbol_dimensions_without_units_as_assumed_units():
    parsed = parse_dimension_text("Ø10", default_unit="mm")
    assert parsed[0].value_mm == 10
    assert parsed[0].confidence == "medium"
    assert parsed[0].requires_confirmation is True
    assert parsed[0].unit_source == "document_default"


def test_rejects_invalid_default_unit_and_non_text_input():
    with pytest.raises(ValueError):
        parse_dimension_text("Ø10", default_unit="pixels")
    with pytest.raises(TypeError):
        parse_dimension_text(None)


def test_dimension_parser_api_returns_reviewable_dimensions():
    from fastapi.testclient import TestClient
    from cad.api.main import app

    response = TestClient(app).post(
        "/cad/sketch/parse-dimensions",
        data={"ocr_text": "4x Ø3.2 mm, R5 mm", "default_unit": "mm"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ocr_performed"] is False
    assert payload["requires_user_confirmation"] is True
    assert [item["kind"] for item in payload["dimensions"]] == ["diameter", "radius"]
    assert payload["dimensions"][0]["count"] == 4


def test_dimension_parser_api_rejects_unknown_units():
    from fastapi.testclient import TestClient
    from cad.api.main import app

    response = TestClient(app).post(
        "/cad/sketch/parse-dimensions",
        data={"ocr_text": "Ø10", "default_unit": "pixels"},
    )
    assert response.status_code == 422
