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
  * THE OPT-OUT IS ACTUALLY ENFORCED: email_actions suppresses a marketing send
    to that contact and does not suppress anybody else. That is the check that
    matters -- a footer whose link records a request nobody reads back is
    decoration, and it would look exactly like this one working.

It cleans its own row up afterwards, so running it does not leave a fake
opt-out in the ledger.
"""
import os
import sys
import time
import logging
import psycopg2
import psycopg2.extras

sys.path.insert(0, '/home/scalogy/artifacts/workflow-runner')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'workflow-runner'))
import email_actions as ea            # noqa: E402

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
        log.info(f"row #{row['id']}: ghl_tag_set={row['ghl_tag_set']} "
                 f"cancelled={row['enrollments_cancelled']} "
                 f"error={(row['ghl_error'] or '-')[:120]}")
        if row['email'] != FAKE_EMAIL:
            fails.append('the email address did not round-trip')
        if row['ghl_tag_set']:
            fails.append('GHL claims it tagged a contact that does not exist - '
                         'the tag call is not being checked properly')
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

    # The part that actually matters: is the opt-out enforced on a send?
    if row:
        opted_out = {'contact': {'id': FAKE_ID, 'email': FAKE_EMAIL}}
        someone_else = {'contact': {'id': 'PROBE-different-person',
                                   'email': 'other@example.invalid'}}
        if not ea.is_suppressed(conn, opted_out):
            fails.append('the opt-out is NOT enforced - a marketing email would '
                         'still go to somebody who unsubscribed')
        if ea.is_suppressed(conn, someone_else):
            fails.append('somebody who did NOT unsubscribe is being suppressed')
        for wf in sorted(ea.MARKETING_WORKFLOWS):
            if not ea.WHY.get(wf):
                fails.append(f'{wf} is marketing but the footer has no reason '
                             f'line for it, so it falls back to the generic one')
        log.info('sequences carrying the footer: '
                 + ', '.join(sorted(ea.MARKETING_WORKFLOWS)))

    # ---------------------------------------------------------------- SMS gate
    # Consent, quiet hours and the opt-out, checked as behaviour rather than as
    # wording. The copy carrying 'Reply STOP' is the builder's job; this is the
    # part that decides whether a text actually leaves.
    MKT = sorted(ea.MARKETING_WORKFLOWS)[0]

    def sms_ctx(consent, **kw):
        c = {'id': kw.get('cid', 'PROBE-sms'), 'email': kw.get('email',
                                                               'sms@example.invalid')}
        return {'workflow': kw.get('wf', MKT), 'contact': c,
                'enrollment': {'id': 'probe', 'context': {'sms_consent': consent}}}

    no_consent = ea.sms_blocked_reason(sms_ctx(False))
    if not no_consent or 'consent' not in no_consent:
        fails.append(f'a marketing text with NO consent was not blocked '
                     f'(reason={no_consent!r})')
    for bad in (None, 'true', 1, 'yes'):
        # Only a real boolean True is consent. A truthy string is what a
        # mis-wired form sends, and it must not be read as a person agreeing.
        r = ea.sms_blocked_reason(sms_ctx(bad))
        if not r:
            fails.append(f'sms_consent={bad!r} was accepted as consent')

    with_consent = ea.sms_blocked_reason(sms_ctx(True))
    if with_consent and not with_consent.startswith('quiet hours'):
        fails.append(f'a consented marketing text was blocked for an unexpected '
                     f'reason: {with_consent!r}')
    log.info(f'consented marketing text right now: '
             f'{with_consent or "would send"}')

    # Transactional texts are not gated by any of this, the same way they carry
    # no footer. A session reminder must not wait on a marketing consent box.
    trans = ea.sms_blocked_reason(sms_ctx(False, wf='image_reveal'))
    if trans is not None:
        fails.append(f'a TRANSACTIONAL text was blocked ({trans!r}) - a session '
                     f'reminder must not depend on marketing consent')

    if not (0 <= ea.SMS_QUIET_START < ea.SMS_QUIET_END <= 24):
        fails.append(f'the quiet-hours window is nonsense: '
                     f'{ea.SMS_QUIET_START}-{ea.SMS_QUIET_END}')
    log.info(f'quiet hours: texts only {ea.SMS_QUIET_START:02d}:00-'
             f'{ea.SMS_QUIET_END:02d}:00 {ea.SMS_TZ}')

    if not KEEP:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM email_optouts WHERE ghl_contact_id=%s", (FAKE_ID,))
        log.info('probe row cleaned up')
    conn.close()

    if fails:
        for f in fails:
            log.error(f)
        raise SystemExit(f'{len(fails)} check(s) failed')
    log.info('COMPLIANCE END-TO-END PASSED - webhook fired, opt-out recorded, '
             'GHL failure surfaced, nobody else touched, email suppression '
             'enforced, and the SMS gate refuses an unconsented text')


if __name__ == '__main__':
    main()
