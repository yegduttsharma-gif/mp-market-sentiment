"""Check public Investing.com index discussion page accessibility; no comment scraping."""
import json,urllib.request,re,html
from datetime import datetime,timezone
from pathlib import Path
URLS={"NIFTY 50":"https://in.investing.com/indices/s-p-cnx-nifty-commentary","BANK NIFTY":"https://in.investing.com/indices/bank-nifty-commentary","SENSEX":"https://in.investing.com/indices/sensex-commentary"}
out={"collected_at":datetime.now(timezone.utc).isoformat(),"platform":"Investing.com","collection_type":"public_forum_accessibility_only","directional_opinions_verified":0,"assets":{}}
for asset,url in URLS.items():
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; PDMP availability research)","Accept":"text/html"})
  with urllib.request.urlopen(req,timeout=15) as response:
   raw=response.read(350000).decode("utf-8","replace");status=response.status
  title=re.search(r"<title[^>]*>(.*?)</title>",raw,re.I|re.S)
  page_title=html.unescape(re.sub(r"<[^>]*>","",title.group(1)).strip())[:140] if title else ""
  out["assets"][asset]={"url":url,"status":"page_accessible" if status==200 and len(raw)>1000 else "unverified","http_status":status,"page_title":page_title,"verified_comments":0}
 except Exception as e:
  out["assets"][asset]={"url":url,"status":"unavailable","error":type(e).__name__,"verified_comments":0}
Path("investing_forum_discovery.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
print("Investing forum source checks",[(k,v["status"]) for k,v in out["assets"].items()])
