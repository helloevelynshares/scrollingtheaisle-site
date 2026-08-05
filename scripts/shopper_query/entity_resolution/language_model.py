"""Derive language profiles and resolution classes from the active catalog."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Iterable

from .catalog import ActiveTracker, load_active_trackers

# Tokens that currently (or soon) drive brand-unspecified / category heuristics.
# Protected phrases are required when a tracker name embeds these tokens.
CATEGORY_HEURISTIC_TOKENS: dict[str, str] = {
    "chip": "chips",
    "chips": "chips",
    "cereal": "cereal",
    "cookie": "cookies",
    "cookies": "cookies",
    "cracker": "crackers",
    "crackers": "crackers",
    "yogurt": "yogurt",
    "oats": "oats",
    "oatmeal": "oats",
    "honey": "honey",
    "apple": "apple",
    "pop": "pop",
    "food": "food",
    "cream": "cream",
    "butter": "butter",
    "cheese": "cheese",
    "bar": "bars",
    "bars": "bars",
}

# Categories the live parser actually fires brand-unspecified heuristics for.
# Protected-phrase registry only auto-includes phrases that embed these.
LIVE_HEURISTIC_CATEGORIES: frozenset[str] = frozenset({"chips", "cereal"})


class ResolutionClass(str, Enum):
    EXACT_ALIAS_SAFE = "exact_alias_safe"
    PROTECTED_PHRASE_REQUIRED = "protected_phrase_required"
    CATEGORY_CONTEXT_REQUIRED = "category_context_required"
    PACKAGE_CLARIFICATION_REQUIRED = "package_clarification_required"
    MULTIPLE_TRACKER_CANDIDATES = "multiple_tracker_candidates"
    NATURAL_LANGUAGE_GAP = "natural_language_gap"
    NOT_SAFELY_RESOLVABLE = "not_safely_resolvable_without_more_detail"


@dataclass(frozen=True)
class LanguageProfile:
    tracker_id: str
    display_name: str
    brand: str
    category: str
    common_full_name: str
    safe_short_name: str | None
    aliases: tuple[str, ...]
    normalized_aliases: tuple[str, ...]
    protected_phrases: tuple[str, ...]
    generic_tokens_in_name: tuple[str, ...]
    punctuation_variants: tuple[str, ...]
    apostrophe_variants: tuple[str, ...]
    spacing_variants: tuple[str, ...]
    brand_only_safe: bool
    clarification_required: bool
    resolution_class: ResolutionClass
    likely_ambiguous_with: tuple[str, ...]
    package_form_notes: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["resolution_class"] = self.resolution_class.value
        return d


def normalize_alias(text: str) -> str:
    t = (text or "").lower().replace("’", "'").replace("‘", "'")
    t = re.sub(r"[®™©!.,]", "", t)
    t = t.replace("&", " and ")
    t = t.replace("-", " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _word_tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", normalize_alias(text))


def _generic_tokens_in(text: str) -> list[str]:
    found: list[str] = []
    for tok in _word_tokens(text):
        cat = CATEGORY_HEURISTIC_TOKENS.get(tok)
        if cat and cat not in found:
            found.append(cat)
    return found


def _variants(name: str) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    base = name.strip()
    punct = tuple(
        dict.fromkeys(
            [
                base,
                base.replace("!", ""),
                base.replace("®", ""),
                base.replace(".", ""),
            ]
        )
    )
    apos = tuple(
        dict.fromkeys(
            [
                base,
                base.replace("'", "’"),
                base.replace("’", "'"),
                base.replace("'", ""),
                base.replace("’", ""),
            ]
        )
    )
    spacing = tuple(
        dict.fromkeys(
            [
                base,
                re.sub(r"\s+", " ", base),
                re.sub(r"\s+", "", base),
                base.replace("-", " "),
                base.replace("-", ""),
            ]
        )
    )
    return punct, apos, spacing


def _brand_share_map(trackers: Iterable[ActiveTracker]) -> dict[str, list[str]]:
    from .package_siblings import _family_stem

    by_stem: dict[str, list[str]] = {}
    for t in trackers:
        stem = _family_stem(t.id)
        by_stem.setdefault(stem, []).append(t.id)
    return by_stem


def _short_name_candidates(tracker: ActiveTracker) -> list[str]:
    cands = [
        tracker.brand,
        tracker.display_name,
        tracker.raw_family_fields.get("canonical_tracker_family", ""),
        *tracker.include[:5],
        *tracker.aliases[:8],
    ]
    out: list[str] = []
    for c in cands:
        n = normalize_alias(str(c))
        if n and n not in out:
            out.append(n)
    return out


def build_language_profile(
    tracker: ActiveTracker,
    *,
    all_trackers: list[ActiveTracker] | None = None,
) -> LanguageProfile:
    from .package_siblings import _family_stem

    peers = all_trackers or [tracker]
    brand_map = _brand_share_map(peers)
    brand_key = normalize_alias(tracker.brand) or normalize_alias(tracker.display_name)
    sibling_key = _family_stem(tracker.id)
    same_brand = [i for i in brand_map.get(sibling_key, []) if i != tracker.id]

    display = tracker.display_name
    generics = _generic_tokens_in(display)
    for inc in tracker.include:
        for g in _generic_tokens_in(inc):
            if g not in generics:
                generics.append(g)

    # Protected phrases for classification: multiword names embedding ANY heuristic
    # token (used for resolution_class). Live registry filters to LIVE categories.
    protected: list[str] = []
    for phrase in (display, tracker.brand, *tracker.include, *tracker.aliases):
        words = _word_tokens(phrase)
        if len(words) < 2:
            continue
        gens = _generic_tokens_in(phrase)
        # Only keep auto phrases that embed a LIVE heuristic token.
        if not any(g in LIVE_HEURISTIC_CATEGORIES for g in gens):
            continue
        norm = normalize_alias(phrase)
        if norm and norm not in protected:
            protected.append(norm)

    # Explicit YAML/overlay protected phrases are always kept when they embed a
    # live heuristic token OR are multiword brand phrases listed by hand.
    for phrase in tracker.protected_phrases:
        norm = normalize_alias(phrase)
        if not norm:
            continue
        gens = _generic_tokens_in(norm)
        words = _word_tokens(norm)
        if any(g in LIVE_HEURISTIC_CATEGORIES for g in gens) or (
            len(words) >= 2 and gens
        ):
            if norm not in protected:
                protected.append(norm)
        elif norm in {
            "chips ahoy",
            "sun chips",
            "goldfish",
            "smartfood",
            "honey bunches of oats",
        }:
            if norm not in protected:
                protected.append(norm)

    brand_words = _word_tokens(tracker.brand)
    if len(brand_words) >= 2 and any(
        g in LIVE_HEURISTIC_CATEGORIES for g in _generic_tokens_in(tracker.brand)
    ):
        b = normalize_alias(tracker.brand)
        if b and b not in protected:
            protected.insert(0, b)

    punct, apos, spacing = _variants(display)
    aliases = tuple(_short_name_candidates(tracker))

    brand_only_safe = bool(brand_key) and len(brand_map.get(sibling_key, [])) == 1
    # Short brand that is also a generic food word is never brand-only safe.
    if brand_key in CATEGORY_HEURISTIC_TOKENS or brand_key in {
        "chips",
        "cereal",
        "cookies",
        "crackers",
        "yogurt",
        "butter",
        "cheese",
        "eggs",
        "milk",
        "bread",
        "rice",
        "pasta",
        "chicken",
        "beef",
        "pork",
        "fish",
        "shrimp",
        "apple",
        "honey",
        "oats",
        "pop",
        "food",
    }:
        brand_only_safe = False

    package_clarify = bool(same_brand) and any(
        p.id != tracker.id
        and normalize_alias(p.brand) == brand_key
        and (p.product_form or p.category) == (tracker.product_form or tracker.category)
        for p in peers
    )
    # Same brand, multiple trackers → package/form clarification typically.
    if same_brand:
        package_clarify = True

    safe_short = None
    if brand_only_safe and tracker.brand:
        safe_short = tracker.brand.strip()
    elif protected:
        # Prefer shortest protected phrase as safe short name.
        safe_short = min(protected, key=len)

    # Natural language gap: no short alias ≤ 3 tokens that isn't the full ad include.
    short_aliases = [a for a in aliases if len(_word_tokens(a)) <= 3]
    nl_gap = not short_aliases

    # Prefer protected-phrase classification whenever the display/brand embeds a
    # category heuristic token (Chips Ahoy → chips), even if the brand is unique.
    # Brand uniqueness alone must not skip the protected-phrase path.
    if package_clarify and same_brand:
        res_class = ResolutionClass.PACKAGE_CLARIFICATION_REQUIRED
        clarification_required = True
    elif protected and generics:
        res_class = ResolutionClass.PROTECTED_PHRASE_REQUIRED
        clarification_required = False
    elif same_brand and not brand_only_safe:
        res_class = ResolutionClass.MULTIPLE_TRACKER_CANDIDATES
        clarification_required = True
    elif brand_only_safe and not same_brand:
        res_class = ResolutionClass.EXACT_ALIAS_SAFE
        clarification_required = False
    elif generics and not protected:
        res_class = ResolutionClass.CATEGORY_CONTEXT_REQUIRED
        clarification_required = True
    elif nl_gap:
        res_class = ResolutionClass.NATURAL_LANGUAGE_GAP
        clarification_required = True
    else:
        res_class = ResolutionClass.EXACT_ALIAS_SAFE
        clarification_required = False

    # Reachability hint later may upgrade NATURAL_LANGUAGE_GAP.

    return LanguageProfile(
        tracker_id=tracker.id,
        display_name=display,
        brand=tracker.brand,
        category=tracker.category,
        common_full_name=display,
        safe_short_name=safe_short,
        aliases=aliases,
        normalized_aliases=tuple(normalize_alias(a) for a in aliases),
        protected_phrases=tuple(protected),
        generic_tokens_in_name=tuple(generics),
        punctuation_variants=punct,
        apostrophe_variants=apos,
        spacing_variants=spacing,
        brand_only_safe=brand_only_safe,
        clarification_required=clarification_required,
        resolution_class=res_class,
        likely_ambiguous_with=tuple(same_brand),
        package_form_notes=tracker.product_form or "",
    )


def build_language_profiles(
    trackers: list[ActiveTracker] | None = None,
) -> list[LanguageProfile]:
    trackers = trackers or load_active_trackers()
    return [build_language_profile(t, all_trackers=trackers) for t in trackers]
