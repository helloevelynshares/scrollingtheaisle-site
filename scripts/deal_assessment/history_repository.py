"""Load historical weekly unit prices from generated tracker series."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from weekly_ad_analysis.benchmarks import (
    _feed_files,
    _parse_ts_export,
    _series_for_tracker,
)

from .models import PriceObservation

ROOT = Path(__file__).resolve().parents[2]
FAMILY_TS = ROOT / "src" / "data" / "canonicalTrackerFamilies.generated.ts"

RETAILER_TO_FEED = {
    "safeway": "safeway_bay_area",
    "safeway bay area": "safeway_bay_area",
    "vons": "vons_albertsons_socal",
    "albertsons": "vons_albertsons_socal",
    "vons/albertsons": "vons_albertsons_socal",
}

DEFAULT_FEED_ID = "safeway_bay_area"


def resolve_feed_id(retailer: str | None) -> str | None:
    if not retailer or not str(retailer).strip():
        return DEFAULT_FEED_ID
    key = str(retailer).strip().lower()
    if key in RETAILER_TO_FEED:
        return RETAILER_TO_FEED[key]
    if "safeway" in key:
        return "safeway_bay_area"
    if "vons" in key or "albertsons" in key:
        return "vons_albertsons_socal"
    return None


def load_family_meta(tracker_id: str) -> dict[str, Any] | None:
    """Best-effort parse of subtitle/displayName for the YAML family id."""
    if not FAMILY_TS.is_file():
        return None
    text = FAMILY_TS.read_text(encoding="utf-8")
    pattern = (
        rf'\{{\s*"id":\s*"{re.escape(tracker_id)}",\s*'
        rf'"displayName":\s*"([^"]*)",\s*'
        rf'"subtitle":\s*"([^"]*)"'
    )
    match = re.search(pattern, text)
    if not match:
        return None
    subtitle = match.group(2).encode("utf-8").decode("unicode_escape")
    return {
        "id": tracker_id,
        "display_name": match.group(1),
        "subtitle": subtitle,
    }


def load_observation_series(
    tracker_id: str,
    feed_id: str,
    *,
    tracker_kind: str = "canonical",
) -> list[PriceObservation]:
    """Return chartable historical unit prices for a tracker+feed (oldest→newest)."""
    canonical_ts, weeks_key, prices_key, family_ts, family_key, _member = _feed_files(
        feed_id
    )
    weeks, prices = _parse_ts_export(canonical_ts, weeks_key, prices_key)
    _, family_prices = _parse_ts_export(family_ts, "FAMILY_WEEKLY_AD_WEEKS", family_key)
    series = _series_for_tracker(
        tracker_id,
        tracker_kind,
        weeks,
        prices,
        family_prices,
        before_week=None,
    )
    bucket = family_prices if tracker_kind == "family" else prices
    out: list[PriceObservation] = []
    for week_start, unit_price in series:
        entry = (bucket.get(tracker_id) or {}).get(week_start) or {}
        out.append(
            PriceObservation(
                week_start=week_start,
                unit_price=float(unit_price),
                promo_note=entry.get("promoNote"),
                offer_text=entry.get("offerText"),
                confidence=entry.get("confidence"),
            )
        )
    return out


def tracker_exists(tracker_id: str, feed_id: str) -> bool:
    if load_family_meta(tracker_id):
        return True
    canonical_ts, weeks_key, prices_key, _family_ts, _family_key, _ = _feed_files(
        feed_id
    )
    _weeks, prices = _parse_ts_export(canonical_ts, weeks_key, prices_key)
    return tracker_id in prices
