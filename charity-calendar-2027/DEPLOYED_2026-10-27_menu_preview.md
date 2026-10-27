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
