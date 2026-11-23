"""One-off helper: detect the country of records whose country is 'Not recorded' from their coordinates.
Needs: pip install "geopandas<1.0"   |   Run from the project root:  python scripts/infer_countries.py
Writes data/processed/inferred_country.csv and data/processed/country_centroids.csv (the app only needs pandas)."""
import sys
from pathlib import Path
import warnings
import pandas as pd
import geopandas as gpd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from modules.data_cleaning import clean_data
from config.settings import RAW_PATH, NOT_RECORDED

ALIAS = {"United States of America": "United States", "Dominican Rep.": "Dominican Republic", "Eq. Guinea": "Equatorial Guinea",
         "Bosnia and Herz.": "Bosnia and Herzegovina", "Central African Rep.": "Central African Republic",
         "Falkland Is.": "Falkland Islands", "Solomon Is.": "Solomon Islands", "S. Sudan": "South Sudan",
         "Dem. Rep. Congo": "Democratic Republic of the Congo", "N. Cyprus": "Northern Cyprus", "W. Sahara": "Western Sahara",
         "Fr. S. Antarctic Lands": "French Southern and Antarctic Lands", "Czechia": "Czech Republic"}
MAX_DEG = 0.4   # ~45 km: samples taken on the shore are matched to the nearest coastline

world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
world = world[world.name != "Antarctica"][["name", "geometry"]].copy()
world["name"] = world.name.replace(ALIAS)

df, _ = clean_data(pd.read_csv(RAW_PATH))
loc = df[df.country == NOT_RECORDED].drop_duplicates("loc_key")[["loc_key", "lat", "lon"]]
pts = gpd.GeoDataFrame(loc, geometry=gpd.points_from_xy(loc.lon, loc.lat), crs=world.crs)

inside = gpd.sjoin(pts, world, how="left", predicate="within")[["loc_key", "name"]].drop_duplicates("loc_key")
found = inside.dropna(subset=["name"])
rest = pts[~pts.loc_key.isin(found.loc_key)]
near = gpd.sjoin_nearest(rest, world, how="left", max_distance=MAX_DEG)[["loc_key", "name"]].dropna(subset=["name"]).drop_duplicates("loc_key")
out = pd.concat([found, near]).rename(columns={"name": "country"})
out.to_csv(ROOT / "data/processed/inferred_country.csv", index=False)

cen = world.dissolve(by="name").representative_point()
pd.DataFrame({"country": cen.index, "lat": cen.y.values, "lon": cen.x.values}).to_csv(ROOT / "data/processed/country_centroids.csv", index=False)
print(f"{len(out):,} of {len(loc):,} unrecorded locations matched to a country")
