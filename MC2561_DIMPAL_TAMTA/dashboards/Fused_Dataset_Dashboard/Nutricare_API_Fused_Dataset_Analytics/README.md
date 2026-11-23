# API Fused Dataset Analytics – Food, Nutrition & Production Dashboard (main page)

Streamlit dashboard for `data/API_Fusion_Dataset.csv` (8,779 foods x 24 columns: nutrition, Nutri-Score, NOVA,
global and Indian production, cancer classification, assumptions). Everything is calculated from the file; no data is invented.

## Pages (top navigation bar, no sidebar)
| Page | What it covers |
|---|---|
| **1 Main Dashboard** | 4 KPI cards · selected food profile (photo from `Image URL`, Hindi/Marathi names, nutrients, Nutri-Score, NOVA, cancer classification) · Nutri-Score donut · NOVA treemap · top producing countries / Indian states (names on the bars) · World/India map that zooms to the selected food's top-3 producers with names shown · selectable nutrient chart · Calories vs Protein scatter · cancer stacked chart · global and Indian production · full Dataset Explorer (search, sort, CSV/Excel) |
| **2 Nutrition** | Macronutrient and micronutrient comparison · scatter with food comparison · nutrient statistics · searchable table |
| **3 Food Quality** | Nutri-Score pie · NOVA treemap · Nutri-Score vs NOVA heatmap · counts/percentage tables |
| **4 Cancer Classification** | Risk classification distribution · support category donut · nutrition across classifications · category-wise food list |
| **5 Production & Maps** | World and India maps (selected food, or food counts per place) · top countries/states · global vs Indian production · India's share · production table |
| **6 Statistics & Data** | Correlation heatmap · z-score box plot · missing values · descriptive stats · summary · full table · duplicates · outliers · validation · export |

A horizontal filter bar (Food/Hindi/Marathi name, Nutri-Score, NOVA, cancer risk, support category, country, state; Apply / Clear), the **8 colour themes**, a data-quality Info panel and a CSV download button work on every page.

## Behaviour notes
* `Cancer_Risk_Classification` has ~1,400 distinct text values, so charts group it by the prefix before " - "
  (Risk factor / Protective / Neutral / Limit or avoid). The full text is shown in the food profile and the tables.
* Maps colour the top-3 producers of the selected food (Rank 1-3); the Production page colours every country/state by number of foods.
  'Unknown' and 'Not produced in India' are left off the maps.
* Missing nutrient values stay blank (never 0). Duplicates are reported, not removed.
* The bundled `data/india_states.geojson` is a simplified older boundary file without Telangana (drawn inside Andhra Pradesh).
* Food photos load in the browser from the `Image URL` column; a placeholder is shown if a link is missing or broken.
* The box plot uses z-scores so nutrients with different units share one axis; the micronutrient chart uses a log axis.

## Run on Windows
```bat
cd API_Fused_Dataset_Analytics
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Structure
```
app.py                          main dashboard
pages/1_Nutrition_Analysis.py
pages/2_Food_Quality_Processing.py
pages/3_Cancer_Classification.py
pages/4_Production_Geographic.py
pages/5_Statistics_Data_Explorer.py
modules/theme.py                8 colour themes
modules/data.py                 loading, parsing, filtering, CSV/Excel export
modules/stats.py                descriptive statistics, missing values, duplicates, quality report
modules/images.py               food photo from Image URL + placeholder
modules/charts.py               main-dashboard charts and both maps
modules/pagecharts.py           charts for the supporting pages
modules/shell.py                header, theme, navigation, global filters
modules/ui.py                   CSS and HTML snippets
data/API_Fusion_Dataset.csv     the fused dataset
data/india_states.geojson       India state boundaries
.streamlit/config.toml          hides default sidebar navigation
```
