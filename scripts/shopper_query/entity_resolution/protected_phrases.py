"""Protected multiword phrases that must not fire generic category heuristics."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable

from .catalog import load_active_trackers
from .language_model import (
    CATEGORY_HEURISTIC_TOKENS,
    LIVE_HEURISTIC_CATEGORIES,
    build_language_profiles,
    normalize_alias,
)

# Single-token category words — never valid protected phrases.
BROAD_CATEGORY_TERMS: frozenset[str] = frozenset(
    {
        "chip",
        "chips",
        "cereal",
        "cookie",
        "cookies",
        "cracker",
        "crackers",
        "yogurt",
        "oats",
        "oatmeal",
        "honey",
        "apple",
        "pop",
        "food",
        "cream",
        "butter",
        "cheese",
        "bar",
        "bars",
        "milk",
        "eggs",
        "bread",
        "snack",
        "snacks",
    }
)


@dataclass(frozen=True)
class ProtectedHit:
    phrase: str
    category_token: str
    tracker_ids: tuple[str, ...]


@dataclass
class ProtectedPhraseRegistry:
    """Maps normalized protected phrases → tracker ids + embedded category tokens."""

    phrase_to_trackers: dict[str, tuple[str, ...]]
    phrase_to_categories: dict[str, tuple[str, ...]]
    phrases_longest_first: tuple[str, ...]

    def find_in_text(self, text: str) -> list[ProtectedHit]:
        norm = normalize_alias(text)
        if not norm:
            return []
        hits: list[ProtectedHit] = []
        for phrase in self.phrases_longest_first:
            pat = (
                r"(?<![a-z0-9])"
                + re.escape(phrase).replace(r"\ ", r"\s+")
                + r"(?![a-z0-9])"
            )
            if re.search(pat, norm):
                cats = self.phrase_to_categories.get(phrase) or ()
                for cat in cats or ("",):
                    hits.append(
                        ProtectedHit(
                            phrase=phrase,
                            category_token=cat,
                            tracker_ids=self.phrase_to_trackers.get(phrase, ()),
                        )
                    )
        seen: set[str] = set()
        uniq: list[ProtectedHit] = []
        for h in hits:
            if h.phrase in seen:
                continue
            seen.add(h.phrase)
            uniq.append(h)
        return uniq

    def suppresses_category(self, text: str, category: str) -> bool:
        cat = CATEGORY_HEURISTIC_TOKENS.get(category, category)
        for hit in self.find_in_text(text):
            if hit.category_token == cat:
                return True
            if cat in hit.phrase.split():
                return True
            for tok, mapped in CATEGORY_HEURISTIC_TOKENS.items():
                if mapped == cat and tok in hit.phrase.split():
                    return True
        return False


def _categories_for_phrase(phrase: str) -> tuple[str, ...]:
    cats: list[str] = []
    for tok in re.findall(r"[a-z0-9']+", phrase):
        mapped = CATEGORY_HEURISTIC_TOKENS.get(tok)
        if mapped and mapped not in cats:
            cats.append(mapped)
    return tuple(cats)


def _live_categories_for_phrase(phrase: str) -> tuple[str, ...]:
    return tuple(c for c in _categories_for_phrase(phrase) if c in LIVE_HEURISTIC_CATEGORIES)


def _should_keep_phrase(phrase: str, *, explicit: bool) -> bool:
    n = normalize_alias(phrase)
    if not n or n in BROAD_CATEGORY_TERMS:
        return False
    live = _live_categories_for_phrase(n)
    if live:
        return True
    # Explicit overlays may protect known noun-collision brands without a live
    # chips/cereal token (Goldfish, Smartfood) — suppress-only, no auto-resolve
    # unless a unique tracker id is attached elsewhere.
    if explicit and n in {
        "goldfish",
        "smartfood",
        "skinnypop",
        "skinny pop",
        "apple jacks",
        "honey bunches of oats",
    }:
        return True
    return False


def build_protected_phrase_registry(
    *,
    extra_phrases: Iterable[tuple[str, Iterable[str]]] | None = None,
) -> ProtectedPhraseRegistry:
    """Build registry: live-heuristic phrases + explicit safe overlays only."""
    trackers = load_active_trackers()
    profiles = build_language_profiles(trackers)
    active_ids = {t.id for t in trackers}
    phrase_to_trackers: dict[str, list[str]] = {}
    phrase_to_categories: dict[str, set[str]] = {}

    def _add(phrase: str, tracker_ids: Iterable[str], *, explicit: bool) -> None:
        n = normalize_alias(phrase)
        if not _should_keep_phrase(n, explicit=explicit):
            return
        phrase_to_trackers.setdefault(n, [])
        for tid in tracker_ids:
            if tid and tid in active_ids and tid not in phrase_to_trackers[n]:
                phrase_to_trackers[n].append(tid)
        phrase_to_categories.setdefault(n, set()).update(_categories_for_phrase(n))

    for profile in profiles:
        for phrase in profile.protected_phrases:
            _add(phrase, [profile.tracker_id], explicit=False)

    # Explicit per-tracker YAML/overlay phrases
    from .catalog import _load_family_yaml_extras, _load_overlays

    overlays = _load_overlays()
    yaml_extras = _load_family_yaml_extras()
    for tid, yx in yaml_extras.items():
        for phrase in yx.get("protected_phrases") or []:
            _add(str(phrase), [tid], explicit=True)
    for tid, ov in (overlays.get("trackers") or {}).items():
        for phrase in ov.get("protected_phrases") or []:
            _add(str(phrase), [str(tid)], explicit=True)

    if extra_phrases:
        for phrase, tracker_ids in extra_phrases:
            _add(phrase, tracker_ids, explicit=True)

    for phrase in overlays.get("global_protected_phrases") or []:
        _add(str(phrase), [], explicit=True)

    # Drop phrases that map to multiple trackers from resolve set — keep for
    # suppression only (empty tracker list) when they embed a live token.
    cleaned_trackers: dict[str, list[str]] = {}
    for phrase, tids in phrase_to_trackers.items():
        if len(tids) > 1:
            # Suppression-only: clear tracker binding to avoid exact multi-map.
            cleaned_trackers[phrase] = []
        else:
            cleaned_trackers[phrase] = tids

    frozen_trackers = {k: tuple(v) for k, v in cleaned_trackers.items()}
    frozen_cats = {k: tuple(sorted(v)) for k, v in phrase_to_categories.items()}
    # Keep only phrases that still have live cats or explicit allowlist
    keep = {
        p
        for p in frozen_trackers
        if _should_keep_phrase(p, explicit=True)
    }
    frozen_trackers = {k: v for k, v in frozen_trackers.items() if k in keep}
    frozen_cats = {k: v for k, v in frozen_cats.items() if k in keep}
    longest = tuple(sorted(frozen_trackers.keys(), key=lambda p: (-len(p), p)))
    return ProtectedPhraseRegistry(
        phrase_to_trackers=frozen_trackers,
        phrase_to_categories=frozen_cats,
        phrases_longest_first=longest,
    )


@lru_cache(maxsize=1)
def get_protected_phrase_registry() -> ProtectedPhraseRegistry:
    return build_protected_phrase_registry()


def clear_protected_phrase_cache() -> None:
    get_protected_phrase_registry.cache_clear()
