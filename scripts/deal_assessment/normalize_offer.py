"""Normalize a confirmed structured offer into a comparable unit price."""

from __future__ import annotations

from .models import NormalizedOffer, SubmittedOffer


def normalize_submitted_offer(offer: SubmittedOffer) -> NormalizedOffer:
    """Derive a comparable unit price from confirmed fields only.

    Does not reparse free-text queries. Does not invent prices.
    """
    notes: list[str] = []
    if offer.price is None or offer.price <= 0:
        return NormalizedOffer(
            comparable_unit_price=None,
            normalization_method="missing_price",
            notes=("price_missing_or_invalid",),
        )

    basis = (offer.price_basis or "unknown").lower()
    qty = offer.required_quantity
    promo = (offer.promotion_type or "").lower()
    price = float(offer.price)

    # Explicit multi-buy totals: "3 for $5" → unit = total / N
    if basis in {"multi_buy", "n_for"} or promo in {"multi_buy", "n_for"}:
        if qty and qty > 1:
            unit = round(price / qty, 4)
            notes.append(f"multi_buy_total_divided_by_{qty}")
            return NormalizedOffer(
                comparable_unit_price=unit,
                normalization_method="multi_buy_unit",
                notes=tuple(notes),
            )
        notes.append("multi_buy_missing_quantity")
        return NormalizedOffer(
            comparable_unit_price=None,
            normalization_method="multi_buy_incomplete",
            notes=tuple(notes),
        )

    # BOGO / buy-one-get-one: treat advertised price as shelf reference → half.
    if basis in {"bogo", "buy_x_get_y"} or promo in {"bogo", "buy_x_get_y"}:
        unit = round(price / 2.0, 4)
        notes.append("bogo_half_of_reference_price")
        return NormalizedOffer(
            comparable_unit_price=unit,
            normalization_method="bogo_effective_unit",
            notes=tuple(notes),
        )

    # "$X each when buying N" and plain each/lb/dozen: price is already unit.
    if basis in {"each", "per_lb", "per_pound", "per_dozen", "unknown", ""}:
        if qty and qty > 1 and basis in {"each", "unknown", ""}:
            notes.append(f"each_price_with_buy_requirement_{qty}")
        return NormalizedOffer(
            comparable_unit_price=round(price, 4),
            normalization_method="as_stated_unit",
            notes=tuple(notes),
        )

    notes.append(f"unsupported_price_basis:{basis}")
    return NormalizedOffer(
        comparable_unit_price=None,
        normalization_method="unsupported_basis",
        notes=tuple(notes),
    )
