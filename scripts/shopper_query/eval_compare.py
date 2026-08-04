"""Comparison evaluator: raw vs normalize→parse→match on the same eval set."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from shopper_query.cases import DEFAULT_EVAL_PATH, DEFAULT_OUTPUT_DIR  # noqa: E402
from shopper_query.eval_baseline import run_baseline  # noqa: E402

FIELD_KEYS = (
    "product_text",
    "price",
    "promotion_type",
    "required_quantity",
    "package_size",
)


def compare_runs(
    baseline_rows: list[dict[str, Any]],
    normalized_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    by_id_b = {r["id"]: r for r in baseline_rows}
    by_id_n = {r["id"]: r for r in normalized_rows}
    ids = sorted(set(by_id_b) & set(by_id_n))

    fields_improved: dict[str, list[str]] = {k: [] for k in FIELD_KEYS}
    fields_regressed: dict[str, list[str]] = {k: [] for k in FIELD_KEYS}
    newly_resolved: list[str] = []
    new_incorrect: list[str] = []
    row_deltas: list[dict[str, Any]] = []

    for cid in ids:
        b = by_id_b[cid]
        n = by_id_n[cid]
        improved = []
        regressed = []
        for k in FIELD_KEYS:
            b_ok = b["field_ok"].get(k, False)
            n_ok = n["field_ok"].get(k, False)
            if not b_ok and n_ok:
                fields_improved[k].append(cid)
                improved.append(k)
            elif b_ok and not n_ok:
                fields_regressed[k].append(cid)
                regressed.append(k)

        b_resolved = b["behavior"]["behavior"] == "continue" and b["tracker_ok"]
        n_resolved = n["behavior"]["behavior"] == "continue" and n["tracker_ok"]
        if not b_resolved and n_resolved:
            newly_resolved.append(cid)
        # New incorrect interpretation: now continues unsafely / confidently wrong
        if not b["confident_wrong"] and n["confident_wrong"]:
            new_incorrect.append(cid)
        elif b["tracker_ok"] and not n["tracker_ok"] and n["behavior"][
            "automatic_continuation_safe"
        ]:
            new_incorrect.append(cid)

        row_deltas.append(
            {
                "id": cid,
                "fields_improved": improved,
                "fields_regressed": regressed,
                "baseline_tracker_ok": b["tracker_ok"],
                "normalized_tracker_ok": n["tracker_ok"],
                "baseline_behavior": b["behavior"]["behavior"],
                "normalized_behavior": n["behavior"]["behavior"],
                "baseline_safe": b["behavior"]["automatic_continuation_safe"],
                "normalized_safe": n["behavior"]["automatic_continuation_safe"],
                "baseline_confident_wrong": b["confident_wrong"],
                "normalized_confident_wrong": n["confident_wrong"],
            }
        )

    def _acc(rows: list[dict[str, Any]], key: str) -> float:
        if not rows:
            return 0.0
        if key == "tracker":
            return sum(1 for r in rows if r["tracker_ok"]) / len(rows)
        if key == "behavior":
            return sum(1 for r in rows if r["behavior_ok"]) / len(rows)
        if key == "safe":
            return sum(1 for r in rows if r["safe_resolution_ok"]) / len(rows)
        return sum(1 for r in rows if r["field_ok"].get(key, False)) / len(rows)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_cases": len(ids),
        "fields_improved": {k: v for k, v in fields_improved.items() if v},
        "fields_regressed": {k: v for k, v in fields_regressed.items() if v},
        "fields_improved_counts": {k: len(v) for k, v in fields_improved.items()},
        "fields_regressed_counts": {k: len(v) for k, v in fields_regressed.items()},
        "newly_resolved_cases": newly_resolved,
        "new_incorrect_interpretations": new_incorrect,
        "exact_tracker_accuracy": {
            "baseline": _acc(baseline_rows, "tracker"),
            "normalized": _acc(normalized_rows, "tracker"),
            "delta": _acc(normalized_rows, "tracker") - _acc(baseline_rows, "tracker"),
        },
        "safe_resolution_rate": {
            "baseline": _acc(baseline_rows, "safe"),
            "normalized": _acc(normalized_rows, "safe"),
            "delta": _acc(normalized_rows, "safe") - _acc(baseline_rows, "safe"),
        },
        "correct_behavior_accuracy": {
            "baseline": _acc(baseline_rows, "behavior"),
            "normalized": _acc(normalized_rows, "behavior"),
            "delta": _acc(normalized_rows, "behavior") - _acc(baseline_rows, "behavior"),
        },
        "confident_wrong_count": {
            "baseline": sum(1 for r in baseline_rows if r["confident_wrong"]),
            "normalized": sum(1 for r in normalized_rows if r["confident_wrong"]),
        },
        "field_accuracy": {
            k: {
                "baseline": _acc(baseline_rows, k),
                "normalized": _acc(normalized_rows, k),
                "delta": _acc(normalized_rows, k) - _acc(baseline_rows, k),
            }
            for k in FIELD_KEYS
        },
        "row_deltas": row_deltas,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_EVAL_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)

    base = run_baseline(
        cases_path=args.cases,
        output_dir=args.output_dir,
        apply_normalization=False,
    )
    norm = run_baseline(
        cases_path=args.cases,
        output_dir=args.output_dir,
        apply_normalization=True,
    )
    comparison = compare_runs(base["rows"], norm["rows"])
    comparison["baseline_summary"] = {
        k: v
        for k, v in base["summary"].items()
        if k
        not in {
            "report_path",
            "results_path",
        }
    }
    comparison["normalized_summary"] = {
        k: v
        for k, v in norm["summary"].items()
        if k not in {"report_path", "results_path"}
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.output_dir / "comparison_report.json"
    out_path.write_text(json.dumps(comparison, indent=2) + "\n", encoding="utf-8")

    print("=== Shopper-query comparison (raw vs normalized) ===")
    print(f"Total cases: {comparison['total_cases']}")
    print(
        "Exact tracker accuracy: "
        f"{comparison['exact_tracker_accuracy']['baseline']*100:.1f}% → "
        f"{comparison['exact_tracker_accuracy']['normalized']*100:.1f}% "
        f"(Δ {comparison['exact_tracker_accuracy']['delta']*100:+.1f}%)"
    )
    print(
        "Safe resolution rate:   "
        f"{comparison['safe_resolution_rate']['baseline']*100:.1f}% → "
        f"{comparison['safe_resolution_rate']['normalized']*100:.1f}% "
        f"(Δ {comparison['safe_resolution_rate']['delta']*100:+.1f}%)"
    )
    print(f"Newly resolved: {comparison['newly_resolved_cases']}")
    print(f"New incorrect:  {comparison['new_incorrect_interpretations']}")
    print("Field deltas:")
    for k, v in comparison["field_accuracy"].items():
        print(
            f"  {k:20s} {v['baseline']*100:5.1f}% → {v['normalized']*100:5.1f}% "
            f"(Δ {v['delta']*100:+.1f}%)"
        )
    print(f"Report: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
