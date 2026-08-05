"""Load every active canonical food tracker from repository sources of truth."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from price_tracker.canonical_families import (
    DEFAULT_YAML_PATH,
    TrackerFamily,
    load_families,
)

ROOT = Path(__file__).resolve().parents[3]
MATCH_RULES_PATH = ROOT / "config" / "canonical_match_rules.yaml"
SAFEWAY_HISTORY = ROOT / "src" / "data" / "weeklyAdPrices.generated.ts"
VONS_HISTORY = ROOT / "src" / "data" / "vonsWeeklyAdPrices.generated.ts"
OVERLAYS_PATH = ROOT / "data" / "entity_resolution" / "phrase_overlays.yaml"

# Explicit non-product / infrastructure exclusions (none today — reserved).
EXPLICIT_EXCLUSIONS: dict[str, str] = {}

# Families with confidence values that mean "do not treat as active shopper targets".
INACTIVE_CONFIDENCE = frozenset({"deprecated", "inactive", "internal", "retired"})


@dataclass(frozen=True)
class ActiveTracker:
    id: str
    display_name: str
    brand: str
    category: str
    product_form: str
    include: tuple[str, ...]
    aliases: tuple[str, ...]
    protected_phrases: tuple[str, ...]
    keep_separate_from: tuple[str, ...]
    package_size_constraints: dict[str, Any]
    comparison_unit: str
    retailer_coverage: tuple[str, ...]
    has_safeway_history: bool
    has_vons_history: bool
    active: bool
    exclusion_reason: str | None = None
    raw_family_fields: dict[str, Any] = field(default_factory=dict, compare=False)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("raw_family_fields", None)
        return d


def _infer_brand(family: TrackerFamily) -> str:
    if family.manufacturer_family:
        return family.manufacturer_family.strip()
    name = (family.display_name or family.canonical_tracker_family or "").strip()
    if not name:
        return ""
    # First 1–3 capitalized / proprietary tokens before a generic noun.
    parts = name.replace("’", "'").split()
    brand_parts: list[str] = []
    stop = {
        "potato",
        "chips",
        "cookies",
        "crackers",
        "cereal",
        "yogurt",
        "ice",
        "cream",
        "bars",
        "tortilla",
        "family",
        "party",
        "size",
        "regular",
        "bags",
    }
    for i, part in enumerate(parts):
        low = part.lower().strip(",.&")
        if i > 0 and low in stop:
            break
        brand_parts.append(part.strip(",.&"))
        if len(brand_parts) >= 3:
            break
    return " ".join(brand_parts).strip() or name


def _history_ids_with_obs(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    text = path.read_text(encoding="utf-8")
    # Rough but committed: any `"price": <number>` under a family key block.
    ids: set[str] = set()
    # Split on top-level `"family_id": {`
    for m in re.finditer(
        r'^\s*"([a-z0-9_]+)"\s*:\s*\{',
        text,
        flags=re.M,
    ):
        fid = m.group(1)
        # Look ahead ~4k chars for a non-null price
        window = text[m.end() : m.end() + 8000]
        if re.search(r'"price"\s*:\s*\d', window):
            ids.add(fid)
    return ids


def _load_match_rules() -> dict[str, Any]:
    if not MATCH_RULES_PATH.is_file():
        return {}
    import yaml

    raw = yaml.safe_load(MATCH_RULES_PATH.read_text(encoding="utf-8")) or {}
    return dict(raw.get("families") or {})


def _load_overlays() -> dict[str, Any]:
    if not OVERLAYS_PATH.is_file():
        return {"trackers": {}, "global_protected_phrases": []}
    import yaml

    raw = yaml.safe_load(OVERLAYS_PATH.read_text(encoding="utf-8")) or {}
    return {
        "trackers": dict(raw.get("trackers") or {}),
        "global_protected_phrases": list(raw.get("global_protected_phrases") or []),
    }


def _load_family_yaml_extras(yaml_path: Path | None = None) -> dict[str, dict[str, Any]]:
    """Optional entity-resolution keys on family YAML (ignored by MatcherFamily parse)."""
    import yaml

    path = yaml_path or DEFAULT_YAML_PATH
    if not path.is_file():
        return {}
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out: dict[str, dict[str, Any]] = {}
    for raw in doc.get("families") or []:
        if not isinstance(raw, dict) or not raw.get("id"):
            continue
        fid = str(raw["id"])
        extras: dict[str, Any] = {}
        for key in ("aliases", "protected_phrases"):
            if raw.get(key):
                extras[key] = list(raw[key])
        if isinstance(raw.get("clarification"), dict):
            extras["clarification"] = dict(raw["clarification"])
        if extras:
            out[fid] = extras
    return out


def _aliases_for(
    family: TrackerFamily,
    overlay: dict[str, Any],
    yaml_extras: dict[str, Any] | None = None,
) -> tuple[str, ...]:
    extras: list[str] = []
    yx = yaml_extras or {}
    ov = overlay.get(family.id) or {}
    for source in (yx, ov):
        for key in ("aliases", "protected_phrases"):
            for item in source.get(key) or []:
                if item and str(item) not in extras:
                    extras.append(str(item))
    # Include phrases + display name are the live alias surface today.
    seen = {
        *(family.include or ()),
        family.canonical_tracker_family,
        family.display_name,
    }
    out = [x for x in seen if x]
    for e in extras:
        if e not in out:
            out.append(e)
    return tuple(out)


def load_active_trackers(
    *,
    yaml_path: Path | None = None,
    include_inactive: bool = False,
) -> list[ActiveTracker]:
    """Return active trackers from the canonical YAML catalog.

    Inactive / excluded entries are omitted unless ``include_inactive`` is set,
    in which case they appear with ``active=False`` and an exclusion reason.
    """
    path = yaml_path or DEFAULT_YAML_PATH
    families = load_families(path)
    rules = _load_match_rules()
    overlays = _load_overlays()
    overlay_trackers = overlays["trackers"]
    yaml_extras = _load_family_yaml_extras(path)
    safeway_obs = _history_ids_with_obs(SAFEWAY_HISTORY)
    vons_obs = _history_ids_with_obs(VONS_HISTORY)

    out: list[ActiveTracker] = []
    for fam in families:
        excl = EXPLICIT_EXCLUSIONS.get(fam.id)
        conf = (fam.confidence or "working").strip().lower()
        if conf in INACTIVE_CONFIDENCE:
            excl = excl or f"confidence={conf}"
        active = excl is None
        if not active and not include_inactive:
            continue

        ov = overlay_trackers.get(fam.id) or {}
        yx = yaml_extras.get(fam.id) or {}
        protected = tuple(
            dict.fromkeys(
                [
                    *(yx.get("protected_phrases") or []),
                    *(ov.get("protected_phrases") or []),
                ]
            )
        )
        rule = rules.get(fam.id) or {}
        size_constraints = {}
        if isinstance(rule, dict):
            for k in (
                "allowed_units",
                "disallowed_package_patterns",
                "required_attributes",
                "require_confirmation_keywords",
            ):
                if k in rule:
                    size_constraints[k] = rule[k]
        if fam.match_eligibility:
            size_constraints["yaml_match_eligibility"] = fam.match_eligibility

        coverage = []
        if fam.id in safeway_obs:
            coverage.append("safeway")
        if fam.id in vons_obs:
            coverage.append("vons")
        # Trackers without history still exist for matching; coverage may be empty.

        display = (fam.display_name or fam.canonical_tracker_family).strip()
        out.append(
            ActiveTracker(
                id=fam.id,
                display_name=display,
                brand=_infer_brand(fam),
                category=fam.category or "",
                product_form=fam.package_type or fam.size_format_subtitle or "",
                include=tuple(fam.include or ()),
                aliases=_aliases_for(fam, overlay_trackers, yx),
                protected_phrases=protected,
                keep_separate_from=tuple(fam.keep_separate_from or ()),
                package_size_constraints=size_constraints,
                comparison_unit=(fam.normalization or "each"),
                retailer_coverage=tuple(coverage) or ("safeway", "vons"),
                has_safeway_history=fam.id in safeway_obs,
                has_vons_history=fam.id in vons_obs,
                active=active,
                exclusion_reason=excl,
                raw_family_fields={
                    "canonical_tracker_family": fam.canonical_tracker_family,
                    "size_format_subtitle": fam.size_format_subtitle,
                    "confidence": fam.confidence,
                    "homepage_section": fam.homepage_section,
                },
            )
        )
    return out


def catalog_exclusions_report() -> list[dict[str, str]]:
    """Document every inactive/excluded family when include_inactive=True."""
    rows = load_active_trackers(include_inactive=True)
    return [
        {"id": r.id, "reason": r.exclusion_reason or "active"}
        for r in rows
        if not r.active
    ]
