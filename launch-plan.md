# Getting the new site onto jhpboudoir.com

**Status: route decided, the bundle is built and checked, and nothing on the
live domain has been touched.** Everything below the line marked YOUR PART is
waiting on you, and none of it is irreversible until the very last step.

---

## Where this landed

You asked for links that read `www.jhpboudoir.com/about`, `/experience`,
`/contact`, and for the Squarespace steps to make it live. Four things I found
before touching anything changed the shape of it, and they are why this is a
hosting decision rather than a link edit.

### 1. Scalogy cannot serve `/about` under your domain. I tested it.

A Scalogy custom domain points at **one page**, not a tenant -- their own docs
say so outright. There was one way round it on paper: a page is a directory, so
one page could in principle hold `about/index.html` and the rest. It is not
reachable from our side:

    /opt/scalogy/data/tenants/jhpboudoir1/web/  ->  PermissionError

That directory belongs to the platform. So `jhpboudoir.com` on Scalogy can
serve exactly one of your twenty pages.

### 2. Your canonical domain is the BARE domain, not `www`.

    www.jhpboudoir.com  ->  301 redirect  ->  jhpboudoir.com
    <link rel="canonical" href="https://jhpboudoir.com">

Google has you indexed as `jhpboudoir.com`. **So the links read
`jhpboudoir.com/about`** -- shorter, already canonical, already indexed, and
`www` keeps redirecting to it exactly as it does now. That is what is built. If
you would rather lead with `www` it is one flag and I will rebuild; it just
costs you the ranking churn of flipping which one is canonical, for nothing.

### 3. It is not Squarespace serving the site. It is Showit on WP Engine.

    jhpboudoir.com  ->  Showit design + WordPress at WP Engine, behind Cloudflare

Squarespace is where the **domain** lives -- the Google Domains move put it
there -- so that is the panel the DNS change happens in and your instinct was
right. But the thing the domain points at today is Showit, and **the moment DNS
moves, all of the old site goes dark at once.** Not page by page.

### 4. You have a live blog, and it is what decided the route.

`jhpboudoir.com/blog/` is a real WordPress install. The new site has no blog.
You told me it is fewer than ten posts, not optimised, and not bringing you
enquiries -- which settles it, because the only route that keeps the blog
exactly where it is would have meant moving your **nameservers**, and that
means recreating every DNS record on the domain including your **MX**. Get
those wrong and your email stops. That was the one genuinely frightening step
in the whole plan, and a blog worth nothing is not a reason to take it.

---

## The route: publish the static pages, leave DNS almost alone

The public site is twenty static HTML files. There is no server behind it: the
two forms POST across to Scalogy webhooks, the calendar is GoHighLevel's, and
every photograph comes off the CDN. So it can be published to a host that
serves directories -- **Netlify**, on the free tier, with SSL included.

What that buys, and what it costs:

- `jhpboudoir.com/about`, `/contact`, `/experience` and the twelve galleries,
  which is what you asked for.
- **Two DNS records change and nothing else.** Your MX records, your
  `treehouse.`, `reveal.`, `boudoirgiveaway.` and the other subdomains are
  never touched. That matters more than it sounds: you have nine subdomains
  pointed at Scalogy pages already.
- Scalogy stays where the site is built and edited. Nothing about the way we
  work on it changes.
- The blog needs somewhere to live -- `blog.jhpboudoir.com` -- and its post
  URLs change once. On fewer than ten unoptimised posts that costs close to
  nothing, and the script redirects `/blog/*` there the moment it exists.

I looked at Cloudflare Pages too and ruled it out: a custom domain on the apex
needs the zone on Cloudflare's own nameservers, which is the exact move we are
avoiding.

---

## What is built and committed

    deploy-site.py     assembles public/ from the repo and applies the launch
                       changes -- SITE, the noindex tag, the wordmark link,
                       Specialty Sessions, the dead /blog link
    netlify.toml       how the host builds it. THE LAUNCH SWITCH IS ONE FLAG
                       ON ONE LINE IN HERE.
    requirements.txt   Jinja2, which is all the build needs

**The launch changes are made on the way out, not in the repo.** Every
`scalogy-*.html` stays byte-identical to its live Scalogy template, because
that is how patches are cut; editing `SITE` and the robots tag into the files
themselves would break that the day before launch, for a change that has to be
reversible in a moment. So `deploy-site.py --preview` builds the bundle with
the preview URLs and the noindex tag still on, and dropping `--preview` is the
launch. Both states are one commit apart and visible in the diff.

**It refuses to publish a bundle it cannot vouch for.** Every check in it is
either something that has already gone wrong on this project or something that
would ship silently:

    20 pages, one h1 each, the phone drawer present on every one
    the header nav AND the footer identical across all twenty, byte for byte
    every internal link resolves to a file that is actually in the bundle
    every canonical tag matches the page it is on
    no pages.scalogy.com, no noindex, no /blog, no ../ left anywhere
    no link out to a host that is not on a known list
    no gallery published empty -- which looks identical to a full one
    the eight page files changed by nothing but their Jinja fence

I ran it, then deliberately broke eight things in the output -- a link to a
page that does not exist, a lost `h1`, the noindex tag back, a renamed phone
drawer, a canonical left on the preview domain, a link left relative -- and it
caught all eight. Then I loaded all twenty pages in a real browser at 1440,
390 and 320: **no horizontal scroll anywhere, one `h1` and one nav per page, no
JavaScript errors.**

---

## YOUR PART, in order

Nothing before step 5 changes anything anybody can see.

**1. Send me the DNS screenshot first.** Squarespace -> Domains ->
`jhpboudoir.com` -> DNS. Every record, including the ones below the fold. This
is the safety net for your email and your nine subdomains and I do not want to
do step 5 without it. It costs you two minutes and it is the only thing in here
that protects you if something goes wrong.

**2. Make a free Netlify account** at netlify.com. Sign in with GitHub, which
saves a step later.

**3. Connect this repository.** Add new site -> Import an existing project ->
GitHub -> this repo -> branch `claude/website-revamp-g9od7u`. It will read
`netlify.toml` and fill the build command and publish directory in by itself --
you should see `python3 deploy-site.py --preview` and `public`. Deploy.

**4. Send me the address it gives you** (something like
`fanciful-name-123.netlify.app`) **and click round it yourself.** This is the
whole site, on a real host, before your domain is involved. Check it on your
phone. It is still `noindex` at this point, so Google will not touch it.

**5. Then, and only then, the domain.** In Netlify: Domain settings -> Add a
domain -> `jhpboudoir.com`. It will tell you it is registered elsewhere and
**print the exact records to create.** Send me that screen. I am not going to
quote you an IP address from memory for the step that takes your website down
if it is wrong -- I will read theirs and check it against what you are about to
save. Then, in Squarespace -> Domains -> `jhpboudoir.com` -> DNS, you change:

| Type | Host | What it becomes |
| --- | --- | --- |
| A | `@` | the IP Netlify shows you |
| CNAME | `www` | the target Netlify shows you |

**Leave every other record alone.** Your MX records in particular do not move.

Propagation takes anywhere from a few minutes to a couple of hours, and SSL is
automatic once it sees the records.

**6. Tell me when it resolves, and I switch indexing on.** That is one commit
removing `--preview`. It is deliberately not automatic, because there is no
undoing a Google index in a hurry.

---

## What I still need from you, separately

1. **The old Showit URL list.** Showit or WP Engine can export it. Every old URL
   that is not also a page in the new bundle will 404 the moment DNS moves,
   which loses whatever links and search results point at it. I can redirect
   them all, but not to addresses I am guessing at.
2. **Where the blog goes.** Simplest is to ask WP Engine to serve it at
   `blog.jhpboudoir.com` -- then it is one CNAME and the script redirects
   `/blog/*` to it. Or export the posts and let it go, which on fewer than ten
   is a defensible choice.
3. **`jhpboudoir.com` or `www.`** -- confirm the first, or say the word.

---

## What launch does NOT fix, so it is not a surprise afterwards

These are already in `CLAUDE.md`; this is the short version, worst first.

1. **Your Google Business Profile carries about a third of local ranking on its
   own**, more than everything on the site put together, and it is not in this
   repo. The primary category is the single biggest thing in it. Launching
   changes nothing about that.
2. **165 gallery photographs share one alt string**, word for word -- useless
   to Google Images and to a screen reader alike.
3. **No `srcset`.** Full 1600px frames are sent to 390px phones. That is the
   page-speed problem on this site and it is worth more after launch than it is
   now.
4. **The name is inconsistent.** The About page's `h1` says "Jessica Paul"; its
   title, its description and all six alt texts say "Jessica Haslag". Search
   engines treat a person as an entity. That one is yours to settle.
5. **There is still no 404 page of your own.** An old URL that I have not been
   given a redirect for lands on Netlify's grey default rather than on your
   site with your nav on it. Worth building, and it is a new page, so it is a
   design decision rather than something to slip in.
6. **The Session Guide PDF is still going out.** The GoHighLevel workflow on
   the `Session Guide - Requested` tag still attaches the old Canva magazine,
   which quotes a $500 session fee and Collections from $2,800 -- $197 and
   $1,550 under what the site says. Nothing in this repo can stop it. That one
   is costing you money today and has nothing to do with launch.
