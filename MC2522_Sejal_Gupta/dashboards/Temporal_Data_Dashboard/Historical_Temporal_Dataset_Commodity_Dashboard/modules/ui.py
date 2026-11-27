"""CSS and small HTML snippets (KPI cards, chart titles, commodity panel)."""
import html
import numpy as np
from .data import fmt_price
from .images import commodity_image, placeholder_uri


def css(t):
    dark = t["mode"] == "dark"
    fam = t["font"].replace(" ", "+")
    return f"""<style>
@import url('https://fonts.googleapis.com/css2?family={fam}:wght@400;600;700;800&display=swap');
html, body, .stApp, [data-testid="stMarkdownContainer"] *, label, button p, input, div[data-baseweb="select"] *, .ct, .kpi * {{font-family:'{t["font"]}',system-ui,sans-serif !important}}
#MainMenu, footer, [data-testid="stDecoration"], [data-testid="stToolbar"] {{display:none !important}}
header[data-testid="stHeader"] {{background:transparent;height:0}}
.stApp {{background:{t['page']};background-attachment:fixed;color:{t['text']};color-scheme:{t['mode']}}}
.block-container {{padding:.7rem 1.3rem .6rem !important;max-width:1600px}}
[data-testid="stVerticalBlock"] {{gap:.6rem}}
.stApp p, .stApp span, .stApp label, .stApp li {{color:{t['text']}}}
[data-testid="stWidgetLabel"] p {{color:{t['text']} !important;font-size:.8rem;font-weight:700;letter-spacing:.01em}}
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, [data-testid="stDateInput"] div[data-baseweb="input"] {{
  background:{t['inp']} !important;border-color:{t['border']} !important;color:{t['text']} !important;min-height:2.3rem}}
div[data-baseweb="select"] *, div[data-baseweb="input"] input {{color:{t['text']} !important}}
span[data-baseweb="tag"] {{background:{t['accent']} !important}} span[data-baseweb="tag"] * {{color:#fff !important}}
div[data-baseweb="popover"] ul, div[data-baseweb="popover"] li, div[data-baseweb="menu"] {{background:{t['card']} !important;color:{t['text']} !important}}
div[data-baseweb="popover"] li:hover {{background:{t['border']} !important}}
[data-testid="stPopoverBody"], [data-testid="stPopoverBody"] > div, div[data-baseweb="popover"] > div, div[data-baseweb="popover"] [data-testid="stVerticalBlock"] {{background:{t['card']} !important;color:{t['text']} !important;border-color:{t['border']} !important}}
[data-testid="stPopoverBody"] div[data-baseweb="select"] > div {{background:{t['inp']} !important}}
[data-testid="stPopoverBody"] [data-testid="stRadio"] label p {{color:{t['text']} !important;font-size:.9rem;font-weight:600}}
button[kind="secondary"], [data-testid="stPopover"] button, .stDownloadButton button {{
  background:{t['card']} !important;color:{t['text']} !important;border:1px solid {t['border']} !important;border-radius:10px;padding:.3rem .6rem;font-weight:700;min-height:2.6rem}}
button[kind="secondary"] *, [data-testid="stPopover"] button *, .stDownloadButton button * {{color:{t['text']} !important}}
[class*="st-key-card"] {{background:{t['card']};border:1px solid {t['border']};border-radius:{t['radius']}px;padding:.6rem .85rem .4rem;
  box-shadow:{t['shadow']}}}
.st-key-card_line, .st-key-card_panel {{height:470px;overflow-y:auto;overflow-x:hidden}}
.banner {{background:{t['banner']};border-radius:{t['radius']}px;padding:0 1.5rem;display:flex;align-items:center;height:64px;margin-bottom:.5rem}}
[data-testid="stMarkdownContainer"]:has(.banner), [data-testid="stMarkdownContainer"]:has(.kpi) {{margin-bottom:0 !important}}
.kpi {{margin-bottom:1rem}}
.banner .bn {{font-size:1.75rem;font-weight:800;margin:0;color:#fff !important;-webkit-text-fill-color:#fff !important;line-height:1.1;letter-spacing:.01em}}
.kpi {{border-radius:{t['radius']}px;padding:1rem 1.2rem;display:flex;gap:1rem;align-items:center;border:1px solid {t['border']};min-height:112px}}
.kpi .ic {{width:6px;align-self:stretch;border-radius:4px;flex:none}}
.kpi .lb {{font-size:.95rem;color:{t['muted']};font-weight:700}} .kpi .vl {{font-size:2.1rem;font-weight:800;line-height:1.15;color:{t['text']}}}
.kpi .vl.sm {{font-size:1.3rem;padding:.25rem 0}} .kpi .sb {{font-size:.85rem;color:{t['muted']}}}
.ct {{font-weight:800;font-size:1.12rem;color:{t['text']};display:flex;align-items:center;gap:.45rem;margin-bottom:.1rem}}
.ct:before {{content:"";width:4px;height:19px;border-radius:2px;background:{t['accent']}}}
.ct .cs {{font-weight:600;font-size:.8rem;color:{t['muted']};margin-left:auto}}
.pimg {{width:100%;height:135px;object-fit:cover;border-radius:12px;display:block}}
.pname {{font-size:1.25rem;font-weight:800;margin:.45rem 0 0;color:{t['text']}}} .psym {{font-size:.78rem;color:{t['muted']};margin-bottom:.4rem}}
.grid2 {{display:grid;grid-template-columns:1fr 1fr;gap:.45rem}}
.sbox {{border:1px solid {t['border']};border-radius:10px;padding:.35rem .6rem;background:{'rgba(255,255,255,.04)' if dark else '#F7FAFD'}}}
.sbox .l {{font-size:.68rem;color:{t['muted']}}} .sbox .v {{font-size:1.02rem;font-weight:800;color:{t['text']}}}
.up {{color:{t['up']} !important}} .down {{color:{t['down']} !important}}
.plist {{max-height:250px;overflow:auto;display:flex;flex-direction:column;gap:.4rem}}
.prow {{display:flex;align-items:center;gap:.6rem;border:1px solid {t['border']};border-radius:10px;padding:.3rem .5rem}}
.prow.f {{border-color:{t['accent']};box-shadow:0 0 0 1px {t['accent']}}}
.prow img {{width:40px;height:40px;border-radius:9px;object-fit:cover;flex:none}}
.prow .n {{font-weight:700;font-size:.82rem;color:{t['text']};line-height:1.1}} .prow .s {{font-size:.68rem;color:{t['muted']}}}
.prow .r {{margin-left:auto;text-align:right;font-size:.8rem;font-weight:700;color:{t['text']}}}
a[data-testid="stPageLink-NavLink"] {{background:{t['card']};border:1px solid {t['border']};border-radius:10px;justify-content:center;padding:.4rem .4rem}}
a[data-testid="stPageLink-NavLink"] p {{color:{t['text']} !important;font-size:.9rem;font-weight:700;margin:0}}
a[data-testid="stPageLink-NavLink"][aria-current="page"] {{background:{t['accent']};border-color:{t['accent']}}}
a[data-testid="stPageLink-NavLink"][aria-current="page"] p {{color:#fff !important}}
[data-testid="stDataFrame"] {{border:1px solid {t['border']};border-radius:10px}}
.hint {{font-size:.76rem;color:{t['muted']};margin:.35rem 0 .2rem}}
.foot {{font-size:.68rem;color:{t['muted']};text-align:center;margin-top:.2rem}}
</style>"""


def banner():
    return "<div class='banner'><div class='bn'>Commodity Market Temporal Analysis</div></div>"


def swatches(themes):
    rows = []
    for n, t in themes.items():
        dots = "".join(f"<span style='display:inline-block;width:14px;height:14px;border-radius:50%;background:{c};margin-right:3px'></span>"
                       for c in [t["bg"] if t["mode"] == "light" else t["card"], t["accent"]] + t["palette"][:3])
        rows.append(f"<div style='display:flex;align-items:center;justify-content:space-between;gap:.6rem;margin:.2rem 0;font-size:.82rem;font-weight:700'>"
                    f"<span>{n}</span><span>{dots}</span></div>")
    return "".join(rows)


def kpi(icon, label, value, sub, tint, small=False):
    return (f"<div class='kpi' style='background:{tint[0]}'><div class='ic' style='background:{tint[1].replace(".18",".95").replace(".20",".95")}'></div>"
            f"<div><div class='lb'>{label}</div><div class='vl{' sm' if small else ''}'>{value}</div><div class='sb'>{sub}</div></div></div>")


def title(text, sub=""):
    return f"<div class='ct'>{html.escape(text)}<span class='cs'>{html.escape(sub)}</span></div>"


def _chg(pct):
    if pct is None or not np.isfinite(pct):
        return "<span>—</span>"
    return f"<span class='{'up' if pct >= 0 else 'down'}'>{'▲' if pct >= 0 else '▼'} {abs(pct):.2f}%</span>"


def panel_none(perf, dark):
    img = placeholder_uri(dark)
    h = (f"<img class='pimg' src='{img}'/><div class='pname'>No commodity selected</div>"
         f"<div class='hint'>Pick commodities in the box above to see photo, price and period stats. Charts show all commodities until then.</div>")
    if perf is not None and len(perf):
        top, low = perf.iloc[0], perf.iloc[-1]
        h += (f"<div class='grid2'><div class='sbox'><div class='l'>Top performer</div><div class='v'>{html.escape(top['name'])}</div>{_chg(top['change_pct'])}</div>"
              f"<div class='sbox'><div class='l'>Weakest performer</div><div class='v'>{html.escape(low['name'])}</div>{_chg(low['change_pct'])}</div></div>")
    return h


def panel_single(name, symbol, s, dark):
    img = commodity_image(name, 960) or placeholder_uri(dark)
    return (f"<img class='pimg' src='{img}' alt='{html.escape(name)}'/><div class='pname'>{html.escape(name)}</div>"
            f"<div class='psym'>Symbol: {html.escape(symbol)} · photo: Wikipedia</div>"
            f"<div class='grid2'><div class='sbox'><div class='l'>Latest close</div><div class='v'>{fmt_price(s['latest'])}</div></div>"
            f"<div class='sbox'><div class='l'>Change over range</div><div class='v'>{_chg(s['change_pct'])}</div></div>"
            f"<div class='sbox'><div class='l'>Period high</div><div class='v'>{fmt_price(s['high'])}</div></div>"
            f"<div class='sbox'><div class='l'>Period low</div><div class='v'>{fmt_price(s['low'])}</div></div></div>")


def panel_multi(rows, focus, dark):
    out = ["<div class='plist'>"]
    for name, symbol, s in rows:
        img = commodity_image(name, 120) or placeholder_uri(dark)
        out.append(f"<div class='prow{' f' if name == focus else ''}'><img src='{img}'/><div><div class='n'>{html.escape(name)}</div>"
                   f"<div class='s'>{html.escape(symbol)}</div></div><div class='r'>{fmt_price(s['latest'])}<br>{_chg(s['change_pct'])}</div></div>")
    out.append("</div>")
    return "".join(out)
