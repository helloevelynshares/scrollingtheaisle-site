# Supabase Edge Functions

## analyze-find-photo

Analyzes a grocery deal photo with OpenAI Vision and returns fields for the Live Finds submit form.

**Production URL:**

```text
https://<PROJECT_REF>.functions.supabase.co/analyze-find-photo
```

With your project (`wurmdtqysegytsjcudve`):

```text
https://wurmdtqysegytsjcudve.functions.supabase.co/analyze-find-photo
```

`app.js` builds this URL automatically from `SUPABASE_URL`.

---

## validate-admin / admin-suggestion-actions / admin-store-actions / admin-find-actions

Password-gated admin API for reviewing vote suggestions and grocery finds.

- **Tracker items:** `/admin/suggestions/` via `admin-suggestion-actions` (`tracker_vote_items`)
- **Grocery stores:** `/admin/stores/` via `admin-store-actions` (`store_vote_items`)
- **Grocery finds:** `/admin/finds/` via `admin-find-actions` (`finds`)

**Secrets:**

```bash
supabase secrets set ADMIN_PASSWORD=your-secret-here
```

`SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are injected automatically in deployed Edge Functions.

**Deploy:**

```bash
supabase functions deploy validate-admin
supabase functions deploy admin-suggestion-actions
supabase functions deploy admin-store-actions
supabase functions deploy admin-find-actions
```

`admin-store-actions` and `admin-find-actions` must be deployed with JWT verification disabled (same as the other admin functions). `supabase/config.toml` sets `verify_jwt = false` for each; if you deploy without linking config, pass `--no-verify-jwt` or the gateway will reject the custom HMAC bearer token with `UNAUTHORIZED_INVALID_JWT_FORMAT` and sign-in will appear to hang or immediately expire.

**Flow:**

1. `POST validate-admin` with JSON `{ "password": "..." }` → `{ "token": "..." }` (8h HMAC token)
2. `POST admin-suggestion-actions`, `admin-store-actions`, or `admin-find-actions` with `Authorization: Bearer <token>` and JSON body:
   - `{ "action": "list" }` → pending items (finds: pending only)
   - `{ "action": "approve", "itemId" | "findId", ... }`
   - `{ "action": "reject", "itemId" | "findId", "adminNotes"? }`
   - `{ "action": "merge", "itemId", "mergeIntoId", "addVoteOnMerge"? }` (suggestions/stores only)

---

## 1. Set the OpenAI secret

```bash
supabase login
supabase link --project-ref wurmdtqysegytsjcudve
supabase secrets set OPENAI_API_KEY=sk-your-key-here
```

Without `OPENAI_API_KEY`, the function returns **mock Keebler JSON** for UI testing.

---

## 2. Deploy

```bash
supabase functions deploy analyze-find-photo
```

---

## 3. Local development

Create `supabase/.env.local` (gitignored):

```env
OPENAI_API_KEY=sk-...
```

Run:

```bash
supabase start
supabase functions serve analyze-find-photo --env-file supabase/.env.local --no-verify-jwt
```

Local URL:

```text
http://127.0.0.1:54321/functions/v1/analyze-find-photo
```

Temporarily set in `app.js`:

```js
const ANALYZE_PHOTO_ENDPOINT = "http://127.0.0.1:54321/functions/v1/analyze-find-photo";
```

Serve the static site:

```bash
python3 -m http.server 8000
```

---

## 4. Test with curl

```bash
curl -s -X POST \
  "https://wurmdtqysegytsjcudve.functions.supabase.co/analyze-find-photo" \
  -F "image=@/path/to/keebler-photo.png" \
  | python3 -m json.tool
```

Local:

```bash
curl -s -X POST \
  "http://127.0.0.1:54321/functions/v1/analyze-find-photo" \
  -F "image=@/path/to/keebler-photo.png" \
  | python3 -m json.tool
```

---

## Request / response

- **Method:** `POST`
- **Body:** `multipart/form-data`, field name `image`
- **Limits:** JPG, PNG, WebP; max 8MB
- **Response:** JSON with `item_name`, `price`, `store`, `location`, `notes`, `confidence`, `raw_extraction`

CORS is enabled for browser calls from your GitHub Pages site.
