#!/usr/bin/env python3
"""Generates scalogy-exp-picker.html -- the picker for The Experience.

The Experience page has six photographs in it and they are not
interchangeable: two of them are bands with type set on top, two are
wide frames of a room, one is a tall frame of a room and one is a
portrait beside a review. A frame that is right for one is usually wrong
for the others, which is why this picker shows a slot at a time.

The thing it does that a contact sheet cannot: the preview at the top is
the chosen frame at the real geometry of that slot -- the real height,
the real crop, the real scrim and the real headline sitting on it. Every
mistake made on this site so far came from judging a photograph at a
quarter scale and finding out at full size that the heading was sitting
on somebody's face.

The grid below is the whole library, 276 frames, each one cut to the
shape of the active slot so the crop is visible before it is chosen.

Selection lives in localStorage and leaves by the clipboard. A page
token is good for fifteen minutes and choosing six photographs takes
longer than that, so the picker never talks to the server.
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
CDN = "https://assets.cdn.filesafe.space/Pcnm8GVNMmWTY65qVOAp/media/"

# --- the library ----------------------------------------------------------
g = json.loads((ROOT / "galleries.json").read_text())
pools = json.loads((ROOT / "picker-pools.json").read_text())
items, seen = [], set()
for gal in g:
    for f, lab, w, h in gal["photos"]:
        if f not in seen:
            seen.add(f); items.append([f, lab, gal["name"]])
for key, group in (("site", "Website folder"), ("rest", "Library")):
    for e in pools[key]:
        f, lab = e[0], e[1]
        if f not in seen and f.lower().endswith((".jpg", ".jpeg", ".png")):
            seen.add(f); items.append([f, lab, group])

# --- the six slots, each with the geometry it is really drawn at ----------
# ratio is width/height of the box on the page at 1080; over is the markup
# that sits on top of it, empty for the frames that carry no type.
# pratio/pfit are the same slot as a phone draws it. The bands are the
# reason this matters: at 390px the top band is 320px tall, not 144, and a
# preview at the desktop ratio would be showing a crop that never happens.
SLOTS = [
    {"k": "intro", "n": "Top band", "ratio": 2.70, "fit": "50% 20%",
     "ph": 320, "pfit": "50% 78%", "over": "intro",
     "note": "Kicker, heading and one line, centred on the floor of the band. "
             "Needs a frame whose bottom third is quiet."},
    {"k": "tall", "n": "Studio — tall", "ratio": 0.53, "fit": "50% 34%",
     "pratio": 0.752, "over": "",
     "note": "The left-hand frame of the studio set. Cut narrower than a "
             "portrait, so the room has to read from its middle."},
    {"k": "wideA", "n": "Studio — upper", "ratio": 1.50, "fit": "50% 40%",
     "pratio": 1.50, "over": "",
     "note": "Top right of the studio set. A whole room, uncropped at "
             "the sides."},
    {"k": "wideB", "n": "Studio — lower", "ratio": 1.50, "fit": "50% 46%",
     "pratio": 1.50, "over": "",
     "note": "Bottom right of the studio set. Pick a different room from "
             "the other two."},
    {"k": "quote", "n": "Review portrait", "ratio": 0.665, "fit": "50% 50%",
     "ph": 430, "over": "",
     "note": "Stands beside Miss N's review. A 2:3 portrait fits this box "
             "exactly, so nothing is cropped."},
    {"k": "band", "n": "Closing band", "ratio": 2.94, "fit": "50% 50%",
     "ph": 320, "pfit": "0% 50%", "over": "band",
     "note": "Heading, one line and the button, all set left. Needs a frame "
             "whose left third is quiet."},
]
CURRENT = {"intro": "6ab3ee86fef86e60d5226fb9.jpg",
           "tall": "6ab3ee7918384d888bb3d890.jpg",
           "wideA": "6ab3ee828bf21de2ae408336.jpg",
           "wideB": "ce79ce12-548d-4471-b9b2-282da4e1c2e9.jpg",
           "quote": "46a7d597-eea6-449f-9299-c3798b846f22.jpg",
           "band": "31196c8e-202f-429f-bbcd-7134a55a8caa.jpg"}

DATA = json.dumps({"cdn": CDN, "items": items, "slots": SLOTS,
                   "current": CURRENT}, separators=(",", ":"),
                  ensure_ascii=False)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Pick the photographs | The Experience</title>
<meta name="robots" content="noindex, nofollow">
<style>html,body{margin:0;padding:0;background:#13100E}body{overflow-x:hidden}</style>
</head>
<body>
{% raw %}
<div class="pk">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500&family=Jost:wght@300;400;500&display=swap');
.pk{--ground:#13100E;--surface:#1C1714;--ink:#F2ECE2;--muted:#A99A86;
  --dim:#7D7161;--gold:#C9A24B;--gold-bright:#E6C576;
  --line:rgba(201,162,75,.22);--line-soft:rgba(242,236,226,.09);
  --serif:'Cormorant Garamond',Georgia,serif;
  --sans:'Jost',-apple-system,'Segoe UI',system-ui,sans-serif;
  width:100vw;position:relative;left:50%;right:50%;
  margin-left:-50vw;margin-right:-50vw;max-width:100vw;
  background:var(--ground);color:var(--ink);font-family:var(--sans);
  font-size:16px;-webkit-font-smoothing:antialiased;overflow-x:hidden}
.pk *,.pk *::before,.pk *::after{box-sizing:border-box}
.pk p,.pk h1,.pk h2{margin:0}
.pk img{display:block;width:100%;height:100%;object-fit:cover;
  filter:saturate(.96) contrast(1.02)}

/* THE HEAD
   The slot tabs are the whole navigation. Each carries a thumbnail of
   what is currently in it, so the six choices can be read at a glance
   without leaving the slot being worked on. */
.pk .top{position:sticky;top:0;z-index:20;background:rgba(19,16,14,.97);
  border-bottom:1px solid var(--line);padding:12px clamp(14px,3vw,26px)}
.pk .ttl{font-family:var(--serif);font-size:19px;letter-spacing:.06em;
  color:var(--gold);text-transform:uppercase;margin-bottom:11px}
.pk .tabs{display:flex;gap:8px;overflow-x:auto;padding-bottom:3px;
  scrollbar-width:thin}
.pk .tab{flex:0 0 auto;display:flex;align-items:center;gap:9px;cursor:pointer;
  background:transparent;border:1px solid var(--line-soft);border-radius:2px;
  padding:6px 12px 6px 6px;color:var(--muted);font-family:var(--sans);
  font-size:11px;letter-spacing:.14em;text-transform:uppercase;
  transition:border-color .25s,color .25s}
.pk .tab .th{width:40px;height:40px;flex:0 0 40px;background:var(--surface);
  overflow:hidden}
.pk .tab.on{border-color:var(--gold);color:var(--ink)}
.pk .tab:hover{color:var(--ink)}

/* THE PREVIEW
   The point of the whole page: the frame at the size and crop it will be
   drawn at on the real page, with the real words on it. */
.pk .prev{position:relative;overflow:hidden;background:var(--surface);
  border-bottom:1px solid var(--line-soft)}
.pk .prev .ph{width:100%;max-height:78vh}
.pk .prev .ph img{object-position:var(--fit)}
.pk .prev .o{position:absolute;inset:0;display:flex;flex-direction:column;
  pointer-events:none}
.pk .k{font-family:var(--sans);font-size:11px;letter-spacing:.3em;
  text-transform:uppercase;color:var(--gold);margin:0 0 12px}
.pk .o h2{font-family:var(--serif);font-weight:500;color:var(--ink);
  font-size:clamp(28px,5vw,46px);line-height:1.1;letter-spacing:.01em}
.pk .o .sub{font-weight:300;font-size:clamp(14px,1.5vw,17px);color:var(--ink);
  opacity:.86;margin-top:13px;max-width:46ch}
.pk .o.intro{align-items:center;justify-content:flex-end;text-align:center;
  padding:0 clamp(20px,5vw,60px) clamp(22px,3.6vw,46px);
  background:linear-gradient(0deg,rgba(19,16,14,.95) 0%,rgba(19,16,14,.85) 27%,
    rgba(19,16,14,.55) 55%,rgba(19,16,14,.08) 84%)}
.pk .o.intro h2{max-width:24ch}
.pk .o.band{align-items:flex-start;justify-content:center;text-align:left;
  padding:0 clamp(22px,6vw,74px);
  background:linear-gradient(0deg,rgba(19,16,14,.8) 0%,rgba(19,16,14,.42) 55%,
      rgba(19,16,14,.3) 100%),
    linear-gradient(90deg,rgba(19,16,14,.72) 0%,rgba(19,16,14,.34) 38%,
      rgba(19,16,14,0) 68%)}
.pk .o.band h2{max-width:17ch;margin-bottom:8px}
.pk .o.band .sub{color:var(--muted);opacity:1;margin:0 0 22px;max-width:30ch}
.pk .o.band .btn{font-size:13px;letter-spacing:.18em;text-transform:uppercase;
  color:var(--ground);background:var(--gold);padding:14px 28px;font-weight:500}
.pk .o.none{display:none}
.pk .cap{display:flex;flex-wrap:wrap;gap:6px 18px;align-items:baseline;
  padding:13px clamp(14px,3vw,26px);border-bottom:1px solid var(--line-soft)}
.pk .cap b{font-weight:400;color:var(--gold);font-size:11px;
  letter-spacing:.24em;text-transform:uppercase}
.pk .cap span{font-weight:300;font-size:14px;color:var(--muted);
  line-height:1.6;max-width:70ch}

/* THE LIBRARY
   Every frame cut to the active slot's shape, so the crop is the thing
   being judged rather than the photograph. */
.pk .bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;
  padding:14px clamp(14px,3vw,26px) 10px}
.pk .bar button.f{background:transparent;border:1px solid var(--line-soft);
  border-radius:2px;color:var(--muted);font-family:var(--sans);font-size:11px;
  letter-spacing:.14em;text-transform:uppercase;padding:8px 13px;cursor:pointer;
  transition:border-color .25s,color .25s}
.pk .bar button.f.on{border-color:var(--gold);color:var(--ink)}
.pk .bar input{flex:1 1 180px;min-width:0;background:var(--surface);
  border:1px solid var(--line-soft);border-radius:2px;color:var(--ink);
  font-family:var(--sans);font-size:14px;padding:9px 12px}
.pk .bar input::placeholder{color:var(--dim)}
.pk .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));
  gap:10px;padding:6px clamp(14px,3vw,26px) 28px}
.pk .cell{position:relative;cursor:pointer;background:var(--surface);
  overflow:hidden;border:1px solid transparent;
  transition:border-color .2s}
.pk .cell img{object-position:var(--fit)}
.pk .cell:hover{border-color:var(--gold)}
.pk .cell.sel{border-color:var(--gold-bright);outline:1px solid var(--gold-bright)}
.pk .cell .lb{position:absolute;left:0;right:0;bottom:0;padding:16px 7px 5px;
  font-size:10px;letter-spacing:.1em;color:var(--ink);
  background:linear-gradient(180deg,rgba(19,16,14,0),rgba(19,16,14,.85))}
.pk .cell .cur{position:absolute;top:5px;left:5px;font-size:9px;
  letter-spacing:.16em;text-transform:uppercase;color:var(--ground);
  background:var(--gold);padding:2px 6px}
.pk .empty{padding:40px clamp(14px,3vw,26px);color:var(--dim);font-weight:300}

/* THE FOOT
   The picks leave by the clipboard: nothing here is saved to the site. */
.pk .foot{position:sticky;bottom:0;z-index:20;background:rgba(19,16,14,.97);
  border-top:1px solid var(--line);padding:12px clamp(14px,3vw,26px);
  display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.pk .foot button{background:var(--gold);border:none;border-radius:2px;
  color:var(--ground);font-family:var(--sans);font-weight:500;font-size:12px;
  letter-spacing:.16em;text-transform:uppercase;padding:13px 22px;cursor:pointer}
.pk .foot button.g{background:transparent;border:1px solid var(--line);
  color:var(--muted)}
.pk .foot .st{font-weight:300;font-size:13px;color:var(--muted)}
.pk .out{white-space:pre-wrap;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  font-size:12px;line-height:1.7;color:var(--muted);background:var(--surface);
  border:1px solid var(--line-soft);padding:14px;margin:0 clamp(14px,3vw,26px) 18px;
  display:none}
.pk .out.on{display:block}

@media (max-width:620px){
  .pk .ttl{font-size:16px}
  .pk .tab{font-size:10px;letter-spacing:.1em;padding:5px 10px 5px 5px}
  .pk .tab .th{width:34px;height:34px;flex:0 0 34px}
  .pk .grid{grid-template-columns:repeat(auto-fill,minmax(132px,1fr));gap:7px}
  .pk .prev .ph{max-height:62vh}
}
</style>

<div class="top">
  <p class="ttl">The Experience &middot; pick the photographs</p>
  <div class="tabs" id="tabs"></div>
</div>

<div class="prev" id="prev"></div>
<div class="cap"><b id="capn"></b><span id="capt"></span></div>

<div class="bar">
  <button class="f on" data-g="">Everything</button>
  <button class="f" data-g="Website folder">Website folder</button>
  <button class="f" data-g="galleries">Client galleries</button>
  <button class="f" data-g="Library">Rest of the library</button>
  <input id="q" type="search" placeholder="Filter by name or client…">
</div>
<div class="grid" id="grid"></div>
<pre class="out" id="out"></pre>

<div class="foot">
  <button id="copy">Copy my picks</button>
  <button class="g" id="show">Show them</button>
  <button class="g" id="reset">Start again</button>
  <span class="st" id="st"></span>
</div>

<script>
(() => {
  const D = @@DATA@@;
  const KEY = "jhp-exp-picks";
  let picks = {};
  try { picks = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) {}
  D.slots.forEach(s => { if (!picks[s.k]) picks[s.k] = D.current[s.k]; });
  let slot = D.slots[0], group = "", q = "";

  /* The one place that knows what shape the active slot is. Below the
     page's own 820 breakpoint it answers with the phone geometry, so the
     preview and every tile in the grid are cut the way the real page cuts
     them rather than the way a desktop would. */
  const geom = () => {
    if (window.innerWidth > 820)
      return { style: "aspect-ratio:" + slot.ratio,
               cell: "aspect-ratio:" + slot.ratio, fit: slot.fit };
    /* A band is a fixed height on a phone rather than a share of the
       width, and the preview has to be exactly that. The tiles must not
       be: 276 of them at 320px each is a forty-thousand-pixel scroll. So
       they take the same shape expressed as a ratio -- 390 wide over the
       height the band really is -- and come out small. */
    const r = slot.ph ? (390 / slot.ph) : (slot.pratio || slot.ratio);
    return { style: slot.ph ? "height:" + slot.ph + "px"
                            : "aspect-ratio:" + r,
             cell: "aspect-ratio:" + r,
             fit: slot.pfit || slot.fit };
  };

  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(picks)); }
                       catch (e) {} };
  const el = id => document.getElementById(id);
  const src = f => D.cdn + f;
  const meta = f => D.items.find(i => i[0] === f);

  /* The overlays are the real ones off the page, so the preview is a
     preview and not an impression of one. */
  const OVER = {
    intro: '<div class="o intro"><p class="k">The Experience</p>' +
      '<h2>What the Day Looks Like</h2><p class="sub">Every step, from the ' +
      'first message to the album in your hands. None of this should be a ' +
      'surprise.</p></div>',
    band: '<div class="o band"><p class="k">Ready when you are</p>' +
      '<h2>Let’s Talk About Your Session</h2><p class="sub">Fifteen ' +
      'minutes on the phone, and every question answered.</p>' +
      '<span class="btn">Book my call</span></div>',
    "": '<div class="o none"></div>'
  };

  function drawTabs() {
    el("tabs").innerHTML = D.slots.map(s =>
      '<button class="tab' + (s.k === slot.k ? ' on' : '') + '" data-k="' + s.k +
      '"><span class="th"><img src="' + src(picks[s.k]) + '" alt=""></span>' +
      s.n + '</button>').join("");
  }

  function drawPreview() {
    const f = picks[slot.k], m = meta(f);
    const gm = geom();
    el("prev").innerHTML =
      '<div class="ph" style="' + gm.style + ';--fit:' + gm.fit +
      '"><img src="' + src(f) + '" alt=""></div>' + OVER[slot.over];
    el("capn").textContent = m ? m[1] : "—";
    el("capt").textContent = (m ? m[2] + " · " : "") + slot.note;
  }

  function drawGrid() {
    const gm = geom();
    const rows = D.items.filter(i => {
      if (group === "galleries") { if (i[2] === "Website folder" ||
                                       i[2] === "Library") return false; }
      else if (group && i[2] !== group) return false;
      if (!q) return true;
      return (i[1] + " " + i[2]).toLowerCase().includes(q);
    });
    el("grid").innerHTML = rows.length ? rows.map(i =>
      '<button class="cell' + (i[0] === picks[slot.k] ? ' sel' : '') +
      '" data-f="' + i[0] + '" style="' + gm.cell + ';--fit:' +
      gm.fit + '"><img src="' + src(i[0]) + '" loading="lazy" alt="">' +
      (i[0] === D.current[slot.k] ? '<span class="cur">On the page</span>' : '') +
      '<span class="lb">' + i[1] + '</span></button>').join("")
      : '<p class="empty">Nothing matches that.</p>';
    el("st").textContent = rows.length + " of " + D.items.length + " frames";
  }

  const draw = () => { drawTabs(); drawPreview(); drawGrid(); };

  el("tabs").addEventListener("click", e => {
    const b = e.target.closest(".tab"); if (!b) return;
    slot = D.slots.find(s => s.k === b.dataset.k); draw();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
  el("grid").addEventListener("click", e => {
    const b = e.target.closest(".cell"); if (!b) return;
    picks[slot.k] = b.dataset.f; save(); draw();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
  document.querySelectorAll(".bar .f").forEach(b =>
    b.addEventListener("click", () => {
      group = b.dataset.g;
      document.querySelectorAll(".bar .f").forEach(x =>
        x.classList.toggle("on", x === b));
      drawGrid();
    }));
  el("q").addEventListener("input", e => {
    q = e.target.value.trim().toLowerCase(); drawGrid();
  });

  const text = () => D.slots.map(s => {
    const m = meta(picks[s.k]);
    return s.n + ": " + picks[s.k] + (m ? "   (" + m[1] + ", " + m[2] + ")" : "");
  }).join("\\n");

  el("show").addEventListener("click", () => {
    const o = el("out"); o.textContent = text(); o.classList.toggle("on");
  });
  el("copy").addEventListener("click", async () => {
    const t = text();
    try { await navigator.clipboard.writeText(t); el("st").textContent =
            "Copied — paste it to Claude."; }
    catch (e) { const o = el("out"); o.textContent = t; o.classList.add("on");
                el("st").textContent = "Select the text above and copy it."; }
  });
  el("reset").addEventListener("click", () => {
    picks = Object.assign({}, D.current); save(); draw();
    el("st").textContent = "Back to what is on the page now.";
  });

  /* Turning a phone sideways crosses the breakpoint, and a stale shape
     here is exactly the wrong thing for this page to be showing. */
  let wide = window.innerWidth > 820;
  window.addEventListener("resize", () => {
    const now = window.innerWidth > 820;
    if (now !== wide) { wide = now; drawPreview(); drawGrid(); }
  });

  draw();
})();
</script>
</div>
{% endraw %}
</body>
</html>
""".replace("@@DATA@@", DATA)

(ROOT / "scalogy-exp-picker.html").write_text(HTML)
print("wrote", len(HTML.encode()), "bytes,", len(items), "frames,",
      len(SLOTS), "slots")
