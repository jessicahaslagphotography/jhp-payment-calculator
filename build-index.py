#!/usr/bin/env python3
"""Rewrites the portfolio index as ten linked client covers.

The index stops being twelve loose photographs and becomes a way in to her
sessions. Each square is a link, and carries the client's heading so a
visitor knows it opens rather than just sits there -- a hover state alone
would say nothing on a phone.

Every count in the page is read from galleries.json, so adding a client is
this script and nothing else.

Squares still crop, which is the price of one rhythm across the row; the
galleries behind them do not. Covers are chosen as the frame that loses
least to a square cut, earliest in Jessica's own order among equals.
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent
CDN = "https://assets.cdn.filesafe.space/Pcnm8GVNMmWTY65qVOAp/media/"

GAL_CSS = """/* THE INDEX
   ---------
   One session per square, three to a row. Squares crop -- a third off the
   sides of a wide frame, off the top and bottom of a tall one, centred
   either way -- because a contact sheet wants one rhythm and mixed shapes
   do not give you one. The galleries behind these squares crop nothing.

   A count that leaves one over would put that last square alone at the
   left of its row looking like a mistake. Columns are capped rather than
   fractional so the grid can centre itself in the page, and a last square
   that lands in column one on its own is moved to the middle -- a
   deliberate-looking full stop instead of an orphan. Both rules are
   conditional, so a count that divides evenly is left alone.

   Two across on a phone: three would draw each session at about 120px. */
.jhp-home .jhp-gal{display:grid;
  grid-template-columns:repeat(3,minmax(0,370px));
  justify-content:center;gap:14px;margin:0 auto}
.jhp-home .jhp-gal a{position:relative;display:block;aspect-ratio:1/1;
  overflow:hidden;background:rgba(19,16,14,.06)}
.jhp-home .jhp-gal img{position:absolute;inset:0;width:100%;height:100%;
  display:block;object-fit:cover;object-position:50% 50%;
  transition:transform .7s ease}
.jhp-home .jhp-gal a:hover img{transform:scale(1.045)}
.jhp-home .jhp-gal a:focus-visible{outline:2px solid var(--gold-bright);
  outline-offset:3px}
/* The centring itself: only when the final square would start a row alone. */
.jhp-home .jhp-gal a:last-child:nth-child(3n+1){grid-column:2}

/* The name sits on the photograph rather than under it, so the squares
   stay a grid of pictures and the row does not gain a band of text. The
   gradient is there to keep the name legible over a bright frame. */
.jhp-home .jhp-gal .nm{position:absolute;left:0;right:0;bottom:0;
  padding:32px 10px 13px;font-family:var(--sans);font-size:11px;
  letter-spacing:.24em;text-transform:uppercase;color:var(--ink);
  text-align:center;
  background:linear-gradient(180deg,rgba(19,16,14,0),rgba(19,16,14,.78))}

@media (max-width:620px){
  .jhp-home .jhp-gal{grid-template-columns:repeat(2,1fr);gap:8px;
    margin-inline:calc((100% - 100vw) / 2)}
  /* An even count divides by two, so nothing is orphaned here and the
     middle-column rule has to be switched back off. */
  .jhp-home .jhp-gal a:last-child:nth-child(3n+1){grid-column:auto}
  .jhp-home .jhp-gal .nm{padding:26px 6px 11px;font-size:var(--ph-label);
    letter-spacing:.2em}
}

/* THE INTRO
   ---------
   The page opens on a photograph rather than on type. The band crops: a
   3:2 frame cut to this height keeps its full width and loses about a
   third of its height, taken a little above centre because that is where
   faces sit. Frame and crop are one line each to change -- the src below
   and the object-position here.

   Shorter than the home page's hero on purpose. That one is the front
   door and can afford the whole screen; this one is a heading with a
   picture behind it, and the sessions need to be in reach. */
.jhp-home .jhp-intro{position:relative}
.jhp-home .jhp-intro img{width:100%;height:clamp(320px,37vw,600px);
  max-height:none;object-fit:cover;object-position:50% 77%}
.jhp-home .jhp-intro .jhp-over{position:absolute;inset:0;display:flex;
  flex-direction:column;align-items:center;justify-content:flex-end;
  text-align:center;
  padding:0 clamp(20px,5vw,60px) clamp(26px,3.6vw,46px);
  background:linear-gradient(0deg,rgba(19,16,14,.94) 0%,
    rgba(19,16,14,.78) 24%,rgba(19,16,14,.34) 52%,rgba(19,16,14,.04) 82%)}
.jhp-home .jhp-intro h1{margin:0;max-width:24ch}
@media (max-width:620px){
  /* A flat height, as on the home page: a share of the width would draw
     this at about 120px on a phone, which is a stripe, not a picture.
     Jessica set 220 in the band tuner, with the crop at 43% across and 89%
     down -- low enough that the band is the floor and her legs rather than
     the windows, which is where the headline wanted to sit. */
  .jhp-home .jhp-intro img{height:220px;object-position:43% 89%}
  /* The height is hers and does not move, so the headline has to be the
     thing that fits it: at the page's display size it takes two lines and
     leaves the top half of the band as photograph. 20ch would have broken
     it into three. */
  .jhp-home .jhp-intro h1{max-width:23ch}
  .jhp-home .jhp-intro .jhp-over{padding:0 var(--ph-gut) 24px}
}

/* THE DIVIDER
   -----------
   Between the grid, the quote and the way on. A hairline that fades out
   at both ends rather than running wall to wall, with a small gold lozenge
   on the centre -- the same gold the kickers and the button use, so the
   page gains a rhythm mark and not a new colour. Purely decorative, so it
   is hidden from screen readers.

   The line is drawn on ::before rather than as a background on the element
   itself, because the reveal below scales the line and the lozenge must
   not scale with it.

   The movement: each divider draws outward from its own centre as it comes
   into view, and the lozenge settles in behind it. Once per divider. It is
   opt in from the script at the foot of the page -- without the js-rev
   class these rules never apply and the dividers are simply drawn, so a
   reader with JavaScript off, or one whose system asks for reduced motion,
   gets the mark rather than an empty gap. */
.jhp-home .jhp-div{position:relative;height:1px;max-width:1080px;margin:0 auto}
.jhp-home .jhp-div::before{content:"";position:absolute;inset:0;
  background:linear-gradient(90deg,transparent,
    var(--line) 20%,var(--line) 80%,transparent)}
.jhp-home .jhp-div::after{content:"";position:absolute;left:50%;top:50%;
  width:7px;height:7px;margin:-4px 0 0 -4px;transform:rotate(45deg);
  background:var(--ground);border:1px solid var(--gold)}
.jhp-home.js-rev .jhp-div::before{transform:scaleX(0);transform-origin:50% 50%;
  transition:transform .9s cubic-bezier(.22,.61,.36,1)}
.jhp-home.js-rev .jhp-div::after{opacity:0;transform:rotate(45deg) scale(.4);
  transition:opacity .45s ease .34s,
    transform .5s cubic-bezier(.34,1.28,.64,1) .34s}
.jhp-home.js-rev .jhp-div.in::before{transform:scaleX(1)}
.jhp-home.js-rev .jhp-div.in::after{opacity:1;transform:rotate(45deg) scale(1)}

/* THE QUOTE
   ---------
   One review, not three. The home page carries the wall of them; here a
   single voice after twelve galleries says the thing the photographs
   cannot -- what it felt like.

   A frame stands beside it, in the 150.3% box every portrait in the
   library fits, so cover has nothing to crop. It is a photograph of a JHP
   client, not of the woman who wrote the review, and it carries no name
   for that reason: it is there to give the words a face's worth of weight,
   the way a magazine sets a pull-quote against an image.

   Set left rather than centred at this width -- centred type beside a
   photograph reads as a caption. It re-centres when the two stack. */
.jhp-home .jhp-quote{display:grid;
  grid-template-columns:minmax(0,.62fr) minmax(0,1fr);
  gap:clamp(26px,4.5vw,64px);align-items:center;
  max-width:1040px;margin:0 auto;text-align:left}
.jhp-home .jhp-quote .shot{position:relative;min-width:0;margin:0}
.jhp-home .jhp-quote .shot::before{content:"";display:block;padding-top:150.3%}
.jhp-home .jhp-quote .shot img{position:absolute;inset:0;width:100%;
  height:100%;object-fit:cover;object-position:center center}
.jhp-home .jhp-quote blockquote{margin:0}
.jhp-home .jhp-quote .qt{font-family:var(--serif);font-style:italic;
  font-size:clamp(18px,1.95vw,23px);line-height:1.55;color:var(--ink);
  margin:0 0 20px;text-wrap:pretty}
.jhp-home .jhp-quote .qa{font-family:var(--sans);font-size:11px;
  letter-spacing:.24em;text-transform:uppercase;color:var(--gold);margin:0}
.jhp-home .jhp-quote .src{display:inline-block;margin-top:18px;
  font-family:var(--sans);font-size:12px;letter-spacing:.06em;
  color:var(--dim);border-bottom:1px solid var(--line);padding-bottom:2px;
  transition:color .3s,border-color .3s}
.jhp-home .jhp-quote .src:hover{color:var(--gold);border-color:var(--gold)}
@media (max-width:820px){
  /* Side by side the photograph would be narrower than the words are tall.
     Stacked it leads, and the quote centres under it. */
  .jhp-home .jhp-quote{grid-template-columns:1fr;gap:24px;max-width:520px;
    text-align:center}
}
@media (max-width:620px){
  /* The page's phone rule: photographs run edge to edge, only text keeps
     its margins.

     Edge to edge in the 150.3% box the portrait is drawn 586px tall on a
     390px screen, which is a wall you scroll past rather than a picture
     you see. Capped to a plate instead -- the box goes and a height takes
     its place, and cover crops the difference off the top and bottom,
     centred, which on this frame is headroom and floor. */
  .jhp-home .jhp-quote .shot{margin-inline:calc((100% - 100vw) / 2);
    height:430px}
  .jhp-home .jhp-quote .shot::before{content:none}
  .jhp-home .jhp-quote .qt{font-size:19px;line-height:1.6;margin-bottom:18px}
  .jhp-home .jhp-quote .qa{font-size:var(--ph-label);letter-spacing:.22em}
  .jhp-home .jhp-quote .src{font-size:12px;margin-top:16px}
}

/* THE WAY ON
   ----------
   The whole band is the link, so there is no small target to find: the
   button inside it is a span, not a second anchor, which keeps the markup
   legal and the click area the full width. Shorter than the intro band
   above -- it is a door, not a heading. */
.jhp-home .jhp-band{position:relative;display:block;overflow:hidden}
.jhp-home .jhp-band img{width:100%;height:clamp(320px,34vw,520px);
  max-height:none;object-fit:cover;object-position:50% 22%;
  transition:transform .8s ease}
.jhp-home .jhp-band:hover img{transform:scale(1.04)}
.jhp-home .jhp-band:focus-visible{outline:2px solid var(--gold-bright);
  outline-offset:-4px}
/* Type to the left, as on the home page's hero. The band crops only
   vertically -- it is wider than the frame at every screen -- so the
   subject stays centred whatever the crop does, and centred type would
   land on her face. Two gradients: one up from the floor for the words,
   one in from the left so they hold against a bright frame. */
.jhp-home .jhp-band .over{position:absolute;inset:0;display:flex;
  flex-direction:column;align-items:flex-start;justify-content:center;
  text-align:left;padding:0 clamp(22px,6vw,74px);
  background:
    linear-gradient(0deg,rgba(19,16,14,.8) 0%,rgba(19,16,14,.42) 55%,
      rgba(19,16,14,.3) 100%),
    linear-gradient(90deg,rgba(19,16,14,.72) 0%,rgba(19,16,14,.34) 38%,
      rgba(19,16,14,0) 68%)}
.jhp-home .jhp-band h2{margin:0 0 8px;max-width:17ch}
.jhp-home .jhp-band .sub{font-family:var(--sans);font-weight:300;
  font-size:15.5px;color:var(--muted);margin:0 0 22px;max-width:30ch}
/* A span dressed as the button: the band is already the anchor. */
.jhp-home .jhp-band .jhp-btn{pointer-events:none}
/* The divider immediately above the band would otherwise sit on the
   photograph's top edge -- the band carries no padding of its own. */
.jhp-home .jhp-div + .jhp-band{margin-top:clamp(42px,6vw,72px)}
@media (max-width:620px){
  /* Jessica set this band's height and crop in the tuner, so neither
     moves. What changes is that a phone crops the frame the other way --
     the band is now taller than the frame's shape, so it is scaled to
     the height and cut at the sides, which puts the subject in the middle
     of the picture instead of off to the right. The left gradient alone
     could not hold the words against her. So: a heavier scrim, and
     measures short enough that neither line reaches her.

     The words stay left rather than centring to match the band at the top
     of the page -- centred here would put them straight on her face. */
  .jhp-home .jhp-band .over{padding:0 var(--ph-gut);
    background:
      linear-gradient(0deg,rgba(19,16,14,.86) 0%,rgba(19,16,14,.52) 58%,
        rgba(19,16,14,.4) 100%),
      linear-gradient(90deg,rgba(19,16,14,.9) 0%,rgba(19,16,14,.66) 50%,
        rgba(19,16,14,.16) 100%)}
  .jhp-home .jhp-band h2{max-width:16ch;margin-bottom:10px}
  .jhp-home .jhp-band .sub{font-size:var(--ph-sub);max-width:22ch;
    margin-bottom:20px}
}
"""


def cover(photos):
    """The frame that loses least to a square cut, earliest among equals."""
    def loss(p):
        f, label, w, h = p
        return round(abs(1 - min(w, h) / max(w, h)), 4)
    best = min(loss(p) for p in photos)
    return next(p for p in photos if loss(p) == best)


def main():
    galleries = json.loads((ROOT / "galleries.json").read_text())
    src = (ROOT / "scalogy-portfolio.html").read_text()

    # Swap the gallery CSS block.
    mark = "/* THE GALLERY" if "/* THE GALLERY" in src else "/* THE INDEX"
    a = src.index(mark)
    b = src.index("/* The closing band carries no photograph.")
    src = src[:a] + GAL_CSS + src[b:]
    # The closing band's comment counts the grid above it, so it is written
    # from the data rather than left to go stale on the next client.
    a = src.index("/* The closing band carries no photograph.")
    b = src.index("*/", a) + 2
    src = src[:a] + (
        "/* The closing band carries no photograph. This page no longer\n"
        "   carries the band at all -- the way on to Info does that work, and\n"
        "   two dark bands in a row said the same thing twice -- but the rule\n"
        "   stays: the galleries slice their design system from this file and\n"
        "   each of them still closes on Your Turn.\n\n"
        "   That first sentence is also the marker build-gallery.py cuts on.\n"
        "   Keep it verbatim. */") + src[b:]

    cards = []
    for g in galleries:
        f, label, w, h = cover(g["photos"])
        cards.append(
            '    <a href="../%s/"><img src="%s%s" width="%d" height="%d"%s '
            'alt="%s &mdash; a boudoir session at JHP Boudoir">'
            '<span class="nm">%s</span></a>'
            % (g["slug"], CDN, f, w, h,
               "" if len(cards) < 5 else ' loading="lazy"',
               g["name"], g["name"]))

    start = src.index('  <div class="jhp-gal">')
    end = src.index("  </div>\n</section>", start) + len("  </div>")
    src = src[:start] + '  <div class="jhp-gal">\n' + "\n".join(cards) \
        + "\n  </div>" + src[end:]

    (ROOT / "scalogy-portfolio.html").write_text(src)
    print("index rewritten:", len(cards), "covers,", len(src.encode()), "bytes")
    for g, c in zip(galleries, cards):
        f, label, w, h = cover(g["photos"])
        print("  %-8s %-14s %dx%d" % (g["name"], label, w, h))


main()
