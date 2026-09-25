# Phone screenshots (390x844) of the site: not connected, connected, basket open.
# Needs playwright + its chromium (pip --break-system-packages). Run against the
# live site or a preview:   python3 tools/phone_shots.py https://voiceofadaholders.com
import json, os, sys, urllib.request
from playwright.sync_api import sync_playwright
if len(sys.argv) != 2:
    sys.exit("usage: phone_shots.py BASE_URL")
BASE = sys.argv[1].rstrip("/")
OUT = os.path.expanduser("~/scratch/shots")
os.makedirs(OUT, exist_ok=True)
STAKE = "abababababababababababababababababababababababababababab"   # a made-up stake key hash: only put in localStorage
# two actions open for answers, from the tally the site serves
_open = [a["id"] for a in json.load(urllib.request.urlopen(BASE + "/data.json"))["actions"]
         if a.get("answerable", a["status"] == "open")]
ACT, ACT2 = _open[0], _open[-1]
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=1)
    pg = ctx.new_page()
    pg.goto(BASE + "/"); pg.wait_for_timeout(1200)
    pg.screenshot(path=f"{OUT}/1_index_anon.png")
    pg.goto(BASE + f"/action?id={ACT}"); pg.wait_for_timeout(1200)
    pg.screenshot(path=f"{OUT}/2_action_anon.png")
    pg.evaluate(f"""() => {{ localStorage.setItem('tvoah.wallet', JSON.stringify({{key:'eternl',name:'Eternl',stake:'{STAKE}'}}));
        localStorage.setItem('tvoah.answers.{STAKE}', JSON.stringify({{'{ACT2}':'yes'}})); }}""")
    pg.goto(BASE + "/"); pg.wait_for_timeout(1500)
    pg.screenshot(path=f"{OUT}/3_index_conn.png")
    pg.goto(BASE + f"/action?id={ACT}"); pg.wait_for_timeout(1500)
    pg.screenshot(path=f"{OUT}/4_action_conn.png", full_page=True)
    pg.click("#cart"); pg.wait_for_timeout(500)
    pg.screenshot(path=f"{OUT}/5_basket.png")
    w = pg.evaluate("() => [document.documentElement.scrollWidth, window.innerWidth]")
    print("scrollWidth vs viewport:", w)
    b.close()
