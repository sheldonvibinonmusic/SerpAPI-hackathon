"""
test_pricing.py — BharatPrice Pulse
Tests for deterministic price distribution mathematics, IQR filtering, and margins.
"""
from datetime import datetime
from app.models.evidence_models import ShoppingItem, EvidenceSource
from app.models.decision_models import MarketPosition
from app.processing.price_calculator import compute_market_metrics, apply_iqr_filtering
from app.utils.datetime_utils import utc_now


def test_price_distribution_calculations():
    now = utc_now()
    # 5 test items with prices: 158, 162, 165, 170, 172
    prices = [158.0, 162.0, 165.0, 170.0, 172.0]
    items = [
        ShoppingItem(
            evidence_id=str(i),
            source=EvidenceSource.GOOGLE_SHOPPING,
            retrieved_at=now,
            title=f"Item {i}",
            price_inr=p,
        )
        for i, p in enumerate(prices)
    ]

    seller_price = 175.0
    landed_cost = 142.0

    metrics = compute_market_metrics(
        comparable_items=items,
        all_items=items,
        seller_price=seller_price,
        landed_cost=landed_cost,
        product_quantity=1.0,
        product_unit="L",
    )

    # Median of [158, 162, 165, 170, 172] is 165
    assert metrics.price_median == 165.0
    assert metrics.price_min == 158.0
    assert metrics.price_max == 172.0

    # Price gap: (175 - 165) / 165 * 100 = ~6.06%
    assert metrics.price_gap_percent is not None
    assert abs(metrics.price_gap_percent - 6.06) < 0.1

    # Gross margin: (175 - 142) / 175 * 100 = ~18.86%
    assert metrics.gross_margin_percent is not None
    assert abs(metrics.gross_margin_percent - 18.86) < 0.1

    # Position should be ABOVE or WELL_ABOVE because seller is above Q3 (171)
    assert metrics.market_position in (MarketPosition.ABOVE, MarketPosition.WELL_ABOVE)


def test_insufficient_data_threshold():
    now = utc_now()
    # Only 2 items (below minimum threshold of 3)
    items = [
        ShoppingItem(evidence_id="1", source=EvidenceSource.GOOGLE_SHOPPING, retrieved_at=now,
                     title="Item 1", price_inr=150.0),
        ShoppingItem(evidence_id="2", source=EvidenceSource.GOOGLE_SHOPPING, retrieved_at=now,
                     title="Item 2", price_inr=160.0),
    ]

    metrics = compute_market_metrics(
        comparable_items=items,
        all_items=items,
        seller_price=175.0,
        landed_cost=None,
        product_quantity=1.0,
        product_unit="L",
    )

    assert metrics.market_position == MarketPosition.INSUFFICIENT_DATA
    assert metrics.price_median is None


def test_iqr_filtering_on_outliers():
    now = utc_now()
    # 7 items: cluster around 150-165, with one extreme outlier at 900
    prices = [150.0, 155.0, 158.0, 160.0, 162.0, 165.0, 900.0]
    items = [
        ShoppingItem(evidence_id=str(i), source=EvidenceSource.GOOGLE_SHOPPING, retrieved_at=now,
                     title=f"Item {i}", price_inr=p)
        for i, p in enumerate(prices)
    ]

    filtered = apply_iqr_filtering(items, min_sample_for_iqr=6)
    filtered_prices = [item.price_inr for item in filtered]
    assert 900.0 not in filtered_prices
    assert len(filtered) == 6
