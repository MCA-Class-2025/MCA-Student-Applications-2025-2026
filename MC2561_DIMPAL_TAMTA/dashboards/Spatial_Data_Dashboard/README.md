<h1 align="center">🌊 NOAA Marine Microplastics Spatial Intelligence &amp; Analytics</h1>

<p align="center">
  An interactive 8-page Streamlit dashboard that shows <b>where microplastics have been sampled in the world's oceans</b>,
  <b>how much was found</b>, and <b>where the real hotspots are</b>.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Streamlit-dashboard-ff4b4b" alt="Streamlit">
  <img src="https://img.shields.io/badge/Plotly-interactive%20charts-3f4f75" alt="Plotly">
  <img src="https://img.shields.io/badge/Data-NOAA%20NCEI-0b5394" alt="NOAA NCEI data">
</p>



---

## Contents

- [About Project](#what-is-this-project)
- [Highlights](#highlights)
- [Pages, one by one](#pages-one-by-one)
- [Quick start](#quick-start)
- [How the data is handled](#how-the-data-is-handled)
- [Spatial statistics used](#spatial-statistics-used)
- [Themes and chart background](#themes-and-chart-background)
- [Project structure](#project-structure)
- [Known limitations](#known-limitations)
- [Data source](#data-source)

---

## About Project

The NOAA National Centers for Environmental Information (NCEI) publish a worldwide database of
microplastic observations: **29,075 sampling records** collected between 1972 and 2026 using nets,
pumps, grab samples and beach surveys.

This dashboard turns that raw table into a clear story that anyone can follow:

1. **Where** were samples taken? (geography and sampling effort)
2. **How much** plastic was found? (concentration, always one unit at a time)
3. **Where is it unusually high?** (hotspots and spatial statistics)
4. **What can I download?** (data explorer, CSV export, automatic PDF report)

Every page starts with a short *"In simple words"* box, so the charts are easy to present and explain.

## Highlights

- **8 linked pages** with one shared filter bar (ocean, country, region, date, concentration class).
- **Click-to-filter maps** – click a country on the map and the whole dashboard follows.
- **Flat map or 3D globe** on the overview page.
- **One colour per ocean everywhere**, so the same ocean always looks the same on every chart.
- **Units are never mixed** – `pieces/m3`, `pieces/10 mins` and `pieces kg-1 d.w.` are analysed separately.
- **Real spatial statistics** – Moran's I, LISA, Getis-Ord Gi\*, DBSCAN, KDE, Clark-Evans, standard deviational ellipse.
- **8 colour themes** plus a *white chart background* option.
- **One-click PDF report** with the key findings and charts you choose.

---

## Pages, one by one

### 1 · Executive Overview

<!-- IMAGE 1 (MAIN IMAGE): full screenshot of page 1 "Executive Overview". Save as images/01_overview.png -->
<p align="center">
  <img src="images/1.png" alt="Executive Overview page" width="100%">
  <img src="images/2.png" alt="Executive Overview page" width="100%">
  <img src="images/3.png" alt="Executive Overview page" width="100%">
  <img src="images/4.png" alt="Executive Overview page" width="100%">
</p>

<p align="center"><i>Page 1 – Executive Overview: KPIs, global sampling map, ocean share, top countries, treemap and trends in one screen.</i></p>

The one-page summary of the whole study. It answers *"what is in this dataset?"* in about ten seconds.

| Visual | What it tells you |
|---|---|
| **KPI tiles** | Number of samples, countries surveyed, oceans covered, and the ocean with the highest sampling coverage |
| **Global sampling map** | Every dot is one sample, coloured by ocean. Switch between *Flat map* and *Globe*. Click a country to filter the dashboard |
| **Share of samples by ocean** | How the records split between the five oceans |
| **Top 8 countries** | Countries with the most sampling records |
| **Where samples come from** | Treemap: ocean → country, bigger tile = more records |
| **How contaminated are the samples?** | Share of records in each concentration class, from Very Low to Very High |
| **Sampling over time** | Records collected each year, one line per ocean |
| **Plastic found vs latitude** | Each dot is one measurement (log scale), coloured by ocean |
| **Sampling timeline heat map** | Records per ocean and decade |

### 2 · Geographic Distribution

<!-- IMAGE 3: full screenshot of page 2. Save as images/02_geography.png -->
<p align="center">
  <img src="images/55.png" alt="Geographic Distribution page" width="100%">
  <img src="images/6.png" alt="Geographic Distribution page" width="100%">
  <img src="images/7.png" alt="Geographic Distribution page" width="100%">
</p>

Shows **where** the samples were taken.

- **Sampling point map** – every record, coloured by ocean.
- **Country explorer map** – pick a country (and optionally an ocean) to zoom in; dots are coloured by marine setting (beach, water, sediment…).
- **Sampling density grid** – number of records per grid square.
- **3D sampling-density surface** – height = samples per 10° block (drag to rotate).
- **Latitude distribution** – how samples spread north to south.
- **Sampling reach arc map** – arcs link the busiest country to the next 14.

### 3 · Regional Analysis

<!-- IMAGE 4: full screenshot of page 3. Save as images/03_regional.png -->
<p align="center">
  <img src="images/8.png" alt="Regional Analysis page" width="100%">
  <img src="images/9.png" alt="Geographic Distribution page" width="100%">
</p>

Compares oceans, countries and regions: *who has the most samples and how contaminated does each region look?*

- **Country map** and **country ranking** (top 15).
- **Samples per ocean** and **regions inside each ocean** (ocean → region treemap).
- **Amount of plastic by region** and **contamination levels by region** (choose one measurement unit for both).

### 4 · Concentration Analysis

<!-- IMAGE 5: full screenshot of page 4. Save as images/04_concentration.png -->
<p align="center">
  <img src="images/10.png" alt="Concentration Analysis page" width="100%">
</p>

Shows **how much** plastic was actually found. A few places have extremely high counts, so values are shown on a
**log scale** – each step is 10× more plastic.

- Distribution of concentration values and the five **contamination classes**.
- **Plastic by marine setting** (box plot) and **median by sampling method**.
- **Concentration map** of average values per area.
- Choose the unit (`pieces/m3`, `pieces/10 mins`, `pieces kg-1 d.w.`) at the top; each unit is analysed on its own.

### 5 · Spatial Density &amp; Hotspots

<!-- IMAGE 6: full screenshot of page 5. Save as images/05_hotspots.png -->
<p align="center">
  <img src="images/hs.png" alt="Spatial Density and Hotspots page" width="100%">
</p>

Finds places that stand out. It keeps two ideas **separate**:

- **Sampling effort** (where scientists looked): density (KDE) map and DBSCAN clusters.
- **Contamination** (what they found): potential hotspot map and statistically supported hotspots / coldspots (Getis-Ord Gi\*).

Use the sliders (smoothing distance, cluster radius, minimum samples, hotspot threshold) to make the search stricter or looser.
Many records in one place do **not** automatically make it a pollution hotspot.

### 6 · Spatial Statistics

Tests whether high or low values sit next to each other more than chance would predict.

| Tab | Question it answers |
|---|---|
| **Global Moran's I** | Is there clustering overall? (result table + Moran scatter plot) |
| **LISA** | *Where* are the local high/low clusters? |
| **Getis-Ord Gi\*** | Which areas are significant hotspots or coldspots (FDR-adjusted)? |
| **Nearest neighbour** | Are sampling locations clustered or random? (Clark-Evans) |
| **Std. deviational ellipse** | Where is the centre and main direction of the samples? |

### 7 · Data Explorer &amp; Export

<!-- IMAGE 8: full screenshot of page 7. Save as images/07_explorer.png -->


The raw records behind every chart. Tabs: **Table**, **Record detail**, **Map & charts**, **Downloads** and **Dataset information**.
Search and filter the data, inspect a single sample, and download the filtered records.

### 8 · Insights &amp; PDF Report

<!-- IMAGE 9: full screenshot of page 8 (the written findings + PDF panel). Save as images/08_insights.png -->
<p align="center">
  <img src="images/11" alt="Insights and PDF Report page" width="100%">
</p>

Automatically written findings (executive summary, geographic, regional, concentration, spatial, statistical and
data-quality findings) based on the current filters. Choose the charts you want, press **Generate PDF Report**, then **Download PDF**.

<!-- IMAGE 10 (optional): first page of a generated PDF report. Save as images/08b_pdf_report.png -->
<p align="center">
  <img src="images/11.png" alt="Example page from the generated PDF report" width="100%">
</p>

---

## Quick start

```bash
# 1. get the code
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

# 2. create a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. install the requirements
pip install -r requirements.txt

# 4. start the dashboard
streamlit run app.py
```

Streamlit opens the dashboard in your browser (normally <http://localhost:8501>).
The data file is already included in `data/raw/`, so no extra download is needed.

## How the data is handled

- The raw CSV in `data/raw/` is **never modified**; cleaning creates a separate copy.
- All 29,075 records have valid coordinates.
- Many records have no country (about 45 % after detection from coordinates), some have no ocean, and many have no region.
  They are shown as **"Not recorded"**, left out only of the charts that need that field, and **never guessed**.
- **Detected countries:** records without a country are matched to a country from their coordinates (on land or within
  about 45 km of the coast). The lookup lives in `data/processed/inferred_country.csv`. Open-sea points stay "Not recorded".
  To rebuild it: `pip install "geopandas<1.0"` then `python scripts/infer_countries.py`.
- **Three units are never mixed:** `pieces/m3`, `pieces kg-1 d.w.` and `pieces/10 mins` (Nurdle Patrol).
- 488 records are exact duplicates apart from their IDs; they are **flagged, not deleted**.
- **Sampling effort** (record counts, KDE of locations, DBSCAN) is analysed separately from **contamination** (Gi\*, LISA).

## Spatial statistics used

Implemented with NumPy, SciPy and scikit-learn:

- Global **Moran's I** (permutation test) and **Local Moran / LISA**
- **Getis-Ord Gi\*** with Benjamini-Hochberg false-discovery-rate correction
- **Clark-Evans** nearest-neighbour index
- **Standard deviational ellipse**
- **Kernel density estimation** and **DBSCAN** clustering

Spatial weights are k-nearest-neighbours on great-circle distance, because a single projected map would distort a
worldwide study area. Analyses are skipped with a message when there are fewer than 30 grid cells.

## Themes and chart background

<!-- IMAGE 11 (optional): open the "🎨 Theme" popup in the header and screenshot it. Save as images/09_themes.png -->
<p align="center">
  <img src="images/13.png" alt="Theme gallery" width="100%">
</p>

- Choose from **8 colour themes** (header → 🎨 **Theme**). The choice is saved in `data/processed/prefs.json`.
- The header switch **White chart background** keeps the panels behind charts and maps white while the page colours follow the theme.
- Filters stay active when you move between pages.

## Project structure

```text
.
├── app.py                      # entry point
├── requirements.txt
├── config/                     # settings, colour themes, theme manager
├── modules/                    # data loading/cleaning, calculations, spatial analysis,
│                               # charts, maps, insights, PDF report, export
├── pages/                      # the 8 dashboard pages
├── scripts/infer_countries.py  # optional: rebuild the detected-country lookup
├── data/
│   ├── raw/                    # original NOAA CSV (never modified)
│   └── processed/              # country lookup files
├── images/                # screenshots used in this README
└── exports/                    # generated PDF reports
```

## Known limitations

- Clicks on the treemap and donut charts are not exposed by Streamlit. Cross-filtering works from the **map**
  (country / point click), the region bar chart and the filter bar.
- Country shading uses Plotly's built-in country names; a name Plotly does not know is simply not shaded.
- The PDF uses static Matplotlib charts (coordinate plot, no basemap). Exporting Plotly charts as PNG needs `kaleido`.
- Results describe **sampled locations only**. Method, mesh size and survey year differ between studies, so
  differences between places are not proof of pollution differences.

## Data source

Microplastics observations from the **NOAA National Centers for Environmental Information (NCEI)** Marine Microplastics
database: <https://www.ncei.noaa.gov/products/microplastics>.
