"""Food photos come from the dataset's `Image URL` column (loaded by the browser). If a link is
missing or broken, a clean placeholder is shown instead."""
import html
import urllib.parse


def placeholder_uri(dark=False):
    a, b, ink = ("#1B3A6B", "#0F274D", "#7F9CC8") if dark else ("#E3ECF8", "#C9D9EF", "#8AA6CF")
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 240'><defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>"
           f"<stop offset='0' stop-color='{a}'/><stop offset='1' stop-color='{b}'/></linearGradient></defs><rect width='400' height='240' fill='url(#g)'/>"
           f"<circle cx='200' cy='105' r='46' fill='none' stroke='{ink}' stroke-width='8' opacity='.7'/>"
           f"<path d='M120 175 Q200 215 280 175' fill='none' stroke='{ink}' stroke-width='8' opacity='.7'/></svg>")
    return "data:image/svg+xml;utf8," + urllib.parse.quote(svg)


def food_image(url, name, dark=False):
    ph = placeholder_uri(dark)
    src = html.escape(str(url), quote=True) if isinstance(url, str) and url.startswith("http") else ph
    return (f"<img class='pimg' src='{src}' alt='{html.escape(name)}' referrerpolicy='no-referrer' "
            f"onerror=\"this.onerror=null;this.src='{ph}'\"/>")
