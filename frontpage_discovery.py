"""Check public FrontPage discussion access without inventing sentiment counts."""
import json,urllib.request,re
from datetime import datetime,timezone
from pathlib import Path
from html.parser import HTMLParser

SOURCES={
 "comments":"https://front.page/comments",
 "nifty":"https://front.page/nifty-50",
 "indices_club":"https://front.page/all-about-indices",
 "stock_bets":"https://front.page/stock-bets",
}
class Visible(HTMLParser):
 def __init__(self):
  super().__init__();self.parts=[];self.skip=0
 def handle_starttag(self,tag,attrs):
  if tag in ("script","style"):self.skip+=1
 def handle_endtag(self,tag):
  if tag in ("script","style") and self.skip:self.skip-=1
 def handle_data(self,data):
  if not self.skip:self.parts.append(data)
out={"platform":"FrontPage","collected_at":datetime.now(timezone.utc).isoformat(),"method":"public_page_access_discovery_only","sources":{},"verified_directional_opinions":0,"included_in_retail_totals":False}
for name,url in SOURCES.items():
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"PDMP-Research/1.0 (public source availability check)","Accept":"text/html"})
  with urllib.request.urlopen(req,timeout=18) as response:
   raw=response.read(800000).decode("utf-8","replace");status=response.status
  parser=Visible();parser.feed(raw);visible=re.sub(r"\\s+"," "," ".join(parser.parts)).strip()
  out["sources"][name]={"url":url,"status":"accessible" if status==200 and len(visible)>100 else "insufficient_public_content","http_status":status,"visible_text_chars":len(visible),"mentions_nifty":bool(re.search(r"\\bnifty\\b",visible,re.I))}
 except Exception as e:out["sources"][name]={"url":url,"status":"unavailable","error":type(e).__name__}
Path("frontpage_discovery.json").write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps(out,indent=2))
