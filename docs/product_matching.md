# Product matching scaffold

Isolated dry-run evaluation for weekly-ad product matching. **Not wired into
production** (`generate_weekly_ad_prices.py` is unchanged).

## Layout

| Path | Role |
|---|---|
| `data/product_matching/eval_cases.jsonl` | Labeled evaluation dataset |
| `data/product_matching/corrections.yaml` | Durable human corrections / aliases (read-only for production) |
| `scripts/product_matching/` | Wrapper around production matcher + eval CLI |
| `docs/product_matching.md` | This file |

## Run the eval

```bash
cd /path/to/scrollingtheaisle-site
PYTHONPATH=scripts python3 -m product_matching.eval_runner
```

Useful flags:

```bash
PYTHONPATH=scripts python3 -m product_matching.eval_runner --failures-only
PYTHONPATH=scripts python3 -m product_matching.eval_runner --json > /tmp/match_eval.json
```

The runner:

- Calls the **same** include/exclude patterns and eligibility gate as production
- Does **not** write `*.generated.ts`, CSV, or Supabase rows
- Surfaces open `baseline_bug` rows from `corrections.yaml` so wrong store
  baselines can be fixed in a separate reviewed change

## Eval case schema (`eval_cases.jsonl`)

One JSON object per line:

```json
{
  "id": "notes_seed_butter_not_butter",
  "offer_text": "O Organics Seed Butter",
  "expected_family_id": "butter_16oz",
  "expected_decision": "reject",
  "must_not_match_family_ids": ["butter_16oz"],
  "category": "false_match_sibling",
  "source": "docs/PROJECT_NOTES.md Jul 22",
  "notes": "Seed butter matched butter_16oz",
  "package_text": ""
}
```

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Stable slug |
| `offer_text` | yes | Flyer / retailer product string |
| `expected_family_id` | yes | Canonical tracker family under test |
| `expected_decision` | yes | `accept`, `reject`, or `manual_review` |
| `must_not_match_family_ids` | yes (may be `[]`) | Families that must **not** auto-accept this offer |
| `category` | yes | Bucket for reporting (e.g. `false_match_brand`) |
| `source` | yes | Where the label came from |
| `notes` | yes | Short human context |
| `package_text` | no | Size/package line (eligibility often needs this) |
| `price` | no | Defaults to `4.99` |

## How to add a case when a human corrects a match

1. **Reproduce** the bad (or newly correct) offer text from the flyer or audit.
2. **Append one JSONL line** to `data/product_matching/eval_cases.jsonl` with
   `expected_decision` set to what the matcher *should* do after your fix.
3. **Document the correction** in `data/product_matching/corrections.yaml`
   (`kind`: `alias`, `hard_negative`, `baseline_bug`, or `note`; set
   `status` to `applied_in_yaml` once YAML/rules are updated, or `open` if
   deferred).
4. If the fix belongs in matching vocabulary, edit
   `data/canonical_tracker_families.yaml` (`include` / `keep_separate_from`)
   and/or `config/canonical_match_rules.yaml` — that is a separate production
   change; this scaffold only records and measures.
5. **Re-run the eval** and confirm the new case passes (and watch for
   regressions in the failure list).
6. Optionally add a short entry to `docs/PROJECT_NOTES.md` for future agents.

### Example: new false accept

Offer “Cape Cod Sea Salt Kettle Chips” was auto-accepted onto
`kettle_brand_chips`. After adding a `keep_separate_from` phrase:

```json
{"id":"notes_cape_cod_sea_salt_not_kettle_brand","offer_text":"Cape Cod Sea Salt Kettle Chips","expected_family_id":"kettle_brand_chips","expected_decision":"reject","must_not_match_family_ids":["kettle_brand_chips"],"category":"false_match_brand","source":"human review 2026-07-25","notes":"Cape Cod must stay off Kettle Brand chart"}
```

### Example: new alias that should accept

```json
{"id":"notes_sun_chips_one_word","offer_text":"SunChips Harvest Cheddar 7 oz","expected_family_id":"sun_chips_7oz","expected_decision":"accept","must_not_match_family_ids":[],"category":"true_match","source":"human review","notes":"One-word SunChips spelling"}
```

## Metrics

| Metric | Definition |
|---|---|
| Correct accepts | Expected `accept` and matcher accepted |
| Correct rejects | Expected `reject` and matcher rejected (or no pattern hit) |
| Incorrect automatic accepts | Matcher accepted when it should not (includes `must_not_match` violations) |
| Incorrect rejects | Expected accept (or manual_review) but got reject / missed accept |
| Manual-review decisions | Cases where actual decision is `manual_review` |
| Precision | correct_accepts / (correct_accepts + incorrect_automatic_accepts) |
| Recall | correct_accepts / expected_accepts that should have accepted |
| False automatic match rate | incorrect_automatic_accepts / all actual accepts |

## Isolation contract

- Do not import this package from `generate_weekly_ad_prices.py` until an
  explicit opt-in flag is reviewed.
- `corrections.yaml` is **not** applied as live overrides yet.
- No LLM is used.
