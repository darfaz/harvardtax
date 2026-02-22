import pytest
from app.allocation.k1_allocator import allocate_pro_rata


def test_equal_split_two_partners():
    totals = {"K-1": 100000, "K-5": 2000}
    partners = [
        {"id": "a", "name": "Alice", "ownership_pct": 50.0},
        {"id": "b", "name": "Bob", "ownership_pct": 50.0},
    ]
    result = allocate_pro_rata(totals, partners)
    assert len(result) == 2
    assert result[0]["allocations"]["K-1"] == 50000
    assert result[1]["allocations"]["K-5"] == 1000


def test_unequal_split():
    totals = {"K-1": 100000}
    partners = [
        {"id": "a", "name": "Alice", "ownership_pct": 70.0},
        {"id": "b", "name": "Bob", "ownership_pct": 30.0},
    ]
    result = allocate_pro_rata(totals, partners)
    assert result[0]["allocations"]["K-1"] == 70000
    assert result[1]["allocations"]["K-1"] == 30000


def test_three_way_split_with_rounding():
    totals = {"K-1": 100000}
    partners = [
        {"id": "a", "name": "A", "ownership_pct": 33.33},
        {"id": "b", "name": "B", "ownership_pct": 33.33},
        {"id": "c", "name": "C", "ownership_pct": 33.34},
    ]
    result = allocate_pro_rata(totals, partners)
    total_allocated = sum(r["allocations"]["K-1"] for r in result)
    assert total_allocated == 100000


def test_single_partner():
    totals = {"K-1": 50000, "K-5": 1000}
    partners = [{"id": "a", "name": "Solo", "ownership_pct": 100.0}]
    result = allocate_pro_rata(totals, partners)
    assert result[0]["allocations"]["K-1"] == 50000
    assert result[0]["allocations"]["K-5"] == 1000


def test_negative_income():
    totals = {"K-1": -25000}
    partners = [
        {"id": "a", "name": "A", "ownership_pct": 60.0},
        {"id": "b", "name": "B", "ownership_pct": 40.0},
    ]
    result = allocate_pro_rata(totals, partners)
    assert result[0]["allocations"]["K-1"] == -15000
    assert result[1]["allocations"]["K-1"] == -10000
