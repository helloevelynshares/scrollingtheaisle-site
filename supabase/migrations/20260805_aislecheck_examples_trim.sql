-- Harden submit_aislecheck_example whitespace handling.
-- Postgres btrim() only removes ASCII spaces by default, so tab/newline-only
-- inputs were accepted. Align with JS String.trim() behavior.

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
  -- Trim common whitespace (space, tab, LF, CR), matching browser String.trim().
  v_raw := trim(both E' \t\n\r' from coalesce(p_query, ''));

  if v_raw = '' then
    raise exception 'Query is required'
      using errcode = '22023';
  end if;

  if char_length(v_raw) > 500 then
    raise exception 'Query must be 500 characters or fewer'
      using errcode = '22023';
  end if;

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
      return json_build_object('ok', true, 'already_submitted', true);
  end;

  return json_build_object('ok', true, 'already_submitted', false);
end;
$$;

revoke all on function public.submit_aislecheck_example(text, uuid) from public;
grant execute on function public.submit_aislecheck_example(text, uuid) to anon;
