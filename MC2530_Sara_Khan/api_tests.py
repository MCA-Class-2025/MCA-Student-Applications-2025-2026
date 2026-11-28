"""Live connectivity smoke tests for the five API providers."""
import time
from pathlib import Path
import requests
import pandas as pd

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"reports"/"api_smoke_test_results.csv"
S=requests.Session();S.headers["User-Agent"]="TravelDestinationIntelligence/1.0 academic-project"
TESTS=[
 ("Open-Meteo forecast","https://api.open-meteo.com/v1/forecast",{"latitude":48.8584,"longitude":2.2945,"daily":"temperature_2m_max","forecast_days":2},"daily"),
 ("Open-Meteo historical","https://archive-api.open-meteo.com/v1/archive",{"latitude":48.8584,"longitude":2.2945,"start_date":"2025-01-01","end_date":"2025-01-03","daily":"temperature_2m_mean"},"daily"),
 ("Wikipedia REST","https://en.wikipedia.org/api/rest_v1/page/summary/Eiffel_Tower",None,"extract"),
 ("Wikidata","https://www.wikidata.org/w/api.php",{"action":"wbgetentities","ids":"Q243","props":"labels","languages":"en","format":"json"},"entities"),
 ("Frankfurter","https://api.frankfurter.dev/v1/latest",{"base":"INR","symbols":"USD,EUR"},"rates"),
 ("Nager.Date supported countries","https://date.nager.at/api/v3/AvailableCountries",None,"list"),
 ("Nager.Date public holidays (Germany)","https://date.nager.at/api/v3/PublicHolidays/2026/DE",None,"list"),
]
def main():
    rows=[]
    for name,url,params,key in TESTS:
        start=time.time()
        try:
            r=S.get(url,params=params,timeout=20);r.raise_for_status();data=r.json()
            ok=isinstance(data,list) if key=="list" else key in data
            if name=="Nager.Date supported countries" and ok:
                ok=any(x.get("countryCode")=="DE" for x in data if isinstance(x,dict))
            rows.append({"service":name,"http_status":r.status_code,"result":"PASS" if ok else "FAIL",
                         "details":"Expected response structure present" if ok else f"Unexpected response structure: {key}",
                         "duration_seconds":round(time.time()-start,2)})
        except Exception as e:
            rows.append({"service":name,"http_status":None,"result":"FAIL","details":str(e)[:250],
                         "duration_seconds":round(time.time()-start,2)})
        print(rows[-1])
    OUT.parent.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT,index=False)
    print("Report:",OUT)
    return all(x["result"]=="PASS" for x in rows)
if __name__=="__main__":main()
