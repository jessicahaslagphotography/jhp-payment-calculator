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

    write('_redirects', redirects(blog_url))
    write('sitemap.xml', sitemap(site, urls))
    write('robots.txt',
          'User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n' % site)
    if not launch:
        # A preview bundle must not be indexable even by accident.
        (OUT / 'robots.txt').write_text('User-agent: *\nDisallow: /\n', encoding='utf-8')
    return urls


def redirects(blog_url):
    """Netlify/Cloudflare Pages _redirects. Only for URLs that already exist.

    The old Showit URLs are NOT in here and cannot be guessed. Getting them
    right needs the list Showit or WP Engine can export; until then any old URL
    that is not also a page in this bundle will 404, which is worth fixing
    before launch rather than after.
    """
    out = ['# Anything bookmarked or texted from the Scalogy preview.',
           '/home-preview/*   /   301!',
           '/home-preview     /   301!']
    if blog_url:
        out += ['', '# The blog, wherever it lives now.',
                '/blog/*   %s:splat   301' % blog_url.rstrip('/'),
                '/blog     %s   301' % blog_url]
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
    if len(files) != 20:
        fail('the bundle has %d pages, expected 20' % len(files))

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
    if len(locs) != 20:
        fail('the sitemap lists %d URLs, expected 20' % len(locs))
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
        notes.append('The dead /blog link was dropped from all nine footers. '
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
