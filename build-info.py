#!/usr/bin/env python3
"""Generates scalogy-faq.html -- the FAQ page under Info.

Like the galleries, this page slices its design system out of
scalogy-portfolio.html at build time rather than keeping its own copy, so
a change to the tokens, the nav, the footer or the phone scale reaches it
without anyone remembering to.

It takes more than the galleries do: the intro band, the divider, the
pull-quote and the closing band are all the Portfolio's components, used
here exactly as they are used there. Only the accordion below is this
page's own, and only the two crops are overridden -- a different
photograph wants a different crop, and the Portfolio's numbers are
Jessica's, set on her own frames in the band tuner.

No blanks are left. Every answer is Jessica's, given 24 September, and
several of them corrected what had been inferred here before: hair and
makeup is done at a local salon beforehand and not at the studio, the
image reveal is a Zoom appointment and not an in-person one, wardrobe is
not planned on the consultation call but sent as a styling guide, and
consent runs through a model release each client signs rather than an
ad-hoc written permission. Session fees start at $697.

The .fill span is kept in the stylesheet on purpose. It is how the next
unanswered thing gets drawn -- as a visible blank rather than as an
invented fact -- and this page had one in it for a day.

The live template is one byte smaller than this file: Scalogy trims
trailing whitespace on templates_create, and the page had to be published
as a create plus patches because it is over the 20KB inline limit. The
difference is a blank line between two CSS sections and nothing else.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
CDN = "https://assets.cdn.filesafe.space/Pcnm8GVNMmWTY65qVOAp/media/"
src = (ROOT / "scalogy-portfolio.html").read_text()

# --- the slices -----------------------------------------------------------
MARK_END = "/* The closing band carries no photograph."
shared = src[:src.index("/* THE INDEX")]            # tokens .. the phone scale
parts = src[src.index("/* THE INTRO"):src.index(MARK_END)]   # intro..band
tail = src[src.index(MARK_END):]
after_style = tail[tail.index("</style>"):]
vip = tail[tail.index(".jhp-home .jhp-vip .jhp-h"):tail.index("</style>")]
nav = after_style[after_style.index('<nav class="jhp-nav">'):
                  after_style.index("</nav>") + len("</nav>\n")]
foot = after_style[after_style.index('<footer class="jhp-foot">'):]

# The nav and the footer come over exactly as the Portfolio writes them --
# Info already points at this page. When The Experience exists the Info
# item becomes a two-item menu, and it changes once, there.

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FAQ | JHP Boudoir</title>
<meta name="description" content="What to wear, who sees your photographs, whether you need to know how to pose. The questions women ask JHP Boudoir before they book a session in Jefferson City, Missouri.">
<meta name="robots" content="noindex, nofollow">
<meta property="og:title" content="FAQ | JHP Boudoir">
<meta property="og:description" content="The questions women ask before they book a boudoir session.">
<meta property="og:type" content="website">
<style>html,body{margin:0;padding:0;background:#13100E}body{overflow-x:hidden}</style>
</head>
<body>
{% raw %}
<div class="jhp-home">
<style>
"""

FAQ_CSS = """
/* THE ANSWERS
   -----------
   Native <details>, not a scripted accordion. It opens without JavaScript,
   it is in the tab order on its own, a screen reader announces it as
   expanded or collapsed without being told to, and the browser's own
   find-in-page can open a closed answer to show a match. Nothing written
   by hand does all four.

   name="faq" makes the group exclusive -- opening one closes the last --
   in the browsers that have it. Where it is missing the answers simply
   all stay open once opened, which is not a failure, so no script is
   needed to paper over it.

   The mark is two rules rather than a + in a font or an SVG: the vertical
   one rotates out of sight when the answer opens, so a plus becomes a
   minus with nothing to load. */
.jhp-home .jhp-ask{max-width:820px;margin:0 auto}
.jhp-home .jhp-ask details{border-top:1px solid var(--line-soft)}
.jhp-home .jhp-ask details:last-of-type{border-bottom:1px solid var(--line-soft)}
.jhp-home .jhp-ask summary{list-style:none;cursor:pointer;display:flex;
  gap:18px;align-items:flex-start;padding:22px 0;
  font-family:var(--serif);font-weight:500;
  font-size:clamp(19px,1.9vw,23px);line-height:1.35;letter-spacing:.01em;
  color:var(--ink);text-wrap:pretty;transition:color .3s}
.jhp-home .jhp-ask summary::-webkit-details-marker{display:none}
.jhp-home .jhp-ask summary:hover{color:var(--gold-bright)}
.jhp-home .jhp-ask summary:focus-visible{outline:2px solid var(--gold-bright);
  outline-offset:3px}
.jhp-home .jhp-ask .mk{position:relative;flex:0 0 14px;height:14px;
  margin-top:.44em}
.jhp-home .jhp-ask .mk::before,.jhp-home .jhp-ask .mk::after{content:"";
  position:absolute;background:var(--gold);transition:transform .3s,opacity .3s}
.jhp-home .jhp-ask .mk::before{left:0;top:6px;width:14px;height:1px}
.jhp-home .jhp-ask .mk::after{left:6px;top:0;width:1px;height:14px}
.jhp-home .jhp-ask details[open] .mk::after{transform:rotate(90deg);opacity:0}
.jhp-home .jhp-ask .a{padding:0 0 26px 32px}
.jhp-home .jhp-ask .a p{font-family:var(--sans);font-weight:300;
  font-size:16.5px;line-height:1.8;color:var(--muted);margin:0 0 14px}
.jhp-home .jhp-ask .a p:last-child{margin-bottom:0}
.jhp-home .jhp-ask .a a{color:var(--gold);border-bottom:1px solid var(--line);
  transition:color .3s,border-color .3s}
.jhp-home .jhp-ask .a a:hover{color:var(--gold-bright);
  border-color:var(--gold-bright)}
/* A blank Jessica still has to fill, drawn so it reads as a blank rather
   than as a number. Delete the span with the answer. */
.jhp-home .jhp-ask .fill{color:var(--gold-bright);font-style:italic;
  border-bottom:1px dashed var(--gold);padding-bottom:1px}

/* This page's bands carry different photographs from the Portfolio's, so
   they carry different crops. Every other line of the two bands is the
   Portfolio's, sliced above.

   Both frames were chosen on where the words land rather than on the
   photograph alone, and swept at the real size rather than judged from a
   thumbnail -- at a quarter scale a heading looks clear of a subject it
   is in fact sitting on top of.

   The top band's heading is centred, so it needed a frame whose lower
   middle is empty: she sits high against the mirror and the words land on
   the floor below her. 35% rather than centred keeps her whole face in,
   which a centred crop cut at the forehead.

   The closing band's heading is set left, so it needed the left third
   empty: she lies to the right of it and the words sit on bare floor.

   Three frames on this page, three different clients. One woman opening
   the page and closing it would read as the only one who has ever been
   here. */
.jhp-home .jhp-intro img{object-position:50% 35%}
.jhp-home .jhp-band img{object-position:50% 50%}
@media (max-width:620px){
  /* The top band barely crops at this width -- 40px off a 260px draw --
     so its number hardly matters. The closing band is the other way
     about: taller than the frame's shape, so it is scaled to the height
     and cut at the sides, 91px of slack. Anchoring left takes that off
     the right and walks her away from the words. */
  .jhp-home .jhp-intro img{object-position:50% 35%}
  .jhp-home .jhp-band img{object-position:10% 50%}
  /* The Portfolio's phone scrim was weighted for a candle-lit frame with
     a bright subject in the middle of it. This one is already dark and
     she lies well right of the words, so the same weight on top of it
     leaves a black rectangle with a heading on it. Lighter, and the floor
     and the leopard rug come back. */
  .jhp-home .jhp-band .over{background:
    linear-gradient(0deg,rgba(19,16,14,.72) 0%,rgba(19,16,14,.4) 58%,
      rgba(19,16,14,.3) 100%),
    linear-gradient(90deg,rgba(19,16,14,.78) 0%,rgba(19,16,14,.44) 50%,
      rgba(19,16,14,.06) 100%)}
  .jhp-home .jhp-ask summary{font-size:18px;padding:19px 0;gap:14px}
  .jhp-home .jhp-ask .a{padding:0 0 22px 28px}
  .jhp-home .jhp-ask .a p{font-size:var(--ph-body);line-height:1.75}
}
"""

BODY = """
<section class="jhp-intro">
  <img src="%(cdn)sf7fbfbb3-5380-4094-85e1-8699a3ff59b9.jpg"
       width="1600" height="1065"
       alt="A client photographed beside the gilt mirror at the JHP Boudoir studio, Jefferson City, Missouri">
  <div class="jhp-over">
    <p class="jhp-kicker">FAQ</p>
    <h1 class="jhp-h jhp-h-lg">The Questions Everyone Asks First</h1>
  </div>
</section>

<section class="jhp-sec" style="border-bottom:none">
  <div class="jhp-ask">

    <details name="faq">
      <summary><span class="mk" aria-hidden="true"></span>I&rsquo;m not a model. I have no idea how to pose.</summary>
      <div class="a">
        <p>Nobody does. That is my job, not yours.</p>
        <p>I pose you from head to toe &mdash; where your chin goes, what your
           hands are doing, where your weight sits. I get up and show you the
           pose myself, and I talk you through it while you find it, so you are
           never left guessing. You will be told what to do for the whole
           session.</p>
      </div>
    </details>

    <details name="faq">
      <summary><span class="mk" aria-hidden="true"></span>Is my body right for this?</summary>
      <div class="a">
        <p>Yes. Every age, every size, every body.</p>
        <p>Go and look at the <a href="../portfolio/">portfolio</a> &mdash;
           those are real clients, not models, and no two of them look alike.
           Tattoos, scars, stretch marks, a C-section shelf, a body six weeks
           postpartum or sixty years lived in: none of it rules you out, and
           none of it is a problem to be fixed before you get here.</p>
      </div>
    </details>

    <details name="faq">
      <summary><span class="mk" aria-hidden="true"></span>Who is going to see my photographs?</summary>
      <div class="a">
        <p>Nobody, unless you decide otherwise.</p>
        <p>Every client signs a model release, and that is where you say
           whether your images stay private or whether I may share them.
           Private is a perfectly ordinary answer. It changes nothing about
           your session, and nothing about how I photograph you.</p>
        <p>Every woman whose face is on this website chose to let it be
           there.</p>
      </div>
    </details>

    <details name="faq">
      <summary><span class="mk" aria-hidden="true"></span>What do I wear? What do I need to bring?</summary>
      <div class="a">
        <p>All clients must bring a nude thong and a black thong. Everything
           else is optional &mdash; hosiery, shoes and jewelry are welcome if
           you have pieces you love, but are not required.</p>
        <p>There is a full studio client wardrobe for you to borrow from, and a
           wardrobe and styling guide comes to you by email before your session
           date, so none of it is left for you to work out on your own.</p>
        <p>If you would rather wear your own pieces, that is completely fine
           &mdash; plenty of women do. Thistle &amp; Spire, Dreamgirl, Oh La La
           Cheri, Honey Birdette and Victoria&rsquo;s Secret are brands I
           recommend.</p>
      </div>
    </details>

    <details name="faq">
      <summary><span class="mk" aria-hidden="true"></span>Is hair and makeup included?</summary>
      <div class="a">
        <p>Yes &mdash; professional hair and makeup is part of every session.</p>
        <p>It is done at a local salon beforehand rather than at the studio, so
           you arrive already finished and we go straight into photographing
           you. You do not need to book it or pay for it separately: your
           artist and the salon address come to you once you book.</p>
      </div>
    </details>

    <details name="faq">
      <summary><span class="mk" aria-hidden="true"></span>What does a session cost?</summary>
      <div class="a">
        <p>The session fee starts at $697. That covers professional hair and
           makeup, access to the client wardrobe, your fully guided session,
           and your image reveal and product ordering appointment.</p>
        <p>Your prints &amp; products are bought separately, as a collection.
           Every client chooses a package when she books, and pays for it on an
           interest-free pre-payment plan or may pay in full.</p>
        <p>We go through all of it on your consultation call, before you commit
           to anything. No surprises and no pressure &mdash; if it is not right
           for you, it is not right for you.</p>
      </div>
    </details>

    <details name="faq">
      <summary><span class="mk" aria-hidden="true"></span>Is a product purchase required?</summary>
      <div class="a">
        <p>Yes. Every client chooses a collection when she books and sets up a
           prepayment plan or may pay in full at booking, so you know what you
           are spending before your session rather than after it.</p>
        <p>Petite Collections start at $1,250 and include 3 digital images.
           Full Collections start at $3,400 and include an album, digitals,
           and a mobile app.</p>
      </div>
    </details>

    <details name="faq">
      <summary><span class="mk" aria-hidden="true"></span>Do you offer payment plans?</summary>
      <div class="a">
        <p>Yes, and every collection is bought through one. You set yours up
           when you book, and pay weekly, biweekly or monthly &mdash; whichever
           suits you.</p>
        <p>They are interest free. It is the same figure either way, spread
           out. You may book your session 12 months in advance.</p>
      </div>
    </details>

    <details name="faq">
      <summary><span class="mk" aria-hidden="true"></span>How long does the day take?</summary>
      <div class="a">
        <p>Plan on two to three hours in total for your session day
           experience.</p>
      </div>
    </details>

    <details name="faq">
      <summary><span class="mk" aria-hidden="true"></span>When do I see the photographs?</summary>
      <div class="a">
        <p>At your image reveal, 7&ndash;14 business days after your session.
           It is a private appointment over Zoom: we go through your images
           together for the first time, and you choose the ones you want to
           keep and how you want them.</p>
        <p>You are not sent a link and left to work it out alone. The reveal is
           most women&rsquo;s favorite part of the whole thing.</p>
      </div>
    </details>

    <details name="faq">
      <summary><span class="mk" aria-hidden="true"></span>Where is the studio?</summary>
      <div class="a">
        <p>Just outside Jefferson City, Missouri. It is by appointment only, so
           the address comes to you as soon as you book &mdash; along with the
           salon where your hair and makeup happens beforehand.</p>
      </div>
    </details>

  </div>
</section>

<div class="jhp-div" aria-hidden="true"></div>

<section class="jhp-sec" style="border-bottom:none">
  <div class="jhp-quote">
    <figure class="shot">
      <img src="%(cdn)s4ed33692-fb5f-4087-ac3f-f9e4894557d5.jpg"
           width="1065" height="1600" loading="lazy"
           alt="A boudoir portrait made at the JHP Boudoir studio">
    </figure>
    <blockquote>
      <p class="qt">&ldquo;I couldn&rsquo;t have been happier with how my shoot and
         image reveal went! I was made to feel so sexy and confident, and she
         captured the glow I have been working so hard to get back! I would
         recommend JHP Photography to any woman!&rdquo;</p>
      <p class="qa">Miss M.</p>
      <a class="src" href="https://www.google.com/search?q=JHP+Boudoir&amp;kgmid=/g/11v3x9fqm9"
         target="_blank" rel="noopener">Read all reviews on Google</a>
    </blockquote>
  </div>
</section>

<div class="jhp-div" aria-hidden="true"></div>

<a class="jhp-band" href="../experience/">
  <img src="%(cdn)s3092823b-efc9-44f8-97ef-b73b65d8ae2f.jpg"
       width="1600" height="1065" loading="lazy"
       alt="A client photographed on the studio floor at JHP Boudoir">
  <span class="over">
    <span class="jhp-kicker">How it works</span>
    <h2 class="jhp-h jhp-h-lg">What the Day Looks Like</h2>
    <span class="sub">Every step, from the first call to the reveal.</span>
    <span class="jhp-btn">Walk me through it</span>
  </span>
</a>

<script>
  /* Draws each divider in as it arrives. Everything here is an
     enhancement: the CSS renders the dividers finished, and js-rev is what
     collapses them ready to animate, so if any one of these checks fails
     the page keeps its dividers and simply does not move them.

     unobserve on the first intersection is what makes it run once. Landing
     part way down the page leaves the dividers above the fold undrawn, and
     that is correct: scrolling up brings them on screen from the top,
     which the observer sees exactly as it sees one arriving from the
     bottom. */
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
    }, { rootMargin: "0px 0px -12%% 0px" });
    rules.forEach((r) => io.observe(r));
  })();
</script>
""" % {"cdn": CDN}

out = HEAD + shared[shared.index("/* SHARED DESIGN SYSTEM"):] + parts + vip \
    + FAQ_CSS + "</style>\n\n" + nav + BODY + "\n" + foot
out = out.replace("</html>\n", "</html>\n")
(ROOT / "scalogy-faq.html").write_text(out)
print("wrote", len(out.encode()), "bytes,",
      out.count('<details name="faq">'), "questions,", out.count('class="fill"'), "blanks")
