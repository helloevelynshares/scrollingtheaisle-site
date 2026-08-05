"""Shopper-facing alias resolution layered on top of production YAML matching.

Uses catalog language profiles and safe short names. Does not change weekly-ad
include/exclude matching. Never resolves brand-only queries when multiple
package/form trackers share the brand.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .catalog import load_active_trackers
from .language_model import (
    ResolutionClass,
    build_language_profiles,
    normalize_alias,
)
from .package_siblings import brand_siblings, resolve_package_ambiguity
from .protected_phrases import get_protected_phrase_registry


@dataclass(frozen=True)
class AliasHit:
    tracker_id: str
    phrase: str
    score: float


def _contains_phrase(text: str, phrase: str) -> bool:
    if not text or not phrase:
        return False
    pat = (
        r"(?<![a-z0-9])"
        + re.escape(phrase).replace(r"\ ", r"\s+")
        + r"(?![a-z0-9])"
    )
    return re.search(pat, text) is not None


def find_alias_hits(product_text: str) -> list[AliasHit]:
    """Return alias hits for a parsed product phrase (normalized)."""
    norm = normalize_alias(product_text)
    if not norm:
        return []

    trackers = load_active_trackers()
    profiles = {p.tracker_id: p for p in build_language_profiles(trackers)}
    registry = get_protected_phrase_registry()

    brand_counts: dict[str, int] = {}
    for t in trackers:
        b = normalize_alias(t.brand)
        if b:
            brand_counts[b] = brand_counts.get(b, 0) + 1

    hits: dict[str, AliasHit] = {}

    # 1) Protected phrases with a unique tracker binding
    for hit in registry.find_in_text(norm):
        if len(hit.tracker_ids) != 1:
            continue
        tid = hit.tracker_ids[0]
        score = 0.95 + min(len(hit.phrase), 40) / 1000.0
        prev = hits.get(tid)
        if prev is None or score > prev.score:
            hits[tid] = AliasHit(tracker_id=tid, phrase=hit.phrase, score=score)

    # 2) Exact-alias-safe / protected short names — never bare brand for
    #    package_clarification_required families OR brands shared by multiple
    #    unrelated trackers (Lucerne cream cheese vs Lucerne yogurt).
    for profile in profiles.values():
        package_family = profile.resolution_class in {
            ResolutionClass.PACKAGE_CLARIFICATION_REQUIRED,
            ResolutionClass.MULTIPLE_TRACKER_CANDIDATES,
        } or len(brand_siblings(profile.tracker_id)) > 1
        brand_n = normalize_alias(profile.brand)
        brand_shared = brand_counts.get(brand_n, 0) > 1

        if package_family:
            candidates = [
                profile.display_name,
                *[
                    a
                    for a in profile.aliases
                    if len(normalize_alias(a).split()) >= 2
                    and normalize_alias(a) != brand_n
                ][:6],
            ]
        elif profile.resolution_class in {
            ResolutionClass.EXACT_ALIAS_SAFE,
            ResolutionClass.PROTECTED_PHRASE_REQUIRED,
        }:
            candidates = [
                profile.safe_short_name or "",
                profile.brand,
                profile.display_name,
                *profile.protected_phrases,
                *profile.aliases[:6],
            ]
        else:
            candidates = [profile.display_name, *profile.protected_phrases]

        for cand in candidates:
            c = normalize_alias(cand or "")
            if len(c) < 3:
                continue
            if not _contains_phrase(norm, c):
                continue
            if c in {
                "butter",
                "chips",
                "cereal",
                "cookies",
                "cheese",
                "eggs",
                "cream",
                "yogurt",
            }:
                continue
            if package_family and c == brand_n:
                continue
            # Shared house brand across unrelated families: require more than brand.
            if brand_shared and c == brand_n:
                continue
            score = 0.85 + min(len(c), 40) / 1000.0
            prev = hits.get(profile.tracker_id)
            if prev is None or score > prev.score:
                hits[profile.tracker_id] = AliasHit(
                    tracker_id=profile.tracker_id, phrase=c, score=score
                )

    return sorted(hits.values(), key=lambda h: (-h.score, h.tracker_id))


def resolve_unique_alias(product_text: str) -> AliasHit | None:
    hits = find_alias_hits(product_text)
    if not hits:
        return None
    if len(hits) == 1:
        hit = hits[0]
    else:
        top = hits[0]
        second = hits[1]
        if top.score < second.score + 0.05:
            return None
        hit = top

    decision, candidates = resolve_package_ambiguity(product_text, hit.tracker_id)
    if decision == "ambiguous":
        return None
    if decision == "rematch":
        return AliasHit(
            tracker_id=candidates[0], phrase=hit.phrase, score=hit.score
        )
    return hit


def resolve_ambiguous_aliases(product_text: str) -> list[AliasHit]:
    hits = find_alias_hits(product_text)
    if len(hits) <= 1:
        # Brand-only multi-package → synthesize ambiguous sibling hits
        if len(hits) == 1:
            decision, candidates = resolve_package_ambiguity(
                product_text, hits[0].tracker_id
            )
            if decision == "ambiguous":
                return [
                    AliasHit(tracker_id=cid, phrase=hits[0].phrase, score=0.5)
                    for cid in candidates
                ]
        return hits
    top = hits[0].score
    return [h for h in hits if h.score >= top - 0.02][:5]
