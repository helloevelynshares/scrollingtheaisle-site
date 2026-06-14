-- Price comparisons: grocery vs Costco per-unit for tracked canonical products.

alter table canonical_products
  add column if not exists package_quantity numeric,
  add column if not exists package_unit text,
  add column if not exists unit_type text,
  add column if not exists comparable_unit text,
  add column if not exists comparison_group text;

create table if not exists price_comparisons (
  id uuid primary key default gen_random_uuid(),
  canonical_product_id text not null references canonical_products(id) on delete cascade,
  grocery_feed_id text not null references price_feeds(id) on delete cascade,
  grocery_store_label text not null,
  grocery_price numeric(10, 2),
  grocery_package_description text,
  grocery_unit_type text,
  grocery_unit_count numeric,
  grocery_unit_price numeric(10, 4),
  costco_region_id text references price_feeds(id) on delete set null,
  costco_store_label text,
  costco_price numeric(10, 2),
  costco_package_description text,
  costco_unit_type text,
  costco_unit_count numeric,
  costco_unit_price numeric(10, 4),
  winner text not null check (winner in ('grocery', 'costco', 'tie', 'grocery_only', 'unknown')),
  savings_amount numeric(10, 4),
  savings_percent numeric(5, 2),
  comparison_status text not null check (
    comparison_status in (
      'comparable',
      'not_sold_at_costco',
      'missing_costco_price',
      'missing_grocery_price',
      'unit_mismatch',
      'needs_review'
    )
  ),
  comparison_note text,
  source text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (canonical_product_id, grocery_feed_id, costco_region_id)
);

create index if not exists price_comparisons_grocery_feed_idx
  on price_comparisons (grocery_feed_id);

create index if not exists price_comparisons_canonical_idx
  on price_comparisons (canonical_product_id);

alter table price_comparisons enable row level security;

grant select on public.price_comparisons to anon;

create policy "Anyone can read price comparisons"
on price_comparisons for select to anon using (true);

-- Package metadata for per-unit normalization (upsert only).
update canonical_products set
  package_quantity = 1, package_unit = 'lb', unit_type = 'lb', comparable_unit = 'lb', comparison_group = 'produce'
where id = 'strawberries';

update canonical_products set
  package_quantity = 1, package_unit = 'each', unit_type = 'each', comparable_unit = 'each', comparison_group = 'produce'
where id = 'avocados';

update canonical_products set
  package_quantity = 9.25, package_unit = 'oz', unit_type = 'oz', comparable_unit = 'oz', comparison_group = 'snacks'
where id = 'doritos_nacho_cheese';

update canonical_products set
  package_quantity = 8.5, package_unit = 'oz', unit_type = 'oz', comparable_unit = 'oz', comparison_group = 'snacks'
where id = 'cheetos_crunchy';

update canonical_products set
  package_quantity = 12, package_unit = 'can', unit_type = 'can', comparable_unit = 'can', comparison_group = 'beverages'
where id = 'coke_zero';

update canonical_products set
  package_quantity = 32, package_unit = 'oz', unit_type = 'oz', comparable_unit = 'oz', comparison_group = 'dairy'
where id = 'chobani_greek_yogurt';

update canonical_products set
  package_quantity = 8.9, package_unit = 'oz', unit_type = 'oz', comparable_unit = 'oz', comparison_group = 'cereal'
where id = 'cheerios';

update canonical_products set
  package_quantity = 56, package_unit = 'oz', unit_type = 'oz', comparable_unit = 'oz', comparison_group = 'frozen'
where id = 'tillamook_ice_cream';

update canonical_products set
  package_quantity = 11, package_unit = 'oz', unit_type = 'oz', comparable_unit = 'oz', comparison_group = 'snacks'
where id = 'mission_tortilla_chips';

update canonical_products set
  package_quantity = 12, package_unit = 'bar', unit_type = 'bar', comparable_unit = 'bar', comparison_group = 'snacks'
where id = 'nature_valley_bars';

update canonical_products set
  package_quantity = 32, package_unit = 'oz', unit_type = 'oz', comparable_unit = 'oz', comparison_group = 'dairy'
where id = 'fage_greek_yogurt';

update canonical_products set
  package_quantity = 42, package_unit = 'bag', unit_type = 'bag', comparable_unit = 'bag', comparison_group = 'snacks'
where id = 'frito_lay_multipack_chips';

update canonical_products set
  package_quantity = 14, package_unit = 'oz', unit_type = 'oz', comparable_unit = 'oz', comparison_group = 'frozen'
where id = 'haagen_dazs_ice_cream';

update canonical_products set
  package_quantity = 1, package_unit = 'lb', unit_type = 'lb', comparable_unit = 'lb', comparison_group = 'produce'
where id = 'grapes';

update canonical_products set
  package_quantity = 18, package_unit = 'egg', unit_type = 'egg', comparable_unit = 'egg', comparison_group = 'dairy'
where id = 'eggs_18_count';

update canonical_products set
  package_quantity = 18, package_unit = 'oz', unit_type = 'oz', comparable_unit = 'oz', comparison_group = 'snacks'
where id = 'oreos_sandwich_cookies';

update canonical_products set
  package_quantity = 12, package_unit = 'bar', unit_type = 'bar', comparable_unit = 'bar', comparison_group = 'snacks'
where id = 'protein_bars';

update canonical_products set
  package_quantity = 8, package_unit = 'oz', unit_type = 'oz', comparable_unit = 'oz', comparison_group = 'snacks'
where id = 'kettle_brand_chips';
