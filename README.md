# Scrolling the Aisle

Static site for Scrolling the Aisle — weekly deal tracking plus a community “live grocery finds” feed.

## Supabase setup

### 1. Add your project credentials

Open `app.js` and replace the placeholders at the top:

```js
const SUPABASE_URL = "YOUR_SUPABASE_PROJECT_URL";
const SUPABASE_ANON_KEY = "YOUR_SUPABASE_ANON_KEY";
```

Use your project URL (e.g. `https://xxxxx.supabase.co`) and the **anon** public key from Supabase → Project Settings → API. Do **not** use the service role key in the frontend.

### 2. Run the database SQL

In Supabase → SQL Editor, run:

```sql
create extension if not exists pgcrypto;

create table if not exists finds (
  id uuid primary key default gen_random_uuid(),
  item_name text not null,
  price numeric(10,2) not null,
  store_name text not null,
  location_label text,
  latitude double precision,
  longitude double precision,
  photo_url text,
  notes text,
  submitted_by text,
  status text default 'approved',
  created_at timestamptz default now(),
  expires_at timestamptz default (now() + interval '3 days')
);

create table if not exists find_votes (
  id uuid primary key default gen_random_uuid(),
  find_id uuid references finds(id) on delete cascade,
  voter_id text not null,
  vote_type text not null default 'still_there',
  created_at timestamptz default now(),
  unique(find_id, voter_id)
);

create table if not exists find_reports (
  id uuid primary key default gen_random_uuid(),
  find_id uuid references finds(id) on delete cascade,
  reporter_id text,
  reason text,
  created_at timestamptz default now()
);

alter table finds enable row level security;
alter table find_votes enable row level security;
alter table find_reports enable row level security;

grant select, insert on public.finds to anon;
grant select, insert on public.find_votes to anon;
grant insert on public.find_reports to anon;

-- Do not grant update/delete on finds to anon (see supabase/migrations/20260525_revoke_finds_update.sql)

create policy "Anyone can read approved active finds"
on finds for select
using (
  status = 'approved'
  and expires_at > now()
);

create policy "Anyone can insert finds"
on finds for insert
with check (
  status = 'approved'
);

create policy "Anyone can vote"
on find_votes for insert
with check (true);

create policy "Anyone can read votes"
on find_votes for select
using (true);

create policy "Anyone can report"
on find_reports for insert
with check (true);
```

**Price tracker voting** — run `supabase/migrations/20260608_product_track_voting.sql` in the SQL Editor (or `supabase db push` from this repo). Votes and suggestions land in `product_track_votes` / `product_track_suggestions` (review in Supabase → Table Editor). The `product_track_suggestion_totals` view powers vote counts on the page.

**Price tracker feeds** — run these in order in the SQL Editor (or `supabase db push`):

1. `supabase/migrations/20260609_price_tracker_feeds.sql` — `canonical_products`, `price_feeds`, `feed_product_matches`, `weekly_price_observations`
2. `supabase/migrations/20260609_price_tracker_seed.sql` — Safeway Bay Area baseline + weekly observations (regenerate with `npm run generate:price-tracker-seed` after weekly ad updates)

**Vons / Albertsons baselines (SoCal)** — same Albertsons `pgmsearch` API via [Vons search](https://www.vons.com/shop/search-results.html?q=grapes&tab=products):

```bash
# 1. In Chrome on vons.com: set SoCal store, search any item, copy Cookie from Network → pgmsearch
# 2. Add to scripts/.env: VONS_COOKIE=...  (or use a vons.com-specific cookie; SAFEWAY_COOKIE alone may not work)
python scripts/seed_vons_baseline_playwright.py --headful --delay 3
python scripts/generate_vons_feed_matches.py   # → Supabase seed + src/data/vonsBaseline.generated.ts
# 3. Run supabase/migrations/20260612_vons_feed_matches_seed.sql in SQL Editor
```

Queries: `data/canonical/price_tracker_baseline_queries.csv`. Output: `data/processed/vons_baseline_candidates_v1.csv`.

### 3. Create the storage bucket

**Option A — Dashboard**

1. Supabase → **Storage** → **New bucket**
2. Name: `find-photos` (must match exactly)
3. **Public bucket**: On
4. Create the bucket

**Option B — SQL Editor** (same result)

```sql
insert into storage.buckets (id, name, public)
values ('find-photos', 'find-photos', true)
on conflict (id) do nothing;
```

### 4. Storage policies

In Supabase → SQL Editor (or Storage → `find-photos` → Policies), run:

```sql
create policy "Anyone can upload find photos"
on storage.objects for insert
with check (
  bucket_id = 'find-photos'
);

create policy "Anyone can read find photos"
on storage.objects for select
using (
  bucket_id = 'find-photos'
);
```

### 5. AI photo columns (optional migration)

If the table already exists, run `supabase/migrations/20260524_add_ai_find_columns.sql` in the SQL Editor to add:

- `price_display` — human-readable price text
- `ai_extracted`, `ai_confidence`, `raw_ai_extraction`

## AI photo analysis

Architecture:

```text
GitHub Pages → Supabase Edge Function (analyze-find-photo) → OpenAI Vision
            → auto-fill form → Supabase Storage + finds table
```

The OpenAI key lives in **Supabase secrets**, not in the frontend.

### Setup

1. Install [Supabase CLI](https://supabase.com/docs/guides/cli) and link your project:

```bash
supabase login
supabase link --project-ref wurmdtqysegytsjcudve
```

2. Set the secret:

```bash
supabase secrets set OPENAI_API_KEY=sk-your-key-here
```

3. Deploy the function:

```bash
supabase functions deploy analyze-find-photo
```

4. **`app.js`** — endpoint is derived from `SUPABASE_URL` automatically:

```text
https://wurmdtqysegytsjcudve.functions.supabase.co/analyze-find-photo
```

Override only for local CLI testing (see `supabase/functions/README.md`).

Without `OPENAI_API_KEY`, the function returns **mock Keebler JSON** so you can test the UI.

Full details: **`supabase/functions/README.md`**

## Local testing

**Static site:**

```bash
python3 -m http.server 8000
```

**Edge Function (optional):**

```bash
supabase functions serve analyze-find-photo --env-file supabase/.env.local --no-verify-jwt
```

Use `http://127.0.0.1:54321/functions/v1/analyze-find-photo` in `app.js` while testing locally.

**Test flow:**

1. Open `http://localhost:8000/submit.html` or `http://localhost:8000/staging-live-finds/submit.html`
2. Upload a shelf-tag photo (e.g. Keebler Fudge Stripes with 50% off sticker)
3. Wait for “Analyzing photo…” — fields should auto-fill
4. Review and edit, then **Post find**
5. Confirm redirect and feed card with photo and price text

**curl:**

```bash
curl -s -X POST \
  "https://wurmdtqysegytsjcudve.functions.supabase.co/analyze-find-photo" \
  -F "image=@/path/to/photo.jpg" | python3 -m json.tool
```

## Pages

| File | Purpose |
|------|---------|
| `index.html` | Landing + Beehiiv signup |
| `submit.html` | Post a grocery find (with AI photo flow) |
| `finds.html` | Live public feed |
| `staging-live-finds/` | Staging feed + submit |
| `app.js` | Supabase client and shared logic |
| `styles.css` | Shared styles |
| `supabase/functions/` | Edge Functions (AI photo analysis) |

## Project notes

Implementation findings, API gotchas, and repeatable debugging notes live in [`docs/PROJECT_NOTES.md`](docs/PROJECT_NOTES.md).

## Price tracker (live)

Multi-feed price tracker (React + Recharts + Supabase, with Safeway static fallback):

```bash
npm install
npm run dev:price-tracker    # local dev → /staging-price-tracker/
npm run build:price-tracker  # build → staging-price-tracker/
```

Public URL: `/staging-price-tracker/`. Canonical products live in `src/data/canonicalProducts.ts`; feed tabs in `src/data/priceFeeds.ts`. Safeway weekly ad prices are generated from `data/weekly_ads/` + `scrolling-the-aisle` offer extraction. Switch tabs to compare Bay Area Safeway vs SoCal Vons/Albertsons.

## GitHub Pages

Push to your `gh-pages` branch (or main, depending on settings). No build step required.

## Web analytics (Cloudflare)

Visitor and page-view tracking uses [Cloudflare Web Analytics](https://developers.cloudflare.com/web-analytics/).

1. In the [Cloudflare dashboard](https://dash.cloudflare.com/) go to **Web Analytics** → **Add a site** → hostname `scrollingtheaisle.com`.
2. Choose **Enable with JS Snippet installation** (required for GitHub Pages — the site is not proxied through Cloudflare).
3. Copy the `token` from the snippet Cloudflare gives you.
4. Paste it into `analytics.js` (replace `YOUR_CF_WEB_ANALYTICS_TOKEN`).
5. Deploy. Open the live site, then check **Web Analytics** in Cloudflare for traffic within a few minutes.

The shared `analytics.js` is included on all public HTML pages (`/`, `/finds.html`, `/submit.html`, `/staging-price-tracker/`, etc.). Page paths appear separately in the dashboard.
