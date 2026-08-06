# Project Notes

Living notes for findings, gotchas, and repeatable workflows discovered while building this project.

## Safeway / Albertsons API Notes

### If a Safeway query fails, refresh the cookie first

Date discovered: 2026-05-24  
Context: Safeway price-result queries (requests or Playwright) during grocery price tracking.  
What happened: Failed searches, empty/stale results, infinite “loading” on search results, `api_timeout`, or 401/403 usually mean the session cookie expired, not bad query params.  
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
5. Headful manual reset: `python scripts/seed_vons_baseline_playwright.py --headful --channel chrome --manual-session --fresh-profile --query grapes`. Set store/zip, sign in if prompted, press Enter.
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
Fix / workaround: Set `SAFEWAY_TIMEOUT_SECONDS=30` (requests) or `VONS_TIMEOUT_SECONDS=45` (curl) in `scripts/.env`. Playwright seeds use `--api-timeout` (default 45s) and `--navigation-timeout` (default 60s). On timeout, logs include actionable text. E.g. refresh `SAFEWAY_COOKIE` / `VONS_COOKIE` from DevTools → Network → pgmsearch; Vons also notes store/zip (`VONS_STORE_ID=2053`, `VONS_ZIPCODE=92110`). Errors distinguish `timeout`, `auth` (401/403), and `empty_response`.  
How to verify: Run with an expired cookie; expect a clear timeout/auth message within the configured seconds, not an indefinite hang.  
Related files: `scripts/safeway_client.py`, `scripts/vons_client.py`, `scripts/safeway_config.py`, `scripts/vons_config.py`, `scripts/seed_safeway_search_playwright.py`, `scripts/seed_vons_baseline_playwright.py`

## Data Extraction Notes

Weekly ad prices for the staging price tracker:

- Manifest (week → PDF): `data/weekly_ads/flyer_manifest_safeway.csv` (synced from `scrolling-the-aisle/inputs/weekly_ads/`)
- Offer rows: `scrolling-the-aisle/outputs/product_discovery_safeway/split_offer_items.csv`
- Regenerate: `npm run generate:weekly-ad-prices` → `src/data/weeklyAdPrices.generated.ts`

Gotchas: grouped offers split into per-item rows, matchers in `scripts/generate_weekly_ad_prices.py` pick the best split row per canonical item. Multi-buy promos need per-unit normalization (`3 for $5`, `when you buy 3`, etc.). Some tracker items have no ad match yet (e.g. Coke Zero 12pk) or use a close proxy (Fairlife → Premier Protein 4pk).

### Jul 22 false matches: seed butter, strips, Cape Cod, chicken word order

Date discovered: 2026-07-23  
Context: Safeway week `2026-07-22` import → tracker publish.  
What happened: (1) `butter_16oz` matched O Organics **Seed Butter**; (2) `chicken_breast_per_lb` preferred Open Nature **breast strips** $6.99 over front-page Signature SELECT breasts $2.99/lb; (3) `lays_kettle_cooked` took Cape Cod from a Friday Cape Cod/Sun Chips tile; (4) after excluding strips, real breasts still failed because flyer text is `chicken boneless skinless breasts` (chicken first) while includes expected `boneless skinless chicken breasts`.  
Fix / workaround: YAML `keep_separate_from` for seed/bean butter, chicken strips/tenders, Cape Cod; add include phrases `chicken boneless skinless breast(s)`. Rematch then `npm run build:price-tracker`.  
How to verify: `chicken_breast_per_lb["2026-07-22"].price === 2.99` with offerText Signature SELECT breasts; no Jul 22 rows for `butter_16oz` / `lays_kettle_cooked`.  
Related files: `data/canonical_tracker_families.yaml`, `src/data/weeklyAdPrices.generated.ts`, `output/weekly_deals/2026-07-22/`

### Kettle Brand requires literal “Kettle Brand” (not bare “Kettle Potato Chips”)

Date discovered: 2026-07-23 (updated 2026-08-05)  
Context: `kettle_brand_chips` matcher vs Safeway flyer titles that say “Kettle Potato Chips” / “Kettle chips”.  
What happened: (1) Jul 22 true Kettle Brand coupon titled **Kettle Potato Chips** (no “Brand”) missed when includes required Brand. Broadening to bare `Kettle Potato Chips` / `Kettle chips` fixed Jul 22 but (2) on **2026-08-05** falsely matched a Lay’s-kettle-style “Kettle Potato Chips” tile @ $1.99 onto `kettle_brand_chips`.  
Fix / workaround: **Require literal “Kettle Brand”** in YAML includes. Keep `Lay's Kettle` / Cape Cod / mix-tile brands in `keep_separate_from`. Do **not** put bare `Kettle Potato Chips` in excludes — QUALIFIER_WORD `brand` would also block true `Kettle Brand Potato Chips`. When a verified Kettle Brand flyer omits Brand (Jul 22), correct the split row text to include “Kettle Brand” rather than broadening includes.  
How to verify: `python -m unittest tests.test_canonical_families.TestKettleBrandChipsMatcher`. `kettle_brand_chips["2026-08-05"]` is null; `["2026-07-22"].price === 1.99` with offerText containing `Kettle Brand`.  
Related files: `data/canonical_tracker_families.yaml` (`kettle_brand_chips`), `tests/test_canonical_families.py`, `src/data/weeklyAdPrices.generated.ts`, sibling `split_offer_items.csv`

### Vons 2026-07-22 import: chips/eggs/chicken vision errors

Date discovered: 2026-07-25  
Context: Vons-only import of `vons 7-22 - 7-28.pdf` via `/usr/bin/python3 scripts/import_weekly_ad.py --week-start 2026-07-22 --week-end 2026-07-28 --vons-pdf "vons 7-22 - 7-28.pdf"`.  
What happened: Vision misread several front-page tiles: chips as **2 for $6** with Ruffles/Kettle (real: Lay’s/Doritos/Simply NKD/Miss Vickie’s/Tim’s **$2.49 when you buy 3**, 4.75–10.75 oz); Post cereal **$1.99** (real **$1.88 buy 3**); eggs **12 ct** (real Lucerne Cage Free **18 ct** $1.99); hallucinated Large Strawberries/Raspberries/Blackberries and 2 lb strawberries; missed Large Cherries $3.99/lb, Lucerne Butter $2.99 buy 2, Tillamook cheese $1.99; matched bone-in **Fresh Split Chicken Breasts** $1.69 onto `chicken_breast_per_lb`.  
Fix / workaround: Manually correct dedicated + consolidated `split_offer_items.csv`; YAML `keep_separate_from` for split/bone-in chicken breasts; add cheese/Simply NKD includes; rematch `--feed vons` then `npm run build:price-tracker`. Friday Hass avocados 3 for $5 ($1.67) correctly stays unmatched when above Vons baseline $1.50.  
How to verify: Vons Jul 22 — Doritos/Lay’s/Simply $2.49, Post $1.88, eggs $1.33/dozen, cherries $3.99, butter $2.99, blueberries $0.99, Oreo/Chips Ahoy $1.99; no chicken_breast / strawberries / Ruffles / kettle for that week. Bundle includes `2026-07-22`.  
Related files: `data/canonical_tracker_families.yaml`, `src/data/vonsWeeklyAdPrices.generated.ts`, `~/Documents/scrolling-the-aisle/outputs/product_discovery_vons*/split_offer_items.csv`, `output/weekly_deals/2026-07-22/`

### Vons 2026-07-29 import: front-page miss + Pick 4 pollution

Date discovered: 2026-07-28  
Context: Vons-only night-before publish of `vons 7-29 - 8-4.pdf` (week `2026-07-29` → `2026-08-04`) via `/usr/bin/python3 scripts/import_weekly_ad.py --week-start 2026-07-29 --week-end 2026-08-04 --vons-pdf "vons 7-29 - 8-4.pdf"`. Soft-start already marks Jul 28 as ACTIVE (no Preview).  
What happened: (1) Vision mostly captured the digital-coupon sidebar + chicken hero on page 1 and missed front-page produce/B2G2/grocery tiles (grapes, white peaches/nectarines/plums $1.99 digital; Doritos/Simply NKD/Tostitos B2G2; soda B2G2; Chobani 10/$10; Häagen-Dazs/Dreyer’s $2.99 buy 2; GM family cereal/Nature Valley $3.99 buy 3). (2) Page 2 Pick 4 rows had polluted package blobs; hallucinated Lay’s/Simply @ $4.99; Kettle/Cape Cod blocked as mixed-item. (3) First vision run hit truncated JSON on page 2 (retry succeeded; page 1 cache HIT). (4) Cream cheese brick is **$0.99** Pick 4 (not the $1.99 spread tile). B2G2 chips effective **$2.75** from “save up to $10.98 on 4” ($5.49 ref).  
Fix / workaround: Manually add/correct dedicated + consolidated `split_offer_items.csv` (`review_reasons=manual_pdf_verified_2026-07-28`); rematch `--feed vons`; `npm run build:price-tracker`. WoW chicken $1.99→$2.99 and Coke B2G2 effective $6 are real flyer prices.  
How to verify: `isPreviewWeek("2026-07-29", Jul 28) === false`. Vons Jul 29 — grapes/peaches/plums $1.99, Doritos/Simply/Tostitos $2.75, Kettle/Cape Cod/Lay’s Kettle $1.99, cream cheese $0.99, Chobani $1.00, HD pints $2.99, GM family Cheerios $3.99, chicken $2.99. Bundle includes `2026-07-29`.  
Related files: `src/data/vonsWeeklyAdPrices.generated.ts`, `~/Documents/scrolling-the-aisle/outputs/product_discovery_vons*/split_offer_items.csv`, `output/weekly_deals/2026-07-29/`

### Vons 2026-08-05 import: page-2 token cap + front-page miss

Date discovered: 2026-08-05  
Context: Vons-only import of `vons 8-5 - 8-11.pdf` via `import_weekly_ad.py --week-start 2026-08-05 --week-end 2026-08-11 --vons-pdf "vons 8-5 - 8-11.pdf"`.  
What happened: (1) Full-page vision on **page 2** hit `finish_reason=length` at 32k completion tokens (model expanded Pick 4 into endless Western Family lists) → `JSONDecodeError`. Workaround: extract page 2 as **top/bottom halves** with an anti-verbosity prompt, merge into `cache/.../page_002.json`, then rerun import. (2) Page 1 again missed buy-3 Goldfish/Lay’s/Kellogg tiles and mislabeled **New York Steak** as Ribeye; Pick 4 polluted Doritos/Cheez-It onto wrong tiles. (3) Discover exited 1 on empty `baseline_price_candidates.csv` but `split_offer_items.csv` existed — import continued. (4) Oreo/Chips Ahoy/Kettle Brand on Pick 4 are **Family/Party Size** ($3.99); regular `kettle_brand_chips` / `chips_ahoy` / `cheez_it` stay unmatched (`Family Size`/`Party Size` excludes).  
Fix / workaround: Manual PDF-verified splits (`review_reasons=manual_pdf_verified_2026-08-05`) with **clean single-product** `raw_offer_text` (mixed group blobs block auto-match). Add `Family Size`/`Party Size` to `cheez_it_crackers` + `chips_ahoy` `keep_separate_from`. Rematch `--feed vons`; `npm run build:price-tracker`.  
How to verify: Vons Aug 5 — chicken $1.99, Goldfish $1.69, Lay’s/Kettle/Popcorners $2.49, peaches/nectarines/plums $1.99, butter $2.99, Oreo family $3.99, Pringles $1.49; `ribeye_steak`/`doritos_5_13oz`/`cheez_it_crackers`/`kettle_brand_chips` null. Bundle includes `2026-08-05`.  
Related files: `src/data/vonsWeeklyAdPrices.generated.ts`, `data/canonical_tracker_families.yaml`, `~/Documents/scrolling-the-aisle/outputs/product_discovery_vons*/split_offer_items.csv`, `output/weekly_deals/2026-08-05/`

**Vons baselines (SoCal):** Same Albertsons `pgmsearch` API: `python scripts/seed_vons_baseline_playwright.py --http-only` (curl transport in `vons_client.py`; Playwright fallback). Env: `VONS_COOKIE`, `VONS_VISITOR_ID`, `VONS_STORE_ID=2053`, `VONS_ZIPCODE=92110`, `VONS_CHANNEL=instore`, `VONS_USER_AGENT` (Safari), optional `VONS_UUID`, `VONS_SUBSCRIPTION_KEY`. Then `npm run generate:vons-feed-matches` → `src/data/vonsBaseline.generated.ts`. **Vons weekly ads** via `vonsWeeklyAdPrices.generated.ts`.

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

### Card size subtitles use Regular size / Family size + range

Date discovered: 2026-07-14
Context: Tracker family cards show `size_format_subtitle` under the product title.
What happened: User-facing size lines mixed filler (“regular bags”, “roughly…”, “X oz bags”) instead of a clear size tier.
Fix / workaround: Where the family is a standard-vs-larger pack split, set YAML to `regular size, <range>` or `family size, <range>` (party/giant map to family size). Skip the prefix for per-lb, packs, tubs, each, etc. `toSentenceCase()` capitalizes the first letter at render. Nabisco cracker shortlist blurbs still use the app label “Nabisco family-size snack crackers” via `shortlist_copy._app_label`, not the size subtitle.
How to verify: Oreo → “Family size, 10.68–18.71 oz”; Ruffles → “Regular size, 5–13 oz”; regenerate with `npm run generate:canonical-families`.
Related files: `data/canonical_tracker_families.yaml`, `src/data/priceTrackerUtils.ts`, `src/staging-price-tracker/FamilyDealCard.tsx`, `scripts/price_tracker/shortlist_copy.py`

### Homepage highlights use balanced editorial breakout (Version 1)

Date discovered: 2026-07-12
Context: Homepage “Scrolling the Aisle's highlights of the week” after layout exploration.
What happened: Chose exploration **Version 1: Balanced editorial breakout** as the public layout. Category columns grouped by editorial `customBadge` → Friday / Produce / Meat / Snacks / Variety / Other Deals (`DEAL` and missing badges → Other Deals). Colored category titles + borders; name and price sit side-by-side on each row. **One horizontal row of four equal columns** (`.hub-picks-cat-columns`: `grid-template-columns: repeat(4, minmax(160px, 1fr))` with `overflow-x: auto` so phones scroll sideways instead of wrapping to 2×2). Safeway/Vons toggle unchanged; data from `data/homepage-preview.generated.json`.
How to verify: Open `index.html` → picks show four category columns on one row (desktop fills width; narrow screens scroll horizontally); name/price on one row; no layout switcher; toggle Safeway/Vons.
Related files: `homepage.js` (`groupPicksByCategory`, `renderPicksReport`), `styles.css` (`.hub-picks-cat-*`), `index.html` (`#picks-grid.hub-picks-report`)

### Never ship layout exploration switchers to production

Date discovered: 2026-07-12
Context: Temporary multi-version layout pickers (e.g. former `homepage-picks-width-explore/` with “Layout exploration” 1–6 controls) are for Evelyn to compare options locally only.
What happened: An explore switcher was left wired into `index.html` / `homepage.js`, so end users could browse every draft layout.
Fix / workaround: **Always true:** never ship version explorers, A/B layout switchers, or TEMP explore CSS/JS on the public site. Keep experiments off the production path (local-only folder, or unlinked). When a layout is chosen, port **only that version** into the real homepage files (`homepage.js`, `styles.css`, `index.html`) and delete the explore scaffolding before considering the work shipped.
How to verify: Public homepage has no “Layout exploration” chrome, no version tabs/arrows, and no `*-explore/` scripts linked from `index.html`.
Related files: `index.html`, `homepage.js`, `styles.css`

### "Hand-picked deals" section has TWO data paths, ONE shared UI layout

Date discovered: 2026-07-08  
Updated: 2026-07-26  
Context: The curated "Hand-picked deals I'm watching…this week" editorial section is fed by two data paths that both read from `data/popular_this_week.yaml`, but they now share the same **balanced editorial breakout** UI (category columns via `.hub-picks-cat-*`).
1. **Staging price tracker** (`/staging-price-tracker/` / `grocery-price-tracker/`): React `PopularThisWeek.tsx` → same `hub-picks-report` markup as homepage; grouping via `src/data/handpickedCategoryReport.ts`. Fed by `POPULAR_THIS_WEEK` in `canonicalTrackerFamilies.generated.ts`. Jump link is a button that scrolls to the family card (`onJumpToFamily`). Requires `npm run build:price-tracker`.
2. **Homepage briefing** ("Scrolling the Aisle's highlights of the week"): plain `homepage.js` (`renderPicksReport` / `groupPicksByCategory`), fed by `data/homepage-preview.generated.json` (`npm run generate:homepage-preview`). Served statically. Links out to the tracker.
Gotcha: Data wiring still differs (tracker live products vs homepage JSON). Keep badge→category maps in sync between `homepage.js` and `handpickedCategoryReport.ts`. Empty/`DEAL` badges → “Other Deals”.
How to verify: Homepage and tracker both show Friday / Produce / Meat / Snacks / Variety / Other Deals columns with name+price on one row; no card-grid pills or top-7 expander on the tracker.
Related files: `homepage.js`, `styles.css` (`.hub-picks-cat-*`), `src/data/handpickedCategoryReport.ts`, `src/homepage/previewData.ts`, `src/staging-price-tracker/PopularThisWeek.tsx`, `data/homepage-preview.generated.json`

### "Hand-picked deals this week" cards support editorial badge + subtitle overrides

Date discovered: 2026-07-08  
Updated: 2026-07-26  
Context: The Safeway/Vons "Hand-picked deals I'm watching…this week" section is an **editorial/content** shortlist curated in `data/popular_this_week.yaml`. It is NOT canonical tracker graph data. Entries need explicit badges (FRIDAY/DEAL/MEAT/etc.) and custom subtitle copy that the original schema (title/tracker_family_ids/reason/display_order) couldn't express.
What changed:
1. YAML schema gained two OPTIONAL per-entry fields: `badge` (label string, e.g. `FRIDAY`) and `subtitle` (display copy that overrides `reason`). Vons entries omit them and keep old behavior.
2. `scripts/generate_canonical_families.py` `_normalize_popular_entries()` passes `subtitle`/`badge` through (empty string when absent) and the generated `PopularThisWeekEntry` type now includes `subtitle: string` and `badge: string`. Re-run `npm run generate:canonical-families` (or `build:price-tracker`) to regenerate `src/data/canonicalTrackerFamilies.generated.ts`.
3. Homepage + tracker both group by `badge` into Friday / Produce / Meat / Snacks / Variety / Other Deals columns (`handpickedCategoryReport.ts` / `homepage.js`). `entry.subtitle || entry.reason` is the note under each row. Tracker "See price history →" jumps to family cards when `tracker_family_ids` is non-empty.
4. `src/homepage/previewData.ts` `PopularPick` gained `customBadge?` and uses `entry.subtitle || entry.reason` as `explanation`.
Guardrails learned: leave `tracker_family_ids: []` when no clean canonical family exists. Do NOT invent/loosen matches to make a card link to a graph. Empty ids render as pure editorial rows (keyed by unique `title`, no collision). This section must never pull/alter canonical graph data, and must never mention fresh/smoked salmon. Also call Nestlé ice cream "Nestlé Drumstick ice cream", never bare "drumsticks".
How to verify: `npm run build:price-tracker` passes `verify-price-tracker-build.mjs`; tracker + homepage show the same category-column layout for the curated week.
Related files: `data/popular_this_week.yaml`, `scripts/generate_canonical_families.py`, `src/data/canonicalTrackerFamilies.generated.ts`, `src/data/handpickedCategoryReport.ts`, `src/staging-price-tracker/PopularThisWeek.tsx`, `src/homepage/previewData.ts`, `styles.css` (`.hub-picks-cat-*`)

### Section items ordered by deal quality (best deals first, row by row)

Date discovered: 2026-07-08
Context: `/staging-price-tracker/` sections previously ordered items by curated `displayOrder`; user wanted strongest current deals ranked first, filling the grid left-to-right/top-to-bottom, and the "Show more" toggle to hide the *worst* deals.
What changed:
1. New reusable helper in `src/data/priceTrackerUtils.ts`: `rankProductsByDealQuality()` / `compareByDealQuality()` / `getDealQualityRankKey()`. Ranking key (best → worst): (1) highlightable preview deal or currently on sale before non-deals; (2) benchmark bucket via `computeFeedProductBenchmark`. All-time low > near all-time low > strong sale > normal sale > weak sale > insufficient history; (3) larger % discount vs baseline (preview discount when `hasHighlightablePreviewDeal`, else `getProductSaleDiscountPercent` ?? `getDiscountPercent`); (4) stable `displayName` then `canonicalId` tiebreak so order is deterministic.
2. `SectionedTrackerList.tsx` now sorts each section with `rankProductsByDealQuality(...)` instead of `displayOrder`. Grid fills row by row, so the ranked array = best-deal-first layout.
3. `sectionShowMore.ts` `partitionSectionProducts` is now **count-based**: it hides the lowest-ranked tail (`products.slice(0, length - N)`), where N = number of ids in the curated `SECTION_COLLAPSED_PRODUCT_IDS` for that section (new `getCollapsedCount()` helper). The curated list still decides *how many* are hidden; deal ranking decides *which*. Products must be pre-sorted best-first before calling. Search still bypasses collapse.
How to verify: `npm run build:price-tracker` (runs `verify-price-tracker-build.mjs`). Passes. `npm run dev:price-tracker` → http://127.0.0.1:5173/staging-price-tracker/ → within any section (e.g. "Stock up on snacks & treats"), the first/top-left cards show the strongest sale badges (all-time low / on sale), non-deal cards trail; click "Show more (N)" and the newly revealed cards are the weaker/baseline items. Toggling store tabs (Safeway/Vons) re-ranks per feed.
Related files: `src/data/priceTrackerUtils.ts` (`rankProductsByDealQuality`, `compareByDealQuality`, `getDealQualityRankKey`, `BENCHMARK_BUCKET_RANK`), `src/staging-price-tracker/SectionedTrackerList.tsx`, `src/staging-price-tracker/sectionShowMore.ts`

### Tracker vote suggestions are moderated before appearing publicly

Date discovered: 2026-06-13  
Context: Price tracker voting module (`TrackVoteModule`) on `/staging-price-tracker/`.  
What happened: User suggestions used to insert into `product_track_suggestions` and show immediately.  
Fix / workaround: New table `tracker_vote_items` with `status` (`pending|approved|rejected|merged`). Public UI reads `status='approved'` only; new suggestions go to `pending` via RPC `submit_suggestion`. Admin review at `/admin/suggestions/` (password via Edge Functions `validate-admin` + `admin-suggestion-actions`).  
How to verify: Submit a custom item on the tracker → success message about review, item not in list. Approve in admin → item appears and accepts votes via RPC `vote_on_item`.  
Related files: `supabase/migrations/20260614_tracker_vote_items.sql`, `src/staging-price-tracker/TrackVoteModule.tsx`, `src/admin/suggestions/`, `supabase/functions/validate-admin/`, `supabase/functions/admin-suggestion-actions/`

### Refresh tracker vote seeds when families get covered

Date discovered: 2026-07-26  
Context: Public “Help pick what we track next” strip reads approved rows from `tracker_vote_items` (fallback seed in `src/lib/trackVote.ts` `SEED_TRACK_ITEMS` only when Supabase is empty/unavailable).  
What happened: Seed chips still offered Berries, Grapes, Chicken breast, Oreos, Ritz, Kettle chips, Ribeye, Bell pepper after those families were added to `canonical_tracker_families.yaml`.  
Fix / workaround: Reject covered approved rows and insert new uncovered staples via migration (e.g. `supabase/migrations/20260726_refresh_tracker_vote_seeds.sql`); keep `SEED_TRACK_ITEMS` in sync. Do not re-suggest shrimp (intentionally untracked). Leave unrelated product chips (e.g. Yasso) alone; reject vague non-products (e.g. Household items) so they don’t crowd the top-6 alphabetical strip when all votes are 0.  
How to verify: `supabase db push` (or run the SQL in the dashboard) → GET approved `tracker_vote_items` no longer includes covered names; new seeds appear. Open `/grocery-price-tracker/#track-vote` (or staging) and confirm pills. Offline fallback: rebuild so `SEED_TRACK_ITEMS` is in the bundle.  
Related files: `supabase/migrations/20260726_refresh_tracker_vote_seeds.sql`, `supabase/migrations/20260727_reject_household_vote_item.sql`, `src/lib/trackVote.ts`, `src/staging-price-tracker/vote/useTrackVote.ts`, `about/index.html`

### Grocery finds are moderated before going live

Date discovered: 2026-07-12
Context: Live grocery finds feed (`finds.html`, `submit.html`, `app.js`).
What happened: Submissions used to insert with `status='approved'` and appear immediately on the public feed.
Fix / workaround: New submissions insert with `status='pending'` (RLS policy enforces pending-only inserts). Public feed still reads `status='approved'` only. Admin review at `/admin/finds/` (password via `validate-admin` + `admin-find-actions` Edge Function). On approve, `expires_at` resets to 3 days from approval time. Apply `supabase/migrations/20260712_finds_moderation.sql`.
How to verify: Post a find → success banner says pending review, item not on feed. Approve in `/admin/finds/` → item appears on `finds.html`. Deploy `admin-find-actions` with `verify_jwt = false` (see `supabase/config.toml`). `npm run build:admin-finds` → commit `admin/finds/` for GitHub Pages.
Related files: `supabase/migrations/20260712_finds_moderation.sql`, `supabase/functions/admin-find-actions/`, `src/admin/finds/`, `app.js`, `finds.html`, `submit.html`

Deploy admin Edge Functions and set secret:

```bash
supabase secrets set ADMIN_PASSWORD=your-secret
supabase functions deploy validate-admin
supabase functions deploy admin-suggestion-actions
supabase functions deploy admin-store-actions
supabase functions deploy admin-find-actions
```

**Important:** `supabase/config.toml` must set `verify_jwt = false` for all four admin functions. If `admin-store-actions` or `admin-find-actions` is deployed without it, the Supabase gateway rejects the custom HMAC bearer token (`UNAUTHORIZED_INVALID_JWT_FORMAT`) and `/admin/stores/` or `/admin/finds/` sign-in appears to hang or immediately bounce back with a session error after password validation succeeds.

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
What happened: Cards could show contradictory copy, e.g. "Comparison unavailable" or "Not found at Costco" alongside "Costco wins on price", plus "San Francisco Costco pricing" location notes and a chart footnote "Not available at Costco".
Fix / workaround: Central gate `hasMeaningfulCostcoComparison()` in `priceComparisonUtils.ts`. Returns true only when `comparisonStatus === "comparable"`, winner is grocery/costco/tie, and Costco price exists. All Costco UI (badge, chart line, takeaway win/loss, expanded Ritz details, location notes) is hidden when false. No explicit "not at Costco" / "comparison unavailable" messaging. Absence of Costco UI is the signal.
How to verify: Open `/staging-price-tracker/` → Coke Zero / Tillamook / Mission chips → no Costco badge, no blue chart line, no Costco takeaway. Doritos Safeway → still shows Via Costco badge + chart line. `npm run build:price-tracker`.
Related files: `src/data/priceComparisonUtils.ts`, `src/data/priceTrackerUtils.ts`, `src/staging-price-tracker/PriceTrendChart.tsx`, `src/data/trackerFamilyUtils.ts`


Date discovered: 2026-07-05
Context: Costco line in price tracker charts after YAML migration.
What happened: (1) Costco warehouse data only covers Jun–Jul 2026; earlier grocery weeks had `costcoPrice: null`, making the line appear as a short right-side stub. (2) For produce items (strawberries, grapes, avocados), Costco sells multi-lb packages but grocery tracks per-lb; using raw `price` made the comparison off. (3) 49 new YAML families without Costco data got `costcoComparable: true` (from YAML) but no history → `isCostcoUnavailableOnChart()` incorrectly showed "Not available at Costco" for all of them.
Fix / workaround:
1. `buildUnifiedChartRows`: after mapping observations to weeks, find `flatCostcoPrice` (last known Costco price) and fill any week without an observation with it → continuous flat line.
2. `getCostcoChartPricePoints`: use `point.unitPrice` instead of `point.price` when `groceryUnitType` is "lb" or "each" (produce items) and `unitPrice < price`. Keeps y-axis in the right per-unit scale.
3. `isCostcoUnavailableOnChart`: only return `true` when `comparison.comparisonStatus === "not_sold_at_costco"` or `comparison.winner === "grocery_only"`. Returns `false` when no comparison data (new families without metadata).
How to verify: Strawberries chart shows Costco line flat at ~$2/lb (per-lb normalized) across all 9 weeks. Doritos chart shows Costco $6.99 package line flat. No "Not available at Costco" message for families like `lays_potato_chips_regular`. `npm run build:price-tracker`.
Related files: `src/data/priceTrackerUtils.ts`

### Recharts Line must be direct children of LineChart (no Fragment wrappers)

Date discovered: 2026-07-05  
Context: Price tracker graphs on `/staging-price-tracker/` after unified Costco/grocery chart refactor (commit 7795b89).  
What happened: Axes, grid, and baseline reference line rendered but **zero** price lines/dots/tooltips. Recharts `findAllByType(children, Line)` returned empty when `<Line />` components were wrapped in `<>...</>` fragments inside the range/unified ternary.  
Fix / workaround: Keep each `<Line />` as a **direct** child of `<LineChart>` (same pattern as pre-refactor). Conditional lines use `{cond ? <Line /> : null}`, not fragment groups.  
How to verify: Playwright: `.recharts-line` count > 0 and hover on a dot shows `.price-tracker-chart-tooltip` with a price. `npm run build:price-tracker`.  
Related files: `src/staging-price-tracker/PriceTrendChart.tsx`

### Price tracker Vite entry must be `src/staging-price-tracker/index.html`, not `grocery-price-tracker/index.html`

Date discovered: 2026-06-07  
Context: `npm run build:price-tracker` / deploying June weekly ad data.  
What happened: `grocery-price-tracker/index.html` is the **deployed** output (overwritten by `scripts/sync-price-tracker-dist.mjs`). It references pre-built `assets/index-*.js`. Using it as the Vite `rollupOptions.input` rebundles stale JS. Source/data changes in `src/` never reach the chart.  
Fix / workaround: Vite input is `src/staging-price-tracker/index.html` (loads `main.tsx`). Sync copies build output into `grocery-price-tracker/` for GitHub Pages (`base: "/grocery-price-tracker/"`). Source stays under `src/staging-price-tracker/`; do not use the deployed `grocery-price-tracker/index.html` as the Vite entry.  
How to verify: `npm run build:price-tracker` runs `scripts/verify-price-tracker-build.mjs` automatically (fails if the JS bundle is missing any `weekStart` from `weeklyAdPrices.generated.ts`). Manual check: `grep 2026-06-03 grocery-price-tracker/assets/index-*.js`. After deploy, hard-refresh the live page and confirm the latest week on the chart x-axis.  
Related files: `vite.config.ts`, `src/staging-price-tracker/index.html`, `scripts/sync-price-tracker-dist.mjs`, `scripts/verify-price-tracker-build.mjs`, `grocery-price-tracker/`

### Public URLs: `/about/` and `/grocery-price-tracker/`

Date discovered: 2026-07-12  
Context: Clean public paths on scrollingtheaisle.com (GitHub Pages).  
What happened: About lived at `/about.html`; tracker at `/staging-price-tracker/` (briefly `/price-tracker/`).  
Fix / workaround: Serve About from `about/index.html` → `/about/`. Serve tracker from `grocery-price-tracker/` with Vite `base: "/grocery-price-tracker/"`. Static HTML redirects (meta refresh + `location.replace`, preserving query + hash): `about.html` → `/about/`; `staging-price-tracker/` → `/grocery-price-tracker/`. Intermediate `price-tracker/` also redirects to `/grocery-price-tracker/`.  
How to verify: Open `/about/` and `/grocery-price-tracker/`; hit old `/about.html` and `/staging-price-tracker/?feed=safeway_bay_area` and confirm landing URLs. `npm run build:price-tracker` passes.  
Related files: `about/index.html`, `about.html`, `staging-price-tracker/index.html`, `vite.config.ts`, `scripts/sync-price-tracker-dist.mjs`, `index.html`, `homepage.js`

Add notes here for useful Cursor prompts, commands, migrations, local testing, and deployment steps.

Living notes rule: `.cursor/rules/project-notes.mdc`, agents should read and update `docs/PROJECT_NOTES.md`.

### Homepage coupon check poll ($10 off online order)

Date discovered: 2026-07-15  
Date updated: 2026-07-29  
Context: Short ask for Safeway shoppers whether they see a specific personalized coupon, beside Beehiiv signup.  
What happened: First poll (Cheez-It / Pringles / Pop-Tarts $3 off) shipped 2026-07-15; UI removed 2026-07-23 with backend left in place. Restored 2026-07-29 for PickUp & Delivery **$10 off next online order** (no minimum; expires 8/11/26) as poll id `safeway_pickup_delivery_10off_202608`.  
Fix / workaround: Tables `coupon_check_polls` + `coupon_check_options`, RPC `vote_coupon_check(text)` from `supabase/migrations/20260715_coupon_check_poll.sql`. New options seeded via `supabase/migrations/20260729_coupon_check_10off_online.sql`. Client: two-column signup row + aside in `index.html`; votes via Supabase + `localStorage` key `sta_coupon_check_votes` (keyed by poll id so prior polls don’t block re-voting). Image: `media/coupons/safeway-pickup-delivery-10off.png`.  
How to verify: Apply `20260729` migration → `npm run preview:homepage` → http://127.0.0.1:8000/ → Yep/Nope beside signup; tally updates; refresh keeps vote; other browsers see shared counts.  
Related files: `supabase/migrations/20260715_coupon_check_poll.sql`, `supabase/migrations/20260729_coupon_check_10off_online.sql`, `index.html`, `homepage.js`, `styles.css`, `media/coupons/safeway-pickup-delivery-10off.png`

### Homepage store vote module (compact chips + Supabase)

Date discovered: 2026-07-07
Context: Homepage hero store suggestion UI, was 4 layout variants saving to localStorage only.
What happened: Needed a single compact chips layout wired to the same moderated vote pattern as tracker item voting (`tracker_vote_items`).
Fix / workaround: New table `store_vote_items` + RPCs `vote_on_store(uuid)` and `submit_store_suggestion(text, text)` in `supabase/migrations/20260707_store_vote_items.sql`. Homepage (`index.html`, `homepage.js`) uses Supabase JS CDN; chips are **rendered dynamically** from all `status='approved'` rows (seed stores Trader Joe's, Whole Foods, Sprouts, Kroger plus any later approvals). Custom form requires store name, optional city → `pending` for review. Client dedupes via `localStorage` key `sta_store_votes`. **Admin UI** at `/admin/stores/` (password via `validate-admin` + `admin-store-actions` Edge Function). Approve/reject/merge pending rows; after refresh, approved stores appear as voteable chips (no HTML edit). Chip order: `vote_count` desc, then oldest `approved_at`/`created_at`, then `id`.
How to verify: Apply migration (`supabase db push` or run SQL in dashboard). Deploy `admin-store-actions` with `verify_jwt = false` (see `supabase/config.toml`). Commit `admin/stores/` build output and push for GitHub Pages. `npm run preview:homepage` → http://127.0.0.1:8000/ → click a chip → success toast; custom store → moderation message. Approve in `/admin/stores/` → store appears for public voting. Check `store_vote_items.vote_count` increments.
Related files: `supabase/migrations/20260707_store_vote_items.sql`, `supabase/functions/admin-store-actions/`, `src/admin/stores/`, `index.html`, `homepage.js`, `styles.css`

### Homepage tracker link copy (variant 3 chosen)

Date discovered: 2026-07-07
Context: Homepage hero tracker CTAs felt too formal ("price trackers"); user explored 5 casual copy options via on-page switcher.
What happened: Static "Price trackers" label + "Safeway price tracker" buttons did not explain live tracking in a playful tone. User chose **variant 3** with button text tweak ("Scroll through the … aisle").
Fix / workaround: Final copy is static in `index.html` hero tracker card, intro: "Hop into the live aisles we've got going:"; buttons: "Scroll through the Safeway aisle" / "Scroll through the Vons aisle". Exploration switcher (`TRACKER_COPY_VARIANTS`, `?trackerCopyVariant=`, `sta_tracker_copy_variant`) removed for production. Store vote copy: "Where should we track prices next?" + lead about voting for where to add tracking.
How to verify: `npm run preview:homepage` → http://127.0.0.1:8000/ → hero shows variant 3 copy; no Copy 1–5 switcher.
Related files: `index.html`, `homepage.js`, `styles.css` (`.hub-hero-trackers-intro`)

### Homepage unstyled + old hero copy (stale cache / dead preview server)

Date discovered: 2026-07-07  
Context: Safari preview at http://127.0.0.1:8000/ showed Times New Roman, plain blue links, old "Safeway price tracker" / "Vons price tracker" buttons, no store-vote module.  
What happened: Two issues stacked: (1) **stale HTML**, browser cached `index.html` from commit `222a841` (before store-vote + variant-3 copy in `a6a8aa7`); (2) **CSS not applied**. Preview server not running (`curl` → connection refused) and/or browser cached a failed `styles.css` request from an earlier deploy window. Commit `5e7a525` fixed this with `/styles.css?v=hub1` but `fab8fdd` reverted to relative paths. `styles.css` itself has no syntax errors (3565 lines, braces balanced). Production https://scrollingtheaisle.com/ serves current HTML + CSS 200.  
Fix / workaround: Re-applied root-absolute cache-busted asset paths: `/styles.css?v=hub2`, `/homepage.js?v=hub2`, `/data/homepage-preview.generated.json`. Run **`npm run preview:homepage`** in your own terminal (repo root) and hard-refresh (Cmd+Shift+R). Do not open `index.html` via `file://`.  
How to verify: `curl -s http://127.0.0.1:8000/ | grep hub2` shows cache-busted links; page shows styled hero, "Scroll through the … aisle" CTAs, store-vote chips.  
Related files: `index.html`, `homepage.js`, `styles.css`, `package.json` (`preview:homepage`)

### Must bump `?v=` in index.html when editing homepage.js / styles.css

Date discovered: 2026-07-08  
Context: Updated `homepage.js` + `styles.css` (handpicked-deals custom badges + top-8 expander) but the local preview kept showing the OLD version even after reloads.  
What happened: `index.html` references assets with version query strings (`/homepage.js?v=hub2`, `/styles.css?v=hub3`). Editing the files WITHOUT bumping the `?v=` means the browser keeps serving the cached asset for that exact URL. The server log showed no re-fetch of `homepage.js?v=hub2` on reload. This also affects the deployed site, not just local.  
Fix / workaround: Whenever you change `homepage.js` or `styles.css`, bump their `?v=` tokens in `index.html` (e.g. `hub2`→`hub3`, `hub3`→`hub4`). Then a normal load fetches the new asset (new cache key).  
How to verify: `rg "homepage\.js\?v=|styles\.css\?v=" index.html` shows the new tokens; reload the preview and confirm the change appears (server log shows a GET for the new `?v=` URL).  
Related files: `index.html`, `homepage.js`, `styles.css`

### GitHub Pages sometimes doesn't build after a push (re-trigger with empty commit)

Date discovered: 2026-07-08
Context: Pushed commit `286efec` (disclaimer "- Evelyn") to `origin/main`; live https://scrollingtheaisle.com/ kept serving the old text ~25 min later.
What happened: Local + `origin/main` were correct (`HEAD == origin/main == 286efec`, text present). But the live `last-modified` (14:43:12 GMT) predated the commit (14:56:44 GMT), and served `content-length` was 7088 vs local 7097 (exactly the 9 bytes of " - Evelyn"). Cache-busting query strings did NOT help. The **origin** itself was stale. Root cause: GitHub Pages never created a deployment for the pushed commit. The GitHub API (`/deployments`) showed the newest `github-pages` deployment was still the PRIOR commit `f372bbd` (state `success`), with no deployment for `286efec`. This site uses legacy branch-based Pages (no `.github/workflows/`, serves `main` root, CNAME `scrollingtheaisle.com`), which normally auto-builds on push but occasionally misses one.
Fix / workaround: Push an empty commit to force a rebuild: `git commit --allow-empty -m "Re-trigger GitHub Pages build" && git push origin main`. Use `--allow-empty` (not a normal commit) so the large uncommitted working-tree changes aren't swept in. Build completed ~30-60s later and live text updated (content-length 7097, `last-modified` matched the new push).
How to verify: `curl -s https://scrollingtheaisle.com/index.html | grep -o "check back often[^<]*"` shows `check back often. - Evelyn`; deployment API newest sha matches `git rev-parse origin/main`: `curl -s https://api.github.com/repos/helloevelynshares/scrollingtheaisle-site/deployments?per_page=1`.
Related files: `CNAME`, `index.html`, `finds.html`, `about/`, `about.html` (redirect), `submit.html` (no workflow file: Pages builds `main` root directly)


Date discovered: 2026-07-06  
Context: Previewing repo root `index.html` in Safari at http://127.0.0.1:8000/.  
What happened: Agent-started `python3 -m http.server 8000` in background shells dies when the agent/subagent session ends, so Safari shows "can't connect" even though it worked briefly.  
Fix / workaround: Run **`npm run preview:homepage`** in your own terminal tab (repo root) and leave it open. Optional detached server: `nohup python3 -m http.server 8000 --bind 127.0.0.1 > /tmp/scrolling-homepage-preview.log 2>&1 &`: PID in `/tmp/scrolling-homepage-preview.pid`. Stop: `kill $(cat /tmp/scrolling-homepage-preview.pid)` or Ctrl+C in the terminal running npm.  
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
# 3. Validate, catches keyword false matches and price outliers
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

### Product-matching eval scaffold (dry-run, not production)

Date discovered: 2026-07-25  
Context: Accumulate labeled match corrections without changing `generate_weekly_ad_prices.py`.  
What happened: Prior fixes lived in YAML, PROJECT_NOTES prose, and fragile sibling-repo CSV edits; no machine-readable eval set.  
Fix / workaround: Isolated scaffold under `scripts/product_matching/` + `data/product_matching/`. Run `PYTHONPATH=scripts python3 -m product_matching.eval_runner`. After any human match correction: append a line to `eval_cases.jsonl` and a row to `corrections.yaml` (see `docs/product_matching.md`). Production matcher does not read these files yet. Four open `baseline_bug` rows document wrong Vons rank-1 SKUs (Hershey’s→Ben & Jerry’s, Malt-O-Meal→Cheerios, BJ non-dairy→Häagen-Dazs, Miss Vickie’s→Kettle Brand) for a separate baseline fix.  
How to verify: Eval prints precision/recall + failure list; exit 2 if incorrect automatic accepts remain.  
Related files: `docs/product_matching.md`, `data/product_matching/eval_cases.jsonl`, `data/product_matching/corrections.yaml`, `scripts/product_matching/eval_runner.py`

Playwright setup: `pip install -r scripts/requirements.txt && playwright install chromium`

### Costco price data for grocery vs Costco comparisons

Date discovered: 2026-06-14  
Context: `price_comparisons` backfill and badge on `/staging-price-tracker/`.  
What happened: Costco warehouse CSVs live outside this repo at `~/Documents/costco-mvp/costco_data` (flat `{date}_{location}_consolidated.csv` plus older per-category CSVs). Default consolidated searches are `cracker chip protein chicken`. Produce/eggs/soda often have no Costco row until more terms are crawled.  
Fix / workaround: Run `python3 scripts/backfill_price_comparisons.py` (override path with `COSTCO_DATA_ROOT`). Maps Safeway → `san-francisco` / `costco_sf`, Vons → `tustin` / `costco_oc`. Writes `supabase/migrations/20260617_price_comparisons_seed.sql` + `src/data/priceComparisons.generated.ts`. Apply schema migration `20260616_price_comparisons.sql` before seed.  
How to verify: Backfill log shows item counts per location; cards show badges like "Via Safeway", "Via Costco", or "Not found at Costco" (scoped to the active grocery tab vs Costco. Never cross-compares Safeway vs Vons). Re-run is idempotent (`on conflict` upsert).  
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
What happened: Families are separate from the 18 `canonical_products` rows: `haagen_dazs_ice_cream` stays as single-SKU; families use new IDs (`ben_jerrys_ice_cream`, `ritz_crackers_snacks`).  
Fix / workaround: Definitions in `src/data/trackerFamilies.ts`; weekly ad matchers in `scripts/generate_weekly_ad_prices.py` write `src/data/familyWeeklyAdPrices.generated.ts` (family + per-member prices). UI merges via `appendFamiliesToFeedProducts()` in `trackerFamilyUtils.ts`. Not yet in Supabase `canonical_products`. Ritz Costco copy uses static warehouse reference ($10.79 / 61.6 oz) with 10%/25% thresholds in `getFamilyComparisonBadge()`.  
How to verify: `npm run build:price-tracker`; Safeway tab → "Handpicked deal families" section with B&J range chart and Ritz "Best value: Costco" / "More variety" badge.  
Related files: `src/data/trackerFamilies.ts`, `src/data/trackerFamilyUtils.ts`, `src/data/familyWeeklyAdPrices.generated.ts`, `src/staging-price-tracker/ProductCard.tsx`

### Weekly ad video brief workflow (watchlist-first)

Date discovered: 2026-06-24  
Context: Repeatable creator workflow for Bay Area Safeway + SoCal Vons/Albertsons short-form scripts.  
What happened: Price tracker already had canonical products, weekly ad matchers, and Costco comparison modules. But no market-scoped brief generator. Legacy `safeway_tracked_items_v1.csv` (50 TikTok SKUs) is separate from the live 18+2 tracker.  
Fix / workaround: **Option B**: `config/content_watchlist_overrides.csv` references existing `canonical_product_id` / `canonical_category_id` (families) for video metadata only. Markets in `config/markets.json` (`bay_area`, `socal_oc`). Run:

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
How to verify: `python3 -c "from pypdf import PdfReader; print(len(PdfReader('safeway_ad.pdf').pages[0].extract_text() or ''))"`. Expect >0 for text PDFs.  
Related files: `scripts/weekly_ad_analysis/ad_loader.py`, `data/weekly_ads/{week}/bay_area/`

### Verify weekly-ad PDFs: extract the embedded image, don't rely on fitz page render

Date discovered: 2026-07-08  
Context: Manually verifying the raw ad text of a specific tile (Vons 7/8 page-1 digital-coupon sidebar) against the vision pipeline's `split_offer_items.csv`.  
What happened: `page.get_pixmap(...)` (any DPI, with/without clip) rendered the page but **dropped the red digital-coupon sidebar**. The sidebar came back pure white, so crops looked blank even though a low-DPI full render once showed it. These Albertsons flyers are a **single full-page JPEG** placed on the PDF page; the page-level render was unreliable for the sidebar region.  
Fix / workaround: Pull the embedded image directly instead of rendering the page: `xref = page.get_images(full=True)[0][0]; d = doc.extract_image(xref); Image.open(io.BytesIO(d['image']))`. Then crop with PIL (open the saved PNG; `Image.frombytes` mis-handles alpha/channels and yields garbage). This gave the true flyer at 917×1792 with the full sidebar.  
How to verify: after extracting, check content coverage of the sidebar band, e.g. `numpy` mean of `(rgb[:, int(W*0.8):].sum(2) < 720)` should be well above 0 (was ~0.82 vs 0.0 for the page render).  
Related files: `inputs/weekly_ads/*.pdf` (sibling `scrolling-the-aisle` repo), `scripts/_tmp_fresh_costco_report_jul8.py`

### Vision pipeline mislabels single-serve multipack coupons as regular cookies

Date discovered: 2026-07-08  
Context: Chips Ahoy / Nabisco audit for the 2026-07-08 weekly-deal reanalysis.  
What happened: The Vons page-1 digital coupon **"Nabisco Single Serve Snacks, 10 ct." $3.99** (imagery: Oreo Mini / Mini Chips Ahoy / Nutter Butter Bites) was extracted as **"Oreo or Chips Ahoy! Cookies 10-15.35 oz $3.99"**. Wrong product AND a fabricated size (the "10" is the *10-count*, not oz). Both the `Oreo` and `Chips Ahoy! Cookies` split rows traced to the *same* `raw_offer_id`, so there was no real separate Oreo family-size deal. Meanwhile the Safeway page-5 tile was a genuine regular Chips Ahoy pack, but its size was extracted as `7-13 oz` when the PDF says `9.5 to 13-oz.`.  
Fix / workaround: Treat single-serve / mini multipack snack coupons as their own `pack_type` (`single_serve_pack`) and **never** merge them with regular cookie packs or feed them into the `chips_ahoy` / `oreo_family_size` canonical trackers. Guardrail `cookie_pack_types_not_merged` is documented in the deal report + comparison audit. Attach per-item provenance (`source_pdf`, `source_page`, `raw_offer_text`, `parsed_*`, `pack_type`, `confidence`) and re-verify against the PDF before scripting.  
How to verify: `output/weekly_deals/2026-07-08/fresh_costco_comparison_audit.md` (Vons rows show `single_serve_pack`, size `10 ct`, not `10-15.35 oz`); the report's shortlist marks these `[CORRECTED]` and routes them to "Manual verification first".  
Related files: `output/weekly_deals/2026-07-08/fresh_costco_deal_report.md` (source of truth), `scripts/_tmp_fresh_costco_report_jul8.py`

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
   Requires `OPENAI_API_KEY` in sibling-repo `.env`. Pipeline may exit 1 on `summary_report.py` bug after writing `split_offer_items.csv`. Merge output anyway. Row counts: Safeway 208, Vons 163 for `2026-06-24`.
How to verify: Audit, expect 208 Safeway + 163 Vons rows for `2026-06-24`, 223 + 115 for `2026-07-01`. `grep 2026-07-01 src/data/weeklyAdPrices.generated.ts`. `npm run build:price-tracker` then check chart x-axis on `/staging-price-tracker/`.  
Related files: `data/weekly_ads/flyer_manifest_*.csv`, `~/Documents/scrolling-the-aisle/outputs/product_discovery_*/split_offer_items.csv`, `src/data/weeklyAdPrices.generated.ts`, `src/data/vonsWeeklyAdPrices.generated.ts`, `src/data/familyWeeklyAdPrices.generated.ts`, `supabase/migrations/20260610_price_tracker_seed.sql`, `supabase/migrations/20260615_vons_weekly_observations_seed.sql`


Date discovered: 2026-07-02  
Context: SoCal Vons weekly ad historical benchmarking for existing STA food watchlist + additive category mappings.  
What happened: Need Vons-only historical labels (all-time low, near low, etc.) separate from Costco-first weekly brief workflow.  
Fix / workaround: Run `npm run vons-historical-low-check` (or `python3 scripts/analysis/vons_historical_low_check.py`). Uses `config/vons_historical_low_category_mappings.csv` (additive. Does not modify canonicalProducts.ts). Historical rows from `scrolling-the-aisle/outputs/product_discovery_vons*/split_offer_items.csv`. Current week needs vision-extracted split_offer CSV (PDF alone is not enough). July 2026 week input: `data/weekly_ads/2026-07-01/socal_oc/split_offer_items.csv`.  
How to verify: `python3 -m unittest tests.test_vons_historical_low_check -v` then inspect `outputs/vons_2026-07-01_historical_low_candidates.csv`.  
Related files: `scripts/analysis/vons_historical_low_check.py`, `config/vons_historical_low_category_mappings.csv`, `tests/test_vons_historical_low_check.py`


### YAML tracker families migration (66 families)

Date discovered: 2026-07-05  
Context: Migrate from ~20 hardcoded `canonical_products` to `data/canonical_tracker_families.yaml`.  
What happened: Tracker cards, weekly-ad matchers, homepage sections, and Popular this week now read from YAML via `scripts/generate_canonical_families.py` → `src/data/canonicalTrackerFamilies.generated.ts`. Weekly ad prices keyed by family id (`doritos_5_13oz`, etc.); legacy canonical rows merged via `LEGACY_CANONICAL_TO_FAMILY` in `scripts/price_tracker/canonical_families.py`.  
Fix / workaround: Edit YAML → `npm run generate:canonical-families` → `npm run generate:weekly-ad-prices` → `npm run build:price-tracker`. Runbook: `docs/YAML_TRACKER_MIGRATION_RUNBOOK.md`. Safeway/Vons UI uses static `yamlFamilyProducts.ts` (no Supabase required). Costco/backfill still maps via legacy canonical ids until extended.  
How to verify: `PYTHONPATH=scripts python3 -m unittest tests.test_canonical_families tests.test_normalization tests.test_ui_copy -v`; open `/staging-price-tracker/`. Five section chips, search, Popular this week.  
Related files: `data/canonical_tracker_families.yaml`, `data/popular_this_week.yaml`, `scripts/price_tracker/`, `src/data/yamlFamilyProducts.ts`, `src/staging-price-tracker/SectionedTrackerList.tsx`



Date discovered: 2026-07-05  
Context: `supabase db push` after adding Costco price comparison seed.  
What happened: Two files shared prefix `20260616` (`20260616_price_comparisons.sql` + `20260616_price_comparisons_seed.sql`). Remote `schema_migrations` already had version `20260616` for the schema migration; push failed with duplicate version.  
Fix / workaround: Give seed its own version (`20260617_price_comparisons_seed.sql`). Schema stays `20260616`. Seed data can also be applied manually: `supabase db query --linked -f supabase/migrations/20260617_price_comparisons_seed.sql` (idempotent upserts). `backfill_price_comparisons.py` writes the `20260617_…` path.  
How to verify: `supabase db push --dry-run` lists only `20260617_price_comparisons_seed.sql` pending; no duplicate-version error.  
Related files: `supabase/migrations/20260616_price_comparisons.sql`, `supabase/migrations/20260617_price_comparisons_seed.sql`, `scripts/backfill_price_comparisons.py`


### Weekly ad import: use system Python + banner+start --only-file token

Date discovered: 2026-07-14
Context: Importing Safeway/Vons Jul 15–21 ads via `scripts/import_weekly_ad.py`.
What happened: (1) Site `.venv` lacks sibling vision deps (`pandas`/`openai`) so extraction crashed immediately. (2) `--only-file` used the end date (`7-21`), which matched **both** PDFs and started processing Vons during the Safeway run. (3) Prior week pollution: Vons Jul 8 rows (118) were sitting in the Safeway consolidated `split_offer_items.csv`; Vons consolidated was missing 7-08 and had an incomplete 6-24 (22 vs 163). (4) Vons merge failed once on ragged CSV `None` keys.
Fix / workaround:
1. Run `/usr/bin/python3 scripts/import_weekly_ad.py ...` (or any env with sibling `requirements.txt`).
2. `--only-file` token is now `safeway 7-15` / `vons 7-15` (banner + week-start).
3. Merge keeps only the target banner in each consolidated cache; union fieldnames and drop `None` restkeys.
4. If Safeway cache contains Vons rows, move them into the Vons cache before rematch.
How to verify: Extraction plan shows `Flyers to process: 1 / 1` for each banner; `verify-only` reports PREVIEW before week start; no Vons banner rows in Safeway `split_offer_items.csv`.
Related files: `scripts/import_weekly_ad.py`, `docs/PROJECT_NOTES.md` (Weekly ad preview workflow), sibling `outputs/product_discovery_{safeway,vons}/split_offer_items.csv`


Date discovered: 2026-07-07
Context: First time loading a weekly ad before its effective start date (Jul 8–14 ad imported on Jul 7).
What happened: Price tracker had no concept of preview vs active ad weeks; UI said "this week" for prices that were not yet in stores.
Fix / workaround:
1. **Import orchestrator:** `/usr/bin/python3 scripts/import_weekly_ad.py --week-start YYYY-MM-DD --week-end YYYY-MM-DD --safeway-pdf "safeway …pdf" --vons-pdf "vons …pdf"`. Use **system Python** (or any env with sibling-repo deps: pandas/openai/PyMuPDF), not the site `.venv` which lacks them. Updates manifests (site + sibling repo), runs vision extraction (`discover_product_candidates.py` with `--only-file` banner+start token e.g. `safeway 7-15` — not bare end-date `7-21`, which matches both banners), merges banner-filtered rows into sibling `split_offer_items.csv`, regenerates TS. Use `--skip-extraction` when CSV already exists; `--verify-only` to audit counts.
2. **Preview detection:** Ad weeks soft-start **one calendar day early** so late night-before publishes are ACTIVE (no Preview chrome). Preview only when `today < week_start − 1 day`. Active window: `week_start − 1 day` through `week_end`. When the ending week and soft-started next week both match, UI picks the **latest** via reverse sort (`getCurrentWeeklyPrice`). Python: `scripts/price_tracker/weekly_ad_preview.py`. TypeScript: `src/data/weeklyAdPreview.ts` + `isPreviewWeek` on each `WeeklyPrice` in `yamlFamilyProducts.ts`.
3. **UI:** `WeeklyAdPreviewBanner` below feed tabs. Card Preview callout / green deal styling only when the upcoming real ad match **beats this week's charted price** (`hasHighlightablePreviewDeal`). Preview label must use the upcoming week's price (graph point), not this week's. Non-improving or unmatched upcoming weeks still plot on the chart (ad point or baseline fill) but keep "this week" / usual copy without Preview green. Helpers: `getPreviewWeeklyPrice`, `getPriorAdWeekPriceForPreview`, `hasHighlightablePreviewDeal` in `priceTrackerUtils.ts`. `saleRangeFromWeekly` must ignore preview weeks.
4. **Safeguards:** `generate_weekly_ad_prices.py` validates canonical product IDs unchanged (66 families) before/after; logs matched/unmatched per feed.
Weekly command (Jul 15–21 example):
```bash
/usr/bin/python3 scripts/import_weekly_ad.py \
  --week-start 2026-07-15 --week-end 2026-07-21 \
  --safeway-pdf "safeway 7-15 - 7-21.pdf" \
  --vons-pdf "vons 7-15 - 7-21.pdf"
npm run verify:weekly-ad
npm run audit:weekly-ad-import -- --week-start 2026-07-15
npm run build:price-tracker
```
Verify: `/usr/bin/python3 scripts/import_weekly_ad.py --verify-only` → tracked product count unchanged; PREVIEW when `--as-of` is **two+ days** before week start; ACTIVE on the night before (`--as-of` = week_start − 1). `PYTHONPATH=scripts python3 -m unittest tests.test_weekly_ad_preview -v`. After import, read `output/weekly_deals/{week}/import_qa_audit.md` for crop price overrides and tracked WoW worsens before publishing.
Related files: `scripts/import_weekly_ad.py`, `scripts/price_tracker/weekly_ad_preview.py`, `src/data/weeklyAdPreview.ts`, `src/staging-price-tracker/WeeklyAdPreviewBanner.tsx`, `data/weekly_ads/flyer_manifest_*.csv`

### Night-before publish: one-day early ACTIVE window (no Preview)

Date discovered: 2026-07-28  
Context: Publishing Safeway week `2026-07-29` late on Jul 28; user wanted live "this week" prices with no Preview banner/labels.  
What happened: Strict `today < week_start` still marked Jul 29 as preview on Jul 28, while Jul 22–28 remained calendar-active through end of Jul 28 — so `getCurrentWeeklyPrice` would keep showing the old week even if Preview chrome were forced off.  
Fix / workaround: Soft-start ad weeks one calendar day early in both TS (`weeklyAdPreview.ts`) and Python (`weekly_ad_preview.py`). On the night before, both the ending week and the next week can be "active"; reverse-sort picks the latest (`2026-07-29`). Two+ days early still PREVIEW.  
How to verify: `PYTHONPATH=scripts python3 -m unittest tests.test_weekly_ad_preview.TestWeeklyAdPreviewDates -v` (Jul 28 → Jul 29 ACTIVE / not preview). After build, tracker shows Jul 29 prices as this week with no Preview banner.  
Related files: `src/data/weeklyAdPreview.ts`, `scripts/price_tracker/weekly_ad_preview.py`, `tests/test_weekly_ad_preview.py`

### Preview highlight only when beating this week's price

Date discovered: 2026-07-14  
Context: Jul 15–21 ad in preview while Jul 8–14 is still the active store week.  
What happened: Cards showed "Preview: $2.50 starting tomorrow" for Doritos/Ruffles/Oreo even when the Jul 15 graph point was $5.99 (worse) or baseline (unmatched). Root cause: preview UI used the preview-week *flag* with *this week's* price, and `isProductInPreviewWeek` is true for every product once any upcoming week exists. Also, comparing to an older ad week (e.g. Goldfish Jul 1 at $2) blocked highlighting a Jul 15 $2.49 deal that beats this week's baseline $3.99.  
Fix / workaround: Use `hasHighlightablePreviewDeal` — real upcoming ad match AND `preview.price < getCurrentWeeklyPrice().price` (this week's chart point). Otherwise keep this-week/usual labels; still plot the upcoming point. Wire green Preview styling through that helper in `FamilyDealCard`.  
How to verify: As of Jul 14, Ruffles/Oreo (no improving Jul 15 match) stay on this-week/usual copy; Doritos after price correction → `Preview: $2.49 starting tomorrow`; Goldfish/Cherries also Preview.  
Related files: `src/data/priceTrackerUtils.ts`, `src/data/trackerFamilyUtils.ts` (`saleRangeFromWeekly`), `src/staging-price-tracker/FamilyDealCard.tsx`

### Doritos Jul 15 $5.99 was seafood price bleed

Date discovered: 2026-07-14  
Context: Safeway Jul 15–21 page-1 coupon grid. Real tile: Lay's / Lay's Kettle / PopCorners / Doritos **5–10.75 oz @ $2.49** clip-or-CLICK Mix & Match. Directly above: Waterfront Bistro shrimp/salmon **$5.99**.  
What happened: Vision wrote Doritos as `4.5-8 oz @ $5.99 MEMBER PRICE` (`raw_offer_id` a995d9904a92, `crop_override_price`). Matcher accepted it onto `doritos_5_13oz`, so the graph showed $5.99 instead of the regular-size $2.49 deal.  
Fix / workaround: Manually correct the sibling `split_offer_items.csv` row (price 2.49, size 5–10.75 oz, promo clip-or-CLICK), then `/usr/bin/python3 scripts/generate_weekly_ad_prices.py --product-ids doritos_5_13oz --feed safeway` (incremental merge updates differing weeks).  
How to verify: `doritos_5_13oz["2026-07-15"].price === 2.49` in `weeklyAdPrices.generated.ts`; offerText mentions PopCorners / 10.75.  
Prevention: After each import run `/usr/bin/python3 scripts/audit_weekly_ad_import.py --week-start YYYY-MM-DD` (also auto-runs at end of `import_weekly_ad.py`). It lists crop first-pass→final price raises (bleed risk) and tracked week-over-week worsens. Dedicated raw cards still showed `original 2.49 → verified 5.99` for this tile.  
Related files: `scripts/audit_weekly_ad_import.py`, `~/Documents/scrolling-the-aisle/outputs/product_discovery_safeway/split_offer_items.csv`, `src/data/weeklyAdPrices.generated.ts`, flyer `safeway 7-15 - 7-21.pdf` p1

### Goldfish Jul 15 $2.49 was Ritz price bleed (real tile $1.99)

Date discovered: 2026-07-15  
Context: Safeway Jul 15–21 page-3 clip-or-CLICK grid. Real tile: **Pepperidge Farm Goldfish Crackers or Crisps 4 to 8-oz @ $1.99 ea** Member Price. Neighbor below: Ritz / Cheez-It @ **$2.49**.  
What happened: Vision extracted Goldfish as `6.1-8 oz @ $2.49` (same price as Ritz; size also drifted). Crop PNG for offer 12 cut the price text; first-pass + crop verify still agreed on $2.49. Tracker correctly matched that wrong row → chart showed $2.49.  
Fix / workaround: Manually correct dedicated + consolidated `split_offer_items.csv` (and dedicated `raw_offer_cards.csv`) to $1.99 / 4 to 8-oz / clip-or-CLICK, then `python3 scripts/generate_weekly_ad_prices.py --product-ids goldfish_bags --feed safeway`. Then **`npm run build:price-tracker`** and commit `grocery-price-tracker/` (see next note).  
How to verify: `goldfish_bags["2026-07-15"].price === 1.99`; offerText includes Pepperidge Farm / 4 to 8-oz; promoNote mentions clip or CLICK. Confirm on flyer PDF page 3. In `grocery-price-tracker/assets/index-*.js` search goldfish Jul 15 → `price:1.99`.  
Related files: `~/Documents/scrolling-the-aisle/outputs/product_discovery_safeway/split_offer_items.csv`, `.../product_discovery_safeway_safeway_7-15_-_7-21/`, `src/data/weeklyAdPrices.generated.ts`, `safeway 7-15 - 7-21.pdf` p3

### Rematch/source fix is not live until `grocery-price-tracker/` rebuild is committed

Date discovered: 2026-07-15  
Context: User still saw Goldfish at **$2.49** after commit `5ea2307` set `weeklyAdPrices.generated.ts` → `goldfish_bags["2026-07-15"]` to **$1.99**.  
What happened: GitHub Pages serves the prebuilt bundle under `grocery-price-tracker/` (synced from Vite via `scripts/sync-price-tracker-dist.mjs`). `5ea2307` updated source TS + audits but left `grocery-price-tracker/assets/index-BRs2cMuN.js` with the old `price:2.49` (last built in `da12eed`). Default feed is Safeway (`safeway_bay_area`); Vons still has no Jul 15 Goldfish ad match (baseline). Preview vs current-week logic was fine once the week became ACTIVE (Jul 15).  
Fix / workaround: After any weekly rematch or `weeklyAdPrices.generated.ts` change that should reach shoppers: `npm run build:price-tracker`, commit the new `grocery-price-tracker/` assets (and admin dist if rebuilt), push `main`. Hard-refresh `/grocery-price-tracker/` (or `/staging-price-tracker/` redirect).  
How to verify: `rg 'goldfish_bags:\{' -n grocery-price-tracker/assets/index-*.js` then confirm `"2026-07-15":{price:1.99`; live page Goldfish card shows ~$1.99 this week.  
Related files: `grocery-price-tracker/`, `scripts/sync-price-tracker-dist.mjs`, `package.json` (`build:price-tracker`), `src/data/weeklyAdPrices.generated.ts`

### Chips Ahoy Jul 15 missed because of bang in "Chips Ahoy!"

Date discovered: 2026-07-15  
Context: Safeway Jul 15–21 page-5 tile **Nabisco Chips Ahoy! Cookies 9.5 to 13-oz @ $2.49 ea** (Member Price; must buy multiples of 2 / Mix & Match Nabisco). Extraction was correct; tracker showed baseline only.  
What happened: YAML include phrases are `Chips Ahoy cookies` → regex requires whitespace between `ahoy` and `cookies`. Ad copy prints **`Chips Ahoy!`**, so `matches()` failed (0 include hits) even though eligibility/taxonomy already understood `chips_ahoy`.  
Fix / workaround: Strip trademark-style `!` alongside `®™©` in `split_text` / `row_text` (`_strip_trademark_punct` in `generate_weekly_ad_prices.py`). Rematch: `python3 scripts/generate_weekly_ad_prices.py --product-ids chips_ahoy --feed safeway`.  
How to verify: `chips_ahoy["2026-07-15"].price === 2.49`; `PYTHONPATH=scripts python3 -m unittest tests.test_split_text_trademark -v`.  
Related files: `scripts/generate_weekly_ad_prices.py`, `tests/test_split_text_trademark.py`, `src/data/weeklyAdPrices.generated.ts`, `data/canonical_tracker_families.yaml` (`chips_ahoy`)

### Chips Ahoy Jul 29 missed: unsplit Nabisco mix-tile + Oreo/Ritz hallucination

Date discovered: 2026-07-28  
Context: Safeway week `2026-07-29` page-1 clip-or-CLICK digital coupon: **Chips Ahoy! Cookies 7–13 oz + Nabisco Snack Crackers 3.5–9.1 oz @ $1.99 EA** (Member Price; Limit 4; 4x points). Tracker showed baseline only.  
What happened: (1) Vision wrote one `group_not_split` row as **"Nabisco Chips Ahoy! Cookies, Snack Crackers, Oreo or Ritz Crackers 3.5–13.7 oz"** — Oreo/Ritz were hallucinated; real tile is Chips Ahoy + snack crackers only (crop for offer 18 also mismatched onto Danish Butter). (2) Even with PDF-correct combined text, `chips_ahoy` `keep_separate_from` includes **Nabisco snack crackers** / Oreo / Ritz, so the unsplit blob cannot match. Not a bang/`!` miss (that was Jul 15).  
Fix / workaround: Correct the group row text in dedicated + consolidated `split_offer_items.csv`; add Chips Ahoy–only manual split (`split_item_id=049ce2fe83ac`, `split_product_text="Nabisco Chips Ahoy! Cookies 7-13 oz."`, `advertised_price=1.99`, `review_reasons=manually_added_missed_tile|manual_pdf_verified_2026-07-28`). Rematch + `npm run build:price-tracker`. Do **not** attach standard 3.5–9.1 oz snack crackers to `nabisco_snack_crackers` (family-size-only).  
Prevention: (1) After import run `PYTHONPATH=scripts /usr/bin/python3 scripts/detect_missed_deals.py --week YYYY-MM-DD` — medium `blocked_by_keep_separate` flags this class (brand present + keep_separate blocking + null chart). (2) PDF spot-check Oreo / Chips Ahoy / Nabisco Mix & Match tiles; if `group_not_split`, add family-only splits before publish. Do **not** loosen `keep_separate_from` to force a match.  
How to verify: `chips_ahoy["2026-07-29"].price === 1.99` with offerText `Nabisco Chips Ahoy! Cookies 7-13 oz.`; audit accepts confidence 1.00. PDF: `safeway 7-29 - 8-4.pdf` p.1 right-rail coupon. `PYTHONPATH=scripts python3 -m unittest tests.test_detect_missed_deals.TestKeepSeparateBlockedMiss -v`.  
Related files: sibling `product_discovery_safeway*/split_offer_items.csv` (`049ce2fe83ac` / `4dbee9be22e1`), `src/data/weeklyAdPrices.generated.ts`, `data/canonical_tracker_families.yaml` (`chips_ahoy`), `scripts/detect_missed_deals.py`, `output/weekly_deals/2026-07-29/canonical_match_audit.md`

### Regular-size Nabisco snack crackers tracker (separate from family-size)

Date discovered: 2026-07-28  
Context: Safeway ads often print **"Nabisco Snack Crackers" 3.5–9.1 oz** for the regular-size Wheat Thins / Triscuit / Chicken in a Biskit trio (UI shows brand names; ad copy is the Nabisco block label). Family-size stays on `nabisco_snack_crackers` (11.5–14 oz). Jul 29 Mix & Match was Chips Ahoy 7–13 oz + snack crackers 3.5–9.1 oz @ $1.99; Chips Ahoy got split `049ce2fe83ac`, crackers needed their own split.  
What happened: Prior keep_separate on Chips Ahoy / family-size-only gating left regular-size weeks null (and blocked the crackers half of unsplit mix tiles).  
Fix / workaround:
1. New family `nabisco_snack_crackers_regular` — display **"Wheat Thins, Triscuit & Chicken in a Biskit — regular size"**; size **3.5–9.1 oz**; includes Nabisco Snack Crackers + brand names (Biskit/Biscuit spellings); Safeway baseline **$5.49**.
2. Match rules require regular-size band confirmation; keep_separate family-size / Chips Ahoy / Oreo / Ritz / Belvita / Kettle siblings.
3. Manual splits: Jul 29 `7b3e1a90c2d4` (crackers half), Jun 17 `a1c4e8f02b67`; cleaned Jun 3 Wheat Thins/Triscuit package_text.
How to verify: `nabisco_snack_crackers_regular["2026-07-29"].price === 1.99`; family-size `nabisco_snack_crackers["2026-07-08"].price === 3.49` unchanged. `PYTHONPATH=scripts python3 -m unittest tests.test_canonical_match_eligibility.TestNabiscoRegularSizeSnackCrackers tests.test_canonical_families -v`.  
Related files: `data/canonical_tracker_families.yaml`, `config/canonical_match_rules.yaml`, `src/data/priceTrackerFallback.ts`, sibling `split_offer_items.csv`, `src/data/weeklyAdPrices.generated.ts`

### Lay's / Lay's Kettle Jul 15 missed: unsplit Mix & Match + abbreviated names

Date discovered: 2026-07-15  
Context: Safeway Jul 15–21 page-1 clip-or-CLICK Mix & Match: **Lay's, Lay's Kettle, PopCorners or Doritos 5–10.75 oz @ $2.49** (same tile Doritos was price-bleed–corrected earlier). Tracker showed baseline for Lay's regular + Lay's Kettle.  
What happened: Row stayed `group_not_split` with abbreviated flyer names. Doritos matched via bare `\bdoritos\b`. Lay's regular includes require **Lay's potato chips** / flavor names (not bare `Lay's`). Lay's Kettle includes required **Lay's Kettle Cooked …** (ads say `Lay's Kettle` or `Kettle Cooked Chips`). So `matches()` returned 0 include hits.  
Fix / workaround:
1. Split sibling rows in consolidated + dedicated `split_offer_items.csv` (`raw_offer_id=a995d9904a92`): Lay's Potato Chips / Lay's Kettle Cooked Chips / PopCorners / Doritos @ $2.49.
2. YAML: broaden `lays_kettle_cooked` includes (`Lay's Kettle`, `Kettle Cooked Chips`, etc.); add `Lay's Kettle` to regular Lay's `keep_separate_from`; add new family `popcorners`.
3. Eligibility/taxonomy: kettle + popcorners rules; `lay's kettle` → `kettle_cooked` type.
4. Rematch: `PYTHONPATH=scripts python3 scripts/generate_weekly_ad_prices.py --product-ids lays_potato_chips_regular,lays_kettle_cooked,popcorners,doritos_5_13oz --feed safeway` (+ `--feed vons` for new family scaffold).
5. PopCorners Safeway baseline: estimate **$4.29** (same-aisle Lay's/Doritos shelf anchor) until a crawl with fresh `SAFEWAY_COOKIE`.
How to verify: `lays_potato_chips_regular` / `lays_kettle_cooked` / `popcorners` / `doritos_5_13oz` all have `["2026-07-15"].price === 2.49`. PopCorners also picks Safeway 2026-06-17 PopCorners split @ $2.49.  
Related files: sibling `split_offer_items.csv`, `data/canonical_tracker_families.yaml`, `config/canonical_match_rules.yaml`, `scripts/price_tracker/product_type_taxonomy.py`, `src/data/priceTrackerFallback.ts`, `src/data/weeklyAdPrices.generated.ts`

### Post-import QA: crop overrides + WoW worsens

Date discovered: 2026-07-14  
Context: Doritos crop verifier overwrote a correct first-pass $2.49 with adjacent seafood $5.99; need a habit + tool before publish.  
What happened: Manual flyer spot-checks are easy to skip; `needs_human_grounding` / `crop_override_price` rows are numerous.  
Fix / workaround:
1. `scripts/audit_weekly_ad_import.py` reads dedicated `raw_offer_cards.csv` (original vs verified price) + consolidated split tags + generated TS week-over-week matches.
2. Writes `output/weekly_deals/{week}/import_qa_audit.md` (+ `.json`).
3. `npm run audit:weekly-ad-import -- --week-start YYYY-MM-DD --fail-on-tracked-findings`. Flags bare `crop_tile_mismatch` for review; `--fail-on-tracked-findings` exits 1 on **WoW worsens + bleed-risk crop raises** (not every noisy mismatch).
4. `import_weekly_ad.py` runs the audit after generate and **fails the import** when `tracked_finding_count > 0`.
How to verify: For 2026-07-15, audit lists Doritos-class bleed from dedicated raw (`$2.49 → $5.99`) even after consolidated CSV was corrected. `PYTHONPATH=scripts /usr/bin/python3 -m unittest tests.test_audit_weekly_ad_import -v`.  
Related files: `scripts/audit_weekly_ad_import.py`, `scripts/import_weekly_ad.py`, `package.json` (`audit:weekly-ad-import`)

Date discovered: 2026-07-05  
Context: HTTP/curl pgmsearch via `seed_safeway_baseline.py`; prior `.env` used SF Jackson St store **4601 / 94111 / pickup** with Chrome UA + logged-in cookie. Requests failed or mismatched session.  
What happened: Working DevTools capture used **storeid=3132**, **zipcode=94611**, **channel=instore**, empty **visitorId**, Safari UA, guest cookie (`userType` **G**), no `sec-ch-ua` headers.  
Fix / workaround: Refresh `SAFEWAY_COOKIE` from that capture; set `SAFEWAY_STORE_ID=3132`, `SAFEWAY_ZIPCODE=94611`, `SAFEWAY_CHANNEL=instore`, Safari `SAFEWAY_USER_AGENT`, clear `SAFEWAY_VISITOR_ID` / `SAFEWAY_UUID`, comment out `SAFEWAY_SEC_CH_UA*`. Code defaults in `safeway_config.py` remain SF 4601/94111/pickup if env vars unset.  
How to verify: `.venv/bin/python scripts/seed_safeway_baseline.py --query "goldfish cheddar cracker" --timeout 30 -v` → `200 success`, candidates CSV populated (e.g. Goldfish Cheddar 10 Oz **$4.99**).  
Related files: `scripts/.env`, `scripts/safeway_config.py`, `scripts/safeway_client.py`, `scripts/seed_safeway_baseline.py`

### Weekly chart price must not exceed shelf baseline (peaches $4.49 Every Day)

Date discovered: 2026-07-14
Context: Peaches/nectarines Safeway charts spiked above the dashed baseline; user confirmed conventional Safeway shelf is **$2.99/lb**.
What happened: (1) Crawl baselines were sale scrapes (`peaches $1.50`, `nectarines $1.20`, also bad `plums $0.85`, `sweet_corn $0.13`, `Simply $3`). (2) Flyer **Every Day $4.49** / `price_role_guess=baseline_candidate` was written as a weekly “deal”. (3) Rematch of “Yellow Peaches or Nectarines” failed because `keep_separate_from` scanned full `raw_offer_text`.
Fix / workaround:
1. Set peaches/nectarines (and plums) baselines to **$2.99/lb**; fix corn/Simply estimate baselines in `priceTrackerFallback.ts` + Vons twin.
2. Generator drops everyday/shelf rows (`is_everyday_shelf_price_row`) and any unit price **> store baseline** (`week_price_from_row` / `pick_best_row`).
3. `matches()` excludes only against **split + package_text** (not raw), so mix-or-match siblings still match after split.
4. Validator `[above_baseline]` check via `load_feed_baselines`.
How to verify: Peach/nectarine Safeway week `2026-06-17` is **null** (Every Day); `2026-06-24` is **$1.99**; baseline line **$2.99**. Audit: no weekly price > baseline. `PYTHONPATH=scripts python3 -m unittest tests.test_everyday_shelf_filter tests.test_validate_weekly_ad_prices.TestAboveBaseline -v`.
Related files: `scripts/generate_weekly_ad_prices.py`, `scripts/validate_weekly_ad_prices.py`, `src/data/priceTrackerFallback.ts`, `src/data/weeklyAdPrices.generated.ts`

### Hass avocados Safeway 2026-04-01: $5 Friday misread as $5 each (was 5 for $5)

Date discovered: 2026-07-14
Context: Same failure class as Kettle Brand April 3 — chart showed $5 for Friday-only Hass avocados.
What happened: Vision stored `$5 ea` / `per_pack` for `Signature SELECT Hass Avocados or Cucumbers 5 ct`. PDF `$5 Friday` tile is a **5 for $5** multi-buy (~$1/ea). Prefer-score also favored plural “Hass avocados” Friday row over the same week’s **97¢** full-week avocado/mango deal.
Fix / workaround:
1. Corrected sibling CSV `raw_offer_id=8c8950291ca5` to `5 for $5 Friday April 3rd` / `multi_buy`.
2. Normalization: `Member Price: $X ea` override when cheaper than advertised; divide `N ct` pack totals; keep always-on `N for $X`.
3. `pick_lowest_in_week` for `hass_avocados_each` + `mangoes_each` so 97¢ beats a unitized Friday multi-buy.
4. Extended `[friday_multibuy]` validator to `produce` (not only snacks).
How to verify: April Safeway avocados chart point is **$0.97** (full-week), not $5; friday_multibuy no longer flags after regenerating. `PYTHONPATH=scripts python3 -m unittest tests.test_normalization.TestNormalization tests.test_validate_weekly_ad_prices.TestFridayMultibuySuspect -v`.
Related files: `scripts/price_tracker/normalization.py`, `scripts/price_tracker/yaml_matchers.py`, `scripts/validate_weekly_ad_prices.py`, `src/data/weeklyAdPrices.generated.ts`

### Kettle Brand Safeway 2026-04-01: $5 Friday misread as $5/bag (was 2 for $5)

Date discovered: 2026-07-14
Context: Kettle Brand chart on Safeway called out $5 for Friday April 3rd; user suspected multi-buy, not a single bag.
What happened: PDF page 6 `$5 Friday` tile is **SunChips / Kettle Brand Potato Chips 5–8.5 oz / Cheetos 6.5–10 oz** with **2 for $5** and Member Price **$2.50 ea**. Vision wrote `raw_offer_text="$5 ea …"`, `price_basis=each`, `advertised_price=5.0`, and dropped Cheetos from the split — so the tracker plotted **$5.00**.
Fix / workaround:
1. Corrected sibling `~/Documents/scrolling-the-aisle/outputs/product_discovery_safeway/split_offer_items.csv` (+ raw card) for `raw_offer_id=c9f97af3a547`: `2.50`, `multi_buy`, promo `2 for $5 Friday April 3rd`, add Cheetos split; use `Sun Chips 7 oz` wording.
2. `base_normalize_unit_price` always applies explicit `N for $X` even when `price_basis=each`.
3. Validator `friday_multibuy_suspect_check`: friday_only snack/chip at exactly **$5.00** with no `N for $X` in promo/offer → `[friday_multibuy]` flag.
4. Added YAML include `SunChips` (one word) for ads that omit the space.
How to verify: `kettle_brand_chips` / `sun_chips_7oz` / `cheetos_regular_bags` for `2026-04-01` → `price: 2.5`, promoNote `2 for $5 Friday April 3rd`. `PYTHONPATH=scripts python3 -m unittest tests.test_normalization tests.test_validate_weekly_ad_prices -v`. Re-run `validate_weekly_ad_prices.py --family-id kettle_brand_chips` → no friday_multibuy flag on April.
Related files: `scripts/price_tracker/normalization.py`, `scripts/validate_weekly_ad_prices.py`, `src/data/weeklyAdPrices.generated.ts`, sibling `split_offer_items.csv`

### Kettle Brand Safeway 2026-07-01: vision pipeline missed $5 Friday tile (fixed)

Date discovered: 2026-07-06  
Context: User reported "Kettle Brand potato chips 3 for $5" was on the $5 Friday page of the Safeway 7/1-7/7 ad, "under the strawberries and half pie." Previous investigation incorrectly concluded it was not there.  
What happened: The vision extraction pipeline captured 31 of 32 offer tiles on page 4 of the Safeway ad. The Kettle Brand Potato Chips tile was in a distinct layout row (approx. y=0.87-0.93) between the "Half Pie row" (y=0.81-0.87) and the "AriZona Tea row" (y=0.89-0.95). The extraction bounding-box detection skipped this row entirely. No raw_offer_card was created for it. Visual inspection of the PDF (rendered with PyMuPDF) confirmed the tile clearly shows: Kettle Brand Potato Chips, 5–8.5 oz., Selected varieties., Member Price $1.67 ea., Limit 3 items., **3 for $5 Member Price** (Friday July 3rd, $5 Friday block).  
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
1. **Stale match from pre-YAML migration**: The old `ProductMatcher` (before YAML families) matched "Kettle Brand Chips Party Size 11.25-13 oz." from a multi-item "Single Price Up To: $11.99" block on page 2 of the Vons 7-1 ad. After the YAML migration, the new patterns (requiring "Kettle Brand Sea Salt", "Kettle Brand Jalapeño", etc.) correctly produce 0 matches for that week. But the stale $11.99 remained because the incremental merge didn't overwrite it. The TS was regenerated from an old run.
2. **Wrong product size**: `kettle_brand_chips` tracks 6.5–8.5 oz bags; the Party Size is 11.25–13 oz. A completely different SKU at a different price point.
3. **Ceiling price, not a promotional price**: "Single Price Up To: $11.99" is the MSRP cap for a broad multi-product block (includes Tide, Totino's, sunscreen, etc.). Not a sale price.
4. **No "$5 Friday July 3rd" deal for Kettle Brand in either chain**: The user clarified the $3.45 deal was **Safeway-specific**, not Vons. Exhaustive search of BOTH Safeway bay_area and Vons socal_oc 2026-07-01 split_offer_items.csv AND raw_offer_cards.csv (all pages, all offers) found: NO Kettle Brand at $3.45 anywhere. The $5 Friday blocks in Safeway 7-1 cover: Pork Spareribs, Sushi, Salmon, Bacon, Caspers Hot Dogs, Strawberries, Peaches/Nectarines/Plums, Red Potatoes, Kinder's BBQ Sauce, Entenmann's Donuts, Popsicles, Sparkling Water/Tea, On the Rocks Cocktails, flowers: NOT chips. "Frito-Lay Lay's, Kettle Cooked, Sun Chips, Ruffles 4.75-8 oz. $1.99 ea" appears on page 3 of the Safeway 7-1 ad. But this is "Lay's Kettle Cooked" (a Frito-Lay variety), not the "Kettle Brand" brand (Kettle Foods/Cape Cod). The $3.45 price appears NOWHERE in any Safeway 7-1 extracted data; the only "3.45" hit is "14.76-23.45 oz" (a size range for Red Baron Pizza). The deal either appeared in-store only (not in the printed/digital weekly ad), or was a digital coupon not captured in the vision pipeline.
Fix / workaround:
1. Added "Kettle Brand Chips" and "Kettle Brand potato chips" to `include` in the YAML (so deals that say just "Kettle Brand Chips" without a specific flavor are matched).
2. Added "Kettle Brand Chips Party Size" and "Party Size" to `keep_separate_from` (excludes the large-format SKU and prevents ceiling/MSRP prices from contaminating the chart).
3. Ran `python3 scripts/generate_weekly_ad_prices.py --product-id kettle_brand_chips --feed vons`: 2026-07-01 now correctly shows null; 2026-05-06 also fixed (was wrongly showing $2.99 from "Lay's Kettle Cooked").
Design limitation: The chart plots one price per week. "Friday-only" intra-week dips (e.g., a $3.45 deal only on July 3rd) CANNOT be shown as a single-day dip. The chart would need daily granularity. Even if the $3.45 data existed, it would need `availability_type_guess: friday_only` in split_offer_items and a chart design change to show it as a Friday-only annotation instead of a full-week price.
How to verify: `grep '"2026-07-01"' src/data/vonsWeeklyAdPrices.generated.ts | head -5`. Kettle_brand_chips entry should have `"price": null`. Open chart on `/staging-price-tracker/` Vons tab → kettle_brand_chips. Should show baseline line (not a spike to $11.99).
Related files: `data/canonical_tracker_families.yaml` (`kettle_brand_chips`), `src/data/vonsWeeklyAdPrices.generated.ts`, `scripts/generate_weekly_ad_prices.py`, `data/weekly_ads/2026-07-01/socal_oc/split_offer_items.csv`

### B2G3F/BOGO deals need reference price in split_offer_items to normalize

Date discovered: 2026-07-06
Context: Doritos on Safeway 7/1 week reported "showing usual price instead of promotional effective price."
What happened: The Safeway 7/1 ad has a "BUY 2, GET 3 FREE Mix & MATCH" deal for "Lay's, Tostitos, Doritos or Simply 4.5–13 oz." with reference price $5.49 ea. The vision pipeline captured this deal in `raw_offer_cards.csv` (page 1, offer 3, `verified_*` fields) but it was NOT promoted to `split_offer_items.csv` because the crop-tile mismatch tagged it as an annotation on the adjacent Sweet Corn row. Two issues combined: (1) missing data row, and (2) `normalization.py` had no `buy_x_get_y` branch: `base_normalize_unit_price` only handled `multi_buy`, so any B2G3F/BOGO row with a price would have returned the raw reference price (e.g. $5.49) instead of the effective per-unit cost (2/5 × $5.49 = $2.20).
Fix / workaround:
1. Added `_buy_x_get_y_unit_price()` in `scripts/price_tracker/normalization.py`, parses "buy N get M free" from promo_text and computes `N/(N+M) × price`. Also handles bare "bogo" keyword.
2. Updated `base_normalize_unit_price()` to apply this logic when `price_basis` is `bogo` or `buy_x_get_y`.
3. Added the 3 missing split rows (Lay's, Tostitos, Doritos) with `advertised_price=5.49`, `price_basis=bogo`, `promo_text="BUY 2, GET 3 FREE Mix & MATCH"` to both `data/weekly_ads/2026-07-01/bay_area/split_offer_items.csv` (local copy) and `~/Documents/scrolling-the-aisle/outputs/product_discovery_safeway/split_offer_items.csv` (sibling repo consolidated, which is what `generate_weekly_ad_prices.py` reads).
4. Regenerated `src/data/weeklyAdPrices.generated.ts` with `--product-ids doritos_5_13oz,lays_potato_chips_regular,tostitos_tortilla_chips`.
Before/after for Safeway 7/1: `doritos_5_13oz` was `price: null` → now `price: 2.2` (confidence: high). Same for Lay's and Tostitos.
Vons 7/1: Vons also has a B2G3F for Lay's/Kettle/Poppables but with NO reference price in the vision extraction → still null. Vons Doritos 7/1 shows $2.50 (from "2 for $5" deal) which is correct and unaffected. Other historical B2G/BOGO rows (6/17 Lay's BOGO, 6/10 Tostitos BOGO) also have no price. Still null (pre-existing data limitation).
How to verify: `python3 -c "import json; ..."` or check `src/data/weeklyAdPrices.generated.ts`: `doritos_5_13oz["2026-07-01"]["price"]` should be `2.2`. All tests pass: `PYTHONPATH=scripts python3 -m unittest tests.test_normalization -v`.
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
Context: Kettle Brand Chips hover tooltip on `/staging-price-tracker/` Safeway tab showed only "Jul 1". No promo note, no Friday annotation, even after Option A was implemented in `PriceTrendChart.tsx`.
What happened: `effectiveWeeklyPrice()` in `yamlFamilyProducts.ts` (the path for all 66 YAML families) did NOT forward `availabilityType` or `promoNote` from the generated entry. So `weeklyEntry?.promoNote` was always `undefined` in the tooltip: `promoLine` never rendered. The `priceTrackerFallback.ts` version already forwarded these fields; only the YAML path was missing them.
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
- `2026-05-06` Safeway: `price: 11.99` ("Lindt Gourmet Truffles Select varieties"). Wrong
- `2026-03-25` Safeway: `price: 5.99` ("Spring Lindt Truffles select varieties"), wrong
The real Ruffles deals in those weeks either had no price data (2026-03-25 BUY 2 GET 2 FREE with no reference price) or no deal at all (2026-05-06). Vons 2026-05-06 `$2.99` was legitimately correct (offerText literally says "Ruffles", Pick 4 Mix or Match).  
Fix / workaround: Changed `phrase_to_pattern()` condition from `if len(text) <= 4 and text.isalpha()` to `if not re.search(r"\d", text)`. Adds `\b...\b` word boundaries to ALL text-only patterns (no digits). Patterns with digits (size ranges like "5–13 oz") are unaffected. Regenerated `weeklyAdPrices.generated.ts` for `ruffles_regular_bags`. Both bad weeks corrected to `null`.  
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
2. **Option B** (pipeline): Added `scripts/price_tracker/baseline_per_lb.py` with `normalize_baseline_price(canonical_id, product_name, price)`. Checks if the YAML family has `size_format_subtitle: per lb`, extracts weight from product name (e.g. "3.5 Lb"), divides. Wired into `generate_safeway_feed_matches.py` and `generate_vons_feed_matches.py` so future re-crawls auto-normalize.
How to verify: Safeway tab → Ribeye chart baseline ~$12.99; Vons tab → Ribeye chart baseline ~$7.99. `npm run build:price-tracker`.
Related files: `src/data/priceTrackerFallback.ts` (SAFEWAY_BASELINES), `src/data/vonsBaseline.generated.ts`, `scripts/price_tracker/baseline_per_lb.py`, `scripts/generate_safeway_feed_matches.py`, `scripts/generate_vons_feed_matches.py`

### Safeway/Vons baselines for per-lb products were stored as total package price (not per-lb)

Date discovered: 2026-07-06
Context: Safeway and Vons baseline prices in `priceTrackerFallback.ts` and `vonsBaseline.generated.ts` for per-lb tracker families (ribeye, tri-tip, chicken, cherries, grapes).
What happened: `generate_safeway_feed_matches.py` and `generate_vons_feed_matches.py` stored the raw pgmsearch package price as the baseline. For per-lb families (YAML: `size_format_subtitle: per lb`), this meant the total package price was used as the chart reference line. Example: "USDA Choice Bone In Beef Rib Steak Mega Pack - 3.5 Lb" → pgmsearch price $45.47 stored as baseline, but chart scale is per-lb; correct baseline is $45.47 / 3.5 = $12.99/lb. Weekly ad prices ($7.99, $9.99/lb) were already correct, so the chart reference line was 4-5x above the sale prices. Visually broken.
**Affected products (Safeway):** ribeye_steak (45.47→12.99), cherries_per_lb (10.48→5.99), chicken_breast_per_lb (20.23→8.99), chicken_thigh_per_lb (8.97→2.99), tri_tip_roast (47.47→18.99), grapes (9.98→4.99).
**Affected products (Vons):** ribeye_steak (23.97→7.99).
Fix / workaround: Added `scripts/price_tracker/baseline_per_lb.py` (`normalize_baseline_price()`): detects per-lb YAML families via `size_format_subtitle`, extracts package weight from product name (e.g. "- 3.5 Lb"), and divides. Both generator scripts now call this before writing the TS value. Manually corrected all existing per-lb baselines in `priceTrackerFallback.ts` and `vonsBaseline.generated.ts`.
Web verification: Direct Safeway fetch blocked by Imperva (expired cookie). Instacart shows Safeway bone-in ribeye at $18.99/lb (promotional, sale ending 7/7/2026). Our $12.99/lb baseline comes from the pgmsearch crawl and may reflect a prior sale period; the regular everyday price is likely $18.99+/lb. To re-crawl at the current regular price: refresh `SAFEWAY_COOKIE`, run `python scripts/seed_safeway_baseline.py --query "ribeye steak"`, then `python scripts/generate_safeway_feed_matches.py --merge-fallback`.
How to verify: `python -c "from price_tracker.baseline_per_lb import normalize_baseline_price; print(normalize_baseline_price('ribeye_steak','USDA Choice Bone In Beef Rib Steak Mega Pack - 3.5 Lb',45.47))"` → `(12.99, True)`.
Related files: `scripts/price_tracker/baseline_per_lb.py`, `scripts/generate_safeway_feed_matches.py`, `scripts/generate_vons_feed_matches.py`, `src/data/priceTrackerFallback.ts`, `src/data/vonsBaseline.generated.ts`

### normalize_per_lb divided price by itself for all "$X lb" offer texts (per_lb bug)

Date discovered: 2026-07-06
Context: Price tracker charts showed ribeye steak at $1 for multiple weeks on both Safeway and Vons tabs. Investigation found the same $1.0 bug on chicken breast, grapes, cherries, peaches, nectarines, and plums.
What happened: `normalize_per_lb()` in `scripts/price_tracker/normalization.py` tries to extract a package weight from offer text (e.g. "Chicken 3 lb for $8.97" → $2.99/lb). But when the ad text printed the per-lb price next to the unit. E.g. "Ribeye Steak $9.99 LB" or "Grapes $2.49 lb Member Price": `_extract_lb_weight()` matched the price itself as the weight (9.99 lb → 9.99/9.99 = $1.0). Every per-lb family where the raw_offer_text included "$X lb" or "X lb" (appended price from vision extraction) yielded exactly $1.0.
A second bug: `base_normalize_unit_price()` had a guard `not re.search(r"(when you )?buy\s+\d+", promo)` that skipped multi-buy normalization for "PICK 4 FOR $20 WHEN YOU BUY 4" bundle deals. This caused Safeway chicken thighs (2026-03-25) to show $20/lb instead of $5/item.
Fix / workaround:
1. `normalize_per_lb`: Added early return `if price_basis == "per_lb": return price`. If the CSV already tags the price as per-lb, no weight extraction needed.
2. `normalize_per_lb`: Added safety check `if abs(lbs - price) / price < 0.02: return price` (skip divide if extracted weight ≈ advertised price).
3. `base_normalize_unit_price`: Removed the "when you buy" guard, always try `_multi_buy_unit_price` for `multi_buy` basis; the function itself returns None when no "N for $X" pattern is found, so no regression.
4. Regenerated all affected products: `ribeye_steak`, `chicken_breast_per_lb`, `seedless_grapes_per_lb`, `chicken_thigh_per_lb`, `tri_tip_roast`, `cherries_per_lb`, `peaches_per_lb`, `nectarines_per_lb`, `plums_per_lb` for both Safeway and Vons.
Before/After examples (price for 2026-07-01):
- Safeway ribeye_steak: $1.0 → $9.99/lb
- Vons ribeye_steak: $1.0 → $7.99/lb
- Safeway cherries: $1.0 → $1.99/lb
- Safeway grapes 2026-03-25: $1.0 → $2.49/lb
- Safeway chicken thighs 2026-03-25: $20.0 → $5.0 (per-pack from "Pick 4 for $20")
How to verify: `PYTHONPATH=scripts python3 -m unittest tests.test_normalization -v`. Check `grep '"2026-07-01"' src/data/weeklyAdPrices.generated.ts` near `ribeye_steak`. Should show `"price": 9.99`. Vons same → `"price": 7.99`.
Related files: `scripts/price_tracker/normalization.py` (`normalize_per_lb`, `base_normalize_unit_price`), `src/data/weeklyAdPrices.generated.ts`, `src/data/vonsWeeklyAdPrices.generated.ts`

### Coca-Cola B2G3F Safeway 7/1: missing split row + stale per-can display (fixed 2026-07-07)

Date discovered: 2026-07-07
Context: Homepage Popular this week + price tracker for `coca_cola_12packs` Safeway week 2026-07-01.
What happened: Safeway 7/1 ad has "BUY 2, GET 3 FREE WHEN YOU BUY 5" on soda 12-packs ($12.99 ref). Vision pipeline captured the multi-brand promo block in `raw_offer_cards.csv` (page 1 offer 14) but did not promote Coca-Cola to `split_offer_items.csv` (`ambiguous_multi_product_offer|missing_or_unclear_price`). `weeklyAdPrices` had `null` for 2026-07-01 → UI fell back to baseline $12.99. Homepage `unitPriceDisplay()` preferred stale `priceComparison.groceryUnitPrice` ($12.99÷12 = $1.08/can) over deal price. `getCurrentPrice()` also preferred the upcoming preview week (2026-07-08) over the calendar-active week when both existed.
Fix / workaround:
1. Manually added Coca-Cola 12-pack row to `data/weekly_ads/2026-07-01/bay_area/split_offer_items.csv` + sibling `outputs/product_discovery_safeway/split_offer_items.csv` with `advertised_price=12.99`, `price_basis=bogo`, `promo_text="BUY 2, GET 3 FREE WHEN YOU BUY 5 MEMBER PRICE"`.
2. Regenerated: `PYTHONPATH=scripts python3 scripts/generate_weekly_ad_prices.py --product-id coca_cola_12packs --feed safeway` → `price: 5.2` per 12-pack (2/5 × $12.99).
3. `getCurrentWeeklyPrice()` / `getDealAdjustedUnitPrice()` in `priceTrackerUtils.ts`. Active week + per-can from deal price.
4. `previewData.ts` prefers deal-adjusted unit price over stale comparison baseline.
5. `backfill_price_comparisons.py` maps legacy canonical ids → YAML family ids (`coke_zero` → `coca_cola_12packs`) and prefers calendar-active ad week over preview.
Before/after: homepage Coca-Cola showed `$12.99` / `$1.08/can` / `onSale: false` → now `$5.20` / `$0.43/can` / `onSale: true`.
How to verify: `npm run generate:homepage-preview` → `data/homepage-preview.generated.json` Coca-Cola `unitPrice: "$0.43/can"`. `npx tsx -e` getCurrentPrice/getDealAdjustedUnitPrice on `coca_cola_12packs`. `PYTHONPATH=scripts python3 -m unittest tests.test_normalization -v`.
Related files: `data/weekly_ads/2026-07-01/bay_area/split_offer_items.csv`, `scripts/price_tracker/normalization.py`, `src/data/priceTrackerUtils.ts`, `src/homepage/previewData.ts`, `scripts/backfill_price_comparisons.py`, `src/data/weeklyAdPrices.generated.ts`


Date discovered: 2026-07-06
Context: FamilyDealCard grid on `/staging-price-tracker/`, cards still had unequal heights after summary/stock-up were moved to the Details toggle.
What happened: Four remaining variance sources:
1. **`h2` name**, no line-clamp on desktop (only mobile had it); long names could wrap to 3+ lines.
2. **Price block** (`usualRange` + `atl-hint`), both conditional; 0–2 extra lines (~32px swing).
3. **`ComparisonBadge`**, biggest source; can be null (0px) or title+detail+locationNote (~60px swing).
4. **`takeaway`**, no line-clamp; could wrap unboundedly.
Fix / workaround:
- `.family-deal-card { min-height: 100%; }`, fills the grid cell so all cards in a row match the tallest one (whitespace at bottom of shorter cards). Uses `min-height` not `height` so the expanded Details panel is not clipped.
- `.family-deal-card__header h2`, added `-webkit-line-clamp: 2` to the **base rule** (not just mobile).
- `.family-deal-card__price-block { min-height: 62px }` (base) / `46px` (mobile ≤767px). Pre-reserves space for sale + usualRange + ATL lines.
- `.family-deal-card__takeaway`, added `-webkit-line-clamp: 2` to the base rule.
How to verify: Open `/staging-price-tracker/`, compare cards with ATL hints, Costco badges, long names, and takeaways; all cards in each row should have identical height. `npm run build:price-tracker` passes.
Related files: `styles.css` (`.family-deal-card`, `.family-deal-card__header h2`, `.family-deal-card__price-block`, `.family-deal-card__takeaway`)

### Card height normalization: secondary info moved to Details toggle

Date discovered: 2026-07-06  
Context: Price tracker card grid on `/staging-price-tracker/`, cards with ATL hint, stock-up badge, promo notes were taller than simpler cards, causing uneven rows.  
What happened: FamilyDealCard had 4 optional elements adding 1–3 lines each: `summary` (always, 1–2 lines), `FamilyStockUpBadge` (always, 1 line), `effectivePrice` (conditional, promo context), and the "Price history" section label.  
Fix / workaround:
1. **Moved to collapsible "Details" toggle**: `summary`, `FamilyStockUpBadge`, `effectivePrice`. Revealed by clicking the new `.family-deal-card__details-toggle` button (styled like the varieties-hint link). Net: 2–4 fewer lines per card in the default view.
2. **Removed "Price history" section label** from `.family-deal-card__chart`, saves 1 line per card uniformly.
3. **Kept on card**: price (`saleLabel`), `usualRange` (compacted to 12px), `ATL hint`, chart, `ComparisonBadge`, takeaway.
4. **CSS**: `.family-deal-card` gap reduced 12px→8px; `price-tracker-product-meta` truncated to 1 line (`-webkit-line-clamp: 1`) on all breakpoints; `usual`/`effective` font-size reduced 14px→12px.  
How to verify: Open `/staging-price-tracker/` → cards across sections should be noticeably more uniform in height. Cards with and without ATL/Costco badges should differ by ≤2 lines. Click "Details" on any card to reveal summary + stock-up. `npm run build:price-tracker` passes.  
Related files: `src/staging-price-tracker/FamilyDealCard.tsx`, `styles.css` (`.family-deal-card__details-toggle`, `.family-deal-card__details-panel`)

### Price tracker vote layout: compact strip after Popular (variant 2 chosen)

Date discovered: 2026-07-06  
Context: `/staging-price-tracker/` voting module placement, too prominent between store tabs and Popular this week.  
What happened: Four layouts were explored via `?voteVariant=1|2|3|4`; **variant 2** (compact horizontal strip below Popular this week) was chosen permanently. Exploration code (`VoteVariantSwitcher`, compare banner, `compare.html`, query-param switching) was removed.  
Fix / workaround: Page order is **filters → Popular this week → vote strip → product sections**. `TrackVotePanel` is a full-width strip: subtle label "Help pick what we track next.", top 6 vote pills in a responsive wrap row, compact inline suggestion form. Supabase upvote + moderated submit unchanged (`useTrackVote`, RPCs `vote_on_item` / `submit_suggestion`).  
How to verify: `npm run build:price-tracker` → open `/staging-price-tracker/` → search/chips, then Popular, then pink-accent vote strip, then sections. No variant switcher or `?voteVariant=` handling.  
Related files: `src/staging-price-tracker/vote/TrackVotePanel.tsx`, `src/staging-price-tracker/SectionedTrackerList.tsx`, `src/staging-price-tracker/App.tsx`, `styles.css`


Date discovered: 2026-07-05  
Updated: 2026-07-26  
Context: `npm run dev:price-tracker` / `ERR_CONNECTION_REFUSED` on http://localhost:5173/grocery-price-tracker/  
What happened: Default Vite 6 listened only on `[::1]:5173`. Browsers and tools using IPv4 `127.0.0.1` could not connect. Agent-background Vite processes also stop when the agent session ends. Separately: with `base: "/grocery-price-tracker/"` and Vite input `src/staging-price-tracker/index.html`, the **live HMR app** is at `/grocery-price-tracker/src/staging-price-tracker/` — bare `/grocery-price-tracker/` in dev can serve the hub homepage HTML (title “Weekly grocery briefing”), not the React tracker. `/staging-price-tracker/` is 404 in current Vite config.  
Fix / workaround: `vite.config.ts` sets `server.host: "127.0.0.1"`, `port: 5173`, `strictPort: true`. Run `npm run dev:price-tracker`. Open **http://127.0.0.1:5173/grocery-price-tracker/src/staging-price-tracker/** for source/HMR preview. Production/GitHub Pages still uses `/grocery-price-tracker/` after `build:price-tracker` sync.  
How to verify: `lsof -i :5173` shows `127.0.0.1:5173`; curl that HMR URL returns title `Safeway Price Tracker: Scrolling the Aisle` and `#root` + `main.tsx`.  
Related files: `vite.config.ts`, `package.json` (`dev:price-tracker`), `src/staging-price-tracker/index.html`

### Canonical match eligibility gates weekly ad graph updates

Date discovered: 2026-07-08
Context: Safeway 7/8–7/14 ad matched "Acme Togarashi or Nova Smoked Salmon 3 oz $4.99" to canonical `salmon` (fresh fillet tracker), producing a false $4.99 all-time low on the chart.
What happened: YAML `include` listed smoked salmon; pattern match (`\bsalmon\b`) accepted any salmon SKU. No product-type or unit guard before writing `weeklyAdPrices.generated.ts`.
Fix / workaround:
1. `salmon` family now tracks **fresh salmon fillet only**, smoked/nova/lox/cured/3–4 oz packs in `keep_separate_from` + `match_eligibility` + `config/canonical_match_rules.yaml`.
2. `scripts/price_tracker/product_type_taxonomy.py` classifies ad text (`fresh_salmon_fillets`, `smoked_salmon`, `12_pack_cans`, `butter_sticks`, etc.).
3. `scripts/price_tracker/canonical_match_eligibility.py` requires product-type + unit compatibility, no hard-negative hits, confidence ≥ threshold before tracker update. `rejected` / `manual_review` do **not** write to generated TS.
4. Every `generate_weekly_ad_prices.py` run writes `output/weekly_deals/<week>/canonical_match_audit.json` + `.md` (section: Graph update safety check).
5. Regression tests: `tests/test_canonical_match_eligibility.py` (5 cases).
How to verify: `PYTHONPATH=scripts python3 scripts/generate_weekly_ad_prices.py --product-id salmon --feed safeway` → `salmon["2026-07-08"].price` is `null`; audit shows rejected Acme Smoked Nova with smoked vs fresh reason; `PYTHONPATH=scripts python3 -m unittest tests.test_canonical_match_eligibility -v`.
Related files: `config/canonical_match_rules.yaml`, `data/canonical_tracker_families.yaml`, `scripts/price_tracker/canonical_match_eligibility.py`, `scripts/generate_weekly_ad_prices.py`, `output/weekly_deals/2026-07-08/canonical_match_audit.md`

### Oreo/Nabisco Family Size Safeway 7/8: missed Oreo tile + "family size" broke snack-cracker pattern (fixed)

Date discovered: 2026-07-08
Context: User reported the Safeway 7/8–7/14 weekly ad (page 1 coupon rail) shows "Nabisco Family Size Oreo Cookies … Snack Crackers … $3.49 EA MEMBER PRICE", but the tracker still showed baseline $6.99 for `oreo_family_size` on 2026-07-08 (both `oreo_family_size` and `nabisco_snack_crackers` were `null`).
What happened: The single Safeway-for-U coupon tile reads "Nabisco Family Size Oreo Cookies 10.68 to 18.71-oz. / Snack Crackers 11.5 to 14-oz. Selected varieties. Limit 4 items. $3.49 EA MEMBER PRICE" (expires 7/14/26). Two separate bugs:
1. **Missed Oreo tile (extraction gap):** The vision pipeline captured only the "Snack Crackers" half of the tile as `Safeway_2026-07-08` page 1 offer 20 ("Nabisco Family Size Snack Crackers 10-14 oz" @ $3.49, `crop_tile_mismatch`). The Oreo Cookies half was never emitted. No Oreo row exists anywhere in `raw_offer_cards.csv` or `split_offer_items.csv` for the 7/8 week. Confirmed by rendering page 1 of `~/Documents/scrolling-the-aisle/inputs/weekly_ads/safeway 7-8 - 7-14.pdf` with PyMuPDF (image-only PDF; text layer is empty). Same failure mode as the Kettle Brand and Coca-Cola B2G3F notes above.
2. **"Family size" broke the snack-cracker include pattern:** `nabisco_snack_crackers` include has "Nabisco snack crackers" → pattern `\bnabisco\s+snack\s+crackers\b` (contiguous words). The ad text "Nabisco **Family Size** Snack Crackers" has words between "Nabisco" and "Snack", so the existing $3.49 row never pattern-matched (it wasn't even in the audit's rejected/manual list. Pattern miss, not an eligibility rejection). `nabisco_snack_crackers` has no `config/canonical_match_rules.yaml` entry, so it uses legacy pattern matching only.
Fix / workaround:
1. Manually added the missing Oreo split row to `~/Documents/scrolling-the-aisle/outputs/product_discovery_safeway/split_offer_items.csv` (the file the generator reads. There is no local `data/weekly_ads/2026-07-08/` dir; the 7/8 week was imported straight into the sibling consolidated CSV): `split_product_text="Nabisco Family Size Oreo Cookies 10.68 to 18.71-oz."`, `advertised_price=3.49`, `price_basis=each`, `promo_text="MEMBER PRICE clip or CLICK! Limit 4 items."`, `review_reasons=manually_added_missed_tile`, week 2026-07-08/2026-07-14, page 1 offer 20 (same `raw_offer_id` as the snack-crackers half). Matches `oreo_family_size` (include "family size Oreo"; prefer "Oreo cookies" → confidence high/1.00; eligibility product-type = oreo/generic_nabisco_block, no negatives).
2. ~~Added "Nabisco Family Size Snack Crackers" to `nabisco_snack_crackers` `include`~~: **superseded**: this per-phrase workaround was reverted in favour of the robust qualifier-tolerant matcher (see "Prevention: robust qualifier-tolerant matching + missed-deal coverage detector" note below). The base "Nabisco snack crackers" include now matches "Nabisco **Family Size** Snack Crackers" generically. NOTE: family-size snack crackers are 11.5–14 oz vs the family's usual 3.5–9.1 oz standard boxes (~$2.49), so $3.49 is a legitimately larger SKU, not a price increase.
3. Regenerated: `PYTHONPATH=scripts /usr/bin/python3 scripts/generate_weekly_ad_prices.py --product-id oreo_family_size --feed safeway` and `--product-id nabisco_snack_crackers --feed safeway`.
Before/after (2026-07-08 Safeway): `oreo_family_size` null (baseline $6.99) → `price: 3.49` (high); `nabisco_snack_crackers` null → `price: 3.49` (medium). Both accepted in the audit; validator shows 0 keyword FAIL rows and neither family flagged.
How to verify: `grep -n '"2026-07-08"' src/data/weeklyAdPrices.generated.ts` near `oreo_family_size` → `"price": 3.49`. `output/weekly_deals/2026-07-08/canonical_match_audit.md` lists both as accepted. `PYTHONPATH=scripts /usr/bin/python3 -m unittest tests.test_normalization tests.test_canonical_families tests.test_canonical_match_eligibility -v` (28 OK). `npm run build:price-tracker` → "Price tracker build OK … 2026-07-08".
Related files: `~/Documents/scrolling-the-aisle/outputs/product_discovery_safeway/split_offer_items.csv`, `data/canonical_tracker_families.yaml` (`nabisco_snack_crackers` include), `src/data/weeklyAdPrices.generated.ts`, `output/weekly_deals/2026-07-08/canonical_match_audit.md`

### nabisco_snack_crackers reworked into explicit family-size cracker family (Wheat Thins / Triscuit / Chicken in a Biskit)

Date discovered: 2026-07-08
Context: The `nabisco_snack_crackers` family was a generic "Nabisco snack crackers" bucket. The Vons/Safeway 7/8–7/14 app deal "Nabisco Snack Crackers Family Size" ($3.49, 11.5–14 oz, limit 4) is really Wheat Thins / Triscuit / Chicken in a Biskit family-size boxes. Reworked the family to mean exactly those eligible items and gated matching so only genuine family-size boxes update the graph.
Canonical meaning (new): **display_name** "Wheat Thins, Triscuit & Chicken in a Biskit"; **subtitle** "Nabisco family-size snack crackers, 11.5–14 oz"; manufacturer Nabisco; package `family_size_box`; product lines Wheat Thins / Triscuit / Chicken in a Biskit; 11.5–14 oz.
Matching rule (see `config/canonical_match_rules.yaml` → `nabisco_snack_crackers`): accept only when the offer has a **family-size or in-range size confirmation** (`require_confirmation_keywords`: family size, 11.5, 12 oz, 12.5, 13 oz, 14 oz, 10-14, …) AND product type ∈ {family_size_snack_crackers, wheat_thins, triscuits, chicken_in_a_biskit, generic_nabisco_block} AND no oreo/chips_ahoy/ritz/single-serve/cookie negatives. A bare "Nabisco snack crackers" (no size, no eligible items) → **manual_review** (no graph update). Standard-size (< 11.5 oz, ~$2.49) Wheat Thins/Triscuit rows now go to manual_review too, so historical standard-box weeks (2026-04-01 $1.67, 2026-06-03/06-24 $2.49) dropped to `null`. Intentional, the family is family-size-only now. The 2026-07-08 Safeway $3.49 family-size match is preserved (confidence 0.89, accepted).
Wiring:
1. `data/canonical_tracker_families.yaml`: `canonical_tracker_family`/`display_name` = display name, `size_format_subtitle`/`subtitle` = subtitle (these are what `generate_canonical_families.py` reads → `displayName`/`subtitle` in `canonicalTrackerFamilies.generated.ts` → UI). Added new metadata fields `manufacturer_family`, `package_type`, `size_range`, `allowed_product_lines`, `eligible_item_examples`. Good Thins + Premium minis moved to `keep_separate_from` (not family-size Nabisco cracker boxes).
2. `scripts/price_tracker/product_type_taxonomy.py`, new types `chicken_in_a_biskit`, `family_size_snack_crackers`, `single_serve_snack_multipack`; tightened the `pint` `14 oz` pattern to require ice-cream context (was swallowing "11.5–14 oz" cracker sizes).
3. `scripts/price_tracker/canonical_families.py`: `TrackerFamily` carries the new metadata (fall back to canonical_tracker_family / size_format_subtitle).
4. `scripts/price_tracker/canonical_match_eligibility.py`, new `require_confirmation_keywords` rule field + confirmation gate; every `MatchEligibilityResult` now carries display_name/subtitle/manufacturer_family/package_type/size_range/allowed_product_lines/eligible_item_examples.
5. `scripts/price_tracker/canonical_match_audit.py` + `scripts/generate_weekly_ad_prices.py`. Audit JSON/MD accepted records include the metadata block.
6. `scripts/price_tracker/shortlist_copy.py` (new): `family_shortlist_blurb()` produces "Wheat Thins, Triscuit, and Chicken in a Biskit family-size boxes are $3.49 this week. The app labels it as Nabisco family-size snack crackers, but those are the actual eligible items." Wired into `scripts/_tmp_expanded_shortlist_jul8.py` (regenerated `output/weekly_deals/2026-07-08/expanded_shortlist.json`).
Ritz / Chips Ahoy / Oreo / single-serve stay separate families (kept `keep_separate_from` cross-refs; added `chicken_in_a_biskit` + `family_size_snack_crackers` to their disallowed_product_types).
Regression tests: `tests/test_canonical_match_eligibility.py` (6 nabisco cases + real-offer accept), `tests/test_canonical_families.py` (metadata).
How to verify: `PYTHONPATH=scripts /usr/bin/python3 scripts/generate_canonical_families.py && PYTHONPATH=scripts /usr/bin/python3 scripts/generate_weekly_ad_prices.py --product-id nabisco_snack_crackers`; `grep -A3 '"2026-07-08"'`-region of `nabisco_snack_crackers` in `src/data/weeklyAdPrices.generated.ts` → `"price": 3.49`; `output/weekly_deals/2026-07-08/canonical_match_audit.md` Accepted list shows the metadata; `PYTHONPATH=scripts /usr/bin/python3 -m unittest tests.test_canonical_match_eligibility tests.test_canonical_families tests.test_normalization tests.test_validate_weekly_ad_prices` (68 OK); `npm run build:price-tracker` → "Price tracker build OK … 2026-07-08".
Related files: `data/canonical_tracker_families.yaml` (`nabisco_snack_crackers`), `config/canonical_match_rules.yaml`, `scripts/price_tracker/product_type_taxonomy.py`, `scripts/price_tracker/canonical_families.py`, `scripts/price_tracker/canonical_match_eligibility.py`, `scripts/price_tracker/canonical_match_audit.py`, `scripts/price_tracker/shortlist_copy.py`, `scripts/generate_weekly_ad_prices.py`, `src/data/canonicalTrackerFamilies.generated.ts`, `src/data/weeklyAdPrices.generated.ts`

### Shortlist family-size blurb must reuse the eligibility gate (not just pattern match)

Date discovered: 2026-07-08
Context: `output/weekly_deals/2026-07-08/expanded_shortlist.json` emitted the Nabisco family-size blurb ("Wheat Thins, Triscuit, and Chicken in a Biskit family-size boxes are $2.49 this week …") for the Vons standard-size, Ritz-led offer "Ritz Crackers, Wheat Thins or Triscuit 3.5-13.7 oz … Mix or Match any 4 … $2.49 ea". The durable tracker already routed these to manual_review/null, but the shortlist copy path did not gate.
What happened: `scripts/_tmp_expanded_shortlist_jul8.py` assigned `family_id` purely from `HIST_MAP` text regex (`family_for_item`) and always called `family_shortlist_blurb`, which emitted the family-size sentence whenever `package_type == family_size_box`. No eligibility check. So standard-size / Ritz-led rows got a false "family-size boxes are $X" claim.
Fix / workaround:
1. `scripts/price_tracker/shortlist_copy.py`: `family_shortlist_blurb()` now takes `family_size_eligible: bool = False` (default off = defensive). The family-size sentence is only produced when the caller passes `family_size_eligible=True` AND `is_family_size_family(family)` (new helper: has `allowed_product_lines` + `package_type == family_size_box`). Otherwise returns the generic `"{display_name} are $X this week."` (no family-size claim).
2. `scripts/_tmp_expanded_shortlist_jul8.py`, reuses the tracker's `EligibilityIndex` (`canonical_match_eligibility`). For any assigned family where `is_family_size_family()`, it runs `EligibilityIndex().evaluate(row, fid, keyword_confidence=…)` (same gate as `generate_weekly_ad_prices.py`). `accepted` → `family_size_eligible=True`; anything else (manual_review/rejected) → drop the attribution entirely (`family_id=None`, no blurb) so standard/Ritz-led rows are not mislabeled. `_keyword_confidence()` mirrors the tracker's coarse comma/" or " → medium else high signal.
Before/after: Vons "Wheat Thins"/"Triscuit" $2.49 rows now `family_id: null`, no blurb (were `nabisco_snack_crackers` + family-size $2.49 blurb). Safeway "Nabisco Family Size Snack Crackers 10-14 oz" $3.49 row unchanged (accepted → exact same family-size $3.49 blurb). Durable `weeklyAdPrices.generated.ts` / `vonsWeeklyAdPrices.generated.ts` untouched (standard weeks still null, Safeway 7/8 = 3.49).
How to verify: `PYTHONPATH=scripts /usr/bin/python3 scripts/_tmp_expanded_shortlist_jul8.py`; `grep -c "family-size boxes are \$2.49"` → 0, `grep -c "family-size boxes are \$3.49"` → 1. `PYTHONPATH=scripts /usr/bin/python3 -m unittest tests.test_shortlist_copy tests.test_canonical_match_eligibility tests.test_canonical_families tests.test_normalization` → 48 OK.
Related files: `scripts/price_tracker/shortlist_copy.py`, `scripts/_tmp_expanded_shortlist_jul8.py`, `scripts/price_tracker/canonical_match_eligibility.py`, `tests/test_shortlist_copy.py`, `output/weekly_deals/2026-07-08/expanded_shortlist.json`

### Prevention: robust qualifier-tolerant matching + missed-deal coverage detector

Date discovered: 2026-07-08
Context: Follow-up to the "Oreo/Nabisco Family Size Safeway 7/8" note, the user asked *why* the miss happened and what durable safeguard prevents this whole class of bug (also seen in the Kettle Brand and Coca-Cola B2G3F notes). Root cause in plain terms: (a) the vision extraction pipeline sometimes silently drops half of a combined coupon tile so no row is ever emitted, and (b) include phrases were matched as *contiguous* words, so any inserted qualifier ("**Family Size**", "**Party Size**") between the brand and product word caused a total pattern miss. Two safeguards were added.

**1. Robust qualifier-tolerant phrase matching** (`scripts/price_tracker/canonical_families.py`):
- `phrase_to_pattern()` now allows a *bounded* run (`{0,3}`) of a curated `QUALIFIER_WORDS` set (family, size, party, value, mega, king, jumbo, share, sharing, fun, snack, big, grab, original, classic, selected, variety, varieties, brand, new) between adjacent words of a multi-word phrase. So `"Nabisco snack crackers"` → matches `"Nabisco Family Size Snack Crackers"`; `"Oreo cookies"` → matches `"Nabisco Family Size Oreo Cookies"`.
- SAFETY: only these non-discriminating qualifiers are allowed: NOT arbitrary words, brand names, product nouns, connectors ("or"/"with"), or digits. So the gap can NEVER bridge two different products (e.g. `"Oreo cookies"` still does NOT match `"Oreo or Chips Ahoy! Cookies"`). `keep_separate_from` patterns get the *same* treatment, so exclusions stay at least as strong, and the `\b…\b` substring guard is preserved (Ruffles ≠ Truffles). The eligibility gate (`canonical_match_eligibility.py`) remains the independent backstop.
- VALIDATION: a full rematch of both feeds after this change produced **zero** unexpected match changes across all 66 families/weeks (only the two intended historical Oreo additions below). I.e. it recovered the missed wording without introducing a single new false match. Regression tests: `tests/test_canonical_families.py::TestRobustPhraseMatching` (6 cases incl. anti-bridge + substring + keep_separate).

**2. Missed-deal coverage detector** (`scripts/detect_missed_deals.py`, NEW):
- For every tracked family × tracked week where the generated TS price is `null`, it scans `raw_offer_cards.csv` (all `product_discovery_{feed}*` per-week dirs) and the consolidated `split_offer_items.csv` for a row whose **product-name field** (not the noisy multi-product `raw_offer_text` blob) matches the family's robust include patterns, is not excluded, and carries a numeric price. Any hit = a "possible missed deal" candidate.
- Severity: **high** = present in raw cards but NOT promoted to split (the Kettle / Coca-Cola dropped-tile class); **medium** = multi-product "or" block or in-split-but-unwritten; **info** = the eligibility gate already rejected it on purpose (cross-referenced from each week's `canonical_match_audit.json`).
- Run: `PYTHONPATH=scripts /usr/bin/python3 scripts/detect_missed_deals.py` → writes `data/review/missed_deal_candidates_{date}.csv` + `.md`. `--feed`, `--week`, `--family-id`, `--fail-on-high` (CI gate) supported. Unit tests: `tests/test_detect_missed_deals.py`.
- KNOWN BLIND SPOT: it keys off *text*, so it CANNOT catch a tile dropped **before** extraction (the Oreo 7/8 half. The word "oreo" never appeared in any CSV). That specific class still needs a vision-pipeline coverage pass / manual PDF audit. It *does* catch the "keyword present but no price written" class (would have flagged the pre-fix Nabisco 7/8 and the Kettle/Coca-Cola raw-but-unpromoted rows).
- First run flagged 6 high / 10 medium / ~28 info candidates (none Oreo/Nabisco, those are fixed). Genuine follow-ups worth a human look: `cheez_it_crackers` Safeway 6/24 $9.99, `dr_pepper_12packs` Safeway 6/24 $5.00, `ritz_toasted_chips` Safeway 7/1 $2.99, `tillamook_ice_cream` Vons 6/10 $3.49 & 7/1 $3.99. (`ben_jerrys_ice_cream` is tracked via the family feed, so its `weeklyAdPrices` null is expected. A detector blind spot to note.)

**Part 2, historical Oreo backfill** (`oreo_family_size`): scanned every week/feed in split + raw for "oreo".
- SUBSTANTIATED & ADDED: **Safeway 2026-05-06 = $3.49** (PDF-confirmed page 3 tile "Nabisco Family Size Oreo Cookies 10.68 to 18.71-oz. / Chips Ahoy! … $3.49 EA MEMBER PRICE", expires 5/12/26). It was `null` because the extracted row's text is the *combined* "Oreo **or Chips Ahoy!**" tile, and "Chips Ahoy" is an Oreo `keep_separate_from`. So I added an Oreo-only split row (`manually_added_missed_tile`). **Vons 2026-07-08 = $3.99** (digital-coupon "Oreo or Chips Ahoy! Cookies", added Oreo-only split row). So the Safeway Oreo chart now dips at 5/06 and 7/08.
- FOUND but NOT added: **Vons 2026-06-24 $4.99** combined "Nabisco Family Size! Oreo, Chips Ahoy! or Ritz". The eligibility gate rejected it (product-type taxonomy misclassified "…12.2-20 oz" as `single_bottle`); respected the gate rather than override it. **Safeway 6/10 & 6/24** Oreo tiles are **BOGO with no extracted reference price** → cannot compute a dollar value without fabricating one (they are real BOGO deals, just not a clean $-figure). **Safeway 5/12** Oreo appears only as a Coca-Cola "PLUS FREE OREOS!" add-on, not an Oreo price.
- To substantiate the BOGO weeks or the Vons $4.99, we'd need the extraction to capture the BOGO reference (regular) price and the taxonomy to classify the family-size cracker/cookie size correctly.

How to verify: `PYTHONPATH=scripts /usr/bin/python3 -m unittest discover -s tests` (118 OK). `PYTHONPATH=scripts /usr/bin/python3 scripts/detect_missed_deals.py`. `grep '"2026-05-06"' -A4` region of `oreo_family_size` in `src/data/weeklyAdPrices.generated.ts` → `"price": 3.49`. `npm run build:price-tracker` → "Price tracker build OK … 2026-07-08".
Related files: `scripts/price_tracker/canonical_families.py` (`phrase_to_pattern`, `QUALIFIER_WORDS`), `scripts/detect_missed_deals.py`, `tests/test_detect_missed_deals.py`, `tests/test_canonical_families.py`, `~/Documents/scrolling-the-aisle/outputs/product_discovery_safeway/split_offer_items.csv`, `~/Documents/scrolling-the-aisle/outputs/product_discovery_vons/split_offer_items.csv`, `src/data/weeklyAdPrices.generated.ts`, `src/data/vonsWeeklyAdPrices.generated.ts`

### Eggs candy false matches + missing cartons; Clif per-bar; berries package size

Date discovered: 2026-07-13  
Context: Staging price tracker showed suspicious ATLs (eggs $1.50, Clif $1.17) and sparse history for berries / Nabisco family-size crackers.  
What happened:
1. **Eggs $1.50** was Russell Stover Chocolate Eggs (2 for $3), not cartons. Bare `\beggs?\b` taxonomy + family name "Eggs" as an include matched candy. Real Lucerne/Eggland rows were missed or beaten by candy; `12 ct` on cartons was also misclassified as soda `12_pack_cans`.
2. **Clif $1.17 / $1.25** was correct per-bar math ($6.99÷6, $14.99÷12) but read like a single-bar shelf price.
3. **Berries** often have size only in `package_text` ("Blackberries" + "6 oz."); include required "blueberries 6 oz" in product text, and hard negatives on full text rejected "Blackberries 6 oz" when the shared package said "Pint, 6 oz".
Fix / workaround:
- Eggs family renamed pattern basis to "Large eggs"; block `candy_eggs`; require carton confirmation (12/18/24 ct, dozen, Lucerne, etc.); normalize via `package_text` (`18-ct.` → $/dozen); pick lowest conventional carton; keep organic/pasture-raised/Vital Farms separate.
- **Usually $10.99 / ATL $1.99 mismatch (2026-07-14):** Safeway baseline was Nellie's **18-count pack** $10.99 mapped onto the dozen chart unscaled. Scale 18-count baselines ×12/18 (→ **$7.33/dozen**). Card title uses `display_name` **Eggs**; price lines append ** / dozen**.
- **Lucerne-only (2026-07-14):** Family narrowed to Lucerne store-brand eggs as the interchangeable buy. Crawl baselines in `safeway_baseline_candidates_v1.csv`: Lucerne 18-count **$5.99**, Lucerne 12-count **$3.99** (chosen as per-dozen shelf anchor). Vons crawl rank-1 Lucerne 18-count **$1.99** was a sale scrape, not shelf — do not use as baseline. Website confirms Lucerne Farms Eggs Large Cage Free 12 Count **$3.99 each**. Safeway may bury the card behind dairy "Show more" when Lucerne is not on sale — intentional deal-ranking behavior (kept).
- Tighten `12_pack_cans` so bare `12 ct` without can/soda context does not steal egg cartons.
- Clif subtitle: **per bar (multipack price ÷ bar count)**.
- Berries: match bare berry names + `require_confirmation_keywords` 6 oz (from package_text); identity negatives from product text only; confirmation boost before ATL confidence floor.
How to validate a price: hover chart `offerText`/`promoNote`; `PYTHONPATH=scripts python3 scripts/validate_weekly_ad_prices.py`; dry-run `generate_weekly_ad_prices.py --product-id <id>`; compare to `split_offer_items.csv` `advertised_price` + `package_text`.
How to verify: Safeway eggs weeks show Eggland/Happy Egg/Lucerne (not chocolate); Lucerne 18-ct $2.99 → **$1.99/dozen**; Clif card subtitle says per bar; Safeway berries 2026-07-08 = Blackberries 6 oz $2.99. `PYTHONPATH=scripts python3 -m unittest tests.test_canonical_match_eligibility tests.test_normalization -v`.
Related files: `data/canonical_tracker_families.yaml`, `config/canonical_match_rules.yaml`, `scripts/price_tracker/product_type_taxonomy.py`, `scripts/price_tracker/canonical_match_eligibility.py`, `scripts/price_tracker/normalization.py`, `src/data/weeklyAdPrices.generated.ts`, `src/data/vonsWeeklyAdPrices.generated.ts`

### Goldfish 30 oz tub matched as 6–8 oz bags (Safeway 2026-05-06 $7.99 spike)

Date discovered: 2026-07-14  
Context: Price tracker Safeway chart for `goldfish_bags` spiked to $7.99 on the 2026-05-06 week. Family intent is regular ~6–8 oz bags only.  
What happened: Extraction correctly captured `Goldfish Crackers 30 oz. 7.99 ea` (`package_text=30 oz`), but matching used `split_product_text` = "Goldfish Crackers" and **no eligibility rules**, so the 30 oz tub was accepted at confidence 0.90. `matches()` also applied `keep_separate_from` excludes only to split text, so size exclusions in package_text were invisible. Same failure class as Kettle party-size / Nabisco bare-block mismatches.  
Fix / workaround:
1. Taxonomy: `goldfish_tub` (20–49 oz / tub / carton) before `goldfish_crackers`.
2. `config/canonical_match_rules.yaml` → `goldfish_bags`: disallow `goldfish_tub`, reject `\b(?:2[0-9]|3[0-9]|4[0-9])\s*oz\b`, require bag-size confirmation (4–8 / 5.9 / 6.1 / 8 oz, etc.). Bare "Goldfish Crackers" → manual_review.
3. YAML `keep_separate_from`: Goldfish tub/carton + 27/30/33 oz + 45 pack.
4. `matches()` now applies exclude patterns to full `row_text()` (includes `package_text` / `raw_offer_text`).
5. Rematched: Safeway 2026-05-06 → `null`; 2026-06-03 bare Friday "Goldfish or Eggo" → `null`; 2026-06-17 6.1–8 oz $3.49 and Vons 2026-05-13 5.9–8 oz $1.88 preserved.  
How to verify: `PYTHONPATH=scripts python3 -m unittest tests.test_canonical_match_eligibility.TestGoldfishBagsVsTubs -v`; `goldfish_bags["2026-05-06"].price` is `null` in `weeklyAdPrices.generated.ts`; chart no longer spikes to $7.99.  
Related files: `config/canonical_match_rules.yaml`, `data/canonical_tracker_families.yaml`, `scripts/price_tracker/product_type_taxonomy.py`, `scripts/generate_weekly_ad_prices.py`, `tests/test_canonical_match_eligibility.py`, `src/data/weeklyAdPrices.generated.ts`

### BOGO without shelf price fell back to baseline (Goldfish 2026-06-24)

Date discovered: 2026-07-14  
Context: Safeway 6/24 Mix & Match tile "Goldfish Crackers or Crisps 4 to 8-oz. BUY 1 GET 1 FREE EQUAL OR LESSER VALUE MEMBER PRICE" — no printed dollar amount on the ad. Chart hovered at baseline $3.99 instead of effective ~$2.  
What happened: Extraction stored `price_basis=bogo` with empty `advertised_price`. `normalize` returned null → UI `getCurrentPrice` fell back to shelf baseline. Same class as other equal-or-lesser BOGO weeks noted earlier.  
Fix / workaround (applies to **all** tracker families, not just Goldfish):
1. `base_normalize_unit_price(..., fallback_reference_price=baseline)` → BOGO/B2G effective unit (`buy/(buy+free) × reference`). Safeway baseline from `SAFEWAY_BASELINES` / Vons from `vonsBaseline.generated.ts`.
2. Eligibility: size-confirmed Mix & Match ("A or B") no longer auto-manual_review; BOGO without shelf price no longer takes the full -0.30 no-price confidence penalty.
3. Rematch: `goldfish_bags` Safeway 2026-06-24 → **$2.00** (3.99÷2) with BOGO promoNote.  
How to verify: hover Goldfish 6/24 → ~$2 + BOGO note; `PYTHONPATH=scripts python3 -m unittest tests.test_normalization.TestNormalization.test_bogo_without_advertised_price_uses_baseline_reference tests.test_canonical_match_eligibility.TestGoldfishBagsVsTubs -v`.  
Re-apply across families: `python3 scripts/generate_weekly_ad_prices.py --product-ids <id1,id2,...>` (or full rematch). Prefer printed `advertised_price` when the ad has one (B2G3F $5.49 path unchanged).  
Related files: `scripts/price_tracker/normalization.py`, `scripts/generate_weekly_ad_prices.py` (`load_feed_baselines`), `scripts/price_tracker/canonical_match_eligibility.py`, `src/data/weeklyAdPrices.generated.ts`

### Chobani cups vs 32 oz tub must be separate tracker families

Date discovered: 2026-07-14  
Context: Price tracker showed `chobani_yogurt_per_cup` with subtitle “normalize per cup”, but the shelf baseline was the legacy 32 oz tub ($7.99) because `chobani_greek_yogurt` mapped into the cups family.  
What happened: Off-sale weeks charted ~$7.99 (tub) next to sale weeks at ~$1/cup — clearly not normalized. YAML already said keep cups separate from tubs; legacy remap + baseline inheritance undid that.  
Fix / workaround:
1. New YAML family `chobani_yogurt_tub` (32 oz only). Remap legacy `chobani_greek_yogurt` → `chobani_yogurt_tub` (not cups).
2. Cups family (`chobani_yogurt_per_cup`) only matches single cups / 4-packs; normalize per cup. Exclude tubs and multi-brand Mix tiles (Simply Juice, Frigo, Oikos, etc.).
3. User-confirmed shelf anchors: regular Greek single cup **$1.99**; 4×5.3 oz multipack (incl. Layered) **$6.99**; 20g protein 4–6.7 oz multipack **$9.99** (separate — do not merge into cups/Layered family); 32 oz tub **$7.99**. Store cup/tub baselines under quoted keys in `SAFEWAY_BASELINES` so `load_feed_baselines` parses them (regex only matches `"id": { price:`).
4. Costco: cups → 20-ct 5.3 oz (#1005641) compared as each/cup; tubs → 40 oz (#2059712). `parse_item_sign(..., target_unit="each")` treats `20 COUNT 5.3 OZ` / `20/5.3 OZ` as 20 each.  
How to verify: Cups chart baseline ~$1.99 with sale weeks ≤$1.25; tub chart baseline $7.99 and never inherits cup deals; `LEGACY_CANONICAL_TO_FAMILY["chobani_greek_yogurt"] == "chobani_yogurt_tub"`.  
Related files: `data/canonical_tracker_families.yaml`, `scripts/price_tracker/canonical_families.py`, `src/data/priceTrackerFallback.ts`, `src/data/vonsBaseline.generated.ts`, `config/costco_item_mappings.csv`, `scripts/price_comparison/unit_normalize.py`, `scripts/price_comparison/canonical_metadata.py`

### Lay's Poppables vs Baked; Chobani Layered vs 20g protein

Date discovered: 2026-07-26  
Context: Policy confirmation for eval aliases `alias_lays_poppables` and `alias_chobani_layered`.  
What happened: Needed clarity on whether Poppables / Layered share existing tracker families.  
Fix / workaround:
1. **Lay's Poppables** stay on `lays_potato_chips_regular` (same ~$4.29 baseline and sale grouping as regular bags). Site subtitle: `regular bags 5–13 oz, including Poppables`. **Lay's Baked** is a different baseline/sale group — `keep_separate_from` includes Baked.
2. **Chobani Layered** stays on `chobani_yogurt_per_cup` with other 4×5.3 oz multipacks (~$6.99). **20g protein** 4–6.7 oz (~$9.99) must not update that family — removed from include; added to `keep_separate_from`. Subtitle calls out Layered multipacks.
How to verify: `npm run generate:canonical-families`; Poppables accept / Baked reject on `lays_potato_chips_regular`; Layered accept / 20g Protein reject on `chobani_yogurt_per_cup`; `npm run eval:product-matching`.  
Related files: `data/canonical_tracker_families.yaml`, `src/data/canonicalTrackerFamilies.generated.ts`, `evals/product-matching.jsonl`

### Lucerne eggs 12 vs 18; Lay's Kettle sizes; Honey Nut under GM

Date discovered: 2026-07-26  
Context: Remaining eval policy confirmations for eggs, Lay's Kettle, Honey Nut Cheerios.  
What happened: Needed clear tracking/display rules without over-merging pack sizes.  
Fix / workaround:
1. **Eggs:** Track Lucerne **12-count** (`eggs_dozen_normalized`) and **18-count** (`lucerne_eggs_18`) separately (no 18→dozen scaling). `display_card_group: lucerne_eggs` collapses them to **one card**; weekly/preview price is the better **per-egg** deal. Subtitle notes which count is shown.
2. **Lay's Kettle:** Regular **6–8 oz** only on `lays_kettle_cooked`; party ~12.5 oz stays off that family. Separate from other Lay's. Ads include size — do not use size-missing needs_review for kettle.
3. **Honey Nut Cheerios:** Confirmed under `general_mills_cereal_regular`.
How to verify: `npm run generate:canonical-families`; eligibility tests for 12 vs 18; one Lucerne Eggs card in tracker; `npm run eval:product-matching`.  
Related files: `data/canonical_tracker_families.yaml`, `config/canonical_match_rules.yaml`, `src/data/yamlFamilyProducts.ts`, `evals/product-matching.jsonl`

### Vons Lucerne eggs Jul 15 $4.99 BOGO was crop bleed (not in ad)

Date discovered: 2026-07-15  
Context: Tracker showed Vons Lucerne Eggs @ **$4.99** with hover “Buy 1 Get 1 Free” for week 2026-07-15; user could not find that deal in the weekly ad.  
What happened: Vision first-pass wrote “Lucerne Large Eggs 12 ct @ $4.99 / Buy 1 Get 1 Free” (page 3 offer 7). Crop verification of the same index saw **Signature SELECT ground beef $5.99/lb**. Row kept first-pass with `review_reasons=crop_tile_mismatch` and `price_basis=each` (so BOGO math never halved). Two generator gaps let it ship: (1) baselines keyed only as legacy `eggs_18_count`, so YAML family `eggs_dozen_normalized` never got `[above_baseline]` vs $3.99 shelf; (2) bare `crop_tile_mismatch` was not a match reject, and import QA was non-fatal.  
Fix / workaround:
1. `load_feed_baselines` remaps legacy → YAML family ids via `LEGACY_CANONICAL_TO_FAMILY` (`eggs_18_count` → `eggs_dozen_normalized`).
2. `is_untrustworthy_crop_mismatch_row`: reject mismatch **only** when paired with BOGO/`buy_x_get_y` promo or unit price above baseline (bare mismatch alone is too common on real Lucerne weeks).
3. Import QA: flag bare `crop_tile_mismatch`; `--fail-on-tracked-findings` / import exit on WoW worsens + mismatch findings.
4. Rematched Vons `eggs_dozen_normalized` → `2026-07-15` **null**; prior real weeks ($2.49 etc.) kept.  
How to verify: `eggs_dozen_normalized["2026-07-15"].price` is `null` in `vonsWeeklyAdPrices.generated.ts`; `PYTHONPATH=scripts python3 -m unittest tests.test_everyday_shelf_filter tests.test_audit_weekly_ad_import -v`.  
Related files: `scripts/generate_weekly_ad_prices.py`, `scripts/audit_weekly_ad_import.py`, `scripts/import_weekly_ad.py`, `tests/test_everyday_shelf_filter.py`, `tests/test_audit_weekly_ad_import.py`, `src/data/vonsWeeklyAdPrices.generated.ts`

## Content-first Analysis Mode

### Content deal shortlist mode (separate from canonical graph matching)

Date discovered: 2026-07-08  
Context: The canonical `fresh_costco_deal_report` optimizes for graph-safe matches (canonical family + usable baseline + same-product Costco match), which downranks/omits great *content* deals that are ad-deal-only, proxy/comparable, missing a Costco mapping, or Friday-only. Added a parallel content-first mode.  
What happened: Built a fully separate scorer + generator that never touches canonical eligibility or writes any generated TS.  
Fix / workaround: New modules/configs: `scripts/weekly_ad_analysis/content_score.py` (0–100 `content_score`; rewards popularity, category, Costco-beat unit price, near-Costco variety/smaller-qty, absolute price, Friday-only, seasonal produce, TikTok hook; never requires a canonical/graph-safe match), `scripts/weekly_ad_analysis/content_shortlist.py` (6-section shortlist + gap analysis), CLI `scripts/generate_content_shortlist.py`. Configs: `config/content_shortlist_seed.csv` (per-item seed incl. `primary_section` 1–6, scoring flags) and `config/content_costco_mappings.csv` (content-only Costco SKUs; NEVER edit `config/costco_item_mappings.csv` for content). Warehouse rules reused: Safeway→San Francisco, Vons→Tustin.  
Run: `PYTHONPATH=scripts /usr/bin/python3 scripts/generate_content_shortlist.py --week 2026-07-08 --store safeway` → writes `content_gap_analysis.{md,json}` + `content_script_shortlist.{md,json}` to `output/weekly_deals/{week}/`.  
Gotchas:
- The sibling `split_offer_items.csv` is a **consolidated Safeway+Vons file**: `find_split_row()` MUST filter by `source_file`/`banner` for the requested store or a Safeway item silently pulls a Vons offer (hit this with Chobani: the "4-ct 20g protein" deal the user remembered is a Vons page-2 tile; Safeway's actual deal is single-serve 3/$4, where Costco's 20-ct variety is cheaper per cup. A smaller-buy note, not a Costco beat).
- Content-mode Costco prices are read **live from the latest `~/Documents/costco-mvp/costco_data/{date}_{location}_consolidated.csv`**, not the cached `observations.json` (which lagged a day).
- SF-crawl coverage gaps for the 7/8 week (no comparable SKU crawled): raw shrimp, fresh bell peppers, Nestlé Drumstick cones, sweet corn, regular/single-serve Oreo. Recorded as gaps rather than fabricated.
- `content_score` ≠ `canonical_match_score`: a proxy or gap item can still rank high for content; separate the two mentally.  
How to verify: `PYTHONPATH=scripts /usr/bin/python3 -m unittest tests.test_content_score` (passes), then the generate command above; md and json are internally consistent (item counts, one-liners, section counts, do-not-say list all match).  
Related files: `scripts/weekly_ad_analysis/content_score.py`, `scripts/weekly_ad_analysis/content_shortlist.py`, `scripts/generate_content_shortlist.py`, `tests/test_content_score.py`, `config/content_shortlist_seed.csv`, `config/content_costco_mappings.csv`, `output/weekly_deals/2026-07-08/content_*.{md,json}`

### Safeway transcript highlight → tracker coverage expansion

Date discovered: 2026-07-25  
Context: Expand canonical families so grocery products highlighted in historical Safeway video transcripts are mapped, aliased, newly tracked, or queued for review.  
What happened: Coverage audit found ~49 already covered, ~5 alias-only gaps, ~16 high-confidence missing families, and ~17 ambiguous/ASR/visual-only items.  
Fix / workaround:
1. Audit: `data/review/highlight_tracker_coverage_audit.yaml`
2. Review queue: `data/product_matching/highlight_tracker_review.yaml`
3. New YAML families (16): Cape Cod, Smartfood, Pringles, Snyder's, Frito-Lay variety pack, Pop-Tarts, Kellogg breakfast bars (Nutri-Grain/Special K), Betty Crocker fruit snacks, Waterloo, bell peppers, chicken wings, shrimp 16 oz, beef short ribs, pork spare ribs, Oscar Mayer hot dogs, cake mix
4. Legacy fix: `frito_lay_multipack_chips` no longer maps to `lays_party_size`
5. `pack_total` normalizer for Waterloo / Frito multipack / shrimp so `12 pack` / `18 ct` / `31-40 ct` do not unitize pack totals
6. Evals: +41 highlight cases; original-suite incorrect accepts unchanged (pre-existing Pepsi Zero Sugar bare-name case only)  
How to verify: `PYTHONPATH=scripts python3 -m product_matching.eval_runner`; `npm run generate:canonical-families`; `python3 scripts/generate_weekly_ad_prices.py --new-only`; `npm run verify:price-tracker`.  
Related files: `data/canonical_tracker_families.yaml`, `config/canonical_match_rules.yaml`, `scripts/price_tracker/normalization.py`, `scripts/price_tracker/canonical_families.py`, `data/product_matching/eval_cases.jsonl`, `src/data/weeklyAdPrices.generated.ts`, `src/data/canonicalTrackerFamilies.generated.ts`

### Durable highlight coverage inventory (post-expansion)

Date discovered: 2026-07-26  
Context: Highlight expansion decisions lived in audit YAML + review queue + notes; no single machine-readable inventory of every highlighted product’s final status.  
What happened: Consolidation (read-only vs production matching) wrote one row per unique normalized highlight.  
Fix / workaround: Use `data/product_matching/highlight_mentions.jsonl` + `data/product_matching/highlight_coverage_report.md`. Grain matches audit uniqueness (89). Do not re-extract transcripts to refresh these unless the audit is updated. Shrimp status is `removed` / not tracking. Family count: 68→84 (incl. shrimp)→83.  
How to verify: `wc -l data/product_matching/highlight_mentions.jsonl` → 89; report headline stats match.  
Related files: `data/product_matching/highlight_mentions.jsonl`, `data/product_matching/highlight_coverage_report.md`, `data/review/highlight_tracker_coverage_audit.yaml`, `data/product_matching/highlight_tracker_review.yaml`

### Bell pepper multi-color regulars vs all-color sales

Date discovered: 2026-07-26  
Context: Safeway `bell_peppers` umbrella family (`size_format_subtitle: each or multi-buy`); user provided everyday shelf regulars.  
What happened: Colors have different everyday prices (green cheapest), but weekly ads usually put **all colors** on sale together. A single chart baseline is required; inventing one price from a colored sale tile or averaging colors is wrong.  
Fix / workaround: Chart baseline = **green $1.49** (Green Bell Pepper). Document color regulars in YAML notes: red **$1.99**, yellow/orange **$2.49**. Do not invent other-store baselines from this.  
How to verify: `SAFEWAY_BASELINES["bell_peppers"].price === 1.49` with `retailerProductName` Green Bell Pepper; YAML notes list all four colors.  
Related files: `src/data/priceTrackerFallback.ts`, `data/canonical_tracker_families.yaml` (`bell_peppers`)

### Mandarins 3 lb tracker family (`mandarins_3lb`)

Date discovered: 2026-07-29  
Context: User asked to track 3 lb bagged mandarin oranges (Cuties / similar) with Safeway baseline $6.99 and include in Jul 29 highlight analysis. Prior note incorrectly said Jul 29 Cuties was a **2 lb** bag.  
What happened: PDF `/Users/evelynchan/Downloads/safeway 7-29 - 8-4.pdf` coupon rail shows **Cuties Mandarins 3-lb. bag @ $3.99**. Apr 1 hero was a different size: **2 lb @ $1.99** (must not join the 3 lb graph). Early matching also pulled **Peelz Mandarins** @ $3.49 (2026-06-10, 2026-06-17); user corrected that Peelz is **not** this product (candy / wrong intent).  
Fix / workaround:
1. YAML family `mandarins_3lb` display **Mandarin oranges (Cuties)**; includes Cuties / mandarin oranges / clementines; **hard-negative Peelz** (include/exclude + match-rule negatives / `\bpeelz\b`).
2. Match rules require **3 lb** confirmation; also hard-negative **2 lb** / Geisha canned / navels.
3. Safeway baseline **$6.99** in `SAFEWAY_BASELINES`; pack_total normalization.
4. After Peelz removal rematch: Safeway matched weeks = **2026-07-29 only** ($3.99 Cuties). Vons still has California Mandarins 3 lb @ $2.99 (2026-05-13).
5. Costco SF item **#1801** `MANDARINS 3 LBS` mapped bag-to-bag.
How to verify: Display name contains mandarin + oranges; Jul 29 $3.99; 6/10 & 6/17 nulled; Peelz rejected in audit. Writeup: `output/weekly_deals/2026-07-29/fresh_costco_highlight_recommendations.md`.  
Related files: `data/canonical_tracker_families.yaml`, `config/canonical_match_rules.yaml`, `scripts/price_tracker/product_type_taxonomy.py`, `src/data/priceTrackerFallback.ts`

### Peelz is not mandarin oranges (do not match)

Date discovered: 2026-07-29  
Context: `mandarins_3lb` family initially included Peelz because some Safeway ads say “Peelz Mandarins” on citrus bag tiles.  
What happened: User clarified Peelz is a **candy** / wrong product intent for this tracker — do not treat Peelz as Cuties/mandarin oranges even when the ad title says mandarins.  
Fix / workaround: Remove Peelz from YAML `include`; add to `keep_separate_from` + match-rule `negative_keywords` / `disallowed_package_patterns` (`\bpeelz\b`); drop `\bpeelz\b` from `mandarins_3lb_bag` taxonomy positives. Rematch with `python3 scripts/generate_weekly_ad_prices.py --product-id mandarins_3lb --feed safeway`.  
How to verify: Audit shows Peelz rejected; weeklyAdPrices 2026-06-10 / 2026-06-17 price null.  
Related files: `data/canonical_tracker_families.yaml`, `config/canonical_match_rules.yaml`, `scripts/price_tracker/product_type_taxonomy.py`

### Tracker highlight writeups omit untracked produce (Cuties mandarins) — RESOLVED

Date discovered: 2026-07-29  
Context: Cuties Mandarins missing from Jul 29 highlight writeup because no YAML family existed.  
What happened: Coverage gap (not a matcher bug). Secondary: extraction omitted package size; early PDF spot-check incorrectly called it 2 lb.  
Fix / workaround: Added `mandarins_3lb` (see note above). Supersedes the “intentional coverage gap” workaround.  
How to verify: Family present in YAML / `weeklyAdPrices.generated.ts`; ranked report includes mandarins.  
Related files: `data/canonical_tracker_families.yaml`, `output/weekly_deals/2026-07-29/fresh_costco_highlight_recommendations.md`

### Gushers / Fruit by the Foot share $5.99 Safeway regular

Date discovered: 2026-07-26  
Context: Family id `betty_crocker_fruit_snacks`; UI display renamed to **Gushers / Fruit by the Foot**.  
What happened: User confirmed 6-pack Gushers and 6-pack Fruit by the Foot both shelf at **$5.99**.  
Fix / workaround: Single chart baseline **$5.99** (`Betty Crocker Fruit Gushers 6 Count`). Keep Betty Crocker / Gushers / Fruit by the Foot / Fruit Roll-Ups includes for Mix & Match matching; id stays `betty_crocker_fruit_snacks`.  
How to verify: Card title “Gushers / Fruit by the Foot”; baseline $5.99 in `SAFEWAY_BASELINES`.  
Related files: `data/canonical_tracker_families.yaml`, `src/data/canonicalTrackerFamilies.generated.ts`, `src/data/priceTrackerFallback.ts`

### Shrimp deliberately dropped from tracker (low engagement)

Date discovered: 2026-07-26  
Context: Highlight coverage had added `shrimp_16oz`; user decided not to track shrimp (audience interest low).  
What happened: Keeping the family would continue matching weekly ads and prompting baselines.  
Fix / workaround: Full removal (no soft-delete): deleted YAML family, `config/canonical_match_rules.yaml` block, baseline query/ledger/candidate CSV rows, highlight eval cases, and `shrimp_16oz` keys from Safeway/Vons weekly ad TS. Regenerated canonical families. Audit recommendation updated to “Do not add.” **Do not set a SAFEWAY baseline for shrimp.** Content-mode `raw_shrimp` shortlist rows are unrelated and left alone.  
How to verify: `shrimp_16oz` absent from `data/canonical_tracker_families.yaml` and `src/data/canonicalTrackerFamilies.generated.ts`; no `SAFEWAY_BASELINES` entry; `PYTHONPATH=scripts python3 -m unittest tests.test_canonical_families.TestHighlightCoverageFamilies -v`.  
Related files: `data/canonical_tracker_families.yaml`, `config/canonical_match_rules.yaml`, `data/product_matching/eval_cases.jsonl`, `data/review/highlight_tracker_coverage_audit.yaml`, `src/data/weeklyAdPrices.generated.ts`, `src/data/vonsWeeklyAdPrices.generated.ts`

### $0 baseline guardrail (Lay's party size)

Date discovered: 2026-07-26  
Context: Safeway price tracker card for `lays_party_size` showed a $0 / “Usually $0” style baseline.  
What happened: Family had **no** `SAFEWAY_BASELINES` entry (never crawled under that id after `frito_lay_multipack_chips` was unmapped). YAML weekly builders used `baseline ?? ad ?? 0`, so unmatched weeks became **price: 0**. Unlike legacy `buildSafewayFallbackProducts`, `yamlFamilyProducts` did not backfill those weeks from an inferred ad max — so current week read as $0 and the UI looked like a $0 regular.  
Fix / workaround:
1. Set `SAFEWAY_BASELINES.lays_party_size` = **$5.99** (`Lays Potato Chips Classic Party Size - 13 Oz`; user-confirmed 12.5–13 oz shelf).
2. Runtime: `sanitizeBaselinePrice` / `backfillBaselineFallbackWeeks` reject `<= 0` and refill baseline-fallback weeks.
3. Generate: `scripts/price_tracker/baseline_guardrails.py` skips `<= 0` in Safeway + Vons feed-match generators.
4. Verify: `verify-price-tracker-build.mjs` fails on any shipped baseline `<= 0` and asserts `lays_party_size === 5.99`.  
How to verify: `npm run build:price-tracker`; Safeway Lay's Party Size card shows Usually ~$5.99, not $0.  
Related files: `src/data/priceTrackerFallback.ts`, `src/data/yamlFamilyProducts.ts`, `src/data/priceTrackerUtils.ts`, `scripts/generate_safeway_feed_matches.py`, `scripts/generate_vons_feed_matches.py`, `scripts/price_tracker/baseline_guardrails.py`, `scripts/verify-price-tracker-build.mjs`

### Product-matching v2 eval harness (`evals/` + npm script)

Date discovered: 2026-07-26  
Context: Local regression harness for weekly-ad matching with `matched` / `needs_review` / `no_match` outcomes.  
What happened: Needed labeled cases + metrics without changing production matcher output.  
Fix / workaround: Dataset `evals/product-matching.jsonl` (v2 schema with `expected.status|product_id|match_type|reason_code`, `must_not_match_product_ids`, optional `boundary_group`). Runner `npm run eval:product-matching` → `scripts/run-product-matching-eval.ts` calls eval-only adapter `scripts/product_matching/eval_match_batch.py`, which wraps the production facade and maps accept/reject/manual_review → matched/no_match/needs_review. Production `match_type`/`reason_code` are `not_reported`. Hard-negative `no_match` rows with `must_not_match_product_ids` probe only those families (do not treat a correct alternate-family hit as a false match). Execution errors are reported separately from match outcomes. Legacy Python suite remains at `data/product_matching/eval_cases.jsonl` / `python3 -m product_matching.eval_runner`.  
How to verify: `npm run eval:product-matching` (exit 2 if wrong automatic matches).  
Related files: `evals/product-matching.jsonl`, `scripts/run-product-matching-eval.ts`, `scripts/product_matching/eval_match_batch.py`, `package.json`

### Safer auto-match gate (`required_attributes` + brand/size negatives)

Date discovered: 2026-07-26  
Context: Frozen v1 product-matching evals showed 9 wrong automatic matches (needs_review cases auto-accepted) and 2 false-eligible candidate checks (Chobani 32 oz tub → per-cup; Miss Vickie's → Lay's Kettle). Branch: `matcher/safer-auto-match-gate`.  
What happened: Several trackers accepted on family-name / broad include patterns alone (e.g. `\bcoca-cola\b`, bare "Chobani yogurt", "Kettle chips") with no pack/size/form/brand confirmation. Legacy `require_confirmation_keywords` already existed for Goldfish/eggs/berries; it was not applied to these families. Miss Vickie's hit `lays_kettle_cooked` via include "Kettle Cooked Potato Chips". Chobani tub did not trip per-cup `keep_separate` because "Chobani tub" is not contiguous in "Chobani Greek Yogurt Tub".  
Fix / workaround:
1. Added named `required_attributes` groups on `FamilyMatchRules` (AND across groups; OR within). Missing groups → `manual_review` with `missing_attributes` + `reason_code`. Legacy `require_confirmation_keywords` still maps to a `confirmation` group.
2. Configured rules in `config/canonical_match_rules.yaml` for: `coca_cola_12packs` (package_count), `butter_16oz` (product_form sticks/quarters), `lays_potato_chips_regular` (package_size), `kettle_brand_chips` (brand: "kettle brand" or "potato chips"), `chobani_yogurt_per_cup` / `chobani_yogurt_tub` (package_size + tub/32 oz reject on cups), `nature_valley_bars` (package_count), `waterloo_sparkling_water` (package_count), `general_mills_cereal_regular` (package_size).
3. Brand negatives: Miss Vickie's (+ Cape Cod) on `lays_kettle_cooked`; Miss Vickie's on `kettle_brand_chips`.
4. Do not infer absent size/count/brand/form from the most common catalog variant.  
How to verify: `PYTHONPATH=scripts python3 -m unittest tests.test_canonical_match_eligibility.TestSaferAutoMatchGate -v`; `npm run eval:product-matching`; `npm run eval:candidate-eligibility` → 74/74 and 27/27 on frozen v1.  
Related files: `scripts/price_tracker/canonical_match_eligibility.py`, `config/canonical_match_rules.yaml`, `tests/test_canonical_match_eligibility.py`, `evals/product-matching-end-to-end-v1.jsonl`, `evals/candidate-eligibility-v1.jsonl`

### `allowed_package_patterns` were parsed but unused until safer-gate tightening

Date discovered: 2026-07-26  
Context: Review of `canonical_match_eligibility.py` while tightening safer-gate tests.  
What happened: `FamilyMatchRules.allowed_package_patterns` was loaded from YAML and merged, but `evaluate_canonical_match` never consulted it (only `disallowed_package_patterns` fed hard negatives). Short keyword hits also used a substring `in` check before word boundaries, so tokens like `ct` / `cup` / `stick` could match inside `selected` / `occupied` / `stickshift`.  
Fix / workaround:
1. Enforce `allowed_package_patterns`: hit → OK; explicit package signal outside patterns → **reject**; no package signal → **manual_review** (do not invent size).
2. Boundary-safe `_keyword_hits` only (no substring shortcut).
3. Mixed-item cans+bottles / distinct oz sizes → abstain even when some required attrs are present.
4. Wired ranges for `lays_kettle_cooked` (6–8 oz) and `general_mills_cereal_regular` (≈8.9–15 oz); Coke cans tracker rejects bottles.  
How to verify: `PYTHONPATH=scripts python3 -m unittest tests.test_canonical_match_eligibility -v` (56 OK); frozen evals still 74/74 and 27/27.  
Related files: `scripts/price_tracker/canonical_match_eligibility.py`, `config/canonical_match_rules.yaml`, `tests/test_canonical_match_eligibility.py`

### Shadow LLM product-attribute extraction (no production coupling)

Date discovered: 2026-07-26  
Context: Experiment whether gpt-4o-mini can extract structured grocery attributes from messy weekly-ad text better than rule taxonomy, without changing match decisions.  
What happened: Needed an isolated extractor + labeled eval separate from frozen matching evals.  
Fix / workaround:
1. Schema + validator: `scripts/product_matching/attribute_schema.py` (null-safe scalars; reject malformed output).
2. Shadow extractor: `scripts/product_matching/llm_attribute_extractor.py` (`OPENAI_API_KEY` from `scripts/.env` or sibling-repo `.env`; never browser-exposed).
3. Eval set: `evals/product-attribute-extraction-v1.jsonl` (52 human-reviewable labels).
4. Runner: `npm run eval:attribute-extraction` → `eval_attribute_extraction.py`.
5. Weekly-ad shadow log: `npm run shadow:attribute-extraction` → `output/shadow_attribute_extraction/` (gitignored).
6. Deterministic eligibility remains sole authority for accept/review/reject.  
How to verify: Frozen matching evals still 74/74 and 27/27; `PYTHONPATH=scripts python3 -m unittest tests.test_attribute_schema -v`; attribute eval requires API key.  
Related files: `evals/product-attribute-extraction-v1.jsonl`, `evals/README.md`, `scripts/product_matching/llm_attribute_extractor.py`, `scripts/shadow_weekly_ad_attribute_extraction.py`

### Clif Bars baseline $7.99 shown as per bar

Date discovered: 2026-07-29  
Context: Price tracker Clif card read like **$7.99 / bar** on off-sale weeks (incl. 2026-07-29). Family charts **per bar**; weekly ads already divide (e.g. $14.99÷12 → $1.25).  
What happened: Safeway baseline crawl stored pack total for **CLIF BAR … 5 Count @ $7.99** without ÷5 (`SAFEWAY_BASELINES.clif_bars`). UI appends ` / bar` from subtitle, so pack price looked like a single-bar shelf price. Vons rank-1 baseline was wrong brand (**GoMacro** $4.00). Week 2026-07-29 has **no** regular Clif Bars weekly-ad match (Builders 2/$5 is separate); card was pure baseline fallback.  
Fix / workaround:
1. Safeway baseline → **$1.60/bar** ($7.99÷5); Vons → Clif 5-count **$8.99÷5 = $1.80/bar**.
2. Extend `scripts/price_tracker/baseline_per_lb.py` `normalize_baseline_price` for `per bar` families (same generator path as per-lb).  
How to verify: Off-sale Clif card shows ~$1.60 / bar (not $7.99); `PYTHONPATH=scripts python3 -m unittest tests.test_baseline_normalize -v`.  
Related files: `src/data/priceTrackerFallback.ts`, `src/data/vonsBaseline.generated.ts`, `scripts/price_tracker/baseline_per_lb.py`, `data/review/baseline_refresh_audit_2026-07-05.csv`, `data/canonical_tracker_families.yaml` (`clif_bars`)

### Deterministic shopper-query experiment (no LLM)

Date discovered: 2026-08-03  
Context: Evaluate how well existing weekly-ad text patterns + production canonical matching handle natural-language shopper questions, with an optional lightweight normalization layer. Separate from the LLM `deal_assistant/` vertical slice (do not expand deal-verdict work).  
What happened: There is **no** dedicated free-text shopper parser in production. Weekly ads are vision-extracted into structured CSV (`split_product_text`, `advertised_price`, `promo_text`, `price_basis`, package fields). Matching consumes those rows via `generate_weekly_ad_prices.matches` / `ProductionMatcherFacade.match_offer`.  
Fix / workaround:
1. New package `scripts/shopper_query/` — deterministic parser adapted from weekly-ad regex families (`price_tracker.normalization` multi-buy/BOGO/`N for $X`, `generate_weekly_ad_prices` BOGO cues) + holdout `PROMOTION_TYPES` / `PRICE_BASIS_VALUES`.
2. Matcher reuse only: `product_matching.engine.ProductionMatcherFacade` / `match_offer` (full catalog; no demo allowlist). Behavior map: `continue|clarify|unsupported|invalid` — no deal verdict.
3. Normalization layer (`normalize.py`) rewrites bucks/verbal prices/BOGO synonyms/`gotta buy N` → ad-like text; records step metadata; does **not** silently resolve product identity or map “big box” to a tracker.
4. Eval: `evals/shopper-query-v1.jsonl` (22 hand-authored cases). Baseline + compare → `output/shopper_query_eval/`.
5. Commands: `npm run eval:shopper-query`, `npm run eval:shopper-query:compare`, `npm run shopper-query -- query|serve`, `npm run test:shopper-query`.
6. Gotcha: production include phrases often assume flyer word order (`family size Cheerios`); shopper “Cheerios family size” may miss. Strip `$N` **after** `N for $X` or dangling quantity tokens remain. Leave `deal_assistant/` alone.  
How to verify: `npm run test:shopper-query`; `npm run eval:shopper-query:compare` — normalization lifts price/promo/qty vs raw; no new incorrect continues.  
Related files: `scripts/shopper_query/`, `evals/shopper-query-v1.jsonl`, `evals/README.md`, `scripts/product_matching/engine.py`, `scripts/price_tracker/normalization.py`, `scripts/holdout_labeler/paths.py`

### AisleCheck homepage prototype (local-only, six variations)

Date discovered: 2026-08-03  
Context: Explore homepage placement + six UI variations for **AisleCheck** (“Is this a good deal?”) without shipping to production or adding LLM/backend.  
What happened: Needed fair visual comparison with mocked empty/loading/result/clarify/unsupported/correction states, while keeping GitHub Pages (`main` only) untouched.  
Fix / workaround:
1. Work started on branch `prototype/aislecheck-homepage`.
2. Assets live under `aislecheck-prototype/` (`aislecheck.js`, `aislecheck.css`, `server.py`, README).
3. Variation switcher is now opt-in: `?aislecheckProto=1`.
4. Local preview: `npm run preview:homepage`. Tests: `npm run test:aislecheck-prototype`.  
Related files: `aislecheck-prototype/`, `index.html`, `tests/test_aislecheck_prototype.py`

### AisleCheck Variation 4 public on homepage

Date discovered: 2026-08-03  
Context: Ship Variation 4 + user-friendly copy to https://scrollingtheaisle.com/ (GitHub Pages from `main`).  
What happened: GitHub Pages cannot run the Python `/api/aislecheck` adapter. Full understand/match flow needs a hosted API; without it, Check deal must not look broken.  
Fix / workaround:
1. Public default: Variation 4 only (`PUBLIC_VARIANT = 4`). Always load CSS/JS on all hosts (no localhost gate).
2. Hide prototype toolbar unless `?aislecheckProto=1`. Hide developer debug unless `?aislecheckDebug=1`.
3. Fallback release: `liveApiEnabled: false` → **AisleCheck is almost ready** with preserved query; no fake interpretation; no silent storage on Check deal.
4. Opt-in examples: `exampleSubmitEnabled: true` shows **Submit this example** → RPC `submit_aislecheck_example` only (migration `20260804` + trim harden `20260805`).  
How to verify: Submit a deal → almost-ready; query still shown; no verdict. Click submit → thanks; no third-party analytics of raw query.  
Related files: `aislecheck-prototype/aislecheck.js`, `index.html`, `styles.css`

### AisleCheck opt-in example storage (Supabase RPC)

Date discovered: 2026-08-04  
Context: Collect homepage deal-phrasing examples only after explicit “Submit this example.”  
What happened: Need write-only storage without public reads, silent capture, or personal data. Local Supabase (`supabase start`) requires Docker, which was not available on the agent host.  
Fix / workaround:
1. Migration `supabase/migrations/20260804_aislecheck_examples.sql`: table `aislecheck_examples` + security-definer RPC `submit_aislecheck_example(text, uuid)` with fixed `search_path`, trim/length checks, unique `client_submission_id`, revoke table access from anon/authenticated, grant execute to anon only.
2. Frontend passes `p_client_submission_id` only when `exampleSubmitEnabled === true` (keep false until post-migration security checks pass).
3. Emergency disable: set `exampleSubmitEnabled: false` and/or `revoke execute on function public.submit_aislecheck_example(text, uuid) from anon`.
4. Full removal SQL: `supabase/rollbacks/20260804_aislecheck_examples.sql` (not auto-applied).
5. Local SQL harness: `scripts/test_aislecheck_examples_migration.sh` (needs `psql` + local Postgres).  
How to verify: After local SQL tests pass, `supabase db push --linked` only with explicit confirmation; then anon RPC ok, direct DML denied.  
Related files: `supabase/migrations/20260804_aislecheck_examples.sql`, `aislecheck-prototype/aislecheck.js`, `index.html`

### AisleCheck example RPC: Postgres btrim misses tabs/newlines

Date discovered: 2026-08-04  
Context: Final activation checks against live `submit_aislecheck_example`.  
What happened: Space-only and empty queries correctly returned 400, but tab/newline/mixed whitespace (`\t`, `\n`, ` \n\t `) returned 200 and inserted rows. Cause: Postgres `btrim(text)` removes only ASCII spaces by default, unlike JS `String.trim()`. Homepage JS trims before calling RPC, but direct anon RPC callers could insert junk.  
Fix / workaround:
1. Immediately revoked `execute` from `anon` (flag stayed `exampleSubmitEnabled: false`).
2. Pending harden migration: `supabase/migrations/20260805_aislecheck_examples_trim.sql` uses `trim(both E' \t\n\r' from ...)`, then re-grants execute to anon.
3. Do not enable frontend until that migration is applied and whitespace checks pass.  
How to verify: After push, RPC with `"\t\t"` / `"\n\n"` / `" \n\t "` → 400 `Query is required`; normal query still 200.  
Related files: `supabase/migrations/20260805_aislecheck_examples_trim.sql`

### AisleCheck temporary-failure vs almost-ready UX

Date discovered: 2026-08-04  
Context: Live API on homepage (`liveApiEnabled: true`) with Render free-tier cold starts / intermittent outages.  
What happened: API failure/timeout previously reused the **AisleCheck is almost ready** copy, which implied the feature had not launched; opt-in submit looked primary.  
Fix / workaround:
1. **State A** (`liveApiEnabled: true` + network/timeout/non-OK): heading **We couldn’t check that deal right now**, body about waking up, preserved query, primary **Try again**, secondary **Submit as an example**, tertiary **Check another deal**. Client aborts hung POSTs after 15s (`API_TIMEOUT_MS`; override via `__AISLECHECK_CONFIG__.apiTimeoutMs`).
2. **State B** (`liveApiEnabled: false` only): keep **AisleCheck is almost ready** + opt-in example / check another — **no Try again**.
3. Never auto-store queries; no fake interpretation/verdict on either path. Assets `?v=ac14` (later bumps may coexist).  
How to verify: `npm run test:aislecheck-prototype` (includes `tests/aislecheck_fallback_harness.cjs`). Local: break `apiBaseUrl` or set short `apiTimeoutMs` → temporary copy; set `liveApiEnabled: false` → almost-ready. Harness must snapshot `getState()` fields after each wait — it returns the live state object.  
Related files: `aislecheck-prototype/aislecheck.js`, `aislecheck-prototype/aislecheck.css`, `tests/test_aislecheck_prototype.py`, `tests/aislecheck_fallback_harness.cjs`, `index.html`

### AisleCheck deterministic historical deal assessment (local)

Date discovered: 2026-08-04  
Context: Wire “Check this price” to grounded historical scoring without LLM / without `deal_assistant`.  
What happened: Interpretation API existed; assessment did not. Grocery history truth is generated TS (`weeklyAdPrices.generated.ts` / Vons twin), not live Supabase (UI bypasses DB for grocery feeds).  
Fix / workaround:
1. Domain module `scripts/deal_assessment/` — `normalize_offer` → `history_repository` (generated TS via `weekly_ad_analysis.benchmarks`) → `comparability` → `scorer` → `assess_deal(tracker_id, retailer, submitted_offer)`.
2. Local API only: `POST /api/aislecheck/assess` in `aislecheck-prototype/server.py` (structured fields only; never reparses free text).
3. Homepage gate: `assessEnabled: false` in production `index.html` — Check this price stays placeholder until Render gets the endpoint. Local preview: set `assessEnabled: true` and empty/`localhost` `apiBaseUrl`.
4. Refuse strong verdicts below 4 comparable weeks: 0–1 → `insufficient_data`; 2–3 → `limited_data` (Early price signal); 4+ → normal benchmark buckets. See `docs/AISLECHECK_ASSESSMENT_POLICY.md` and `scripts/deal_assessment/policy.py`.  
How to verify: `PYTHONPATH=scripts python3 -m unittest tests.test_deal_assessment -v`. Local: `npm run preview:homepage` with `assessEnabled: true` → Doritos understood → Check this price → evidence panel.  
Related files: `scripts/deal_assessment/`, `docs/AISLECHECK_ASSESSMENT_POLICY.md`, `aislecheck-prototype/server.py`, `aislecheck-prototype/aislecheck.js`, `tests/test_deal_assessment.py`, `config/price_benchmark_thresholds.json`

### AisleCheck live API published on homepage

Date discovered: 2026-08-04  
Context: Production activation of hosted deterministic interpretation after Render validation.  
What happened: Merged `release/aislecheck-enable-live-api` (`7b58d23`) into `main` as `dc2b1e5`. Live config: `apiBaseUrl=https://aislecheck-api.onrender.com`, `liveApiEnabled: true`, `exampleSubmitEnabled: true`, assets `?v=ac13`. Diff vs main was only `index.html` + prototype test assertion (no matcher/LLM/scoring changes).  
Fix / workaround: Instant rollback = set `liveApiEnabled: false` on `main` and push (keep `exampleSubmitEnabled: true` unless that flow fails). Free-tier cold start can take ~2–3s on first POST; intermittent edge `404` with `x-render-routing: no-server` until awake. Outage/timeout with live API enabled shows temporary-unavailable copy (**We couldn’t check that deal right now**) with Try again + preserved query + optional Submit as an example — not the almost-ready launch-preview messaging.  
How to verify: https://scrollingtheaisle.com/ source shows `ac13` + live flags; Doritos → understood; cereal → clarify; quinoa → unsupported; conflict → invalid; Check this price → “Still in progress” placeholder.  
Related files: `index.html`, `aislecheck-prototype/aislecheck.js`, `docs/AISLECHECK_API_ACTIVATION.patch.txt`

### AisleCheck wired to deterministic shopper_query (no LLM)

Date discovered: 2026-08-03  
Context: Connect homepage AisleCheck prototype to real normalize → parse → production matcher without deal scoring or `deal_assistant`.  
What happened: Homepage was static JS with keyword fixtures; `shopper_query` is Python (`process_query`) and cannot run in the browser. Subprocess-per-request and TS reimplementation are unnecessary.  
Fix / workaround:
1. Thin local adapter: `aislecheck-prototype/server.py` serves the site and `POST /api/aislecheck` calling `shopper_query.aislecheck_contract.run_aislecheck_query` **in-process** (normalization on).
2. Contract mapper: `scripts/shopper_query/aislecheck_contract.py` → `original_query`, `normalized_query`, `normalizations_applied`, extracted fields, `missing_fields`, `matcher_status`, selected/plausible trackers, `next_action` (`continue|clarify|unsupported|invalid`), reason codes, debug blob.
3. UI states: understood confirmation (“Here’s what AisleCheck understood”) → **Check this price** is a labeled placeholder only; clarify field/product; unsupported; invalid; **Fix it** correction; expandable **Developer debug**.
4. Local query log: `output/aislecheck_query_records/records.jsonl` (gitignored). No third-party analytics of raw queries. Inspect via file or `GET /api/aislecheck/records`.
5. Do not extract parser/matcher into TypeScript for this slice; keep Python as source of truth.  
How to verify: `npm run preview:homepage`; submit “Safeway Doritos 9.75 oz are $2.49 each when I buy four”; expand Developer debug. `npm run test:aislecheck-prototype`.  
Related files: `aislecheck-prototype/server.py`, `aislecheck-prototype/aislecheck.js`, `scripts/shopper_query/aislecheck_contract.py`, `tests/test_aislecheck_shopper_query.py`, `output/aislecheck_query_records/`

### AisleCheck API must not import untracked holdout_labeler

Date discovered: 2026-08-04  
Context: Render deploy of `deploy/aislecheck-assessment-api` built Docker successfully but Uvicorn crashed on import.  
What happened: `shopper_query.schema` imported `PRICE_BASIS_VALUES` / `PROMOTION_TYPES` from `holdout_labeler.paths`. Locally that package exists as **untracked** `scripts/holdout_labeler/` (not in git), so unit tests passed. Render builds from git only, so `COPY scripts` never included it → `ModuleNotFoundError: No module named 'holdout_labeler'`.  
Fix / workaround: Single source of truth in committed `scripts/shopper_query/offer_vocab.py`. Production `shopper_query.schema` imports from there. Local `holdout_labeler.paths` re-exports the same constants (do not duplicate the tuples). Never make production API code depend on labeling-only packages.  
How to verify: `PYTHONPATH=scripts python3 -c "from services.aislecheck_api.app import app; print('import ok')"`; `PYTHONPATH=scripts python3 -m unittest tests.test_aislecheck_api_container_import -v`; Docker: `docker build -f services/aislecheck_api/Dockerfile -t aislecheck-api . && docker run --rm aislecheck-api python -c "from services.aislecheck_api.app import app; print('import ok')"`.  
Related files: `scripts/shopper_query/offer_vocab.py`, `scripts/shopper_query/schema.py`, `services/aislecheck_api/Dockerfile`, `tests/test_aislecheck_api_container_import.py`

### AisleCheck Day 2 hosted assessment validated; scoring still off on main

Date discovered: 2026-08-04  
Context: After Render ran `12090f7` on `deploy/aislecheck-assessment-api`, complete Day 2 gates before public scoring.  
What happened: Hosted `/health` advertises `query: aislecheck.v1` + `assessment: aislecheck_history_v1`. Query regression + assess cases (each / multi-buy / BOGO / limited_data / insufficient_data / invalid_offer / not_comparable / unknown tracker / malformed) passed. CORS allows `https://scrollingtheaisle.com`, blocks unapproved origins. Local homepage × hosted API with temporary `assessEnabled: true` completed interpretation → Fix it → Check this price → verdict, plus failure/retry and mobile. Usefulness feedback UI is **not implemented** yet.  
Fix / workaround: Fast-forwarded `release/aislecheck-deal-assessment` (incl. import fix) to `main` as `3c6d5b8` with **`assessEnabled: false`**. Do **not** merge `8561208` (`release/aislecheck-enable-assessment`) until explicit activation approval. Rollback scoring forever: keep/set `assessEnabled: false`. Rollback interpretation: `liveApiEnabled: false`.  
How to verify: Live `index.html` shows `assessEnabled: false`, assets `ac15`; `GET https://aislecheck-api.onrender.com/health` includes both contracts; `8561208` not ancestor of `main`.  
Related files: `index.html`, `services/aislecheck_api/app.py`, `scripts/deal_assessment/`, `release/aislecheck-enable-assessment`

### AisleCheck public scoring activated

Date discovered: 2026-08-04  
Context: User approved merging activation commit after Day 2 hosted validation.  
What happened: Cherry-picked `8561208` onto `main` as `bf6d52a` (`assessEnabled: true`, assets `ac16`). Live Pages verified Doritos `normal_sale`, Tillamook `weak_sale`, ribs `limited_data`, Chobani tub `insufficient_data`, 30 oz Doritos `not_comparable`, and assess outage → temporary unavailable + Try again (no fake verdict). Hosted `/api/aislecheck/event` remains absent (404s are best-effort local logging only; query/assess unaffected).  
Fix / workaround: Instant rollback = set `assessEnabled: false` in `index.html` and push `main` (optionally bump cache beyond `ac16`).  
How to verify: Live source shows `assessEnabled: true` + `ac16`; Check this price returns evidence panel.  
Related files: `index.html`, `tests/test_deal_assessment.py`

### AisleCheck Chips Ahoy brand-clarify loop

Date discovered: 2026-08-04  
Context: Live AisleCheck after public scoring; user query like “Safeway Chips Ahoy are $1.99”.  
What happened: Parser treated “Chips” inside **Chips Ahoy** as generic chips → `product_brand_unspecified:chips` → “Which brand of chips was it?”. Answering “Chips Ahoy” re-triggered the same prompt. Bare “Chips Ahoy” also failed matcher includes (patterns required “cookies” / flavor words from family includes).  
Fix / workaround: (1) Exclude `\bchips\s*ahoy\b` from the chips brand-unspecified heuristic. (2) Don’t block unique matcher hits on brand-unspecified (package-synonym clarify still blocks). (3) Add YAML include `Chips Ahoy` under `chips_ahoy`. Redeploy Render API — this is server-side, not an `ac*` frontend bump.  
How to verify: `PYTHONPATH=scripts python3 -c "from shopper_query.aislecheck_contract import run_aislecheck_query; print(run_aislecheck_query('Safeway Chips Ahoy are \$1.99')['next_action'], run_aislecheck_query('Safeway Chips Ahoy are \$1.99')['selected_tracker']['id'])"` → `continue chips_ahoy`. Generic “Safeway chips are $2.49” still clarifies brand.  
Related files: `scripts/shopper_query/deterministic_parser.py`, `scripts/shopper_query/behavior.py`, `data/canonical_tracker_families.yaml`, `tests/test_aislecheck_shopper_query.py`

### AisleCheck catalog-wide entity resolution

Date discovered: 2026-08-04  
Context: Feature branch `feature/aislecheck-catalog-entity-resolution` — catalog-wide hardening after the Chips Ahoy one-off.  
What happened: Generic category tokens inside brand names, missing shopper aliases, free-text clarify reparsing, and no clarify progress fingerprint caused misclassification / loops / unreachable trackers beyond Chips Ahoy.  
Fix / workaround:
1. Derive protected phrases + language profiles from `data/canonical_tracker_families.yaml` (+ optional family YAML keys `aliases` / `protected_phrases` / `clarification`, plus `data/entity_resolution/phrase_overlays.yaml`).
2. Parser uses `entity_resolution.protected_phrases` registry instead of one-off brand regexes.
3. Shopper alias layer on top of YAML matching (`shopper_aliases.py`) — does not change weekly-ad includes.
4. Clarify fingerprints ignore product-text drift; frontend sends `prior_clarify_digests` on clarify retries.
5. Audits: `npm run audit:entity-resolution` → `evals/entity-resolution/tracker-coverage-report.json`, `collision-report.json`, `docs/AISLECHECK_TRACKER_LANGUAGE_COVERAGE.md`.
6. Public structured clarification UX gated by `structuredClarificationEnabled` (default **false**). See `docs/AISLECHECK_STRUCTURED_CLARIFICATION_FLAG.md`.
How to verify: `npm run test:entity-resolution`; Chips Ahoy / Sun Chips / Goldfish / Smartfood continue; generic chips still clarifies; second identical brand-clarify escalates with `clarify_loop_broken`.
Related files: `scripts/shopper_query/entity_resolution/`, `docs/AISLECHECK_ENTITY_RESOLUTION_ROOT_CAUSE.md`, `tests/test_entity_resolution.py`, `index.html`

### AisleCheck deterministic-baseline-v1 freeze

Date discovered: 2026-08-05  
Context: Public pre-LLM freeze after structured clarification activation (`44ff557`, asset `ac18`, Render backend `0096b89`).  
What happened: Need an immutable offline + documentation baseline before any LLM shadow work.  
Fix / workaround: Branch `chore/freeze-deterministic-baseline-v1` adds version constants (`scripts/shopper_query/baseline_versions.py`, exposed under `/health` → `versions`), manifests under `docs/baselines/`, frozen eval hashes, integrity command `npm run verify:deterministic-baseline-v1`, and report skeleton `PYTHONPATH=scripts python3 -m baselines.report_deterministic_baseline_v1`. No matching/scoring/UI policy change.  
How to verify: `npm run verify:deterministic-baseline-v1`; catalog eval 276/276; tag `deterministic-baseline-v1` after merge.  
Related files: `docs/baselines/deterministic-baseline-v1.json`, `docs/baselines/deterministic-baseline-v1-policy.md`, `docs/baselines/deterministic-baseline-v1-metrics.md`, `tests/test_deterministic_baseline_v1.py`

