#!/usr/bin/env python3
"""END-TO-END self-test for the marketing email unsubscribe.

POSTs a DELIBERATELY FAKE contact to the real email-unsubscribe webhook, exactly
as the /unsubscribe page would, then reads back what the ingest did. Nothing
real is touched: the contact id does not exist in GHL, so the DND call is
expected to fail, and the point of the test is that the OPT-OUT IS STILL
RECORDED when it does. A request that is lost because GHL had a bad day is the
failure that matters here, and it is invisible unless somebody looks.

What a pass proves:
  * the webhook accepts an unsigned browser-shaped POST and fires the workflow
  * the email_optouts row is written and committed before GHL is involved
  * a GHL failure is recorded on the row rather than swallowed
  * no enrollment belonging to anybody else was cancelled

It cleans its own row up afterwards, so running it does not leave a fake
opt-out in the ledger.
"""
import os
import sys
import time
import logging
import psycopg2
import psycopg2.extras

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('probe_unsubscribe')

HOOK = 'https://app.scalogy.com/webhooks/in/jhpboudoir1/email-unsubscribe'
FAKE_ID = 'PROBE-not-a-real-contact'
FAKE_EMAIL = 'probe@example.invalid'
KEEP = '--keep' in sys.argv


def connect():
    return psycopg2.connect(
        dbname=os.environ['PGDATABASE'], user=os.environ['PGUSER'],
        host=os.environ['PGHOST'], cursor_factory=psycopg2.extras.RealDictCursor)


def main():
    import httpx
    fails = []

    conn = connect()
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) AS n FROM jhp_workflow_enrollments "
                    "WHERE status IN ('active','paused')")
        open_before = cur.fetchone()['n']
        cur.execute("DELETE FROM email_optouts WHERE ghl_contact_id=%s", (FAKE_ID,))

    body = {'c': FAKE_ID, 'e': FAKE_EMAIL, 'src': 'probe', 'ua': 'unsubscribe self-test'}
    r = httpx.post(HOOK, json=body, timeout=30)
    log.info(f'webhook -> HTTP {r.status_code} {r.text[:200]}')
    if r.status_code >= 400:
        fails.append(f'the webhook refused the POST ({r.status_code})')

    row = None
    for _ in range(20):
        time.sleep(1.5)
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM email_optouts WHERE ghl_contact_id=%s "
                        "ORDER BY id DESC LIMIT 1", (FAKE_ID,))
            row = cur.fetchone()
        if row:
            break

    if not row:
        fails.append('no email_optouts row appeared within 30s - the opt-out '
                     'would have been silently lost')
    else:
        log.info(f"row #{row['id']}: dnd_set={row['ghl_dnd_set']} "
                 f"cancelled={row['enrollments_cancelled']} "
                 f"error={(row['ghl_error'] or '-')[:120]}")
        if row['email'] != FAKE_EMAIL:
            fails.append('the email address did not round-trip')
        if row['ghl_dnd_set']:
            fails.append('GHL claims it set DND on a contact that does not '
                         'exist - the DND call is not being checked properly')
        if not row['ghl_error']:
            fails.append('a failed GHL call left no error on the row, so a real '
                         'outage would look like a success')
        if row['enrollments_cancelled'] != 0:
            fails.append(f"cancelled {row['enrollments_cancelled']} enrollment(s) "
                         f"for a contact that does not exist")

    with conn.cursor() as cur:
        cur.execute("SELECT count(*) AS n FROM jhp_workflow_enrollments "
                    "WHERE status IN ('active','paused')")
        open_after = cur.fetchone()['n']
    if open_after != open_before:
        fails.append(f'open enrollments moved {open_before} -> {open_after}')

    if not KEEP:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM email_optouts WHERE ghl_contact_id=%s", (FAKE_ID,))
        log.info('probe row cleaned up')
    conn.close()

    if fails:
        for f in fails:
            log.error(f)
        raise SystemExit(f'{len(fails)} check(s) failed')
    log.info('UNSUBSCRIBE END-TO-END PASSED - webhook fired, opt-out recorded, '
             'GHL failure surfaced, nobody else touched')


if __name__ == '__main__':
    main()
