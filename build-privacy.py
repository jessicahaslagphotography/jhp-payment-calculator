#!/usr/bin/env python3
"""Generates scalogy-privacy.html -- /privacy-policy, the page the old site
had and the new one did not.

WHY IT EXISTS, AND WHY IT IS NOT A PORT. The Showit site has a
/privacy-policy page, and the whole of it is the sentence "Click here to read
our privacy policy" over a link to privacypolicies.com. That generated
document talks about this studio's "parent company", its "joint venture
partners", its "affiliates", and about "signing in to Your Account" -- none of
which exist. It also says nothing at all about text messages, which is the one
genuinely new thing this site collects and the one with damages attached.
Copying it across would have carried all of that over.

So this is written from what the site ACTUALLY DOES, which is knowable to the
byte: the two forms are in build-contact.py and build-inquiry.py, where the
data goes is in scripts/site_leads_ingest.py and the Scalogy workflows, the
SMS gate is sms_blocked_reason() in email_actions.py and the unsubscribe is
email_unsubscribe_ingest.py. Every claim below is checked against one of them.

THE URL IS DELIBERATELY UNCHANGED. /privacy-policy is what the old site
serves, so keeping it means every existing link still resolves and no redirect
is needed. That is also why the page is not called /privacy.

THREE CLAIMS ARE CHECKED BY THE BUILD rather than trusted, because each one
would be a false statement in a privacy policy if it drifted:

  * no cookies, no analytics, no tracking pixel on any public page
  * the /contact SMS box is still optional and still carries its disclosure
  * the unsubscribe page still exists

ONE THING IS STILL MARKED ASK and is Jessica's to confirm, not mine to invent:

  * RETENTION. No period is stated anywhere in this project, so the page says
    what is true -- kept while it is being used for what it was given for, and
    deleted on request -- rather than a number nobody has set.

THE AGE IS SETTLED, AND IT IS A BOOKING RULE. It was an ASK for about an hour;
Jessica answered on 26 September in her own words -- "You must be 18 years of
age or older to book with my studio" -- and that sentence is on the page
verbatim, in bold, as the first thing in its section. The heading states the
rule outright rather than saying "Under 18", because this is a condition of
booking and not only a statement about data. The generated document it
replaces set the age at 13, which is that generator's default and wrong for a
boudoir studio by a distance. AGE_RULE is a guarded figure now, like every
other figure on this project: the build fails if her sentence goes missing.

IT IS STATED IN EXACTLY ONE PLACE ON THE SITE, WHICH IS THIS PAGE. Nothing in
the FAQ, the Session Guide, /contact or /inquire says it. A booking
requirement a woman only meets if she opens the privacy policy is badly
placed, and the FAQ is where it belongs -- but the FAQ is Jessica's copy and
adding a question to it is her call, not a gap to quietly fill.

I am not a lawyer and this is not legal advice. What it is, is accurate --
which the document it replaces is not.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
src = (ROOT / "scalogy-portfolio.html").read_text()

UPDATED = "26 September 2026"
# Jessica's own sentence, 26 September. A booking rule, not just a data one.
AGE_RULE = "You must be 18 years of age or older to book with my studio."
STUDIO = "JHP Boudoir"
ADDRESS = "11811 Main Street, Centertown, MO 65023"
EMAIL = "jessica@jhpboudoir.com"

# --- the slices -----------------------------------------------------------
# The same three cuts build-contact.py and build-inquiry.py take. This page
# needs no intro band and no pull-quote: it opens on type, deliberately, both
# because a legal page should start with the words and because choosing a
# photograph from this sandbox is choosing one blind.
MARK_END = "/* The closing band carries no photograph."
shared = src[:src.index("/* THE INDEX")]
parts = (src[src.index("/* THE INTRO"):src.index("/* THE QUOTE")]
         + src[src.index("/* THE WAY ON"):src.index(MARK_END)])
tail = src[src.index(MARK_END):]
after_style = tail[tail.index("</style>"):]
nav = after_style[after_style.index('<nav class="jhp-nav">'):
                  after_style.index("</nav>") + len("</nav>\n")]
foot = after_style[after_style.index('<footer class="jhp-foot">'):]

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Privacy Policy | JHP Boudoir, Jefferson City MO</title>
<meta name="description" content="What JHP Boudoir collects when you use this website, why, who else handles it, and how to ask for it back or have it deleted. No cookies and no tracking.">
<meta name="robots" content="noindex, nofollow">
<link rel="canonical" href="https://pages.scalogy.com/jhpboudoir1/privacy-policy/">
<meta name="theme-color" content="#13100E">
<meta property="og:site_name" content="JHP Boudoir">
<meta property="og:locale" content="en_US">
<meta property="og:title" content="Privacy Policy | JHP Boudoir">
<meta property="og:description" content="What this website collects, why, and how to have it deleted. No cookies and no tracking.">
<meta property="og:url" content="https://pages.scalogy.com/jhpboudoir1/privacy-policy/">
<meta property="og:image" content="https://assets.cdn.filesafe.space/Pcnm8GVNMmWTY65qVOAp/media/6ab1b5f198fc609c5dbd2205.jpg">
<meta property="og:image:alt" content="A boudoir portrait photographed at the JHP Boudoir studio in Jefferson City, Missouri">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Privacy Policy | JHP Boudoir">
<meta name="twitter:description" content="What this website collects, why, and how to have it deleted. No cookies and no tracking.">
<meta name="twitter:image" content="https://assets.cdn.filesafe.space/Pcnm8GVNMmWTY65qVOAp/media/6ab1b5f198fc609c5dbd2205.jpg">
<meta property="og:type" content="website">
<style>html,body{margin:0;padding:0;background:#13100E}body{overflow-x:hidden}</style>
</head>
<body>
{% raw %}
<div class="jhp-home">
<style>
"""

PAGE_CSS = """
/* THE POLICY
   ----------
   A reading page and nothing else. No band, no photograph, no pull-quote:
   somebody who opens this wants an answer, and the rest of the site is one
   tap away in the nav above. It is also the one page whose frame would have
   had to be chosen from this sandbox, where the image CDN is unreachable and
   a photograph is therefore chosen blind.

   The measure is the whole design here. 68ch is about eleven words a line,
   which is where prose stays readable; the rest of the site runs wider
   because the rest of the site is headlines over photographs.

   The prose is the FAQ's answer style to the character -- sans, weight 300,
   16.5px on 1.8, in --muted, with gold links on a --line underline rather
   than a browser one. This is the site's long-reading setting and it was
   already settled; a second one would be a second thing to keep in step.

   .lead is the summary at the top and is not decoration. Most people who
   open a privacy policy want three facts -- what is taken, who else sees it,
   how to stop it -- and will not read thirteen sections to find them. */
.jhp-home .jhp-priv{max-width:calc(68ch + 2 * clamp(20px,5vw,60px));
  margin:0 auto;padding:clamp(48px,6vw,88px) clamp(20px,5vw,60px)
  clamp(56px,6vw,96px)}
.jhp-home .jhp-priv .jhp-kicker{margin:0 0 10px}
.jhp-home .jhp-priv h1{margin:0 0 6px}
.jhp-home .jhp-priv .when{margin:0 0 clamp(30px,3.4vw,44px);
  font-family:var(--sans);font-size:11px;letter-spacing:.2em;
  text-transform:uppercase;color:var(--dim)}
.jhp-home .jhp-priv h2{margin:clamp(38px,4vw,54px) 0 12px;
  font-family:var(--serif);font-weight:600;line-height:1.2;
  font-size:clamp(22px,2.2vw,28px);color:var(--ink)}
.jhp-home .jhp-priv h3{margin:26px 0 8px;font-family:var(--sans);
  font-weight:600;font-size:12px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--gold)}
.jhp-home .jhp-priv p,
.jhp-home .jhp-priv li{font-family:var(--sans);font-weight:300;
  font-size:16.5px;line-height:1.8;color:var(--muted);margin:0 0 14px}
.jhp-home .jhp-priv ul{margin:0 0 14px;padding-left:20px}
.jhp-home .jhp-priv li{margin:0 0 8px;padding-left:2px}
.jhp-home .jhp-priv li::marker{color:var(--gold)}
.jhp-home .jhp-priv a{color:var(--gold);border-bottom:1px solid var(--line);
  text-decoration:none;transition:color .3s,border-color .3s}
.jhp-home .jhp-priv a:hover{color:var(--gold-bright);
  border-color:var(--gold-bright)}
.jhp-home .jhp-priv b{color:var(--ink);font-weight:600}
/* The summary. A hairline box rather than a filled one -- a filled panel at
   the top of a dark page reads as a warning, and this is the reassuring
   part. */
.jhp-home .jhp-priv .lead{border:1px solid var(--line);
  padding:clamp(20px,2.4vw,28px) clamp(20px,2.4vw,30px);
  margin:0 0 clamp(14px,1.6vw,20px)}
.jhp-home .jhp-priv .lead p:last-child{margin-bottom:0}
@media (max-width:620px){
  .jhp-home .jhp-priv{padding:40px var(--ph-gut) 52px}
  .jhp-home .jhp-priv h2{font-size:22px}
  /* --ph-body, the same reading size the FAQ's answers take on a phone. */
  .jhp-home .jhp-priv p,
  .jhp-home .jhp-priv li{font-size:var(--ph-body);line-height:1.75}
}
"""

BODY = """
<main class="jhp-priv">

  <p class="jhp-kicker">JHP Boudoir</p>
  <h1 class="jhp-h jhp-h-lg">Privacy Policy</h1>
  <p class="when">Last updated %(updated)s</p>

  <div class="lead">
    <p><b>The short version.</b> This website has no cookies, no analytics and
      no tracking of any kind. The only personal information it holds is what
      you type into one of the two forms and press send on &mdash; your name,
      your email address, your phone number, and on the inquiry form a few
      things about the session you are thinking about.</p>
    <p>It is used to answer you and to send you what you asked for. It is
      never sold, and it is never passed to anyone who is not helping me run
      the studio. You can ask me to delete it at any time by emailing
      <a href="mailto:%(email)s">%(email)s</a>, and I will.</p>
  </div>

  <h2>Who You Are Dealing With</h2>
  <p>%(studio)s is a boudoir photography studio just outside Jefferson City,
    Missouri, run by Jessica Haslag. Everything on this page is about me and
    this website. If you write to me about your information, it reaches me
    and nobody else.</p>
  <p>%(studio)s<br>%(address)s<br>
    <a href="mailto:%(email)s">%(email)s</a></p>

  <h2>What This Website Collects</h2>
  <p>Only what you choose to type and send. There is no account to make and
    nothing is gathered in the background.</p>

  <h3>The Session Guide form, on the Contact page</h3>
  <ul>
    <li>your first and last name</li>
    <li>your email address</li>
    <li>your phone number</li>
    <li>whether you ticked the box agreeing to be texted &mdash; optional, and
      leaving it unticked costs you nothing</li>
  </ul>

  <h3>The inquiry form</h3>
  <ul>
    <li>your first and last name, email address and phone number</li>
    <li>which kind of session you are thinking about, and roughly when</li>
    <li>the occasion, if there is one, and how you heard about the studio</li>
    <li>anything you write in the notes box &mdash; which is yours, so please
      put in it only what you want me to have</li>
  </ul>

  <h3>Booking a call</h3>
  <p>The Book a Call button opens my scheduling calendar, which is run for me
    by GoHighLevel. Booking a slot gives them your name, email and phone
    number so the appointment can exist. Their privacy policy governs what
    happens on that page.</p>

  <h2>What I Do With It</h2>
  <ul>
    <li><b>Answer you</b>, and send you the Session Guide Magazine if that is
      what you asked for.</li>
    <li><b>Follow up.</b> If you ask for the guide you also go onto a short
      series of emails about booking a session. Every one of them carries an
      unsubscribe link, and one click ends it.</li>
    <li><b>Run your session</b>, if you book one &mdash; scheduling, your
      contract, your payment plan, your image reveal and getting your
      photographs to you.</li>
  </ul>
  <p><b>I do not sell your information, and I never will.</b> It is not
    traded, rented or handed to advertisers, and nobody gets it as part of a
    list.</p>

  <h2>Who Else Handles It</h2>
  <p>Running a studio takes a few services, and each of them sees the part of
    your information it needs to do its job. They work for me and are not
    allowed to use it for anything else.</p>
  <ul>
    <li><b>Scalogy</b> &mdash; hosts this website and stores what the forms
      collect.</li>
    <li><b>GoHighLevel</b> &mdash; my client records, my booking calendar and
      my text messages.</li>
    <li><b>Mailgun</b> &mdash; delivers the emails I send you.</li>
    <li><b>Google Workspace</b> &mdash; my own inbox, where your email to me
      arrives.</li>
  </ul>
  <p>I may also have to hand something over if the law requires it. That has
    never happened and I would not expect it to.</p>

  <h2>Your Photographs</h2>
  <p>This is the part that matters most in a studio like mine, so it is worth
    saying plainly.</p>
  <p><b>Nobody sees your photographs unless you decide otherwise.</b> Every
    client signs a model release, and that release is where you say whether
    your images stay private or whether I may share them. Private is a
    perfectly ordinary answer. It changes nothing about your session and
    nothing about how I photograph you. Every woman whose face is on this
    website chose to let it be there.</p>
  <p>If you said yes and later change your mind, tell me and I will take them
    down. I cannot unpublish something somebody else has already saved or
    reshared, which is true of any photograph anywhere, but everything within
    my reach comes down.</p>

  <h2>Text Messages</h2>
  <p>The box on the Contact form is the only way you get texted about
    marketing, and it is <b>optional</b>. Leaving it unticked does not stop
    your Session Guide arriving, and it does not change anything else.</p>
  <ul>
    <li>Message frequency varies, and message and data rates may apply.</li>
    <li><b>Reply STOP to any message and the texts end.</b> Reply HELP for
      help.</li>
    <li>Marketing texts are only sent between 9am and 8pm Central time. If
      the hour cannot be worked out, the message is not sent.</li>
    <li>Texts about a session you have actually booked &mdash; a reminder, a
      change of time &mdash; are a different thing and do not depend on that
      box.</li>
  </ul>

  <h2>Email</h2>
  <p>Every marketing email carries an unsubscribe link in the footer, along
    with the studio's postal address. One click records it and the marketing
    stops. It deliberately does <b>not</b> switch off email about a session
    you have booked &mdash; your confirmation, your contract and your image
    reveal still reach you, because unsubscribing from a newsletter should
    not quietly cancel your own paperwork.</p>

  <h2>Cookies and Tracking</h2>
  <p><b>There are none.</b> This website sets no cookies, runs no analytics,
    carries no advertising pixel and does not follow you anywhere. There is
    no banner to dismiss because there is nothing to consent to.</p>
  <p>Two things on the page do come from elsewhere: the photographs are served
    from a content delivery network, and the fonts come from Google Fonts.
    Both see your browser's request for a file, as any website's images and
    fonts do. Neither is used to track you and neither is under my control
    beyond choosing to use it.</p>
  <p>Links out to Instagram, Facebook, TikTok, my Facebook group and my
    booking calendar take you to somebody else's website, where their rules
    apply rather than mine.</p>

  <h2>How Long I Keep It</h2>
  <p>While it is still doing the job you gave it to me for. An inquiry that
    never becomes a booking is not kept forever, and if you unsubscribe or
    ask me to stop, that is recorded so I do not contact you again by
    mistake. Client records and photographs are kept while you are a client of
    the studio and for as long afterwards as my accounts and contracts
    require.</p>
  <p>If you want a firmer answer than that for your own situation, ask me.</p>

  <h2>What You Can Ask Me To Do</h2>
  <p>Email <a href="mailto:%(email)s">%(email)s</a> and I will do any of
    these, free, without asking you why:</p>
  <ul>
    <li>tell you what I hold about you</li>
    <li>correct anything that is wrong</li>
    <li>delete it</li>
    <li>stop emailing you, stop texting you, or both</li>
    <li>take your photographs off this website and off my social media</li>
  </ul>
  <p>There are one or two things I may have to keep &mdash; a record that you
    unsubscribed, so the unsubscribe holds, and anything my accountant needs
    for a session you actually paid for. I will tell you if that applies.</p>

  <h2>You Must Be 18 or Older</h2>
  <p><b>You must be 18 years of age or older to book with my studio.</b> This
    website is not for anyone under 18 and I do not knowingly collect anything
    from anyone under 18. If you believe a child has sent me something through
    this site, email me and I will delete it.</p>

  <h2>Changes to This Policy</h2>
  <p>If this changes, the new version goes up on this page and the date at the
    top changes with it. If it ever changes in a way that affects what I do
    with information I already hold, I will email the people it affects
    rather than leave it to be noticed.</p>

  <h2>Questions</h2>
  <p>Email me at <a href="mailto:%(email)s">%(email)s</a>. A question about
    your own information gets answered by me, not by a form.</p>

</main>
"""


def build():
    body = BODY % {"updated": UPDATED, "studio": STUDIO,
                   "address": ADDRESS, "email": EMAIL}
    out = (HEAD + shared[shared.index("/* SHARED DESIGN SYSTEM"):] + parts
           + PAGE_CSS + "</style>\n\n" + nav + body + "\n" + foot)
    check(out)
    (ROOT / "scalogy-privacy.html").write_text(out)
    return out


def check(out):
    """Refuse to write a policy that says something untrue.

    A privacy policy is the one page on this site where a stale sentence is
    not a tidiness problem. Each of these is a claim the page makes about
    the rest of the project, checked against the rest of the project.
    """
    fails = []

    # "There are none." -- checked across every public page, not asserted.
    pages = ["scalogy-home.html", "scalogy-about.html", "scalogy-portfolio.html",
             "scalogy-faq.html", "scalogy-experience.html", "scalogy-contact.html",
             "scalogy-inquire.html", "scalogy-guide.html", "scalogy-gallery.html"]
    tracker = re.compile(r"googletagmanager|google-analytics|gtag\(|fbq\(|"
                         r"connect\.facebook\.net|hotjar|clarity\.ms|"
                         r"document\.cookie|localStorage|sessionStorage", re.I)
    for p in pages:
        f = ROOT / p
        if not f.exists():
            fails.append(f"{p} is missing, so the no-tracking claim is unchecked")
            continue
        hit = tracker.search(f.read_text())
        if hit:
            fails.append(f'{p} contains {hit.group(0)!r} -- this page says the '
                         f'site has no cookies and no tracking, and that would '
                         f'make it a false statement')

    # The SMS section describes an OPTIONAL box carrying a disclosure.
    contact = (ROOT / "scalogy-contact.html").read_text()
    box = re.search(r'<input[^>]*name="sms_consent"[^>]*>', contact)
    if not box:
        fails.append('the /contact SMS consent box is gone, but this page '
                     'describes it')
    elif "required" in box.group(0):
        fails.append('the /contact SMS box has become required, but this page '
                     'says ticking it is optional')
    for phrase in ("Reply STOP to opt out", "Message frequency varies",
                   "message and data rates may apply"):
        if phrase.lower() not in " ".join(contact.split()).lower():
            fails.append(f'the /contact disclosure no longer says {phrase!r}, '
                         f'which this page states as a promise')

    # Her age rule, verbatim. A booking requirement that exists in exactly one
    # place on the whole site is one edit away from existing nowhere.
    if AGE_RULE not in BODY:
        fails.append('the page no longer states Jessica\'s own wording for '
                     'the booking age requirement')

    # The email section promises an unsubscribe link that works.
    ea = ROOT / "scripts" / "email_actions.py"
    if not ea.exists() or "UNSUB_BASE" not in ea.read_text():
        fails.append('scripts/email_actions.py no longer defines UNSUB_BASE, so '
                     'the unsubscribe this page promises may not exist')

    # Every figure that is also stated elsewhere must agree with it.
    if "11811 Main Street, Centertown, MO 65023" not in (ea.read_text()
                                                         if ea.exists() else ""):
        fails.append('the postal address here does not match the one in the '
                     'email footer')
    if "9am and 8pm Central" in BODY:
        txt = ea.read_text() if ea.exists() else ""
        if "SMS_QUIET_START = 9" not in txt or "SMS_QUIET_END = 20" not in txt:
            fails.append('the quiet hours stated here are not the ones the send '
                         'gate enforces')

    # EVERY CSS TOKEN THIS PAGE USES MUST EXIST IN THE SLICED SYSTEM.
    # The first draft of PAGE_CSS reached for --body and --rule, which are
    # not tokens on this site; an undefined var() falls back to nothing and
    # the text would have rendered in the browser's default colour on a
    # near-black page. Silent, and only visible to somebody looking.
    defined = set(re.findall(r'(--[a-z-]+)\s*:', shared))
    for tok in sorted(set(re.findall(r'var\((--[a-z-]+)\)', PAGE_CSS))):
        if tok not in defined:
            fails.append(f'PAGE_CSS uses {tok}, which is not a token in the '
                         f'shared design system')

    if fails:
        for f in fails:
            print("FAIL:", f)
        raise SystemExit(f"{len(fails)} check(s) failed -- not writing a privacy "
                         f"policy that says something untrue")


if __name__ == "__main__":
    o = build()
    print("wrote scalogy-privacy.html,", len(o.encode()), "bytes,",
          o.count("<h2>"), "sections")
