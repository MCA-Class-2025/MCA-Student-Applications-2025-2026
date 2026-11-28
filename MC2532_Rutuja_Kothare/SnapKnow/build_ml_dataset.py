"""
build_ml_dataset.py — turns SnapKnow data into an ML-ready CSV.

Output: snapknow_ml_dataset.csv  (one row per unique image; clean labels; numeric features)

MODE 1 — from your saved history (offline, no API calls):
    python build_ml_dataset.py

MODE 2 — label a whole folder of images with the AI (this is how you get a BIG dataset):
    python build_ml_dataset.py --folder my_images --provider gemini
    Put images in sub-folders named after the true class to also get a `true_label`
    ground-truth column, e.g.  my_images/Animal/*.jpg   my_images/Food/*.jpg
    (API key is read from .env: GOOGLE_API_KEY / Google_api_key, or ANTHROPIC_API_KEY.)

OPTIONAL — add columns from the free external APIs (needs internet, slower):
    python build_ml_dataset.py --enrich

Results from the AI are cached in snapknow_ml_cache.json, so re-running never
re-calls the API for an image it has already analysed.
"""

import argparse
import base64
import hashlib
import io
import json
import os
import re
import time

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(HERE, "snapknow_history.json")
CACHE_FILE = os.path.join(HERE, "snapknow_ml_cache.json")
DEFAULT_OUT = os.path.join(HERE, "snapknow_ml_dataset.csv")
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif")

# The 9 categories the model is asked to choose from (see core.ANALYSIS_PROMPT).
VALID_CATEGORIES = ["Animal", "Flower", "Food", "Vegetable", "Fruit", "Object", "Place", "Person", "Other"]


# ---------------------------------------------------------------- cleaning
def clean_label(text: str) -> str:
    """'Animal.' -> 'Animal', 'Pasta with sauce.' -> 'Pasta with sauce'."""
    return re.sub(r"\s+", " ", (text or "").strip()).rstrip(".:;, ").strip()


def clean_category(text: str) -> str:
    c = clean_label(text)
    for v in VALID_CATEGORIES:  # normalise case / stray words
        if c.lower() == v.lower() or c.lower().startswith(v.lower()):
            return v
    return "Other" if c else ""


def clean_confidence(text) -> float:
    m = re.search(r"\d+(\.\d+)?", str(text or ""))
    return min(100.0, float(m.group())) if m else np.nan


def n_words(text: str) -> int:
    return len(re.findall(r"\w+", text or ""))


# ---------------------------------------------------------- image features
def image_features(image_bytes: bytes) -> dict:
    """Simple, interpretable computer-vision features — good for classic ML
    (random forest, logistic regression, k-means) without needing a GPU."""
    img = Image.open(io.BytesIO(image_bytes))
    w, h = img.size
    rgb = img.convert("RGB")
    small = rgb.copy()
    small.thumbnail((256, 256))
    a = np.asarray(small, dtype=np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]

    hsv = np.asarray(small.convert("HSV"), dtype=np.float32)
    hue, sat, val = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255, hsv[..., 2] / 255
    gray = np.asarray(small.convert("L"), dtype=np.float32)

    # sharpness: variance of a Laplacian-like filter; edge density: share of strong gradients
    lap = np.asarray(small.convert("L").filter(ImageFilter.FIND_EDGES), dtype=np.float32)
    gy, gx = np.gradient(gray)
    grad = np.hypot(gx, gy)

    # colourfulness (Hasler & Süsstrunk 2003)
    rg, yb = r - g, 0.5 * (r + g) - b
    colorfulness = float(np.hypot(rg.std(), yb.std()) + 0.3 * np.hypot(rg.mean(), yb.mean()))

    # share of pixels in 6 hue families (only for reasonably saturated pixels)
    mask = sat > 0.2
    hue_bins = np.histogram(hue[mask], bins=6, range=(0, 360))[0] / max(1, mask.sum())

    return {
        "img_width": w,
        "img_height": h,
        "img_aspect_ratio": round(w / h, 4),
        "img_megapixels": round(w * h / 1e6, 4),
        "img_size_kb": round(len(image_bytes) / 1024, 2),
        "mean_r": round(float(r.mean()), 3),
        "mean_g": round(float(g.mean()), 3),
        "mean_b": round(float(b.mean()), 3),
        "std_r": round(float(r.std()), 3),
        "std_g": round(float(g.std()), 3),
        "std_b": round(float(b.std()), 3),
        "brightness": round(float(val.mean()), 4),
        "contrast": round(float(gray.std()), 3),
        "mean_saturation": round(float(sat.mean()), 4),
        "colorfulness": round(colorfulness, 3),
        "sharpness": round(float(lap.var()), 3),
        "edge_density": round(float((grad > 30).mean()), 4),
        "hue_red_share": round(float(hue_bins[0]), 4),  # 0-60°
        "hue_yellow_share": round(float(hue_bins[1]), 4),  # 60-120°
        "hue_green_share": round(float(hue_bins[2]), 4),  # 120-180°
        "hue_cyan_share": round(float(hue_bins[3]), 4),  # 180-240°
        "hue_blue_share": round(float(hue_bins[4]), 4),  # 240-300°
        "hue_magenta_share": round(float(hue_bins[5]), 4),  # 300-360°
    }


# ----------------------------------------------------------- text features
def text_features(res: dict) -> dict:
    cap, desc = res.get("CAPTION", ""), res.get("DESCRIPTION", "")
    det, fun, name = res.get("DETAILS", ""), res.get("FUN_FACT", ""), res.get("NAME", "")
    return {
        "name_word_count": n_words(name),
        "caption_word_count": n_words(cap),
        "description_word_count": n_words(desc),
        "details_word_count": n_words(det),
        "fun_fact_word_count": n_words(fun),
        "details_number_count": len(re.findall(r"\d+", det)),  # years, sizes, lifespans...
        "has_followup_answer": int(bool(res.get("ANSWER"))),
    }


# --------------------------------------------------------------- AI labels
def _load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=1)


def analyse_folder(folder, provider, model, api_key, delay, limit):
    """Run every image in `folder` through core.analyze_image (cached)."""
    from core import analyze_image, guess_media_type_from_bytes, parse_response, resize_image_bytes

    prov = {"gemini": "Google Gemini", "claude": "Anthropic Claude", "ollama": "Ollama"}[provider]
    cache, records = _load_cache(), []
    files = []
    for root, _, names in os.walk(folder):
        for n in sorted(names):
            if n.lower().endswith(IMG_EXT):
                rel = os.path.relpath(root, folder)
                files.append((os.path.join(root, n), "" if rel == "." else rel.split(os.sep)[0]))
    if limit:
        files = files[:limit]
    print(f"Found {len(files)} images in {folder}")

    for i, (path, true_label) in enumerate(files, 1):
        raw = open(path, "rb").read()
        key = hashlib.md5(raw).hexdigest()[:12]
        if key not in cache:
            small = resize_image_bytes(raw)
            for attempt in range(3):
                try:
                    text = analyze_image(small, guess_media_type_from_bytes(small), api_key, model, prov)
                    cache[key] = parse_response(text)
                    break
                except Exception as e:  # rate limits etc.
                    print(f"  retry {attempt + 1}/3 for {os.path.basename(path)}: {e}")
                    time.sleep(delay * (attempt + 2))
            else:
                print(f"  SKIPPED {path}")
                continue
            _save_cache(cache)
            time.sleep(delay)
        print(f"[{i}/{len(files)}] {os.path.basename(path)} -> {cache[key].get('CATEGORY')} / {cache[key].get('NAME')}")
        records.append(
            {
                "result": cache[key],
                "image_bytes": raw,
                "source": os.path.relpath(path, folder),
                "true_label": true_label,
            }
        )
    return records


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return [
        {
            "result": e["result"],
            "image_bytes": base64.b64decode(e["image_b64"]),
            "source": "history",
            "true_label": e["result"].get("TRUE_LABEL", ""),
        }
        for e in data
        if e.get("image_b64")
    ]


# ------------------------------------------------------- optional enrichment
def enrich_row(res: dict) -> dict:
    """Extra columns from the free APIs in extra_apis.py (internet needed)."""
    import extra_apis as ex

    name, cat = res.get("NAME", ""), res.get("CATEGORY", "").lower()
    out = {"wikidata_found": 0, "wikidata_fact_count": 0}
    wd = ex.wikidata_lookup(name)
    if wd:
        out.update(wikidata_found=1, wikidata_fact_count=len(wd["facts"]))
    if cat in ("animal", "flower"):
        t = ex.inaturalist_lookup(name)
        out["inat_found"] = int(bool(t))
        out["inat_observations"] = t.get("observations") if t else np.nan
        out["inat_conservation_status"] = (t or {}).get("conservation") or ""
    if cat in ("food", "fruit", "vegetable"):
        f = ex.openfoodfacts_lookup(name)
        out["off_found"] = int(bool(f))
        out["off_nutriscore"] = (f or {}).get("nutriscore") or ""
        out["off_nova_group"] = (f or {}).get("nova_group") if f else np.nan
        out["off_allergen_count"] = len((f or {}).get("allergens", [])) if f else np.nan
    if cat == "place":
        g = ex.nominatim_geocode(name)
        out["geo_found"] = int(bool(g))
        if g:
            out["latitude"], out["longitude"] = g["lat"], g["lon"]
            c = ex.restcountries_lookup(g["country_code"])
            if c:
                out["country"] = c.get("name")
                out["country_population"] = c.get("population")
    time.sleep(1.1)  # be polite to Nominatim (1 request/second)
    return out


# -------------------------------------------------------------------- main
def build(records, enrich=False) -> pd.DataFrame:
    rows, seen = [], set()
    for rec in records:
        raw = rec["image_bytes"]
        h = hashlib.md5(raw).hexdigest()[:12]
        if h in seen:  # same photo analysed twice -> keep one row
            continue
        seen.add(h)
        res = {
            k: clean_label(v) if k in ("CATEGORY", "NAME", "CONFIDENCE") else (v or "").strip()
            for k, v in rec["result"].items()
        }
        row = {
            "image_id": h,
            "image_filename": f"{h}.{(Image.open(io.BytesIO(raw)).format or 'JPEG').lower()}",
            "source": rec["source"],
            # ---- labels / targets ----
            "category": clean_category(res.get("CATEGORY", "")),
            "name": res.get("NAME", ""),
            "true_label": rec["true_label"],
            "confidence": clean_confidence(res.get("CONFIDENCE")),
            # ---- raw text (for NLP / TF-IDF / embeddings) ----
            "caption": res.get("CAPTION", ""),
            "description": res.get("DESCRIPTION", ""),
            "details": res.get("DETAILS", ""),
            "fun_fact": res.get("FUN_FACT", ""),
        }
        row.update(text_features(res))
        row.update(image_features(raw))
        if enrich:
            print(f"Enriching {row['name']} ...")
            row.update(enrich_row(res))
        rows.append(row)

    df = pd.DataFrame(rows)
    if "true_label" in df and (df["true_label"] == "").all():
        df = df.drop(columns="true_label")  # no ground truth available
    else:
        df["ai_correct"] = (df["category"].str.lower() == df["true_label"].str.lower()).astype(int)
    return df


def main():
    load_dotenv(os.path.join(HERE, ".env"))
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--folder", help="folder of images to analyse with the AI (sub-folder names = true labels)")
    ap.add_argument("--provider", default="gemini", choices=["gemini", "claude", "ollama"])
    ap.add_argument("--model", default=None)
    ap.add_argument("--api-key", default=None)
    ap.add_argument("--delay", type=float, default=4.0, help="seconds between API calls (free tier rate limits)")
    ap.add_argument("--limit", type=int, default=0, help="only analyse the first N images")
    ap.add_argument("--enrich", action="store_true", help="add columns from the free external APIs")
    ap.add_argument("--no-history", action="store_true", help="when using --folder, don't also include saved history")
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()

    records = [] if (args.folder and args.no_history) else load_history()
    if args.folder:
        env = {k.lower(): v for k, v in os.environ.items()}
        key = args.api_key or (
            env.get("google_api_key") or env.get("gemini_api_key")
            if args.provider == "gemini"
            else env.get("anthropic_api_key") if args.provider == "claude" else "http://localhost:11434"
        )
        if not key:
            raise SystemExit("No API key found — pass --api-key or set it in .env")
        model = (
            args.model
            or {"gemini": "gemini-3.6-flash", "claude": "claude-sonnet-4-6", "ollama": "llava"}[args.provider]
        )
        records += analyse_folder(args.folder, args.provider, model, key, args.delay, args.limit)

    df = build(records, enrich=args.enrich)
    df.to_csv(args.out, index=False, encoding="utf-8")
    print(f"\nSaved {len(df)} rows x {len(df.columns)} columns -> {args.out}")
    print(df["category"].value_counts().to_string())


if __name__ == "__main__":
    main()
