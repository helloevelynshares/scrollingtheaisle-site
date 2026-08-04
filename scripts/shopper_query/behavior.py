"""Map parse + match outcomes to continue | clarify | unsupported | invalid."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from shopper_query.schema import ParsedShopperQuery


@dataclass(frozen=True)
class BehaviorDecision:
    behavior: str  # continue | clarify | unsupported | invalid
    automatic_continuation_safe: bool
    reason: str
    matched_family_id: str | None = None
    candidate_family_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["candidate_family_ids"] = list(self.candidate_family_ids)
        return d


def decide_behavior(
    parsed: ParsedShopperQuery,
    *,
    match_status: str,
    matched_family_id: str | None,
    candidate_family_ids: tuple[str, ...] = (),
) -> BehaviorDecision:
    """Conservative behavior mapping — prefer clarify over silent continue."""

    if parsed.conflicting_prices or parsed.malformed_price:
        return BehaviorDecision(
            behavior="invalid",
            automatic_continuation_safe=False,
            reason="conflicting_or_malformed_price",
            matched_family_id=matched_family_id,
            candidate_family_ids=candidate_family_ids,
        )

    if parsed.unsupported_retailer:
        return BehaviorDecision(
            behavior="unsupported",
            automatic_continuation_safe=False,
            reason="unsupported_retailer",
            matched_family_id=matched_family_id,
            candidate_family_ids=candidate_family_ids,
        )

    if match_status == "unsupported":
        return BehaviorDecision(
            behavior="unsupported",
            automatic_continuation_safe=False,
            reason="product_outside_catalog",
            matched_family_id=matched_family_id,
            candidate_family_ids=candidate_family_ids,
        )

    # Package synonym / brand ambiguity → clarify even if a matcher hit exists.
    blocking_ambiguities = [
        a
        for a in parsed.ambiguities
        if a.startswith("package_synonym_ambiguous")
        or a.startswith("product_brand_unspecified")
    ]
    if blocking_ambiguities and match_status != "matched":
        return BehaviorDecision(
            behavior="clarify",
            automatic_continuation_safe=False,
            reason=blocking_ambiguities[0],
            matched_family_id=matched_family_id,
            candidate_family_ids=candidate_family_ids,
        )
    if blocking_ambiguities and match_status == "matched":
        # Matched despite synonym — still unsafe to auto-continue without size.
        return BehaviorDecision(
            behavior="clarify",
            automatic_continuation_safe=False,
            reason=blocking_ambiguities[0],
            matched_family_id=matched_family_id,
            candidate_family_ids=candidate_family_ids,
        )

    if match_status in {"ambiguous", "needs_review"}:
        return BehaviorDecision(
            behavior="clarify",
            automatic_continuation_safe=False,
            reason="ambiguous_tracker_match",
            matched_family_id=matched_family_id,
            candidate_family_ids=candidate_family_ids,
        )

    if match_status in {"no_match", "error"}:
        # Empty product or unknown item
        if not parsed.product_text.strip():
            return BehaviorDecision(
                behavior="clarify",
                automatic_continuation_safe=False,
                reason="missing_product_text",
                candidate_family_ids=candidate_family_ids,
            )
        return BehaviorDecision(
            behavior="unsupported",
            automatic_continuation_safe=False,
            reason="no_tracker_match",
            candidate_family_ids=candidate_family_ids,
        )

    if match_status == "matched" and matched_family_id:
        # Missing price is clarify for a deal answer, but match itself succeeded.
        if parsed.price is None and "price" in parsed.missing_fields:
            return BehaviorDecision(
                behavior="clarify",
                automatic_continuation_safe=False,
                reason="missing_price",
                matched_family_id=matched_family_id,
                candidate_family_ids=candidate_family_ids,
            )
        if (
            parsed.promotion_type in {"multi_buy", "buy_x_get_y", "bogo"}
            and parsed.required_quantity is None
        ):
            return BehaviorDecision(
                behavior="clarify",
                automatic_continuation_safe=False,
                reason="missing_required_quantity",
                matched_family_id=matched_family_id,
                candidate_family_ids=candidate_family_ids,
            )
        return BehaviorDecision(
            behavior="continue",
            automatic_continuation_safe=True,
            reason="unique_tracker_match",
            matched_family_id=matched_family_id,
            candidate_family_ids=candidate_family_ids,
        )

    return BehaviorDecision(
        behavior="clarify",
        automatic_continuation_safe=False,
        reason="unresolved",
        matched_family_id=matched_family_id,
        candidate_family_ids=candidate_family_ids,
    )
