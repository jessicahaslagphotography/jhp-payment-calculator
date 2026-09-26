#!/usr/bin/env python3
"""Audit the built site and report what is actually wrong, page by page.

Written because "optimise the site for SEO" is not a task until it is a list,
and a list written from memory is a list of the things somebody happens to
remember. This reads the twenty-one pages the host actually serves and
measures them.

It reports rather than fails: it is a survey, not a build guard. The guards
that must not regress live in deploy-site.py and in the generators.

    python3 seo-audit.py            the whole site
    python3 seo-audit.py --alt      just the alt-text inventory
"""
import collections
import html
import json
import re
import sys
import pathlib

OUT = pathlib.Path(__file__).resolve().parent / 'public'
SITE = 'https://jhpboudoir.com'


def text_of(h):
    b = re.sub(r'<(script|style|svg)\b.*?</\1>', ' ', h, flags=re.S | re.I)
    b = re.sub(r'<[^>]+>', ' ', b)
    return re.sub(r'\s+', ' ', html.unescape(b)).strip()


def audit():
    pages = sorted(OUT.rglob('*.html'))
    rows, alts, all_imgs = [], collections.Counter(), []
    schema_types = collections.Counter()
    issues = collections.defaultdict(list)

    for f in pages:
        rel = str(f.relative_to(OUT).parent)
        url = '/' if rel == '.' else f'/{rel}/'
        h = f.read_text(encoding='utf-8')

        title = (re.search(r'<title>(.*?)</title>', h, re.S) or [None, ''])[1]
        title = html.unescape(re.sub(r'\s+', ' ', title)).strip()
        desc = re.search(r'<meta name="description" content="([^"]*)"', h)
        desc = html.unescape(desc.group(1)) if desc else ''
        h1s = [text_of(m) for m in re.findall(r'<h1\b[^>]*>(.*?)</h1>', h, re.S)]
        h2s = [text_of(m) for m in re.findall(r'<h2\b[^>]*>(.*?)</h2>', h, re.S)]
        h3s = re.findall(r'<h3\b', h)
        words = len(text_of(h).split())

        # Strip scripts and styles before counting images: the Session
        # Guide's name-validation comment contains the literal string
        # "<img src=x onerror=...>" as an example of what it refuses, and
        # counting that as a photograph with no alt text is a false alarm
        # that would send somebody looking for a bug that is not there.
        markup = re.sub(r'<(script|style)\b.*?</\1>', ' ', h, flags=re.S | re.I)
        imgs = re.findall(r'<img\b[^>]*>', markup)
        page_alts, no_dim, lazy = [], 0, 0
        for tag in imgs:
            a = re.search(r'\balt="([^"]*)"', tag)
            a = html.unescape(a.group(1)).strip() if a else None
            page_alts.append(a)
            all_imgs.append((url, a, tag))
            if a is not None:
                alts[a] += 1
            if not (re.search(r'\bwidth=', tag) and re.search(r'\bheight=', tag)):
                no_dim += 1
            if 'loading="lazy"' in tag:
                lazy += 1

        ld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)
        types = []
        for blob in ld:
            try:
                d = json.loads(blob)
            except Exception:
                issues[url].append('a JSON-LD block does not parse')
                continue
            for node in (d.get('@graph') if isinstance(d, dict) and '@graph' in d
                         else [d] if isinstance(d, dict) else d):
                t = node.get('@type') if isinstance(node, dict) else None
                if t:
                    types.append(t if isinstance(t, str) else '/'.join(t))
        for t in types:
            schema_types[t] += 1

        internal = len(set(re.findall(r'href="(/[^"#?]*)"', h)))
        srcset = h.count('srcset=')

        # --- the checks -------------------------------------------------
        if not title:
            issues[url].append('no <title>')
        elif len(title) > 60:
            issues[url].append(f'title is {len(title)} chars, over the ~60 '
                               f'Google shows')
        if not desc:
            issues[url].append('no meta description')
        elif not (120 <= len(desc) <= 165):
            issues[url].append(f'description is {len(desc)} chars, outside 120-165')
        if len(h1s) != 1:
            issues[url].append(f'{len(h1s)} h1 elements')
        if imgs and srcset == 0:
            issues[url].append(f'{len(imgs)} images, no srcset on any of them')
        if no_dim:
            issues[url].append(f'{no_dim} images with no width/height (layout shift)')
        if words < 300:
            issues[url].append(f'only {words} words of text')
        if not types:
            issues[url].append('no structured data at all')

        rows.append(dict(url=url, title=title, tlen=len(title), dlen=len(desc),
                         h1=h1s[0] if h1s else '', nh2=len(h2s), nh3=len(h3s),
                         words=words, imgs=len(imgs), lazy=lazy, nodim=no_dim,
                         srcset=srcset, internal=internal, types=types,
                         kb=len(h.encode()) // 1024))

    return rows, alts, all_imgs, schema_types, issues


def main():
    rows, alts, all_imgs, schema_types, issues = audit()
    only_alt = '--alt' in sys.argv

    if not only_alt:
        print('=' * 78)
        print(f'{"page":26}{"title":>6}{"desc":>6}{"words":>7}{"imgs":>6}'
              f'{"h2":>4}{"h3":>4}{"links":>7}{"KB":>5}')
        print('=' * 78)
        for r in rows:
            print(f'{r["url"]:26}{r["tlen"]:>6}{r["dlen"]:>6}{r["words"]:>7}'
                  f'{r["imgs"]:>6}{r["nh2"]:>4}{r["nh3"]:>4}'
                  f'{r["internal"]:>7}{r["kb"]:>5}')

        print('\nSTRUCTURED DATA across the site')
        for t, n in schema_types.most_common():
            print(f'  {n:>3}  {t}')
        pages_without = [r['url'] for r in rows if not r['types']]
        print(f'  {len(pages_without)} of {len(rows)} pages carry none: '
              + ', '.join(pages_without[:6])
              + (' ...' if len(pages_without) > 6 else ''))

    print(f'\nALT TEXT  {len(all_imgs)} images across {len(rows)} pages')
    missing = [u for u, a, _ in all_imgs if a is None]
    empty = [u for u, a, _ in all_imgs if a == '']
    print(f'  {len(missing)} with no alt attribute at all')
    print(f'  {len(empty)} with alt=""')
    print(f'  {len(alts)} distinct alt strings for '
          f'{sum(alts.values())} images that have one')
    print('\n  most reused:')
    for a, n in alts.most_common(6):
        print(f'    {n:>4}x  {a[:64]}')

    if not only_alt:
        print('\n' + '=' * 78)
        print('ISSUES, page by page')
        print('=' * 78)
        n = 0
        for url in sorted(issues):
            print(f'\n{url}')
            for i in issues[url]:
                print(f'   - {i}')
                n += 1
        print(f'\n{n} issues across {len(issues)} pages')


if __name__ == '__main__':
    main()
