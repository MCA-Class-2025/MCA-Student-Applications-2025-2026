"""
extra_apis.py — five additional free, key-free APIs for SnapKnow.

Each function takes the identified NAME and returns a small dict (or None if nothing
was found / the API was unreachable). Nothing here depends on Streamlit, so these can
also be reused from api_server.py later.

  API #8   iNaturalist        — species info, common name, conservation status, photo
  API #9   OpenStreetMap      — Nominatim geocoding (coordinates + address) for places
  API #10  REST Countries     — capital, population, currency, languages, flag
  API #11  Open Food Facts    — Nutri-Score, NOVA group, allergens for packaged food
  API #12  Wikidata           — structured facts for ANY subject (object, person, place...)
"""

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger("snapknow.extra_apis")

_UA = {"User-Agent": "SnapKnow/1.0 (student project)"}


def _clean(name: str) -> str:
    """'Red Fox (Vulpes vulpes), adult' -> 'Red Fox'."""
    if not name:
        return ""
    return name.split(",")[0].split("(")[0].strip()


def _get_json(url: str, timeout: int = 8):
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ---------------------------------------------------------------------------
# API #8 — iNaturalist API (no key needed)
# Species match with common name, rank, conservation status and a reference photo.
# ---------------------------------------------------------------------------
def inaturalist_lookup(name: str):
    query = _clean(name)
    if not query:
        return None
    url = "https://api.inaturalist.org/v1/taxa?" + urllib.parse.urlencode({"q": query, "per_page": 1})
    try:
        data = _get_json(url)
        results = data.get("results") or []
        if not results:
            return None
        t = results[0]
        cons = t.get("conservation_status") or {}
        photo = t.get("default_photo") or {}
        return {
            "scientific_name": t.get("name"),
            "common_name": t.get("preferred_common_name"),
            "rank": t.get("rank"),
            "group": t.get("iconic_taxon_name"),
            "observations": t.get("observations_count"),
            "conservation": cons.get("status_name"),
            "photo": photo.get("medium_url"),
            "photo_credit": photo.get("attribution"),
            "wikipedia_url": t.get("wikipedia_url"),
            "inat_url": f"https://www.inaturalist.org/taxa/{t.get('id')}" if t.get("id") else None,
        }
    except Exception:
        logger.info(f"iNaturalist lookup found nothing for '{name}'", exc_info=True)
        return None


# ---------------------------------------------------------------------------
# API #9 — OpenStreetMap Nominatim geocoding (no key needed)
# Coordinates + address for Place results. (Nominatim policy: identify yourself
# with a User-Agent and keep to ~1 request/second — fine for interactive use.)
# ---------------------------------------------------------------------------
def nominatim_geocode(place_name: str):
    query = _clean(place_name)
    if not query:
        return None
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": query, "format": "jsonv2", "limit": 1, "addressdetails": 1}
    )
    try:
        data = _get_json(url)
        if not data:
            return None
        hit = data[0]
        addr = hit.get("address") or {}
        lat, lon = float(hit["lat"]), float(hit["lon"])
        return {
            "display_name": hit.get("display_name"),
            "lat": lat,
            "lon": lon,
            "country": addr.get("country"),
            "country_code": (addr.get("country_code") or "").upper(),
            "state": addr.get("state"),
            "city": addr.get("city") or addr.get("town") or addr.get("village"),
            "osm_url": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=14/{lat}/{lon}",
        }
    except Exception:
        logger.info(f"Nominatim geocoding found nothing for '{place_name}'", exc_info=True)
        return None


# ---------------------------------------------------------------------------
# API #10 — REST Countries API (no key needed)
# Country facts for a place, looked up by the ISO country code from Nominatim.
# ---------------------------------------------------------------------------
def restcountries_lookup(country_code: str):
    if not country_code:
        return None
    fields = "name,capital,region,subregion,population,area,currencies,languages,flags,timezones"
    url = f"https://restcountries.com/v3.1/alpha/{urllib.parse.quote(country_code)}?fields={fields}"
    try:
        data = _get_json(url)
        c = data[0] if isinstance(data, list) else data
        if not c:
            return None
        currencies = ", ".join(
            f"{v.get('name')} ({v.get('symbol', '')})".replace(" ()", "") for v in (c.get("currencies") or {}).values()
        )
        return {
            "name": (c.get("name") or {}).get("common"),
            "capital": ", ".join(c.get("capital") or []),
            "region": c.get("region"),
            "subregion": c.get("subregion"),
            "population": c.get("population"),
            "area_km2": c.get("area"),
            "currencies": currencies,
            "languages": ", ".join((c.get("languages") or {}).values()),
            "flag": (c.get("flags") or {}).get("png"),
            "timezones": ", ".join((c.get("timezones") or [])[:3]),
        }
    except Exception:
        logger.info(f"REST Countries lookup failed for code '{country_code}'", exc_info=True)
        return None


# ---------------------------------------------------------------------------
# API #11 — Open Food Facts API (no key needed)
# Nutri-Score, NOVA processing group, allergens and ingredients for food products.
# ---------------------------------------------------------------------------
def openfoodfacts_lookup(name: str):
    query = _clean(name)
    if not query:
        return None
    url = "https://world.openfoodfacts.org/cgi/search.pl?" + urllib.parse.urlencode(
        {
            "search_terms": query,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": 5,
            "fields": "product_name,brands,nutriscore_grade,nova_group,allergens_tags,"
            "ingredients_text,image_front_small_url,code",
        }
    )
    try:
        data = _get_json(url, timeout=10)
        products = data.get("products") or []
        # Prefer a product that actually has a Nutri-Score; fall back to the first hit.
        product = next(
            (p for p in products if p.get("nutriscore_grade") in ("a", "b", "c", "d", "e")),
            products[0] if products else None,
        )
        if not product:
            return None
        allergens = [a.split(":")[-1].replace("-", " ") for a in product.get("allergens_tags") or []]
        grade = product.get("nutriscore_grade")
        return {
            "product_name": product.get("product_name") or query,
            "brands": product.get("brands"),
            "nutriscore": grade.upper() if grade in ("a", "b", "c", "d", "e") else None,
            "nova_group": product.get("nova_group"),
            "allergens": allergens,
            "ingredients": product.get("ingredients_text"),
            "image": product.get("image_front_small_url"),
            "url": f"https://world.openfoodfacts.org/product/{product['code']}" if product.get("code") else None,
        }
    except Exception:
        logger.info(f"Open Food Facts lookup found nothing for '{name}'", exc_info=True)
        return None


# ---------------------------------------------------------------------------
# API #12 — Wikidata API (no key needed)
# Structured facts for ANY identified subject — this is the one that covers
# Object / Person / Other results that the species, food and place APIs don't.
# ---------------------------------------------------------------------------
_WD_PROPS = {
    "P31": "Instance of",
    "P279": "Subclass of",
    "P17": "Country",
    "P495": "Country of origin",
    "P27": "Citizenship",
    "P106": "Occupation",
    "P571": "Inception",
    "P569": "Born",
    "P170": "Creator",
    "P178": "Developer",
    "P176": "Manufacturer",
    "P138": "Named after",
}


def wikidata_lookup(name: str, lang: str = "en"):
    query = _clean(name)
    if not query:
        return None
    base = "https://www.wikidata.org/w/api.php?"
    try:
        search = _get_json(
            base
            + urllib.parse.urlencode(
                {
                    "action": "wbsearchentities",
                    "search": query,
                    "language": lang,
                    "format": "json",
                    "limit": 1,
                }
            )
        )
        hits = search.get("search") or []
        if not hits:
            return None
        qid = hits[0]["id"]

        ent = _get_json(
            base
            + urllib.parse.urlencode(
                {
                    "action": "wbgetentities",
                    "ids": qid,
                    "props": "claims",
                    "format": "json",
                }
            )
        )
        claims = ((ent.get("entities") or {}).get(qid) or {}).get("claims") or {}

        raw_facts = {}  # label -> list of raw values (strings or Q-ids)
        to_resolve = set()  # Q-ids we need human-readable labels for
        for pid, label in _WD_PROPS.items():
            for c in (claims.get(pid) or [])[:3]:
                val = ((c.get("mainsnak") or {}).get("datavalue") or {}).get("value")
                if val is None:
                    continue
                if isinstance(val, dict) and val.get("id"):
                    to_resolve.add(val["id"])
                    raw_facts.setdefault(label, []).append(val["id"])
                elif isinstance(val, dict) and val.get("time"):
                    raw_facts.setdefault(label, []).append(val["time"].lstrip("+").split("T")[0])
                elif isinstance(val, str):
                    raw_facts.setdefault(label, []).append(val)

        labels = {}
        if to_resolve:
            lab = _get_json(
                base
                + urllib.parse.urlencode(
                    {
                        "action": "wbgetentities",
                        "ids": "|".join(sorted(to_resolve)),
                        "props": "labels",
                        "languages": lang,
                        "format": "json",
                    }
                )
            )
            for eid, e in (lab.get("entities") or {}).items():
                labels[eid] = ((e.get("labels") or {}).get(lang) or {}).get("value", eid)

        facts = {k: ", ".join(labels.get(v, v) for v in vals) for k, vals in raw_facts.items()}

        image = None
        img_claim = (claims.get("P18") or [None])[0]
        if img_claim:
            fname = ((img_claim.get("mainsnak") or {}).get("datavalue") or {}).get("value")
            if fname:
                image = (
                    "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(fname) + "?width=300"
                )

        return {
            "id": qid,
            "label": hits[0].get("label", query),
            "description": hits[0].get("description"),
            "facts": facts,
            "image": image,
            "url": f"https://www.wikidata.org/wiki/{qid}",
        }
    except Exception:
        logger.info(f"Wikidata lookup found nothing for '{name}'", exc_info=True)
        return None
