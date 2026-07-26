#!/usr/bin/env python3
"""Dry-run product-matching evaluation against labeled cases.

Invokes the current production matching logic (YAML patterns + eligibility)
without writing generated TypeScript, CSV files, or Supabase records.

Usage:
  PYTHONPATH=scripts python3 -m product_matching.eval_runner
  PYTHONPATH=scripts python3 -m product_matching.eval_runner --json
  PYTHONPATH=scripts python3 -m product_matching.eval_runner --failures-only
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from product_matching.aliases import open_baseline_bugs  # noqa: E402
from product_matching.cases import DEFAULT_EVAL_CASES_PATH, load_eval_cases  # noqa: E402
from product_matching.engine import get_facade  # noqa: E402
from product_matching.metrics import EvalReport, evaluate_case  # noqa: E402


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def _rule_responsible(decision) -> str:
    parts: list[str] = []
    if decision.matching_phrase:
        parts.append(f"include phrase: {decision.matching_phrase!r}")
    elif decision.matching_pattern:
        parts.append(f"pattern: {decision.matching_pattern}")
    exclude = (decision.details or {}).get("exclude_hit")
    if exclude:
        parts.append(f"exclude: {exclude}")
    if decision.eligibility_reason:
        parts.append(f"eligibility: {decision.eligibility_reason}")
    if decision.reject_reason:
        parts.append(f"reject: {decision.reject_reason}")
    return "; ".join(parts) if parts else "(no pattern / no eligibility detail)"


def run_eval(cases_path: Path) -> EvalReport:
    cases = load_eval_cases(cases_path)
    facade = get_facade()
    results = []
    for case in cases:
        decision = facade.match_offer(
            case.to_offer_row(),
            expected_family_id=case.expected_family_id,
            must_not_match_family_ids=case.must_not_match_family_ids,
            # Only expected + must_not families (production path per family).
            scan_all_families=False,
        )
        results.append(evaluate_case(case, decision))

    baseline = [
        {
            "id": c.id,
            "family_id": c.family_id,
            "offer_text": c.offer_text,
            "status": c.status,
            "notes": c.notes,
            "source": c.source,
        }
        for c in open_baseline_bugs()
    ]
    return EvalReport(results=results, open_baseline_bugs=baseline)


def print_report(report: EvalReport, *, failures_only: bool = False) -> None:
    s = report.summary_dict()
    if not failures_only:
        print("=== Product matching eval (dry-run, production logic) ===")
        print(f"Total cases:                    {s['total_cases']}")
        print(f"Correct accepts:                {s['correct_accepts']}")
        print(f"Correct rejects:                {s['correct_rejects']}")
        print(f"Incorrect automatic accepts:    {s['incorrect_automatic_accepts']}")
        print(f"Incorrect rejects:              {s['incorrect_rejects']}")
        print(f"Manual-review decisions:        {s['manual_review_decisions']}")
        print(f"Precision:                      {_fmt_pct(s['precision'])}")
        print(f"Recall:                         {_fmt_pct(s['recall'])}")
        print(f"False automatic match rate:     {_fmt_pct(s['false_automatic_match_rate'])}")
        print()
        print("Outcome counts:")
        for key, count in sorted(s["outcome_counts"].items()):
            print(f"  {key}: {count}")
        print()
        print("By category:")
        for cat, counts in s["by_category"].items():
            bad = counts.get("incorrect_automatic_accept", 0)
            print(
                f"  {cat}: total={counts.get('total', 0)} "
                f"incorrect_accept={bad} "
                f"correct_accept={counts.get('correct_accept', 0)} "
                f"correct_reject={counts.get('correct_reject', 0)}"
            )
        print()
        print("By canonical family (families with failures or incorrect accepts):")
        for fam, counts in s["by_family"].items():
            bad = counts.get("incorrect_automatic_accept", 0)
            fails = sum(
                counts.get(k, 0)
                for k in counts
                if k
                not in {
                    "total",
                    "correct_accept",
                    "correct_reject",
                    "correct_manual_review",
                    "actual_accept",
                }
            )
            if bad or fails:
                print(
                    f"  {fam}: total={counts.get('total', 0)} "
                    f"incorrect_accept={bad} outcomes={dict(counts)}"
                )
        print()
        print("Open baseline bugs (stored wrong SKUs; fix in a separate change):")
        if not report.open_baseline_bugs:
            print("  (none)")
        for bug in report.open_baseline_bugs:
            print(
                f"  - [{bug['id']}] family={bug['family_id']!r} "
                f"← {bug['offer_text']!r}"
            )
            if bug.get("notes"):
                print(f"    {bug['notes'][:200]}")
        print()

    failures = report.failures()
    print(f"=== Failure list ({len(failures)}) ===")
    if not failures:
        print("(none)")
        return
    for r in failures:
        d = r.decision
        c = r.case
        print("-" * 72)
        print(f"id:              {c.id}")
        print(f"category:        {c.category}")
        print(f"offer_text:      {c.offer_text!r}")
        if c.package_text:
            print(f"package_text:    {c.package_text!r}")
        print(f"expected:        family={c.expected_family_id} decision={c.expected_decision}")
        print(
            f"actual:          family={d.matched_family_id} decision={d.actual_decision} "
            f"outcome={r.outcome}"
        )
        print(f"matched family:  {d.matched_family_id}")
        print(f"rule/phrase:     {_rule_responsible(d)}")
        print(
            f"eligibility:     {d.eligibility_decision} "
            f"(reason={d.eligibility_reason!r})"
        )
        print(
            f"confidence:      {d.confidence} "
            f"(keyword={d.keyword_confidence})"
        )
        if d.must_not_violations:
            print(f"must_not violated: {list(d.must_not_violations)}")
        if d.accepted_family_ids:
            print(f"all accepted families: {list(d.accepted_family_ids)}")
        if c.notes:
            print(f"notes:           {c.notes[:240]}")
        if c.source:
            print(f"source:          {c.source}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run eval of production product matching (no writes)."
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=DEFAULT_EVAL_CASES_PATH,
        help="Path to eval_cases.jsonl",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable summary JSON (failures included)",
    )
    parser.add_argument(
        "--failures-only",
        action="store_true",
        help="Print only the failure list",
    )
    args = parser.parse_args(argv)

    report = run_eval(args.cases)
    if args.json:
        payload = report.summary_dict()
        payload["failures"] = [
            {
                "id": r.case.id,
                "offer_text": r.case.offer_text,
                "expected_family_id": r.case.expected_family_id,
                "expected_decision": r.case.expected_decision,
                "actual_decision": r.decision.actual_decision,
                "matched_family_id": r.decision.matched_family_id,
                "outcome": r.outcome,
                "matching_phrase": r.decision.matching_phrase,
                "matching_pattern": r.decision.matching_pattern,
                "eligibility_decision": r.decision.eligibility_decision,
                "eligibility_reason": r.decision.eligibility_reason,
                "reject_reason": r.decision.reject_reason,
                "confidence": r.decision.confidence,
                "must_not_violations": list(r.decision.must_not_violations),
                "category": r.case.category,
                "source": r.case.source,
            }
            for r in report.failures()
        ]
        print(json.dumps(payload, indent=2, default=str))
    else:
        print_report(report, failures_only=args.failures_only)

    # Non-zero if incorrect automatic accepts (most dangerous) or many fails.
    if report.incorrect_automatic_accepts > 0:
        return 2
    if report.failures():
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
