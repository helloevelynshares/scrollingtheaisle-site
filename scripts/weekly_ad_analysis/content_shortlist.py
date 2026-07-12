"""Content-first weekly-ad deal shortlist generator (ANALYSIS ONLY).

This is a SEPARATE analysis mode from the canonical tracker-graph pipeline. It
produces a content/TikTok-oriented view of a week's grocery ad that can INCLUDE
ad-deal-only items (no canonical family), missing-Costco items, proxy matches,
and Friday-only deals, exactly the items the graph-safe report downranks.

It NEVER writes to ``weeklyAdPrices.generated.ts`` or any generated graph TS,
and it never mutates canonical eligibility. It only reads:

* the sibling vision pipeline ``split_offer_items.csv`` (raw ad provenance)
* the latest Costco consolidated CSV for the store's warehouse
* two content-mode configs: ``config/content_shortlist_seed.csv`` and
  ``config/content_costco_mappings.csv``

and writes four analysis artifacts under ``output/weekly_deals/<week>/``.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from price_comparison.costco_loader import costco_data_root  # noqa: E402
from weekly_ad_analysis.content_score import (  # noqa: E402
    ContentScoreInput,
    score_content_deal,
)

CONFIG_DIR = ROOT / "config"
SEED_CSV = CONFIG_DIR / "content_shortlist_seed.csv"
COSTCO_MAP_CSV = CONFIG_DIR / "content_costco_mappings.csv"

# Warehouse rules (must match canonical pipeline): Safeway -> SF, Vons -> Tustin.
STORE_WAREHOUSE = {
    "safeway": ("san_francisco", "san-francisco", "Costco San Francisco"),
    "vons": ("tustin", "tustin", "Costco Tustin"),
}

STORE_LABEL = {"safeway": "Safeway", "vons": "Vons"}

# Sibling vision-pipeline offer rows (raw ad text + page provenance).
SIBLING_OUTPUTS = Path.home() / "Documents" / "scrolling-the-aisle" / "outputs"
SPLIT_CSV = {
    "safeway": SIBLING_OUTPUTS / "product_discovery_safeway" / "split_offer_items.csv",
    "vons": SIBLING_OUTPUTS / "product_discovery_vons" / "split_offer_items.csv",
}

SOURCE_PDF = {
    "safeway": "safeway 7-8 - 7-14.pdf",
    "vons": "vons 7-8 - 7-14.pdf",
}

USABLE_MATCH_TYPES = {"exact same product", "same product different size"}
PROXY_MATCH_TYPES = {"same category comparable", "proxy / manual-review"}

SECTION_TITLES = {
    1: "Lead-worthy Costco beaters",
    2: "Costco-close but better for variety / smaller quantity",
    3: "High-interest ad deals even without Costco",
    4: "Friday-only deals",
    5: "Manual verification required",
    6: "Do not use",
}


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"true", "1", "yes", "y"}


def _to_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


# --------------------------------------------------------------------- configs

def load_seed(week: str, store: str) -> list[dict]:
    rows: list[dict] = []
    with SEED_CSV.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["week_start"] == week and row["store"] == store:
                rows.append(row)
    return rows


def load_costco_mappings() -> dict[tuple[str, str], dict]:
    out: dict[tuple[str, str], dict] = {}
    with COSTCO_MAP_CSV.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            out[(row["content_item_id"], row["warehouse"])] = row
    return out


# ---------------------------------------------------------------- ad provenance

def load_split_rows(store: str, week: str) -> list[dict]:
    path = SPLIT_CSV[store]
    rows: list[dict] = []
    if not path.is_file():
        return rows
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("week_start") == week:
                rows.append(row)
    return rows


def _norm(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


def find_split_row(query: str, split_rows: list[dict], store: str) -> dict | None:
    """Find the first row matching ``query`` whose provenance is this store.

    The sibling consolidated CSV mixes Safeway and Vons rows, so we must not
    let a Safeway shortlist item pull a Vons-sourced offer (and vice versa).
    """
    q = _norm(query)
    for row in split_rows:
        source = _norm(row.get("source_file")) + " " + _norm(row.get("banner"))
        if store not in source:
            continue
        blob = _norm(
            " ".join(
                row.get(k) or ""
                for k in ("raw_offer_text", "raw_product_text", "split_product_text")
            )
        )
        if q in blob:
            return row
    return None


# -------------------------------------------------------------------- costco

def _latest_consolidated_csv(filename_slug: str) -> Path | None:
    root = costco_data_root()
    if not root.is_dir():
        return None
    candidates = sorted(root.glob(f"*_{filename_slug}_consolidated.csv"))
    return candidates[-1] if candidates else None


def costco_price_for_item(filename_slug: str, item_number: str) -> tuple[float | None, str | None, str | None, str | None]:
    """Return (price, item_sign, source_file, date) for one Costco item number."""
    path = _latest_consolidated_csv(filename_slug)
    if path is None or not item_number:
        return None, None, None, None
    date_match = re.match(r"^(\d{4}-\d{2}-\d{2})_", path.name)
    file_date = date_match.group(1) if date_match else None
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if (row.get("itemNumber") or "").strip() == item_number:
                price = _to_float(row.get("sellPrice"))
                return price, (row.get("itemSign") or "").strip(), path.name, file_date
    return None, None, path.name, file_date


# ------------------------------------------------------------------- assembly

@dataclass
class ContentItem:
    content_item_id: str
    display_item: str
    category: str
    raw_offer_text: str | None
    source_pdf: str | None
    source_page: int | None
    ad_price_effective: float | None
    ad_unit_label: str
    package_text: str | None
    availability: str
    grocery_unit_price: float | None
    compare_basis: str
    costco_item_number: str | None
    costco_item_sign: str | None
    costco_warehouse_label: str
    costco_price: float | None
    costco_qty: float | None
    costco_unit_price: float | None
    match_type: str
    pct_diff_vs_costco: float | None
    is_coverage_gap: bool
    graph_update: bool
    content_score: int
    content_score_components: dict = field(default_factory=dict)
    content_score_rationale: list = field(default_factory=list)
    safe_for_script: str = ""
    can_say_cheaper_than_costco: bool = False
    script_one_liner: str = ""
    needs_manual_verification: bool = False
    primary_section: int = 6
    prev_report_status: str = ""
    why_missed: str = ""
    notes: str = ""
    costco_source_file: str | None = None
    costco_date: str | None = None


def _availability_label(avail: str) -> str:
    return "Friday-only" if avail == "friday_only" else "full-week"


def _pct(costco_unit: float | None, grocery_unit: float | None) -> float | None:
    if costco_unit is None or grocery_unit is None or costco_unit <= 0:
        return None
    return round(((costco_unit - grocery_unit) / costco_unit) * 100, 1)


def _safe_for_script(item: ContentItem, seed: dict) -> str:
    if _truthy(seed.get("needs_manual_verification")):
        return "manual verification"
    pct = item.pct_diff_vs_costco
    usable = item.match_type in USABLE_MATCH_TYPES and not item.is_coverage_gap
    proxy = item.match_type in PROXY_MATCH_TYPES
    if usable and pct is not None and pct >= 20:
        return "lead-worthy"
    if usable and pct is not None and pct >= 8:
        return "strong supporting mention"
    if usable and pct is not None and pct > -8:
        return "quick mention"
    if usable and pct is not None and pct <= -8:
        # Costco clearly cheaper but same product, variety/smaller-buy angle.
        return "quick mention"
    if proxy and pct is not None and pct > 0 and not item.is_coverage_gap:
        return "strong supporting mention"
    strength = (seed.get("absolute_price_strength") or "moderate").lower()
    if strength == "strong":
        return "strong supporting mention"
    return "quick mention"


def _can_say_cheaper(item: ContentItem) -> bool:
    return (
        item.match_type in USABLE_MATCH_TYPES
        and not item.is_coverage_gap
        and item.pct_diff_vs_costco is not None
        and item.pct_diff_vs_costco >= 8
    )


def _one_liner(item: ContentItem, store_label: str) -> str:
    """Build a script-ready one-liner following the fixed wording rules."""
    pct = item.pct_diff_vs_costco
    has_costco = item.costco_price is not None and not item.is_coverage_gap
    proxy = item.match_type in PROXY_MATCH_TYPES

    if not has_costco:
        line = "Good ad price, but no Costco comparison available."
    elif pct is not None and pct >= 8:
        # Grocery clearly cheaper on a usable match.
        line = f"{store_label} is about {pct:.0f}% cheaper than Costco on this."
    else:
        # Roughly tied or Costco cheaper, variety / smaller-quantity angle.
        line = (
            "Costco is similar or a little cheaper, but "
            f"{store_label} wins if you want variety or smaller quantity."
        )

    # Proxy / comparable matches always carry the directional qualifier.
    if proxy and has_costco:
        line += " This is a directional comparison, not exact."
    if item.availability == "friday_only":
        line += " (Friday-only, not valid all week.)"
    return line


def build_items(week: str, store: str) -> list[ContentItem]:
    seeds = load_seed(week, store)
    mappings = load_costco_mappings()
    split_rows = load_split_rows(store, week)
    warehouse_slug, filename_slug, warehouse_label = STORE_WAREHOUSE[store]
    store_label = STORE_LABEL[store]

    items: list[ContentItem] = []
    for seed in seeds:
        cid = seed["content_item_id"]
        split = find_split_row(seed["match_query"], split_rows, store)
        raw_offer_text = (split or {}).get("raw_offer_text")
        source_page = None
        if split and (split.get("page_number") or "").strip().isdigit():
            source_page = int(split["page_number"])
        source_pdf = (split or {}).get("source_file") or SOURCE_PDF.get(store)
        package_text = (split or {}).get("package_text")
        availability = (
            seed.get("availability_override")
            or (split or {}).get("availability_type_guess")
            or "full_week"
        )

        mapping = mappings.get((cid, warehouse_slug), {})
        costco_item_number = (mapping.get("costco_item_number") or "").strip() or None
        is_coverage_gap = _truthy(mapping.get("is_coverage_gap"))
        match_type = mapping.get("match_type") or "proxy / manual-review"
        costco_qty = _to_float(mapping.get("costco_qty"))

        costco_price = costco_sign = costco_src = costco_date = None
        if costco_item_number:
            costco_price, costco_sign, costco_src, costco_date = costco_price_for_item(
                filename_slug, costco_item_number
            )
        costco_unit_price = (
            round(costco_price / costco_qty, 4)
            if (costco_price is not None and costco_qty)
            else None
        )
        grocery_unit_price = _to_float(seed.get("grocery_unit_price"))
        pct = _pct(costco_unit_price, grocery_unit_price)

        item = ContentItem(
            content_item_id=cid,
            display_item=seed["display_item"],
            category=seed["category"],
            raw_offer_text=raw_offer_text,
            source_pdf=source_pdf,
            source_page=source_page,
            ad_price_effective=_to_float(seed.get("ad_price_effective")),
            ad_unit_label=seed.get("ad_unit_label") or "",
            package_text=package_text,
            availability=availability,
            grocery_unit_price=grocery_unit_price,
            compare_basis=seed.get("compare_basis") or "unit",
            costco_item_number=costco_item_number,
            costco_item_sign=costco_sign,
            costco_warehouse_label=warehouse_label,
            costco_price=costco_price,
            costco_qty=costco_qty,
            costco_unit_price=costco_unit_price,
            match_type=match_type,
            pct_diff_vs_costco=pct,
            is_coverage_gap=is_coverage_gap,
            graph_update=_truthy(seed.get("graph_update")),
            content_score=0,
            needs_manual_verification=_truthy(seed.get("needs_manual_verification")),
            primary_section=int(seed.get("primary_section") or 6),
            prev_report_status=seed.get("prev_report_status") or "",
            why_missed=seed.get("why_missed") or "",
            notes=seed.get("notes") or "",
            costco_source_file=costco_src,
            costco_date=costco_date,
        )

        # Content score, never requires canonical/graph match.
        costco_pct_for_score = None
        if pct is not None and pct > 0 and not is_coverage_gap:
            costco_pct_for_score = pct
        score = score_content_deal(
            ContentScoreInput(
                category=item.category,
                recognizable_brand=_truthy(seed.get("recognizable_brand")),
                costco_percent_cheaper=costco_pct_for_score,
                costco_match_type=match_type,
                near_costco_with_smaller_qty=_truthy(seed.get("near_costco_variety")),
                absolute_price_strength=seed.get("absolute_price_strength") or "moderate",
                is_friday_only=(availability == "friday_only"),
                is_seasonal_produce=_truthy(seed.get("seasonal")),
                tiktok_hook=seed.get("tiktok_hook") or "moderate",
            )
        )
        item.content_score = score.content_score
        item.content_score_components = score.components
        item.content_score_rationale = score.rationale

        item.safe_for_script = _safe_for_script(item, seed)
        item.can_say_cheaper_than_costco = _can_say_cheaper(item)
        item.script_one_liner = _one_liner(item, store_label)
        items.append(item)

    items.sort(key=lambda i: i.content_score, reverse=True)
    return items


# ------------------------------------------------------- costco coverage audit

# Per the task: audit these specific items against the store's Costco warehouse.
# ``costco_item_number`` is looked up live from the latest consolidated CSV;
# ``None`` means the item is a genuine coverage gap (no matching SKU crawled).
COVERAGE_SPEC = {
    ("2026-07-08", "safeway"): [
        {"item": "raw shrimp", "costco_item_number": None, "unit": "lb",
         "proposed_target": None,
         "notes": "No raw frozen shrimp SKU in SF crawl. Prepared only (Kirkland Garlic Butter Shrimp 2 lb $15.99, Shrimp Cocktail $10.99/lb). Coverage gap for an exact raw-shrimp comparison."},
        {"item": "bell peppers", "costco_item_number": None, "unit": "each",
         "proposed_target": None,
         "notes": "No fresh bell peppers in SF crawl. Coverage gap (Costco 6-ct exists in stores ~$1/ea but not crawled)."},
        {"item": "drumsticks (Nestle ice cream)", "costco_item_number": None, "unit": "cone",
         "proposed_target": None,
         "notes": "No Nestle Drumstick ice cream in SF crawl; only FRESH ORGANIC CHICKEN DRUMSTICK #22501 $1.99/lb (different product). Coverage gap."},
        {"item": "Doritos", "costco_item_number": "933402", "unit": "30 oz bag",
         "proposed_target": "already mapped (canonical doritos_nacho_cheese, config/costco_item_mappings.csv)",
         "notes": "DORITOS NACHO CHEESE 30 OZ, already mapped for the canonical tracker."},
        {"item": "avocados", "costco_item_number": "647465", "unit": "6 count",
         "proposed_target": "already mapped (canonical avocados)",
         "notes": "AVOCADOS HASS VARIETY 6 COUNT, already mapped."},
        {"item": "blackberries", "costco_item_number": "791185", "unit": "12 oz (organic)",
         "proposed_target": "config/content_costco_mappings.csv (berry_mix_6oz)",
         "notes": "ORGANIC BLACKBERRIES 12 OZ, exists; add as content-mode comparable (organic vs conventional caveat)."},
        {"item": "raspberries", "costco_item_number": "56366", "unit": "12 oz",
         "proposed_target": "config/content_costco_mappings.csv (new raspberries row)",
         "notes": "RASPBERRIES 12 OZ, exists; conventional, good same-product comparable."},
        {"item": "blueberries", "costco_item_number": "57554", "unit": "18 oz",
         "proposed_target": "config/content_costco_mappings.csv (new blueberries row)",
         "notes": "BLUEBERRIES 18 OZ, exists; same-product comparable."},
        {"item": "Chobani", "costco_item_number": "1005641", "unit": "20 ct 5.3 oz",
         "proposed_target": "config/content_costco_mappings.csv (chobani_yogurt)",
         "notes": "CHOBANI GREEK YOGURT VARIETY 20 COUNT 5.3 OZ, exists but was unmapped; matches the Safeway single-serve 3/$4 cups (Costco is cheaper per cup). Protein 16-ct #1920008 relates to the Vons 4-ct protein deal, not Safeway."},
        {"item": "beef chuck short ribs", "costco_item_number": "34044", "unit": "per lb (Choice boneless)",
         "proposed_target": "config/content_costco_mappings.csv (beef_chuck_short_ribs)",
         "notes": "CHOICE BEEF CHUCK BONELESS SHORT RIBS $12.29/lb, exists; Prime bone-in #12329 $7.99/lb and #12239 $10.99/lb also exist. Add as content comparable (grade/bone caveat)."},
        {"item": "pork shoulder ribs", "costco_item_number": "33997", "unit": "per lb",
         "proposed_target": "config/content_costco_mappings.csv (pork_shoulder_ribs)",
         "notes": "PORK SHOULDER COUNTRY RIBS BONELESS $3.79/lb, exists; near-exact same product. Add as content comparable."},
        {"item": "Sargento / string cheese", "costco_item_number": "1352319", "unit": "60 ct 1 oz",
         "proposed_target": "config/content_costco_mappings.csv (sargento_cheese, category comparable)",
         "notes": "GALBANI WHOLE MILK STRING CHEESE 60 COUNT $11.49, bulk store-brand; no Sargento SKU. Bulk is cheaper per stick, so this is NOT a Costco beat."},
        {"item": "Oreo regular packs", "costco_item_number": None, "unit": "n/a",
         "proposed_target": None,
         "notes": "No regular Oreo SKU in SF crawl (only mini/assorted cookies). Coverage gap; Costco Oreo (~$3.79) known in stores but not crawled."},
        {"item": "Oreo BTS / single-serve / snack packs", "costco_item_number": None, "unit": "n/a",
         "proposed_target": None,
         "notes": "No Oreo single-serve/snack multipack SKU in SF crawl. Coverage gap."},
    ]
}


def build_coverage_audit(week: str, store: str) -> list[dict]:
    warehouse_slug, filename_slug, warehouse_label = STORE_WAREHOUSE[store]
    spec = COVERAGE_SPEC.get((week, store), [])
    out: list[dict] = []
    for entry in spec:
        num = entry.get("costco_item_number")
        price = sign = None
        if num:
            price, sign, _src, _date = costco_price_for_item(filename_slug, num)
        exists = num is not None and price is not None
        proposed = None
        if exists and entry.get("proposed_target"):
            proposed = {
                "costco_item_number": num,
                "costco_item_sign": sign,
                "costco_price": price,
                "costco_unit": entry.get("unit"),
                "warehouse": warehouse_label,
                "goes_to": entry["proposed_target"],
            }
        out.append(
            {
                "item": entry["item"],
                "costco_sf_data_exists": bool(exists),
                "proposed_mapping": proposed,
                "is_coverage_gap": not exists,
                "notes": entry["notes"],
            }
        )
    return out


# ------------------------------------------------------------------ rendering

WHY_DIFFERS = (
    "The previous `fresh_costco_deal_report` was optimized for canonical "
    "tracker-graph-safe matches: an item only ranked well if it had a canonical "
    "family, an exact/usable baseline, and a same-product Costco match that was "
    "safe to write to a price graph. That is the right bar for the tracker "
    "graphs (it is what keeps smoked salmon from overwriting the fresh-salmon "
    "chart), but it is the wrong bar for content. As a result the graph-safe "
    "report omitted or buried items that are excellent *content* deals but are "
    "ad-deal-only (raw shrimp, bell peppers, Nestle Drumstick, beef chuck short "
    "ribs, Sargento cheese), have no Costco mapping, rely on a proxy/comparable "
    "match, or are Friday-only. This content-first view keeps the same-strict "
    "'beats Costco' guardrails but scores items on shopper interest, absolute "
    "price, category, seasonality, and TikTok hook, so a $5 Friday shrimp or a "
    "$0.99 avocado surfaces even when the graph pipeline would never chart it. "
    "Canonical eligibility is untouched; nothing here updates any tracker graph."
)


def _md_escape(text: str | None) -> str:
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def _fmt_price(value: float | None) -> str:
    return f"${value:.2f}" if value is not None else "unknown"


def _fmt_unit(value: float | None, basis: str) -> str:
    return f"${value:.3f}/{basis}" if value is not None else "unknown"


def _fmt_pct(pct: float | None) -> str:
    if pct is None:
        return "unknown"
    if pct >= 0:
        return f"+{pct:.0f}% (grocery cheaper)"
    return f"{pct:.0f}% (Costco cheaper)"


def build_gap_analysis_md(week: str, store: str, items: list[ContentItem], coverage: list[dict]) -> str:
    store_label = STORE_LABEL[store]
    _, _, warehouse_label = STORE_WAREHOUSE[store]
    now = datetime.now(timezone.utc).isoformat()
    L: list[str] = []
    L.append(f"# Content gap analysis: {store_label} {week}")
    L.append("")
    L.append(f"_Generated {now} · CONTENT ANALYSIS ONLY (no website UI changed, no tracker graph updated)._")
    L.append("")
    L.append("## Why the manual shortlist differs from the previous report.")
    L.append("")
    L.append(WHY_DIFFERS)
    L.append("")
    L.append("## Missing/downranked item table")
    L.append("")
    L.append(f"All Costco comparisons use **{warehouse_label}** (Safeway → San Francisco; Vons → Tustin).")
    L.append("")
    L.append("### Table A, shortlist item, ad provenance, availability")
    L.append("")
    L.append("| Item from shortlist | Raw weekly ad offer text | Source PDF & page | Parsed ad price | Parsed package size / unit | Full-week or Friday-only |")
    L.append("|---|---|---|---|---|---|")
    for it in items:
        page = f"p{it.source_page}" if it.source_page else "unknown"
        pkg = it.package_text or it.ad_unit_label or "unknown"
        adp = (
            f"${it.ad_price_effective:.2f} ({it.ad_unit_label})"
            if it.ad_price_effective is not None
            else "unknown"
        )
        L.append(
            f"| {_md_escape(it.display_item)} | {_md_escape(it.raw_offer_text) or 'unknown'} | "
            f"{_md_escape(it.source_pdf)} {page} | {adp} | {_md_escape(pkg)} | {_availability_label(it.availability)} |"
        )
    L.append("")
    L.append("### Table B: Costco comparison, match quality, verdict")
    L.append("")
    L.append("| Item from shortlist | Costco matched item | Costco warehouse | Costco price | Costco size / unit | Grocery unit price | Costco unit price | % diff | Match type | Updates canonical graph | Safe for content script | Why previously missed/downranked |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for it in items:
        costco_item = it.costco_item_sign or ("unknown (coverage gap)" if it.is_coverage_gap else "unknown")
        costco_size = (
            f"{it.costco_qty:g} {it.compare_basis}" if it.costco_qty else (it.costco_item_sign and "see item" or "unknown")
        )
        L.append(
            f"| {_md_escape(it.display_item)} | {_md_escape(costco_item)} | {it.costco_warehouse_label} | "
            f"{_fmt_price(it.costco_price)} | {_md_escape(costco_size)} | "
            f"{_fmt_unit(it.grocery_unit_price, it.compare_basis)} | {_fmt_unit(it.costco_unit_price, it.compare_basis)} | "
            f"{_fmt_pct(it.pct_diff_vs_costco)} | {it.match_type} | {'yes' if it.graph_update else 'no'} | "
            f"{it.safe_for_script} | {_md_escape(it.why_missed)} |"
        )
    L.append("")
    L.append("## Costco mapping coverage gaps")
    L.append("")
    L.append("| Item | Costco SF data exists? | Proposed mapping | Coverage gap? | Notes |")
    L.append("|---|---|---|---|---|")
    for c in coverage:
        if c["proposed_mapping"]:
            pm = c["proposed_mapping"]
            proposed = (
                f"#{pm['costco_item_number']} {pm['costco_item_sign']} "
                f"{_fmt_price(pm['costco_price'])} / {pm['costco_unit']} → {pm['goes_to']}"
            )
        else:
            proposed = "n/a (none)"
        L.append(
            f"| {_md_escape(c['item'])} | {'yes' if c['costco_sf_data_exists'] else 'no'} | "
            f"{_md_escape(proposed)} | {'yes' if c['is_coverage_gap'] else 'no'} | {_md_escape(c['notes'])} |"
        )
    L.append("")
    return "\n".join(L)


def _do_not_say(items: list[ContentItem]) -> list[str]:
    claims = [
        "Do not present any Friday-only deal (raw shrimp $5/lb, bell peppers 5/$5, "
        "Nestle Drumstick 8-ct $5, Doritos 2/$5, sweet corn 10/$5) as an all-week price.",
        "Do not call the berry deal an exact Costco match: Costco blackberries are "
        "organic 12 oz vs the conventional 6 oz ad pack; keep it directional.",
        "Do not say Sargento string cheese 'beats Costco': Costco's Galbani 60-ct "
        "bulk is cheaper per stick; it is a strong absolute deal / no-bulk-lock-in only.",
        "Do not claim a Costco price for raw shrimp, Nestle Drumstick, sweet corn, bell "
        "peppers, or Oreo, those SKUs are not in this SF crawl (coverage gaps).",
        "Do not call the Chobani single-serve 3/$4 cheaper than Costco: Costco's 20-ct "
        "variety multipack is cheaper per cup; only the 20g protein 4-ct beats Costco.",
        "Do not reuse the graph-safe 'do not update tracker' guardrails as content bans: "
        "content mode never updates a graph, so a proxy is fine to *mention* (labeled) even "
        "though it must never write to weeklyAdPrices.generated.ts.",
    ]
    return claims


def build_script_shortlist_md(week: str, store: str, items: list[ContentItem]) -> str:
    store_label = STORE_LABEL[store]
    _, _, warehouse_label = STORE_WAREHOUSE[store]
    now = datetime.now(timezone.utc).isoformat()
    by_section: dict[int, list[ContentItem]] = {n: [] for n in SECTION_TITLES}
    for it in items:
        by_section[it.primary_section].append(it)
    friday = [it for it in items if it.availability == "friday_only"]
    manual = [it for it in items if it.needs_manual_verification]

    L: list[str] = []
    L.append(f"# Content script shortlist: {store_label} {week}")
    L.append("")
    L.append(f"_Generated {now} · content-first ranking (compared only to {warehouse_label})._")
    L.append("")
    L.append("Each item is labeled: exact vs proxy match, Costco confidence, source page, raw ad text, "
             "whether it is safe to say 'cheaper than Costco', and whether it is only a smaller-buy/variety option.")
    L.append("")

    def emit(section: int, entries: list[ContentItem]) -> None:
        L.append(f"## {section}. {SECTION_TITLES[section]}")
        L.append("")
        if not entries:
            L.append("- (none this week)")
            L.append("")
            return
        for it in sorted(entries, key=lambda i: i.content_score, reverse=True):
            page = f"p{it.source_page}" if it.source_page else "page unknown"
            match_label = "exact" if it.match_type in USABLE_MATCH_TYPES else "proxy/comparable"
            cheaper = "yes" if it.can_say_cheaper_than_costco else "no"
            conf = "n/a (coverage gap)" if it.is_coverage_gap else it.match_type
            L.append(f"- **{_md_escape(it.display_item)}**, content_score {it.content_score}")
            L.append(f"    - _{_availability_label(it.availability)} · {match_label} match · "
                     f"Costco confidence: {conf} · safe: {it.safe_for_script}_")
            L.append(f"    - Script line: \"{it.script_one_liner}\"")
            if it.can_say_cheaper_than_costco:
                cheaper_note = ""
            elif (it.match_type in PROXY_MATCH_TYPES and not it.is_coverage_gap
                  and it.pct_diff_vs_costco is not None and it.pct_diff_vs_costco >= 8):
                cheaper_note = ", directional only (say 'roughly cheaper, not exact')"
            else:
                cheaper_note = ", use smaller-buy / variety framing only"
            L.append(f"    - Safe to say 'cheaper than Costco': {cheaper}" + cheaper_note)
            L.append(f"    - Source: `{_md_escape(it.source_pdf)}` {page} · raw: \"{_md_escape(it.raw_offer_text) or 'unknown'}\"")
            L.append("")

    do_not_use = [it for it in items if it.primary_section == 6]

    for n in (1, 2, 3):
        emit(n, by_section[n])
    emit(4, friday)
    L.append(f"## 5. {SECTION_TITLES[5]}")
    L.append("")
    if manual:
        for it in sorted(manual, key=lambda i: i.content_score, reverse=True):
            L.append(f"- **{_md_escape(it.display_item)}**: {_md_escape(it.notes)}")
    else:
        L.append("- (none this week)")
    L.append("")
    L.append(f"## 6. {SECTION_TITLES[6]}")
    L.append("")
    if do_not_use:
        for it in sorted(do_not_use, key=lambda i: i.content_score, reverse=True):
            L.append(f"- **{_md_escape(it.display_item)}**: {_md_escape(it.notes)}")
    else:
        L.append("- (none this week, every shortlist item is usable with correct framing; "
                 "see the Do-not-say claims below for the wording guardrails.)")
    L.append("")
    L.append("## Do-not-say claims (misleading, do NOT say on camera)")
    L.append("")
    for claim in _do_not_say(items):
        L.append(f"- {claim}")
    L.append("")
    return "\n".join(L)


def _item_to_json(it: ContentItem) -> dict:
    page = f"p{it.source_page}" if it.source_page else "unknown"
    return {
        "item_from_shortlist": it.display_item,
        "raw_weekly_ad_offer_text": it.raw_offer_text,
        "source_pdf_and_page": f"{it.source_pdf} {page}",
        "parsed_ad_price": it.ad_price_effective,
        "parsed_ad_unit_label": it.ad_unit_label,
        "parsed_package_size_unit": it.package_text or it.ad_unit_label,
        "full_week_or_friday_only": _availability_label(it.availability),
        "costco_matched_item": it.costco_item_sign,
        "costco_warehouse_used": it.costco_warehouse_label,
        "costco_price": it.costco_price,
        "costco_package_size_unit": (f"{it.costco_qty:g} {it.compare_basis}" if it.costco_qty else it.costco_item_sign),
        "grocery_unit_price": it.grocery_unit_price,
        "costco_unit_price": it.costco_unit_price,
        "grocery_vs_costco_percent_difference": it.pct_diff_vs_costco,
        "match_type": it.match_type,
        "updates_canonical_tracker_graph": "yes" if it.graph_update else "no",
        "safe_for_content_script": it.safe_for_script,
        "why_previously_missed_or_downranked": it.why_missed,
        "content_item_id": it.content_item_id,
        "category": it.category,
        "content_score": it.content_score,
        "content_score_components": it.content_score_components,
        "content_score_rationale": it.content_score_rationale,
        "can_say_cheaper_than_costco": it.can_say_cheaper_than_costco,
        "script_one_liner": it.script_one_liner,
        "needs_manual_verification": it.needs_manual_verification,
        "primary_section": it.primary_section,
        "prev_report_status": it.prev_report_status,
        "is_coverage_gap": it.is_coverage_gap,
        "costco_source_file": it.costco_source_file,
        "costco_date": it.costco_date,
        "notes": it.notes,
    }


def write_outputs(week: str, store: str, output_dir: Path) -> dict:
    items = build_items(week, store)
    coverage = build_coverage_audit(week, store)
    _, _, warehouse_label = STORE_WAREHOUSE[store]
    now = datetime.now(timezone.utc).isoformat()

    output_dir.mkdir(parents=True, exist_ok=True)

    warehouse_rules = {
        "safeway": "Costco San Francisco",
        "vons": "Costco Tustin",
        "this_week": f"{STORE_LABEL[store]} → {warehouse_label}",
        "seattle": "imported but not wired; labeled fallback only",
    }

    gap_json = {
        "week_start": week,
        "store": store,
        "generated_at": now,
        "mode": "content_first_analysis_only",
        "why_differs": WHY_DIFFERS,
        "warehouse_rules": warehouse_rules,
        "items": [_item_to_json(it) for it in items],
        "costco_mapping_coverage": coverage,
    }
    (output_dir / "content_gap_analysis.json").write_text(
        json.dumps(gap_json, indent=2), encoding="utf-8"
    )
    (output_dir / "content_gap_analysis.md").write_text(
        build_gap_analysis_md(week, store, items, coverage), encoding="utf-8"
    )

    by_section: dict[str, list[dict]] = {SECTION_TITLES[n]: [] for n in SECTION_TITLES}
    for it in items:
        by_section[SECTION_TITLES[it.primary_section]].append(_item_to_json(it))
    friday = [_item_to_json(it) for it in items if it.availability == "friday_only"]
    manual = [_item_to_json(it) for it in items if it.needs_manual_verification]

    shortlist_json = {
        "week_start": week,
        "store": store,
        "generated_at": now,
        "mode": "content_first_analysis_only",
        "warehouse_rules": warehouse_rules,
        "sections": {
            "1_lead_worthy_costco_beaters": by_section[SECTION_TITLES[1]],
            "2_costco_close_variety_smaller_qty": by_section[SECTION_TITLES[2]],
            "3_high_interest_without_costco": by_section[SECTION_TITLES[3]],
            "4_friday_only": friday,
            "5_manual_verification_required": manual,
            "6_do_not_use": by_section[SECTION_TITLES[6]],
        },
        "do_not_say_claims": _do_not_say(items),
        "section_counts": {
            "1_lead_worthy_costco_beaters": len(by_section[SECTION_TITLES[1]]),
            "2_costco_close_variety_smaller_qty": len(by_section[SECTION_TITLES[2]]),
            "3_high_interest_without_costco": len(by_section[SECTION_TITLES[3]]),
            "4_friday_only": len(friday),
            "5_manual_verification_required": len(manual),
            "6_do_not_use": len(by_section[SECTION_TITLES[6]]),
        },
    }
    (output_dir / "content_script_shortlist.json").write_text(
        json.dumps(shortlist_json, indent=2), encoding="utf-8"
    )
    (output_dir / "content_script_shortlist.md").write_text(
        build_script_shortlist_md(week, store, items), encoding="utf-8"
    )

    return {
        "items": len(items),
        "section_counts": shortlist_json["section_counts"],
        "coverage_gaps": sum(1 for c in coverage if c["is_coverage_gap"]),
        "output_dir": str(output_dir),
    }
