"""Shared guards so clearly invalid shelf baselines cannot ship."""

from __future__ import annotations

# Sweet-corn-style cents prices (e.g. $0.79/ear) remain valid; only <= 0 is rejected.
MIN_BASELINE_PRICE = 0.0


def is_valid_baseline_price(price: float | None) -> bool:
    """True when price is a usable positive shelf/regular price."""
    return price is not None and isinstance(price, (int, float)) and price > MIN_BASELINE_PRICE


def reject_invalid_baseline(
    canonical_id: str,
    price: float | None,
    *,
    product_name: str = "",
) -> str | None:
    """
    Return a warning message when price must be skipped, else None.
    """
    if is_valid_baseline_price(price):
        return None
    name = f" ({product_name[:60]})" if product_name else ""
    return (
        f"[skip invalid baseline] {canonical_id}{name}: "
        f"price={price!r} (must be > 0)"
    )
