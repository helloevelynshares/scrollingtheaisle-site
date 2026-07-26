-- Remove vote options now covered by canonical tracker families,
-- then seed six new uncovered staples for public voting.

update public.tracker_vote_items
set
  status = 'rejected',
  rejected_at = now(),
  admin_notes = coalesce(admin_notes || ' ', '') ||
    'Removed from public vote list: now covered by an existing tracker family.'
where status = 'approved'
  and normalized_name in (
    public.normalize_tracker_vote_name('Berries'),
    public.normalize_tracker_vote_name('Grapes'),
    public.normalize_tracker_vote_name('Chicken breast'),
    public.normalize_tracker_vote_name('Oreos'),
    public.normalize_tracker_vote_name('Ritz crackers'),
    public.normalize_tracker_vote_name('Kettle chips'),
    public.normalize_tracker_vote_name('Ribeye Steak'),
    public.normalize_tracker_vote_name('ribeye steak'),
    public.normalize_tracker_vote_name('Bell Pepper'),
    public.normalize_tracker_vote_name('Bell pepper')
  );

insert into public.tracker_vote_items (
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
    ('Dot''s Pretzels', 'Dot''s Pretzels'),
    ('Hawaiian Brand chips', 'Hawaiian Brand chips'),
    ('Ground beef', 'Ground beef'),
    ('Bacon', 'Bacon'),
    ('Eggo waffles', 'Eggo waffles'),
    ('Oat milk', 'Oat milk')
) as seed(raw_text, public_name)
where not exists (
  select 1
  from public.tracker_vote_items existing
  where existing.normalized_name = public.normalize_tracker_vote_name(seed.raw_text)
    and existing.status in ('approved', 'pending')
);
