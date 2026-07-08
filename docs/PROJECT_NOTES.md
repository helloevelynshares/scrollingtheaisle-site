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
supabase functions deploy admin-store-actions
```

**Important:** `supabase/config.toml` must set `verify_jwt = false` for all three admin functions. If `admin-store-actions` is deployed without it, the Supabase gateway rejects the custom HMAC bearer token (`UNAUTHORIZED_INVALID_JWT_FORMAT`) and `/admin/stores/` sign-in appears to hang or immediately bounce back with a session error after password validation succeeds.

Apply migration: `supabase db push` or run SQL in Supabase dashboard.

### All 66 YAML families need chartMode-based rangeMode (not isDealFamily)

Date discovered: 2026-07-05
Context: Price tracker graphs after YAML migration to 66 tracker families.
What happened: `yamlFamilyProducts.ts` sets `trackerType: "brand_family"` for all 66 families. `isDealFamily()` returns `true` for `brand_family`. `PriceTrendChart.tsx` had `rangeMode = product.chartMode === "range" || isDealFamily(product)`. Because `isDealFamily` was `true` for all YAML families, `rangeMode` was always `true` → `showCostcoOverlay = false` → the Costco line never rendered for any of the 66 new families. Only old `deal_family` products (Ben & Jerry's, Ritz) legitimately need `rangeMode`.
Fix / workaround: Change `PriceTrendChart.tsx` to `rangeMode = product.chartMode === "range"` only. YAML families all have `chartMode: "single"` → rangeMode stays false → three-line chart shows correctly. `deal_family` products explicitly set `chartMode: "range"` via `trackerFamilyUtils.ts` (`members.length > 1 ? "range" : "single"`), so they still get range mode.
How to verify: Open `/staging-price-tracker/` → Doritos/strawberries/etc. charts show baseline reference line + grocery trend line + Costco comparison line. `npm run build:price-tracker`.
Related files: `src/staging-price-tracker/PriceTrendChart.tsx`, `src/data/priceTrackerUtils.ts`, `src/data/yamlFamilyProducts.ts`, `src/data/trackerFamilyUtils.ts`

### Costco-unavailable state: hide all Costco UI (no negative callouts)

Date discovered: 2026-07-07
Context: Price tracker cards/charts when Costco comparison data is missing, not sold, needs review, or unit-mismatched.
What happened: Cards could show contradictory copy — e.g. "Comparison unavailable" or "Not found at Costco" alongside "Costco wins on price", plus "San Francisco Costco pricing" location notes and a chart footnote "Not available at Costco".
Fix / workaround: Central gate `hasMeaningfulCostcoComparison()` in `priceComparisonUtils.ts` — returns true only when `comparisonStatus === "comparable"`, winner is grocery/costco/tie, and Costco price exists. All Costco UI (badge, chart line, takeaway win/loss, expanded Ritz details, location notes) is hidden when false. No explicit "not at Costco" / "comparison unavailable" messaging — absence of Costco UI is the signal.
How to verify: Open `/staging-price-tracker/` → Coke Zero / Tillamook / Mission chips → no Costco badge, no blue chart line, no Costco takeaway. Doritos Safeway → still shows Via Costco badge + chart line. `npm run build:price-tracker`.
Related files: `src/data/priceComparisonUtils.ts`, `src/data/priceTrackerUtils.ts`, `src/staging-price-tracker/PriceTrendChart.tsx`, `src/data/trackerFamilyUtils.ts`


Date discovered: 2026-07-05
Context: Costco line in price tracker charts after YAML migration.
What happened: (1) Costco warehouse data only covers Jun–Jul 2026; earlier grocery weeks had `costcoPrice: null`, making the line appear as a short right-side stub. (2) For produce items (strawberries, grapes, avocados), Costco sells multi-lb packages but grocery tracks per-lb; using raw `price` made the comparison off. (3) 49 new YAML families without Costco data got `costcoComparable: true` (from YAML) but no history → `isCostcoUnavailableOnChart()` incorrectly showed "Not available at Costco" for all of them.
Fix / workaround:
1. `buildUnifiedChartRows`: after mapping observations to weeks, find `flatCostcoPrice` (last known Costco price) and fill any week without an observation with it → continuous flat line.
2. `getCostcoChartPricePoints`: use `point.unitPrice` instead of `point.price` when `groceryUnitType` is "lb" or "each" (produce items) and `unitPrice < price` — keeps y-axis in the right per-unit scale.
3. `isCostcoUnavailableOnChart`: only return `true` when `comparison.comparisonStatus === "not_sold_at_costco"` or `comparison.winner === "grocery_only"`. Returns `false` when no comparison data (new families without metadata).
How to verify: Strawberries chart shows Costco line flat at ~$2/lb (per-lb normalized) across all 9 weeks. Doritos chart shows Costco $6.99 package line flat. No "Not available at Costco" message for families like `lays_potato_chips_regular`. `npm run build:price-tracker`.
Related files: `src/data/priceTrackerUtils.ts`

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

### Homepage store vote module (compact chips + Supabase)

Date discovered: 2026-07-07
Context: Homepage hero store suggestion UI — was 4 layout variants saving to localStorage only.
What happened: Needed a single compact chips layout wired to the same moderated vote pattern as tracker item voting (`tracker_vote_items`).
Fix / workaround: New table `store_vote_items` + RPCs `vote_on_store(uuid)` and `submit_store_suggestion(text, text)` in `supabase/migrations/20260707_store_vote_items.sql`. Homepage (`index.html`, `homepage.js`) uses Supabase JS CDN; chips vote on approved seed stores (Trader Joe's, Whole Foods, Sprouts, Kroger); custom form requires store name, optional city → `pending` for review. Client dedupes via `localStorage` key `sta_store_votes`. **Admin UI** at `/admin/stores/` (password via `validate-admin` + `admin-store-actions` Edge Function) — approve/reject/merge pending rows before they appear on the homepage voting list.
How to verify: Apply migration (`supabase db push` or run SQL in dashboard). Deploy `admin-store-actions` with `verify_jwt = false` (see `supabase/config.toml`). Commit `admin/stores/` build output and push for GitHub Pages. `npm run preview:homepage` → http://127.0.0.1:8000/ → click a chip → success toast; custom store → moderation message. Approve in `/admin/stores/` → store appears for public voting. Check `store_vote_items.vote_count` increments.
Related files: `supabase/migrations/20260707_store_vote_items.sql`, `supabase/functions/admin-store-actions/`, `src/admin/stores/`, `index.html`, `homepage.js`, `styles.css`

### Homepage tracker link copy (variant 3 chosen)

Date discovered: 2026-07-07
Context: Homepage hero tracker CTAs felt too formal ("price trackers"); user explored 5 casual copy options via on-page switcher.
What happened: Static "Price trackers" label + "Safeway price tracker" buttons did not explain live tracking in a playful tone. User chose **variant 3** with button text tweak ("Scroll through the … aisle").
Fix / workaround: Final copy is static in `index.html` hero tracker card — intro: "Hop into the live aisles we've got going:"; buttons: "Scroll through the Safeway aisle" / "Scroll through the Vons aisle". Exploration switcher (`TRACKER_COPY_VARIANTS`, `?trackerCopyVariant=`, `sta_tracker_copy_variant`) removed for production. Store vote copy: "Where should we track prices next?" + lead about voting for where to add tracking.
How to verify: `npm run preview:homepage` → http://127.0.0.1:8000/ → hero shows variant 3 copy; no Copy 1–5 switcher.
Related files: `index.html`, `homepage.js`, `styles.css` (`.hub-hero-trackers-intro`)

### Homepage unstyled + old hero copy (stale cache / dead preview server)

Date discovered: 2026-07-07  
Context: Safari preview at http://127.0.0.1:8000/ showed Times New Roman, plain blue links, old "Safeway price tracker" / "Vons price tracker" buttons, no store-vote module.  
What happened: Two issues stacked: (1) **stale HTML** — browser cached `index.html` from commit `222a841` (before store-vote + variant-3 copy in `a6a8aa7`); (2) **CSS not applied** — preview server not running (`curl` → connection refused) and/or browser cached a failed `styles.css` request from an earlier deploy window. Commit `5e7a525` fixed this with `/styles.css?v=hub1` but `fab8fdd` reverted to relative paths. `styles.css` itself has no syntax errors (3565 lines, braces balanced). Production https://scrollingtheaisle.com/ serves current HTML + CSS 200.  
Fix / workaround: Re-applied root-absolute cache-busted asset paths: `/styles.css?v=hub2`, `/homepage.js?v=hub2`, `/data/homepage-preview.generated.json`. Run **`npm run preview:homepage`** in your own terminal (repo root) and hard-refresh (Cmd+Shift+R). Do not open `index.html` via `file://`.  
How to verify: `curl -s http://127.0.0.1:8000/ | grep hub2` shows cache-busted links; page shows styled hero, "Scroll through the … aisle" CTAs, store-vote chips.  
Related files: `index.html`, `homepage.js`, `styles.css`, `package.json` (`preview:homepage`)


Date discovered: 2026-07-06  
Context: Previewing repo root `index.html` in Safari at http://127.0.0.1:8000/.  
What happened: Agent-started `python3 -m http.server 8000` in background shells dies when the agent/subagent session ends, so Safari shows "can't connect" even though it worked briefly.  
Fix / workaround: Run **`npm run preview:homepage`** in your own terminal tab (repo root) and leave it open. Optional detached server: `nohup python3 -m http.server 8000 --bind 127.0.0.1 > /tmp/scrolling-homepage-preview.log 2>&1 &` — PID in `/tmp/scrolling-homepage-preview.pid`. Stop: `kill $(cat /tmp/scrolling-homepage-preview.pid)` or Ctrl+C in the terminal running npm.  
How to verify: `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/` → `200`.  
Related files: `package.json` (`preview:homepage`), root `index.html`, `npm run generate:homepage-preview`

### Generate → Validate → Fix workflow for weekly ad prices

Date discovered: 2026-07-06  
Context: Weekly ad price generation pipeline after YAML tracker families migration.  
What happened: The generator can produce false matches where an offer is matched to the wrong tracker family (e.g. "Lindt Gourmet Truffles" matching `ruffles_regular_bags`, "SToK Cold Brew Coffee" matching `haagen_dazs_pints`, "Skippy Peanut Butter" matching `butter_16oz`, "Mango Habanero Chicken" matching `mangoes_each`, "Chex Mix" matching `general_mills_cereal_regular`).  
Fix / workaround: Run the standard workflow after any YAML change or new week's data:

```bash
# 1. Edit data/canonical_tracker_families.yaml (add/fix include or keep_separate_from)
# 2. Regenerate (full or targeted)
PYTHONPATH=scripts /usr/bin/python3 scripts/generate_weekly_ad_prices.py --product-id <id>
# or full rematch:
PYTHONPATH=scripts /usr/bin/python3 scripts/generate_weekly_ad_prices.py
# 3. Validate — catches keyword false matches and price outliers
PYTHONPATH=scripts /usr/bin/python3 scripts/validate_weekly_ad_prices.py
# 4. Review data/review/weekly_price_sanity_{date}.csv
#    - [keyword/FAIL] + high confidence = definite false match → fix YAML keep_separate_from, re-run step 2
#    - [keyword/WARN] = medium confidence mismatch → investigate
#    - [outlier] = price swing → inspect offerText; often legitimate seasonal/promotional variation
# 5. Run tests
PYTHONPATH=scripts /usr/bin/python3 -m unittest tests.test_validate_weekly_ad_prices tests.test_canonical_families -v
```

Output columns: `family_id, store, week, price, offerText, confidence, check_failed, reason`  
Checks: (1) keyword sanity (offerText must match at least one include token; must not match keep_separate_from), (2) price outlier (>2× median or >3× / <0.5× prior week), (3) per-lb plausibility ($0.25–$50/lb).  
False matches fixed 2026-07-06: `haagen_dazs_pints` ("coffee"/"vanilla" → too generic; removed standalone flavor words from include), `butter_16oz` (peanut butter added to keep_separate_from), `general_mills_cereal_regular` ("Chex Mix", "Rold Gold" added to keep_separate_from; "Chex" → "Chex cereal" in include), `mangoes_each` ("habanero", "chicken" added to keep_separate_from), `nature_valley_bars` (already had "protein bars" in keep_separate_from; stale TS re-generated to apply exclusion), `ruffles_regular_bags` (Lindt/LINDOR/Gourmet Truffles/chocolate truffles added to keep_separate_from as preventive measure).  
How to verify: 0 `[keyword/FAIL]` rows in sanity CSV. `PYTHONPATH=scripts /usr/bin/python3 -m unittest tests.test_validate_weekly_ad_prices -v` → 32 tests OK.  
Related files: `scripts/validate_weekly_ad_prices.py`, `data/canonical_tracker_families.yaml`, `data/review/weekly_price_sanity_{date}.csv`, `tests/test_validate_weekly_ad_prices.py`

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


### YAML tracker families migration (66 families)

Date discovered: 2026-07-05  
Context: Migrate from ~20 hardcoded `canonical_products` to `data/canonical_tracker_families.yaml`.  
What happened: Tracker cards, weekly-ad matchers, homepage sections, and Popular this week now read from YAML via `scripts/generate_canonical_families.py` → `src/data/canonicalTrackerFamilies.generated.ts`. Weekly ad prices keyed by family id (`doritos_5_13oz`, etc.); legacy canonical rows merged via `LEGACY_CANONICAL_TO_FAMILY` in `scripts/price_tracker/canonical_families.py`.  
Fix / workaround: Edit YAML → `npm run generate:canonical-families` → `npm run generate:weekly-ad-prices` → `npm run build:price-tracker`. Runbook: `docs/YAML_TRACKER_MIGRATION_RUNBOOK.md`. Safeway/Vons UI uses static `yamlFamilyProducts.ts` (no Supabase required). Costco/backfill still maps via legacy canonical ids until extended.  
How to verify: `PYTHONPATH=scripts python3 -m unittest tests.test_canonical_families tests.test_normalization tests.test_ui_copy -v`; open `/staging-price-tracker/` — five section chips, search, Popular this week.  
Related files: `data/canonical_tracker_families.yaml`, `data/popular_this_week.yaml`, `scripts/price_tracker/`, `src/data/yamlFamilyProducts.ts`, `src/staging-price-tracker/SectionedTrackerList.tsx`



Date discovered: 2026-07-05  
Context: `supabase db push` after adding Costco price comparison seed.  
What happened: Two files shared prefix `20260616` (`20260616_price_comparisons.sql` + `20260616_price_comparisons_seed.sql`). Remote `schema_migrations` already had version `20260616` for the schema migration; push failed with duplicate version.  
Fix / workaround: Give seed its own version (`20260617_price_comparisons_seed.sql`). Schema stays `20260616`. Seed data can also be applied manually: `supabase db query --linked -f supabase/migrations/20260617_price_comparisons_seed.sql` (idempotent upserts). `backfill_price_comparisons.py` writes the `20260617_…` path.  
How to verify: `supabase db push --dry-run` lists only `20260617_price_comparisons_seed.sql` pending; no duplicate-version error.  
Related files: `supabase/migrations/20260616_price_comparisons.sql`, `supabase/migrations/20260617_price_comparisons_seed.sql`, `scripts/backfill_price_comparisons.py`


### Weekly ad preview workflow (upcoming ad before start date)

Date discovered: 2026-07-07
Context: First time loading a weekly ad before its effective start date (Jul 8–14 ad imported on Jul 7).
What happened: Price tracker had no concept of preview vs active ad weeks; UI said "this week" for prices that were not yet in stores.
Fix / workaround:
1. **Import orchestrator:** `python3 scripts/import_weekly_ad.py --week-start YYYY-MM-DD --week-end YYYY-MM-DD --safeway-pdf "safeway …pdf" --vons-pdf "vons …pdf"` — updates manifests (site + sibling repo), runs vision extraction (`discover_product_candidates.py` with `--only-file` date token e.g. `7-8`), merges banner-filtered rows into sibling `split_offer_items.csv`, regenerates TS. Use `--skip-extraction` when CSV already exists; `--verify-only` to audit counts.
2. **Preview detection:** `today < week_start` → preview (date-based, no manual flag). Python: `scripts/price_tracker/weekly_ad_preview.py`. TypeScript: `src/data/weeklyAdPreview.ts` + `isPreviewWeek` on each `WeeklyPrice` in `yamlFamilyProducts.ts`.
3. **UI:** `WeeklyAdPreviewBanner` below feed tabs; card copy uses "Preview: $X starting tomorrow" instead of "this week"; status pills "Preview sale" / "Preview promo".
4. **Safeguards:** `generate_weekly_ad_prices.py` validates canonical product IDs unchanged (66 families) before/after; logs matched/unmatched per feed.
Weekly command (Jul 8–14 example):
```bash
python3 scripts/import_weekly_ad.py \
  --week-start 2026-07-08 --week-end 2026-07-14 \
  --safeway-pdf "safeway 7-8 - 7-14.pdf" \
  --vons-pdf "vons 7-8 - 7-14.pdf"
npm run verify:weekly-ad
npm run build:price-tracker
```
Verify: `python3 scripts/import_weekly_ad.py --verify-only` → 66 tracked products, PREVIEW status when `--as-of` before week start. `PYTHONPATH=scripts python3 -m unittest tests.test_weekly_ad_preview -v`.
Related files: `scripts/import_weekly_ad.py`, `scripts/price_tracker/weekly_ad_preview.py`, `src/data/weeklyAdPreview.ts`, `src/staging-price-tracker/WeeklyAdPreviewBanner.tsx`, `data/weekly_ads/flyer_manifest_*.csv`


Date discovered: 2026-07-05  
Context: HTTP/curl pgmsearch via `seed_safeway_baseline.py`; prior `.env` used SF Jackson St store **4601 / 94111 / pickup** with Chrome UA + logged-in cookie — requests failed or mismatched session.  
What happened: Working DevTools capture used **storeid=3132**, **zipcode=94611**, **channel=instore**, empty **visitorId**, Safari UA, guest cookie (`userType` **G**), no `sec-ch-ua` headers.  
Fix / workaround: Refresh `SAFEWAY_COOKIE` from that capture; set `SAFEWAY_STORE_ID=3132`, `SAFEWAY_ZIPCODE=94611`, `SAFEWAY_CHANNEL=instore`, Safari `SAFEWAY_USER_AGENT`, clear `SAFEWAY_VISITOR_ID` / `SAFEWAY_UUID`, comment out `SAFEWAY_SEC_CH_UA*`. Code defaults in `safeway_config.py` remain SF 4601/94111/pickup if env vars unset.  
How to verify: `.venv/bin/python scripts/seed_safeway_baseline.py --query "goldfish cheddar cracker" --timeout 30 -v` → `200 success`, candidates CSV populated (e.g. Goldfish Cheddar 10 Oz **$4.99**).  
Related files: `scripts/.env`, `scripts/safeway_config.py`, `scripts/safeway_client.py`, `scripts/seed_safeway_baseline.py`

### Kettle Brand Safeway 2026-07-01: vision pipeline missed $5 Friday tile (fixed)

Date discovered: 2026-07-06  
Context: User reported "Kettle Brand potato chips 3 for $5" was on the $5 Friday page of the Safeway 7/1-7/7 ad, "under the strawberries and half pie." Previous investigation incorrectly concluded it was not there.  
What happened: The vision extraction pipeline captured 31 of 32 offer tiles on page 4 of the Safeway ad. The Kettle Brand Potato Chips tile was in a distinct layout row (approx. y=0.87-0.93) between the "Half Pie row" (y=0.81-0.87) and the "AriZona Tea row" (y=0.89-0.95). The extraction bounding-box detection skipped this row entirely — no raw_offer_card was created for it. Visual inspection of the PDF (rendered with PyMuPDF) confirmed the tile clearly shows: Kettle Brand Potato Chips, 5–8.5 oz., Selected varieties., Member Price $1.67 ea., Limit 3 items., **3 for $5 Member Price** (Friday July 3rd, $5 Friday block).  
Fix / workaround:
1. Manually added the missing row to both `data/weekly_ads/2026-07-01/bay_area/split_offer_items.csv` (local) and `~/Documents/scrolling-the-aisle/outputs/product_discovery_safeway/split_offer_items.csv` (sibling repo consolidated) with `advertised_price=5.0`, `price_basis=multi_buy`, `promo_text="3 for $5 Friday July 3rd"`, `availability_type_guess=friday_only`.
2. Ran `python3 scripts/generate_weekly_ad_prices.py --product-id kettle_brand_chips --feed safeway`.
3. Result: `weeklyAdPrices.generated.ts` now shows `kettle_brand_chips["2026-07-01"]["price"] = 1.67` (correctly normalized: $5 ÷ 3 = $1.67 ea via `_multi_buy_unit_price`).  
How to verify: `grep '"2026-07-01"' src/data/weeklyAdPrices.generated.ts` near `kettle_brand_chips` → should show `"price": 1.67`. Open `/staging-price-tracker/` Safeway tab → Kettle Brand chart → 2026-07-01 should dip to $1.67.  
Related files: `data/weekly_ads/2026-07-01/bay_area/split_offer_items.csv`, `~/Documents/scrolling-the-aisle/outputs/product_discovery_safeway/split_offer_items.csv`, `src/data/weeklyAdPrices.generated.ts`

### Kettle Brand Vons 2026-07-01 showed wrong $11.99 (stale pre-YAML match)

Date discovered: 2026-07-06
Context: Price tracker chart for `kettle_brand_chips` (Vons tab) showed $11.99 for the 2026-07-01 week.
What happened: Three separate issues combined:
1. **Stale match from pre-YAML migration**: The old `ProductMatcher` (before YAML families) matched "Kettle Brand Chips Party Size 11.25-13 oz." from a multi-item "Single Price Up To: $11.99" block on page 2 of the Vons 7-1 ad. After the YAML migration, the new patterns (requiring "Kettle Brand Sea Salt", "Kettle Brand Jalapeño", etc.) correctly produce 0 matches for that week — but the stale $11.99 remained because the incremental merge didn't overwrite it. The TS was regenerated from an old run.
2. **Wrong product size**: `kettle_brand_chips` tracks 6.5–8.5 oz bags; the Party Size is 11.25–13 oz — a completely different SKU at a different price point.
3. **Ceiling price, not a promotional price**: "Single Price Up To: $11.99" is the MSRP cap for a broad multi-product block (includes Tide, Totino's, sunscreen, etc.) — not a sale price.
4. **No "$5 Friday July 3rd" deal for Kettle Brand in either chain**: The user clarified the $3.45 deal was **Safeway-specific**, not Vons. Exhaustive search of BOTH Safeway bay_area and Vons socal_oc 2026-07-01 split_offer_items.csv AND raw_offer_cards.csv (all pages, all offers) found: NO Kettle Brand at $3.45 anywhere. The $5 Friday blocks in Safeway 7-1 cover: Pork Spareribs, Sushi, Salmon, Bacon, Caspers Hot Dogs, Strawberries, Peaches/Nectarines/Plums, Red Potatoes, Kinder's BBQ Sauce, Entenmann's Donuts, Popsicles, Sparkling Water/Tea, On the Rocks Cocktails, flowers — NOT chips. "Frito-Lay Lay's, Kettle Cooked, Sun Chips, Ruffles 4.75-8 oz. $1.99 ea" appears on page 3 of the Safeway 7-1 ad — but this is "Lay's Kettle Cooked" (a Frito-Lay variety), not the "Kettle Brand" brand (Kettle Foods/Cape Cod). The $3.45 price appears NOWHERE in any Safeway 7-1 extracted data; the only "3.45" hit is "14.76-23.45 oz" (a size range for Red Baron Pizza). The deal either appeared in-store only (not in the printed/digital weekly ad), or was a digital coupon not captured in the vision pipeline.
Fix / workaround:
1. Added "Kettle Brand Chips" and "Kettle Brand potato chips" to `include` in the YAML (so deals that say just "Kettle Brand Chips" without a specific flavor are matched).
2. Added "Kettle Brand Chips Party Size" and "Party Size" to `keep_separate_from` (excludes the large-format SKU and prevents ceiling/MSRP prices from contaminating the chart).
3. Ran `python3 scripts/generate_weekly_ad_prices.py --product-id kettle_brand_chips --feed vons` — 2026-07-01 now correctly shows null; 2026-05-06 also fixed (was wrongly showing $2.99 from "Lay's Kettle Cooked").
Design limitation: The chart plots one price per week. "Friday-only" intra-week dips (e.g., a $3.45 deal only on July 3rd) CANNOT be shown as a single-day dip — the chart would need daily granularity. Even if the $3.45 data existed, it would need `availability_type_guess: friday_only` in split_offer_items and a chart design change to show it as a Friday-only annotation instead of a full-week price.
How to verify: `grep '"2026-07-01"' src/data/vonsWeeklyAdPrices.generated.ts | head -5` — kettle_brand_chips entry should have `"price": null`. Open chart on `/staging-price-tracker/` Vons tab → kettle_brand_chips — should show baseline line (not a spike to $11.99).
Related files: `data/canonical_tracker_families.yaml` (`kettle_brand_chips`), `src/data/vonsWeeklyAdPrices.generated.ts`, `scripts/generate_weekly_ad_prices.py`, `data/weekly_ads/2026-07-01/socal_oc/split_offer_items.csv`

### B2G3F/BOGO deals need reference price in split_offer_items to normalize

Date discovered: 2026-07-06
Context: Doritos on Safeway 7/1 week reported "showing usual price instead of promotional effective price."
What happened: The Safeway 7/1 ad has a "BUY 2, GET 3 FREE Mix & MATCH" deal for "Lay's, Tostitos, Doritos or Simply 4.5–13 oz." with reference price $5.49 ea. The vision pipeline captured this deal in `raw_offer_cards.csv` (page 1, offer 3, `verified_*` fields) but it was NOT promoted to `split_offer_items.csv` because the crop-tile mismatch tagged it as an annotation on the adjacent Sweet Corn row. Two issues combined: (1) missing data row, and (2) `normalization.py` had no `buy_x_get_y` branch — `base_normalize_unit_price` only handled `multi_buy`, so any B2G3F/BOGO row with a price would have returned the raw reference price (e.g. $5.49) instead of the effective per-unit cost (2/5 × $5.49 = $2.20).
Fix / workaround:
1. Added `_buy_x_get_y_unit_price()` in `scripts/price_tracker/normalization.py` — parses "buy N get M free" from promo_text and computes `N/(N+M) × price`. Also handles bare "bogo" keyword.
2. Updated `base_normalize_unit_price()` to apply this logic when `price_basis` is `bogo` or `buy_x_get_y`.
3. Added the 3 missing split rows (Lay's, Tostitos, Doritos) with `advertised_price=5.49`, `price_basis=bogo`, `promo_text="BUY 2, GET 3 FREE Mix & MATCH"` to both `data/weekly_ads/2026-07-01/bay_area/split_offer_items.csv` (local copy) and `~/Documents/scrolling-the-aisle/outputs/product_discovery_safeway/split_offer_items.csv` (sibling repo consolidated, which is what `generate_weekly_ad_prices.py` reads).
4. Regenerated `src/data/weeklyAdPrices.generated.ts` with `--product-ids doritos_5_13oz,lays_potato_chips_regular,tostitos_tortilla_chips`.
Before/after for Safeway 7/1: `doritos_5_13oz` was `price: null` → now `price: 2.2` (confidence: high). Same for Lay's and Tostitos.
Vons 7/1: Vons also has a B2G3F for Lay's/Kettle/Poppables but with NO reference price in the vision extraction → still null. Vons Doritos 7/1 shows $2.50 (from "2 for $5" deal) which is correct and unaffected. Other historical B2G/BOGO rows (6/17 Lay's BOGO, 6/10 Tostitos BOGO) also have no price — still null (pre-existing data limitation).
How to verify: `python3 -c "import json; ..."` or check `src/data/weeklyAdPrices.generated.ts` — `doritos_5_13oz["2026-07-01"]["price"]` should be `2.2`. All tests pass: `PYTHONPATH=scripts python3 -m unittest tests.test_normalization -v`.
Related files: `scripts/price_tracker/normalization.py`, `data/weekly_ads/2026-07-01/bay_area/split_offer_items.csv`, `~/Documents/scrolling-the-aisle/outputs/product_discovery_safeway/split_offer_items.csv`, `src/data/weeklyAdPrices.generated.ts`

### Card-level ATL hint + Option A tooltip (D1 revised)

Date discovered: 2026-07-06  
Context: Price tracker product cards after Option A + D1 UX revision.  
What happened: Prior agent added D1 (benchmark bucket in tooltip) + Option A (promoNote/friday_only in tooltip). User revised D1: do NOT show benchmark bucket label in tooltip. Instead, surface all-time low on the card upfront as a subtle reference, and keep Option A (friday_only + promoNote) in tooltip.  
Fix / workaround:
1. **Card ATL hint** (`FamilyDealCard.tsx`): `computeFeedProductBenchmark(product)` runs per-card. If `observationCount >= 2` and `allTimeLowUnitPrice != null`, renders `.family-deal-card__atl-hint` below the price block: "All-time low: $X.XX" (gray, subtle). When current price IS the all-time low (`benchmarkBucket === "all-time low"`), the hint becomes "All-time low $X.XX" in green (`.family-deal-card__atl-hint--match`).
2. **Tooltip Option A** (`PriceTrendChart.tsx`): On grocery row hover, if `weeklyEntry.availabilityType === "friday_only"`, tooltip shows `promoNote + " (Fri Jul 3 only)"` (computed via `getFridayOfWeek`). For non-friday promo rows, shows `promoNote` as italic amber sub-line (`.price-tracker-chart-tooltip-promo`).
3. **Removed D1**: No benchmark bucket label appended to tooltip series label.
4. **UnifiedChartRow** now carries `availabilityType` and `promoNote` (forwarded from `WeeklyPrice` via `buildUnifiedChartRows`).
Kettle Brand Safeway example: Card shows "All-time low $1.67" in green (2026-07-01 is the lowest tracked at $1.67 = 3 for $5). Tooltip for that dot shows "3 for $5 Friday July 3rd (Fri Jul 3 only)".  
How to verify: `npm run build:price-tracker` → open `/staging-price-tracker/` → Safeway tab → Kettle Brand card → price block shows "All-time low $1.67" in green. Hover the 7/1 dip → tooltip shows promo note with Friday annotation. All 66 families with ≥2 observations show the ATL hint.  
Related files: `src/staging-price-tracker/FamilyDealCard.tsx`, `src/staging-price-tracker/PriceTrendChart.tsx`, `src/data/priceTrackerUtils.ts` (`UnifiedChartRow`, `buildUnifiedChartRows`), `styles.css` (`.family-deal-card__atl-hint`, `.price-tracker-chart-tooltip-promo`)

### ATL chip on product card (not tooltip); Option A tooltip unchanged

Date discovered: 2026-07-06  
Context: Staging price tracker (`/staging-price-tracker/`) benchmark display after Option A + D1 work.  
What happened: D1 benchmark bucket label was added to `PriceChartTooltip` in `PriceTrendChart.tsx` using `computeFeedProductBenchmark` without importing it (runtime ReferenceError on hover). User refinement: ATL should appear subtly on the **card**, not in the hover tooltip.  
Fix / workaround: Removed D1 tooltip logic from `PriceTrendChart.tsx`. Card-level ATL display lives in `FamilyDealCard.tsx`: `computeFeedProductBenchmark(product)` → `allTimeLowUnitPrice` + `benchmarkBucket`. Shows `.family-deal-card__atl-hint` (grey, subtle) when `observationCount >= 2`; adds `--match` modifier (green bold) when `isAtl`. Option A tooltip (friday_only + promoNote on hover) is unaffected. Kettle Brand Safeway 2026-07-01 card shows "All-time low $1.67" (green).  
How to verify: Open `/staging-price-tracker/` → Kettle Brand Safeway card → "All-time low $1.67" shown in green below sale label (no ATL text in tooltip). `npm run build:price-tracker` passes.  
Related files: `src/staging-price-tracker/FamilyDealCard.tsx`, `src/staging-price-tracker/PriceTrendChart.tsx`, `src/data/priceBenchmarks.ts`, `styles.css` (`.family-deal-card__atl-hint`, `.family-deal-card__atl-hint--match`, `.family-deal-card__atl-price`)

### friday_only tooltip: promoNote was silently dropped (yamlFamilyProducts.ts fix)

Date discovered: 2026-07-06
Context: Kettle Brand Chips hover tooltip on `/staging-price-tracker/` Safeway tab showed only "Jul 1" — no promo note, no Friday annotation, even after Option A was implemented in `PriceTrendChart.tsx`.
What happened: `effectiveWeeklyPrice()` in `yamlFamilyProducts.ts` (the path for all 66 YAML families) did NOT forward `availabilityType` or `promoNote` from the generated entry. So `weeklyEntry?.promoNote` was always `undefined` in the tooltip — `promoLine` never rendered. The `priceTrackerFallback.ts` version already forwarded these fields; only the YAML path was missing them.
Fix / workaround:
1. Added `availabilityType: entry?.availabilityType ?? undefined` and `promoNote: entry?.promoNote ?? undefined` to the returned object in `effectiveWeeklyPrice()` in `yamlFamilyProducts.ts`.
2. Improved tooltip UX for `friday_only` deals in `PriceTrendChart.tsx`:
   - Date header: shows week range "Jul 1–7" (new `formatWeekRangeLabel()` helper) instead of just "Jul 1".
   - Series label: shows "Safeway $5 Friday" instead of "Safeway weekly ad".
   - Promo line: shows `"${promoNote} · Fri Jul 3 only"` (computed via existing `getFridayOfWeek`).
   - Fallback (no promoNote): shows "Fri Jul 3 only · not valid all week".
   - Generic non-friday promos: still show just `promoNote` in amber italic.
3. CSS: added `.price-tracker-chart-tooltip--limited` (amber left border) and `.price-tracker-chart-tooltip-promo--limited` (amber pill badge, non-italic, bold) for `friday_only` rows.
Kettle Brand Safeway example tooltip for 2026-07-01:
- Date: "Jul 1–7"
- Series: "Safeway $5 Friday"
- Price: "$1.67"
- Promo badge: "3 for $5 Friday July 3rd · Fri Jul 3 only"
How to verify: `npm run build:price-tracker` → hover Kettle Brand Safeway chart → Jul 1 dot → tooltip shows week range + Friday annotation + amber promo badge.
Related files: `src/data/yamlFamilyProducts.ts` (`effectiveWeeklyPrice`), `src/staging-price-tracker/PriceTrendChart.tsx` (`formatWeekRangeLabel`, `PriceChartTooltip`, `isLimitedDay`), `styles.css` (`.price-tracker-chart-tooltip--limited`, `.price-tracker-chart-tooltip-promo--limited`)

### Ruffles/Truffles false match: phrase_to_pattern missing word boundaries (fixed 2026-07-06)

Date discovered: 2026-07-06  
Context: User reported May 6 pricing for Ruffles looked wrong on the price tracker chart (Safeway tab).  
What happened: `phrase_to_pattern("Ruffles")` in `canonical_families.py` generated the pattern `ruffles` with no word boundaries. `re.search("ruffles", "lindt gourmet truffles select varieties")` matched because "ruffles" is a substring of "truffles". The matcher therefore returned Lindt Chocolate Truffles prices as Ruffles chip prices:
- `2026-05-06` Safeway: `price: 11.99` ("Lindt Gourmet Truffles Select varieties") — wrong
- `2026-03-25` Safeway: `price: 5.99` ("Spring Lindt Truffles select varieties") — wrong
The real Ruffles deals in those weeks either had no price data (2026-03-25 BUY 2 GET 2 FREE with no reference price) or no deal at all (2026-05-06). Vons 2026-05-06 `$2.99` was legitimately correct (offerText literally says "Ruffles", Pick 4 Mix or Match).  
Fix / workaround: Changed `phrase_to_pattern()` condition from `if len(text) <= 4 and text.isalpha()` to `if not re.search(r"\d", text)` — adds `\b...\b` word boundaries to ALL text-only patterns (no digits). Patterns with digits (size ranges like "5–13 oz") are unaffected. Regenerated `weeklyAdPrices.generated.ts` for `ruffles_regular_bags` — both bad weeks corrected to `null`.  
How to verify: `PYTHONPATH=scripts python3 -m unittest tests.test_normalization tests.test_canonical_families -v` (22 tests pass). Check `grep '"2026-05-06"' src/data/weeklyAdPrices.generated.ts` near `ruffles_regular_bags` → `"price": null`. Vons same week shows `"price": 2.99` (untouched).  
Related files: `scripts/price_tracker/canonical_families.py` (`phrase_to_pattern`), `src/data/weeklyAdPrices.generated.ts`

### Per-lb baseline stores package price not unit price (fixed 2026-07-06)

Date discovered: 2026-07-06
Context: Safeway and Vons baselines for per-lb tracker families (ribeye, tri-tip, chicken breast, chicken thighs, cherries, grapes) showed absurdly high values on the chart baseline reference line.
What happened: The seed pipeline (`seed_safeway_baseline.py`, `seed_vons_baseline_playwright.py`) stores the first-matched product's listed price. For per-lb families it retrieved a pre-packaged item (e.g. "USDA Choice Bone In Beef Rib Steak Mega Pack - 3.5 Lb" at $45.47) and stored the total package price instead of the per-lb rate ($12.99/lb). The chart baseline then showed $45.47 instead of $12.99, making every ad price look like a massive deal.
Fix / workaround:
1. **Option A** (immediate): Manually corrected the 6 affected Safeway entries in `src/data/priceTrackerFallback.ts` (SAFEWAY_BASELINES) and 6 Vons entries in `src/data/vonsBaseline.generated.ts` by dividing package price by package weight.
   - Safeway: ribeye 45.47→12.99 (/3.5lb), tri_tip 47.47→18.99 (/2.5lb), chicken_breast 20.23→8.99 (/2.25lb), chicken_thigh 8.97→2.99 (/3lb), cherries 10.48→5.99 (/1.75lb), grapes 9.98→4.99 (/2lb)
   - Vons: ribeye 23.97→7.99 (/3lb), tri_tip 17.47→4.99 (/3.5lb), chicken_breast 10.47→2.99 (/3.5lb), chicken_thigh 8.97→2.99 (/3lb), cherries 10.48→5.99 (/1.75lb), grapes 7.98→3.99 (/2lb)
2. **Option B** (pipeline): Added `scripts/price_tracker/baseline_per_lb.py` with `normalize_baseline_price(canonical_id, product_name, price)` — checks if the YAML family has `size_format_subtitle: per lb`, extracts weight from product name (e.g. "3.5 Lb"), divides. Wired into `generate_safeway_feed_matches.py` and `generate_vons_feed_matches.py` so future re-crawls auto-normalize.
How to verify: Safeway tab → Ribeye chart baseline ~$12.99; Vons tab → Ribeye chart baseline ~$7.99. `npm run build:price-tracker`.
Related files: `src/data/priceTrackerFallback.ts` (SAFEWAY_BASELINES), `src/data/vonsBaseline.generated.ts`, `scripts/price_tracker/baseline_per_lb.py`, `scripts/generate_safeway_feed_matches.py`, `scripts/generate_vons_feed_matches.py`

### Safeway/Vons baselines for per-lb products were stored as total package price (not per-lb)

Date discovered: 2026-07-06
Context: Safeway and Vons baseline prices in `priceTrackerFallback.ts` and `vonsBaseline.generated.ts` for per-lb tracker families (ribeye, tri-tip, chicken, cherries, grapes).
What happened: `generate_safeway_feed_matches.py` and `generate_vons_feed_matches.py` stored the raw pgmsearch package price as the baseline. For per-lb families (YAML: `size_format_subtitle: per lb`), this meant the total package price was used as the chart reference line. Example: "USDA Choice Bone In Beef Rib Steak Mega Pack - 3.5 Lb" → pgmsearch price $45.47 stored as baseline, but chart scale is per-lb; correct baseline is $45.47 / 3.5 = $12.99/lb. Weekly ad prices ($7.99, $9.99/lb) were already correct, so the chart reference line was 4-5x above the sale prices — visually broken.
**Affected products (Safeway):** ribeye_steak (45.47→12.99), cherries_per_lb (10.48→5.99), chicken_breast_per_lb (20.23→8.99), chicken_thigh_per_lb (8.97→2.99), tri_tip_roast (47.47→18.99), grapes (9.98→4.99).
**Affected products (Vons):** ribeye_steak (23.97→7.99).
Fix / workaround: Added `scripts/price_tracker/baseline_per_lb.py` (`normalize_baseline_price()`): detects per-lb YAML families via `size_format_subtitle`, extracts package weight from product name (e.g. "- 3.5 Lb"), and divides. Both generator scripts now call this before writing the TS value. Manually corrected all existing per-lb baselines in `priceTrackerFallback.ts` and `vonsBaseline.generated.ts`.
Web verification: Direct Safeway fetch blocked by Imperva (expired cookie). Instacart shows Safeway bone-in ribeye at $18.99/lb (promotional, sale ending 7/7/2026). Our $12.99/lb baseline comes from the pgmsearch crawl and may reflect a prior sale period; the regular everyday price is likely $18.99+/lb. To re-crawl at the current regular price: refresh `SAFEWAY_COOKIE`, run `python scripts/seed_safeway_baseline.py --query "ribeye steak"`, then `python scripts/generate_safeway_feed_matches.py --merge-fallback`.
How to verify: `python -c "from price_tracker.baseline_per_lb import normalize_baseline_price; print(normalize_baseline_price('ribeye_steak','USDA Choice Bone In Beef Rib Steak Mega Pack - 3.5 Lb',45.47))"` → `(12.99, True)`.
Related files: `scripts/price_tracker/baseline_per_lb.py`, `scripts/generate_safeway_feed_matches.py`, `scripts/generate_vons_feed_matches.py`, `src/data/priceTrackerFallback.ts`, `src/data/vonsBaseline.generated.ts`

### normalize_per_lb divided price by itself for all "$X lb" offer texts (per_lb bug)

Date discovered: 2026-07-06
Context: Price tracker charts showed ribeye steak at $1 for multiple weeks on both Safeway and Vons tabs. Investigation found the same $1.0 bug on chicken breast, grapes, cherries, peaches, nectarines, and plums.
What happened: `normalize_per_lb()` in `scripts/price_tracker/normalization.py` tries to extract a package weight from offer text (e.g. "Chicken 3 lb for $8.97" → $2.99/lb). But when the ad text printed the per-lb price next to the unit — e.g. "Ribeye Steak $9.99 LB" or "Grapes $2.49 lb Member Price" — `_extract_lb_weight()` matched the price itself as the weight (9.99 lb → 9.99/9.99 = $1.0). Every per-lb family where the raw_offer_text included "$X lb" or "X lb" (appended price from vision extraction) yielded exactly $1.0.
A second bug: `base_normalize_unit_price()` had a guard `not re.search(r"(when you )?buy\s+\d+", promo)` that skipped multi-buy normalization for "PICK 4 FOR $20 WHEN YOU BUY 4" bundle deals. This caused Safeway chicken thighs (2026-03-25) to show $20/lb instead of $5/item.
Fix / workaround:
1. `normalize_per_lb`: Added early return `if price_basis == "per_lb": return price` — if the CSV already tags the price as per-lb, no weight extraction needed.
2. `normalize_per_lb`: Added safety check `if abs(lbs - price) / price < 0.02: return price` (skip divide if extracted weight ≈ advertised price).
3. `base_normalize_unit_price`: Removed the "when you buy" guard — always try `_multi_buy_unit_price` for `multi_buy` basis; the function itself returns None when no "N for $X" pattern is found, so no regression.
4. Regenerated all affected products: `ribeye_steak`, `chicken_breast_per_lb`, `seedless_grapes_per_lb`, `chicken_thigh_per_lb`, `tri_tip_roast`, `cherries_per_lb`, `peaches_per_lb`, `nectarines_per_lb`, `plums_per_lb` for both Safeway and Vons.
Before/After examples (price for 2026-07-01):
- Safeway ribeye_steak: $1.0 → $9.99/lb
- Vons ribeye_steak: $1.0 → $7.99/lb
- Safeway cherries: $1.0 → $1.99/lb
- Safeway grapes 2026-03-25: $1.0 → $2.49/lb
- Safeway chicken thighs 2026-03-25: $20.0 → $5.0 (per-pack from "Pick 4 for $20")
How to verify: `PYTHONPATH=scripts python3 -m unittest tests.test_normalization -v`. Check `grep '"2026-07-01"' src/data/weeklyAdPrices.generated.ts` near `ribeye_steak` — should show `"price": 9.99`. Vons same → `"price": 7.99`.
Related files: `scripts/price_tracker/normalization.py` (`normalize_per_lb`, `base_normalize_unit_price`), `src/data/weeklyAdPrices.generated.ts`, `src/data/vonsWeeklyAdPrices.generated.ts`

### Coca-Cola B2G3F Safeway 7/1: missing split row + stale per-can display (fixed 2026-07-07)

Date discovered: 2026-07-07
Context: Homepage Popular this week + price tracker for `coca_cola_12packs` Safeway week 2026-07-01.
What happened: Safeway 7/1 ad has "BUY 2, GET 3 FREE WHEN YOU BUY 5" on soda 12-packs ($12.99 ref). Vision pipeline captured the multi-brand promo block in `raw_offer_cards.csv` (page 1 offer 14) but did not promote Coca-Cola to `split_offer_items.csv` (`ambiguous_multi_product_offer|missing_or_unclear_price`). `weeklyAdPrices` had `null` for 2026-07-01 → UI fell back to baseline $12.99. Homepage `unitPriceDisplay()` preferred stale `priceComparison.groceryUnitPrice` ($12.99÷12 = $1.08/can) over deal price. `getCurrentPrice()` also preferred the upcoming preview week (2026-07-08) over the calendar-active week when both existed.
Fix / workaround:
1. Manually added Coca-Cola 12-pack row to `data/weekly_ads/2026-07-01/bay_area/split_offer_items.csv` + sibling `outputs/product_discovery_safeway/split_offer_items.csv` with `advertised_price=12.99`, `price_basis=bogo`, `promo_text="BUY 2, GET 3 FREE WHEN YOU BUY 5 MEMBER PRICE"`.
2. Regenerated: `PYTHONPATH=scripts python3 scripts/generate_weekly_ad_prices.py --product-id coca_cola_12packs --feed safeway` → `price: 5.2` per 12-pack (2/5 × $12.99).
3. `getCurrentWeeklyPrice()` / `getDealAdjustedUnitPrice()` in `priceTrackerUtils.ts` — active week + per-can from deal price.
4. `previewData.ts` prefers deal-adjusted unit price over stale comparison baseline.
5. `backfill_price_comparisons.py` maps legacy canonical ids → YAML family ids (`coke_zero` → `coca_cola_12packs`) and prefers calendar-active ad week over preview.
Before/after: homepage Coca-Cola showed `$12.99` / `$1.08/can` / `onSale: false` → now `$5.20` / `$0.43/can` / `onSale: true`.
How to verify: `npm run generate:homepage-preview` → `data/homepage-preview.generated.json` Coca-Cola `unitPrice: "$0.43/can"`. `npx tsx -e` getCurrentPrice/getDealAdjustedUnitPrice on `coca_cola_12packs`. `PYTHONPATH=scripts python3 -m unittest tests.test_normalization -v`.
Related files: `data/weekly_ads/2026-07-01/bay_area/split_offer_items.csv`, `scripts/price_tracker/normalization.py`, `src/data/priceTrackerUtils.ts`, `src/homepage/previewData.ts`, `scripts/backfill_price_comparisons.py`, `src/data/weeklyAdPrices.generated.ts`


Date discovered: 2026-07-06
Context: FamilyDealCard grid on `/staging-price-tracker/` — cards still had unequal heights after summary/stock-up were moved to the Details toggle.
What happened: Four remaining variance sources:
1. **`h2` name** — no line-clamp on desktop (only mobile had it); long names could wrap to 3+ lines.
2. **Price block** (`usualRange` + `atl-hint`) — both conditional; 0–2 extra lines (~32px swing).
3. **`ComparisonBadge`** — biggest source; can be null (0px) or title+detail+locationNote (~60px swing).
4. **`takeaway`** — no line-clamp; could wrap unboundedly.
Fix / workaround:
- `.family-deal-card { min-height: 100%; }` — fills the grid cell so all cards in a row match the tallest one (whitespace at bottom of shorter cards). Uses `min-height` not `height` so the expanded Details panel is not clipped.
- `.family-deal-card__header h2` — added `-webkit-line-clamp: 2` to the **base rule** (not just mobile).
- `.family-deal-card__price-block { min-height: 62px }` (base) / `46px` (mobile ≤767px) — pre-reserves space for sale + usualRange + ATL lines.
- `.family-deal-card__takeaway` — added `-webkit-line-clamp: 2` to the base rule.
How to verify: Open `/staging-price-tracker/` — compare cards with ATL hints, Costco badges, long names, and takeaways; all cards in each row should have identical height. `npm run build:price-tracker` passes.
Related files: `styles.css` (`.family-deal-card`, `.family-deal-card__header h2`, `.family-deal-card__price-block`, `.family-deal-card__takeaway`)

### Card height normalization: secondary info moved to Details toggle

Date discovered: 2026-07-06  
Context: Price tracker card grid on `/staging-price-tracker/` — cards with ATL hint, stock-up badge, promo notes were taller than simpler cards, causing uneven rows.  
What happened: FamilyDealCard had 4 optional elements adding 1–3 lines each: `summary` (always, 1–2 lines), `FamilyStockUpBadge` (always, 1 line), `effectivePrice` (conditional, promo context), and the "Price history" section label.  
Fix / workaround:
1. **Moved to collapsible "Details" toggle**: `summary`, `FamilyStockUpBadge`, `effectivePrice` — revealed by clicking the new `.family-deal-card__details-toggle` button (styled like the varieties-hint link). Net: 2–4 fewer lines per card in the default view.
2. **Removed "Price history" section label** from `.family-deal-card__chart` — saves 1 line per card uniformly.
3. **Kept on card**: price (`saleLabel`), `usualRange` (compacted to 12px), `ATL hint`, chart, `ComparisonBadge`, takeaway.
4. **CSS**: `.family-deal-card` gap reduced 12px→8px; `price-tracker-product-meta` truncated to 1 line (`-webkit-line-clamp: 1`) on all breakpoints; `usual`/`effective` font-size reduced 14px→12px.  
How to verify: Open `/staging-price-tracker/` → cards across sections should be noticeably more uniform in height. Cards with and without ATL/Costco badges should differ by ≤2 lines. Click "Details" on any card to reveal summary + stock-up. `npm run build:price-tracker` passes.  
Related files: `src/staging-price-tracker/FamilyDealCard.tsx`, `styles.css` (`.family-deal-card__details-toggle`, `.family-deal-card__details-panel`)

### Price tracker vote layout: compact strip after Popular (variant 2 chosen)

Date discovered: 2026-07-06  
Context: `/staging-price-tracker/` voting module placement — too prominent between store tabs and Popular this week.  
What happened: Four layouts were explored via `?voteVariant=1|2|3|4`; **variant 2** (compact horizontal strip below Popular this week) was chosen permanently. Exploration code (`VoteVariantSwitcher`, compare banner, `compare.html`, query-param switching) was removed.  
Fix / workaround: Page order is **filters → Popular this week → vote strip → product sections**. `TrackVotePanel` is a full-width strip: subtle label "Help pick what we track next.", top 6 vote pills in a responsive wrap row, compact inline suggestion form. Supabase upvote + moderated submit unchanged (`useTrackVote`, RPCs `vote_on_item` / `submit_suggestion`).  
How to verify: `npm run build:price-tracker` → open `/staging-price-tracker/` → search/chips, then Popular, then pink-accent vote strip, then sections. No variant switcher or `?voteVariant=` handling.  
Related files: `src/staging-price-tracker/vote/TrackVotePanel.tsx`, `src/staging-price-tracker/SectionedTrackerList.tsx`, `src/staging-price-tracker/App.tsx`, `styles.css`


Date discovered: 2026-07-05
Context: `npm run dev:price-tracker` / `ERR_CONNECTION_REFUSED` on http://localhost:5173/staging-price-tracker/
What happened: Default Vite 6 listened only on `[::1]:5173`. Browsers and tools using IPv4 `127.0.0.1` could not connect. Agent-background Vite processes also stop when the agent session ends.
Fix / workaround: `vite.config.ts` sets `server.host: "127.0.0.1"`, `port: 5173`, `strictPort: true`. Run dev server in the user's own terminal: `cd <repo> && npm run dev:price-tracker`. Open http://127.0.0.1:5173/staging-price-tracker/ (base path `/staging-price-tracker/`).
How to verify: `lsof -i :5173` shows `127.0.0.1:5173`; `curl -I http://127.0.0.1:5173/staging-price-tracker/` returns HTTP 200.
Related files: `vite.config.ts`, `package.json` (`dev:price-tracker`)

