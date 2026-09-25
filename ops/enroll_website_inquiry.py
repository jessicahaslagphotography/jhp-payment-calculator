#!/usr/bin/env python3
"""Enroll website contact-form leads into the 'Website Inquiry - 2027' sequence.

Polls site_leads -- the table the /contact Session Guide form writes through
webhook site-lead-submit -> workflow site-leads-ingest -- and enrolls each new
non-test lead at step 1 with next_action_at=NOW(), so the welcome email goes out
on the very next jhp-workflow-runner pass (within about five minutes of her
pressing the button). Every later delay is measured from enrolled_at, so the
whole six-month cadence is anchored to the moment she inquired.

Stamped into enrollment.context, which the runner exposes as merge fields:
  guide_url     -> /session-guide, carrying ?n=<First> so the page greets her
  calendar_url  -> the Boudoir Consultation Call calendar, prefilled with the
                   four fields she already typed
  site_lead_id  -> the dedupe key, so one lead is never enrolled twice

WHY ?n= IS VALIDATED HERE TOO. The guide validates the parameter itself against
^\\p{L}[\\p{L}'-]{1,23}$ and falls back to its default copy if it fails, so a
bad value is harmless -- but sending a URL we know the page will reject is
sloppy, and a name with a space or a digit in it means the row is probably not
a first name at all. When it does not validate we send the guide unadorned.

Robustness, mirroring ops/enroll_promo_inquiry.py:
  - artifacts baseline (website-inquiry/state.json). The FIRST RUN baselines to
    NOW() and enrolls nobody, so the leads already sitting in site_leads are not
    mailed a welcome six months late.
  - context.site_lead_id guards against double enrollment.
  - one active/paused enrollment per email per workflow.
  - anyone who has already paid or booked is skipped -- she is a client now.
  - each lead runs inside its own SAVEPOINT, so one bad row cannot stop the rest.
  - --dry-run reports what it would do and writes nothing.
"""
import os
import re
import sys
import json
import logging
from datetime import datetime
from urllib.parse import quote
import psycopg2
import psycopg2.extras

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('enroll_website_inquiry')

STATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                          'website-inquiry', 'state.json')
WF_NAME = 'website_inquiry_2027'
WF_DISPLAY = 'Website Inquiry - 2027'

GUIDE_URL = 'https://pages.scalogy.com/jhpboudoir1/session-guide/'
CALENDAR_URL = 'https://api.leadconnectorhq.com/widget/booking/mi2EqYRq4gGEbBJHe82b'

# The same shape the guide page accepts: a letter, then 1-23 more letters,
# apostrophes or hyphens. Python's re has no \p{L}, so this is the ASCII-plus-
# accents approximation; anything else falls back to the unadorned guide link.
FIRST_NAME_OK = re.compile(r"^[^\W\d_](?:[^\W\d_]|['-]){1,23}$", re.UNICODE)

DRY = '--dry-run' in sys.argv


def connect():
    return psycopg2.connect(
        dbname=os.environ['PGDATABASE'], user=os.environ['PGUSER'],
        host=os.environ['PGHOST'], cursor_factory=psycopg2.extras.RealDictCursor)


def load_baseline():
    try:
        with open(STATE_PATH) as f:
            return json.load(f).get('baseline')
    except Exception:
        return None


def save_baseline(ts_iso):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, 'w') as f:
        json.dump({'baseline': ts_iso}, f)


def _sp(conn, sql):
    with conn.cursor() as cur:
        cur.execute(sql)


def split_name(full):
    parts = (full or '').strip().split()
    if not parts:
        return '', ''
    return parts[0], ' '.join(parts[1:])


def guide_url_for(first):
    if first and FIRST_NAME_OK.match(first):
        return GUIDE_URL + '?n=' + quote(first)
    return GUIDE_URL


def calendar_url_for(first, last, email, phone):
    parts = []
    for k, v in (('first_name', first), ('last_name', last),
                 ('email', email), ('phone', phone)):
        if (v or '').strip():
            parts.append(k + '=' + quote(v.strip()))
    return CALENDAR_URL + ('?' + '&'.join(parts) if parts else '')


def main():
    conn = connect()
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM jhp_workflows WHERE name=%s OR display_name=%s LIMIT 1",
                        (WF_NAME, WF_DISPLAY))
            wf = cur.fetchone()
        if not wf:
            log.error(f"{WF_DISPLAY} not found - run build-website-inquiry-2027 first")
            return
        wid = wf['id']

        with conn.cursor() as cur:
            cur.execute("SELECT MIN(position) AS p FROM jhp_workflow_steps WHERE workflow_id=%s",
                        (wid,))
            mn = cur.fetchone()
        if not mn or mn['p'] is None:
            log.error("workflow has no steps - refusing to enrol into an empty sequence")
            return
        start_pos = mn['p']

        baseline = load_baseline()
        if baseline is None:
            with conn.cursor() as cur:
                cur.execute("SELECT NOW() AS w")
                w = cur.fetchone()['w']
            if DRY:
                log.info(f"[dry-run] would baseline at {w.isoformat()} and enrol nobody")
                return
            save_baseline(w.isoformat())
            log.info(f"first run - baseline {w.isoformat()} (existing leads are NOT backfilled)")
            conn.commit()
            return
        bl = datetime.fromisoformat(baseline)

        with conn.cursor() as cur:
            cur.execute(
                "SELECT l.id, l.contact_name, l.contact_email, l.contact_phone, "
                "       l.ghl_contact_id, l.created_at "
                "FROM site_leads l "
                "WHERE l.is_test IS NOT TRUE AND COALESCE(l.contact_email,'') <> '' "
                "  AND l.ghl_contact_id IS NOT NULL AND l.created_at > %s "
                "  AND NOT EXISTS (SELECT 1 FROM jhp_workflow_enrollments e "
                "                  WHERE e.workflow_id = %s "
                "                    AND e.context->>'site_lead_id' = l.id::text) "
                # already a client -> she is in a booked flow, not a nurture
                "  AND NOT EXISTS (SELECT 1 FROM psppv2_form_responses p "
                "                  WHERE lower(p.contact_email) = lower(l.contact_email) "
                "                    AND p.is_test IS NOT TRUE "
                "                    AND p.square_status LIKE 'completed%%') "
                "ORDER BY l.created_at ASC", (bl, wid))
            rows = cur.fetchall()
        log.info(f"{len(rows)} website lead(s) to enrol{' [dry-run]' if DRY else ''}")

        enrolled = 0
        for r in rows:
            lid = str(r['id'])
            email = (r.get('contact_email') or '').strip()
            _sp(conn, "SAVEPOINT sp")
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM jhp_workflow_enrollments WHERE workflow_id=%s "
                                "AND lower(contact_email)=lower(%s) "
                                "AND status IN ('active','paused') LIMIT 1", (wid, email))
                    if cur.fetchone():
                        log.info(f"skip {email} - already has an active enrollment")
                        _sp(conn, "RELEASE SAVEPOINT sp")
                        continue

                first, last = split_name(r.get('contact_name'))
                ctx = {
                    'site_lead_id': lid,
                    'source': 'website-contact-form',
                    'guide_url': guide_url_for(first),
                    'calendar_url': calendar_url_for(first, last, email,
                                                     r.get('contact_phone')),
                }
                if DRY:
                    log.info(f"[dry-run] would enrol {email} at step {start_pos} "
                             f"guide={ctx['guide_url']}")
                    _sp(conn, "RELEASE SAVEPOINT sp")
                    enrolled += 1
                    continue
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO jhp_workflow_enrollments "
                        "(workflow_id, ghl_contact_id, contact_name, contact_email, status, "
                        " current_step_position, next_action_at, context, enrolled_by) "
                        "VALUES (%s,%s,%s,%s,'active',%s,NOW(),%s::jsonb,%s) RETURNING id",
                        (wid, r['ghl_contact_id'], r.get('contact_name'), email, start_pos,
                         json.dumps(ctx), 'enroll_website_inquiry'))
                    new = cur.fetchone()
                _sp(conn, "RELEASE SAVEPOINT sp")
                enrolled += 1
                log.info(f"enrolled {email} -> #{new['id']} (site_lead {lid})")
            except psycopg2.Error as e:
                _sp(conn, "ROLLBACK TO SAVEPOINT sp")
                log.warning(f"lead {lid} ({email}) failed, skipped: {e}")

        if DRY:
            conn.rollback()
            log.info(f"[dry-run] {enrolled} would be enrolled; nothing written")
            return
        conn.commit()
        log.info(f"done - {enrolled} enrolled")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
