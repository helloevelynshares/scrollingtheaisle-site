# Safeway price tracker: TikTok food SKU workflow

Shift from generic staples (`manual_canonical_50.csv`) to food SKUs aligned with TikTok performance.

## Inputs

| File | Role |
|------|------|
| `bulk_transcripts.csv` | TikTok transcripts + views → `data/processed/tiktok_item_mentions.csv` |
| `data/canonical/manual_canonical_50.csv` | Legacy staples (10 non-food items excluded) |
| `scripts/output/safeway_search_seed.jsonl` | Optional prior Safeway crawl (staples era) |

## Outputs

| File | Role |
|------|------|
| `data/processed/tiktok_item_mentions.csv` | Food mentions weighted by views |
| `data/canonical/safeway_tracked_items_v1.csv` | **50** TikTok-informed food SKUs (`accepted_pid` / `accepted_upc` blank) |
| `scripts/output/safeway_tracked_candidates.jsonl` | Full Playwright API response per ledger row |
| `data/processed/safeway_tracked_candidates_v1.csv` | Top 15 candidates per item for manual SKU pick |

## Commands

```bash
# Audit what’s on disk
python scripts/audit_tiktok_food_inputs.py

# 1) Extract food mentions from TikTok transcripts
python scripts/extract_tiktok_food_mentions.py

# 2) Fetch Safeway candidates for ledger search queries (manual SKU pick after)
python scripts/seed_safeway_tracked_playwright.py --headful --delay 3
python scripts/seed_safeway_tracked_playwright.py --headful --delay 3 --resume
python scripts/seed_safeway_tracked_playwright.py --max-items 5 --delay 3
# Review data/processed/safeway_tracked_candidates_v1.csv → fill ledger accepted_pid/upc
```

## Excluded non-food (not in v1 ledger)

bottled water, paper towels, toilet paper, dish soap, laundry detergent, shampoo, toothpaste, diapers, dog food, cat food

## View priority (mentions)

- views ≥ 20,000 → priority **3.0**
- views ≥ 10,000 → priority **2.0**
- views &lt; 10,000 → priority **1.0**

No fuzzy matching in v1, fill `accepted_pid` / `accepted_upc` in the ledger after reviewing candidates.
