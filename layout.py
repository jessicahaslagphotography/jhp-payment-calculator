#!/usr/bin/env python3
"""Lays a gallery out into justified rows of deliberately varying height.

Within a row every figure gets flex-grow equal to its aspect ratio, so the
row fills the width and all its frames land on one height. That height is
decided entirely by what is in the row: three wide frames make a short
strip, two tall ones make a deep block, a lone wide frame makes a banner.

So the composition of each row IS the rhythm of the page. Filling rows
greedily gives you the same row over and over -- tall, wide, tall, wide --
which is the repetitiveness this is here to avoid. Instead every way of
spending the gallery's wide and tall frames is searched, and the
arrangement whose row heights vary most is chosen, with a penalty for two
neighbouring rows of the same shape.

Frames are then dealt into those rows spread across the shoot rather than
in capture order, because consecutive frame numbers are the same pose from
the same setup and sit badly side by side.
"""
import json, pathlib, sys
from itertools import product

WIDTH, GAP = 1240, 14
# Row shapes worth using, as (tall, wide) counts. A lone tall frame is
# excluded: at 0.67 aspect it would stand nearly two thousand pixels high.
SHAPES = [(0, 1), (0, 2), (0, 3), (1, 1), (1, 2), (2, 1), (2, 0), (3, 0)]
MIN_H, MAX_H = 240, 960


def height(tall, wide, ar_t, ar_w):
    n = tall + wide
    return (WIDTH - GAP * (n - 1)) / (tall * ar_t + wide * ar_w)


def search(n_tall, n_wide, ar_t, ar_w):
    """Pick the multiset of row shapes that spends every frame exactly.

    Scored on how far apart the row heights are and on how many distinct
    shapes are used -- a gallery of seven different rows reads as composed,
    one of seven identical rows reads as a grid. Sequencing happens after;
    this only decides what the rows are made of.
    """
    best = None
    stack = [([], n_tall, n_wide)]
    while stack:
        rows, t, w = stack.pop()
        if t == 0 and w == 0:
            if len(rows) < 2:
                continue
            hs = [height(a, b, ar_t, ar_w) for a, b in rows]
            if any(h < MIN_H or h > MAX_H for h in hs):
                continue
            spread = max(hs) - min(hs)
            distinct = len(set(rows))
            score = spread + distinct * 120 - len(rows) * 8
            if best is None or score > best[0]:
                best = (score, rows, hs)
            continue
        if len(rows) > 10:
            continue
        for a, b in SHAPES:
            if a <= t and b <= w:
                stack.append((rows + [(a, b)], t - a, w - b))
    return best


def sequence(shapes, ar_t, ar_w):
    """Order the rows tall, short, tall, short down the page.

    Sorted by height they would run deep blocks first and thin strips last,
    which is a gradient, not a rhythm. Dealing alternately off the two ends
    of the sorted list puts a banner next to a strip the whole way down.
    """
    order = sorted(shapes, key=lambda s: -height(s[0], s[1], ar_t, ar_w))
    out, lo, hi = [], 0, len(order) - 1
    while lo <= hi:
        out.append(order[lo]); lo += 1
        if lo <= hi:
            out.append(order[hi]); hi -= 1
    return out


def deal(photos, rows):
    """Spread the shoot across the rows rather than dealing in capture
    order, so two frames of the same pose never sit side by side."""
    tall = [p for p in photos if p["ar"] < 1]
    wide = [p for p in photos if p["ar"] >= 1]
    # The widest frame opens the gallery, wherever the banner row landed.
    wide.sort(key=lambda p: -p["ar"])

    def spread(seq, n):
        """n picks walked across seq at an even stride, not off the front."""
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
    src = json.loads(pathlib.Path(sys.argv[1]).read_text())
    photos = [{"file": f, "label": lb, "w": w, "h": h, "ar": round(w / h, 4),
               "alt": "Boudoir portrait from a session at JHP Boudoir"}
              for f, lb, w, h in src["photos"]]
    tall = [p for p in photos if p["ar"] < 1]
    wide = [p for p in photos if p["ar"] >= 1]
    ar_t = sum(p["ar"] for p in tall) / len(tall) if tall else 0.67
    ar_w = sum(p["ar"] for p in wide) / len(wide) if wide else 1.5

    best = search(len(tall), len(wide), ar_t, ar_w)
    if not best:
        raise SystemExit("no arrangement found for %d tall / %d wide"
                         % (len(tall), len(wide)))
    rows = deal(photos, sequence(best[1], ar_t, ar_w))

    print("%d frames: %d wide, %d tall\n" % (len(photos), len(wide), len(tall)))
    for n, row in enumerate(rows, 1):
        gaps = GAP * (len(row) - 1)
        h = round((WIDTH - gaps) / sum(p["ar"] for p in row))
        shape = "  ".join("%s %s" % (p["label"], "wide" if p["ar"] > 1 else "tall")
                          for p in row)
        print("row %-2d %-56s %4dpx" % (n, shape, h))

    out = dict(src)
    out["rows"] = rows
    pathlib.Path(sys.argv[2]).write_text(json.dumps(out, indent=1))
    used = [p["label"] for r in rows for p in r]
    assert sorted(used) == sorted(p["label"] for p in photos), "frames lost"
    print("\n%d rows, every frame used once" % len(rows))


main()
