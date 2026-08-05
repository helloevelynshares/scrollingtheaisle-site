# Structured clarification compatibility decision

Date: 2026-08-04  
Branch: `feature/aislecheck-catalog-entity-resolution` → release/deploy

## Decision

Ship parser/matcher/loop-protection backend fixes now.  
Keep **public structured clarification UX off** via:

```js
structuredClarificationEnabled: false
```

## Why public FE is safe against the new backend

| Response change | Old public FE (`ac16`) handling |
|---|---|
| Additive `clarify_fingerprint` | Ignored |
| Optional `prior_clarify_digests` request | Not sent; loop break inactive until FE upgrade |
| Loop break → `unsupported` + `clarify_loop_broken` | Existing unsupported view |
| Package/multi-family → `clarify` / `ambiguous_product` + `plausible_trackers` | Existing product-pick UI (pre-existing) |
| Exact products continue (Chips Ahoy, etc.) | Existing continue path |

No deal-assessment, LLM, or Supabase changes.

## Flag semantics

| | `structuredClarificationEnabled: false` (public) | `true` (local / activation) |
|---|---|---|
| Parser/matcher hardening | on | on |
| `prior_clarify_digests` | sent after FE upgrade | sent |
| Loop terminal UI copy | standard unsupported | loop-specific copy |
| Loop terminal candidate picks | **no** (API forces unsupported) | yes when candidates exist |
| Request body | `structured_clarification: false` | `structured_clarification: true` |

## Activation

Separate tiny commit flips `false` → `true` and bumps `ac17` → next cache if needed.  
Rollback: set `structuredClarificationEnabled: false`.
