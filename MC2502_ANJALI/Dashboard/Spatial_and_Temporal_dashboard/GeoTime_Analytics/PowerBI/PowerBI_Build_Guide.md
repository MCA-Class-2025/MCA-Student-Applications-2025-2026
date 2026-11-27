# Power BI build guide (from the project plan)
1. Get Data > Text/CSV > Dataset/USGS_Earthquake_Cleaned.csv (name the table Earthquakes). Also load Dataset/Daily_Anomalies.csv.
2. Add the items in DAX_Measures.dax; create the relationship and mark the date table.
3. Pages: Global Overview, Temporal Intelligence, Spatial Intelligence, Advanced Analytics (same layout as Dashboard/geotime_dashboard.html).
4. Maps: latitude/longitude as "Don't summarize" (never Sum). Use heat map or aggregated grid for large data. Tooltip: time, mag, depth, place. Add bookmarks, date slicer, drill-through.
