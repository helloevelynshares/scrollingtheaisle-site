# AisleCheck eval freeze policy

Baseline: `deterministic-baseline-v1`

## Eval classes

### Frozen eval
Committed JSONL/JSON (or frozen_reference test modules) listed in `docs/baselines/deterministic-baseline-v1-evals.json` with SHA-256 hashes.

- May change **only** via an explicit new baseline version (e.g. `deterministic-baseline-v2`) and updated hashes.
- Do **not** silently append production failures to frozen files.
- Integrity check: `npm run verify:deterministic-baseline-v1`

### Development eval
Working cases under `evals/development/` (or untracked local harness files).

- Used while iterating on matcher/parser/clarification.
- Not a public quality claim until promoted.

### Production-derived candidate eval
Cases mined from reviewed public traffic after the pre-LLM measurement window.

- Land in `evals/development/` or `evals/candidates/` first.
- Promote into a new frozen baseline only after review and a baseline-version bump.

### Future holdout promotion
1. Label candidate cases offline (never require labeling packages in the Render image).
2. Score against the frozen deterministic pipeline.
3. Document precision/recall deltas vs `deterministic-baseline-v1`.
4. Cut a new baseline if policy or catalog intentionally changes.

## Related
- Manifest: `docs/baselines/deterministic-baseline-v1.json`
- Eval hashes: `docs/baselines/deterministic-baseline-v1-evals.json`
