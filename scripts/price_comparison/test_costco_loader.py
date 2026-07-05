"""Tests for regional Costco CSV loading and warehouse isolation."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from price_comparison.costco_loader import (  # noqa: E402
    COSTCO_REGIONS,
    GROCERY_TRACKER_TO_COSTCO_REGION,
    cache_observations_path,
    load_region_observations,
    match_costco_item,
    parse_costco_filename,
)
from price_comparison.costco_warehouse_mapping import (  # noqa: E402
    feed_id_to_warehouse,
    normalize_warehouse_slug,
)
from price_comparison.import_costco_data import import_costco_data  # noqa: E402


class CostcoLoaderTests(unittest.TestCase):
    def test_parse_costco_filename_tustin(self) -> None:
        parsed = parse_costco_filename(Path("2026-07-05_tustin_consolidated.csv"))
        self.assertEqual(parsed, ("2026-07-05", "tustin"))

    def test_parse_costco_filename_san_francisco(self) -> None:
        parsed = parse_costco_filename(
            Path("2026-06-18_san-francisco_consolidated.csv"),
        )
        self.assertEqual(parsed, ("2026-06-18", "san_francisco"))

    def test_normalize_warehouse_slug(self) -> None:
        self.assertEqual(normalize_warehouse_slug("san-francisco"), "san_francisco")
        self.assertEqual(normalize_warehouse_slug("tustin"), "tustin")

    def test_grocery_tracker_mapping(self) -> None:
        self.assertEqual(
            GROCERY_TRACKER_TO_COSTCO_REGION["safeway"],
            "san_francisco",
        )
        self.assertEqual(
            GROCERY_TRACKER_TO_COSTCO_REGION["vons-albertsons"],
            "tustin",
        )
        self.assertNotIn("seattle", GROCERY_TRACKER_TO_COSTCO_REGION.values())

    def test_feed_id_to_warehouse_no_cross_fallback(self) -> None:
        self.assertEqual(feed_id_to_warehouse("safeway_bay_area"), "san_francisco")
        self.assertEqual(feed_id_to_warehouse("vons_albertsons_socal"), "tustin")
        self.assertIsNone(feed_id_to_warehouse("costco_seattle"))

    def test_load_region_observations_preserves_warehouse(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache_dir = root / "cache"
            cache_dir.mkdir()
            cache_path = cache_dir / "observations.json"
            cache_path.write_text(
                json.dumps([
                    {
                        "date": "2026-06-19",
                        "warehouse": "tustin",
                        "itemNumber": "123",
                        "productName": "DORITOS 30 OZ",
                        "price": 6.99,
                        "availability": "in stock",
                        "sourceFile": "2026-06-18_tustin_consolidated.csv",
                        "timestamp": "2026-06-19T03:48:11+00:00",
                    },
                    {
                        "date": "2026-06-19",
                        "warehouse": "san_francisco",
                        "itemNumber": "999",
                        "productName": "OTHER ITEM",
                        "price": 1.0,
                        "availability": "in stock",
                        "sourceFile": "2026-06-18_san-francisco_consolidated.csv",
                        "timestamp": "2026-06-19T03:48:11+00:00",
                    },
                ]),
                encoding="utf-8",
            )

            import os

            os.environ["COSTCO_CACHE_PATH"] = str(cache_path)
            try:
                tustin = load_region_observations("tustin")
                sf = load_region_observations("san_francisco")
            finally:
                os.environ.pop("COSTCO_CACHE_PATH", None)

            self.assertEqual(len(tustin), 1)
            self.assertEqual(tustin[0].region, "tustin")
            self.assertEqual(tustin[0].item_number, "123")
            self.assertEqual(len(sf), 1)
            self.assertEqual(sf[0].region, "san_francisco")

    def test_item_number_match_preferred_over_text(self) -> None:
        from price_comparison.costco_loader import CostcoItem

        catalog = [
            CostcoItem(
                item_number="2014409",
                item_sign="DORITOS NACHO CHEESE NKD 30 OZ",
                sell_price=6.99,
                timestamp="2026-07-05T00:00:00",
                source_file="test.csv",
                region="san_francisco",
                date="2026-07-05",
                availability="in stock",
                parsed=None,
            ),
            CostcoItem(
                item_number="000001",
                item_sign="DORITOS FLAMIN HOT 30 OZ",
                sell_price=5.99,
                timestamp="2026-07-05T00:00:00",
                source_file="test.csv",
                region="san_francisco",
                date="2026-07-05",
                availability="in stock",
                parsed=None,
            ),
        ]
        item, _ = match_costco_item(
            "doritos_nacho_cheese", catalog, warehouse="san_francisco",
        )
        self.assertIsNotNone(item)
        assert item is not None
        self.assertEqual(item.item_number, "2014409")
        self.assertEqual(item.match_method, "item_number")

    def test_region_observations_never_mix_warehouses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "observations.json"
            cache_path.write_text(
                json.dumps([
                    {
                        "date": "2026-07-05",
                        "warehouse": "tustin",
                        "itemNumber": "933402",
                        "productName": "DORITOS",
                        "price": 7.29,
                        "availability": "in stock",
                        "sourceFile": "2026-07-05_tustin_consolidated.csv",
                        "timestamp": "2026-07-05T00:00:00",
                    },
                    {
                        "date": "2026-07-05",
                        "warehouse": "san_francisco",
                        "itemNumber": "933402",
                        "productName": "DORITOS",
                        "price": 6.99,
                        "availability": "in stock",
                        "sourceFile": "2026-07-05_san-francisco_consolidated.csv",
                        "timestamp": "2026-07-05T00:00:00",
                    },
                ]),
                encoding="utf-8",
            )
            import os

            os.environ["COSTCO_CACHE_PATH"] = str(cache_path)
            try:
                sf_prices = {o.price for o in load_region_observations("san_francisco")}
                tustin_prices = {o.price for o in load_region_observations("tustin")}
            finally:
                os.environ.pop("COSTCO_CACHE_PATH", None)

            self.assertEqual(sf_prices, {6.99})
            self.assertEqual(tustin_prices, {7.29})
            self.assertNotEqual(sf_prices, tustin_prices)

    def test_known_regions(self) -> None:
        self.assertIn("seattle", COSTCO_REGIONS)
        self.assertIn("san_francisco", COSTCO_REGIONS)
        self.assertIn("tustin", COSTCO_REGIONS)


class CostcoImportTests(unittest.TestCase):
    def test_import_writes_local_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            (source / "2026-07-05_tustin_consolidated.csv").write_text(
                "timestamp,searchTerm,itemNumber,itemSign,sellPrice,inventoryStatus\n"
                "2026-07-05T18:59:41+00:00,chip,123,DORITOS 30 OZ,6.99,in stock\n",
                encoding="utf-8",
            )

            cache_dir = Path(tmp) / "cache"
            cache_dir.mkdir()
            obs_path = cache_dir / "observations.json"
            manifest_path = cache_dir / "manifest.json"

            import os

            os.environ["COSTCO_DATA_ROOT"] = str(source)
            os.environ["COSTCO_CACHE_PATH"] = str(obs_path)

            # Patch CACHE paths via re-import with custom logic
            from price_comparison import import_costco_data as mod

            original_cache = mod.CACHE_DIR
            original_obs = mod.OBSERVATIONS_PATH
            original_manifest = mod.MANIFEST_PATH
            mod.CACHE_DIR = cache_dir
            mod.OBSERVATIONS_PATH = obs_path
            mod.MANIFEST_PATH = manifest_path
            try:
                manifest = mod.import_costco_data()
            finally:
                mod.CACHE_DIR = original_cache
                mod.OBSERVATIONS_PATH = original_obs
                mod.MANIFEST_PATH = original_manifest
                os.environ.pop("COSTCO_DATA_ROOT", None)
                os.environ.pop("COSTCO_CACHE_PATH", None)

            self.assertTrue(obs_path.is_file())
            self.assertTrue(manifest_path.is_file())
            rows = json.loads(obs_path.read_text(encoding="utf-8"))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["warehouse"], "tustin")
            self.assertEqual(rows[0]["sourceFile"], "2026-07-05_tustin_consolidated.csv")
            self.assertEqual(manifest["observationCount"], 1)


if __name__ == "__main__":
    unittest.main()
