# BreatheIndia · Geo-Spatial Dashboard (Plotly Dash)

Dynamic dashboard for **geo-spatial** analysis: interactive bubble map, density heat-map, city rankings, sunburst
hierarchy (region → state → city), drivers scatter, regional box-plots, animated month-by-month map and a
click-to-drill city profile.

## Structure
| File | Purpose |
|---|---|
| `data_prep.py` | generates synthetic monthly air-quality data for 36 Indian cities -> `data.xlsx` |
| `eda.py` | console exploratory analysis |
| `dashboard.py` | the Dash app (filters: date range, region, state, AQI category, metric, map mode, reset) |
| `export_figures.py` | saves charts as PNG in `figures/` |
| `assets/style.css` | styling (auto-loaded) |

## Run (VS Code terminal)
```
python -m venv venv
venv\Scripts\activate        # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python data_prep.py          # optional – dashboard auto-creates data.xlsx
python dashboard.py          # open http://127.0.0.1:8050
```
Map tiles (carto-positron) need internet. Own data needs columns:
`city, state, region, lat, lon, date, population_m, pm25, aqi, temp_c, humidity, green_cover_pct, vehicles_per_1000, aqi_category`.
