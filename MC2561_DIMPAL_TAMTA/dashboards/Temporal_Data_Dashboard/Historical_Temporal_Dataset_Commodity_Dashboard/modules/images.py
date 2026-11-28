"""Real commodity photos, fetched at run time from the Wikipedia REST API (lead image of the article).

No image files ship with the project. If the machine is offline, or an article has no
image, a clean placeholder is shown instead.
"""
import base64
from urllib.parse import quote
import requests
import streamlit as st

WIKI_TITLE = {
    "Cocoa": "Cocoa bean", "Coffee": "Coffee bean", "Cotton": "Cotton", "Gold": "Gold", "Silver": "Silver",
    "Platinum": "Platinum", "Palladium": "Palladium", "Copper": "Copper", "Corn": "Maize", "Wheat": "Wheat",
    "Soybeans": "Soybean", "Sugar": "Sugar", "Live Cattle": "Cattle", "Natural Gas": "Natural gas",
    "Brent Crude Oil": "Brent Crude", "WTI Crude Oil": "West Texas Intermediate",
    "Heating Oil": "Heating oil", "RBOB Gasoline": "Gasoline",
}
_UA = {"User-Agent": "GeoTimeAnalytics/1.0 (student dashboard project; python-requests)"}


def placeholder_uri(dark=False):
    a, b = ("#1B3A6B", "#0F274D") if dark else ("#E3ECF8", "#C9D9EF")
    ink = "#7F9CC8" if dark else "#8AA6CF"
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 240'>"
           f"<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='{a}'/>"
           f"<stop offset='1' stop-color='{b}'/></linearGradient></defs><rect width='400' height='240' fill='url(#g)'/>"
           f"<circle cx='292' cy='72' r='20' fill='{ink}' opacity='.55'/>"
           f"<path d='M40 200 L140 108 L205 168 L255 124 L360 200 Z' fill='{ink}' opacity='.6'/>"
           f"<rect x='1.5' y='1.5' width='397' height='237' fill='none' stroke='{ink}' stroke-width='2' stroke-dasharray='8 6' opacity='.5'/>"
           f"</svg>")
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


@st.cache_data(show_spinner=False, ttl=7 * 24 * 3600)
def commodity_image(name: str, width: int = 960):
    """Return a base64 data-URI of the commodity photo, or None. width: 960 (hero) or 120 (thumbnail)."""
    title = WIKI_TITLE.get(name, name)
    try:
        r = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title.replace(' ', '_'))}",
                         headers=_UA, timeout=6)
        thumb = (r.json().get("thumbnail") or {}).get("source")
        if not thumb:
            return None
        import re
        for w in dict.fromkeys([width, 500, 320]):
            url = re.sub(r"/\d+px-", f"/{w}px-", thumb)
            img = requests.get(url, headers=_UA, timeout=10)
            ctype = img.headers.get("content-type", "")
            if img.ok and ctype.startswith("image/"):
                return f"data:{ctype};base64," + base64.b64encode(img.content).decode()
    except Exception:
        return None
    return None
