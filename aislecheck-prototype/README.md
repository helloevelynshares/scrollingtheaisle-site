# AisleCheck (public Variation 4)

Homepage AisleCheck ships as **Variation 4** on production.

Deterministic `scripts/shopper_query/` powers `/api/aislecheck` when that API is
available (local preview server). GitHub Pages is static-only, so live
“Check deal” shows a friendly still-in-progress state until an API host exists.
No LLM. No `deal_assistant`.

## Local preview (full pipeline)

```bash
npm run preview:homepage
# http://127.0.0.1:8000/
```

## Public URL

https://scrollingtheaisle.com/

## Optional local controls

- Variation switcher: `?aislecheckProto=1`
- Debug panel: `?aislecheckDebug=1`

## Tests

```bash
npm run test:aislecheck-prototype
```

## Files

| File | Role |
|------|------|
| `aislecheck.js` | Public Variation 4 UI + API client |
| `aislecheck.css` | Layout + Variation 4 grid |
| `server.py` | Local static + `/api/aislecheck` |
| `../scripts/shopper_query/` | Deterministic normalize → parse → match |
