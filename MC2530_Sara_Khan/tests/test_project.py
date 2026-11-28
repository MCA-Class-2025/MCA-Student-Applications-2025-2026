import sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from api_enrichment import avg

def test_average_ignores_missing():
    assert avg([2,4,None,float("nan")]) == 3.0

def test_average_empty():
    assert avg([None,float("nan")]) is None

def test_dataset_has_expected_columns_if_present():
    path=ROOT/"data"/"travel_attractions_1500.csv"
    if path.exists():
        df=pd.read_csv(path,nrows=5)
        required={"name_en","country_en","city_en","category","latitude","longitude"}
        assert required.issubset(df.columns)
