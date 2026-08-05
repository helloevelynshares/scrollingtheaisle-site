"""Write committed entity-resolution audit artifacts from the live catalog."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from shopper_query.entity_resolution.catalog import (
    catalog_exclusions_report,
    load_active_trackers,
)
from shopper_query.entity_resolution.language_model import build_language_profiles
from shopper_query.entity_resolution.protected_phrases import (
    build_protected_phrase_registry,
)
from shopper_query.entity_resolution.reachability import (
    probe_reachability,
    summarize_reachability,
)
from shopper_query.entity_resolution.collisions import find_collisions

ROOT = Path(__file__).resolve().parents[3]
OUT_JSON = ROOT / "evals" / "entity-resolution" / "tracker-coverage-report.json"
OUT_MD = ROOT / "docs" / "AISLECHECK_TRACKER_LANGUAGE_COVERAGE.md"
OUT_COLLISIONS = ROOT / "evals" / "entity-resolution" / "collision-report.json"


def build_report(*, run_reachability: bool = True) -> dict[str, Any]:
    trackers = load_active_trackers(include_inactive=True)
    active = [t for t in trackers if t.active]
    profiles = build_language_profiles(active)
    registry = build_protected_phrase_registry()
    probes = probe_reachability(trackers=active) if run_reachability else []
    reach = summarize_reachability(probes) if probes else {}
    collisions = find_collisions(trackers=active, profiles=profiles)

    by_class: dict[str, int] = {}
    for p in profiles:
        by_class[p.resolution_class.value] = by_class.get(p.resolution_class.value, 0) + 1

    collision_counts: dict[str, int] = {}
    for c in collisions:
        collision_counts[c.kind] = collision_counts.get(c.kind, 0) + 1

    return {
        "generated_on": date.today().isoformat(),
        "source": "data/canonical_tracker_families.yaml",
        "active_count": len(active),
        "inactive_or_excluded": catalog_exclusions_report(),
        "resolution_class_counts": by_class,
        "protected_phrase_count": len(registry.phrases_longest_first),
        "protected_phrases_sample": list(registry.phrases_longest_first)[:40],
        "reachability": reach,
        "collision_counts": collision_counts,
        "collisions": [c.to_dict() for c in collisions],
        "trackers": [
            {
                **t.to_dict(),
                "language": next(
                    (p.to_dict() for p in profiles if p.tracker_id == t.id),
                    None,
                ),
                "reachable": next(
                    (
                        p.reachable
                        for p in probes
                        if p.tracker_id == t.id and p.probe_kind == "summary"
                    ),
                    None,
                ),
            }
            for t in active
        ],
        "reachability_probes": [p.to_dict() for p in probes if p.probe_kind == "summary"],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# AisleCheck tracker language coverage",
        "",
        f"Generated: **{report['generated_on']}**",
        "",
        "Authoritative source: `data/canonical_tracker_families.yaml` "
        "(this report is derived — do not edit tracker lists by hand).",
        "",
        "## Summary",
        "",
        f"- Active trackers: **{report['active_count']}**",
        f"- Protected phrases: **{report['protected_phrase_count']}**",
        f"- Exclusions: **{len(report.get('inactive_or_excluded') or [])}**",
        "",
        "### Resolution classes",
        "",
    ]
    for cls, n in sorted((report.get("resolution_class_counts") or {}).items()):
        lines.append(f"- `{cls}`: {n}")
    reach = report.get("reachability") or {}
    if reach:
        lines += [
            "",
            "### Reachability (NL probes via production contract)",
            "",
            f"- Reachable: **{reach.get('reachable')}** / {reach.get('active_trackers')}",
            f"- Unreachable: **{reach.get('unreachable')}**",
            "",
        ]
        if reach.get("unreachable_ids"):
            lines.append("Unreachable IDs:")
            for tid in reach["unreachable_ids"]:
                lines.append(f"- `{tid}`")
            lines.append("")

    if report.get("collision_counts"):
        lines += ["", "### Collision inventory", ""]
        for kind, n in sorted((report.get("collision_counts") or {}).items()):
            lines.append(f"- `{kind}`: {n}")
        lines.append("")
        lines.append(
            "Full collision rows: `evals/entity-resolution/collision-report.json`."
        )
        lines.append("")

    lines += [
        "## Per-tracker",
        "",
        "| ID | Display | Class | Brand-only safe | Protected phrases | Reachable |",
        "|---|---|---|---|---|---|",
    ]
    for row in report.get("trackers") or []:
        lang = row.get("language") or {}
        prot = ", ".join((lang.get("protected_phrases") or [])[:3]) or "—"
        lines.append(
            "| `{id}` | {display} | `{cls}` | {bos} | {prot} | {reach} |".format(
                id=row.get("id"),
                display=(row.get("display_name") or "").replace("|", "/"),
                cls=(lang.get("resolution_class") or "—"),
                bos="yes" if lang.get("brand_only_safe") else "no",
                prot=prot.replace("|", "/"),
                reach="yes" if row.get("reachable") else "no",
            )
        )

    if report.get("inactive_or_excluded"):
        lines += ["", "## Exclusions", ""]
        for ex in report["inactive_or_excluded"]:
            lines.append(f"- `{ex['id']}`: {ex['reason']}")

    lines += [
        "",
        "## Notes",
        "",
        "- `exact_alias_safe`: short brand/name uniquely maps to one family.",
        "- `protected_phrase_required`: name embeds a category heuristic token; "
        "multiword phrase must be protected.",
        "- `package_clarification_required`: same brand, multiple package/form trackers.",
        "- Reachability probes use queries like `Safeway <name> are $2.49`. "
        "A `clarify` that already selects the correct tracker counts as reachable.",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    report = build_report(run_reachability=True)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_markdown(report), encoding="utf-8")
    collision_doc = {
        "generated_on": report["generated_on"],
        "source": report["source"],
        "counts": report.get("collision_counts") or {},
        "collisions": report.get("collisions") or [],
    }
    OUT_COLLISIONS.write_text(json.dumps(collision_doc, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_COLLISIONS}")
    reach = report.get("reachability") or {}
    print(
        f"active={report['active_count']} "
        f"protected={report['protected_phrase_count']} "
        f"reachable={reach.get('reachable')}/{reach.get('active_trackers')} "
        f"collisions={len(report.get('collisions') or [])}"
    )


if __name__ == "__main__":
    main()
