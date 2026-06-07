-- Suggestions for products to add to the Safeway price tracker.

create table if not exists tracker_suggestions (
  id uuid primary key default gen_random_uuid(),
  item_name text not null,
  notes text,
  photo_url text,
  submitted_by text,
  created_at timestamptz default now()
);

alter table tracker_suggestions enable row level security;

grant insert on public.tracker_suggestions to anon;

create policy "Anyone can submit tracker suggestions"
on tracker_suggestions for insert
to anon
with check (
  char_length(trim(item_name)) > 0
  and char_length(trim(item_name)) <= 200
);

-- Review submissions in Supabase Table Editor (no public read for anon).
revoke select, update, delete on public.tracker_suggestions from anon;
revoke select, update, delete on public.tracker_suggestions from authenticated;
