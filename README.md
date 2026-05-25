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

## GitHub Pages

Push to your `gh-pages` branch (or main, depending on settings). No build step required.
