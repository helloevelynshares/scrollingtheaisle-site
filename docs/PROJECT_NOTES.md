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
Fix / workaround: Run `python3 scripts/backfill_price_comparisons.py` (override path with `COSTCO_DATA_ROOT`). Maps Safeway → `san-francisco` / `costco_sf`, Vons → `tustin` / `costco_oc`. Writes `supabase/migrations/20260616_price_comparisons_seed.sql` + `src/data/priceComparisons.generated.ts`. Apply schema migration `20260616_price_comparisons.sql` before seed.  
How to verify: Backfill log shows item counts per location; cards show badges like "Via Safeway", "Via Costco", or "Not found at Costco" (scoped to the active grocery tab vs Costco — never cross-compares Safeway vs Vons). Re-run is idempotent (`on conflict` upsert).  
Related files: `scripts/backfill_price_comparisons.py`, `scripts/price_comparison/`, `COSTCO_DATA_ROOT`, `src/staging-price-tracker/ComparisonBadge.tsx`

## Open Questions

Track unresolved questions here.
