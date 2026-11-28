# 🛡️ Social Media Fused Dataset Analytics Dashboard

<p align="center">
  An interactive 5-page Streamlit analytics dashboard providing deep statistical, NLP, vision, and LLM insights into the multimodal fused social media content moderation dataset.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Streamlit-Dashboard-ff4b4b" alt="Streamlit">
  <img src="https://img.shields.io/badge/Plotly-Interactive%20Charts-3f4f75" alt="Plotly">
  <img src="https://img.shields.io/badge/Data-API%20Fused%20Dataset-2e7d32" alt="API Fused Dataset">
</p>

---

## 📌 Contents

- [About Project](#about-project)
- [Key Highlights](#key-highlights)
- [Pages Overview](#pages-overview)
- [Quick Start](#quick-start)
- [Dataset Specifications](#dataset-specifications)
- [Project Structure](#project-structure)

---

## 📖 About Project

The **Social Media Fused Dataset Analytics Dashboard** combines multiple moderation signals into an intuitive, interactive analytical experience:
1. **Benchmark Toxicity Annotations**: Severe toxicity, obscenity, threats, insults, and identity hate.
2. **Hugging Face NLP Signals**: Transformer sentiment polarity and confidence scores.
3. **Google Vision API SafeSearch**: Image safety scores across adult, violence, racy, medical, and spoof dimensions.
4. **Gemini LLM Decisions**: Fine-grained categorization, risk assessment, and contextual explanations.

---

## ✨ Key Highlights

- **5 Interactive Pages**: Comprehensive analysis covering Toxicity, Sentiment, Multimodal Vision, LLM Decisions, and full Dataset Explorer.
- **Global Filter Bar**: Dynamically filter by comment language, Gemini risk level, moderation decision, and toxicity status.
- **Sample Inspector**: Deep-dive into individual comments to trace OCR text, translations, and LLM reasoning.
- **Export Capabilities**: Search, slice, and download custom subsets in CSV format.

---

## 📑 Pages Overview

### 1 · Main Overview Dashboard
- High-level KPI metrics (Total records, toxic comments %, clean samples, high-risk flags).
- Toxicity breakdown donut and Gemini LLM risk assessment.
- Subcategory toxicity bar charts and sentiment vs toxicity confidence scatter plot.
- Google Vision SafeSearch distribution.

### 2 · Toxicity Subcategory Analysis
- Correlation matrix across severe toxic, obscene, threat, insult, and identity hate flags.
- Co-occurrence distribution (multi-flag toxicity per comment).
- Model confidence comparison between toxic and clean benchmarks.

### 3 · Sentiment & Emotion Dynamics
- Sentiment polarity breakdown (Positive, Negative, Neutral).
- Sentiment score histograms comparing toxic vs clean content.
- Multilingual distribution cross-tabulated with sentiment scores.

### 4 · Multimodal Visual Safety & OCR
- SafeSearch likelihood distribution across adult, violence, racy, medical, and spoof checks.
- Risk matrix cross-tabulating adult likelihood against violence likelihood.

### 5 · LLM Gemini Decisions & Explanations
- Hierarchical sunburst chart: Decision ➔ Risk Level ➔ Category.
- Cross-tabulation of Gemini LLM decisions against baseline benchmark labels.

### 6 · Dataset Explorer & Statistics
- Searchable data table with instant text filtering.
- Full descriptive statistics and data integrity checks.
- CSV download button for filtered results.

---

## 🚀 Quick Start

```bash
# 1. Navigate to the dashboard directory
cd dashboards/Fused_Dataset_Dashboard/Social_Media_Fused_Dataset_Analytics

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch Streamlit
streamlit run app.py
```

The application will be accessible in your browser at `http://localhost:8501`.

---

## 🗂️ Project Structure

```text
Social_Media_Fused_Dataset_Analytics/
├── app.py                      # Main dashboard entrypoint
├── requirements.txt            # Python dependencies
├── README.md                   # Dashboard documentation
├── data/
│   └── Final_fused_dataset.csv # Multimodal fused dataset
├── modules/
│   ├── charts.py               # Plotly interactive chart routines
│   ├── data.py                 # Dataset loader and caching
│   └── ui.py                   # Custom CSS styling and UI metrics
└── pages/
    ├── 1_Toxicity_Analysis.py
    ├── 2_Sentiment_and_Emotions.py
    ├── 3_Vision_and_Multimodal_Safety.py
    ├── 4_LLM_Gemini_Decisions.py
    └── 5_Dataset_Explorer_and_Statistics.py
```
