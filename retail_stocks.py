"""Multi-forum investor discussion sentiment; NOT measured retail ownership."""
import json,re,urllib.request,urllib.parse,xml.etree.ElementTree as ET
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
"Waaree Energies":["waaree energies","waaree stock"],
"Jio Financial":["jio financial","jiofin"],
"Trent":["trent stock","trent ltd"],
"BEL":["bharat electronics","bel stock"],
"Coal India":["coal india"],
"Paytm":["paytm","one97"],
"Vodafone Idea":["vodafone idea","vi stock","idea stock"],
"Yes Bank":["yes bank","yesbank"],
"Suzlon Energy":["suzlon"],
"JP Power":["jaiprakash power","jp power"],
"IRFC":["irfc","indian railway finance"],
"NHPC":["nhpc"],
"NBCC":["nbcc"],
"Tata Power":["tata power"],
"JSW Energy":["jsw energy"],
"Adani Power":["adani power"],
"Adani Green":["adani green"],
"Adani Ports":["adani ports"],
"Punjab National Bank":["punjab national bank","pnb stock"],
"Canara Bank":["canara bank"],
"IDFC First Bank":["idfc first"],
"Bank of Baroda":["bank of baroda"],
"Axis Bank":["axis bank"],
"Kotak Bank":["kotak mahindra bank","kotak bank"],
"Maruti Suzuki":["maruti suzuki","maruti stock"],
"Mahindra & Mahindra":["mahindra and mahindra","m&m stock"],
"Hyundai Motor India":["hyundai motor india"],
"ONGC":["ongc"],
"Vedanta":["vedanta stock","vedanta ltd"],
"Hindustan Zinc":["hindustan zinc"],
"HFCL":["hfcl"],
"RailTel":["railtel"],
"Titagarh Rail":["titagarh"],
"CDSL":["cdsl"],
"BSE Ltd":["bse ltd","bse stock"],
"MCX":["mcx stock","multi commodity exchange"],
"Jubilant Foodworks":["jubilant foodworks"],
"Dixon Technologies":["dixon technologies"],
"KPIT Technologies":["kpit"],
"Persistent Systems":["persistent systems"],
"Polycab":["polycab"],
"CG Power":["cg power"],
"Indian Hotels":["indian hotels","ihcl"],
}
POS=set("buy buying bought accumulate accumulating bullish upside breakout multibagger undervalued conviction hold holding long opportunity strong upside rebound rally outperform".split())
NEG=set("sell selling sold bearish overvalued avoid crash falling weak loss losses trap dump short downside".split())
NEG |= set("suspend suspends suspended suspending suspension ban banned bans restriction restrictions investigation investigations probe probes fraud alleged allegations terrible layoffs layoff fired firing recession crisis slump collapse collapses collapsed plunge plunges losses warning downgrade downgraded".split())
POS |= set("approval approved approves expansion expands expanded growth grows growing contract contracts order orders wins won profit profits profitable upgrade upgraded record recovery".split())
NEG_PHRASES=("rest in peace","green card programme","green card program","immigration program","immigration programme","labor certification","labour certification","near 0% gain","near zero gain","regulatory action","regulatory crackdown","under investigation","h-1b abuse","h1b abuse")
POS_PHRASES=("beats estimates","record profit","strong earnings","raises guidance","new order win","wins contract","receives approval","all time high","all-time high")
def direction(title):
 t=title.lower()
 words=set(re.findall(r"[a-z]+",t))
 up=len(words&POS)+2*sum(p in t for p in POS_PHRASES)
 down=len(words&NEG)+2*sum(p in t for p in NEG_PHRASES)
 return "bullish" if up>down else "bearish" if down>up else "neutral"

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
# Direct public Discourse feeds: do not depend on search indexing for these forums.
# Keep publication dates and source labels; RSS titles are not individual trader votes.
import email.utils
DIRECT_FORUMS={
 "tradingqna":"https://www.tradingqna.com/latest.rss?order=created",
 "valuepickr":"https://forum.valuepickr.com/latest.rss?order=created",
}
feed_health={}
for source,url in DIRECT_FORUMS.items():
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; PDMP public research)","Accept":"application/rss+xml,application/xml,*/*"})
  with urllib.request.urlopen(req,timeout=20) as response: root=ET.fromstring(response.read(1600000))
  accepted=0
  for item in root.findall(".//item"):
   title=(item.findtext("title") or "").strip()
   link=(item.findtext("link") or "").strip()
   published=(item.findtext("pubDate") or "").strip()
   if not title or not link or not published:continue
   try: dt=email.utils.parsedate_to_datetime(published).astimezone(timezone.utc)
   except (TypeError,ValueError):continue
   if now-dt>timedelta(days=7) or dt>now+timedelta(minutes=5):continue
   posts.append({"title":title,"url":link,"published":published,"subreddit":source})
   accepted+=1
  feed_health[source]={"status":"ok","recent_items":accepted}
 except Exception as exc:
  feed_health[source]={"status":"unavailable","recent_items":0,"error":type(exc).__name__}
  failures.append(source+" direct RSS: "+type(exc).__name__)
# If Reddit blocks RSS requests, Google News may still index public Reddit discussions.
# These are only search-result titles, not a representative sample.
# Broader discovery: indexed public discussion titles across several stock groups.
# Search-engine indexing is incomplete; this is not a representative retail poll.
SEARCHES=[
 'site:reddit.com/r/IndianStockMarket (stock OR shares OR buy OR bullish) when:7d',
 'site:reddit.com/r/IndianStreetBets (stock OR shares OR buy OR bullish) when:7d',
 'site:reddit.com/r/IndianStockMarket (suzlon OR irfc OR ireda OR rvnl OR paytm OR yesbank) when:7d',
 'site:reddit.com/r/IndianStreetBets (tata OR reliance OR hdfc OR adani OR bank) when:7d',
 'site:reddit.com/r/IndianStockMarket (smallcap OR midcap OR multibagger OR portfolio) when:7d',
 'site:tradingqna.com (stock OR shares OR bullish OR buying) when:7d',
 'site:forum.valuepickr.com (stock OR shares OR buy OR investing) when:7d',
 'site:tradingqna.com (suzlon OR irfc OR ireda OR rvnl OR reliance OR hdfc) when:7d',
 'site:forum.valuepickr.com (tata OR adani OR bank OR smallcap OR midcap) when:7d',
 'site:x.com (nifty OR stocks OR shares OR bullish OR buying) when:7d',
 'site:twitter.com (nifty OR stocks OR shares OR bullish OR buying) when:7d',
 'site:youtube.com/watch (indian stocks OR stock market OR share analysis) when:7d',
 'site:facebook.com (indian stock market OR stocks bullish OR share market) when:7d',
 'site:instagram.com (indian stocks OR stock market OR share market) when:7d',
 'site:x.com (suzlon OR irfc OR ireda OR rvnl OR tata motors OR reliance) when:7d',
 'site:youtube.com/watch (suzlon OR irfc OR ireda OR rvnl OR tata motors OR reliance) when:7d',
]
# Search queries are independent; fetch concurrently to reduce workflow time.
# Indexed search is discovery only, not a direct platform API.
from concurrent.futures import ThreadPoolExecutor,as_completed
def fetch_indexed(query):
 url="https://news.google.com/rss/search?q="+urllib.parse.quote(query)+"&hl=en-IN&gl=IN&ceid=IN:en"
 req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
 with urllib.request.urlopen(req,timeout=10) as r: root=ET.fromstring(r.read(1500000))
 source=("tradingqna" if "tradingqna.com" in query else "valuepickr" if "valuepickr.com" in query else "x" if "site:x.com" in query or "site:twitter.com" in query else "youtube" if "site:youtube.com" in query else "facebook" if "site:facebook.com" in query else "instagram" if "site:instagram.com" in query else "indexed_reddit")
 found=[]
 for item in root.findall(".//item"):
  title=(item.findtext("title") or "").strip()
  link=(item.findtext("link") or "").strip()
  published=(item.findtext("pubDate") or "").strip()
  if not title or not link or not published:continue
  try: dt=email.utils.parsedate_to_datetime(published).astimezone(timezone.utc)
  except (TypeError,ValueError):continue
  if now-dt>timedelta(days=7) or dt>now+timedelta(minutes=5):continue
  # Google News may return unrelated articles; require a matching source domain in title.
  domain={"indexed_reddit":"reddit.com","tradingqna":"tradingqna.com","valuepickr":"valuepickr.com","x":"x.com","youtube":"youtube.com","facebook":"facebook.com","instagram":"instagram.com"}[source]
  markers={"indexed_reddit":("reddit",),"tradingqna":("tradingqna","trading q&a"),"valuepickr":("valuepickr",),"x":("twitter","x.com"),"youtube":("youtube",),"facebook":("facebook",),"instagram":("instagram",)}[source]
  if not any(marker in title.lower() for marker in markers):continue
  found.append({"title":title,"url":link,"published":published,"subreddit":source})
 return found
with ThreadPoolExecutor(max_workers=6) as pool:
 futures={pool.submit(fetch_indexed,q):q for q in SEARCHES}
 for future in as_completed(futures):
  try: posts.extend(future.result())
  except Exception as e: failures.append("Indexed search "+type(e).__name__)
# Preserve the original source URL, prefer direct forum links to indexed duplicates.
posts.sort(key=lambda p: (p["subreddit"] in ("tradingqna","valuepickr","IndianStockMarket","IndianStreetBets")),reverse=True)
posts=list({re.sub(r"\\s+"," ",re.sub(r" - (Reddit|Trading Q&A|ValuePickr)$","",p["title"],flags=re.I).strip().lower()):p for p in posts}.values())
source_counts=dict(Counter(p["subreddit"] for p in posts))

rows=[]
for name,aliases in STOCKS.items():
 relevant=[p for p in posts if any(re.search(r"(?<![a-z0-9])"+re.escape(alias)+r"(?![a-z0-9])",p["title"].lower()) for alias in aliases)]
 relevant=list({p["url"]:p for p in relevant}.values())
 for p in relevant:
  p["sentiment"]=direction(p["title"])
 counts=Counter(p["sentiment"] for p in relevant)
 directional=counts["bullish"]+counts["bearish"]
 rows.append({"name":name,"mentions":len(relevant),"bullish":counts["bullish"],"bearish":counts["bearish"],"neutral":counts["neutral"],"bullish_pct":round(100*counts["bullish"]/directional) if directional else None,"evidence":relevant[:12],"sufficient":directional>=3})
rows.sort(key=lambda r:(r["sufficient"],r["bullish_pct"] if r["sufficient"] else -1,r["mentions"]),reverse=True)
out={"collected_at":now.isoformat(),"method":"three_way_direct_discourse_and_indexed_titles_v7","sources":FEEDS+["TradingQnA indexed discussions","ValuePickr indexed discussions","X/Twitter indexed public posts","YouTube indexed public videos","Facebook indexed public posts","Instagram indexed public posts"],"source_errors":failures,"coverage":"Direct public RSS plus search-indexed titles, with a seven-day freshness filter. Indexed platform labels are inferred from publisher titles, not verified platform API access. Coverage varies sharply and is not a representative poll.","posts_collected":len(posts),"source_counts":source_counts,"direct_feed_health":feed_health,"status":"available" if posts else "sources_unavailable","stocks":rows}
Path("retail_stocks.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
print("Retail posts",len(posts),"stock matches",sum(x["mentions"] for x in rows),"errors",failures)
