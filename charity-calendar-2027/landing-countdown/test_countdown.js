const {chromium}=require('playwright');
(async()=>{
 const b=await chromium.launch();
 for (const [name,ts,w] of [['pre',Date.parse('2026-10-25T20:00:00Z'),1280],['open',Date.parse('2026-10-28T15:00:00Z'),390],['closed',Date.parse('2026-10-31T06:00:00Z'),1280],['flip',Date.parse('2026-10-26T13:59:57Z'),1280]]){
  const p=await b.newPage({viewport:{width:w,height:900}});
  await p.clock.install({time:ts});
  await p.route('**/*',r=>{const u=r.request().url(); if(u.startsWith('http://localhost:9/'))return r.fulfill({body:require('fs').readFileSync('test.html','utf8'),contentType:'text/html'}); if(u.includes('_api'))return r.fulfill({body:'{"rows":[]}',contentType:'application/json'}); r.abort();});
  let loads=0; p.on('load',()=>loads++);
  await p.goto('http://localhost:9/');
  if(name==='flip'){await p.clock.runFor(6000); await p.waitForTimeout(500);}
  const info=await p.evaluate(()=>({status:document.getElementById('cc-status').textContent,cds:[...document.querySelectorAll('[data-cd]')].map(b=>b.hidden?'hidden':b.innerText.replace(/\s+/g,' ')),form:document.getElementById('cc-apply').hidden,closedH:document.getElementById('cc-closed').hidden?null:document.getElementById('cc-closed-h').textContent,ow:document.documentElement.scrollWidth}));
  console.log(name,'loads',loads,JSON.stringify(info));
  if(name!=='flip'){await p.screenshot({path:name+'-hero.png'}); await p.locator('#apply').scrollIntoViewIfNeeded(); await p.screenshot({path:name+'-apply.png'});}
  await p.close();
 }
 await b.close();
})();
