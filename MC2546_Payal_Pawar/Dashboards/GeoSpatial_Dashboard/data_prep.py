"""Generate a synthetic geo-spatial dataset (Indian cities, monthly air-quality) -> data.xlsx"""
import numpy as np, pandas as pd
# city, state, region, lat, lon, population (millions)
C = """Delhi,Delhi,North,28.61,77.21,32.9|Gurugram,Haryana,North,28.46,77.03,1.2|Lucknow,Uttar Pradesh,North,26.85,80.95,3.9|Kanpur,Uttar Pradesh,North,26.45,80.35,3.2
Varanasi,Uttar Pradesh,North,25.32,83.01,1.6|Chandigarh,Chandigarh,North,30.73,76.78,1.2|Amritsar,Punjab,North,31.63,74.87,1.4|Jaipur,Rajasthan,North,26.91,75.79,4.1
Jodhpur,Rajasthan,North,26.24,73.02,1.2|Dehradun,Uttarakhand,North,30.32,78.03,0.8|Srinagar,Jammu & Kashmir,North,34.08,74.80,1.5|Patna,Bihar,East,25.59,85.14,2.5
Ranchi,Jharkhand,East,23.34,85.31,1.2|Kolkata,West Bengal,East,22.57,88.36,15.0|Bhubaneswar,Odisha,East,20.30,85.82,1.1|Guwahati,Assam,East,26.14,91.74,1.1
Mumbai,Maharashtra,West,19.08,72.88,21.0|Pune,Maharashtra,West,18.52,73.86,7.4|Nagpur,Maharashtra,West,21.15,79.09,2.9|Nashik,Maharashtra,West,20.00,73.79,2.1
Ahmedabad,Gujarat,West,23.02,72.57,8.4|Surat,Gujarat,West,21.17,72.83,7.5|Panaji,Goa,West,15.50,73.83,0.1|Indore,Madhya Pradesh,Central,22.72,75.86,3.3
Bhopal,Madhya Pradesh,Central,23.26,77.41,2.4|Raipur,Chhattisgarh,Central,21.25,81.63,1.6|Hyderabad,Telangana,South,17.39,78.49,10.5|Visakhapatnam,Andhra Pradesh,South,17.69,83.22,2.2
Vijayawada,Andhra Pradesh,South,16.51,80.65,1.5|Bengaluru,Karnataka,South,12.97,77.59,13.6|Mysuru,Karnataka,South,12.30,76.64,1.1|Chennai,Tamil Nadu,South,13.08,80.27,11.5
Coimbatore,Tamil Nadu,South,11.02,76.96,2.2|Kochi,Kerala,South,9.93,76.27,2.2|Thiruvananthapuram,Kerala,South,8.52,76.94,1.7|Madurai,Tamil Nadu,South,9.93,78.12,1.6""".replace("\n", "|").split("|")

def category(a):
    return pd.cut(a, [0, 50, 100, 200, 300, 400, 1000], labels=["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]).astype(str)

def build(seed=7):
    rng = np.random.default_rng(seed); months = pd.date_range("2024-01-01", "2026-10-01", freq="MS"); rows = []
    base = {"North": 105, "East": 85, "Central": 70, "West": 62, "South": 42}
    for line in C:
        city, st, reg, lat, lon, pop = line.split(","); lat, lon, pop = float(lat), float(lon), float(pop)
        veh = np.clip(120 + 18 * np.log1p(pop) * 10 + rng.normal(0, 40), 60, 600); green = np.clip(rng.normal(14, 6) - pop * .3, 2, 35)
        cb = base[reg] * (1 + .12 * np.log1p(pop)) * (1 + (veh - 300) / 1500)
        for d in months:
            m = d.month; winter = 1 + (.9 if reg in ("North", "East") else .35) * np.cos(2 * np.pi * (m - 12) / 12) ** 2 * (m in (10, 11, 12, 1, 2))
            monsoon = .55 if m in (7, 8, 9) else 1
            pm = max(8, cb * winter * monsoon * (1 - .004 * (d.year - 2024) * 12) * rng.normal(1, .08))
            t = 25 + (6 if reg != "South" else 2) * np.sin(2 * np.pi * (m - 4) / 12) - (lat - 20) * .15 + rng.normal(0, 1)
            rows.append([city, st, reg, lat, lon, d, pop, round(pm, 1), round(min(500, pm * 1.9 + rng.normal(0, 8))), round(t, 1),
                         round(np.clip(60 + 25 * np.sin(2 * np.pi * (m - 7) / 12) + rng.normal(0, 5), 20, 98)), round(green, 1), round(veh)])
    df = pd.DataFrame(rows, columns=["city", "state", "region", "lat", "lon", "date", "population_m", "pm25", "aqi", "temp_c", "humidity", "green_cover_pct", "vehicles_per_1000"])
    df["aqi_category"] = category(df.aqi); return df

if __name__ == "__main__":
    df = build(); df.to_excel("data.xlsx", index=False, sheet_name="Fused"); print(f"data.xlsx written: {df.shape[0]:,} rows, {df.city.nunique()} cities")
