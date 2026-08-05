# Pre-LLM measurement window

Baseline tag target: `deterministic-baseline-v1`  
Public main at freeze: `44ff557`  
Render backend: `0096b89` on `deploy/aislecheck-catalog-entity-resolution`

## Window definition

| Boundary | Rule |
|---|---|
| Start | After Git tag `deterministic-baseline-v1` exists on the freeze commit (or immediately after this freeze lands on main if tagging is deferred — record the exact start SHA/time). |
| End | Before any LLM shadow traffic, LLM provider wiring in the public path, or matcher/assessment policy change. |
| Target volume | At least **100 valid external queries** where practical (not a significance guarantee). |
| Review | Include a **manually reviewed sample** (prioritize continues + clarifies that later continued). |
| Sessions | Record unique anonymous `session_id` counts when available. |

## Closing checklist

- [ ] Enough diverse queries (brands, generics, multi-family, missing price, BOGO/multi-buy)
- [ ] Reviewed sample completed; wrong-confident rate computed on **reviewed continues only**
- [ ] Failure taxonomy populated (unsupported reasons, clarify kinds, assess verdicts)
- [ ] Latency median/p95 for query and assess recorded (note cold starts)
- [ ] Helpfulness feedback captured if UI collects it
- [ ] Production incidents noted
- [ ] Version drift checked: live `ac*` asset, health contracts, and Render SHA still match baseline (or deltas documented)
- [ ] Report written under `reports/deterministic-baseline-v1/YYYY-MM-DD_to_YYYY-MM-DD.*`

## Report command

```bash
PYTHONPATH=scripts python3 -m baselines.report_deterministic_baseline_v1 \
  --start YYYY-MM-DD --end YYYY-MM-DD \
  --out-dir reports/deterministic-baseline-v1
```

If production event logs are unavailable, the command emits a skeleton report with `production_metrics_status: unavailable`.
