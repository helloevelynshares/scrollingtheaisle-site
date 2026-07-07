"""Per-lb baseline price normalization for seed pipelines.

When a YAML tracker family has size_format_subtitle containing "per lb" and the
scraped product name includes a package weight like "3.5 Lb", the seed pipeline
stores the full package price instead of the per-lb rate.  This module converts
the raw package price to per-lb at the point of baseline generation so the stored
value matches the chart axis unit (dollars per pound).

Used by:
  scripts/generate_safeway_feed_matches.py
  scripts/generate_vons_feed_matches.py
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .canonical_families import TrackerFamily

try:
    from .canonical_families import family_by_id, LEGACY_CANONICAL_TO_FAMILY
except ImportError:
    from canonical_families import family_by_id, LEGACY_CANONICAL_TO_FAMILY


_PER_LB_RE = re.compile(r"\bper\s*lb\b", re.IGNORECASE)
# Matches weights like "3.5 Lb", "3 lb", "1.75 Lbs" in a product name.
_WEIGHT_RE = re.compile(r"\b(\d+(?:\.\d+)?)\s*lbs?\b", re.IGNORECASE)


def _resolve_family_id(canonical_id: str) -> str:
    """Translate a legacy canonical ID to the current YAML family ID if needed."""
    return LEGACY_CANONICAL_TO_FAMILY.get(canonical_id, canonical_id)


def _is_per_lb_family(family: "TrackerFamily | None") -> bool:
    return family is not None and bool(_PER_LB_RE.search(family.size_format_subtitle))


def extract_package_weight_lbs(product_name: str) -> float | None:
    """Return the package weight in pounds extracted from a product name, or None.

    Examples:
      "USDA Choice Bone In Beef Rib Steak Mega Pack - 3.5 Lb"  → 3.5
      "Red Cherries - 1.75 Lb"                                  → 1.75
      "Boneless Skinless Chicken Breast Value Pack - 3.5 Lb"   → 3.5
    """
    m = _WEIGHT_RE.search(product_name)
    if m:
        return float(m.group(1))
    return None


def normalize_baseline_price(
    canonical_id: str,
    product_name: str,
    price: float,
    families: "dict[str, TrackerFamily] | None" = None,
) -> tuple[float, bool]:
    """Return (per_lb_price, was_normalized).

    If the canonical family is a per-lb tracker and the product name contains a
    package weight, divides price by that weight and returns (per_lb_price, True).
    Otherwise returns (price, False) unchanged.

    Args:
        canonical_id: The canonical/family ID from the CSV (may be a legacy ID).
        product_name: The retailer product name string (e.g. "Red Cherries - 1.75 Lb").
        price: The raw package price to potentially divide.
        families: Pre-loaded family dict; loaded from YAML if not provided.
    """
    if families is None:
        families = family_by_id()

    family_id = _resolve_family_id(canonical_id)
    family = families.get(family_id) or families.get(canonical_id)

    if not _is_per_lb_family(family):
        return price, False

    weight = extract_package_weight_lbs(product_name)
    if not weight or weight <= 0:
        return price, False

    per_lb = round(price / weight, 2)
    return per_lb, True
