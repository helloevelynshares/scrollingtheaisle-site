# AisleCheck historical deal-assessment policy

Date: 2026-08-04  
Policy version: `aislecheck_history_v1`  
Code: `scripts/deal_assessment/`

## 1. Historical source used

- Safeway Bay Area: `src/data/weeklyAdPrices.generated.ts`
- Vons / Albertsons SoCal: `src/data/vonsWeeklyAdPrices.generated.ts`
- Tracker metadata: `src/data/canonicalTrackerFamilies.generated.ts` / `data/canonical_tracker_families.yaml`
- Thresholds: `config/price_benchmark_thresholds.json`
- Benchmark helpers: `scripts/weekly_ad_analysis/benchmarks.py`

## 2. Why generated files (not live Supabase)

Price-tracker grocery tabs already treat generated TS as source of truth and bypass Supabase for Safeway/Vons feeds. Seeds can lag. Hosted scoring therefore reads the same committed generated series the site charts use.

## 3. Comparable observation

A week counts when the generated entry has:

- a non-null `price` (already normalized unit price)
- `confidence` present and not `"low"`

Baseline-fallback / null BOGO weeks without a usable price are excluded by that rule.

## 4. Minimum-history threshold

| Comparable weeks | Status | Shopper label |
|---|---|---|
| 0–1 | `insufficient_data` | Not enough history |
| 2–3 | `limited_data` | Early price signal |
| 4+ | normal verdict from benchmark buckets | All-time low / Near all-time low / Strong / Normal / Weak sale |

Constants: `scripts/deal_assessment/policy.py`  
`limited_data` returns evidence (unit price, low, median) but **never** a strong stock-up / good / fair sale label.

## 5. Definition of “typical”

Typical = **median** of chartable unit prices in the feed series for that tracker (`market_median_unit_price` / `typical_unit_price` in evidence). Same semantics as the price-tracker benchmark helpers.

## 6. Duplicate weekly observations

Duplicate prices across different weeks are kept as separate observations (they reflect real ad recurrence). Same-week keys cannot duplicate inside the generated map (one entry per `weekStart`).

## 7. BOGO and multi-buy

Submitted structured fields only (no free-text reparse):

- `multi_buy` / `n_for` with quantity N and total `$X` → unit = `X / N`
- `bogo` / `buy_x_get_y` with reference shelf price → unit = `price / 2`
- `$X each when buying N` (`price_basis=each`) → unit = `X`
- Missing BOGO reference price → `invalid_offer` / cannot normalize

History already stores effective unit prices when the weekly pipeline could normalize them.

## 8. Size ranges

When the family subtitle has an oz range (e.g. Doritos 5–13 oz) and the offer includes an oz size outside that range → `not_comparable` (`package_size_out_of_family_range`). Missing size is allowed (soft).

## 9. Cases that return no full verdict

- `insufficient_data` (0–1 weeks)
- `limited_data` (2–3 weeks; directional only)
- `not_comparable` (unsupported retailer, unknown tracker, size out of range, …)
- `invalid_offer` (missing/zero/negative price, incomplete multi-buy, …)
- History load failure → HTTP 500 (no fabricated series)

## 10. Known limitations

- Week-level ad history, not daily shelf scrapes
- Safeway and Vons series are never mixed
- Some trackers have empty or sparse series
- Some BOGO/B2G weeks remain null when vision had no reference price
- Deal-family mixed forms are not member-scored in v1
- Homepage public scoring stays behind `assessEnabled` until hosted validation passes
