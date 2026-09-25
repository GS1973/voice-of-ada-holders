# Run: python3 tools/menu_check.py BASE_URL OUT_DIR (playwright).
# The menu button on a phone: navigation hidden, opens and closes; on a wide screen no button, navigation shown.
import sys
from playwright.sync_api import sync_playwright
BASE, OUT = sys.argv[1], sys.argv[2]
ok = True
def must(c, what):
    global ok
    print('OK ' if c else 'BAD', what); ok &= bool(c)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_context(viewport={"width": 360, "height": 740}, device_scale_factor=2, is_mobile=True, has_touch=True).new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(BASE + "/"); pg.wait_for_timeout(1200)
    must(pg.locator('.menu-btn').is_visible() and not pg.locator('.nav').is_visible(), 'phone: button shown, navigation folded')
    pg.screenshot(path=f"{OUT}/menu_closed.png")
    pg.tap('.menu-btn'); pg.wait_for_timeout(200)
    must(pg.locator('.nav').is_visible() and pg.locator('.menu-btn').get_attribute('aria-expanded') == 'true', 'phone: tap opens it')
    n = pg.locator('.nav a').count()
    must(n >= 4 and all(pg.locator('.nav a').nth(i).is_visible() for i in range(n)), f'phone: all {n} items visible')
    pg.screenshot(path=f"{OUT}/menu_open.png")
    pg.tap('.menu-btn'); pg.wait_for_timeout(200)
    must(not pg.locator('.nav').is_visible(), 'phone: second tap closes it')
    pg.mouse.wheel(0, 3000); pg.wait_for_timeout(300); pg.tap('.menu-btn'); pg.wait_for_timeout(200)
    must(pg.locator('.nav a').first.is_visible() and pg.locator('.nav').bounding_box()['y'] < 740, 'phone: opens in view after scrolling')
    pg.screenshot(path=f"{OUT}/menu_scrolled.png")
    pg.locator('.nav a', has_text='Contact').tap(); pg.wait_for_timeout(1000)
    must(pg.url.endswith('/contact') and not pg.locator('.nav').is_visible(), 'phone: item navigates, menu folded on the new page')
    pg.keyboard.press('Escape')
    must(pg.evaluate("document.documentElement.scrollWidth") <= 360, 'phone: no sideways scroll')
    pg2 = b.new_context(viewport={"width": 1280, "height": 800}).new_page()
    pg2.goto(BASE + "/"); pg2.wait_for_timeout(1200)
    must(not pg2.locator('.menu-btn').is_visible() and pg2.locator('.nav').is_visible(), 'wide: no button, navigation shown')
    pg2.screenshot(path=f"{OUT}/menu_wide.png")
    must(not errs, 'no page errors ' + str(errs))
    b.close()
print('RESULT', 'OK' if ok else 'BAD')
