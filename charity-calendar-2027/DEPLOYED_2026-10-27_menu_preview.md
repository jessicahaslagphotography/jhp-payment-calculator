# 2026-10-27: CCMC investment menu preview page

Page forms-pspp-2027-ccmc-menu (app pspp-checkout-v2), bound to the shared checkout
template forms-pspp-setup-editorial-pspp-checkout-v2 (47f596b3-...). New flag
IS_MENU_ONLY (path contains forms-pspp-2027-ccmc-menu), so no other page changes:

- Shows the CCMC menu (same collections, prices, inclusions, calendar-vote note).
- Back button and step dots hidden; intro/heading/how-it-works copy reworded.
- The bottom button is always enabled and never submits a booking:
  ?t=<invite_token> -> "Begin My Booking" -> ccmc-claim/?t=<token> (claim, then the
  claim page forwards to the real booking page; already-claimed shows its
  continue-to-booking link). No ?t= -> "Email Me to Book" (mailto jessica@).
- Link to send: https://pages.scalogy.com/jhpboudoir1/forms-pspp-2027-ccmc-menu/?t=<invite_token>
  (invite_token from charity_calendar_applications).

Verified locally: no JS errors; button text/behaviour with and without ?t=; the
real forms-pspp-2027-ccmc page unchanged (Continue, dots visible).

## Security fix (same day, Jessica approved "that needs locked down")

security_check flagged psppv2_form_assets (all contracts + collection photos) as
publicly WRITABLE through app pspp-checkout-v2 (allow_write=true on that attachment).
The checkout template only GETs it (all writes go through webhooks), so the
attachment was re-made with allow_write=false. The other five apps sharing the
table were already read-only. Audit: all 22 rows present, updated_at values match
known edits, no script/iframe content in any contract. contract-lastminute-2026's
`bytes` column was stale from its documented 2026-10-13 edit and was corrected.
Still open (reported, not changed): the table is publicly readable (by design, the
pages need it), and several webhooks are unsigned.

## Daily booking reminders (Jessica: "Every day")

ops/ccmc_booking_deadline_monitor.py (workflow ccmc-booking-deadline-monitor, hourly
at :41): the single 48-hour reminder is replaced by one email + SMS per Central
calendar day while a claim is unbooked, starting the day after she claims, only
9 AM-8 PM Central, with a countdown ("6 days left" ... "Today is your last day").
New columns ccmc_reservations.last_reminder_at, reminder_count. Stops when she
books (booking check runs before the reminder). First live run 2026-10-27 3:04 PM
CT reminded Mia Malcolm and Kelsie Depew (6 days left); the four who claimed today
start tomorrow.
