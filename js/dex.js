// Builds the dex (sections and cards) and loads artwork as cards come into view.

// Each section is written as one block of HTML (much faster than creating 1,082 cards node by
// node); image fallbacks are handled by one listener on <main> instead of one per image.
const main = document.getElementById("main");

const DEX_INFO = window.DEX_INFO || {}; // from data/info-data.js (missing file = no info buttons)

function cardHtml(e) {
  const cls = (sets.normal.has(e.id) ? " cn" : "") + (sets.shiny.has(e.id) ? " cs" : "") + (mode === "shiny" ? " t-shiny" : "") +
              (otSets.normal.has(e.id) ? " on" : "") + (otSets.shiny.has(e.id) ? " os" : "");
  const label = esc(e.label);
  // images get their address only once the card nears the screen (see artIO below)
  const img = (kind, src, extra, alt) =>
    `<img draggable="false" decoding="async" referrerpolicy="no-referrer" width="96" height="96" alt="${alt}" data-k="${kind}" data-src="${esc(src)}"${extra}>`;
  return `<div class="card${cls}" tabindex="0" role="checkbox" aria-checked="${caught.has(e.id)}" data-id="${esc(e.id)}" title="${label}${e.note ? ` (${esc(e.note)})` : ""}">` +
    `<div class="art"><div class="v n" data-ph="#${e.dex}">${img("normal", e.srcs.normal[0], ` data-srcset="${esc(e.srcset)}"`, label)}</div>` +
    `<div class="v s" data-ph="#${e.dex}">${img("shiny", e.srcs.shiny[0], "", `Shiny ${label}`)}</div></div>` +
    (DEX_INFO[e.id] ? `<button type="button" class="info-btn" aria-label="More about ${label}" title="More about ${label}"></button>` : "") +
    `<button type="button" class="ot-btn" aria-label="Original trainer mark for ${label}" title="OT: caught by you (click to toggle)"></button>` +
    `<span class="tick"></span><div class="num">#${pad(e.dex)}</div><div class="name">${label}</div>` +
    (e.note ? `<div class="form">${esc(e.note)}</div>` : "") + `</div>`;
}

const sections = new Map();
let html = "";
for (const g of GROUPS) {
  if (g.form && g === GROUPS.find(x => x.form)) html += `<div class="divider" id="formsDivider"><span>Regional Forms</span></div>`;
  html += `<section data-group="${g.key}"><div class="sec-head"><h2>${esc(g.title)}<small>${esc(g.sub)}</small></h2><span class="count"></span></div>` +
          `<div class="grid">${entries.filter(e => e.group === g).map(cardHtml).join("")}</div></section>`;
}
main.innerHTML = html;
for (const sec of main.querySelectorAll("section")) {
  const g = groupByKey.get(sec.dataset.group);
  sections.set(g.key, { g, sec, count: sec.querySelector(".count") });
}
for (const card of main.querySelectorAll(".card")) byId.get(card.dataset.id).el = card;

// imgbb (shiny art), measured with tools/test_imgbb.py: 100 requests at once without a 503, but some images hang
// for 15+ s the first time they're asked for after a while, then load in under a second. So its images go out fast
// (32 at once), slower (4) only after a real error, and one that hangs is replaced by the next source after 8 s
// while the imgbb copy keeps loading; when it arrives, the card switches to it.
// When the image cache (sw.js) runs the page, it does all this itself and serves saved art instantly.
const swActive = () => !!(navigator.serviceWorker && navigator.serviceWorker.controller);
const IMGBB_FAST = 32, IMGBB_SLOW = 4;
let imgbbLimit = IMGBB_FAST, imgbbOk = 0, imgbbBusy = 0;
const imgbbQueue = [];
function setSrc(img, url) {
  if (!url.startsWith(IMGBB) || swActive()) { img.src = url; return; }
  imgbbQueue.push([img, url]);
  pumpImgbb();
}
function pumpImgbb() {
  while (imgbbBusy < imgbbLimit && imgbbQueue.length) {
    const [img, url] = imgbbQueue.shift();
    imgbbBusy++;
    let finished = false;
    const done = ev => {
      if (finished) return;
      finished = true;
      clearTimeout(timer);
      img.removeEventListener("load", done); img.removeEventListener("error", done);
      // an error (usually a 503) means slow down; a run of successes speeds back up
      if (ev && ev.type === "error") { imgbbLimit = IMGBB_SLOW; imgbbOk = 0; }
      else if (ev && ++imgbbOk >= 8 && imgbbLimit < IMGBB_FAST) { imgbbLimit = Math.min(IMGBB_FAST, imgbbLimit + 4); imgbbOk = 0; }
      imgbbBusy--; pumpImgbb();
    };
    // a hanging image isn't a sign of going too fast: show the next source now, keep loading this one
    const timer = setTimeout(() => {
      done();
      if (img.getAttribute("src") === url && !img.naturalWidth) { img.dataset.retry = "2"; artFailed(img, url); }
    }, 8000);
    img.addEventListener("load", done); img.addEventListener("error", done);
    img.src = url;
  }
}
// The imgbb art arrived late: switch cards that still show a fallback back to it. The image cache says so with a
// message when its background download finishes; without it, the page keeps loading the image itself.
function useLateArt(url) {
  for (const img of document.querySelectorAll(`img[data-late="${CSS.escape(url)}"]`)) {
    img.removeAttribute("data-late");
    if (img.getAttribute("src") === url) continue;
    img.dataset.step = "0";
    img.parentNode.classList.remove("noimg");
    img.src = url;
  }
}
function lateArt(img, url) {
  img.dataset.late = url;
  if (swActive()) return;
  const probe = new Image();
  probe.referrerPolicy = "no-referrer";
  probe.onload = () => useLateArt(url);
  probe.src = url;
}
if (navigator.serviceWorker) navigator.serviceWorker.addEventListener("message", ev => {
  if (ev.data && ev.data.type === "art-ready") useLateArt(ev.data.url);
});

// Cards start loading their two artworks when they come within about a screen of view:
// a fast first paint (no 2,000+ image requests set up at once) and less data on phones
const artIO = new IntersectionObserver(list => {
  for (const it of list) {
    if (!it.isIntersecting) continue;
    artIO.unobserve(it.target);
    for (const img of it.target.querySelectorAll("img[data-src]")) {
      if (img.dataset.srcset) img.srcset = img.dataset.srcset;
      setSrc(img, img.dataset.src);
      img.removeAttribute("data-src");
    }
  }
}, { rootMargin: "1000px 0px" });
for (const e of entries) artIO.observe(e.el);

// Each artwork walks its own source list until one loads, then is decoded ahead of time
// so switching between the regular and shiny dex never waits on an image
function artFailed(img, url = img.src) {
  const e = byId.get(img.closest(".card").dataset.id);
  const list = e.srcs[img.dataset.k];
  // an imgbb error (usually a 503) gets two more tries, 2 s and 5 s later, before the next source is used
  const tries = Number(img.dataset.retry) || 0;
  if (url.startsWith(IMGBB) && tries < 2 && !swActive()) {  // the image cache already retried
    img.dataset.retry = String(tries + 1);
    img.removeAttribute("src");
    setTimeout(() => setSrc(img, url), (tries ? 5000 : 2000) + Math.random() * 1000);
    return;
  }
  if (url.startsWith(IMGBB)) lateArt(img, url);
  const next = (Number(img.dataset.step) || 0) + 1;
  img.removeAttribute("srcset");
  if (next < list.length) { img.dataset.step = String(next); setSrc(img, list[next]); }
  else img.parentNode.classList.add("noimg");
}
main.addEventListener("error", ev => {
  const img = ev.target;
  if (img.tagName !== "IMG" || img.classList.contains("paint") || !img.getAttribute("src")) return;
  artFailed(img);
}, true);
main.addEventListener("load", ev => {
  const img = ev.target;
  if (img.tagName === "IMG" && !img.classList.contains("paint") && img.decode) img.decode().catch(() => {});
}, true);
