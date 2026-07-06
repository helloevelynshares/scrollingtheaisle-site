"""Load and validate data/canonical_tracker_families.yaml — source of truth for tracker families."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_YAML_PATH = ROOT / "data" / "canonical_tracker_families.yaml"

HOMEPAGE_GROUP_TO_SECTION: dict[str, str] = {
    "snacks_and_crackers": "stock_up_snacks_and_treats",
    "ice_cream": "stock_up_snacks_and_treats",
    "produce": "fresh_produce",
    "dairy_breakfast_bakery": "dairy_breakfast_bakery",
    "meat_and_seafood": "meat_and_seafood",
    "drinks": "drinks",
}

HOMEPAGE_SECTION_ORDER: tuple[str, ...] = (
    "stock_up_snacks_and_treats",
    "fresh_produce",
    "dairy_breakfast_bakery",
    "meat_and_seafood",
    "drinks",
)

HOMEPAGE_SECTION_LABELS: dict[str, str] = {
    "stock_up_snacks_and_treats": "Stock-up snacks & treats",
    "fresh_produce": "Fresh produce",
    "dairy_breakfast_bakery": "Dairy, breakfast & bakery",
    "meat_and_seafood": "Meat & seafood",
    "drinks": "Drinks",
}

VALID_HOMEPAGE_SECTIONS = set(HOMEPAGE_SECTION_ORDER)

# Old canonical / family ids → new YAML family id (preserve historical weekly/baseline data).
LEGACY_CANONICAL_TO_FAMILY: dict[str, str] = {
    "strawberries": "strawberries_1_2lb",
    "avocados": "hass_avocados_each",
    "doritos_nacho_cheese": "doritos_5_13oz",
    "cheetos_crunchy": "cheetos_regular_bags",
    "coke_zero": "coca_cola_12packs",
    "chobani_greek_yogurt": "chobani_yogurt_per_cup",
    "cheerios": "general_mills_cereal_regular",
    "tillamook_ice_cream": "tillamook_ice_cream",
    "mission_tortilla_chips": "tostitos_tortilla_chips",
    "nature_valley_bars": "nature_valley_bars",
    "fage_greek_yogurt": "fage_tub",
    "haagen_dazs_ice_cream": "haagen_dazs_pints",
    "grapes": "seedless_grapes_per_lb",
    "eggs_18_count": "eggs_dozen_normalized",
    "oreos_sandwich_cookies": "oreo_family_size",
    "kettle_brand_chips": "kettle_brand_chips",
    "ben_jerrys_ice_cream": "ben_jerrys_ice_cream",
    "ritz_crackers_snacks": "ritz_crackers",
    "frito_lay_multipack_chips": "lays_party_size",
    "protein_bars": "quest_bars",
}

REQUIRED_FAMILY_FIELDS = (
    "id",
    "canonical_tracker_family",
    "size_format_subtitle",
    "display_order",
)


@dataclass(frozen=True)
class TrackerFamily:
    id: str
    canonical_tracker_family: str
    size_format_subtitle: str
    display_order: int
    homepage_section: str
    category: str = ""
    include: tuple[str, ...] = ()
    keep_separate_from: tuple[str, ...] = ()
    notes: str = ""
    confidence: str = "working"
    patterns: tuple[str, ...] = ()
    exclude_patterns: tuple[str, ...] = ()
    prefer_patterns: tuple[str, ...] = ()
    normalization: str | None = None


def phrase_to_pattern(phrase: str) -> str:
    """Turn a human include/exclude phrase into a case-insensitive regex."""
    text = phrase.strip().lower()
    if not text:
        return r"$^"
    # Size ranges like "5–13 oz" → flexible dash
    text = text.replace("–", "-").replace("—", "-")
    parts = re.split(r"(\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?)", text)
    escaped_parts: list[str] = []
    for part in parts:
        if re.match(r"\d", part):
            escaped_parts.append(part.replace(" ", r"\s*"))
        else:
            escaped_parts.append(re.escape(part).replace(r"\ ", r"\s+"))
    pattern = "".join(escaped_parts)
    # Word boundaries for short tokens
    if len(text) <= 4 and text.isalpha():
        return rf"\b{pattern}\b"
    return pattern


def build_patterns_from_family(raw: dict[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    family_name = (raw.get("canonical_tracker_family") or "").strip()
    includes = list(raw.get("include") or [])
    if family_name and family_name not in includes:
        includes.insert(0, family_name)

    patterns = tuple(phrase_to_pattern(p) for p in includes if p)
    excludes = tuple(phrase_to_pattern(p) for p in (raw.get("keep_separate_from") or []) if p)
    prefers = ()
    if family_name:
        prefers = (phrase_to_pattern(family_name),)
    return patterns, excludes, prefers


def infer_normalization(family_id: str, notes: str, subtitle: str) -> str | None:
    combined = f"{family_id} {notes} {subtitle}".lower()
    if family_id == "strawberries_1_2lb" or "normalize by lb" in combined and "strawberr" in combined:
        return "strawberries_per_lb"
    if family_id == "seedless_grapes_per_lb" or ("grape" in combined and "per lb" in combined):
        return "per_lb"
    if family_id in ("cherries_per_lb", "peaches_per_lb", "nectarines_per_lb", "plums_per_lb"):
        return "per_lb"
    if family_id == "eggs_dozen_normalized" or "per dozen" in combined or "12-count" in combined:
        return "per_dozen"
    if family_id == "chobani_yogurt_per_cup" or "per cup" in combined and "chobani" in combined:
        return "per_cup"
    if family_id == "butter_16oz" or "16 oz" in combined and "butter" in combined:
        return "per_16oz"
    if family_id == "sliced_or_shredded_cheese_6_8oz":
        return "cheese_6_8oz"
    if family_id in ("quest_bars", "clif_bars"):
        return "per_bar"
    if family_id in ("chicken_breast_per_lb", "chicken_thigh_per_lb", "ribeye_steak", "tri_tip_roast"):
        return "per_lb"
    if "per lb" in subtitle.lower():
        return "per_lb"
    return None


def resolve_homepage_section(raw: dict[str, Any]) -> str:
    if raw.get("homepage_section"):
        return str(raw["homepage_section"])
    group = str(raw.get("homepage_group") or "")
    return HOMEPAGE_GROUP_TO_SECTION.get(group, "stock_up_snacks_and_treats")


def parse_family(raw: dict[str, Any]) -> TrackerFamily:
    patterns, excludes, prefers = build_patterns_from_family(raw)
    family_id = str(raw["id"])
    notes = str(raw.get("notes") or "")
    subtitle = str(raw.get("size_format_subtitle") or "")
    return TrackerFamily(
        id=family_id,
        canonical_tracker_family=str(raw["canonical_tracker_family"]),
        size_format_subtitle=subtitle,
        display_order=int(raw["display_order"]),
        homepage_section=resolve_homepage_section(raw),
        category=str(raw.get("category") or ""),
        include=tuple(raw.get("include") or ()),
        keep_separate_from=tuple(raw.get("keep_separate_from") or ()),
        notes=notes,
        confidence=str(raw.get("confidence") or "working"),
        patterns=patterns,
        exclude_patterns=excludes,
        prefer_patterns=prefers,
        normalization=infer_normalization(family_id, notes, subtitle),
    )


def load_families(path: Path | None = None) -> list[TrackerFamily]:
    yaml_path = path or DEFAULT_YAML_PATH
    with yaml_path.open(encoding="utf-8") as handle:
        doc = yaml.safe_load(handle)
    families = [parse_family(raw) for raw in doc.get("families") or []]
    return sorted(families, key=lambda f: f.display_order)


def validate_families(families: list[TrackerFamily]) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    for family in families:
        for field_name in REQUIRED_FAMILY_FIELDS:
            if not getattr(family, field_name if field_name != "id" else "id"):
                errors.append(f"{family.id or '?'}: missing {field_name}")
        if family.id in seen_ids:
            errors.append(f"duplicate id: {family.id}")
        seen_ids.add(family.id)
        if family.homepage_section not in VALID_HOMEPAGE_SECTIONS:
            errors.append(
                f"{family.id}: invalid homepage_section {family.homepage_section!r}"
            )
        if not family.patterns:
            errors.append(f"{family.id}: no include patterns")
    return errors


def family_ids(families: list[TrackerFamily] | None = None) -> list[str]:
    return [f.id for f in (families or load_families())]


def family_by_id(families: list[TrackerFamily] | None = None) -> dict[str, TrackerFamily]:
    return {f.id: f for f in (families or load_families())}
