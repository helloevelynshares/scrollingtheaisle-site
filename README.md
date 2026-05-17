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

## Local testing

Serve the folder with any static server (or open files directly; some browsers block Supabase from `file://`):

```bash
python3 -m http.server 8080
```

Then:

1. Open `http://localhost:8080/submit.html`
2. Fill in item name, price, store; optionally add a photo and notes
3. Click **Post find**
4. Confirm redirect to `finds.html?posted=1` and the green “Your find is live.” banner
5. Confirm your card appears in the feed with photo, price, store, and actions

From the home page (`index.html`), use **View live finds** or **Post a find** to enter the same flow.

## Pages

| File | Purpose |
|------|---------|
| `index.html` | Landing + Beehiiv signup + finds promo |
| `submit.html` | Post a grocery find |
| `finds.html` | Live public feed |
| `app.js` | Supabase client and shared logic |
| `styles.css` | Shared styles |

## GitHub Pages

Push to your `gh-pages` branch (or main, depending on settings). No build step required.
