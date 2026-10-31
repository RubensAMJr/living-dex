"""Measure how many shiny artworks imgbb serves at once before it starts answering 503.

Sends bursts of N requests at the same time (HTTP/2, like the browser) for N = 4, 8, 16, 32, 64, 100, each burst
with different images, pausing between bursts, and prints for each: status codes, failures, typical and slowest time.

    py tools/test_imgbb.py            # all levels
    py tools/test_imgbb.py 32 64      # only these levels

Needs curl with HTTP/2 (Git for Windows' curl has it). Uses about 15 MB.
"""
import collections
import json
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEVELS = [int(a) for a in sys.argv[1:]] or [4, 8, 16, 32, 64, 100]
PER_LEVEL = 64      # requests per burst level (at least one full wave even at 64)
PAUSE = 20          # seconds between levels, so one level's limit doesn't spill into the next
TIMEOUT = 15
# Windows' own curl.exe (System32) has no HTTP/2 and would be picked first by name, so ask for Git's by path
CURL = shutil.which("curl", path=r"C:\Program Files\Git\mingw64\bin") or shutil.which("curl")


FAILED = []


def shiny_urls():
    page = (ROOT / "index.html").read_text(encoding="utf-8")
    rows = json.loads(re.search(r"const DATA = (\[.*?\]);\r?\n", page, re.S).group(1))
    return [f"https://i.ibb.co/{row[8]}/{row[6]}.png" for row in rows if row[8]]


def burst(urls, at_once):
    """[(http status, seconds)] for urls fetched at most at_once at a time over one HTTP/2 connection"""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as cfg:
        for u in urls:
            cfg.write(f'url = "{u}"\noutput = "nul"\n')
    out = subprocess.run([CURL, "--silent", "--http2", "--parallel", "--parallel-immediate", "--parallel-max", str(at_once),
                          "--max-time", str(TIMEOUT), "--write-out", "%{http_code} %{time_total} %{url_effective}\\n", "--config", cfg.name],
                         capture_output=True, text=True)
    Path(cfg.name).unlink()
    rows = [line.split() for line in out.stdout.split("\n") if line.strip()]
    FAILED.extend(u for c, _, u in rows if c != "200")
    # curl writes times with the system's decimal separator (a comma on a Portuguese Windows)
    return [(int(code), float(t.replace(",", "."))) for code, t, _ in rows]


def main():
    urls = shiny_urls()
    start = 0
    print(f"{'at once':>8} {'requests':>9}  {'statuses':<28} {'typical':>8} {'slowest':>8} {'wall':>6}")
    for n, level in enumerate(LEVELS):
        if n:
            time.sleep(PAUSE)
        batch = urls[start:start + PER_LEVEL]
        start += PER_LEVEL
        t0 = time.time()
        results = burst(batch, level)
        wall = time.time() - t0
        codes = collections.Counter("timeout" if c == 0 else c for c, _ in results)
        times = [t for c, t in results if c == 200]
        typical = f"{statistics.median(times):.2f}s" if times else "-"
        slowest = f"{max(times):.2f}s" if times else "-"
        print(f"{level:>8} {len(results):>9}  {', '.join(f'{k}: {v}' for k, v in codes.most_common()):<28} "
              f"{typical:>8} {slowest:>8} {wall:5.1f}s", flush=True)
    if FAILED:
        # same images again, one at a time: a failure that repeats is that image, not the burst size
        time.sleep(PAUSE)
        again = burst(list(FAILED), 1)
        print(f"\nfailed ones retried one at a time: {collections.Counter('timeout' if c == 0 else c for c, _ in again).most_common()}")
        for u in FAILED[:len(again)]:
            print("  ", u)


if __name__ == "__main__":
    main()
