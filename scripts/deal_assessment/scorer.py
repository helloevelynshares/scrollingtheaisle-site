"""Map historical benchmarks to a deterministic shopper-facing verdict."""

from __future__ import annotations

from typing import Any

from weekly_ad_analysis.benchmarks import HistoricalBenchmark

from .policy import POLICY_VERSION, history_tier

# Stable machine verdicts (underscore) ← benchmark buckets (space).
BUCKET_TO_VERDICT = {
    "all-time low": "all_time_low",
    "near all-time low": "near_all_time_low",
    "strong sale": "strong_sale",
    "normal sale": "normal_sale",
    "weak sale": "weak_sale",
    "insufficient history": "insufficient_data",
}

VERDICT_LABELS = {
    "all_time_low": "All-time low",
    "near_all_time_low": "Near all-time low",
    "strong_sale": "Strong sale",
    "normal_sale": "Normal sale",
    "weak_sale": "Weak sale",
    "insufficient_data": "Not enough history",
    "insufficient_history": "Not enough history",  # alias
    "limited_data": "Early price signal",
    "not_comparable": "Can’t compare yet",
    "invalid_offer": "Need a clearer price",
}

VERDICT_HEADLINES = {
    "all_time_low": "This looks like an all-time low",
    "near_all_time_low": "This is near the all-time low",
    "strong_sale": "This looks like a strong sale",
    "normal_sale": "This is around a normal sale price",
    "weak_sale": "This isn’t a particularly strong deal",
    "insufficient_data": "We don’t have enough price history yet",
    "insufficient_history": "We don’t have enough price history yet",
    "limited_data": "Early price signal",
    "not_comparable": "We can’t compare this offer yet",
    "invalid_offer": "We need a usable price to check",
}


def verdict_from_bucket(bucket: str) -> str:
    return BUCKET_TO_VERDICT.get(bucket, "insufficient_data")


def label_for_verdict(verdict: str) -> str:
    return VERDICT_LABELS.get(verdict, verdict.replace("_", " ").title())


def headline_for_verdict(verdict: str) -> str:
    return VERDICT_HEADLINES.get(verdict, "Here’s what history shows")


def build_summary(
    *,
    verdict: str,
    unit_price: float | None,
    benchmark: HistoricalBenchmark | None,
    tracker_label: str | None = None,
) -> str:
    name = tracker_label or "this product"
    if verdict in {"insufficient_data", "insufficient_history"}:
        count = benchmark.observation_count if benchmark else 0
        return (
            f"We only have {count} comparable week(s) on file for {name}, "
            "so a grounded verdict isn’t ready yet."
        )
    if verdict == "limited_data":
        count = benchmark.observation_count if benchmark else 0
        bits = [
            "We only have a few comparable prices for this product, "
            "so treat this as directional rather than a confident rating."
        ]
        if unit_price is not None:
            bits.append(f"Your comparable unit price is ${unit_price:.2f}.")
        if benchmark and benchmark.market_all_time_low_unit_price is not None:
            bits.append(
                f"Lowest tracked ad so far: "
                f"${benchmark.market_all_time_low_unit_price:.2f}."
            )
        if benchmark and benchmark.market_median_unit_price is not None:
            bits.append(
                f"Median of those weeks: ${benchmark.market_median_unit_price:.2f}."
            )
        bits.append(f"Based on {count} comparable weeks.")
        return " ".join(bits)
    if verdict == "not_comparable":
        return (
            f"The submitted offer doesn’t line up cleanly with tracked history for {name}."
        )
    if verdict == "invalid_offer" or unit_price is None:
        return "Submit a confirmed price (and buy requirement if it’s a multi-buy) to compare."

    assert benchmark is not None
    bits = [f"Your comparable unit price is ${unit_price:.2f}."]
    if benchmark.market_all_time_low_unit_price is not None:
        bits.append(
            f"All-time low in tracked ads: ${benchmark.market_all_time_low_unit_price:.2f}."
        )
    if benchmark.market_median_unit_price is not None:
        bits.append(
            f"Typical (median) tracked ad price: ${benchmark.market_median_unit_price:.2f}."
        )
    bits.append(f"Based on {benchmark.observation_count} comparable weeks.")
    return " ".join(bits)


def evidence_from_benchmark(
    benchmark: HistoricalBenchmark,
    *,
    unit_price: float | None,
    feed_id: str,
    tracker_id: str,
    history_tier_name: str | None = None,
) -> dict[str, Any]:
    tier = history_tier_name or history_tier(benchmark.observation_count)
    return {
        "comparable_unit_price": unit_price,
        "observation_count": benchmark.observation_count,
        "all_time_low_unit_price": benchmark.market_all_time_low_unit_price,
        "ninety_day_low_unit_price": benchmark.market_90_day_low_unit_price,
        "median_unit_price": benchmark.market_median_unit_price,
        "typical_unit_price": benchmark.market_median_unit_price,
        "latest_seen_unit_price": benchmark.latest_seen_unit_price,
        "percent_above_all_time_low": benchmark.percent_above_all_time_low,
        "percent_below_median": benchmark.percent_below_median,
        "benchmark_bucket": benchmark.benchmark_bucket,
        "history_tier": tier,
        "feed_id": feed_id,
        "tracker_id": tracker_id,
        "policy_version": POLICY_VERSION,
        "scoring": "deterministic_historical_benchmark",
    }
