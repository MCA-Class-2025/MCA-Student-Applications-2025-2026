import os
import time
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# Load .env variables natively
if os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

from src.rag import build_documents, build_faiss_index, stream_rag

st.set_page_config(
    page_title="CountryWise AI | Global Insights & Prediction Studio",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern Dark-Header + Crisp Card Studio Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        color: #0f172a;
    }
    h1, h2, h3, .hero-title, .kpi-num {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    .stApp {
        background: linear-gradient(180deg, #eef2ff 0%, #f8fafc 28%, #f1f5f9 100%) !important;
    }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1280px !important;
    }

    /* Bold Executive Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 55%, #312e81 100%);
        border-radius: 18px;
        padding: 24px 30px;
        color: #ffffff;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.16);
        margin-bottom: 18px;
    }
    .hero-title {
        font-size: 1.65rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0;
        color: #ffffff;
    }
    .hero-sub {
        font-size: 0.9rem;
        color: #cbd5e1;
        margin-top: 4px;
    }
    .live-pill {
        background: rgba(255, 255, 255, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.25);
        color: #e0e7ff;
        padding: 8px 16px;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
    .green-dot {
        width: 9px;
        height: 9px;
        background: #34d399;
        border-radius: 50%;
        box-shadow: 0 0 8px #34d399;
        display: inline-block;
    }

    /* Metric Cards */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 16px 20px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
        transition: transform 0.15s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-top {
        font-size: 0.76rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
    }
    .kpi-num {
        font-size: 1.65rem;
        font-weight: 800;
        color: #0f172a;
        margin: 4px 0;
    }
    .metric-sub {
        font-size: 0.78rem;
        color: #4f46e5;
        font-weight: 600;
    }

    /* Navigation Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #ffffff !important;
        padding: 6px !important;
        border-radius: 14px !important;
        gap: 6px !important;
        border: 1px solid #cbd5e1 !important;
        margin-bottom: 1.4rem !important;
        box-shadow: 0 4px 10px rgba(15, 23, 42, 0.04) !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.86rem !important;
        padding: 9px 16px !important;
        color: #475569 !important;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 10px rgba(79, 70, 229, 0.28) !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 10px 14px !important;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25) !important;
    }
    .side-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 12px 14px;
        font-size: 0.82rem;
        color: #334155;
        margin-top: 10px;
    }

    /* Quick Prompt Buttons */
    .stTabs div[data-testid="stButton"] button {
        border-radius: 12px !important;
        padding: 9px 14px !important;
        font-size: 0.84rem !important;
        font-weight: 600 !important;
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        color: #1e293b !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03) !important;
    }
    .stTabs div[data-testid="stButton"] button:hover {
        border-color: #4f46e5 !important;
        color: #4f46e5 !important;
        background: #eef2ff !important;
    }

    /* Chat Bubbles */
    .user-container { display: flex; justify-content: flex-end; margin-bottom: 12px; }
    .chat-bubble-user {
        background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
        color: #ffffff;
        padding: 12px 18px;
        border-radius: 16px 16px 4px 16px;
        font-size: 0.92rem;
        max-width: 75%;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
    }
    .assistant-container { display: flex; justify-content: flex-start; margin-bottom: 12px; }
    .chat-bubble-assistant {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        color: #0f172a;
        padding: 16px 20px;
        border-radius: 16px 16px 16px 4px;
        font-size: 0.94rem;
        line-height: 1.6;
        width: 100%;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("### 🌍 CountryWise AI")
    st.caption("Global Data & AI Assistant")

    mode = st.radio(
        "Choose Data Source:",
        ["Full Multi-Source Data (156 Countries)", "Basic Happiness Report Only"],
        index=0
    )

    data_path = "data/fused_dataset.csv" if mode.startswith("Full") else "data/original_dataset.csv"

    @st.cache_resource
    def load_rag_pipeline(path):
        df = pd.read_csv(path)
        docs = build_documents(df)
        index = build_faiss_index(docs)
        return df, docs, index

    try:
        df, docs, index = load_rag_pipeline(data_path)
    except Exception as e:
        st.error(f"Cannot load dataset: {e}")
        st.stop()

    st.write("")
    if st.button("+ Start Fresh Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.run_prompt = None
        st.rerun()

    st.markdown(f"""
    <div class="side-card">
        <div style="font-weight:700; color:#0f172a; margin-bottom:6px;">System Overview</div>
        <div>• Countries Covered: <strong>{len(df)}</strong></div>
        <div>• Data Points / Country: <strong>{df.shape[1]}</strong></div>
        <div>• Searchable Fact Cards: <strong>{len(docs)}</strong></div>
        <div>• AI Answer Engine: <strong>Groq LLM</strong></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Recent Questions")
    if "chat_history" in st.session_state and st.session_state.chat_history:
        recent_queries = [m["content"] for m in st.session_state.chat_history if m["role"] == "user"]
        for q in reversed(recent_queries[-5:]):
            st.caption(f"↗ {q[:34]}{'...' if len(q) > 34 else ''}")
    else:
        st.caption("Ask a question to see history here.")

# ----------------- TRAIN & BENCHMARK 4 ML MODELS (CACHED) -----------------
@st.cache_data
def evaluate_ml_models(dataframe):
    candidate_cols = [
        "log_gdp_per_capita",
        "social_support",
        "wb_life_expectancy",
        "freedom",
        "annual_mean_temp_c"
    ]
    feats = [c for c in candidate_cols if c in dataframe.columns]
    clean_df = dataframe[["country"] + feats + ["happiness_score"]].dropna().reset_index(drop=True)

    X = clean_df[features := feats]
    y = clean_df["happiness_score"]

    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X, y, clean_df.index, test_size=0.20, random_state=42
    )
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    models = {
        "Linear Regression": make_pipeline(StandardScaler(), LinearRegression()),
        "Ridge Regression": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        "Decision Tree": DecisionTreeRegressor(max_depth=4, random_state=42),
        "Random Forest": RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
    }

    results = []
    test_predictions = {}

    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        cv_scores = cross_val_score(model, X, y, cv=kf, scoring="r2")

        r2 = r2_score(y_test, preds)
        mae = mean_absolute_error(y_test, preds)
        rmse = np.sqrt(mean_squared_error(y_test, preds))

        results.append({
            "Model Name": name,
            "Test Accuracy (R² %)": round(r2 * 100, 1),
            "5-Fold CV Accuracy (%)": round(cv_scores.mean() * 100, 1),
            "Avg Error (MAE)": round(mae, 3),
            "Typical Error (RMSE)": round(rmse, 3)
        })
        test_predictions[name] = preds

    results_df = pd.DataFrame(results).sort_values("Test Accuracy (R² %)", ascending=False).reset_index(drop=True)
    top_model_name = results_df.iloc[0]["Model Name"]

    # Build Actual vs Predicted Comparison Matrix on Test Countries
    test_countries = clean_df.loc[idx_test, "country"].values
    matrix_df = pd.DataFrame({
        "Country": test_countries,
        "Actual Score": np.round(y_test.values, 2),
        "Ridge Predicted": np.round(test_predictions["Ridge Regression"], 2),
        "Random Forest Predicted": np.round(test_predictions["Random Forest"], 2),
        "Difference (Best Model)": np.round(test_predictions[top_model_name] - y_test.values, 2)
    }).sort_values("Actual Score", ascending=False).reset_index(drop=True)

    # Fit smooth Ridge model on full clean dataset for live slider predictions
    best_full_model = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    best_full_model.fit(X, y)

    return features, clean_df, results_df, matrix_df, best_full_model

feats, clean_df, bench_df, matrix_df, live_model = evaluate_ml_models(df)
best_acc = bench_df["Test Accuracy (R² %)"].max()
winner_row = bench_df.iloc[0]

# ----------------- TOP HERO BANNER & KPI CARDS -----------------
top_nation = df.sort_values("happiness_score", ascending=False).iloc[0]

st.markdown(f"""
<div class="hero-banner">
    <div>
        <div class="hero-title">CountryWise AI — Global Insights & Prediction Studio</div>
        <div class="hero-sub">Ask questions in plain English, compare nations side-by-side, and test what drives national happiness.</div>
    </div>
    <div class="live-pill">
        <span class="green-dot"></span> {len(df)} Countries Active
    </div>
</div>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-top">Countries Analyzed</div>
        <div class="kpi-num">{len(df)}</div>
        <div class="metric-sub">4 Global Data Sources Merged</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-top">World Average Score</div>
        <div class="kpi-num">{df['happiness_score'].mean():.2f} / 10</div>
        <div class="metric-sub">Range: {df['happiness_score'].min():.2f} to {df['happiness_score'].max():.2f}</div>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-top">#1 Happiest Country</div>
        <div class="kpi-num">{top_nation['country']}</div>
        <div class="metric-sub">Score: {top_nation['happiness_score']:.2f} / 10</div>
    </div>
    """, unsafe_allow_html=True)
with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-top">Best Model Accuracy</div>
        <div class="kpi-num">{best_acc:.1f}%</div>
        <div class="metric-sub">{winner_row['Model Name']}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ----------------- NAVIGATION TABS -----------------
tab_chat, tab_compare, tab_predict, tab_models, tab_eda, tab_data = st.tabs([
    "💬 AI Chatbot",
    "⚖️ Compare Countries",
    "🔮 Score Simulator",
    "🏆 Model Accuracy & Matrix",
    "📊 Visual Trends",
    "📁 Browse Data"
])

# ----------------- TAB 1: AI CHATBOT -----------------
with tab_chat:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "run_prompt" not in st.session_state:
        st.session_state.run_prompt = None

    if not st.session_state.chat_history:
        col_intro, col_chart = st.columns([1.15, 1], gap="large")
        with col_intro:
            st.markdown("""
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:16px; padding:24px; height:100%;">
                <h4 style="margin-top:0;">Ask Anything About Any Country</h4>
                <p style="color:#475569; font-size:0.92rem; line-height:1.6;">
                    Our AI reads directly from verified World Happiness, World Bank, Weather, and Wikipedia records—so every answer is grounded in real numbers without guessing.
                </p>
                <p style="color:#4f46e5; font-size:0.85rem; font-weight:600; margin-bottom:0;">
                    👇 Click a sample question below or type your own at the bottom:
                </p>
            </div>
            """, unsafe_allow_html=True)
        with col_chart:
            if "region" in df.columns:
                reg_avg = df.groupby("region")["happiness_score"].mean().sort_values(ascending=True)
                st.markdown("**Average Happiness Score by Region**")
                st.bar_chart(reg_avg, height=185, color="#4f46e5")

    st.write("")
    p1, p2, p3, p4 = st.columns(4)
    if p1.button("🏆 Top 5 Happiest Nations", use_container_width=True):
        st.session_state.run_prompt = "Which are the top 5 happiest nations in the world and what are their scores?"
    if p2.button("🇫🇮 About Finland", use_container_width=True):
        st.session_state.run_prompt = "Tell me about the history, origins, and governance of Finland."
    if p3.button("🇮🇳 India Economy & Climate", use_container_width=True):
        st.session_state.run_prompt = "What is India's capital city, annual mean temperature, and happiness rank?"
    if p4.button("🛡️ Out-of-Topic Safety Check", use_container_width=True):
        st.session_state.run_prompt = "What is the stock ticker for Apple?"

    st.write("")

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-container"><div class="chat-bubble-user">{msg["content"]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="assistant-container"><div class="chat-bubble-assistant">{msg["content"]}</div></div>', unsafe_allow_html=True)
            st.caption(f"⏱️ Answered in {msg.get('latency', 0.0)}s using verified country records")
            if "context" in msg and msg["context"]:
                with st.expander(f"See Source Facts Used ({len(msg['context'])} records)"):
                    for i, c in enumerate(msg["context"], 1):
                        st.caption(f"Source #{i} | Match Score: {c['score']:.2f}")
                        st.code(c["text"], language="text")

    typed_q = st.chat_input("Type your question here (e.g., Compare weather and economy of Japan and Norway)...")
    active_prompt = typed_q or st.session_state.run_prompt

    if active_prompt:
        st.session_state.run_prompt = None
        st.session_state.chat_history.append({"role": "user", "content": active_prompt})
        st.markdown(f'<div class="user-container"><div class="chat-bubble-user">{active_prompt}</div></div>', unsafe_allow_html=True)

        with st.chat_message("assistant"):
            start_t = time.time()
            stream_gen, retrieved = stream_rag(active_prompt, index, docs)

            def token_gen():
                for chunk in stream_gen:
                    delta = chunk.choices[0].delta.content or ""
                    yield delta

            answer_text = st.write_stream(token_gen())
            elapsed = round(time.time() - start_t, 2)

            with st.expander(f"See Source Facts Used ({len(retrieved)} records)"):
                for i, c in enumerate(retrieved, 1):
                    st.caption(f"Source #{i} | Match Score: {c['score']:.2f}")
                    st.code(c["text"], language="text")

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer_text,
                "latency": elapsed,
                "mode": mode,
                "context": retrieved
            })
            st.rerun()

# ----------------- TAB 2: COMPARE COUNTRIES -----------------
with tab_compare:
    st.subheader("Compare Any Two Countries Side-by-Side")
    st.caption("Pick two countries below to immediately see how their economy, health, weather, and happiness stack up.")

    c_list = sorted(df["country"].unique().tolist())
    ca, cb = st.columns(2)
    with ca:
        n1 = st.selectbox("First Country:", c_list, index=c_list.index("Finland") if "Finland" in c_list else 0)
    with cb:
        n2 = st.selectbox("Second Country:", c_list, index=c_list.index("India") if "India" in c_list else 1)

    if n1 and n2:
        r1 = df[df["country"] == n1].iloc[0]
        r2 = df[df["country"] == n2].iloc[0]

        m1, m2, m3 = st.columns(3)
        score_diff = float(r1["happiness_score"]) - float(r2["happiness_score"])
        m1.metric(f"{n1} Happiness Score", f"{r1['happiness_score']:.2f} / 10", f"{score_diff:+.2f} vs {n2}")

        if "wb_life_expectancy" in df.columns and pd.notna(r1["wb_life_expectancy"]) and pd.notna(r2["wb_life_expectancy"]):
            le_diff = float(r1["wb_life_expectancy"]) - float(r2["wb_life_expectancy"])
            m2.metric(f"{n1} Life Expectancy", f"{r1['wb_life_expectancy']:.1f} yrs", f"{le_diff:+.1f} yrs vs {n2}")

        if "annual_mean_temp_c" in df.columns and pd.notna(r1["annual_mean_temp_c"]) and pd.notna(r2["annual_mean_temp_c"]):
            t_diff = float(r1["annual_mean_temp_c"]) - float(r2["annual_mean_temp_c"])
            m3.metric(f"{n1} Average Temp", f"{r1['annual_mean_temp_c']:.1f} °C", f"{t_diff:+.1f} °C vs {n2}")

        st.write("")
        fields = [
            ("World Happiness Rank", "happiness_rank"),
            ("Happiness Score (out of 10)", "happiness_score"),
            ("Capital City", "capital"),
            ("Continent / Region", "region"),
            ("Average Yearly Temp (°C)", "annual_mean_temp_c"),
            ("Life Expectancy (Years)", "wb_life_expectancy"),
            ("Economy (Log GDP per Person)", "log_gdp_per_capita"),
            ("Social Support Score", "social_support"),
            ("Currency", "currency_code"),
            ("Exchange Rate (vs 1 USD)", "exchange_rate_usd")
        ]

        data_rows = []
        for label, col in fields:
            v1 = r1.get(col, "N/A")
            v2 = r2.get(col, "N/A")
            if isinstance(v1, float): v1 = f"{v1:.2f}"
            if isinstance(v2, float): v2 = f"{v2:.2f}"
            data_rows.append({"Factor": label, n1: v1, n2: v2})

        st.dataframe(pd.DataFrame(data_rows).set_index("Factor"), use_container_width=True)

# ----------------- TAB 3: SCORE SIMULATOR -----------------
with tab_predict:
    st.subheader("Interactive Happiness Score Simulator")
    st.caption("Move the sliders below to test how improving economy, social support, health, or freedom changes a country's predicted score.")

    if len(feats) < 2:
        st.warning("Switch to 'Full Multi-Source Data' in the left sidebar to unlock the simulator.")
    else:
        c_names = ["Custom Country"] + sorted(df["country"].dropna().unique().tolist())
        preset_country = st.selectbox(
            "Start with real numbers from a country:",
            c_names,
            index=c_names.index("India") if "India" in c_names else 0
        )

        if preset_country != "Custom Country":
            base_row = df[df["country"] == preset_country].iloc[0]
        else:
            base_row = clean_df[feats].median()

        st.write("")
        col_sliders, col_result = st.columns([1.3, 1], gap="large")

        friendly_names = {
            "log_gdp_per_capita": "Economy Strength (Log GDP per Person)",
            "social_support": "Community & Family Support",
            "wb_life_expectancy": "Average Life Expectancy (Years)",
            "freedom": "Personal Freedom Score",
            "annual_mean_temp_c": "Average Yearly Temperature (°C)"
        }

        user_inputs = {}
        with col_sliders:
            st.markdown("##### Adjust Country Factors")
            for feat in feats:
                min_v = float(clean_df[feat].min())
                max_v = float(clean_df[feat].max())
                default_v = float(base_row[feat]) if pd.notna(base_row[feat]) else float(clean_df[feat].median())
                default_v = max(min_v, min(max_v, default_v))
                user_inputs[feat] = st.slider(
                    friendly_names.get(feat, feat),
                    min_value=round(min_v, 2),
                    max_value=round(max_v, 2),
                    value=round(default_v, 2)
                )

        input_df = pd.DataFrame([user_inputs])
        pred_score = max(1.0, min(10.0, float(live_model.predict(input_df)[0])))

        est_rank = int((df["happiness_score"] > pred_score).sum()) + 1
        if pred_score >= 6.2:
            tier, tier_bg, tier_fg = "High Happiness Group", "#dcfce7", "#166534"
        elif pred_score >= 4.8:
            tier, tier_bg, tier_fg = "Medium Happiness Group", "#eef2ff", "#4338ca"
        else:
            tier, tier_bg, tier_fg = "Low Happiness Group", "#fee2e2", "#991b1b"

        with col_result:
            st.markdown(f"""
            <div style="background:#ffffff; border:1px solid #cbd5e1; border-top:5px solid #4f46e5; border-radius:16px; padding:26px; box-shadow:0 6px 18px rgba(15,23,42,0.06); text-align:center;">
                <div style="font-size:0.78rem; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:0.06em;">Predicted Score</div>
                <div style="font-size:3.2rem; font-weight:800; color:#0f172a; margin:8px 0;">{pred_score:.2f} <span style="font-size:1.1rem; color:#64748b;">/ 10</span></div>
                <div style="display:inline-block; background:{tier_bg}; color:{tier_fg}; padding:5px 14px; border-radius:999px; font-size:0.82rem; font-weight:700; margin-bottom:14px;">{tier}</div>
                <div style="font-size:0.92rem; color:#334155;">Estimated World Rank: <strong>#{est_rank}</strong> out of {len(df)}</div>
            </div>
            """, unsafe_allow_html=True)

            if preset_country != "Custom Country" and pd.notna(base_row["happiness_score"]):
                actual_s = float(base_row["happiness_score"])
                diff = pred_score - actual_s
                st.write("")
                st.info(f"**{preset_country}'s Real Score:** {actual_s:.2f}  |  **Change After Adjustment:** {diff:+.2f}")

            coefs = live_model.named_steps["ridge"].coef_
            coef_df = pd.DataFrame({
                "Factor": [friendly_names.get(f, f) for f in feats],
                "Impact Strength": coefs
            }).set_index("Factor")
            st.markdown("##### What Matters Most? (Factor Impact)")
            st.bar_chart(coef_df, height=200, color="#4f46e5")

# ----------------- TAB 4: MODEL ACCURACY & MATRIX -----------------
with tab_models:
    st.subheader("Model Comparison, Accuracy & Prediction Matrix")
    st.caption("We tested 4 different prediction algorithms on unseen countries (80% training / 20% testing + shuffled 5-Fold Cross-Validation) to pick the most reliable model.")

    if len(feats) < 2:
        st.warning("Switch to 'Full Multi-Source Data' in the sidebar to view model comparisons.")
    else:
        col_tbl, col_bar = st.columns([1.25, 1], gap="large")
        with col_tbl:
            st.markdown("##### 1. Side-by-Side Model Accuracy Table")
            st.dataframe(bench_df.set_index("Model Name"), use_container_width=True)
            st.success(f"**Top Performer:** {winner_row['Model Name']} achieves **{winner_row['Test Accuracy (R² %)']}% test accuracy** (5-Fold CV: **{winner_row['5-Fold CV Accuracy (%)']}%**) with an average error of ±{winner_row['Avg Error (MAE)']}.")

        with col_bar:
            st.markdown("##### 2. Accuracy Comparison Chart (%)")
            chart_data = bench_df.set_index("Model Name")[["Test Accuracy (R² %)", "5-Fold CV Accuracy (%)"]]
            st.bar_chart(chart_data, height=250)

        st.markdown("---")
        st.markdown("##### 3. Actual vs. Predicted Country Matrix (Unseen Test Set)")
        st.caption("Compare each test country's real World Happiness Score against what our models predicted.")
        st.dataframe(matrix_df, use_container_width=True, height=340)

# ----------------- TAB 5: VISUAL TRENDS -----------------
with tab_eda:
    st.subheader("Global Trends & Relationships")
    st.caption("Visual patterns discovered across 156 nations.")

    col1, col2 = st.columns(2)
    with col1:
        if os.path.exists("report/figures/fig1_correlation_matrix.png"):
            st.image("report/figures/fig1_correlation_matrix.png", caption="How Different Country Factors Connect", use_container_width=True)
        if os.path.exists("report/figures/fig2_happiness_vs_temp.png"):
            st.image("report/figures/fig2_happiness_vs_temp.png", caption="Happiness Score vs. Yearly Temperature", use_container_width=True)
    with col2:
        if os.path.exists("report/figures/fig3_happiness_vs_life_expectancy.png"):
            st.image("report/figures/fig3_happiness_vs_life_expectancy.png", caption="Happiness Score vs. Life Expectancy", use_container_width=True)
        if os.path.exists("report/figures/fig4_happiness_by_region.png"):
            st.image("report/figures/fig4_happiness_by_region.png", caption="Happiness Scores Across World Regions", use_container_width=True)

# ----------------- TAB 6: BROWSE DATA -----------------
with tab_data:
    st.subheader("Explore All 156 Countries")
    c_search, c_reg = st.columns([2, 1])
    with c_search:
        query_filter = st.text_input("Search by country name:")
    with c_reg:
        if "region" in df.columns:
            reg_options = ["All Regions"] + sorted(df["region"].dropna().unique().tolist())
            selected_reg = st.selectbox("Filter by region:", reg_options)
        else:
            selected_reg = "All Regions"

    filtered = df.copy()
    if query_filter:
        filtered = filtered[filtered["country"].str.contains(query_filter, case=False, na=False)]
    if selected_reg != "All Regions" and "region" in filtered.columns:
        filtered = filtered[filtered["region"] == selected_reg]

    st.dataframe(filtered, use_container_width=True, height=460)