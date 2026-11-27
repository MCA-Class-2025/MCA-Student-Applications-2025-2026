# NOAA Marine Microplastics – Spatial Intelligence & Analytics

Eight-page Streamlit application for exploring the NOAA NCEI Marine Microplastics dataset
(29,075 point observations, 36 raw columns): sampling geography, regional and concentration
patterns, hotspots, spatial statistics, a data explorer and an automatic PDF report.

## Run
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Pages
1 Executive Overview · 2 Geographic Distribution · 3 Regional Analysis · 4 Concentration Analysis ·
5 Spatial Density & Hotspots · 6 Spatial Statistics · 7 Data Explorer & Export · 8 Insights & PDF Report

Eight themes (header → 🎨 Theme). The choice is saved in `data/processed/prefs.json`.
Filters are kept in the session when you move between pages.

## Data handling (decided from the real CSV)
* The raw CSV in `data/raw/` is never modified; cleaning produces a separate dataframe.
* 29,075 records, all with valid coordinates. ~59.8 % have no Country, ~4.8 % no Ocean, ~54 % no Region:
  these are shown as "Not recorded", excluded only from charts that need the field, and never guessed.
* Three units exist and are **never mixed**: `pieces/m3`, `pieces kg-1 d.w.` and `pieces/10 mins`
  (Nurdle Patrol; its value is taken from *Standardized Nurdle Amount*). Every statistic is per unit.
* 488 records are exact duplicates apart from IDs; they are flagged, not deleted.
* Sampling effort (record counts, KDE of locations, DBSCAN) is analysed separately from contamination
  (Gi*, LISA, weighted KDE).

## Spatial statistics
Implemented with NumPy/SciPy/scikit-learn: Global Moran's I (permutation), Local Moran / LISA,
Getis-Ord Gi* (Benjamini-Hochberg FDR), Clark-Evans nearest neighbour, standard deviational ellipse.
Weights are k-nearest-neighbour on great-circle distance (a single projected CRS would distort a
worldwide study area); a local Lambert azimuthal equal-area projection is used for areas and the ellipse.
Analyses are skipped with a message below 30 grid cells.

## Known limitations
* Treemap and donut clicks are not exposed by Streamlit; cross-filtering works from the map
  (country / point click) and the region bar chart, plus the filter bar.
* Country shading matches Plotly's built-in country names; unmatched names are simply not shaded.
* The PDF uses static Matplotlib charts (coordinate plot, no basemap). PNG export of Plotly charts needs `kaleido`.
* Results describe sampled locations only; method, mesh size and survey era differ between studies.

## Structure
`app.py` · `config/` (settings, theme, theme_manager) · `modules/` (data, calculations, spatial, charts, maps,
insights, report, export) · `pages/` (8 pages) · `data/` · `exports/`

## Detected countries
Records with no country are matched to a country from their coordinates (on land or within ~45 km of the coast).
The lookup is stored in `data/processed/inferred_country.csv`; rebuild it with `pip install "geopandas<1.0"` and
`python scripts/infer_countries.py`. Hover text marks these records as "detected from coordinates".
Open-sea points stay "Not recorded".

## Chart background option
The header toggle **White chart background** keeps the panels behind charts/maps white while the page colours follow the theme.
