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
            [row.get("promo_text"), row.get("raw_offer_text"), row.get("split_product_text")],
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


def base_normalize_unit_price(row: dict[str, str]) -> float | None:
    price = _parse_price(row.get("advertised_price"))
    if price is None:
        return None
    basis = (row.get("price_basis") or "").lower()
    promo = _promo_text(row)
    if basis == "multi_buy" and not _re.search(r"(when you )?buy\s+\d+", promo):
        unit = _multi_buy_unit_price(row, price)
        if unit is not None:
            return unit
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
    return price


def normalize_per_lb(row: dict[str, str]) -> float | None:
    price = base_normalize_unit_price(row)
    if price is None:
        return None
    text = _promo_text(row)
    if _re.search(r"per\s*lb|/lb|lb bag", text):
        return price
    lbs = _extract_lb_weight(text)
    if lbs and lbs > 0:
        return round(price / lbs, 2)
    return price


def normalize_per_dozen(row: dict[str, str]) -> float | None:
    price = base_normalize_unit_price(row)
    if price is None:
        return None
    text = _promo_text(row)
    for count in (24, 18, 12):
        if _re.search(rf"{count}\s*(?:ct|count|-count)", text):
            return round(price * (12 / count), 2)
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


def normalize_price(row: dict[str, str], rule: str | None) -> float | None:
    if rule and rule in NORMALIZERS:
        return NORMALIZERS[rule](row)
    return base_normalize_unit_price(row)
