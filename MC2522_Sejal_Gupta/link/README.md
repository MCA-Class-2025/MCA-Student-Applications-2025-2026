# 🌐 Project & Dashboards Direct Access Links

This directory contains direct access links to the **AI Social Media Content Moderator** and all **3 Analytical Dashboards**, along with the Vercel web portal launcher.

---

## 🚀 Live Cloud Deployment Links

| Resource | Type | Live Cloud URL (Streamlit Cloud) | Local Dev URL |
|---|---|---|---|
| 🛡️ **AI Social Media Moderator** | Core Application | [Open Application](https://sejal-gupta-ai-moderator.streamlit.app) | `http://localhost:8501` |
| 📊 **Fused Dataset Dashboard** | Analytical Dashboard | [Open Dashboard](https://social-media-fused-analytics-mc2522.streamlit.app) | `http://localhost:8501` |
| 🌊 **Spatial Data Dashboard (Microplastics)** | Spatial Intelligence | [Open Dashboard](https://noaa-marine-spatial-mc2522.streamlit.app) | `http://localhost:8502` |
| 📈 **Temporal Data Dashboard (Commodities)** | Time-Series Analytics | [Open Dashboard](https://commodity-temporal-mc2522.streamlit.app) | `http://localhost:8503` |
| ⚡ **Vercel Web Portal Launcher** | Vercel Deployment | [Open Vercel Portal](https://sejal-gupta-ai-moderator.vercel.app) | `link/index.html` |

> **Vercel Account:** [https://vercel.com/sejal-gupta](https://vercel.com/sejal-gupta)

---

## 📁 Files in this Directory

- **`index.html`**: Interactive Web Portal Launcher (styled with modern UI & buttons) ready for 1-click hosting on Vercel.
- **`vercel.json`**: Deployment routing configuration for Vercel.
- **`1_AI_Social_Media_Moderator.url`**: Windows internet shortcut to launch the core moderation app.
- **`2_Fused_Dataset_Dashboard.url`**: Windows internet shortcut to launch the Fused Dataset Analytics Dashboard.
- **`3_Spatial_Data_Dashboard.url`**: Windows internet shortcut to launch the Spatial Data Dashboard.
- **`4_Temporal_Data_Dashboard.url`**: Windows internet shortcut to launch the Temporal Data Dashboard.
- **`5_Vercel_Account_Profile.url`**: Shortcut to Sejal Gupta's Vercel account.
- **`DEPLOYMENT_GUIDE.md`**: Step-by-step hosting guide for Vercel and Streamlit Community Cloud.

---

## 💡 Quick Launch via Local Terminal

```powershell
# 1. Main Project App
cd ../src
streamlit run app.py

# 2. Fused Dataset Dashboard
cd ../dashboards/Fused_Dataset_Dashboard/Social_Media_Fused_Dataset_Analytics
streamlit run app.py

# 3. Spatial Data Dashboard
cd ../dashboards/Spatial_Data_Dashboard/NOAA_Marine_Microplastics_Spatial_Analytics
streamlit run app.py --server.port 8502

# 4. Temporal Data Dashboard
cd ../dashboards/Temporal_Data_Dashboard/Historical_Temporal_Dataset_Commodity_Dashboard
streamlit run app.py --server.port 8503
```
