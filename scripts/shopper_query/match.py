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
        # Shopper queries: a single manual-review candidate is enough evidence to
        # continue (clarify only for missing price/size). Asking "which product?"
        # with one option created dead-end loops.
        hit = next(h for h in decision.all_hits if h.family_id == review[0])
        return MatchResult(
            status="matched",
            matched_family_id=review[0],
            candidate_family_ids=review,
            review_family_ids=review,
            reason="single_manual_review_elevated",
            matching_phrase=hit.matching_phrase,
            eligibility_reason=hit.eligibility_reason,
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
        result = _decision_to_result(decision)
        if result.status in {"no_match", "error"}:
            from shopper_query.entity_resolution.package_siblings import (
                find_brand_only_siblings,
            )
            from shopper_query.entity_resolution.shopper_aliases import (
                resolve_ambiguous_aliases,
                resolve_unique_alias,
            )

            brand_sibs = find_brand_only_siblings(parsed.product_text)
            if len(brand_sibs) > 1:
                return MatchResult(
                    status="ambiguous",
                    matched_family_id=None,
                    candidate_family_ids=brand_sibs,
                    reason="brand_only_package_ambiguous",
                )

            unique = resolve_unique_alias(parsed.product_text)
            if unique:
                result = MatchResult(
                    status="matched",
                    matched_family_id=unique.tracker_id,
                    candidate_family_ids=(unique.tracker_id,),
                    matching_phrase=unique.phrase,
                    reason="shopper_alias_unique",
                    details={"alias_score": unique.score, "base": result.to_dict()},
                )
            else:
                amb = resolve_ambiguous_aliases(parsed.product_text)
                if len(amb) > 1:
                    ids = tuple(h.tracker_id for h in amb)
                    result = MatchResult(
                        status="ambiguous",
                        matched_family_id=None,
                        candidate_family_ids=ids,
                        reason="shopper_alias_ambiguous",
                        details={
                            "aliases": [
                                {
                                    "id": h.tracker_id,
                                    "phrase": h.phrase,
                                    "score": h.score,
                                }
                                for h in amb
                            ],
                            "base": result.to_dict(),
                        },
                    )

        from shopper_query.entity_resolution.package_siblings import (
            resolve_package_ambiguity,
            score_package_fit,
        )

        # Package/form sibling gate on unique matches.
        if result.status == "matched" and result.matched_family_id:
            decision_kind, candidates = resolve_package_ambiguity(
                parsed.product_text, result.matched_family_id
            )
            if decision_kind == "ambiguous":
                return MatchResult(
                    status="ambiguous",
                    matched_family_id=None,
                    candidate_family_ids=candidates,
                    reason="package_form_ambiguous",
                    details={"base": result.to_dict()},
                )
            if decision_kind == "rematch":
                return MatchResult(
                    status="matched",
                    matched_family_id=candidates[0],
                    candidate_family_ids=candidates,
                    matching_phrase=result.matching_phrase,
                    reason="package_form_rematch",
                    details={"base": result.to_dict()},
                )

        # Disambiguate matcher multi-hits when package cues uniquely pick one sibling.
        if result.status == "ambiguous" and len(result.candidate_family_ids) >= 2:
            scores = {
                sid: score_package_fit(parsed.product_text, sid)
                for sid in result.candidate_family_ids
            }
            best = max(scores.values()) if scores else 0
            winners = tuple(
                sorted(sid for sid, sc in scores.items() if sc == best and sc > 0)
            )
            if len(winners) == 1:
                return MatchResult(
                    status="matched",
                    matched_family_id=winners[0],
                    candidate_family_ids=winners,
                    reason="package_form_disambiguated",
                    details={"scores": scores, "base": result.to_dict()},
                )

        return result
    except Exception as exc:  # noqa: BLE001
        return MatchResult(
            status="error",
            matched_family_id=None,
            reason=f"{type(exc).__name__}: {exc}",
        )
