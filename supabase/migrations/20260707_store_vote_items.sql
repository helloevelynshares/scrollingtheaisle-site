-- Moderated store vote items: homepage store suggestions + approved voting list.

create table if not exists public.store_vote_items (
  id uuid primary key default gen_random_uuid(),
  raw_text text not null,
  public_name text,
  normalized_name text not null,
  city text,
  vote_count int not null default 0,
  status text not null default 'pending'
    check (status in ('pending', 'approved', 'rejected', 'merged')),
  admin_notes text,
  merged_into_id uuid references public.store_vote_items (id),
  created_at timestamptz not null default now(),
  approved_at timestamptz,
  rejected_at timestamptz
);

create index if not exists store_vote_items_status_idx
  on public.store_vote_items (status);

create index if not exists store_vote_items_normalized_name_idx
  on public.store_vote_items (normalized_name);

create unique index if not exists store_vote_items_normalized_approved_uidx
  on public.store_vote_items (normalized_name)
  where status = 'approved';

create unique index if not exists store_vote_items_normalized_pending_uidx
  on public.store_vote_items (normalized_name)
  where status = 'pending';

alter table public.store_vote_items enable row level security;

grant select on public.store_vote_items to anon;

create policy "Anyone can read approved store vote items"
on public.store_vote_items
for select
to anon
using (status = 'approved');

revoke insert, update, delete on public.store_vote_items from anon;

create or replace function public.vote_on_store(p_item_id uuid)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  if p_item_id is null then
    raise exception 'Item id is required';
  end if;

  update public.store_vote_items
  set vote_count = vote_count + 1
  where id = p_item_id
    and status = 'approved';

  if not found then
    raise exception 'Store not found or not approved';
  end if;
end;
$$;

create or replace function public.submit_store_suggestion(
  p_store_name text,
  p_city text default null
)
returns json
language plpgsql
security definer
set search_path = public
as $$
declare
  v_raw text;
  v_city text;
  v_normalized text;
  v_approved_id uuid;
  v_pending_id uuid;
begin
  v_raw := trim(coalesce(p_store_name, ''));
  if v_raw = '' then
    raise exception 'Store name is required';
  end if;
  if char_length(v_raw) > 80 then
    raise exception 'Store name must be 80 characters or fewer';
  end if;

  v_city := nullif(trim(coalesce(p_city, '')), '');
  if v_city is not null and char_length(v_city) > 80 then
    raise exception 'City must be 80 characters or fewer';
  end if;

  v_normalized := public.normalize_tracker_vote_name(v_raw);
  if v_normalized = '' then
    raise exception 'Store name is required';
  end if;

  select id
  into v_approved_id
  from public.store_vote_items
  where normalized_name = v_normalized
    and status = 'approved'
  limit 1;

  if v_approved_id is not null then
    update public.store_vote_items
    set vote_count = vote_count + 1
    where id = v_approved_id;

    return json_build_object(
      'action', 'voted',
      'item_id', v_approved_id,
      'normalized_name', v_normalized
    );
  end if;

  select id
  into v_pending_id
  from public.store_vote_items
  where normalized_name = v_normalized
    and status = 'pending'
  limit 1;

  if v_pending_id is not null then
    return json_build_object(
      'action', 'already_pending',
      'item_id', v_pending_id,
      'normalized_name', v_normalized
    );
  end if;

  insert into public.store_vote_items (raw_text, normalized_name, city, status)
  values (v_raw, v_normalized, v_city, 'pending')
  returning id into v_pending_id;

  return json_build_object(
    'action', 'submitted',
    'item_id', v_pending_id,
    'normalized_name', v_normalized
  );
end;
$$;

grant execute on function public.vote_on_store(uuid) to anon;
grant execute on function public.submit_store_suggestion(text, text) to anon;

insert into public.store_vote_items (
  raw_text,
  public_name,
  normalized_name,
  status,
  approved_at,
  vote_count
)
select
  seed.raw_text,
  seed.public_name,
  public.normalize_tracker_vote_name(seed.raw_text),
  'approved',
  now(),
  0
from (
  values
    ('Trader Joe''s', 'Trader Joe''s'),
    ('Whole Foods', 'Whole Foods'),
    ('Sprouts', 'Sprouts'),
    ('Kroger', 'Kroger')
) as seed(raw_text, public_name)
where not exists (
  select 1
  from public.store_vote_items existing
  where existing.normalized_name = public.normalize_tracker_vote_name(seed.raw_text)
    and existing.status = 'approved'
);
