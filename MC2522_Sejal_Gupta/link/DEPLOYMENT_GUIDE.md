# 🚀 Deployment Guide: Vercel & Streamlit Community Cloud

This guide explains how to deploy the **Web Portal on Vercel** (`https://vercel.com/sejal-gupta`) and the **Streamlit Applications on Streamlit Cloud** (`share.streamlit.io`), exactly as required for MCA academic submissions.

---

## ⚡ Option A: Hosting the Web Portal on Vercel (2 Minutes)

Vercel is optimized for frontend web applications, static portals, and HTML landing hubs.

### Steps to Deploy on Vercel:
1. Log in to your Vercel account: [https://vercel.com/sejal-gupta](https://vercel.com/sejal-gupta)
2. Click **"Add New..."** ➔ **"Project"**.
3. Import your GitHub repository (`MCA-Student-Applications-2025-2026`).
4. In the Project Configuration:
   - **Root Directory**: Select `MC2522_Sejal_Gupta/link`
   - **Framework Preset**: `Other`
   - Click **Deploy**!
5. Within 15 seconds, Vercel will assign a public domain like `https://sejal-gupta-ai-moderator.vercel.app`!
6. This portal has one-click buttons that directly open the core project and all 3 analytical dashboards.

---

## 🎈 Option B: Hosting Streamlit Apps on Streamlit Community Cloud (Free)

Python Streamlit applications require persistent WebSocket connections, which are natively supported on **Streamlit Community Cloud** (just like your classmate Dimpal Tamta did at `https://nutricare-ai-llm.streamlit.app/`).

### Steps to Deploy Each App:
1. Go to [https://share.streamlit.io/](https://share.streamlit.io/) and click **"Continue with GitHub"**.
2. Click **"Create app"** ➔ **"I already have an app"**.
3. Configure the fields:

#### 1. Core Project App:
- **Repository:** `MCA-Class-2025/MCA-Student-Applications-2025-2026`
- **Branch:** `main`
- **Main file path:** `MC2522_Sejal_Gupta/src/app.py`
- **App URL:** `sejal-gupta-ai-moderator.streamlit.app`
- Click **Deploy**!

#### 2. Fused Dataset Dashboard:
- **Repository:** `MCA-Class-2025/MCA-Student-Applications-2025-2026`
- **Branch:** `main`
- **Main file path:** `MC2522_Sejal_Gupta/dashboards/Fused_Dataset_Dashboard/Social_Media_Fused_Dataset_Analytics/app.py`
- **App URL:** `social-media-fused-analytics-mc2522.streamlit.app`
- Click **Deploy**!

#### 3. Spatial Data Dashboard:
- **Main file path:** `MC2522_Sejal_Gupta/dashboards/Spatial_Data_Dashboard/NOAA_Marine_Microplastics_Spatial_Analytics/app.py`
- **App URL:** `noaa-marine-spatial-mc2522.streamlit.app`
- Click **Deploy**!

#### 4. Temporal Data Dashboard:
- **Main file path:** `MC2522_Sejal_Gupta/dashboards/Temporal_Data_Dashboard/Historical_Temporal_Dataset_Commodity_Dashboard/app.py`
- **App URL:** `commodity-temporal-mc2522.streamlit.app`
- Click **Deploy**!

---

## 🔒 Secrets / API Keys in Streamlit Cloud (Settings ➔ Secrets)
If your app needs `HF_TOKEN` or `GEMINI_API_KEY`:
In your app's dashboard on Streamlit Cloud, go to **Settings** ➔ **Secrets** and paste:
```toml
HF_TOKEN = "your_huggingface_token"
GEMINI_API_KEY = "your_gemini_key"
```
