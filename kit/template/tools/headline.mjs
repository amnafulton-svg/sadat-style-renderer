// A real news article page as a HeadlineCard picture (layers/Headline.tsx).
//
//   node tools/headline.mjs <url> <name> ["phrase" ...] [--height 1400] [--wait 8]
//
// Opens the article in the headless browser, hides ads, cookie bars and sidebars, and saves the article column from
// its headline down (--height CSS px, default 1400) to public/headlines/<name>.png at 2x (sharp when the camera
// moves in). It prints the card's w/h, the headline box and the box of every phrase you give (the words as printed
// on the page, e.g. the line the narrator quotes), ready to paste as the card's `cam` and `marks` boxes.
// Never guess a box by eye. Open the png (Read) before using it: a paywall, "access denied" or a cookie wall means
// that outlet cannot be used; try another outlet that ran the same story.
import {spawn} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(k); if (i < 0) return d; const v = args[i + 1]; args.splice(i, 2); return v; };
const HEIGHT = +opt('--height', 1400), WAIT = +opt('--wait', 8);
const [url, name, ...phrases] = args;
if (!url || !name) { console.error('usage: node tools/headline.mjs <url> <name> ["phrase" ...] [--height 1400] [--wait 8]'); process.exit(2); }

const findChrome = () => {
  const base = path.join(ROOT, 'node_modules/.remotion/chrome-headless-shell');
  const walk = (d) => { for (const e of fs.readdirSync(d, {withFileTypes: true})) { const p = path.join(d, e.name);
    if (e.isDirectory()) { const r = walk(p); if (r) return r; } else if (e.name === 'chrome-headless-shell') return p; } };
  if (fs.existsSync(base)) { const r = walk(base); if (r) return r; }
  throw new Error('no chrome-headless-shell under node_modules/.remotion: render one still first (npx remotion still)');
};

const prof = fs.mkdtempSync(path.join(os.tmpdir(), 'headline-'));
const chrome = spawn(findChrome(), ['--headless', '--no-sandbox', '--disable-gpu', '--hide-scrollbars', '--mute-audio',
  `--user-data-dir=${prof}`, '--remote-debugging-port=0', '--window-size=1440,2400', 'about:blank'], {stdio: ['ignore', 'ignore', 'pipe']});
const kill = () => { try { chrome.kill('SIGKILL'); } catch {} try { fs.rmSync(prof, {recursive: true, force: true}); } catch {} };
const guard = setTimeout(() => { console.error('timed out'); kill(); process.exit(1); }, (WAIT + 60) * 1000);

const wsUrl = await new Promise((res, rej) => {
  let buf = '';
  chrome.stderr.on('data', (d) => { buf += d; const m = buf.match(/DevTools listening on (ws:\/\/\S+)/); if (m) res(m[1]); });
  chrome.on('exit', () => rej(new Error('browser exited')));
});
const port = new URL(wsUrl).port;
const tab = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, {method: 'PUT'})).json();
const ws = new WebSocket(tab.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener('open', r));
let seq = 0; const pending = new Map();
ws.addEventListener('message', (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
const send = (method, params = {}) => new Promise((res, rej) => { const id = ++seq; pending.set(id, (m) => m.error ? rej(new Error(m.error.message)) : res(m.result)); ws.send(JSON.stringify({id, method, params})); });
const evaluate = async (expr) => { const r = await send('Runtime.evaluate', {expression: expr, returnByValue: true, awaitPromise: true}); if (r.exceptionDetails) throw new Error(r.exceptionDetails.text + ' ' + (r.exceptionDetails.exception?.description || '')); return r.result.value; };

await send('Network.enable');
await send('Network.setBlockedURLs', {urls: ['*doubleclick*', '*googlesyndication*', '*adservice*', '*taboola*', '*outbrain*', '*amazon-adsystem*', '*recaptcha*']});
await send('Emulation.setDeviceMetricsOverride', {width: 1440, height: 2400, deviceScaleFactor: 2, mobile: false});
await send('Page.enable');
send('Page.navigate', {url}).catch(() => {});
await new Promise((r) => setTimeout(r, WAIT * 1000)); // never wait for "load": ad-heavy pages never finish

const info = await evaluate(`(() => {
  const AD = /(^|[-_ ])(ad|ads|advert|sponsor|promo|related|sidebar|newsletter|outbrain|taboola|recirc|trending|more-from|subscribe|cookie|consent|banner|paywall-prompt)([-_ ]|$)/i;
  const css = document.createElement('style');
  css.textContent = 'iframe,aside,video,[role=complementary],[aria-label*=advert i]{visibility:hidden!important}';
  document.head.appendChild(css);
  for (const el of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(el);
    if (cs.position === 'fixed' || cs.position === 'sticky') { el.style.setProperty('display', 'none', 'important'); continue; }
    const tag = ((el.id || '') + ' ' + (typeof el.className === 'string' ? el.className : '')).trim();
    if (tag && AD.test(tag) && !el.querySelector('h1')) el.style.setProperty('visibility', 'hidden', 'important');
  }
  const h1 = [...document.querySelectorAll('h1')].filter(h => h.innerText.trim().length > 15 && h.getBoundingClientRect().width > 200)[0];
  if (!h1) return {err: 'no headline (h1) found: paywall, block page or not an article'};
  window.scrollTo(0, 0);
  const hr = h1.getBoundingClientRect();
  const ps = [...document.querySelectorAll('p')].map(p => p.getBoundingClientRect())
    .filter(r => r.top > hr.top && r.top < hr.top + ${HEIGHT} && r.width > 250 && r.left < hr.right && r.right > hr.left);
  // buttons, app badges and pictures beside the text column (not the article's own photos) or above the headline
  const pRight = ps.length ? Math.max(...ps.map(r => r.right)) : hr.right;
  for (const el of document.querySelectorAll('a, button, img, picture, svg, [role=button]')) {
    const r = el.getBoundingClientRect(); if (!r.width) continue;
    if ((r.top > hr.bottom && r.left >= pRight + 10) || (el.tagName === 'IMG' && r.bottom < hr.top - 4))
      el.style.setProperty('visibility', 'hidden', 'important');
  }
  const left = Math.max(0, Math.min(hr.left, ...ps.map(r => r.left)) - 40);
  const right = Math.min(1440, Math.max(hr.right, ...ps.map(r => r.right)) + 40);
  const top = Math.max(0, hr.top + scrollY - 70);
  return {left, top, width: right - left, height: Math.min(${HEIGHT}, document.documentElement.scrollHeight - top),
    head: [hr.left, hr.top + scrollY, hr.width, hr.height], title: h1.innerText.trim(), text: document.body.innerText.slice(0, 300)};
})()`);
if (info.err) { console.error(info.err); kill(); process.exit(1); }

const boxes = [];
for (const ph of phrases) {
  boxes.push([ph, await evaluate(`(() => {
    const want = ${JSON.stringify(ph)}.toLowerCase().replace(/[‘’]/g, "'").replace(/[“”]/g, '"').replace(/\\s+/g, ' ').trim();
    const nodes = []; const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let all = '', map = [];
    for (let n; (n = tw.nextNode());) { const p = n.parentElement; if (!p || getComputedStyle(p).visibility === 'hidden' || !p.offsetParent) continue;
      const t = n.data; for (let i = 0; i < t.length; i++) { let c = t[i].toLowerCase().replace(/[‘’]/, "'").replace(/[“”]/, '"');
        if (/\\s/.test(c)) { if (all.endsWith(' ')) continue; c = ' '; } all += c; map.push([n, i]); } }
    const at = all.indexOf(want); if (at < 0) return null;
    const r = document.createRange(); const [sn, si] = map[at]; const [en, ei] = map[at + want.length - 1];
    r.setStart(sn, si); r.setEnd(en, ei + 1);
    const lines = [];
    for (const q of r.getClientRects()) { if (q.width < 2) continue; const l = lines.find(L => Math.abs(L[1] - q.top) < q.height / 2);
      if (l) { const x1 = Math.max(l[0] + l[2], q.right); l[0] = Math.min(l[0], q.left); l[2] = x1 - l[0]; l[3] = Math.max(l[3], q.height); }
      else lines.push([q.left, q.top + scrollY, q.width, q.height]); }
    return lines;
  })()`)]);
}

// the card always reaches the last marked line
const lows = boxes.flatMap(([, ls]) => ls || []).map((b) => b[1] + b[3] - info.top + 80);
if (lows.length) info.height = Math.max(info.height, ...lows);
const shot = await send('Page.captureScreenshot', {format: 'png', captureBeyondViewport: true,
  clip: {x: info.left, y: info.top, width: info.width, height: info.height, scale: 1}});
const out = path.join(ROOT, 'public/headlines', `${name}.png`);
fs.mkdirSync(path.dirname(out), {recursive: true});
fs.writeFileSync(out, Buffer.from(shot.data, 'base64'));
clearTimeout(guard); ws.close(); kill();

const R = (b) => `[${[b[0] - info.left, b[1] - info.top, b[2], b[3]].map(Math.round).join(', ')}]`;
console.log(`saved public/headlines/${name}.png  (${info.title})`);
console.log(`  src="headlines/${name}.png" w={${Math.round(info.width)}} h={${Math.round(info.height)}}`);
console.log(`  headline box: ${R(info.head)}`);
for (const [ph, lines] of boxes) console.log(lines ? `  "${ph}": ${lines.map(R).join(', ')}   (one box per printed line)` : `  "${ph}": NOT FOUND on the page (copy the words exactly as printed)`);
process.exit(0);
