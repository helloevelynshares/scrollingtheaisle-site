"""Package/form sibling gate for multi-tracker brands.

Brand-only or underspecified shopper queries must clarify when multiple active
trackers share a brand — never silently pick regular/default.
"""

from __future__ import annotations

import re
from functools import lru_cache

from .catalog import ActiveTracker, load_active_trackers
from .language_model import normalize_alias

_PACKAGE_MARKERS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("party_size", re.compile(r"\bparty[\s-]*size\b", re.I)),
    ("family_size", re.compile(r"\bfamily[\s-]*size\b", re.I)),
    ("giant_size", re.compile(r"\bgiant[\s-]*size\b", re.I)),
    ("regular", re.compile(r"\bregular(?:\s+size)?\b", re.I)),
    ("tub", re.compile(r"\btubs?\b", re.I)),
    ("cup", re.compile(r"\bcups?\b", re.I)),
    ("pint", re.compile(r"\bpints?\b", re.I)),
    ("bar", re.compile(r"\b(?:ice\s*cream\s*)?bars?\b|\bnovelties\b", re.I)),
    ("per_lb", re.compile(r"\bper\s*lb\b|/lb\b", re.I)),
    ("shredded", re.compile(r"\bshredded\b", re.I)),
    ("sliced", re.compile(r"\bsliced\b", re.I)),
    ("block", re.compile(r"\bblock\b", re.I)),
    ("multipack", re.compile(r"\bmulti[\s-]*packs?\b|\bvariety\s*packs?\b", re.I)),
)

# Brand + generic category is not enough to pick a package sibling.
_GENERIC_PRODUCT_WORDS = frozenset(
    {
        "cereal",
        "yogurt",
        "chips",
        "cookies",
        "crackers",
        "popcorn",
        "butter",
        "cheese",
        "milk",
        "eggs",
        "bread",
        "snack",
        "snacks",
        "ice",
        "cream",
    }
)


_SIZE_SUFFIXES: tuple[str, ...] = (
    "_bars_novelties",
    "_party_size",
    "_family_size",
    "_giant_size",
    "_regular_bags",
    "_per_cup",
    "_regular",
    "_pints",
    "_tubs",
    "_tub",
    "_cups",
    "_bags",
)


def _family_stem(tracker_id: str) -> str:
    # Explicit package-variant stems that suffix stripping alone cannot unify.
    explicit = {
        "lays_potato_chips_regular": "lays_regular_or_party",
        "lays_party_size": "lays_regular_or_party",
    }
    if tracker_id in explicit:
        return explicit[tracker_id]
    for suffix in _SIZE_SUFFIXES:
        if tracker_id.endswith(suffix):
            return tracker_id[: -len(suffix)]
    return tracker_id


def _keep_separate_links(trackers: list[ActiveTracker]) -> list[tuple[str, str]]:
    """Link trackers when keep_separate text points at another family's display/brand."""
    by_id = {t.id: t for t in trackers}
    links: list[tuple[str, str]] = []
    for t in trackers:
        for phrase in t.keep_separate_from:
            pn = normalize_alias(phrase)
            if not pn or len(pn) < 4:
                continue
            for other in trackers:
                if other.id == t.id:
                    continue
                if normalize_alias(t.brand) != normalize_alias(other.brand):
                    continue
                hay = " ".join(
                    [
                        normalize_alias(other.display_name),
                        normalize_alias(other.id.replace("_", " ")),
                        normalize_alias(
                            str(other.raw_family_fields.get("canonical_tracker_family") or "")
                        ),
                    ]
                )
                if pn in hay or hay in pn:
                    links.append((t.id, other.id))
    return links


@lru_cache(maxsize=1)
def _brand_sibling_map() -> dict[str, tuple[str, ...]]:
    """Group package/form variants via id stem + same-brand keep_separate links."""
    trackers = load_active_trackers()
    parent = {t.id: t.id for t in trackers}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    by_stem: dict[str, list[str]] = {}
    for t in trackers:
        by_stem.setdefault(_family_stem(t.id), []).append(t.id)
    for ids in by_stem.values():
        for other in ids[1:]:
            union(ids[0], other)

    for a, b in _keep_separate_links(trackers):
        union(a, b)

    groups: dict[str, list[str]] = {}
    for t in trackers:
        groups.setdefault(find(t.id), []).append(t.id)
    return {k: tuple(sorted(v)) for k, v in groups.items() if len(v) > 1}



@lru_cache(maxsize=1)
def _tracker_index() -> dict[str, ActiveTracker]:
    return {t.id: t for t in load_active_trackers()}


def clear_package_sibling_cache() -> None:
    _brand_sibling_map.cache_clear()
    _tracker_index.cache_clear()


def brand_siblings(tracker_id: str) -> tuple[str, ...]:
    for _root, ids in _brand_sibling_map().items():
        if tracker_id in ids:
            return ids
    return ()


def multi_family_brands() -> dict[str, tuple[str, ...]]:
    """Return {brand_label: tracker_ids} for reporting."""
    idx = _tracker_index()
    out: dict[str, tuple[str, ...]] = {}
    for stem, ids in _brand_sibling_map().items():
        brand = normalize_alias(idx[ids[0]].brand) if ids and ids[0] in idx else stem
        label = brand
        n = 2
        while label in out:
            label = f"{brand} ({n})"
            n += 1
        out[label] = ids
    return out


def find_brand_only_siblings(product_text: str) -> tuple[str, ...]:
    """If text is bare brand (optional generic noun) of a multi-form family, return ids."""
    norm = normalize_alias(product_text)
    if not norm:
        return ()
    tokens = [t for t in norm.split() if t not in _GENERIC_PRODUCT_WORDS]
    if not tokens:
        return ()
    idx = _tracker_index()
    for _stem, ids in _brand_sibling_map().items():
        brand = normalize_alias(idx[ids[0]].brand)
        brand_tokens = brand.split()
        if tokens == brand_tokens or norm == brand:
            return ids
    return ()


def _marker_hits(text: str) -> set[str]:
    hits: set[str] = set()
    for name, pat in _PACKAGE_MARKERS:
        if pat.search(text or ""):
            hits.add(name)
    return hits


def _tracker_marker_tags(tracker: ActiveTracker) -> set[str]:
    blob = " ".join(
        [
            tracker.id,
            tracker.display_name,
            tracker.product_form,
            " ".join(tracker.include[:8]),
        ]
    ).lower()
    tags: set[str] = set()
    for name, pat in _PACKAGE_MARKERS:
        if pat.search(blob) or name in tracker.id:
            tags.add(name)
    return tags


def _is_brand_level_phrase(phrase: str, tracker: ActiveTracker) -> bool:
    p = normalize_alias(phrase)
    brand = normalize_alias(tracker.brand)
    if not p:
        return True
    if p == brand:
        return True
    # "Cheetos", "General Mills cereal", "Post cereal", "Chobani yogurt"
    tokens = [t for t in p.split() if t not in _GENERIC_PRODUCT_WORDS]
    brand_tokens = brand.split()
    return tokens == brand_tokens or p == normalize_alias(tracker.display_name) and not any(
        m in p for m, _ in _PACKAGE_MARKERS
    ) and set(tokens) <= set(brand_tokens) | _GENERIC_PRODUCT_WORDS


def _line_core(phrase: str) -> tuple[str, ...]:
    noise = {
        "family",
        "size",
        "party",
        "giant",
        "regular",
        "tub",
        "tubs",
        "cup",
        "cups",
        "pint",
        "pints",
        "bag",
        "bags",
        "and",
        "or",
        "the",
        "a",
        "an",
        "of",
        "in",
        "with",
        "for",
    }
    return tuple(t for t in normalize_alias(phrase).split() if t not in noise)


def _distinctive_line_hit(
    norm: str, tracker: ActiveTracker, sibling_ids: tuple[str, ...]
) -> bool:
    """True when a line/flavor include unique to this tracker appears in text."""
    idx = _tracker_index()
    sibling_cores: set[tuple[str, ...]] = set()
    shared: set[str] = set()
    for sid in sibling_ids:
        other = idx.get(sid)
        if other is None or sid == tracker.id:
            continue
        for inc in other.include:
            shared.add(normalize_alias(inc))
            core = _line_core(inc)
            if core:
                sibling_cores.add(core)
    brand = normalize_alias(tracker.brand)
    for inc in tracker.include:
        p = normalize_alias(inc)
        if not p or p in shared or _is_brand_level_phrase(p, tracker):
            continue
        if p == brand:
            continue
        core = _line_core(p)
        if core and core in sibling_cores:
            # Same product line exists on a sibling in another package form.
            continue
        if p in norm or all(tok in norm.split() for tok in p.split() if len(tok) > 2):
            return True
    return False


def score_package_fit(product_text: str, tracker_id: str) -> int:
    """Higher = stronger evidence this package/form tracker is intended.

    For multi-tracker brands, bare brand / brand+category scores 0. Callers treat
    all-zero as ambiguous.
    """
    idx = _tracker_index()
    tracker = idx.get(tracker_id)
    if tracker is None:
        return 0
    siblings = brand_siblings(tracker_id)
    text = product_text or ""
    norm = normalize_alias(text)
    text_marks = _marker_hits(text)
    tracker_marks = _tracker_marker_tags(tracker)
    score = 0

    if len(siblings) > 1:
        # Package markers are the primary disambiguator.
        for m in text_marks & tracker_marks:
            score += 5
        for m in text_marks - tracker_marks:
            score -= 3
        # Distinctive product line (Cheetos Crunchy, Cheerios) on one sibling only.
        if _distinctive_line_hit(norm, tracker, siblings):
            score += 4
        return score

    # Single-tracker brand: allow normal phrase evidence.
    for phrase in (tracker.display_name, *tracker.include[:10], *tracker.aliases[:6]):
        p = normalize_alias(phrase)
        if len(p) < 3:
            continue
        if p == norm or (len(p) >= 6 and p in norm):
            score += 3
    return score


def resolve_package_ambiguity(
    product_text: str,
    matched_family_id: str,
) -> tuple[str, tuple[str, ...]]:
    """Return (decision, candidate_ids) where decision is ok|ambiguous|rematch."""
    siblings = brand_siblings(matched_family_id)
    if len(siblings) <= 1:
        return "ok", (matched_family_id,)

    scores = {sid: score_package_fit(product_text, sid) for sid in siblings}
    best = max(scores.values())
    winners = tuple(sorted(sid for sid, sc in scores.items() if sc == best and sc > 0))
    if len(winners) == 1:
        if winners[0] == matched_family_id:
            return "ok", winners
        return "rematch", winners
    return "ambiguous", siblings
