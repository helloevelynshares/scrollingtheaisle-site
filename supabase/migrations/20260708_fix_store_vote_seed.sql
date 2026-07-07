-- Fix Trejo's typo → Trader Joe's; remove H-E-B from approved store vote chips.

update public.store_vote_items
set
  raw_text = 'Trader Joe''s',
  public_name = 'Trader Joe''s',
  normalized_name = public.normalize_tracker_vote_name('Trader Joe''s')
where normalized_name = public.normalize_tracker_vote_name('Trejo''s')
  and status = 'approved';

update public.store_vote_items
set
  status = 'rejected',
  rejected_at = now(),
  admin_notes = coalesce(admin_notes, '') || 'Removed from homepage chip list.'
where normalized_name = public.normalize_tracker_vote_name('H-E-B')
  and status = 'approved';
