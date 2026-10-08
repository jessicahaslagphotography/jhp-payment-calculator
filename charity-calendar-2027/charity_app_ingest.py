#!/usr/bin/env python3
"""charity-app-ingest: capture an application for the 2027 Charity Calendar Model Call.

Fired by the charity-app-submit webhook when the charity-calendar-2027 page's
application form is submitted. A near-copy of scripts/site_inquiry_ingest.py on
purpose: same GHL conventions, same dedupe-on-client_token, same
store-first-then-GHL ordering.

The differences are the table (charity_calendar_applications, with her answers
to the application questions and a status column Jessica uses to select models)
and the tag (APPLY_TAG). This script does not email anybody. Whatever happens
next is a GHL workflow watching APPLY_TAG; if nothing watches it, the
application is captured in the table but silent.

is_test rows are stored but skip GHL, so the live form can be submitted
without putting Jessica into her own CRM.
"""
import os
import sys
import json
import re
import psycopg2
import psycopg2.extras

MAX_BODY_BYTES = 20_000

GHL_BASE = "https://services.leadconnectorhq.com"
GHL_VERSION = "2021-07-28"
GHL_SOURCE = "jhpboudoir.com - 2027 Charity Calendar Model Call"
APPLY_TAG = "Charity Calendar 2027 - Applied"
LEAD_TAGS = [APPLY_TAG, "Model Call Lead"]

# Whitelists: the only values allowed to reach the database or GHL.
BOUDOIR_BEFORE = {"no", "yes-jhp", "yes-other"}
SHARING = {"calendar-only", "faceless", "private", "open"}
HEARD_VIA = {"instagram", "facebook", "vip-group", "friend", "past-client", "other"}

_ghl_token = os.environ.get("GHL_API_KEY")
_ghl_location = os.environ.get("GHL_LOCATION_ID") or "Pcnm8GVNMmWTY65qVOAp"


def _read_body():
    raw = ""
    if not sys.stdin.isatty():
        try:
            raw = sys.stdin.read(MAX_BODY_BYTES)
        except Exception:
            raw = ""
    try:
        body = json.loads(raw) if raw.strip() else {}
    except Exception:
        print("body was not valid JSON")
        return {}
    return body if isinstance(body, dict) else {}


def _e164(phone):
    d = re.sub(r"[^0-9]", "", phone or "")
    if not d:
        return None
    if len(d) == 10:
        return f"+1{d}"
    return f"+{d}"


def _ghl_upsert(name, email, phone):
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
        "source": GHL_SOURCE, "tags": LEAD_TAGS,
    }
    body = {k: v for k, v in body.items() if v}
    try:
        r = httpx.post(
            f"{GHL_BASE}/contacts/upsert",
            headers={"Authorization": f"Bearer {_ghl_token}", "Version": GHL_VERSION,
                     "Content-Type": "application/json", "Accept": "application/json",
                     "User-Agent": "Mozilla/5.0 (compatible; JHP-Scalogy/1.0)"},
            json=body, timeout=20,
        )
        if r.status_code >= 400:
            return None, {}, f"GHL HTTP {r.status_code}: {r.text[:200]}"
        contact = (r.json() or {}).get("contact") or {}
        return contact.get("id"), contact, None
    except Exception as e:
        return None, {}, f"{type(e).__name__}: {e}"


def _mirror_ghl(cur, cid, contact, name, email, phone):
    try:
        cur.execute("SAVEPOINT mirror")
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
             LEAD_TAGS, ["charity_calendar_2027_application"], json.dumps(contact)),
        )
        cur.execute("RELEASE SAVEPOINT mirror")
    except Exception as e:
        cur.execute("ROLLBACK TO SAVEPOINT mirror")
        print(f"ghl mirror warning: {type(e).__name__}: {e}")


def main():
    body = _read_body()

    def s(key, limit=200):
        v = body.get(key)
        if v is None or isinstance(v, (dict, list)):
            return None
        v = str(v).strip()
        return v[:limit] or None

    def pick(key, allowed):
        v = s(key, 40)
        if v and v.lower() in allowed:
            return v.lower()
        if v:
            print(f"{key}={v!r} is not a recognised value -- stored as NULL")
        return None

    token = s("client_token", 120)
    name = s("name")
    email = s("email", 254)
    phone = s("phone", 60)
    if not token:
        print("no client_token in body -- nothing to do")
        return
    if not name or not (email or phone):
        print("missing name or contact point -- rejected, nothing stored")
        return
    if email and not re.fullmatch(r"[^@ ]+@[^@ ]+[.][^@ ]+", email):
        print("email does not look like an address -- stored as NULL")
        email = None
        if not phone:
            print("no usable contact point -- rejected, nothing stored")
            return

    is_test = bool(body.get("is_test"))

    conn = psycopg2.connect(dbname=os.environ["PGDATABASE"], user=os.environ["PGUSER"],
                            host=os.environ["PGHOST"],
                            cursor_factory=psycopg2.extras.RealDictCursor)
    conn.autocommit = False
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO charity_calendar_applications
              (client_token, contact_name, contact_email, contact_phone, city, instagram,
               why_apply, cause, boudoir_before, sharing_pref, heard_via, notes,
               acknowledged, source_page, is_test, user_agent)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (client_token) DO NOTHING
            RETURNING id
            """,
            (token, name, email, phone, s("city", 120), s("instagram", 120),
             s("why_apply", 3000), s("cause", 1000),
             pick("boudoir_before", BOUDOIR_BEFORE), pick("sharing_pref", SHARING),
             pick("heard_via", HEARD_VIA), s("notes", 2000),
             bool(body.get("acknowledged")),
             s("source_page", 200), is_test, s("user_agent", 400)),
        )
        row = cur.fetchone()
        if not row:
            conn.commit()
            print("duplicate client_token -- already stored, nothing to do")
            return
        app_id = row["id"]
        print(f"application {app_id} stored ({'test' if is_test else 'live'})")

        if is_test:
            print("is_test -- GHL skipped")
        else:
            cid, contact, err = _ghl_upsert(name, email, phone)
            if cid:
                _mirror_ghl(cur, cid, contact, name, email, phone)
                cur.execute(
                    "UPDATE charity_calendar_applications SET ghl_contact_id=%s, "
                    "ghl_synced_at=NOW(), ghl_error=NULL WHERE id=%s", (cid, app_id))
                print(f"GHL contact upserted, tagged {APPLY_TAG!r}")
            else:
                cur.execute("UPDATE charity_calendar_applications SET ghl_error=%s WHERE id=%s",
                            (err, app_id))
                print(f"GHL upsert failed: {err}")

        conn.commit()
        print("done")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"db error, rolled back: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
