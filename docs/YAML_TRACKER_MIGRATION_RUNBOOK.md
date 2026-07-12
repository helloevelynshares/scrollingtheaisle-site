# YAML Tracker Families Runbook

Source of truth: `data/canonical_tracker_families.yaml`

## Edit tracker families

1. Open `data/canonical_tracker_families.yaml`.
2. Add or edit a family block with:
   - `id` (internal, never shown in UI)
   - `canonical_tracker_family` (card title)
   - `size_format_subtitle` (card subtitle)
   - `display_order`, `homepage_group` (maps to homepage section)
   - `include` / `keep_separate_from` (weekly-ad matching guidance)
3. Regenerate TypeScript metadata:
   ```bash
   npm run generate:canonical-families
   ```
4. Run validation:
   ```bash
   PYTHONPATH=scripts python3 -m unittest tests.test_canonical_families -v
   ```

### Homepage sections (fixed order)

| Order | Section id | Label |
|------:|------------|-------|
| 1 | `stock_up_snacks_and_treats` | Stock-up snacks & treats |
| 2 | `fresh_produce` | Fresh produce |
| 3 | `dairy_breakfast_bakery` | Dairy, breakfast & bakery |
| 4 | `meat_and_seafood` | Meat & seafood |
| 5 | `drinks` | Drinks |

`homepage_group` in YAML maps automatically (`snacks_and_crackers`, `ice_cream` → section 1; `drinks` → section 5).

## Refresh baselines (Safeway + Vons)

Only when a family has **no** baseline in existing CSVs:

```bash
# Add row to data/canonical/price_tracker_baseline_queries_new_only.csv
python3 scripts/seed_safeway_baseline.py --browser-like \
  --input data/canonical/price_tracker_baseline_queries_new_only.csv \
  --merge-csv data/processed/safeway_baseline_candidates_v1.csv
python3 scripts/generate_safeway_feed_matches.py --merge-fallback

python3 scripts/seed_vons_baseline_playwright.py --http-only \
  --input data/canonical/price_tracker_baseline_queries_new_only.csv \
  --merge-csv data/processed/vons_baseline_candidates_v1.csv
python3 scripts/generate_vons_feed_matches.py
```

Do **not** overwrite good baselines unless running an explicit refresh workflow.

## Rebuild weekly ad graphs

Uses cached `split_offer_items.csv`, never re-extracts PDFs.

```bash
npm run generate:weekly-ad-prices
# or incremental:
python3 scripts/generate_weekly_ad_prices.py --product-id doritos_5_13oz
```

Legacy canonical ids (e.g. `strawberries`) are merged into mapped YAML families automatically.

### Canonical match eligibility (required for graph updates)

Weekly ad rows must pass **eligibility** before writing `weeklyAdPrices.generated.ts` / `vonsWeeklyAdPrices.generated.ts`. Pattern match alone is not enough for families with rules in `config/canonical_match_rules.yaml` (or per-family `match_eligibility` in YAML).

Checks: product-type compatibility, unit/package, hard-negative keywords, confidence threshold. Outcomes:

| `match_decision` | Tracker graph updated? |
|------------------|------------------------|
| `accepted` | Yes |
| `rejected` | No, ad deal only |
| `manual_review` | No, needs human review |

After every generate/import run, inspect:

```bash
open output/weekly_deals/YYYY-MM-DD/canonical_match_audit.md
```

Section **Graph update safety check** lists blocked all-time lows and tempting false matches (e.g. smoked salmon vs fresh salmon fillet tracker).

Validate:

```bash
PYTHONPATH=scripts python3 scripts/validate_weekly_ad_prices.py
PYTHONPATH=scripts python3 -m unittest tests.test_canonical_match_eligibility -v
```

Import workflow (`scripts/import_weekly_ad.py`) regenerates prices and writes the same audit files per week.

## Update Popular this week

Edit `data/popular_this_week.yaml` manually (not auto-generated):

```bash
npm run generate:canonical-families
```

Verify ids resolve:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_canonical_families.TestPopularThisWeek -v
```

## Costco regional matching

- Safeway tab → San Francisco (`san_francisco` / `costco_sf`)
- Vons tab → Tustin (`tustin` / `costco_oc`)
- Seattle data imported but not wired to grocery tabs

```bash
npm run import:costco-data
npm run generate:price-comparisons
```

No confident match → card shows comparison unavailable / not found.

## Verify homepage ordering

```bash
npm run generate:canonical-families
npm run build:price-tracker
```

Open `/staging-price-tracker/`, confirm section chips, search, Popular this week, and 4-col desktop grid.

## Full build

```bash
npm run build:price-tracker
PYTHONPATH=scripts python3 -m unittest tests.test_canonical_families tests.test_normalization tests.test_ui_copy -v
```
