import pytest
from app.pdf.generator import generate_fdf, format_amount


def test_generate_fdf_structure():
    fdf = generate_fdf({"field1": "value1", "field2": "value2"})
    assert "%FDF-1.2" in fdf
    assert "field1" in fdf
    assert "value1" in fdf
    assert "%%EOF" in fdf


def test_format_amount_positive():
    assert format_amount(100000) == "100,000"


def test_format_amount_negative():
    assert format_amount(-50000) == "(50,000)"


def test_format_amount_zero():
    assert format_amount(0) == "0"


def test_fdf_escapes_parentheses():
    fdf = generate_fdf({"field": "value (with parens)"})
    assert "value \\(with parens\\)" in fdf
