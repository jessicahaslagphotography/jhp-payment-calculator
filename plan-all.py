#!/usr/bin/env python3
"""Plans every gallery's rows and writes the render payloads.

Miss T is nine wide frames and nothing tall, which the planner cannot make
interesting on its own -- with one shape available every row of the same
length is the same height. Those galleries get their variety from row
LENGTH instead: a lone banner against a run of three.
"""
import json, pathlib, re

CDN = "https://assets.cdn.filesafe.space/Pcnm8GVNMmWTY65qVOAp/media/"

# REAL ALT TEXT, ONE STRING PER PHOTOGRAPH.
# All 165 frames used to share this line, word for word:
#
#     "Boudoir portrait from a session at JHP Boudoir"
#
# Honest, and useless -- to Google Images and to a screen reader alike. It was
# the third item on CLAUDE.md's SEO list and the only one nobody could do from
# the build sandbox, because the image CDN is unreachable from here and a
# photograph cannot be described unseen.
#
# gallery-alt-text.json is that description, keyed by filename: written on
# 26 September by putting every frame through Claude's vision API from a
# Scalogy workflow, which CAN reach the CDN. Jessica cleared it -- her clients
# sign a full model release covering marketing use, and these are her own
# published photographs and her own API key. $2.43 for all 165.
#
# THE FALLBACK IS STILL HERE AND IS DELIBERATE. A frame added to
# galleries.json tomorrow has no entry yet, and a missing description must not
# stop the site building -- it gets the old generic line and shows up in the
# count this script prints, which is how anybody notices.
ALT = "Boudoir portrait from a session at JHP Boudoir"
ALT_TEXT = json.loads(pathlib.Path("gallery-alt-text.json").read_text())
WIDTH, GAP = 1240, 14
SHAPES = [(0, 1), (0, 2), (0, 3), (1, 1), (1, 2), (2, 1), (2, 0), (3, 0)]
MIN_H, MAX_H = 240, 960


def height(t, w, ar_t, ar_w):
    n = t + w
    return (WIDTH - GAP * (n - 1)) / (t * ar_t + w * ar_w)


def search(n_tall, n_wide, ar_t, ar_w):
    best, stack = None, [([], n_tall, n_wide)]
    while stack:
        rows, t, w = stack.pop()
        if t == 0 and w == 0:
            if len(rows) < 2:
                continue
            hs = [height(a, b, ar_t, ar_w) for a, b in rows]
            if any(h < MIN_H or h > MAX_H for h in hs):
                continue
            score = (max(hs) - min(hs)) + len(set(rows)) * 120 - len(rows) * 8
            if best is None or score > best[0]:
                best = (score, rows)
            continue
        if len(rows) > 10:
            continue
        for a, b in SHAPES:
            if a <= t and b <= w:
                stack.append((rows + [(a, b)], t - a, w - b))
    return best[1] if best else None


def sequence(shapes, ar_t, ar_w):
    order = sorted(shapes, key=lambda s: -height(s[0], s[1], ar_t, ar_w))
    out, lo, hi = [], 0, len(order) - 1
    while lo <= hi:
        out.append(order[lo]); lo += 1
        if lo <= hi:
            out.append(order[hi]); hi -= 1
    return out


def deal(photos, rows):
    tall = [p for p in photos if p["ar"] < 1]
    wide = [p for p in photos if p["ar"] >= 1]
    wide.sort(key=lambda p: -p["ar"])

    def spread(seq, n):
        if not seq or n <= 0:
            return []
        step = max(1, len(seq) // n)
        picked, i = [], 0
        while len(picked) < n and seq:
            picked.append(seq.pop(min(i % max(1, len(seq)), len(seq) - 1)))
            i += step
        return picked

    return [spread(tall, a) + spread(wide, b) for a, b in rows]


def main():
    out_dir = pathlib.Path("renders")
    out_dir.mkdir(exist_ok=True)
    galleries = json.loads(pathlib.Path("galleries.json").read_text())
    summary = []
    described = generic = 0

    for g in galleries:
        photos = [{"file": f, "label": lb, "w": w, "h": h,
                   "ar": round(w / h, 4),
                   "alt": ALT_TEXT.get(f, ALT)}
                  for f, lb, w, h in g["photos"]]
        described += sum(1 for p in photos if p["alt"] != ALT)
        generic += sum(1 for p in photos if p["alt"] == ALT)
        tall = [p for p in photos if p["ar"] < 1]
        wide = [p for p in photos if p["ar"] >= 1]
        ar_t = sum(p["ar"] for p in tall) / len(tall) if tall else 0.67
        ar_w = sum(p["ar"] for p in wide) / len(wide) if wide else 1.5

        shapes = search(len(tall), len(wide), ar_t, ar_w)
        if not shapes:
            raise SystemExit("no arrangement for %s (%d tall, %d wide)"
                             % (g["slug"], len(tall), len(wide)))
        rows = deal(photos, sequence(shapes, ar_t, ar_w))

        used = sorted(p["label"] for r in rows for p in r)
        assert used == sorted(p["label"] for p in photos), g["slug"]

        hs = [round((WIDTH - GAP * (len(r) - 1)) / sum(p["ar"] for p in r))
              for r in rows]
        # The bar at the foot of the gallery walks Jessica's own order and
        # wraps at both ends, so no session is a dead end.
        i = galleries.index(g)
        prev = galleries[i - 1]
        nxt = galleries[(i + 1) % len(galleries)]
        # `slug` is what the gallery template builds its canonical and og:url
        # from, and what deploy-site.py checks the filename against. It was in
        # the payloads on disk but NOT written here, so re-running this script
        # would have silently dropped it and broken every gallery's canonical
        # tag. Caught on 26 September when this file was next touched.
        payload = {"name": g["name"], "slug": g["slug"], "cdn": CDN,
                   "rows": rows,
                   "prev": {"name": prev["name"], "slug": prev["slug"]},
                   "nxt": {"name": nxt["name"], "slug": nxt["slug"]}}
        (out_dir / (g["slug"] + ".json")).write_text(
            json.dumps(payload, separators=(",", ":")))
        summary.append((g["slug"], g["name"], len(photos), len(wide), len(tall),
                        len(rows), len(set(map(tuple, shapes))), hs))

    print("\nalt text: %d described, %d still on the generic line"
          % (described, generic))
    if generic:
        print("         (a frame with no entry in gallery-alt-text.json "
              "falls back; add one)")
    print()
    print("%-20s %-7s %4s %4s %4s %5s %6s  row heights"
          % ("slug", "name", "n", "wide", "tall", "rows", "shapes"))
    for s in summary:
        print("%-20s %-7s %4d %4d %4d %5d %6d  %s"
              % (s[0], s[1], s[2], s[3], s[4], s[5], s[6],
                 " ".join(str(h) for h in s[7])))


main()
