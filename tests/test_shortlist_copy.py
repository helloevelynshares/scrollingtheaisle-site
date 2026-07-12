"""Regression tests for shortlist copy family-size gating.

The Nabisco family-size snack cracker family ("Wheat Thins, Triscuit & Chicken
in a Biskit") must only claim a "family-size boxes are $X" deal when the offer
actually passes the canonical match eligibility gate (family-size confirmation,
allowed product lines, no Ritz-led / single-serve / cookie negatives). A
standard-size (3.5–13.7 oz) Ritz-led mix-or-match offer must not be labeled as a
family-size deal.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from price_tracker.canonical_families import family_by_id  # noqa: E402
from price_tracker.canonical_match_eligibility import EligibilityIndex  # noqa: E402
from price_tracker.shortlist_copy import (  # noqa: E402
    family_shortlist_blurb,
    family_shortlist_blurb_by_id,
    is_family_size_family,
)

FAMILY_ID = "nabisco_snack_crackers"

FAMILY_SIZE_ROW = {
    "split_product_text": "Nabisco Family Size Snack Crackers 10-14 oz",
    "raw_offer_text": "Nabisco Family Size Snack Crackers 10-14 oz 3.49 EA MEMBER PRICE",
    "promo_text": "MEMBER PRICE",
    "advertised_price": "3.49",
    "price_basis": "each",
}

STANDARD_RITZ_LED_ROW = {
    "split_product_text": "Wheat Thins",
    "raw_offer_text": (
        "Ritz Crackers, Wheat Thins or Triscuit 3.5-13.7 oz, Selected varieties. "
        "Mix or Match any 4 or more participating items. $2.49 ea"
    ),
    "promo_text": "Mix or Match any 4 or more participating items",
    "advertised_price": "2.49",
    "price_basis": "each",
}

EXPECTED_SAFEWAY_BLURB = (
    "Wheat Thins, Triscuit, and Chicken in a Biskit family-size boxes are $3.49 "
    "this week, the app labels it as Nabisco family-size snack crackers, but "
    "those are the actual eligible items."
)


class ShortlistCopyGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.family = family_by_id()[FAMILY_ID]
        self.index = EligibilityIndex()

    def test_family_is_family_size(self) -> None:
        self.assertTrue(is_family_size_family(self.family))

    def test_family_size_accepted_offer_gets_family_size_blurb(self) -> None:
        decision = self.index.evaluate(
            FAMILY_SIZE_ROW, FAMILY_ID, keyword_confidence="high"
        ).match_decision
        self.assertEqual(decision, "accepted")
        blurb = family_shortlist_blurb(
            self.family, 3.49, family_size_eligible=(decision == "accepted")
        )
        self.assertEqual(blurb, EXPECTED_SAFEWAY_BLURB)

    def test_standard_ritz_led_offer_not_accepted(self) -> None:
        decision = self.index.evaluate(
            STANDARD_RITZ_LED_ROW, FAMILY_ID, keyword_confidence="high"
        ).match_decision
        self.assertNotEqual(decision, "accepted")

    def test_standard_offer_never_claims_family_size(self) -> None:
        # Even if the family were still attributed, without confirmation the
        # blurb must not claim a family-size boxes deal.
        blurb = family_shortlist_blurb(
            self.family, 2.49, family_size_eligible=False
        )
        self.assertNotIn("family-size boxes are", blurb)

    def test_helper_defaults_to_no_family_size_claim(self) -> None:
        # Defensive default: without explicit confirmation, no family-size claim.
        blurb = family_shortlist_blurb(self.family, 2.49)
        self.assertNotIn("family-size boxes are", blurb)

    def test_by_id_helper_honors_flag(self) -> None:
        confirmed = family_shortlist_blurb_by_id(
            FAMILY_ID, 3.49, family_size_eligible=True
        )
        self.assertIn("family-size boxes are $3.49", confirmed)
        unconfirmed = family_shortlist_blurb_by_id(FAMILY_ID, 3.49)
        self.assertNotIn("family-size boxes are", unconfirmed)


if __name__ == "__main__":
    unittest.main()
