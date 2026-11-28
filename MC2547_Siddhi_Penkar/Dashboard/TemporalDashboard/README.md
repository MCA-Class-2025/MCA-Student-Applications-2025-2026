# Temporal Analytics Dashboard

An interactive Python dashboard for time-series analysis of Melbourne daily minimum temperature and monthly airline passenger counts.

## Objective
To identify trends, seasonality, volatility and anomalies in time-based data.

## Datasets
- `Dataset/melbourne_daily_min_temperature.csv`: daily minimum temperature, 1981-1990 (3,650 records)
- `Dataset/airline_passengers.csv`: monthly international airline passengers (thousands), 1949-1960 (144 records)

## Data Preparation
- Dates were parsed, values converted to numeric, and missing values and duplicates removed.
- Derived temporal features: year, month, day of year, season (southern hemisphere), 30-day rolling mean and volatility, year-over-year growth, 12-month trend.
- Anomaly detection: a day is flagged when it deviates more than 3 standard deviations from its 30-day rolling mean.

## Project Structure
```
Temporal_Dashboard/
  temporal_dashboard.py     # main script
  dashkit.py                # shared layout and theme helper
  requirements.txt
  Dataset/
    melbourne_daily_min_temperature.csv
    airline_passengers.csv
  Dashboard/
    temporal_dashboard.html   # generated output
```

## How to Run (VS Code)
1. Open the terminal (Ctrl + `).
2. Install the libraries:
   ```
   pip install -r requirements.txt
   ```
3. Run the dashboard:
   ```
   python temporal_dashboard.py
   ```
4. The dashboard opens in your browser. If it does not, double-click `Dashboard/temporal_dashboard.html`.

## Technologies
Python, pandas, NumPy, Plotly
