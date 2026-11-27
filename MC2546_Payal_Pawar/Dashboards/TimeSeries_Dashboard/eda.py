"""Quick console EDA of the time-series dataset."""
import pandas as pd, numpy as np
df = pd.read_excel("data.xlsx", parse_dates=["date"])
print(df.info(), "\n"); print(df.describe().round(1), "\n")
daily = df.groupby("date").revenue.sum()
print("Missing values:", int(df.isna().sum().sum()))
print("Date gaps:", int((daily.index.to_series().diff().dt.days > 1).sum()))
print("\nRevenue by year:\n", daily.groupby(daily.index.year).sum().round(0))
print("\nAvg revenue by weekday:\n", daily.groupby(daily.index.day_name()).mean().round(0))
z = (daily - daily.rolling(30, center=True, min_periods=5).mean()); z = z / z.std()
print("\nDays with |z|>3 :", int((z.abs() > 3).sum()))
print("Lag-1 / lag-7 autocorrelation:", round(daily.autocorr(1), 3), round(daily.autocorr(7), 3))
