"""Lightweight eval helpers for deterministic deal assessment."""

from __future__ import annotations

from typing import Any

from .models import SubmittedOffer
from .service import assess_deal


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    """Run one eval case: expects tracker_id, retailer, submitted_offer, optional expect_verdict."""
    result = assess_deal(
        str(case["tracker_id"]),
        str(case.get("retailer") or "Safeway"),
        SubmittedOffer.from_mapping(case.get("submitted_offer") or {}),
    )
    out = result.to_dict()
    expected = case.get("expect_verdict")
    if expected is not None:
        out["expect_verdict"] = expected
        out["verdict_match"] = result.verdict == expected
    return out


def run_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [run_case(c) for c in cases]
    judged = [r for r in rows if "verdict_match" in r]
    matched = sum(1 for r in judged if r.get("verdict_match"))
    return {
        "count": len(rows),
        "judged": len(judged),
        "matched": matched,
        "rows": rows,
    }
