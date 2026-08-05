"""Orchestrate normalize → history → comparability → deterministic score."""

from __future__ import annotations

from typing import Any

from weekly_ad_analysis.benchmarks import compute_benchmark_from_values

from .comparability import check_comparability
from .history_repository import load_family_meta, load_observation_series
from .models import DealAssessment, SubmittedOffer
from .normalize_offer import normalize_submitted_offer
from .policy import history_tier
from .scorer import (
    build_summary,
    evidence_from_benchmark,
    headline_for_verdict,
    label_for_verdict,
    verdict_from_bucket,
)


def assess_deal(
    tracker_id: str,
    retailer: str,
    submitted_offer: SubmittedOffer | dict[str, Any],
) -> DealAssessment:
    """Assess a confirmed structured offer against tracked historical unit prices.

    Interpretation (free-text → structured fields) must already be done.
    This function never reparses a shopper sentence and never uses an LLM.

    Minimum-history policy (see policy.py):
    - 0–1 comparable weeks → insufficient_data (no verdict)
    - 2–3 weeks → limited_data (evidence only; no strong sale label)
    - 4+ weeks → normal benchmark verdict
    """
    offer = (
        submitted_offer
        if isinstance(submitted_offer, SubmittedOffer)
        else SubmittedOffer.from_mapping(submitted_offer)
    )
    normalized = normalize_submitted_offer(offer)
    comparability = check_comparability(
        tracker_id=tracker_id,
        retailer=retailer,
        offer=offer,
        normalized=normalized,
    )
    meta = load_family_meta(tracker_id.strip()) if tracker_id else None
    tracker_label = None
    if meta:
        tracker_label = f"{meta.get('display_name')} ({meta.get('subtitle')})"

    if normalized.comparable_unit_price is None and "cannot_normalize_unit_price" in (
        comparability.reasons
    ):
        verdict = "invalid_offer"
        return DealAssessment(
            ok=False,
            verdict=verdict,
            verdict_label=label_for_verdict(verdict),
            headline=headline_for_verdict(verdict),
            summary=build_summary(
                verdict=verdict,
                unit_price=None,
                benchmark=None,
                tracker_label=tracker_label,
            ),
            tracker_id=tracker_id,
            retailer=retailer,
            feed_id=comparability.feed_id,
            submitted_offer=offer,
            normalized_offer=normalized,
            comparability=comparability,
            evidence={"scoring": "deterministic_historical_benchmark"},
        )

    if not comparability.ok or not comparability.feed_id:
        if "insufficient_history" in comparability.reasons:
            verdict = "insufficient_data"
        else:
            verdict = "not_comparable"
        observations = (
            load_observation_series(tracker_id, comparability.feed_id)
            if comparability.feed_id
            else []
        )
        values = [o.unit_price for o in observations]
        benchmark = compute_benchmark_from_values(
            values, normalized.comparable_unit_price
        )
        return DealAssessment(
            ok=False,
            verdict=verdict,
            verdict_label=label_for_verdict(verdict),
            headline=headline_for_verdict(verdict),
            summary=build_summary(
                verdict=verdict,
                unit_price=normalized.comparable_unit_price,
                benchmark=benchmark,
                tracker_label=tracker_label,
            ),
            tracker_id=tracker_id,
            retailer=retailer,
            feed_id=comparability.feed_id,
            submitted_offer=offer,
            normalized_offer=normalized,
            comparability=comparability,
            evidence=evidence_from_benchmark(
                benchmark,
                unit_price=normalized.comparable_unit_price,
                feed_id=comparability.feed_id or "",
                tracker_id=tracker_id,
            ),
            recent_observations=tuple(observations[-5:]),
        )

    observations = load_observation_series(tracker_id, comparability.feed_id)
    values = [o.unit_price for o in observations]
    benchmark = compute_benchmark_from_values(
        values, normalized.comparable_unit_price
    )
    tier = history_tier(len(values))

    if tier == "insufficient_data":
        verdict = "insufficient_data"
        return DealAssessment(
            ok=False,
            verdict=verdict,
            verdict_label=label_for_verdict(verdict),
            headline=headline_for_verdict(verdict),
            summary=build_summary(
                verdict=verdict,
                unit_price=normalized.comparable_unit_price,
                benchmark=benchmark,
                tracker_label=tracker_label,
            ),
            tracker_id=tracker_id,
            retailer=retailer,
            feed_id=comparability.feed_id,
            submitted_offer=offer,
            normalized_offer=normalized,
            comparability=comparability,
            evidence=evidence_from_benchmark(
                benchmark,
                unit_price=normalized.comparable_unit_price,
                feed_id=comparability.feed_id,
                tracker_id=tracker_id,
                history_tier_name=tier,
            ),
            recent_observations=tuple(observations[-5:]),
        )

    if tier == "limited_data":
        verdict = "limited_data"
        return DealAssessment(
            ok=True,
            verdict=verdict,
            verdict_label=label_for_verdict(verdict),
            headline=headline_for_verdict(verdict),
            summary=build_summary(
                verdict=verdict,
                unit_price=normalized.comparable_unit_price,
                benchmark=benchmark,
                tracker_label=tracker_label,
            ),
            tracker_id=tracker_id,
            retailer=retailer,
            feed_id=comparability.feed_id,
            submitted_offer=offer,
            normalized_offer=normalized,
            comparability=comparability,
            evidence=evidence_from_benchmark(
                benchmark,
                unit_price=normalized.comparable_unit_price,
                feed_id=comparability.feed_id,
                tracker_id=tracker_id,
                history_tier_name=tier,
            ),
            recent_observations=tuple(observations[-5:]),
        )

    verdict = verdict_from_bucket(benchmark.benchmark_bucket)
    return DealAssessment(
        ok=True,
        verdict=verdict,
        verdict_label=label_for_verdict(verdict),
        headline=headline_for_verdict(verdict),
        summary=build_summary(
            verdict=verdict,
            unit_price=normalized.comparable_unit_price,
            benchmark=benchmark,
            tracker_label=tracker_label,
        ),
        tracker_id=tracker_id,
        retailer=retailer,
        feed_id=comparability.feed_id,
        submitted_offer=offer,
        normalized_offer=normalized,
        comparability=comparability,
        evidence=evidence_from_benchmark(
            benchmark,
            unit_price=normalized.comparable_unit_price,
            feed_id=comparability.feed_id,
            tracker_id=tracker_id,
            history_tier_name=tier,
        ),
        recent_observations=tuple(observations[-5:]),
    )


def assess_deal_dict(
    tracker_id: str,
    retailer: str,
    submitted_offer: dict[str, Any],
) -> dict[str, Any]:
    """JSON-friendly wrapper for HTTP adapters."""
    return assess_deal(tracker_id, retailer, submitted_offer).to_dict()
