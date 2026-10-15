# The news ticker with few items: on a desktop, a wide screen and a phone the
# run must be at least as wide as its window (so the loop shows no jump), both
# runs equally wide, the copies hidden from screen readers; with reduced motion
# nothing is added. Run against a site whose data.json has one or two news
# items. Needs playwright.
#   python3 tools/ticker_fit.py BASE_URL
import sys, json
from playwright.sync_api import sync_playwright
BASE=sys.argv[1]
JS="""() => { const w=document.querySelector('.ticker-window'), runs=[...document.querySelectorAll('.ticker-run')], t=document.querySelector('.ticker-track');
  if(!w||!runs.length) return null;
  return {window:w.clientWidth, run0:runs[0].scrollWidth, run1:runs[1].scrollWidth, track:t.scrollWidth, fills:runs[0].querySelectorAll('.ticker-fill').length,
          items:runs[0].querySelectorAll(':scope > span:not(.ticker-sep):not(.ticker-fill), :scope > a').length, dur:t.style.animationDuration,
          hiddenFills:[...runs[0].querySelectorAll('.ticker-fill')].every(f=>f.getAttribute('aria-hidden')==='true'), text:runs[0].textContent.slice(0,60)}; }"""
bad=0
with sync_playwright() as p:
    b=p.chromium.launch()
    for name,w,h,opts in (('desktop',1280,800,{}),('wide',1920,1000,{}),('phone',360,740,dict(is_mobile=True,has_touch=True)),('reduced motion',1280,800,dict(reduced_motion='reduce'))):
        ctx=b.new_context(viewport={'width':w,'height':h},**opts); pg=ctx.new_page(); pg.goto(BASE+'/index.html'); pg.wait_for_selector('.ticker',timeout=15000); pg.wait_for_timeout(500)
        r=pg.evaluate(JS); 
        ok = r and (r['run0']>=r['window'] or name=='reduced motion') and r['run0']==r['run1'] and r['hiddenFills'] and (name!='reduced motion' or r['fills']==0)
        bad+= not ok; print(name, 'OK ' if ok else 'BAD', r)
        if name=='desktop':
            pg.set_viewport_size({'width':1900,'height':800}); pg.wait_for_timeout(700); r2=pg.evaluate(JS); ok2=r2['run0']>=r2['window']; bad+=not ok2; print('  after widening to 1900:', 'OK ' if ok2 else 'BAD', {k:r2[k] for k in ('window','run0','fills')})
        ctx.close()
    b.close()
sys.exit(1 if bad else 0)
