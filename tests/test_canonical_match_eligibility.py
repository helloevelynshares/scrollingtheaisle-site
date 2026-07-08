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


class TestNabiscoFamilySizeSnackCrackers(unittest.TestCase):
    """Wheat Thins / Triscuit / Chicken in a Biskit family-size snack crackers."""

    DISPLAY_NAME = "Wheat Thins, Triscuit & Chicken in a Biskit"
    SUBTITLE = "Nabisco family-size snack crackers, 11.5–14 oz"

    @classmethod
    def setUpClass(cls) -> None:
        cls.families = {f.id: f for f in load_families()}
        cls.rules = load_match_rules()

    def _evaluate(self, text: str, price: str, keyword_confidence: str = "medium"):
        family = self.families["nabisco_snack_crackers"]
        rules = merge_family_yaml_rules(family, self.rules)
        return evaluate_canonical_match(
            _row(text, price=price),
            family,
            rules=rules,
            keyword_confidence=keyword_confidence,
        )

    def test_1_accept_family_size_snack_crackers(self) -> None:
        result = self._evaluate(
            "Nabisco Snack Crackers Family Size 11.5–14 oz",
            price="3.49",
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "accepted")
        self.assertEqual(result.display_name, self.DISPLAY_NAME)
        self.assertEqual(result.subtitle, self.SUBTITLE)
        self.assertEqual(result.manufacturer_family, "Nabisco")
        self.assertEqual(result.package_type, "family_size_box")
        self.assertIn("Wheat Thins", result.allowed_product_lines)
        self.assertIn("Triscuit", result.allowed_product_lines)
        self.assertIn("Chicken in a Biskit", result.allowed_product_lines)
        self.assertTrue(result.eligible_item_examples)

    def test_1b_accept_real_safeway_offer(self) -> None:
        # The live 2026-07-08 Safeway offer text must still ACCEPT.
        result = self._evaluate(
            "Nabisco Family Size Snack Crackers 10-14 oz",
            price="3.49",
            keyword_confidence="medium",
        )
        self.assertEqual(result.match_decision, "accepted")
        self.assertEqual(result.display_name, self.DISPLAY_NAME)

    def test_2_reject_chips_ahoy(self) -> None:
        result = self._evaluate(
            "Nabisco Chips Ahoy! Cookies 9.5–13 oz", price="3.49", keyword_confidence="high"
        )
        self.assertNotEqual(result.match_decision, "accepted")
        self.assertEqual(result.match_decision, "rejected")
        self.assertEqual(result.ad_product_type, "chips_ahoy")

    def test_3_reject_oreo(self) -> None:
        result = self._evaluate(
            "Oreo Family Size Cookies 10–18 oz", price="3.99", keyword_confidence="high"
        )
        self.assertNotEqual(result.match_decision, "accepted")
        self.assertEqual(result.match_decision, "rejected")
        self.assertEqual(result.ad_product_type, "oreo")

    def test_4_reject_ritz(self) -> None:
        result = self._evaluate(
            "Ritz Crackers 8.8–13.7 oz", price="2.49", keyword_confidence="high"
        )
        self.assertNotEqual(result.match_decision, "accepted")
        self.assertEqual(result.match_decision, "rejected")
        self.assertEqual(result.ad_product_type, "ritz_crackers")

    def test_5_reject_single_serve_multipack(self) -> None:
        result = self._evaluate(
            "Nabisco Single Serve Snacks 10 pack", price="3.99", keyword_confidence="high"
        )
        self.assertNotEqual(result.match_decision, "accepted")
        self.assertIn(result.match_decision, ("rejected", "manual_review"))
        self.assertEqual(result.ad_product_type, "single_serve_snack_multipack")

    def test_6_manual_review_bare_nabisco_snack_crackers(self) -> None:
        # No size, no eligible items → manual review, no graph update.
        result = self._evaluate(
            "Nabisco Snack Crackers", price="2.49", keyword_confidence="high"
        )
        self.assertEqual(result.match_decision, "manual_review")
        self.assertIn("confirmation", (result.reject_reason or "").lower())


if __name__ == "__main__":
    unittest.main()
