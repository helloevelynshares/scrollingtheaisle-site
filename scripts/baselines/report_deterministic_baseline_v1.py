"""Produce a deterministic-baseline-v1 window report skeleton.

When production event logs are not available, marks production metrics as
unavailable rather than inventing rates.
"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs" / "baselines" / "deterministic-baseline-v1.json"
DEFAULT_OUT = ROOT / "reports" / "deterministic-baseline-v1"


def build_report(start: str, end: str, min_sample: int) -> dict:
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {
        "report_id": f"deterministic-baseline-v1_{start}_to_{end}",
        "baseline_id": man["baseline_id"],
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "window": {"start": start, "end": end},
        "code_filter": {
            "main_sha": man["main_sha"],
            "render_backend_sha": man["deployed_branches"]["render_backend_sha"],
            "frontend_asset_version": man["frontend_asset_version"],
            "feature_flags": man["feature_flags"],
        },
        "minimum_sample_size": min_sample,
        "minimum_sample_warning": (
            f"Target at least {min_sample} valid external queries before closing the window."
        ),
        "production_metrics_status": "unavailable",
        "production_metrics_note": (
            "Instrumentation for production query/assess event aggregation is not yet "
            "wired into this reporter. Fill offline quality from the freeze; leave "
            "production rates null until logs are available."
        ),
        "counts": {
            "submitted_queries": None,
            "valid_queries": None,
            "reviewed_queries": None,
            "unreviewed_queries": None,
            "unique_sessions": None,
        },
        "metrics": {
            "valid_query_rate": None,
            "deterministic_safe_resolution_rate": None,
            "direct_resolution_rate": None,
            "clarification_rate": None,
            "clarification_completion_rate": None,
            "unsupported_rate": None,
            "invalid_rate": None,
            "assessment_completion_rate": None,
            "insufficient_history_rate": None,
            "helpfulness_rate": None,
            "correction_rate": None,
            "wrong_confident_match_rate": None,
            "query_service_failure_rate": None,
            "assessment_service_failure_rate": None,
            "query_latency_ms_p50": None,
            "query_latency_ms_p95": None,
            "assessment_latency_ms_p50": None,
            "assessment_latency_ms_p95": None,
        },
        "cost": {
            "llm_token_cost_usd": 0,
            "llm_invocation_count": 0,
            "provider_error_count": 0,
        },
        "offline_quality_at_freeze": man.get("evals"),
        "failure_reason_distribution": {},
        "top_unresolved_categories": [],
        "usefulness_feedback": {"status": "unavailable"},
        "correction_outcomes": {"status": "unavailable"},
        "denominators": {
            "doc": "docs/baselines/deterministic-baseline-v1-metrics.md"
        },
    }


def to_markdown(report: dict) -> str:
    w = report["window"]
    lines = [
        f"# {report['report_id']}",
        "",
        f"Generated: {report['generated_at']}",
        f"Window: {w['start']} → {w['end']}",
        f"Baseline: {report['baseline_id']}",
        "",
        f"**Production metrics status:** `{report['production_metrics_status']}`",
        "",
        report["production_metrics_note"],
        "",
        "## Code filter",
        "",
        "```json",
        json.dumps(report["code_filter"], indent=2),
        "```",
        "",
        "## Cost (deterministic)",
        "",
        f"- LLM token cost: ${report['cost']['llm_token_cost_usd']}",
        f"- LLM invocations: {report['cost']['llm_invocation_count']}",
        "",
        "## Offline quality at freeze",
        "",
        "```json",
        json.dumps(report.get("offline_quality_at_freeze"), indent=2),
        "```",
        "",
        "## Next steps",
        "",
        "- Collect ≥ "
        + str(report["minimum_sample_size"])
        + " valid external queries before closing.",
        "- Complete reviewed sample for wrong-confident rate.",
        "- See docs/baselines/deterministic-baseline-v1-measurement-window.md.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--min-sample", type=int, default=100)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    # Validate dates
    date.fromisoformat(args.start)
    date.fromisoformat(args.end)
    report = build_report(args.start, args.end, args.min_sample)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{args.start}_to_{args.end}"
    json_path = args.out_dir / f"{stem}.json"
    md_path = args.out_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(to_markdown(report), encoding="utf-8")
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
