"""
test_fusion.py — BharatPrice Pulse
Tests for multi-dimensional evidence fusion and confidence scoring.
"""
from datetime import datetime
from app.models.evidence_models import (
    EvidenceBundle,
    ShoppingItem,
    LocalMerchant,
    EvidenceSource,
)
from app.models.decision_models import MarketMetrics, MarketPosition, LocalSourcingSignal, ConfidenceLevel
from app.services.evidence_fusion import fuse_evidence
from app.utils.datetime_utils import utc_now


def test_evidence_fusion_dimensions():
    now = utc_now()
    items = [
        ShoppingItem(evidence_id=f"s_{i}", source=EvidenceSource.GOOGLE_SHOPPING, retrieved_at=now,
                     title=f"Oil {i}", price_inr=160.0)
        for i in range(5)
    ]
    merchants = [
        LocalMerchant(evidence_id="m_1", source=EvidenceSource.GOOGLE_LOCAL, retrieved_at=now,
                      title="Shri Karni Oil Mill", is_wholesaler_or_distributor=True, type_relevance_score=0.9),
        LocalMerchant(evidence_id="m_2", source=EvidenceSource.GOOGLE_LOCAL, retrieved_at=now,
                      title="Jaipur Wholesale Traders", is_wholesaler_or_distributor=True, type_relevance_score=0.8),
    ]

    bundle = EvidenceBundle(
        analysis_id="test_fuse",
        normalized_query_cache_key="key",
        collected_at=now,
        shopping_items=items,
        comparable_items=items,
        local_merchants=merchants,
    )

    metrics = MarketMetrics(
        total_retrieved=5,
        comparable_count=5,
        excluded_count=0,
        seller_price=175.0,
        price_median=160.0,
        price_gap_percent=9.37,
        market_position=MarketPosition.ABOVE,
    )

    fusion = fuse_evidence(bundle, metrics)

    assert fusion.market_position == MarketPosition.ABOVE
    assert fusion.local_sourcing_signal == LocalSourcingSignal.HIGH
    assert fusion.local_merchants_found == 2
    assert fusion.wholesaler_count == 2
    assert fusion.confidence in (ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM)
    assert len(fusion.market_position_evidence_ids) > 0
