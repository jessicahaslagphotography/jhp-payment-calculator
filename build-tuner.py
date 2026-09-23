#!/usr/bin/env python3
"""Generates scalogy-band-tuner.html -- the tool Jessica crops with.

Three rounds of "move it up a bit" went through me, which is two too many.
This puts the two photographic bands on the Portfolio page in her hands:
pick the frame from her own library, drag the crop, see the real headline
sitting on it at both a desktop and a phone width, and copy out numbers I
can apply in a minute.

The preview is a scale model, not an approximation. The band is drawn at
its true pixel size inside a wrapper that CSS-scales the whole thing, type
included, so cover crops exactly as it will on the page.

Heights are kept in the units the page uses: a share of the screen width
on a desktop, which is the vw in the CSS, and flat pixels on a phone.
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
CDN = "https://assets.cdn.filesafe.space/Pcnm8GVNMmWTY65qVOAp/media/"


def groups():
    """Every landscape frame in the library, grouped the way she thinks."""
    out = []
    pools = json.loads((ROOT / "picker-pools.json").read_text())
    dims = {d["f"]: (d["w"], d["h"])
            for d in json.loads((ROOT / "assets/pick/index.json").read_text())}
    site = [[f, lb] for f, lb, *used in pools["site"]
            if not used and dims.get(lb + ".jpg", (0, 1))[0]
            > dims.get(lb + ".jpg", (0, 1))[1]]
    out.append({"name": "Website folder", "items": site})
    for g in json.loads((ROOT / "galleries.json").read_text()):
        wide = [[f, lb] for f, lb, w, h in g["photos"] if w > h]
        if wide:
            out.append({"name": g["name"] + " — " + g["slug"][10:],
                        "items": wide})
    return out


BANDS = [
    {"id": "top", "label": "Top of the page",
     "file": "6ab3ee808d8128ee4caa5fd3.jpg", "name": "DSC_4553-BW",
     "def": {"dw": 37, "dx": 50, "dy": 34, "ph": 340, "px": 50, "py": 30},
     "kicker": "Portfolio", "title": "Take a look at the ones who came before you",
     "align": "center"},
    {"id": "info", "label": "The Info band",
     "file": "6ab3ee7718384d888bb3d80d.jpg", "name": "DSC_2043",
     "def": {"dw": 34, "dx": 50, "dy": 22, "ph": 320, "px": 50, "py": 22},
     "kicker": "What’s included", "title": "What Your Session Includes",
     "sub": "From the first call to the final reveal.", "cta": "Learn more",
     "align": "left"},
]

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Band Tuner | JHP Boudoir</title>
<meta name="robots" content="noindex, nofollow">
<style>html,body{margin:0;padding:0;background:#13100E}body{overflow-x:hidden}</style>
</head>
<body>
<div class="tn">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500&family=Jost:wght@300;400;500&display=swap');
.tn{--ground:#13100E;--surface:#1C1714;--raised:#241D18;--ink:#F2ECE2;
  --muted:#A99A86;--dim:#7D7161;--gold:#C9A24B;--gold-bright:#E6C576;
  --line:rgba(201,162,75,.22);--line-soft:rgba(242,236,226,.09);
  --serif:'Cormorant Garamond',Georgia,serif;
  --sans:'Jost',-apple-system,'Segoe UI',system-ui,sans-serif;
  background:var(--ground);color:var(--ink);font-family:var(--sans);
  font-size:16px;line-height:1.5;-webkit-font-smoothing:antialiased;
  min-height:100vh;padding-bottom:40px}
.tn *,.tn *::before,.tn *::after{box-sizing:border-box}
.tn h1,.tn h2,.tn p{margin:0}
.tn .head{text-align:center;padding:26px 20px 18px}
.tn .head .k{font-size:11px;letter-spacing:.3em;text-transform:uppercase;
  color:var(--gold)}
.tn .head h1{font-family:var(--serif);font-weight:500;font-size:34px;
  line-height:1.1;margin:8px 0 0}
.tn .head p{font-size:13.5px;color:var(--muted);margin-top:8px;
  max-width:46ch;margin-inline:auto}
.tn .switch{display:flex;justify-content:center;gap:8px;flex-wrap:wrap;
  padding:0 16px 14px}
.tn .switch button{font-family:var(--sans);font-size:11px;letter-spacing:.2em;
  text-transform:uppercase;color:var(--muted);background:transparent;
  border:1px solid var(--line-soft);border-radius:2px;padding:10px 16px;
  cursor:pointer;transition:all .25s}
.tn .switch button[aria-pressed=true]{color:var(--ground);background:var(--gold);
  border-color:var(--gold)}
.tn .wrap{max-width:1180px;margin:0 auto;padding:0 16px}
.tn .stage{position:relative;overflow:hidden;background:var(--raised);
  border:1px solid var(--line-soft);cursor:grab;touch-action:none;
  margin:0 auto}
.tn .stage.drag{cursor:grabbing}
.tn .frame{position:absolute;top:0;left:0;transform-origin:top left;
  overflow:hidden}
.tn .frame img{position:absolute;inset:0;width:100%;height:100%;
  object-fit:cover;display:block;filter:saturate(.96) contrast(1.02);
  pointer-events:none;-webkit-user-drag:none;user-select:none}
.tn .over{position:absolute;inset:0;display:flex;flex-direction:column;
  pointer-events:none}
.tn .over.center{align-items:center;justify-content:flex-end;text-align:center;
  padding:0 60px 46px;
  background:linear-gradient(0deg,rgba(19,16,14,.94) 0%,rgba(19,16,14,.78) 24%,
    rgba(19,16,14,.34) 52%,rgba(19,16,14,.04) 82%)}
.tn .over.left{align-items:flex-start;justify-content:center;text-align:left;
  padding:0 74px;
  background:linear-gradient(0deg,rgba(19,16,14,.8) 0%,rgba(19,16,14,.42) 55%,
      rgba(19,16,14,.3) 100%),
    linear-gradient(90deg,rgba(19,16,14,.72) 0%,rgba(19,16,14,.34) 38%,
      rgba(19,16,14,0) 68%)}
.tn .over .ek{font-family:var(--sans);font-size:11px;letter-spacing:.3em;
  text-transform:uppercase;color:var(--gold);margin-bottom:12px}
.tn .over .tt{font-family:var(--serif);font-weight:500;font-size:46px;
  line-height:1.1;max-width:24ch}
.tn .over.left .tt{max-width:17ch;margin-bottom:8px}
.tn .over .sub{font-family:var(--sans);font-weight:300;font-size:15.5px;
  color:var(--muted);margin-bottom:22px}
.tn .over .btn{align-self:flex-start;font-family:var(--sans);font-weight:500;
  font-size:13px;letter-spacing:.18em;text-transform:uppercase;
  color:var(--ground);background:var(--gold);padding:14px 28px;border-radius:2px}
.tn .hint{position:absolute;left:50%;top:14px;transform:translateX(-50%);
  font-size:11px;letter-spacing:.18em;text-transform:uppercase;
  color:var(--ink);background:rgba(19,16,14,.6);padding:7px 13px;
  border-radius:2px;pointer-events:none;transition:opacity .4s;z-index:3}
.tn .ctl{max-width:620px;margin:20px auto 0;padding:0 16px}
.tn .row{margin-bottom:16px}
.tn .lab{display:flex;justify-content:space-between;font-size:11px;
  letter-spacing:.2em;text-transform:uppercase;color:var(--muted);
  margin-bottom:8px}
.tn .lab span:last-child{color:var(--gold);letter-spacing:.08em}
.tn input[type=range]{-webkit-appearance:none;appearance:none;width:100%;
  background:transparent;margin:0;height:30px}
.tn input[type=range]::-webkit-slider-runnable-track{height:2px;
  background:var(--line)}
.tn input[type=range]::-moz-range-track{height:2px;background:var(--line)}
.tn input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:30px;
  height:30px;border-radius:50%;background:var(--gold);border:none;
  margin-top:-14px}
.tn input[type=range]::-moz-range-thumb{width:30px;height:30px;border:none;
  border-radius:50%;background:var(--gold)}
.tn .note{font-size:11.5px;color:var(--dim);margin-top:6px}
.tn .acts{display:flex;gap:10px;margin:22px 0 18px}
.tn .acts button{flex:1;font-family:var(--sans);font-size:12px;
  letter-spacing:.18em;text-transform:uppercase;padding:15px 10px;
  border-radius:2px;cursor:pointer;border:1px solid var(--gold)}
.tn .send{color:var(--ground);background:var(--gold)}
.tn .ghost{color:var(--gold);background:transparent}
.tn .out{border:1px solid var(--line-soft);border-radius:2px;
  background:var(--surface);padding:14px 15px}
.tn .out .t{font-size:10.5px;letter-spacing:.22em;text-transform:uppercase;
  color:var(--gold);margin-bottom:8px}
.tn pre{margin:0;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  font-size:11.5px;line-height:1.75;color:var(--muted);white-space:pre-wrap}
.tn .pick{max-width:1180px;margin:26px auto 0;padding:0 16px}
.tn .pick h2{font-family:var(--serif);font-weight:500;font-size:24px;
  margin-bottom:10px}
.tn select{font-family:var(--sans);font-size:14px;color:var(--ink);
  background:var(--raised);border:1px solid var(--line);border-radius:2px;
  padding:11px 12px;width:100%;max-width:420px}
.tn .strip{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));
  gap:10px;margin-top:14px}
.tn .strip button{position:relative;padding:0;border:1px solid transparent;
  background:var(--raised);border-radius:2px;overflow:hidden;cursor:pointer;
  aspect-ratio:3/2}
.tn .strip button[aria-pressed=true]{border-color:var(--gold)}
.tn .strip img{width:100%;height:100%;object-fit:cover;display:block}
.tn .strip .nm{position:absolute;left:0;right:0;bottom:0;font-family:var(--sans);
  font-size:10px;letter-spacing:.1em;color:var(--ink);padding:14px 6px 5px;
  background:linear-gradient(180deg,rgba(19,16,14,0),rgba(19,16,14,.8))}
.tn .foot{text-align:center;font-size:11.5px;color:var(--dim);padding:30px 20px 0}
.tn .foot a{color:var(--gold)}
@media (prefers-reduced-motion:reduce){.tn *{transition:none!important}}
</style>

<div class="head">
  <p class="k">JHP Boudoir</p>
  <h1>Band Tuner</h1>
  <p>The two photographs on the Portfolio page. Pick a frame, drag it to move
     it, and slide to change the height. The words on top are the real ones,
     at the real size, so what you see is what the page does. Then tap
     <em>Copy settings</em> and paste it to me.</p>
</div>

<div class="switch" id="bandSw"></div>
<div class="switch" id="viewSw">
  <button data-v="desktop" aria-pressed="true">Desktop</button>
  <button data-v="phone" aria-pressed="false">Phone</button>
</div>

<div class="wrap">
  <div class="stage" id="stage">
    <div class="hint" id="hint">Drag the photograph</div>
    <div class="frame" id="frame"><img id="img" alt=""><div class="over" id="over"></div></div>
  </div>
</div>

<div class="ctl">
  <div class="row">
    <div class="lab"><span>Height</span><span id="vH">&mdash;</span></div>
    <input type="range" id="sH" aria-label="Height">
    <p class="note" id="nH"></p>
  </div>
  <div class="row">
    <div class="lab"><span>Left &ndash; right</span><span id="vX">&mdash;</span></div>
    <input type="range" id="sX" min="0" max="100" step="1" aria-label="Across">
    <p class="note" id="nX"></p>
  </div>
  <div class="row">
    <div class="lab"><span>Up &ndash; down</span><span id="vY">&mdash;</span></div>
    <input type="range" id="sY" min="0" max="100" step="1" aria-label="Up and down">
    <p class="note" id="nY"></p>
  </div>
  <div class="acts">
    <button class="send" id="copy">Copy settings</button>
    <button class="ghost" id="reset">Reset this band</button>
  </div>
  <div class="out">
    <div class="t">What I will apply</div>
    <pre id="out"></pre>
  </div>
</div>

<div class="pick">
  <h2>Choose the photograph</h2>
  <select id="grp" aria-label="Which set of photographs"></select>
  <div class="strip" id="strip"></div>
</div>

<p class="foot">Your changes are remembered on this device.<br>
  <a href="../portfolio/">The Portfolio page</a></p>

<script>
(function(){
var CDN = '@@CDN@@';
var BANDS = @@BANDS@@;
var GROUPS = @@GROUPS@@;
var KEY = 'jhp-band-tuner-v1';

var state = {};
try { state = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch(e){}
BANDS.forEach(function(b){
  if (!state[b.id]) state[b.id] = {file:b.file, name:b.name,
    dw:b.def.dw, dx:b.def.dx, dy:b.def.dy,
    ph:b.def.ph, px:b.def.px, py:b.def.py};
});
var save = function(){ try{ localStorage.setItem(KEY, JSON.stringify(state)); }catch(e){} };

var $ = function(id){ return document.getElementById(id); };
var band = BANDS[0], view = 'desktop';
/* 1440 is the laptop the page is usually judged on; 390 is her phone. The
   preview is drawn at those widths and scaled down to fit, so nothing here
   is an approximation of the crop -- only of the screen. */
var REAL = {desktop:1440, phone:390};

function st(){ return state[band.id]; }
function isDesk(){ return view === 'desktop'; }
function heightPx(){
  var s = st();
  if (!isDesk()) return s.ph;
  return Math.max(320, Math.min(600, REAL.desktop * s.dw / 100));
}
function pos(){ var s = st(); return isDesk() ? [s.dx, s.dy] : [s.px, s.py]; }
function setPos(x, y){
  var s = st();
  if (isDesk()) { s.dx = x; s.dy = y; } else { s.px = x; s.py = y; }
}

function draw(){
  var s = st(), W = REAL[view], H = heightPx();
  var avail = $('stage').parentNode.clientWidth - 32;
  var scale = Math.min(1, avail / W);
  $('stage').style.width = Math.round(W * scale) + 'px';
  $('stage').style.height = Math.round(H * scale) + 'px';
  var f = $('frame');
  f.style.width = W + 'px'; f.style.height = H + 'px';
  f.style.transform = 'scale(' + scale + ')';
  $('img').src = CDN + s.file;
  var p = pos();
  $('img').style.objectPosition = p[0] + '% ' + p[1] + '%';

  var o = $('over');
  o.className = 'over ' + band.align;
  var html = '<p class="ek">' + band.kicker + '</p>' +
             '<p class="tt">' + band.title + '</p>';
  if (band.sub) html += '<p class="sub">' + band.sub + '</p>';
  if (band.cta) html += '<span class="btn">' + band.cta + '</span>';
  o.innerHTML = html;

  $('sH').min = isDesk() ? 20 : 220;
  $('sH').max = isDesk() ? 55 : 560;
  $('sH').step = 1;
  $('sH').value = isDesk() ? s.dw : s.ph;
  $('vH').textContent = isDesk()
    ? s.dw + '% of the screen (' + Math.round(H) + 'px here)'
    : s.ph + 'px';
  $('sX').value = p[0]; $('vX').textContent = p[0] + '%';
  $('sY').value = p[1]; $('vY').textContent = p[1] + '%';
  notes(W, H);
  out();
}

/* How much room the crop actually has. A frame wider than its box only
   moves sideways; one taller than its box only moves up and down. Saying
   so stops a slider that does nothing from looking broken. */
function notes(W, H){
  var im = $('img');
  var iw = im.naturalWidth, ih = im.naturalHeight;
  if (!iw) { $('nX').textContent = $('nY').textContent = ''; return; }
  var sc = Math.max(W / iw, H / ih);
  var ox = Math.round(iw * sc - W), oy = Math.round(ih * sc - H);
  $('nH').textContent = isDesk()
    ? 'A share of the screen width, which is what the page uses.'
    : 'A flat height, the way the page sets it on a phone.';
  $('nX').textContent = ox > 2
    ? Math.round(ox) + 'px of the photograph is off the sides here.'
    : 'Nothing to move sideways at this height.';
  $('nY').textContent = oy > 2
    ? Math.round(oy) + 'px of the photograph is off the top and bottom.'
    : 'Nothing to move up or down at this height.';
}

function out(){
  var t = [];
  BANDS.forEach(function(b){
    var s = state[b.id];
    t.push(b.label.toUpperCase());
    t.push('  photo: ' + s.name + '  [' + s.file + ']');
    t.push('  desktop: height ' + s.dw + '% of width, crop ' + s.dx +
           '% across / ' + s.dy + '% down');
    t.push('  phone:   height ' + s.ph + 'px, crop ' + s.px +
           '% across / ' + s.py + '% down');
  });
  $('out').textContent = t.join('\\n');
}

/* Drag. The pointer moves in screen pixels, the crop moves in percent of
   whatever is hanging off the edge, and the preview is scaled -- so the
   delta is divided by the scale before it is turned into percent. */
var drag = null;
$('stage').addEventListener('pointerdown', function(e){
  var im = $('img'), W = REAL[view], H = heightPx();
  var sc = Math.max(W / im.naturalWidth, H / im.naturalHeight);
  var p = pos();
  drag = {x:e.clientX, y:e.clientY, px:p[0], py:p[1],
          ox:im.naturalWidth * sc - W, oy:im.naturalHeight * sc - H,
          s:Math.min(1, ($('stage').parentNode.clientWidth - 32) / W)};
  $('stage').setPointerCapture(e.pointerId);
  $('stage').classList.add('drag');
  $('hint').style.opacity = 0;
});
$('stage').addEventListener('pointermove', function(e){
  if (!drag) return;
  var dx = (e.clientX - drag.x) / drag.s, dy = (e.clientY - drag.y) / drag.s;
  var nx = drag.ox > 2 ? drag.px - dx / drag.ox * 100 : drag.px;
  var ny = drag.oy > 2 ? drag.py - dy / drag.oy * 100 : drag.py;
  setPos(Math.max(0, Math.min(100, Math.round(nx))),
         Math.max(0, Math.min(100, Math.round(ny))));
  save(); draw();
});
['pointerup','pointercancel'].forEach(function(ev){
  $('stage').addEventListener(ev, function(){ drag = null;
    $('stage').classList.remove('drag'); });
});

$('sH').addEventListener('input', function(){
  var v = +this.value; if (isDesk()) st().dw = v; else st().ph = v;
  save(); draw();
});
$('sX').addEventListener('input', function(){
  var p = pos(); setPos(+this.value, p[1]); save(); draw();
});
$('sY').addEventListener('input', function(){
  var p = pos(); setPos(p[0], +this.value); save(); draw();
});
$('reset').addEventListener('click', function(){
  state[band.id] = {file:band.file, name:band.name, dw:band.def.dw,
    dx:band.def.dx, dy:band.def.dy, ph:band.def.ph, px:band.def.px,
    py:band.def.py};
  save(); draw(); strip();
});
$('copy').addEventListener('click', function(){
  var txt = $('out').textContent, b = this;
  var done = function(){ b.textContent = 'Copied'; setTimeout(function(){
    b.textContent = 'Copy settings'; }, 1600); };
  if (navigator.clipboard) navigator.clipboard.writeText(txt).then(done, done);
  else { var t = document.createElement('textarea'); t.value = txt;
    document.body.appendChild(t); t.select(); document.execCommand('copy');
    document.body.removeChild(t); done(); }
});

var sw = $('bandSw');
BANDS.forEach(function(b, i){
  var el = document.createElement('button');
  el.textContent = b.label;
  el.setAttribute('aria-pressed', i === 0 ? 'true' : 'false');
  el.addEventListener('click', function(){
    band = b;
    [].forEach.call(sw.children, function(c){
      c.setAttribute('aria-pressed', c === el ? 'true' : 'false'); });
    draw(); strip();
  });
  sw.appendChild(el);
});
[].forEach.call($('viewSw').children, function(el){
  el.addEventListener('click', function(){
    view = el.dataset.v;
    [].forEach.call($('viewSw').children, function(c){
      c.setAttribute('aria-pressed', c === el ? 'true' : 'false'); });
    draw();
  });
});

GROUPS.forEach(function(g, i){
  var op = document.createElement('option');
  op.value = i; op.textContent = g.name + ' (' + g.items.length + ')';
  $('grp').appendChild(op);
});
function strip(){
  var g = GROUPS[+$('grp').value || 0], host = $('strip');
  host.innerHTML = '';
  g.items.forEach(function(it){
    var b = document.createElement('button');
    b.setAttribute('aria-pressed', it[0] === st().file ? 'true' : 'false');
    b.innerHTML = '<img loading="lazy" src="' + CDN + it[0] + '" alt="">' +
                  '<span class="nm">' + it[1] + '</span>';
    b.addEventListener('click', function(){
      st().file = it[0]; st().name = it[1]; save(); draw(); strip();
    });
    host.appendChild(b);
  });
}
$('grp').addEventListener('change', strip);

$('img').addEventListener('load', function(){ notes(REAL[view], heightPx()); });
window.addEventListener('resize', draw);
draw(); strip();
})();
</script>
</div>
</body>
</html>
"""


def main():
    # str.replace rather than %-formatting: the CSS is full of per-cent
    # signs and every one of them would have to be doubled.
    # ensure_ascii=False so an em dash is an em dash: the published template
    # holds the character, and the mirror has to match it byte for byte or
    # the size check stops meaning anything.
    dump = lambda o: json.dumps(o, separators=(",", ":"), ensure_ascii=False)
    body = (HTML.replace("@@CDN@@", CDN)
                .replace("@@BANDS@@", dump(BANDS))
                .replace("@@GROUPS@@", dump(groups())))
    (ROOT / "scalogy-band-tuner.html").write_text(body)
    n = sum(len(g["items"]) for g in groups())
    print("wrote", len(body.encode()), "bytes,", n, "frames to choose from")


main()
