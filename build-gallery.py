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
head = src[:src.index("/* THE GALLERY")]
tail = src[src.index("/* The closing band carries no photograph."):]
shared_css = tail[:tail.index("</style>")]
after_style = tail[tail.index("</style>"):]

# nav + footer come over verbatim; only the middle is this page's own.
nav = after_style[after_style.index("<nav class=\"jhp-nav\">"):
                  after_style.index("<section class=\"jhp-sec\"")]
foot = after_style[after_style.index("<footer class=\"jhp-foot\">"):]

GAL_CSS = """/* THE CLIENT GALLERY
   ------------------
   Uncropped, unlike the twelve squares on the index. The index is a
   contact sheet and wants one rhythm; a session is the work itself and
   every frame keeps the shape it was taken in. Multi-column absorbs the
   difference between her tall and wide frames without cutting either.

   Reading order runs down a column rather than across the page, which
   costs nothing here -- there are no captions and no narrative, just a
   set. */
.jhp-home .jhp-set{columns:3;column-gap:16px;max-width:1240px;margin:0 auto}
.jhp-home .jhp-set figure{break-inside:avoid;margin:0 0 16px}
.jhp-home .jhp-set img{width:100%;height:auto;display:block}
@media (max-width:960px){
  .jhp-home .jhp-set{columns:2;column-gap:12px}
  .jhp-home .jhp-set figure{margin-bottom:12px}
}
/* One column edge to edge on a phone, the rule the About page follows:
   photographs take the full width, only text keeps its margins. */
@media (max-width:620px){
  .jhp-home .jhp-set{columns:1;max-width:none;
    margin-inline:calc((100% - 100vw) / 2)}
  .jhp-home .jhp-set figure{margin-bottom:10px}
}

/* A single photograph is not a gallery -- it is a portrait, so it gets
   drawn as one rather than stretched across three dead columns. */
.jhp-home .jhp-set.one{columns:1;max-width:760px}

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
  <div class="jhp-set{% if photos|length == 1 %} one{% endif %}">
{% for p in photos %}    <figure><img src="{{ cdn }}{{ p.file }}"{% if not loop.first %} loading="lazy"{% endif %} alt="{{ p.alt }}"></figure>
{% endfor %}  </div>
  <a class="jhp-back" href="/portfolio">&larr; All sessions</a>
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
