"""Shared offer vocabulary for promotion types and price bases.

Single source of truth used by shopper_query (production) and optional
local labeling tools. Keep this module dependency-neutral — no imports from
holdout_labeler, deal_assistant, or other tooling packages.
"""

from __future__ import annotations

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
