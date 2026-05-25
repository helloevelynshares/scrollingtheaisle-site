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
