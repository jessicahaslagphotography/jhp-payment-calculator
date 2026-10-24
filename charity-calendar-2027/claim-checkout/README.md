# CCMC "Claim your spot" — build kit (NOT deployed)

2027 Charity Calendar Model Call reservation checkout, cloned from the Everybody
Model Call (EMC) reserve flow. Nothing here has been written to the Scalogy
tenant, Square or GHL. Everything below is the plan for whoever deploys it.

## Files

| File | Becomes |
|---|---|
| `ccmc_tables.sql` | `ccmc_reservations` (private, PII) + `ccmc_reservation_status` (PII-free, page-polled) |
| `ccmc_claim.template.html` | template `ccmc-claim`, page slug `ccmc-claim` |
| `ccmc_reserve_charge.py` | workflow `ccmc-reserve-charge` (webhook-fired) |
| `ccmc_reserve_monitor.py` | workflow `ccmc-reserve-monitor` (cron, $98 balance) |
| `ccmc_booking_deadline_monitor.py` | workflow `ccmc-booking-deadline-monitor` (cron, 7-day booking clock + 48h reminder) |

## The flow

1. Jessica approves an application. A separate invite sender (out of scope) sets
   `charity_calendar_applications.status='invited'`, `invite_token=<random hex>`,
   `invited_at=now()`, `claim_deadline=now()+72h`, and sends
   `https://pages.scalogy.com/jhpboudoir1/ccmc-claim/?t=<invite_token>`.
2. **Page load.** No `?t=` (or a malformed one) shows "This link is personal" and
   does not load the card form. Otherwise the page POSTs `{mode:'check', client_token, invite_token}`
   to `ccmc-reserve-pay` and polls `_api/ccmc_reservation_status`. The charger answers with
   `ready` (the form appears with "please claim by …"), `invalid`, `expired`, or `claimed`
   (a closed screen, plus a "Continue to booking" button if her claim is live).
   If the check is slow (about 30s) the form appears anyway, because the pay run checks the invite again.
3. **Pay.** Plan `full` ($99) or `deposit` ($1 now, $98 auto-charged on a date 1–14 days out),
   name on card (used only for Square `verifyBuyer`, never sent to the server), Square
   tokenize + `verifyBuyer` `CHARGE_AND_STORE`, and the non-refundable checkbox. The POST body is
   `{client_token, invite_token, sourceId, verification_token, plan, balance_date, acknowledged, is_test, user_agent}`.
4. **Charger.** It locks the application row by `invite_token` and refuses (writing a status row with a
   friendly message) when the token is unknown, the status is not `invited`, or `now > claim_deadline`.
   Name, email and phone come only from the application row. The Square customer, card, payment,
   order and invoice logic and the amounts are the same as EMC. Idempotency keys start with
   `ccmccu-/ccmccd-/ccmcch-/ccmcor-/ccmciv-/ccmcpb-`. On success:
   - reservation becomes `paid` (full) or `reserved` (deposit), with `booking_deadline = now()+7d` on **both** plans
   - application becomes `claimed`, with `reserved_at = now()`
   - GHL gets tags `Charity Calendar 2027 - Claimed` (+ `- Paid` on full)
   - SMS and branded email with the booking link and deadline
   - an `action_queue` owner alert (`ccmc_reservation_alert`)
5. The page decrypts `next_url` and redirects there **only if** it starts with
   `https://pages.scalogy.com/jhpboudoir1/`. Otherwise it says "check your email and texts".
6. **ccmc-reserve-monitor** (every 15 min) watches every open $98 (`plan='deposit' AND paid_at IS NULL`):
   - When the invoice is PAID: set `paid_at`. A `reserved` claim becomes `paid`. Tag `- Paid`.
     Send a short "balance received" SMS and email with no booking link (skipped if forfeited). Owner alert.
   - When it expires unpaid:
     - `reserved`: cancel the invoice, mark it `released`, set the application to `released` with `released_at`, tag `- Released (balance unpaid)`, owner alert.
     - `booked`: no release. Alert the owner once (`balance_alerted_at`).
     - `forfeited`: cancel the invoice and alert the owner.
   - It also prunes stale non-claim status rows older than 2 days.
7. **ccmc-booking-deadline-monitor** (hourly) checks `paid`/`reserved` claims that are not booked:
   - A non-test `psppv2_form_responses` row for her email or GHL id, `submitted_at >= reserved_at`, makes it `booked` (application `booked`, tag `- Booked`).
   - Past `booking_deadline` it becomes `forfeited` (application `forfeited` + `released_at`, tag `- Forfeited (no booking)`, owner alert `ccmc_booking_forfeit`).
   - Otherwise it sends **one** reminder email and SMS within 48h of the deadline, between 9am and 8pm Central, tracked by `reminder_sent_at`.

### Statuses

- `ccmc_reservations.status`: `new → reserved | paid → booked | forfeited | released`, plus `error`.
- `charity_calendar_applications.status` (values this kit adds): `claimed`, `booked`, `forfeited`, `released`.
- `ccmc_reservation_status.status`: `ready, invalid, expired, claimed, new, error, reserved, paid, booked, released, forfeited`.

## Objects to create

### Tables

Run each statement in `ccmc_tables.sql` with `db_query`, one per call. Then:

- `tables_create ccmc_reservations`: private. **Never attach it to any app.**
- `tables_create ccmc_reservation_status`: the only table the page sees.

### Webhook

- `endpoint_slug: ccmc-reserve-pay`
- `signing_mode: none` (the caller is a browser, same as every other reserve hook on this tenant)
- `action_kind: run_workflow`, `action_target: ccmc-reserve-charge`
- Description: Browser-originated (no-cors) claim checkout for page ccmc-claim. Body is
  `{mode:'check'|'pay', client_token, invite_token, sourceId, verification_token, plan, balance_date, acknowledged, is_test, user_agent}`.
  The invite_token is the authorization, and the script re-validates everything server-side.
  Amounts are fixed in the script. It dedupes on client_token and on application.

### Workflows

Upload the scripts to tenant artifacts first, at the `script_path`s below (same layout as EMC). Settings shared by all three:

- `interpreter: python3`
- `source: artifacts`
- `memory_max: 512M`

| name | trigger | schedule (`on_calendar`) | script_path | timeout | declared_secrets |
|---|---|---|---|---|---|
| `ccmc-reserve-charge` | `manual` (on_demand, fired by the webhook) | — | `scripts/ccmc_reserve_charge.py` | 600 | `square_access_token`, `ghl_api_key`, `ghl_location_id` |
| `ccmc-reserve-monitor` | `cron` | `*-*-* *:11/15:00` (every 15 min, offset from EMC's :7) | `ops/ccmc_reserve_monitor.py` | 600 | `square_access_token`, `ghl_api_key` |
| `ccmc-booking-deadline-monitor` | `cron` | `*-*-* *:41:00` (hourly) | `ops/ccmc_booking_deadline_monitor.py` | 300 | `ghl_api_key` |

If you flip `SQUARE_ENV='sandbox'` for testing, declare `square_sandbox_access_token` instead,
because the scripts read `SQUARE_SANDBOX_ACCESS_TOKEN`.

Create both cron workflows **paused** and unpause them after the test plan passes.

### Template, page, app

- `templates_create` name `ccmc-claim` from `ccmc_claim.template.html`. Its JS is inside `{% raw %}` and it renders cleanly with Jinja2.
- `pages_create` slug `ccmc-claim`, name "Claim Your Spot · 2027 Charity Calendar". Then `pages_set_template`.
- `apps_create` slug `ccmc-claim`, then attach:
  - `kind=page`: `ccmc-claim`
  - `kind=db_table`: `ccmc_reservation_status`, **read-only** (`allow_write` false). Attach nothing else.
- `pages_render ccmc-claim`. Then run `security_check(app_slug='ccmc-claim')` and confirm
  that only `ccmc_reservation_status` is exposed.
- The page has `noindex` and `referrer: no-referrer`, so the `?t=` token doesn't leak through the Referer header to Google Fonts or Square.

### Small follow-up in an existing script (optional)

`notify_via_ghl.py` already delivers these alerts, because every CCMC alert row carries Jessica's
email (`is_owner_alert`). For clarity, consider adding `ccmc_reservation_alert` and
`ccmc_booking_forfeit` to `OWNER_ALERT_ACTIONS`.

## Deploy order

1. Tables: SQL, then `tables_create` for both.
2. Upload the three scripts to artifacts.
3. Create the workflows. Create the monitors paused.
4. Create the webhook `ccmc-reserve-pay` pointing at `ccmc-reserve-charge`.
5. Create the template and the page, set the template, create the app, attach the page and the status table (read-only), render, and run `security_check`.
6. **Prerequisite:** the booking page `forms-pspp-2027-ccmc` **does not exist yet** (checked with
   `pages_list` on 2026-10-24). It must exist before launch, or every redirect and email link 404s.
7. Run the test plan below.
8. Unpause the monitors. Turn on the invite sender last.

## Test plan

**Test mode is decided by the APPLICATION row, not the URL.** If `?test=1` is used on a real invite,
the charger refuses with "Test mode isn't available for this invitation". If the application is a test row
(`is_test=true`), the charger short-circuits before any Square or GHL call, whatever the URL says.
Use `?test=1` anyway on test invites, so the page sends `is_test` the same way EMC does.

1. **Seed a test invite.** `charity_calendar_applications.client_token` is NOT NULL and unique:
   ```sql
   INSERT INTO charity_calendar_applications
     (client_token, contact_name, contact_email, contact_phone, status, invite_token,
      invited_at, claim_deadline, is_test, acknowledged)
   VALUES ('ccmc-test-1', 'Test Claimer', 'jessicahaslagphotography+ccmctest@gmail.com', '5735550100',
           'invited', md5(random()::text) || md5(random()::text), now(), now() + interval '72 hours',
           true, true)
   RETURNING id, invite_token;
   ```
2. **Page states:**
   - No `?t=`: shows "This link is personal" and no card form.
   - `?t=abc`: same.
   - `?t=<64 random hex>`: shows "We couldn't find this invitation".
   - Set the test row's `claim_deadline = now() - interval '1 minute'`: shows "This invitation has expired". Reset it afterwards.
3. **Test claim, both plans.** Open `/ccmc-claim/?t=<token>&test=1` and pick the $1 plan.
   The live Square card form still loads. Use a real card: verifyBuyer runs but **no charge is made**,
   because the server short-circuits. Then check:
   - `ccmc_reservations` has `status='reserved'`, `booking_deadline ≈ now()+7d`, and `next_url` with `&test=1`.
   - The application is `claimed`.
   - The page redirects to `forms-pspp-2027-ccmc/?name=…&email=…&phone=…&test=1`.

   Reset the application to `invited`, set the first test reservation's status to `error` (otherwise the one-live-claim-per-application guard blocks the retry), clear the browser's localStorage key `ccmcResvToken`, and repeat with the $99 plan. Expect `status='paid'`.
   Cleanup: `ccmc_reservations.application_id` has a foreign key, so delete test reservations before deleting test applications.
4. **Already claimed.** Reload the original invite link. You should get "You've already claimed your spot" with a "Continue to booking" button.
5. **Exposure check.** Fetch `_api/ccmc_reservation_status` with the page token. Rows should hold only
   `token_hash`, status and dates, plus an opaque `next_url_enc`. No names, emails, phones or invite tokens.
6. **Deadline monitor on test rows.** It performs DB transitions for `is_test` rows and skips GHL and alerts:
   - Set `booking_deadline = now() + interval '47 hours'` and run it. `reminder_sent_at` gets set. The send itself is skipped and logged.
   - Set `booking_deadline = now() - interval '1 minute'` and run it. The reservation and the application both become `forfeited`.
   - Booked detection needs a **non-test** `psppv2_form_responses` row, so it can only be exercised for real, or with a temporary non-test row you delete afterwards.
7. **Square sandbox, end to end** (charger and reserve monitor; the reserve monitor ignores `is_test` rows like EMC):
   - In all three scripts set `SQUARE_ENV='sandbox'`.
   - In the page, set APP_ID to the **sandbox application id** (not on file in the EMC sources, so it has to come from the Square dashboard), LOCATION_ID `LPFHRECZXJ8EV`, and the SDK `https://sandbox.web.squarecdn.com/v1/square.js`.
   - Declare `square_sandbox_access_token`.
   - Use a NON-test application row with a sandbox card such as 4111 1111 1111 1111. **This sends real GHL SMS and email to the row's contact**, so point it at Jessica's own number and address.
   - Check $1 + invoice. Then pay the sandbox invoice in the Square dashboard and run the monitor: expect `paid` and a "balance received" message.
   - Check expiry: set `expires_at` in the past on an unpaid one, and expect it `released` with the invoice cancelled.
   - **Flip everything back to production** before launch.
8. **Double-submit.** Open the invite in two tabs and pay in both within a few seconds. The second gets
   "It looks like your claim is already going through". Only one charge appears in Square.

## Design decisions worth knowing

- **Encrypted `next_url`, hashed row key.** The spec put the prefilled booking link (name, email,
  phone) in `ccmc_reservation_status.next_url`. That table is readable **in full** by anyone who loads
  the public page, because the page token reads every row. Storing plaintext would have exposed every
  claimant's contact details. So:
  - rows are keyed by `token_hash = sha256(client_token)`
  - the link is stored as `next_url_enc`: HMAC-SHA256 counter-mode keystream, key `sha256('ccmc-next-url|'+client_token)`, random 16-byte nonce
  - only the browser holding the raw `client_token` can decrypt it

  The Python encrypt and WebCrypto decrypt were cross-tested in Node. The private copy of `next_url` lives in `ccmc_reservations`.
- **Invite pre-check (`mode:'check'`).** Without it, an expired or already-claimed invitee would only find out after entering a card.
- **Webhook re-POSTs.** The runner drops a dispatch that arrives while the workflow is already running,
  which can be any visitor's run (see the session-reschedule template). So the page re-POSTs the same
  payload up to 3 times while the row hasn't moved. This is safe because of the same-token dedupe and the identical Square idempotency keys.
- **Error retry.** After an `error`, the page mints a **new** client_token. EMC reused the same token,
  so a retry with a different card hit the same Square idempotency keys.
- **Charged means never `error`.** After the payment succeeds, the DB is finalized **before** GHL and
  messaging. A later exception queues an owner alert instead of telling the client it failed.
- **Partial success blocks a second $1.** A row that already took the $1 but failed to schedule the $98
  blocks a second claim, and Jessica is alerted to finish it by hand.
- **GHL tags are additive.** The upsert carries no tags, and tags go through `POST /contacts/{id}/tags`,
  so the application-stage tags are never overwritten. (EMC passed tags inside the upsert.)
- **Email logo.** It uses the GHL-CDN logo from `email_actions.py`, not the Drive thumbnail EMC used,
  because Drive links break in many inboxes. All interpolated values are HTML-escaped.
- **Balance tracking is separate from claim status.** Booking opens right after $1, so a claim can be
  `booked` while its $98 is pending. The monitor never releases a booked client. It alerts Jessica instead.
- **`receipt_url`** is kept in the status table for parity but left NULL, because a Square receipt shows card details and the table is public.

## Open questions / unsure

1. **Booking page** `forms-pspp-2027-ccmc` doesn't exist yet. Its `form_slug` also matters if the
   "booked" signal should be narrowed: right now any non-test psppv2 row after the claim counts, as in EMC.
   The workflow runner and enroll-booked use `square_status LIKE 'completed%'`; I didn't, to avoid false forfeits.
2. **Season dates.** The spec says sessions **October 2026**–October 2027 are calendar-eligible. The
   `charity-calendar-2027` landing page description says **Nov 2026**–Oct 2027. Confirm which and fix the copy if needed.
3. **"Through March 2028"** is read as the session date, not the date the booking is made.
4. **Forfeited $1 claims with a pending $98.** The $98 invoice is left alone at forfeit. If it charges
   on its date, it's kept, because the fee is non-refundable and she authorized it. If it's still unpaid
   at expiry, it's cancelled. Jessica may prefer to cancel it at forfeit time instead.
5. **Booked but $98 failed** gets an owner alert only, with no auto-release. Confirm.
6. **Expired claim window.** Nothing flips an `invited` application whose 72h passed. The page just says
   "expired". If Jessica wants such applications marked (for example `status='expired'`) or wants to
   re-offer the spot, that belongs in the invite sender or a small cron.
7. **Square sandbox APP_ID** isn't in the sources. It's needed for the sandbox test path.
8. **`ghl_location_id`** is declared for the charger, as EMC does. The monitors don't need it.
9. **Page token TTL.** The reschedule template says page tokens last 15 minutes, while the platform notes
   say they never expire. The page reloads on a 401. The persisted claim token makes the reload resume the in-flight claim.
10. **Status-table growth.** The page reads `?limit=500` and matches client-side, like EMC. The monitor
    prunes stale check rows. If `_api` supports server-side equality filters (help article
    `getting-started/page-api-filters`), switching to `?token_hash=<hash>` would be tidier.
