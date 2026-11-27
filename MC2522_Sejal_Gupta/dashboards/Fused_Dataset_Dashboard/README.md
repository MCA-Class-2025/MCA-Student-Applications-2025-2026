# 📊 Social Media Fused Dataset Dashboard

This directory houses the interactive multi-page analytics dashboard for the multimodal fused social media toxicity dataset.

## 📁 Directory Contents

- **`Social_Media_Fused_Dataset_Analytics/`**: The complete Streamlit dashboard application powered by Plotly and Pandas.
  - `app.py`: Overview KPIs, toxicity breakdown, and sample inspector.
  - `pages/`: 5 modular pages covering subcategory toxicity, sentiment, vision safety, LLM decisions, and full data explorer.
  - `data/`: Bundled `Final_fused_dataset.csv`.
  - `modules/`: Charting, caching, filtering, and custom CSS UI components.
  - `requirements.txt`: Package dependencies for running the dashboard.

## 🚀 Running the Dashboard

```bash
cd Social_Media_Fused_Dataset_Analytics
pip install -r requirements.txt
streamlit run app.py
```
