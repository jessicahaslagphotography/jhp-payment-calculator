#!/usr/bin/env python3
"""Builds scalogy-guide.html -- the Session Guide Magazine at /session-guide.

WHY THIS EXISTS AS A PAGE AND NOT A CANVA EXPORT

The guide Jessica has been sending is a 21-page PDF made in Canva, emailed out
of GHL to every woman who fills in /contact. On 24 September it turned out to
contradict this site in nine places, and the reason is structural rather than
careless: a PDF is a photograph of the truth on the day it was exported. Every
figure in it has to be re-typed by hand, in Canva, and re-uploaded to GHL
before a single woman sees the correction.

This is the same document as a page. The figures live in FIGURES below, once,
and the copy is built around them -- so the next time a price moves it moves
here and the guide is already correct. GHL emails the link instead of the
attachment. build-guide.py --pdf renders the same page to a PDF for the times
she wants a file.

WHAT IS HERS AND WHAT IS NOT

Almost every word here is lifted from her own guide, in her own voice, down to
"best ass-sets" and "bodacious babe". What changed is only what her 24
September figures forced:

  the day        4-5 hours -> 2-3 hours
  the reveal     same day, in person, "I do not offer online galleries"
                 -> a private Zoom appointment 7-14 business days later
  delivery       6-8 weeks after the session
                 -> within 6 weeks of the Zoom reveal
  session fee    $500 -> $697
  Collections    from $2,800 -> Petite from $1,250, Full from $3,400, eight
  booking        18 months -> 15 months
  studio hours   M-F 9am-4pm -> Mon-Thu 10am-3pm
  consultation   30 minutes in one place, 20 in another -> 20, the length of
                 her actual GHL calendar
  location       "located in Jefferson City" -> "just outside Jefferson City",
                 which is what every other page says

The reveal moving is the one that rewrites rather than edits. Her session-day
page was built around a same-day ordering appointment -- 10AM start, lunch at
12, back by 2:30, ordering by 3 -- and none of that survives a 2-3 hour day
with the reveal a fortnight later over Zoom. So HOW THE SESSION DAY WORKS and
YOUR IMAGE REVEAL are written fresh from her facts. The intent of the line she
cared about is kept: you are not sent a link and left alone with it.

FOUR THINGS ARE DELIBERATELY MISSING, because she has not said and the old
figure may or may not still hold. Each is marked ASK below:
  - the session fee split (it was 2 x $250 against a $500 fee)
  - album pricing (the old guide said $1,500 to $3,500 standalone)
  - her age and "photographing for 4 years", both of which decay
  - the session start time (the old 10AM Tue-Thu is inside the new Mon-Thu
    10am-3pm window, but a 2-3 hour day fits it differently)
Nothing here states any of them. Adding a figure back is a decision, not a
tidy-up.
"""
import os, re, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent
CDN = "https://assets.cdn.filesafe.space/Pcnm8GVNMmWTY65qVOAp/media/"
src = (ROOT / "scalogy-portfolio.html").read_text()

# ---------------------------------------------------------------- the figures
# The single source of truth for this document. Jessica, 24 September. If one
# of these moves, it moves here and nowhere else in this file.
F = {
    "fee":            "$697",
    "petite":         "$1,250",
    "full":           "$3,400",
    "collections":    "eight",
    "day":            "two to three hours",
    "reveal_wait":    "7&ndash;14 business days",
    "delivery":       "within 6 weeks",
    "booking_window": "15 months",
    "studio_hours":   "Monday to Thursday, 10am&ndash;3pm",
    "call_hours":     "Monday to Friday, 8am&ndash;5pm",
    "consult":        "20 minute",
    "wardrobe":       "160",
    "sqft":           "2,000",
    "shown":          "50 to 100",
}
CALENDAR = "https://api.leadconnectorhq.com/widget/booking/mi2EqYRq4gGEbBJHe82b"
VIP = "https://www.facebook.com/groups/1107773373084834"

# The design system, sliced rather than copied -- the same three cuts
# build-contact.py and build-inquiry.py take, for the same reason.
MARK_END = "/* The closing band carries no photograph."
shared = src[:src.index("/* THE INDEX")]
parts = (src[src.index("/* THE INTRO"):src.index("/* THE QUOTE")]
         + src[src.index("/* THE WAY ON"):src.index(MARK_END)])
tail = src[src.index(MARK_END):]
after_style = tail[tail.index("</style>"):]
nav = after_style[after_style.index('<nav class="jhp-nav">'):
                  after_style.index("</nav>") + len("</nav>\n")]
foot = after_style[after_style.index('<footer class="jhp-foot">'):]

# ------------------------------------------------------------------ the CSS
# Everything this document adds on top of the sliced system. It is a long read
# rather than a landing page, so the rules here are about sustained reading:
# one measure, a clear question-to-answer rhythm, and photographs that break
# the column rather than decorate it.
GUIDE_CSS = """
/* THE GUIDE
   ---------
   A 21-page magazine as one page. The shape of the original is kept -- it is
   a run of questions a woman actually asks, in her order -- because that
   order is the thing that makes it readable rather than a specification.

   ONE MEASURE, 62 CHARACTERS. The body copy never changes width, at any
   screen, and every photograph and panel is measured against it. A long
   document that changes its measure as it goes is what makes a reader lose
   their place.

   Nothing here is a new colour, a new typeface or a new size. The questions
   are .jhp-h at the section size, the answers are .jhp-p, and the only new
   objects are the three panels below -- the fact card, the included list and
   the day. */
.jhp-home .jhp-gd{max-width:62ch;margin:0 auto}
.jhp-home .jhp-gd > * + *{margin-top:18px}
.jhp-home .jhp-gd .q{margin:0 0 16px}
/* A question after an answer needs air above it or the document reads as one
   undifferentiated column. 56px is the same rhythm the sections use. */
.jhp-home .jhp-gd .q:not(:first-child){margin-top:clamp(42px,5vw,64px)}
.jhp-home .jhp-gd .lead{font-size:19px;line-height:1.7;color:var(--ink)}
.jhp-home .jhp-gd em{font-style:italic;color:var(--ink)}
.jhp-home .jhp-gd strong{font-weight:500;color:var(--ink)}
.jhp-home .jhp-gd a:not(.jhp-btn){color:var(--gold);
  border-bottom:1px solid var(--line);transition:color .3s,border-color .3s}
.jhp-home .jhp-gd a:not(.jhp-btn):hover{color:var(--gold-bright);
  border-color:var(--gold-bright)}

/* The contents. Jessica cut a five-point list off /contact on 24 September
   because that page is four fields and a paragraph, and a contents list over
   a form is furniture. This document is the opposite case: it is long on
   purpose -- her own words are "this guide is very thorough...which means
   it's long!" -- and a woman who only wants the price should not have to
   scroll past the retouching answer to find it. Anchors, not JavaScript. */
.jhp-home .jhp-toc{max-width:62ch;margin:0 auto;padding:22px 26px;
  background:var(--surface);border:1px solid var(--line);border-radius:2px}
.jhp-home .jhp-toc h2{font-family:var(--sans);font-weight:400;font-size:11px;
  letter-spacing:.26em;text-transform:uppercase;color:var(--gold);
  margin:0 0 14px}
.jhp-home .jhp-toc ul{list-style:none;display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));gap:2px 26px}
.jhp-home .jhp-toc a{display:block;padding:9px 0;font-family:var(--sans);
  font-weight:300;font-size:14.5px;line-height:1.4;color:var(--muted);
  border-bottom:1px solid var(--line-soft);transition:color .3s}
.jhp-home .jhp-toc a:hover{color:var(--gold)}
@media (max-width:620px){
  .jhp-home .jhp-toc{padding:18px 20px}
  .jhp-home .jhp-toc ul{grid-template-columns:1fr}
  /* 13px of line plus 15px either side is the 44px a thumb needs, which a
     22-item list has to honour or it is unusable on the device most of these
     women are reading on. */
  .jhp-home .jhp-toc a{padding:15px 0;font-size:var(--ph-body)}
}

/* A photograph that breaks the column. Full-bleed on a phone, and on a
   desktop wider than the measure so the document breathes between answers
   without the reader losing the left edge. */
.jhp-home .jhp-plate{max-width:980px;margin:clamp(42px,5vw,64px) auto;
  position:relative}
.jhp-home .jhp-plate img{width:100%;height:auto}
.jhp-home .jhp-plate figcaption{margin:10px 0 0;font-family:var(--sans);
  font-weight:300;font-size:12.5px;letter-spacing:.04em;color:var(--dim);
  text-align:center}
@media (max-width:620px){
  .jhp-home .jhp-plate{max-width:none;margin-inline:calc((100% - 100vw) / 2);
    margin-block:34px}
  .jhp-home .jhp-plate figcaption{padding:0 var(--ph-gut)}
}

/* THE FACT CARD -- what the session fee is, what a Collection starts at.
   The figures are the thing a woman scrolls this document looking for, so
   they are set as figures rather than buried in a sentence. Raised off the
   page, gold hairline, the number at display size. */
.jhp-home .jhp-card{max-width:62ch;margin:clamp(30px,3.6vw,42px) auto;
  padding:clamp(24px,3vw,34px);background:var(--surface);
  border:1px solid var(--line);border-radius:2px}
.jhp-home .jhp-card .lb{font-family:var(--sans);font-weight:400;font-size:11px;
  letter-spacing:.26em;text-transform:uppercase;color:var(--gold);
  margin:0 0 10px}
.jhp-home .jhp-card .fig{font-family:var(--serif);font-weight:600;
  font-size:clamp(34px,4.4vw,52px);line-height:1;color:var(--ink);margin:0}
.jhp-home .jhp-card .fig .u{font-family:var(--sans);font-weight:300;
  font-size:15px;letter-spacing:.02em;color:var(--muted);margin-left:10px}
.jhp-home .jhp-card p{font-family:var(--sans);font-weight:300;font-size:15.5px;
  line-height:1.7;color:var(--muted);margin:14px 0 0}
.jhp-home .jhp-card p:first-of-type{margin-top:16px}
/* Two figures side by side for the Collections, one each. They stack on a
   phone rather than shrinking, because a price set at 20px is not a price. */
.jhp-home .jhp-card.two{display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(20px,3vw,34px)}
.jhp-home .jhp-card.two .fig{font-size:clamp(28px,3.4vw,40px)}
@media (max-width:620px){
  .jhp-home .jhp-card.two{grid-template-columns:1fr;gap:26px}
}

/* THE INCLUDED LIST. Her own seven lines, set as a list rather than a
   paragraph because that is how they are read -- scanned for the one thing
   she is checking for. The rule under each is the same hairline the footer
   uses, not a bullet: a tick would claim these are features and they are
   simply what is in the room. */
.jhp-home .jhp-inc{list-style:none;margin:18px 0 0;padding:0}
.jhp-home .jhp-inc li{padding:13px 0 13px 26px;position:relative;
  font-family:var(--sans);font-weight:300;font-size:15.5px;line-height:1.6;
  color:var(--muted);border-top:1px solid var(--line-soft)}
.jhp-home .jhp-inc li:first-child{border-top:0;padding-top:4px}
.jhp-home .jhp-inc li::before{content:"";position:absolute;left:4px;top:22px;
  width:5px;height:5px;transform:rotate(45deg);background:var(--gold)}
.jhp-home .jhp-inc li:first-child::before{top:13px}

/* THE DAY. A numbered run rather than the process spine the Experience page
   uses: that one is six steps from first contact to delivery and this is the
   inside of one morning, so it wants to read as a sequence of hours. The
   numeral is a serif figure in gold, hung in the margin. */
.jhp-home .jhp-day{list-style:none;max-width:62ch;margin:22px auto 0;padding:0;
  counter-reset:d}
.jhp-home .jhp-day li{counter-increment:d;position:relative;
  padding:0 0 22px 46px}
.jhp-home .jhp-day li::before{content:counter(d);position:absolute;left:0;
  top:-4px;font-family:var(--serif);font-weight:600;font-size:26px;
  line-height:1;color:var(--gold)}
/* The line down the margin ties the numerals together and stops at the last
   one rather than trailing off under it. */
.jhp-home .jhp-day li::after{content:"";position:absolute;left:11px;top:24px;
  bottom:0;width:1px;background:var(--line-soft)}
.jhp-home .jhp-day li:last-child{padding-bottom:0}
.jhp-home .jhp-day li:last-child::after{content:none}
.jhp-home .jhp-day h3{font-family:var(--sans);font-weight:500;font-size:13px;
  letter-spacing:.14em;text-transform:uppercase;color:var(--ink);margin:0 0 7px}
.jhp-home .jhp-day p{font-family:var(--sans);font-weight:300;font-size:15.5px;
  line-height:1.7;color:var(--muted);margin:0}

/* The two session types, side by side. No photographs in these -- the studio
   and the outdoor sessions are both represented in the plates above, and a
   thumbnail each would make them look like products on a shelf. */
.jhp-home .jhp-two{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));
  gap:clamp(16px,2.4vw,26px);max-width:62ch;margin:22px auto 0}
.jhp-home .jhp-two > div{padding:clamp(20px,2.6vw,28px);
  background:var(--surface);border:1px solid var(--line);border-radius:2px}
.jhp-home .jhp-two h3{font-family:var(--serif);font-weight:600;font-size:23px;
  line-height:1.2;color:var(--ink);margin:0 0 6px}
.jhp-home .jhp-two .when{font-family:var(--sans);font-weight:400;font-size:10px;
  letter-spacing:.24em;text-transform:uppercase;color:var(--gold);margin:0 0 12px}
.jhp-home .jhp-two p{font-family:var(--sans);font-weight:300;font-size:15px;
  line-height:1.7;color:var(--muted);margin:0}
@media (max-width:620px){.jhp-home .jhp-two{grid-template-columns:1fr;gap:14px}}

/* The rules of the studio. Short, absolute, and set apart from the prose
   because they are the only lines in the document that are not an invitation.
   Not shouted -- a woman reading a guide does not need to be told off -- but
   not buried either. */
.jhp-home .jhp-rules{max-width:62ch;margin:clamp(26px,3.2vw,36px) auto 0;
  padding:20px 24px;border-left:2px solid var(--line);background:var(--surface)}
.jhp-home .jhp-rules p{font-family:var(--sans);font-weight:300;font-size:15px;
  line-height:1.7;color:var(--muted);margin:0}
.jhp-home .jhp-rules p + p{margin-top:10px}

/* The close. Her last page is a thank-you and a button, and it gets the full
   width so the document ends on something rather than trailing off. */
.jhp-home .jhp-end{max-width:62ch;margin:0 auto;text-align:center}
.jhp-home .jhp-end .jhp-btn{margin-top:8px}
.jhp-home .jhp-sig{font-family:var(--serif);font-style:italic;font-weight:400;
  font-size:26px;color:var(--gold);margin:22px 0 0}

@media (max-width:620px){
  .jhp-home .jhp-gd,.jhp-home .jhp-card,.jhp-home .jhp-day,
  .jhp-home .jhp-two,.jhp-home .jhp-rules,.jhp-home .jhp-end,
  .jhp-home .jhp-toc{max-width:none}
  .jhp-home .jhp-gd .lead{font-size:17px}
  .jhp-home .jhp-card{padding:20px}
  .jhp-home .jhp-rules{padding:16px 18px}
}

/* PRINTING, AND THE PDF BUILT FROM THIS PAGE.
   build-guide.py --pdf drives headless Chromium over this file, so what it
   emits is these rules. Two things have to be said outright: backgrounds are
   kept (a dark magazine printed as black type on white is a different
   document), and a question is never orphaned from its answer. */
@media print{
  .jhp-home{width:auto;left:auto;right:auto;margin:0;max-width:none}
  /* The nav and the contents are navigation, and a PDF has its own. The
     footer's Explore row is eight links to pages a reader of the file cannot
     click, and the wordmark is a screen-blend PNG that prints as a black
     square -- so both go, and the footer keeps the two things that are still
     true on paper: who the studio is, and how to reach it. */
  .jhp-home .jhp-nav,.jhp-home .jhp-toc,
  .jhp-home .jhp-foot .logo-mark,.jhp-home .jhp-foot .ftnav,
  .jhp-home .jhp-foot .social{display:none}
  .jhp-home .jhp-foot .cols{grid-template-columns:1fr 1fr}
  /* The site grades every photograph very slightly (saturate .96,
     contrast 1.02). On screen that is free; in a print render it forces
     the engine to rasterise each frame and re-embed it as an upscaled
     RGBA PNG, which took this file from a few megabytes to twenty-one.
     Off for print, the original JPEG is passed straight through. The
     grade is imperceptible on paper and the file has to survive an
     email. */
  .jhp-home img{filter:none}
  .jhp-home .jhp-gd .q,.jhp-home .jhp-two h3,.jhp-home .jhp-day h3,
  .jhp-home .jhp-card .lb{break-after:avoid;page-break-after:avoid}
  .jhp-home .jhp-plate,.jhp-home .jhp-card,.jhp-home .jhp-two > div,
  .jhp-home .jhp-day li,.jhp-home .jhp-rules{break-inside:avoid;
    page-break-inside:avoid}
  .jhp-home .jhp-sec{padding:26px 0}
  .jhp-home .jhp-foot{padding-top:26px}
}
"""

# ------------------------------------------------------------------ the copy
# Her guide, page by page, in her order. The voice is hers throughout -- where
# a sentence reads oddly formal or oddly blunt, that is because it is a
# transcription and not a rewrite.
#
# The photographs are eight different women, one frame each, which is the
# house rule: the same face opening and closing a document reads as the only
# woman who has ever been there. Alt text says what is honestly known about
# each frame -- studio, and colour or black and white -- rather than the one
# string the 165 gallery frames share. It would be better still if Jessica
# described them; that is a note in CLAUDE.md, not a thing to invent here.
HERO = "fe2033e0-3571-441e-8c98-089358e06f10.jpg"

TOC = [
    ("about",    "A Bit About Me"),
    ("studio",   "Where the Studio Is"),
    ("boudoir",  "So, What Is Boudoir?"),
    ("why",      "What Would I Do With Boudoir Portraits?"),
    ("thinner",  "Can You Make Me Look Thinner?"),
    ("portfolio","I Don&rsquo;t Look Like the Women in Your Portfolio"),
    ("who",      "Who Is Going to Be There?"),
    ("retouch",  "What About Retouching?"),
    ("wear",     "What Will I Wear?"),
    ("talk",     "Do I Get to Talk to You First?"),
    ("types",    "What Types of Sessions Do You Offer?"),
    ("day",      "How the Session Day Works"),
    ("reveal",   "Your Image Reveal"),
    ("delivery", "When the Albums and Prints Arrive"),
    ("book",     "What Do I Need to Do to Book?"),
    ("guests",   "Can Someone Come With Me?"),
    ("when",     "I Need My Images By a Certain Date"),
    ("spend",    "What Can I Expect to Spend?"),
    ("money",    "The Collections"),
    ("ready",    "Ready to Book?"),
]

def plate(f, alt, cap):
    return ('<figure class="jhp-plate">\n'
            '  <img src="%s%s" loading="lazy" alt="%s">\n'
            '  <figcaption>%s</figcaption>\n'
            '</figure>' % (CDN, f, alt, cap))

SCRIPT = """<script>
  /* HER NAME, OUT OF THE LINK
     ------------------------
     GHL builds the link with its own merge field, so the email sends her to
     .../session-guide/?n=Sarah and the page greets her by name. Three places
     change and no more: the eyebrow over the title, the first line, and the
     sign-off. A guide that says her name in every other paragraph reads like
     a mail merge, which is the opposite of the point.

     WHAT IS IN THAT PARAMETER IS A STRANGER'S TEXT. Anyone can type anything
     into a query string and send the link on, so it is treated as hostile:
     letters, spaces, hyphens and apostrophes only, one word, 24 characters,
     and it is written with textContent so the browser puts it on the page as
     words rather than as markup. innerHTML here would be a cross-site
     scripting hole on a page Jessica emails to her clients.

     WITHOUT a name -- someone who forwarded the link, or a merge field that
     came through empty -- nothing runs and the copy already in the markup
     stands on its own. That is why each slot holds real words rather than an
     empty span waiting to be filled. */
  (() => {
    const q = new URLSearchParams(location.search);
    const raw = q.get("n") || q.get("name") || q.get("first_name") || "";
    /* A merge field that did not resolve arrives literally. */
    if (!raw || raw.includes("{") || raw.includes("%7B")) return;

    /* Validated, not scrubbed. Stripping the bad characters out of
       "<img src=x onerror=...>" leaves "Img", and the page then greets her as
       Img -- safe, but it looks broken. A real first name matches this
       outright, so anything that does not is simply not a name and the
       default copy stands. */
    const clean = raw.trim().split(/\s+/)[0];
    if (!/^\p{L}[\p{L}'-]{1,23}$/u.test(clean)) return;
    /* SARAH and sarah both become Sarah. Names like O'Brien and Mary-Kate keep
       the capital after the punctuation, which is the whole reason this is not
       just one toUpperCase on the first letter. */
    const name = clean.toLowerCase().replace(
      /(^|['-])(\p{L})/gu, (m, sep, ch) => sep + ch.toUpperCase());

    document.querySelectorAll("[data-greet]").forEach((el) => {
      el.textContent = el.dataset.greet.replace("{name}", name);
    });
  })();
</script>
"""

BODY = """
<section class="jhp-intro">
  <img src="{cdn}{hero}" width="1600" height="1065"
       alt="A client photographed in the window light at the JHP Boudoir studio">
  <div class="jhp-over">
    <p class="jhp-kicker" data-greet="Prepared for {{name}}">JHP Boudoir</p>
    <h1 class="jhp-h jhp-h-lg">Your Session Guide</h1>
  </div>
</section>

<section class="jhp-sec" style="border-bottom:none">
  <div class="jhp-gd">
    <p class="jhp-p lead" data-greet="{{name}}, I am so glad you are here.">Welcome
       &mdash; I am so glad you are here.</p>
    <p class="jhp-p">This guide walks you through what a boudoir shoot is and
       how the process works here at JHP Boudoir. I am excited to get you in
       the studio.</p>
    <p class="jhp-p">If you have any questions after reading it, please reach
       out and I will get back to you as soon as I can. My studio hours are
       {studio_hours}, and consultation calls run {call_hours}.</p>
    <p class="jhp-p">This guide is very thorough &mdash; which means it is
       long. Sit down, grab a glass of your favourite whatever, and read it
       to the very end.</p>
  </div>

  <nav class="jhp-toc" aria-label="What is in this guide">
    <h2>What Is in Here</h2>
    <ul>{toc}</ul>
  </nav>

  <div class="jhp-gd">
    <h2 class="jhp-h q" id="about">A Bit About Me</h2>
    <p class="jhp-p">I am Jess. Wife to Zach, and I love the local weatherman
       with all my heart. Gin, tonic, lime.</p>
    <p class="jhp-p">Seven years of college and three degrees later, I ended up
       running my own business full time. I would not trade the journey.</p>
    <p class="jhp-p">I love changing lives through my art. Thank you for being
       here and for supporting my business &mdash; I cannot wait to meet you
       and make some of the most gorgeous photographs of yourself you will
       ever have.</p>

    <h2 class="jhp-h q" id="studio">Where the Studio Is</h2>
    <p class="jhp-p">The studio is just outside Jefferson City, Missouri. There
       is over {sqft} square feet of it: multiple set-ups, a hair and makeup
       room, a wardrobe room, and a sales area full of samples.</p>
    <p class="jhp-p">It is full of gorgeous natural light, vintage exposed
       brick, wood beams and glass chandeliers. It is a comforting space, and
       it was built for boudoir photography.</p>
  </div>

  {plate1}

  <div class="jhp-gd">
    <h2 class="jhp-h q" id="boudoir">So, What Is Boudoir?</h2>
    <p class="jhp-p">The French word <em>boudoir</em> means a woman&rsquo;s
       dressing room or bedroom, but I like to think of it as a fancy word for
       women&rsquo;s intimate portraiture. I want to make the most beautiful
       portraits of you that you will ever have.</p>
    <p class="jhp-p">Boudoir is <strong>not</strong> pornographic or overly
       sexual. It can be fun, flirty, beautiful, cute, sexy, feminine,
       intimate, candid, posed &mdash; or really anything else you want it to
       be.</p>
    <p class="jhp-p">If you have not already joined my private VIP group on
       Facebook, I highly suggest you do:
       <a href="{vip}" target="_blank" rel="noopener">the JHP Boudoir VIP
       group</a>.</p>

    <h2 class="jhp-h q" id="why">What Would I Do With Boudoir Portraits?</h2>
    <p class="jhp-p">I believe boudoir is the best gift you can give yourself
       &mdash; to capture your essence as you are right now. When you need a
       reminder of the strong, beautiful woman that you are, you will have a
       collection of amazing portraits to look at.</p>
    <p class="jhp-p">I love it when women come to me for themselves. The images
       we make together will boost your self esteem and your confidence, and
       that should be celebrated by you. It will help you reclaim your
       femininity and your sexuality, two things that are often lost as we get
       consumed with our lives, our jobs, our families.</p>
    <p class="jhp-p">Put that pep back in your step and reflect on the
       bodacious babe you are. Celebrate the body that you live in.</p>

    <h2 class="jhp-h q" id="thinner">Can You Make Me Look Thinner?</h2>
    <p class="jhp-p">I want to help you feel beautiful now, just the way you
       are. I flatter you with hair and makeup styling, a wardrobe that
       compliments your figure, and amazing lighting and posing techniques to
       highlight your best ass-sets. See what I did there.</p>
    <p class="jhp-p">I do not believe in heavy photoshopping. Do not get me
       wrong &mdash; I retouch all of your images and will gladly remove your
       bruises and pimples &mdash; but I do not want to over-manipulate your
       body to make you look like someone you are not. We already live in a
       time when we are consumed with unrealistic bodies in the media. I want
       to show you that you are beautiful at this very moment, without over
       the top retouching.</p>

    <h2 class="jhp-h q" id="portfolio">I Don&rsquo;t Look Like the Women in
       Your Portfolio</h2>
    <p class="jhp-p">Actually, you do. You just have not had the chance to see
       yourself from my perspective yet. Come into the studio and let me show
       you how beautiful you really are.</p>
    <p class="jhp-p">There is no such thing as the perfect body. Boudoir is for
       every body. You are never too big, too small, too old or too young to do
       a boudoir session &mdash; though I only photograph clients over the age
       of 18.</p>

    <h2 class="jhp-h q" id="who">Who Is Going to Be There?</h2>
    <p class="jhp-p">You and me. Your hair and makeup artist leaves once the
       service is finished.</p>
    <p class="jhp-p">I have a full female staff, and the studio is designed
       with private rooms for each portion of your day.</p>

    <h2 class="jhp-h q" id="retouch">What About Retouching?</h2>
    <p class="jhp-p">I am happy to retouch your images. I always remove pimples,
       bruises, scratches and under eye circles. I also offer retouching on
       cellulite, scars, small tattoos and stretch marks, if you choose to have
       them removed.</p>
    <p class="jhp-p">Honestly, most of my clients are wowed at how amazing
       their images look straight out of camera and opt for less retouching
       than they thought they needed. It is a very personal decision and one I
       leave up to you once you have seen your images.</p>
    <p class="jhp-p">I do not remove tan lines or correct skin tone from tanning
       beds or spray tans, so proceed with caution. I do have editing
       techniques to keep you from looking pasty, if that is a concern.</p>
  </div>

  {plate2}

  <div class="jhp-gd">
    <h2 class="jhp-h q" id="wear">What Will I Wear?</h2>
    <p class="jhp-p">I have a beautiful and comprehensive wardrobe guide that
       gives you the full picture on how to look and feel like a bombshell for
       your session. My policy is always: when in doubt, bring it.</p>
    <p class="jhp-p">You are welcome to make a Pinterest board and share it
       with me so I can help make your dream shoot a reality. And there is a
       client wardrobe of over {wardrobe} pieces, sizes XS to 4X, that you are
       more than welcome to borrow from and browse through.</p>

    <h2 class="jhp-h q" id="talk">Do I Get to Talk to You First?</h2>
    <p class="jhp-p">Most of my clients book their session over the phone,
       which is kind of like our first date. We will have one {consult} phone
       consultation, so we can make sure you are ready and answer any
       questions you have.</p>
    <p class="jhp-p">I am here for you every step of the way. Email is how I
       communicate most effectively with clients, so write to me any time at
       <a href="mailto:jessica@jhpboudoir.com">jessica@jhpboudoir.com</a>.
       Emails are typically returned within two to three business days.</p>
    <div class="jhp-rules">
      <p>Please, no props, no spray tans, and absolutely no weapons in the
         studio at any time.</p>
      <p>I also do not allow anyone under the age of 18 in the boudoir studio,
         ever.</p>
    </div>

    <h2 class="jhp-h q" id="types">What Types of Sessions Do You Offer?</h2>
    <p class="jhp-p">Yes, there are different types of boudoir session you can
       book, and I am always changing it up. Right now I am offering these:</p>
    <div class="jhp-two">
      <div>
        <p class="when">Year round &middot; most popular</p>
        <h3>Traditional Studio Sessions</h3>
        <p>In the studio, all year. Great for a first timer.</p>
      </div>
      <div>
        <p class="when">Summer dates only</p>
        <h3>Outdoor Boudoir Sessions</h3>
        <p>Exclusive locations, on summer dates only.</p>
      </div>
    </div>
    <p class="jhp-p" style="margin-top:20px">Have something else in mind? Ask
       me. I am always up for a new adventure.</p>
  </div>

  {plate3}

  <div class="jhp-gd">
    <h2 class="jhp-h q" id="day">How the Session Day Works</h2>
    <p class="jhp-p">Your session day runs {day} from start to finish. You get
       complimentary hair and makeup, access to the {wardrobe}-piece client
       wardrobe, and I pose you from head to pointed toe and help you with a
       whole range of facial expressions.</p>
    <p class="jhp-p">Be prepared to be sore afterwards. We do a lot of bending
       and twisting &mdash; it is quite the workout.</p>
    <ol class="jhp-day">
      <li>
        <h3>Hair and Makeup</h3>
        <p>Professional hair and makeup first, so you arrive in front of the
           camera already finished. Your artist leaves once it is done.</p>
      </li>
      <li>
        <h3>Wardrobe</h3>
        <p>We go through what you brought and what you want to borrow, and pick
           the order we will shoot it in.</p>
      </li>
      <li>
        <h3>Your Session</h3>
        <p>The studio is private and it is just the two of us. I direct
           everything &mdash; you do not need to know how to pose, and you will
           not be left standing there wondering what to do with your hands.</p>
      </li>
      <li>
        <h3>And That Is the Day</h3>
        <p>Sessions run inside studio hours, {studio_hours}. Your reveal is a
           separate appointment, so you go home when we are done rather than
           making decisions about pictures you have not seen yet.</p>
      </li>
    </ol>

    <h2 class="jhp-h q" id="reveal">Your Image Reveal</h2>
    <p class="jhp-p">Your reveal is {reveal_wait} after your session. It is a
       private appointment over Zoom, and it is where you see your images for
       the very first time &mdash; together, with me, going through them one by
       one.</p>
    <p class="jhp-p">You will be shown {shown} images. You choose which ones
       you want to keep and how you want them, and you order them at that same
       appointment.</p>
    <p class="jhp-p">You are not sent a link and left to work it out alone.
       That is the part most women tell me afterwards was their favourite of
       the whole thing.</p>

    <h2 class="jhp-h q" id="delivery">When the Albums and Prints Arrive</h2>
    <p class="jhp-p">Your digital images are yours the moment the reveal ends.
       Albums, wall art and anything else printed are made to order and arrive
       at your door {delivery} of that appointment. I usually drop ship
       everything directly to you to keep the process as simple as
       possible.</p>
  </div>

  {plate4}

  <div class="jhp-gd">
    <h2 class="jhp-h q" id="book">What Do I Need to Do to Book?</h2>
    <p class="jhp-p">The session fee reserves your date on my calendar. Your
       images are purchased separately from it, at your reveal and ordering
       appointment, and the full investment menu comes to you once the session
       fee is paid.</p>
    <div class="jhp-card">
      <p class="lb">Session Fee</p>
      <p class="fig">{fee}<span class="u">to reserve your date</span></p>
      <p>It can be paid in full, or split into two payments &mdash; the first
         to reserve the date on the calendar, the second within 14 days of it.
         If the second payment is not made within those 14 days, the date and
         the first payment are forfeited.</p>
    </div>
    <p class="jhp-p" style="margin-top:26px">What the session fee includes:</p>
    <ul class="jhp-inc">
      <li>Your {consult} pre-session consultation</li>
      <li>Private use of the boudoir studio</li>
      <li>Professional hair and makeup application</li>
      <li>Access to the {wardrobe}-piece client wardrobe</li>
      <li>60 minutes of photography</li>
      <li>Complete posing and expression coaching</li>
      <li>Your private reveal and ordering appointment over Zoom</li>
    </ul>

    <h2 class="jhp-h q" id="guests">Can Someone Come With Me?</h2>
    <p class="jhp-p">No &mdash; I do not allow guests for any portion of the
       time you spend with us, including the ordering appointment. What I do is
       delivered best one to one, with your complete undivided attention.</p>

    <h2 class="jhp-h q" id="when">I Need My Images By a Certain Date</h2>
    <p class="jhp-p">The studio books up to {booking_window} in advance, and
       printed products take up to six weeks after your reveal. So reach out
       well before the date you need them.</p>
    <p class="jhp-p">If you have a special occasion coming up, or you want a
       holiday appointment, I recommend booking a <strong>year</strong> ahead
       of that date. Those dates go first.</p>

    <h2 class="jhp-h q" id="spend">What Can I Expect to Spend?</h2>
    <p class="jhp-p">Before I have photographed you it is hard to give you an
       exact figure. Some women want a basic album; others invest several
       thousand in a Collection with a variety of products. What you spend is
       up to you. You can buy from my Collections or a la carte, and the full
       investment menu comes to you as soon as your booking is complete.</p>
    <p class="jhp-p">That said &mdash; if you are looking for a quick shoot, or
       just a few images, this is not the session for you. I offer a full
       experience and I show you {shown} images. I only offer luxury products,
       because you are worth it. Investing in yourself is priceless. You will
       never tire of your images, or forget the way the session day made you
       feel.</p>

    <h2 class="jhp-h q" id="money">The Collections</h2>
    <p class="jhp-p">There are {collections} Collections in all, so there is
       room to find the one that fits.</p>
    <div class="jhp-card two">
      <div>
        <p class="lb">Petite Collections</p>
        <p class="fig">from {petite}</p>
        <p>Three digital images.</p>
      </div>
      <div>
        <p class="lb">Full Collections</p>
        <p class="fig">from {full}</p>
        <p>An album, your digitals and a mobile app.</p>
      </div>
    </div>
    <p class="jhp-p" style="margin-top:26px">Sticker shock? I get it. I had it
       too, the first time I booked a professional boudoir session with my own
       dream photographer. And you know what &mdash; I would have paid her
       double by the time it was done.</p>
    <p class="jhp-p">I know this is an investment, which is why every Collection
       is chosen when you book and paid for on an interest-free in-house
       payment plan before your session. Weekly, biweekly or monthly &mdash;
       whichever suits you, spread over the months between booking and your
       session day. It is the same figure either way, and we set it up on
       auto-pay so you never have to think about a late fee.</p>
  </div>

  {plate5}

  <div class="jhp-gd jhp-end">
    <h2 class="jhp-h q" id="ready">Ready to Book?</h2>
    <p class="jhp-p">If you have made it this far and you are ready to take the
       next step, book your consultation call below. If you would rather ask
       something first, reply to the email this guide came with and tell me you
       would like to chat before taking the leap.</p>
    <p class="jhp-p">I truly hope you have enjoyed reading this, and that it
       has left you excited about the thought of having your own session. Ask
       me anything at all &mdash; I want you to be completely comfortable, and
       completely empowered, during your session.</p>
    <p class="jhp-p" data-greet="{{name}}, I cannot wait to chat with you soon.">I
       cannot wait to chat with you soon.</p>
    <p class="jhp-sig">Jess</p>
  </div>
</section>

{script}

<div class="jhp-div" aria-hidden="true"></div>

<a class="jhp-band" href="{calendar}" target="_blank" rel="noopener">
  <img src="{cdn}78e3da43-f19a-4c5b-a450-c76cd27ad02f.jpg"
       width="1600" height="1064" loading="lazy"
       alt="A black and white portrait from a studio session at JHP Boudoir">
  <span class="over">
    <span class="jhp-kicker">The next step</span>
    <h2 class="jhp-h jhp-h-lg">Book Your Consultation Call</h2>
    <span class="sub">Twenty minutes, and nothing is committed to.</span>
    <span class="jhp-btn">Schedule My Call</span>
  </span>
</a>
"""

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Session Guide | Jefferson City, MO | JHP Boudoir</title>
<meta name="description" content="Everything a boudoir session at JHP Boudoir involves: the studio, the day, the reveal, what it costs and how to book. Just outside Jefferson City, Missouri.">
<meta name="robots" content="noindex, nofollow">
<link rel="canonical" href="https://pages.scalogy.com/jhpboudoir1/session-guide/">
<meta name="theme-color" content="#13100E">
<meta property="og:site_name" content="JHP Boudoir">
<meta property="og:locale" content="en_US">
<meta property="og:title" content="The Session Guide | JHP Boudoir">
<meta property="og:description" content="The studio, the day, the reveal, what it costs and how to book.">
<meta property="og:url" content="https://pages.scalogy.com/jhpboudoir1/session-guide/">
<meta property="og:image" content="__CDN__%s">
<meta property="og:image:alt" content="A client photographed in the window light at the JHP Boudoir studio">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="The Session Guide | JHP Boudoir">
<meta name="twitter:description" content="The studio, the day, the reveal, what it costs and how to book.">
<meta name="twitter:image" content="__CDN__%s">
<meta property="og:type" content="article">
<style>html,body{margin:0;padding:0;background:#13100E}body{overflow-x:hidden}</style>
</head>
<body>
{%% raw %%}
<div class="jhp-home">
<style>
""" % (HERO, HERO)

toc_html = "".join(
    '\n      <li><a href="#%s">%s</a></li>' % (i, t) for i, t in TOC) + "\n    "

body = BODY.format(
    cdn=CDN, hero=HERO, vip=VIP, calendar=CALENDAR, toc=toc_html,
    script=SCRIPT,
    plate1=plate("f9de4c0c-ba8e-48bb-b559-a9a11beac76c.jpg",
                 "The window light in the JHP Boudoir studio, from a client session",
                 "The studio, on an ordinary afternoon."),
    plate2=plate("678293dc-8167-4463-a41b-8a20bfaee783.jpg",
                 "A black and white portrait from a studio session at JHP Boudoir",
                 "Posed from head to pointed toe &mdash; you will not have to work it out."),
    plate3=plate("1d6d5e7e-7f3d-490b-9883-371ecaa5f1d0.jpg",
                 "A client photographed at the JHP Boudoir studio",
                 "Every body. Every age. Every size."),
    plate4=plate("538477d1-c964-4c26-babe-89e797786880.jpg",
                 "A black and white portrait from a studio session at JHP Boudoir",
                 "Your images, seen together for the first time at your reveal."),
    plate5=plate("958c1b0e-53b1-4d18-b5ed-7b4b2ae1ccc5.jpg",
                 "A black and white portrait from a studio session at JHP Boudoir",
                 "This is the part I cannot wait for."),
    **F)

out = (HEAD.replace("__CDN__", CDN)
       + shared[shared.index("/* SHARED DESIGN SYSTEM"):]
       + parts + GUIDE_CSS + "</style>\n" + nav + body + "\n" + foot)

# ------------------------------------------------------------------- the checks
# Loud rather than silent: every one of these has a way of going wrong quietly.
stale = {
    "$500": "the old session fee", "$2,800": "the old Collection floor",
    "$2800": "the old Collection floor", "18 months": "the old booking window",
    "4-5 hours": "the old session length", "9am-4pm": "the old studio hours",
    "6-8 weeks": "the old delivery window", "30 minute": "the wrong consult",
    "30 Minute": "the wrong consult", "in-person reveal": "the reveal is Zoom",
    "located in Jefferson City": "it is just outside",
    "$1500": "unconfirmed album pricing", "$3500": "unconfirmed album pricing",
}
for s, why in stale.items():
    if s in out:
        raise SystemExit("REFUSING TO BUILD: %r is still in the guide (%s)" % (s, why))

for i, t in TOC:
    if 'id="%s"' % i not in out:
        raise SystemExit("contents points at #%s and nothing has that id" % i)

assert out.count("{% raw %}") == 1 and out.count("{% endraw %}") == 1, "fence"
assert out.count("<h1") == 1, "one h1"
for f in (HERO, "78e3da43-f19a-4c5b-a450-c76cd27ad02f.jpg"):
    assert out.count(f) >= 1
# One frame per client, no repeats. Counted off the <img> tags only -- the
# hero frame is legitimately named three more times, in og:image,
# twitter:image and the canonical share card.
import re as _re
photos = _re.findall(r'<img[^>]+media/([0-9a-f-]+\.jpg)', out)
dupes = [f for f in set(photos) if photos.count(f) > 1]
assert not dupes, "a frame is drawn twice: %s" % dupes

(ROOT / "scalogy-guide.html").write_text(out)
print("wrote %d bytes, %d questions, %d photographs, %d contents rows"
      % (len(out.encode()), out.count('class="jhp-h q"'), len(photos), len(TOC)))

# ---------------------------------------------------------------------- the PDF
# --pdf drives headless Chromium over the built file and writes
# jhp-session-guide.pdf beside it, for the times she wants a file to attach
# rather than a link to send. The page is the source either way.
if "--pdf" in sys.argv:
    import subprocess, json, tempfile
    flat = out.replace("{% raw %}", "").replace("{% endraw %}", "")

    # THE PHOTOGRAPHS HAVE TO BE LOCAL FOR THIS STEP, and that is an
    # environment problem rather than a page one. Every <img> on this page
    # points at Jessica's GHL media library, which is exactly right for the
    # page -- that is where her photographs live and where the rest of the
    # site loads them from. It is the build sandbox that cannot reach
    # assets.cdn.filesafe.space, so a PDF rendered against the live URLs
    # comes out with seven empty frames and nobody notices until it is in
    # somebody's inbox.
    #
    # So --pdf requires a directory of the same files fetched some other way
    # (Scalogy's own egress proxy will serve them) and swaps the URLs for
    # file paths just for the render. The page itself is never rewritten.
    cache = pathlib.Path(os.environ.get("JHP_IMG_CACHE", ""))
    if not cache.is_dir():
        raise SystemExit(
            "--pdf needs JHP_IMG_CACHE=<dir> holding the guide's photographs.\n"
            "Without it the PDF renders with empty frames. Fetch each file in\n"
            "the media library through an egress route that can reach the CDN.")
    # Only the photographs. The footer wordmark is hidden by the print rules
    # above, so a missing PNG is not a reason to refuse to build the file.
    missing = [f for f in re.findall(r'media/([0-9a-f-]+\.jpg)', flat)
               if not (cache / f).exists()]
    if missing:
        raise SystemExit("--pdf is missing %d file(s) from the cache: %s"
                         % (len(missing), ", ".join(sorted(set(missing)))))
    # A Letter page is about 180mm of content, which at 150dpi is roughly
    # 1,060 pixels -- so the 1600px originals put about 21MB into a file that
    # has to survive an email. Downscaled to 1,200px at quality 82 it is a
    # few MB and no reader can tell the difference on paper or on a screen.
    # The originals are untouched; this is a copy made for the render.
    small = pathlib.Path(tempfile.mkdtemp())
    try:
        from PIL import Image
        for f in sorted(set(re.findall(r'media/([0-9a-f-]+\.jpg)', flat))):
            im = Image.open(cache / f)
            im.load()
            if im.width > 1200:
                im = im.resize((1200, round(im.height * 1200 / im.width)),
                               Image.LANCZOS)
            im.convert("RGB").save(small / f, "JPEG", quality=82,
                                   optimize=True, progressive=True)
        cache = small
    except ImportError:
        print("  (no Pillow: printing the full-size frames, expect a big file)")
    flat = flat.replace(CDN, "file://%s/" % cache)
    # loading="lazy" is right for the page and wrong for this. A print render
    # never scrolls, so a lazy frame below the first screen is simply never
    # fetched and lands in the PDF as blank space -- which is how the first
    # build of this file came out with three photographs instead of seven.
    flat = flat.replace(' loading="lazy"', "")

    tmp = pathlib.Path(tempfile.mkdtemp()) / "guide.html"
    tmp.write_text(flat)
    script = '''
    import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
    const b = await chromium.launch({ args: ['--allow-file-access-from-files'] });
    const p = await b.newPage({ viewport: { width: 900, height: 1200 } });
    await p.goto('file://%s', { waitUntil: 'networkidle' });
    // Belt and braces: decode() resolves only once the bytes are actually
    // there, so this cannot print ahead of the photographs.
    await p.evaluate(() => Promise.all(
      [...document.images].map(i => i.decode().catch(() => null))));
    await p.emulateMedia({ media: 'print' });
    await p.pdf({ path: '%s', format: 'Letter', printBackground: true,
                  margin: { top: '14mm', bottom: '14mm', left: '16mm', right: '16mm' } });
    await b.close();
    ''' % (tmp, ROOT / "jhp-session-guide.pdf")
    js = tmp.parent / "pdf.mjs"
    js.write_text(script)
    subprocess.run(["node", str(js)], check=True)
    n = (ROOT / "jhp-session-guide.pdf").stat().st_size
    print("wrote jhp-session-guide.pdf, %d bytes" % n)
