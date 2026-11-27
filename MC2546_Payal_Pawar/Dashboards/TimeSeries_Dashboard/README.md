# RetailPulse · Time-Series Dashboard (Plotly Dash)

Dynamic dashboard for **temporal / time-series** analysis: trend, rolling mean, anomaly detection, YoY comparison,
weekday×month heatmap, decomposition, category mix, 60-day forecast and autocorrelation.

## Structure
| File | Purpose |
|---|---|
| `data_prep.py` | generates the synthetic daily dataset -> `data.xlsx` |
| `eda.py` | console exploratory analysis |
| `dashboard.py` | the Dash app (filters: date range, store, category, metric, frequency, reset) |
| `export_figures.py` | saves all charts as PNG in `figures/` |
| `assets/style.css` | styling (auto-loaded by Dash) |

## Run (VS Code terminal)
```
python -m venv venv
venv\Scripts\activate        # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python data_prep.py          # creates data.xlsx (optional – dashboard auto-creates it)
python dashboard.py          # open http://127.0.0.1:8050
```
To use your own data keep columns: `date, store, category, revenue, orders` (+ optional others).
