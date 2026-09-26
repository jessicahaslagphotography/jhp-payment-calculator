# Getting the new site onto jhpboudoir.com

**Status: DECISION NEEDED. Nothing has been changed.**

You asked for links that read `www.jhpboudoir.com/about`, `/experience`,
`/contact`, and for the Squarespace steps to make it live. Before touching DNS
I checked what is actually running today and what Scalogy can actually serve.
Four things came back that change the shape of this, so they are first.

---

## What I found

### 1. Scalogy cannot serve `/about` under your domain. I tested it.

Scalogy binds a custom domain to **one page**, not to your whole site — their
own documentation says so outright: *"A custom domain points at a single page,
not your whole tenant."*

There was one possible way round it. The same docs say a page is a *directory*
and that subdirectories keep their paths, so in principle one page could hold
`about/index.html`, `contact/index.html` and so on, and the whole site would
sit under one domain with clean URLs.

I tested whether that is reachable from our side. It is not:

    /opt/scalogy/data/tenants/jhpboudoir1/web/  ->  PermissionError

That directory belongs to the platform, not to the tenant. So **as things
stand, `jhpboudoir.com` can serve exactly one of your twenty pages.** Your
request is not a link edit — it needs a hosting decision.

### 2. Your canonical domain is the BARE domain, not `www`.

    www.jhpboudoir.com  ->  301 redirect  ->  jhpboudoir.com
    <link rel="canonical" href="https://jhpboudoir.com">

Google has indexed you as `jhpboudoir.com`. If we publish links as
`www.jhpboudoir.com/about` we are pointing at a redirect, and flipping which
one is canonical churns the ranking you already have for no gain.

**Recommendation: links read `jhpboudoir.com/about`** — shorter, already
canonical, already indexed. `www` keeps redirecting to it exactly as now.
Say the word if you would rather have `www` and I will flip it instead.

### 3. It is not Squarespace serving the site. It is Showit on WP Engine.

    jhpboudoir.com  ->  Showit design + WordPress, hosted at WP Engine,
                        behind Cloudflare

Squarespace is almost certainly where the **domain** lives — Google Domains
customers were moved to Squarespace, and that is the panel you log into. That
is where the DNS change happens, so your instinct was right. But the thing the
domain currently points at is Showit/WP Engine, and **the moment DNS moves, the
whole of the old site goes dark.** Not page by page. All at once.

### 4. YOU HAVE A LIVE BLOG, and it is the reason this needs a real decision.

    jhpboudoir.com/blog/  ->  200, live WordPress

It is a real WordPress install (`/wp-json/`, `/wp-admin/`) behind the Showit
design. The new site has no blog and `/blog` 404s on it.

Pointing the domain at the new site therefore **takes your blog offline and
breaks every post URL**, along with whatever search traffic and backlinks they
carry. `CLAUDE.md` already notes that for a local studio a blog is the single
biggest organic lever there is. Losing the one you have to launch the new site
is a bad trade made by accident.

This is the constraint that decides the route, because only one of the options
below can keep `/blog` where it is.

---

## The three routes

### A. Cloudflare in front of the domain  — *keeps the blog*

Cloudflare sits in front of `jhpboudoir.com` and routes by path:

    /blog/*     ->  WP Engine   (your blog, untouched)
    everything  ->  pages.scalogy.com/jhpboudoir1/...

- **Gives you exactly what you asked for**: `jhpboudoir.com/about`.
- **The only route that keeps the blog at `/blog`.**
- Free tier is ample. Done with Cloudflare Rules, no code.
- Relative links on the site (`../about/`) keep working, because the path depth
  is unchanged — one segment either way.
- **The cost: your DNS nameservers move from Squarespace to Cloudflare**, which
  means every existing record has to be recreated there. That includes your
  **MX records — get those wrong and your email stops** — plus
  `treehouse.`, `reveal.`, `boudoirgiveaway.` and anything else on the domain.
  Recoverable, but it is the one step in this whole plan that can break
  something that has nothing to do with the website.

### B. Ask Scalogy to bind the domain at tenant level  — *cleanest, no ETA*

`jhpboudoir.com/about/` → `jhpboudoir1/about/`, served by them. For Scalogy
this is a small change to how their edge maps a domain; for you it is zero
infrastructure and nothing new to maintain.

- Cleanest long-term answer, and keeps everything in one system.
- **Does not solve the blog** — that still needs route A's path split or a move.
- **No timeline.** It depends on them saying yes. Worth asking either way; I can
  draft the request.

### C. Publish the static pages to a host that does paths  — *lowest risk*

The public site is twenty static HTML files. Cloudflare Pages or Netlify serve
`/about/` natively, free, with SSL, and take **A/CNAME records from Squarespace
— no nameserver move**, so your email and subdomains are never touched.

- Gives you `jhpboudoir.com/about`.
- Lowest-risk DNS change of the three.
- The blog moves to `blog.jhpboudoir.com` with `/blog/*` redirected to it. You
  keep the posts; the URLs change once, which costs some ranking.
- Adds a publish step: Scalogy stays where the site is built, and a deploy
  pushes the rendered pages to the static host. I would build and test that.

### My recommendation

**Route A**, because your blog is worth more than the convenience of the other
two, and A is the only one that leaves it exactly where Google already has it.

Ask Scalogy for B in parallel — if they do it, A gets simpler (Cloudflare then
only needs the `/blog` rule).

**What would change my mind:** if the blog has only a handful of posts and
little traffic, route C is clearly better — no nameserver move means no chance
of breaking your email, which is the only genuinely scary step here. That is
your call because you know what the blog is worth. **Tell me roughly how many
posts there are and whether any of them bring you enquiries**, and I will tell
you which way I would go.

---

## What you would change in Squarespace

### If route A (Cloudflare)

1. **First, inventory.** In Squarespace → Domains → `jhpboudoir.com` → DNS,
   screenshot **every** record. Send it to me. This is the safety net for your
   email and subdomains and I do not want to do the next step without it.
2. Create a free Cloudflare account and add `jhpboudoir.com`. Cloudflare imports
   the records it can see — **verify them against your screenshot**, especially
   MX.
3. Cloudflare gives you two nameservers. In Squarespace → Domains →
   `jhpboudoir.com` → **Nameservers**, switch from Squarespace's to those two.
4. Tell me when it has propagated. I will set the routing rules and bind the
   pages.

### If route C (static host)

Two records, and nothing else on the domain is touched:

| Type | Host | Value |
| --- | --- | --- |
| A | `@` | *(the host's IP — I will give you the exact value)* |
| CNAME | `www` | *(the host's target)* |

### If route B alone (Scalogy, home page only)

This is what Scalogy supports *today* without a proxy, and it only gets you the
home page at the domain:

| Type | Host | Value |
| --- | --- | --- |
| A | `@` | `178.105.37.93` |
| CNAME | `www` | `edge.scalogy.com` |

I would not launch on this — every other page would still read
`pages.scalogy.com/jhpboudoir1/...`, which is the problem you asked me to fix.

---

## What I do on the site, whichever route

None of this is done yet; it all waits on the route, because most of it needs
the final URL shape.

1. **`SITE` changes from `https://pages.scalogy.com/jhpboudoir1` to
   `https://jhpboudoir.com`** — three HTML files and four generators. It feeds
   every canonical tag and `og:url`.
2. **The `noindex, nofollow` comes off.** Deliberately switched on so the
   preview could not compete with the live site in Google; it comes off as one
   step, at launch, with your say-so. Every other SEO signal is already built
   and waiting, so it all counts from day one.
3. **The JHP wordmark link** goes from `../home-preview/` to `/`.
4. **Specialty Sessions in the footer** — currently relative to the Treehouse
   page. Decide with the wordmark whether it stays a path or becomes
   `treehouse.jhpboudoir.com`.
5. **`sitemap.xml` and `robots.txt`** — both need the real domain and cannot be
   written until it is bound.
6. **Redirects from the old Showit URLs** to the new equivalents, so existing
   links and search results do not land on 404s. I need the old URL list for
   this; Showit or WP Engine can export it.
7. **Update the links we send** — the Session Guide and the calendar URLs in
   the follow-up emails currently point at `pages.scalogy.com`. They keep
   working, but they should read as hers.

---

## What I need from you

1. **Route A, B or C** — and the blog answer above if you want me to decide.
2. **`jhpboudoir.com/about` or `www.jhpboudoir.com/about`.** I recommend the
   first; your site is already canonically non-www.
3. **The DNS screenshot** from Squarespace, before anything changes.
