-- Moderate grocery finds before they appear on the public feed.

alter table finds add column if not exists approved_at timestamptz;
alter table finds add column if not exists rejected_at timestamptz;
alter table finds add column if not exists admin_notes text;

alter table finds alter column status set default 'pending';

drop policy if exists "Anyone can insert finds" on finds;

create policy "Anyone can insert pending finds"
on finds for insert
with check (status = 'pending');
