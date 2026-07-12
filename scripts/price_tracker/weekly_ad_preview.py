"""Weekly ad preview helpers, date-based active vs preview-only weeks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable


def iso_date(value: date | datetime | None = None) -> str:
    if value is None:
        return date.today().isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    return value.isoformat()


def parse_iso_date(value: str) -> date:
    return date.fromisoformat(value)


def is_preview_week(week_start: str, as_of: date | None = None) -> bool:
    """True when today is strictly before the ad week start date."""
    today = parse_iso_date(as_of.isoformat() if as_of else iso_date())
    return today < parse_iso_date(week_start)


def is_active_week(week_start: str, week_end: str, as_of: date | None = None) -> bool:
    """True when today falls within the ad week (inclusive)."""
    today = parse_iso_date(as_of.isoformat() if as_of else iso_date())
    start = parse_iso_date(week_start)
    end = parse_iso_date(week_end)
    return start <= today <= end


def latest_manifest_entry(manifest: list[dict[str, str]]) -> dict[str, str] | None:
    if not manifest:
        return None
    return max(manifest, key=lambda row: row["week_start"])


@dataclass(frozen=True)
class FeedPreviewSummary:
    feed_label: str
    week_start: str
    week_end: str
    is_preview: bool
    tracked_products: int
    matched_products: int
    unmatched_products: int
    products_before: int
    products_after: int


def validate_tracker_product_ids_unchanged(
    before: Iterable[str],
    after: Iterable[str],
) -> tuple[set[str], set[str]]:
    """Return (added, removed); raises if either is non-empty."""
    before_set = set(before)
    after_set = set(after)
    added = after_set - before_set
    removed = before_set - after_set
    if added or removed:
        parts: list[str] = []
        if added:
            parts.append(f"added={sorted(added)}")
        if removed:
            parts.append(f"removed={sorted(removed)}")
        raise SystemExit(
            "Canonical tracker product list changed during weekly ad import. "
            + "; ".join(parts)
        )
    return added, removed


def build_feed_preview_summary(
    feed_label: str,
    manifest: list[dict[str, str]],
    prices: dict[str, dict[str, dict[str, object | None]]],
    tracked_ids: Iterable[str],
    *,
    as_of: date | None = None,
    products_before: int | None = None,
    products_after: int | None = None,
) -> FeedPreviewSummary | None:
    latest = latest_manifest_entry(manifest)
    if latest is None:
        return None

    week_start = latest["week_start"]
    week_end = latest["week_end"]
    tracked = list(tracked_ids)
    matched = sum(
        1
        for product_id in tracked
        if (prices.get(product_id) or {}).get(week_start, {}).get("price") is not None
    )

    return FeedPreviewSummary(
        feed_label=feed_label,
        week_start=week_start,
        week_end=week_end,
        is_preview=is_preview_week(week_start, as_of),
        tracked_products=len(tracked),
        matched_products=matched,
        unmatched_products=len(tracked) - matched,
        products_before=products_before if products_before is not None else len(tracked),
        products_after=products_after if products_after is not None else len(tracked),
    )


def format_preview_summary(summary: FeedPreviewSummary) -> str:
    status = "PREVIEW (not yet active)" if summary.is_preview else "ACTIVE"
    return (
        f"{summary.feed_label}: {summary.week_start} → {summary.week_end} [{status}] | "
        f"tracked={summary.tracked_products} (before={summary.products_before}, "
        f"after={summary.products_after}) | "
        f"matched={summary.matched_products} unmatched={summary.unmatched_products} | "
        f"no adds/removes confirmed"
    )
