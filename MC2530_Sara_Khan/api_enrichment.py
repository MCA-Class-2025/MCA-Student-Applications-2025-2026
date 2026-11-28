import argparse, json, time, hashlib
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote
import pandas as pd
import requests

ROOT=Path(__file__).resolve().parent
DATA=ROOT/"data"; REPORTS=ROOT/"reports"; CACHE=DATA/"api_cache"
DATA.mkdir(exist_ok=True); REPORTS.mkdir(exist_ok=True); CACHE.mkdir(exist_ok=True)
INPUT=DATA/"travel_attractions_1500.csv"; OUTPUT=DATA/"travel_attractions_master.xlsx"
S=requests.Session(); S.headers.update({"User-Agent":"TravelDestinationIntelligence/1.0 (academic project)"})
TIMEOUT=25

def cached_get(key,url,params=None,ttl=30):
    raw=json.dumps([key,url,params],sort_keys=True,default=str).encode()
    path=CACHE/(hashlib.sha256(raw).hexdigest()+".json")
    if path.exists() and time.time()-path.stat().st_mtime<ttl*86400:
        try:return json.loads(path.read_text(encoding="utf-8")),"CACHED"
        except Exception:pass
    try:
        response=S.get(url,params=params,timeout=TIMEOUT); response.raise_for_status()
        payload=response.json()
        path.write_text(json.dumps(payload,ensure_ascii=False),encoding="utf-8")
        return payload,"SUCCESS"
    except Exception as exc:return {},"ERROR: "+str(exc)[:250]

def avg(values):
    vals=[v for v in values if isinstance(v,(int,float)) and pd.notna(v)]
    return round(sum(vals)/len(vals),1) if vals else None

def get_weather(row):
    lat,lon=row.get("latitude"),row.get("longitude")
    if pd.isna(lat) or pd.isna(lon):return {},"SKIPPED: coordinates missing"
    p={"latitude":float(lat),"longitude":float(lon),"daily":"temperature_2m_max,temperature_2m_min,precipitation_probability_max","forecast_days":7,"timezone":"auto"}
    f,fs=cached_get("forecast","https://api.open-meteo.com/v1/forecast",p,1)
    end=date.today()-timedelta(days=1)
    hp={"latitude":float(lat),"longitude":float(lon),"start_date":(end-timedelta(days=29)).isoformat(),"end_date":end.isoformat(),"daily":"temperature_2m_mean,precipitation_sum","timezone":"auto"}
    h,hs=cached_get("history","https://archive-api.open-meteo.com/v1/archive",hp,30)
    fd=f.get("daily",{}); hd=h.get("daily",{})
    rain=[x for x in fd.get("precipitation_probability_max",[]) if x is not None]
    precip=[x for x in hd.get("precipitation_sum",[]) if x is not None]
    return {"forecast_avg_max_temp_c":avg(fd.get("temperature_2m_max",[])),
            "forecast_avg_min_temp_c":avg(fd.get("temperature_2m_min",[])),
            "forecast_max_rain_probability_pct":max(rain) if rain else None,
            "past_30d_avg_temp_c":avg(hd.get("temperature_2m_mean",[])),
            "past_30d_precipitation_mm":round(sum(precip),1) if precip else None},f"forecast={fs}; historical={hs}"

def get_wikipedia(name):
    if not name or pd.isna(name):return {},"SKIPPED: no name"
    data,status=cached_get("wikipedia","https://en.wikipedia.org/api/rest_v1/page/summary/"+quote(str(name).replace(" ","_")),None,90)
    return {"wikipedia_title":data.get("title"),"wikipedia_summary":data.get("extract"),
            "wikipedia_url":data.get("content_urls",{}).get("desktop",{}).get("page")},status

def get_wikidata(df):
    ids=list(dict.fromkeys(str(v) for v in df.wikidata_id if pd.notna(v) and str(v).startswith("Q")))
    output={}
    for i in range(0,len(ids),40):
        batch=ids[i:i+40]
        data,status=cached_get("wikidata","https://www.wikidata.org/w/api.php",
            {"action":"wbgetentities","ids":"|".join(batch),"props":"labels|descriptions|claims","languages":"en","format":"json"},30)
        for qid,entity in data.get("entities",{}).items():
            claims=entity.get("claims",{})
            def claim(prop):
                try:return claims[prop][0]["mainsnak"]["datavalue"]["value"]
                except Exception:return None
            inception=claim("P571"); architect=claim("P84"); heritage=claim("P1435")
            output[qid]={"wikidata_description":entity.get("descriptions",{}).get("en",{}).get("value"),
                "inception_date":inception.get("time") if isinstance(inception,dict) else None,
                "architect_wikidata_id":architect.get("id") if isinstance(architect,dict) else None,
                "heritage_designation_wikidata_id":heritage.get("id") if isinstance(heritage,dict) else None,
                "official_website":claim("P856")}
        time.sleep(.15)
    return output

def get_currency_codes():
    try:
        import pycountry
        from babel.numbers import get_territory_currencies
        mapping={}
        for country in pycountry.countries:
            found=get_territory_currencies(country.alpha_2,tender=True)
            if found:mapping[country.alpha_2]=found[0]
        return mapping
    except Exception:return {}

def enrich(limit=None):
    if not INPUT.exists():raise FileNotFoundError(f"Missing {INPUT}. Run python setup_project.py first.")
    df=pd.read_csv(INPUT)
    if limit:df=df.head(limit).copy()
    else:df=df.copy()
    print(f"Starting enrichment for {len(df)} attractions")
    wd=get_wikidata(df)
    for col in ["wikidata_description","inception_date","architect_wikidata_id","heritage_designation_wikidata_id","official_website"]:
        df[col]=[wd.get(str(qid),{}).get(col) for qid in df.wikidata_id]
    wiki_rows=[];weather_rows=[];logs=[]
    for n,(_,row) in enumerate(df.iterrows(),1):
        print(f"[{n}/{len(df)}] {row.get('name_en','')}")
        w,ws=get_wikipedia(row.get("name_en")); m,ms=get_weather(row)
        wiki_rows.append(w);weather_rows.append(m)
        logs.append({"record_id":row.get("record_id"),"attraction":row.get("name_en"),
                     "wikipedia_status":ws,"weather_status":ms})
        time.sleep(.10)
    for part in (pd.DataFrame(wiki_rows),pd.DataFrame(weather_rows)):
        for col in part.columns:df[col]=part[col].values
    currency_map=get_currency_codes()
    df["currency_code"]=df["country_iso2"].map(currency_map)
    currencies=sorted(set(x for x in df.currency_code.dropna() if x!="INR"))
    rates={}
    for i in range(0,len(currencies),30):
        batch=currencies[i:i+30]
        fx,status=cached_get("frankfurter","https://api.frankfurter.dev/v1/latest",
                             {"base":"INR","symbols":",".join(batch)},1)
        for code,value in fx.get("rates",{}).items():
            rates[code]=round(1/float(value),5) if value else None
    rates["INR"]=1.0
    df["currency_inr_per_unit"]=df["currency_code"].map(rates)
    holidays={}
    year=date.today().year
    available,status_available=cached_get("nager_available","https://date.nager.at/api/v3/AvailableCountries",None,7)
    supported={item.get("countryCode") for item in available if isinstance(item,dict)} if isinstance(available,list) else set()
    for code in sorted(set(str(x) for x in df.country_iso2.dropna())):
        if code not in supported:
            holidays[code]={"public_holidays_this_year":None,"next_public_holiday":None,
                            "next_public_holiday_date":None,"holiday_api_status":"UNSUPPORTED_COUNTRY"}
            continue
        data,status=cached_get("nager_date",f"https://date.nager.at/api/v3/PublicHolidays/{year}/{code}",None,30)
        if isinstance(data,list):
            upcoming=[x for x in data if x.get("date","")>=date.today().isoformat()]
            holidays[code]={"public_holidays_this_year":len(data),
                "next_public_holiday":((upcoming[0].get("localName") or upcoming[0].get("name")) if upcoming else None),
                "next_public_holiday_date":(upcoming[0].get("date") if upcoming else None),
                "holiday_api_status":status}
        else:holidays[code]={"public_holidays_this_year":None,"next_public_holiday":None,
                            "next_public_holiday_date":None,"holiday_api_status":status}
        time.sleep(.10)
    holiday_df=pd.DataFrame([holidays.get(str(c),{}) for c in df.country_iso2])
    for col in holiday_df.columns:df[col]=holiday_df[col].values
    # Keep master workbook with all processed records in this run.
    log_df=pd.DataFrame(logs)
    with pd.ExcelWriter(OUTPUT,engine="openpyxl") as writer:
        df.to_excel(writer,sheet_name="Attractions",index=False)
        log_df.to_excel(writer,sheet_name="API_Log",index=False)
        pd.DataFrame([
            ["Open-Meteo","7-day forecast and previous 30 days of weather"],
            ["Wikipedia REST","Attraction summary and page URL"],
            ["Wikidata","Structured facts using attraction QID"],
            ["Frankfurter","Indicative exchange rates converted to INR per currency unit"],
            ["Nager.Date","Public holidays by country and year"]
        ],columns=["API","Purpose"]).to_excel(writer,sheet_name="API_Reference",index=False)
    df.to_csv(DATA/"travel_attractions_enriched.csv",index=False)
    log_df.to_csv(REPORTS/"api_processing_log.csv",index=False)
    print(f"Saved enriched workbook: {OUTPUT}")
    return df,log_df

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--limit",type=int,default=50)
    parser.add_argument("--all",action="store_true")
    args=parser.parse_args()
    enrich(None if args.all else max(1,args.limit))
