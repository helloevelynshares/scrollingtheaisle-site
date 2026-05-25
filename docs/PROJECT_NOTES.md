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

Add notes here for weekly ad parsing, OCR/vision extraction, canonical item matching, package size issues, and price normalization.

TikTok mentions: `python scripts/extract_tiktok_food_mentions.py` reads `bulk_transcripts.csv` → `data/processed/tiktok_item_mentions.csv`.

## Price Tracking Logic

Add notes here for baseline prices, promo expiration behavior, effective price, lowest seen price, and canonical item rules.

## Cursor / Dev Workflow Notes

Add notes here for useful Cursor prompts, commands, migrations, local testing, and deployment steps.

Living notes rule: `.cursor/rules/project-notes.mdc` — agents should read and update `docs/PROJECT_NOTES.md`.

Playwright setup: `pip install -r scripts/requirements.txt && playwright install chromium`

## Open Questions

Track unresolved questions here.
