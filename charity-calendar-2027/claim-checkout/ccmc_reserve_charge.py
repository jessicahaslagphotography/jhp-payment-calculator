#!/usr/bin/env python3
"""ccmc-reserve-charge: the 2027 Charity Calendar Model Call "claim your spot" charger (LIVE production Square).

Clone of emc-reserve-charge, INVITE-GATED. Only an approved applicant holding a
personal invite link (charity_calendar_applications.invite_token, status
'invited', inside its 72-hour claim_deadline) can claim.

Two plans (the invitee picks on the ccmc-claim page):
  * plan="deposit"  -> $1 now + $98 BALANCE invoice auto-charged on a chosen
                       date within 14 days. status -> 'reserved'.
  * plan="full"     -> $99 charged now, no balance. status -> 'paid'.
  BOTH plans open booking immediately: booking_deadline = claim time + 7 days,
  and the confirmation SMS/email carries the prefilled PSPP booking link.

Two MODES on the same webhook (ccmc-reserve-pay, body on STDIN):
  * mode="check" -> no money. The page fires this on load with
                    {mode, client_token, invite_token}; we write the invite's
                    state (ready / invalid / expired / claimed) to
                    ccmc_reservation_status so the page can show the right
                    screen BEFORE she types her card.
  * mode="pay"   -> (default) {client_token, invite_token, sourceId,
                    verification_token, plan, balance_date, acknowledged,
                    is_test, user_agent}.

FLOW (pay)
  * Name/email/phone come ONLY from the application row (looked up by
    invite_token under a row lock), never from the body.
  * Amounts are SERVER-AUTHORITATIVE: $1 (100), $98 (9800), $99 (9900).
  * Reuses/creates the Square customer, VAULTS the card, charges, (deposit
    only) schedules the balance invoice, writes ccmc_reservations (PII) +
    ccmc_reservation_status (PII-free, page-polled), flips the application to
    'claimed', tags GHL, sends the confirmation SMS + email and queues an owner
    alert.
  * is_test is taken from the APPLICATION row (a public ?test=1 cannot claim a
    real invite for free). Test claims short-circuit BEFORE any Square/GHL call.
  * Dedupe on client_token; a different-token attempt for the same application
    (or email) while one is live / in flight is refused, so a double-submit or
    a second tab never double-charges.

PII-FREE STATUS TABLE: the page token can read every row of
ccmc_reservation_status, so rows are keyed by sha256(client_token) and the
prefilled booking link (name/email/phone) is stored only encrypted
(next_url_enc) under a key derived from the raw client_token, which only the
claimant's browser holds. See _enc_next_url() and the matching JS in
ccmc_claim.template.html.

Square environment is a SINGLE SWITCH (SQUARE_ENV below): 'production' charges real
cards (connect.squareup.com, prod location LPEFSHS0X4QPD, SQUARE_ACCESS_TOKEN);
'sandbox' uses test money. The claim page template must be set to the same env.
"""
import os, sys, re, json, base64, hashlib, hmac, html
from datetime import date, datetime, timedelta, timezone
import psycopg2, psycopg2.extras

MAX_BODY_BYTES = 20_000
DEPOSIT_CENTS = 100      # $1
BALANCE_CENTS = 9800     # $98
FULL_CENTS = 9900        # $99
CURRENCY = "USD"
MAX_WINDOW_DAYS = 14
BOOKING_WINDOW_DAYS = 7
INFLIGHT_GUARD_MINUTES = 10

SQUARE_VERSION = "2025-04-16"
# ---- Square environment — SINGLE SWITCH. Flip SQUARE_ENV to change base+location+token.
# The page template ccmc-claim has a matching APP_ID/LOCATION_ID/SDK-URL
# block that MUST be set to the same environment. ----
SQUARE_ENV = "production"
if SQUARE_ENV == "production":
    SQUARE_BASE = "https://connect.squareup.com"
    LOCATION_ID = "LPEFSHS0X4QPD"                      # LIVE prod location (Jessica Haslag Photography)
    _SQ_TOKEN_ENV = "SQUARE_ACCESS_TOKEN"
else:
    SQUARE_BASE = "https://connect.squareupsandbox.com"
    LOCATION_ID = "LPFHRECZXJ8EV"                      # SANDBOX location
    _SQ_TOKEN_ENV = "SQUARE_SANDBOX_ACCESS_TOKEN"

GHL_BASE = "https://services.leadconnectorhq.com"
GHL_VERSION = "2021-07-28"
CLAIMED_TAG = "Charity Calendar 2027 - Claimed"
PAID_TAG = "Charity Calendar 2027 - Paid"
GHL_SOURCE = "Charity Calendar 2027 claim"
JESSICA_EMAIL = "jessicahaslagphotography@gmail.com"
BOOKING_PAGE_URL = "https://pages.scalogy.com/jhpboudoir1/forms-pspp-2027-ccmc/"
# GHL-CDN copy of the JHP mark (email_actions.py: Drive-hosted logos break in many inboxes).
LOGO_URL = "https://assets.cdn.filesafe.space/Pcnm8GVNMmWTY65qVOAp/media/0ac375b0-cf32-4ccb-aff6-526a5847ae0f.png"
LOCAL_TZ = "America/Chicago"

_sq_token = os.environ.get(_SQ_TOKEN_ENV)
_ghl_token = os.environ.get("GHL_API_KEY")
_ghl_location = os.environ.get("GHL_LOCATION_ID") or "Pcnm8GVNMmWTY65qVOAp"

INVITE_RE = re.compile(r"[A-Za-z0-9_-]{16,128}")

# Friendly, PII-free page messages (shown via textContent).
MSG_INVALID = ("We couldn't find this invitation. Please use the personal link from your "
               "invitation email, or reach out and we'll help.")
MSG_EXPIRED = ("This invitation has expired. Invitations can be claimed for 72 hours — if you "
               "think this is a mistake, reach out and we'll help.")
MSG_CLOSED = ("This invitation is no longer active. If you think this is a mistake, reach out "
              "and we'll help.")
MSG_CLAIMED = "You've already claimed your spot — check your email and texts for your booking link."
MSG_BOOKED = "You've already claimed your spot and booked your session. We can't wait to see you!"
MSG_INFLIGHT = ("It looks like your claim is already going through — please check your email for "
                "confirmation. If you don't hear from us shortly, reach out and we'll help.")


def _read_webhook_body():
    raw = ""
    try:
        if not sys.stdin.isatty():
            raw = sys.stdin.read()
    except Exception:
        raw = ""
    if not (raw or "").strip():
        raw = os.environ.get("WEBHOOK_BODY") or os.environ.get("WEBHOOK_PAYLOAD") or ""
    if not (raw or "").strip():
        b64 = os.environ.get("WEBHOOK_RAW_BODY_BASE64")
        if b64:
            try:
                raw = base64.b64decode(b64).decode("utf-8", "replace")
            except Exception:
                raw = ""
    return (raw or "").strip()


def _e164(raw):
    d = re.sub(r"[^0-9]", "", raw or "")
    if len(d) == 10:
        return "+1" + d
    if len(d) == 11 and d.startswith("1"):
        return "+" + d
    return None


def _token_hash(token):
    """Row key of ccmc_reservation_status: lower-hex sha256 of the raw client_token."""
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def _enc_next_url(token, url):
    """Encrypt next_url so only the browser holding the raw client_token can read it.

    key       = sha256('ccmc-next-url|' + client_token)
    keystream = HMAC-SHA256(key, nonce16 || uint32_be(block_index)), 32 bytes per block
    output    = base64(nonce16 || plaintext XOR keystream)
    Mirrored by decNext() in ccmc_claim.template.html (WebCrypto).
    """
    if not (token and url):
        return None
    key = hashlib.sha256(("ccmc-next-url|" + token).encode("utf-8")).digest()
    nonce = os.urandom(16)
    pt = url.encode("utf-8")
    out = bytearray()
    for i in range(0, len(pt), 32):
        block = hmac.new(key, nonce + (i // 32).to_bytes(4, "big"), hashlib.sha256).digest()
        out += bytes(a ^ b for a, b in zip(pt[i:i + 32], block))
    return base64.b64encode(nonce + bytes(out)).decode("ascii")


def _sq(method, path, body=None, idem=None):
    import httpx
    if idem and method in ("POST", "PUT"):
        body = dict(body or {})
        body.setdefault("idempotency_key", idem[:45])
    r = httpx.request(
        method, f"{SQUARE_BASE}{path}",
        headers={"Square-Version": SQUARE_VERSION, "Authorization": f"Bearer {_sq_token}",
                 "Content-Type": "application/json", "Accept": "application/json"},
        json=body, timeout=30,
    )
    try:
        data = r.json()
    except Exception:
        data = {"_text": r.text}
    return r.status_code < 400, r.status_code, data


def _sq_err(data, fallback="That card could not be processed."):
    errs = (data or {}).get("errors") or []
    if errs:
        return errs[0].get("detail") or errs[0].get("code") or fallback
    return fallback


def _status(cur, token, status, card_error=None, receipt_url=None, balance_date=None,
            claim_deadline=None, next_url=None):
    """Upsert the page-polled, PII-free status row for this client_token."""
    if not token:
        return
    cur.execute(
        """
        INSERT INTO ccmc_reservation_status
            (token_hash, status, card_error, receipt_url, balance_due_date, claim_deadline, next_url_enc, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s, NOW())
        ON CONFLICT (token_hash) DO UPDATE SET
            status = EXCLUDED.status, card_error = EXCLUDED.card_error,
            receipt_url = EXCLUDED.receipt_url,
            balance_due_date = COALESCE(EXCLUDED.balance_due_date, ccmc_reservation_status.balance_due_date),
            claim_deadline = COALESCE(EXCLUDED.claim_deadline, ccmc_reservation_status.claim_deadline),
            next_url_enc = COALESCE(EXCLUDED.next_url_enc, ccmc_reservation_status.next_url_enc),
            updated_at = NOW()
        """,
        (_token_hash(token), status, card_error, receipt_url, balance_date, claim_deadline,
         _enc_next_url(token, next_url)),
    )


def _check_status(cur, token, status, card_error=None, claim_deadline=None, next_url=None):
    """Like _status, but never clobbers a row a pay run already owns (new / reserved / paid / booked),
    e.g. when the page is reloaded while a charge is in flight."""
    if not token:
        return
    cur.execute(
        """
        INSERT INTO ccmc_reservation_status
            (token_hash, status, card_error, claim_deadline, next_url_enc, updated_at)
        VALUES (%s,%s,%s,%s,%s, NOW())
        ON CONFLICT (token_hash) DO UPDATE SET
            status = EXCLUDED.status, card_error = EXCLUDED.card_error,
            claim_deadline = EXCLUDED.claim_deadline, next_url_enc = EXCLUDED.next_url_enc,
            updated_at = NOW()
        WHERE ccmc_reservation_status.status NOT IN ('new','reserved','paid','booked')
        """,
        (_token_hash(token), status, card_error, claim_deadline, _enc_next_url(token, next_url)),
    )


def _invite_state(app, now):
    """(state, message) for an application row: ready | invalid | expired | claimed."""
    if not app:
        return "invalid", MSG_INVALID
    st = (app.get("status") or "").strip().lower()
    if st == "invited":
        dl = app.get("claim_deadline")
        if dl is None:
            return "invalid", MSG_INVALID
        if now > dl:
            return "expired", MSG_EXPIRED
        return "ready", None
    if st == "claimed":
        return "claimed", MSG_CLAIMED
    if st == "booked":
        return "claimed", MSG_BOOKED
    return "expired", MSG_CLOSED


def _live_next_url(cur, app_id):
    """Prefilled booking link of this application's live (not yet booked) claim, if any."""
    cur.execute(
        "SELECT next_url FROM ccmc_reservations WHERE application_id=%s "
        "AND status IN ('reserved','paid') AND next_url IS NOT NULL ORDER BY id DESC LIMIT 1",
        (app_id,))
    r = cur.fetchone()
    return r["next_url"] if r else None


def _ghl_upsert(name, email, phone):
    """Best-effort GHL upsert WITHOUT tags (tags are added separately so the upsert can
    never overwrite the contact's existing application tags). Returns (contact_id, contact_dict, error)."""
    if not _ghl_token:
        return None, {}, "missing GHL_API_KEY"
    try:
        import httpx
    except Exception as e:
        return None, {}, f"httpx import failed: {e}"
    parts = (name or "").strip().split()
    body = {
        "locationId": _ghl_location,
        "firstName": parts[0] if parts else None,
        "lastName": " ".join(parts[1:]) if len(parts) > 1 else None,
        "email": email, "phone": _e164(phone),
        "source": GHL_SOURCE,
    }
    body = {k: v for k, v in body.items() if v}
    try:
        r = httpx.post(
            f"{GHL_BASE}/contacts/upsert",
            headers={"Authorization": f"Bearer {_ghl_token}", "Version": GHL_VERSION,
                     "Content-Type": "application/json", "Accept": "application/json"},
            json=body, timeout=20,
        )
        if r.status_code >= 400:
            return None, {}, f"GHL HTTP {r.status_code}: {r.text[:200]}"
        contact = (r.json() or {}).get("contact") or {}
        return contact.get("id"), contact, None
    except Exception as e:
        return None, {}, f"{type(e).__name__}: {e}"


def _ghl_add_tags(cid, tags):
    """Additive tag write (never removes existing tags). Returns error or None."""
    if not (_ghl_token and cid and tags):
        return "missing token/contact/tags"
    try:
        import httpx
        r = httpx.post(f"{GHL_BASE}/contacts/{cid}/tags",
                       headers={"Authorization": f"Bearer {_ghl_token}", "Version": GHL_VERSION,
                                "Content-Type": "application/json", "Accept": "application/json"},
                       json={"tags": tags}, timeout=20)
        if r.status_code >= 400:
            return f"GHL tags HTTP {r.status_code}: {r.text[:200]}"
        return None
    except Exception as e:
        return f"{type(e).__name__}: {e}"


def _mirror_ghl(cur, cid, contact, name, email, phone, tags):
    try:
        cur.execute("SAVEPOINT ghlm")
        cur.execute(
            """
            INSERT INTO ghl_contacts (ghl_id, email, name, phone, source, date_added, tags, match_reasons, raw, synced_at)
            VALUES (%s,%s,%s,%s,%s, NOW(), %s,%s,%s, NOW())
            ON CONFLICT (ghl_id) DO UPDATE SET
                email = COALESCE(EXCLUDED.email, ghl_contacts.email),
                name = COALESCE(EXCLUDED.name, ghl_contacts.name),
                phone = COALESCE(EXCLUDED.phone, ghl_contacts.phone),
                source = EXCLUDED.source, tags = EXCLUDED.tags,
                raw = EXCLUDED.raw, synced_at = NOW()
            """,
            (cid, contact.get("email") or email, contact.get("contactName") or name,
             contact.get("phone") or _e164(phone), GHL_SOURCE,
             (contact.get("tags") or []) + [t for t in tags if t not in (contact.get("tags") or [])],
             ["ccmc_claimed"], json.dumps(contact)),
        )
        cur.execute("RELEASE SAVEPOINT ghlm")
    except Exception as e:
        try:
            cur.execute("ROLLBACK TO SAVEPOINT ghlm")
        except Exception:
            pass
        print(f"ghl mirror warning: {type(e).__name__}: {e}")


def _ghl_sms(contact_id, message):
    """Best-effort confirmation SMS via GHL Conversations. Returns (message_id, error)."""
    if not (_ghl_token and contact_id and message):
        return None, "missing token/contact/message"
    try:
        import httpx
        r = httpx.post(f"{GHL_BASE}/conversations/messages",
                       headers={"Authorization": f"Bearer {_ghl_token}", "Version": GHL_VERSION,
                                "Content-Type": "application/json", "Accept": "application/json"},
                       json={"type": "SMS", "contactId": contact_id, "message": message}, timeout=20)
        if r.status_code >= 400:
            return None, f"GHL SMS HTTP {r.status_code}: {r.text[:200]}"
        return (r.json() or {}).get("messageId"), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def _ghl_email(contact_id, subject, html_body):
    """Best-effort branded email via GHL Conversations. Returns (message_id, error)."""
    if not (_ghl_token and contact_id and html_body):
        return None, "missing token/contact/html"
    try:
        import httpx
        r = httpx.post(f"{GHL_BASE}/conversations/messages",
                       headers={"Authorization": f"Bearer {_ghl_token}", "Version": GHL_VERSION,
                                "Content-Type": "application/json", "Accept": "application/json"},
                       json={"type": "Email", "contactId": contact_id, "subject": subject, "html": html_body}, timeout=25)
        if r.status_code >= 400:
            return None, f"GHL Email HTTP {r.status_code}: {r.text[:200]}"
        j = r.json() or {}
        return j.get("messageId") or j.get("emailMessageId") or j.get("id"), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def queue_note(cur, subject, message):
    """Owner alert -> action_queue (notify-via-ghl emails it to Jessica)."""
    try:
        cur.execute("SAVEPOINT qn")
        cur.execute(
            "INSERT INTO action_queue (action, email, subject, message, status, created_at) "
            "VALUES (%s,%s,%s,%s,'pending', NOW())",
            ("ccmc_reservation_alert", JESSICA_EMAIL, subject, message))
        cur.execute("RELEASE SAVEPOINT qn")
    except Exception as e:
        try:
            cur.execute("ROLLBACK TO SAVEPOINT qn")
        except Exception:
            pass
        print(f"  queue_note warning: {type(e).__name__}: {e}")


def _booking_url(name, email, phone, is_test):
    """CCMC PSPP booking link with contact prefill (redirect target + SMS/email link)."""
    from urllib.parse import urlencode
    q = {}
    if name:
        q["name"] = name
    if email:
        q["email"] = email
    if phone:
        q["phone"] = phone
    if is_test:
        q["test"] = "1"
    u = BOOKING_PAGE_URL
    if q:
        u += "?" + urlencode(q)
    return u


def _local(dt):
    try:
        from zoneinfo import ZoneInfo
        return dt.astimezone(ZoneInfo(LOCAL_TZ))
    except Exception:
        return dt


def _fmt_deadline(dt):
    """'Saturday, October 31 at 4:12 PM' (Central)."""
    if dt is None:
        return "7 days from today"
    d = _local(dt)
    return f"{d.strftime('%A, %B')} {d.day} at {d.strftime('%I:%M %p').lstrip('0')}"


def _fmt_day(d):
    return (d.strftime("%B ") + str(d.day)) if d else "your selected date"


def _claimed_email_html(first, plan, bal, deadline, book):
    e = lambda s: html.escape(s or "", quote=True)
    greet = f"You&rsquo;re in, {e(first)}!" if (first and first != "there") else "You&rsquo;re in!"
    if plan == "full":
        pay_line = ("Your <strong style=\"color:#f4eee2;\">$99 session fee is paid in full</strong> and your spot in the "
                    "2027 Charity Calendar Model Call is officially claimed.")
        bal_box = ""
    else:
        pay_line = ("Your <strong style=\"color:#f4eee2;\">$1 today is in</strong> and your spot in the "
                    "2027 Charity Calendar Model Call is officially claimed.")
        bal_box = f"""<tr><td style="padding:8px 40px 0;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#16110d;border:1px solid #2a2018;border-radius:10px;"><tr><td style="padding:16px 18px;font-family:Arial,Helvetica,sans-serif;"><div style="font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#8a8072;margin-bottom:5px;">Your $98 balance</div><div style="font-size:17px;color:#ece4d6;">Charges automatically on <strong style="color:#c8a35a;">{e(bal)}</strong></div><div style="font-size:13px;color:#a89e8d;margin-top:5px;">Nothing for you to do &mdash; it&rsquo;s on your card on file. You don&rsquo;t need to wait for it: book your session now.</div></td></tr></table></td></tr>"""
    return f"""<!doctype html><html><body style="margin:0;padding:0;background:#0c0a09;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">Your Charity Calendar spot is claimed — book your session within 7 days.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0c0a09;"><tr><td align="center" style="padding:26px 14px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#12100c;border:1px solid #241c12;border-radius:14px;overflow:hidden;">
<tr><td align="center" style="padding:34px 40px 6px;"><img src="{LOGO_URL}" width="120" alt="JHP Boudoir" style="display:block;border:0;margin:0 auto 10px;width:120px;max-width:50%;height:auto;"><div style="font-family:Arial,Helvetica,sans-serif;font-size:11px;letter-spacing:3px;color:#c8a35a;text-transform:uppercase;">JHP Boudoir &middot; 2027 Charity Calendar</div></td></tr>
<tr><td align="center" style="padding:14px 40px 0;"><div style="font-family:Arial,Helvetica,sans-serif;font-size:12px;letter-spacing:4px;color:#c8a35a;text-transform:uppercase;">Your spot is claimed</div><h1 style="font-family:Georgia,'Cormorant Garamond',serif;font-weight:normal;font-size:40px;line-height:1.1;color:#f4eee2;margin:12px 0 6px;">You&rsquo;re In</h1></td></tr>
<tr><td style="padding:14px 40px 0;font-family:Arial,Helvetica,sans-serif;font-size:16px;line-height:1.7;color:#cfc6b6;"><p style="margin:0 0 14px;">{greet}</p><p style="margin:0 0 14px;">{pay_line} There&rsquo;s one step left &mdash; book your session.</p></td></tr>
{bal_box}
<tr><td style="padding:14px 40px 0;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#1a1206;border:1px solid #6e4a2e;border-left:4px solid #c8a35a;border-radius:8px;"><tr><td style="padding:16px 18px;font-family:Arial,Helvetica,sans-serif;"><div style="font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#c8a35a;margin-bottom:5px;">Important &middot; 7 days to book</div><div style="font-size:15px;line-height:1.6;color:#f4eee2;">Please choose your package and session date by <strong style="color:#c8a35a;">{e(deadline)}</strong> (Central). If you haven&rsquo;t booked by then, your spot is forfeited without refund.</div></td></tr></table></td></tr>
<tr><td align="center" style="padding:24px 40px 6px;"><a href="{e(book)}" style="display:inline-block;background:#c8a35a;color:#0c0a09;font-family:Arial,Helvetica,sans-serif;font-size:14px;font-weight:bold;letter-spacing:1px;text-decoration:none;padding:15px 30px;border-radius:6px;">Book your session</a></td></tr>
<tr><td style="padding:26px 40px 0;font-family:Arial,Helvetica,sans-serif;"><div style="border-top:1px solid #241c12;padding-top:22px;"><div style="font-size:12px;letter-spacing:3px;text-transform:uppercase;color:#c8a35a;text-align:center;">Your model-call reward</div><div style="font-family:Georgia,serif;font-size:26px;color:#f4eee2;text-align:center;margin:8px 0 14px;">A $99 session fee + $500 off your package</div><p style="font-size:14.5px;line-height:1.65;color:#a89e8d;margin:0 0 8px;">Sessions held <strong style="color:#cfc6b6;">October 2026 &ndash; October 2027</strong> are eligible for the 2027 calendar. You can also book a session through <strong style="color:#cfc6b6;">March 2028</strong> at the same discounted rate &mdash; it just won&rsquo;t be in the calendar.</p><p style="font-size:14.5px;line-height:1.65;color:#a89e8d;margin:0;">Being in the calendar is completely optional &mdash; your images are always yours.</p></div></td></tr>
<tr><td style="padding:24px 40px 0;font-family:Arial,Helvetica,sans-serif;"><div style="border-top:1px solid #241c12;padding-top:22px;"><p style="font-size:14.5px;line-height:1.7;color:#cfc6b6;margin:0;"><em style="color:#e6ddcd;">A little note from me:</em> almost every woman who walks into my studio feels nervous &mdash; and leaves beaming. You&rsquo;re in the best of hands. Every pose is guided and the whole day is designed to help you relax and feel beautiful. All you have to do is show up.</p></div></td></tr>
<tr><td style="padding:20px 40px 32px;font-family:Georgia,serif;font-size:16px;color:#c8a35a;">Xo, Jess</td></tr>
<tr><td style="padding:20px 40px 30px;background:#0a0807;font-family:Arial,Helvetica,sans-serif;font-size:11.5px;line-height:1.6;color:#7d7466;">Your $99 session fee is non-refundable. You have 7 days from claiming your spot to choose your package and session date, or your spot is forfeited without refund. Sessions held October 2026 &ndash; October 2027 are eligible for the 2027 Charity Calendar; sessions through March 2028 receive the same discounted rate but are not included in the calendar. Calendar participation is optional.<br><br>JHP Boudoir &middot; Jefferson City, MO</td></tr>
</table></td></tr></table></body></html>"""


def _confirm_sms(plan, name, balance_date, deadline, book_url):
    first = (name or "").split(" ")[0] or "there"
    if plan == "full":
        return (f"Hi {first}! It's Jessica w/ JHP Boudoir. Your $99 session fee is paid in full — your "
                f"Charity Calendar spot is claimed! You have 7 days (until {deadline}) to choose your "
                f"package & session date here: {book_url} (It's in your email too.) Xo, Jess")
    return (f"Hi {first}! It's Jessica w/ JHP Boudoir. Your $1 is in & your Charity Calendar spot is claimed! "
            f"Your $98 balance charges on {_fmt_day(balance_date)}. You have 7 days (until {deadline}) to choose "
            f"your package & session date here: {book_url} Xo, Jess")


def _run_check(cur, token, app, now):
    state, msg = _invite_state(app, now)
    nxt = None
    if state == "claimed" and app and (app.get("status") or "").lower() == "claimed":
        nxt = _live_next_url(cur, app["id"])
    _check_status(cur, token, state, card_error=msg,
                  claim_deadline=(app or {}).get("claim_deadline") if state == "ready" else None,
                  next_url=nxt)
    print(f"check: invite -> {state}" + (f" (application {app['id']})" if app else ""))


def main():
    raw = _read_webhook_body()
    if not raw:
        print("no webhook body; nothing to do")
        return
    if len(raw) > MAX_BODY_BYTES:
        print(f"body too large ({len(raw)} bytes); dropped")
        return
    try:
        body = json.loads(raw)
    except Exception:
        print("body is not valid JSON; dropped")
        return
    if not isinstance(body, dict):
        print("body is not a JSON object; dropped")
        return

    def s(key, cap=400):
        v = body.get(key)
        if v is None or v == "":
            return None
        return str(v)[:cap]

    token = str(body.get("client_token") or "").strip()[:80]
    if not token:
        print("missing client_token; nothing to report to")
        return
    mode = "check" if str(body.get("mode") or "").strip().lower() == "check" else "pay"
    invite = str(body.get("invite_token") or "").strip()[:128]
    source_id = s("sourceId", 1000) or s("source_id", 1000)
    verification_token = s("verification_token", 4096)
    acknowledged = bool(body.get("acknowledged"))
    body_is_test = bool(body.get("is_test"))
    user_agent = s("user_agent", 400)
    plan = "full" if str(body.get("plan") or "").strip().lower() == "full" else "deposit"

    # balance_date required only for the deposit plan; must be 1..14 days out.
    balance_date = None
    if plan == "deposit":
        try:
            bd = str(body.get("balance_date") or "").strip()[:10]
            d = date.fromisoformat(bd)
            today = date.today()
            if today < d <= today + timedelta(days=MAX_WINDOW_DAYS):
                balance_date = d
        except Exception:
            balance_date = None

    deposit_amt = FULL_CENTS if plan == "full" else DEPOSIT_CENTS
    balance_amt = 0 if plan == "full" else BALANCE_CENTS

    # Expiry of the $98 is anchored to the balance-charge date (+2-day grace) so the scheduled
    # $98 always settles before the monitor can release the claim (same as EMC).
    if plan == "deposit" and balance_date:
        expires_at = datetime.combine(balance_date, datetime.max.time(),
                                      tzinfo=timezone.utc) + timedelta(days=2)
    else:
        expires_at = datetime.now(timezone.utc) + timedelta(days=14)

    conn = psycopg2.connect(dbname=os.environ["PGDATABASE"], user=os.environ["PGUSER"], host=os.environ["PGHOST"])
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    charged = False   # once True, never report 'error' for a later (non-money) failure
    rid = None
    try:
        now = datetime.now(timezone.utc)
        app = None
        if INVITE_RE.fullmatch(invite or ""):
            # Row lock serializes concurrent claims (two tabs / double-submit) on the same invite
            # until the 'new' reservation row below is committed.
            cur.execute("SELECT * FROM charity_calendar_applications WHERE invite_token=%s "
                        "LIMIT 1 FOR UPDATE", (invite,))
            app = cur.fetchone()

        if mode == "check":
            _run_check(cur, token, app, now)
            conn.commit()
            return

        # same-token dedupe (a successful claim flips the application to 'claimed', so this
        # must run before the invite-state check to stay silent on a duplicate POST)
        cur.execute("SELECT id, status FROM ccmc_reservations WHERE client_token=%s LIMIT 1", (token,))
        ex = cur.fetchone()
        if ex and ex["status"] in ("reserved", "paid", "booked", "released", "forfeited"):
            conn.commit()
            print(f"client_token already {ex['status']} (row {ex['id']}); skipping")
            return

        state, msg = _invite_state(app, now)
        if state != "ready":
            nxt = None
            if state == "claimed" and (app.get("status") or "").lower() == "claimed":
                nxt = _live_next_url(cur, app["id"])
            _status(cur, token, state, card_error=msg, next_url=nxt)
            conn.commit()
            print(f"invite not claimable ({state}); refused" + (f" (application {app['id']})" if app else ""))
            return

        app_id = app["id"]
        is_test = bool(app.get("is_test"))
        if body_is_test and not is_test:
            _status(cur, token, "error", card_error="Test mode isn't available for this invitation.")
            conn.commit()
            print(f"is_test=true in body but application {app_id} is not a test row; refused")
            return

        name = (app.get("contact_name") or "").strip()[:200] or None
        email = (app.get("contact_email") or "").strip()[:200] or None
        phone = (app.get("contact_phone") or "").strip()[:60] or None

        # Different-token double-charge guard (second tab, reload mid-'Processing'): refuse
        # while this application already has a live claim or a very recent in-flight one.
        # Same-token retries are allowed — they reuse the Square idempotency keys. A row that
        # already took money but then failed (balance scheduling error) also blocks: Jessica is
        # alerted and fixes it by hand, rather than the invitee paying a second $1.
        cur.execute(
            "SELECT id, status FROM ccmc_reservations "
            "WHERE application_id=%s AND client_token IS DISTINCT FROM %s "
            "  AND (status IN ('reserved','paid','booked') "
            "       OR square_deposit_payment_id IS NOT NULL "
            "       OR (status = 'new' AND created_at > NOW() - (%s || ' minutes')::interval)) "
            "ORDER BY id DESC LIMIT 1",
            (app_id, token, str(INFLIGHT_GUARD_MINUTES)))
        dup = cur.fetchone()
        if not dup and email and not is_test:
            cur.execute(
                "SELECT id, status FROM ccmc_reservations "
                "WHERE lower(contact_email)=lower(%s) AND is_test = false "
                "  AND (status IN ('reserved','paid','booked') "
                "       OR (status = 'new' AND created_at > NOW() - (%s || ' minutes')::interval)) "
                "  AND client_token IS DISTINCT FROM %s "
                "ORDER BY id DESC LIMIT 1",
                (email, str(INFLIGHT_GUARD_MINUTES), token))
            dup = cur.fetchone()
        if dup:
            _status(cur, token, "error", card_error=MSG_INFLIGHT)
            conn.commit()
            print(f"application {app_id} already has a live/in-flight claim (row {dup['id']} {dup['status']}); "
                  f"skipping to avoid double charge")
            return

        if not acknowledged:
            _status(cur, token, "error", card_error="Please agree to the reservation terms."); conn.commit()
            print("acknowledged=false; refused"); return
        if not source_id:
            _status(cur, token, "error", card_error="We didn't receive your card details. Please try again."); conn.commit()
            print("missing sourceId; refused"); return
        if plan == "deposit" and not balance_date:
            _status(cur, token, "error", card_error="Please choose a balance date within the next 14 days."); conn.commit()
            print("bad balance_date; refused"); return

        cur.execute(
            """
            INSERT INTO ccmc_reservations
                (application_id, invite_token, client_token, contact_name, contact_email, contact_phone,
                 plan, balance_due_date, deposit_cents, balance_cents, status, is_test, user_agent, expires_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'new',%s,%s,%s)
            ON CONFLICT (client_token) DO UPDATE SET
                plan=EXCLUDED.plan, balance_due_date=EXCLUDED.balance_due_date,
                deposit_cents=EXCLUDED.deposit_cents, balance_cents=EXCLUDED.balance_cents,
                expires_at=EXCLUDED.expires_at, status='new', card_error=NULL
            RETURNING id
            """,
            (app_id, invite, token, name, email, phone, plan, balance_date, deposit_amt, balance_amt,
             is_test, user_agent, expires_at),
        )
        rid = cur.fetchone()["id"]
        _status(cur, token, "new", balance_date=balance_date)
        conn.commit()   # also releases the application row lock

        done_status = "paid" if plan == "full" else "reserved"
        next_url = _booking_url(name, email, phone, is_test)

        if is_test:
            cur.execute(
                "UPDATE ccmc_reservations SET status=%s, reserved_at=NOW(), "
                "paid_at=CASE WHEN %s='full' THEN NOW() ELSE NULL END, handed_off_at=NOW(), "
                "booking_deadline=NOW() + (%s || ' days')::interval, next_url=%s, "
                "notes='is_test short-circuit' WHERE id=%s",
                (done_status, plan, str(BOOKING_WINDOW_DAYS), next_url, rid))
            cur.execute("UPDATE charity_calendar_applications SET status='claimed', reserved_at=NOW() WHERE id=%s",
                        (app_id,))
            _status(cur, token, done_status, balance_date=balance_date, next_url=next_url)
            conn.commit()
            print(f"is_test claim {rid} (application {app_id}) plan={plan} — no Square/GHL"); return

        if not _sq_token:
            _status(cur, token, "error", card_error="Payments are temporarily unavailable."); conn.commit()
            print(f"missing {_SQ_TOKEN_ENV}"); return

        # customer (reuse by email, else create)
        customer_id = None
        if email:
            ok, _, sd = _sq("POST", "/v2/customers/search", {"query": {"filter": {"email_address": {"exact": email}}}})
            if ok and (sd.get("customers") or []):
                customer_id = sd["customers"][0]["id"]
        if not customer_id:
            parts = (name or "").split(" ")
            cbody = {"given_name": parts[0] or None, "family_name": " ".join(parts[1:]) or None,
                     "email_address": email, "phone_number": phone,
                     "reference_id": f"ccmc-{rid}", "note": "2027 Charity Calendar Model Call claim"}
            cbody = {k: v for k, v in cbody.items() if v}
            ok, code, cd = _sq("POST", "/v2/customers", cbody, idem=f"ccmccu-{token}")
            if not ok:
                _status(cur, token, "error", card_error="We couldn't set up your reservation. Please try again.")
                cur.execute("UPDATE ccmc_reservations SET status='error', card_error=%s WHERE id=%s",
                            (json.dumps({"step": "customer", "data": cd}), rid)); conn.commit()
                print(f"customer failed {code}: {cd}"); return
            customer_id = cd["customer"]["id"]

        # vault the card (include buyer-verification token for SCA when the page sent one)
        _card_req = {"source_id": source_id, "card": {"customer_id": customer_id}}
        if verification_token:
            _card_req["verification_token"] = verification_token
        ok, code, kd = _sq("POST", "/v2/cards", _card_req, idem=f"ccmccd-{token}")
        if not ok:
            _status(cur, token, "error", card_error=_sq_err(kd, "That card could not be saved. Please check the details."))
            cur.execute("UPDATE ccmc_reservations SET status='error', square_customer_id=%s, card_error=%s WHERE id=%s",
                        (customer_id, json.dumps({"step": "card", "data": kd}), rid)); conn.commit()
            print(f"card vault failed {code}: {kd}"); return
        card_id = kd["card"]["id"]

        # charge now: $99 (full) or $1 (deposit)
        note = ("2027 Charity Calendar Model Call — $99 session fee (paid in full). All payments are final and non-refundable."
                if plan == "full"
                else "2027 Charity Calendar Model Call — $1 claim deposit (of $99). All payments are final and non-refundable.")
        pbody = {"source_id": card_id, "customer_id": customer_id,
                 "amount_money": {"amount": deposit_amt, "currency": CURRENCY},
                 "location_id": LOCATION_ID, "note": note}
        if email:
            pbody["buyer_email_address"] = email
        ok, code, pd = _sq("POST", "/v2/payments", pbody, idem=f"ccmcch-{token}")
        if not ok:
            _status(cur, token, "error", card_error=_sq_err(pd, "Your card was declined."))
            cur.execute("UPDATE ccmc_reservations SET status='error', square_customer_id=%s, square_card_id=%s, card_error=%s WHERE id=%s",
                        (customer_id, card_id, json.dumps({"step": "charge", "data": pd}), rid)); conn.commit()
            print(f"charge failed {code}: {pd}"); return
        charged = True
        pay = pd["payment"]
        pay_id = pay.get("id")
        # Persist the money trail immediately so nothing after this point can lose it.
        cur.execute("UPDATE ccmc_reservations SET square_customer_id=%s, square_card_id=%s, "
                    "square_deposit_payment_id=%s WHERE id=%s", (customer_id, card_id, pay_id, rid))
        conn.commit()

        invoice_id = public_url = None
        if plan == "deposit":
            # 1) create a DRAFT order with the $98 line item, then 2) create the invoice
            # referencing it (Square has no invoice.order_request field).
            ord_body = {"idempotency_key": f"ccmcor-{token}"[:45],
                        "order": {"location_id": LOCATION_ID, "customer_id": customer_id, "state": "OPEN",
                                  "line_items": [{"name": "2027 Charity Calendar Model Call — Session Fee (balance of $99)",
                                                  "quantity": "1", "base_price_money": {"amount": BALANCE_CENTS, "currency": CURRENCY}}]}}
            ooki, ocode, odata = _sq("POST", "/v2/orders", ord_body)
            if not ooki:
                print(f"order create failed {ocode}: {odata}")
                _status(cur, token, "error", card_error="Your $1 went through, but scheduling the balance failed — we'll be in touch.")
                cur.execute("UPDATE ccmc_reservations SET status='error', card_error=%s WHERE id=%s",
                            (json.dumps({"step": "order", "data": odata}), rid))
                queue_note(cur, "Charity Calendar claim needs attention",
                           f"{name or email}'s $1 claim deposit went through but the $98 balance invoice could "
                           f"not be scheduled (order step). Reservation {rid}, application {app_id}. Please "
                           f"follow up and set up the balance by hand.")
                conn.commit()
                return
            order_id = odata["order"]["id"]
            inv_body = {
                "invoice": {
                    "location_id": LOCATION_ID,
                    "order_id": order_id,
                    "primary_recipient": {"customer_id": customer_id},
                    "payment_requests": [{
                        "request_type": "BALANCE", "due_date": balance_date.isoformat(),
                        "automatic_payment_source": "CARD_ON_FILE", "card_id": card_id,
                    }],
                    "delivery_method": "EMAIL", "accepted_payment_methods": {"card": True},
                    "title": "JHP Boudoir — Charity Calendar Session Fee (balance)",
                    "description": "Remaining balance of your $99 2027 Charity Calendar Model Call session fee. All payments are final and non-refundable.",
                },
                "idempotency_key": f"ccmciv-{token}"[:45],
            }
            ok, code, ivd = _sq("POST", "/v2/invoices", inv_body)
            if ok:
                invoice_id = ivd["invoice"]["id"]
                version = ivd["invoice"]["version"]
                okp, codep, pubd = _sq("POST", f"/v2/invoices/{invoice_id}/publish",
                                       {"version": version, "idempotency_key": f"ccmcpb-{token}"[:45]})
                if okp:
                    public_url = (pubd.get("invoice") or {}).get("public_url")
                else:
                    print(f"invoice publish failed {codep}: {pubd}")
                    _status(cur, token, "error", card_error="Your $1 went through, but scheduling the balance failed — we'll be in touch.")
                    cur.execute("UPDATE ccmc_reservations SET status='error', square_invoice_id=%s, card_error=%s WHERE id=%s",
                                (invoice_id, json.dumps({"step": "publish", "data": pubd}), rid))
                    queue_note(cur, "Charity Calendar claim needs attention",
                               f"{name or email}'s $1 claim deposit went through but the $98 balance invoice "
                               f"{invoice_id} could not be published. Reservation {rid}, application {app_id}.")
                    conn.commit()
                    return
            else:
                print(f"invoice create failed {code}: {ivd}")
                _status(cur, token, "error", card_error="Your $1 went through, but scheduling the balance failed — we'll be in touch.")
                cur.execute("UPDATE ccmc_reservations SET status='error', card_error=%s WHERE id=%s",
                            (json.dumps({"step": "invoice", "data": ivd}), rid))
                queue_note(cur, "Charity Calendar claim needs attention",
                           f"{name or email}'s $1 claim deposit went through but the $98 balance invoice could "
                           f"not be created. Reservation {rid}, application {app_id}.")
                conn.commit()
                return

        # finalize in the DB FIRST (money is in; nothing after this may flip the claim to 'error')
        cur.execute(
            """UPDATE ccmc_reservations SET status=%s, reserved_at=NOW(),
                   paid_at=CASE WHEN %s='full' THEN NOW() ELSE NULL END, handed_off_at=NOW(),
                   booking_deadline=NOW() + (%s || ' days')::interval, next_url=%s,
                   square_invoice_id=%s, square_invoice_public_url=%s, card_error=NULL
               WHERE id=%s
               RETURNING booking_deadline""",
            (done_status, plan, str(BOOKING_WINDOW_DAYS), next_url, invoice_id, public_url, rid))
        booking_deadline = cur.fetchone()["booking_deadline"]
        cur.execute("UPDATE charity_calendar_applications SET status='claimed', reserved_at=NOW() WHERE id=%s",
                    (app_id,))
        _status(cur, token, done_status, balance_date=balance_date, next_url=next_url)
        conn.commit()
        print(f"{done_status.upper()} {rid} (application {app_id}): plan={plan} customer={customer_id} "
              f"payment={pay_id} invoice={invoice_id} balance_due={balance_date} deadline={booking_deadline}")

        # GHL upsert (best-effort) + additive tags + mirror
        tags = [CLAIMED_TAG, PAID_TAG] if plan == "full" else [CLAIMED_TAG]
        gid, contact, gerr = _ghl_upsert(name, email, phone)
        if not gid:
            print(f"ghl upsert failed: {gerr}")
            gid = app.get("ghl_contact_id")
        if gid:
            terr = _ghl_add_tags(gid, tags)
            if terr:
                print(f"ghl tag warning: {terr}")
            if contact:
                _mirror_ghl(cur, gid, contact, name, email, phone, tags)
            cur.execute("UPDATE ccmc_reservations SET ghl_contact_id=%s WHERE id=%s", (gid, rid))
            cur.execute("UPDATE charity_calendar_applications SET ghl_contact_id=COALESCE(ghl_contact_id, %s) WHERE id=%s",
                        (gid, app_id))
            conn.commit()

        deadline_str = _fmt_deadline(booking_deadline)
        first_nm = (name or "").split(" ")[0] or "there"
        sid, serr = _ghl_sms(gid, _confirm_sms(plan, name, balance_date, deadline_str, next_url))
        print(f"  confirm sms: {sid or serr}")
        subj = ("You're in! Your Charity Calendar spot is claimed ✦" if plan == "deposit"
                else "You're in! Your Charity Calendar session fee is paid ✦")
        eid, eerr = _ghl_email(gid, subj, _claimed_email_html(first_nm, plan, _fmt_day(balance_date),
                                                              deadline_str, next_url))
        print(f"  confirm email: {eid or eerr}")

        if plan == "full":
            pay_desc = "paid the $99 session fee in full"
        else:
            pay_desc = f"paid $1 today; the $98 balance auto-charges on {_fmt_day(balance_date)}"
        queue_note(cur, "Charity Calendar spot claimed",
                   f"{name or email} claimed their 2027 Charity Calendar Model Call spot and {pay_desc}. "
                   f"They have until {deadline_str} (Central) to book their package and session date. "
                   f"Reservation {rid}, application {app_id}. Confirmation SMS: {'sent' if sid else 'NOT sent'}; "
                   f"email: {'sent' if eid else 'NOT sent'}.")
        conn.commit()

    except Exception as e:
        conn.rollback()
        try:
            if charged:
                # Money moved: keep the page's success path; just log + alert.
                print(f"post-charge warning (reservation {rid}): {type(e).__name__}: {e}")
                queue_note(cur, "Charity Calendar claim needs attention",
                           f"Reservation {rid} was charged but a later step failed "
                           f"({type(e).__name__}). Please check the reservation and the client's messages.")
                conn.commit()
            else:
                _status(cur, token, "error", card_error="Something went wrong on our end. Please try again.")
                conn.commit()
        except Exception:
            pass
        print(f"claim error: {type(e).__name__}: {e}")
        if not charged:
            raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
