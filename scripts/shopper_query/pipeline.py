"""End-to-end shopper-query pipeline: optional normalize → parse → match → behavior."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from product_matching.engine import ProductionMatcherFacade, get_facade
from shopper_query.behavior import BehaviorDecision, decide_behavior
from shopper_query.deterministic_parser import parse_shopper_query
from shopper_query.match import MatchResult, match_parsed_query
from shopper_query.normalize import NormalizationResult, normalize_shopper_query
from shopper_query.schema import ParsedShopperQuery


@dataclass
class PipelineResult:
    original_query: str
    query_used: str
    normalized: NormalizationResult | None
    parsed: ParsedShopperQuery
    match: MatchResult
    behavior: BehaviorDecision
    path: str  # "raw" | "normalized"

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_query": self.original_query,
            "query_used": self.query_used,
            "path": self.path,
            "normalization": self.normalized.to_dict() if self.normalized else None,
            "parsed": self.parsed.to_dict(),
            "match": self.match.to_dict(),
            "behavior": self.behavior.to_dict(),
        }


def process_query(
    question: str,
    *,
    apply_normalization: bool = False,
    facade: ProductionMatcherFacade | None = None,
) -> PipelineResult:
    """Run deterministic parse + production matcher (+ optional normalize)."""
    original = question or ""
    norm: NormalizationResult | None = None
    if apply_normalization:
        norm = normalize_shopper_query(original)
        query_used = norm.normalized
        path = "normalized"
    else:
        query_used = original
        path = "raw"

    parsed = parse_shopper_query(query_used)
    match = match_parsed_query(parsed, facade=facade or get_facade())
    behavior = decide_behavior(
        parsed,
        match_status=match.status,
        matched_family_id=match.matched_family_id,
        candidate_family_ids=match.candidate_family_ids,
    )
    return PipelineResult(
        original_query=original,
        query_used=query_used,
        normalized=norm,
        parsed=parsed,
        match=match,
        behavior=behavior,
        path=path,
    )
