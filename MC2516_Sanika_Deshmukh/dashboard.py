"""
dashboard.py — PlatePal: an interactive data-storytelling dashboard
────────────────────────────────────────────────────────────────────
Reads the fused dataset (original LLM/nutrition data + API-derived weather,
recipe and price data, joined on dish_name) and walks the reader through it
as a short story in six chapters:

    1. Where we started      — the nutrition landscape (original data)
    2. What the APIs added   — new attributes and how complete they are
    3. Weather and food      — does context change what suits a dish?
    4. Healthy vs. expensive — price against health
    5. What drives health    — original variables vs API variables
    6. Put it together       — a dish finder that needs BOTH data sources

Every sentence of narration is computed from the data currently selected in
the sidebar, so the story updates as the reader filters.

Run:
    pip install streamlit pandas numpy plotly
    streamlit run src/dashboard.py
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="PlatePal — Data Story", page_icon="🍽️", layout="wide")

# ─────────────────────────────────────────────────────────────────────────
# Look & feel
# ─────────────────────────────────────────────────────────────────────────
GREEN, ORANGE, GOLD, GREY = "#2F5233", "#B0562A", "#D4A017", "#6B6B6B"
SOURCE_COLORS = {"Original (LLM)": GREEN, "API-derived": ORANGE}
CATEGORY_COLORS = px.colors.qualitative.Safe

st.markdown(
    f"""
    <style>
      .kicker {{ color:{ORANGE}; font-weight:700; letter-spacing:.08em; font-size:.78rem; margin-top:2.2rem; }}
      .hero-title {{ font-size:2.6rem; font-weight:800; color:{GREEN}; line-height:1.1; margin-bottom:.2rem; }}
      .hero-sub {{ font-size:1.1rem; color:{GREY}; margin-bottom:1rem; }}
      .story {{ font-size:1.05rem; line-height:1.6; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────
# Lookups
# ─────────────────────────────────────────────────────────────────────────
METRICS = {
    "Calories (kcal)": ("calories_kcal", "kcal"),
    "Protein (g)": ("protein_g", "g"),
    "Carbs (g)": ("carbs_g", "g"),
    "Fat (g)": ("fat_g", "g"),
    "Sugar (g)": ("sugar_g", "g"),
    "Fiber (g)": ("fiber_g", "g"),
    "Sodium (mg)": ("sodium_mg", "mg"),
    "Health score (0–100)": ("health_score", "pts"),
}
GROUPS = {
    "Cuisine region": "cuisine_region",
    "Dish category": "category",
    "Meal type": "meal_type",
    "Nutri-Score grade": "nutriscore_grade",
}
CURRENCIES = {"INR (₹)": ("cost_inr", "₹"), "USD ($)": ("cost_usd", "$"), "EUR (€)": ("cost_eur", "€")}
TEMP_BANDS = ["Cold (<15°C)", "Mild (15–32°C)", "Hot (>32°C)"]

# Which variables came from where — used to colour chapter 5 and describe chapter 2
DRIVER_SOURCE = {
    "calories_kcal": "Original (LLM)", "protein_g": "Original (LLM)", "carbs_g": "Original (LLM)",
    "fat_g": "Original (LLM)", "sugar_g": "Original (LLM)", "fiber_g": "Original (LLM)",
    "sodium_mg": "Original (LLM)", "cook_time_min": "Original (LLM)", "spice_level": "Original (LLM)",
    "weather_temp_c": "API-derived", "weather_suitability_score": "API-derived", "cost_inr": "API-derived",
}
NEW_ATTRIBUTES = pd.DataFrame(
    [
        ("recipe_category", "TheMealDB", "Recipe classification for the dish"),
        ("recipe_area", "TheMealDB", "Cuisine area of the matched recipe"),
        ("weather_city", "OpenWeatherMap", "City the weather was read for"),
        ("weather_country", "OpenWeatherMap", "Country code of that city"),
        ("weather_temp_c", "OpenWeatherMap", "Temperature at lookup time (°C)"),
        ("weather_condition", "OpenWeatherMap", "Sky condition at lookup time"),
        ("weather_suitability_score", "Derived (dish × weather)", "0–1 score: how well the dish suits the weather"),
        ("cost_inr", "ExchangeRate API", "Estimated base price in rupees"),
        ("cost_usd", "ExchangeRate API", "Same price converted to US dollars"),
        ("cost_eur", "ExchangeRate API", "Same price converted to euros"),
    ],
    columns=["Attribute", "Source", "What it tells you"],
)


# ─────────────────────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────────────────────
def find_csv():
    here = Path(__file__).resolve().parent
    env = os.environ.get("PLATEPAL_FUSED_CSV")
    candidates = ([Path(env)] if env else []) + [
        here / ".." / "data" / "fused_dataset.csv",
        here / "data" / "fused_dataset.csv",
        Path("data/fused_dataset.csv"),
        here / "fused_dataset.csv",
        Path("fused_dataset.csv"),
        Path("phase1_C_fused_dataset.csv"),
        here / "phase1_C_fused_dataset.csv",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


@st.cache_data(show_spinner=False)
def load_data(source):
    raw = pd.read_csv(source)
    df = raw.drop_duplicates().reset_index(drop=True)  # the 25 duplicate API keys from the join
    df["has_api"] = df["weather_temp_c"].notna()
    df["temp_band"] = pd.cut(
        df["weather_temp_c"], bins=[-np.inf, 15, 32, np.inf], labels=TEMP_BANDS
    ).astype("object")
    return df, {"raw_rows": len(raw), "dupes_removed": len(raw) - len(df)}


def apply_filters(df, regions, cats, diet, grades, kcal_range, api_only):
    m = (
        df["cuisine_region"].isin(regions)
        & df["category"].isin(cats)
        & df["nutriscore_grade"].isin(grades)
        & df["calories_kcal"].between(kcal_range[0], kcal_range[1])
    )
    if diet == "Vegetarian only":
        m &= df["is_vegetarian"]
    elif diet == "Non-vegetarian only":
        m &= ~df["is_vegetarian"]
    if api_only:
        m &= df["has_api"]
    return df[m]


# ─────────────────────────────────────────────────────────────────────────
# Small helpers
# ─────────────────────────────────────────────────────────────────────────
def show(fig):
    """st.plotly_chart across Streamlit versions (width= is newer than use_container_width=)."""
    try:
        st.plotly_chart(fig, width="stretch")
    except Exception:
        st.plotly_chart(fig, use_container_width=True)


def show_table(data, **kwargs):
    """st.dataframe across Streamlit versions."""
    try:
        st.dataframe(data, width="stretch", **kwargs)
    except Exception:
        st.dataframe(data, use_container_width=True, **kwargs)


def chapter(n, anchor, kicker, title):
    st.markdown(f'<div class="kicker">CHAPTER {n} OF 6 · {kicker.upper()}</div>', unsafe_allow_html=True)
    st.header(title, anchor=anchor)


def tidy(fig, height=380):
    fig.update_layout(
        template="plotly_white", height=height, margin=dict(l=10, r=10, t=40, b=10),
        font=dict(size=13), legend=dict(orientation="h", y=-0.2),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────
# Chapters
# ─────────────────────────────────────────────────────────────────────────
def chapter_1(df):
    chapter(1, "ch1", "Where we started", "What is actually on the plate?")
    st.markdown(
        '<div class="story">Before any API was involved, PlatePal\'s language model could tell you what a dish '
        "is and what it contains. Pick a nutrient and a way of grouping dishes to see how that picture "
        "looks across the menu.</div>",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    metric_label = c1.selectbox("Nutrient", list(METRICS), key="c1_metric")
    group_label = c2.radio("Group dishes by", list(GROUPS), horizontal=True, key="c1_group")
    metric, unit = METRICS[metric_label]
    group = GROUPS[group_label]

    order = df.groupby(group)[metric].median().sort_values(ascending=False).index.tolist()
    fig = px.box(
        df, x=group, y=metric, color=group, category_orders={group: order},
        color_discrete_sequence=CATEGORY_COLORS, points=False,
        labels={metric: metric_label, group: group_label},
    )
    fig.update_layout(showlegend=False)
    show(tidy(fig, 420))

    med = df.groupby(group)[metric].median().sort_values(ascending=False)
    if len(med) >= 2:
        spread = f" — a **{med.iloc[0] / med.iloc[-1]:.1f}×** gap" if med.iloc[-1] > 0 else ""
        st.info(
            f"**What this tells us:** across **{len(df):,}** dishes the typical (median) value is "
            f"**{df[metric].median():.1f} {unit}**. **{med.index[0]}** sits highest at **{med.iloc[0]:.1f}**, "
            f"**{med.index[-1]}** lowest at **{med.iloc[-1]:.1f}**{spread}."
        )
    else:
        st.info(f"Only one {group_label.lower()} is selected, so there is nothing to compare — widen the sidebar filters.")


def chapter_2(df):
    chapter(2, "ch2", "What the APIs added", "What did the external data bring in?")
    st.markdown(
        '<div class="story">Three outside services were asked about every dish — a recipe database, a weather '
        "service and a currency service — and their answers were joined onto the nutrition data using "
        "<b>dish_name</b> as the shared key. That added ten new attributes. Not every dish got an answer, "
        "though, so it is worth checking how complete the new data is.</div>",
        unsafe_allow_html=True,
    )
    left, right = st.columns([1, 1])
    with left:
        show_table(NEW_ATTRIBUTES, hide_index=True)
    with right:
        counts = df["has_api"].value_counts().rename({True: "Enriched by API", False: "No API match"})
        fig = px.pie(
            names=counts.index, values=counts.values, hole=0.55,
            color=counts.index, color_discrete_map={"Enriched by API": GREEN, "No API match": "#C9C9C9"},
        )
        fig.update_traces(textinfo="percent+label")
        fig.update_layout(showlegend=False)
        show(tidy(fig, 300))

    group_label = st.radio("Check completeness by", list(GROUPS), horizontal=True, key="c2_group")
    group = GROUPS[group_label]
    cov = (df.groupby(group)["has_api"].mean() * 100).sort_values()
    overall = df["has_api"].mean() * 100
    fig = px.bar(
        x=cov.values, y=cov.index, orientation="h",
        labels={"x": "Dishes with API data (%)", "y": group_label},
        color_discrete_sequence=[GREEN],
    )
    fig.add_vline(x=overall, line_dash="dash", line_color=ORANGE, annotation_text=f"overall {overall:.1f}%")
    fig.update_xaxes(range=[0, 100])
    show(tidy(fig, 340))

    if len(cov) >= 2 and overall < 100:
        spread = cov.max() - cov.min()
        verdict = (
            "no group is systematically left behind — the gaps look like general API unreliability, not a blind spot"
            if spread < 6 else
            f"**{cov.index[0]}** is noticeably worse served, which is worth investigating"
        )
        st.info(
            f"**What this tells us:** **{overall:.1f}%** of the selected dishes received API data. By "
            f"{group_label.lower()} the coverage ranges from **{cov.min():.1f}%** to **{cov.max():.1f}%** "
            f"(a **{spread:.1f}-point** spread), so {verdict}."
        )
    elif overall >= 100:
        st.info("**What this tells us:** the sidebar is set to *API-enriched dishes only*, so coverage is 100% by construction.")


def chapter_3(df):
    chapter(3, "ch3", "Weather and food", "Does the weather change what suits a dish?")
    d = df[df["has_api"]]
    st.markdown(
        '<div class="story">This question could not even be asked before the weather API: the nutrition data '
        "has no notion of today's conditions. Each dish carries a 0–1 <b>suitability score</b> built by "
        "combining its category with the temperature and sky at lookup time. Darker cells mean a better match.</div>",
        unsafe_allow_html=True,
    )
    if d.empty:
        st.warning("No API-enriched dishes in the current selection.")
        return
    by = st.radio("Compare dish categories against", ["Weather condition", "Temperature band"], horizontal=True, key="c3_by")
    col = "weather_condition" if by == "Weather condition" else "temp_band"
    pivot = d.pivot_table(index="category", columns=col, values="weather_suitability_score", aggfunc="mean")
    if by == "Temperature band":
        pivot = pivot.reindex(columns=[b for b in TEMP_BANDS if b in pivot.columns])
    fig = px.imshow(
        pivot, text_auto=".2f", aspect="auto", color_continuous_scale="Greens",
        labels=dict(color="Mean suitability", x=by, y="Category"),
    )
    show(tidy(fig, 420))

    cells = pivot.stack().sort_values(ascending=False)
    if len(cells) >= 2:
        (cat_hi, col_hi), v_hi = cells.index[0], cells.iloc[0]
        (cat_lo, col_lo), v_lo = cells.index[-1], cells.iloc[-1]
        st.info(
            f"**What this tells us:** the best pairing is **{cat_hi}** in **{col_hi}** conditions "
            f"(mean suitability **{v_hi:.2f}**) and the weakest is **{cat_lo}** in **{col_lo}** "
            f"(**{v_lo:.2f}**), against an overall average of **{d['weather_suitability_score'].mean():.2f}**. "
            "So context changes which dishes score as a good fit — information the original data could not supply."
        )
    st.caption(
        "Reading note: the suitability score is rule-based (for example, hot snacks and soups score up in rain, "
        "cold desserts score up in heat), so this chart shows those rules at work rather than measured eating behaviour."
    )


def chapter_4(df):
    chapter(4, "ch4", "Healthy vs. expensive", "Does healthier food cost more?")
    d = df[df["has_api"]]
    st.markdown(
        '<div class="story">Price only exists because of the currency API, and health grades only exist '
        "because of the original analysis. Putting them side by side lets us test a common assumption.</div>",
        unsafe_allow_html=True,
    )
    if len(d) < 3:
        st.warning("Not enough API-enriched dishes in the current selection.")
        return
    cur_label = st.radio("Show prices in", list(CURRENCIES), horizontal=True, key="c4_cur")
    cost_col, sym = CURRENCIES[cur_label]

    left, right = st.columns(2)
    with left:
        g = d.groupby("nutriscore_grade")[cost_col].mean().sort_index()
        fig = px.bar(x=g.index, y=g.values, labels={"x": "Nutri-Score grade", "y": f"Mean price ({sym})"},
                     color_discrete_sequence=[ORANGE], text=[f"{sym}{v:,.2f}" for v in g.values])
        fig.add_hline(y=d[cost_col].mean(), line_dash="dash", line_color=GREEN)
        fig.update_traces(textposition="outside")
        show(tidy(fig, 380))
    with right:
        sample = d.sample(min(2500, len(d)), random_state=1)
        fig = px.scatter(sample, x="health_score", y=cost_col, opacity=0.35, color_discrete_sequence=[GREEN],
                         labels={"health_score": "Health score", cost_col: f"Price ({sym})"})
        slope, intercept = np.polyfit(d["health_score"], d[cost_col], 1)
        xs = np.array([d["health_score"].min(), d["health_score"].max()])
        fig.add_trace(go.Scatter(x=xs, y=slope * xs + intercept, mode="lines", name="trend",
                                 line=dict(color=ORANGE, width=3)))
        fig.update_layout(showlegend=False)
        show(tidy(fig, 380))

    r = d["health_score"].corr(d[cost_col])
    gap = (g.max() - g.min()) / d[cost_col].mean() * 100
    if abs(r) < 0.1:
        meaning = "so price is a poor guide to how healthy a dish is."
    elif r > 0:
        meaning = "so healthier dishes do tend to cost somewhat more."
    else:
        meaning = "so healthier dishes tend to be somewhat cheaper."
    st.info(
        f"**What this tells us:** the correlation between health score and price is **r = {r:.2f}**, and mean price "
        f"moves by only **{gap:.1f}%** between the best and worst Nutri-Score grade, {meaning}"
    )


def chapter_5(df):
    chapter(5, "ch5", "What drives health", "Which variables actually explain the health score?")
    st.markdown(
        '<div class="story">If the API data were just repeating what the nutrition columns already said, it would '
        "correlate strongly with them. Here every variable is compared with the health score, coloured by "
        "where it came from.</div>",
        unsafe_allow_html=True,
    )
    cols = list(DRIVER_SOURCE)
    corr = df[cols + ["health_score"]].corr()["health_score"].drop("health_score").dropna().sort_values()
    plot = pd.DataFrame({"variable": corr.index, "r": corr.values, "source": [DRIVER_SOURCE[c] for c in corr.index]})
    fig = px.bar(plot, x="r", y="variable", color="source", orientation="h", color_discrete_map=SOURCE_COLORS,
                 labels={"r": "Correlation with health score", "variable": ""})
    fig.update_xaxes(range=[-1, 1])
    show(tidy(fig, 440))

    orig = plot[plot["source"] == "Original (LLM)"]
    api = plot[plot["source"] == "API-derived"]
    if not orig.empty and not api.empty:
        pos, neg = orig.loc[orig["r"].idxmax()], orig.loc[orig["r"].idxmin()]
        m = api["r"].abs().max()
        reading = (
            "all sit close to zero, so they carry information the nutrition columns do not"
            if m < 0.1 else "show some relationship worth a closer look"
        )
        st.info(
            f"**What this tells us:** the strongest positive driver is **{pos['variable']}** (r = {pos['r']:.2f}) and "
            f"the strongest negative is **{neg['variable']}** (r = {neg['r']:.2f}). The API-derived variables "
            f"never exceed **|r| = {m:.2f}** — they {reading}. That is the point of fusion: new, independent "
            "information rather than a restatement of what was already known."
        )
    with st.expander("See the full correlation matrix"):
        full = df[cols + ["health_score"]].corr()
        fig = px.imshow(full, text_auto=".2f", aspect="auto", color_continuous_scale="RdYlGn", zmin=-1, zmax=1)
        show(tidy(fig, 600))


def chapter_6(df):
    chapter(6, "ch6", "Put it together", "So what should I eat right now?")
    d = df[df["has_api"]]
    st.markdown(
        '<div class="story">This is the payoff of the fusion. Answering \"what should I eat, given the weather and my '
        "budget?\" needs nutrition from the original data <i>and</i> weather and price from the APIs. Neither source "
        "could answer it alone.</div>",
        unsafe_allow_html=True,
    )
    if d.empty:
        st.warning("No API-enriched dishes in the current selection.")
        return
    c1, c2, c3 = st.columns(3)
    conds = ["Any"] + sorted(d["weather_condition"].dropna().unique().tolist())
    cond = c1.selectbox("Sky today", conds, key="c6_cond")
    band = c2.selectbox("Temperature", ["Any"] + TEMP_BANDS, key="c6_band")
    max_cost = int(np.ceil(d["cost_inr"].max()))
    budget = c3.slider("Budget (₹)", int(d["cost_inr"].min()), max_cost, max_cost, key="c6_budget")
    min_health = st.slider("Minimum health score", 0, 100, 50, key="c6_health")

    pick = d[(d["cost_inr"] <= budget) & (d["health_score"] >= min_health)]
    if cond != "Any":
        pick = pick[pick["weather_condition"] == cond]
    if band != "Any":
        pick = pick[pick["temp_band"] == band]

    if pick.empty:
        st.warning("No dish satisfies all of these at once — relax the budget, the health floor or the weather.")
        return
    pick = pick.assign(match=0.5 * pick["health_score"] / 100 + 0.5 * pick["weather_suitability_score"])
    top = pick.sort_values("match", ascending=False).head(10)
    best = top.iloc[0]
    st.success(
        f"**{len(pick):,}** dishes pass your filters. The best overall match is **{best['dish_name']}** "
        f"({best['category']}): health **{best['health_score']:.0f}/100**, weather suitability "
        f"**{best['weather_suitability_score']:.2f}**, about **₹{best['cost_inr']:.0f}**."
    )
    table = top[["dish_name", "category", "calories_kcal", "health_score", "weather_suitability_score", "cost_inr"]].rename(
        columns={
            "dish_name": "Dish", "category": "Category", "calories_kcal": "kcal", "health_score": "Health",
            "weather_suitability_score": "Weather fit", "cost_inr": "Price (₹)",
        }
    )
    cfg = {
        "Health": st.column_config.ProgressColumn("Health", min_value=0, max_value=100, format="%.0f"),
        "Weather fit": st.column_config.ProgressColumn("Weather fit", min_value=0, max_value=1, format="%.2f"),
    }
    show_table(table, hide_index=True, column_config=cfg)
    st.caption("Ranking = half health score, half weather suitability.")


# ─────────────────────────────────────────────────────────────────────────
# Page
# ─────────────────────────────────────────────────────────────────────────
def main():
    path = find_csv()
    if path is None:
        st.title("🍽️ PlatePal — Data Story")
        st.warning("Could not find data/fused_dataset.csv. Upload the fused CSV to continue.")
        up = st.file_uploader("Fused dataset (CSV)", type="csv")
        if up is None:
            st.stop()
        source = up
    else:
        source = path
    df_all, info = load_data(source)

    # Sidebar: the reader's controls + table of contents
    sb = st.sidebar
    sb.markdown("### 📖 The story")
    for anchor, label in [
        ("ch1", "1 · Where we started"), ("ch2", "2 · What the APIs added"), ("ch3", "3 · Weather and food"),
        ("ch4", "4 · Healthy vs. expensive"), ("ch5", "5 · What drives health"), ("ch6", "6 · Put it together"),
    ]:
        sb.markdown(f"[{label}](#{anchor})")
    sb.divider()
    sb.markdown("### 🎛️ Filter the story")
    regions = sb.multiselect("Cuisine region", sorted(df_all["cuisine_region"].unique()),
                             default=sorted(df_all["cuisine_region"].unique()))
    cats = sb.multiselect("Dish category", sorted(df_all["category"].unique()),
                          default=sorted(df_all["category"].unique()))
    diet = sb.radio("Diet", ["All", "Vegetarian only", "Non-vegetarian only"])
    grades = sb.multiselect("Nutri-Score grade", sorted(df_all["nutriscore_grade"].unique()),
                            default=sorted(df_all["nutriscore_grade"].unique()))
    lo, hi = int(df_all["calories_kcal"].min()), int(np.ceil(df_all["calories_kcal"].max()))
    kcal = sb.slider("Calories (kcal)", lo, hi, (lo, hi))
    api_only = sb.checkbox("Only dishes enriched by the APIs", value=False)

    df = apply_filters(df_all, regions, cats, diet, grades, kcal, api_only)

    # Hero
    st.markdown('<div class="hero-title">🍽️ From a photo to a decision</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-sub">How external APIs turned a food-recognition app\'s nutrition data into context-aware '
        "answers — told through the fused PlatePal dataset.</div>",
        unsafe_allow_html=True,
    )
    if df.empty:
        st.warning("No dishes match the current filters. Loosen them in the sidebar to continue the story.")
        st.stop()

    k = st.columns(5)
    k[0].metric("Dishes in view", f"{len(df):,}", delta=f"{len(df) / len(df_all) * 100:.0f}% of all", delta_color="off")
    k[1].metric("API coverage", f"{df['has_api'].mean() * 100:.1f}%")
    k[2].metric("Avg calories", f"{df['calories_kcal'].mean():.0f} kcal")
    k[3].metric("Avg health score", f"{df['health_score'].mean():.1f}")
    cost = df.loc[df["has_api"], "cost_inr"]
    k[4].metric("Median price", f"₹{cost.median():.0f}" if len(cost) else "n/a")

    chapter_1(df)
    chapter_2(df)
    chapter_3(df)
    chapter_4(df)
    chapter_5(df)
    chapter_6(df)

    st.divider()
    st.subheader("About this data")
    st.markdown(
        f"""
- The nutrition records follow PlatePal's own Gemini-analysis fields and calculation logic but were **generated
  programmatically** to reach a usable size; they are not {info['raw_rows']:,} separate live model calls.
- About **10% of dishes have no API data by design**, mimicking the real misses seen during testing (no recipe
  match, service errors). Missing values are left blank, never imputed.
- **{info['dupes_removed']} duplicate rows** created by repeated API keys in the join were removed for this dashboard,
  so each dish is counted once.
- The weather **suitability score is rule-based**, and weather values were assigned independently of the dish, so
  chapter 3 demonstrates the feature working as designed, not real-world eating habits.
        """
    )


main()
