-- Price tracker: vote on items to track + lightweight custom suggestions.

create table if not exists product_track_suggestions (
  id uuid primary key default gen_random_uuid(),
  item_name text not null,
  normalized_item_name text not null unique,
  source text not null default 'tracker_module',
  created_at timestamptz not null default now()
);

create table if not exists product_track_votes (
  id uuid primary key default gen_random_uuid(),
  suggestion_id uuid not null references product_track_suggestions(id) on delete cascade,
  item_name text not null,
  normalized_item_name text not null,
  vote_source text not null default 'tracker_module',
  anonymous_user_key text not null,
  created_at timestamptz not null default now(),
  unique (suggestion_id, anonymous_user_key)
);

create index if not exists product_track_votes_suggestion_id_idx
  on product_track_votes (suggestion_id);

alter table product_track_suggestions enable row level security;
alter table product_track_votes enable row level security;

grant select, insert on public.product_track_suggestions to anon;
grant insert on public.product_track_votes to anon;

create policy "Anyone can read track suggestions"
on product_track_suggestions for select
to anon
using (true);

create policy "Anyone can add track suggestions"
on product_track_suggestions for insert
to anon
with check (
  char_length(trim(item_name)) > 0
  and char_length(trim(item_name)) <= 120
  and char_length(trim(normalized_item_name)) > 0
);

create policy "Anyone can cast track votes"
on product_track_votes for insert
to anon
with check (
  char_length(trim(anonymous_user_key)) > 0
  and char_length(trim(item_name)) > 0
  and char_length(trim(normalized_item_name)) > 0
);

create or replace view public.product_track_suggestion_totals
with (security_barrier = false) as
select
  s.id,
  s.item_name,
  s.normalized_item_name,
  count(v.id)::int as vote_count
from public.product_track_suggestions s
left join public.product_track_votes v on v.suggestion_id = s.id
group by s.id, s.item_name, s.normalized_item_name;

grant select on public.product_track_suggestion_totals to anon;

insert into product_track_suggestions (item_name, normalized_item_name, source)
select v.item_name, v.normalized_item_name, 'tracker_module'
from (
  values
    ('Berries', 'berries'),
    ('Grapes', 'grapes'),
    ('Chicken breast', 'chicken breast'),
    ('Oreos', 'oreos'),
    ('Ritz crackers', 'ritz crackers'),
    ('Kettle chips', 'kettle chips')
) as v(item_name, normalized_item_name)
where not exists (
  select 1
  from product_track_suggestions s
  where s.normalized_item_name = v.normalized_item_name
);
