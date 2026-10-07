"""
test_normalizer.py — BharatPrice Pulse
Tests for query normalization, brand extraction, unit detection, and canonicalization.
"""
from app.models.request_models import AnalysisRequest, ProductCategory
from app.processing.query_normalizer import normalize_request, build_cache_key


def test_mustard_oil_normalization():
    req = AnalysisRequest(
        product_raw="Fortune Mustard Oil 1L",
        city_raw="Jaipur",
        selling_price=175.0,
    )
    norm = normalize_request(req)
    assert norm.brand == "Fortune"
    assert norm.quantity == 1.0
    assert norm.base_unit == "L"
    assert norm.city == "Jaipur"
    assert norm.category == ProductCategory.EDIBLE_OIL_FMCG
    assert "Fortune" in norm.search_query


def test_unit_conversion_in_normalizer():
    req = AnalysisRequest(
        product_raw="Dhara Kachi Ghani Mustard Oil 1000ml",
        city_raw="delhi",
        selling_price=160.0,
    )
    norm = normalize_request(req)
    # 1000ml should normalize to 1.0 L
    assert norm.quantity == 1.0
    assert norm.base_unit == "L"
    assert norm.city == "Delhi"


def test_rice_staple_normalization():
    req = AnalysisRequest(
        product_raw="India Gate Basmati Rice 5kg",
        city_raw="Mumbai",
        selling_price=520.0,
    )
    norm = normalize_request(req)
    assert norm.brand == "India Gate"
    assert norm.quantity == 5.0
    assert norm.base_unit == "kg"
    assert norm.category == ProductCategory.PACKAGED_STAPLES


def test_deterministic_cache_key():
    k1 = build_cache_key("google", "fortune mustard oil 1l", "jaipur", "en")
    k2 = build_cache_key("google", "fortune mustard oil 1l", "jaipur", "en")
    k3 = build_cache_key("google", "fortune mustard oil 1l", "delhi", "en")
    assert k1 == k2
    assert k1 != k3
