-- Opt-in AisleCheck example queries from the public homepage fallback.
-- Write-only for the public via a narrowly scoped RPC. No public reads.
-- Collects only trimmed query text + fixed source + optional client submission id.
-- No email, IP, account id, user-agent, or arbitrary metadata.

create table if not exists public.aislecheck_examples (
  id uuid primary key default gen_random_uuid(),
  raw_query text not null,
  source text not null default 'homepage'
    check (source = 'homepage'),
  client_submission_id uuid,
  created_at timestamptz not null default now(),
  constraint aislecheck_examples_query_len
    check (char_length(raw_query) between 1 and 500)
);

-- Idempotent retries / double-clicks from the same client attempt.
create unique index if not exists aislecheck_examples_client_submission_uidx
  on public.aislecheck_examples (client_submission_id)
  where client_submission_id is not null;

create index if not exists aislecheck_examples_created_at_idx
  on public.aislecheck_examples (created_at desc);

alter table public.aislecheck_examples enable row level security;

-- No table privileges for browser roles. Access only through the RPC below.
revoke all on table public.aislecheck_examples from public;
revoke all on table public.aislecheck_examples from anon;
revoke all on table public.aislecheck_examples from authenticated;

-- Explicit deny policies (defense in depth; table grants already revoked).
drop policy if exists "Deny anon select aislecheck_examples" on public.aislecheck_examples;
drop policy if exists "Deny anon insert aislecheck_examples" on public.aislecheck_examples;
drop policy if exists "Deny anon update aislecheck_examples" on public.aislecheck_examples;
drop policy if exists "Deny anon delete aislecheck_examples" on public.aislecheck_examples;
drop policy if exists "Deny authenticated select aislecheck_examples" on public.aislecheck_examples;
drop policy if exists "Deny authenticated insert aislecheck_examples" on public.aislecheck_examples;
drop policy if exists "Deny authenticated update aislecheck_examples" on public.aislecheck_examples;
drop policy if exists "Deny authenticated delete aislecheck_examples" on public.aislecheck_examples;

create policy "Deny anon select aislecheck_examples"
  on public.aislecheck_examples for select to anon using (false);
create policy "Deny anon insert aislecheck_examples"
  on public.aislecheck_examples for insert to anon with check (false);
create policy "Deny anon update aislecheck_examples"
  on public.aislecheck_examples for update to anon using (false);
create policy "Deny anon delete aislecheck_examples"
  on public.aislecheck_examples for delete to anon using (false);

create policy "Deny authenticated select aislecheck_examples"
  on public.aislecheck_examples for select to authenticated using (false);
create policy "Deny authenticated insert aislecheck_examples"
  on public.aislecheck_examples for insert to authenticated with check (false);
create policy "Deny authenticated update aislecheck_examples"
  on public.aislecheck_examples for update to authenticated using (false);
create policy "Deny authenticated delete aislecheck_examples"
  on public.aislecheck_examples for delete to authenticated using (false);

-- Drop draft single-arg overload if present so callers use the hardened signature.
drop function if exists public.submit_aislecheck_example(text);

create or replace function public.submit_aislecheck_example(
  p_query text,
  p_client_submission_id uuid default null
)
returns json
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  v_raw text;
  v_existing_id uuid;
begin
  v_raw := btrim(coalesce(p_query, ''));

  if v_raw = '' then
    raise exception 'Query is required'
      using errcode = '22023';
  end if;

  if char_length(v_raw) > 500 then
    raise exception 'Query must be 500 characters or fewer'
      using errcode = '22023';
  end if;

  -- Duplicate / retry of the same client attempt: confirm without inserting again.
  if p_client_submission_id is not null then
    select e.id
      into v_existing_id
    from public.aislecheck_examples as e
    where e.client_submission_id = p_client_submission_id
    limit 1;

    if v_existing_id is not null then
      return json_build_object('ok', true, 'already_submitted', true);
    end if;
  end if;

  begin
    insert into public.aislecheck_examples (raw_query, source, client_submission_id)
    values (v_raw, 'homepage', p_client_submission_id);
  exception
    when unique_violation then
      -- Race between concurrent retries with the same client_submission_id.
      return json_build_object('ok', true, 'already_submitted', true);
  end;

  -- Minimal confirmation only — never return query text or other rows.
  return json_build_object('ok', true, 'already_submitted', false);
end;
$$;

revoke all on function public.submit_aislecheck_example(text, uuid) from public;

-- Homepage uses the anon key; keep execute narrowly scoped.
grant execute on function public.submit_aislecheck_example(text, uuid) to anon;
