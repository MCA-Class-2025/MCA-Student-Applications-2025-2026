"""PDF report (ReportLab) - content comes from the filtered data and computed insights only."""
import io
from datetime import date
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from config.settings import NOT_RECORDED, APP_TITLE
from modules import calculations as calc

CHARTS = {
    "Sampling locations (lon/lat)": "locations",
    "Samples by ocean": "ocean",
    "Top countries": "country",
    "Records per year": "year",
    "Measurement histogram": "hist",
}


def _clean(t):
    return escape(str(t)).encode("latin-1", "replace").decode("latin-1")


def _png(fig):
    b = io.BytesIO()
    fig.savefig(b, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    b.seek(0)
    return b


def make_chart(kind, df, th, unit):
    pal = th["palette"]
    fig, ax = plt.subplots(figsize=(7, 3.4))
    if kind == "locations":
        ax.scatter(df.lon, df.lat, s=2, color=pal[0], alpha=.5)
        ax.set_xlim(-180, 180); ax.set_ylim(-90, 90); ax.grid(alpha=.3)
        ax.set_xlabel("Longitude (°)"); ax.set_ylabel("Latitude (°)")
        ax.set_title("Sampling locations (coordinate plot, no basemap)")
    elif kind == "ocean":
        c = df.loc[df.ocean != NOT_RECORDED, "ocean"].value_counts()
        ax.barh(c.index[::-1], c.values[::-1], color=pal[1]); ax.set_title("Records by ocean"); ax.set_xlabel("Records")
    elif kind == "country":
        c = df.loc[df.country != NOT_RECORDED, "country"].value_counts().head(12)
        ax.barh(c.index[::-1], c.values[::-1], color=pal[2]); ax.set_title("Top countries by record count"); ax.set_xlabel("Records")
    elif kind == "year":
        c = df.year.value_counts().sort_index()
        ax.bar(c.index, c.values, color=pal[3]); ax.set_title("Records per year"); ax.set_xlabel("Year")
    elif kind == "hist":
        d = calc.unit_subset(df, unit)
        v = d.log_value.dropna()
        if len(v) < 5:
            plt.close(fig); return None
        ax.hist(v, bins=40, color=pal[4]); ax.set_title(f"Distribution of log10({unit})"); ax.set_xlabel(f"log10({unit})")
    if df.empty:
        plt.close(fig); return None
    fig.tight_layout()
    return _png(fig)


def build_pdf(df, kpi, insights, quality, filt_text, th, charts, unit, spatial_note=""):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                            title="NOAA Marine Microplastics - Spatial Analytics Report")
    ss = getSampleStyleSheet()
    prim = colors.HexColor(th["primary"])
    H1 = ParagraphStyle("H1", parent=ss["Title"], textColor=prim, fontSize=22)
    H2 = ParagraphStyle("H2", parent=ss["Heading2"], textColor=prim, spaceBefore=10)
    B = ParagraphStyle("B", parent=ss["BodyText"], fontSize=9.5, leading=13)
    S = ParagraphStyle("S", parent=B, fontSize=8, textColor=colors.grey)
    el = [Paragraph(_clean(APP_TITLE.title()), H1), Paragraph("Spatial Intelligence & Analytics - Report", ss["Heading3"]),
          Paragraph(f"Generated: {date.today():%d %B %Y}", B), Spacer(1, 6),
          Paragraph("<b>Dataset.</b> NOAA National Centers for Environmental Information (NCEI) Marine Microplastics database "
                    "(point observations from published studies and citizen-science programmes). The original CSV is unchanged; analysis uses a cleaned copy.", B),
          Paragraph(_clean(f"<b>Filters applied:</b> {filt_text}").replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>"), B), Spacer(1, 8)]
    t = Table([["Microplastic samples", "Countries surveyed", "Oceans covered", "Highest sampling coverage"],
               [f"{kpi['samples']:,}", f"{kpi['countries']}", f"{kpi['oceans']}", _clean(f"{kpi['top_ocean']} ({kpi['top_ocean_pct']}%)")]],
              colWidths=[4.2 * cm] * 4)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), prim), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                           ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("FONTSIZE", (0, 1), (-1, 1), 11), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                           ("GRID", (0, 0), (-1, -1), .5, colors.lightgrey), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    el += [t, Spacer(1, 10)]
    for sec, items in insights.items():
        el.append(Paragraph(_clean(sec), H2))
        for s in items:
            el.append(Paragraph("• " + _clean(s), B))
        if sec == "Geographic Findings":
            for kind in charts:
                img = make_chart(kind, df, th, unit)
                if img:
                    el += [Spacer(1, 4), Image(img, width=15 * cm, height=7.3 * cm)]
    el += [PageBreak(), Paragraph("Data limitations", H2)]
    for s in ["Observations come from many studies using different methods, mesh sizes, depths and eras; values are not strictly comparable across studies.",
              "Measurements in different units (pieces/m3, pieces kg-1 d.w., pieces/10 mins) are never combined.",
              "Sampling effort is uneven worldwide; record counts reflect where researchers sampled, not where plastic is most abundant.",
              "Hotspot and cluster statistics describe the sampled locations only and are sensitive to grid size and neighbourhood definition.",
              spatial_note]:
        if s:
            el.append(Paragraph("• " + _clean(s), B))
    el.append(Spacer(1, 10))
    el.append(Paragraph("Report generated automatically from the filtered dataset; no values were imputed.", S))
    doc.build(el)
    return buf.getvalue()
