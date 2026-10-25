# Landing page countdown (deployed 2026-10-25)

Template `jhp-charity-calendar-2027-v3`, page `charity-calendar-2027`.

- Application window on the page: Mon Oct 26 2026 9:00 AM CT (`OPEN_AT = 2026-10-26T14:00:00Z`)
  to Fri Oct 30 11:59 PM CT (`CLOSE_AT = 2026-10-31T05:00:00Z`).
- Before launch the form is hidden and three `[data-cd]` blocks (hero, apply, closing band)
  count down to opening; after launch they count down to close. At zero the page reloads
  itself to switch phase. After close they hide.
- Copy now names Friday Oct 30 at midnight (bar, hero pill, steps, closing band, fine print).
- `charity-app-ingest` still accepts submissions from Oct 22 through the close.

`countdown.patches.json` is the exact `templates_patch` call that was applied.
`test_countdown.js` is the Playwright check (pre-launch, open, closed, auto-flip at 9 AM).

## Offer removed from landing page (2026-10-25)

Per Jess: the $99 session / $500 off offer is revealed only in the invitation to selected
women. The landing page no longer shows the offer anywhere (meta tags, hero, offer band →
"By invitation / 2 minutes / Oct 2026 – Oct 2027", privacy bullet, step 03, FAQs, fine
print). The package qualifier on the form keeps its three choices but drops the prices.

## Past-client early access (2026-10-25)

`?access=vip` opens the form 24 hours early: Sun Oct 25 9:00 AM CT (`EARLY_AT`), counting
down "Opens to everyone in" until Monday 9 AM, then behaving like the public page. Before
Sunday 9 AM the VIP link shows "Your early access opens in". The link is only in the
past-client email. `test_vip_early_access.js` checks Sat night, Sun, plain link on Sun,
Tue, and the 9 AM Sunday flip.
