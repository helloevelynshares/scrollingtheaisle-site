-- Rollback / full removal for AisleCheck example submission.
-- Prefer emergency disable first (frontend flag + revoke execute) before dropping data.

revoke execute on function public.submit_aislecheck_example(text, uuid) from anon;
revoke execute on function public.submit_aislecheck_example(text, uuid) from authenticated;
drop function if exists public.submit_aislecheck_example(text, uuid);
drop function if exists public.submit_aislecheck_example(text);

drop policy if exists "Deny anon select aislecheck_examples" on public.aislecheck_examples;
drop policy if exists "Deny anon insert aislecheck_examples" on public.aislecheck_examples;
drop policy if exists "Deny anon update aislecheck_examples" on public.aislecheck_examples;
drop policy if exists "Deny anon delete aislecheck_examples" on public.aislecheck_examples;
drop policy if exists "Deny authenticated select aislecheck_examples" on public.aislecheck_examples;
drop policy if exists "Deny authenticated insert aislecheck_examples" on public.aislecheck_examples;
drop policy if exists "Deny authenticated update aislecheck_examples" on public.aislecheck_examples;
drop policy if exists "Deny authenticated delete aislecheck_examples" on public.aislecheck_examples;

drop index if exists public.aislecheck_examples_client_submission_uidx;
drop index if exists public.aislecheck_examples_created_at_idx;
drop table if exists public.aislecheck_examples;
