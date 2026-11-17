
import pandas as pd
import os

df = pd.read_csv("data/fused_country_intelligence.csv")

pairs = [
    ("GDP per capita", "PM2.5"),
    ("GDP per capita", "Temperature (°C)"),
    ("GDP per capita", "Exchange Rate"),
    ("Life expectancy", "PM2.5"),
    ("Life expectancy", "Temperature (°C)"),
    ("Internet usage", "PM2.5"),
    ("Unemployment", "PM2.5")
]

results = []

for x, y in pairs:
    temp = df[[x, y]].apply(
        pd.to_numeric, errors="coerce"
    ).dropna()

    if len(temp) >= 3:
        correlation = round(temp[x].corr(temp[y]), 4)
    else:
        correlation = "Insufficient data"

    results.append({
        "WDI Variable": x,
        "API Variable": y,
        "Valid Country Pairs": len(temp),
        "Pearson Correlation": correlation
    })

result_df = pd.DataFrame(results)

os.makedirs("data", exist_ok=True)
result_df.to_csv("data/part_f_relationships.csv", index=False)

print("\n========== PART F: NEW RELATIONSHIPS ==========")
print(result_df.to_string(index=False))
print("\nSaved: data/part_f_relationships.csv")
