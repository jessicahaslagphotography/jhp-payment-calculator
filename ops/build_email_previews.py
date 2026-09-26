#!/usr/bin/env python3
"""Render the eight 'Website Inquiry - 2027' emails into email_previews.

THE PREVIEW IS THE REAL RENDER. It goes through the same two functions a live
send does -- workflow_runner.render_text for the merge fields, then
email_actions._md_to_html for the markup and the branded wrapper -- against a
fake contact. A hand-built mock-up of these emails would be a drawing of the
truth on the day somebody drew it, which is exactly the mistake the Canva
Session Guide made. Change a message, run build-website-inquiry-2027, run this,
refresh the page.

Writes nothing but this table and sends nothing. The rows carry a fake lead's
details only, so the table is safe to attach read-only to the preview page.
"""
import os
import re
import sys
import logging
import psycopg2
import psycopg2.extras

sys.path.insert(0, '/home/scalogy/artifacts/workflow-runner')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'workflow-runner'))
import workflow_runner as wr          # noqa: E402
import email_actions as ea            # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_website_inquiry_2027 as b  # noqa: E402

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('build_email_previews')

# A fake lead. Deliberately Jessica's own name so she reads the emails as a
# client would see them addressed, and deliberately example.com so nothing here
# could ever be mistaken for a real address.
CTX = {
    'contact': {'id': 'preview', 'name': 'Jessica Haslag',
                'first_name': 'Jessica', 'email': 'jessica@example.com',
                'phone': '(573) 555-0100'},
    'enrollment': {'id': 'preview', 'context': {
        'guide_url': 'https://pages.scalogy.com/jhpboudoir1/session-guide/?n=Jessica',
        'calendar_url': ('https://api.leadconnectorhq.com/widget/booking/'
                         'mi2EqYRq4gGEbBJHe82b?first_name=Jessica&last_name=Haslag'
                         '&email=jessica%40example.com&phone=5735550100'),
    }},
    'session_date': None,
}

TIMING = {
    'website-inquiry-day0': 'Sent immediately',
    'website-inquiry-24h': '24 hours later',
    'website-inquiry-72h': '72 hours later',
    'website-inquiry-7d': '7 days later',
    'website-inquiry-14d': '14 days later',
    'website-inquiry-1mo': '1 month later',
    'website-inquiry-3mo': '3 months later',
    'website-inquiry-6mo': '6 months later',
}


def connect():
    return psycopg2.connect(
        dbname=os.environ['PGDATABASE'], user=os.environ['PGUSER'],
        host=os.environ['PGHOST'], cursor_factory=psycopg2.extras.RealDictCursor)


def main():
    b.check()
    conn = connect()
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM email_previews WHERE workflow_name=%s", (b.WF_NAME,))
            for i, s in enumerate(b.STEPS, start=1):
                raw = b.body_of(s)
                cfg = {'subject': s['subject'], 'body_md': raw, 'sms': s['sms']}
                subject = wr.render_text(s['subject'], CTX, cfg)
                body = wr.render_text(raw, CTX, cfg)
                sms = wr.render_text(s['sms'], CTX, cfg)
                html = ea._md_to_html(body)
                frame = b.FRAMES[s['target']][0]
                if 'alt="JHP Boudoir"' not in html:
                    raise SystemExit(f"{s['target']}: the logo header is missing "
                                     f"from the render")
                if f'media/{frame}' not in html:
                    raise SystemExit(f"{s['target']}: frame {frame[:8]} is not in "
                                     f"the render")
                cur.execute(
                    "INSERT INTO email_previews (workflow_name, step_position, target, "
                    " label, timing, subject, email_html, sms_text, sms_armed, frame) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (b.WF_NAME, i, s['target'], b.LABELS[s['target']],
                     TIMING[s['target']], subject, html, sms, b.SEND_SMS, frame))
                log.info(f"  {i}. {s['target']}: {len(html)} bytes of HTML, "
                         f"frame {frame[:8]}")
        conn.commit()
        log.info(f"done - {len(b.STEPS)} preview(s) written, "
                 f"SMS {'armed' if b.SEND_SMS else 'parked'}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
