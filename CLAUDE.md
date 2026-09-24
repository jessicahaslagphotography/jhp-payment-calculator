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

## The type scale is one scale, and it lives in three files

Jessica asked on 24 September for headings that stand out. What was making
them recede was not only size -- Cormorant Garamond is a high-contrast serif
with light stems, and at `font-weight:500` it went quiet at any size. The
weight is now **600** everywhere, which is loaded already (the `@import` asks
for 400, 500 and 600) and so costs nothing.

The scale, and the only numbers to touch:

    .jhp-h      section heading     clamp(30px, 3.5vw, 46px)   weight 600
    .jhp-h-lg   page display        clamp(38px, 5.6vw, 66px)
    --ph-head   phone section       30px      = the .jhp-h floor
    --ph-display phone display      38px      = the .jhp-h-lg floor

The two phone tokens deliberately equal the two desktop floors. The home page
and the About page carry their own copy of the design system and have no `--ph`
tokens, so on a phone they land on the floors; making the tokens the same
numbers means all seven templates agree at 390px by construction rather than by
two figures somebody has to keep in step.

**A heading must never out-rank the page's own h1.** Both places that broke it
are now guarded and both are worth knowing about:

- The home page's display heading is `.jhp-ttl` in the hero, not `.jhp-h-lg` --
  h-lg does section duty there ("What They Said Afterwards"). So home alone
  steps its phone h-lg down to 34px, under a 40px hero.
- Jessica's tuner-set band heights are fixed, so a bigger heading has to fit
  inside them rather than the other way round. The hero is 280px on a phone and
  at 46px the title wrapped to four lines and pushed the eyebrow up over the
  nav; 40px fits, with a 36px guard below 360px. The About lead band no longer
  carries a heading at all -- Jessica removed "Meet Your Photographer" on
  24 September and the plate went with it, so that band is a photograph and
  the page's h1 is "Jessica Paul" in the intro under it.

After any change here, measure every page at 1440, 390 and 320 and check three
things: no horizontal scroll, no band whose overlay content is taller than the
band, and no h2 larger than that page's h1. The one number that moved off one
of Jessica's own: the About page's closing band was 190px and is now about
199px, because it is padding plus content rather than a set height.

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
- **Contact is the Session Guide, not a calendar.** `/contact` asks for a
  name, email and phone and promises the **Session Guide Magazine**; the
  link to book a consultation call is inside that magazine, not on the site.
  The page names it in full where a visitor first meets it and says "the
  magazine" after -- Jessica's note, 24 September, so a woman can tell what
  actually arrives. "The guide" is the same object and is still correct in
  prose; the string that must never follow the copy is the GHL tag below. Every "Book a
  Call" button on all seven templates lands there, so the label and the page
  do not quite agree -- that is Jessica's wording to settle, not something to
  quietly reword. A submission goes: the form POSTs no-cors to the
  `site-lead-submit` webhook, workflow `site-leads-ingest` writes a
  `site_leads` row and upserts the contact into GHL tagged
  **`Session Guide - Requested`**, and a GHL workflow watching that tag is
  what actually sends the guide. That tag string is the whole contract
  between this site and the guide: if guides stop arriving, check GHL before
  touching the page. `site_leads` holds PII and must never be attached to an
  app. The page needs JavaScript and says so in a `<noscript>`. A no-cors
  POST cannot be confirmed, so a woman whose submission failed silently
  needs a route that does not depend on the form: the footer's Get In Touch
  column is the only one always on the page, with the `<noscript>` line
  (scripting off) and the thank-you state (after submitting) behind it.
  Jessica has removed the two that used to sit in the flow -- the block at
  the foot and the note under the button. **The footer one is load-bearing.**
  Take it out and this page has no recourse at all for a failed submission.
- **/contact is one paragraph and a form, and that is deliberate.** It had a
  five-point contents list and a review; Jessica cut both on 24 September --
  353 words and 3941px on a phone is ten screens of scrolling to collect
  four fields, and a review below the form persuades nobody. What is left is
  the band, her three paragraphs, the form and the VIP band -- and the copy
  has no heading over it either, which went the same day, so the band's h1
  heads the whole page. The paragraph breaks are Jessica's own and are one
  thought each: the invitation, what arrives, what to do if it does not.
  Keep them if the copy is rewritten. The list's substance survives as the clause after
  the dash, and the magazine is named in that paragraph's first sentence
  because nothing above it names the thing any more. Adding a section back
  is a decision to re-make, not an omission to repair -- and anything added
  should be measured against 2388px, which is what the page is now.
- **The VIP group is on two pages and is one link.** The Facebook group
  (`facebook.com/groups/1107773373084834`) is the homepage's `.jhp-vip`
  panel -- mid-page, no photograph -- and the closing `.jhp-band` at the
  foot of `/contact`. They are worded differently on purpose but they point
  at the same group, so changing the group means editing both
  `scalogy-home.html` and `build-contact.py`. Contact's is the only one of
  the four closing bands whose href leaves the site, which is why it alone
  carries `target="_blank"` and `rel="noopener"`; it is also why `/contact`
  now slices `THE WAY ON` out of the portfolio, which it used not to.
- **Links are relative** (`../about/`), so they resolve on
  `pages.scalogy.com/jhpboudoir1/` now and on the real domain later. The
  one link that has to change at launch is the JHP wordmark:
  `../home-preview/` becomes `/`.
- **Specialty Sessions in the footer is the Treehouse page.** It pointed at
  `/specialty-sessions`, which 404s, in all seven footers; it is
  `../treehouse-sessions/` now -- Jessica's own live landing page for the
  Treehouse Specialty Sessions. It is relative like every other link, which
  is right today. AT LAUNCH IT MAY NOT BE: that page also has its own
  custom domain, `treehouse.jhpboudoir.com`, and a Scalogy custom domain
  maps to ONE page, so if `jhpboudoir.com` ends up serving only the home
  page then `/treehouse-sessions/` will not exist under it and this link
  wants to become the absolute subdomain. Decide it with the wordmark link
  above, not separately. **`/blog` in the same footer is still dead** and
  still 404s in all seven.
- **Changing the footer means eighteen pages, not seven.** The footer lives
  in `scalogy-home.html` and `scalogy-about.html` by hand and in
  `scalogy-portfolio.html` for everything sliced from it, so a footer edit
  is three files plus a rebuild -- and then seven templates to patch and
  **eighteen** pages to render, because the twelve galleries all share
  `jhp-gallery-2026`. THE GALLERIES RENDER FROM DATA: `pages_render` on one
  of them without its payload from `renders/<slug>.json` would publish an
  empty page. Render each with its payload and check the byte count against
  a local Jinja render of `scalogy-gallery.html` first.
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
- **A pull-quote leads on its most impactful line.** Jessica's note,
  24 September: each of the three pull-quotes is now a big `.qt` line, a
  `.qr` paragraph with the rest of what she wrote, and one phrase inside it
  in gold (`.hl`). **The split is always at a sentence boundary** -- a
  sentence is lifted whole or not at all, nothing is reworded or trimmed to
  make a better headline, and the remainder keeps her original order. Which
  sentence was lifted from which review, and why, is the table in
  `reviews.md`. The home page's three are a wall, not pull-quotes, and are
  deliberately left alone.
- **Photographs are judged at real size.** A frame that looks clear of a
  heading on a contact sheet is often sitting on the subject at 1440. And
  one page, one client per frame -- the same face opening and closing a
  page reads as the only woman who has ever been there.
