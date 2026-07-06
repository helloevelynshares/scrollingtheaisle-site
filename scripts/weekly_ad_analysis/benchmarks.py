"""Historical benchmark stats from generated weekly ad price files."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
THRESHOLDS_PATH = ROOT / "config" / "price_benchmark_thresholds.json"

SAFEWAY_TS = ROOT / "src" / "data" / "weeklyAdPrices.generated.ts"
VONS_TS = ROOT / "src" / "data" / "vonsWeeklyAdPrices.generated.ts"
FAMILY_TS = ROOT / "src" / "data" / "familyWeeklyAdPrices.generated.ts"


@dataclass(frozen=True)
class BenchmarkThresholds:
    min_observations: int = 2
    all_time_low_tolerance: float = 1.001
    near_all_time_low_multiplier: float = 1.05
    strong_sale_vs_ninety_day_low: float = 0.999
    strong_sale_vs_median: float = 0.97
    normal_sale_vs_median: float = 1.03
    ninety_day_week_fallback: int = 13


@dataclass(frozen=True)
class HistoricalBenchmark:
    market_all_time_low_unit_price: float | None
    market_90_day_low_unit_price: float | None
    market_median_unit_price: float | None
    latest_seen_unit_price: float | None
    percent_above_all_time_low: float | None
    percent_below_median: float | None
    benchmark_bucket: str
    observation_count: int


def load_benchmark_thresholds(path: Path = THRESHOLDS_PATH) -> BenchmarkThresholds:
    if not path.is_file():
        return BenchmarkThresholds()
    raw = json.loads(path.read_text(encoding="utf-8"))
    return BenchmarkThresholds(
        min_observations=int(raw.get("minObservations", 2)),
        all_time_low_tolerance=float(raw.get("allTimeLowTolerance", 1.001)),
        near_all_time_low_multiplier=float(raw.get("nearAllTimeLowMultiplier", 1.05)),
        strong_sale_vs_ninety_day_low=float(raw.get("strongSaleVsNinetyDayLow", 0.999)),
        strong_sale_vs_median=float(raw.get("strongSaleVsMedian", 0.97)),
        normal_sale_vs_median=float(raw.get("normalSaleVsMedian", 1.03)),
        ninety_day_week_fallback=int(raw.get("ninetyDayWeekFallback", 13)),
    )


def percent_above_all_time_low(
    price: float | None,
    all_time_low: float | None,
) -> float | None:
    if price is None or all_time_low is None or all_time_low <= 0:
        return None
    return round(((price - all_time_low) / all_time_low) * 100, 2)


def percent_below_median(
    price: float | None,
    median: float | None,
) -> float | None:
    if price is None or median is None or median <= 0:
        return None
    return round(((median - price) / median) * 100, 2)


def _parse_ts_export(path: Path, weeks_key: str, prices_key: str) -> tuple[list[dict], dict]:
    text = path.read_text(encoding="utf-8")
    weeks_match = re.search(rf"export const {weeks_key}.*?=\s*(\[.*?\]);", text, re.S)
    prices_match = re.search(rf"export const {prices_key}.*?=\s*(\{{.*?\}});", text, re.S)
    if not weeks_match or not prices_match:
        raise RuntimeError(f"Could not parse {path}")
    return json.loads(weeks_match.group(1)), json.loads(prices_match.group(1))


def _feed_files(feed_id: str) -> tuple[Path, str, str, Path, str, str]:
    if feed_id == "safeway_bay_area":
        return (
            SAFEWAY_TS,
            "WEEKLY_AD_WEEKS",
            "WEEKLY_AD_PRICES",
            FAMILY_TS,
            "FAMILY_WEEKLY_AD_PRICES",
            "FAMILY_MEMBER_WEEKLY_AD_PRICES",
        )
    return (
        VONS_TS,
        "VONS_WEEKLY_AD_WEEKS",
        "VONS_WEEKLY_AD_PRICES",
        FAMILY_TS,
        "VONS_FAMILY_WEEKLY_AD_PRICES",
        "VONS_FAMILY_MEMBER_WEEKLY_AD_PRICES",
    )


def _series_for_tracker(
    tracker_id: str,
    tracker_kind: str,
    weeks: list[dict],
    prices: dict,
    family_prices: dict,
    *,
    before_week: str | None = None,
) -> list[tuple[str, float]]:
    bucket = family_prices if tracker_kind == "family" else prices
    series: list[tuple[str, float]] = []
    for week in sorted(weeks, key=lambda w: w["weekStart"]):
        week_start = week["weekStart"]
        if before_week and week_start >= before_week:
            continue
        entry = bucket.get(tracker_id, {}).get(week_start)
        if not entry:
            continue
        price = entry.get("price")
        confidence = entry.get("confidence")
        if price is None or confidence is None or confidence == "low":
            continue
        series.append((week_start, float(price)))
    return series


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    sorted_vals = sorted(values)
    mid = len(sorted_vals) // 2
    if len(sorted_vals) % 2:
        return sorted_vals[mid]
    return round((sorted_vals[mid - 1] + sorted_vals[mid]) / 2, 4)


def bucket_for_price(
    price: float | None,
    *,
    all_time_low: float | None,
    ninety_day_low: float | None,
    median: float | None,
    count: int,
    thresholds: BenchmarkThresholds | None = None,
) -> str:
    cfg = thresholds or load_benchmark_thresholds()
    if price is None or count < cfg.min_observations:
        return "insufficient history"
    near_low_threshold = (
        all_time_low * cfg.near_all_time_low_multiplier if all_time_low is not None else None
    )
    if all_time_low is not None and price <= all_time_low * cfg.all_time_low_tolerance:
        return "all-time low"
    if near_low_threshold is not None and price <= near_low_threshold:
        return "near all-time low"
    if ninety_day_low is not None and price < ninety_day_low * cfg.strong_sale_vs_ninety_day_low:
        return "strong sale"
    if median is not None and price < median * cfg.strong_sale_vs_median:
        return "strong sale"
    if median is not None and price <= median * cfg.normal_sale_vs_median:
        return "normal sale"
    return "weak sale"


def compute_benchmark_from_values(
    values: list[float],
    current_unit_price: float | None,
    *,
    ninety_values: list[float] | None = None,
    thresholds: BenchmarkThresholds | None = None,
) -> HistoricalBenchmark:
    cfg = thresholds or load_benchmark_thresholds()
    ninety = ninety_values if ninety_values is not None else values
    if len(values) > cfg.ninety_day_week_fallback and ninety_values is None:
        ninety = values[-cfg.ninety_day_week_fallback :]

    all_time_low = min(values) if values else None
    ninety_day_low = min(ninety) if ninety else None
    median = _median(values)
    latest = values[-1] if values else None

    bucket = bucket_for_price(
        current_unit_price,
        all_time_low=all_time_low,
        ninety_day_low=ninety_day_low,
        median=median,
        count=len(values),
        thresholds=cfg,
    )

    return HistoricalBenchmark(
        market_all_time_low_unit_price=all_time_low,
        market_90_day_low_unit_price=ninety_day_low,
        market_median_unit_price=median,
        latest_seen_unit_price=latest,
        percent_above_all_time_low=percent_above_all_time_low(current_unit_price, all_time_low),
        percent_below_median=percent_below_median(current_unit_price, median),
        benchmark_bucket=bucket,
        observation_count=len(values),
    )


def compute_benchmark(
    tracker_id: str,
    tracker_kind: str,
    feed_id: str,
    current_unit_price: float | None,
    *,
    week_start: str | None = None,
) -> HistoricalBenchmark:
    canonical_ts, weeks_key, prices_key, family_ts, family_key, _member_key = _feed_files(feed_id)
    weeks, prices = _parse_ts_export(canonical_ts, weeks_key, prices_key)
    _, family_prices = _parse_ts_export(family_ts, "FAMILY_WEEKLY_AD_WEEKS", family_key)

    series = _series_for_tracker(
        tracker_id,
        tracker_kind,
        weeks,
        prices,
        family_prices,
        before_week=week_start,
    )
    values = [price for _, price in series]
    if week_start:
        cutoff = (date.fromisoformat(week_start) - timedelta(days=90)).isoformat()
        ninety_values = [price for week, price in series if week >= cutoff]
    else:
        ninety_values = None

    return compute_benchmark_from_values(
        values,
        current_unit_price,
        ninety_values=ninety_values,
    )
