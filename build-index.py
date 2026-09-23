#!/usr/bin/env python3
"""Rewrites the portfolio index as ten linked client covers.

The index stops being twelve loose photographs and becomes a way in to ten
sessions. Each square is a link, and carries the client's heading so a
visitor knows it opens rather than just sits there -- a hover state alone
would say nothing on a phone.

Squares still crop, which is the price of one rhythm across the row; the
galleries behind them do not. Covers are chosen as the frame that loses
least to a square cut, earliest in Jessica's own order among equals.
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent
CDN = "https://assets.cdn.filesafe.space/Pcnm8GVNMmWTY65qVOAp/media/"

GAL_CSS = """/* THE INDEX
   ---------
   Ten sessions, one square each. Squares crop -- a third off the sides of
   a wide frame, off the top and bottom of a tall one, centred either way --
   because a contact sheet wants one rhythm and mixed shapes do not give
   you one. The galleries behind these squares crop nothing.

   auto-fit rather than a fixed column count, so the row rebalances when
   Jessica adds or retires a client instead of stranding one on a line of
   its own. At full width ten lands as two rows of five. */
.jhp-home .jhp-gal{display:grid;
  grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
  gap:14px;max-width:1300px;margin:0 auto}
.jhp-home .jhp-gal a{position:relative;display:block;aspect-ratio:1/1;
  overflow:hidden;background:rgba(19,16,14,.06)}
.jhp-home .jhp-gal img{position:absolute;inset:0;width:100%;height:100%;
  display:block;object-fit:cover;object-position:50% 50%;
  transition:transform .7s ease}
.jhp-home .jhp-gal a:hover img{transform:scale(1.045)}
.jhp-home .jhp-gal a:focus-visible{outline:2px solid var(--gold-bright);
  outline-offset:3px}

/* The name sits on the photograph rather than under it, so the squares
   stay a grid of pictures and the row does not gain a band of text. The
   gradient is there to keep the name legible over a bright frame. */
.jhp-home .jhp-gal .nm{position:absolute;left:0;right:0;bottom:0;
  padding:30px 10px 13px;font-family:var(--sans);font-size:11px;
  letter-spacing:.24em;text-transform:uppercase;color:var(--ink);
  text-align:center;
  background:linear-gradient(180deg,rgba(19,16,14,0),rgba(19,16,14,.78))}

@media (max-width:620px){
  .jhp-home .jhp-gal{grid-template-columns:repeat(2,1fr);gap:8px;
    max-width:none;margin-inline:calc((100% - 100vw) / 2)}
  .jhp-home .jhp-gal .nm{padding:24px 6px 10px;font-size:10px;
    letter-spacing:.18em}
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
    src = src.replace(
        "   thirteenth behind the text would have said nothing new - and with no",
        "   eleventh behind the text would have said nothing new - and with no")
    src = src.replace("The grid above it is twelve, so a",
                      "The grid above it is ten sessions, so an")

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
