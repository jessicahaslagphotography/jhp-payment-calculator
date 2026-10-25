#!/usr/bin/env python3
"""Tuesday-Friday story frames for the 2027 Charity Calendar Model Call. Same look and
helpers as ccmc_stories.py (Sun/Mon); only the frames differ.

  python3 ccmc_stories_tf.py OUT_DIR FONTS_DIR [--placeholders]
"""
import os, sys
from PIL import Image, ImageDraw
import ccmc_stories as cs
from ccmc_stories import (W, H, BG, GOLD, GOLD_B, INK, SOFT, MUTED, cover, shade, tracked,
                          lines, rule, pill, brand_top, brand_bottom)

cs.PHOTOS.update({
    "apply": cs.LH3.format("1RRM-T82fdj68TXiKIxjSn4_hVHyISJkp"),
    "review2": cs.LH3.format("1v4Lg1tHnjlSHKiQs67hu0Hu8ys1F2RRD"),
    "review3": cs.LH3.format("1OGYsnLuLrDVEIcpJRe8OpIsExohMQJMN"),
    "ba4": cs.CDN + "6add6babd542268bb41287e3.png",       # Before and After Posts (4)
    "ba5": cs.CDN + "6add6bab736386d0dcb4daa6.png",       # Before and After Posts (5)
    "graphic6": cs.CDN + "6add6be4736386d0dcb4dee9.png",  # Model Call Graphics 6.png
})
_fetch = cs.fetch


def fetch(key, placeholders):
    # placeholder shapes follow the real images
    im = _fetch(key, placeholders)
    if placeholders and key.startswith("ba"):
        im = im.resize((1080, 1080))
    if placeholders and key.startswith("graphic"):
        im = im.resize((940, 788))
    return im


cs.fetch = fetch


# ------------------------------------------------------------ frame builders

def photo_frame(F, ph, key, kicker, rows, size=100, tail=None, start=0.40, y0=1060, focus=0.3):
    im = shade(cover(ph(key), W, H, focus), start=start)
    d = ImageDraw.Draw(im)
    brand_top(d, F)
    tracked(d, (W / 2, y0), kicker, F.sans(28), GOLD_B, 9)
    y = lines(d, W / 2, y0 + 55, rows, F.serif(size), INK, 1.02)
    if tail:
        lines(d, W / 2, y + 26, [tail], F.italic(54), GOLD_B)
    return im


def ba_frame(F, ph, key, kicker, title, sub):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    brand_top(d, F)
    tracked(d, (W / 2, 420), kicker, F.sans(26), GOLD, 8)
    s = 840
    im.paste(cover(ph(key), s, s, 0.5), ((W - s) // 2, 470))
    d.rectangle([(W - s) // 2 - 1, 469, (W + s) // 2, 470 + s], outline=(80, 66, 40), width=1)
    y = lines(d, W / 2, 470 + s + 50, [title], F.serif(74), INK)
    if sub:
        lines(d, W / 2, y + 14, [sub], F.italic(42), MUTED)
    brand_bottom(d, F)
    return im


def card(F, kicker, rows, size=118, italic=True, body=None, pill_text=None, y0=500):
    """Black text card; the area below is left for a sticker when needed."""
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    brand_top(d, F)
    tracked(d, (W / 2, y0 - 50), kicker, F.sans(26), GOLD, 8)
    font = F.italic(size) if italic else F.serif(size)
    y = lines(d, W / 2, y0, rows, font, GOLD_B if italic else INK, 1.05)
    if body:
        rule(d, W / 2, y + 60)
        y = lines(d, W / 2, y + 110, body, F.sans(36, "Light"), SOFT, 1.45)
    if pill_text:
        pill(d, W / 2, y + 90, pill_text, F)
    brand_bottom(d, F)
    return im


def link_card(F, kicker, rows, body, size=150):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    brand_top(d, F)
    tracked(d, (W / 2, 520), kicker, F.sans(28), GOLD, 10)
    y = lines(d, W / 2, 580, rows, F.serif(size), GOLD_B, 1.0)
    rule(d, W / 2, y + 70)
    lines(d, W / 2, y + 120, body, F.sans(34, "Light"), SOFT, 1.5)
    tracked(d, (W / 2, 1290), "TAP THE LINK BELOW", F.sans(26), GOLD, 8)
    d.line([(W / 2, 1330), (W / 2, 1390)], fill=GOLD, width=2)
    d.polygon([(W / 2 - 12, 1380), (W / 2 + 12, 1380), (W / 2, 1402)], fill=GOLD)
    brand_bottom(d, F)
    return im


def qa_card(F, n, q, a):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    brand_top(d, F)
    tracked(d, (W / 2, 470), f"YOU ASKED · {n}", F.sans(26), GOLD, 8)
    y = lines(d, W / 2, 540, q, F.italic(92), GOLD_B, 1.06)
    rule(d, W / 2, y + 55)
    lines(d, W / 2, y + 115, a, F.serif(62), INK, 1.18)
    brand_bottom(d, F)
    return im


def quote_card(F, kicker, quote_rows, who):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    brand_top(d, F)
    tracked(d, (W / 2, 470), kicker, F.sans(26), GOLD, 8)
    tracked(d, (W / 2, 560), "★★★★★", F.sans(40), GOLD, 14)
    y = lines(d, W / 2, 640, quote_rows, F.italic(70), INK, 1.18)
    tracked(d, (W / 2, y + 60), who, F.sans(26), MUTED, 6)
    brand_bottom(d, F)
    return im


def graphic_frame(F, ph, key, rows, sub):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    brand_top(d, F)
    g = ph(key)
    gw = 820
    g = g.resize((gw, int(g.height * gw / g.width)), Image.LANCZOS)
    im.paste(g, ((W - gw) // 2, 380))
    y = lines(d, W / 2, 380 + g.height + 80, rows, F.serif(84), INK, 1.05)
    rule(d, W / 2, y + 36)
    lines(d, W / 2, y + 76, [sub], F.sans(32, "Light"), MUTED)
    brand_bottom(d, F)
    return im


# ------------------------------------------------------------------ frames

FRAMES = [
    # Tuesday: the why
    ("Tue-1-why", lambda F, ph: photo_frame(
        F, ph, "apply", "WHY I’M DOING THIS",
        ["Every woman in", "this calendar almost", "talked herself out of it."], size=92)),
    ("Tue-2-not-a-model", lambda F, ph: card(
        F, "WHAT I HEAR EVERY TIME", ["“I’m not", "a model.”"], size=150,
        body=["Almost every woman says it first.", "By the end of her session, she’s",
              "standing a little taller."])),
    ("Tue-3-every-pose-slider", lambda F, ph: photo_frame(
        F, ph, "review2", "NO EXPERIENCE NEEDED", ["Every pose, guided.", "Every angle, flattering."],
        size=88, tail="I direct it all, out loud.", start=0.50, y0=1180, focus=0.25)),
    ("Tue-4-apply-link", lambda F, ph: link_card(
        F, "THE ONLY REQUIREMENT", ["Have a body?", "You qualify."],
        ["Two minutes. Free. No commitment.", "Applications close Friday at midnight."], size=128)),
    # Wednesday: proof
    ("Wed-1-before-after", lambda F, ph: ba_frame(
        F, ph, "ba4", "THE TRANSFORMATION", "Same woman. Same body.", "No diet. Just light, posing and hype.")),
    ("Wed-2-before-after", lambda F, ph: ba_frame(
        F, ph, "ba5", "THE TRANSFORMATION", "Seen the way she deserves to be.", None)),
    ("Wed-3-review", lambda F, ph: quote_card(
        F, "SHE CAME IN NERVOUS TOO",
        ["“I was feeling nervous", "and insecure, but she", "immediately made me feel",
         "at home while hyping me", "up the entire time. By the", "end I felt like I could", "do anything!”"],
        "SKYLAR · GOOGLE REVIEW")),
    ("Wed-4-your-turn-link", lambda F, ph: link_card(
        F, "THIS COULD BE YOU", ["Your turn?"],
        ["Apply in two minutes.", "Applications close Friday at midnight."], size=170)),
    # Thursday: questions
    ("Thu-1-ask-me-question-box", lambda F, ph: card(
        F, "MODEL CALL Q&A", ["Ask me", "anything about", "the calendar"], size=120,
        body=["Nervous? Curious? Not sure if it’s for you?", "Send me your question below."])),
    ("Thu-2-answer-calendar", lambda F, ph: qa_card(
        F, 1, ["Do I have to be", "in the calendar?"],
        ["Nope! You decide at your", "image reveal, after you’ve", "seen your images. They stay",
         "private unless you say yes."])),
    ("Thu-3-answer-pose", lambda F, ph: qa_card(
        F, 2, ["I don’t know", "how to pose."],
        ["You don’t need to.", "I coach you through every", "single pose, out loud,", "the whole time."])),
    ("Thu-4-closing-link", lambda F, ph: link_card(
        F, "CLOSING SOON", ["Closes", "tomorrow"],
        ["Applications close Friday, Oct 30", "at midnight. Apply in two minutes."], size=160)),
    # Friday: last call
    ("Fri-1-last-call", lambda F, ph: photo_frame(
        F, ph, "review3", "LAST CALL", ["Last call for", "calendar models"], size=110,
        tail="Applications close tonight.", focus=0.25)),
    ("Fri-2-two-minutes", lambda F, ph: graphic_frame(
        F, ph, "graphic6", ["Two minutes.", "Free. No commitment."], "Every applicant hears back from me")),
    ("Fri-3-dont-talk-yourself-out-countdown", lambda F, ph: card(
        F, "BEFORE YOU SCROLL PAST", ["Don’t talk", "yourself", "out of it."], size=140,
        pill_text="CLOSES TONIGHT · MIDNIGHT")),
    ("Fri-4-apply-now-link", lambda F, ph: link_card(
        F, "FINAL HOURS", ["Apply now"],
        ["Applications close tonight at midnight.", "I can’t wait to read yours."], size=170)),
]


def build(out, fonts_dir, placeholders=False):
    cs.FRAMES[:] = FRAMES
    return cs.build(out, fonts_dir, placeholders)


if __name__ == "__main__":
    print(build(sys.argv[1], sys.argv[2], "--placeholders" in sys.argv))
