"""Fetch delayed public index quotes for PDMP. Never substitute stale or invented prices."""
import json, urllib.request, urllib.parse, datetime, pathlib, time
SYMBOLS={"vix":"^INDIAVIX","nifty":"^NSEI","sensex":"^BSESN"}
out={"checked_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"provider":"Yahoo Finance public chart endpoint (unofficial, may be unavailable)","quotes":{}}
for name,symbol in SYMBOLS.items():
    try:
        url="https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(symbol,safe="")+"?interval=1m&range=1d"
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; PDMP/1.0)","Accept":"application/json"})
        with urllib.request.urlopen(req,timeout=18) as r: data=json.load(r)
        result=data["chart"]["result"][0]
        meta=result["meta"]
        price=meta.get("regularMarketPrice")
        stamp=meta.get("regularMarketTime")
        if not isinstance(price,(int,float)) or price<=0 or not stamp: raise ValueError("missing price or quote timestamp")
        previous=meta.get("chartPreviousClose") or meta.get("previousClose")
        previous=float(previous) if isinstance(previous,(int,float)) and previous>0 else None
        out["quotes"][name]={"value":round(float(price),2),"as_of":datetime.datetime.fromtimestamp(stamp,datetime.timezone.utc).isoformat(),"symbol":symbol,"previous_close":previous}
        print(name,price)
    except Exception as e:
        print(name,"UNAVAILABLE",str(e))
        out["quotes"][name]=None
    time.sleep(1)
pathlib.Path("market.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
