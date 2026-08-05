# deterministic-baseline-v1 test results

Recorded: 2026-08-05  
Branch: `chore/freeze-deterministic-baseline-v1`  
Public main SHA at freeze: `44ff557`  
Method: clean tree sync of HEAD + freeze artifacts; `PYTHONPATH=scripts`; no reliance on untracked `holdout_labeler` / `deal_assistant`.

## Summary

| Suite | Command | Pass | Fail | Skip | Duration | Notes |
|---|---|---:|---:|---:|---:|---|
| Entity-resolution | `python3 -m unittest tests.test_entity_resolution -v` | 24 | 0 | 0 | 15.459s | Includes clarification-loop tests |
| Catalog eval | `python3 -m shopper_query.entity_resolution.run_catalog_eval` | 276 | 0 | 0 | 26.509s | `wrong_confident_match_count=0` |
| Shopper-query | `python3 -m unittest tests.test_shopper_query tests.test_aislecheck_shopper_query -v` | 39 | 0 | 0 | 2.001s | Parser + contract |
| Matcher eligibility | `python3 -m unittest tests.test_canonical_match_eligibility -v` | 63 | 0 | 0 | 1.420s | Weekly-ad package gates |
| API query + assess | `python3 -m unittest tests.test_aislecheck_api -v` | 23 | 0 | 0 | 1.739s | Includes health versions assert |
| Deal-assessment | `python3 -m unittest tests.test_deal_assessment -v` | 26 | 0 | 0 | 0.041s | Policy + normalize |
| Frontend / prototype | `python3 -m unittest tests.test_aislecheck_prototype tests.test_aislecheck_shopper_query -v` | 33 | 0 | 0 | 2.120s | Public assets + contracts |
| Container import | `python3 -m unittest tests.test_aislecheck_api_container_import -v` | 3 | 0 | 0 | 0.308s | No holdout_labeler |
| Baseline integrity | `python3 -m unittest tests.test_deterministic_baseline_v1 -v` | 7 | 0 | 0 | 0.173s | Also `npm run verify:deterministic-baseline-v1` |
| Production app smoke | import FastAPI app + Chips Ahoy continue / chips clarify | 1 | 0 | 0 | 1.545s | Clean scripts path |

**Total deterministic suites run above: all required suites executed and passed.**

## Catalog eval detail

```
total: 276
passed: 276
failed: 0
wrong_confident_match_count: 0
loop_termination_ok: true
```

## Pre-existing unrelated failure (not part of AisleCheck baseline)

| Suite | Command | Result |
|---|---|---|
| Canonical families / popular week | `python3 -m unittest tests.test_canonical_families -v` | **25 tests, 2 failures** |

Failures:
- `test_popular_loads` expects week `2026-07-08`, data has `2026-07-29`
- `test_multi_family_refs` expects ≥1 multi-family popular refs, found 0

**Production impact:** Homepage popular-this-week content drift only. Does **not** affect AisleCheck parse/match/clarify/assess runtime.

## Versions exercised

- `deterministic_pipeline_version`: `deterministic_pipeline_v1`
- `catalog_version`: `catalog_v1` (86 active trackers)
- `entity_resolution_version`: `entity_resolution_v1`
- `assessment_policy_version`: `aislecheck_history_v1`
- `clarification_policy_version`: `structured_clarification_v1`
- `query_contract_version`: `aislecheck.v1`
- Frontend asset: `ac18`
- `llm_used`: false
