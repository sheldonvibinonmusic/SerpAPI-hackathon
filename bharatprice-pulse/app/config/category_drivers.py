"""
category_drivers.py — BharatPrice Pulse
Category-to-search-engine driver matrix.

This module determines WHICH SerpApi engines are relevant for a given product category
and WHAT to search for. This is how we avoid wasting search credits on irrelevant engines
(e.g., querying USD/INR finance signal for a product of mustard oil).

Rule: Only include a market factor when it has a plausible relationship to the product
and seller decision. Do not add GDP, UPI, ONDC or every economic indicator to every query.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.models.request_models import ProductCategory


@dataclass
class CategoryDriver:
    """Defines the research plan for a product category."""
    category: ProductCategory
    display_name: str

    # SerpApi engines to use (in Standard mode — max 4 total including Search hub)
    use_shopping: bool = True
    use_google_local: bool = True
    use_news: bool = True
    use_trends: bool = True
    use_finance: bool = False  # Only when a validated instrument exists for this category

    # Finance instrument to query (only when use_finance=True)
    # Must be a verified, documented instrument — never fabricate a ticker
    finance_instrument: Optional[str] = None
    finance_instrument_label: Optional[str] = None

    # Google Local search query template — what type of merchant to look for
    local_search_template: str = "{product} wholesale distributor {city}"
    local_merchant_types: List[str] = field(default_factory=list)  # Relevant merchant types

    # News search keywords — specific to this category
    news_keywords: List[str] = field(default_factory=list)

    # Trends: which query to use (product name vs category term)
    trends_use_category_term: bool = False
    trends_comparison_queries: List[str] = field(default_factory=list)

    # Amazon search: whether Amazon India is a relevant benchmark for this category
    amazon_relevant: bool = False

    # Deep-check enrichments
    use_product_api_enrichment: bool = False  # Google Product API in Deep mode
    use_amazon_product: bool = False

    # Explanation hints for the UI
    why_finance_relevant: Optional[str] = None
    why_amazon_relevant: Optional[str] = None


# ---------------------------------------------------------------------------
# Category Driver Registry
# ---------------------------------------------------------------------------

CATEGORY_DRIVERS: Dict[ProductCategory, CategoryDriver] = {

    ProductCategory.EDIBLE_OIL_FMCG: CategoryDriver(
        category=ProductCategory.EDIBLE_OIL_FMCG,
        display_name="Edible Oils & FMCG",
        use_shopping=True,
        use_google_local=True,
        use_news=True,
        use_trends=True,
        # Finance: Edible oils are commodity-sensitive. However, no publicly
        # documented SerpApi Google Finance ticker directly maps to Indian edible oil
        # futures in a guaranteed way. We skip Finance rather than fabricate a ticker.
        # A future version can add verified NCDEX/MCX instrument codes if they become
        # consistently available via SerpApi Finance.
        use_finance=False,
        finance_instrument=None,
        local_search_template="edible oil wholesale distributor {city}",
        local_merchant_types=["wholesale distributor", "oil mill", "grocery wholesaler", "kirana wholesaler"],
        news_keywords=["mustard oil", "edible oil", "cooking oil", "import duty", "crop", "msp",
                       "supply", "wholesale price", "vegetable oil", "palm oil", "sunflower"],
        trends_use_category_term=True,
        amazon_relevant=True,
    ),

    ProductCategory.ELECTRONICS_MOBILES: CategoryDriver(
        category=ProductCategory.ELECTRONICS_MOBILES,
        display_name="Electronics & Mobile Phones",
        use_shopping=True,
        use_google_local=True,
        use_news=True,
        use_trends=True,
        # Finance: USD/INR is directly relevant for import-sensitive electronics.
        # SerpApi Google Finance supports currency queries. Using standard format.
        use_finance=True,
        finance_instrument="USDINR",
        finance_instrument_label="USD/INR Exchange Rate",
        why_finance_relevant=(
            "Most consumer electronics components are priced in USD. A weaker rupee "
            "can increase import costs and affect wholesale prices over time."
        ),
        local_search_template="mobile phone electronics wholesale {city}",
        local_merchant_types=["electronics distributor", "mobile wholesale", "electronics market"],
        news_keywords=["smartphone", "mobile", "electronics", "import duty", "customs",
                       "component shortage", "PLI scheme", "semiconductor", "GST electronics"],
        trends_use_category_term=False,  # Use specific model search for trends
        amazon_relevant=True,
        use_product_api_enrichment=True,  # Product detail/variant verification important
        why_amazon_relevant="Amazon India is a major online electronics market benchmark.",
    ),

    ProductCategory.PACKAGED_STAPLES: CategoryDriver(
        category=ProductCategory.PACKAGED_STAPLES,
        display_name="Packaged Staples (Rice, Pulses, Grains)",
        use_shopping=True,
        use_google_local=True,
        use_news=True,
        use_trends=True,
        use_finance=False,  # No consistent verified Finance instrument for grain futures via SerpApi
        local_search_template="grain rice pulse wholesale mandi {city}",
        local_merchant_types=["grain wholesale", "mandi", "rice mill", "food distributor", "agro trader"],
        news_keywords=["rice", "wheat", "basmati", "pulses", "msp", "procurement",
                       "kharif", "rabi", "harvest", "food inflation", "export ban", "PDS"],
        trends_use_category_term=True,
        amazon_relevant=True,
    ),

    ProductCategory.HOME_HARDWARE: CategoryDriver(
        category=ProductCategory.HOME_HARDWARE,
        display_name="Home & Hardware",
        use_shopping=True,
        use_google_local=True,
        use_news=True,
        use_trends=False,  # Trends less useful for slow-moving hardware categories
        use_finance=False,
        local_search_template="hardware wholesale supplier {city}",
        local_merchant_types=["hardware distributor", "building material supplier", "industrial supplier"],
        news_keywords=["steel price", "hardware", "construction material", "logistics",
                       "import duty", "supply chain"],
        amazon_relevant=False,
    ),

    ProductCategory.PERSONAL_CARE: CategoryDriver(
        category=ProductCategory.PERSONAL_CARE,
        display_name="Personal Care & Beauty",
        use_shopping=True,
        use_google_local=True,
        use_news=True,
        use_trends=True,
        use_finance=False,
        local_search_template="cosmetics personal care wholesale distributor {city}",
        local_merchant_types=["cosmetics distributor", "FMCG wholesale", "beauty wholesale"],
        news_keywords=["personal care", "FMCG", "cosmetics", "beauty", "GST", "import",
                       "D2C", "quick commerce"],
        amazon_relevant=True,
    ),

    ProductCategory.DAIRY_BEVERAGES: CategoryDriver(
        category=ProductCategory.DAIRY_BEVERAGES,
        display_name="Dairy & Beverages",
        use_shopping=True,
        use_google_local=True,
        use_news=True,
        use_trends=False,
        use_finance=False,
        local_search_template="dairy beverage distributor wholesale {city}",
        local_merchant_types=["dairy distributor", "FMCG wholesale", "beverage distributor"],
        news_keywords=["milk price", "dairy", "beverage", "soft drink", "FSSAI",
                       "cold chain", "Amul", "supply"],
        amazon_relevant=False,  # Dairy is not typically a strong Amazon category
    ),

    ProductCategory.SEASONAL_FESTIVAL: CategoryDriver(
        category=ProductCategory.SEASONAL_FESTIVAL,
        display_name="Seasonal & Festival Goods",
        use_shopping=True,
        use_google_local=True,
        use_news=True,
        use_trends=True,   # Trends is VERY useful for seasonal demand spikes
        use_finance=False,
        local_search_template="seasonal gift festival goods wholesale {city}",
        local_merchant_types=["seasonal goods", "gift wholesale", "festival supplier"],
        news_keywords=["Diwali", "Holi", "Eid", "festival season", "demand surge",
                       "gifting", "fireworks", "seasonal"],
        trends_use_category_term=True,
        amazon_relevant=True,
    ),

    ProductCategory.GENERAL: CategoryDriver(
        category=ProductCategory.GENERAL,
        display_name="General Products",
        use_shopping=True,
        use_google_local=True,
        use_news=True,
        use_trends=True,
        use_finance=False,
        local_search_template="{product} wholesale distributor {city}",
        local_merchant_types=["wholesale", "distributor", "supplier"],
        news_keywords=[],  # Will be populated from product name at runtime
        amazon_relevant=True,
    ),

    ProductCategory.UNKNOWN: CategoryDriver(
        category=ProductCategory.UNKNOWN,
        display_name="Unknown Category",
        use_shopping=True,
        use_google_local=True,
        use_news=False,    # Cannot search news without category context
        use_trends=False,
        use_finance=False,
        local_search_template="{product} wholesale {city}",
        local_merchant_types=["wholesale", "distributor"],
        news_keywords=[],
        amazon_relevant=False,
    ),
}


def get_driver(category: ProductCategory) -> CategoryDriver:
    """Return the driver for a given category, falling back to GENERAL."""
    return CATEGORY_DRIVERS.get(category, CATEGORY_DRIVERS[ProductCategory.GENERAL])
