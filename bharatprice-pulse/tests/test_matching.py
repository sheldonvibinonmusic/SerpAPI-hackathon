"""
test_matching.py — BharatPrice Pulse
Tests for product matching, outlier stripping, bundle exclusion, and comparability.
"""
from datetime import datetime
from app.models.evidence_models import ShoppingItem, EvidenceSource
from app.models.request_models import AnalysisRequest
from app.processing.query_normalizer import normalize_request
from app.processing.product_matcher import match_and_filter_products
from app.utils.datetime_utils import utc_now


def test_product_matcher_filters_bulk_and_bundles():
    req = AnalysisRequest(
        product_raw="Fortune Mustard Oil 1L",
        city_raw="Jaipur",
        selling_price=175.0,
    )
    norm = normalize_request(req)

    now = utc_now()
    raw_items = [
        # Valid 1L items
        ShoppingItem(evidence_id="1", source=EvidenceSource.GOOGLE_SHOPPING, retrieved_at=now,
                     title="Fortune Kachi Ghani Mustard Oil 1L Pouch", price_inr=158.0),
        ShoppingItem(evidence_id="2", source=EvidenceSource.GOOGLE_SHOPPING, retrieved_at=now,
                     title="Fortune Pure Mustard Oil 1 Litre Bottle", price_inr=165.0),
        ShoppingItem(evidence_id="3", source=EvidenceSource.GOOGLE_SHOPPING, retrieved_at=now,
                     title="Fortune Mustard Oil 1L", price_inr=155.0),
        # 15L commercial tin -> should be filtered
        ShoppingItem(evidence_id="4", source=EvidenceSource.GOOGLE_SHOPPING, retrieved_at=now,
                     title="Fortune Mustard Oil 15L Commercial Tin", price_inr=2200.0),
        # Pack of 3 bundle -> should be filtered
        ShoppingItem(evidence_id="5", source=EvidenceSource.GOOGLE_SHOPPING, retrieved_at=now,
                     title="Fortune Mustard Oil 1L Pack of 3", price_inr=470.0),
        # Unrelated brand
        ShoppingItem(evidence_id="6", source=EvidenceSource.GOOGLE_SHOPPING, retrieved_at=now,
                     title="Dhara Mustard Oil 1L", price_inr=160.0),
    ]

    comparable, excluded = match_and_filter_products(raw_items, norm)

    # All three 1L Fortune items should be kept
    comp_ids = [item.evidence_id for item in comparable]
    assert "1" in comp_ids
    assert "2" in comp_ids
    assert "3" in comp_ids

    # 15L tin and pack of 3 should be in excluded
    excl_ids = [item.evidence_id for item in excluded]
    assert "4" in excl_ids
    assert "5" in excl_ids
    assert "6" in excl_ids


def test_electronics_matcher_filters_cases():
    req = AnalysisRequest(
        product_raw="Samsung Galaxy M14 5G",
        city_raw="Delhi",
        selling_price=12999.0,
    )
    norm = normalize_request(req)
    now = utc_now()

    raw_items = [
        ShoppingItem(evidence_id="1", source=EvidenceSource.GOOGLE_SHOPPING, retrieved_at=now,
                     title="Samsung Galaxy M14 5G (6GB, 128GB)", price_inr=12499.0),
        ShoppingItem(evidence_id="2", source=EvidenceSource.GOOGLE_SHOPPING, retrieved_at=now,
                     title="Samsung Galaxy M14 5G Smartphone", price_inr=12999.0),
        # Case accessory
        ShoppingItem(evidence_id="3", source=EvidenceSource.GOOGLE_SHOPPING, retrieved_at=now,
                     title="Shockproof Protective Back Case for Samsung Galaxy M14 5G", price_inr=299.0),
    ]

    comparable, excluded = match_and_filter_products(raw_items, norm)
    comp_ids = [item.evidence_id for item in comparable]
    assert "1" in comp_ids
    assert "2" in comp_ids
    assert "3" not in comp_ids
