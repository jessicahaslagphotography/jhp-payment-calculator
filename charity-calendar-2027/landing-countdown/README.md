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
