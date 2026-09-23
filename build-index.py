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
  .jhp-home .jhp-gal .nm{padding:24px 6px 10px;font-size:10px;
    letter-spacing:.18em}
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
  max-height:none;object-fit:cover;object-position:50% 34%}
.jhp-home .jhp-intro .jhp-over{position:absolute;inset:0;display:flex;
  flex-direction:column;align-items:center;justify-content:flex-end;
  text-align:center;
  padding:0 clamp(20px,5vw,60px) clamp(26px,3.6vw,46px);
  background:linear-gradient(0deg,rgba(19,16,14,.94) 0%,
    rgba(19,16,14,.78) 24%,rgba(19,16,14,.34) 52%,rgba(19,16,14,.04) 82%)}
.jhp-home .jhp-intro h1{margin:0;max-width:24ch}
@media (max-width:620px){
  /* A flat height again, as on the home page: a share of the width would
     draw this at about 120px on a phone, which is a stripe, not a picture.
     Cropping 3:2 that tall throws away the width instead, so the
     horizontal position is what matters here. */
  .jhp-home .jhp-intro img{height:340px;object-position:50% 30%}
  .jhp-home .jhp-intro h1{max-width:20ch}
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
        "/* The closing band carries no photograph. The grid above it is %d\n"
        "   sessions, so one more behind the text would have said nothing new -\n"
        "   and with no paragraph under it the button needs its own gap. */"
        % len(galleries)) + src[b:]

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
