"""Content-first deal scorer (TikTok/short-form selection).

This scorer is DELIBERATELY SEPARATE from the canonical tracker-graph match
score / eligibility logic in ``scripts/price_tracker/``. It NEVER requires a
canonical tracker family, an exact price baseline, or a graph-safe match. Its
only job is to answer: "how good is this as a *content* deal to talk about in a
short-form video this week?"

Reward rules (see :func:`score_content_deal`):

* popular / recognizable grocery items
* snack / produce / protein / dairy / freezer categories
* Costco-beating unit price (with a usable, non-proxy comparison)
* near-Costco price with a smaller-quantity / variety advantage
* strong absolute ad price
* clearly-labeled Friday-only deals (rewarded, not zeroed out)
* seasonal produce
* good TikTok hook potential

The output is a 0-100 ``content_score`` plus a component breakdown so callers
can show *why* an item scored the way it did.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

# Categories that reliably perform in grocery short-form content.
HIGH_INTEREST_CATEGORIES = {
    "produce",
    "snacks",
    "snack",
    "protein",
    "meat",
    "seafood",
    "dairy",
    "frozen",
    "freezer",
    "beverage",
    "drinks",
    "bakery",
}

# Match types that are strong enough to make a "cheaper than Costco" claim.
USABLE_COSTCO_MATCH_TYPES = {
    "exact same product",
    "same product different size",
}

# Match types that are directional only (never a hard "beats Costco" claim).
PROXY_COSTCO_MATCH_TYPES = {
    "same category comparable",
    "proxy / manual-review",
}

# Component weights (max sum == 100).
_MAX = {
    "shopper_recognizability": 15,
    "category_fit": 12,
    "costco_unit_win": 22,
    "near_costco_variety": 12,
    "absolute_price": 15,
    "friday_flag_bonus": 6,
    "seasonal_produce": 8,
    "tiktok_hook": 10,
}

_STRENGTH_SCALE = {"strong": 1.0, "moderate": 0.6, "weak": 0.3, "none": 0.0}


@dataclass(frozen=True)
class ContentScoreInput:
    """Feature bundle for one candidate content deal.

    All fields are optional-ish and default to conservative values so the
    scorer works even with sparse data (ad-deal-only items with no Costco
    mapping still get a score).
    """

    category: str = "other"
    recognizable_brand: bool = False
    # Percent the grocery unit price is *below* Costco (positive == grocery
    # cheaper). ``None`` when there is no usable Costco comparison.
    costco_percent_cheaper: float | None = None
    costco_match_type: str | None = None
    near_costco_with_smaller_qty: bool = False
    # "strong" | "moderate" | "weak", how good the absolute ad price is
    # (seasonal-low, deep discount, cheap unit, etc.).
    absolute_price_strength: str = "moderate"
    is_friday_only: bool = False
    is_seasonal_produce: bool = False
    # "strong" | "moderate" | "weak" | "none": TikTok hook potential.
    tiktok_hook: str = "moderate"


@dataclass(frozen=True)
class ContentScore:
    content_score: int
    components: dict[str, int] = field(default_factory=dict)
    max_components: dict[str, int] = field(default_factory=dict)
    rationale: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _clamp(value: float, hi: int) -> int:
    return int(max(0, min(hi, round(value))))


def _category_key(category: str | None) -> str:
    return (category or "other").strip().lower()


def _costco_unit_win_points(pct: float | None, match_type: str | None) -> tuple[int, str | None]:
    """Reward a genuine Costco-beating unit price.

    Only usable (non-proxy) match types can earn the full award; proxy/
    category matches earn a small directional credit at most.
    """
    if pct is None or pct <= 0:
        return 0, None
    match = (match_type or "").strip().lower()
    if match in USABLE_COSTCO_MATCH_TYPES:
        # Scale: >=25% cheaper == full points; 5% cheaper == ~5 pts.
        raw = min(_MAX["costco_unit_win"], (pct / 25.0) * _MAX["costco_unit_win"])
        return _clamp(raw, _MAX["costco_unit_win"]), (
            f"beats Costco by ~{pct:.0f}% on a usable match"
        )
    if match in PROXY_COSTCO_MATCH_TYPES:
        # Directional only, cap low so proxies never look like hard wins.
        raw = min(6, (pct / 25.0) * 6)
        return _clamp(raw, 6), f"directionally under Costco (~{pct:.0f}%, proxy only)"
    return 0, None


def score_content_deal(features: ContentScoreInput) -> ContentScore:
    """Return a 0-100 content score + component breakdown for one deal."""
    comp: dict[str, int] = {}
    why: list[str] = []

    # 1. Shopper recognizability.
    comp["shopper_recognizability"] = (
        _MAX["shopper_recognizability"] if features.recognizable_brand else 6
    )
    if features.recognizable_brand:
        why.append("recognizable/popular item")

    # 2. Category fit.
    cat = _category_key(features.category)
    comp["category_fit"] = _MAX["category_fit"] if cat in HIGH_INTEREST_CATEGORIES else 2
    if cat in HIGH_INTEREST_CATEGORIES:
        why.append(f"high-interest category ({cat})")

    # 3. Costco-beating unit price (usable match required for full credit).
    win_pts, win_reason = _costco_unit_win_points(
        features.costco_percent_cheaper, features.costco_match_type
    )
    comp["costco_unit_win"] = win_pts
    if win_reason:
        why.append(win_reason)

    # 4. Near-Costco price with smaller-quantity / variety advantage.
    comp["near_costco_variety"] = (
        _MAX["near_costco_variety"] if features.near_costco_with_smaller_qty else 0
    )
    if features.near_costco_with_smaller_qty:
        why.append("near-Costco price with smaller-quantity/variety edge")

    # 5. Absolute ad-price strength.
    strength = (features.absolute_price_strength or "moderate").strip().lower()
    comp["absolute_price"] = _clamp(
        _STRENGTH_SCALE.get(strength, 0.6) * _MAX["absolute_price"],
        _MAX["absolute_price"],
    )
    if strength == "strong":
        why.append("strong absolute ad price")

    # 6. Friday-only deals are still REWARDED (just clearly labeled).
    comp["friday_flag_bonus"] = _MAX["friday_flag_bonus"] if features.is_friday_only else 0
    if features.is_friday_only:
        why.append("labeled Friday-only doorbuster")

    # 7. Seasonal produce.
    comp["seasonal_produce"] = (
        _MAX["seasonal_produce"] if features.is_seasonal_produce else 0
    )
    if features.is_seasonal_produce:
        why.append("in-season produce")

    # 8. TikTok hook potential.
    hook = (features.tiktok_hook or "moderate").strip().lower()
    comp["tiktok_hook"] = _clamp(
        _STRENGTH_SCALE.get(hook, 0.6) * _MAX["tiktok_hook"], _MAX["tiktok_hook"]
    )
    if hook == "strong":
        why.append("strong TikTok hook")

    total = _clamp(sum(comp.values()), 100)
    return ContentScore(
        content_score=total,
        components=comp,
        max_components=dict(_MAX),
        rationale=why,
    )
