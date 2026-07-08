"""Regression tests for canonical weekly ad match eligibility."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from price_tracker.canonical_families import load_families  # noqa: E402
from price_tracker.canonical_match_eligibility import (  # noqa: E402
    EligibilityIndex,
    evaluate_canonical_match,
    load_match_rules,
    merge_family_yaml_rules,
)


def _row(text: str, price: str = "4.99") -> dict[str, str]:
    return {
        "split_product_text": text,
        "raw_offer_text": text,
        "promo_text": "Member Price",
        "advertised_price": price,
        "price_basis": "each",
        "package_unit": "each",
    }


class TestCanonicalMatchEligibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.families = {f.id: f for f in load_families()}
        cls.rules = load_match_rules()
        cls.index = EligibilityIndex()

    def test_smoked_salmon_rejected_for_fresh_salmon_family(self) -> None:
        family = self.families["salmon"]
        rules = merge_family_yaml_rules(family, self.rules)
        result = evaluate_canonical_match(
            _row("Acme Togarashi or Nova Smoked Salmon 3 oz"),
            family,
            rules=rules,
            keyword_confidence="high",
            historical_low=6.99,
        )
        self.assertEqual(result.match_decision, "rejected")
        self.assertEqual(result.ad_product_type, "smoked_salmon")
        self.assertIn("smoked", result.hard_negative_hits)
        self.assertIn("smoked", (result.reject_reason or "").lower())

    def test_fresh_atlantic_fillets_accepted(self) -> None:
        family = self.families["salmon"]
        rules = merge_family_yaml_rules(family, self.rules)
        result = evaluate_canonical_match(
            _row("Fresh Atlantic Salmon Fillets Farm Raised", price="8.99"),
            family,
            rules=rules,
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "accepted")
        self.assertEqual(result.ad_product_type, "fresh_salmon_fillets")

    def test_2_liter_soda_rejected_for_coca_cola_12packs(self) -> None:
        family = self.families["coca_cola_12packs"]
        rules = merge_family_yaml_rules(family, self.rules)
        result = evaluate_canonical_match(
            _row("Coca-Cola 2 Liter Bottle", price="1.99"),
            family,
            rules=rules,
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "rejected")
        self.assertEqual(result.ad_product_type, "2_liter_bottle")

    def test_12_pack_soda_accepted_or_manual_review_for_coca_cola_12packs(self) -> None:
        family = self.families["coca_cola_12packs"]
        rules = merge_family_yaml_rules(family, self.rules)
        result = evaluate_canonical_match(
            _row("Coca-Cola 12-Pack 12 fl oz cans", price="5.99"),
            family,
            rules=rules,
            keyword_confidence="high",
        )
        self.assertIn(result.match_decision, ("accepted", "manual_review"))
        self.assertEqual(result.ad_product_type, "12_pack_cans")

    def test_butter_spread_rejected_butter_sticks_accepted(self) -> None:
        family = self.families["butter_16oz"]
        rules = merge_family_yaml_rules(family, self.rules)

        spread = evaluate_canonical_match(
            _row(
                "Land O Lakes Butter 16-oz. Spread 13 to 15-oz. Selected varieties.",
                price="3.49",
            ),
            family,
            rules=rules,
            keyword_confidence="high",
        )
        self.assertEqual(spread.match_decision, "rejected")
        self.assertEqual(spread.ad_product_type, "butter_spread")

        sticks = evaluate_canonical_match(
            _row("Challenge Butter Quarters 16 oz", price="4.99"),
            family,
            rules=rules,
            keyword_confidence="high",
        )
        self.assertEqual(sticks.match_decision, "accepted")
        self.assertEqual(sticks.ad_product_type, "butter_sticks")


if __name__ == "__main__":
    unittest.main()
