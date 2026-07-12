#!/usr/bin/env python3
"""Expanded TikTok/script shortlist from full split_offer_items for 2026-07-08 week."""

from __future__ import annotations

import csv
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from price_comparison.canonical_metadata import CANONICAL_PACKAGES
from price_comparison.compare import compare_prices
from price_comparison.costco_loader import load_location_catalog, match_costco_item
from price_tracker.canonical_families import LEGACY_CANONICAL_TO_FAMILY, family_by_id
from price_tracker.canonical_match_eligibility import EligibilityIndex
from price_tracker.normalization import base_normalize_unit_price
from price_tracker.shortlist_copy import family_shortlist_blurb, is_family_size_family
from weekly_ad_analysis.benchmarks import compute_benchmark

WEEK_START = "2026-07-08"
WEEK_END = "2026-07-14"
SPLIT_CSV = Path(
    "/Users/evelynchan/Documents/scrolling-the-aisle/outputs/product_discovery_safeway/split_offer_items.csv"
)
OUT_JSON = ROOT / "output" / "weekly_deals" / "2026-07-08" / "expanded_shortlist.json"

FAMILY_TO_CANONICAL = {v: k for k, v in LEGACY_CANONICAL_TO_FAMILY.items()}
EXTRA_CANONICAL = {
    "ritz": "ritz_crackers_snacks",
    "wheat thins": "nabisco",
    "triscuit": "nabisco",
    "coca-cola": "coke_zero",
    "pepsi 2 liter": None,  # exclude 12pk proxy
    "coca-cola 2 liter": None,
    "doritos": "doritos_nacho_cheese",
    "ruffles": "doritos_nacho_cheese",
    "cheetos": "cheetos_crunchy",
    "lay's": "doritos_nacho_cheese",
    "hass avocado": "avocados",
    "seedless grape": "grapes",
    "cherries": "grapes",
    "cherry": "grapes",
    "strawberr": "strawberries",
    "lucerne large eggs": "eggs_18_count",
    "ben & jerry": "haagen_dazs_ice_cream",
    "oreo": "oreos_sandwich_cookies",
    "chips ahoy": "oreos_sandwich_cookies",
    "butter": None,
    "kellogg": "cheerios",
    "cheez-it": None,
}

# Map product text hints → tracker family for historical lookup
HIST_MAP = {
    r"hass avocado": "hass_avocados_each",
    r"land o.?lakes butter|lucerne butter": "butter_16oz",
    r"smoked.*salmon|nova salmon": "salmon",
    r"doritos": "doritos_5_13oz",
    r"ruffles potato": "ruffles_regular_bags",
    r"red seedless grape|green seedless grape": "seedless_grapes_per_lb",
    r"cherr": "cherries_per_lb",
    r"strawberr": "strawberries_1_2lb",
    r"lucerne large eggs|large eggs": "eggs_dozen_normalized",
    r"ritz cracker": "ritz_crackers",
    r"nabisco.*snack cracker|nabisco snack cracker|chicken in a biskit|triscuit|wheat thins": "nabisco_snack_crackers",
    r"coca-cola, pepsi|coca-cola 12|pepsi 12": "coca_cola_12packs",
    r"coca-cola 2 liter": None,
    r"pepsi 2 liter": None,
    r"chicken breast.*organic|o organics.*chicken breast": "chicken_breast_per_lb",
    r"chips ahoy": "chips_ahoy",
    r"oreo": "oreo_family_size",
    r"cheez-it": "cheez_it_crackers",
    r"frito.?lay variety": "lays_party_size",
    r"tostitos.*party|ruffles party": "lays_party_size",
    r"kellogg.*cereal|kashi cereal": "general_mills_cereal_regular",
    r"ben & jerry": "ben_jerrys_ice_cream",
    r"signature select ice cream": "breyers_ice_cream",
}


@dataclass
class AdItem:
    id: str
    store: str
    name: str
    raw_offer: str
    ad_price_raw: float
    effective_price: float | None
    price_basis: str
    package_text: str
    availability: str
    promo_text: str
    purchase_requirement: str
    family_id: str | None = None
    display_name: str | None = None
    subtitle: str | None = None
    shortlist_blurb: str | None = None
    baseline: float | None = None
    baseline_pct: float | None = None
    hist_label: str = "Unknown"
    hist_bucket: str = "insufficient history"
    costco_note: str | None = None
    costco_pct: float | None = None
    costco_winner: str | None = None
    script_score: float = 0.0
    confidence: str = "Medium"
    script_label: str = "Quick mention only"
    script_reason: str = ""
    category: str = "other"
    caveats: list[str] = field(default_factory=list)


def load_baselines() -> tuple[dict[str, float], dict[str, float]]:
    sw: dict[str, float] = {}
    text = (ROOT / "src/data/priceTrackerFallback.ts").read_text()
    for m in re.finditer(r'"([^"]+)":\s*\{\s*price:\s*([\d.]+)', text):
        sw[m.group(1)] = float(m.group(2))
    vn: dict[str, float] = {}
    text = (ROOT / "src/data/vonsBaseline.generated.ts").read_text()
    for m in re.finditer(r'"([^"]+)":\s*\{\s*"baselinePrice":\s*([\d.]+)', text):
        vn[m.group(1)] = float(m.group(2))
    return sw, vn


def categorize(name: str) -> str:
    n = name.lower()
    rules = [
        ("produce", ["avocado", "mango", "grape", "cherr", "corn", "peach", "plum", "nectarine", "berry", "apple", "melon", "banana", "pepper", "lettuce", "salad"]),
        ("meat", ["chicken", "beef", "pork", "salmon", "shrimp", "lamb", "turkey", "rib", "steak", "ground", "bacon", "sausage"]),
        ("dairy", ["butter", "egg", "cheese", "yogurt", "milk", "cream cheese"]),
        ("snacks", ["doritos", "ruffles", "cheetos", "lay", "oreo", "ritz", "cheez", "goldfish", "chips ahoy", "tostitos", "frito", "cracker", "cookie", "bar", "clif", "quest", "kind"]),
        ("drinks", ["coca", "pepsi", "dr pepper", "sparkling", "la croix", "lacroix", "celsius", "juice", "tea", "water", "soda", "7up"]),
        ("frozen", ["ice cream", "ben", "jerry", "haagen", "tillamook", "klondike", "talenti", "yasso", "pizza", "frozen"]),
        ("pantry", ["cereal", "kellogg", "kashi", "pasta", "macaroni", "pillsbury", "oil"]),
    ]
    for cat, kws in rules:
        if any(k in n for k in kws):
            return cat
    return "other"


def family_for_item(name: str) -> str | None:
    n = name.lower()
    for pat, fid in HIST_MAP.items():
        if fid is None:
            continue
        if re.search(pat, n):
            return fid
    return None


_ELIGIBILITY = EligibilityIndex()


def _keyword_confidence(row: dict) -> str:
    """Mirror the tracker's coarse keyword-confidence signal for the gate."""
    text = (row.get("split_product_text") or row.get("raw_product_text") or "").lower()
    return "medium" if re.search(r",|\sor\s", text) else "high"


def family_size_eligibility(row: dict, fid: str) -> str:
    """Reuse the canonical match eligibility gate the tracker uses.

    Returns the match decision (accepted | manual_review | rejected). Only
    "accepted" offers may claim the family-size deal in the shortlist.
    """
    return _ELIGIBILITY.evaluate(
        row, fid, keyword_confidence=_keyword_confidence(row)
    ).match_decision


def purchase_req(row: dict) -> str:
    parts = []
    promo = (row.get("promo_text") or "").strip()
    raw = (row.get("raw_offer_text") or "").strip()
    if promo:
        parts.append(promo)
    for pat in [
        r"when you buy \d+",
        r"buy \d+ or more",
        r"mix or match any \d+",
        r"digital coupon",
        r"with digital coupon",
        r"member price",
        r"\d+ for \$",
        r"\d+ lb bag",
    ]:
        m = re.search(pat, raw, re.I)
        if m and m.group(0).lower() not in promo.lower():
            parts.append(m.group(0))
    return "; ".join(dict.fromkeys(parts)) or "Member price (Safeway/Vons for U)"


def canonical_for_text(name: str) -> str | None:
    n = name.lower()
    for hint, cid in EXTRA_CANONICAL.items():
        if hint in n:
            return cid
    return None


def costco_compare(name: str, price: float, size_hint: str, region: str, region_id: str, label: str):
    cid = canonical_for_text(name)
    if not cid or cid not in CANONICAL_PACKAGES:
        return None, None, None
    cat = load_location_catalog(region)
    item, note = match_costco_item(cid, cat, warehouse=region)
    if not item:
        return note, None, None
    r = compare_prices(
        canonical_id=cid,
        grocery_feed_id="x",
        grocery_store_label=label,
        grocery_effective_price=price,
        grocery_size_label=size_hint,
        costco_region_id=region_id,
        costco_store_label=f"Costco {region.replace('_', ' ').title()}",
        costco_item=item,
        costco_searched=True,
    )
    pct = None
    if r.grocery_unit_price and r.costco_unit_price and r.costco_unit_price > 0:
        pct = round((r.costco_unit_price - r.grocery_unit_price) / r.costco_unit_price * 100, 1)
    note = r.comparison_note or (f"{item.item_sign[:50]} ${item.sell_price}")
    return note, pct, r.winner


def script_score(item: AdItem) -> float:
    s = 0.0
    pop = {
        "doritos": 15, "ruffles": 12, "cheetos": 12, "lay": 12, "oreo": 14, "ritz": 13,
        "cheez-it": 12, "chips ahoy": 11, "butter": 16, "egg": 16, "chicken": 18,
        "avocado": 17, "strawberr": 16, "grape": 14, "cherr": 14, "corn": 13, "salmon": 12,
        "ben & jerry": 15, "ice cream": 14, "coca": 13, "pepsi": 12, "cereal": 11,
        "pork": 14, "ground beef": 15, "whole chicken": 17,
    }
    nl = item.name.lower()
    for k, v in pop.items():
        if k in nl:
            s += v
            break
    else:
        s += 5

    if item.baseline_pct is not None:
        if item.baseline_pct >= 40:
            s += 25
        elif item.baseline_pct >= 20:
            s += 15
        elif item.baseline_pct >= 10:
            s += 8
        elif item.baseline_pct < 0:
            s -= 10

    hb = item.hist_bucket
    s += {"all-time low": 20, "near all-time low": 15, "strong sale": 10, "normal sale": 4}.get(hb, 0)

    if item.costco_pct is not None:
        if item.costco_pct >= 15:
            s += 20
        elif item.costco_pct >= 0:
            s += 10
        elif item.costco_pct >= -10:
            s += 5
        else:
            s -= 8

    if item.availability == "full_week":
        s += 10
    elif item.availability == "friday_only":
        s -= 12

    if "2 liter" in nl and "12" in item.category:
        s -= 50
    if "wrong" in " ".join(item.caveats).lower():
        s -= 40

    for c in item.caveats:
        if "10 lb bag" in c.lower() or "buy 10" in c.lower() or "buy 4" in c.lower():
            s -= 3

    if item.confidence == "Low":
        s -= 15
    return round(s, 1)


def label_item(item: AdItem) -> str:
    if any("do not" in c.lower() or "wrong match" in c.lower() for c in item.caveats):
        return "Do not mention"
    if item.confidence == "Low" or "verify" in item.script_reason.lower():
        if item.script_score >= 55:
            return "Manual verification first"
        return "Do not mention" if item.script_score < 30 else "Manual verification first"
    if item.script_score >= 70 and item.availability == "full_week":
        return "Lead-worthy"
    if item.script_score >= 55:
        return "Strong supporting mention"
    if item.script_score >= 35:
        return "Quick mention only"
    return "Do not mention"


def load_rows(banner: str) -> list[dict]:
    with SPLIT_CSV.open(newline="", encoding="utf-8") as f:
        return [
            r for r in csv.DictReader(f)
            if r.get("week_start") == WEEK_START and r.get("banner") == banner
        ]


def row_to_item(row: dict, store: str, sw_base: dict, vn_base: dict) -> AdItem | None:
    raw_price = row.get("advertised_price")
    if not raw_price:
        return None
    try:
        p = float(raw_price)
    except ValueError:
        return None
    if p <= 0:
        return None

    eff = base_normalize_unit_price(row)
    name = (row.get("split_product_text") or row.get("raw_product_text") or "").strip()
    if not name:
        return None

    avail = row.get("availability_type_guess") or "full_week"
    caveats: list[str] = []

    # Known bad matches
    nl = name.lower()
    if "coca-cola 2 liter" in nl or "pepsi 2 liter" in nl or "7up 2 liter" in nl:
        caveats.append("2-liter bottle: NOT 12-pack soda; do not use for 12-pack tracker narrative")
    if "coca-cola, pepsi" in nl and store == "Safeway":
        caveats.append("Multi-brand soda block, verify 12-pack vs 2-liter in store")
    if "weber seasoning" in nl and "kettle" in nl:
        caveats.append("Multi-product promo block: Kettle chips price unclear from split row")

    if "sold in 10 lb bag" in (row.get("raw_offer_text") or "").lower():
        caveats.append("Sold in 10 lb bag minimum (~$9.90 total)")

    fid = family_for_item(name)
    fam = family_by_id().get(fid) if fid else None

    # Gate family-size families (e.g. Nabisco family-size snack crackers) through
    # the SAME canonical match eligibility used by the durable tracker. Only
    # offers that would be ACCEPTED (family-size confirmation, allowed product
    # lines, no Ritz-led/Oreo/single-serve/cookie negatives) may claim the
    # "family-size boxes are $X" deal. Standard-size / Ritz-led mix-or-match
    # rows are not this family, so drop the attribution entirely rather than
    # mislabel them.
    family_size_eligible = False
    if fam is not None and is_family_size_family(fam):
        if family_size_eligibility(row, fid) == "accepted":
            family_size_eligible = True
        else:
            fid = None
            fam = None

    display_name = fam.display_name if fam else None
    subtitle = fam.subtitle if fam else None
    shortlist_blurb = (
        family_shortlist_blurb(
            fam,
            eff if eff is not None else p,
            family_size_eligible=family_size_eligible,
        )
        if fam
        else None
    )
    baselines = sw_base if store == "Safeway" else vn_base
    baseline = baselines.get(fid) if fid else None
    b_pct = None
    if baseline and eff:
        b_pct = round((baseline - eff) / baseline * 100, 1)

    hist_label = "Unknown"
    hist_bucket = "insufficient history"
    if fid:
        feed = "safeway_bay_area" if store == "Safeway" else "vons_albertsons_socal"
        bench = compute_benchmark(fid, "canonical", feed, eff, week_start=WEEK_START)
        hist_bucket = bench.benchmark_bucket
        hist_label = {
            "all-time low": "Historical low",
            "near all-time low": "Near historical low",
            "strong sale": "Typical sale",
            "normal sale": "Typical sale",
            "weak sale": "Worse than previous",
        }.get(hist_bucket, "Unknown")

    region = "san_francisco" if store == "Safeway" else "tustin"
    rid = "costco_sf" if store == "Safeway" else "costco_oc"
    costco_note, costco_pct, costco_winner = costco_compare(
        name, eff or p, row.get("package_text") or "", region, rid, store
    )

    conf = "High"
    if caveats or "selected varieties" in nl:
        conf = "Medium"
    if "2 liter" in nl:
        conf = "Low"
    if row.get("split_confidence") and float(row.get("split_confidence") or 1) < 0.75:
        conf = "Low"

    item = AdItem(
        id=row.get("split_item_id", ""),
        store=store,
        name=name,
        raw_offer=(row.get("raw_offer_text") or "")[:200],
        ad_price_raw=p,
        effective_price=eff,
        price_basis=row.get("price_basis") or "",
        package_text=row.get("package_text") or "",
        availability=avail,
        promo_text=row.get("promo_text") or "",
        purchase_requirement=purchase_req(row),
        family_id=fid,
        display_name=display_name,
        subtitle=subtitle,
        shortlist_blurb=shortlist_blurb,
        baseline=baseline,
        baseline_pct=b_pct,
        hist_label=hist_label,
        hist_bucket=hist_bucket,
        costco_note=costco_note,
        costco_pct=costco_pct,
        costco_winner=costco_winner,
        confidence=conf,
        category=categorize(name),
        caveats=caveats,
    )
    item.script_score = script_score(item)
    item.script_label = label_item(item)

    reasons = []
    if b_pct and b_pct >= 15:
        reasons.append(f"{b_pct:.0f}% below baseline")
    if hist_bucket in ("all-time low", "near all-time low"):
        reasons.append(hist_label.lower())
    if costco_pct and costco_pct >= 10:
        reasons.append(f"beats Costco by ~{costco_pct:.0f}% per unit")
    elif costco_pct is not None and -10 <= costco_pct < 10:
        reasons.append("close to Costco with smaller pack")
    elif costco_pct is not None and costco_pct < -10:
        reasons.append("Costco cheaper on unit math")
    if avail == "friday_only":
        reasons.append("Friday-only")
    if not reasons:
        reasons.append("seasonal promo" if item.category == "produce" else "ad highlight")
    item.script_reason = "; ".join(reasons)
    return item


def analyze_store(store: str, sw_base: dict, vn_base: dict) -> list[AdItem]:
    items = []
    for row in load_rows(store):
        it = row_to_item(row, store, sw_base, vn_base)
        if it:
            items.append(it)
    items.sort(key=lambda x: x.script_score, reverse=True)
    return items


def pick_exec(items: list[AdItem], store: str) -> dict:
    fw = [i for i in items if i.availability == "full_week" and i.script_label != "Do not mention"]
    fri = [i for i in items if i.availability == "friday_only" and i.script_label != "Do not mention"]
    costco_beat = [i for i in fw if i.costco_pct is not None and i.costco_pct >= 10]
    costco_close = [i for i in fw if i.costco_pct is not None and -10 <= i.costco_pct < 10]
    staple = [i for i in fw if i.category in ("dairy", "meat", "pantry") and i.baseline_pct and i.baseline_pct >= 15]
    avoid = [i for i in items if i.script_label == "Do not mention"]

    def best(lst, default=None):
        return lst[0].name if lst else default

    return {
        "best_lead": best([i for i in fw if i.script_label == "Lead-worthy"], best(fw)),
        "best_costco_beating": best(costco_beat),
        "best_full_week_staple": best(staple, best(fw)),
        "best_friday_only": best(fri),
        "best_costco_close_smaller_qty": best(costco_close),
        "avoid": [i.name for i in avoid[:8]],
    }


def main():
    sw_base, vn_base = load_baselines()
    safeway = analyze_store("Safeway", sw_base, vn_base)
    vons = analyze_store("Vons", sw_base, vn_base)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "week_start": WEEK_START,
        "week_end": WEEK_END,
        "safeway": {
            "total_priced": len(safeway),
            "exec": pick_exec(safeway, "Safeway"),
            "items": [asdict(i) for i in safeway],
        },
        "vons": {
            "total_priced": len(vons),
            "exec": pick_exec(vons, "Vons"),
            "items": [asdict(i) for i in vons],
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    print(f"Safeway: {len(safeway)} priced items")
    print(f"Vons: {len(vons)} priced items")
    for store, items in [("Safeway", safeway), ("Vons", vons)]:
        print(f"\n{store} top 12:")
        for i in items[:12]:
            print(f"  [{i.script_score}] {i.script_label}: ${i.effective_price} {i.name[:45]} | {i.availability}")


if __name__ == "__main__":
    main()
