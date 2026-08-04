"""Bridge parsed shopper fields → production canonical matcher.

Reuses ``product_matching.engine.ProductionMatcherFacade.match_offer``.
Does not duplicate YAML matching or eligibility rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from product_matching.engine import MatchDecision, ProductionMatcherFacade, get_facade
from shopper_query.deterministic_parser import parsed_to_offer_row
from shopper_query.schema import ParsedShopperQuery


@dataclass(frozen=True)
class MatchResult:
    status: str  # matched | ambiguous | no_match | error | unsupported
    matched_family_id: str | None
    candidate_family_ids: tuple[str, ...] = ()
    review_family_ids: tuple[str, ...] = ()
    reason: str | None = None
    matching_phrase: str | None = None
    eligibility_reason: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "matched_family_id": self.matched_family_id,
            "candidate_family_ids": list(self.candidate_family_ids),
            "review_family_ids": list(self.review_family_ids),
            "reason": self.reason,
            "matching_phrase": self.matching_phrase,
            "eligibility_reason": self.eligibility_reason,
            "details": self.details,
        }


def _decision_to_result(decision: MatchDecision) -> MatchResult:
    accepted = tuple(decision.accepted_family_ids)
    review = tuple(
        h.family_id
        for h in decision.all_hits
        if h.pattern_matched and h.eligibility_decision == "manual_review"
    )

    if len(accepted) == 1 and not review:
        hit = next(h for h in decision.all_hits if h.family_id == accepted[0])
        return MatchResult(
            status="matched",
            matched_family_id=accepted[0],
            candidate_family_ids=accepted,
            matching_phrase=hit.matching_phrase,
            eligibility_reason=hit.eligibility_reason,
        )

    if len(accepted) > 1 or (accepted and review):
        return MatchResult(
            status="ambiguous",
            matched_family_id=None,
            candidate_family_ids=accepted or review,
            review_family_ids=review,
            reason="multiple_plausible_trackers",
        )

    if not accepted and len(review) > 1:
        return MatchResult(
            status="ambiguous",
            matched_family_id=None,
            candidate_family_ids=review,
            review_family_ids=review,
            reason="multiple_manual_review_candidates",
        )

    if not accepted and len(review) == 1:
        return MatchResult(
            status="ambiguous",
            matched_family_id=None,
            candidate_family_ids=review,
            review_family_ids=review,
            reason="needs_clarification",
            eligibility_reason=next(
                (
                    h.eligibility_reason
                    for h in decision.all_hits
                    if h.family_id == review[0]
                ),
                None,
            ),
        )

    return MatchResult(
        status="no_match",
        matched_family_id=None,
        reason="no_accepted_tracker",
        details={
            "pattern_hits": [
                {
                    "family_id": h.family_id,
                    "eligibility": h.eligibility_decision,
                    "reason": h.eligibility_reason,
                }
                for h in decision.all_hits
                if h.pattern_matched
            ]
        },
    )


def match_parsed_query(
    parsed: ParsedShopperQuery,
    *,
    facade: ProductionMatcherFacade | None = None,
) -> MatchResult:
    if not parsed.product_text.strip():
        return MatchResult(
            status="error",
            matched_family_id=None,
            reason="empty_product_text",
        )
    try:
        engine = facade or get_facade()
        row = parsed_to_offer_row(parsed)
        decision = engine.match_offer(
            row,
            expected_family_id=None,
            scan_all_families=True,
        )
        return _decision_to_result(decision)
    except Exception as exc:  # noqa: BLE001
        return MatchResult(
            status="error",
            matched_family_id=None,
            reason=f"{type(exc).__name__}: {exc}",
        )
