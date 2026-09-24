#!/usr/bin/env python3
"""Generates scalogy-experience.html -- The Experience, the second page
under Info and the one the FAQ's closing band walks people to.

Same arrangement as build-info.py: the tokens, the type, the nav, the
intro band, the divider, the pull-quote, the closing band and the footer
are all sliced out of scalogy-portfolio.html at build time, so a change
to the design system reaches this page without anyone remembering to.

Three components are this page's own and are commented where they are
defined below: the studio set (one tall frame beside two wide ones), the
four inclusions, and the six-step process with its drawn spine.

Six photographs, six different women. A page about what happens to you
here reads as a brochure for one client if the same face opens it and
closes it.

Every figure on this page is Jessica's, given on 23 September: fifteen
minutes for the consultation call, two to three hours on session day,
seven to fourteen business days to the reveal, six weeks to delivery for
anything printed. The only thing still missing is where pricing starts,
and that number is not written here -- the page says the Session Guide
carries it, which is true and needs no blank.
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

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Experience | JHP Boudoir</title>
<meta name="description" content="Every step of a JHP Boudoir session, from the first message to the album in your hands: the studio, what is included, and how long each part takes. Jefferson City, Missouri.">
<meta name="robots" content="noindex, nofollow">
<meta property="og:title" content="The Experience | JHP Boudoir">
<meta property="og:description" content="What the day looks like, start to finish.">
<meta property="og:type" content="website">
<style>html,body{margin:0;padding:0;background:#13100E}body{overflow-x:hidden}</style>
</head>
<body>
{% raw %}
<div class="jhp-home">
<style>
"""

PAGE_CSS = """
/* THE INTRO'S SENTENCE
   --------------------
   The Portfolio and the FAQ open on a kicker and a heading and nothing
   else. This page is answering a question somebody clicked a button to
   ask, so it gets one line under the heading to say what it is about.
   Measured at 46 characters so it breaks to two lines on a desktop and
   does not turn into a paragraph on the band. */
.jhp-home .jhp-intro .lede{font-family:var(--sans);font-weight:300;
  font-size:clamp(15px,1.5vw,17.5px);line-height:1.65;color:var(--ink);
  opacity:.86;margin:14px 0 0;max-width:46ch}
/* And a deeper scrim than the shared one to put all three lines on. The
   shared gradient is only a third opaque by the middle of the band, which
   is enough for a heading over a floor and not enough over this frame:
   the library is lit shelf by shelf all the way across, so the kicker --
   eleven pixels of gold, the smallest type on the band -- was landing on
   a lamp-lit row of books and vanishing into it. The weight is added
   between a quarter and two thirds of the way up, where the three lines
   sit; the top of the band is left alone so the room still reads. */
.jhp-home .jhp-intro .jhp-over{background:linear-gradient(0deg,
  rgba(19,16,14,.95) 0%,rgba(19,16,14,.85) 27%,
  rgba(19,16,14,.55) 55%,rgba(19,16,14,.08) 84%)}

/* THE STUDIO
   ----------
   One tall frame beside two wide ones. The shape is the argument: the
   room is the thing being sold here, and a row of three equal tiles would
   have had to crop all three to the same box -- which on a 3:2 frame of a
   whole room means throwing away the room and keeping the woman.

   So the wide frames stay wide. Only they carry a ratio box, which makes
   the right-hand column set the height of the row; the tall frame has no
   height of its own at all and is stretched to whatever that comes to by
   the grid, which is why the two columns line up at every width without a
   fixed number anywhere. At 1440 the row is 918px and the tall frame is
   486 across, so it crops about 60px off each side of its 3:2 -- the
   mantel and the candles are well inside that.

   The frames were chosen for three different sets -- brick and candles,
   the gilt mirror under the windows, the green velvet against brick --
   because "multiple sets" is a claim in the copy beside them and one
   room photographed three times would quietly contradict it. */
.jhp-home .jhp-studio{display:grid;
  grid-template-columns:minmax(0,.72fr) minmax(0,1fr);
  gap:clamp(12px,1.4vw,18px);max-width:1180px;margin:clamp(30px,4vw,46px) auto 0}
.jhp-home .jhp-studio .stack{display:grid;gap:clamp(12px,1.4vw,18px);
  grid-template-rows:1fr 1fr;min-width:0}
.jhp-home .jhp-studio figure{position:relative;margin:0;min-width:0;
  overflow:hidden;background:var(--surface)}
.jhp-home .jhp-studio figure img{position:absolute;inset:0;width:100%;
  height:100%;object-fit:cover;transition:transform .9s ease}
.jhp-home .jhp-studio figure:hover img{transform:scale(1.03)}
.jhp-home .jhp-studio .wide::before{content:"";display:block;padding-top:66.6%}
/* The two frames in the right column are landscape and the left one is a
   portrait of a whole wall; cover would take the mantel off the top of
   one and the ceiling off the other. Each is anchored where its room is. */
.jhp-home .jhp-studio .tall img{object-position:50% 34%}
.jhp-home .jhp-studio .wide-a img{object-position:50% 40%}
.jhp-home .jhp-studio .wide-b img{object-position:50% 46%}
@media (max-width:820px){
  /* One column, edge to edge, which is this site's rule for photographs
     on a phone. There is no second column left for the tall frame to be
     stretched against, so here it is the one that needs a box of its own
     -- shallower than its 3:2, because full height it would be a 520px
     wall to scroll past. */
  .jhp-home .jhp-studio{grid-template-columns:1fr;
    margin-inline:calc((100% - 100vw) / 2);gap:0}
  .jhp-home .jhp-studio .stack{grid-template-rows:auto auto;gap:0}
  .jhp-home .jhp-studio .tall::before{content:"";display:block;padding-top:133%}
  .jhp-home .jhp-studio figure:hover img{transform:none}
}

/* THE INCLUSIONS
   --------------
   Four things, set as two columns of two. Each is headed by the same
   small gold lozenge the divider carries, rotated out of a square, so
   the page has one decorative mark and not five.

   No icons. Four line drawings of a comb, a hanger, a chandelier and a
   pair of hands would be four more things to load and would read as a
   pricing table on a software site. The gold mark and the serif heading
   do the same job in the typeface the rest of the page is set in. */
.jhp-home .jhp-inc{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));
  gap:clamp(26px,3.6vw,52px) clamp(30px,5vw,80px);
  max-width:960px;margin:clamp(30px,4vw,44px) auto 0;text-align:left}
.jhp-home .jhp-inc .it{position:relative;padding-left:26px}
.jhp-home .jhp-inc .it::before{content:"";position:absolute;left:0;top:.62em;
  width:7px;height:7px;transform:rotate(45deg);
  background:var(--ground);border:1px solid var(--gold)}
.jhp-home .jhp-inc h3{font-family:var(--serif);font-weight:500;
  font-size:clamp(19px,1.8vw,22px);line-height:1.3;color:var(--ink);
  margin:0 0 9px;letter-spacing:.01em}
.jhp-home .jhp-inc p{font-family:var(--sans);font-weight:300;font-size:16px;
  line-height:1.75;color:var(--muted);margin:0}
@media (max-width:760px){
  .jhp-home .jhp-inc{grid-template-columns:1fr;gap:26px;text-align:left}
  .jhp-home .jhp-inc h3{font-size:var(--ph-head);margin-bottom:7px}
  .jhp-home .jhp-inc p{font-size:var(--ph-body);line-height:1.7}
}

/* THE PROCESS
   -----------
   Two columns of three: one, two, three down the left and four, five,
   six down the right, which is how a numbered list is set in two columns
   anywhere else.

   Each column is joined by a real hairline with the step numbers sitting
   on it, in discs of the page's own background so the line appears to
   pass behind them. Numbers are the serif face: they are the only
   figures on the page and they should read as type, not as a UI.

   The line is one segment per step rather than one line per column,
   because a single line has no way of knowing where its last number is
   -- it ran on past the bottom step to the foot of its paragraph. A
   segment belongs to its own step, and the step at the foot of each
   column simply has none, so the line ends inside that disc.

   Segments run to the bottom of their grid row rather than to the bottom
   of their own text, so the six steps can be six different lengths and
   the line still comes out continuous. That is also why there is no row
   gap: the space between steps is padding inside them, which the segment
   covers, and a gap would have broken the line into dashes.

   Nothing joins the foot of the left column to the head of the right.
   The numbers carry that jump, as they do in print -- and so does the
   draw-in below, which runs down the left column and then down the
   right, in reading order. */
.jhp-home .jhp-flow{position:relative;max-width:1080px;
  margin:clamp(30px,4vw,44px) auto 0;list-style:none;padding:0;
  display:grid;grid-template-columns:repeat(2,minmax(0,1fr));
  grid-template-rows:repeat(3,auto);grid-auto-flow:column;
  column-gap:clamp(34px,5vw,76px)}
.jhp-home .jhp-flow li{position:relative;padding:0 0 clamp(26px,3.4vw,38px) 62px;
  text-align:left}
.jhp-home .jhp-flow li::before{content:"";position:absolute;left:21px;top:10px;
  bottom:0;width:1px;background:var(--line)}
.jhp-home .jhp-flow li:nth-child(3)::before,
.jhp-home .jhp-flow li:nth-child(6)::before{content:none}
.jhp-home .jhp-flow li:nth-child(3),
.jhp-home .jhp-flow li:nth-child(6){padding-bottom:0}
.jhp-home .jhp-flow .n{position:absolute;left:0;top:-2px;width:43px;height:43px;
  display:flex;align-items:center;justify-content:center;border-radius:50%;
  background:var(--ground);border:1px solid var(--line);
  font-family:var(--serif);font-size:19px;font-weight:500;color:var(--gold);
  letter-spacing:.02em}
.jhp-home .jhp-flow h3{font-family:var(--serif);font-weight:500;
  font-size:clamp(20px,1.9vw,24px);line-height:1.3;color:var(--ink);
  margin:5px 0 9px;letter-spacing:.01em}
.jhp-home .jhp-flow p{font-family:var(--sans);font-weight:300;font-size:16.5px;
  line-height:1.78;color:var(--muted);margin:0 0 12px}
.jhp-home .jhp-flow p:last-child{margin-bottom:0}
/* The one piece of timing the eye should catch without reading. */
.jhp-home .jhp-flow .when{display:inline-block;margin:0 0 9px;
  font-family:var(--sans);font-size:11px;font-weight:400;letter-spacing:.24em;
  text-transform:uppercase;color:var(--gold)}
/* Below a tablet the two columns would be about 340px each, which is a
   40-character measure with a 62px indent taken out of it first. One
   column of six instead -- and then step three is in the middle of the
   run again and needs its segment back, while step six is the only one
   at the foot of anything. */
@media (max-width:820px){
  .jhp-home .jhp-flow{display:block;max-width:760px}
  .jhp-home .jhp-flow li:nth-child(3)::before{content:""}
  .jhp-home .jhp-flow li:nth-child(3){padding-bottom:clamp(26px,3.4vw,38px)}
}
@media (max-width:620px){
  .jhp-home .jhp-flow li::before{left:17px}
  .jhp-home .jhp-flow li{padding-left:50px}
  .jhp-home .jhp-flow .n{width:35px;height:35px;font-size:16px;top:0}
  .jhp-home .jhp-flow h3{font-size:var(--ph-head);margin-top:2px}
  .jhp-home .jhp-flow p{font-size:var(--ph-body);line-height:1.72}
  .jhp-home .jhp-flow .when{font-size:var(--ph-label);letter-spacing:.2em}
}
/* The spine draws down as the list arrives, on the same opt-in as the
   dividers: without js-rev it is simply a line. Six steps is the one
   place on this site where a reader is being asked to follow an order,
   and a line that draws in that order is the cheapest way to say so. */
.jhp-home.js-rev .jhp-flow li::before{transform:scaleY(0);transform-origin:50% 0;
  transition:transform .34s linear}
.jhp-home.js-rev .jhp-flow.in li::before{transform:scaleY(1)}
/* Staggered so it reads as one line travelling through the steps rather
   than as four lines growing at once -- down the left column, then down
   the right, which is the only thing on the page that shows the jump
   from step three to step four. Steps three and six carry no segment, so
   they take no delay. */
.jhp-home.js-rev .jhp-flow.in li:nth-child(1)::before{transition-delay:.05s}
.jhp-home.js-rev .jhp-flow.in li:nth-child(2)::before{transition-delay:.39s}
.jhp-home.js-rev .jhp-flow.in li:nth-child(4)::before{transition-delay:.73s}
.jhp-home.js-rev .jhp-flow.in li:nth-child(5)::before{transition-delay:1.07s}
/* One column, so the run is one to five and step three is back in it. */
@media (max-width:820px){
  .jhp-home.js-rev .jhp-flow.in li:nth-child(3)::before{transition-delay:.73s}
  .jhp-home.js-rev .jhp-flow.in li:nth-child(4)::before{transition-delay:1.07s}
  .jhp-home.js-rev .jhp-flow.in li:nth-child(5)::before{transition-delay:1.41s}
}

/* This page's bands carry different photographs from the Portfolio's, so
   they carry different crops. Every other line of the two bands is the
   Portfolio's, sliced above.

   The top band is the library: bookcase wall, clock, the mirror and the
   window beyond it. Anchored high, at 20%, so the heading lands on the
   dark lower shelves and the whole room stays in -- a centred crop put
   the second line of the heading across her legs.

   The closing band's heading is set left, so it needed the left third
   quiet: she stands centre-right against the gilt mirror and the words
   sit on the plant and the dark wall beside her.

   Both were swept at 1440 with the real words on them rather than judged
   from a contact sheet. At a quarter scale a heading looks clear of a
   subject it is in fact sitting on top of. */
.jhp-home .jhp-intro img{object-position:50% 20%}
.jhp-home .jhp-band img{object-position:50% 50%}
/* 1024 rather than the 620 the rest of the page breaks at, because what
   changes here is not the phone: it is the band losing its depth. At 1440
   it is 533px tall and the library has room to be a room. By 865 the
   clamp has bottomed out at 320 and the same wall is squeezed into a
   third of the height, which makes it the busiest thing on the page --
   so the frame is anchored low from a tablet down, on the dark bottom
   shelves, and the scrim is deepened again over the one above.

   The height is restated because the slice above sets 220 at 620: that
   is the number Jessica tuned in the band tuner for a frame carrying two
   lines of type. This band carries four -- kicker, two lines of heading,
   two of sentence -- and at 220 they filled it to the top edge.

   Neither band has horizontal slack at these widths. A 3:2 frame in a box
   this wide scales to the width, so only the vertical number does
   anything, and the closing band's crop below is for the phone alone. */
@media (max-width:1024px){
  .jhp-home .jhp-intro img{height:320px;object-position:50% 78%}
  .jhp-home .jhp-intro .jhp-over{background:linear-gradient(0deg,
    rgba(19,16,14,.96) 0%,rgba(19,16,14,.88) 30%,
    rgba(19,16,14,.52) 62%,rgba(19,16,14,.1) 88%)}
}
@media (max-width:620px){
  /* The closing band is the other way about at this width: taller than a
     3:2 frame's shape, so it scales to the height and crops 91px at the
     sides. Anchored hard left, which takes all of that off the right and
     walks her as far from the words as the frame allows.

     The Portfolio's phone scrim came over with the band and is weighted
     for a candle-lit frame with a bright subject in the middle of it.
     This one is already a dark room, and under that weight the left half
     went black -- a heading on a rectangle, with the mirror, the rug and
     the woman all gone. Lighter on both axes; the type still holds. */
  .jhp-home .jhp-band img{object-position:0% 50%}
  .jhp-home .jhp-band .over{background:
    linear-gradient(0deg,rgba(19,16,14,.72) 0%,rgba(19,16,14,.4) 58%,
      rgba(19,16,14,.3) 100%),
    linear-gradient(90deg,rgba(19,16,14,.8) 0%,rgba(19,16,14,.46) 52%,
      rgba(19,16,14,.06) 100%)}
}
"""

BODY = """
<section class="jhp-intro">
  <img src="%(cdn)s6ab3ee86fef86e60d5226fb9.jpg"
       width="1600" height="1065"
       alt="The library set at the JHP Boudoir studio, a client photographed in front of the bookcase wall">
  <div class="jhp-over">
    <p class="jhp-kicker">The Experience</p>
    <h1 class="jhp-h jhp-h-lg">What the Day Looks Like</h1>
    <p class="lede">Every step, from the first message to the album in your
       hands. None of this should be a surprise.</p>
  </div>
</section>

<section class="jhp-sec" style="border-bottom:none">
  <div class="jhp-center-wide">
    <h2 class="jhp-h jhp-h-lg">A Studio Designed Exactly for Boudoir</h2>
    <p class="jhp-p">High ceilings, wood beams, chandeliers and brick, and
       more than one set to move between &mdash; so a single session gives you
       photographs that do not all look like they were taken in the same
       corner.</p>
    <p class="jhp-p">It is a private studio, by appointment only. For the
       hours you are here it is yours: no waiting room, no one else booked
       after you, nobody walking through. Just the two of us, good light, and
       a playlist you picked.</p>
  </div>

  <div class="jhp-studio">
    <figure class="tall">
      <img src="%(cdn)s6ab3ee7918384d888bb3d890.jpg"
           width="1065" height="1600" loading="lazy"
           alt="The fireplace set at JHP Boudoir, exposed brick and a mantel lit with candles">
    </figure>
    <div class="stack">
      <figure class="wide wide-a">
        <img src="%(cdn)s6ab3ee828bf21de2ae408336.jpg"
             width="1600" height="1065" loading="lazy"
             alt="A client photographed beside the floor-to-ceiling gilt mirror under the studio windows">
      </figure>
      <figure class="wide wide-b">
        <img src="%(cdn)sce79ce12-548d-4471-b9b2-282da4e1c2e9.jpg"
             width="1600" height="1065" loading="lazy"
             alt="A client photographed on the green velvet sofa against the studio's brick wall">
      </figure>
    </div>
  </div>
</section>

<div class="jhp-div" aria-hidden="true"></div>

<section class="jhp-sec" style="border-bottom:none">
  <div class="jhp-quote">
    <figure class="shot">
      <img src="%(cdn)s46a7d597-eea6-449f-9299-c3798b846f22.jpg"
           width="1065" height="1600" loading="lazy"
           alt="A boudoir portrait made at the JHP Boudoir studio">
    </figure>
    <blockquote>
      <p class="qt">&ldquo;Jessica was fabulous from the very first contact to
         the image reveal! Very professional and made the whole experience
         amazing! Would definitely do this experience again with her and highly
         recommend!&rdquo;</p>
      <p class="qa">Miss N.</p>
      <a class="src" href="https://www.google.com/search?q=JHP+Boudoir&amp;kgmid=/g/11v3x9fqm9"
         target="_blank" rel="noopener">Read all reviews on Google</a>
    </blockquote>
  </div>
</section>

<div class="jhp-div" aria-hidden="true"></div>

<section class="jhp-sec" style="border-bottom:none">
  <div class="jhp-center-wide">
    <p class="jhp-kicker">Included</p>
    <h2 class="jhp-h jhp-h-lg">What Comes With Every Session</h2>
  </div>

  <div class="jhp-inc">
    <div class="it">
      <h3>Professional Hair and Makeup</h3>
      <p>Done here at the studio before we shoot, by someone who does this for
         a living. You do not need to arrive ready and you do not need to book
         it separately &mdash; it is part of the session.</p>
    </div>
    <div class="it">
      <h3>The Client Wardrobe</h3>
      <p>A full wardrobe here for you to borrow from, so you are not shopping
         for something you will wear once. Bring what you love if you have it;
         pull from mine if you do not.</p>
    </div>
    <div class="it">
      <h3>The Studio Itself</h3>
      <p>High ceilings, wood beams, chandeliers, and several sets to work
         through in one session &mdash; brick and candlelight, the gilt mirror
         under the windows, green velvet, the library wall.</p>
    </div>
    <div class="it">
      <h3>Professional Posing, Head to Toe</h3>
      <p>Where your chin goes, what your hands are doing, where your weight
         sits. I show you rather than describe it, and I do it for the whole
         session. You will never be left standing there guessing.</p>
    </div>
  </div>
</section>

<div class="jhp-div" aria-hidden="true"></div>

<section class="jhp-sec" style="border-bottom:none">
  <div class="jhp-center-wide">
    <p class="jhp-kicker">Step by step</p>
    <h2 class="jhp-h jhp-h-lg">How It All Works</h2>
  </div>

  <ol class="jhp-flow">
    <li>
      <span class="n" aria-hidden="true">1</span>
      <h3>Inquire</h3>
      <p>Send me a message and I will send you the Session Guide &mdash; the
         studio, the experience, what a session includes and where pricing
         starts, all in one place. Read it in your own time, with no one
         waiting on an answer.</p>
    </li>
    <li>
      <span class="n" aria-hidden="true">2</span>
      <p class="when">Fifteen minutes</p>
      <h3>Consultation Call</h3>
      <p>A short call &mdash; fifteen minutes at the most. We go over the
         details, I answer anything the guide did not, and if it feels right we
         get your session on the calendar.</p>
    </li>
    <li>
      <span class="n" aria-hidden="true">3</span>
      <h3>Before the Session</h3>
      <p>Prep guides arrive by email in the weeks before your session: what to
         wear, what to bring, how to prepare, what to expect on the day. You
         will not be left to work any of it out on your own.</p>
    </li>
    <li>
      <span class="n" aria-hidden="true">4</span>
      <p class="when">Two to three hours</p>
      <h3>Session Day</h3>
      <p>Hair and makeup first, then we shoot. Your session experience will
         last 2&ndash;3 hours on average.</p>
    </li>
    <li>
      <span class="n" aria-hidden="true">5</span>
      <p class="when">7&ndash;14 business days later</p>
      <h3>Image Reveal</h3>
      <p>We sit down together and go through your images for the first time,
         7&ndash;14 business days after your session. You choose which
         ones you want to keep and how you want them &mdash; and you order them
         here, at the same appointment.</p>
      <p>You are not sent a link and left to work it out alone. It is most
         women&rsquo;s favourite part of the whole thing.</p>
    </li>
    <li>
      <span class="n" aria-hidden="true">6</span>
      <h3>Product Delivery</h3>
      <p>Your digital images are yours the moment the reveal ends. Albums, wall
         art and anything else printed are made to order and arrive at your
         door within 6 weeks of that appointment.</p>
    </li>
  </ol>
</section>

<div class="jhp-div" aria-hidden="true"></div>

<a class="jhp-band" href="/contact">
  <img src="%(cdn)s31196c8e-202f-429f-bbcd-7134a55a8caa.jpg"
       width="1600" height="1065" loading="lazy"
       alt="A client photographed in front of the gilt mirror at the JHP Boudoir studio">
  <span class="over">
    <span class="jhp-kicker">Ready when you are</span>
    <h2 class="jhp-h jhp-h-lg">Let&rsquo;s Talk About Your Session</h2>
    <span class="sub">Fifteen minutes on the phone, and every question
      answered.</span>
    <span class="jhp-btn">Book my call</span>
  </span>
</a>

<script>
  /* Draws the dividers and the process spine in as they arrive. Everything
     here is an enhancement: the CSS renders all of it finished, and js-rev
     is what collapses it ready to animate, so if any one of these checks
     fails the page keeps its dividers and its spine and simply does not
     move them.

     The selector is the one line that differs from the other pages --
     this is the only page with a spine to draw.

     unobserve on the first intersection is what makes it run once. Landing
     part way down the page leaves the marks above the fold undrawn, and
     that is correct: scrolling up brings them on screen from the top,
     which the observer sees exactly as it sees one arriving from the
     bottom. */
  (() => {
    const home = document.querySelector(".jhp-home");
    const rules = home ? home.querySelectorAll(".jhp-div, .jhp-flow") : [];
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
    + PAGE_CSS + "</style>\n\n" + nav + BODY + "\n" + foot
(ROOT / "scalogy-experience.html").write_text(out)
print("wrote", len(out.encode()), "bytes,",
      out.count("<li>"), "steps,", out.count('class="it"'), "inclusions")
