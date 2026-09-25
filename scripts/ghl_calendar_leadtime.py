#!/usr/bin/env python3
"""Read, and optionally set, two things on Jessica's consultation calendar.

RUNS ON SCALOGY, NOT HERE. This file is the version-controlled copy; the one
that executes lives in the tenant artifact store at the same path and is
fired by the manual workflow `ghl-calendar-settings`. It needs
`ghl_api_key`, which is a tenant secret -- `http_request` refuses secret
substitution outright, so a secret-bearing call has to be a workflow. Keep
the two copies in step by hand; nothing enforces it.

Her asks, 25 September: "For the consultation calendar, allow a lead time of
4 days" and "Time slots on the calendar should be 20 minutes also."

THE 20 MINUTES WAS ALSO A CONSISTENCY FIX. The site already tells women the
consultation is twenty minutes -- F["consult"] in build-guide.py, and an
answer in the FAQ -- and CLAUDE.md records that her old Canva guide
contradicted itself on it (20 minutes on page 11, 30 on page 15). The first
read settled it: the calendar was 30. The site had been contradicting the
scheduler, and this closed it in the scheduler's favour because she said so.

IT NEEDS A REAL USER-AGENT. urllib sends "Python-urllib/3.x", which
Cloudflare blanket-bans in front of services.leadconnectorhq.com -- the first
run came back 403 error 1010, "browser signature banned", before the request
ever reached GHL. The UA below names this client honestly rather than
pretending to be a browser; the credential doing the talking is still her own
API key.

THE PUT REJECTS SOME OF WHAT THE GET RETURNS. GHL's calendar object is not
round-trippable: a PUT carrying locationId or formSubmitRedirectUrl comes
back 422 "property X should not exist". Rather than guess at the read-only
set, the loop below reads the names out of the 422 and drops exactly those,
then retries. It is capped, and it never drops a field this script is trying
to SET -- if the API ever rejects one of those, that is a real failure and it
stops rather than quietly writing three of four values.

READ FIRST, ALWAYS. Run it with no argument and it only reports. Run it with
`apply` and it writes. The read is not politeness: the update is a PUT, and a
PUT that omits a field can blank it, so the write sends the WHOLE calendar
object back with only the wanted values changed. It then re-reads and proves
the change landed and that nothing else moved.

The calendar is the Info calendar, mi2EqYRq4gGEbBJHe82b -- the one
/contact forwards to and every Book a Call button on the site opens.
"""
import json
import os
import re
import sys
import urllib.request
import urllib.error

CAL = "mi2EqYRq4gGEbBJHe82b"
BASE = "https://services.leadconnectorhq.com"
KEY = os.environ["ghl_api_key"]
UA = "JHPBoudoir-Scalogy/1.0 (calendar settings; +https://pages.scalogy.com/jhpboudoir1/)"

# Her figures. The units are GHL's own vocabulary, not free text.
WANT = {
    "allowBookingAfter": 4,        # the lead time
    "allowBookingAfterUnit": "days",
    "slotDuration": 20,            # the appointment length
    "slotDurationUnit": "mins",
}

# Known not to survive a round trip. The 422 loop finds any others.
DROP = {"id", "_id", "dateAdded", "dateUpdated", "deleted"}

# What a PUT must not silently change. Compared before and after.
# slotInterval is in here deliberately: it is how OFTEN a bookable start
# appears, which is a different setting from how LONG the appointment is, and
# it must not move as a side effect of shortening the appointment.
WATCH = ["name", "slug", "calendarType", "slotInterval", "slotIntervalUnit",
         "slotBufferUnit", "appoinmentPerSlot", "appoinmentPerDay",
         "appointmentPerSlot", "appointmentPerDay", "allowBookingFor",
         "allowBookingForUnit", "openHours", "isActive", "autoConfirm",
         "groupId", "teamMembers", "availabilities", "eventTitle",
         "eventType", "widgetSlug", "notifications"]


def call(method, path, payload=None):
    req = urllib.request.Request(
        BASE + path,
        method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={
            "Authorization": "Bearer " + KEY,
            "Version": "2021-04-15",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": UA,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, {"_error": e.read().decode()[:1200]}


def summarise(cal, label):
    print("--- %s ---" % label)
    print("  name               : %r" % cal.get("name"))
    print("  allowBookingAfter  : %r %r   <- the lead time"
          % (cal.get("allowBookingAfter"), cal.get("allowBookingAfterUnit")))
    print("  slotDuration       : %r %r   <- the slot length"
          % (cal.get("slotDuration"), cal.get("slotDurationUnit")))
    print("  slotInterval       : %r %r   (how often a slot starts)"
          % (cal.get("slotInterval"), cal.get("slotIntervalUnit")))
    print("  allowBookingFor    : %r %r   (how far ahead)"
          % (cal.get("allowBookingFor"), cal.get("allowBookingForUnit")))
    print("  isActive           : %r" % cal.get("isActive"))


status, body = call("GET", "/calendars/" + CAL)
if status >= 400:
    print("GET failed: %s %s" % (status, body))
    sys.exit(1)

cal = body.get("calendar", body)
summarise(cal, "BEFORE")

before = {k: cal.get(k) for k in WATCH}
need = {k: v for k, v in WANT.items() if cal.get(k) != v}

if "apply" not in sys.argv:
    print("\nREAD ONLY. Nothing was written.")
    print("would change: %s" % (need if need else "nothing, already correct"))
    sys.exit(0)

if not need:
    print("\nAlready correct. Nothing to write.")
    sys.exit(0)

drop = set(DROP)
for attempt in range(1, 7):
    payload = {k: v for k, v in cal.items() if k not in drop}
    payload.update(WANT)
    status, body = call("PUT", "/calendars/" + CAL, payload)
    if status < 400:
        print("\nPUT -> %s on attempt %d" % (status, attempt))
        break
    msg = body.get("_error", "")
    rejected = set(re.findall(r"property (\w+) should not exist", msg))
    clash = rejected & set(WANT)
    if clash:
        print("\nSTOPPING: the API rejects %s, which is a value we must set."
              % sorted(clash))
        sys.exit(1)
    if not rejected:
        print("\nPUT -> %s, and the error names no droppable field:\n  %s"
              % (status, msg))
        sys.exit(1)
    print("  attempt %d: %s rejected %s, dropping and retrying"
          % (attempt, status, sorted(rejected)))
    drop |= rejected
else:
    print("\nGave up after 6 attempts. Nothing was written.")
    sys.exit(1)

print("  fields the PUT would not accept: %s" % sorted(drop - DROP))

status, body = call("GET", "/calendars/" + CAL)
after_cal = body.get("calendar", body)
summarise(after_cal, "AFTER")

wrong = {k: {"wanted": WANT[k], "got": after_cal.get(k)}
         for k in WANT if after_cal.get(k) != WANT[k]}
print("\nwanted vs got: %s" % (wrong if wrong else "all four correct"))

moved = {k: {"was": before.get(k), "now": after_cal.get(k)} for k in WATCH
         if json.dumps(before.get(k), sort_keys=True, default=str)
         != json.dumps(after_cal.get(k), sort_keys=True, default=str)}
print("other settings that moved: %s" % (moved if moved else "none"))
sys.exit(0 if not wrong and not moved else 1)
