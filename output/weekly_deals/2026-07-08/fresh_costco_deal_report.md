# Fresh Costco Reanalysis — 2026-07-08 to 2026-07-14

_Generated 2026-07-08T14:58:55.220388+00:00 · ANALYSIS ONLY (no website UI changed)._

> **Source of truth for scripting:** this file (`output/weekly_deals/2026-07-08/fresh_costco_deal_report.md`). Do **not** script from `expanded_shortlist.json` (stale Costco + weak canonical matches).

## 1. Data freshness summary

- **Ad week:** 2026-07-08 → 2026-07-14 — **ACTIVE (calendar-active week; today is 2026-07-08, not a preview)**.
- **Costco cache imported:** 2026-07-08T05:27:34.157688+00:00 from `/Users/evelynchan/Documents/costco-mvp/costco_data` (18,641 observations).
- **Costco San Francisco (for Safeway):** latest crawl **2026-07-07** (`2026-07-07_san-francisco_consolidated.csv`).
- **Costco Tustin (for Vons):** latest crawl **2026-07-07** (`2026-07-07_tustin_consolidated.csv`).
- **Costco Seattle:** latest **2026-07-07** — labeled fallback only (not used; SF and Tustin both present).
- **Replaced or supplemented:** Supplemented: import added the 2026-07-07 crawl on top of all prior dated observations; load_location_catalog picks the newest observation per item by timestamp. No older rows were deleted.
- **Weekly ad sources:** `safeway 7-8 - 7-14.pdf` → `weeklyAdPrices.generated.ts`; `vons 7-8 - 7-14.pdf` → `vonsWeeklyAdPrices.generated.ts` (week `2026-07-08`).
- **Baseline sources:** Safeway `priceTrackerFallback.ts` (SAFEWAY_BASELINES); Vons `vonsBaseline.generated.ts`. Provenance graded in `baseline_audit.json`.
- **Historical ad sources:** `weeklyAdPrices.generated.ts` / `vonsWeeklyAdPrices.generated.ts` (prior weeks) via `weekly_ad_analysis/benchmarks.py`.
- **Audit files used:** `baseline_audit.json`, `canonical_match_audit.json`, `fresh_costco_comparison_audit.json` (this run).

### Costco price changes on tracked items (fresh 07-07 vs prior)

| Item | Warehouse | 07-07 price | Prior crawl (07-05) | Last *different* value | Change |
|---|---|---|---|---|---|
| STRAWBERRIES 2 LBS | san_francisco | $3.99 | 2026-07-05 $3.99 | 2026-06-27 $5.49 | ↓ from 2026-06-27 $5.49 |
| AVOCADOS HASS VARIETY 6 COUNT | san_francisco | $7.99 | 2026-07-05 $7.99 | 2026-06-27 $8.99 | ↓ from 2026-06-27 $8.99 |
| ORGANIC GREEN SEEDLESS GRAPES 3 LBS | san_francisco | $7.99 | 2026-07-05 $7.99 | 2026-06-27 $8.49 | ↓ from 2026-06-27 $8.49 |
| KIRKLAND SIGNATURE CAGE FREE LARGE EGGS 5 DZ | san_francisco | $11.99 | 2026-07-05 $11.99 | — | stable (no change in series) |
| DORITOS NACHO CHEESE 30 OZ | san_francisco | $6.99 | 2026-07-05 $6.99 | — | stable (no change in series) |
| STRAWBERRIES 2 LBS | tustin | $3.99 | 2026-07-05 $3.99 | 2026-06-27 $5.49 | ↓ from 2026-06-27 $5.49 |
| AVOCADOS HASS VARIETY 6 COUNT | tustin | $7.99 | 2026-07-05 $7.99 | 2026-06-27 $8.99 | ↓ from 2026-06-27 $8.99 |
| ORGANIC GREEN SEEDLESS GRAPES 3 LBS | tustin | $7.99 | 2026-07-05 $7.99 | — | stable (no change in series) |
| KIRKLAND SIGNATURE CAGE FREE LARGE EGGS 5 DZ | tustin | $8.59 | 2026-07-05 $8.59 | — | stable (no change in series) |
| DORITOS NACHO CHEESE 30 OZ | tustin | $7.29 | 2026-07-05 $7.29 | — | stable (no change in series) |

_No tracked-item Costco price changed between the two most recent crawls (07-05 → 07-07). Relative to the mid/late-June cache, strawberries, avocados and SF grapes had already stepped down at the 07-02 crawl; 07-07 confirms those lower prices._

## 2. What changed because of fresh Costco prices

Fresh 07-07 Costco prices match the 07-05 crawl, so **no recommendation flips vs the 07-05-based numbers**. Versus the older (mid/late-June) Costco cache, three produce comparisons now use a lower Costco price, which makes Costco *more* competitive:

| Item | Store | Old Costco (late-June) | Fresh Costco (07-07) | Effect on recommendation |
|---|---|---|---|---|
| Strawberries | Vons↔Tustin | $5.49 / 2 lb ($2.75/lb) | $3.99 / 2 lb ($2.00/lb) | Costco win margin grows; Vons $2.50/lb Friday no longer beats Costco |
| Avocados | Safeway↔SF & Vons↔Tustin | $8.99 / 6 ct ($1.50/ea) | $7.99 / 6 ct ($1.33/ea) | Safeway $0.99 still beats; Vons $1.50 now *loses* to Costco $1.33 |
| Grapes | Safeway↔SF | $8.49 / 3 lb ($2.83/lb) | $7.99 / 3 lb ($2.66/lb) | Costco edge widens vs Safeway $2.99/lb |

All other items were already `null`/proxy at Costco and are unaffected by the refresh.

## 2b. PDF-verified corrections (this run — Chips Ahoy / Nabisco audit)

Both PDFs were opened and the embedded flyer images inspected to confirm ground truth.

| Store | Was (vision) | Corrected to | Source | Why |
|---|---|---|---|---|
| Safeway | Nabisco Chips Ahoy! Cookies **7-13 oz** $3.49 | Nabisco Chips Ahoy! Cookies **9.5–13 oz** $3.49 (buy 2; single $3.99) | `safeway 7-8 - 7-14.pdf` p5 | **VALID, kept.** Regular cookie pack; only the size was wrong (7-13 → 9.5-13 oz). |
| Vons | "Oreo or Chips Ahoy! Cookies **10-15.35 oz** $3.99" (regular cookies) | **Nabisco Single Serve Snacks 10 ct** $3.99 digital coupon (Oreo Mini / Mini Chips Ahoy / Nutter Butter Bites) | `vons 7-8 - 7-14.pdf` p1 sidebar | **RELABELED.** Vision misread a single-serve multipack coupon as regular cookies AND fabricated size "10-15.35 oz" (the "10" is *10 ct*). |
| Vons | "Oreo" $3.99 (Oreo family-size) | **Nabisco Single Serve Snacks 10 ct** $3.99 (same coupon tile) | `vons 7-8 - 7-14.pdf` p1 sidebar | **RELABELED.** Same `raw_offer_id b0d4b8ff406a` as the Chips Ahoy row — there is **no** separate Oreo family-size deal in this Vons ad. |

Net effect: the Vons single-serve item is **no longer promoted as regular Chips Ahoy cookies** and drops from Vons "Top script-safe deals" to "Manual verification first" / quick mention only.

## 3. Safeway corrected ranking (vs Costco San Francisco only)

_Safeway: audited baseline provenance + fresh Costco recompute + PDF-verified corrections._

**Top script-safe deals**
- **Acme Smoked Nova Salmon 4 oz** — $4.99 (4 oz), full-week, pack: regular_retail_pack. Hist: Historical low. Baseline: 17% off (usable) [usable-baseline]. Costco: no Costco item mapped. Src: safeway 7-8 - 7-14.pdf p7.
- **Hass Avocado** — $0.99 (see ad), full-week, pack: regular_retail_pack. Hist: Historical low. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: grocery cheaper by 26%/unit — AVOCADOS HASS VARIETY 6 COUNT @ $7.99 ($1.332/unit, 2026-07-07) [same_product, Medium]. Src: safeway 7-8 - 7-14.pdf p1.

**Next usable mentions**
- **O Organics Organic Fresh Boneless Skinless Chicken Breast Value Pack.** — $5.99 (per lb), full-week, pack: regular_retail_pack. Hist: Unknown. Baseline: ~33% off (PROXY — do not headline) [proxy/same_family_proxy]. Costco: no Costco item mapped. Src: safeway 7-8 - 7-14.pdf p3.
- **Land O'Lakes Butter 16-oz. Spread 13 to 15-oz. Selected varieties.** — $3.49 (13 to 15-oz.), full-week, pack: regular_retail_pack. Hist: Typical sale. Baseline: ~42% off (PROXY — do not headline) [proxy/same_family_proxy]. Costco: no Costco item mapped. Src: safeway 7-8 - 7-14.pdf p3.

**Costco still wins, but smaller grocery quantity is useful**
- **Ruffles Potato Chips** — $2.5 (9-13 oz.), Friday-only, pack: regular_retail_pack. Hist: Near historical low. Baseline: ~54% off (PROXY — do not headline) [proxy/same_family_proxy]. Costco: Costco cheaper by 16%/unit — DORITOS NACHO CHEESE 30 OUNCES @ $6.99 ($0.233/unit, 2026-07-07) [weak_proxy, Low]. Src: safeway 7-8 - 7-14.pdf p2.

**Manual verification first**
- **Nabisco Chips Ahoy! Cookies (9.5–13 oz)** **[CORRECTED]** — $3.49 (9.5–13 oz (selected varieties)), full-week, pack: regular_retail_pack. Hist: Unknown. Baseline: ~42% off (PROXY — do not headline) [proxy/same_product_different_size]. Costco: no Costco item mapped. Src: safeway 7-8 - 7-14.pdf p5.

**Do not mention / bad matches**
- **Red Cherries** — $4.99 (per lb), full-week, pack: regular_retail_pack. Hist: Typical sale. Baseline: ~17% off (PROXY — do not headline) [proxy/same_family_proxy]. Costco: NOT COMPARABLE — ORGANIC GREEN SEEDLESS GRAPES 3 LBS @ $7.99 ($2.663/unit, 2026-07-07) [not_comparable, Low]. Src: safeway 7-8 - 7-14.pdf p2.
- **Coca-Cola, Pepsi** — $3.99 (12-pack, 12 fl oz cans or 8-pack, 12 fl oz bottles), full-week, pack: regular_retail_pack. Hist: Typical sale. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: no Costco data (weak_proxy). Src: safeway 7-8 - 7-14.pdf p1.
- **Foster Farms Fresh & Natural Chicken Leg Quarters** — $0.99 (10 lb bag), full-week, pack: regular_retail_pack. Hist: Unknown. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: no Costco item mapped. Src: safeway 7-8 - 7-14.pdf p2.
- **Blade Steaks Pork Spareribs** — $2.99 (per lb), full-week, pack: regular_retail_pack. Hist: Unknown. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: no Costco item mapped. Src: safeway 7-8 - 7-14.pdf p1.
- **Red Seedless Grapes** — $2.99 (per lb), full-week, pack: regular_retail_pack. Hist: Worse than previous. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: Costco cheaper by 12%/unit — ORGANIC GREEN SEEDLESS GRAPES 3 LBS @ $7.99 ($2.663/unit, 2026-07-07) [same_product, Medium]. Src: vons 7-8 - 7-14.pdf p3.
- **Large Mango** — $1.25 (see ad), full-week, pack: regular_retail_pack. Hist: Unknown. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: no Costco item mapped. Src: safeway 7-8 - 7-14.pdf p2.
- **Yoplait Yogurt 4-6 oz** — $0.39 (4-6 oz), full-week, pack: regular_retail_pack. Hist: Unknown. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: no Costco item mapped. Src: safeway 7-8 - 7-14.pdf p1.
- **Blueberries Pint, Raspberries** — $2.99 (Pint, 6 oz), full-week, pack: regular_retail_pack. Hist: Unknown. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: no Costco item mapped. Src: safeway 7-8 - 7-14.pdf p1.
- **Soleil Sparkling Water** — $3.5 (8 pk, 12 fl oz cans), full-week, pack: multipack. Hist: Unknown. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: no Costco item mapped. Src: safeway 7-8 - 7-14.pdf p4.
- **Frito-Lay Variety Pack 18 ct Selected varieties** — $8.99 (18 ct), full-week, pack: multipack. Hist: Unknown. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: no Costco item mapped. Src: safeway 7-8 - 7-14.pdf p7.
- **Sweet Corn** — $0.5 (10 for $5), Friday-only, pack: regular_retail_pack. Hist: Unknown. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: no Costco item mapped. Src: vons 7-8 - 7-14.pdf p3.
- **Chobani Greek Yogurt, Oikos Triple Zero Greek Yogurt, or Danone Light + Fit Greek Yogurt Selected varieties.** — $1.33 (4.5-5.3 oz.), full-week, pack: broad_promo_block. Hist: Unknown. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: no Costco item mapped. Src: safeway 7-8 - 7-14.pdf p3.
- **Doritos Tortilla Chips** — $2.5 (9-13 oz.), Friday-only, pack: regular_retail_pack. Hist: Typical sale. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: Costco cheaper by 16%/unit — DORITOS NACHO CHEESE 30 OUNCES @ $6.99 ($0.233/unit, 2026-07-07) [same_product, High]. Src: safeway 7-8 - 7-14.pdf p2.
- **Kashi Cereal, Kellogg's Cereal or Nutri-Grain Bars Selected varieties.** — $3.99 (7.2-16.3 oz.), full-week, pack: broad_promo_block. Hist: Worse than previous. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: no Costco item mapped. Src: safeway 7-8 - 7-14.pdf p3.

## 4. Vons corrected ranking (vs Costco Tustin only)

_Vons: audited baseline provenance + fresh Costco recompute + PDF-verified corrections._

**Top script-safe deals**
- (none rated strong this week)

**Next usable mentions**
- **Ritz Crackers** — $2.49 (3.5-13.7 oz), full-week, pack: regular_retail_pack. Hist: Historical low. Baseline: ~50% off (PROXY — do not headline) [proxy/same_product_different_size]. Costco: no Costco item mapped. Src: vons 7-8 - 7-14.pdf p2.
- **Wheat Thins** — $2.49 (3.5-13.7 oz), full-week, pack: regular_retail_pack. Hist: Historical low. Baseline: ~29% off (PROXY — do not headline) [proxy/same_product_different_size]. Costco: no Costco item mapped. Src: vons 7-8 - 7-14.pdf p2.
- **Lucerne Large Eggs** — $2.49 (12 ct), full-week, pack: multipack. Hist: Worse than previous. Baseline: ~-25% off (PROXY — do not headline) [proxy/same_family_proxy]. Costco: MANUAL REVIEW (normalization unreliable) — KIRKLAND SIGNATURE CAGE FREE LARGE EGGS USDA GRADE AA 5 DZ @ $8.59 ($8.590/unit, 2026-07-07) [same_product, Low]. Src: vons 7-8 - 7-14.pdf p1.
- **Cherries** — $2.99 (per lb), full-week, pack: regular_retail_pack. Hist: Typical sale. Baseline: ~50% off (PROXY — do not headline) [proxy/same_family_proxy]. Costco: NOT COMPARABLE — ORGANIC GREEN SEEDLESS GRAPES 3 LBS @ $7.99 ($2.663/unit, 2026-07-07) [not_comparable, Low]. Src: vons 7-8 - 7-14.pdf p1.
- **Green Seedless Grapes** — $1.99 (per lb), Friday-only, pack: regular_retail_pack. Hist: Near historical low. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: grocery cheaper by 25%/unit — ORGANIC GREEN SEEDLESS GRAPES 3 LBS @ $7.99 ($2.663/unit, 2026-07-07) [same_product, Medium]. Src: vons 7-8 - 7-14.pdf p3.
- **Signature SELECT Ice Cream 1.5 qt.** — $3.49 (14-16 oz. or 4 ct.), full-week, pack: regular_retail_pack. Hist: Unknown. Baseline: ~61% off (PROXY — do not headline) [proxy/same_family_proxy]. Costco: no Costco item mapped. Src: vons 7-8 - 7-14.pdf p1.
- **Cheez-It Crackers, Keebler Fudge Shoppe Cookies** — $1.67 (6.6 to 13.7 oz), Friday-only, pack: regular_retail_pack. Hist: Unknown. Baseline: ~76% off (PROXY — do not headline) [proxy/same_family_proxy]. Costco: no Costco item mapped. Src: vons 7-8 - 7-14.pdf p3.

**Costco still wins, but smaller grocery quantity is useful**
- (none)

**Manual verification first**
- **Nabisco Single Serve Snacks 10 pack (Oreo Mini / Mini Chips Ahoy / Nutter Butter Bites)** **[CORRECTED]** — $3.99 (10 ct (single-serve multipack)), full-week, pack: single_serve_pack. Hist: Unknown. Baseline: ~20% off (PROXY — do not headline) [proxy/same_product_different_size]. Costco: no Costco item mapped. Src: vons 7-8 - 7-14.pdf p1.
- **Nabisco Single Serve Snacks 10 pack (same coupon — Oreo Mini variety)** **[CORRECTED]** — $3.99 (10 ct (single-serve multipack)), full-week, pack: single_serve_pack. Hist: Unknown. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: no Costco item mapped. Src: vons 7-8 - 7-14.pdf p1.
- **Ben & Jerry’s 14-16 oz.** — $3.49 (14-16 oz. or 4 ct.), full-week, pack: regular_retail_pack. Hist: Unknown. Baseline: ~56% off (PROXY — do not headline) [proxy/invalid_baseline]. Costco: no Costco item mapped. Src: vons 7-8 - 7-14.pdf p1.

**Do not mention / bad matches**
- **Lucerne Butter** — $3.99 (16 oz), full-week, pack: regular_retail_pack. Hist: Worse than previous. Baseline: 0% off (usable) [usable-baseline]. Costco: no Costco item mapped. Src: vons 7-8 - 7-14.pdf p1.
- **Whole Chicken Bone-in, Value pack** — $0.99 (Bone-in, Value pack), full-week, pack: regular_retail_pack. Hist: Unknown. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: no Costco item mapped. Src: vons 7-8 - 7-14.pdf p1.
- **Large Hass Avocados** — $1.5 (see ad), full-week, pack: regular_retail_pack. Hist: Worse than previous. Baseline: ~0% off (PROXY — do not headline) [proxy/same_family_proxy]. Costco: Costco cheaper by 13%/unit — AVOCADOS HASS VARIETY 6 COUNT @ $7.99 ($1.332/unit, 2026-07-07) [same_product, Medium]. Src: vons 7-8 - 7-14.pdf p3.
- **Five Crowns Sweet White Corn** — $0.67 (see ad), full-week, pack: regular_retail_pack. Hist: Unknown. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: no Costco item mapped. Src: vons 7-8 - 7-14.pdf p3.
- **Red Seedless Grapes** — $2.99 (per lb), full-week, pack: regular_retail_pack. Hist: Worse than previous. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: Costco cheaper by 12%/unit — ORGANIC GREEN SEEDLESS GRAPES 3 LBS @ $7.99 ($2.663/unit, 2026-07-07) [same_product, Medium]. Src: vons 7-8 - 7-14.pdf p3.
- **Blueberries** — $0.99 (6 oz), full-week, pack: regular_retail_pack. Hist: Unknown. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: no Costco item mapped. Src: vons 7-8 - 7-14.pdf p1.
- **Kellogg’s Cereal** — $2.58 (10.1-13.7 oz), full-week, pack: regular_retail_pack. Hist: Worse than previous. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: no Costco item mapped. Src: vons 7-8 - 7-14.pdf p1.
- **Coca-Cola 2 liter** — $0.99 (2 liter), full-week, pack: regular_retail_pack. Hist: Unknown. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: no Costco item mapped. Src: vons 7-8 - 7-14.pdf p2.
- **Pepsi 2 liter** — $0.99 (2 liter), full-week, pack: regular_retail_pack. Hist: Unknown. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: no Costco item mapped. Src: vons 7-8 - 7-14.pdf p2.
- **Fresh Strawberries** — $2.5 (12 ct), Friday-only, pack: multipack. Hist: Worse than previous. Baseline: no baseline % claim [proxy/missing_baseline]. Costco: Costco cheaper by 25%/unit — STRAWBERRIES 2 LBS @ $3.99 ($1.995/unit, 2026-07-07) [same_product, Medium]. Src: vons 7-8 - 7-14.pdf p1.

## 5. Script-ready shortlist

_Every item carries source provenance (PDF + page + raw ad text + pack type). Items marked **[CORRECTED]** were re-verified against the PDF this run._

### Safeway (12) — compared only to Costco San Francisco

- **Acme Smoked Nova Salmon 4 oz** — Smoked Nova salmon is $4.99 this week — a real snack-deal, ~17% under its usual $5.99 (NOT the fresh-fillet price).
    - _full-week · not tracked at Costco · exact-match · pack: regular_retail_pack_
    - Source: `safeway 7-8 - 7-14.pdf` p7 · raw: "Acme Smoked Nova Salmon 4 oz 4.99 Member Price" · parsed: Acme Smoked Nova Salmon 4 oz / 4 oz / $4.99
- **Hass Avocado** — Hass Avocado at $0.99 actually undercuts Costco per unit if you only want a small amount.
    - _full-week · beats Costco (per-unit, small-qty; fairness caveat) · PROXY/manual-review; Costco Medium-confidence · pack: regular_retail_pack_
    - Source: `safeway 7-8 - 7-14.pdf` p1 · raw: "Hass Avocado 99¢ EA MEMBER PRICE" · parsed: Hass Avocado / see ad / $0.99
- **O Organics Organic Fresh Boneless Skinless Chicken Breast Value Pack.** — O Organics Organic Fresh Boneless Skinless Chicken Breast Value Pack. is $5.99 this week.
    - _full-week · not tracked at Costco · PROXY/manual-review · pack: regular_retail_pack_
    - Source: `safeway 7-8 - 7-14.pdf` p3 · raw: "O Organics Organic Fresh Boneless Skinless Chicken Breast Value Pack. 5.99 lb Member Price" · parsed: O Organics Organic Fresh Boneless Skinless Chicken Breast Value Pack. / per lb / $5.99
- **Land O'Lakes Butter 16-oz. Spread 13 to 15-oz. Selected varieties.** — Land O'Lakes Butter 16-oz. Spread 13 to 15-oz. is $3.49 this week.
    - _full-week · not tracked at Costco · PROXY/manual-review · pack: regular_retail_pack_
    - Source: `safeway 7-8 - 7-14.pdf` p3 · raw: "Land O'Lakes Butter 16-oz. Spread 13 to 15-oz. Selected varieties. 13 to 15-oz. 3 49 ea Member Price" · parsed: Land O'Lakes Butter 16-oz. Spread 13 to 15-oz. Selected varieties. / 13 to 15-oz. / $3.49
- **Ruffles Potato Chips** — Ruffles Potato Chips is $2.5 on sale — fine for a small haul, but Costco is still cheaper per unit in bulk.
    - _Friday-only · no Costco claim (weak/invalid proxy) · PROXY/manual-review · pack: regular_retail_pack_
    - Source: `safeway 7-8 - 7-14.pdf` p2 · raw: "Calidad Tortilla Chips 9-13 oz. 2/$5 Member Price Earn 4X Points" · parsed: Calidad Tortilla Chips 9-13 oz. / 9-13 oz. / $2.5
- **Red Cherries** — Red Cherries is $4.99 this week.
    - _full-week · no Costco claim (weak/invalid proxy) · PROXY/manual-review · pack: regular_retail_pack_
    - Source: `safeway 7-8 - 7-14.pdf` p2 · raw: "Red Cherries 4.99 lb Member Price" · parsed: Red Cherries / per lb / $4.99
- **Nabisco Chips Ahoy! Cookies (9.5–13 oz)** **[CORRECTED]** — Safeway has Nabisco Chips Ahoy! cookies (9.5–13 oz) at $3.49 when you buy 2 — a solid regular-pack cookie deal (single $3.99).
    - _full-week · not tracked at Costco · manual-verification (PDF-corrected) · pack: regular_retail_pack_
    - Source: `safeway 7-8 - 7-14.pdf` p5 · raw: "Nabisco Chips Ahoy! Cookies 9.5 to 13-oz. Selected varieties. $3.49 ea when you Buy 2 Member Price (single item $3.99)" · parsed: Nabisco Chips Ahoy! Cookies / 9.5–13 oz (selected varieties) / $3.49
- **Coca-Cola, Pepsi** — Coca-Cola is $3.99 this week.
    - _full-week · not tracked at Costco · PROXY/manual-review · pack: regular_retail_pack_
    - Source: `safeway 7-8 - 7-14.pdf` p1 · raw: "Coca-Cola, Pepsi or 7UP 12-pack, 12 fl oz cans or 8-pack, 12 fl oz bottles 3.99 EA MEMBER PRICE MIX & MATCH" · parsed: Coca-Cola, Pepsi / 12-pack, 12 fl oz cans or 8-pack, 12 fl oz bottles / $3.99
- **Foster Farms Fresh & Natural Chicken Leg Quarters** — Foster Farms Fresh & Natural Chicken Leg Quarters is $0.99 this week.
    - _full-week · not tracked at Costco · PROXY/manual-review · pack: regular_retail_pack_
    - Source: `safeway 7-8 - 7-14.pdf` p2 · raw: "Foster Farms Fresh & Natural Chicken Leg Quarters 99¢ lb Member Price Sold in 10 lb bag" · parsed: Foster Farms Fresh & Natural Chicken Leg Quarters / 10 lb bag / $0.99
- **Blade Steaks Pork Spareribs** — Blade Steaks Pork Spareribs is $2.99 this week.
    - _full-week · not tracked at Costco · PROXY/manual-review · pack: regular_retail_pack_
    - Source: `safeway 7-8 - 7-14.pdf` p1 · raw: "Signature SELECT Pork Shoulder Country Style Ribs or Blade Steaks Pork Spareribs 2.99 LB MEMBER PRICE" · parsed: Signature SELECT Pork Shoulder Country Style Ribs / per lb / $2.99
- **Red Seedless Grapes** — Red Seedless Grapes is $2.99 on sale — fine for a small haul, but Costco is still cheaper per unit in bulk.
    - _full-week · Costco still wins on bulk unit price · PROXY/manual-review; Costco Medium-confidence · pack: regular_retail_pack_
    - Source: `vons 7-8 - 7-14.pdf` p3 · raw: "Red Seedless Grapes $2.99 lb" · parsed: Red Seedless Grapes / per lb / $2.99
- **Large Mango** — Large Mango is $1.25 this week.
    - _full-week · not tracked at Costco · PROXY/manual-review · pack: regular_retail_pack_
    - Source: `safeway 7-8 - 7-14.pdf` p2 · raw: "Large Mango or Ataulfo Mangoes 4/$5 Member Price" · parsed: Large Mango / see ad / $1.25

### Vons (12) — compared only to Costco Tustin

- **Ritz Crackers** — Ritz Crackers hits $2.49 — historical low in our tracked ad history.
    - _full-week · not tracked at Costco · PROXY/manual-review · pack: regular_retail_pack_
    - Source: `vons 7-8 - 7-14.pdf` p2 · raw: "Ritz Crackers, Wheat Thins or Triscuit 3.5-13.7 oz, Selected varieties. Mix or Match any 4 or more participating items. $2.49 ea" · parsed: Ritz Crackers / 3.5-13.7 oz / $2.49
- **Nabisco Single Serve Snacks 10 pack (Oreo Mini / Mini Chips Ahoy / Nutter Butter Bites)** **[CORRECTED]** — Vons has Nabisco Single Serve Snacks (Oreo Mini / mini Chips Ahoy / Nutter Butter Bites), 10-pack, $3.99 with a digital coupon — these are lunchbox single-serve packs, NOT regular Chips Ahoy cookies.
    - _full-week · not tracked at Costco · manual-verification (PDF-corrected) · pack: single_serve_pack_
    - Source: `vons 7-8 - 7-14.pdf` p1 · raw: "Nabisco Single Serve Snacks 10 ct. Selected varieties. $3.99 ea DIGITAL ONLY, Limit 3 Total" · parsed: Nabisco Single Serve Snacks 10 pack / 10 ct (single-serve multipack) / $3.99
- **Wheat Thins** — Wheat Thins hits $2.49 — historical low in our tracked ad history.
    - _full-week · not tracked at Costco · PROXY/manual-review · pack: regular_retail_pack_
    - Source: `vons 7-8 - 7-14.pdf` p2 · raw: "Ritz Crackers, Wheat Thins or Triscuit 3.5-13.7 oz, Selected varieties. Mix or Match any 4 or more participating items. $2.49 ea" · parsed: Ritz Crackers / 3.5-13.7 oz / $2.49
- **Lucerne Large Eggs** — Lucerne Large Eggs is $2.49 this week.
    - _full-week · no Costco claim (normalization unreliable) · PROXY/manual-review · pack: multipack_
    - Source: `vons 7-8 - 7-14.pdf` p1 · raw: "Lucerne Large Eggs 12 ct $2.49 each" · parsed: Lucerne Large Eggs / 12 ct / $2.49
- **Cherries** — Cherries is $2.99 this week.
    - _full-week · no Costco claim (weak/invalid proxy) · PROXY/manual-review · pack: regular_retail_pack_
    - Source: `vons 7-8 - 7-14.pdf` p1 · raw: "Cherries $2.99 lb DIGITAL COUPON" · parsed: Cherries / per lb / $2.99
- **Green Seedless Grapes** — Green Seedless Grapes at $1.99 actually undercuts Costco per unit if you only want a small amount.
    - _Friday-only · beats Costco (per-unit, small-qty; fairness caveat) · PROXY/manual-review; Costco Medium-confidence · pack: regular_retail_pack_
    - Source: `vons 7-8 - 7-14.pdf` p3 · raw: "Red or Green Seedless Grapes $1.99 lb" · parsed: Red / per lb / $1.99
- **Nabisco Single Serve Snacks 10 pack (same coupon — Oreo Mini variety)** **[CORRECTED]** — Vons has Nabisco Single Serve Snacks (Oreo Mini / mini Chips Ahoy / Nutter Butter Bites), 10-pack, $3.99 with a digital coupon — these are lunchbox single-serve packs, NOT regular Oreo cookies.
    - _full-week · not tracked at Costco · manual-verification (PDF-corrected) · pack: single_serve_pack_
    - Source: `vons 7-8 - 7-14.pdf` p1 · raw: "Nabisco Single Serve Snacks 10 ct. Selected varieties. $3.99 ea DIGITAL ONLY, Limit 3 Total" · parsed: Nabisco Single Serve Snacks 10 pack / 10 ct (single-serve multipack) / $3.99
- **Signature SELECT Ice Cream 1.5 qt.** — Signature SELECT Ice Cream 1.5 qt. is $3.49 this week.
    - _full-week · not tracked at Costco · PROXY/manual-review · pack: regular_retail_pack_
    - Source: `vons 7-8 - 7-14.pdf` p1 · raw: "Ben & Jerry’s 14-16 oz. or 4 ct. Signature SELECT® Ice Cream 1.5 qt. Klondike 4-6 ct. Talenti 14-16 oz. Yasso 14-16 oz. or 4 ct. 3.49 each" · parsed: Ben & Jerry’s 14-16 oz. / 14-16 oz. or 4 ct. / $3.49
- **Lucerne Butter** — Lucerne Butter is $3.99 this week.
    - _full-week · not tracked at Costco · exact-match · pack: regular_retail_pack_
    - Source: `vons 7-8 - 7-14.pdf` p1 · raw: "Lucerne Butter 16 oz $3.99 each With Digital Coupon" · parsed: Lucerne Butter / 16 oz / $3.99
- **Cheez-It Crackers, Keebler Fudge Shoppe Cookies** — Cheez-It Crackers is $1.67 this week.
    - _Friday-only · not tracked at Costco · PROXY/manual-review · pack: regular_retail_pack_
    - Source: `vons 7-8 - 7-14.pdf` p3 · raw: "Cheez-It Crackers, Keebler Fudge Shoppe Cookies or Kellogg’s Rice Krispies Treats 3 for $5 Selected varieties, 6.6 to 13.7 oz." · parsed: Cheez-It Crackers, Keebler Fudge Shoppe Cookies / 6.6 to 13.7 oz / $1.67
- **Whole Chicken Bone-in, Value pack** — Whole Chicken Bone-in is $0.99 this week.
    - _full-week · not tracked at Costco · PROXY/manual-review · pack: regular_retail_pack_
    - Source: `vons 7-8 - 7-14.pdf` p1 · raw: "Signature SELECT® Thighs, Drumsticks or Whole Chicken Bone-in, Value pack Bone-in, Value pack 99¢ lb Member Price" · parsed: Signature SELECT® Thighs, Drumsticks / Bone-in, Value pack / $0.99
- **Large Hass Avocados** — Large Hass Avocados is $1.5 on sale — fine for a small haul, but Costco is still cheaper per unit in bulk.
    - _full-week · Costco still wins on bulk unit price · PROXY/manual-review; Costco Medium-confidence · pack: regular_retail_pack_
    - Source: `vons 7-8 - 7-14.pdf` p3 · raw: "Large Hass Avocados 2 for $3" · parsed: Large Hass Avocados / see ad / $1.5

## 6. Do-not-use claims (say none of these on camera)

1. **Smoked salmon is NOT fresh salmon.** Do not compare Acme Togarashi / Nova Smoked Salmon 3 oz @ $4.99 to the fresh-salmon fillet baseline ($9.29) or to any per-lb fresh salmon. It is a smoked-salmon ad deal only (~17% off its own $5.99 retail).
2. **No new all-time low on the fresh-salmon graph** from the $4.99 smoked pack. The canonical match audit **rejected** it (smoked vs fresh, 3–4 oz hard-negative). It must not update the salmon tracker.
3. **No fake baselines from unrelated products.** Ben & Jerry's $3.49 was matched to a Hershey's chocolate-strawberries baseline (`invalid_baseline`) — do not claim a % off.
4. **2-liter is not a 12-pack.** Coca-Cola / Pepsi 2 L @ $0.99 must not be presented as a 12-pack soda deal or compared to 12-pack cans (canonical audit rejected it).
5. **No 'beats Costco' on weak proxies.** Ruffles↔Doritos, cherries↔grapes, and soda↔Coke-Zero are discovery proxies, not valid Costco comparisons.
6. **Do not headline % off on proxy baselines** (`same_family_proxy`, `same_product_different_size`, `stale/missing/invalid_baseline`): butter spread, Chips Ahoy, Wheat Thins, Cheez-It, Signature Select ice cream, Ritz size-mismatch.
7. **Eggs vs Costco is unreliable.** Vons Lucerne eggs $2.49 vs Costco 5-dozen does not normalize cleanly (per-egg vs whole-pack) — do not claim it beats Costco.
8. **Vons "$3.99 Chips Ahoy / Oreo" is NOT regular cookies.** It is the *Nabisco Single Serve Snacks 10-ct* digital coupon (Oreo Mini / Mini Chips Ahoy / Nutter Butter Bites, Limit 3). Do not call it a regular Chips Ahoy or Oreo family-size cookie deal, do not use "10–15.35 oz," and do not update the chips_ahoy or oreo_family_size trackers with it.

## Guardrail — cookie pack types must not be merged

Regular cookie packs, family-size cookies, and single-serve snack multipacks are **distinct products** and must NOT be merged, cross-priced, or share a baseline/tracker unless explicitly intended:

- Chips Ahoy 9.5–13 oz **regular pack** ≠ Nabisco Single Serve Snacks 10-pack
- Oreo **family size** ≠ Oreo Mini 10-pack
- Chips Ahoy **regular cookies** ≠ Chips Ahoy **mini** multipack

Enforcement here: each script-ready item carries a `pack_type` (`regular_retail_pack` / `multipack` / `single_serve_pack` / `broad_promo_block`); items of different `pack_type` are never blended and single-serve/multipack items never feed a regular-pack canonical tracker.

## Final sanity checks

- [x] Ad week is 2026-07-08 → 2026-07-14 and is ACTIVE today (calendar-active, not preview).
- [x] Safeway compared **only** to fresh Costco San Francisco (07-07).
- [x] Vons compared **only** to fresh Costco Tustin (07-07).
- [x] No Safeway-vs-Vons comparison anywhere in this report.
- [x] Smoked salmon does NOT update the fresh-salmon tracker (canonical audit: rejected).
- [x] No new all-time low is claimed without an accepted canonical match.
- [x] Every 'beats Costco' statement uses the fresh 07-07 Costco data.
- [x] Shortlist is built from the audited baseline + fresh Costco recompute, NOT the stale expanded shortlist.
- [x] Safeway Chips Ahoy kept as a valid regular cookie pack (size corrected to 9.5–13 oz, PDF p5).
- [x] Vons single-serve coupon relabeled ('Nabisco Single Serve Snacks 10 pack') and NOT promoted as regular Chips Ahoy/Oreo cookies.
- [x] Every script-ready item has source provenance (PDF, page, raw offer text, parsed fields, pack_type).

---
**Use `fresh_costco_deal_report.md` (this file) as the single source of truth for scripting.**
