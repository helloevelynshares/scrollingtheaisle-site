"""UI smoke tests: no internal IDs in user-facing copy."""

from __future__ import annotations

import re
import unittest

from price_tracker.canonical_families import load_families

INTERNAL_ID_PATTERN = re.compile(
    r"\b(regular_bags|5_13oz|party_size|per_lb|dozen_normalized|family_size)\b",
    re.I,
)


class TestNoInternalIdsExposed(unittest.TestCase):
    def test_display_names_hide_internal_ids(self) -> None:
        for family in load_families():
            self.assertFalse(
                INTERNAL_ID_PATTERN.search(family.canonical_tracker_family),
                msg=family.id,
            )
            if "_" in family.id:
                self.assertNotEqual(
                    family.id.lower(),
                    family.canonical_tracker_family.lower(),
                    msg=f"raw id exposed as title: {family.id}",
                )

    def test_subtitles_are_user_facing(self) -> None:
        for family in load_families():
            self.assertTrue(len(family.size_format_subtitle) > 0)
            self.assertNotIn("regular_bags", family.size_format_subtitle.lower())


if __name__ == "__main__":
    unittest.main()
