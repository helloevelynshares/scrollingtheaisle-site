# AisleCheck Query API (hosted)

Deterministic normalize → parse → production matcher. No LLM. No deal scoring.

This service is independent of the homepage opt-in example Supabase RPC.

## Local run

From the repo root:

```bash
python3 -m pip install -r services/aislecheck_api/requirements.txt
npm run dev:aislecheck-api
```

Health: http://127.0.0.1:8080/health  
Query: `POST http://127.0.0.1:8080/api/aislecheck` with `{"query":"…"}`

## Tests

```bash
python3 -m pip install -r services/aislecheck_api/requirements.txt httpx
npm run test:aislecheck-api
```

## Recommended host

**Render** (Docker free/starter web service) or **Railway** — both run this Python image
in-process with filesystem access to YAML catalogs.

Supabase Edge Functions are Deno/TS only and cannot import `shopper_query` without a rewrite.

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `AISLECHECK_CORS_ORIGINS` | production + local preview origins | Comma-separated allowlist (no `*`) |
| `AISLECHECK_MAX_QUERY_CHARS` | `500` | Max query length |
| `AISLECHECK_TIMEOUT_MS` | `8000` | Soft latency budget |
| `AISLECHECK_RATE_LIMIT_PER_MINUTE` | `30` | Per-IP in-memory limit |
| `AISLECHECK_DEBUG_LOG` | off | Log action + latency only (never raw query) |

## Frontend config (activation is a separate, confirmed step)

Keep production on fallback until the hosted service is verified:

```html
<script>
  window.__AISLECHECK_CONFIG__ = {
    apiBaseUrl: "",
    liveApiEnabled: false,
    exampleSubmitEnabled: true
  };
</script>
```

Local test against hosted API (do not push):

```html
<script>
  window.__AISLECHECK_CONFIG__ = {
    apiBaseUrl: "https://YOUR-SERVICE.onrender.com",
    liveApiEnabled: true,
    exampleSubmitEnabled: true
  };
</script>
```

## Deploy checklist

1. Push this branch / merge API scaffold to a deployable ref.
2. Create Render web service from `services/aislecheck_api/Dockerfile` (repo root context) or `render.yaml`.
3. Confirm `GET /health`.
4. Run sample `POST /api/aislecheck` cases (understood / clarify / unsupported / invalid).
5. Point local homepage `apiBaseUrl` at the hosted URL and verify CORS.
6. Only after confirmation: set production `apiBaseUrl` + `liveApiEnabled: true` on `main`.
7. Rollback: set `liveApiEnabled: false` (or clear `apiBaseUrl`) and redeploy Pages.

Do not enable request-body logging on the host dashboard.
Do not log raw shopper queries.
