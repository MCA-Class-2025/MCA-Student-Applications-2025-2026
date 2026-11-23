"""CSS and small HTML snippets (banner, KPI cards, chart titles, food profile)."""
import html
from .data import MACROS
from .images import food_image


def css(t):
    dark = t["mode"] == "dark"
    fam = t["font"].replace(" ", "+")
    return f"""<style>
@import url('https://fonts.googleapis.com/css2?family={fam}:wght@400;600;700;800&display=swap');
html, body, .stApp, [data-testid="stMarkdownContainer"] *, label, button p, input, div[data-baseweb="select"] *, .ct, .kpi * {{font-family:'{t["font"]}',system-ui,sans-serif !important}}
#MainMenu, footer, [data-testid="stDecoration"], [data-testid="stToolbar"] {{display:none !important}}
header[data-testid="stHeader"] {{background:transparent;height:0}}
.stApp {{background:{t['page']};background-attachment:fixed;color:{t['text']};color-scheme:{t['mode']}}}
.block-container {{padding:.7rem 1.3rem .6rem !important;max-width:1700px}}
.stApp {{font-size:17px}} .stApp p, .stApp li {{font-size:1.02rem}}
[data-testid="stVerticalBlock"] {{gap:.6rem}}
.stApp p, .stApp span, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3 {{color:{t['text']}}}
[data-testid="stWidgetLabel"] p {{color:{t['text']} !important;font-size:.95rem;font-weight:700}}
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {{background:{t['inp']} !important;border-color:{t['border']} !important;color:{t['text']} !important;min-height:2.5rem;font-size:1rem}}
div[data-baseweb="select"] *, div[data-baseweb="input"] input {{color:{t['text']} !important}}
span[data-baseweb="tag"] {{background:{t['accent']} !important}} span[data-baseweb="tag"] * {{color:#fff !important}}
div[data-baseweb="popover"] ul, div[data-baseweb="popover"] li, div[data-baseweb="menu"] {{background:{t['card']} !important;color:{t['text']} !important}}
div[data-baseweb="popover"] li:hover {{background:{t['border']} !important}}
[data-testid="stPopoverBody"], [data-testid="stPopoverBody"] > div, div[data-baseweb="popover"] > div {{background:{t['card']} !important;color:{t['text']} !important;border-color:{t['border']} !important}}
[data-testid="stPopoverBody"] [data-testid="stRadio"] label p {{color:{t['text']} !important;font-size:.9rem;font-weight:600}}
button[kind="secondary"], [data-testid="stPopover"] button, .stDownloadButton button {{background:{t['card']} !important;color:{t['text']} !important;border:1px solid {t['border']} !important;border-radius:10px;font-weight:700;min-height:2.6rem}}
button[kind="secondary"] *, [data-testid="stPopover"] button *, .stDownloadButton button * {{color:{t['text']} !important}}
[class*="st-key-card"] {{background:{t['card']};border:1px solid {t['border']};border-radius:{t['radius']}px;padding:.6rem .85rem .5rem;box-shadow:{t['shadow']}}}
.banner {{background:{t['banner']};border-radius:{t['radius']}px;padding:0 1.5rem;display:flex;align-items:center;height:72px;margin-bottom:.5rem}}
.banner .bn {{font-size:2rem;font-weight:800;color:#fff !important;-webkit-text-fill-color:#fff !important;letter-spacing:.01em}}
.banner .bs {{margin-left:auto;font-size:.8rem;color:#dfe8f5 !important;-webkit-text-fill-color:#dfe8f5 !important}}
.kpi {{border-radius:{t['radius']}px;padding:1rem 1.2rem;display:flex;gap:1rem;align-items:center;border:1px solid {t['border']};background:{t['card']};min-height:104px;box-shadow:{t['shadow']}}}
.kpi .ic {{width:6px;align-self:stretch;border-radius:4px;flex:none}}
.kpi .lb {{font-size:1.05rem;color:{t['muted']};font-weight:700}} .kpi .vl {{font-size:2.6rem;font-weight:800;line-height:1.15;color:{t['text']}}} .kpi .sb {{font-size:.9rem;color:{t['muted']}}}
.ct {{font-weight:800;font-size:1.3rem;color:{t['text']};display:flex;align-items:center;gap:.45rem;margin-bottom:.1rem}}
.ct:before {{content:"";width:4px;height:19px;border-radius:2px;background:{t['accent']}}}
.ct .cs {{font-weight:600;font-size:.9rem;color:{t['muted']};margin-left:auto}}
.pimg {{width:100%;height:250px;object-fit:cover;border-radius:12px;display:block}}
.pname {{font-size:1.9rem;font-weight:800;color:{t['text']};margin:.1rem 0}}
.nm {{font-size:1.1rem;color:{t['muted']}}} .nm b {{color:{t['text']}}}
.grid5 {{display:grid;grid-template-columns:repeat(5,1fr);gap:.45rem;margin-top:.5rem}}
.sbox {{border:1px solid {t['border']};border-radius:10px;padding:.4rem .6rem;background:{'rgba(255,255,255,.04)' if dark else '#F7FAFD'}}}
.sbox .l {{font-size:.82rem;color:{t['muted']}}} .sbox .v {{font-size:1.35rem;font-weight:800;color:{t['text']}}}
.badge {{display:inline-block;border-radius:20px;padding:.2rem .8rem;font-weight:800;font-size:1rem;margin:.3rem .4rem .1rem 0;color:#fff !important}}
.cls {{border:1px solid {t['border']};border-left:5px solid {t['accent']};border-radius:10px;padding:.5rem .8rem;margin-bottom:.5rem}}
.cls .l {{font-size:.82rem;color:{t['muted']};font-weight:700;text-transform:uppercase;letter-spacing:.04em}} .cls .v {{font-size:1.1rem;font-weight:700;color:{t['text']}}}
a[data-testid="stPageLink-NavLink"] {{background:{t['card']};border:1px solid {t['border']};border-radius:10px;justify-content:center;padding:.4rem}}
a[data-testid="stPageLink-NavLink"] p {{color:{t['text']} !important;font-size:1.02rem;font-weight:700;margin:0}}
a[data-testid="stPageLink-NavLink"][aria-current="page"] {{background:{t['accent']};border-color:{t['accent']}}}
a[data-testid="stPageLink-NavLink"][aria-current="page"] p {{color:#fff !important}}
button[data-baseweb="tab"] p {{color:{t['text']} !important;font-weight:700}}
[data-testid="stDataFrame"] {{border:1px solid {t['border']};border-radius:10px}}
.hint {{font-size:.92rem;color:{t['muted']};margin:.3rem 0 .2rem}}
[data-testid="stExpander"] {{background:{t['card']};border:1px solid {t['border']};border-radius:{t['radius']}px}}
[data-testid="stExpander"] summary p {{font-weight:800;font-size:1.1rem}}
[data-testid="stMetricValue"] {{font-size:2rem}}
</style>"""


def banner(sub=""):
    return f"<div class='banner'><div class='bn'>API Fused Dataset Analytics</div><div class='bs'>{html.escape(sub)}</div></div>"


def swatches(themes):
    rows = []
    for n, t in themes.items():
        dots = "".join(f"<span style='display:inline-block;width:14px;height:14px;border-radius:50%;background:{c};margin-right:3px'></span>"
                       for c in [t["bg"] if t["mode"] == "light" else t["card"], t["accent"]] + t["palette"][:3])
        rows.append(f"<div style='display:flex;align-items:center;justify-content:space-between;gap:.6rem;margin:.2rem 0;font-size:.82rem;font-weight:700'><span>{n}</span><span>{dots}</span></div>")
    return "".join(rows)


def kpi(label, value, sub, color):
    return (f"<div class='kpi'><div class='ic' style='background:{color}'></div><div><div class='lb'>{label}</div>"
            f"<div class='vl'>{value}</div><div class='sb'>{sub}</div></div></div>")


def title(text, sub=""):
    return f"<div class='ct'>{html.escape(text)}<span class='cs'>{html.escape(sub)}</span></div>"


def profile_left(r, dark):
    return food_image(r["Image URL"], r["Food Name"], dark)


def profile_mid(r, nutri, nova):
    boxes = "".join(f"<div class='sbox'><div class='l'>{n.split(' (')[0]}</div><div class='v'>{r[n]:g}"
                    f"<span style='font-size:.7rem;font-weight:600'> {n.split('(')[1][:-1]}</span></div></div>" for n in MACROS)
    return (f"<div class='pname'>{html.escape(r['Food Name'])}</div>"
            f"<div class='nm'>Hindi: <b>{html.escape(str(r['Hindi Name']))}</b> &nbsp;·&nbsp; Marathi: <b>{html.escape(str(r['Marathi Name']))}</b></div>"
            f"<span class='badge' style='background:{nutri}'>Nutri-Score {r['Nutri-Score Grade']}</span>"
            f"<span class='badge' style='background:{nova}'>NOVA {r['nova_group']}</span><div class='grid5'>{boxes}</div>")


def profile_right(r):
    return (f"<div class='cls'><div class='l'>Cancer risk classification</div><div class='v'>{html.escape(str(r['Cancer_Risk_Classification']))}</div></div>"
            f"<div class='cls'><div class='l'>Cancer patient support category</div><div class='v'>{html.escape(str(r['Cancer_Patient_Support_Category']))}</div></div>"
            f"<div class='hint'>Assumption: {html.escape(str(r['Assumption']))}</div>")
