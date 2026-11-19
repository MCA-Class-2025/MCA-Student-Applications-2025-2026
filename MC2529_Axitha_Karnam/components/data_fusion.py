import os
import re
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.svm import SVC


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
            font-size: 1.5rem;
            font-weight: 700;
            line-height: 1.2;
        }
        .kpi-badge {
            display: inline-block;
            margin-top: 6px;
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            background-color: #ECFDF5;
            color: #059669;
        }
        .chart-section-title {
            color: #1E293B;
            font-size: 1.12rem;
            font-weight: 700;
            margin: 18px 0 4px 0;
            padding-left: 4px;
        }
        .explanation-box {
            background-color: #F8FAFC;
            border-left: 3px solid #3B82F6;
            padding: 8px 14px;
            margin-bottom: 20px;
            border-radius: 0 8px 8px 0;
            color: #475569;
            font-size: 0.9rem;
            line-height: 1.4;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def _style_light_fig(fig, height=380):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8FAFC",
        font=dict(color="#1E293B", family="Inter, sans-serif", size=12),
        height=height,
        margin=dict(l=35, r=25, t=35, b=35),
        legend=dict(
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#E2E8F0",
            borderwidth=1,
            font=dict(color="#334155")
        ),
        xaxis=dict(gridcolor="#E2E8F0", zerolinecolor="#CBD5E1"),
        yaxis=dict(gridcolor="#E2E8F0", zerolinecolor="#CBD5E1")
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
    if series is None or series.empty:
        return pd.Series(dtype=float)
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
    if df.empty:
        return None
    lookup = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lookup:
            return lookup[cand.lower()]
    return None


# ============================================================
# MACHINE LEARNING MODULE FOR ALL 5 APIS
# ============================================================

def _render_ml_analytics_for_api(df: pd.DataFrame, api_name: str):
    st.markdown("---")
    st.markdown(
        f"""
        <div class="fusion-header" style="margin-top: 20px;">
            <h2>Machine Learning Analytics ({api_name})</h2>
            <p>Training all 5 selected models (Regression & Classification) on fused dataset features</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    if df.empty or len(df) < 5:
        st.info(f"Not enough records in {api_name} dataset to run ML modeling.")
        return

    numeric_cols = [c for c in df.columns if df[c].dtype in [np.float64, np.int64] or _to_numeric_clean(df[c]).notna().sum() > len(df) * 0.3]
    if len(numeric_cols) < 2:
        st.warning("Insufficient numeric features found for modeling.")
        return

    scaler = StandardScaler()

    if "alpha_vantage" in api_name.lower():
        target_reg = _find_col(df, "Close")
        target_clf = _find_col(df, "Market_Sentiment", "Sentiment")
        feature_candidates = ["Open", "High", "Low", "Volume", "Volatility", "SMA_10", "EMA_10"]
    elif "macro" in api_name.lower() or "fred" in api_name.lower() or "frankfurter" in api_name.lower():
        target_reg = _find_col(df, "GDP (in billion USD)", "GDP")
        target_clf = _find_col(df, "Country")
        feature_candidates = ["Inflation Rate (%)", "Unemployment Rate (%)", "Economic Growth (%)", "Inflation", "Unemployment"]
    elif "coingecko" in api_name.lower():
        target_reg = _find_col(df, "Market Cap (USD)", "Market Cap", "Market_Cap", "Price (USD)", "Price")
        target_clf = _find_col(df, "Name", "Coin", "Symbol")
        feature_candidates = ["Price (USD)", "Price", "24h Volume (USD)", "Volume"]
    else:
        target_reg = None
        target_clf = _find_col(df, "publisher", "source")
        feature_candidates = []

    feature_cols = [c for c in feature_candidates if c in df.columns]
    if not feature_cols:
        feature_cols = [c for c in numeric_cols if c != target_reg][:4]

    if not feature_cols:
        st.warning("Could not automatically map valid features for ML training.")
        return

    model_df = df.dropna(subset=feature_cols).copy()
    X = model_df[feature_cols].apply(_to_numeric_clean).fillna(0)

    # --- TRAIN REGRESSION MODELS (1, 2, 3) ---
    if target_reg and not model_df[target_reg].dropna().empty:
        y_reg = _to_numeric_clean(model_df[target_reg]).fillna(0)
        if len(y_reg.unique()) > 1:
            X_tr, X_te, y_tr, y_te = train_test_split(X, y_reg, test_size=0.2, random_state=42)
            X_tr_sc = scaler.fit_transform(X_tr)
            X_te_sc = scaler.transform(X_te)

            lr = LinearRegression().fit(X_tr_sc, y_tr)
            p_lr = lr.predict(X_te_sc)
            r2_lr, rmse_lr = r2_score(y_te, p_lr), np.sqrt(mean_squared_error(y_te, p_lr))

            dt = DecisionTreeRegressor(random_state=42).fit(X_tr, y_tr)
            p_dt = dt.predict(X_te)
            r2_dt, rmse_dt = r2_score(y_te, p_dt), np.sqrt(mean_squared_error(y_te, p_dt))

            rf = RandomForestRegressor(n_estimators=100, random_state=42).fit(X_tr, y_tr)
            p_rf = rf.predict(X_te)
            r2_rf, rmse_rf = r2_score(y_te, p_rf), np.sqrt(mean_squared_error(y_te, p_rf))

            st.markdown('<div class="chart-section-title">Regression Models (Target Prediction)</div>', unsafe_allow_html=True)
            rc1, rc2, rc3 = st.columns(3)
            _render_kpi_card(rc1, "1. Multiple Linear Reg.", f"R²: {r2_lr:.4f}", f"RMSE: {rmse_lr:.2f}")
            _render_kpi_card(rc2, "2. Decision Tree Reg.", f"R²: {r2_dt:.4f}", f"RMSE: {rmse_dt:.2f}")
            _render_kpi_card(rc3, "3. Random Forest Reg.", f"R²: {r2_rf:.4f}", f"RMSE: {rmse_rf:.2f}")

            st.markdown(f'<div class="chart-section-title">Actual vs Predicted Parity Plot (Random Forest)</div>', unsafe_allow_html=True)
            comp_df = pd.DataFrame({"Actual": y_te, "Predicted": p_rf})
            fig_p = px.scatter(comp_df, x="Actual", y="Predicted", color_discrete_sequence=["#3B82F6"], title=f"Model Fit for {api_name}")
            min_v, max_v = min(y_te.min(), p_rf.min()), max(y_te.max(), p_rf.max())
            fig_p.add_shape(type="line", x0=min_v, y0=min_v, x1=max_v, y1=max_v, line=dict(color="#10B981", dash="dash", width=2))
            st.plotly_chart(_style_light_fig(fig_p), use_container_width=True)
            st.markdown(
                '<div class="explanation-box">'
                '<b>What this shows:</b> Evaluates how closely machine learning predictions match actual target values along the green parity line.'
                '</div>',
                unsafe_allow_html=True
            )

    # --- TRAIN CLASSIFICATION MODELS (4, 5) ---
    if target_clf and not model_df[target_clf].dropna().empty:
        y_clf = model_df[target_clf].astype(str)
        if y_clf.nunique() > 1 and len(y_clf.unique()) <= 20:
            X_trc, X_tec, y_trc, y_tec = train_test_split(X, y_clf, test_size=0.2, random_state=42)
            X_trc_sc = scaler.fit_transform(X_trc)
            X_tec_sc = scaler.transform(X_tec)

            log_c = LogisticRegression(max_iter=1000).fit(X_trc_sc, y_trc)
            acc_log = accuracy_score(y_tec, log_c.predict(X_tec_sc))

            svm_c = SVC().fit(X_trc_sc, y_trc)
            acc_svm = accuracy_score(y_tec, svm_c.predict(X_tec_sc))

            st.markdown('<div class="chart-section-title">Classification Models (Category/Sentiment Prediction)</div>', unsafe_allow_html=True)
            cc1, cc2 = st.columns(2)
            _render_kpi_card(cc1, "4. Logistic Regression", f"Accuracy: {acc_log * 100:.2f}%", "Linear Classifier")
            _render_kpi_card(cc2, "5. Support Vector Machine", f"Accuracy: {acc_svm * 100:.2f}%", "Kernel Classifier")
            st.markdown(
                '<div class="explanation-box">'
                '<b>What this shows:</b> Measures classification accuracy for categorical targets like sentiment or classification tags.'
                '</div>',
                unsafe_allow_html=True
            )


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
        if sel_cats: df = df[df[cat_col].astype(str).isin(sel_cats)]
    if sent_col:
        sents = sorted(df[sent_col].dropna().astype(str).unique().tolist())
        sel_sents = f2.multiselect("Market Sentiment", sents, default=sents, key="av_sent_filter")
        if sel_sents: df = df[df[sent_col].astype(str).isin(sel_sents)]
    if tag_col:
        tags = sorted(df[tag_col].dropna().astype(str).unique().tolist())
        sel_tags = f3.multiselect("News Tag", tags, default=tags, key="av_tag_filter")
        if sel_tags: df = df[df[tag_col].astype(str).isin(sel_tags)]

    if df.empty:
        st.info("No records match the selected filters.")
        return

    df = df.copy()
    if close_col: df["_close"] = _to_numeric_clean(df[close_col])
    if vol_col: df["_vol"] = _to_numeric_clean(df[vol_col])
    if volat_col: df["_volat"] = _to_numeric_clean(df[volat_col])

    c1, c2, c3, c4 = st.columns(4)
    _render_kpi_card(c1, "Latest Close Price", f"${df['_close'].dropna().iloc[-1]:,.2f}" if close_col and not df["_close"].dropna().empty else "$0.00", "Fused Stock Record")
    _render_kpi_card(c2, "Average Close", f"${df['_close'].mean():,.2f}" if close_col else "$0.00", f"{len(df)} Fused Rows")
    _render_kpi_card(c3, "Average Volatility", f"{df['_volat'].mean():,.4f}" if volat_col else "0.0000", "Risk Indicator")
    _render_kpi_card(c4, "Fused Observations", f"{len(df):,}", "Alpha Vantage")

    st.markdown('<div class="chart-section-title">1. Close price distribution by category</div>', unsafe_allow_html=True)
    if close_col and cat_col:
        fig1 = px.histogram(df.dropna(subset=["_close"]), x="_close", color=cat_col, nbins=15, barmode="stack", color_discrete_sequence=LIGHT_PALETTE)
        st.plotly_chart(_style_light_fig(fig1), use_container_width=True)
        st.markdown(
            '<div class="explanation-box">'
            '<b>What this shows:</b> This histogram displays the frequency and spread of stock close prices, stacked by industry category so we can see which sectors dominate specific price ranges.'
            '</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div class="chart-section-title">2. Close price spread by category — boxplot</div>', unsafe_allow_html=True)
    if close_col and cat_col:
        fig2 = px.box(df.dropna(subset=["_close"]), x=cat_col, y="_close", color=cat_col, color_discrete_sequence=LIGHT_PALETTE)
        fig2.update_layout(showlegend=False)
        st.plotly_chart(_style_light_fig(fig2), use_container_width=True)
        st.markdown(
            '<div class="explanation-box">'
            '<b>What this shows:</b> This boxplot highlights the median, interquartile range, and outliers of stock closing prices for each individual category, showing valuation variance.'
            '</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div class="chart-section-title">3–4. Market relationships & technical comparison</div>', unsafe_allow_html=True)
    col_left, col_right = st.columns(2)
    with col_left:
        if close_col and vol_col:
            fig3 = px.scatter(df.dropna(subset=["_close", "_vol"]), x="_vol", y="_close", color=cat_col if cat_col else None, color_discrete_sequence=LIGHT_PALETTE, title="Close Price vs. Trading Volume")
            st.plotly_chart(_style_light_fig(fig3, height=350), use_container_width=True)
            st.markdown(
                '<div class="explanation-box">'
                '<b>What this shows:</b> This scatter plot maps trading volume against stock closing prices to check if high-priced stocks correlate with higher market liquidity.'
                '</div>',
                unsafe_allow_html=True
            )
    with col_right:
        if sma_col and ema_col and cat_col:
            df["_sma"] = _to_numeric_clean(df[sma_col])
            df["_ema"] = _to_numeric_clean(df[ema_col])
            tech_grp = df.groupby(cat_col)[["_sma", "_ema"]].mean().reset_index()
            fig4 = px.bar(tech_grp, x=cat_col, y=["_sma", "_ema"], barmode="group", color_discrete_sequence=["#3B82F6", "#10B981"], title="Average SMA_10 vs. EMA_10 by Category")
            st.plotly_chart(_style_light_fig(fig4, height=350), use_container_width=True)
            st.markdown(
                '<div class="explanation-box">'
                '<b>What this shows:</b> This bar chart compares simple moving averages (SMA_10) and exponential moving averages (EMA_10) across categories to reveal short-term trend directions.'
                '</div>',
                unsafe_allow_html=True
            )

    _render_ml_analytics_for_api(df, "Alpha Vantage Stock Dataset")


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
        if sel_countries: df = df[df[country_col].astype(str).isin(sel_countries)]
    if year_col:
        years = sorted(df[year_col].dropna().astype(str).unique().tolist())
        sel_years = f2.multiselect("Year", years, default=years, key=f"{key_prefix}_year")
        if sel_years: df = df[df[year_col].astype(str).isin(sel_years)]

    if df.empty:
        st.info("No fused macroeconomic records match the selected filters.")
        return

    df = df.copy()
    if gdp_col: df["_gdp"] = _to_numeric_clean(df[gdp_col])
    if inf_col: df["_inf"] = _to_numeric_clean(df[inf_col])
    if unemp_col: df["_unemp"] = _to_numeric_clean(df[unemp_col])
    if growth_col: df["_growth"] = _to_numeric_clean(df[growth_col])

    c1, c2, c3, c4 = st.columns(4)
    _render_kpi_card(c1, "Latest Fused GDP", f"${df['_gdp'].dropna().iloc[-1]:,.1f}B" if gdp_col and not df["_gdp"].dropna().empty else "$0B", "Macro GDP")
    _render_kpi_card(c2, "Average Inflation", f"{df['_inf'].mean():,.2f}%" if inf_col else "0.00%", "Macro CPI")
    _render_kpi_card(c3, "Average Unemployment", f"{df['_unemp'].mean():,.2f}%" if unemp_col else "0.00%", "Labor Market")
    _render_kpi_card(c4, "Fused Observations", f"{len(df):,}", api_label)

    st.markdown('<div class="chart-section-title">1. GDP distribution across fused countries</div>', unsafe_allow_html=True)
    if country_col and gdp_col and not df["_gdp"].dropna().empty:
        fig1 = px.histogram(df.dropna(subset=["_gdp"]), x="_gdp", color=country_col, nbins=12, barmode="stack", color_discrete_sequence=LIGHT_PALETTE)
        st.plotly_chart(_style_light_fig(fig1), use_container_width=True)
        st.markdown(
            '<div class="explanation-box">'
            '<b>What this shows:</b> This histogram illustrates the distribution of Gross Domestic Product (GDP) values across different countries, categorized by nation.'
            '</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div class="chart-section-title">2. Inflation rate spread by country — boxplot</div>', unsafe_allow_html=True)
    if country_col and inf_col and not df["_inf"].dropna().empty:
        fig2 = px.box(df.dropna(subset=["_inf"]), x=country_col, y="_inf", color=country_col, color_discrete_sequence=LIGHT_PALETTE)
        fig2.update_layout(showlegend=False)
        st.plotly_chart(_style_light_fig(fig2), use_container_width=True)
        st.markdown(
            '<div class="explanation-box">'
            '<b>What this shows:</b> This boxplot visualizes inflation rate fluctuations and median levels for each country to compare economic price stability.'
            '</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div class="chart-section-title">3–4. Macroeconomic relationships</div>', unsafe_allow_html=True)
    col_left, col_right = st.columns(2)
    with col_left:
        if inf_col and unemp_col and not df["_inf"].dropna().empty and not df["_unemp"].dropna().empty:
            fig3 = px.scatter(df.dropna(subset=["_inf", "_unemp"]), x="_unemp", y="_inf", color=country_col if country_col else None, color_discrete_sequence=LIGHT_PALETTE, title="Inflation vs. Unemployment")
            st.plotly_chart(_style_light_fig(fig3, height=350), use_container_width=True)
            st.markdown(
                '<div class="explanation-box">'
                '<b>What this shows:</b> This scatter plot demonstrates the economic relationship between unemployment and inflation rates across different regions.'
                '</div>',
                unsafe_allow_html=True
            )
    with col_right:
        if country_col and growth_col and not df["_growth"].dropna().empty:
            grp_growth = df.groupby(country_col)[["_growth", "_inf"]].mean().reset_index()
            fig4 = px.bar(grp_growth, x=country_col, y=["_growth", "_inf"], barmode="group", color_discrete_sequence=["#10B981", "#F59E0B"], title="Economic Growth vs. Inflation")
            st.plotly_chart(_style_light_fig(fig4, height=350), use_container_width=True)
            st.markdown(
                '<div class="explanation-box">'
                '<b>What this shows:</b> This grouped bar chart compares average economic growth percentages against inflation rates for each country.'
                '</div>',
                unsafe_allow_html=True
            )

    _render_ml_analytics_for_api(df, f"{api_label} Macro Dataset")


def _viz_coingecko(df: pd.DataFrame):
    name_col = _find_col(df, "Name", "Coin", "Symbol", "Cryptocurrency")
    price_col = _find_col(df, "Price (USD)", "Price", "Current_Price", "Current Price")
    mcap_col = _find_col(df, "Market Cap (USD)", "Market Cap", "Market_Cap", "Market Cap(USD)")
    vol_col = _find_col(df, "24h Volume (USD)", "Volume", "Total_Volume", "24h Volume")
    chg_col = _find_col(df, "24h Change (%)", "Price_Change_24h", "24h Change")

    if name_col:
        coins = sorted(df[name_col].dropna().astype(str).unique().tolist())
        sel_coins = st.multiselect("Cryptocurrency", coins, default=coins, key="cg_coin_filter")
        if sel_coins: df = df[df[name_col].astype(str).isin(sel_coins)]

    if df.empty:
        st.info("No cryptocurrency records match the selected filters.")
        return

    df = df.copy()
    if price_col: df["_price"] = _to_numeric_clean(df[price_col])
    if mcap_col: df["_mcap"] = _to_numeric_clean(df[mcap_col])
    if vol_col: df["_vol"] = _to_numeric_clean(df[vol_col])
    if chg_col: df["_chg"] = _to_numeric_clean(df[chg_col])

    c1, c2, c3, c4 = st.columns(4)
    highest_price = f"${df['_price'].max():,.2f}" if price_col and not df["_price"].dropna().empty else "N/A"
    total_mcap = f"${df['_mcap'].sum() / 1e9:,.2f}B" if mcap_col and not df["_mcap"].dropna().empty else "N/A"
    avg_chg = f"{df['_chg'].mean():+.2f}%" if chg_col and not df["_chg"].dropna().empty else "0.00%"

    _render_kpi_card(c1, "Highest Asset Price", highest_price, "CoinGecko Fused")
    _render_kpi_card(c2, "Combined Market Cap", total_mcap, "Total Valuation")
    _render_kpi_card(c3, "Avg 24h Change", avg_chg, "Momentum")
    _render_kpi_card(c4, "Fused Crypto Records", f"{len(df):,}", "CoinGecko")

    st.markdown('<div class="chart-section-title">1. Market capitalization comparison across cryptocurrencies</div>', unsafe_allow_html=True)
    if name_col and mcap_col and not df["_mcap"].dropna().empty:
        fig1 = px.bar(df.dropna(subset=["_mcap"]).sort_values(by="_mcap", ascending=False), x=name_col, y="_mcap", color=name_col, color_discrete_sequence=LIGHT_PALETTE)
        fig1.update_layout(showlegend=False)
        st.plotly_chart(_style_light_fig(fig1), use_container_width=True)
        st.markdown(
            '<div class="explanation-box">'
            '<b>What this shows:</b> This bar chart ranks cryptocurrencies by their total market capitalization, highlighting the dominant digital assets.'
            '</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div class="chart-section-title">2. Price spread by cryptocurrency — boxplot</div>', unsafe_allow_html=True)
    if name_col and price_col and not df["_price"].dropna().empty:
        fig2 = px.box(df.dropna(subset=["_price"]), x=name_col, y="_price", color=name_col, color_discrete_sequence=LIGHT_PALETTE)
        fig2.update_layout(showlegend=False)
        st.plotly_chart(_style_light_fig(fig2), use_container_width=True)
        st.markdown(
            '<div class="explanation-box">'
            '<b>What this shows:</b> This boxplot displays the price volatility and distribution range for each cryptocurrency token in the dataset.'
            '</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div class="chart-section-title">3–4. Liquidity & 24h performance relationships</div>', unsafe_allow_html=True)
    col_left, col_right = st.columns(2)
    with col_left:
        if mcap_col and vol_col and not df["_mcap"].dropna().empty and not df["_vol"].dropna().empty:
            fig3 = px.scatter(df.dropna(subset=["_mcap", "_vol"]), x="_mcap", y="_vol", color=name_col if name_col else None, color_discrete_sequence=LIGHT_PALETTE, title="Volume vs. Market Cap")
            st.plotly_chart(_style_light_fig(fig3, height=350), use_container_width=True)
            st.markdown(
                '<div class="explanation-box">'
                '<b>What this shows:</b> This scatter plot correlates 24-hour trading volume with market capitalization to show asset liquidity levels.'
                '</div>',
                unsafe_allow_html=True
            )
    with col_right:
        if name_col and chg_col and not df["_chg"].dropna().empty:
            fig4 = px.bar(df.dropna(subset=["_chg"]), x=name_col, y="_chg", color=name_col, color_discrete_sequence=LIGHT_PALETTE, title="24h Price Change (%)")
            fig4.update_layout(showlegend=False)
            st.plotly_chart(_style_light_fig(fig4, height=350), use_container_width=True)
            st.markdown(
                '<div class="explanation-box">'
                '<b>What this shows:</b> This bar chart highlights the 24-hour percentage price change for each cryptocurrency, indicating short-term market gains or losses.'
                '</div>',
                unsafe_allow_html=True
            )

    _render_ml_analytics_for_api(df, "CoinGecko Crypto Dataset")


def _viz_financial_news(df: pd.DataFrame):
    stock_col = _find_col(df, "stock", "symbol", "ticker")
    pub_col = _find_col(df, "publisher", "source")
    date_col = _find_col(df, "date", "published_at")

    f1, f2 = st.columns(2)
    if stock_col:
        stocks = sorted(df[stock_col].dropna().astype(str).unique().tolist())
        sel_stocks = f1.multiselect("Stock Ticker", stocks, default=stocks, key="news_stock_filter")
        if sel_stocks: df = df[df[stock_col].astype(str).isin(sel_stocks)]
    if pub_col:
        pubs = sorted(df[pub_col].dropna().astype(str).unique().tolist())
        sel_pubs = f2.multiselect("Publisher", pubs, default=pubs, key="news_pub_filter")
        if sel_pubs: df = df[df[pub_col].astype(str).isin(sel_pubs)]

    if df.empty:
        st.info("No news records match the selected filters.")
        return

    df = df.copy()
    c1, c2, c3, c4 = st.columns(4)
    _render_kpi_card(c1, "Fused Articles", f"{len(df):,}", "Partner Headlines")
    _render_kpi_card(c2, "Distinct Publishers", f"{df[pub_col].nunique() if pub_col else 0}", "News Sources")
    _render_kpi_card(c3, "Tracked Tickers", f"{df[stock_col].nunique() if stock_col else 0}", "Equities")
    _render_kpi_card(c4, "Top Publisher", str(df[pub_col].value_counts().index[0])[:18] if pub_col and not df[pub_col].dropna().empty else "N/A", "Most Active")

    st.markdown('<div class="chart-section-title">1. Article volume distribution by publisher</div>', unsafe_allow_html=True)
    if pub_col:
        pub_counts = df[pub_col].astype(str).value_counts().reset_index()
        pub_counts.columns = ["Publisher", "Articles"]
        fig1 = px.bar(pub_counts.head(12), x="Publisher", y="Articles", color="Publisher", color_discrete_sequence=LIGHT_PALETTE)
        fig1.update_layout(showlegend=False)
        st.plotly_chart(_style_light_fig(fig1), use_container_width=True)
        st.markdown(
            '<div class="explanation-box">'
            '<b>What this shows:</b> This bar chart ranks news publishers by the volume of financial articles published, showing which media sources contribute the most.'
            '</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div class="chart-section-title">2. Timeline of fused financial headlines</div>', unsafe_allow_html=True)
    if date_col:
        df["_date_only"] = df[date_col].astype(str).str.slice(0, 10)
        timeline = df.groupby(["_date_only"] + ([pub_col] if pub_col else [])).size().reset_index(name="Articles")
        fig2 = px.bar(timeline, x="_date_only", y="Articles", color=pub_col if pub_col else None, barmode="stack", color_discrete_sequence=LIGHT_PALETTE)
        st.plotly_chart(_style_light_fig(fig2), use_container_width=True)
        st.markdown(
            '<div class="explanation-box">'
            '<b>What this shows:</b> This timeline chart tracks the daily volume of published news articles over time, segmented by publisher sources.'
            '</div>',
            unsafe_allow_html=True
        )

    _render_ml_analytics_for_api(df, "Marketaux Financial News Dataset")


# ============================================================
# MAIN ENTRY POINT CALLED BY app.py
# ============================================================

def render_data_fusion():
    """Renders ONLY the clean light-themed visualization diagrams for all 5 fused APIs."""
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
            f"Ask a question in the Chat tab to fuse data for **{selected_label}**, then view the charts here."
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