# Run: python3 tools/open_check.py BASE_URL DATA.json (playwright); DATA must say answers_open.
# answers_open true: welcome shown, Sign enabled for everyone, no test wording.
# answers_open false: Sign disabled with the "switched off" line.
import sys, json
from playwright.sync_api import sync_playwright
BASE, DATA = sys.argv[1], sys.argv[2]
STAKE = "abababababababababababababababababababababababababababab"   # a made-up stake key hash: the tests only put it in localStorage
d = json.load(open(DATA)); ACT = [a for a in d['actions'] if a['answerable']][0]['id']
ok = True
def must(c, what):
    global ok; print('OK ' if c else 'BAD', what); ok &= bool(c)
with sync_playwright() as p:
    b = p.chromium.launch()
    for lang in ('en', 'es'):
        pg = b.new_context(viewport={"width": 390, "height": 844}).new_page()
        pg.goto(BASE + "/index.html")
        pg.evaluate(f"() => {{ localStorage.setItem('lang', '{lang}'); localStorage.setItem('tvoah.wallet', JSON.stringify({{key:'eternl',name:'Eternl',stake:'{STAKE}'}})); localStorage.setItem('tvoah.answers.{STAKE}', JSON.stringify({{'{ACT}':'yes'}})); }}")
        pg.goto(BASE + "/index.html"); pg.wait_for_timeout(1200)
        body = pg.locator('main').inner_text()
        must(('Welcome to The Voice' in body) or ('Te damos la bienvenida a The Voice' in body), f'{lang}: welcome shown')
        must(not any(w in body for w in ('Test phase', 'Fase de prueba', 'testers', 'prueban')), f'{lang}: no test wording on the overview')
        pg.click('#cart'); pg.wait_for_timeout(300)
        btn = pg.locator(".basket-modal button[data-act='sign']")
        must(btn.count() == 1 and btn.is_enabled(), f'{lang}: Sign enabled without ?sign=on')
        must(not any(w in pg.locator('.basket-modal').inner_text() for w in ('?sign=', 'switched off', 'desactivado')), f'{lang}: no switch note in the basket')
        pg.goto(BASE + "/how.html"); pg.wait_for_timeout(800)
        must(not any(w in pg.locator('main').inner_text() for w in ('test phase', 'fase de prueba', 'testers')), f'{lang}: no test wording on How it works')
    b.close()
print('RESULT', 'OK' if ok else 'BAD')
