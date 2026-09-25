#!/usr/bin/env python3
"""Read, and optionally set, the words a woman reads on the booking widget.

RUNS ON SCALOGY, NOT HERE. This file is the version-controlled copy; the one
that executes lives in the tenant artifact store at the same path and is
fired by the manual workflow `ghl-calendar-copy`. Keep the two in step by
hand; nothing enforces it.

Her ask, 25 September: "All fill out the info for the calendar so the reader
knows what they are booking. Let them know to have their credit card ready if
they are ready to proceed with booking to process their session fee
retainer."

WHAT THE FIRST READ FOUND, and why there was more to do than she asked:
  name                     'Info'          -- meaningless to a reader
  description              ''              -- EMPTY. The main ask.
  eventTitle               '{{contact.name}}'  -- her name and nothing else,
                                           so the appointment in a diary says
                                           who but not what
  formSubmitThanksMessage  GHL's stock text, which says "We will contact you
                           shortly to confirm your request" -- and autoConfirm
                           is True, so it IS confirmed. It also printed a bare
                           {{contactMethod}} token.

Run with no argument to REPORT every text field. Run with `apply` to write.
Read, write the whole object back minus what the PUT rejects, re-read, prove
it, and print the lead time and slot length so a copy change cannot quietly
undo the settings the other script set.
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
UA = "JHPBoudoir-Scalogy/1.0 (calendar copy; +https://pages.scalogy.com/jhpboudoir1/)"

TEXT = ["name", "description", "eventTitle", "eventType", "consentLabel",
        "formSubmitThanksMessage", "formSubmitType", "formSubmitRedirectUrl",
        "notes", "widgetSlug", "widgetType", "calendarCoverImage",
        "guestType", "eventColor", "isLivePaymentMode", "formId",
        "allowCancellation", "allowReschedule", "enableRecurring",
        "shouldAssignContactToTeamMember", "stickyContact", "autoConfirm"]

DROP = {"id", "_id", "dateAdded", "dateUpdated", "deleted"}

# ---------------------------------------------------------------- the copy
#
# NO FIGURE IN IT, deliberately. The session fee is $697 and it already lives
# in three places -- the FAQ, the guide, and the home page's Offer schema. A
# fourth copy on a GHL calendar is a fourth thing to remember on the day the
# fee changes, and a stale price on a booking page is exactly how the Canva
# guide came to undercut the site by $197. The call is where the number gets
# said. ASK JESSICA before putting one here.
#
# IT SAYS PHONE, NOT ZOOM. The consultation is a phone call -- "one 20 minute
# phone consultation" in the guide. The ZOOM appointment is the image reveal,
# which is a different thing entirely and much later. Confusing the two would
# have her waiting at a laptop for a call that never comes.
#
# CONSENTLABEL IS LEFT ALONE. It is a marketing-consent checkbox with
# compliance weight, not copy to tidy.
WANT = {
    # 'Info' is what the widget headed itself with. It tells a reader nothing.
    "name": "Boudoir Consultation Call",

    "description": (
        "A twenty minute phone call with Jess, and the first step to a "
        "session at JHP Boudoir.\n\n"
        "We will talk through what a boudoir session here is really like, "
        "which type of session suits you, how the day itself runs, and the "
        "Collections. Bring every question you have — including the ones "
        "you have not said out loud yet. There is no pressure and nothing to "
        "prepare.\n\n"
        "If you already know you would like to book, have a card ready to "
        "process your session fee retainer over the phone. That is what "
        "reserves your date."
    ),

    # Who AND what, so a diary entry a fortnight from now still makes sense.
    "eventTitle": "Boudoir Consultation — {{contact.name}}",

    "formSubmitThanksMessage": (
        "You are booked — thank you. A confirmation is on its way to your "
        "email, and it carries links to reschedule or cancel if anything "
        "changes.\n\n"
        "If you already know you would like to book your session when we "
        "talk, have a card ready to process your session fee retainer over "
        "the phone.\n\n"
        "I cannot wait to speak with you. — Jess"
    ),
}


def call(method, path, payload=None):
    req = urllib.request.Request(
        BASE + path, method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Authorization": "Bearer " + KEY, "Version": "2021-04-15",
                 "Accept": "application/json",
                 "Content-Type": "application/json", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, {"_error": e.read().decode()[:1200]}


status, body = call("GET", "/calendars/" + CAL)
if status >= 400:
    print("GET failed: %s %s" % (status, body))
    sys.exit(1)
cal = body.get("calendar", body)

print("--- the words, as they stand ---")
for k in TEXT:
    print("  %-32s %r" % (k, cal.get(k)))

if "apply" not in sys.argv:
    print("\nREAD ONLY. Nothing was written.")
    print("would change: %s"
          % sorted(k for k, v in WANT.items() if cal.get(k) != v))
    sys.exit(0)

need = {k: v for k, v in WANT.items() if cal.get(k) != v}
if not need:
    print("\nAlready correct. Nothing to write.")
    sys.exit(0)
print("\nwill change: %s" % sorted(need))

drop = set(DROP)
for attempt in range(1, 7):
    payload = {k: v for k, v in cal.items() if k not in drop}
    payload.update(WANT)
    status, body = call("PUT", "/calendars/" + CAL, payload)
    if status < 400:
        print("PUT -> %s on attempt %d" % (status, attempt))
        break
    msg = body.get("_error", "")
    rejected = set(re.findall(r"property (\w+) should not exist", msg))
    if rejected & set(WANT):
        print("STOPPING: API rejects %s, which we must set."
              % sorted(rejected & set(WANT)))
        sys.exit(1)
    if not rejected:
        print("PUT -> %s, no droppable field named:\n  %s" % (status, msg))
        sys.exit(1)
    drop |= rejected
else:
    print("Gave up after 6 attempts. Nothing written.")
    sys.exit(1)

status, body = call("GET", "/calendars/" + CAL)
after = body.get("calendar", body)
print("\n--- the words now ---")
for k in TEXT:
    print("  %-32s %r" % (k, after.get(k)))

wrong = {k: {"wanted": WANT[k], "got": after.get(k)}
         for k in WANT if after.get(k) != WANT[k]}
print("\nwanted vs got: %s" % (wrong if wrong else "every field correct"))

print("\n--- the settings, which a copy change must not touch ---")
for k in ("allowBookingAfter", "allowBookingAfterUnit", "slotDuration",
          "slotDurationUnit", "slotInterval"):
    print("  %-24s %r" % (k, after.get(k)))
sys.exit(0 if not wrong else 1)
