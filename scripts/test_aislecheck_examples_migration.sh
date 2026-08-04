#!/usr/bin/env bash
# Local permission + RPC tests for aislecheck_examples migration.
# Requires: psql, a running Postgres, roles anon/authenticated (or created here).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MIGRATION="$ROOT/supabase/migrations/20260804_aislecheck_examples.sql"
DSN="${AISLECHECK_TEST_DSN:-postgresql://postgres:postgres@127.0.0.1:5432/aislecheck_examples_test}"

psql "$DSN" -v ON_ERROR_STOP=1 <<'SQL'
select version();

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'anon') then
    create role anon nologin;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then
    create role authenticated nologin;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticator') then
    create role authenticator noinherit login password 'postgres';
  end if;
  grant anon to authenticator;
  grant authenticated to authenticator;
end $$;

create extension if not exists pgcrypto;
drop table if exists public.aislecheck_examples cascade;
drop function if exists public.submit_aislecheck_example(text, uuid);
drop function if exists public.submit_aislecheck_example(text);
SQL

psql "$DSN" -v ON_ERROR_STOP=1 -f "$MIGRATION"

psql "$DSN" -v ON_ERROR_STOP=1 <<'SQL'
\set ON_ERROR_STOP on

-- Helper: assert exception
create or replace function pg_temp.expect_fail(p_sql text, p_label text)
returns void language plpgsql as $$
begin
  begin
    execute p_sql;
  exception when others then
    raise notice 'PASS % (%)', p_label, SQLERRM;
    return;
  end;
  raise exception 'FAIL %: expected error', p_label;
end;
$$;

-- 1) Valid RPC submission succeeds
set role anon;
select public.submit_aislecheck_example('Doritos are $2.49 each when I buy four.', '11111111-1111-4111-8111-111111111111') as r1;
reset role;

-- 2) Whitespace-only fails
select pg_temp.expect_fail(
  $q$set role anon; select public.submit_aislecheck_example('   ', null); reset role;$q$,
  'whitespace-only'
);

-- 3) Oversized fails
select pg_temp.expect_fail(
  format(
    $q$set role anon; select public.submit_aislecheck_example(%L, null); reset role;$q$,
    repeat('x', 501)
  ),
  'oversized'
);

-- 4) Duplicate client submission id does not create another row
set role anon;
select public.submit_aislecheck_example('Doritos retry', '11111111-1111-4111-8111-111111111111') as r_dup;
reset role;

do $$
declare c int;
begin
  select count(*) into c from public.aislecheck_examples
  where client_submission_id = '11111111-1111-4111-8111-111111111111';
  if c <> 1 then
    raise exception 'FAIL duplicate id row count=%', c;
  end if;
  raise notice 'PASS duplicate client_submission_id (rows=1)';
end $$;

-- 5-8) Anonymous direct DML fails
select pg_temp.expect_fail(
  $q$set role anon; insert into public.aislecheck_examples (raw_query) values ('nope'); reset role;$q$,
  'anon direct insert'
);
select pg_temp.expect_fail(
  $q$set role anon; select * from public.aislecheck_examples; reset role;$q$,
  'anon select'
);
select pg_temp.expect_fail(
  $q$set role anon; update public.aislecheck_examples set raw_query = 'x'; reset role;$q$,
  'anon update'
);
select pg_temp.expect_fail(
  $q$set role anon; delete from public.aislecheck_examples; reset role;$q$,
  'anon delete'
);

-- 9) RPC returns only minimal confirmation data
do $$
declare j json;
begin
  set role anon;
  j := public.submit_aislecheck_example('Cheez-It 3/$5', '22222222-2222-4222-8222-222222222222');
  reset role;
  if j ? 'raw_query' or j ? 'id' or j ? 'created_at' then
    raise exception 'FAIL minimal return leaked keys: %', j;
  end if;
  if (j->>'ok') <> 'true' then
    raise exception 'FAIL ok missing: %', j;
  end if;
  if not (j ? 'already_submitted') then
    raise exception 'FAIL already_submitted missing: %', j;
  end if;
  raise notice 'PASS minimal confirmation %', j;
end $$;

-- Stored fields are minimal (admin view)
do $$
declare cols text;
begin
  select string_agg(column_name, ',' order by ordinal_position) into cols
  from information_schema.columns
  where table_schema = 'public' and table_name = 'aislecheck_examples';
  if cols <> 'id,raw_query,source,client_submission_id,created_at' then
    raise exception 'FAIL unexpected columns: %', cols;
  end if;
  raise notice 'PASS columns %', cols;
end $$;

select 'ALL_LOCAL_SQL_TESTS_PASSED' as status;
SQL
