# Project Notes

Living notes for findings, gotchas, and repeatable workflows discovered while building this project.

## Safeway / Albertsons API Notes

### If a Safeway query fails, refresh the cookie first

Date discovered: 2026-05-24  
Context: Safeway price-result queries (requests or Playwright) during grocery price tracking.  
What happened: Failed searches, empty/stale results, infinite “loading” on search results, `api_timeout`, or 401/403 usually mean the session cookie expired—not bad query params.  
Fix / workaround: **Default assumption: needs a new cookie.** Paste a fresh `Cookie` header from Chrome DevTools → Network → `pgmsearch` into `scripts/.env` as `SAFEWAY_COOKIE`, then retry. Treat cookies as short-lived session state, not stable credentials.  
How to verify: After updating `.env`, rerun one item (e.g. `python scripts/seed_safeway_tracked_playwright.py --query oreo_original_family_size --headful -v`). Expect `200 success` before debugging payload or code.  
Related files: `scripts/.env` (`SAFEWAY_COOKIE`), `scripts/playwright_session.py`, `scripts/safeway_client.py`, `scripts/seed_safeway_tracked_playwright.py`

### Playwright must use SAFEWAY_COOKIE from .env (profile alone is not enough)

Date discovered: 2026-05-24  
Context: TikTok-informed ledger seeding via Playwright (`seed_safeway_tracked_playwright.py`).  
What happened: Search results page loaded (`Search Results | Safeway`) but products spun forever; pgmsearch API never fired. Python `requests` with the same session worked when `SAFEWAY_COOKIE` was set. Persistent profile `scripts/.playwright-profile` did not carry Imperva/login cookies.  
Fix / workaround: Inject `SAFEWAY_COOKIE` from `scripts/.env` into Playwright on startup (`scripts/playwright_session.py`). Refresh cookie from Chrome DevTools → Network → pgmsearch request.  
How to verify: Log shows `Applying N cookie(s) from scripts/.env` then `200 success` and rows in `data/processed/safeway_tracked_candidates_v1.csv`.  
Related files: `scripts/playwright_session.py`, `scripts/seed_safeway_search_playwright.py`, `scripts/seed_safeway_tracked_playwright.py`, `scripts/.env`

### Raw Python requests often timeout; use Playwright for pgmsearch

Date discovered: 2026-05-24  
Context: Direct calls to `https://www.safeway.com/abs/pub/xapi/pgmsearch/v1/search/products`.  
What happened: Same URL returned 200 in Chrome but timed out from Python `requests` even with subscription key, visitorId, uuid, and user-agent.  
Fix / workaround: Use Playwright Chromium with browser-like headers and `.env` cookies; capture the pgmsearch XHR from the search results page.  
How to verify: `python scripts/seed_safeway_tracked_playwright.py --query oreo_original_family_size --headful -v`  
Related files: `scripts/seed_safeway_search_playwright.py`, `scripts/seed_safeway_tracked_playwright.py`

### Resume Playwright batch after cookie expiry mid-run

Date discovered: 2026-05-24  
Context: Full 50-item ledger crawl; session died around item 39 (spinner stuck).  
What happened: First 38 items succeeded, then pgmsearch stopped firing until cookie refresh. Re-running without `--resume` overwrote JSONL and redid all 38.  
Fix / workaround: `python scripts/seed_safeway_tracked_playwright.py --headful --delay 3 --resume` skips `canonical_id` rows that already have `ok: true` in the output JSONL. Refresh `SAFEWAY_COOKIE` first. Use `--retry-failed` to re-attempt prior failures.  
How to verify: Log shows `Resume: 50 in scope, 38 already ok (skipped), 12 to run`.  
Related files: `scripts/seed_safeway_tracked_playwright.py`

### pgmsearch endpoint and ledger workflow

Date discovered: 2026-05-24  
Context: Food-only TikTok SKU tracking (50 items), not generic staples.  
What happened: Staples seed (`manual_canonical_50.csv`) included non-food items; first search hit per query is often wrong for canonical matching.  
Fix / workaround: Use `data/canonical/safeway_tracked_items_v1.csv` for tracked SKUs; fetch candidates with Playwright; manually fill `accepted_pid` / `accepted_upc` (no fuzzy match in v1).  
How to verify: Ledger has 50 rows `status=needs_selection`; candidates CSV has top-N products per `canonical_id`.  
Related files: `data/canonical/safeway_tracked_items_v1.csv`, `data/processed/safeway_tracked_candidates_v1.csv`, `scripts/ledger.py`, `data/README.md`

## API Gotchas

Add notes here for auth headers, cookies, rate limits, payload quirks, pagination, or anti-bot behavior.

Required `.env` for web pgmsearch (requests path): `SAFEWAY_SUBSCRIPTION_KEY`, `SAFEWAY_USER_AGENT`, `SAFEWAY_VISITOR_ID`, `SAFEWAY_UUID`, optional `SAFEWAY_COOKIE`.

### Vons search stuck on loading spinner (pgmsearch never fires)

Date discovered: 2026-06-13  
Context: `seed_vons_baseline_playwright.py --headful` or injected `VONS_COOKIE` on vons.com.  
What happened: Search results page loads but products spin forever; DevTools shows no `pgmsearch` XHR. Same root causes as Safeway: **stale/wrong cookie**, **Safeway cookie reused on Vons**, **store/zip/channel mismatch**, **corrupted Playwright profile**, or **Imperva bot tags** (`xDTags: bad_user_agents, non_human`). Raw Python `requests` usually **times out** (Imperva TLS fingerprint) even with subscription key + cookie.  
Fix / workaround:
1. Copy a **fresh** `Cookie` header from Chrome/Safari → vons.com → Network → `pgmsearch` → `scripts/.env` as `VONS_COOKIE` (must include `ACI_S_ECommBanner=vons`, not safeway).
2. Copy matching query params: `VONS_VISITOR_ID`, `VONS_STORE_ID`, `VONS_ZIPCODE`, `VONS_CHANNEL` from the same pgmsearch request. **`uuid` is optional** (working Safari captures omit it).
3. Use **store 2053 / zip 92110 / channel instore** for San Diego guest store (Orange 2335/92865/pickup caused stuck search + OSSR0033-R errors).
4. Set `VONS_USER_AGENT` to Safari UA from the working capture (Chrome UA can trigger Imperva tags).
5. Headful manual reset: `python scripts/seed_vons_baseline_playwright.py --headful --channel chrome --manual-session --fresh-profile --query grapes` — set store/zip, sign in if prompted, press Enter.
6. HTTP-only path after `.env` refresh: `python scripts/seed_vons_baseline_playwright.py --http-only --delay 1` (`vons_client.py` uses **curl**, not requests).
How to verify: Log shows `200 success`; `data/processed/vons_baseline_candidates_v1.csv` has rows.  
Related files: `scripts/playwright_session.py`, `scripts/seed_vons_baseline_playwright.py`, `scripts/vons_client.py`, `scripts/.env`

### Vons pgmsearch env vars (not interchangeable with Safeway)

Date discovered: 2026-06-13  
Context: Vons baseline crawl (`scripts/seed_vons_baseline_playwright.py`, `scripts/vons_client.py`).  
What happened: Reusing Safeway `visitorId`/`storeid` on vons.com causes timeouts; wrong store/zip/channel (2335/92865/pickup vs 2053/92110/instore) returns OSSR0033-R or stuck spinner. Imperva blocks Python `requests` TLS; use curl transport in `vons_client.py`.  
Fix / workaround: Copy pgmsearch query params from **vons.com** DevTools into `scripts/.env`: `VONS_VISITOR_ID`, `VONS_STORE_ID=2053`, `VONS_ZIPCODE=92110`, `VONS_CHANNEL=instore`, optional `VONS_UUID`, fresh `VONS_COOKIE`, `VONS_USER_AGENT` (Safari), `VONS_SUBSCRIPTION_KEY`. Request-id must be 19-digit browser format: `628` + epoch-ms + 3-digit suffix.  
How to verify: `python scripts/seed_vons_baseline_playwright.py --http-only --query goldfish` returns 200; full run populates CSV for all 10 baseline queries. Refresh `VONS_COOKIE` if curl times out with 0 bytes (session expires quickly).  
Related files: `scripts/vons_config.py`, `scripts/vons_client.py`, `scripts/.env.example`

### Vons pgmsearch HTTP uses curl (not requests)

Date discovered: 2026-06-13  
Context: `scripts/vons_client.py` direct HTTP after working Safari DevTools curl.  
What happened: Same URL + cookie returns 200 in curl but Python `requests` read-times out; wrong `request-id` format (`time_ns()` only) returns OSSR0033-R 400.  
Fix / workaround: `search_vons_product` shells out to `curl --compressed` with Safari-like headers. `generate_vons_request_id()` returns `628{epoch_ms}{3-digit suffix}`. Keep `pgm=wineshop,merch-banner` comma unencoded in query string.  
How to verify: `search_vons_product('goldfish')` → 200 with ~40 `primaryProducts.response.docs`.  
Related files: `scripts/vons_client.py`

### Safeway/Vons timeout env vars and error messages

Date discovered: 2026-06-13  
Context: HTTP/curl and Playwright pgmsearch runs when cookies expire or Imperva stalls.  
What happened: Requests hung with generic errors; users could not tell timeout vs auth vs stale cookie.  
Fix / workaround: Set `SAFEWAY_TIMEOUT_SECONDS=30` (requests) or `VONS_TIMEOUT_SECONDS=45` (curl) in `scripts/.env`. Playwright seeds use `--api-timeout` (default 45s) and `--navigation-timeout` (default 60s). On timeout, logs include actionable text — e.g. refresh `SAFEWAY_COOKIE` / `VONS_COOKIE` from DevTools → Network → pgmsearch; Vons also notes store/zip (`VONS_STORE_ID=2053`, `VONS_ZIPCODE=92110`). Errors distinguish `timeout`, `auth` (401/403), and `empty_response`.  
How to verify: Run with an expired cookie; expect a clear timeout/auth message within the configured seconds, not an indefinite hang.  
Related files: `scripts/safeway_client.py`, `scripts/vons_client.py`, `scripts/safeway_config.py`, `scripts/vons_config.py`, `scripts/seed_safeway_search_playwright.py`, `scripts/seed_vons_baseline_playwright.py`

## Data Extraction Notes

Weekly ad prices for the staging price tracker:

- Manifest (week → PDF): `data/weekly_ads/flyer_manifest_safeway.csv` (synced from `scrolling-the-aisle/inputs/weekly_ads/`)
- Offer rows: `scrolling-the-aisle/outputs/product_discovery_safeway/split_offer_items.csv`
- Regenerate: `npm run generate:weekly-ad-prices` → `src/data/weeklyAdPrices.generated.ts`

Gotchas: grouped offers split into per-item rows — matchers in `scripts/generate_weekly_ad_prices.py` pick the best split row per canonical item. Multi-buy promos need per-unit normalization (`3 for $5`, `when you buy 3`, etc.). Some tracker items have no ad match yet (e.g. Coke Zero 12pk) or use a close proxy (Fairlife → Premier Protein 4pk).

**Vons baselines (SoCal):** Same Albertsons `pgmsearch` API — `python scripts/seed_vons_baseline_playwright.py --http-only` (curl transport in `vons_client.py`; Playwright fallback). Env: `VONS_COOKIE`, `VONS_VISITOR_ID`, `VONS_STORE_ID=2053`, `VONS_ZIPCODE=92110`, `VONS_CHANNEL=instore`, `VONS_USER_AGENT` (Safari), optional `VONS_UUID`, `VONS_SUBSCRIPTION_KEY`. Then `npm run generate:vons-feed-matches` → `src/data/vonsBaseline.generated.ts`. **Vons weekly ads** via `vonsWeeklyAdPrices.generated.ts`.

TikTok mentions: `python scripts/extract_tiktok_food_mentions.py` reads `bulk_transcripts.csv` → `data/processed/tiktok_item_mentions.csv`.

## Price Tracking Logic

### Safeway recurring items need baseline OR inferred ad anchor to chart

Date discovered: 2026-06-18  
Context: 8 recurring cross-store products on Safeway tab (`fage_greek_yogurt`, `frito_lay_multipack_chips`, etc.) showed “Tracking soon” despite weekly ad data in Supabase and `weeklyAdPrices.generated.ts`.  
What happened: New recurring items have **no** `feed_product_matches` / `SAFEWAY_BASELINES` crawl yet (only original 10 staples do). `hasFeedData` was true from weekly ad observations, but `ProductCard` and `priceTrackerUtils` also required `baselinePrice != null`, so charts never rendered. Vons worked because `vonsBaseline.generated.ts` has all 18 products.  
Fix / workaround: `inferBaselineFromWeeklyPrices()` uses max non-low-confidence ad price as chart anchor when no store baseline exists. `hasChartableData()` gates the UI. `priceTrackerApi` enriches sparse Supabase rows from offline fallback. To add true Safeway baselines: crawl with `scripts/seed_safeway_baseline_playwright.py` then `python scripts/generate_safeway_feed_matches.py`.  
How to verify: Safeway tab → recurring section → all 8 cards show charts with weekly ad trend lines. `npm run build:price-tracker` then reload `/staging-price-tracker/`.  
Related files: `src/staging-price-tracker/ProductCard.tsx`, `src/data/priceTrackerUtils.ts`, `src/data/priceTrackerFallback.ts`, `src/lib/priceTrackerApi.ts`, `src/data/weeklyAdPrices.generated.ts`

### Friday-only deals should dip on one day, not the whole week

Date discovered: 2026-06-07  
Context: Safeway weekly ads + staging price tracker charts (`/staging-price-tracker/`).  
What happened: Some Safeway promos are **Friday-only** (e.g. `$5 FRIDAY MAR. 27TH` in `friday_only_block` layout). The price tracker currently plots **one price per flyer week** (`week_start` → `week_end`), so a Friday deal can look like it applies all week.  
Fix / workaround (future): Use `availability_type_guess` / `price_role_guess` from `split_offer_items.csv` (`friday_only`, `short_term_dip`). Options: (a) for Friday-only matches, keep the weekly chart at **baseline** and annotate “Friday $X” in the tooltip; or (b) switch to **daily** points within the ad week (baseline Mon–Thu, ad price on Friday only). Do not treat `friday_only` rows as the effective price for the full week.  
How to verify: Find a `friday_only` row in `scrolling-the-aisle/outputs/product_discovery_safeway/split_offer_items.csv`; confirm chart behavior matches chosen rule.  
Related files: `scripts/generate_weekly_ad_prices.py`, `src/data/priceTrackerV1.ts`, `src/staging-price-tracker/PriceTrendChart.tsx`, `scrolling-the-aisle/outputs/product_discovery_safeway/split_offer_items.csv` (`availability_type_guess`, `promo_text`).

## Cursor / Dev Workflow Notes

### Tracker vote suggestions are moderated before appearing publicly

Date discovered: 2026-06-13  
Context: Price tracker voting module (`TrackVoteModule`) on `/staging-price-tracker/`.  
What happened: User suggestions used to insert into `product_track_suggestions` and show immediately.  
Fix / workaround: New table `tracker_vote_items` with `status` (`pending|approved|rejected|merged`). Public UI reads `status='approved'` only; new suggestions go to `pending` via RPC `submit_suggestion`. Admin review at `/admin/suggestions/` (password via Edge Functions `validate-admin` + `admin-suggestion-actions`).  
How to verify: Submit a custom item on the tracker → success message about review, item not in list. Approve in admin → item appears and accepts votes via RPC `vote_on_item`.  
Related files: `supabase/migrations/20260614_tracker_vote_items.sql`, `src/staging-price-tracker/TrackVoteModule.tsx`, `src/admin/suggestions/`, `supabase/functions/validate-admin/`, `supabase/functions/admin-suggestion-actions/`

Deploy admin Edge Functions and set secret:

```bash
supabase secrets set ADMIN_PASSWORD=your-secret
supabase functions deploy validate-admin
supabase functions deploy admin-suggestion-actions
```

Apply migration: `supabase db push` or run SQL in Supabase dashboard.

### Recharts Line must be direct children of LineChart (no Fragment wrappers)

Date discovered: 2026-07-05  
Context: Price tracker graphs on `/staging-price-tracker/` after unified Costco/grocery chart refactor (commit 7795b89).  
What happened: Axes, grid, and baseline reference line rendered but **zero** price lines/dots/tooltips. Recharts `findAllByType(children, Line)` returned empty when `<Line />` components were wrapped in `<>...</>` fragments inside the range/unified ternary.  
Fix / workaround: Keep each `<Line />` as a **direct** child of `<LineChart>` (same pattern as pre-refactor). Conditional lines use `{cond ? <Line /> : null}`, not fragment groups.  
How to verify: Playwright — `.recharts-line` count > 0 and hover on a dot shows `.price-tracker-chart-tooltip` with a price. `npm run build:price-tracker`.  
Related files: `src/staging-price-tracker/PriceTrendChart.tsx`

### Price tracker Vite entry must be `src/staging-price-tracker/index.html`, not `staging-price-tracker/index.html`

Date discovered: 2026-06-07  
Context: `npm run build:price-tracker` / deploying June weekly ad data.  
What happened: `staging-price-tracker/index.html` is the **deployed** output (overwritten by `scripts/sync-price-tracker-dist.mjs`). It references pre-built `assets/index-*.js`. Using it as the Vite `rollupOptions.input` rebundles stale JS — source/data changes in `src/` never reach the chart.  
Fix / workaround: Vite input is `src/staging-price-tracker/index.html` (loads `main.tsx`). Sync copies build output into `staging-price-tracker/` for GitHub Pages. Do not put the source HTML under `price-tracker/` — that path is gitignored.  
How to verify: `npm run build:price-tracker` runs `scripts/verify-price-tracker-build.mjs` automatically (fails if the JS bundle is missing any `weekStart` from `weeklyAdPrices.generated.ts`). Manual check: `grep 2026-06-03 staging-price-tracker/assets/index-*.js`. After deploy, hard-refresh the live page and confirm the latest week on the chart x-axis.  
Related files: `vite.config.ts`, `src/staging-price-tracker/index.html`, `scripts/sync-price-tracker-dist.mjs`, `scripts/verify-price-tracker-build.mjs`, `staging-price-tracker/`

Add notes here for useful Cursor prompts, commands, migrations, local testing, and deployment steps.

Living notes rule: `.cursor/rules/project-notes.mdc` — agents should read and update `docs/PROJECT_NOTES.md`.

Playwright setup: `pip install -r scripts/requirements.txt && playwright install chromium`

### Costco price data for grocery vs Costco comparisons

Date discovered: 2026-06-14  
Context: `price_comparisons` backfill and badge on `/staging-price-tracker/`.  
What happened: Costco warehouse CSVs live outside this repo at `~/Documents/costco-mvp/costco_data` (flat `{date}_{location}_consolidated.csv` plus older per-category CSVs). Default consolidated searches are `cracker chip protein chicken` — produce/eggs/soda often have no Costco row until more terms are crawled.  
Fix / workaround: Run `python3 scripts/backfill_price_comparisons.py` (override path with `COSTCO_DATA_ROOT`). Maps Safeway → `san-francisco` / `costco_sf`, Vons → `tustin` / `costco_oc`. Writes `supabase/migrations/20260617_price_comparisons_seed.sql` + `src/data/priceComparisons.generated.ts`. Apply schema migration `20260616_price_comparisons.sql` before seed.  
How to verify: Backfill log shows item counts per location; cards show badges like "Via Safeway", "Via Costco", or "Not found at Costco" (scoped to the active grocery tab vs Costco — never cross-compares Safeway vs Vons). Re-run is idempotent (`on conflict` upsert).  
Related files: `scripts/backfill_price_comparisons.py`, `scripts/price_comparison/`, `COSTCO_DATA_ROOT`, `src/staging-price-tracker/ComparisonBadge.tsx`

### Costco warehouse pricing import cache (read-only from costco-mvp)

Date discovered: 2026-07-05  
Context: Price tracker graph Costco comparison lines; data lives in sibling repo `costco-mvp/costco_data`.  
What happened: Pipeline read CSVs directly at build time; warehouse slugs mixed filename hyphens (`san-francisco`) with no local cache; product matching was text-only.  
Fix / workaround: `scripts/price_comparison/import_costco_data.py` imports read-only CSVs → `data/processed/costco/observations.json` + `manifest.json`. Central mapping: `config/costco_warehouse_mapping.json` (Safeway→`san_francisco`, Vons→`tustin`, Seattle imported but not wired to grocery tabs). Item numbers: `config/costco_item_mappings.csv` (warehouse-specific when SKUs differ). `backfill_price_comparisons.py` auto-imports then generates `costcoPriceHistory.generated.ts` / `priceComparisons.generated.ts`. No cross-warehouse fallback.  
How to verify: `npm run import:costco-data` then `npm run generate:price-comparisons`; `PYTHONPATH=scripts python3 -m unittest scripts.price_comparison.test_costco_loader`; Safeway Doritos chart → SF item #2014409; Vons → Tustin #933402; `npm run build:price-tracker`.  
Related files: `scripts/price_comparison/`, `config/costco_warehouse_mapping.json`, `config/costco_item_mappings.csv`, `src/data/costcoRegions.ts`, `data/processed/costco/`


Date discovered: 2026-06-19  
Context: Location-aware Costco tracker on `/staging-price-tracker/`.  
What happened: Costco CSVs are per warehouse (`2026-06-18_san-francisco_consolidated.csv`, `_tustin_`, `_seattle_`). Safeway compares only SF Costco; Vons/Albertsons compares only Tustin; Seattle is parsed into history but not wired to grocery tabs until a Seattle tracker exists.  
Fix / workaround: Region slugs/types in `src/data/costcoRegions.ts`; loader in `scripts/price_comparison/costco_loader.py` (`CostcoObservation`, filename date/region parse, date mismatch warnings). Backfill writes `src/data/costcoPriceHistory.generated.ts` for regional chart overlays. UI badges/charts show "Costco comparison uses San Francisco/Tustin Costco pricing."  
How to verify: `npm run generate:price-comparisons`; Safeway tab → Doritos chart has blue Costco line + SF note; Vons tab → separate Tustin history; `PYTHONPATH=scripts python3 -m unittest scripts.price_comparison.test_costco_loader`.  
Related files: `src/data/costcoRegions.ts`, `src/data/costcoPriceHistory.generated.ts`, `scripts/price_comparison/costco_loader.py`, `src/staging-price-tracker/PriceTrendChart.tsx`, `src/data/priceComparisonUtils.ts`

### Tracker families are additive client-side layers

Date discovered: 2026-06-19  
Context: Handpicked deal families (Ben & Jerry's, Ritz) on `/staging-price-tracker/`.  
What happened: Families are separate from the 18 `canonical_products` rows — `haagen_dazs_ice_cream` stays as single-SKU; families use new IDs (`ben_jerrys_ice_cream`, `ritz_crackers_snacks`).  
Fix / workaround: Definitions in `src/data/trackerFamilies.ts`; weekly ad matchers in `scripts/generate_weekly_ad_prices.py` write `src/data/familyWeeklyAdPrices.generated.ts` (family + per-member prices). UI merges via `appendFamiliesToFeedProducts()` in `trackerFamilyUtils.ts` — not yet in Supabase `canonical_products`. Ritz Costco copy uses static warehouse reference ($10.79 / 61.6 oz) with 10%/25% thresholds in `getFamilyComparisonBadge()`.  
How to verify: `npm run build:price-tracker`; Safeway tab → "Handpicked deal families" section with B&J range chart and Ritz "Best value: Costco" / "More variety" badge.  
Related files: `src/data/trackerFamilies.ts`, `src/data/trackerFamilyUtils.ts`, `src/data/familyWeeklyAdPrices.generated.ts`, `src/staging-price-tracker/ProductCard.tsx`

### Weekly ad video brief workflow (watchlist-first)

Date discovered: 2026-06-24  
Context: Repeatable creator workflow for Bay Area Safeway + SoCal Vons/Albertsons short-form scripts.  
What happened: Price tracker already had canonical products, weekly ad matchers, and Costco comparison modules — but no market-scoped brief generator. Legacy `safeway_tracked_items_v1.csv` (50 TikTok SKUs) is separate from the live 18+2 tracker.  
Fix / workaround: **Option B** — `config/content_watchlist_overrides.csv` references existing `canonical_product_id` / `canonical_category_id` (families) for video metadata only. Markets in `config/markets.json` (`bay_area`, `socal_oc`). Run:

```bash
npm run analyze-weekly-ad -- --week=YYYY-MM-DD --market=bay_area
npm run analyze-weekly-ad -- --week=YYYY-MM-DD --market=socal_oc
```

Inputs: `data/weekly_ads/{week}/{market}/` with grocer PDF **or** `split_offer_items.csv` (preferred), plus `costco_consolidated.csv`. Outputs: `output/weekly_deals/{week}/{market}/` (`matched_watchlist_deals.csv`, `ranked_video_candidates.csv`, `video_brief.md`, etc.). Reuses matchers from `scripts/generate_weekly_ad_prices.py`, Costco logic from `scripts/price_comparison/`, historical benchmarks from `weeklyAdPrices.generated.ts` / `vonsWeeklyAdPrices.generated.ts`. PDF fallback uses `pypdf` (`pip install pypdf`).  
How to verify: Drop Jun 17 `split_offer_items.csv` + Costco consolidated CSV into input folder; run both markets; open `video_brief.md`.  
Related files: `scripts/analyze_weekly_ad.py`, `scripts/weekly_ad_analysis/`, `config/markets.json`, `config/content_watchlist_overrides.csv`

### Safeway image-only PDFs need split_offer_items.csv (not pypdf)

Date discovered: 2026-06-24  
Context: `analyze-weekly-ad` for week `2026-06-24` bay_area with `safeway 6-24 - 6-30.pdf`.  
What happened: `pypdf` extracted 0 text chars from all 12 pages (image-based flyer). Pipeline ran but produced empty `matched_watchlist_deals.csv` and `debug_unmatched_items.csv`.  
Fix / workaround: Prefer `split_offer_items.csv` from the scrolling-the-aisle vision pipeline (`discover_product_candidates.py`) in the input folder. PDF fallback only works when the PDF has a text layer.  
How to verify: `python3 -c "from pypdf import PdfReader; print(len(PdfReader('safeway_ad.pdf').pages[0].extract_text() or ''))"` — expect >0 for text PDFs.  
Related files: `scripts/weekly_ad_analysis/ad_loader.py`, `data/weekly_ads/{week}/bay_area/`

### Shared price benchmark buckets (pipeline + UI)

Date discovered: 2026-06-24  
Context: Weekly ad scoring and future UI deal badges need explicit historical buckets, not just `getLowestObservedPrice`.  
What happened: `priceTrackerUtils.ts` inferred baseline from max ad price; pipeline had bucket logic only in Python.  
Fix / workaround: Shared thresholds in `config/price_benchmark_thresholds.json`. TypeScript: `src/data/priceBenchmarks.ts` (`computeFeedProductBenchmark`, `computePriceBenchmarkFromWeeklyPrices`). Python: `scripts/weekly_ad_analysis/benchmarks.py` (`compute_benchmark`, `bucket_for_price`). Buckets: all-time low, near all-time low, strong sale, normal sale, weak sale, insufficient history.  
How to verify: `PYTHONPATH=scripts python3 -c "from weekly_ad_analysis.benchmarks import compute_benchmark; print(compute_benchmark('strawberries','canonical','safeway_bay_area',2.5))"`  
Related files: `config/price_benchmark_thresholds.json`, `src/data/priceBenchmarks.ts`, `scripts/weekly_ad_analysis/benchmarks.py`


### Incremental price tracker product add (cached weekly ads)

Date discovered: 2026-07-05  
Context: Adding canonical/tracked items without re-scanning all products or re-extracting historical PDFs.  
What happened: Full `generate_weekly_ad_prices.py` rematched all products × all weeks every build; baseline crawls could overwrite CSVs. Historical offers already live in sibling-repo `split_offer_items.csv`.  
Fix / workaround: Incremental flags on `scripts/generate_weekly_ad_prices.py` (`--product-id`, `--new-only`, `--dry-run`, merge into existing TS). Orchestrator: `scripts/add_tracker_product.py --product-id ID --all`. Baseline seeds support `--product-id` + `--merge-csv`. Costco: `backfill_price_comparisons.py --product-id`. Runbook: `docs/PRICE_TRACKER_ADD_RUNBOOK.md`. Full rematch: `--full-rematch` (default when no incremental flags).  
How to verify: `python3 scripts/generate_weekly_ad_prices.py --product-id grapes --dry-run` shows `extraction=0 (cache only)`; `python3 -m unittest tests.test_generate_weekly_ad_prices_incremental`.  
Related files: `scripts/generate_weekly_ad_prices.py`, `scripts/price_tracker/artifacts.py`, `scripts/add_tracker_product.py`, `docs/PRICE_TRACKER_ADD_RUNBOOK.md`

### Weekly ad weeks 2026-06-24 and 2026-07-01 added to price tracker

Date discovered: 2026-07-05  
Context: Price tracker was missing the last two ad weeks (Jun 24–30 and Jul 1–7) for Safeway and Vons.  
What happened: **2026-07-01** vision extraction already existed in sibling repo (`product_discovery_safeway_7-1/`, `product_discovery_vons_7-1/`) but was not merged into the consolidated `split_offer_items.csv` caches. **2026-06-24** PDFs exist (`safeway 6-24 - 6-30.pdf`, `vons 6-24 - 6-30.pdf`) but had no vision extraction anywhere (image-only PDFs; pypdf returns 0 chars).  
Fix / workaround:
1. Append week rows from `product_discovery_*_7-1/split_offer_items.csv` into sibling-repo `outputs/product_discovery_{safeway,vons}/split_offer_items.csv` (dedupe by `split_item_id`).
2. Add manifest rows in `data/weekly_ads/flyer_manifest_{safeway,vons}.csv` using PDF filenames from `~/Documents/scrolling-the-aisle/inputs/weekly_ads/`.
3. Regenerate: `npm run generate:weekly-ad-prices` (or `--full-rematch`) then `npm run generate:price-tracker-seed`.
4. **6-24 extraction** runs in sibling repo (image-only PDFs; not in scrollingtheaisle-site). Completed 2026-07-05 via cached vision pipeline:
   ```bash
   cd ~/Documents/scrolling-the-aisle
   python3 src/discover_product_candidates.py --input-dir inputs/weekly_ads \
     --manifest inputs/weekly_ads/flyer_manifest_safeway.csv \
     --output-dir outputs/product_discovery_safeway_6-24 --only-file "safeway 6-24"
   python3 src/discover_product_candidates.py --input-dir inputs/weekly_ads \
     --manifest inputs/weekly_ads/flyer_manifest_vons.csv \
     --output-dir outputs/product_discovery_vons_6-24 --only-file "vons 6-24"
   # Merge split_offer_items.csv into outputs/product_discovery_{safeway,vons}/ then rerun generate.
   ```
   Requires `OPENAI_API_KEY` in sibling-repo `.env`. Pipeline may exit 1 on `summary_report.py` bug after writing `split_offer_items.csv` — merge output anyway. Row counts: Safeway 208, Vons 163 for `2026-06-24`.
How to verify: Audit — expect 208 Safeway + 163 Vons rows for `2026-06-24`, 223 + 115 for `2026-07-01`. `grep 2026-07-01 src/data/weeklyAdPrices.generated.ts`. `npm run build:price-tracker` then check chart x-axis on `/staging-price-tracker/`.  
Related files: `data/weekly_ads/flyer_manifest_*.csv`, `~/Documents/scrolling-the-aisle/outputs/product_discovery_*/split_offer_items.csv`, `src/data/weeklyAdPrices.generated.ts`, `src/data/vonsWeeklyAdPrices.generated.ts`, `src/data/familyWeeklyAdPrices.generated.ts`, `supabase/migrations/20260610_price_tracker_seed.sql`, `supabase/migrations/20260615_vons_weekly_observations_seed.sql`


Date discovered: 2026-07-02  
Context: SoCal Vons weekly ad historical benchmarking for existing STA food watchlist + additive category mappings.  
What happened: Need Vons-only historical labels (all-time low, near low, etc.) separate from Costco-first weekly brief workflow.  
Fix / workaround: Run `npm run vons-historical-low-check` (or `python3 scripts/analysis/vons_historical_low_check.py`). Uses `config/vons_historical_low_category_mappings.csv` (additive — does not modify canonicalProducts.ts). Historical rows from `scrolling-the-aisle/outputs/product_discovery_vons*/split_offer_items.csv`. Current week needs vision-extracted split_offer CSV (PDF alone is not enough). July 2026 week input: `data/weekly_ads/2026-07-01/socal_oc/split_offer_items.csv`.  
How to verify: `python3 -m unittest tests.test_vons_historical_low_check -v` then inspect `outputs/vons_2026-07-01_historical_low_candidates.csv`.  
Related files: `scripts/analysis/vons_historical_low_check.py`, `config/vons_historical_low_category_mappings.csv`, `tests/test_vons_historical_low_check.py`


### Supabase migration version must be unique per file

Date discovered: 2026-07-05  
Context: `supabase db push` after adding Costco price comparison seed.  
What happened: Two files shared prefix `20260616` (`20260616_price_comparisons.sql` + `20260616_price_comparisons_seed.sql`). Remote `schema_migrations` already had version `20260616` for the schema migration; push failed with duplicate version.  
Fix / workaround: Give seed its own version (`20260617_price_comparisons_seed.sql`). Schema stays `20260616`. Seed data can also be applied manually: `supabase db query --linked -f supabase/migrations/20260617_price_comparisons_seed.sql` (idempotent upserts). `backfill_price_comparisons.py` writes the `20260617_…` path.  
How to verify: `supabase db push --dry-run` lists only `20260617_price_comparisons_seed.sql` pending; no duplicate-version error.  
Related files: `supabase/migrations/20260616_price_comparisons.sql`, `supabase/migrations/20260617_price_comparisons_seed.sql`, `scripts/backfill_price_comparisons.py`

