"""Build weekly-ad ProductMatcher rows from canonical_tracker_families.yaml."""

from __future__ import annotations

from dataclasses import dataclass

from price_tracker.canonical_families import TrackerFamily, load_families


@dataclass(frozen=True)
class YamlProductMatcher:
    canonical_id: str
    patterns: tuple[str, ...]
    exclude_patterns: tuple[str, ...] = ()
    prefer_patterns: tuple[str, ...] = ()
    normalization: str | None = None
    pick_lowest_in_week: bool = False


def build_yaml_matchers(families: list[TrackerFamily] | None = None) -> tuple[YamlProductMatcher, ...]:
    families = families or load_families()
    matchers: list[YamlProductMatcher] = []
    for family in families:
        matchers.append(
            YamlProductMatcher(
                canonical_id=family.id,
                patterns=family.patterns,
                exclude_patterns=family.exclude_patterns,
                prefer_patterns=family.prefer_patterns,
                normalization=family.normalization,
                pick_lowest_in_week=(
                    family.normalization == "strawberries_per_lb"
                    or family.id
                    in {
                        "eggs_dozen_normalized",
                        "berries_6oz",
                        "hass_avocados_each",
                        "mangoes_each",
                        "chobani_yogurt_per_cup",
                    }
                ),
            )
        )
    return tuple(matchers)


def tracker_family_ids(families: list[TrackerFamily] | None = None) -> list[str]:
    return [family.id for family in (families or load_families())]
