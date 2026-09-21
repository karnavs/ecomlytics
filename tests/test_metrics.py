import csv
from pathlib import Path

from analytics.metrics import (
    overview,
    product_metrics,
    period_comparison,
    read_csv,
)

DATA = Path(__file__).resolve().parents[1] / "data"


def _row_count(name):
    with open(DATA / name, newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.DictReader(f))


def test_overview_matches_dataset():
    o = overview()
    completed = [r for r in read_csv("orders.csv") if r.get("status", "").lower() == "completed"]
    assert o["orders"] == len(completed)
    assert o["customers"] == _row_count("customers.csv")
    assert o["products"] == _row_count("products.csv")
    assert o["revenue"] >= 0
    if o["orders"]:
        assert round(o["revenue"] / o["orders"], 2) == round(o["aov"], 2)


def test_products_row_count_matches_csv():
    products = product_metrics()
    assert len(products) == _row_count("products.csv")
    for p in products:
        assert p["revenue"] >= 0
        assert 0 <= p["return_rate"] <= 100


def test_zero_denominator_never_fabricated():
    for p in product_metrics():
        if p["views"] == 0:
            assert p["conversion"] == 0


def test_period_comparison_shape():
    orders = read_csv("orders.csv")
    result = period_comparison(orders, days=30)
    assert result["period_days"] == 30
    for key in ("revenue", "orders", "aov", "repeat_rate"):
        m = result["metrics"][key]
        assert "value" in m and "change_pct" in m


def test_period_comparison_handles_no_data():
    result = period_comparison([], days=30)
    assert "note" in result
