"""Unit tests for the content-first deal scorer."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from weekly_ad_analysis.content_score import (  # noqa: E402
    ContentScoreInput,
    score_content_deal,
)


class TestContentScore(unittest.TestCase):
    def test_score_is_bounded_0_100(self) -> None:
        best = ContentScoreInput(
            category="produce",
            recognizable_brand=True,
            costco_percent_cheaper=40,
            costco_match_type="exact same product",
            near_costco_with_smaller_qty=True,
            absolute_price_strength="strong",
            is_friday_only=True,
            is_seasonal_produce=True,
            tiktok_hook="strong",
        )
        result = score_content_deal(best)
        self.assertLessEqual(result.content_score, 100)
        self.assertGreaterEqual(result.content_score, 0)

    def test_does_not_require_canonical_or_costco(self) -> None:
        """An ad-deal-only item (no Costco comp) still earns a real score."""
        ad_only = ContentScoreInput(
            category="snacks",
            recognizable_brand=True,
            costco_percent_cheaper=None,
            costco_match_type=None,
            absolute_price_strength="strong",
            tiktok_hook="strong",
        )
        result = score_content_deal(ad_only)
        self.assertGreater(result.content_score, 40)
        self.assertEqual(result.components["costco_unit_win"], 0)

    def test_costco_beater_scores_higher_than_proxy(self) -> None:
        exact = ContentScoreInput(
            category="produce",
            costco_percent_cheaper=25,
            costco_match_type="exact same product",
        )
        proxy = ContentScoreInput(
            category="produce",
            costco_percent_cheaper=25,
            costco_match_type="proxy / manual-review",
        )
        self.assertGreater(
            score_content_deal(exact).components["costco_unit_win"],
            score_content_deal(proxy).components["costco_unit_win"],
        )

    def test_proxy_match_gets_only_directional_credit(self) -> None:
        proxy = ContentScoreInput(
            category="snacks",
            costco_percent_cheaper=50,
            costco_match_type="same category comparable",
        )
        self.assertLessEqual(score_content_deal(proxy).components["costco_unit_win"], 6)

    def test_friday_only_is_rewarded_not_penalized(self) -> None:
        weekday = ContentScoreInput(category="produce", is_friday_only=False)
        friday = ContentScoreInput(category="produce", is_friday_only=True)
        self.assertGreater(
            score_content_deal(friday).content_score,
            score_content_deal(weekday).content_score,
        )

    def test_costco_wins_gives_no_unit_win_points(self) -> None:
        """Negative pct (Costco cheaper) earns zero Costco-win points."""
        costco_wins = ContentScoreInput(
            category="snacks",
            costco_percent_cheaper=-16,
            costco_match_type="same product different size",
        )
        self.assertEqual(score_content_deal(costco_wins).components["costco_unit_win"], 0)

    def test_high_interest_category_beats_other(self) -> None:
        produce = ContentScoreInput(category="produce")
        other = ContentScoreInput(category="other")
        self.assertGreater(
            score_content_deal(produce).components["category_fit"],
            score_content_deal(other).components["category_fit"],
        )

    def test_recognizable_brand_bonus(self) -> None:
        known = ContentScoreInput(category="snacks", recognizable_brand=True)
        generic = ContentScoreInput(category="snacks", recognizable_brand=False)
        self.assertGreater(
            score_content_deal(known).components["shopper_recognizability"],
            score_content_deal(generic).components["shopper_recognizability"],
        )

    def test_components_have_max_reference(self) -> None:
        result = score_content_deal(ContentScoreInput())
        self.assertEqual(set(result.components), set(result.max_components))
        self.assertEqual(sum(result.max_components.values()), 100)

    def test_near_costco_variety_award(self) -> None:
        variety = ContentScoreInput(
            category="dairy", near_costco_with_smaller_qty=True
        )
        self.assertGreater(score_content_deal(variety).components["near_costco_variety"], 0)


if __name__ == "__main__":
    unittest.main()
