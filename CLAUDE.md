# JHP Boudoir — house rules for the website

The site is built as Jinja templates on Scalogy and mirrored here as
`scalogy-*.html`. The generators are `build-index.py` (the PORTFOLIO --
not the home page, whatever this line used to say), `build-info.py` (FAQ),
`build-experience.py` (The Experience), `build-contact.py` (/contact) and
`build-gallery.py` + `plan-all.py` (the twelve client galleries).
**`scalogy-home.html` and `scalogy-about.html` have no generator** and are
edited by hand. Everywhere else: edit the generator, never the built file.

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

## SEO: the site is switched off, and that is on purpose

**Every page is `noindex, nofollow`.** That is not an oversight and it is
not a bug to fix in passing. While `www.jhpboudoir.com` still serves the
Showit site, letting Google index the Scalogy preview would put two JHP
Boudoir sites in the index competing with each other, and the one that
wins might be the preview URL. The tag comes off at launch, as one
deliberate step, with Jessica's say-so -- never as a side effect of some
other change.

Until then **every other SEO signal is built and inert**, which is the
right order: switched on at launch it all counts from day one.

What is in place, and the rules that go with it:

- **Titles and descriptions carry the location.** Every `<title>` leads
  with what the page is and names Jefferson City or Missouri, and stops
  under about 60 characters so Google does not truncate it; descriptions
  sit near 150. They are not headlines and the Title Case rule above does
  not apply to them.
- **`SITE` is `https://pages.scalogy.com/jhpboudoir1` and it is wrong at
  launch.** Canonical and `og:url` are built from it on all seven
  templates, and the twelve galleries build theirs from the `slug` now
  stored in each `renders/<slug>.json`. Changing the domain means changing
  it in three HTML files and four generators -- do it in the same pass as
  the wordmark link and the Specialty Sessions link.
- **Share cards exist now and did not before.** Every page has `og:image`,
  `og:image:alt` and a `summary_large_image` Twitter card; each gallery
  uses its own first photograph. Before this, any link she texted or
  posted rendered as a blank grey box. The frames are 3:2 and the ideal is
  1.91:1, so a purpose-made 1200x630 card would crop better -- worth doing,
  not urgent.
- **The FAQ's structured data is DERIVED, never written twice.**
  `build-info.py` parses the built accordion and emits `FAQPage` JSON-LD
  from it, so the copy Google reads cannot drift from the copy a woman
  reads. It filters to `.jhp-ask` on purpose: the phone nav is a
  `<details>`/`<summary>` too and its summary says "Menu". It hard-fails
  the build if fewer than eight questions parse, so a markup change that
  breaks the parser is loud rather than silent.
- **The business schema on the home page has three deliberate holes.**
  No `streetAddress`, no `telephone`, no `geo` -- none of those are
  written down anywhere in this project, and NAP has to match the Google
  Business Profile character for character or it actively costs her.
  A guessed address is worse than no address. And no `aggregateRating` or
  review markup at all: Google does not permit a business to mark up
  reviews of itself on its own site. Her Google reviews do their work on
  the GBP listing.
- **The `@type` is `ProfessionalService`**, which is certainly a valid
  LocalBusiness subtype. `PhotographyBusiness` may be more specific and
  would be a one-word upgrade; confirm it in Rich Results Test first,
  because an invalid type voids the whole block.

Still to do, roughly in order of what it is worth:

1. **The Google Business Profile, which is not in this repo at all.** It
   carries about a third of local ranking weight on its own -- more than
   everything on this site put together -- and the single biggest factor
   inside it is the primary category. Nothing here substitutes for it.
2. **Nothing is written for anyone to find.** There is no blog and
   `/blog` 404s. For a local studio that is the main organic lever there
   is, and the FAQ answers are already the raw material.
3. **165 gallery photographs share one alt string**, word for word:
   "Boudoir portrait from a session at JHP Boudoir". It is honest and it
   is useless -- to Google Images and to a screen reader alike.
4. **No `srcset` anywhere.** Full 1600px frames are served to 390px
   phones, which is the page-speed problem on this site.
5. **`sitemap.xml` and `robots.txt`** both want the real domain and
   cannot be written until it is bound.
6. **The name is inconsistent.** The About h1 says "Jessica Paul"; its
   own meta description, its title and all six alt texts say "Jessica
   Haslag". Search engines treat a person as an entity and entity
   consistency matters, so this needs settling -- and it is Jessica's to
   settle, not a find-and-replace.

## The rest of the system, in one place

- **The design system is sliced, not copied.** `build-info.py` and
  `build-experience.py` cut the tokens, type, nav, bands, divider,
  pull-quote and footer out of `scalogy-portfolio.html` at build time so
  the pages cannot drift. Change a shared rule there and rebuild.
- **The nav is the wordmark hard left and everything else hard right.**
  Jessica's ask, 24 September; before it the bar was one centred row with
  JHP sitting in the middle of the links. The mark is a direct child of
  `.jhp-nav`, which is `justify-content:space-between`; every link lives in
  a `.jhp-navr` flex row beside it. The wrapper exists because
  space-between across seven children would spread them over the whole bar
  rather than gather them, and it takes **`align-self:stretch`** so it
  still fills the nav's content height -- that height is what the Info
  panel's `margin-top:21px` (padding-bottom plus the 1px border) is
  measured from, and without it the panel floats off the rule under the
  header. Reading order is About, Portfolio, Info, Specialty Sessions,
  Book a Call.
- **Info is a menu, not a page.** Under Info sit FAQ and The Experience.
  Info itself is a `<span>` and goes nowhere -- there is no Info page. On a
  desktop the menu uses no JavaScript: both links are always in the markup
  and in the tab order, and the panel is revealed by `:hover` and
  `:focus-within`, never by `display` or `visibility` (either would take
  the links out of the tab order and `:focus-within` could then never
  fire). On a phone Info is not a menu at all -- it is a section label
  inside the drawer, with its two pages as ordinary rows indented beneath
  it. A word that goes nowhere does not get a 44px tap target.
- **On a phone the whole nav is a drawer, and it is a `<details>`.**
  Jessica's ask, 24 September. Flat, six links and a wordmark came to four
  rows and 165px of bar before a visitor saw a photograph. Closed it is now
  one 71px row -- the mark left, the word **Menu** and a chevron right --
  and the hero starts 94px higher. Open, the panel hangs off `.jhp-nav`
  (which is the positioned ancestor and carries `z-index:30`), so it
  overlays the hero rather than pushing the page down: 306px, full width,
  one link per row on a hairline, every row 44px or more.
  Still no JavaScript, but not by the same trick as the desktop panel: a
  phone has no hover, so this needs a real open and shut. `<details>` gives
  a focusable control, Enter and Space, and a disclosure a screen reader
  announces as one -- none of which a checkbox dressed as a button gets
  right. The FAQ's accordion is the same element, so the site now uses it
  twice for the same reason.
  **Two rules keep the two states apart, and neither is optional.** Up top
  the wrapper is dissolved (`.jhp-navd{display:contents}`, the summary
  hidden) AND `::details-content` is forced visible, because browsers hide
  a closed `<details>` two different ways -- older engines with a display
  rule on the children, which a child can override, newer ones with
  `content-visibility` on that pseudo, which a child cannot. Setting both
  means the desktop bar is always drawn whatever state the details is left
  in, including the state a visitor leaves it in by opening the menu on a
  phone and turning the phone sideways. In the phone block, because those
  overrides are inherited, the closed state has to be stated outright:
  `.jhp-navd:not([open]) .jhp-navr{display:none}`. Leave that line out and
  the drawer hangs open on every phone.
  **It does not close on an outside tap.** No-JS `<details>` closes only
  from its own summary. Tapping a link navigates away, so the only cost is
  a menu left open over the hero until Menu is tapped again. Closing it on
  an outside tap needs a few lines of JavaScript, and that is a trade to
  make deliberately rather than by accident.
  All seven templates carry the same nav markup byte-for-byte; check that
  with an md5 of the `<nav>` block before believing a change landed
  everywhere.
- **Contact is the Session Guide AND the calendar. She gets both.**
  Jessica's ask, 24 September; until then it was the guide alone and the
  booking link lived inside it, which meant every "Book a Call" button on
  the site landed on a page with no calendar on it. That is closed now.
  `/contact` asks for a name, email and phone, and on submit the page goes
  **straight to her GHL `Info` calendar**
  (`api.leadconnectorhq.com/widget/booking/mi2EqYRq4gGEbBJHe82b`) with the
  four fields she just typed carried over as query parameters, while the
  magazine still arrives by email off the same webhook. No confirmation
  screen in between -- her choice, made against the alternative of pausing
  on one. The copy above the form says both things happen, because a
  calendar nobody was told about is a surprise, not a hand-off.
  **`keepalive:true` on that fetch is load-bearing now in a way it was not
  before.** The page navigates away in the same breath as the POST; without
  keepalive the browser is free to cancel the in-flight request and the
  lead is lost on the way to the calendar. Verified against a server that
  deliberately waited 1.2s to acknowledge: the page was already on the
  calendar at 400ms and the body still arrived. Do not drop it, and do not
  move the redirect above the fetch.
  The page still names the **Session Guide Magazine** in full where a
  visitor first meets it and says "the magazine" after, so she can tell what
  actually arrives. "The guide" is the same object and is still correct in
  prose; the string that must never follow the copy is the GHL tag below.
  The submit button still reads "Send Me the Session Guide", which now
  under-describes what pressing it does -- Jessica's wording to settle, not
  something to quietly reword.
  A submission goes: the form POSTs no-cors to the `site-lead-submit`
  webhook, workflow `site-leads-ingest` writes a `site_leads` row and
  upserts the contact into GHL tagged **`Session Guide - Requested`**, and a
  GHL workflow watching that tag is what actually sends the guide. That tag
  string is the whole contract between this site and the guide: if guides
  stop arriving, check GHL before touching the page. `site_leads` holds PII
  and must never be attached to an app. The page needs JavaScript and says
  so in a `<noscript>`.
  **The thank-you state is a fallback, not the flow, and is not dead code.**
  It shows in exactly two cases: a filled honeypot (a bot, which gets a
  thank-you and no request) and a redirect the browser refused, which an
  extension or a locked-down in-app webview can do. It therefore has to
  stand alone as the last thing a woman sees, which is why it carries a
  Schedule My Call button rather than a sentence about a link.
  A no-cors POST still cannot be confirmed, so a woman whose submission
  failed silently needs a route that does not depend on the form. With the
  page no longer ending on the thank-you, **the footer's Get In Touch column
  is what is left** -- along with the `<noscript>` line if scripting is off.
  Take the footer one out and this page has no recourse at all. The one
  consolation is that booking the call reaches Jessica even when the POST
  did not, so a silent failure now costs the magazine rather than the lead.
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
  should be measured against 2380px, which is what the page is now. (It was
  2388 before the calendar hand-off; the third paragraph gained a clause and
  the copy re-wrapped 8px shorter, so nothing was spent.)
- **There are two forms now, and they are for two different women.**
  `/contact` is for the woman who is still looking: four fields, the Session
  Guide Magazine, and straight on to the calendar. `/inquire` is for the one
  who has decided: nine questions, and it ends on a thank-you rather than a
  scheduler. Its generator is `build-inquiry.py`, which slices the shared
  system out of `scalogy-portfolio.html` exactly as the other generators do
  and takes the form CSS out of `scalogy-contact.html` on top -- so the
  inputs, the focus ring and the 16px floor are one set of rules, not two.
  Template `jhp-inquire-2026`, page `inquire`, 52,877 bytes live.
  The fields are first, last, email, phone, which session (studio / outdoor /
  not sure), timeframe, occasion, how she heard, notes, an acknowledgment
  checkbox and a honeypot. The three selects Jessica cares about are
  whitelisted **server side as well** in `scripts/site_inquiry_ingest.py`;
  a value the page never offered is dropped rather than stored.
  A submission goes: no-cors POST to the `site-inquiry-submit` webhook,
  workflow `site-inquiry-ingest` writes a `site_inquiries` row and upserts the
  contact into GHL tagged **`Session Inquiry`**. That tag is the whole
  contract, as `Session Guide - Requested` is for `/contact`, and **nothing in
  GHL is watching it yet** -- until Jessica builds that workflow, inquiries
  are captured and silent. `site_inquiries` holds PII and must never be
  attached to an app, same as `site_leads`.
  **`FORWARD = false` is a decision, not a stub.** One line in the generator
  makes this page behave exactly like `/contact` and hand off to the calendar.
  It does not, because `/contact` collected four fields and owes her nothing,
  while this form asks nine questions including what she is spending -- and
  throwing her at a scheduler mid-thought reads as though nobody was
  listening. The thank-you carries a Book My Call button instead, so the
  calendar is one tap away and is her choice.
  **The acknowledgment checkbox deliberately carries no figure.** Her Session
  Guide PDF and this site's FAQ disagree about the numbers -- the guide says a
  $500 session fee and Collections from $2,800, the FAQ says the session fee
  starts at $697 with Petite Collections from $1,250 -- along with eight other
  conflicts (session length, delivery time, whether the reveal is in person or
  over Zoom, when the Collection is bought, the booking window, studio hours).
  Both are Jessica's, one of them is stale, and it is hers to settle. The
  checkbox states only the structure both versions agree on: images are
  purchased separately from the session fee.
  The closing band hands the undecided woman to `/contact` rather than
  repeating the VIP group, because a woman who opened the inquiry form and
  found she was not ready should meet the guide, not a Facebook link.
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
  it every time. The gallery template has no fence, so its pages render
  at the template's own size.
- **The repo copy and the live template are not byte-identical, and two
  files differ by more than whitespace.** Patches are cut by diffing the
  working file against `git show HEAD:`, so the two have to agree *in the
  region being patched* -- not everywhere. Known gaps, all checked on
  24 September and all harmless:
  - `scalogy-faq.html` and `scalogy-portfolio.html` are 1 byte larger
    locally. Scalogy trims trailing whitespace on save.
  - `scalogy-about.html` is 24 bytes smaller locally.
  - `scalogy-home.html` is **2,253 bytes larger locally**: the repo copy
    carries the section comments (`/* ---------- 2 · hero ---------- */`,
    the `<!-- ===== 7 · email opt-in ===== -->` markers, the file header)
    and three rule-sets that nothing on the page uses -- `.jhp-empower`,
    `.jhp-band` and `.jhp-ba`. Dead CSS; the live page is not missing
    anything it renders. (`.jhp-empower-sub` is the one that *is* used,
    and it is live.)

  The failure mode here is loud, not silent: `templates_patch` requires
  each search to match exactly once and applies nothing if one does not,
  so a search string that strays into one of those comment blocks errors
  rather than landing in the wrong place. Do not "fix" the gap by pushing
  comments live unless there is another reason to touch those files.
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
