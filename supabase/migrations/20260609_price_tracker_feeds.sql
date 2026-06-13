-- Multi-feed price tracker schema.
-- canonical_products are shared across feeds; feed_id scopes regional price data.

create table if not exists canonical_products (
  id text primary key,
  display_name text not null,
  product_family text not null,
  size_label text,
  costco_comparable boolean not null default true,
  confidence text not null default 'high'
    check (confidence in ('high', 'medium', 'low')),
  sort_order int not null default 0,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists price_feeds (
  id text primary key,
  label text not null,
  region_label text not null,
  store_group text not null,
  stores text[] not null default '{}',
  sort_order int not null default 0,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

-- feed_product_matches: same canonical item → different retailer SKUs per feed.
create table if not exists feed_product_matches (
  id uuid primary key default gen_random_uuid(),
  canonical_product_id text not null references canonical_products(id) on delete cascade,
  feed_id text not null references price_feeds(id) on delete cascade,
  retailer_product_id text,
  upc text,
  retailer_product_name text,
  size text,
  baseline_price numeric(10, 2) not null,
  baseline_source text,
  created_at timestamptz not null default now(),
  unique (canonical_product_id, feed_id)
);

create index if not exists feed_product_matches_feed_id_idx
  on feed_product_matches (feed_id);

-- weekly_price_observations keyed by canonical_product_id + feed_id + week_start.
create table if not exists weekly_price_observations (
  id uuid primary key default gen_random_uuid(),
  canonical_product_id text not null references canonical_products(id) on delete cascade,
  feed_id text not null references price_feeds(id) on delete cascade,
  week_start date not null,
  week_end date,
  ad_price numeric(10, 2),
  effective_price numeric(10, 2) not null,
  match_confidence text check (match_confidence in ('high', 'medium', 'low')),
  price_type text not null check (price_type in ('baseline', 'weekly_ad')),
  is_baseline_fallback boolean not null default false,
  source_label text,
  offer_text text,
  created_at timestamptz not null default now(),
  unique (canonical_product_id, feed_id, week_start)
);

create index if not exists weekly_price_observations_feed_week_idx
  on weekly_price_observations (feed_id, week_start);

alter table canonical_products enable row level security;
alter table price_feeds enable row level security;
alter table feed_product_matches enable row level security;
alter table weekly_price_observations enable row level security;

grant select on public.canonical_products to anon;
grant select on public.price_feeds to anon;
grant select on public.feed_product_matches to anon;
grant select on public.weekly_price_observations to anon;

create policy "Anyone can read canonical products"
on canonical_products for select to anon using (is_active = true);

create policy "Anyone can read price feeds"
on price_feeds for select to anon using (is_active = true);

create policy "Anyone can read feed product matches"
on feed_product_matches for select to anon using (true);

create policy "Anyone can read weekly price observations"
on weekly_price_observations for select to anon using (true);
