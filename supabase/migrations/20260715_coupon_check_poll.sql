-- Homepage coupon personalization check: tally Yes/No for a specific Safeway coupon.

create table if not exists public.coupon_check_polls (
  id text primary key,
  question text not null,
  expires_at date,
  created_at timestamptz not null default now()
);

create table if not exists public.coupon_check_options (
  id text primary key,
  poll_id text not null references public.coupon_check_polls (id) on delete cascade,
  label text not null,
  sort_order int not null default 0,
  vote_count int not null default 0
);

create index if not exists coupon_check_options_poll_id_idx
  on public.coupon_check_options (poll_id, sort_order);

alter table public.coupon_check_polls enable row level security;
alter table public.coupon_check_options enable row level security;

grant select on public.coupon_check_polls to anon;
grant select on public.coupon_check_options to anon;

create policy "Anyone can read coupon check polls"
on public.coupon_check_polls
for select
to anon
using (true);

create policy "Anyone can read coupon check options"
on public.coupon_check_options
for select
to anon
using (true);

revoke insert, update, delete on public.coupon_check_polls from anon;
revoke insert, update, delete on public.coupon_check_options from anon;

create or replace function public.vote_coupon_check(p_option_id text)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  if p_option_id is null or trim(p_option_id) = '' then
    raise exception 'Option id is required';
  end if;

  update public.coupon_check_options
  set vote_count = vote_count + 1
  where id = trim(p_option_id);

  if not found then
    raise exception 'Coupon check option not found';
  end if;
end;
$$;

grant execute on function public.vote_coupon_check(text) to anon;

insert into public.coupon_check_polls (id, question, expires_at)
values (
  'safeway_cheezit_pringles_3off_202607',
  'Safeway shoppers — do you see this coupon?',
  '2026-07-28'
)
on conflict (id) do nothing;

insert into public.coupon_check_options (id, poll_id, label, sort_order, vote_count)
values
  ('safeway_cheezit_pringles_3off_202607_yes', 'safeway_cheezit_pringles_3off_202607', 'Yep', 1, 0),
  ('safeway_cheezit_pringles_3off_202607_no', 'safeway_cheezit_pringles_3off_202607', 'Nope', 2, 0)
on conflict (id) do nothing;
