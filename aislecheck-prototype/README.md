# AisleCheck (public Variation 4 — fallback release)

Homepage AisleCheck ships as **Variation 4**.

This release is **fallback-only**: live API and example submission stay off.

## Public behavior

When a shopper clicks **Check deal**:

1. Heading: **AisleCheck is almost ready**
2. Body: **We’re testing how shoppers describe deals before turning on live price checks.**
3. Their submitted query is preserved and shown
4. No fake product interpretation
5. No fake deal verdict
6. No silent query storage
7. **Submit this example** stays hidden

## Production config (`index.html`)

```js
window.__AISLECHECK_CONFIG__ = {
  apiBaseUrl: "",
  liveApiEnabled: false,
  exampleSubmitEnabled: false
};
```

## Local preview

```bash
npm run preview:homepage
# http://127.0.0.1:8000/
```

Optional: `?aislecheckProto=1` (variation switcher), `?aislecheckDebug=1` (debug panel).

## Tests

```bash
npm run test:aislecheck-prototype
```
