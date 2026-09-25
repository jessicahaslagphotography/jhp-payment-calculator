#!/usr/bin/env python3
"""Read, and optionally set, the booking settings on the consultation calendar.

RUNS ON SCALOGY, NOT HERE. This file is the version-controlled copy; the one
that executes lives in the tenant artifact store at the same path and is
fired by the manual workflow `ghl-calendar-settings`. Keep the two in step by
hand -- nothing enforces it, and this file has already drifted once.

Her asks, 25 September, in the order they came:
  "For the consultation calendar, allow a lead time of 4 days."
  "Time slots on the calendar should be 20 minutes also."
  "time slots on the calendar need to be 20 minutes so it doesn't disrupt my
   giveaway call calendar availability. Change it."
  "People should only be able to book this calendar up to 4 days in advance.
   Change it."

"LEAD TIME" WAS READ BACKWARDS THE FIRST TIME, and the fourth message is the
correction. GHL has two opposite settings and the phrase fits either:

    allowBookingAfter   the MINIMUM notice. "Not sooner than."
    allowBookingFor     the MAXIMUM window. "Not later than."

It went into allowBookingAfter, which meant nobody could book inside four
days. She meant the other one: nobody can book beyond four days.

SETTING BOTH TO 4 WOULD LEAVE NOTHING BOOKABLE -- not sooner than four days
and not later than four days is a single instant, and in practice an empty
calendar. So clearing the minimum notice is not tidying up after a mistake,
it is required for her actual ask to work, and the guard at the foot refuses
to finish if the two ever end up fighting again.

DURATION AND INTERVAL ARE TWO SETTINGS AND SHE NEEDED BOTH at 20. Duration is
how long the call is; interval is how often a bookable start appears. A 30
minute grid here did not line up with her giveaway calendar's slots, so hours
that should have been free on both showed as unavailable.

THE 20 MINUTES WAS ALSO A CONSISTENCY FIX. The site already tells women the
consultation is twenty minutes -- F["consult"] in build-guide.py, and an
answer in the FAQ -- and her old Canva guide contradicted itself on it
(20 on page 11, 30 on page 15). The first read settled it: the calendar was
30, so the site had been contradicting the scheduler.

IT NEEDS A REAL USER-AGENT. urllib sends "Python-urllib/3.x", which
Cloudflare blanket-bans in front of services.leadconnectorhq.com -- the first
run came back 403 error 1010, "browser signature banned", before the request
ever reached GHL.

THE PUT REJECTS SOME OF WHAT THE GET RETURNS. A PUT carrying locationId or
formSubmitRedirectUrl comes back 422 "property X should not exist". The loop
reads the rejected names out of the 422 and drops exactly those, capped, and
never drops a field it is trying to SET.

READ FIRST, ALWAYS. No argument reports; `apply` writes the WHOLE object back
with only the wanted values changed, then re-reads and proves it.

The calendar is mi2EqYRq4gGEbBJHe82b -- the one /contact forwards to and
every Book a Call button on the site opens.
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
    "allowBookingFor": 4,          # nobody books further out than four days
    "allowBookingForUnit": "days",
    "allowBookingAfter": None,     # and no minimum notice, or nothing is bookable
    "slotDuration": 20,            # how long the call is
    "slotDurationUnit": "mins",
    "slotInterval": 20,            # how often a bookable start appears
    "slotIntervalUnit": "mins",
}

# Known not to survive a round trip. The 422 loop finds any others.
DROP = {"id", "_id", "dateAdded", "dateUpdated", "deleted"}

# What a PUT must not silently change. Compared before and after.
WATCH = ["name", "slug", "calendarType", "description",
         "formSubmitThanksMessage", "eventTitle", "slotBufferUnit",
         "appoinmentPerSlot", "appoinmentPerDay", "appointmentPerSlot",
         "appointmentPerDay", "openHours", "isActive", "autoConfirm",
         "groupId", "teamMembers", "availabilities", "eventType",
         "widgetSlug", "notifications"]


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
    print("  allowBookingFor    : %r %r   <- furthest ahead she can book"
          % (cal.get("allowBookingFor"), cal.get("allowBookingForUnit")))
    print("  allowBookingAfter  : %r %r   <- minimum notice; must stay empty"
          % (cal.get("allowBookingAfter"), cal.get("allowBookingAfterUnit")))
    print("  slotDuration       : %r %r   <- how long the call is"
          % (cal.get("slotDuration"), cal.get("slotDurationUnit")))
    print("  slotInterval       : %r %r   <- how often a slot starts"
          % (cal.get("slotInterval"), cal.get("slotIntervalUnit")))
    print("  isActive           : %r" % cal.get("isActive"))


def bookable(cal):
    """Is there any window left at all?

    A minimum notice at or beyond the maximum window leaves nothing to book.
    Worth checking out loud: an empty calendar looks fine in the API and
    silently costs her every enquiry until somebody notices.
    """
    lo, hi = cal.get("allowBookingAfter"), cal.get("allowBookingFor")
    if not lo or not hi:
        return True
    if cal.get("allowBookingAfterUnit") != cal.get("allowBookingForUnit"):
        return True          # different units, not comparable here; say so
    return lo < hi


status, body = call("GET", "/calendars/" + CAL)
if status >= 400:
    print("GET failed: %s %s" % (status, body))
    sys.exit(1)

cal = body.get("calendar", body)
summarise(cal, "BEFORE")
print("  anything bookable? : %s" % bookable(cal))

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

status, body = call("GET", "/calendars/" + CAL)
after_cal = body.get("calendar", body)
summarise(after_cal, "AFTER")

wrong = {k: {"wanted": WANT[k], "got": after_cal.get(k)}
         for k in WANT if after_cal.get(k) != WANT[k]}
print("\nwanted vs got: %s" % (wrong if wrong else "every value correct"))

moved = {k: {"was": before.get(k), "now": after_cal.get(k)} for k in WATCH
         if json.dumps(before.get(k), sort_keys=True, default=str)
         != json.dumps(after_cal.get(k), sort_keys=True, default=str)}
print("other settings that moved: %s" % (moved if moved else "none"))

ok_window = bookable(after_cal)
print("anything bookable?: %s" % ok_window)
if not ok_window:
    print("FAILED: the minimum notice and the maximum window leave no slots. "
          "Her calendar would take no bookings at all.")
sys.exit(0 if not wrong and not moved and ok_window else 1)
