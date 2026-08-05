# Milestone 1 — AisleCheck measurement foundation (implementation plan)

Branch: `feature/aislecheck-measurement-foundation`  
Depends on: code baseline `deterministic-baseline-v1` @ `1cf5be3`  
**Do not implement in this document.** Planning only. No LLM. No shopper-behavior change in Milestone 1 beyond additive instrumentation and optional usefulness UI behind a flag.

## Goals

1. Durable, privacy-aware capture of query / session / assess / interaction events in production.
2. Minimal review workflow for wrong-confident sampling.
3. Wire `scripts/baselines/report_deterministic_baseline_v1.py` to real aggregates.
4. Start the **production-data** measurement window only after instrumentation is activated.

## 1. Existing surfaces (current code)

### Supabase

| Asset | Role |
|---|---|
| `supabase/migrations/20260804_aislecheck_examples.sql` | Table `aislecheck_examples` + RPC `submit_aislecheck_example` |
| `supabase/migrations/20260805_aislecheck_examples_trim.sql` | Trim parity with JS |
| RLS | Deny-all for anon/authenticated; insert only via security-definer RPC |

Stores **opt-in raw example queries only**. No session/event/assess/usefulness tables.

### Frontend (`aislecheck-prototype/aislecheck.js` + `index.html`)

| Flag | Live value | Role |
|---|---|---|
| `liveApiEnabled` | true | Query API |
| `assessEnabled` | true | Assess API |
| `structuredClarificationEnabled` | true | Candidate UX |
| `exampleSubmitEnabled` | true | Opt-in examples |

- `session_id` in `sessionStorage` (`sta_aislecheck_session`) — sent on query/assess; **not persisted** server-side today.
- `logEvent` → `POST /api/aislecheck/event` with `raw_query` + parser summary — **hosted API has no `/event` route** (404 best-effort).
- Events already named: `check_price_assess`, `clarify_*`, `correction_submit`, `request_product`, etc.
- Client **ignores** `request_id` from API responses.
- **No usefulness / helpful UI** on assessment view.
- Cloudflare `analytics.js` is page beacon only (no query content).

### Hosted API (`services/aislecheck_api/app.py`)

- Returns `request_id`; strips `debug` when not debugging.
- In-memory `/metrics` only (resets on restart; no query text).
- `AISLECHECK_DEBUG_LOG` never logs raw query.
- Accepts `session_id` but does not store it.

### Local prototype (`aislecheck-prototype/server.py`)

- Appends to `output/aislecheck_query_records/records.jsonl` including raw query (local-only).
- Implements `/api/aislecheck/event` and `/api/aislecheck/records`.

### Baseline linkage

- Metrics formulas: `docs/baselines/deterministic-baseline-v1-metrics.md`
- Report skeleton: `scripts/baselines/report_deterministic_baseline_v1.py` → `production_metrics_status: unavailable`
- Window rules: `docs/baselines/deterministic-baseline-v1-measurement-window.md`

## 2. Proposed schema (minimum)

Prefer **Postgres via Supabase** (already used for examples). Keep RLS deny-by-default; writes via security-definer RPCs or server service role from Render only.

### `aislecheck_sessions`

| Column | Notes |
|---|---|
| `session_id` text PK | Client anonymous id |
| `first_seen_at` / `last_seen_at` timestamptz | |
| `user_agent_hash` text nullable | Optional hashed UA; no IP stored long-term |
| `baseline_id` text | e.g. `deterministic-baseline-v1` |

### `aislecheck_query_events`

| Column | Notes |
|---|---|
| `id` uuid PK | |
| `request_id` text unique | From API |
| `session_id` text | FK soft |
| `created_at` | |
| `contract_version` / pipeline versions | From health/constants |
| `next_action` / `clarify_kind` / `matcher_status` | |
| `reason_codes` jsonb | Failure taxonomy |
| `selected_tracker_id` / `plausible_tracker_ids` | |
| `extracted` jsonb | price, promo, retailer, package — **structured only** |
| `latency_ms` int | |
| `http_status` int | |
| `query_fingerprint` text | HMAC/hash of normalized query — **not raw text by default** |
| `raw_query_retained` bool | default false |
| `raw_query` text nullable | **only if retention policy allows** (see §4) |

### `aislecheck_assess_events`

Mirror query events for `/assess`: tracker_id, retailer, normalized offer summary, verdict, latency, request_id, session_id.

### `aislecheck_ui_events`

Replace orphan FE `logEvent` payloads: event name, session_id, optional request_id, small jsonb payload **without raw_query** unless explicitly allowed.

### `aislecheck_usefulness`

| Column | Notes |
|---|---|
| `request_id` / `session_id` | |
| `rating` | e.g. helpful / not_helpful |
| `created_at` | |

### `aislecheck_review_labels`

Manual review sample: request_id, label enum (`correct_continue`, `wrong_confident`, `should_clarify`, `unsupported_correct`, …), reviewer notes, created_at.

**Do not** put review labels in the public anon path.

## 3. Event model

| Event | Producer | Persist |
|---|---|---|
| `query_completed` | Render after successful/failed query | `aislecheck_query_events` |
| `assess_completed` | Render after assess | `aislecheck_assess_events` |
| `ui_*` | FE via new hosted `/api/aislecheck/event` or direct RPC | `aislecheck_ui_events` |
| `usefulness` | FE after assess | `aislecheck_usefulness` |
| `example_submitted` | existing RPC | `aislecheck_examples` (unchanged) |

Join key: prefer `request_id` (server) + `session_id` (client). FE must start storing/echoing `request_id`.

## 4. Privacy and retention — raw query recommendation

**Recommendation: do not store raw query by default in production measurement tables.**

| Approach | Pros | Cons |
|---|---|---|
| **A. Hash-only (recommended default)** | Enables volume/latency/taxonomy metrics without PII risk | Cannot re-read exact text for review |
| **B. Short-retention raw (optional, reviewed sample only)** | Supports wrong-confident review | Privacy + retention ops cost |
| **C. Always store raw** | Max debug | Unnecessary for baseline metrics; conflicts with “no raw in CF analytics” stance |

**Minimum-retention plan:**

1. Production path stores **`query_fingerprint`** = HMAC-SHA256(normalized_query, server secret) + optional length bucket.
2. Raw query **not** written to `aislecheck_query_events` by default (`raw_query_retained=false`).
3. Opt-in examples remain in `aislecheck_examples` (existing product path).
4. For review sampling: either (a) ask user “Share this query for product improvement” before retaining raw for N days, or (b) retain raw ≤7 days behind a feature flag `rawQueryRetentionEnabled`, auto-purge job, never export to analytics vendors.
5. Cloudflare / third-party beacons never receive raw query (already true).

## 5. Failure taxonomy (persist reason_codes)

Reuse contract codes already emitted:

- Query: `matcher_no_match`, `ambiguous_tracker_match`, `product_brand_unspecified:*`, `clarify_loop_broken`, `clarify_loop_terminal`, `user_rejected_candidates`, …
- Assess: `insufficient_data`, `limited_data`, `not_comparable`, `invalid_offer`, verdict labels

Reporter aggregates `failure_reason_distribution` from stored events — no new scoring policy.

## 6. Review workflow

1. Nightly (or on-demand) sample of continues + clarify→continue chains.
2. Reviewer UI or CSV export with **structured extracted fields + tracker**; raw text only if retention allowed.
3. Write `aislecheck_review_labels`.
4. Compute `wrong_confident_match_rate` on **reviewed continues only** (per metrics doc).
5. Promote interesting failures into `evals/development/` candidates — never silently into frozen evals.

## 7. Deterministic baseline report linkage

Extend `report_deterministic_baseline_v1` to:

- Accept `--from-db` / service-role connection when available.
- Filter by `baseline_id` + version fields + date window.
- Fill counts/rates from SQL; keep `unavailable` when empty.
- Emit cost block with LLM = $0 / invocations = 0.

## 8. Migration order

1. Docs + feature flags (this plan).
2. Supabase migrations: sessions → query_events → assess_events → ui_events → usefulness → review_labels (+ purge function).
3. Render: persist query/assess events server-side (most reliable; no FE dependency).
4. Hosted `/api/aislecheck/event` (or RPC) for UI events; stop 404s.
5. FE: attach `request_id`; gate usefulness UI behind `usefulnessFeedbackEnabled: false` initially.
6. Review export script + labels writer.
7. Reporter DB mode.
8. Activate flags → **then** mark production-data window start in docs/notes with UTC + SHAs.

## 9. Feature flags

| Flag | Default | Purpose |
|---|---|---|
| `measurementPersistEnabled` | false (server env) | Write events to Supabase |
| `rawQueryRetentionEnabled` | false | Allow short-lived raw storage |
| `usefulnessFeedbackEnabled` | false (FE) | Show helpful/not helpful |
| `measurementEventClientEnabled` | false (FE) | Send UI events to hosted `/event` |

Rollback: set persist flags false; FE flags false. Data already written remains; ingestion stops.

## 10. Rollout and rollback

1. Deploy schema (no FE change).
2. Deploy API with persist behind env flag (off).
3. Enable persist in Render for staging/self-test.
4. Enable for production; verify rows without raw text.
5. Enable client events + usefulness behind FE flags (separate tiny commits).
6. Record measurement-window start.

Rollback: disable env/FE flags. Do not delete schema. Do not change matcher/assess.

## 11. Explicit non-goals (Milestone 1)

- No LLM, no shadow traffic
- No matching / clarification / assessment policy changes
- No change to public structured clarification behavior
- No second Render service

## 12. Blockers before implementation

1. **Render must switch** to `deploy/aislecheck-deterministic-baseline-v1` @ `1cf5be3` so `/health.versions` matches the code baseline (manual step).
2. Decide raw-query policy (**recommend hash-only default**).
3. Confirm Supabase service-role usage from Render (secret already or new).
4. Approve usefulness UI copy before enabling FE flag.
