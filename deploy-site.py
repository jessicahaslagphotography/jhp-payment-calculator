#!/usr/bin/env python3
"""Assemble the public site as static files, ready for a host that serves paths.

WHY THIS EXISTS. Scalogy binds a custom domain to ONE page, so jhpboudoir.com
cannot serve /about, /contact and the twelve galleries from the tenant. The
public site is twenty static HTML files with no server behind them -- the two
forms POST cross-origin to Scalogy webhooks and the calendar is GHL's -- so it
can be published anywhere that serves a directory. This script builds that
directory out of the repo's own built pages, so Scalogy stays where the site is
AUTHORED and nothing here is a second copy of the copy.

    python3 deploy-site.py                     build public/ for jhpboudoir.com
    python3 deploy-site.py --preview           build it unchanged, noindex kept
    python3 deploy-site.py --site https://x    somewhere else
    python3 deploy-site.py --blog-url https://blog.jhpboudoir.com/

THE LAUNCH CHANGES ARE MADE HERE AND NOT IN THE REPO, deliberately. Every
scalogy-*.html is kept byte-identical (bar the known gaps in CLAUDE.md) to the
live Scalogy template, and patches are cut by diffing against git. Editing SITE
and the noindex tag in the files themselves would break that the day before
launch, for a change that has to be reversible on a moment's notice. So the
launch state is a transform applied on the way out, the repo stays the preview,
and --preview proves the bundle is the same pages before any of it is switched.

WHAT IT CHANGES, and why each one is a launch decision rather than a tidy-up:

  SITE          pages.scalogy.com/jhpboudoir1 -> the real domain. Feeds every
                canonical, og:url and the home page's business schema @id.
  robots        noindex,nofollow -> index,follow. CLAUDE.md: this comes off as
                ONE deliberate step at launch, with Jessica's say-so, never as
                a side effect. --preview is how you build without it.
  the wordmark  ../home-preview/ -> /
  treehouse     ../treehouse-sessions/ -> https://treehouse.jhpboudoir.com/,
                which is her own live custom domain for that page. The page
                stays on Scalogy; it is not in this repo and is not in here.
  /blog         dead in all nine footers and 404s. Dropped, unless --blog-url
                says where the blog now lives.
  ../x/         -> /x/. The bundle is flat, one segment per page, so ../x/
                would already resolve -- but a root-relative href cannot be
                wrong, and a browser clamping ../ at the root is behaviour to
                rely on rather than a thing to need.

It refuses to write a bundle it cannot vouch for. Every check at the foot is
something that has gone wrong on this project or would be invisible if it did:
a page that lost its nav, a link to a page that is not in the bundle, a
pages.scalogy.com URL left in a canonical tag, a gallery published empty.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'public'
SRC_SITE = 'https://pages.scalogy.com/jhpboudoir1'
TREEHOUSE = 'https://treehouse.jhpboudoir.com/'

# source file -> path in the bundle. ONE SEGMENT EACH, which is what keeps every
# ../x/ link in the markup resolving to the right place.
PAGES = [
    ('scalogy-home.html',       '',            'home-preview', 1.0),
    ('scalogy-about.html',      'about',       'about',        0.8),
    ('scalogy-portfolio.html',  'portfolio',   'portfolio',    0.9),
    ('scalogy-experience.html', 'experience',  'experience',   0.8),
    ('scalogy-faq.html',        'faq',         'faq',          0.8),
    ('scalogy-contact.html',    'contact',     'contact',      0.9),
    ('scalogy-inquire.html',    'inquire',     'inquire',      0.6),
    ('scalogy-guide.html',      'session-guide', 'session-guide', 0.7),
    # Same path the old Showit site serves, deliberately: every existing link
    # to it keeps working and it needs no redirect.
    ('scalogy-privacy.html',    'privacy-policy', 'privacy-policy', 0.2),
]
GALLERY_TPL = 'scalogy-gallery.html'
GALLERY_PRIORITY = 0.5

# Hosts the site is allowed to link out to. An href to anywhere else is a typo
# or something that wandered in, and is worth failing on rather than shipping.
EXTERNAL_OK = {
    'treehouse.jhpboudoir.com',       # her Treehouse Specialty Sessions page
    'assets.cdn.filesafe.space',      # every photograph
    'fonts.googleapis.com', 'fonts.gstatic.com',
    'api.leadconnectorhq.com',        # the consultation calendar
    'app.scalogy.com',                # the two form webhooks
    'www.instagram.com', 'www.tiktok.com', 'www.facebook.com',
    'www.google.com',                 # her Google reviews
    'schema.org',
}

ROBOTS_OFF = '<meta name="robots" content="noindex, nofollow">'
ROBOTS_ON = '<meta name="robots" content="index, follow, max-image-preview:large">'

fails = []
notes = []


def fail(msg):
    fails.append(msg)


def render_jinja(path, ctx=None):
    """Render a repo page the way Scalogy does, so the fence comes off the same.

    The eight page files wrap their body in {% raw %} because the CSS and the
    inline JS are full of braces; the twelve galleries are real Jinja. Putting
    both through the same renderer means the static bundle cannot differ from
    the live page by the way it was produced.
    """
    from jinja2 import Environment, FileSystemLoader, StrictUndefined
    env = Environment(loader=FileSystemLoader(str(ROOT)), undefined=StrictUndefined,
                      keep_trailing_newline=True, autoescape=False)
    return env.get_template(path).render(**(ctx or {}))


def transform(html, site, page_dir, blog_url, launch):
    """Apply the launch changes. Order matters in three places, marked."""
    # home-preview BEFORE the generic SITE swap, or the home page's canonical
    # comes out as <site>/home-preview/ and competes with <site>/ itself.
    html = html.replace(SRC_SITE + '/home-preview/', site + '/')
    html = html.replace(SRC_SITE + '/', site + '/')
    html = html.replace(SRC_SITE, site)

    # ..and the relative wordmark before the blanket href="../" rewrite below.
    html = html.replace('href="../home-preview/"', 'href="/"')
    html = html.replace('href="../treehouse-sessions/"', 'href="%s"' % TREEHOUSE)

    if blog_url:
        html = html.replace('href="/blog"', 'href="%s"' % blog_url)
    else:
        # The whole row, not just the href: a footer column with an <li> that
        # goes nowhere is worse than a column with one fewer link.
        html = re.sub(r'\s*<li><a href="/blog">Blog</a></li>', '', html)

    html = html.replace('href="../', 'href="/').replace('src="../', 'src="/')

    if launch:
        if ROBOTS_OFF not in html:
            fail('%s: no noindex tag to switch off -- has the head changed?'
                 % (page_dir or '/'))
        html = html.replace(ROBOTS_OFF, ROBOTS_ON)
    return html


# What each page IS, in schema.org's vocabulary, and what a visitor would
# call it in a breadcrumb. Anything not listed is a plain WebPage.
SCHEMA = {
    '':               ('WebSite',      'Home'),
    'about':          ('AboutPage',    'About'),
    'portfolio':      ('CollectionPage', 'Portfolio'),
    'experience':     ('WebPage',      'The Experience'),
    'faq':            (None,           'FAQ'),   # already has FAQPage, derived
    'contact':        ('ContactPage',  'Book a Call'),
    'inquire':        ('ContactPage',  'Inquire'),
    'session-guide':  ('Article',      'The Session Guide'),
    'privacy-policy': ('WebPage',      'Privacy Policy'),
}


def _meta(html, name=None, prop=None):
    pat = (r'<meta name="%s" content="([^"]*)"' % name if name
           else r'<meta property="%s" content="([^"]*)"' % prop)
    m = re.search(pat, html)
    return html_unescape(m.group(1)) if m else None


def html_unescape(s):
    import html as _h
    return _h.unescape(s)


def structured_data(html, site, page_dir, ctx=None):
    """Build the JSON-LD for one page FROM THAT PAGE.

    Derived, never written twice -- the same rule the FAQ's FAQPage already
    follows. Title, description, canonical and share image are read back out
    of the head that was just built, so a copy change moves the markup Google
    reads in the same pass and the two cannot disagree.

    Nineteen of the twenty-one pages carried nothing at all before this. The
    two that did are left alone: the home page's ProfessionalService block is
    hand-written in scalogy-home.html and holds her NAP, and the FAQ's
    FAQPage is parsed out of its own accordion by build-info.py. Adding a
    second description of the same business on the same page would be two
    things to keep true, which is the failure this whole project is arranged
    against.

    Everything here points at that one business node by @id, so the graph has
    a single publisher rather than twenty-one copies of her details.
    """
    kind, label = SCHEMA.get(page_dir, ('WebPage', page_dir))
    if ctx:                       # a client gallery
        kind, label = 'ImageGallery', ctx['name']
    if kind is None and not ctx:
        kind = None

    url = site + '/' + (page_dir + '/' if page_dir else '')
    biz = site + '/#business'
    title = _meta(html, prop='og:title') or ''
    desc = _meta(html, name='description') or ''
    img = _meta(html, prop='og:image')

    graph = []

    # The trail. Home is not a breadcrumb of itself.
    if page_dir:
        trail = [('Home', site + '/')]
        if ctx:
            trail.append(('Portfolio', site + '/portfolio/'))
        trail.append((label, url))
        graph.append({
            '@type': 'BreadcrumbList',
            '@id': url + '#breadcrumb',
            'itemListElement': [
                {'@type': 'ListItem', 'position': i, 'name': n, 'item': u}
                for i, (n, u) in enumerate(trail, 1)],
        })

    if kind:
        node = {
            '@type': kind,
            '@id': url + '#page',
            'url': url,
            'name': title,
            'isPartOf': {'@id': site + '/#website'},
            'publisher': {'@id': biz},
        }
        if desc:
            node['description'] = desc
        if img:
            node['primaryImageOfPage'] = {'@type': 'ImageObject', 'url': img}
        if page_dir:
            node['breadcrumb'] = {'@id': url + '#breadcrumb'}
        if kind == 'WebSite':
            node['@id'] = site + '/#website'
            node['name'] = 'JHP Boudoir'
            node.pop('isPartOf', None)
            node.pop('breadcrumb', None)
        if kind == 'Article':
            node['headline'] = title[:110]
            node['author'] = {'@id': biz}
            node['image'] = img

        # A gallery lists what is in it. This is the one place the 165
        # photographs get described to Google individually, and it is only
        # worth anything once they have alt text worth reading -- see the
        # note in CLAUDE.md. The structure goes in now so that the day the
        # alt text improves, the markup improves with it.
        if ctx:
            photos = [p for row in ctx['rows'] for p in row]
            node['numberOfItems'] = len(photos)
            node['associatedMedia'] = [{
                '@type': 'ImageObject',
                'contentUrl': ctx['cdn'] + p['file'],
                'width': p.get('w'),
                'height': p.get('h'),
                'caption': p.get('alt'),
            } for p in photos]
        graph.append(node)

    if not graph:
        return ''
    blob = json.dumps({'@context': 'https://schema.org', '@graph': graph},
                      indent=1, ensure_ascii=False)
    return '<script type="application/ld+json">\n%s\n</script>\n' % blob


def inject_schema(html, site, page_dir, ctx=None):
    block = structured_data(html, site, page_dir, ctx)
    if not block:
        return html
    assert '</head>' in html, 'no </head> to put the structured data before'
    return html.replace('</head>', block + '</head>', 1)


# RESPONSIVE IMAGES
# -----------------
# Every photograph is served from GoHighLevel's CDN, which ignores resize
# parameters -- ?width=600 and the bare URL return the same 689,704 bytes
# with the same etag, checked 26 September. So a 1600px frame went to a
# 390px phone and there was no way to ask for less. That was the page-speed
# problem on this site and it is the one thing here a visitor can feel.
#
# Netlify's image CDN resizes the remote original instead. Measured on one
# of the portfolio frames:
#
#       original                689,704 bytes
#       /.netlify/images w=400   38,561 bytes    -94%
#       ... w=1200 as AVIF      103,271 bytes    -85%
#
# No `fm` is set on purpose: Netlify negotiates the format from the
# browser's Accept header, so a modern browser gets AVIF or WebP and an old
# one still gets the JPEG, without a <picture> element and two code paths.
#
# THE HOST MUST BE IN netlify.toml's [images] remote_images OR EVERY
# PHOTOGRAPH ON THE SITE 404s. It is; do not remove it.
WIDTHS = [400, 640, 900, 1200, 1600]

# THE REAL PIXEL SIZE OF EVERY FRAME THAT DOES NOT DECLARE ONE.
# Measured on 26 September by Range-requesting each file's header off the CDN
# and reading the JPEG SOF marker or the PNG IHDR -- a few hundred KB rather
# than fifteen megabytes, and exact rather than assumed.
#
# It is worth having twice over. An <img> with no width and height gives the
# browser nothing to reserve, so the page reflows as each photograph lands,
# which is Cumulative Layout Shift and Google measures it. And the srcset
# below caps at the declared width, so an undeclared image was being offered
# every step up to 1600 and Netlify asked to UPSCALE anything smaller.
#
# TWO OF THEM ARE STRAIGHT OFF HER CAMERA at 6048x4024 and 4024x6048, which
# is why this mattered: those were going out whole.
DIMS = json.loads((ROOT / 'image-dimensions.json').read_text())

# What share of the viewport each kind of frame actually occupies, so the
# browser asks for the right one. Wrong `sizes` is worse than none: too
# small and it fetches a blurry frame, too large and the whole exercise was
# pointless. Keyed on the nearest container class above the <img>.
SIZES = {
    'jhp-gal':   '(max-width:620px) 50vw, (max-width:1200px) 33vw, 370px',
    'jhp-set':   '(max-width:620px) 100vw, (max-width:900px) 50vw, 33vw',
    'jhp-pair':  '(max-width:700px) 100vw, 33vw',
    'shot':      '(max-width:820px) 100vw, 45vw',
    'logo-mark': '176px',
}
DEFAULT_SIZES = '100vw'


def _resized(src, w):
    from urllib.parse import quote
    return '/.netlify/images?url=%s&w=%d&q=72' % (quote(src, safe=''), w)


def responsive(html):
    """Rewrite every CDN <img> into a srcset. Returns (html, count)."""
    out, n = [], 0
    # Everything after the last </style> is markup. Class names before that
    # point are CSS selectors and must not be mistaken for containers.
    markup_at = html.rfind('</style>')
    markup_at = 0 if markup_at < 0 else markup_at
    for m in re.finditer(r'<img\b[^>]*>', html):
        tag = m.group(0)
        src = re.search(r'\bsrc="(https://assets\.cdn\.filesafe\.space/[^"]+)"', tag)
        if not src or 'srcset=' in tag:
            continue
        url = src.group(1)

        # Never offer more pixels than the original has. The tag's own
        # width attribute first; failing that, the measured table above.
        nat = re.search(r'\bwidth="(\d+)"', tag)
        nat = int(nat.group(1)) if nat else None
        known = DIMS.get(url.rsplit('/', 1)[-1])
        if nat is None and known:
            nat = known['w']
        widths = [w for w in WIDTHS if not nat or w < nat] + ([nat] if nat and
                                                              nat <= 1600 else [1600])
        widths = sorted(set(w for w in widths if w))

        # The nearest container above this <img> decides `sizes`.
        #
        # THIS LOOKS AT MARKUP ONLY, and the first version did not. Searching
        # the raw page for 'jhp-gal' or 'logo-mark' hits the STYLESHEET,
        # which sits above every <img> on the page -- so the home page's hero
        # came out at sizes="176px", the footer logo's width, and would have
        # been fetched at 176px and drawn across 1440. It matches whole class
        # tokens in a class attribute, in the body, and takes the last one.
        before = html[markup_at:m.start()]
        sizes, at_best = DEFAULT_SIZES, -1
        for attr in re.finditer(r'class="([^"]*)"', before):
            for cls in attr.group(1).split():
                if cls in SIZES and attr.start() > at_best:
                    sizes, at_best = SIZES[cls], attr.start()

        srcset = ', '.join('%s %dw' % (_resized(url, w), w) for w in widths)
        new_tag = tag[:-1].rstrip()
        if known and not re.search(r'\bheight="\d+"', new_tag):
            new_tag = re.sub(r'\s*\bwidth="\d+"', '', new_tag)
            new_tag += ' width="%d" height="%d"' % (known['w'], known['h'])
        if new_tag.endswith('/'):
            new_tag = new_tag[:-1].rstrip()
        new_tag += ' srcset="%s" sizes="%s">' % (srcset, sizes)
        # and point src at a mid-size render rather than the 1600px original
        new_tag = new_tag.replace('src="%s"' % url,
                                  'src="%s"' % _resized(url, min(1200, widths[-1])))
        out.append((m.start(), m.end(), new_tag))
        n += 1

    for start, end, tag in reversed(out):
        html = html[:start] + tag + html[end:]
    return html, n


def write(rel, text):
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')
    return p


def nav_of(html):
    """md5 of the header nav and the footer nav, which every page shares.

    Named by class rather than taken as the first <nav> on the page: a gallery
    carries three (the bar, prev/next, the footer column) and the one CLAUDE.md
    asks to be checked byte-for-byte is .jhp-nav. The footer is in the same
    tuple because a footer edit is three source files, nine templates and
    twenty pages, and a page left behind looks fine on its own.
    """
    out = []
    for cls in ('jhp-nav', 'ftnav'):
        m = re.search(r'<nav class="%s".*?</nav>' % cls, html, re.S)
        out.append(hashlib.md5(m.group(0).encode()).hexdigest() if m else None)
    return tuple(out)


def build(site, blog_url, launch):
    if OUT.exists():
        shutil.rmtree(OUT)
    urls = []
    navs = {}
    shrunk = {}

    for src, d, scalogy_page, prio in PAGES:
        raw = (ROOT / src).read_text(encoding='utf-8')
        rendered = render_jinja(src)
        # The only thing Jinja may do to these eight is take the raw fence off.
        # Anything else means a {{ }} or {% %} has appeared in the head or in
        # the JSON-LD below the fence, where it would be live Jinja on Scalogy
        # too and is a bug there before it is one here.
        # Jinja drops the tag and NOTHING else -- not the newline after it --
        # which is why the rendered page is the template less exactly 21 bytes.
        stripped = re.sub(r'\{%\s*(end)?raw\s*%\}', '', raw)
        if rendered != stripped:
            fail('%s: Jinja changed more than the raw fence -- there is live '
                 'template syntax outside {%% raw %%}' % src)
        html = transform(rendered, site, d, blog_url, launch)
        html = inject_schema(html, site, d)
        html, nimg = responsive(html)
        shrunk[d or '/'] = nimg
        rel = (d + '/index.html') if d else 'index.html'
        write(rel, html)
        urls.append(('/' + (d + '/' if d else ''), prio))
        navs[rel] = nav_of(html)

    payloads = sorted((ROOT / 'renders').glob('*.json'))
    if len(payloads) != 12:
        fail('expected 12 gallery payloads in renders/, found %d' % len(payloads))
    for p in payloads:
        ctx = json.loads(p.read_text(encoding='utf-8'))
        slug = ctx.get('slug')
        if slug != p.stem:
            fail('%s: slug is %r but the file is named %r -- the canonical URL '
                 'comes off the slug' % (p.name, slug, p.stem))
        html = transform(render_jinja(GALLERY_TPL, ctx), site, slug, blog_url, launch)
        html = inject_schema(html, site, slug, ctx)
        html, nimg = responsive(html)
        shrunk[slug] = nimg
        if ctx['name'] not in html:
            fail('%s: rendered without the client name -- an empty gallery '
                 'looks exactly like a full one from the outside' % slug)
        if len(html) < 20000:
            fail('%s: only %d bytes' % (slug, len(html)))
        rel = slug + '/index.html'
        write(rel, html)
        urls.append(('/' + slug + '/', GALLERY_PRIORITY))
        navs[rel] = nav_of(html)

    # All twenty carry the same nav byte for byte. CLAUDE.md asks for this check
    # by hand after a nav change; here it is free on every build.
    missing = [k for k, v in navs.items() if None in v]
    distinct = {v for v in navs.values() if None not in v}
    if missing:
        fail('these pages are missing a header or footer nav: ' + ', '.join(missing))
    elif len(distinct) != 1:
        groups = {}
        for k, v in navs.items():
            groups.setdefault(v, []).append(k)
        fail('the nav or footer is not identical across the bundle -- %d '
             'versions: %s' % (len(distinct),
                               '; '.join('[%s/%s] %s' % (h[0][:6], h[1][:6],
                                                         ', '.join(sorted(f)))
                                         for h, f in groups.items())))

    notes.append('%d of the %d photographs now go through Netlify\'s resizer '
                 'instead of being sent full size.'
                 % (sum(shrunk.values()), sum(shrunk.values())))
    write('_redirects', redirects(blog_url))
    write('sitemap.xml', sitemap(site, urls))
    write('robots.txt',
          'User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n' % site)
    if not launch:
        # A preview bundle must not be indexable even by accident.
        (OUT / 'robots.txt').write_text('User-agent: *\nDisallow: /\n', encoding='utf-8')
    return urls


def redirects(blog_url):
    """Netlify/Cloudflare Pages _redirects, built from the OLD SITE AS CRAWLED.

    Not guessed. On 26 September the live Showit/WordPress site was crawled
    from its own navigation and its WordPress API read; it is eight pages and
    five posts, and every one of them is accounted for below. An old URL that
    404s after the cutover loses whatever links and search results point at
    it, and the only way to know which ones exist is to go and look.

        /                     -> /                     same
        /about                -> /about/               same
        /portfolio            -> /portfolio/           same
        /contact              -> /contact/             same
        /faq                  -> /faq/                 same (not in the old
                                  nav, but live -- found by probing)
        /information          -> /faq/                 RENAMED. Info is a menu
                                  on the new site, not a page; the FAQ is what
                                  that page's content became.
        /specialty-sessions   -> treehouse subdomain   the Treehouse page,
                                  which stays on Scalogy under its own domain
        /privacy-policy       -> /privacy-policy/   SAME PATH, on purpose
        /blog/, /YYYY/MM/DD/  -> --blog-url, when there is one
        /category/*           -> two of them, found by reading the blog index
        /feed/*, /wp-json/*   -> so a feed reader and the API follow too

    The first five need no rule: the bundle has a directory of that name and
    the host resolves it. They are written out here because this list is the
    old site's map and a reader should not have to work out which lines are
    missing on purpose.

    **/privacy-policy IS NOW A REAL PAGE AND KEEPS ITS OLD PATH.** The old
    site's version is a stub whose whole content is "Click here to read our
    privacy policy" over a link to a generated document on privacypolicies.com
    -- one that describes this studio's parent company, affiliates and joint
    venture partners, none of which exist, and says nothing about text
    messages. It is replaced by build-privacy.py, written from what the site
    actually does. Keeping the path means every existing link to it still
    resolves and no rule is needed here at all.
    """
    out = ['# The old Showit site, crawled 26 September 2026. See redirects()',
           '# in deploy-site.py for the full map and for what is missing.',
           '',
           '# Renamed: Info is a menu on the new site, not a page.',
           '/information      /faq/   301',
           '',
           '# The Treehouse page stays on Scalogy, under her own subdomain.',
           '/specialty-sessions   %s   301' % TREEHOUSE,
           '',
           '# Anything bookmarked or texted from the Scalogy preview.',
           '/home-preview/*   /   301!',
           '/home-preview     /   301!']
    if blog_url:
        b = blog_url.rstrip('/')
        out += ['',
                '# The blog and its five posts. The post URLs are date-based at',
                '# the ROOT, not under /blog/, so /blog/* alone would miss',
                '# them -- and there are two category pages besides.',
                '/blog/*      %s/blog/:splat      301' % b,
                '/blog        %s/blog/             301' % b,
                '/2024/*      %s/2024/:splat       301' % b,
                '/2025/*      %s/2025/:splat       301' % b,
                '/category/*  %s/category/:splat   301' % b,
                '/feed/*      %s/feed/:splat       301' % b,
                '/wp-json/*   %s/wp-json/:splat    301' % b]
    else:
        out += ['',
                '# NO --blog-url WAS GIVEN, so the blog and its five posts are',
                '# not redirected anywhere and will 404:',
                '#   /blog/  /2024/02/01/*  /2025/03/*  /2025/04/*',
                '#   /category/empowerment-stories-client-testimonials/',
                '#   /category/tips-tricks/']
    return '\n'.join(out) + '\n'


def sitemap(site, urls):
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, prio in urls:
        out.append('  <url><loc>%s%s</loc><priority>%.1f</priority></url>'
                   % (site, path, prio))
    out.append('</urlset>')
    return '\n'.join(out) + '\n'


def check(site, blog_url, launch):
    """Read the bundle back and refuse to bless it if anything is off.

    Everything here is either a mistake this project has actually made or one
    that would ship silently. The expensive kind is a link to a page that is
    not in the bundle: on Scalogy a bad relative link 404s on a preview URL
    nobody visits, and on the real domain it 404s in front of a client.
    """
    files = sorted(OUT.rglob('*.html'))
    if len(files) != 21:
        fail('the bundle has %d pages, expected 21' % len(files))

    for f in files:
        rel = f.relative_to(OUT)
        html = f.read_text(encoding='utf-8')
        where = '/' + str(rel.parent).replace('.', '').strip('/')

        if 'pages.scalogy.com/jhpboudoir1' in html and launch:
            for m in re.finditer(r'[^\s"\'<>]*pages\.scalogy\.com/jhpboudoir1[^\s"\'<>]*', html):
                fail('%s: still points at the preview: %s' % (where, m.group(0)))
        if launch and 'noindex' in html:
            fail('%s: still carries noindex' % where)
        if 'home-preview' in html:
            fail('%s: home-preview survived somewhere' % where)
        if not blog_url and '/blog' in html:
            fail('%s: a /blog link survived, and /blog 404s' % where)
        for m in re.finditer(r'(?:href|src)="(\.\./[^"]*)"', html):
            fail('%s: relative link %s was not rewritten' % (where, m.group(1)))

        # Structure, checked without a browser. A page that loses its h1 or its
        # phone drawer still renders, still looks finished in a screenshot, and
        # is broken -- and these are the two that a slicing generator can drop.
        h1s = re.findall(r'<h1\b', html)
        if len(h1s) != 1:
            fail('%s: %d h1 elements, expected exactly 1' % (where, len(h1s)))
        if 'class="jhp-navd"' not in html:
            fail('%s: no <details class="jhp-navd"> -- the phone nav is gone' % where)
        # A privacy policy nobody can reach is not a privacy policy. It is
        # linked from the copyright line of all twenty-one footers and that
        # is the only route to it, so losing the link loses the page.
        if 'href="/privacy-policy/"' not in html and where != '/privacy-policy':
            fail('%s: the footer has lost its privacy policy link' % where)

        # Nineteen of twenty-one pages had no structured data before
        # 26 September. Having added it, the build refuses to lose it again.
        blobs = re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                           html, re.S)
        if not blobs:
            fail('%s: no structured data' % where)
        for b in blobs:
            try:
                json.loads(b)
            except Exception as e:
                fail('%s: a JSON-LD block does not parse (%s)' % (where, e))

        canon = re.search(r'<link rel="canonical" href="([^"]+)"', html)
        want = site + '/' + (str(rel.parent) + '/' if str(rel.parent) != '.' else '')
        if not canon:
            fail('%s: no canonical tag' % where)
        elif canon.group(1) != want:
            fail('%s: canonical is %s, expected %s' % (where, canon.group(1), want))

        for attr, url in re.findall(r'(href|src)="([^"]+)"', html):
            if url.startswith(('#', 'mailto:', 'tel:', 'data:', 'javascript:')):
                continue
            # An absolute self-link -- the canonical, og:url, the schema @id --
            # is checked as a path, so a canonical pointing at a page that is
            # not in the bundle is caught rather than waved through as external.
            if url.startswith(site + '/') or url == site:
                url = url[len(site):] or '/'
            if url.startswith('http'):
                host = re.sub(r'^https?://([^/]+).*$', r'\1', url)
                if host not in EXTERNAL_OK and not (
                        blog_url and url.startswith(blog_url)):
                    fail('%s: links to an unexpected host %s (%s)'
                         % (where, host, url))
                continue
            if url.startswith('/.netlify/images?'):
                continue          # served by the host, not a file in the bundle
            if not url.startswith('/'):
                fail('%s: %s="%s" is neither absolute nor rooted' % (where, attr, url))
                continue
            target = url.lstrip('/').split('?')[0].split('#')[0]
            cand = OUT / target
            if cand.is_dir():
                cand = cand / 'index.html'
            elif target.endswith('/') or not target:
                cand = OUT / target / 'index.html'
            if not cand.exists():
                fail('%s: %s points at %s, which is not in the bundle'
                     % (where, url, target or '/'))

    sm = (OUT / 'sitemap.xml').read_text(encoding='utf-8')
    locs = re.findall(r'<loc>([^<]+)</loc>', sm)
    if len(locs) != 21:
        fail('the sitemap lists %d URLs, expected 21' % len(locs))
    for loc in locs:
        p = loc[len(site):].lstrip('/')
        if not (OUT / (p + 'index.html' if p.endswith('/') or not p else p)).exists():
            fail('the sitemap lists %s, which is not in the bundle' % loc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--site', default='https://jhpboudoir.com',
                    help='the domain the bundle will be served from, no trailing slash')
    ap.add_argument('--blog-url', default='',
                    help='where the blog lives now, e.g. https://blog.jhpboudoir.com/ '
                         '(without it the dead /blog link is dropped)')
    ap.add_argument('--preview', action='store_true',
                    help='build the bundle without switching indexing on')
    a = ap.parse_args()
    site = a.site.rstrip('/')
    launch = not a.preview

    if a.preview:
        site = SRC_SITE
        EXTERNAL_OK.add('pages.scalogy.com')
        notes.append('PREVIEW BUILD: SITE is still the Scalogy preview and every '
                     'page keeps noindex. robots.txt disallows everything.')

    urls = build(site, a.blog_url, launch)
    check(site, a.blog_url, launch)

    total = sum(f.stat().st_size for f in OUT.rglob('*') if f.is_file())
    print('%d pages, %s, %.0f KB -> %s'
          % (len(urls), site, total / 1024, OUT.relative_to(ROOT)))
    if not a.blog_url:
        notes.append('The dead /blog link was dropped from every footer in the bundle. '
                     'Pass --blog-url once the blog has somewhere to live.')
    notes.append('The wordmark now points at / and Specialty Sessions at %s '
                 '(her own live custom domain for that page).' % TREEHOUSE)
    for n in notes:
        print('  note: ' + n)
    if fails:
        print('\n%d CHECK(S) FAILED -- do not publish this:' % len(fails),
              file=sys.stderr)
        for f in fails:
            print('  - ' + f, file=sys.stderr)
        raise SystemExit(1)
    print('  all checks passed')


if __name__ == '__main__':
    main()
