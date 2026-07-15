#!/usr/bin/env python3
"""Post-import QA for weekly ad extraction + tracker matches.

Flags the failure class behind Doritos Jul 15 ($2.49 first-pass overwritten by
adjacent seafood $5.99 via crop_override_price):

  1. Crop price overrides (first-pass vs crop-verified) from dedicated raw cards
     and/or consolidated split rows tagged crop_override_price.
  2. Tracked-family week-over-week price worsens (new match much higher than
     the prior matched week).

Usage:
  /usr/bin/python3 scripts/audit_weekly_ad_import.py --week-start 2026-07-15
  /usr/bin/python3 scripts/audit_weekly_ad_import.py --week-start 2026-07-15 --fail-on-findings
  npm run audit:weekly-ad-import -- --week-start 2026-07-15
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from price_tracker.artifacts import parse_ts_export  # noqa: E402

ROOT = SCRIPT_DIR.parent
DEFAULT_DATA_ROOT = Path.home() / "Documents" / "scrolling-the-aisle"
DATA_ROOT = Path(os.environ.get("SCROLLING_THE_AISLE_ROOT", DEFAULT_DATA_ROOT))

SAFEWAY_TS = ROOT / "src" / "data" / "weeklyAdPrices.generated.ts"
VONS_TS = ROOT / "src" / "data" / "vonsWeeklyAdPrices.generated.ts"

# Flag when new matched price is at least this multiple of the prior matched week.
WOW_HIGH_FACTOR = 1.5
# Also flag absolute jumps of this many dollars (catches $2.50 → $3.99 etc.).
WOW_ABS_DELTA = 1.5

FEED_PATHS = {
    "safeway": {
        "label": "Safeway",
        "split": DATA_ROOT / "outputs" / "product_discovery_safeway" / "split_offer_items.csv",
        "discovery_parent": DATA_ROOT / "outputs",
        "slug_prefix": "product_discovery_safeway_",
        "ts": SAFEWAY_TS,
        "weeks_key": "WEEKLY_AD_WEEKS",
        "prices_key": "WEEKLY_AD_PRICES",
        "banner": "Safeway",
    },
    "vons": {
        "label": "Vons",
        "split": DATA_ROOT / "outputs" / "product_discovery_vons" / "split_offer_items.csv",
        "discovery_parent": DATA_ROOT / "outputs",
        "slug_prefix": "product_discovery_vons_",
        "ts": VONS_TS,
        "weeks_key": "VONS_WEEKLY_AD_WEEKS",
        "prices_key": "VONS_WEEKLY_AD_PRICES",
        "banner": "Vons",
    },
}


@dataclass
class CropOverrideFinding:
    feed: str
    source: str
    page: str
    offer_index: str
    product: str
    original_price: str | None
    final_price: str | None
    package: str
    layout: str
    review_reasons: str
    note: str = ""


@dataclass
class WowWorsenFinding:
    feed: str
    family_id: str
    week: str
    prior_week: str
    price: float
    prior_price: float
    ratio: float
    offer_text: str
    confidence: str


@dataclass
class AuditReport:
    week_start: str
    crop_overrides: list[CropOverrideFinding] = field(default_factory=list)
    wow_worsens: list[WowWorsenFinding] = field(default_factory=list)

    @property
    def finding_count(self) -> int:
        return len(self.crop_overrides) + len(self.wow_worsens)


def _parse_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _short(text: str | None, limit: int = 90) -> str:
    s = " ".join(str(text or "").split())
    return s if len(s) <= limit else s[: limit - 1] + "…"


def find_dedicated_raw_cards(feed_key: str, week_start: str) -> Path | None:
    """Locate the per-flyer raw_offer_cards.csv for this week when present."""
    cfg = FEED_PATHS[feed_key]
    parent: Path = cfg["discovery_parent"]
    slug_prefix: str = cfg["slug_prefix"]
    # Prefer folders that include week tokens from the start date (e.g. 7-15).
    month = str(int(week_start[5:7]))
    day = str(int(week_start[8:10]))
    token = f"{month}-{day}"
    candidates: list[Path] = []
    for path in parent.glob(f"{slug_prefix}*/raw_offer_cards.csv"):
        folder = path.parent.name
        if token in folder or week_start in folder:
            candidates.append(path)
    if not candidates:
        # Fall back: any dedicated folder whose split/raw rows include week_start.
        for path in parent.glob(f"{slug_prefix}*/raw_offer_cards.csv"):
            try:
                with path.open(newline="", encoding="utf-8") as handle:
                    for row in csv.DictReader(handle):
                        if row.get("week_start") == week_start:
                            candidates.append(path)
                            break
            except OSError:
                continue
    if not candidates:
        return None
    # Newest mtime wins when multiple match.
    return max(candidates, key=lambda p: p.stat().st_mtime)


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def crop_overrides_from_raw(
    feed_key: str,
    week_start: str,
    rows: list[dict[str, str]],
    source: str,
) -> list[CropOverrideFinding]:
    findings: list[CropOverrideFinding] = []
    for row in rows:
        if row.get("week_start") and row.get("week_start") != week_start:
            continue
        reasons = row.get("review_reasons") or ""
        original = row.get("original_advertised_price")
        verified = row.get("verified_advertised_price")
        final = row.get("advertised_price")
        has_override_tag = "crop_override_price" in reasons or (
            "crop_verification_override" in reasons and "first_pass_crop_disagreement" in reasons
        )
        o_price = _parse_float(original)
        v_price = _parse_float(verified)
        price_disagreed = (
            o_price is not None and v_price is not None and abs(o_price - v_price) >= 0.01
        )
        if not (has_override_tag or price_disagreed):
            continue
        note = ""
        if price_disagreed and o_price is not None and v_price is not None:
            if v_price > o_price * WOW_HIGH_FACTOR or (v_price - o_price) >= WOW_ABS_DELTA:
                note = "crop raised price vs first-pass — check adjacent-tile bleed"
            elif o_price > v_price * WOW_HIGH_FACTOR or (o_price - v_price) >= WOW_ABS_DELTA:
                note = "crop lowered price vs first-pass — confirm which is correct"
        # Prefer showing the crop disagreement pair (original → verified).
        display_final = verified if price_disagreed else (final or verified)
        findings.append(
            CropOverrideFinding(
                feed=FEED_PATHS[feed_key]["label"],
                source=source,
                page=str(row.get("page_number") or ""),
                offer_index=str(row.get("offer_index_on_page") or ""),
                product=_short(
                    row.get("raw_product_text")
                    or row.get("split_product_text")
                    or row.get("verified_raw_product_text")
                ),
                original_price=original or None,
                final_price=display_final or final or None,
                package=_short(row.get("package_text") or row.get("verified_package_text") or "", 40),
                layout=str(row.get("layout_type") or ""),
                review_reasons=_short(reasons, 120),
                note=note,
            )
        )
    return findings


def crop_overrides_from_split(
    feed_key: str,
    week_start: str,
    rows: list[dict[str, str]],
) -> list[CropOverrideFinding]:
    findings: list[CropOverrideFinding] = []
    for row in rows:
        if row.get("week_start") != week_start:
            continue
        reasons = row.get("review_reasons") or ""
        if "crop_override_price" not in reasons and "crop_verification_override" not in reasons:
            continue
        findings.append(
            CropOverrideFinding(
                feed=FEED_PATHS[feed_key]["label"],
                source="split_offer_items.csv",
                page=str(row.get("page_number") or ""),
                offer_index=str(row.get("offer_index_on_page") or ""),
                product=_short(row.get("split_product_text") or row.get("raw_product_text")),
                original_price=row.get("original_advertised_price") or None,
                final_price=row.get("advertised_price") or None,
                package=_short(row.get("package_text") or "", 40),
                layout=str(row.get("layout_type") or ""),
                review_reasons=_short(reasons, 120),
                note="tagged crop override in consolidated split",
            )
        )
    return findings


def prior_matched_week(
    weeks: dict[str, dict[str, Any]],
    week_start: str,
) -> tuple[str, float] | None:
    dated = sorted(
        (
            (start, entry)
            for start, entry in weeks.items()
            if start < week_start and _parse_float(entry.get("price")) is not None
        ),
        key=lambda item: item[0],
    )
    if not dated:
        return None
    start, entry = dated[-1]
    price = _parse_float(entry.get("price"))
    if price is None:
        return None
    return start, price


def wow_worsens_for_feed(
    feed_key: str,
    week_start: str,
    *,
    high_factor: float,
    abs_delta: float,
) -> list[WowWorsenFinding]:
    cfg = FEED_PATHS[feed_key]
    parsed = parse_ts_export(cfg["ts"], cfg["weeks_key"], cfg["prices_key"])
    if not parsed:
        return []
    _, prices = parsed
    findings: list[WowWorsenFinding] = []
    for family_id, by_week in prices.items():
        entry = by_week.get(week_start)
        if not entry:
            continue
        price = _parse_float(entry.get("price"))
        if price is None:
            continue
        prior = prior_matched_week(by_week, week_start)
        if prior is None:
            continue
        prior_week, prior_price = prior
        if prior_price <= 0:
            continue
        ratio = price / prior_price
        if ratio < high_factor and (price - prior_price) < abs_delta:
            continue
        findings.append(
            WowWorsenFinding(
                feed=cfg["label"],
                family_id=family_id,
                week=week_start,
                prior_week=prior_week,
                price=price,
                prior_price=prior_price,
                ratio=round(ratio, 2),
                offer_text=_short(str(entry.get("offerText") or "")),
                confidence=str(entry.get("confidence") or ""),
            )
        )
    findings.sort(key=lambda f: (-f.ratio, f.family_id))
    return findings


def build_report(
    week_start: str,
    *,
    feeds: list[str] | None = None,
    high_factor: float = WOW_HIGH_FACTOR,
    abs_delta: float = WOW_ABS_DELTA,
) -> AuditReport:
    report = AuditReport(week_start=week_start)
    selected = feeds or list(FEED_PATHS.keys())
    for feed_key in selected:
        cfg = FEED_PATHS[feed_key]
        raw_path = find_dedicated_raw_cards(feed_key, week_start)
        if raw_path:
            try:
                source = str(raw_path.relative_to(DATA_ROOT))
            except ValueError:
                source = str(raw_path)
            report.crop_overrides.extend(
                crop_overrides_from_raw(
                    feed_key,
                    week_start,
                    load_csv_rows(raw_path),
                    source=source,
                )
            )
        split_rows = load_csv_rows(cfg["split"])
        # Avoid duplicating the same page/index when raw already covered it.
        seen = {
            (f.feed, f.page, f.offer_index, f.final_price)
            for f in report.crop_overrides
            if f.feed == cfg["label"]
        }
        for finding in crop_overrides_from_split(feed_key, week_start, split_rows):
            key = (finding.feed, finding.page, finding.offer_index, finding.final_price)
            if key in seen:
                continue
            report.crop_overrides.append(finding)
        report.wow_worsens.extend(
            wow_worsens_for_feed(
                feed_key,
                week_start,
                high_factor=high_factor,
                abs_delta=abs_delta,
            )
        )
    # Prefer bleed-risk overrides first.
    report.crop_overrides.sort(
        key=lambda f: (
            0 if "bleed" in f.note else 1,
            f.feed,
            f.page,
            f.offer_index,
        )
    )
    return report


def render_markdown(report: AuditReport) -> str:
    lines = [
        f"# Weekly ad import QA: {report.week_start}",
        "",
        "Auto checklist for crop-price overrides and tracked week-over-week worsens.",
        f"**Findings:** {len(report.crop_overrides)} crop overrides, "
        f"{len(report.wow_worsens)} WoW worsens.",
        "",
        "## Crop price overrides",
        "",
    ]
    if not report.crop_overrides:
        lines.append("_None found._")
    else:
        lines.append(
            "| Feed | Pg | Idx | Product | First-pass → Final | Layout | Note |"
        )
        lines.append("|---|---|---|---|---|---|---|")
        for f in report.crop_overrides:
            left = f.original_price or "?"
            right = f.final_price or "?"
            lines.append(
                f"| {f.feed} | {f.page} | {f.offer_index} | {f.product} | "
                f"${left} → ${right} | {f.layout} | {f.note or f.review_reasons} |"
            )
    lines.extend(["", "## Tracked week-over-week worsens", ""])
    if not report.wow_worsens:
        lines.append("_None found._")
    else:
        lines.append(
            "| Feed | Family | Prior → New | Ratio | Offer |"
        )
        lines.append("|---|---|---|---|---|")
        for f in report.wow_worsens:
            lines.append(
                f"| {f.feed} | `{f.family_id}` | "
                f"${f.prior_price:.2f} ({f.prior_week}) → ${f.price:.2f} | "
                f"{f.ratio:.2f}× | {f.offer_text} |"
            )
    lines.extend(
        [
            "",
            "## What to do",
            "",
            "1. Open the flyer page for each crop override — especially "
            "`coupon_grid_offer` rows where first-pass and final prices disagree.",
            "2. For WoW worsens, confirm the new ad size/price is real (not bleed "
            "from a neighbor tile, party-size, or multipack).",
            "3. Correct sibling `split_offer_items.csv`, then rematch:",
            "   `/usr/bin/python3 scripts/generate_weekly_ad_prices.py "
            "--product-ids <id> --feed safeway`",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(
    report: AuditReport,
    *,
    high_factor: float = WOW_HIGH_FACTOR,
    abs_delta: float = WOW_ABS_DELTA,
) -> tuple[Path, Path]:
    out_dir = ROOT / "output" / "weekly_deals" / report.week_start
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "import_qa_audit.md"
    json_path = out_dir / "import_qa_audit.json"
    md_path.write_text(render_markdown(report), encoding="utf-8")
    payload = {
        "week_start": report.week_start,
        "crop_overrides": [asdict(x) for x in report.crop_overrides],
        "wow_worsens": [asdict(x) for x in report.wow_worsens],
        "finding_count": report.finding_count,
        "thresholds": {
            "wow_high_factor": high_factor,
            "wow_abs_delta": abs_delta,
        },
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return md_path, json_path


def print_console(report: AuditReport) -> None:
    print(f"\n=== Weekly ad import QA ({report.week_start}) ===")
    print(
        f"Crop overrides: {len(report.crop_overrides)} | "
        f"WoW worsens: {len(report.wow_worsens)}"
    )
    bleed = [f for f in report.crop_overrides if "bleed" in f.note]
    if bleed:
        print("\nHigh-priority crop raises (possible adjacent-tile bleed):")
        for f in bleed[:15]:
            print(
                f"  [{f.feed} p{f.page}/{f.offer_index}] "
                f"${f.original_price} → ${f.final_price}  {f.product}"
            )
    elif report.crop_overrides:
        print("\nCrop overrides (top):")
        for f in report.crop_overrides[:10]:
            print(
                f"  [{f.feed} p{f.page}/{f.offer_index}] "
                f"${f.original_price or '?'} → ${f.final_price or '?'}  {f.product}"
            )
    if report.wow_worsens:
        print("\nTracked WoW worsens:")
        for f in report.wow_worsens[:15]:
            print(
                f"  [{f.feed}] {f.family_id}: "
                f"${f.prior_price:.2f} → ${f.price:.2f} ({f.ratio:.2f}×)  {f.offer_text}"
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit weekly ad import for crop price overrides and WoW worsens."
    )
    parser.add_argument("--week-start", required=True, help="Ad week start YYYY-MM-DD")
    parser.add_argument(
        "--feed",
        choices=("all", "safeway", "vons"),
        default="all",
        help="Limit to one feed (default: all)",
    )
    parser.add_argument(
        "--wow-factor",
        type=float,
        default=WOW_HIGH_FACTOR,
        help=f"Flag when new price ≥ this × prior matched week (default {WOW_HIGH_FACTOR})",
    )
    parser.add_argument(
        "--wow-abs-delta",
        type=float,
        default=WOW_ABS_DELTA,
        help=f"Also flag absolute $ increase of this amount (default {WOW_ABS_DELTA})",
    )
    parser.add_argument(
        "--fail-on-findings",
        action="store_true",
        help="Exit 1 when any crop override or WoW worsen is found",
    )
    parser.add_argument(
        "--fail-on-bleed-risk",
        action="store_true",
        help="Exit 1 only when crop raised price vs first-pass (bleed-risk class)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    feeds = None if args.feed == "all" else [args.feed]
    report = build_report(
        args.week_start,
        feeds=feeds,
        high_factor=args.wow_factor,
        abs_delta=args.wow_abs_delta,
    )
    md_path, json_path = write_outputs(
        report,
        high_factor=args.wow_factor,
        abs_delta=args.wow_abs_delta,
    )
    print_console(report)
    print(f"\nWrote {md_path}")
    print(f"Wrote {json_path}")

    bleed_count = sum(1 for f in report.crop_overrides if "bleed" in f.note)
    if args.fail_on_bleed_risk and bleed_count:
        raise SystemExit(
            f"Failing: {bleed_count} crop raise(s) vs first-pass (adjacent-tile bleed risk)"
        )
    if args.fail_on_findings and report.finding_count:
        raise SystemExit(f"Failing: {report.finding_count} import QA finding(s)")


if __name__ == "__main__":
    main()
