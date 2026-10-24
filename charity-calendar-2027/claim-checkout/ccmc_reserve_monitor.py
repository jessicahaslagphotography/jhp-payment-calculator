#!/usr/bin/env python3
"""ccmc-reserve-monitor: watches the $98 balance invoice of 2027 Charity Calendar Model Call
claims made on the $1 plan. Runs every 15 min. Clone of emc-reserve-monitor.

Unlike EMC, booking opens the moment she claims (both plans), so a $1 claim can
already be 'booked' (or 'forfeited') while its $98 is still pending. This monitor
therefore tracks the BALANCE separately from the claim status: it looks at every
non-test deposit claim whose balance is still open
(plan='deposit', paid_at IS NULL, balance_cancelled_at IS NULL,
 status IN ('reserved','booked','forfeited')).

  * $98 invoice PAID -> paid_at=NOW(); a 'reserved' claim becomes 'paid'
    (booked/forfeited keep their status); tag GHL "Charity Calendar 2027 - Paid";
    a short "balance received" SMS + email (NO booking link — she already has it)
    unless the claim was forfeited; owner alert. Idempotent.
  * Past expires_at (balance_date + 2-day grace) and still unpaid:
      - 'reserved'  -> cancel the invoice, status 'released', application
                       'released' + released_at, tag GHL Released, owner alert.
      - 'booked'    -> NOT released (she's booked): owner alert once
                       (balance_alerted_at), invoice left open for Jessica.
      - 'forfeited' -> cancel the invoice (the spot is already gone), owner alert.

Writes to Square only on expiry (invoice cancel). Everything else is DB + GHL.
Also prunes stale non-claim rows (ready/invalid/expired/claimed/error, >2 days)
from ccmc_reservation_status, which the claim page reads in full.
"""
import os, hashlib, html
from datetime import datetime, timezone
import psycopg2, psycopg2.extras

SQUARE_VERSION = "2025-04-16"
# ---- Square environment — SINGLE SWITCH. Must match ccmc_reserve_charge.py's SQUARE_ENV
# and the claim page template. 'production' = real money. ----
SQUARE_ENV = "production"
if SQUARE_ENV == "production":
    SQUARE_BASE = "https://connect.squareup.com"
    _SQ_TOKEN_ENV = "SQUARE_ACCESS_TOKEN"
else:
    SQUARE_BASE = "https://connect.squareupsandbox.com"
    _SQ_TOKEN_ENV = "SQUARE_SANDBOX_ACCESS_TOKEN"
GHL_BASE = "https://services.leadconnectorhq.com"
GHL_VERSION = "2021-07-28"
JESSICA_EMAIL = "jessicahaslagphotography@gmail.com"
PAID_TAG = "Charity Calendar 2027 - Paid"
RELEASED_TAG = "Charity Calendar 2027 - Released (balance unpaid)"
LOGO_URL = "https://assets.cdn.filesafe.space/Pcnm8GVNMmWTY65qVOAp/media/0ac375b0-cf32-4ccb-aff6-526a5847ae0f.png"
LOCAL_TZ = "America/Chicago"

_sq = os.environ.get(_SQ_TOKEN_ENV)
_ghl = os.environ.get("GHL_API_KEY")


def _client():
    import httpx
    return httpx


def sq_get(path):
    httpx = _client()
    r = httpx.get(f"{SQUARE_BASE}{path}", headers={
        "Square-Version": SQUARE_VERSION, "Authorization": f"Bearer {_sq}",
        "Accept": "application/json"}, timeout=30)
    try:
        return r.status_code < 400, r.json()
    except Exception:
        return False, {}


def sq_post(path, body):
    httpx = _client()
    r = httpx.post(f"{SQUARE_BASE}{path}", headers={
        "Square-Version": SQUARE_VERSION, "Authorization": f"Bearer {_sq}",
        "Content-Type": "application/json", "Accept": "application/json"},
        json=body, timeout=30)
    try:
        return r.status_code < 400, r.json()
    except Exception:
        return False, {}


def invoice_status(inv_id):
    if not (inv_id and _sq):
        return None, None
    ok, data = sq_get(f"/v2/invoices/{inv_id}")
    if not ok:
        return None, None
    inv = data.get("invoice") or {}
    return inv.get("status"), inv.get("version")


def cancel_invoice(inv_id):
    """Cancel an open invoice. Returns True if it is cancelled (now or already)."""
    st, ver = invoice_status(inv_id)
    if st == "CANCELED":
        return True
    if st in (None, "PAID", "REFUNDED", "PARTIALLY_REFUNDED") or ver is None:
        return False
    ok, _ = sq_post(f"/v2/invoices/{inv_id}/cancel", {"version": ver})
    return ok


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


def fmt_deadline(dt):
    if dt is None:
        return None
    try:
        from zoneinfo import ZoneInfo
        dt = dt.astimezone(ZoneInfo(LOCAL_TZ))
    except Exception:
        pass
    return f"{dt.strftime('%A, %B')} {dt.day} at {dt.strftime('%I:%M %p').lstrip('0')}"


def balance_email_html(first, booked, deadline):
    e = lambda s: html.escape(s or "", quote=True)
    greet = f"Thank you, {e(first)}!" if (first and first != "there") else "Thank you!"
    if booked:
        nxt = "You&rsquo;re all booked &mdash; there&rsquo;s nothing else you need to do right now."
    elif deadline:
        nxt = (f"Just a reminder: please choose your package and session date by "
               f"<strong style=\"color:#c8a35a;\">{e(deadline)}</strong> (Central) using the booking link "
               f"in your confirmation email or text.")
    else:
        nxt = "Just a reminder to book your session using the link in your confirmation email or text."
    return f"""<!doctype html><html><body style="margin:0;padding:0;background:#0c0a09;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">Your $98 balance cleared — your $99 session fee is paid in full.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0c0a09;"><tr><td align="center" style="padding:26px 14px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#12100c;border:1px solid #241c12;border-radius:14px;overflow:hidden;">
<tr><td align="center" style="padding:34px 40px 6px;"><img src="{LOGO_URL}" width="120" alt="JHP Boudoir" style="display:block;border:0;margin:0 auto 10px;width:120px;max-width:50%;height:auto;"><div style="font-family:Arial,Helvetica,sans-serif;font-size:11px;letter-spacing:3px;color:#c8a35a;text-transform:uppercase;">JHP Boudoir &middot; 2027 Charity Calendar</div></td></tr>
<tr><td align="center" style="padding:14px 40px 0;"><div style="font-family:Arial,Helvetica,sans-serif;font-size:12px;letter-spacing:4px;color:#c8a35a;text-transform:uppercase;">Session fee paid in full</div><h1 style="font-family:Georgia,'Cormorant Garamond',serif;font-weight:normal;font-size:40px;line-height:1.1;color:#f4eee2;margin:12px 0 6px;">Balance Received</h1></td></tr>
<tr><td style="padding:14px 40px 0;font-family:Arial,Helvetica,sans-serif;font-size:16px;line-height:1.7;color:#cfc6b6;"><p style="margin:0 0 14px;">{greet}</p><p style="margin:0 0 14px;">Your <strong style="color:#f4eee2;">$98 balance just cleared</strong> &mdash; your $99 Charity Calendar session fee is paid in full.</p><p style="margin:0 0 14px;">{nxt}</p></td></tr>
<tr><td style="padding:12px 40px 32px;font-family:Georgia,serif;font-size:16px;color:#c8a35a;">Xo, Jess</td></tr>
<tr><td style="padding:20px 40px 30px;background:#0a0807;font-family:Arial,Helvetica,sans-serif;font-size:11.5px;line-height:1.6;color:#7d7466;">Your $99 session fee is non-refundable. You have 7 days from claiming your spot to choose your package and session date, or your spot is forfeited without refund.<br><br>JHP Boudoir &middot; Jefferson City, MO</td></tr>
</table></td></tr></table></body></html>"""


def balance_sms(first, booked, deadline):
    first = first or "there"
    tail = ("You're all booked — see you soon!" if booked
            else (f"Reminder: choose your package & session date by {deadline} using the link we sent you."
                  if deadline else "Reminder: book your session using the link we sent you."))
    return (f"Hi {first}! It's Jessica w/ JHP Boudoir. Your $98 balance cleared — your Charity Calendar "
            f"session fee is paid in full! {tail} Xo, Jess")


def _status(cur, token, status):
    if not token:
        return
    cur.execute(
        "UPDATE ccmc_reservation_status SET status=%s, updated_at=NOW() WHERE token_hash=%s",
        (status, hashlib.sha256(token.encode("utf-8")).hexdigest()))


def queue_note(cur, subject, message):
    try:
        cur.execute(
            "INSERT INTO action_queue (action, email, subject, message, status, created_at) "
            "VALUES (%s,%s,%s,%s,'pending', NOW())",
            ("ccmc_reservation_alert", JESSICA_EMAIL, subject, message))
    except Exception as e:
        print(f"  queue_note warning: {type(e).__name__}: {e}")


def connect():
    return psycopg2.connect(dbname=os.environ["PGDATABASE"], user=os.environ["PGUSER"],
                            host=os.environ["PGHOST"], cursor_factory=psycopg2.extras.RealDictCursor)


def main():
    if not _sq:
        print(f"missing {_SQ_TOKEN_ENV}; nothing to check")
        return
    now = datetime.now(timezone.utc)
    conn = connect()
    conn.autocommit = False
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT * FROM ccmc_reservations "
            "WHERE plan='deposit' AND paid_at IS NULL AND balance_cancelled_at IS NULL "
            "AND status IN ('reserved','booked','forfeited') AND is_test=false "
            "AND square_invoice_id IS NOT NULL ORDER BY id")
        rows = cur.fetchall()
        print(f"{len(rows)} open $98 balance(s) to check")
        paid = released = alerted = 0
        for r in rows:
            rid = r["id"]
            st = r["status"]
            token = r.get("client_token")
            cid = r.get("ghl_contact_id")
            who = r.get("contact_name") or r.get("contact_email") or f"reservation {rid}"
            first = (r.get("contact_name") or "").split(" ")[0] if r.get("contact_name") else "there"
            inv_id = r.get("square_invoice_id")
            cur.execute("SAVEPOINT sp")
            try:
                inv_status, _ = invoice_status(inv_id)

                # --- balance paid ---
                if inv_status == "PAID":
                    new_st = "paid" if st == "reserved" else st
                    cur.execute("UPDATE ccmc_reservations SET status=%s, paid_at=NOW() WHERE id=%s", (new_st, rid))
                    if new_st != st:
                        _status(cur, token, new_st)
                    ghl_add_tags(cid, [PAID_TAG])
                    sid = eid = None
                    serr = eerr = "skipped (forfeited)"
                    if st != "forfeited":
                        booked = (st == "booked")
                        dl = fmt_deadline(r.get("booking_deadline"))
                        sid, serr = ghl_sms(cid, balance_sms(first, booked, dl))
                        eid, eerr = ghl_email(cid, "Your $98 balance cleared — session fee paid in full ✦",
                                              balance_email_html(first, booked, dl))
                    queue_note(cur, "Charity Calendar session fee paid in full",
                               f"{who} paid their $98 balance — the $99 Charity Calendar session fee is now paid "
                               f"in full (claim status: {new_st}). Reservation {rid}.")
                    cur.execute("RELEASE SAVEPOINT sp")
                    paid += 1
                    print(f"  PAID {rid} ({st}->{new_st}): sms={sid or serr} email={eid or eerr}")
                    continue

                exp = r.get("expires_at")
                if not (exp and now > exp):
                    cur.execute("RELEASE SAVEPOINT sp")
                    continue

                # --- expired unpaid --- Safety re-check so we NEVER release a client whose $98 just cleared.
                inv_status, _ = invoice_status(inv_id)
                if inv_status == "PAID":
                    cur.execute("RELEASE SAVEPOINT sp")
                    print(f"  {rid}: balance cleared at expiry — will record next run")
                    continue
                if inv_status is None:
                    # Couldn't read the invoice (Square hiccup): never release blind — retry next run.
                    cur.execute("RELEASE SAVEPOINT sp")
                    print(f"  {rid}: expired but invoice {inv_id} unreadable — retry next run")
                    continue

                if st == "reserved":
                    cancelled = cancel_invoice(inv_id)
                    cur.execute("UPDATE ccmc_reservations SET status='released', released_at=NOW(), "
                                "balance_cancelled_at=CASE WHEN %s THEN NOW() ELSE balance_cancelled_at END "
                                "WHERE id=%s", (cancelled, rid))
                    _status(cur, token, "released")
                    if r.get("application_id"):
                        cur.execute("UPDATE charity_calendar_applications SET status='released', released_at=NOW() "
                                    "WHERE id=%s AND status='claimed'", (r["application_id"],))
                    ghl_add_tags(cid, [RELEASED_TAG])
                    queue_note(cur, "Charity Calendar claim released — $98 unpaid",
                               f"{who} did not pay their $98 balance (due {r.get('balance_due_date')}) and had not "
                               f"booked. Their Charity Calendar spot has been released and the balance invoice "
                               f"{'cancelled' if cancelled else 'could NOT be cancelled — please cancel it in Square'}. "
                               f"Reservation {rid}.")
                    released += 1
                    print(f"  RELEASED {rid}: expired unpaid (invoice cancelled={cancelled})")
                elif st == "booked":
                    if r.get("balance_alerted_at") is None:
                        cur.execute("UPDATE ccmc_reservations SET balance_alerted_at=NOW() WHERE id=%s", (rid,))
                        queue_note(cur, "Charity Calendar: booked client's $98 balance is unpaid",
                                   f"{who} has booked their session, but the automatic $98 balance charge (due "
                                   f"{r.get('balance_due_date')}) has not gone through. Nothing was released or "
                                   f"cancelled — the Square invoice {inv_id} is still open. Please follow up with them. "
                                   f"Reservation {rid}.")
                        alerted += 1
                        print(f"  ALERT {rid}: booked but $98 unpaid")
                else:  # forfeited
                    cancelled = cancel_invoice(inv_id)
                    if cancelled:
                        cur.execute("UPDATE ccmc_reservations SET balance_cancelled_at=NOW() WHERE id=%s", (rid,))
                    if r.get("balance_alerted_at") is None:
                        cur.execute("UPDATE ccmc_reservations SET balance_alerted_at=NOW() WHERE id=%s", (rid,))
                        queue_note(cur, "Charity Calendar: forfeited claim's $98 balance closed",
                                   f"{who} forfeited their Charity Calendar spot (no booking within 7 days) and their "
                                   f"$98 balance never cleared. The balance invoice was "
                                   f"{'cancelled' if cancelled else 'NOT cancelled — please cancel it in Square'}. "
                                   f"Reservation {rid}.")
                    print(f"  CLOSED {rid}: forfeited + $98 unpaid (invoice cancelled={cancelled})")
                cur.execute("RELEASE SAVEPOINT sp")
            except psycopg2.Error as e:
                cur.execute("ROLLBACK TO SAVEPOINT sp")
                print(f"  row {rid} failed, skipped: {e}")
        # Housekeeping: every page load writes a status row (invite check). The page reads the
        # whole table (?limit=500), so prune stale non-claim rows to keep it small.
        cur.execute("DELETE FROM ccmc_reservation_status "
                    "WHERE status IN ('ready','invalid','expired','claimed','error') "
                    "AND updated_at < NOW() - interval '2 days'")
        print(f"pruned {cur.rowcount} stale status row(s)")
        conn.commit()
        print(f"done - {paid} paid, {released} released, {alerted} booked-but-unpaid alerts")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
