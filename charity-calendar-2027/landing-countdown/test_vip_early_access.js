const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const b=await chromium.launch();
for (const [name,q,ts] of [['vip-sat','?access=vip','2026-10-25T03:00:00Z'],['vip-sun','?access=vip','2026-10-25T15:00:00Z'],['plain-sun','','2026-10-25T15:00:00Z'],['vip-tue','?access=vip','2026-10-27T15:00:00Z'],['vip-flip','?access=vip','2026-10-25T13:59:58Z']]){
 const p=await b.newPage(); await p.clock.install({time:Date.parse(ts)});
 await p.route('**/*',r=>{const u=r.request().url(); if(u.startsWith('http://localhost:9/'))return r.fulfill({body:fs.readFileSync('test2.html','utf8'),contentType:'text/html'}); if(u.includes('_api'))return r.fulfill({body:'{"rows":[]}',contentType:'application/json'}); r.abort();});
 await p.goto('http://localhost:9/'+q);
 if(name==='vip-flip'){await p.clock.runFor(6000);await p.waitForTimeout(400);}
 console.log(name, JSON.stringify(await p.evaluate(()=>({s:document.getElementById('cc-status').textContent,form:!document.getElementById('cc-apply').hidden,cd:document.querySelector('[data-cd]').hidden?'-':document.querySelector('[data-cd]').innerText.replace(/\s+/g,' ')}))));
 await p.close();}
await b.close();})();
