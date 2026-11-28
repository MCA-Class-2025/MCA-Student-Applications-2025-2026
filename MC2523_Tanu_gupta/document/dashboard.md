# Weather Insights Dashboard

This Python dashboard uses Streamlit and Plotly to explore historical climate
records and saved live-weather captures. The implementation and bundled
assets are in [`dashboard/`](../dashboard/).

## Dashboard sections

- **Overview:** dataset KPIs, latest saved capture, and weather summaries.
- **Historical climate:** annual temperatures, monthly patterns, rain,
  precipitation, city comparisons, conditions, and wind.
- **Live + historical fusion:** captured temperatures, historical comparisons,
  deviations, and weather relationships.
- **Data explorer:** filtered source records, quality counts, and CSV downloads.

The dashboard includes its own weather icons in
`dashboard/code/assets/weather_app_img/`. It reads data from
`dataset/processed/` and compares locations by city because the source data
does not contain latitude/longitude coordinates.

## Run

From the project folder in PowerShell:

```powershell
python -m pip install -r .\dashboard\code\requirements.txt
streamlit run .\dashboard\code\app.py
```

Streamlit prints a local URL (normally `http://localhost:8501`).

## Screenshots

Captures of all dashboard tabs and representative chart/table views:

- [Overview](../dashboard/screenshots/01-overview.png)
- [Annual temperature trend](../dashboard/screenshots/02-overview-temperature-trend.png)
- [Historical climate](../dashboard/screenshots/03-historical-climate.png)
- [Historical climate chart](../dashboard/screenshots/04-historical-climate-chart.png)
- [Live and historical fusion](../dashboard/screenshots/05-live-historical-fusion.png)
- [Fusion comparison chart](../dashboard/screenshots/06-live-historical-fusion-chart.png)
- [Data explorer](../dashboard/screenshots/07-data-explorer.png)
- [Data table](../dashboard/screenshots/08-data-explorer-table.png)
