# Pre-LLM measurement window

Code baseline: Git tag `deterministic-baseline-v1` → commit `1cf5be3`  
Public main at freeze merge: `1cf5be3` (shopper FE still `44ff557` behavior: `structuredClarificationEnabled: true`, `ac18`)  
Render backend at code freeze: deploy branch `deploy/aislecheck-deterministic-baseline-v1` @ `1cf5be3` (additive `/health.versions`; switch required)

## Important: code baseline ≠ production-data window

| Phase | Meaning | Status criteria |
|---|---|---|
| **Code baseline official** | Tag + main + Render versions match freeze | Tag pushed; main includes freeze; Render `/health.versions` reports baseline constants |
| **Production-data window start** | Metric collection for Milestone 1 reports | Code baseline official **and** measurement instrumentation activated |

Do **not** mark the production baseline window as started merely because the Git tag was pushed.

## Window definition (production data)

| Boundary | Rule |
|---|---|
| Start | Only after **all** of: (1) tag `deterministic-baseline-v1` on `1cf5be3` is on origin, (2) `main` includes freeze artifacts, (3) Render reports baseline `versions` on `/health`, (4) Milestone 1 instrumentation is live (query/session/event capture + review path). Record start UTC + SHAs. |
| End | Before any LLM shadow traffic, LLM provider wiring in the public path, or matcher/assessment policy change. |
| Target volume | At least **100 valid external queries** where practical (not a significance guarantee). |
| Review | Include a **manually reviewed sample** (prioritize continues + clarifies that later continued). |
| Sessions | Record unique anonymous `session_id` counts when available. |

## Closing checklist

- [ ] Code baseline official (tag + main + Render versions)
- [ ] Milestone 1 instrumentation activated
- [ ] Enough diverse queries (brands, generics, multi-family, missing price, BOGO/multi-buy)
- [ ] Reviewed sample completed; wrong-confident rate computed on **reviewed continues only**
- [ ] Failure taxonomy populated (unsupported reasons, clarify kinds, assess verdicts)
- [ ] Latency median/p95 for query and assess recorded (note cold starts)
- [ ] Helpfulness feedback captured if UI collects it
- [ ] Production incidents noted
- [ ] Version drift checked: live `ac*` asset, health contracts/versions, and Render SHA still match baseline (or deltas documented)
- [ ] Report written under `reports/deterministic-baseline-v1/YYYY-MM-DD_to_YYYY-MM-DD.*`

## Report command

```bash
PYTHONPATH=scripts python3 -m baselines.report_deterministic_baseline_v1 \
  --start YYYY-MM-DD --end YYYY-MM-DD \
  --out-dir reports/deterministic-baseline-v1
```

If production event logs are unavailable, the command emits a skeleton report with `production_metrics_status: unavailable`.
