"""Content scoring and deal bucket assignment."""

from __future__ import annotations

from dataclasses import dataclass

from weekly_ad_analysis.benchmarks import HistoricalBenchmark
from weekly_ad_analysis.costco_match import CostcoMatchResult
from weekly_ad_analysis.matcher import WatchlistMatch


@dataclass(frozen=True)
class ScoredDeal:
    content_score: int
    deal_bucket: str
    confidence: str
    script_angle: str
    skip_reason: str | None
    unit_math_uncertain: bool


def _costco_savings_score(pct: float | None, winner_favors_grocer: bool | None) -> int:
    if pct is None:
        return 0
    if pct >= 20:
        return 5
    if pct >= 5:
        return 3
    if pct >= -5:
        return 2
    if pct < -5:
        return 0
    return 0


def _historical_score(bucket: str) -> int:
    return {
        "all-time low": 5,
        "near all-time low": 4,
        "strong sale": 3,
        "normal sale": 1,
        "weak sale": 0,
        "insufficient history": 0,
    }.get(bucket, 0)


def _deal_bucket(
    *,
    costco: CostcoMatchResult,
    benchmark: HistoricalBenchmark,
    track_costco: bool,
    grocer_wins_costco: bool,
    costco_wins: bool,
    on_par: bool,
) -> str:
    if track_costco and grocer_wins_costco:
        return "Clear win vs Costco"
    if track_costco and on_par:
        return "On par with Costco / grocer wins on variety"
    if not track_costco or costco.match_type == "no comp":
        if benchmark.benchmark_bucket in {"all-time low", "near all-time low", "strong sale"}:
            return "No Costco comp, but historically strong market price"
    if track_costco and costco_wins:
        return "Not a Costco win"
    if benchmark.benchmark_bucket in {"all-time low", "near all-time low", "strong sale"}:
        return "No Costco comp, but historically strong market price"
    return "Skip / not worth highlighting"


def score_deal(
    match: WatchlistMatch,
    *,
    normalized_unit_price: float | None,
    unit_math_uncertain: bool,
    costco: CostcoMatchResult,
    benchmark: HistoricalBenchmark,
    retailer_label: str,
    is_five_dollar_friday: bool,
) -> ScoredDeal:
    pct = costco.percent_difference_vs_costco
    grocer_wins = pct is not None and pct >= 5
    costco_wins = pct is not None and pct < -5
    on_par = pct is not None and -5 <= pct < 5

    score = 0
    if match.content.track_costco_comp:
        score += _costco_savings_score(pct, grocer_wins)
    if match.content.track_historical_low:
        score += _historical_score(benchmark.benchmark_bucket)
    score += match.content.shopper_popularity_score
    score += match.content.content_clarity_score

    if on_par and match.content.default_content_angle and "variety" in match.content.default_content_angle:
        score += 2
    elif on_par:
        score += 1

    if costco.match_confidence == "low":
        score -= 3
    if unit_math_uncertain:
        score -= 2
    if match.match_confidence == "low":
        score -= 2
    if costco_wins and match.content.track_costco_comp:
        score -= 4

    deal_bucket = _deal_bucket(
        costco=costco,
        benchmark=benchmark,
        track_costco=match.content.track_costco_comp,
        grocer_wins_costco=grocer_wins,
        costco_wins=costco_wins,
        on_par=on_par,
    )

    skip_reason = None
    if deal_bucket == "Not a Costco win":
        skip_reason = "Costco clearly cheaper"
    elif deal_bucket == "Skip / not worth highlighting":
        if benchmark.benchmark_bucket == "weak sale":
            skip_reason = "weak historical price"
        elif unit_math_uncertain:
            skip_reason = "unclear size"
        elif match.match_confidence == "low":
            skip_reason = "low confidence match"
        elif match.content.shopper_popularity_score <= 2:
            skip_reason = "not shopper-interesting enough"
        else:
            skip_reason = "too hard to explain"

    confidence = match.match_confidence
    if costco.match_confidence == "low" or unit_math_uncertain:
        confidence = "low" if confidence == "low" else "medium"

    angle = match.content.default_content_angle
    if grocer_wins and match.content.track_costco_comp:
        angle = (
            f"{retailer_label} is actually cheaper than Costco here, and you do not need "
            "to buy the giant bulk pack."
        )
    elif on_par and match.content.track_costco_comp:
        angle = (
            f"This is basically Costco pricing, but {retailer_label} wins because you get "
            "way more flavors."
        )
    elif benchmark.benchmark_bucket in {"all-time low", "near all-time low", "strong sale"}:
        angle = (
            "This is not a perfect Costco comparison, but it is near the lowest price we "
            "have tracked for this category."
        )
    elif costco_wins:
        angle = (
            "This sounds good, but Costco still wins per unit, so I would skip it for the video."
        )

    if is_five_dollar_friday:
        score += 3

    return ScoredDeal(
        content_score=score,
        deal_bucket=deal_bucket,
        confidence=confidence,
        script_angle=angle,
        skip_reason=skip_reason,
        unit_math_uncertain=unit_math_uncertain,
    )
