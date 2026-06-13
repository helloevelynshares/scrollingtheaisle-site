-- Prevent anonymous clients from updating or deleting finds rows.
-- (The feed only needs SELECT + INSERT.)

revoke update, delete on public.finds from anon;
revoke update, delete on public.finds from authenticated;
