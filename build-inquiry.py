#!/usr/bin/env python3
"""Builds scalogy-inquire.html -- the booking inquiry form at /inquire.

WHAT THIS PAGE IS, AND HOW IT DIFFERS FROM /contact

Two forms, two different women, and the difference is worth keeping straight
because it is the whole reason this page exists.

  /contact is the Session Guide request. Four fields, no questions, and the
  lowest possible bar: she does not know yet whether she wants this. She gets
  the magazine and a calendar.

  /inquire is for the woman who already knows. She has read the guide or she
  does not need it. So this page may reasonably ask more -- which session,
  when, what for, and an acknowledgment of what the thing costs -- because
  every answer is one less thing to establish on the call.

Asking MORE has to be earned, and it is: Jessica's own guide says most clients
book over the phone and that the consultation is "kind of like our first
date". Everything this form collects is something she would otherwise spend
that call establishing.

THE ACKNOWLEDGMENT CARRIES NO NUMBER, DELIBERATELY. Her Session Guide PDF and
the website's own FAQ disagree about the figures -- the guide says a $500
session fee and Collections from $2,800; the FAQ says the session fee starts
at $697 with Digital Collections from $1,250. Both are Jessica's, one of them
is stale, and it is not this file's job to guess which. So the acknowledgment
uses her wording from the guide instead ("a quick shoot or just a few images,
this is not the session for you") and states the structure -- images are
bought separately from the session fee -- which is true in both versions.
Put a figure back only once the guide and the FAQ agree on one.

WHERE IT GOES. The form POSTs no-cors to the site-inquiry-submit webhook,
workflow site-inquiry-ingest writes a site_inquiries row and upserts the
contact into GHL tagged 'Session Inquiry'. That tag is the contract, exactly
as 'Session Guide - Requested' is for /contact: nothing here sends an email,
and if no GHL workflow watches the tag then the inquiry is captured and
silent. site_inquiries holds PII and must never be attached to an app.

IT ENDS ON A THANK-YOU, NOT A REDIRECT, and that is the one place this page
deliberately parts company with /contact. /contact goes straight to the
calendar because it collected four fields and owes her nothing; this form
asks nine questions including what she is spending, and throwing her at a
scheduler mid-thought reads as though nobody was listening. So she gets a
confirmation that repeats what happens next, with the calendar on a button.
Switching it to /contact's behaviour is one line -- see FORWARD below.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
CDN = "https://assets.cdn.filesafe.space/Pcnm8GVNMmWTY65qVOAp/media/"
src = (ROOT / "scalogy-portfolio.html").read_text()

# The design system, sliced rather than copied -- same three cuts
# build-contact.py takes, for the same reason: a shared rule changed on the
# portfolio must land here too, and a fourth copy of it would not.
MARK_END = "/* The closing band carries no photograph."
shared = src[:src.index("/* THE INDEX")]
parts = (src[src.index("/* THE INTRO"):src.index("/* THE QUOTE")]
         + src[src.index("/* THE WAY ON"):src.index(MARK_END)])
tail = src[src.index(MARK_END):]
after_style = tail[tail.index("</style>"):]
nav = after_style[after_style.index('<nav class="jhp-nav">'):
                  after_style.index("</nav>") + len("</nav>\n")]
foot = after_style[after_style.index('<footer class="jhp-foot">'):]

WEBHOOK = "https://app.scalogy.com/webhooks/in/jhpboudoir1/site-inquiry-submit"
CALENDAR = "https://api.leadconnectorhq.com/widget/booking/mi2EqYRq4gGEbBJHe82b"
# True makes this behave exactly like /contact: straight to the calendar on
# submit, no confirmation. See the note at the head of this file.
FORWARD = False

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Inquire About a Session | Jefferson City, MO | JHP Boudoir</title>
<meta name="description" content="Tell me about the boudoir session you have in mind and I will come back to you personally. Studio and outdoor sessions near Jefferson City, Missouri.">
<meta name="robots" content="noindex, nofollow">
<link rel="canonical" href="https://pages.scalogy.com/jhpboudoir1/inquire/">
<meta name="theme-color" content="#13100E">
<meta property="og:site_name" content="JHP Boudoir">
<meta property="og:locale" content="en_US">
<meta property="og:title" content="Inquire About a Session | JHP Boudoir">
<meta property="og:description" content="Tell me about the session you have in mind and I will come back to you personally.">
<meta property="og:url" content="https://pages.scalogy.com/jhpboudoir1/inquire/">
<meta property="og:image" content="{{CDN}}6ab3ee7718384d888bb3d80d.jpg">
<meta property="og:image:alt" content="A client photographed by candlelight at the JHP Boudoir studio">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Inquire About a Session | JHP Boudoir">
<meta name="twitter:description" content="Tell me about the session you have in mind and I will come back to you personally.">
<meta name="twitter:image" content="{{CDN}}6ab3ee7718384d888bb3d80d.jpg">
<meta property="og:type" content="website">
<style>html,body{margin:0;padding:0;background:#13100E}body{overflow-x:hidden}</style>
</head>
<body>
{% raw %}
<div class="jhp-home">
<style>
"""
print("scaffolding built:", len(shared), "shared,", len(parts), "parts")

# The form's look is SLICED OUT OF /contact, not copied. Both forms are the
# same object visually -- gold uppercase labels, hairline inputs on --surface,
# the 16px floor that stops mobile Safari zooming a focused field -- and two
# copies of that is two things to keep in step. build-contact.py owns those
# rules; this file borrows them, which means /contact must be built first.
contact = (ROOT / "scalogy-contact.html").read_text()
FORM_CSS = contact[contact.index("/* THE FORM"):contact.index('/* The band says')]

# Only what this page adds: three controls /contact has no use for. They
# inherit the input styling above rather than restating it.
EXTRA_CSS = """
/* SELECT, TEXTAREA AND THE ACKNOWLEDGMENT

   Everything here is a delta on the input rules sliced above -- same
   background, same hairline, same gold focus ring, same 16px floor. What is
   different is only what has to be.

   The select loses its native arrow (appearance:none) and gets the site's own
   chevron drawn as a background gradient pair, so it matches the one the Info
   menu wears rather than shipping whatever grey triangle the OS supplies. The
   padding-right leaves room for it. option is coloured explicitly because a
   dark select with default options renders black-on-black on Windows.

   The checkbox is a real <input type=checkbox>, not a styled span: it has to
   be focusable, it has to be in the tab order, and the browser's own
   :checked state is what the required attribute reads. accent-color tints it
   gold without taking over the control. */
.jhp-home .jhp-ask-form select,
.jhp-home .jhp-ask-form textarea{display:block;width:100%;box-sizing:border-box;
  padding:14px 15px;font-family:var(--sans);font-weight:300;font-size:16px;
  line-height:1.4;color:var(--ink);background:var(--surface);
  border:1px solid var(--line);border-radius:2px;appearance:none;
  transition:border-color .3s,background .3s}
.jhp-home .jhp-ask-form select:hover,
.jhp-home .jhp-ask-form textarea:hover{border-color:var(--gold)}
.jhp-home .jhp-ask-form select:focus,
.jhp-home .jhp-ask-form textarea:focus{outline:none;background:var(--raised);
  border-color:var(--gold-bright)}
.jhp-home .jhp-ask-form select:focus-visible,
.jhp-home .jhp-ask-form textarea:focus-visible{
  outline:2px solid var(--gold-bright);outline-offset:2px}
.jhp-home .jhp-ask-form select{padding-right:40px;cursor:pointer;
  background-image:
    linear-gradient(45deg,transparent 50%,var(--muted) 50%),
    linear-gradient(135deg,var(--muted) 50%,transparent 50%);
  background-position:calc(100% - 20px) 50%,calc(100% - 15px) 50%;
  background-size:5px 5px,5px 5px;background-repeat:no-repeat}
.jhp-home .jhp-ask-form select option{background:var(--surface);color:var(--ink)}
.jhp-home .jhp-ask-form textarea{min-height:104px;resize:vertical;
  line-height:1.6}

/* The acknowledgment. A row rather than a block so the box sits on the first
   line of its own sentence at any width, and the whole thing is a <label>, so
   the sentence is the tap target as well as the box -- 15px of checkbox is
   not something to ask a thumb to find. */
.jhp-home .jhp-ask-form .ack{display:flex;align-items:flex-start;gap:12px;
  margin:22px 0 0;padding:16px 18px;cursor:pointer;
  background:var(--surface);border:1px solid var(--line);border-radius:2px;
  transition:border-color .3s}
.jhp-home .jhp-ask-form .ack:hover{border-color:var(--gold)}
.jhp-home .jhp-ask-form .ack input{flex:0 0 auto;width:17px;height:17px;
  margin:2px 0 0;accent-color:var(--gold);cursor:pointer}
.jhp-home .jhp-ask-form .ack span{font-family:var(--sans);font-weight:300;
  font-size:14.5px;line-height:1.65;color:var(--muted)}
.jhp-home .jhp-ask-form .ack input:focus-visible{
  outline:2px solid var(--gold-bright);outline-offset:3px}
/* A required checkbox that has never been touched must not be painted as an
   error, exactly as with the text inputs above. :user-invalid only fires once
   the browser has actually validated it. */
.jhp-home .jhp-ask-form .ack:has(input:user-invalid){border-color:#B4614B}
.jhp-home .jhp-ask-form .opt{font-size:10px;letter-spacing:.14em;
  color:var(--dim);margin-left:8px}

@media (max-width:620px){
  .jhp-home .jhp-ask-form select,
  .jhp-home .jhp-ask-form textarea{font-size:16px}
  .jhp-home .jhp-ask-form .ack{padding:14px 15px}
  .jhp-home .jhp-ask-form .ack span{font-size:14px}
}
"""

BODY = """
<section class="jhp-intro">
  <img src="{{CDN}}6ab3ee7718384d888bb3d80d.jpg"
       width="2048" height="1363"
       alt="A client photographed by candlelight at the JHP Boudoir studio, Jefferson City, Missouri">
  <div class="jhp-over">
    <p class="jhp-kicker">Inquire</p>
    <h1 class="jhp-h jhp-h-lg">Tell Me About Your Session</h1>
  </div>
</section>

<section class="jhp-sec" style="border-bottom:none">
  <!-- Two paragraphs, on the /contact pattern: one thought each, and no
       heading over them because the band's h1 already heads the page.
       Both facts here are Jessica's own, out of the Session Guide -- the
       two-to-three-day reply window and the consultation being "kind of
       like our first date". Neither is invented, and neither restates a
       figure the guide and the FAQ currently disagree about. -->
  <div class="jhp-center">
    <p class="jhp-p">Fill this in and it comes straight to me. I answer
       personally, usually within two or three business days.</p>
    <p class="jhp-p">Then we talk. Most women book over the phone, and that
       call is a bit like a first date &mdash; twenty minutes to make sure
       this is right for you, and to answer anything this page has not.</p>
  </div>

  <form class="jhp-ask-form" id="jhp-inq" novalidate>
    <div class="row">
      <label class="f">
        <span class="lb">First Name</span>
        <input type="text" name="first" autocomplete="given-name"
               placeholder="Jane" required>
      </label>
      <label class="f">
        <span class="lb">Last Name</span>
        <input type="text" name="last" autocomplete="family-name"
               placeholder="Smith" required>
      </label>
    </div>
    <div class="row">
      <label class="f">
        <span class="lb">Email</span>
        <input type="email" name="email" autocomplete="email"
               placeholder="jane@example.com" required>
      </label>
      <label class="f">
        <span class="lb">Phone</span>
        <input type="tel" name="phone" autocomplete="tel"
               placeholder="(573) 000-0000" required>
      </label>
    </div>

    <!-- The two session types are Jessica's own, from the guide: studio
         year round, outdoor on summer dates only. "Not sure yet" is there
         so the question never becomes a reason to abandon the form. -->
    <label class="f">
      <span class="lb">Which Session</span>
      <select name="session_type" required>
        <option value="" selected disabled>Choose one</option>
        <option value="studio">In the studio &mdash; year round</option>
        <option value="outdoor">Specialty Session &mdash; certain dates only</option>
        <option value="not-sure">Not sure yet</option>
      </select>
    </label>

    <label class="f">
      <span class="lb">When Are You Hoping to Shoot</span>
      <select name="timeframe" required>
        <option value="" selected disabled>Choose one</option>
        <option value="next-3-months">In the next three months</option>
        <option value="3-6-months">Three to six months</option>
        <option value="6-12-months">Six to twelve months</option>
        <option value="still-deciding">Still deciding</option>
      </select>
    </label>

    <label class="f">
      <span class="lb">Is It for an Occasion<span class="opt">OPTIONAL</span></span>
      <select name="occasion">
        <option value="" selected>No particular reason</option>
        <option value="just-for-me">Just for me</option>
        <option value="birthday">A birthday</option>
        <option value="anniversary">An anniversary</option>
        <option value="wedding">A wedding or engagement</option>
        <option value="gift">A gift for someone</option>
        <option value="other">Something else</option>
      </select>
    </label>

    <label class="f">
      <span class="lb">How Did You Hear About Me<span class="opt">OPTIONAL</span></span>
      <select name="heard_via">
        <option value="" selected>Prefer not to say</option>
        <option value="instagram">Instagram</option>
        <option value="facebook">Facebook</option>
        <option value="google">Google</option>
        <option value="friend">A friend or past client</option>
        <option value="tiktok">TikTok</option>
        <option value="other">Somewhere else</option>
      </select>
    </label>

    <label class="f">
      <span class="lb">Anything You&rsquo;d Like Me to Know<span class="opt">OPTIONAL</span></span>
      <textarea name="notes" rows="4"
                placeholder="Nerves, a date you have in mind, a Pinterest board &mdash; anything at all."></textarea>
    </label>

    <!-- NO FIGURE IN HERE ON PURPOSE. See the note at the head of this file:
         the Session Guide and the website FAQ currently quote different
         numbers, and a form is the wrong place to pick a side. The wording
         is Jessica's own and the structure it states -- images bought
         separately from the session fee -- is true in both versions. -->
    <label class="ack">
      <input type="checkbox" name="acknowledged" required>
      <span>I understand this is a full experience rather than a quick shoot,
        and that images are purchased separately from the session fee.</span>
    </label>

    <div class="hp" aria-hidden="true">
      <label>Website<input type="text" name="website" tabindex="-1"
             autocomplete="off"></label>
    </div>
    <div class="go">
      <button class="jhp-btn" type="submit">Send My Inquiry</button>
    </div>
    <noscript>
      <p class="note">This form needs JavaScript, which your browser has
         switched off. Email me at
         <a href="mailto:jessica@jhpboudoir.com">jessica@jhpboudoir.com</a>
         and tell me what you have in mind.</p>
    </noscript>
  </form>

  <div class="jhp-done" id="jhp-done" hidden>
    <h2 class="jhp-h">It Is With Me</h2>
    <p>Thank you &mdash; I have your inquiry and I will come back to you
       personally, usually within two or three business days.</p>
    <p>If you would rather not wait, book your consultation call now and we
       will talk it through properly.</p>
    <p style="margin-bottom:24px"><a class="jhp-btn"
       href="{{CALENDAR}}" style="border-bottom:0">Book My Call</a></p>
    <p>Anything urgent, write to me at
       <a href="mailto:jessica@jhpboudoir.com">jessica@jhpboudoir.com</a>.</p>
  </div>
</section>

<div class="jhp-div" aria-hidden="true"></div>

<!-- The way on for the woman who is NOT ready, which is the whole point of
     having two forms. She has arrived on the page for the decided, found she
     has not decided, and the worst outcome is that she closes the tab. This
     band hands her to /contact and the Session Guide instead. -->
<a class="jhp-band" href="../contact/">
  <img src="{{CDN}}6ab3ee3d18384d888bb3d0b1.jpg"
       width="1363" height="2048" loading="lazy"
       alt="A boudoir portrait made at the JHP Boudoir studio">
  <span class="over">
    <span class="jhp-kicker">Not quite ready</span>
    <h2 class="jhp-h jhp-h-lg">Start With the Guide</h2>
    <span class="sub">The studio, the day, and where pricing starts.</span>
    <span class="jhp-btn">Send Me the Guide</span>
  </span>
</a>
"""

SCRIPT = """
<script>
  /* The divider reveal, same opt-in pattern as every other page: the CSS
     renders the divider finished and js-rev is what collapses it ready to
     animate, so JavaScript off gets the mark rather than a gap. */
  (() => {
    const home = document.querySelector(".jhp-home");
    const rules = home ? home.querySelectorAll(".jhp-div") : [];
    if (!rules.length || !("IntersectionObserver" in window)) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    home.classList.add("js-rev");
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting) return;
        e.target.classList.add("in");
        io.unobserve(e.target);
      });
    }, { rootMargin: "0px 0px -12% 0px" });
    rules.forEach((r) => io.observe(r));
  })();

  /* THE SUBMIT

     The same fire-and-forget no-cors POST /contact uses, for the same reason:
     the browser cannot read the response of a no-cors request, so there is
     nothing to check and the thank-you shows on the attempt. keepalive is
     carried over even though this page does not navigate away by default --
     it costs nothing and it is what keeps the request alive if she closes the
     tab in the same breath as pressing the button, or if FORWARD is ever
     turned on.

     ?test=1 marks the row is_test, which site-inquiry-ingest stores but does
     not push to GHL, so Jessica can submit the live form without putting
     herself in her own CRM. */
  (() => {
    const form = document.getElementById("jhp-inq");
    const done = document.getElementById("jhp-done");
    if (!form || !done) return;

    const ENDPOINT = "{{WEBHOOK}}";
    const CALENDAR = "{{CALENDAR}}";
    const FORWARD = {{FORWARD}};

    const token = () => {
      try {
        if (crypto && crypto.randomUUID) return crypto.randomUUID();
      } catch (e) { /* fall through */ }
      return "t-" + Date.now() + "-" + Math.random().toString(36).slice(2, 11);
    };

    form.addEventListener("submit", (ev) => {
      ev.preventDefault();
      if (!form.checkValidity()) { form.reportValidity(); return; }

      const v = (n) => (form.elements[n] ? form.elements[n].value.trim() : "");

      /* A filled honeypot is a bot. It gets the thank-you and no request,
         because telling it that it failed only teaches it to try again. */
      if (v("website")) { form.hidden = true; done.hidden = false; return; }

      const first = v("first"), last = v("last");
      const body = {
        client_token: token(),
        name: (first + " " + last).trim(),
        email: v("email"),
        phone: v("phone"),
        session_type: v("session_type"),
        timeframe: v("timeframe"),
        occasion: v("occasion"),
        heard_via: v("heard_via"),
        notes: v("notes").slice(0, 2000),
        acknowledged: !!(form.elements["acknowledged"] &&
                         form.elements["acknowledged"].checked),
        source_page: location.pathname,
        is_test: new URLSearchParams(location.search).has("test"),
        user_agent: navigator.userAgent.slice(0, 400),
      };

      try {
        fetch(ENDPOINT, {
          method: "POST",
          mode: "no-cors",
          keepalive: true,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }).catch(() => {});
      } catch (e) { /* the thank-you still names her email address */ }

      if (FORWARD) {
        try { window.location.href = CALENDAR; return; } catch (e) { /* fall through */ }
      }
      form.hidden = true;
      done.hidden = false;
      done.scrollIntoView({ block: "center", behavior: "smooth" });
    });
  })();
</script>
"""

out = (HEAD + shared[shared.index("/* SHARED DESIGN SYSTEM"):] + parts
       + FORM_CSS + EXTRA_CSS + "</style>\n\n" + nav + BODY + SCRIPT + "\n"
       + foot)
out = (out.replace("{{CDN}}", CDN)
          .replace("{{WEBHOOK}}", WEBHOOK)
          .replace("{{CALENDAR}}", CALENDAR)
          .replace("{{FORWARD}}", "true" if FORWARD else "false"))
(ROOT / "scalogy-inquire.html").write_text(out)

fields = (out.count('<input type="text"') + out.count('<input type="email"')
          + out.count('<input type="tel"') + out.count("<select")
          + out.count("<textarea") + out.count('type="checkbox"'))
print("wrote %d bytes, %d controls (9 real + 1 honeypot), %d selects, "
      "forward=%s" % (len(out.encode()), fields, out.count("<select"), FORWARD))
assert "{{" not in out, "an unreplaced placeholder survived"
# The fence is opened by HEAD and closed by the footer slice, which runs to
# the end of scalogy-portfolio.html and carries {% endraw %} with it. Exactly
# one of each, or Scalogy rejects the template as unparseable Jinja.
assert out.count("{% raw %}") == 1 and out.count("{% endraw %}") == 1, \
    "the raw fence must be opened once and closed once"
