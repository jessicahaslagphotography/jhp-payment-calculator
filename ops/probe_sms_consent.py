#!/usr/bin/env python3
"""END-TO-END self-test for the SMS consent chain.

Submits two TEST leads to the real site-lead-submit webhook, one with the
consent box ticked and one without, and follows the flag the whole way:

    /contact  ->  webhook  ->  site_leads.sms_consent  ->  the SMS gate

Both are is_test=true, so they are stored and never pushed to GHL, never
enrolled and never texted. Both rows are deleted at the end.

WHY THIS EXISTS. Every link in that chain fails silently. A form that stops
sending the field, an ingest that stops reading it, an enroller that stops
stamping it -- none of them raise, and the visible result of all three is
identical to working correctly, right up until the day Jessica is texting
people who never agreed to it. TCPA damages are per message.

The gate itself is checked here too, against the enrollment shape the enroller
actually writes, because a consent flag that is stored perfectly and then read
from the wrong place is the same violation.
"""
import os
import sys
import time
import uuid
import logging
import psycopg2
import psycopg2.extras

sys.path.insert(0, '/home/scalogy/artifacts/workflow-runner')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'workflow-runner'))
import email_actions as ea            # noqa: E402

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('probe_sms_consent')

HOOK = 'https://app.scalogy.com/webhooks/in/jhpboudoir1/site-lead-submit'
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

    cases = [
        ('ticked', True),
        ('not ticked', False),
    ]
    # ONE SUBMISSION AT A TIME, AND WAIT FOR IT TO LAND.
    # The first run of this probe fired both POSTs 37ms apart. Both webhook
    # events were accepted and both reported 'run_workflow dispatched', but only
    # ONE workflow execution happened and the FIRST lead was lost. Two rapid
    # deliveries to the same workflow collide on the platform side. That is worth
    # knowing about in its own right -- see CLAUDE.md -- and it means a probe
    # that fires concurrently is testing the platform's dispatch rather than the
    # consent chain it is supposed to be testing.
    tokens = {}
    for label, consent in cases:
        tok = 'probe-sms-' + uuid.uuid4().hex[:12]
        tokens[label] = (tok, consent)
        body = {
            'client_token': tok,
            'name': 'Probe Consent',
            'email': f'{tok}@example.invalid',
            'phone': '(573) 555-0100',
            'sms_consent': consent,
            'source_page': '/contact',
            'is_test': True,
            'user_agent': 'sms consent self-test',
        }
        r = httpx.post(HOOK, json=body, timeout=30)
        log.info(f'{label}: webhook -> HTTP {r.status_code}')
        if r.status_code >= 400:
            fails.append(f'{label}: the webhook refused the POST ({r.status_code})')
            continue
        # Wait for this row before submitting the next one.
        landed = False
        for _ in range(14):
            time.sleep(1.5)
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM site_leads WHERE client_token=%s", (tok,))
                if cur.fetchone():
                    landed = True
                    break
        log.info(f'{label}: row {"landed" if landed else "DID NOT LAND"}')

    for label, (tok, want) in tokens.items():
        with conn.cursor() as cur:
            cur.execute("SELECT id, sms_consent, is_test FROM site_leads "
                        "WHERE client_token=%s", (tok,))
            row = cur.fetchone()
        if not row:
            fails.append(f'{label}: no site_leads row was ever written')
            continue
        if row['sms_consent'] is not want:
            fails.append(f'{label}: stored sms_consent={row["sms_consent"]!r}, '
                         f'expected {want!r} -- the consent flag is not surviving '
                         f'the trip from the form to the database')
        if row['is_test'] is not True:
            fails.append(f'{label}: the probe row was not stored as a test row')
        log.info(f'{label}: row #{row["id"]} sms_consent={row["sms_consent"]}')

    # And the gate, against the enrollment shape enroll_website_inquiry writes.
    MKT = sorted(ea.MARKETING_WORKFLOWS)[0]

    def enrollment_like(consent):
        return {'workflow': MKT,
                'contact': {'id': 'PROBE', 'email': 'probe@example.invalid'},
                'enrollment': {'id': 'probe', 'context': {
                    'site_lead_id': '0', 'source': 'website-contact-form',
                    'sms_consent': consent,
                    'guide_url': 'https://example.invalid/g',
                    'calendar_url': 'https://example.invalid/c'}}}

    if ea.sms_blocked_reason(enrollment_like(False)) is None:
        fails.append('the gate would text a lead who did NOT tick the box')
    unticked = ea.sms_blocked_reason(enrollment_like(True))
    if unticked and not unticked.startswith('quiet hours'):
        fails.append(f'a consented lead was blocked unexpectedly: {unticked!r}')
    log.info(f'gate with consent: {unticked or "would send"}')

    if not KEEP:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM site_leads WHERE client_token LIKE 'probe-sms-%'")
        log.info('probe rows cleaned up')
    conn.close()

    if fails:
        for f in fails:
            log.error(f)
        raise SystemExit(f'{len(fails)} check(s) failed')
    log.info('SMS CONSENT CHAIN PASSED - the ticked box is stored as consent, '
             'the unticked box is stored as refusal, and the gate refuses to '
             'text the one who did not tick it')


if __name__ == '__main__':
    main()
