"""Rebuild the dashboard from the fused CSV: python build_dashboard.py"""
import json, pandas as pd, os
here = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(here, "Dataset", "final_fusion_dataset.csv"))
S = []
for sp, g in df.groupby("species"):
    f = g.iloc[0]
    S.append(dict(name=sp, n=len(g), train=int((g.split == "train").sum()), test=int((g.split == "test").sum()),
        can=f.gbif_canonical_name, tk=int(f.gbif_taxon_key), cty=f.gbif_top_country, lat=float(f.gbif_mean_latitude),
        lon=float(f.gbif_mean_longitude), occ=int(f.gbif_occurrence_count), countries=int(f.gbif_country_count),
        fdc=int(f.usda_fdc_id), fdesc=f.usda_description, cal=float(f.usda_calories), pro=float(f.usda_protein),
        fat=float(f.usda_fat), car=float(f.usda_carbohydrate), wdesc=f.weather_description, loc=f.weather_location,
        temp=float(f.weather_temperature), hum=float(f.weather_humidity), prs=float(f.weather_pressure),
        wnd=float(f.weather_wind_speed), cld=float(f.weather_clouds)))
Q = dict(total=len(df), gbif=int((df.gbif_status == "success").sum()), usda=int((df.usda_status == "verified").sum()),
         wx=int((df.weather_status == "success").sum()), unk=int((df.weather_location == "Unknown").sum()),
         nulls=int(df.isnull().sum().sum()))
Q["ok"] = int(((df.gbif_status == "success") & (df.usda_status == "verified") & (df.weather_status == "success")).sum())
html = open(os.path.join(here, "Dashboard", "template.html"), encoding="utf-8").read()
html = html.replace("/*DATA*/", json.dumps(S)).replace("/*QUALITY*/", json.dumps(Q))
open(os.path.join(here, "Dashboard", "fishfusion_dashboard.html"), "w", encoding="utf-8").write(html)
print("built", len(S), "species,", Q)
