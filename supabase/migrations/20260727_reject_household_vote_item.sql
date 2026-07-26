-- Household items is too vague for product voting and crowds out real staples
-- in the top-6 vote strip (all chips currently at 0 votes, alphabetical).

update public.tracker_vote_items
set
  status = 'rejected',
  rejected_at = now(),
  admin_notes = coalesce(admin_notes || ' ', '') ||
    'Removed from public vote list: not a specific grocery product family.'
where status = 'approved'
  and normalized_name = public.normalize_tracker_vote_name('Household items');
