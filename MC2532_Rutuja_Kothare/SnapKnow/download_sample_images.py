"""
download_sample_images.py — fetches ~50 real, freely licensed photos from Wikimedia Commons
(no API key needed) and packs them into sample_images.zip, ready for the app's
📦 Bulk Import. Sub-folders are named after the class, so they become `true_label`s.

    python download_sample_images.py
    -> sample_images/<Class>/*.jpg   +   sample_images/CREDITS.csv   +   sample_images.zip

Then:  streamlit run app.py  ->  📦 Bulk Import  ->  upload sample_images.zip  ->  Analyze all.

Images come from Wikimedia Commons under free licences (CC / public domain) that require
attribution — CREDITS.csv records the author and licence of every photo; keep it with the project.
"""

import csv
import json
import os
import re
import shutil
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "sample_images")
API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "SnapKnow/1.0 (student project; image dataset for ML)"}

# class -> search terms (one photo per term, so every image shows a different subject)
PLAN = {
    "Animal": ["tiger", "elephant", "giraffe", "red panda", "flamingo", "owl", "koala", "zebra", "penguin", "peacock"],
    "Flower": ["sunflower", "red rose", "lotus flower", "tulip", "orchid", "daisy", "marigold", "hibiscus"],
    "Food": [
        "pizza",
        "sushi",
        "hamburger",
        "biryani",
        "masala dosa",
        "pancakes",
        "spaghetti",
        "samosa",
        "ice cream",
        "salad bowl",
    ],
    "Fruit": ["banana", "mango", "strawberry", "pineapple", "watermelon"],
    "Vegetable": ["tomato", "carrot", "broccoli", "cauliflower", "eggplant"],
    "Place": ["Taj Mahal", "Eiffel Tower", "Gateway of India", "Colosseum", "Statue of Liberty", "Sydney Opera House"],
    "Object": ["bicycle", "wristwatch", "acoustic guitar", "laptop", "backpack", "camera"],
}


def _get(url: str, binary: bool = False):
    """Fetch a URL. If Wikimedia says 'Too Many Requests' (429), wait and retry."""
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
            return data if binary else json.loads(data.decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 4:
                raise
            wait = int(e.headers.get("Retry-After") or 0) or 15 * (attempt + 1)
            print(f"      rate-limited, waiting {wait}s ...")
            time.sleep(wait)


def search_photo(term: str, used: set):
    """Return (thumb_url, title, artist, licence, page_url) for the first suitable JPEG, or None."""
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": f"{term} filetype:bitmap",
        "gsrnamespace": 6,
        "gsrlimit": 12,
        "prop": "imageinfo",
        "iiprop": "url|mime|size|extmetadata",
        "iiurlwidth": 800,
    }
    data = _get(API + "?" + urllib.parse.urlencode(params))
    pages = sorted((data.get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    for p in pages:
        info = (p.get("imageinfo") or [{}])[0]
        if info.get("mime") != "image/jpeg" or p["title"] in used:
            continue
        if min(info.get("width", 0), info.get("height", 0)) < 400:
            continue
        meta = info.get("extmetadata") or {}
        artist = re.sub(r"<[^>]+>", "", (meta.get("Artist") or {}).get("value", "unknown")).strip()
        licence = (meta.get("LicenseShortName") or {}).get("value", "unknown")
        return info.get("thumburl") or info.get("url"), p["title"], artist, licence, info.get("descriptionurl", "")
    return None


def main():
    """Download the photos. Safe to re-run: photos already downloaded are kept and skipped."""
    os.makedirs(OUT_DIR, exist_ok=True)
    credits_path = os.path.join(OUT_DIR, "CREDITS.csv")
    used, credits, failed = set(), [], []
    if os.path.exists(credits_path):
        with open(credits_path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))[1:]
        credits = [r for r in rows if os.path.exists(os.path.join(OUT_DIR, r[0], r[1]))]
        used = {r[2] for r in credits}
    total = sum(len(v) for v in PLAN.values())
    n = 0
    for cls, terms in PLAN.items():
        os.makedirs(os.path.join(OUT_DIR, cls), exist_ok=True)
        for term in terms:
            n += 1
            fname = re.sub(r"[^a-z0-9]+", "_", term.lower()).strip("_") + ".jpg"
            if os.path.exists(os.path.join(OUT_DIR, cls, fname)):
                print(f"[{n}/{total}] already have {cls}/{fname}")
                continue
            try:
                hit = search_photo(term, used)
                if not hit:
                    raise RuntimeError("no suitable photo found")
                url, title, artist, licence, page = hit
                data = _get(url, binary=True)
                with open(os.path.join(OUT_DIR, cls, fname), "wb") as f:
                    f.write(data)
                used.add(title)
                credits.append([cls, fname, title, artist, licence, page])
                print(f"[{n}/{total}] {cls}/{fname}  ({licence})")
            except Exception as e:
                failed.append(term)
                print(f"[{n}/{total}] FAILED {term}: {e}")
            time.sleep(2.0)  # be polite to Wikimedia

    with open(os.path.join(OUT_DIR, "CREDITS.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["class", "file", "commons_title", "author", "licence", "source_page"])
        w.writerows(credits)

    zip_path = shutil.make_archive(os.path.join(HERE, "sample_images"), "zip", HERE, "sample_images")
    print(f"\nDownloaded {len(credits)}/{total} photos -> {zip_path}")
    if failed:
        print("Failed: just run this script again, it only downloads the missing ones:", ", ".join(failed))


if __name__ == "__main__":
    main()