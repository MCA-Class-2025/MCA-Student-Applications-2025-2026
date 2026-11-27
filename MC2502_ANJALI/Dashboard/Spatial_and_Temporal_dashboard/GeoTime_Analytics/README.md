# GeoTime Analytics
1. pip install pandas numpy requests scikit-learn pyarrow
2. Run Python_Analysis/GeoTime_Pipeline.ipynb top to bottom (needs internet). It writes Dataset/*.csv and Dashboard/dashboard_data.js.
3. Open Dashboard/geotime_dashboard.html (double-click or Live Server). It loads the data automatically; no upload needed.
4. Build the Power BI version using PowerBI/.
Dataset/ and the data file are empty until step 2 runs, because the data must be downloaded from USGS.
