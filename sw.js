// Image cache for the Living Dex Checklist.
// Artwork from imgbb (shiny) and Bulbapedia (regular) is kept on this device after its first download, so later
// visits show it instantly without asking those sites again. Only real downloads go out, a few at a time for
// imgbb (it answers bursts with 503s), and a failed or silent one is retried twice before the page falls back to
// the next source. Only successful responses are stored: both hosts allow CORS, so the status can be checked.
const CACHE = "art-v1"; // bump to start over with an empty cache
const HOSTS = new Set(["i.ibb.co", "archives.bulbagarden.net"]);
const THROTTLED = "i.ibb.co";
const MAX_AT_ONCE = 4;
const TIMEOUT = 6000;

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
  ev.respondWith(cached(req.url, url.hostname === THROTTLED));
});

async function cached(url, throttled) {
  const cache = await caches.open(CACHE);
  const hit = await cache.match(url);
  if (hit) return hit;
  const res = throttled ? await queued(() => download(url)) : await download(url);
  if (res.ok) cache.put(url, res.clone()).catch(() => {}); // a full disk just means no caching
  return res;
}

// one download with up to two retries (2 s and 5 s later) for 503s, other 5xx and network errors; a request that
// gets no answer at all is tried only once more, so the page can move on to the next source quickly
async function download(url) {
  let silent = 0;
  for (let attempt = 0; ; attempt++) {
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), TIMEOUT);
    try {
      // no referrer: Bulbapedia refuses image requests that carry another site's address
      const res = await fetch(url, { mode: "cors", credentials: "omit", referrerPolicy: "no-referrer", signal: ctl.signal });
      if (res.ok || res.status < 500 || attempt >= 2) return res;
    } catch (err) {
      if (ctl.signal.aborted) silent++;
      if (attempt >= 2 || silent >= 2) return Response.error();
    } finally {
      clearTimeout(timer);
    }
    await new Promise(r => setTimeout(r, (attempt ? 5000 : 2000) + Math.random() * 1000));
  }
}

let busy = 0;
const waiting = [];
function queued(job) {
  return new Promise(resolve => {
    waiting.push(() => job().then(resolve, () => resolve(Response.error())).finally(() => { busy--; next(); }));
    next();
  });
}
function next() {
  while (busy < MAX_AT_ONCE && waiting.length) { busy++; waiting.shift()(); }
}
