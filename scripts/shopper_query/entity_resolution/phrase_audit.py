"""Audit and validate protected phrases for AisleCheck entity resolution."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .catalog import (
    OVERLAYS_PATH,
    _load_family_yaml_extras,
    _load_overlays,
    load_active_trackers,
)
from .language_model import (
    LIVE_HEURISTIC_CATEGORIES,
    build_language_profiles,
    normalize_alias,
)
from .package_siblings import brand_siblings, multi_family_brands
from .protected_phrases import (
    BROAD_CATEGORY_TERMS,
    build_protected_phrase_registry,
    clear_protected_phrase_cache,
)

ROOT = Path(__file__).resolve().parents[3]
OUT_JSON = ROOT / "evals" / "entity-resolution" / "protected-phrase-audit.json"
OUT_MD = ROOT / "docs" / "AISLECHECK_PROTECTED_PHRASE_AUDIT.md"


@dataclass(frozen=True)
class PhraseAuditRow:
    phrase: str
    source: str
    tracker_ids: tuple[str, ...]
    resolves_tracker: bool
    suppresses_only: bool
    collision_count: int
    multi_tracker_brand: bool
    package_clarification_required: bool
    risk: str
    live_categories: tuple[str, ...]
    validation_errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["tracker_ids"] = list(self.tracker_ids)
        d["live_categories"] = list(self.live_categories)
        d["validation_errors"] = list(self.validation_errors)
        return d


def _source_for_phrase(phrase: str, tracker_ids: tuple[str, ...]) -> str:
    n = normalize_alias(phrase)
    overlays = _load_overlays()
    globals_ = {normalize_alias(p) for p in overlays.get("global_protected_phrases") or []}
    if n in globals_:
        return "manual_overlay"
    yaml_extras = _load_family_yaml_extras()
    for tid in tracker_ids:
        yx = yaml_extras.get(tid) or {}
        for p in yx.get("protected_phrases") or []:
            if normalize_alias(str(p)) == n:
                return "canonical_alias"
        ov = (overlays.get("trackers") or {}).get(tid) or {}
        for p in ov.get("protected_phrases") or []:
            if normalize_alias(str(p)) == n:
                return "manual_overlay"
    trackers = {t.id: t for t in load_active_trackers()}
    for tid in tracker_ids:
        t = trackers.get(tid)
        if not t:
            continue
        if normalize_alias(t.display_name) == n:
            return "canonical_display_name"
        if normalize_alias(t.brand) == n:
            return "canonical_alias"
    return "generated_catalog_phrase"


def _live_cats(phrase: str) -> tuple[str, ...]:
    cats: list[str] = []
    for tok in re.findall(r"[a-z0-9']+", phrase):
        # LIVE set only
        from .language_model import CATEGORY_HEURISTIC_TOKENS

        mapped = CATEGORY_HEURISTIC_TOKENS.get(tok)
        if mapped in LIVE_HEURISTIC_CATEGORIES and mapped not in cats:
            cats.append(mapped)
    return tuple(cats)


def audit_protected_phrases() -> list[PhraseAuditRow]:
    clear_protected_phrase_cache()
    registry = build_protected_phrase_registry()
    active_ids = {t.id for t in load_active_trackers()}
    profiles = {p.tracker_id: p for p in build_language_profiles()}
    multi = multi_family_brands()
    rows: list[PhraseAuditRow] = []

    for phrase in registry.phrases_longest_first:
        tids = registry.phrase_to_trackers.get(phrase) or ()
        errors: list[str] = []
        if phrase in BROAD_CATEGORY_TERMS or phrase in LIVE_HEURISTIC_CATEGORIES:
            errors.append("broad_category_term")
        missing = [t for t in tids if t not in active_ids]
        if missing:
            errors.append(f"nonexistent_tracker:{','.join(missing)}")
        collision = len(tids)
        if collision > 1:
            # Multi-tracker phrase must not be treated as exact resolve
            errors.append("maps_to_multiple_trackers")
        multi_brand = False
        package_req = False
        for tid in tids:
            sibs = brand_siblings(tid)
            if len(sibs) > 1:
                multi_brand = True
                package_req = True
            prof = profiles.get(tid)
            if prof and prof.resolution_class.value == "package_clarification_required":
                package_req = True
        # Bypass package boundary if phrase resolves uniquely despite multi-brand
        resolves = collision == 1 and not package_req
        if collision == 1 and package_req and phrase == normalize_alias(
            (profiles.get(tids[0]).brand if profiles.get(tids[0]) else "") or ""
        ):
            errors.append("bypasses_package_form_boundary")
        live = _live_cats(phrase)
        # Overlay phrases with no live cats and no tracker are suppress-only globals
        if not live and not tids and _source_for_phrase(phrase, tids) == "manual_overlay":
            # Allowed only if phrase embeds a future-risk token from CATEGORY map
            from .language_model import CATEGORY_HEURISTIC_TOKENS

            embedded = any(
                CATEGORY_HEURISTIC_TOKENS.get(tok)
                for tok in phrase.split()
            )
            if not embedded and phrase not in {"goldfish", "smartfood", "skinnypop", "skinny pop"}:
                errors.append("unnecessary_no_heuristic_token")
        if not live and tids and _source_for_phrase(phrase, tids) == "generated_catalog_phrase":
            errors.append("unnecessary_generated_without_live_heuristic")

        if errors and "broad_category_term" in errors:
            risk = "broad_phrase"
        elif collision > 1:
            risk = "collision"
        elif errors:
            risk = "requires_manual_review"
        else:
            risk = "safe_exact_phrase"

        rows.append(
            PhraseAuditRow(
                phrase=phrase,
                source=_source_for_phrase(phrase, tids),
                tracker_ids=tids,
                resolves_tracker=resolves,
                suppresses_only=not resolves,
                collision_count=collision,
                multi_tracker_brand=multi_brand,
                package_clarification_required=package_req,
                risk=risk,
                live_categories=live,
                validation_errors=tuple(errors),
            )
        )
    return rows


def validation_failures(rows: list[PhraseAuditRow] | None = None) -> list[PhraseAuditRow]:
    rows = rows or audit_protected_phrases()
    hard = {
        "broad_category_term",
        "maps_to_multiple_trackers",
        "bypasses_package_form_boundary",
        "nonexistent_tracker",
        "unnecessary_generated_without_live_heuristic",
    }
    out: list[PhraseAuditRow] = []
    for r in rows:
        if any(
            e in hard or e.startswith("nonexistent_tracker") for e in r.validation_errors
        ):
            out.append(r)
    return out


def build_report() -> dict[str, Any]:
    rows = audit_protected_phrases()
    failures = validation_failures(rows)
    risk_counts: dict[str, int] = {}
    for r in rows:
        risk_counts[r.risk] = risk_counts.get(r.risk, 0) + 1
    return {
        "generated_on": date.today().isoformat(),
        "source": "data/canonical_tracker_families.yaml + data/entity_resolution/phrase_overlays.yaml",
        "phrase_count": len(rows),
        "risk_counts": risk_counts,
        "validation_failure_count": len(failures),
        "validation_failures": [r.to_dict() for r in failures],
        "phrases": [r.to_dict() for r in rows],
        "overlays_path_tracked": True,
        "overlays_path": str(OVERLAYS_PATH.relative_to(ROOT)),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# AisleCheck protected-phrase audit",
        "",
        f"Generated: **{report['generated_on']}**",
        "",
        f"- Phrase count: **{report['phrase_count']}**",
        f"- Validation failures: **{report['validation_failure_count']}**",
        "",
        "### Risk counts",
        "",
    ]
    for k, n in sorted((report.get("risk_counts") or {}).items()):
        lines.append(f"- `{k}`: {n}")
    lines += [
        "",
        "| Phrase | Source | Trackers | Resolves | Suppress only | Collisions | Multi-brand | Package clarify | Risk | Errors |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in report.get("phrases") or []:
        lines.append(
            "| `{phrase}` | {src} | {tids} | {res} | {sup} | {col} | {mb} | {pkg} | `{risk}` | {err} |".format(
                phrase=r["phrase"],
                src=r["source"],
                tids=", ".join(f"`{t}`" for t in r["tracker_ids"]) or "—",
                res="yes" if r["resolves_tracker"] else "no",
                sup="yes" if r["suppresses_only"] else "no",
                col=r["collision_count"],
                mb="yes" if r["multi_tracker_brand"] else "no",
                pkg="yes" if r["package_clarification_required"] else "no",
                risk=r["risk"],
                err=", ".join(r["validation_errors"]) or "—",
            )
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    report = build_report()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    print(
        f"phrases={report['phrase_count']} failures={report['validation_failure_count']} "
        f"risks={report['risk_counts']}"
    )
    if report["validation_failure_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
