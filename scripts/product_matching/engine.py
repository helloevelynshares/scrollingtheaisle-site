"""Wrap production weekly-ad matching for dry-run evaluation.

Uses generate_weekly_ad_prices.matches / match_confidence and
canonical_match_eligibility.evaluate_canonical_match — the same logic that
writes tracker prices — without writing any outputs.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_weekly_ad_prices import (  # noqa: E402
    MATCHERS,
    ProductMatcher,
    match_confidence,
    matches,
    split_text,
)
from price_tracker.canonical_families import load_families  # noqa: E402
from price_tracker.canonical_match_eligibility import (  # noqa: E402
    MatchEligibilityResult,
    evaluate_canonical_match,
    load_match_rules,
    merge_family_yaml_rules,
)

DECISION_MAP = {
    "accepted": "accept",
    "rejected": "reject",
    "manual_review": "manual_review",
}


@dataclass(frozen=True)
class FamilyHit:
    family_id: str
    pattern_matched: bool
    matching_phrase: str | None
    matching_pattern: str | None
    exclude_hit: str | None
    keyword_confidence: str | None
    eligibility_decision: str | None
    eligibility_reason: str | None
    reject_reason: str | None
    match_confidence: float | None
    ad_product_type: str | None = None


@dataclass(frozen=True)
class MatchDecision:
    """Outcome of evaluating one offer against production matching logic."""

    offer_text: str
    expected_family_id: str | None
    actual_decision: str
    matched_family_id: str | None
    matching_phrase: str | None
    matching_pattern: str | None
    eligibility_decision: str | None
    eligibility_reason: str | None
    reject_reason: str | None
    confidence: float | None
    keyword_confidence: str | None
    pattern_matched_expected: bool
    accepted_family_ids: tuple[str, ...]
    must_not_violations: tuple[str, ...] = ()
    all_hits: tuple[FamilyHit, ...] = ()
    details: dict[str, Any] = field(default_factory=dict)


class ProductionMatcherFacade:
    """Lazy-loaded wrapper around production YAML matchers + eligibility."""

    def __init__(self) -> None:
        self._families = {f.id: f for f in load_families()}
        self._rules = load_match_rules()
        self._matchers = {m.canonical_id: m for m in MATCHERS}
        self._include_phrases = {
            fid: tuple(fam.include) for fid, fam in self._families.items()
        }

    @property
    def family_ids(self) -> list[str]:
        return list(self._matchers.keys())

    def _find_matching_phrase(
        self, family_id: str, text: str
    ) -> tuple[str | None, str | None]:
        matcher = self._matchers.get(family_id)
        if matcher is None:
            return None, None
        for pattern in matcher.patterns:
            m = re.search(pattern, text)
            if not m:
                continue
            # Prefer a human include phrase that also hits.
            for phrase in self._include_phrases.get(family_id, ()):
                try:
                    from price_tracker.canonical_families import phrase_to_pattern

                    if re.search(phrase_to_pattern(phrase), text):
                        return phrase, pattern
                except Exception:
                    continue
            return m.group(0), pattern
        return None, None

    def _find_exclude_hit(self, matcher: ProductMatcher, row: dict[str, str]) -> str | None:
        text = split_text(row)
        exclude_text = " ".join(
            filter(
                None,
                [
                    text,
                    (row.get("package_text") or "").lower(),
                ],
            )
        )
        for pattern in matcher.exclude_patterns:
            m = re.search(pattern, exclude_text)
            if m:
                return f"{pattern} → {m.group(0)!r}"
        return None

    def evaluate_family(
        self, row: dict[str, str], family_id: str
    ) -> FamilyHit:
        matcher = self._matchers.get(family_id)
        family = self._families.get(family_id)
        if matcher is None or family is None:
            return FamilyHit(
                family_id=family_id,
                pattern_matched=False,
                matching_phrase=None,
                matching_pattern=None,
                exclude_hit=None,
                keyword_confidence=None,
                eligibility_decision="reject",
                eligibility_reason="Unknown family id",
                reject_reason="unknown_family",
                match_confidence=None,
            )

        text = split_text(row)
        include_hit = any(re.search(p, text) for p in matcher.patterns)
        exclude_hit = self._find_exclude_hit(matcher, row) if include_hit else None
        pattern_ok = matches(row, matcher)
        phrase, pattern = (
            self._find_matching_phrase(family_id, text) if include_hit else (None, None)
        )

        if not pattern_ok:
            reason = "include pattern excluded" if include_hit and exclude_hit else "no include pattern hit"
            return FamilyHit(
                family_id=family_id,
                pattern_matched=False,
                matching_phrase=phrase,
                matching_pattern=pattern,
                exclude_hit=exclude_hit,
                keyword_confidence=None,
                eligibility_decision="reject",
                eligibility_reason=reason,
                reject_reason=exclude_hit or reason,
                match_confidence=None,
            )

        keyword_conf = match_confidence(row, matcher)
        rules = merge_family_yaml_rules(family, self._rules)
        elig: MatchEligibilityResult = evaluate_canonical_match(
            row,
            family,
            rules=rules,
            keyword_confidence=keyword_conf or "medium",
        )
        decision = DECISION_MAP.get(elig.match_decision, elig.match_decision)
        return FamilyHit(
            family_id=family_id,
            pattern_matched=True,
            matching_phrase=phrase,
            matching_pattern=pattern,
            exclude_hit=None,
            keyword_confidence=keyword_conf,
            eligibility_decision=decision,
            eligibility_reason=elig.match_reason,
            reject_reason=elig.reject_reason,
            match_confidence=elig.match_confidence,
            ad_product_type=elig.ad_product_type,
        )

    def match_offer(
        self,
        row: dict[str, str],
        *,
        expected_family_id: str | None = None,
        must_not_match_family_ids: tuple[str, ...] = (),
        scan_all_families: bool = True,
    ) -> MatchDecision:
        """Run production matching against one synthetic offer row.

        Primary decision is for ``expected_family_id`` (production path for that
        family). Also scans other families for must_not_match violations and
        optional diagnostics.
        """
        families_to_check: list[str] = []
        if expected_family_id:
            families_to_check.append(expected_family_id)
        for fid in must_not_match_family_ids:
            if fid not in families_to_check:
                families_to_check.append(fid)
        if scan_all_families:
            for fid in self._matchers:
                if fid not in families_to_check:
                    families_to_check.append(fid)

        hits: list[FamilyHit] = []
        for fid in families_to_check:
            # Only fully evaluate expected + must_not + pattern candidates when
            # scanning all (skip expensive eligibility for clear non-hits).
            if (
                scan_all_families
                and fid != expected_family_id
                and fid not in must_not_match_family_ids
            ):
                matcher = self._matchers[fid]
                if not matches(row, matcher):
                    continue
            hits.append(self.evaluate_family(row, fid))

        by_id = {h.family_id: h for h in hits}
        expected_hit = by_id.get(expected_family_id) if expected_family_id else None

        if expected_hit is None:
            actual = "reject"
            matched_family = None
            phrase = pattern = elig_dec = elig_reason = reject = None
            conf = keyword_conf = None
            pattern_matched = False
        else:
            pattern_matched = expected_hit.pattern_matched
            actual = expected_hit.eligibility_decision or "reject"
            matched_family = (
                expected_family_id if expected_hit.pattern_matched else None
            )
            phrase = expected_hit.matching_phrase
            pattern = expected_hit.matching_pattern
            elig_dec = expected_hit.eligibility_decision
            elig_reason = expected_hit.eligibility_reason
            reject = expected_hit.reject_reason
            conf = expected_hit.match_confidence
            keyword_conf = expected_hit.keyword_confidence

        accepted = tuple(
            h.family_id
            for h in hits
            if h.pattern_matched and h.eligibility_decision == "accept"
        )
        violations = tuple(
            fid
            for fid in must_not_match_family_ids
            if by_id.get(fid)
            and by_id[fid].pattern_matched
            and by_id[fid].eligibility_decision == "accept"
        )

        return MatchDecision(
            offer_text=row.get("split_product_text") or row.get("raw_offer_text") or "",
            expected_family_id=expected_family_id,
            actual_decision=actual,
            matched_family_id=matched_family,
            matching_phrase=phrase,
            matching_pattern=pattern,
            eligibility_decision=elig_dec,
            eligibility_reason=elig_reason,
            reject_reason=reject,
            confidence=conf,
            keyword_confidence=keyword_conf,
            pattern_matched_expected=pattern_matched,
            accepted_family_ids=accepted,
            must_not_violations=violations,
            all_hits=tuple(hits),
            details={
                "ad_product_type": expected_hit.ad_product_type if expected_hit else None,
                "exclude_hit": expected_hit.exclude_hit if expected_hit else None,
            },
        )


_FACADE: ProductionMatcherFacade | None = None


def get_facade() -> ProductionMatcherFacade:
    global _FACADE
    if _FACADE is None:
        _FACADE = ProductionMatcherFacade()
    return _FACADE


def match_offer_row(
    row: dict[str, str],
    *,
    expected_family_id: str | None = None,
    must_not_match_family_ids: tuple[str, ...] = (),
) -> MatchDecision:
    return get_facade().match_offer(
        row,
        expected_family_id=expected_family_id,
        must_not_match_family_ids=must_not_match_family_ids,
        scan_all_families=True,
    )
