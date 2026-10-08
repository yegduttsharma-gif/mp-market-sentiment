"""Collect Bitcoin USD index and 30-day DVOL from public Deribit endpoints."""
import json, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

OUT=Path("btc_volatility.json")
now=datetime.now(timezone.utc)
data={"updated_at":now.isoformat(),"source":"Deribit public API","btc_usd":None,"dvol":None,"errors":[]}
def get(endpoint):
    req=urllib.request.Request("https://www.deribit.com/api/v2/public/"+endpoint,headers={"User-Agent":"PDMP-market-research/1.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=20) as response:
        obj=json.load(response)
    if obj.get("error"): raise ValueError(str(obj["error"]))
    return obj["result"]
try:
    quote=get("get_index_price?index_name=btc_usd")
    data["btc_usd"]={"value":float(quote["index_price"]),"as_of":now.isoformat()}
except Exception as exc:
    data["errors"].append("Deribit BTC index unavailable: "+str(exc)[:140])
    try:
        req=urllib.request.Request("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",headers={"User-Agent":"PDMP-research/1.0","Accept":"application/json"})
        with urllib.request.urlopen(req,timeout=15) as response: alt=json.load(response)
        data["btc_usd"]={"value":float(alt["bitcoin"]["usd"]),"as_of":now.isoformat(),"source":"CoinGecko"}
    except Exception as other:
        data["errors"].append("CoinGecko BTC price unavailable: "+str(other)[:140])
try:
    start=int((now-timedelta(days=3)).timestamp()*1000)
    end=int(now.timestamp()*1000)
    result=get(f"get_volatility_index_data?currency=BTC&start_timestamp={start}&end_timestamp={end}&resolution=3600")
    rows=result.get("data",[])
    if rows:
        last=max(rows,key=lambda x:x[0])
        data["dvol"]={"value":float(last[4]),"as_of":datetime.fromtimestamp(last[0]/1000,timezone.utc).isoformat(),"description":"Deribit BTC 30-day implied volatility"}
    else: data["errors"].append("No DVOL observations returned")
except Exception as exc:
    data["errors"].append("DVOL unavailable: "+str(exc)[:140])
# Never silently substitute historical prices for a live quote.
OUT.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
print("Bitcoin volatility:",json.dumps(data))
