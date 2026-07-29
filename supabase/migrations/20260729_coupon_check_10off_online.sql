-- Seed homepage coupon check for $10 off next online order (PickUp & Delivery).
-- Reuses coupon_check_polls / coupon_check_options + vote_coupon_check from 20260715.

insert into public.coupon_check_polls (id, question, expires_at)
values (
  'safeway_pickup_delivery_10off_202608',
  'Safeway shoppers — do you see this coupon?',
  '2026-08-11'
)
on conflict (id) do nothing;

insert into public.coupon_check_options (id, poll_id, label, sort_order, vote_count)
values
  ('safeway_pickup_delivery_10off_202608_yes', 'safeway_pickup_delivery_10off_202608', 'Yep', 1, 0),
  ('safeway_pickup_delivery_10off_202608_no', 'safeway_pickup_delivery_10off_202608', 'Nope', 2, 0)
on conflict (id) do nothing;
