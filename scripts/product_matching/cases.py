"""Load labeled product-matching eval cases from JSONL."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVAL_CASES_PATH = ROOT / "data" / "product_matching" / "eval_cases.jsonl"

VALID_DECISIONS = frozenset({"accept", "reject", "manual_review"})


@dataclass(frozen=True)
class EvalCase:
    id: str
    offer_text: str
    expected_family_id: str
    expected_decision: str
    must_not_match_family_ids: tuple[str, ...] = ()
    category: str = ""
    source: str = ""
    notes: str = ""
    package_text: str = ""
    price: str = "4.99"
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    def to_offer_row(self) -> dict[str, str]:
        """Synthetic split-offer row for the production matcher."""
        text = self.offer_text
        return {
            "split_product_text": text,
            "raw_offer_text": text,
            "promo_text": "Member Price",
            "advertised_price": self.price,
            "price_basis": "each",
            "package_unit": "each",
            "package_text": self.package_text or "",
        }


def _parse_case(raw: dict[str, Any], *, line_no: int) -> EvalCase:
    case_id = str(raw.get("id") or "").strip()
    offer_text = str(raw.get("offer_text") or "").strip()
    expected_family_id = str(raw.get("expected_family_id") or "").strip()
    expected_decision = str(raw.get("expected_decision") or "").strip().lower()
    if not case_id:
        raise ValueError(f"eval case at line {line_no}: missing id")
    if not offer_text:
        raise ValueError(f"eval case {case_id!r}: missing offer_text")
    if not expected_family_id:
        raise ValueError(f"eval case {case_id!r}: missing expected_family_id")
    if expected_decision not in VALID_DECISIONS:
        raise ValueError(
            f"eval case {case_id!r}: expected_decision must be one of "
            f"{sorted(VALID_DECISIONS)}, got {expected_decision!r}"
        )
    must_not = raw.get("must_not_match_family_ids") or []
    if isinstance(must_not, str):
        must_not = [must_not]
    return EvalCase(
        id=case_id,
        offer_text=offer_text,
        expected_family_id=expected_family_id,
        expected_decision=expected_decision,
        must_not_match_family_ids=tuple(str(x) for x in must_not if str(x).strip()),
        category=str(raw.get("category") or ""),
        source=str(raw.get("source") or ""),
        notes=str(raw.get("notes") or ""),
        package_text=str(raw.get("package_text") or ""),
        price=str(raw.get("price") or "4.99"),
        raw=raw,
    )


def load_eval_cases(path: Path | None = None) -> list[EvalCase]:
    path = path or DEFAULT_EVAL_CASES_PATH
    if not path.is_file():
        raise FileNotFoundError(f"Eval cases not found: {path}")
    cases: list[EvalCase] = []
    seen: set[str] = set()
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            raw = json.loads(stripped)
            case = _parse_case(raw, line_no=line_no)
            if case.id in seen:
                raise ValueError(f"Duplicate eval case id: {case.id!r}")
            seen.add(case.id)
            cases.append(case)
    return cases


def iter_eval_cases(path: Path | None = None) -> Iterable[EvalCase]:
    yield from load_eval_cases(path)
