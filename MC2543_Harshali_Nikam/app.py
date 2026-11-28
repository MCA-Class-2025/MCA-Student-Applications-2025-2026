import streamlit as st
import pandas as pd
import json
from pathlib import Path
import os
import plotly.express as px

from data_fusion import run_raw_data_fusion
from feature_fusion import run_feature_fusion
from model_fusion import run_model_fusion

# ==========================================
# PAGE CONFIG & STYLES
# ==========================================
st.set_page_config(
    page_title="CityFusion - Data Science Pipeline",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Professional academic light theme overrides */
    h1, h2, h3, h4, p, span, div {
        color: #2b2b2b !important;
    }
    .stApp {
        background-color: #f8f9fa;
    }
    .metric-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 20px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        text-align: center;
    }
    .flow-box {
        background-color: #ffffff;
        padding: 12px;
        border-radius: 6px;
        text-align: center;
        font-weight: 600;
        border: 2px solid #3498db;
        color: #2c3e50 !important;
        margin-bottom: 5px;
    }
    .flow-arrow {
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        color: #7f8c8d !important;
        margin: 5px 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# HELPERS & DATA LOADING (NO AUTO-FETCH)
# ==========================================
RAW_DIR = Path("data/raw")
CITIES_FILE = "data/cities.csv"
RAW_FUSED_FILE = "data/raw_fused_dataset.csv"
CLEANED_FILE = "data/cleaned_dataset.csv"
FEATURE_FILE = "data/feature_fusion.csv"

@st.cache_data(show_spinner=False)
def get_existing_data():
    data = {
        "cities": pd.DataFrame(),
        "raw_fused": pd.DataFrame(),
        "cleaned": pd.DataFrame(),
        "features": pd.DataFrame()
    }
    try:
        if os.path.exists(CITIES_FILE): data["cities"] = pd.read_csv(CITIES_FILE)
        if os.path.exists(RAW_FUSED_FILE): data["raw_fused"] = pd.read_csv(RAW_FUSED_FILE)
        if os.path.exists(CLEANED_FILE): data["cleaned"] = pd.read_csv(CLEANED_FILE)
        if os.path.exists(FEATURE_FILE): data["features"] = pd.read_csv(FEATURE_FILE)
    except Exception as e:
        pass
    return data

def safely_get_json(filepath):
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.title("🌍 CityFusion Control")
st.sidebar.write("Manage the Data Science Pipeline.")

if st.sidebar.button("Run Full Pipeline", type="primary", use_container_width=True):
    progress_text = st.sidebar.empty()
    try:
        progress_text.info("API Collection & Raw Fusion...")
        df_fused = run_raw_data_fusion()
        
        progress_text.info("Data Cleaning & Feature Fusion...")
        df_features, stats = run_feature_fusion()
        
        progress_text.info("Model Training & Fusion...")
        metrics, predictions = run_model_fusion()
        
        st.session_state['stats'] = stats
        st.session_state['metrics'] = metrics
        st.session_state['predictions'] = predictions
        
        # Clear cache to reflect new exact files
        get_existing_data.clear()
        progress_text.success("Pipeline Complete!")
    except Exception as e:
        progress_text.error(f"Pipeline error: {str(e)}")

st.sidebar.divider()
st.sidebar.markdown("**API Status**")
st.sidebar.markdown("✓ Open-Meteo Weather\n✓ Open-Meteo Air Quality\n✓ REST Countries\n✓ World Bank\n✓ ExchangeRate-API")

# Load existing datasets for the UI
datasets = get_existing_data()
cities_df = datasets["cities"]
raw_fused_df = datasets["raw_fused"]
cleaned_df = datasets["cleaned"]
features_df = datasets["features"]

data_available = not (cities_df.empty or raw_fused_df.empty or cleaned_df.empty or features_df.empty)

if data_available:
    st.sidebar.success("Using previously collected API data. Click Run Full Pipeline to refresh live API data.")
else:
    st.sidebar.warning("Datasets missing. Please 'Run Full Pipeline' to begin.")

# ==========================================
# MAIN UI HEADER
# ==========================================
st.title("🌍 CityFusion")
st.subheader("Multi-Source Data Fusion & Machine Learning")

# ==========================================
# TABS NAVIGATION
# ==========================================
tabs = st.tabs([
    "1. Overview", 
    "2. 5 API Sources", 
    "3. Raw Data Fusion", 
    "4. Feature Fusion", 
    "5. Model Fusion", 
    "6. Analysis",
    "⬇️ Downloads"
])

# ----------------- TAB 1: OVERVIEW -----------------
with tabs[0]:
    st.markdown("##### CityFusion integrates data from five external APIs with a downloaded city dataset, performs raw data fusion and feature-level fusion, and applies multiple regression models followed by model fusion to predict PM2.5.")
    
    if data_available:
        # KPIs
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Cities Tracked", len(cities_df))
        c2.metric("API Sources", 5)
        c3.metric("Engineered Features", len(features_df.columns))
        c4.metric("Target Variable", "PM2.5")
        
        st.divider()
        st.markdown("### City Snapshot")
        selected_city = st.selectbox("Select a City:", cities_df['city'].tolist())
        
        city_metrics = cleaned_df[cleaned_df['city'] == selected_city]
        if not city_metrics.empty:
            row = city_metrics.iloc[0]
            mc1, mc2, mc3, mc4, mc5 = st.columns(5)
            mc1.metric("Temperature", f"{row.get('temperature', 'N/A')} °C")
            mc2.metric("PM2.5", f"{row.get('pm2_5', 'N/A')} µg/m³")
            mc3.metric("Population", f"{row.get('base_population', 'N/A'):,}")
            mc4.metric("GDP", f"${row.get('wb_gdp', 0):,.0f}" if row.get('wb_gdp') else "N/A")
            mc5.metric("Exchange Rate", f"{row.get('exchange_rate', 'N/A')}")
    else:
        st.info("No data available yet. Please run the pipeline.")

# ----------------- TAB 2: API SOURCES -----------------
with tabs[1]:
    st.header("5 Live API Sources")
    st.write("Dynamic data extraction from robust public architectures.")
    
    apis = [
        {"name": "Open-Meteo Weather", "purpose": "Temperature, humidity, precipitation, wind speed"},
        {"name": "Open-Meteo Air Quality", "purpose": "PM2.5, PM10, NO2, Ozone"},
        {"name": "REST Countries", "purpose": "Country, capital, population, currency, region"},
        {"name": "World Bank", "purpose": "Population, GDP, urban population"},
        {"name": "ExchangeRate API", "purpose": "Currency exchange rates (to USD)"}
    ]
    
    for api in apis:
        with st.container():
            st.markdown(f"#### {api['name']}")
            colA, colB = st.columns([3, 1])
            colA.write(f"**Purpose:** {api['purpose']}")
            colB.markdown("✅ **Data available**" if data_available else "⏳ **Awaiting Execution**")
            st.markdown("---")
            
    if data_available:
        st.subheader("Raw JSON Inspection")
        inspect_city = st.selectbox("Inspect JSON payload for:", cities_df['city'].tolist(), key="json_inspect")
        city_filename = inspect_city.replace(' ', '_') + "_raw.json"
        raw_json = safely_get_json(RAW_DIR / city_filename)
        
        if raw_json:
            jc1, jc2 = st.columns(2)
            with jc1:
                st.write("**Weather Context (Safe Extraction)**")
                # Safely get current OR first element of hourly if current is missing
                weather_data = raw_json.get("weather", {})
                w_current = weather_data.get("current", weather_data.get("hourly", {"Information": "Nested/Unavailable"}))
                st.json(w_current)
            with jc2:
                st.write("**Air Quality Context (Safe Extraction)**")
                aq_data = raw_json.get("air_quality", {})
                # Extract carefully to prevent KeyError 'current'
                aq_current = aq_data.get("current") 
                if not aq_current:
                    aq_current = aq_data.get("hourly", {"Information": "Nested/Unavailable"})
                st.json(aq_current)

# ----------------- TAB 3: RAW DATA FUSION -----------------
with tabs[2]:
    st.header("Raw Data Fusion")
    st.markdown("Raw Data Fusion combines heterogeneous records from the downloaded city dataset and the five API sources using common city/country identifiers.")
    
    col_vis, col_data = st.columns([1, 2])
    with col_vis:
        st.markdown("""
        <div class='flow-box'>Base Dataset</div>
        <div class='flow-box'>Weather API</div>
        <div class='flow-box'>Air Quality API</div>
        <div class='flow-box'>Countries API</div>
        <div class='flow-box'>World Bank API</div>
        <div class='flow-box'>ExchangeRate API</div>
        <div class='flow-arrow'>↓</div>
        <div class='flow-box' style='background:#e3f2fd;'>Raw Data Fusion</div>
        <div class='flow-arrow'>↓</div>
        <div class='flow-box' style='background:#e8f5e9;'>Unified Dataset</div>
        """, unsafe_allow_html=True)
    
    with col_data:
        if not raw_fused_df.empty:
            st.write(f"**Rows:** {raw_fused_df.shape[0]} | **Columns:** {raw_fused_df.shape[1]}")
            st.dataframe(raw_fused_df, height=400)
        else:
            st.info("Raw fused dataset not generated.")
            
    st.divider()
    st.header("Data Cleaning")
    st.markdown("Handles missing values (median/mode fillers), drops duplicates, and standardizes formats.")
    if not cleaned_df.empty:
        st.write(f"**Cleaned Dimensions:** {cleaned_df.shape[0]} Rows, {cleaned_df.shape[1]} Columns")
        st.dataframe(cleaned_df.head())
    else:
        st.info("Cleaned dataset not generated.")

# ----------------- TAB 4: FEATURE FUSION -----------------
with tabs[3]:
    st.header("Feature Fusion")
    st.write("Features from different sources are extracted, imputed, and combined into one robust analytical feature space. PM2.5 is deliberately preserved as our target variable and removed from training arrays internally.")
    
    c1, c2, c3 = st.columns(3)
    c1.markdown("**Weather Features**\n- temperature\n- humidity\n- precipitation\n- wind speed")
    c2.markdown("**Air Quality Features**\n- PM10\n- NO2\n- ozone")
    c3.markdown("**Economic Features**\n- GDP\n- population\n- urban percentage")
    
    if not features_df.empty:
        st.write(f"**Unified Feature Matrix:** {features_df.shape[0]} Rows | {features_df.shape[1]} Engineered Features")
        st.dataframe(features_df)
        
        st.subheader("Correlation Analysis")
        # Compute dynamic correlation strictly on numeric structures safely
        numeric_cleaned = cleaned_df.select_dtypes(include=['number'])
        if not numeric_cleaned.empty and len(numeric_cleaned.columns) > 1:
            try:
                corr_matrix = numeric_cleaned[['pm2_5', 'temperature', 'humidity', 'wind_speed', 'wb_gdp', 'base_population']].corr()
                fig_corr = px.imshow(corr_matrix, text_auto=".2f", aspect="auto", color_continuous_scale="Blues", title="Numeric Correlation Heatmap")
                st.plotly_chart(fig_corr, use_container_width=True)
            except Exception as e:
                st.warning("Correlation metrics unavailable or missing columns.")
    else:
        st.info("Feature fusion dataset not available.")

# ----------------- TAB 5: MODEL FUSION -----------------
with tabs[4]:
    st.header("Model Fusion")
    st.write("Three independent regressors algorithmically target PM2.5 concentrations, dynamically evaluated, and formally fused using structural weighted averaging.")
    
    if 'metrics' in st.session_state and 'predictions' in st.session_state:
        metrics = st.session_state['metrics']
        preds = st.session_state['predictions']
        
        st.markdown("### Model Evaluation (Actual Run Metrics)")
        # Create comparison table
        comp_data = []
        for model_name, m_stats in metrics.items():
            if model_name != "Fused Model":
                comp_data.append({"Model": model_name, "R²": round(m_stats["R²"], 4), "MSE": round(m_stats["MSE"], 4), "MAE": round(m_stats["MAE"], 4)})
        
        st.table(pd.DataFrame(comp_data))
        
        st.divider()
        st.markdown("### Ensemble Model Fusion Strategy")
        st.info("**Final Prediction = 0.30 × LR Prediction + 0.40 × RF Prediction + 0.30 × SVR Prediction**")
        
        cma, cmb = st.columns(2)
        cma.markdown("#### Fused Model Performance")
        cma.write(f"**R² (Explained Variance):** {metrics['Fused Model']['R²']:.4f}")
        cma.write(f"**Mean Squared Error:** {metrics['Fused Model']['MSE']:.4f}")
        cma.write(f"**Mean Absolute Error:** {metrics['Fused Model']['MAE']:.4f}")
        
        cmb.markdown("#### Target Validation Sample")
        cmb.dataframe(preds.head(8))
    else:
        st.info("Model training data is strictly preserved in memory. Click 'Run Full Pipeline' to generate evaluation metrics dynamically.")

# ----------------- TAB 6: ANALYSIS -----------------
with tabs[5]:
    st.header("Visual Analysis")
    st.write("Dynamic charts displaying real fused relationships from the cleaned dataset.")
    
    if not cleaned_df.empty:
        ca1, ca2 = st.columns(2)
        try:
            with ca1:
                if 'city' in cleaned_df and 'pm2_5' in cleaned_df:
                    f1 = px.bar(cleaned_df, x="city", y="pm2_5", color="pm2_5", title="1. PM2.5 by City (Target Variable)", color_continuous_scale="Reds")
                    st.plotly_chart(f1, use_container_width=True)
                
                if 'pm10' in cleaned_df and 'pm2_5' in cleaned_df:
                    f3 = px.scatter(cleaned_df, x="pm10", y="pm2_5", title="3. PM10 vs PM2.5 (High Correlation)", color="city")
                    st.plotly_chart(f3, use_container_width=True)
                    
                if 'base_population' in cleaned_df and 'pm2_5' in cleaned_df:
                    f5 = px.scatter(cleaned_df, x="base_population", y="pm2_5", title="5. Population vs PM2.5", size="base_population", color="city")
                    st.plotly_chart(f5, use_container_width=True)
                    
            with ca2:
                if 'temperature' in cleaned_df and 'pm2_5' in cleaned_df:
                    f2 = px.scatter(cleaned_df, x="temperature", y="pm2_5", title="2. Temperature vs PM2.5", color="city")
                    st.plotly_chart(f2, use_container_width=True)
                
                if 'wb_gdp' in cleaned_df and 'pm2_5' in cleaned_df:
                    f4 = px.scatter(cleaned_df, x="wb_gdp", y="pm2_5", title="4. GDP vs PM2.5 (Economic Factor)", color="city")
                    st.plotly_chart(f4, use_container_width=True)
                    
                if 'metrics' in st.session_state:
                    rf_r2 = st.session_state['metrics']['Random Forest']['R²']
                    lr_r2 = st.session_state['metrics']['Linear Regression']['R²']
                    svr_r2 = st.session_state['metrics']['SVR']['R²']
                    f6 = px.bar(x=["Random Forest", "Linear Regression", "SVR"], y=[rf_r2, lr_r2, svr_r2], title="6. R² Model Performance Comparison", labels={"x": "Model", "y":"R² Score"}, color=["Random Forest", "Linear Regression", "SVR"])
                    st.plotly_chart(f6, use_container_width=True)
        except Exception as e:
            st.error(f"Visualization error (missing columns from APIs): {e}")
    else:
        st.info("Cleaned dataset required for visualizations.")

# ----------------- TAB 7: DOWNLOADS -----------------
with tabs[6]:
    st.header("Project Dataset Downloads")
    st.write("Export generated components directly for your project submission.")
    
    def get_csv(df):
        return df.to_csv(index=False).encode('utf-8')
    
    if not cities_df.empty:
        st.download_button("Download Base Dataset (cities.csv)", get_csv(cities_df), "cities.csv", "text/csv")
    if not raw_fused_df.empty:
        st.download_button("Download Raw Fused Data (raw_fused_dataset.csv)", get_csv(raw_fused_df), "raw_fused_dataset.csv", "text/csv")
    if not cleaned_df.empty:
        st.download_button("Download Cleaned Data (cleaned_dataset.csv)", get_csv(cleaned_df), "cleaned_dataset.csv", "text/csv")
    if not features_df.empty:
        st.download_button("Download Feature Matrix (feature_fusion.csv)", get_csv(features_df), "feature_fusion.csv", "text/csv")
    
    if 'predictions' in st.session_state:
        st.download_button("Download Model Predictions", get_csv(st.session_state['predictions']), "predictions.csv", "text/csv")
