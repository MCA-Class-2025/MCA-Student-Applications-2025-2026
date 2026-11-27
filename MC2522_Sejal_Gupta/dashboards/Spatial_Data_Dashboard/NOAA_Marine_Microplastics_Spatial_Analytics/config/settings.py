"""Global settings for the NOAA Marine Microplastics app."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = ROOT / "data" / "raw" / "NOAA_Marine_Microplastics.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
PREFS_PATH = ROOT / "data" / "processed" / "prefs.json"
EXPORT_DIR = ROOT / "exports"

APP_TITLE = "NOAA MARINE MICROPLASTICS"
APP_SUBTITLE = "Spatial Intelligence & Analytics"
NOT_RECORDED = "Not recorded"
DEFAULT_THEME = "ocean_intelligence"

# (file, nav label, page title)
PAGES = [
    ("pages/1_Executive_Overview.py", "Overview", "Executive Overview"),
    ("pages/2_Geographic_Distribution.py", "Geography", "Geographic Distribution"),
    ("pages/3_Regional_Analysis.py", "Regional", "Regional Analysis"),
    ("pages/4_Concentration_Analysis.py", "Concentration", "Concentration Analysis"),
    ("pages/5_Spatial_Density_Hotspots.py", "Hotspots", "Spatial Density & Hotspots"),
    ("pages/6_Spatial_Statistics.py", "Statistics", "Spatial Statistics"),
    ("pages/7_Data_Explorer_Export.py", "Explorer", "Data Explorer & Export"),
    ("pages/8_Insights_PDF_Report.py", "Insights", "Insights & PDF Report"),
]

CLASS_ORDER = ["Very Low", "Low", "Medium", "High", "Very High"]
DEFAULT_UNIT = "pieces/m3"
