// Draw the overview and every action page against data.json, in one language,
// as a browser would; then exercise the answer basket. Run before every deploy
// of app.js:   DATA=path/to/live/data.json node tools/render.test.js en|es
const fs = require('fs');
const path = require('path');
const src = fs.readFileSync(path.join(__dirname, '..', 'app.js'), 'utf8');
const data = JSON.parse(fs.readFileSync(process.env.DATA || path.join(__dirname, '..', 'data.json'), 'utf8'));
const lang = process.argv[2] || 'en';

let html = '', bodyHtml = '';
const appended = [];
const cart = { hidden: true, innerHTML: '' };
const element = () => {
  const inner = { innerHTML: '' };
  return { className: '', innerHTML: '', setAttribute() {}, remove() {}, addEventListener() {},
    querySelector: () => inner, inner };
};
const store = { 'lang': lang };
const main = { set innerHTML(v) { html = v; }, get innerHTML() { return html; }, insertAdjacentHTML() {} };
global.navigator = { language: lang };
global.localStorage = { getItem: k => store[k] ?? null, setItem: (k, v) => { store[k] = String(v); } };
global.document = {
  documentElement: {}, addEventListener() {}, title: '', hidden: false,
  querySelector: q => q === 'main' ? main
    : q === '.basket-modal' ? appended.filter(e => e.className.includes('basket-modal')).pop() || null : null,
  createElement: element,
  querySelectorAll: () => [],
  getElementById: id => id === 'cart' ? cart : null,
  body: { insertAdjacentHTML: (w, v) => { bodyHtml += v; }, classList: { add() {}, remove() {} },
    appendChild: e => appended.push(e), style: {} },
};
const loc = { search: '', pathname: '/', hash: '' };
global.location = loc;
const api = new Function(src + `; return { renderIndex, renderAction, renderContact, renderDisclaimer, renderRecount, drawTicker, pruneBasket, drawBasket, basket, openBasket,
  setData: d => { DATA = d; }, setMine: m => { MINE = m; } };`)();

api.renderIndex(data);
console.log(`[${lang}] overview ok, ${html.length} chars, ${(html.match(/closes by|cierra a más tardar/g) || []).length} closing lines`);
for (const a of data.actions) { loc.search = '?id=' + a.id; api.renderAction(data); }
console.log(`[${lang}] ${data.actions.length} action pages ok`);
api.renderContact();
if (!html.includes('href="mailto:developmentbkind@gmail.com"')) throw new Error('contact page without the address');
console.log(`[${lang}] contact page ok`);
// The ticker: one sentence per event in this language, links to the actions,
// the copy of the run out of the tab order; nothing drawn without news.
const newsData = { ...data, news: [
  { time: data.tally.time, kind: 'submitted', action: data.actions[0].id },
  { time: data.tally.time, kind: 'answers_day', count: 3 },
  { time: data.tally.time, kind: 'epoch_began', epoch: 657 },
  { time: data.tally.time, kind: 'epoch_ends', epoch: 657, ends_at: '2026-09-26T21:44:51Z' },
  { time: data.tally.time, kind: 'closing', action: data.actions[0].id, closes_at: '2026-09-27T21:44:51Z' },
  { time: data.tally.time, kind: 'unknown-kind' },
] };
bodyHtml = '';
api.drawTicker(newsData);
if (!/New governance action|Nueva acción de gobernanza/.test(bodyHtml) || !/3 answers on chain|3 respuestas en la cadena/.test(bodyHtml)
    || !/Epoch 657 has begun|Ha empezado la época 657/.test(bodyHtml)
    || !/Epoch 657 ends Sep 26|La época 657 termina el 26 sept/.test(bodyHtml)) throw new Error('ticker sentences missing');
if (!bodyHtml.includes(`href="/action?id=${encodeURIComponent(data.actions[0].id)}"`) || !bodyHtml.includes('tabindex="-1"')) throw new Error('ticker links wrong');
// Only the closing warning blinks and carries the sign, in the run and its copy.
if ((bodyHtml.match(/class="ticker-alert"/g) || []).length !== 2 || (bodyHtml.match(/⚠ /g) || []).length !== 2) throw new Error('closing warning not marked');
bodyHtml = '';
api.drawTicker({ ...data, news: [] });
if (/ticker/.test(bodyHtml)) throw new Error('ticker drawn without news');
console.log(`[${lang}] ticker ok`);
// Disclaimer: Spanish law; the open-source line and the recount page's
// "published" only once SOURCE_URL is filled in, and then both.
// Both cases whatever app.js carries: SOURCE_URL set to empty, then to an example.
if (!/const SOURCE_URL = '[^']*';/.test(src)) throw new Error('SOURCE_URL not found in app.js');
const withSource = url => new Function(src.replace(/const SOURCE_URL = '[^']*';/, "const SOURCE_URL = '" + url + "';")
  + '; return { renderDisclaimer, renderRecount };')();
const none = withSource('');
none.renderDisclaimer();
if (!/Spanish law applies|legislación española/.test(html) || /GitHub/.test(html)) throw new Error('disclaimer wrong without a source address');
none.renderRecount();
if (!/not public yet|aún no es público/.test(html)) throw new Error('recount page claims public code without an address');
const pub = withSource('https://github.com/example/x');
pub.renderDisclaimer();
if (!/GitHub \(<a href="https:\/\/github.com\/example\/x"/.test(html)) throw new Error('disclaimer without the open-source line once the address is set');
pub.renderRecount();
if (/not public yet|aún no es público/.test(html) || !html.includes('https://github.com/example/x')) throw new Error('recount page not switched to the address');
console.log(`[${lang}] disclaimer ok: without a source address no open-source claim; with one, disclaimer and recount page both`);

const isOpen = a => a.answerable ?? a.status === 'open';
const open = data.actions.find(isOpen);
const closed = data.actions.find(a => !isOpen(a));

// A link to an action the tally does not have: said so, not another action shown.
loc.search = '?id=' + 'ab'.repeat(32) + '-0'; api.renderAction(data);
if (!/no governance action at this link|ninguna acción de gobernanza en este enlace/.test(html)) throw new Error('unknown action id not reported');
// A ratified action still in its ratified epoch takes answers: among the open ones.
const ratified = { ...open, id: 'cd'.repeat(32) + '-0', status: 'ratified', status_epoch: data.tally.epoch, answerable: true };
const withRatified = { ...data, actions: [...data.actions, ratified] };
api.renderIndex(withRatified);
const openPart = html.split(/Earlier actions|Acciones anteriores/)[0];
if (!openPart.includes(encodeURIComponent(ratified.id))) throw new Error('answerable ratified action not among the open ones');
api.renderIndex({ ...data, actions: [...data.actions, { ...ratified, answerable: false }] });
if (html.split(/Earlier actions|Acciones anteriores/)[0].includes(encodeURIComponent(ratified.id))) throw new Error('closed ratified action among the open ones');
console.log(`[${lang}] unknown id reported; ratified action open until its closing, closed after`);

// No wallet connected: answering is closed, with a way to connect.
loc.search = '?id=' + open.id; api.renderAction(data);
if (!/value="yes" disabled/.test(html) || !/Connect your wallet|Conecta tu billetera/.test(html)) throw new Error('answering possible without a wallet');
// A wallet registered after the action was submitted: cannot answer.
const stake = 'ab'.repeat(28);
store['tvoah.wallet'] = JSON.stringify({ key: 'mock', name: 'Mock', stake });
api.setMine({ answers: {}, reg: open.pos + 1 });
api.renderAction(data);
if (!/value="yes" disabled/.test(html) || !/not registered before|no estaba registrada/.test(html)) throw new Error('ineligible wallet can answer');
// Registered before: can answer; an answer on the chain is shown.
api.setMine({ answers: { [open.id]: { choice: 'no', tx: 'cd'.repeat(32), counted: true } }, reg: open.pos - 1 });
api.renderAction(data);
if (/value="yes" disabled/.test(html) || !/already on chain|ya está en la cadena/.test(html) || !/Changed your mind|Cambiaste de opinión/.test(html)) throw new Error('eligible wallet cannot answer, or its answer is not shown');
// Its eligibility file could not be read: answering off, and said why.
api.setMine({ answers: {}, reg: undefined });
api.renderAction(data);
if (!/value="yes" disabled/.test(html) || !/could not be checked|No se pudo comprobar/.test(html)) throw new Error('unreadable eligibility lets the wallet answer');
// Sent, and the tally passed the transaction's time-to-live without it: not landed.
api.setMine({ answers: {}, reg: open.pos - 1 });
api.setData(data);
store['tvoah.sent'] = JSON.stringify([{ tx: 'ef'.repeat(32), at: data.tally.time, ttl: data.tally.slot + 100, stake, answers: { [open.id]: 'yes' } }]);
api.renderAction(data);
if (!/Sent: |Enviada: /.test(html) || /did not reach the chain|no llegó a la cadena/.test(html)) throw new Error('pending answer not shown as sent');
store['tvoah.sent'] = JSON.stringify([{ tx: 'ef'.repeat(32), at: data.tally.time, ttl: data.tally.slot, stake, answers: { [open.id]: 'yes' } }]);
api.renderAction(data);
if (!/did not reach the chain|no llegó a la cadena/.test(html)) throw new Error('answer past its time-to-live still shown as sent');
delete store['tvoah.sent'];
console.log(`[${lang}] wallet ok: none → connect first; registered after → cannot answer; registered before → answers, chain answer shown; unreadable → off; sent past ttl → not landed`);

store['tvoah.answers.' + stake] = JSON.stringify({ [open.id]: 'yes', [closed.id]: 'no' });
api.setData(data);
const pruned = api.pruneBasket(data);
api.drawBasket(pruned);
const kept = Object.keys(api.basket());
if (pruned.length !== 1 || kept.length !== 1 || kept[0] !== open.id) throw new Error('basket pruning wrong: ' + JSON.stringify({ pruned, kept }));
if (cart.hidden || !/>1</.test(cart.innerHTML)) throw new Error('basket button in the top bar missing or wrong: ' + cart.innerHTML);
if (!appended.some(e => e.className === 'toast' && /closed|cerró/.test(e.innerHTML))) throw new Error('no notice for the removed answer');
api.openBasket();
const list = appended.filter(e => e.className.includes('basket-modal')).pop().inner.innerHTML;
if (!/answer ready|respuesta lista/.test(list) || !/Remove|Quitar/.test(list)) throw new Error('basket list wrong');
loc.search = '?id=' + open.id; api.renderAction(data);
if (!/value="yes" checked/.test(html)) throw new Error('stored answer not shown as chosen');
api.renderIndex(data);
if (html.includes(`href="/action?id=${encodeURIComponent(open.id)}"`)) throw new Error('answered action still selectable on the overview');
if (!/Your answer|Tu respuesta/.test(html)) throw new Error('answered tag missing');
console.log(`[${lang}] basket ok: closed action removed, open answer kept, shown, and not selectable on the overview`);
