"""Tests for deterministic AisleCheck historical deal assessment."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from deal_assessment.eval import run_cases  # noqa: E402
from deal_assessment.models import PriceObservation, SubmittedOffer  # noqa: E402
from deal_assessment.normalize_offer import normalize_submitted_offer  # noqa: E402
from deal_assessment.policy import (  # noqa: E402
    FULL_VERDICT_MIN_OBS,
    history_tier,
)
from deal_assessment.service import assess_deal  # noqa: E402


class TestNormalizeOffer(unittest.TestCase):
    def test_each_when_buying_n(self) -> None:
        offer = SubmittedOffer(price=2.49, price_basis="each", required_quantity=4)
        norm = normalize_submitted_offer(offer)
        self.assertEqual(norm.comparable_unit_price, 2.49)
        self.assertEqual(norm.normalization_method, "as_stated_unit")

    def test_multi_buy_total(self) -> None:
        offer = SubmittedOffer(price=5.0, price_basis="multi_buy", required_quantity=2)
        norm = normalize_submitted_offer(offer)
        self.assertEqual(norm.comparable_unit_price, 2.5)
        self.assertEqual(norm.normalization_method, "multi_buy_unit")

    def test_n_for_x_alias(self) -> None:
        offer = SubmittedOffer(price=5.0, price_basis="n_for", required_quantity=4)
        norm = normalize_submitted_offer(offer)
        self.assertEqual(norm.comparable_unit_price, 1.25)

    def test_bogo_halves_reference(self) -> None:
        offer = SubmittedOffer(price=5.49, price_basis="bogo")
        norm = normalize_submitted_offer(offer)
        self.assertEqual(norm.comparable_unit_price, 2.745)

    def test_bogo_missing_price(self) -> None:
        norm = normalize_submitted_offer(SubmittedOffer(price=None, price_basis="bogo"))
        self.assertIsNone(norm.comparable_unit_price)

    def test_zero_and_negative_price(self) -> None:
        self.assertIsNone(normalize_submitted_offer(SubmittedOffer(price=0)).comparable_unit_price)
        self.assertIsNone(
            normalize_submitted_offer(SubmittedOffer(price=-1.0)).comparable_unit_price
        )

    def test_missing_price_basis_defaults_as_unit(self) -> None:
        norm = normalize_submitted_offer(SubmittedOffer(price=2.49, price_basis="unknown"))
        self.assertEqual(norm.comparable_unit_price, 2.49)


class TestHistoryPolicy(unittest.TestCase):
    def test_tiers(self) -> None:
        self.assertEqual(history_tier(0), "insufficient_data")
        self.assertEqual(history_tier(1), "insufficient_data")
        self.assertEqual(history_tier(2), "limited_data")
        self.assertEqual(history_tier(3), "limited_data")
        self.assertEqual(history_tier(FULL_VERDICT_MIN_OBS), "full")
        self.assertEqual(history_tier(10), "full")


class TestAssessDeal(unittest.TestCase):
    def test_doritos_full_verdict(self) -> None:
        result = assess_deal(
            "doritos_5_13oz",
            "Safeway",
            {
                "price": 2.49,
                "price_basis": "each",
                "required_quantity": 4,
                "package_size": "9.75 oz",
                "product_text": "Doritos",
            },
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.verdict, "normal_sale")
        self.assertEqual(result.evidence["history_tier"], "full")
        self.assertGreaterEqual(result.evidence["observation_count"], 4)
        self.assertEqual(result.normalized_offer.comparable_unit_price, 2.49)

    def test_multi_buy_submitted(self) -> None:
        result = assess_deal(
            "doritos_5_13oz",
            "Safeway",
            {"price": 10.0, "price_basis": "multi_buy", "required_quantity": 4},
        )
        self.assertEqual(result.normalized_offer.comparable_unit_price, 2.5)
        self.assertTrue(result.ok)

    def test_kettle_all_time_low(self) -> None:
        result = assess_deal(
            "kettle_brand_chips",
            "Safeway",
            {"price": 1.67, "price_basis": "each", "package_size": "7 oz"},
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.verdict, "all_time_low")

    def test_above_all_history(self) -> None:
        result = assess_deal(
            "doritos_5_13oz",
            "Safeway",
            {"price": 9.99, "price_basis": "each"},
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.verdict, "weak_sale")

    def test_limited_data_two_obs(self) -> None:
        result = assess_deal(
            "beef_short_ribs_per_lb",
            "Safeway",
            {"price": 5.0, "price_basis": "per_lb"},
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.verdict, "limited_data")
        self.assertEqual(result.verdict_label, "Early price signal")
        self.assertIn("directional", result.summary.lower())
        self.assertEqual(result.evidence["history_tier"], "limited_data")
        self.assertEqual(result.evidence["observation_count"], 2)
        # Must not silently promote a strong sale label with only 2 obs.
        self.assertNotIn(result.verdict, {"strong_sale", "all_time_low", "normal_sale"})

    def test_limited_data_three_obs(self) -> None:
        result = assess_deal(
            "butter_16oz",
            "Safeway",
            {"price": 3.99, "price_basis": "each"},
        )
        self.assertEqual(result.verdict, "limited_data")
        self.assertEqual(result.evidence["observation_count"], 3)

    def test_insufficient_data_zero_obs(self) -> None:
        result = assess_deal(
            "chobani_yogurt_tub",
            "Safeway",
            {"price": 1.25, "price_basis": "each"},
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.verdict, "insufficient_data")

    def test_does_not_reparse_query(self) -> None:
        result = assess_deal(
            "doritos_5_13oz",
            "Safeway",
            {
                "price": 2.49,
                "price_basis": "each",
                "product_text": "IGNORE THIS FREE TEXT $99.99 BOGO quinoa",
            },
        )
        self.assertEqual(result.normalized_offer.comparable_unit_price, 2.49)

    def test_unsupported_retailer(self) -> None:
        result = assess_deal(
            "doritos_5_13oz",
            "Costco",
            {"price": 2.49, "price_basis": "each"},
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.verdict, "not_comparable")
        self.assertIn("unsupported_retailer", result.comparability.reasons)

    def test_unknown_tracker(self) -> None:
        result = assess_deal(
            "not_a_real_tracker_xyz",
            "Safeway",
            {"price": 2.49, "price_basis": "each"},
        )
        self.assertFalse(result.ok)
        self.assertIn("unknown_tracker", result.comparability.reasons)

    def test_package_size_out_of_range(self) -> None:
        result = assess_deal(
            "doritos_5_13oz",
            "Safeway",
            {"price": 2.49, "price_basis": "each", "package_size": "30 oz"},
        )
        self.assertFalse(result.ok)
        self.assertIn("package_size_out_of_family_range", result.comparability.reasons)

    def test_bogo_with_reference(self) -> None:
        result = assess_deal(
            "doritos_5_13oz",
            "Safeway",
            {"price": 4.98, "price_basis": "bogo"},
        )
        self.assertEqual(result.normalized_offer.comparable_unit_price, 2.49)
        self.assertTrue(result.ok)

    def test_history_repository_failure(self) -> None:
        with mock.patch(
            "deal_assessment.service.load_observation_series",
            side_effect=RuntimeError("disk_missing"),
        ):
            with self.assertRaises(RuntimeError):
                assess_deal(
                    "doritos_5_13oz",
                    "Safeway",
                    {"price": 2.49, "price_basis": "each"},
                )

    def test_duplicate_weekly_prices_allowed(self) -> None:
        # Butter has duplicate 3.99 weeks; median/typical still computable.
        result = assess_deal(
            "butter_16oz",
            "Safeway",
            {"price": 3.99, "price_basis": "each"},
        )
        self.assertEqual(result.verdict, "limited_data")
        self.assertIsNotNone(result.evidence.get("typical_unit_price"))

    def test_eval_runner(self) -> None:
        report = run_cases(
            [
                {
                    "tracker_id": "kettle_brand_chips",
                    "retailer": "Safeway",
                    "submitted_offer": {"price": 1.67, "price_basis": "each"},
                    "expect_verdict": "all_time_low",
                },
                {
                    "tracker_id": "beef_short_ribs_per_lb",
                    "retailer": "Safeway",
                    "submitted_offer": {"price": 5.0, "price_basis": "per_lb"},
                    "expect_verdict": "limited_data",
                },
            ]
        )
        self.assertEqual(report["matched"], 2)


class TestAssessEndpointContract(unittest.TestCase):
    def test_server_registers_assess_route(self) -> None:
        text = (ROOT / "aislecheck-prototype" / "server.py").read_text(encoding="utf-8")
        self.assertIn("/api/aislecheck/assess", text)
        self.assertIn("assess_deal_dict", text)
        self.assertNotIn("deal_assistant", text)

    def test_ui_gates_assess(self) -> None:
        js = (ROOT / "aislecheck-prototype" / "aislecheck.js").read_text(encoding="utf-8")
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("assessEnabled", js)
        self.assertIn("startAssess", js)
        self.assertIn("/api/aislecheck/assess", js)
        self.assertIn("assessEnabled: true", html)
        self.assertIn("structuredClarificationEnabled: false", html)
        self.assertIn("aislecheck.js?v=ac17", html)
        self.assertNotIn("deal_assistant", js)

    def test_policy_module_present(self) -> None:
        text = (ROOT / "scripts" / "deal_assessment" / "policy.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("FULL_VERDICT_MIN_OBS = 4", text)
        self.assertIn("limited_data", text)


if __name__ == "__main__":
    unittest.main()
