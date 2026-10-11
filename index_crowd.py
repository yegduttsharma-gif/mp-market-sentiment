"""Conservative index crowd-opinion collector. Public forum titles, not market news or positioning."""
import json,re,urllib.request,urllib.parse,xml.etree.ElementTree as ET
from datetime import datetime,timezone,timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from collections import Counter
NOW=datetime.now(timezone.utc)
FEEDS={"IndianStockMarket":"https://www.reddit.com/r/IndianStockMarket/new/.rss?limit=100","IndianStreetBets":"https://www.reddit.com/r/IndianStreetBets/new/.rss?limit=100","StockMarketIndia":"https://www.reddit.com/r/StockMarketIndia/new/.rss?limit=100","IndianStocks":"https://www.reddit.com/r/IndianStocks/new/.rss?limit=100","tradingqna":"https://www.tradingqna.com/latest.rss?order=created","valuepickr":"https://forum.valuepickr.com/latest.rss?order=created"}
PATTERNS={"NIFTY 50":r"\b(?:nifty\s*50|nifty50|nifty index|nifty)\b","BANK NIFTY":r"\b(?:bank\s*nifty|banknifty|nifty\s*bank)\b","SENSEX":r"\b(?:sensex|bse\s*sensex)\b"}
BULL=re.compile(r"\b(?:bullish|upside|buy\s+calls?|buy\s+on\s+dips|going\s+(?:up|higher)|expect\s+(?:a\s+)?(?:rise|bounce)|breakout|new\s+highs?|long\s+nifty)\b",re.I)
BEAR=re.compile(r"\b(?:bearish|downside|buy\s+puts?|going\s+(?:down|lower)|expect\s+(?:a\s+)?(?:fall|crash|drop)|breakdown|new\s+lows?|short\s+nifty)\b",re.I)
QUESTION=re.compile(r"\b(?:what|why|how|should|could|would|prediction|forecast|analysis|news|update|thoughts)\b",re.I)
REPORT=re.compile(r"\b(?:fell|rose|surged|plunged|closed|ended|traded|session|recorded|reported|according|analyst|brokerage|declined|gained|dropped|slipped|crashed|market\s+wrap)\b",re.I)
for label,term in {"nifty_search":"nifty","bank_nifty_search":"bank nifty","sensex_search":"sensex","nifty_bets_search":"nifty"}.items():
 community="IndianStreetBets" if "bets" in label else "IndianStockMarket"
 FEEDS[label]="https://www.reddit.com/r/"+community+"/search.rss?"+urllib.parse.urlencode({"q":term,"restrict_sr":"on","sort":"new","t":"week","limit":100})
ATOM="{http://www.w3.org/2005/Atom}"
posts=[];health={}
for source,url in FEEDS.items():
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; PDMP research)","Accept":"application/rss+xml,application/atom+xml"})
  with urllib.request.urlopen(req,timeout=12) as response:root=ET.fromstring(response.read(1000000))
  entries=root.findall(ATOM+"entry") if "reddit.com" in url else root.findall(".//item")
  added=0
  for entry in entries:
   title=(entry.findtext(ATOM+"title") if "reddit.com" in url else entry.findtext("title")) or ""
   if "reddit.com" in url:
    linkel=entry.find(ATOM+"link");link=linkel.get("href","") if linkel is not None else ""
    date=entry.findtext(ATOM+"published") or entry.findtext(ATOM+"updated") or ""
    try:dt=datetime.fromisoformat(date.replace("Z","+00:00"))
    except ValueError:continue
   else:
    link=entry.findtext("link") or "";date=entry.findtext("pubDate") or ""
    try:dt=parsedate_to_datetime(date).astimezone(timezone.utc)
    except (TypeError,ValueError):continue
   if not title.strip() or not link or dt>NOW+timedelta(minutes=5) or NOW-dt>timedelta(days=7):continue
   posts.append({"title":title.strip(),"url":link,"source":source,"published":dt.isoformat()});added+=1
  health[source]={"status":"ok","recent":added}
 except Exception as e:health[source]={"status":"unavailable","error":type(e).__name__}
unique={}
for p in posts:
 key=re.sub(r"[^a-z0-9]+"," ",p["title"].lower()).strip()
 if key and key not in unique:unique[key]=p
posts=list(unique.values())
out={}
for name,pattern in PATTERNS.items():
 matched=[]
 for p in posts:
  title=p["title"]
  if not re.search(pattern,title,re.I):continue
  # NIFTY 50 excludes bank-nifty-only posts.
  if name=="NIFTY 50" and re.search(PATTERNS["BANK NIFTY"],title,re.I) and not re.search(r"\b(?:nifty\s*50|nifty50)\b",title,re.I):continue
  up=bool(BULL.search(title));down=bool(BEAR.search(title))
  opinion=not (QUESTION.search(title) or "?" in title or REPORT.search(title))
  stance="bullish" if opinion and up and not down else "bearish" if opinion and down and not up else "neutral"
  matched.append(dict(p,sentiment=stance))
 counts=Counter(p["sentiment"] for p in matched);n=counts["bullish"]+counts["bearish"];share=round(100*counts["bullish"]/n) if n else None
 label=("Insufficient Evidence" if n<10 else "Crowd Extremely Bullish" if share>=80 else "Crowd Bullish" if share>=60 else "Neutral" if share>=41 else "Crowd Bearish" if share>=21 else "Crowd Extremely Bearish")
 out[name]={"bullish":counts["bullish"],"bearish":counts["bearish"],"neutral":counts["neutral"],"directional":n,"bullish_pct":share if n>=10 else None,"label":label,"evidence":matched[:20]}
Path("index_crowd.json").write_text(json.dumps({"collected_at":NOW.isoformat(),"method":"explicit_directional_index_forum_titles_v2","minimum_directional":10,"source_health":health,"unique_titles":len(posts),"indices":out},indent=2)+"\n")
print("Index crowd titles",len(posts),{k:v["directional"] for k,v in out.items()})
