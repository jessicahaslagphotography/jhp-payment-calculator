#!/usr/bin/env python3
"""Instagram/Facebook story frames (1080x1920) for the 2027 Charity Calendar Model Call,
styled like the landing page: near-black #13100E, gold #C9A24B / #E6C576, ivory #F2ECE2,
Cormorant Garamond (light serif) + Jost (letter-spaced caps).

Instagram covers roughly the top and bottom 250px with its own UI, so all text sits
between y=250 and y=1670. Each frame leaves a clear area for the sticker Jessica adds
in the app (countdown / poll / link).

  python3 stories.py OUT_DIR FONTS_DIR [--placeholders]
Photos are fetched by URL; with --placeholders (or on a failed fetch) a dark gradient
stands in so the layout can be checked offline.
"""
import io, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
BG = (19, 16, 14)
PANEL = (28, 23, 20)
GOLD = (201, 162, 75)
GOLD_B = (230, 197, 118)
INK = (242, 236, 226)
SOFT = (217, 208, 195)
MUTED = (169, 154, 134)
DIM = (125, 113, 97)

LH3 = "https://lh3.googleusercontent.com/d/{}=w1600"
CDN = "https://assets.cdn.filesafe.space/Pcnm8GVNMmWTY65qVOAp/media/"
PHOTOS = {
    "hero": LH3.format("1S-Cp7Jf9f9_vlBV0rDxJLuIUf8ByGfpI"),
    "privacy": LH3.format("1ajMRwLjGI-FvWLtgjOCQmRsmHakEqDRS"),
    "review1": LH3.format("1bSg71Wy7JLbR7419zn2mk8JOXleoHGRu"),
    "ba": CDN + "6add6babd542268bb41287d9.png",        # Before and After Posts (3)
    "graphic": CDN + "6add6be49c1511d5b9afb075.png",   # Model Call Graphics 2.png
}


class Fonts:
    def __init__(self, d):
        self.d = d

    def _f(self, file, size, var):
        f = ImageFont.truetype(os.path.join(self.d, file), size)
        try:
            f.set_variation_by_name(var)
        except Exception:
            pass
        return f

    def serif(self, size, var="Light"):
        return self._f("CormorantGaramond[wght].ttf", size, var)

    def italic(self, size, var="Light"):
        return self._f("CormorantGaramond-Italic[wght].ttf", size, var)

    def sans(self, size, var="Regular"):
        return self._f("Jost[wght].ttf", size, var)


def fetch(key, placeholders):
    if not placeholders:
        try:
            import requests
            r = requests.get(PHOTOS[key], timeout=60)
            r.raise_for_status()
            return Image.open(io.BytesIO(r.content)).convert("RGB")
        except Exception as e:
            print("photo fetch failed", key, e)
    pw, phh = {"graphic": (940, 788), "ba": (1080, 1080)}.get(key, (1200, 1600))
    im = Image.new("RGB", (pw, phh), (70, 58, 50))
    g = ImageDraw.Draw(im)
    for y in range(phh):
        c = int(40 + 50 * y / phh)
        g.line([(0, y), (pw, y)], fill=(c + 30, c + 18, c + 10))
    g.ellipse([pw * .3, phh * .2, pw * .7, phh * .8], fill=(120, 96, 80))
    return im


def cover(im, w, h, focus_y=0.4):
    s = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * s + 0.5), int(im.height * s + 0.5)), Image.LANCZOS)
    x = (im.width - w) // 2
    y = int((im.height - h) * focus_y)
    return im.crop((x, y, x + w, y + h))


def shade(im, start=0.42, top=0.35):
    """Landing-page hero treatment: dark at the bottom, lighter mid, dim at the top."""
    ov = Image.new("RGBA", im.size)
    d = ImageDraw.Draw(ov)
    h = im.height
    for y in range(h):
        t = y / h
        if t < 0.18:
            a = int(255 * top * (1 - t / 0.18))
        elif t < start:
            a = 0
        else:
            a = int(255 * min(0.96, (t - start) / (1 - start) * 1.25))
        d.line([(0, y), (im.width, y)], fill=BG + (a,))
    return Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")


def tracked(d, xy, text, font, fill, spacing, anchor="mm"):
    """Letter-spaced caps (the landing page's .kick style)."""
    widths = [d.textlength(ch, font=font) for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x, y = xy
    x0 = x - total / 2 if anchor[0] == "m" else x
    for ch, w in zip(text, widths):
        d.text((x0, y), ch, font=font, fill=fill, anchor="l" + anchor[1])
        x0 += w + spacing
    return total


def lines(d, x, y, rows, font, fill, gap=1.12, anchor="ma"):
    lh = font.size * gap
    for i, r in enumerate(rows):
        d.text((x, y + i * lh), r, font=font, fill=fill, anchor=anchor)
    return y + len(rows) * lh


def rule(d, cx, y, w=120, color=GOLD):
    d.line([(cx - w / 2, y), (cx + w / 2, y)], fill=color, width=2)


def pill(d, cx, cy, text, F, color=GOLD_B):
    f = F.sans(26)
    tw = tracked(ImageDraw.Draw(Image.new("RGB", (1, 1))), (0, 0), text, f, color, 5)
    pad = 34
    box = [cx - tw / 2 - pad, cy - 34, cx + tw / 2 + pad, cy + 34]
    d.rounded_rectangle(box, radius=34, outline=(201, 162, 75), width=2, fill=(19, 16, 14))
    tracked(d, (cx, cy), text, f, color, 5)


def brand_top(d, F, y=300):
    tracked(d, (W / 2, y), "JHP BOUDOIR", F.sans(30), GOLD, 11)


def brand_bottom(d, F, y=1630):
    tracked(d, (W / 2, y), "2027 CHARITY CALENDAR · MODEL CALL", F.sans(22), DIM, 6)


# ---------------------------------------------------------------- frames

def sun1(F, ph):
    im = shade(cover(ph("hero"), W, H, 0.3), start=0.40)
    d = ImageDraw.Draw(im)
    brand_top(d, F)
    tracked(d, (W / 2, 1060), "SOMETHING IS COMING", F.sans(28), GOLD_B, 9)
    y = lines(d, W / 2, 1110, ["Be a model in my", "2027 Charity", "Calendar"], F.serif(112), INK, 1.0)
    pill(d, W / 2, y + 70, "TOMORROW · 9 AM CT", F)
    return im


def sun2(F, ph):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    brand_top(d, F)
    tracked(d, (W / 2, 470), "MODEL CALL · BY APPLICATION", F.sans(26), GOLD, 7)
    y = lines(d, W / 2, 540, ["Real women.", "Every body.", "One good cause."], F.italic(118), GOLD_B, 1.05)
    rule(d, W / 2, y + 40)
    lines(d, W / 2, y + 90, ["I’m hand-picking a small group of", "women for my 2027 Charity Calendar."],
          F.sans(36, "Light"), SOFT, 1.45)
    pill(d, W / 2, 1180, "APPLICATIONS OPEN TOMORROW · 9 AM", F)
    # 1280-1560 left clear for the countdown sticker
    brand_bottom(d, F)
    return im


def sun3(F, ph):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    brand_top(d, F)
    tracked(d, (W / 2, 420), "THE TRANSFORMATION", F.sans(26), GOLD, 8)
    s = 840
    ba = cover(ph("ba"), s, s, 0.5)
    im.paste(ba, ((W - s) // 2, 470))
    d.rectangle([(W - s) // 2 - 1, 469, (W + s) // 2, 470 + s], outline=(80, 66, 40), width=1)
    y = lines(d, W / 2, 470 + s + 50, ["Same woman. Same body."], F.serif(78), INK)
    lines(d, W / 2, y + 14, ["Just finally seen the way she deserves to be."], F.italic(42), MUTED)
    brand_bottom(d, F)
    return im


def mon1(F, ph):
    im = shade(cover(ph("privacy"), W, H, 0.3), start=0.38)
    d = ImageDraw.Draw(im)
    brand_top(d, F)
    tracked(d, (W / 2, 1020), "MODEL CALL · NOW OPEN", F.sans(28), GOLD_B, 9)
    y = lines(d, W / 2, 1075, ["I’m looking for", "models for my", "2027 Charity Calendar"],
              F.serif(100), INK, 1.02)
    lines(d, W / 2, y + 30, ["Real women. Every body."], F.italic(52), GOLD_B)
    return im


def mon2(F, ph):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    brand_top(d, F)
    g = ph("graphic")
    gw = 820
    g = g.resize((gw, int(g.height * gw / g.width)), Image.LANCZOS)
    top = 380
    im.paste(g, ((W - gw) // 2, top))
    y = top + g.height + 80
    y = lines(d, W / 2, y, ["I’m hand-picking", "a small group of models"], F.serif(84), INK, 1.05)
    rule(d, W / 2, y + 36)
    lines(d, W / 2, y + 76, ["Applications close Friday, Oct 30 at midnight"], F.sans(32, "Light"), MUTED)
    brand_bottom(d, F)
    return im


def mon3(F, ph):
    im = shade(cover(ph("review1"), W, H, 0.25), start=0.52)
    d = ImageDraw.Draw(im)
    brand_top(d, F)
    # upper-middle left clear (photo) for the poll sticker
    y = lines(d, W / 2, 1230, ["No experience needed."], F.serif(92), INK)
    lines(d, W / 2, y + 6, ["Every body."], F.italic(96), GOLD_B)
    brand_bottom(d, F)
    return im


def mon4(F, ph):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    brand_top(d, F)
    tracked(d, (W / 2, 520), "YOUR MOMENT", F.sans(28), GOLD, 10)
    y = lines(d, W / 2, 580, ["Apply in", "2 minutes"], F.serif(170), GOLD_B, 0.98)
    rule(d, W / 2, y + 40)
    lines(d, W / 2, y + 90, ["Free. No commitment. No experience needed.",
                             "Applications close Friday, Oct 30 at midnight."], F.sans(34, "Light"), SOFT, 1.5)
    tracked(d, (W / 2, 1290), "TAP THE LINK BELOW", F.sans(26), GOLD, 8)
    d.line([(W / 2, 1330), (W / 2, 1390)], fill=GOLD, width=2)
    d.polygon([(W / 2 - 12, 1380), (W / 2 + 12, 1380), (W / 2, 1402)], fill=GOLD)
    # 1420-1580 left clear for the link sticker
    brand_bottom(d, F)
    return im


FRAMES = [("Sun-1-teaser", sun1), ("Sun-2-real-women", sun2), ("Sun-3-before-after", sun3),
          ("Mon-1-looking-for-models", mon1), ("Mon-2-hand-picking", mon2),
          ("Mon-3-every-body-poll", mon3), ("Mon-4-apply-link", mon4)]


def build(out, fonts_dir, placeholders=False):
    os.makedirs(out, exist_ok=True)
    F = Fonts(fonts_dir)
    cache = {}

    def ph(k):
        if k not in cache:
            cache[k] = fetch(k, placeholders)
        return cache[k]

    paths = []
    for name, fn in FRAMES:
        p = os.path.join(out, f"CCMC-Story-{name}.png")
        fn(F, ph).save(p, optimize=True)
        paths.append(p)
    return paths


if __name__ == "__main__":
    print(build(sys.argv[1], sys.argv[2], "--placeholders" in sys.argv))
