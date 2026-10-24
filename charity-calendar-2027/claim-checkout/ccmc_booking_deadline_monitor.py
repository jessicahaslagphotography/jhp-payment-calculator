#!/usr/bin/env python3
"""ccmc-booking-deadline-monitor: enforces the 2027 Charity Calendar Model Call 7-day booking deadline.

Clone of emc-booking-deadline-monitor. Booking opens the moment she claims her
spot (BOTH plans: $99 in full -> 'paid', $1 hold -> 'reserved'), and
ccmc-reserve-charge stamps ccmc_reservations.booking_deadline = claim + 7 days.
Completion signal = a non-test psppv2_form_responses row for her email (or her
GHL contact id) submitted at/after the claim (same signal EMC uses).

For each claim with status IN ('paid','reserved'), booked_at IS NULL and
forfeited_at IS NULL:
  * BOOKED  -> status='booked', booked_at=NOW(); application status 'booked';
               tag GHL "Booked". Stops the clock.
  * FORFEIT (NOW > booking_deadline, still no booking) -> status='forfeited',
               forfeited_at=NOW(); application status 'forfeited'; tag GHL
               "Forfeited"; queue owner alert. No refund: the session fee is
               non-refundable. (Any $98 still pending on a $1 claim is closed
               out by ccmc-reserve-monitor at its expiry.)
  * REMINDER (once) -> inside the last 48 hours before booking_deadline, and only
               between 9am and 8pm Central, send ONE reminder email + SMS with
               her booking link and deadline; stamp reminder_sent_at.
  * else -> leave as-is.

No Square calls. Idempotent. is_test rows get the DB transitions (and
reminder_sent_at) but SKIP all GHL tags/messages + action_queue writes (log only)
so the monitor is safely testable.
"""
import os, hashlib, html
from datetime import datetime, timezone, timedelta
import psycopg2, psycopg2.extras

GHL_BASE = "https://services.leadconnectorhq.com"
GHL_VERSION = "2021-07-28"
JESSICA_EMAIL = "jessicahaslagphotography@gmail.com"
BOOKED_TAG = "Charity Calendar 2027 - Booked"
FORFEIT_TAG = "Charity Calendar 2027 - Forfeited (no booking)"
REMINDER_LEAD = timedelta(hours=48)
REMINDER_HOURS = (9, 20)          # local send window [start, end), America/Chicago
LOCAL_TZ = "America/Chicago"
LOGO_URL = "https://assets.cdn.filesafe.space/Pcnm8GVNMmWTY65qVOAp/media/0ac375b0-cf32-4ccb-aff6-526a5847ae0f.png"

_ghl = os.environ.get("GHL_API_KEY")


def _client():
    import httpx
    return httpx


def ghl_add_tags(cid, tags):
    if not (_ghl and cid):
        return
    try:
        httpx = _client()
        httpx.post(f"{GHL_BASE}/contacts/{cid}/tags",
                   headers={"Authorization": f"Bearer {_ghl}", "Version": GHL_VERSION,
                            "Content-Type": "application/json", "Accept": "application/json"},
                   json={"tags": tags}, timeout=20)
    except Exception as e:
        print(f"  ghl tag warning ({cid}): {type(e).__name__}: {e}")


def ghl_sms(cid, message):
    if not (_ghl and cid and message):
        return None, "missing token/contact/message"
    try:
        httpx = _client()
        r = httpx.post(f"{GHL_BASE}/conversations/messages",
                       headers={"Authorization": f"Bearer {_ghl}", "Version": GHL_VERSION,
                                "Content-Type": "application/json", "Accept": "application/json"},
                       json={"type": "SMS", "contactId": cid, "message": message}, timeout=20)
        if r.status_code >= 400:
            return None, f"GHL SMS HTTP {r.status_code}: {r.text[:200]}"
        return (r.json() or {}).get("messageId"), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def ghl_email(cid, subject, html_body):
    if not (_ghl and cid and html_body):
        return None, "missing token/contact/html"
    try:
        httpx = _client()
        r = httpx.post(f"{GHL_BASE}/conversations/messages",
                       headers={"Authorization": f"Bearer {_ghl}", "Version": GHL_VERSION,
                                "Content-Type": "application/json", "Accept": "application/json"},
                       json={"type": "Email", "contactId": cid, "subject": subject, "html": html_body}, timeout=25)
        if r.status_code >= 400:
            return None, f"GHL Email HTTP {r.status_code}: {r.text[:200]}"
        j = r.json() or {}
        return j.get("messageId") or j.get("emailMessageId") or j.get("id"), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def local(dt):
    try:
        from zoneinfo import ZoneInfo
        return dt.astimezone(ZoneInfo(LOCAL_TZ))
    except Exception:
        return None


def fmt_deadline(dt):
    d = local(dt) or dt
    return f"{d.strftime('%A, %B')} {d.day} at {d.strftime('%I:%M %p').lstrip('0')}"


def reminder_email_html(first, deadline, book):
    e = lambda s: html.escape(s or "", quote=True)
    greet = f"Hi {e(first)}," if (first and first != "there") else "Hi there,"
    return f"""<!doctype html><html><body style="margin:0;padding:0;background:#0c0a09;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">2 days left to book your Charity Calendar session.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0c0a09;"><tr><td align="center" style="padding:26px 14px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#12100c;border:1px solid #241c12;border-radius:14px;overflow:hidden;">
<tr><td align="center" style="padding:34px 40px 6px;"><img src="{LOGO_URL}" width="120" alt="JHP Boudoir" style="display:block;border:0;margin:0 auto 10px;width:120px;max-width:50%;height:auto;"><div style="font-family:Arial,Helvetica,sans-serif;font-size:11px;letter-spacing:3px;color:#c8a35a;text-transform:uppercase;">JHP Boudoir &middot; 2027 Charity Calendar</div></td></tr>
<tr><td align="center" style="padding:14px 40px 0;"><div style="font-family:Arial,Helvetica,sans-serif;font-size:12px;letter-spacing:4px;color:#c8a35a;text-transform:uppercase;">2 days left to book</div><h1 style="font-family:Georgia,'Cormorant Garamond',serif;font-weight:normal;font-size:40px;line-height:1.1;color:#f4eee2;margin:12px 0 6px;">Don&rsquo;t Lose Your Spot</h1></td></tr>
<tr><td style="padding:14px 40px 0;font-family:Arial,Helvetica,sans-serif;font-size:16px;line-height:1.7;color:#cfc6b6;"><p style="margin:0 0 14px;">{greet}</p><p style="margin:0 0 14px;">Your Charity Calendar spot is claimed &mdash; the last step is choosing your package and session date. Please book by <strong style="color:#c8a35a;">{e(deadline)}</strong> (Central), or your spot is forfeited without refund.</p><p style="margin:0 0 14px;">It only takes a few minutes.</p></td></tr>
<tr><td align="center" style="padding:16px 40px 6px;"><a href="{e(book)}" style="display:inline-block;background:#c8a35a;color:#0c0a09;font-family:Arial,Helvetica,sans-serif;font-size:14px;font-weight:bold;letter-spacing:1px;text-decoration:none;padding:15px 30px;border-radius:6px;">Book your session</a></td></tr>
<tr><td style="padding:22px 40px 32px;font-family:Georgia,serif;font-size:16px;color:#c8a35a;">Xo, Jess</td></tr>
<tr><td style="padding:20px 40px 30px;background:#0a0807;font-family:Arial,Helvetica,sans-serif;font-size:11.5px;line-height:1.6;color:#7d7466;">Your $99 session fee is non-refundable. Sessions held October 2026 &ndash; October 2027 are eligible for the 2027 Charity Calendar; sessions through March 2028 receive the same discounted rate but are not included in the calendar. Calendar participation is optional.<br><br>JHP Boudoir &middot; Jefferson City, MO</td></tr>
</table></td></tr></table></body></html>"""


def reminder_sms(first, deadline, book):
    first = first or "there"
    return (f"Hi {first}! It's Jessica w/ JHP Boudoir. Just 2 days left to book your Charity Calendar "
            f"session — please choose your package & date by {deadline} or your spot is forfeited: {book} Xo, Jess")


def _status(cur, token, status):
    if not token:
        return
    cur.execute(
        "UPDATE ccmc_reservation_status SET status=%s, updated_at=NOW() WHERE token_hash=%s",
        (status, hashlib.sha256(token.encode("utf-8")).hexdigest()))


def _app_status(cur, app_id, status, released=False):
    if not app_id:
        return
    cur.execute(
        "UPDATE charity_calendar_applications SET status=%s"
        + (", released_at=NOW()" if released else "")
        + " WHERE id=%s AND status='claimed'",
        (status, app_id))


def queue_note(cur, subject, message):
    try:
        cur.execute(
            "INSERT INTO action_queue (action, email, subject, message, status, created_at) "
            "VALUES (%s,%s,%s,%s,'pending', NOW())",
            ("ccmc_booking_forfeit", JESSICA_EMAIL, subject, message))
    except Exception as e:
        print(f"  queue_note warning: {type(e).__name__}: {e}")


def connect():
    return psycopg2.connect(dbname=os.environ["PGDATABASE"], user=os.environ["PGUSER"],
                            host=os.environ["PGHOST"], cursor_factory=psycopg2.extras.RealDictCursor)


def main():
    now = datetime.now(timezone.utc)
    lnow = local(now)
    in_send_window = lnow is not None and REMINDER_HOURS[0] <= lnow.hour < REMINDER_HOURS[1]
    conn = connect()
    conn.autocommit = False
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT * FROM ccmc_reservations "
            "WHERE status IN ('paid','reserved') AND booked_at IS NULL AND forfeited_at IS NULL "
            "AND booking_deadline IS NOT NULL ORDER BY id")
        rows = cur.fetchall()
        print(f"{len(rows)} claim(s) awaiting booking to check (reminder window open: {in_send_window})")
        booked = forfeited = reminded = waiting = 0
        for r in rows:
            rid = r["id"]
            is_test = bool(r.get("is_test"))
            email = r.get("contact_email")
            cid = r.get("ghl_contact_id")
            since = r.get("reserved_at") or r.get("created_at")
            deadline = r.get("booking_deadline")
            who = r.get("contact_name") or email or f"reservation {rid}"
            first = (r.get("contact_name") or "").split(" ")[0] if r.get("contact_name") else "there"
            cur.execute("SAVEPOINT sp")
            try:
                # --- BOOKED check: non-test PSPP v2 booking for her email / GHL contact at/after the claim ---
                is_booked = False
                if email or cid:
                    cur.execute(
                        "SELECT 1 FROM psppv2_form_responses "
                        "WHERE is_test=false AND submitted_at >= %s "
                        "AND ((%s <> '' AND lower(contact_email)=lower(%s)) "
                        "     OR (%s <> '' AND ghl_contact_id=%s)) LIMIT 1",
                        (since, email or "", email or "", cid or "", cid or ""))
                    is_booked = cur.fetchone() is not None

                if is_booked:
                    cur.execute("UPDATE ccmc_reservations SET status='booked', booked_at=NOW() WHERE id=%s", (rid,))
                    _status(cur, r.get("client_token"), "booked")
                    _app_status(cur, r.get("application_id"), "booked")
                    if is_test:
                        print(f"  BOOKED {rid} ({who}) [is_test] -> skipped GHL tag")
                    else:
                        ghl_add_tags(cid, [BOOKED_TAG])
                        print(f"  BOOKED {rid} ({who}) -> tagged GHL")
                    cur.execute("RELEASE SAVEPOINT sp")
                    booked += 1
                    continue

                # --- FORFEIT check: past the 7-day window, still no booking ---
                if now > deadline:
                    cur.execute("UPDATE ccmc_reservations SET status='forfeited', forfeited_at=NOW() WHERE id=%s", (rid,))
                    _status(cur, r.get("client_token"), "forfeited")
                    _app_status(cur, r.get("application_id"), "forfeited", released=True)
                    if is_test:
                        print(f"  FORFEIT {rid} ({who}) [is_test] -> skipped GHL tag + owner alert")
                    else:
                        ghl_add_tags(cid, [FORFEIT_TAG])
                        bal_note = ""
                        if r.get("plan") == "deposit" and r.get("paid_at") is None:
                            bal_note = (f" They claimed with $1; their $98 balance (due {r.get('balance_due_date')}) "
                                        f"has not cleared yet — the Square invoice is left as-is and "
                                        f"ccmc-reserve-monitor cancels it if it is still unpaid at expiry.")
                        queue_note(
                            cur,
                            "Charity Calendar spot forfeited — no booking in 7 days",
                            f"{who} claimed a 2027 Charity Calendar Model Call spot but did not choose a package "
                            f"and session date within 7 days (deadline {fmt_deadline(deadline)} Central). Their "
                            f"spot has been released and is now forfeited. No refund is due — the session fee is "
                            f"non-refundable.{bal_note} Reservation {rid}.")
                        print(f"  FORFEIT {rid} ({who}) -> tagged GHL + queued owner alert")
                    cur.execute("RELEASE SAVEPOINT sp")
                    forfeited += 1
                    continue

                # --- ONE reminder ~48h before the deadline (daytime only) ---
                if (r.get("reminder_sent_at") is None and now >= deadline - REMINDER_LEAD
                        and in_send_window):
                    dl = fmt_deadline(deadline)
                    book = r.get("next_url")
                    if is_test:
                        print(f"  REMIND {rid} ({who}) [is_test] -> skipped GHL send")
                    elif not (cid and book):
                        print(f"  REMIND {rid} ({who}) -> NOT sent (ghl_contact_id={bool(cid)} next_url={bool(book)})")
                    else:
                        sid, serr = ghl_sms(cid, reminder_sms(first, dl, book))
                        eid, eerr = ghl_email(cid, "2 days left to book your Charity Calendar session ✦",
                                              reminder_email_html(first, dl, book))
                        print(f"  REMIND {rid} ({who}): sms={sid or serr} email={eid or eerr}")
                    cur.execute("UPDATE ccmc_reservations SET reminder_sent_at=NOW() WHERE id=%s", (rid,))
                    cur.execute("RELEASE SAVEPOINT sp")
                    reminded += 1
                    continue

                # --- within window, not yet booked ---
                cur.execute("RELEASE SAVEPOINT sp")
                waiting += 1
                print(f"  WAITING {rid} ({who}) -> booking window open until {fmt_deadline(deadline)}")
            except psycopg2.Error as e:
                cur.execute("ROLLBACK TO SAVEPOINT sp")
                print(f"  row {rid} failed, skipped: {e}")
        conn.commit()
        print(f"done - {booked} booked, {forfeited} forfeited, {reminded} reminded, {waiting} still waiting")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
