"""Comparability gates before a historical verdict is allowed."""

from __future__ import annotations

import re

from .history_repository import (
    load_family_meta,
    load_observation_series,
    resolve_feed_id,
    tracker_exists,
)
from .models import ComparabilityResult, NormalizedOffer, SubmittedOffer
from .policy import history_tier


def _parse_oz_range(subtitle: str | None) -> tuple[float | None, float | None]:
    if not subtitle:
        return None, None
    match = re.search(
        r"(\d+(?:\.\d+)?)\s*[–\-]\s*(\d+(?:\.\d+)?)\s*oz",
        subtitle,
        re.I,
    )
    if not match:
        return None, None
    return float(match.group(1)), float(match.group(2))


def _parse_offer_oz(package_size: str | None) -> float | None:
    if not package_size:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*oz", package_size, re.I)
    if not match:
        return None
    return float(match.group(1))


def check_comparability(
    *,
    tracker_id: str,
    retailer: str,
    offer: SubmittedOffer,
    normalized: NormalizedOffer,
) -> ComparabilityResult:
    """Hard gates only. History volume is handled as a scoring tier, not here.

    Hard fail reasons:
    - missing_tracker_id
    - unknown_tracker
    - unsupported_retailer
    - cannot_normalize_unit_price
    - package_size_out_of_family_range
    """
    reasons: list[str] = []
    notes: list[str] = []

    tid = (tracker_id or "").strip()
    if not tid:
        reasons.append("missing_tracker_id")
        return ComparabilityResult(ok=False, reasons=tuple(reasons), notes=tuple(notes))

    feed_id = resolve_feed_id(retailer or offer.retailer)
    if feed_id is None:
        reasons.append("unsupported_retailer")
        return ComparabilityResult(
            ok=False,
            reasons=tuple(reasons),
            notes=tuple(notes),
            tracker_id=tid,
        )

    if not tracker_exists(tid, feed_id):
        reasons.append("unknown_tracker")
        return ComparabilityResult(
            ok=False,
            reasons=tuple(reasons),
            notes=tuple(notes),
            feed_id=feed_id,
            tracker_id=tid,
        )

    if normalized.comparable_unit_price is None:
        reasons.append("cannot_normalize_unit_price")
        notes.extend(normalized.notes)

    meta = load_family_meta(tid)
    if meta is None:
        notes.append("family_meta_missing")

    observations = load_observation_series(tid, feed_id)
    count = len(observations)
    tier = history_tier(count)
    notes.append(f"observation_count={count}")
    notes.append(f"history_tier={tier}")

    # Soft size-range check when both sides are oz-denominated.
    if meta:
        lo, hi = _parse_oz_range(meta.get("subtitle"))
        offer_oz = _parse_offer_oz(offer.package_size)
        if lo is not None and hi is not None and offer_oz is not None:
            if offer_oz < lo - 0.05 or offer_oz > hi + 0.05:
                reasons.append("package_size_out_of_family_range")
                notes.append(f"offer_oz={offer_oz} family_range={lo}-{hi}")
            else:
                notes.append(f"package_size_within_range_{lo}-{hi}_oz")

    ok = len(reasons) == 0
    return ComparabilityResult(
        ok=ok,
        reasons=tuple(reasons),
        notes=tuple(notes),
        feed_id=feed_id,
        tracker_id=tid,
        observation_count=count,
    )
