"""
FinSight AI — Corporate Travel Analytics Platform
Run with:  streamlit run app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import re
from pathlib import Path

# ----------------------------------------------------------------------
# PAGE CONFIG + THEME
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="FinSight AI — Travel Analytics",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRIMARY = "#5B5FEF"
ACCENT = "#22D3B7"
DARK = "#12141F"
CARD_BG = "#1B1E2E"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

    .stApp {{
        background: radial-gradient(1200px 600px at 10% -10%, #23264a 0%, #0f1120 45%, #0b0c17 100%);
        color: #EAEAF5;
    }}
    section[data-testid="stSidebar"] {{
        background: #10101c;
        border-right: 1px solid rgba(255,255,255,0.06);
    }}
    h1, h2, h3 {{ color: #F5F6FF !important; letter-spacing: -0.02em; }}

    .hero {{
        padding: 28px 34px; border-radius: 20px; margin-bottom: 18px;
        background: linear-gradient(120deg, rgba(91,95,239,0.28), rgba(34,211,183,0.14));
        border: 1px solid rgba(255,255,255,0.08);
    }}
    .hero h1 {{ margin: 0 0 6px 0; font-size: 2rem; font-weight: 800; }}
    .hero p {{ margin: 0; color: #B7BAD6; font-size: 0.98rem; }}

    div[data-testid="stMetric"] {{
        background: {CARD_BG};
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 14px 16px 8px 16px;
        box-shadow: 0 4px 18px rgba(0,0,0,0.25);
    }}
    div[data-testid="stMetricLabel"] {{ color: #9EA2C7 !important; font-weight: 600; }}
    div[data-testid="stMetricValue"] {{ color: #FFFFFF !important; }}

    .card {{
        background: {CARD_BG}; border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px; padding: 18px 20px; margin-bottom: 14px;
        box-shadow: 0 4px 18px rgba(0,0,0,0.22);
    }}
    .pill {{
        display:inline-block; padding:3px 10px; border-radius:999px;
        background: rgba(34,211,183,0.15); color:{ACCENT}; font-size:0.75rem; font-weight:700;
        margin-right:6px;
    }}
    .chat-bubble-user {{
        background: linear-gradient(120deg, #5B5FEF, #7A7EF7); color:white;
        padding:10px 14px; border-radius:14px 14px 2px 14px; margin:6px 0; max-width:80%;
        margin-left:auto; font-size:0.92rem;
    }}
    .chat-bubble-bot {{
        background:{CARD_BG}; border:1px solid rgba(255,255,255,0.08); color:#EAEAF5;
        padding:12px 16px; border-radius:14px 14px 14px 2px; margin:6px 0; max-width:88%;
        font-size:0.92rem; line-height:1.5;
    }}
    .stButton>button {{
        background: linear-gradient(120deg, #5B5FEF, #4749c9); color:white; border:none;
        border-radius:10px; font-weight:600; padding:0.5rem 1rem;
    }}
    .stButton>button:hover {{ background: linear-gradient(120deg,#6d70f5,#5b5fef); }}
    footer {{visibility:hidden;}}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# DATA LOADING
# ----------------------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent / "data"

@st.cache_data
def load_data():
    hotels = pd.read_csv(BASE / "fused" / "fused_hotels_weather_employee.csv")
    flights = pd.read_csv(BASE / "fused" / "fused_flights_weather_employee.csv")
    weather = pd.read_csv(BASE / "api" / "weather_climate_api.csv")
    users = pd.read_csv(BASE / "original" / "users.csv")
    with open(BASE / "fused" / "quality_report.json") as f:
        quality = json.load(f)
    with open(BASE / "fused" / "fusion_validation.json") as f:
        validation = json.load(f)
    with open(BASE / "fused" / "eda_insights.json") as f:
        insights = json.load(f)
    return hotels, flights, weather, users, quality, validation, insights

hotels, flights, weather, users, quality, validation, insights = load_data()

# ----------------------------------------------------------------------
# ANALYTICS ASSISTANT ENGINE  (deterministic, pandas-backed — no vague answers)
# ----------------------------------------------------------------------
def top_employee_by_trips():
    t = flights.groupby(["userCode","employee_name","company"])["travelCode"].nunique() \
        .reset_index(name="num_trips").sort_values("num_trips", ascending=False)
    return t

def top_employee_by_spend():
    f_spend = flights.groupby(["userCode","employee_name","company"])["price"].sum().reset_index(name="flight_spend")
    h_spend = hotels.groupby(["userCode","employee_name","company"])["total"].sum().reset_index(name="hotel_spend")
    merged = f_spend.merge(h_spend, on=["userCode","employee_name","company"], how="outer").fillna(0)
    merged["total_spend"] = merged["flight_spend"] + merged["hotel_spend"]
    return merged.sort_values("total_spend", ascending=False)

def company_spend_table():
    f = flights.groupby("company")["price"].sum().rename("flight_spend")
    h = hotels.groupby("company")["total"].sum().rename("hotel_spend")
    tbl = pd.concat([f, h], axis=1).fillna(0)
    tbl["total_spend"] = tbl["flight_spend"] + tbl["hotel_spend"]
    return tbl.sort_values("total_spend", ascending=False)

def city_table():
    return hotels.groupby("city_key").agg(
        avg_price=("price","mean"), avg_days=("days","mean"),
        avg_temp_c=("avg_temp_c","mean"), n_bookings=("travelCode","count")
    ).round(2).sort_values("n_bookings", ascending=False)

INTENTS = [
    (["travel most", "most trips", "most flights", "frequent traveler", "frequent flyer",
      "travels the most", "travel the most", "travelled the most", "traveled the most"],
     "employee_trips"),
    (["spend most", "highest spend", "most expensive employee", "top spender", "cost the most",
      "spends the most", "spend the most"],
     "employee_spend"),
    (["most visited", "popular city", "most bookings", "top city", "most travelled city", "most traveled city"],
     "top_city"),
    (["expensive city", "expensive hotel", "priciest"],
     "expensive_city"),
    (["cheapest city", "cheapest hotel", "lowest price"],
     "cheapest_city"),
    (["agency", "airline used most", "most used agency"],
     "top_agency"),
    (["company spend", "which company", "spends the most", "biggest spender company"],
     "company_spend"),
    (["temperature", "weather", "climate", "hot", "cold"],
     "weather_insight"),
    (["correlation", "relationship between"],
     "correlation"),
    (["flight type", "economic", "premium", "first class", "firstclass"],
     "flight_type"),
    (["outlier", "data error", "anomaly"],
     "outliers"),
    (["missing", "null", "nan"],
     "missing_data"),
]

def match_intent(q):
    ql = q.lower()
    for keywords, intent in INTENTS:
        if any(k in ql for k in keywords):
            return intent
    return None

def answer(question):
    intent = match_intent(question)

    if intent == "employee_trips":
        t = top_employee_by_trips()
        top = t.iloc[0]
        text = (f"**{top['employee_name']}** ({top['company']}) travels the most, with "
                f"**{int(top['num_trips'])} trips** recorded in the fused flight data.")
        return text, t.head(10)

    if intent == "employee_spend":
        t = top_employee_by_spend()
        top = t.iloc[0]
        text = (f"**{top['employee_name']}** ({top['company']}) has the highest total travel spend: "
                f"**R$ {top['total_spend']:,.2f}** (flights: R$ {top['flight_spend']:,.2f} + "
                f"hotels: R$ {top['hotel_spend']:,.2f}).")
        return text, t.head(10)[["employee_name","company","flight_spend","hotel_spend","total_spend"]]

    if intent == "top_city":
        c = city_table()
        top = c.iloc[0]
        text = f"**{c.index[0]}** is the most visited destination, with **{int(top['n_bookings'])} hotel bookings** (avg price R$ {top['avg_price']:.2f}/night)."
        return text, c

    if intent == "expensive_city":
        c = city_table().sort_values("avg_price", ascending=False)
        top = c.iloc[0]
        text = f"**{c.index[0]}** has the highest average hotel price: **R$ {top['avg_price']:.2f}/night**."
        return text, c

    if intent == "cheapest_city":
        c = city_table().sort_values("avg_price", ascending=True)
        top = c.iloc[0]
        text = f"**{c.index[0]}** has the lowest average hotel price: **R$ {top['avg_price']:.2f}/night**."
        return text, c

    if intent == "top_agency":
        vc = flights["agency"].value_counts()
        text = f"**{vc.index[0]}** is the most used travel agency, booked **{int(vc.iloc[0])} times** ({vc.iloc[0]/vc.sum()*100:.1f}% of all flights)."
        return text, vc.rename("flights_booked").to_frame()

    if intent == "company_spend":
        t = company_spend_table()
        top = t.iloc[0]
        text = f"**{t.index[0]}** has the highest total travel spend: **R$ {top['total_spend']:,.2f}** across flights and hotels."
        return text, t

    if intent == "weather_insight":
        corr_p = insights["correlation_temp_vs_price"]
        corr_d = insights["correlation_temp_vs_days"]
        text = (f"Destination temperature has a **weak correlation of {corr_p:+.3f}** with hotel price and "
                f"**{corr_d:+.3f}** with length of stay. In short: warmer cities are *not* significantly "
                f"more or less expensive, and employees don't stay longer in warmer destinations — trip "
                f"length is driven by business need, not climate.")
        return text, weather

    if intent == "correlation":
        num_cols = ["price","total","days","avg_temp_c","total_precip_mm","avg_humidity_pct"]
        corr = hotels[num_cols].corr().round(3)
        text = "Correlation matrix across price, stay length, and the API-sourced climate variables:"
        return text, corr

    if intent == "flight_type":
        t = flights.groupby("flightType")["price"].agg(["mean","count"]).round(2).sort_values("mean", ascending=False)
        top = t.iloc[0]
        text = f"**{t.index[0]}** is the most expensive flight type on average, at **R$ {top['mean']:.2f}** per ticket ({int(top['count'])} tickets)."
        return text, t

    if intent == "outliers":
        low, high = quality["price_outliers"]["lower_bound"], quality["price_outliers"]["upper_bound"]
        n = quality["price_outliers"]["count"]
        text = (f"IQR outlier detection on hotel price found **{n} outliers** outside the range "
                f"[{low:.2f}, {high:.2f}]. These look like genuine data-entry errors (e.g. a negative price, "
                f"and one price ~20x the typical rate for that city) rather than valid premium bookings.")
        return text, pd.DataFrame(quality["price_outliers"]["example_rows"])

    if intent == "missing_data":
        rows = [(k, v["count"], v["pct"]) for k, v in quality["missing_values"].items()]
        df = pd.DataFrame(rows, columns=["column","missing_count","missing_pct"]).sort_values("missing_pct", ascending=False)
        text = f"**{quality['attribute_with_max_missing']}** has the most missing values. Full breakdown below:"
        return text, df

    # fallback — not a vague non-answer, but a helpful menu of what CAN be asked
    return (
        "I can only answer from the actual fused dataset (no guessing). Try one of these — "
        "or click a suggested question in the sidebar:\n\n"
        "- Which employee travels the most?\n- Which employee spends the most?\n"
        "- What is the most visited city?\n- Which city has the most expensive hotels?\n"
        "- Which agency is used the most?\n- Which company spends the most on travel?\n"
        "- How does temperature relate to hotel price?\n- Which flight type is most expensive?\n"
        "- What outliers were found in the data?\n- Which columns have missing data?"
    ), None

SUGGESTED_QUESTIONS = [
    "Which employee travels the most?",
    "Which employee spends the most?",
    "What is the most visited city?",
    "Which city has the most expensive hotels?",
    "Which agency is used the most?",
    "Which company spends the most on travel?",
    "How does temperature relate to hotel price?",
    "Which flight type is most expensive?",
    "What outliers were found in the data?",
    "Which columns have missing data?",
]


# ----------------------------------------------------------------------
# PREMIUM UI + SHARED FILTERS
# ----------------------------------------------------------------------
CHART_TEMPLATE = "plotly_dark"
CHART_LAYOUT = dict(
    template=CHART_TEMPLATE, paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter", color="#DCE3F5"),
    margin=dict(l=18, r=18, t=55, b=18), height=360,
    hoverlabel=dict(bgcolor="#171D30", font_size=12),
    legend=dict(orientation="h", y=-0.22),
)
PALETTE = ["#7C83FF", "#31D6B4", "#F6BD60", "#F28482", "#82Aaff", "#C792EA", "#56CFE1"]

def polish(fig, height=360):
    fig.update_layout(**{**CHART_LAYOUT, "height": height})
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor="rgba(255,255,255,.08)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,.07)", zeroline=False)
    return fig

def money(value):
    return f"R$ {value:,.0f}"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@500;600;700;800&display=swap');
:root { --ink:#e9edfa; --muted:#98a5c4; --panel:#151d30; --line:rgba(157,174,211,.13); }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background:radial-gradient(ellipse at 12% 0%,#202c50 0%,#0b1120 48%,#080d18 100%); color:var(--ink); }
[data-testid="stHeader"] { background:rgba(8,13,24,.7); }
section[data-testid="stSidebar"] { background:linear-gradient(180deg,#101a2d,#0b1220); border-right:1px solid var(--line); }
section[data-testid="stSidebar"] .block-container { padding-top:1.8rem; }
h1,h2,h3 { font-family:'Manrope',sans-serif !important; letter-spacing:-.035em; color:#f4f6ff !important; }
h1 { font-size:2.15rem !important; font-weight:800 !important; }
h2 { font-size:1.55rem !important; font-weight:750 !important; }
h3 { font-size:1.12rem !important; font-weight:700 !important; }
p, label, .stCaption { color:#aebbd4; }
.hero { padding:30px 34px; border:1px solid rgba(139,155,255,.24); border-radius:24px; margin:4px 0 22px;
background:linear-gradient(115deg,rgba(85,99,220,.28),rgba(28,191,169,.13)),linear-gradient(135deg,#17233c,#111a2c);
box-shadow:0 18px 55px rgba(0,0,0,.18); position:relative; overflow:hidden; }
.hero:after { content:'✈'; position:absolute; right:5%; top:4px; font-size:100px; opacity:.08; transform:rotate(-14deg); }
.hero h1 { margin:8px 0 5px; font-size:2rem !important; }
.hero p { margin:0; color:#b8c5df; max-width:820px; }
.eyebrow { color:#5fe0c4; text-transform:uppercase; letter-spacing:.16em; font-size:.72rem; font-weight:800; }
.pill { display:inline-block; padding:5px 11px; border-radius:30px; background:rgba(49,214,180,.12); color:#5fe0c4; font-size:.7rem; font-weight:800; margin-right:7px; border:1px solid rgba(49,214,180,.18); }
div[data-testid="stMetric"] { background:linear-gradient(145deg,rgba(27,40,65,.96),rgba(18,28,46,.96)); border:1px solid var(--line); border-radius:17px; padding:17px 18px 13px; box-shadow:0 10px 28px rgba(0,0,0,.14); min-height:112px; }
div[data-testid="stMetricLabel"] { color:#9eacc9 !important; font-size:.8rem; font-weight:600; }
div[data-testid="stMetricValue"] { color:#f4f7ff !important; font-family:'Manrope',sans-serif; font-weight:800; font-size:1.55rem; }
div[data-testid="stMetricDelta"] { font-size:.75rem; }
div[data-testid="stTabs"] button { color:#aebbd4; font-weight:650; }
div[data-testid="stTabs"] button[aria-selected="true"] { color:#67dfc6; }
div[data-testid="stPlotlyChart"], div[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:16px; overflow:hidden; background:rgba(17,27,45,.55); padding:5px; }
.stButton>button, .stDownloadButton>button { border:1px solid rgba(124,131,255,.35); border-radius:11px; color:#f5f6ff; background:linear-gradient(110deg,#555ed1,#3e9c9a); font-weight:700; }
.stButton>button:hover, .stDownloadButton>button:hover { border-color:#70e2cc; color:white; }
div[data-baseweb="select"]>div, .stDateInput input, .stTextInput input { background:#131e32; border-color:var(--line); border-radius:10px; }
hr { border-color:var(--line); }
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#9eacc9; }
div[data-testid="stChatMessage"] { background:rgba(21,31,51,.8); border:1px solid var(--line); border-radius:15px; }
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# parse dates once for interactive date filtering
hotels["date"] = pd.to_datetime(hotels["date"], errors="coerce")
flights["date"] = pd.to_datetime(flights["date"], errors="coerce")

st.sidebar.markdown("""
<div style="padding:8px 2px 18px">
<div style="font-size:1.55rem;font-weight:800;color:#f4f6ff;font-family:Manrope">✦ FinSight <span style="color:#65dec5">AI</span></div>
<div style="font-size:.76rem;color:#91a1c2;margin-top:3px">TRAVEL INTELLIGENCE PLATFORM</div>
</div>
""", unsafe_allow_html=True)
page = st.sidebar.radio("WORKSPACE", [
    "🏠 Overview", "📈 Analytics Studio", "🔎 Explore Data",
    "🌎 API & Fusion", "🧪 Data Quality", "💬 Ask FinSight",
])
st.sidebar.markdown("---")
companies = sorted(hotels["company"].dropna().unique())
sel_companies = st.sidebar.multiselect("COMPANIES", companies, default=companies)
date_min = min(hotels["date"].min(), flights["date"].min()).date()
date_max = max(hotels["date"].max(), flights["date"].max()).date()
date_range = st.sidebar.date_input("TRAVEL DATE RANGE", value=(date_min, date_max), min_value=date_min, max_value=date_max)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    start_date, end_date = pd.Timestamp(date_min), pd.Timestamp(date_max)
h = hotels[hotels["company"].isin(sel_companies) & hotels["date"].between(start_date, end_date)].copy()
fl = flights[flights["company"].isin(sel_companies) & flights["date"].between(start_date, end_date)].copy()
st.sidebar.markdown("---")
st.sidebar.caption("Connected datasets · Fused hotel + flight + climate records")
st.sidebar.caption(f"Showing {len(h):,} hotel rows and {len(fl):,} flight rows")

def hero(kicker, title, subtitle):
    st.markdown(f'<div class="hero"><div class="eyebrow">{kicker}</div><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)

def spend_by_month():
    f = fl.groupby(fl["date"].dt.to_period("M"))["price"].sum().rename("Flight spend")
    hotel = h.groupby(h["date"].dt.to_period("M"))["total"].sum().rename("Hotel spend")
    out = pd.concat([f, hotel], axis=1).fillna(0).reset_index()
    out["month"] = out["date"].astype(str)
    return out

def filtered_company_spend():
    f = fl.groupby("company")["price"].sum().rename("Flight spend")
    hotel = h.groupby("company")["total"].sum().rename("Hotel spend")
    return pd.concat([f, hotel], axis=1).fillna(0).assign(Total=lambda x: x.sum(axis=1)).sort_values("Total", ascending=False)

# ----------------------------------------------------------------------
# OVERVIEW
# ----------------------------------------------------------------------
if page == "🏠 Overview":
    hero("CORPORATE TRAVEL · EXECUTIVE OVERVIEW", "Your travel spend, in focus.",
         "A live command centre for corporate trips, employee activity, hotel bookings and destination climate.")
    if h.empty and fl.empty:
        st.warning("No records match the selected filters. Adjust the company or date range.")
    else:
        total_trips = pd.concat([h["travelCode"], fl["travelCode"]]).nunique()
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Unique trips", f"{total_trips:,}")
        c2.metric("Employees", f"{pd.concat([h['userCode'],fl['userCode']]).nunique():,}")
        c3.metric("Flight spend", money(fl["price"].sum()))
        c4.metric("Hotel spend", money(h["total"].sum()))
        c5.metric("Avg. destination temp", f"{h['avg_temp_c'].mean():.1f} °C" if h["avg_temp_c"].notna().any() else "N/A")
        st.markdown("### Spend performance")
        left,right = st.columns([1.55,1])
        with left:
            monthly = spend_by_month()
            if not monthly.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=monthly["month"],y=monthly["Flight spend"],name="Flights",mode="lines+markers",line=dict(color="#858bff",width=3),fill="tozeroy",fillcolor="rgba(133,139,255,.10)"))
                fig.add_trace(go.Scatter(x=monthly["month"],y=monthly["Hotel spend"],name="Hotels",mode="lines+markers",line=dict(color="#35d6b5",width=3),fill="tozeroy",fillcolor="rgba(53,214,181,.09)"))
                polish(fig,390); fig.update_layout(title="Monthly spend trend",hovermode="x unified")
                st.plotly_chart(fig,use_container_width=True)
        with right:
            comp = filtered_company_spend().reset_index()
            if not comp.empty:
                fig = px.bar(comp,x="company",y="Total",color="Total",text_auto=".2s",color_continuous_scale=["#31466c","#31d6b5"],labels={"Total":"Spend (BRL)"})
                polish(fig,390); fig.update_layout(title="Spend by company",coloraxis_showscale=False)
                st.plotly_chart(fig,use_container_width=True)
        st.markdown("### Travel mix")
        a,b,c = st.columns(3)
        with a:
            city = h["city_key"].value_counts().head(8).reset_index(); city.columns=["Destination","Bookings"]
            if not city.empty:
                fig=px.bar(city,x="Bookings",y="Destination",orientation="h",color="Bookings",color_continuous_scale="Teal")
                polish(fig,330); fig.update_layout(title="Top destinations",yaxis=dict(categoryorder="total ascending"),coloraxis_showscale=False)
                st.plotly_chart(fig,use_container_width=True)
        with b:
            ft=fl["flightType"].value_counts().reset_index(); ft.columns=["Flight type","Bookings"]
            if not ft.empty:
                fig=px.pie(ft,names="Flight type",values="Bookings",hole=.66,color_discrete_sequence=PALETTE)
                polish(fig,330); fig.update_layout(title="Flight class mix")
                st.plotly_chart(fig,use_container_width=True)
        with c:
            agency=fl["agency"].value_counts().head(7).reset_index(); agency.columns=["Agency","Bookings"]
            if not agency.empty:
                fig=px.bar(agency,x="Agency",y="Bookings",color="Bookings",color_continuous_scale="Teal")
                polish(fig,330); fig.update_layout(title="Top travel agencies",coloraxis_showscale=False)
                st.plotly_chart(fig,use_container_width=True)
        st.markdown("### Top employees")
        top=fl.groupby(["employee_name","company"])["travelCode"].nunique().reset_index(name="Trips").sort_values("Trips",ascending=False).head(8)
        if not top.empty:
            fig=px.bar(top,x="Trips",y="employee_name",color="company",orientation="h",barmode="group",color_discrete_sequence=PALETTE)
            polish(fig,350); fig.update_layout(title="Most frequent travellers",yaxis=dict(categoryorder="total ascending"),legend_title="Company")
            st.plotly_chart(fig,use_container_width=True)

# ----------------------------------------------------------------------
# ANALYTICS STUDIO — INTERACTIVE VISUAL EXPLORATION
# ----------------------------------------------------------------------
elif page == "📈 Analytics Studio":
    hero("INTERACTIVE EXPLORATION", "Analytics Studio", "Explore spend patterns, booking behaviour and climate relationships with interactive visual controls.")
    tab1,tab2,tab3,tab4 = st.tabs(["Spend & trends","Travel behaviour","People & destinations","Climate & relationships"])
    with tab1:
        st.markdown("### Spend analysis")
        metric_col, group_col = st.columns(2)
        with metric_col: spend_metric=st.selectbox("Spend metric",["Hotel total","Hotel nightly price","Flight price"],key="spend_metric")
        source = h if spend_metric != "Flight price" else fl
        breakdown_options = ["Company","Destination","Month","Climate zone"] if source is h else ["Company","Destination","Month","Flight type","Agency"]
        with group_col: breakdown=st.selectbox("Break down by",breakdown_options,key="spend_group")
        value_col = {"Hotel total":"total","Hotel nightly price":"price","Flight price":"price"}[spend_metric]
        group_map={"Company":"company","Destination":"city_key" if source is h else "dest_city_key","Month":"date","Climate zone":"climate_zone","Flight type":"flightType","Agency":"agency"}
        group_key=group_map[breakdown]
        temp=source.copy()
        if breakdown=="Month": temp["Month"]=temp["date"].dt.to_period("M").astype(str); group_key="Month"
        if group_key in temp.columns and value_col in temp.columns:
            agg=temp.groupby(group_key)[value_col].sum().reset_index(name="Spend").sort_values("Spend",ascending=False)
            if breakdown=="Month": agg=agg.sort_values(group_key)
            fig=px.bar(agg,x=group_key,y="Spend",color="Spend",color_continuous_scale=["#4a5b9c","#32d5b5"],text_auto=".2s")
            polish(fig,420); fig.update_layout(title=f"{spend_metric} by {breakdown.lower()}",coloraxis_showscale=False)
            st.plotly_chart(fig,use_container_width=True)
        monthly=spend_by_month()
        if not monthly.empty:
            fig=px.area(monthly,x="month",y=["Flight spend","Hotel spend"],color_discrete_sequence=["#858bff","#35d6b5"],title="Spend composition over time")
            polish(fig,370); fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig,use_container_width=True)
    with tab2:
        st.markdown("### Booking behaviour")
        x,y=st.columns(2)
        with x:
            if not fl.empty:
                ft=fl.groupby("flightType").agg(bookings=("travelCode","count"),avg_price=("price","mean")).reset_index()
                fig=px.bar(ft,x="flightType",y="bookings",color="avg_price",text_auto=True,color_continuous_scale="Teal",labels={"flightType":"Flight class","bookings":"Bookings"})
                polish(fig); fig.update_layout(title="Bookings by flight class",coloraxis_colorbar_title="Avg price")
                st.plotly_chart(fig,use_container_width=True)
        with y:
            if not fl.empty:
                fig=px.box(fl,x="flightType",y="price",color="flightType",points="outliers",color_discrete_sequence=PALETTE)
                polish(fig); fig.update_layout(title="Ticket price distribution",showlegend=False)
                st.plotly_chart(fig,use_container_width=True)
        if not fl.empty:
            agency=fl.groupby("agency").agg(bookings=("travelCode","count"),avg_price=("price","mean")).reset_index().sort_values("bookings",ascending=False)
            fig=px.scatter(agency,x="bookings",y="avg_price",size="bookings",color="agency",hover_name="agency",color_discrete_sequence=PALETTE)
            polish(fig,390); fig.update_layout(title="Agency volume vs average ticket price",showlegend=False)
            st.plotly_chart(fig,use_container_width=True)
    with tab3:
        st.markdown("### Employee and destination insights")
        c1,c2=st.columns(2)
        with c1:
            top=fl.groupby("employee_name").agg(trips=("travelCode","nunique"),spend=("price","sum")).reset_index().nlargest(12,"trips")
            if not top.empty:
                fig=px.bar(top.sort_values("trips"),x="trips",y="employee_name",orientation="h",color="spend",color_continuous_scale="Teal",hover_data=["spend"])
                polish(fig,420); fig.update_layout(title="Employee trip leaderboard",coloraxis_colorbar_title="Flight spend")
                st.plotly_chart(fig,use_container_width=True)
        with c2:
            city=h.groupby("city_key").agg(bookings=("travelCode","count"),hotel_spend=("total","sum")).reset_index().nlargest(12,"bookings")
            if not city.empty:
                fig=px.treemap(city,path=["city_key"],values="bookings",color="hotel_spend",color_continuous_scale="Teal")
                polish(fig,420); fig.update_layout(title="Destination booking treemap")
                st.plotly_chart(fig,use_container_width=True)
    with tab4:
        st.markdown("### Climate relationships")
        climate=h.dropna(subset=["avg_temp_c","price"])
        if not climate.empty:
            c1,c2=st.columns(2)
            with c1:
                city=climate.groupby("city_key").agg(avg_temp=("avg_temp_c","mean"),avg_price=("price","mean"),bookings=("travelCode","count")).reset_index()
                fig=px.scatter(city,x="avg_temp",y="avg_price",size="bookings",color="city_key",hover_name="city_key",color_discrete_sequence=PALETTE)
                polish(fig); fig.update_layout(title="Destination temperature vs hotel price",showlegend=False,xaxis_title="Average temperature (°C)",yaxis_title="Average nightly price (BRL)")
                st.plotly_chart(fig,use_container_width=True)
            with c2:
                cols=["price","total","days","avg_temp_c","total_precip_mm","avg_humidity_pct"]
                corr=h[cols].corr()
                fig=px.imshow(corr,text_auto=".2f",zmin=-1,zmax=1,color_continuous_scale="RdBu_r")
                polish(fig); fig.update_layout(title="Travel & climate correlation")
                st.plotly_chart(fig,use_container_width=True)
        else: st.info("Climate fields are not available for the current filter selection.")

# ----------------------------------------------------------------------
# EXPLORE DATA
# ----------------------------------------------------------------------
elif page == "🔎 Explore Data":
    hero("DATA EXPLORER","Explore your datasets","Inspect filtered fused records and export the data behind your dashboard.")
    tab1,tab2,tab3=st.tabs(["🏨 Hotels","🛫 Flights","👤 Users"])
    with tab1:
        st.caption(f"{len(h):,} hotel records · {h.shape[1]} fields")
        st.dataframe(h,use_container_width=True,height=430)
        st.download_button("⬇ Download filtered hotel CSV",h.to_csv(index=False),"finsight_hotels_filtered.csv","text/csv")
    with tab2:
        st.caption(f"{len(fl):,} flight records · {fl.shape[1]} fields")
        st.dataframe(fl,use_container_width=True,height=430)
        st.download_button("⬇ Download filtered flight CSV",fl.to_csv(index=False),"finsight_flights_filtered.csv","text/csv")
    with tab3:
        st.dataframe(users,use_container_width=True,height=430)

# ----------------------------------------------------------------------
# API & FUSION
# ----------------------------------------------------------------------
elif page == "🌎 API & Fusion":
    hero("DATA ENGINEERING","API & data fusion","Understand how external climate data enriches internal corporate travel records.")
    a,b,c,d=st.columns(4)
    a.metric("API provider","Open-Meteo"); b.metric("Request method","GET"); c.metric("Authentication","None"); d.metric("Fusion strategy","Left + inner join")
    st.markdown("### Enrichment pipeline")
    st.markdown('<div class="card"><span class="pill">01 · SOURCE</span> Internal hotel, flight and employee records &nbsp; → &nbsp; <span class="pill">02 · ENRICH</span> Open-Meteo historical climate &nbsp; → &nbsp; <span class="pill">03 · FUSE</span> City-based join &nbsp; → &nbsp; <span class="pill">04 · ANALYSE</span> Unified travel intelligence</div>',unsafe_allow_html=True)
    x,y=st.columns([1,1])
    with x:
        st.markdown("### Climate API dataset"); st.dataframe(weather,use_container_width=True,height=360)
    with y:
        st.markdown("### Fusion validation"); st.json(validation)
    orig=pd.read_csv(BASE/"original"/"hotels.csv")
    comp_df=pd.DataFrame({"Original hotels":[len(orig),orig.shape[1],orig["travelCode"].nunique(),int(orig.isna().sum().sum()),int(orig.duplicated().sum())],"Weather API":[len(weather),weather.shape[1],weather["city"].nunique(),int(weather.isna().sum().sum()),int(weather.duplicated().sum())],"Fused hotels":[len(hotels),hotels.shape[1],hotels["travelCode"].nunique(),int(hotels.isna().sum().sum()),int(hotels.duplicated().sum())]},index=["Records","Attributes","Unique IDs","Missing values","Duplicates"])
    st.markdown("### Dataset comparison"); st.dataframe(comp_df,use_container_width=True)

# ----------------------------------------------------------------------
# DATA QUALITY
# ----------------------------------------------------------------------
elif page == "🧪 Data Quality":
    hero("TRUST & RELIABILITY","Data quality centre","Review missing values, duplicates and statistical outliers in the fused travel dataset.")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Dataset dimensions",f"{quality['dimensions']['rows']:,} × {quality['dimensions']['columns']}")
    c2.metric("Duplicate records",f"{quality['duplicate_records']:,}")
    c3.metric("Price outliers",f"{quality['price_outliers']['count']:,}")
    c4.metric("Most missing field",quality["attribute_with_max_missing"])
    miss_df=pd.DataFrame([{"Column":k,**v} for k,v in quality["missing_values"].items()]).sort_values("pct",ascending=False)
    left,right=st.columns([1.25,1])
    with left:
        fig=px.bar(miss_df.head(18),x="pct",y="Column",orientation="h",color="pct",color_continuous_scale="Sunset")
        polish(fig,480); fig.update_layout(title="Missing values by attribute (%)",yaxis=dict(categoryorder="total ascending"),coloraxis_showscale=False)
        st.plotly_chart(fig,use_container_width=True)
    with right:
        fig=px.pie(miss_df[miss_df["count"]>0],names="Column",values="count",hole=.58,color_discrete_sequence=PALETTE)
        polish(fig,480); fig.update_layout(title="Share of missing values")
        st.plotly_chart(fig,use_container_width=True)
    st.markdown("### Hotel price outlier analysis")
    st.write(f"IQR bounds: **{quality['price_outliers']['lower_bound']:.2f} – {quality['price_outliers']['upper_bound']:.2f}** · **{quality['price_outliers']['count']:,} outliers** detected.")
    l,r=st.columns([1.2,1])
    with l:
        fig=px.box(hotels,y="price",points="outliers",color_discrete_sequence=["#858bff"])
        polish(fig,350); fig.update_layout(title="Hotel nightly price distribution")
        st.plotly_chart(fig,use_container_width=True)
    with r:
        st.markdown("#### Example outlier records")
        st.dataframe(pd.DataFrame(quality["price_outliers"]["example_rows"]),use_container_width=True,height=350)
    with st.expander("View full missing-value table"):
        st.dataframe(miss_df,use_container_width=True,hide_index=True)

# ----------------------------------------------------------------------
# ASK FINSIGHT
# ----------------------------------------------------------------------
elif page == "💬 Ask FinSight":
    hero("CONVERSATIONAL ANALYTICS","Ask FinSight","Ask questions about travel spend, employees, destinations, climate and data quality.")
    st.caption("Answers are computed from the project's fused datasets.")
    if "chat_history" not in st.session_state: st.session_state.chat_history=[]
    with st.expander("Suggested questions",expanded=True):
        cols=st.columns(2)
        for i,q in enumerate(SUGGESTED_QUESTIONS):
            if cols[i%2].button(q,key=f"ask_{i}",use_container_width=True):
                st.session_state.chat_history.append(("user",q))
                response,df=answer(q); st.session_state.chat_history.append(("bot",response,df))
    user_q=st.chat_input("Ask about employees, trips, spend, cities, weather…")
    if user_q:
        st.session_state.chat_history.append(("user",user_q))
        response,df=answer(user_q); st.session_state.chat_history.append(("bot",response,df))
    for entry in st.session_state.chat_history:
        if entry[0]=="user":
            with st.chat_message("user"): st.markdown(entry[1])
        else:
            with st.chat_message("assistant"):
                st.markdown(entry[1])
                if entry[2] is not None: st.dataframe(entry[2],use_container_width=True)
    if st.session_state.chat_history and st.button("Clear conversation"):
        st.session_state.chat_history=[]; st.rerun()
