#!/usr/bin/env python3
"""The picker Jessica chooses the Session Guide's hero photograph with.

WHY THIS EXISTS. The image CDN (assets.cdn.filesafe.space) is not reachable
from the build sandbox, so nobody here can look at a photograph and say
whether it works as a hero. Her browser can. So the judgement moves to the
browser, exactly as the band tuner and the two photo pickers already do.

WHAT IT SHOWS. Every landscape frame from the twelve galleries that is not
already on this site -- ninety of them -- each drawn at the REAL hero
geometry: the same clamp()ed height, the same object-fit and object-position,
the same bottom-up scrim, and the real eyebrow and title over it. A frame is
judged at the size and crop it will actually land at, which is the house rule.
A contact sheet of uncropped thumbnails would be a different picture.

THE PREVIEW IS A SCALE MODEL, the same trick as the band tuner: the hero is
drawn at a true 1440px (and a true 390px) inside a CSS-scaled wrapper, so
`cover` crops exactly as it will on the page rather than approximately.

SELF-CONTAINED on purpose -- no database, no page token, nothing that
expires. She can leave it open for a week. The selection lives in
localStorage and leaves by the clipboard.

RETIRE IT when she has chosen: render the page against jhp-temp-retired
FIRST, then delete it. pages_delete leaves the last rendered file served by
Caddy, and this one is full of client photographs.
"""
import json, glob, re, pathlib

ROOT = pathlib.Path(__file__).parent
CDN = "https://assets.cdn.filesafe.space/Pcnm8GVNMmWTY65qVOAp/media/"

# ---------------------------------------------------------------- the frames
# Landscape only: the hero is a wide band and a portrait frame would be cropped
# to a sliver of itself. And nothing already on the site, so whatever she picks
# does not turn up twice -- the same face opening two pages reads as the only
# woman who has ever been there.
# THE TOOLS ARE NOT THE SITE, and this one would poison itself. Its own
# output names all ninety candidates, so a second run would read them back as
# "already used" and build an empty picker -- which the guard at the foot
# caught the first time this ran twice. The tuners and the other pickers are
# excluded for the same reason: a frame shown in a tool is not a frame
# published on a page.
TOOLS = {"scalogy-hero-picker.html", "scalogy-picker.html",
         "scalogy-exp-picker.html", "scalogy-band-tuner.html",
         "scalogy-crop-tuner.html", "scalogy-gallery.html"}
used = set()
for f in glob.glob(str(ROOT / "scalogy-*.html")):
    if pathlib.Path(f).name in TOOLS:
        continue
    used |= set(re.findall(r"media/([0-9a-f-]+\.jpg)", open(f).read()))

frames = []
seen = set()
for p in sorted(glob.glob(str(ROOT / "renders" / "*.json"))):
    d = json.load(open(p))
    for row in d["rows"]:
        for fr in row:
            # The payload calls it "file" and carries a precomputed aspect
            # ratio; do not guess at either, a wrong key here silently yields
            # an empty picker rather than an error.
            fn = fr.get("file")
            if not fn or fn in used or fn in seen:
                continue
            if fr.get("ar", 0) <= 1.3:
                continue
            seen.add(fn)
            frames.append({"f": fn, "g": d["name"]})

# THE TILES ARE DATA, NOT MARKUP, and that is a size decision. Ninety tiles
# written out as HTML came to 42KB of a 47KB template, almost all of it the
# same six tags around a different UUID -- and a template over 20KB has to go
# up as a create plus a run of patches. As a JSON array of ninety names it is
# 4KB and the whole tool publishes in one call. The page builds the tiles on
# load, which is no loss: this is a private tool for Jessica, the other
# pickers are JS-driven for the same reason, and nothing here is for a client
# or a crawler.
TILES = json.dumps([[fr["f"], fr["g"]] for fr in frames])

HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Session Guide Hero Picker</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=Jost:wght@300;400;500;600&display=swap');
:root{
  --ground:#13100E; --surface:#1C1714; --raised:#241D18;
  --ink:#F2ECE2; --muted:#A99A86; --dim:#7D7161;
  --gold:#C9A24B; --gold-bright:#E6C576;
  --line:rgba(201,162,75,.22); --line-soft:rgba(242,236,226,.09);
  --serif:'Cormorant Garamond',Georgia,'Times New Roman',serif;
  --sans:'Jost',-apple-system,'Segoe UI',system-ui,sans-serif;
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);
  font-weight:300;-webkit-font-smoothing:antialiased}
header{padding:28px 22px 20px;border-bottom:1px solid var(--line-soft);
  position:sticky;top:0;background:var(--ground);z-index:20}
h1{font-family:var(--serif);font-weight:600;font-size:30px;line-height:1.1;
  margin:0 0 8px}
header p{margin:0;font-size:13px;line-height:1.6;color:var(--muted);max-width:66ch}
header b{color:var(--gold);font-weight:500}

/* THE SCALE MODEL. The hero inside .sc is drawn at a true 1440x555 -- 555 is
   what clamp(320px,37vw,600px) resolves to at 1440 -- and the wrapper scales
   the whole thing down. cover then crops against the real box, so what she
   sees is what the page does, not an approximation of it. */
.sc{display:block;width:100%;aspect-ratio:1440/555;overflow:hidden;position:relative}
.hero{position:absolute;top:0;left:0;width:1440px;height:555px;
  transform-origin:0 0;display:block}
.hero img{width:1440px;height:555px;object-fit:cover;object-position:50% 77%;
  display:block;filter:saturate(.96) contrast(1.02)}
.hero .ov{position:absolute;inset:0;display:flex;flex-direction:column;
  align-items:center;justify-content:flex-end;text-align:center;
  padding:0 60px 46px;
  background:linear-gradient(0deg,rgba(19,16,14,.94) 0%,
    rgba(19,16,14,.78) 24%,rgba(19,16,14,.34) 52%,rgba(19,16,14,.04) 82%)}
.hero .k{font-family:var(--sans);font-weight:400;font-size:11px;
  letter-spacing:.3em;text-transform:uppercase;color:var(--gold);
  margin:0 0 12px;display:block}
.hero .h1{font-family:var(--serif);font-weight:600;font-size:66px;
  line-height:1.06;letter-spacing:-.012em;color:var(--ink);display:block;
  max-width:24ch}

/* The phone model: a true 390x220 with the phone's own object-position and
   38px title, because that crop is a different photograph from the desktop
   one and she should see both before choosing. */
.sc.ph{aspect-ratio:390/220}
.sc.ph .hero{width:390px;height:220px}
.sc.ph .hero img{width:390px;height:220px;object-position:43% 89%}
.sc.ph .hero .ov{padding:0 22px 24px}
.sc.ph .hero .k{font-size:10px;letter-spacing:.26em;margin-bottom:10px}
.sc.ph .hero .h1{font-size:38px;line-height:1.12;max-width:23ch}

main{padding:22px}
.grid{display:grid;gap:18px;
  grid-template-columns:repeat(auto-fill,minmax(330px,1fr))}
.t{padding:0;border:1px solid var(--line-soft);background:var(--surface);
  border-radius:2px;cursor:pointer;overflow:hidden;text-align:left;
  transition:border-color .25s;font:inherit;color:inherit;display:block}
.t:hover{border-color:var(--line)}
.t[aria-pressed="true"]{border-color:var(--gold-bright);box-shadow:0 0 0 1px var(--gold-bright)}
.t:focus-visible{outline:2px solid var(--gold-bright);outline-offset:3px}
.cap{display:block;padding:9px 12px;font-size:10px;letter-spacing:.2em;
  text-transform:uppercase;color:var(--dim)}
.t[aria-pressed="true"] .cap{color:var(--gold)}

/* The chosen frame, big, at both widths, pinned where she can keep looking. */
#out{position:sticky;bottom:0;background:var(--raised);
  border-top:1px solid var(--line);padding:18px 22px;z-index:20}
#out[hidden]{display:none}
.pair{display:flex;gap:18px;align-items:flex-start;flex-wrap:wrap}
.pair .big{flex:1 1 520px;min-width:300px}
.pair .sm{flex:0 0 260px}
.lab{font-size:10px;letter-spacing:.22em;text-transform:uppercase;
  color:var(--dim);margin:0 0 7px}
.id{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;
  color:var(--ink);word-break:break-all;margin:12px 0 10px}
button.copy{font-family:var(--sans);font-size:10px;letter-spacing:.22em;
  text-transform:uppercase;color:var(--ground);background:var(--gold);
  border:0;border-radius:2px;padding:17px 22px;cursor:pointer}
button.copy:hover{background:var(--gold-bright)}
button.copy:focus-visible{outline:2px solid var(--ink);outline-offset:3px}
@media (max-width:620px){
  header{padding:20px 16px 16px}
  h1{font-size:24px}
  main{padding:16px}
  .grid{grid-template-columns:1fr;gap:14px}
  .pair .sm{flex:1 1 100%}
}
</style>
</head>
<body>
<header>
  <h1>Pick the Session Guide Hero</h1>
  <p><b>@@COUNT@@ frames</b>, every landscape photograph from your twelve galleries
     that is not already somewhere on this site. Each one is drawn at the real
     size and crop the hero lands at, with the real eyebrow and title over it
     &mdash; so what you see here is what the page does. Tap one to see it big,
     at a desktop width and a phone width, then copy the name and send it to
     me.</p>
</header>

<main>
  <div class="grid" id="grid"></div>
  <noscript><p style="color:#A99A86">This picker needs JavaScript to draw the
     ninety frames at the hero\u2019s real size.</p></noscript>
</main>

<div id="out" hidden>
  <div class="pair">
    <div class="big">
      <p class="lab">At 1440</p>
      <span class="sc"><span class="hero" id="bigHero"></span></span>
    </div>
    <div class="sm">
      <p class="lab">At 390</p>
      <span class="sc ph"><span class="hero" id="phHero"></span></span>
      <p class="id" id="pickId"></p>
      <button class="copy" type="button" id="copy">Copy the Name</button>
    </div>
  </div>
</div>

<script>
(() => {
  const CDN = @@CDN@@;
  const FRAMES = @@TILES@@;

  /* Build the grid from the data. Same markup the server used to write, one
     tile per frame, each an honest scale model of the hero. */
  document.getElementById("grid").innerHTML = FRAMES.map(([f, g]) =>
    '<button class="t" type="button" data-f="' + f + '" data-g="' + g + '">' +
    '<span class="sc"><span class="hero">' +
    '<img src="' + CDN + f + '" loading="lazy" alt="">' +
    '<span class="ov"><span class="k">JHP Boudoir</span>' +
    '<span class="h1">Your Session Guide</span></span></span></span>' +
    '<span class="cap">' + g + '</span></button>').join("");
  /* The scale models are drawn at true pixel sizes and shrunk to fit, so the
     transform has to be recomputed whenever the box changes width -- on load,
     on resize, and when the sticky panel first appears. */
  const fit = (el) => {
    const box = el.closest(".sc");
    if (!box) return;
    const w = box.classList.contains("ph") ? 390 : 1440;
    el.style.transform = "scale(" + (box.clientWidth / w) + ")";
  };
  const fitAll = () => document.querySelectorAll(".hero").forEach(fit);

  const shell = (f) =>
    '<img src="' + CDN + f + '" alt="">' +
    '<span class="ov"><span class="k">JHP Boudoir</span>' +
    '<span class="h1">Your Session Guide</span></span>';

  const out = document.getElementById("out");
  const pick = (f, g) => {
    document.querySelectorAll(".t").forEach((b) =>
      b.setAttribute("aria-pressed", String(b.dataset.f === f)));
    document.getElementById("bigHero").innerHTML = shell(f);
    document.getElementById("phHero").innerHTML = shell(f);
    document.getElementById("pickId").textContent = f;
    out.hidden = false;
    fitAll();
    try { localStorage.setItem("jhp-guide-hero", f); } catch (e) {}
  };

  document.querySelectorAll(".t").forEach((b) => {
    b.setAttribute("aria-pressed", "false");
    b.addEventListener("click", () => pick(b.dataset.f, b.dataset.g));
  });

  document.getElementById("copy").addEventListener("click", async () => {
    const f = document.getElementById("pickId").textContent;
    const btn = document.getElementById("copy");
    try { await navigator.clipboard.writeText(f); btn.textContent = "Copied"; }
    catch (e) { btn.textContent = "Select it above and copy"; }
    setTimeout(() => { btn.textContent = "Copy the Name"; }, 2200);
  });

  fitAll();
  addEventListener("resize", fitAll);
  /* The tiles load lazily, so a frame that arrives after the first fit needs
     its own -- otherwise it draws at 1440 inside a 330px box. */
  document.querySelectorAll(".hero img").forEach((i) =>
    i.addEventListener("load", () => fit(i.parentElement)));

  try {
    const last = localStorage.getItem("jhp-guide-hero");
    if (last) {
      const b = document.querySelector('.t[data-f="' + last + '"]');
      if (b) pick(last, b.dataset.g);
    }
  } catch (e) {}
})();
</script>
</body>
</html>
"""
HTML = (HTML.replace("@@COUNT@@", str(len(frames)))
            .replace("@@TILES@@", TILES)
            .replace("@@CDN@@", json.dumps(CDN)))

if len(frames) < 20:
    raise SystemExit("only %d candidate frames -- the payload keys have moved, "
                     "and an empty picker is worse than a build error" % len(frames))

(ROOT / "scalogy-hero-picker.html").write_text(HTML)
print("wrote %d bytes, %d candidate frames" % (len(HTML.encode()), len(frames)))
