#!/usr/bin/env python3
"""Install (or re-install) the 'Website Inquiry - 2027' follow-up sequence.

This is the DEFINITION OF RECORD for the eight messages a woman gets after she
fills in the Session Guide form on /contact. The copy lives here, once; the
script upserts jhp_workflows + jhp_workflow_steps from it. To change a message,
edit this file and run the workflow again -- never edit the rows by hand, or the
next run of this script silently reverts them.

Approved by Jessica on 25 September 2026. The draft and the reasoning behind
each message are in followup-sequence.md in the website repo.

CADENCE (all delays measured from enrollment, so the clock starts the moment
she submits the form):

    1  immediately   welcome + the guide + the plan
    2  24 hours      did it land, and you do not have to feel ready
    3  72 hours      what if I am nervous -- get her on the phone
    4  7 days        what the session day actually looks like
    5  14 days       the investment, in full
    6  1 month       I have not forgotten about you
    7  3 months      touch base -- what can I answer
    8  6 months      final call, door stays open

SMS IS PARKED, NOT MISSING. Every step carries its text in action_config.sms,
but action_kind is 'send_email', which makes the runner ignore it. /contact
takes a phone number and never asks permission to text, which is TCPA exposure
priced per message. Add the consent line under the phone field, flip SEND_SMS
to True here, re-run, and all eight texts arm at once.

GUARDS (this script refuses to install rather than ship a wrong figure):
  - every superseded number from the Canva guide era is rejected outright
  - a text carrying an emoji is rejected (Jessica's rule, 25 Sep, and some
    carriers upgrade an emoji SMS to MMS, which costs more and can fail)
  - every step must have a subject, a body and a text
  - every {{token}} must be one the runner actually substitutes
"""
import os
import re
import json
import unicodedata
import logging
import psycopg2
import psycopg2.extras

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('build_website_inquiry_2027')

WF_NAME = 'website_inquiry_2027'
WF_DISPLAY = 'Website Inquiry - 2027'

# Flip to True ONLY once /contact carries an SMS consent line. See the docstring.
SEND_SMS = False

# Tokens render_text() in workflow-runner/workflow_runner.py actually knows.
# Anything else silently renders as an empty string, which is how a live email
# ends up with a sentence trailing into nothing.
KNOWN_TOKENS = {
    'contact.first_name', 'contact.name', 'contact.email',
    'guide_url', 'calendar_url', 'book_url', 'booking_deadline',
}

# Every figure that is superseded. Finding one of these in the copy means the
# copy predates Jessica's 24 September settlement -- see CLAUDE.md.
STALE = [
    '$500', '$2,800', '$5,600', '18 month', '3-4 hour', '3 to 4 hour',
    '4-5 hour', '4 to 5 hour', '9am-4pm', '6-8 week', '50 to 100',
    'Petite', 'right after your session', 'S-4X', 'a la carte',
    'Klarna', 'Affirm', 'AfterPay', 'PayPal Credit',
]

# ---------------------------------------------------------------------------
# The photographs.
#
# EVERY ONE OF THESE IS ALREADY ON THE SITE, which is the whole reason they can
# be chosen from here. The image CDN is unreachable from this sandbox, so nobody
# working on this can look at a frame and judge it -- the house rule is that a
# photograph is judged at real size, and these eight already were, by Jessica,
# on the page each one sits on. Picking a fresh frame for an email means picking
# it blind, and that is what the pickers exist to avoid.
#
# One frame per email and no repeats. The same face opening and closing a run
# reads as the only woman who has ever been there.
CDN = 'https://assets.cdn.filesafe.space/Pcnm8GVNMmWTY65qVOAp/media/'

FRAMES = {
    # the /contact lead band -- the photograph she was looking at when she
    # filled the form in, so the email and the page are plainly one thing
    'website-inquiry-day0': ('80df5d3e-43e6-4eb5-84c2-673a346bbec3.jpg',
                             'A client photographed at the JHP Boudoir studio '
                             'near Jefferson City, Missouri'),
    # the studio in window light -- this email is about the room, not her
    'website-inquiry-24h': ('f9de4c0c-ba8e-48bb-b559-a9a11beac76c.jpg',
                            'Window light in the JHP Boudoir studio'),
    # the guide's own posing plate, under the posing answer
    'website-inquiry-72h': ('678293dc-8167-4463-a41b-8a20bfaee783.jpg',
                            'A client posed from head to pointed toe at '
                            'JHP Boudoir'),
    # "this is the part I cannot wait for" -- the session day
    'website-inquiry-7d': ('958c1b0e-53b1-4d18-b5ed-7b4b2ae1ccc5.jpg',
                           'A black and white portrait from a studio session '
                           'at JHP Boudoir'),
    # the reveal plate, under the email that explains what she is buying
    'website-inquiry-14d': ('538477d1-c964-4c26-babe-89e797786880.jpg',
                            'Finished images seen together at a JHP Boudoir '
                            'image reveal'),
    # "every body, every age, every size" -- the email about finally booking
    'website-inquiry-1mo': ('1d6d5e7e-7f3d-490b-9883-371ecaa5f1d0.jpg',
                            'A client photographed at the JHP Boudoir studio '
                            '-- every body, every age, every size'),
    # the consultation band frame, under the touch-base ask
    'website-inquiry-3mo': ('78e3da43-f19a-4c5b-a450-c76cd27ad02f.jpg',
                            'A black and white portrait from a studio session '
                            'at JHP Boudoir'),
    # the Session Guide cover, Jessica's own pick -- the goodbye closes on the
    # frame she chose for the document herself
    'website-inquiry-6mo': ('92138463-6253-40ca-a072-7005daa9d96a.jpg',
                            'A client photographed at the JHP Boudoir studio, '
                            'from the Session Guide'),
}


# The Instagram sign-off, on all eight. Jessica's ask, 26 September.
#
# DELIBERATELY AN INLINE LINK AND NOT A BUTTON. A standalone link on its own
# line is what _md_to_html turns into a centred gold CTA, and a second gold
# button under "Book my call" would compete with the only ask that matters in
# these emails. This is a quiet secondary action, under a rule, after the
# sign-off -- a footer, not a second request.
#
# The handle is @jhpboudoir_ (the trailing underscore is part of it) and the
# wording matches the home page's own "Follow on Instagram".
INSTAGRAM = (
    "---\n\n"
    "**Come find me on Instagram** — new work, a look behind the scenes, and "
    "the occasional reveal I am allowed to share: "
    "[@jhpboudoir_](https://www.instagram.com/jhpboudoir_)"
)


def photo(target):
    """The markdown image line for an email.

    A standalone image line is what email_actions._md_to_html turns into a
    centred, Outlook-safe frame. Inline HTML must NOT be used instead: the
    renderer sees an HTML tag anywhere in a body and passes the WHOLE body
    through unprocessed, which would kill every bold run, link and button in
    the email.
    """
    f, alt = FRAMES[target]
    return '![%s](%s%s)' % (alt, CDN, f)


INCLUDES = (
    "✨ A two to three hour experience in our luxury studio\n"
    "✨ Professional hair and makeup at a local salon before you arrive "
    "(hellooooo makeover!)\n"
    "✨ Full access to the studio wardrobe — 160 pieces, sizes XS to 4X\n"
    "✨ A full session where I pose you from head to pointed toe\n"
    "✨ Expert posing and expression guidance\n"
    "✨ Retouching, and your private image reveal and ordering appointment"
)

# ---------------------------------------------------------------------------
# The eight messages.
#
# body_md is rendered by email_actions._md_to_html, which does NOT understand
# "- " bullet lists -- a run of consecutive lines becomes one paragraph joined
# with <br>, which is why the includes list carries no dashes. A link alone on
# its line becomes a centred gold CTA button; a link inside a sentence stays
# inline. Both are used deliberately below.
# ---------------------------------------------------------------------------
STEPS = [
    dict(
        target='website-inquiry-day0', delay=(0, 'minutes'),
        subject="\U0001f5a4 You're in the right place",
        body="""Hi {{contact.first_name}}!

I am **so** excited you reached out about a boudoir session with us at JHP Boudoir.

Whether this is something you have been thinking about for years or you just had a little spark of *"maybe I could do this..."* — you are in the right place.

@@PHOTO@@

There are a lot of photographers you could have asked about this. You asked me. Thank you. That means more than you know. \U0001f495

Everything about the experience is right here — what is included, what it costs, how the day runs, and how to claim your spot on my calendar:

[Read your Session Guide →]({{guide_url}})

Your boudoir experience includes:

""" + INCLUDES + """

**You do not have to pay for it all at once.** Your images and products are purchased separately from the session fee, and every Collection can go on an **interest-free prepayment plan** — weekly, biweekly or monthly, whichever suits you. Would you rather pay in full? You are very welcome to do that instead. And you can book your session **up to 15 months in advance**, so a plan spreads across as many payments as you need to keep the amount manageable.

**Ready to chat?** Grab a time and bring every question you have — the practical ones and the nervous ones. No pressure and no obligation. \U0001f5a4

And if you already know you are ready to book — have a credit card handy! We will process your session fee retainer right on the call and get your booking started.

[Book my call →]({{calendar_url}})

Take your time reading through it, and if you have questions I am just a message away.

— Jess""",
        sms="""Hi {{contact.first_name}}! It's Jess at JHP Boudoir. I am so excited you reached out about a boudoir session!

Everything about the experience is right here - what's included, what it costs and how the day runs: {{guide_url}}

There are plenty of photographers you could've asked - thank you for inquiring with my studio!

Questions or Ready to Book? Let's Chat: {{calendar_url}}

Msg frequency varies. Msg & data rates may apply. Reply STOP to opt out, HELP for help.""",
    ),
    dict(
        target='website-inquiry-24h', delay=(24, 'hours'),
        subject="Did your guide land?",
        body="""Hi {{contact.first_name}}!

Just making sure the Session Guide reached you — it sometimes hides in your spam folder.

[Your Session Guide →]({{guide_url}})

@@PHOTO@@

And in case it helps to hear it: the thing women say most on that first call is some version of *"I'm not sure I'm the kind of person who does this."*

Nearly every single one. You do not need to be brave, or in shape, or photogenic. You just need to show up — I will do the rest, and you will love every minute of it. This is a full service boudoir studio, and I will take great care of you throughout your boudoir experience.

Bring your questions and we will go through them together.

[Book my call →]({{calendar_url}})

— Jess""",
        sms="""Hey, {{contact.first_name}}! Just checking to see if your session guide arrived? It sometimes hides in your spam folder! {{guide_url}}

You do not need to be brave, or in shape, or photogenic - you just need to show up. This is a full service boudoir studio and I will take great care of you the whole way through.

Any questions at all, reply right here or book a call! Talk soon!

{{calendar_url}} - Jess

Reply STOP to opt out.""",
    ),
    dict(
        target='website-inquiry-72h', delay=(72, 'hours'),
        subject="What if I'm nervous?",
        body="""Hi {{contact.first_name}},

Totally normal to be nervous. **Everyone** is.

But nervous turns into empowered real quick, and you will leave feeling like a damn goddess. That is just what happens in my studio.

*"But I don't look like the women in your portfolio."*

You do. The women in my galleries are teachers and nurses and mothers and grandmothers, and not one of them walked in feeling ready. What they had was two hours, professional hair and makeup, and someone telling them exactly what to do with their hands.

@@PHOTO@@

> *"Jessica is amazing! Such a lovely day. She is so fun and professional! She really makes the studio a safe and comfortable place!"*

**And what if I don't know how to pose?** You don't need to. That is literally my job. I guide you the entire time — hands, hips, face, everything.

[The things women worry about →]({{guide_url}}#worries)

[Book my call →]({{calendar_url}})

— Jess""",
        sms="""{{contact.first_name}}, the question everyone asks me: "what if I'm nervous?"

Totally normal to be nervous. Everyone is! And you don't need to know how to pose - that is literally my job. I guide you the entire time.

Being nervous is the best reason there is to book the call. Bring every worry you have and we will talk it all the way through - no pressure and no obligation.

Let's get you on the phone: {{calendar_url}}

- Jess

Reply STOP to opt out.""",
    ),
    dict(
        target='website-inquiry-7d', delay=(7, 'days'),
        subject="What your session day actually looks like",
        body="""Hi {{contact.first_name}}!

It has been a week since you inquired with the studio, and I would love to get your call on the books! So here is the whole thing, start to finish.

**Hair and makeup first**, at a local salon — you drive over to the studio already done and gorgeous.

**Then we photograph**, two to three hours, just the two of us. Be prepared to be sore afterwards. We do a lot of bending and twisting — it is quite the workout! \U0001f605

**Then you go home.** Your images come later, at a private Zoom appointment where we go through every one of them together, one at a time. You are never sent a link and left to figure it out on your own.

That is the part women tell me afterwards was their favourite of the whole experience, and it is easily mine.

@@PHOTO@@

[How it all works →]({{guide_url}}#works)

Questions about any of it? Bring them all. Let's get you booked!

[Book my call →]({{calendar_url}})

— Jess""",
        sms="""{{contact.first_name}}, it's been a week since you inquired with the studio! Have you had a chance to read through your Session Guide yet? {{guide_url}}

Hair and makeup first at a local salon, then two to three hours in the studio, then your images at a private Zoom reveal where we go through every one together. You are never sent a link and left to figure it out on your own.

Any questions I can answer for you? Let's get your call booked: {{calendar_url}}

- Jess

Reply STOP to opt out.""",
    ),
    dict(
        target='website-inquiry-14d', delay=(14, 'days'),
        subject="Let's talk about the investment",
        body="""Hi {{contact.first_name}},

It has been two weeks since you reached out to the studio, so I wanted to check in with you again!

@@PHOTO@@

And I would much rather you knew what this costs before we talk than after. So, plainly:

**The session fee is $697.** It is non-refundable, it reserves your date, and it covers everything — the studio, hair and makeup, the wardrobe, the full session, retouching, and your reveal and ordering appointment.

**Your images and products are purchased separately**, at your reveal. Digital Collections begin at **$1,250**, and Full Collections — album, digitals, mobile app, wall art and more — begin at **$3,400**. There are eight in all, so there is room to find the one that fits.

**Got a little sticker shock?** Totally get it. Most of my clients feel that way at first. \U0001f64c

Here is the good news: you do not have to pay for it all at once. Every Collection can go on an **interest-free prepayment plan** — weekly, biweekly or monthly, whichever suits you — or you can pay in full if you would rather. A plan is set up within 7 days of booking, and your first payment is due within 30 days.

And you can book your session **up to 15 months in advance**, which matters more than it sounds. The further out your date, the more payments your plan spreads across — and that is what keeps the amount manageable for most women.

[Every figure, written down →]({{guide_url}}#investment)

If a number raises a question, bring it. No pressure and no obligation! Let's get on the phone and work through any questions you have!

[Book my call →]({{calendar_url}})

— Jess""",
        sms="""{{contact.first_name}}! It's been two weeks since you reached out. I just sent over everything about the investment - the session fee, the Collections and the interest-free payment plans, all written down.

And you can book up to 15 months out, so your plan spreads across as many payments as you need to keep it manageable.

If a number raises a question, bring it. No pressure and no obligation!

I would absolutely love to get your session on the books. Let's find a time to chat: {{calendar_url}}

- Jess

Reply STOP to opt out.""",
    ),
    dict(
        target='website-inquiry-1mo', delay=(30, 'days'),
        subject="I haven't forgotten about you \U0001f5a4",
        body="""Hi {{contact.first_name}},

It has been a month since you reached out — and I have not forgotten about you!

Here is the thing about why women finally book. It is rarely a birthday, though a birthday is a wonderful reason. It is usually that they got tired of waiting to feel ready.

> *"The confidence boost I had from this experience was unparalleled!"*

> *"Jessica was fabulous from the very first contact to the image reveal!"*

If you are still thinking about it a month later, {{contact.first_name}}, that is generally your answer.

@@PHOTO@@

**So let's get your session on the books.** Pick a time that suits you and we will talk the whole thing through — the date, the Collections, the payment plan, all of it. You can book as far out as 15 months, so we can put your date wherever it suits you and spread the plan across the months in between.

[Book my call →]({{calendar_url}})

I would love to welcome you into the studio. \U0001f5a4

— Jess""",
        sms="""{{contact.first_name}}, it's been 30 days - and I haven't forgotten about you!

Women rarely book because of a birthday. They book because they got tired of waiting to feel ready. If you are still thinking about it a month later, that is generally your answer.

I would love to welcome you into the studio. Let's get your call booked and your session on the calendar: {{calendar_url}}

- Jess

Reply STOP to opt out.""",
    ),
    dict(
        target='website-inquiry-3mo', delay=(90, 'days'),
        subject="Three months on — what can I answer for you?",
        body="""Hi {{contact.first_name}}!

It has been three months since you reached out about a session with us, and I wanted to check in. **What questions can I answer for you?**

In case it helps to see it again, here is what your experience includes:

""" + INCLUDES + """

@@PHOTO@@

And you do not have to pay for it all at once. Every Collection can go on an **interest-free prepayment plan** — weekly, biweekly or monthly, set up within 7 days of booking, with your first payment due within 30 days — or you can pay in full if you would rather. You can book your session **up to 15 months in advance**, too, so a plan spreads across as many payments as you need to keep the amount manageable.

You have been thinking about this for three months, {{contact.first_name}}. Let's do it!

[Book my call →]({{calendar_url}})

No obligation, just a conversation.

— Jess""",
        sms="""{{contact.first_name}}, three months since you reached out! What questions can I answer for you?

Your experience includes the studio, hair and makeup at a local salon beforehand, the full wardrobe - 160 pieces, XS to 4X - your session with me posing you head to pointed toe, retouching, and your private image reveal and ordering appointment.

And you do not have to pay for it all at once. Every Collection can go on an interest-free prepayment plan - weekly, biweekly or monthly - or you can pay in full if you would rather. You can book up to 15 months out, so the amount stays manageable.

You have thought about it. Let's do it! Book a no-obligation call: {{calendar_url}}

- Jess

Reply STOP to opt out.""",
    ),
    dict(
        target='website-inquiry-6mo', delay=(180, 'days'),
        subject="My door is always open \U0001f5a4",
        body="""Hi {{contact.first_name}},

This is the last time I will reach out, so I wanted to make it count.

Thank you for thinking of my studio in the first place. With everywhere you could have looked, that still means a great deal to me.

**My door is always open to you.** Next month, next year, whenever the time is right — I would love to have you in.

@@PHOTO@@

[Book my call →]({{calendar_url}})

You are worth it, {{contact.first_name}}. Truly. And I would be honored to be the one who captures you.

— Jess""",
        sms="""{{contact.first_name}}, this is my last message - but my door is always open.

Thank you for thinking of my studio in the first place. With everywhere you could have looked, that means a great deal to me.

Next month, next year, whenever the time is right - I would love to have you in. You are worth it, and I would be honored to be the one who captures you.

{{calendar_url}} - Jess

Reply STOP to opt out.""",
    ),
]

LABELS = {
    'website-inquiry-day0': 'Immediately — welcome, the guide, the plan',
    'website-inquiry-24h': '24 hours — did your guide land',
    'website-inquiry-72h': '72 hours — what if I am nervous',
    'website-inquiry-7d': '7 days — what the session day looks like',
    'website-inquiry-14d': '14 days — the investment',
    'website-inquiry-1mo': '1 month — I have not forgotten about you',
    'website-inquiry-3mo': '3 months — touch base',
    'website-inquiry-6mo': '6 months — final call, door stays open',
}

DESCRIPTION = (
    "Eight-touch follow-up for a woman who fills in the Session Guide form on "
    "/contact -- immediately, then 24h, 72h, 7d, 14d, 1 month, 3 months and "
    "6 months, each message doing a different job (welcome, reassure, name the "
    "fear, walk the day, the investment, ask for the booking, touch base, close "
    "the door gently). Replaces the Dubsado 'Inquiry - Website' workflow, which "
    "sent the same 700-word email six times and contradicted the site's figures "
    "in nine places. Enrolled by enroll-website-inquiry off site_leads; exited "
    "by website-inquiry-stopgate. EMAIL ONLY until /contact carries an SMS "
    "consent line -- every text is written and parked in action_config.sms."
)

TRIGGER_NOTES = (
    "Automatic. /contact POSTs to webhook site-lead-submit -> workflow "
    "site-leads-ingest writes a site_leads row and upserts the GHL contact "
    "tagged 'Session Guide - Requested'. enroll-website-inquiry (cron, every "
    "5 min) picks that row up and enrolls her at step 1 with next_action_at=NOW, "
    "so the welcome email goes out on the next jhp-workflow-runner pass."
)


def connect():
    return psycopg2.connect(
        dbname=os.environ['PGDATABASE'], user=os.environ['PGUSER'],
        host=os.environ['PGHOST'], cursor_factory=psycopg2.extras.RealDictCursor)


def body_of(step):
    """The step's body with its photograph substituted in.

    The placeholder exists so the frame table stays the one place a photograph
    is named, and so check(), main() and the render probe cannot disagree about
    what was installed.
    """
    return (step['body'].replace('@@PHOTO@@', photo(step['target']))
            + '\n\n' + INSTAGRAM)


def check():
    """Refuse to install rather than ship a wrong figure or an emoji text."""
    problems = []
    frames_seen = {}
    for i, s in enumerate(STEPS, start=1):
        t = s['target']
        body = body_of(s)
        if '@@PHOTO@@' in body:
            problems.append(f"{t}: photograph placeholder not substituted")
        if body.count('](' + CDN) != 1:
            problems.append(f"{t}: expected exactly one photograph, found "
                            f"{body.count('](' + CDN)}")
        frame = FRAMES[t][0]
        if frame in frames_seen:
            problems.append(f"{t}: reuses the frame already in "
                            f"{frames_seen[frame]} -- one frame per email")
        frames_seen[frame] = t
        if not FRAMES[t][1].strip():
            problems.append(f"{t}: photograph has no alt text")
        blob = s['subject'] + '\n' + body + '\n' + s['sms']
        for bad in STALE:
            if bad.lower() in blob.lower():
                problems.append(f"{t}: superseded figure {bad!r}")
        for field in ('subject', 'body', 'sms'):
            if not (s.get(field) or '').strip():
                problems.append(f"{t}: empty {field}")
        # SMS COMPLIANCE IS NOT COPY AND MAY NOT BE TRIMMED FOR LENGTH.
        # Every marketing text needs a visible opt-out; the first one, which is
        # the one that opens the relationship, needs the full disclosure. These
        # are the texts a carrier audit looks at, and the segment count is not a
        # reason to drop any of it.
        if 'Reply STOP to opt out' not in s['sms']:
            problems.append(f"{t}: the text has no 'Reply STOP to opt out'")
        if i == 1:
            for phrase in ('Msg & data rates may apply', 'Msg frequency varies',
                           'HELP for help', 'JHP Boudoir'):
                if phrase not in s['sms']:
                    problems.append(f"{t}: the first text is missing the "
                                    f"disclosure phrase {phrase!r}")
        # Her rule: no emoji in any text. Also protects against an SMS being
        # upgraded to MMS by the carrier.
        for ch in s['sms']:
            if ord(ch) > 0x2100 and unicodedata.category(ch) in ('So', 'Sk'):
                problems.append(f"{t}: emoji {ch!r} in the text")
        for tok in re.findall(r'\{\{\s*([^}|]+?)\s*(?:\|[^}]*)?\}\}', blob):
            if tok.strip().lower() not in KNOWN_TOKENS:
                problems.append(f"{t}: unknown merge token {{{{{tok}}}}}")
        # A link the runner would render as a dead button.
        for url in re.findall(r'\]\(([^)]*)\)', body):
            if not (url.startswith('{{') or url.startswith('http')):
                problems.append(f"{t}: link target {url!r} is neither a token nor a URL")
    targets = [s['target'] for s in STEPS]
    if len(set(targets)) != len(targets):
        problems.append("duplicate step targets")
    if problems:
        for p in problems:
            log.error(p)
        raise SystemExit(f"{len(problems)} problem(s) -- nothing installed")
    log.info(f"checks passed: {len(STEPS)} steps, "
             f"{'email + SMS' if SEND_SMS else 'EMAIL ONLY (SMS parked)'}")


def main():
    check()
    kind = 'send_email_sms' if SEND_SMS else 'send_email'
    conn = connect()
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM jhp_workflows WHERE name=%s", (WF_NAME,))
            row = cur.fetchone()
            if row:
                wid = row['id']
                cur.execute(
                    "UPDATE jhp_workflows SET display_name=%s, description=%s, "
                    "source='scalogy', migration_status='live', is_active=true, "
                    "trigger_kind='automation', trigger_notes=%s, updated_at=NOW() "
                    "WHERE id=%s",
                    (WF_DISPLAY, DESCRIPTION, TRIGGER_NOTES, wid))
                log.info(f"updated workflow {wid}")
            else:
                cur.execute(
                    "INSERT INTO jhp_workflows (name, display_name, description, source, "
                    "migration_status, is_active, trigger_kind, trigger_notes) "
                    "VALUES (%s,%s,%s,'scalogy','live',true,'automation',%s) RETURNING id",
                    (WF_NAME, WF_DISPLAY, DESCRIPTION, TRIGGER_NOTES))
                wid = cur.fetchone()['id']
                log.info(f"created workflow {wid}")

            # Steps are rebuilt wholesale: this script is the definition of
            # record, so a hand edit in the DB is not something to merge with.
            cur.execute("DELETE FROM jhp_workflow_steps WHERE workflow_id=%s", (wid,))
            for i, s in enumerate(STEPS, start=1):
                amount, unit = s['delay']
                cfg = {'subject': s['subject'], 'body_md': body_of(s),
                       'sms': s['sms']}
                cur.execute(
                    "INSERT INTO jhp_workflow_steps (workflow_id, position, label, kind, "
                    "action_kind, action_target, action_config, delay_amount, delay_unit, "
                    "delay_relative_to, trigger_text) "
                    "VALUES (%s,%s,%s,'action',%s,%s,%s::jsonb,%s,%s,'enrollment',%s)",
                    (wid, i, LABELS[s['target']], kind, s['target'], json.dumps(cfg),
                     amount, unit, f"{amount} {unit} after she submits the form"))
                log.info(f"  step {i}: {s['target']} (+{amount} {unit}) {kind}")
        conn.commit()
        log.info(f"done - {WF_DISPLAY} installed with {len(STEPS)} steps")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
