"""Detect catalog language collisions across the active tracker set."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .catalog import ActiveTracker, load_active_trackers
from .language_model import (
    CATEGORY_HEURISTIC_TOKENS,
    LanguageProfile,
    build_language_profiles,
    normalize_alias,
)


@dataclass(frozen=True)
class Collision:
    kind: str
    phrase: str
    tracker_ids: tuple[str, ...]
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def find_collisions(
    trackers: list[ActiveTracker] | None = None,
    profiles: list[LanguageProfile] | None = None,
) -> list[Collision]:
    trackers = trackers or load_active_trackers()
    profiles = profiles or build_language_profiles(trackers)
    by_id = {t.id: t for t in trackers}
    collisions: list[Collision] = []

    # 1) Shared normalized short aliases across families.
    alias_owners: dict[str, list[str]] = {}
    for p in profiles:
        for alias in set(p.normalized_aliases) | set(p.protected_phrases):
            if len(alias) < 3:
                continue
            alias_owners.setdefault(alias, []).append(p.tracker_id)
    for phrase, ids in sorted(alias_owners.items()):
        uniq = tuple(sorted(set(ids)))
        if len(uniq) > 1:
            collisions.append(
                Collision(
                    kind="shared_alias",
                    phrase=phrase,
                    tracker_ids=uniq,
                    detail="Same shopper alias/protected phrase maps to multiple trackers",
                )
            )

    # 2) Display/brand embeds a category heuristic token.
    for p in profiles:
        if p.generic_tokens_in_name:
            collisions.append(
                Collision(
                    kind="embedded_category_token",
                    phrase=normalize_alias(p.display_name),
                    tracker_ids=(p.tracker_id,),
                    detail=f"embeds tokens: {', '.join(p.generic_tokens_in_name)}",
                )
            )

    # 3) Same brand, multiple package/form trackers.
    brand_map: dict[str, list[str]] = {}
    for t in trackers:
        key = normalize_alias(t.brand) or normalize_alias(t.display_name)
        if key:
            brand_map.setdefault(key, []).append(t.id)
    for brand, ids in sorted(brand_map.items()):
        if len(ids) > 1:
            collisions.append(
                Collision(
                    kind="multi_package_brand",
                    phrase=brand,
                    tracker_ids=tuple(sorted(ids)),
                    detail="Multiple active trackers share this brand",
                )
            )

    # 4) Brand/name is itself a generic food word.
    for p in profiles:
        brand = normalize_alias(p.brand)
        if brand in CATEGORY_HEURISTIC_TOKENS or brand in {
            "chips",
            "cereal",
            "cookies",
            "crackers",
            "butter",
            "cheese",
            "yogurt",
            "eggs",
            "milk",
            "bread",
        }:
            collisions.append(
                Collision(
                    kind="brand_is_generic_food_term",
                    phrase=brand,
                    tracker_ids=(p.tracker_id,),
                    detail="Brand token is an ordinary food/category word",
                )
            )

    # 5) keep_separate peers that resolve to another active tracker id/display/brand.
    for t in trackers:
        for peer_name in t.keep_separate_from:
            peer_norm = normalize_alias(peer_name)
            if not peer_norm or len(peer_norm) < 3:
                continue
            peer_ids = []
            for o in trackers:
                if o.id == t.id:
                    continue
                if peer_norm in {
                    normalize_alias(o.display_name),
                    normalize_alias(o.brand),
                    normalize_alias(o.id.replace("_", " ")),
                }:
                    peer_ids.append(o.id)
            if peer_ids:
                collisions.append(
                    Collision(
                        kind="keep_separate_peer",
                        phrase=peer_norm,
                        tracker_ids=(t.id, *sorted(peer_ids)[:4]),
                        detail=f"{t.id} keep_separate resolves to active tracker(s)",
                    )
                )

    # Deduplicate identical rows.
    seen: set[tuple[Any, ...]] = set()
    uniq: list[Collision] = []
    for c in collisions:
        key = (c.kind, c.phrase, c.tracker_ids)
        if key in seen:
            continue
        seen.add(key)
        # Drop self-only keep_separate noise when peer is only the same id
        if c.kind == "keep_separate_peer" and len(set(c.tracker_ids)) == 1:
            continue
        if c.tracker_ids and c.tracker_ids[0] not in by_id and c.kind != "shared_alias":
            continue
        uniq.append(c)
    return uniq
