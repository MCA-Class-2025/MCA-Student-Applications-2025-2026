"""
01_make_messy_raw.py
Takes the freshly generated (clean) hotels/flights/users CSVs and introduces
realistic real-world messiness that is typical of Kaggle-exported travel data
(mixed date formats, a few missing values, duplicate rows, inconsistent text
casing/spacing, and a handful of genuine outliers). This gives Part D of the
assignment (Data Quality Assessment) real issues to find and treat, instead
of a spotlessly clean dataset that would make the exercise trivial.
"""
import pandas as pd
import numpy as np
import random

random.seed(7)
np.random.seed(7)

RAW = "/home/claude/FinSightAI/data/original"

def messy_date(date_str):
    """Randomly reformat ~35% of dates from MM/DD/YYYY to MM-DD-YYYY,
    mimicking the inconsistent formats seen in the original Kaggle export."""
    if random.random() < 0.35:
        return date_str.replace("/", "-")
    return date_str

# ---------------- USERS ----------------
users = pd.read_csv(f"{RAW}/users.csv")
# Inject a few missing ages / genders
miss_idx = users.sample(frac=0.03, random_state=1).index
users.loc[miss_idx, "age"] = np.nan
miss_idx2 = users.sample(frac=0.02, random_state=2).index
users.loc[miss_idx2, "gender"] = np.nan
# Inconsistent casing / spacing on a few names & companies
cas_idx = users.sample(frac=0.05, random_state=3).index
users.loc[cas_idx, "company"] = users.loc[cas_idx, "company"].str.upper()
users.loc[users.sample(frac=0.03, random_state=4).index, "name"] = \
    users.loc[users.sample(frac=0.03, random_state=4).index, "name"].str.strip() + "  "
# Duplicate a few user rows (data entry duplicates)
dup_users = users.sample(frac=0.02, random_state=5)
users = pd.concat([users, dup_users], ignore_index=True)
users.to_csv(f"{RAW}/users.csv", index=False)

# ---------------- HOTELS ----------------
hotels = pd.read_csv(f"{RAW}/hotels.csv")
hotels["date"] = hotels["date"].apply(messy_date)
# Inconsistent place spelling/casing on a small subset
def mess_place(p):
    r = random.random()
    if r < 0.03:
        return p.lower()
    if r < 0.05:
        return p.replace("(", " (").replace("  (", " (")
    return p
hotels["place"] = hotels["place"].apply(mess_place)
# A few missing prices
miss_p = hotels.sample(frac=0.015, random_state=6).index
hotels.loc[miss_p, "price"] = np.nan
# Genuine outliers: one data-entry error (extreme price), one negative (refund glitch)
out_idx = hotels.sample(n=3, random_state=7).index.tolist()
hotels.loc[out_idx[0], "price"] = hotels["price"].max() * 18   # data entry error, e.g. extra digit
hotels.loc[out_idx[1], "total"] = hotels.loc[out_idx[1], "price"] * hotels.loc[out_idx[1], "days"] * 15
hotels.loc[out_idx[2], "price"] = -hotels.loc[out_idx[2], "price"]  # negative price error
# Duplicate rows
dup_hotels = hotels.sample(frac=0.015, random_state=8)
hotels = pd.concat([hotels, dup_hotels], ignore_index=True)
hotels.to_csv(f"{RAW}/hotels.csv", index=False)

# ---------------- FLIGHTS ----------------
flights = pd.read_csv(f"{RAW}/flights.csv")
flights["date"] = flights["date"].apply(messy_date)
flights["to"] = flights["to"].apply(mess_place)
flights["from"] = flights["from"].apply(mess_place)
miss_f = flights.sample(frac=0.01, random_state=9).index
flights.loc[miss_f, "price"] = np.nan
out_idx_f = flights.sample(n=2, random_state=10).index.tolist()
flights.loc[out_idx_f[0], "price"] = flights["price"].max() * 12
flights.loc[out_idx_f[1], "distance"] = -flights.loc[out_idx_f[1], "distance"]
dup_flights = flights.sample(frac=0.01, random_state=11)
flights = pd.concat([flights, dup_flights], ignore_index=True)
flights.to_csv(f"{RAW}/flights.csv", index=False)

print("Users  :", users.shape)
print("Hotels :", hotels.shape)
print("Flights:", flights.shape)
print("Done injecting realistic messiness into raw CSVs.")
