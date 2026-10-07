"""
test_units.py — BharatPrice Pulse
Tests for pure Python unit normalization, pack counts, and bulk lot detection.
"""
from app.processing.unit_normalizer import (
    normalize_to_base_unit,
    compute_unit_price,
    detect_unit_from_title,
    detect_pack_count,
    detect_is_bundle,
    detect_is_bulk_commercial,
    are_quantities_comparable,
)


def test_base_unit_conversion():
    assert normalize_to_base_unit(1000, "ml") == (1.0, "L")
    assert normalize_to_base_unit(500, "g") == (0.5, "kg")
    assert normalize_to_base_unit(5, "kg") == (5.0, "kg")
    assert normalize_to_base_unit(12, "pcs") == (12.0, "pcs")


def test_detect_unit_from_title():
    qty, unit = detect_unit_from_title("Fortune Kachi Ghani Mustard Oil 1L Pouch")
    assert qty == 1.0
    assert unit == "L"

    qty, unit = detect_unit_from_title("Dhara Mustard Oil 500ml")
    assert qty == 0.5
    assert unit == "L"

    qty, unit = detect_unit_from_title("India Gate Basmati Rice 5kg Bag")
    assert qty == 5.0
    assert unit == "kg"


def test_bundle_and_pack_detection():
    assert detect_pack_count("Fortune Mustard Oil Pack of 3") == 3
    assert detect_is_bundle("Fortune Mustard Oil Pack of 3") is True
    assert detect_is_bundle("Fortune Mustard Oil 1L") is False
    assert detect_pack_count("Dhara Mustard Oil 1L Bottle") == 1


def test_bulk_commercial_detection():
    # 15L commercial tin
    assert detect_is_bulk_commercial("Fortune Mustard Oil 15L Commercial Tin", 15.0, "L") is True
    # 1L consumer bottle
    assert detect_is_bulk_commercial("Fortune Mustard Oil 1L Pouch", 1.0, "L") is False
    # 50kg wholesale sack
    assert detect_is_bulk_commercial("Basmati Rice 50kg Sack", 50.0, "kg") is True


def test_quantity_comparability():
    # 1L vs 1L -> True
    assert are_quantities_comparable(1.0, "L", 1.0, "L") is True
    # 1L vs 2L -> False (outside 30% tolerance)
    assert are_quantities_comparable(1.0, "L", 2.0, "L") is False
    # 1L vs 500ml -> False
    assert are_quantities_comparable(1.0, "L", 0.5, "L") is False
    # 1L vs 1kg -> False (different unit families)
    assert are_quantities_comparable(1.0, "L", 1.0, "kg") is False


def test_unit_price_calculation():
    # ₹160 for 1L -> ₹160/L
    assert compute_unit_price(160.0, 1.0, "L") == 160.0
    # ₹85 for 500ml -> ₹170/L
    assert compute_unit_price(85.0, 500.0, "ml") == 170.0
    # ₹500 for 5kg -> ₹100/kg
    assert compute_unit_price(500.0, 5.0, "kg") == 100.0
