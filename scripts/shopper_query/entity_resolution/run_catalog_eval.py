"""Run catalog-resolution-v1.jsonl against the live AisleCheck contract."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from shopper_query.aislecheck_contract import run_aislecheck_query
from shopper_query.entity_resolution.protected_phrases import clear_protected_phrase_cache
from shopper_query.entity_resolution.package_siblings import clear_package_sibling_cache

ROOT = Path(__file__).resolve().parents[3]
EVAL_PATH = ROOT / "evals" / "entity-resolution" / "catalog-resolution-v1.jsonl"
REPORT_PATH = ROOT / "evals" / "entity-resolution" / "catalog-resolution-v1.report.json"


def _status_ok(case: dict, result: dict) -> bool:
    expected = case["expected_status"]
    action = result.get("next_action")
    selected = (result.get("selected_tracker") or {}).get("id")
    forbidden = set(case.get("forbidden_tracker_ids") or [])

    if selected and selected in forbidden:
        return False

    if expected == "continue":
        return action == "continue" and selected == case.get("expected_tracker_id")
    if expected == "clarify":
        return action == "clarify"
    if expected == "unsupported":
        return action == "unsupported"
    if expected == "clarify_or_unsupported":
        return action in {"clarify", "unsupported"}
    if expected == "any_non_match":
        return not (action == "continue" and selected == case.get("tracker_id"))
    return False


def run_eval(path: Path = EVAL_PATH) -> dict:
    clear_protected_phrase_cache()
    clear_package_sibling_cache()
    cases = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    failures = []
    wrong_confident = 0
    by_type: Counter[str] = Counter()
    by_type_fail: Counter[str] = Counter()
    for case in cases:
        by_type[case["coverage_type"]] += 1
        # Skip loop_setup as standalone assertion beyond clarify
        result = run_aislecheck_query(case["query"])
        ok = _status_ok(case, result)
        selected = (result.get("selected_tracker") or {}).get("id")
        forbidden = set(case.get("forbidden_tracker_ids") or [])
        if selected and selected in forbidden:
            wrong_confident += 1
            ok = False
        elif not ok and result.get("next_action") == "continue" and case.get(
            "expected_status"
        ) not in {"continue", "any_non_match"}:
            # Unexpected continue outside forbidden list still counted below via ok
            pass
        if not ok:
            by_type_fail[case["coverage_type"]] += 1
            failures.append(
                {
                    "id": case["id"],
                    "query": case["query"],
                    "expected_status": case["expected_status"],
                    "expected_tracker_id": case.get("expected_tracker_id"),
                    "got_action": result.get("next_action"),
                    "got_tracker": selected,
                    "reason_codes": result.get("reason_codes"),
                }
            )

    # Loop termination probe
    first = run_aislecheck_query("Safeway chips are $2.49")
    fp = first.get("clarify_fingerprint")
    second = run_aislecheck_query(
        "Safeway chips are $2.49 chips",
        prior_clarify_digests=[fp] if fp else None,
    )
    loop_ok = "clarify_loop_broken" in (second.get("reason_codes") or []) and second.get(
        "next_action"
    ) in {"unsupported", "clarify"}
    if not loop_ok:
        failures.append(
            {
                "id": "loop__termination",
                "query": "Safeway chips are $2.49 chips",
                "expected_status": "clarify_loop_broken",
                "got_action": second.get("next_action"),
                "got_tracker": None,
                "reason_codes": second.get("reason_codes"),
            }
        )

    report = {
        "eval_path": str(path.relative_to(ROOT)),
        "total": len(cases),
        "passed": len(cases) - len([f for f in failures if f["id"] != "loop__termination"]),
        "failed": len(failures),
        "wrong_confident_match_count": wrong_confident,
        "coverage_type_counts": dict(by_type),
        "coverage_type_failures": dict(by_type_fail),
        "loop_termination_ok": loop_ok,
        "failures": failures[:80],
        "failure_count_total": len(failures),
    }
    # Adjust passed if loop failure is extra
    if any(f["id"] == "loop__termination" for f in failures):
        report["failed"] = len(failures)
    return report


def main() -> None:
    report = run_eval()
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in report if k != "failures"}, indent=2))
    if report["failure_count_total"]:
        print(f"failures sample: {len(report['failures'])}", file=sys.stderr)
        for f in report["failures"][:15]:
            print(f"  FAIL {f['id']}: expected={f['expected_status']} got={f['got_action']}/{f['got_tracker']}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
