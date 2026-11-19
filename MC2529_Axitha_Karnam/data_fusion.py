import os
import re
import pandas as pd
import streamlit as st
import plotly.express as px


# ============================================================
# BACKWARD-COMPATIBLE STUBS (PREVENTS IMPORT ERRORS IN COMPONENTS)
# ============================================================

def get_alpha_vantage_data(*args, **kwargs):
    return {}


def get_frankfurter_data(*args, **kwargs):
    return {}


def get_coingecko_data(*args, **kwargs):
    return {}


def get_fred_data(*args, **kwargs):
    return {}


def get_twelve_data(*args, **kwargs):
    return {}


def perform_api_data_fusion(*args, **kwargs):
    return {"data_fusion": True, "type": "API Data Fusion", "sources": [], "results": {}}


def format_fusion_result(*args, **kwargs):
    return ""


# ============================================================
# FUSED CSV CONFIGURATION (ALL 5 APIS)
# ============================================================

FUSED_DATASETS = {
    "Alpha Vantage (Stock & Technicals)": {
        "key": "alpha_vantage",
        "path": "csv/fused/fused_alpha_vantage.csv",
        "subtitle": "Fused Stock OHLC, Volume, Volatility, Technicals & Market Sentiment"
    },
    "Frankfurter (Global Macro & FX)": {
        "key": "frankfurter",
        "path": "csv/fused/fused_frankfurter.csv",
        "subtitle": "Fused Country GDP, Inflation, Unemployment, Growth & Exchange Rates"
    },
    "CoinGecko (Cryptocurrency Market)": {
        "key": "coingecko",
        "path": "csv/fused/fused_coingecko.csv",
        "subtitle": "Fused Crypto Prices, Market Cap, Supply, Volume & Live API Metrics"
    },
    "FRED (Federal Reserve Macro)": {
        "key": "fred",
        "path": "csv/fused/fused_fred.csv",
        "subtitle": "Fused Historical Dataset vs. Federal Reserve Economic Data"
    },
    "Marketaux (Financial News)": {
        "key": "financial_news",
        "path": "csv/fused/fused_financial_news.csv",
        "subtitle": "Fused Partner Headlines, Publishers, Tickers & Live News Coverage"
    }
}

LIGHT_PALETTE = [
    "#3B82F6",  # Sky Blue
    "#10B981",  # Emerald Mint
    "#F59E0B",  # Warm Amber
    "#8B5CF6",  # Soft Violet
    "#EC4899",  # Rose Pink
    "#06B6D4",  # Cyan
    "#6366F1",  # Indigo
    "#14B8A6",  # Teal
    "#F97316",  # Coral Orange
    "#84CC16"   # Lime
]


# ============================================================
# LIGHT THEME STYLING & HELPERS
# ============================================================

def _inject_light_dashboard_css():
    st.markdown(
        """
        <style>
        .fusion-header {
            background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%);
            border: 1px solid #DBEAFE;
            border-radius: 14px;
            padding: 18px 24px;
            margin-bottom: 18px;
        }
        .fusion-header h2 {
            color: #1E293B;
            margin: 0 0 4px 0;
            font-size: 1.55rem;
            font-weight: 700;
        }
        .fusion-header p {
            color: #64748B;
            margin: 0;
            font-size: 0.92rem;
        }
        .kpi-card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 16px 20px;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
            margin-bottom: 14px;
        }
        .kpi-title {
            color: #64748B;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 6px;
        }
        .kpi-value {
            color: #0F172A;
            font-size: 1.65rem;
            font-weight: 700;
            line-height: 1.2;
        }
        .kpi-badge {
            display: inline-block;
            margin-top: 8px;
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
            background-color: #ECFDF5;
            color: #059669;
        }
        .chart-section-title {
            color: #1E293B;
            font-size: 1.12rem;
            font-weight: 700;
            margin: 18px 0 8px 0;
            padding-left: 4px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def _style_light_fig(fig, height=390):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8FAFC",
        font=dict(color="#1E293B", family="Inter, sans-serif", size=12),
        height=height,
        margin=dict(l=35, r=25, t=42, b=35),
        legend=dict(
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#E2E8F0",
            borderwidth=1,
            font=dict(color="#334155")
        ),
        xaxis=dict(
            gridcolor="#E2E8F0",
            zerolinecolor="#CBD5E1",
            title_font=dict(color="#334155"),
            tickfont=dict(color="#475569")
        ),
        yaxis=dict(
            gridcolor="#E2E8F0",
            zerolinecolor="#CBD5E1",
            title_font=dict(color="#334155"),
            tickfont=dict(color="#475569")
        )
    )
    return fig


def _render_kpi_card(col, title: str, value: str, badge: str = ""):
    badge_html = f'<div class="kpi-badge">{badge}</div>' if badge else ""
    col.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True
    )


def _norm_col(col):
    return re.sub(r"\s+", " ", str(col).replace("\ufeff", "").replace("\xa0", " ")).strip()


def _to_numeric_clean(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.replace("€", "", regex=False)
        .str.replace("₹", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.strip()
    )
    cleaned = cleaned.replace({"null": None, "None": None, "nan": None, "NaN": None, "N/A": None, "": None})
    return pd.to_numeric(cleaned, errors="coerce")


def _load_fused_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
        df.columns = [_norm_col(c) for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


def _find_col(df: pd.DataFrame, *candidates):
    lookup = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lookup:
            return lookup[cand.lower()]
    return None


# ============================================================
# VISUALIZATION BUILDERS FOR EACH OF THE 5 APIS
# ============================================================

def _viz_alpha_vantage(df: pd.DataFrame):
    cat_col = _find_col(df, "Category", "Sector")
    sent_col = _find_col(df, "Market_Sentiment", "Market Sentiment")
    tag_col = _find_col(df, "News_Tag", "News Tag")
    close_col = _find_col(df, "Close")
    vol_col = _find_col(df, "Volume")
    volat_col = _find_col(df, "Volatility")
    sma_col = _find_col(df, "SMA_10")
    ema_col = _find_col(df, "EMA_10")

    f1, f2, f3 = st.columns([1.3, 1.3, 1])
    if cat_col:
        cats = sorted(df[cat_col].dropna().astype(str).unique().tolist())
        sel_cats = f1.multiselect("Category", cats, default=cats, key="av_cat_filter")
        if sel_cats:
            df = df[df[cat_col].astype(str).isin(sel_cats)]
    if sent_col:
        sents = sorted(df[sent_col].dropna().astype(str).unique().tolist())
        sel_sents = f2.multiselect("Market Sentiment", sents, default=sents, key="av_sent_filter")
        if sel_sents:
            df = df[df[sent_col].astype(str).isin(sel_sents)]
    if tag_col:
        tags = sorted(df[tag_col].dropna().astype(str).unique().tolist())
        sel_tags = f3.multiselect("News Tag", tags, default=tags, key="av_tag_filter")
        if sel_tags:
            df = df[df[tag_col].astype(str).isin(sel_tags)]

    if df.empty:
        st.info("No records match the selected filters.")
        return

    df = df.copy()
    if close_col:
        df["_close"] = _to_numeric_clean(df[close_col])
    if vol_col:
        df["_vol"] = _to_numeric_clean(df[vol_col])
    if volat_col:
        df["_volat"] = _to_numeric_clean(df[volat_col])

    c1, c2, c3, c4 = st.columns(4)
    latest_close = df["_close"].dropna().iloc[-1] if close_col and not df["_close"].dropna().empty else 0.0
    avg_close = df["_close"].mean() if close_col else 0.0
    avg_volat = df["_volat"].mean() if volat_col else 0.0
    _render_kpi_card(c1, "Latest Close Price", f"${latest_close:,.2f}", "Fused Stock Record")
    _render_kpi_card(c2, "Average Close", f"${avg_close:,.2f}", f"{len(df)} Fused Rows")
    _render_kpi_card(c3, "Average Volatility", f"{avg_volat:,.4f}", "Risk Indicator")
    _render_kpi_card(c4, "Fused Observations", f"{len(df):,}", "Alpha Vantage")

    st.markdown('<div class="chart-section-title">1. Close price distribution by category</div>', unsafe_allow_html=True)
    if close_col and cat_col:
        fig1 = px.histogram(
            df.dropna(subset=["_close"]),
            x="_close",
            color=cat_col,
            nbins=15,
            barmode="stack",
            color_discrete_sequence=LIGHT_PALETTE,
            labels={"_close": "Close Price (USD)", cat_col: "Category"}
        )
        st.plotly_chart(_style_light_fig(fig1), use_container_width=True)

    st.markdown('<div class="chart-section-title">2. Close price spread by category — boxplot</div>', unsafe_allow_html=True)
    if close_col and cat_col:
        fig2 = px.box(
            df.dropna(subset=["_close"]),
            x=cat_col,
            y="_close",
            color=cat_col,
            points="all",
            color_discrete_sequence=LIGHT_PALETTE,
            labels={"_close": "Close Price (USD)", cat_col: "Category"}
        )
        fig2.update_layout(showlegend=False)
        st.plotly_chart(_style_light_fig(fig2), use_container_width=True)

    st.markdown('<div class="chart-section-title">3–4. Market relationships & technical comparison</div>', unsafe_allow_html=True)
    col_left, col_right = st.columns(2)
    with col_left:
        if close_col and vol_col:
            fig3 = px.scatter(
                df.dropna(subset=["_close", "_vol"]),
                x="_vol",
                y="_close",
                color=cat_col if cat_col else None,
                size="_volat" if volat_col and df["_volat"].notna().any() else None,
                color_discrete_sequence=LIGHT_PALETTE,
                title="Close Price vs. Trading Volume",
                labels={"_vol": "Trading Volume", "_close": "Close Price (USD)"}
            )
            st.plotly_chart(_style_light_fig(fig3, height=360), use_container_width=True)

    with col_right:
        if sma_col and ema_col and cat_col:
            df["_sma"] = _to_numeric_clean(df[sma_col])
            df["_ema"] = _to_numeric_clean(df[ema_col])
            tech_grp = df.groupby(cat_col)[["_sma", "_ema"]].mean().reset_index()
            fig4 = px.bar(
                tech_grp,
                x=cat_col,
                y=["_sma", "_ema"],
                barmode="group",
                color_discrete_sequence=["#3B82F6", "#10B981"],
                title="Average SMA_10 vs. EMA_10 by Category",
                labels={"value": "Indicator Value", "variable": "Indicator"}
            )
            st.plotly_chart(_style_light_fig(fig4, height=360), use_container_width=True)


def _viz_macro_economic(df: pd.DataFrame, api_label: str, key_prefix: str):
    country_col = _find_col(df, "Country")
    year_col = _find_col(df, "Year")
    gdp_col = _find_col(df, "GDP (in billion USD)", "GDP")
    inf_col = _find_col(df, "Inflation Rate (%)", "Inflation")
    unemp_col = _find_col(df, "Unemployment Rate (%)", "Unemployment")
    growth_col = _find_col(df, "Economic Growth (%)", "Economic Growth")

    f1, f2 = st.columns([1.6, 1])
    if country_col:
        countries = sorted(df[country_col].dropna().astype(str).unique().tolist())
        sel_countries = f1.multiselect("Country", countries, default=countries, key=f"{key_prefix}_country")
        if sel_countries:
            df = df[df[country_col].astype(str).isin(sel_countries)]
    if year_col:
        years = sorted(df[year_col].dropna().astype(str).unique().tolist())
        sel_years = f2.multiselect("Year", years, default=years, key=f"{key_prefix}_year")
        if sel_years:
            df = df[df[year_col].astype(str).isin(sel_years)]

    if df.empty:
        st.info("No fused macroeconomic records match the selected filters.")
        return

    df = df.copy()
    df["_gdp"] = _to_numeric_clean(df[gdp_col]) if gdp_col else pd.Series(dtype=float)
    df["_inf"] = _to_numeric_clean(df[inf_col]) if inf_col else pd.Series(dtype=float)
    df["_unemp"] = _to_numeric_clean(df[unemp_col]) if unemp_col else pd.Series(dtype=float)
    df["_growth"] = _to_numeric_clean(df[growth_col]) if growth_col else pd.Series(dtype=float)

    c1, c2, c3, c4 = st.columns(4)
    latest_gdp = df["_gdp"].dropna().iloc[-1] if not df["_gdp"].dropna().empty else 0.0
    latest_country = str(df[country_col].iloc[-1]) if country_col else "N/A"
    avg_inf = df["_inf"].mean() if not df["_inf"].dropna().empty else 0.0
    avg_unemp = df["_unemp"].mean() if not df["_unemp"].dropna().empty else 0.0

    _render_kpi_card(c1, "Latest Fused GDP", f"${latest_gdp:,.1f}B", f"{latest_country}")
    _render_kpi_card(c2, "Average Inflation", f"{avg_inf:,.2f}%", "Macro CPI")
    _render_kpi_card(c3, "Average Unemployment", f"{avg_unemp:,.2f}%", "Labor Market")
    _render_kpi_card(c4, "Fused Observations", f"{len(df):,}", api_label)

    st.markdown('<div class="chart-section-title">1. GDP distribution across fused countries</div>', unsafe_allow_html=True)
    if country_col and not df["_gdp"].dropna().empty:
        fig1 = px.histogram(
            df.dropna(subset=["_gdp"]),
            x="_gdp",
            color=country_col,
            nbins=12,
            barmode="stack",
            color_discrete_sequence=LIGHT_PALETTE,
            labels={"_gdp": "GDP (in Billion USD)", country_col: "Country"}
        )
        st.plotly_chart(_style_light_fig(fig1), use_container_width=True)

    st.markdown('<div class="chart-section-title">2. Inflation rate spread by country — boxplot</div>', unsafe_allow_html=True)
    if country_col and not df["_inf"].dropna().empty:
        fig2 = px.box(
            df.dropna(subset=["_inf"]),
            x=country_col,
            y="_inf",
            color=country_col,
            points="all",
            color_discrete_sequence=LIGHT_PALETTE,
            labels={"_inf": "Inflation Rate (%)", country_col: "Country"}
        )
        fig2.update_layout(showlegend=False)
        st.plotly_chart(_style_light_fig(fig2), use_container_width=True)

    st.markdown('<div class="chart-section-title">3–4. Macroeconomic relationships</div>', unsafe_allow_html=True)
    col_left, col_right = st.columns(2)
    with col_left:
        if not df["_inf"].dropna().empty and not df["_unemp"].dropna().empty:
            fig3 = px.scatter(
                df.dropna(subset=["_inf", "_unemp"]),
                x="_unemp",
                y="_inf",
                color=country_col if country_col else None,
                size="_gdp" if df["_gdp"].notna().any() else None,
                color_discrete_sequence=LIGHT_PALETTE,
                title="Phillips Curve: Inflation vs. Unemployment (%)",
                labels={"_unemp": "Unemployment Rate (%)", "_inf": "Inflation Rate (%)"}
            )
            st.plotly_chart(_style_light_fig(fig3, height=360), use_container_width=True)

    with col_right:
        if country_col and not df["_growth"].dropna().empty:
            grp_growth = df.groupby(country_col)[["_growth", "_inf"]].mean().reset_index()
            fig4 = px.bar(
                grp_growth,
                x=country_col,
                y=["_growth", "_inf"],
                barmode="group",
                color_discrete_sequence=["#10B981", "#F59E0B"],
                title="Average Economic Growth vs. Inflation by Country",
                labels={"value": "Percentage (%)", "variable": "Indicator"}
            )
            st.plotly_chart(_style_light_fig(fig4, height=360), use_container_width=True)


def _viz_coingecko(df: pd.DataFrame):
    name_col = _find_col(df, "Name", "Coin", "Symbol")
    price_col = _find_col(df, "Price (USD)", "Price", "Current_Price")
    mcap_col = _find_col(df, "Market Cap (USD)", "Market Cap", "Market_Cap")
    vol_col = _find_col(df, "24h Volume (USD)", "Volume", "Total_Volume")
    chg_col = _find_col(df, "24h Change (%)", "Price_Change_24h")

    if name_col:
        coins = sorted(df[name_col].dropna().astype(str).unique().tolist())
        sel_coins = st.multiselect("Cryptocurrency", coins, default=coins, key="cg_coin_filter")
        if sel_coins:
            df = df[df[name_col].astype(str).isin(sel_coins)]

    if df.empty:
        st.info("No cryptocurrency records match the selected filters.")
        return

    df = df.copy()
    df["_price"] = _to_numeric_clean(df[price_col]) if price_col else pd.Series(dtype=float)
    df["_mcap"] = _to_numeric_clean(df[mcap_col]) if mcap_col else pd.Series(dtype=float)
    df["_vol"] = _to_numeric_clean(df[vol_col]) if vol_col else pd.Series(dtype=float)
    df["_chg"] = _to_numeric_clean(df[chg_col]) if chg_col else pd.Series(dtype=float)

    c1, c2, c3, c4 = st.columns(4)
    top_price = df["_price"].max() if not df["_price"].dropna().empty else 0.0
    total_mcap = df["_mcap"].sum() if not df["_mcap"].dropna().empty else 0.0
    avg_chg = df["_chg"].mean() if not df["_chg"].dropna().empty else 0.0

    _render_kpi_card(c1, "Highest Asset Price", f"${top_price:,.2f}", "CoinGecko Fused")
    _render_kpi_card(c2, "Combined Market Cap", f"${total_mcap / 1e9:,.2f}B", "Total Valuation")
    _render_kpi_card(c3, "Avg 24h Change", f"{avg_chg:+.2f}%", "Momentum")
    _render_kpi_card(c4, "Fused Crypto Records", f"{len(df):,}", "CoinGecko")

    st.markdown('<div class="chart-section-title">1. Market capitalization comparison across cryptocurrencies</div>', unsafe_allow_html=True)
    if name_col and not df["_mcap"].dropna().empty:
        fig1 = px.bar(
            df.dropna(subset=["_mcap"]).sort_values(by="_mcap", ascending=False),
            x=name_col,
            y="_mcap",
            color=name_col,
            color_discrete_sequence=LIGHT_PALETTE,
            labels={"_mcap": "Market Cap (USD)", name_col: "Cryptocurrency"}
        )
        fig1.update_layout(showlegend=False)
        st.plotly_chart(_style_light_fig(fig1), use_container_width=True)

    st.markdown('<div class="chart-section-title">2. Price spread by cryptocurrency — boxplot</div>', unsafe_allow_html=True)
    if name_col and not df["_price"].dropna().empty:
        fig2 = px.box(
            df.dropna(subset=["_price"]),
            x=name_col,
            y="_price",
            color=name_col,
            points="all",
            color_discrete_sequence=LIGHT_PALETTE,
            labels={"_price": "Price (USD)", name_col: "Cryptocurrency"}
        )
        fig2.update_layout(showlegend=False)
        st.plotly_chart(_style_light_fig(fig2), use_container_width=True)

    st.markdown('<div class="chart-section-title">3–4. Liquidity & 24h performance relationships</div>', unsafe_allow_html=True)
    col_left, col_right = st.columns(2)
    with col_left:
        if not df["_mcap"].dropna().empty and not df["_vol"].dropna().empty:
            fig3 = px.scatter(
                df.dropna(subset=["_mcap", "_vol"]),
                x="_mcap",
                y="_vol",
                color=name_col if name_col else None,
                size="_price" if df["_price"].notna().any() else None,
                color_discrete_sequence=LIGHT_PALETTE,
                title="24h Trading Volume vs. Market Cap",
                labels={"_mcap": "Market Cap (USD)", "_vol": "24h Volume (USD)"}
            )
            st.plotly_chart(_style_light_fig(fig3, height=360), use_container_width=True)

    with col_right:
        if name_col and not df["_chg"].dropna().empty:
            fig4 = px.bar(
                df.dropna(subset=["_chg"]),
                x=name_col,
                y="_chg",
                color=name_col,
                color_discrete_sequence=LIGHT_PALETTE,
                title="24h Price Change (%) by Asset",
                labels={"_chg": "24h Change (%)", name_col: "Cryptocurrency"}
            )
            fig4.update_layout(showlegend=False)
            st.plotly_chart(_style_light_fig(fig4, height=360), use_container_width=True)


def _viz_financial_news(df: pd.DataFrame):
    stock_col = _find_col(df, "stock", "symbol", "ticker")
    pub_col = _find_col(df, "publisher", "source")
    date_col = _find_col(df, "date", "published_at")

    f1, f2 = st.columns(2)
    if stock_col:
        stocks = sorted(df[stock_col].dropna().astype(str).unique().tolist())
        sel_stocks = f1.multiselect("Stock Ticker", stocks, default=stocks, key="news_stock_filter")
        if sel_stocks:
            df = df[df[stock_col].astype(str).isin(sel_stocks)]
    if pub_col:
        pubs = sorted(df[pub_col].dropna().astype(str).unique().tolist())
        sel_pubs = f2.multiselect("Publisher", pubs, default=pubs, key="news_pub_filter")
        if sel_pubs:
            df = df[df[pub_col].astype(str).isin(sel_pubs)]

    if df.empty:
        st.info("No news records match the selected filters.")
        return

    df = df.copy()
    c1, c2, c3, c4 = st.columns(4)
    distinct_pubs = df[pub_col].nunique() if pub_col else 0
    distinct_stocks = df[stock_col].nunique() if stock_col else 0
    top_pub = str(df[pub_col].value_counts().index[0]) if pub_col and not df[pub_col].dropna().empty else "N/A"

    _render_kpi_card(c1, "Fused Articles", f"{len(df):,}", "Partner Headlines")
    _render_kpi_card(c2, "Distinct Publishers", f"{distinct_pubs}", "News Sources")
    _render_kpi_card(c3, "Tracked Tickers", f"{distinct_stocks}", "Equities")
    _render_kpi_card(c4, "Top Publisher", top_pub[:18], "Most Active")

    st.markdown('<div class="chart-section-title">1. Article volume distribution by publisher</div>', unsafe_allow_html=True)
    if pub_col:
        pub_counts = df[pub_col].astype(str).value_counts().reset_index()
        pub_counts.columns = ["Publisher", "Articles"]
        fig1 = px.bar(
            pub_counts.head(12),
            x="Publisher",
            y="Articles",
            color="Publisher",
            color_discrete_sequence=LIGHT_PALETTE
        )
        fig1.update_layout(showlegend=False)
        st.plotly_chart(_style_light_fig(fig1), use_container_width=True)

    st.markdown('<div class="chart-section-title">2. Timeline of fused financial headlines</div>', unsafe_allow_html=True)
    if date_col:
        df["_date_only"] = df[date_col].astype(str).str.slice(0, 10)
        timeline = df.groupby(["_date_only"] + ([pub_col] if pub_col else [])).size().reset_index(name="Articles")
        fig2 = px.bar(
            timeline,
            x="_date_only",
            y="Articles",
            color=pub_col if pub_col else None,
            barmode="stack",
            color_discrete_sequence=LIGHT_PALETTE,
            labels={"_date_only": "Publication Date", "Articles": "Headline Count"}
        )
        st.plotly_chart(_style_light_fig(fig2), use_container_width=True)


# ============================================================
# MAIN STREAMLIT VISUALIZATION ENTRY POINT
# ============================================================

def render_fusion_dashboard():
    """Renders ONLY the clean light-themed visualization dashboard for all 5 fused APIs."""
    _inject_light_dashboard_css()

    st.markdown(
        """
        <div class="fusion-header">
            <h2>API Data Fusion Visualizations</h2>
            <p>Interactive light-theme visual analytics across all 5 fused API datasets</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    selected_label = st.selectbox(
        "Select Fused API Dataset",
        options=list(FUSED_DATASETS.keys()),
        index=0,
        key="fusion_api_selector"
    )

    meta = FUSED_DATASETS[selected_label]
    csv_path = meta["path"]
    api_key = meta["key"]

    st.caption(f"Source: `{csv_path}` — {meta['subtitle']}")

    df = _load_fused_csv(csv_path)
    if df.empty:
        st.info(
            f"No fused records found yet in `{csv_path}`. "
            f"Ask a question in the chat assistant to fuse data for **{selected_label}**, then view the charts here."
        )
        return

    if api_key == "alpha_vantage":
        _viz_alpha_vantage(df)
    elif api_key == "frankfurter":
        _viz_macro_economic(df, api_label="Frankfurter", key_prefix="ff")
    elif api_key == "fred":
        _viz_macro_economic(df, api_label="FRED", key_prefix="fred")
    elif api_key == "coingecko":
        _viz_coingecko(df)
    elif api_key == "financial_news":
        _viz_financial_news(df)


def render_data_fusion():
    render_fusion_dashboard()


def show_data_fusion():
    render_fusion_dashboard()


if __name__ == "__main__":
    st.set_page_config(
        page_title="API Data Fusion Visualizations",
        layout="wide"
    )
    render_fusion_dashboard()