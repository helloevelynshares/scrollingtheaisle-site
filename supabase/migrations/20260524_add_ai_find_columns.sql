-- Run in Supabase SQL Editor if your finds table already exists.

alter table finds add column if not exists price_display text;
alter table finds add column if not exists ai_extracted boolean default false;
alter table finds add column if not exists ai_confidence jsonb;
alter table finds add column if not exists raw_ai_extraction jsonb;

-- price_display: human-readable deal text (e.g. "50% off — reg. $7.99, approx. $3.99")
-- price: keep numeric column for sorting; app sends parsed value from price_display
