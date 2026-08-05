# deterministic-baseline-v1 metrics

Formulas for offline quality and later production windows.  
**Absence of a user correction is not proof of correctness.** Unreviewed production continues are counted separately from reviewed continues.

## Eligibility

| Term | Definition |
|---|---|
| Submitted query | Client POST to `/api/aislecheck` that reaches the server (includes invalid/empty rejected at edge if logged). |
| Valid query | HTTP 200 contract response with parseable `next_action` ∈ {continue, clarify, unsupported, invalid} and non-empty extracted intent (product and/or price attempt). Empty / oversized / rate-limited are **invalid or service**, not valid. |
| Eligible valid query | Valid query during the measurement window for the documented code SHA / feature flags. |
| Reviewed query | Human reviewer labeled the outcome (correct tracker / wrong tracker / should-clarify / unsupported-correct / etc.). |

## Rates

### submitted_query_count
Count of POSTs to `/api/aislecheck` in the window.

### valid_query_rate
`valid_queries / submitted_queries`  
(Exclude pure transport failures from the numerator; include them in service failure.)

### deterministic_safe_resolution_rate
`queries that reach a confirmed tracker (next_action continue with selected_tracker) without later reviewer marking wrong-confident / `
`eligible valid queries`  
For **unreviewed** traffic, report a separate `unreviewed_continue_rate` — do **not** equate it to safe resolution.

### direct_resolution_rate
`continues with no prior clarify turn in the session for that deal / eligible valid queries`

### clarification_rate
`responses with next_action=clarify / eligible valid queries`

### clarification_completion_rate
`sessions that clarified then later continued to a tracker / sessions that received at least one clarify`  
Requires session linkage (`session_id`).

### unsupported_rate
`next_action=unsupported / eligible valid queries`

### invalid_rate
`next_action=invalid (or HTTP 4xx invalid_request/empty/oversized) / submitted queries`

### assessment_completion_rate
`successful `/api/aislecheck/assess` with ok=true and a verdict status / continues that invoked assess`  
If assess was not offered/invoked, exclude from denominator or report separately.

### insufficient_history_rate
`assess responses with verdict insufficient_data / completed assessments`

### helpfulness_rate
`explicit positive usefulness feedback / feedback responses received`  
Do not impute helpfulness from silence.

### correction_rate
`deals where user used Fix it or changed interpretation before assess / continues shown to user`

### wrong_confident_match_rate
`reviewed queries that continued to the wrong tracker / reviewed queries that continued to any tracker`  
**Requires review.** Offline proxy at freeze: catalog eval `wrong_confident_match_count / continue-expecting cases` (= 0 / positives at freeze).

### query_service_failure_rate
`5xx + timeout + network failure on `/api/aislecheck` / submitted attempts`

### assessment_service_failure_rate
`5xx + timeout + network failure on `/api/aislecheck/assess` / assess attempts`

## Latency

- **median / p95 query latency:** server-side processing time when available; else client round-trip for `/api/aislecheck`.
- **median / p95 assessment latency:** same for `/api/aislecheck/assess`.

Report cold-start separately on Render free tier when possible.

## Cost (deterministic baseline)

- LLM token cost = **$0**
- LLM invocation count = **0**

## Offline vs production

1. **Offline quality baseline** — catalog eval 276/276, unit/API suites (this freeze).
2. **Initial public-production baseline** — first tagged window after `deterministic-baseline-v1` with reviewed sample.
3. **Later pre-LLM production window** — extended collection before any LLM shadow traffic.
