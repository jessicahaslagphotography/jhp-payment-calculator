#!/usr/bin/env python3
"""Exit guard for the 'Website Inquiry - 2027' sequence.

An eight-touch sequence running for six months is only safe if it stops the
moment it stops being true. The runner's own gates cannot see any of these
signals -- they are not form submissions -- so they are checked here, every five
minutes, and the enrollment is CANCELLED rather than deleted so the funnel
history survives.

WHAT STOPS IT, and how each one is detected:

  booked_call    She booked the Boudoir Consultation Call. One GHL
                 /calendars/events read per run (not per lead) over a wide
                 window, matched on contactId. She is in the pre-call flow now
                 and a "book your call" email would read as though nobody
                 noticed.
  inquired       She came back and filled in /inquire (site_inquiries). That is
                 a warmer form with its own tag and its own follow-up; two
                 sequences at once is the thing that looks automated.
  booked_paid    A completed PSPP v2 booking, or a paid promo/treehouse
                 reservation, under her email. She is a client.
  unsubscribed   GHL says email DND. Required, not optional.
  replied        She replied to an email or a text. Automation gives way to a
                 conversation -- Jessica is talking to her now.

WHAT DOES NOT STOP IT: opening an email, clicking a link, or time passing. The
sequence is meant to run its length.

EVERY EXTERNAL CHECK FAILS SAFE. A GHL error, a timeout, a shape we did not
expect -- none of them cancel anybody. The cost of a missed exit is one extra
email; the cost of a false exit is a lead dropped silently, which is worse and
invisible. Nothing here ever un-cancels an enrollment either.

--dry-run reports and writes nothing.
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone, timedelta
import psycopg2
import psycopg2.extras
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('website_inquiry_stopgate')

WF_NAME = 'website_inquiry_2027'
CALENDAR_ID = 'mi2EqYRq4gGEbBJHe82b'          # Boudoir Consultation Call
GHL_BASE = 'https://services.leadconnectorhq.com'
# urllib's and requests' default agents are both liable to Cloudflare's
# "browser signature banned" 1010 in front of this host. Be honest instead.
UA = ('JHPBoudoir-Scalogy/1.0 (website-inquiry stopgate; '
      '+https://pages.scalogy.com/jhpboudoir1/)')

DRY = '--dry-run' in sys.argv


def connect():
    return psycopg2.connect(
        dbname=os.environ['PGDATABASE'], user=os.environ['PGUSER'],
        host=os.environ['PGHOST'], cursor_factory=psycopg2.extras.RealDictCursor)


def _hdrs():
    key = os.environ.get('GHL_API_KEY')
    if not key:
        raise RuntimeError('GHL_API_KEY not declared on this workflow')
    return {'Authorization': f'Bearer {key}', 'Version': '2021-04-15',
            'Accept': 'application/json', 'User-Agent': UA}


def booked_contact_ids():
    """GHL contact ids with a consultation appointment in a wide window.

    One call for the whole run. The calendar itself only opens four days out,
    but a window of -60/+120 days costs nothing and covers an appointment she
    booked before this guard existed, or one Jessica moved out by hand.

    Returns None on any failure, which the caller reads as "do not use this
    signal on this pass" rather than as "nobody has booked".
    """
    loc = os.environ.get('GHL_LOCATION_ID')
    if not loc:
        log.warning('no GHL_LOCATION_ID - skipping the booked-call signal')
        return None
    now = datetime.now(timezone.utc)
    params = {
        'locationId': loc,
        'calendarId': CALENDAR_ID,
        # GHL wants epoch milliseconds here.
        'startTime': str(int((now - timedelta(days=60)).timestamp() * 1000)),
        'endTime': str(int((now + timedelta(days=120)).timestamp() * 1000)),
    }
    try:
        r = requests.get(f'{GHL_BASE}/calendars/events', headers=_hdrs(),
                         params=params, timeout=30)
        if not r.ok:
            log.warning(f'calendars/events -> {r.status_code}: {r.text[:200]}')
            return None
        data = r.json() or {}
        events = data.get('events') or data.get('appointments') or []
        ids = set()
        for e in events:
            cid = e.get('contactId') or (e.get('contact') or {}).get('id')
            status = (e.get('appointmentStatus') or e.get('status') or '').lower()
            if cid and status not in ('cancelled', 'canceled', 'noshow', 'no-show'):
                ids.add(cid)
        log.info(f'{len(events)} consultation event(s), {len(ids)} distinct contact(s)')
        return ids
    except Exception as e:
        log.warning(f'booked-call signal unavailable: {e}')
        return None


def has_replied(contact_id, since):
    """True only if GHL clearly shows an INBOUND message after enrollment.

    Anything ambiguous returns False: an exit we did not take costs one email,
    an exit we took wrongly costs the lead.
    """
    if not contact_id:
        return False
    try:
        r = requests.get(f'{GHL_BASE}/conversations/search', headers=_hdrs(),
                         params={'locationId': os.environ.get('GHL_LOCATION_ID', ''),
                                 'contactId': contact_id}, timeout=30)
        if not r.ok:
            return False
        for conv in (r.json() or {}).get('conversations') or []:
            if (conv.get('lastMessageDirection') or '').lower() != 'inbound':
                continue
            ts = conv.get('lastMessageDate') or conv.get('dateUpdated')
            if ts is None:
                continue
            try:
                # GHL gives epoch ms here, occasionally an ISO string.
                when = (datetime.fromtimestamp(int(ts) / 1000, timezone.utc)
                        if str(ts).isdigit()
                        else datetime.fromisoformat(str(ts).replace('Z', '+00:00')))
            except Exception:
                continue
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            if when > since:
                return True
        return False
    except Exception as e:
        log.warning(f'reply signal unavailable for {contact_id}: {e}')
        return False


def cancel(conn, enr_id, reason):
    if DRY:
        log.info(f'[dry-run] would cancel #{enr_id} ({reason})')
        return
    with conn.cursor() as cur:
        cur.execute("UPDATE jhp_workflow_enrollments SET status='cancelled', "
                    "cancelled_reason=%s, next_action_at=NULL, updated_at=NOW() "
                    "WHERE id=%s AND status IN ('active','paused')", (reason, enr_id))
    log.info(f'cancelled #{enr_id} - {reason}')


def probe():
    """Exercise the GHL signals with nobody enrolled.

    Worth having its own mode: the booked-call check fails SAFE, so if the
    endpoint, the secret or the date format were wrong the sequence would simply
    never stop when she books a call, and the logs would say '0 cancelled' every
    five minutes exactly as they do when nothing is wrong. This makes that
    difference visible.
    """
    ids = booked_contact_ids()
    if ids is None:
        log.error('booked-call signal FAILED - see the warning above. '
                  'The sequence would not stop when she books.')
        raise SystemExit(1)
    log.info(f'booked-call signal OK - {len(ids)} contact(s) hold a consultation')
    for cid in sorted(ids):
        log.info(f'  {cid}')


def main():
    if '--probe' in sys.argv:
        probe()
        return
    conn = connect()
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM jhp_workflows WHERE name=%s LIMIT 1", (WF_NAME,))
            wf = cur.fetchone()
        if not wf:
            log.error(f'{WF_NAME} not found')
            return
        wid = wf['id']

        with conn.cursor() as cur:
            cur.execute("SELECT id, ghl_contact_id, contact_email, enrolled_at "
                        "FROM jhp_workflow_enrollments "
                        "WHERE workflow_id=%s AND status IN ('active','paused')", (wid,))
            open_enrs = cur.fetchall()
        log.info(f"{len(open_enrs)} open enrollment(s){' [dry-run]' if DRY else ''}")
        if not open_enrs:
            conn.commit()
            return

        booked = booked_contact_ids()
        stopped = 0
        for e in open_enrs:
            email = (e.get('contact_email') or '').strip()
            cid = e.get('ghl_contact_id')
            reason = None

            if booked is not None and cid and cid in booked:
                reason = 'booked_call'

            if reason is None and email:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM site_inquiries "
                                "WHERE lower(contact_email)=lower(%s) "
                                "AND is_test IS NOT TRUE LIMIT 1", (email,))
                    if cur.fetchone():
                        reason = 'inquired'

            if reason is None and email:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT 1 FROM psppv2_form_responses "
                        "WHERE lower(contact_email)=lower(%s) AND is_test IS NOT TRUE "
                        "  AND square_status LIKE 'completed%%' "
                        "UNION ALL SELECT 1 FROM promo_reservations "
                        "WHERE lower(contact_email)=lower(%s) AND is_test IS NOT TRUE "
                        "  AND status IN ('paid','booked') "
                        "UNION ALL SELECT 1 FROM treehouse_reservations "
                        "WHERE lower(contact_email)=lower(%s) AND is_test IS NOT TRUE "
                        "  AND status IN ('paid','booked','reserved') LIMIT 1",
                        (email, email, email))
                    if cur.fetchone():
                        reason = 'booked_paid'

            if reason is None and email:
                with conn.cursor() as cur:
                    cur.execute("SELECT raw FROM ghl_contacts WHERE lower(email)=lower(%s) "
                                "LIMIT 1", (email,))
                    row = cur.fetchone()
                raw = (row or {}).get('raw') or {}
                if isinstance(raw, str):
                    try:
                        raw = json.loads(raw)
                    except Exception:
                        raw = {}
                dnd = bool(raw.get('dnd'))
                settings = raw.get('dndSettings') or {}
                if isinstance(settings, dict):
                    for ch in ('Email', 'email'):
                        st = (settings.get(ch) or {})
                        if isinstance(st, dict) and str(st.get('status', '')).lower() == 'active':
                            dnd = True
                if dnd:
                    reason = 'unsubscribed'

            if reason is None and has_replied(cid, e['enrolled_at']):
                reason = 'replied'

            if reason:
                cancel(conn, e['id'], reason)
                stopped += 1

        if DRY:
            conn.rollback()
            log.info(f'[dry-run] {stopped} would be cancelled; nothing written')
            return
        conn.commit()
        log.info(f'done - {stopped} cancelled, {len(open_enrs) - stopped} still running')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
