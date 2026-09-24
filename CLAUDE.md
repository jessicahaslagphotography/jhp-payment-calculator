# JHP Boudoir — house rules for the website

The site is built as Jinja templates on Scalogy and mirrored here as
`scalogy-*.html`. The generators are `build-index.py` (home),
`build-info.py` (FAQ), `build-experience.py` (The Experience),
`build-gallery.py` + `plan-all.py` (the twelve client galleries).
Edit the generator, never the built file.

## Headlines are Title Case. Always.

Every `<h1>`, `<h2>` and `<h3>` on this site is set in title case, on
every page, including new ones. Jessica asked for this on 23 September
and it is not a per-page decision.

Capitalise every word except articles, short conjunctions and short
prepositions in the middle of the line -- `a`, `an`, `the`, `and`, `of`,
`to`, `at`, `for`, `in`, `on` -- which stay lowercase unless they are the
first or last word. The line the rest should match is **What the Day
Looks Like**.

    yes   What Comes With Every Session
    yes   A Studio Designed Exactly for Boudoir
    yes   Professional Posing, Head to Toe
    no    What comes with every session
    no    A room built for exactly this

Not headlines, and left as written sentences: the FAQ's questions, which
are `<summary>` elements phrased the way a client would say them out
loud; the `.lede` under a band heading; the `.sub` line in a band; body
copy. Kickers and the small `.when` labels are already set in uppercase
by their own CSS and need no change in the markup.

## The rest of the system, in one place

- **The design system is sliced, not copied.** `build-info.py` and
  `build-experience.py` cut the tokens, type, nav, bands, divider,
  pull-quote and footer out of `scalogy-portfolio.html` at build time so
  the pages cannot drift. Change a shared rule there and rebuild.
- **Info is a menu, not a page.** The nav carries About, Portfolio, the
  wordmark, Info and Book a Call, and under Info sit FAQ and The
  Experience. Info itself is a `<span>` and goes nowhere -- there is no
  Info page. The menu uses no JavaScript: both links are always in the
  markup and in the tab order, and the panel is revealed by `:hover` and
  `:focus-within`, never by `display` or `visibility` (either would take
  the links out of the tab order and `:focus-within` could then never
  fire). On a phone there is no hover, so the two links simply sit on the
  line beneath Info. All six templates carry the same nav markup
  byte-for-byte; check that with an md5 of the `<nav>` block before
  believing a change landed everywhere.
- **Links are relative** (`../about/`), so they resolve on
  `pages.scalogy.com/jhpboudoir1/` now and on the real domain later. The
  one link that has to change at launch is the JHP wordmark:
  `../home-preview/` becomes `/`.
- **Movement is opt-in.** The CSS renders every page finished; a script
  at the foot adds `js-rev`, which is what collapses the dividers and the
  process spine ready to animate. JavaScript off, no IntersectionObserver
  or a system asking for reduced motion all get the finished page rather
  than an empty gap. Anything animated must follow that pattern.
- **Publishing.** Templates over 20KB truncate on `templates_create`, so
  they go up as a create plus successive `templates_patch` calls, and the
  template has to stay Jinja-parseable at every step -- a `{% raw %}`
  without its `{% endraw %}` is rejected. After a patch, `pages_render`.
  A rendered page is the template less 21 bytes (the raw fence); check
  it every time.
- **One review, one page.** No Google review appears twice on the site.
  Miss M.'s was on three pages at once, beside three different faces, which
  reads as three women who happened to write the identical paragraph. The
  nine reviews Jessica has supplied, where each one sits and why, and the
  three still held back are in `reviews.md` -- read it before adding or
  moving a review, and update it in the same commit. The photograph beside a
  pull-quote is not the woman who wrote it and carries no name for that
  reason, so a review can change pages without the frame changing with it.
- **Photographs are judged at real size.** A frame that looks clear of a
  heading on a contact sheet is often sitting on the subject at 1440. And
  one page, one client per frame -- the same face opening and closing a
  page reads as the only woman who has ever been there.
