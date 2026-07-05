"""Tests for Vons historical low check normalization and labeling."""

from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analysis.vons_historical_low_check import (  # noqa: E402
    TrackerMapping,
    build_weekly_series,
    classify_historical,
    load_mappings,
    normalize_offer_unit_price,
    pick_best_row_for_mapping,
    run_check,
)


def _mapping(key: str, **kwargs) -> TrackerMapping:
    defaults = {
        "tracker_kind": "category",
        "display_name": key,
        "category_group": "test",
        "comparable_unit": "each",
        "patterns": (key.replace("_", " "),),
        "exclude_patterns": (),
        "prefer_patterns": (),
        "costco_comparable": False,
        "maps_to_canonical_id": None,
    }
    defaults.update(kwargs)
    return TrackerMapping(tracker_key=key, **defaults)


def _row(**fields) -> dict[str, str]:
    base = {
        "banner": "Vons",
        "week_start": "2026-07-01",
        "week_end": "2026-07-07",
        "split_product_text": "",
        "raw_offer_text": "",
        "promo_text": "",
        "advertised_price": "",
        "package_text": "",
        "package_size_min": "",
        "package_size_max": "",
        "package_unit": "",
        "price_basis": "",
        "review_reasons": "",
        "split_status": "single_product",
    }
    base.update(fields)
    return base


class NormalizeOfferTests(unittest.TestCase):
    def test_five_for_five_avocados(self) -> None:
        mapping = _mapping(
            "avocados",
            comparable_unit="each",
            patterns=(r"hass avocado",),
            maps_to_canonical_id="avocados",
        )
        row = _row(
            split_product_text="Medium Ripe Hass Avocados",
            raw_offer_text="Medium Ripe Hass Avocados 5 for $5",
            advertised_price="5.0",
            price_basis="multi_buy",
            promo_text="5 for $5",
        )
        result = normalize_offer_unit_price(row, mapping)
        self.assertEqual(result.unit_price, 1.0)
        self.assertEqual(result.unit, "each")

    def test_salmon_per_lb(self) -> None:
        mapping = _mapping("category_salmon", comparable_unit="lb", patterns=(r"salmon",))
        row = _row(
            split_product_text="Fresh Atlantic Salmon Fillets",
            advertised_price="7.97",
            price_basis="per_lb",
            package_unit="lb",
        )
        result = normalize_offer_unit_price(row, mapping)
        self.assertEqual(result.unit_price, 7.97)
        self.assertEqual(result.unit, "lb")

    def test_haagen_dazs_per_oz(self) -> None:
        mapping = _mapping(
            "haagen_dazs_ice_cream",
            comparable_unit="oz",
            patterns=(r"haagen.?dazs",),
            maps_to_canonical_id="haagen_dazs_ice_cream",
        )
        row = _row(
            split_product_text="Haagen-Dazs Ice Cream 14 oz",
            advertised_price="2.77",
            package_text="14 oz",
            package_size_min="14",
            package_size_max="14",
            package_unit="oz",
            price_basis="each",
        )
        result = normalize_offer_unit_price(row, mapping)
        self.assertAlmostEqual(result.unit_price, 0.1979, places=3)

    def test_ritz_oreo_package_range_per_oz(self) -> None:
        mapping = _mapping(
            "ritz_crackers_snacks",
            tracker_kind="family",
            comparable_unit="oz",
            patterns=(r"ritz",),
            maps_to_canonical_id="ritz_crackers_snacks",
        )
        row = _row(
            split_product_text="Ritz Crackers",
            advertised_price="2.99",
            package_text="7 to 13.7 oz",
            package_size_min="7",
            package_size_max="13.7",
            package_unit="oz",
            price_basis="each",
        )
        result = normalize_offer_unit_price(row, mapping)
        self.assertIsNotNone(result.unit_price)
        self.assertLess(result.unit_price, 0.5)

    def test_buy_two_get_three_free_chips_manual(self) -> None:
        mapping = _mapping("doritos_nacho_cheese", comparable_unit="oz", patterns=(r"doritos",))
        row = _row(
            split_product_text="Doritos",
            advertised_price="3.99",
            promo_text="Buy 2 Get 3 Free",
            price_basis="each",
            review_reasons="ambiguous_multi_product_offer",
            split_status="group_not_split",
        )
        result = normalize_offer_unit_price(row, mapping)
        self.assertTrue(result.manual_review)

    def test_eggs_eighteen_count(self) -> None:
        mapping = _mapping(
            "eggs_18_count",
            comparable_unit="each",
            patterns=(r"18 count|cage free eggs",),
            maps_to_canonical_id="eggs_18_count",
        )
        row = _row(
            split_product_text="Lucerne Cage Free Large Eggs 18 ct",
            advertised_price="5.0",
            package_text="18 ct",
            package_size_min="18",
            package_size_max="18",
            package_unit="ct",
            price_basis="each",
        )
        result = normalize_offer_unit_price(row, mapping)
        self.assertAlmostEqual(result.unit_price, 0.2778, places=3)


class HistoricalLabelTests(unittest.TestCase):
    def test_all_time_low(self) -> None:
        label = classify_historical(1.0, {"min": 1.05, "median": 1.5, "weeks_seen": 4})
        self.assertEqual(label["historical_label"], "all-time low")
        self.assertTrue(label["is_all_time_low"])

    def test_tied_all_time_low(self) -> None:
        label = classify_historical(1.0, {"min": 1.0, "median": 1.4, "weeks_seen": 4})
        self.assertEqual(label["historical_label"], "tied all-time low")
        self.assertTrue(label["is_tied_all_time_low"])


class IntegrationFixtureTests(unittest.TestCase):
    def test_end_to_end_fixture(self) -> None:
        mappings_path = ROOT / "config/vons_historical_low_category_mappings.csv"
        self.assertTrue(mappings_path.is_file())
        mappings = load_mappings(mappings_path)
        self.assertGreater(len(mappings), 20)

        historical = [
            _row(
                week_start="2026-06-17",
                split_product_text="Fresh Atlantic Salmon Fillets",
                advertised_price="9.99",
                price_basis="per_lb",
                package_unit="lb",
            ),
            _row(
                week_start="2026-06-10",
                split_product_text="Fresh Atlantic Salmon Fillets",
                advertised_price="8.99",
                price_basis="per_lb",
                package_unit="lb",
            ),
        ]
        current = [
            _row(
                split_product_text="Fresh Atlantic Salmon Fillets Farm Raised",
                advertised_price="7.97",
                price_basis="per_lb",
                package_unit="lb",
            )
        ]
        salmon = next(m for m in mappings if m.tracker_key == "category_salmon")
        series = build_weekly_series(historical, salmon)
        self.assertEqual(len(series), 2)
        best = pick_best_row_for_mapping(current, salmon)
        self.assertIsNotNone(best)
        normalized = normalize_offer_unit_price(best, salmon)
        stats_min = min(price for _, price, _ in series)
        label = classify_historical(normalized.unit_price or 0, {"min": stats_min, "median": 9.49, "weeks_seen": 2})
        self.assertEqual(label["historical_label"], "all-time low")


class RunCheckSmokeTests(unittest.TestCase):
    def test_run_check_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            current_csv = tmp_path / "current.csv"
            hist_csv = tmp_path / "hist.csv"
            out_csv = tmp_path / "out.csv"
            out_md = tmp_path / "out.md"

            hist_rows = [
                _row(
                    week_start="2026-06-17",
                    split_product_text="Sweet Bi-Color Corn",
                    raw_offer_text="Sweet Bi-Color Corn 5 for $1",
                    advertised_price="1.0",
                    price_basis="multi_buy",
                    promo_text="5 for $1",
                )
            ]
            current_rows = [
                _row(
                    split_product_text="Sweet Bi-Color Corn LOCAL!",
                    raw_offer_text="Sweet Bi-Color Corn LOCAL! 5 for $1",
                    advertised_price="1.0",
                    price_basis="multi_buy",
                    promo_text="5 for $1",
                )
            ]
            fieldnames = list(hist_rows[0].keys())
            for path, rows in ((hist_csv, hist_rows), (current_csv, current_rows)):
                with path.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)

            ranked = run_check(
                current_week_start="2026-07-01",
                current_week_end="2026-07-07",
                current_split_csv=current_csv,
                historical_paths=[hist_csv],
                mappings_path=ROOT / "config/vons_historical_low_category_mappings.csv",
                costco_csv=None,
                output_csv=out_csv,
                output_md=out_md,
            )
            self.assertTrue(out_csv.is_file())
            self.assertTrue(out_md.is_file())
            corn = [r for r in ranked if r["tracker_key"] == "category_sweet_corn"]
            self.assertEqual(len(corn), 1)


if __name__ == "__main__":
    unittest.main()
