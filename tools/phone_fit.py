# Every page and dialog on a small phone (320 and 360 px, mobile emulation):
# nothing may be wider than the screen. Needs playwright.
#   python3 tools/phone_fit.py BASE_URL OUT_DIR DATA.json
import sys, json
from playwright.sync_api import sync_playwright
BASE, OUT = sys.argv[1], sys.argv[2]
STAKE = "abababababababababababababababababababababababababababab"   # a made-up stake key hash: the tests only put it in localStorage
d = json.load(open(sys.argv[3]))
ACT = [a for a in d['actions'] if a['answerable']][0]['id']
DOC = next(a for a in d['actions'] if a.get('title_status') == 'verified' and not a['answerable'])['id']
WIDE = """() => { const w = document.documentElement.clientWidth;
  const bad = [...document.querySelectorAll('body *')].filter(e => { const r = e.getBoundingClientRect(); return r.width && r.right > w + 1 && getComputedStyle(e).position !== 'fixed' && !e.closest('.nav'); });
  return [document.documentElement.scrollWidth, innerWidth, w, bad.slice(0, 4).map(e => e.tagName.toLowerCase() + (e.className ? '.' + e.className : '') + ':' + Math.round(e.getBoundingClientRect().right))]; }"""
MODAL = "() => { const m = document.querySelector('.modal'); const r = m.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.right), innerWidth, [...m.querySelectorAll('*')].filter(e => e.getBoundingClientRect().right > r.right + 1).slice(0,3).map(e => e.tagName + '.' + e.className)]; }"
fails = 0
with sync_playwright() as p:
    b = p.chromium.launch()
    for w, h in ((320, 640), (360, 740)):
        ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2, is_mobile=True, has_touch=True)
        pg = ctx.new_page()
        def check(name):
            global fails
            r = pg.evaluate(WIDE); ok = r[0] <= w and r[1] == w and not r[3]
            fails += not ok; print(w, 'OK ' if ok else 'BAD', name, r)
        def modal(name):
            global fails
            r = pg.evaluate(MODAL); ok = r[0] >= 0 and r[1] <= w and not r[3]
            fails += not ok; print(w, 'OK ' if ok else 'BAD', 'dialog', name, r)
            pg.screenshot(path=f"{OUT}/after_{w}_{name}.png"); pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
        for lang in ('en', 'es'):
            pg.goto(BASE + "/"); pg.evaluate(f"localStorage.setItem('lang', '{lang}')")
            for page in ('index', 'how', 'recount', 'contact', 'disclaimer'):
                pg.goto(BASE + ("/" if page == "index" else f"/{page}")); pg.wait_for_timeout(1000); check(f'{lang} {page}')
            for a in d['actions']:
                if a['answerable'] or a['groups'] or a['id'] == DOC:
                    pg.goto(BASE + f"/action?id={a['id']}"); pg.wait_for_timeout(800); check(f"{lang} action {a['id'][:8]}")
        pg.evaluate("localStorage.setItem('lang', 'en')")
        pg.goto(BASE + "/"); pg.wait_for_timeout(1000)
        pg.locator('table').last.scroll_into_view_if_needed(); pg.screenshot(path=f"{OUT}/after_{w}_closed.png")
        pg.click("button[data-act='connect']"); pg.wait_for_timeout(300); modal('connect')
        pg.evaluate(f"() => {{ localStorage.setItem('tvoah.wallet', JSON.stringify({{key:'eternl',name:'Eternl',stake:'{STAKE}'}})); localStorage.setItem('tvoah.answers.{STAKE}', JSON.stringify({{'{ACT}':'yes'}})); localStorage.setItem('tvoah.sign', 'on'); }}")
        pg.goto(BASE + "/"); pg.wait_for_timeout(1200); check('index with wallet')
        pg.click("#cart"); pg.wait_for_timeout(300); modal('basket')
        pg.click("#cart"); pg.wait_for_timeout(300); pg.click("button[data-act='sign']"); pg.wait_for_timeout(800); modal('sign')
        pg.goto(BASE + f"/action?id={DOC}"); pg.wait_for_timeout(1200)
        pg.click("button[data-act='doc']"); pg.wait_for_timeout(1200); modal('document')
        ctx.close()
    b.close()
print('FAILS', fails)
