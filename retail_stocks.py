"""Public Reddit-post headline sentiment: a limited proxy, NOT measured retail ownership."""
import json,re,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime,timezone,timedelta
from collections import Counter
STOCKS={
"Reliance Industries":["reliance industries","ril stock","reliance stock"],
"HDFC Bank":["hdfc bank","hdfcbank"],
"ICICI Bank":["icici bank","icicibank"],
"SBI":["state bank of india","sbi stock","sbin"],
"Tata Motors":["tata motors","tatamotors"],
"Tata Consultancy Services":["tcs stock","tata consultancy"],
"Infosys":["infosys","infy stock"],
"ITC":["itc stock","itc ltd"],
"Bharti Airtel":["bharti airtel","airtel stock"],
"Adani Enterprises":["adani enterprises","adanient"],
"HAL":["hindustan aeronautics","hal stock"],
"BHEL":["bhel","bharat heavy electricals"],
"IREDA":["ireda"],
"RVNL":["rvnl","rail vikas nigam"],
"Zomato / Eternal":["zomato","eternal ltd","eternal stock"],
"W aaree Energies":["waaree energies","waaree stock"],
"Jio Financial":["jio financial","jiofin"],
"Trent":["trent stock","trent ltd"],
"BEL":["bharat electronics","bel stock"],
"Coal India":["coal india"],
}
POS=set("buy buying bought accumulate accumulating bullish upside breakout multibagger undervalued conviction hold holding long opportunity strong upside rebound rally outperform".split())
NEG=set("sell selling sold bearish overvalued avoid crash falling weak loss losses trap dump short downside".split())
FEEDS=["https://www.reddit.com/r/IndianStockMarket/new/.rss?limit=100","https://www.reddit.com/r/IndianStreetBets/new/.rss?limit=100"]
ATOM="{http://www.w3.org/2005/Atom}"
now=datetime.now(timezone.utc)
posts=[];failures=[]
for url in FEEDS:
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"PDMP-public-sentiment-research/1.0 (public RSS; non-commercial)","Accept":"application/atom+xml"})
  with urllib.request.urlopen(req,timeout=20) as r: root=ET.fromstring(r.read(1200000))
  for entry in root.findall(ATOM+"entry"):
   title=(entry.findtext(ATOM+"title") or "").strip()
   link=entry.find(ATOM+"link")
   href=link.get("href","") if link is not None else ""
   published=entry.findtext(ATOM+"published") or entry.findtext(ATOM+"updated") or ""
   try: dt=datetime.fromisoformat(published.replace("Z","+00:00"))
   except ValueError: continue
   if now-dt>timedelta(days=7) or dt>now+timedelta(minutes=5):continue
   posts.append({"title":title,"url":href,"published":published,"subreddit":url.split("/")[4]})
 except Exception as e:failures.append(type(e).__name__+": "+str(e)[:120])
rows=[]
for name,aliases in STOCKS.items():
 relevant=[p for p in posts if any(re.search(r"(?<![a-z0-9])"+re.escape(alias)+r"(?![a-z0-9])",p["title"].lower()) for alias in aliases)]
 relevant=list({p["url"]:p for p in relevant}.values())
 for p in relevant:
  words=set(re.findall(r"[a-z]+",p["title"].lower()))
  up=len(words&POS);down=len(words&NEG)
  p["sentiment"]="bullish" if up>down else "bearish" if down>up else "unclear"
 counts=Counter(p["sentiment"] for p in relevant)
 directional=counts["bullish"]+counts["bearish"]
 rows.append({"name":name,"mentions":len(relevant),"bullish":counts["bullish"],"bearish":counts["bearish"],"unclear":counts["unclear"],"bullish_pct":round(100*counts["bullish"]/directional) if directional else None,"evidence":relevant[:12],"sufficient":directional>=3})
rows.sort(key=lambda r:(r["sufficient"],r["bullish_pct"] if r["sufficient"] else -1,r["mentions"]),reverse=True)
out={"collected_at":now.isoformat(),"method":"public_reddit_post_titles_lexicon_v1","sources":FEEDS,"source_errors":failures,"coverage":"Two subreddit new-post RSS feeds; last 7 days; title-only; fixed watchlist; not all retail investors.","stocks":rows}
if posts:
 Path("retail_stocks.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
 print("Retail posts",len(posts),"stock matches",sum(x["mentions"] for x in rows))
else:
 print("No usable posts; preserving previous snapshot.",failures)
