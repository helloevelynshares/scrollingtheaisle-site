# Price Tracker — Add Product Runbook

Incremental workflow for approving a user-suggested item into the live price tracker.
**Historical weekly ad extraction is cached** — normal adds never re-OCR or re-extract PDFs.

## Data layers (separation of concerns)

| Layer | Location | Role |
|-------|----------|------|
| Raw weekly ad source | `data/weekly_ads/flyer_manifest_*.csv`, PDFs in sibling repo | Week metadata + source files |
| Extracted normalized offers | `scrolling-the-aisle/outputs/product_discovery_{safeway,vons}/split_offer_items.csv` | **Durable cache** — vision/OCR output, reused every build |
| Canonical products | `src/data/canonicalProducts.ts`, Supabase `canonical_products` | Shared product definitions |
| Tracker families | `src/data/trackerFamilies.ts`, matchers in `generate_weekly_ad_prices.py` | Multi-SKU deal families (B&J, Ritz) |
| Matched observations | `src/data/weeklyAdPrices.generated.ts`, `vonsWeeklyAdPrices.generated.ts`, `familyWeeklyAdPrices.generated.ts` | Product × week × feed price points |
| Baselines | `src/data/priceTrackerFallback.ts` (Safeway), `vonsBaseline.generated.ts`, Supabase `feed_product_matches` | Store search anchor prices |
| Costco comparisons | `src/data/priceComparisons.generated.ts`, `costcoPriceHistory.generated.ts` | Grocery vs warehouse |
| Runtime UI | `/staging-price-tracker/`, Supabase observations | Built from generated TS + live API |

## Extraction cache (already exists)

- **Safeway:** `~/Documents/scrolling-the-aisle/outputs/product_discovery_safeway/split_offer_items.csv` (~1500 rows)
- **Vons:** `~/Documents/scrolling-the-aisle/outputs/product_discovery_vons/split_offer_items.csv` (~800 rows)
- Stable keys per row: `split_item_id`, `week_start`, `week_end`, `source_file`, `banner`, `region`, offer text, price, package, promo fields
- Regenerated only when a **new ad week** is vision-processed in the sibling repo — **not** on each product add
- `generate_weekly_ad_prices.py` only reads this CSV (cheap regex matching)

## Expensive vs cheap steps

| Step | Cost | When needed |
|------|------|-------------|
| PDF/vision/OCR extraction | **Expensive** | New ad week only (sibling repo) |
| Weekly ad text normalization | **Expensive** (part of extraction) | Same — cached in split_offer_items |
| Product matching vs normalized rows | **Cheap** | Every add — incremental flags limit scope |
| Safeway/Vons baseline API crawl | **Expensive** | New product only (`--run-baseline`) |
| Costco CSV matching | **Cheap** | New product only (`--product-id`) |
| UI TS generation | **Cheap** | Merge into existing files |

---

## Minimum metadata for a new tracker item

Before running the pipeline, add:

1. **`src/data/canonicalProducts.ts`** — `id`, `displayName`, `searchAliases`, `sortOrder`, `costcoComparable`
2. **`scripts/generate_weekly_ad_prices.py`** — `ProductMatcher` + `TRACKER_CANONICAL_IDS` entry
3. **`data/canonical/price_tracker_baseline_queries.csv`** — baseline search row
4. **`data/canonical/price_tracker_baseline_queries_new_only.csv`** — same row (for incremental crawl)
5. **`scripts/price_comparison/canonical_metadata.py`** — if Costco badge desired
6. Optional: Supabase migration for `canonical_products` (or run full `generate_price_tracker_seed.py` after backfill)

---

## Approve user suggestion → live tracker

After admin approves at `/admin/suggestions/`, complete metadata (above), then:

### Option A — orchestrator (recommended)

```bash
# Validate metadata + dry-run commands
python3 scripts/add_tracker_product.py --product-id NEW_ID --dry-run

# Full incremental pipeline (requires fresh SAFEWAY_COOKIE / VONS_COOKIE)
python3 scripts/add_tracker_product.py --product-id NEW_ID --all
```

### Option B — step by step

```bash
# 1. Baselines — new product only, merge into existing CSVs
python3 scripts/seed_safeway_baseline.py --browser-like \
  --input data/canonical/price_tracker_baseline_queries_new_only.csv \
  --csv data/processed/safeway_baseline_candidates_new_only.csv \
  --merge-csv data/processed/safeway_baseline_candidates_v1.csv

python3 scripts/generate_safeway_feed_matches.py --merge-fallback

python3 scripts/seed_vons_baseline_playwright.py --http-only \
  --input data/canonical/price_tracker_baseline_queries_new_only.csv \
  --csv data/processed/vons_baseline_candidates_new_only.csv \
  --merge-csv data/processed/vons_baseline_candidates_v1.csv

python3 scripts/generate_vons_feed_matches.py

# 2. Historical weekly ad backfill — cache only, no PDF re-extraction
python3 scripts/generate_weekly_ad_prices.py --product-id NEW_ID

# Or auto-detect products missing from generated output:
python3 scripts/generate_weekly_ad_prices.py --new-only

# 3. Costco comparison — scoped to new product
python3 scripts/backfill_price_comparisons.py --product-id NEW_ID

# 4. Build + verify
npm run build:price-tracker
```

---

## CLI reference — weekly ad matching

```bash
python3 scripts/generate_weekly_ad_prices.py                      # full rematch (all products)
python3 scripts/generate_weekly_ad_prices.py --full-rematch         # explicit full rematch
python3 scripts/generate_weekly_ad_prices.py --product-id grapes
python3 scripts/generate_weekly_ad_prices.py --product-ids a,b
python3 scripts/generate_weekly_ad_prices.py --new-only
python3 scripts/generate_weekly_ad_prices.py --family-id ben_jerrys_ice_cream
python3 scripts/generate_weekly_ad_prices.py --feed safeway         # one feed only
python3 scripts/generate_weekly_ad_prices.py --dry-run
```

Output always reports `extraction=0 (cache only)` unless you run vision pipeline in sibling repo.

---

## One-time full historical extraction (only if cache incomplete)

If a week is in `flyer_manifest_*.csv` but missing from `split_offer_items.csv`:

1. Run vision pipeline in `scrolling-the-aisle` for that PDF/week
2. Append rows to `split_offer_items.csv`
3. Then run `python3 scripts/generate_weekly_ad_prices.py --full-rematch` once

Do **not** rerun extraction for normal product adds.

---

## Validate

```bash
npm run verify:price-tracker
# Open /staging-price-tracker/ — new card should chart with weekly ad + baseline
```

---

## Remaining manual steps

- Admin approval of vote suggestion (`tracker_vote_items.status = approved`)
- Metadata edits in TS/Python/CSV (no auto-sync from admin UI yet)
- Cookie refresh when baseline crawls fail
- Supabase seed SQL is not incremental — apply product row manually or full regen
- New ad weeks still require sibling-repo vision extraction before matching
