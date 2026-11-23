"""dashkit.py - tiny helper that turns Plotly figures into ONE polished, offline HTML dashboard
(dark theme, gradient header, KPI cards, tab navigation) - same look as the GeoTime reference."""
import os, webbrowser
import plotly.graph_objects as go
import plotly.io as pio

PALETTE = ["#ff7a45", "#b05cff", "#3ddc97", "#4cc9f0", "#ffd166", "#ef476f", "#06d6a0", "#8d99ae"]
CARD, GRID, TEXT, MUTED = "#131b33", "#25305a", "#e9edf8", "#93a0c4"

def style(fig, height=380, legend=True):
    """Apply the shared dark theme to a figure."""
    fig.update_layout(
        template="plotly_dark", height=height, colorway=PALETTE,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT, family="Segoe UI, system-ui, sans-serif", size=12),
        margin=dict(l=45, r=20, t=20, b=45), showlegend=legend,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
        hoverlabel=dict(bgcolor="#0b1020", font_size=12))
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID)
    return fig

CSS = """
:root{--bg:#0b1020;--cd:#131b33;--bd:#25305a;--tx:#e9edf8;--mu:#93a0c4;--a1:#ff7a45;--a2:#b05cff}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(1200px 500px at 70% -10%,#2a1b5c55,transparent),var(--bg);
color:var(--tx);font:14px 'Segoe UI',system-ui,sans-serif}
.w{max-width:1320px;margin:auto;padding:14px 16px 40px}
header{padding:20px 24px;border-radius:16px;background:linear-gradient(120deg,#ff7a45,#b05cff);box-shadow:0 8px 30px #b05cff33}
h1{margin:0;font-size:28px;color:#fff}header p{margin:4px 0 0;color:#ffffffd9;font-size:13px}
nav{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}
nav button{font:inherit;color:var(--mu);background:var(--cd);border:1px solid var(--bd);border-radius:999px;padding:8px 18px;cursor:pointer;transition:.2s}
nav button:hover{color:#fff;border-color:var(--a2)}
nav button.on{color:#fff;background:linear-gradient(120deg,#ff7a45,#b05cff);border-color:transparent}
.k{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-bottom:14px}
.k .c{border-top:3px solid var(--a1);padding:12px 16px}.k b{display:block;font-size:28px;margin-top:4px}.k span{color:var(--mu);font-size:12px}
.g{display:grid;grid-template-columns:repeat(12,1fr);gap:12px}
.c{background:var(--cd);border:1px solid var(--bd);border-radius:14px;padding:12px 14px;box-shadow:0 2px 12px #0006;min-width:0}
.c h3{margin:0 0 6px;font-size:12px;letter-spacing:.05em;text-transform:uppercase;color:var(--mu)}
.s4{grid-column:span 4}.s6{grid-column:span 6}.s8{grid-column:span 8}.s12{grid-column:span 12}
@media(max-width:900px){.s4,.s6,.s8{grid-column:span 12}}
.tab{display:none}.tab.on{display:block}
footer{margin-top:24px;text-align:center;color:var(--mu);font-size:12px}
"""

def build(title, subtitle, kpis, tabs, out_path, footer="", open_browser=True):
    """kpis: [(label, value)]   tabs: {tab_name: [(chart_title, fig, span)]}  span in 4/6/8/12"""
    first, tab_html, nav = True, [], []
    for i, (tname, charts) in enumerate(tabs.items()):
        cards = []
        for ctitle, fig, span in charts:
            div = pio.to_html(fig, full_html=False, include_plotlyjs=True if first else False,
                              config={"displaylogo": False, "responsive": True})
            first = False
            cards.append(f'<div class="c s{span}"><h3>{ctitle}</h3>{div}</div>')
        tab_html.append(f'<section class="tab{" on" if i == 0 else ""}" id="t{i}"><div class="g">{"".join(cards)}</div></section>')
        nav.append(f'<button class="{"on" if i == 0 else ""}" onclick="show({i},this)">{tname}</button>')
    kp = "".join(f'<div class="c"><span>{l}</span><b>{v}</b></div>' for l, v in kpis)
    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{CSS}</style></head>
<body><div class="w"><header><h1>{title}</h1><p>{subtitle}</p></header>
<nav>{"".join(nav)}</nav><div class="k">{kp}</div>{"".join(tab_html)}<footer>{footer}</footer></div>
<script>function show(i,b){{document.querySelectorAll('.tab').forEach(t=>t.classList.remove('on'));
document.querySelectorAll('nav button').forEach(t=>t.classList.remove('on'));
document.getElementById('t'+i).classList.add('on');b.classList.add('on');
window.dispatchEvent(new Event('resize'));document.querySelectorAll('#t'+i+' .plotly-graph-div').forEach(p=>Plotly.Plots.resize(p));}}</script></body></html>"""
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("Dashboard saved ->", os.path.abspath(out_path))
    if open_browser:
        webbrowser.open("file://" + os.path.abspath(out_path))
