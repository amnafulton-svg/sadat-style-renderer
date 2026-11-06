// A real news article page as a HeadlineCard picture (layers/Headline.tsx).
//
//   node tools/headline.mjs <url> <name> ["phrase" ...] [--height 1400] [--wait 8]
//
// Opens the article in the headless browser and cleans it like a reader view: ads, cookie bars, sidebars, share and
// print bars, "related"/"read more" boxes, loading spinners and empty picture slots go, and letters the page's own
// font cannot draw (German „quotes“ showed as boxes) get a fallback font. It saves the article column from its
// headline down (--height CSS px, default 1400) to public/headlines/<name>.png at 2x (sharp when the camera moves in)
// and prints the card's src/w/h/site, the headline box and the box of every phrase you give (the words as printed on
// the page, e.g. the line the narrator quotes), ready to paste as the card's `cam` and `marks` boxes.
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
const guard = setTimeout(() => { console.error('timed out'); kill(); process.exit(1); }, (WAIT + 70) * 1000);

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
// scroll through once so lazy pictures load (an unloaded one would leave an empty grey slot or a spinner)
await evaluate(`(async () => { for (let y = 0; y < Math.min(document.documentElement.scrollHeight, ${HEIGHT + 2400}); y += 700) { scrollTo(0, y); await new Promise(r => setTimeout(r, 150)); } scrollTo(0, 0); await new Promise(r => setTimeout(r, 800)); })()`);

const info = await evaluate(`(() => {
  const h1 = [...document.querySelectorAll('h1')].filter(h => h.innerText.trim().length > 15 && h.getBoundingClientRect().width > 200)[0];
  if (!h1) return {err: 'no headline (h1) found: paywall, block page or not an article'};
  const keep = (el) => el.contains(h1) || h1.contains(el) || !!el.closest('p, blockquote');
  const gone = (el) => { if (!keep(el)) el.style.setProperty('display', 'none', 'important'); };
  const css = document.createElement('style');
  css.textContent = 'iframe,aside,video,[role=complementary],[aria-label*=advert i]{visibility:hidden!important} footer,[role=contentinfo]{display:none!important}';
  document.head.appendChild(css);
  const AD = /(^|[-_ ])(ad|ads|advert|advertisement|sponsor|sponsored|promo|related|sidebar|newsletter|outbrain|taboola|recirc|trending|more-from|subscribe|cookie|consent|banner|paywall-prompt|share|sharing|social|sharebar|toolbar|print|spinner|loader|loading|skeleton|placeholder|comments?|breadcrumbs?|follow|font-?size|audio-?player|listen|read-?more)([-_ ]|$)/i;
  for (const el of document.querySelectorAll('body *')) {
    if (keep(el)) continue;
    const cs = getComputedStyle(el);
    if (cs.position === 'fixed' || cs.position === 'sticky') { gone(el); continue; }
    const tag = ((el.id || '') + ' ' + (typeof el.className === 'string' ? el.className : (el.className?.baseVal || ''))).trim();
    if (tag && AD.test(tag) && (el.innerText || '').length < 600) gone(el);
  }
  // clutter found by its words: share/print/font-size bars, "add X on Google", related-reading boxes
  const JUNK = /^(share|share this|teilen|compartir|condividi|partager|drucken|print|imprimir|stampa|(add|añade|agrega|aggiungi|ajoute|füge) .{2,60} (on|a|in|à|zu) google|.{0,40} on google news|lo más visto|most read|most popular|meistgelesen|últimos vídeos|últimos videos|ultime notizie|legal notice|aviso legal|impressum|este artículo se publicó hace|this article (is|was published) more than|follow us|síguenos|noticias relacionadas|related|related articles|read more|read next|lesen sie auch|mehr zum thema|leer más|ver más|leggi anche|newsletter|subscribe|abonnieren|suscríbete|kommentare|comentarios|listen to|escuchar|anhören|vorlesen|schriftgrösse|schriftgröße|font size|text size|copy link|link kopieren|advertisement|anzeige|publicidad|werbung)\\b/i;
  for (const el of document.querySelectorAll('body *')) {
    if (el.children.length > 8 || el.contains(h1) || h1.contains(el)) continue;
    const t = (el.innerText || '').trim();
    if (!t || t.length > 70 || !JUNK.test(t)) continue;
    // inside a paragraph only when the paragraph is nothing but this line ("this article was published 10 years ago")
    const para = el.closest('p, blockquote');
    if (para) { if ((para.innerText || '').trim().length <= t.length + 10) para.style.setProperty('display', 'none', 'important'); continue; }
    let box = el; // climb to the bar or box holding it, as long as it stays small
    while (box.parentElement && !keep(box.parentElement) && (box.parentElement.innerText || '').trim().length < 160 && box.parentElement.getBoundingClientRect().height < 260) box = box.parentElement;
    gone(box);
  }
  // link-only lists of 3+ items (related-reading sidebars, "more stories")
  for (const el of document.querySelectorAll('ul, ol')) {
    if (keep(el)) continue;
    const items = el.querySelectorAll(':scope > li'); if (items.length < 3) continue;
    const all = (el.innerText || '').replace(/\\s+/g, '').length;
    const linked = [...el.querySelectorAll('a')].reduce((a, x) => a + (x.innerText || '').replace(/\\s+/g, '').length, 0);
    if (all && linked / all > 0.8) gone(el);
  }
  // rows of round icon buttons (share bars whose only words are icons)
  for (const el of document.querySelectorAll('ul, div, nav')) {
    if (keep(el) || (el.innerText || '').trim().length > 30) continue;
    const icons = [...el.querySelectorAll('a, button')].filter(a => { const r = a.getBoundingClientRect(); return r.width > 10 && r.width < 70 && r.height < 70; });
    if (icons.length >= 3 && el.getBoundingClientRect().height < 120) gone(el);
  }
  // empty slots: big boxes with no words and no loaded picture (spinners, lazy images that never came)
  for (const el of document.querySelectorAll('div, figure, section, span, picture')) {
    if (keep(el)) continue;
    const r = el.getBoundingClientRect(); if (r.height < 40) continue;
    if ((el.innerText || '').trim()) continue;
    const pics = [...el.querySelectorAll('img, canvas')];
    const real = pics.some(p => p.tagName === 'CANVAS' || (p.complete && p.naturalWidth > 80 && p.getBoundingClientRect().width > 80));
    if (!real) gone(el);
  }
  // Windows-1252 letters stored as control characters (profil.at: „ “ became U+0084/U+0093 -> boxes)
  const CP = {0x80:'€',0x82:'‚',0x84:'„',0x85:'…',0x86:'†',0x87:'‡',0x8A:'Š',0x8B:'‹',0x8C:'Œ',0x91:'‘',0x92:'’',0x93:'“',0x94:'”',0x95:'•',0x96:'–',0x97:'—',0x99:'™',0x9A:'š',0x9B:'›',0x9C:'œ',0x9F:'Ÿ'};
  let c1 = 0;
  { const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let n; (n = w.nextNode());) if (/[\u0080-\u009f]/.test(n.data)) { n.data = n.data.replace(/[\u0080-\u009f]/g, ch => { c1++; return CP[ch.charCodeAt(0)] || ''; }); } }
  // letters the page font cannot draw: drawn like the font's "missing" box -> wrap them in a fallback font
  const cv = document.createElement('canvas'); cv.width = 64; cv.height = 64; const cx = cv.getContext('2d');
  const shot = (font, ch) => { cx.clearRect(0, 0, 64, 64); cx.font = font; cx.fillText(ch, 6, 46); return cx.getImageData(0, 0, 64, 64).data.join(','); };
  const memo = new Map(); let fixed = c1;
  const RISKY = /[„“”‚‘’«»–—…€£]/;
  const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); const todo = [];
  for (let n; (n = tw.nextNode());) if (RISKY.test(n.data) && n.parentElement) todo.push(n);
  for (const n of todo) {
    const cs = getComputedStyle(n.parentElement); const font = '40px ' + cs.fontFamily;
    const parts = n.data.split(/([„“”‚‘’«»–—…€£])/); if (parts.length < 2) continue;
    const frag = document.createDocumentFragment(); let any = false;
    for (const p of parts) {
      if (p.length === 1 && RISKY.test(p)) {
        const k = font + p;
        if (!memo.has(k)) { const a = shot(font, p); memo.set(k, a === shot(font, '\\uFFFF') || a === shot(font, '\\u0378') || a === shot(font, '\\uE7FF')); }
        if (memo.get(k)) { const s = document.createElement('span'); s.textContent = p; s.style.fontFamily = /serif/i.test(cs.fontFamily) && !/sans/i.test(cs.fontFamily) ? '"DejaVu Serif", serif' : '"DejaVu Sans", sans-serif'; frag.appendChild(s); any = true; fixed++; continue; }
      }
      frag.appendChild(document.createTextNode(p));
    }
    if (any) n.parentNode.replaceChild(frag, n);
  }
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
  const left = Math.max(0, Math.min(hr.left, ...ps.map(r => r.left)) - 48);
  const right = Math.min(1440, Math.max(hr.right, ...ps.map(r => r.right)) + 48);
  const top = Math.max(0, hr.top + scrollY - 60);
  const lastP = ps.length ? Math.max(...ps.map(r => r.bottom + scrollY)) : 0;
  const tall = lastP ? Math.min(${HEIGHT}, lastP - top + 70) : ${HEIGHT};
  return {left, top, width: right - left, height: Math.min(tall, document.documentElement.scrollHeight - top), fixed,
    head: [hr.left, hr.top + scrollY, hr.width, hr.height], title: h1.innerText.trim(), host: location.hostname.replace(/^(www\\d?|amp|m)\\./, '')};
})()`);
if (info.err) { console.error(info.err); kill(); process.exit(1); }

const boxes = [];
for (const ph of phrases) {
  boxes.push([ph, await evaluate(`(() => {
    const want = ${JSON.stringify(ph)}.toLowerCase().replace(/[‘’]/g, "'").replace(/[“”„]/g, '"').replace(/\\s+/g, ' ').trim();
    const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let all = '', map = [];
    for (let n; (n = tw.nextNode());) { const p = n.parentElement; if (!p || getComputedStyle(p).visibility === 'hidden' || !p.offsetParent) continue;
      const t = n.data; for (let i = 0; i < t.length; i++) { let c = t[i].toLowerCase().replace(/[‘’]/, "'").replace(/[“”„]/, '"');
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
console.log(`saved public/headlines/${name}.png  (${info.title})${info.fixed ? `  [${info.fixed} letters given a fallback font]` : ''}`);
console.log(`  src="headlines/${name}.png" w={${Math.round(info.width)}} h={${Math.round(info.height)}} site="${info.host}"`);
console.log(`  headline box: ${R(info.head)}`);
for (const [ph, lines] of boxes) console.log(lines ? `  "${ph}": ${lines.map(R).join(', ')}   (one box per printed line)` : `  "${ph}": NOT FOUND on the page (copy the words exactly as printed)`);
process.exit(0);
