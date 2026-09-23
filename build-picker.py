#!/usr/bin/env python3
"""Generates scalogy-picker.html — the twelve-image portfolio picker.

Every candidate comes from Jessica's own GHL media library at full
resolution: her Website folder first, the rest of the library second.
Which ones the live home and about pages already use was read off those
pages, not remembered, so the badge cannot drift.

The picker is self-contained: selection lives in localStorage and leaves
by the clipboard, because a page-api token only lives fifteen minutes and
choosing twelve takes longer than that.
"""
import json, pathlib

ROOT = pathlib.Path("/home/user/jhp-payment-calculator")

POOLS_RAW = json.loads((ROOT
                        / "picker-pools.json").read_text())

GHL = "https://assets.cdn.filesafe.space/Pcnm8GVNMmWTY65qVOAp/media/"


def order(rows):
    """Anything the site already uses sinks to the bottom of its tab."""
    return sorted(rows, key=lambda r: (len(r) > 2, r[1].lower()))


POOLS = [
    {"key": "w", "title": "Website folder", "base": GHL,
     "items": order(POOLS_RAW["site"])},
    {"key": "l", "title": "Rest of the library", "base": GHL,
     "items": order(POOLS_RAW["rest"])},
]

data = json.dumps(POOLS, separators=(",", ":"))

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Pick your twelve | JHP Boudoir</title>
<meta name="robots" content="noindex, nofollow">
<style>html,body{margin:0;padding:0;background:#13100E}body{overflow-x:hidden}</style>
</head>
<body>
{% raw %}
<div class="pk">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500&family=Jost:wght@300;400;500&display=swap');

.pk{--ground:#13100E;--surface:#1C1714;--ink:#F2ECE2;--muted:#A99A86;--dim:#7D7161;
  --gold:#C9A24B;--gold-bright:#E6C576;
  --line:rgba(201,162,75,.22);--line-soft:rgba(242,236,226,.10);
  --serif:'Cormorant Garamond',Georgia,serif;
  --sans:'Jost',-apple-system,'Segoe UI',system-ui,sans-serif;
  background:var(--ground);color:var(--ink);font-family:var(--sans);
  font-size:16px;line-height:1.5;-webkit-font-smoothing:antialiased;
  min-height:100vh;overflow-x:hidden;padding-bottom:96px}
.pk *,.pk *::before,.pk *::after{box-sizing:border-box}
.pk h1,.pk h2,.pk p{margin:0}

.pk .head{padding:18px 20px 14px;text-align:center}
.pk .head .k{font-size:10px;letter-spacing:.3em;text-transform:uppercase;
  color:var(--gold);margin-bottom:6px}
.pk .head h1{font-family:var(--serif);font-weight:500;font-size:28px}
.pk .head p{font-size:13px;color:var(--muted);margin-top:8px;line-height:1.6;
  max-width:52ch;margin-left:auto;margin-right:auto}

/* The shape control. Four rows of three is a fixed grid, so every frame has
   to be cut to one shape -- she chooses which, and sees it applied live. */
.pk .shape{display:flex;justify-content:center;gap:0;padding:6px 20px 0}
.pk .shape button{font-family:var(--sans);font-size:10.5px;letter-spacing:.18em;
  text-transform:uppercase;color:var(--muted);background:transparent;
  border:1px solid var(--line-soft);padding:11px 14px;cursor:pointer;
  transition:all .25s;-webkit-tap-highlight-color:transparent}
.pk .shape button+button{border-left:none}
.pk .shape button:first-child{border-radius:2px 0 0 2px}
.pk .shape button:last-child{border-radius:0 2px 2px 0}
.pk .shape button.on{color:var(--ground);background:var(--gold);
  border-color:var(--gold)}

/* Which pool of photographs we are looking through. */
.pk .tabs{display:flex;justify-content:center;gap:26px;padding:20px 20px 0;
  border-bottom:1px solid var(--line-soft);margin:16px 16px 0}
.pk .tabs button{font-family:var(--sans);font-size:11px;letter-spacing:.2em;
  text-transform:uppercase;color:var(--dim);background:transparent;border:none;
  border-bottom:2px solid transparent;padding:0 2px 12px;cursor:pointer;
  transition:all .25s;-webkit-tap-highlight-color:transparent}
.pk .tabs button.on{color:var(--gold-bright);border-bottom-color:var(--gold)}

.pk .note{max-width:52ch;margin:14px auto 0;padding:0 20px;font-size:12px;
  color:var(--dim);line-height:1.6;text-align:center}
.pk .filter{text-align:center;margin-top:10px}
.pk .filter label{font-size:11px;letter-spacing:.1em;color:var(--muted);
  cursor:pointer;display:inline-flex;align-items:center;gap:7px;
  -webkit-tap-highlight-color:transparent}
.pk .filter input{accent-color:var(--gold);width:15px;height:15px;margin:0}

/* The contact sheet. Whole frames, uncropped, so she is choosing the
   photograph and not a crop of it. */
.pk .sheet{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));
  gap:10px;padding:18px 16px 0;max-width:1240px;margin:0 auto}
.pk .cell{position:relative;background:var(--surface);border:1px solid transparent;
  cursor:pointer;padding:0;overflow:hidden;-webkit-tap-highlight-color:transparent;
  transition:border-color .2s,transform .2s;display:block;width:100%}
.pk .cell img{display:block;width:100%;height:190px;object-fit:contain;
  background:#0D0B09}
.pk .cell .nm{font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;
  color:var(--dim);padding:7px 8px;text-align:center;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pk .cell.on{border-color:var(--gold)}
.pk .cell.on img{opacity:.72}
.pk .cell .num{position:absolute;top:8px;left:8px;width:26px;height:26px;
  border-radius:50%;background:var(--gold);color:var(--ground);font-size:12px;
  font-weight:500;display:none;align-items:center;justify-content:center;
  letter-spacing:0}
.pk .cell.on .num{display:flex}
.pk .cell.full{opacity:.38}
/* Placed photographs stay reachable but say so, and sink to the bottom
   of their tab. The toggle above the sheet hides them outright. */
.pk .cell.placed img{opacity:.42}
.pk .cell.placed.on img{opacity:.72}
.pk .cell .where{position:absolute;top:8px;right:8px;font-size:8px;
  letter-spacing:.14em;text-transform:uppercase;color:var(--ground);
  background:var(--muted);padding:3px 6px;border-radius:2px}

/* The twelve, laid out the way the portfolio will lay them out. */
.pk .chosen{padding:26px 16px 0;max-width:520px;margin:0 auto;
  transition:max-width .3s}
.pk .chosen.big{max-width:1040px}
.pk .chosen h2{font-family:var(--serif);font-weight:500;font-size:22px;
  text-align:center;margin-bottom:4px}
.pk .chosen .sub{font-size:12px;color:var(--dim);text-align:center;
  margin-bottom:10px}
.pk .zoom{text-align:center;margin-bottom:16px}
.pk .zoom button{font-family:var(--sans);font-size:10px;letter-spacing:.2em;
  text-transform:uppercase;color:var(--dim);background:transparent;border:none;
  border-bottom:1px solid var(--line-soft);padding:2px 0 3px;cursor:pointer;
  -webkit-tap-highlight-color:transparent}
.pk .zoom button:hover{color:var(--gold-bright);border-bottom-color:var(--gold)}
.pk .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.pk .slot{position:relative;background:var(--surface);
  border:1px dashed var(--line-soft);overflow:hidden}
.pk .slot img{display:block;width:100%;height:100%;object-fit:cover;
  position:absolute;inset:0}
.pk .slot .bar{position:absolute;left:0;right:0;bottom:0;display:flex;
  background:rgba(13,11,9,.72);opacity:0;transition:opacity .2s}
.pk .slot:hover .bar,.pk .slot:focus-within .bar{opacity:1}
.pk .slot .bar button{flex:1;background:transparent;border:none;color:var(--ink);
  font-size:13px;padding:7px 0;cursor:pointer;
  -webkit-tap-highlight-color:transparent}
.pk .slot .bar button:hover{background:rgba(201,162,75,.22)}
.pk .slot .idx{position:absolute;top:6px;left:6px;font-size:10px;
  letter-spacing:.1em;color:var(--dim);z-index:1}
.pk .slot.empty::after{content:attr(data-n);position:absolute;inset:0;
  display:flex;align-items:center;justify-content:center;
  font-family:var(--serif);font-size:26px;color:rgba(242,236,226,.14)}
@media (max-width:620px){
  .pk .slot .bar{opacity:1}
  .pk .sheet{grid-template-columns:repeat(2,1fr);gap:8px;padding:16px 12px 0}
  .pk .cell img{height:150px}
  .pk .tabs{gap:18px}
}

/* Everything she needs to finish sits on screen, always. */
.pk .bar-fixed{position:fixed;left:0;right:0;bottom:0;z-index:20;
  background:rgba(19,16,14,.94);backdrop-filter:blur(8px);
  border-top:1px solid var(--line);padding:12px 16px;
  display:flex;align-items:center;justify-content:center;gap:12px;flex-wrap:wrap}
.pk .count{font-size:11px;letter-spacing:.2em;text-transform:uppercase;
  color:var(--muted)}
.pk .count b{color:var(--gold-bright);font-weight:500}
.pk .count.flash{animation:pkflash .5s ease}
@keyframes pkflash{0%,100%{transform:translateX(0)}
  25%{transform:translateX(-5px)}75%{transform:translateX(5px)}}
.pk .bar-fixed button{font-family:var(--sans);font-size:10.5px;letter-spacing:.2em;
  text-transform:uppercase;padding:12px 20px;cursor:pointer;border-radius:2px;
  transition:all .25s;-webkit-tap-highlight-color:transparent}
.pk .go{background:var(--gold);color:var(--ground);border:1px solid var(--gold)}
.pk .go:disabled{background:transparent;color:var(--dim);
  border-color:var(--line-soft);cursor:default}
.pk .ghost{background:transparent;color:var(--muted);border:1px solid var(--line-soft)}
.pk .ghost:hover{color:var(--ink);border-color:var(--line)}

.pk .out{max-width:760px;margin:22px auto 0;padding:0 16px}
.pk .out textarea{width:100%;height:230px;background:var(--surface);
  color:var(--ink);border:1px solid var(--line-soft);border-radius:2px;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;
  line-height:1.6;padding:12px;resize:vertical}
.pk .out.hide{display:none}
</style>

<div class="head">
  <div class="k">Portfolio</div>
  <h1>Pick your twelve</h1>
  <p>Tap twelve photographs and they fill the grid below in the order you tap
     them. Four rows of three means every frame gets cut to one shape &mdash;
     choose the shape first, and the grid shows you the real cut.</p>
</div>

<div class="shape" id="shape"></div>

<div class="chosen">
  <h2>Your portfolio</h2>
  <div class="sub" id="sub">Nothing chosen yet</div>
  <div class="zoom"><button id="zoom">See them bigger</button></div>
  <div class="grid" id="grid"></div>
</div>

<div class="tabs" id="tabs"></div>
<div class="note" id="note"></div>
<div class="filter"><label>
  <input type="checkbox" id="hide" checked>
  Hide the ones already on your home or about page
</label></div>
<div class="sheet" id="sheet"></div>

<div class="out hide" id="out">
  <textarea id="txt" readonly></textarea>
</div>

<div class="bar-fixed">
  <div class="count" id="cnt"><b id="n">0</b> of 12</div>
  <button class="go" id="copy" disabled>Copy my picks</button>
  <button class="ghost" id="clear">Start over</button>
</div>
</div>

<script>
(function(){
  var POOLS = __DATA__;
  var SHAPES = [
    {key:'tall',  label:'Tall 4:5',   pct:125},
    {key:'square',label:'Square',     pct:100},
    {key:'wide',  label:'Wide 3:2',   pct:66.667}
  ];
  var NOTES = {
    w:'User Uploads / Website \u2014 77 photographs, full resolution.',
    l:'Everything else in your media library, including the six in ' +
      'Relocated Item.'
  };
  var KEY = 'jhp-portfolio-pick';
  var ALL = {};
  POOLS.forEach(function(p){
    p.items = p.items.map(function(row){
      var it = {id: p.key + ':' + row[0], label: row[1],
                url: p.base + row[0], on: row[2] || ''};
      ALL[it.id] = it;
      return it;
    });
  });

  var st = {pool:POOLS[0].key, shape:'tall', hide:true, picks:[]};
  try {
    var saved = JSON.parse(localStorage.getItem(KEY) || 'null');
    if (saved && saved.picks) {
      st.shape = saved.shape || st.shape;
      if (typeof saved.hide === 'boolean') st.hide = saved.hide;
      // Drop anything that is no longer in either pool, so a stale save
      // cannot leave her staring at a broken frame.
      st.picks = saved.picks.filter(function(id){ return ALL[id]; }).slice(0,12);
    }
  } catch(e){}
  function save(){
    try { localStorage.setItem(KEY, JSON.stringify(st)); } catch(e){}
  }

  var el = function(id){ return document.getElementById(id); };

  function shapePct(){
    for (var i=0;i<SHAPES.length;i++) if (SHAPES[i].key===st.shape) return SHAPES[i].pct;
    return 125;
  }

  function drawShape(){
    var box = el('shape'); box.innerHTML = '';
    SHAPES.forEach(function(s){
      var b = document.createElement('button');
      b.textContent = s.label;
      if (s.key === st.shape) b.className = 'on';
      b.onclick = function(){ st.shape = s.key; save(); drawShape(); drawGrid(); };
      box.appendChild(b);
    });
  }

  function visible(p){
    return p.items.filter(function(it){
      // A placed photograph she has already chosen never disappears
      // underneath her, whatever the toggle says.
      return !(st.hide && it.on) || st.picks.indexOf(it.id) >= 0;
    });
  }

  function drawTabs(){
    var box = el('tabs'); box.innerHTML = '';
    POOLS.forEach(function(p){
      var b = document.createElement('button');
      b.textContent = p.title + ' (' + visible(p).length + ')';
      if (p.key === st.pool) b.className = 'on';
      b.onclick = function(){ st.pool = p.key; drawTabs(); drawSheet(); };
      box.appendChild(b);
    });
    el('note').textContent = NOTES[st.pool] || '';
    el('hide').checked = st.hide;
  }

  function drawSheet(){
    var pool = POOLS.filter(function(p){ return p.key === st.pool; })[0];
    var box = el('sheet'); box.innerHTML = '';
    var full = st.picks.length >= 12;
    visible(pool).forEach(function(it){
      var pos = st.picks.indexOf(it.id);
      var c = document.createElement('button');
      c.className = 'cell' + (pos >= 0 ? ' on' : (full ? ' full' : ''));
      if (it.on) c.className += ' placed';
      c.innerHTML = '<span class="num">' + (pos + 1) + '</span>' +
        (it.on ? '<span class="where">On ' + it.on + '</span>' : '') +
        '<img loading="lazy" src="' + it.url + '" alt="">' +
        '<div class="nm">' + it.label + '</div>';
      c.onclick = function(){ toggle(it.id); };
      box.appendChild(c);
    });
  }

  function toggle(id){
    var pos = st.picks.indexOf(id);
    if (pos >= 0) st.picks.splice(pos, 1);
    else if (st.picks.length < 12) st.picks.push(id);
    else {
      // Twelve already. Say so instead of swallowing the tap.
      var c = el('cnt'); c.className = 'count';
      void c.offsetWidth; c.className = 'count flash';
      return;
    }
    save(); drawTabs(); drawSheet(); drawGrid();
  }

  function move(i, d){
    var j = i + d;
    if (j < 0 || j >= st.picks.length) return;
    var t = st.picks[i]; st.picks[i] = st.picks[j]; st.picks[j] = t;
    save(); drawSheet(); drawGrid();
  }

  function drawGrid(){
    var box = el('grid'); box.innerHTML = '';
    var pct = shapePct();
    for (var i = 0; i < 12; i++) {
      var id = st.picks[i];
      var s = document.createElement('div');
      s.className = 'slot' + (id ? '' : ' empty');
      s.setAttribute('data-n', i + 1);
      s.style.paddingTop = pct + '%';
      if (id) {
        var it = ALL[id];
        s.innerHTML = '<img src="' + it.url + '" alt="">' +
          '<span class="idx">' + (i + 1) + '</span>' +
          '<div class="bar">' +
            '<button data-a="l" title="Move left">&#9664;</button>' +
            '<button data-a="x" title="Remove">&#10005;</button>' +
            '<button data-a="r" title="Move right">&#9654;</button>' +
          '</div>';
        (function(idx, pid){
          s.querySelectorAll('.bar button').forEach(function(b){
            b.onclick = function(){
              var a = b.getAttribute('data-a');
              if (a === 'x') toggle(pid);
              else move(idx, a === 'l' ? -1 : 1);
            };
          });
        })(i, id);
      }
      box.appendChild(s);
    }
    var n = st.picks.length;
    el('n').textContent = n;
    el('copy').disabled = n === 0;
    el('sub').textContent = n === 0 ? 'Nothing chosen yet'
      : n < 12 ? n + ' chosen, ' + (12 - n) + ' to go'
      : 'All twelve chosen — reorder with the arrows, then copy';
  }

  function text(){
    var s = SHAPES.filter(function(x){ return x.key === st.shape; })[0];
    var lines = ['PORTFOLIO PICKS', 'Tile shape: ' + s.label, ''];
    st.picks.forEach(function(id, i){
      lines.push((i + 1) + '. ' + ALL[id].label + '  [' + id + ']' +
                 (ALL[id].on ? '  (already on ' + ALL[id].on + ')' : ''));
    });
    if (st.picks.length < 12) {
      lines.push('', '(' + (12 - st.picks.length) + ' still to choose)');
    }
    return lines.join('\\n');
  }

  el('copy').onclick = function(){
    var t = text();
    el('txt').value = t;
    el('out').className = 'out';
    var done = function(){
      el('copy').textContent = 'Copied — paste it to me';
      setTimeout(function(){ el('copy').textContent = 'Copy my picks'; }, 2600);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(t).then(done, function(){
        el('txt').select(); done();
      });
    } else { el('txt').select(); done(); }
  };

  el('clear').onclick = function(){
    st.picks = []; save(); drawTabs(); drawSheet(); drawGrid();
    el('out').className = 'out hide';
  };

  el('hide').onchange = function(){
    st.hide = el('hide').checked; save(); drawTabs(); drawSheet();
  };

  el('zoom').onclick = function(){
    var c = document.querySelector('.pk .chosen');
    var big = c.className.indexOf('big') >= 0;
    c.className = big ? 'chosen' : 'chosen big';
    el('zoom').textContent = big ? 'See them bigger' : 'See them smaller';
  };

  drawShape(); drawTabs(); drawSheet(); drawGrid();
})();
</script>
{% endraw %}
</body>
</html>
"""

out = HTML.replace("__DATA__", data)
(ROOT / "scalogy-picker.html").write_text(out)
print("wrote", len(out), "bytes;",
      " + ".join("%s %d (%d placed)" % (p["title"], len(p["items"]),
      sum(1 for r in p["items"] if len(r) > 2)) for p in POOLS))
