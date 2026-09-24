#!/usr/bin/env python3
"""Generates scalogy-contact.html -- the Session Guide request page at /contact.

Like the FAQ and The Experience, this page slices its design system out of
scalogy-portfolio.html at build time rather than keeping a copy, so a change
to the tokens, the nav, the footer or the phone scale reaches it without
anyone remembering to. It takes the intro band, the divider, the pull-quote
and the closing band.

THE CLOSING BAND GOES TO FACEBOOK, NOT ONWARD THROUGH THE SITE. On every
other page that band is the door to the next page; here there is no next
page, because this is the end of the funnel. So it is the VIP Facebook
group instead -- Jessica's ask, 24 September. That makes it the one band on
the site whose anchor leaves the site, which is why it alone carries
target="_blank" and rel="noopener".

It is deliberately the same .jhp-band construction as the other three, not a
new shape: a woman who has just handed over her email should recognise the
foot of this page as the foot of any other, and the group is a softer ask
than the one she has already said yes to. The home page also has a VIP
block, in its own plainer .jhp-vip shape and mid-page rather than at the
foot; the two say different things and neither is a copy of the other.

WHAT THIS PAGE IS, AND IS NOT

It is not a booking page. Every "Book a Call" button on the site lands here,
but the exchange this page offers is the Session Guide, and the link to book a
consultation call lives INSIDE that guide -- Jessica's sequence, 24 September.
So the page asks for an email address and nothing else is promised on it. If
the button labels across the site are ever reworded, that is a separate edit
to six templates and does not belong here.

IT IS A MAGAZINE, AND SAYING SO IS THE POINT. Jessica's note, 24 September:
a woman should be able to tell what actually arrives. So the page names the
Session Guide Magazine in full where she first meets it, calls it "the
magazine" after that, and sets the expectation before she submits rather
than only in the thank-you -- get your details right, five or ten minutes,
then the spam folder. The short form "the guide" is still the same object
and still correct; what is not correct is a page that never says what shape
the thing is.

That name is copy and nothing else. The GHL tag is still
"Session Guide - Requested" and renaming anything a visitor reads must not
go near it -- see HOW A SUBMISSION TRAVELS below.

HOW A SUBMISSION TRAVELS

  the form  ->  POST (no-cors) to the site-lead-submit webhook
            ->  workflow site-leads-ingest
            ->  a site_leads row  +  a GHL contact tagged
                "Session Guide - Requested"

and Jessica's GHL workflow watching that tag is what actually sends the
guide. This page never sends an email and never sees the guide. Two
consequences worth knowing before debugging it: a submission that reaches
site_leads has worked as far as this page is concerned, and a guide that
stops arriving is a GHL problem, not a page problem.

The POST is no-cors and fire-and-forget, exactly like the four other lead
forms on this tenant, so the browser cannot read the response and the page
must not pretend to. It shows the thank-you state on the attempt, not on a
confirmation -- which is why the form also keeps Jessica's email address
visible underneath: a woman whose submission silently failed still has a way
through.

NO JAVASCRIPT, NO FORM. That is stated on the page rather than hidden: a
no-cors POST needs fetch, and a plain HTML POST would navigate the visitor to
a JSON response and send the wrong content type besides. The <noscript> line
gives the email address instead, and the note under the form and the footer's
Get In Touch column carry it too, so the page still does its job with
scripting off. Jessica removed the block that used to repeat it at the foot,
so those three are now the whole of it -- do not let the last one go. This is the same
bargain the dividers make -- the page is finished without JavaScript, and
JavaScript only ever adds.

Substitution here is .replace("{{CDN}}", CDN), not %-formatting as in
build-info.py. The form CSS is full of percentages and a single undoubled %
in a %-formatted string is a build error three sections away from its cause.

THE TWO PHOTOGRAPHS ARE UNTUNED. Both crops are a neutral 50% 50% and were
chosen on aspect ratio and on which client was least used elsewhere -- Miss T
for the band, Miss V for the quote, one client per frame. Nobody has looked
at either one at 1440 or on a phone yet. Jessica has the band tuner for
exactly this; until she has been through it, treat both object-position
values as placeholders and not as decisions.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
CDN = "https://assets.cdn.filesafe.space/Pcnm8GVNMmWTY65qVOAp/media/"
src = (ROOT / "scalogy-portfolio.html").read_text()

# --- the slices -----------------------------------------------------------
# The same cut points build-info.py uses. THE WAY ON is included: the VIP
# band at the foot of this page is a .jhp-band, the same construction as the
# closing band on Portfolio, the FAQ and The Experience, so it takes that
# CSS rather than carrying a second copy of it here.
MARK_END = "/* The closing band carries no photograph."
shared = src[:src.index("/* THE INDEX")]                     # tokens .. phone
parts = src[src.index("/* THE INTRO"):src.index(MARK_END)]
tail = src[src.index(MARK_END):]
after_style = tail[tail.index("</style>"):]
nav = after_style[after_style.index('<nav class="jhp-nav">'):
                  after_style.index("</nav>") + len("</nav>\n")]
foot = after_style[after_style.index('<footer class="jhp-foot">'):]

WEBHOOK = "https://app.scalogy.com/webhooks/in/jhpboudoir1/site-lead-submit"

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Contact | JHP Boudoir</title>
<meta name="description" content="Ask for the JHP Boudoir Session Guide: the studio, how a session day runs, what is included and where pricing starts. Boudoir photography in Jefferson City, Missouri.">
<meta name="robots" content="noindex, nofollow">
<meta property="og:title" content="Contact | JHP Boudoir">
<meta property="og:description" content="Ask for the Session Guide and read it in your own time.">
<meta property="og:type" content="website">
<style>html,body{margin:0;padding:0;background:#13100E}body{overflow-x:hidden}</style>
</head>
<body>
{% raw %}
<div class="jhp-home">
<style>
"""

FORM_CSS = """
/* WHAT IS INSIDE THE GUIDE
   ------------------------
   A numbered list without the numbers: what matters is that there are five
   of them and that they are short, not what order they are in. Each item is
   one line of gold rule and one line of type, so the block reads as a
   contents page rather than as a sales list -- which is the honest shape,
   because a contents page is what it is describing. */
.jhp-home .jhp-inside{list-style:none;max-width:680px;margin:0 auto;
  padding:0;display:grid;gap:0}
.jhp-home .jhp-inside li{display:flex;gap:16px;align-items:baseline;
  padding:17px 0;border-top:1px solid var(--line-soft);
  font-family:var(--sans);font-weight:300;font-size:16.5px;line-height:1.7;
  color:var(--muted);text-wrap:pretty}
.jhp-home .jhp-inside li:last-child{border-bottom:1px solid var(--line-soft)}
/* A small gold lozenge, the divider's mark at half size, so the list is
   marked in the page's own vocabulary rather than with a bullet. */
.jhp-home .jhp-inside li::before{content:"";flex:0 0 5px;height:5px;
  margin-top:.62em;transform:rotate(45deg);
  background:var(--ground);border:1px solid var(--gold)}

/* THE FORM
   --------
   Four fields. Every one of them is something Jessica needs in order to
   send a guide or follow it up, and nothing is asked for that could be
   asked for later on the call instead -- a fifth field costs more requests
   than the answer is worth at this point in the conversation.

   Inputs are drawn on --surface with a hairline, so they read as part of
   the page rather than as a browser's idea of a form. The focus ring is the
   gold one every other interactive thing on the site uses; it is never
   removed, only restyled, because the whole form has to be usable from the
   keyboard alone.

   font-size is 16px on the inputs and that number is not a design choice.
   Mobile Safari zooms the viewport when a focused input is smaller than
   16px, and the page is then left scrolled sideways with the submit button
   off screen. 16 is the floor that stops it. */
.jhp-home .jhp-ask-form{max-width:560px;margin:0 auto}
.jhp-home .jhp-ask-form .row{display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.jhp-home .jhp-ask-form .f{display:block;margin:0 0 16px}
.jhp-home .jhp-ask-form .row .f{margin-bottom:0}
.jhp-home .jhp-ask-form .row + .f{margin-top:16px}
.jhp-home .jhp-ask-form .lb{display:block;margin:0 0 7px;
  font-family:var(--sans);font-weight:400;font-size:11px;letter-spacing:.2em;
  text-transform:uppercase;color:var(--gold)}
.jhp-home .jhp-ask-form input{display:block;width:100%;box-sizing:border-box;
  padding:14px 15px;font-family:var(--sans);font-weight:300;font-size:16px;
  line-height:1.4;color:var(--ink);background:var(--surface);
  border:1px solid var(--line);border-radius:2px;appearance:none;
  transition:border-color .3s,background .3s}
.jhp-home .jhp-ask-form input::placeholder{color:var(--dim);opacity:1}
.jhp-home .jhp-ask-form input:hover{border-color:var(--gold)}
.jhp-home .jhp-ask-form input:focus{outline:none;background:var(--raised);
  border-color:var(--gold-bright)}
.jhp-home .jhp-ask-form input:focus-visible{outline:2px solid var(--gold-bright);
  outline-offset:2px}
/* Marked invalid only once it has been left, never while it is being typed
   in -- :invalid alone paints an empty required field red before the
   visitor has touched it, which is a telling-off for arriving. */
.jhp-home .jhp-ask-form input:not(:placeholder-shown):invalid{
  border-color:#B4614B}
.jhp-home .jhp-ask-form .go{margin-top:24px;text-align:center}
.jhp-home .jhp-ask-form .go .jhp-btn{width:100%;max-width:340px}
.jhp-home .jhp-ask-form .note{margin:18px 0 0;font-family:var(--sans);
  font-weight:300;font-size:13.5px;line-height:1.7;color:var(--dim);
  text-align:center}
.jhp-home .jhp-ask-form .note a{color:var(--muted);
  border-bottom:1px solid var(--line);transition:color .3s,border-color .3s}
.jhp-home .jhp-ask-form .note a:hover{color:var(--gold);
  border-color:var(--gold)}
/* The honeypot. Off-screen rather than display:none, because some bots skip
   what is not rendered; a human using a screen reader is kept out of it by
   aria-hidden and tabindex, so it is never announced and never tabbed to. */
.jhp-home .jhp-ask-form .hp{position:absolute;left:-9999px;width:1px;
  height:1px;overflow:hidden}

/* The thank-you, and the form, are the same slot: one is hidden while the
   other shows. Hidden with the hidden attribute, which is a real removal
   from the accessibility tree -- a screen reader should not be able to tab
   into a form that is no longer on the page. Nothing here is animated,
   because a woman who has just given her email address wants to be told it
   worked, not shown a transition. */
.jhp-home .jhp-done{max-width:560px;margin:0 auto;text-align:center}
.jhp-home .jhp-done .jhp-h{margin-bottom:14px}
.jhp-home .jhp-done p{font-family:var(--sans);font-weight:300;font-size:16.5px;
  line-height:1.8;color:var(--muted);margin:0 0 14px}
.jhp-home .jhp-done p:last-child{margin-bottom:0}
.jhp-home .jhp-done a{color:var(--gold);border-bottom:1px solid var(--line);
  transition:color .3s,border-color .3s}
.jhp-home .jhp-done a:hover{color:var(--gold-bright);
  border-color:var(--gold-bright)}
.jhp-home [hidden]{display:none!important}

/* The band says "The Session Guide" over "Let's Get in Touch" rather than
   "Contact" over it: the heading is Jessica's, and with it in place a kicker
   reading Contact said the same thing twice and left the thing the page is
   actually offering below the fold on a phone. The kicker carries the offer
   instead. Revert the kicker to Contact if she would rather have it back.

   This page's band is its own photograph, so it is the one crop overridden
   -- and it has NOT been looked at yet. Neutral until Jessica has run it
   through the band tuner. */
.jhp-home .jhp-intro img{object-position:50% 50%}

@media (max-width:620px){
  /* Two name fields side by side at 390px leaves each about 150px wide,
     which is narrower than the words that go in them. They stack. */
  .jhp-home .jhp-ask-form .row{grid-template-columns:1fr;gap:0}
  .jhp-home .jhp-ask-form .row .f{margin-bottom:16px}
  .jhp-home .jhp-ask-form .row + .f{margin-top:0}
  .jhp-home .jhp-ask-form .go .jhp-btn{max-width:none}
  .jhp-home .jhp-ask-form .note{font-size:13px}
  .jhp-home .jhp-inside li{font-size:var(--ph-body);gap:13px;padding:15px 0}
  .jhp-home .jhp-done p{font-size:var(--ph-body)}
}
"""

BODY = """
<section class="jhp-intro">
  <img src="{{CDN}}80df5d3e-43e6-4eb5-84c2-673a346bbec3.jpg"
       width="1600" height="1065"
       alt="A client photographed at the JHP Boudoir studio, Jefferson City, Missouri">
  <div class="jhp-over">
    <p class="jhp-kicker">The Session Guide</p>
    <h1 class="jhp-h jhp-h-lg">Let&rsquo;s Get in Touch</h1>
  </div>
</section>

<section class="jhp-sec">
  <div class="jhp-center">
    <h2 class="jhp-h">What&rsquo;s Inside the JHP Boudoir Session Guide
        Magazine?</h2>
    <p class="jhp-p">Ready to learn more about working with the studio? Your
       copy comes over the moment you fill in the form below &mdash;
       everything you would want to know before you speak to anybody, to
       read in your own time with no one waiting on an answer.</p>
  </div>
  <ul class="jhp-inside">
    <li>The studio, and what it is like to be in it.</li>
    <li>How a session day runs, from hair and makeup to the last frame.</li>
    <li>Everything a session includes.</li>
    <li>Where pricing starts, and how the interest-free payment plans
        work.</li>
    <li>A link to book your consultation call &mdash; for whenever you are
        ready, and not before.</li>
  </ul>
</section>

<section class="jhp-sec" style="border-bottom:none">
  <div class="jhp-center">
    <p class="jhp-kicker">No obligation</p>
    <h2 class="jhp-h">Send Me the Guide</h2>
    <p class="jhp-p">Tell me where to send it and the magazine comes straight
       to your inbox. Do check your details are right so that I can reach
       you, and if it has not arrived within five or ten minutes, have a
       look in your spam folder.</p>
  </div>

  <form class="jhp-ask-form" id="jhp-guide" novalidate>
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
    <div class="hp" aria-hidden="true">
      <label>Website<input type="text" name="website" tabindex="-1"
             autocomplete="off"></label>
    </div>
    <div class="go">
      <button class="jhp-btn" type="submit">Send Me the Session Guide</button>
    </div>
    <p class="note">Your details come to me and nobody else. If you would
       rather just write to me,
       <a href="mailto:jessica@jhpboudoir.com">jessica@jhpboudoir.com</a>
       reaches me directly.</p>
    <noscript>
      <p class="note">This form needs JavaScript, which your browser has
         switched off. Email me at
         <a href="mailto:jessica@jhpboudoir.com">jessica@jhpboudoir.com</a>
         and I will send the guide straight back.</p>
    </noscript>
  </form>

  <div class="jhp-done" id="jhp-done" hidden>
    <h2 class="jhp-h">It Is On Its Way</h2>
    <p>Check your inbox &mdash; the magazine is heading there now, and should
       land within five or ten minutes. Have a proper look at it when you
       have a quiet ten minutes of your own.</p>
    <p>Inside it there is a link to book your consultation call, for whenever
       you are ready. Fifteen minutes, and nothing is decided on it that you
       do not decide.</p>
    <p>If it has not arrived, look in your spam folder first, then write to
       me at <a href="mailto:jessica@jhpboudoir.com">jessica@jhpboudoir.com</a>
       and I will send it by hand.</p>
  </div>
</section>

<div class="jhp-div" aria-hidden="true"></div>

<section class="jhp-sec" style="border-bottom:none">
  <!-- ONE REVIEW, ONE PAGE -- the rule is written out in
       scalogy-portfolio.html and the register is reviews.md. Miss H.'s is
       here because it is the only review on the site about the room itself,
       and this is the page a woman is on at the moment she is deciding
       whether she could walk into it. -->
  <div class="jhp-quote">
    <figure class="shot">
      <img src="{{CDN}}85a53ea4-6572-4c9a-a28b-40ec240427c5.jpg"
           width="1065" height="1600" loading="lazy"
           alt="A boudoir portrait made at the JHP Boudoir studio">
    </figure>
    <blockquote>
      <p class="qt">&ldquo;Jessica is amazing! Such a lovely day. She is so fun
         and professional! She really makes the studio a safe and comfortable
         place! Recommend to anyone who wants to feel good about themselves or
         just have a fun self-love day!&rdquo;</p>
      <p class="qa">Miss H.</p>
      <a class="src" href="https://www.google.com/search?q=JHP+Boudoir&amp;kgmid=/g/11v3x9fqm9"
         target="_blank" rel="noopener">Read all reviews on Google</a>
    </blockquote>
  </div>
</section>

<div class="jhp-div" aria-hidden="true"></div>

<!-- The way on, which here means off the site. See the note at the head of
     build-contact.py: the band is the link, the button inside it is a span,
     and this is the only one of the four whose href leaves jhpboudoir.com.

     ONE CLIENT PER FRAME. Miss P is on Portfolio and the FAQ but on neither
     of this page's two other photographs -- the intro band is Miss T and
     the pull-quote is Miss V -- so no face appears twice here. Her set is
     black and white throughout, which is the reason to use it rather than a
     coincidence: the scrim over this band has to hold cream type and a gold
     kicker, and a frame with no colour of its own is the easiest thing in
     the library to set them against.

     THE CROP IS INHERITED, NOT CHOSEN. There is no object-position here, so
     this frame takes the shared band crop of 50% 22% along with the other
     three -- which is a tuned number, but tuned against their frames and
     not against this one. Preferring it to a fresh 50% 50% keeps the four
     bands one crop rather than three plus an exception, and means this page
     adds no new untuned figure of its own. It is still a figure nobody has
     checked at 1440 against this photograph. Band tuner.

     The band crops vertically at every width above a phone, so the subject
     stays centred and the type is on the left away from her; below 620px
     the frame is cut at the sides instead and the heavier phone scrim takes
     over. -->
<a class="jhp-band" href="https://www.facebook.com/groups/1107773373084834"
   target="_blank" rel="noopener">
  <img src="{{CDN}}8a91728b-dbb1-4728-8eb5-7361f93c0611.jpg"
       width="1600" height="1065" loading="lazy"
       alt="A client photographed in black and white at JHP Boudoir">
  <span class="over">
    <span class="jhp-kicker">The VIP Facebook group</span>
    <h2 class="jhp-h jhp-h-lg">Become One of My VIPs</h2>
    <span class="sub">Perks, first looks, early openings.</span>
    <span class="jhp-btn">Become a VIP</span>
  </span>
</a>

<script>
  /* Draws each divider in as it arrives. Everything here is an
     enhancement: the CSS renders the dividers finished, and js-rev is what
     collapses them ready to animate, so if any one of these checks fails
     the page keeps its dividers and simply does not move them. */
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
     ----------
     A no-cors POST to the site-lead-submit webhook, which is the same
     fire-and-forget shape the other four lead forms on this tenant use. The
     browser cannot read the response of a no-cors request, so there is
     nothing to check and the thank-you shows on the attempt. That is why the
     thank-you carries Jessica's email address: it is the only recourse a
     woman has if the POST quietly failed, and she should not have to go
     looking for it.

     keepalive is what lets the request finish if the page is closed in the
     same breath as the button is pressed.

     ?test=1 in the URL marks the row is_test, which site-leads-ingest
     stores but does not push to GHL -- so Jessica can submit the live form
     without putting herself in her own CRM. */
  (() => {
    const form = document.getElementById("jhp-guide");
    const done = document.getElementById("jhp-done");
    if (!form || !done) return;

    const ENDPOINT = "{{WEBHOOK}}";

    const token = () => {
      try {
        if (crypto && crypto.randomUUID) return crypto.randomUUID();
      } catch (e) { /* fall through */ }
      return "t-" + Date.now() + "-" + Math.random().toString(36).slice(2, 11);
    };

    form.addEventListener("submit", (ev) => {
      ev.preventDefault();

      /* novalidate is on the form so this runs on our terms rather than the
         browser's, but the constraints themselves are still the browser's
         and reportValidity is what draws its messages. */
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
      } catch (e) { /* nothing to recover: the thank-you names the email */ }

      form.hidden = true;
      done.hidden = false;
      done.scrollIntoView({ block: "center", behavior: "smooth" });
    });
  })();
</script>
"""

out = (HEAD + shared[shared.index("/* SHARED DESIGN SYSTEM"):] + parts
       + FORM_CSS + "</style>\n\n" + nav + BODY + "\n" + foot)
out = out.replace("{{CDN}}", CDN).replace("{{WEBHOOK}}", WEBHOOK)
(ROOT / "scalogy-contact.html").write_text(out)

n_fields = out.count('<input type="text"') + out.count('<input type="email"') \
    + out.count('<input type="tel"')
print("wrote", len(out.encode()), "bytes,", n_fields, "inputs (4 real + 1 honeypot),",
      out.count('href="/contact"'), "absolute contact links (want 0)")
