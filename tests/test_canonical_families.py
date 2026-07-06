"""Tests for data/canonical_tracker_families.yaml."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from price_tracker.canonical_families import (
    HOMEPAGE_SECTION_ORDER,
    load_families,
    validate_families,
)

ROOT = Path(__file__).resolve().parents[1]
YAML_PATH = ROOT / "data" / "canonical_tracker_families.yaml"
POPULAR_PATH = ROOT / "data" / "popular_this_week.yaml"


class TestCanonicalFamiliesYaml(unittest.TestCase):
    def test_yaml_file_exists(self) -> None:
        self.assertTrue(YAML_PATH.is_file())

    def test_families_load_without_errors(self) -> None:
        families = load_families()
        self.assertGreaterEqual(len(families), 50)

    def test_required_fields_and_sections(self) -> None:
        families = load_families()
        errors = validate_families(families)
        self.assertEqual(errors, [], msg="\n".join(errors))

    def test_no_duplicate_ids(self) -> None:
        families = load_families()
        ids = [family.id for family in families]
        self.assertEqual(len(ids), len(set(ids)))

    def test_homepage_sections_valid(self) -> None:
        families = load_families()
        valid = set(HOMEPAGE_SECTION_ORDER)
        for family in families:
            self.assertIn(family.homepage_section, valid)

    def test_drinks_section_is_fifth(self) -> None:
        self.assertEqual(HOMEPAGE_SECTION_ORDER[4], "drinks")


class TestPopularThisWeek(unittest.TestCase):
    def test_popular_loads(self) -> None:
        self.assertTrue(POPULAR_PATH.is_file())
        with POPULAR_PATH.open(encoding="utf-8") as handle:
            doc = yaml.safe_load(handle)
        self.assertEqual(doc["week"], "2026-07-01")

    def test_popular_ids_resolve(self) -> None:
        families = load_families()
        known = {family.id for family in families}
        with POPULAR_PATH.open(encoding="utf-8") as handle:
            doc = yaml.safe_load(handle)
        unresolved: list[str] = []
        for store in ("safeway", "vons"):
            for entry in doc["stores"][store]:
                for family_id in entry["tracker_family_ids"]:
                    if family_id not in known:
                        unresolved.append(family_id)
        self.assertEqual(unresolved, [])

    def test_no_shrimp(self) -> None:
        with POPULAR_PATH.open(encoding="utf-8") as handle:
            text = handle.read().lower()
        self.assertNotIn("shrimp", text)

    def test_multi_family_refs(self) -> None:
        with POPULAR_PATH.open(encoding="utf-8") as handle:
            doc = yaml.safe_load(handle)
        safeway_multi = doc["stores"]["safeway"][3]["tracker_family_ids"]
        self.assertGreaterEqual(len(safeway_multi), 2)


if __name__ == "__main__":
    unittest.main()
