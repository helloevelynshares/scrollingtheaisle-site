"""Eval case loading / scoring helpers for shopper-query experiment."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVAL_PATH = ROOT / "evals" / "shopper-query-v1.jsonl"
DEFAULT_OUTPUT_DIR = ROOT / "output" / "shopper_query_eval"

BEHAVIORS = frozenset({"continue", "clarify", "unsupported", "invalid"})


@dataclass
class EvalCase:
    id: str
    raw_query: str
    expected_fields: dict[str, Any]
    expected_tracker_id: str | None
    expected_behavior: str
    automatic_continuation_safe: bool
    notes: str = ""
    category: str = ""

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "EvalCase":
        eid = str(raw.get("id") or "").strip()
        if not eid:
            raise ValueError("eval case missing id")
        behavior = str(raw.get("expected_behavior") or "").strip()
        if behavior not in BEHAVIORS:
            raise ValueError(f"{eid}: invalid expected_behavior {behavior!r}")
        return cls(
            id=eid,
            raw_query=str(raw.get("raw_query") or ""),
            expected_fields=dict(raw.get("expected_fields") or {}),
            expected_tracker_id=raw.get("expected_tracker_id"),
            expected_behavior=behavior,
            automatic_continuation_safe=bool(raw.get("automatic_continuation_safe")),
            notes=str(raw.get("notes") or ""),
            category=str(raw.get("category") or ""),
        )


def load_eval_cases(path: Path | None = None) -> list[EvalCase]:
    path = path or DEFAULT_EVAL_PATH
    cases: list[EvalCase] = []
    seen: set[str] = set()
    with path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            case = EvalCase.from_dict(raw)
            if case.id in seen:
                raise ValueError(f"duplicate eval id: {case.id}")
            seen.add(case.id)
            cases.append(case)
    return cases


def _norm_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    return text or None


def _norm_product(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(str(text).lower().split())


def product_text_match(expected: Any, actual: str) -> bool:
    """Loose product-text check: expected tokens should appear in actual (or vice versa)."""
    exp = _norm_product(expected if isinstance(expected, str) else None)
    act = _norm_product(actual)
    if not exp and not act:
        return True
    if not exp or not act:
        return False
    # Allow either containment of key tokens (brand/product words >= 3 chars).
    exp_tokens = [t for t in exp.split() if len(t) >= 3]
    if not exp_tokens:
        return exp in act or act in exp
    hits = sum(1 for t in exp_tokens if t in act)
    return hits >= max(1, (len(exp_tokens) + 1) // 2)


def field_matches(field: str, expected: Any, parsed: dict[str, Any]) -> bool:
    actual = parsed.get(field)
    if field == "product_text":
        return product_text_match(expected, str(actual or ""))
    if field == "price":
        if expected is None and actual is None:
            return True
        if expected is None or actual is None:
            return False
        try:
            return abs(float(expected) - float(actual)) < 0.011
        except (TypeError, ValueError):
            return False
    if field in {"required_quantity", "items_received"}:
        if expected is None and actual is None:
            return True
        try:
            return int(expected) == int(actual)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return False
    if field == "package_size_text":
        exp = _norm_str(expected)
        act = _norm_str(actual)
        if exp is None and act is None:
            return True
        if exp is None or act is None:
            return False
        return exp in act or act in exp
    if field in {"promotion_type", "price_basis", "package_size_unit", "retailer"}:
        return _norm_str(expected) == _norm_str(actual)
    if field == "package_size_value":
        if expected is None and actual is None:
            return True
        if expected is None or actual is None:
            return False
        try:
            return abs(float(expected) - float(actual)) < 0.011
        except (TypeError, ValueError):
            return False
    return expected == actual


FAILURE_CATEGORIES = (
    "product_text",
    "price",
    "promotion_type",
    "required_quantity",
    "package_size",
    "tracker",
    "behavior",
    "safe_resolution",
    "confident_wrong",
)


def classify_failures(
    *,
    field_ok: dict[str, bool],
    tracker_ok: bool,
    behavior_ok: bool,
    safe_ok: bool,
    confident_wrong: bool,
) -> list[str]:
    cats: list[str] = []
    for key in (
        "product_text",
        "price",
        "promotion_type",
        "required_quantity",
        "package_size",
    ):
        if not field_ok.get(key, True):
            cats.append(key)
    if not tracker_ok:
        cats.append("tracker")
    if not behavior_ok:
        cats.append("behavior")
    if not safe_ok:
        cats.append("safe_resolution")
    if confident_wrong:
        cats.append("confident_wrong")
    return cats
