// Image cache for the Living Dex Checklist.
// Artwork from imgbb (shiny) and Bulbapedia (regular) is kept on this device after its first download, so later
// visits show it instantly without asking those sites again. Only successful responses are stored: both hosts
// allow CORS, so the status can be checked.
//
// What tools/test_imgbb.py measured (2026-10-31): imgbb served 100 requests at once without a single 503, but some
// images hang for 15+ seconds the first time they're asked for after a while (imgbb pulling them from slow storage),
// then load in under a second. So:
// - downloads start fast (32 at once) and drop to 4 only when imgbb really answers 503/429, speeding back up after
//   a run of successes;
// - the page waits at most 8 s, then shows its next source, while the download carries on here in the background
//   (up to a minute) and is stored, so the right art is there next time.
const CACHE = "art-v1"; // bump to start over with an empty cache
const HOSTS = new Set(["i.ibb.co", "archives.bulbagarden.net"]);
const THROTTLED = "i.ibb.co";
const FAST = 32, SLOW = 4, STEP = 4, OK_TO_SPEED_UP = 8;
const PAGE_WAIT = 8000;       // how long the page waits for an image before using its next source
const DOWNLOAD_LIMIT = 60000; // how long a download may carry on in the background

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", ev => ev.waitUntil((async () => {
  for (const key of await caches.keys()) if (key !== CACHE) await caches.delete(key);
  await self.clients.claim();
})()));

self.addEventListener("fetch", ev => {
  const req = ev.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (!HOSTS.has(url.hostname)) return;
  const job = load(req.url, url.hostname === THROTTLED);
  ev.waitUntil(job);   // keeps a slow download (and its storing) going after the page has moved on
  ev.respondWith(Promise.race([job, wait(PAGE_WAIT)]).then(res => res || Response.error()));
});

const wait = ms => new Promise(r => setTimeout(() => r(null), ms));

// one download per address at a time: a second request for the same image joins the first
const inFlight = new Map();
function load(url, throttled) {
  if (!inFlight.has(url)) {
    const job = (async () => {
      const cache = await caches.open(CACHE);
      const hit = await cache.match(url);
      if (hit) return hit;
      const started = Date.now();
      const res = throttled ? await queued(() => download(url, true)) : await download(url, false);
      if (res.ok) {
        await cache.put(url, res.clone()).catch(() => {}); // a full disk just means no caching
        // the page gave up on this one and shows another source: tell it the right art is here now
        if (Date.now() - started >= PAGE_WAIT)
          for (const client of await self.clients.matchAll()) client.postMessage({ type: "art-ready", url });
      }
      return res;
    })().catch(() => Response.error()).finally(() => inFlight.delete(url));
    inFlight.set(url, job);
  }
  // every caller gets its own copy, so the page and a later request can both read the image
  return inFlight.get(url).then(res => (res.type === "error" ? res : res.clone()));
}

// a download, retried twice (2 s and 5 s later) after a 503/429, other 5xx or a network error
async function download(url, throttled) {
  for (let attempt = 0; ; attempt++) {
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), DOWNLOAD_LIMIT);
    try {
      // no referrer: Bulbapedia refuses image requests that carry another site's address
      const res = await fetch(url, { mode: "cors", credentials: "omit", referrerPolicy: "no-referrer", signal: ctl.signal });
      if (throttled) (res.status === 503 || res.status === 429 ? slowDown : speedUp)();
      if (res.ok || res.status < 500 && res.status !== 429 || attempt >= 2) return res;
    } catch (err) {
      if (ctl.signal.aborted || attempt >= 2) return Response.error();
    } finally {
      clearTimeout(timer);
    }
    await new Promise(r => setTimeout(r, (attempt ? 5000 : 2000) + Math.random() * 1000));
  }
}

// how many imgbb downloads may run at once: fast until imgbb complains, then slow, then gradually fast again
let limit = FAST, okInARow = 0, busy = 0;
const waiting = [];
function slowDown() { limit = SLOW; okInARow = 0; }
function speedUp() {
  if (++okInARow >= OK_TO_SPEED_UP && limit < FAST) { limit = Math.min(FAST, limit + STEP); okInARow = 0; next(); }
}
function queued(job) {
  return new Promise(resolve => {
    waiting.push(() => job().then(resolve, () => resolve(Response.error())).finally(() => { busy--; next(); }));
    next();
  });
}
function next() {
  while (busy < limit && waiting.length) { busy++; waiting.shift()(); }
}
