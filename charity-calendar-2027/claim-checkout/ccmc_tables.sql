-- 2027 Charity Calendar Model Call (CCMC) — "claim your spot" reservation tables.
-- Clone of emc_reservations / emc_reservation_status with the CCMC differences.
--
-- db_query runs ONE statement per call: run each statement below separately,
-- in order, then register both tables with tables_create.
--
-- ccmc_reservations        PRIVATE (PII). Never attach to any app/page.
-- ccmc_reservation_status  PII-FREE, polled by page ccmc-claim through _api
--                          (attach READ-ONLY to app ccmc-claim). Every visitor
--                          holding the public page token can read EVERY row, so:
--                            * rows are keyed by sha256(client_token), never the
--                              raw client_token (the raw token is the key that
--                              decrypts next_url_enc in the claimant's browser);
--                            * next_url (which carries name/email/phone prefill)
--                              is stored only ENCRYPTED in next_url_enc;
--                            * no names, emails, phones, invite tokens, Square ids.

-- 1) private reservation ledger ------------------------------------------------
CREATE TABLE IF NOT EXISTS ccmc_reservations (
    id                          serial PRIMARY KEY,
    application_id              bigint REFERENCES charity_calendar_applications(id),
    invite_token                text,
    client_token                text UNIQUE,
    contact_name                text,
    contact_email               text,
    contact_phone               text,
    plan                        text,                 -- 'full' | 'deposit'
    balance_due_date            date,
    deposit_cents               integer,
    balance_cents               integer,
    status                      text,                 -- new|error|reserved|paid|booked|forfeited|released
    is_test                     boolean DEFAULT false,
    user_agent                  text,
    expires_at                  timestamptz,          -- deposit: balance_date+2d grace (release cutoff for the $98)
    booking_deadline            timestamptz,          -- claim time + 7 days (BOTH plans)
    next_url                    text,                 -- prefilled PSPP booking link (private copy, used in emails)
    reserved_at                 timestamptz,
    paid_at                     timestamptz,          -- full $99 collected (full plan at charge; deposit when invoice PAID)
    handed_off_at               timestamptz,
    released_at                 timestamptz,
    booked_at                   timestamptz,
    forfeited_at                timestamptz,
    reminder_sent_at            timestamptz,          -- the single ~48h booking reminder (sent once)
    balance_cancelled_at        timestamptz,          -- $98 invoice cancelled by a monitor
    balance_alerted_at          timestamptz,          -- owner told: booked/forfeited but $98 still unpaid at expiry
    square_customer_id          text,
    square_card_id              text,
    square_deposit_payment_id   text,
    square_invoice_id           text,
    square_invoice_public_url   text,
    ghl_contact_id              text,
    card_error                  text,
    notes                       text,
    created_at                  timestamptz DEFAULT now()
);

-- 2) lookups used by the charger guard + monitors (non-unique on purpose: a
--    claim that errored and was retried with a fresh client_token leaves an
--    'error' row behind for the same application)
CREATE INDEX IF NOT EXISTS ccmc_reservations_application_idx ON ccmc_reservations (application_id);

CREATE INDEX IF NOT EXISTS ccmc_reservations_status_idx ON ccmc_reservations (status);

-- 3) PII-free status table polled by the page --------------------------------
CREATE TABLE IF NOT EXISTS ccmc_reservation_status (
    token_hash        text PRIMARY KEY,               -- lower-hex sha256(client_token)
    status            text,                           -- ready|invalid|expired|claimed|new|error|reserved|paid|booked|released|forfeited
    card_error        text,                           -- friendly, PII-free message for the page
    balance_due_date  date,
    claim_deadline    timestamptz,                    -- shown as "claim by ..." on the page
    receipt_url       text,                           -- kept for parity with EMC; left NULL (see README)
    next_url_enc      text,                           -- base64(nonce16 || ciphertext), key = sha256('ccmc-next-url|' || client_token)
    updated_at        timestamptz DEFAULT now()
);
