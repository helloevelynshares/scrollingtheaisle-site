"""Generate catalog-wide entity-resolution eval set from the active tracker catalog."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from shopper_query.entity_resolution.catalog import load_active_trackers
from shopper_query.entity_resolution.language_model import (
    ResolutionClass,
    build_language_profiles,
    normalize_alias,
)
from shopper_query.entity_resolution.package_siblings import brand_siblings, multi_family_brands

ROOT = Path(__file__).resolve().parents[3]
OUT_JSONL = ROOT / "evals" / "entity-resolution" / "catalog-resolution-v1.jsonl"
OUT_META = ROOT / "evals" / "entity-resolution" / "catalog-resolution-v1.meta.json"
OUT_WAIVERS = ROOT / "evals" / "entity-resolution" / "catalog-resolution-waivers.json"
OUT_MULTIFAMILY = ROOT / "docs" / "AISLECHECK_MULTI_FAMILY_BRANDS.md"
OUT_MANUAL = ROOT / "docs" / "AISLECHECK_ENTITY_RESOLUTION_MANUAL_REVIEW.md"


def _case(
    *,
    case_id: str,
    tracker_id: str | None,
    query: str,
    expected_status: str,
    expected_tracker_id: str | None,
    forbidden_tracker_ids: list[str],
    expected_clarification_field: str | None,
    coverage_type: str,
    reason: str,
    source: str,
) -> dict:
    return {
        "id": case_id,
        "tracker_id": tracker_id,
        "query": query,
        "expected_status": expected_status,
        "expected_tracker_id": expected_tracker_id,
        "forbidden_tracker_ids": forbidden_tracker_ids,
        "expected_clarification_field": expected_clarification_field,
        "coverage_type": coverage_type,
        "reason": reason,
        "source": source,
    }


def generate_cases() -> tuple[list[dict], list[dict], dict]:
    trackers = load_active_trackers()
    profiles = {p.tracker_id: p for p in build_language_profiles(trackers)}
    cases: list[dict] = []
    waivers: list[dict] = []

    for t in trackers:
        p = profiles[t.id]
        sibs = [s for s in brand_siblings(t.id) if s != t.id]
        forbidden = list(sibs)

        # 1) Canonical / full-name positive
        full_q = f"Safeway {t.display_name} are $2.49"
        needs_branded_positive = t.id.startswith("sliced_or_shredded_cheese") or (
            " or " in normalize_alias(t.display_name)
        )
        if needs_branded_positive:
            branded = next(
                (
                    a
                    for a in t.aliases
                    if "lucerne" in normalize_alias(a) or "sargento" in normalize_alias(a)
                ),
                None,
            )
            if branded:
                cases.append(
                    _case(
                        case_id=f"{t.id}__branded_positive",
                        tracker_id=t.id,
                        query=f"Safeway {branded} are $2.49",
                        expected_status="continue",
                        expected_tracker_id=t.id,
                        forbidden_tracker_ids=forbidden,
                        expected_clarification_field=None,
                        coverage_type="positive_full",
                        reason="Brand-qualified alias required for this family",
                        source="generated_from_catalog",
                    )
                )
            cases.append(
                _case(
                    case_id=f"{t.id}__full_name_underspecified",
                    tracker_id=t.id,
                    query=full_q,
                    expected_status="clarify_or_unsupported",
                    expected_tracker_id=None,
                    forbidden_tracker_ids=[],
                    expected_clarification_field=None,
                    coverage_type="negative_underspecified",
                    reason="Bare display name is intentionally unresolved",
                    source="generated_from_catalog",
                )
            )
        elif p.resolution_class == ResolutionClass.PACKAGE_CLARIFICATION_REQUIRED and not any(
            x in normalize_alias(t.display_name)
            for x in (
                "party",
                "family",
                "giant",
                "tub",
                "cup",
                "pint",
                "bar",
                "regular",
                "novelty",
            )
        ):
            # Display name alone may be underspecified for package siblings.
            cases.append(
                _case(
                    case_id=f"{t.id}__full_name_clarify",
                    tracker_id=t.id,
                    query=full_q,
                    expected_status="clarify",
                    expected_tracker_id=None,
                    forbidden_tracker_ids=[],
                    expected_clarification_field="product",
                    coverage_type="positive_full_clarify",
                    reason="Display name lacks package cue among multi-form siblings",
                    source="generated_from_catalog",
                )
            )
        else:
            cases.append(
                _case(
                    case_id=f"{t.id}__full_name",
                    tracker_id=t.id,
                    query=full_q,
                    expected_status="continue",
                    expected_tracker_id=t.id,
                    forbidden_tracker_ids=forbidden,
                    expected_clarification_field=None,
                    coverage_type="positive_full",
                    reason="Canonical display name should resolve",
                    source="generated_from_catalog",
                )
            )

        # 2) Alternate / safe-short / punctuation variant
        alt = None
        alt_reason = ""
        if p.protected_phrases:
            alt = p.protected_phrases[0]
            alt_reason = "protected phrase alternate"
        elif p.safe_short_name and p.brand_only_safe:
            alt = p.safe_short_name
            alt_reason = "safe short name"
        elif t.include:
            alt = t.include[0]
            alt_reason = "primary include phrase"
        if alt:
            # Capitalization / punctuation variant
            alt_query = f"Safeway {alt.title().replace(' And ', ' & ')} are $2.49"
            size_cues = (
                "party",
                "family",
                "giant",
                "tub",
                "cup",
                "pint",
                "crunchy",
                "classic",
                "novelty",
                "bar",
                "regular",
            )
            expect_continue = p.resolution_class in {
                ResolutionClass.EXACT_ALIAS_SAFE,
                ResolutionClass.PROTECTED_PHRASE_REQUIRED,
                ResolutionClass.CATEGORY_CONTEXT_REQUIRED,
            }
            if p.resolution_class == ResolutionClass.PACKAGE_CLARIFICATION_REQUIRED:
                expect_continue = any(x in normalize_alias(alt) for x in size_cues)
            if normalize_alias(alt) == normalize_alias(t.brand) and not p.brand_only_safe:
                expect_continue = False
            if " or " in normalize_alias(alt) or normalize_alias(alt) in {
                "sliced or shredded",
                "lucerne",
            }:
                expect_continue = False
            if expect_continue and not (
                p.resolution_class == ResolutionClass.PACKAGE_CLARIFICATION_REQUIRED
                and normalize_alias(alt) == normalize_alias(t.brand)
            ):
                cases.append(
                    _case(
                        case_id=f"{t.id}__alternate",
                        tracker_id=t.id,
                        query=alt_query,
                        expected_status="continue",
                        expected_tracker_id=t.id,
                        forbidden_tracker_ids=forbidden,
                        expected_clarification_field=None,
                        coverage_type="positive_alternate",
                        reason=alt_reason,
                        source="generated_from_catalog",
                    )
                )
            else:
                safer = None
                for cand in list(t.include)[:8]:
                    cn = normalize_alias(cand)
                    if cn == normalize_alias(t.brand) or " or " in cn:
                        continue
                    if sibs and not any(x in cn for x in size_cues):
                        continue
                    if len(cn.split()) >= 2:
                        safer = cand
                        break
                if safer:
                    cases.append(
                        _case(
                            case_id=f"{t.id}__alternate",
                            tracker_id=t.id,
                            query=f"Safeway {safer} are $2.49",
                            expected_status="continue",
                            expected_tracker_id=t.id,
                            forbidden_tracker_ids=forbidden,
                            expected_clarification_field=None,
                            coverage_type="positive_alternate",
                            reason="Size/form-qualified include alternate",
                            source="generated_from_catalog",
                        )
                    )
                else:
                    cases.append(
                        _case(
                            case_id=f"{t.id}__alternate_safe_clarify",
                            tracker_id=t.id,
                            query=alt_query,
                            expected_status="clarify_or_unsupported",
                            expected_tracker_id=None,
                            forbidden_tracker_ids=[t.id] if sibs else [],
                            expected_clarification_field="product",
                            coverage_type="positive_alternate_clarify",
                            reason="Alternate is underspecified for this family",
                            source="generated_from_catalog",
                        )
                    )
        else:
            waivers.append(
                {
                    "tracker_id": t.id,
                    "missing": "positive_alternate",
                    "reason": "No safe short/protected/include alternate available",
                }
            )

        # 3) Nearby negative / ambiguous control
        if sibs:
            cases.append(
                _case(
                    case_id=f"{t.id}__brand_only_control",
                    tracker_id=t.id,
                    query=f"Safeway {t.brand} are $2.49",
                    expected_status="clarify",
                    expected_tracker_id=None,
                    forbidden_tracker_ids=[t.id, *sibs],
                    expected_clarification_field="product",
                    coverage_type="negative_brand_only",
                    reason="Brand-only must clarify among package/form siblings",
                    source="generated_from_catalog",
                )
            )
        else:
            # Cheese-style trackers that need a brand: expect unsupported/clarify, not continue.
            if t.id.startswith("sliced_or_shredded_cheese") or p.resolution_class in {
                ResolutionClass.NATURAL_LANGUAGE_GAP,
                ResolutionClass.NOT_SAFELY_RESOLVABLE,
            }:
                cases.append(
                    _case(
                        case_id=f"{t.id}__underspecified_control",
                        tracker_id=t.id,
                        query=f"Safeway {t.display_name} are $2.49",
                        expected_status="clarify_or_unsupported",
                        expected_tracker_id=None,
                        forbidden_tracker_ids=[],
                        expected_clarification_field=None,
                        coverage_type="negative_underspecified",
                        reason="Requires brand or more detail — do not force continue",
                        source="generated_from_catalog",
                    )
                )
                waivers.append(
                    {
                        "tracker_id": t.id,
                        "missing": "forced_positive_continue",
                        "reason": "Policy: underspecified / category-context tracker",
                    }
                )
            elif t.category.startswith("cereal"):
                cases.append(
                    _case(
                        case_id=f"{t.id}__generic_cereal_control",
                        tracker_id=t.id,
                        query="Safeway cereal are $2.49",
                        expected_status="clarify",
                        expected_tracker_id=None,
                        forbidden_tracker_ids=[t.id],
                        expected_clarification_field="brand",
                        coverage_type="negative_generic_category",
                        reason="Generic cereal must not resolve a brand tracker",
                        source="generated_from_catalog",
                    )
                )
            else:
                # Wrong nearby product: another tracker brand
                other = next((x for x in trackers if x.id != t.id), None)
                if other:
                    cases.append(
                        _case(
                            case_id=f"{t.id}__wrong_brand_control",
                            tracker_id=t.id,
                            query=f"Safeway {other.brand} are $2.49",
                            expected_status="any_non_match",
                            expected_tracker_id=None,
                            forbidden_tracker_ids=[t.id],
                            expected_clarification_field=None,
                            coverage_type="negative_wrong_brand",
                            reason="Must not resolve to this tracker from another brand",
                            source="generated_from_catalog",
                        )
                    )

    # Multi-family stress block
    for brand, ids in sorted(multi_family_brands().items()):
        id_list = list(ids)
        cases.append(
            _case(
                case_id=f"multifamily__{normalize_alias(brand).replace(' ', '_')}__brand_only",
                tracker_id=None,
                query=f"Safeway {brand.title()} are $2.49",
                expected_status="clarify",
                expected_tracker_id=None,
                forbidden_tracker_ids=id_list,
                expected_clarification_field="product",
                coverage_type="multifamily_brand_only",
                reason="Multi-family brand-only must clarify",
                source="generated_multifamily",
            )
        )
        cases.append(
            _case(
                case_id=f"multifamily__{normalize_alias(brand).replace(' ', '_')}__broad_category",
                tracker_id=None,
                query=f"Safeway {brand.title()} snacks are $2.49",
                expected_status="clarify_or_unsupported",
                expected_tracker_id=None,
                forbidden_tracker_ids=id_list,
                expected_clarification_field=None,
                coverage_type="multifamily_broad_category",
                reason="Brand + broad category must not pick a package form",
                source="generated_multifamily",
            )
        )

    # Loop cases
    cases.append(
        _case(
            case_id="loop__generic_chips_repeat",
            tracker_id=None,
            query="Safeway chips are $2.49",
            expected_status="clarify",
            expected_tracker_id=None,
            forbidden_tracker_ids=[],
            expected_clarification_field="brand",
            coverage_type="loop_setup",
            reason="First clarify for loop test",
            source="handwritten_loop",
        )
    )

    meta = {
        "generated_on": date.today().isoformat(),
        "schema_version": "catalog-resolution-v1",
        "active_trackers": len(trackers),
        "case_count": len(cases),
        "waiver_count": len(waivers),
        "coverage_types": {},
    }
    for c in cases:
        meta["coverage_types"][c["coverage_type"]] = (
            meta["coverage_types"].get(c["coverage_type"], 0) + 1
        )
    return cases, waivers, meta


def render_multifamily_doc() -> str:
    lines = [
        "# Multi-family brand clarification expectations",
        "",
        "Brand-only or underspecified queries must **clarify**, never continue.",
        "",
        "| Brand | Tracker IDs | Expected brand-only | Expected options |",
        "|---|---|---|---|",
    ]
    for brand, ids in sorted(multi_family_brands().items()):
        lines.append(
            f"| {brand} | {', '.join(f'`{i}`' for i in ids)} | clarify | "
            f"{', '.join(f'`{i}`' for i in ids)} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_manual_review() -> str:
    trackers = load_active_trackers()
    profiles = {p.tracker_id: p for p in build_language_profiles(trackers)}
    lines = [
        "# Entity-resolution manual review list",
        "",
        "Trackers that should **not** be forced into automatic resolution without "
        "a product-policy decision.",
        "",
    ]
    for t in trackers:
        p = profiles[t.id]
        notes: list[str] = []
        if p.resolution_class == ResolutionClass.PACKAGE_CLARIFICATION_REQUIRED:
            notes.append("overlapping package/form families")
        if p.resolution_class == ResolutionClass.NATURAL_LANGUAGE_GAP:
            notes.append("natural-language gap")
        if p.resolution_class == ResolutionClass.NOT_SAFELY_RESOLVABLE:
            notes.append("not safely resolvable")
        if not p.brand_only_safe and brand_siblings(t.id):
            notes.append("unsafe brand-only alias")
        if "or" in normalize_alias(t.display_name):
            notes.append("ambiguous short/display name")
        if notes:
            lines.append(f"- `{t.id}` ({t.display_name}): {'; '.join(notes)}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    cases, waivers, meta = generate_cases()
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with OUT_JSONL.open("w", encoding="utf-8") as fh:
        for row in cases:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    OUT_META.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    OUT_WAIVERS.write_text(json.dumps(waivers, indent=2) + "\n", encoding="utf-8")
    OUT_MULTIFAMILY.write_text(render_multifamily_doc(), encoding="utf-8")
    OUT_MANUAL.write_text(render_manual_review(), encoding="utf-8")
    print(f"Wrote {OUT_JSONL} ({len(cases)} cases)")
    print(f"Wrote {OUT_META}")
    print(f"Wrote {OUT_WAIVERS} ({len(waivers)} waivers)")
    print(f"Wrote {OUT_MULTIFAMILY}")
    print(f"Wrote {OUT_MANUAL}")


if __name__ == "__main__":
    main()
