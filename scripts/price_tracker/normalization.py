"""Unit normalization for YAML tracker families (weekly ad price extraction)."""

from __future__ import annotations

import re
from typing import Callable

import re as _re


def _parse_price(value: str | None) -> float | None:
    if not value or value in {"$", ""}:
        return None
    try:
        return float(value.replace("$", "").strip())
    except ValueError:
        return None


def _promo_text(row: dict[str, str]) -> str:
    return " ".join(
        filter(
            None,
            [
                row.get("promo_text"),
                row.get("raw_offer_text"),
                row.get("split_product_text"),
                row.get("package_text"),
            ],
        )
    ).lower()


def _multi_buy_unit_price(row: dict[str, str], price: float) -> float | None:
    promo = _promo_text(row)
    count_match = _re.search(r"(\d+)\s*(?:for|/)\s*\$?\s*(\d+(?:\.\d+)?)", promo)
    if count_match:
        count = float(count_match.group(1))
        total = float(count_match.group(2))
        if count > 0:
            return round(total / count, 2)
    if "2 for" in promo and price > 0:
        return round(price / 2, 2)
    size = row.get("package_size_min") or row.get("package_size_max") or ""
    unit = (row.get("package_unit") or "").lower()
    if size and unit in {"", "count", "ct", "each"}:
        try:
            count = float(size)
            if count > 1:
                return round(price / count, 2)
        except ValueError:
            pass
    return None


def _explicit_n_for_x_unit_price(row: dict[str, str]) -> float | None:
    """Unit price from an explicit ``N for $X`` / ``N/$X`` total in offer text.

    Applied regardless of ``price_basis`` so a multi-buy total mislabeled as
    ``each`` (e.g. ``$5 ea`` on a ``2 for $5`` Friday tile) still normalizes.
    """
    promo = _promo_text(row)
    count_match = _re.search(r"(\d+)\s*(?:for|/)\s*\$?\s*(\d+(?:\.\d+)?)", promo)
    if not count_match:
        return None
    count = float(count_match.group(1))
    total = float(count_match.group(2))
    if count <= 0:
        return None
    return round(total / count, 2)


def _member_price_each_from_text(row: dict[str, str]) -> float | None:
    """Small-print ``Member Price: $X.XX ea`` when it disagrees with a big $5 badge."""
    promo = _promo_text(row)
    m = _re.search(
        r"member\s+price\s*:?\s*\$?\s*(\d+(?:\.\d+)?)\s*(?:ea\.?|each)\b",
        promo,
    )
    if not m:
        return None
    return round(float(m.group(1)), 2)


def _pack_count_unit_price(row: dict[str, str], price: float) -> float | None:
    """Divide pack-total prices by N from ``5 ct`` / ``5-count`` package cues."""
    if price <= 0:
        return None
    promo = _promo_text(row)
    size = row.get("package_size_min") or row.get("package_size_max") or ""
    unit = (row.get("package_unit") or "").lower()
    count: float | None = None
    if size and unit in {"", "count", "ct", "each"}:
        try:
            count = float(size)
        except ValueError:
            count = None
    if count is None:
        m = _re.search(r"\b(\d+)\s*-?\s*(?:ct|count)\b", promo)
        if m:
            count = float(m.group(1))
    if count is None or count <= 1:
        return None
    return round(price / count, 2)


def _buy_x_get_y_unit_price(row: dict[str, str], price: float) -> float | None:
    """Compute effective per-unit price for buy-X-get-Y-free deals.

    E.g. 'BUY 2 GET 3 FREE' with ref price $5.49 → pay for 2, receive 5 → $2.20/unit.
    E.g. 'BUY 1 GET 1 FREE' (BOGO) → pay for 1, receive 2 → price/2.
    """
    promo = _promo_text(row)
    # "buy N get M free" / "buy N, get M free" patterns
    m = _re.search(r"buy\s+(\d+)[,\s]+get\s+(\d+)\s+free", promo)
    if m:
        buy_count = float(m.group(1))
        free_count = float(m.group(2))
        total = buy_count + free_count
        if total > 0 and price > 0:
            return round(price * buy_count / total, 2)
    # BOGO: "buy 1 get 1 free" already covered above; catch bare "bogo" keyword
    if _re.search(r"\bbogo\b", promo) and price > 0:
        return round(price / 2, 2)
    return None


def base_normalize_unit_price(
    row: dict[str, str],
    *,
    fallback_reference_price: float | None = None,
) -> float | None:
    price = _parse_price(row.get("advertised_price"))
    basis = (row.get("price_basis") or "").lower()
    # BOGO / buy-X-get-Y ads often print the mechanic but not a shelf price
    # ("BUY 1 GET 1 FREE EQUAL OR LESSER VALUE"). Use the tracker baseline (or
    # another caller-supplied reference) so charts show effective unit cost.
    if price is None:
        if (
            basis in {"bogo", "buy_x_get_y"}
            and fallback_reference_price is not None
            and fallback_reference_price > 0
        ):
            return _buy_x_get_y_unit_price(row, float(fallback_reference_price))
        return None
    # Explicit "N for $X" always wins, even when vision labeled the row as each/$5 ea.
    explicit = _explicit_n_for_x_unit_price(row)
    if explicit is not None:
        return explicit
    # Small-print unit price on $5 Friday tiles (e.g. Member Price: $1.25 ea).
    member_each = _member_price_each_from_text(row)
    if member_each is not None and member_each < price:
        return member_each
    # Handle B2G3F / BOGO: compute effective per-unit price from reference price
    if basis in {"bogo", "buy_x_get_y"}:
        unit = _buy_x_get_y_unit_price(row, price)
        if unit is not None:
            return unit
    if basis == "multi_buy":
        # Always try explicit "N for $X" normalization first (e.g. "PICK 4 FOR $20 WHEN YOU BUY 4").
        # The old guard `not re.search(r"(when you )?buy N")` skipped this for bundle deals that
        # restate the quantity condition, those still need the per-unit divide.
        # Only skip if there is no "N for $X" pattern AND there is a "save $X when you buy N"
        # style (discount trigger rather than total price), i.e. _multi_buy_unit_price returns None.
        unit = _multi_buy_unit_price(row, price)
        if unit is not None:
            return unit
    # Pack totals labeled per_pack with "5 ct" → per-unit (do not use for eggs/bars `each`).
    if basis == "per_pack":
        pack_unit = _pack_count_unit_price(row, price)
        if pack_unit is not None:
            return pack_unit
    return round(price, 2)


def _extract_lb_weight(text: str) -> float | None:
    m = _re.search(r"(\d+(?:\.\d+)?)\s*(?:-|\s)?\s*lb", text)
    if m:
        return float(m.group(1))
    return None


def normalize_strawberries_per_lb(row: dict[str, str]) -> float | None:
    price = base_normalize_unit_price(row)
    if price is None:
        return None
    text = _promo_text(row)
    lbs = _extract_lb_weight(text)
    if lbs and lbs > 0:
        return round(price / lbs, 2)
    if _re.search(r"2\s*lb|2-lb", text):
        return round(price / 2, 2)
    # "Large Pack" without an explicit lb weight is ambiguous for the 1–2 lb
    # graph; do not treat the pack total as a per-lb / 1-lb proxy.
    if _re.search(r"large\s+pack", text) and not _re.search(r"\b\d+(?:\.\d+)?\s*lb\b", text):
        return None
    return price


def normalize_per_lb(row: dict[str, str]) -> float | None:
    price = base_normalize_unit_price(row)
    if price is None:
        return None
    # If the CSV explicitly says the price is already per-lb, no weight conversion needed.
    # Weekly ad extraction sets price_basis="per_lb" when the ad shows a per-lb rate
    # (e.g. "Ribeye Steak $9.99 LB", "Grapes $2.49 lb"). Without this guard,
    # _extract_lb_weight() would find "9.99" before "lb" in the offer text and divide
    # the price by itself, yielding $1.00.
    if (row.get("price_basis") or "").lower() == "per_lb":
        return price
    text = _promo_text(row)
    if _re.search(r"per\s*lb|/lb|lb bag", text):
        return price
    lbs = _extract_lb_weight(text)
    if lbs and lbs > 0:
        # Safety check: if the extracted weight equals the advertised price the offer text
        # likely says "$X/lb" not "weighs X lbs", skip division to avoid yielding $1.00.
        if price > 0 and abs(lbs - price) / price < 0.02:
            return price
        return round(price / lbs, 2)
    return price


def normalize_per_dozen(row: dict[str, str]) -> float | None:
    price = base_normalize_unit_price(row)
    if price is None:
        return None
    text = _promo_text(row)
    for count in (24, 18, 12):
        # Match "18 ct", "18-ct.", "18 count", "18-count"
        if _re.search(rf"{count}\s*[- ]?(?:ct|count)\b", text):
            return round(price * (12 / count), 2)
    if _re.search(r"\bdozen\b|\bdz\b", text):
        return price
    # Fall back to CSV package size when text is sparse (e.g. "Eggs" + size 18).
    for key in ("package_size_min", "package_size_max"):
        raw = (row.get(key) or "").strip()
        if not raw:
            continue
        try:
            size = float(raw)
        except ValueError:
            continue
        if size in (24, 18, 12):
            return round(price * (12 / size), 2)
    return price


def normalize_per_cup(row: dict[str, str]) -> float | None:
    price = base_normalize_unit_price(row)
    if price is None:
        return None
    text = _promo_text(row)
    pack = _re.search(r"(\d+)\s*(?:-?\s*pack|pk|ct|count)", text)
    if pack:
        count = float(pack.group(1))
        if count > 1:
            return round(price / count, 2)
    oz = _re.search(r"(\d+(?:\.\d+)?)\s*oz", text)
    if oz:
        cups = float(oz.group(1)) / 5.3
        if cups > 1:
            return round(price / cups, 2)
    if price > 8:
        return round(price / 4, 2)
    return price


def normalize_per_16oz(row: dict[str, str]) -> float | None:
    price = base_normalize_unit_price(row)
    if price is None:
        return None
    text = _promo_text(row)
    oz = _re.search(r"(\d+(?:\.\d+)?)\s*oz", text)
    if oz:
        weight = float(oz.group(1))
        if weight > 0:
            return round(price * (16 / weight), 2)
    return price


def normalize_cheese_6_8oz(row: dict[str, str]) -> float | None:
    return base_normalize_unit_price(row)


def normalize_per_bar(row: dict[str, str]) -> float | None:
    price = base_normalize_unit_price(row)
    if price is None:
        return None
    text = _promo_text(row)
    pack = _re.search(r"(\d+)\s*(?:ct|count|pk|pack|bars?)", text)
    if pack:
        count = float(pack.group(1))
        if count > 1:
            return round(price / count, 2)
    return price


NORMALIZERS: dict[str, Callable[[dict[str, str]], float | None]] = {
    "strawberries_per_lb": normalize_strawberries_per_lb,
    "per_lb": normalize_per_lb,
    "per_dozen": normalize_per_dozen,
    "per_cup": normalize_per_cup,
    "per_16oz": normalize_per_16oz,
    "cheese_6_8oz": normalize_cheese_6_8oz,
    "per_bar": normalize_per_bar,
}


def normalize_price(
    row: dict[str, str],
    rule: str | None,
    *,
    fallback_reference_price: float | None = None,
) -> float | None:
    if rule and rule in NORMALIZERS:
        result = NORMALIZERS[rule](row)
        if result is not None:
            return result
        # Specialized normalizers that need an advertised price still return None
        # for BOGO-without-price; fall through to baseline-backed BOGO math.
    return base_normalize_unit_price(
        row, fallback_reference_price=fallback_reference_price
    )
