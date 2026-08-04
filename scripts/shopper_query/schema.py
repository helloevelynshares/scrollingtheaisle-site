"""Structured fields extracted from a shopper query (deterministic).

Promotion / price-basis vocabularies stay aligned with the weekly-ad
labeling schema (same values as holdout_labeler.paths).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# Keep in sync with holdout_labeler.paths (avoid importing that package at runtime).
PROMOTION_TYPES = (
    "regular_price",
    "simple_sale",
    "member_price",
    "digital_coupon",
    "multi_buy",
    "buy_x_get_y",
    "bogo",
    "price_per_pound",
    "mixed_or_unclear",
    "unknown",
)

PRICE_BASIS_VALUES = (
    "each",
    "per_lb",
    "per_oz",
    "multi_buy",
    "bogo",
    "buy_x_get_y",
    "per_pack",
    "unknown",
)

PROMOTION_TYPE_SET = frozenset(PROMOTION_TYPES)
PRICE_BASIS_SET = frozenset(PRICE_BASIS_VALUES)

SUPPORTED_RETAILERS = frozenset(
    {
        "safeway",
        "vons",
        "albertsons",
        "pavilions",
    }
)


@dataclass
class ParsedShopperQuery:
    retailer: str | None = None
    product_text: str = ""
    price: float | None = None
    package_size_text: str | None = None
    package_size_value: float | None = None
    package_size_unit: str | None = None
    promotion_type: str = "unknown"
    required_quantity: int | None = None
    items_received: int | None = None
    price_basis: str = "unknown"
    missing_fields: list[str] = field(default_factory=list)
    ambiguities: list[str] = field(default_factory=list)
    # Parser diagnostics (not part of holdout label schema).
    conflicting_prices: bool = False
    malformed_price: bool = False
    unsupported_retailer: bool = False
    parse_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
