"""One-off patch: imgbb answers bursts of requests with 503, which left shiny art blank. Its images are now requested
a few at a time (nearest cards first, as the observer hands them over), and a failed one is retried twice with a
growing pause before falling back to the next source. Loaded images stay in the browser cache (imgbb sends a 10-year
max-age), so this only matters the first time.
"""
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "index.template.html"
src = SRC.read_text(encoding="utf-8")


def rep(old, new):
    global src
    assert src.count(old) == 1, (old[:80], src.count(old))
    src = src.replace(old, new)


rep("""// Cards start loading their two artworks when they come within about a screen of view:""",
    """// imgbb answers bursts with 503s: its art is fetched a few images at a time, in the order cards come into view
const IMGBB_MAX = 4;
let imgbbBusy = 0;
const imgbbQueue = [];
function setSrc(img, url) {
  if (!url.startsWith(IMGBB)) { img.src = url; return; }
  imgbbQueue.push([img, url]);
  pumpImgbb();
}
function pumpImgbb() {
  while (imgbbBusy < IMGBB_MAX && imgbbQueue.length) {
    const [img, url] = imgbbQueue.shift();
    imgbbBusy++;
    const done = () => {
      img.removeEventListener("load", done); img.removeEventListener("error", done);
      imgbbBusy--; pumpImgbb();
    };
    img.addEventListener("load", done); img.addEventListener("error", done);
    img.src = url;
  }
}

// Cards start loading their two artworks when they come within about a screen of view:""")
rep("""      if (img.dataset.srcset) img.srcset = img.dataset.srcset;
      img.src = img.dataset.src;
      img.removeAttribute("data-src");""", """      if (img.dataset.srcset) img.srcset = img.dataset.srcset;
      setSrc(img, img.dataset.src);
      img.removeAttribute("data-src");""")
rep("""  const e = byId.get(img.closest(".card").dataset.id);
  const list = e.srcs[img.dataset.k];
  const next = (Number(img.dataset.step) || 0) + 1;""", """  const e = byId.get(img.closest(".card").dataset.id);
  const list = e.srcs[img.dataset.k];
  // a busy imgbb (503) gets two more tries, 2 s and 5 s later, before the next source is used
  const tries = Number(img.dataset.retry) || 0;
  if (img.src.startsWith(IMGBB) && tries < 2) {
    const url = img.src;
    img.dataset.retry = String(tries + 1);
    img.removeAttribute("src");
    setTimeout(() => setSrc(img, url), (tries ? 5000 : 2000) + Math.random() * 1000);
    return;
  }
  const next = (Number(img.dataset.step) || 0) + 1;""")

SRC.write_text(src, encoding="utf-8")
print("ok")
