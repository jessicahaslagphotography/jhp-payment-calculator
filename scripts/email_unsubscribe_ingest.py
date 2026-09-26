#!/usr/bin/env python3
"""email-unsubscribe-ingest: honour an unsubscribe from the marketing footer.

Fired by the email-unsubscribe webhook, which the /unsubscribe page POSTs to.

Three things happen, in this order, and the FIRST is the one that must never
fail: the row is written and committed before GHL is touched, so an opt-out
survives a GHL outage and can be replayed by hand. CAN-SPAM allows ten business
days to honour a request; this aims at ten seconds, but the durable record is
what makes the promise keepable either way.

  1. email_optouts row        the durable record, and the list every marketing
                              send checks before it goes out
  2. GHL tag                  'Email Unsubscribed', so the opt-out is visible to
                              Jessica in GHL and she can exclude them from
                              anything she sends by hand
  3. cancel open enrollments  so the sequence stops now rather than at the next
                              stopgate pass

IT DELIBERATELY DOES **NOT** SET GHL'S EMAIL DND, and that was a correction
made on 26 September rather than the original design. GHL's DND is ACCOUNT-WIDE:
it blocks every email to that contact, transactional included. So a woman who
unsubscribed from the nurture emails and later booked a session would silently
stop receiving her own confirmation, her contract and her image-reveal notice --
the automation would look healthy and she would simply never hear from the
studio again. Suppression therefore lives in email_optouts, which only marketing
sends consult, and the GHL tag carries the same information for Jessica's eyes
without the blast radius. If a hard account-wide block is ever wanted for one
person, set DND on that contact by hand in GHL.

ONLY MARKETING EMAIL IS AFFECTED. Her SMS and call consent are separate
permissions and an email unsubscribe is not a request about either.

THE TOKEN IS THE GHL CONTACT ID, and that is a deliberate, stated trade.
Anyone holding a contact id could opt that contact out of marketing email. The
id is a 20-plus character opaque value that appears nowhere public; the only
consequence is that somebody stops receiving marketing; and nothing
transactional is affected, because session confirmations, contracts and image
reveals carry no footer and are never suppressed by this. An HMAC would be
stronger and needs a tenant secret that does not exist yet -- if one is added,
sign the id on the way out and verify it here. What is NOT an acceptable
alternative is making unsubscribing harder in order to avoid the trade.

An unknown or missing contact id still writes the row with whatever did arrive,
usually the email address: a request we cannot match is still a request and
must not be dropped silently.

Body conventions (WEBHOOK_BODY, base64 fallback, stdin) are copied from
scripts/site_leads_ingest.py so every webhook on this tenant reads the same way.
"""
import os
import sys
import json
import base64
import logging
import psycopg2
import psycopg2.extras

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('email_unsubscribe_ingest')

MAX_BODY_BYTES = 20_000
GHL_BASE = 'https://services.leadconnectorhq.com'
GHL_VERSION = '2021-07-28'
UNSUB_TAG = 'Email Unsubscribed'
UA = ('JHPBoudoir-Scalogy/1.0 (email unsubscribe; '
      '+https://pages.scalogy.com/jhpboudoir1/)')


def _read_body():
    raw = os.environ.get('WEBHOOK_BODY') or os.environ.get('WEBHOOK_PAYLOAD') or ''
    if not raw:
        b64 = os.environ.get('WEBHOOK_RAW_BODY_BASE64')
        if b64:
            try:
                raw = base64.b64decode(b64).decode('utf-8', 'replace')
            except Exception:
                raw = ''
    if not raw and not sys.stdin.isatty():
        try:
            raw = sys.stdin.read(MAX_BODY_BYTES)
        except Exception:
            raw = ''
    raw = (raw or '')[:MAX_BODY_BYTES]
    try:
        d = json.loads(raw) if raw.strip() else {}
    except Exception:
        log.warning('body was not valid JSON')
        return {}
    return d if isinstance(d, dict) else {}


def connect():
    return psycopg2.connect(
        dbname=os.environ['PGDATABASE'], user=os.environ['PGUSER'],
        host=os.environ['PGHOST'], cursor_factory=psycopg2.extras.RealDictCursor)


def tag_unsubscribed(contact_id):
    """Tag the contact in GHL so the opt-out is visible there. (ok, error_text).

    A tag and not DND -- see the module docstring. This is for Jessica's eyes
    and for anything she sends by hand; what actually stops the automated
    marketing email is the email_optouts row, which email_actions checks on
    every marketing send.
    """
    token = os.environ.get('GHL_API_KEY')
    if not token:
        return False, 'missing GHL_API_KEY'
    try:
        import httpx
    except Exception as e:
        return False, f'httpx import failed: {e}'
    try:
        r = httpx.post(
            f'{GHL_BASE}/contacts/{contact_id}/tags',
            headers={'Authorization': f'Bearer {token}', 'Version': GHL_VERSION,
                     'Content-Type': 'application/json', 'Accept': 'application/json',
                     'User-Agent': UA},
            json={'tags': [UNSUB_TAG]}, timeout=20)
        if r.status_code >= 400:
            return False, f'GHL HTTP {r.status_code}: {r.text[:300]}'
        return True, None
    except Exception as e:
        return False, f'{type(e).__name__}: {e}'


def main():
    d = _read_body()

    def s(*keys, limit=400):
        for k in keys:
            v = d.get(k)
            if v is None:
                continue
            v = str(v).strip()
            if v:
                return v[:limit]
        return None

    cid = s('c', 'contact_id', limit=120)
    email = s('e', 'email', limit=200)
    source = s('src', 'source', limit=120) or 'email-footer'
    ua = s('ua', 'user_agent', limit=500)

    if not cid and not email:
        log.error('neither a contact id nor an email address - nothing to honour')
        return

    conn = connect()
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO email_optouts (ghl_contact_id, email, source, user_agent) '
                'VALUES (%s,%s,%s,%s) RETURNING id', (cid, email, source, ua))
            row_id = cur.fetchone()['id']
        conn.commit()
        log.info(f'opt-out #{row_id} recorded '
                 f'(contact={cid or "-"} email={email or "-"} src={source})')

        tag_ok, tag_err = False, 'no contact id supplied'
        if cid:
            tag_ok, tag_err = tag_unsubscribed(cid)
            log.info(f'GHL tagged {UNSUB_TAG!r}' if tag_ok
                     else f'GHL tag failed: {tag_err}')

        cancelled = 0
        with conn.cursor() as cur:
            if cid:
                cur.execute(
                    "UPDATE jhp_workflow_enrollments SET status='cancelled', "
                    "cancelled_reason='unsubscribed', next_action_at=NULL, "
                    "updated_at=NOW() WHERE ghl_contact_id=%s "
                    "AND status IN ('active','paused')", (cid,))
                cancelled += cur.rowcount
            if email:
                cur.execute(
                    "UPDATE jhp_workflow_enrollments SET status='cancelled', "
                    "cancelled_reason='unsubscribed', next_action_at=NULL, "
                    "updated_at=NOW() WHERE lower(contact_email)=lower(%s) "
                    "AND status IN ('active','paused')", (email,))
                cancelled += cur.rowcount
            cur.execute(
                'UPDATE email_optouts SET ghl_tag_set=%s, ghl_error=%s, '
                'enrollments_cancelled=%s WHERE id=%s',
                (tag_ok, None if tag_ok else (tag_err or '')[:500], cancelled, row_id))
        conn.commit()
        log.info(f'done - {cancelled} enrollment(s) cancelled, '
                 f'GHL tag {"set" if tag_ok else "NOT set"}. The opt-out itself '
                 f'is in email_optouts and is what stops the email.')
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
