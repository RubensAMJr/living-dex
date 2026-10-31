"""Copy the site to the local copy that's opened as a file: D:\\Pokemon\\Living Dex - Web Checker.

    python tools/copy_local.py

index.html becomes "Living Dex Checklist.html"; css/, js/, data/ and icons/ are replaced as a whole. Files from the
old single-file layout (info-data.js, info-places.js, locations/) are removed there, since the page no longer uses them.
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL = Path(r"D:\Pokemon\Living Dex - Web Checker")
FOLDERS = ["css", "js", "data", "icons"]
OLD_LAYOUT = ["info-data.js", "info-places.js", "locations"]

shutil.copy2(ROOT / "index.html", LOCAL / "Living Dex Checklist.html")
for name in FOLDERS:
    if (LOCAL / name).exists():
        shutil.rmtree(LOCAL / name)
    shutil.copytree(ROOT / name, LOCAL / name)
for name in OLD_LAYOUT:
    path = LOCAL / name
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()
print(f"copied to {LOCAL}")
