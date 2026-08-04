"""Baseline evaluator: raw query → deterministic parser → production matcher."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from product_matching.engine import get_facade  # noqa: E402
from shopper_query.cases import (  # noqa: E402
    DEFAULT_EVAL_PATH,
    DEFAULT_OUTPUT_DIR,
    classify_failures,
    field_matches,
    load_eval_cases,
)
from shopper_query.pipeline import process_query  # noqa: E402

SCORED_FIELDS = (
    "product_text",
    "price",
    "promotion_type",
    "required_quantity",
    "package_size",
)


def score_case(case, result) -> dict[str, Any]:
    parsed = result.parsed.to_dict()
    expected = case.expected_fields

    field_ok: dict[str, bool] = {}
    for field in ("product_text", "price", "promotion_type", "required_quantity"):
        if field in expected:
            field_ok[field] = field_matches(field, expected[field], parsed)
        else:
            field_ok[field] = True

    # Package size: accept text OR value+unit when either is labeled.
    pkg_ok = True
    if any(
        k in expected
        for k in ("package_size_text", "package_size_value", "package_size_unit")
    ):
        checks = []
        for k in ("package_size_text", "package_size_value", "package_size_unit"):
            if k in expected:
                checks.append(field_matches(k, expected[k], parsed))
        pkg_ok = all(checks) if checks else True
    field_ok["package_size"] = pkg_ok

    predicted_tracker = result.match.matched_family_id
    candidates = tuple(result.match.candidate_family_ids or ())
    if case.expected_tracker_id is None:
        # No required tracker id: only fail if the system auto-continues with one.
        if result.behavior.behavior == "continue" and predicted_tracker:
            tracker_ok = False
        else:
            tracker_ok = True
    else:
        tracker_ok = predicted_tracker == case.expected_tracker_id
        # Clarify/invalid cases may surface the right family only as a review
        # candidate (no automatic accept) — count as exact-tracker hit.
        if (
            not tracker_ok
            and predicted_tracker is None
            and case.expected_behavior in {"clarify", "invalid"}
            and len(candidates) == 1
            and candidates[0] == case.expected_tracker_id
        ):
            tracker_ok = True

    behavior_ok = result.behavior.behavior == case.expected_behavior
    safe_ok = (
        result.behavior.automatic_continuation_safe
        == case.automatic_continuation_safe
    )

    # Confident wrong: system would continue with wrong tracker or wrong key fields.
    confident_wrong = False
    if result.behavior.automatic_continuation_safe:
        if case.expected_tracker_id and predicted_tracker != case.expected_tracker_id:
            confident_wrong = True
        if not case.automatic_continuation_safe:
            confident_wrong = True
        if not field_ok.get("price", True) and expected.get("price") is not None:
            confident_wrong = True

    failures = classify_failures(
        field_ok=field_ok,
        tracker_ok=tracker_ok,
        behavior_ok=behavior_ok,
        safe_ok=safe_ok,
        confident_wrong=confident_wrong,
    )

    return {
        "id": case.id,
        "category": case.category,
        "raw_query": case.raw_query,
        "path": result.path,
        "query_used": result.query_used,
        "parsed": parsed,
        "match": result.match.to_dict(),
        "behavior": result.behavior.to_dict(),
        "expected_fields": expected,
        "expected_tracker_id": case.expected_tracker_id,
        "expected_behavior": case.expected_behavior,
        "expected_automatic_continuation_safe": case.automatic_continuation_safe,
        "field_ok": field_ok,
        "tracker_ok": tracker_ok,
        "behavior_ok": behavior_ok,
        "safe_resolution_ok": safe_ok,
        "confident_wrong": confident_wrong,
        "failure_categories": failures,
        "passed": len(failures) == 0,
    }


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows) or 1

    def rate(key: str) -> float:
        return sum(1 for r in rows if r["field_ok"].get(key, False)) / n

    pkg_rate = sum(1 for r in rows if r["field_ok"].get("package_size", False)) / n
    tracker_rate = sum(1 for r in rows if r["tracker_ok"]) / n
    behavior_rate = sum(1 for r in rows if r["behavior_ok"]) / n
    safe_rate = sum(1 for r in rows if r["safe_resolution_ok"]) / n
    # Safe resolution rate per experiment: fraction where system continues safely
    # AND labels say continuation is safe — also report absolute safe-continue rate.
    auto_safe_correct = sum(
        1
        for r in rows
        if r["behavior"]["automatic_continuation_safe"]
        and r["expected_automatic_continuation_safe"]
        and r["tracker_ok"]
    )
    auto_safe_attempts = sum(
        1 for r in rows if r["behavior"]["automatic_continuation_safe"]
    )
    confident_wrong = sum(1 for r in rows if r["confident_wrong"])
    fail_counts = Counter()
    for r in rows:
        for c in r["failure_categories"]:
            fail_counts[c] += 1

    return {
        "total_cases": len(rows),
        "product_text_accuracy": rate("product_text"),
        "price_extraction_accuracy": rate("price"),
        "promotion_type_accuracy": rate("promotion_type"),
        "required_quantity_accuracy": rate("required_quantity"),
        "package_size_accuracy": pkg_rate,
        "exact_tracker_accuracy": tracker_rate,
        "correct_behavior_accuracy": behavior_rate,
        "safe_resolution_rate": safe_rate,
        "safe_continue_correct": auto_safe_correct,
        "safe_continue_attempts": auto_safe_attempts,
        "confident_wrong_interpretation_count": confident_wrong,
        "passed_cases": sum(1 for r in rows if r["passed"]),
        "failure_category_counts": dict(fail_counts),
    }


def run_baseline(
    *,
    cases_path: Path,
    output_dir: Path,
    apply_normalization: bool = False,
) -> dict[str, Any]:
    cases = load_eval_cases(cases_path)
    facade = get_facade()
    rows = []
    for case in cases:
        result = process_query(
            case.raw_query,
            apply_normalization=apply_normalization,
            facade=facade,
        )
        rows.append(score_case(case, result))

    summary = aggregate(rows)
    summary["mode"] = "normalized" if apply_normalization else "baseline_raw"
    summary["cases_path"] = str(cases_path)
    summary["generated_at"] = datetime.now(timezone.utc).isoformat()

    output_dir.mkdir(parents=True, exist_ok=True)
    tag = "normalized" if apply_normalization else "baseline"
    report_path = output_dir / f"{tag}_report.json"
    rows_path = output_dir / f"{tag}_results.jsonl"
    report_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    with rows_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    summary["report_path"] = str(report_path)
    summary["results_path"] = str(rows_path)
    return {"summary": summary, "rows": rows}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases",
        type=Path,
        default=DEFAULT_EVAL_PATH,
        help="JSONL eval path",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for report + row JSONL",
    )
    parser.add_argument(
        "--normalized",
        action="store_true",
        help="Run with normalization layer (usually use eval_compare instead)",
    )
    args = parser.parse_args(argv)
    out = run_baseline(
        cases_path=args.cases,
        output_dir=args.output_dir,
        apply_normalization=args.normalized,
    )
    s = out["summary"]
    print("=== Shopper-query baseline eval ===")
    print(f"Mode:                         {s['mode']}")
    print(f"Total cases:                  {s['total_cases']}")
    print(f"Product-text accuracy:        {s['product_text_accuracy']*100:.1f}%")
    print(f"Price extraction accuracy:    {s['price_extraction_accuracy']*100:.1f}%")
    print(f"Promotion-type accuracy:      {s['promotion_type_accuracy']*100:.1f}%")
    print(f"Required-quantity accuracy:   {s['required_quantity_accuracy']*100:.1f}%")
    print(f"Package-size accuracy:        {s['package_size_accuracy']*100:.1f}%")
    print(f"Exact tracker accuracy:       {s['exact_tracker_accuracy']*100:.1f}%")
    print(f"Correct behavior accuracy:    {s['correct_behavior_accuracy']*100:.1f}%")
    print(f"Safe resolution rate:         {s['safe_resolution_rate']*100:.1f}%")
    print(f"Confident wrong count:        {s['confident_wrong_interpretation_count']}")
    print(f"Report: {s['report_path']}")
    print(f"Rows:   {s['results_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
