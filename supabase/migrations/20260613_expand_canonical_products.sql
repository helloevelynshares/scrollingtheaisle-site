-- Expand canonical product list with recurring cross-store items + Costco feeds.
-- Safe to run after 20260610_price_tracker_seed.sql (upserts only).

insert into canonical_products (id, display_name, product_family, size_label, sort_order) values
  ('fage_greek_yogurt', 'Fage Greek Yogurt', 'fage_greek_yogurt', '32 oz', 11),
  ('frito_lay_multipack_chips', 'Frito-Lay Multipack Chips', 'frito_lay_multipack_chips', 'Multipack', 12),
  ('haagen_dazs_ice_cream', 'Häagen-Dazs Ice Cream', 'haagen_dazs_ice_cream', '14 oz', 13),
  ('grapes', 'Grapes', 'grapes', 'per lb', 14),
  ('eggs_18_count', 'Eggs, 18-count', 'eggs_18_count', '18 ct', 15),
  ('oreos_sandwich_cookies', 'Oreos / Sandwich Cookies', 'oreos_sandwich_cookies', 'Family size', 16),
  ('protein_bars', 'Protein Bars', 'protein_bars', 'Varies', 17),
  ('kettle_brand_chips', 'Kettle Brand Chips', 'kettle_brand_chips', '8 oz', 18)
on conflict (id) do update set
  display_name = excluded.display_name,
  product_family = excluded.product_family,
  size_label = excluded.size_label,
  sort_order = excluded.sort_order;

-- Refresh aliases/display for existing items (no duplicates).
update canonical_products
set display_name = 'Strawberries', product_family = 'strawberries', size_label = '1 lb', sort_order = 1
where id = 'strawberries';

update canonical_products
set display_name = 'Nature Valley Bars', product_family = 'nature_valley_bars', size_label = '12 ct', sort_order = 10
where id = 'nature_valley_bars';

insert into price_feeds (id, label, region_label, store_group, stores, sort_order) values
  ('costco_sf', 'Costco', 'San Francisco', 'costco', array['Costco'], 3),
  ('costco_oc', 'Costco', 'Orange County', 'costco', array['Costco'], 4)
on conflict (id) do update set
  label = excluded.label,
  region_label = excluded.region_label,
  store_group = excluded.store_group,
  stores = excluded.stores,
  sort_order = excluded.sort_order;
