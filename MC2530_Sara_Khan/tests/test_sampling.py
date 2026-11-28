import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from setup_project import choose_stratified_sample

def test_sample_is_reproducible_and_unique():
    rows = []
    for country, count in [("AA", 30), ("BB", 20), ("CC", 10)]:
        for i in range(count):
            rows.append({
                "wikidata_id": f"{country}{i}",
                "country_iso2": country,
                "country_en": country,
                "city_en": f"City{i%3}",
                "name_en": f"Place {country} {i}",
                "category": "museum" if i % 2 else "monument",
                "latitude": float(i),
                "longitude": float(i),
            })
    source = pd.DataFrame(rows)
    a = choose_stratified_sample(source, n=30, seed=42)
    b = choose_stratified_sample(source, n=30, seed=42)
    assert len(a) == 30
    assert a["wikidata_id"].is_unique
    assert a["wikidata_id"].tolist() == b["wikidata_id"].tolist()
    assert set(a["country_iso2"]) == {"AA", "BB", "CC"}

if __name__ == "__main__":
    test_sample_is_reproducible_and_unique()
    print("Sampling test passed.")
