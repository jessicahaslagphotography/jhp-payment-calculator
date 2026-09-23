#!/usr/bin/env python3
"""Generates scalogy-gallery.html -- one template, twelve client galleries.

Scalogy pages are static HTML: the page-api token that would let a page
fetch its own data lives fifteen minutes, so a visitor arriving later
than that would find an empty gallery. The data has to be baked in at
render time instead, which pages_render does when you hand it `data`.

So one template serves all twelve galleries, and each page is rendered
with its own client's rows. Adding a client's photographs is one render
call, not a new template.

The design system is sliced out of scalogy-portfolio.html at build time,
the same way the portfolio slices it from the About page, so the pages
cannot drift apart.
"""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent
src = (ROOT / "scalogy-portfolio.html").read_text()

# Everything from the shared-system banner down to the gallery's own rules.
MARK = "/* THE GALLERY" if "/* THE GALLERY" in src else "/* THE INDEX"
head = src[:src.index(MARK)]
tail = src[src.index("/* The closing band carries no photograph."):]
shared_css = tail[:tail.index("</style>")]
shared_css = shared_css[shared_css.index(".jhp-home .jhp-vip .jhp-h"):]
after_style = tail[tail.index("</style>"):]

# nav + footer come over verbatim; only the middle is this page's own.
nav = after_style[after_style.index("<nav class=\"jhp-nav\">"):
                  after_style.index("<section class=\"jhp-sec\"")]
foot = after_style[after_style.index("<footer class=\"jhp-foot\">"):]

GAL_CSS = """/* THE CLIENT GALLERY
   ------------------
   Justified rows, not a grid. Every frame keeps the shape it was taken in
   -- the index crops to squares because a contact sheet wants one rhythm,
   but a session is the work itself and nothing here is cut.

   The trick is one declaration: within a row each figure gets flex-grow
   equal to its own aspect ratio, so widths come out proportional to shape
   and every frame in the row lands on exactly the same height. The row
   fills the width with no arithmetic and no letterboxing, at any size.

   Row composition is chosen per gallery from the actual mix of tall and
   wide frames -- one wide alone, then three, then a pair -- so the page
   changes shape as you scroll instead of repeating. */
.jhp-home .jhp-set{max-width:1240px;margin:0 auto;
  display:flex;flex-direction:column;gap:14px}
.jhp-home .jhp-set .row{display:flex;gap:14px}
.jhp-home .jhp-set figure{margin:0;min-width:0}
.jhp-home .jhp-set img{width:100%;height:auto;display:block}

/* Between tablet and desktop a row of three is too tight, so rows wrap.
   Each wrapped line re-justifies itself by the same flex-grow rule, which
   is why the heights still agree after the break. */
@media (max-width:900px){
  .jhp-home .jhp-set .row{flex-wrap:wrap}
  .jhp-home .jhp-set .row figure{min-width:calc(50% - 7px)}
}
/* One frame per row edge to edge on a phone -- the rule the About page
   follows, where photographs take the full width and only text keeps its
   margins. Three across would draw each one at about 120px. */
@media (max-width:620px){
  .jhp-home .jhp-set{max-width:none;gap:10px;
    margin-inline:calc((100% - 100vw) / 2)}
  .jhp-home .jhp-set .row{flex-direction:column;gap:10px}
  .jhp-home .jhp-set .row figure{min-width:0}
}

/* The way back. A gallery is a dead end without it, and the browser's
   back button is not a design. */
.jhp-home .jhp-back{display:block;text-align:center;
  font-family:var(--sans);font-size:11px;letter-spacing:.24em;
  text-transform:uppercase;color:var(--dim);padding:26px 18px 0;
  transition:color .3s}
.jhp-home .jhp-back:hover{color:var(--gold)}
"""

BODY = """
<section class="jhp-sec" style="border-bottom:none;padding-bottom:clamp(24px,3vw,34px)">
  <div class="jhp-center">
    <p class="jhp-kicker">A session</p>
    <h1 class="jhp-h jhp-h-lg" style="margin-bottom:14px">{{ name }}</h1>
    <p class="jhp-p" style="margin-bottom:0">{{ blurb }}</p>
  </div>
</section>

<section class="jhp-sec" style="border-bottom:none;padding-top:0">
  <div class="jhp-set">
{% for row in rows %}    <div class="row">
{% for p in row %}      <figure style="flex:{{ p.ar }} 1 0"><img src="{{ cdn }}{{ p.file }}" width="{{ p.w }}" height="{{ p.h }}"{% if not (loop.first and loop.index0 == 0) %} loading="lazy"{% endif %} alt="{{ p.alt }}"></figure>
{% endfor %}    </div>
{% endfor %}  </div>
  <a class="jhp-back" href="../portfolio/">&larr; All sessions</a>
</section>

<section class="jhp-vip">
  <div class="inner">
    <p class="jhp-kicker">When you are ready</p>
    <h2 class="jhp-h">Your Turn</h2>
    <a class="jhp-btn" href="/contact">Book Your Session</a>
  </div>
</section>

"""

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ name }} | JHP Boudoir</title>
<meta name="description" content="A boudoir session photographed by JHP Boudoir, Jefferson City, Missouri.">
<meta name="robots" content="noindex, nofollow">
<meta property="og:title" content="{{ name }} | JHP Boudoir">
<meta property="og:description" content="A boudoir session at JHP Boudoir, Jefferson City, Missouri.">
<meta property="og:type" content="website">
<style>html,body{margin:0;padding:0;background:#13100E}body{overflow-x:hidden}</style>
</head>
<body>
<div class="jhp-home">
<style>
"""

out = (HEAD + head[head.index("/* SHARED DESIGN SYSTEM"):] + GAL_CSS + shared_css
       + "</style>\n\n" + nav + BODY + foot)

# Unlike the other pages this one is a real template, so it carries no
# {% raw %} fence at all -- the CSS, nav and footer contain no Jinja
# tokens, and the body's {{ }} are the whole point.
for tag in ("{% raw %}\n", "{% endraw %}\n", "{% raw %}", "{% endraw %}"):
    out = out.replace(tag, "")
(ROOT / "scalogy-gallery.html").write_text(out)
print("wrote", len(out.encode()), "bytes")
