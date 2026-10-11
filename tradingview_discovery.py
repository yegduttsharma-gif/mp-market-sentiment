"""Best-effort public TradingView idea-page availability monitor.

This is a DISCOVERY/HEALTH collector, not a retail sentiment classifier.
TradingView public idea listings can contain creator analyses, stale posts,
conditional bull/bear scenarios and duplicated authors. Never count them as
independent retail positions without item-level verification.
"""
import json,urllib.request,urllib.error,re
from datetime import datetime,timezone
from pathlib import Path
SOURCES={
 "NIFTY 50":"https://in.tradingview.com/symbols/NSE-NIFTY/ideas/",
 "BANK NIFTY":"https://in.tradingview.com/ideas/banknifty/",
 "SENSEX":"https://in.tradingview.com/symbols/INDEX-SENSEX/ideas/"
}
out={"collected_at":datetime.now(timezone.utc).isoformat(),"platform":"TradingView","collection_type":"public_trader_ideas_discovery_only","retail_sentiment_count":0,"note":"TradingView creator ideas are NOT counted as independent retail viewer comments or crowd consensus.","sources":{}}
for asset,url in SOURCES.items():
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; PDMP public idea availability research)","Accept":"text/html"})
  with urllib.request.urlopen(req,timeout=20) as response:
   raw=response.read(600000).decode("utf-8","replace")
   status=response.status
  title=re.search(r"<title[^>]*>(.*?)</title>",raw,re.I|re.S)
  page_title=re.sub(r"\\s+"," ",re.sub(r"<[^>]*>"," ",title.group(1))).strip()[:180] if title else ""
  usable=bool(status==200 and len(raw)>1500 and ("tradingview" in raw.lower()) and ("idea" in raw.lower()))
  out["sources"][asset]={"url":url,"status":"page_accessible" if usable else "unverified_page","http_status":status,"page_title":page_title,"html_bytes":len(raw),"individual_ideas_verified":0}
 except Exception as e:
  out["sources"][asset]={"url":url,"status":"unavailable","error":type(e).__name__,"individual_ideas_verified":0}
Path("tradingview_discovery.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
print("TradingView discovery",[(k,v["status"]) for k,v in out["sources"].items()])
