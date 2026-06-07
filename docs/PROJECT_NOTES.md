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

## Data Extraction Notes

Weekly ad prices for the staging price tracker:

- Manifest (week → PDF): `data/weekly_ads/flyer_manifest_safeway.csv` (synced from `scrolling-the-aisle/inputs/weekly_ads/`)
- Offer rows: `scrolling-the-aisle/outputs/product_discovery_safeway/split_offer_items.csv`
- Regenerate: `npm run generate:weekly-ad-prices` → `src/data/weeklyAdPrices.generated.ts`

Gotchas: grouped offers split into per-item rows — matchers in `scripts/generate_weekly_ad_prices.py` pick the best split row per canonical item. Multi-buy promos need per-unit normalization (`3 for $5`, `when you buy 3`, etc.). Some tracker items have no ad match yet (e.g. Coke Zero 12pk) or use a close proxy (Fairlife → Premier Protein 4pk).

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

### Price tracker Vite entry must be `src/staging-price-tracker/index.html`, not `staging-price-tracker/index.html`

Date discovered: 2026-06-07  
Context: `npm run build:price-tracker` / deploying June weekly ad data.  
What happened: `staging-price-tracker/index.html` is the **deployed** output (overwritten by `scripts/sync-price-tracker-dist.mjs`). It references pre-built `assets/index-*.js`. Using it as the Vite `rollupOptions.input` rebundles stale JS — source/data changes in `src/` never reach the chart.  
Fix / workaround: Vite input is `src/staging-price-tracker/index.html` (loads `main.tsx`). Sync copies build output into `staging-price-tracker/` for GitHub Pages. Do not put the source HTML under `price-tracker/` — that path is gitignored.  
How to verify: After `npm run build:price-tracker`, `grep 2026-06-03 staging-price-tracker/assets/index-*.js` should match when that week is in the manifest.  
Related files: `vite.config.ts`, `src/staging-price-tracker/index.html`, `scripts/sync-price-tracker-dist.mjs`, `staging-price-tracker/`

Add notes here for useful Cursor prompts, commands, migrations, local testing, and deployment steps.

Living notes rule: `.cursor/rules/project-notes.mdc` — agents should read and update `docs/PROJECT_NOTES.md`.

Playwright setup: `pip install -r scripts/requirements.txt && playwright install chromium`

## Open Questions

Track unresolved questions here.
