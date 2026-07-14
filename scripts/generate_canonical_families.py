#!/usr/bin/env python3
"""Generate src/data/canonicalTrackerFamilies.generated.ts from YAML source of truth."""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from price_tracker.canonical_families import (  # noqa: E402
    HOMEPAGE_SECTION_LABELS,
    HOMEPAGE_SECTION_ORDER,
    LEGACY_CANONICAL_TO_FAMILY,
    load_families,
    validate_families,
)

ROOT = SCRIPT_DIR.parent
OUTPUT = ROOT / "src" / "data" / "canonicalTrackerFamilies.generated.ts"
POPULAR_YAML = ROOT / "data" / "popular_this_week.yaml"
EDITORIAL_DIR = ROOT / "data" / "editorial_handpicked_deals"

# Card display order for the editorial Safeway shortlist. The first 8 are the
# default-visible priority cards; the remaining 4 sit behind the expander.
EDITORIAL_SAFEWAY_ORDER: list[str] = [
    "Hass avocados",
    "Berries",
    "Chobani yogurt",
    "Frozen shrimp",
    "Bell peppers",
    "Nestlé Drumstick ice cream",
    "Pork shoulder ribs",
    "Oreo / Nabisco snacks",
    "Doritos / snack bags",
    "Beef chuck short ribs",
    "Sargento cheese",
    "Oreo variety angle",
]


def _empty_popular_extras() -> dict:
    """Editorial-only fields; empty defaults keep YAML/Vons entries backward compatible."""
    return {"subtitle": "", "badge": "", "price": "", "availability": "", "fridayOnly": False}


def _normalize_popular_entries(entries: list | None) -> list[dict]:
    normalized: list[dict] = []
    for entry in entries or []:
        normalized.append(
            {
                "title": entry.get("title", ""),
                "trackerFamilyIds": entry.get("tracker_family_ids")
                or entry.get("trackerFamilyIds")
                or [],
                "reason": entry.get("reason", ""),
                # Optional editorial overrides (curated shortlist cards only).
                "subtitle": entry.get("subtitle") or "",
                "badge": entry.get("badge") or "",
                "price": entry.get("price") or "",
                "availability": entry.get("availability") or "",
                "fridayOnly": bool(
                    entry.get("fridayOnly") or entry.get("friday_only") or False
                ),
                "displayOrder": entry.get("display_order")
                or entry.get("displayOrder")
                or 0,
            }
        )
    return normalized


def load_editorial_safeway(week: str) -> list[dict] | None:
    """Manual editorial handpicked deals (content only: NOT canonical tracker/price data).

    Prices come straight from the owner-provided JSON (effective_price or ad_price);
    nothing here feeds price graphs, history, comparisons, or Supabase seeds.
    Returns None when no editorial file exists for the week (caller falls back to YAML).
    """
    if not week:
        return None
    path = EDITORIAL_DIR / f"{week}_safeway.json"
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as handle:
        raw = json.load(handle)

    order_index = {title: idx for idx, title in enumerate(EDITORIAL_SAFEWAY_ORDER)}
    entries: list[dict] = []
    for deal in raw.get("deals") or []:
        title = deal.get("title", "")
        availability = deal.get("availability") or ""
        friday_only = availability.strip().lower().startswith("friday")
        subtitle = deal.get("subtitle") or ""
        entries.append(
            {
                "title": title,
                # Editorial cards do not link canonical families, they must never
                # pull/alter tracker graph data. Price is the editorial string only.
                "trackerFamilyIds": [],
                "reason": subtitle,
                "subtitle": subtitle,
                "badge": deal.get("badge") or "",
                "price": deal.get("effective_price") or deal.get("ad_price") or "",
                "availability": availability,
                "fridayOnly": friday_only,
                "displayOrder": order_index.get(title, len(EDITORIAL_SAFEWAY_ORDER) + len(entries)) + 1,
            }
        )
    entries.sort(key=lambda item: item["displayOrder"])
    return entries


def load_popular_yaml() -> dict:
    import yaml

    if not POPULAR_YAML.is_file():
        return {"week": "", "stores": {"safeway": [], "vons": []}}
    with POPULAR_YAML.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    stores = raw.get("stores") or {}
    week = raw.get("week") or ""

    # Safeway shortlist prefers the owner-provided editorial JSON for the week
    # (carries manual prices + availability). Falls back to YAML when absent.
    # Vons is always YAML-driven and untouched.
    editorial_safeway = load_editorial_safeway(week)
    safeway_entries = (
        editorial_safeway
        if editorial_safeway is not None
        else _normalize_popular_entries(stores.get("safeway"))
    )

    return {
        "week": week,
        "stores": {
            "safeway": safeway_entries,
            "vons": _normalize_popular_entries(stores.get("vons")),
        },
    }


def render_ts() -> str:
    families = load_families()
    errors = validate_families(families)
    if errors:
        raise SystemExit("YAML validation failed:\n" + "\n".join(errors))

    family_payload = [
        {
            "id": f.id,
            "displayName": f.display_name or f.canonical_tracker_family,
            "subtitle": f.subtitle or f.size_format_subtitle,
            "displayOrder": f.display_order,
            "homepageSection": f.homepage_section,
            "category": f.category,
            "confidence": f.confidence,
            "costcoComparable": True,
            "searchAliases": list(f.include) + [f.canonical_tracker_family],
            "legacyCanonicalIds": [
                legacy
                for legacy, target in LEGACY_CANONICAL_TO_FAMILY.items()
                if target == f.id
            ],
        }
        for f in families
    ]

    sections = [
        {
            "id": section_id,
            "label": HOMEPAGE_SECTION_LABELS[section_id],
            "order": index + 1,
        }
        for index, section_id in enumerate(HOMEPAGE_SECTION_ORDER)
    ]

    popular = load_popular_yaml()
    section_union = "\n".join(f'  | "{s}"' for s in HOMEPAGE_SECTION_ORDER)

    return f"""// AUTO-GENERATED by scripts/generate_canonical_families.py; do not edit by hand.
// Source: data/canonical_tracker_families.yaml

export type HomepageSectionId =
{section_union};

export type CanonicalTrackerFamily = {{
  id: string;
  displayName: string;
  subtitle: string;
  displayOrder: number;
  homepageSection: HomepageSectionId;
  category: string;
  confidence: "high" | "medium" | "low" | "working";
  costcoComparable: boolean;
  searchAliases: string[];
  /** Old canonical_products ids whose historical rows map to this family. */
  legacyCanonicalIds: string[];
}};

export type HomepageSection = {{
  id: HomepageSectionId;
  label: string;
  order: number;
}};

export type PopularThisWeekEntry = {{
  title: string;
  trackerFamilyIds: string[];
  reason: string;
  /** Optional editorial subtitle override (curated shortlist cards). */
  subtitle: string;
  /** Optional editorial badge label override (e.g. FRIDAY, DEAL, MEAT). */
  badge: string;
  /** Curated editorial display price (effective_price or ad_price); empty for YAML/Vons cards. */
  price: string;
  /** Curated availability label, e.g. "Friday-only" or "Full week"; empty for YAML/Vons cards. */
  availability: string;
  /** True when the deal is a Friday-only editorial highlight. */
  fridayOnly: boolean;
  displayOrder: number;
}};

export type PopularThisWeekStore = "safeway" | "vons";

export const HOMEPAGE_SECTIONS: HomepageSection[] = {json.dumps(sections, indent=2)};

export const CANONICAL_TRACKER_FAMILIES: CanonicalTrackerFamily[] = {json.dumps(family_payload, indent=2)};

export const LEGACY_CANONICAL_TO_FAMILY: Record<string, string> = {json.dumps(LEGACY_CANONICAL_TO_FAMILY, indent=2)};

export const POPULAR_THIS_WEEK_WEEK: string = {json.dumps(popular.get("week") or "")};

export const POPULAR_THIS_WEEK: Record<PopularThisWeekStore, PopularThisWeekEntry[]> = {{
  safeway: {json.dumps(popular.get("stores", {}).get("safeway", []), indent=2)},
  vons: {json.dumps(popular.get("stores", {}).get("vons", []), indent=2)},
}};
"""


def main() -> None:
    OUTPUT.write_text(render_ts(), encoding="utf-8")
    families = load_families()
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({len(families)} families)")


if __name__ == "__main__":
    main()
