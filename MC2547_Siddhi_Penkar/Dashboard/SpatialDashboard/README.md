# Spatial Analytics Dashboard

An interactive Python dashboard for spatial (location-based) analysis of US airport traffic and US city populations.

## Objective
To show where air traffic and population are concentrated across the United States using maps, regional comparisons and density analysis.

## Datasets
- `Dataset/us_airport_traffic.csv`: airports with IATA code, name, city, state, latitude, longitude and flight count (Feb 2011)
- `Dataset/us_cities_population.csv`: US cities with population, latitude and longitude (2014)

## Data Preparation
- Rows with missing values and duplicate airports/cities were removed.
- Coordinates were validated to lie within the US (including Alaska and Hawaii).
- Derived spatial features: region (West / Central / East by longitude), latitude band, state-level totals, and distance from the geographic centre of the US (haversine formula).


## Project Structure
```
Spatial_Dashboard/
  spatial_dashboard.py     # main script
  dashkit.py               # shared layout and theme helper
  requirements.txt
  Dataset/
    us_airport_traffic.csv
    us_cities_population.csv
  Dashboard/
    spatial_dashboard.html   # generated output
```

## How to Run (VS Code)
1. Open the terminal (Ctrl + `).
2. Install the libraries:
   ```
   pip install -r requirements.txt
   ```
3. Run the dashboard:
   ```
   python spatial_dashboard.py
   ```
4. The dashboard opens in your browser. If it does not, double-click `Dashboard/spatial_dashboard.html`.

## Technologies
Python, pandas, NumPy, Plotly
