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
  Collections    from $2,800 -> Digital from $1,250, Full from $3,400, eight
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
    "digital":        "$1,250",
    "full":           "$3,400",
    "collections":    "eight",
    "day":            "two to three hours",
    "reveal_wait":    "7&ndash;14 business days",
    "delivery":       "within 6 weeks",
    "booking_window": "15 months",
    "studio_hours":   "Monday to Thursday, 10am&ndash;3pm",
    # The days she is BEHIND THE CAMERA, which is narrower than the studio
    # hours above: the studio is open Monday to Thursday for consultations and
    # reveals, and she photographs on two of those days. Her own, 25 September.
    # ASK: this says 9am and the settled studio hours say 10am. One of the two
    # is wrong and it is hers to settle -- see CLAUDE.md.
    "shoot_days":     "Tuesdays and Thursdays, 9am&ndash;3pm",
    "call_hours":     "Monday to Friday, 8am&ndash;5pm",
    "consult":        "20 minute",
    "wardrobe":       "160",
    "sqft":           "2,000",
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
  .jhp-home .jhp-two,.jhp-home .jhp-rules,.jhp-home .jhp-end{max-width:none}
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
  .jhp-home .jhp-nav,
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


# The second half of the guide's CSS: what the 24 September restructure added.
# Jessica asked for the questions in two columns, for more formatting, and for
# the whole thing to be more beautiful. All three are one problem -- a 14,500px
# column of undifferentiated prose is not a magazine, it is a scroll.
GUIDE_CSS += """
/* FOUR PARTS, AND WHY THE DOCUMENT HAS THEM NOW
   ---------------------------------------------
   Twenty questions in a row is a list. The same twenty grouped into four
   parts is a document with a shape, and the shape is what tells a woman how
   far in she is and what kind of answer to expect next: who I am, what you
   are worried about, how it works, what it costs.

   The grouping is also what makes two columns legible. Balanced columns read
   down the left and then down the right, which is only acceptable when each
   item is self-contained and the run between headings is short. Four short
   runs, not one of twenty. */
/* THE PART IS THE CONTROL, AND THE WHOLE PART OPENS AT ONCE
   --------------------------------------------------------
   Jessica's ask, 25 September, and it replaces the previous two. She had the
   questions opening one at a time and did not like the layout: "is it possible
   to have the header, they click it, and then all of the follow-up questions
   underneath are shown instead of having to click each time?"

   So there are FOUR controls on this page and not nineteen. Each part is a
   <details> whose summary is the part heading, and opening it reveals that
   whole part -- every question, every answer, and the photograph that closes
   it -- as continuous prose. She taps once and then reads.

   That means the questions themselves are no longer controls: they are plain
   <article> headings again, which is why the card, the chevron and the
   summary's tap padding are all gone from .jhp-q below. A heading that does
   nothing when it is clicked must not look like a button.

   Closed, the top of the guide is four rows. */
.jhp-home .jhp-pt{max-width:1080px;margin:0 auto}
/* A hairline between rows rather than a box round each: closed, the four read
   as one list, which is what they are. */
.jhp-home .jhp-pt + .jhp-pt{border-top:1px solid var(--line-soft)}
.jhp-home .jhp-pt > summary{display:block;cursor:pointer;list-style:none;
  -webkit-tap-highlight-color:transparent;
  padding:clamp(30px,3.6vw,46px) 0 clamp(26px,3vw,40px)}
.jhp-home .jhp-pt > summary::-webkit-details-marker{display:none}
.jhp-home .jhp-pt > summary:focus-visible{outline:2px solid var(--gold-bright);
  outline-offset:2px}
/* The whole row is the target, so nothing here needs its own 44px: the
   summary is 100+px tall at every width. */
.jhp-home .jhp-part{max-width:1080px;text-align:center;margin:0 auto}
.jhp-home .jhp-part .no{font-family:var(--sans);font-weight:400;font-size:10px;
  letter-spacing:.42em;text-transform:uppercase;color:var(--gold);margin:0 0 14px}
.jhp-home .jhp-part h2{font-family:var(--serif);font-weight:600;
  font-size:clamp(27px,3.1vw,40px);line-height:1.14;color:var(--ink);margin:0;
  text-wrap:balance;transition:color .3s}
.jhp-home .jhp-pt > summary:hover h2{color:var(--gold-bright)}
/* A short rule rather than a full-width one: it closes the heading off
   without drawing a line across the page every time a part begins. */
.jhp-home .jhp-part .rule{width:34px;height:1px;background:var(--gold);
  margin:18px auto 0;opacity:.8}
/* The count tells her the size of what she is about to open -- five questions
   in The Investment is worth knowing before she taps it -- and it carries the
   same 6px chevron the Info menu, the phone drawer and the FAQ wear, so the
   row reads as a disclosure and not as a heading that happens to be centred. */
.jhp-home .jhp-part .ct{display:inline-flex;align-items:center;gap:11px;
  font-family:var(--sans);font-weight:400;font-size:10px;letter-spacing:.24em;
  text-transform:uppercase;color:var(--dim);margin:16px 0 0;
  transition:color .3s}
.jhp-home .jhp-part .ct::after{content:"";width:6px;height:6px;margin-top:-4px;
  border-right:1px solid currentColor;border-bottom:1px solid currentColor;
  transform:rotate(45deg);transition:transform .3s}
.jhp-home .jhp-pt > summary:hover .ct{color:var(--gold)}
.jhp-home .jhp-pt[open] .ct{color:var(--gold)}
.jhp-home .jhp-pt[open] .ct::after{transform:rotate(-135deg);margin-top:3px}

/* ONE COLUMN, AND A QUESTION IS JUST A HEADING AGAIN
   -------------------------------------------------
   The whole part opens at once, so nothing inside it is a control. Each
   question is a heading and its prose, separated from the next by a hairline
   -- a magazine, read straight down, which is what it was always meant to be.

   TWO COLUMNS ARE STILL NOT BACK, and the reason has changed. They were
   dropped because a one-at-a-time reveal only reads down a single column;
   now the reveal is per part, so that argument is spent. What replaces it is
   plainer: this is nineteen answers of continuous prose and a balanced
   two-column run of it would have her reading down the left of a part and
   then back up to the top of the right, with photographs spanning across.
   One column at an honest measure is the right shape for prose. Set
   .jhp-qs back to columns:2 to try it; measure Part Two before believing it.

   860px, because a single column of 15px type at 1080 is a 140-character
   line. */
.jhp-home .jhp-qs{max-width:860px;margin:0 auto}
.jhp-home .jhp-qs > * + *{margin-top:clamp(26px,2.8vw,34px)}

.jhp-home .jhp-q{border-top:1px solid var(--line-soft);
  padding-top:clamp(22px,2.4vw,28px)}
.jhp-home .jhp-q:first-child{border-top:0;padding-top:0}
.jhp-home .jhp-q h3{font-family:var(--serif);font-weight:600;
  font-size:clamp(19px,1.9vw,24px);line-height:1.22;color:var(--ink);
  margin:0 0 14px;text-wrap:balance}
.jhp-home .jhp-q p{font-family:var(--sans);font-weight:300;font-size:15.5px;
  line-height:1.75;color:var(--muted);margin:0 0 13px}
.jhp-home .jhp-q p:last-child{margin-bottom:0}
.jhp-home .jhp-q em{font-style:italic;color:var(--ink)}
.jhp-home .jhp-q strong{font-weight:500;color:var(--ink)}
.jhp-home .jhp-q a{color:var(--gold);border-bottom:1px solid var(--line);
  transition:color .3s,border-color .3s}
.jhp-home .jhp-q a:hover{color:var(--gold-bright);border-color:var(--gold-bright)}
/* .jhp-wide used to mean "span both columns". There is one column now, so it
   only marks the questions that carry a panel and needs no layout of its own.
   It is what the columns would key off if they ever came back. */
.jhp-home .jhp-wide{margin-top:14px}

/* THE LIFTED LINE
   ---------------
   A sentence of hers, set large between two parts. This is NOT the review
   pull-quote object -- that one is .qt/.qr and belongs to somebody else's
   words, with rules in CLAUDE.md about where a review may appear. This is
   Jessica quoting herself, which is what a magazine does with its own copy.

   The line is repeated verbatim from the body a few hundred pixels above.
   That is the point of a lifted line and not an accident: it gives the eye
   somewhere to rest between two dense runs, and it puts the sentence she most
   wants remembered in the largest type on the page. Whole sentences only --
   nothing is trimmed to make it fit. */
.jhp-home .jhp-lift{max-width:900px;margin:clamp(50px,6.4vw,84px) auto;
  padding:0 clamp(18px,4vw,40px);text-align:center}
.jhp-home .jhp-lift::before{content:"";display:block;width:7px;height:7px;
  margin:0 auto clamp(20px,2.4vw,30px);transform:rotate(45deg);
  border:1px solid var(--gold)}
.jhp-home .jhp-lift p{font-family:var(--serif);font-style:italic;font-weight:400;
  font-size:clamp(23px,3.1vw,38px);line-height:1.3;color:var(--ink);margin:0;
  text-wrap:balance}
.jhp-home .jhp-lift .gl{color:var(--gold)}

/* The opening paragraph takes a drop cap, which is the one place on this site
   that does. It is the first thing under the title and it marks where the
   reading starts -- and the guide is the only document here long enough for
   that to mean anything. Not on the greeting line above it: that line is one
   sentence and is rewritten by the name script, and a capital the size of
   three lines over a paragraph one line deep looks like a mistake. */
.jhp-home .jhp-gd .opener::first-letter{float:left;font-family:var(--serif);
  font-weight:600;font-size:60px;line-height:.82;color:var(--gold);
  padding:6px 13px 0 0}
@media (max-width:620px){
  .jhp-home .jhp-gd .opener::first-letter{font-size:48px;padding:4px 10px 0 0}
}

/* The close gets the full width and sits on its own, because the last thing
   in a long document should not look like the twenty-first question. */
.jhp-home .jhp-end{max-width:62ch}
.jhp-home .jhp-end .jhp-h{margin-bottom:18px}
"""

# The contents list is grouped now, and the panels inside a question card sit
# a heading level lower than they did, so both need their own rules.
GUIDE_CSS += """
/* A question is an h3 now, so the headings inside the day and the session
   types dropped to h4. Same type, one level down the document. */
.jhp-home .jhp-day h4{font-family:var(--sans);font-weight:500;font-size:13px;
  letter-spacing:.14em;text-transform:uppercase;color:var(--ink);margin:0 0 7px}
.jhp-home .jhp-two h4{font-family:var(--serif);font-weight:600;font-size:23px;
  line-height:1.2;color:var(--ink);margin:0 0 6px}
/* The panels sit in the question's own column rather than in the 62ch prose
   measure, so they lose the auto margins that used to centre them. */
.jhp-home .jhp-q .jhp-card,.jhp-home .jhp-q .jhp-day,
.jhp-home .jhp-q .jhp-two,.jhp-home .jhp-q .jhp-rules{max-width:none}
.jhp-home .jhp-q .jhp-card{margin-inline:0}
.jhp-home .jhp-q .jhp-p{font-size:15.5px;line-height:1.75;margin:0 0 13px}

/* ON A PHONE the four rows tighten and the type steps down one notch. There
   is no box to take off any more -- the questions have been hairlines and
   prose at every width since the part became the control. */
@media (max-width:620px){
  .jhp-home .jhp-qs{max-width:none}
  .jhp-home .jhp-q h3{font-size:19px}
  .jhp-home .jhp-pt > summary{padding:26px 0 22px}
  .jhp-home .jhp-lift{margin:38px auto}
}
"""

# The print overrides have to come LAST in the sheet, not in the block above.
# A media query adds no specificity, so an @media print rule that appears
# before an equally specific normal rule loses to it while printing -- which
# would have left the PDF trying to lay out two columns with spanners in them,
# something print engines handle badly and inconsistently.
GUIDE_CSS += """
@media print{
  /* ALL FOUR PARTS ARE OPEN ON PAPER. A part is a <details> and a closed one
     prints as its summary alone -- the first render after the questions became
     disclosures came out nine pages of headings with not a word of copy under
     any of them, and the file looked fine from the outside. Paper does not tap.

     Both hiding mechanisms have to be undone, the same pair the phone nav
     spells out: older engines hide a closed <details>'s children with a
     display rule, which a child can override, and newer ones hide
     ::details-content with content-visibility, which a child cannot. Setting
     one and not the other leaves half the engines printing headings. This does
     not depend on any script having run, which is the point -- a stylesheet
     must not wait on an event. */
  .jhp-home .jhp-pt > .jhp-qs,.jhp-home .jhp-pt > figure,
  .jhp-home .jhp-pt > .jhp-lift{display:block !important}
  .jhp-home .jhp-pt::details-content{content-visibility:visible !important;
    display:block !important;block-size:auto !important}
  /* A chevron and a question count are instructions to tap, and there is
     nothing to tap on paper. */
  .jhp-home .jhp-part .ct{display:none}
  /* A part heading starts a page rather than orphaning itself at the foot of
     the last one. Not the first, which would leave a blank sheet in front of
     Part One. */
  .jhp-home .jhp-pt + .jhp-pt{break-before:page;page-break-before:always;
    border-top:0}
  .jhp-home .jhp-pt > summary{padding:0 0 26px}
  /* One column on paper. Two columns of 15px type in a Letter page is a
     newspaper, and the spanners that make the screen layout work have no
     reliable print behaviour across engines. */
  .jhp-home .jhp-qs{columns:1;max-width:none}
  .jhp-home .jhp-wide{column-span:none}
  .jhp-home .jhp-q,.jhp-home .jhp-part,.jhp-home .jhp-lift{
    break-inside:avoid;page-break-inside:avoid}
  .jhp-home .jhp-part{break-after:avoid;page-break-after:avoid}
  .jhp-home .jhp-q{background:none;border:0;border-top:1px solid var(--line-soft);
    border-radius:0;padding:14px 0 0}
  .jhp-home .jhp-lift{margin:30px auto}
}
"""

# ------------------------------------------------------------------ the copy
# Her guide, in her order, grouped into four parts. The voice is hers
# throughout -- where a sentence reads oddly formal or oddly blunt, that is
# because it is a transcription and not a rewrite.
#
# WHY THIS IS DATA AND NOT MARKUP. The contents list, the anchors and the
# headings all have to agree, and when they were three separate blocks of HTML
# they were three chances to disagree. One structure generates all three, and
# the build fails if an anchor has no id.
#
# The photographs are eight different women, one frame each, which is the
# house rule: the same face opening and closing a document reads as the only
# woman who has ever been there. Alt text says what is honestly known about
# each frame -- studio, and colour or black and white -- rather than the one
# string the 165 gallery frames share. It would be better still if Jessica
# described them; that is a note in CLAUDE.md, not a thing to invent here.
HERO = "fe2033e0-3571-441e-8c98-089358e06f10.jpg"


def plate(f, alt, cap, wide=True):
    """A photograph that breaks the column."""
    return ('<figure class="jhp-plate%s">\n'
            '  <img src="%s%s" loading="lazy" alt="%s">\n'
            '  <figcaption>%s</figcaption>\n'
            '</figure>' % (" jhp-wide" if wide else "", CDN, f, alt, cap))


def lift(html):
    """One of her own sentences, set large between two parts."""
    return '<div class="jhp-lift">\n  <p>%s</p>\n</div>' % html


def q(qid, question, answer, wide=False):
    return {"id": qid, "q": question, "a": answer, "wide": wide}


# The two panels that are too wide for a column, written once here and dropped
# into their questions below.
DAY = """
    <ol class="jhp-day">
      <li>
        <h4>Hair and Makeup</h4>
        <p>Professional hair and makeup first, so you arrive in front of the
           camera already finished. Your artist leaves once it is done.</p>
      </li>
      <li>
        <h4>Wardrobe</h4>
        <p>We go through what you brought and what you want to borrow, and pick
           the order we will shoot it in.</p>
      </li>
      <li>
        <h4>Your Session</h4>
        <p>The studio is private and it is just the two of us. I direct
           everything &mdash; you do not need to know how to pose, and you will
           not be left standing there wondering what to do with your hands.</p>
      </li>
      <li>
        <h4>And That Is the Day</h4>
        <p>I photograph on {shoot_days}. Your reveal is a separate
           appointment, so you go home when we are done rather than making
           decisions about pictures you have not seen yet.</p>
      </li>
    </ol>"""

FEE = """
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
    </ul>"""

COLLECTIONS = """
    <p class="jhp-p">There are {collections} Collections in all, so there is
       room to find the one that fits.</p>
    <div class="jhp-card two">
      <div>
        <p class="lb">Digital Collections</p>
        <p class="fig">from {digital}</p>
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
       auto-pay so you never have to think about a late fee.</p>"""

TYPES = """
    <p class="jhp-p">Yes, there are different types of boudoir session you can
       book, and I am always changing it up. Right now I am offering these:</p>
    <div class="jhp-two">
      <div>
        <p class="when">Year round &middot; most popular</p>
        <h4>Traditional Studio Sessions</h4>
        <p>In the studio, all year. Great for a first timer.</p>
      </div>
      <div>
        <p class="when">Certain dates only</p>
        <h4>Specialty Sessions</h4>
        <p>Exclusive locations and sets, on certain dates only.</p>
      </div>
    </div>
    <p class="jhp-p" style="margin-top:20px">Have something else in mind? Ask
       me. I am always up for a new adventure.</p>"""

PARTS = [
 {"no": "Part One", "id": "begin", "title": "Before We Begin", "items": [
   q("about", "A Bit About Me", """
    <p>I am Jess. Wife to Zach, and I love the local weatherman with all my
       heart. Gin, tonic, lime.</p>
    <p>Seven years of college and three degrees later, I ended up running my
       own business full time. I would not trade the journey.</p>
    <p>I love changing lives through my art. Thank you for being here and for
       supporting my business &mdash; I cannot wait to meet you and make some
       of the most gorgeous photographs of yourself you will ever have.</p>"""),
   q("studio", "Where the Studio Is", """
    <p>The studio is just outside Jefferson City, Missouri. There is over
       {sqft} square feet of it: multiple set-ups, a hair and makeup room, a
       wardrobe room, and a sales area full of samples.</p>
    <p>It is full of gorgeous natural light, vintage exposed brick, wood beams
       and glass chandeliers. It is a comforting space, and it was built for
       boudoir photography.</p>"""),
   q("boudoir", "So, What Is Boudoir?", """
    <p>The French word <em>boudoir</em> means a woman&rsquo;s dressing room or
       bedroom, but I like to think of it as a fancy word for women&rsquo;s
       intimate portraiture. I want to make the most beautiful portraits of you
       that you will ever have.</p>
    <p>Boudoir is <strong>not</strong> pornographic or overly sexual. It can be
       fun, flirty, beautiful, cute, sexy, feminine, intimate, candid, posed
       &mdash; or really anything else you want it to be.</p>
    <p>If you have not already joined my private VIP group on Facebook, I
       highly suggest you do:
       <a href="{vip}" target="_blank" rel="noopener">the JHP Boudoir VIP
       group</a>.</p>"""),
   q("why", "What Would I Do With Boudoir Portraits?", """
    <p>I believe boudoir is the best gift you can give yourself &mdash; to
       capture your essence as you are right now. When you need a reminder of
       the strong, beautiful woman that you are, you will have a collection of
       amazing portraits to look at.</p>
    <p>I love it when women come to me for themselves. The images we make
       together will boost your self esteem and your confidence, and that
       should be celebrated by you. It will help you reclaim your femininity
       and your sexuality, two things that are often lost as we get consumed
       with our lives, our jobs, our families.</p>
    <p>Put that pep back in your step and reflect on the bodacious babe you
       are. Celebrate the body that you live in.</p>"""),
 ]},

 {"no": "Part Two", "id": "worries", "title": "The Things Women Worry About",
  "items": [
   q("thinner", "Can You Make Me Look Thinner?", """
    <p>I want to help you feel beautiful now, just the way you are. I flatter
       you with hair and makeup styling, a wardrobe that compliments your
       figure, and amazing lighting and posing techniques to highlight your
       best ass-sets. See what I did there.</p>
    <p>I do not believe in heavy photoshopping. Do not get me wrong &mdash; I
       retouch all of your images and will gladly remove your bruises and
       pimples &mdash; but I do not want to over-manipulate your body to make
       you look like someone you are not. We already live in a time when we are
       consumed with unrealistic bodies in the media. I want to show you that
       you are beautiful at this very moment, without over the top
       retouching.</p>"""),
   q("portfolio", "I Don&rsquo;t Look Like the Women in Your Portfolio", """
    <p>Actually, you do. You just have not had the chance to see yourself from
       my perspective yet. Come into the studio and let me show you how
       beautiful you really are.</p>
    <p>There is no such thing as the perfect body. Boudoir is for every body.
       You are never too big, too small, too old or too young to do a boudoir
       session &mdash; though I only photograph clients over the age of 18.</p>"""),
   q("who", "Who Is Going to Be There?", """
    <p>You and me. Your hair and makeup artist leaves once the service is
       finished.</p>
    <p>I have a full female staff, and the studio is designed with private
       rooms for each portion of your day.</p>"""),
   q("retouch", "What About Retouching?", """
    <p>I am happy to retouch your images. I always remove pimples, bruises,
       scratches and under eye circles. I also offer retouching on cellulite,
       scars, small tattoos and stretch marks, if you choose to have them
       removed.</p>
    <p>Honestly, most of my clients are wowed at how amazing their images look
       straight out of camera and opt for less retouching than they thought
       they needed. It is a very personal decision and one I leave up to you
       once you have seen your images.</p>
    <p>I do not remove tan lines or correct skin tone from tanning beds or
       spray tans, so proceed with caution. I do have editing techniques to
       keep you from looking pasty, if that is a concern.</p>"""),
   q("wear", "What Will I Wear?", """
    <p>I have a beautiful and comprehensive wardrobe guide that gives you the
       full picture on how to look and feel like a bombshell for your session.
       My policy is always: when in doubt, bring it.</p>
    <p>You are welcome to make a Pinterest board and share it with me so I can
       help make your dream shoot a reality. And there is a client wardrobe of
       over {wardrobe} pieces, sizes XS to 4X, that you are more than welcome
       to borrow from and browse through.</p>"""),
 ]},

 {"no": "Part Three", "id": "works", "title": "How It All Works", "items": [
   q("talk", "Do I Get to Talk to You First?", """
    <p>Most of my clients book their session over the phone, which is kind of
       like our first date. We will have one {consult} phone consultation, so
       we can make sure you are ready and answer any questions you have.</p>
    <p>I am here for you every step of the way. Email is how I communicate most
       effectively with clients, so write to me any time at
       <a href="mailto:jessica@jhpboudoir.com">jessica@jhpboudoir.com</a>.
       Emails are typically returned within two to three business days.</p>
    <div class="jhp-rules">
      <p>Please, no props, no spray tans, and absolutely no weapons in the
         studio at any time.</p>
      <p>I also do not allow anyone under the age of 18 in the boudoir studio,
         ever.</p>
    </div>"""),
   q("types", "What Types of Sessions Do You Offer?", TYPES, wide=True),
   q("day", "How the Session Day Works", """
    <p class="jhp-p">Your session day runs {day} from start to finish. You get
       complimentary hair and makeup, access to the {wardrobe}-piece client
       wardrobe, and I pose you from head to pointed toe and help you with a
       whole range of facial expressions.</p>
    <p class="jhp-p">Be prepared to be sore afterwards. We do a lot of bending
       and twisting &mdash; it is quite the workout.</p>""" + DAY, wide=True),
   q("reveal", "Your Image Reveal", """
    <p>Your reveal is {reveal_wait} after your session. It is a private
       appointment over Zoom, and it is where you see your images for the very
       first time &mdash; together, with me, going through them one by one.</p>
    <p>You will be shown plenty of images to choose from, well above what your
       Collection includes. You choose which ones you want to keep and how you
       want them, and you order them at that same appointment.</p>
    <p>You are not sent a link and left to work it out alone. That is the part
       most women tell me afterwards was their favourite of the whole
       thing.</p>"""),
   q("delivery", "When the Albums and Prints Arrive", """
    <p>Your digital images are yours the moment the reveal ends. Albums, wall
       art and anything else printed are made to order and arrive at your door
       {delivery} of that appointment. I drop ship everything directly
       to you to keep the process as simple as possible.</p>"""),
 ]},

 {"no": "Part Four", "id": "investment", "title": "The Investment", "items": [
   q("book", "What Do I Need to Do to Book?", """
    <p class="jhp-p">The session fee reserves your date on my calendar. Your
       images are purchased separately from it, at your reveal and ordering
       appointment, and the full investment menu comes to you once the session
       fee is paid.</p>""" + FEE, wide=True),
   q("guests", "Can Someone Come With Me?", """
    <p>No &mdash; I do not allow guests for any portion of the time you spend
       with us, including the ordering appointment. What I do is delivered best
       one to one, with your complete undivided attention.</p>"""),
   q("when", "I Need My Images By a Certain Date", """
    <p>The studio books up to {booking_window} in advance, and printed products
       take up to six weeks after your reveal. So reach out well before the
       date you need them.</p>
    <p>If you have a special occasion coming up, or you want a holiday
       appointment, I recommend booking a <strong>year</strong> ahead of that
       date. Those dates go first.</p>"""),
   q("spend", "What Can I Expect to Spend?", """
    <p>Before I have photographed you it is hard to give you an exact figure.
       Some women want a basic album; others invest several thousand in a
       Collection with a variety of products. What you spend is up to you. You
       can buy a full Collection &mdash; an album, your digital images, the
       mobile app and more &mdash; or you can buy digitals on their own. The
       full investment menu comes to you as soon as your booking is
       complete.</p>
    <p><strong>That said &mdash; if you are looking for a quick shoot, or just
       a few images, this is not the session for you.</strong> I offer a full
       experience, and how many images you are shown depends on the Collection
       you have chosen. I only offer luxury products, because you are worth it.
       Investing in yourself is priceless. You will never tire of your images,
       or forget the way the session day made you feel.</p>"""),
   q("money", "The Collections", COLLECTIONS, wide=True),
 ]},
]

# Where the photographs and the lifted lines fall, keyed to the part they
# follow. Each lifted line is a whole sentence of hers from the part above it.
AFTER = {
 "begin": plate("f9de4c0c-ba8e-48bb-b559-a9a11beac76c.jpg",
                "The window light in the JHP Boudoir studio, from a client session",
                "The studio, on an ordinary afternoon.")
          + "\n" + lift("Celebrate the body that you <span class=\"gl\">live in</span>."),
 "worries": plate("678293dc-8167-4463-a41b-8a20bfaee783.jpg",
                  "A black and white portrait from a studio session at JHP Boudoir",
                  "Posed from head to pointed toe &mdash; you will not have to work it out."),
 "works": plate("1d6d5e7e-7f3d-490b-9883-371ecaa5f1d0.jpg",
                "A client photographed at the JHP Boudoir studio",
                "Every body. Every age. Every size.")
          + "\n" + lift("There is no such thing as the perfect body. "
                        "Boudoir is for <span class=\"gl\">every body</span>."),
 "investment": plate("538477d1-c964-4c26-babe-89e797786880.jpg",
                     "A black and white portrait from a studio session at JHP Boudoir",
                     "Your images, seen together for the first time at your reveal."),
}

# One plate sits INSIDE Part Three rather than after it. That part is the
# longest and its two full-width panels -- the session types and the day --
# leave a run of column pairs either side; a photograph between them is what
# stops the middle of the document reading as a specification.
INSIDE = {"day": plate("958c1b0e-53b1-4d18-b5ed-7b4b2ae1ccc5.jpg",
                       "A black and white portrait from a studio session at JHP Boudoir",
                       "This is the part I cannot wait for.")}

# ---------------------------------------------------------------- the renderer
# Spelt out because a number in a heading has to read as words: "Four
# Questions", not "4 questions", in a document that is set in Cormorant.
COUNTS = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six",
          7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten"}


def render_parts():
    """Four disclosures, each holding one whole part.

    Jessica's ask, 25 September: the part heading is the control, and opening
    it shows every question underneath at once rather than asking her to click
    each one. So the <details> is the PART, and the questions inside it are
    plain articles -- headings and prose, read straight down.

    Everything that belongs to a part goes inside it, the closing photograph
    and the lifted line included. Left outside they would sit between the four
    closed rows, which is the wall the drop-downs exist to avoid.

    NOT MUTUALLY EXCLUSIVE, unlike the FAQ accordion. name="guide-part" would
    keep the page short, but a part collapsing while she is below it removes
    thousands of pixels from above the viewport and yanks the page under her
    thumb. She opens what she wants and it stays open."""
    out = []
    for part in PARTS:
        items = []
        for it in part["items"]:
            items.append(
                '  <article class="jhp-q%s" id="%s">\n'
                '    <h3>%s</h3>%s\n'
                '  </article>' % (" jhp-wide" if it["wide"] else "",
                                  it["id"], it["q"], it["a"]))
            if it["id"] in INSIDE:
                items.append("  " + INSIDE[it["id"]].replace("\n", "\n  "))
        # NOT re-indented to sit inside the <details>, deliberately. Adding two
        # spaces to every line of nineteen answers made every one of them a
        # changed line, which turned a 5KB template patch into a 37KB one for
        # whitespace no browser reads. The markup nests; the indentation does
        # not have to.
        inner = '<div class="jhp-qs">\n%s\n</div>' % "\n".join(items)
        if part["id"] in AFTER:
            inner += "\n" + AFTER[part["id"]]
        n = len(part["items"])
        out.append(
            '<details class="jhp-pt" id="%s">\n'
            '  <summary>\n'
            '    <div class="jhp-part">\n'
            '      <p class="no">%s</p>\n'
            '      <h2>%s</h2>\n'
            '      <div class="rule" aria-hidden="true"></div>\n'
            '      <p class="ct">%s Question%s</p>\n'
            '    </div>\n'
            '  </summary>\n'
            '%s\n'
            '</details>\n'
            % (part["id"], part["no"], part["title"],
               COUNTS[n], "" if n == 1 else "s", inner))
    return "\n".join(out)


# A DEEP LINK OPENS THE PART IT POINTS INTO.
# Added to SCRIPT so the page carries one script block and not two.
#
# This is the only script the reveal needs now. Native <details> does the
# opening and shutting; what it will not do reliably across engines is open
# itself because the URL names something inside it. Chrome and Safari have
# started auto-expanding for fragment navigation and for Find on Page, Firefox
# has not, and a link she texted to a client that lands on a shut part looks
# like a broken link.
#
# NOTHING IS HIDDEN BY SCRIPT any more -- that is the difference from the
# version this replaces. With JavaScript off the four parts are still there
# and still open on a tap; all this adds is that #money opens The Investment
# on the way in. Failing is therefore harmless, which is the right shape for
# an enhancement.
STEP = """
  (() => {
    const jumpTo = () => {
      if (!location.hash) return;
      let target = null;
      try { target = document.querySelector(location.hash); } catch (e) { return; }
      if (!target) return;
      /* Walk up, because the hash usually names a question and the thing that
         has to open is the part around it. closest() includes the element
         itself, which is what makes #begin work as well as #money. */
      let d = target.closest("details");
      while (d) { d.open = true; d = d.parentElement && d.parentElement.closest("details"); }
      /* After the open, or it scrolls to where the target was while shut. */
      target.scrollIntoView();
    };
    jumpTo();
    window.addEventListener("hashchange", jumpTo);
  })();
"""

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
""" + STEP + """
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
    <p class="jhp-p opener">This guide walks you through what a boudoir shoot
       is and how the process works here at JHP Boudoir. It is in four parts:
       who I am, the things women worry about before they book, how the day
       itself works, and what it costs. Tap a part below to open it and read
       straight through, and take them in whatever order you like.</p>
    <p class="jhp-p">If you have any questions afterwards, please reach out and
       I will get back to you as soon as I can. My studio hours are
       {studio_hours}, and consultation calls run {call_hours}.</p>
  </div>

{parts}
  <div class="jhp-gd jhp-end">
    <h2 class="jhp-h" id="ready">Ready to Book?</h2>
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

# The parts carry the figures, so they are formatted FIRST and the result is
# dropped into the shell as one value -- str.format does not recurse into what
# it substitutes, so a placeholder left inside `parts` would survive to the
# published page.
parts_html = render_parts().format(vip=VIP, **F)
assert "{" not in parts_html.replace("{% raw %}", "").replace("{% endraw %}", ""), \
    "a figure placeholder survived into the parts"

body = BODY.format(cdn=CDN, hero=HERO, calendar=CALENDAR,
                   parts=parts_html, script=SCRIPT, **F)

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

anchors = [p["id"] for p in PARTS] + [i["id"] for p in PARTS for i in p["items"]]
for a in anchors:
    if 'id="%s"' % a not in out:
        raise SystemExit("contents points at #%s and nothing has that id" % a)
if len(anchors) != len(set(anchors)):
    raise SystemExit("two things share an id, so one contents row is a dead link")

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
print("wrote %d bytes, %d parts, %d questions, %d photographs, %d lifted lines"
      % (len(out.encode()), len(PARTS),
         sum(len(p["items"]) for p in PARTS), len(photos),
         out.count('class="jhp-lift"')))

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
