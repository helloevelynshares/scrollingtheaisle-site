"""Score dry-run match decisions against labeled eval cases."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

from product_matching.cases import EvalCase
from product_matching.engine import MatchDecision


@dataclass
class CaseResult:
    case: EvalCase
    decision: MatchDecision
    outcome: str
    passed: bool

    @property
    def is_incorrect_accept(self) -> bool:
        return self.outcome == "incorrect_automatic_accept"

    @property
    def is_incorrect_reject(self) -> bool:
        return self.outcome == "incorrect_reject"


def classify_outcome(case: EvalCase, decision: MatchDecision) -> str:
    """Map expected vs actual into an outcome bucket."""
    if decision.must_not_violations:
        return "incorrect_automatic_accept"

    expected = case.expected_decision
    actual = decision.actual_decision

    if expected == "accept":
        if actual == "accept":
            return "correct_accept"
        if actual == "manual_review":
            return "manual_review_instead_of_accept"
        return "incorrect_reject"

    if expected == "reject":
        if actual == "reject":
            return "correct_reject"
        if actual == "accept":
            return "incorrect_automatic_accept"
        return "manual_review_instead_of_reject"

    # expected manual_review
    if actual == "manual_review":
        return "correct_manual_review"
    if actual == "accept":
        return "incorrect_automatic_accept"
    return "incorrect_reject_instead_of_manual_review"


@dataclass
class EvalReport:
    results: list[CaseResult]
    open_baseline_bugs: list[dict[str, Any]] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    def count(self, outcome: str) -> int:
        return sum(1 for r in self.results if r.outcome == outcome)

    @property
    def correct_accepts(self) -> int:
        return self.count("correct_accept")

    @property
    def correct_rejects(self) -> int:
        return self.count("correct_reject")

    @property
    def incorrect_automatic_accepts(self) -> int:
        return self.count("incorrect_automatic_accept")

    @property
    def incorrect_rejects(self) -> int:
        return sum(
            1
            for r in self.results
            if r.outcome
            in {
                "incorrect_reject",
                "incorrect_reject_instead_of_manual_review",
                "manual_review_instead_of_accept",
            }
        )

    @property
    def manual_review_decisions(self) -> int:
        """Cases where the matcher returned manual_review (any expected)."""
        return sum(
            1 for r in self.results if r.decision.actual_decision == "manual_review"
        )

    @property
    def precision(self) -> float | None:
        """TP / (TP + FP) among automatic accepts."""
        tp = self.correct_accepts
        fp = self.incorrect_automatic_accepts
        denom = tp + fp
        return (tp / denom) if denom else None

    @property
    def recall(self) -> float | None:
        """TP / (TP + FN) for expected accepts."""
        tp = self.correct_accepts
        # FN = expected accept that was not accepted
        fn = sum(
            1
            for r in self.results
            if r.case.expected_decision == "accept"
            and r.decision.actual_decision != "accept"
        )
        denom = tp + fn
        return (tp / denom) if denom else None

    @property
    def false_automatic_match_rate(self) -> float | None:
        """Incorrect automatic accepts / all automatic accepts."""
        auto_accepts = sum(
            1 for r in self.results if r.decision.actual_decision == "accept"
        )
        if not auto_accepts:
            return None
        return self.incorrect_automatic_accepts / auto_accepts

    def by_category(self) -> dict[str, dict[str, int]]:
        out: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for r in self.results:
            cat = r.case.category or "(uncategorized)"
            out[cat]["total"] += 1
            out[cat][r.outcome] += 1
            if r.decision.actual_decision == "accept":
                out[cat]["actual_accept"] += 1
        return {k: dict(v) for k, v in sorted(out.items())}

    def by_family(self) -> dict[str, dict[str, int]]:
        out: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for r in self.results:
            fam = r.case.expected_family_id
            out[fam]["total"] += 1
            out[fam][r.outcome] += 1
        return {k: dict(v) for k, v in sorted(out.items())}

    def failures(self) -> list[CaseResult]:
        ok = {
            "correct_accept",
            "correct_reject",
            "correct_manual_review",
        }
        return [r for r in self.results if r.outcome not in ok]

    def outcome_counts(self) -> Counter[str]:
        return Counter(r.outcome for r in self.results)

    def summary_dict(self) -> dict[str, Any]:
        return {
            "total_cases": self.total,
            "correct_accepts": self.correct_accepts,
            "correct_rejects": self.correct_rejects,
            "incorrect_automatic_accepts": self.incorrect_automatic_accepts,
            "incorrect_rejects": self.incorrect_rejects,
            "manual_review_decisions": self.manual_review_decisions,
            "precision": self.precision,
            "recall": self.recall,
            "false_automatic_match_rate": self.false_automatic_match_rate,
            "outcome_counts": dict(self.outcome_counts()),
            "by_category": self.by_category(),
            "by_family": self.by_family(),
            "open_baseline_bugs": self.open_baseline_bugs,
        }


def evaluate_case(case: EvalCase, decision: MatchDecision) -> CaseResult:
    outcome = classify_outcome(case, decision)
    passed = outcome in {
        "correct_accept",
        "correct_reject",
        "correct_manual_review",
    }
    return CaseResult(case=case, decision=decision, outcome=outcome, passed=passed)
